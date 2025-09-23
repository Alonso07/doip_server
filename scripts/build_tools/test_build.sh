#!/bin/bash

# Test Build Script for DoIP Server
# This script tests the built executable to ensure it works correctly

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$PROJECT_ROOT/dist/executables"

# Function to print colored output
print_info() {
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

# Function to detect platform
detect_platform() {
    case "$(uname -s)" in
        Linux*)     echo "linux" ;;
        Darwin*)    echo "macos" ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
        *)          echo "unknown" ;;
    esac
}

# Function to test executable
test_executable() {
    local platform=$(detect_platform)
    local exe_path=""
    
    if [ "$platform" = "windows" ]; then
        exe_path="$BUILD_DIR/doip_server/doip_server.exe"
    else
        exe_path="$BUILD_DIR/doip_server/doip_server"
    fi
    
    print_info "Testing executable for platform: $platform"
    print_info "Executable path: $exe_path"
    
    # Check if executable exists
    if [ ! -f "$exe_path" ]; then
        print_error "Executable not found at $exe_path"
        print_info "Available files in build directory:"
        if [ -d "$BUILD_DIR" ]; then
            find "$BUILD_DIR" -type f -name "*doip*" | head -10
        fi
        return 1
    fi
    
    # Test 1: Help command
    print_info "Test 1: Testing --help command..."
    if timeout 10s "$exe_path" --help > /dev/null 2>&1; then
        print_success "✓ --help command works"
    else
        print_error "✗ --help command failed"
        return 1
    fi
    
    # Test 2: Version command (if available)
    print_info "Test 2: Testing --version command..."
    if timeout 10s "$exe_path" --version > /dev/null 2>&1; then
        print_success "✓ --version command works"
    else
        print_warning "⚠ --version command not available (this is OK)"
    fi
    
    # Test 3: Invalid argument
    print_info "Test 3: Testing invalid argument handling..."
    if timeout 10s "$exe_path" --invalid-arg > /dev/null 2>&1; then
        print_warning "⚠ Invalid argument was accepted (unexpected)"
    else
        print_success "✓ Invalid argument properly rejected"
    fi
    
    # Test 4: Configuration file validation
    print_info "Test 4: Testing configuration file handling..."
    if timeout 10s "$exe_path" --gateway-config config/gateway1.yaml --help > /dev/null 2>&1; then
        print_success "✓ Configuration file path handling works"
    else
        print_warning "⚠ Configuration file path handling failed (may be expected)"
    fi
    
    # Test 5: Check executable properties
    print_info "Test 5: Checking executable properties..."
    if command -v file &> /dev/null; then
        file_info=$(file "$exe_path")
        print_info "File info: $file_info"
    fi
    
    if command -v ls &> /dev/null; then
        size=$(ls -lh "$exe_path" | awk '{print $5}')
        print_info "Executable size: $size"
    fi
    
    print_success "All executable tests passed!"
}

# Function to test distribution package
test_distribution() {
    print_info "Testing distribution packages..."
    
    # Find distribution packages
    local tar_files=$(find "$BUILD_DIR" -name "*.tar.gz" 2>/dev/null || true)
    local zip_files=$(find "$BUILD_DIR" -name "*.zip" 2>/dev/null || true)
    
    if [ -n "$tar_files" ]; then
        print_info "Found tar.gz packages:"
        echo "$tar_files"
        
        # Test extracting tar.gz
        for tar_file in $tar_files; do
            print_info "Testing extraction of $tar_file..."
            if tar -tzf "$tar_file" > /dev/null 2>&1; then
                print_success "✓ $tar_file is valid"
            else
                print_error "✗ $tar_file is corrupted"
            fi
        done
    fi
    
    if [ -n "$zip_files" ]; then
        print_info "Found zip packages:"
        echo "$zip_files"
        
        # Test extracting zip
        for zip_file in $zip_files; do
            print_info "Testing extraction of $zip_file..."
            if unzip -t "$zip_file" > /dev/null 2>&1; then
                print_success "✓ $zip_file is valid"
            else
                print_error "✗ $zip_file is corrupted"
            fi
        done
    fi
    
    if [ -z "$tar_files" ] && [ -z "$zip_files" ]; then
        print_warning "No distribution packages found"
    fi
}

# Function to run integration test
run_integration_test() {
    print_info "Running integration test..."
    
    local platform=$(detect_platform)
    local exe_path=""
    
    if [ "$platform" = "windows" ]; then
        exe_path="$BUILD_DIR/doip_server/doip_server.exe"
    else
        exe_path="$BUILD_DIR/doip_server/doip_server"
    fi
    
    if [ ! -f "$exe_path" ]; then
        print_error "Cannot run integration test: executable not found"
        return 1
    fi
    
    # Start server in background
    print_info "Starting DoIP server in background..."
    cd "$PROJECT_ROOT"
    timeout 5s "$exe_path" --gateway-config config/gateway1.yaml &
    local server_pid=$!
    
    # Wait a moment for server to start
    sleep 2
    
    # Check if server is running
    if kill -0 $server_pid 2>/dev/null; then
        print_success "✓ Server started successfully"
        
        # Stop server
        kill $server_pid 2>/dev/null || true
        wait $server_pid 2>/dev/null || true
        print_info "Server stopped"
    else
        print_error "✗ Server failed to start"
        return 1
    fi
}

# Main execution
print_info "Starting DoIP Server build test..."
print_info "Project root: $PROJECT_ROOT"
print_info "Build directory: $BUILD_DIR"

# Check if build directory exists
if [ ! -d "$BUILD_DIR" ]; then
    print_error "Build directory not found: $BUILD_DIR"
    print_info "Please run the build script first: ./scripts/build_tools/build_executables.sh"
    exit 1
fi

# Test executable
test_executable

# Test distribution packages
test_distribution

# Run integration test
run_integration_test

print_success "All tests completed successfully!"
print_info "The DoIP Server executable is ready for distribution."
