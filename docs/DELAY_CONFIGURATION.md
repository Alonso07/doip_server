# Response Delay Configuration

This document describes the response delay configuration feature introduced in issue #24, which allows configuring delays for UDS service responses.

## Overview

The response delay feature enables you to add configurable delays (in milliseconds) to UDS service responses. This is useful for:

- **Testing timing-sensitive diagnostic applications**
- **Simulating realistic ECU response times**
- **Testing timeout handling in diagnostic clients**
- **Simulating slow ECU responses under load**

## Configuration Schema

Delays can be configured at two levels:

### 1. Service-Level Delay

A service-level delay applies to all responses for a specific UDS service unless overridden by a response-level delay.

```yaml
specific_services:
  Engine_RPM_Read:
    request: "0x220C01"
    responses:
      - "0x620C018000"  # 8000 RPM
      - "0x620C017500"  # 7500 RPM
    description: "Read engine RPM"
    supports_functional: false
    delay_ms: 150  # All responses delayed by 150ms
```

### 2. Response-Level Delay

Response-level delays allow you to configure different delays for each response in a service. This is useful when implementing response cycling with varying delays.

```yaml
specific_services:
  Engine_Temperature_Read:
    request: "0x220C05"
    responses:
      - response: "0x620C0580"  # 80°C
        delay_ms: 0  # No delay
      - response: "0x620C0590"  # 90°C
        delay_ms: 150  # 150ms delay
      - response: "0x620C0570"  # 70°C
        delay_ms: 300  # 300ms delay
    description: "Read engine temperature"
    supports_functional: false
```

### 3. Mixed Configuration

You can combine service-level and response-level delays. Response-level delays always take precedence:

```yaml
specific_services:
  Engine_Start_Stop:
    request: "0x31010001"
    responses:
      - response: "0x71010001"  # Engine started
        delay_ms: 100  # Override: 100ms delay
      - response: "0x71010002"  # Engine stopped
        delay_ms: 0  # Override: no delay
      - "0x71010003"  # Engine error - uses service-level delay
    description: "Engine start/stop control"
    supports_functional: false
    delay_ms: 75  # Default delay for responses without explicit delay
```

## Delay Priority

The delay configuration follows this priority order:

1. **Response-level delay** (highest priority) - Specified in the `delay_ms` field of a response dictionary
2. **Service-level delay** - Specified in the `delay_ms` field of the service configuration
3. **No delay** (default) - 0ms delay if neither is configured

## Configuration Examples

### Example 1: Fixed Service-Level Delay

All responses delayed by the same amount:

```yaml
specific_services:
  Read_VIN:
    request: "0x22F190"
    responses:  
      - "0x62F1901020011223344556677889AABB12121212"
      - "0x62F1901020011223344556677889BBCC12121211"
    description: "Read Vehicle Identification Number"
    supports_functional: true
    delay_ms: 100  # All responses delayed by 100ms
```

### Example 2: Progressive Response Delays

Each response has an increasing delay for testing timeout scenarios:

```yaml
specific_services:
  Engine_Diagnostic_Codes:
    request: "0x1902"
    responses:
      - response: "0x5902"  # No DTCs
        delay_ms: 50
      - response: "0x5902P0100"  # P0100
        delay_ms: 150
      - response: "0x5902P0200"  # P0200
        delay_ms: 300
      - response: "0x5902P0300"  # P0300
        delay_ms: 500
    description: "Read engine diagnostic trouble codes"
    supports_functional: true
```

### Example 3: No Delay Configuration

Services without delay configuration default to immediate response (0ms):

```yaml
specific_services:
  Tester_Present:
    request: "0x3E00"
    responses:
      - "0x7E00"  # Positive response
    description: "Tester Present"
    supports_functional: true
    # No delay_ms specified - immediate response
```

## Implementation Details

### Delay Application

- Delays are applied **before** sending each response to the client
- The delay is implemented using `time.sleep()` for simplicity
- Delays only apply to **diagnostic messages** (UDS services), not to:
  - Routing activation requests
  - Vehicle identification requests
  - Power mode requests
  - Entity status requests

### Response Cycling with Delays

When using response cycling (multiple responses for a service), each response can have its own delay:

```yaml
specific_services:
  Variable_Response_Time:
    request: "0x220C01"
    responses:
      - response: "0x620C0100"  # Fast response
        delay_ms: 10
      - response: "0x620C0150"  # Medium response
        delay_ms: 100
      - response: "0x620C0180"  # Slow response
        delay_ms: 500
    description: "Service with variable response times"
```

### Functional Addressing with Delays

For functional addressing (broadcast to multiple ECUs), delays are applied to each ECU's response individually:

```yaml
specific_services:
  Diagnostic_Session_Control:
    request: "0x1003"
    responses:
      - response: "0x500300001212"
        delay_ms: 50
    description: "Diagnostic Session Control"
    supports_functional: true  # Each ECU response delayed by 50ms
```

## Testing

The delay functionality includes comprehensive unit tests in `tests/test_response_delay.py`:

- Service-level delay configuration
- Response-level delay configuration
- Mixed configuration with priority handling
- No delay configuration (default behavior)
- Invalid data handling
- Non-diagnostic message handling

Run the tests with:

```bash
python -m pytest tests/test_response_delay.py -v
```

## Performance Considerations

- **Blocking Delays**: The current implementation uses blocking `time.sleep()` calls
- **Multiple Clients**: Delays are applied per-connection, so multiple clients are affected independently
- **Large Delays**: Be cautious with large delays (>1000ms) as they can affect server responsiveness
- **Testing**: Use appropriate delays for your testing scenario (typically 10-500ms)

## Future Enhancements

Potential improvements for future versions:

1. **Asynchronous Delays**: Non-blocking delay implementation using async/await
2. **Random Delays**: Support for random delay ranges (e.g., `delay_ms: [100, 500]`)
3. **Conditional Delays**: Apply delays based on request parameters
4. **Delay Statistics**: Track and log delay statistics for monitoring

## Migration Guide

### Backward Compatibility

The delay feature is fully backward compatible:

- Existing configurations without `delay_ms` continue to work unchanged
- String-format responses (legacy format) default to service-level delay or 0ms
- No changes required to existing YAML files

### Migrating to Delay Configuration

To add delays to existing services:

**Before:**
```yaml
specific_services:
  My_Service:
    request: "0x220C01"
    responses:
      - "0x620C018000"
    description: "My service"
```

**After (service-level delay):**
```yaml
specific_services:
  My_Service:
    request: "0x220C01"
    responses:
      - "0x620C018000"
    description: "My service"
    delay_ms: 100  # Add this line
```

**After (response-level delay):**
```yaml
specific_services:
  My_Service:
    request: "0x220C01"
    responses:
      - response: "0x620C018000"  # Change to dictionary format
        delay_ms: 100  # Add delay
    description: "My service"
```

## See Also

- [Configuration Guide](CONFIGURATION.md)
- [UDS Services Configuration](../config/generic/generic_uds_messages.yaml)
- [Example with Delays](../config/ecus/engine/ecu_engine_services_with_delay.yaml)
