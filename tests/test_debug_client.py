#!/usr/bin/env python3
"""
Test module for DebugDoIPClient
"""

import json
import pytest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from doip_client.debug_client import DebugDoIPClient


class TestDebugDoIPClient:
    """Test cases for DebugDoIPClient"""

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing"""
        return {
            "server": {"host": "127.0.0.1", "port": 13400, "timeout": 5.0},
            "client": {"logical_address": "0x0E00", "target_address": "0x1000"},
            "debug": {"log_level": "INFO", "log_file": None},
            "uds_services": {
                "diagnostic_session_control": {"session_type": "0x03"},
                "read_data_by_identifier": {"data_identifiers": ["0xF190", "0xF191"]},
                "routine_control": {
                    "routine_identifier": "0x0202",
                    "routine_type": "0x01",
                },
            },
            "test_scenarios": [
                {
                    "name": "basic_connection",
                    "description": "Basic connection test",
                    "steps": ["connect", "alive_check", "disconnect"],
                },
                {
                    "name": "diagnostic_test",
                    "description": "Diagnostic message test",
                    "steps": [
                        "connect",
                        "diagnostic_session_control",
                        "read_data_by_identifier",
                        "disconnect",
                    ],
                },
            ],
        }

    @pytest.fixture
    def temp_config_file(self, sample_config):
        """Create a temporary config file for testing"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_config, f)
            temp_file = f.name
        yield temp_file
        os.unlink(temp_file)

    def test_debug_client_initialization(self, temp_config_file):
        """Test DebugDoIPClient initialization"""
        with patch("doip_client.debug_client.DoIPClient"):
            client = DebugDoIPClient(temp_config_file)

            assert client.server_host == "127.0.0.1"
            assert client.server_port == 13400
            assert client.timeout == 5.0
            assert client.logical_address == 0x0E00
            assert client.target_address == 0x1000
            assert client.doip_client is None

    def test_debug_client_initialization_default_config(self):
        """Test DebugDoIPClient initialization with default config file"""
        # Create a default config file
        default_config = {
            "server": {"host": "127.0.0.1", "port": 13400, "timeout": 5.0},
            "client": {"logical_address": "0x0E00", "target_address": "0x1000"},
            "debug": {"log_level": "INFO", "log_file": None},
            "uds_services": {
                "diagnostic_session_control": {"session_type": "0x03"},
                "read_data_by_identifier": {"data_identifiers": ["0xF190"]},
                "routine_control": {
                    "routine_identifier": "0x0202",
                    "routine_type": "0x01",
                },
            },
            "test_scenarios": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(default_config, f)
            temp_file = f.name

        try:
            with patch("doip_client.debug_client.DoIPClient"):
                client = DebugDoIPClient(temp_file)
                assert client.server_host == "127.0.0.1"
        finally:
            os.unlink(temp_file)

    def test_debug_client_config_file_not_found(self):
        """Test DebugDoIPClient with non-existent config file"""
        with pytest.raises(FileNotFoundError):
            DebugDoIPClient("non_existent_config.json")

    def test_load_config(self, temp_config_file, sample_config):
        """Test _load_config method"""
        with patch("doip_client.debug_client.DoIPClient"):
            client = DebugDoIPClient(temp_config_file)
            assert client.config == sample_config

    def test_setup_logging(self, temp_config_file):
        """Test _setup_logging method"""
        with patch("doip_client.debug_client.DoIPClient"):
            client = DebugDoIPClient(temp_config_file)
            assert client.logger is not None
            assert client.logger.name == "debug_doip_client"

    def test_setup_logging_with_file(self, sample_config):
        """Test _setup_logging method with log file"""
        sample_config["debug"]["log_file"] = "test.log"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_config, f)
            temp_file = f.name

        try:
            with patch("doip_client.debug_client.DoIPClient"):
                client = DebugDoIPClient(temp_file)
                assert client.logger is not None
                assert len(client.logger.handlers) == 2  # Console + File handler
        finally:
            os.unlink(temp_file)
            if os.path.exists("test.log"):
                os.unlink("test.log")

    @patch("doip_client.debug_client.DoIPClient")
    def test_connect_success(self, mock_doip_client, temp_config_file):
        """Test successful connection"""
        mock_client_instance = Mock()
        mock_doip_client.return_value = mock_client_instance

        client = DebugDoIPClient(temp_config_file)
        result = client.connect()

        assert result is True
        assert client.doip_client == mock_client_instance
        mock_doip_client.assert_called_once_with("127.0.0.1", 0x1000)

    @patch("doip_client.debug_client.DoIPClient")
    def test_connect_failure(self, mock_doip_client, temp_config_file):
        """Test connection failure"""
        mock_doip_client.side_effect = Exception("Connection failed")

        client = DebugDoIPClient(temp_config_file)
        result = client.connect()

        assert result is False
        assert client.doip_client is None

    def test_disconnect_with_client(self, temp_config_file):
        """Test disconnect with active client"""
        mock_client = Mock()

        with patch("doip_client.debug_client.DoIPClient"):
            client = DebugDoIPClient(temp_config_file)
            client.doip_client = mock_client
            client.disconnect()

            mock_client.close.assert_called_once()
            assert client.doip_client is None

    def test_disconnect_without_client(self, temp_config_file):
        """Test disconnect without active client"""
        with patch("doip_client.debug_client.DoIPClient"):
            client = DebugDoIPClient(temp_config_file)
            client.doip_client = None
            client.disconnect()  # Should not raise exception

    @patch("doip_client.debug_client.DoIPClient")
    def test_send_diagnostic_message_success(self, mock_doip_client, temp_config_file):
        """Test successful diagnostic message sending"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x01\x02\x03"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DebugDoIPClient(temp_config_file)
        client.doip_client = mock_client_instance

        result = client.send_diagnostic_message([0x22, 0xF1, 0x90])

        assert result == b"\x62\xf1\x90\x01\x02\x03"
        mock_client_instance.send_diagnostic_message.assert_called_once()

    def test_send_diagnostic_message_not_connected(self, temp_config_file):
        """Test diagnostic message sending without connection"""
        with patch("doip_client.debug_client.DoIPClient"):
            client = DebugDoIPClient(temp_config_file)
            client.doip_client = None

            result = client.send_diagnostic_message([0x22, 0xF1, 0x90])
            assert result is None

    @patch("doip_client.debug_client.DoIPClient")
    def test_send_diagnostic_message_with_bytes(
        self, mock_doip_client, temp_config_file
    ):
        """Test diagnostic message sending with bytes payload"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x01\x02\x03"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DebugDoIPClient(temp_config_file)
        client.doip_client = mock_client_instance

        result = client.send_diagnostic_message(b"\x22\xf1\x90")

        assert result == b"\x62\xf1\x90\x01\x02\x03"
        mock_client_instance.send_diagnostic_message.assert_called_once()

    @patch("doip_client.debug_client.DoIPClient")
    def test_send_diagnostic_message_exception(
        self, mock_doip_client, temp_config_file
    ):
        """Test diagnostic message sending with exception"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.side_effect = Exception(
            "Send failed"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DebugDoIPClient(temp_config_file)
        client.doip_client = mock_client_instance

        result = client.send_diagnostic_message([0x22, 0xF1, 0x90])
        assert result is None

    @patch("doip_client.debug_client.DoIPClient")
    def test_send_alive_check_success(self, mock_doip_client, temp_config_file):
        """Test successful alive check"""
        mock_client_instance = Mock()
        mock_client_instance.send_alive_check.return_value = "Alive response"
        mock_doip_client.return_value = mock_client_instance

        client = DebugDoIPClient(temp_config_file)
        client.doip_client = mock_client_instance

        result = client.send_alive_check()
        assert result == "Alive response"

    def test_send_alive_check_not_connected(self, temp_config_file):
        """Test alive check without connection"""
        with patch("doip_client.debug_client.DoIPClient"):
            client = DebugDoIPClient(temp_config_file)
            client.doip_client = None

            result = client.send_alive_check()
            assert result is None

    @patch("doip_client.debug_client.DoIPClient")
    def test_send_alive_check_exception(self, mock_doip_client, temp_config_file):
        """Test alive check with exception"""
        mock_client_instance = Mock()
        mock_client_instance.send_alive_check.side_effect = Exception(
            "Alive check failed"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DebugDoIPClient(temp_config_file)
        client.doip_client = mock_client_instance

        result = client.send_alive_check()
        assert result is None

    @patch("doip_client.debug_client.DoIPClient")
    def test_run_test_scenario_connect(self, mock_doip_client, temp_config_file):
        """Test running test scenario with connect step"""
        mock_client_instance = Mock()
        mock_doip_client.return_value = mock_client_instance

        client = DebugDoIPClient(temp_config_file)

        result = client.run_test_scenario("basic_connection")
        assert result is True

    @patch("doip_client.debug_client.DoIPClient")
    def test_run_test_scenario_connect_failure(
        self, mock_doip_client, temp_config_file
    ):
        """Test running test scenario with connect failure"""
        mock_doip_client.side_effect = Exception("Connection failed")

        client = DebugDoIPClient(temp_config_file)

        result = client.run_test_scenario("basic_connection")
        assert result is False

    @patch("doip_client.debug_client.DoIPClient")
    def test_run_test_scenario_diagnostic_session_control(
        self, mock_doip_client, temp_config_file
    ):
        """Test running test scenario with diagnostic session control step"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = b"\x50\x03"
        mock_doip_client.return_value = mock_client_instance

        client = DebugDoIPClient(temp_config_file)
        client.doip_client = mock_client_instance

        result = client.run_test_scenario("diagnostic_test")
        assert result is True

    @patch("doip_client.debug_client.DoIPClient")
    def test_run_test_scenario_read_data_by_identifier(
        self, mock_doip_client, temp_config_file
    ):
        """Test running test scenario with read data by identifier step"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x01\x02\x03"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DebugDoIPClient(temp_config_file)
        client.doip_client = mock_client_instance

        result = client.run_test_scenario("diagnostic_test")
        assert result is True

    @patch("doip_client.debug_client.DoIPClient")
    def test_run_test_scenario_routine_control(
        self, mock_doip_client, temp_config_file, sample_config
    ):
        """Test running test scenario with routine control step"""
        # Add routine control to test scenario
        config = sample_config.copy()
        config["test_scenarios"][0]["steps"].append("routine_control")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            temp_file = f.name

        try:
            mock_client_instance = Mock()
            mock_client_instance.send_diagnostic_message.return_value = (
                b"\x71\x01\x02\x02\x01"
            )
            mock_doip_client.return_value = mock_client_instance

            client = DebugDoIPClient(temp_file)
            client.doip_client = mock_client_instance

            result = client.run_test_scenario("basic_connection")
            assert result is True
        finally:
            os.unlink(temp_file)

    @patch("doip_client.debug_client.DoIPClient")
    def test_run_test_scenario_tester_present(
        self, mock_doip_client, temp_config_file, sample_config
    ):
        """Test running test scenario with tester present step"""
        # Add tester present to test scenario
        config = sample_config.copy()
        config["test_scenarios"][0]["steps"].append("tester_present")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            temp_file = f.name

        try:
            mock_client_instance = Mock()
            mock_client_instance.send_diagnostic_message.return_value = b"\x7e\x00"
            mock_doip_client.return_value = mock_client_instance

            client = DebugDoIPClient(temp_file)
            client.doip_client = mock_client_instance

            result = client.run_test_scenario("basic_connection")
            assert result is True
        finally:
            os.unlink(temp_file)

    @patch("doip_client.debug_client.DoIPClient")
    def test_run_test_scenario_invalid_uds_request(
        self, mock_doip_client, temp_config_file, sample_config
    ):
        """Test running test scenario with invalid UDS request step"""
        # Add invalid UDS request to test scenario
        config = sample_config.copy()
        config["test_scenarios"][0]["steps"].append("invalid_uds_request")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            temp_file = f.name

        try:
            mock_client_instance = Mock()
            mock_client_instance.send_diagnostic_message.return_value = None
            mock_doip_client.return_value = mock_client_instance

            client = DebugDoIPClient(temp_file)
            client.doip_client = mock_client_instance

            result = client.run_test_scenario("basic_connection")
            assert result is True
        finally:
            os.unlink(temp_file)

    @patch("doip_client.debug_client.DoIPClient")
    def test_run_test_scenario_reconnect(
        self, mock_doip_client, temp_config_file, sample_config
    ):
        """Test running test scenario with reconnect step"""
        # Add reconnect to test scenario
        config = sample_config.copy()
        config["test_scenarios"][0]["steps"].append("reconnect")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            temp_file = f.name

        try:
            mock_client_instance = Mock()
            mock_doip_client.return_value = mock_client_instance

            client = DebugDoIPClient(temp_file)

            result = client.run_test_scenario("basic_connection")
            assert result is True
        finally:
            os.unlink(temp_file)

    @patch("doip_client.debug_client.DoIPClient")
    def test_run_test_scenario_valid_uds_request(
        self, mock_doip_client, temp_config_file, sample_config
    ):
        """Test running test scenario with valid UDS request step"""
        # Add valid UDS request to test scenario
        config = sample_config.copy()
        config["test_scenarios"][0]["steps"].append("valid_uds_request")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            temp_file = f.name

        try:
            mock_client_instance = Mock()
            mock_client_instance.send_diagnostic_message.return_value = b"\x7e\x00"
            mock_doip_client.return_value = mock_client_instance

            client = DebugDoIPClient(temp_file)
            client.doip_client = mock_client_instance

            result = client.run_test_scenario("basic_connection")
            assert result is True
        finally:
            os.unlink(temp_file)

    def test_run_test_scenario_not_found(self, temp_config_file):
        """Test running non-existent test scenario"""
        with patch("doip_client.debug_client.DoIPClient"):
            client = DebugDoIPClient(temp_config_file)

            result = client.run_test_scenario("non_existent_scenario")
            assert result is False

    def test_run_test_scenario_unknown_step(self, temp_config_file, sample_config):
        """Test running test scenario with unknown step"""
        # Add unknown step to test scenario
        config = sample_config.copy()
        config["test_scenarios"][0]["steps"].append("unknown_step")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config, f)
            temp_file = f.name

        try:
            with patch("doip_client.debug_client.DoIPClient"):
                client = DebugDoIPClient(temp_file)

                result = client.run_test_scenario("basic_connection")
                assert result is True  # Should continue despite unknown step
        finally:
            os.unlink(temp_file)

    @patch("doip_client.debug_client.DoIPClient")
    def test_run_all_tests(self, mock_doip_client, temp_config_file):
        """Test running all test scenarios"""
        mock_client_instance = Mock()
        mock_doip_client.return_value = mock_client_instance

        client = DebugDoIPClient(temp_config_file)

        results = client.run_all_tests()

        assert isinstance(results, dict)
        assert "basic_connection" in results
        assert "diagnostic_test" in results
        assert all(isinstance(success, bool) for success in results.values())

    @patch("doip_client.debug_client.DoIPClient")
    def test_run_all_tests_with_exception(self, mock_doip_client, temp_config_file):
        """Test running all test scenarios with exception"""
        mock_doip_client.side_effect = Exception("Test failed")

        client = DebugDoIPClient(temp_config_file)

        results = client.run_all_tests()

        assert isinstance(results, dict)
        assert all(success is False for success in results.values())

    @patch("doip_client.debug_client.DebugDoIPClient")
    def test_main_function_success(self, mock_client_class, temp_config_file):
        """Test main function with successful execution"""
        mock_client = Mock()
        mock_client.run_all_tests.return_value = {"test1": True, "test2": True}
        mock_client_class.return_value = mock_client

        from doip_client.debug_client import main

        with patch("doip_client.debug_client.DebugDoIPClient", mock_client_class):
            exit_code = main()
            assert exit_code == 0

    @patch("doip_client.debug_client.DebugDoIPClient")
    def test_main_function_failure(self, mock_client_class, temp_config_file):
        """Test main function with failed execution"""
        mock_client = Mock()
        mock_client.run_all_tests.return_value = {"test1": True, "test2": False}
        mock_client_class.return_value = mock_client

        from doip_client.debug_client import main

        with patch("doip_client.debug_client.DebugDoIPClient", mock_client_class):
            exit_code = main()
            assert exit_code == 1

    @patch("doip_client.debug_client.DebugDoIPClient")
    def test_main_function_exception(self, mock_client_class, temp_config_file):
        """Test main function with exception"""
        mock_client_class.side_effect = Exception("Initialization failed")

        from doip_client.debug_client import main

        with patch("doip_client.debug_client.DebugDoIPClient", mock_client_class):
            exit_code = main()
            assert exit_code == 1
