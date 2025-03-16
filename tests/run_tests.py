#!/usr/bin/env python3
"""
Simple test runner for DoIP tests.
Provides easy access to different test categories.
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def main():
    """Main test runner"""
    print("DoIP Test Runner")
    print("=" * 50)
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    if len(sys.argv) < 2:
        print("Usage: python run_tests.py [unit|integration|all|coverage]")
        print("\nOptions:")
        print("  unit       - Run unit tests only (fast)")
        print("  integration- Run integration tests only")
        print("  all        - Run all tests")
        print("  coverage   - Run tests with coverage report")
        print("\nExamples:")
        print("  python run_tests.py unit")
        print("  python run_tests.py integration")
        print("  python run_tests.py all")
        print("  python run_tests.py coverage")
        return
    
    test_type = sys.argv[1].lower()
    
    if test_type == "unit":
        print("Running unit tests...")
        cmd = f"cd {project_root} && poetry run pytest tests/test_doip_unit.py -v"
        output = run_command(cmd)
        if output:
            print(output)
    
    elif test_type == "integration":
        print("Running integration tests...")
        cmd = f"cd {project_root} && poetry run pytest tests/test_doip_integration.py -v"
        output = run_command(cmd)
        if output:
            print(output)
    
    elif test_type == "all":
        print("Running all tests...")
        cmd = f"cd {project_root} && poetry run pytest tests/ -v"
        output = run_command(cmd)
        if output:
            print(output)
    
    elif test_type == "coverage":
        print("Running tests with coverage...")
        cmd = f"cd {project_root} && poetry run pytest tests/ --cov=src/doip_server --cov-report=html --cov-report=term-missing"
        output = run_command(cmd)
        if output:
            print(output)
        print("\nCoverage report generated in htmlcov/ directory")
    
    else:
        print(f"Unknown test type: {test_type}")
        print("Valid options: unit, integration, all, coverage")

if __name__ == "__main__":
    main()
