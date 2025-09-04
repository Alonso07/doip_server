# PyPI Publishing Guide for DoIP Server

This guide walks you through publishing the DoIP Server package to PyPI (Python Package Index).

## 📋 Prerequisites

### 1. PyPI Accounts
- **PyPI Account**: [https://pypi.org/account/register/](https://pypi.org/account/register/)
- **TestPyPI Account**: [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/) (recommended for testing)

### 2. Required Tools
```bash
# Install publishing tools (already done)
poetry add --group dev build twine
```

## 🚀 Quick Start

### Option 1: Use the Automated Script
```bash
./publish_to_pypi.sh
```

### Option 2: Manual Publishing

## 📦 Step-by-Step Publishing Process

### Step 1: Prepare Your Package

1. **Update Version** (if needed):
   ```bash
   # Edit pyproject.toml and update version
   version = "0.1.0"  # or your new version
   ```

2. **Run Tests**:
   ```bash
   poetry run pytest tests/ -v
   ```

3. **Clean Previous Builds**:
   ```bash
   rm -rf dist/ build/ *.egg-info/
   ```

### Step 2: Build the Package

```bash
# Build source distribution and wheel
poetry run python -m build
```

This creates:
- `dist/doip_server-0.1.0.tar.gz` (source distribution)
- `dist/doip_server-0.1.0-py3-none-any.whl` (wheel)

### Step 3: Check the Package

```bash
# Validate package
poetry run twine check dist/*
```

### Step 4: Publish to TestPyPI (Recommended First)

```bash
# Upload to TestPyPI
poetry run twine upload --repository testpypi dist/*
```

**Test the package**:
```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ doip-server

# Test the package
python -c "import doip_server; print('Package works!')"
```

### Step 5: Publish to PyPI (Production)

```bash
# Upload to PyPI
poetry run twine upload dist/*
```

**Install from PyPI**:
```bash
pip install doip-server
```

## 🔧 Configuration Details

### Package Configuration (`pyproject.toml`)

The package is configured with:
- **Name**: `doip-server` (PyPI-friendly name)
- **Version**: `0.1.0`
- **Description**: Clear description for PyPI
- **Keywords**: `["doip", "diagnostics", "automotive", "uds", "iso13400", "server", "client"]`
- **Classifiers**: Proper PyPI classifiers for discoverability
- **Dependencies**: `PyYAML>=6.0,<7.0` and `doipclient>=1.1.7,<2.0.0`

### Included Files

- **Source Code**: `src/doip_server/` directory
- **Configuration**: `config/` directory with YAML files
- **Tests**: `tests/` directory
- **Documentation**: `README.md`, `LICENSE`, etc.

## 🎯 Package Features on PyPI

Once published, users can:

### Install the Package
```bash
pip install doip-server
```

### Use the Server
```python
from doip_server import DoIPServer

# Start server with default config
server = DoIPServer()
server.start()
```

### Use the Client
```python
from doip_server import DoIPClient

# Connect to DoIP server
client = DoIPClient('127.0.0.1', 13400)
```

### Use Command Line Tools
```bash
# Start DoIP server
doip-server

# Run DoIP client
doip-client

# Validate configuration
validate-config

# View message formats
demo
```

## 📊 Package Statistics

- **Package Size**: ~25KB (wheel)
- **Dependencies**: 2 (PyYAML, doipclient)
- **Python Versions**: 3.10, 3.11, 3.12, 3.13
- **Platforms**: OS Independent
- **License**: MIT

## 🔄 Version Management

### Semantic Versioning
- **Major** (1.0.0): Breaking changes
- **Minor** (0.2.0): New features, backward compatible
- **Patch** (0.1.1): Bug fixes, backward compatible

### Updating Version
1. Edit `pyproject.toml`:
   ```toml
   version = "0.2.0"  # New version
   ```
2. Update `CHANGELOG.md` (if you have one)
3. Commit changes:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git tag v0.2.0
   git push origin main --tags
   ```
4. Publish new version:
   ```bash
   ./publish_to_pypi.sh
   ```

## 🛡️ Security Considerations

### API Tokens
- **TestPyPI Token**: Store in `~/.pypirc` or environment variables
- **PyPI Token**: Store securely, never commit to version control

### Example `~/.pypirc`:
```ini
[distutils]
index-servers = pypi testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-testpypi-token-here
```

## 🐛 Troubleshooting

### Common Issues

1. **Package Already Exists**:
   ```
   HTTPError: 400 Client Error: File already exists.
   ```
   **Solution**: Update version number in `pyproject.toml`

2. **Authentication Failed**:
   ```
   HTTPError: 403 Client Error: Invalid or non-existent authentication information.
   ```
   **Solution**: Check your API token in `~/.pypirc`

3. **Package Check Failed**:
   ```
   ERROR: The package contains invalid metadata.
   ```
   **Solution**: Run `poetry run twine check dist/*` to see specific errors

4. **Build Failed**:
   ```
   ERROR: Failed to build package
   ```
   **Solution**: Check `pyproject.toml` syntax and dependencies

### Debug Commands

```bash
# Check package metadata
poetry run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb')))"

# Validate package
poetry run twine check dist/* --verbose

# Test package locally
pip install dist/doip_server-0.1.0-py3-none-any.whl
```

## 📈 Post-Publishing

### 1. Verify Installation
```bash
pip install doip-server
python -c "import doip_server; print(doip_server.__version__)"
```

### 2. Test Functionality
```bash
# Run the server
doip-server

# In another terminal, test client
doip-client
```

### 3. Monitor Downloads
- Check PyPI statistics: [https://pypi.org/project/doip-server/](https://pypi.org/project/doip-server/)
- Monitor package health and downloads

### 4. Update Documentation
- Update README.md with PyPI installation instructions
- Add PyPI badge to README.md
- Update any external documentation

## 🎉 Success!

Once published, your package will be available at:
- **PyPI**: https://pypi.org/project/doip-server/
- **Installation**: `pip install doip-server`

### Package Badges for README.md

Add these badges to your README.md:

```markdown
[![PyPI version](https://badge.fury.io/py/doip-server.svg)](https://badge.fury.io/py/doip-server)
[![Downloads](https://pepy.tech/badge/doip-server)](https://pepy.tech/project/doip-server)
[![Python versions](https://img.shields.io/pypi/pyversions/doip-server.svg)](https://pypi.org/project/doip-server/)
```

## 🔄 Continuous Publishing

Consider setting up GitHub Actions for automated publishing:

1. **On Tag Push**: Automatically publish to PyPI when you push a git tag
2. **On Release**: Publish when you create a GitHub release
3. **Version Bump**: Automatically bump version numbers

This ensures consistent and reliable publishing without manual steps.

---

**Happy Publishing! 🚀**

Your DoIP Server package is now ready for the Python community!
