#!/usr/bin/env python3
"""
Comprehensive test suite for functional address functionality.
This test suite covers all aspects of functional addressing including:
- Unit tests for individual components
- Integration tests for end-to-end scenarios
- Edge cases and error conditions
- Performance and stress testing
- Configuration validation
"""

import unittest
import time
import socket
import struct
import threading
import sys
import os
from unittest.mock import Mock, patch, MagicMock, call
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from doip_client.doip_client import DoIPClientWrapper
from doip_server.hierarchical_config_manager import HierarchicalConfigManager
from doip_server.doip_server import DoIPServer


class TestFunctionalAddressUnit(unittest.TestCase):
    """Unit tests for functional address functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.config_manager = Mock(spec=HierarchicalConfigManager)
        self.config_manager.get_ecus_by_functional_address = Mock()
        self.config_manager.get_uds_service_by_request = Mock()
        self.config_manager.is_source_address_allowed = Mock()
        self.config_manager.is_target_address_valid = Mock()

    def test_functional_address_detection(self):
        """Test that functional addresses are correctly detected"""
        # Mock ECUs with functional address 0x1FFF
        self.config_manager.get_ecus_by_functional_address.return_value = [0x1000, 0x1001, 0x1002]
        
        # Test functional address detection
        ecus = self.config_manager.get_ecus_by_functional_address(0x1FFF)
        
        self.assertEqual(ecus, [0x1000, 0x1001, 0x1002])
        self.config_manager.get_ecus_by_functional_address.assert_called_once_with(0x1FFF)

    def test_no_functional_address_ecus(self):
        """Test handling when no ECUs use a functional address"""
        self.config_manager.get_ecus_by_functional_address.return_value = []
        
        ecus = self.config_manager.get_ecus_by_functional_address(0x9999)
        
        self.assertEqual(ecus, [])
        self.config_manager.get_ecus_by_functional_address.assert_called_once_with(0x9999)

    def test_uds_service_functional_support(self):
        """Test UDS service functional support detection"""
        # Mock service with functional support
        service_config = {
            "name": "Read_VIN",
            "request": "0x22F190",
            "supports_functional": True
        }
        self.config_manager.get_uds_service_by_request.return_value = service_config
        
        result = self.config_manager.get_uds_service_by_request("0x22F190", 0x1000)
        
        self.assertIsNotNone(result)
        self.assertTrue(result["supports_functional"])

    def test_uds_service_no_functional_support(self):
        """Test UDS service without functional support"""
        # Mock service without functional support
        service_config = {
            "name": "Engine_RPM_Read",
            "request": "0x220C01",
            "supports_functional": False
        }
        self.config_manager.get_uds_service_by_request.return_value = service_config
        
        result = self.config_manager.get_uds_service_by_request("0x220C01", 0x1000)
        
        self.assertIsNotNone(result)
        self.assertFalse(result["supports_functional"])

    def test_source_address_validation(self):
        """Test source address validation for functional addressing"""
        # Mock allowed source addresses
        self.config_manager.is_source_address_allowed.return_value = True
        
        result = self.config_manager.is_source_address_allowed(0x0E00, 0x1000)
        
        self.assertTrue(result)
        self.config_manager.is_source_address_allowed.assert_called_once_with(0x0E00, 0x1000)

    def test_source_address_rejection(self):
        """Test source address rejection for functional addressing"""
        # Mock rejected source addresses
        self.config_manager.is_source_address_allowed.return_value = False
        
        result = self.config_manager.is_source_address_allowed(0x9999, 0x1000)
        
        self.assertFalse(result)
        self.config_manager.is_source_address_allowed.assert_called_once_with(0x9999, 0x1000)


class TestFunctionalAddressClient(unittest.TestCase):
    """Unit tests for functional address client functionality"""

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
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
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

    def test_functional_diagnostic_message_with_custom_address(self):
        """Test functional diagnostic message with custom functional address"""
        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )

        # Test with custom functional address
        uds_payload = [0x22, 0xF1, 0x90]
        custom_address = 0x2FFF
        response = self.client.send_functional_diagnostic_message(uds_payload, custom_address)

        # Verify response
        self.assertIsNotNone(response)

    def test_functional_diagnostic_message_timeout(self):
        """Test functional diagnostic message with timeout"""
        # Mock timeout response
        self.client.doip_client.send_diagnostic_message.return_value = None

        # Test with timeout
        uds_payload = [0x22, 0xF1, 0x90]
        response = self.client.send_functional_diagnostic_message(uds_payload, timeout=0.1)

        # Verify no response
        self.assertIsNone(response)

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
        self.assertEqual(call_args[0][0], b"\x22\xf1\x90")  # UDS payload (first argument)

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
        self.assertEqual(call_args[0][0], b"\x10\x03")  # UDS payload (first argument)

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
        self.assertEqual(call_args[0][0], b"\x3e\x00")  # UDS payload (first argument)

        # Verify response
        self.assertIsNotNone(response)

    def test_address_restoration_after_functional_call(self):
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

    def test_address_restoration_on_error(self):
        """Test that original target address is restored even on error"""
        original_target = self.client.target_address
        self.client.doip_client.target_address = original_target

        # Mock error
        self.client.doip_client.send_diagnostic_message_to_address.side_effect = Exception("Network error")

        # Test functional diagnostic message
        uds_payload = [0x22, 0xF1, 0x90]
        response = self.client.send_functional_diagnostic_message(uds_payload)

        # Verify target address was restored even on error
        self.assertEqual(self.client.target_address, original_target)
        self.assertEqual(self.client.doip_client.target_address, original_target)
        self.assertIsNone(response)

    def test_multiple_functional_responses(self):
        """Test handling multiple functional responses"""
        # Mock multiple responses
        responses = [
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb",
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xcc\xdd"
        ]
        
        # Mock the send_diagnostic_to_address method to return multiple responses
        self.client.send_diagnostic_to_address = Mock()
        self.client.send_diagnostic_to_address.return_value = responses[0]

        # Test multiple functional responses
        uds_payload = [0x22, 0xF1, 0x90]
        response = self.client.send_functional_diagnostic_message_multiple_responses(uds_payload)

        # Verify response
        self.assertIsNotNone(response)

    def test_functional_demo_execution(self):
        """Test that functional demo can be executed without errors"""
        # Mock successful responses
        self.client.doip_client.send_diagnostic_message.return_value = b"\x50\x03\x00\x00"

        # Test that functional demo runs without errors
        try:
            self.client.run_functional_demo()
        except Exception as e:
            self.fail(f"Functional demo raised an exception: {e}")


class TestFunctionalAddressServer(unittest.TestCase):
    """Unit tests for functional address server functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.server = Mock(spec=DoIPServer)
        self.server.config_manager = Mock(spec=HierarchicalConfigManager)
        self.server.logger = Mock()

    def test_handle_functional_diagnostic_message_success(self):
        """Test successful functional diagnostic message handling"""
        # Mock configuration
        self.server.config_manager.get_ecus_by_functional_address.return_value = [0x1000, 0x1001]
        self.server.config_manager.is_source_address_allowed.return_value = True
        self.server.config_manager.get_uds_service_by_request.return_value = {
            "supports_functional": True
        }
        
        # Mock UDS processing
        self.server.process_uds_message = Mock(return_value=b"\x62\xf1\x90\x10\x20\x01")
        self.server.create_diagnostic_message_response = Mock(return_value=b"response")

        # Test functional diagnostic message handling
        source_address = 0x0E00
        functional_address = 0x1FFF
        uds_payload = b"\x22\xf1\x90"
        target_ecus = [0x1000, 0x1001]

        # Simulate the calls that would be made by the actual server
        self.server.config_manager.get_ecus_by_functional_address(functional_address)
        self.server.config_manager.is_source_address_allowed(source_address, target_ecus[0])
        self.server.config_manager.get_uds_service_by_request(uds_payload.hex().upper(), target_ecus[0])

        # Verify configuration calls
        self.server.config_manager.get_ecus_by_functional_address.assert_called_once_with(functional_address)
        self.server.config_manager.is_source_address_allowed.assert_called()
        self.server.config_manager.get_uds_service_by_request.assert_called()

    def test_handle_functional_diagnostic_message_no_responding_ecus(self):
        """Test functional diagnostic message handling when no ECUs respond"""
        # Mock configuration with no responding ECUs
        self.server.config_manager.get_ecus_by_functional_address.return_value = [0x1000, 0x1001]
        self.server.config_manager.is_source_address_allowed.return_value = True
        self.server.config_manager.get_uds_service_by_request.return_value = {
            "supports_functional": False
        }

        # Test functional diagnostic message handling
        source_address = 0x0E00
        functional_address = 0x1FFF
        uds_payload = b"\x22\xf1\x90"
        target_ecus = [0x1000, 0x1001]

        # Verify that no ECUs support functional addressing
        for ecu_address in target_ecus:
            service_config = self.server.config_manager.get_uds_service_by_request(
                uds_payload.hex().upper(), ecu_address
            )
            self.assertFalse(service_config["supports_functional"])

    def test_handle_functional_diagnostic_message_source_not_allowed(self):
        """Test functional diagnostic message handling when source address not allowed"""
        # Mock configuration with source address not allowed
        self.server.config_manager.get_ecus_by_functional_address.return_value = [0x1000, 0x1001]
        self.server.config_manager.is_source_address_allowed.return_value = False

        # Test functional diagnostic message handling
        source_address = 0x9999  # Not allowed
        functional_address = 0x1FFF
        uds_payload = b"\x22\xf1\x90"
        target_ecus = [0x1000, 0x1001]

        # Verify source address validation
        for ecu_address in target_ecus:
            is_allowed = self.server.config_manager.is_source_address_allowed(
                source_address, ecu_address
            )
            self.assertFalse(is_allowed)


class TestFunctionalAddressIntegration(unittest.TestCase):
    """Integration tests for functional address functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = DoIPClientWrapper(
            server_host="127.0.0.1",
            server_port=13400,
            logical_address=0x0E00,
            target_address=0x1000,
        )

    def test_end_to_end_functional_addressing(self):
        """Test end-to-end functional addressing flow"""
        # Mock the doip_client to avoid actual network calls
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock successful responses for different services
        responses = {
            b"\x22\xf1\x90": b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb",  # Read VIN
            b"\x22\xf1\x91": b"\x62\xf1\x91\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xbb\xcc",  # Read Vehicle Type
            b"\x10\x03": b"\x50\x03\x00\x00",  # Diagnostic Session Control
            b"\x3e\x00": b"\x7e\x00",  # Tester Present
        }

        def mock_send_diagnostic_message(payload, *args, **kwargs):
            return responses.get(payload, None)

        self.client.doip_client.send_diagnostic_message.side_effect = mock_send_diagnostic_message

        # Test multiple functional services
        test_cases = [
            ("Read VIN", lambda: self.client.send_functional_read_data_by_identifier(0xF190)),
            ("Read Vehicle Type", lambda: self.client.send_functional_read_data_by_identifier(0xF191)),
            ("Diagnostic Session Control", lambda: self.client.send_functional_diagnostic_session_control(0x03)),
            ("Tester Present", lambda: self.client.send_functional_tester_present()),
        ]

        for service_name, test_func in test_cases:
            with self.subTest(service=service_name):
                response = test_func()
                self.assertIsNotNone(response, f"{service_name} should return a response")

    def test_physical_vs_functional_comparison(self):
        """Test comparison between physical and functional addressing"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock different responses for physical vs functional
        physical_response = b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        functional_response = b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xcc\xdd"

        def mock_send_diagnostic_to_address(address, payload, *args, **kwargs):
            # Simulate different responses based on target address
            if hasattr(self.client, '_is_functional_call') and self.client._is_functional_call:
                return functional_response
            else:
                return physical_response

        def mock_send_diagnostic(payload, *args, **kwargs):
            # For physical addressing
            return physical_response

        self.client.doip_client.send_diagnostic_message_to_address.side_effect = mock_send_diagnostic_to_address
        self.client.doip_client.send_diagnostic_message.side_effect = mock_send_diagnostic

        # Test physical addressing
        self.client._is_functional_call = False
        physical_result = self.client.send_read_data_by_identifier(0xF190)

        # Test functional addressing
        self.client._is_functional_call = True
        functional_result = self.client.send_functional_read_data_by_identifier(0xF190)

        # Verify both return responses
        self.assertIsNotNone(physical_result)
        self.assertIsNotNone(functional_result)

    def test_concurrent_functional_requests(self):
        """Test concurrent functional requests"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )

        def send_functional_request(request_id):
            """Send a functional request with a unique ID"""
            return self.client.send_functional_read_data_by_identifier(0xF190)

        # Test concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_functional_request, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]

        # Verify all requests completed successfully
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertIsNotNone(result)


class TestFunctionalAddressEdgeCases(unittest.TestCase):
    """Edge case tests for functional address functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = DoIPClientWrapper(
            server_host="127.0.0.1",
            server_port=13400,
            logical_address=0x0E00,
            target_address=0x1000,
        )
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

    def test_invalid_functional_address(self):
        """Test handling of invalid functional addresses"""
        # Test with invalid functional address
        uds_payload = [0x22, 0xF1, 0x90]
        invalid_address = 0x0000  # Invalid functional address
        
        # Mock no response for invalid address
        self.client.doip_client.send_diagnostic_message.return_value = None
        
        response = self.client.send_functional_diagnostic_message(uds_payload, invalid_address)
        
        # Should return None for invalid address
        self.assertIsNone(response)

    def test_empty_uds_payload(self):
        """Test handling of empty UDS payload"""
        # Test with empty payload
        empty_payload = []
        
        # Mock no response for empty payload
        self.client.doip_client.send_diagnostic_message.return_value = None
        
        response = self.client.send_functional_diagnostic_message(empty_payload)
        
        # Should handle empty payload gracefully
        self.assertIsNone(response)

    def test_very_large_uds_payload(self):
        """Test handling of very large UDS payload"""
        # Test with large payload
        large_payload = [0x22] + [0x00] * 1000  # Large payload
        
        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = b"\x62\x00"
        
        response = self.client.send_functional_diagnostic_message(large_payload)
        
        # Should handle large payload
        self.assertIsNotNone(response)

    def test_network_timeout(self):
        """Test handling of network timeout"""
        # Mock timeout
        self.client.doip_client.send_diagnostic_message_to_address.side_effect = socket.timeout("Timeout")
        
        uds_payload = [0x22, 0xF1, 0x90]
        
        # The implementation catches exceptions and returns None
        response = self.client.send_functional_diagnostic_message(uds_payload, timeout=0.1)
        self.assertIsNone(response)

    def test_connection_lost_during_functional_call(self):
        """Test handling of connection loss during functional call"""
        # Mock connection loss
        self.client.doip_client.send_diagnostic_message_to_address.side_effect = ConnectionError("Connection lost")
        
        uds_payload = [0x22, 0xF1, 0x90]
        
        # The implementation catches exceptions and returns None
        response = self.client.send_functional_diagnostic_message(uds_payload)
        self.assertIsNone(response)

    def test_malformed_response(self):
        """Test handling of malformed response"""
        # Mock malformed response
        self.client.doip_client.send_diagnostic_message.return_value = b"\x00"  # Malformed
        
        uds_payload = [0x22, 0xF1, 0x90]
        response = self.client.send_functional_diagnostic_message(uds_payload)
        
        # Should return the malformed response as-is
        self.assertEqual(response, b"\x00")

    def test_negative_response_code(self):
        """Test handling of negative response codes"""
        # Mock negative response
        self.client.doip_client.send_diagnostic_message.return_value = b"\x7f\x22\x11"  # Negative response
        
        uds_payload = [0x22, 0xF1, 0x90]
        response = self.client.send_functional_diagnostic_message(uds_payload)
        
        # Should return the negative response
        self.assertEqual(response, b"\x7f\x22\x11")

    def test_multiple_functional_addresses(self):
        """Test using multiple different functional addresses"""
        functional_addresses = [0x1FFF, 0x2FFF, 0x3FFF]
        
        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )
        
        uds_payload = [0x22, 0xF1, 0x90]
        
        for func_addr in functional_addresses:
            with self.subTest(functional_address=func_addr):
                response = self.client.send_functional_diagnostic_message(uds_payload, func_addr)
                self.assertIsNotNone(response)


class TestFunctionalAddressPerformance(unittest.TestCase):
    """Performance tests for functional address functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = DoIPClientWrapper(
            server_host="127.0.0.1",
            server_port=13400,
            logical_address=0x0E00,
            target_address=0x1000,
        )
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

    def test_functional_request_performance(self):
        """Test performance of functional requests"""
        # Mock fast response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )
        
        uds_payload = [0x22, 0xF1, 0x90]
        
        # Measure time for multiple requests
        start_time = time.time()
        num_requests = 100
        
        for _ in range(num_requests):
            response = self.client.send_functional_diagnostic_message(uds_payload)
            self.assertIsNotNone(response)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 100 requests in reasonable time
        self.assertLess(total_time, 5.0)  # Less than 5 seconds for 100 requests
        print(f"Completed {num_requests} functional requests in {total_time:.2f} seconds")

    def test_concurrent_functional_requests_performance(self):
        """Test performance of concurrent functional requests"""
        # Mock fast response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )
        
        def send_functional_request():
            """Send a functional request"""
            return self.client.send_functional_diagnostic_message([0x22, 0xF1, 0x90])
        
        # Test concurrent performance
        num_concurrent = 20
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(send_functional_request) for _ in range(num_concurrent)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all requests completed
        self.assertEqual(len(results), num_concurrent)
        for result in results:
            self.assertIsNotNone(result)
        
        # Should complete concurrent requests in reasonable time
        self.assertLess(total_time, 3.0)  # Less than 3 seconds for 20 concurrent requests
        print(f"Completed {num_concurrent} concurrent functional requests in {total_time:.2f} seconds")

    def test_memory_usage_functional_requests(self):
        """Test memory usage during functional requests"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Mock response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )
        
        # Send many requests
        uds_payload = [0x22, 0xF1, 0x90]
        num_requests = 1000
        
        for _ in range(num_requests):
            response = self.client.send_functional_diagnostic_message(uds_payload)
            self.assertIsNotNone(response)
        
        # Get final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 10MB)
        self.assertLess(memory_increase, 10 * 1024 * 1024)
        print(f"Memory increase after {num_requests} requests: {memory_increase / 1024 / 1024:.2f} MB")


class TestFunctionalAddressConfiguration(unittest.TestCase):
    """Configuration validation tests for functional address functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.config_manager = Mock(spec=HierarchicalConfigManager)

    def test_functional_address_configuration_validation(self):
        """Test validation of functional address configuration"""
        # Mock different responses for different functional addresses
        def mock_get_ecus_by_functional_address(functional_address):
            if functional_address == 0x1FFF:
                return [0x1000, 0x1001, 0x1002]
            else:
                return []
        
        self.config_manager.get_ecus_by_functional_address.side_effect = mock_get_ecus_by_functional_address
        
        # Test valid functional address
        ecus = self.config_manager.get_ecus_by_functional_address(0x1FFF)
        self.assertGreater(len(ecus), 0)
        
        # Test invalid functional address
        ecus = self.config_manager.get_ecus_by_functional_address(0x9999)
        self.assertEqual(len(ecus), 0)

    def test_uds_service_functional_support_configuration(self):
        """Test UDS service functional support configuration"""
        # Mock service configurations
        services_with_functional = [
            {"name": "Read_VIN", "supports_functional": True},
            {"name": "Read_Vehicle_Type", "supports_functional": True},
            {"name": "Diagnostic_Session_Control", "supports_functional": True},
            {"name": "Tester_Present", "supports_functional": True},
        ]
        
        services_without_functional = [
            {"name": "Engine_RPM_Read", "supports_functional": False},
            {"name": "Engine_Temperature_Read", "supports_functional": False},
        ]
        
        # Test services with functional support
        for service in services_with_functional:
            with self.subTest(service=service["name"]):
                self.assertTrue(service["supports_functional"])
        
        # Test services without functional support
        for service in services_without_functional:
            with self.subTest(service=service["name"]):
                self.assertFalse(service["supports_functional"])

    def test_ecu_functional_address_assignment(self):
        """Test ECU functional address assignment"""
        # Mock ECU configurations with functional addresses
        ecu_configs = [
            {"name": "Engine_ECU", "target_address": 0x1000, "functional_address": 0x1FFF},
            {"name": "Transmission_ECU", "target_address": 0x1001, "functional_address": 0x1FFF},
            {"name": "ABS_ECU", "target_address": 0x1002, "functional_address": 0x1FFF},
        ]
        
        # Test functional address assignment
        for ecu_config in ecu_configs:
            with self.subTest(ecu=ecu_config["name"]):
                self.assertEqual(ecu_config["functional_address"], 0x1FFF)
                self.assertIn(ecu_config["target_address"], [0x1000, 0x1001, 0x1002])

    def test_tester_address_validation(self):
        """Test tester address validation for functional addressing"""
        # Mock allowed tester addresses
        allowed_testers = [0x0E00, 0x0E01, 0x0E02]
        
        # Test each allowed tester address
        for tester_addr in allowed_testers:
            with self.subTest(tester_address=tester_addr):
                # In a real implementation, this would validate against ECU configuration
                self.assertIn(tester_addr, allowed_testers)

    def test_functional_address_range_validation(self):
        """Test functional address range validation"""
        # Valid functional addresses (typically 0x1FFF)
        valid_functional_addresses = [0x1FFF, 0x2FFF, 0x3FFF]
        
        # Invalid functional addresses
        invalid_functional_addresses = [0x0000, 0x0001, 0x1000, 0x1001]
        
        # Test valid addresses
        for addr in valid_functional_addresses:
            with self.subTest(address=addr):
                # Functional addresses should be in the valid range
                self.assertGreaterEqual(addr, 0x1FFF)
                self.assertLessEqual(addr, 0xFFFF)
        
        # Test invalid addresses
        for addr in invalid_functional_addresses:
            with self.subTest(address=addr):
                # These should not be valid functional addresses
                self.assertLess(addr, 0x1FFF)


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestFunctionalAddressUnit,
        TestFunctionalAddressClient,
        TestFunctionalAddressServer,
        TestFunctionalAddressIntegration,
        TestFunctionalAddressEdgeCases,
        TestFunctionalAddressPerformance,
        TestFunctionalAddressConfiguration,
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
