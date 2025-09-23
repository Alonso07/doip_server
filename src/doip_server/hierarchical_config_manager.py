#!/usr/bin/env python3
"""
Hierarchical Configuration Manager for DoIP Server
Handles loading and parsing of multiple YAML configuration files with ECU hierarchy
"""

import logging
import os
from typing import Any, Dict, List, Optional

import yaml
import re


class HierarchicalConfigManager:
    """Manages DoIP server configuration from multiple YAML files with ECU hierarchy.

    This class provides a comprehensive configuration management system for the DoIP server,
    supporting hierarchical configuration loading from multiple YAML files. It handles:

    - Gateway configuration (network, protocol, logging settings)
    - ECU configurations (target addresses, tester addresses, UDS services)
    - UDS service definitions (common and ECU-specific services)
    - Configuration validation and fallback mechanisms
    - Dynamic configuration reloading

    The hierarchical structure allows for:
    - Centralized gateway configuration
    - ECU-specific configurations in separate files
    - Service definitions that can be shared or ECU-specific
    - Flexible addressing schemes (physical and functional)

    Attributes:
        gateway_config_path (str): Path to the main gateway configuration file
        gateway_config (Dict[str, Any]): Loaded gateway configuration
        ecu_configs (Dict[int, Dict[str, Any]]): ECU configurations by target address
        uds_services (Dict[str, Dict[str, Any]]): UDS service definitions
        logger (logging.Logger): Logger instance for this manager
    """

    def __init__(self, gateway_config_path: str = None):
        """Initialize the hierarchical configuration manager.

        This constructor initializes the configuration manager and loads all
        configuration files. If no gateway configuration path is provided,
        it will attempt to find a default configuration file or create one.

        Args:
            gateway_config_path (str, optional): Path to the gateway configuration file.
                If None, the manager will search for default configuration files
                in common locations or create a default configuration.

        Raises:
            FileNotFoundError: If no configuration files can be found or created
            yaml.YAMLError: If configuration files contain invalid YAML
            Exception: If configuration loading fails and fallback also fails

        Note:
            The initialization process:
            1. Sets up the gateway configuration path
            2. Initializes empty configuration dictionaries
            3. Sets up logging
            4. Loads all configuration files (gateway, ECUs, UDS services)
            5. Falls back to default configurations if loading fails
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
        """Find the default gateway configuration file path.

        This method searches for gateway configuration files in common locations
        in the following order of priority:
        1. config/gateway1.yaml (relative to current working directory)
        2. gateway1.yaml (in current working directory)
        3. ../config/gateway1.yaml (parent directory config)
        4. src/doip_server/config/gateway1.yaml (source directory)

        If no configuration file is found, a default configuration will be created.

        Returns:
            str: Path to the found or created gateway configuration file

        Note:
            This method is called during initialization when no explicit
            gateway configuration path is provided.
        """
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
        """Create a default gateway configuration file if none exists

        This method generates a comprehensive default gateway configuration
        with proper network settings, protocol configuration, and ECU references.
        The configuration follows the hierarchical structure expected by the
        DoIP server implementation.

        Returns:
            str: Path to the created configuration file

        Note:
            The default configuration includes:
            - Network binding to all interfaces (0.0.0.0:13400)
            - DoIP protocol version 0x02 with inverse 0xFD
            - Reference to engine ECU configuration
            - Reasonable connection limits and timeouts
        """
        default_config_content = """# Default Gateway Configuration
# This file provides a comprehensive default configuration for the DoIP gateway
gateway:
  name: "DefaultGateway"
  description: "Default DoIP Gateway - Auto-generated configuration"
  network:
    host: "0.0.0.0"  # Bind to all interfaces
    port: 13400      # Standard DoIP port
    max_connections: 5
    timeout: 30
  protocol:
    version: 0x02      # DoIP protocol version
    inverse_version: 0xFD  # Inverse protocol version for validation
  ecus:
    - "ecu_engine.yaml"  # Reference to engine ECU configuration
"""

        # Create config directory if it doesn't exist
        os.makedirs("config", exist_ok=True)
        config_path = "config/gateway1.yaml"

        with open(config_path, "w") as f:
            f.write(default_config_content)

        self.logger.info("Created default gateway configuration file: %s", config_path)
        return config_path

    def _load_all_configs(self):
        """Load all configuration files in the correct order.

        This method orchestrates the loading of all configuration components:
        1. Gateway configuration (network, protocol, logging settings)
        2. ECU configurations (target addresses, tester addresses, UDS services)
        3. UDS service definitions (common and ECU-specific services)

        If any step fails, the method will attempt to load fallback configurations
        to ensure the server can still start with minimal functionality.

        Raises:
            Exception: If configuration loading fails completely and no fallback
                configurations can be loaded
        """
        try:
            # Load gateway configuration
            self._load_gateway_config()

            # Load ECU configurations
            self._load_ecu_configs()

            # Load UDS services
            self._load_uds_services()

            self.logger.info("All configurations loaded successfully")
        except Exception as e:
            self.logger.error("Failed to load configurations: %s", e)
            self._load_fallback_configs()

    def _load_gateway_config(self):
        """Load gateway configuration from YAML file"""
        try:
            with open(self.gateway_config_path, "r") as f:
                self.gateway_config = yaml.safe_load(f)
            self.logger.info(
                "Gateway configuration loaded from: %s", self.gateway_config_path
            )
        except Exception as e:
            self.logger.error("Failed to load gateway configuration: %s", e)
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
        """Load UDS services configuration from multiple files"""
        try:
            # Load services from each ECU configuration
            for ecu_addr, ecu_config in self.ecu_configs.items():
                ecu_info = ecu_config.get("ecu", {})
                uds_config = ecu_info.get("uds_services", {})

                # Get service files for this ECU
                service_files = uds_config.get("service_files", [])

                # Load services from each file
                for service_file in service_files:
                    self._load_services_from_file(service_file, ecu_addr)

                # Also load from the old single file for backward compatibility
                uds_services_path = self._find_uds_services_path()
                if uds_services_path and os.path.exists(uds_services_path):
                    self._load_services_from_file(uds_services_path, ecu_addr)

            self.logger.info(f"UDS services loaded: {len(self.uds_services)} services")
        except Exception as e:
            self.logger.error(f"Failed to load UDS services: {e}")

    def _load_services_from_file(
        self, service_file_path: str, _ecu_address: int = None
    ):
        """Load UDS services from a specific file"""
        try:
            # Find the actual file path
            actual_path = self._find_service_file_path(service_file_path)
            if not actual_path or not os.path.exists(actual_path):
                self.logger.warning(f"Service file not found: {service_file_path}")
                return

            with open(actual_path, "r") as f:
                service_config = yaml.safe_load(f)

            # Load common services
            common_services = service_config.get("common_services", {})
            for service_name, service_config_data in common_services.items():
                self.uds_services[service_name] = service_config_data

            # Load ECU-specific services based on file name or content
            if "engine_services" in service_config:
                engine_services = service_config.get("engine_services", {})
                for service_name, service_config_data in engine_services.items():
                    self.uds_services[service_name] = service_config_data

            if "transmission_services" in service_config:
                transmission_services = service_config.get("transmission_services", {})
                for service_name, service_config_data in transmission_services.items():
                    self.uds_services[service_name] = service_config_data

            if "abs_services" in service_config:
                abs_services = service_config.get("abs_services", {})
                for service_name, service_config_data in abs_services.items():
                    self.uds_services[service_name] = service_config_data

            self.logger.debug(f"Loaded services from: {actual_path}")

        except Exception as e:
            self.logger.error(f"Failed to load services from {service_file_path}: {e}")

    def _find_service_file_path(self, service_file: str) -> str:
        """Find the actual path to a service file"""
        possible_paths = [
            service_file,  # Direct path
            os.path.join("config", service_file),  # In config directory
            os.path.join("..", "config", service_file),  # Relative to parent
            os.path.join("src", "doip_server", "config", service_file),  # In src
            # New folder structure paths
            os.path.join("config", "generic", service_file),  # Generic services
            os.path.join("config", "ecus", "abs", service_file),  # ABS services
            os.path.join("config", "ecus", "engine", service_file),  # Engine services
            os.path.join(
                "config", "ecus", "transmission", service_file
            ),  # Transmission services
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def _find_uds_services_path(self) -> str:
        """Find the UDS services configuration file path"""
        possible_paths = [
            "config/uds_services.yaml",
            "uds_services.yaml",
            "../config/uds_services.yaml",
            "src/doip_server/config/uds_services.yaml",
            # New folder structure paths
            "config/generic/generic_uds_messages.yaml",
            "config/generic/uds_services.yaml",
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
        """Get the complete gateway configuration.

        Returns:
            Dict[str, Any]: Gateway configuration dictionary containing:
                - name: Gateway name
                - description: Gateway description
                - network: Network configuration (host, port, etc.)
                - protocol: Protocol configuration (version, inverse_version)
                - ecus: List of ECU configuration file references
                - logging: Logging configuration (if present)
                - security: Security configuration (if present)
                - vehicle: Vehicle information (if present)
        """
        return self.gateway_config.get("gateway", {})

    def get_network_config(self) -> Dict[str, Any]:
        """Get network configuration settings.

        Returns:
            Dict[str, Any]: Network configuration containing:
                - host: Server host address (default: "0.0.0.0")
                - port: Server port number (default: 13400)
                - max_connections: Maximum concurrent connections
                - timeout: Connection timeout in seconds
        """
        return self.get_gateway_config().get("network", {})

    def get_server_binding_info(self) -> tuple[str, int]:
        """Get server host and port for binding.

        Returns:
            tuple[str, int]: A tuple containing (host, port) for server binding.
                - host: Server host address (default: "0.0.0.0")
                - port: Server port number (default: 13400)
        """
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

    def get_vehicle_info(self) -> Dict[str, Any]:
        """Get vehicle information from gateway configuration"""
        return self.get_gateway_config().get("vehicle", {})

    def get_gateway_info(self) -> Dict[str, Any]:
        """Get gateway information including logical address"""
        gateway_config = self.get_gateway_config()
        return {
            "logical_address": gateway_config.get("logical_address", 0x1000),
            "name": gateway_config.get("name", "Unknown"),
            "description": gateway_config.get("description", ""),
        }

    # ECU configuration methods
    def get_all_ecu_addresses(self) -> List[int]:
        """Get all configured ECU target addresses.

        Returns:
            List[int]: List of all configured ECU target addresses.
                These are the addresses that the DoIP server will accept
                as valid target addresses for diagnostic messages.
        """
        return list(self.ecu_configs.keys())

    def get_ecu_config(self, target_address: int) -> Optional[Dict[str, Any]]:
        """Get ECU configuration by target address.

        Args:
            target_address (int): The target address of the ECU to retrieve

        Returns:
            Optional[Dict[str, Any]]: ECU configuration dictionary if found, None otherwise.
                The configuration contains:
                - ecu: ECU information (name, target_address, tester_addresses, etc.)
                - uds_services: UDS service configuration for this ECU
                - routine_activation: Routine activation configuration
        """
        return self.ecu_configs.get(target_address)

    def get_ecu_tester_addresses(self, target_address: int) -> List[int]:
        """Get allowed tester addresses for a specific ECU.

        Args:
            target_address (int): The target address of the ECU

        Returns:
            List[int]: List of allowed tester addresses for this ECU.
                These are the source addresses that are permitted to send
                diagnostic messages to this ECU.
        """
        ecu_config = self.get_ecu_config(target_address)
        if ecu_config:
            ecu_info = ecu_config.get("ecu", {})
            return ecu_info.get("tester_addresses", [])
        return []

    def get_ecu_functional_address(self, target_address: int) -> Optional[int]:
        """Get functional address for a specific ECU"""
        ecu_config = self.get_ecu_config(target_address)
        if ecu_config:
            ecu_info = ecu_config.get("ecu", {})
            return ecu_info.get("functional_address")
        return None

    def get_ecus_by_functional_address(self, functional_address: int) -> List[int]:
        """Get all ECU target addresses that use the specified functional address"""
        matching_ecus = []
        for ecu_addr in self.get_all_ecu_addresses():
            ecu_functional_addr = self.get_ecu_functional_address(ecu_addr)
            if ecu_functional_addr == functional_address:
                matching_ecus.append(ecu_addr)
        return matching_ecus

    def is_source_address_allowed(
        self, source_addr: int, target_addr: int = None
    ) -> bool:
        """Check if source address is allowed for a specific ECU or any ECU"""
        if target_addr is not None:
            # Check specific ECU
            allowed_sources = self.get_ecu_tester_addresses(target_addr)
            return source_addr in allowed_sources

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

        # Get service files for this ECU
        service_files = uds_config.get("service_files", [])

        # Load services from the specified files for this ECU
        ecu_services = {}

        # Load from service files
        for service_file in service_files:
            file_services = self._get_services_from_file(service_file, target_address)
            ecu_services.update(file_services)

        # Also load from the old method for backward compatibility
        common_services = uds_config.get("common_services", [])
        specific_services = uds_config.get("specific_services", [])
        all_service_names = common_services + specific_services

        # Get actual service configurations
        for service_name in all_service_names:
            if service_name in self.uds_services:
                ecu_services[service_name] = self.uds_services[service_name]
            else:
                self.logger.warning(
                    f"Service {service_name} not found in UDS services "
                    f"for ECU 0x{target_address:04X}"
                )

        return ecu_services

    def _get_services_from_file(
        self, service_file_path: str, ecu_address: int
    ) -> Dict[str, Any]:
        """Get services from a specific file for a specific ECU"""
        try:
            actual_path = self._find_service_file_path(service_file_path)
            if not actual_path or not os.path.exists(actual_path):
                return {}

            with open(actual_path, "r") as f:
                service_config = yaml.safe_load(f)

            services = {}

            # Always load common services
            common_services = service_config.get("common_services", {})
            services.update(common_services)

            # Load ECU-specific services based on ECU address
            if ecu_address == 0x1000:  # Engine ECU
                engine_services = service_config.get("engine_services", {})
                services.update(engine_services)
            elif ecu_address == 0x1001:  # Transmission ECU
                transmission_services = service_config.get("transmission_services", {})
                services.update(transmission_services)
            elif ecu_address == 0x1002:  # ABS ECU
                abs_services = service_config.get("abs_services", {})
                services.update(abs_services)

            return services

        except Exception as e:
            self.logger.error(f"Failed to get services from {service_file_path}: {e}")
            return {}

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
                        "supports_functional": service_config.get(
                            "supports_functional", False
                        ),
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
                        "supports_functional": service_config.get(
                            "supports_functional", False
                        ),
                    }
        return None

    def process_response_with_mirroring(
        self, response_template: str, request: str
    ) -> str:
        """Process a response template with request mirroring expressions.

        Args:
            response_template: Response template string that may contain mirroring expressions
            request: Original request string (hex format)

        Returns:
            Processed response string with mirrored request parts

        Mirroring expressions:
            - {request[start:end]} - Mirror characters from start to end (exclusive)
            - {request[start:]} - Mirror characters from start to end of string
            - {request[:end]} - Mirror characters from start to end (exclusive)
            - {request[index]} - Mirror single character at index
        """
        if not response_template or not request:
            return response_template

        # Remove 0x prefix from request if present for easier indexing
        clean_request = request[2:] if request.startswith("0x") else request

        # Pattern to match {request[...]} expressions
        pattern = r"\{request\[([^\]]+)\]\}"

        def replace_mirror_expression(match):
            try:
                index_expr = match.group(1)

                # Handle slice notation [start:end]
                if ":" in index_expr:
                    parts = index_expr.split(":")
                    if len(parts) == 2:
                        start_str, end_str = parts
                        start = int(start_str) if start_str else 0
                        end = int(end_str) if end_str else len(clean_request)

                        # Direct character indexing (no conversion needed)
                        if start < 0 or end > len(clean_request) or start >= end:
                            return "00"  # Default fallback

                        return clean_request[start:end]
                    else:
                        return "00"  # Invalid slice format
                else:
                    # Single index
                    index = int(index_expr)

                    if index < 0 or index >= len(clean_request):
                        return "00"  # Default fallback

                    return clean_request[index]

            except (ValueError, IndexError):
                return "00"  # Default fallback for any error

        # Replace all mirroring expressions
        processed_response = re.sub(
            pattern, replace_mirror_expression, response_template
        )

        return processed_response

    def get_uds_services_supporting_functional(self, target_address: int) -> List[str]:
        """Get list of service names that support functional addressing for a specific ECU"""
        ecu_services = self.get_ecu_uds_services(target_address)
        functional_services = []
        for service_name, service_config in ecu_services.items():
            if service_config.get("supports_functional", False):
                functional_services.append(service_name)
        return functional_services

    def _match_request(self, config_request: str, request: str) -> bool:
        """Check if a request matches a configured request or regex pattern"""
        # Handle both with and without 0x prefix for exact matches
        if config_request == request:
            return True
        if config_request == f"0x{request}":
            return True
        if config_request.lstrip("0x") == request:
            return True
        if f"0x{config_request}" == request:
            return True

        # Check if config_request is a regex pattern (starts with 'regex:')
        if config_request.startswith("regex:"):
            pattern = config_request[6:]  # Remove 'regex:' prefix
            try:
                # Compile the regex pattern for case-insensitive matching
                regex = re.compile(pattern, re.IGNORECASE)
                # Test against both the original request and variations with/without 0x prefix
                if regex.match(request):
                    return True
                # If request has 0x prefix, test without it
                if request.startswith("0x") and regex.match(request[2:]):
                    return True
                # If request doesn't have 0x prefix, test with it
                if not request.startswith("0x") and regex.match(f"0x{request}"):
                    return True
            except re.error as e:
                # Log regex compilation error but don't fail the matching
                self.logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                return False

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
        """Validate all configuration files for completeness and correctness.

        This method performs comprehensive validation of all loaded configurations:
        - Gateway configuration (network, protocol settings)
        - ECU configurations (target addresses, tester addresses)
        - UDS services (service definitions)

        Returns:
            bool: True if all configurations are valid, False otherwise

        Note:
            Validation errors are logged with appropriate error levels.
            Warnings are issued for missing optional configurations,
            errors are issued for missing required configurations.
        """
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
        version = protocol.get("version", "N/A")
        if version == "N/A":
            summary.append(f"Protocol Version: {version}")
        else:
            # Convert string hex to int if needed
            if isinstance(version, str):
                version_int = (
                    int(version, 16) if version.startswith("0x") else int(version)
                )
            else:
                version_int = version
            summary.append(f"Protocol Version: 0x{version_int:02X}")

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
