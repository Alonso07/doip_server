# UDP DoIP Vehicle Identification

This document describes the UDP DoIP Vehicle Identification functionality that has been added to the DoIP server and client.

## Overview

The UDP DoIP Vehicle Identification feature allows clients to discover DoIP servers on the network by broadcasting vehicle identification requests over UDP. This is particularly useful for:

- Network discovery of DoIP servers
- Vehicle identification without establishing TCP connections
- Testing and validation of DoIP implementations

## Architecture

### UDP DoIP Client (`src/doip_client/udp_doip_client.py`)

The UDP DoIP client broadcasts vehicle identification requests to the network and receives responses from DoIP servers.

**Key Features:**
- Broadcasts requests to UDP port 13400
- Parses vehicle identification responses
- Configurable timeout and retry logic
- Comprehensive logging and error handling

**Usage:**
```bash
# Run with default settings
python scripts/utilities/run_udp_client.py

# Run with custom parameters
python scripts/utilities/run_udp_client.py --port 13400 --timeout 5.0 --requests 3 --verbose
```

### DoIP Server UDP Support

The DoIP server has been enhanced to support both TCP and UDP connections simultaneously:

**Key Features:**
- Listens on UDP port 13400 for vehicle identification requests
- Responds with vehicle information from configuration
- Maintains existing TCP functionality
- Non-blocking UDP message handling

## Protocol Implementation

### Vehicle Identification Request (Payload Type 0x0001)

**Message Structure:**
```
+------------------+------------------+------------------+------------------+
| Protocol Version | Inverse Protocol | Payload Type     | Payload Length   |
| (1 byte)         | Version (1 byte) | (2 bytes)        | (4 bytes)        |
+------------------+------------------+------------------+------------------+
| Payload (0 bytes)                                                         |
+--------------------------------------------------------------------------+
```

**Example:**
```
02 FD 00 01 00 00 00 00
```

### Vehicle Identification Response (Payload Type 0x0004)

**Message Structure:**
```
+------------------+------------------+------------------+------------------+
| Protocol Version | Inverse Protocol | Payload Type     | Payload Length   |
| (1 byte)         | Version (1 byte) | (2 bytes)        | (4 bytes)        |
+------------------+------------------+------------------+------------------+
| VIN (17 bytes)                                                           |
+--------------------------------------------------------------------------+
| Logical Address (2 bytes)                                                |
+--------------------------------------------------------------------------+
| EID (6 bytes)                                                            |
+--------------------------------------------------------------------------+
| GID (6 bytes)                                                            |
+--------------------------------------------------------------------------+
| Further Action Required (1 byte)                                         |
+--------------------------------------------------------------------------+
| VIN/GID Sync Status (1 byte)                                             |
+--------------------------------------------------------------------------+
```

**Example:**
```
02 FD 00 04 00 00 00 21 31 48 47 42 48 34 31 4A 58 4D 4E 31 30 39 31 38 36 00 00 10 00 12 34 56 78 9A BC DE F0 12 34 56 78 00 00
```

## Configuration

### Gateway Configuration

The gateway configuration now includes vehicle information:

```yaml
gateway:
  name: "Gateway1"
  description: "Primary DoIP Gateway"
  logical_address: 0x1000  # Gateway logical address
  
  # Vehicle Information
  vehicle:
    vin: "1HGBH41JXMN109186"  # Vehicle Identification Number
    eid: "123456789ABC"  # Entity ID (6 bytes hex)
    gid: "DEF012345678"  # Group ID (6 bytes hex)
```

### Configuration Methods

The hierarchical configuration manager now supports:

- `get_vehicle_info()`: Returns vehicle information (VIN, EID, GID)
- `get_gateway_info()`: Returns gateway information including logical address

## Testing

### Manual Testing

1. **Start the DoIP server:**
   ```bash
   python -m doip_server.main --gateway-config config/gateway1.yaml
   ```

2. **Run the UDP client:**
   ```bash
   python run_udp_client.py --verbose
   ```

### Automated Testing

Run the comprehensive test script:

```bash
python test_udp_doip.py
```

This will:
1. Start the DoIP server in the background
2. Run the UDP client with multiple requests
3. Display the results

## Example Output

### Server Output
```
DoIP server listening on 0.0.0.0:13400 (TCP and UDP)
Received UDP message from ('192.168.1.100', 54321): 02fd000100000000
UDP Protocol Version: 0x02
UDP Inverse Protocol Version: 0xFD
UDP Payload Type: 0x0001
UDP Payload Length: 0
Processing vehicle identification request
Vehicle identification response: VIN=1HGBH41JXMN109186, Address=0x1000
Sent vehicle identification response to ('192.168.1.100', 54321)
```

### Client Output
```
UDP DoIP client started on port 54321
Sending vehicle identification request to 255.255.255.255:13400
Request: 02fd000100000000
Waiting for vehicle identification response...
Received response from ('192.168.1.1', 13400)
Response: 02fd000400000021314847424834314a584d4e31303931383600001000123456789abcdef0123456780000
Vehicle identification response parsed successfully
VIN: 1HGBH41JXMN109186
Logical Address: 0x1000
EID: 123456789ABC
GID: DEF012345678
Further Action Required: 0
VIN/GID Sync Status: 0
```

## Error Handling

The implementation includes comprehensive error handling for:

- Invalid protocol versions
- Malformed messages
- Network timeouts
- Configuration errors
- Socket errors

## Security Considerations

- UDP broadcasts are sent to the local network only
- No authentication is required for vehicle identification requests
- Sensitive information (VIN, EID, GID) should be configured appropriately
- Consider network segmentation for production deployments

## Future Enhancements

Potential improvements for future versions:

1. **Security**: Add authentication for vehicle identification requests
2. **Filtering**: Allow filtering of requests based on source addresses
3. **Multiple Vehicles**: Support for multiple vehicle configurations
4. **Discovery**: Enhanced network discovery features
5. **Monitoring**: Statistics and monitoring of UDP requests

## Troubleshooting

### Common Issues

1. **No responses received:**
   - Check if server is running
   - Verify network connectivity
   - Check firewall settings
   - Ensure correct port (13400)

2. **Invalid response format:**
   - Check server configuration
   - Verify VIN format (17 characters)
   - Check EID/GID format (12 hex characters each)

3. **Timeout errors:**
   - Increase timeout value
   - Check network latency
   - Verify server is responding

### Debug Mode

Enable verbose logging for detailed debugging:

```bash
python run_udp_client.py --verbose
```

This will show detailed protocol information and message parsing.
