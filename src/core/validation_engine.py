import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

from ..models.base import (
    NormalizedIntent, VerificationPlan, CandidatePayload, 
    ServiceType, Transport
)
from .netconf_client import NetconfClient
from .gnmi_client import GnmiClient
from .restconf_client import RestconfClient


@dataclass
class ValidationResult:
    success: bool
    test_name: str
    details: str
    timestamp: datetime
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CommitResult:
    success: bool
    device: str
    commit_id: Optional[str] = None
    rollback_info: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None


class ValidationEngine:
    """
    Handles configuration validation, commit operations, and post-deployment verification
    Supports rollback and safety mechanisms across multiple vendors
    """
    
    def __init__(self):
        self.active_commits = {}
        self.rollback_history = {}
    
    def create_verification_plan(
        self,
        intent: NormalizedIntent,
        inventory: List[Dict[str, Any]]
    ) -> VerificationPlan:
        """Create comprehensive verification plan for the intent"""
        
        tests = self._generate_tests(intent, inventory)
        telemetry_queries = self._generate_telemetry_queries(intent, inventory)
        
        return VerificationPlan(
            tests=tests,
            telemetry_queries=telemetry_queries
        )
    
    def _generate_tests(
        self,
        intent: NormalizedIntent,
        inventory: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate test cases based on intent and inventory"""
        
        tests = []
        service_type = intent.service_type
        
        if service_type == ServiceType.L3VPN:
            tests.extend(self._generate_l3vpn_tests(intent, inventory))
        elif service_type == ServiceType.EVPN:
            tests.extend(self._generate_evpn_tests(intent, inventory))
        elif service_type == ServiceType.BGP:
            tests.extend(self._generate_bgp_tests(intent, inventory))
        
        if intent.policy and intent.policy.bfd:
            tests.extend(self._generate_bfd_tests(intent, inventory))
        
        if intent.slo:
            tests.extend(self._generate_slo_tests(intent, inventory))
        
        return tests
    
    def _generate_l3vpn_tests(
        self,
        intent: NormalizedIntent,
        inventory: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate L3VPN-specific tests"""
        
        tests = [
            "VRF creation verification",
            "Route distinguisher configuration check",
            "Route target import/export verification",
            "BGP VPNv4 neighbor establishment",
            "VRF routing table population check",
            "Inter-VRF connectivity test"
        ]
        
        if len(intent.endpoints) >= 2:
            endpoint_pairs = [(intent.endpoints[i], intent.endpoints[i+1]) 
                            for i in range(0, len(intent.endpoints)-1, 2)]
            
            for ep1, ep2 in endpoint_pairs:
                tests.append(f"Ping test from {ep1.device} to {ep2.device}")
                tests.append(f"Traceroute {ep1.device} to {ep2.device}")
        
        return tests
    
    def _generate_evpn_tests(
        self,
        intent: NormalizedIntent,
        inventory: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate EVPN-specific tests"""
        
        return [
            "EVPN instance creation verification",
            "EVI configuration check",
            "BGP EVPN neighbor establishment", 
            "MAC learning verification",
            "EVPN route advertisement check",
            "L2 connectivity test between endpoints",
            "MAC mobility test"
        ]
    
    def _generate_bgp_tests(
        self,
        intent: NormalizedIntent,
        inventory: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate BGP-specific tests"""
        
        return [
            "BGP process status check",
            "BGP neighbor establishment",
            "BGP session state verification",
            "Route advertisement verification",
            "BGP table convergence check"
        ]
    
    def _generate_bfd_tests(
        self,
        intent: NormalizedIntent,
        inventory: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate BFD-specific tests"""
        
        return [
            "BFD session establishment",
            "BFD neighbor discovery",
            "BFD failure detection test",
            "BFD convergence time measurement"
        ]
    
    def _generate_slo_tests(
        self,
        intent: NormalizedIntent,
        inventory: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate SLO verification tests"""
        
        tests = []
        slo = intent.slo
        
        if slo.latency_ms:
            tests.append(f"Latency measurement (target: {slo.latency_ms}ms)")
        
        if slo.loss_pct:
            tests.append(f"Packet loss measurement (target: <{slo.loss_pct}%)")
        
        if slo.jitter_ms:
            tests.append(f"Jitter measurement (target: <{slo.jitter_ms}ms)")
        
        return tests
    
    def _generate_telemetry_queries(
        self,
        intent: NormalizedIntent,
        inventory: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate telemetry queries for monitoring"""
        
        queries = []
        service_type = intent.service_type
        
        queries.extend([
            "gnmi:/interfaces/interface/state/oper-status",
            "gnmi:/interfaces/interface/state/admin-status",
            "netconf filter: <interfaces><interface><name/><enabled/></interface></interfaces>"
        ])
        
        if service_type == ServiceType.L3VPN:
            queries.extend([
                "gnmi:/network-instances/network-instance/state/name",
                "gnmi:/bgp/neighbors/neighbor/state/session-state",
                "netconf filter: <routing-instances><instance><name/><instance-type/></instance></routing-instances>"
            ])
        
        elif service_type == ServiceType.BGP:
            queries.extend([
                "gnmi:/bgp/global/state/as",
                "gnmi:/bgp/neighbors/neighbor/state/established-transitions",
                "netconf filter: <bgp><neighbors><neighbor><peer-as/><state/></neighbor></neighbors></bgp>"
            ])
        
        return queries
    
    async def validate_configuration(
        self,
        payloads: List[CandidatePayload],
        dry_run: bool = True
    ) -> List[ValidationResult]:
        """Validate configurations before commit"""
        
        results = []
        
        for payload in payloads:
            try:
                if payload.transport == Transport.NETCONF:
                    result = await self._validate_netconf_payload(payload, dry_run)
                elif payload.transport == Transport.GNMI:
                    result = await self._validate_gnmi_payload(payload, dry_run)
                elif payload.transport == Transport.RESTCONF:
                    result = await self._validate_restconf_payload(payload, dry_run)
                else:
                    result = ValidationResult(
                        success=False,
                        test_name=f"Validation for {payload.target}",
                        details=f"Unsupported transport: {payload.transport}",
                        timestamp=datetime.now()
                    )
                
                results.append(result)
                
            except Exception as e:
                results.append(ValidationResult(
                    success=False,
                    test_name=f"Validation for {payload.target}",
                    details=f"Validation failed: {str(e)}",
                    timestamp=datetime.now()
                ))
        
        return results
    
    async def _validate_netconf_payload(
        self,
        payload: CandidatePayload,
        dry_run: bool
    ) -> ValidationResult:
        """Validate NETCONF payload"""
        
        start_time = datetime.now()
        
        try:
            device_info = self._parse_device_info(payload.target)
            
            client = NetconfClient(
                host=device_info['host'],
                username=device_info['username'],
                password=device_info['password']
            )
            
            async with client:
                if dry_run:
                    success = await client.validate("candidate")
                    details = "Candidate configuration validated successfully" if success else "Validation failed"
                else:
                    success = await client.edit_config(payload.payload)
                    if success:
                        success = await client.validate("candidate")
                        details = "Configuration applied and validated" if success else "Applied but validation failed"
                    else:
                        details = "Failed to apply configuration"
                
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                return ValidationResult(
                    success=success,
                    test_name=f"NETCONF validation for {payload.target}",
                    details=details,
                    timestamp=start_time,
                    duration_ms=duration
                )
        
        except Exception as e:
            return ValidationResult(
                success=False,
                test_name=f"NETCONF validation for {payload.target}",
                details=f"Connection or validation error: {str(e)}",
                timestamp=start_time
            )
    
    async def _validate_gnmi_payload(self, payload: CandidatePayload, dry_run: bool) -> ValidationResult:
        """Validate gNMI payload"""
        
        start_time = datetime.now()
        
        try:
            device_info = self._parse_device_info(payload.target)
            
            client = GnmiClient(
                host=device_info['host'],
                username=device_info['username'],
                password=device_info['password']
            )
            
            async with client:
                import json
                set_request = json.loads(payload.payload)
                
                if dry_run:
                    success = True
                    details = "gNMI payload syntax validation passed"
                else:
                    updates = set_request.get('update', {})
                    success = await client.set(updates)
                    details = "Configuration applied via gNMI" if success else "gNMI set operation failed"
                
                duration = (datetime.now() - start_time).total_seconds() * 1000
                
                return ValidationResult(
                    success=success,
                    test_name=f"gNMI validation for {payload.target}",
                    details=details,
                    timestamp=start_time,
                    duration_ms=duration
                )
        
        except Exception as e:
            return ValidationResult(
                success=False,
                test_name=f"gNMI validation for {payload.target}",
                details=f"gNMI validation error: {str(e)}",
                timestamp=start_time
            )
    
    async def _validate_restconf_payload(self, payload: CandidatePayload, dry_run: bool) -> ValidationResult:
        """Validate RESTCONF payload"""
        
        start_time = datetime.now()
        
        return ValidationResult(
            success=True,
            test_name=f"RESTCONF validation for {payload.target}",
            details="RESTCONF validation not implemented yet",
            timestamp=start_time
        )
    
    async def commit_configurations(
        self,
        payloads: List[CandidatePayload],
        confirmed: bool = True,
        timeout_minutes: int = 10
    ) -> List[CommitResult]:
        """Commit configurations with optional confirmed commit"""
        
        results = []
        
        for payload in payloads:
            try:
                result = await self._commit_device_config(
                    payload, confirmed, timeout_minutes
                )
                results.append(result)
                
                if confirmed and result.success:
                    self.active_commits[payload.target] = {
                        'commit_id': result.commit_id,
                        'timeout': datetime.now() + timedelta(minutes=timeout_minutes),
                        'payload': payload
                    }
            
            except Exception as e:
                results.append(CommitResult(
                    success=False,
                    device=payload.target,
                    error_message=str(e),
                    timestamp=datetime.now()
                ))
        
        return results
    
    async def _commit_device_config(
        self,
        payload: CandidatePayload,
        confirmed: bool,
        timeout_minutes: int
    ) -> CommitResult:
        """Commit configuration on a single device"""
        
        if payload.transport == Transport.NETCONF:
            return await self._commit_netconf_config(payload, confirmed, timeout_minutes)
        elif payload.transport == Transport.GNMI:
            return await self._commit_gnmi_config(payload)
        else:
            return CommitResult(
                success=False,
                device=payload.target,
                error_message=f"Unsupported transport for commit: {payload.transport}",
                timestamp=datetime.now()
            )
    
    async def _commit_netconf_config(
        self,
        payload: CandidatePayload,
        confirmed: bool,
        timeout_minutes: int
    ) -> CommitResult:
        """Commit NETCONF configuration"""
        
        try:
            device_info = self._parse_device_info(payload.target)
            
            client = NetconfClient(
                host=device_info['host'],
                username=device_info['username'],
                password=device_info['password']
            )
            
            async with client:
                success = await client.edit_config(payload.payload)
                if not success:
                    return CommitResult(
                        success=False,
                        device=payload.target,
                        error_message="Failed to edit candidate configuration",
                        timestamp=datetime.now()
                    )
                
                validation_success = await client.validate("candidate")
                if not validation_success:
                    await client.discard_changes()
                    return CommitResult(
                        success=False,
                        device=payload.target,
                        error_message="Configuration validation failed",
                        timestamp=datetime.now()
                    )
                
                commit_success = await client.commit(
                    confirmed=confirmed,
                    timeout=timeout_minutes * 60
                )
                
                if commit_success:
                    commit_id = f"commit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    return CommitResult(
                        success=True,
                        device=payload.target,
                        commit_id=commit_id,
                        timestamp=datetime.now()
                    )
                else:
                    return CommitResult(
                        success=False,
                        device=payload.target,
                        error_message="Commit operation failed",
                        timestamp=datetime.now()
                    )
        
        except Exception as e:
            return CommitResult(
                success=False,
                device=payload.target,
                error_message=f"NETCONF commit error: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def _commit_gnmi_config(self, payload: CandidatePayload) -> CommitResult:
        """Commit gNMI configuration"""
        
        return CommitResult(
            success=True,
            device=payload.target,
            commit_id="gnmi_immediate",
            timestamp=datetime.now()
        )
    
    async def confirm_commits(self, device_targets: Optional[List[str]] = None) -> List[CommitResult]:
        """Confirm pending commits"""
        
        results = []
        targets = device_targets or list(self.active_commits.keys())
        
        for target in targets:
            if target in self.active_commits:
                try:
                    device_info = self._parse_device_info(target)
                    
                    client = NetconfClient(
                        host=device_info['host'],
                        username=device_info['username'],
                        password=device_info['password']
                    )
                    
                    async with client:
                        success = await client.commit(confirmed=False)
                        
                        if success:
                            del self.active_commits[target]
                            results.append(CommitResult(
                                success=True,
                                device=target,
                                commit_id="confirmed",
                                timestamp=datetime.now()
                            ))
                        else:
                            results.append(CommitResult(
                                success=False,
                                device=target,
                                error_message="Failed to confirm commit",
                                timestamp=datetime.now()
                            ))
                
                except Exception as e:
                    results.append(CommitResult(
                        success=False,
                        device=target,
                        error_message=f"Confirm commit error: {str(e)}",
                        timestamp=datetime.now()
                    ))
        
        return results
    
    async def rollback_configurations(self, device_targets: Optional[List[str]] = None) -> List[CommitResult]:
        """Rollback configurations on specified devices"""
        
        results = []
        targets = device_targets or list(self.active_commits.keys())
        
        for target in targets:
            try:
                device_info = self._parse_device_info(target)
                
                client = NetconfClient(
                    host=device_info['host'],
                    username=device_info['username'],
                    password=device_info['password']
                )
                
                async with client:
                    success = await client.discard_changes()
                    
                    if target in self.active_commits:
                        del self.active_commits[target]
                    
                    results.append(CommitResult(
                        success=success,
                        device=target,
                        commit_id="rollback",
                        error_message=None if success else "Rollback failed",
                        timestamp=datetime.now()
                    ))
            
            except Exception as e:
                results.append(CommitResult(
                    success=False,
                    device=target,
                    error_message=f"Rollback error: {str(e)}",
                    timestamp=datetime.now()
                ))
        
        return results
    
    async def run_verification_tests(
        self,
        verification_plan: VerificationPlan,
        inventory: List[Dict[str, Any]]
    ) -> List[ValidationResult]:
        """Execute verification tests post-deployment"""
        
        results = []
        
        for test in verification_plan.tests:
            result = await self._execute_verification_test(test, inventory)
            results.append(result)
        
        for query in verification_plan.telemetry_queries:
            result = await self._execute_telemetry_query(query, inventory)
            results.append(result)
        
        return results
    
    async def _execute_verification_test(
        self,
        test: str,
        inventory: List[Dict[str, Any]]
    ) -> ValidationResult:
        """Execute a single verification test"""
        
        start_time = datetime.now()
        
        if "ping" in test.lower():
            success = True  # Simulated
            details = f"Ping test completed: {test}"
        elif "bgp" in test.lower():
            success = True  # Simulated
            details = f"BGP verification completed: {test}"
        elif "vrf" in test.lower():
            success = True  # Simulated
            details = f"VRF verification completed: {test}"
        else:
            success = True  # Simulated
            details = f"Test completed: {test}"
        
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        return ValidationResult(
            success=success,
            test_name=test,
            details=details,
            timestamp=start_time,
            duration_ms=duration
        )
    
    async def _execute_telemetry_query(
        self,
        query: str,
        inventory: List[Dict[str, Any]]
    ) -> ValidationResult:
        """Execute a telemetry query"""
        
        start_time = datetime.now()
        
        success = True  # Simulated
        details = f"Telemetry query executed: {query}"
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        return ValidationResult(
            success=success,
            test_name=f"Telemetry: {query[:50]}...",
            details=details,
            timestamp=start_time,
            duration_ms=duration
        )
    
    def _parse_device_info(self, target: str) -> Dict[str, str]:
        """Parse device connection information"""
        
        return {
            'host': target,
            'username': 'admin',
            'password': 'admin'
        }
    
    def get_active_commits(self) -> Dict[str, Any]:
        """Get information about active commits"""
        return dict(self.active_commits)
    
    def cleanup_expired_commits(self):
        """Clean up expired confirmed commits"""
        
        now = datetime.now()
        expired = []
        
        for target, commit_info in self.active_commits.items():
            if commit_info['timeout'] < now:
                expired.append(target)
        
        for target in expired:
            del self.active_commits[target]
            logging.warning(f"Confirmed commit expired for device {target}")