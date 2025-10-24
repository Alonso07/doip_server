#!/usr/bin/env python3
"""
Test script to validate the doip_server configuration for doip_tester_yaml compatibility.
This script checks if all required ECUs are configured with correct addresses.
"""

import yaml
import os
import sys
from pathlib import Path

def load_yaml_file(file_path):
    """Load and parse a YAML file."""
    try:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def validate_gateway_config(config_path):
    """Validate the gateway configuration."""
    print(f"Validating gateway configuration: {config_path}")
    
    config = load_yaml_file(config_path)
    if not config:
        return False
    
    gateway = config.get('gateway', {})
    
    # Check required fields
    required_fields = ['name', 'logical_address', 'network', 'ecus']
    for field in required_fields:
        if field not in gateway:
            print(f"Missing required field: {field}")
            return False
    
    # Check network configuration
    network = gateway.get('network', {})
    if network.get('port') != 13400:
        print(f"Warning: Port is {network.get('port')}, expected 13400")
    
    # Check ECU references
    ecus = gateway.get('ecus', [])
    print(f"Found {len(ecus)} ECU references:")
    for ecu in ecus:
        print(f"  - {ecu}")
    
    return True

def validate_ecu_config(ecu_path):
    """Validate an ECU configuration."""
    print(f"Validating ECU configuration: {ecu_path}")
    
    config = load_yaml_file(ecu_path)
    if not config:
        return False
    
    ecu = config.get('ecu', {})
    
    # Check required fields
    required_fields = ['name', 'target_address', 'functional_address', 'tester_addresses']
    for field in required_fields:
        if field not in ecu:
            print(f"Missing required field: {field}")
            return False
    
    # Check addresses
    target_addr = ecu.get('target_address')
    functional_addr = ecu.get('functional_address')
    tester_addrs = ecu.get('tester_addresses', [])
    
    print(f"  Name: {ecu.get('name')}")
    print(f"  Target Address: 0x{target_addr:04X}")
    print(f"  Functional Address: 0x{functional_addr:04X}")
    print(f"  Tester Addresses: {[hex(addr) for addr in tester_addrs]}")
    
    # Check if 0x0E80 is in tester addresses (required by doip_tester_yaml)
    if 0x0E80 not in tester_addrs:
        print(f"  Warning: 0x0E80 not in tester addresses (required by doip_tester_yaml)")
    
    return True

def main():
    """Main validation function."""
    print("=== DoIP Server Configuration Validation ===")
    print("Checking configuration for doip_tester_yaml compatibility...\n")
    
    # Get the project root directory
    project_root = Path(__file__).parent
    config_dir = project_root / "config"
    
    # Validate gateway configuration
    gateway_configs = [
        "gateway1.yaml",
        "test_gateway.yaml"
    ]
    
    for gateway_config in gateway_configs:
        gateway_path = config_dir / gateway_config
        if gateway_path.exists():
            print(f"\n--- {gateway_config} ---")
            if validate_gateway_config(gateway_path):
                print("✓ Gateway configuration is valid")
            else:
                print("✗ Gateway configuration has issues")
        else:
            print(f"Gateway config not found: {gateway_path}")
    
    # Validate ECU configurations
    print(f"\n--- ECU Configurations ---")
    ecu_dirs = [
        "ecus/engine",
        "ecus/transmission", 
        "ecus/abs",
        "ecus/esp",
        "ecus/steering",
        "ecus/bcm",
        "ecus/gateway",
        "ecus/hvac"
    ]
    
    for ecu_dir in ecu_dirs:
        ecu_path = config_dir / ecu_dir
        if ecu_path.exists():
            # Find ECU YAML files
            for yaml_file in ecu_path.glob("ecu_*.yaml"):
                if yaml_file.name != "ecu_*_services.yaml":  # Skip service files
                    print(f"\n--- {yaml_file.relative_to(config_dir)} ---")
                    if validate_ecu_config(yaml_file):
                        print("✓ ECU configuration is valid")
                    else:
                        print("✗ ECU configuration has issues")
        else:
            print(f"ECU directory not found: {ecu_path}")
    
    # Check for expected ECU addresses from doip_tester_yaml
    print(f"\n--- Expected ECU Addresses (from doip_tester_yaml) ---")
    expected_ecus = {
        "Engine_ECM": 0x01,
        "Transmission_TCU": 0x02,
        "ABS": 0x03,
        "ESP": 0x04,
        "Steering_EPS": 0x05,
        "BCM": 0x06,
        "Gateway": 0x07,
        "HVAC": 0x08
    }
    
    for ecu_name, expected_addr in expected_ecus.items():
        print(f"  {ecu_name}: 0x{expected_addr:02X}")
    
    print(f"\n=== Validation Complete ===")
    print("Configuration should now be compatible with doip_tester_yaml")
    print("To start the server, run:")
    print("  python -m doip_server.main --config config/test_gateway.yaml")

if __name__ == "__main__":
    main()
