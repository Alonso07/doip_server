#!/usr/bin/env python3
"""
UDP DoIP Client for Vehicle Identification Testing
This client broadcasts vehicle identification requests over UDP and receives responses.
"""

import socket
import struct
import time
import logging
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

    def __init__(self, server_port: int = 13400, timeout: float = 5.0):
        """
        Initialize the UDP DoIP client.

        Args:
            server_port: UDP port to send requests to (default: 13400)
            timeout: Timeout for receiving responses in seconds
        """
        self.server_port = server_port
        self.timeout = timeout
        self.socket = None
        self.broadcast_address = "255.255.255.255"

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

        Returns:
            bytes: Complete DoIP message with vehicle identification request
        """
        # DoIP header: protocol_version, inverse_protocol_version, payload_type, payload_length
        header = struct.pack(
            ">BBHI",
            self.DOIP_PROTOCOL_VERSION,
            self.DOIP_INVERSE_PROTOCOL_VERSION,
            self.PAYLOAD_TYPE_VEHICLE_IDENTIFICATION_REQUEST,
            0,  # No payload for vehicle identification request
        )

        return header

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
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.socket.settimeout(self.timeout)

            # Bind to any available port
            self.socket.bind(("", 0))
            local_port = self.socket.getsockname()[1]

            self.logger.info(f"UDP DoIP client started on port {local_port}")
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
                f"{self.broadcast_address}:{self.server_port}"
            )
            self.logger.debug(f"Request: {request.hex()}")

            # Send request
            self.socket.sendto(request, (self.broadcast_address, self.server_port))

            # Wait for response
            self.logger.info("Waiting for vehicle identification response...")
            data, addr = self.socket.recvfrom(1024)

            self.logger.info(f"Received response from {addr}")
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
