"""Socket helpers for IPv4/IPv6 and dual-stack DoIP server binding."""

import ipaddress
import socket
from typing import Optional, Tuple

# IPv6 multicast for vehicle discovery (optional client use)
IPV6_LINK_LOCAL_MULTICAST = "ff02::1"


def validate_bind_host(host: str) -> str:
    """Validate a bind host string; return normalized host for bind()."""
    if not host or not str(host).strip():
        raise ValueError("network.host must not be empty")
    host = str(host).strip()
    try:
        ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError(f"Invalid network.host: {host!r}") from exc
    return host


def resolve_bind_params(
    host: str, dual_stack: Optional[bool] = None
) -> Tuple[int, str, bool]:
    """Resolve socket family, bind address, and dual-stack flag from host config.

    Args:
        host: Bind address from configuration (e.g. "0.0.0.0", "::", "::1").
        dual_stack: Explicit dual-stack override. When None, True only for "::".

    Returns:
        (address_family, bind_host, enable_dual_stack)
    """
    bind_host = validate_bind_host(host)
    addr = ipaddress.ip_address(bind_host)

    if addr.version == 6:
        family = socket.AF_INET6
        if dual_stack is None:
            enable_dual_stack = bind_host == "::"
        else:
            enable_dual_stack = bool(dual_stack)
        if enable_dual_stack and bind_host != "::":
            raise ValueError("dual_stack is only supported when network.host is '::'")
        return family, bind_host, enable_dual_stack

    # IPv4
    if dual_stack:
        raise ValueError("dual_stack requires an IPv6 bind host (use host: '::')")
    return socket.AF_INET, bind_host, False


def format_listen_address(host: str, port: int, dual_stack: bool) -> str:
    """Format host:port for logs (bracket IPv6 literals)."""
    try:
        if ipaddress.ip_address(host).version == 6:
            suffix = ", dual-stack" if dual_stack else ""
            return f"[{host}]:{port}{suffix}"
    except ValueError:
        pass
    suffix = ", dual-stack" if dual_stack else ""
    return f"{host}:{port}{suffix}"


def resolve_client_socket_family(server_host: str) -> int:
    """Pick AF_INET or AF_INET6 for a client connecting to server_host."""
    host = str(server_host).strip()
    if host in ("255.255.255.255", ""):
        return socket.AF_INET
    try:
        if ipaddress.ip_address(host).version == 6:
            return socket.AF_INET6
    except ValueError:
        pass
    return socket.AF_INET


def is_ipv6_multicast_host(server_host: str) -> bool:
    """True if server_host is an IPv6 multicast address."""
    host = str(server_host).strip()
    try:
        addr = ipaddress.ip_address(host)
        return addr.version == 6 and addr.is_multicast
    except ValueError:
        return False


def create_listening_socket(
    sock_type: int,
    host: str,
    port: int,
    *,
    dual_stack: bool = False,
    max_connections: int = 5,
) -> socket.socket:
    """Create a bound listening socket (TCP or UDP) for the given host/port.

    Args:
        sock_type: socket.SOCK_STREAM or socket.SOCK_DGRAM
        host: Address to bind (validated via resolve_bind_params)
        port: Port number
        dual_stack: When True with IPv6, set IPV6_V6ONLY=0 for IPv4-mapped peers
        max_connections: listen() backlog for TCP only

    Returns:
        Bound socket (TCP sockets are already listen()-ing)
    """
    family, bind_host, enable_dual_stack = resolve_bind_params(host, dual_stack)

    sock = socket.socket(family, sock_type)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if family == socket.AF_INET6 and enable_dual_stack:
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        sock.bind((bind_host, port))
        if sock_type == socket.SOCK_STREAM:
            sock.listen(max_connections)
    except Exception:
        sock.close()
        raise
    return sock
