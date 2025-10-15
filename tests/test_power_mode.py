#!/usr/bin/env python3
"""
Tests for power mode functionality in DoIP server.
Tests power mode request handling, response generation, and configuration.
"""

import pytest
import struct
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from doip_server.doip_server import DoIPServer
from doip_server.hierarchical_config_manager import HierarchicalConfigManager


class TestPowerModeConfiguration:
    """Test power mode configuration loading and management"""

    def test_power_mode_config_loading(self):
        """Test that power mode configuration is properly loaded from YAML"""
        config_manager = HierarchicalConfigManager("config/gateway1.yaml")
        power_config = config_manager.get_power_mode_config()

        # Verify configuration structure
        assert isinstance(power_config, dict)
        assert "current_status" in power_config
        assert "available_statuses" in power_config
        assert "response_cycling" in power_config

        # Verify current status
        assert power_config["current_status"] == 0x0001  # Power On

        # Verify available statuses
        available_statuses = power_config["available_statuses"]
        assert len(available_statuses) == 5
        assert 0x0000 in available_statuses  # Power Off
        assert 0x0001 in available_statuses  # Power On
        assert 0x0002 in available_statuses  # Power Standby
        assert 0x0003 in available_statuses  # Power Sleep
        assert 0x0004 in available_statuses  # Power Wake

        # Verify status details
        power_on_status = available_statuses[0x0001]
        assert power_on_status["name"] == "Power On"
        assert power_on_status["description"] == "ECU is powered on and ready"

        # Verify response cycling configuration
        response_cycling = power_config["response_cycling"]
        assert response_cycling["enabled"] == False
        assert response_cycling["cycle_through"] == [0x0001, 0x0002, 0x0003]

    def test_power_mode_config_fallback(self):
        """Test power mode configuration fallback when config is missing"""
        # Create a config manager with a non-existent config file
        config_manager = HierarchicalConfigManager("non_existent_config.yaml")
        power_config = config_manager.get_power_mode_config()

        # Should return empty dict when config is missing
        assert power_config == {}

    def test_power_mode_config_with_custom_values(self):
        """Test power mode configuration with custom values"""
        # Create a temporary config file with custom power mode settings
        custom_config = {
            "gateway": {
                "name": "Test Gateway",
                "logical_address": 0x1000,
                "power_mode_status": {
                    "current_status": 0x0002,  # Power Standby
                    "available_statuses": {
                        0x0002: {
                            "name": "Custom Standby",
                            "description": "Custom standby mode",
                        }
                    },
                    "response_cycling": {"enabled": True, "cycle_through": [0x0002]},
                },
            }
        }

        # Create a config manager and manually set the config
        config_manager = HierarchicalConfigManager()
        config_manager.gateway_config = custom_config
        power_config = config_manager.get_power_mode_config()

        assert power_config["current_status"] == 0x0002
        assert power_config["response_cycling"]["enabled"] == True
        assert power_config["response_cycling"]["cycle_through"] == [0x0002]


class TestPowerModeResponseGeneration:
    """Test power mode response generation functionality"""

    def test_create_power_mode_response_default(self):
        """Test power mode response creation with default configuration"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")
        response = server.create_power_mode_response()

        # Verify response structure
        assert len(response) == 10  # 8 bytes header + 2 bytes payload

        # Verify DoIP header
        assert response[0] == 0x02  # Protocol version
        assert response[1] == 0xFD  # Inverse protocol version
        assert struct.unpack(">H", response[2:4])[0] == 0x4004  # Payload type
        assert struct.unpack(">I", response[4:8])[0] == 2  # Payload length

        # Verify power mode status (should be 0x0001 - Power On)
        power_status = struct.unpack(">H", response[8:10])[0]
        assert power_status == 0x0001

    def test_create_power_mode_response_custom_status(self):
        """Test power mode response creation with custom status"""
        # Create server with custom config
        custom_config = {
            "gateway": {
                "name": "Test Gateway",
                "logical_address": 0x1000,
                "power_mode_status": {
                    "current_status": 0x0003,  # Power Sleep
                    "available_statuses": {
                        0x0003: {
                            "name": "Power Sleep",
                            "description": "ECU is in sleep mode",
                        }
                    },
                },
            }
        }

        server = DoIPServer()
        server.config_manager.gateway_config = custom_config
        response = server.create_power_mode_response()

        # Verify power mode status (should be 0x0003 - Power Sleep)
        power_status = struct.unpack(">H", response[8:10])[0]
        assert power_status == 0x0003

    def test_create_power_mode_response_cycling_enabled(self):
        """Test power mode response creation with cycling enabled"""
        # Create server with cycling enabled
        custom_config = {
            "gateway": {
                "name": "Test Gateway",
                "logical_address": 0x1000,
                "power_mode_status": {
                    "current_status": 0x0001,
                    "available_statuses": {
                        0x0001: {
                            "name": "Power On",
                            "description": "ECU is powered on",
                        },
                        0x0002: {
                            "name": "Power Standby",
                            "description": "ECU is in standby",
                        },
                        0x0003: {
                            "name": "Power Sleep",
                            "description": "ECU is in sleep",
                        },
                    },
                    "response_cycling": {
                        "enabled": True,
                        "cycle_through": [0x0001, 0x0002, 0x0003],
                    },
                },
            }
        }

        server = DoIPServer()
        server.config_manager.gateway_config = custom_config

        # Test multiple calls to see cycling
        responses = []
        for i in range(6):  # Test 2 full cycles
            response = server.create_power_mode_response()
            power_status = struct.unpack(">H", response[8:10])[0]
            responses.append(power_status)

        # Verify cycling pattern: 0x0001, 0x0002, 0x0003, 0x0001, 0x0002, 0x0003
        expected_pattern = [0x0001, 0x0002, 0x0003, 0x0001, 0x0002, 0x0003]
        assert responses == expected_pattern

    def test_create_power_mode_response_cycling_empty_list(self):
        """Test power mode response creation with empty cycling list"""
        custom_config = {
            "gateway": {
                "name": "Test Gateway",
                "logical_address": 0x1000,
                "power_mode_status": {
                    "current_status": 0x0001,
                    "response_cycling": {
                        "enabled": True,
                        "cycle_through": [],  # Empty list
                    },
                },
            }
        }

        server = DoIPServer()
        server.config_manager.gateway_config = custom_config
        response = server.create_power_mode_response()

        # Should fall back to current_status when cycling list is empty
        power_status = struct.unpack(">H", response[8:10])[0]
        assert power_status == 0x0001

    def test_create_power_mode_response_missing_config(self):
        """Test power mode response creation when config is missing"""
        # Create server with missing power mode config
        custom_config = {
            "gateway": {
                "name": "Test Gateway",
                "logical_address": 0x1000,
                # No power_mode_status section
            }
        }

        server = DoIPServer()
        server.config_manager.gateway_config = custom_config
        response = server.create_power_mode_response()

        # Should use default status (0x0001) when config is missing
        power_status = struct.unpack(">H", response[8:10])[0]
        assert power_status == 0x0001


class TestPowerModeRequestHandling:
    """Test power mode request handling functionality"""

    def test_handle_power_mode_request(self):
        """Test power mode request handling"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Mock the create_power_mode_response method to verify it's called
        with patch.object(server, "create_power_mode_response") as mock_create:
            mock_create.return_value = b"mock_response"

            # Call handle_power_mode_request
            result = server.handle_power_mode_request(b"")

            # Verify the method was called and result returned
            mock_create.assert_called_once()
            assert result == b"mock_response"

    def test_handle_power_mode_request_with_payload(self):
        """Test power mode request handling with payload (should be ignored)"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Power mode requests don't use the payload, but we should test it doesn't break
        with patch.object(server, "create_power_mode_response") as mock_create:
            mock_create.return_value = b"mock_response"

            # Call with some payload data
            result = server.handle_power_mode_request(b"some_payload_data")

            # Verify the method was called and result returned
            mock_create.assert_called_once()
            assert result == b"mock_response"


class TestPowerModeIntegration:
    """Integration tests for power mode functionality"""

    def test_power_mode_tcp_message_handling(self):
        """Test power mode request handling through TCP message processing"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Create a power mode request (payload type 0x4003)
        power_mode_request = struct.pack(">BBHI", 0x02, 0xFD, 0x4003, 0)  # No payload

        # Process the DoIP message
        result = server.process_doip_message(power_mode_request)

        # Verify the response is a power mode response
        assert result is not None
        assert len(result) == 10  # 8 bytes header + 2 bytes payload
        assert result[0] == 0x02  # Protocol version
        assert result[1] == 0xFD  # Inverse protocol version
        assert struct.unpack(">H", result[2:4])[0] == 0x4004  # Payload type
        assert struct.unpack(">I", result[4:8])[0] == 2  # Payload length

    def test_power_mode_response_cycling_state_management(self):
        """Test power mode response cycling state management"""
        custom_config = {
            "gateway": {
                "name": "Test Gateway",
                "logical_address": 0x1000,
                "power_mode_status": {
                    "current_status": 0x0001,
                    "response_cycling": {
                        "enabled": True,
                        "cycle_through": [0x0001, 0x0002, 0x0003],
                    },
                },
            }
        }

        server = DoIPServer()
        server.config_manager.gateway_config = custom_config

        # Verify initial cycling state is empty
        cycling_state = server.get_response_cycling_state()
        assert "power_mode_power_mode_status" not in cycling_state

        # Make first call
        server.create_power_mode_response()
        cycling_state = server.get_response_cycling_state()
        assert cycling_state["power_mode_power_mode_status"] == 1

        # Make second call
        server.create_power_mode_response()
        cycling_state = server.get_response_cycling_state()
        assert cycling_state["power_mode_power_mode_status"] == 2

        # Make third call (should cycle back to 0)
        server.create_power_mode_response()
        cycling_state = server.get_response_cycling_state()
        assert cycling_state["power_mode_power_mode_status"] == 0

    def test_power_mode_logging(self):
        """Test power mode response logging"""
        server = DoIPServer(gateway_config_path="config/gateway1.yaml")

        # Capture log output
        with patch.object(server.logger, "info") as mock_log:
            server.create_power_mode_response()

            # Verify logging was called
            mock_log.assert_called()
            log_calls = [call[0][0] for call in mock_log.call_args_list]

            # Should log the power mode response
            power_mode_logs = [
                log for log in log_calls if "Power mode response:" in log
            ]
            assert len(power_mode_logs) == 1
            assert "Power On (0x0001)" in power_mode_logs[0]

    def test_power_mode_response_cycling_logging(self):
        """Test power mode response cycling logging"""
        custom_config = {
            "gateway": {
                "name": "Test Gateway",
                "logical_address": 0x1000,
                "power_mode_status": {
                    "current_status": 0x0001,
                    "response_cycling": {
                        "enabled": True,
                        "cycle_through": [0x0001, 0x0002],
                    },
                },
            }
        }

        server = DoIPServer()
        server.config_manager.gateway_config = custom_config

        # Capture log output
        with patch.object(server.logger, "info") as mock_log:
            server.create_power_mode_response()

            # Verify cycling logging was called
            log_calls = [call[0][0] for call in mock_log.call_args_list]
            cycling_logs = [
                log for log in log_calls if "Power mode response cycling:" in log
            ]
            assert len(cycling_logs) == 1
            assert "0x0001" in cycling_logs[0]


class TestPowerModeEdgeCases:
    """Test edge cases and error conditions for power mode functionality"""

    def test_power_mode_response_with_invalid_status(self):
        """Test power mode response with invalid status value"""
        custom_config = {
            "gateway": {
                "name": "Test Gateway",
                "logical_address": 0x1000,
                "power_mode_status": {
                    "current_status": 0x9999,  # Invalid status
                    "available_statuses": {
                        0x0001: {"name": "Power On", "description": "ECU is powered on"}
                    },
                },
            }
        }

        server = DoIPServer()
        server.config_manager.gateway_config = custom_config
        response = server.create_power_mode_response()

        # Should still work with invalid status
        power_status = struct.unpack(">H", response[8:10])[0]
        assert power_status == 0x9999

    def test_power_mode_response_cycling_with_single_status(self):
        """Test power mode response cycling with only one status"""
        custom_config = {
            "gateway": {
                "name": "Test Gateway",
                "logical_address": 0x1000,
                "power_mode_status": {
                    "current_status": 0x0001,
                    "response_cycling": {
                        "enabled": True,
                        "cycle_through": [0x0001],  # Only one status
                    },
                },
            }
        }

        server = DoIPServer()
        server.config_manager.gateway_config = custom_config

        # Test multiple calls - should always return the same status
        for i in range(5):
            response = server.create_power_mode_response()
            power_status = struct.unpack(">H", response[8:10])[0]
            assert power_status == 0x0001

    def test_power_mode_response_malformed_config(self):
        """Test power mode response with malformed configuration"""
        custom_config = {
            "gateway": {
                "name": "Test Gateway",
                "logical_address": 0x1000,
                "power_mode_status": {
                    # Missing current_status
                    "available_statuses": {},
                    "response_cycling": {"enabled": True, "cycle_through": [0x0001]},
                },
            }
        }

        server = DoIPServer()
        server.config_manager.gateway_config = custom_config
        response = server.create_power_mode_response()

        # Should fall back to default status (0x0001)
        power_status = struct.unpack(">H", response[8:10])[0]
        assert power_status == 0x0001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
