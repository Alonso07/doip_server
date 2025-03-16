#!/usr/bin/env python3
import socket
import struct
import logging
from scapy.all import *
from .config_manager import DoIPConfigManager

# DoIP Protocol constants
DOIP_PROTOCOL_VERSION = 0x02
DOIP_INVERSE_PROTOCOL_VERSION = 0xFD

# DoIP Payload types
PAYLOAD_TYPE_ALIVE_CHECK_REQUEST = 0x0001
PAYLOAD_TYPE_ALIVE_CHECK_RESPONSE = 0x0002
PAYLOAD_TYPE_ROUTINE_ACTIVATION_REQUEST = 0x0005
PAYLOAD_TYPE_ROUTINE_ACTIVATION_RESPONSE = 0x0006
PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE = 0x8001
PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE_ACK = 0x8002
PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE_NACK = 0x8003

# UDS Service IDs
UDS_READ_DATA_BY_IDENTIFIER = 0x22

# Response codes
ROUTINE_ACTIVATION_RESPONSE_CODE_SUCCESS = 0x10
ROUTINE_ACTIVATION_RESPONSE_CODE_INCORRECT_ROUTINE_IDENTIFIER = 0x31
ROUTINE_ACTIVATION_RESPONSE_CODE_CONDITIONS_NOT_CORRECT = 0x22

class DoIPServer:
    def __init__(self, host=None, port=None, config_path=None):
        # Initialize configuration manager
        self.config_manager = DoIPConfigManager(config_path)
        
        # Get server configuration - prioritize explicit parameters over config
        config_host, config_port = self.config_manager.get_server_binding_info()
        self.host = host if host is not None else config_host
        self.port = port if port is not None else config_port
        
        # Get other server configuration
        server_config = self.config_manager.get_server_config()
        self.max_connections = server_config.get('max_connections', 5)
        self.timeout = server_config.get('timeout', 30)
        
        # Get protocol configuration
        protocol_config = self.config_manager.get_protocol_config()
        self.protocol_version = protocol_config.get('version', 0x02)
        self.inverse_protocol_version = protocol_config.get('inverse_version', 0xFD)
        
        # Initialize server state
        self.server_socket = None
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
        # Validate configuration
        if not self.config_manager.validate_config():
            self.logger.warning("Configuration validation failed, using fallback settings")
        
        # Validate host and port configuration
        self._validate_binding_config()
    
    def _validate_binding_config(self):
        """Validate host and port configuration"""
        # Validate host
        if not self.host or self.host.strip() == "":
            self.logger.error("Invalid host configuration: host cannot be empty")
            raise ValueError("Invalid host configuration: host cannot be empty")
        
        # Validate port
        if not isinstance(self.port, int) or self.port < 1 or self.port > 65535:
            self.logger.error(f"Invalid port configuration: port must be between 1-65535, got {self.port}")
            raise ValueError(f"Invalid port configuration: port must be between 1-65535, got {self.port}")
        
        # Validate max_connections
        if not isinstance(self.max_connections, int) or self.max_connections < 1:
            self.logger.error(f"Invalid max_connections configuration: must be positive integer, got {self.max_connections}")
            raise ValueError(f"Invalid max_connections configuration: must be positive integer, got {self.max_connections}")
        
        # Validate timeout
        if not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
            self.logger.error(f"Invalid timeout configuration: must be positive number, got {self.timeout}")
            raise ValueError(f"Invalid timeout configuration: must be positive number, got {self.timeout}")
        
        self.logger.info(f"Binding configuration validated: {self.host}:{self.port}")
        self.logger.info(f"Server settings: max_connections={self.max_connections}, timeout={self.timeout}s")
    
    def get_binding_info(self) -> tuple[str, int]:
        """Get current server binding information
        
        Returns:
            tuple: (host, port) for current server binding
        """
        return self.host, self.port
    
    def get_server_info(self) -> dict:
        """Get comprehensive server information
        
        Returns:
            dict: Server configuration and status information
        """
        return {
            'host': self.host,
            'port': self.port,
            'max_connections': self.max_connections,
            'timeout': self.timeout,
            'running': self.running,
            'protocol_version': f"0x{self.protocol_version:02X}",
            'inverse_protocol_version': f"0x{self.inverse_protocol_version:02X}"
        }
    
    def _setup_logging(self):
        """Setup logging based on configuration"""
        logging_config = self.config_manager.get_logging_config()
        log_level = getattr(logging, logging_config.get('level', 'INFO'))
        log_format = logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(),  # Console handler
                logging.FileHandler(logging_config.get('file', 'doip_server.log')) if logging_config.get('file') else logging.NullHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging configured")
    
    def start(self):
        """Start the DoIP server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.max_connections)
        self.running = True
        
        self.logger.info(f"DoIP server listening on {self.host}:{self.port}")
        self.logger.info(self.config_manager.get_config_summary())
        
        print(f"DoIP server listening on {self.host}:{self.port}")
        
        try:
            while self.running:
                client_socket, client_address = self.server_socket.accept()
                print(f"Connection from {client_address}")
                self.handle_client(client_socket)
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the DoIP server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
    
    def handle_client(self, client_socket):
        """Handle client connection"""
        try:
            while self.running:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                print(f"Received data: {data.hex()}")
                response = self.process_doip_message(data)
                if response:
                    client_socket.send(response)
                    print(f"Sent response: {response.hex()}")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
    
    def process_doip_message(self, data):
        """Process incoming DoIP message and return appropriate response"""
        if len(data) < 8:  # Minimum DoIP header size
            return None
        
        # Parse DoIP header
        protocol_version = data[0]
        inverse_protocol_version = data[1]
        payload_type = struct.unpack('>H', data[2:4])[0]
        payload_length = struct.unpack('>I', data[4:8])[0]
        
        print(f"Protocol Version: 0x{protocol_version:02X}")
        print(f"Inverse Protocol Version: 0x{inverse_protocol_version:02X}")
        print(f"Payload Type: 0x{payload_type:04X}")
        print(f"Payload Length: {payload_length}")
        
        # Validate protocol version
        if protocol_version != self.protocol_version or inverse_protocol_version != self.inverse_protocol_version:
            self.logger.warning(f"Invalid protocol version: 0x{protocol_version:02X}, expected 0x{self.protocol_version:02X}")
            return self.create_doip_nack(0x02)  # Invalid protocol version
        
        # Process based on payload type
        if payload_type == PAYLOAD_TYPE_ROUTINE_ACTIVATION_REQUEST:
            return self.handle_routine_activation(data[8:])
        elif payload_type == PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE:
            return self.handle_diagnostic_message(data[8:])
        elif payload_type == PAYLOAD_TYPE_ALIVE_CHECK_REQUEST:
            return self.handle_alive_check()
        else:
            print(f"Unsupported payload type: 0x{payload_type:04X}")
            return None
    
    def handle_routine_activation(self, payload):
        """Handle routine activation request"""
        self.logger.info("Processing routine activation request")
        
        if len(payload) < 4:
            self.logger.warning("Routine activation payload too short")
            return self.create_routine_activation_response(ROUTINE_ACTIVATION_RESPONSE_CODE_CONDITIONS_NOT_CORRECT)
        
        # Extract routine identifier
        routine_identifier = struct.unpack('>H', payload[0:2])[0]
        routine_type = struct.unpack('>H', payload[2:4])[0]
        
        self.logger.info(f"Routine Identifier: 0x{routine_identifier:04X}")
        self.logger.info(f"Routine Type: 0x{routine_type:04X}")
        
        # Check if routine is supported
        routine_config = self.config_manager.get_supported_routine(routine_identifier)
        if routine_config:
            self.logger.info(f"Routine '{routine_config.get('name', 'Unknown')}' activated successfully")
            return self.create_routine_activation_response(routine_config.get('response_code', 0x10))
        else:
            default_response = self.config_manager.get_routine_default_response()
            self.logger.warning(f"Unsupported routine 0x{routine_identifier:04X}: {default_response.get('message', 'Routine not supported')}")
            return self.create_routine_activation_response(default_response.get('code', 0x31))
    
    def handle_diagnostic_message(self, payload):
        """Handle diagnostic message (UDS)"""
        self.logger.info("Processing diagnostic message")
        
        if len(payload) < 4:
            self.logger.warning("Diagnostic message payload too short")
            return None
        
        # Extract source and target addresses
        source_address = struct.unpack('>H', payload[0:2])[0]
        target_address = struct.unpack('>H', payload[2:4])[0]
        uds_payload = payload[4:]
        
        self.logger.info(f"Source Address: 0x{source_address:04X}")
        self.logger.info(f"Target Address: 0x{target_address:04X}")
        self.logger.info(f"UDS Payload: {uds_payload.hex()}")
        
        # Validate addresses
        if not self.config_manager.is_source_address_allowed(source_address):
            self.logger.warning(f"Source address 0x{source_address:04X} not allowed")
            return self.create_doip_nack(0x03)  # Unsupported source address
        
        if not self.config_manager.is_target_address_valid(target_address):
            self.logger.warning(f"Target address 0x{target_address:04X} not valid")
            return self.create_doip_nack(0x04)  # Unsupported target address
        
        # Process UDS message
        uds_response = self.process_uds_message(uds_payload)
        if uds_response:
            return self.create_diagnostic_message_response(target_address, source_address, uds_response)
        
        return None
    
    def process_uds_message(self, uds_payload):
        """Process UDS message and return response"""
        if not uds_payload:
            return None
        
        service_id = uds_payload[0]
        self.logger.info(f"UDS Service ID: 0x{service_id:02X}")
        
        # Check if service is supported
        service_config = self.config_manager.get_supported_uds_service(service_id)
        if service_config:
            self.logger.info(f"Processing UDS service: {service_config.get('name', 'Unknown')}")
            if service_id == UDS_READ_DATA_BY_IDENTIFIER:
                return self.handle_read_data_by_identifier(uds_payload[1:])
            # Add more UDS services here as needed
        else:
            self.logger.warning(f"Unsupported UDS service: 0x{service_id:02X}")
            default_response = self.config_manager.get_uds_default_negative_response(service_id)
            return self.create_uds_negative_response(service_id, default_response.get('code', 0x7F))
        
        return None
    
    def handle_read_data_by_identifier(self, payload):
        """Handle UDS Read Data by Identifier (0x22)"""
        self.logger.info("Processing Read Data by Identifier request")
        
        if len(payload) < 2:
            self.logger.warning("Data identifier payload too short")
            return None
        
        data_identifier = struct.unpack('>H', payload[0:2])[0]
        self.logger.info(f"Data Identifier: 0x{data_identifier:04X}")
        
        # Check if data identifier is supported
        data_config = self.config_manager.get_supported_data_identifier(UDS_READ_DATA_BY_IDENTIFIER, data_identifier)
        if data_config:
            self.logger.info(f"Data identifier '{data_config.get('name', 'Unknown')}' requested")
            
            # Convert response data from list to bytes
            response_data = bytes(data_config.get('response_data', []))
            
            # Create UDS positive response (0x62 + data identifier + data)
            uds_response = b'\x62' + struct.pack('>H', data_identifier) + response_data
            
            self.logger.info(f"Returning {len(response_data)} bytes of data")
            return uds_response
        else:
            # Negative response - data identifier not supported
            default_response = self.config_manager.get_uds_default_negative_response(UDS_READ_DATA_BY_IDENTIFIER)
            self.logger.warning(f"Unsupported data identifier 0x{data_identifier:04X}: {default_response.get('message', 'Data identifier not supported')}")
            return self.create_uds_negative_response(UDS_READ_DATA_BY_IDENTIFIER, default_response.get('code', 0x31))
    
    def handle_alive_check(self):
        """Handle alive check request"""
        self.logger.info("Processing alive check request")
        return self.create_alive_check_response()
    
    def create_uds_negative_response(self, service_id: int, nrc: int) -> bytes:
        """Create UDS negative response"""
        # UDS negative response format: 0x7F + service_id + NRC
        return b'\x7F' + bytes([service_id]) + bytes([nrc])
    
    def create_routine_activation_response(self, response_code):
        """Create routine activation response"""
        payload = struct.pack('>H', response_code)  # Response code
        payload += b'\x00\x00'  # Optional routine type
        
        header = struct.pack('>BBHI', 
                           self.protocol_version,
                           self.inverse_protocol_version,
                           PAYLOAD_TYPE_ROUTINE_ACTIVATION_RESPONSE,
                           len(payload))
        
        # Log response code description
        response_desc = self.config_manager.get_response_code_description('routine_activation', response_code)
        self.logger.info(f"Routine activation response: {response_desc}")
        
        return header + payload
    
    def create_diagnostic_message_response(self, source_addr, target_addr, uds_response):
        """Create diagnostic message response"""
        payload = struct.pack('>HH', source_addr, target_addr) + uds_response
        
        header = struct.pack('>BBHI',
                           self.protocol_version,
                           self.inverse_protocol_version,
                           PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE,
                           len(payload))
        
        return header + payload
    
    def create_alive_check_response(self):
        """Create alive check response"""
        payload = b'\x00\x00'  # Empty payload for alive check response
        
        header = struct.pack('>BBHI',
                           self.protocol_version,
                           self.inverse_protocol_version,
                           PAYLOAD_TYPE_ALIVE_CHECK_RESPONSE,
                           len(payload))
        
        return header + payload
    
    def create_doip_nack(self, nack_code):
        """Create DoIP negative acknowledgment"""
        payload = struct.pack('>I', nack_code)
        
        header = struct.pack('>BBHI',
                           self.protocol_version,
                           self.inverse_protocol_version,
                           0x8000,  # Generic NACK payload type
                           len(payload))
        
        return header + payload

def start_doip_server(host=None, port=None, config_path=None):
    """Start the DoIP server (entry point for poetry script)"""
    server = DoIPServer(host, port, config_path)
    server.start()

if __name__ == "__main__":
    start_doip_server()
