import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
import json

from .base_llm import BaseLLM, LLMConfig, LLMMessage, LLMResponse

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not available. Install with: pip install openai")


class OpenAIProvider(BaseLLM):
    """
    OpenAI LLM Provider for GPT models
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package is required. Install with: pip install openai")
        
        api_key = config.provider_specific.get('api_key')
        api_base = config.provider_specific.get('api_base')
        
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=api_base
        )
    
    async def generate(
        self, 
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        """Generate response using OpenAI API"""
        
        try:
            openai_messages = self._format_messages(messages)
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=openai_messages,
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                top_p=kwargs.get('top_p', self.config.top_p),
                frequency_penalty=kwargs.get('frequency_penalty', self.config.frequency_penalty),
                presence_penalty=kwargs.get('presence_penalty', self.config.presence_penalty),
                stop=kwargs.get('stop_sequences', self.config.stop_sequences)
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                finish_reason=response.choices[0].finish_reason,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            )
            
        except Exception as e:
            logging.error(f"OpenAI generation failed: {e}")
            raise
    
    async def generate_stream(
        self, 
        messages: List[LLMMessage],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI API"""
        
        try:
            openai_messages = self._format_messages(messages)
            
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=openai_messages,
                temperature=kwargs.get('temperature', self.config.temperature),
                max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logging.error(f"OpenAI streaming generation failed: {e}")
            raise
    
    def _format_messages(self, messages: List[LLMMessage]) -> List[Dict[str, str]]:
        """Format messages for OpenAI API"""
        
        return [
            {
                "role": message.role,
                "content": message.content
            }
            for message in messages
        ]
    
    def validate_config(self) -> bool:
        """Validate OpenAI provider configuration"""
        
        try:
            if not OPENAI_AVAILABLE:
                return False
            
            if not self.config.model:
                return False
            
            if not hasattr(self.client, '_api_key') or not self.client._api_key:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models"""
        
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        
        return len(text.split()) * 1.3
    
    @property
    def provider_name(self) -> str:
        return "OpenAI"
    
    async def list_models(self) -> List[str]:
        """List available models from OpenAI API"""
        
        try:
            models = await self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logging.error(f"Failed to list OpenAI models: {e}")
            return self.get_available_models()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on OpenAI provider"""
        
        health = {
            'status': 'healthy',
            'openai_available': OPENAI_AVAILABLE,
            'api_key_set': bool(self.client._api_key),
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