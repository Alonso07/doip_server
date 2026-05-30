# DoIP Server — Web Dashboard

The DoIP Server ships with a **FastAPI** web dashboard (`src/web/`) that lets you start, inspect, and exercise the server from a browser without writing any code.

---

## Prerequisites

```bash
poetry install        # installs fastapi, uvicorn, jinja2, htmx, websockets, etc.
```

All web dependencies are declared in `pyproject.toml` and installed by the standard `poetry install`.

---

## Starting the Web Server

### Via the installed entry-point (recommended)

```bash
poetry run doip_web --gateway-config config/gateway1.yaml
```

### Via the module directly

```bash
poetry run python -m web.app \
  --gateway-config config/gateway1.yaml \
  --host 0.0.0.0 \
  --port 8080
```

### CLI flags

| Flag | Default | Description |
|---|---|---|
| `--gateway-config` | `config/gateway1.yaml` | Path to the gateway YAML config |
| `--host` | `0.0.0.0` | Interface to bind the HTTP server |
| `--port` | `8080` | TCP port for the web dashboard |
| `--reload` | _(off)_ | Enable uvicorn auto-reload (development only) |

Once running, open `http://localhost:8080` in a browser.

---

## Pages

### Dashboard (`/`)

The home page displays three live stat cards (auto-refreshing every 5 s via HTMX):

| Card | Content |
|---|---|
| **Status** | Running / stopped, host, port |
| **ECU count** | Number of loaded ECU configs |
| **Service count** | Total UDS services across all ECUs |

Below the stats you'll find:

- **Gateway Configuration** — a read-only YAML view of the loaded gateway settings with an **Edit** button to modify them in-place (see [Configuration editing](#configuration-editing)).
- **ECUs overview** — a compact card list with a **Manage →** link to the ECU detail page.

---

### ECU Management (`/ecus`)

Lists every configured ECU with:

- Name, target address (hex), functional address, allowed tester addresses
- Number of configured UDS services
- Per-ECU **Edit** and **Delete** buttons
- A **+ Add ECU** form to register a new ECU at runtime

---

### Services (`/ecus/{address}/services`)

Drill into the UDS services of a single ECU (identified by its decimal target address).

Each service shows:

- Service name, request hex bytes, configured response(s)
- Whether `supports_functional` is enabled
- Inline **Edit** / **Delete** controls
- A **+ Add Service** panel

---

### DoIP Client Tester (`/client`)

An in-browser DoIP client that lets you fire UDS requests directly against the running server over a **WebSocket** (`/api/client/ws`).

Fill in:

| Field | Example | Notes |
|---|---|---|
| Server host | `127.0.0.1` | Hostname of the DoIP server |
| Server port | `13400` | TCP port |
| Source address | `0x0E00` | Logical address of the tester |
| Target address | `0x1000` | ECU target address |
| UDS message | `22F190` | Hex bytes, no spaces required |
| Timeout | `5` | Seconds |

Click **Send** to execute a full DoIP exchange (routing activation → diagnostic message → ACK → UDS response). The log panel streams each step in real time.

---

## REST API

All pages are backed by a JSON API. You can call it directly with `curl` or any HTTP client.

### Status

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/status` | Server running state, host/port, ECU and service counts |

### Gateway

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/gateway` | Full gateway configuration (network, protocol, vehicle info) |
| `PUT` | `/api/gateway?persist=false` | Update gateway settings in memory (or persist to YAML) |

**Example — change the log level:**
```bash
curl -X PUT http://localhost:8080/api/gateway \
  -H 'Content-Type: application/json' \
  -d '{"gateway": {"logging": {"level": "DEBUG"}}}'
```

### ECUs

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/ecus` | List all ECUs |
| `GET` | `/api/ecus/{address}` | Get one ECU by target address |
| `POST` | `/api/ecus?persist=false` | Add a new ECU |
| `PUT` | `/api/ecus/{address}?persist=false` | Update an ECU |
| `DELETE` | `/api/ecus/{address}?persist=false` | Remove an ECU |

### Services

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/ecus/{address}/services` | List services for an ECU |
| `GET` | `/api/ecus/{address}/services/{name}` | Get one service |
| `POST` | `/api/ecus/{address}/services?persist=false` | Add a service |
| `PUT` | `/api/ecus/{address}/services/{name}?persist=false` | Update a service |
| `DELETE` | `/api/ecus/{address}/services/{name}?persist=false` | Remove a service |

### DoIP Client

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/client/send` | Single DoIP exchange (JSON body, returns log + UDS response) |
| `WS` | `/api/client/ws` | WebSocket — stream log events for a DoIP exchange |

**POST `/api/client/send` body:**
```json
{
  "host": "127.0.0.1",
  "port": 13400,
  "source_address": 3584,
  "target_address": 4096,
  "uds_message": "22F190",
  "timeout": 5.0
}
```

---

## Configuration Editing

All mutating endpoints accept an optional `?persist=false` query parameter:

| Value | Behaviour |
|---|---|
| `false` _(default)_ | Change is applied to the in-memory config only; restarting the server reverts it |
| `true` | Change is applied AND written back to the underlying YAML file(s) |

Use `persist=false` for temporary testing and `persist=true` when you want the change to survive a server restart.

---

## Auto-Refresh Behaviour

The dashboard uses [HTMX](https://htmx.org) for live updates:

- Status cards poll `GET /api/status` every **5 seconds**.
- Gateway and ECU sections load once on page render and refresh on explicit button click.
- The Client page uses a persistent **WebSocket** for streaming log events during a diagnostic exchange.

No page reloads or JavaScript framework required.

---

## Interactive API Docs

FastAPI ships a built-in Swagger UI and ReDoc browser:

| URL | Interface |
|---|---|
| `http://localhost:8080/docs` | Swagger UI (try it out) |
| `http://localhost:8080/redoc` | ReDoc (read-only reference) |
| `http://localhost:8080/openapi.json` | Raw OpenAPI 3.x schema |

---

## Troubleshooting

**"Server not initialised yet" (503)**
The DoIP server process failed to start. Check `--gateway-config` points to a valid file and that port 13400 is free.

**HTMX cards stay empty / show "Loading…"**
The browser console will show the failing request. Most likely the gateway config is invalid or missing ECU files.

**Cannot connect from a remote host**
Make sure you started the server with `--host 0.0.0.0` (not `127.0.0.1`).
