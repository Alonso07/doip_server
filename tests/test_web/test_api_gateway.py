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
