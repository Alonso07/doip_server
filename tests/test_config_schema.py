"""Tests for the JSON Schema config validator (doip_server.config_schema)."""

import pytest

from doip_server.config_schema import (
    ECU_SCHEMA_FILE,
    GATEWAY_SCHEMA_FILE,
    UDS_SERVICES_SCHEMA_FILE,
    validate_config_tree,
    validate_yaml_data,
    validate_yaml_file,
)
from doip_server.hierarchical_config_manager import HierarchicalConfigManager


@pytest.mark.unit
def test_valid_gateway_data_passes():
    data = {
        "gateway": {
            "network": {"host": "0.0.0.0", "port": 13400},
            "protocol": {"version": 0x02, "inverse_version": 0xFD},
        }
    }
    assert validate_yaml_data(data, GATEWAY_SCHEMA_FILE) == []


@pytest.mark.unit
def test_invalid_gateway_data_missing_required():
    data = {"gateway": {"network": {"host": "0.0.0.0", "port": 13400}}}
    errors = validate_yaml_data(data, GATEWAY_SCHEMA_FILE)
    assert errors
    assert any("protocol" in e for e in errors)


@pytest.mark.unit
def test_invalid_ecu_data_missing_target_address():
    data = {"ecu": {"name": "Engine"}}
    errors = validate_yaml_data(data, ECU_SCHEMA_FILE)
    assert any("target_address" in e for e in errors)


@pytest.mark.unit
def test_valid_uds_service_hex_request():
    data = {
        "common_services": {
            "Test_Service": {
                "request": "0x22F190",
                "responses": ["0x62F19012345678"],
            }
        }
    }
    assert validate_yaml_data(data, UDS_SERVICES_SCHEMA_FILE) == []


@pytest.mark.unit
def test_invalid_uds_service_bad_hex_request():
    data = {
        "common_services": {
            "Test_Service": {
                "request": "0x22GG",
                "responses": ["0x62F190"],
            }
        }
    }
    errors = validate_yaml_data(data, UDS_SERVICES_SCHEMA_FILE)
    assert errors
    assert any("request" in e for e in errors)


@pytest.mark.unit
def test_uds_service_regex_request_is_valid():
    data = {
        "common_services": {
            "Test_Service": {
                "request": "regex:^10[0-9A-F]{2}$",
                "responses": ["0x5010"],
            }
        }
    }
    assert validate_yaml_data(data, UDS_SERVICES_SCHEMA_FILE) == []


@pytest.mark.unit
def test_uds_service_mirroring_response_is_valid():
    data = {
        "specific_services": {
            "Test_Mirroring": {
                "request": "0x220C01",
                "responses": ["0x620C01{request[2:4]}"],
            }
        }
    }
    assert validate_yaml_data(data, UDS_SERVICES_SCHEMA_FILE) == []


@pytest.mark.unit
def test_validate_yaml_file_missing_file():
    result = validate_yaml_file("config/does_not_exist.yaml", GATEWAY_SCHEMA_FILE)
    assert not result.valid
    assert "Failed to load" in result.errors[0]


@pytest.mark.unit
def test_validate_config_tree_for_real_config():
    cm = HierarchicalConfigManager("config/gateway1.yaml")
    results = validate_config_tree(cm)
    assert results
    for result in results:
        assert result.valid, f"{result.path}: {result.errors}"


@pytest.mark.unit
def test_get_config_file_paths():
    cm = HierarchicalConfigManager("config/gateway1.yaml")
    gateway_path, ecu_paths, service_paths = cm.get_config_file_paths()

    assert gateway_path == "config/gateway1.yaml"
    assert len(ecu_paths) == len(cm.ecu_configs)
    assert all(p.endswith(".yaml") for p in ecu_paths)
    assert service_paths
    assert all(p.endswith(".yaml") for p in service_paths)


@pytest.mark.unit
def test_validate_configs_fails_on_schema_error(tmp_path, monkeypatch):
    cm = HierarchicalConfigManager("config/gateway1.yaml")

    # validate_config_tree validates files on disk, so point it at a file
    # containing an invalid UDS service definition.
    bad_file = tmp_path / "bad_services.yaml"
    bad_file.write_text("common_services:\n  Bad_Service:\n    request: 'not_hex'\n")
    monkeypatch.setattr(
        cm,
        "get_config_file_paths",
        lambda: ("config/gateway1.yaml", [], [str(bad_file)]),
    )

    assert cm.validate_configs() is False
