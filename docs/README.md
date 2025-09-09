# DoIP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/YOUR_USERNAME/doip_server/workflows/Tests/badge.svg)](https://github.com/YOUR_USERNAME/doip_server/actions)
[![CI](https://github.com/YOUR_USERNAME/doip_server/workflows/CI/badge.svg)](https://github.com/YOUR_USERNAME/doip_server/actions)

A Python implementation of DoIP (Diagnostics over Internet Protocol) server and client with comprehensive YAML configuration management.

## Features

- **DoIP Server**: Full DoIP protocol implementation with routing activation and UDS diagnostic messages
- **DoIP Client**: Complete client implementation with automated testing capabilities
- **UDS Support**: Implements Read Data by Identifier service (0x22) with configurable responses
- **Routing Activation**: Supports DoIP routing activation (0x0005/0x0006) with proper 13-byte payload format
- **Protocol Compliance**: Full DoIP protocol compliance with multiple payload types
- **Configuration-Driven**: YAML-based configuration with interchangeable config files
- **Address Validation**: Configurable source and target address validation
- **Comprehensive Logging**: Configurable logging with file and console output
- **Configuration Validation**: Built-in validation and error checking
- **Extensible Design**: Easy to add new UDS services and routine types
- **Comprehensive Testing**: 186 tests with 99.5% pass rate (185 passing, 1 skipped)
- **Multiple DoIP Message Types**: Supports alive checks, power mode requests, and diagnostic messages

## Installation

```bash
# Install dependencies
poetry install

# Or using pip
pip install -r requirements.txt
```

## Quick Start

### 1. Configuration Setup

The server automatically creates a default configuration if none exists, or you can use the provided templates:

```bash
# Validate default configuration
poetry run validate_config

# Use example configuration
cp config/example_config.yaml config/doip_config.yaml
poetry run validate_config config/doip_config.yaml
```

### 2. Start the DoIP Server

```bash
# Using poetry (uses default config)
poetry run doip_server

# Or directly
python src/doip_server/doip_server.py
```

The server will automatically load configuration from `config/doip_config.yaml` and start listening.

### 3. Run the DoIP Client

```bash
# Using poetry
poetry run doip_client

# Or directly
python src/doip_server/doip_client.py
```

### 4. Test and Validate

```bash
# View message formats (no network required)
poetry run demo

# Run unit tests (fast, no server required)
poetry run pytest tests/test_doip_unit.py -v

# Run integration tests (requires server)
poetry run pytest tests/test_doip_integration.py -v

# Run all tests
poetry run pytest tests/ -v

# Validate configuration
poetry run validate_config
```

## Configuration System

### Overview

The DoIP server now uses a comprehensive YAML-based configuration system that eliminates all hardcoded values:

- **Routine Definitions**: Configure supported routines, response codes, and conditions
- **UDS Services**: Define supported services, data identifiers, and responses
- **Address Management**: Set allowed source and target addresses
- **Response Codes**: Customize all response codes and messages
- **Logging**: Configure log levels, formats, and output destinations
- **Security**: Set access control and authentication requirements

### Configuration File Structure

```yaml
# Server Configuration
server:
  host: "0.0.0.0"        # Server host address
  port: 13400            # Server port
  max_connections: 5     # Maximum concurrent connections
  timeout: 30            # Connection timeout in seconds
```

**Configuration Priority**: The server automatically loads these settings from the YAML configuration file. You can also override them programmatically when creating the server instance.

### Configuration Override

The server supports multiple ways to configure the host and port:

```python
from doip_server.doip_server import DoIPServer

# Use YAML configuration (default)
server = DoIPServer()

# Override specific settings
server = DoIPServer(host='127.0.0.1', port=13400)

# Use custom configuration file
server = DoIPServer(config_path='config/custom_config.yaml')

# Override settings from custom config
server = DoIPServer(host='192.168.1.100', port=9999, config_path='config/custom_config.yaml')
```

**Priority Order**:
1. **Explicit Parameters**: `host` and `port` passed to constructor
2. **YAML Configuration**: Settings from configuration file
3. **Default Values**: Fallback values if configuration is missing

# Address Configuration
addresses:
  allowed_sources: [0x0E00, 0x0E01, 0x0E02]
  target_addresses: [0x1000, 0x1001, 0x1002]
  default_source: 0x1000

# Routine Activation
routine_activation:
  supported_routines:
    0x0202:
      name: "Engine Test Routine"
      description: "Basic engine functionality test"
      response_code: 0x10
      conditions: ["Engine off", "Ignition on"]

# UDS Services
uds_services:
  0x22:
    name: "Read Data by Identifier"
    supported_data_identifiers:
      0xF187:
        name: "Vehicle Identification Number"
        response_data: [0x01, 0x02, 0x03, 0x04]
```

### Configuration Locations

The server automatically finds configuration files in this order:
1. `config/doip_config.yaml` (recommended)
2. `doip_config.yaml` (current directory)
3. `../config/doip_config.yaml` (parent config directory)
4. `src/doip_server/config/doip_config.yaml` (source config directory)

### Configuration Validation

The system provides comprehensive configuration validation:

```bash
# Validate default configuration
poetry run validate_config

# Validate custom configuration
poetry run validate_config /path/to/config.yaml

# Validate and get summary
poetry run validate_config | grep "✅"
```

**Validation Features**:
- **Structure Validation**: Ensures required sections exist
- **Data Validation**: Checks data types and ranges
- **Binding Validation**: Validates host and port configuration
- **Error Reporting**: Clear error messages for configuration issues

**Server Configuration Validation**:
- Host must be non-empty string
- Port must be between 1-65535
- Max connections must be positive integer
- Timeout must be positive number

## Protocol Details

### DoIP Message Format

```
+--------+--------+--------+--------+--------+
| Proto  | Inv    | Payload| Payload| Payload|
| Ver    | Proto  | Type   | Length | Data   |
| (1B)   | Ver(1B)| (2B)  | (4B)  | (nB)  |
+--------+--------+--------+--------+--------+
```

### Supported Payload Types

- **0x0001**: Alive Check Request
- **0x0002**: Alive Check Response  
- **0x0005**: Routing Activation Request
- **0x0006**: Routing Activation Response (13-byte payload with !HHBLL format)
- **0x0007**: Alive Check Request (alternative format)
- **0x0008**: Power Mode Request/Response
- **0x8001**: Diagnostic Message
- **0x8002**: Diagnostic Message ACK
- **0x8003**: Diagnostic Message NACK

### UDS Services

- **0x22**: Read Data by Identifier
  - Configurable data identifiers and responses
  - Automatic positive/negative response generation
  - Customizable error codes and messages

### Routing Activation

- **DoIP Standard Compliance**: Implements proper routing activation (0x0005/0x0006)
- **13-byte Payload Format**: Uses !HHBLL struct format as required by DoIP standard
- **Response Codes**: Customize success and error responses
- **Address Validation**: Validates source and target addresses
- **Multiple Client Support**: Handles multiple concurrent connections

## Example Messages

### Routing Activation Request
```
02 FD 00 05 00 07 0E 00 00 00 00 00 00
```
- Protocol: 0x02
- Inverse: 0xFD  
- Type: 0x0005 (Routing Activation)
- Length: 0x00000007
- Client Address: 0x0E00
- Logical Address: 0x0000
- Response Code: 0x00
- Reserved: 0x00000000

### UDS Read Data by Identifier
```
02 FD 80 01 00 07 0E 00 10 00 22 F1 87
```

### Alive Check Request
```
02 FD 00 01 00 00
```

## Advanced Configuration

### Custom Routine Definitions

```yaml
routine_activation:
  supported_routines:
    0x0202:
      name: "Engine Test Routine"
      description: "Basic engine functionality test"
      type: 0x0001
      response_code: 0x10
      conditions:
        - "Engine off"
        - "Ignition on"
        - "Battery voltage > 12V"
    
    0x0203:
      name: "Emission Test Routine"
      description: "Emission system diagnostic"
      type: 0x0002
      response_code: 0x10
      conditions:
        - "Engine running"
        - "Warm engine (>80°C)"
        - "Vehicle stationary"
```

### Custom UDS Responses

```yaml
uds_services:
  0x22:
    supported_data_identifiers:
      0xF187:
        name: "Vehicle Identification Number"
        description: "VIN data (17 characters)"
        response_data: [0x31, 0x48, 0x4D, 0x42, 0x43, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x30, 0x31, 0x32]
        access_control: "public"
      
      0xF188:
        name: "Vehicle Type"
        description: "Vehicle type information"
        response_data: [0x48, 0x4F, 0x4E, 0x44, 0x41, 0x20, 0x43, 0x49, 0x56, 0x49, 0x43]
        access_control: "public"
```

### Logging Configuration

```yaml
logging:
  level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "doip_server.log"  # Optional file logging
  console: true            # Console output
```

### Security Configuration

```yaml
security:
  enabled: false           # Enable/disable security features
  allowed_sources_strict: false  # Strict source address checking
  require_auth_for:        # Operations requiring authentication
    - "routine_activation"
    - "uds_write_operations"
```

## Testing and Validation

### Test Structure

The project includes a comprehensive test suite organized into logical categories:

```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── test_doip_unit.py             # Unit tests (fast, no server required)
├── test_doip_integration.py      # Integration tests (requires server)
└── run_tests.py                  # Convenient test runner script
```

#### **Unit Tests** (`test_doip_unit.py`)
- **Configuration Manager Tests**: 17 tests covering all configuration functionality
- **Message Format Tests**: Tests for DoIP message construction
- **Fast Execution**: No server startup required (runs in ~0.05s)
- **Comprehensive Coverage**: Tests all configuration aspects
- **100% Pass Rate**: All unit tests consistently pass

#### **Integration Tests** (`test_doip_integration.py`)
- **Server-Client Tests**: Full communication testing with real DoIP client library
- **Message Format Tests**: Message construction validation
- **Configuration Tests**: Server configuration loading and validation
- **Real Network**: Tests actual server-client communication
- **Protocol Compliance**: Tests routing activation, UDS services, alive checks, and power mode
- **12 Tests**: Complete coverage of all DoIP functionality

### Configuration Testing

```bash
# Validate configuration structure
poetry run validate_config

# Test specific configuration file
poetry run validate_config config/example_config.yaml

# Get configuration summary
poetry run validate_config | grep "Configuration Summary"
```

### Running Tests

```bash
# Run unit tests only (fast)
poetry run pytest tests/test_doip_unit.py -v

# Run integration tests only
poetry run pytest tests/test_doip_integration.py -v

# Run all tests
poetry run pytest tests/ -v

# Use convenient test runner
poetry run python tests/run_tests.py unit
poetry run python tests/run_tests.py integration
poetry run python tests/run_tests.py all
poetry run python tests/run_tests.py coverage
```

### Test Coverage

The test suite provides comprehensive coverage:

- **Configuration Management**: Loading, validation, section access
- **Message Formats**: DoIP header construction, payload creation
- **Server Functionality**: Startup, shutdown, message processing
- **Client Functionality**: Connection management, message sending
- **Address Validation**: Source and target address checking
- **Response Handling**: Success and error response validation

### Test Benefits

The reorganized test structure provides several advantages:

- **Better Organization**: Clear separation of unit vs integration tests
- **Improved Performance**: Unit tests run quickly, integration tests only when needed
- **Easier Maintenance**: Focused test files with clear purposes
- **Better Developer Experience**: Fast feedback from unit tests and comprehensive coverage reporting
- **Industry Standards**: Follows pytest best practices and conventions

### Message Format Testing

```bash
# View message construction (no network required)
poetry run demo

# Test specific message types
python src/doip_server/demo.py
```

## Configuration Management

### Environment-Specific Configurations

```bash
# Development configuration
cp config/doip_config.yaml config/doip_dev.yaml
# Edit config/doip_dev.yaml for development settings

# Production configuration
cp config/doip_config.yaml config/doip_prod.yaml
# Edit config/doip_prod.yaml for production settings

# Use specific configuration
poetry run doip_server --config config/doip_prod.yaml
```

### Configuration Reloading

```python
from doip_server.doip_server import DoIPServer

# Create server with configuration
server = DoIPServer(config_path="config/doip_config.yaml")

# Reload configuration at runtime
server.config_manager.reload_config()
```

### Server Information

The server provides methods to access configuration and status information:

```python
# Get binding information (host, port)
host, port = server.get_binding_info()

# Get comprehensive server information
server_info = server.get_server_info()
# Returns: {'host': '0.0.0.0', 'port': 13400, 'max_connections': 5, ...}

# Access configuration manager directly
config = server.config_manager
server_config = config.get_server_config()
```

### Configuration Validation

The system provides comprehensive validation:

- **Structure Validation**: Ensures required sections exist
- **Data Validation**: Checks data types and ranges
- **Dependency Validation**: Validates relationships between sections
- **Error Reporting**: Clear error messages for configuration issues

## Migration from Hardcoded Values

### What Changed

1. **Routine Definitions**: Moved from Python constants to YAML configuration
2. **UDS Responses**: Data identifiers and responses now configurable
3. **Address Validation**: Source and target addresses configurable
4. **Response Codes**: All response codes and messages configurable

### Migration Steps

1. **Create Configuration**: Use provided YAML templates
2. **Transfer Values**: Move hardcoded values to configuration
3. **Validate**: Use validation script to check configuration
4. **Test**: Verify server behavior with new configuration
5. **Deploy**: Replace hardcoded server with configuration-driven version

## Extensibility

### Adding New Features

1. **New UDS Services**: Add to YAML configuration
2. **New Routine Types**: Define in routine_activation section
3. **Custom Response Codes**: Add to response_codes section
4. **Security Features**: Configure in security section

### Configuration Schema

The configuration system is designed to be extensible:

- **New Sections**: Add new top-level configuration sections
- **New Fields**: Extend existing sections with additional fields
- **Validation Rules**: Add custom validation logic
- **Default Values**: Provide sensible defaults for new options

## Troubleshooting

### Common Issues

1. **Configuration Not Found**: Check file paths and permissions
2. **Validation Errors**: Review YAML syntax and required fields
3. **Import Errors**: Ensure PyYAML is installed (`poetry install`)
4. **Permission Denied**: Check file and directory permissions

### Debug Mode

Enable debug logging to see detailed configuration loading:

```yaml
logging:
  level: "DEBUG"
  console: true
```

### Configuration Issues

```bash
# Check configuration syntax
poetry run validate_config

# View configuration summary
poetry run validate_config | grep "✅"

# Test specific configuration
poetry run validate_config /path/to/problematic/config.yaml
```

## Dependencies

- Python 3.8+
- Scapy 2.6.1+
- PyYAML 6.0+
- Standard library modules (socket, struct, threading, logging)

## Project Structure

```
doip_server/
├── config/                     # Configuration files
│   ├── doip_config.yaml       # Main configuration
│   └── example_config.yaml    # Example configuration
├── src/doip_server/
│   ├── doip_server.py         # Configuration-driven server
│   ├── doip_client.py         # Enhanced client
│   ├── config_manager.py      # Configuration management
│   ├── validate_config.py     # Configuration validation
│   └── demo.py               # Message format demo
├── tests/                     # Test suite (reorganized)
│   ├── conftest.py           # Pytest configuration and fixtures
│   ├── test_doip_unit.py     # Unit tests (fast, no server required)
│   ├── test_doip_integration.py  # Integration tests (server-client)
│   └── run_tests.py          # Convenient test runner
├── CONFIGURATION_GUIDE.md     # Comprehensive configuration guide
├── CONFIGURATION_IMPLEMENTATION_SUMMARY.md  # Implementation details
└── README.md                  # This file
```

### Test Organization

The test structure has been reorganized for better maintainability:

- **Unit Tests**: Fast tests for individual components (configuration, message formats)
- **Integration Tests**: Full system testing with server-client communication
- **Test Fixtures**: Shared configuration and test data
- **Test Runner**: Easy execution of different test categories

## Available Commands

```bash
# Server and Client
poetry run doip_server          # Start DoIP server
poetry run doip_client          # Run DoIP client demo

# Configuration and Testing
poetry run validate_config      # Validate configuration
poetry run demo                # View message formats

# Testing
poetry run pytest tests/ -v    # Run all tests
poetry run pytest tests/test_doip_unit.py -v      # Run unit tests
poetry run pytest tests/test_doip_integration.py -v  # Run integration tests

# Development
poetry run main                # Run main application
```

## Continuous Integration

This project uses GitHub Actions for automated testing and quality assurance:

### Automated Workflows

- **Tests**: Runs on every push and pull request
  - Unit tests
  - Integration tests  
  - Configuration validation
  - Demo execution

- **CI**: Comprehensive testing across multiple platforms
  - Python versions: 3.9, 3.10, 3.11, 3.12
  - Operating systems: Ubuntu, macOS, Windows
  - Code quality checks (flake8, black)
  - Security scanning (bandit, safety)
  - Package building

### Local Development

To run the same checks locally:

```bash
# Install development dependencies
poetry install --with dev

# Run code quality checks
poetry run flake8 src/ tests/
poetry run black --check src/ tests/

# Run security checks
poetry run bandit -r src/
poetry run safety check

# Run tests with coverage
poetry run pytest tests/ --cov=doip_server --cov-report=html
```

## Best Practices

1. **Use Descriptive Names**: Give meaningful names to routines and data identifiers
2. **Document Conditions**: Include conditions for routine activation when relevant
3. **Validate Addresses**: Ensure source and target addresses are properly configured
4. **Test Configurations**: Use the validation script before deploying
5. **Version Control**: Keep configuration files in version control
6. **Environment-Specific**: Use different configurations for development, testing, and production

## Future Enhancements

### Planned Features

1. **Hot Reloading**: Reload configuration without server restart
2. **Configuration API**: REST API for configuration management
3. **Templates**: Pre-built configuration templates for common use cases
4. **Validation Rules**: Custom validation rules for specific requirements

### Advanced Configuration

1. **Conditional Logic**: Configuration based on runtime conditions
2. **Dynamic Responses**: Responses that change based on context
3. **Security Policies**: Advanced security configuration options
4. **Performance Tuning**: Configuration for performance optimization

## License

MIT License - see LICENSE file for details.

## Support

For configuration issues:
1. Check the `CONFIGURATION_GUIDE.md` for detailed documentation
2. Use `poetry run validate_config` to validate your configuration
3. Review the example configurations in the `config/` directory
4. Check the `CONFIGURATION_IMPLEMENTATION_SUMMARY.md` for implementation details