# Contributing to DoIP Server

Thank you for your interest in contributing to the DoIP Server project! This document provides guidelines and information for contributors.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (3.11+ recommended)
- Poetry (for dependency management)
- Git

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/doip_server.git
   cd doip_server
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Run tests to verify setup**
   ```bash
   poetry run pytest tests/ -v
   ```

4. **Start the server for testing**
   ```bash
   poetry run python -m doip_server.main --gateway-config config/gateway1.yaml
   ```

## 📋 Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Your Changes
- Follow the coding standards (see below)
- Add tests for new functionality
- Update documentation if needed

### 3. Test Your Changes
```bash
# Run all tests
poetry run pytest tests/ -v

# Run specific test categories
poetry run pytest tests/test_doip_unit.py -v
poetry run pytest tests/test_doip_integration.py -v

# Run with coverage
poetry run pytest tests/ --cov=doip_server --cov-report=html
```

### 4. Code Quality Checks
```bash
# Format code
poetry run black src/ tests/

# Lint code
poetry run flake8 src/ tests/

# Security checks
poetry run bandit -r src/
poetry run safety check
```

### 5. Commit and Push
```bash
git add .
git commit -m "feat: add new feature description"
git push origin feature/your-feature-name
```

### 6. Create Pull Request
- Use the provided PR template
- Reference any related issues
- Ensure all CI checks pass

## 🎨 Coding Standards

### Python Style
- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 127)
- Use type hints where appropriate
- Write docstrings for all public functions/classes

### Code Organization
- Keep functions focused and small
- Use meaningful variable and function names
- Add comments for complex logic
- Follow the existing project structure

### Testing Requirements
- **New features must include tests**
- Aim for high test coverage
- Use descriptive test names
- Include both unit and integration tests
- Test error conditions and edge cases

## 🧪 Testing Guidelines

### Test Structure
```
tests/
├── test_doip_unit.py              # Unit tests
├── test_doip_integration.py       # Integration tests
├── test_hierarchical_configuration.py  # Config tests
├── test_functional_diagnostics.py # Feature tests
└── conftest.py                    # Test fixtures
```

### Writing Tests
```python
def test_new_feature():
    """Test that new feature works correctly."""
    # Arrange
    setup_test_data()
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected_value
```

### Test Categories
- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: Test component interactions
- **Configuration Tests**: Test YAML configuration handling
- **Functional Tests**: Test end-to-end scenarios

## 📝 Documentation

### Code Documentation
- Use Google-style docstrings
- Include parameter and return type information
- Add usage examples for complex functions

### User Documentation
- Update README.md for user-facing changes
- Update docs/ directory for API changes
- Add configuration examples for new features

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Clear description** of the issue
2. **Steps to reproduce** the problem
3. **Expected behavior** vs actual behavior
4. **Environment details** (OS, Python version, etc.)
5. **Configuration files** (with sensitive data removed)
6. **Logs** and error messages
7. **Screenshots** if applicable

Use the bug report template in `.github/ISSUE_TEMPLATE/bug_report.md`.

## ✨ Feature Requests

When requesting features, please include:

1. **Problem description** - What issue does this solve?
2. **Proposed solution** - How should it work?
3. **Alternatives considered** - Other approaches you've thought about
4. **Additional context** - Any other relevant information

Use the feature request template in `.github/ISSUE_TEMPLATE/feature_request.md`.

## 🔧 Configuration Changes

### Adding New Configuration Options
1. Update the relevant YAML schema
2. Add validation in `HierarchicalConfigManager`
3. Update configuration documentation
4. Add tests for the new option
5. Update example configurations

### Configuration File Structure
```
config/
├── gateway1.yaml              # Gateway configuration
├── ecus/
│   ├── engine/
│   ├── transmission/
│   └── abs/
└── generic/
    └── generic_uds_messages.yaml
```

## 🚀 Release Process

### Version Bumping
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml`
- Update CHANGELOG.md
- Tag the release

### Release Types
- **Patch**: Bug fixes, documentation updates
- **Minor**: New features, backward compatible
- **Major**: Breaking changes

## 🤝 Community Guidelines

### Communication
- Be respectful and constructive
- Help others learn and grow
- Ask questions when you need help
- Share knowledge and best practices

### Code Review
- Review code, not people
- Provide constructive feedback
- Suggest improvements, not just problems
- Be patient with new contributors

## 📚 Resources

### Documentation
- [Project Documentation](docs/INDEX.md)
- [API Reference](docs/API.md)
- [Configuration Guide](docs/CONFIGURATION.md)
- [Testing Guide](docs/TESTING.md)

### Development Tools
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)

### DoIP Protocol
- [ISO 13400-2:2019](https://www.iso.org/standard/72439.html)
- [UDS Protocol](https://www.iso.org/standard/46430.html)

## 🆘 Getting Help

- **Documentation**: Check the docs/ directory first
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact maintainers for sensitive issues

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to DoIP Server! 🎉
