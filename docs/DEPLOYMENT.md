# Deployment Guide

This guide covers deployment options and CI/CD setup for the DoIP server.

## Quick Deployment

### Local Development
```bash
# Install dependencies
poetry install

# Start server
poetry run python -m doip_server.main

# Run tests
poetry run pytest tests/ -v
```

### Production Deployment
```bash
# Install production dependencies
poetry install --only=main

# Start server with production config
poetry run python -m doip_server.main --gateway-config config/production.yaml
```

## Configuration Management

### Environment-Specific Configurations

#### Development
```yaml
# config/development.yaml
gateway:
  name: "DoIP Gateway - Development"
  network:
    host: "127.0.0.1"
    port: 13400
  logging:
    level: "DEBUG"
    console: true
```

#### Production
```yaml
# config/production.yaml
gateway:
  name: "DoIP Gateway - Production"
  network:
    host: "0.0.0.0"
    port: 13400
  logging:
    level: "INFO"
    file: "/var/log/doip_server.log"
    console: false
```

### Configuration Validation
```bash
# Validate configuration before deployment
poetry run python -c "from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager; HierarchicalConfigManager('config/production.yaml').validate_configs()"
```

## Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY src/ ./src/
COPY config/ ./config/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 13400

# Start server
CMD ["python", "-m", "doip_server.main"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  doip-server:
    build: .
    ports:
      - "13400:13400"
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    environment:
      - PYTHONPATH=/app/src
    restart: unless-stopped
```

### Build and Run
```bash
# Build Docker image
docker build -t doip-server .

# Run container
docker run -p 13400:13400 -v $(pwd)/config:/app/config doip-server

# Using Docker Compose
docker-compose up -d
```

## CI/CD Pipeline

### GitHub Actions

#### Main CI Workflow (`.github/workflows/ci.yml`)
```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: [3.9, 3.10, 3.11, 3.12]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
    
    - name: Install dependencies
      run: poetry install --with dev
    
    - name: Run tests
      run: poetry run pytest tests/ -v
    
    - name: Run linting
      run: poetry run flake8 src/ tests/
    
    - name: Run security checks
      run: |
        poetry run bandit -r src/
        poetry run safety check
```

#### Deployment Workflow
```yaml
name: Deploy

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install Poetry
      uses: snok/install-poetry@v1
    
    - name: Build package
      run: poetry build
    
    - name: Publish to PyPI
      run: poetry publish
      env:
        POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_TOKEN }}
```

### Local CI Testing
```bash
# Run local CI checks
make test-all

# Run specific checks
make lint
make format-check
make security
make build
```

## PyPI Package Publishing

### Package Configuration
The project is configured for PyPI publishing in `pyproject.toml`:

```toml
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "doip-server"
version = "1.0.0"
description = "DoIP (Diagnostics over IP) server implementation"
authors = ["Your Name <your.email@example.com>"]
license = "MIT"
readme = "README.md"
packages = [{include = "doip_server", from = "src"}]

[tool.poetry.dependencies]
python = "^3.8"
pyyaml = "^6.0"
scapy = "^2.6.1"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
pytest-cov = "^4.0"
flake8 = "^6.0"
black = "^23.0"
bandit = "^1.7"
safety = "^2.0"
```

### Publishing Process
```bash
# Build package
poetry build

# Publish to PyPI
poetry publish

# Publish to test PyPI
poetry publish --repository testpypi
```

### Installation from PyPI
```bash
# Install from PyPI
pip install doip-server

# Install specific version
pip install doip-server==1.0.0

# Install with dependencies
pip install doip-server[dev]
```

## System Service (systemd)

### Service File
```ini
# /etc/systemd/system/doip-server.service
[Unit]
Description=DoIP Server
After=network.target

[Service]
Type=simple
User=doip
Group=doip
WorkingDirectory=/opt/doip-server
ExecStart=/opt/doip-server/.venv/bin/python -m doip_server.main
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Service Management
```bash
# Create user
sudo useradd -r -s /bin/false doip

# Create directory
sudo mkdir -p /opt/doip-server
sudo chown doip:doip /opt/doip-server

# Copy application
sudo cp -r . /opt/doip-server/
sudo chown -R doip:doip /opt/doip-server

# Enable and start service
sudo systemctl enable doip-server
sudo systemctl start doip-server

# Check status
sudo systemctl status doip-server
```

## Monitoring and Logging

### Log Configuration
```yaml
# config/production.yaml
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/var/log/doip_server.log"
  console: false
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

### Log Rotation
```bash
# /etc/logrotate.d/doip-server
/var/log/doip_server.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 doip doip
    postrotate
        systemctl reload doip-server
    endscript
}
```

### Health Checks
```bash
# Check server status
curl -f http://localhost:13400/health || exit 1

# Check logs
tail -f /var/log/doip_server.log

# Check process
ps aux | grep doip_server
```

## Security Considerations

### Network Security
- **Firewall**: Configure firewall rules for port 13400
- **Access Control**: Use source address validation
- **TLS**: Consider TLS for production deployments
- **VPN**: Use VPN for remote access

### Application Security
- **User Permissions**: Run as non-root user
- **File Permissions**: Restrict configuration file access
- **Log Security**: Secure log files and rotation
- **Updates**: Keep dependencies updated

### Configuration Security
```yaml
# config/secure.yaml
gateway:
  security:
    enabled: true
    allowed_sources_strict: true
    require_auth: true
    max_connections_per_source: 5
```

## Performance Tuning

### Server Configuration
```yaml
# config/performance.yaml
gateway:
  network:
    max_connections: 50
    timeout: 120
    keepalive: true
  logging:
    level: "WARNING"  # Reduce logging overhead
```

### System Tuning
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize network settings
echo "net.core.somaxconn = 1024" >> /etc/sysctl.conf
sysctl -p
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   sudo netstat -tlnp | grep :13400
   sudo lsof -i :13400
   
   # Kill process
   sudo kill -9 <PID>
   ```

2. **Permission Denied**
   ```bash
   # Check file permissions
   ls -la config/
   chmod 644 config/*.yaml
   chown doip:doip config/
   ```

3. **Configuration Errors**
   ```bash
   # Validate configuration
   poetry run python -c "from src.doip_server.hierarchical_config_manager import HierarchicalConfigManager; HierarchicalConfigManager().validate_configs()"
   ```

### Debug Mode
```bash
# Enable debug logging
export DOIP_DEBUG=1
poetry run python -m doip_server.main

# Or modify configuration
logging:
  level: "DEBUG"
  console: true
```

### Log Analysis
```bash
# Check for errors
grep ERROR /var/log/doip_server.log

# Monitor real-time
tail -f /var/log/doip_server.log | grep -E "(ERROR|WARNING)"

# Analyze performance
grep "Processing" /var/log/doip_server.log | wc -l
```

## Backup and Recovery

### Configuration Backup
```bash
# Backup configuration
tar -czf doip-config-backup-$(date +%Y%m%d).tar.gz config/

# Restore configuration
tar -xzf doip-config-backup-20241201.tar.gz
```

### Database Backup
If using persistent storage for configuration:
```bash
# Backup configuration database
pg_dump doip_config > doip-config-backup.sql

# Restore configuration database
psql doip_config < doip-config-backup.sql
```

## Scaling

### Horizontal Scaling
- **Load Balancer**: Use load balancer for multiple instances
- **Configuration Sync**: Synchronize configuration across instances
- **Session Management**: Handle client sessions across instances

### Vertical Scaling
- **Resource Monitoring**: Monitor CPU, memory, and network usage
- **Performance Profiling**: Profile application performance
- **Optimization**: Optimize based on performance data

## Maintenance

### Regular Tasks
- **Log Rotation**: Ensure log files are rotated
- **Configuration Updates**: Update configuration as needed
- **Dependency Updates**: Keep dependencies updated
- **Security Patches**: Apply security patches promptly

### Monitoring
- **Health Checks**: Implement health check endpoints
- **Metrics Collection**: Collect performance metrics
- **Alerting**: Set up alerts for critical issues
- **Dashboard**: Create monitoring dashboard
