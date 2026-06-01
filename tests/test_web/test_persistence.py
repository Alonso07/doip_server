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

    cm.persist_delete_ecu(addr)
    cm.delete_ecu(addr)
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
def test_session_delete_recreate_does_not_reuse_previous_ecu_source(cm):
    existing_ecu = Path(cm._ecu_file_paths[ENGINE_ADDR])
    before_ecu = existing_ecu.read_text()

    cm.delete_ecu(ENGINE_ADDR)
    cm.add_ecu(
        {
            "target_address": ENGINE_ADDR,
            "name": "Replacement_ECU",
            "tester_addresses": [0x0E00],
        }
    )

    with pytest.raises(KeyError, match="No source file tracked"):
        cm.persist_ecu_update(ENGINE_ADDR, {"name": "Replacement_ECU"})
    with pytest.raises(ValueError, match="already references"):
        cm.persist_new_ecu(ENGINE_ADDR)
    assert existing_ecu.read_text() == before_ecu


@pytest.mark.unit
def test_persist_delete_then_recreate_same_address_uses_new_source(cm):
    old_ecu = Path(cm._ecu_file_paths[ENGINE_ADDR])

    cm.persist_delete_ecu(ENGINE_ADDR)
    cm.delete_ecu(ENGINE_ADDR)
    cm.add_ecu(
        {
            "target_address": ENGINE_ADDR,
            "name": "Recreated_Engine",
            "tester_addresses": [0x0E00],
        }
    )
    full = Path(cm.persist_new_ecu(ENGINE_ADDR))

    assert not old_ecu.exists()
    assert full.exists()
    assert full != old_ecu
    assert _load(full)["ecu"]["name"] == "Recreated_Engine"


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
def test_absolute_gateway_path_ignores_colliding_cwd_service_tree(
    tmp_path, monkeypatch
):
    repo_config = Path(__file__).parent.parent.parent / "config"
    vehicle_root = tmp_path / "vehicle"
    cwd_root = tmp_path / "cwd"
    shutil.copytree(repo_config, vehicle_root / "config")
    shutil.copytree(repo_config, cwd_root / "config")
    monkeypatch.chdir(cwd_root)

    vehicle_services = vehicle_root / "config/ecus/engine/ecu_engine_services.yaml"
    cwd_services = cwd_root / "config/ecus/engine/ecu_engine_services.yaml"
    vehicle_text = vehicle_services.read_text()
    cwd_text = cwd_services.read_text()
    vehicle_services.write_text(
        vehicle_text.replace(
            'description: "Read engine RPM"', 'description: "vehicle tree RPM"'
        )
    )
    cwd_services.write_text(
        cwd_text.replace(
            'description: "Read engine RPM"', 'description: "cwd tree RPM"'
        )
    )

    gateway_path = (vehicle_root / "config/gateway1.yaml").resolve()
    cm = HierarchicalConfigManager(str(gateway_path))

    rpm = cm.get_ecu_uds_services(ENGINE_ADDR)["Engine_RPM_Read"]
    assert rpm["description"] == "vehicle tree RPM"

    cm.update_service(ENGINE_ADDR, "Engine_RPM_Read", {"description": "Patched RPM"})
    cm.persist_service_update(
        ENGINE_ADDR, "Engine_RPM_Read", {"description": "Patched RPM"}
    )

    assert (
        _load(vehicle_services)["specific_services"]["Engine_RPM_Read"]["description"]
        == "Patched RPM"
    )
    assert (
        _load(cwd_services)["specific_services"]["Engine_RPM_Read"]["description"]
        == "cwd tree RPM"
    )


@pytest.mark.unit
def test_persist_delete_ecu_only_removes_exact_gateway_reference(cm):
    gateway_data = _load(GATEWAY_PATH)
    gateway_data["gateway"]["ecus"].extend(
        [
            "ecus/custom_a/ecu_duplicate.yaml",
            "ecus/custom_b/ecu_duplicate.yaml",
        ]
    )
    with open(GATEWAY_PATH, "w") as f:
        yaml.safe_dump(gateway_data, f)

    custom_a = Path("config/ecus/custom_a/ecu_duplicate.yaml")
    custom_b = Path("config/ecus/custom_b/ecu_duplicate.yaml")
    custom_a.parent.mkdir(parents=True)
    custom_b.parent.mkdir(parents=True)
    custom_a.write_text(
        yaml.safe_dump(
            {"ecu": {"target_address": 0x00B1, "name": "A", "tester_addresses": []}}
        )
    )
    custom_b.write_text(
        yaml.safe_dump(
            {"ecu": {"target_address": 0x00B2, "name": "B", "tester_addresses": []}}
        )
    )

    cm.reload_configs()
    cm.persist_delete_ecu(0x00B1)
    cm.delete_ecu(0x00B1)

    ecus = [str(e) for e in _load(GATEWAY_PATH)["gateway"]["ecus"]]
    assert "ecus/custom_a/ecu_duplicate.yaml" not in ecus
    assert "ecus/custom_b/ecu_duplicate.yaml" in ecus


@pytest.mark.unit
def test_persist_new_service_requires_persisted_ecu(cm):
    addr = 0x00AE
    service_data = {
        "request": "0x22AE01",
        "responses": ["0x62AE0100"],
        "description": "orphan prevention",
        "supports_functional": False,
        "no_response": False,
    }
    cm.add_ecu(
        {
            "target_address": addr,
            "name": "RuntimeOnlyECU",
            "tester_addresses": [0x0E00],
        }
    )
    cm.add_service(addr, "Runtime_Only_Service", service_data)

    with pytest.raises(KeyError, match="No source file tracked"):
        cm.persist_new_service(addr, "Runtime_Only_Service", service_data)


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


@pytest.mark.unit
def test_api_persist_delete_removes_file_before_runtime_state(persist_client):
    engine_path = Path("config/ecus/engine/ecu_engine.yaml")

    r = persist_client.delete(f"/api/ecus/{ENGINE_ADDR}?persist=true")

    assert r.status_code == 200
    assert r.json()["persisted"] is True
    assert not engine_path.exists()
    ecus = [str(e) for e in _load(GATEWAY_PATH)["gateway"]["ecus"]]
    assert "ecus/engine/ecu_engine.yaml" not in ecus
