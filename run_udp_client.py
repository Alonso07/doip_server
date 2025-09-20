#!/usr/bin/env python3
"""
Standalone script to run the UDP DoIP client for vehicle identification testing
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import after path modification
from doip_client.udp_doip_client import main  # pylint: disable=wrong-import-position

if __name__ == "__main__":
    main()
