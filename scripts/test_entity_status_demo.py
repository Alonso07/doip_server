#!/usr/bin/env python3
"""
Demonstration script for DoIP Entity Status Request and Response functionality.
This script shows how to use the new entity status features.
"""

import sys
import os
import time
import threading

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from doip_server.doip_server import DoIPServer
from doip_client.udp_doip_client import UDPDoIPClient


def run_entity_status_demo():
    """Run a demonstration of the entity status functionality."""
    print("=== DoIP Entity Status Demo ===")
    print()

    # Start server in background
    print("Starting DoIP server...")
    server = DoIPServer(host="127.0.0.1", port=13400)

    def run_server():
        try:
            server.start()
        except KeyboardInterrupt:
            pass

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(1)  # Give server time to start

    print("Server started on 127.0.0.1:13400")
    print()

    try:
        # Start client
        print("Starting UDP DoIP client...")
        client = UDPDoIPClient(server_port=13400, server_host="127.0.0.1")

        if not client.start():
            print("Failed to start client")
            return

        print("Client started successfully")
        print()

        # Test 1: Vehicle Identification Request
        print("=== Test 1: Vehicle Identification Request ===")
        vin_response = client.send_vehicle_identification_request()
        if vin_response:
            print("✓ Vehicle Identification Response received:")
            print(f"  VIN: {vin_response['vin']}")
            print(f"  Logical Address: 0x{vin_response['logical_address']:04X}")
            print(f"  EID: {vin_response['eid']}")
            print(f"  GID: {vin_response['gid']}")
        else:
            print("✗ Failed to receive vehicle identification response")
        print()

        # Test 2: Entity Status Request
        print("=== Test 2: Entity Status Request ===")
        status_response = client.send_entity_status_request()
        if status_response:
            print("✓ Entity Status Response received:")
            print(f"  Node Type: 0x{status_response['node_type']:02X}")
            print(f"  Max Open Sockets: {status_response['max_open_sockets']}")
            print(f"  Current Open Sockets: {status_response['current_open_sockets']}")
            print(
                f"  DoIP Entity Status: 0x{status_response['doip_entity_status']:02X}"
            )
            print(
                f"  Diagnostic Power Mode: 0x{status_response['diagnostic_power_mode']:02X}"
            )

            # Decode the values
            node_types = {0x01: "Vehicle Gateway", 0x02: "Node"}
            entity_statuses = {0x00: "Ready", 0x01: "Not Ready"}
            power_modes = {0x01: "Power On", 0x02: "Power Off", 0x03: "Not Ready"}

            print("  Decoded values:")
            print(
                f"    Node Type: {node_types.get(status_response['node_type'], 'Unknown')}"
            )
            print(
                f"    Entity Status: {entity_statuses.get(status_response['doip_entity_status'], 'Unknown')}"
            )
            print(
                f"    Power Mode: {power_modes.get(status_response['diagnostic_power_mode'], 'Unknown')}"
            )
        else:
            print("✗ Failed to receive entity status response")
        print()

        # Test 3: Multiple Entity Status Requests
        print("=== Test 3: Multiple Entity Status Requests ===")
        print("Sending 3 entity status requests...")
        for i in range(3):
            response = client.send_entity_status_request()
            if response:
                print(
                    f"  Request {i+1}: ✓ (Node Type: 0x{response['node_type']:02X}, Status: 0x{response['doip_entity_status']:02X})"
                )
            else:
                print(f"  Request {i+1}: ✗ Failed")
            time.sleep(0.5)
        print()

        # Test 4: Show configuration values
        print("=== Test 4: Configuration Values ===")
        try:
            entity_config = server.config_manager.get_entity_status_config()
            print("Current entity status configuration:")
            print(f"  Node Type: 0x{entity_config.get('node_type', 0x01):02X}")
            print(f"  Max Open Sockets: {entity_config.get('max_open_sockets', 10)}")
            print(
                f"  Current Open Sockets: {entity_config.get('current_open_sockets', 0)}"
            )
            print(
                f"  DoIP Entity Status: 0x{entity_config.get('doip_entity_status', 0x00):02X}"
            )
            print(
                f"  Diagnostic Power Mode: 0x{entity_config.get('diagnostic_power_mode', 0x02):02X}"
            )
        except Exception as e:
            print(f"Could not retrieve configuration: {e}")
        print()

        print("=== Demo Complete ===")
        print("All tests completed successfully!")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo failed with error: {e}")
    finally:
        # Cleanup
        print("Cleaning up...")
        client.stop()
        server.stop()
        server_thread.join(timeout=2)
        print("Cleanup complete")


if __name__ == "__main__":
    run_entity_status_demo()
