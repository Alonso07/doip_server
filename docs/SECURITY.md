# Security Policy

## Supported Versions

We provide security updates for the following versions of DoIP Server:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 1. **DO NOT** create a public GitHub issue

Security vulnerabilities should be reported privately to avoid exposing users to potential risks.

### 2. Report via Email

Please send an email to: **alonsoram07@gmail.com**

Include the following information:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes or mitigations
- Your contact information (optional)

### 3. What to Expect

- **Acknowledgment**: We will acknowledge receipt of your report within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 5 business days
- **Regular Updates**: We will keep you informed of our progress
- **Resolution**: We will work to resolve the issue as quickly as possible

### 4. Disclosure Timeline

- **Immediate**: Critical vulnerabilities (remote code execution, data breach)
- **7 days**: High severity vulnerabilities
- **30 days**: Medium severity vulnerabilities
- **90 days**: Low severity vulnerabilities

## Security Best Practices

### For Users

1. **Keep Updated**: Always use the latest version of DoIP Server
2. **Network Security**: Run DoIP Server in a secure network environment
3. **Access Control**: Limit access to DoIP Server ports (default: 13400)
4. **Configuration**: Review and secure your configuration files
5. **Monitoring**: Monitor logs for suspicious activity

### For Developers

1. **Dependencies**: Keep all dependencies updated
2. **Code Review**: All code changes undergo security review
3. **Testing**: Security tests are included in the CI/CD pipeline
4. **Input Validation**: All user inputs are validated and sanitized
5. **Error Handling**: Sensitive information is not exposed in error messages

## Security Features

### Current Security Measures

- **Input Validation**: All DoIP messages are validated before processing
- **Address Validation**: Source and target addresses are validated per ECU
- **Configuration Validation**: YAML configurations are validated for security
- **Error Handling**: Secure error handling without information disclosure
- **Logging**: Comprehensive logging for security monitoring
- **Dependency Scanning**: Regular security scans of dependencies

### Security Tools

- **Bandit**: Static security analysis
- **Safety**: Dependency vulnerability scanning
- **Flake8**: Code quality and security linting
- **Pytest**: Security-focused testing

## Known Security Considerations

### DoIP Protocol Security

The DoIP protocol itself has some inherent security considerations:

1. **Network Exposure**: DoIP servers typically listen on network interfaces
2. **Authentication**: The DoIP protocol does not include built-in authentication
3. **Encryption**: DoIP messages are not encrypted by default
4. **Access Control**: Relies on network-level access control

### Mitigation Strategies

1. **Network Isolation**: Run DoIP Server in isolated network segments
2. **Firewall Rules**: Implement strict firewall rules
3. **VPN Access**: Use VPN for remote access
4. **Monitoring**: Implement network monitoring and logging
5. **Regular Updates**: Keep the server and dependencies updated

## Security Updates

Security updates are released as soon as possible after vulnerabilities are discovered and fixed. Updates are distributed through:

- **PyPI**: `pip install --upgrade doip-server`
- **GitHub Releases**: Tagged releases with security notes
- **Docker Images**: Updated container images
- **Git Repository**: Latest code with security fixes

## Security Changelog

### 2024-12-19
- Added comprehensive security documentation
- Implemented dependency vulnerability scanning
- Enhanced input validation for DoIP messages
- Improved error handling to prevent information disclosure

### 2024-11-15
- Fixed potential buffer overflow in message parsing
- Enhanced address validation
- Improved configuration file security

### 2024-10-20
- Initial security implementation
- Basic input validation
- Secure configuration handling

## Contact Information

For security-related questions or concerns:

- **Email**: alonsoram07@gmail.com
- **GitHub**: [Create a private security advisory](https://github.com/Alonso07/doip_server/security/advisories/new)
- **Response Time**: Within 48 hours for security issues

## Acknowledgments

We thank the security researchers and community members who help us maintain the security of DoIP Server. Security researchers who responsibly disclose vulnerabilities will be acknowledged in our security changelog (unless they prefer to remain anonymous).

## Legal

This security policy is provided for informational purposes only. By using DoIP Server, you agree to use it responsibly and in accordance with applicable laws and regulations. The maintainers of DoIP Server are not liable for any security issues or damages resulting from the use of this software.
