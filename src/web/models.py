"""Pydantic models for the web API request/response bodies."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, field_validator


def _validate_protocol_byte(v: Optional[int]) -> Optional[int]:
    """Accept None or an integer DoIP protocol byte (0x00–0xFF)."""
    if v is None:
        return v
    # bool is a subclass of int; reject it explicitly.
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError("must be an integer in range 0x00–0xFF")
    if not (0x00 <= v <= 0xFF):
        raise ValueError("must be in range 0x00–0xFF")
    return v


class ProtocolUpdate(BaseModel):
    """DoIP protocol version fields used by gateway runtime updates."""

    version: Optional[int] = None
    inverse_version: Optional[int] = None

    @field_validator("version", "inverse_version")
    @classmethod
    def validate_version_byte(cls, v: Optional[int]) -> Optional[int]:
        return _validate_protocol_byte(v)


class GatewayUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    network: Optional[Dict[str, Any]] = None
    protocol: Optional[ProtocolUpdate] = None


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


UDP_MESSAGE_TYPES = {"vehicle_identification", "entity_status", "power_mode"}


class DoIPSendUdpRequest(BaseModel):
    host: str = "localhost"
    port: int = 13400
    message_type: str = "vehicle_identification"
    timeout: float = 5.0

    @field_validator("message_type")
    @classmethod
    def validate_message_type(cls, v: str) -> str:
        if v not in UDP_MESSAGE_TYPES:
            raise ValueError(f"message_type must be one of {sorted(UDP_MESSAGE_TYPES)}")
        return v


class DoIPSendRawUdpRequest(BaseModel):
    host: str = "localhost"
    port: int = 13400
    version: Optional[int] = None
    inverse_version: Optional[int] = None
    payload_type: int
    payload_hex: str = ""
    timeout: float = 5.0

    @field_validator("payload_hex")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        clean = v.replace(" ", "")
        if clean.lower().startswith("0x"):
            clean = clean[2:]
        try:
            bytes.fromhex(clean)
        except ValueError:
            raise ValueError("payload_hex must be a valid hex string")
        return clean.upper()

    @field_validator("payload_type")
    @classmethod
    def validate_payload_type(cls, v: int) -> int:
        if not (0 <= v <= 0xFFFF):
            raise ValueError("payload_type must be in range 0x0000–0xFFFF")
        return v

    @field_validator("version", "inverse_version")
    @classmethod
    def validate_version_byte(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if not (0 <= v <= 0xFF):
            raise ValueError("version/inverse_version must be in range 0x00–0xFF")
        return v
