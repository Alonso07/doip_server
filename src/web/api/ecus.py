from fastapi import APIRouter, HTTPException
from web.models import ECUCreate, ECUUpdate
from web.state import get_state

router = APIRouter(prefix="/api/ecus", tags=["ecus"])


def _require_cm():
    cm = get_state().config_manager
    if cm is None:
        raise HTTPException(503, "Server not initialised yet")
    return cm


def _ecu_summary(cm, address: int) -> dict:
    cfg = cm.get_ecu_config(address)
    info = cfg.get("ecu", {}) if cfg else {}
    services = cm.get_ecu_uds_services(address)
    return {
        "target_address": address,
        "target_address_hex": f"0x{address:04X}",
        "name": info.get("name", "Unknown"),
        "functional_address": info.get("functional_address", 0),
        "tester_addresses": info.get("tester_addresses", []),
        "description": info.get("description"),
        "service_count": len(services),
    }


@router.get("")
def list_ecus():
    cm = _require_cm()
    return [_ecu_summary(cm, addr) for addr in cm.get_all_ecu_addresses()]


@router.get("/{address}")
def get_ecu(address: int):
    cm = _require_cm()
    if address not in cm.ecu_configs:
        raise HTTPException(404, f"ECU 0x{address:04X} not found")
    return _ecu_summary(cm, address)


@router.post("", status_code=201)
def create_ecu(body: ECUCreate):
    cm = _require_cm()
    try:
        addr = cm.add_ecu(body.model_dump())
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return _ecu_summary(cm, addr)


@router.put("/{address}")
def update_ecu(address: int, body: ECUUpdate):
    cm = _require_cm()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    try:
        cm.update_ecu(address, updates)
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    return _ecu_summary(cm, address)


@router.delete("/{address}", status_code=204)
def delete_ecu(address: int):
    cm = _require_cm()
    if not cm.delete_ecu(address):
        raise HTTPException(404, f"ECU 0x{address:04X} not found")
