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
from typing import Optional, Dict, Any
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
        self.config_manager = HierarchicalConfigManager(gateway_config_path)

        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)

        # Get server configuration
        gateway_config = self.config_manager.get_gateway_config()

        # Set host and port
        self.host = host or gateway_config.get("host", "0.0.0.0")
        self.port = port or gateway_config.get("port", 13400)

        # Validate configuration
        self._validate_binding_config()

        # Initialize servers
        self.tcp_server = DoIPTCPServer(
            self.host, self.port, self.config_manager, self.logger
        )
        self.udp_server = DoIPUDPServer(
            self.host, self.port, self.config_manager, self.logger
        )

        # Server state
        self.running = False
        self.server_threads = []

        self.logger.info(
            f"DoIP Server initialized - Host: {self.host}, Port: {self.port}"
        )

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
                "gateway_config_path": self.config_manager.gateway_config_path,
                "ecu_count": len(self.config_manager.get_all_ecu_addresses()),
                "uds_services_count": len(self.config_manager.get_uds_services()),
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
        logging_config = self.config_manager.get_logging_config()

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

        # Add file handler if enabled
        if logging_config.get("file", {}).get("enabled", False):
            file_config = logging_config["file"]
            file_handler = logging.FileHandler(
                file_config.get("path", "doip_server.log")
            )
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
        return self.tcp_server.handlers.get_response_cycling_state()


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
