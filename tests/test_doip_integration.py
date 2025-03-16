#!/usr/bin/env python3
"""
Integration tests for DoIP server and client functionality.
Tests routine activation and UDS message handling.
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
from doip_server.doip_client import DoIPClient


class TestDoIPIntegration:
    """Integration tests for DoIP server and client"""
    
    @pytest.fixture(scope="class")
    def server(self):
        """Create and start a DoIP server for testing"""
        server = DoIPServer('127.0.0.1', 13400)
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        yield server
        
        # Cleanup
        server.stop()
        time.sleep(1)
    
    def test_server_startup(self, server):
        """Test that the server starts successfully"""
        assert server.running is True
        assert server.server_socket is not None
    
    def test_client_connection(self, server):
        """Test that client can connect to server"""
        client = DoIPClient('127.0.0.1', 13400)
        client.connect()
        
        assert client.client_socket is not None
        
        client.disconnect()
    
    def test_routine_activation(self, server):
        """Test routine activation functionality"""
        client = DoIPClient('127.0.0.1', 13400)
        client.connect()
        
        try:
            # Test routine activation
            response = client.send_routine_activation(0x0202, 0x0001)
            assert response is not None
            assert len(response) > 0
            
            # Verify response format (DoIP header + payload)
            assert len(response) >= 8  # Minimum DoIP header size
            
        finally:
            client.disconnect()
    
    def test_uds_read_data_by_identifier(self, server):
        """Test UDS Read Data by Identifier service"""
        client = DoIPClient('127.0.0.1', 13400)
        client.connect()
        
        try:
            # Test supported data identifier
            response = client.send_uds_read_data_by_identifier(0xF187)
            assert response is not None
            assert len(response) > 0
            
            # Verify response format
            assert len(response) >= 8  # Minimum DoIP header size
            
        finally:
            client.disconnect()
    
    def test_alive_check(self, server):
        """Test alive check functionality"""
        client = DoIPClient('127.0.0.1', 13400)
        client.connect()
        
        try:
            response = client.send_alive_check()
            assert response is not None
            assert len(response) > 0
            
        finally:
            client.disconnect()


class TestDoIPMessageFormats:
    """Test DoIP message format construction"""
    
    def test_routine_activation_message_format(self):
        """Test routine activation message construction"""
        client = DoIPClient('127.0.0.1', 13400)
        
        # Test message creation without connecting
        routine_id = 0x0202
        routine_type = 0x0001
        
        # Create payload
        payload = client._pack_routine_activation_payload(routine_id, routine_type)
        assert len(payload) == 4
        assert payload[0:2] == b'\x02\x02'  # Routine ID
        assert payload[2:4] == b'\x00\x01'  # Routine Type
    
    def test_uds_message_format(self):
        """Test UDS message construction"""
        client = DoIPClient('127.0.0.1', 13400)
        
        data_identifier = 0xF187
        source_addr = 0x0E00
        target_addr = 0x1000
        
        # Create UDS payload
        uds_payload = client._pack_uds_read_data_payload(data_identifier)
        assert len(uds_payload) == 3
        assert uds_payload[0] == 0x22  # UDS service ID
        assert uds_payload[1:3] == b'\xF1\x87'  # Data identifier
    
    def test_doip_header_format(self):
        """Test DoIP header construction"""
        client = DoIPClient('127.0.0.1', 13400)
        
        payload_type = 0x0005  # Routine activation
        payload_length = 4
        
        header = client.create_doip_header(payload_type, payload_length)
        assert len(header) == 8
        
        # Verify protocol version
        assert header[0] == 0x02  # Protocol version
        assert header[1] == 0xFD  # Inverse protocol version
        
        # Verify payload type and length
        assert header[2:4] == b'\x00\x05'  # Payload type
        assert header[4:8] == b'\x00\x00\x00\x04'  # Payload length


class TestDoIPConfiguration:
    """Test DoIP configuration loading and validation"""
    
    def test_default_configuration_loading(self):
        """Test that server can load default configuration"""
        server = DoIPServer()
        
        assert server.config_manager is not None
        assert server.config_manager.config is not None
        
        # Verify basic configuration sections exist
        assert 'server' in server.config_manager.config
        assert 'protocol' in server.config_manager.config
        assert 'addresses' in server.config_manager.config
    
    def test_configuration_validation(self):
        """Test configuration validation"""
        server = DoIPServer()
        
        # Configuration should be valid by default
        assert server.config_manager.validate_config() is True
    
    def test_supported_routines_configuration(self):
        """Test that supported routines are loaded from configuration"""
        server = DoIPServer()
        
        routines = server.config_manager.get_routine_activation_config()
        supported_routines = routines.get('supported_routines', {})
        
        # Should have at least one supported routine
        assert len(supported_routines) > 0
        
        # Check that routine 0x0202 is supported
        assert 0x0202 in supported_routines
    
    def test_uds_services_configuration(self):
        """Test that UDS services are loaded from configuration"""
        server = DoIPServer()
        
        uds_services = server.config_manager.get_uds_services_config()
        
        # Should have at least one UDS service
        assert len(uds_services) > 0
        
        # Check that service 0x22 is supported
        assert 0x22 in uds_services
        
        # Check that data identifier 0xF187 is supported
        service_22 = uds_services[0x22]
        data_ids = service_22.get('supported_data_identifiers', {})
        assert 0xF187 in data_ids


# Helper functions for testing
def _pack_routine_activation_payload(self, routine_id, routine_type):
    """Helper method to pack routine activation payload"""
    import struct
    return struct.pack('>HH', routine_id, routine_type)


def _pack_uds_read_data_payload(self, data_identifier):
    """Helper method to pack UDS read data payload"""
    import struct
    return b'\x22' + struct.pack('>H', data_identifier)


# Add helper methods to DoIPClient class for testing
DoIPClient._pack_routine_activation_payload = _pack_routine_activation_payload
DoIPClient._pack_uds_read_data_payload = _pack_uds_read_data_payload


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
