# DoIP Server

A Python implementation of DoIP (Diagnostics over Internet Protocol) server and client with comprehensive YAML configuration management.

## 🚀 Quick Start

```bash
# Install dependencies
poetry install

# Run with hierarchical configuration
poetry run python src/doip_server/main.py --gateway-config config/gateway1.yaml

# Run with legacy configuration
poetry run python src/doip_server/main.py --legacy-config config/example_config.yaml
```

## 📚 Documentation

All documentation has been moved to the `docs/` directory for better organization:

- **[📖 Documentation Index](docs/INDEX.md)** - Complete documentation index
- **[🚀 Getting Started](docs/README.md)** - Detailed project overview and setup
- **[⚙️ Configuration Guide](docs/HIERARCHICAL_CONFIGURATION_GUIDE.md)** - Hierarchical configuration system
- **[🧪 Test Results](docs/COMPREHENSIVE_TEST_RESULTS.md)** - Complete test results and analysis

## ✨ Key Features

- **Hierarchical Configuration**: Multi-file configuration system with dynamic ECU loading
- **Response Cycling**: Automatic cycling through multiple responses per UDS service
- **Per-ECU Services**: ECU-specific UDS service definitions
- **Backward Compatibility**: Support for legacy single-file configuration
- **Comprehensive Testing**: 91% test pass rate with full core functionality

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
- **Overall**: 73/80 tests passing (91% success rate)

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
