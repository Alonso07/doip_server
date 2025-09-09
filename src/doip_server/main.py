#!/usr/bin/env python3
"""
Main entry point for the DoIP Server
Uses hierarchical configuration system
"""

import argparse
import sys
import os
from .doip_server import start_doip_server


def main():
    """Main entry point for the DoIP server"""
    parser = argparse.ArgumentParser(
        description="DoIP Server - Diagnostic over IP Server"
    )
    parser.add_argument(
        "--host", type=str, help="Server host address (overrides config)"
    )
    parser.add_argument("--port", type=int, help="Server port (overrides config)")
    parser.add_argument(
        "--gateway-config",
        type=str,
        help="Path to gateway configuration file (default: config/gateway1.yaml)",
        default="config/gateway1.yaml",
    )

    args = parser.parse_args()

    # Use hierarchical configuration
    print(f"Using hierarchical configuration: {args.gateway_config}")
    start_doip_server(
        host=args.host, port=args.port, gateway_config_path=args.gateway_config
    )


if __name__ == "__main__":
    main()
