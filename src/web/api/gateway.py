from fastapi import APIRouter, HTTPException
from web.models import GatewayUpdate
from web.state import get_state

router = APIRouter(prefix="/api/gateway", tags=["gateway"])


def _require_cm():
    cm = get_state().config_manager
    if cm is None:
        raise HTTPException(503, "Server not initialised yet")
    return cm


@router.get("")
def get_gateway():
    cm = _require_cm()
    return {
        "gateway": cm.get_gateway_config(),
        "network": cm.get_network_config(),
        "protocol": cm.get_protocol_config(),
        "vehicle": cm.get_vehicle_info(),
    }


@router.put("")
def update_gateway(body: GatewayUpdate):
    cm = _require_cm()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    result = cm.update_gateway(updates)
    return {"gateway": result}
