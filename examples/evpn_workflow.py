#!/usr/bin/env python3
"""
AURORA-IBN EVPN Workflow Example  
Demonstrates EVPN VPWS E-Line service provisioning
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
    
    # Initialize LLM with OpenAI (alternative to MLX)
    llm_connector = create_llm_connector(
        provider='openai',
        model='gpt-4o-mini',
        temperature=0.1
    )
    llm_provider = llm_connector.get_provider()
    
    print("🌐 AURORA-IBN EVPN Workflow Example")
    print(f"📡 Using {llm_provider.provider_name} with model: {llm_connector.config.model}")
    print()
    
    # Initialize intent processor
    processor = IntentProcessor()
    
    # EVPN E-Line service intent
    intent_text = """
    Provision an EVPN VPWS E-Line service between sites.
    Connect PE-J1 interface xe-0/0/5 to PE-H1 interface 10GE1/0/5.
    Use VLAN 200 for customer traffic encapsulation.
    Service should support multihoming and fast convergence with BFD.
    Configure EVI 200 with automatic RT assignment.
    Ensure symmetric IRB is not required for this point-to-point service.
    Customer: DataCenter Corp, Service Level: Gold (99.9% uptime).
    """
    
    # Multi-vendor inventory (Juniper + Huawei)
    inventory = [
        {
            'device_id': 'PE-J1',
            'hostname': 'pe-j1.dc.corp',
            'vendor': 'juniper', 
            'os_version': 'Junos 21.4R1',
            'mgmt_ip': '10.1.1.10',
            'bgp_asn': '65001',
            'netconf_enabled': True,
            'netconf_port': 830,
            'interfaces': ['xe-0/0/5', 'xe-0/0/6'],
            'site': 'dc-west'
        },
        {
            'device_id': 'PE-H1',
            'hostname': 'pe-h1.dc.corp', 
            'vendor': 'huawei',
            'os_version': 'VRP V800R012C00',
            'mgmt_ip': '10.1.1.11',
            'bgp_asn': '65001',
            'netconf_enabled': True,
            'netconf_port': 830,
            'interfaces': ['10GE1/0/5', '10GE1/0/6'],
            'site': 'dc-east'
        },
        {
            'device_id': 'RR1',
            'hostname': 'rr1.dc.corp',
            'vendor': 'cisco',
            'os_version': 'IOS-XR 7.5.1',
            'mgmt_ip': '10.1.1.12',
            'bgp_asn': '65001',
            'role': 'route-reflector',
            'netconf_enabled': True
        }
    ]
    
    # Stringent policy for critical service
    policy = {
        'service_class': 'gold',
        'maintenance_window': {
            'start': '2024-01-20T03:00:00Z',
            'duration_min': 45
        },
        'rollback_timeout': 5,  # Fast rollback for critical service
        'validation_required': True,
        'confirmation_required': True,
        'change_approval': 'required',
        'backup_required': True,
        'performance_baseline': True
    }
    
    # Optional telemetry hints (simulated current state)
    telemetry_hint = {
        'interfaces': {
            'PE-J1': {
                'xe-0/0/5': {'status': 'up', 'mtu': 1500, 'vlan': None},
                'xe-0/0/6': {'status': 'down', 'mtu': 1500, 'vlan': None}
            },
            'PE-H1': {
                '10GE1/0/5': {'status': 'up', 'mtu': 1500, 'vlan': None},
                '10GE1/0/6': {'status': 'up', 'mtu': 1500, 'vlan': 100}
            }
        },
        'bgp_sessions': {
            'established': 4,
            'evpn_neighbors': 2
        }
    }
    
    print("📋 EVPN Service Request")
    print(f"Intent: EVPN VPWS E-Line between {inventory[0]['site']} and {inventory[1]['site']}")
    print(f"Devices: {len(inventory)} devices ({inventory[0]['vendor']}, {inventory[1]['vendor']}, {inventory[2]['vendor']})")
    print(f"Service Class: {policy['service_class'].upper()}")
    print(f"VLAN: 200, EVI: 200")
    print()
    
    # Process the intent
    print("🧠 Processing EVPN Intent...")
    try:
        result_json = processor.process_intent(
            intent_text=intent_text,
            inventory=inventory,
            policy=policy,
            telemetry_hint=telemetry_hint
        )
        
        result = json.loads(result_json)
        
        # Enhanced result display for EVPN
        print("✅ EVPN Intent Processing Complete")
        print()
        
        # Risk assessment with EVPN-specific considerations
        print("🚨 Risk Assessment")
        risk = result.get('risk_assessment', {})
        risk_level = risk.get('level', 'UNKNOWN')
        risk_color = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🔴'}.get(risk_level, '⚪')
        print(f"Risk Level: {risk_color} {risk_level}")
        
        if risk.get('factors'):
            print("Risk Factors:")
            for factor in risk['factors']:
                print(f"  ⚠️  {factor}")
        
        if risk.get('mitigations'):
            print("Mitigations:")
            for mitigation in risk['mitigations']:
                print(f"  🛡️  {mitigation}")
        print()
        
        # Model discovery with vendor-specific details
        print("🔍 YANG Model Discovery")
        for discovery in result.get('model_discovery', []):
            vendor_emoji = {
                'juniper': '🌿',
                'huawei': '🏢', 
                'cisco': '🔧'
            }.get(discovery['target'].split('-')[1][0].lower(), '📡')
            
            print(f"{vendor_emoji} Device: {discovery['target']}")
            print(f"   Transport: {discovery['transport']}")
            print(f"   Models: {len(discovery['models_found'])} found")
            print(f"   Source: {discovery['source']}")
            
            if discovery.get('gaps'):
                print(f"   ⚠️  Gaps: {', '.join(discovery['gaps'])}")
        print()
        
        # Service-specific normalization details
        print("🎯 EVPN Service Normalization")
        normalized = result.get('normalized_intent', {})
        print(f"Service Type: {normalized.get('service_type', '').upper()}")
        
        endpoints = normalized.get('endpoints', [])
        print(f"Endpoints: {len(endpoints)}")
        for i, ep in enumerate(endpoints):
            print(f"  {i+1}. {ep['device']} - {ep['interface']} {ep.get('tags', [])}")
        
        if normalized.get('slo'):
            slo = normalized['slo']
            print(f"SLO Requirements:")
            if slo.get('latency_ms'):
                print(f"  • Latency: <{slo['latency_ms']}ms")
            if slo.get('loss_pct'):
                print(f"  • Packet Loss: <{slo['loss_pct']}%")
        print()
        
        # Vendor-specific configuration mappings
        print("🗺️ Vendor Configuration Mappings")
        for mapping in result.get('mapping_table', []):
            vendor_name = mapping['vendor'].upper()
            print(f"{vendor_name} ({mapping['os_version']})")
            print(f"  YANG Paths: {len(mapping['yang_paths'])}")
            
            # Show some key paths
            paths = mapping['yang_paths'][:3]
            for path in paths:
                print(f"    • {path}")
            if len(mapping['yang_paths']) > 3:
                print(f"    • ... and {len(mapping['yang_paths'])-3} more")
            
            if mapping.get('notes'):
                print(f"  📝 Notes: {mapping['notes']}")
        print()
        
        # Configuration payload details
        print("📦 Configuration Payloads")
        payloads = result.get('candidate_payloads', [])
        total_size = sum(len(p['payload']) for p in payloads)
        
        print(f"Generated: {len(payloads)} payloads, {total_size:,} total characters")
        
        for payload in payloads:
            transport_emoji = {'NETCONF': '🔌', 'RESTCONF': '🌐', 'gNMI': '📡'}.get(payload['transport'], '📄')
            print(f"{transport_emoji} {payload['target']}")
            print(f"   Transport: {payload['transport']} ({payload['payload_type']})")
            print(f"   Size: {len(payload['payload']):,} chars")
            print(f"   Prechecks: {len(payload.get('prechecks', []))}")
            print(f"   Post-validation: {len(payload.get('post_validation', []))}")
        print()
        
        # Deployment strategy
        print("🚀 Deployment Strategy")
        commit_plan = result.get('commit_plan', {})
        print(f"Strategy: {commit_plan.get('strategy', 'Unknown')}")
        print(f"Batching: {commit_plan.get('batching', 'Unknown')}")
        
        rollback = commit_plan.get('rollback', {})
        if rollback:
            method = rollback.get('method', 'Unknown')
            timeout = rollback.get('timeout_seconds', 'N/A')
            print(f"Rollback: {method} ({timeout}s timeout)")
        
        maint_window = commit_plan.get('maintenance_window')
        if maint_window:
            print(f"Maintenance: {maint_window}")
        print()
        
        # Comprehensive verification
        print("✅ Service Verification Plan")
        verification = result.get('verification_plan', {})
        
        tests = verification.get('tests', [])
        evpn_tests = [t for t in tests if 'evpn' in t.lower() or 'mac' in t.lower()]
        connectivity_tests = [t for t in tests if 'ping' in t.lower() or 'connectivity' in t.lower()]
        
        print(f"📋 Total Tests: {len(tests)}")
        
        if evpn_tests:
            print("🌐 EVPN-Specific Tests:")
            for test in evpn_tests[:3]:
                print(f"   • {test}")
        
        if connectivity_tests:
            print("🔗 Connectivity Tests:")
            for test in connectivity_tests[:2]:
                print(f"   • {test}")
        
        telemetry = verification.get('telemetry_queries', [])
        print(f"📊 Telemetry Queries: {len(telemetry)}")
        print()
        
        # Audit and compliance
        print("📋 Audit & Compliance")
        audit = result.get('audit_log', {})
        print(f"Timestamp: {audit.get('timestamp')}")
        print(f"Model Sources: {', '.join(audit.get('sources', []))}")
        
        hashes = audit.get('hashes', {})
        print(f"Configuration Hashes: {len(hashes)} generated for integrity verification")
        print()
        
        # Save results with EVPN-specific naming
        output_file = Path(__file__).parent / "evpn_vpws_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Generate summary report
        summary_file = Path(__file__).parent / "evpn_summary.md"
        with open(summary_file, 'w') as f:
            f.write("# EVPN VPWS E-Line Service Summary\n\n")
            f.write(f"**Service Type:** EVPN VPWS E-Line\n")
            f.write(f"**Risk Level:** {risk_level}\n")
            f.write(f"**Devices:** {len(inventory)} ({', '.join(d['vendor'] for d in inventory)})\n")
            f.write(f"**Generated Payloads:** {len(payloads)}\n")
            f.write(f"**Verification Tests:** {len(tests)}\n\n")
            f.write("## Next Steps\n")
            f.write("1. Obtain change approval for Gold service\n")
            f.write("2. Schedule maintenance window\n") 
            f.write("3. Execute pre-change verification\n")
            f.write("4. Deploy configurations with confirmed commit\n")
            f.write("5. Run post-deployment verification\n")
            f.write("6. Update service inventory\n")
        
        print(f"💾 Results saved to: {output_file}")
        print(f"📄 Summary report: {summary_file}")
        print()
        print("🎉 EVPN Workflow Complete!")
        print()
        print("🚀 Ready for deployment with comprehensive safety measures")
        
    except Exception as e:
        print(f"❌ Error processing EVPN intent: {e}")
        logging.exception("EVPN intent processing failed")


if __name__ == "__main__":
    asyncio.run(main())