#!/usr/bin/env python3
"""
Demo script for the hierarchical DoIP configuration
Shows how to use the new configuration structure with multiple ECUs
"""

import sys
import os
import time

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager

def demo_configuration_loading():
    """Demonstrate loading and using the hierarchical configuration"""
    print("=== Hierarchical DoIP Configuration Demo ===\n")
    
    # Load configuration
    print("1. Loading hierarchical configuration...")
    config_manager = HierarchicalConfigManager("config/gateway1.yaml")
    
    # Display configuration summary
    print("\n2. Configuration Summary:")
    print(config_manager.get_config_summary())
    
    # Show gateway information
    print("\n3. Gateway Information:")
    gateway_config = config_manager.get_gateway_config()
    print(f"   Name: {gateway_config.get('name', 'Unknown')}")
    print(f"   Description: {gateway_config.get('description', 'Unknown')}")
    
    network_config = config_manager.get_network_config()
    print(f"   Network: {network_config.get('host')}:{network_config.get('port')}")
    print(f"   Max Connections: {network_config.get('max_connections')}")
    
    # Show ECU information
    print("\n4. ECU Information:")
    for target_addr in config_manager.get_all_ecu_addresses():
        ecu_config = config_manager.get_ecu_config(target_addr)
        ecu_info = ecu_config.get('ecu', {}) if ecu_config else {}
        print(f"   ECU 0x{target_addr:04X}: {ecu_info.get('name', 'Unknown')}")
        print(f"     Description: {ecu_info.get('description', 'Unknown')}")
        print(f"     Tester Addresses: {[f'0x{addr:04X}' for addr in config_manager.get_ecu_tester_addresses(target_addr)]}")
        
        # Show available UDS services for this ECU
        uds_services = config_manager.get_ecu_uds_services(target_addr)
        print(f"     Available UDS Services: {len(uds_services)}")
        for service_name in uds_services.keys():
            print(f"       - {service_name}")
    
    # Demonstrate UDS service lookup
    print("\n5. UDS Service Lookup Demo:")
    
    # Test common service lookup
    test_requests = [
        ("0x22F190", "Read VIN request"),
        ("0x22F191", "Read Vehicle Type request"),
        ("0x31010202", "Routine calibration start request")
    ]
    
    for request, description in test_requests:
        print(f"\n   Testing {description} ({request}):")
        
        # Test for each ECU
        for target_addr in config_manager.get_all_ecu_addresses():
            service_config = config_manager.get_uds_service_by_request(request, target_addr)
            if service_config:
                print(f"     ECU 0x{target_addr:04X}: ✓ {service_config['name']}")
                print(f"       Description: {service_config.get('description', 'N/A')}")
                print(f"       Responses: {len(service_config.get('responses', []))}")
            else:
                print(f"     ECU 0x{target_addr:04X}: ✗ Not available")
    
    # Test ECU-specific services
    print("\n6. ECU-Specific Service Demo:")
    ecu_specific_requests = [
        ("0x220C01", "Engine RPM read"),
        ("0x220C0A", "Transmission gear read"),
        ("0x220C0B", "ABS wheel speed read")
    ]
    
    for request, description in ecu_specific_requests:
        print(f"\n   Testing {description} ({request}):")
        for target_addr in config_manager.get_all_ecu_addresses():
            service_config = config_manager.get_uds_service_by_request(request, target_addr)
            if service_config:
                print(f"     ECU 0x{target_addr:04X}: ✓ {service_config['name']}")
            else:
                print(f"     ECU 0x{target_addr:04X}: ✗ Not available")
    
    # Demonstrate address validation
    print("\n7. Address Validation Demo:")
    test_addresses = [
        (0x0E00, 0x1000, "Primary tester to Engine ECU"),
        (0x0E01, 0x1001, "Backup tester to Transmission ECU"),
        (0x0E02, 0x1002, "Diagnostic tool to ABS ECU"),
        (0x0E99, 0x1000, "Unauthorized tester to Engine ECU"),
        (0x0E00, 0x1999, "Primary tester to non-existent ECU")
    ]
    
    for source_addr, target_addr, description in test_addresses:
        source_valid = config_manager.is_source_address_allowed(source_addr, target_addr)
        target_valid = config_manager.is_target_address_valid(target_addr)
        print(f"   {description}:")
        print(f"     Source 0x{source_addr:04X} allowed: {'✓' if source_valid else '✗'}")
        print(f"     Target 0x{target_addr:04X} valid: {'✓' if target_valid else '✗'}")
        print(f"     Overall: {'✓' if source_valid and target_valid else '✗'}")
    
    print("\n=== Demo Complete ===")

def demo_runtime_ecu_loading():
    """Demonstrate runtime ECU loading capabilities"""
    print("\n=== Runtime ECU Loading Demo ===\n")
    
    config_manager = HierarchicalConfigManager("config/gateway1.yaml")
    
    print("1. Current ECUs loaded at startup:")
    for target_addr in config_manager.get_all_ecu_addresses():
        ecu_config = config_manager.get_ecu_config(target_addr)
        ecu_info = ecu_config.get('ecu', {}) if ecu_config else {}
        print(f"   - 0x{target_addr:04X}: {ecu_info.get('name', 'Unknown')}")
    
    print("\n2. Simulating dynamic ECU addition...")
    print("   (In a real implementation, this would load new ECU configs at runtime)")
    
    # Show how the system would handle new ECUs
    print("\n3. Available UDS services per ECU:")
    for target_addr in config_manager.get_all_ecu_addresses():
        ecu_config = config_manager.get_ecu_config(target_addr)
        ecu_info = ecu_config.get('ecu', {}) if ecu_config else {}
        print(f"\n   ECU 0x{target_addr:04X} ({ecu_info.get('name', 'Unknown')}):")
        
        uds_services = config_manager.get_ecu_uds_services(target_addr)
        common_services = [name for name in uds_services.keys() if name in ['Read_VIN', 'Read_Vehicle_Type', 'Routine_calibration_start', 'Routine_calibration_stop', 'Routine_calibration_status']]
        specific_services = [name for name in uds_services.keys() if name not in common_services]
        
        print(f"     Common services ({len(common_services)}): {', '.join(common_services)}")
        print(f"     Specific services ({len(specific_services)}): {', '.join(specific_services)}")

if __name__ == "__main__":
    try:
        demo_configuration_loading()
        demo_runtime_ecu_loading()
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
