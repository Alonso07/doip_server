# DoIP Server Documentation

A comprehensive Python implementation of DoIP (Diagnostics over Internet Protocol) server and client with hierarchical configuration management.

## 🚀 Quick Start

### Installation
```bash
poetry install
```

### Start Server
```bash
poetry run python -m doip_server.main
```

### Run Tests
```bash
poetry run pytest tests/ -v
```

## 📚 Documentation Structure

### Core Documentation
- **[README.md](README.md)** - This overview
- **[CONFIGURATION.md](CONFIGURATION.md)** - Complete configuration guide
- **[API.md](API.md)** - API reference and examples
- **[TESTING.md](TESTING.md)** - Testing guide and results

### Features
- **DoIP Protocol**: Full DoIP protocol implementation (TCP/UDP)
- **Hierarchical Configuration**: YAML-based configuration management
- **Multi-ECU Support**: Support for multiple ECUs with individual configurations
- **Functional Addressing**: Broadcast diagnostic requests to multiple ECUs
- **Response Cycling**: Configurable response cycling for testing
- **UDS Services**: Unified Diagnostic Services implementation
- **Vehicle Identification**: UDP-based vehicle identification

### Test Coverage
- **185/186 tests passing (99.5%)**
- **Unit Tests**: 17/17 passing
- **Integration Tests**: 168/169 passing
- **Comprehensive coverage** of all functionality

## 🏗️ Architecture

### Configuration Structure
```
config/
├── gateway1.yaml          # Gateway configuration
├── ecu_engine.yaml        # Engine ECU configuration
├── ecu_transmission.yaml  # Transmission ECU configuration
├── ecu_abs.yaml          # ABS ECU configuration
└── uds_services.yaml     # UDS service definitions
```

### Key Components
- **DoIPServer**: Main server implementation
- **HierarchicalConfigManager**: Configuration management
- **UDS Services**: Diagnostic service implementations
- **Response Cycling**: Testing response variations

## 📖 Documentation Files

| File | Description |
|------|-------------|
| [README.md](README.md) | Main documentation overview |
| [CONFIGURATION.md](CONFIGURATION.md) | Configuration guide and examples |
| [API.md](API.md) | API reference and usage examples |
| [TESTING.md](TESTING.md) | Testing guide and results |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment and CI/CD guide |

## 🔧 Configuration

The server uses hierarchical YAML configuration files for:
- Gateway settings (network, protocol)
- ECU configurations (addresses, services)
- UDS service definitions
- Response cycling settings
- Logging configuration

See [CONFIGURATION.md](CONFIGURATION.md) for detailed configuration guide.

## 🧪 Testing

Comprehensive test suite with:
- Unit tests (fast, no server required)
- Integration tests (full server-client communication)
- Configuration validation tests
- Response cycling tests

See [TESTING.md](TESTING.md) for detailed testing information.

## 📦 Deployment

The project includes:
- GitHub Actions CI/CD
- PyPI package publishing
- Docker support
- Cross-platform compatibility

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `poetry run pytest tests/ -v`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.

## 🆘 Support

- **Documentation**: Check the relevant documentation files
- **Issues**: Create an issue on GitHub
- **Configuration**: Use `poetry run python -m doip_server.main --help`