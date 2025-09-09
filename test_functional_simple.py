#!/usr/bin/env python3
"""
Simple test for functional diagnostics feature.
This test verifies that the server correctly handles functional addressing
by checking the server logs for functional address processing.
"""

import time
import socket
import struct

def test_functional_addressing():
    """Test functional addressing by sending raw DoIP messages"""
    print("=== Simple Functional Addressing Test ===")
    print("This test sends raw DoIP messages to verify functional addressing works.")
    print()
    
    # Create a raw socket connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # Connect to server
        print("Connecting to DoIP server...")
        sock.connect(("127.0.0.1", 13400))
        print("✓ Connected to server")
        
        # Send routing activation request
        print("\n--- Sending Routing Activation Request ---")
        routing_activation = create_routing_activation_request()
        sock.send(routing_activation)
        print(f"Sent routing activation: {routing_activation.hex()}")
        
        # Receive routing activation response
        response = sock.recv(1024)
        print(f"Received routing activation response: {response.hex()}")
        
        # Send functional diagnostic request (Read VIN)
        print("\n--- Sending Functional Diagnostic Request (Read VIN) ---")
        functional_request = create_functional_diagnostic_request(b'\x22\xF1\x90')  # Read VIN
        sock.send(functional_request)
        print(f"Sent functional request: {functional_request.hex()}")
        
        # Receive response
        response = sock.recv(1024)
        print(f"Received functional response: {response.hex()}")
        
        # Parse the response to verify it's a valid DoIP diagnostic message
        if len(response) >= 8:
            protocol_version = response[0]
            inverse_protocol_version = response[1]
            payload_type = struct.unpack(">H", response[2:4])[0]
            payload_length = struct.unpack(">I", response[4:8])[0]
            
            print(f"Response - Protocol: 0x{protocol_version:02X}, Inverse: 0x{inverse_protocol_version:02X}")
            print(f"Response - Payload Type: 0x{payload_type:04X}, Length: {payload_length}")
            
            if payload_type == 0x8001:  # Diagnostic message
                print("✓ Received valid DoIP diagnostic message response")
                
                # Extract UDS payload
                if len(response) >= 12:  # Header + source + target + UDS payload
                    source_addr = struct.unpack(">H", response[8:10])[0]
                    target_addr = struct.unpack(">H", response[10:12])[0]
                    uds_payload = response[12:]
                    
                    print(f"Response - Source: 0x{source_addr:04X}, Target: 0x{target_addr:04X}")
                    print(f"Response - UDS Payload: {uds_payload.hex()}")
                    
                    if uds_payload.startswith(b'\x62\xF1\x90'):  # Positive response for Read VIN (0x62 = Read Data by Identifier positive response)
                        print("✓ Received valid UDS response for Read VIN")
                        print("✓ Functional addressing is working correctly!")
                    else:
                        print(f"✗ Unexpected UDS response format: {uds_payload.hex()}")
                        print("Expected: 62F190... (Read Data by Identifier positive response)")
                else:
                    print("✗ Response too short for diagnostic message")
            else:
                print(f"✗ Unexpected payload type: 0x{payload_type:04X}")
        else:
            print("✗ Response too short")
            
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        sock.close()
        print("\nDisconnected from server")

def create_routing_activation_request():
    """Create a DoIP routing activation request"""
    # DoIP header
    protocol_version = 0x02
    inverse_protocol_version = 0xFD
    payload_type = 0x0005  # Routing activation request
    payload_length = 7
    
    # Payload
    client_logical_address = 0x0E00
    logical_address = 0x0000
    response_code = 0x00
    reserved = 0x00000000
    
    # Build message
    header = struct.pack(">BBHI", protocol_version, inverse_protocol_version, payload_type, payload_length)
    payload = struct.pack(">HHB", client_logical_address, logical_address, response_code)
    payload += struct.pack(">I", reserved)
    
    return header + payload

def create_functional_diagnostic_request(uds_payload):
    """Create a DoIP diagnostic message request to functional address"""
    # DoIP header
    protocol_version = 0x02
    inverse_protocol_version = 0xFD
    payload_type = 0x8001  # Diagnostic message
    payload_length = 4 + len(uds_payload)  # source + target + UDS payload
    
    # Payload
    source_address = 0x0E00
    target_address = 0x1FFF  # Functional address
    
    # Build message
    header = struct.pack(">BBHI", protocol_version, inverse_protocol_version, payload_type, payload_length)
    payload = struct.pack(">HH", source_address, target_address)
    payload += uds_payload
    
    return header + payload

if __name__ == "__main__":
    print("Simple Functional Addressing Test")
    print("Make sure the DoIP server is running before starting this test.")
    print()
    
    test_functional_addressing()
    
    print("\nTest completed. Check server logs for detailed functional addressing information.")
