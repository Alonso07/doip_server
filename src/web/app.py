"""FastAPI application for the DoIP Server web dashboard."""

import argparse
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Allow running as `python -m web.app` from src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from web.api import doip_client, ecus, gateway, messages, services, status
from web.state import get_state

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_STATIC_DIR = Path(__file__).parent / "static"
_DEFAULT_GATEWAY_CONFIG = "config/gateway1.yaml"
_GATEWAY_CONFIG_ENV = "DOIP_GATEWAY_CONFIG"

templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    gateway_config = getattr(app.state, "gateway_config_path", None) or os.environ.get(
        _GATEWAY_CONFIG_ENV, _DEFAULT_GATEWAY_CONFIG
    )
    get_state().start_doip_server(gateway_config)
    yield
    get_state().stop_doip_server()


app = FastAPI(
    title="DoIP Server Dashboard",
    description="Web UI for managing and testing a DoIP/UDS server at runtime.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# API routers
app.include_router(status.router)
app.include_router(gateway.router)
app.include_router(ecus.router)
app.include_router(services.router)
app.include_router(messages.router)
app.include_router(doip_client.router)


# ── HTML page routes ──────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/ecus", response_class=HTMLResponse)
async def ecus_page(request: Request):
    return templates.TemplateResponse(request, "ecus.html")


@app.get("/ecus/{address}/services", response_class=HTMLResponse)
async def services_page(request: Request, address: int):
    return templates.TemplateResponse(
        request, "services.html", {"ecu_address": address}
    )


@app.get("/messages", response_class=HTMLResponse)
async def messages_page(request: Request):
    return templates.TemplateResponse(request, "messages.html")


@app.get("/client", response_class=HTMLResponse)
async def client_page(request: Request):
    return templates.TemplateResponse(request, "client.html")


# ── Entry point ───────────────────────────────────────────────────────────────


def run_server():
    parser = argparse.ArgumentParser(description="DoIP Server Web Dashboard")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--gateway-config", default="config/gateway1.yaml")
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    app.state.gateway_config_path = args.gateway_config

    uvicorn.run(
        "web.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir=str(Path(__file__).parent.parent),
    )


if __name__ == "__main__":
    run_server()
