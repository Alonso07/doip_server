#!/usr/bin/env python3
"""
Unit tests for DoIP functionality.
Tests individual components without requiring server startup.
"""

import os
import struct
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doip_server.doip_server import DoIPServer
from doip_server.hierarchical_config_manager import HierarchicalConfigManager


class TestDoIPMessageFormats:
    """Test DoIP message format construction without server"""

    def test_doip_header_creation(self):
        """Test DoIP header creation"""
        import struct

        # Create header manually
        protocol_version = 0x02
        inverse_version = 0xFD
        payload_type = 0x0005
        payload_length = 4

        header = struct.pack(
            ">BBHI", protocol_version, inverse_version, payload_type, payload_length
        )

        assert len(header) == 8
        assert header[0] == 0x02
        assert header[1] == 0xFD
        assert header[2:4] == b"\x00\x05"
        assert header[4:8] == b"\x00\x00\x00\x04"

    def test_routine_activation_payload(self):
        """Test routine activation payload creation"""
        import struct

        routine_id = 0x0202
        routine_type = 0x0001

        payload = struct.pack(">HH", routine_id, routine_type)

        assert len(payload) == 4
        assert payload[0:2] == b"\x02\x02"
        assert payload[2:4] == b"\x00\x01"

    def test_uds_payload_creation(self):
        """Test UDS payload creation"""
        import struct

        service_id = 0x22
        data_identifier = 0xF187

        payload = bytes([service_id]) + struct.pack(">H", data_identifier)

        assert len(payload) == 3
        assert payload[0] == 0x22
        assert payload[1:3] == b"\xf1\x87"


class TestProcessDoIPMessageReturnType:
    """Verify process_doip_message always returns list[bytes] | None."""

    def _make_server(self):
        return DoIPServer(gateway_config_path="config/gateway1.yaml")

    def _build_message(self, payload_type: int, payload: bytes = b"") -> bytes:
        return struct.pack(">BBHI", 0x02, 0xFD, payload_type, len(payload)) + payload

    def test_routing_activation_returns_list(self):
        """Routing activation response must be a list."""
        server = self._make_server()
        # Minimal routing activation payload: source(2) + activation_type(2) + reserved(1+4)
        payload = struct.pack(">HHBII", 0x0E00, 0x0001, 0x00, 0, 0)
        msg = self._build_message(0x0005, payload)
        result = server.process_doip_message(msg)
        assert isinstance(result, list), "Routing activation must return list"
        assert len(result) >= 1

    def test_alive_check_returns_list(self):
        """Alive check response must be a list."""
        server = self._make_server()
        msg = self._build_message(0x0007)
        result = server.process_doip_message(msg)
        assert isinstance(result, list), "Alive check must return list"
        assert len(result) == 1

    def test_power_mode_returns_list(self):
        """Power mode response must be a list."""
        server = self._make_server()
        msg = self._build_message(0x4003)
        result = server.process_doip_message(msg)
        assert isinstance(result, list), "Power mode response must return list"
        assert len(result) == 1

    def test_entity_status_returns_list(self):
        """Entity status response must be a list."""
        server = self._make_server()
        msg = self._build_message(0x4001)
        result = server.process_doip_message(msg)
        assert isinstance(result, list), "Entity status response must return list"
        assert len(result) == 1

    def test_invalid_protocol_version_returns_list(self):
        """Protocol version NACK must be a list."""
        server = self._make_server()
        msg = struct.pack(">BBHI", 0x99, 0x66, 0x0007, 0)
        result = server.process_doip_message(msg)
        assert isinstance(result, list), "NACK must return list"

    def test_unknown_payload_type_returns_none(self):
        """Unknown payload type must return None (no response)."""
        server = self._make_server()
        msg = self._build_message(0x9999)
        result = server.process_doip_message(msg)
        assert result is None, "Unknown payload type must return None"

    def test_too_short_message_returns_none(self):
        """Messages shorter than 8 bytes must return None."""
        server = self._make_server()
        result = server.process_doip_message(b"\x02\xfd\x00\x07")
        assert result is None
