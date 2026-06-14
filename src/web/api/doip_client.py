"""REST + WebSocket endpoints for the in-browser DoIP client tester."""

import asyncio
import ipaddress
import json
import socket
import struct
import time
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from web.models import DoIPSendRequest, DoIPSendUdpRequest
from web.state import get_state

router = APIRouter(prefix="/api/client", tags=["doip-client"])

DOIP_VERSION = 0x02
DOIP_INV_VERSION = 0xFD
ROUTING_ACTIVATION_REQUEST = 0x0005
DIAGNOSTIC_MESSAGE = 0x8001
MAX_DOIP_PAYLOAD_LEN = 64 * 1024
EXPECTED_RESPONSE_TYPES = {0x0006, 0x8001, 0x8002, 0x8003}
# Extra time to wait for additional responses from other ECUs after a
# functional (broadcast) request, once the first UDS response is in.
FUNCTIONAL_EXTRA_TIMEOUT = 0.5

PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_REQUEST = 0x0001
PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_RESPONSE = 0x0004
PAYLOAD_TYPE_ENTITY_STATUS_REQUEST = 0x4001
PAYLOAD_TYPE_ENTITY_STATUS_RESPONSE = 0x4002
PAYLOAD_TYPE_POWER_MODE_INFORMATION_REQUEST = 0x4003
PAYLOAD_TYPE_POWER_MODE_INFORMATION_RESPONSE = 0x4004

# ISO 13400-2:2019 mandates 0xFF/0x00 for vehicle identification requests;
# all other UDP messages use the standard DoIP protocol version.
UDP_MESSAGE_SPECS = {
    "vehicle_identification": {
        "version": (0xFF, 0x00),
        "request_type": PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_REQUEST,
        "response_type": PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_RESPONSE,
    },
    "entity_status": {
        "version": (DOIP_VERSION, DOIP_INV_VERSION),
        "request_type": PAYLOAD_TYPE_ENTITY_STATUS_REQUEST,
        "response_type": PAYLOAD_TYPE_ENTITY_STATUS_RESPONSE,
    },
    "power_mode": {
        "version": (DOIP_VERSION, DOIP_INV_VERSION),
        "request_type": PAYLOAD_TYPE_POWER_MODE_INFORMATION_REQUEST,
        "response_type": PAYLOAD_TYPE_POWER_MODE_INFORMATION_RESPONSE,
    },
}


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

    # Prefer IPv4 — the default server binding is 0.0.0.0, not ::
    ipv4 = [a for a in addresses if a.version == 4]
    return str((ipv4 or addresses)[0])


def _parse_udp_response_payload(message_type: str, payload: bytes) -> dict:
    """Decode a UDP response payload for the given message type."""
    if message_type == "vehicle_identification":
        if len(payload) < 33:
            raise ValueError(
                f"Vehicle identification payload too short: {len(payload)}"
            )
        logical_address = int.from_bytes(payload[17:19], "big")
        return {
            "vin": payload[0:17].decode("ascii", errors="ignore").rstrip("\x00"),
            "logical_address": logical_address,
            "logical_address_hex": f"0x{logical_address:04X}",
            "eid": payload[19:25].hex().upper(),
            "gid": payload[25:31].hex().upper(),
            "further_action_required": payload[31],
            "vin_gid_sync_status": payload[32],
        }
    if message_type == "entity_status":
        if len(payload) < 5:
            raise ValueError(f"Entity status payload too short: {len(payload)}")
        return {
            "node_type": payload[0],
            "max_open_sockets": payload[1],
            "current_open_sockets": payload[2],
            "doip_entity_status": payload[3],
            "diagnostic_power_mode": payload[4],
        }
    if message_type == "power_mode":
        if len(payload) < 1:
            raise ValueError("Power mode payload too short")
        return {"power_mode_status": payload[0]}
    raise ValueError(f"Unknown UDP message type: {message_type}")


def _send_udp_sync(req: DoIPSendUdpRequest) -> dict:
    """Send a single UDP DoIP request (vehicle ID / entity status / power mode)."""
    log: list[dict] = []

    def note(event: str, detail: str = ""):
        log.append({"ts": round(time.time() * 1000), "event": event, "detail": detail})

    spec = UDP_MESSAGE_SPECS[req.message_type]
    try:
        target_host = _resolve_loopback_host(req.host, req.port)
        note("connecting", f"{req.host}:{req.port}")

        family = socket.AF_INET6 if ":" in target_host else socket.AF_INET
        ver, inv = spec["version"]
        request = struct.pack(">BBHI", ver, inv, spec["request_type"], 0)

        with socket.socket(family, socket.SOCK_DGRAM) as sock:
            sock.settimeout(req.timeout)
            sock.sendto(request, (target_host, req.port))
            note("sent", f"type=0x{spec['request_type']:04X}")

            data, addr = sock.recvfrom(MAX_DOIP_PAYLOAD_LEN)
            note("received", f"{len(data)} bytes from {addr[0]}:{addr[1]}")

            if len(data) < 8:
                note("error", "Response too short for DoIP header")
                return {"ok": False, "log": log, "response": None}

            resp_ver, resp_inv, payload_type, payload_len = struct.unpack(
                ">BBHI", data[:8]
            )
            if resp_ver != DOIP_VERSION or resp_inv != DOIP_INV_VERSION:
                note(
                    "error",
                    f"Invalid response header version 0x{resp_ver:02X}/0x{resp_inv:02X}",
                )
                return {"ok": False, "log": log, "response": None}
            if payload_type != spec["response_type"]:
                note("unexpected_frame", f"type=0x{payload_type:04X}")
                return {"ok": False, "log": log, "response": None}

            payload = data[8 : 8 + payload_len]
            parsed = _parse_udp_response_payload(req.message_type, payload)
            note("parsed_response")
            return {
                "ok": True,
                "log": log,
                "response": parsed,
                "raw_response": payload.hex().upper(),
            }

    except TimeoutError:
        note("timeout")
        return {"ok": False, "log": log, "response": None}
    except Exception as exc:
        note("error", str(exc))
        return {"ok": False, "log": log, "response": None}


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
            diag = _build_diagnostic_message(
                req.source_address, req.target_address, uds_bytes
            )
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
                return {"ok": False, "log": log, "response": None, "responses": []}

            # UDS response(s) — a functional (broadcast) request may receive one
            # response frame per responding ECU.
            cm = get_state().config_manager
            is_functional = bool(
                cm and cm.get_ecus_by_functional_address(req.target_address)
            )

            responses: list[dict] = []
            while True:
                sock.settimeout(
                    req.timeout if not responses else FUNCTIONAL_EXTRA_TIMEOUT
                )
                try:
                    resp_frame = _parse_doip_frame(sock)
                except TimeoutError:
                    break

                if resp_frame is None:
                    break
                if resp_frame["type"] != 0x8001:
                    note("unexpected_frame", f"type=0x{resp_frame['type']:04X}")
                    break

                payload = resp_frame["payload"]
                ecu_address = int.from_bytes(payload[0:2], "big")
                uds_response = payload[4:].hex().upper()
                note("got_response", f"from 0x{ecu_address:04X}: {uds_response}")
                responses.append(
                    {
                        "ecu_address": ecu_address,
                        "ecu_address_hex": f"0x{ecu_address:04X}",
                        "response": uds_response,
                    }
                )

                if not is_functional:
                    break

            if not responses:
                note("no_response")
                return {"ok": False, "log": log, "response": None, "responses": []}

            return {
                "ok": True,
                "log": log,
                "response": responses[0]["response"],
                "responses": responses,
            }

    except TimeoutError:
        note("timeout")
        return {"ok": False, "log": log, "response": None, "responses": []}
    except Exception as exc:
        note("error", str(exc))
        return {"ok": False, "log": log, "response": None, "responses": []}


@router.post("/send")
async def send_diagnostic(req: DoIPSendRequest):
    """Send a single DoIP diagnostic message and return the UDS response."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _send_diagnostic_sync, req)
    return result


@router.post("/send-udp")
async def send_udp(req: DoIPSendUdpRequest):
    """Send a UDP DoIP request (vehicle identification / entity status / power mode)."""
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _send_udp_sync, req)
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
                    "responses": result.get("responses", []),
                }
            )

    except WebSocketDisconnect:
        pass
