import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
import json

from .base_llm import BaseLLM, LLMConfig, LLMMessage, LLMResponse

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("Anthropic package not available. Install with: pip install anthropic")


class AnthropicProvider(BaseLLM):
    """
    Anthropic LLM Provider for Claude models
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package is required. Install with: pip install anthropic")
        
        api_key = config.provider_specific.get('api_key')
        
        self.client = anthropic.AsyncAnthropic(
            api_key=api_key
        )
    
    async def generate(
        self, 
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        """Generate response using Anthropic API"""
        
        try:
            system_message, user_messages = self._format_messages(messages)
            
            response = await self.client.messages.create(
                model=self.config.model,
                system=system_message,
                messages=user_messages,
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens or 4096),
                stop_sequences=kwargs.get('stop_sequences', self.config.stop_sequences)
            )
            
            content = response.content[0].text if response.content else ""
            
            return LLMResponse(
                content=content,
                model=response.model,
                finish_reason=response.stop_reason,
                usage={
                    'prompt_tokens': response.usage.input_tokens,
                    'completion_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                }
            )
            
        except Exception as e:
            logging.error(f"Anthropic generation failed: {e}")
            raise
    
    async def generate_stream(
        self, 
        messages: List[LLMMessage],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using Anthropic API"""
        
        try:
            system_message, user_messages = self._format_messages(messages)
            
            stream = await self.client.messages.create(
                model=self.config.model,
                system=system_message,
                messages=user_messages,
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens or 4096),
                stream=True
            )
            
            async for chunk in stream:
                if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                    yield chunk.delta.text
                    
        except Exception as e:
            logging.error(f"Anthropic streaming generation failed: {e}")
            raise
    
    def _format_messages(self, messages: List[LLMMessage]) -> tuple:
        """Format messages for Anthropic API"""
        
        system_message = ""
        user_messages = []
        
        for message in messages:
            if message.role == "system":
                system_message = message.content
            else:
                user_messages.append({
                    "role": message.role,
                    "content": message.content
                })
        
        return system_message, user_messages
    
    def validate_config(self) -> bool:
        """Validate Anthropic provider configuration"""
        
        try:
            if not ANTHROPIC_AVAILABLE:
                return False
            
            if not self.config.model:
                return False
            
            if not hasattr(self.client, 'api_key') or not self.client.api_key:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available Anthropic models"""
        
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0"
        ]
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        
        return len(text.split()) * 1.3
    
    @property
    def provider_name(self) -> str:
        return "Anthropic"
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Anthropic provider"""
        
        health = {
            'status': 'healthy',
            'anthropic_available': ANTHROPIC_AVAILABLE,
            'api_key_set': bool(self.client.api_key),
            'model': self.config.model
        }
        
        try:
            test_message = [LLMMessage(role="user", content="Test")]
            response = await self.generate(test_message)
            health['test_generation'] = len(response.content) > 0
            health['usage'] = response.usage
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
            health['test_generation'] = False
        
        return health