#!/usr/bin/env python3
"""
Standalone script to run the UDP DoIP client for vehicle identification testing
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from doip_client.udp_doip_client import main

if __name__ == "__main__":
    main()
