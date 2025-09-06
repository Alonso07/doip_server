#!/usr/bin/env python3
import socket
import struct
import logging
from .hierarchical_config_manager import HierarchicalConfigManager

# DoIP Protocol constants
DOIP_PROTOCOL_VERSION = 0x02
DOIP_INVERSE_PROTOCOL_VERSION = 0xFD

# DoIP Payload types
PAYLOAD_TYPE_ALIVE_CHECK_REQUEST = 0x0001
PAYLOAD_TYPE_ALIVE_CHECK_RESPONSE = 0x0002
PAYLOAD_TYPE_ROUTING_ACTIVATION_REQUEST = 0x0005
PAYLOAD_TYPE_ROUTING_ACTIVATION_RESPONSE = 0x0006
PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE = 0x8001
PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE_ACK = 0x8002
PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE_NACK = 0x8003

# UDS Service IDs (legacy - now handled by configuration)

# Response codes
ROUTING_ACTIVATION_RESPONSE_CODE_SUCCESS = 0x10
ROUTING_ACTIVATION_RESPONSE_CODE_UNKNOWN_SOURCE_ADDRESS = 0x02
ROUTING_ACTIVATION_RESPONSE_CODE_ALL_SOCKETS_TAKEN = 0x03
ROUTING_ACTIVATION_RESPONSE_CODE_DIFFERENT_SOURCE_ADDRESS = 0x04
ROUTING_ACTIVATION_RESPONSE_CODE_ALREADY_ACTIVATED = 0x05


class DoIPServer:
    def __init__(self, host=None, port=None, gateway_config_path=None):
        # Initialize configuration manager based on provided path
        if gateway_config_path is None:
            # Use legacy configuration manager for backward compatibility
            from .config_manager import DoIPConfigManager

            self.config_manager = DoIPConfigManager()
        else:
            # Use hierarchical configuration manager
            self.config_manager = HierarchicalConfigManager(gateway_config_path)

        # Get server configuration - prioritize explicit parameters over config
        config_host, config_port = self.config_manager.get_server_binding_info()
        self.host = host if host is not None else config_host
        self.port = port if port is not None else config_port

        # Get other server configuration
        if hasattr(self.config_manager, "get_network_config"):
            # Hierarchical configuration manager
            network_config = self.config_manager.get_network_config()
            self.max_connections = network_config.get("max_connections", 5)
            self.timeout = network_config.get("timeout", 30)
        else:
            # Legacy configuration manager
            server_config = self.config_manager.get_server_config()
            self.max_connections = server_config.get("max_connections", 5)
            self.timeout = server_config.get("timeout", 30)

        # Get protocol configuration
        protocol_config = self.config_manager.get_protocol_config()
        self.protocol_version = protocol_config.get("version", 0x02)
        self.inverse_protocol_version = protocol_config.get("inverse_version", 0xFD)

        # Initialize server state
        self.server_socket = None
        self.running = False

        # Response cycling state - tracks current response index for each service per ECU
        self.response_cycle_state = (
            {}
        )  # Format: {(ecu_address, service_name): current_index}

        # Setup logging
        self._setup_logging()

        # Validate configuration
        if hasattr(self.config_manager, "validate_configs"):
            # Hierarchical configuration manager
            if not self.config_manager.validate_configs():
                self.logger.warning(
                    "Configuration validation failed, using fallback settings"
                )
        else:
            # Legacy configuration manager
            if not self.config_manager.validate_config():
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
            self.logger.error(
                f"Invalid max_connections configuration: must be positive integer, got {self.max_connections}"
            )
            raise ValueError(
                f"Invalid max_connections configuration: must be positive integer, got {self.max_connections}"
            )

        # Validate timeout
        if not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
            self.logger.error(
                f"Invalid timeout configuration: must be positive number, got {self.timeout}"
            )
            raise ValueError(
                f"Invalid timeout configuration: must be positive number, got {self.timeout}"
            )

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
        """Start the DoIP server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_connections)
        self.running = True

        self.logger.info(f"DoIP server listening on {self.host}:{self.port}")
        self.logger.info(self.config_manager.get_config_summary())

        print(f"DoIP server listening on {self.host}:{self.port}")

        try:
            while self.running:
                client_socket, client_address = self.server_socket.accept()
                print(f"Connection from {client_address}")
                self.handle_client(client_socket)
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.stop()

    def stop(self):
        """Stop the DoIP server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()

    def handle_client(self, client_socket):
        """Handle client connection"""
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break

                print(f"Received data: {data.hex()}")
                response = self.process_doip_message(data)
                if response:
                    client_socket.send(response)
                    print(f"Sent response: {response.hex()}")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()

    def process_doip_message(self, data):
        """Process incoming DoIP message and return appropriate response"""
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
                f"Invalid protocol version: 0x{protocol_version:02X}, expected 0x{self.protocol_version:02X}"
            )
            return self.create_doip_nack(0x02)  # Invalid protocol version

        # Process based on payload type
        if payload_type == PAYLOAD_TYPE_ROUTING_ACTIVATION_REQUEST:
            return self.handle_routing_activation(data[8:])
        elif payload_type == PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE:
            return self.handle_diagnostic_message(data[8:])
        elif payload_type == PAYLOAD_TYPE_ALIVE_CHECK_REQUEST:
            return self.handle_alive_check()
        elif payload_type == 0x0007:
            return self.handle_alive_check_0007()
        elif payload_type == 0x0008:
            return self.handle_power_mode_request(data[8:])
        else:
            print(f"Unsupported payload type: 0x{payload_type:04X}")
            return None

    def handle_routing_activation(self, payload):
        """Handle routing activation request"""
        self.logger.info("Processing routing activation request")

        if len(payload) < 7:
            self.logger.warning("Routing activation payload too short")
            return self.create_routing_activation_response(
                ROUTING_ACTIVATION_RESPONSE_CODE_UNKNOWN_SOURCE_ADDRESS
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
        if hasattr(self.config_manager, "get_all_ecu_addresses"):
            # Hierarchical configuration manager - check all ECUs
            if not self.config_manager.is_source_address_allowed(
                client_logical_address
            ):
                self.logger.warning(
                    f"Source address 0x{client_logical_address:04X} not allowed"
                )
                return self.create_routing_activation_response(
                    ROUTING_ACTIVATION_RESPONSE_CODE_UNKNOWN_SOURCE_ADDRESS
                )
        else:
            # Legacy configuration manager
            if not self.config_manager.is_source_address_allowed(
                client_logical_address
            ):
                self.logger.warning(
                    f"Source address 0x{client_logical_address:04X} not allowed"
                )
                return self.create_routing_activation_response(
                    ROUTING_ACTIVATION_RESPONSE_CODE_UNKNOWN_SOURCE_ADDRESS
                )

        # Accept the routing activation
        self.logger.info(
            f"Routing activation accepted for client 0x{client_logical_address:04X}"
        )
        return self.create_routing_activation_response(
            ROUTING_ACTIVATION_RESPONSE_CODE_SUCCESS,
            client_logical_address,
            logical_address,
        )

    def handle_diagnostic_message(self, payload):
        """Handle diagnostic message (UDS)"""
        self.logger.info("Processing diagnostic message")

        if len(payload) < 4:
            self.logger.warning("Diagnostic message payload too short")
            return None

        # Extract source and target addresses
        source_address = struct.unpack(">H", payload[0:2])[0]
        target_address = struct.unpack(">H", payload[2:4])[0]
        uds_payload = payload[4:]

        self.logger.info(f"Source Address: 0x{source_address:04X}")
        self.logger.info(f"Target Address: 0x{target_address:04X}")
        self.logger.info(f"UDS Payload: {uds_payload.hex()}")

        # Validate addresses
        if hasattr(self.config_manager, "get_all_ecu_addresses"):
            # Hierarchical configuration manager
            if not self.config_manager.is_source_address_allowed(
                source_address, target_address
            ):
                self.logger.warning(
                    f"Source address 0x{source_address:04X} not allowed for target 0x{target_address:04X}"
                )
                return self.create_doip_nack(0x03)  # Unsupported source address

            if not self.config_manager.is_target_address_valid(target_address):
                self.logger.warning(f"Target address 0x{target_address:04X} not valid")
                return self.create_doip_nack(0x04)  # Unsupported target address
        else:
            # Legacy configuration manager
            if not self.config_manager.is_source_address_allowed(source_address):
                self.logger.warning(
                    f"Source address 0x{source_address:04X} not allowed"
                )
                return self.create_doip_nack(0x03)  # Unsupported source address

            if not self.config_manager.is_target_address_valid(target_address):
                self.logger.warning(f"Target address 0x{target_address:04X} not valid")
                return self.create_doip_nack(0x04)  # Unsupported target address

        # Process UDS message
        if hasattr(self.config_manager, "get_all_ecu_addresses"):
            # Hierarchical configuration manager - process for specific ECU
            uds_response = self.process_uds_message(uds_payload, target_address)
        else:
            # Legacy configuration manager - process without target address
            uds_response = self.process_uds_message(uds_payload, None)

        if uds_response:
            return self.create_diagnostic_message_response(
                target_address, source_address, uds_response
            )

        return None

    def process_uds_message(self, uds_payload, target_address):
        """Process UDS message and return response for specific ECU"""
        if not uds_payload:
            return None

        # Convert UDS payload to hex string for matching
        uds_hex = uds_payload.hex().upper()
        self.logger.info(f"UDS Payload: {uds_hex}")

        # Check if this UDS request matches any configured service
        if hasattr(self.config_manager, "get_all_ecu_addresses"):
            # Hierarchical configuration manager - check for specific ECU
            service_config = self.config_manager.get_uds_service_by_request(
                uds_hex, target_address
            )
            if service_config:
                self.logger.info(
                    f"Processing UDS service: {service_config.get('name', 'Unknown')} for ECU 0x{target_address:04X}"
                )
            else:
                self.logger.warning(
                    f"Unsupported UDS request: {uds_hex} for ECU 0x{target_address:04X}"
                )
                return self.create_uds_negative_response(
                    0x7F, 0x7F
                )  # Service not supported in active session
        else:
            # Legacy configuration manager - check without target address
            service_config = self.config_manager.get_uds_service_by_request(uds_hex)
            if service_config:
                self.logger.info(
                    f"Processing UDS service: {service_config.get('name', 'Unknown')}"
                )
            else:
                self.logger.warning(f"Unsupported UDS request: {uds_hex}")
                return self.create_uds_negative_response(
                    0x7F, 0x7F
                )  # Service not supported in active session

        if service_config:
            # Get responses for this service
            responses = service_config.get("responses", [])
            if responses:
                # Get service name for cycling
                service_name = service_config.get("name", "Unknown")

                # Create unique key for this ECU-service combination
                if hasattr(self.config_manager, "get_all_ecu_addresses"):
                    # Hierarchical configuration manager - use target address
                    cycle_key = (target_address, service_name)
                else:
                    # Legacy configuration manager - use 0 as default ECU address
                    cycle_key = (0, service_name)

                # Get current response index for this service-ECU combination
                current_index = self.response_cycle_state.get(cycle_key, 0)

                # Select response based on current index
                response_hex = responses[current_index]

                # Update index for next time (cycle back to 0 when reaching end)
                next_index = (current_index + 1) % len(responses)
                self.response_cycle_state[cycle_key] = next_index

                self.logger.info(
                    f"Returning response {current_index + 1}/{len(responses)} for service {service_name}: {response_hex}"
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
            readable_state[f"ECU_0x{ecu_addr:04X}_{service_name}"] = index
        return readable_state

    def handle_alive_check(self):
        """Handle alive check request"""
        self.logger.info("Processing alive check request")
        return self.create_alive_check_response()

    def handle_alive_check_0007(self):
        """Handle alive check request with payload type 0x0007"""
        self.logger.info("Processing alive check request (0x0007)")
        return self.create_alive_check_response_0007()

    def handle_power_mode_request(self, payload):
        """Handle power mode request (payload type 0x0008)"""
        self.logger.info("Processing power mode request")
        return self.create_power_mode_response()

    def create_uds_negative_response(self, service_id: int, nrc: int) -> bytes:
        """Create UDS negative response"""
        # UDS negative response format: 0x7F + service_id + NRC
        return b"\x7F" + bytes([service_id]) + bytes([nrc])

    def create_routing_activation_response(
        self, response_code, client_logical_address, logical_address
    ):
        """Create routing activation response"""
        # Create payload according to DoIP standard: !HHBLL format
        payload = struct.pack(">H", client_logical_address)  # Client logical address
        payload += struct.pack(">H", logical_address)  # Logical address
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

    def create_alive_check_response_0007(self):
        """Create alive check response for payload type 0x0007"""
        # Respond with the same payload type 0x0007
        payload = b"\x00\x00\x00\x00\x00\x00"  # 6 bytes for alive check response

        header = struct.pack(
            ">BBHI",
            self.protocol_version,
            self.inverse_protocol_version,
            0x0007,  # Same payload type as request
            len(payload),
        )

        return header + payload

    def create_power_mode_response(self):
        """Create power mode response for payload type 0x0008"""
        # Power mode response - client expects 2 bytes (H format)
        payload = b"\x00\x00"  # 2 bytes indicating power mode status

        header = struct.pack(
            ">BBHI",
            self.protocol_version,
            self.inverse_protocol_version,
            0x0008,  # Same payload type as request
            len(payload),
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


def start_doip_server(host=None, port=None, gateway_config_path=None):
    """Start the DoIP server (entry point for poetry script)"""
    server = DoIPServer(host, port, gateway_config_path)
    server.start()


if __name__ == "__main__":
    start_doip_server()
