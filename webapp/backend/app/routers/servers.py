from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from ..models import ServerCreate, ServerUpdate, ServerInstance
from ..store import ServerStore
from ..docker_manager import DockerManager
from ..config_defaults import DOIP_DEFAULT_CONFIG

router = APIRouter()


def _sync_status(s: ServerInstance) -> ServerInstance:
    if s.container_id:
        raw = DockerManager.get_status(s.container_id)
        s.status = "running" if raw == "running" else "stopped"
    return s


@router.get("/", response_model=list[ServerInstance])
def list_servers():
    return [_sync_status(s) for s in ServerStore.list_servers()]


@router.post("/", response_model=ServerInstance, status_code=201)
def create_server(body: ServerCreate):
    existing = ServerStore.list_servers()
    used_ports = {p for s in existing for p in [s.host_port, s.web_port]}

    if body.host_port in used_ports:
        raise HTTPException(400, f"Port {body.host_port} is already used by another server")
    if body.web_port in used_ports:
        raise HTTPException(400, f"Port {body.web_port} is already used by another server")
    if body.type == "doip" and body.host_port == body.web_port:
        raise HTTPException(400, "DoIP servers require different host_port and web_port")

    config_yaml = body.config_yaml
    if not config_yaml and body.type == "doip":
        config_yaml = DOIP_DEFAULT_CONFIG.format(name=body.name)

    server = ServerInstance(
        name=body.name,
        type=body.type,
        description=body.description,
        host_port=body.host_port,
        web_port=body.web_port,
        config_yaml=config_yaml,
    )
    ServerStore.save_server(server)
    return server


@router.get("/{server_id}", response_model=ServerInstance)
def get_server(server_id: str):
    s = ServerStore.get_server(server_id)
    if not s:
        raise HTTPException(404, "Server not found")
    return _sync_status(s)


@router.put("/{server_id}", response_model=ServerInstance)
def update_server(server_id: str, body: ServerUpdate):
    s = ServerStore.get_server(server_id)
    if not s:
        raise HTTPException(404, "Server not found")
    if body.name is not None:
        s.name = body.name
    if body.description is not None:
        s.description = body.description
    if body.config_yaml is not None:
        s.config_yaml = body.config_yaml
    s.updated_at = datetime.utcnow()
    ServerStore.save_server(s)
    return s


@router.delete("/{server_id}")
def delete_server(server_id: str):
    s = ServerStore.get_server(server_id)
    if not s:
        raise HTTPException(404, "Server not found")
    if s.status == "running":
        raise HTTPException(400, "Stop the server before deleting it")
    if s.container_id:
        DockerManager.remove_container(s.container_id)
    ServerStore.delete_server(server_id)
    return {"ok": True}


@router.post("/{server_id}/start", response_model=ServerInstance)
def start_server(server_id: str):
    s = ServerStore.get_server(server_id)
    if not s:
        raise HTTPException(404, "Server not found")
    try:
        container_id, ip = DockerManager.start_server(s)
        s.container_id = container_id
        s.ip_address = ip
        s.status = "running"
        s.updated_at = datetime.utcnow()
        ServerStore.save_server(s)
        return s
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to start container: {e}")


@router.post("/{server_id}/stop", response_model=ServerInstance)
def stop_server(server_id: str):
    s = ServerStore.get_server(server_id)
    if not s:
        raise HTTPException(404, "Server not found")
    if s.container_id:
        DockerManager.stop_server(s.container_id)
    s.status = "stopped"
    s.updated_at = datetime.utcnow()
    ServerStore.save_server(s)
    return s


@router.post("/{server_id}/reload", response_model=ServerInstance)
def reload_server(server_id: str):
    s = ServerStore.get_server(server_id)
    if not s:
        raise HTTPException(404, "Server not found")
    try:
        container_id, ip = DockerManager.reload_server(s)
        s.container_id = container_id
        s.ip_address = ip
        s.status = "running"
        s.updated_at = datetime.utcnow()
        ServerStore.save_server(s)
        return s
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to reload container: {e}")


@router.get("/{server_id}/logs", response_class=PlainTextResponse)
def get_logs(server_id: str, tail: int = 200):
    s = ServerStore.get_server(server_id)
    if not s:
        raise HTTPException(404, "Server not found")
    if not s.container_id:
        return "No container has been started for this server yet"
    return DockerManager.get_logs(s.container_id, tail=tail)
