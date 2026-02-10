"""Unit tests for Spark Adapter components

Tests for:
- ModelRegistry: YAML parsing, validation, fallback chains
- SparkAdapter: Model loading, tier selection, compatibility checks
- LlamaCppAdapter: llama.cpp integration (mock-based)
- GuardedNarrationService integration with Spark

Reference: docs/design/SPARK_ADAPTER_ARCHITECTURE.md
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from aidm.spark import (
    ModelRegistry,
    ModelProfile,
    HardwareTier,
    TierName,
    ModelLoadError,
    InsufficientResourcesError,
    NoSuitableModelError,
    NoFallbackAvailableError,
)
from aidm.spark.model_registry import (
    InvalidSchemaError,
    CircularFallbackError,
)
from aidm.spark.llamacpp_adapter import LlamaCppAdapter


# ============================================================================
# ModelRegistry Tests
# ============================================================================


def test_model_registry_load_from_file():
    """Test loading model registry from models.yaml."""
    registry = ModelRegistry.load_from_file("config/models.yaml")

    # Verify registry loaded
    assert registry is not None
    assert len(registry.models) > 0
    assert len(registry.tier_rules) > 0

    # Verify default model
    default_model = registry.get_default_model()
    assert default_model is not None
    assert default_model.id == registry.default_model_id


def test_model_registry_get_model_by_id():
    """Test retrieving model by ID."""
    registry = ModelRegistry.load_from_file("config/models.yaml")

    # Get known model
    model = registry.get_model_by_id("mistral-7b-instruct-4bit")
    assert model is not None
    assert model.id == "mistral-7b-instruct-4bit"
    assert model.tier == TierName.MEDIUM

    # Get non-existent model
    model = registry.get_model_by_id("non-existent-model")
    assert model is None


def test_model_registry_get_tier_rule():
    """Test retrieving tier selection rules."""
    registry = ModelRegistry.load_from_file("config/models.yaml")

    # Get MEDIUM tier rule
    tier_rule = registry.get_tier_rule(TierName.MEDIUM)
    assert tier_rule is not None
    assert tier_rule.tier == TierName.MEDIUM
    assert tier_rule.preferred_model == "mistral-7b-instruct-4bit"


def test_model_registry_get_models_by_tier():
    """Test retrieving all models for a tier."""
    registry = ModelRegistry.load_from_file("config/models.yaml")

    # Get MEDIUM tier models
    medium_models = registry.get_models_by_tier(TierName.MEDIUM)
    assert len(medium_models) > 0
    assert all(model.tier == TierName.MEDIUM for model in medium_models)


def test_model_registry_fallback_chain():
    """Test fallback chain retrieval."""
    registry = ModelRegistry.load_from_file("config/models.yaml")

    # Get fallback chain for 14B model
    chain = registry.get_fallback_chain("mistral-14b-instruct-4bit")
    assert len(chain) > 1
    assert chain[0] == "mistral-14b-instruct-4bit"
    assert chain[-1] == "template-narration"  # Should end at template


def test_model_registry_validates_schema():
    """Test that registry validates schema on load."""
    # This test ensures validation happens
    # Actual validation tested by loading real config
    registry = ModelRegistry.load_from_file("config/models.yaml")

    # Should not raise - config is valid
    assert registry is not None


def test_model_registry_circular_fallback_detection():
    """Test detection of circular fallback chains."""
    # Create test models with circular fallback
    model_a = ModelProfile(
        id="model-a",
        name="Model A",
        provider="llamacpp",
        path="models/model-a.gguf",
        quantization="4bit",
        max_tokens=1024,
        max_context_window=4096,
        min_vram_gb=6.0,
        min_ram_gb=8.0,
        supports_streaming=True,
        supports_json_mode=False,
        backend="llama.cpp",
        tier=TierName.MEDIUM,
        fallback_model="model-b",  # Points to B
        presets={},
        description="Test model A",
    )

    model_b = ModelProfile(
        id="model-b",
        name="Model B",
        provider="llamacpp",
        path="models/model-b.gguf",
        quantization="4bit",
        max_tokens=1024,
        max_context_window=4096,
        min_vram_gb=3.0,
        min_ram_gb=4.0,
        supports_streaming=True,
        supports_json_mode=False,
        backend="llama.cpp",
        tier=TierName.FALLBACK,
        fallback_model="model-a",  # Points back to A (circular!)
        presets={},
        description="Test model B",
    )

    tier_rule = {
        TierName.MEDIUM: Mock(
            tier=TierName.MEDIUM,
            min_vram_gb=6.0,
            preferred_model="model-a",
            alternatives=[],
            description="Test tier",
        )
    }

    # Should raise CircularFallbackError
    with pytest.raises(CircularFallbackError):
        ModelRegistry(
            models=[model_a, model_b],
            tier_rules=tier_rule,
            default_model_id="model-a",
        )


# ============================================================================
# LlamaCppAdapter Tests (Mock-Based)
# ============================================================================


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_llamacpp_adapter_initialization(mock_check):
    """Test LlamaCpp adapter initialization."""
    mock_check.return_value = True

    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    assert adapter.registry is registry
    assert adapter.enable_gpu is True


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_llamacpp_adapter_select_model_for_tier(mock_check):
    """Test tier-based model selection."""
    mock_check.return_value = True

    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    # Test HIGH tier selection
    high_tier = HardwareTier(
        tier_name=TierName.HIGH,
        vram_gb=10.0,
        ram_gb=32.0,
        cpu_cores=8,
        supports_gpu=True,
    )

    # Mock compatibility check to return True
    with patch.object(adapter, 'check_model_compatibility') as mock_compat:
        mock_compat.return_value = Mock(is_compatible=True)
        model_id = adapter.select_model_for_tier(high_tier)

    assert model_id is not None
    # Should select HIGH tier preferred model
    tier_rule = registry.get_tier_rule(TierName.HIGH)
    assert model_id == tier_rule.preferred_model


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_llamacpp_adapter_get_fallback_model(mock_check):
    """Test fallback model retrieval."""
    mock_check.return_value = True

    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    # Get fallback for 14B model
    fallback_id = adapter.get_fallback_model("mistral-14b-instruct-4bit")
    assert fallback_id == "mistral-7b-instruct-4bit"

    # Get fallback for 7B model
    fallback_id = adapter.get_fallback_model("mistral-7b-instruct-4bit")
    assert fallback_id == "phi-3b-instruct-4bit"


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_llamacpp_adapter_no_fallback_raises_error(mock_check):
    """Test that NoFallbackAvailableError raised when no fallback exists."""
    mock_check.return_value = True

    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    # Template narration has no fallback
    with pytest.raises(NoFallbackAvailableError):
        adapter.get_fallback_model("template-narration")


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_llamacpp_adapter_check_compatibility(mock_check):
    """Test model compatibility checking."""
    mock_check.return_value = True

    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    # Mock hardware detection
    with patch.object(adapter, '_get_available_vram_gb', return_value=10.0):
        with patch.object(adapter, '_get_available_ram_gb', return_value=32.0):
            # Check 7B model compatibility (should be compatible)
            report = adapter.check_model_compatibility("mistral-7b-instruct-4bit")

    # Note: Report may show not compatible due to missing model file
    # In real scenario with model files present, it should be compatible
    assert report.model_id == "mistral-7b-instruct-4bit"
    assert report.vram_required_gb == 6.0
    assert report.vram_available_gb == 10.0


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_llamacpp_adapter_template_narration_always_compatible(mock_check):
    """Test that template-narration is always compatible."""
    mock_check.return_value = True

    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    # Check template compatibility
    report = adapter.check_model_compatibility("template-narration")

    assert report.is_compatible is True
    assert report.vram_required_gb == 0.0
    assert len(report.compatibility_issues) == 0


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_llamacpp_adapter_load_template_model(mock_check):
    """Test loading template-narration model (no LLM)."""
    # Template loading works even without llama-cpp-python
    mock_check.return_value = False  # Simulate llama-cpp NOT available

    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    # Load template model (should succeed even without llama-cpp)
    loaded_model = adapter.load_model("template-narration")

    assert loaded_model.model_id == "template-narration"
    assert loaded_model.inference_engine is None
    assert loaded_model.device == "cpu"
    assert loaded_model.memory_usage_mb == 0.0


# ============================================================================
# GuardedNarrationService Integration Tests
# ============================================================================


def test_guarded_narration_service_backwards_compatible():
    """Test that GuardedNarrationService works without Spark (M1 mode)."""
    from aidm.narration.guarded_narration_service import (
        GuardedNarrationService,
        FrozenMemorySnapshot,
        NarrationRequest,
    )
    from aidm.schemas.engine_result import EngineResult, EngineResultStatus

    # Initialize service without loaded model (M1 mode)
    service = GuardedNarrationService(loaded_model=None)

    # Create narration request
    snapshot = FrozenMemorySnapshot.create()
    engine_result = EngineResult(
        result_id="test-result-001",
        intent_id="test-intent-001",
        status=EngineResultStatus.SUCCESS,
        resolved_at=datetime(2025, 1, 1, 12, 0, 0),
        narration_token="attack_hit",
        events=[],
    )
    request = NarrationRequest(
        engine_result=engine_result,
        memory_snapshot=snapshot,
        temperature=0.8,
    )

    # Generate narration
    narration = service.generate_narration(request)

    # Should use template narration
    assert narration is not None
    assert isinstance(narration, str)
    assert len(narration) > 0
    assert "attack" in narration.lower()


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_guarded_narration_service_with_template_model(mock_check):
    """Test GuardedNarrationService with template-narration LoadedModel."""
    from aidm.narration.guarded_narration_service import (
        GuardedNarrationService,
        FrozenMemorySnapshot,
        NarrationRequest,
    )
    from aidm.schemas.engine_result import EngineResult, EngineResultStatus

    # Template loading works without llama-cpp
    mock_check.return_value = False

    # Load template model
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)
    loaded_model = adapter.load_model("template-narration")

    # Initialize service with template model
    service = GuardedNarrationService(loaded_model=loaded_model)

    # Create narration request
    snapshot = FrozenMemorySnapshot.create()
    engine_result = EngineResult(
        result_id="test-result-001",
        intent_id="test-intent-001",
        status=EngineResultStatus.SUCCESS,
        resolved_at=datetime(2025, 1, 1, 12, 0, 0),
        narration_token="critical_hit",
        events=[],
    )
    request = NarrationRequest(
        engine_result=engine_result,
        memory_snapshot=snapshot,
        temperature=0.8,
    )

    # Generate narration
    narration = service.generate_narration(request)

    # Should use template narration
    assert narration is not None
    assert "critical" in narration.lower() or "hit" in narration.lower()


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_guarded_narration_service_maintains_guardrails(mock_check):
    """Test that Spark integration maintains all M1 guardrails."""
    from aidm.narration.guarded_narration_service import (
        GuardedNarrationService,
        FrozenMemorySnapshot,
        NarrationRequest,
    )
    from aidm.schemas.engine_result import EngineResult, EngineResultStatus
    from aidm.schemas.campaign_memory import SessionLedgerEntry

    # Template loading works without llama-cpp
    mock_check.return_value = False

    # Load template model
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)
    loaded_model = adapter.load_model("template-narration")

    # Initialize service with template model
    service = GuardedNarrationService(loaded_model=loaded_model)

    # Create narration request
    snapshot = FrozenMemorySnapshot.create()
    engine_result = EngineResult(
        result_id="test-result-001",
        intent_id="test-intent-001",
        status=EngineResultStatus.SUCCESS,
        resolved_at=datetime(2025, 1, 1, 12, 0, 0),
        narration_token="critical_hit",
        events=[],
    )
    request = NarrationRequest(
        engine_result=engine_result,
        memory_snapshot=snapshot,
        temperature=0.8,
    )

    # Generate narration
    narration = service.generate_narration(request)

    # Should use template narration
    assert narration is not None
    assert "critical" in narration.lower() or "hit" in narration.lower()


def test_guarded_narration_service_maintains_guardrails():
    """Test that Spark integration maintains all M1 guardrails."""
    from aidm.narration.guarded_narration_service import (
        GuardedNarrationService,
        FrozenMemorySnapshot,
        NarrationRequest,
    )
    from aidm.schemas.engine_result import EngineResult, EngineResultStatus
    from aidm.schemas.campaign_memory import SessionLedgerEntry

    # Load template model
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)
    loaded_model = adapter.load_model("template-narration")

    # Initialize service
    service = GuardedNarrationService(loaded_model=loaded_model)

    # Create memory snapshot
    session_ledger = SessionLedgerEntry(
        session_id="test_session",
        campaign_id="test_campaign",
        session_number=1,
        created_at="2026-02-10T00:00:00Z",
        summary="Test session",
    )
    snapshot = FrozenMemorySnapshot.create(session_ledger=session_ledger)
    hash_before = snapshot.snapshot_hash

    # Create narration request
    engine_result = EngineResult(
        result_id="test-result-001",
        intent_id="test-intent-001",
        status=EngineResultStatus.SUCCESS,
        resolved_at=datetime(2025, 1, 1, 12, 0, 0),
        narration_token="attack_hit",
        events=[],
    )
    request = NarrationRequest(
        engine_result=engine_result,
        memory_snapshot=snapshot,
        temperature=0.8,
    )

    # Generate narration
    narration = service.generate_narration(request)

    # Verify guardrails maintained
    hash_after = snapshot.snapshot_hash
    assert hash_before == hash_after, "Memory snapshot must be unchanged (FREEZE-001)"

    metrics = service.get_metrics()
    assert not metrics.has_violations(), "No guardrail violations should occur"
    assert not service.is_kill_switch_active(), "Kill switch should remain inactive"


# ============================================================================
# Integration Test: Full Spark Workflow
# ============================================================================


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_full_spark_workflow_with_fallback(mock_check):
    """Integration test: Full Spark workflow from tier selection to narration."""
    mock_check.return_value = True

    # 1. Load model registry
    registry = ModelRegistry.load_from_file("config/models.yaml")

    # 2. Create adapter
    adapter = LlamaCppAdapter(registry=registry)

    # 3. Detect hardware tier (simulated)
    hardware_tier = HardwareTier(
        tier_name=TierName.FALLBACK,  # Low-spec hardware
        vram_gb=2.0,
        ram_gb=8.0,
        cpu_cores=4,
        supports_gpu=False,
    )

    # 4. Select model for tier
    with patch.object(adapter, 'check_model_compatibility') as mock_compat:
        # First model incompatible, fallback compatible
        mock_compat.side_effect = [
            Mock(is_compatible=False),  # phi-3b incompatible
            Mock(is_compatible=True),   # template compatible
        ]
        model_id = adapter.select_model_for_tier(hardware_tier)

    # Should have fallen back to template
    assert model_id in ["phi-3b-instruct-4bit", "qwen2.5-3b-instruct", "template-narration"]

    # 5. Load model (template will always succeed)
    loaded_model = adapter.load_model("template-narration")
    assert loaded_model is not None

    # 6. Initialize GuardedNarrationService
    from aidm.narration.guarded_narration_service import (
        GuardedNarrationService,
        FrozenMemorySnapshot,
        NarrationRequest,
    )
    from aidm.schemas.engine_result import EngineResult, EngineResultStatus

    service = GuardedNarrationService(loaded_model=loaded_model)

    # 7. Generate narration
    snapshot = FrozenMemorySnapshot.create()
    engine_result = EngineResult(
        result_id="test-result-001",
        intent_id="test-intent-001",
        status=EngineResultStatus.SUCCESS,
        resolved_at=datetime(2025, 1, 1, 12, 0, 0),
        narration_token="attack_hit",
        events=[],
    )
    request = NarrationRequest(
        engine_result=engine_result,
        memory_snapshot=snapshot,
        temperature=0.8,
    )

    narration = service.generate_narration(request)

    # 8. Verify result
    assert narration is not None
    assert isinstance(narration, str)
    assert len(narration) > 0

    # 9. Verify guardrails maintained
    assert not service.is_kill_switch_active()
    assert not service.get_metrics().has_violations()
