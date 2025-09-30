# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2025-01-29

### Fixed
- **BREAKING**: Corrected power mode status length from 2 bytes to 1 byte per ISO 13400-2:2025 specification
  - Updated power mode information response payload to use 1-byte status field
  - Modified YAML configuration to use 1-byte hex values (0x01, 0x02, etc.) instead of 2-byte values
  - Updated server implementation to pack status as single byte using `struct.pack(">B", status)`
  - Updated UDP client to parse 1-byte status field correctly
  - Fixed all test cases to expect 1-byte payload length (9 bytes total instead of 10 bytes)

### Changed
- **BREAKING**: Updated DoIP payload types to comply with ISO 13400-2:2025 specification
  - Power Mode Information Request: 0x4003 (UDP)
  - Power Mode Information Response: 0x4004 (UDP) 
  - Alive Check Request: 0x0007 (TCP)
  - Alive Check Response: 0x0008 (TCP)
  - Updated server message processing to use correct payload types
  - Updated UDP client to support power mode information requests/responses
  - Enhanced test coverage with comprehensive end-to-end power mode testing

### Added
- Complete power mode information functionality over UDP
- Comprehensive test suite for power mode information (32 tests)
- End-to-end testing for power mode with custom configurations and response cycling
- UDP client methods for power mode information requests and responses
- Support for power mode response cycling with configurable status sequences

## [0.4.0] - 2024-12-25

### Changed
- **BREAKING**: Updated ECU service configuration naming convention
  - Changed from ECU-specific service names (`abs_services`, `engine_services`, `transmission_services`) to generic `specific_services`
  - This makes the configuration more agnostic and easily extensible for new ECU types
  - Updated `hierarchical_config_manager.py` to use the new naming convention
  - All existing functionality preserved with improved maintainability

### Added
- docs/CONTRIBUTING.md with comprehensive contributor guidelines
- docs/CODE_OF_CONDUCT.md for community standards
- docs/CHANGELOG.md for tracking changes
- docs/SECURITY.md for security reporting

### Changed
- Improved project documentation structure
- Enhanced contributor onboarding experience

## [0.2.2] - 2024-12-19

### Added
- New metadata for project poetry PyPI publishing
- Mirror feature for request handling
- Regular expressions support for request matching
- Executable build support with PyInstaller
- Hierarchical configuration system with subfolder organization
- Comprehensive documentation with docstrings for main classes

### Changed
- Updated GitHub Actions to latest versions
- Migrated from pylint to flake8 for code linting
- Improved code formatting with Black
- Enhanced CI/CD pipeline with better dependency management
- Updated project structure for better separation of concerns

### Fixed
- Response cycling response handling
- Functional address implementation
- Test suite improvements and fixes
- Pipeline configuration issues
- Windows test build compatibility

### Dependencies
- Updated black from ^24.0.0 to ^25.9.0
- Updated pytest from 8.3.5 to 8.4.2
- Updated safety from 2.3.4 to 3.6.1
- Updated pytest-cov from 6.2.1 to 7.0.0

## [0.2.1] - 2024-11-15

### Added
- Multi-service file support
- Enhanced functional addressing
- Improved test coverage

### Fixed
- Functional address handling
- Test suite stability
- Code formatting issues

## [0.2.0] - 2024-10-20

### Added
- Hierarchical configuration system
- Multi-ECU support with individual configurations
- Functional addressing for broadcast diagnostics
- Response cycling for testing scenarios
- UDP vehicle identification
- Comprehensive test suite (185/186 tests passing)
- YAML-based configuration management
- Gateway and ECU-specific configurations

### Changed
- Complete rewrite of configuration system
- Improved architecture for better maintainability
- Enhanced error handling and validation

### Fixed
- Various bug fixes and stability improvements
- Test coverage improvements

## [0.1.0] - 2024-09-01

### Added
- Initial DoIP server implementation
- Basic TCP/UDP support
- Simple configuration system
- Basic UDS services
- Initial test suite

---

## Release Notes

### Version 0.2.2
This release focuses on improving the development experience and project infrastructure. Key highlights include:

- **Enhanced Development Tools**: Migration from pylint to flake8, improved code formatting
- **Build System**: Added PyInstaller support for creating executables
- **Configuration**: Introduced hierarchical configuration system for better organization
- **Documentation**: Comprehensive documentation with detailed API references
- **Testing**: Improved test coverage and CI/CD pipeline

### Version 0.2.1
Minor release with bug fixes and stability improvements:

- **Multi-Service Support**: Ability to handle multiple service configuration files
- **Functional Addressing**: Enhanced support for broadcast diagnostics
- **Test Improvements**: Better test coverage and stability

### Version 0.2.0
Major release introducing the hierarchical configuration system:

- **Hierarchical Configuration**: Complete rewrite of the configuration system
- **Multi-ECU Support**: Individual ECU configurations with service isolation
- **Functional Addressing**: Broadcast communication to multiple ECUs
- **Response Cycling**: Configurable response variations for testing
- **Comprehensive Testing**: 99.5% test pass rate with 185/186 tests

### Version 0.1.0
Initial release with basic DoIP server functionality:

- **Core DoIP Protocol**: TCP/UDP server implementation
- **Basic UDS Services**: Essential diagnostic services
- **Simple Configuration**: Basic YAML configuration support
- **Initial Testing**: Basic test suite

## Migration Guide

### Upgrading from 0.1.x to 0.2.x

The 0.2.x release introduces significant changes to the configuration system:

1. **Configuration Structure**: The old single-file configuration has been replaced with a hierarchical system
2. **File Organization**: Configuration files are now organized in subdirectories
3. **ECU Management**: ECUs now have individual configuration files
4. **Service Definitions**: UDS services are defined in separate files

See the [Configuration Guide](docs/CONFIGURATION.md) for detailed migration instructions.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for information on how to contribute to this project.

## Security

See [SECURITY.md](SECURITY.md) for information on security reporting.
