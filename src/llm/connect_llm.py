import os
import logging
from typing import Dict, Any, Optional, Type
from dataclasses import dataclass

from .base_llm import BaseLLM, LLMConfig
from .mlx_llm import MLXProvider
from .openai_llm import OpenAIProvider
from .anthropic_llm import AnthropicProvider


@dataclass
class LLMProviderConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.1
    max_tokens: Optional[int] = 4096
    provider_specific: Optional[Dict[str, Any]] = None


class LLMConnector:
    """
    Centralized LLM connection manager for easy provider switching
    """
    
    PROVIDERS = {
        'mlx': MLXProvider,
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider
    }
    
    def __init__(self, config: Optional[LLMProviderConfig] = None):
        self.config = config or self._load_default_config()
        self._provider_instance: Optional[BaseLLM] = None
    
    def _load_default_config(self) -> LLMProviderConfig:
        """Load default config from environment variables"""
        
        provider = os.getenv('AURORA_LLM_PROVIDER', 'mlx')
        model = os.getenv('AURORA_LLM_MODEL')
        api_key = os.getenv('AURORA_LLM_API_KEY')
        api_base = os.getenv('AURORA_LLM_API_BASE')
        
        if provider == 'mlx':
            model = model or 'mlx-community/Llama-3.2-3B-Instruct-4bit'
        elif provider == 'openai':
            model = model or 'gpt-4'
            api_key = api_key or os.getenv('OPENAI_API_KEY')
        elif provider == 'anthropic':
            model = model or 'claude-3-sonnet-20240229'
            api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        
        return LLMProviderConfig(
            provider=provider,
            model=model,
            api_key=api_key,
            api_base=api_base,
            temperature=float(os.getenv('AURORA_LLM_TEMPERATURE', '0.1')),
            max_tokens=int(os.getenv('AURORA_LLM_MAX_TOKENS', '4096'))
        )
    
    def get_provider(self) -> BaseLLM:
        """Get or create LLM provider instance"""
        
        if self._provider_instance is None:
            self._provider_instance = self._create_provider()
        
        return self._provider_instance
    
    def _create_provider(self) -> BaseLLM:
        """Create provider instance based on configuration"""
        
        provider_class = self.PROVIDERS.get(self.config.provider.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {self.config.provider}")
        
        llm_config = LLMConfig(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            provider_specific=self.config.provider_specific or {}
        )
        
        if self.config.api_key:
            llm_config.provider_specific['api_key'] = self.config.api_key
        
        if self.config.api_base:
            llm_config.provider_specific['api_base'] = self.config.api_base
        
        try:
            provider = provider_class(llm_config)
            if not provider.validate_config():
                raise ValueError(f"Invalid configuration for provider {self.config.provider}")
            
            logging.info(f"Initialized {provider.provider_name} with model {self.config.model}")
            return provider
            
        except Exception as e:
            logging.error(f"Failed to create provider {self.config.provider}: {e}")
            raise
    
    def switch_provider(self, new_config: LLMProviderConfig):
        """Switch to a different LLM provider"""
        
        self.config = new_config
        self._provider_instance = None
        logging.info(f"Switched to provider {new_config.provider} with model {new_config.model}")
    
    def mac_mlx_llm(
        self,
        model: str = "mlx-community/Llama-3.2-3B-Instruct-4bit",
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> BaseLLM:
        """
        Dedicated function to connect to MLX provider on Mac
        Optimized for Mac Silicon with local model execution
        """
        
        mlx_config = LLMProviderConfig(
            provider='mlx',
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            provider_specific={
                'device': 'mps',  # Use Metal Performance Shaders
                'dtype': 'float16',  # Optimize memory usage
                'max_memory': '8GB',  # Set memory limit
                'offload_folder': '~/.aurora-ibn/mlx-cache',
                'trust_remote_code': True
            }
        )
        
        self.switch_provider(mlx_config)
        provider = self.get_provider()
        
        logging.info(f"MLX provider initialized on Mac with model {model}")
        return provider
    
    def get_available_models(self) -> Dict[str, list]:
        """Get available models for all providers"""
        
        models = {}
        
        for provider_name, provider_class in self.PROVIDERS.items():
            try:
                temp_config = LLMConfig(model="dummy")
                temp_provider = provider_class(temp_config)
                models[provider_name] = temp_provider.get_available_models()
            except Exception as e:
                logging.warning(f"Could not get models for {provider_name}: {e}")
                models[provider_name] = []
        
        return models
    
    def test_connection(self) -> bool:
        """Test connection to current provider"""
        
        try:
            provider = self.get_provider()
            return provider.validate_config()
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current provider"""
        
        try:
            provider = self.get_provider()
            return {
                'provider': provider.provider_name,
                'model': self.config.model,
                'config': {
                    'temperature': self.config.temperature,
                    'max_tokens': self.config.max_tokens,
                },
                'available_models': provider.get_available_models()[:5],  # Show first 5
                'connection_valid': provider.validate_config()
            }
        except Exception as e:
            return {
                'error': str(e),
                'provider': self.config.provider,
                'model': self.config.model
            }


def create_llm_connector(
    provider: str = None,
    model: str = None,
    **kwargs
) -> LLMConnector:
    """
    Factory function to create LLM connector with optional overrides
    """
    
    if provider or model:
        config = LLMProviderConfig(
            provider=provider or 'mlx',
            model=model or 'mlx-community/Llama-3.2-3B-Instruct-4bit',
            **kwargs
        )
        return LLMConnector(config)
    
    return LLMConnector()


def get_recommended_mac_models() -> Dict[str, str]:
    """
    Get recommended MLX models for different Mac configurations
    """
    
    return {
        'low_memory': 'mlx-community/Llama-3.2-1B-Instruct-4bit',
        'balanced': 'mlx-community/Llama-3.2-3B-Instruct-4bit', 
        'high_performance': 'mlx-community/Llama-3.1-8B-Instruct-4bit',
        'max_performance': 'mlx-community/Llama-3.1-70B-Instruct-4bit'
    }