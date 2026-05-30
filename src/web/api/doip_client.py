"""REST + WebSocket endpoints for the in-browser DoIP client tester."""

import asyncio
import ipaddress
import json
import socket
import struct
import time
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from web.models import DoIPSendRequest

router = APIRouter(prefix="/api/client", tags=["doip-client"])

DOIP_VERSION = 0x02
DOIP_INV_VERSION = 0xFD
ROUTING_ACTIVATION_REQUEST = 0x0005
DIAGNOSTIC_MESSAGE = 0x8001
MAX_DOIP_PAYLOAD_LEN = 64 * 1024
EXPECTED_RESPONSE_TYPES = {0x0006, 0x8001, 0x8002, 0x8003}


def _build_header(payload_type: int, payload_len: int) -> bytes:
    return struct.pack(
        ">BBHI",
        DOIP_VERSION,
        DOIP_INV_VERSION,
        payload_type,
        payload_len,
    )


def _build_routing_activation(source_address: int) -> bytes:
    payload = struct.pack(">HBL", source_address, 0x00, 0x00000000)
    return _build_header(ROUTING_ACTIVATION_REQUEST, len(payload)) + payload


def _build_diagnostic_message(source: int, target: int, uds_bytes: bytes) -> bytes:
    payload = struct.pack(">HH", source, target) + uds_bytes
    return _build_header(DIAGNOSTIC_MESSAGE, len(payload)) + payload


def _resolve_loopback_host(host: str, port: int) -> str:
    """Resolve a client target and require it to stay on the dashboard host."""
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError(f"Unable to resolve host '{host}'") from exc

    addresses = []
    for _family, _socktype, _proto, _canonname, sockaddr in infos:
        try:
            addresses.append(ipaddress.ip_address(sockaddr[0]))
        except ValueError:
            continue

    if not addresses:
        raise ValueError(f"Unable to resolve host '{host}'")
    if any(not address.is_loopback for address in addresses):
        raise ValueError("DoIP client host must resolve to a loopback address")

    return str(addresses[0])


def _recv_exact(sock: socket.socket, n: int) -> Optional[bytes]:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def _parse_doip_frame(sock: socket.socket) -> Optional[dict]:
    header = _recv_exact(sock, 8)
    if not header:
        return None
    ver, inv, payload_type, payload_len = struct.unpack(">BBHI", header)
    if ver != DOIP_VERSION or inv != DOIP_INV_VERSION:
        raise ValueError("Invalid DoIP response header")
    if payload_type not in EXPECTED_RESPONSE_TYPES:
        raise ValueError(f"Unexpected DoIP payload type: 0x{payload_type:04X}")
    if payload_len > MAX_DOIP_PAYLOAD_LEN:
        raise ValueError(
            f"DoIP payload length {payload_len} exceeds limit {MAX_DOIP_PAYLOAD_LEN}"
        )
    payload = _recv_exact(sock, payload_len) if payload_len else b""
    if payload is None:
        return None
    return {"type": payload_type, "payload": payload}


def _send_diagnostic_sync(req: DoIPSendRequest) -> dict:
    """Run a single DoIP diagnostic exchange synchronously (called in thread pool)."""
    log: list[dict] = []
    uds_bytes = bytes.fromhex(req.uds_message)

    def note(event: str, detail: str = ""):
        log.append({"ts": round(time.time() * 1000), "event": event, "detail": detail})

    try:
        note("connecting", f"{req.host}:{req.port}")
        target_host = _resolve_loopback_host(req.host, req.port)
        with socket.create_connection(
            (target_host, req.port), timeout=req.timeout
        ) as sock:
            sock.settimeout(req.timeout)
            note("connected")

            # Routing activation
            sock.sendall(_build_routing_activation(req.source_address))
            note("sent_routing_activation", f"source=0x{req.source_address:04X}")

            frame = _parse_doip_frame(sock)
            if frame is None:
                note("error", "No routing activation response")
                return {"ok": False, "log": log, "response": None}

            if frame["type"] == 0x0006:
                payload = frame["payload"]
                code = payload[4] if len(payload) > 4 else -1
                if code != 0x10:
                    note("routing_failed", f"code=0x{code:02X}")
                    return {"ok": False, "log": log, "response": None}
                note("routing_activated")
            else:
                note("unexpected_frame", f"type=0x{frame['type']:04X}")

            # Diagnostic message
            diag = _build_diagnostic_message(req.source_address, req.target_address, uds_bytes)
            sock.sendall(diag)
            note(
                "sent_diagnostic",
                f"src=0x{req.source_address:04X} tgt=0x{req.target_address:04X} uds={req.uds_message}",
            )

            # ACK
            ack_frame = _parse_doip_frame(sock)
            if ack_frame and ack_frame["type"] == 0x8002:
                note("got_ack")
            elif ack_frame and ack_frame["type"] == 0x8003:
                note("got_nack", ack_frame["payload"].hex())
                return {"ok": False, "log": log, "response": None}

            # UDS response
            resp_frame = _parse_doip_frame(sock)
            if resp_frame and resp_frame["type"] == 0x8001:
                uds_response = resp_frame["payload"][4:].hex().upper()
                note("got_response", uds_response)
                return {"ok": True, "log": log, "response": uds_response}

            note("no_response")
            return {"ok": False, "log": log, "response": None}

    except TimeoutError:
        note("timeout")
        return {"ok": False, "log": log, "response": None}
    except Exception as exc:
        note("error", str(exc))
        return {"ok": False, "log": log, "response": None}


@router.post("/send")
async def send_diagnostic(req: DoIPSendRequest):
    """Send a single DoIP diagnostic message and return the UDS response."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _send_diagnostic_sync, req)
    return result


@router.websocket("/ws")
async def doip_client_ws(websocket: WebSocket):
    """WebSocket endpoint for the interactive DoIP client tester.

    The client sends JSON matching *DoIPSendRequest*; the server streams
    log events as JSON objects and ends with a final result frame.
    """
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
                req = DoIPSendRequest(**data)
            except Exception as exc:
                await websocket.send_json({"event": "error", "detail": str(exc)})
                continue

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, _send_diagnostic_sync, req)

            for entry in result["log"]:
                await websocket.send_json(entry)

            await websocket.send_json(
                {
                    "event": "done",
                    "ok": result["ok"],
                    "response": result["response"],
                }
            )

    except WebSocketDisconnect:
        pass
