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
