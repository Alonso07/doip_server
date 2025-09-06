#!/usr/bin/env python3
"""
Configuration Manager for DoIP Server
Handles loading and parsing of YAML configuration files
"""

import yaml
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path


class DoIPConfigManager:
    """Manages DoIP server configuration from YAML files"""

    def __init__(self, config_path: str = None):
        """
        Initialize the configuration manager

        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path or self._find_default_config()
        self.config = {}
        self.logger = logging.getLogger(__name__)
        self._load_config()

    def _find_default_config(self) -> str:
        """Find the default configuration file path"""
        # Look for config in multiple locations
        possible_paths = [
            "config/doip_config.yaml",
            "doip_config.yaml",
            "../config/doip_config.yaml",
            "src/doip_server/config/doip_config.yaml",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # If no config found, create a default one
        default_config = self._create_default_config()
        return default_config

    def _create_default_config(self) -> str:
        """Create a default configuration file if none exists"""
        default_config_content = """# Default DoIP Configuration
server:
  host: "0.0.0.0"
  port: 13400
  max_connections: 5
  timeout: 30

protocol:
  version: 0x02
  inverse_version: 0xFD

addresses:
  allowed_sources: [0x0E00]
  target_addresses: [0x1000]
  default_source: 0x1000

routine_activation:
  active_type: 0x00
  reserved_by_iso: 0x00000000
  reserved_by_manufacturer: 0x00000000

uds_services:
  Read_VIN:
    request: 0x22F190
    responses:
      - 0x62F19010200112233445566778899AA
"""

        # Create config directory if it doesn't exist
        os.makedirs("config", exist_ok=True)
        config_path = "config/doip_config.yaml"

        with open(config_path, "w") as f:
            f.write(default_config_content)

        self.logger.info(f"Created default configuration file: {config_path}")
        return config_path

    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
            self.logger.info(f"Configuration loaded from: {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = self._get_fallback_config()

    def _get_fallback_config(self) -> Dict[str, Any]:
        """Get fallback configuration if YAML loading fails"""
        return {
            "server": {"host": "0.0.0.0", "port": 13400},
            "protocol": {"version": 0x02, "inverse_version": 0xFD},
            "addresses": {"allowed_sources": [0x0E00], "target_addresses": [0x1000]},
            "routine_activation": {
                "active_type": 0x00,
                "reserved_by_iso": 0x00000000,
                "reserved_by_manufacturer": 0x00000000,
            },
            "uds_services": {},
        }

    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return self.config.get("server", {})

    def get_server_binding_info(self) -> tuple[str, int]:
        """Get server host and port for binding

        Returns:
            tuple: (host, port) for server binding
        """
        server_config = self.get_server_config()
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 13400)
        return host, port

    def get_protocol_config(self) -> Dict[str, Any]:
        """Get protocol configuration"""
        return self.config.get("protocol", {})

    def get_addresses_config(self) -> Dict[str, Any]:
        """Get addresses configuration"""
        return self.config.get("addresses", {})

    def get_routine_activation_config(self) -> Dict[str, Any]:
        """Get routine activation configuration"""
        return self.config.get("routine_activation", {})

    def get_uds_services_config(self) -> Dict[str, Any]:
        """Get UDS services configuration"""
        return self.config.get("uds_services", {})

    def get_response_codes_config(self) -> Dict[str, Any]:
        """Get response codes configuration"""
        return self.config.get("response_codes", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config.get("logging", {})

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.config.get("security", {})

    def is_source_address_allowed(self, source_addr: int) -> bool:
        """Check if source address is allowed"""
        allowed_sources = self.get_addresses_config().get("allowed_sources", [])
        return source_addr in allowed_sources

    def is_target_address_valid(self, target_addr: int) -> bool:
        """Check if target address is valid"""
        target_addresses = self.get_addresses_config().get("target_addresses", [])
        return target_addr in target_addresses

    def get_default_source_address(self) -> int:
        """Get default source address for responses"""
        return self.get_addresses_config().get("default_source", 0x1000)

    def get_routine_activation_type(self) -> int:
        """Get routine activation type"""
        return self.get_routine_activation_config().get("active_type", 0x00)

    def get_routine_reserved_by_iso(self) -> int:
        """Get routine reserved by ISO"""
        return self.get_routine_activation_config().get("reserved_by_iso", 0x00000000)

    def get_routine_reserved_by_manufacturer(self) -> int:
        """Get routine reserved by manufacturer"""
        return self.get_routine_activation_config().get(
            "reserved_by_manufacturer", 0x00000000
        )

    def get_uds_service_by_request(self, request: str) -> Optional[Dict[str, Any]]:
        """Get UDS service configuration by request string"""
        services = self.get_uds_services_config()
        for service_name, service_config in services.items():
            config_request = service_config.get("request", "")
            # Handle both with and without 0x prefix
            if (
                config_request == request
                or config_request == f"0x{request}"
                or config_request.lstrip("0x") == request
            ):
                return {
                    "name": service_name,
                    "request": service_config.get("request"),
                    "responses": service_config.get("responses", []),
                }
        return None

    def get_uds_service_by_name(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get UDS service configuration by service name"""
        services = self.get_uds_services_config()
        service_config = services.get(service_name)
        if service_config:
            return {
                "name": service_name,
                "request": service_config.get("request"),
                "responses": service_config.get("responses", []),
            }
        return None

    def get_all_uds_services(self) -> Dict[str, Dict[str, Any]]:
        """Get all UDS services configuration"""
        services = self.get_uds_services_config()
        result = {}
        for service_name, service_config in services.items():
            result[service_name] = {
                "name": service_name,
                "request": service_config.get("request"),
                "responses": service_config.get("responses", []),
            }
        return result

    def get_response_code_description(self, category: str, code: int) -> str:
        """Get description for a response code"""
        response_codes = self.get_response_codes_config()
        category_codes = response_codes.get(category, {})
        return category_codes.get(code, f"Unknown response code: 0x{code:02X}")

    def reload_config(self):
        """Reload configuration from file"""
        self._load_config()
        self.logger.info("Configuration reloaded")

    def validate_config(self) -> bool:
        """Validate configuration structure"""
        required_sections = ["server", "protocol", "addresses"]

        for section in required_sections:
            if section not in self.config:
                self.logger.error(f"Missing required configuration section: {section}")
                return False

        # Validate protocol version
        protocol = self.get_protocol_config()
        if "version" not in protocol or "inverse_version" not in protocol:
            self.logger.error("Missing protocol version configuration")
            return False

        # Validate addresses
        addresses = self.get_addresses_config()
        if "target_addresses" not in addresses or not addresses["target_addresses"]:
            self.logger.error("Missing or empty target addresses configuration")
            return False

        # Validate routine activation
        routine_activation = self.get_routine_activation_config()
        if "active_type" not in routine_activation:
            self.logger.error("Missing routine activation type configuration")
            return False

        self.logger.info("Configuration validation passed")
        return True

    def get_config_summary(self) -> str:
        """Get a summary of the current configuration"""
        summary = []
        summary.append("DoIP Configuration Summary")
        summary.append("=" * 40)

        # Server config
        server = self.get_server_config()
        summary.append(
            f"Server: {server.get('host', 'N/A')}:{server.get('port', 'N/A')}"
        )

        # Protocol config
        protocol = self.get_protocol_config()
        summary.append(f"Protocol Version: 0x{protocol.get('version', 'N/A'):02X}")

        # Addresses
        addresses = self.get_addresses_config()
        summary.append(
            f"Target Addresses: {len(addresses.get('target_addresses', []))}"
        )
        summary.append(f"Allowed Sources: {len(addresses.get('allowed_sources', []))}")

        # Routines
        routines = self.get_routine_activation_config()
        summary.append(
            f"Routine Activation Type: 0x{routines.get('active_type', 0x00):02X}"
        )

        # UDS Services
        uds_services = self.get_uds_services_config()
        summary.append(f"UDS Services: {len(uds_services)}")

        return "\n".join(summary)
