"""IPv6 loopback integration tests (skipped when IPv6 is unavailable)."""

import socket
import struct
import threading
import time

import pytest

from doip_server.doip_server import DoIPServer

DOIP_VERSION = 0x02
DOIP_INV_VERSION = 0xFD
VEHICLE_IDENTIFICATION_REQUEST = 0x0001


def _free_ipv6_loopback_port() -> int:
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    sock.bind(("::1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _vehicle_identification_request() -> bytes:
    return struct.pack(
        ">BBHI",
        0xFF,
        0x00,
        VEHICLE_IDENTIFICATION_REQUEST,
        0,
    )


@pytest.mark.integration
def test_doip_server_binds_ipv6_loopback(has_ipv6):
    if not has_ipv6:
        pytest.skip("IPv6 loopback not available")

    port = _free_ipv6_loopback_port()
    server = DoIPServer(
        host="::1",
        port=port,
        gateway_config_path="config/gateway1.yaml",
    )
    assert server.dual_stack is False

    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if server.running:
            break
        time.sleep(0.05)
    assert server.running

    try:
        tcp = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        tcp.settimeout(2.0)
        tcp.connect(("::1", port))
        tcp.close()

        udp = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        udp.settimeout(2.0)
        udp.sendto(_vehicle_identification_request(), ("::1", port))
        data, addr = udp.recvfrom(4096)
        udp.close()
        assert len(data) >= 8
        assert addr[0] == "::1"
    finally:
        server.stop()
        thread.join(timeout=3.0)


@pytest.mark.integration
def test_doip_server_dual_stack_config(has_ipv6):
    if not has_ipv6:
        pytest.skip("IPv6 loopback not available")

    from doip_server.hierarchical_config_manager import HierarchicalConfigManager

    cm = HierarchicalConfigManager("config/gateway1_ipv6.yaml")
    assert cm.get_server_binding_info()[0] == "::"
    assert cm.get_dual_stack("::") is True
