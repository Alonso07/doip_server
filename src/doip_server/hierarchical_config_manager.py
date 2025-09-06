#!/usr/bin/env python3
"""
Hierarchical Configuration Manager for DoIP Server
Handles loading and parsing of multiple YAML configuration files with ECU hierarchy
"""

import yaml
import os
import logging
from typing import Dict, List, Any, Optional, Set
from pathlib import Path


class HierarchicalConfigManager:
    """Manages DoIP server configuration from multiple YAML files with ECU hierarchy"""

    def __init__(self, gateway_config_path: str = None):
        """
        Initialize the hierarchical configuration manager

        Args:
            gateway_config_path: Path to the gateway configuration file
        """
        self.gateway_config_path = (
            gateway_config_path or self._find_default_gateway_config()
        )
        self.gateway_config = {}
        self.ecu_configs = {}  # target_address -> ecu_config
        self.uds_services = {}  # service_name -> service_config
        self.logger = logging.getLogger(__name__)
        self._load_all_configs()

    def _find_default_gateway_config(self) -> str:
        """Find the default gateway configuration file path"""
        possible_paths = [
            "config/gateway1.yaml",
            "gateway1.yaml",
            "../config/gateway1.yaml",
            "src/doip_server/config/gateway1.yaml",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # If no config found, create a default one
        default_config = self._create_default_gateway_config()
        return default_config

    def _create_default_gateway_config(self) -> str:
        """Create a default gateway configuration file if none exists"""
        default_config_content = """# Default Gateway Configuration
gateway:
  name: "DefaultGateway"
  description: "Default DoIP Gateway"
  network:
    host: "0.0.0.0"
    port: 13400
    max_connections: 5
    timeout: 30
  protocol:
    version: 0x02
    inverse_version: 0xFD
  ecus:
    - "ecu_engine.yaml"
"""

        # Create config directory if it doesn't exist
        os.makedirs("config", exist_ok=True)
        config_path = "config/gateway1.yaml"

        with open(config_path, "w") as f:
            f.write(default_config_content)

        self.logger.info(f"Created default gateway configuration file: {config_path}")
        return config_path

    def _load_all_configs(self):
        """Load all configuration files"""
        try:
            # Load gateway configuration
            self._load_gateway_config()

            # Load ECU configurations
            self._load_ecu_configs()

            # Load UDS services
            self._load_uds_services()

            self.logger.info("All configurations loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load configurations: {e}")
            self._load_fallback_configs()

    def _load_gateway_config(self):
        """Load gateway configuration from YAML file"""
        try:
            with open(self.gateway_config_path, "r") as f:
                self.gateway_config = yaml.safe_load(f)
            self.logger.info(
                f"Gateway configuration loaded from: {self.gateway_config_path}"
            )
        except Exception as e:
            self.logger.error(f"Failed to load gateway configuration: {e}")
            self.gateway_config = self._get_fallback_gateway_config()

    def _load_ecu_configs(self):
        """Load all ECU configurations referenced by the gateway"""
        gateway_config = self.gateway_config.get("gateway", {})
        ecu_files = gateway_config.get("ecus", [])

        for ecu_file in ecu_files:
            try:
                ecu_path = self._find_ecu_config_path(ecu_file)
                if ecu_path and os.path.exists(ecu_path):
                    with open(ecu_path, "r") as f:
                        ecu_config = yaml.safe_load(f)

                    ecu_info = ecu_config.get("ecu", {})
                    target_address = ecu_info.get("target_address")

                    if target_address is not None:
                        self.ecu_configs[target_address] = ecu_config
                        self.logger.info(
                            f"ECU configuration loaded: {ecu_file} -> 0x{target_address:04X}"
                        )
                    else:
                        self.logger.warning(
                            f"ECU configuration missing target_address: {ecu_file}"
                        )
                else:
                    self.logger.warning(f"ECU configuration file not found: {ecu_file}")
            except Exception as e:
                self.logger.error(f"Failed to load ECU configuration {ecu_file}: {e}")

    def _find_ecu_config_path(self, ecu_file: str) -> str:
        """Find the full path to an ECU configuration file"""
        possible_paths = [
            f"config/{ecu_file}",
            ecu_file,
            f"../config/{ecu_file}",
            f"src/doip_server/config/{ecu_file}",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _load_uds_services(self):
        """Load UDS services configuration"""
        try:
            uds_services_path = self._find_uds_services_path()
            if uds_services_path and os.path.exists(uds_services_path):
                with open(uds_services_path, "r") as f:
                    uds_config = yaml.safe_load(f)

                # Load common services
                common_services = uds_config.get("common_services", {})
                for service_name, service_config in common_services.items():
                    self.uds_services[service_name] = service_config

                # Load engine services
                engine_services = uds_config.get("engine_services", {})
                for service_name, service_config in engine_services.items():
                    self.uds_services[service_name] = service_config

                # Load transmission services
                transmission_services = uds_config.get("transmission_services", {})
                for service_name, service_config in transmission_services.items():
                    self.uds_services[service_name] = service_config

                # Load ABS services
                abs_services = uds_config.get("abs_services", {})
                for service_name, service_config in abs_services.items():
                    self.uds_services[service_name] = service_config

                self.logger.info(
                    f"UDS services loaded: {len(self.uds_services)} services"
                )
            else:
                self.logger.warning("UDS services configuration file not found")
        except Exception as e:
            self.logger.error(f"Failed to load UDS services: {e}")

    def _find_uds_services_path(self) -> str:
        """Find the UDS services configuration file path"""
        possible_paths = [
            "config/uds_services.yaml",
            "uds_services.yaml",
            "../config/uds_services.yaml",
            "src/doip_server/config/uds_services.yaml",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _load_fallback_configs(self):
        """Load fallback configurations if loading fails"""
        self.gateway_config = self._get_fallback_gateway_config()
        self.ecu_configs = {}
        self.uds_services = {}

    def _get_fallback_gateway_config(self) -> Dict[str, Any]:
        """Get fallback gateway configuration"""
        return {
            "gateway": {
                "name": "FallbackGateway",
                "network": {"host": "0.0.0.0", "port": 13400},
                "protocol": {"version": 0x02, "inverse_version": 0xFD},
                "ecus": [],
            }
        }

    # Gateway configuration methods
    def get_gateway_config(self) -> Dict[str, Any]:
        """Get gateway configuration"""
        return self.gateway_config.get("gateway", {})

    def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration"""
        return self.get_gateway_config().get("network", {})

    def get_server_binding_info(self) -> tuple[str, int]:
        """Get server host and port for binding"""
        network_config = self.get_network_config()
        host = network_config.get("host", "0.0.0.0")
        port = network_config.get("port", 13400)
        return host, port

    def get_protocol_config(self) -> Dict[str, Any]:
        """Get protocol configuration"""
        return self.get_gateway_config().get("protocol", {})

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.gateway_config.get("logging", {})

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.gateway_config.get("security", {})

    def get_response_codes_config(self) -> Dict[str, Any]:
        """Get response codes configuration"""
        return self.get_gateway_config().get("response_codes", {})

    # ECU configuration methods
    def get_all_ecu_addresses(self) -> List[int]:
        """Get all configured ECU target addresses"""
        return list(self.ecu_configs.keys())

    def get_ecu_config(self, target_address: int) -> Optional[Dict[str, Any]]:
        """Get ECU configuration by target address"""
        return self.ecu_configs.get(target_address)

    def get_ecu_tester_addresses(self, target_address: int) -> List[int]:
        """Get allowed tester addresses for a specific ECU"""
        ecu_config = self.get_ecu_config(target_address)
        if ecu_config:
            ecu_info = ecu_config.get("ecu", {})
            return ecu_info.get("tester_addresses", [])
        return []

    def is_source_address_allowed(
        self, source_addr: int, target_addr: int = None
    ) -> bool:
        """Check if source address is allowed for a specific ECU or any ECU"""
        if target_addr is not None:
            # Check specific ECU
            allowed_sources = self.get_ecu_tester_addresses(target_addr)
            return source_addr in allowed_sources
        else:
            # Check all ECUs
            for ecu_addr in self.get_all_ecu_addresses():
                if source_addr in self.get_ecu_tester_addresses(ecu_addr):
                    return True
            return False

    def is_target_address_valid(self, target_addr: int) -> bool:
        """Check if target address is valid (has ECU configuration)"""
        return target_addr in self.ecu_configs

    def get_ecu_uds_services(self, target_address: int) -> Dict[str, Any]:
        """Get UDS services available for a specific ECU"""
        ecu_config = self.get_ecu_config(target_address)
        if not ecu_config:
            return {}

        ecu_info = ecu_config.get("ecu", {})
        uds_config = ecu_info.get("uds_services", {})

        # Get common services
        common_services = uds_config.get("common_services", [])
        specific_services = uds_config.get("specific_services", [])

        # Combine all service names
        all_service_names = common_services + specific_services

        # Get actual service configurations
        ecu_services = {}
        for service_name in all_service_names:
            if service_name in self.uds_services:
                ecu_services[service_name] = self.uds_services[service_name]
            else:
                self.logger.warning(
                    f"Service {service_name} not found in UDS services for ECU 0x{target_address:04X}"
                )

        return ecu_services

    def get_uds_service_by_request(
        self, request: str, target_address: int = None
    ) -> Optional[Dict[str, Any]]:
        """Get UDS service configuration by request string for a specific ECU"""
        if target_address is not None:
            # Search in ECU-specific services
            ecu_services = self.get_ecu_uds_services(target_address)
            for service_name, service_config in ecu_services.items():
                config_request = service_config.get("request", "")
                if self._match_request(config_request, request):
                    return {
                        "name": service_name,
                        "request": service_config.get("request"),
                        "responses": service_config.get("responses", []),
                        "description": service_config.get("description", ""),
                        "ecu_address": target_address,
                    }
        else:
            # Search in all services
            for service_name, service_config in self.uds_services.items():
                config_request = service_config.get("request", "")
                if self._match_request(config_request, request):
                    return {
                        "name": service_name,
                        "request": service_config.get("request"),
                        "responses": service_config.get("responses", []),
                        "description": service_config.get("description", ""),
                        "ecu_address": None,
                    }
        return None

    def _match_request(self, config_request: str, request: str) -> bool:
        """Check if a request matches a configured request"""
        # Handle both with and without 0x prefix
        if config_request == request:
            return True
        if config_request == f"0x{request}":
            return True
        if config_request.lstrip("0x") == request:
            return True
        if f"0x{config_request}" == request:
            return True
        return False

    def get_routine_activation_config(self, target_address: int) -> Dict[str, Any]:
        """Get routine activation configuration for a specific ECU"""
        ecu_config = self.get_ecu_config(target_address)
        if ecu_config:
            ecu_info = ecu_config.get("ecu", {})
            return ecu_info.get("routine_activation", {})
        return {}

    def get_response_code_description(self, category: str, code: int) -> str:
        """Get description for a response code"""
        response_codes = self.get_response_codes_config()
        category_codes = response_codes.get(category, {})
        return category_codes.get(code, f"Unknown response code: 0x{code:02X}")

    def reload_configs(self):
        """Reload all configuration files"""
        self._load_all_configs()
        self.logger.info("All configurations reloaded")

    def validate_configs(self) -> bool:
        """Validate all configuration files"""
        # Validate gateway configuration
        if not self.gateway_config:
            self.logger.error("Gateway configuration is empty")
            return False

        gateway = self.get_gateway_config()
        if not gateway:
            self.logger.error("Missing gateway configuration")
            return False

        # Validate network configuration
        network = self.get_network_config()
        if "host" not in network or "port" not in network:
            self.logger.error("Missing network configuration")
            return False

        # Validate protocol configuration
        protocol = self.get_protocol_config()
        if "version" not in protocol or "inverse_version" not in protocol:
            self.logger.error("Missing protocol configuration")
            return False

        # Validate ECU configurations
        if not self.ecu_configs:
            self.logger.warning("No ECU configurations loaded")
        else:
            for target_addr, ecu_config in self.ecu_configs.items():
                ecu_info = ecu_config.get("ecu", {})
                if "target_address" not in ecu_info:
                    self.logger.error(f"ECU 0x{target_addr:04X} missing target_address")
                    return False
                if "tester_addresses" not in ecu_info:
                    self.logger.error(
                        f"ECU 0x{target_addr:04X} missing tester_addresses"
                    )
                    return False

        # Validate UDS services
        if not self.uds_services:
            self.logger.warning("No UDS services loaded")

        self.logger.info("Configuration validation passed")
        return True

    def get_config_summary(self) -> str:
        """Get a summary of the current configuration"""
        summary = []
        summary.append("Hierarchical DoIP Configuration Summary")
        summary.append("=" * 50)

        # Gateway config
        gateway = self.get_gateway_config()
        network = self.get_network_config()
        summary.append(f"Gateway: {gateway.get('name', 'Unknown')}")
        summary.append(
            f"Network: {network.get('host', 'N/A')}:{network.get('port', 'N/A')}"
        )

        # Protocol config
        protocol = self.get_protocol_config()
        summary.append(f"Protocol Version: 0x{protocol.get('version', 'N/A'):02X}")

        # ECU configs
        summary.append(f"Configured ECUs: {len(self.ecu_configs)}")
        for target_addr in self.get_all_ecu_addresses():
            ecu_config = self.get_ecu_config(target_addr)
            ecu_info = ecu_config.get("ecu", {}) if ecu_config else {}
            summary.append(
                f"  - 0x{target_addr:04X}: {ecu_info.get('name', 'Unknown')}"
            )

        # UDS services
        summary.append(f"UDS Services: {len(self.uds_services)}")

        return "\n".join(summary)
