import asyncio
import aiohttp
import json
import base64
from typing import Dict, List, Any, Optional
import logging


class RestconfClient:
    """
    Async RESTCONF client for network device configuration
    """
    
    def __init__(
        self,
        host: str,
        port: int = 443,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: bool = False,
        timeout: int = 30
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.base_url = f"https://{host}:{port}/restconf"
        self.session = None
        
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    async def connect(self):
        """Establish HTTP session with authentication"""
        
        connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._get_auth_headers()
        )
        
        try:
            await self._test_connection()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}")
    
    async def disconnect(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Generate authentication headers"""
        
        headers = {
            'Content-Type': 'application/yang-data+json',
            'Accept': 'application/yang-data+json'
        }
        
        if self.username and self.password:
            auth_string = f"{self.username}:{self.password}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            headers['Authorization'] = f"Basic {auth_bytes}"
        
        return headers
    
    async def _test_connection(self):
        """Test connection to RESTCONF endpoint"""
        
        try:
            async with self.session.get(f"{self.base_url}/data") as response:
                if response.status == 401:
                    raise ConnectionError("Authentication failed")
                elif response.status >= 500:
                    raise ConnectionError(f"Server error: {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Connection test failed: {e}")
    
    async def get_modules(self) -> List[Dict[str, Any]]:
        """Get available YANG modules"""
        
        try:
            url = f"{self.base_url}/data/ietf-yang-library:modules-state"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    modules_state = data.get('ietf-yang-library:modules-state', {})
                    return modules_state.get('module', [])
                else:
                    logging.warning(f"Failed to get modules: HTTP {response.status}")
                    return []
        
        except Exception as e:
            logging.error(f"Error getting modules: {e}")
            return []
    
    async def get_config(
        self,
        path: str = "",
        config_type: str = "config"
    ) -> Optional[Dict[str, Any]]:
        """Get configuration data"""
        
        try:
            if config_type == "config":
                url = f"{self.base_url}/data/{path}" if path else f"{self.base_url}/data"
            else:
                url = f"{self.base_url}/data/{path}?content=nonconfig" if path else f"{self.base_url}/data?content=nonconfig"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    return None
                else:
                    logging.warning(f"Get config failed: HTTP {response.status}")
                    return None
        
        except Exception as e:
            logging.error(f"Error getting config: {e}")
            return None
    
    async def put_config(
        self,
        path: str,
        data: Dict[str, Any]
    ) -> bool:
        """Put (create/replace) configuration data"""
        
        try:
            url = f"{self.base_url}/data/{path}"
            
            async with self.session.put(url, json=data) as response:
                return response.status in [200, 201, 204]
        
        except Exception as e:
            logging.error(f"Error putting config: {e}")
            return False
    
    async def patch_config(
        self,
        path: str,
        data: Dict[str, Any]
    ) -> bool:
        """Patch (merge) configuration data"""
        
        try:
            url = f"{self.base_url}/data/{path}"
            
            async with self.session.patch(url, json=data) as response:
                return response.status in [200, 204]
        
        except Exception as e:
            logging.error(f"Error patching config: {e}")
            return False
    
    async def post_config(
        self,
        path: str,
        data: Dict[str, Any]
    ) -> bool:
        """Post (create) configuration data"""
        
        try:
            url = f"{self.base_url}/data/{path}"
            
            async with self.session.post(url, json=data) as response:
                return response.status in [201, 204]
        
        except Exception as e:
            logging.error(f"Error posting config: {e}")
            return False
    
    async def delete_config(self, path: str) -> bool:
        """Delete configuration data"""
        
        try:
            url = f"{self.base_url}/data/{path}"
            
            async with self.session.delete(url) as response:
                return response.status in [200, 204]
        
        except Exception as e:
            logging.error(f"Error deleting config: {e}")
            return False
    
    async def get_operational(self, path: str = "") -> Optional[Dict[str, Any]]:
        """Get operational state data"""
        
        try:
            if path:
                url = f"{self.base_url}/data/{path}?content=nonconfig"
            else:
                url = f"{self.base_url}/data?content=nonconfig"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        
        except Exception as e:
            logging.error(f"Error getting operational data: {e}")
            return None
    
    async def call_rpc(
        self,
        rpc_name: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Call RESTCONF RPC operation"""
        
        try:
            url = f"{self.base_url}/operations/{rpc_name}"
            
            if input_data:
                async with self.session.post(url, json=input_data) as response:
                    if response.status in [200, 204]:
                        if response.content_length and response.content_length > 0:
                            return await response.json()
                        else:
                            return {"success": True}
                    else:
                        return None
            else:
                async with self.session.post(url) as response:
                    if response.status in [200, 204]:
                        if response.content_length and response.content_length > 0:
                            return await response.json()
                        else:
                            return {"success": True}
                    else:
                        return None
        
        except Exception as e:
            logging.error(f"Error calling RPC {rpc_name}: {e}")
            return None
    
    async def get_capabilities(self) -> List[str]:
        """Get RESTCONF capabilities"""
        
        try:
            url = f"{self.base_url}/data/ietf-restconf-monitoring:restconf-state/capabilities"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    capabilities = data.get('ietf-restconf-monitoring:capabilities', {})
                    return capabilities.get('capability', [])
                else:
                    return []
        
        except Exception as e:
            logging.error(f"Error getting capabilities: {e}")
            return []
    
    async def validate_path(self, path: str) -> bool:
        """Validate if a RESTCONF path exists"""
        
        try:
            url = f"{self.base_url}/data/{path}"
            
            async with self.session.head(url) as response:
                return response.status in [200, 404]  # 404 means path is valid but no data
        
        except Exception as e:
            logging.error(f"Error validating path {path}: {e}")
            return False
    
    async def get_yang_schema(self, module_name: str, revision: Optional[str] = None) -> Optional[str]:
        """Get YANG schema for a module"""
        
        try:
            if revision:
                url = f"{self.base_url}/yang-library-version/modules/{module_name},{revision}/module"
            else:
                url = f"{self.base_url}/yang-library-version/modules/{module_name}/module"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    return None
        
        except Exception as e:
            logging.error(f"Error getting YANG schema for {module_name}: {e}")
            return None
    
    def format_path(self, *path_segments) -> str:
        """Format RESTCONF path from segments"""
        
        formatted_segments = []
        for segment in path_segments:
            if isinstance(segment, dict):
                for key, value in segment.items():
                    formatted_segments.append(f"{key}={value}")
            else:
                formatted_segments.append(str(segment))
        
        return "/".join(formatted_segments)
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on RESTCONF connection"""
        
        health = {
            'status': 'healthy',
            'restconf_available': False,
            'authentication_valid': False,
            'modules_accessible': False
        }
        
        try:
            async with self.session.get(f"{self.base_url}/data") as response:
                health['restconf_available'] = response.status != 404
                health['authentication_valid'] = response.status != 401
            
            modules = await self.get_modules()
            health['modules_accessible'] = len(modules) > 0
            health['module_count'] = len(modules)
            
            if not all([health['restconf_available'], health['authentication_valid']]):
                health['status'] = 'unhealthy'
        
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
        
        return health