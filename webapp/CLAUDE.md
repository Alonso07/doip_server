# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Overview

`diagnostic-servers-webapp` manages DoIP and SOVD diagnostic servers running in Docker
containers. It wraps `doip-server` (PyPI) and `sovd-server` (PyPI) as library dependencies
inside per-server Docker images.

## Commands

```bash
# Build server images and start management webapp
make start

# Development (hot-reload)
make dev-backend      # FastAPI on :8000  (needs Docker for container management)
make dev-frontend     # Vite dev server on :5173

# Build server images only
make build-images

# Show running diagnostic containers
make status

# Stream backend logs
make logs

# Stop webapp
make stop

# Full teardown
make clean
```

## Architecture

```
backend/              FastAPI (Python 3.12) — REST API + Docker SDK
  app/main.py           FastAPI app, lifespan ensures Docker network exists
  app/models.py         Pydantic models (ServerCreate, ServerInstance, …)
  app/store.py          JSON persistence in data/servers.json
  app/docker_manager.py Docker SDK wrapper (start/stop/reload containers)
  app/config_defaults.py  Default gateway.yaml template for DoIP servers
  app/routers/
    servers.py          CRUD + start/stop/reload/logs endpoints
    network.py          Docker network info endpoint

frontend/             React 18 + Vite + TailwindCSS
  src/pages/Dashboard.tsx     Main page: server grid + network banner
  src/components/ServerCard.tsx  Per-server card with action buttons
  src/components/CreateServerModal.tsx  Create DoIP/SOVD server form
  src/components/EditConfigModal.tsx    YAML config editor
  src/components/LogsModal.tsx          Container log viewer
  src/components/NetworkInfoBanner.tsx  Docker network overview

docker/
  doip-server/Dockerfile    pip install doip-server, exposes 13400+8080
  sovd-server/Dockerfile    pip install sovd-server, exposes 8080
  sovd-server/entrypoint.sh Copies built-in config to /config on first run

data/                  Gitignored — created at runtime
  servers.json          Server instance metadata
  configs/{id}/         Per-server YAML config directory (mounted as /config)
```

## Docker Volume Mount Architecture

The backend container spawns child (server) containers via `/var/run/docker.sock`.
Volume mounts in the `docker run` call must use **host-side absolute paths** (as seen
by the Docker daemon), not container-internal paths.

```
Host:        /home/user/project/data/configs/{id}/gateway.yaml  ← HOST_DATA_DIR
Backend:     /app/data/configs/{id}/gateway.yaml                 ← DATA_DIR
Server ctr:  /config/gateway.yaml
```

Set `HOST_DATA_DIR` in the `.env` file or let `make start` detect it automatically.

## Server Types

### DoIP (`diag-doip-server:latest`)
- Protocol: TCP/UDP port 13400 (configurable `host_port`)
- Web dashboard: port 8080 (configurable `web_port`)
- Config file: `/config/gateway.yaml` — hierarchical YAML (see doip_server CLAUDE.md)
- Management app generates a default `gateway.yaml` when none is provided

### SOVD (`diag-sovd-server:latest`)
- REST API + Web UI: port 8080 (configurable `web_port`)
- Config: `/config/sovd_gateway.yaml` + entities + resources
- **First-run behavior**: `entrypoint.sh` copies the package's built-in config tree
  to `/config` if `sovd_gateway.yaml` is absent. Subsequent restarts use the existing files.
- Management app edits only `sovd_gateway.yaml` via the Config editor

## API Endpoints

```
GET    /api/servers/               List all servers (syncs status from Docker)
POST   /api/servers/               Create server
GET    /api/servers/{id}           Get server
PUT    /api/servers/{id}           Update config/name/description
DELETE /api/servers/{id}           Delete (must be stopped first)
POST   /api/servers/{id}/start     Start Docker container
POST   /api/servers/{id}/stop      Stop Docker container
POST   /api/servers/{id}/reload    Stop + restart container
GET    /api/servers/{id}/logs      Container logs (plain text, ?tail=N)
GET    /api/network/info           Docker network info
```

Interactive docs available at `http://localhost:8000/docs`.

## Network Access for Testers

Each server maps its ports to the **host machine**:
- DoIP tester connects to `<host-ip>:<host_port>` (default 13400)
- Web UI opens at `http://localhost:<web_port>`

The `diag-net` bridge network assigns Docker IPs to each container (visible in the
Network banner of the management webapp). For testers needing servers to appear at
dedicated IPs (not host-port-mapped), consider:
- **Macvlan driver**: containers get IPs on the physical network
- **Host route**: `ip route add <diag-net-subnet> via <docker-bridge-ip>`
