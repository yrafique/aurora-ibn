import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
import json
import os
from pathlib import Path

from .base_llm import BaseLLM, LLMConfig, LLMMessage, LLMResponse

try:
    import mlx.core as mx
    import mlx.nn as nn
    from mlx_lm import load, generate, stream_generate
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False
    logging.warning("MLX not available. Install with: pip install mlx-lm")


class MLXProvider(BaseLLM):
    """
    MLX LLM Provider for Apple Silicon Macs
    Optimized for local model execution with Metal Performance Shaders
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if not MLX_AVAILABLE:
            raise ImportError("MLX is required for MLXProvider. Install with: pip install mlx-lm")
        
        self.model = None
        self.tokenizer = None
        self.cache_dir = Path(config.provider_specific.get('offload_folder', '~/.aurora-ibn/mlx-cache')).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_model()
    
    def _load_model(self):
        """Load MLX model and tokenizer"""
        try:
            logging.info(f"Loading MLX model: {self.config.model}")
            
            model_path = self.cache_dir / self.config.model.replace('/', '_')
            
            if model_path.exists():
                logging.info(f"Loading cached model from {model_path}")
                self.model, self.tokenizer = load(str(model_path))
            else:
                logging.info(f"Downloading model {self.config.model}")
                self.model, self.tokenizer = load(self.config.model)
                
                logging.info(f"Caching model to {model_path}")
                model_path.mkdir(parents=True, exist_ok=True)
            
            logging.info(f"MLX model loaded successfully: {self.config.model}")
            
        except Exception as e:
            logging.error(f"Failed to load MLX model {self.config.model}: {e}")
            raise
    
    async def generate(
        self, 
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        """Generate response using MLX model"""
        
        try:
            prompt = self._format_messages(messages)
            
            max_tokens = kwargs.get('max_tokens', self.config.max_tokens) or 4096
            temperature = kwargs.get('temperature', self.config.temperature)
            
            response_text = await asyncio.get_event_loop().run_in_executor(
                None,
                self._generate_sync,
                prompt,
                max_tokens,
                temperature
            )
            
            return LLMResponse(
                content=response_text,
                model=self.config.model,
                finish_reason="stop",
                usage={
                    'prompt_tokens': self.estimate_tokens(prompt),
                    'completion_tokens': self.estimate_tokens(response_text),
                    'total_tokens': self.estimate_tokens(prompt + response_text)
                }
            )
            
        except Exception as e:
            logging.error(f"MLX generation failed: {e}")
            raise
    
    async def generate_stream(
        self, 
        messages: List[LLMMessage],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response using MLX model"""
        
        try:
            prompt = self._format_messages(messages)
            
            max_tokens = kwargs.get('max_tokens', self.config.max_tokens) or 4096
            temperature = kwargs.get('temperature', self.config.temperature)
            
            for token in stream_generate(
                self.model,
                self.tokenizer,
                prompt,
                max_tokens=max_tokens,
                temp=temperature
            ):
                yield token
                
        except Exception as e:
            logging.error(f"MLX streaming generation failed: {e}")
            raise
    
    def _generate_sync(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Synchronous generation wrapper for MLX"""
        
        response = generate(
            self.model,
            self.tokenizer,
            prompt,
            max_tokens=max_tokens,
            temp=temperature,
            verbose=False
        )
        
        return response
    
    def _format_messages(self, messages: List[LLMMessage]) -> str:
        """Format messages for MLX model input"""
        
        formatted_parts = []
        
        for message in messages:
            if message.role == "system":
                formatted_parts.append(f"<|system|>\n{message.content}\n")
            elif message.role == "user":
                formatted_parts.append(f"<|user|>\n{message.content}\n")
            elif message.role == "assistant":
                formatted_parts.append(f"<|assistant|>\n{message.content}\n")
        
        formatted_parts.append("<|assistant|>\n")
        
        return "".join(formatted_parts)
    
    def validate_config(self) -> bool:
        """Validate MLX provider configuration"""
        
        try:
            if not MLX_AVAILABLE:
                return False
            
            if not self.config.model:
                return False
            
            if not mx.metal.is_available():
                logging.warning("Metal is not available, MLX performance will be reduced")
                return False
            
            if self.model is None or self.tokenizer is None:
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"MLX config validation failed: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of recommended MLX models"""
        
        return [
            "mlx-community/Llama-3.2-1B-Instruct-4bit",
            "mlx-community/Llama-3.2-3B-Instruct-4bit", 
            "mlx-community/Llama-3.1-8B-Instruct-4bit",
            "mlx-community/Meta-Llama-3-8B-Instruct-4bit",
            "mlx-community/CodeLlama-7B-Instruct-4bit",
            "mlx-community/Mistral-7B-Instruct-v0.2-4bit",
            "mlx-community/gemma-2-2b-it-4bit",
            "mlx-community/Phi-3-mini-4k-instruct-4bit"
        ]
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        
        if self.tokenizer is None:
            return len(text.split()) * 1.3
        
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except Exception:
            return len(text.split()) * 1.3
    
    @property
    def provider_name(self) -> str:
        return "MLX"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information"""
        
        info = {
            'provider': self.provider_name,
            'model': self.config.model,
            'cache_dir': str(self.cache_dir),
            'metal_available': mx.metal.is_available() if MLX_AVAILABLE else False,
            'model_loaded': self.model is not None
        }
        
        if MLX_AVAILABLE and mx.metal.is_available():
            try:
                info['metal_memory'] = mx.metal.get_active_memory() / (1024**3)  # GB
                info['metal_peak_memory'] = mx.metal.get_peak_memory() / (1024**3)  # GB
            except Exception:
                pass
        
        return info
    
    def clear_cache(self):
        """Clear MLX model cache"""
        
        try:
            import shutil
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logging.info("MLX cache cleared")
        except Exception as e:
            logging.error(f"Failed to clear MLX cache: {e}")
    
    def optimize_for_inference(self):
        """Optimize model for inference performance"""
        
        if not MLX_AVAILABLE or self.model is None:
            return
        
        try:
            mx.eval(self.model.parameters())
            mx.metal.clear_cache()
            logging.info("MLX model optimized for inference")
        except Exception as e:
            logging.warning(f"MLX optimization failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on MLX provider"""
        
        health = {
            'status': 'healthy',
            'mlx_available': MLX_AVAILABLE,
            'metal_available': mx.metal.is_available() if MLX_AVAILABLE else False,
            'model_loaded': self.model is not None,
            'tokenizer_loaded': self.tokenizer is not None
        }
        
        try:
            test_message = [LLMMessage(role="user", content="Test")]
            response = await self.generate(test_message)
            health['test_generation'] = len(response.content) > 0
        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)
            health['test_generation'] = False
        
        return health