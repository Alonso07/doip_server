"""Tests for UDS service CRUD endpoints."""

import pytest


def _first_ecu(client) -> int:
    return client.get("/api/ecus").json()[0]["target_address"]


@pytest.mark.unit
def test_list_services(web_client):
    addr = _first_ecu(web_client)
    r = web_client.get(f"/api/ecus/{addr}/services")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.unit
def test_service_has_name(web_client):
    addr = _first_ecu(web_client)
    svc = web_client.get(f"/api/ecus/{addr}/services").json()[0]
    assert "name" in svc
    assert "request" in svc


@pytest.mark.unit
def test_get_single_service(web_client):
    addr = _first_ecu(web_client)
    services = web_client.get(f"/api/ecus/{addr}/services").json()
    name = services[0]["name"]
    r = web_client.get(f"/api/ecus/{addr}/services/{name}")
    assert r.status_code == 200
    assert r.json()["name"] == name


@pytest.mark.unit
def test_get_missing_service(web_client):
    addr = _first_ecu(web_client)
    r = web_client.get(f"/api/ecus/{addr}/services/__no_such_service__")
    assert r.status_code == 404


@pytest.mark.unit
def test_create_and_delete_service(web_client):
    addr = _first_ecu(web_client)
    svc_name = "test_runtime_service"
    payload = {
        "request": "0x22AABB",
        "responses": ["0x62AABB00"],
        "description": "runtime test",
        "supports_functional": False,
        "no_response": False,
        "delay_ms": 0,
    }
    r = web_client.post(
        f"/api/ecus/{addr}/services?service_name={svc_name}", json=payload
    )
    assert r.status_code == 201

    # Duplicate
    r2 = web_client.post(
        f"/api/ecus/{addr}/services?service_name={svc_name}", json=payload
    )
    assert r2.status_code == 409

    # Delete
    r3 = web_client.delete(f"/api/ecus/{addr}/services/{svc_name}")
    assert r3.status_code == 200
    assert r3.json()["deleted"] is True

    r4 = web_client.get(f"/api/ecus/{addr}/services/{svc_name}")
    assert r4.status_code == 404


@pytest.mark.unit
def test_update_service(web_client):
    addr = _first_ecu(web_client)
    services = web_client.get(f"/api/ecus/{addr}/services").json()
    name = services[0]["name"]
    r = web_client.put(
        f"/api/ecus/{addr}/services/{name}", json={"description": "patched"}
    )
    assert r.status_code == 200
    assert r.json()["description"] == "patched"


@pytest.mark.unit
def test_update_missing_service(web_client):
    addr = _first_ecu(web_client)
    r = web_client.put(
        f"/api/ecus/{addr}/services/__no_such__", json={"description": "x"}
    )
    assert r.status_code == 404
