import re
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import json
import hashlib
from datetime import datetime

from ..models.base import (
    IntentResponse, NormalizedIntent, ServiceType, 
    Endpoint, Routing, SLO, Policy, RiskAssessment, RiskLevel
)
from .nlp_parser import NLPParser
from .model_discovery import ModelDiscovery
from .config_generator import ConfigGenerator
from .validation_engine import ValidationEngine


class IntentProcessor:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.nlp_parser = NLPParser()
        self.model_discovery = ModelDiscovery(self.config)
        self.config_generator = ConfigGenerator()
        self.validation_engine = ValidationEngine()
        
    def process_intent(
        self,
        intent_text: str,
        inventory: List[Dict[str, Any]],
        policy: Optional[Dict[str, Any]] = None,
        telemetry_hint: Optional[Dict[str, Any]] = None
    ) -> str:
        try:
            normalized_intent = self._normalize_intent(intent_text, telemetry_hint)
            
            risk_assessment = self._assess_risks(
                normalized_intent, inventory, policy
            )
            
            model_discovery_results = self.model_discovery.discover_models(
                inventory, normalized_intent
            )
            
            mapping_table = self._create_mapping_table(
                normalized_intent, model_discovery_results, inventory
            )
            
            candidate_payloads = self.config_generator.generate_payloads(
                normalized_intent, mapping_table, inventory
            )
            
            commit_plan = self._create_commit_plan(
                candidate_payloads, risk_assessment, policy
            )
            
            verification_plan = self.validation_engine.create_verification_plan(
                normalized_intent, inventory
            )
            
            audit_log = self._create_audit_log(
                model_discovery_results, candidate_payloads
            )
            
            response = IntentResponse(
                intent_summary=self._summarize_intent(intent_text),
                risk_assessment=risk_assessment,
                model_discovery=model_discovery_results,
                normalized_intent=normalized_intent,
                mapping_table=mapping_table,
                candidate_payloads=candidate_payloads,
                commit_plan=commit_plan,
                verification_plan=verification_plan,
                audit_log=audit_log
            )
            
            return json.dumps(self._serialize_response(response), indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "intent_summary": intent_text[:100],
                "risk_assessment": {
                    "level": "HIGH",
                    "factors": ["Processing error encountered"],
                    "mitigations": ["Manual review required"]
                }
            }, indent=2)
    
    def _normalize_intent(
        self, 
        intent_text: str, 
        telemetry_hint: Optional[Dict[str, Any]]
    ) -> NormalizedIntent:
        parsed = self.nlp_parser.parse(intent_text)
        
        service_type = self._detect_service_type(intent_text, parsed)
        endpoints = self._extract_endpoints(parsed, telemetry_hint)
        routing = self._extract_routing(parsed)
        slo = self._extract_slo(parsed)
        policy = self._extract_policy(parsed)
        
        return NormalizedIntent(
            service_type=service_type,
            endpoints=endpoints,
            routing=routing,
            slo=slo,
            policy=policy
        )
    
    def _detect_service_type(self, text: str, parsed: Dict) -> ServiceType:
        text_lower = text.lower()
        
        if any(term in text_lower for term in ["l3vpn", "vrf", "vpnv4", "vpnv6"]):
            return ServiceType.L3VPN
        elif any(term in text_lower for term in ["l2vpn", "epipe", "vpws", "e-line"]):
            return ServiceType.L2VPN_EPIPE
        elif any(term in text_lower for term in ["evpn", "vxlan", "e-lan"]):
            return ServiceType.EVPN
        elif "isis" in text_lower or "is-is" in text_lower:
            return ServiceType.ISIS
        elif "ospf" in text_lower:
            return ServiceType.OSPF
        elif "bgp" in text_lower:
            return ServiceType.BGP
        elif any(term in text_lower for term in ["qos", "queue", "shaping"]):
            return ServiceType.QOS
        elif any(term in text_lower for term in ["acl", "filter", "firewall"]):
            return ServiceType.ACL
        elif "srv6" in text_lower:
            return ServiceType.SRV6
        elif any(term in text_lower for term in ["segment", "sr-mpls", "sr-te"]):
            return ServiceType.SEGMENT_ROUTING
        elif any(term in text_lower for term in ["telemetry", "streaming"]):
            return ServiceType.TELEMETRY
        
        return ServiceType.L3VPN
    
    def _extract_endpoints(
        self, 
        parsed: Dict, 
        telemetry_hint: Optional[Dict]
    ) -> List[Endpoint]:
        endpoints = []
        
        devices = parsed.get("devices", [])
        interfaces = parsed.get("interfaces", [])
        
        for i, device in enumerate(devices):
            interface = interfaces[i] if i < len(interfaces) else "auto"
            tags = []
            
            if "pe" in device.lower():
                tags.append("pe")
            if "ce" in device.lower():
                tags.append("ce")
                
            endpoints.append(Endpoint(
                device=device,
                interface=interface,
                tags=tags
            ))
        
        return endpoints if endpoints else [
            Endpoint(device="auto", interface="auto", tags=["auto-discovered"])
        ]
    
    def _extract_routing(self, parsed: Dict) -> Optional[Routing]:
        protocols = []
        address_families = []
        
        if parsed.get("protocols"):
            protocols = parsed["protocols"]
        if parsed.get("address_families"):
            address_families = parsed["address_families"]
        
        if protocols or address_families:
            return Routing(
                protocols=protocols or ["bgp"],
                address_families=address_families or ["ipv4", "ipv6"]
            )
        
        return None
    
    def _extract_slo(self, parsed: Dict) -> Optional[SLO]:
        if not parsed.get("slo"):
            return None
            
        slo_data = parsed["slo"]
        return SLO(
            latency_ms=slo_data.get("latency_ms"),
            loss_pct=slo_data.get("loss_pct"),
            jitter_ms=slo_data.get("jitter_ms")
        )
    
    def _extract_policy(self, parsed: Dict) -> Optional[Policy]:
        if not parsed.get("policy"):
            return Policy()
            
        policy_data = parsed["policy"]
        return Policy(
            mtu=policy_data.get("mtu", 1500),
            bfd=policy_data.get("bfd", False),
            auth=policy_data.get("auth")
        )
    
    def _assess_risks(
        self,
        intent: NormalizedIntent,
        inventory: List[Dict],
        policy: Optional[Dict]
    ) -> RiskAssessment:
        factors = []
        mitigations = []
        level = RiskLevel.LOW
        
        if intent.service_type in [ServiceType.L3VPN, ServiceType.EVPN]:
            factors.append("Core routing modification required")
            mitigations.append("Use confirmed-commit with auto-rollback")
            level = RiskLevel.MEDIUM
        
        multi_vendor = len(set(d.get("vendor", "") for d in inventory)) > 1
        if multi_vendor:
            factors.append("Multi-vendor environment detected")
            mitigations.append("Validate vendor-specific YANG models")
            level = RiskLevel.MEDIUM
        
        if not policy or not policy.get("maintenance_window"):
            factors.append("No maintenance window specified")
            mitigations.append("Schedule during low-traffic period")
            if level == RiskLevel.LOW:
                level = RiskLevel.MEDIUM
        
        if intent.slo and intent.slo.latency_ms and intent.slo.latency_ms < 10:
            factors.append("Aggressive SLO requirements")
            mitigations.append("Enable performance monitoring pre/post change")
            level = RiskLevel.HIGH
        
        return RiskAssessment(
            level=level,
            factors=factors if factors else ["Standard configuration change"],
            mitigations=mitigations if mitigations else ["Follow standard procedures"]
        )
    
    def _create_mapping_table(
        self,
        intent: NormalizedIntent,
        discovery_results: List,
        inventory: List[Dict]
    ) -> List:
        from .yang_mapper import YANGMapper
        mapper = YANGMapper()
        
        return mapper.create_mappings(intent, discovery_results, inventory)
    
    def _create_commit_plan(
        self,
        payloads: List,
        risk: RiskAssessment,
        policy: Optional[Dict]
    ) -> Dict:
        strategy = "candidate+validate+confirmed-commit"
        
        if risk.level == RiskLevel.HIGH:
            strategy = "dry-run+manual-review+staged-commit"
        
        return {
            "strategy": strategy,
            "batching": "per-vendor" if len(payloads) > 5 else "all-at-once",
            "rollback": {
                "method": "confirmed-commit-timeout",
                "timeout_seconds": 120 if risk.level == RiskLevel.HIGH else 300
            },
            "maintenance_window": policy.get("maintenance_window") if policy else None
        }
    
    def _create_audit_log(
        self,
        discovery_results: List,
        payloads: List
    ) -> Dict:
        sources = []
        for result in discovery_results:
            if hasattr(result, 'source'):
                sources.append(result.source)
        
        hashes = {}
        for i, payload in enumerate(payloads):
            if hasattr(payload, 'payload'):
                payload_str = payload.payload
                hashes[f"payload_{i}"] = hashlib.sha256(
                    payload_str.encode()
                ).hexdigest()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "sources": list(set(sources)),
            "hashes": hashes
        }
    
    def _summarize_intent(self, intent_text: str) -> str:
        summary = intent_text[:200]
        if len(intent_text) > 200:
            summary += "..."
        return summary.replace("\n", " ").strip()
    
    def _serialize_response(self, response: IntentResponse) -> Dict:
        def serialize_value(obj):
            if hasattr(obj, '__dict__'):
                return {k: serialize_value(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, list):
                return [serialize_value(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: serialize_value(v) for k, v in obj.items()}
            elif isinstance(obj, (datetime,)):
                return obj.isoformat()
            elif hasattr(obj, 'value'):
                return obj.value
            else:
                return obj
        
        return serialize_value(asdict(response))