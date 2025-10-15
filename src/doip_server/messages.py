#!/usr/bin/env python3
"""
DoIP Message handling module.

This module provides classes and functions for creating, parsing, and handling
DoIP (Diagnostics over IP) messages according to ISO 13400-2:2019.
"""
import struct
import logging
from typing import Optional, Tuple, Dict, Any


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

# Response codes
ROUTING_ACTIVATION_RESPONSE_CODE_SUCCESS = 0x10
ROUTING_ACTIVATION_RESPONSE_CODE_UNKNOWN_SOURCE_ADDRESS = 0x02
ROUTING_ACTIVATION_RESPONSE_CODE_ALL_SOCKETS_TAKEN = 0x03
ROUTING_ACTIVATION_RESPONSE_CODE_DIFFERENT_SOURCE_ADDRESS = 0x04
ROUTING_ACTIVATION_RESPONSE_CODE_ALREADY_ACTIVATED = 0x05


class DoIPMessage:
    """Base class for DoIP message handling."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize DoIP message handler.

        Args:
            logger: Logger instance for this message handler
        """
        self.logger = logger or logging.getLogger(__name__)

    def create_doip_header(self, payload_type: int, payload_length: int) -> bytes:
        """Create DoIP message header.

        Args:
            payload_type: DoIP payload type
            payload_length: Length of payload in bytes

        Returns:
            DoIP message header as bytes
        """
        return struct.pack(
            ">BBHI",
            DOIP_PROTOCOL_VERSION,
            DOIP_INVERSE_PROTOCOL_VERSION,
            payload_type,
            payload_length,
        )

    def create_doip_message(self, payload_type: int, payload: bytes) -> bytes:
        """Create complete DoIP message with header and payload.

        Args:
            payload_type: DoIP payload type
            payload: Message payload as bytes

        Returns:
            Complete DoIP message as bytes
        """
        header = self.create_doip_header(payload_type, len(payload))
        return header + payload

    def parse_doip_header(self, data: bytes) -> Tuple[int, int, int]:
        """Parse DoIP message header.

        Args:
            data: Raw DoIP message data

        Returns:
            Tuple of (protocol_version, payload_type, payload_length)

        Raises:
            ValueError: If header is invalid or too short
        """
        if len(data) < 8:
            raise ValueError("DoIP header too short")

        protocol_version, inverse_version, payload_type, payload_length = struct.unpack(
            ">BBHI", data[:8]
        )

        if protocol_version != DOIP_PROTOCOL_VERSION:
            raise ValueError(f"Invalid protocol version: {protocol_version}")

        if inverse_version != DOIP_INVERSE_PROTOCOL_VERSION:
            raise ValueError(f"Invalid inverse protocol version: {inverse_version}")

        return protocol_version, payload_type, payload_length

    def create_routing_activation_response(
        self, response_code: int, client_logical_address: int, logical_address: int
    ) -> bytes:
        """Create routing activation response message.

        Args:
            response_code: Response code for the activation
            client_logical_address: Client's logical address
            logical_address: Server's logical address

        Returns:
            Complete DoIP routing activation response message
        """
        # Create payload according to DoIP standard: !HHBLL format
        payload = struct.pack(">H", client_logical_address)  # Client logical address
        payload += struct.pack(
            ">H", logical_address
        )  # Gateway logical address (source)
        payload += struct.pack(">B", response_code)  # Response code
        payload += struct.pack(">I", 0x00000000)  # Reserved (4 bytes)
        payload += struct.pack(">I", 0x00000000)  # VM specific (4 bytes)

        return self.create_doip_message(
            PAYLOAD_TYPE_ROUTING_ACTIVATION_RESPONSE, payload
        )

    def create_diagnostic_message_response(
        self, source_addr: int, target_addr: int, uds_response: bytes
    ) -> bytes:
        """Create diagnostic message response.

        Args:
            source_addr: Source logical address
            target_addr: Target logical address
            uds_response: UDS response payload

        Returns:
            Complete DoIP diagnostic message response
        """
        payload = struct.pack(">HH", source_addr, target_addr) + uds_response
        return self.create_doip_message(PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE, payload)

    def create_diagnostic_message_ack(
        self, source_addr: int, target_addr: int, ack_code: int = 0x00
    ) -> bytes:
        """Create DoIP diagnostic message acknowledgment.

        Args:
            source_addr: Source logical address
            target_addr: Target logical address
            ack_code: Acknowledgment code (default: 0x00)

        Returns:
            Complete DoIP diagnostic message ACK
        """
        payload = struct.pack(">BHH", ack_code, source_addr, target_addr)
        return self.create_doip_message(PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE_ACK, payload)

    def create_doip_nack(self, nack_code: int) -> bytes:
        """Create DoIP negative acknowledgment.

        Args:
            nack_code: NACK code

        Returns:
            Complete DoIP NACK message
        """
        payload = struct.pack(">I", nack_code)
        return self.create_doip_message(PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE_NACK, payload)

    def create_alive_check_response(self) -> bytes:
        """Create alive check response message.

        Returns:
            Complete DoIP alive check response
        """
        # DoIP alive check response should have 6 bytes payload
        payload = b"\x00" * 6
        return self.create_doip_message(PAYLOAD_TYPE_ALIVE_CHECK_RESPONSE, payload)

    def create_vehicle_identification_response(
        self, vin: str, logical_address: int, eid: bytes, gid: bytes
    ) -> bytes:
        """Create vehicle identification response message.

        Args:
            vin: Vehicle Identification Number (17 characters)
            logical_address: Gateway logical address
            eid: Entity ID (6 bytes)
            gid: Group ID (6 bytes)

        Returns:
            Complete DoIP vehicle identification response
        """
        # Ensure VIN is exactly 17 characters
        vin_bytes = vin.encode("ascii").ljust(17, b"\x00")[:17]

        # Further action required (1 byte) - 0x00 = no further action required
        further_action_required = 0x00

        # VIN/GID synchronization status (1 byte) - 0x00 = synchronized
        vin_gid_sync_status = 0x00

        # Pack the response: VIN(17) + Logical Address(2) + EID(6) + GID(6) +
        # Further Action(1) + Sync Status(1)
        payload = (
            vin_bytes
            + struct.pack(">H", logical_address)
            + eid
            + gid
            + struct.pack(">BB", further_action_required, vin_gid_sync_status)
        )
        return self.create_doip_message(
            PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_RESPONSE, payload
        )

    def create_power_mode_response(self, power_mode: int) -> bytes:
        """Create power mode information response.

        Args:
            power_mode: Power mode value

        Returns:
            Complete DoIP power mode response
        """
        payload = struct.pack(">H", power_mode)
        return self.create_doip_message(
            PAYLOAD_TYPE_POWER_MODE_INFORMATION_RESPONSE, payload
        )

    def create_entity_status_response(
        self,
        node_type: int = 0x01,
        max_open_sockets: int = 10,
        current_open_sockets: int = 0,
        doip_entity_status: int = 0x00,
        diagnostic_power_mode: int = 0x02,
    ) -> bytes:
        """Create DoIP entity status response.

        Args:
            node_type: Node type (1 byte)
            max_open_sockets: Maximum open sockets (1 byte)
            current_open_sockets: Current open sockets (1 byte)
            doip_entity_status: DoIP entity status (1 byte)
            diagnostic_power_mode: Diagnostic power mode (1 byte)

        Returns:
            Complete DoIP entity status response
        """
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
        return self.create_doip_message(PAYLOAD_TYPE_ENTITY_STATUS_RESPONSE, payload)

    def create_uds_negative_response(self, service_id: int, nrc: int) -> bytes:
        """Create UDS negative response.

        Args:
            service_id: UDS service ID that failed
            nrc: Negative response code

        Returns:
            UDS negative response as bytes
        """
        # UDS negative response format: 0x7F + service_id + NRC
        return struct.pack(">BBB", 0x7F, service_id, nrc)

    def parse_routing_activation_request(self, payload: bytes) -> Tuple[int, int]:
        """Parse routing activation request payload.

        Args:
            payload: Raw payload data

        Returns:
            Tuple of (source_address, activation_type)

        Raises:
            ValueError: If payload is invalid
        """
        if len(payload) < 3:
            raise ValueError("Routing activation request payload too short")

        source_address, activation_type = struct.unpack(">HB", payload[:3])
        return source_address, activation_type

    def parse_diagnostic_message(self, payload: bytes) -> Tuple[int, int, bytes]:
        """Parse diagnostic message payload.

        Args:
            payload: Raw payload data

        Returns:
            Tuple of (source_address, target_address, uds_payload)

        Raises:
            ValueError: If payload is invalid
        """
        if len(payload) < 4:
            raise ValueError("Diagnostic message payload too short")

        source_address, target_address = struct.unpack(">HH", payload[:4])
        uds_payload = payload[4:]
        return source_address, target_address, uds_payload
