"""Model Registry: Parses and validates models.yaml configuration

This module provides the ModelRegistry class for loading and validating
LLM model configurations from the models.yaml file.

Reference: docs/design/SPARK_ADAPTER_ARCHITECTURE.md (Section 3)
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


class TierName(str, Enum):
    """Hardware tier classifications for model selection."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    FALLBACK = "FALLBACK"
    TEMPLATE = "TEMPLATE"


@dataclass(frozen=True)
class HardwareTier:
    """Hardware capability tier detected by hardware detection system.

    This dataclass represents the detected hardware capabilities used
    for tier-based model selection.

    Attributes:
        tier_name: Classification tier (HIGH/MEDIUM/LOW/FALLBACK/TEMPLATE)
        vram_gb: Available VRAM in gigabytes
        ram_gb: Available system RAM in gigabytes
        cpu_cores: Number of available CPU cores
        supports_gpu: Whether GPU acceleration is available
    """
    tier_name: TierName
    vram_gb: float
    ram_gb: float
    cpu_cores: int
    supports_gpu: bool


@dataclass(frozen=True)
class ModelProfile:
    """Model metadata from model registry (models.yaml).

    This dataclass represents a single model's configuration including
    hardware requirements, quantization, and backend information.

    Attributes:
        id: Unique model identifier (e.g., "mistral-7b-instruct-4bit")
        name: Human-readable model name
        provider: Provider identifier ("llamacpp", "transformers", "template")
        path: Path to model file (None for template-narration)
        quantization: Quantization format ("4bit", "8bit", "fp16", or None)
        max_tokens: Maximum generation length
        max_context_window: Maximum context size in tokens
        min_vram_gb: Minimum VRAM required in gigabytes
        min_ram_gb: Minimum system RAM required in gigabytes
        supports_streaming: Whether streaming generation is supported
        supports_json_mode: Whether JSON mode is supported
        backend: Inference runtime ("llama.cpp", "transformers", "template")
        tier: Hardware tier classification
        fallback_model: Next model to try if this fails (None for template)
        presets: Provider-specific generation presets
        description: Human-readable description
        offload_config: Optional CPU offload configuration
    """
    id: str
    name: str
    provider: str
    path: Optional[str]
    quantization: Optional[str]
    max_tokens: Optional[int]
    max_context_window: Optional[int]
    min_vram_gb: float
    min_ram_gb: float
    supports_streaming: bool
    supports_json_mode: bool
    backend: str
    tier: TierName
    fallback_model: Optional[str]
    presets: Dict[str, Any]
    description: str
    offload_config: Optional[Dict[str, Any]] = None


@dataclass
class TierSelectionRule:
    """Tier selection rule from models.yaml.

    Attributes:
        tier: Tier classification
        min_vram_gb: Minimum VRAM threshold for this tier
        preferred_model: Default model ID for this tier
        alternatives: List of alternative model IDs
        description: Human-readable description
    """
    tier: TierName
    min_vram_gb: float
    preferred_model: str
    alternatives: List[str]
    description: str


class ModelRegistryError(Exception):
    """Base exception for model registry errors."""
    pass


class InvalidSchemaError(ModelRegistryError):
    """Raised when models.yaml has invalid schema."""
    pass


class CircularFallbackError(ModelRegistryError):
    """Raised when fallback chain contains cycles."""
    pass


class ModelRegistry:
    """Model registry parser and validator.

    Parses models.yaml and provides access to model profiles and tier rules.

    Example usage:
        registry = ModelRegistry.load_from_file("config/models.yaml")
        model_profile = registry.get_model_by_id("mistral-7b-instruct-4bit")
        tier_rule = registry.get_tier_rule(TierName.MEDIUM)
    """

    def __init__(
        self,
        models: List[ModelProfile],
        tier_rules: Dict[TierName, TierSelectionRule],
        default_model_id: str,
    ):
        """Initialize model registry.

        Args:
            models: List of model profiles
            tier_rules: Dictionary mapping tier names to selection rules
            default_model_id: Default model ID (used if no tier detected)
        """
        self.models = models
        self.tier_rules = tier_rules
        self.default_model_id = default_model_id
        self._models_by_id = {model.id: model for model in models}

        # Validate registry
        self._validate_schema()
        self._validate_fallback_chains()

    @classmethod
    def load_from_file(cls, file_path: str) -> "ModelRegistry":
        """Load model registry from models.yaml file.

        Args:
            file_path: Path to models.yaml configuration file

        Returns:
            ModelRegistry instance

        Raises:
            ModelRegistryError: If file cannot be loaded or schema is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise ModelRegistryError(f"Model registry file not found: {file_path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise InvalidSchemaError(f"Failed to parse models.yaml: {e}")

        # Parse default model
        spark_config = config.get('spark', {})
        default_model_id = spark_config.get('default', 'mistral-7b-instruct-4bit')

        # Parse model profiles
        models_data = spark_config.get('models', [])
        models = [cls._parse_model_profile(model_data) for model_data in models_data]

        # Parse tier selection rules
        tier_selection_data = config.get('tier_selection', {})
        tier_rules = {
            TierName(tier_name): cls._parse_tier_rule(tier_name, rule_data)
            for tier_name, rule_data in tier_selection_data.items()
        }

        return cls(models=models, tier_rules=tier_rules, default_model_id=default_model_id)

    @staticmethod
    def _parse_model_profile(data: Dict[str, Any]) -> ModelProfile:
        """Parse model profile from YAML data.

        Args:
            data: Model profile dictionary from models.yaml

        Returns:
            ModelProfile instance

        Raises:
            InvalidSchemaError: If required fields are missing
        """
        required_fields = ['id', 'name', 'provider', 'tier', 'min_vram_gb']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise InvalidSchemaError(
                f"Model profile missing required fields: {missing_fields}"
            )

        return ModelProfile(
            id=data['id'],
            name=data['name'],
            provider=data['provider'],
            path=data.get('path'),
            quantization=data.get('quantization'),
            max_tokens=data.get('max_tokens'),
            max_context_window=data.get('max_context_window'),
            min_vram_gb=float(data['min_vram_gb']),
            min_ram_gb=float(data.get('min_ram_gb', 0.0)),
            supports_streaming=data.get('supports_streaming', False),
            supports_json_mode=data.get('supports_json_mode', False),
            backend=data.get('backend', data['provider']),
            tier=TierName(data['tier']),
            fallback_model=data.get('fallback_model'),
            presets=data.get('presets', {}),
            description=data.get('description', ''),
            offload_config=data.get('offload_config'),
        )

    @staticmethod
    def _parse_tier_rule(tier_name: str, data: Dict[str, Any]) -> TierSelectionRule:
        """Parse tier selection rule from YAML data.

        Args:
            tier_name: Tier name (HIGH/MEDIUM/FALLBACK/TEMPLATE)
            data: Tier rule dictionary from models.yaml

        Returns:
            TierSelectionRule instance
        """
        return TierSelectionRule(
            tier=TierName(tier_name),
            min_vram_gb=float(data.get('min_vram_gb', 0.0)),
            preferred_model=data['preferred_model'],
            alternatives=data.get('alternatives', []),
            description=data.get('description', ''),
        )

    def get_model_by_id(self, model_id: str) -> Optional[ModelProfile]:
        """Get model profile by ID.

        Args:
            model_id: Model identifier

        Returns:
            ModelProfile if found, None otherwise
        """
        return self._models_by_id.get(model_id)

    def get_tier_rule(self, tier: TierName) -> Optional[TierSelectionRule]:
        """Get tier selection rule for given tier.

        Args:
            tier: Hardware tier classification

        Returns:
            TierSelectionRule if found, None otherwise
        """
        return self.tier_rules.get(tier)

    def get_models_by_tier(self, tier: TierName) -> List[ModelProfile]:
        """Get all models for given tier.

        Args:
            tier: Hardware tier classification

        Returns:
            List of ModelProfile instances
        """
        return [model for model in self.models if model.tier == tier]

    def get_default_model(self) -> ModelProfile:
        """Get default model profile.

        Returns:
            Default ModelProfile

        Raises:
            ModelRegistryError: If default model not found
        """
        model = self.get_model_by_id(self.default_model_id)
        if model is None:
            raise ModelRegistryError(
                f"Default model not found: {self.default_model_id}"
            )
        return model

    def _validate_schema(self) -> None:
        """Validate model registry schema.

        Raises:
            InvalidSchemaError: If schema validation fails
        """
        if not self.models:
            raise InvalidSchemaError("Model registry contains no models")

        if not self.tier_rules:
            raise InvalidSchemaError("Model registry contains no tier rules")

        # Verify default model exists
        if self.default_model_id not in self._models_by_id:
            raise InvalidSchemaError(
                f"Default model '{self.default_model_id}' not found in registry"
            )

        # Verify tier rule preferred models exist
        for tier_name, tier_rule in self.tier_rules.items():
            if tier_rule.preferred_model not in self._models_by_id:
                raise InvalidSchemaError(
                    f"Tier {tier_name} preferred model '{tier_rule.preferred_model}' "
                    f"not found in registry"
                )

    def _validate_fallback_chains(self) -> None:
        """Validate fallback chains are acyclic.

        Raises:
            CircularFallbackError: If circular fallback chain detected
        """
        for model in self.models:
            visited = set()
            current_id = model.id

            while current_id is not None:
                if current_id in visited:
                    raise CircularFallbackError(
                        f"Circular fallback chain detected: {visited} -> {current_id}"
                    )

                visited.add(current_id)
                current_model = self.get_model_by_id(current_id)

                if current_model is None:
                    raise InvalidSchemaError(
                        f"Fallback model '{current_id}' not found in registry"
                    )

                current_id = current_model.fallback_model

    def list_all_models(self) -> List[ModelProfile]:
        """Get list of all registered models.

        Returns:
            List of all ModelProfile instances
        """
        return self.models.copy()

    def get_fallback_chain(self, model_id: str) -> List[str]:
        """Get complete fallback chain for a model.

        Args:
            model_id: Starting model ID

        Returns:
            List of model IDs in fallback order (including starting model)

        Raises:
            ModelRegistryError: If model not found
        """
        chain = []
        current_id = model_id

        while current_id is not None:
            model = self.get_model_by_id(current_id)
            if model is None:
                raise ModelRegistryError(f"Model not found: {current_id}")

            chain.append(current_id)
            current_id = model.fallback_model

        return chain
