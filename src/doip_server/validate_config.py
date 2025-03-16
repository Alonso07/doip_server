#!/usr/bin/env python3
"""
Configuration validation script for DoIP server
Validates the YAML configuration file and reports any issues
"""

import sys
import os
from pathlib import Path

from .config_manager import DoIPConfigManager

def validate_configuration(config_path=None):
    """Validate the DoIP configuration file"""
    print("DoIP Configuration Validation")
    print("=" * 40)
    
    try:
        # Initialize configuration manager
        config_manager = DoIPConfigManager(config_path)
        
        # Print configuration summary
        print("\nConfiguration Summary:")
        print(config_manager.get_config_summary())
        
        # Validate configuration
        print("\nValidating configuration...")
        if config_manager.validate_config():
            print("✅ Configuration validation passed!")
        else:
            print("❌ Configuration validation failed!")
            return False
        
        # Test specific configurations
        print("\nTesting specific configurations...")
        
        # Test routine activation
        routines = config_manager.get_routine_activation_config()
        supported_routines = routines.get('supported_routines', {})
        print(f"✅ Found {len(supported_routines)} supported routines")
        
        for routine_id, routine_config in supported_routines.items():
            print(f"  - 0x{routine_id:04X}: {routine_config.get('name', 'Unknown')}")
        
        # Test UDS services
        uds_services = config_manager.get_uds_services_config()
        print(f"✅ Found {len(uds_services)} UDS services")
        
        for service_id, service_config in uds_services.items():
            print(f"  - 0x{service_id:02X}: {service_config.get('name', 'Unknown')}")
            data_ids = service_config.get('supported_data_identifiers', {})
            print(f"    Supports {len(data_ids)} data identifiers")
        
        # Test addresses
        addresses = config_manager.get_addresses_config()
        target_addrs = addresses.get('target_addresses', [])
        allowed_sources = addresses.get('allowed_sources', [])
        
        print(f"✅ Target addresses: {len(target_addrs)}")
        for addr in target_addrs:
            print(f"  - 0x{addr:04X}")
        
        print(f"✅ Allowed source addresses: {len(allowed_sources)}")
        for addr in allowed_sources:
            print(f"  - 0x{addr:04X}")
        
        # Test response codes
        response_codes = config_manager.get_response_codes_config()
        routine_codes = response_codes.get('routine_activation', {})
        uds_codes = response_codes.get('uds', {})
        
        print(f"✅ Routine activation response codes: {len(routine_codes)}")
        print(f"✅ UDS response codes: {len(uds_codes)}")
        
        print("\n🎉 Configuration validation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed with error: {e}")
        return False

def main():
    """Main function"""
    config_path = None
    
    # Check if config path is provided as command line argument
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    success = validate_configuration(config_path)
    
    if success:
        print("\nThe configuration file is valid and ready to use!")
        sys.exit(0)
    else:
        print("\nThe configuration file has issues that need to be fixed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
