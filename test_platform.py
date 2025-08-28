#!/usr/bin/env python3
"""
Simple AURORA-IBN Platform Test
Tests core functionality without ContainerLab/network devices
"""

import sys
import json
import logging
from pathlib import Path

# Add src to path  
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_platform_imports():
    """Test that all core modules can be imported"""
    
    print("🧪 Testing AURORA-IBN Platform Imports...")
    
    try:
        # Test data models
        from models.base import (
            IntentResponse, NormalizedIntent, ServiceType, 
            Vendor, Transport, RiskLevel
        )
        print("✅ Data models imported successfully")
        
        # Test LLM interface
        from llm.base_llm import BaseLLM, LLMMessage, LLMResponse
        from llm.connect_llm import LLMConnector, create_llm_connector
        print("✅ LLM interface imported successfully")
        
        # Test core processors (mock test since LLM might not be available)
        from core.nlp_parser import NLPParser
        from core.yang_mapper import YANGMapper
        from core.config_generator import ConfigGenerator
        
        print("✅ Core processors imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_nlp_parsing():
    """Test NLP intent parsing"""
    
    print("\n🧠 Testing NLP Intent Parsing...")
    
    try:
        from core.nlp_parser import NLPParser
        
        parser = NLPParser()
        
        intent_text = """
        Create L3VPN ACME between PE1 and PE2.
        Use interfaces GigabitEthernet0/0/1 and GigabitEthernet0/0/2.
        Configure BGP AS 65000, enable BFD, set MTU to 9000.
        """
        
        result = parser.parse(intent_text)
        
        print(f"✅ Parsed intent successfully")
        print(f"  - Devices found: {result['devices']}")
        print(f"  - Interfaces found: {result['interfaces']}")
        print(f"  - Protocols found: {result['protocols']}")
        print(f"  - Policy extracted: {result['policy']}")
        
        return True
        
    except Exception as e:
        print(f"❌ NLP parsing test failed: {e}")
        return False

def test_yang_mapping():
    """Test YANG model mapping"""
    
    print("\n🗺️ Testing YANG Model Mapping...")
    
    try:
        from core.yang_mapper import YANGMapper
        from models.base import NormalizedIntent, ServiceType, Vendor, Endpoint
        
        mapper = YANGMapper()
        
        # Create mock intent
        intent = NormalizedIntent(
            service_type=ServiceType.L3VPN,
            endpoints=[
                Endpoint(device="PE1", interface="eth1", tags=["pe"]),
                Endpoint(device="PE2", interface="eth1", tags=["pe"])
            ]
        )
        
        # Mock inventory
        inventory = [
            {"vendor": "nokia", "os_version": "SR OS 21.7"},
            {"vendor": "cisco", "os_version": "IOS-XR 7.3"}
        ]
        
        mappings = mapper.create_mappings(intent, [], inventory)
        
        print(f"✅ YANG mappings created successfully")
        print(f"  - Generated {len(mappings)} vendor mappings")
        
        for mapping in mappings:
            print(f"  - {mapping.vendor.value}: {len(mapping.yang_paths)} YANG paths")
        
        return True
        
    except Exception as e:
        print(f"❌ YANG mapping test failed: {e}")
        return False

def test_config_generation():
    """Test configuration generation"""
    
    print("\n📦 Testing Configuration Generation...")
    
    try:
        from core.config_generator import ConfigGenerator
        from models.base import (
            NormalizedIntent, ServiceType, MappingEntry, 
            Vendor, Endpoint
        )
        
        generator = ConfigGenerator()
        
        # Mock normalized intent
        intent = NormalizedIntent(
            service_type=ServiceType.L3VPN,
            endpoints=[
                Endpoint(device="PE1", interface="ethernet-1/3", tags=["pe"]),
                Endpoint(device="PE2", interface="ethernet-1/3", tags=["pe"])
            ]
        )
        
        # Mock mapping table
        mappings = [
            MappingEntry(
                vendor=Vendor.NOKIA,
                os_version="SR OS 21.7",
                yang_paths=[
                    "nokia-conf:configure/service/vprn/service-id",
                    "nokia-conf:configure/service/vprn/route-distinguisher"
                ]
            )
        ]
        
        # Mock inventory
        inventory = [
            {
                "device_id": "PE1",
                "vendor": "nokia",
                "bgp_asn": "65000",
                "netconf_enabled": True
            }
        ]
        
        payloads = generator.generate_payloads(intent, mappings, inventory)
        
        print(f"✅ Configuration payloads generated successfully")
        print(f"  - Generated {len(payloads)} payloads")
        
        for payload in payloads:
            print(f"  - {payload.target}: {payload.transport.value} ({len(payload.payload)} chars)")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration generation test failed: {e}")
        return False

def test_llm_interface():
    """Test LLM interface (without actual LLM)"""
    
    print("\n🤖 Testing LLM Interface...")
    
    try:
        from llm.connect_llm import LLMConnector, get_recommended_mac_models
        from llm.base_llm import LLMMessage
        
        # Test connector initialization
        connector = LLMConnector()
        
        print(f"✅ LLM Connector initialized")
        print(f"  - Provider: {connector.config.provider}")
        print(f"  - Model: {connector.config.model}")
        
        # Test Mac model recommendations
        mac_models = get_recommended_mac_models()
        print(f"✅ Mac MLX models available:")
        for category, model in mac_models.items():
            print(f"  - {category}: {model}")
        
        # Test message formatting
        messages = [
            LLMMessage(role="user", content="Test message")
        ]
        
        print(f"✅ LLM message formatting works")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM interface test failed: {e}")
        return False

def run_all_tests():
    """Run all platform tests"""
    
    print("🚀 AURORA-IBN Platform Validation Test Suite")
    print("=" * 50)
    
    tests = [
        ("Platform Imports", test_platform_imports),
        ("NLP Parsing", test_nlp_parsing), 
        ("YANG Mapping", test_yang_mapping),
        ("Config Generation", test_config_generation),
        ("LLM Interface", test_llm_interface)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("🏁 Test Suite Results")
    print("=" * 50)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AURORA-IBN platform is functional.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed. Review the output above.")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)  # Reduce noise
    success = run_all_tests()
    sys.exit(0 if success else 1)