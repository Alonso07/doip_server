# Documentation Index

This is the main index for all DoIP server documentation.

## 📚 Core Documentation

### [README.md](README.md)
Main project overview with quick start guide, features, and basic usage.

### [CONFIGURATION.md](CONFIGURATION.md)
Complete configuration guide covering:
- Hierarchical configuration system
- Gateway configuration
- ECU configuration
- UDS services setup
- Response cycling configuration
- Troubleshooting and best practices

### [API.md](API.md)
Comprehensive API reference including:
- DoIPServer class methods
- HierarchicalConfigManager class methods
- Command-line interface
- Configuration API
- UDS services API
- Error handling and examples

### [TESTING.md](TESTING.md)
Testing guide and results covering:
- Test suite overview (185/186 tests passing)
- Running tests (unit, integration, configuration)
- Test structure and organization
- Test coverage and results
- CI/CD pipeline testing

### [DEPLOYMENT.md](DEPLOYMENT.md)
Deployment and CI/CD guide including:
- Local and production deployment
- Docker deployment
- GitHub Actions CI/CD
- PyPI package publishing
- System service setup
- Monitoring and security

## 🤝 Community & Project Management

### [CONTRIBUTING.md](CONTRIBUTING.md)
Comprehensive contributor guide including:
- Development setup and workflow
- Coding standards and testing requirements
- Pull request process
- Issue reporting guidelines
- Community guidelines

### [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
Community standards and guidelines:
- Expected behavior and community values
- Reporting and enforcement procedures
- Creating a welcoming environment

### [CHANGELOG.md](CHANGELOG.md)
Project changelog and release notes:
- Version history and changes
- Migration guides
- Security updates
- Feature announcements

### [SECURITY.md](SECURITY.md)
Security policy and procedures:
- Vulnerability reporting process
- Security best practices
- Supported versions
- Security considerations

## 🏗️ Architecture Overview

### Configuration Structure
```
config/
├── gateway1.yaml          # Gateway configuration
├── ecu_engine.yaml        # Engine ECU configuration
├── ecu_transmission.yaml  # Transmission ECU configuration
├── ecu_abs.yaml          # ABS ECU configuration
└── uds_services.yaml     # UDS service definitions
```

### Key Features
- **Hierarchical Configuration**: Multi-file YAML configuration system
- **Multi-ECU Support**: Individual ECU configurations
- **Functional Addressing**: Broadcast diagnostic requests
- **Response Cycling**: Configurable response variations for testing
- **UDS Services**: Unified Diagnostic Services implementation
- **Vehicle Identification**: UDP-based vehicle identification

## 🧪 Test Coverage

| Category | Tests | Status | Description |
|----------|-------|--------|-------------|
| **Unit Tests** | 17/17 | ✅ 100% | Fast component tests |
| **Hierarchical Config** | 21/21 | ✅ 100% | Configuration management |
| **Response Cycling** | 9/9 | ✅ 100% | Response cycling functionality |
| **Integration Tests** | 13/13 | ✅ 100% | Server-client communication |
| **Client Extended** | 25/25 | ✅ 100% | Extended client functionality |
| **Main Module** | 12/12 | ✅ 100% | Main module tests |
| **Validate Config** | 15/15 | ✅ 100% | Configuration validation |
| **Debug Client** | 30/30 | ✅ 100% | Debug client functionality |
| **Demo Tests** | 5/6 | ✅ 83% | Demo functionality |
| **TOTAL** | **185/186** | **✅ 99.5%** | **Comprehensive coverage** |

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

### Configuration
```bash
# Validate configuration
poetry run python -c "from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager; HierarchicalConfigManager().validate_configs()"
```

## 📖 Documentation Navigation

### For Users
1. Start with [README.md](README.md) for overview
2. Read [CONFIGURATION.md](CONFIGURATION.md) for setup
3. Check [API.md](API.md) for usage examples
4. See [TESTING.md](TESTING.md) for validation

### For Developers
1. Review [API.md](API.md) for implementation details
2. Check [TESTING.md](TESTING.md) for test coverage
3. See [DEPLOYMENT.md](DEPLOYMENT.md) for CI/CD setup
4. Use [CONFIGURATION.md](CONFIGURATION.md) for customization

### For DevOps
1. Start with [DEPLOYMENT.md](DEPLOYMENT.md) for deployment
2. Check [TESTING.md](TESTING.md) for CI/CD testing
3. Review [CONFIGURATION.md](CONFIGURATION.md) for production config
4. See [API.md](API.md) for monitoring integration

## 🔧 Configuration Examples

### Basic Gateway
```yaml
gateway:
  name: "Basic Gateway"
  network:
    host: "0.0.0.0"
    port: 13400
  protocol:
    version: 0x02
    inverse_version: 0xFD
  ecus: []
```

### Multi-ECU Setup
```yaml
gateway:
  name: "Multi-ECU Gateway"
  network:
    host: "0.0.0.0"
    port: 13400
  ecus:
    - "ecu_engine.yaml"
    - "ecu_transmission.yaml"
    - "ecu_abs.yaml"
```

## 🧪 Testing Examples

### Run All Tests
```bash
poetry run pytest tests/ -v
```

### Run Specific Tests
```bash
# Unit tests only
poetry run pytest tests/test_doip_unit.py -v

# Integration tests
poetry run pytest tests/test_doip_integration.py -v

# Configuration tests
poetry run pytest tests/test_hierarchical_configuration.py -v
```

## 🚀 Deployment Examples

### Docker
```bash
docker build -t doip-server .
docker run -p 13400:13400 doip-server
```

### System Service
```bash
sudo systemctl enable doip-server
sudo systemctl start doip-server
```

### PyPI Package
```bash
pip install doip-server
```

## 📞 Support

- **Documentation**: Check the relevant documentation files
- **Issues**: Create an issue on GitHub
- **Configuration**: Use `poetry run python -m doip_server.main --help`
- **Testing**: See [TESTING.md](TESTING.md) for troubleshooting

## 📄 License

MIT License - see [LICENSE](../LICENSE) for details.
