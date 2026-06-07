import subprocess
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

from doip_server import __version__
from web.state import get_state

router = APIRouter(tags=["status"])

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_git(*args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            cwd=_REPO_ROOT,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() or None if result.returncode == 0 else None


@lru_cache(maxsize=1)
def _git_info() -> dict:
    """Git tag/hash of the running checkout, cached for the process lifetime."""
    return {
        "git_tag": _run_git("describe", "--tags", "--always"),
        "git_hash": _run_git("rev-parse", "--short", "HEAD"),
    }


@router.get("/api/status")
def server_status():
    state = get_state()
    cm = state.config_manager
    info = {"version": __version__, **_git_info()}
    if cm is None:
        return {"running": False, "ecus": 0, "services": 0, **info}

    return {
        "running": state.is_running,
        "host": cm.get_network_config().get("host"),
        "port": cm.get_network_config().get("port"),
        "ecu_count": len(cm.get_all_ecu_addresses()),
        "service_count": len(cm.uds_services),
        **info,
    }
