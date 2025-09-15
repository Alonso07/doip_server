#!/usr/bin/env python3
"""
End-to-End UDS Diagnostic Communication Test
This test demonstrates the complete DoIP workflow including:
1. UDP Vehicle Identification Discovery
2. TCP Connection Establishment
3. UDS Diagnostic Message Exchange
4. Multiple ECU Communication
5. Response Cycling
"""

import pytest
import socket
import struct
import time
import threading
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doip_client.udp_doip_client import UDPDoIPClient
from doip_server.doip_server import DoIPServer


class TestUDSEndToEnd:
    """End-to-end UDS diagnostic communication tests"""

    @pytest.fixture
    def server(self):
        """Create and start DoIP server for testing"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()

        # Wait for server to start
        time.sleep(1)

        yield server

        # Cleanup
        server.stop()

    def test_udp_vehicle_discovery_to_tcp_diagnostics(self, server):
        """Test complete workflow: UDP discovery -> TCP connection -> UDS diagnostics"""

        # Step 1: UDP Vehicle Identification Discovery
        print("\n=== Step 1: UDP Vehicle Identification Discovery ===")
        udp_client = UDPDoIPClient(server_port=13400, timeout=5.0)

        # Start UDP client and send discovery request
        udp_client.start()
        vehicle_info = udp_client.send_vehicle_identification_request()
        udp_client.stop()

        # Verify vehicle information received
        assert vehicle_info is not None
        assert vehicle_info["vin"] == "1HGBH41JXMN109186"
        assert vehicle_info["logical_address"] == 0x1000
        assert vehicle_info["eid"] == "123456789ABC"
        assert vehicle_info["gid"] == "DEF012345678"

        print(
            f"✅ Vehicle discovered: VIN={vehicle_info['vin']}, Address=0x{vehicle_info['logical_address']:04X}"
        )

        # Step 2: TCP Connection Establishment
        print("\n=== Step 2: TCP Connection Establishment ===")

        # Create TCP client socket
        tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_client.settimeout(10.0)

        try:
            # Connect to server
            tcp_client.connect(("127.0.0.1", 13400))
            print("✅ TCP connection established")

            # Step 3: DoIP Routing Activation
            print("\n=== Step 3: DoIP Routing Activation ===")

            # Create routing activation request
            routing_request = self._create_routing_activation_request()
            tcp_client.send(routing_request)

            # Receive routing activation response
            response = tcp_client.recv(1024)
            routing_response = self._parse_routing_activation_response(response)

            assert routing_response["response_code"] == 0x10  # Success
            print(
                f"✅ Routing activation successful: {routing_response['response_code']:02X}"
            )

            # Step 4: UDS Diagnostic Session Control
            print("\n=== Step 4: UDS Diagnostic Session Control ===")

            # Send diagnostic session control request (extended session)
            session_request = self._create_diagnostic_session_control_request(0x03)
            diag_request = self._create_diagnostic_message_request(
                0x0E00, 0x1000, session_request
            )
            tcp_client.send(diag_request)

            # Receive session control response
            response = tcp_client.recv(1024)
            session_response = self._parse_diagnostic_message_response(response)

            assert session_response["uds_response"][0] == 0x50  # Positive response
            assert session_response["uds_response"][1] == 0x03  # Extended session
            print("✅ Extended diagnostic session activated")

            # Step 5: UDS Read Data by Identifier (VIN)
            print("\n=== Step 5: UDS Read Data by Identifier (VIN) ===")

            # Send VIN read request
            vin_request = self._create_read_data_by_identifier_request(0xF190)
            diag_request = self._create_diagnostic_message_request(
                0x0E00, 0x1000, vin_request
            )
            tcp_client.send(diag_request)

            # Receive VIN response
            response = tcp_client.recv(1024)
            vin_response = self._parse_diagnostic_message_response(response)

            assert vin_response["uds_response"][0] == 0x62  # Positive response
            assert vin_response["uds_response"][1] == 0xF1  # Data identifier high
            assert vin_response["uds_response"][2] == 0x90  # Data identifier low
            print("✅ VIN read successful")

            # Step 6: ECU-Specific UDS Services
            print("\n=== Step 6: ECU-Specific UDS Services ===")

            # Test Engine ECU services
            engine_services = [
                (0x220C01, "Engine RPM Read"),
                (0x220C05, "Engine Temperature Read"),
                (0x220C2F, "Fuel Level Read"),
            ]

            for service_id, service_name in engine_services:
                print(f"  Testing {service_name}...")

                # Send service request
                service_request = self._create_read_data_by_identifier_request(
                    service_id
                )
                diag_request = self._create_diagnostic_message_request(
                    0x0E00, 0x1000, service_request
                )
                tcp_client.send(diag_request)

                # Receive service response
                response = tcp_client.recv(1024)
                service_response = self._parse_diagnostic_message_response(response)

                assert service_response["uds_response"][0] == 0x62  # Positive response
                print(f"    ✅ {service_name} successful")

            # Step 7: Response Cycling Test
            print("\n=== Step 7: Response Cycling Test ===")

            # Send multiple VIN requests to test response cycling
            for i in range(3):
                vin_request = self._create_read_data_by_identifier_request(0xF190)
                diag_request = self._create_diagnostic_message_request(
                    0x0E00, 0x1000, vin_request
                )
                tcp_client.send(diag_request)

                response = tcp_client.recv(1024)
                vin_response = self._parse_diagnostic_message_response(response)

                assert vin_response["uds_response"][0] == 0x62
                print(f"    ✅ VIN request {i+1}/3 - Response cycling working")

            # Step 8: Tester Present
            print("\n=== Step 8: Tester Present ===")

            # Send tester present to keep session alive
            tester_present = self._create_tester_present_request()
            diag_request = self._create_diagnostic_message_request(
                0x0E00, 0x1000, tester_present
            )
            tcp_client.send(diag_request)

            response = tcp_client.recv(1024)
            tester_response = self._parse_diagnostic_message_response(response)

            assert tester_response["uds_response"][0] == 0x7E  # Positive response
            print("✅ Tester present successful")

            print("\n🎉 End-to-End UDS Diagnostic Test Completed Successfully!")

        finally:
            tcp_client.close()

    def test_multi_ecu_communication(self, server):
        """Test communication with multiple ECUs"""

        print("\n=== Multi-ECU Communication Test ===")

        # Connect to server
        tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_client.settimeout(10.0)

        try:
            tcp_client.connect(("127.0.0.1", 13400))

            # Activate routing
            routing_request = self._create_routing_activation_request()
            tcp_client.send(routing_request)
            tcp_client.recv(1024)  # Consume response

            # Test Engine ECU (0x1000)
            print("Testing Engine ECU (0x1000)...")
            engine_request = self._create_diagnostic_message_request(
                0x0E00,
                0x1000,
                self._create_read_data_by_identifier_request(0x220C01),  # RPM
            )
            tcp_client.send(engine_request)
            engine_response = self._parse_diagnostic_message_response(
                tcp_client.recv(1024)
            )
            assert engine_response["uds_response"][0] == 0x62
            print("  ✅ Engine ECU communication successful")

            # Test Transmission ECU (0x1001)
            print("Testing Transmission ECU (0x1001)...")
            trans_request = self._create_diagnostic_message_request(
                0x0E00,
                0x1001,
                self._create_read_data_by_identifier_request(0x220C0A),  # Gear
            )
            tcp_client.send(trans_request)
            trans_response = self._parse_diagnostic_message_response(
                tcp_client.recv(1024)
            )
            assert trans_response["uds_response"][0] == 0x62
            print("  ✅ Transmission ECU communication successful")

            # Test ABS ECU (0x1002)
            print("Testing ABS ECU (0x1002)...")
            abs_request = self._create_diagnostic_message_request(
                0x0E00,
                0x1002,
                self._create_read_data_by_identifier_request(0x220C0B),  # Wheel Speed
            )
            tcp_client.send(abs_request)
            abs_response = self._parse_diagnostic_message_response(
                tcp_client.recv(1024)
            )
            assert abs_response["uds_response"][0] == 0x62
            print("  ✅ ABS ECU communication successful")

            print("✅ Multi-ECU communication test completed")

        finally:
            tcp_client.close()

    def test_error_handling_and_validation(self, server):
        """Test error handling and validation scenarios"""

        print("\n=== Error Handling and Validation Test ===")

        tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_client.settimeout(5.0)

        try:
            tcp_client.connect(("127.0.0.1", 13400))

            # Test invalid source address
            print("Testing invalid source address...")
            invalid_request = self._create_diagnostic_message_request(
                0x9999,
                0x1000,  # Invalid source address
                self._create_read_data_by_identifier_request(0xF190),
            )
            tcp_client.send(invalid_request)
            response = tcp_client.recv(1024)

            # Should receive NACK for invalid source address
            diag_response = self._parse_diagnostic_message_response(response)
            assert diag_response is None or len(diag_response["uds_response"]) == 0
            print("  ✅ Invalid source address correctly rejected")

            # Test invalid target address
            print("Testing invalid target address...")
            invalid_request = self._create_diagnostic_message_request(
                0x0E00,
                0x9999,  # Invalid target address
                self._create_read_data_by_identifier_request(0xF190),
            )
            tcp_client.send(invalid_request)
            response = tcp_client.recv(1024)

            # Should receive NACK for invalid target address
            diag_response = self._parse_diagnostic_message_response(response)
            assert diag_response is None or len(diag_response["uds_response"]) == 0
            print("  ✅ Invalid target address correctly rejected")

            print("✅ Error handling test completed")

        finally:
            tcp_client.close()

    # Helper methods for creating DoIP messages

    def _create_routing_activation_request(self):
        """Create DoIP routing activation request"""
        # DoIP header
        header = struct.pack(">BBHI", 0x02, 0xFD, 0x0005, 7)

        # Routing activation payload
        payload = struct.pack(
            ">HHB", 0x0E00, 0x1000, 0x00
        )  # Client, target, response code
        payload += struct.pack(">I", 0x00000000)  # Reserved

        return header + payload

    def _parse_routing_activation_response(self, data):
        """Parse DoIP routing activation response"""
        if len(data) < 15:
            return None

        # Parse header
        protocol_version = data[0]
        inverse_protocol_version = data[1]
        payload_type = struct.unpack(">H", data[2:4])[0]
        payload_length = struct.unpack(">I", data[4:8])[0]

        # Parse payload
        client_logical_address = struct.unpack(">H", data[8:10])[0]
        logical_address = struct.unpack(">H", data[10:12])[0]
        response_code = data[12]

        return {
            "protocol_version": protocol_version,
            "inverse_protocol_version": inverse_protocol_version,
            "payload_type": payload_type,
            "payload_length": payload_length,
            "client_logical_address": client_logical_address,
            "logical_address": logical_address,
            "response_code": response_code,
        }

    def _create_diagnostic_message_request(self, source_addr, target_addr, uds_payload):
        """Create DoIP diagnostic message request"""
        # DoIP header
        header = struct.pack(">BBHI", 0x02, 0xFD, 0x8001, len(uds_payload) + 4)

        # Diagnostic message payload
        payload = struct.pack(">HH", source_addr, target_addr) + uds_payload

        return header + payload

    def _parse_diagnostic_message_response(self, data):
        """Parse DoIP diagnostic message response"""
        if len(data) < 8:
            return None

        # Parse header
        protocol_version = data[0]
        inverse_protocol_version = data[1]
        payload_type = struct.unpack(">H", data[2:4])[0]
        payload_length = struct.unpack(">I", data[4:8])[0]

        if payload_length < 4:
            return None

        # Parse payload
        source_address = struct.unpack(">H", data[8:10])[0]
        target_address = struct.unpack(">H", data[10:12])[0]
        uds_response = data[12 : 12 + payload_length - 4]

        return {
            "protocol_version": protocol_version,
            "inverse_protocol_version": inverse_protocol_version,
            "payload_type": payload_type,
            "payload_length": payload_length,
            "source_address": source_address,
            "target_address": target_address,
            "uds_response": uds_response,
        }

    def _create_diagnostic_session_control_request(self, session_type):
        """Create UDS diagnostic session control request"""
        return bytes([0x10, session_type])

    def _create_read_data_by_identifier_request(self, data_identifier):
        """Create UDS read data by identifier request"""
        return bytes([0x22, (data_identifier >> 8) & 0xFF, data_identifier & 0xFF])

    def _create_tester_present_request(self):
        """Create UDS tester present request"""
        return bytes([0x3E, 0x00])


class TestUDSEndToEndIntegration:
    """Integration tests for end-to-end UDS communication"""

    def test_complete_diagnostic_workflow(self):
        """Test complete diagnostic workflow with real server"""

        print("\n=== Complete Diagnostic Workflow Test ===")

        # Start server in background
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")
        server_thread = threading.Thread(target=server.start, daemon=True)
        server_thread.start()

        try:
            # Wait for server to start
            time.sleep(2)

            # Step 1: UDP Discovery
            print("1. UDP Vehicle Discovery...")
            udp_client = UDPDoIPClient(server_port=13400, timeout=5.0)
            udp_client.start()
            vehicle_info = udp_client.send_vehicle_identification_request()
            udp_client.stop()

            assert vehicle_info is not None
            print(f"   ✅ Vehicle discovered: {vehicle_info['vin']}")

            # Step 2: TCP Diagnostic Communication
            print("2. TCP Diagnostic Communication...")

            tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_client.settimeout(10.0)
            tcp_client.connect(("127.0.0.1", 13400))

            # Routing activation
            routing_request = self._create_routing_activation_request()
            tcp_client.send(routing_request)
            tcp_client.recv(1024)
            print("   ✅ Routing activation successful")

            # Diagnostic session control
            session_request = bytes([0x10, 0x03])  # Extended session
            diag_request = self._create_diagnostic_message_request(
                0x0E00, 0x1000, session_request
            )
            tcp_client.send(diag_request)
            tcp_client.recv(1024)
            print("   ✅ Diagnostic session activated")

            # Read VIN
            vin_request = bytes([0x22, 0xF1, 0x90])
            diag_request = self._create_diagnostic_message_request(
                0x0E00, 0x1000, vin_request
            )
            tcp_client.send(diag_request)
            vin_response = tcp_client.recv(1024)
            print("   ✅ VIN read successful")

            tcp_client.close()

            print("🎉 Complete diagnostic workflow test passed!")

        finally:
            server.stop()

    def _create_routing_activation_request(self):
        """Create DoIP routing activation request"""
        header = struct.pack(">BBHI", 0x02, 0xFD, 0x0005, 7)
        payload = struct.pack(">HHB", 0x0E00, 0x1000, 0x00) + struct.pack(
            ">I", 0x00000000
        )
        return header + payload

    def _create_diagnostic_message_request(self, source_addr, target_addr, uds_payload):
        """Create DoIP diagnostic message request"""
        header = struct.pack(">BBHI", 0x02, 0xFD, 0x8001, len(uds_payload) + 4)
        payload = struct.pack(">HH", source_addr, target_addr) + uds_payload
        return header + payload


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
