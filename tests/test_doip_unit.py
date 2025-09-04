#!/usr/bin/env python3
"""
Unit tests for DoIP functionality.
Tests individual components without requiring server startup.
"""

import pytest
import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doip_server.config_manager import DoIPConfigManager


class TestDoIPConfigurationManager:
    """Test the configuration manager functionality"""
    
    def test_config_manager_creation(self):
        """Test that configuration manager can be created"""
        config_manager = DoIPConfigManager()
        assert config_manager is not None
        assert config_manager.config is not None
    
    def test_config_sections_exist(self):
        """Test that all required configuration sections exist"""
        config_manager = DoIPConfigManager()
        config = config_manager.config
        
        required_sections = ['server', 'protocol', 'addresses', 'routine_activation', 'uds_services']
        for section in required_sections:
            assert section in config, f"Missing required section: {section}"
    
    def test_server_config_loading(self):
        """Test server configuration loading"""
        config_manager = DoIPConfigManager()
        server_config = config_manager.get_server_config()
        
        assert 'host' in server_config
        assert 'port' in server_config
        assert server_config['port'] == 13400
    
    def test_protocol_config_loading(self):
        """Test protocol configuration loading"""
        config_manager = DoIPConfigManager()
        protocol_config = config_manager.get_protocol_config()
        
        assert 'version' in protocol_config
        assert 'inverse_version' in protocol_config
        assert protocol_config['version'] == 0x02
        assert protocol_config['inverse_version'] == 0xFD
    
    def test_addresses_config_loading(self):
        """Test addresses configuration loading"""
        config_manager = DoIPConfigManager()
        addresses_config = config_manager.get_addresses_config()
        
        assert 'allowed_sources' in addresses_config
        assert 'target_addresses' in addresses_config
        assert 'default_source' in addresses_config
        
        # Check that we have at least one allowed source and target
        assert len(addresses_config['allowed_sources']) > 0
        assert len(addresses_config['target_addresses']) > 0
    
    def test_routine_activation_config_loading(self):
        """Test routine activation configuration loading"""
        config_manager = DoIPConfigManager()
        routine_config = config_manager.get_routine_activation_config()
        
        assert 'active_type' in routine_config
        assert 'reserved_by_iso' in routine_config
        assert 'reserved_by_manufacturer' in routine_config
        
        # Check that we have valid values
        assert routine_config['active_type'] == 0x00
        assert routine_config['reserved_by_iso'] == 0x00000000
        assert routine_config['reserved_by_manufacturer'] == 0x00000000
    
    def test_uds_services_config_loading(self):
        """Test UDS services configuration loading"""
        config_manager = DoIPConfigManager()
        uds_config = config_manager.get_uds_services_config()
        
        # Check that we have at least one UDS service
        assert len(uds_config) > 0
        
        # Check that Read_VIN service exists
        assert 'Read_VIN' in uds_config
        
        read_vin_service = uds_config['Read_VIN']
        assert 'request' in read_vin_service
        assert 'responses' in read_vin_service
        
        # Check that we have valid request and responses
        assert read_vin_service['request'] == '0x22F190'
        assert len(read_vin_service['responses']) > 0
    
    def test_source_address_validation(self):
        """Test source address validation"""
        config_manager = DoIPConfigManager()
        
        # Test allowed source address
        assert config_manager.is_source_address_allowed(0x0E00) is True
        
        # Test disallowed source address
        assert config_manager.is_source_address_allowed(0x9999) is False
    
    def test_target_address_validation(self):
        """Test target address validation"""
        config_manager = DoIPConfigManager()
        
        # Test valid target address
        assert config_manager.is_target_address_valid(0x1000) is True
        
        # Test invalid target address
        assert config_manager.is_target_address_valid(0x9999) is False
    
    def test_routine_activation_methods(self):
        """Test routine activation methods"""
        config_manager = DoIPConfigManager()
        
        # Test routine activation type
        active_type = config_manager.get_routine_activation_type()
        assert active_type == 0x00
        
        # Test reserved values
        reserved_iso = config_manager.get_routine_reserved_by_iso()
        assert reserved_iso == 0x00000000
        
        reserved_manufacturer = config_manager.get_routine_reserved_by_manufacturer()
        assert reserved_manufacturer == 0x00000000
    
    def test_uds_service_lookup(self):
        """Test UDS service lookup"""
        config_manager = DoIPConfigManager()
        
        # Test existing service by name
        service = config_manager.get_uds_service_by_name('Read_VIN')
        assert service is not None
        assert service['name'] == 'Read_VIN'
        assert service['request'] == '0x22F190'
        assert len(service['responses']) > 0
        
        # Test existing service by request
        service = config_manager.get_uds_service_by_request('22F190')
        assert service is not None
        assert service['name'] == 'Read_VIN'
        
        # Test non-existing service
        service = config_manager.get_uds_service_by_name('NonExistentService')
        assert service is None
        
        # Test non-existing request
        service = config_manager.get_uds_service_by_request('999999')
        assert service is None
    
    def test_response_code_descriptions(self):
        """Test response code description loading"""
        config_manager = DoIPConfigManager()
        
        # Test routine activation response codes
        routine_desc = config_manager.get_response_code_description('routine_activation', 0x10)
        assert 'success' in routine_desc.lower() or routine_desc != f"Unknown response code: 0x10"
        
        # Test UDS response codes
        uds_desc = config_manager.get_response_code_description('uds', 0x31)
        assert 'range' in uds_desc.lower() or uds_desc != f"Unknown response code: 0x31"
    
    def test_config_validation(self):
        """Test configuration validation"""
        config_manager = DoIPConfigManager()
        
        # Configuration should be valid
        assert config_manager.validate_config() is True
    
    def test_config_summary(self):
        """Test configuration summary generation"""
        config_manager = DoIPConfigManager()
        summary = config_manager.get_config_summary()
        
        assert "DoIP Configuration Summary" in summary
        assert "Server:" in summary
        assert "Protocol Version:" in summary
        assert "Target Addresses:" in summary


class TestDoIPMessageFormats:
    """Test DoIP message format construction without server"""
    
    def test_doip_header_creation(self):
        """Test DoIP header creation"""
        import struct
        
        # Create header manually
        protocol_version = 0x02
        inverse_version = 0xFD
        payload_type = 0x0005
        payload_length = 4
        
        header = struct.pack('>BBHI', 
                           protocol_version,
                           inverse_version,
                           payload_type,
                           payload_length)
        
        assert len(header) == 8
        assert header[0] == 0x02
        assert header[1] == 0xFD
        assert header[2:4] == b'\x00\x05'
        assert header[4:8] == b'\x00\x00\x00\x04'
    
    def test_routine_activation_payload(self):
        """Test routine activation payload creation"""
        import struct
        
        routine_id = 0x0202
        routine_type = 0x0001
        
        payload = struct.pack('>HH', routine_id, routine_type)
        
        assert len(payload) == 4
        assert payload[0:2] == b'\x02\x02'
        assert payload[2:4] == b'\x00\x01'
    
    def test_uds_payload_creation(self):
        """Test UDS payload creation"""
        import struct
        
        service_id = 0x22
        data_identifier = 0xF187
        
        payload = bytes([service_id]) + struct.pack('>H', data_identifier)
        
        assert len(payload) == 3
        assert payload[0] == 0x22
        assert payload[1:3] == b'\xF1\x87'


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
