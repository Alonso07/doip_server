#!/usr/bin/env python3
"""
Tests for UDP DoIP Vehicle Identification functionality
"""

import struct
import sys
import threading
import time
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


class TestEntityStatusUDP:
    """Test cases for DoIP Entity Status functionality over UDP"""

    def test_create_entity_status_request(self):
        """Test entity status request creation"""
        client = UDPDoIPClient()
        request = client.create_entity_status_request()

        # Check request format
        assert len(request) == 8  # DoIP header only
        assert request[0] == 0x02  # Protocol version
        assert request[1] == 0xFD  # Inverse protocol version
        assert struct.unpack(">H", request[2:4])[0] == 0x4001  # Payload type
        assert struct.unpack(">I", request[4:8])[0] == 0  # Payload length

    def test_parse_entity_status_response(self):
        """Test entity status response parsing"""
        client = UDPDoIPClient()

        # Create a valid response
        node_type = 0x01
        max_open_sockets = 10
        current_open_sockets = 2
        doip_entity_status = 0x00
        diagnostic_power_mode = 0x02

        # Create payload
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
            0x02,  # Protocol version
            0xFD,  # Inverse protocol version
            0x4002,  # Payload type
            len(payload),
        )

        response_data = header + payload

        # Parse response
        result = client.parse_entity_status_response(response_data)

        assert result is not None
        assert result["node_type"] == node_type
        assert result["max_open_sockets"] == max_open_sockets
        assert result["current_open_sockets"] == current_open_sockets
        assert result["doip_entity_status"] == doip_entity_status
        assert result["diagnostic_power_mode"] == diagnostic_power_mode

    def test_parse_entity_status_invalid_response(self):
        """Test parsing of invalid entity status responses"""
        client = UDPDoIPClient()

        # Test too short response
        result = client.parse_entity_status_response(b"\x02\xfd")
        assert result is None

        # Test wrong protocol version
        invalid_response = b"\x01\xfe\x40\x02\x00\x00\x00\x05\x01\x0a\x02\x00\x02"
        result = client.parse_entity_status_response(invalid_response)
        assert result is None

        # Test wrong payload type
        invalid_response = b"\x02\xfd\x00\x01\x00\x00\x00\x05\x01\x0a\x02\x00\x02"
        result = client.parse_entity_status_response(invalid_response)
        assert result is None

        # Test wrong payload length
        invalid_response = b"\x02\xfd\x40\x02\x00\x00\x00\x03\x01\x0a\x02"
        result = client.parse_entity_status_response(invalid_response)
        assert result is None

    def test_entity_status_response_creation(self):
        """Test entity status response creation"""
        # Mock configuration manager
        mock_config = MagicMock()
        mock_config.get_entity_status_config.return_value = {
            "node_type": 0x01,
            "max_open_sockets": 10,
            "current_open_sockets": 2,
            "doip_entity_status": 0x00,
            "diagnostic_power_mode": 0x02,
            "available_node_types": {0x01: {"name": "Vehicle Gateway"}},
            "available_entity_statuses": {0x00: {"name": "Ready"}},
            "available_diagnostic_power_modes": {0x02: {"name": "Power Off"}},
        }

        # Create server with mock config
        server = DoIPServer()
        server.config_manager = mock_config

        # Create response
        response = server.create_entity_status_response()

        # Check response format
        assert len(response) == 8 + 5  # Header + payload
        assert response[0] == 0x02  # Protocol version
        assert response[1] == 0xFD  # Inverse protocol version
        assert struct.unpack(">H", response[2:4])[0] == 0x4002  # Payload type
        assert struct.unpack(">I", response[4:8])[0] == 5  # Payload length

        # Check payload content
        payload = response[8:]
        node_type = payload[0]
        max_open_sockets = payload[1]
        current_open_sockets = payload[2]
        doip_entity_status = payload[3]
        diagnostic_power_mode = payload[4]

        assert node_type == 0x01
        assert max_open_sockets == 10
        assert current_open_sockets == 2
        assert doip_entity_status == 0x00
        assert diagnostic_power_mode == 0x02


class TestEntityStatusIntegration:
    """Integration tests for Entity Status functionality"""

    def test_entity_status_udp_message_handling(self):
        """Test entity status UDP message handling in server"""
        # Create server
        server = DoIPServer()

        # Mock UDP socket
        mock_socket = MagicMock()
        server.udp_socket = mock_socket

        # Create entity status request
        request = b"\x02\xfd\x40\x01\x00\x00\x00\x00"

        # Test message handling
        server.handle_udp_message(request, ("127.0.0.1", 12345))

        # Verify sendto was called
        mock_socket.sendto.assert_called_once()
        response_data, addr = mock_socket.sendto.call_args[0]
        assert addr == ("127.0.0.1", 12345)
        assert len(response_data) == 13  # Should have header (8) + payload (5)

    def test_entity_status_udp_message_handling_invalid_protocol(self):
        """Test entity status UDP message handling with invalid protocol version"""
        server = DoIPServer()

        # Mock UDP socket
        mock_socket = MagicMock()
        server.udp_socket = mock_socket

        # Create invalid request (wrong protocol version)
        request = b"\x01\xfe\x40\x01\x00\x00\x00\x00"

        # Test message handling
        server.handle_udp_message(request, ("127.0.0.1", 12345))

        # Verify sendto was not called
        mock_socket.sendto.assert_not_called()

    def test_entity_status_udp_message_handling_unsupported_payload_type(self):
        """Test entity status UDP message handling with unsupported payload type"""
        server = DoIPServer()

        # Mock UDP socket
        mock_socket = MagicMock()
        server.udp_socket = mock_socket

        # Create request with unsupported payload type
        request = b"\x02\xfd\x40\x99\x00\x00\x00\x00"

        # Test message handling
        server.handle_udp_message(request, ("127.0.0.1", 12345))

        # Verify sendto was not called
        mock_socket.sendto.assert_not_called()


class TestEntityStatusEndToEnd:
    """End-to-end tests for DoIP Entity Status functionality using port 13400"""

    def setup_method(self):
        """Setup test environment before each test method."""
        self.server = None
        self.client = None
        self.server_thread = None

    def teardown_method(self):
        """Cleanup after each test method."""
        if hasattr(self, "client") and self.client:
            self.client.stop()
        if hasattr(self, "server") and self.server:
            self.server.stop()
        if (
            hasattr(self, "server_thread")
            and self.server_thread
            and self.server_thread.is_alive()
        ):
            self.server_thread.join(timeout=3)

    def start_server(self, config_path=None):
        """Start the DoIP server in a separate thread."""
        self.server = DoIPServer(
            host="127.0.0.1",
            port=13400,  # Use standard port 13400
            gateway_config_path=config_path,
        )

        def run_server():
            try:
                self.server.start()
            except Exception as e:
                print(f"Server error: {e}")

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        # Give server time to start and verify it's running
        time.sleep(1)
        assert self.server.is_ready(), "Server should be ready after startup"

    def start_client(self):
        """Start the UDP DoIP client."""
        self.client = UDPDoIPClient(
            server_port=13400,  # Use standard port 13400
            server_host="127.0.0.1",
            timeout=10.0,
        )
        success = self.client.start()
        assert success, "Client should start successfully"
        return self.client

    def test_entity_status_basic_e2e(self):
        """Test basic end-to-end entity status request/response flow using port 13400"""
        # Start server
        self.start_server()

        # Start client
        self.start_client()

        # Send entity status request
        response = self.client.send_entity_status_request()

        # Verify response
        assert response is not None, "Should receive entity status response"

        # Verify response structure
        required_fields = [
            "node_type",
            "max_open_sockets",
            "current_open_sockets",
            "doip_entity_status",
            "diagnostic_power_mode",
        ]
        for field in required_fields:
            assert field in response, f"Response should contain {field}"

        # Verify response values are reasonable
        assert isinstance(response["node_type"], int), "Node type should be integer"
        assert isinstance(
            response["max_open_sockets"], int
        ), "Max open sockets should be integer"
        assert isinstance(
            response["current_open_sockets"], int
        ), "Current open sockets should be integer"
        assert isinstance(
            response["doip_entity_status"], int
        ), "Entity status should be integer"
        assert isinstance(
            response["diagnostic_power_mode"], int
        ), "Diagnostic power mode should be integer"

    def test_entity_status_with_custom_config_e2e(self):
        """Test entity status with custom configuration values using port 13400"""
        # Create custom configuration
        config_content = """
gateway:
  name: "Test Gateway E2E"
  logical_address: 0x2000
  entity_status:
    node_type: 0x02  # Node instead of Vehicle Gateway
    max_open_sockets: 15
    current_open_sockets: 3
    doip_entity_status: 0x01  # Not Ready
    diagnostic_power_mode: 0x01  # Power On
    available_node_types:
      0x01:
        name: "Vehicle Gateway"
        description: "DoIP entity is a vehicle gateway"
      0x02:
        name: "Node"
        description: "DoIP entity is a node"
    available_entity_statuses:
      0x00:
        name: "Ready"
        description: "Entity is ready for diagnostic communication"
      0x01:
        name: "Not Ready"
        description: "Entity is not ready for diagnostic communication"
    available_diagnostic_power_modes:
      0x01:
        name: "Power On"
        description: "Diagnostic power is on"
      0x02:
        name: "Power Off"
        description: "Diagnostic power is off"
      0x03:
        name: "Not Ready"
        description: "Diagnostic power is not ready"
"""

        config_path = "/tmp/test_entity_status_e2e_config.yaml"
        with open(config_path, "w") as f:
            f.write(config_content)

        try:
            # Start server with custom config
            self.start_server(config_path)

            # Start client
            self.start_client()

            # Send entity status request
            response = self.client.send_entity_status_request()

            # Verify response matches configuration
            assert response is not None, "Should receive entity status response"
            assert (
                response["node_type"] == 0x02
            ), f"Node type should be 0x02, got 0x{response['node_type']:02X}"
            assert (
                response["max_open_sockets"] == 15
            ), f"Max open sockets should be 15, got {response['max_open_sockets']}"
            assert (
                response["current_open_sockets"] == 3
            ), f"Current open sockets should be 3, got {response['current_open_sockets']}"
            assert (
                response["doip_entity_status"] == 0x01
            ), f"Entity status should be 0x01, got 0x{response['doip_entity_status']:02X}"
            assert (
                response["diagnostic_power_mode"] == 0x01
            ), f"Diagnostic power mode should be 0x01, got 0x{response['diagnostic_power_mode']:02X}"

        finally:
            # Clean up config file
            import os

            if os.path.exists(config_path):
                os.remove(config_path)

    def test_entity_status_with_vehicle_identification_e2e(self):
        """Test entity status alongside vehicle identification requests using port 13400"""
        # Start server
        self.start_server()

        # Start client
        self.start_client()

        # Send vehicle identification request
        vin_response = self.client.send_vehicle_identification_request()
        assert (
            vin_response is not None
        ), "Should receive vehicle identification response"

        # Send entity status request
        status_response = self.client.send_entity_status_request()
        assert status_response is not None, "Should receive entity status response"

        # Verify both responses are valid
        assert "vin" in vin_response, "VIN response should contain VIN"
        assert (
            "logical_address" in vin_response
        ), "VIN response should contain logical_address"
        assert (
            "node_type" in status_response
        ), "Status response should contain node_type"
        assert (
            "doip_entity_status" in status_response
        ), "Status response should contain doip_entity_status"

    def test_entity_status_multiple_requests_e2e(self):
        """Test multiple entity status requests using port 13400"""
        # Start server
        self.start_server()

        # Start client
        self.start_client()

        # Send multiple requests
        num_requests = 3
        responses = []

        for i in range(num_requests):
            response = self.client.send_entity_status_request()
            assert response is not None, f"Request {i+1} should receive response"
            responses.append(response)
            time.sleep(0.1)  # Small delay between requests

        # Verify all responses are identical (no state changes)
        first_response = responses[0]
        for i, response in enumerate(responses[1:], 1):
            assert (
                response == first_response
            ), f"Response {i+1} should match first response"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
