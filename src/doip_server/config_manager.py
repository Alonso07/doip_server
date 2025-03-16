#!/usr/bin/env python3
"""
Configuration Manager for DoIP Server
Handles loading and parsing of YAML configuration files
"""

import yaml
import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

class DoIPConfigManager:
    """Manages DoIP server configuration from YAML files"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the configuration manager
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path or self._find_default_config()
        self.config = {}
        self.logger = logging.getLogger(__name__)
        self._load_config()
    
    def _find_default_config(self) -> str:
        """Find the default configuration file path"""
        # Look for config in multiple locations
        possible_paths = [
            "config/doip_config.yaml",
            "doip_config.yaml",
            "../config/doip_config.yaml",
            "src/doip_server/config/doip_config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # If no config found, create a default one
        default_config = self._create_default_config()
        return default_config
    
    def _create_default_config(self) -> str:
        """Create a default configuration file if none exists"""
        default_config_content = """# Default DoIP Configuration
server:
  host: "0.0.0.0"
  port: 13400
  max_connections: 5
  timeout: 30

protocol:
  version: 0x02
  inverse_version: 0xFD

addresses:
  allowed_sources: [0x0E00]
  target_addresses: [0x1000]
  default_source: 0x1000

routine_activation:
  supported_routines:
    0x0202:
      name: "Example Routine"
      response_code: 0x10
      type: 0x0001

uds_services:
  0x22:
    supported_data_identifiers:
      0xF187:
        response_data: [0x01, 0x02, 0x03, 0x04]
"""
        
        # Create config directory if it doesn't exist
        os.makedirs("config", exist_ok=True)
        config_path = "config/doip_config.yaml"
        
        with open(config_path, 'w') as f:
            f.write(default_config_content)
        
        self.logger.info(f"Created default configuration file: {config_path}")
        return config_path
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            self.logger.info(f"Configuration loaded from: {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config = self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Get fallback configuration if YAML loading fails"""
        return {
            'server': {'host': '0.0.0.0', 'port': 13400},
            'protocol': {'version': 0x02, 'inverse_version': 0xFD},
            'addresses': {'allowed_sources': [0x0E00], 'target_addresses': [0x1000]},
            'routine_activation': {'supported_routines': {}},
            'uds_services': {}
        }
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return self.config.get('server', {})
    
    def get_server_binding_info(self) -> tuple[str, int]:
        """Get server host and port for binding
        
        Returns:
            tuple: (host, port) for server binding
        """
        server_config = self.get_server_config()
        host = server_config.get('host', '0.0.0.0')
        port = server_config.get('port', 13400)
        return host, port
    
    def get_protocol_config(self) -> Dict[str, Any]:
        """Get protocol configuration"""
        return self.config.get('protocol', {})
    
    def get_addresses_config(self) -> Dict[str, Any]:
        """Get addresses configuration"""
        return self.config.get('addresses', {})
    
    def get_routine_activation_config(self) -> Dict[str, Any]:
        """Get routine activation configuration"""
        return self.config.get('routine_activation', {})
    
    def get_uds_services_config(self) -> Dict[str, Any]:
        """Get UDS services configuration"""
        return self.config.get('uds_services', {})
    
    def get_response_codes_config(self) -> Dict[str, Any]:
        """Get response codes configuration"""
        return self.config.get('response_codes', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config.get('logging', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return self.config.get('security', {})
    
    def is_source_address_allowed(self, source_addr: int) -> bool:
        """Check if source address is allowed"""
        allowed_sources = self.get_addresses_config().get('allowed_sources', [])
        return source_addr in allowed_sources
    
    def is_target_address_valid(self, target_addr: int) -> bool:
        """Check if target address is valid"""
        target_addresses = self.get_addresses_config().get('target_addresses', [])
        return target_addr in target_addresses
    
    def get_default_source_address(self) -> int:
        """Get default source address for responses"""
        return self.get_addresses_config().get('default_source', 0x1000)
    
    def get_supported_routine(self, routine_id: int) -> Optional[Dict[str, Any]]:
        """Get supported routine configuration"""
        routines = self.get_routine_activation_config().get('supported_routines', {})
        return routines.get(routine_id)
    
    def get_routine_default_response(self) -> Dict[str, Any]:
        """Get default response for unsupported routines"""
        return self.get_routine_activation_config().get('default_response', {
            'code': 0x31,
            'message': 'Routine not supported'
        })
    
    def get_supported_uds_service(self, service_id: int) -> Optional[Dict[str, Any]]:
        """Get supported UDS service configuration"""
        services = self.get_uds_services_config()
        return services.get(service_id)
    
    def get_supported_data_identifier(self, service_id: int, data_id: int) -> Optional[Dict[str, Any]]:
        """Get supported data identifier configuration"""
        service = self.get_supported_uds_service(service_id)
        if service:
            data_ids = service.get('supported_data_identifiers', {})
            return data_ids.get(data_id)
        return None
    
    def get_uds_default_negative_response(self, service_id: int) -> Dict[str, Any]:
        """Get default negative response for UDS service"""
        service = self.get_supported_uds_service(service_id)
        if service:
            return service.get('default_negative_response', {
                'code': 0x31,
                'message': 'Service not supported'
            })
        return {'code': 0x7F, 'message': 'Service not supported'}
    
    def get_response_code_description(self, category: str, code: int) -> str:
        """Get description for a response code"""
        response_codes = self.get_response_codes_config()
        category_codes = response_codes.get(category, {})
        return category_codes.get(code, f"Unknown response code: 0x{code:02X}")
    
    def reload_config(self):
        """Reload configuration from file"""
        self._load_config()
        self.logger.info("Configuration reloaded")
    
    def validate_config(self) -> bool:
        """Validate configuration structure"""
        required_sections = ['server', 'protocol', 'addresses']
        
        for section in required_sections:
            if section not in self.config:
                self.logger.error(f"Missing required configuration section: {section}")
                return False
        
        # Validate protocol version
        protocol = self.get_protocol_config()
        if 'version' not in protocol or 'inverse_version' not in protocol:
            self.logger.error("Missing protocol version configuration")
            return False
        
        # Validate addresses
        addresses = self.get_addresses_config()
        if 'target_addresses' not in addresses or not addresses['target_addresses']:
            self.logger.error("Missing or empty target addresses configuration")
            return False
        
        self.logger.info("Configuration validation passed")
        return True
    
    def get_config_summary(self) -> str:
        """Get a summary of the current configuration"""
        summary = []
        summary.append("DoIP Configuration Summary")
        summary.append("=" * 40)
        
        # Server config
        server = self.get_server_config()
        summary.append(f"Server: {server.get('host', 'N/A')}:{server.get('port', 'N/A')}")
        
        # Protocol config
        protocol = self.get_protocol_config()
        summary.append(f"Protocol Version: 0x{protocol.get('version', 'N/A'):02X}")
        
        # Addresses
        addresses = self.get_addresses_config()
        summary.append(f"Target Addresses: {len(addresses.get('target_addresses', []))}")
        summary.append(f"Allowed Sources: {len(addresses.get('allowed_sources', []))}")
        
        # Routines
        routines = self.get_routine_activation_config()
        supported_routines = routines.get('supported_routines', {})
        summary.append(f"Supported Routines: {len(supported_routines)}")
        
        # UDS Services
        uds_services = self.get_uds_services_config()
        summary.append(f"UDS Services: {len(uds_services)}")
        
        return "\n".join(summary)
