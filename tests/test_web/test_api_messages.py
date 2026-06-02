"""Tests for global UDS messages catalog endpoint."""

import pytest


@pytest.mark.unit
def test_list_messages(web_client):
    r = web_client.get("/api/messages")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.unit
def test_message_has_scope_fields(web_client):
    msg = web_client.get("/api/messages").json()[0]
    assert "name" in msg
    assert "request" in msg
    assert "shared" in msg
    assert "ecu_count" in msg
    assert "used_by" in msg
    assert "used_by_names" in msg


@pytest.mark.unit
def test_service_list_has_scope_fields(web_client):
    addr = web_client.get("/api/ecus").json()[0]["target_address"]
    svc = web_client.get(f"/api/ecus/{addr}/services").json()[0]
    assert "shared" in svc
    assert "ecu_count" in svc
    assert "used_by" in svc
