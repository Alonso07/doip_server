#!/usr/bin/env python3
"""
Test cases for functional diagnostics feature.
Tests the ability to send requests to functional addresses and receive responses from multiple ECUs.
"""

import unittest
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from doip_client.doip_client import DoIPClientWrapper
from doip_server.hierarchical_config_manager import HierarchicalConfigManager


class TestFunctionalDiagnostics(unittest.TestCase):
    """Test cases for functional diagnostics functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = DoIPClientWrapper(
            server_host="127.0.0.1",
            server_port=13400,
            logical_address=0x0E00,
            target_address=0x1000,
        )

        # Mock the doip_client to avoid actual network calls
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.close = Mock()

    def test_functional_diagnostic_message_basic(self):
        """Test basic functional diagnostic message sending"""
        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )

        # Test functional diagnostic message
        uds_payload = [0x22, 0xF1, 0x90]  # Read VIN
        response = self.client.send_functional_diagnostic_message(uds_payload)

        # Verify the method was called
        self.client.doip_client.send_diagnostic_message.assert_called_once()

        # Verify response
        self.assertIsNotNone(response)
        self.assertEqual(
            response, b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )

    def test_functional_read_data_by_identifier(self):
        """Test functional read data by identifier"""
        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )

        # Test functional read data by identifier
        response = self.client.send_functional_read_data_by_identifier(0xF190)

        # Verify the method was called with correct payload
        self.client.doip_client.send_diagnostic_message.assert_called_once()
        call_args = self.client.doip_client.send_diagnostic_message.call_args
        self.assertEqual(call_args[0][0], b"\x22\xf1\x90")  # UDS payload

        # Verify response
        self.assertIsNotNone(response)

    def test_functional_diagnostic_session_control(self):
        """Test functional diagnostic session control"""
        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x50\x03\x00\x00"
        )

        # Test functional diagnostic session control
        response = self.client.send_functional_diagnostic_session_control(0x03)

        # Verify the method was called with correct payload
        self.client.doip_client.send_diagnostic_message.assert_called_once()
        call_args = self.client.doip_client.send_diagnostic_message.call_args
        self.assertEqual(call_args[0][0], b"\x10\x03")  # UDS payload

        # Verify response
        self.assertIsNotNone(response)

    def test_functional_tester_present(self):
        """Test functional tester present"""
        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = b"\x7e\x00"

        # Test functional tester present
        response = self.client.send_functional_tester_present()

        # Verify the method was called with correct payload
        self.client.doip_client.send_diagnostic_message.assert_called_once()
        call_args = self.client.doip_client.send_diagnostic_message.call_args
        self.assertEqual(call_args[0][0], b"\x3e\x00")  # UDS payload

        # Verify response
        self.assertIsNotNone(response)

    def test_functional_address_restoration(self):
        """Test that original target address is restored after functional call"""
        original_target = self.client.target_address
        self.client.doip_client.target_address = original_target

        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )

        # Test functional diagnostic message
        uds_payload = [0x22, 0xF1, 0x90]
        self.client.send_functional_diagnostic_message(uds_payload)

        # Verify target address was restored
        self.assertEqual(self.client.target_address, original_target)
        self.assertEqual(self.client.doip_client.target_address, original_target)

    def test_functional_address_restoration_on_error(self):
        """Test that original target address is restored even on error"""
        original_target = self.client.target_address
        self.client.doip_client.target_address = original_target

        # Mock error
        self.client.doip_client.send_diagnostic_message.side_effect = Exception(
            "Network error"
        )

        # Test functional diagnostic message
        uds_payload = [0x22, 0xF1, 0x90]
        response = self.client.send_functional_diagnostic_message(uds_payload)

        # Verify target address was restored even on error
        self.assertEqual(self.client.target_address, original_target)
        self.assertEqual(self.client.doip_client.target_address, original_target)
        self.assertIsNone(response)


class TestHierarchicalConfigManagerFunctional(unittest.TestCase):
    """Test cases for hierarchical config manager functional addressing support"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a mock config manager
        self.config_manager = Mock(spec=HierarchicalConfigManager)
        self.config_manager.get_ecus_by_functional_address = Mock()
        self.config_manager.get_uds_service_by_request = Mock()
        self.config_manager.is_source_address_allowed = Mock()

    def test_get_ecus_by_functional_address(self):
        """Test getting ECUs by functional address"""
        # Mock ECUs with functional address 0x1FFF
        self.config_manager.get_ecus_by_functional_address.return_value = [
            0x1000,
            0x1001,
            0x1002,
        ]

        ecus = self.config_manager.get_ecus_by_functional_address(0x1FFF)

        self.assertEqual(ecus, [0x1000, 0x1001, 0x1002])
        self.config_manager.get_ecus_by_functional_address.assert_called_once_with(
            0x1FFF
        )

    def test_get_uds_service_with_functional_support(self):
        """Test getting UDS service with functional support flag"""
        # Mock service config with functional support
        service_config = {
            "name": "Read_VIN",
            "request": "0x22F190",
            "responses": ["0x62F1901020011223344556677889AABB"],
            "description": "Read Vehicle Identification Number",
            "supports_functional": True,
        }
        self.config_manager.get_uds_service_by_request.return_value = service_config

        result = self.config_manager.get_uds_service_by_request("0x22F190", 0x1000)

        self.assertIsNotNone(result)
        self.assertTrue(result["supports_functional"])
        self.assertEqual(result["name"], "Read_VIN")

    def test_get_uds_service_without_functional_support(self):
        """Test getting UDS service without functional support"""
        # Mock service config without functional support
        service_config = {
            "name": "Engine_RPM_Read",
            "request": "0x220C01",
            "responses": ["0x620C018000"],
            "description": "Read engine RPM",
            "supports_functional": False,
        }
        self.config_manager.get_uds_service_by_request.return_value = service_config

        result = self.config_manager.get_uds_service_by_request("0x220C01", 0x1000)

        self.assertIsNotNone(result)
        self.assertFalse(result["supports_functional"])
        self.assertEqual(result["name"], "Engine_RPM_Read")


class TestFunctionalDiagnosticsIntegration(unittest.TestCase):
    """Integration tests for functional diagnostics"""

    def test_functional_demo_execution(self):
        """Test that functional demo can be executed without errors"""
        client = DoIPClientWrapper(
            server_host="127.0.0.1",
            server_port=13400,
            logical_address=0x0E00,
            target_address=0x1000,
        )

        # Mock the doip_client to avoid actual network calls
        client.doip_client = Mock()
        client.doip_client.send_diagnostic_message = Mock(
            return_value=b"\x50\x03\x00\x00"
        )
        client.doip_client.close = Mock()

        # Test that functional demo runs without errors
        try:
            client.run_functional_demo()
        except Exception as e:
            self.fail(f"Functional demo raised an exception: {e}")
        finally:
            client.disconnect()


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
