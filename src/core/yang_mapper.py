from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import logging

from ..models.base import NormalizedIntent, ServiceType, Vendor, MappingEntry


@dataclass
class YANGPath:
    path: str
    leaf_type: str  # string, int, boolean, etc.
    mandatory: bool = False
    default_value: Any = None
    constraints: Optional[Dict[str, Any]] = None


@dataclass
class VendorMapping:
    vendor: Vendor
    os_version: str
    service_paths: Dict[str, YANGPath]
    deviations: List[str] = None
    augmentations: List[str] = None


class YANGMapper:
    """
    Maps normalized intents to vendor-specific YANG paths
    Handles model differences and deviations across vendors
    """
    
    def __init__(self):
        self.vendor_mappings = self._initialize_vendor_mappings()
        self.standard_mappings = self._initialize_standard_mappings()
    
    def create_mappings(
        self,
        intent: NormalizedIntent,
        discovery_results: List,
        inventory: List[Dict[str, Any]]
    ) -> List[MappingEntry]:
        """Create YANG path mappings for the given intent"""
        
        mappings = []
        
        for device in inventory:
            vendor_str = device.get('vendor', '').lower()
            try:
                vendor = Vendor(vendor_str)
            except ValueError:
                logging.warning(f"Unknown vendor: {vendor_str}")
                continue
            
            os_version = device.get('os_version', 'unknown')
            
            yang_paths = self._get_yang_paths_for_intent(
                intent, vendor, os_version, discovery_results
            )
            
            notes = self._get_mapping_notes(vendor, intent)
            
            mapping = MappingEntry(
                vendor=vendor,
                os_version=os_version,
                yang_paths=yang_paths,
                notes=notes
            )
            
            mappings.append(mapping)
        
        return mappings
    
    def _get_yang_paths_for_intent(
        self,
        intent: NormalizedIntent,
        vendor: Vendor,
        os_version: str,
        discovery_results: List
    ) -> List[str]:
        """Get YANG paths for a specific vendor and intent"""
        
        paths = []
        service_type = intent.service_type.value
        
        if service_type == 'l3vpn':
            paths.extend(self._get_l3vpn_paths(vendor, intent))
        elif service_type == 'evpn':
            paths.extend(self._get_evpn_paths(vendor, intent))
        elif service_type == 'bgp':
            paths.extend(self._get_bgp_paths(vendor, intent))
        elif service_type in ['isis', 'ospf']:
            paths.extend(self._get_igp_paths(vendor, service_type, intent))
        
        if intent.policy and intent.policy.bfd:
            paths.extend(self._get_bfd_paths(vendor))
        
        return paths
    
    def _get_l3vpn_paths(self, vendor: Vendor, intent: NormalizedIntent) -> List[str]:
        """Get L3VPN YANG paths for vendor"""
        
        if vendor == Vendor.CISCO:
            return [
                "Cisco-IOS-XR-infra-rsi-cfg:vrfs/vrf/vrf-name",
                "Cisco-IOS-XR-infra-rsi-cfg:vrfs/vrf/description",
                "Cisco-IOS-XR-infra-rsi-cfg:vrfs/vrf/vpn-id",
                "Cisco-IOS-XR-mpls-vpn-cfg:l3vpn/vrfs/vrf",
                "Cisco-IOS-XR-bgp-cfg:bgp/instance/instance-as/four-byte-as/default-vrf/global/route-distinguisher"
            ]
        elif vendor == Vendor.NOKIA:
            return [
                "nokia-conf:configure/service/vprn/service-id",
                "nokia-conf:configure/service/vprn/customer",
                "nokia-conf:configure/service/vprn/description",
                "nokia-conf:configure/service/vprn/route-distinguisher",
                "nokia-conf:configure/service/vprn/vrf-target"
            ]
        elif vendor == Vendor.JUNIPER:
            return [
                "junos-conf-routing-instances:configuration/routing-instances/instance/name",
                "junos-conf-routing-instances:configuration/routing-instances/instance/instance-type",
                "junos-conf-routing-instances:configuration/routing-instances/instance/route-distinguisher",
                "junos-conf-routing-instances:configuration/routing-instances/instance/vrf-target"
            ]
        else:
            return [
                "openconfig-network-instance:network-instances/network-instance/name",
                "openconfig-network-instance:network-instances/network-instance/config/type",
                "openconfig-network-instance:network-instances/network-instance/config/route-distinguisher"
            ]
    
    def _get_evpn_paths(self, vendor: Vendor, intent: NormalizedIntent) -> List[str]:
        """Get EVPN YANG paths for vendor"""
        
        if vendor == Vendor.CISCO:
            return [
                "Cisco-IOS-XR-l2vpn-cfg:l2vpn/database/bridge-domain-groups/bridge-domain-group",
                "Cisco-IOS-XR-l2vpn-cfg:l2vpn/database/xconnect-groups/xconnect-group",
                "Cisco-IOS-XR-evpn-cfg:evpn/enable",
                "Cisco-IOS-XR-evpn-cfg:evpn/interfaces/interface"
            ]
        elif vendor == Vendor.NOKIA:
            return [
                "nokia-conf:configure/service/epipe/service-id",
                "nokia-conf:configure/service/vpls/service-id",
                "nokia-conf:configure/service/epipe/bgp-evpn/evi",
                "nokia-conf:configure/service/vpls/bgp-evpn/evi"
            ]
        elif vendor == Vendor.JUNIPER:
            return [
                "junos-conf-protocols:configuration/protocols/evpn/encapsulation",
                "junos-conf-protocols:configuration/protocols/evpn/extended-vni-list",
                "junos-conf-routing-instances:configuration/routing-instances/instance/protocols/evpn"
            ]
        else:
            return [
                "openconfig-evpn:evpn/global/config/enabled",
                "openconfig-network-instance:network-instances/network-instance/evpn/config"
            ]
    
    def _get_bgp_paths(self, vendor: Vendor, intent: NormalizedIntent) -> List[str]:
        """Get BGP YANG paths for vendor"""
        
        if vendor == Vendor.CISCO:
            return [
                "Cisco-IOS-XR-bgp-cfg:bgp/instance/instance-as/four-byte-as",
                "Cisco-IOS-XR-bgp-cfg:bgp/instance/instance-as/four-byte-as/default-vrf/global/router-id",
                "Cisco-IOS-XR-bgp-cfg:bgp/instance/instance-as/four-byte-as/default-vrf/bgp-entity/neighbors/neighbor"
            ]
        elif vendor == Vendor.NOKIA:
            return [
                "nokia-conf:configure/router/bgp/autonomous-system",
                "nokia-conf:configure/router/bgp/router-id",
                "nokia-conf:configure/router/bgp/group",
                "nokia-conf:configure/router/bgp/neighbor"
            ]
        elif vendor == Vendor.JUNIPER:
            return [
                "junos-conf-protocols:configuration/protocols/bgp/group/name",
                "junos-conf-protocols:configuration/protocols/bgp/group/neighbor",
                "junos-conf-routing-options:configuration/routing-options/autonomous-system"
            ]
        else:
            return [
                "openconfig-bgp:bgp/global/config/as",
                "openconfig-bgp:bgp/global/config/router-id",
                "openconfig-bgp:bgp/neighbors/neighbor"
            ]
    
    def _get_igp_paths(self, vendor: Vendor, protocol: str, intent: NormalizedIntent) -> List[str]:
        """Get IGP (ISIS/OSPF) YANG paths for vendor"""
        
        if protocol == 'isis':
            if vendor == Vendor.CISCO:
                return [
                    "Cisco-IOS-XR-clns-isis-cfg:isis/instances/instance/instance-name",
                    "Cisco-IOS-XR-clns-isis-cfg:isis/instances/instance/running/addresses/address",
                    "Cisco-IOS-XR-clns-isis-cfg:isis/instances/instance/running/interfaces/interface"
                ]
            elif vendor == Vendor.NOKIA:
                return [
                    "nokia-conf:configure/router/isis/instance",
                    "nokia-conf:configure/router/isis/area-address",
                    "nokia-conf:configure/router/isis/interface"
                ]
            else:
                return [
                    "openconfig-isis:isis/global/config/instance",
                    "openconfig-isis:isis/global/afi-safi",
                    "openconfig-isis:isis/interfaces/interface"
                ]
        
        elif protocol == 'ospf':
            if vendor == Vendor.CISCO:
                return [
                    "Cisco-IOS-XR-ipv4-ospf-cfg:ospf/processes/process/process-name",
                    "Cisco-IOS-XR-ipv4-ospf-cfg:ospf/processes/process/default-vrf/router-id",
                    "Cisco-IOS-XR-ipv4-ospf-cfg:ospf/processes/process/default-vrf/area-addresses/area-area-id"
                ]
            elif vendor == Vendor.NOKIA:
                return [
                    "nokia-conf:configure/router/ospf/instance",
                    "nokia-conf:configure/router/ospf/router-id",
                    "nokia-conf:configure/router/ospf/area"
                ]
            else:
                return [
                    "openconfig-ospfv2:ospfv2/global/config/router-id",
                    "openconfig-ospfv2:ospfv2/areas/area",
                    "openconfig-ospfv2:ospfv2/areas/area/interfaces/interface"
                ]
        
        return []
    
    def _get_bfd_paths(self, vendor: Vendor) -> List[str]:
        """Get BFD YANG paths for vendor"""
        
        if vendor == Vendor.CISCO:
            return [
                "Cisco-IOS-XR-ip-bfd-cfg:bfd/ipv4bf-table/ipv4bf-mhop-table/ipv4bf-mhop/destination-address",
                "Cisco-IOS-XR-ip-bfd-cfg:bfd/ipv4bf-table/ipv4bf-shfrom-table/ipv4bf-sh/source-address"
            ]
        elif vendor == Vendor.NOKIA:
            return [
                "nokia-conf:configure/router/bfd/session-type",
                "nokia-conf:configure/router/bfd/transmit-interval",
                "nokia-conf:configure/router/bfd/receive-interval"
            ]
        elif vendor == Vendor.JUNIPER:
            return [
                "junos-conf-protocols:configuration/protocols/bfd/session",
                "junos-conf-protocols:configuration/protocols/bfd/traceoptions"
            ]
        else:
            return [
                "openconfig-bfd:bfd/interfaces/interface",
                "openconfig-bfd:bfd/ipv4-single-hop/sessions/session"
            ]
    
    def _get_mapping_notes(self, vendor: Vendor, intent: NormalizedIntent) -> Optional[str]:
        """Get vendor-specific notes for mapping"""
        
        notes = []
        
        if vendor == Vendor.CISCO:
            if intent.service_type == ServiceType.L3VPN:
                notes.append("IOS-XR uses separate VRF and BGP VPNv4 configuration")
            if intent.policy and intent.policy.bfd:
                notes.append("BFD requires explicit interface configuration")
        
        elif vendor == Vendor.NOKIA:
            if intent.service_type == ServiceType.L3VPN:
                notes.append("SR OS uses service-based VPN configuration")
            notes.append("Nokia requires explicit service activation")
        
        elif vendor == Vendor.JUNIPER:
            if intent.service_type == ServiceType.EVPN:
                notes.append("Junos requires EVPN protocol configuration under routing-instances")
            notes.append("Juniper uses commit-confirmed for safe configuration")
        
        return "; ".join(notes) if notes else None
    
    def _initialize_vendor_mappings(self) -> Dict[Vendor, Dict[str, Any]]:
        """Initialize vendor-specific mappings"""
        return {}
    
    def _initialize_standard_mappings(self) -> Dict[str, Any]:
        """Initialize standard OpenConfig mappings"""
        return {}
    
    def validate_yang_path(self, path: str, available_models: List[str]) -> bool:
        """Validate if YANG path is supported by available models"""
        
        module_name = path.split(':')[0]
        
        for model in available_models:
            if module_name in model:
                return True
        
        return False
    
    def suggest_alternatives(
        self, 
        unsupported_paths: List[str], 
        available_models: List[str]
    ) -> Dict[str, List[str]]:
        """Suggest alternative paths for unsupported YANG paths"""
        
        alternatives = {}
        
        for path in unsupported_paths:
            alts = []
            
            if "openconfig" not in path and any("openconfig" in model for model in available_models):
                alts.append(self._convert_to_openconfig(path))
            
            if "ietf" not in path and any("ietf" in model for model in available_models):
                alts.append(self._convert_to_ietf(path))
            
            alternatives[path] = [alt for alt in alts if alt]
        
        return alternatives
    
    def _convert_to_openconfig(self, vendor_path: str) -> Optional[str]:
        """Convert vendor-specific path to OpenConfig equivalent"""
        
        conversion_map = {
            'vrf': 'network-instance',
            'bgp': 'bgp',
            'isis': 'isis',
            'ospf': 'ospfv2',
            'interface': 'interface'
        }
        
        for vendor_term, oc_term in conversion_map.items():
            if vendor_term in vendor_path.lower():
                return f"openconfig-{oc_term}:..."
        
        return None
    
    def _convert_to_ietf(self, vendor_path: str) -> Optional[str]:
        """Convert vendor-specific path to IETF equivalent"""
        
        conversion_map = {
            'l3vpn': 'ietf-l3vpn-svc',
            'l2vpn': 'ietf-l2vpn-svc', 
            'bgp': 'ietf-bgp',
            'isis': 'ietf-isis',
            'ospf': 'ietf-ospf'
        }
        
        for vendor_term, ietf_term in conversion_map.items():
            if vendor_term in vendor_path.lower():
                return f"{ietf_term}:..."
        
        return None