#!/usr/bin/env python3
"""
DoIP Client implementation using the doipclient library.
This provides a higher-level interface for DoIP communication.
"""

import time
from doipclient import DoIPClient


class DoIPClientWrapper:
    """
    Wrapper around the doipclient library to provide a simplified interface
    for DoIP communication with our server.
    """

    def __init__(
        self,
        server_host="127.0.0.1",
        server_port=13400,
        logical_address=0x0E00,
        target_address=0x1000,
    ):
        """
        Initialize the DoIP client wrapper.

        Args:
            server_host: IP address of the DoIP server
            server_port: Port of the DoIP server (default: 13400)
            logical_address: Logical address of this client
            target_address: Logical address of the target ECU
        """
        self.server_host = server_host
        self.server_port = server_port
        self.logical_address = logical_address
        self.target_address = target_address
        self.doip_client = None

    def connect(self):
        """Connect to the DoIP server"""
        try:
            # Create DoIP client instance
            self.doip_client = DoIPClient(
                self.server_host, self.target_address  # IP address  # Logical address
            )

            print(f"Connected to DoIP server at {self.server_host}:{self.server_port}")
            print(f"Client logical address: 0x{self.logical_address:04X}")
            print(f"Target logical address: 0x{self.target_address:04X}")

        except Exception as e:
            print(f"Failed to connect to DoIP server: {e}")
            raise

    def disconnect(self):
        """Disconnect from the DoIP server"""
        if self.doip_client:
            try:
                self.doip_client.close()
                print("Disconnected from DoIP server")
            except Exception as e:
                print(f"Error during disconnect: {e}")
            finally:
                self.doip_client = None

    def send_diagnostic_message(self, uds_payload, timeout=2.0):
        """
        Send a diagnostic message and receive response.

        Args:
            uds_payload: UDS service payload (list of bytes or bytes)
            timeout: Request timeout in seconds

        Returns:
            Response payload or None if failed
        """
        if not self.doip_client:
            print("Not connected to server")
            return None

        try:
            # Convert payload to bytes if it's a list
            if isinstance(uds_payload, list):
                uds_payload = bytes(uds_payload)

            print(f"Sending diagnostic message: {uds_payload.hex()}")

            # Send diagnostic message using doipclient
            response = self.doip_client.send_diagnostic_message(
                uds_payload, timeout=timeout
            )

            if response:
                print(f"Received response: {response.hex()}")
                return response
            else:
                print("No response received")
                return None

        except Exception as e:
            print(f"Error sending diagnostic message: {e}")
            return None

    def send_routine_identification_message(
        self, routine_identifier=0x0202, routine_type=0x0001
    ):
        """
        Send routine activation request using UDS service 0x31.

        Args:
            routine_identifier: Routine identifier (2 bytes)
            routine_type: Routine type (1 byte)

        Returns:
            Response payload or None if failed
        """
        print(f"\n=== Sending Routine Activation Request ===")
        print(f"Routine Identifier: 0x{routine_identifier:04X}")
        print(f"Routine Type: 0x{routine_type:04X}")

        # UDS Routine Control service (0x31) with Start Routine subfunction (0x01)
        uds_payload = [
            0x31,  # Routine Control service
            0x01,  # Start Routine subfunction
            (routine_identifier >> 8) & 0xFF,  # Routine ID high byte
            routine_identifier & 0xFF,  # Routine ID low byte
            routine_type & 0xFF,  # Routine type
        ]

        return self.send_diagnostic_message(uds_payload)

    def send_read_data_by_identifier(self, data_identifier):
        """
        Send UDS Read Data by Identifier request.

        Args:
            data_identifier: Data identifier (2 bytes)

        Returns:
            Response payload or None if failed
        """
        print(f"\n=== Sending UDS Read Data by Identifier Request ===")
        print(f"Data Identifier: 0x{data_identifier:04X}")

        # UDS Read Data by Identifier service (0x22)
        uds_payload = [
            0x22,  # Read Data by Identifier service
            (data_identifier >> 8) & 0xFF,  # Data ID high byte
            data_identifier & 0xFF,  # Data ID low byte
        ]

        return self.send_diagnostic_message(uds_payload)

    def send_tester_present(self):
        """
        Send UDS Tester Present request to keep the session alive.

        Returns:
            Response payload or None if failed
        """
        print(f"\n=== Sending Tester Present Request ===")

        # UDS Tester Present service (0x3E) with suppress positive response (0x00)
        uds_payload = [0x3E, 0x00]

        return self.send_diagnostic_message(uds_payload)

    def send_diagnostic_session_control(self, session_type=0x03):
        """
        Send UDS Diagnostic Session Control request.

        Args:
            session_type: Session type (default: 0x03 for extended diagnostic session)

        Returns:
            Response payload or None if failed
        """
        print(f"\n=== Sending Diagnostic Session Control Request ===")
        print(f"Session Type: 0x{session_type:02X}")

        # UDS Diagnostic Session Control service (0x10)
        uds_payload = [0x10, session_type]

        return self.send_diagnostic_message(uds_payload)

    def send_alive_check(self):
        """Send alive check request"""
        print(f"\n=== Sending Alive Check Request ===")

        try:
            if not self.doip_client:
                print("Not connected to server")
                return None

            # Use doipclient's alive check method
            response = self.doip_client.send_alive_check()

            if response:
                print(f"Alive check response: {response}")
                return response
            else:
                print("No alive check response received")
                return None

        except Exception as e:
            print(f"Error sending alive check: {e}")
            return None

    def run_demo(self):
        """Run a demonstration of DoIP functionality using the doipclient library"""
        try:
            self.connect()

            # Send alive check
            self.send_alive_check()
            time.sleep(1)

            # Send diagnostic session control to enter extended session
            self.send_diagnostic_session_control(0x03)
            time.sleep(1)

            # Send routine activation
            self.send_routine_identification_message(0x0202, 0x0001)
            time.sleep(1)

            # Send UDS Read Data by Identifier requests
            data_identifiers = [0xF187, 0xF188, 0xF189, 0xF190]  # Last one should fail
            for di in data_identifiers:
                self.send_read_data_by_identifier(di)
                time.sleep(1)

            # Send tester present to keep session alive
            self.send_tester_present()
            time.sleep(1)

        except Exception as e:
            print(f"Error during demo: {e}")
        finally:
            self.disconnect()


# Legacy compatibility functions
def start_doip_client(server_host="127.0.0.1", server_port=13400):
    """Start the DoIP client (entry point for poetry script)"""
    client = DoIPClientWrapper(server_host, server_port)
    client.run_demo()


def create_doip_request():
    """Legacy function for backward compatibility - returns a simple UDS request"""
    # Return a simple Read Data by Identifier request for VIN
    return bytes([0x22, 0xF1, 0x90])


if __name__ == "__main__":
    start_doip_client()
