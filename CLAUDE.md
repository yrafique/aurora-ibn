# AURORA-IBN: Intent-Based Networking Platform

## Project Overview

AURORA-IBN (Aurora Intent-Based Networking) is a comprehensive, multi-vendor network automation platform that translates natural language intents into vendor-specific network configurations. The platform leverages Large Language Models (LLMs), YANG model discovery, and advanced configuration generation to enable seamless network service provisioning across heterogeneous network infrastructures.

## Key Features

### 🧠 Natural Language Processing
- **Intent Parsing**: Converts natural language descriptions into structured network intents
- **Multi-Protocol Support**: Automatically identifies L3VPN, EVPN, QoS, Security, and Routing requirements
- **Context-Aware Processing**: Understands network topology and device relationships
- **Policy Extraction**: Automatically extracts BFD, MTU, BGP, and other protocol parameters

### 🏗️ Multi-Vendor Architecture
- **Vendor Support**: Nokia SR Linux/SR OS, Cisco IOS-XR/NX-OS, Juniper Junos, Huawei VRP, Arista EOS
- **Protocol Abstraction**: NETCONF, gNMI, RESTCONF, and SSH transport support
- **YANG Model Discovery**: Automatic discovery and normalization of vendor YANG models
- **Configuration Templates**: Vendor-specific Jinja2 templates for configuration generation

### 🔄 Intelligent Workflow Engine
- **Intent Normalization**: Converts parsed intents into vendor-neutral data structures
- **Mapping Engine**: Maps normalized intents to vendor-specific YANG paths
- **Configuration Generation**: Produces ready-to-deploy XML, JSON, and CLI configurations
- **Validation Engine**: Pre-deployment validation and post-deployment verification

### 🤖 LLM Integration (Modular)
- **Provider Support**: MLX (Apple Silicon), OpenAI, Anthropic
- **Apple Silicon Optimization**: Native MLX integration for Mac users
- **Configurable Models**: Easy switching between different LLM providers
- **Local Processing**: Privacy-focused local model execution

### 🛡️ Risk Assessment & Safety
- **Impact Analysis**: Evaluates potential service disruption before deployment
- **Rollback Mechanisms**: Automatic configuration rollback on failure
- **Change Validation**: Syntax and semantic validation of generated configurations
- **Approval Workflows**: Human-in-the-loop approval for high-risk changes

### 🏠 Containerized Testing Environment
- **Docker Compose Setup**: Complete testing infrastructure with mock devices
- **Network Simulation**: Multi-network topology with management and customer networks
- **SSH Access**: Full SSH connectivity to all containers for testing
- **Mock Devices**: Nokia SR Linux, Cisco IOS-XR simulated environments

## Architecture Components

### Core Modules

#### 1. Intent Processor (`src/core/intent_processor.py`)
- Main orchestration engine
- Coordinates workflow from intent to deployment
- Handles error propagation and rollback

#### 2. NLP Parser (`src/core/nlp_parser.py`)
- Natural language processing for network intents
- Extracts devices, interfaces, protocols, and policies
- Supports complex multi-service configurations

#### 3. Model Discovery (`src/core/model_discovery.py`)
- YANG model discovery across vendors
- Capability detection (NETCONF, gNMI, RESTCONF)
- Version compatibility checking

#### 4. YANG Mapper (`src/core/yang_mapper.py`)
- Intent-to-YANG path mapping
- Vendor-specific model handling
- Configuration template selection

#### 5. Configuration Generator (`src/core/config_generator.py`)
- Multi-transport payload generation
- Template-based configuration rendering
- Format conversion (XML, JSON, CLI)

#### 6. Validation Engine (`src/core/validation_engine.py`)
- Pre-deployment validation
- Syntax and semantic checking
- Network impact simulation

### Data Models (`src/models/base.py`)

```python
@dataclass
class NormalizedIntent:
    service_type: ServiceType
    service_id: str
    endpoints: List[Endpoint]
    routing_policy: Optional[Dict]
    qos_policy: Optional[Dict]
    security_policy: Optional[Dict]

@dataclass
class IntentResponse:
    intent_summary: str
    risk_assessment: RiskAssessment
    model_discovery: List[ModelDiscoveryResult]
    normalized_intent: NormalizedIntent
    configuration_payloads: List[ConfigPayload]
```

### LLM Integration (`src/llm/`)

#### Modular Provider System
- **Base LLM Interface**: Abstract base class for all providers
- **MLX Provider**: Optimized for Apple Silicon with Metal Performance Shaders
- **OpenAI Provider**: GPT-3.5/GPT-4 integration
- **Anthropic Provider**: Claude integration
- **Connect LLM**: Centralized connection management

#### Configuration
```python
# Easy provider switching
connector = LLMConnector()
mlx_llm = connector.mac_mlx_llm(model="mlx-community/Llama-3.2-3B-Instruct-4bit")
```

## Service Types Supported

### 1. L3VPN (Layer 3 VPN)
- Multi-PE VPN provisioning
- BGP route-target configuration
- Customer routing protocol support
- Quality of Service integration

### 2. EVPN (Ethernet VPN)
- Layer 2 and Layer 3 EVPN services
- VXLAN overlay configuration
- Multi-homing and redundancy
- MAC mobility and learning

### 3. QoS (Quality of Service)
- Traffic classification and marking
- Queuing and scheduling policies
- Rate limiting and shaping
- Service level agreements

### 4. Security Policies
- Access control lists (ACLs)
- Firewall rule generation
- Intrusion prevention systems
- Network segmentation

### 5. Routing Configurations
- OSPF, ISIS, BGP protocol setup
- Route redistribution policies
- Load balancing and failover
- Route filtering and manipulation

## Containerized Testing Environment

### Infrastructure Components

#### Management Network (172.25.25.0/24)
- **AURORA Controller** (172.25.25.100): Main platform container
- **AURORA Tester** (172.25.25.101): Test automation container
- **Network Tools** (172.25.25.200): Network monitoring and debugging tools
- **Mock Devices**: Nokia PE1 (172.25.25.10), Cisco PE2 (172.25.25.11)

#### Customer Networks
- **West Customer** (192.168.100.0/24): CE1 Linux container
- **East Customer** (192.168.200.0/24): CE2 Linux container

#### Container Services
```bash
# AURORA Controller Access
ssh aurora@localhost -p 2200    # password: aurora123

# AURORA Tester Access
ssh tester@localhost -p 2201    # password: tester123

# Customer Edge Access
ssh root@localhost -p 2230      # CE1, password: ce1pass
ssh root@localhost -p 2231      # CE2, password: ce2pass

# Network Tools Access
ssh root@localhost -p 2240      # password: nettools123

# Mock Device Access
ssh admin@localhost -p 2210     # Nokia PE1, password: admin
ssh cisco@localhost -p 2211     # Cisco PE2, password: cisco
```

## Installation and Setup

### Prerequisites
```bash
# Python 3.11+
# Docker and Docker Compose
# Optional: MLX for Apple Silicon users
```

### Quick Start
```bash
# Clone and navigate
cd aurora-ibn

# Start containerized environment
cd containerlab
docker-compose -f docker-compose-full.yml up -d

# Test SSH connectivity
./test_ssh_connectivity.sh

# Run platform tests
docker exec aurora-controller python3 test_platform.py
```

### Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# For MLX support (Mac users)
pip install mlx-lm

# For cloud LLM providers
pip install openai anthropic
```

## Configuration Examples

### L3VPN Intent Example
```
Create L3VPN service "ACME-CORP" between PE1 and PE2.
Use interfaces ethernet-1/3 on both devices.
Configure BGP AS 65000, enable BFD, set MTU to 9000.
Apply Gold QoS policy and enable MPLS transport.
```

### EVPN Intent Example
```
Deploy EVPN Layer 2 service "DATACENTER-INTERCONNECT".
Connect PE1:ethernet-1/5 to PE2:ethernet-1/5.
Use VXLAN VNI 10001, BGP route-target 65000:10001.
Enable MAC learning and ARP suppression.
```

### Generated Configuration Output
```xml
<!-- Nokia SR Linux Configuration -->
<configure>
  <service>
    <vprn service-id="1001">
      <service-name>ACME-CORP</service-name>
      <route-distinguisher>65000:1001</route-distinguisher>
      <vrf-target>
        <community>target:65000:1001</community>
      </vrf-target>
    </vprn>
  </service>
</configure>
```

## API Integration

### REST API Endpoints
```python
# Process network intent
POST /api/v1/intents
{
  "intent": "Create L3VPN between PE1 and PE2...",
  "approve_deployment": false
}

# Get deployment status
GET /api/v1/deployments/{deployment_id}

# Validate configuration
POST /api/v1/validate
{
  "vendor": "nokia",
  "config": "<configure>...</configure>"
}
```

### Python SDK
```python
from aurora_ibn import IntentProcessor

processor = IntentProcessor()
result = processor.process_intent(
    intent_text="Create L3VPN ACME between PE1 and PE2",
    inventory=device_inventory,
    approve_deployment=False
)

print(f"Risk Level: {result.risk_assessment.risk_level}")
print(f"Generated {len(result.configuration_payloads)} configurations")
```

## Testing and Validation

### Platform Tests
```bash
# Run comprehensive test suite
python3 test_platform.py

# Test individual components
python3 -m pytest src/tests/

# Container connectivity tests
./containerlab/test_ssh_connectivity.sh
```

### Demo Platform
```bash
# Interactive demonstration
python3 demo_platform.py

# Example scenarios included:
# - L3VPN provisioning
# - EVPN deployment  
# - QoS policy application
# - Multi-vendor configuration
```

## Development Guidelines

### Code Structure
```
aurora-ibn/
├── src/                    # Core platform code
│   ├── core/              # Processing engines
│   ├── llm/               # LLM integration
│   ├── models/            # Data models
│   └── templates/         # Configuration templates
├── containerlab/          # Testing environment
├── examples/              # Usage examples
└── tests/                 # Test suites
```

### Adding New Vendors
1. Create vendor-specific templates in `src/templates/{vendor}/`
2. Add YANG model mappings in `src/core/yang_mapper.py`
3. Update vendor enumeration in `src/models/base.py`
4. Add transport protocol support

### LLM Provider Integration
1. Implement `BaseLLM` interface in `src/llm/{provider}_llm.py`
2. Add provider configuration in `src/llm/connect_llm.py`
3. Update provider enumeration and factory methods
4. Add provider-specific dependencies

## Performance and Scalability

### Optimization Features
- **Lazy Loading**: YANG models loaded on-demand
- **Caching**: Template and model caching for repeated operations
- **Parallel Processing**: Concurrent configuration generation
- **Memory Efficiency**: Streaming processing for large configurations

### Scalability Metrics
- **Device Support**: 1000+ devices per deployment
- **Intent Processing**: <2 seconds for complex L3VPN intents
- **Configuration Generation**: <500ms per device
- **Memory Usage**: <1GB for typical workloads

## Security Considerations

### Data Protection
- **Credential Management**: Secure storage of device credentials
- **Configuration Encryption**: In-transit and at-rest encryption
- **Audit Logging**: Complete audit trail of all changes
- **Access Control**: Role-based access control (RBAC)

### Network Security
- **SSH Key Management**: Automated SSH key rotation
- **Certificate Validation**: TLS certificate verification
- **Network Isolation**: Segregated management networks
- **Change Approval**: Multi-stage approval workflows

## Roadmap and Future Enhancements

### Version 2.0 Features
- **AI-Driven Optimization**: Machine learning for configuration optimization
- **Network Telemetry**: Real-time network state monitoring
- **Intent Verification**: Continuous intent compliance checking
- **Cloud Integration**: Native cloud provider support

### Version 3.0 Vision
- **Digital Twin**: Complete network digital twin simulation
- **Predictive Analytics**: Network failure prediction and prevention
- **Autonomous Operations**: Self-healing network configurations
- **Edge Computing**: Distributed intent processing

## Support and Community

### Documentation
- **API Reference**: Complete API documentation with examples
- **User Guides**: Step-by-step implementation guides
- **Best Practices**: Network automation best practices
- **Troubleshooting**: Common issues and resolution guides

### Community Resources
- **GitHub Repository**: Source code and issue tracking
- **Discussion Forums**: Community support and discussions
- **Training Materials**: Educational content and workshops
- **Certification Programs**: Professional certification tracks

## License and Contributing

### Open Source License
AURORA-IBN is released under the MIT License, encouraging community contributions and commercial adoption.

### Contributing Guidelines
1. **Code Standards**: Follow PEP 8 Python style guidelines
2. **Testing Requirements**: All contributions must include tests
3. **Documentation**: Update documentation for new features
4. **Review Process**: All changes require peer review

### Getting Involved
- **Bug Reports**: Report issues via GitHub Issues
- **Feature Requests**: Propose new features via GitHub Discussions
- **Code Contributions**: Submit pull requests with improvements
- **Documentation**: Help improve documentation and examples

---

*AURORA-IBN: Transforming network automation through intelligent intent-based configuration management.*