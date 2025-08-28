import re
from typing import Dict, List, Any, Optional


class NLPParser:
    def __init__(self):
        self.device_patterns = [
            r'\b(PE[1-9]\d*|CE[1-9]\d*|P[1-9]\d*)\b',
            r'\b([A-Z]{2,}-[A-Z0-9]+-[A-Z0-9]+)\b',
            r'\b(\w+-\w+-\d+)\b'
        ]
        
        self.interface_patterns = [
            r'\b(xe-\d+/\d+/\d+|ge-\d+/\d+/\d+|et-\d+/\d+/\d+)\b',
            r'\b(GigabitEthernet\d+/\d+/\d+|Gi\d+/\d+/\d+)\b',
            r'\b(10GE\d+/\d+/\d+|100GE\d+/\d+/\d+)\b',
            r'\b(Ethernet\d+/\d+|eth\d+/\d+)\b',
            r'\b(port\s+\d+/\d+/\d+)\b'
        ]
        
        self.protocol_keywords = {
            'bgp': ['bgp', 'ebgp', 'ibgp', 'as\d+', 'as \d+'],
            'isis': ['isis', 'is-is', 'level-1', 'level-2'],
            'ospf': ['ospf', 'ospfv2', 'ospfv3', 'area'],
            'ldp': ['ldp', 'label', 'mpls'],
            'rsvp': ['rsvp', 'rsvp-te'],
            'segment-routing': ['segment-routing', 'sr', 'sr-mpls', 'sr-te', 'srv6']
        }
        
        self.slo_patterns = {
            'latency': r'(\d+)\s*ms\s*(?:latency|delay|rtt)',
            'loss': r'(\d+(?:\.\d+)?)\s*%?\s*(?:loss|packet loss)',
            'jitter': r'(\d+)\s*ms\s*jitter',
            'bandwidth': r'(\d+)\s*(?:gbps|mbps|kbps)',
        }
        
        self.policy_patterns = {
            'mtu': r'mtu\s*[:\s]*(\d+)',
            'vlan': r'vlan\s*[:\s]*(\d+)',
            'vrf': r'vrf\s+(\S+)',
            'rd': r'rd\s+([0-9.:]+)',
            'rt': r'rt\s+([0-9.:]+)'
        }
    
    def parse(self, intent_text: str) -> Dict[str, Any]:
        text_lower = intent_text.lower()
        
        result = {
            'original_text': intent_text,
            'devices': self._extract_devices(intent_text),
            'interfaces': self._extract_interfaces(intent_text),
            'protocols': self._extract_protocols(text_lower),
            'address_families': self._extract_address_families(text_lower),
            'slo': self._extract_slo(text_lower),
            'policy': self._extract_policy(intent_text),
            'service_attributes': self._extract_service_attributes(intent_text)
        }
        
        return result
    
    def _extract_devices(self, text: str) -> List[str]:
        devices = []
        for pattern in self.device_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            devices.extend(matches)
        
        return list(set(devices)) if devices else []
    
    def _extract_interfaces(self, text: str) -> List[str]:
        interfaces = []
        for pattern in self.interface_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            interfaces.extend(matches)
        
        return list(set(interfaces)) if interfaces else []
    
    def _extract_protocols(self, text: str) -> List[str]:
        protocols = []
        for proto, keywords in self.protocol_keywords.items():
            for keyword in keywords:
                if re.search(r'\b' + keyword + r'\b', text, re.IGNORECASE):
                    protocols.append(proto)
                    break
        
        return list(set(protocols)) if protocols else []
    
    def _extract_address_families(self, text: str) -> List[str]:
        families = []
        
        if any(term in text for term in ['ipv4', 'v4', 'inet']):
            families.append('ipv4')
        if any(term in text for term in ['ipv6', 'v6', 'inet6']):
            families.append('ipv6')
        if 'vpnv4' in text:
            families.append('vpnv4')
        if 'vpnv6' in text:
            families.append('vpnv6')
        if any(term in text for term in ['evpn', 'l2vpn']):
            families.append('l2vpn-evpn')
        
        return families if families else ['ipv4']
    
    def _extract_slo(self, text: str) -> Optional[Dict[str, Any]]:
        slo = {}
        
        for slo_type, pattern in self.slo_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                if slo_type == 'latency':
                    slo['latency_ms'] = value
                elif slo_type == 'loss':
                    slo['loss_pct'] = value
                elif slo_type == 'jitter':
                    slo['jitter_ms'] = value
                elif slo_type == 'bandwidth':
                    slo['bandwidth_mbps'] = value
        
        return slo if slo else None
    
    def _extract_policy(self, text: str) -> Dict[str, Any]:
        policy = {}
        
        for policy_type, pattern in self.policy_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if policy_type == 'mtu':
                    policy['mtu'] = int(match.group(1))
                elif policy_type == 'vlan':
                    policy['vlan'] = int(match.group(1))
                else:
                    policy[policy_type] = match.group(1)
        
        if 'bfd' in text.lower():
            policy['bfd'] = True
        
        if 'auth' in text.lower() or 'authentication' in text.lower():
            policy['auth'] = 'keychain-default'
        
        return policy
    
    def _extract_service_attributes(self, text: str) -> Dict[str, Any]:
        attributes = {}
        
        rd_match = re.search(r'rd\s+([0-9.:]+)', text, re.IGNORECASE)
        if rd_match:
            attributes['route_distinguisher'] = rd_match.group(1)
        elif 'rd auto' in text.lower():
            attributes['route_distinguisher'] = 'auto'
        
        rt_matches = re.findall(r'rt\s+([0-9.:]+)', text, re.IGNORECASE)
        if rt_matches:
            attributes['route_targets'] = rt_matches
        elif 'rt auto' in text.lower():
            attributes['route_targets'] = ['auto']
        
        vrf_match = re.search(r'vrf\s+(\S+)', text, re.IGNORECASE)
        if vrf_match:
            attributes['vrf_name'] = vrf_match.group(1)
        
        as_match = re.search(r'as\s*(\d+)', text, re.IGNORECASE)
        if as_match:
            attributes['autonomous_system'] = int(as_match.group(1))
        
        if any(term in text.lower() for term in ['rfc1918', 'private']):
            attributes['filter_private'] = True
        
        if 'symmetric' in text.lower():
            attributes['symmetric'] = True
        
        if 'multihoming' in text.lower() or 'multi-homing' in text.lower():
            attributes['multihoming'] = True
        
        return attributes