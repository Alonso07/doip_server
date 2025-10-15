#!/usr/bin/env python3
"""
DoIP TCP Server module.

This module provides TCP-specific functionality for the DoIP server,
including connection handling, message processing, and client management.
"""
import socket
import threading
import logging
from typing import Optional, List, Callable
from .messages import (
    DoIPMessage,
    PAYLOAD_TYPE_ROUTING_ACTIVATION_REQUEST,
    PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE,
    PAYLOAD_TYPE_ALIVE_CHECK_REQUEST,
    PAYLOAD_TYPE_POWER_MODE_INFORMATION_REQUEST,
    PAYLOAD_TYPE_ENTITY_STATUS_REQUEST,
)
from .handlers import DoIPHandlers
from .hierarchical_config_manager import HierarchicalConfigManager


class DoIPTCPServer:
    """DoIP TCP Server for handling diagnostic sessions."""

    def __init__(
        self,
        host: str,
        port: int,
        config_manager: HierarchicalConfigManager,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize DoIP TCP server.

        Args:
            host: Server host address
            port: Server port number
            config_manager: Configuration manager instance
            logger: Logger instance for this server
        """
        self.host = host
        self.port = port
        self.config_manager = config_manager
        self.logger = logger or logging.getLogger(__name__)

        self.message_handler = DoIPMessage(logger)
        self.handlers = DoIPHandlers(config_manager, logger)

        self.server_socket = None
        self.running = False
        self.client_threads = []
        self.max_connections = 10
        self.timeout = 30

    def start(self) -> bool:
        """Start the TCP server.

        Returns:
            True if server started successfully
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_connections)
            self.server_socket.settimeout(1.0)  # Non-blocking with timeout

            self.running = True
            self.logger.info(f"TCP server started on {self.host}:{self.port}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start TCP server: {e}")
            return False

    def stop(self):
        """Stop the TCP server."""
        self.running = False

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"Error closing server socket: {e}")

        # Wait for client threads to finish
        for thread in self.client_threads:
            if thread.is_alive():
                thread.join(timeout=5.0)

        self.logger.info("TCP server stopped")

    def accept_connections(self):
        """Accept incoming TCP connections in a loop."""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                self.logger.info(f"New TCP connection from {client_address}")

                # Create client thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True,
                )
                client_thread.start()
                self.client_threads.append(client_thread)

                # Clean up finished threads
                self.client_threads = [t for t in self.client_threads if t.is_alive()]

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Error accepting connection: {e}")
                break

    def handle_client(self, client_socket: socket.socket, client_address: tuple):
        """Handle client connection and process DoIP messages.

        Args:
            client_socket: Client socket
            client_address: Client address tuple
        """
        try:
            client_socket.settimeout(self.timeout)

            while self.running:
                try:
                    # Receive DoIP message
                    data = self._receive_doip_message(client_socket)
                    if not data:
                        break

                    # Process DoIP message
                    responses = self.process_doip_message(data)

                    # Send responses
                    for i, response in enumerate(responses):
                        client_socket.send(response)
                        self.logger.debug(
                            f"Sent response {i+1}/{len(responses)} to {client_address}"
                        )

                except socket.timeout:
                    self.logger.debug(f"Client {client_address} timeout")
                    break
                except ConnectionResetError:
                    self.logger.debug(f"Client {client_address} disconnected")
                    break
                except Exception as e:
                    self.logger.error(f"Error handling client {client_address}: {e}")
                    break

        except Exception as e:
            self.logger.error(f"Error in client handler for {client_address}: {e}")
        finally:
            try:
                client_socket.close()
                self.logger.info(f"Closed connection to {client_address}")
            except Exception as e:
                self.logger.error(f"Error closing client socket: {e}")

    def process_doip_message(self, data: bytes) -> List[bytes]:
        """Process incoming DoIP message and return appropriate response(s).

        Args:
            data: Raw DoIP message data

        Returns:
            List of DoIP response messages
        """
        try:
            # Parse DoIP header
            protocol_version, payload_type, payload_length = (
                self.message_handler.parse_doip_header(data)
            )

            # Validate payload length
            if len(data) < 8 + payload_length:
                self.logger.error("Incomplete DoIP message")
                return [
                    self.message_handler.create_doip_nack(0x02)
                ]  # Invalid payload length

            payload = data[8 : 8 + payload_length]

            # Route to appropriate handler based on payload type
            if payload_type == PAYLOAD_TYPE_ROUTING_ACTIVATION_REQUEST:
                response = self.handlers.handle_routing_activation(payload)
                return [response]

            elif payload_type == PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE:
                return self.handlers.handle_diagnostic_message(payload)

            elif payload_type == PAYLOAD_TYPE_ALIVE_CHECK_REQUEST:
                response = self.handlers.handle_alive_check()
                return [response]

            elif payload_type == PAYLOAD_TYPE_POWER_MODE_INFORMATION_REQUEST:
                response = self.handlers.handle_power_mode_request(payload)
                return [response]

            elif payload_type == PAYLOAD_TYPE_ENTITY_STATUS_REQUEST:
                response = self.handlers.handle_entity_status_request(payload)
                return [response]

            else:
                self.logger.warning(f"Unsupported payload type: 0x{payload_type:04X}")
                return [
                    self.message_handler.create_doip_nack(0x00)
                ]  # Unknown payload type

        except Exception as e:
            self.logger.error(f"Error processing DoIP message: {e}")
            return [
                self.message_handler.create_doip_nack(0x02)
            ]  # Invalid payload length

    def _receive_doip_message(self, client_socket: socket.socket) -> bytes:
        """Receive complete DoIP message from client.

        Args:
            client_socket: Client socket

        Returns:
            Complete DoIP message as bytes
        """
        # Use simple approach like original implementation
        data = client_socket.recv(1024)
        if not data:
            return b""

        return data

    def get_server_info(self) -> dict:
        """Get TCP server information.

        Returns:
            Dictionary containing server information
        """
        return {
            "type": "TCP",
            "host": self.host,
            "port": self.port,
            "running": self.running,
            "max_connections": self.max_connections,
            "timeout": self.timeout,
            "active_connections": len([t for t in self.client_threads if t.is_alive()]),
        }

    def is_ready(self) -> bool:
        """Check if TCP server is ready to accept connections.

        Returns:
            True if server is ready
        """
        return self.running and self.server_socket is not None
