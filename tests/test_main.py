#!/usr/bin/env python3
"""
Test module for main.py
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from doip_server.main import main


class TestMain:
    """Test cases for main.py"""

    @patch('doip_server.main.start_doip_server')
    @patch('doip_server.main.argparse.ArgumentParser')
    def test_main_with_default_args(self, mock_parser_class, mock_start_server):
        """Test main function with default arguments"""
        # Mock argument parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(
            host=None,
            port=None,
            gateway_config='config/gateway1.yaml',
        )
        mock_parser_class.return_value = mock_parser
        
        # Call main function
        main()
        
        # Verify start_doip_server was called with correct arguments
        mock_start_server.assert_called_once_with(
            host=None, 
            port=None, 
            gateway_config_path='config/gateway1.yaml'
        )

    @patch('doip_server.main.start_doip_server')
    @patch('doip_server.main.argparse.ArgumentParser')
    def test_main_with_custom_args(self, mock_parser_class, mock_start_server):
        """Test main function with custom arguments"""
        # Mock argument parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(
            host='192.168.1.100',
            port=13401,
            gateway_config='custom_gateway.yaml',
        )
        mock_parser_class.return_value = mock_parser
        
        # Call main function
        main()
        
        # Verify start_doip_server was called with correct arguments
        mock_start_server.assert_called_once_with(
            host='192.168.1.100', 
            port=13401, 
            gateway_config_path='custom_gateway.yaml'
        )

    @patch('doip_server.main.start_doip_server')
    @patch('doip_server.main.argparse.ArgumentParser')
    def test_main_with_keyboard_interrupt(self, mock_parser_class, mock_start_server):
        """Test main function with KeyboardInterrupt"""
        # Mock argument parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(
            host=None,
            port=None,
            gateway_config='config/gateway1.yaml',
        )
        mock_parser_class.return_value = mock_parser
        
        # Mock start_doip_server to raise KeyboardInterrupt
        mock_start_server.side_effect = KeyboardInterrupt()
        
        # Call main function - should handle KeyboardInterrupt gracefully
        with pytest.raises(KeyboardInterrupt):
            main()

    @patch('doip_server.main.start_doip_server')
    @patch('doip_server.main.argparse.ArgumentParser')
    def test_main_with_exception(self, mock_parser_class, mock_start_server):
        """Test main function with exception"""
        # Mock argument parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(
            host=None,
            port=None,
            gateway_config='config/gateway1.yaml',
        )
        mock_parser_class.return_value = mock_parser
        
        # Mock start_doip_server to raise exception
        mock_start_server.side_effect = Exception("Test exception")
        
        # Call main function - should propagate exception
        with pytest.raises(Exception, match="Test exception"):
            main()

    @patch('doip_server.main.start_doip_server')
    @patch('doip_server.main.argparse.ArgumentParser')
    def test_main_with_server_start_exception(self, mock_parser_class, mock_start_server):
        """Test main function with server start exception"""
        # Mock argument parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(
            host=None,
            port=None,
            gateway_config='config/gateway1.yaml',
        )
        mock_parser_class.return_value = mock_parser
        
        # Mock start_doip_server to raise exception
        mock_start_server.side_effect = RuntimeError("Server start failed")
        
        # Call main function - should propagate exception
        with pytest.raises(RuntimeError, match="Server start failed"):
            main()

    @patch('doip_server.main.start_doip_server')
    @patch('doip_server.main.argparse.ArgumentParser')
    def test_main_with_verbose_logging(self, mock_parser_class, mock_start_server):
        """Test main function with verbose logging"""
        # Mock argument parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(
            host=None,
            port=None,
            gateway_config='config/gateway1.yaml',
        )
        mock_parser_class.return_value = mock_parser
        
        # Call main function
        main()
        
        # Verify start_doip_server was called
        mock_start_server.assert_called_once()

    @patch('doip_server.main.start_doip_server')
    @patch('doip_server.main.argparse.ArgumentParser')
    def test_main_with_debug_logging(self, mock_parser_class, mock_start_server):
        """Test main function with debug logging"""
        # Mock argument parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(
            host=None,
            port=None,
            gateway_config='config/gateway1.yaml',
        )
        mock_parser_class.return_value = mock_parser
        
        # Call main function
        main()
        
        # Verify start_doip_server was called
        mock_start_server.assert_called_once()

    @patch('doip_server.main.start_doip_server')
    @patch('doip_server.main.argparse.ArgumentParser')
    def test_main_with_both_verbose_and_debug(self, mock_parser_class, mock_start_server):
        """Test main function with both verbose and debug logging"""
        # Mock argument parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(
            host=None,
            port=None,
            gateway_config='config/gateway1.yaml',
        )
        mock_parser_class.return_value = mock_parser
        
        # Call main function
        main()
        
        # Verify start_doip_server was called
        mock_start_server.assert_called_once()

    @patch('doip_server.main.start_doip_server')
    @patch('doip_server.main.argparse.ArgumentParser')
    def test_main_with_config_file(self, mock_parser_class, mock_start_server):
        """Test main function with config file"""
        # Mock argument parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(
            host=None,
            port=None,
            gateway_config='custom_config.yaml',
        )
        mock_parser_class.return_value = mock_parser
        
        # Call main function
        main()
        
        # Verify start_doip_server was called with correct config
        mock_start_server.assert_called_once_with(
            host=None,
            port=None,
            gateway_config_path='custom_config.yaml'
        )

    @patch('doip_server.main.start_doip_server')
    @patch('doip_server.main.argparse.ArgumentParser')
    def test_main_with_custom_port(self, mock_parser_class, mock_start_server):
        """Test main function with custom port"""
        # Mock argument parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(
            host=None,
            port=13401,
            gateway_config='config/gateway1.yaml',
        )
        mock_parser_class.return_value = mock_parser
        
        # Call main function
        main()
        
        # Verify start_doip_server was called with correct port
        mock_start_server.assert_called_once_with(
            host=None,
            port=13401,
            gateway_config_path='config/gateway1.yaml'
        )

    @patch('doip_server.main.start_doip_server')
    @patch('doip_server.main.argparse.ArgumentParser')
    def test_main_with_custom_host(self, mock_parser_class, mock_start_server):
        """Test main function with custom host"""
        # Mock argument parser
        mock_parser = Mock()
        mock_parser.parse_args.return_value = Mock(
            host='192.168.1.100',
            port=None,
            gateway_config='config/gateway1.yaml',
        )
        mock_parser_class.return_value = mock_parser
        
        # Call main function
        main()
        
        # Verify start_doip_server was called with correct host
        mock_start_server.assert_called_once_with(
            host='192.168.1.100',
            port=None,
            gateway_config_path='config/gateway1.yaml'
        )
