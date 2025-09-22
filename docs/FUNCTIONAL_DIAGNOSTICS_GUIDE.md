# Functional Diagnostics Feature Guide

## Overview

The functional diagnostics feature allows DoIP clients to send diagnostic requests to a functional address, which is then broadcast to multiple ECUs that support the requested service. This enables efficient communication with multiple ECUs using a single request.

## Key Concepts

### Functional Address
- A special logical address (default: `0x1FFF`) that represents multiple ECUs
- When a request is sent to this address, the server broadcasts it to all ECUs that:
  1. Use the same functional address
  2. Support the requested UDS service with functional addressing
  3. Allow the source address

### Physical vs Functional Addressing
- **Physical Addressing**: Direct communication with a specific ECU using its unique logical address
- **Functional Addressing**: Broadcast communication to multiple ECUs using a shared functional address

## Configuration

### ECU Configuration
Each ECU configuration file (e.g., `ecu_engine.yaml`) now includes a functional address:

```yaml
ecu:
  name: "Engine_ECU"
  description: "Engine Control Unit"
  target_address: 0x1000
  functional_address: 0x1FFF  # Functional address for broadcast diagnostics
  tester_addresses:
    - 0x0E00  # Primary tester
    - 0x0E01  # Backup tester
    - 0x0E02  # Diagnostic tool
```

### UDS Services Configuration
Services that support functional addressing are marked in `uds_services.yaml`:

```yaml
common_services:
  Read_VIN:
    request: "0x22F190"
    responses:  
      - "0x22F1901020011223344556677889AABB"
      - "0x62F1901020011223344556677889BBCC"
    description: "Read Vehicle Identification Number"
    supports_functional: true  # Supports both physical and functional addressing
```

## Server Implementation

### Functional Address Detection
The server automatically detects when a request is sent to a functional address by checking if any ECUs are configured with that address.

### Broadcasting Logic
When a functional address request is received:
1. The server identifies all ECUs using that functional address
2. For each ECU, it checks if:
   - The source address is allowed
   - The ECU supports the UDS service with functional addressing
3. The server processes the request for each qualifying ECU
4. The server returns the first valid response (in a real implementation, you might want different behavior)

### Logging
The server logs detailed information about:
- Which ECUs are targeted by functional requests
- Which ECUs support the requested service
- Which ECUs actually respond
- The responses generated

## Client Implementation

### New Methods
The client now includes several new methods for functional addressing:

#### `send_functional_diagnostic_message(uds_payload, functional_address=0x1FFF, timeout=2.0)`
Sends a raw UDS payload to a functional address.

#### `send_functional_read_data_by_identifier(data_identifier, functional_address=0x1FFF)`
Sends a Read Data by Identifier request using functional addressing.

#### `send_functional_diagnostic_session_control(session_type=0x03, functional_address=0x1FFF)`
Sends a Diagnostic Session Control request using functional addressing.

#### `send_functional_tester_present(functional_address=0x1FFF)`
Sends a Tester Present request using functional addressing.

#### `run_functional_demo()`
Runs a demonstration of functional diagnostics functionality.

### Address Management
The client automatically manages target address switching:
- Temporarily changes the target address to the functional address
- Sends the request
- Restores the original target address
- Handles errors gracefully to ensure address restoration

## Usage Examples

### Basic Functional Request
```python
from doip_client.doip_client import DoIPClientWrapper

# Create client
client = DoIPClientWrapper(
    server_host="127.0.0.1",
    server_port=13400,
    logical_address=0x0E00,
    target_address=0x1000
)

# Connect
client.connect()

# Send functional request
response = client.send_functional_read_data_by_identifier(0xF190)  # Read VIN
print(f"Response: {response.hex()}")

# Disconnect
client.disconnect()
```

### Running Functional Demo
```python
# Run the functional diagnostics demo
client.run_functional_demo()
```

### Comparison with Physical Addressing
```python
# Physical addressing - Engine ECU only
response_physical = client.send_read_data_by_identifier(0xF190)

# Functional addressing - All ECUs that support it
response_functional = client.send_functional_read_data_by_identifier(0xF190)
```

## Testing

### Test Script
A test script is provided at `scripts/test/test_functional_diagnostics.py`:

```bash
python scripts/test/test_functional_diagnostics.py
```

### Unit Tests
Comprehensive unit tests are available in `tests/test_functional_diagnostics.py`:

```bash
python -m pytest tests/test_functional_diagnostics.py -v
```

## Configuration Files Updated

### ECU Configurations
- `config/ecu_engine.yaml` - Added functional address
- `config/ecu_transmission.yaml` - Added functional address  
- `config/ecu_abs.yaml` - Added functional address

### UDS Services
- `config/uds_services.yaml` - Added `supports_functional` flag to relevant services

## Services Supporting Functional Addressing

The following services are configured to support functional addressing:

### Common Services
- `Read_VIN` - Read Vehicle Identification Number
- `Read_Vehicle_Type` - Read Vehicle Type Information
- `Diagnostic_Session_Control` - Diagnostic Session Control
- `Tester_Present` - Tester Present

### ECU-Specific Services
- `Engine_Diagnostic_Codes` - Read engine diagnostic trouble codes
- `Transmission_Diagnostic_Codes` - Read transmission diagnostic trouble codes
- `ABS_Diagnostic_Codes` - Read ABS diagnostic trouble codes

## Server Logs

When using functional addressing, check the server logs for detailed information:

```
INFO - Functional address request to 0x1FFF, targeting 3 ECUs
INFO - ECU 0x1000 supports functional addressing for this service
INFO - ECU 0x1001 supports functional addressing for this service
INFO - ECU 0x1002 supports functional addressing for this service
INFO - Generated response from ECU 0x1000
INFO - Generated response from ECU 0x1001
INFO - Generated response from ECU 0x1002
INFO - Functional addressing: 3 ECUs responded, returning first response
```

## Benefits

1. **Efficiency**: Single request can reach multiple ECUs
2. **Simplicity**: Client doesn't need to know individual ECU addresses
3. **Flexibility**: Easy to add/remove ECUs from functional groups
4. **Compatibility**: Works alongside existing physical addressing
5. **Logging**: Comprehensive logging for debugging and monitoring

## Limitations

1. **Single Response**: Currently returns only the first response (could be enhanced)
2. **Service Support**: Only services marked with `supports_functional: true` work
3. **Address Validation**: Source address must be allowed for all target ECUs
4. **Error Handling**: If no ECUs support the service, request fails

## Future Enhancements

1. **Multiple Responses**: Return all responses instead of just the first
2. **Response Aggregation**: Combine responses from multiple ECUs
3. **Priority Handling**: Handle responses based on ECU priority
4. **Timeout Management**: Different timeouts for different ECUs
5. **Response Filtering**: Filter responses based on criteria

## Troubleshooting

### Common Issues

1. **No Response**: Check if any ECUs support the service with functional addressing
2. **Address Not Allowed**: Verify source address is allowed for target ECUs
3. **Service Not Supported**: Ensure service has `supports_functional: true`
4. **Configuration Error**: Check ECU functional address configuration

### Debug Steps

1. Check server logs for functional address detection
2. Verify ECU configurations have functional addresses
3. Confirm UDS services support functional addressing
4. Test with physical addressing first to isolate issues
5. Use the test script to validate functionality
