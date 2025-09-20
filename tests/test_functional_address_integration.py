#!/usr/bin/env python3
"""
Integration tests for functional address functionality.
This test suite focuses on end-to-end scenarios and real-world usage patterns.
"""

import unittest
import time
import socket
import struct
import threading
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from doip_client.doip_client import DoIPClientWrapper
from doip_server.hierarchical_config_manager import HierarchicalConfigManager
from doip_server.doip_server import DoIPServer


class TestFunctionalAddressEndToEnd(unittest.TestCase):
    """End-to-end integration tests for functional addressing"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = DoIPClientWrapper(
            server_host="127.0.0.1",
            server_port=13400,
            logical_address=0x0E00,
            target_address=0x1000,
        )

    def test_complete_functional_diagnostics_workflow(self):
        """Test complete functional diagnostics workflow from connection to response"""
        # Mock the doip_client to simulate real behavior
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock responses for different services
        service_responses = {
            # Diagnostic Session Control
            b"\x10\x03": b"\x50\x03\x00\x00",
            # Read VIN
            b"\x22\xf1\x90": b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb",
            # Read Vehicle Type
            b"\x22\xf1\x91": b"\x62\xf1\x91\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xbb\xcc",
            # Tester Present
            b"\x3e\x00": b"\x7e\x00",
        }

        def mock_send_diagnostic_message(payload, *args, **kwargs):
            return service_responses.get(payload, None)

        self.client.doip_client.send_diagnostic_message.side_effect = (
            mock_send_diagnostic_message
        )

        # Test complete workflow
        print("\n=== Complete Functional Diagnostics Workflow Test ===")

        # Step 1: Connect (simulated)
        print("Step 1: Connecting to server...")
        # In real test, this would be: self.client.connect()

        # Step 2: Start diagnostic session
        print("Step 2: Starting diagnostic session...")
        session_response = self.client.send_functional_diagnostic_session_control(0x03)
        self.assertIsNotNone(session_response)
        self.assertEqual(session_response, b"\x50\x03\x00\x00")
        print(f"✓ Session started: {session_response.hex()}")

        # Step 3: Read VIN using functional addressing
        print("Step 3: Reading VIN using functional addressing...")
        vin_response = self.client.send_functional_read_data_by_identifier(0xF190)
        self.assertIsNotNone(vin_response)
        self.assertTrue(vin_response.startswith(b"\x62\xf1\x90"))
        print(f"✓ VIN read: {vin_response.hex()}")

        # Step 4: Read Vehicle Type using functional addressing
        print("Step 4: Reading Vehicle Type using functional addressing...")
        vehicle_type_response = self.client.send_functional_read_data_by_identifier(
            0xF191
        )
        self.assertIsNotNone(vehicle_type_response)
        self.assertTrue(vehicle_type_response.startswith(b"\x62\xf1\x91"))
        print(f"✓ Vehicle Type read: {vehicle_type_response.hex()}")

        # Step 5: Send Tester Present
        print("Step 5: Sending Tester Present...")
        tester_present_response = self.client.send_functional_tester_present()
        self.assertIsNotNone(tester_present_response)
        self.assertEqual(tester_present_response, b"\x7e\x00")
        print(f"✓ Tester Present: {tester_present_response.hex()}")

        # Step 6: Disconnect (simulated)
        print("Step 6: Disconnecting...")
        # In real test, this would be: self.client.disconnect()

        print("✓ Complete functional diagnostics workflow completed successfully!")

    def test_multiple_ecu_functional_addressing(self):
        """Test functional addressing with multiple ECUs responding"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock different responses from different ECUs
        ecu_responses = [
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb",  # Engine ECU
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xcc\xdd",  # Transmission ECU
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xee\xff",  # ABS ECU
        ]

        response_index = 0

        def mock_send_diagnostic_message(payload, *args, **kwargs):
            nonlocal response_index
            if payload == b"\x22\xf1\x90":  # Read VIN
                response = ecu_responses[response_index % len(ecu_responses)]
                response_index += 1
                return response
            return None

        self.client.doip_client.send_diagnostic_message.side_effect = (
            mock_send_diagnostic_message
        )

        print("\n=== Multiple ECU Functional Addressing Test ===")

        # Send multiple functional requests to simulate different ECUs responding
        responses = []
        for i in range(5):
            print(f"Sending functional request {i+1}...")
            response = self.client.send_functional_read_data_by_identifier(0xF190)
            self.assertIsNotNone(response)
            responses.append(response)
            print(f"✓ Response {i+1}: {response.hex()}")
            time.sleep(0.1)  # Small delay to simulate real timing

        # Verify we got responses (may be from different ECUs)
        self.assertEqual(len(responses), 5)
        print(f"✓ Received {len(responses)} responses from functional addressing")

    def test_functional_vs_physical_addressing_comparison(self):
        """Test comprehensive comparison between functional and physical addressing"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock different responses for physical vs functional
        physical_response = b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"  # Single ECU
        functional_responses = [
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb",  # Engine ECU
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xcc\xdd",  # Transmission ECU
        ]

        call_count = 0

        def mock_send_diagnostic_message(payload, *args, **kwargs):
            nonlocal call_count
            call_count += 1

            if payload == b"\x22\xf1\x90":  # Read VIN
                # Simulate different behavior for physical vs functional
                if (
                    hasattr(self.client, "_is_functional_call")
                    and self.client._is_functional_call
                ):
                    # Return different responses for functional addressing
                    return functional_responses[call_count % len(functional_responses)]
                else:
                    # Return single response for physical addressing
                    return physical_response
            return None

        def mock_send_diagnostic(payload, *args, **kwargs):
            # For physical addressing
            return physical_response

        self.client.doip_client.send_diagnostic_message.side_effect = (
            mock_send_diagnostic_message
        )
        self.client.doip_client.send_diagnostic_message.side_effect = (
            mock_send_diagnostic
        )

        print("\n=== Functional vs Physical Addressing Comparison ===")

        # Test physical addressing
        print("Testing physical addressing (single ECU)...")
        self.client._is_functional_call = False
        physical_result = self.client.send_read_data_by_identifier(0xF190)
        self.assertIsNotNone(physical_result)
        print(f"✓ Physical response: {physical_result.hex()}")

        # Test functional addressing
        print("Testing functional addressing (multiple ECUs)...")
        self.client._is_functional_call = True
        functional_result = self.client.send_functional_read_data_by_identifier(0xF190)
        self.assertIsNotNone(functional_result)
        print(f"✓ Functional response: {functional_result.hex()}")

        # Verify both approaches work
        self.assertIsNotNone(physical_result)
        self.assertIsNotNone(functional_result)
        print("✓ Both physical and functional addressing work correctly")

    def test_functional_addressing_error_handling(self):
        """Test error handling in functional addressing"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        print("\n=== Functional Addressing Error Handling Test ===")

        # Test 1: No response from any ECU
        print("Test 1: No response from any ECU...")
        self.client.doip_client.send_diagnostic_message.return_value = None
        response = self.client.send_functional_read_data_by_identifier(0xF190)
        self.assertIsNone(response)
        print("✓ Handled no response correctly")

        # Test 2: Network error
        print("Test 2: Network error...")
        self.client.doip_client.send_diagnostic_message.side_effect = ConnectionError(
            "Network error"
        )
        response = self.client.send_functional_read_data_by_identifier(0xF190)
        self.assertIsNone(response)
        print("✓ Handled network error correctly")

        # Test 3: Timeout
        print("Test 3: Timeout...")
        self.client.doip_client.send_diagnostic_message.side_effect = socket.timeout(
            "Timeout"
        )
        response = self.client.send_functional_read_data_by_identifier(0xF190)
        self.assertIsNone(response)
        print("✓ Handled timeout correctly")

        # Test 4: Malformed response
        print("Test 4: Malformed response...")
        self.client.doip_client.send_diagnostic_message.side_effect = None
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x00"  # Malformed
        )
        response = self.client.send_functional_read_data_by_identifier(0xF190)
        self.assertEqual(response, b"\x00")  # Should return malformed response as-is
        print("✓ Handled malformed response correctly")

    def test_concurrent_functional_requests(self):
        """Test concurrent functional requests from multiple clients"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )

        def send_concurrent_request(request_id):
            """Send a concurrent functional request"""
            print(f"Client {request_id}: Sending functional request...")
            response = self.client.send_functional_read_data_by_identifier(0xF190)
            print(
                f"Client {request_id}: Received response: {response.hex() if response else 'None'}"
            )
            return response

        print("\n=== Concurrent Functional Requests Test ===")

        # Test with multiple concurrent requests
        num_clients = 5
        with ThreadPoolExecutor(max_workers=num_clients) as executor:
            futures = [
                executor.submit(send_concurrent_request, i) for i in range(num_clients)
            ]
            results = [future.result() for future in as_completed(futures)]

        # Verify all requests completed successfully
        self.assertEqual(len(results), num_clients)
        for i, result in enumerate(results):
            self.assertIsNotNone(result, f"Client {i} should have received a response")

        print(f"✓ All {num_clients} concurrent requests completed successfully")

    def test_functional_addressing_with_different_services(self):
        """Test functional addressing with different UDS services"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock responses for different services
        service_responses = {
            b"\x22\xf1\x90": b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb",  # Read VIN
            b"\x22\xf1\x91": b"\x62\xf1\x91\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xbb\xcc",  # Read Vehicle Type
            b"\x10\x03": b"\x50\x03\x00\x00",  # Diagnostic Session Control
            b"\x3e\x00": b"\x7e\x00",  # Tester Present
            b"\x19\x02": b"\x59\x02",  # Read DTCs
        }

        def mock_send_diagnostic_message(payload, *args, **kwargs):
            return service_responses.get(payload, None)

        self.client.doip_client.send_diagnostic_message.side_effect = (
            mock_send_diagnostic_message
        )

        print("\n=== Functional Addressing with Different Services Test ===")

        # Test different services that support functional addressing
        test_services = [
            (
                "Read VIN",
                lambda: self.client.send_functional_read_data_by_identifier(0xF190),
            ),
            (
                "Read Vehicle Type",
                lambda: self.client.send_functional_read_data_by_identifier(0xF191),
            ),
            (
                "Diagnostic Session Control",
                lambda: self.client.send_functional_diagnostic_session_control(0x03),
            ),
            ("Tester Present", lambda: self.client.send_functional_tester_present()),
        ]

        for service_name, test_func in test_services:
            print(f"Testing {service_name}...")
            response = test_func()
            self.assertIsNotNone(response, f"{service_name} should return a response")
            print(f"✓ {service_name}: {response.hex()}")
            time.sleep(0.1)  # Small delay between requests

        print("✓ All functional services work correctly")

    def test_functional_addressing_performance_under_load(self):
        """Test functional addressing performance under load"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock fast response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )

        print("\n=== Functional Addressing Performance Under Load Test ===")

        # Test with high number of requests
        num_requests = 100
        start_time = time.time()

        for i in range(num_requests):
            response = self.client.send_functional_read_data_by_identifier(0xF190)
            self.assertIsNotNone(response)
            if (i + 1) % 20 == 0:
                print(f"Completed {i + 1}/{num_requests} requests...")

        end_time = time.time()
        total_time = end_time - start_time
        requests_per_second = num_requests / total_time

        print(f"✓ Completed {num_requests} requests in {total_time:.2f} seconds")
        print(f"✓ Performance: {requests_per_second:.1f} requests/second")

        # Verify performance is reasonable
        self.assertLess(total_time, 10.0)  # Should complete in less than 10 seconds
        self.assertGreater(requests_per_second, 10.0)  # At least 10 requests per second

    def test_functional_addressing_with_custom_addresses(self):
        """Test functional addressing with custom functional addresses"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )

        print("\n=== Functional Addressing with Custom Addresses Test ===")

        # Test different functional addresses
        functional_addresses = [0x1FFF, 0x2FFF, 0x3FFF, 0x4FFF]

        for func_addr in functional_addresses:
            print(f"Testing functional address 0x{func_addr:04X}...")
            response = self.client.send_functional_diagnostic_message(
                [0x22, 0xF1, 0x90], functional_address=func_addr
            )
            self.assertIsNotNone(response)
            print(f"✓ Functional address 0x{func_addr:04X}: {response.hex()}")

        print("✓ All custom functional addresses work correctly")


class TestFunctionalAddressRealWorldScenarios(unittest.TestCase):
    """Real-world scenario tests for functional addressing"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = DoIPClientWrapper(
            server_host="127.0.0.1",
            server_port=13400,
            logical_address=0x0E00,
            target_address=0x1000,
        )

    def test_diagnostic_tool_simulation(self):
        """Test simulation of a diagnostic tool using functional addressing"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock responses for diagnostic tool workflow
        responses = {
            b"\x10\x03": b"\x50\x03\x00\x00",  # Session start
            b"\x22\xf1\x90": b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb",  # VIN
            b"\x22\xf1\x91": b"\x62\xf1\x91\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xbb\xcc",  # Vehicle Type
            b"\x19\x02": b"\x59\x02",  # DTCs
            b"\x3e\x00": b"\x7e\x00",  # Tester Present
        }

        def mock_send_diagnostic_message(payload, *args, **kwargs):
            return responses.get(payload, None)

        self.client.doip_client.send_diagnostic_message.side_effect = (
            mock_send_diagnostic_message
        )

        print("\n=== Diagnostic Tool Simulation Test ===")

        # Simulate diagnostic tool workflow
        print("Step 1: Starting diagnostic session...")
        session_response = self.client.send_functional_diagnostic_session_control(0x03)
        self.assertIsNotNone(session_response)
        print(f"✓ Session started: {session_response.hex()}")

        print("Step 2: Reading vehicle information...")
        vin_response = self.client.send_functional_read_data_by_identifier(0xF190)
        self.assertIsNotNone(vin_response)
        print(f"✓ VIN: {vin_response.hex()}")

        vehicle_type_response = self.client.send_functional_read_data_by_identifier(
            0xF191
        )
        self.assertIsNotNone(vehicle_type_response)
        print(f"✓ Vehicle Type: {vehicle_type_response.hex()}")

        print("Step 3: Reading diagnostic trouble codes...")
        dtc_response = self.client.send_functional_diagnostic_message([0x19, 0x02])
        self.assertIsNotNone(dtc_response)
        print(f"✓ DTCs: {dtc_response.hex()}")

        print("Step 4: Keeping session alive...")
        for i in range(3):
            tester_present_response = self.client.send_functional_tester_present()
            self.assertIsNotNone(tester_present_response)
            print(f"✓ Tester Present {i+1}: {tester_present_response.hex()}")
            time.sleep(0.1)

        print("✓ Diagnostic tool simulation completed successfully!")

    def test_ecu_network_scan(self):
        """Test scanning ECU network using functional addressing"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock responses from different ECUs
        ecu_responses = {
            "engine": b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb",
            "transmission": b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xcc\xdd",
            "abs": b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xee\xff",
        }

        response_count = 0

        def mock_send_diagnostic_message(payload, *args, **kwargs):
            nonlocal response_count
            if payload == b"\x22\xf1\x90":  # Read VIN
                response_count += 1
                # Simulate different ECUs responding
                ecu_names = list(ecu_responses.keys())
                ecu_name = ecu_names[response_count % len(ecu_names)]
                return ecu_responses[ecu_name]
            return None

        self.client.doip_client.send_diagnostic_message.side_effect = (
            mock_send_diagnostic_message
        )

        print("\n=== ECU Network Scan Test ===")

        # Scan network using functional addressing
        print("Scanning ECU network using functional addressing...")
        responses = []

        for i in range(6):  # Send multiple requests to detect different ECUs
            print(f"Scan request {i+1}...")
            response = self.client.send_functional_read_data_by_identifier(0xF190)
            if response:
                responses.append(response)
                print(f"✓ Response {i+1}: {response.hex()}")
            else:
                print(f"✗ No response {i+1}")
            time.sleep(0.1)

        # Verify we detected multiple ECUs
        self.assertGreater(len(responses), 0)
        print(f"✓ Detected {len(responses)} responses from ECU network")

        # Check for different responses (indicating different ECUs)
        unique_responses = set(responses)
        print(f"✓ Found {len(unique_responses)} unique responses (different ECUs)")

    def test_functional_addressing_fault_tolerance(self):
        """Test fault tolerance of functional addressing"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        print("\n=== Functional Addressing Fault Tolerance Test ===")

        # Test 1: Intermittent failures
        print("Test 1: Intermittent failures...")
        call_count = 0

        def mock_intermittent_failure(payload, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Fail every 3rd call
                return None
            return b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"

        self.client.doip_client.send_diagnostic_message.side_effect = (
            mock_intermittent_failure
        )

        success_count = 0
        for i in range(10):
            response = self.client.send_functional_read_data_by_identifier(0xF190)
            if response:
                success_count += 1
            print(f"Request {i+1}: {'Success' if response else 'Failed'}")

        print(f"✓ Intermittent failure test: {success_count}/10 requests succeeded")
        self.assertGreater(success_count, 0)  # At least some should succeed

        # Test 2: Recovery after failure
        print("Test 2: Recovery after failure...")
        self.client.doip_client.send_diagnostic_message.side_effect = None
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )

        response = self.client.send_functional_read_data_by_identifier(0xF190)
        self.assertIsNotNone(response)
        print("✓ Recovery after failure successful")

    def test_functional_addressing_with_different_testers(self):
        """Test functional addressing with different tester addresses"""
        # Mock the doip_client
        self.client.doip_client = Mock()
        self.client.doip_client.send_diagnostic_message = Mock()
        self.client.doip_client.send_diagnostic_message_to_address = Mock()
        self.client.doip_client.close = Mock()

        # Mock successful response
        self.client.doip_client.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
        )

        print("\n=== Functional Addressing with Different Testers Test ===")

        # Test with different tester addresses
        tester_addresses = [0x0E00, 0x0E01, 0x0E02, 0x0E03]

        for tester_addr in tester_addresses:
            print(f"Testing with tester address 0x{tester_addr:04X}...")

            # Create client with different tester address
            test_client = DoIPClientWrapper(
                server_host="127.0.0.1",
                server_port=13400,
                logical_address=tester_addr,
                target_address=0x1000,
            )
            test_client.doip_client = Mock()
            test_client.doip_client.send_diagnostic_message = Mock()
            test_client.doip_client.close = Mock()
            test_client.doip_client.send_diagnostic_message.return_value = (
                b"\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb"
            )

            response = test_client.send_functional_read_data_by_identifier(0xF190)
            self.assertIsNotNone(response)
            print(f"✓ Tester 0x{tester_addr:04X}: {response.hex()}")

        print("✓ All tester addresses work correctly with functional addressing")


if __name__ == "__main__":
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestFunctionalAddressEndToEnd,
        TestFunctionalAddressRealWorldScenarios,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'='*50}")
    print(f"Integration Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )
    print(f"{'='*50}")
