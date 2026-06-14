"""Tests for the DoIP client REST and WebSocket endpoints.

The actual TCP socket call is mocked so these remain fast unit tests.
"""

import struct
from unittest.mock import patch

import pytest

from web.api.doip_client import (
    _resolve_loopback_host,
    _send_diagnostic_sync,
    _send_raw_udp_sync,
    _send_udp_sync,
)
from web.models import DoIPSendRawUdpRequest, DoIPSendRequest, DoIPSendUdpRequest

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
        mock_get_state.return_value.config_manager.get_protocol_config.return_value = {
            "version": 0x02,
            "inverse_version": 0xFD,
        }
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
        mock_get_state.return_value.config_manager.get_protocol_config.return_value = {
            "version": 0x02,
            "inverse_version": 0xFD,
        }
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


class _FakeUdpSocket:
    """Minimal UDP socket stand-in returning a single canned datagram."""

    def __init__(self, data: bytes, addr=("127.0.0.1", 13400)):
        self.data = data
        self.addr = addr
        self.sent = []

    def settimeout(self, timeout):
        pass

    def sendto(self, data, addr):
        self.sent.append((data, addr))
        return len(data)

    def recvfrom(self, n):
        return self.data, self.addr

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def _udp_response(payload_type: int, payload: bytes) -> bytes:
    return struct.pack(">BBHI", 0x02, 0xFD, payload_type, len(payload)) + payload


@pytest.mark.unit
def test_send_udp_vehicle_identification():
    payload = (
        b"1HGBH41JXMN109186".ljust(17, b"\x00")  # VIN
        + struct.pack(">H", 0x0001)  # logical address
        + bytes.fromhex("AABBCCDDEEFF")  # EID
        + bytes.fromhex("112233445566")  # GID
        + b"\x00"  # further action required
        + b"\x00"  # vin/gid sync status
    )
    fake_sock = _FakeUdpSocket(
        _udp_response(0x0004, payload), addr=("127.0.0.1", 13400)
    )

    req = DoIPSendUdpRequest(
        host="127.0.0.1", port=13400, message_type="vehicle_identification"
    )

    with (
        patch("web.api.doip_client._resolve_loopback_host", return_value="127.0.0.1"),
        patch("socket.socket", return_value=fake_sock),
    ):
        result = _send_udp_sync(req)

    assert result["ok"] is True
    assert result["response"]["vin"] == "1HGBH41JXMN109186"
    assert result["response"]["logical_address"] == 0x0001
    assert result["response"]["logical_address_hex"] == "0x0001"
    assert result["response"]["eid"] == "AABBCCDDEEFF"
    assert result["response"]["gid"] == "112233445566"

    # Vehicle identification requests use the ISO 13400-2:2019 0xFF/0x00 version.
    sent_data, _ = fake_sock.sent[0]
    assert sent_data == struct.pack(">BBHI", 0xFF, 0x00, 0x0001, 0)


@pytest.mark.unit
def test_send_udp_entity_status():
    payload = bytes([0x00, 0x05, 0x01, 0x00, 0x01])
    fake_sock = _FakeUdpSocket(_udp_response(0x4002, payload))

    req = DoIPSendUdpRequest(host="127.0.0.1", port=13400, message_type="entity_status")

    with (
        patch("web.api.doip_client._resolve_loopback_host", return_value="127.0.0.1"),
        patch("socket.socket", return_value=fake_sock),
    ):
        result = _send_udp_sync(req)

    assert result["ok"] is True
    assert result["response"] == {
        "node_type": 0x00,
        "max_open_sockets": 0x05,
        "current_open_sockets": 0x01,
        "doip_entity_status": 0x00,
        "diagnostic_power_mode": 0x01,
    }


@pytest.mark.unit
def test_send_udp_power_mode():
    payload = bytes([0x01])
    fake_sock = _FakeUdpSocket(_udp_response(0x4004, payload))

    req = DoIPSendUdpRequest(host="127.0.0.1", port=13400, message_type="power_mode")

    with (
        patch("web.api.doip_client._resolve_loopback_host", return_value="127.0.0.1"),
        patch("socket.socket", return_value=fake_sock),
    ):
        result = _send_udp_sync(req)

    assert result["ok"] is True
    assert result["response"] == {"power_mode_status": 0x01}


@pytest.mark.unit
def test_send_udp_unexpected_response_type():
    fake_sock = _FakeUdpSocket(_udp_response(0x4002, bytes(5)))

    req = DoIPSendUdpRequest(
        host="127.0.0.1", port=13400, message_type="vehicle_identification"
    )

    with (
        patch("web.api.doip_client._resolve_loopback_host", return_value="127.0.0.1"),
        patch("socket.socket", return_value=fake_sock),
    ):
        result = _send_udp_sync(req)

    assert result["ok"] is False
    assert result["response"] is None


@pytest.mark.unit
def test_send_udp_timeout():
    class _TimeoutSocket(_FakeUdpSocket):
        def recvfrom(self, n):
            raise TimeoutError()

    req = DoIPSendUdpRequest(
        host="127.0.0.1", port=13400, message_type="vehicle_identification"
    )

    with (
        patch("web.api.doip_client._resolve_loopback_host", return_value="127.0.0.1"),
        patch("socket.socket", return_value=_TimeoutSocket(b"")),
    ):
        result = _send_udp_sync(req)

    assert result["ok"] is False
    assert any(entry["event"] == "timeout" for entry in result["log"])


@pytest.mark.unit
def test_send_udp_endpoint(web_client):
    mock_result = {
        "ok": True,
        "response": {"power_mode_status": 0x01},
        "log": [{"ts": 0, "event": "sent", "detail": ""}],
    }
    with patch("web.api.doip_client._send_udp_sync", return_value=mock_result):
        r = web_client.post(
            "/api/client/send-udp",
            json={"host": "127.0.0.1", "port": 13400, "message_type": "power_mode"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["response"] == {"power_mode_status": 0x01}


@pytest.mark.unit
def test_send_udp_invalid_message_type(web_client):
    r = web_client.post(
        "/api/client/send-udp",
        json={"host": "127.0.0.1", "port": 13400, "message_type": "bogus"},
    )
    assert r.status_code == 422


@pytest.mark.unit
def test_send_udp_uses_configured_protocol_version():
    """entity_status/power_mode requests use the gateway's configured DoIP version."""
    payload = bytes([0x01])
    # Configured version 0x03/0xFC instead of the 0x02/0xFD default.
    fake_sock = _FakeUdpSocket(_udp_response(0x4004, payload))
    fake_sock.data = struct.pack(">BBHI", 0x03, 0xFC, 0x4004, len(payload)) + payload

    req = DoIPSendUdpRequest(host="127.0.0.1", port=13400, message_type="power_mode")

    with (
        patch("web.api.doip_client._resolve_loopback_host", return_value="127.0.0.1"),
        patch("socket.socket", return_value=fake_sock),
        patch("web.api.doip_client.get_state") as mock_get_state,
    ):
        mock_get_state.return_value.config_manager.get_protocol_config.return_value = {
            "version": 0x03,
            "inverse_version": 0xFC,
        }
        result = _send_udp_sync(req)

    assert result["ok"] is True
    assert result["response"] == {"power_mode_status": 0x01}

    sent_data, _ = fake_sock.sent[0]
    assert sent_data == struct.pack(">BBHI", 0x03, 0xFC, 0x4003, 0)


@pytest.mark.unit
def test_send_udp_raw_default_version():
    """Raw UDP request uses the configured protocol version when none is given."""
    payload = bytes([0x01])
    fake_sock = _FakeUdpSocket(_udp_response(0x4004, payload))

    req = DoIPSendRawUdpRequest(
        host="127.0.0.1", port=13400, payload_type=0x4003, payload_hex=""
    )

    with (
        patch("web.api.doip_client._resolve_loopback_host", return_value="127.0.0.1"),
        patch("socket.socket", return_value=fake_sock),
    ):
        result = _send_raw_udp_sync(req)

    assert result["ok"] is True
    assert result["response"]["payload_type_hex"] == "0x4004"
    assert result["response"]["payload_hex"] == "01"
    assert result["response"]["parsed"] == {"power_mode_status": 0x01}

    sent_data, _ = fake_sock.sent[0]
    assert sent_data == struct.pack(">BBHI", 0x02, 0xFD, 0x4003, 0)


@pytest.mark.unit
def test_send_udp_raw_explicit_version_and_payload():
    """Raw UDP request honors an explicit version/inverse_version and payload bytes."""
    payload = b"1HGBH41JXMN109186".ljust(17, b"\x00") + bytes(16)
    fake_sock = _FakeUdpSocket(_udp_response(0x0004, payload))

    req = DoIPSendRawUdpRequest(
        host="127.0.0.1",
        port=13400,
        version=0xFF,
        inverse_version=0x00,
        payload_type=0x0001,
        payload_hex="DEADBEEF",
    )

    with (
        patch("web.api.doip_client._resolve_loopback_host", return_value="127.0.0.1"),
        patch("socket.socket", return_value=fake_sock),
    ):
        result = _send_raw_udp_sync(req)

    assert result["ok"] is True
    sent_data, _ = fake_sock.sent[0]
    assert sent_data == struct.pack(">BBHI", 0xFF, 0x00, 0x0001, 4) + bytes.fromhex(
        "DEADBEEF"
    )
    assert result["response"]["parsed"]["vin"] == "1HGBH41JXMN109186"


@pytest.mark.unit
def test_send_udp_raw_unknown_response_type_no_parsed():
    """An unknown response payload type is returned raw without a 'parsed' field."""
    fake_sock = _FakeUdpSocket(_udp_response(0x9999, bytes.fromhex("AABBCC")))

    req = DoIPSendRawUdpRequest(host="127.0.0.1", port=13400, payload_type=0x0001)

    with (
        patch("web.api.doip_client._resolve_loopback_host", return_value="127.0.0.1"),
        patch("socket.socket", return_value=fake_sock),
    ):
        result = _send_raw_udp_sync(req)

    assert result["ok"] is True
    assert result["response"]["payload_type_hex"] == "0x9999"
    assert result["response"]["payload_hex"] == "AABBCC"
    assert "parsed" not in result["response"]


@pytest.mark.unit
def test_send_udp_raw_endpoint(web_client):
    mock_result = {
        "ok": True,
        "response": {
            "version": 2,
            "version_hex": "0x02",
            "inverse_version": 253,
            "inverse_version_hex": "0xFD",
            "payload_type": 0x4004,
            "payload_type_hex": "0x4004",
            "payload_hex": "01",
            "parsed": {"power_mode_status": 1},
        },
        "log": [{"ts": 0, "event": "sent", "detail": ""}],
    }
    with patch("web.api.doip_client._send_raw_udp_sync", return_value=mock_result):
        r = web_client.post(
            "/api/client/send-udp-raw",
            json={"host": "127.0.0.1", "port": 13400, "payload_type": 16387},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["response"]["parsed"] == {"power_mode_status": 1}


@pytest.mark.unit
def test_send_udp_raw_invalid_hex(web_client):
    r = web_client.post(
        "/api/client/send-udp-raw",
        json={
            "host": "127.0.0.1",
            "port": 13400,
            "payload_type": 1,
            "payload_hex": "ZZ",
        },
    )
    assert r.status_code == 422
