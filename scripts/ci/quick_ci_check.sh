#!/bin/bash

# Quick CI Check - Run essential checks before pushing
# This is a faster version that runs the most critical checks

set -e

echo " Quick CI Check"
echo "================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo " Not in the project root directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
poetry install --no-interaction --no-root

# Run flake8 linting
echo "🔍 Running flake8 linting..."
poetry run flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
poetry run flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
echo "✅ Flake8 linting passed"

# Run tests if they exist
if [ -d "tests" ] && [ -f "tests/conftest.py" ]; then
    echo " Running tests..."
    poetry run pytest tests/ -v --tb=short
    echo "✅ Tests passed"
fi

echo ""
echo "🎉 All checks passed! Ready to push."
