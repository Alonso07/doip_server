# Hierarchical DoIP Configuration Guide

This guide explains the new hierarchical configuration system for the DoIP server, which divides configuration into three separate files for better organization and dynamic ECU management.

## Overview

The hierarchical configuration system consists of three main components:

1. **Gateway Configuration** (`gateway1.yaml`) - TCP/IP network settings and gateway-level configuration
2. **ECU Configurations** (`ecu_*.yaml`) - Individual ECU settings including addresses and service references
3. **UDS Services Configuration** (`uds_services.yaml`) - All UDS service definitions

## Configuration Files

### 1. Gateway Configuration (`config/gateway1.yaml`)

Contains the TCP/IP network configuration and gateway-level settings:

```yaml
gateway:
  name: "Gateway1"
  description: "Primary DoIP Gateway"
  
  # TCP/IP Network Configuration
  network:
    host: "0.0.0.0"
    port: 13400
    max_connections: 10
    timeout: 60
    
  # Protocol Configuration
  protocol:
    version: 0x02
    inverse_version: 0xFD
    
  # ECU References - List of ECU configuration files
  ecus:
    - "ecu_engine.yaml"
    - "ecu_transmission.yaml" 
    - "ecu_abs.yaml"
```

### 2. ECU Configuration (`config/ecu_*.yaml`)

Each ECU has its own configuration file containing:

```yaml
ecu:
  name: "Engine_ECU"
  description: "Engine Control Unit"
  target_address: 0x1000
  tester_addresses:
    - 0x0E00  # Primary tester
    - 0x0E01  # Backup tester
  
  # UDS Services Reference
  uds_services:
    # Common services shared across all ECUs
    common_services:
      - "Read_VIN"
      - "Read_Vehicle_Type"
      - "Routine_calibration_start"
    
    # ECU-specific services (only available for this ECU)
    specific_services:
      - "Engine_RPM_Read"
      - "Engine_Temperature_Read"
      - "Fuel_Level_Read"
```

### 3. UDS Services Configuration (`config/uds_services.yaml`)

Contains all UDS service definitions organized by category:

```yaml
# Common UDS Services (available to all ECUs)
common_services:
  Read_VIN:
    request: "0x22F190"
    responses:  
      - "0x62F1901020011223344556677889AABB"
    description: "Read Vehicle Identification Number"

# Engine-specific UDS Services
engine_services:
  Engine_RPM_Read:
    request: "0x220C01"
    responses:
      - "0x620C018000"  # 8000 RPM
    description: "Read engine RPM"
```

## Key Features

### 1. Dynamic ECU Loading

ECUs are loaded at runtime based on the gateway configuration. This allows for:
- Easy addition/removal of ECUs without code changes
- Different ECU configurations for different deployments
- Runtime ECU discovery and loading

### 2. Hierarchical Service Management

UDS services are organized hierarchically:
- **Common Services**: Available to all ECUs (e.g., Read VIN, Read Vehicle Type)
- **ECU-Specific Services**: Only available to specific ECUs (e.g., Engine RPM, Transmission Gear)

### 3. Address Validation

The system validates both source and target addresses:
- Source addresses are validated against ECU-specific tester lists
- Target addresses are validated against configured ECU addresses
- Each ECU can have different allowed tester addresses

### 4. Service Lookup

UDS service lookup is performed per ECU:
- Services are looked up based on the target ECU address
- Only services available to that specific ECU are considered
- Common services are available to all ECUs
- Specific services are only available to their designated ECUs

## Usage Examples

### Starting the Server

```bash
# Using the new hierarchical configuration
python -m doip_server.main --gateway-config config/gateway1.yaml

# Override host and port
python -m doip_server.main --host 192.168.1.100 --port 13400

# Using legacy configuration (backward compatibility)
python -m doip_server.main --legacy-config config/doip_config.yaml
```

### Programmatic Usage

```python
from doip_server.hierarchical_config_manager import HierarchicalConfigManager

# Load configuration
config_manager = HierarchicalConfigManager("config/gateway1.yaml")

# Get all ECU addresses
ecu_addresses = config_manager.get_all_ecu_addresses()

# Get ECU-specific UDS services
for target_addr in ecu_addresses:
    services = config_manager.get_ecu_uds_services(target_addr)
    print(f"ECU 0x{target_addr:04X} has {len(services)} services")

# Look up a specific service for an ECU
service = config_manager.get_uds_service_by_request("0x22F190", 0x1000)
if service:
    print(f"Found service: {service['name']}")
```

## Migration from Legacy Configuration

The new hierarchical system is backward compatible. To migrate:

1. **Keep existing configuration**: Your current `doip_config.yaml` will continue to work
2. **Create new configurations**: Use the new file structure for new deployments
3. **Gradual migration**: Migrate ECUs one by one to the new system

### Migration Steps

1. Create a gateway configuration file (`gateway1.yaml`)
2. Create individual ECU configuration files (`ecu_*.yaml`)
3. Create a UDS services configuration file (`uds_services.yaml`)
4. Update your startup scripts to use the new configuration

## Benefits

### 1. Better Organization
- Clear separation of concerns
- Easier to maintain and understand
- Modular configuration structure

### 2. Dynamic ECU Management
- Add/remove ECUs without code changes
- Runtime configuration loading
- Flexible ECU deployment

### 3. Service Isolation
- ECU-specific services are isolated
- Common services are shared efficiently
- Clear service ownership

### 4. Scalability
- Easy to add new ECUs
- Easy to add new services
- Configuration can grow with the system

## Configuration Validation

The system validates configurations at startup:

- Gateway configuration structure
- ECU configuration completeness
- UDS service definitions
- Address consistency
- Service references

## Error Handling

The system provides comprehensive error handling:

- Missing configuration files
- Invalid configuration syntax
- Missing service references
- Address validation errors
- Service lookup failures

## Demo and Testing

Use the demo script to test the configuration:

```bash
python src/doip_server/demo_hierarchical.py
```

This will demonstrate:
- Configuration loading
- ECU information display
- Service lookup functionality
- Address validation
- Runtime capabilities

## Troubleshooting

### Common Issues

1. **ECU not found**: Check that the ECU configuration file exists and is referenced in the gateway config
2. **Service not available**: Verify the service is defined in `uds_services.yaml` and referenced in the ECU config
3. **Address validation failed**: Check that source addresses are in the ECU's tester list
4. **Configuration loading failed**: Verify YAML syntax and file paths

### Debug Mode

Enable debug logging to see detailed configuration loading information:

```yaml
logging:
  level: "DEBUG"
```

## Future Enhancements

Planned enhancements include:

1. **Hot Reloading**: Reload ECU configurations without restarting the server
2. **Service Versioning**: Support for different service versions per ECU
3. **Configuration Templates**: Reusable configuration templates
4. **Dynamic Service Discovery**: Automatic service discovery from ECU responses
5. **Configuration Validation Tools**: Standalone tools for validating configurations
