"""
DoIP Server Package - Diagnostics over IP Server Implementation.

This package provides a comprehensive DoIP (Diagnostics over IP) server implementation
for automotive diagnostic communication. It supports both TCP and UDP protocols with
hierarchical configuration management and multi-ECU support.

Key Components:
    - DoIPServer: Main server class for handling diagnostic communication
    - HierarchicalConfigManager: Configuration management with YAML support
    - main: Command-line interface for server startup

Features:
    - Vehicle Identification (UDP)
    - Routing Activation (TCP)
    - UDS Message Processing (TCP)
    - Functional Addressing (broadcast to multiple ECUs)
    - Response Cycling for testing scenarios
    - Hierarchical Configuration Management
    - Multi-ECU Support
    - Source Address Validation
    - Comprehensive Logging

Usage:
    Basic server startup:
        >>> from doip_server import start_doip_server
        >>> start_doip_server()

    With custom configuration:
        >>> start_doip_server(host="0.0.0.0", port=13400, gateway_config_path="config/gateway1.yaml")

    Command-line interface:
        >>> python -m doip_server.main --host 0.0.0.0 --port 13400

Configuration:
    The server uses hierarchical YAML configuration files:
    - Gateway configuration (network, protocol settings)
    - ECU configurations (target addresses, UDS services)
    - UDS service definitions (common and ECU-specific)

Protocol Support:
    - DoIP Protocol Version 0x02
    - UDS (Unified Diagnostic Services)
    - ISO 14229-1 compliant diagnostic services
    - Functional addressing (ISO 14229-2)

Author: DoIP Server Development Team
Version: 1.0.0
License: MIT
"""

# Package version
__version__ = "1.0.0"

# Main exports
from .doip_server import DoIPServer, start_doip_server
from .hierarchical_config_manager import HierarchicalConfigManager
from .main import main

# Public API
__all__ = [
    "DoIPServer",
    "start_doip_server",
    "HierarchicalConfigManager",
    "main",
    "__version__",
]
