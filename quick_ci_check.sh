#!/bin/bash

# Quick CI Check - Run essential checks before pushing
# This is a faster version that runs the most critical checks

set -e

echo "🚀 Quick CI Check"
echo "================="

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Not in the project root directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
poetry install --no-interaction --no-root

# Run pylint (the main check from your CI)
echo "🔍 Running pylint analysis..."
pylint_result=$(poetry run pylint $(git ls-files '*.py') 2>/dev/null || true)
pylint_score=$(echo "$pylint_result" | tail -1 | grep -o '[0-9]\+\.[0-9]\+/10' | head -1)

echo "Pylint Score: $pylint_score"

# Check if score is above 8.5
if [ -n "$pylint_score" ]; then
    score=$(echo "$pylint_score" | cut -d'/' -f1)
    if (( $(echo "$score >= 8.5" | bc -l) )); then
        echo "✅ Pylint passed (score: $pylint_score)"
    else
        echo "❌ Pylint failed (score: $pylint_score, target: 8.5+)"
        echo "$pylint_result"
        exit 1
    fi
else
    echo "❌ Could not parse pylint score"
    echo "$pylint_result"
    exit 1
fi

# Run tests if they exist
if [ -d "tests" ] && [ -f "tests/conftest.py" ]; then
    echo "🧪 Running tests..."
    poetry run pytest tests/ -v --tb=short
    echo "✅ Tests passed"
fi

echo ""
echo "🎉 All checks passed! Ready to push."
