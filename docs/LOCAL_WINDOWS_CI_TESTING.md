# Local Windows CI Testing Guide

This guide explains how to locally test your GitHub Actions CI workflow for Windows architecture before pushing to GitHub.

## 🎯 **Why Test Windows CI Locally?**

- **Faster feedback**: Catch Windows-specific issues before pushing
- **Cost savings**: Avoid using GitHub Actions minutes for failed builds
- **Better debugging**: Easier to debug issues in your local environment
- **Confidence**: Ensure your code works across all platforms

## 🚀 **Method 1: Using `act` (Recommended)**

### Installation

```bash
# On macOS
brew install act

# On Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# On Windows (with Chocolatey)
choco install act-cli
```

### Basic Usage

```bash
# Run the full CI workflow
act -W .github/workflows/ci.yml

# Run only the test job (includes Windows matrix)
act -j test -W .github/workflows/ci.yml

# Run with verbose output
act -v -W .github/workflows/ci.yml

# Run only Windows jobs
act -j test -P windows-latest=catthehacker/ubuntu:act-latest -W .github/workflows/ci.yml
```

### Advanced Usage

```bash
# Run with specific event
act push -W .github/workflows/ci.yml

# Run with environment variables
act -e .env -W .github/workflows/ci.yml

# Run with secrets
act --secret-file .secrets -W .github/workflows/ci.yml

# Dry run (see what would be executed)
act -n -W .github/workflows/ci.yml
```

## 🐍 **Method 2: Python Simulation Script**

Use the provided `simulate_windows_ci.py` script:

```bash
# Run the simulation
python3 simulate_windows_ci.py

# Or make it executable and run directly
./simulate_windows_ci.py
```

This script:
- ✅ Simulates the exact CI workflow steps
- ✅ Runs all tests with coverage
- ✅ Performs code quality checks
- ✅ Runs security scans
- ✅ Builds the package
- ✅ Provides detailed output

## 🐳 **Method 3: Docker Windows Container**

Use the provided `test_windows_local.sh` script:

```bash
# Make executable and run
chmod +x test_windows_local.sh
./test_windows_local.sh
```

This script:
- ✅ Creates a Windows-based Docker container
- ✅ Installs Poetry and dependencies
- ✅ Runs all tests exactly as in CI
- ✅ Provides Windows-specific environment testing

## 🖥️ **Method 4: GitHub Codespaces**

1. Go to your GitHub repository
2. Click "Code" → "Codespaces" → "Create codespace on Windows"
3. This gives you a full Windows environment
4. Run the same commands as in your CI workflow

## 🔧 **Method 5: Manual Windows Simulation**

Run the exact commands from your CI workflow:

```bash
# 1. Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# 2. Install dependencies
poetry install --no-interaction --no-root

# 3. Show environment info
python --version
poetry --version
pwd
poetry show

# 4. Run unit tests
poetry run pytest tests/test_doip_unit.py -v --cov=doip_server --cov-report=xml --cov-report=term-missing

# 5. Run integration tests
poetry run pytest tests/test_doip_integration.py -v --cov=doip_server --cov-report=xml --cov-report=term-missing

# 6. Run all tests
poetry run pytest tests/ -v --cov=doip_server --cov-report=xml --cov-report=term-missing

# 7. Validate configuration
poetry run validate_config

# 8. Code quality checks
poetry run flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
poetry run flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
poetry run black --check --diff src/ tests/

# 9. Security checks
poetry run bandit -r src/ -f json -o bandit-report.json
poetry run safety check --json --output safety-report.json

# 10. Build package
poetry build
```

## 📊 **Understanding Your CI Matrix**

Your CI workflow tests:
- **Operating Systems**: Ubuntu, macOS, Windows
- **Python Versions**: 3.11, 3.12
- **Total Combinations**: 6 different environments

The Windows-specific testing includes:
- Windows Server 2022 (windows-latest)
- Python 3.11 and 3.12
- All your tests, linting, security checks, and package building

## 🐛 **Common Windows-Specific Issues**

### Path Separators
- **Issue**: Using `/` instead of `\` in file paths
- **Solution**: Use `pathlib.Path` or `os.path.join()`

### Line Endings
- **Issue**: CRLF vs LF line endings
- **Solution**: Configure Git to handle line endings properly

### Case Sensitivity
- **Issue**: Case-sensitive file names on Linux vs case-insensitive on Windows
- **Solution**: Use consistent casing in imports and file names

### Environment Variables
- **Issue**: Different environment variable handling
- **Solution**: Use `os.environ.get()` with defaults

### Executable Permissions
- **Issue**: Scripts not executable on Windows
- **Solution**: Use proper shebang and ensure scripts are executable

## 🎯 **Best Practices**

### 1. Test Early and Often
```bash
# Run before every commit
./simulate_windows_ci.py

# Or use act for more accurate testing
act -j test -W .github/workflows/ci.yml
```

### 2. Use Cross-Platform Libraries
- Use `pathlib` instead of `os.path`
- Use `subprocess` with proper shell handling
- Use `tempfile` for temporary files

### 3. Handle Platform Differences
```python
import platform
import os

if platform.system() == "Windows":
    # Windows-specific code
    pass
else:
    # Unix-specific code
    pass
```

### 4. Test Dependencies
- Ensure all dependencies work on Windows
- Test with different Python versions
- Verify Poetry works correctly

## 🔍 **Debugging Tips**

### 1. Check act Logs
```bash
# Run with verbose output
act -v -W .github/workflows/ci.yml

# Check specific job logs
act -j test -v -W .github/workflows/ci.yml
```

### 2. Use Local Simulation
```bash
# Run the Python simulation for detailed output
python3 simulate_windows_ci.py
```

### 3. Test Individual Components
```bash
# Test just the unit tests
poetry run pytest tests/test_doip_unit.py -v

# Test just the integration tests
poetry run pytest tests/test_doip_integration.py -v

# Test just the configuration validation
poetry run validate_config
```

## 📈 **Performance Tips**

### 1. Use Caching
- act caches Docker images
- Poetry caches dependencies
- GitHub Actions caches are configured in your workflow

### 2. Parallel Testing
- Your CI runs tests in parallel across different OS/Python combinations
- Use `pytest-xdist` for parallel test execution locally

### 3. Selective Testing
```bash
# Test only changed files
poetry run pytest tests/ --lf

# Test only failed tests from last run
poetry run pytest tests/ --ff
```

## 🚨 **Troubleshooting**

### act Issues
```bash
# Update act to latest version
brew upgrade act

# Clear act cache
act --rm

# Check act version
act --version
```

### Docker Issues
```bash
# Check Docker is running
docker info

# Restart Docker if needed
# On macOS: Restart Docker Desktop
# On Linux: sudo systemctl restart docker
```

### Poetry Issues
```bash
# Update Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Clear Poetry cache
poetry cache clear --all pypi

# Reinstall dependencies
rm -rf .venv
poetry install --no-interaction --no-root
```

## 🎉 **Success Indicators**

Your Windows CI testing is successful when:
- ✅ All tests pass locally
- ✅ Code quality checks pass
- ✅ Security scans pass
- ✅ Package builds successfully
- ✅ Configuration validation passes
- ✅ act runs without errors

## 📚 **Additional Resources**

- [act Documentation](https://github.com/nektos/act)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)

---

**💡 Pro Tip**: Start with the Python simulation script (`simulate_windows_ci.py`) for quick feedback, then use `act` for more accurate testing before pushing to GitHub.
