# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
poetry install

# Run server with hierarchical config (standard)
poetry run python src/doip_server/main.py --gateway-config config/gateway1.yaml
# or via Makefile
make run-hierarchical

# Run all tests
poetry run pytest tests/ -v

# Run a single test file
poetry run pytest tests/test_doip_unit.py -v

# Run a single test by name
poetry run pytest tests/test_doip_unit.py -v -k "test_name"

# Lint (errors only, then style warnings)
poetry run flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
poetry run flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format check / format
poetry run black --check --diff src/ tests/
poetry run black src/ tests/

# Security scans
poetry run bandit -r src/ -f json -o reports/bandit-report.json
poetry run safety check --json > reports/safety-report.json

# Validate configuration
poetry run python -c "from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager; HierarchicalConfigManager('config/gateway1.yaml')"

# Build package
poetry build

# Full CI simulation
make ci-local
```

## Architecture

### Package layout

```
src/
  doip_server/     # Server package (published to PyPI as doip-server)
    main.py                    # CLI entry point (--host, --port, --gateway-config)
    doip_server.py             # DoIPServer class — core TCP+UDP server
    net_utils.py               # IPv4/IPv6 bind helpers (dual-stack via IPV6_V6ONLY=0)
    hierarchical_config_manager.py  # YAML config loader/validator
  doip_client/     # Client package (bundled for testing/demo)
    doip_client.py             # DoIPClientWrapper around the doipclient library
    udp_doip_client.py         # Raw UDP client for vehicle identification
    debug_client.py            # Debug/diagnostic CLI client
config/
  gateway1.yaml              # Root config (network, ECU file references)
  gateway1_ipv6.yaml         # Example dual-stack config (host: "::")
  ecus/<ecu>/ecu_*.yaml      # Per-ECU config (addresses, service references)
  generic/generic_uds_messages.yaml  # Common UDS service definitions
tests/                         # pytest suite; conftest.py sets sys.path and fixtures
```

### Request flow

`DoIPServer` runs a single-threaded event loop polling both TCP (`server_socket`) and UDP (`udp_socket`) with short timeouts (100 ms each).

- **UDP**: Vehicle identification (0x0001), entity status (0x4001), power mode (0x4003) — all handled in `handle_udp_message`, responded to via `sendto`.
- **TCP**: Routing activation (0x0005) → `handle_routing_activation`; Diagnostic messages (0x8001) → `handle_diagnostic_message` → `process_uds_message`.

Every TCP diagnostic message returns a **list** of frames: `[ACK_frame, UDS_response_frame, ...]`. Per-response delays (in ms) are applied in `handle_client` before each send.

### IPv6 / dual-stack networking

- `gateway.network.host`: `0.0.0.0` (IPv4 default), `::` (dual-stack when `dual_stack` is true or omitted), or `::1` (IPv6 loopback).
- `DoIPServer.start()` uses `net_utils.create_listening_socket()` for TCP and UDP.
- Web dashboard DoIP client proxy (`web/api/doip_client.py`) only allows loopback targets; use `localhost`, `127.0.0.1`, or `::1`.

### Configuration hierarchy

`HierarchicalConfigManager` loads configs in this order:
1. **`gateway1.yaml`** — network/protocol settings, vehicle info, list of ECU config file paths under `gateway.ecus`.
2. **Per-ECU YAML** (`ecus/<name>/ecu_<name>.yaml`) — ECU `target_address`, `functional_address` (default `0x1FFF`), `tester_addresses`, and references to UDS service files.
3. **UDS service files** — keyed by service name; each entry has `request` (hex string), `responses` (list of hex strings or `{response, delay_ms}` dicts), optional `no_response: true`, `supports_functional: true`.

`DoIPServer` asks the manager for everything via its API (`get_uds_service_by_request`, `is_source_address_allowed`, `get_ecus_by_functional_address`, etc.) rather than reading YAML directly.

### Functional vs. physical addressing

- **Physical** (`target_address` = specific ECU address): routed to one ECU.
- **Functional** (`target_address` = `functional_address`, e.g. `0x1FFF`): `handle_functional_diagnostic_message` iterates all ECUs sharing that functional address and responds from each ECU that has `supports_functional: true` on the matching service.

### Response cycling

`DoIPServer.response_cycle_state` is a `dict` keyed by `(ecu_address, service_name)`. Each UDS hit advances the index, cycling through the `responses` list. Power-mode cycling uses key `("power_mode", "power_mode_status")`.

### Test markers

`pyproject.toml` defines `unit`, `integration`, and `slow` markers. The default `addopts` adds `-v --tb=short --strict-markers --disable-warnings`. `conftest.py` inserts `src/` into `sys.path` at session scope.
