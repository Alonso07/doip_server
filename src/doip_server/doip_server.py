#!/usr/bin/env python3
"""
DoIP Server implementation for automotive diagnostics.

This module provides the main DoIP (Diagnostics over IP) server functionality
for handling automotive diagnostic communication protocols.

Refactored version with modular architecture:
- messages.py: DoIP message handling
- handlers.py: Request/response handlers
- doip_tcp.py: TCP-specific functionality
- doip_udp.py: UDP-specific functionality
"""

import threading
import logging
from typing import Optional, Dict, Any, Tuple
from .hierarchical_config_manager import HierarchicalConfigManager
from .doip_tcp import DoIPTCPServer
from .doip_udp import DoIPUDPServer


class DoIPServer:
    """DoIP Server class for handling automotive diagnostic communication.

    This class implements a comprehensive DoIP (Diagnostics over IP) server that provides:

    - **Vehicle Identification**: UDP-based vehicle identification requests/responses
    - **Routing Activation**: TCP-based routing activation for diagnostic sessions
    - **Diagnostic Message Handling**: UDS (Unified Diagnostic Services) message processing
    - **Functional Addressing**: Support for functional addressing (broadcast to multiple ECUs)
    - **Response Cycling**: Configurable response cycling for testing scenarios
    - **Hierarchical Configuration**: Integration with hierarchical configuration management

    The server supports both TCP and UDP protocols simultaneously:
    - **TCP**: Used for diagnostic sessions, routing activation, and UDS communication
    - **UDP**: Used for vehicle identification requests and responses

    Key Features:
    - Multi-ECU support with configurable target addresses
    - Source address validation and authorization
    - UDS service configuration and response generation
    - Functional addressing for broadcast diagnostic requests
    - Response cycling for testing multiple response scenarios
    - Comprehensive logging and error handling

    Attributes:
        config_manager (HierarchicalConfigManager): Configuration management instance
        host (str): Server host address for binding
        port (int): Server port number for binding
        tcp_server (DoIPTCPServer): TCP server instance
        udp_server (DoIPUDPServer): UDP server instance
        running (bool): Server running state
        logger (logging.Logger): Logger instance for this server
    """

    def __init__(self, host=None, port=None, gateway_config_path=None):
        """Initialize the DoIP server with configuration management.

        This constructor initializes the DoIP server with hierarchical configuration
        management, network settings, and protocol configuration. The server can be
        configured either through explicit parameters or through configuration files.

        Args:
            host (str, optional): Server host address. If None, uses configuration value.
                Default: None (uses config or "0.0.0.0")
            port (int, optional): Server port number. If None, uses configuration value.
                Default: None (uses config or 13400)
            gateway_config_path (str, optional): Path to gateway configuration file.
                If None, searches for default configuration files.
                Default: None

        Raises:
            ValueError: If host, port, max_connections, or timeout configuration is invalid
            FileNotFoundError: If no configuration files can be found or created
            yaml.YAMLError: If configuration files contain invalid YAML
        """
        # Initialize configuration manager
        self._config_manager = HierarchicalConfigManager(gateway_config_path)

        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)

        # Get server configuration
        gateway_config = self._config_manager.get_gateway_config()

        # Set host and port
        self.host = host or gateway_config.get("host", "0.0.0.0")
        self.port = port or gateway_config.get("port", 13400)

        # Validate configuration
        self._validate_binding_config()

        # Initialize servers
        self.tcp_server = DoIPTCPServer(
            self.host, self.port, self._config_manager, self.logger
        )
        self.udp_server = DoIPUDPServer(
            self.host, self.port, self._config_manager, self.logger
        )

        # Server state
        self.running = False
        self.server_threads = []

        # Response cycling state
        self.response_cycle_state = {}

        self.logger.info(
            f"DoIP Server initialized - Host: {self.host}, Port: {self.port}"
        )

    @property
    def server_socket(self):
        """Get the TCP server socket for backward compatibility.

        Returns:
            TCP server socket or None if not started
        """
        return self.tcp_server.server_socket if self.tcp_server else None

    @property
    def udp_socket(self):
        """Get the UDP server socket for backward compatibility.

        Returns:
            UDP server socket or None if not started
        """
        return self.udp_server.udp_socket if self.udp_server else None

    @udp_socket.setter
    def udp_socket(self, value):
        """Set the UDP server socket for backward compatibility."""
        if self.udp_server:
            self.udp_server.udp_socket = value

    @property
    def config_manager(self):
        """Get the configuration manager."""
        return self._config_manager

    @config_manager.setter
    def config_manager(self, value):
        """Set the configuration manager and update sub-servers."""
        self._config_manager = value
        if self.tcp_server:
            self.tcp_server.config_manager = value
        if self.udp_server:
            self.udp_server.config_manager = value

    def _validate_binding_config(self):
        """Validate host and port configuration"""
        # Validate host
        if not isinstance(self.host, str) or not self.host:
            raise ValueError("Host must be a non-empty string")

        # Validate port
        if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
            raise ValueError("Port must be an integer between 1 and 65535")

    def get_binding_info(self) -> tuple[str, int]:
        """Get current server binding information

        Returns:
            Tuple of (host, port)
        """
        return self.host, self.port

    def get_server_info(self) -> dict:
        """Get comprehensive server information

        Returns:
            Dictionary containing server information
        """
        return {
            "host": self.host,
            "port": self.port,
            "running": self.running,
            "tcp_server": self.tcp_server.get_server_info(),
            "udp_server": self.udp_server.get_server_info(),
            "config_manager": {
                "gateway_config_path": self._config_manager.gateway_config_path,
                "ecu_count": len(self._config_manager.get_all_ecu_addresses()),
                "uds_services_count": len(self._config_manager.get_uds_services()),
            },
        }

    def is_ready(self) -> bool:
        """Check if server is ready to accept connections

        Returns:
            True if both TCP and UDP servers are ready
        """
        return self.tcp_server.is_ready() and self.udp_server.is_ready()

    def _setup_logging(self):
        """Setup logging based on configuration"""
        logging_config = self._config_manager.get_logging_config()

        # Configure root logger
        log_level = getattr(logging, logging_config.get("level", "INFO").upper())
        logging.basicConfig(
            level=log_level,
            format=logging_config.get(
                "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            handlers=[],
        )

        # Add console handler if enabled
        if logging_config.get("console", True):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            formatter = logging.Formatter(
                logging_config.get(
                    "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            console_handler.setFormatter(formatter)
            logging.getLogger().addHandler(console_handler)

        # Add file handler if file path is specified
        file_path = logging_config.get("file")
        if file_path and isinstance(file_path, str):
            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(log_level)
            formatter = logging.Formatter(
                logging_config.get(
                    "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)

    def start(self):
        """Start the DoIP server with both TCP and UDP support.

        This method starts both TCP and UDP servers in separate threads.
        The TCP server handles diagnostic sessions, routing activation, and UDS communication.
        The UDP server handles vehicle identification requests and responses.

        The server will run until stop() is called or an error occurs.

        Raises:
            RuntimeError: If server fails to start
        """
        try:
            self.logger.info("Starting DoIP Server...")

            # Start TCP server
            if not self.tcp_server.start():
                raise RuntimeError("Failed to start TCP server")

            # Start UDP server
            if not self.udp_server.start():
                self.tcp_server.stop()
                raise RuntimeError("Failed to start UDP server")

            self.running = True

            # Start server threads
            tcp_thread = threading.Thread(
                target=self.tcp_server.accept_connections, daemon=True
            )
            udp_thread = threading.Thread(
                target=self.udp_server.listen_for_messages, daemon=True
            )

            tcp_thread.start()
            udp_thread.start()

            self.server_threads = [tcp_thread, udp_thread]

            self.logger.info("DoIP Server started successfully")
            self.logger.info(f"TCP server listening on {self.host}:{self.port}")
            self.logger.info(f"UDP server listening on {self.host}:{self.port}")

        except Exception as e:
            self.logger.error(f"Failed to start DoIP server: {e}")
            self.stop()
            raise RuntimeError(f"Failed to start DoIP server: {e}")

    def stop(self):
        """Stop the DoIP server"""
        self.logger.info("Stopping DoIP Server...")

        self.running = False

        # Stop TCP server
        self.tcp_server.stop()

        # Stop UDP server
        self.udp_server.stop()

        # Wait for threads to finish
        for thread in self.server_threads:
            if thread.is_alive():
                thread.join(timeout=5.0)

        self.logger.info("DoIP Server stopped")

    def reset_response_cycling(self, ecu_address=None, service_name=None):
        """Reset response cycling state for a specific ECU-service combination or all states

        Args:
            ecu_address (int, optional): ECU address to reset. If None, resets all ECUs.
            service_name (str, optional): Service name to reset. If None, resets all services.
        """
        self.tcp_server.handlers.reset_response_cycling(ecu_address, service_name)

    def get_response_cycling_state(self):
        """Get current response cycling state for debugging

        Returns:
            Dictionary containing response cycling state
        """
        # Combine TCP and UDP response cycling states
        tcp_state = self.tcp_server.handlers.get_response_cycling_state()
        udp_state = self.udp_server.get_response_cycling_state()

        # Merge the states
        combined_state = {}
        combined_state.update(tcp_state)
        combined_state.update(udp_state)

        return combined_state

    def process_uds_message(
        self, uds_payload: bytes, target_address: int
    ) -> Optional[bytes]:
        """Process UDS message and return response for specific ECU.

        This method provides backward compatibility for direct UDS message processing.

        Args:
            uds_payload: Raw UDS payload
            target_address: Target ECU address

        Returns:
            UDS response payload or None if no response
        """
        return self.tcp_server.handlers.process_uds_message(uds_payload, target_address)

    def _get_vehicle_vin(self) -> str:
        """Get VIN from configuration or return default"""
        try:
            # Try to get VIN from configuration
            vehicle_info = self._config_manager.get_vehicle_info()
            return vehicle_info.get("vin", "1HGBH41JXMN109186")
        except Exception as e:
            self.logger.warning(f"Could not get VIN from configuration: {e}")
            return "1HGBH41JXMN109186"

    def _get_gateway_logical_address(self) -> int:
        """Get gateway logical address from configuration"""
        try:
            # Try to get gateway address from configuration
            gateway_info = self._config_manager.get_gateway_info()
            return gateway_info.get("logical_address", 0x1000)
        except Exception as e:
            self.logger.warning(
                f"Could not get gateway address from configuration: {e}"
            )
            return 0x1000

    def _get_vehicle_eid_gid(self) -> Tuple[bytes, bytes]:
        """Get EID and GID from configuration"""
        try:
            # Try to get EID and GID from configuration
            vehicle_info = self._config_manager.get_vehicle_info()
            eid_hex = vehicle_info.get("eid", "123456789ABC")
            gid_hex = vehicle_info.get("gid", "DEF012345678")

            # Convert hex strings to bytes
            eid = bytes.fromhex(eid_hex)
            gid = bytes.fromhex(gid_hex)

            return eid, gid
        except Exception as e:
            self.logger.warning(f"Could not get EID/GID from configuration: {e}")
            return b"\x12\x34\x56\x78\x9a\xbc", b"\xde\xf0\x12\x34\x56\x78"

    def create_vehicle_identification_response(self) -> bytes:
        """Create DoIP Vehicle Identification Response message"""
        # Get VIN from configuration or use default
        vin = self._get_vehicle_vin()

        # Get logical address from configuration (use first ECU address)
        logical_address = self._get_gateway_logical_address()

        # Get EID and GID from configuration
        eid, gid = self._get_vehicle_eid_gid()

        return self.udp_server.message_handler.create_vehicle_identification_response(
            vin, logical_address, eid, gid
        )

    def create_entity_status_response(self) -> bytes:
        """Create DoIP entity status response message"""
        return self.udp_server.create_entity_status_response()

    def create_power_mode_response(self) -> bytes:
        """Create DoIP power mode information response message"""
        return self.udp_server.create_power_mode_response()

    def handle_udp_message(self, data: bytes, addr: tuple) -> Optional[bytes]:
        """Handle UDP message (wrapper for backward compatibility).

        Args:
            data: UDP message data
            addr: Client address tuple (host, port)

        Returns:
            UDP response message or None
        """
        response = self.udp_server.handle_udp_message(data, addr)
        if response and self.udp_socket:
            self.udp_socket.sendto(response, addr)
        return response

    def handle_power_mode_request(self, payload: bytes) -> bytes:
        """Handle power mode information request.

        Args:
            payload: Raw power mode request payload (ignored)

        Returns:
            DoIP power mode response message
        """
        return self.create_power_mode_response()

    def process_doip_message(self, message: bytes) -> Optional[bytes]:
        """Process DoIP message and return response.

        Args:
            message: Raw DoIP message

        Returns:
            DoIP response message or None
        """
        return self.tcp_server.handlers.process_doip_message(message)


def start_doip_server(host=None, port=None, gateway_config_path=None):
    """Start a DoIP server with the specified configuration.

    This is a convenience function that creates and starts a DoIP server instance.

    Args:
        host (str, optional): Server host address
        port (int, optional): Server port number
        gateway_config_path (str, optional): Path to gateway configuration file

    Returns:
        DoIPServer: Started server instance
    """
    server = DoIPServer(host, port, gateway_config_path)
    server.start()
    return server
