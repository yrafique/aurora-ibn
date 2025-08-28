from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class LLMMessage:
    role: str  # "system", "user", "assistant"
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass 
class LLMResponse:
    content: str
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMConfig:
    model: str
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    provider_specific: Optional[Dict[str, Any]] = None


class BaseLLM(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    async def generate(
        self, 
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    async def generate_stream(
        self, 
        messages: List[LLMMessage],
        **kwargs
    ):
        """Generate a streaming response from the LLM"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the LLM configuration"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider"""
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the LLM provider"""
        pass
    
    def format_system_prompt(self, intent_context: str) -> str:
        """Format system prompt for intent processing"""
        return f"""You are AURORA-IBN, a senior intent-based networking architect with deep multi-vendor expertise.
        
Your role is to process network intents and generate validated, vendor-specific configurations.

Context: {intent_context}

You must:
1. Parse natural language intents accurately
2. Identify required YANG models and vendor capabilities  
3. Generate safe, validated configurations
4. Assess risks and provide mitigations
5. Return structured JSON responses only

Follow these principles:
- Intent-first, risk-first approach
- Model-aware normalization across vendors
- Deterministic, machine-readable outputs
- Safety through validation and rollback plans
- No hidden reasoning - provide clear rationales"""
    
    def create_intent_messages(
        self, 
        intent_text: str, 
        inventory: List[Dict[str, Any]], 
        policy: Optional[Dict[str, Any]] = None
    ) -> List[LLMMessage]:
        """Create message sequence for intent processing"""
        
        system_prompt = self.format_system_prompt(
            f"Intent: {intent_text}\nInventory: {len(inventory)} devices"
        )
        
        user_content = f"""Process this network intent:

Intent: {intent_text}

Inventory:
{self._format_inventory(inventory)}

Policy: {policy if policy else "None specified"}

Return the complete JSON response as specified in the schema."""
        
        return [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_content)
        ]
    
    def _format_inventory(self, inventory: List[Dict[str, Any]]) -> str:
        """Format inventory for LLM consumption"""
        formatted = []
        for i, device in enumerate(inventory[:10]):  # Limit to 10 devices for context
            device_info = f"Device {i+1}:"
            device_info += f"\n  - ID: {device.get('device_id', 'unknown')}"
            device_info += f"\n  - Vendor: {device.get('vendor', 'unknown')}"
            device_info += f"\n  - OS: {device.get('os_version', 'unknown')}"
            device_info += f"\n  - Management IP: {device.get('mgmt_ip', 'unknown')}"
            formatted.append(device_info)
        
        if len(inventory) > 10:
            formatted.append(f"... and {len(inventory) - 10} more devices")
        
        return "\n".join(formatted)