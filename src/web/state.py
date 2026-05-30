"""Shared runtime state between the DoIP server and the web layer."""

import threading
from typing import Optional

from doip_server.doip_server import DoIPServer
from doip_server.hierarchical_config_manager import HierarchicalConfigManager


class ServerState:
    """Thread-safe singleton that holds live references to the DoIP server and config."""

    def __init__(self):
        self._lock = threading.Lock()
        self.config_manager: Optional[HierarchicalConfigManager] = None
        self.doip_server: Optional[DoIPServer] = None
        self._server_thread: Optional[threading.Thread] = None

    def start_doip_server(self, gateway_config_path: str) -> None:
        """Initialise the config manager and launch the DoIP server in a daemon thread."""
        with self._lock:
            if self.doip_server and self.doip_server.running:
                return

            self.config_manager = HierarchicalConfigManager(gateway_config_path)
            self.doip_server = DoIPServer(gateway_config_path=gateway_config_path)
            # Share the same config_manager instance so web mutations are picked up
            self.doip_server.config_manager = self.config_manager

            self._server_thread = threading.Thread(
                target=self.doip_server.start,
                name="doip-server",
                daemon=True,
            )
            self._server_thread.start()

    def stop_doip_server(self) -> None:
        with self._lock:
            if self.doip_server:
                self.doip_server.stop()

    @property
    def is_running(self) -> bool:
        return bool(self.doip_server and self.doip_server.running)


# Module-level singleton
_state = ServerState()


def get_state() -> ServerState:
    return _state
