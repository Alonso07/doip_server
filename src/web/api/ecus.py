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


@router.get("/functional-addresses")
def list_functional_addresses():
    """Group ECUs by functional address, with the services each group can broadcast."""
    cm = _require_cm()

    groups: dict[int, list[int]] = {}
    for addr in cm.get_all_ecu_addresses():
        func_addr = cm.get_ecu_functional_address(addr)
        if func_addr is None:
            continue
        groups.setdefault(func_addr, []).append(addr)

    result = []
    for func_addr, ecu_addresses in groups.items():
        services: dict[str, dict] = {}
        for ecu_addr in ecu_addresses:
            ecu_services = cm.get_ecu_uds_services(ecu_addr)
            for name in cm.get_uds_services_supporting_functional(ecu_addr):
                entry = services.setdefault(
                    name,
                    {
                        "name": name,
                        "request": ecu_services[name].get("request"),
                        "ecus": [],
                    },
                )
                entry["ecus"].append(f"0x{ecu_addr:04X}")

        result.append(
            {
                "functional_address": func_addr,
                "functional_address_hex": f"0x{func_addr:04X}",
                "ecus": [
                    {
                        "target_address": addr,
                        "target_address_hex": f"0x{addr:04X}",
                        "name": (cm.get_ecu_config(addr) or {})
                        .get("ecu", {})
                        .get("name", "Unknown"),
                        "tester_addresses": (cm.get_ecu_config(addr) or {})
                        .get("ecu", {})
                        .get("tester_addresses", []),
                    }
                    for addr in ecu_addresses
                ],
                "services": list(services.values()),
            }
        )

    return result


@router.get("/{address}")
def get_ecu(address: int):
    cm = _require_cm()
    if address not in cm.ecu_configs:
        raise HTTPException(404, f"ECU 0x{address:04X} not found")
    return _ecu_summary(cm, address)


@router.post("", status_code=201)
def create_ecu(body: ECUCreate, persist: bool = False):
    cm = _require_cm()
    try:
        addr = cm.add_ecu(body.model_dump())
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    if persist:
        try:
            cm.persist_new_ecu(addr)
        except Exception as exc:  # pragma: no cover - surfaced to client
            raise HTTPException(500, f"Saved in memory but file write failed: {exc}")
    return _ecu_summary(cm, addr)


@router.put("/{address}")
def update_ecu(address: int, body: ECUUpdate, persist: bool = False):
    cm = _require_cm()
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    try:
        cm.update_ecu(address, updates)
    except KeyError as exc:
        raise HTTPException(404, str(exc))
    if persist:
        try:
            cm.persist_ecu_update(address, updates)
        except Exception as exc:  # pragma: no cover - surfaced to client
            raise HTTPException(500, f"Saved in memory but file write failed: {exc}")
    return _ecu_summary(cm, address)


@router.delete("/{address}")
def delete_ecu(address: int, persist: bool = False):
    cm = _require_cm()
    if not cm.delete_ecu(address):
        raise HTTPException(404, f"ECU 0x{address:04X} not found")
    if persist:
        try:
            cm.persist_delete_ecu(address)
        except Exception as exc:  # pragma: no cover - surfaced to client
            raise HTTPException(500, f"Deleted in memory but file write failed: {exc}")
    return {"deleted": True, "persisted": persist}
