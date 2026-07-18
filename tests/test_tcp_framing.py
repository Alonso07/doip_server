import socket
import struct
import threading
from unittest.mock import MagicMock

from doip_server.doip_tcp import DoIPTCPServer


def create_doip_message(payload_type, payload=b""):
    return struct.pack(">BBHI", 0x02, 0xFD, payload_type, len(payload)) + payload


class TestTCPFraming:
    def setup_method(self):
        self.server = DoIPTCPServer("127.0.0.1", 0, MagicMock())

    def test_receive_reassembles_fragmented_message(self):
        message = create_doip_message(0x0007)
        client_socket = MagicMock()
        client_socket.recv.side_effect = [
            message[:3],
            message[3:8],
        ]

        assert self.server._receive_doip_message(client_socket) == message

    def test_coalesced_messages_are_processed_separately(self):
        server_socket, client_socket = socket.socketpair()
        self.server.running = True
        client_thread = threading.Thread(
            target=self.server.handle_client,
            args=(server_socket, ("local", 0)),
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

        client_thread.join(timeout=1)
        client_socket.close()

        response_length = 8 + 6
        assert len(received) == response_length * 2
        assert struct.unpack(">H", received[2:4])[0] == 0x0008
        assert (
            struct.unpack(">H", received[response_length + 2 : response_length + 4])[0]
            == 0x0008
        )
