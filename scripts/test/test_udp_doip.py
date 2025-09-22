#!/usr/bin/env python3
"""
Test script for UDP DoIP Vehicle Identification functionality
This script demonstrates the UDP DoIP client and server working together.
"""

import time
import threading
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from doip_client.udp_doip_client import UDPDoIPClient
from doip_server.doip_server import start_doip_server


def run_server():
    """Run the DoIP server in a separate thread"""
    print("Starting DoIP server...")
    try:
        start_doip_server(gateway_config_path="config/gateway1.yaml")
    except KeyboardInterrupt:
        print("Server stopped")


def run_client_test():
    """Run the UDP DoIP client test"""
    print("Starting UDP DoIP client test...")

    # Wait a moment for server to start
    time.sleep(2)

    # Create and run client
    client = UDPDoIPClient(server_port=13400, timeout=5.0)
    responses = client.run_test(num_requests=3, delay=1.0)

    # Print results
    if responses:
        print("\n=== Test Results ===")
        print(f"Received {len(responses)} responses:")
        for i, response in enumerate(responses):
            print(f"  {i+1}. VIN: {response['vin']}")
            print(f"     Address: 0x{response['logical_address']:04X}")
            print(f"     EID: {response['eid']}")
            print(f"     GID: {response['gid']}")
            print(f"     Further Action: {response['further_action_required']}")
            print(f"     Sync Status: {response['vin_gid_sync_status']}")
            print()
    else:
        print("No responses received - test failed")

    return len(responses) > 0


def main():
    """Main test function"""
    print("=== UDP DoIP Vehicle Identification Test ===")
    print("This test will:")
    print("1. Start the DoIP server with UDP support")
    print("2. Run the UDP DoIP client to send vehicle identification requests")
    print("3. Display the responses received")
    print()

    # Start server in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    try:
        # Run client test
        success = run_client_test()

        if success:
            print("✅ Test completed successfully!")
        else:
            print("❌ Test failed - no responses received")

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")

    print("\nTest completed. Server will continue running until interrupted.")


if __name__ == "__main__":
    main()
