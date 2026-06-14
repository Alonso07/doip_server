"""JSON Schema validation for DoIP server YAML configuration files.

Validates gateway, ECU, and UDS service configuration files against the
JSON Schema documents in ``src/doip_server/schemas/``.
"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List

import yaml
from jsonschema import Draft202012Validator

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")

GATEWAY_SCHEMA_FILE = "gateway.schema.json"
ECU_SCHEMA_FILE = "ecu.schema.json"
UDS_SERVICES_SCHEMA_FILE = "uds_services.schema.json"

# Mirrors the patterns in schemas/uds_services.schema.json, for validating
# UDS request/response strings entered through the web UI.
HEX_BYTES_RE = re.compile(r"^0[xX]([0-9A-Fa-f]{2})+$")
REQUEST_RE = re.compile(r"^(0[xX]([0-9A-Fa-f]{2})+|regex:.+)$")
RESPONSE_RE = re.compile(r"^0[xX]([0-9A-Fa-f]{2}|\{[^{}]*\})+$")

_schema_cache: Dict[str, Dict[str, Any]] = {}


def load_schema(schema_file: str) -> Dict[str, Any]:
    """Load and cache a JSON schema document from ``SCHEMA_DIR``."""
    if schema_file not in _schema_cache:
        path = os.path.join(SCHEMA_DIR, schema_file)
        with open(path, "r") as f:
            _schema_cache[schema_file] = json.load(f)
    return _schema_cache[schema_file]


@dataclass
class FileValidationResult:
    """Result of validating a single YAML file against a schema."""

    path: str
    schema_file: str
    errors: List[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_yaml_data(data: Any, schema_file: str) -> List[str]:
    """Validate already-loaded YAML data against *schema_file*.

    Returns a list of human-readable error messages (empty if valid).
    """
    validator = Draft202012Validator(load_schema(schema_file))
    errors = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        location = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{location}: {err.message}")
    return errors


def validate_yaml_file(path: str, schema_file: str) -> FileValidationResult:
    """Load *path* as YAML and validate it against *schema_file*."""
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as exc:
        return FileValidationResult(path, schema_file, [f"Failed to load: {exc}"])

    return FileValidationResult(
        path, schema_file, validate_yaml_data(data or {}, schema_file)
    )


def validate_config_tree(config_manager) -> List[FileValidationResult]:
    """Validate every config file known to *config_manager* against its schema.

    Args:
        config_manager: A ``HierarchicalConfigManager`` instance.

    Returns:
        List[FileValidationResult]: One result per gateway, ECU, and UDS
        service file currently loaded.
    """
    gateway_path, ecu_paths, service_paths = config_manager.get_config_file_paths()

    results: List[FileValidationResult] = []
    if gateway_path:
        results.append(validate_yaml_file(gateway_path, GATEWAY_SCHEMA_FILE))
    for ecu_path in ecu_paths:
        results.append(validate_yaml_file(ecu_path, ECU_SCHEMA_FILE))
    for service_path in service_paths:
        results.append(validate_yaml_file(service_path, UDS_SERVICES_SCHEMA_FILE))

    return results
