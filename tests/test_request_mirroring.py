"""Tests for request mirroring functionality in UDS responses."""

import pytest

from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager


class TestRequestMirroring:
    """Test cases for request mirroring functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config_manager = HierarchicalConfigManager()

    def test_process_response_with_mirroring_basic(self):
        """Test basic request mirroring functionality."""
        # Test case 1: Mirror specific characters
        response_template = "0x620C{request[2:4]}"
        request = "0x220C01"
        result = self.config_manager.process_response_with_mirroring(
            response_template, request
        )
        assert result == "0x620C0C"

    def test_process_response_with_mirroring_slice(self):
        """Test request mirroring with slice notation."""
        # Test case 2: Mirror characters from start to end
        response_template = "0x620C{request[2:6]}"
        request = "0x220C01"
        result = self.config_manager.process_response_with_mirroring(
            response_template, request
        )
        assert result == "0x620C0C01"

    def test_process_response_with_mirroring_single_byte(self):
        """Test request mirroring with single character."""
        # Test case 3: Mirror single character
        response_template = "0x620C{request[2]}"
        request = "0x220C01"
        result = self.config_manager.process_response_with_mirroring(
            response_template, request
        )
        assert result == "0x620C0"

    def test_process_response_with_mirroring_multiple_parts(self):
        """Test request mirroring with multiple parts."""
        # Test case 4: Mirror multiple parts
        response_template = "0x620C{request[2:4]}{request[6:8]}"
        request = "0x220C01FF"
        result = self.config_manager.process_response_with_mirroring(
            response_template, request
        )
        assert result == "0x620C0CFF"

    def test_process_response_with_mirroring_no_prefix(self):
        """Test request mirroring without 0x prefix."""
        response_template = "620C{request[2:4]}"
        request = "220C01"
        result = self.config_manager.process_response_with_mirroring(
            response_template, request
        )
        assert result == "620C0C"

    def test_process_response_with_mirroring_edge_cases(self):
        """Test request mirroring edge cases."""
        # Test case 5: Empty template
        result = self.config_manager.process_response_with_mirroring("", "0x220C01")
        assert result == ""

        # Test case 6: No mirroring expressions
        result = self.config_manager.process_response_with_mirroring(
            "0x620C01", "0x220C01"
        )
        assert result == "0x620C01"

        # Test case 7: Invalid index (should return 00)
        result = self.config_manager.process_response_with_mirroring(
            "0x620C{request[10:12]}", "0x220C01"
        )
        assert result == "0x620C00"

    def test_process_response_with_mirroring_complex(self):
        """Test complex request mirroring scenarios."""
        # Test case 8: Complex mirroring with longer request
        response_template = "0x620C{request[2:4]}{request[6:8]}{request[8:10]}"
        request = "0x220C01FFAA"
        result = self.config_manager.process_response_with_mirroring(
            response_template, request
        )
        assert result == "0x620C0CFFAA"

    def test_process_response_with_mirroring_negative_index(self):
        """Test request mirroring with negative index."""
        # Test case 9: Negative index (should return 00)
        result = self.config_manager.process_response_with_mirroring(
            "0x620C{request[-1:2]}", "0x220C01"
        )
        assert result == "0x620C00"

    def test_process_response_with_mirroring_invalid_syntax(self):
        """Test request mirroring with invalid syntax."""
        # Test case 10: Invalid syntax (should return 00)
        result = self.config_manager.process_response_with_mirroring(
            "0x620C{request[2:4:2]}", "0x220C01"
        )
        assert result == "0x620C00"

    def test_process_response_with_mirroring_real_world_examples(self):
        """Test real-world request mirroring examples."""
        # Example 1: Read Data by Identifier - mirror the data identifier
        response_template = "0x620C{request[4:6]}"
        request = "0x220C02"
        result = self.config_manager.process_response_with_mirroring(
            response_template, request
        )
        assert result == "0x620C02"

        # Example 2: Routine Control - mirror the routine identifier
        response_template = "0x7101{request[2:8]}"
        request = "0x31010001"
        result = self.config_manager.process_response_with_mirroring(
            response_template, request
        )
        assert result == "0x7101010001"

        # Example 3: Diagnostic Session Control - mirror the session type
        response_template = "0x5003{request[2:4]}"
        request = "0x1003"
        result = self.config_manager.process_response_with_mirroring(
            response_template, request
        )
        assert result == "0x500303"

    def test_process_response_with_mirroring_hex_conversion(self):
        """Test that hex conversion works correctly."""
        # Test that the function properly handles hex string conversion
        response_template = "0x620C{request[2:4]}"
        request = "220C01"  # Without 0x prefix
        result = self.config_manager.process_response_with_mirroring(
            response_template, request
        )
        assert result == "0x620C0C"

        # Test with 0x prefix
        request = "0x220C01"
        result = self.config_manager.process_response_with_mirroring(
            response_template, request
        )
        assert result == "0x620C0C"


if __name__ == "__main__":
    pytest.main([__file__])
