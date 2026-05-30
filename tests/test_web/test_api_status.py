"""Tests for GET /api/status."""

import pytest


@pytest.mark.unit
def test_status_running(web_client):
    r = web_client.get("/api/status")
    assert r.status_code == 200
    data = r.json()
    assert data["running"] is True
    assert "ecu_count" in data
    assert "service_count" in data


@pytest.mark.unit
def test_status_fields(web_client):
    data = web_client.get("/api/status").json()
    assert isinstance(data["ecu_count"], int)
    assert data["ecu_count"] > 0
