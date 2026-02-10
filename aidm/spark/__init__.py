"""Spark Layer: Swappable LLM Narration System

This module implements the Spark Adapter architecture for dynamic LLM model loading
and tier-based model selection.

Key Components:
- ModelRegistry: Parses and validates models.yaml
- SparkAdapter: Abstract interface for model loading
- LlamaCppAdapter: llama.cpp backend implementation
- HardwareTierDetector: Detects available hardware resources

Reference: docs/design/SPARK_ADAPTER_ARCHITECTURE.md
"""

from aidm.spark.model_registry import (
    ModelRegistry,
    ModelProfile,
    HardwareTier,
    TierName,
)
from aidm.spark.spark_adapter import (
    SparkAdapter,
    SparkRequest,
    SparkResponse,
    FinishReason,
    LoadedModel,
    CompatibilityReport,
    ModelLoadError,
    InsufficientResourcesError,
    NoSuitableModelError,
    NoFallbackAvailableError,
)
from aidm.spark.llamacpp_adapter import LlamaCppAdapter

__all__ = [
    # Model Registry
    "ModelRegistry",
    "ModelProfile",
    "HardwareTier",
    "TierName",
    # Spark Adapter
    "SparkAdapter",
    "SparkRequest",
    "SparkResponse",
    "FinishReason",
    "LlamaCppAdapter",
    "LoadedModel",
    "CompatibilityReport",
    # Exceptions
    "ModelLoadError",
    "InsufficientResourcesError",
    "NoSuitableModelError",
    "NoFallbackAvailableError",
]
