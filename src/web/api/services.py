from fastapi import APIRouter, HTTPException
from web.models import ServiceCreate, ServiceUpdate
from web.state import get_state

router = APIRouter(prefix="/api/ecus/{address}/services", tags=["services"])


def _require_cm():
    cm = get_state().config_manager
    if cm is None:
        raise HTTPException(503, "Server not initialised yet")
    return cm


@router.get("")
def list_services(address: int):
    cm = _require_cm()
    if address not in cm.ecu_configs:
        raise HTTPException(404, f"ECU 0x{address:04X} not found")
    services = cm.get_ecu_uds_services(address)
    return [{"name": name, **cfg} for name, cfg in services.items()]


@router.get("/{service_name}")
def get_service(address: int, service_name: str):
    cm = _require_cm()
    services = cm.get_ecu_uds_services(address)
    if service_name not in services:
        raise HTTPException(
            404, f"Service '{service_name}' not found on ECU 0x{address:04X}"
        )
    return {"name": service_name, **services[service_name]}


@router.post("", status_code=201)
def create_service(address: int, service_name: str, body: ServiceCreate):
    cm = _require_cm()
    try:
        cm.add_service(address, service_name, body.model_dump())
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return {"name": service_name, **body.model_dump()}


@router.put("/{service_name}")
def update_service(address: int, service_name: str, body: ServiceUpdate):
    cm = _require_cm()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    try:
        result = cm.update_service(address, service_name, updates)
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    return {"name": service_name, **result}


@router.delete("/{service_name}", status_code=204)
def delete_service(address: int, service_name: str):
    cm = _require_cm()
    if not cm.delete_service(address, service_name):
        raise HTTPException(
            404, f"Service '{service_name}' not found on ECU 0x{address:04X}"
        )
