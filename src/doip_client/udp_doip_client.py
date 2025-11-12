#!/usr/bin/env python3
"""
UDP DoIP Client for Vehicle Identification Testing
This client broadcasts vehicle identification requests over UDP and receives responses.
"""

import logging
import socket
import struct
import time
from typing import Optional


class UDPDoIPClient:
    """
    UDP-based DoIP client for vehicle identification testing.
    Broadcasts vehicle identification requests and receives responses.
    """

    # DoIP Protocol constants
    DOIP_PROTOCOL_VERSION = 0x02
    DOIP_INVERSE_PROTOCOL_VERSION = 0xFD

    # DoIP Payload types
    PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_REQUEST = 0x0001
    PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_RESPONSE = 0x0004
    PAYLOAD_TYPE_ENTITY_STATUS_REQUEST = 0x4001
    PAYLOAD_TYPE_ENTITY_STATUS_RESPONSE = 0x4002
    PAYLOAD_TYPE_POWER_MODE_INFORMATION_REQUEST = 0x4003
    PAYLOAD_TYPE_POWER_MODE_INFORMATION_RESPONSE = 0x4004

    def __init__(
        self,
        server_port: int = 13400,
        server_host: str = "255.255.255.255",
        timeout: float = 5.0,
    ):
        """
        Initialize the UDP DoIP client.

        Args:
            server_port: UDP port to send requests to (default: 13400)
            server_host: Server host address (default: 255.255.255.255 for broadcast)
            timeout: Timeout for receiving responses in seconds
        """
        self.server_port = server_port
        self.server_host = server_host
        self.timeout = timeout
        self.socket = None
        self.broadcast_address = server_host

        # Setup logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def create_vehicle_identification_request(self) -> bytes:
        """
        Create a DoIP Vehicle Identification Request message.

        According to ISO 13400-2:2019, vehicle identification requests should use
        protocol version 0xFF and inverse protocol version 0x00.

        Returns:
            bytes: Complete DoIP message with vehicle identification request
        """
        # DoIP header: protocol_version, inverse_protocol_version, payload_type, payload_length
        # For vehicle identification requests, use 0xFF/0x00 per ISO 13400-2:2019
        header = struct.pack(
            ">BBHI",
            0xFF,  # Protocol version for vehicle identification (ISO 13400-2:2019)
            0x00,  # Inverse protocol version for vehicle identification
            self.PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_REQUEST,
            0,  # No payload for vehicle identification request
        )

        return header

    def create_entity_status_request(self) -> bytes:
        """
        Create a DoIP Entity Status Request message.

        Returns:
            bytes: Complete DoIP message with entity status request
        """
        # DoIP header: protocol_version, inverse_protocol_version, payload_type, payload_length
        header = struct.pack(
            ">BBHI",
            self.DOIP_PROTOCOL_VERSION,
            self.DOIP_INVERSE_PROTOCOL_VERSION,
            self.PAYLOAD_TYPE_ENTITY_STATUS_REQUEST,
            0,  # No payload for entity status request
        )

        return header

    def create_power_mode_information_request(self) -> bytes:
        """
        Create a DoIP Power Mode Information Request message.

        Returns:
            bytes: Complete DoIP message with power mode information request
        """
        # DoIP header: protocol_version, inverse_protocol_version, payload_type, payload_length
        header = struct.pack(
            ">BBHI",
            self.DOIP_PROTOCOL_VERSION,
            self.DOIP_INVERSE_PROTOCOL_VERSION,
            self.PAYLOAD_TYPE_POWER_MODE_INFORMATION_REQUEST,
            0,  # No payload for power mode information request
        )

        return header

    def parse_power_mode_information_response(self, data: bytes) -> Optional[dict]:
        """
        Parse a DoIP Power Mode Information Response message.

        Args:
            data: Raw DoIP message bytes

        Returns:
            dict: Parsed response data or None if invalid
        """
        if len(data) < 8:  # Minimum DoIP header size
            self.logger.error("Response too short for DoIP header")
            return None

        # Parse DoIP header
        protocol_version = data[0]
        inverse_protocol_version = data[1]
        payload_type = struct.unpack(">H", data[2:4])[0]
        payload_length = struct.unpack(">I", data[4:8])[0]

        self.logger.debug(f"Protocol Version: 0x{protocol_version:02X}")
        self.logger.debug(f"Inverse Protocol Version: 0x{inverse_protocol_version:02X}")
        self.logger.debug(f"Payload Type: 0x{payload_type:04X}")
        self.logger.debug(f"Payload Length: {payload_length}")

        # Validate protocol version
        if (
            protocol_version != self.DOIP_PROTOCOL_VERSION
            or inverse_protocol_version != self.DOIP_INVERSE_PROTOCOL_VERSION
        ):
            self.logger.error(f"Invalid protocol version: 0x{protocol_version:02X}")
            return None

        # Check payload type
        if payload_type != self.PAYLOAD_TYPE_POWER_MODE_INFORMATION_RESPONSE:
            self.logger.error(f"Unexpected payload type: 0x{payload_type:04X}")
            return None

        # Check payload length (should be 1 byte for power mode information response)
        if payload_length != 1:
            self.logger.error(f"Invalid payload length: {payload_length}, expected 1")
            return None

        if len(data) < 8 + payload_length:
            self.logger.error("Incomplete payload data")
            return None

        # Parse payload
        payload = data[8 : 8 + payload_length]

        # Power Mode Information Response payload structure:
        # Power Mode Status (1 byte)
        power_mode_status = payload[0]

        return {
            "power_mode_status": power_mode_status,
        }

    def parse_entity_status_response(self, data: bytes) -> Optional[dict]:
        """
        Parse a DoIP Entity Status Response message.

        Args:
            data: Raw DoIP message bytes

        Returns:
            dict: Parsed response data or None if invalid
        """
        if len(data) < 8:  # Minimum DoIP header size
            self.logger.error("Response too short for DoIP header")
            return None

        # Parse DoIP header
        protocol_version = data[0]
        inverse_protocol_version = data[1]
        payload_type = struct.unpack(">H", data[2:4])[0]
        payload_length = struct.unpack(">I", data[4:8])[0]

        self.logger.debug(f"Protocol Version: 0x{protocol_version:02X}")
        self.logger.debug(f"Inverse Protocol Version: 0x{inverse_protocol_version:02X}")
        self.logger.debug(f"Payload Type: 0x{payload_type:04X}")
        self.logger.debug(f"Payload Length: {payload_length}")

        # Validate protocol version
        if (
            protocol_version != self.DOIP_PROTOCOL_VERSION
            or inverse_protocol_version != self.DOIP_INVERSE_PROTOCOL_VERSION
        ):
            self.logger.error(f"Invalid protocol version: 0x{protocol_version:02X}")
            return None

        # Check payload type
        if payload_type != self.PAYLOAD_TYPE_ENTITY_STATUS_RESPONSE:
            self.logger.error(f"Unexpected payload type: 0x{payload_type:04X}")
            return None

        # Check payload length (should be 5 bytes for entity status response)
        if payload_length != 5:
            self.logger.error(f"Invalid payload length: {payload_length}, expected 5")
            return None

        if len(data) < 8 + payload_length:
            self.logger.error("Incomplete payload data")
            return None

        # Parse payload
        payload = data[8 : 8 + payload_length]

        # Entity Status Response payload structure:
        # Node Type (1 byte) + Max Open Sockets (1 byte) + Current Open Sockets (1 byte) +
        # DoIP Entity Status (1 byte) + Diagnostic Power Mode (1 byte)
        node_type = payload[0]
        max_open_sockets = payload[1]
        current_open_sockets = payload[2]
        doip_entity_status = payload[3]
        diagnostic_power_mode = payload[4]

        return {
            "node_type": node_type,
            "max_open_sockets": max_open_sockets,
            "current_open_sockets": current_open_sockets,
            "doip_entity_status": doip_entity_status,
            "diagnostic_power_mode": diagnostic_power_mode,
        }

    def parse_vehicle_identification_response(self, data: bytes) -> Optional[dict]:
        """
        Parse a DoIP Vehicle Identification Response message.

        Args:
            data: Raw DoIP message bytes

        Returns:
            dict: Parsed response data or None if invalid
        """
        if len(data) < 8:  # Minimum DoIP header size
            self.logger.error("Response too short for DoIP header")
            return None

        # Parse DoIP header
        protocol_version = data[0]
        inverse_protocol_version = data[1]
        payload_type = struct.unpack(">H", data[2:4])[0]
        payload_length = struct.unpack(">I", data[4:8])[0]

        self.logger.debug(f"Protocol Version: 0x{protocol_version:02X}")
        self.logger.debug(f"Inverse Protocol Version: 0x{inverse_protocol_version:02X}")
        self.logger.debug(f"Payload Type: 0x{payload_type:04X}")
        self.logger.debug(f"Payload Length: {payload_length}")

        # Validate protocol version
        if (
            protocol_version != self.DOIP_PROTOCOL_VERSION
            or inverse_protocol_version != self.DOIP_INVERSE_PROTOCOL_VERSION
        ):
            self.logger.error(f"Invalid protocol version: 0x{protocol_version:02X}")
            return None

        # Check payload type
        if payload_type != self.PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_RESPONSE:
            self.logger.error(f"Unexpected payload type: 0x{payload_type:04X}")
            return None

        # Check payload length (should be 33 bytes for vehicle identification response)
        if payload_length != 33:
            self.logger.error(f"Invalid payload length: {payload_length}, expected 33")
            return None

        if len(data) < 8 + payload_length:
            self.logger.error("Incomplete payload data")
            return None

        # Parse payload
        payload = data[8 : 8 + payload_length]

        # Vehicle Identification Response payload structure:
        # VIN (17 bytes) + Logical Address (2 bytes) + EID (6 bytes) +
        # GID (6 bytes) + Further Action Required (1 byte) + VIN/GID Sync Status (1 byte)
        vin = payload[0:17].decode("ascii", errors="ignore")
        logical_address = struct.unpack(">H", payload[17:19])[0]
        eid = payload[19:25].hex().upper()
        gid = payload[25:31].hex().upper()
        further_action_required = payload[31]
        vin_gid_sync_status = payload[32]

        return {
            "vin": vin,
            "logical_address": logical_address,
            "eid": eid,
            "gid": gid,
            "further_action_required": further_action_required,
            "vin_gid_sync_status": vin_gid_sync_status,
        }

    def start(self) -> bool:
        """
        Start the UDP client and bind to a local port.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Only enable broadcast if using broadcast address
            if self.server_host == "255.255.255.255":
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                self.logger.info("UDP client configured for broadcast mode")
            else:
                self.logger.info(
                    f"UDP client configured for unicast mode to {self.server_host}"
                )

            self.socket.settimeout(self.timeout)

            # Bind to any available port
            self.socket.bind(("", 0))
            local_port = self.socket.getsockname()[1]

            self.logger.info(f"UDP DoIP client started on port {local_port}")

            # Test that we can actually send data
            try:
                test_data = b"test"
                self.socket.sendto(test_data, (self.server_host, self.server_port))
                self.logger.debug("UDP client test send successful")
            except Exception as e:
                self.logger.warning(f"UDP client test send failed: {e}")
                # Don't fail startup for this, but log it

            return True

        except Exception as e:
            self.logger.error(f"Failed to start UDP client: {e}")
            return False

    def stop(self):
        """Stop the UDP client and close the socket."""
        if self.socket:
            self.socket.close()
            self.socket = None
            self.logger.info("UDP DoIP client stopped")

    def send_vehicle_identification_request(self) -> Optional[dict]:
        """
        Send a vehicle identification request and wait for response.

        Returns:
            dict: Parsed response data or None if failed
        """
        if not self.socket:
            self.logger.error("Client not started")
            return None

        try:
            # Create request message
            request = self.create_vehicle_identification_request()

            self.logger.info(
                f"Sending vehicle identification request to "
                f"{self.server_host}:{self.server_port}"
            )
            self.logger.debug(f"Request: {request.hex()}")

            # Send request
            bytes_sent = self.socket.sendto(
                request, (self.server_host, self.server_port)
            )
            self.logger.debug(f"Sent {bytes_sent} bytes")

            # Wait for response
            self.logger.info("Waiting for vehicle identification response...")
            data, addr = self.socket.recvfrom(1024)

            self.logger.info(f"Received response from {addr} ({len(data)} bytes)")
            self.logger.debug(f"Response: {data.hex()}")

            # Parse response
            response_data = self.parse_vehicle_identification_response(data)
            if response_data:
                self.logger.info("Vehicle identification response parsed successfully")
                self.logger.info(f"VIN: {response_data['vin']}")
                self.logger.info(
                    f"Logical Address: 0x{response_data['logical_address']:04X}"
                )
                self.logger.info(f"EID: {response_data['eid']}")
                self.logger.info(f"GID: {response_data['gid']}")
                self.logger.info(
                    f"Further Action Required: {response_data['further_action_required']}"
                )
                self.logger.info(
                    f"VIN/GID Sync Status: {response_data['vin_gid_sync_status']}"
                )
            else:
                self.logger.error("Failed to parse vehicle identification response")

            return response_data

        except socket.timeout:
            self.logger.warning("Timeout waiting for vehicle identification response")
            return None
        except Exception as e:
            self.logger.error(f"Error sending vehicle identification request: {e}")
            return None

    def send_entity_status_request(self) -> Optional[dict]:
        """
        Send an entity status request and wait for response.

        Returns:
            dict: Parsed response data or None if failed
        """
        if not self.socket:
            self.logger.error("Client not started")
            return None

        try:
            # Create request message
            request = self.create_entity_status_request()

            self.logger.info(
                f"Sending entity status request to "
                f"{self.server_host}:{self.server_port}"
            )
            self.logger.debug(f"Request: {request.hex()}")

            # Send request
            bytes_sent = self.socket.sendto(
                request, (self.server_host, self.server_port)
            )
            self.logger.debug(f"Sent {bytes_sent} bytes")

            # Wait for response
            self.logger.info("Waiting for entity status response...")
            data, addr = self.socket.recvfrom(1024)

            self.logger.info(f"Received response from {addr} ({len(data)} bytes)")
            self.logger.debug(f"Response: {data.hex()}")

            # Parse response
            response_data = self.parse_entity_status_response(data)
            if response_data:
                self.logger.info("Entity status response parsed successfully")
                self.logger.info(f"Node Type: 0x{response_data['node_type']:02X}")
                self.logger.info(
                    f"Max Open Sockets: {response_data['max_open_sockets']}"
                )
                self.logger.info(
                    f"Current Open Sockets: {response_data['current_open_sockets']}"
                )
                self.logger.info(
                    f"DoIP Entity Status: 0x{response_data['doip_entity_status']:02X}"
                )
                self.logger.info(
                    f"Diagnostic Power Mode: 0x{response_data['diagnostic_power_mode']:02X}"
                )
            else:
                self.logger.error("Failed to parse entity status response")

            return response_data

        except socket.timeout:
            self.logger.warning("Timeout waiting for entity status response")
            return None
        except Exception as e:
            self.logger.error(f"Error sending entity status request: {e}")
            return None

    def send_power_mode_information_request(self) -> Optional[dict]:
        """
        Send a power mode information request and wait for response.

        Returns:
            dict: Parsed response data or None if failed
        """
        if not self.socket:
            self.logger.error("Client not started")
            return None

        try:
            # Create request message
            request = self.create_power_mode_information_request()

            self.logger.info(
                f"Sending power mode information request to "
                f"{self.server_host}:{self.server_port}"
            )
            self.logger.debug(f"Request: {request.hex()}")

            # Send request
            bytes_sent = self.socket.sendto(
                request, (self.server_host, self.server_port)
            )
            self.logger.debug(f"Sent {bytes_sent} bytes")

            # Wait for response
            self.logger.info("Waiting for power mode information response...")
            data, addr = self.socket.recvfrom(1024)

            self.logger.info(f"Received response from {addr} ({len(data)} bytes)")
            self.logger.debug(f"Response: {data.hex()}")

            # Parse response
            response_data = self.parse_power_mode_information_response(data)
            if response_data:
                self.logger.info("Power mode information response parsed successfully")
                self.logger.info(
                    f"Power Mode Status: 0x{response_data['power_mode_status']:02X}"
                )
            else:
                self.logger.error("Failed to parse power mode information response")

            return response_data

        except socket.timeout:
            self.logger.warning("Timeout waiting for power mode information response")
            return None
        except Exception as e:
            self.logger.error(f"Error sending power mode information request: {e}")
            return None

    def send_raw_request(self, request_data: bytes) -> Optional[bytes]:
        """
        Send a raw request and wait for response.

        Args:
            request_data: Raw request bytes to send

        Returns:
            bytes: Raw response data or None if failed
        """
        if not self.socket:
            self.logger.error("Client not started")
            return None

        try:
            self.logger.info(
                f"Sending raw request to {self.server_host}:{self.server_port}"
            )
            self.logger.debug(f"Request: {request_data.hex()}")

            # Send request
            bytes_sent = self.socket.sendto(
                request_data, (self.server_host, self.server_port)
            )
            self.logger.debug(f"Sent {bytes_sent} bytes")

            # Wait for response
            self.logger.info("Waiting for response...")
            data, addr = self.socket.recvfrom(1024)

            self.logger.info(f"Received response from {addr} ({len(data)} bytes)")
            self.logger.debug(f"Response: {data.hex()}")

            return data

        except socket.timeout:
            self.logger.warning("Timeout waiting for response")
            return None
        except Exception as e:
            self.logger.error(f"Error sending raw request: {e}")
            return None

    def run_test(self, num_requests: int = 1, delay: float = 1.0) -> list:
        """
        Run vehicle identification test with multiple requests.

        Args:
            num_requests: Number of requests to send
            delay: Delay between requests in seconds

        Returns:
            list: List of response data dictionaries
        """
        if not self.start():
            return []

        responses = []

        try:
            for i in range(num_requests):
                self.logger.info(
                    f"\n=== Vehicle Identification Request {i+1}/{num_requests} ==="
                )

                response = self.send_vehicle_identification_request()
                if response:
                    responses.append(response)
                else:
                    self.logger.warning(f"Request {i+1} failed")

                if i < num_requests - 1:  # Don't delay after last request
                    time.sleep(delay)

        finally:
            self.stop()

        self.logger.info("\n=== Test Complete ===")
        self.logger.info(f"Successful responses: {len(responses)}/{num_requests}")

        return responses


def main():
    """Main entry point for testing the UDP DoIP client."""
    import argparse

    parser = argparse.ArgumentParser(
        description="UDP DoIP Client for Vehicle Identification Testing"
    )
    parser.add_argument(
        "--port", type=int, default=13400, help="UDP port to send requests to"
    )
    parser.add_argument(
        "--timeout", type=float, default=5.0, help="Response timeout in seconds"
    )
    parser.add_argument(
        "--requests", type=int, default=1, help="Number of requests to send"
    )
    parser.add_argument(
        "--delay", type=float, default=1.0, help="Delay between requests in seconds"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Create and run client
    client = UDPDoIPClient(server_port=args.port, timeout=args.timeout)
    responses = client.run_test(num_requests=args.requests, delay=args.delay)

    # Print summary
    if responses:
        print("\n=== Summary ===")
        for i, response in enumerate(responses):
            print(
                f"Response {i+1}: VIN={response['vin']}, "
                f"Address=0x{response['logical_address']:04X}"
            )
    else:
        print("No responses received")


if __name__ == "__main__":
    main()
