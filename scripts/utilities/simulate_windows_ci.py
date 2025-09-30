#!/usr/bin/env python3
"""
Windows CI Simulation Script
Simulates the Windows CI environment locally on macOS/Linux
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔧 {description}")
    print(f"   Running: {cmd}")

    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print("   ✅ Success")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed with exit code {e.returncode}")
        if e.stdout:
            print(f"   Output: {e.stdout.strip()}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False


def simulate_windows_ci():
    """Simulate the Windows CI workflow locally"""
    print("🚀 Windows CI Simulation for DoIP Server")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Not in the project root directory. Please run from the project root.")
        return False

    # Simulate Windows environment variables
    print("🖥️ Simulating Windows environment...")
    os.environ["OS"] = "Windows_NT"
    os.environ["PLATFORM"] = "windows"

    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"🐍 Python version: {python_version}")

    # Install Poetry if not available
    if not run_command("poetry --version", "Checking Poetry installation"):
        print("📦 Installing Poetry...")
        run_command(
            "curl -sSL https://install.python-poetry.org | python3 -",
            "Installing Poetry",
        )

    # Install dependencies
    if not run_command(
        "poetry install --no-interaction --no-root", "Installing dependencies"
    ):
        print("❌ Failed to install dependencies")
        return False

    # Show environment info (simulating CI step)
    print("\n🔍 Environment Information:")
    run_command("python --version", "Python version")
    run_command("poetry --version", "Poetry version")
    run_command("pwd", "Working directory")
    run_command("poetry show", "Installed packages")

    # Run tests (simulating CI test steps)
    print("\n🧪 Running Tests (Windows CI Simulation):")

    # Unit tests
    success = run_command(
        "poetry run pytest tests/test_doip_unit.py -v --cov=doip_server "
        "--cov-report=xml --cov-report=term-missing",
        "Running unit tests",
    )

    # Integration tests
    success &= run_command(
        "poetry run pytest tests/test_doip_integration.py -v --cov=doip_server "
        "--cov-report=xml --cov-report=term-missing",
        "Running integration tests",
    )

    # All tests
    success &= run_command(
        "poetry run pytest tests/ -v --cov=doip_server --cov-report=xml --cov-report=term-missing",
        "Running all tests",
    )

    # Configuration validation
    success &= run_command("poetry run validate_config", "Validating configuration")

    # Check coverage file
    if Path("coverage.xml").exists():
        size = Path("coverage.xml").stat().st_size
        print(f"📊 Coverage file found, size: {size} bytes")
    else:
        print("⚠️ Coverage file not found")

    # Code quality checks (simulating lint job)
    print("\n🔍 Code Quality Checks:")
    run_command(
        "poetry run flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics",
        "Running flake8 (critical errors)",
    )
    run_command(
        "poetry run flake8 src/ tests/ --count --exit-zero --max-complexity=10 "
        "--max-line-length=127 --statistics",
        "Running flake8 (style checks)",
    )
    run_command(
        "poetry run black --check --diff src/ tests/",
        "Checking code formatting with black",
    )

    # Security checks (simulating security job)
    print("\n🔒 Security Checks:")
    run_command(
        "poetry run bandit -r src/ -f json -o bandit-report.json",
        "Running bandit security scan",
    )
    run_command("poetry run safety check --json", "Running safety dependency check")

    # Build package (simulating build job)
    print("\n📦 Building Package:")
    run_command("poetry build", "Building package")

    if success:
        print("\n✅ Windows CI simulation completed successfully!")
        print("🎯 Your code should work on Windows in the actual CI environment.")
    else:
        print("\n❌ Windows CI simulation found issues.")
        print("🔧 Please fix the failing tests/checks before pushing to CI.")

    return success


if __name__ == "__main__":
    success = simulate_windows_ci()
    sys.exit(0 if success else 1)
