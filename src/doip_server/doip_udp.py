#!/usr/bin/env python3
"""
DoIP UDP Server module.

This module provides UDP-specific functionality for the DoIP server,
including vehicle identification requests and responses.
"""
import socket
import threading
import logging
from typing import Optional, Tuple
from .messages import (
    DoIPMessage,
    PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_REQUEST,
    PAYLOAD_TYPE_ENTITY_STATUS_REQUEST,
    PAYLOAD_TYPE_POWER_MODE_INFORMATION_REQUEST,
)
from .hierarchical_config_manager import HierarchicalConfigManager


class DoIPUDPServer:
    """DoIP UDP Server for handling vehicle identification requests."""

    def __init__(
        self,
        host: str,
        port: int,
        config_manager: HierarchicalConfigManager,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize DoIP UDP server.

        Args:
            host: Server host address
            port: Server port number
            config_manager: Configuration manager instance
            logger: Logger instance for this server
        """
        self.host = host
        self.port = port
        self.config_manager = config_manager
        self.logger = logger or logging.getLogger(__name__)

        self.message_handler = DoIPMessage(logger)
        self.udp_socket = None
        self.running = False
        self.response_cycle_state = {}

    def start(self) -> bool:
        """Start the UDP server.

        Returns:
            True if server started successfully
        """
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.bind((self.host, self.port))
            self.udp_socket.settimeout(1.0)  # Non-blocking with timeout

            self.running = True
            self.logger.info(f"UDP server started on {self.host}:{self.port}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start UDP server: {e}")
            return False

    def stop(self):
        """Stop the UDP server."""
        self.running = False

        if self.udp_socket:
            try:
                self.udp_socket.close()
            except Exception as e:
                self.logger.error(f"Error closing UDP socket: {e}")

        self.logger.info("UDP server stopped")

    def listen_for_messages(self):
        """Listen for incoming UDP messages in a loop."""
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                self.logger.debug(f"Received UDP message from {addr}: {data.hex()}")

                # Process the message
                response = self.handle_udp_message(data, addr)
                if response:
                    self.udp_socket.sendto(response, addr)
                    self.logger.debug(f"Sent UDP response to {addr}: {response.hex()}")

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error receiving UDP message: {e}")
                break

    def handle_udp_message(self, data: bytes, addr: Tuple[str, int]) -> Optional[bytes]:
        """Handle incoming UDP message (vehicle identification requests).

        Args:
            data: Raw UDP message data
            addr: Client address tuple

        Returns:
            DoIP response message or None if no response
        """
        try:
            # Parse DoIP header
            protocol_version, payload_type, payload_length = (
                self.message_handler.parse_doip_header(data)
            )

            # Validate payload length
            if len(data) < 8 + payload_length:
                self.logger.error("Incomplete DoIP message")
                return None

            payload = data[8 : 8 + payload_length]

            # Handle vehicle identification request
            if payload_type == PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_REQUEST:
                self.logger.info(f"Vehicle identification request from {addr}")
                return self.create_vehicle_identification_response()

            # Handle entity status request
            elif payload_type == PAYLOAD_TYPE_ENTITY_STATUS_REQUEST:
                self.logger.info(f"Processing DoIP entity status request from {addr}")
                response = self.create_entity_status_response()
                self.logger.info(f"Entity Status Response: {response.hex()}")
                return response

            # Handle power mode information request
            elif payload_type == PAYLOAD_TYPE_POWER_MODE_INFORMATION_REQUEST:
                self.logger.info(f"Power mode information request from {addr}")
                return self.create_power_mode_response()

            else:
                self.logger.warning(
                    f"Unsupported UDP payload type: 0x{payload_type:04X}"
                )
                return None

        except Exception as e:
            self.logger.error(f"Error processing UDP message: {e}")
            return None

    def create_vehicle_identification_response(self) -> bytes:
        """Create DoIP Vehicle Identification Response message.

        Returns:
            Complete DoIP vehicle identification response
        """
        try:
            # Get VIN from configuration
            vin = self._get_vehicle_vin()

            # Get gateway logical address
            logical_address = self._get_gateway_logical_address()

            # Get EID and GID
            eid, gid = self._get_vehicle_eid_gid()

            return self.message_handler.create_vehicle_identification_response(
                vin, logical_address, eid, gid
            )

        except Exception as e:
            self.logger.error(f"Error creating vehicle identification response: {e}")
            # Return default response
            return self.message_handler.create_vehicle_identification_response(
                "1HGBH41JXMN109186",  # Default VIN
                0x0E80,  # Default gateway address
                b"\x00" * 6,  # Default EID
                b"\x00" * 6,  # Default GID
            )

    def _get_vehicle_vin(self) -> str:
        """Get VIN from configuration or return default.

        Returns:
            Vehicle Identification Number
        """
        try:
            # Try to get VIN from configuration
            vehicle_info = self.config_manager.get_vehicle_info()
            return vehicle_info.get("vin", "1HGBH41JXMN109186")
        except Exception as e:
            self.logger.warning(f"Could not get VIN from configuration: {e}")
            return "1HGBH41JXMN109186"

    def _get_gateway_logical_address(self) -> int:
        """Get gateway logical address from configuration.

        Returns:
            Gateway logical address
        """
        try:
            # Try to get gateway address from configuration
            gateway_info = self.config_manager.get_gateway_info()
            return gateway_info.get("logical_address", 0x1000)
        except Exception as e:
            self.logger.warning(
                f"Could not get gateway address from configuration: {e}"
            )
            return 0x1000

    def _get_vehicle_eid_gid(self) -> Tuple[bytes, bytes]:
        """Get EID and GID from configuration.

        Returns:
            Tuple of (EID, GID) as bytes
        """
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

    def create_entity_status_response(self) -> bytes:
        """Create DoIP entity status response message.

        Returns:
            Complete DoIP entity status response
        """
        try:
            entity_status_config = self.config_manager.get_entity_status_config()

            # Get configuration values with defaults
            node_type = entity_status_config.get("node_type", 0x01)
            max_open_sockets = entity_status_config.get("max_open_sockets", 10)
            current_open_sockets = entity_status_config.get("current_open_sockets", 0)
            doip_entity_status = entity_status_config.get("doip_entity_status", 0x00)
            diagnostic_power_mode = entity_status_config.get(
                "diagnostic_power_mode", 0x02
            )

            return self.message_handler.create_entity_status_response(
                node_type,
                max_open_sockets,
                current_open_sockets,
                doip_entity_status,
                diagnostic_power_mode,
            )
        except Exception as e:
            self.logger.error(f"Error creating entity status response: {e}")
            return self.message_handler.create_entity_status_response()

    def create_power_mode_response(self) -> bytes:
        """Create DoIP power mode information response message.

        Returns:
            Complete DoIP power mode response
        """
        try:
            power_mode_config = self.config_manager.get_power_mode_config()
            current_status = power_mode_config.get("current_status", 0x01)

            # Check if response cycling is enabled
            response_cycling = power_mode_config.get("response_cycling", {})
            if response_cycling.get("enabled", False):
                # Get cycling statuses
                cycle_through = response_cycling.get("cycle_through", [0x01])
                if cycle_through:
                    # Use response cycling logic with string key format
                    cycle_key = "power_mode_power_mode_status"
                    if cycle_key not in self.response_cycle_state:
                        self.response_cycle_state[cycle_key] = 0

                    current_index = self.response_cycle_state[cycle_key]
                    current_status = cycle_through[current_index % len(cycle_through)]

                    # Update index for next time
                    self.response_cycle_state[cycle_key] = (current_index + 1) % len(
                        cycle_through
                    )

                    self.logger.info(
                        f"Power mode response cycling: index {current_index}, status 0x{current_status:04X}"
                    )

            response = self.message_handler.create_power_mode_response(current_status)

            # Log the power mode response
            status_names = {
                0x00: "Power Off",
                0x01: "Power On",
                0x02: "Power Standby",
                0x03: "Power Sleep",
                0x04: "Power Wake",
            }
            status_name = status_names.get(
                current_status, f"Unknown (0x{current_status:02X})"
            )
            self.logger.info(
                f"Power mode response: {status_name} (0x{current_status:04X})"
            )

            return response
        except Exception as e:
            self.logger.error(f"Error creating power mode response: {e}")
            return self.message_handler.create_power_mode_response(0x01)


    def get_server_info(self) -> dict:
        """Get UDP server information.

        Returns:
            Dictionary containing server information
        """
        return {
            "type": "UDP",
            "host": self.host,
            "port": self.port,
            "running": self.running,
        }

    def is_ready(self) -> bool:
        """Check if UDP server is ready to receive messages.

        Returns:
            True if server is ready
        """
        return self.running and self.udp_socket is not None

    def get_response_cycling_state(self) -> dict:
        """Get response cycling state for debugging.

        Returns:
            Dictionary containing response cycling state
        """
        return self.response_cycle_state.copy()
