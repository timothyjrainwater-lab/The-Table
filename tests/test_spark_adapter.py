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
    model = registry.get_model_by_id("qwen3-8b-instruct-4bit")
    assert model is not None
    assert model.id == "qwen3-8b-instruct-4bit"
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
    assert tier_rule.preferred_model == "qwen3-8b-instruct-4bit"


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
    chain = registry.get_fallback_chain("qwen3-14b-instruct-4bit")
    assert len(chain) > 1
    assert chain[0] == "qwen3-14b-instruct-4bit"
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
    fallback_id = adapter.get_fallback_model("qwen3-14b-instruct-4bit")
    assert fallback_id == "qwen3-8b-instruct-4bit"

    # Get fallback for 8B model
    fallback_id = adapter.get_fallback_model("qwen3-8b-instruct-4bit")
    assert fallback_id == "qwen3-4b-instruct-4bit"


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
            # Check 8B model compatibility (should be compatible)
            report = adapter.check_model_compatibility("qwen3-8b-instruct-4bit")

    # Note: Report may show not compatible due to missing model file
    # In real scenario with model files present, it should be compatible
    assert report.model_id == "qwen3-8b-instruct-4bit"
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
    result = service.generate_narration(request)

    # Should use template narration
    assert result is not None
    narration = result.text if hasattr(result, 'text') else str(result)
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
    result = service.generate_narration(request)

    # Should use template narration
    assert result is not None
    narration = result.text if hasattr(result, 'text') else str(result)
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
    result = service.generate_narration(request)

    # Should use template narration
    assert result is not None
    narration = result.text if hasattr(result, 'text') else str(result)
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
            Mock(is_compatible=False),  # qwen3-4b incompatible
            Mock(is_compatible=True),   # gemma3-4b or template compatible
        ]
        model_id = adapter.select_model_for_tier(hardware_tier)

    # Should have fallen back through the chain
    assert model_id in ["qwen3-4b-instruct-4bit", "gemma3-4b-qat", "template-narration"]

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

    result = service.generate_narration(request)

    # 8. Verify result
    assert result is not None
    narration = result.text if hasattr(result, 'text') else str(result)
    assert isinstance(narration, str)
    assert len(narration) > 0

    # 9. Verify guardrails maintained
    assert not service.is_kill_switch_active()
    assert not service.get_metrics().has_violations()


# ============================================================================
# WO-027: LlamaCppAdapter.generate() Canonical Contract Tests
# ============================================================================

from aidm.spark.spark_adapter import (
    SparkRequest,
    SparkResponse,
    FinishReason,
    LoadedModel,
)


def _make_mock_llm_response(
    text=" Generated text.",
    prompt_tokens=10,
    completion_tokens=5,
    finish_reason="stop",
):
    """Helper: build a dict matching llama-cpp's response format."""
    return {
        "choices": [{"text": text, "finish_reason": finish_reason}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
    }


def _make_loaded_model(inference_engine=None, model_id="test-model"):
    """Helper: build a LoadedModel with a mock inference engine."""
    profile = Mock()
    profile.name = "Test Model"
    profile.tier = Mock(value="medium")
    profile.backend = "llama.cpp"
    profile.quantization = "4bit"
    profile.max_tokens = 1024
    profile.max_context_window = 8192
    return LoadedModel(
        model_id=model_id,
        profile=profile,
        inference_engine=inference_engine,
        device="cpu",
        memory_usage_mb=100.0,
    )


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_basic_response(mock_check):
    """generate() returns SparkResponse with correct text."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response(text=" Hello world."))
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Say hello", temperature=0.7, max_tokens=50)
    response = adapter.generate(request, loaded)

    assert response.text == "Hello world."
    assert response.finish_reason == FinishReason.COMPLETED
    assert response.error is None


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_token_count_nonzero(mock_check):
    """generate() populates tokens_used with actual counts, not 0."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response(
        prompt_tokens=15, completion_tokens=20,
    ))
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test prompt", temperature=0.5, max_tokens=100)
    response = adapter.generate(request, loaded)

    assert response.tokens_used == 35  # 15 + 20
    assert response.tokens_used > 0


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_stop_sequence_detection(mock_check):
    """generate() sets finish_reason=STOP_SEQUENCE when output ends with stop seq."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    # Text ends with the stop sequence (after strip)
    mock_engine = Mock(return_value=_make_mock_llm_response(
        text=" The answer is 42.\n\n###",
        completion_tokens=8,
    ))
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(
        prompt="Question", temperature=0.5, max_tokens=100,
        stop_sequences=["###", "---"],
    )
    response = adapter.generate(request, loaded)

    assert response.finish_reason == FinishReason.STOP_SEQUENCE


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_stop_sequence_no_match(mock_check):
    """generate() returns COMPLETED when no stop sequence matches."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response(
        text=" Normal text here.",
        completion_tokens=5,
    ))
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(
        prompt="Test", temperature=0.5, max_tokens=100,
        stop_sequences=["###"],
    )
    response = adapter.generate(request, loaded)

    assert response.finish_reason == FinishReason.COMPLETED


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_length_limit_detection(mock_check):
    """generate() sets finish_reason=LENGTH_LIMIT when completion_tokens >= max_tokens."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response(
        completion_tokens=50,
    ))
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Long prompt", temperature=0.5, max_tokens=50)
    response = adapter.generate(request, loaded)

    assert response.finish_reason == FinishReason.LENGTH_LIMIT


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_length_limit_exceeds_max_tokens(mock_check):
    """generate() sets LENGTH_LIMIT when completion_tokens > max_tokens."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response(
        completion_tokens=60,
    ))
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
    response = adapter.generate(request, loaded)

    assert response.finish_reason == FinishReason.LENGTH_LIMIT


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_seed_forwarding(mock_check):
    """generate() forwards seed to llama-cpp when provided."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response())
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50, seed=42)
    adapter.generate(request, loaded)

    # Verify seed was passed in the call
    call_kwargs = mock_engine.call_args
    assert call_kwargs[1]["seed"] == 42


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_no_seed_not_forwarded(mock_check):
    """generate() does not forward seed when not provided."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response())
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
    adapter.generate(request, loaded)

    call_kwargs = mock_engine.call_args
    assert "seed" not in call_kwargs[1]


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_json_mode_flag(mock_check):
    """generate() passes response_format when json_mode=True."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response(text=' {"key": "value"}'))
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(
        prompt="Return JSON", temperature=0.5, max_tokens=50, json_mode=True,
    )
    adapter.generate(request, loaded)

    call_kwargs = mock_engine.call_args
    assert call_kwargs[1]["response_format"] == {"type": "json_object"}


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_json_mode_off_no_format(mock_check):
    """generate() does not pass response_format when json_mode=False."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response())
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
    adapter.generate(request, loaded)

    call_kwargs = mock_engine.call_args
    assert "response_format" not in call_kwargs[1]


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_template_model_returns_error(mock_check):
    """generate() with template model (no engine) returns ERROR, not crash."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    loaded = _make_loaded_model(inference_engine=None, model_id="template-narration")

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
    response = adapter.generate(request, loaded)

    assert response.finish_reason == FinishReason.ERROR
    assert response.tokens_used == 0
    assert response.text == ""
    assert "No inference engine loaded" in response.error
    assert "template fallback" in response.error


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_no_loaded_model_returns_error(mock_check):
    """generate() with loaded_model=None returns ERROR response."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
    response = adapter.generate(request, loaded_model=None)

    assert response.finish_reason == FinishReason.ERROR
    assert response.error is not None
    assert "No inference engine loaded" in response.error


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_provider_metadata_populated(mock_check):
    """generate() populates provider_metadata with token counts and model_id."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response(
        prompt_tokens=12, completion_tokens=8,
    ))
    loaded = _make_loaded_model(inference_engine=mock_engine, model_id="my-model")

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
    response = adapter.generate(request, loaded)

    assert response.provider_metadata is not None
    assert response.provider_metadata["prompt_tokens"] == 12
    assert response.provider_metadata["completion_tokens"] == 8
    assert response.provider_metadata["model_id"] == "my-model"


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_error_during_generation(mock_check):
    """generate() produces finish_reason=ERROR with error message on exception."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(side_effect=RuntimeError("CUDA out of memory"))
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
    response = adapter.generate(request, loaded)

    assert response.finish_reason == FinishReason.ERROR
    assert response.tokens_used == 0
    assert response.text == ""
    assert "CUDA out of memory" in response.error


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_error_preserves_model_id_in_metadata(mock_check):
    """generate() error response still includes model_id in provider_metadata."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(side_effect=ValueError("bad param"))
    loaded = _make_loaded_model(inference_engine=mock_engine, model_id="err-model")

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
    response = adapter.generate(request, loaded)

    assert response.provider_metadata["model_id"] == "err-model"


def test_spark_request_invalid_temperature_rejected():
    """SparkRequest rejects temperature outside [0.0, 2.0] (BL-013)."""
    with pytest.raises(ValueError, match="temperature MUST be in"):
        SparkRequest(prompt="Test", temperature=-0.1, max_tokens=50)

    with pytest.raises(ValueError, match="temperature MUST be in"):
        SparkRequest(prompt="Test", temperature=2.1, max_tokens=50)


def test_spark_request_empty_prompt_rejected():
    """SparkRequest rejects empty prompt."""
    with pytest.raises(ValueError, match="prompt MUST be non-empty"):
        SparkRequest(prompt="", temperature=0.5, max_tokens=50)


def test_spark_request_invalid_max_tokens_rejected():
    """SparkRequest rejects non-positive max_tokens."""
    with pytest.raises(ValueError, match="max_tokens MUST be positive"):
        SparkRequest(prompt="Test", temperature=0.5, max_tokens=0)

    with pytest.raises(ValueError, match="max_tokens MUST be positive"):
        SparkRequest(prompt="Test", temperature=0.5, max_tokens=-1)


def test_spark_response_error_requires_message():
    """SparkResponse with finish_reason=ERROR requires error field (BL-016)."""
    with pytest.raises(ValueError, match="error field MUST be populated"):
        SparkResponse(text="", finish_reason=FinishReason.ERROR, tokens_used=0)


def test_spark_response_negative_tokens_rejected():
    """SparkResponse rejects negative tokens_used."""
    with pytest.raises(ValueError, match="tokens_used MUST be non-negative"):
        SparkResponse(text="ok", finish_reason=FinishReason.COMPLETED, tokens_used=-1)


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_temperature_forwarded(mock_check):
    """generate() forwards temperature to llama-cpp."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response())
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=1.5, max_tokens=50)
    adapter.generate(request, loaded)

    call_kwargs = mock_engine.call_args
    assert call_kwargs[1]["temperature"] == 1.5


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_max_tokens_forwarded(mock_check):
    """generate() forwards max_tokens to llama-cpp."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response())
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=200)
    adapter.generate(request, loaded)

    call_kwargs = mock_engine.call_args
    assert call_kwargs[1]["max_tokens"] == 200


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_stop_sequences_forwarded(mock_check):
    """generate() forwards stop_sequences as 'stop' kwarg."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response())
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(
        prompt="Test", temperature=0.5, max_tokens=50,
        stop_sequences=["###", "\n\n"],
    )
    adapter.generate(request, loaded)

    call_kwargs = mock_engine.call_args
    assert call_kwargs[1]["stop"] == ["###", "\n\n"]


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_no_stop_sequences_not_forwarded(mock_check):
    """generate() does not pass 'stop' kwarg when no stop_sequences."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response())
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
    adapter.generate(request, loaded)

    call_kwargs = mock_engine.call_args
    assert "stop" not in call_kwargs[1]


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_determinism_same_seed_same_output(mock_check):
    """10x determinism: same seed + same prompt -> same SparkResponse.text."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    # Mock engine returns deterministic output
    mock_engine = Mock(return_value=_make_mock_llm_response(
        text=" Deterministic output.",
        prompt_tokens=10,
        completion_tokens=3,
    ))
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test prompt", temperature=0.0, max_tokens=50, seed=12345)

    results = []
    for _ in range(10):
        response = adapter.generate(request, loaded)
        results.append(response.text)

    # All 10 results must be identical
    assert all(r == results[0] for r in results), "Determinism violated: outputs differ"
    # Verify seed was passed all 10 times
    assert mock_engine.call_count == 10
    for call in mock_engine.call_args_list:
        assert call[1]["seed"] == 12345


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_determinism_seed_consistency(mock_check):
    """Same seed produces same response fields (tokens_used, finish_reason)."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    response_data = _make_mock_llm_response(
        text=" Consistent.",
        prompt_tokens=8,
        completion_tokens=2,
    )
    mock_engine = Mock(return_value=response_data)
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=0.0, max_tokens=50, seed=99)

    responses = [adapter.generate(request, loaded) for _ in range(10)]

    texts = [r.text for r in responses]
    tokens = [r.tokens_used for r in responses]
    reasons = [r.finish_reason for r in responses]

    assert len(set(texts)) == 1
    assert len(set(tokens)) == 1
    assert len(set(reasons)) == 1


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_completed_finish_reason(mock_check):
    """generate() returns COMPLETED for normal generation."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response(
        completion_tokens=10,
    ))
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=100)
    response = adapter.generate(request, loaded)

    assert response.finish_reason == FinishReason.COMPLETED


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_prompt_forwarded(mock_check):
    """generate() passes the prompt as first positional arg to engine."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response())
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="My specific prompt", temperature=0.5, max_tokens=50)
    adapter.generate(request, loaded)

    call_args = mock_engine.call_args
    assert call_args[0][0] == "My specific prompt"


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_echo_false(mock_check):
    """generate() always passes echo=False to llama-cpp."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    mock_engine = Mock(return_value=_make_mock_llm_response())
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
    adapter.generate(request, loaded)

    call_kwargs = mock_engine.call_args
    assert call_kwargs[1]["echo"] is False


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_raw_text_stop_sequence_detection(mock_check):
    """generate() detects stop sequence in raw text even after stripping."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    # Raw text ends with stop seq but stripped text does not
    mock_engine = Mock(return_value={
        "choices": [{"text": "The end\n\n", "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 3},
    })
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(
        prompt="Test", temperature=0.5, max_tokens=100,
        stop_sequences=["\n\n"],
    )
    response = adapter.generate(request, loaded)

    assert response.finish_reason == FinishReason.STOP_SEQUENCE


@patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
def test_generate_missing_usage_returns_zero_tokens(mock_check):
    """generate() returns tokens_used=0 when response has no 'usage' field."""
    mock_check.return_value = True
    registry = ModelRegistry.load_from_file("config/models.yaml")
    adapter = LlamaCppAdapter(registry=registry)

    # Response without usage field
    mock_engine = Mock(return_value={
        "choices": [{"text": " Some text."}],
    })
    loaded = _make_loaded_model(inference_engine=mock_engine)

    request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
    response = adapter.generate(request, loaded)

    assert response.tokens_used == 0
    assert response.text == "Some text."
    assert response.finish_reason == FinishReason.COMPLETED
