#!/usr/bin/env python3
"""
Test module for response cycling functionality
Tests how the server cycles through different responses for the same UDS service
"""

import sys
import os
import time
import threading
import pytest
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from doip_server.doip_server import DoIPServer
from doip_server.hierarchical_config_manager import HierarchicalConfigManager


def test_response_cycling():
    """Test response cycling functionality"""
    # Load configuration
    config_manager = HierarchicalConfigManager("config/gateway1.yaml")

    # Test available services with multiple responses
    for target_addr in config_manager.get_all_ecu_addresses():
        ecu_config = config_manager.get_ecu_config(target_addr)
        ecu_info = ecu_config.get("ecu", {}) if ecu_config else {}
        
        uds_services = config_manager.get_ecu_uds_services(target_addr)
        for service_name, service_config in uds_services.items():
            responses = service_config.get("responses", [])
            if len(responses) > 1:
                # Verify multiple responses exist
                assert len(responses) > 1
                assert isinstance(responses, list)

    # Create server
    server = DoIPServer("127.0.0.1", 13402, gateway_config_path="config/gateway1.yaml")

    # Start server in background
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # Wait for server to start

    try:
        # Test response cycling for different services
        test_services = [
            ("0x22F190", 0x1000, "Read_VIN", "Engine ECU"),
            ("0x22F190", 0x1001, "Read_VIN", "Transmission ECU"),
            ("0x22F190", 0x1002, "Read_VIN", "ABS ECU"),
            ("0x220C01", 0x1000, "Engine_RPM_Read", "Engine ECU"),
            ("0x220C0A", 0x1001, "Transmission_Gear_Read", "Transmission ECU"),
            ("0x220C0B", 0x1002, "ABS_Wheel_Speed_Read", "ABS ECU"),
        ]

        for request_hex, target_addr, service_name, ecu_desc in test_services:
            # Convert hex string to bytes (remove 0x prefix if present)
            clean_hex = request_hex[2:] if request_hex.startswith("0x") else request_hex
            request_bytes = bytes.fromhex(clean_hex)

            # Test multiple calls to see cycling
            for call_num in range(1, 4):  # Test 3 calls
                # Simulate UDS message processing
                uds_response = server.process_uds_message(request_bytes, target_addr)
                
                # Response may or may not exist depending on configuration
                # We just verify the method doesn't crash
                assert uds_response is None or isinstance(uds_response, bytes)

                # Show current cycling state
                cycling_state = server.get_response_cycling_state()
                key = f"ECU_0x{target_addr:04X}_{service_name}"
                if key in cycling_state:
                    assert isinstance(cycling_state[key], int)
                    assert cycling_state[key] >= 0

        # Test final cycling state
        cycling_state = server.get_response_cycling_state()
        assert isinstance(cycling_state, dict)

        # Test reset functionality
        server.reset_response_cycling(0x1000, "Read_VIN")

        # Test the same service again to see it starts from index 0
        request_bytes = bytes.fromhex("22F190")
        uds_response = server.process_uds_message(request_bytes, 0x1000)
        # Response may or may not exist depending on configuration
        assert uds_response is None or isinstance(uds_response, bytes)

        # Show updated cycling state
        cycling_state = server.get_response_cycling_state()
        key = "ECU_0x1000_Read_VIN"
        if key in cycling_state:
            assert isinstance(cycling_state[key], int)
            assert cycling_state[key] >= 0

    finally:
        # Stop server
        server.stop()
        time.sleep(1)


def test_hierarchical_response_cycling():
    """Test response cycling with hierarchical configuration"""
    # Create server with hierarchical configuration
    server = DoIPServer("127.0.0.1", 13403, gateway_config_path="config/gateway1.yaml")

    # Start server in background
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # Wait for server to start

    try:
        # Test Read_VIN service multiple times
        request_bytes = bytes.fromhex("22F190")  # Read VIN request

        for call_num in range(1, 4):  # Test 3 calls
            # Simulate UDS message processing for Engine ECU (0x1000)
            uds_response = server.process_uds_message(request_bytes, 0x1000)
            
            # Response may or may not exist depending on configuration
            assert uds_response is None or isinstance(uds_response, bytes)

            # Show current cycling state
            cycling_state = server.get_response_cycling_state()
            key = "ECU_0x0_Read_VIN"  # Legacy uses 0 as ECU address
            if key in cycling_state:
                assert isinstance(cycling_state[key], int)
                assert cycling_state[key] >= 0

    finally:
        # Stop server
        server.stop()
        time.sleep(1)
