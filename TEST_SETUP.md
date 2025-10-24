# DoIP Server Test Setup for doip_tester_yaml

This document describes how to configure and run the doip_server for end-to-end testing with the doip_tester_yaml project.

## Overview

The doip_server has been configured to work with the doip_tester_yaml project by:

1. **Matching ECU logical addresses** - All ECUs now use the logical addresses expected by the tester
2. **Configuring proper tester addresses** - All ECUs accept connections from tester address 0x0E80
3. **Setting up comprehensive ECU coverage** - 8 ECUs are configured to match the tester's expectations
4. **Creating test-specific configuration** - A dedicated test gateway configuration is provided

## Configured ECUs

The following ECUs are configured and ready for testing:

| ECU Name | Logical Address | Description |
|----------|----------------|-------------|
| Engine_ECM | 0x01 | Engine Control Module |
| Transmission_TCU | 0x02 | Transmission Control Unit |
| ABS | 0x03 | Anti-lock Braking System |
| ESP | 0x04 | Electronic Stability Program |
| Steering_EPS | 0x05 | Electric Power Steering |
| BCM | 0x06 | Body Control Module |
| Gateway | 0x07 | Gateway ECU |
| HVAC | 0x08 | Heating, Ventilation, Air Conditioning |

## Quick Start

### 1. Start the DoIP Server

```bash
# Option 1: Use the startup script
./start_test_server.sh

# Option 2: Use poetry directly
poetry run python -m doip_server.main --gateway-config config/test_gateway.yaml

# Option 3: Use the default configuration
poetry run python -m doip_server.main
```

### 2. Run Tests with doip_tester_yaml

In your doip_tester_yaml project directory:

```bash
# Run basic communication tests
poetry run python -m doip_tester.main --config config/test_cases.yaml

# Run DoIP-specific tests
poetry run python -m doip_tester.main --config config/doip_test_cases.yaml

# Run UDP tests
poetry run python -m doip_tester.main --config config/udp_doip_test_cases.yaml
```

## Configuration Files

### Main Configuration Files

- **`config/test_gateway.yaml`** - Test-specific gateway configuration
- **`config/gateway1.yaml`** - Default gateway configuration (updated with new ECUs)

### ECU Configuration Files

- **`config/ecus/engine/ecu_engine.yaml`** - Engine ECU configuration
- **`config/ecus/transmission/ecu_transmission.yaml`** - Transmission ECU configuration
- **`config/ecus/abs/ecu_abs.yaml`** - ABS ECU configuration
- **`config/ecus/esp/ecu_esp.yaml`** - ESP ECU configuration
- **`config/ecus/steering/ecu_steering.yaml`** - Steering ECU configuration
- **`config/ecus/bcm/ecu_bcm.yaml`** - BCM ECU configuration
- **`config/ecus/gateway/ecu_gateway.yaml`** - Gateway ECU configuration
- **`config/ecus/hvac/ecu_hvac.yaml`** - HVAC ECU configuration

### Service Configuration Files

Each ECU has its own service configuration file (e.g., `ecu_engine_services.yaml`) that defines the UDS services available for that ECU.

## Network Configuration

- **Server Host**: 0.0.0.0 (listens on all interfaces)
- **Server Port**: 13400 (standard DoIP port)
- **Tester Address**: 0x0E80 (matches doip_tester_yaml expectations)
- **Functional Address**: 0x0000 (for broadcast communication)

## Supported UDS Services

All ECUs support the following common UDS services:

- **Diagnostic Session Control** (0x10) - Physical and functional addressing
- **Tester Present** (0x3E) - Physical and functional addressing
- **Read Data By Identifier** (0x22) - Physical and functional addressing
- **Security Access** (0x27) - Physical addressing only
- **Read DTC Information** (0x19) - Physical and functional addressing
- **Clear DTC Information** (0x14) - Physical addressing only
- **Routine Control** (0x31) - Physical addressing only
- **Communication Control** (0x28) - Physical addressing only

Each ECU also has specific services defined in their respective service configuration files.

## Testing Scenarios

The configuration supports the following test scenarios from doip_tester_yaml:

### Basic Communication Tests
- UDP DoIP communication
- Vehicle identification requests
- Power mode requests
- Entity status requests

### ECU-Specific Tests
- Physical addressing to individual ECUs
- Functional addressing (broadcast) to multiple ECUs
- Session control and security access
- Data reading and DTC management

### Advanced Tests
- Multi-ECU communication
- Security access procedures
- Routine control operations
- Communication control

## Validation

To validate the configuration:

```bash
poetry run python test_config.py
```

This script checks:
- Gateway configuration validity
- ECU configuration validity
- Address mapping correctness
- Service configuration completeness

## Troubleshooting

### Common Issues

1. **Port already in use**: Make sure no other DoIP server is running on port 13400
2. **Configuration errors**: Run the validation script to check for issues
3. **ECU not responding**: Check that the ECU logical address matches the test expectations

### Logs

Server logs are written to:
- **Console**: Real-time output
- **File**: `doip_server_test.log` (for test configuration)

### Debug Mode

To enable debug logging, modify the logging level in `config/test_gateway.yaml`:

```yaml
logging:
  level: "DEBUG"  # Change from "INFO" to "DEBUG"
```

## Integration with doip_tester_yaml

The doip_server is now fully compatible with doip_tester_yaml:

1. **ECU addresses match** - All logical addresses correspond to the tester's expectations
2. **Tester address supported** - All ECUs accept connections from 0x0E80
3. **Services available** - All required UDS services are implemented
4. **Network configuration** - Server listens on the correct port and interface

## Next Steps

1. Start the doip_server using one of the methods above
2. Run your doip_tester_yaml tests
3. Monitor the server logs for any issues
4. Adjust configurations as needed for your specific test requirements

For more information about the doip_tester_yaml project, refer to its documentation and configuration files.
