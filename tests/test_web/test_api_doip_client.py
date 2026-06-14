"""Tests for the DoIP client REST and WebSocket endpoints.

The actual TCP socket call is mocked so these remain fast unit tests.
"""

import struct
from unittest.mock import patch

import pytest

from web.api.doip_client import _resolve_loopback_host, _send_diagnostic_sync
from web.models import DoIPSendRequest

# The sync function we'll mock out
_TARGET = "web.api.doip_client._send_diagnostic_sync"


@pytest.mark.unit
def test_resolve_loopback_host_ipv6():
    assert _resolve_loopback_host("::1", 13400) == "::1"


@pytest.mark.unit
def test_resolve_loopback_host_localhost():
    import ipaddress

    resolved = _resolve_loopback_host("localhost", 13400)
    assert ipaddress.ip_address(resolved).is_loopback


@pytest.mark.unit
def test_resolve_loopback_host_rejects_public():
    with pytest.raises(ValueError, match="loopback"):
        _resolve_loopback_host("8.8.8.8", 13400)


@pytest.mark.unit
def test_send_success(web_client):
    mock_result = {
        "ok": True,
        "response": "62F1901HGBH41JXM",
        "responses": [
            {
                "ecu_address": 1,
                "ecu_address_hex": "0x0001",
                "response": "62F1901HGBH41JXM",
            }
        ],
        "log": [{"ts": 0, "event": "connected", "detail": ""}],
    }
    with patch(_TARGET, return_value=mock_result):
        r = web_client.post(
            "/api/client/send",
            json={
                "host": "127.0.0.1",
                "port": 13400,
                "source_address": 0x0E00,
                "target_address": 0x0001,
                "uds_message": "22F190",
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["response"] == "62F1901HGBH41JXM"


@pytest.mark.unit
def test_send_timeout(web_client):
    mock_result = {
        "ok": False,
        "response": None,
        "responses": [],
        "log": [{"ts": 0, "event": "timeout", "detail": ""}],
    }
    with patch(_TARGET, return_value=mock_result):
        r = web_client.post(
            "/api/client/send",
            json={
                "host": "127.0.0.1",
                "port": 13400,
                "source_address": 0x0E00,
                "target_address": 0x0001,
                "uds_message": "22F190",
            },
        )
    assert r.status_code == 200
    assert r.json()["ok"] is False


@pytest.mark.unit
def test_send_invalid_hex(web_client):
    r = web_client.post(
        "/api/client/send",
        json={
            "host": "127.0.0.1",
            "port": 13400,
            "source_address": 0x0E00,
            "target_address": 0x0001,
            "uds_message": "ZZZZZZ",  # invalid hex
        },
    )
    assert r.status_code == 422


def _doip_frame(payload_type: int, payload: bytes) -> bytes:
    return struct.pack(">BBHI", 0x02, 0xFD, payload_type, len(payload)) + payload


class _FakeSocket:
    """Minimal socket stand-in that serves a fixed byte stream then times out."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def settimeout(self, timeout):
        pass

    def sendall(self, data):
        pass

    def recv(self, n):
        if self.pos >= len(self.data):
            raise TimeoutError()
        chunk = self.data[self.pos : self.pos + n]
        self.pos += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


@pytest.mark.unit
def test_send_diagnostic_sync_functional_multi_response():
    """A functional broadcast collects one response frame per responding ECU."""
    routing_resp = _doip_frame(0x0006, b"\x00\x00\x00\x00\x10")
    ack_resp = _doip_frame(0x8002, b"\x00\x00\x00\x00\x00")
    uds_resp_1 = _doip_frame(
        0x8001, struct.pack(">HH", 0x0001, 0x0E00) + bytes.fromhex("62F19011")
    )
    uds_resp_2 = _doip_frame(
        0x8001, struct.pack(">HH", 0x0002, 0x0E00) + bytes.fromhex("62F19022")
    )
    fake_sock = _FakeSocket(routing_resp + ack_resp + uds_resp_1 + uds_resp_2)

    req = DoIPSendRequest(
        host="127.0.0.1",
        port=13400,
        source_address=0x0E00,
        target_address=0x0000,
        uds_message="22F190",
    )

    with (
        patch("web.api.doip_client._resolve_loopback_host", return_value="127.0.0.1"),
        patch("socket.create_connection", return_value=fake_sock),
        patch("web.api.doip_client.get_state") as mock_get_state,
    ):
        mock_get_state.return_value.config_manager.get_ecus_by_functional_address.return_value = [
            1,
            2,
        ]
        result = _send_diagnostic_sync(req)

    assert result["ok"] is True
    assert result["response"] == "62F19011"
    assert result["responses"] == [
        {"ecu_address": 1, "ecu_address_hex": "0x0001", "response": "62F19011"},
        {"ecu_address": 2, "ecu_address_hex": "0x0002", "response": "62F19022"},
    ]


@pytest.mark.unit
def test_send_diagnostic_sync_physical_single_response():
    """A physical request stops after the first UDS response, even if more frames follow."""
    routing_resp = _doip_frame(0x0006, b"\x00\x00\x00\x00\x10")
    ack_resp = _doip_frame(0x8002, b"\x00\x00\x00\x00\x00")
    uds_resp_1 = _doip_frame(
        0x8001, struct.pack(">HH", 0x0001, 0x0E00) + bytes.fromhex("62F19011")
    )
    uds_resp_2 = _doip_frame(
        0x8001, struct.pack(">HH", 0x0002, 0x0E00) + bytes.fromhex("62F19022")
    )
    fake_sock = _FakeSocket(routing_resp + ack_resp + uds_resp_1 + uds_resp_2)

    req = DoIPSendRequest(
        host="127.0.0.1",
        port=13400,
        source_address=0x0E00,
        target_address=0x0001,
        uds_message="22F190",
    )

    with (
        patch("web.api.doip_client._resolve_loopback_host", return_value="127.0.0.1"),
        patch("socket.create_connection", return_value=fake_sock),
        patch("web.api.doip_client.get_state") as mock_get_state,
    ):
        mock_get_state.return_value.config_manager.get_ecus_by_functional_address.return_value = (
            []
        )
        result = _send_diagnostic_sync(req)

    assert result["ok"] is True
    assert result["responses"] == [
        {"ecu_address": 1, "ecu_address_hex": "0x0001", "response": "62F19011"},
    ]


@pytest.mark.unit
def test_ws_send_and_receive(web_client):
    mock_result = {
        "ok": True,
        "response": "62F190AA",
        "responses": [
            {"ecu_address": 1, "ecu_address_hex": "0x0001", "response": "62F190AA"}
        ],
        "log": [{"ts": 1, "event": "got_response", "detail": "62F190AA"}],
    }
    with patch(_TARGET, return_value=mock_result):
        with web_client.websocket_connect("/api/client/ws") as ws:
            ws.send_json(
                {
                    "host": "127.0.0.1",
                    "port": 13400,
                    "source_address": 0x0E00,
                    "target_address": 0x0001,
                    "uds_message": "22F190",
                }
            )
            events = []
            while True:
                msg = ws.receive_json()
                events.append(msg)
                if msg.get("event") == "done":
                    break

    done = events[-1]
    assert done["event"] == "done"
    assert done["ok"] is True
    assert done["response"] == "62F190AA"
    assert done["responses"] == mock_result["responses"]


@pytest.mark.unit
def test_ws_invalid_json(web_client):
    with web_client.websocket_connect("/api/client/ws") as ws:
        ws.send_json({"not_a_valid": "request"})  # missing required fields
        msg = ws.receive_json()
        assert msg["event"] == "error"
