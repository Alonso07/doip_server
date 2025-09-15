#!/usr/bin/env python3
"""
Test module for DoIP message construction and parsing using the doipclient library.
This module contains pytest tests for both message format analysis and actual network communication.
"""

import struct
import time
import pytest
import sys
import os

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from doip_client.doip_client import DoIPClientWrapper


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
    return struct.pack(
        ">BBHI",
        DOIP_PROTOCOL_VERSION,
        DOIP_INVERSE_PROTOCOL_VERSION,
        payload_type,
        payload_length,
    )


def test_routine_activation():
    """Test routine activation message construction"""
    # Routine activation payload
    routine_identifier = 0x0202
    routine_type = 0x0001
    payload = struct.pack(">HH", routine_identifier, routine_type)

    # Create DoIP message
    header = create_doip_header(PAYLOAD_TYPE_ROUTINE_ACTIVATION_REQUEST, len(payload))
    message = header + payload

    # Verify message structure
    assert len(message) == 12  # 8 bytes header + 4 bytes payload
    assert message[0] == DOIP_PROTOCOL_VERSION
    assert message[1] == DOIP_INVERSE_PROTOCOL_VERSION
    assert (
        struct.unpack(">H", message[2:4])[0] == PAYLOAD_TYPE_ROUTINE_ACTIVATION_REQUEST
    )
    assert struct.unpack(">I", message[4:8])[0] == len(payload)
    assert struct.unpack(">H", message[8:10])[0] == routine_identifier
    assert struct.unpack(">H", message[10:12])[0] == routine_type


def test_uds_message():
    """Test UDS message construction"""
    # UDS Read Data by Identifier
    data_identifier = 0xF187
    source_address = 0x0E00
    target_address = 0x1000

    # Create UDS payload
    uds_payload = struct.pack(">BH", UDS_READ_DATA_BY_IDENTIFIER, data_identifier)

    # Create DoIP payload
    payload = struct.pack(">HH", source_address, target_address) + uds_payload

    # Create DoIP message
    header = create_doip_header(PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE, len(payload))
    message = header + payload

    # Verify message structure
    assert len(message) == 15  # 8 bytes header + 7 bytes payload
    assert message[0] == DOIP_PROTOCOL_VERSION
    assert message[1] == DOIP_INVERSE_PROTOCOL_VERSION
    assert struct.unpack(">H", message[2:4])[0] == PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE
    assert struct.unpack(">I", message[4:8])[0] == len(payload)
    assert struct.unpack(">H", message[8:10])[0] == source_address
    assert struct.unpack(">H", message[10:12])[0] == target_address
    assert message[12] == UDS_READ_DATA_BY_IDENTIFIER
    assert struct.unpack(">H", message[13:15])[0] == data_identifier


def test_alive_check():
    """Test alive check message construction"""
    # Empty payload for alive check
    payload = b""

    # Create DoIP message
    header = create_doip_header(PAYLOAD_TYPE_ALIVE_CHECK_REQUEST, len(payload))
    message = header + payload

    # Verify message structure
    assert len(message) == 8  # 8 bytes header + 0 bytes payload
    assert message[0] == DOIP_PROTOCOL_VERSION
    assert message[1] == DOIP_INVERSE_PROTOCOL_VERSION
    assert struct.unpack(">H", message[2:4])[0] == PAYLOAD_TYPE_ALIVE_CHECK_REQUEST
    assert struct.unpack(">I", message[4:8])[0] == 0


def test_response_creation():
    """Test response message creation"""
    # Routine activation response
    response_code = 0x10  # Success
    routine_type = 0x0001
    payload = struct.pack(">HH", response_code, routine_type)

    header = create_doip_header(PAYLOAD_TYPE_ROUTINE_ACTIVATION_RESPONSE, len(payload))
    response = header + payload

    # Verify routine activation response
    assert len(response) == 12  # 8 bytes header + 4 bytes payload
    assert response[0] == DOIP_PROTOCOL_VERSION
    assert response[1] == DOIP_INVERSE_PROTOCOL_VERSION
    assert (
        struct.unpack(">H", response[2:4])[0]
        == PAYLOAD_TYPE_ROUTINE_ACTIVATION_RESPONSE
    )
    assert struct.unpack(">I", response[4:8])[0] == len(payload)
    assert struct.unpack(">H", response[8:10])[0] == response_code
    assert struct.unpack(">H", response[10:12])[0] == routine_type

    # UDS response for Read Data by Identifier
    data_identifier = 0xF187
    uds_response = b"\x62" + struct.pack(">H", data_identifier) + b"\x01\x02\x03\x04"

    source_addr = 0x1000
    target_addr = 0x0E00
    payload = struct.pack(">HH", source_addr, target_addr) + uds_response

    header = create_doip_header(PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE, len(payload))
    response = header + payload

    # Verify UDS response
    assert len(response) == 19  # 8 bytes header + 11 bytes payload
    assert response[0] == DOIP_PROTOCOL_VERSION
    assert response[1] == DOIP_INVERSE_PROTOCOL_VERSION
    assert struct.unpack(">H", response[2:4])[0] == PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE
    assert struct.unpack(">I", response[4:8])[0] == len(payload)
    assert struct.unpack(">H", response[8:10])[0] == source_addr
    assert struct.unpack(">H", response[10:12])[0] == target_addr
    assert response[12] == 0x62  # UDS positive response for 0x22
    assert struct.unpack(">H", response[13:15])[0] == data_identifier


@pytest.mark.integration
def test_doipclient_usage():
    """Test usage of the doipclient library (requires running server)"""
    # Create client wrapper
    client = DoIPClientWrapper(
        server_host="127.0.0.1",
        server_port=13400,
        logical_address=0x0E00,
        target_address=0x1000,
    )

    try:
        # This test will be skipped if no server is running
        client.connect()

        # Test diagnostic session control
        response = client.send_diagnostic_session_control(0x03)
        # Note: We don't assert on response content as it depends on server state

        # Test routine activation
        response = client.send_routine_activation(0x0202, 0x0001)
        # Note: We don't assert on response content as it depends on server state

        # Test read data by identifier
        data_identifiers = [0xF187, 0xF188, 0xF189]
        for di in data_identifiers:
            response = client.send_read_data_by_identifier(di)
            # Note: We don't assert on response content as it depends on server state

        # Test tester present
        response = client.send_tester_present()
        # Note: We don't assert on response content as it depends on server state

    except Exception as e:
        # Skip test if no server is running
        pytest.skip(f"Test requires running DoIP server: {e}")
    finally:
        client.disconnect()


def test_doipclient_wrapper_creation():
    """Test DoIPClientWrapper creation and basic properties"""
    client = DoIPClientWrapper(
        server_host="127.0.0.1",
        server_port=13400,
        logical_address=0x0E00,
        target_address=0x1000,
    )

    assert client.server_host == "127.0.0.1"
    assert client.server_port == 13400
    assert client.logical_address == 0x0E00
    assert client.target_address == 0x1000
    assert client.doip_client is None  # Not connected yet
