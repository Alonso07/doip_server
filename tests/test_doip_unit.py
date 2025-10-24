#!/usr/bin/env python3
"""
Unit tests for DoIP functionality.
Tests individual components without requiring server startup.
"""

import os
import sys
from pathlib import Path

import pytest

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


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
