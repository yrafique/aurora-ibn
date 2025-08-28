import asyncio
import asyncssh
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging


@dataclass
class NetconfCapability:
    uri: str
    module: Optional[str] = None
    revision: Optional[str] = None


class NetconfClient:
    def __init__(
        self,
        host: str,
        port: int = 830,
        username: str = None,
        password: str = None,
        timeout: int = 30
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session = None
        self.message_id = 1
        self.capabilities = []
        
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    async def connect(self):
        try:
            self.conn = await asyncssh.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                known_hosts=None,
                client_keys=None
            )
            
            self.session = await self.conn.create_session(
                'netconf',
                encoding='utf-8'
            )
            
            await self._exchange_hello()
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}")
    
    async def disconnect(self):
        if self.session:
            await self._send_close_session()
            self.session.close()
        
        if hasattr(self, 'conn'):
            self.conn.close()
    
    async def _exchange_hello(self):
        hello_msg = self._build_hello()
        await self.session.stdin.write(hello_msg + ']]>]]>')
        await self.session.stdin.drain()
        
        response = await self._read_response()
        self._parse_capabilities(response)
    
    def _build_hello(self) -> str:
        return """<?xml version="1.0" encoding="UTF-8"?>
<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <capabilities>
        <capability>urn:ietf:params:netconf:base:1.0</capability>
        <capability>urn:ietf:params:netconf:base:1.1</capability>
        <capability>urn:ietf:params:netconf:capability:candidate:1.0</capability>
        <capability>urn:ietf:params:netconf:capability:confirmed-commit:1.0</capability>
        <capability>urn:ietf:params:netconf:capability:validate:1.0</capability>
        <capability>urn:ietf:params:netconf:capability:xpath:1.0</capability>
    </capabilities>
</hello>"""
    
    async def _read_response(self) -> str:
        response = ""
        while True:
            try:
                data = await asyncio.wait_for(
                    self.session.stdout.read(8192),
                    timeout=self.timeout
                )
                if not data:
                    break
                response += data
                if ']]>]]>' in response:
                    break
            except asyncio.TimeoutError:
                break
        
        return response.replace(']]>]]>', '')
    
    def _parse_capabilities(self, hello_response: str):
        try:
            root = ET.fromstring(hello_response)
            ns = {'nc': 'urn:ietf:params:xml:ns:netconf:base:1.0'}
            
            cap_elements = root.findall('.//nc:capability', ns)
            
            for cap_elem in cap_elements:
                cap_text = cap_elem.text
                if cap_text:
                    capability = NetconfCapability(uri=cap_text)
                    
                    if 'module=' in cap_text:
                        module_start = cap_text.find('module=') + 7
                        module_end = cap_text.find('&', module_start)
                        if module_end == -1:
                            module_end = cap_text.find('?', module_start)
                        if module_end == -1:
                            module_end = len(cap_text)
                        capability.module = cap_text[module_start:module_end]
                    
                    if 'revision=' in cap_text:
                        rev_start = cap_text.find('revision=') + 9
                        rev_end = cap_text.find('&', rev_start)
                        if rev_end == -1:
                            rev_end = cap_text.find('?', rev_start)
                        if rev_end == -1:
                            rev_end = len(cap_text)
                        capability.revision = cap_text[rev_start:rev_end]
                    
                    self.capabilities.append(capability)
        
        except ET.ParseError as e:
            logging.warning(f"Failed to parse capabilities: {e}")
    
    async def get_capabilities(self) -> List[str]:
        return [cap.uri for cap in self.capabilities]
    
    async def get_schema(self, identifier: str, version: Optional[str] = None) -> Optional[str]:
        schema_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<rpc message-id="{self.message_id}" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <get-schema xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">
        <identifier>{identifier}</identifier>"""
        
        if version:
            schema_request += f"<version>{version}</version>"
        
        schema_request += """
    </get-schema>
</rpc>"""
        
        self.message_id += 1
        
        try:
            await self.session.stdin.write(schema_request + ']]>]]>')
            await self.session.stdin.drain()
            
            response = await self._read_response()
            return self._parse_schema_response(response)
        
        except Exception as e:
            logging.error(f"Failed to get schema for {identifier}: {e}")
            return None
    
    def _parse_schema_response(self, response: str) -> Optional[str]:
        try:
            root = ET.fromstring(response)
            ns = {
                'nc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                'mon': 'urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring'
            }
            
            error_elem = root.find('.//nc:rpc-error', ns)
            if error_elem is not None:
                return None
            
            data_elem = root.find('.//mon:data', ns)
            if data_elem is not None:
                return data_elem.text
            
            return None
        
        except ET.ParseError:
            return None
    
    async def get_config(self, source: str = "running", filter_xml: Optional[str] = None) -> Optional[str]:
        config_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<rpc message-id="{self.message_id}" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <get-config>
        <source>
            <{source}/>
        </source>"""
        
        if filter_xml:
            config_request += f"<filter>{filter_xml}</filter>"
        
        config_request += """
    </get-config>
</rpc>"""
        
        self.message_id += 1
        
        try:
            await self.session.stdin.write(config_request + ']]>]]>')
            await self.session.stdin.drain()
            
            response = await self._read_response()
            return response
        
        except Exception as e:
            logging.error(f"Failed to get config: {e}")
            return None
    
    async def edit_config(
        self,
        config_xml: str,
        target: str = "candidate",
        default_operation: str = "merge"
    ) -> bool:
        edit_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<rpc message-id="{self.message_id}" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <edit-config>
        <target>
            <{target}/>
        </target>
        <default-operation>{default_operation}</default-operation>
        <config>
            {config_xml}
        </config>
    </edit-config>
</rpc>"""
        
        self.message_id += 1
        
        try:
            await self.session.stdin.write(edit_request + ']]>]]>')
            await self.session.stdin.drain()
            
            response = await self._read_response()
            return self._check_ok_response(response)
        
        except Exception as e:
            logging.error(f"Failed to edit config: {e}")
            return False
    
    async def commit(self, confirmed: bool = False, timeout: int = 300) -> bool:
        commit_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<rpc message-id="{self.message_id}" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <commit"""
        
        if confirmed:
            commit_request += f' confirmed-timeout="{timeout}"'
        
        commit_request += """/>
</rpc>"""
        
        self.message_id += 1
        
        try:
            await self.session.stdin.write(commit_request + ']]>]]>')
            await self.session.stdin.drain()
            
            response = await self._read_response()
            return self._check_ok_response(response)
        
        except Exception as e:
            logging.error(f"Failed to commit: {e}")
            return False
    
    async def validate(self, source: str = "candidate") -> bool:
        validate_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<rpc message-id="{self.message_id}" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <validate>
        <source>
            <{source}/>
        </source>
    </validate>
</rpc>"""
        
        self.message_id += 1
        
        try:
            await self.session.stdin.write(validate_request + ']]>]]>')
            await self.session.stdin.drain()
            
            response = await self._read_response()
            return self._check_ok_response(response)
        
        except Exception as e:
            logging.error(f"Failed to validate: {e}")
            return False
    
    async def discard_changes(self) -> bool:
        discard_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<rpc message-id="{self.message_id}" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <discard-changes/>
</rpc>"""
        
        self.message_id += 1
        
        try:
            await self.session.stdin.write(discard_request + ']]>]]>')
            await self.session.stdin.drain()
            
            response = await self._read_response()
            return self._check_ok_response(response)
        
        except Exception as e:
            logging.error(f"Failed to discard changes: {e}")
            return False
    
    def _check_ok_response(self, response: str) -> bool:
        try:
            root = ET.fromstring(response)
            ns = {'nc': 'urn:ietf:params:xml:ns:netconf:base:1.0'}
            
            ok_elem = root.find('.//nc:ok', ns)
            error_elem = root.find('.//nc:rpc-error', ns)
            
            return ok_elem is not None and error_elem is None
        
        except ET.ParseError:
            return False
    
    async def _send_close_session(self):
        close_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<rpc message-id="{self.message_id}" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <close-session/>
</rpc>"""
        
        self.message_id += 1
        
        try:
            await self.session.stdin.write(close_request + ']]>]]>')
            await self.session.stdin.drain()
        except Exception:
            pass
    
    def has_capability(self, capability_uri: str) -> bool:
        return any(cap.uri == capability_uri for cap in self.capabilities)
    
    def supports_candidate(self) -> bool:
        return self.has_capability("urn:ietf:params:netconf:capability:candidate:1.0")
    
    def supports_confirmed_commit(self) -> bool:
        return self.has_capability("urn:ietf:params:netconf:capability:confirmed-commit:1.0")
    
    def supports_validate(self) -> bool:
        return self.has_capability("urn:ietf:params:netconf:capability:validate:1.0")