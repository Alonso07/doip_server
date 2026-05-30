"""Tests for ECU CRUD endpoints."""

import pytest


@pytest.mark.unit
def test_list_ecus(web_client):
    r = web_client.get("/api/ecus")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.unit
def test_ecu_has_required_fields(web_client):
    ecu = web_client.get("/api/ecus").json()[0]
    for field in ("target_address", "target_address_hex", "name", "service_count"):
        assert field in ecu, f"Missing field: {field}"


@pytest.mark.unit
def test_get_single_ecu(web_client):
    ecus = web_client.get("/api/ecus").json()
    addr = ecus[0]["target_address"]
    r = web_client.get(f"/api/ecus/{addr}")
    assert r.status_code == 200
    assert r.json()["target_address"] == addr


@pytest.mark.unit
def test_get_missing_ecu(web_client):
    r = web_client.get("/api/ecus/9999")
    assert r.status_code == 404


@pytest.mark.unit
def test_create_and_delete_ecu(web_client):
    new_ecu = {
        "target_address": 0x00FF,
        "name": "TestECU",
        "tester_addresses": [0x0E00],
    }
    r = web_client.post("/api/ecus", json=new_ecu)
    assert r.status_code == 201
    assert r.json()["name"] == "TestECU"

    # Duplicate should be rejected
    r2 = web_client.post("/api/ecus", json=new_ecu)
    assert r2.status_code == 409

    # Delete
    r3 = web_client.delete(f"/api/ecus/{new_ecu['target_address']}")
    assert r3.status_code == 204

    # After delete, 404
    r4 = web_client.get(f"/api/ecus/{new_ecu['target_address']}")
    assert r4.status_code == 404


@pytest.mark.unit
def test_update_ecu(web_client):
    ecus = web_client.get("/api/ecus").json()
    addr = ecus[0]["target_address"]
    r = web_client.put(f"/api/ecus/{addr}", json={"description": "updated"})
    assert r.status_code == 200
    assert r.json()["description"] == "updated"


@pytest.mark.unit
def test_update_missing_ecu(web_client):
    r = web_client.put("/api/ecus/9998", json={"name": "X"})
    assert r.status_code == 404


@pytest.mark.unit
def test_delete_missing_ecu(web_client):
    r = web_client.delete("/api/ecus/9997")
    assert r.status_code == 404
