#!/usr/bin/env python3
"""
Main entry point for the DoIP Server
Supports both legacy single-config and new hierarchical configuration
"""

import argparse
import sys
import os
from .doip_server import start_doip_server

def main():
    """Main entry point for the DoIP server"""
    parser = argparse.ArgumentParser(description='DoIP Server - Diagnostic over IP Server')
    parser.add_argument('--host', type=str, help='Server host address (overrides config)')
    parser.add_argument('--port', type=int, help='Server port (overrides config)')
    parser.add_argument('--gateway-config', type=str, 
                       help='Path to gateway configuration file (default: config/gateway1.yaml)',
                       default='config/gateway1.yaml')
    parser.add_argument('--legacy-config', type=str,
                       help='Path to legacy configuration file (for backward compatibility)')
    
    args = parser.parse_args()
    
    # Determine which configuration to use
    if args.legacy_config:
        # Use legacy configuration
        print(f"Using legacy configuration: {args.legacy_config}")
        from .config_manager import DoIPConfigManager
        # This would require updating the server to support both config types
        print("Legacy configuration support not yet implemented in hierarchical version")
        sys.exit(1)
    else:
        # Use hierarchical configuration
        print(f"Using hierarchical configuration: {args.gateway_config}")
        start_doip_server(
            host=args.host,
            port=args.port,
            gateway_config_path=args.gateway_config
        )

if __name__ == "__main__":
    main()