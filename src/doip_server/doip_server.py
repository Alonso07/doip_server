#!/usr/bin/env python3
"""
DoIP Server implementation for automotive diagnostics.

This module provides the main DoIP (Diagnostics over IP) server functionality
for handling automotive diagnostic communication protocols.
"""
import socket
import struct
import logging
import time
from .hierarchical_config_manager import HierarchicalConfigManager

# DoIP Protocol constants
DOIP_PROTOCOL_VERSION = 0x02
DOIP_INVERSE_PROTOCOL_VERSION = 0xFD

# DoIP Payload types
PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_REQUEST = 0x0001
PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_RESPONSE = 0x0004
PAYLOAD_TYPE_ALIVE_CHECK_REQUEST = 0x0007
PAYLOAD_TYPE_ALIVE_CHECK_RESPONSE = 0x0008
PAYLOAD_TYPE_ROUTING_ACTIVATION_REQUEST = 0x0005
PAYLOAD_TYPE_ROUTING_ACTIVATION_RESPONSE = 0x0006
PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE = 0x8001
PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE_ACK = 0x8002
PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE_NACK = 0x8003
PAYLOAD_TYPE_ENTITY_STATUS_REQUEST = 0x4001
PAYLOAD_TYPE_ENTITY_STATUS_RESPONSE = 0x4002
PAYLOAD_TYPE_POWER_MODE_INFORMATION_REQUEST = 0x4003
PAYLOAD_TYPE_POWER_MODE_INFORMATION_RESPONSE = 0x4004

# UDS Service IDs (now handled by configuration)

# Response codes
ROUTING_ACTIVATION_RESPONSE_CODE_SUCCESS = 0x10
ROUTING_ACTIVATION_RESPONSE_CODE_UNKNOWN_SOURCE_ADDRESS = 0x02
ROUTING_ACTIVATION_RESPONSE_CODE_ALL_SOCKETS_TAKEN = 0x03
ROUTING_ACTIVATION_RESPONSE_CODE_DIFFERENT_SOURCE_ADDRESS = 0x04
ROUTING_ACTIVATION_RESPONSE_CODE_ALREADY_ACTIVATED = 0x05


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
        max_connections (int): Maximum concurrent TCP connections
        timeout (int): Connection timeout in seconds
        protocol_version (int): DoIP protocol version (default: 0x02)
        inverse_protocol_version (int): Inverse protocol version for validation (default: 0xFD)
        server_socket (socket.socket): TCP server socket
        udp_socket (socket.socket): UDP server socket
        running (bool): Server running state
        response_cycle_state (dict): Response cycling state for each ECU-service combination
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

        Note:
            The initialization process:
            1. Initializes hierarchical configuration manager
            2. Loads server configuration (host, port, max_connections, timeout)
            3. Loads protocol configuration (version, inverse_version)
            4. Sets up logging based on configuration
            5. Validates all configuration parameters
            6. Initializes server state and response cycling
        """
        # Initialize hierarchical configuration manager
        self.config_manager = HierarchicalConfigManager(gateway_config_path)

        # Get server configuration - prioritize explicit parameters over config
        config_host, config_port = self.config_manager.get_server_binding_info()
        self.host = host if host is not None else config_host
        self.port = port if port is not None else config_port

        # Get other server configuration
        network_config = self.config_manager.get_network_config()
        self.max_connections = network_config.get("max_connections", 5)
        self.timeout = network_config.get("timeout", 30)

        # Get protocol configuration
        protocol_config = self.config_manager.get_protocol_config()
        self.protocol_version = protocol_config.get("version", 0x02)
        self.inverse_protocol_version = protocol_config.get("inverse_version", 0xFD)

        # Initialize server state
        self.server_socket = None
        self.udp_socket = None
        self.running = False

        # Response cycling state - tracks current response index for each service per ECU
        self.response_cycle_state = (
            {}
        )  # Format: {(ecu_address, service_name): current_index}

        # Setup logging
        self._setup_logging()

        # Validate configuration
        if not self.config_manager.validate_configs():
            self.logger.warning(
                "Configuration validation failed, using fallback settings"
            )

        # Validate host and port configuration
        self._validate_binding_config()

    def _validate_binding_config(self):
        """Validate host and port configuration"""
        # Validate host
        if not self.host or self.host.strip() == "":
            self.logger.error("Invalid host configuration: host cannot be empty")
            raise ValueError("Invalid host configuration: host cannot be empty")

        # Validate port
        if not isinstance(self.port, int) or self.port < 1 or self.port > 65535:
            self.logger.error(
                f"Invalid port configuration: port must be between 1-65535, got {self.port}"
            )
            raise ValueError(
                f"Invalid port configuration: port must be between 1-65535, got {self.port}"
            )

        # Validate max_connections
        if not isinstance(self.max_connections, int) or self.max_connections < 1:
            error_msg = (
                f"Invalid max_connections configuration: must be positive integer, "
                f"got {self.max_connections}"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # Validate timeout
        if not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
            error_msg = (
                f"Invalid timeout configuration: must be positive number, "
                f"got {self.timeout}"
            )
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info(f"Binding configuration validated: {self.host}:{self.port}")
        self.logger.info(
            f"Server settings: max_connections={self.max_connections}, timeout={self.timeout}s"
        )

    def get_binding_info(self) -> tuple[str, int]:
        """Get current server binding information

        Returns:
            tuple: (host, port) for current server binding
        """
        return self.host, self.port

    def get_server_info(self) -> dict:
        """Get comprehensive server information

        Returns:
            dict: Server configuration and status information
        """
        return {
            "host": self.host,
            "port": self.port,
            "max_connections": self.max_connections,
            "timeout": self.timeout,
            "running": self.running,
            "protocol_version": f"0x{self.protocol_version:02X}",
            "inverse_protocol_version": f"0x{self.inverse_protocol_version:02X}",
        }

    def is_ready(self) -> bool:
        """Check if server is ready to accept connections

        Returns:
            bool: True if server is running and sockets are bound, False otherwise
        """
        return (
            self.running
            and self.server_socket is not None
            and self.udp_socket is not None
        )

    def _setup_logging(self):
        """Setup logging based on configuration"""
        logging_config = self.config_manager.get_logging_config()
        log_level = getattr(logging, logging_config.get("level", "INFO"))
        log_format = logging_config.get(
            "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Configure logging
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(),  # Console handler
                (
                    logging.FileHandler(logging_config.get("file", "doip_server.log"))
                    if logging_config.get("file")
                    else logging.NullHandler()
                ),
            ],
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging configured")
        self.logger.info(f"Server will bind to {self.host}:{self.port}")

    def start(self):
        """Start the DoIP server with both TCP and UDP support.

        This method starts the DoIP server by:
        1. Creating and binding TCP server socket for diagnostic sessions
        2. Creating and binding UDP server socket for vehicle identification
        3. Entering the main server loop to handle incoming connections
        4. Processing both TCP and UDP messages concurrently

        The server runs until interrupted (KeyboardInterrupt) or stopped programmatically.
        Both TCP and UDP sockets are bound to the same host and port.

        Note:
            The server uses non-blocking socket operations with short timeouts
            to allow for concurrent handling of TCP and UDP messages.
            This ensures responsive handling of both connection types.

        Raises:
            OSError: If socket binding fails (e.g., port already in use)
            Exception: If server startup fails for any other reason
        """
        # Start TCP server
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_connections)

        # Start UDP server for vehicle identification
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind((self.host, self.port))

        self.running = True

        self.logger.info(
            f"DoIP server listening on {self.host}:{self.port} (TCP and UDP)"
        )
        self.logger.info(self.config_manager.get_config_summary())

        print(f"DoIP server listening on {self.host}:{self.port} (TCP and UDP)")

        # Signal that server is ready for connections
        self.logger.info("DoIP server is ready to accept connections")

        try:
            while self.running:
                # Check for UDP messages first (non-blocking)
                try:
                    self.udp_socket.settimeout(0.1)  # Short timeout for UDP check
                    data, addr = self.udp_socket.recvfrom(1024)
                    self.handle_udp_message(data, addr)
                except socket.timeout:
                    pass  # No UDP message, continue to TCP
                except Exception as e:
                    self.logger.error(f"Error handling UDP message: {e}")

                # Check for TCP connections
                try:
                    self.server_socket.settimeout(0.1)  # Short timeout for TCP check
                    client_socket, client_address = self.server_socket.accept()
                    print(f"TCP connection from {client_address}")
                    self.handle_client(client_socket)
                except socket.timeout:
                    pass  # No TCP connection, continue loop
                except Exception as e:
                    self.logger.error(f"Error handling TCP connection: {e}")

        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.stop()

    def stop(self):
        """Stop the DoIP server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.udp_socket:
            self.udp_socket.close()

    def handle_client(self, client_socket):
        """Handle client connection and send multiple DoIP messages when needed"""
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break

                print(f"Received data: {data.hex()}")
                responses = self.process_doip_message(data)

                # Handle both single response and list of responses
                if responses:
                    if isinstance(responses, list):
                        # Send multiple responses with delay support
                        for i, response in enumerate(responses):
                            # Check if this response has a delay configuration
                            delay_ms = self._get_response_delay(data, i)
                            if delay_ms > 0:
                                self.logger.info(
                                    f"Delaying response {i+1} by {delay_ms}ms"
                                )
                                time.sleep(delay_ms / 1000.0)  # Convert ms to seconds

                            client_socket.send(response)
                            print(
                                f"Sent response {i+1}/{len(responses)}: {response.hex()}"
                            )
                    else:
                        # Single response (backward compatibility)
                        delay_ms = self._get_response_delay(data, 0)
                        if delay_ms > 0:
                            self.logger.info(f"Delaying response by {delay_ms}ms")
                            time.sleep(delay_ms / 1000.0)  # Convert ms to seconds

                        client_socket.send(responses)
                        print(f"Sent response: {responses.hex()}")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def _get_response_delay(self, data, response_index):
        """Get delay configuration for a specific response.

        Args:
            data (bytes): Original DoIP message data
            response_index (int): Index of the response (0 for single response)

        Returns:
            int: Delay in milliseconds, 0 if no delay configured
        """
        try:
            # Parse DoIP header to get payload type
            if len(data) < 8:
                return 0

            payload_type = struct.unpack(">H", data[2:4])[0]

            # Only apply delays to diagnostic messages (UDS)
            if payload_type != PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE:
                return 0

            # Extract UDS payload for service lookup
            if len(data) < 12:  # DoIP header (8) + source (2) + target (2)
                return 0

            uds_payload = data[8:]  # Skip DoIP header
            if len(uds_payload) < 4:
                return 0

            # Extract target address and UDS payload
            target_address = struct.unpack(">H", uds_payload[2:4])[0]
            uds_data = uds_payload[4:]

            if not uds_data:
                return 0

            # Convert UDS payload to hex string for service matching
            uds_hex = uds_data.hex().upper()

            # Get service configuration
            service_config = self.config_manager.get_uds_service_by_request(
                uds_hex, target_address
            )

            if not service_config:
                return 0

            # Check for response-level delay first (higher priority)
            responses = service_config.get("responses", [])
            if response_index < len(responses):
                response = responses[response_index]
                if isinstance(response, dict):
                    # Response-level delay overrides service-level delay
                    return response.get("delay_ms", 0)
                elif isinstance(response, str):
                    # For string responses, fall back to service-level delay
                    return service_config.get("delay_ms", 0)

            # Fall back to service-level delay if no response-level delay
            return service_config.get("delay_ms", 0)

        except Exception as e:
            self.logger.warning(f"Error getting response delay: {e}")
            return 0

    def process_doip_message(self, data):
        """Process incoming DoIP message and return appropriate response(s).

        This method parses incoming DoIP messages and routes them to the appropriate
        handler based on the payload type. It validates the DoIP header and protocol
        version before processing the message.

        Args:
            data (bytes): Raw DoIP message data including header and payload

        Returns:
            bytes, list, or None: DoIP response message(s) if successful, None if invalid or unsupported
            - For diagnostic messages: Returns list of responses (ACK + UDS responses)
            - For other messages: Returns single response message

        Supported Payload Types:
            - 0x0005: Routing Activation Request
            - 0x8001: Diagnostic Message (UDS) - returns list of responses
            - 0x0007: Alive Check Request (TCP)
            - 0x4003: Power Mode Information Request (UDP)

        Note:
            The method validates:
            - Minimum message length (8 bytes for DoIP header)
            - Protocol version compatibility
            - Payload type support
        """
        if len(data) < 8:  # Minimum DoIP header size
            return None

        # Parse DoIP header
        protocol_version = data[0]
        inverse_protocol_version = data[1]
        payload_type = struct.unpack(">H", data[2:4])[0]
        payload_length = struct.unpack(">I", data[4:8])[0]

        print(f"Protocol Version: 0x{protocol_version:02X}")
        print(f"Inverse Protocol Version: 0x{inverse_protocol_version:02X}")
        print(f"Payload Type: 0x{payload_type:04X}")
        print(f"Payload Length: {payload_length}")

        # Validate protocol version
        if (
            protocol_version != self.protocol_version
            or inverse_protocol_version != self.inverse_protocol_version
        ):
            self.logger.warning(
                f"Invalid protocol version: 0x{protocol_version:02X}, "
                f"expected 0x{self.protocol_version:02X}"
            )
            return self.create_doip_nack(0x02)  # Invalid protocol version

        # Process based on payload type
        if payload_type == PAYLOAD_TYPE_ROUTING_ACTIVATION_REQUEST:
            return self.handle_routing_activation(data[8:])
        if payload_type == PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE:
            return self.handle_diagnostic_message(data[8:])
        if payload_type == PAYLOAD_TYPE_ALIVE_CHECK_REQUEST:
            return self.handle_alive_check()
        if payload_type == PAYLOAD_TYPE_POWER_MODE_INFORMATION_REQUEST:
            return self.handle_power_mode_request(data[8:])

        print(f"Unsupported payload type: 0x{payload_type:04X}")
        return None

    def handle_routing_activation(self, payload):
        """Handle routing activation request"""
        self.logger.info("Processing routing activation request")

        if len(payload) < 7:
            self.logger.warning("Routing activation payload too short")
            return self.create_routing_activation_response(
                ROUTING_ACTIVATION_RESPONSE_CODE_UNKNOWN_SOURCE_ADDRESS,
                0x0000,  # client_logical_address (unknown due to short payload)
                self._get_gateway_logical_address(),  # logical_address (gateway address from config)
            )

        # Extract routing activation parameters
        client_logical_address = struct.unpack(">H", payload[0:2])[0]
        logical_address = struct.unpack(">H", payload[2:4])[0]
        response_code = payload[4]
        reserved = struct.unpack(">I", payload[5:9])[0] if len(payload) >= 9 else 0

        self.logger.info(f"Client Logical Address: 0x{client_logical_address:04X}")
        self.logger.info(f"Logical Address: 0x{logical_address:04X}")
        self.logger.info(f"Response Code: 0x{response_code:02X}")
        self.logger.info(f"Reserved: 0x{reserved:08X}")

        # Check if source address is allowed
        if not self.config_manager.is_source_address_allowed(client_logical_address):
            self.logger.warning(
                f"Source address 0x{client_logical_address:04X} not allowed"
            )
            return self.create_routing_activation_response(
                ROUTING_ACTIVATION_RESPONSE_CODE_UNKNOWN_SOURCE_ADDRESS,
                client_logical_address,  # Use the extracted client address
                self._get_gateway_logical_address(),  # logical_address (gateway address from config)
            )

        # Accept the routing activation
        self.logger.info(
            f"Routing activation accepted for client 0x{client_logical_address:04X}"
        )
        return self.create_routing_activation_response(
            ROUTING_ACTIVATION_RESPONSE_CODE_SUCCESS,
            client_logical_address,
            self._get_gateway_logical_address(),  # Use gateway logical address as source
        )

    def handle_diagnostic_message(self, payload):
        """Handle diagnostic message (UDS) and return list of responses

        Returns:
            list: List of DoIP response messages to send to client
        """
        self.logger.info("Processing diagnostic message")

        if len(payload) < 4:
            self.logger.warning("Diagnostic message payload too short")
            return [self.create_doip_nack(0x01)]  # Invalid payload length

        # Extract source and target addresses
        source_address = struct.unpack(">H", payload[0:2])[0]
        target_address = struct.unpack(">H", payload[2:4])[0]
        uds_payload = payload[4:]

        self.logger.info(f"Source Address: 0x{source_address:04X}")
        self.logger.info(f"Target Address: 0x{target_address:04X}")
        self.logger.info(f"UDS Payload: {uds_payload.hex()}")

        # Check if this is a functional address request
        functional_ecus = self.config_manager.get_ecus_by_functional_address(
            target_address
        )
        if functional_ecus:
            self.logger.info(
                f"Functional address request to 0x{target_address:04X}, "
                f"targeting {len(functional_ecus)} ECUs"
            )
            return self.handle_functional_diagnostic_message(
                source_address, target_address, uds_payload, functional_ecus
            )

        # Validate addresses for physical addressing
        if not self.config_manager.is_source_address_allowed(
            source_address, target_address
        ):
            self.logger.warning(
                f"Source address 0x{source_address:04X} not allowed for "
                f"target 0x{target_address:04X}"
            )
            return [self.create_doip_nack(0x03)]  # Unsupported source address

        if not self.config_manager.is_target_address_valid(target_address):
            self.logger.warning(f"Target address 0x{target_address:04X} not valid")
            return [self.create_doip_nack(0x04)]  # Unsupported target address

        # Process UDS message
        uds_response = self.process_uds_message(uds_payload, target_address)

        responses = []

        # Always send diagnostic message acknowledgment first
        ack_message = self.create_diagnostic_message_ack(
            target_address, source_address, 0x00  # ACK code
        )
        responses.append(ack_message)
        self.logger.info("Added diagnostic message acknowledgment to response list")

        # Add UDS response if available
        if uds_response:
            uds_response_message = self.create_diagnostic_message_response(
                target_address, source_address, uds_response
            )
            responses.append(uds_response_message)
            self.logger.info("Added UDS response to response list")
        else:
            self.logger.warning("No UDS response generated")

        return responses

    def handle_functional_diagnostic_message(
        self, source_address, functional_address, uds_payload, target_ecus
    ):
        """Handle functional diagnostic message by broadcasting to multiple ECUs.

        This method implements functional addressing where a single UDS request
        is broadcast to multiple ECUs that support the service. It:
        1. Validates source address authorization for each target ECU
        2. Checks if each ECU supports the UDS service with functional addressing
        3. Processes the UDS message for each responding ECU
        4. Returns a list of all valid responses

        Args:
            source_address (int): Source logical address of the requesting client
            functional_address (int): Functional address (e.g., 0x1FFF) for broadcast
            uds_payload (bytes): UDS service payload to broadcast
            target_ecus (List[int]): List of ECU addresses that use this functional address

        Returns:
            list: List of DoIP response messages to send to client
        """
        self.logger.info(
            f"Handling functional diagnostic message to 0x{functional_address:04X}"
        )

        # Convert UDS payload to hex string for matching
        uds_hex = uds_payload.hex().upper()

        # Find ECUs that support this UDS service with functional addressing
        responding_ecus = []
        for ecu_address in target_ecus:
            # Check if source address is allowed for this ECU
            if not self.config_manager.is_source_address_allowed(
                source_address, ecu_address
            ):
                self.logger.warning(
                    f"Source address 0x{source_address:04X} not allowed for ECU 0x{ecu_address:04X}"
                )
                continue

            # Check if this ECU supports the UDS service with functional addressing
            service_config = self.config_manager.get_uds_service_by_request(
                uds_hex, ecu_address
            )
            if service_config and service_config.get("supports_functional", False):
                responding_ecus.append(ecu_address)
                self.logger.info(
                    f"ECU 0x{ecu_address:04X} supports functional addressing for this service"
                )
            else:
                self.logger.debug(
                    f"ECU 0x{ecu_address:04X} does not support functional "
                    f"addressing for this service"
                )

        if not responding_ecus:
            self.logger.warning(
                f"No ECUs support functional addressing for UDS request: {uds_hex}"
            )
            return [self.create_doip_nack(0x04)]  # Unsupported target address

        # Send one ACK for the functional request (using functional address as source)
        ack_message = self.create_diagnostic_message_ack(
            functional_address, source_address, 0x00  # ACK code
        )
        responses = [ack_message]
        self.logger.info(
            "Added single diagnostic message acknowledgment for functional request"
        )

        # Process the UDS message for each responding ECU and collect responses
        ecu_addresses_with_responses = []
        for ecu_address in responding_ecus:
            uds_response = self.process_uds_message(uds_payload, ecu_address)
            if uds_response:
                # Create individual response for this ECU (using ECU's address as source)
                response = self.create_diagnostic_message_response(
                    ecu_address, source_address, uds_response
                )
                responses.append(response)
                ecu_addresses_with_responses.append(ecu_address)
                self.logger.info(f"Generated response from ECU 0x{ecu_address:04X}")

        if len(responses) == 1:  # Only ACK, no UDS responses
            self.logger.warning("No valid UDS responses generated from any ECU")
            # Still return the ACK message

        # Enhanced functional addressing: return multiple responses
        # 1 ACK + N UDS responses (one per responding ECU)
        ecu_count = len(responses) - 1  # Subtract 1 for the ACK
        self.logger.info(
            f"Functional addressing: {ecu_count} ECUs responded (1 ACK + {ecu_count} UDS responses)"
        )

        # Log all responses for debugging
        for i, resp in enumerate(responses):
            if i == 0:  # First response is the ACK
                self.logger.info(f"ACK Response: {resp.hex()}")
            else:  # Remaining responses are UDS responses from individual ECUs
                ecu_addr = ecu_addresses_with_responses[i - 1]
                self.logger.info(
                    f"UDS Response from ECU 0x{ecu_addr:04X}: {resp.hex()}"
                )

        return responses

    def handle_functional_diagnostic_message_multiple_responses(
        self, source_address, functional_address, uds_payload, target_ecus
    ):
        """
        Handle functional diagnostic message and return multiple responses from different ECUs.
        This is an enhanced version that can return multiple responses.

        Args:
            source_address: Source logical address
            functional_address: Functional address (e.g., 0x1FFF)
            uds_payload: UDS service payload
            target_ecus: List of ECU addresses that use this functional address

        Returns:
            List of response messages from different ECUs
        """
        self.logger.info(
            f"Handling functional diagnostic message with multiple responses "
            f"to 0x{functional_address:04X}"
        )

        # Convert UDS payload to hex string for matching
        uds_hex = uds_payload.hex().upper()

        # Find ECUs that support this UDS service with functional addressing
        responding_ecus = []
        for ecu_address in target_ecus:
            # Check if source address is allowed for this ECU
            if not self.config_manager.is_source_address_allowed(
                source_address, ecu_address
            ):
                self.logger.warning(
                    f"Source address 0x{source_address:04X} not allowed for ECU 0x{ecu_address:04X}"
                )
                continue

            # Check if this ECU supports the UDS service with functional addressing
            service_config = self.config_manager.get_uds_service_by_request(
                uds_hex, ecu_address
            )
            if service_config and service_config.get("supports_functional", False):
                responding_ecus.append(ecu_address)
                self.logger.info(
                    f"ECU 0x{ecu_address:04X} supports functional addressing for this service"
                )
            else:
                self.logger.debug(
                    f"ECU 0x{ecu_address:04X} does not support functional "
                    f"addressing for this service"
                )

        if not responding_ecus:
            self.logger.warning(
                f"No ECUs support functional addressing for UDS request: {uds_hex}"
            )
            return []

        # Process the UDS message for each responding ECU and collect all responses
        all_responses = []
        for ecu_address in responding_ecus:
            uds_response = self.process_uds_message(uds_payload, ecu_address)
            if uds_response:
                # Create individual response for this ECU
                response = self.create_diagnostic_message_response(
                    functional_address, source_address, uds_response
                )
                all_responses.append(
                    {
                        "ecu_address": ecu_address,
                        "response": response,
                        "uds_response": uds_response,
                    }
                )
                self.logger.info(f"Generated response from ECU 0x{ecu_address:04X}")

        self.logger.info(
            f"Functional addressing with multiple responses: {len(all_responses)} ECUs responded"
        )

        # Log all responses for debugging
        for i, resp in enumerate(all_responses):
            self.logger.info(
                f"Response {i+1} from ECU 0x{resp['ecu_address']:04X}: "
                f"{resp['response'].hex()}"
            )

        return all_responses

    def process_uds_message(self, uds_payload, target_address):
        """Process UDS message and return response for specific ECU.

        This method processes UDS (Unified Diagnostic Services) messages by:
        1. Converting the UDS payload to hex string for service matching
        2. Looking up the service configuration for the target ECU
        3. Implementing response cycling if multiple responses are configured
        4. Returning the appropriate UDS response or negative response

        Args:
            uds_payload (bytes): Raw UDS message payload
            target_address (int): Target ECU address for the UDS message

        Returns:
            bytes or None: UDS response message if service is supported, None otherwise

        Response Cycling:
            If a service has multiple responses configured, this method implements
            response cycling where each subsequent request returns the next response
            in the configured list, cycling back to the first response after the last.

        Negative Responses:
            Returns UDS negative response (0x7F + service_id + NRC) for:
            - Unsupported services (NRC 0x7F)
            - General programming failures (NRC 0x72)
        """
        if not uds_payload:
            return None

        # Convert UDS payload to hex string for matching
        uds_hex = uds_payload.hex().upper()
        self.logger.info(f"UDS Payload: {uds_hex}")

        # Check if this UDS request matches any configured service
        service_config = self.config_manager.get_uds_service_by_request(
            uds_hex, target_address
        )
        if service_config:
            self.logger.info(
                f"Processing UDS service: {service_config.get('name', 'Unknown')} "
                f"for ECU 0x{target_address:04X}"
            )
        else:
            self.logger.warning(
                f"Unsupported UDS request: {uds_hex} for ECU 0x{target_address:04X}"
            )
            return self.create_uds_negative_response(
                0x7F, 0x7F
            )  # Service not supported in active session

        if service_config:
            # Check if this service is configured for no response
            no_response = service_config.get("no_response", False)
            if no_response:
                self.logger.info(
                    f"Service {service_config.get('name', 'Unknown')} configured for no response"
                )
                return None  # Return None to indicate no response should be sent

            # Get responses for this service
            responses = service_config.get("responses", [])
            if responses:
                # Get service name for cycling
                service_name = service_config.get("name", "Unknown")

                # Create unique key for this ECU-service combination
                cycle_key = (target_address, service_name)

                # Get current response index for this service-ECU combination
                current_index = self.response_cycle_state.get(cycle_key, 0)

                # Select response based on current index
                response_template = responses[current_index]

                # Handle both string and dictionary response formats
                if isinstance(response_template, dict):
                    # New format: {"response": "0x...", "delay_ms": 100}
                    response_hex = self.config_manager.process_response_with_mirroring(
                        response_template.get("response", ""), uds_hex
                    )
                else:
                    # Legacy format: "0x..." string
                    response_hex = self.config_manager.process_response_with_mirroring(
                        response_template, uds_hex
                    )

                # Update index for next time (cycle back to 0 when reaching end)
                next_index = (current_index + 1) % len(responses)
                self.response_cycle_state[cycle_key] = next_index

                self.logger.info(
                    f"Returning response {current_index + 1}/{len(responses)} "
                    f"for service {service_name}: {response_hex}"
                )
                self.logger.debug(f"Next response will be index {next_index}")

                # Convert hex string back to bytes
                try:
                    # Strip "0x" prefix if present
                    hex_str = (
                        response_hex[2:]
                        if response_hex.startswith("0x")
                        else response_hex
                    )
                    self.logger.debug(
                        f"Processing hex string: '{hex_str}' (length: {len(hex_str)})"
                    )
                    response_bytes = bytes.fromhex(hex_str)
                    return response_bytes
                except ValueError as e:
                    self.logger.error(
                        f"Invalid response hex format: {response_hex} - {e}"
                    )
                    self.logger.error(
                        f"Processed hex string: '{hex_str}' (length: {len(hex_str)})"
                    )
                    return self.create_uds_negative_response(
                        0x7F, 0x72
                    )  # General programming failure
            else:
                self.logger.warning(
                    f"No responses configured for service: {service_config.get('name', 'Unknown')}"
                )
                return self.create_uds_negative_response(
                    0x7F, 0x72
                )  # General programming failure

        return None

    def reset_response_cycling(self, ecu_address=None, service_name=None):
        """Reset response cycling state for a specific ECU-service combination or all states

        Args:
            ecu_address: ECU address to reset (None for all ECUs)
            service_name: Service name to reset (None for all services)
        """
        if ecu_address is None and service_name is None:
            # Reset all cycling states
            self.response_cycle_state.clear()
            self.logger.info("Reset all response cycling states")
        elif ecu_address is not None and service_name is not None:
            # Reset specific ECU-service combination
            cycle_key = (ecu_address, service_name)
            if cycle_key in self.response_cycle_state:
                del self.response_cycle_state[cycle_key]
                self.logger.info(
                    f"Reset response cycling for ECU 0x{ecu_address:04X}, service {service_name}"
                )
            else:
                self.logger.warning(
                    f"No cycling state found for ECU 0x{ecu_address:04X}, service {service_name}"
                )
        else:
            # Reset all states for a specific ECU or service
            keys_to_remove = []
            for key in self.response_cycle_state.keys():
                if ecu_address is not None and key[0] == ecu_address:
                    keys_to_remove.append(key)
                elif service_name is not None and key[1] == service_name:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.response_cycle_state[key]

            if keys_to_remove:
                self.logger.info(f"Reset {len(keys_to_remove)} response cycling states")
            else:
                self.logger.warning("No matching cycling states found to reset")

    def get_response_cycling_state(self):
        """Get current response cycling state for debugging

        Returns:
            dict: Current cycling state with readable format
        """
        readable_state = {}
        for (ecu_addr, service_name), index in self.response_cycle_state.items():
            if isinstance(ecu_addr, int):
                readable_state[f"ECU_0x{ecu_addr:04X}_{service_name}"] = index
            else:
                # Handle non-ECU cycling (like power mode)
                readable_state[f"{ecu_addr}_{service_name}"] = index
        return readable_state

    def handle_alive_check(self):
        """Handle alive check request"""
        self.logger.info("Processing alive check request")
        return self.create_alive_check_response()

    def handle_power_mode_request(self, _payload):
        """Handle power mode information request (payload type 0x4003)"""
        self.logger.info("Processing power mode information request")
        return self.create_power_mode_response()

    def handle_entity_status_request(self, _payload):
        """Handle DoIP entity status request (payload type 0x4001)"""
        self.logger.info("Processing DoIP entity status request")
        return self.create_entity_status_response()

    def create_uds_negative_response(self, service_id: int, nrc: int) -> bytes:
        """Create UDS negative response"""
        # UDS negative response format: 0x7F + service_id + NRC
        return b"\x7f" + bytes([service_id]) + bytes([nrc])

    def create_routing_activation_response(
        self, response_code, client_logical_address, logical_address
    ):
        """Create routing activation response

        Args:
            response_code: DoIP routing activation response code
            client_logical_address: Client's logical address (target in response)
            logical_address: Gateway's logical address (source in response)
        """
        # Create payload according to DoIP standard: !HHBLL format
        payload = struct.pack(">H", client_logical_address)  # Client logical address
        payload += struct.pack(
            ">H", logical_address
        )  # Gateway logical address (source)
        payload += struct.pack(">B", response_code)  # Response code
        payload += struct.pack(">I", 0x00000000)  # Reserved (4 bytes)
        payload += struct.pack(">I", 0x00000000)  # VM specific (4 bytes)

        header = struct.pack(
            ">BBHI",
            self.protocol_version,
            self.inverse_protocol_version,
            PAYLOAD_TYPE_ROUTING_ACTIVATION_RESPONSE,
            len(payload),
        )

        # Log response code description
        response_desc = self.config_manager.get_response_code_description(
            "routine_activation", response_code
        )
        self.logger.info(f"Routing activation response: {response_desc}")

        return header + payload

    def create_diagnostic_message_response(
        self, source_addr, target_addr, uds_response
    ):
        """Create diagnostic message response"""
        payload = struct.pack(">HH", source_addr, target_addr) + uds_response

        header = struct.pack(
            ">BBHI",
            self.protocol_version,
            self.inverse_protocol_version,
            PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE,
            len(payload),
        )

        return header + payload

    def create_alive_check_response(self):
        """Create alive check response"""
        # DoIP alive check response should have 6 bytes payload
        payload = b"\x00\x00\x00\x00\x00\x00"  # 6 bytes for alive check response

        header = struct.pack(
            ">BBHI",
            self.protocol_version,
            self.inverse_protocol_version,
            PAYLOAD_TYPE_ALIVE_CHECK_RESPONSE,
            len(payload),
        )

        return header + payload

    def create_power_mode_response(self):
        """Create power mode information response for payload type 0x4004"""
        # Get power mode configuration
        power_mode_config = self.config_manager.get_power_mode_config()

        # Get current status from configuration, default to 0x01 (Power On)
        current_status = power_mode_config.get("current_status", 0x01)

        # Check if response cycling is enabled
        response_cycling = power_mode_config.get("response_cycling", {})
        if response_cycling.get("enabled", False):
            # Get cycling statuses
            cycle_through = response_cycling.get("cycle_through", [0x01])
            if cycle_through:
                # Use response cycling logic similar to UDS services
                cycle_key = ("power_mode", "power_mode_status")
                if cycle_key not in self.response_cycle_state:
                    self.response_cycle_state[cycle_key] = 0

                current_index = self.response_cycle_state[cycle_key]
                current_status = cycle_through[current_index % len(cycle_through)]

                # Update index for next time
                self.response_cycle_state[cycle_key] = (current_index + 1) % len(
                    cycle_through
                )

                self.logger.info(
                    f"Power mode response cycling: using status 0x{current_status:02X}"
                )

        # Power mode response - client expects 1 byte (B format)
        payload = struct.pack(
            ">B", current_status
        )  # 1 byte indicating power mode status

        # Log the power mode status being returned
        available_statuses = power_mode_config.get("available_statuses", {})
        status_info = available_statuses.get(current_status, {})
        status_name = status_info.get("name", f"Unknown (0x{current_status:02X})")
        self.logger.info(f"Power mode response: {status_name} (0x{current_status:02X})")

        header = struct.pack(
            ">BBHI",
            self.protocol_version,
            self.inverse_protocol_version,
            PAYLOAD_TYPE_POWER_MODE_INFORMATION_RESPONSE,  # 0x4004
            len(payload),
        )

        return header + payload

    def create_entity_status_response(self):
        """Create DoIP Entity Status Response message (payload type 0x4002)"""
        # Get entity status configuration
        entity_status_config = self.config_manager.get_entity_status_config()

        # Get configuration values with defaults
        node_type = entity_status_config.get("node_type", 0x01)
        max_open_sockets = entity_status_config.get("max_open_sockets", 10)
        current_open_sockets = entity_status_config.get("current_open_sockets", 0)
        doip_entity_status = entity_status_config.get("doip_entity_status", 0x00)
        diagnostic_power_mode = entity_status_config.get("diagnostic_power_mode", 0x02)

        # Create payload according to DoIP Entity Status Response format:
        # Node Type (1 byte) + Max Open Sockets (1 byte) + Current Open Sockets (1 byte) +
        # DoIP Entity Status (1 byte) + Diagnostic Power Mode (1 byte)
        payload = struct.pack(
            ">BBBBB",
            node_type,
            max_open_sockets,
            current_open_sockets,
            doip_entity_status,
            diagnostic_power_mode,
        )

        # Create DoIP header
        header = struct.pack(
            ">BBHI",
            self.protocol_version,
            self.inverse_protocol_version,
            PAYLOAD_TYPE_ENTITY_STATUS_RESPONSE,
            len(payload),
        )

        # Log the entity status being returned
        available_node_types = entity_status_config.get("available_node_types", {})
        available_entity_statuses = entity_status_config.get(
            "available_entity_statuses", {}
        )
        available_diagnostic_power_modes = entity_status_config.get(
            "available_diagnostic_power_modes", {}
        )

        node_type_info = available_node_types.get(node_type, {})
        node_type_name = node_type_info.get("name", f"Unknown (0x{node_type:02X})")

        entity_status_info = available_entity_statuses.get(doip_entity_status, {})
        entity_status_name = entity_status_info.get(
            "name", f"Unknown (0x{doip_entity_status:02X})"
        )

        diagnostic_power_mode_info = available_diagnostic_power_modes.get(
            diagnostic_power_mode, {}
        )
        diagnostic_power_mode_name = diagnostic_power_mode_info.get(
            "name", f"Unknown (0x{diagnostic_power_mode:02X})"
        )

        self.logger.info(
            f"Entity Status Response: {node_type_name}, "
            f"Max Sockets: {max_open_sockets}, Current Sockets: {current_open_sockets}, "
            f"Status: {entity_status_name}, Power Mode: {diagnostic_power_mode_name}"
        )

        return header + payload

    def create_doip_nack(self, nack_code):
        """Create DoIP negative acknowledgment"""
        payload = struct.pack(">I", nack_code)

        header = struct.pack(
            ">BBHI",
            self.protocol_version,
            self.inverse_protocol_version,
            0x8000,  # Generic NACK payload type
            len(payload),
        )

        return header + payload

    def create_diagnostic_message_ack(self, source_addr, target_addr, ack_code=0x00):
        """Create DoIP diagnostic message acknowledgment (0x8002)

        Args:
            source_addr (int): Source address (ECU address)
            target_addr (int): Target address (tester address)
            ack_code (int): Acknowledgment code (0x00 = ACK)

        Returns:
            bytes: DoIP diagnostic message acknowledgment message

        Payload structure:
            - 1 byte: DoIP version (from config)
            - 1 byte: Inverse DoIP version (from config)
            - 2 bytes: Payload type (0x8002)
            - 4 bytes: Payload length (usually 5)
            - 2 bytes: Source address (ECU address)
            - 2 bytes: Target address (tester address)
            - 1 byte: Acknowledgment code (0x00 = ACK)
        """
        # Create payload: source_addr (2 bytes) + target_addr (2 bytes) + ack_code (1 byte)
        payload = struct.pack(">HHB", source_addr, target_addr, ack_code)

        # Create DoIP header
        header = struct.pack(
            ">BBHI",
            self.protocol_version,
            self.inverse_protocol_version,
            PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE_ACK,
            len(payload),
        )

        return header + payload

    def handle_udp_message(self, data, addr):
        """Handle incoming UDP message (vehicle identification requests)"""
        try:
            self.logger.info(f"Received UDP message from {addr}: {data.hex()}")

            if len(data) < 8:  # Minimum DoIP header size
                self.logger.warning("UDP message too short for DoIP header")
                return

            # Parse DoIP header
            protocol_version = data[0]
            inverse_protocol_version = data[1]
            payload_type = struct.unpack(">H", data[2:4])[0]
            payload_length = struct.unpack(">I", data[4:8])[0]

            self.logger.info(f"UDP Protocol Version: 0x{protocol_version:02X}")
            self.logger.info(
                f"UDP Inverse Protocol Version: 0x{inverse_protocol_version:02X}"
            )
            self.logger.info(f"UDP Payload Type: 0x{payload_type:04X}")
            self.logger.info(f"UDP Payload Length: {payload_length}")

            # Validate protocol version
            if (
                protocol_version != self.protocol_version
                or inverse_protocol_version != self.inverse_protocol_version
            ):
                self.logger.warning(
                    f"Invalid UDP protocol version: 0x{protocol_version:02X}"
                )
                return

            # Handle vehicle identification request
            if payload_type == PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_REQUEST:
                self.logger.info("Processing vehicle identification request")
                response = self.create_vehicle_identification_response()
                if response:
                    self.udp_socket.sendto(response, addr)
                    self.logger.info(f"Sent vehicle identification response to {addr}")
            elif payload_type == PAYLOAD_TYPE_ENTITY_STATUS_REQUEST:
                self.logger.info("Processing DoIP entity status request")
                response = self.create_entity_status_response()
                if response:
                    self.udp_socket.sendto(response, addr)
                    self.logger.info(f"Sent entity status response to {addr}")
            elif payload_type == PAYLOAD_TYPE_POWER_MODE_INFORMATION_REQUEST:
                self.logger.info("Processing power mode information request")
                response = self.create_power_mode_response()
                if response:
                    self.udp_socket.sendto(response, addr)
                    self.logger.info(f"Sent power mode information response to {addr}")
            else:
                self.logger.warning(
                    f"Unsupported UDP payload type: 0x{payload_type:04X}"
                )

        except Exception as e:
            self.logger.error(f"Error handling UDP message: {e}")

    def create_vehicle_identification_response(self):
        """Create DoIP Vehicle Identification Response message"""
        # Get VIN from configuration or use default
        vin = self._get_vehicle_vin()

        # Get logical address from configuration (use first ECU address)
        logical_address = self._get_gateway_logical_address()

        # Get EID and GID from configuration
        eid, gid = self._get_vehicle_eid_gid()

        # Further action required (1 byte) - 0x00 = no further action required
        further_action_required = 0x00

        # VIN/GID synchronization status (1 byte) - 0x00 = synchronized
        vin_gid_sync_status = 0x00

        # Create payload: VIN (17) + Logical Address (2) + EID (6) + GID (6) +
        # Further Action (1) + Sync Status (1)
        payload = vin.encode("ascii").ljust(17, b"\x00")  # VIN, pad to 17 bytes
        payload += struct.pack(">H", logical_address)  # Logical address
        payload += eid  # EID
        payload += gid  # GID
        payload += struct.pack(">B", further_action_required)  # Further action required
        payload += struct.pack(">B", vin_gid_sync_status)  # VIN/GID sync status

        # Create DoIP header
        header = struct.pack(
            ">BBHI",
            self.protocol_version,
            self.inverse_protocol_version,
            PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_RESPONSE,
            len(payload),
        )

        self.logger.info(
            f"Vehicle identification response: VIN={vin}, Address=0x{logical_address:04X}"
        )

        return header + payload

    def _get_vehicle_vin(self):
        """Get VIN from configuration or return default"""
        try:
            # Try to get VIN from configuration
            vehicle_info = self.config_manager.get_vehicle_info()
            return vehicle_info.get("vin", "1HGBH41JXMN109186")
        except Exception as e:
            self.logger.warning(f"Could not get VIN from configuration: {e}")
            return "1HGBH41JXMN109186"

    def _get_gateway_logical_address(self):
        """Get gateway logical address from configuration"""
        try:
            # Try to get gateway address from configuration
            gateway_info = self.config_manager.get_gateway_info()
            return gateway_info.get("logical_address", 0x1000)
        except Exception as e:
            self.logger.warning(
                f"Could not get gateway address from configuration: {e}"
            )
            return 0x1000

    def _get_vehicle_eid_gid(self):
        """Get EID and GID from configuration"""
        try:
            # Try to get EID and GID from configuration
            vehicle_info = self.config_manager.get_vehicle_info()
            eid_hex = vehicle_info.get("eid", "123456789ABC")
            gid_hex = vehicle_info.get("gid", "DEF012345678")

            # Convert hex strings to bytes
            eid = bytes.fromhex(eid_hex)
            gid = bytes.fromhex(gid_hex)

            return eid, gid
        except Exception as e:
            self.logger.warning(f"Could not get EID/GID from configuration: {e}")
            return b"\x12\x34\x56\x78\x9a\xbc", b"\xde\xf0\x12\x34\x56\x78"


def start_doip_server(host=None, port=None, gateway_config_path=None):
    """Start the DoIP server (entry point for poetry script)"""
    server = DoIPServer(host, port, gateway_config_path)
    server.start()


if __name__ == "__main__":
    start_doip_server()
