import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

from ..models.base import (
    NormalizedIntent, CandidatePayload, Transport, 
    ServiceType, Vendor, MappingEntry
)


@dataclass
class ConfigTemplate:
    name: str
    vendor: Vendor
    transport: Transport
    template: str
    variables: List[str]
    prechecks: List[str] = None
    post_validation: List[str] = None


class ConfigGenerator:
    """
    Generates vendor-specific configurations from normalized intents
    Supports NETCONF XML, RESTCONF JSON, and gNMI Set payloads
    """
    
    def __init__(self):
        self.templates = self._load_templates()
        self.namespace_map = self._initialize_namespaces()
    
    def generate_payloads(
        self,
        intent: NormalizedIntent,
        mapping_table: List[MappingEntry],
        inventory: List[Dict[str, Any]]
    ) -> List[CandidatePayload]:
        """Generate configuration payloads for all devices"""
        
        payloads = []
        
        for i, device in enumerate(inventory):
            if i < len(mapping_table):
                mapping = mapping_table[i]
                
                payload = self._generate_device_payload(
                    intent, mapping, device
                )
                
                if payload:
                    payloads.append(payload)
        
        return payloads
    
    def _generate_device_payload(
        self,
        intent: NormalizedIntent,
        mapping: MappingEntry,
        device: Dict[str, Any]
    ) -> Optional[CandidatePayload]:
        """Generate payload for a specific device"""
        
        device_id = device.get('device_id', device.get('hostname', 'unknown'))
        vendor = mapping.vendor
        transport = self._determine_transport(device)
        
        try:
            if transport == Transport.NETCONF:
                payload_content = self._generate_netconf_payload(
                    intent, mapping, device
                )
                payload_type = "xml"
            
            elif transport == Transport.RESTCONF:
                payload_content = self._generate_restconf_payload(
                    intent, mapping, device
                )
                payload_type = "json"
            
            elif transport == Transport.GNMI:
                payload_content = self._generate_gnmi_payload(
                    intent, mapping, device
                )
                payload_type = "gnmi-set"
            
            else:
                logging.error(f"Unsupported transport: {transport}")
                return None
            
            prechecks = self._generate_prechecks(mapping, device)
            post_validation = self._generate_post_validation(intent, mapping, device)
            
            return CandidatePayload(
                target=device_id,
                transport=transport,
                payload_type=payload_type,
                payload=payload_content,
                prechecks=prechecks,
                post_validation=post_validation
            )
        
        except Exception as e:
            logging.error(f"Failed to generate payload for {device_id}: {e}")
            return None
    
    def _determine_transport(self, device: Dict[str, Any]) -> Transport:
        """Determine the best transport for device"""
        
        if device.get('netconf_enabled', True):
            return Transport.NETCONF
        elif device.get('restconf_enabled', False):
            return Transport.RESTCONF
        elif device.get('gnmi_enabled', False):
            return Transport.GNMI
        else:
            return Transport.NETCONF
    
    def _generate_netconf_payload(
        self,
        intent: NormalizedIntent,
        mapping: MappingEntry,
        device: Dict[str, Any]
    ) -> str:
        """Generate NETCONF XML payload"""
        
        vendor = mapping.vendor
        service_type = intent.service_type
        
        if service_type == ServiceType.L3VPN:
            return self._generate_l3vpn_netconf(intent, mapping, device)
        elif service_type == ServiceType.EVPN:
            return self._generate_evpn_netconf(intent, mapping, device)
        elif service_type == ServiceType.BGP:
            return self._generate_bgp_netconf(intent, mapping, device)
        else:
            return self._generate_generic_netconf(intent, mapping, device)
    
    def _generate_l3vpn_netconf(
        self,
        intent: NormalizedIntent,
        mapping: MappingEntry,
        device: Dict[str, Any]
    ) -> str:
        """Generate L3VPN NETCONF configuration"""
        
        vendor = mapping.vendor
        
        if vendor == Vendor.CISCO:
            return self._generate_cisco_l3vpn_xml(intent, device)
        elif vendor == Vendor.NOKIA:
            return self._generate_nokia_l3vpn_xml(intent, device)
        elif vendor == Vendor.JUNIPER:
            return self._generate_juniper_l3vpn_xml(intent, device)
        else:
            return self._generate_openconfig_l3vpn_xml(intent, device)
    
    def _generate_cisco_l3vpn_xml(self, intent: NormalizedIntent, device: Dict[str, Any]) -> str:
        """Generate Cisco IOS-XR L3VPN XML configuration"""
        
        vrf_name = self._extract_vrf_name(intent)
        rd = self._generate_rd(device)
        rt = self._generate_rt(device)
        
        xml_template = f"""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <vrfs xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-infra-rsi-cfg">
    <vrf>
      <vrf-name>{vrf_name}</vrf-name>
      <create/>
      <description>L3VPN service for {vrf_name}</description>
      <vpn-id>
        <vpn-oui>1</vpn-oui>
        <vpn-index>1</vpn-index>
      </vpn-id>
    </vrf>
  </vrfs>
  <bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-bgp-cfg">
    <instance>
      <instance-name>default</instance-name>
      <instance-as>
        <as>0</as>
        <four-byte-as>
          <as>{device.get('bgp_asn', '65000')}</as>
          <bgp-running/>
          <default-vrf>
            <global>
              <route-distinguisher>
                <type>as</type>
                <as>{device.get('bgp_asn', '65000')}</as>
                <as-index>{device.get('device_id', '1')}</as-index>
              </route-distinguisher>
            </global>
          </default-vrf>
          <vrfs>
            <vrf>
              <vrf-name>{vrf_name}</vrf-name>
              <vrf-global>
                <route-distinguisher>
                  <type>as</type>
                  <as>{device.get('bgp_asn', '65000')}</as>
                  <as-index>{device.get('device_id', '1')}</as-index>
                </route-distinguisher>
                <route-target>
                  <route-target-as-format>
                    <as>{device.get('bgp_asn', '65000')}</as>
                    <as-index>{device.get('device_id', '1')}</as-index>
                  </route-target-as-format>
                </route-target>
              </vrf-global>
            </vrf>
          </vrfs>
        </four-byte-as>
      </instance-as>
    </instance>
  </bgp>
</config>"""
        
        return xml_template.strip()
    
    def _generate_nokia_l3vpn_xml(self, intent: NormalizedIntent, device: Dict[str, Any]) -> str:
        """Generate Nokia SR OS L3VPN XML configuration"""
        
        vrf_name = self._extract_vrf_name(intent)
        service_id = device.get('service_id', '100')
        
        xml_template = f"""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <configure xmlns="urn:nokia.com:sros:ns:yang:sr:conf">
    <service>
      <vprn>
        <service-id>{service_id}</service-id>
        <admin-state>enable</admin-state>
        <service-name>{vrf_name}</service-name>
        <customer>1</customer>
        <description>L3VPN service for {vrf_name}</description>
        <route-distinguisher>{device.get('bgp_asn', '65000')}:{service_id}</route-distinguisher>
        <auto-bind-tunnel>
          <resolution>any</resolution>
        </auto-bind-tunnel>
        <vrf-target>
          <community>target:{device.get('bgp_asn', '65000')}:{service_id}</community>
          <import-export/>
        </vrf-target>
        <bgp-ipvpn>
          <mpls>
            <admin-state>enable</admin-state>
            <route-distinguisher>{device.get('bgp_asn', '65000')}:{service_id}</route-distinguisher>
            <vrf-target>
              <export>target:{device.get('bgp_asn', '65000')}:{service_id}</export>
              <import>target:{device.get('bgp_asn', '65000')}:{service_id}</import>
            </vrf-target>
          </mpls>
        </bgp-ipvpn>
      </vprn>
    </service>
  </configure>
</config>"""
        
        return xml_template.strip()
    
    def _generate_juniper_l3vpn_xml(self, intent: NormalizedIntent, device: Dict[str, Any]) -> str:
        """Generate Juniper Junos L3VPN XML configuration"""
        
        vrf_name = self._extract_vrf_name(intent)
        
        xml_template = f"""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <configuration xmlns="http://xml.juniper.net/xnm/1.1/xnm">
    <routing-instances>
      <instance>
        <name>{vrf_name}</name>
        <instance-type>vrf</instance-type>
        <route-distinguisher>
          <rd-type>{device.get('bgp_asn', '65000')}:{device.get('device_id', '1')}</rd-type>
        </route-distinguisher>
        <vrf-target>
          <community>target:{device.get('bgp_asn', '65000')}:{device.get('device_id', '1')}</community>
        </vrf-target>
        <vrf-table-label/>
        <protocols>
          <bgp>
            <group>
              <name>ibgp</name>
              <type>internal</type>
              <family>
                <inet-vpn>
                  <unicast/>
                </inet-vpn>
              </family>
            </group>
          </bgp>
        </protocols>
      </instance>
    </routing-instances>
  </configuration>
</config>"""
        
        return xml_template.strip()
    
    def _generate_openconfig_l3vpn_xml(self, intent: NormalizedIntent, device: Dict[str, Any]) -> str:
        """Generate OpenConfig L3VPN XML configuration"""
        
        vrf_name = self._extract_vrf_name(intent)
        
        xml_template = f"""
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <network-instances xmlns="http://openconfig.net/yang/network-instance">
    <network-instance>
      <name>{vrf_name}</name>
      <config>
        <name>{vrf_name}</name>
        <type xmlns:oc-ni-types="http://openconfig.net/yang/network-instance-types">oc-ni-types:L3VRF</type>
        <description>L3VPN service for {vrf_name}</description>
        <route-distinguisher>{device.get('bgp_asn', '65000')}:{device.get('device_id', '1')}</route-distinguisher>
      </config>
      <inter-instance-policies>
        <apply-policy>
          <config>
            <import-policy>IMPORT_{vrf_name.upper()}</import-policy>
            <export-policy>EXPORT_{vrf_name.upper()}</export-policy>
          </config>
        </apply-policy>
      </inter-instance-policies>
    </network-instance>
  </network-instances>
</config>"""
        
        return xml_template.strip()
    
    def _generate_evpn_netconf(self, intent: NormalizedIntent, mapping: MappingEntry, device: Dict[str, Any]) -> str:
        """Generate EVPN NETCONF configuration"""
        return "<config><!-- EVPN config --></config>"
    
    def _generate_bgp_netconf(self, intent: NormalizedIntent, mapping: MappingEntry, device: Dict[str, Any]) -> str:
        """Generate BGP NETCONF configuration"""
        return "<config><!-- BGP config --></config>"
    
    def _generate_generic_netconf(self, intent: NormalizedIntent, mapping: MappingEntry, device: Dict[str, Any]) -> str:
        """Generate generic NETCONF configuration"""
        return "<config><!-- Generic config --></config>"
    
    def _generate_restconf_payload(self, intent: NormalizedIntent, mapping: MappingEntry, device: Dict[str, Any]) -> str:
        """Generate RESTCONF JSON payload"""
        
        payload = {
            "ietf-restconf:data": {
                "example-config": {
                    "service-type": intent.service_type.value,
                    "endpoints": [
                        {
                            "device": ep.device,
                            "interface": ep.interface
                        } for ep in intent.endpoints
                    ]
                }
            }
        }
        
        return json.dumps(payload, indent=2)
    
    def _generate_gnmi_payload(self, intent: NormalizedIntent, mapping: MappingEntry, device: Dict[str, Any]) -> str:
        """Generate gNMI Set payload"""
        
        payload = {
            "prefix": {
                "elem": [
                    {"name": "network-instances"},
                    {"name": "network-instance", "key": {"name": self._extract_vrf_name(intent)}}
                ]
            },
            "update": [
                {
                    "path": {
                        "elem": [{"name": "config"}, {"name": "type"}]
                    },
                    "val": {
                        "string_val": "L3VRF"
                    }
                }
            ]
        }
        
        return json.dumps(payload, indent=2)
    
    def _generate_prechecks(self, mapping: MappingEntry, device: Dict[str, Any]) -> List[str]:
        """Generate prechecks for the configuration"""
        
        prechecks = [
            f"capability:urn:ietf:params:netconf:capability:candidate:1.0",
            f"capability:urn:ietf:params:netconf:capability:validate:1.0"
        ]
        
        if mapping.vendor == Vendor.CISCO:
            prechecks.append("feature:bgp-vpnv4")
        elif mapping.vendor == Vendor.NOKIA:
            prechecks.append("feature:service-vprn")
        
        return prechecks
    
    def _generate_post_validation(
        self, 
        intent: NormalizedIntent, 
        mapping: MappingEntry, 
        device: Dict[str, Any]
    ) -> List[str]:
        """Generate post-configuration validation checks"""
        
        validations = []
        
        if intent.service_type == ServiceType.L3VPN:
            vrf_name = self._extract_vrf_name(intent)
            validations.extend([
                f"get-config filter: //*[local-name()='vrf' and text()='{vrf_name}']",
                f"operational check: VRF {vrf_name} routing table exists",
                f"bgp check: VPNv4 routes for VRF {vrf_name}"
            ])
        
        if intent.policy and intent.policy.bfd:
            validations.append("bfd check: sessions established")
        
        return validations
    
    def _extract_vrf_name(self, intent: NormalizedIntent) -> str:
        """Extract VRF name from intent"""
        
        if intent.endpoints and intent.endpoints[0].tags:
            for tag in intent.endpoints[0].tags:
                if tag.startswith('vrf:'):
                    return tag[4:]
        
        return f"VRF_{intent.service_type.value.upper()}"
    
    def _generate_rd(self, device: Dict[str, Any]) -> str:
        """Generate Route Distinguisher"""
        asn = device.get('bgp_asn', '65000')
        device_id = device.get('device_id', '1')
        return f"{asn}:{device_id}"
    
    def _generate_rt(self, device: Dict[str, Any]) -> str:
        """Generate Route Target"""
        asn = device.get('bgp_asn', '65000')
        device_id = device.get('device_id', '1')
        return f"target:{asn}:{device_id}"
    
    def _load_templates(self) -> Dict[str, ConfigTemplate]:
        """Load configuration templates"""
        return {}
    
    def _initialize_namespaces(self) -> Dict[str, str]:
        """Initialize XML namespace mappings"""
        return {
            'cisco-xr': 'http://cisco.com/ns/yang/',
            'nokia-sros': 'urn:nokia.com:sros:ns:yang:sr:conf',
            'junos': 'http://xml.juniper.net/xnm/1.1/xnm',
            'openconfig': 'http://openconfig.net/yang/',
            'ietf': 'urn:ietf:params:xml:ns:yang:'
        }