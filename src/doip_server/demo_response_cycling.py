#!/usr/bin/env python3
"""
Demo script for response cycling functionality
Shows how the server cycles through different responses for the same UDS service
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.doip_server.doip_server import DoIPServer
from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager

def demo_response_cycling():
    """Demonstrate response cycling functionality"""
    print("=== Response Cycling Demo ===\n")
    
    # Load configuration
    print("1. Loading hierarchical configuration...")
    config_manager = HierarchicalConfigManager("config/gateway1.yaml")
    
    # Show available services with multiple responses
    print("\n2. Services with multiple responses:")
    for target_addr in config_manager.get_all_ecu_addresses():
        ecu_config = config_manager.get_ecu_config(target_addr)
        ecu_info = ecu_config.get('ecu', {}) if ecu_config else {}
        print(f"\n   ECU 0x{target_addr:04X} ({ecu_info.get('name', 'Unknown')}):")
        
        uds_services = config_manager.get_ecu_uds_services(target_addr)
        for service_name, service_config in uds_services.items():
            responses = service_config.get('responses', [])
            if len(responses) > 1:
                print(f"     - {service_name}: {len(responses)} responses")
                for i, response in enumerate(responses):
                    print(f"       {i+1}. {response}")
    
    # Create server
    print("\n3. Creating DoIP server...")
    server = DoIPServer('127.0.0.1', 13402, gateway_config_path="config/gateway1.yaml")
    
    # Start server in background
    print("4. Starting server...")
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # Wait for server to start
    
    print("5. Testing response cycling...")
    
    # Test response cycling for different services
    test_services = [
        ("0x22F190", 0x1000, "Read_VIN", "Engine ECU"),
        ("0x22F190", 0x1001, "Read_VIN", "Transmission ECU"),
        ("0x22F190", 0x1002, "Read_VIN", "ABS ECU"),
        ("0x220C01", 0x1000, "Engine_RPM_Read", "Engine ECU"),
        ("0x220C0A", 0x1001, "Transmission_Gear_Read", "Transmission ECU"),
        ("0x220C0B", 0x1002, "ABS_Wheel_Speed_Read", "ABS ECU")
    ]
    
    for request_hex, target_addr, service_name, ecu_desc in test_services:
        print(f"\n   Testing {service_name} for {ecu_desc} (0x{target_addr:04X}):")
        
        # Convert hex string to bytes (remove 0x prefix if present)
        clean_hex = request_hex[2:] if request_hex.startswith('0x') else request_hex
        request_bytes = bytes.fromhex(clean_hex)
        
        # Test multiple calls to see cycling
        for call_num in range(1, 4):  # Test 3 calls
            print(f"     Call {call_num}:")
            
            # Simulate UDS message processing
            uds_response = server.process_uds_message(request_bytes, target_addr)
            
            if uds_response:
                response_hex = uds_response.hex().upper()
                print(f"       Request: {request_hex}")
                print(f"       Response: {response_hex}")
            else:
                print(f"       Request: {request_hex}")
                print(f"       Response: None (service not found)")
            
            # Show current cycling state
            cycling_state = server.get_response_cycling_state()
            key = f"ECU_0x{target_addr:04X}_{service_name}"
            if key in cycling_state:
                print(f"       Next response index: {cycling_state[key]}")
    
    # Show final cycling state
    print("\n6. Final response cycling state:")
    cycling_state = server.get_response_cycling_state()
    if cycling_state:
        for key, index in cycling_state.items():
            print(f"   {key}: next index {index}")
    else:
        print("   No cycling state recorded")
    
    # Test reset functionality
    print("\n7. Testing reset functionality...")
    print("   Resetting Engine ECU Read_VIN cycling...")
    server.reset_response_cycling(0x1000, "Read_VIN")
    
    # Test the same service again to see it starts from index 0
    print("   Testing Engine ECU Read_VIN after reset:")
    request_bytes = bytes.fromhex("22F190")
    uds_response = server.process_uds_message(request_bytes, 0x1000)
    if uds_response:
        response_hex = uds_response.hex().upper()
        print(f"     Request: 0x22F190")
        print(f"     Response: {response_hex}")
    
    # Show updated cycling state
    cycling_state = server.get_response_cycling_state()
    key = "ECU_0x1000_Read_VIN"
    if key in cycling_state:
        print(f"     Next response index: {cycling_state[key]}")
    
    # Stop server
    print("\n8. Stopping server...")
    server.stop()
    time.sleep(1)
    
    print("\n=== Demo Complete ===")

def demo_legacy_response_cycling():
    """Demonstrate response cycling with legacy configuration"""
    print("\n=== Legacy Response Cycling Demo ===\n")
    
    # Create server with legacy configuration
    print("1. Creating DoIP server with legacy configuration...")
    server = DoIPServer('127.0.0.1', 13403, gateway_config_path=None)
    
    # Start server in background
    print("2. Starting server...")
    server_thread = threading.Thread(target=server.start)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # Wait for server to start
    
    print("3. Testing response cycling with legacy configuration...")
    
    # Test Read_VIN service multiple times
    print("   Testing Read_VIN service (legacy):")
    request_bytes = bytes.fromhex("22F190")  # Read VIN request
    
    for call_num in range(1, 4):  # Test 3 calls
        print(f"     Call {call_num}:")
        
        # Simulate UDS message processing (legacy mode uses target_address=None)
        uds_response = server.process_uds_message(request_bytes, None)
        
        if uds_response:
            response_hex = uds_response.hex().upper()
            print(f"       Request: 22F190")
            print(f"       Response: {response_hex}")
        else:
            print(f"       Request: 22F190")
            print(f"       Response: None (service not found)")
        
        # Show current cycling state
        cycling_state = server.get_response_cycling_state()
        key = "ECU_0x0_Read_VIN"  # Legacy uses 0 as ECU address
        if key in cycling_state:
            print(f"       Next response index: {cycling_state[key]}")
    
    # Stop server
    print("\n4. Stopping server...")
    server.stop()
    time.sleep(1)
    
    print("\n=== Legacy Demo Complete ===")

if __name__ == "__main__":
    try:
        demo_response_cycling()
        demo_legacy_response_cycling()
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
