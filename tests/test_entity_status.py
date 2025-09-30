#!/usr/bin/env python3
"""
Test module for DoIP Entity Status Request and Response functionality.
This module contains pytest tests for entity status message handling.
"""

import os
import struct
import sys
import time
import threading
import tempfile
import pytest

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from doip_server.doip_server import DoIPServer
from doip_client.udp_doip_client import UDPDoIPClient


class TestDoIPEntityStatus:
    """Test class for DoIP Entity Status functionality."""

    def setup_method(self):
        """Setup test environment before each test method."""
        self.server = None
        self.client = None
        self.server_thread = None

    def teardown_method(self):
        """Cleanup after each test method."""
        if self.server:
            self.server.stop()
        if self.client:
            self.client.stop()
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=2)

    def start_server(self, config_path=None):
        """Start the DoIP server in a separate thread."""
        self.server = DoIPServer(
            host="127.0.0.1",
            port=13401,  # Use different port to avoid conflicts
            gateway_config_path=config_path,
        )

        def run_server():
            try:
                self.server.start()
            except Exception as e:
                print(f"Server error: {e}")

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        # Give server time to start
        time.sleep(0.5)

    def start_client(self, port=13401):
        """Start the UDP DoIP client."""
        self.client = UDPDoIPClient(
            server_port=port, server_host="127.0.0.1", timeout=5.0
        )
        return self.client.start()

    def test_entity_status_request_creation(self):
        """Test creation of DoIP Entity Status Request message."""
        client = UDPDoIPClient()

        # Create entity status request
        request = client.create_entity_status_request()

        # Verify message structure
        assert (
            len(request) == 8
        ), "Entity status request should be 8 bytes (header only)"

        # Parse header
        protocol_version = request[0]
        inverse_protocol_version = request[1]
        payload_type = struct.unpack(">H", request[2:4])[0]
        payload_length = struct.unpack(">I", request[4:8])[0]

        # Verify header values
        assert protocol_version == 0x02, "Protocol version should be 0x02"
        assert (
            inverse_protocol_version == 0xFD
        ), "Inverse protocol version should be 0xFD"
        assert (
            payload_type == 0x4001
        ), "Payload type should be 0x4001 (Entity Status Request)"
        assert payload_length == 0, "Payload length should be 0 (no payload)"

    def test_entity_status_response_parsing(self):
        """Test parsing of DoIP Entity Status Response message."""
        client = UDPDoIPClient()

        # Create a mock entity status response
        mock_response = self.create_mock_entity_status_response(
            node_type=0x01,
            max_open_sockets=10,
            current_open_sockets=2,
            doip_entity_status=0x00,
            diagnostic_power_mode=0x02,
        )

        # Parse the response
        parsed_data = client.parse_entity_status_response(mock_response)

        # Verify parsed data
        assert parsed_data is not None, "Response should be parsed successfully"
        assert parsed_data["node_type"] == 0x01, "Node type should be 0x01"
        assert parsed_data["max_open_sockets"] == 10, "Max open sockets should be 10"
        assert (
            parsed_data["current_open_sockets"] == 2
        ), "Current open sockets should be 2"
        assert parsed_data["doip_entity_status"] == 0x00, "Entity status should be 0x00"
        assert (
            parsed_data["diagnostic_power_mode"] == 0x02
        ), "Diagnostic power mode should be 0x02"

    def test_entity_status_invalid_response(self):
        """Test handling of invalid entity status response."""
        client = UDPDoIPClient()

        # Test with too short data
        short_data = b"\x02\xfd\x40\x02\x00\x00\x00\x01"  # Missing payload
        parsed_data = client.parse_entity_status_response(short_data)
        assert parsed_data is None, "Short data should return None"

        # Test with wrong payload type
        wrong_type = b"\x02\xfd\x00\x01\x00\x00\x00\x05\x01\x0a\x02\x00\x02"  # Vehicle ID response
        parsed_data = client.parse_entity_status_response(wrong_type)
        assert parsed_data is None, "Wrong payload type should return None"

        # Test with wrong payload length
        wrong_length = b"\x02\xfd\x40\x02\x00\x00\x00\x03\x01\x0a\x02"  # Wrong length
        parsed_data = client.parse_entity_status_response(wrong_length)
        assert parsed_data is None, "Wrong payload length should return None"

    def test_entity_status_server_response(self):
        """Test server's entity status response generation."""
        # Start server with default config
        self.start_server()

        # Start client
        assert self.start_client(), "Client should start successfully"

        # Send entity status request
        response_data = self.client.send_entity_status_request()

        # Verify response
        assert response_data is not None, "Should receive entity status response"
        assert "node_type" in response_data, "Response should contain node_type"
        assert (
            "max_open_sockets" in response_data
        ), "Response should contain max_open_sockets"
        assert (
            "current_open_sockets" in response_data
        ), "Response should contain current_open_sockets"
        assert (
            "doip_entity_status" in response_data
        ), "Response should contain doip_entity_status"
        assert (
            "diagnostic_power_mode" in response_data
        ), "Response should contain diagnostic_power_mode"

    def test_entity_status_configuration_values(self):
        """Test that server uses configuration values correctly."""
        # Create a custom config file
        config_content = """
gateway:
  name: "Test Gateway"
  logical_address: 0x1000
  entity_status:
    node_type: 0x02
    max_open_sockets: 5
    current_open_sockets: 1
    doip_entity_status: 0x01
    diagnostic_power_mode: 0x01
"""

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(config_content)
            config_path = f.name

        try:
            # Start server with custom config
            self.start_server(config_path)

            # Start client
            assert self.start_client(), "Client should start successfully"

            # Send entity status request
            response_data = self.client.send_entity_status_request()

            # Verify response matches configuration
            assert response_data is not None, "Should receive entity status response"
            assert (
                response_data["node_type"] == 0x02
            ), "Node type should match config (0x02)"
            assert (
                response_data["max_open_sockets"] == 5
            ), "Max open sockets should match config (5)"
            assert (
                response_data["current_open_sockets"] == 1
            ), "Current open sockets should match config (1)"
            assert (
                response_data["doip_entity_status"] == 0x01
            ), "Entity status should match config (0x01)"
            assert (
                response_data["diagnostic_power_mode"] == 0x01
            ), "Diagnostic power mode should match config (0x01)"

        finally:
            # Clean up config file
            if os.path.exists(config_path):
                os.remove(config_path)

    def test_entity_status_multiple_requests(self):
        """Test multiple entity status requests."""
        # Start server
        self.start_server()

        # Start client
        assert self.start_client(), "Client should start successfully"

        # Send multiple requests
        responses = []
        for i in range(3):
            response_data = self.client.send_entity_status_request()
            assert response_data is not None, f"Request {i+1} should receive response"
            responses.append(response_data)
            time.sleep(0.1)  # Small delay between requests

        # All responses should be identical (no state changes)
        for i in range(1, len(responses)):
            assert (
                responses[i] == responses[0]
            ), f"Response {i+1} should match first response"

    def test_entity_status_with_vehicle_identification(self):
        """Test entity status alongside vehicle identification."""
        # Start server
        self.start_server()

        # Start client
        assert self.start_client(), "Client should start successfully"

        # Send vehicle identification request
        vin_response = self.client.send_vehicle_identification_request()
        assert (
            vin_response is not None
        ), "Should receive vehicle identification response"

        # Send entity status request
        status_response = self.client.send_entity_status_request()
        assert status_response is not None, "Should receive entity status response"

        # Both should work independently
        assert "vin" in vin_response, "VIN response should contain VIN"
        assert (
            "node_type" in status_response
        ), "Status response should contain node_type"

    def create_mock_entity_status_response(
        self,
        node_type,
        max_open_sockets,
        current_open_sockets,
        doip_entity_status,
        diagnostic_power_mode,
    ):
        """Create a mock DoIP Entity Status Response message for testing."""
        # Create payload
        payload = struct.pack(
            ">BBBBB",
            node_type,
            max_open_sockets,
            current_open_sockets,
            doip_entity_status,
            diagnostic_power_mode,
        )

        # Create header
        header = struct.pack(
            ">BBHI",
            0x02,  # Protocol version
            0xFD,  # Inverse protocol version
            0x4002,  # Entity Status Response payload type
            len(payload),  # Payload length
        )

        return header + payload


class TestDoIPEntityStatusIntegration:
    """Integration tests for DoIP Entity Status functionality."""

    def test_entity_status_server_logging(self):
        """Test that server logs entity status requests and responses."""
        import logging
        import io

        # Capture log output
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)

        # Setup server with custom logging
        server = DoIPServer(host="127.0.0.1", port=13402)
        server.logger.addHandler(handler)
        server.logger.setLevel(logging.INFO)

        # Start server in thread
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()
        time.sleep(0.5)

        try:
            # Start client
            client = UDPDoIPClient(server_port=13402, server_host="127.0.0.1")
            assert client.start(), "Client should start"

            # Send entity status request
            response = client.send_entity_status_request()
            assert response is not None, "Should receive response"

            # Check logs
            log_output = log_capture.getvalue()
            assert (
                "Processing DoIP entity status request" in log_output
            ), "Should log request processing"
            assert (
                "Entity Status Response:" in log_output
            ), "Should log response details"

        finally:
            server.stop()
            client.stop()
            server_thread.join(timeout=2)

    def test_entity_status_error_handling(self):
        """Test error handling in entity status functionality."""
        # Test with invalid server port
        client = UDPDoIPClient(server_port=9999, server_host="127.0.0.1", timeout=1.0)
        assert client.start(), "Client should start even with invalid port"

        # Send request to non-existent server
        response = client.send_entity_status_request()
        assert response is None, "Should not receive response from non-existent server"

        client.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
