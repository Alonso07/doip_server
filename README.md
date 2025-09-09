# DoIP Server

A Python implementation of DoIP (Diagnostics over Internet Protocol) server and client with comprehensive YAML configuration management.

## 🚀 Quick Start

```bash
# Install dependencies
poetry install

# Run with hierarchical configuration
poetry run python src/doip_server/main.py --gateway-config config/gateway1.yaml

# Test UDP Vehicle Identification
python run_udp_client.py --verbose

# Test Functional Diagnostics (NEW!)
python test_functional_diagnostics.py
```

## 📚 Documentation

All documentation has been moved to the `docs/` directory for better organization:

- **[📖 Documentation Index](docs/INDEX.md)** - Complete documentation index
- **[🚀 Getting Started](docs/README.md)** - Detailed project overview and setup
- **[⚙️ Configuration Guide](docs/HIERARCHICAL_CONFIGURATION_GUIDE.md)** - Hierarchical configuration system
- **[🔧 Functional Diagnostics](docs/FUNCTIONAL_DIAGNOSTICS_GUIDE.md)** - Functional addressing and broadcast diagnostics
- **[🧪 Test Results](docs/COMPREHENSIVE_TEST_RESULTS.md)** - Complete test results and analysis

## ✨ Key Features

- **Hierarchical Configuration**: Multi-file configuration system with dynamic ECU loading
- **Response Cycling**: Automatic cycling through multiple responses per UDS service
- **Per-ECU Services**: ECU-specific UDS service definitions
- **Functional Diagnostics**: Broadcast requests to multiple ECUs using functional addressing (NEW!)
- **UDP Vehicle Identification**: Network discovery via UDP broadcasts
- **Comprehensive Testing**: 99.5% test pass rate with full core functionality

## 🏗️ Architecture

```
config/
├── gateway1.yaml          # Gateway network configuration
├── ecu_engine.yaml        # Engine ECU configuration
├── ecu_transmission.yaml  # Transmission ECU configuration
├── ecu_abs.yaml          # ABS ECU configuration
└── uds_services.yaml     # Common UDS services
```

## 📊 Test Status

- **Unit Tests**: 17/17 ✅ (100%)
- **Hierarchical Config Tests**: 21/21 ✅ (100%)
- **Response Cycling Tests**: 9/9 ✅ (100%)
- **Legacy Integration Tests**: 13/13 ✅ (100%)
- **Client Extended Tests**: 25/25 ✅ (100%)
- **Main Module Tests**: 12/12 ✅ (100%)
- **Validate Config Tests**: 15/15 ✅ (100%)
- **Debug Client Tests**: 30/30 ✅ (100%)
- **Demo Tests**: 5/6 ✅ (83% - 1 skipped)
- **Overall**: 185/186 tests passing (99.5% success rate)

## 🔧 Development

```bash
# Run tests
poetry run pytest tests/ -v

# Run specific test categories
poetry run pytest tests/test_doip_unit.py -v
poetry run pytest tests/test_hierarchical_configuration.py -v
poetry run pytest tests/test_response_cycling.py -v
```

## 📖 Documentation

For detailed documentation, see the [docs/](docs/) directory or start with the [Documentation Index](docs/INDEX.md).

---

*For complete documentation and implementation details, see the [docs/](docs/) directory.*
