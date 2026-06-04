import docker
import os
from pathlib import Path
from typing import Optional, Tuple

NETWORK_NAME = os.environ.get("DOCKER_NETWORK", "diag-net")
DOIP_IMAGE = os.environ.get("DOIP_IMAGE", "diag-doip-server:latest")
SOVD_IMAGE = os.environ.get("SOVD_IMAGE", "diag-sovd-server:latest")
# HOST_DATA_DIR: path as seen by the Docker daemon (host side) for volume mounts
HOST_DATA_DIR = os.environ.get("HOST_DATA_DIR", "")
# CONTAINER_DATA_DIR: path inside the backend container
CONTAINER_DATA_DIR = os.environ.get("DATA_DIR", "/app/data")


class DockerManager:
    _client: Optional[docker.DockerClient] = None

    @classmethod
    def client(cls) -> docker.DockerClient:
        if cls._client is None:
            cls._client = docker.from_env()
        return cls._client

    @classmethod
    def ensure_network(cls):
        client = cls.client()
        existing = {n.name for n in client.networks.list()}
        if NETWORK_NAME not in existing:
            client.networks.create(NETWORK_NAME, driver="bridge", check_duplicate=True)

    @classmethod
    def _container_name(cls, server_id: str, server_type: str) -> str:
        return f"diag-{server_type}-{server_id[:8]}"

    @classmethod
    def _remove_if_exists(cls, name: str):
        try:
            c = cls.client().containers.get(name)
            c.remove(force=True)
        except docker.errors.NotFound:
            pass

    @classmethod
    def _host_config_dir(cls, server_id: str) -> str:
        """Return the host-side path to a server's config directory."""
        if HOST_DATA_DIR:
            return str(Path(HOST_DATA_DIR) / "configs" / server_id)
        # Fallback: assume backend is not containerised (dev mode)
        return str(Path(CONTAINER_DATA_DIR) / "configs" / server_id)

    @classmethod
    def start_server(cls, server) -> Tuple[str, Optional[str]]:
        client = cls.client()
        container_name = cls._container_name(server.id, server.type)
        cls._remove_if_exists(container_name)

        # Ensure config dir exists on the backend's local filesystem
        local_config_dir = Path(CONTAINER_DATA_DIR) / "configs" / server.id
        local_config_dir.mkdir(parents=True, exist_ok=True)

        host_config_dir = cls._host_config_dir(server.id)
        image = DOIP_IMAGE if server.type == "doip" else SOVD_IMAGE

        if server.type == "doip":
            ports = {
                "13400/tcp": server.host_port,
                "13400/udp": server.host_port,
                "8080/tcp": server.web_port,
            }
        else:
            ports = {"8080/tcp": server.web_port}

        try:
            container = client.containers.run(
                image=image,
                name=container_name,
                detach=True,
                ports=ports,
                volumes={host_config_dir: {"bind": "/config", "mode": "rw"}},
                network=NETWORK_NAME,
                labels={
                    "diag-manager": "true",
                    "diag-server-id": server.id,
                    "diag-server-type": server.type,
                },
                restart_policy={"Name": "unless-stopped"},
            )
        except docker.errors.ImageNotFound:
            raise RuntimeError(
                f"Image '{image}' not found. Run 'make build-images' first."
            )

        container.reload()
        net_settings = container.attrs.get("NetworkSettings", {}).get("Networks", {})
        ip = net_settings.get(NETWORK_NAME, {}).get("IPAddress")
        return container.id, ip

    @classmethod
    def stop_server(cls, container_id: str):
        try:
            c = cls.client().containers.get(container_id)
            c.stop(timeout=10)
        except docker.errors.NotFound:
            pass

    @classmethod
    def reload_server(cls, server) -> Tuple[str, Optional[str]]:
        if server.container_id:
            cls.stop_server(server.container_id)
        return cls.start_server(server)

    @classmethod
    def remove_container(cls, container_id: str):
        try:
            c = cls.client().containers.get(container_id)
            c.remove(force=True)
        except docker.errors.NotFound:
            pass

    @classmethod
    def get_status(cls, container_id: str) -> str:
        try:
            c = cls.client().containers.get(container_id)
            return c.status
        except docker.errors.NotFound:
            return "not_found"

    @classmethod
    def get_logs(cls, container_id: str, tail: int = 200) -> str:
        try:
            c = cls.client().containers.get(container_id)
            return c.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
        except docker.errors.NotFound:
            return "Container not found"

    @classmethod
    def network_info(cls) -> dict:
        try:
            net = cls.client().networks.get(NETWORK_NAME)
            ipam_config = net.attrs.get("IPAM", {}).get("Config", [{}])
            subnet = ipam_config[0].get("Subnet", "N/A") if ipam_config else "N/A"
            gateway_ip = ipam_config[0].get("Gateway", "N/A") if ipam_config else "N/A"
            containers_raw = net.attrs.get("Containers", {})
            containers = [
                {
                    "id": cid[:12],
                    "name": info.get("Name", "").lstrip("/"),
                    "ip": info.get("IPv4Address", "").split("/")[0],
                }
                for cid, info in containers_raw.items()
            ]
            return {
                "name": NETWORK_NAME,
                "subnet": subnet,
                "gateway": gateway_ip,
                "containers": containers,
                "exists": True,
            }
        except docker.errors.NotFound:
            return {"name": NETWORK_NAME, "exists": False}
        except Exception as e:
            return {"name": NETWORK_NAME, "exists": False, "error": str(e)}
