# Configuration Guide

This guide explains how to configure the DoIP server using hierarchical YAML configuration files.

## Overview

The DoIP server uses a hierarchical configuration system that allows you to:
- Configure gateway settings (network, protocol, logging)
- Define ECU configurations with individual settings
- Set up UDS services and responses
- Configure functional addressing
- Set up response cycling for testing

## Configuration Structure

### Gateway Configuration (`config/gateway1.yaml`)

```yaml
gateway:
  name: "DoIP Gateway"
  description: "Main DoIP gateway server"
  logical_address: 0x1000
  
  network:
    host: "0.0.0.0"
    port: 13400
    max_connections: 10
    timeout: 60
    
  protocol:
    version: 0x02
    inverse_version: 0xFD
    
  ecus:
    - "ecu_engine.yaml"
    - "ecu_transmission.yaml"
    - "ecu_abs.yaml"
    
  logging:
    level: "INFO"
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: "logs/doip_server.log"
    
  vehicle:
    vin: "1HGBH41JXMN109186"
    eid: "123456789ABC"
    gid: "DEF012345678"
```

### ECU Configuration (`config/ecu_engine.yaml`)

```yaml
ecu:
  name: "Engine ECU"
  target_address: 0x1000
  functional_address: 0x1FFF
  tester_addresses: [0x0E00, 0x0E01]
  
  uds_services:
    service_files:
      - "ecu_engine_services.yaml"
      - "generic_uds_messages.yaml"
      
    common_services:
      - "read_vin"
      - "read_vehicle_type"
      - "diagnostic_session_control"
      
    specific_services:
      - "read_engine_data"
      - "engine_routine_control"
      
  routine_activation:
    supported_routines:
      0x0202:
        name: "Engine Test Routine"
        response_code: 0x10
        conditions: ["Engine off", "Ignition on"]
```

### UDS Services Configuration (`config/ecu_engine_services.yaml`)

```yaml
common_services:
  read_vin:
    request: "22F190"
    responses: ["62F1901020011223344556677889BBCC12121211"]
    description: "Read Vehicle Identification Number"
    supports_functional: true
    
  read_vehicle_type:
    request: "22F191"
    responses: ["62F1911020011223344556677889BBCC12121211"]
    description: "Read Vehicle Type"
    supports_functional: true
    
  diagnostic_session_control:
    request: "1003"
    responses: ["5003"]
    description: "Diagnostic Session Control - Extended"
    supports_functional: true

engine_services:
  read_engine_data:
    request: "22F186"
    responses: ["62F1861020011223344556677889BBCC12121211"]
    description: "Read Engine Data"
    supports_functional: false
    
  engine_routine_control:
    request: "31F186"
    responses: ["71F1861020011223344556677889BBCC12121211"]
    description: "Engine Routine Control"
    supports_functional: false
```

## Configuration Features

### Hierarchical Loading
- Gateway configuration loads ECU configurations
- ECU configurations load UDS service files
- Automatic path resolution for configuration files
- Fallback to default configurations if files are missing

### Address Management
- **Target Addresses**: ECU addresses for diagnostic messages
- **Source Addresses**: Allowed tester addresses per ECU
- **Functional Addresses**: Broadcast addresses for functional addressing
- **Address Validation**: Automatic validation of source/target addresses

### UDS Request Matching

The DoIP server supports two types of UDS request matching:

#### Exact Matching (Default)
UDS requests are matched exactly against the configured request string:
```yaml
engine_services:
  read_engine_rpm:
    request: "0x220C01"  # Exact match required
    responses: ["0x620C018000"]
    description: "Read engine RPM"
```

#### Regular Expression Matching
For flexible request patterns, use the `regex:` prefix to enable regular expression matching:
```yaml
engine_services:
  read_any_engine_data:
    request: "regex:^220C[0-9A-F]{2}$"  # Matches any 220CXX request
    responses: ["0x620C0080"]
    description: "Read any engine data identifier"
    
  diagnostic_session_any:
    request: "regex:^10[0-9A-F]{2}$"  # Matches any 10XX request
    responses: ["0x500300001212"]
    description: "Any diagnostic session control request"
    
  security_access_any:
    request: "regex:^27[0-9A-F]{2}$"  # Matches any 27XX request
    responses: ["0x6701"]
    description: "Any security access request"
```

**Regex Pattern Guidelines:**
- Use `^` to match the start of the string
- Use `$` to match the end of the string
- Use `[0-9A-F]` to match any hexadecimal character
- Use `{2}` to match exactly 2 characters
- Use `+` to match one or more characters
- Use `*` to match zero or more characters
- Use `|` for alternation (OR logic)

**Examples:**
- `^22F1[0-9A-F]{2}$` - Matches 22F1 followed by any 2 hex digits
- `^10[0-9A-F]+$` - Matches 10 followed by one or more hex digits
- `^19(02|03|0A)$` - Matches 1902, 1903, or 190A
- `^31[0-9A-F]{2}00[0-9A-F]{2}$` - Matches 31XX00XX pattern for routine control

**Important Notes:**
- Regex patterns are case-insensitive
- Both the original request and the request with `0x` prefix are tested
- Invalid regex patterns are logged as warnings and treated as non-matching
- Exact matching is tried first, then regex matching

### UDS Services
- **Service Definitions**: Configure UDS services and responses
- **Response Cycling**: Multiple responses per service for testing
- **Functional Support**: Services can support functional addressing
- **Service Files**: Organize services by ECU type

### Response Cycling
- **Multiple Responses**: Configure multiple responses per service
- **Cycling Logic**: Automatically cycle through responses
- **Per-ECU State**: Separate cycling state for each ECU-service combination
- **Reset Capability**: Reset cycling state for testing

## Configuration Validation

### Automatic Validation
The server automatically validates configurations on startup:
- Required fields present
- Valid data types and ranges
- Address validation
- Service configuration validation

### Manual Validation
```bash
# Validate all configurations
poetry run python -c "from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager; HierarchicalConfigManager().validate_configs()"

# Validate specific configuration
poetry run python -c "from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager; HierarchicalConfigManager('config/gateway1.yaml').validate_configs()"
```

## Configuration Examples

### Basic Gateway
```yaml
gateway:
  name: "Basic Gateway"
  network:
    host: "0.0.0.0"
    port: 13400
  protocol:
    version: 0x02
    inverse_version: 0xFD
  ecus: []
```

### Single ECU Setup
```yaml
gateway:
  name: "Single ECU Gateway"
  network:
    host: "127.0.0.1"
    port: 13400
  ecus:
    - "ecu_engine.yaml"
```

### Multi-ECU Setup
```yaml
gateway:
  name: "Multi-ECU Gateway"
  network:
    host: "0.0.0.0"
    port: 13400
  ecus:
    - "ecu_engine.yaml"
    - "ecu_transmission.yaml"
    - "ecu_abs.yaml"
```

## Troubleshooting

### Common Issues

1. **Configuration Not Found**
   - Check file paths in gateway configuration
   - Ensure configuration files exist
   - Verify file permissions

2. **Validation Errors**
   - Check YAML syntax
   - Verify required fields are present
   - Check data types and ranges

3. **Service Not Found**
   - Verify service files are loaded
   - Check service names in configuration
   - Ensure UDS service definitions are correct

### Debug Configuration
```yaml
logging:
  level: "DEBUG"
  console: true
  file: "logs/debug.log"
```

### Configuration Summary
```bash
poetry run python -c "from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager; print(HierarchicalConfigManager().get_config_summary())"
```

## Best Practices

1. **Use Descriptive Names**: Give meaningful names to ECUs and services
2. **Organize by ECU Type**: Separate service files by ECU type
3. **Validate Configurations**: Always validate before deployment
4. **Version Control**: Keep configuration files in version control
5. **Environment-Specific**: Use different configurations for different environments
6. **Documentation**: Document custom services and configurations
7. **Testing**: Test configurations with the validation tools
