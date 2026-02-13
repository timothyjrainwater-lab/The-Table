"""Spark Layer: Swappable LLM Narration System

This module implements the Spark Adapter architecture for dynamic LLM model loading
and tier-based model selection.

Key Components:
- ModelRegistry: Parses and validates models.yaml
- SparkAdapter: Abstract interface for model loading
- LlamaCppAdapter: llama.cpp backend implementation
- GrammarShield: Output validation layer for LLM responses
- HardwareTierDetector: Detects available hardware resources
- DMPersona: DM personality layer for consistent narration voice

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
from aidm.spark.grammar_shield import (
    GrammarShield,
    GrammarShieldConfig,
    GrammarValidationError,
    MechanicalAssertionError,
    JsonParseError,
    SchemaValidationError,
    ValidationResult,
)
from aidm.spark.dm_persona import (
    DMPersona,
    ToneConfig,
    create_default_dm,
    create_gritty_dm,
    create_theatrical_dm,
    create_humorous_dm,
    create_terse_dm,
)

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
    # Grammar Shield
    "GrammarShield",
    "GrammarShieldConfig",
    "GrammarValidationError",
    "MechanicalAssertionError",
    "JsonParseError",
    "SchemaValidationError",
    "ValidationResult",
    # DM Persona
    "DMPersona",
    "ToneConfig",
    "create_default_dm",
    "create_gritty_dm",
    "create_theatrical_dm",
    "create_humorous_dm",
    "create_terse_dm",
    # Exceptions
    "ModelLoadError",
    "InsufficientResourcesError",
    "NoSuitableModelError",
    "NoFallbackAvailableError",
]
