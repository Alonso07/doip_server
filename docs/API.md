# API Reference

This document provides a comprehensive API reference for the DoIP server implementation.

## DoIPServer Class

### Constructor
```python
DoIPServer(host=None, port=None, gateway_config_path=None)
```

**Parameters:**
- `host` (str, optional): Server host address. If None, uses configuration value.
- `port` (int, optional): Server port number. If None, uses configuration value.
- `gateway_config_path` (str, optional): Path to gateway configuration file.

**Example:**
```python
from doip_server import DoIPServer

# Use default configuration
server = DoIPServer()

# Override specific settings
server = DoIPServer(host="127.0.0.1", port=13400)

# Use custom configuration
server = DoIPServer(gateway_config_path="config/custom_gateway.yaml")
```

### Methods

#### `start()`
Start the DoIP server with both TCP and UDP support.

```python
server.start()
```

**Features:**
- Creates and binds TCP server socket for diagnostic sessions
- Creates and binds UDP server socket for vehicle identification
- Handles both TCP and UDP messages concurrently
- Runs until interrupted (KeyboardInterrupt) or stopped programmatically

#### `stop()`
Stop the DoIP server and close all sockets.

```python
server.stop()
```

#### `get_binding_info() -> tuple[str, int]`
Get current server binding information.

**Returns:**
- `tuple[str, int]`: (host, port) for current server binding

#### `get_server_info() -> dict`
Get comprehensive server information.

**Returns:**
- `dict`: Server configuration and status information

**Example:**
```python
info = server.get_server_info()
print(f"Server: {info['host']}:{info['port']}")
print(f"Running: {info['running']}")
```

#### `reset_response_cycling(ecu_address=None, service_name=None)`
Reset response cycling state.

**Parameters:**
- `ecu_address` (int, optional): ECU address to reset (None for all ECUs)
- `service_name` (str, optional): Service name to reset (None for all services)

**Example:**
```python
# Reset all cycling states
server.reset_response_cycling()

# Reset specific ECU
server.reset_response_cycling(ecu_address=0x1000)

# Reset specific service
server.reset_response_cycling(service_name="read_vin")
```

## HierarchicalConfigManager Class

### Constructor
```python
HierarchicalConfigManager(gateway_config_path=None)
```

**Parameters:**
- `gateway_config_path` (str, optional): Path to gateway configuration file.

### Methods

#### `get_gateway_config() -> Dict[str, Any]`
Get the complete gateway configuration.

**Returns:**
- `Dict[str, Any]`: Gateway configuration dictionary

#### `get_network_config() -> Dict[str, Any]`
Get network configuration settings.

**Returns:**
- `Dict[str, Any]`: Network configuration containing host, port, max_connections, timeout

#### `get_server_binding_info() -> tuple[str, int]`
Get server host and port for binding.

**Returns:**
- `tuple[str, int]`: (host, port) for server binding

#### `get_all_ecu_addresses() -> List[int]`
Get all configured ECU target addresses.

**Returns:**
- `List[int]`: List of all configured ECU target addresses

#### `get_ecu_config(target_address: int) -> Optional[Dict[str, Any]]`
Get ECU configuration by target address.

**Parameters:**
- `target_address` (int): The target address of the ECU to retrieve

**Returns:**
- `Optional[Dict[str, Any]]`: ECU configuration dictionary if found, None otherwise

#### `get_ecu_tester_addresses(target_address: int) -> List[int]`
Get allowed tester addresses for a specific ECU.

**Parameters:**
- `target_address` (int): The target address of the ECU

**Returns:**
- `List[int]`: List of allowed tester addresses for this ECU

#### `is_source_address_allowed(source_addr: int, target_addr: int = None) -> bool`
Check if source address is allowed for a specific ECU or any ECU.

**Parameters:**
- `source_addr` (int): Source address to check
- `target_addr` (int, optional): Target ECU address (None for any ECU)

**Returns:**
- `bool`: True if source address is allowed

#### `is_target_address_valid(target_addr: int) -> bool`
Check if target address is valid (has ECU configuration).

**Parameters:**
- `target_addr` (int): Target address to validate

**Returns:**
- `bool`: True if target address is valid

#### `get_uds_service_by_request(request: str, target_address: int = None) -> Optional[Dict[str, Any]]`
Get UDS service configuration by request string.

**Parameters:**
- `request` (str): UDS request string (hex format)
- `target_address` (int, optional): Target ECU address

**Returns:**
- `Optional[Dict[str, Any]]`: Service configuration if found, None otherwise

#### `validate_configs() -> bool`
Validate all configuration files.

**Returns:**
- `bool`: True if all configurations are valid

#### `reload_configs()`
Reload all configuration files.

#### `get_config_summary() -> str`
Get a summary of the current configuration.

**Returns:**
- `str`: Configuration summary string

## Command Line Interface

### Main Entry Point
```bash
python -m doip_server.main [options]
```

**Options:**
- `--host HOST`: Server host address (overrides config)
- `--port PORT`: Server port (overrides config)
- `--gateway-config PATH`: Path to gateway configuration file

**Examples:**
```bash
# Use default configuration
python -m doip_server.main

# Override host and port
python -m doip_server.main --host 127.0.0.1 --port 13400

# Use custom configuration
python -m doip_server.main --gateway-config config/custom.yaml
```

## Configuration API

### Loading Configurations
```python
from doip_server import HierarchicalConfigManager

# Load default configuration
config = HierarchicalConfigManager()

# Load specific configuration
config = HierarchicalConfigManager("config/gateway1.yaml")
```

### Accessing Configuration Data
```python
# Get gateway configuration
gateway = config.get_gateway_config()

# Get network settings
network = config.get_network_config()
host, port = config.get_server_binding_info()

# Get ECU information
ecu_addresses = config.get_all_ecu_addresses()
ecu_config = config.get_ecu_config(0x1000)

# Validate configuration
if config.validate_configs():
    print("Configuration is valid")
```

## UDS Services API

### Service Configuration
```python
# Get service configuration
service = config.get_uds_service_by_request("22F190", 0x1000)
if service:
    print(f"Service: {service['name']}")
    print(f"Responses: {service['responses']}")
```

### Response Cycling
```python
# Reset response cycling
server.reset_response_cycling()

# Reset specific ECU
server.reset_response_cycling(ecu_address=0x1000)

# Get cycling state
state = server.get_response_cycling_state()
print(f"Cycling state: {state}")
```

## Error Handling

### Configuration Errors
```python
try:
    config = HierarchicalConfigManager("invalid_config.yaml")
except FileNotFoundError:
    print("Configuration file not found")
except yaml.YAMLError as e:
    print(f"Invalid YAML: {e}")
```

### Server Errors
```python
try:
    server = DoIPServer(host="invalid_host", port=99999)
except ValueError as e:
    print(f"Invalid configuration: {e}")
```

## Logging

### Configuration
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Get logger
logger = logging.getLogger(__name__)
```

### Server Logging
The server automatically configures logging based on the configuration file:
```yaml
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/doip_server.log"
  console: true
```

## Examples

### Basic Server Setup
```python
from doip_server import DoIPServer

# Create and start server
server = DoIPServer()
server.start()
```

### Custom Configuration
```python
from doip_server import DoIPServer

# Create server with custom settings
server = DoIPServer(
    host="192.168.1.100",
    port=13400,
    gateway_config_path="config/production.yaml"
)
server.start()
```

### Configuration Management
```python
from doip_server import HierarchicalConfigManager

# Load configuration
config = HierarchicalConfigManager("config/gateway1.yaml")

# Validate configuration
if config.validate_configs():
    print("Configuration is valid")
    
    # Get server binding info
    host, port = config.get_server_binding_info()
    print(f"Server will bind to {host}:{port}")
    
    # Get ECU information
    ecus = config.get_all_ecu_addresses()
    print(f"Configured ECUs: {ecus}")
```

### Service Testing
```python
# Test UDS service
service = config.get_uds_service_by_request("22F190", 0x1000)
if service:
    print(f"Service found: {service['name']}")
    print(f"Supports functional: {service['supports_functional']}")
else:
    print("Service not found")
```
