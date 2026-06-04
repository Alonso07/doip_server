from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field
import uuid


class ServerCreate(BaseModel):
    name: str
    type: Literal["doip", "sovd"]
    description: str = ""
    host_port: int = Field(ge=1024, le=65535)
    web_port: int = Field(ge=1024, le=65535)
    config_yaml: str = ""


class ServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config_yaml: Optional[str] = None


class ServerInstance(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: Literal["doip", "sovd"]
    description: str = ""
    status: Literal["running", "stopped", "error"] = "stopped"
    host_port: int
    web_port: int
    container_id: Optional[str] = None
    ip_address: Optional[str] = None
    config_yaml: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
