import json
import shutil
import os
from pathlib import Path
from typing import Optional
from .models import ServerInstance

DATA_DIR = Path(os.environ.get("DATA_DIR", "/app/data"))
SERVERS_FILE = DATA_DIR / "servers.json"
CONFIGS_DIR = DATA_DIR / "configs"


def _ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)


class ServerStore:
    @staticmethod
    def list_servers() -> list[ServerInstance]:
        _ensure_dirs()
        if not SERVERS_FILE.exists():
            return []
        try:
            data = json.loads(SERVERS_FILE.read_text())
            return [ServerInstance(**s) for s in data]
        except Exception:
            return []

    @staticmethod
    def get_server(server_id: str) -> Optional[ServerInstance]:
        for s in ServerStore.list_servers():
            if s.id == server_id:
                return s
        return None

    @staticmethod
    def save_server(server: ServerInstance):
        _ensure_dirs()
        servers = [s for s in ServerStore.list_servers() if s.id != server.id]
        servers.append(server)
        SERVERS_FILE.write_text(
            json.dumps([s.model_dump(mode="json") for s in servers], indent=2)
        )
        # Only write config file if content is non-empty (not just whitespace/comments)
        config_dir = CONFIGS_DIR / server.id
        config_dir.mkdir(parents=True, exist_ok=True)
        if server.config_yaml and server.config_yaml.strip():
            fname = "gateway.yaml" if server.type == "doip" else "sovd_gateway.yaml"
            (config_dir / fname).write_text(server.config_yaml)

    @staticmethod
    def delete_server(server_id: str):
        _ensure_dirs()
        servers = [s for s in ServerStore.list_servers() if s.id != server_id]
        SERVERS_FILE.write_text(
            json.dumps([s.model_dump(mode="json") for s in servers], indent=2)
        )
        config_dir = CONFIGS_DIR / server_id
        if config_dir.exists():
            shutil.rmtree(config_dir)

    @staticmethod
    def get_config_dir(server_id: str) -> Path:
        return CONFIGS_DIR / server_id
