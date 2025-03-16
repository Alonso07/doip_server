#!/usr/bin/env python3
"""
Pytest configuration for DoIP tests.
Sets up the test environment and provides common fixtures.
"""

import pytest
import sys
import os
from pathlib import Path

# Add the src directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def test_config_path():
    """Provide path to test configuration file"""
    return "config/doip_config.yaml"


@pytest.fixture(scope="session")
def test_server_host():
    """Provide test server host"""
    return "127.0.0.1"


@pytest.fixture(scope="session")
def test_server_port():
    """Provide test server port"""
    return 13400


@pytest.fixture(scope="session")
def test_source_address():
    """Provide test source address"""
    return 0x0E00


@pytest.fixture(scope="session")
def test_target_address():
    """Provide test target address"""
    return 0x1000


@pytest.fixture(scope="session")
def test_routine_id():
    """Provide test routine ID"""
    return 0x0202


@pytest.fixture(scope="session")
def test_data_identifier():
    """Provide test data identifier"""
    return 0xF187
