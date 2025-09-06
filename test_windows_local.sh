#!/bin/bash

# Local Windows CI Testing Script
# This script simulates the Windows CI environment locally

echo "🚀 Local Windows CI Testing for DoIP Server"
echo "============================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create a Windows-based test container
echo "📦 Creating Windows test container..."

# Use a Windows-based Python image
docker run --rm -it \
    -v "$(pwd)":/workspace \
    -w /workspace \
    python:3.11-windowsservercore \
    powershell -Command "
        Write-Host '🐍 Setting up Python environment...'
        
        # Install Poetry
        (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
        
        # Add Poetry to PATH
        `$env:PATH += ';C:\Users\ContainerUser\AppData\Roaming\Python\Scripts'
        
        # Verify Poetry installation
        poetry --version
        
        # Install dependencies
        Write-Host '📦 Installing dependencies...'
        poetry install --no-interaction --no-root
        
        # Show environment info
        Write-Host '🔍 Environment Information:'
        python --version
        poetry --version
        Get-Location
        poetry show
        
        # Run tests
        Write-Host '🧪 Running tests...'
        poetry run pytest tests/test_doip_unit.py -v --cov=doip_server --cov-report=xml --cov-report=term-missing
        
        # Run integration tests
        Write-Host '🔗 Running integration tests...'
        poetry run pytest tests/test_doip_integration.py -v --cov=doip_server --cov-report=xml --cov-report=term-missing
        
        # Validate configuration
        Write-Host '⚙️ Validating configuration...'
        poetry run validate_config
        
        Write-Host '✅ Windows CI simulation completed!'
    "
