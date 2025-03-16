#!/usr/bin/env python3
import socket
import struct
import time

# DoIP Protocol constants
DOIP_PROTOCOL_VERSION = 0x02
DOIP_INVERSE_PROTOCOL_VERSION = 0xFD

# DoIP Payload types
PAYLOAD_TYPE_ALIVE_CHECK_REQUEST = 0x0001
PAYLOAD_TYPE_ROUTINE_ACTIVATION_REQUEST = 0x0005
PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE = 0x8001

# UDS Service IDs
UDS_READ_DATA_BY_IDENTIFIER = 0x22

class DoIPClient:
    def __init__(self, server_host='127.0.0.1', server_port=13400):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        
    def connect(self):
        """Connect to the DoIP server"""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_host, self.server_port))
        print(f"Connected to DoIP server at {self.server_host}:{self.server_port}")
        
    def disconnect(self):
        """Disconnect from the DoIP server"""
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            
    def send_message(self, message):
        """Send a message to the server and receive response"""
        if not self.client_socket:
            print("Not connected to server")
            return None
            
        print(f"Sending message: {message.hex()}")
        self.client_socket.send(message)
        
        response = self.client_socket.recv(1024)
        print(f"Received response: {response.hex()}")
        return response
        
    def create_doip_header(self, payload_type, payload_length):
        """Create DoIP header"""
        return struct.pack('>BBHI', 
                          DOIP_PROTOCOL_VERSION,
                          DOIP_INVERSE_PROTOCOL_VERSION,
                          payload_type,
                          payload_length)
    
    def send_routine_activation(self, routine_identifier=0x0202, routine_type=0x0001):
        """Send routine activation request"""
        print(f"\n=== Sending Routine Activation Request ===")
        print(f"Routine Identifier: 0x{routine_identifier:04X}")
        print(f"Routine Type: 0x{routine_type:04X}")
        
        # Create payload
        payload = struct.pack('>HH', routine_identifier, routine_type)
        
        # Create DoIP message
        header = self.create_doip_header(PAYLOAD_TYPE_ROUTINE_ACTIVATION_REQUEST, len(payload))
        message = header + payload
        
        return self.send_message(message)
    
    def send_uds_read_data_by_identifier(self, data_identifier, source_addr=0x0E00, target_addr=0x1000):
        """Send UDS Read Data by Identifier request"""
        print(f"\n=== Sending UDS Read Data by Identifier Request ===")
        print(f"Data Identifier: 0x{data_identifier:04X}")
        print(f"Source Address: 0x{source_addr:04X}")
        print(f"Target Address: 0x{target_addr:04X}")
        
        # Create UDS payload
        uds_payload = struct.pack('>BH', UDS_READ_DATA_BY_IDENTIFIER, data_identifier)
        
        # Create DoIP payload
        payload = struct.pack('>HH', source_addr, target_addr) + uds_payload
        
        # Create DoIP message
        header = self.create_doip_header(PAYLOAD_TYPE_DIAGNOSTIC_MESSAGE, len(payload))
        message = header + payload
        
        return self.send_message(message)
    
    def send_alive_check(self):
        """Send alive check request"""
        print(f"\n=== Sending Alive Check Request ===")
        
        # Empty payload for alive check
        payload = b''
        
        # Create DoIP message
        header = self.create_doip_header(PAYLOAD_TYPE_ALIVE_CHECK_REQUEST, len(payload))
        message = header + payload
        
        return self.send_message(message)
    
    def run_demo(self):
        """Run a demonstration of all DoIP functionality"""
        try:
            self.connect()
            
            # Send alive check
            self.send_alive_check()
            time.sleep(1)
            
            # Send routine activation
            self.send_routine_activation(0x0202, 0x0001)
            time.sleep(1)
            
            # Send UDS Read Data by Identifier requests
            data_identifiers = [0xF187, 0xF188, 0xF189, 0xF190]  # Last one should fail
            for di in data_identifiers:
                self.send_uds_read_data_by_identifier(di)
                time.sleep(1)
                
        except Exception as e:
            print(f"Error during demo: {e}")
        finally:
            self.disconnect()

def start_doip_client(server_host='127.0.0.1', server_port=13400):
    """Start the DoIP client (entry point for poetry script)"""
    client = DoIPClient(server_host, server_port)
    client.run_demo()

def create_doip_request():
    """Legacy function for backward compatibility"""
    # Create a simple routine activation request
    payload = struct.pack('>HH', 0x0202, 0x0001)
    header = struct.pack('>BBHI', 0x02, 0xFD, 0x0005, len(payload))
    return header + payload

if __name__ == "__main__":
    start_doip_client()
