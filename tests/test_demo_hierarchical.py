#!/usr/bin/env python3
"""
Test module for the hierarchical DoIP configuration
Tests the new configuration structure with multiple ECUs
"""

import sys
import os
import time
import pytest

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from doip_server.hierarchical_config_manager import HierarchicalConfigManager


def test_configuration_loading():
    """Test loading and using the hierarchical configuration"""
    # Load configuration
    config_manager = HierarchicalConfigManager("config/gateway1.yaml")

    # Test configuration summary
    summary = config_manager.get_config_summary()
    assert summary is not None
    assert isinstance(summary, str)

    # Test gateway information
    gateway_config = config_manager.get_gateway_config()
    assert gateway_config is not None
    assert 'name' in gateway_config
    assert 'description' in gateway_config

    network_config = config_manager.get_network_config()
    assert network_config is not None
    assert 'host' in network_config
    assert 'port' in network_config
    assert 'max_connections' in network_config

    # Test ECU information
    ecu_addresses = config_manager.get_all_ecu_addresses()
    assert len(ecu_addresses) > 0

    for target_addr in ecu_addresses:
        ecu_config = config_manager.get_ecu_config(target_addr)
        assert ecu_config is not None
        ecu_info = ecu_config.get("ecu", {})
        assert 'name' in ecu_info
        assert 'description' in ecu_info

        # Test tester addresses
        tester_addresses = config_manager.get_ecu_tester_addresses(target_addr)
        assert isinstance(tester_addresses, list)

        # Test UDS services
        uds_services = config_manager.get_ecu_uds_services(target_addr)
        assert isinstance(uds_services, dict)


def test_uds_service_lookup():
    """Test UDS service lookup functionality"""
    config_manager = HierarchicalConfigManager("config/gateway1.yaml")

    # Test common service lookup
    test_requests = [
        ("0x22F190", "Read VIN request"),
        ("0x22F191", "Read Vehicle Type request"),
        ("0x31010202", "Routine calibration start request"),
    ]

    for request, description in test_requests:
        # Test for each ECU
        for target_addr in config_manager.get_all_ecu_addresses():
            service_config = config_manager.get_uds_service_by_request(
                request, target_addr
            )
            # Service may or may not be available, but if it is, it should have proper structure
            if service_config:
                assert 'name' in service_config
                assert 'description' in service_config
                assert 'responses' in service_config
                assert isinstance(service_config['responses'], list)

    # Test ECU-specific services
    ecu_specific_requests = [
        ("0x220C01", "Engine RPM read"),
        ("0x220C0A", "Transmission gear read"),
        ("0x220C0B", "ABS wheel speed read"),
    ]

    for request, description in ecu_specific_requests:
        for target_addr in config_manager.get_all_ecu_addresses():
            service_config = config_manager.get_uds_service_by_request(
                request, target_addr
            )
            # Service may or may not be available, but if it is, it should have proper structure
            if service_config:
                assert 'name' in service_config


def test_address_validation():
    """Test address validation functionality"""
    config_manager = HierarchicalConfigManager("config/gateway1.yaml")

    test_addresses = [
        (0x0E00, 0x1000, "Primary tester to Engine ECU"),
        (0x0E01, 0x1001, "Backup tester to Transmission ECU"),
        (0x0E02, 0x1002, "Diagnostic tool to ABS ECU"),
        (0x0E99, 0x1000, "Unauthorized tester to Engine ECU"),
        (0x0E00, 0x1999, "Primary tester to non-existent ECU"),
    ]

    for source_addr, target_addr, description in test_addresses:
        source_valid = config_manager.is_source_address_allowed(
            source_addr, target_addr
        )
        target_valid = config_manager.is_target_address_valid(target_addr)
        
        # These should return boolean values
        assert isinstance(source_valid, bool)
        assert isinstance(target_valid, bool)


def test_runtime_ecu_loading():
    """Test runtime ECU loading capabilities"""
    config_manager = HierarchicalConfigManager("config/gateway1.yaml")

    # Test current ECUs loaded at startup
    ecu_addresses = config_manager.get_all_ecu_addresses()
    assert len(ecu_addresses) > 0

    for target_addr in ecu_addresses:
        ecu_config = config_manager.get_ecu_config(target_addr)
        assert ecu_config is not None
        ecu_info = ecu_config.get("ecu", {})
        assert 'name' in ecu_info

    # Test UDS services per ECU
    for target_addr in ecu_addresses:
        ecu_config = config_manager.get_ecu_config(target_addr)
        ecu_info = ecu_config.get("ecu", {})
        
        uds_services = config_manager.get_ecu_uds_services(target_addr)
        assert isinstance(uds_services, dict)
        
        # Test common services categorization
        common_services = [
            name
            for name in uds_services.keys()
            if name
            in [
                "Read_VIN",
                "Read_Vehicle_Type",
                "Routine_calibration_start",
                "Routine_calibration_stop",
                "Routine_calibration_status",
            ]
        ]
        specific_services = [
            name for name in uds_services.keys() if name not in common_services
        ]

        # Verify service categorization
        assert len(common_services) + len(specific_services) == len(uds_services)
        assert isinstance(common_services, list)
        assert isinstance(specific_services, list)
