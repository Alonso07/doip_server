#!/usr/bin/env python3
"""
Demonstration script showing DoIP message construction and parsing using the doipclient library.
This script demonstrates both message format analysis and actual network communication.
"""

import struct
import time
from .doip_client import DoIPClientWrapper


# DoIP Protocol constants (for reference)
DOIP_PROTOCOL_VERSION = 0x02
DOIP_INVERSE_PROTOCOL_VERSION = 0xFD

# DoIP Payload types
PAYLOAD_TYPE_ALIVE_CHECK_REQUEST = 0x0001
PAYLOAD_TYPE_ALIVE_CHECK_RESPONSE = 0x0002
PAYLOAD_TYPE_ROUTINE_ACTIVATION_REQUEST = 0x0005
PAYLOAD_TYPE_ROUTINE_ACTIVATION_RESPONSE = 0x0006
PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE = 0x8001

# UDS Service IDs
UDS_READ_DATA_BY_IDENTIFIER = 0x22
UDS_ROUTINE_CONTROL = 0x31
UDS_DIAGNOSTIC_SESSION_CONTROL = 0x10
UDS_TESTER_PRESENT = 0x3E


def create_doip_header(payload_type, payload_length):
    """Create DoIP header (for reference/demonstration)"""
    return struct.pack('>BBHI', 
                      DOIP_PROTOCOL_VERSION,
                      DOIP_INVERSE_PROTOCOL_VERSION,
                      payload_type,
                      payload_length)


def demo_routine_activation():
    """Demonstrate routine activation message construction"""
    print("=== Routine Activation Demo ===")
    
    # Routine activation payload
    routine_identifier = 0x0202
    routine_type = 0x0001
    payload = struct.pack('>HH', routine_identifier, routine_type)
    
    # Create DoIP message
    header = create_doip_header(PAYLOAD_TYPE_ROUTINE_ACTIVATION_REQUEST, len(payload))
    message = header + payload
    
    print(f"Routine Identifier: 0x{routine_identifier:04X}")
    print(f"Routine Type: 0x{routine_type:04X}")
    print(f"Payload: {payload.hex()}")
    print(f"Full Message: {message.hex()}")
    print(f"Message Length: {len(message)} bytes")
    
    # Parse the message back
    print("\nParsing the message:")
    print(f"Protocol Version: 0x{message[0]:02X}")
    print(f"Inverse Protocol Version: 0x{message[1]:02X}")
    print(f"Payload Type: 0x{struct.unpack('>H', message[2:4])[0]:04X}")
    print(f"Payload Length: {struct.unpack('>I', message[4:8])[0]}")
    print(f"Routine ID: 0x{struct.unpack('>H', message[8:10])[0]:04X}")
    print(f"Routine Type: 0x{struct.unpack('>H', message[10:12])[0]:04X}")
    print()


def demo_uds_message():
    """Demonstrate UDS message construction"""
    print("=== UDS Message Demo ===")
    
    # UDS Read Data by Identifier
    data_identifier = 0xF187
    source_address = 0x0E00
    target_address = 0x1000
    
    # Create UDS payload
    uds_payload = struct.pack('>BH', UDS_READ_DATA_BY_IDENTIFIER, data_identifier)
    
    # Create DoIP payload
    payload = struct.pack('>HH', source_address, target_address) + uds_payload
    
    # Create DoIP message
    header = create_doip_header(PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE, len(payload))
    message = header + payload
    
    print(f"Source Address: 0x{source_address:04X}")
    print(f"Target Address: 0x{target_address:04X}")
    print(f"UDS Service: 0x{UDS_READ_DATA_BY_IDENTIFIER:02X}")
    print(f"Data Identifier: 0x{data_identifier:04X}")
    print(f"UDS Payload: {uds_payload.hex()}")
    print(f"Full Message: {message.hex()}")
    print(f"Message Length: {len(message)} bytes")
    
    # Parse the message back
    print("\nParsing the message:")
    print(f"Protocol Version: 0x{message[0]:02X}")
    print(f"Inverse Protocol Version: 0x{message[1]:02X}")
    print(f"Payload Type: 0x{struct.unpack('>H', message[2:4])[0]:04X}")
    print(f"Payload Length: {struct.unpack('>I', message[4:8])[0]}")
    print(f"Source Address: 0x{struct.unpack('>H', message[8:10])[0]:04X}")
    print(f"Target Address: 0x{struct.unpack('>H', message[10:12])[0]:04X}")
    print(f"UDS Service: 0x{message[12]:02X}")
    print(f"Data Identifier: 0x{struct.unpack('>H', message[13:15])[0]:04X}")
    print()


def demo_alive_check():
    """Demonstrate alive check message construction"""
    print("=== Alive Check Demo ===")
    
    # Empty payload for alive check
    payload = b''
    
    # Create DoIP message
    header = create_doip_header(PAYLOAD_TYPE_ALIVE_CHECK_REQUEST, len(payload))
    message = header + payload
    
    print(f"Payload: (empty)")
    print(f"Full Message: {message.hex()}")
    print(f"Message Length: {len(message)} bytes")
    
    # Parse the message back
    print("\nParsing the message:")
    print(f"Protocol Version: 0x{message[0]:02X}")
    print(f"Inverse Protocol Version: 0x{message[1]:02X}")
    print(f"Payload Type: 0x{struct.unpack('>H', message[2:4])[0]:04X}")
    print(f"Payload Length: {struct.unpack('>I', message[4:8])[0]}")
    print()


def demo_response_creation():
    """Demonstrate response message creation"""
    print("=== Response Creation Demo ===")
    
    # Routine activation response
    response_code = 0x10  # Success
    routine_type = 0x0001
    payload = struct.pack('>HH', response_code, routine_type)
    
    header = create_doip_header(PAYLOAD_TYPE_ROUTINE_ACTIVATION_RESPONSE, len(payload))
    response = header + payload
    
    print(f"Response Code: 0x{response_code:02X} (Success)")
    print(f"Routine Type: 0x{routine_type:04X}")
    print(f"Response Message: {response.hex()}")
    print()
    
    # UDS response for Read Data by Identifier
    data_identifier = 0xF187
    uds_response = b'\x62' + struct.pack('>H', data_identifier) + b'\x01\x02\x03\x04'
    
    source_addr = 0x1000
    target_addr = 0x0E00
    payload = struct.pack('>HH', source_addr, target_addr) + uds_response
    
    header = create_doip_header(PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE, len(payload))
    response = header + payload
    
    print(f"UDS Response: {uds_response.hex()}")
    print(f"Source Address: 0x{source_addr:04X}")
    print(f"Target Address: 0x{target_addr:04X}")
    print(f"Response Message: {response.hex()}")
    print()


def demo_doipclient_usage():
    """Demonstrate usage of the doipclient library"""
    print("=== DoIP Client Library Demo ===")
    print("This demo shows how to use the doipclient library for actual communication.")
    print("Note: This requires a running DoIP server to connect to.")
    print()
    
    # Create client wrapper
    client = DoIPClientWrapper(
        server_host='127.0.0.1',
        server_port=13400,
        logical_address=0x0E00,
        target_address=0x1000
    )
    
    try:
        print("Attempting to connect to DoIP server...")
        client.connect()
        
        print("\n--- Sending Diagnostic Session Control ---")
        response = client.send_diagnostic_session_control(0x03)
        if response:
            print(f"Session control response: {response.hex()}")
        
        time.sleep(1)
        
        print("\n--- Sending Routine Activation ---")
        response = client.send_routine_activation(0x0202, 0x0001)
        if response:
            print(f"Routine activation response: {response.hex()}")
        
        time.sleep(1)
        
        print("\n--- Sending Read Data by Identifier ---")
        data_identifiers = [0xF187, 0xF188, 0xF189]
        for di in data_identifiers:
            response = client.send_read_data_by_identifier(di)
            if response:
                print(f"Read data response for 0x{di:04X}: {response.hex()}")
            time.sleep(0.5)
        
        print("\n--- Sending Tester Present ---")
        response = client.send_tester_present()
        if response:
            print(f"Tester present response: {response.hex()}")
        
    except Exception as e:
        print(f"Demo failed (this is expected if no server is running): {e}")
        print("To test the client, start the DoIP server first using: poetry run doip_server")
    finally:
        client.disconnect()


def main():
    """Run all demonstrations"""
    print("DoIP Message Construction and Parsing Demo")
    print("Using doipclient library for enhanced functionality")
    print("=" * 70)
    print()
    
    # Message format demonstrations (no network required)
    demo_routine_activation()
    demo_uds_message()
    demo_alive_check()
    demo_response_creation()
    
    print("=" * 70)
    print()
    
    # Network communication demo (requires running server)
    demo_doipclient_usage()
    
    print("\nDemo completed!")
    print("\nTo test the client with a real server:")
    print("1. Start the DoIP server: poetry run doip_server")
    print("2. Run the client: poetry run doip_client")


if __name__ == "__main__":
    main()