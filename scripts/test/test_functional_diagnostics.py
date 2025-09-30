#!/usr/bin/env python3
"""
Test script for functional diagnostics feature.
This script demonstrates how to use functional addressing to send requests
to multiple ECUs simultaneously.
"""

import time
import sys
import os

# Add the src directory to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(project_root, "src"))

from doip_client.doip_client import DoIPClientWrapper


def test_functional_diagnostics():
    """Test functional diagnostics functionality"""
    print("=== Functional Diagnostics Test ===")
    print("This test demonstrates functional addressing where a single request")
    print("is broadcast to multiple ECUs that support the service.")
    print()

    # Create client
    client = DoIPClientWrapper(
        server_host="127.0.0.1",
        server_port=13400,
        logical_address=0x0E00,
        target_address=0x1000,  # This will be overridden for functional addressing
    )

    try:
        # Connect to server
        print("Connecting to DoIP server...")
        client.connect()
        time.sleep(1)

        # Test 1: Functional Diagnostic Session Control
        print("\n--- Test 1: Functional Diagnostic Session Control ---")
        response = client.send_functional_diagnostic_session_control(0x03)
        if response:
            print(f"✓ Functional session control successful: {response.hex()}")
        else:
            print("✗ Functional session control failed")
        time.sleep(1)

        # Test 2: Functional Read VIN (should be supported by all ECUs)
        print("\n--- Test 2: Functional Read VIN ---")
        response = client.send_functional_read_data_by_identifier(0xF190)
        if response:
            print(f"✓ Functional VIN read successful: {response.hex()}")
        else:
            print("✗ Functional VIN read failed")
        time.sleep(1)

        # Test 3: Functional Read Vehicle Type (should be supported by all ECUs)
        print("\n--- Test 3: Functional Read Vehicle Type ---")
        response = client.send_functional_read_data_by_identifier(0xF191)
        if response:
            print(f"✓ Functional vehicle type read successful: {response.hex()}")
        else:
            print("✗ Functional vehicle type read failed")
        time.sleep(1)

        # Test 4: Functional Tester Present
        print("\n--- Test 4: Functional Tester Present ---")
        response = client.send_functional_tester_present()
        if response:
            print(f"✓ Functional tester present successful: {response.hex()}")
        else:
            print("✗ Functional tester present failed")
        time.sleep(1)

        # Test 5: Compare with physical addressing
        print("\n--- Test 5: Comparison with Physical Addressing ---")
        print("Sending same request to physical address (Engine ECU only)...")
        response = client.send_read_data_by_identifier(0xF190)
        if response:
            print(f"✓ Physical VIN read successful: {response.hex()}")
        else:
            print("✗ Physical VIN read failed")
        time.sleep(1)

        print("\n=== Functional Diagnostics Test Complete ===")
        print(
            "Note: Check server logs to see which ECUs responded to functional requests."
        )

    except Exception as e:
        print(f"Error during functional diagnostics test: {e}")
    finally:
        client.disconnect()


def test_physical_vs_functional():
    """Compare physical vs functional addressing"""
    print("\n=== Physical vs Functional Addressing Comparison ===")

    client = DoIPClientWrapper(
        server_host="127.0.0.1",
        server_port=13400,
        logical_address=0x0E00,
        target_address=0x1000,
    )

    try:
        client.connect()
        time.sleep(1)

        # Physical addressing - Engine ECU only
        print("\n--- Physical Addressing (Engine ECU: 0x1000) ---")
        response = client.send_read_data_by_identifier(0xF190)
        if response:
            print(f"Physical response: {response.hex()}")
        else:
            print("No physical response")

        time.sleep(1)

        # Functional addressing - All ECUs that support it
        print("\n--- Functional Addressing (0x1FFF) ---")
        response = client.send_functional_read_data_by_identifier(0xF190)
        if response:
            print(f"Functional response: {response.hex()}")
        else:
            print("No functional response")

    except Exception as e:
        print(f"Error during comparison test: {e}")
    finally:
        client.disconnect()


if __name__ == "__main__":
    print("Functional Diagnostics Test Script")
    print("Make sure the DoIP server is running before starting this test.")
    print()

    # Run the tests
    test_functional_diagnostics()
    test_physical_vs_functional()

    print("\nTest completed. Check server logs for detailed information about")
    print("which ECUs responded to the functional addressing requests.")
