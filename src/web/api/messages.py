"""Global UDS message / service catalog across all ECUs."""

from fastapi import APIRouter, HTTPException
from web.state import get_state

router = APIRouter(prefix="/api/messages", tags=["messages"])


def _require_cm():
    cm = get_state().config_manager
    if cm is None:
        raise HTTPException(503, "Server not initialised yet")
    return cm


def _ecu_name(cm, address: int) -> str:
    cfg = cm.get_ecu_config(address)
    if cfg:
        return cfg.get("ecu", {}).get("name", "Unknown")
    return "Unknown"


@router.get("")
def list_messages():
    """List every UDS service by name with ECU usage and shared/unique scope."""
    cm = _require_cm()
    usage = cm.get_service_ecu_usage()
    catalog = []

    for name in sorted(usage.keys()):
        addrs = usage[name]
        first_addr = addrs[0]
        cfg = cm.get_ecu_uds_services(first_addr).get(name, {})
        ecu_count = len(addrs)
        source = cm.get_service_source_info(first_addr, name)
        catalog.append(
            {
                "name": name,
                "request": cfg.get("request"),
                "responses_count": len(cfg.get("responses", [])),
                "supports_functional": cfg.get("supports_functional", False),
                "no_response": cfg.get("no_response", False),
                "description": cfg.get("description"),
                "ecu_count": ecu_count,
                "shared": ecu_count > 1,
                "used_by": [f"0x{a:04X}" for a in addrs],
                "used_by_addresses": addrs,
                "used_by_names": [_ecu_name(cm, a) for a in addrs],
                "is_generic": source.get("is_generic"),
                "source_file": source.get("source_file"),
            }
        )

    return catalog
