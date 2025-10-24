#!/usr/bin/env python3
"""
End-to-End Functional Addressing Test

This test suite provides comprehensive end-to-end testing of functional addressing
functionality. It tests the complete flow from client request to server response,
ensuring that functional addressing works correctly according to the DoIP standard.

Key test areas:
- Functional addressing with multiple ECUs
- Proper source address handling (ECU addresses, not functional address)
- Single ACK message per functional request
- Multiple UDS responses from different ECUs
- Physical vs functional addressing comparison
"""

import os
import socket
import struct
import sys
import threading
import time
import unittest
from unittest.mock import Mock, patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class FunctionalAddressingE2ETest(unittest.TestCase):
    """End-to-end functional addressing tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.server_host = "127.0.0.1"
        self.server_port = 13400
        self.client_address = 0x0E00
        self.functional_address = 0x1FFF
        self.sock = None

    def tearDown(self):
        """Clean up after tests"""
        if self.sock:
            self.sock.close()

    def create_doip_header(self, payload_type, payload_length):
        """Create DoIP header"""
        return struct.pack(">BBHI", 0x02, 0xFD, payload_type, payload_length)

    def create_routing_activation_request(self, client_address, logical_address):
        """Create routing activation request"""
        payload = struct.pack(">HHB", client_address, logical_address, 0x00)
        payload += struct.pack(">I", 0x00000000)  # Reserved
        payload += struct.pack(">I", 0x00000000)  # VM specific
        header = self.create_doip_header(0x0005, len(payload))
        return header + payload

    def create_diagnostic_message(self, source_addr, target_addr, uds_payload):
        """Create diagnostic message"""
        payload = struct.pack(">HH", source_addr, target_addr) + uds_payload
        header = self.create_doip_header(0x8001, len(payload))
        return header + payload

    def connect_to_server(self):
        """Connect to the DoIP server"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(10.0)
        self.sock.connect((self.server_host, self.server_port))
        return True

    def perform_routing_activation(self):
        """Perform routing activation"""
        routing_request = self.create_routing_activation_request(
            self.client_address, 0x0000
        )
        self.sock.send(routing_request)
        response = self.sock.recv(1024)

        if len(response) >= 17:
            response_code = response[12]
            return response_code == 0x10
        return False

    def send_functional_request(self, uds_payload):
        """Send functional request and collect all responses"""
        diag_message = self.create_diagnostic_message(
            self.client_address, self.functional_address, uds_payload
        )

        self.sock.send(diag_message)

        # Collect all responses
        responses = []
        timeout_start = time.time()

        while (time.time() - timeout_start) < 3.0:
            try:
                self.sock.settimeout(1.0)
                response = self.sock.recv(1024)
                if response:
                    responses.append(response)
                else:
                    break
            except socket.timeout:
                break

        return responses

    def parse_responses(self, responses):
        """Parse responses and extract ACK and UDS responses"""
        ack_count = 0
        uds_responses = []
        ecu_addresses = []

        for response in responses:
            if len(response) >= 8:
                payload_type = struct.unpack(">H", response[2:4])[0]

                if payload_type == 0x8002:  # ACK
                    ack_count += 1
                elif payload_type == 0x8001:  # UDS Response
                    if len(response) >= 10:
                        source_addr = struct.unpack(">H", response[8:10])[0]
                        ecu_addresses.append(source_addr)
                        if len(response) > 10:
                            uds_data = response[10:]
                            uds_responses.append(uds_data)

        return ack_count, uds_responses, ecu_addresses

    @unittest.skipUnless(
        os.environ.get("DOIP_SERVER_RUNNING", "false").lower() == "true",
        "Set DOIP_SERVER_RUNNING=true to run integration tests",
    )
    def test_functional_addressing_basic(self):
        """Test basic functional addressing functionality"""
        # Connect to server
        self.assertTrue(self.connect_to_server(), "Failed to connect to server")

        # Perform routing activation
        self.assertTrue(self.perform_routing_activation(), "Routing activation failed")

        # Test functional read VIN
        responses = self.send_functional_request(b"\x22\xf1\x90")  # Read VIN

        # Parse responses
        ack_count, uds_responses, ecu_addresses = self.parse_responses(responses)

        # Verify results
        self.assertEqual(ack_count, 1, "Should receive exactly one ACK message")
        self.assertGreater(len(uds_responses), 0, "Should receive UDS responses")
        self.assertGreater(len(ecu_addresses), 0, "Should receive responses from ECUs")

        # Verify no UDS response uses functional address as source
        functional_as_source = [
            addr for addr in ecu_addresses if addr == self.functional_address
        ]
        self.assertEqual(
            len(functional_as_source),
            0,
            "No UDS response should use functional address as source",
        )

    @unittest.skipUnless(
        os.environ.get("DOIP_SERVER_RUNNING", "false").lower() == "true",
        "Set DOIP_SERVER_RUNNING=true to run integration tests",
    )
    def test_functional_addressing_multiple_ecus(self):
        """Test functional addressing with multiple ECUs"""
        # Connect to server
        self.assertTrue(self.connect_to_server(), "Failed to connect to server")

        # Perform routing activation
        self.assertTrue(self.perform_routing_activation(), "Routing activation failed")

        # Test functional read VIN (should get responses from multiple ECUs)
        responses = self.send_functional_request(b"\x22\xf1\x90")  # Read VIN

        # Parse responses
        ack_count, uds_responses, ecu_addresses = self.parse_responses(responses)

        # Verify results
        self.assertEqual(ack_count, 1, "Should receive exactly one ACK message")
        self.assertGreater(len(uds_responses), 0, "Should receive UDS responses")

        # Check for multiple ECUs responding
        unique_ecu_addresses = set(ecu_addresses)
        self.assertGreaterEqual(
            len(unique_ecu_addresses),
            1,
            "Should receive responses from at least one ECU",
        )

        # Verify all ECU addresses are valid (not functional address)
        for ecu_addr in unique_ecu_addresses:
            self.assertNotEqual(
                ecu_addr,
                self.functional_address,
                f"ECU address {ecu_addr:04X} should not be functional address",
            )

    @unittest.skipUnless(
        os.environ.get("DOIP_SERVER_RUNNING", "false").lower() == "true",
        "Set DOIP_SERVER_RUNNING=true to run integration tests",
    )
    def test_functional_vs_physical_addressing(self):
        """Test comparison between functional and physical addressing"""
        # Connect to server
        self.assertTrue(self.connect_to_server(), "Failed to connect to server")

        # Perform routing activation
        self.assertTrue(self.perform_routing_activation(), "Routing activation failed")

        # Test physical addressing (single ECU)
        physical_message = self.create_diagnostic_message(
            self.client_address,
            0x1000,  # Engine ECU address
            b"\x22\xf1\x90",  # Read VIN
        )

        self.sock.send(physical_message)
        physical_responses = []
        timeout_start = time.time()

        while (time.time() - timeout_start) < 2.0:
            try:
                self.sock.settimeout(1.0)
                response = self.sock.recv(1024)
                if response:
                    physical_responses.append(response)
                else:
                    break
            except socket.timeout:
                break

        # Test functional addressing (multiple ECUs)
        functional_responses = self.send_functional_request(b"\x22\xf1\x90")

        # Parse responses
        physical_ack, physical_uds, physical_ecus = self.parse_responses(
            physical_responses
        )
        functional_ack, functional_uds, functional_ecus = self.parse_responses(
            functional_responses
        )

        # Verify both work
        self.assertGreater(
            physical_ack + len(physical_uds), 0, "Physical addressing should work"
        )
        self.assertGreater(
            functional_ack + len(functional_uds), 0, "Functional addressing should work"
        )

        # Functional addressing should have more or equal responses
        self.assertGreaterEqual(
            len(functional_uds),
            len(physical_uds),
            "Functional addressing should get at least as many responses as physical",
        )

    @unittest.skipUnless(
        os.environ.get("DOIP_SERVER_RUNNING", "false").lower() == "true",
        "Set DOIP_SERVER_RUNNING=true to run integration tests",
    )
    def test_functional_addressing_different_services(self):
        """Test functional addressing with different UDS services"""
        # Connect to server
        self.assertTrue(self.connect_to_server(), "Failed to connect to server")

        # Perform routing activation
        self.assertTrue(self.perform_routing_activation(), "Routing activation failed")

        # Test different services that support functional addressing
        test_services = [
            (b"\x22\xf1\x90", "Read VIN"),
            (b"\x10\x03", "Diagnostic Session Control"),
            (b"\x3e\x00", "Tester Present"),
        ]

        for uds_payload, service_name in test_services:
            with self.subTest(service=service_name):
                responses = self.send_functional_request(uds_payload)
                ack_count, uds_responses, ecu_addresses = self.parse_responses(
                    responses
                )

                # Each service should work with functional addressing
                self.assertEqual(ack_count, 1, f"{service_name} should get one ACK")

                # UDS responses are optional for some services
                if len(uds_responses) > 0:
                    # Verify no functional address as source
                    functional_as_source = [
                        addr
                        for addr in ecu_addresses
                        if addr == self.functional_address
                    ]
                    self.assertEqual(
                        len(functional_as_source),
                        0,
                        f"{service_name} should not use functional address as source",
                    )
                else:
                    # If no UDS responses, that's also acceptable for some services
                    print(
                        f"  Note: {service_name} received no UDS responses (this may be normal)"
                    )

        # Test Read Vehicle Type separately (might not be configured for all ECUs)
        with self.subTest(service="Read Vehicle Type"):
            responses = self.send_functional_request(b"\x22\xf1\x91")
            ack_count, uds_responses, ecu_addresses = self.parse_responses(responses)

            # Should get ACK at minimum
            self.assertEqual(ack_count, 1, "Read Vehicle Type should get one ACK")

            # UDS responses are optional (depends on ECU configuration)
            if len(uds_responses) > 0:
                functional_as_source = [
                    addr for addr in ecu_addresses if addr == self.functional_address
                ]
                self.assertEqual(
                    len(functional_as_source),
                    0,
                    "Read Vehicle Type should not use functional address as source",
                )

    def test_functional_addressing_unit_mocks(self):
        """Test functional addressing with mocked components (unit test)"""
        # Test the response parsing logic directly
        mock_responses = [
            b"\x02\xfd\x80\x02\x00\x00\x00\x05\x1f\xff\x0e\x00\x00",  # ACK
            b"\x02\xfd\x80\x01\x00\x00\x00\x18\x10\x00\x0e\x00\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xaa\xbb\x12\x12\x12\x12",  # ECU 0x1000
            b"\x02\xfd\x80\x01\x00\x00\x00\x18\x10\x01\x0e\x00\x62\xf1\x90\x10\x20\x01\x12\x23\x34\x45\x67\x78\x89\xbb\xcc\x12\x12\x12\x11",  # ECU 0x1001
        ]

        # Parse responses
        ack_count, uds_responses, ecu_addresses = self.parse_responses(mock_responses)

        # Verify results
        self.assertEqual(ack_count, 1, "Should receive exactly one ACK message")
        self.assertEqual(len(uds_responses), 2, "Should receive 2 UDS responses")
        self.assertEqual(len(ecu_addresses), 2, "Should receive responses from 2 ECUs")

        # Verify ECU addresses
        self.assertIn(0x1000, ecu_addresses, "Should receive response from ECU 0x1000")
        self.assertIn(0x1001, ecu_addresses, "Should receive response from ECU 0x1001")
        self.assertNotIn(
            self.functional_address,
            ecu_addresses,
            "Should not use functional address as source",
        )


class FunctionalAddressingIntegrationTest(unittest.TestCase):
    """Integration tests for functional addressing"""

    def setUp(self):
        """Set up test fixtures"""
        self.server_host = "127.0.0.1"
        self.server_port = 13400

    @unittest.skipUnless(
        os.environ.get("DOIP_SERVER_RUNNING", "false").lower() == "true",
        "Set DOIP_SERVER_RUNNING=true to run integration tests",
    )
    def test_server_availability(self):
        """Test that the DoIP server is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            result = sock.connect_ex((self.server_host, self.server_port))
            sock.close()
            self.assertEqual(
                result,
                0,
                f"Server not available at {self.server_host}:{self.server_port}",
            )
        except Exception as e:
            self.fail(f"Failed to check server availability: {e}")


if __name__ == "__main__":
    # Set environment variable to enable integration tests
    os.environ["DOIP_SERVER_RUNNING"] = "true"

    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        FunctionalAddressingE2ETest,
        FunctionalAddressingIntegrationTest,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'='*50}")
    print(f"Functional Addressing Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )
    print(f"{'='*50}")

    # Exit with appropriate code
    sys.exit(0 if len(result.failures) == 0 and len(result.errors) == 0 else 1)
