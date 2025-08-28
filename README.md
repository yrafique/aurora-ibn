# AURORA-IBN: Intent-Based Networking Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

## Overview

AURORA-IBN (Aurora Intent-Based Networking) is a comprehensive, multi-vendor network automation platform that translates natural language intents into vendor-specific network configurations. The platform leverages Large Language Models (LLMs), YANG model discovery, and advanced configuration generation to enable seamless network service provisioning.

## 🚀 Key Features

- **Natural Language Processing**: Convert plain English intents to network configurations
- **Multi-Vendor Support**: Nokia, Cisco, Juniper, Huawei, Arista
- **LLM Integration**: Modular support for MLX (Mac Silicon), OpenAI, Anthropic
- **Service Types**: L3VPN, EVPN, QoS, Security, Routing
- **Risk Assessment**: Pre-deployment validation and rollback mechanisms
- **Containerized Testing**: Complete Docker-based testing environment

## 📋 Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd aurora-ibn

# Start containerized environment
cd containerlab
docker-compose -f docker-compose-full.yml up -d

# Test connectivity
./test_ssh_connectivity.sh

# Run platform tests
docker exec aurora-controller python3 test_platform.py
```

## 🏗️ Architecture

```
aurora-ibn/
├── src/                    # Core platform code
│   ├── core/              # Processing engines
│   ├── llm/               # LLM integration (modular)
│   ├── models/            # Data models
│   └── templates/         # Configuration templates
├── containerlab/          # Testing environment
├── examples/              # Usage examples
└── tests/                 # Test suites
```

## 💡 Example Usage

```python
from aurora_ibn import IntentProcessor

processor = IntentProcessor()
result = processor.process_intent(
    intent_text="Create L3VPN ACME between PE1 and PE2 with BGP AS 65000",
    inventory=device_inventory,
    approve_deployment=False
)

print(f"Risk Level: {result.risk_assessment.risk_level}")
print(f"Generated {len(result.configuration_payloads)} configurations")
```

## 🔧 Container Access

```bash
# AURORA Controller
ssh aurora@localhost -p 2200    # password: aurora123

# Test Environment
ssh tester@localhost -p 2201    # password: tester123

# Customer Edge Devices
ssh root@localhost -p 2230      # CE1, password: ce1pass
ssh root@localhost -p 2231      # CE2, password: ce2pass

# Network Tools
ssh root@localhost -p 2240      # password: nettools123
```

## 📚 Documentation

See [CLAUDE.md](CLAUDE.md) for complete project documentation including:
- Detailed architecture overview
- API reference
- Development guidelines
- Security considerations
- Roadmap and future enhancements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with modern Python and containerization best practices
- Supports multiple LLM providers for flexibility
- Designed for enterprise network automation at scale

---

*Transform your network operations with intelligent intent-based automation.*