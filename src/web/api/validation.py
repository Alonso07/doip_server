from fastapi import APIRouter, HTTPException

from doip_server.config_schema import validate_config_tree
from web.state import get_state

router = APIRouter(prefix="/api/validate", tags=["validation"])


@router.get("")
def validate_configuration():
    cm = get_state().config_manager
    if cm is None:
        raise HTTPException(503, "Server not initialised yet")

    results = validate_config_tree(cm)
    files = [
        {
            "path": result.path,
            "schema": result.schema_file,
            "valid": result.valid,
            "errors": result.errors,
        }
        for result in results
    ]
    semantic_valid = cm.validate_configs()

    return {
        "valid": semantic_valid and all(f["valid"] for f in files),
        "semantic_valid": semantic_valid,
        "files": files,
    }
