import os
import sys
from scapy.all import *

def main():
    # Check for root privileges
    if os.geteuid() != 0:
        print("This script requires root privileges. Please run with sudo.")
        sys.exit(1)
    
    # Example: Sniffing network traffic
    print("Starting to sniff network traffic...")
    sniff(prn=lambda x: x.summary(), count=10)

if __name__ == "__main__":
    main()