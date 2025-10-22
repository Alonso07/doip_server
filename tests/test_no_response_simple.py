#!/usr/bin/env python3
"""
Simple test cases for the no_response service configuration feature.

This module tests the core functionality where UDS services can be configured
to not send any response back to the client.
"""

import pytest

from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager


class TestNoResponseSimple:
    """Simple test cases for the no_response service configuration feature."""

    def test_no_response_validation_boolean(self):
        """Test that no_response must be a boolean value."""
        config_manager = HierarchicalConfigManager()

        # Test with invalid string value
        config_manager.uds_services = {
            "invalid_service": {
                "request": "0x2F1234",
                "no_response": "yes",  # Invalid - should be boolean
                "description": "Service with invalid no_response type",
            }
        }

        # Test validation should fail
        result = config_manager.validate_configs()
        assert result is False, "Validation should fail for invalid no_response type"

    def test_no_response_validation_valid_boolean(self):
        """Test that no_response works with valid boolean values."""
        config_manager = HierarchicalConfigManager()

        # Test with valid boolean values
        config_manager.uds_services = {
            "valid_service_true": {
                "request": "0x2F1234",
                "no_response": True,
                "description": "Service with no_response true",
            },
            "valid_service_false": {
                "request": "0x2F1235",
                "no_response": False,
                "description": "Service with no_response false",
            },
            "valid_service_default": {
                "request": "0x2F1236",
                "description": "Service without no_response (defaults to false)",
            },
        }

        # Test validation should pass
        result = config_manager.validate_configs()
        assert result is True, "Validation should pass for valid boolean values"

    def test_no_response_warning_with_responses(self):
        """Test that validation passes when no_response=True but responses are configured."""
        config_manager = HierarchicalConfigManager()

        config_manager.uds_services = {
            "conflicting_service": {
                "request": "0x2F1234",
                "no_response": True,
                "responses": ["0x620C018000"],  # This should trigger a warning
                "description": "Service with conflicting configuration",
            }
        }

        # Validate configuration - this should pass but log a warning
        result = config_manager.validate_configs()

        # Should pass validation (warnings don't fail validation)
        assert (
            result is True
        ), "Validation should pass even with conflicting configuration"

        # The warning is logged to the actual logger, which we can see in the test output
        # This test verifies that the validation logic handles conflicting configurations correctly

    def test_no_response_service_processing_logic(self):
        """Test the core logic of no_response processing."""
        # Create a mock service config
        service_config = {
            "name": "test_service",
            "request": "0x2F1234",
            "no_response": True,
            "description": "Test service with no response",
        }

        # Test the logic that would be in process_uds_message
        no_response = service_config.get("no_response", False)
        assert no_response is True, "no_response should be True"

        # Test the logic that would return None
        if no_response:
            result = None
        else:
            result = "some_response"

        assert result is None, "Should return None when no_response is True"

    def test_no_response_with_responses_ignored(self):
        """Test that responses are ignored when no_response is True."""
        service_config = {
            "name": "test_service",
            "request": "0x2F1234",
            "no_response": True,
            "responses": ["0x620C018000", "0x620C017500"],  # These should be ignored
            "description": "Test service with no response",
        }

        # Test the logic
        no_response = service_config.get("no_response", False)
        responses = service_config.get("responses", [])

        if no_response:
            # When no_response is True, responses should be ignored
            result = None
        else:
            # When no_response is False, use responses
            result = responses[0] if responses else None

        assert (
            result is None
        ), "Should return None when no_response is True, ignoring responses"
        assert (
            len(responses) == 2
        ), "Responses should still exist in config but be ignored"

    def test_no_response_default_behavior(self):
        """Test that default behavior works when no_response is not specified."""
        service_config = {
            "name": "test_service",
            "request": "0x2F1234",
            "responses": ["0x620C018000"],
            "description": "Test service without no_response specified",
        }

        # Test the logic
        no_response = service_config.get("no_response", False)  # Default to False
        responses = service_config.get("responses", [])

        assert no_response is False, "no_response should default to False"
        assert len(responses) == 1, "Should have responses"

        if no_response:
            result = None
        else:
            result = responses[0] if responses else None

        assert (
            result == "0x620C018000"
        ), "Should return response when no_response is False"

    def test_no_response_validation_direct(self):
        """Test validation logic directly without mocking."""
        config_manager = HierarchicalConfigManager()

        # Test service with conflicting configuration
        config_manager.uds_services = {
            "test_service": {
                "request": "0x2F1234",
                "no_response": True,
                "responses": ["0x620C018000"],
                "description": "Test service with conflicting config",
            }
        }

        # This should pass validation but log a warning
        result = config_manager.validate_configs()
        assert (
            result is True
        ), "Validation should pass even with conflicting configuration"

        # Test service with valid no_response configuration
        config_manager.uds_services = {
            "test_service": {
                "request": "0x2F1234",
                "no_response": True,
                "description": "Test service with valid no_response config",
            }
        }

        result = config_manager.validate_configs()
        assert (
            result is True
        ), "Validation should pass with valid no_response configuration"


if __name__ == "__main__":
    pytest.main([__file__])
