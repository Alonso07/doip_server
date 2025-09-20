#!/usr/bin/env python3
"""
Tests for UDP DoIP Vehicle Identification functionality
"""

import struct
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doip_client.udp_doip_client import UDPDoIPClient
from doip_server.doip_server import DoIPServer


class TestUDPDoIPClient:
    """Test cases for UDP DoIP client"""

    def test_create_vehicle_identification_request(self):
        """Test vehicle identification request creation"""
        client = UDPDoIPClient()
        request = client.create_vehicle_identification_request()

        # Check request format
        assert len(request) == 8  # DoIP header only
        assert request[0] == 0x02  # Protocol version
        assert request[1] == 0xFD  # Inverse protocol version
        assert struct.unpack(">H", request[2:4])[0] == 0x0001  # Payload type
        assert struct.unpack(">I", request[4:8])[0] == 0  # Payload length

    def test_parse_vehicle_identification_response(self):
        """Test vehicle identification response parsing"""
        client = UDPDoIPClient()

        # Create a valid response
        vin = "1HGBH41JXMN109186"
        logical_address = 0x1000
        eid = b"\x12\x34\x56\x78\x9a\xbc"
        gid = b"\xde\xf0\x12\x34\x56\x78"
        further_action = 0x00
        sync_status = 0x00

        # Create payload
        payload = vin.encode("ascii").ljust(17, b"\x00")
        payload += struct.pack(">H", logical_address)
        payload += eid
        payload += gid
        payload += struct.pack(">B", further_action)
        payload += struct.pack(">B", sync_status)

        # Create DoIP header
        header = struct.pack(
            ">BBHI",
            0x02,  # Protocol version
            0xFD,  # Inverse protocol version
            0x0004,  # Payload type
            len(payload),
        )

        response_data = header + payload

        # Parse response
        result = client.parse_vehicle_identification_response(response_data)

        assert result is not None
        assert result["vin"] == vin
        assert result["logical_address"] == logical_address
        assert result["eid"] == eid.hex().upper()
        assert result["gid"] == gid.hex().upper()
        assert result["further_action_required"] == further_action
        assert result["vin_gid_sync_status"] == sync_status

    def test_parse_invalid_response(self):
        """Test parsing of invalid responses"""
        client = UDPDoIPClient()

        # Test too short response
        result = client.parse_vehicle_identification_response(b"\x02\xfd")
        assert result is None

        # Test wrong protocol version
        invalid_response = b"\x01\xfe\x00\x04\x00\x00\x00\x21" + b"\x00" * 33
        result = client.parse_vehicle_identification_response(invalid_response)
        assert result is None

        # Test wrong payload type
        invalid_response = b"\x02\xfd\x00\x01\x00\x00\x00\x21" + b"\x00" * 33
        result = client.parse_vehicle_identification_response(invalid_response)
        assert result is None

    def test_client_initialization(self):
        """Test client initialization"""
        client = UDPDoIPClient(server_port=13400, timeout=5.0)
        assert client.server_port == 13400
        assert client.timeout == 5.0
        assert client.broadcast_address == "255.255.255.255"
        assert client.socket is None


class TestDoIPServerUDP:
    """Test cases for DoIP server UDP functionality"""

    def test_vehicle_identification_response_creation(self):
        """Test vehicle identification response creation"""
        # Mock configuration manager
        mock_config = MagicMock()
        mock_config.get_vehicle_info.return_value = {
            "vin": "1HGBH41JXMN109186",
            "eid": "123456789ABC",
            "gid": "DEF012345678",
        }
        mock_config.get_gateway_info.return_value = {"logical_address": 0x1000}

        # Create server with mock config
        server = DoIPServer()
        server.config_manager = mock_config

        # Create response
        response = server.create_vehicle_identification_response()

        # Check response format
        assert len(response) == 8 + 33  # Header + payload
        assert response[0] == 0x02  # Protocol version
        assert response[1] == 0xFD  # Inverse protocol version
        assert struct.unpack(">H", response[2:4])[0] == 0x0004  # Payload type
        assert struct.unpack(">I", response[4:8])[0] == 33  # Payload length

        # Check payload content
        payload = response[8:]
        vin = payload[0:17].decode("ascii", errors="ignore").rstrip("\x00")
        logical_address = struct.unpack(">H", payload[17:19])[0]

        assert vin == "1HGBH41JXMN109186"
        assert logical_address == 0x1000

    def test_get_vehicle_vin(self):
        """Test VIN retrieval from configuration"""
        # Mock configuration manager
        mock_config = MagicMock()
        mock_config.get_vehicle_info.return_value = {"vin": "TEST1234567890123"}

        server = DoIPServer()
        server.config_manager = mock_config

        vin = server._get_vehicle_vin()
        assert vin == "TEST1234567890123"

    def test_get_vehicle_vin_fallback(self):
        """Test VIN fallback when configuration fails"""
        # Mock configuration manager without get_vehicle_info
        mock_config = MagicMock()
        mock_config.get_vehicle_info.side_effect = AttributeError()

        server = DoIPServer()
        server.config_manager = mock_config

        vin = server._get_vehicle_vin()
        assert vin == "1HGBH41JXMN109186"  # Default VIN

    def test_get_gateway_logical_address(self):
        """Test gateway logical address retrieval"""
        # Mock configuration manager
        mock_config = MagicMock()
        mock_config.get_gateway_info.return_value = {"logical_address": 0x2000}

        server = DoIPServer()
        server.config_manager = mock_config

        address = server._get_gateway_logical_address()
        assert address == 0x2000

    def test_get_vehicle_eid_gid(self):
        """Test EID and GID retrieval from configuration"""
        # Mock configuration manager
        mock_config = MagicMock()
        mock_config.get_vehicle_info.return_value = {
            "eid": "123456789ABC",
            "gid": "DEF012345678",
        }

        server = DoIPServer()
        server.config_manager = mock_config

        eid, gid = server._get_vehicle_eid_gid()
        assert eid == bytes.fromhex("123456789ABC")
        assert gid == bytes.fromhex("DEF012345678")


class TestUDPDoIPIntegration:
    """Integration tests for UDP DoIP functionality"""

    def test_udp_message_handling(self):
        """Test UDP message handling in server"""
        # Create server
        server = DoIPServer()

        # Mock UDP socket
        mock_socket = MagicMock()
        server.udp_socket = mock_socket

        # Create vehicle identification request
        request = b"\x02\xfd\x00\x01\x00\x00\x00\x00"

        # Test message handling
        server.handle_udp_message(request, ("127.0.0.1", 12345))

        # Verify sendto was called
        mock_socket.sendto.assert_called_once()
        response_data, addr = mock_socket.sendto.call_args[0]
        assert addr == ("127.0.0.1", 12345)
        assert len(response_data) > 8  # Should have header + payload

    def test_udp_message_handling_invalid_protocol(self):
        """Test UDP message handling with invalid protocol version"""
        server = DoIPServer()

        # Mock UDP socket
        mock_socket = MagicMock()
        server.udp_socket = mock_socket

        # Create invalid request (wrong protocol version)
        request = b"\x01\xfe\x00\x01\x00\x00\x00\x00"

        # Test message handling
        server.handle_udp_message(request, ("127.0.0.1", 12345))

        # Verify sendto was not called
        mock_socket.sendto.assert_not_called()

    def test_udp_message_handling_unsupported_payload_type(self):
        """Test UDP message handling with unsupported payload type"""
        server = DoIPServer()

        # Mock UDP socket
        mock_socket = MagicMock()
        server.udp_socket = mock_socket

        # Create request with unsupported payload type
        request = b"\x02\xfd\x00\x99\x00\x00\x00\x00"

        # Test message handling
        server.handle_udp_message(request, ("127.0.0.1", 12345))

        # Verify sendto was not called
        mock_socket.sendto.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
