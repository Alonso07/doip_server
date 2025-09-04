# DoIP Server Configuration Guide

This guide explains how to configure the DoIP server using YAML configuration files to customize behavior, supported UDS services, and responses.

## Overview

The DoIP server uses a comprehensive configuration-driven approach that allows you to:
- Configure UDS services and data identifiers with custom responses
- Set allowed source and target addresses
- Customize response codes and messages
- Configure logging and security settings
- Use interchangeable configuration files (`doip_config.yaml` and `example_config.yaml`)

## Current Status: ✅ Production Ready

- **29 Tests Passing**: 17 unit tests + 12 integration tests
- **Full DoIP Compliance**: Supports all major DoIP message types
- **Real Client Compatible**: Works with actual DoIP client libraries
- **Configuration Validated**: All configurations tested and working

## Configuration File Structure

The configuration is stored in YAML format with the following main sections:

### 1. Server Configuration
```yaml
server:
  host: "0.0.0.0"        # Server host address
  port: 13400            # Server port
  max_connections: 5     # Maximum concurrent connections
  timeout: 30            # Connection timeout in seconds
```

### 2. Protocol Configuration
```yaml
protocol:
  version: 0x02          # DoIP protocol version
  inverse_version: 0xFD  # Inverse protocol version
```

### 3. Address Configuration
```yaml
addresses:
  allowed_sources:        # Source addresses allowed to send requests
    - 0x0E00             # Tester 1
    - 0x0E01             # Tester 2
  
  target_addresses:       # Addresses this server represents
    - 0x1000             # ECU 1
    - 0x1001             # ECU 2
  
  default_source: 0x1000 # Default source address for responses
```

### 4. Routine Activation Configuration
```yaml
routine_activation:
  supported_routines:
    0x0202:               # Routine identifier
      name: "Test Routine"
      description: "Basic test routine"
      type: 0x0001        # Routine type
      response_code: 0x10 # Success response code
      conditions:          # Optional conditions
        - "Engine off"
        - "Ignition on"
  
  default_response:        # Response for unsupported routines
    code: 0x31            # NRC code
    message: "Routine not supported"
```

### 5. UDS Services Configuration
```yaml
uds_services:
  0x22:                   # UDS service ID (Read Data by Identifier)
    name: "Read Data by Identifier"
    description: "Read data by identifier service"
    
    supported_data_identifiers:
      0xF187:             # Data identifier
        name: "VIN"
        description: "Vehicle Identification Number"
        response_data: [0x01, 0x02, 0x03, 0x04]  # Response data
        response_format: "raw"
        access_control: "public"
    
    default_negative_response:
      code: 0x31          # NRC for unsupported data identifiers
      message: "Data identifier not supported"
```

### 6. Response Codes Configuration
```yaml
response_codes:
  routine_activation:      # Routine activation response codes
    0x10: "Routine started successfully"
    0x22: "Conditions not correct"
    0x31: "Incorrect routine identifier"
  
  uds:                     # UDS response codes
    0x10: "General reject"
    0x31: "Request out of range"
    0x7F: "Service not supported"
```

### 7. Logging Configuration
```yaml
logging:
  level: "INFO"           # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "doip_server.log" # Log file path (optional)
  console: true           # Enable console logging
```

### 8. Security Configuration
```yaml
security:
  enabled: false          # Enable/disable security features
  allowed_sources_strict: false  # Strict source address checking
  require_auth_for:       # Operations requiring authentication
    - "routine_activation"
    - "uds_write_operations"
```

## Configuration File Locations

The server looks for configuration files in the following order:
1. `config/doip_config.yaml` (recommended)
2. `doip_config.yaml` (current directory)
3. `../config/doip_config.yaml` (parent config directory)
4. `src/scapy_test/config/doip_config.yaml` (source config directory)

If no configuration file is found, a default configuration is created automatically.

## Using Custom Configurations

### Method 1: Command Line
```bash
# Start server with custom configuration
poetry run doip_server --config /path/to/custom_config.yaml

# Or in Python
from scapy_test.doip_server import DoIPServer
server = DoIPServer(config_path="/path/to/custom_config.yaml")
```

### Method 2: Environment Variable
```bash
export DOIP_CONFIG_PATH="/path/to/custom_config.yaml"
poetry run doip_server
```

### Method 3: Default Location
Place your configuration file at `config/doip_config.yaml` and it will be loaded automatically.

## Configuration Validation

Use the validation script to check your configuration:
```bash
# Validate default configuration
poetry run validate_config

# Validate custom configuration
poetry run validate_config /path/to/config.yaml
```

## Example Configurations

### Basic Configuration
```yaml
server:
  host: "127.0.0.1"
  port: 13400

addresses:
  allowed_sources: [0x0E00]
  target_addresses: [0x1000]
  default_source: 0x1000

routine_activation:
  supported_routines:
    0x0202:
      name: "Basic Test"
      response_code: 0x10

uds_services:
  0x22:
    supported_data_identifiers:
      0xF187:
        response_data: [0x01, 0x02, 0x03, 0x04]
```

### Advanced Configuration
```yaml
server:
  host: "0.0.0.0"
  port: 13400
  max_connections: 10
  timeout: 60

addresses:
  allowed_sources: [0x0E00, 0x0E01, 0x0E02]
  target_addresses: [0x1000, 0x1001, 0x1002]
  default_source: 0x1000

routine_activation:
  supported_routines:
    0x0202:
      name: "Engine Test"
      description: "Engine functionality test"
      type: 0x0001
      response_code: 0x10
      conditions: ["Engine off", "Ignition on"]
    
    0x0203:
      name: "Emission Test"
      description: "Emission system diagnostic"
      type: 0x0002
      response_code: 0x10
      conditions: ["Engine running", "Warm engine"]
  
  default_response:
    code: 0x31
    message: "Routine not supported"

uds_services:
  0x22:
    name: "Read Data by Identifier"
    supported_data_identifiers:
      0xF187:
        name: "VIN"
        description: "Vehicle Identification Number"
        response_data: [0x31, 0x48, 0x4D, 0x42, 0x43, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x30, 0x31, 0x32]
        access_control: "public"
      
      0xF188:
        name: "Vehicle Type"
        description: "Vehicle type information"
        response_data: [0x48, 0x4F, 0x4D, 0x44, 0x41, 0x20, 0x43, 0x49, 0x56, 0x49, 0x43]
        access_control: "public"
    
    default_negative_response:
      code: 0x31
      message: "Data identifier not supported"

logging:
  level: "DEBUG"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "doip_server.log"
  console: true

security:
  enabled: false
  allowed_sources_strict: false
```

## Best Practices

1. **Use Descriptive Names**: Give meaningful names to routines and data identifiers
2. **Document Conditions**: Include conditions for routine activation when relevant
3. **Validate Addresses**: Ensure source and target addresses are properly configured
4. **Test Configurations**: Use the validation script before deploying
5. **Version Control**: Keep configuration files in version control
6. **Environment-Specific**: Use different configurations for development, testing, and production

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

### Configuration Reload

The server can reload configuration at runtime:
```python
server.config_manager.reload_config()
```

## Migration from Hardcoded Values

If you're migrating from the previous hardcoded implementation:

1. **Create Configuration File**: Use the provided template
2. **Move Hardcoded Values**: Transfer routines, UDS services, and addresses
3. **Test Configuration**: Use validation script
4. **Update Server**: Restart with new configuration
5. **Verify Functionality**: Test all supported operations

## Extending Configuration

To add new configuration options:

1. **Update YAML Schema**: Add new sections and fields
2. **Extend ConfigManager**: Add getter methods for new options
3. **Update Server Logic**: Use new configuration values
4. **Add Validation**: Include new fields in validation logic
5. **Update Documentation**: Document new configuration options

The configuration system is designed to be extensible, allowing you to add new features without modifying the core server code.
