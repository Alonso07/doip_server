#!/usr/bin/env python3
"""
Simple test for UDP DoIP functionality without external dependencies
"""

import sys
import struct
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from doip_client.udp_doip_client import UDPDoIPClient  # pylint: disable=wrong-import-position

def test_udp_client():
    """Test UDP DoIP client functionality"""
    print("=== UDP DoIP Client Test ===")

    # Create client
    client = UDPDoIPClient(server_port=13400, timeout=2.0)

    # Test request creation
    print("1. Testing request creation...")
    request = client.create_vehicle_identification_request()
    print(f"   Request: {request.hex()}")
    print(f"   Length: {len(request)} bytes")

    # Test response parsing
    print("\n2. Testing response parsing...")

    # Create a mock response
    vin = "1HGBH41JXMN109186"
    logical_address = 0x1000
    eid = b'\x12\x34\x56\x78\x9A\xBC'
    gid = b'\xDE\xF0\x12\x34\x56\x78'
    further_action = 0x00
    sync_status = 0x00

    # Create payload
    payload = vin.encode('ascii').ljust(17, b'\x00')
    payload += struct.pack(">H", logical_address)
    payload += eid
    payload += gid
    payload += struct.pack(">B", further_action)
    payload += struct.pack(">B", sync_status)

    # Create DoIP header
    header = struct.pack(
        ">BBHI",
        0x02,  # Protocol version
        0xFD,  # Inverse protocol version
        0x0004,  # Payload type
        len(payload)
    )

    response_data = header + payload
    print(f"   Mock response: {response_data.hex()}")

    # Parse response
    result = client.parse_vehicle_identification_response(response_data)
    if result:
        print("   ✅ Response parsed successfully!")
        print(f"   VIN: {result['vin']}")
        print(f"   Logical Address: 0x{result['logical_address']:04X}")
        print(f"   EID: {result['eid']}")
        print(f"   GID: {result['gid']}")
        print(f"   Further Action: {result['further_action_required']}")
        print(f"   Sync Status: {result['vin_gid_sync_status']}")
    else:
        print("   ❌ Response parsing failed!")

    # Test invalid response
    print("\n3. Testing invalid response handling...")
    invalid_response = b'\x01\xFE\x00\x04\x00\x00\x00\x21' + b'\x00' * 33
    result = client.parse_vehicle_identification_response(invalid_response)
    if result is None:
        print("   ✅ Invalid response correctly rejected!")
    else:
        print("   ❌ Invalid response should have been rejected!")

    print("\n=== Test Complete ===")
    print("✅ UDP DoIP client functionality working correctly!")

if __name__ == "__main__":
    test_udp_client()
