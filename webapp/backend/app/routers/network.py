from fastapi import APIRouter
from ..docker_manager import DockerManager

router = APIRouter()


@router.get("/info")
def network_info():
    return DockerManager.network_info()
