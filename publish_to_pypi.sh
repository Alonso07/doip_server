#!/bin/bash

# DoIP Server PyPI Publishing Script
# This script helps you publish the doip-server package to PyPI

set -e  # Exit on any error

echo "🚀 DoIP Server PyPI Publishing Script"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml not found. Please run this script from the project root directory."
    print_error "Current directory: $(pwd)"
    print_error "Script directory: $SCRIPT_DIR"
    exit 1
fi

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    print_error "Poetry is not installed. Please install Poetry first."
    print_status "You can install Poetry with: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check if we're in a poetry project
if [ ! -f "pyproject.toml" ] || ! grep -q "tool.poetry" pyproject.toml; then
    print_error "This doesn't appear to be a Poetry project. Please run from a Poetry project directory."
    exit 1
fi

# Check if build and twine are installed in poetry environment
if ! poetry run python -c "import build, twine" &> /dev/null; then
    print_status "Installing build and twine in Poetry environment..."
    poetry add --group dev build twine
fi

# Verify poetry environment is activated
print_status "Using Poetry environment: $(poetry env info --path)"

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Run tests
print_status "Running tests..."
poetry run pytest tests/ --tb=no -q
if [ $? -ne 0 ]; then
    print_error "Tests failed. Please fix tests before publishing."
    exit 1
fi
print_success "All tests passed!"

# Build the package
print_status "Building package..."
poetry run python -m build
if [ $? -ne 0 ]; then
    print_error "Build failed."
    exit 1
fi
print_success "Package built successfully!"

# Check the package
print_status "Checking package..."
poetry run twine check dist/*
if [ $? -ne 0 ]; then
    print_error "Package check failed."
    exit 1
fi
print_success "Package check passed!"

# Ask user for publishing target
echo ""
echo "Where would you like to publish?"
echo "1) TestPyPI (recommended for testing)"
echo "2) PyPI (production)"
echo "3) Both (TestPyPI first, then PyPI)"
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        print_status "Publishing to TestPyPI..."
        poetry run twine upload --repository testpypi dist/*
        print_success "Published to TestPyPI! Test with: pip install --index-url https://test.pypi.org/simple/ doip-server"
        ;;
    2)
        print_warning "Publishing to PyPI (production)..."
        read -p "Are you sure you want to publish to PyPI? (y/N): " confirm
        if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
            poetry run twine upload dist/*
            print_success "Published to PyPI! Install with: pip install doip-server"
        else
            print_status "Publishing cancelled."
        fi
        ;;
    3)
        print_status "Publishing to TestPyPI first..."
        poetry run twine upload --repository testpypi dist/*
        print_success "Published to TestPyPI!"
        
        echo ""
        read -p "Test the package from TestPyPI first. Press Enter when ready to publish to PyPI..."
        
        print_warning "Publishing to PyPI (production)..."
        poetry run twine upload dist/*
        print_success "Published to PyPI! Install with: pip install doip-server"
        ;;
    *)
        print_error "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
print_success "Publishing complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Test your package: pip install doip-server"
echo "2. Check your package on PyPI: https://pypi.org/project/doip-server/"
echo "3. Update version in pyproject.toml for future releases"
echo "4. Create a GitHub release with the same version"
