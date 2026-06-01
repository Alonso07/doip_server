"""Tests for temporary (session) vs permanent (file write-back) config edits.

These tests copy the real ``config/`` tree into an isolated temp cwd so the
repository's configuration files are never modified.
"""

import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from fastapi.testclient import TestClient

from doip_server.hierarchical_config_manager import HierarchicalConfigManager

ENGINE_ADDR = 0x01
GATEWAY_PATH = "config/gateway1.yaml"


@pytest.fixture()
def temp_config(tmp_path, monkeypatch):
    repo_config = Path(__file__).parent.parent.parent / "config"
    shutil.copytree(repo_config, tmp_path / "config")
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture()
def cm(temp_config):
    return HierarchicalConfigManager(GATEWAY_PATH)


@pytest.fixture()
def persist_client(cm):
    import web.state as state_module
    from web.app import app

    app.state.gateway_config_path = GATEWAY_PATH
    mock_state = MagicMock()
    mock_state.config_manager = cm
    mock_state.is_running = True
    mock_state.doip_server = MagicMock(running=True)
    mock_state.start_doip_server = MagicMock()
    mock_state.stop_doip_server = MagicMock()

    with patch.object(state_module, "_state", mock_state):
        with TestClient(app, raise_server_exceptions=True) as client:
            yield client


def _load(path):
    with open(path) as f:
        return yaml.safe_load(f)


# ── Config manager level ─────────────────────────────────────────────────────


@pytest.mark.unit
def test_persist_gateway_writes_file(cm):
    cm.update_gateway({"name": "PersistedGW"})
    cm.persist_gateway({"name": "PersistedGW"})
    assert _load(GATEWAY_PATH)["gateway"]["name"] == "PersistedGW"


@pytest.mark.unit
def test_persist_gateway_preserves_comments(cm):
    cm.persist_gateway({"name": "PersistedGW"})
    text = Path(GATEWAY_PATH).read_text()
    # A comment from the original file should survive a round-trip write.
    assert "# Vehicle Information" in text


@pytest.mark.unit
def test_update_without_persist_leaves_file_untouched(cm):
    before = Path(GATEWAY_PATH).read_text()
    cm.update_gateway({"name": "SessionOnlyGW"})
    assert Path(GATEWAY_PATH).read_text() == before


@pytest.mark.unit
def test_persist_ecu_update(cm):
    cm.update_ecu(ENGINE_ADDR, {"description": "Persisted desc"})
    cm.persist_ecu_update(ENGINE_ADDR, {"description": "Persisted desc"})
    path = cm._ecu_file_paths[ENGINE_ADDR]
    assert _load(path)["ecu"]["description"] == "Persisted desc"


@pytest.mark.unit
def test_persist_service_update(cm):
    name = "Engine_RPM_Read"
    cm.update_service(ENGINE_ADDR, name, {"description": "Patched RPM"})
    cm.persist_service_update(ENGINE_ADDR, name, {"description": "Patched RPM"})
    src_path, section = cm._service_source[(ENGINE_ADDR, name)]
    assert _load(src_path)[section][name]["description"] == "Patched RPM"


@pytest.mark.unit
def test_persist_new_and_delete_ecu(cm):
    addr = 0x00AB
    cm.add_ecu(
        {
            "target_address": addr,
            "name": "NewECU",
            "tester_addresses": [0x0E00],
        }
    )
    full = cm.persist_new_ecu(addr)
    assert Path(full).exists()
    ecus = _load(GATEWAY_PATH)["gateway"]["ecus"]
    assert any("ecu_newecu" in str(e) for e in ecus)

    cm.delete_ecu(addr)
    cm.persist_delete_ecu(addr)
    assert not Path(full).exists()
    ecus_after = _load(GATEWAY_PATH)["gateway"]["ecus"]
    assert not any("ecu_newecu" in str(e) for e in ecus_after)


@pytest.mark.unit
def test_persist_new_ecu_name_collision_does_not_overwrite_existing_file(cm):
    existing_ecu = Path("config/ecus/engine/ecu_engine.yaml")
    existing_services = Path("config/ecus/engine/ecu_engine_services.yaml")
    before_ecu = existing_ecu.read_text()
    before_services = existing_services.read_text()
    addr = 0x00AC
    cm.add_ecu(
        {
            "target_address": addr,
            "name": "engine",
            "tester_addresses": [0x0E00],
        }
    )

    full = Path(cm.persist_new_ecu(addr))

    assert full != existing_ecu
    assert full.exists()
    assert existing_ecu.read_text() == before_ecu
    ecus = [str(e) for e in _load(GATEWAY_PATH)["gateway"]["ecus"]]
    assert "ecus/engine/ecu_engine.yaml" in ecus
    assert full.relative_to("config").as_posix() in ecus

    service_data = {
        "request": "0x22AC01",
        "responses": ["0x62AC0100"],
        "description": "collision-safe service",
        "supports_functional": False,
        "no_response": False,
    }
    service_name = "Collision_Safe_Service"
    cm.add_service(addr, service_name, service_data)
    cm.persist_new_service(addr, service_name, service_data)

    src_path, section = cm._service_source[(addr, service_name)]
    assert Path(src_path).parent == full.parent
    assert _load(src_path)[section][service_name]["request"] == "0x22AC01"
    assert existing_services.read_text() == before_services


@pytest.mark.unit
def test_absolute_gateway_path_uses_its_config_tree(tmp_path, monkeypatch):
    repo_config = Path(__file__).parent.parent.parent / "config"
    vehicle_root = tmp_path / "vehicle"
    shutil.copytree(repo_config, vehicle_root / "config")
    outside_cwd = tmp_path / "outside"
    outside_cwd.mkdir()
    monkeypatch.chdir(outside_cwd)

    gateway_path = (vehicle_root / "config/gateway1.yaml").resolve()
    cm = HierarchicalConfigManager(str(gateway_path))

    engine_path = Path(cm._ecu_file_paths[ENGINE_ADDR]).resolve()
    assert engine_path == vehicle_root / "config/ecus/engine/ecu_engine.yaml"
    assert "Engine_RPM_Read" in cm.get_ecu_uds_services(ENGINE_ADDR)

    addr = 0x00AD
    cm.add_ecu(
        {
            "target_address": addr,
            "name": "AbsolutePathECU",
            "tester_addresses": [0x0E00],
        }
    )
    full = Path(cm.persist_new_ecu(addr)).resolve()
    service_data = {
        "request": "0x22AD01",
        "responses": ["0x62AD0100"],
        "description": "absolute-path service",
        "supports_functional": False,
        "no_response": False,
    }
    service_name = "Absolute_Path_Service"
    cm.add_service(addr, service_name, service_data)
    cm.persist_new_service(addr, service_name, service_data)

    reloaded = HierarchicalConfigManager(str(gateway_path))
    assert Path(reloaded._ecu_file_paths[addr]).resolve() == full
    assert service_name in reloaded.get_ecu_uds_services(addr)


@pytest.mark.unit
def test_persist_new_and_delete_service(cm):
    name = "Runtime_Persisted_Service"
    data = {
        "request": "0x22AB01",
        "responses": ["0x62AB0100"],
        "description": "persisted runtime svc",
        "supports_functional": False,
        "no_response": False,
    }
    cm.add_service(ENGINE_ADDR, name, data)
    cm.persist_new_service(ENGINE_ADDR, name, data)
    src_path, section = cm._service_source[(ENGINE_ADDR, name)]
    assert _load(src_path)[section][name]["request"] == "0x22AB01"

    cm.delete_service(ENGINE_ADDR, name)
    cm.persist_delete_service(ENGINE_ADDR, name)
    assert name not in _load(src_path).get(section, {})


# ── Web API level ────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_api_persist_true_writes_file(persist_client):
    r = persist_client.put("/api/gateway?persist=true", json={"name": "WebPersistGW"})
    assert r.status_code == 200
    assert r.json()["persisted"] is True
    assert _load(GATEWAY_PATH)["gateway"]["name"] == "WebPersistGW"


@pytest.mark.unit
def test_api_persist_false_is_session_only(persist_client):
    before = Path(GATEWAY_PATH).read_text()
    r = persist_client.put("/api/gateway", json={"name": "WebSessionGW"})
    assert r.status_code == 200
    assert r.json()["persisted"] is False
    # In-memory change is visible via API, but the file is untouched.
    assert (
        persist_client.get("/api/gateway").json()["gateway"]["name"] == "WebSessionGW"
    )
    assert Path(GATEWAY_PATH).read_text() == before
