#!/usr/bin/env python3
"""
Tests for response cycling functionality
Tests that the server cycles through different responses for the same UDS service
"""

import pytest
import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doip_server.doip_server import DoIPServer
from doip_server.hierarchical_config_manager import HierarchicalConfigManager


class TestResponseCycling:
    """Test response cycling functionality"""

    def test_response_cycling_initialization(self):
        """Test that response cycling state is properly initialized"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Check that response cycling state is initialized
        assert hasattr(server, "response_cycle_state")
        assert isinstance(server.response_cycle_state, dict)
        assert len(server.response_cycle_state) == 0  # Should be empty initially

    def test_response_cycling_hierarchical_config(self):
        """Test response cycling with hierarchical configuration"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Test Read_VIN service for Engine ECU (has 2 responses)
        request_bytes = bytes.fromhex("22F190")
        target_address = 0x1000

        # First call - should return first response
        response1 = server.process_uds_message(request_bytes, target_address)
        assert response1 is not None
        assert response1.hex().upper() == "62F1901020011223344556677889AABB"

        # Check cycling state
        cycling_state = server.get_response_cycling_state()
        key = "ECU_0x1000_Read_VIN"
        assert key in cycling_state
        assert cycling_state[key] == 1  # Next response should be index 1

        # Second call - should return second response
        response2 = server.process_uds_message(request_bytes, target_address)
        assert response2 is not None
        assert response2.hex().upper() == "62F1901020011223344556677889BBCC"

        # Check cycling state
        cycling_state = server.get_response_cycling_state()
        assert cycling_state[key] == 0  # Next response should cycle back to index 0

        # Third call - should return first response again
        response3 = server.process_uds_message(request_bytes, target_address)
        assert response3 is not None
        assert response3.hex().upper() == "62F1901020011223344556677889AABB"

        # Check cycling state
        cycling_state = server.get_response_cycling_state()
        assert cycling_state[key] == 1  # Next response should be index 1 again

    def test_response_cycling_different_ecus(self):
        """Test that different ECUs have independent cycling states"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        request_bytes = bytes.fromhex("22F190")

        # Test Engine ECU
        response_engine = server.process_uds_message(request_bytes, 0x1000)
        assert response_engine is not None

        # Test Transmission ECU
        response_transmission = server.process_uds_message(request_bytes, 0x1001)
        assert response_transmission is not None

        # Test ABS ECU
        response_abs = server.process_uds_message(request_bytes, 0x1002)
        assert response_abs is not None

        # All should return the first response (index 0) since they're independent
        expected_response = "62F1901020011223344556677889AABB"
        assert response_engine.hex().upper() == expected_response
        assert response_transmission.hex().upper() == expected_response
        assert response_abs.hex().upper() == expected_response

        # Check that all have independent cycling states
        cycling_state = server.get_response_cycling_state()
        assert "ECU_0x1000_Read_VIN" in cycling_state
        assert "ECU_0x1001_Read_VIN" in cycling_state
        assert "ECU_0x1002_Read_VIN" in cycling_state

        # All should be at index 1 (next response)
        assert cycling_state["ECU_0x1000_Read_VIN"] == 1
        assert cycling_state["ECU_0x1001_Read_VIN"] == 1
        assert cycling_state["ECU_0x1002_Read_VIN"] == 1

    def test_response_cycling_different_services(self):
        """Test that different services have independent cycling states"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")
        target_address = 0x1000  # Engine ECU

        # Test Read_VIN service
        vin_request = bytes.fromhex("22F190")
        vin_response1 = server.process_uds_message(vin_request, target_address)
        assert vin_response1 is not None

        # Test Engine_RPM_Read service
        rpm_request = bytes.fromhex("220C01")
        rpm_response1 = server.process_uds_message(rpm_request, target_address)
        assert rpm_response1 is not None

        # Both should return first response
        assert vin_response1.hex().upper() == "62F1901020011223344556677889AABB"
        assert rpm_response1.hex().upper() == "620C018000"

        # Check that both services have independent cycling states
        cycling_state = server.get_response_cycling_state()
        assert "ECU_0x1000_Read_VIN" in cycling_state
        assert "ECU_0x1000_Engine_RPM_Read" in cycling_state

        # Both should be at index 1 (next response)
        assert cycling_state["ECU_0x1000_Read_VIN"] == 1
        assert cycling_state["ECU_0x1000_Engine_RPM_Read"] == 1

    def test_response_cycling_with_three_responses(self):
        """Test response cycling with a service that has 3 responses"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Test Transmission_Gear_Read service (has 3 responses)
        request_bytes = bytes.fromhex("220C0A")
        target_address = 0x1001  # Transmission ECU

        # First call - should return first response
        response1 = server.process_uds_message(request_bytes, target_address)
        assert response1 is not None
        assert response1.hex().upper() == "620C0A01"

        # Second call - should return second response
        response2 = server.process_uds_message(request_bytes, target_address)
        assert response2 is not None
        assert response2.hex().upper() == "620C0A02"

        # Third call - should return third response
        response3 = server.process_uds_message(request_bytes, target_address)
        assert response3 is not None
        assert response3.hex().upper() == "620C0A03"

        # Fourth call - should cycle back to first response
        response4 = server.process_uds_message(request_bytes, target_address)
        assert response4 is not None
        assert response4.hex().upper() == "620C0A01"

        # Check cycling state
        cycling_state = server.get_response_cycling_state()
        key = "ECU_0x1001_Transmission_Gear_Read"
        assert key in cycling_state
        assert cycling_state[key] == 1  # Next response should be index 1

    def test_response_cycling_reset_functionality(self):
        """Test response cycling reset functionality"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        request_bytes = bytes.fromhex("22F190")
        target_address = 0x1000

        # Make a few calls to advance the cycling state
        server.process_uds_message(request_bytes, target_address)
        server.process_uds_message(request_bytes, target_address)

        # Check that cycling state is advanced
        cycling_state = server.get_response_cycling_state()
        key = "ECU_0x1000_Read_VIN"
        assert key in cycling_state
        assert cycling_state[key] == 0  # Should be back to index 0 after cycling

        # Reset the cycling state
        server.reset_response_cycling(target_address, "Read_VIN")

        # Check that cycling state is reset
        cycling_state = server.get_response_cycling_state()
        assert key not in cycling_state  # Should be removed

        # Next call should start from first response again
        response = server.process_uds_message(request_bytes, target_address)
        assert response is not None
        assert response.hex().upper() == "62F1901020011223344556677889AABB"

        # Check that cycling state is recreated
        cycling_state = server.get_response_cycling_state()
        assert key in cycling_state
        assert cycling_state[key] == 1  # Next response should be index 1

    def test_response_cycling_reset_all(self):
        """Test resetting all response cycling states"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Make some calls to create cycling states
        server.process_uds_message(bytes.fromhex("22F190"), 0x1000)
        server.process_uds_message(bytes.fromhex("220C01"), 0x1000)
        server.process_uds_message(bytes.fromhex("22F190"), 0x1001)

        # Check that cycling states exist
        cycling_state = server.get_response_cycling_state()
        assert len(cycling_state) > 0

        # Reset all cycling states
        server.reset_response_cycling()

        # Check that all cycling states are cleared
        cycling_state = server.get_response_cycling_state()
        assert len(cycling_state) == 0

    def test_response_cycling_hierarchical_config(self):
        """Test response cycling with hierarchical configuration"""
        server = DoIPServer(
            gateway_config_path="config/gateway1.yaml"
        )  # Use hierarchical config

        # Test Read_VIN service for Engine ECU (0x1000)
        request_bytes = bytes.fromhex("22F190")

        # First call - should return first response
        response1 = server.process_uds_message(request_bytes, 0x1000)
        assert response1 is not None
        assert response1.hex().upper() == "62F1901020011223344556677889AABB"

        # Second call - should return second response
        response2 = server.process_uds_message(request_bytes, 0x1000)
        assert response2 is not None
        assert response2.hex().upper() == "62F1901020011223344556677889BBCC"

        # Third call - should cycle back to first response
        response3 = server.process_uds_message(request_bytes, 0x1000)
        assert response3 is not None
        assert response3.hex().upper() == "62F1901020011223344556677889AABB"

        # Check cycling state (hierarchical uses actual ECU address)
        cycling_state = server.get_response_cycling_state()
        key = "ECU_0x1000_Read_VIN"
        assert key in cycling_state
        assert cycling_state[key] == 1  # Next response should be index 1

    def test_response_cycling_single_response(self):
        """Test response cycling with a service that has only one response"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Test Routine_calibration_start service (has 1 response)
        request_bytes = bytes.fromhex("31010202")
        target_address = 0x1000

        # Multiple calls should return the same response
        response1 = server.process_uds_message(request_bytes, target_address)
        response2 = server.process_uds_message(request_bytes, target_address)
        response3 = server.process_uds_message(request_bytes, target_address)

        assert response1 is not None
        assert response2 is not None
        assert response3 is not None

        # All responses should be the same
        expected_response = "71010202"
        assert response1.hex().upper() == expected_response
        assert response2.hex().upper() == expected_response
        assert response3.hex().upper() == expected_response

        # Check cycling state (should cycle between 0 and 0)
        cycling_state = server.get_response_cycling_state()
        key = "ECU_0x1000_Routine_calibration_start"
        assert key in cycling_state
        assert cycling_state[key] == 0  # Should stay at index 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
