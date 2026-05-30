"""Tests for the DoIP client REST and WebSocket endpoints.

The actual TCP socket call is mocked so these remain fast unit tests.
"""

import json
from unittest.mock import patch

import pytest

# The sync function we'll mock out
_TARGET = "web.api.doip_client._send_diagnostic_sync"


@pytest.mark.unit
def test_send_success(web_client):
    mock_result = {
        "ok": True,
        "response": "62F1901HGBH41JXM",
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


@pytest.mark.unit
def test_ws_send_and_receive(web_client):
    mock_result = {
        "ok": True,
        "response": "62F190AA",
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


@pytest.mark.unit
def test_ws_invalid_json(web_client):
    with web_client.websocket_connect("/api/client/ws") as ws:
        ws.send_json({"not_a_valid": "request"})  # missing required fields
        msg = ws.receive_json()
        assert msg["event"] == "error"
