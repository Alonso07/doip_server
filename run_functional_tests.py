#!/usr/bin/env python3
"""
Run Functional Addressing Tests

This script runs the functional addressing end-to-end tests.
It automatically starts the DoIP server in the background and runs the tests.

Usage:
    python run_functional_tests.py
"""

import subprocess
import time
import sys
import os
import signal
import atexit
from pathlib import Path


def cleanup_process(process):
    """Clean up a process"""
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def main():
    """Main function"""
    print("=" * 60)
    print("DoIP Functional Addressing Test Runner")
    print("=" * 60)
    
    # Get project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Start DoIP server in background
    print("Starting DoIP server...")
    server_process = subprocess.Popen([
        sys.executable, "-m", "doip_server.main",
        "--host", "0.0.0.0",
        "--port", "13400",
        "--gateway-config", "config/gateway1.yaml"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Register cleanup
    atexit.register(cleanup_process, server_process)
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    # Check if server is running
    if server_process.poll() is not None:
        stdout, stderr = server_process.communicate()
        print("Failed to start server:")
        print("STDOUT:", stdout.decode())
        print("STDERR:", stderr.decode())
        return 1
    
    print("✓ Server started successfully")
    
    # Run functional addressing tests
    print("\nRunning functional addressing tests...")
    test_cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_functional_addressing_e2e.py",
        "-v",
        "--tb=short"
    ]
    
    # Set environment variable to enable integration tests
    env = os.environ.copy()
    env['DOIP_SERVER_RUNNING'] = 'true'
    
    try:
        result = subprocess.run(test_cmd, env=env, cwd=project_root)
        test_exit_code = result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        test_exit_code = 1
    
    # Clean up server
    print("\nStopping server...")
    cleanup_process(server_process)
    
    # Print results
    print("\n" + "=" * 60)
    if test_exit_code == 0:
        print("🎉 All functional addressing tests passed!")
    else:
        print("⚠️  Some functional addressing tests failed!")
    print("=" * 60)
    
    return test_exit_code


if __name__ == "__main__":
    sys.exit(main())
