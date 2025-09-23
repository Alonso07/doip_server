#!/usr/bin/env python3
"""
Tests for the new hierarchical configuration system.
Tests the HierarchicalConfigManager and its integration with the DoIP server.
"""

import pytest
import sys
import os
import time
import threading
from pathlib import Path

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doip_server.hierarchical_config_manager import HierarchicalConfigManager
from doip_server.doip_server import DoIPServer


class TestHierarchicalConfigurationManager:
    """Test the hierarchical configuration manager functionality"""

    def test_config_manager_creation(self):
        """Test that hierarchical configuration manager can be created"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")
        assert config_manager is not None
        assert config_manager.gateway_config is not None

    def test_gateway_config_loading(self):
        """Test gateway configuration loading"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")
        gateway_config = config_manager.get_gateway_config()

        assert "name" in gateway_config
        assert "network" in gateway_config
        assert "protocol" in gateway_config
        assert "ecus" in gateway_config

        assert gateway_config["name"] == "Gateway1"
        assert gateway_config["network"]["port"] == 13400

    def test_network_config_loading(self):
        """Test network configuration loading"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")
        network_config = config_manager.get_network_config()

        assert "host" in network_config
        assert "port" in network_config
        assert "max_connections" in network_config
        assert network_config["port"] == 13400
        assert network_config["host"] == "0.0.0.0"

    def test_protocol_config_loading(self):
        """Test protocol configuration loading"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")
        protocol_config = config_manager.get_protocol_config()

        assert "version" in protocol_config
        assert "inverse_version" in protocol_config
        assert protocol_config["version"] == 0x02
        assert protocol_config["inverse_version"] == 0xFD

    def test_ecu_loading(self):
        """Test ECU configuration loading"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")
        ecu_addresses = config_manager.get_all_ecu_addresses()

        # Should have 3 ECUs loaded
        assert len(ecu_addresses) == 3
        assert 0x1000 in ecu_addresses  # Engine ECU
        assert 0x1001 in ecu_addresses  # Transmission ECU
        assert 0x1002 in ecu_addresses  # ABS ECU

    def test_ecu_config_loading(self):
        """Test individual ECU configuration loading"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")

        # Test Engine ECU
        engine_config = config_manager.get_ecu_config(0x1000)
        assert engine_config is not None
        ecu_info = engine_config.get("ecu", {})
        assert ecu_info["name"] == "Engine_ECU"
        assert ecu_info["target_address"] == 0x1000

        # Test Transmission ECU
        transmission_config = config_manager.get_ecu_config(0x1001)
        assert transmission_config is not None
        ecu_info = transmission_config.get("ecu", {})
        assert ecu_info["name"] == "Transmission_ECU"
        assert ecu_info["target_address"] == 0x1001

        # Test ABS ECU
        abs_config = config_manager.get_ecu_config(0x1002)
        assert abs_config is not None
        ecu_info = abs_config.get("ecu", {})
        assert ecu_info["name"] == "ABS_ECU"
        assert ecu_info["target_address"] == 0x1002

    def test_ecu_tester_addresses(self):
        """Test ECU tester addresses"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")

        # Test Engine ECU tester addresses
        engine_testers = config_manager.get_ecu_tester_addresses(0x1000)
        assert 0x0E00 in engine_testers
        assert 0x0E01 in engine_testers
        assert 0x0E02 in engine_testers

        # Test Transmission ECU tester addresses
        transmission_testers = config_manager.get_ecu_tester_addresses(0x1001)
        assert 0x0E00 in transmission_testers
        assert 0x0E01 in transmission_testers
        assert 0x0E02 in transmission_testers

    def test_address_validation(self):
        """Test address validation"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")

        # Test valid source addresses for specific ECUs
        assert config_manager.is_source_address_allowed(0x0E00, 0x1000) is True
        assert config_manager.is_source_address_allowed(0x0E01, 0x1001) is True
        assert config_manager.is_source_address_allowed(0x0E02, 0x1002) is True

        # Test invalid source addresses
        assert config_manager.is_source_address_allowed(0x9999, 0x1000) is False
        assert config_manager.is_source_address_allowed(0x0E00, 0x9999) is False

        # Test target address validation
        assert config_manager.is_target_address_valid(0x1000) is True
        assert config_manager.is_target_address_valid(0x1001) is True
        assert config_manager.is_target_address_valid(0x1002) is True
        assert config_manager.is_target_address_valid(0x9999) is False

    def test_uds_services_loading(self):
        """Test UDS services loading"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")

        # Test Engine ECU services
        engine_services = config_manager.get_ecu_uds_services(0x1000)
        assert len(engine_services) > 0
        assert "Read_VIN" in engine_services  # Common service
        assert "Engine_RPM_Read" in engine_services  # Engine-specific service
        assert (
            "Transmission_Gear_Read" not in engine_services
        )  # Not available for Engine ECU

        # Test Transmission ECU services
        transmission_services = config_manager.get_ecu_uds_services(0x1001)
        assert len(transmission_services) > 0
        assert "Read_VIN" in transmission_services  # Common service
        assert (
            "Transmission_Gear_Read" in transmission_services
        )  # Transmission-specific service
        assert (
            "Engine_RPM_Read" not in transmission_services
        )  # Not available for Transmission ECU

        # Test ABS ECU services
        abs_services = config_manager.get_ecu_uds_services(0x1002)
        assert len(abs_services) > 0
        assert "Read_VIN" in abs_services  # Common service
        assert "ABS_Wheel_Speed_Read" in abs_services  # ABS-specific service
        assert "Engine_RPM_Read" not in abs_services  # Not available for ABS ECU

    def test_uds_service_lookup(self):
        """Test UDS service lookup by request"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")

        # Test common service lookup for Engine ECU
        service = config_manager.get_uds_service_by_request("0x22F190", 0x1000)
        assert service is not None
        assert service["name"] == "Read_VIN"
        assert service["ecu_address"] == 0x1000

        # Test common service lookup for Transmission ECU
        service = config_manager.get_uds_service_by_request("0x22F190", 0x1001)
        assert service is not None
        assert service["name"] == "Read_VIN"
        assert service["ecu_address"] == 0x1001

        # Test Engine-specific service lookup
        service = config_manager.get_uds_service_by_request("0x220C01", 0x1000)
        assert service is not None
        assert service["name"] == "Engine_RPM_Read"
        assert service["ecu_address"] == 0x1000

        # Test Transmission-specific service lookup
        service = config_manager.get_uds_service_by_request("0x220C0A", 0x1001)
        assert service is not None
        assert service["name"] == "Transmission_Gear_Read"
        assert service["ecu_address"] == 0x1001

        # Test ABS-specific service lookup
        service = config_manager.get_uds_service_by_request("0x220C0B", 0x1002)
        assert service is not None
        assert service["name"] == "ABS_Wheel_Speed_Read"
        assert service["ecu_address"] == 0x1002

        # Test service not available for ECU
        service = config_manager.get_uds_service_by_request(
            "0x220C01", 0x1001
        )  # Engine service for Transmission ECU
        assert service is None

        # Test non-existent service
        service = config_manager.get_uds_service_by_request("0x999999", 0x1000)
        assert service is None

    def test_routine_activation_config(self):
        """Test routine activation configuration for specific ECUs"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")

        # Test Engine ECU routine activation
        engine_routine = config_manager.get_routine_activation_config(0x1000)
        assert "active_type" in engine_routine
        assert engine_routine["active_type"] == 0x00

        # Test Transmission ECU routine activation
        transmission_routine = config_manager.get_routine_activation_config(0x1001)
        assert "active_type" in transmission_routine
        assert transmission_routine["active_type"] == 0x00

    def test_response_codes(self):
        """Test response codes configuration"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")

        # Test routine activation response codes
        desc = config_manager.get_response_code_description("routine_activation", 0x10)
        assert "success" in desc.lower()

        # Test UDS response codes
        desc = config_manager.get_response_code_description("uds", 0x31)
        assert "range" in desc.lower()

    def test_config_validation(self):
        """Test configuration validation"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")
        assert config_manager.validate_configs() is True

    def test_config_summary(self):
        """Test configuration summary generation"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")
        summary = config_manager.get_config_summary()

        assert "Hierarchical DoIP Configuration Summary" in summary
        assert "Gateway: Gateway1" in summary
        assert "Configured ECUs: 3" in summary
        assert "0x1000: Engine_ECU" in summary
        assert "0x1001: Transmission_ECU" in summary
        assert "0x1002: ABS_ECU" in summary


class TestHierarchicalDoIPServer:
    """Test DoIP server with hierarchical configuration"""

    def test_server_creation_with_hierarchical_config(self):
        """Test that server can be created with hierarchical configuration"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        assert server is not None
        assert server.config_manager is not None
        assert isinstance(server.config_manager, HierarchicalConfigManager)

    def test_server_configuration_loading(self):
        """Test that server loads hierarchical configuration correctly"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Test that ECUs are loaded
        ecu_addresses = server.config_manager.get_all_ecu_addresses()
        assert len(ecu_addresses) == 3
        assert 0x1000 in ecu_addresses
        assert 0x1001 in ecu_addresses
        assert 0x1002 in ecu_addresses

    def test_server_address_validation(self):
        """Test server address validation with hierarchical config"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Test valid addresses
        assert server.config_manager.is_source_address_allowed(0x0E00, 0x1000) is True
        assert server.config_manager.is_target_address_valid(0x1000) is True

        # Test invalid addresses
        assert server.config_manager.is_source_address_allowed(0x9999, 0x1000) is False
        assert server.config_manager.is_target_address_valid(0x9999) is False

    def test_server_uds_service_processing(self):
        """Test server UDS service processing with hierarchical config"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Test common service for Engine ECU
        service = server.config_manager.get_uds_service_by_request("0x22F190", 0x1000)
        assert service is not None
        assert service["name"] == "Read_VIN"

        # Test Engine-specific service
        service = server.config_manager.get_uds_service_by_request("0x220C01", 0x1000)
        assert service is not None
        assert service["name"] == "Engine_RPM_Read"

        # Test service not available for ECU (using a pattern that doesn't match any regex)
        service = server.config_manager.get_uds_service_by_request(
            "0x9999", 0x1000
        )  # Non-existent service for Engine ECU
        assert service is None

    def test_regex_request_matching(self):
        """Test regex-based request matching functionality"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")
        
        # Test exact matching still works
        assert config_manager._match_request("0x220C01", "220C01") is True
        assert config_manager._match_request("220C01", "0x220C01") is True
        assert config_manager._match_request("0x220C01", "0x220C01") is True
        
        # Test regex matching with various patterns
        assert config_manager._match_request("regex:^220C[0-9A-F]{2}$", "220C01") is True
        assert config_manager._match_request("regex:^220C[0-9A-F]{2}$", "220CFF") is True
        assert config_manager._match_request("regex:^220C[0-9A-F]{2}$", "0x220C01") is True
        assert config_manager._match_request("regex:^220C[0-9A-F]{2}$", "220C") is False  # Too short
        assert config_manager._match_request("regex:^220C[0-9A-F]{2}$", "220C123") is False  # Too long
        
        # Test diagnostic session control pattern
        assert config_manager._match_request("regex:^10[0-9A-F]{2}$", "1003") is True
        assert config_manager._match_request("regex:^10[0-9A-F]{2}$", "10FF") is True
        assert config_manager._match_request("regex:^10[0-9A-F]{2}$", "0x1003") is True
        assert config_manager._match_request("regex:^10[0-9A-F]{2}$", "100") is False  # Too short
        
        # Test security access pattern
        assert config_manager._match_request("regex:^27[0-9A-F]{2}$", "2701") is True
        assert config_manager._match_request("regex:^27[0-9A-F]{2}$", "27FF") is True
        assert config_manager._match_request("regex:^27[0-9A-F]{2}$", "0x2701") is True
        assert config_manager._match_request("regex:^27[0-9A-F]{2}$", "270") is False  # Too short
        
        # Test complex pattern for routine control
        assert config_manager._match_request("regex:^31[0-9A-F]{2}00[0-9A-F]{2}$", "31010001") is True
        assert config_manager._match_request("regex:^31[0-9A-F]{2}00[0-9A-F]{2}$", "31FF00FF") is True
        assert config_manager._match_request("regex:^31[0-9A-F]{2}00[0-9A-F]{2}$", "0x31010001") is True
        assert config_manager._match_request("regex:^31[0-9A-F]{2}00[0-9A-F]{2}$", "3101000") is False  # Too short
        assert config_manager._match_request("regex:^31[0-9A-F]{2}00[0-9A-F]{2}$", "310100011") is False  # Too long
        
        # Test alternation pattern
        assert config_manager._match_request("regex:^19(02|03|0A)$", "1902") is True
        assert config_manager._match_request("regex:^19(02|03|0A)$", "1903") is True
        assert config_manager._match_request("regex:^19(02|03|0A)$", "190A") is True
        assert config_manager._match_request("regex:^19(02|03|0A)$", "0x1902") is True
        assert config_manager._match_request("regex:^19(02|03|0A)$", "1901") is False  # Not in alternation
        assert config_manager._match_request("regex:^19(02|03|0A)$", "190B") is False  # Not in alternation
        
        # Test case insensitivity
        assert config_manager._match_request("regex:^220C[0-9A-F]{2}$", "220c01") is True
        assert config_manager._match_request("regex:^220C[0-9A-F]{2}$", "220C01") is True
        assert config_manager._match_request("regex:^220C[0-9A-F]{2}$", "220cff") is True
        
        # Test invalid regex patterns
        assert config_manager._match_request("regex:^220C[0-9A-F{2}$", "220C01") is False  # Invalid regex
        assert config_manager._match_request("regex:^220C[0-9A-F]{2", "220C01") is False  # Invalid regex
        
        # Test non-regex strings (should not match)
        assert config_manager._match_request("regex:^220C[0-9A-F]{2}$", "220C01") is True
        assert config_manager._match_request("not_regex:^220C[0-9A-F]{2}$", "220C01") is False  # Not a regex prefix

    def test_regex_service_lookup(self):
        """Test that regex-based services can be found in configuration"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")
        
        # Test that regex services from generic config can be found
        service = config_manager.get_uds_service_by_request("22F190", 0x1000)  # Engine ECU
        assert service is not None
        assert "Read_Data_By_Identifier_Any" in service["name"] or "Read_VIN" in service["name"]
        
        # Test that regex services from engine config can be found
        service = config_manager.get_uds_service_by_request("220C01", 0x1000)  # Engine ECU
        assert service is not None
        # Should match either exact or regex pattern
        assert "Engine_RPM_Read" in service["name"] or "Engine_Data_Read_Any" in service["name"]


class TestHierarchicalConfigurationIntegration:
    """Integration tests for hierarchical configuration with server"""

    @pytest.fixture(scope="class")
    def server(self):
        """Create and start a DoIP server with hierarchical configuration for testing"""
        server = DoIPServer(
            "127.0.0.1", 13401, gateway_config_path="config/gateway1.yaml"
        )
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()

        # Wait for server to start
        time.sleep(2)

        yield server

        # Cleanup
        server.stop()
        time.sleep(1)

    def test_server_startup_with_hierarchical_config(self, server):
        """Test that the server starts successfully with hierarchical configuration"""
        assert server.running is True
        assert server.server_socket is not None
        assert isinstance(server.config_manager, HierarchicalConfigManager)

    def test_hierarchical_configuration_validation(self, server):
        """Test that hierarchical configuration is valid"""
        assert server.config_manager.validate_configs() is True

    def test_ecu_loading_in_server(self, server):
        """Test that ECUs are loaded correctly in the server"""
        ecu_addresses = server.config_manager.get_all_ecu_addresses()
        assert len(ecu_addresses) == 3
        assert 0x1000 in ecu_addresses  # Engine ECU
        assert 0x1001 in ecu_addresses  # Transmission ECU
        assert 0x1002 in ecu_addresses  # ABS ECU


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
