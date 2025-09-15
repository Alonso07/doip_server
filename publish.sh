#!/bin/bash

# Simple wrapper script to ensure Poetry is used for publishing
# This script ensures the publish_to_pypi.sh script runs in the correct environment

echo "🔧 DoIP Server Publishing Wrapper"
echo "================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the project root directory."
    echo "   Current directory: $(pwd)"
    echo "   Script directory: $SCRIPT_DIR"
    exit 1
fi

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Error: Poetry is not installed or not in PATH."
    echo "📦 Install Poetry with: curl -sSL https://install.python-poetry.org | python3 -"
    echo "   Or visit: https://python-poetry.org/docs/#installation"
    echo ""
    echo "Current PATH: $PATH"
    echo "Poetry locations to check:"
    echo "  - ~/.local/bin/poetry"
    echo "  - /opt/homebrew/bin/poetry"
    echo "  - /usr/local/bin/poetry"
    exit 1
fi

# Ensure we're using the poetry environment
echo "🐍 Using Poetry environment: $(poetry env info --path)"
echo ""

# Run the main publishing script
exec poetry run ./publish_to_pypi.sh
