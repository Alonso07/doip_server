"""Test fixtures for the web layer.

We patch the module-level _state singleton so the TestClient's lifespan
calls start_doip_server on a mock (no real sockets) while the real
HierarchicalConfigManager is wired in for accurate API behaviour.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from doip_server.hierarchical_config_manager import HierarchicalConfigManager


@pytest.fixture(scope="session")
def config_manager():
    return HierarchicalConfigManager("config/gateway1.yaml")


@pytest.fixture()
def web_client(config_manager):
    import web.state as state_module
    from web.app import app

    # Set the attribute the lifespan reads from app.state
    app.state.gateway_config_path = "config/gateway1.yaml"

    mock_state = MagicMock()
    mock_state.config_manager = config_manager
    mock_state.is_running = True
    mock_state.doip_server = MagicMock(running=True)
    # start/stop are no-ops
    mock_state.start_doip_server = MagicMock()
    mock_state.stop_doip_server = MagicMock()

    with patch.object(state_module, "_state", mock_state):
        with TestClient(app, raise_server_exceptions=True) as client:
            yield client
