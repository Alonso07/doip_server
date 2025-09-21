#!/bin/bash

# Local CI Testing Script
# This script runs the same checks that GitHub Actions would run locally

set -e  # Exit on any error

echo "🚀 Running Local CI Tests"
echo "========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Not in the project root directory. Please run from the project root."
    exit 1
fi

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install poetry first."
    exit 1
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    print_error "Git is not available. Please install git first."
    exit 1
fi

echo ""
echo "📋 Running Tests for Python Versions: 3.9, 3.10, 3.11"
echo ""

# Test each Python version (simulate the matrix strategy)
for python_version in "3.9" "3.10" "3.11"; do
    echo "🐍 Testing Python $python_version"
    echo "----------------------------------------"
    
    # Set up Python version (if pyenv is available)
    if command -v pyenv &> /dev/null; then
        print_status "Setting Python version to $python_version"
        pyenv local $python_version
    else
        print_warning "pyenv not found, using system Python"
    fi
    
    # Install dependencies
    print_status "Installing dependencies with poetry"
    poetry install --no-interaction --no-root
    
    # Run flake8 linting (replacing pylint)
    print_status "Running flake8 linting"
    poetry run flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
    poetry run flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    print_status "Flake8 linting passed"
    
    echo ""
done

# Run tests (if you have them)
if [ -d "tests" ]; then
    echo "🧪 Running Test Suite"
    echo "--------------------"
    print_status "Running pytest"
    poetry run pytest tests/ -v --tb=short || {
        print_error "Tests failed"
        exit 1
    }
    print_status "All tests passed"
    echo ""
fi

# Run other checks that might be in your CI
echo "🔍 Running Additional Checks"
echo "----------------------------"

# Check code formatting (if black is installed)
if poetry run black --version &> /dev/null; then
    print_status "Checking code formatting with black"
    poetry run black --check src/ tests/ || {
        print_warning "Code formatting issues found. Run 'poetry run black src/ tests/' to fix."
    }
fi

# Check import sorting (if isort is installed)
if poetry run isort --version &> /dev/null; then
    print_status "Checking import sorting with isort"
    poetry run isort --check-only src/ tests/ || {
        print_warning "Import sorting issues found. Run 'poetry run isort src/ tests/' to fix."
    }
fi

# Security check (if bandit is installed)
if poetry run bandit --version &> /dev/null; then
    print_status "Running security check with bandit"
    poetry run bandit -r src/ -f json -o bandit-report.json || {
        print_warning "Security issues found. Check bandit-report.json for details."
    }
fi

echo ""
print_status "🎉 All CI checks passed! Ready to push to remote."
echo ""
echo "Next steps:"
echo "1. git add ."
echo "2. git commit -m 'Your commit message'"
echo "3. git push origin main"
