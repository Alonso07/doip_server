"""Unit tests for doip_server.net_utils."""

import socket

import pytest

from doip_server.net_utils import (
    create_listening_socket,
    format_listen_address,
    resolve_bind_params,
    resolve_client_socket_family,
    validate_bind_host,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "host, dual_stack, expected_family, expected_dual",
    [
        ("0.0.0.0", None, socket.AF_INET, False),
        ("127.0.0.1", None, socket.AF_INET, False),
        ("::", None, socket.AF_INET6, True),
        ("::1", None, socket.AF_INET6, False),
        ("::", False, socket.AF_INET6, False),
        ("::", True, socket.AF_INET6, True),
    ],
)
def test_resolve_bind_params(host, dual_stack, expected_family, expected_dual):
    family, bind_host, enable_dual = resolve_bind_params(host, dual_stack)
    assert family == expected_family
    assert bind_host == host
    assert enable_dual == expected_dual


@pytest.mark.unit
def test_resolve_bind_params_invalid_host():
    with pytest.raises(ValueError, match="Invalid network.host"):
        resolve_bind_params("not-an-ip", None)


@pytest.mark.unit
def test_resolve_bind_params_dual_stack_on_ipv4():
    with pytest.raises(ValueError, match="dual_stack requires"):
        resolve_bind_params("0.0.0.0", True)


@pytest.mark.unit
def test_resolve_bind_params_dual_stack_on_non_wildcard_ipv6():
    with pytest.raises(ValueError, match="only supported when"):
        resolve_bind_params("::1", True)


@pytest.mark.unit
def test_validate_bind_host_empty():
    with pytest.raises(ValueError, match="must not be empty"):
        validate_bind_host("")


@pytest.mark.unit
def test_format_listen_address_ipv6():
    assert format_listen_address("::1", 13400, False) == "[::1]:13400"
    assert format_listen_address("::", 13400, True) == "[::]:13400, dual-stack"


@pytest.mark.unit
def test_resolve_client_socket_family():
    assert resolve_client_socket_family("127.0.0.1") == socket.AF_INET
    assert resolve_client_socket_family("::1") == socket.AF_INET6
    assert resolve_client_socket_family("255.255.255.255") == socket.AF_INET


@pytest.mark.unit
def test_create_listening_socket_tcp_ipv4():
    sock = create_listening_socket(socket.SOCK_STREAM, "127.0.0.1", 0)
    try:
        assert sock.family == socket.AF_INET
        assert sock.getsockname()[0] == "127.0.0.1"
    finally:
        sock.close()


@pytest.mark.unit
def test_create_listening_socket_udp_ipv6_loopback(has_ipv6):
    if not has_ipv6:
        pytest.skip("IPv6 loopback not available")
    sock = create_listening_socket(socket.SOCK_DGRAM, "::1", 0)
    try:
        assert sock.family == socket.AF_INET6
    finally:
        sock.close()
