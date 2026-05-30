#!/usr/bin/env python3
"""
Main entry point for the DoIP Server.

This module provides the command-line interface for starting the DoIP server
with hierarchical configuration support. It handles command-line argument parsing
and delegates server startup to the main DoIP server implementation.

The server supports configuration through:
- Command-line arguments (highest priority)
- Configuration files (hierarchical YAML configuration)
- Default fallback configurations

Usage:
    python -m doip_server.main [options]
    python -m doip_server.main --host 0.0.0.0 --port 13400 --gateway-config config/gateway1.yaml
"""

import argparse
import os
import sys

# Add the src directory to the path for PyInstaller compatibility
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from .doip_server import start_doip_server
except ImportError:
    # Fallback for PyInstaller
    from doip_server import start_doip_server


def main():
    """Main entry point for the DoIP server.

    This function provides the command-line interface for starting the DoIP server.
    It parses command-line arguments and starts the server with the specified
    configuration. Command-line arguments take precedence over configuration file
    settings.

    Command-line Arguments:
        --host: Server host address (overrides configuration)
        --port: Server port number (overrides configuration)
        --gateway-config: Path to gateway configuration file

    Configuration Priority:
        1. Command-line arguments (highest priority)
        2. Configuration file settings
        3. Default fallback values (lowest priority)

    Raises:
        SystemExit: If argument parsing fails or server startup fails
        FileNotFoundError: If configuration file cannot be found
        ValueError: If configuration parameters are invalid

    Example:
        >>> python -m doip_server.main --host 0.0.0.0 --port 13400
        >>> python -m doip_server.main --gateway-config custom_config.yaml
    """
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
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start the web dashboard (FastAPI) alongside the DoIP server",
    )
    parser.add_argument(
        "--web-host",
        type=str,
        default="0.0.0.0",
        help="Web dashboard host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=8080,
        help="Web dashboard port (default: 8080)",
    )

    args = parser.parse_args()

    if args.web:
        # Launch FastAPI web server (which starts the DoIP server as a background thread)
        try:
            import uvicorn
            from web.app import app

            app.state.gateway_config_path = args.gateway_config
            print(f"Starting web dashboard on http://{args.web_host}:{args.web_port}")
            uvicorn.run(app, host=args.web_host, port=args.web_port)
        except ImportError as exc:
            print(f"Web mode requires FastAPI/uvicorn: {exc}")
            sys.exit(1)
    else:
        print(f"Using hierarchical configuration: {args.gateway_config}")
        start_doip_server(
            host=args.host, port=args.port, gateway_config_path=args.gateway_config
        )


if __name__ == "__main__":
    main()
