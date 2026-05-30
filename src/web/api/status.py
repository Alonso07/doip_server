from fastapi import APIRouter
from web.state import get_state

router = APIRouter(tags=["status"])


@router.get("/api/status")
def server_status():
    state = get_state()
    cm = state.config_manager
    if cm is None:
        return {"running": False, "ecus": 0, "services": 0}

    return {
        "running": state.is_running,
        "host": cm.get_network_config().get("host"),
        "port": cm.get_network_config().get("port"),
        "ecu_count": len(cm.get_all_ecu_addresses()),
        "service_count": len(cm.uds_services),
    }
