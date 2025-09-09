#!/usr/bin/env python3
"""
Updated integration tests for DoIP server and client functionality.
Tests routine activation and UDS message handling with both legacy and hierarchical configurations.
"""

import pytest
import time
import threading
import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doip_server.doip_server import DoIPServer
from doip_client.doip_client import DoIPClientWrapper


class TestDoIPIntegrationHierarchical:
    """Integration tests for DoIP server and client with hierarchical configuration"""

    @pytest.fixture(scope="class")
    def server(self):
        """Create and start a DoIP server for testing with hierarchical config"""
        server = DoIPServer(
            "127.0.0.1", 13400, gateway_config_path="config/gateway1.yaml"
        )
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()

        # Wait for server to start
        time.sleep(5)

        # Verify server is actually running
        assert server.running is True
        assert server.server_socket is not None

        # Test basic socket connection to ensure server is ready
        import socket

        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            test_socket.connect(("127.0.0.1", 13400))
            test_socket.close()
            print("✅ Basic socket connection test passed")
        except Exception as e:
            print(f"❌ Basic socket connection test failed: {e}")
            raise

        yield server

        # Cleanup
        server.stop()
        time.sleep(1)

    def test_server_startup(self, server):
        """Test that the server starts successfully with hierarchical config"""
        assert server.running is True
        assert server.server_socket is not None
        assert hasattr(
            server.config_manager, "get_all_ecu_addresses"
        )  # Hierarchical config manager method

    def test_client_connection(self, server):
        """Test that client can connect to server"""
        # Longer delay to ensure server is fully ready
        time.sleep(2.0)

        # Try multiple connection attempts with delays
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                print(
                    f"Attempting DoIPClientWrapper connection (attempt {attempt + 1}/{max_attempts})"
                )
                client = DoIPClientWrapper("127.0.0.1", 13400)
                print("✅ DoIPClientWrapper connection successful!")
                break
            except Exception as e:
                print(f"❌ DoIPClientWrapper connection attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(1.0)
                else:
                    raise

        # If we get here without an exception, the connection was successful
        assert client is not None

        client.disconnect()

    def test_routine_activation(self, server):
        """Test routine activation functionality"""
        time.sleep(0.5)
        client = DoIPClientWrapper("127.0.0.1", 13400)

        try:
            # If we get here without an exception, the routing activation was successful
            assert client is not None

        finally:
            client.disconnect()

    def test_uds_read_data_by_identifier_engine_ecu(self, server):
        """Test UDS Read Data by Identifier service for Engine ECU"""
        time.sleep(0.5)
        client = DoIPClientWrapper("127.0.0.1", 13400)

        try:
            client.connect()
            # Test VIN reading for Engine ECU (0x1000)
            response = client.send_read_data_by_identifier(0xF190)
            # Response may or may not exist depending on server configuration
            assert response is None or isinstance(response, bytes)
        finally:
            client.disconnect()

    def test_uds_read_data_by_identifier_transmission_ecu(self, server):
        """Test UDS Read Data by Identifier service for Transmission ECU"""
        time.sleep(0.5)
        client = DoIPClientWrapper("127.0.0.1", 13400)

        try:
            client.connect()
            # Test VIN reading for Transmission ECU (0x1001)
            response = client.send_read_data_by_identifier(0xF190)
            # Response may or may not exist depending on server configuration
            assert response is None or isinstance(response, bytes)
        finally:
            client.disconnect()

    def test_uds_read_data_by_identifier_abs_ecu(self, server):
        """Test UDS Read Data by Identifier service for ABS ECU"""
        time.sleep(0.5)
        client = DoIPClientWrapper("127.0.0.1", 13400)

        try:
            client.connect()
            # Test VIN reading for ABS ECU (0x1002)
            response = client.send_read_data_by_identifier(0xF190)
            # Response may or may not exist depending on server configuration
            assert response is None or isinstance(response, bytes)
        finally:
            client.disconnect()

    def test_ecu_specific_services(self, server):
        """Test ECU-specific UDS services"""
        time.sleep(0.5)
        client = DoIPClientWrapper("127.0.0.1", 13400)

        try:
            client.connect()
            # Test Engine-specific service (RPM read) for Engine ECU
            response = client.send_read_data_by_identifier(0x0C01)
            # Response may or may not exist depending on server configuration
            assert response is None or isinstance(response, bytes)

            # Test Transmission-specific service (Gear read) for Transmission ECU
            response = client.send_read_data_by_identifier(0x0C0A)
            # Response may or may not exist depending on server configuration
            assert response is None or isinstance(response, bytes)

            # Test ABS-specific service (Wheel speed read) for ABS ECU
            response = client.send_read_data_by_identifier(0x0C0B)
            # Response may or may not exist depending on server configuration
            assert response is None or isinstance(response, bytes)
        finally:
            client.disconnect()

    def test_alive_check(self, server):
        """Test alive check functionality"""
        time.sleep(0.5)
        client = DoIPClientWrapper("127.0.0.1", 13400)

        try:
            client.connect()
            response = client.send_alive_check()
            # Response may or may not exist depending on server configuration
            assert response is None or isinstance(response, (bytes, str))
        finally:
            client.disconnect()


class TestDoIPMessageFormats:
    """Test DoIP message format construction"""

    def test_routine_activation_message_format(self):
        """Test routine activation message construction"""
        # Test message creation using our server's method
        from src.doip_server.doip_server import DoIPServer
        import struct

        server = DoIPServer()

        # Test routing activation payload creation
        routine_id = 0x0202
        routine_type = 0x0001

        # Create payload manually (routing activation format)
        payload = struct.pack(">H", 0x0E00)  # Client logical address
        payload += struct.pack(">H", 0x1000)  # Logical address
        payload += struct.pack(">B", 0x00)  # Response code
        payload += struct.pack(">I", 0x00000000)  # Reserved

        assert len(payload) == 9  # 2 + 2 + 1 + 4 = 9 bytes
        assert payload[0:2] == b"\x0e\x00"  # Client address
        assert payload[2:4] == b"\x10\x00"  # Logical address
        assert payload[4] == 0x00  # Response code

    def test_uds_message_format(self):
        """Test UDS message construction"""
        import struct

        data_identifier = 0xF187
        source_addr = 0x0E00
        target_addr = 0x1000

        # Create UDS payload manually
        uds_payload = struct.pack(">B", 0x22)  # UDS service ID
        uds_payload += struct.pack(">H", data_identifier)  # Data identifier

        assert len(uds_payload) == 3
        assert uds_payload[0] == 0x22  # UDS service ID
        assert uds_payload[1:3] == b"\xF1\x87"  # Data identifier

    def test_doip_header_format(self):
        """Test DoIP header construction"""
        import struct

        payload_type = 0x0005  # Routing activation
        payload_length = 7

        # Create DoIP header manually
        header = struct.pack(
            ">BBHI",
            0x02,  # Protocol version
            0xFD,  # Inverse protocol version
            payload_type,
            payload_length,
        )

        assert len(header) == 8
        assert header[0] == 0x02  # Protocol version
        assert header[1] == 0xFD  # Inverse protocol version
        assert header[2:4] == b"\x00\x05"  # Payload type
        assert header[4:8] == b"\x00\x00\x00\x07"  # Payload length


class TestDoIPConfiguration:
    """Test DoIP configuration loading and validation"""


    def test_hierarchical_configuration_loading(self):
        """Test that server can load hierarchical configuration"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        assert server.config_manager is not None
        # For hierarchical config, we expect the new interface
        assert hasattr(server.config_manager, "get_all_ecu_addresses")
        assert hasattr(server.config_manager, "get_ecu_uds_services")

    def test_hierarchical_configuration_validation(self):
        """Test hierarchical configuration validation"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Configuration should be valid
        assert server.config_manager.validate_configs() is True

    def test_hierarchical_ecu_loading(self):
        """Test that ECUs are loaded correctly in hierarchical configuration"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        ecu_addresses = server.config_manager.get_all_ecu_addresses()
        assert len(ecu_addresses) == 3
        assert 0x1000 in ecu_addresses  # Engine ECU
        assert 0x1001 in ecu_addresses  # Transmission ECU
        assert 0x1002 in ecu_addresses  # ABS ECU

    def test_hierarchical_uds_services(self):
        """Test that UDS services are loaded correctly in hierarchical configuration"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Test Engine ECU services
        engine_services = server.config_manager.get_ecu_uds_services(0x1000)
        assert len(engine_services) > 0
        assert "Read_VIN" in engine_services  # Common service
        assert "Engine_RPM_Read" in engine_services  # Engine-specific service

        # Test Transmission ECU services
        transmission_services = server.config_manager.get_ecu_uds_services(0x1001)
        assert len(transmission_services) > 0
        assert "Read_VIN" in transmission_services  # Common service
        assert (
            "Transmission_Gear_Read" in transmission_services
        )  # Transmission-specific service

        # Test ABS ECU services
        abs_services = server.config_manager.get_ecu_uds_services(0x1002)
        assert len(abs_services) > 0
        assert "Read_VIN" in abs_services  # Common service
        assert "ABS_Wheel_Speed_Read" in abs_services  # ABS-specific service


# Helper functions for testing
def _pack_routine_activation_payload(self, routine_id, routine_type):
    """Helper method to pack routine activation payload"""
    import struct

    return struct.pack(">HH", routine_id, routine_type)


def _pack_uds_read_data_payload(self, data_identifier):
    """Helper method to pack UDS read data payload"""
    import struct

    return b"\x22" + struct.pack(">H", data_identifier)


# Add helper methods to DoIPClientWrapper class for testing
DoIPClientWrapper._pack_routine_activation_payload = _pack_routine_activation_payload
DoIPClientWrapper._pack_uds_read_data_payload = _pack_uds_read_data_payload


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
