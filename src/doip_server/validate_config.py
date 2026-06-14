#!/usr/bin/env python3
"""
Command-line configuration validator for the DoIP server.

Validates a gateway configuration and every ECU/UDS service file it
references, both against their JSON Schemas and against the semantic
checks performed by ``HierarchicalConfigManager.validate_configs()``.

Usage:
    python -m doip_server.validate_config [--gateway-config config/gateway1.yaml]
"""

import argparse
import sys

from .config_schema import validate_config_tree
from .hierarchical_config_manager import HierarchicalConfigManager


def main() -> None:
    """Entry point for the ``validate_config`` console script."""
    parser = argparse.ArgumentParser(
        description="Validate DoIP server YAML configuration files"
    )
    parser.add_argument(
        "--gateway-config",
        type=str,
        default="config/gateway1.yaml",
        help="Path to the gateway configuration file (default: config/gateway1.yaml)",
    )
    args = parser.parse_args()

    config_manager = HierarchicalConfigManager(args.gateway_config)

    schema_results = validate_config_tree(config_manager)
    schema_ok = True
    for result in schema_results:
        if result.valid:
            print(f"OK    {result.path}")
        else:
            schema_ok = False
            print(f"FAIL  {result.path}")
            for error in result.errors:
                print(f"      {error}")

    semantic_ok = config_manager.validate_configs()
    if semantic_ok:
        print("OK    semantic validation")
    else:
        print("FAIL  semantic validation (see log output above)")

    if schema_ok and semantic_ok:
        print("\nAll configuration files are valid.")
        sys.exit(0)
    else:
        print("\nConfiguration validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
