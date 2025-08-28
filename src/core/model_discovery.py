import asyncio
import aiohttp
import os
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

from ..models.base import ModelDiscoveryResult, Transport, Vendor
from .netconf_client import NetconfClient
from .gnmi_client import GnmiClient
from .restconf_client import RestconfClient


@dataclass
class YangModel:
    name: str
    revision: str
    namespace: str
    source: str
    content: Optional[str] = None
    dependencies: List[str] = None
    checksum: Optional[str] = None


class ModelCache:
    def __init__(self, cache_dir: str = "~/.aurora-ibn/cache"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.models_file = self.cache_dir / "models.json"
        self.models = self._load_cache()
    
    def _load_cache(self) -> Dict[str, YangModel]:
        if self.models_file.exists():
            try:
                with open(self.models_file, 'r') as f:
                    data = json.load(f)
                    return {k: YangModel(**v) for k, v in data.items()}
            except Exception:
                return {}
        return {}
    
    def save(self):
        with open(self.models_file, 'w') as f:
            data = {k: v.__dict__ for k, v in self.models.items()}
            json.dump(data, f, indent=2)
    
    def get(self, model_key: str) -> Optional[YangModel]:
        return self.models.get(model_key)
    
    def put(self, model_key: str, model: YangModel):
        self.models[model_key] = model
        self.save()
    
    def is_expired(self, model_key: str, max_age_days: int = 7) -> bool:
        model = self.models.get(model_key)
        if not model:
            return True
        
        cache_file = self.cache_dir / f"{model_key}.yang"
        if not cache_file.exists():
            return True
        
        age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        return age > timedelta(days=max_age_days)


class ModelDiscovery:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache = ModelCache(config.get('cache_dir'))
        
        self.standard_repos = {
            'openconfig': 'https://raw.githubusercontent.com/openconfig/public/master',
            'ietf': 'https://raw.githubusercontent.com/YangModels/yang/main/standard/ietf',
            'ieee': 'https://raw.githubusercontent.com/YangModels/yang/main/standard/ieee',
        }
        
        self.vendor_repos = {
            'cisco': {
                'ios-xr': 'https://raw.githubusercontent.com/YangModels/yang/main/vendor/cisco/xr',
                'ios-xe': 'https://raw.githubusercontent.com/YangModels/yang/main/vendor/cisco/xe',
                'nx-os': 'https://raw.githubusercontent.com/YangModels/yang/main/vendor/cisco/nx'
            },
            'nokia': {
                'sr-os': 'https://raw.githubusercontent.com/nokia/7x50_YangModels/master'
            },
            'juniper': {
                'junos': 'https://raw.githubusercontent.com/Juniper/yang/master'
            },
            'arista': {
                'eos': 'https://raw.githubusercontent.com/aristanetworks/yang/master'
            },
            'huawei': {
                'vrp': 'https://raw.githubusercontent.com/Huawei/yang/master'
            }
        }
    
    async def discover_models(
        self, 
        inventory: List[Dict[str, Any]], 
        intent: Any
    ) -> List[ModelDiscoveryResult]:
        tasks = []
        for device in inventory:
            task = self._discover_device_models(device, intent)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                continue
            valid_results.append(result)
        
        return valid_results
    
    async def _discover_device_models(
        self, 
        device: Dict[str, Any], 
        intent: Any
    ) -> ModelDiscoveryResult:
        device_id = device.get('device_id', device.get('hostname', 'unknown'))
        vendor = device.get('vendor', '').lower()
        
        models_found = []
        gaps = []
        source = "unknown"
        transport = Transport.NETCONF
        
        try:
            if device.get('netconf_enabled', True):
                transport = Transport.NETCONF
                models, gaps_netconf, src = await self._discover_via_netconf(device, intent)
                models_found.extend(models)
                gaps.extend(gaps_netconf)
                source = src
            
            elif device.get('gnmi_enabled', False):
                transport = Transport.GNMI
                models, gaps_gnmi, src = await self._discover_via_gnmi(device, intent)
                models_found.extend(models)
                gaps.extend(gaps_gnmi)
                source = src
            
            elif device.get('restconf_enabled', False):
                transport = Transport.RESTCONF
                models, gaps_rest, src = await self._discover_via_restconf(device, intent)
                models_found.extend(models)
                gaps.extend(gaps_rest)
                source = src
            
            else:
                models, gaps_repo = await self._discover_from_repos(vendor, intent)
                models_found.extend(models)
                gaps.extend(gaps_repo)
                source = "repository"
            
        except Exception as e:
            gaps.append(f"Discovery failed: {str(e)}")
            models, gaps_repo = await self._discover_from_repos(vendor, intent)
            models_found.extend(models)
            gaps.extend(gaps_repo)
            source = "repository-fallback"
        
        return ModelDiscoveryResult(
            target=device_id,
            transport=transport,
            models_found=list(set(models_found)),
            source=source,
            gaps=list(set(gaps))
        )
    
    async def _discover_via_netconf(
        self, 
        device: Dict[str, Any], 
        intent: Any
    ) -> Tuple[List[str], List[str], str]:
        models = []
        gaps = []
        
        try:
            client = NetconfClient(
                host=device.get('mgmt_ip'),
                port=device.get('netconf_port', 830),
                username=device.get('username'),
                password=device.get('password')
            )
            
            async with client:
                capabilities = await client.get_capabilities()
                
                for cap in capabilities:
                    if 'module=' in cap and 'revision=' in cap:
                        module_match = cap.split('module=')[1].split('&')[0]
                        revision_match = cap.split('revision=')[1].split('&')[0] if 'revision=' in cap else 'unknown'
                        models.append(f"{module_match}@{revision_match}")
                
                required_models = self._get_required_models(intent, device.get('vendor'))
                for req_model in required_models:
                    if not any(req_model.split('@')[0] in model for model in models):
                        try:
                            schema = await client.get_schema(req_model.split('@')[0])
                            if schema:
                                models.append(req_model)
                                await self._cache_schema(req_model, schema, "netconf")
                            else:
                                gaps.append(f"Schema not available: {req_model}")
                        except Exception as e:
                            gaps.append(f"Failed to get schema {req_model}: {str(e)}")
        
        except Exception as e:
            gaps.append(f"NETCONF connection failed: {str(e)}")
        
        return models, gaps, "on-device-netconf"
    
    async def _discover_via_gnmi(
        self, 
        device: Dict[str, Any], 
        intent: Any
    ) -> Tuple[List[str], List[str], str]:
        models = []
        gaps = []
        
        try:
            client = GnmiClient(
                host=device.get('mgmt_ip'),
                port=device.get('gnmi_port', 9339),
                username=device.get('username'),
                password=device.get('password')
            )
            
            capabilities = await client.get_capabilities()
            
            for model in capabilities.get('supported_models', []):
                name = model.get('name', '')
                version = model.get('version', '')
                models.append(f"{name}@{version}")
            
            required_models = self._get_required_models(intent, device.get('vendor'))
            for req_model in required_models:
                if not any(req_model.split('@')[0] in model for model in models):
                    gaps.append(f"Required model not supported: {req_model}")
        
        except Exception as e:
            gaps.append(f"gNMI connection failed: {str(e)}")
        
        return models, gaps, "on-device-gnmi"
    
    async def _discover_via_restconf(
        self, 
        device: Dict[str, Any], 
        intent: Any
    ) -> Tuple[List[str], List[str], str]:
        models = []
        gaps = []
        
        try:
            client = RestconfClient(
                host=device.get('mgmt_ip'),
                port=device.get('restconf_port', 443),
                username=device.get('username'),
                password=device.get('password')
            )
            
            modules = await client.get_modules()
            
            for module in modules:
                name = module.get('name', '')
                revision = module.get('revision', 'unknown')
                models.append(f"{name}@{revision}")
        
        except Exception as e:
            gaps.append(f"RESTCONF connection failed: {str(e)}")
        
        return models, gaps, "on-device-restconf"
    
    async def _discover_from_repos(
        self, 
        vendor: str, 
        intent: Any
    ) -> Tuple[List[str], List[str]]:
        models = []
        gaps = []
        
        required_models = self._get_required_models(intent, vendor)
        
        for model in required_models:
            cached = await self._get_from_cache_or_repo(model, vendor)
            if cached:
                models.append(model)
            else:
                gaps.append(f"Model not found in repositories: {model}")
        
        return models, gaps
    
    async def _get_from_cache_or_repo(self, model: str, vendor: str) -> Optional[str]:
        model_key = f"{vendor}_{model}"
        
        if not self.cache.is_expired(model_key):
            cached = self.cache.get(model_key)
            if cached:
                return cached.content
        
        content = await self._fetch_from_repos(model, vendor)
        if content:
            yang_model = YangModel(
                name=model.split('@')[0],
                revision=model.split('@')[1] if '@' in model else 'unknown',
                namespace='',
                source='repository',
                content=content,
                checksum=hashlib.sha256(content.encode()).hexdigest()
            )
            self.cache.put(model_key, yang_model)
            return content
        
        return None
    
    async def _fetch_from_repos(self, model: str, vendor: str) -> Optional[str]:
        model_name = model.split('@')[0]
        
        urls_to_try = []
        
        if vendor in self.vendor_repos:
            for os_variant, base_url in self.vendor_repos[vendor].items():
                urls_to_try.append(f"{base_url}/{model_name}.yang")
        
        for repo_name, base_url in self.standard_repos.items():
            urls_to_try.append(f"{base_url}/modules/{model_name}.yang")
        
        async with aiohttp.ClientSession() as session:
            for url in urls_to_try:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            return await response.text()
                except Exception:
                    continue
        
        return None
    
    def _get_required_models(self, intent: Any, vendor: Optional[str]) -> List[str]:
        models = []
        
        service_type = getattr(intent, 'service_type', None)
        if not service_type:
            return models
        
        service_name = service_type.value if hasattr(service_type, 'value') else str(service_type)
        
        if service_name == 'l3vpn':
            models.extend([
                'ietf-l3vpn-svc@2018-01-19',
                'ietf-network-instance@2019-01-21',
                'openconfig-network-instance@2021-08-24'
            ])
            
            if vendor == 'cisco':
                models.extend([
                    'Cisco-IOS-XR-mpls-vpn-cfg@2019-04-05',
                    'cisco-xr-openconfig-network-instance-deviations@2019-04-05'
                ])
            elif vendor == 'nokia':
                models.extend([
                    'nokia-conf-service@2021-09-30',
                    'nokia-state-service@2021-09-30'
                ])
            elif vendor == 'juniper':
                models.extend([
                    'junos-conf-routing-instances@2021-01-01'
                ])
        
        elif service_name in ['evpn', 'l2vpn-epipe']:
            models.extend([
                'ietf-l2vpn-svc@2020-08-24',
                'openconfig-evpn@2021-06-16',
                'ietf-evpn@2021-07-13'
            ])
        
        elif service_name == 'bgp':
            models.extend([
                'ietf-bgp@2019-03-21',
                'openconfig-bgp@2021-08-06'
            ])
        
        elif service_name in ['isis', 'ospf']:
            models.extend([
                f'ietf-{service_name}@2020-02-24',
                f'openconfig-{service_name}@2021-07-28'
            ])
        
        return models
    
    async def _cache_schema(self, model: str, content: str, source: str):
        model_key = f"{source}_{model}"
        yang_model = YangModel(
            name=model.split('@')[0],
            revision=model.split('@')[1] if '@' in model else 'unknown',
            namespace='',
            source=source,
            content=content,
            checksum=hashlib.sha256(content.encode()).hexdigest()
        )
        self.cache.put(model_key, yang_model)