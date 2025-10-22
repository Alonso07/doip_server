# DoIP Server

A Python implementation of DoIP (Diagnostics over Internet Protocol) server and client with comprehensive YAML configuration management.

## 🚀 Quick Start

```bash
# Install dependencies
poetry install

# Run with hierarchical configuration
poetry run python src/doip_server/main.py --gateway-config config/gateway1.yaml

# Test UDP Vehicle Identification
python scripts/utilities/run_udp_client.py --verbose

# Test Functional Diagnostics
python scripts/test/test_functional_diagnostics.py

# Test Hierarchical Configuration
python -m pytest tests/test_hierarchical_configuration.py -v

# Run comprehensive test suite
poetry run pytest tests/ -v
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[📖 Documentation Index](docs/INDEX.md)** - Complete documentation index
- **[🚀 Getting Started](docs/README.md)** - Detailed project overview and setup
- **[⚙️ Configuration Guide](docs/CONFIGURATION.md)** - Complete configuration guide
- **[🔧 API Reference](docs/API.md)** - API reference and examples
- **[🧪 Testing Guide](docs/TESTING.md)** - Testing guide and results
- **[🚀 Deployment Guide](docs/DEPLOYMENT.md)** - Deployment and CI/CD guide
- **[🤝 Contributing](docs/CONTRIBUTING.md)** - How to contribute to this project
- **[📋 Changelog](docs/CHANGELOG.md)** - Project changelog and release notes
- **[🔒 Security](docs/SECURITY.md)** - Security policy and vulnerability reporting
- **[📜 Code of Conduct](docs/CODE_OF_CONDUCT.md)** - Community guidelines

## ✨ Key Features

### 🏗️ Hierarchical Configuration System
- **Multi-File Architecture**: Gateway, ECU, and UDS services in separate files
- **Dynamic ECU Loading**: Add/remove ECUs at runtime without code changes
- **Service Isolation**: ECU-specific services with common service sharing
- **Address Validation**: Per-ECU source and target address validation
- **Configuration Validation**: Comprehensive validation with clear error reporting

### 🔧 Functional Diagnostics
- **Broadcast Communication**: Single request to multiple ECUs simultaneously
- **Functional Addressing**: Default 0x1FFF address for broadcast requests
- **Service Filtering**: Only ECUs supporting the service with functional addressing respond
- **Efficient Diagnostics**: Reduce network traffic and improve diagnostic efficiency
- **Flexible Configuration**: Per-service functional addressing support

### 🚀 Advanced Features
- **Response Cycling**: Automatic cycling through multiple responses per UDS service
- **No Response Configuration**: Configure services that don't send responses (Issue #35)
- **UDP Vehicle Identification**: Network discovery via UDP broadcasts
- **Per-ECU Services**: ECU-specific UDS service definitions
- **Comprehensive Testing**: 99.5% test pass rate with full core functionality
- **Backward Compatibility**: Support for legacy configuration formats

## 🏗️ Architecture

### Hierarchical Configuration System

The DoIP server uses a sophisticated hierarchical configuration system that separates concerns into three main components:

```
config/
├── gateway1.yaml          # Gateway network configuration & ECU references
├── ecu_engine.yaml        # Engine ECU configuration (0x1000)
├── ecu_transmission.yaml  # Transmission ECU configuration (0x1001)
├── ecu_abs.yaml          # ABS ECU configuration (0x1002)
└── uds_services.yaml     # UDS service definitions (common + ECU-specific)
```

### Configuration Components

```mermaid
graph LR
    subgraph "Configuration File Structure"
        GW["gateway1.yaml<br/>Gateway Configuration<br/>Network Settings<br/>Protocol Config<br/>ECU References<br/>Logging & Security"]
        
        subgraph "ECU Configuration Files"
            ECU1["ecu_engine.yaml<br/>Engine ECU (0x1000)<br/>Target Address<br/>Functional Address<br/>Tester Addresses<br/>Service References"]
            ECU2["ecu_transmission.yaml<br/>Transmission ECU (0x1001)<br/>Target Address<br/>Functional Address<br/>Tester Addresses<br/>Service References"]
            ECU3["ecu_abs.yaml<br/>ABS ECU (0x1002)<br/>Target Address<br/>Functional Address<br/>Tester Addresses<br/>Service References"]
        end
        
        subgraph "Service Configuration Files"
            COMMON["generic_uds_messages.yaml<br/>Common UDS Services<br/>Read VIN<br/>Session Control<br/>Tester Present<br/>Vehicle Type"]
            ENGINE["ecu_engine_services.yaml<br/>Engine-Specific Services<br/>Engine Diagnostics<br/>Engine Parameters<br/>Engine Controls"]
            TRANS["ecu_transmission_services.yaml<br/>Transmission Services<br/>Transmission Diagnostics<br/>Gear Status<br/>Transmission Controls"]
            ABS["ecu_abs_services.yaml<br/>ABS Services<br/>ABS Diagnostics<br/>Wheel Speed<br/>Brake Controls"]
        end
    end
    
    %% Relationships
    GW --> ECU1
    GW --> ECU2
    GW --> ECU3
    
    ECU1 --> COMMON
    ECU1 --> ENGINE
    ECU2 --> COMMON
    ECU2 --> TRANS
    ECU3 --> COMMON
    ECU3 --> ABS
    
    %% Styling
    classDef gatewayClass fill:#e3f2fd,stroke:#0277bd,stroke-width:3px
    classDef ecuClass fill:#f1f8e9,stroke:#388e3c,stroke-width:2px
    classDef serviceClass fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    
    class GW gatewayClass
    class ECU1,ECU2,ECU3 ecuClass
    class COMMON,ENGINE,TRANS,ABS serviceClass
```

#### 1. Gateway Configuration (`gateway1.yaml`)
- **Network Settings**: TCP/IP host, port, max connections, timeouts
- **Protocol Configuration**: DoIP version, inverse version
- **ECU References**: Dynamic list of ECU configuration files
- **Response Codes**: Gateway-level response configuration
- **Logging & Security**: Centralized logging and security settings

#### 2. ECU Configurations (`ecu_*.yaml`)
- **ECU Identity**: Name, description, target address
- **Functional Address**: Broadcast address for functional diagnostics (default: 0x1FFF)
- **Tester Addresses**: Allowed source addresses per ECU
- **Service References**: Common services + ECU-specific services
- **ECU-Specific Settings**: Custom configuration per ECU

#### 3. UDS Services Configuration (`uds_services.yaml`)
- **Common Services**: Available to all ECUs (Read VIN, Diagnostic Session Control, etc.)
- **ECU-Specific Services**: Engine, Transmission, ABS specific services
- **Functional Addressing Support**: Services marked for broadcast capability
- **Response Cycling**: Multiple response options per service

### Configuration Flow Diagram

```mermaid
graph TB
    subgraph "DoIP Server Architecture"
        subgraph "Configuration Layer"
            GW["Gateway Configuration<br/>gateway1.yaml<br/>Network Settings<br/>Protocol Config<br/>ECU References<br/>Logging & Security"]
            
            subgraph "ECU Configurations"
                ECU1["Engine ECU<br/>0x1000<br/>Target Address<br/>Functional Address<br/>Tester Addresses"]
                ECU2["Transmission ECU<br/>0x1001<br/>Target Address<br/>Functional Address<br/>Tester Addresses"]
                ECU3["ABS ECU<br/>0x1002<br/>Target Address<br/>Functional Address<br/>Tester Addresses"]
            end
            
            subgraph "UDS Services"
                COMMON["Common Services<br/>Read VIN<br/>Session Control<br/>Tester Present<br/>Vehicle Type"]
                SPECIFIC["ECU-Specific Services<br/>Engine Services<br/>Transmission Services<br/>ABS Services"]
            end
        end
        
        subgraph "DoIP Server Core"
            UDP["UDP Handler<br/>Vehicle Identification<br/>VIN Requests<br/>Entity Status<br/>Power Mode"]
            TCP["TCP Handler<br/>Diagnostic Sessions<br/>Routing Activation<br/>Connection Management<br/>Keep-Alive"]
            UDS["UDS Message Handler<br/>Diagnostic Processing<br/>Service Routing<br/>Response Generation<br/>Error Handling"]
        end
        
        subgraph "Communication Layer"
            PHYSICAL["Physical Addressing<br/>Direct ECU Communication<br/>Single ECU Response<br/>Specific Target Address"]
            FUNCTIONAL["Functional Addressing<br/>Broadcast Communication<br/>Multiple ECU Response<br/>Service Filtering<br/>0x1FFF Address"]
        end
        
        subgraph "Client Interface"
            CLIENT["DoIP Client<br/>Connection Management<br/>Message Sending<br/>Response Handling"]
        end
    end
    
    %% Configuration Flow
    GW --> ECU1
    GW --> ECU2
    GW --> ECU3
    GW --> COMMON
    GW --> SPECIFIC
    
    %% Service Assignment
    COMMON --> ECU1
    COMMON --> ECU2
    COMMON --> ECU3
    SPECIFIC --> ECU1
    SPECIFIC --> ECU2
    SPECIFIC --> ECU3
    
    %% Server Processing
    UDP --> UDS
    TCP --> UDS
    UDS --> PHYSICAL
    UDS --> FUNCTIONAL
    
    %% Client Communication
    CLIENT --> UDP
    CLIENT --> TCP
    CLIENT --> PHYSICAL
    CLIENT --> FUNCTIONAL
    
    %% Styling
    classDef configClass fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef serverClass fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef commClass fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef clientClass fill:#fff3e0,stroke:#e65100,stroke-width:2px
    
    class GW,ECU1,ECU2,ECU3,COMMON,SPECIFIC configClass
    class UDP,TCP,UDS serverClass
    class PHYSICAL,FUNCTIONAL commClass
    class CLIENT clientClass
```

### Communication Flow Diagram

```mermaid
sequenceDiagram
    participant Client as DoIP Client
    participant UDP as UDP Handler
    participant TCP as TCP Handler
    participant UDS as UDS Handler
    participant ECU1 as Engine ECU
    participant ECU2 as Transmission ECU
    participant ECU3 as ABS ECU
    
    Note over Client,ECU3: Vehicle Identification (UDP)
    Client->>UDP: Vehicle Identification Request
    UDP->>Client: VIN + Entity Status Response
    
    Note over Client,ECU3: Diagnostic Session Setup (TCP)
    Client->>TCP: TCP Connection Request
    TCP->>Client: Connection Established
    Client->>TCP: Routing Activation Request
    TCP->>Client: Routing Activation Response
    
    Note over Client,ECU3: Physical Addressing (Single ECU)
    Client->>TCP: UDS Request (Target: 0x1000)
    TCP->>UDS: Route to Engine ECU
    UDS->>ECU1: Process UDS Service
    ECU1->>UDS: UDS Response
    UDS->>TCP: Forward Response
    TCP->>Client: UDS Response
    
    Note over Client,ECU3: Functional Addressing (Multiple ECUs)
    Client->>TCP: UDS Request (Target: 0x1FFF)
    TCP->>UDS: Route to All ECUs
    UDS->>ECU1: Process UDS Service
    UDS->>ECU2: Process UDS Service
    UDS->>ECU3: Process UDS Service
    ECU1->>UDS: UDS Response (if supported)
    ECU2->>UDS: UDS Response (if supported)
    ECU3->>UDS: UDS Response (if supported)
    UDS->>TCP: Aggregate Responses
    TCP->>Client: Multiple UDS Responses
    
    Note over Client,ECU3: Session Maintenance
    Client->>TCP: Tester Present
    TCP->>UDS: Keep-Alive Processing
    UDS->>ECU1: Update Session Status
    UDS->>ECU2: Update Session Status
    UDS->>ECU3: Update Session Status
```

### Benefits of Hierarchical Configuration

#### 🎯 **Separation of Concerns**
- **Gateway Configuration**: Network and protocol settings centralized
- **ECU Configuration**: Individual ECU settings isolated and manageable
- **Service Configuration**: UDS services organized by category and ECU

#### 🔄 **Dynamic Management**
- **Runtime ECU Loading**: Add/remove ECUs without server restart
- **Service Isolation**: ECU-specific services don't interfere with others
- **Easy Scaling**: Add new ECUs by simply adding configuration files

#### 🛡️ **Enhanced Security & Validation**
- **Per-ECU Address Validation**: Source addresses validated per ECU
- **Service Authorization**: Only authorized services available per ECU
- **Configuration Validation**: Comprehensive validation with clear error messages

#### 📈 **Improved Maintainability**
- **Modular Structure**: Easy to understand and modify
- **Clear Ownership**: Each configuration file has a specific purpose
- **Backward Compatibility**: Legacy configurations still supported

## 🔧 Functional Diagnostics

### Overview

The DoIP server supports **functional diagnostics**, enabling broadcast communication to multiple ECUs using a single request. This powerful feature allows clients to efficiently communicate with multiple ECUs simultaneously.

### Key Concepts

#### Functional Addressing
- **Functional Address**: Special logical address (default: `0x1FFF`) representing multiple ECUs
- **Broadcast Communication**: Single request sent to multiple ECUs that support the service
- **Service Filtering**: Only ECUs supporting the requested UDS service with functional addressing respond

#### Physical vs Functional Addressing
- **Physical Addressing**: Direct communication with specific ECU using unique logical address
- **Functional Addressing**: Broadcast communication to multiple ECUs using shared functional address

### Configuration

#### ECU Configuration
Each ECU configuration includes a functional address:

```yaml
ecu:
  name: "Engine_ECU"
  target_address: 0x1000
  functional_address: 0x1FFF  # Broadcast address
  tester_addresses: [0x0E00, 0x0E01, 0x0E02]
```

#### UDS Services Configuration
Services supporting functional addressing are marked:

```yaml
common_services:
  Read_VIN:
    request: "0x22F190"
    responses: ["0x62F1901020011223344556677889AABB"]
    supports_functional: true  # Enables broadcast capability
```

### Usage Examples

#### Basic Functional Request
```python
from doip_client.doip_client import DoIPClientWrapper

# Create client
client = DoIPClientWrapper(
    server_host="127.0.0.1",
    server_port=13400,
    logical_address=0x0E00,
    target_address=0x1000
)

# Connect and send functional request
client.connect()
response = client.send_functional_read_data_by_identifier(0xF190)  # Read VIN
print(f"Response: {response.hex()}")
client.disconnect()
```

#### Functional vs Physical Comparison
```python
# Physical addressing - Engine ECU only
response_physical = client.send_read_data_by_identifier(0xF190)

# Functional addressing - All ECUs that support it
response_functional = client.send_functional_read_data_by_identifier(0xF190)
```

### Supported Services

#### Common Services (All ECUs)
- `Read_VIN` - Vehicle Identification Number
- `Read_Vehicle_Type` - Vehicle Type Information
- `Diagnostic_Session_Control` - Session management
- `Tester_Present` - Keep-alive functionality

#### ECU-Specific Services
- `Engine_Diagnostic_Codes` - Engine trouble codes
- `Transmission_Diagnostic_Codes` - Transmission trouble codes
- `ABS_Diagnostic_Codes` - ABS trouble codes

### Testing

```bash
# Test functional diagnostics
python scripts/test/test_functional_diagnostics.py

# Run functional demo
python -c "from doip_client.doip_client import DoIPClientWrapper; DoIPClientWrapper().run_functional_demo()"
```

## 📊 Test Status

- **Unit Tests**: 17/17 ✅ (100%)
- **Hierarchical Config Tests**: 21/21 ✅ (100%)
- **Response Cycling Tests**: 9/9 ✅ (100%)
- **Legacy Integration Tests**: 13/13 ✅ (100%)
- **Client Extended Tests**: 25/25 ✅ (100%)
- **Main Module Tests**: 12/12 ✅ (100%)
- **Validate Config Tests**: 15/15 ✅ (100%)
- **Debug Client Tests**: 30/30 ✅ (100%)
- **Demo Tests**: 5/6 ✅ (83% - 1 skipped)
- **Overall**: 185/186 tests passing (99.5% success rate)

## 🔧 Development

```bash
# Run tests
poetry run pytest tests/ -v

# Run specific test categories
poetry run pytest tests/test_doip_unit.py -v
poetry run pytest tests/test_hierarchical_configuration.py -v
poetry run pytest tests/test_response_cycling.py -v
```

## 📖 Documentation

For detailed documentation, see the [docs/](docs/) directory or start with the [Documentation Index](docs/INDEX.md).

---

*For complete documentation and implementation details, see the [docs/](docs/) directory.*
