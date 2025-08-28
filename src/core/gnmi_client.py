import asyncio
import grpc
import json
from typing import Dict, List, Any, Optional
import logging

try:
    from gnmi import gnmi_pb2, gnmi_pb2_grpc
except ImportError:
    gnmi_pb2 = None
    gnmi_pb2_grpc = None
    logging.warning("gNMI protobuf modules not available. Install with: pip install gnmi-proto")


class GnmiClient:
    def __init__(
        self,
        host: str,
        port: int = 9339,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30,
        insecure: bool = True
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.insecure = insecure
        self.channel = None
        self.stub = None
        
        if gnmi_pb2 is None or gnmi_pb2_grpc is None:
            raise ImportError("gNMI protobuf modules not available")
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    async def connect(self):
        try:
            if self.insecure:
                self.channel = grpc.aio.insecure_channel(f"{self.host}:{self.port}")
            else:
                credentials = grpc.ssl_channel_credentials()
                self.channel = grpc.aio.secure_channel(f"{self.host}:{self.port}", credentials)
            
            self.stub = gnmi_pb2_grpc.gNMIStub(self.channel)
            
            await self.channel.channel_ready()
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}")
    
    async def disconnect(self):
        if self.channel:
            await self.channel.close()
    
    def _create_metadata(self) -> List[tuple]:
        metadata = []
        if self.username and self.password:
            import base64
            auth_string = f"{self.username}:{self.password}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            metadata.append(("authorization", f"Basic {auth_bytes}"))
        return metadata
    
    async def get_capabilities(self) -> Dict[str, Any]:
        try:
            request = gnmi_pb2.CapabilityRequest()
            metadata = self._create_metadata()
            
            response = await self.stub.Capabilities(
                request,
                timeout=self.timeout,
                metadata=metadata
            )
            
            capabilities = {
                "gnmi_version": response.gNMI_version,
                "supported_models": [],
                "supported_encodings": [encoding for encoding in response.supported_encodings]
            }
            
            for model in response.supported_models:
                model_info = {
                    "name": model.name,
                    "organization": model.organization,
                    "version": model.version
                }
                capabilities["supported_models"].append(model_info)
            
            return capabilities
        
        except Exception as e:
            logging.error(f"Failed to get capabilities: {e}")
            return {}
    
    def _create_path(self, path_str: str) -> gnmi_pb2.Path:
        path = gnmi_pb2.Path()
        
        if path_str.startswith('/'):
            path_str = path_str[1:]
        
        elements = path_str.split('/')
        for element in elements:
            if '[' in element and ']' in element:
                name = element.split('[')[0]
                key_part = element.split('[')[1].rstrip(']')
                
                path_elem = gnmi_pb2.PathElem()
                path_elem.name = name
                
                if '=' in key_part:
                    key, value = key_part.split('=', 1)
                    path_elem.key[key] = value.strip('"\'')
                
                path.elem.append(path_elem)
            else:
                path_elem = gnmi_pb2.PathElem()
                path_elem.name = element
                path.elem.append(path_elem)
        
        return path
    
    async def get(self, paths: List[str], encoding: str = "JSON") -> Dict[str, Any]:
        try:
            request = gnmi_pb2.GetRequest()
            
            encoding_map = {
                "JSON": gnmi_pb2.Encoding.JSON,
                "BYTES": gnmi_pb2.Encoding.BYTES,
                "PROTO": gnmi_pb2.Encoding.PROTO,
                "ASCII": gnmi_pb2.Encoding.ASCII
            }
            
            request.encoding = encoding_map.get(encoding, gnmi_pb2.Encoding.JSON)
            
            for path_str in paths:
                path = self._create_path(path_str)
                request.path.append(path)
            
            metadata = self._create_metadata()
            
            response = await self.stub.Get(
                request,
                timeout=self.timeout,
                metadata=metadata
            )
            
            results = {}
            for notification in response.notification:
                for update in notification.update:
                    path_str = self._path_to_string(update.path)
                    
                    if update.val.json_val:
                        try:
                            value = json.loads(update.val.json_val)
                        except json.JSONDecodeError:
                            value = update.val.json_val
                    elif update.val.string_val:
                        value = update.val.string_val
                    elif update.val.int_val:
                        value = update.val.int_val
                    elif update.val.uint_val:
                        value = update.val.uint_val
                    elif update.val.bool_val:
                        value = update.val.bool_val
                    elif update.val.bytes_val:
                        value = update.val.bytes_val.decode('utf-8', errors='ignore')
                    else:
                        value = str(update.val)
                    
                    results[path_str] = value
            
            return results
        
        except Exception as e:
            logging.error(f"Failed to get data: {e}")
            return {}
    
    async def set(self, updates: Dict[str, Any], deletes: Optional[List[str]] = None) -> bool:
        try:
            request = gnmi_pb2.SetRequest()
            
            for path_str, value in updates.items():
                update = gnmi_pb2.Update()
                update.path.CopyFrom(self._create_path(path_str))
                
                if isinstance(value, (dict, list)):
                    update.val.json_val = json.dumps(value).encode()
                elif isinstance(value, str):
                    update.val.string_val = value
                elif isinstance(value, int):
                    update.val.int_val = value
                elif isinstance(value, bool):
                    update.val.bool_val = value
                elif isinstance(value, float):
                    update.val.float_val = value
                else:
                    update.val.string_val = str(value)
                
                request.update.append(update)
            
            if deletes:
                for path_str in deletes:
                    path = self._create_path(path_str)
                    request.delete.append(path)
            
            metadata = self._create_metadata()
            
            response = await self.stub.Set(
                request,
                timeout=self.timeout,
                metadata=metadata
            )
            
            return len(response.response) > 0
        
        except Exception as e:
            logging.error(f"Failed to set data: {e}")
            return False
    
    async def subscribe(
        self,
        subscription_list: List[Dict[str, Any]],
        mode: str = "STREAM",
        encoding: str = "JSON"
    ):
        try:
            request = gnmi_pb2.SubscribeRequest()
            
            subscribe_list = gnmi_pb2.SubscriptionList()
            
            mode_map = {
                "STREAM": gnmi_pb2.SubscriptionList.STREAM,
                "ONCE": gnmi_pb2.SubscriptionList.ONCE,
                "POLL": gnmi_pb2.SubscriptionList.POLL
            }
            subscribe_list.mode = mode_map.get(mode, gnmi_pb2.SubscriptionList.STREAM)
            
            encoding_map = {
                "JSON": gnmi_pb2.Encoding.JSON,
                "BYTES": gnmi_pb2.Encoding.BYTES,
                "PROTO": gnmi_pb2.Encoding.PROTO
            }
            subscribe_list.encoding = encoding_map.get(encoding, gnmi_pb2.Encoding.JSON)
            
            for subscription_info in subscription_list:
                subscription = gnmi_pb2.Subscription()
                subscription.path.CopyFrom(self._create_path(subscription_info["path"]))
                
                if "sample_interval" in subscription_info:
                    subscription.sample_interval = subscription_info["sample_interval"]
                
                if "heartbeat_interval" in subscription_info:
                    subscription.heartbeat_interval = subscription_info["heartbeat_interval"]
                
                subscribe_list.subscription.append(subscription)
            
            request.subscribe.CopyFrom(subscribe_list)
            
            metadata = self._create_metadata()
            
            response_stream = self.stub.Subscribe(
                iter([request]),
                timeout=None,
                metadata=metadata
            )
            
            async for response in response_stream:
                yield self._process_subscribe_response(response)
        
        except Exception as e:
            logging.error(f"Failed to subscribe: {e}")
            return
    
    def _process_subscribe_response(self, response: gnmi_pb2.SubscribeResponse) -> Dict[str, Any]:
        result = {
            "timestamp": response.update.timestamp,
            "prefix": self._path_to_string(response.update.prefix) if response.update.prefix else "",
            "updates": {},
            "deletes": []
        }
        
        for update in response.update.update:
            path_str = self._path_to_string(update.path)
            
            if update.val.json_val:
                try:
                    value = json.loads(update.val.json_val)
                except json.JSONDecodeError:
                    value = update.val.json_val
            elif update.val.string_val:
                value = update.val.string_val
            else:
                value = str(update.val)
            
            result["updates"][path_str] = value
        
        for delete in response.update.delete:
            result["deletes"].append(self._path_to_string(delete))
        
        return result
    
    def _path_to_string(self, path: gnmi_pb2.Path) -> str:
        path_parts = []
        
        for elem in path.elem:
            if elem.key:
                keys = []
                for key, value in elem.key.items():
                    keys.append(f"{key}={value}")
                path_parts.append(f"{elem.name}[{','.join(keys)}]")
            else:
                path_parts.append(elem.name)
        
        return "/" + "/".join(path_parts)
    
    async def validate_path(self, path: str) -> bool:
        try:
            result = await self.get([path])
            return path in result or len(result) > 0
        except Exception:
            return False