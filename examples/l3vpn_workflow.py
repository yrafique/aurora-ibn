#!/usr/bin/env python3
"""
AURORA-IBN L3VPN Workflow Example
Demonstrates complete L3VPN provisioning workflow
"""

import asyncio
import json
import logging
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from src.core.intent_processor import IntentProcessor
from src.llm.connect_llm import create_llm_connector


async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Initialize LLM connector with MLX on Mac
    llm_connector = create_llm_connector(provider='mlx')
    llm_provider = llm_connector.mac_mlx_llm(
        model="mlx-community/Llama-3.2-3B-Instruct-4bit",
        temperature=0.1
    )
    
    print("🚀 AURORA-IBN L3VPN Workflow Example")
    print(f"📡 Using {llm_provider.provider_name} with model: {llm_connector.config.model}")
    print()
    
    # Initialize intent processor
    processor = IntentProcessor()
    
    # Example L3VPN intent
    intent_text = """
    Create an L3VPN called ACME between PE1 and PE2.
    PE1 should use interface GigabitEthernet0/0/1 and PE2 should use GigabitEthernet0/0/2.
    Configure BGP AS 65000, enable BFD for fast convergence.
    Use route distinguisher and route target auto-assignment.
    Set MTU to 9000 bytes and ensure latency is under 20ms.
    This is for customer ACME Corp with RFC1918 addressing only.
    """
    
    # Example inventory
    inventory = [
        {
            'device_id': 'PE1',
            'hostname': 'pe1.acme.net',
            'vendor': 'cisco',
            'os_version': 'IOS-XR 7.3.2',
            'mgmt_ip': '192.168.1.10',
            'bgp_asn': '65000',
            'netconf_enabled': True,
            'netconf_port': 830,
            'username': 'admin',
            'password': 'admin123'
        },
        {
            'device_id': 'PE2', 
            'hostname': 'pe2.acme.net',
            'vendor': 'nokia',
            'os_version': 'SR OS 21.7.R1',
            'mgmt_ip': '192.168.1.11',
            'bgp_asn': '65000',
            'service_id': '100',
            'netconf_enabled': True,
            'netconf_port': 830,
            'username': 'admin',
            'password': 'admin123'
        }
    ]
    
    # Policy constraints
    policy = {
        'maintenance_window': {
            'start': '2024-01-15T02:00:00Z',
            'duration_min': 30
        },
        'rollback_timeout': 10,
        'validation_required': True,
        'confirmation_required': True
    }
    
    print("📋 Intent Analysis")
    print(f"Intent: {intent_text[:100]}...")
    print(f"Devices: {len(inventory)} devices")
    print(f"Policy: Maintenance window required, rollback in {policy['rollback_timeout']} min")
    print()
    
    # Process the intent
    print("🧠 Processing Intent...")
    try:
        result_json = processor.process_intent(
            intent_text=intent_text,
            inventory=inventory,
            policy=policy
        )
        
        result = json.loads(result_json)
        
        # Display results
        print("✅ Intent Processing Complete")
        print()
        
        print("📊 Risk Assessment")
        risk = result.get('risk_assessment', {})
        print(f"Risk Level: {risk.get('level', 'UNKNOWN')}")
        if risk.get('factors'):
            print("Risk Factors:")
            for factor in risk['factors']:
                print(f"  • {factor}")
        if risk.get('mitigations'):
            print("Mitigations:")
            for mitigation in risk['mitigations']:
                print(f"  • {mitigation}")
        print()
        
        print("🔍 Model Discovery")
        for discovery in result.get('model_discovery', []):
            print(f"Device: {discovery['target']}")
            print(f"  Transport: {discovery['transport']}")
            print(f"  Models: {len(discovery['models_found'])} found")
            print(f"  Source: {discovery['source']}")
            if discovery.get('gaps'):
                print(f"  Gaps: {', '.join(discovery['gaps'])}")
        print()
        
        print("🎯 Normalized Intent")
        normalized = result.get('normalized_intent', {})
        print(f"Service Type: {normalized.get('service_type')}")
        print(f"Endpoints: {len(normalized.get('endpoints', []))}")
        if normalized.get('slo'):
            slo = normalized['slo']
            print(f"SLO: {slo.get('latency_ms')}ms latency")
        print()
        
        print("🗺️ YANG Mappings")
        for mapping in result.get('mapping_table', []):
            print(f"Vendor: {mapping['vendor']}")
            print(f"  OS Version: {mapping['os_version']}")
            print(f"  YANG Paths: {len(mapping['yang_paths'])}")
            if mapping.get('notes'):
                print(f"  Notes: {mapping['notes']}")
        print()
        
        print("📦 Generated Payloads")
        payloads = result.get('candidate_payloads', [])
        for payload in payloads:
            print(f"Target: {payload['target']}")
            print(f"  Transport: {payload['transport']}")
            print(f"  Type: {payload['payload_type']}")
            print(f"  Size: {len(payload['payload'])} chars")
            print(f"  Prechecks: {len(payload.get('prechecks', []))}")
        print()
        
        print("🚀 Commit Strategy")
        commit_plan = result.get('commit_plan', {})
        print(f"Strategy: {commit_plan.get('strategy')}")
        print(f"Batching: {commit_plan.get('batching')}")
        rollback = commit_plan.get('rollback', {})
        if rollback:
            print(f"Rollback: {rollback.get('method')} ({rollback.get('timeout_seconds', 'N/A')}s)")
        print()
        
        print("✅ Verification Plan")
        verification = result.get('verification_plan', {})
        tests = verification.get('tests', [])
        print(f"Tests: {len(tests)} planned")
        for i, test in enumerate(tests[:3]):  # Show first 3
            print(f"  {i+1}. {test}")
        if len(tests) > 3:
            print(f"  ... and {len(tests)-3} more tests")
        
        telemetry = verification.get('telemetry_queries', [])
        print(f"Telemetry Queries: {len(telemetry)} planned")
        print()
        
        print("📋 Audit Trail")
        audit = result.get('audit_log', {})
        print(f"Timestamp: {audit.get('timestamp')}")
        print(f"Sources: {', '.join(audit.get('sources', []))}")
        hashes = audit.get('hashes', {})
        print(f"Payload Hashes: {len(hashes)} generated")
        print()
        
        # Save detailed result
        output_file = Path(__file__).parent / "l3vpn_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 Detailed results saved to: {output_file}")
        print()
        print("🎉 L3VPN Workflow Complete!")
        print()
        print("Next steps:")
        print("1. Review risk assessment and mitigations")
        print("2. Schedule maintenance window")
        print("3. Execute configurations with validation")
        print("4. Run verification tests")
        print("5. Confirm commits or rollback if needed")
        
    except Exception as e:
        print(f"❌ Error processing intent: {e}")
        logging.exception("Intent processing failed")


if __name__ == "__main__":
    asyncio.run(main())