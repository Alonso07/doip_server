#!/bin/bash

# Universal launcher for DoIP Server publishing scripts
# This script ensures the publishing scripts work in any terminal environment

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the project root directory (parent of scripts directory)
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
cd "$PROJECT_ROOT"

# Function to find poetry in common locations
find_poetry() {
    local poetry_paths=(
        "$HOME/.local/bin/poetry"
        "/opt/homebrew/bin/poetry"
        "/usr/local/bin/poetry"
        "$(which poetry 2>/dev/null)"
    )
    
    for path in "${poetry_paths[@]}"; do
        if [ -x "$path" ] && [ -f "$path" ]; then
            echo "$path"
            return 0
        fi
    done
    
    return 1
}

# Function to setup environment
setup_environment() {
    # Add common poetry paths to PATH if not already present
    local additional_paths=(
        "$HOME/.local/bin"
        "/opt/homebrew/bin"
        "/usr/local/bin"
    )
    
    for path in "${additional_paths[@]}"; do
        if [[ ":$PATH:" != *":$path:"* ]]; then
            export PATH="$path:$PATH"
        fi
    done
}

echo "🔧 DoIP Server Publishing Launcher"
echo "=================================="
echo "Script directory: $SCRIPT_DIR"
echo "Working directory: $(pwd)"

# Setup environment
setup_environment

# Find poetry
POETRY_CMD=$(find_poetry)
if [ -z "$POETRY_CMD" ]; then
    echo "❌ Error: Poetry not found in any common locations."
    echo "📦 Install Poetry with: curl -sSL https://install.python-poetry.org | python3 -"
    echo "   Or visit: https://python-poetry.org/docs/#installation"
    echo ""
    echo "Searched locations:"
    echo "  - $HOME/.local/bin/poetry"
    echo "  - /opt/homebrew/bin/poetry"
    echo "  - /usr/local/bin/poetry"
    echo "  - PATH: $PATH"
    exit 1
fi

echo "✅ Found Poetry at: $POETRY_CMD"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found."
    echo "   Current directory: $(pwd)"
    echo "   Script directory: $SCRIPT_DIR"
    exit 1
fi

# Run the main publishing script
echo "🚀 Starting publishing process..."
exec "$POETRY_CMD" run ./scripts/publish/publish_to_pypi.sh
