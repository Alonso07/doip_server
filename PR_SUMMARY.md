# Pull Request Summary: Response Delay Configuration (Issue #24)

## Overview

This PR implements the response delay configuration feature requested in issue #24, allowing users to configure delays in milliseconds for UDS service responses. This is useful for testing timing-sensitive applications, simulating realistic ECU response times, and testing timeout handling.

## Branch

- **Branch Name**: `feature/response-delay-configuration`
- **Base Branch**: `main`

## Changes Made

### 1. Core Implementation (`src/doip_server/doip_server.py`)

#### Added Imports
- `time` - For implementing delays
- `asyncio` - For future async support (prepared for future enhancement)

#### New Method: `_get_response_delay(data, response_index)`
- Parses DoIP messages to extract UDS service information
- Looks up delay configuration from service config
- Implements priority: response-level delay > service-level delay > no delay (0ms)
- Only applies delays to diagnostic messages (not routing, vehicle ID, power mode, etc.)
- Robust error handling for invalid data

#### Modified Method: `handle_client(client_socket)`
- Added delay application before sending each response
- Supports both single response and multiple response scenarios
- Logs delay information for debugging
- Uses `time.sleep(delay_ms / 1000.0)` for delay implementation

#### Modified Method: `process_uds_message(uds_payload, target_address)`
- Added support for dictionary-format responses: `{"response": "0x...", "delay_ms": 100}`
- Maintains backward compatibility with string-format responses
- Properly extracts response data from both formats

### 2. Configuration Files

#### `config/generic/generic_uds_messages.yaml`
- Added service-level delay example to `Read_VIN` service (100ms)
- Added response-level delay examples to `Diagnostic_Session_Control` service

#### `config/ecus/engine/ecu_engine_services_with_delay.yaml` (NEW)
- Comprehensive example configuration demonstrating all delay features
- Service-level delays
- Response-level delays
- Mixed configurations
- Progressive delays for testing

### 3. Tests (`tests/test_response_delay.py`) (NEW)

Comprehensive test suite with 8 test cases:

1. `test_get_response_delay_service_level` - Service-level delay configuration
2. `test_get_response_delay_response_level` - Response-level delay configuration
3. `test_get_response_delay_mixed_configuration` - Mixed configuration with priority
4. `test_get_response_delay_no_delay_configured` - Default behavior (no delay)
5. `test_get_response_delay_non_diagnostic_message` - Non-diagnostic message handling
6. `test_get_response_delay_invalid_data` - Error handling
7. `test_get_response_delay_service_not_found` - Service not found handling
8. `test_response_delay_timing` - Performance verification

**All tests passing: 8/8 ✓**

### 4. Documentation (`docs/DELAY_CONFIGURATION.md`) (NEW)

Complete documentation including:
- Feature overview and use cases
- Configuration schema and syntax
- Priority rules
- Multiple examples with explanations
- Implementation details
- Performance considerations
- Migration guide for existing configurations
- Future enhancement suggestions

## Configuration Schema

### Service-Level Delay
```yaml
specific_services:
  My_Service:
    request: "0x220C01"
    responses:
      - "0x620C018000"
    delay_ms: 150  # All responses delayed by 150ms
```

### Response-Level Delay
```yaml
specific_services:
  My_Service:
    request: "0x220C05"
    responses:
      - response: "0x620C0580"
        delay_ms: 0
      - response: "0x620C0590"
        delay_ms: 150
      - response: "0x620C0570"
        delay_ms: 300
```

### Mixed Configuration
```yaml
specific_services:
  My_Service:
    request: "0x31010001"
    delay_ms: 75  # Default for string responses
    responses:
      - response: "0x71010001"
        delay_ms: 100  # Override
      - response: "0x71010002"
        delay_ms: 0  # Override
      - "0x71010003"  # Uses service-level delay (75ms)
```

## Delay Priority Rules

1. **Response-level delay** (highest priority) - Explicitly configured in response dictionary
2. **Service-level delay** - Configured at service level
3. **No delay** (default) - 0ms if nothing configured

## Backward Compatibility

✓ **Fully backward compatible**
- Existing configurations work without any changes
- String-format responses continue to work
- No delays applied unless explicitly configured
- No breaking changes to existing functionality

## Testing

### Unit Tests
```bash
python -m pytest tests/test_response_delay.py -v
```
Result: 8/8 tests passing

### Integration Testing Recommendations
1. Test with real DoIP client
2. Verify delays are applied correctly
3. Test timeout scenarios
4. Verify functional addressing with delays
5. Test response cycling with varying delays

## Files Changed

- `src/doip_server/doip_server.py` - Core delay implementation
- `config/generic/generic_uds_messages.yaml` - Example configurations
- `config/ecus/engine/ecu_engine_services_with_delay.yaml` - Comprehensive examples (NEW)
- `tests/test_response_delay.py` - Test suite (NEW)
- `docs/DELAY_CONFIGURATION.md` - Documentation (NEW)

## How to Push and Create PR

Since network access is restricted in the current environment, please run these commands manually:

```bash
# Navigate to the repository
cd /Users/alonsoramirez/Documents/vscode/python_projects/python/doip_server

# Push the branch to GitHub
git push -u origin feature/response-delay-configuration

# Create PR using GitHub CLI (if installed)
gh pr create --title "Add response delay configuration feature (issue #24)" \
  --body-file PR_SUMMARY.md \
  --base main \
  --head feature/response-delay-configuration

# Or create PR via GitHub web interface:
# 1. Go to: https://github.com/Alonso07/doip_server/pulls
# 2. Click "New Pull Request"
# 3. Select base: main, compare: feature/response-delay-configuration
# 4. Title: "Add response delay configuration feature (issue #24)"
# 5. Copy content from this file into the PR description
# 6. Add labels: enhancement, feature
# 7. Link to issue #24
# 8. Submit PR
```

## PR Checklist

- [x] Feature implemented and working
- [x] Unit tests added and passing (8/8)
- [x] Documentation created
- [x] Example configurations provided
- [x] Backward compatibility maintained
- [x] Code follows project style guidelines
- [x] Commits are clean and well-described
- [ ] PR created on GitHub
- [ ] PR linked to issue #24
- [ ] Reviewers assigned (if applicable)

## Notes

- The implementation uses blocking `time.sleep()` for simplicity
- Future enhancement could use async/await for non-blocking delays
- Delays only apply to diagnostic messages (UDS services)
- All existing tests continue to pass
