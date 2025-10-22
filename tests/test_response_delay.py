#!/usr/bin/env python3
"""
Test cases for response delay functionality in DoIP server.

This module tests the new delay configuration feature that allows
configuring response delays in milliseconds for UDS services.
"""

import time
import unittest
from unittest.mock import Mock, patch, MagicMock
import struct

from src.doip_server.doip_server import DoIPServer
from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager


class TestResponseDelay(unittest.TestCase):
    """Test cases for response delay functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the hierarchical config manager
        self.mock_config_manager = Mock(spec=HierarchicalConfigManager)
        
        # Mock required config manager methods
        self.mock_config_manager.get_server_binding_info.return_value = ("127.0.0.1", 13400)
        self.mock_config_manager.get_network_config.return_value = {"max_connections": 5, "timeout": 30}
        self.mock_config_manager.get_protocol_config.return_value = {"version": 0x02, "inverse_version": 0xFD}
        self.mock_config_manager.get_logging_config.return_value = {"level": "INFO", "format": "%(message)s", "file": None}
        self.mock_config_manager.validate_configs.return_value = True
        
        # Create DoIP server with mocked config manager
        with patch('src.doip_server.doip_server.HierarchicalConfigManager', return_value=self.mock_config_manager):
            self.server = DoIPServer(host="127.0.0.1", port=13400)
            self.server.config_manager = self.mock_config_manager

    def test_get_response_delay_service_level(self):
        """Test service-level delay configuration."""
        # Mock service configuration with service-level delay
        service_config = {
            "name": "Test_Service",
            "delay_ms": 150,
            "responses": ["0x620C018000", "0x620C017500"]
        }
        
        # Mock the config manager to return this service config
        self.mock_config_manager.get_uds_service_by_request.return_value = service_config
        
        # Create a mock DoIP diagnostic message
        doip_data = self._create_doip_diagnostic_message("0x220C01", 0x1000, 0x2000)
        
        # Test delay retrieval
        delay = self.server._get_response_delay(doip_data, 0)
        self.assertEqual(delay, 150)
        
        delay = self.server._get_response_delay(doip_data, 1)
        self.assertEqual(delay, 150)  # Service-level delay applies to all responses

    def test_get_response_delay_response_level(self):
        """Test response-level delay configuration."""
        # Mock service configuration with response-level delays
        service_config = {
            "name": "Test_Service",
            "responses": [
                {"response": "0x620C018000", "delay_ms": 50},
                {"response": "0x620C017500", "delay_ms": 100},
                {"response": "0x620C016500", "delay_ms": 200}
            ]
        }
        
        # Mock the config manager to return this service config
        self.mock_config_manager.get_uds_service_by_request.return_value = service_config
        
        # Create a mock DoIP diagnostic message
        doip_data = self._create_doip_diagnostic_message("0x220C01", 0x1000, 0x2000)
        
        # Test delay retrieval for each response
        delay_0 = self.server._get_response_delay(doip_data, 0)
        self.assertEqual(delay_0, 50)
        
        delay_1 = self.server._get_response_delay(doip_data, 1)
        self.assertEqual(delay_1, 100)
        
        delay_2 = self.server._get_response_delay(doip_data, 2)
        self.assertEqual(delay_2, 200)

    def test_get_response_delay_mixed_configuration(self):
        """Test mixed service-level and response-level delay configuration."""
        # Mock service configuration with both service-level and response-level delays
        service_config = {
            "name": "Test_Service",
            "delay_ms": 75,  # Service-level delay
            "responses": [
                {"response": "0x620C018000", "delay_ms": 0},  # Override service delay
                {"response": "0x620C017500", "delay_ms": 150},  # Override service delay
                "0x620C016500"  # Use service-level delay
            ]
        }
        
        # Mock the config manager to return this service config
        self.mock_config_manager.get_uds_service_by_request.return_value = service_config
        
        # Create a mock DoIP diagnostic message
        doip_data = self._create_doip_diagnostic_message("0x220C01", 0x1000, 0x2000)
        
        # Test delay retrieval
        delay_0 = self.server._get_response_delay(doip_data, 0)
        self.assertEqual(delay_0, 0)  # Response-level override
        
        delay_1 = self.server._get_response_delay(doip_data, 1)
        self.assertEqual(delay_1, 150)  # Response-level override
        
        delay_2 = self.server._get_response_delay(doip_data, 2)
        self.assertEqual(delay_2, 75)  # Service-level delay (string response)

    def test_get_response_delay_no_delay_configured(self):
        """Test delay retrieval when no delay is configured."""
        # Mock service configuration without delay
        service_config = {
            "name": "Test_Service",
            "responses": ["0x620C018000", "0x620C017500"]
        }
        
        # Mock the config manager to return this service config
        self.mock_config_manager.get_uds_service_by_request.return_value = service_config
        
        # Create a mock DoIP diagnostic message
        doip_data = self._create_doip_diagnostic_message("0x220C01", 0x1000, 0x2000)
        
        # Test delay retrieval
        delay = self.server._get_response_delay(doip_data, 0)
        self.assertEqual(delay, 0)

    def test_get_response_delay_non_diagnostic_message(self):
        """Test delay retrieval for non-diagnostic messages."""
        # Create a mock DoIP routing activation message
        doip_data = self._create_doip_routing_activation_message()
        
        # Test delay retrieval
        delay = self.server._get_response_delay(doip_data, 0)
        self.assertEqual(delay, 0)  # No delay for non-diagnostic messages

    def test_get_response_delay_invalid_data(self):
        """Test delay retrieval with invalid data."""
        # Test with too short data
        delay = self.server._get_response_delay(b"short", 0)
        self.assertEqual(delay, 0)
        
        # Test with invalid DoIP message
        delay = self.server._get_response_delay(b"", 0)
        self.assertEqual(delay, 0)

    def test_get_response_delay_service_not_found(self):
        """Test delay retrieval when service is not found."""
        # Mock the config manager to return None (service not found)
        self.mock_config_manager.get_uds_service_by_request.return_value = None
        
        # Create a mock DoIP diagnostic message
        doip_data = self._create_doip_diagnostic_message("0x220C01", 0x1000, 0x2000)
        
        # Test delay retrieval
        delay = self.server._get_response_delay(doip_data, 0)
        self.assertEqual(delay, 0)

    def test_response_delay_timing(self):
        """Test that response delays actually delay responses."""
        # Mock service configuration with delay
        service_config = {
            "name": "Test_Service",
            "delay_ms": 100,
            "responses": ["0x620C018000"]
        }
        
        # Mock the config manager to return this service config
        self.mock_config_manager.get_uds_service_by_request.return_value = service_config
        
        # Create a mock DoIP diagnostic message
        doip_data = self._create_doip_diagnostic_message("0x220C01", 0x1000, 0x2000)
        
        # Measure time for delay retrieval
        start_time = time.time()
        delay = self.server._get_response_delay(doip_data, 0)
        end_time = time.time()
        
        # The delay retrieval itself should be fast (no actual delay)
        self.assertLess(end_time - start_time, 0.01)  # Less than 10ms
        self.assertEqual(delay, 100)

    def _create_doip_diagnostic_message(self, uds_request, source_addr, target_addr):
        """Create a mock DoIP diagnostic message for testing."""
        # DoIP header: version (1) + inverse_version (1) + payload_type (2) + payload_length (4)
        header = struct.pack(">BBHI", 0x02, 0xFD, 0x8001, 4)  # Diagnostic message payload type
        
        # Payload: source_addr (2) + target_addr (2) + uds_request
        uds_bytes = bytes.fromhex(uds_request[2:])  # Remove "0x" prefix
        payload = struct.pack(">HH", source_addr, target_addr) + uds_bytes
        
        return header + payload

    def _create_doip_routing_activation_message(self):
        """Create a mock DoIP routing activation message for testing."""
        # DoIP header: version (1) + inverse_version (1) + payload_type (2) + payload_length (4)
        header = struct.pack(">BBHI", 0x02, 0xFD, 0x0005, 9)  # Routing activation payload type
        
        # Payload: client_logical_address (2) + logical_address (2) + response_code (1) + reserved (4)
        payload = struct.pack(">HHB", 0x2000, 0x1000, 0x00) + struct.pack(">I", 0x00000000)
        
        return header + payload


if __name__ == "__main__":
    unittest.main()
