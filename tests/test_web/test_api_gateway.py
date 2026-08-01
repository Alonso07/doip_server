"""Tests for GET /api/gateway and PUT /api/gateway."""

import pytest


@pytest.mark.unit
def test_get_gateway(web_client):
    r = web_client.get("/api/gateway")
    assert r.status_code == 200
    data = r.json()
    assert "gateway" in data
    assert "network" in data
    assert "protocol" in data


@pytest.mark.unit
def test_get_gateway_network_fields(web_client):
    network = web_client.get("/api/gateway").json()["network"]
    assert "host" in network
    assert "port" in network


@pytest.mark.unit
def test_update_gateway_name(web_client):
    r = web_client.put("/api/gateway", json={"name": "TestGW"})
    assert r.status_code == 200
    assert r.json()["gateway"]["name"] == "TestGW"


@pytest.mark.unit
def test_update_gateway_empty_body_rejected(web_client):
    r = web_client.put("/api/gateway", json={})
    assert r.status_code == 400


@pytest.mark.unit
def test_update_gateway_protocol_version_auto_syncs_inverse(web_client):
    r = web_client.put("/api/gateway", json={"protocol": {"version": 0x03}})
    assert r.status_code == 200
    protocol = r.json()["gateway"]["protocol"]
    assert protocol["version"] == 0x03
    assert protocol["inverse_version"] == 0xFF - 0x03


@pytest.mark.unit
def test_update_gateway_protocol_explicit_inverse_version_kept(web_client):
    r = web_client.put(
        "/api/gateway", json={"protocol": {"version": 0x03, "inverse_version": 0x10}}
    )
    assert r.status_code == 200
    protocol = r.json()["gateway"]["protocol"]
    assert protocol["version"] == 0x03
    assert protocol["inverse_version"] == 0x10


@pytest.mark.unit
def test_update_gateway_rejects_out_of_range_protocol_version(web_client):
    """Out-of-range protocol bytes must not brick live DoIP header packing."""
    before = web_client.get("/api/gateway").json()["protocol"]
    r = web_client.put("/api/gateway", json={"protocol": {"version": 999}})
    assert r.status_code == 422
    after = web_client.get("/api/gateway").json()["protocol"]
    assert after == before


@pytest.mark.unit
def test_update_gateway_null_protocol_version_does_not_brick_config(web_client):
    """JSON null must not store None into live protocol.version (breaks DoIP packing)."""
    before = web_client.get("/api/gateway").json()["protocol"]
    r = web_client.put(
        "/api/gateway", json={"protocol": {"version": None, "inverse_version": 0xFD}}
    )
    assert r.status_code == 200
    after = web_client.get("/api/gateway").json()["protocol"]
    assert after["version"] == before["version"]
    assert isinstance(after["version"], int)
    assert 0x00 <= after["version"] <= 0xFF


@pytest.mark.unit
def test_update_gateway_rejects_non_integer_protocol_version(web_client):
    before = web_client.get("/api/gateway").json()["protocol"]
    r = web_client.put("/api/gateway", json={"protocol": {"version": "GG"}})
    assert r.status_code == 422
    after = web_client.get("/api/gateway").json()["protocol"]
    assert after == before


@pytest.mark.unit
def test_config_manager_rejects_invalid_protocol_version(config_manager):
    before = dict(config_manager.get_protocol_config())
    with pytest.raises(ValueError, match="protocol.version"):
        config_manager.update_gateway({"protocol": {"version": 999}})
    assert config_manager.get_protocol_config() == before
