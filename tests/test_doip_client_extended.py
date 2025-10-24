#!/usr/bin/env python3
"""
Extended test module for DoIPClientWrapper
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from doip_client.doip_client import (
    DoIPClientWrapper,
    create_doip_request,
    start_doip_client,
)


class TestDoIPClientWrapperExtended:
    """Extended test cases for DoIPClientWrapper"""

    def test_doip_client_wrapper_initialization_defaults(self):
        """Test DoIPClientWrapper initialization with default values"""
        client = DoIPClientWrapper()

        assert client.server_host == "127.0.0.1"
        assert client.server_port == 13400
        assert client.logical_address == 0x0E00
        assert client.target_address == 0x1000
        assert client.doip_client is None

    def test_doip_client_wrapper_initialization_custom(self):
        """Test DoIPClientWrapper initialization with custom values"""
        client = DoIPClientWrapper(
            server_host="192.168.1.100",
            server_port=13401,
            logical_address=0x0E01,
            target_address=0x1001,
        )

        assert client.server_host == "192.168.1.100"
        assert client.server_port == 13401
        assert client.logical_address == 0x0E01
        assert client.target_address == 0x1001
        assert client.doip_client is None

    @patch("doip_client.doip_client.DoIPClient")
    def test_connect_success(self, mock_doip_client):
        """Test successful connection"""
        mock_client_instance = Mock()
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.connect()

        assert client.doip_client == mock_client_instance
        mock_doip_client.assert_called_once_with("127.0.0.1", 0x1000)

    @patch("doip_client.doip_client.DoIPClient")
    def test_connect_failure(self, mock_doip_client):
        """Test connection failure"""
        mock_doip_client.side_effect = Exception("Connection failed")

        client = DoIPClientWrapper()

        with pytest.raises(Exception, match="Connection failed"):
            client.connect()

    def test_disconnect_with_client(self):
        """Test disconnect with active client"""
        client = DoIPClientWrapper()
        mock_client = Mock()
        client.doip_client = mock_client

        client.disconnect()

        mock_client.close.assert_called_once()
        assert client.doip_client is None

    def test_disconnect_without_client(self):
        """Test disconnect without active client"""
        client = DoIPClientWrapper()
        client.doip_client = None

        # Should not raise exception
        client.disconnect()

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_diagnostic_message_success(self, mock_doip_client):
        """Test successful diagnostic message sending"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x01\x02\x03"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_diagnostic_message([0x22, 0xF1, 0x90])

        assert result == b"\x62\xf1\x90\x01\x02\x03"
        mock_client_instance.send_diagnostic_message.assert_called_once()

    def test_send_diagnostic_message_not_connected(self):
        """Test diagnostic message sending without connection"""
        client = DoIPClientWrapper()
        client.doip_client = None

        result = client.send_diagnostic_message([0x22, 0xF1, 0x90])
        assert result is None

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_diagnostic_message_with_bytes(self, mock_doip_client):
        """Test diagnostic message sending with bytes payload"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x01\x02\x03"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_diagnostic_message(b"\x22\xf1\x90")

        assert result == b"\x62\xf1\x90\x01\x02\x03"
        mock_client_instance.send_diagnostic_message.assert_called_once()

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_diagnostic_message_exception(self, mock_doip_client):
        """Test diagnostic message sending with exception"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.side_effect = Exception(
            "Send failed"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_diagnostic_message([0x22, 0xF1, 0x90])
        assert result is None

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_diagnostic_message_with_timeout(self, mock_doip_client):
        """Test diagnostic message sending with custom timeout"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x01\x02\x03"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_diagnostic_message([0x22, 0xF1, 0x90], timeout=5.0)

        assert result == b"\x62\xf1\x90\x01\x02\x03"
        mock_client_instance.send_diagnostic_message.assert_called_once_with(
            b"\x22\xf1\x90", timeout=5.0
        )

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_routine_activation_success(self, mock_doip_client):
        """Test successful routine activation"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = (
            b"\x71\x01\x02\x02\x01"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_routine_activation(0x0202, 0x0001)

        assert result == b"\x71\x01\x02\x02\x01"
        mock_client_instance.send_diagnostic_message.assert_called_once_with(
            b"\x31\x01\x02\x02\x01", timeout=2.0
        )

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_routine_activation_default_values(self, mock_doip_client):
        """Test routine activation with default values"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = (
            b"\x71\x01\x02\x02\x01"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_routine_activation()

        assert result == b"\x71\x01\x02\x02\x01"
        mock_client_instance.send_diagnostic_message.assert_called_once_with(
            b"\x31\x01\x02\x02\x01", timeout=2.0
        )

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_read_data_by_identifier_success(self, mock_doip_client):
        """Test successful read data by identifier"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = (
            b"\x62\xf1\x90\x01\x02\x03"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_read_data_by_identifier(0xF190)

        assert result == b"\x62\xf1\x90\x01\x02\x03"
        mock_client_instance.send_diagnostic_message.assert_called_once_with(
            b"\x22\xf1\x90", timeout=2.0
        )

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_tester_present_success(self, mock_doip_client):
        """Test successful tester present"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = b"\x7e\x00"
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_tester_present()

        assert result == b"\x7e\x00"
        mock_client_instance.send_diagnostic_message.assert_called_once_with(
            b"\x3e\x00", timeout=2.0
        )

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_diagnostic_session_control_success(self, mock_doip_client):
        """Test successful diagnostic session control"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = b"\x50\x03"
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_diagnostic_session_control(0x03)

        assert result == b"\x50\x03"
        mock_client_instance.send_diagnostic_message.assert_called_once_with(
            b"\x10\x03", timeout=2.0
        )

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_diagnostic_session_control_default_value(self, mock_doip_client):
        """Test diagnostic session control with default value"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = b"\x50\x03"
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_diagnostic_session_control()

        assert result == b"\x50\x03"
        mock_client_instance.send_diagnostic_message.assert_called_once_with(
            b"\x10\x03", timeout=2.0
        )

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_alive_check_success(self, mock_doip_client):
        """Test successful alive check"""
        mock_client_instance = Mock()
        mock_client_instance.send_alive_check.return_value = "Alive response"
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_alive_check()

        assert result == "Alive response"
        mock_client_instance.send_alive_check.assert_called_once()

    def test_send_alive_check_not_connected(self):
        """Test alive check without connection"""
        client = DoIPClientWrapper()
        client.doip_client = None

        result = client.send_alive_check()
        assert result is None

    @patch("doip_client.doip_client.DoIPClient")
    def test_send_alive_check_exception(self, mock_doip_client):
        """Test alive check with exception"""
        mock_client_instance = Mock()
        mock_client_instance.send_alive_check.side_effect = Exception(
            "Alive check failed"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        result = client.send_alive_check()
        assert result is None

    @patch("doip_client.doip_client.DoIPClient")
    def test_run_demo_success(self, mock_doip_client):
        """Test successful demo run"""
        mock_client_instance = Mock()
        mock_client_instance.send_alive_check.return_value = "Alive response"
        mock_client_instance.send_diagnostic_message.return_value = b"\x50\x03"
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()

        # Should not raise exception
        client.run_demo()

    @patch("doip_client.doip_client.DoIPClient")
    def test_run_demo_with_exception(self, mock_doip_client):
        """Test demo run with exception"""
        mock_doip_client.side_effect = Exception("Demo failed")

        client = DoIPClientWrapper()

        # Should not raise exception
        client.run_demo()

    def test_start_doip_client_function(self):
        """Test start_doip_client function"""
        with patch("doip_client.doip_client.DoIPClientWrapper") as mock_wrapper_class:
            mock_client = Mock()
            mock_wrapper_class.return_value = mock_client

            start_doip_client("192.168.1.100", 13401)

            mock_wrapper_class.assert_called_once_with("192.168.1.100", 13401)
            mock_client.run_demo.assert_called_once()

    def test_start_doip_client_function_defaults(self):
        """Test start_doip_client function with default values"""
        with patch("doip_client.doip_client.DoIPClientWrapper") as mock_wrapper_class:
            mock_client = Mock()
            mock_wrapper_class.return_value = mock_client

            start_doip_client()

            mock_wrapper_class.assert_called_once_with("127.0.0.1", 13400)
            mock_client.run_demo.assert_called_once()

    def test_create_doip_request_function(self):
        """Test create_doip_request function"""
        result = create_doip_request()

        assert result == b"\x22\xf1\x90"
        assert isinstance(result, bytes)

    def test_doip_client_wrapper_properties(self):
        """Test DoIPClientWrapper properties"""
        client = DoIPClientWrapper(
            server_host="192.168.1.100",
            server_port=13401,
            logical_address=0x0E01,
            target_address=0x1001,
        )

        # Test property access
        assert client.server_host == "192.168.1.100"
        assert client.server_port == 13401
        assert client.logical_address == 0x0E01
        assert client.target_address == 0x1001
        assert client.doip_client is None

    @patch("doip_client.doip_client.DoIPClient")
    def test_doip_client_wrapper_connection_lifecycle(self, mock_doip_client):
        """Test complete connection lifecycle"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.return_value = b"\x50\x03"
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()

        # Connect
        client.connect()
        assert client.doip_client == mock_client_instance

        # Send message
        result = client.send_diagnostic_message([0x10, 0x03])
        assert result == b"\x50\x03"

        # Disconnect
        client.disconnect()
        assert client.doip_client is None
        mock_client_instance.close.assert_called_once()

    @patch("doip_client.doip_client.DoIPClient")
    def test_doip_client_wrapper_multiple_connections(self, mock_doip_client):
        """Test multiple connection attempts"""
        mock_client_instance = Mock()
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()

        # First connection
        client.connect()
        assert client.doip_client == mock_client_instance

        # Second connection (should replace first)
        client.connect()
        assert client.doip_client == mock_client_instance
        assert mock_doip_client.call_count == 2

    @patch("doip_client.doip_client.DoIPClient")
    def test_doip_client_wrapper_error_handling(self, mock_doip_client):
        """Test error handling in various scenarios"""
        mock_client_instance = Mock()
        mock_client_instance.send_diagnostic_message.side_effect = Exception(
            "Send failed"
        )
        mock_doip_client.return_value = mock_client_instance

        client = DoIPClientWrapper()
        client.doip_client = mock_client_instance

        # Test error handling in send_diagnostic_message
        result = client.send_diagnostic_message([0x22, 0xF1, 0x90])
        assert result is None

        # Test error handling in send_routine_activation
        result = client.send_routine_activation()
        assert result is None

        # Test error handling in send_read_data_by_identifier
        result = client.send_read_data_by_identifier(0xF190)
        assert result is None

        # Test error handling in send_tester_present
        result = client.send_tester_present()
        assert result is None

        # Test error handling in send_diagnostic_session_control
        result = client.send_diagnostic_session_control()
        assert result is None
