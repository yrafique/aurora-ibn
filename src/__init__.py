"""
AURORA-IBN: Intent-Based Networking System
Multi-vendor network automation with YANG model discovery and normalization
"""

__version__ = "1.0.0"
__author__ = "AURORA-IBN Team"

from .core.intent_processor import IntentProcessor
from .core.model_discovery import ModelDiscovery
from .core.config_generator import ConfigGenerator
from .core.validation_engine import ValidationEngine

__all__ = [
    "IntentProcessor",
    "ModelDiscovery", 
    "ConfigGenerator",
    "ValidationEngine"
]