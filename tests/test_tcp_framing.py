"""Regression tests for TCP DoIP stream framing."""

import socket
import struct
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doip_server.doip_server import DoIPServer


def create_doip_message(payload_type, payload=b""):
    return struct.pack(">BBHI", 0x02, 0xFD, payload_type, len(payload)) + payload


@pytest.mark.unit
class TestTCPFraming:
    def setup_method(self):
        self.server = DoIPServer(gateway_config_path="config/gateway1.yaml")

    def test_receive_reassembles_fragmented_message(self):
        message = create_doip_message(0x0007)
        client_socket = MagicMock()
        # Header arrives split across two TCP reads; payload length is 0.
        client_socket.recv.side_effect = [message[:3], message[3:]]
        assert self.server._receive_doip_message(client_socket) == message

    def test_receive_reassembles_fragmented_payload(self):
        payload = struct.pack(">HHBII", 0x0E00, 0x0000, 0x00, 0, 0)
        message = create_doip_message(0x0005, payload)
        client_socket = MagicMock()
        client_socket.recv.side_effect = [
            message[:8],
            message[8:12],
            message[12:],
        ]
        assert self.server._receive_doip_message(client_socket) == message

    def test_coalesced_messages_are_processed_separately(self):
        server_socket, client_socket = socket.socketpair()
        self.server.running = True
        client_thread = threading.Thread(
            target=self.server.handle_client,
            args=(server_socket,),
        )
        client_thread.start()

        alive_check = create_doip_message(0x0007)
        client_socket.sendall(alive_check + alive_check)
        client_socket.shutdown(socket.SHUT_WR)

        received = bytearray()
        while True:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            received.extend(chunk)

        client_thread.join(timeout=2)
        client_socket.close()

        response_length = len(self.server.handle_alive_check())
        assert len(received) == response_length * 2
        assert struct.unpack(">H", received[2:4])[0] == 0x0008
        assert (
            struct.unpack(">H", received[response_length + 2 : response_length + 4])[0]
            == 0x0008
        )
