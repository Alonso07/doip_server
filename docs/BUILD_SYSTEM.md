# DoIP Server Build System

This document describes the complete build system for creating cross-platform executables of the DoIP Server.

## Overview

The build system creates standalone executables for:
- **Windows** (Windows 10/11)
- **macOS** (Intel and Apple Silicon)
- **Linux** (Ubuntu, CentOS, and other distributions)

## Quick Start

### Local Development

```bash
# Build executable for current platform
make build-exe

# Build and test executable
make build-exe-test

# Clean build and test
make build-exe-clean
```

### Direct Script Usage

```bash
# Build for current platform
./scripts/build_tools/build_executables.sh

# Build and test
./scripts/build_tools/build_executables.sh --test

# Clean build and test
./scripts/build_tools/build_executables.sh --clean --test
```

## Files Structure

```
scripts/build_tools/
├── build_executables.sh    # Main build script
├── test_build.sh          # Test script
├── generate_spec.py       # Dynamic spec file generator
└── README.md              # Detailed documentation

.github/workflows/
└── build-executables.yml  # GitHub Actions CI workflow

requirements-build.txt     # Build dependencies
```

## Features

### ✅ Cross-Platform Support
- Single executable file for each platform
- Windows, macOS, and Linux executables
- Universal macOS binaries (Intel + Apple Silicon)
- Self-contained (no Python installation required)

### ✅ Automated Testing
- Local build testing with `test_build.sh`
- CI/CD testing via GitHub Actions
- Integration tests for built executables

### ✅ Distribution Packages
- Compressed archives (tar.gz, zip)
- Platform-specific runner scripts
- Complete configuration included

### ✅ CI/CD Integration
- GitHub Actions workflow
- Multi-platform builds
- Automatic release creation on tags
- Artifact upload and retention

## Build Process

### 1. Dependencies
- PyInstaller for executable creation
- Project dependencies (PyYAML, doipclient, psutil)
- Platform-specific build tools

### 2. Configuration
- Dynamic PyInstaller spec file generation (`generate_spec.py`)
- Hidden imports for all dependencies
- Data files (configuration) included
- Optimized exclusions to reduce size

### 3. Build Steps
1. **Spec Generation**: Generate PyInstaller spec file dynamically
2. **Analysis**: Analyze dependencies and imports
3. **PYZ Creation**: Create Python bytecode archive
4. **EXE Creation**: Create standalone executable
5. **Testing**: Verify executable functionality
6. **Packaging**: Create distribution packages

### 4. Output
- Single standalone executable file
- Distribution packages with configs
- Platform-specific runner scripts
- Compressed archives for distribution

## Usage Examples

### Basic Build
```bash
# Build for current platform
./scripts/build_tools/build_executables.sh
```

### Test Build
```bash
# Build and test
./scripts/build_tools/build_executables.sh --test
```

### Clean Build
```bash
# Clean and build
./scripts/build_tools/build_executables.sh --clean --test
```

### Makefile Targets
```bash
make build-exe          # Build executable
make build-exe-test     # Build and test
make build-exe-clean    # Clean build and test
```

## CI/CD Pipeline

### GitHub Actions Workflow

The `.github/workflows/build-executables.yml` workflow:

1. **Triggers**:
   - Push to `main` or `develop` branches
   - Pull requests
   - Git tags (creates releases)
   - Manual trigger

2. **Platforms**:
   - Windows (windows-latest)
   - macOS (macos-latest)
   - Linux (ubuntu-latest)

3. **Steps**:
   - Checkout code
   - Set up Python environment
   - Install dependencies
   - Build executable
   - Test executable
   - Create distribution packages
   - Upload artifacts

### Artifacts

Build artifacts are available for 30 days:
- `doip_server_windows` - Windows executable
- `doip_server_macos` - macOS executable
- `doip_server_linux` - Linux executable

## Distribution Packages

### Package Contents
```
doip_server_platform_timestamp/
├── doip_server[.exe]          # Main executable
├── config/                    # Configuration files
│   ├── gateway1.yaml
│   ├── ecus/                  # ECU configurations
│   └── generic/               # Generic services
├── README.md                  # Documentation
├── LICENSE                    # License file
├── run_doip_server.sh         # Linux/macOS runner
└── run_doip_server.bat        # Windows runner
```

### Runner Scripts

**Linux/macOS** (`run_doip_server.sh`):
```bash
#!/bin/bash
./doip_server --gateway-config config/gateway1.yaml "$@"
```

**Windows** (`run_doip_server.bat`):
```batch
@echo off
doip_server.exe --gateway-config config\gateway1.yaml %*
```

## Troubleshooting

### Common Issues

1. **"Executable not found"**
   - Check if build completed successfully
   - Verify build directory exists
   - Run with `--clean` flag

2. **"Permission denied"**
   - Make scripts executable: `chmod +x scripts/build_tools/*.sh`
   - Check file permissions

3. **"PyInstaller not found"**
   - Install PyInstaller: `pip install pyinstaller`
   - Activate virtual environment

4. **"Import errors"**
   - Check hidden imports in spec file
   - Verify all dependencies are installed

### Debug Mode

Enable debug output:
```bash
export PYINSTALLER_DEBUG=1
./scripts/build_tools/build_executables.sh --clean --test
```

## Performance

### Executable Size
- **macOS**: ~8MB single file
- **Windows**: ~8MB single file
- **Linux**: ~8MB single file

### Build Time
- **Local**: ~30-60 seconds
- **CI/CD**: ~5-10 minutes per platform

## Security

### Code Signing
- macOS executables are automatically signed
- Windows executables can be signed with certificates
- Linux executables use standard ELF format

### Dependencies
- All dependencies are bundled
- No external network access required
- Configuration files included

## Maintenance

### Adding Dependencies
1. Update `requirements-build.txt`
2. Add to `hidden_imports` in `doip_server.spec`
3. Test build locally
4. Update CI workflow if needed

### Updating PyInstaller
1. Update version in `requirements-build.txt`
2. Test build on all platforms
3. Update CI workflow if needed

## Support

For build-related issues:
1. Check this documentation
2. Review build logs
3. Test locally with debug mode
4. Create GitHub issue with details

## License

This build system is part of the DoIP Server project and follows the same MIT license.
