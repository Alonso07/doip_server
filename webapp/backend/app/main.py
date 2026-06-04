from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import servers, network
from .docker_manager import DockerManager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        DockerManager.ensure_network()
    except Exception as e:
        logger.warning("Could not ensure Docker network on startup: %s", e)
    yield


app = FastAPI(
    title="Diagnostic Servers Manager",
    description="Manage DoIP and SOVD diagnostic servers running in Docker containers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(servers.router, prefix="/api/servers", tags=["servers"])
app.include_router(network.router, prefix="/api/network", tags=["network"])
