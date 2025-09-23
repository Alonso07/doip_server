# DoIP Server Build System

This directory contains scripts and configuration files for building DoIP Server executables across multiple platforms using PyInstaller.

## Overview

The build system creates standalone executables for:
- **Windows** (Windows 10/11)
- **macOS** (Intel and Apple Silicon)
- **Linux** (Ubuntu, CentOS, and other distributions)

## Files

- `build_executables.sh` - Main build script for local development
- `test_build.sh` - Test script to verify built executables
- `generate_spec.py` - Dynamic PyInstaller spec file generator
- `requirements-build.txt` - Build dependencies

## Quick Start

### Local Build

1. **Install dependencies:**
   ```bash
   # Install PyInstaller
   pip install pyinstaller
   
   # Or install from requirements
   pip install -r requirements-build.txt
   ```

2. **Build executable:**
   ```bash
   # Build for current platform
   ./scripts/build_tools/build_executables.sh
   
   # Clean build and test
   ./scripts/build_tools/build_executables.sh --clean --test
   ```

3. **Test the build:**
   ```bash
   ./scripts/build_tools/test_build.sh
   ```

### CI/CD Build

The GitHub Actions workflow automatically builds executables for all platforms on:
- Push to `main` or `develop` branches
- Pull requests
- Git tags (creates releases)
- Manual trigger via workflow_dispatch

## Build Script Usage

### `build_executables.sh`

```bash
./scripts/build_tools/build_executables.sh [OPTIONS]

OPTIONS:
    -c, --clean          Clean build directory before building
    -t, --test           Test the built executable
    -p, --platform PLAT  Target platform (auto-detected if not specified)
    -h, --help           Show help message

EXAMPLES:
    ./scripts/build_tools/build_executables.sh                    # Build for current platform
    ./scripts/build_tools/build_executables.sh --clean --test    # Clean build and test
    ./scripts/build_tools/build_executables.sh --platform linux  # Build for Linux
```

### `test_build.sh`

```bash
./scripts/build_tools/test_build.sh
```

Tests the built executable for:
- Basic functionality (--help, --version)
- Error handling
- Configuration file loading
- Integration test (server startup)

## Build Output

### Directory Structure

```
dist/executables/
├── doip_server/                    # Executable directory
│   ├── doip_server[.exe]          # Main executable
│   ├── _internal/                  # PyInstaller internal files
│   └── ...                        # Other dependencies
├── doip_server_platform_timestamp/ # Distribution package
│   ├── doip_server/               # Executable
│   ├── config/                    # Configuration files
│   ├── README.md                  # Documentation
│   ├── LICENSE                    # License file
│   ├── run_doip_server.sh         # Linux/macOS runner script
│   └── run_doip_server.bat        # Windows runner script
├── doip_server_platform_timestamp.tar.gz  # Compressed package
└── doip_server_platform_timestamp.zip     # Compressed package
```

### Executable Features

- **Standalone**: No Python installation required
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Self-contained**: Includes all dependencies
- **Configurable**: Uses YAML configuration files
- **Runnable**: Includes platform-specific runner scripts

## Configuration

### Dynamic Spec File Generation

The `generate_spec.py` script creates PyInstaller spec files dynamically:
- Entry point: `src/doip_server/main.py`
- Data files: Configuration files from `config/`
- Hidden imports: All required dependencies
- Excludes: Unnecessary packages to reduce size
- Output: Single executable with console interface
- Auto-cleanup: Generated spec files are removed after build

### Build Dependencies

- **PyInstaller**: Creates standalone executables
- **PyYAML**: Configuration file parsing
- **doipclient**: DoIP protocol implementation
- **psutil**: System utilities

## Platform-Specific Notes

### Windows
- Creates `doip_server.exe`
- Includes Windows batch file runner
- Tested on Windows 10/11

### macOS
- Creates `doip_server` executable
- Universal binary (Intel + Apple Silicon)
- Tested on macOS 12+

### Linux
- Creates `doip_server` executable
- Tested on Ubuntu 20.04+, CentOS 8+
- Requires glibc 2.17+

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

4. **"Configuration file not found"**
   - Ensure `config/` directory exists
   - Check file paths in spec file

### Debug Mode

Enable debug output:
```bash
# Set debug environment variable
export PYINSTALLER_DEBUG=1

# Run build with verbose output
./scripts/build_tools/build_executables.sh --clean --test
```

### Size Optimization

To reduce executable size:
1. Remove unused dependencies from `excludes` list
2. Use `--onefile` option (single file executable)
3. Strip debug symbols
4. Use UPX compression

## CI/CD Integration

### GitHub Actions

The workflow file `.github/workflows/build-executables.yml` provides:
- Multi-platform builds (Windows, macOS, Linux)
- Automated testing
- Artifact upload
- Release creation on tags

### Manual Trigger

Trigger builds manually:
1. Go to Actions tab in GitHub
2. Select "Build Executables" workflow
3. Click "Run workflow"
4. Choose platforms and branch

### Artifacts

Build artifacts are available for 30 days:
- `doip_server_windows` - Windows executable
- `doip_server_macos` - macOS executable  
- `doip_server_linux` - Linux executable

## Development

### Adding New Dependencies

1. Update `requirements-build.txt`
2. Add to `hidden_imports` in `doip_server.spec`
3. Test build locally
4. Update CI workflow if needed

### Modifying Build Process

1. Edit `doip_server.spec` for PyInstaller configuration
2. Update `build_executables.sh` for build logic
3. Modify `.github/workflows/build-executables.yml` for CI
4. Test changes locally first

## Support

For build-related issues:
1. Check this README
2. Review build logs
3. Test locally with debug mode
4. Create GitHub issue with details

## License

This build system is part of the DoIP Server project and follows the same MIT license.
