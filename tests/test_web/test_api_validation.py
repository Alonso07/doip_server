"""Tests for GET /api/validate."""

import pytest


@pytest.mark.unit
def test_validate_endpoint_ok(web_client):
    r = web_client.get("/api/validate")
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is True
    assert data["semantic_valid"] is True
    assert isinstance(data["files"], list)
    assert data["files"]
    for entry in data["files"]:
        assert entry["valid"] is True
        assert entry["errors"] == []
