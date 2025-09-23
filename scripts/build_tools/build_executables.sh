#!/bin/bash

# Build Executables Script for DoIP Server
# This script builds executables for the current platform using PyInstaller
# and provides options for testing the builds locally

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

# Default values
CLEAN_BUILD=false
TEST_BUILD=false
PLATFORM=""
BUILD_DIR="$PROJECT_ROOT/dist/executables"
VENV_DIR="$PROJECT_ROOT/.venv-313"

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

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build DoIP Server executables using PyInstaller

OPTIONS:
    -c, --clean          Clean build directory before building
    -t, --test           Test the built executable
    -p, --platform PLAT  Target platform (auto-detected if not specified)
    -h, --help           Show this help message

EXAMPLES:
    $0                    # Build for current platform
    $0 --clean --test    # Clean build and test
    $0 --platform linux  # Build for Linux (if on compatible system)

EOF
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

# Function to check dependencies
check_dependencies() {
    print_info "Checking dependencies..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found at $VENV_DIR"
        print_info "Please run: python3 -m venv .venv-313"
        exit 1
    fi
    
    # Check if PyInstaller is installed
    if ! "$VENV_DIR/bin/python" -c "import PyInstaller" 2>/dev/null; then
        print_warning "PyInstaller not found, installing..."
        "$VENV_DIR/bin/pip" install pyinstaller
    fi
    
    print_success "Dependencies check passed"
}

# Function to clean build directory
clean_build() {
    print_info "Cleaning build directory..."
    if [ -d "$BUILD_DIR" ]; then
        rm -rf "$BUILD_DIR"
        print_success "Build directory cleaned"
    else
        print_info "Build directory does not exist, nothing to clean"
    fi
}

# Function to build executable
build_executable() {
    print_info "Building executable for platform: $PLATFORM"
    
    # Create build directory
    mkdir -p "$BUILD_DIR"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Generate PyInstaller spec file dynamically
    print_info "Generating PyInstaller spec file..."
    python3 "$SCRIPT_DIR/generate_spec.py" "$PROJECT_ROOT" "$PROJECT_ROOT/doip_server.spec"
    
    # Build with PyInstaller
    print_info "Running PyInstaller..."
    python3 -m PyInstaller \
        --clean \
        --noconfirm \
        --distpath "$BUILD_DIR" \
        --workpath "$PROJECT_ROOT/build" \
        doip_server.spec
    
    print_success "Build completed successfully"
    
    # Clean up generated spec file
    if [ -f "$PROJECT_ROOT/doip_server.spec" ]; then
        rm -f "$PROJECT_ROOT/doip_server.spec"
        print_info "Cleaned up generated spec file"
    fi
    
    # Show build results
    print_info "Build artifacts:"
    if [ -d "$BUILD_DIR" ]; then
        ls -la "$BUILD_DIR/"
    else
        print_warning "No build artifacts found"
    fi
}

# Function to test executable
test_executable() {
    print_info "Testing executable..."
    
    local exe_path=""
    if [ "$PLATFORM" = "windows" ]; then
        exe_path="$BUILD_DIR/doip_server.exe"
    else
        exe_path="$BUILD_DIR/doip_server"
    fi
    
    if [ ! -f "$exe_path" ]; then
        print_error "Executable not found at $exe_path"
        return 1
    fi
    
    # Test basic functionality
    print_info "Testing help command..."
    if "$exe_path" --help > /dev/null 2>&1; then
        print_success "Executable responds to --help"
    else
        print_error "Executable failed --help test"
        return 1
    fi
    
    # Test version info (if available)
    print_info "Testing version command..."
    if "$exe_path" --version > /dev/null 2>&1; then
        print_success "Executable responds to --version"
    else
        print_warning "Executable does not support --version"
    fi
    
    print_success "Executable tests passed"
}

# Function to create distribution package
create_distribution() {
    print_info "Creating distribution package..."
    
    local dist_name="doip_server_${PLATFORM}_$(date +%Y%m%d_%H%M%S)"
    local dist_path="$BUILD_DIR/$dist_name"
    
    # Create distribution directory
    mkdir -p "$dist_path"
    
    # Copy executable and config
    if [ -f "$BUILD_DIR/doip_server" ]; then
        cp "$BUILD_DIR/doip_server" "$dist_path/"
    elif [ -f "$BUILD_DIR/doip_server.exe" ]; then
        cp "$BUILD_DIR/doip_server.exe" "$dist_path/"
    else
        print_error "Executable not found in build directory"
        return 1
    fi
    cp -r "$PROJECT_ROOT/config" "$dist_path/"
    cp "$PROJECT_ROOT/README.md" "$dist_path/"
    cp "$PROJECT_ROOT/LICENSE" "$dist_path/"
    
    # Create run script
    cat > "$dist_path/run_doip_server.sh" << 'EOF'
#!/bin/bash
# DoIP Server Runner Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

        # Check if executable exists
        if [ -f "./doip_server" ]; then
          ./doip_server --gateway-config config/gateway1.yaml "$@"
        elif [ -f "./doip_server.exe" ]; then
          ./doip_server.exe --gateway-config config/gateway1.yaml "$@"
        else
          echo "Error: DoIP Server executable not found"
          exit 1
        fi
EOF
    
    chmod +x "$dist_path/run_doip_server.sh"
    
    # Create Windows batch file
    cat > "$dist_path/run_doip_server.bat" << 'EOF'
@echo off
REM DoIP Server Runner Script for Windows

cd /d "%~dp0"

        REM Check if executable exists
        if exist "doip_server.exe" (
          doip_server.exe --gateway-config config\gateway1.yaml %*
        ) else (
          echo Error: DoIP Server executable not found
          exit /b 1
        )
EOF
    
    # Create archive
    cd "$BUILD_DIR"
    if command -v tar &> /dev/null; then
        tar -czf "${dist_name}.tar.gz" "$dist_name"
        print_success "Created distribution: ${dist_name}.tar.gz"
    fi
    
    if command -v zip &> /dev/null; then
        zip -r "${dist_name}.zip" "$dist_name"
        print_success "Created distribution: ${dist_name}.zip"
    fi
    
    print_success "Distribution package created: $dist_path"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--clean)
            CLEAN_BUILD=true
            shift
            ;;
        -t|--test)
            TEST_BUILD=true
            shift
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Set platform if not specified
if [ -z "$PLATFORM" ]; then
    PLATFORM=$(detect_platform)
fi

# Main execution
print_info "Starting DoIP Server build process..."
print_info "Platform: $PLATFORM"
print_info "Project root: $PROJECT_ROOT"
print_info "Build directory: $BUILD_DIR"

# Check dependencies
check_dependencies

# Clean if requested
if [ "$CLEAN_BUILD" = true ]; then
    clean_build
fi

# Build executable
build_executable

# Test if requested
if [ "$TEST_BUILD" = true ]; then
    test_executable
fi

# Create distribution package
create_distribution

print_success "Build process completed successfully!"
print_info "Executable location: $BUILD_DIR/doip_server"
print_info "Distribution packages: $BUILD_DIR/*.tar.gz, $BUILD_DIR/*.zip"
