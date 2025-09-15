"""
DoIP Client package
"""

# Import UDP DoIP client (no external dependencies)
from .udp_doip_client import UDPDoIPClient

# Try to import other clients (may have external dependencies)
try:
    from .doip_client import DoIPClientWrapper, start_doip_client, create_doip_request
    from .debug_client import DebugDoIPClient

    __all__ = [
        "DoIPClientWrapper",
        "start_doip_client",
        "create_doip_request",
        "DebugDoIPClient",
        "UDPDoIPClient",
    ]
except ImportError:
    # Fallback if external dependencies are not available
    __all__ = ["UDPDoIPClient"]
