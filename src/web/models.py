"""Pydantic models for the web API request/response bodies."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, field_validator


class GatewayUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    network: Optional[Dict[str, Any]] = None
    protocol: Optional[Dict[str, Any]] = None


class ECUCreate(BaseModel):
    target_address: int
    name: str
    functional_address: int = 0x0000
    tester_addresses: List[int] = []
    description: Optional[str] = None

    @field_validator("target_address")
    @classmethod
    def validate_address(cls, v: int) -> int:
        if not (0x0000 <= v <= 0xFFFF):
            raise ValueError("address must be in range 0x0000–0xFFFF")
        return v


class ECUUpdate(BaseModel):
    name: Optional[str] = None
    functional_address: Optional[int] = None
    tester_addresses: Optional[List[int]] = None
    description: Optional[str] = None


class ServiceResponse(BaseModel):
    response: str
    delay_ms: Optional[int] = None


class ServiceCreate(BaseModel):
    request: str
    responses: List[Union[str, ServiceResponse]] = []
    description: Optional[str] = None
    supports_functional: bool = False
    no_response: bool = False
    delay_ms: int = 0


class ServiceUpdate(BaseModel):
    request: Optional[str] = None
    responses: Optional[List[Union[str, ServiceResponse]]] = None
    description: Optional[str] = None
    supports_functional: Optional[bool] = None
    no_response: Optional[bool] = None
    delay_ms: Optional[int] = None


class DoIPSendRequest(BaseModel):
    host: str = "localhost"
    port: int = 13400
    source_address: int = 0x0E00
    target_address: int
    uds_message: str  # hex string, e.g. "22F190"
    timeout: float = 5.0

    @field_validator("uds_message")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        clean = v.replace(" ", "").lstrip("0x").lstrip("0X")
        try:
            bytes.fromhex(clean)
        except ValueError:
            raise ValueError("uds_message must be a valid hex string")
        return clean.upper()
