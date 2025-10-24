#!/usr/bin/env python3
"""
Debug DoIP Client implementation with JSON configuration and detailed logging.
This version provides extensive debugging capabilities for troubleshooting DoIP communication.
"""

import json
import logging
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from doipclient import DoIPClient


class DebugDoIPClient:
    """
    Debug version of DoIP client with extensive logging and configuration support.
    """

    def __init__(self, config_file: str = "debug_config.json"):
        """
        Initialize the debug DoIP client.

        Args:
            config_file: Path to JSON configuration file
        """
        self.config = self._load_config(config_file)
        self.doip_client = None
        self.logger = self._setup_logging()

        # Extract configuration values
        self.server_host = self.config["server"]["host"]
        self.server_port = self.config["server"]["port"]
        self.timeout = self.config["server"]["timeout"]
        self.logical_address = int(self.config["client"]["logical_address"], 16)
        self.target_address = int(self.config["client"]["target_address"], 16)

        self.logger.info("Debug DoIP Client initialized")
        self.logger.info(f"Server: {self.server_host}:{self.server_port}")
        self.logger.info(f"Client address: 0x{self.logical_address:04X}")
        self.logger.info(f"Target address: 0x{self.target_address:04X}")

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_path, "r") as f:
            config = json.load(f)

        return config

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger("debug_doip_client")
        logger.setLevel(getattr(logging, self.config["debug"]["log_level"]))

        # Clear existing handlers
        logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # File handler
        if self.config["debug"]["log_file"]:
            file_handler = logging.FileHandler(self.config["debug"]["log_file"])
            file_handler.setLevel(logging.DEBUG)

            # File formatter
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

        # Console formatter
        console_formatter = logging.Formatter(
            "%(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        return logger

    def connect(self) -> bool:
        """Connect to the DoIP server with detailed logging."""
        try:
            self.logger.info("Attempting to connect to DoIP server...")
            self.logger.debug(
                f"Connection parameters: host={self.server_host}, "
                f"target=0x{self.target_address:04X}"
            )

            # Create DoIP client instance
            self.doip_client = DoIPClient(
                self.server_host, self.target_address  # IP address  # Logical address
            )

            self.logger.info("DoIP client created successfully")
            self.logger.info(
                f"Connected to DoIP server at {self.server_host}:{self.server_port}"
            )
            self.logger.info(f"Client logical address: 0x{self.logical_address:04X}")
            self.logger.info(f"Target logical address: 0x{self.target_address:04X}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to DoIP server: {e}")
            self.logger.debug(f"Connection error details: {traceback.format_exc()}")
            return False

    def disconnect(self):
        """Disconnect from the DoIP server with logging."""
        if self.doip_client:
            try:
                self.logger.info("Disconnecting from DoIP server...")
                self.doip_client.close()
                self.logger.info("Disconnected from DoIP server")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")
                self.logger.debug(f"Disconnect error details: {traceback.format_exc()}")
            finally:
                self.doip_client = None
        else:
            self.logger.warning("No active connection to disconnect")

    def cleanup(self):
        """Clean up resources including closing file handlers."""
        # Close all logger handlers to release file handles
        for handler in self.logger.handlers:
            try:
                handler.close()
            except Exception as e:
                self.logger.debug(f"Error closing handler: {e}")
        self.logger.handlers.clear()

        # Disconnect if still connected
        self.disconnect()

    def send_diagnostic_message(
        self, uds_payload: List[int], timeout: Optional[float] = None
    ) -> Optional[bytes]:
        """
        Send a diagnostic message with detailed logging.

        Args:
            uds_payload: UDS service payload (list of bytes)
            timeout: Request timeout in seconds

        Returns:
            Response payload or None if failed
        """
        if not self.doip_client:
            self.logger.error("Not connected to server")
            return None

        if timeout is None:
            timeout = self.timeout

        try:
            # Convert payload to bytes if it's a list
            if isinstance(uds_payload, list):
                uds_payload_bytes = bytes(uds_payload)
            else:
                uds_payload_bytes = uds_payload

            self.logger.info(f"Sending diagnostic message: {uds_payload_bytes.hex()}")
            self.logger.debug(f"Payload details: {[hex(b) for b in uds_payload]}")
            self.logger.debug(f"Timeout: {timeout}s")

            # Send diagnostic message using doipclient
            response = self.doip_client.send_diagnostic_message(
                uds_payload_bytes, timeout=timeout
            )

            if response:
                self.logger.info(f"Received response: {response.hex()}")
                self.logger.debug(f"Response details: {[hex(b) for b in response]}")
                return response

            self.logger.warning("No response received")
            return None

        except Exception as e:
            self.logger.error(f"Error sending diagnostic message: {e}")
            self.logger.debug(f"Send error details: {traceback.format_exc()}")
            return None

    def send_alive_check(self) -> Optional[Any]:
        """Send alive check request with logging."""
        self.logger.info("Sending alive check request...")

        try:
            if not self.doip_client:
                self.logger.error("Not connected to server")
                return None

            # Use doipclient's alive check method
            response = self.doip_client.send_alive_check()

            if response:
                self.logger.info(f"Alive check response: {response}")
                return response

            self.logger.warning("No alive check response received")
            return None

        except Exception as e:
            self.logger.error(f"Error sending alive check: {e}")
            self.logger.debug(f"Alive check error details: {traceback.format_exc()}")
            return None

    def run_test_scenario(self, scenario_name: str) -> bool:
        """Run a specific test scenario from configuration."""
        scenarios = self.config["test_scenarios"]
        scenario = next((s for s in scenarios if s["name"] == scenario_name), None)

        if not scenario:
            self.logger.error(
                f"Test scenario '{scenario_name}' not found in configuration"
            )
            return False

        self.logger.info(f"Running test scenario: {scenario['name']}")
        self.logger.info(f"Description: {scenario['description']}")

        success = True
        for step in scenario["steps"]:
            self.logger.info(f"Executing step: {step}")

            if step == "connect":
                if not self.connect():
                    success = False
                    break

            elif step == "disconnect":
                self.disconnect()

            elif step == "alive_check":
                if not self.send_alive_check():
                    self.logger.warning("Alive check failed")

            elif step == "diagnostic_session_control":
                session_type = int(
                    self.config["uds_services"]["diagnostic_session_control"][
                        "session_type"
                    ],
                    16,
                )
                uds_payload = [0x10, session_type]
                if not self.send_diagnostic_message(uds_payload):
                    self.logger.warning("Diagnostic session control failed")

            elif step == "read_data_by_identifier":
                data_ids = self.config["uds_services"]["read_data_by_identifier"][
                    "data_identifiers"
                ]
                for data_id_str in data_ids:
                    data_id = int(data_id_str, 16)
                    uds_payload = [0x22, (data_id >> 8) & 0xFF, data_id & 0xFF]
                    if not self.send_diagnostic_message(uds_payload):
                        self.logger.warning(
                            f"Read data by identifier failed for 0x{data_id:04X}"
                        )
                    time.sleep(0.5)

            elif step == "routine_control":
                routine_id = int(
                    self.config["uds_services"]["routine_control"][
                        "routine_identifier"
                    ],
                    16,
                )
                routine_type = int(
                    self.config["uds_services"]["routine_control"]["routine_type"], 16
                )
                uds_payload = [
                    0x31,
                    0x01,
                    (routine_id >> 8) & 0xFF,
                    routine_id & 0xFF,
                    routine_type,
                ]
                if not self.send_diagnostic_message(uds_payload):
                    self.logger.warning("Routine control failed")

            elif step == "tester_present":
                uds_payload = [0x3E, 0x00]
                if not self.send_diagnostic_message(uds_payload):
                    self.logger.warning("Tester present failed")

            elif step == "invalid_uds_request":
                # Send an invalid UDS request to test error handling
                uds_payload = [0xFF, 0xFF, 0xFF]  # Invalid service
                self.send_diagnostic_message(uds_payload)

            elif step == "reconnect":
                self.disconnect()
                time.sleep(1)
                if not self.connect():
                    success = False
                    break

            elif step == "valid_uds_request":
                # Send a valid UDS request after reconnection
                uds_payload = [0x3E, 0x00]  # Tester present
                self.send_diagnostic_message(uds_payload)

            else:
                self.logger.warning(f"Unknown step: {step}")

            time.sleep(0.5)  # Small delay between steps

        self.logger.info(
            f"Test scenario '{scenario_name}' completed. Success: {success}"
        )
        return success

    def run_all_tests(self):
        """Run all configured test scenarios."""
        self.logger.info("Starting comprehensive DoIP client testing...")

        scenarios = self.config["test_scenarios"]
        results = {}

        for scenario in scenarios:
            scenario_name = scenario["name"]
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Running scenario: {scenario_name}")
            self.logger.info(f"{'='*60}")

            try:
                success = self.run_test_scenario(scenario_name)
                results[scenario_name] = success

                if success:
                    self.logger.info(f"✅ Scenario '{scenario_name}' PASSED")
                else:
                    self.logger.error(f"❌ Scenario '{scenario_name}' FAILED")

            except Exception as e:
                self.logger.error(
                    f"❌ Scenario '{scenario_name}' FAILED with exception: {e}"
                )
                self.logger.debug(f"Scenario error details: {traceback.format_exc()}")
                results[scenario_name] = False

            # Ensure clean disconnect between scenarios
            self.disconnect()
            time.sleep(1)

        # Print summary
        self.logger.info(f"\n{'='*60}")
        self.logger.info("TEST SUMMARY")
        self.logger.info(f"{'='*60}")

        passed = sum(1 for success in results.values() if success)
        total = len(results)

        for scenario_name, success in results.items():
            status = "✅ PASSED" if success else "❌ FAILED"
            self.logger.info(f"{scenario_name}: {status}")

        self.logger.info(f"\nOverall: {passed}/{total} scenarios passed")

        return results


def main():
    """Main entry point for debug client."""
    try:
        # Create debug client
        client = DebugDoIPClient()

        # Run all tests
        results = client.run_all_tests()

        # Exit with appropriate code
        all_passed = all(results.values())
        exit_code = 0 if all_passed else 1

        print(f"\nDebug client completed with exit code: {exit_code}")
        return exit_code

    except Exception as e:
        print(f"Debug client failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
