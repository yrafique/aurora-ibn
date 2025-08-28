# AURORA-IBN ContainerLab Testbed

This directory contains a comprehensive ContainerLab testbed for validating the AURORA-IBN platform with real network devices.

## Testbed Architecture

```
                    ┌─────────────────┐
                    │  AURORA-IBN     │
                    │  Controller     │
                    │  172.20.20.100  │
                    └─────────────────┘
                             │
                    ┌─────────────────┐
                    │ Management      │
                    │ Network         │
                    │ 172.20.20.0/24  │
                    └─────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │  PE1    │         │   P1    │         │  PE2    │
   │ SRLinux │◄────────┤ SRLinux ├────────►│ SRLinux │
   │.10:830  │         │.20:835  │         │.11:831  │
   └────┬────┘         └────┬────┘         └────┬────┘
        │                   │                   │
        │              ┌────▼────┐              │
        │              │  RR1    │              │
        │              │ cEOS    │              │
        │              │.21:834  │              │
        │              └─────────┘              │
        │                                       │
   ┌────▼────┐                             ┌────▼────┐
   │  CE1    │                             │  CE2    │
   │ Linux   │                             │ Linux   │
   │.30      │                             │.31      │
   └─────────┘                             └─────────┘
```

## Components

### Network Devices
- **PE1/PE2**: Nokia SR Linux Provider Edge routers
- **P1**: Nokia SR Linux Provider core router  
- **RR1**: Arista cEOS Route Reflector (planned)
- **CE1/CE2**: Alpine Linux Customer Edge devices

### AURORA-IBN Platform
- **Controller**: Python container with AURORA-IBN platform
- **Tester**: Automated test runner

## Quick Start

### Option 1: Using ContainerLab (Recommended)

1. **Install ContainerLab** (requires sudo):
   ```bash
   curl -sL https://get.containerlab.dev | sudo bash
   ```

2. **Deploy testbed**:
   ```bash
   cd containerlab
   sudo containerlab deploy -t aurora-testbed.yml
   ```

3. **Run tests**:
   ```bash
   python3 test-runner.py
   ```

4. **Cleanup**:
   ```bash
   sudo containerlab destroy -t aurora-testbed.yml
   ```

### Option 2: Using Docker Compose (Alternative)

1. **Start testbed**:
   ```bash
   cd containerlab
   docker-compose up -d
   ```

2. **Run tests**:
   ```bash
   docker-compose exec aurora-tester python test-runner.py --quick
   ```

3. **Cleanup**:
   ```bash
   docker-compose down -v
   ```

## Testing Scenarios

### 1. Model Discovery Test
- Connects to all PE devices via NETCONF
- Discovers available YANG models
- Tests model caching and fallback mechanisms

### 2. Intent Processing Test
```python
intent = """
Create L3VPN TESTLAB-ACME between PE1 and PE2.
Use ethernet-1/3 interfaces for customer connections.
Configure BGP AS 65000, enable BFD, MTU 9000.
"""
```

### 3. Configuration Generation Test  
- Generates Nokia SR Linux NETCONF XML
- Validates YANG model compliance
- Tests multi-vendor normalization

### 4. Validation Engine Test
- Dry-run configuration validation
- Rollback mechanism testing  
- Post-deployment verification

## Device Access

### NETCONF Ports
- PE1: localhost:830
- PE2: localhost:831  
- P1: localhost:835

### Default Credentials
- Username: `admin`
- Password: `admin`

### Management Access
- Controller UI: http://localhost:8080
- API: http://localhost:8000
- Jupyter: http://localhost:8888

## Test Results

Results are stored in `test-results/`:
- `validation_test_results.json`: Overall test summary
- `model_discovery_results.json`: YANG model discovery details
- `connectivity_test_results.json`: Device connectivity status
- `intent_processing_results.json`: Intent processing output
- `AURORA_IBN_Test_Report.md`: Human-readable summary

## Available Test Commands

```bash
# Full test suite
python3 test-runner.py

# Quick connectivity test only  
python3 test-runner.py --quick

# Keep testbed running after tests
python3 test-runner.py --no-cleanup

# Manual device access
docker exec -it clab-aurora-pe1-srlinux sr_cli
docker exec -it clab-aurora-controller bash
```

## Troubleshooting

### Device Not Ready
- Check container logs: `docker logs clab-aurora-pe1-srlinux`
- Wait longer for device boot (60-120 seconds)
- Verify network connectivity: `docker network ls`

### NETCONF Connection Failed
- Ensure NETCONF is enabled in device configs
- Check port mappings: `docker ps`
- Test with manual SSH: `ssh admin@172.20.20.10 -p 830 -s netconf`

### Tests Failing
- Check Python dependencies in controller container
- Verify AURORA-IBN source code is mounted correctly
- Review test logs in `test-results/`

## Advanced Usage

### Adding New Vendors
1. Add device to `aurora-testbed.yml`
2. Create startup config in `configs/`
3. Update inventory in `test-runner.py`
4. Add vendor-specific YANG mappings

### Custom Intents
```bash
# Edit test-runner.py and modify intent_text
intent_text = """
Your custom network intent here...
"""
```

### Live Configuration Deployment
```bash
# Connect to controller
docker exec -it clab-aurora-controller bash

# Run live deployment
cd examples
python3 l3vpn_workflow.py
```

## Platform Validation

This testbed validates:
- ✅ Multi-vendor YANG model discovery
- ✅ Intent parsing and normalization  
- ✅ Configuration generation (Nokia SR Linux)
- ✅ NETCONF client connectivity
- ✅ Risk assessment and safety mechanisms
- ✅ Validation engine functionality
- 🚧 Live configuration deployment (partial)
- 🚧 Service verification (planned)
- 🚧 Rollback mechanisms (planned)

## Next Steps

1. **Add Arista cEOS support** (requires cEOS image)
2. **Implement live configuration deployment**
3. **Add service verification tests**  
4. **Scale to larger topologies**
5. **Add performance benchmarking**

## Requirements

- Docker & Docker Compose
- ContainerLab (optional but recommended)
- 4GB+ RAM for full testbed
- Network vendor container images (Nokia SR Linux is public)

For questions or issues, check the main AURORA-IBN documentation.