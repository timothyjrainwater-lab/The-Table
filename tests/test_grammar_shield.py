"""Tests for Grammar Shield: Output validation layer for Spark/LLM responses

WO-031: Tests covering JSON validation, schema validation, mechanical assertion
detection, retry logic, and LlamaCppAdapter.generate_validated() integration.

Reference: docs/design/SPARK_ADAPTER_ARCHITECTURE.md
"""

import json
import pytest
from unittest.mock import Mock, patch

from aidm.spark.spark_adapter import (
    SparkRequest,
    SparkResponse,
    FinishReason,
    LoadedModel,
)
from aidm.spark.grammar_shield import (
    GrammarShield,
    GrammarShieldConfig,
    GrammarValidationError,
    MechanicalAssertionError,
    JsonParseError,
    SchemaValidationError,
    ValidationResult,
)
from aidm.spark.model_registry import ModelRegistry
from aidm.spark.llamacpp_adapter import LlamaCppAdapter


# ============================================================================
# Helpers
# ============================================================================


def _make_response(text: str, finish_reason: FinishReason = FinishReason.COMPLETED) -> SparkResponse:
    """Build a SparkResponse with given text."""
    return SparkResponse(
        text=text,
        finish_reason=finish_reason,
        tokens_used=10,
        provider_metadata={"model_id": "test-model"},
    )


def _make_request(
    prompt: str = "Test prompt",
    temperature: float = 0.8,
    max_tokens: int = 100,
    json_mode: bool = False,
) -> SparkRequest:
    """Build a SparkRequest."""
    return SparkRequest(
        prompt=prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        json_mode=json_mode,
    )


def _make_generate_fn(responses):
    """Build a mock generate function that returns responses in sequence."""
    call_count = [0]

    def generate_fn(request):
        idx = min(call_count[0], len(responses) - 1)
        call_count[0] += 1
        return responses[idx]

    return generate_fn


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


def _make_mock_llm_response(text=" Generated text.", prompt_tokens=10, completion_tokens=5):
    """Helper: build a dict matching llama-cpp's response format."""
    return {
        "choices": [{"text": text, "finish_reason": "stop"}],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
    }


# ============================================================================
# JSON Validation Tests (5 tests)
# ============================================================================


class TestJsonValidation:
    """Tests for Grammar Shield JSON validation."""

    def test_valid_json_passes(self):
        """Valid JSON passes validation."""
        shield = GrammarShield()
        request = _make_request(json_mode=True)
        response = _make_response('{"key": "value"}')

        result = shield.validate_and_retry(
            request=request,
            response=response,
            generate_fn=lambda r: response,
        )

        assert result.valid is True
        assert result.retries_used == 0
        assert result.final_text == '{"key": "value"}'

    def test_invalid_json_detected(self):
        """Invalid JSON fails validation."""
        shield = GrammarShield()
        errors = shield.validate_only(text="not json at all", json_mode=True)

        assert len(errors) > 0
        assert any(isinstance(e, JsonParseError) for e in errors)

    def test_json_retry_succeeds(self):
        """First attempt bad JSON, retry good JSON → passes."""
        shield = GrammarShield()
        request = _make_request(json_mode=True)
        bad_response = _make_response("not json")
        good_response = _make_response('{"fixed": true}')

        generate_fn = _make_generate_fn([good_response])

        result = shield.validate_and_retry(
            request=request,
            response=bad_response,
            generate_fn=generate_fn,
        )

        assert result.valid is True
        assert result.retries_used == 1
        assert result.original_text == "not json"
        assert result.final_text == '{"fixed": true}'

    def test_json_retry_exhausted_raises(self):
        """All retries bad JSON → raises JsonParseError."""
        shield = GrammarShield()
        request = _make_request(json_mode=True)
        bad_response = _make_response("still not json")

        generate_fn = _make_generate_fn([
            _make_response("also not json"),
            _make_response("nope still not"),
        ])

        with pytest.raises(JsonParseError):
            shield.validate_and_retry(
                request=request,
                response=bad_response,
                generate_fn=generate_fn,
            )

    def test_json_not_checked_without_json_mode(self):
        """json_mode=False skips JSON check — plain text passes."""
        shield = GrammarShield()
        # Disable assertion detection to isolate JSON check
        shield.config.enable_assertion_detection = False
        errors = shield.validate_only(text="not json", json_mode=False)

        assert len(errors) == 0


# ============================================================================
# Schema Validation Tests (5 tests)
# ============================================================================


class TestSchemaValidation:
    """Tests for Grammar Shield schema validation."""

    def test_valid_schema_passes(self):
        """Output matching schema passes validation."""
        shield = GrammarShield()
        shield.config.enable_assertion_detection = False

        # Use a callable validator
        def validate(data):
            assert "name" in data
            assert "value" in data

        text = '{"name": "fireball", "value": 42}'
        errors = shield.validate_only(text=text, json_mode=True, schema=validate)

        assert len(errors) == 0

    def test_schema_mismatch_detected(self):
        """Missing required field fails schema validation."""
        shield = GrammarShield()
        shield.config.enable_assertion_detection = False

        def validate(data):
            if "required_field" not in data:
                raise ValueError("Missing required_field")

        text = '{"other_field": "value"}'
        errors = shield.validate_only(text=text, json_mode=True, schema=validate)

        assert any(isinstance(e, SchemaValidationError) for e in errors)

    def test_schema_retry_succeeds(self):
        """First attempt mismatch, retry matches → passes."""
        shield = GrammarShield()
        shield.config.enable_assertion_detection = False

        def validate(data):
            if "name" not in data:
                raise ValueError("Missing name")

        request = _make_request(json_mode=True)
        bad_response = _make_response('{"wrong": "field"}')
        good_response = _make_response('{"name": "correct"}')

        generate_fn = _make_generate_fn([good_response])

        result = shield.validate_and_retry(
            request=request,
            response=bad_response,
            generate_fn=generate_fn,
            schema=validate,
        )

        assert result.valid is True
        assert result.retries_used == 1

    def test_schema_retry_exhausted_raises(self):
        """All retries mismatch → raises SchemaValidationError."""
        shield = GrammarShield()
        shield.config.enable_assertion_detection = False

        def validate(data):
            if "name" not in data:
                raise ValueError("Missing name")

        request = _make_request(json_mode=True)
        bad_response = _make_response('{"wrong": 1}')

        generate_fn = _make_generate_fn([
            _make_response('{"still_wrong": 2}'),
            _make_response('{"nope": 3}'),
        ])

        with pytest.raises(SchemaValidationError):
            shield.validate_and_retry(
                request=request,
                response=bad_response,
                generate_fn=generate_fn,
                schema=validate,
            )

    def test_no_schema_skips_check(self):
        """schema=None skips schema validation."""
        shield = GrammarShield()
        shield.config.enable_assertion_detection = False
        errors = shield.validate_only(text="plain text", json_mode=False, schema=None)

        assert len(errors) == 0


# ============================================================================
# Mechanical Assertion Detection Tests (7 tests)
# ============================================================================


class TestMechanicalAssertionDetection:
    """Tests for Grammar Shield mechanical assertion detection."""

    def test_clean_narration_passes(self):
        """Clean narrative text passes assertion check."""
        shield = GrammarShield()
        errors = shield.validate_only(text="The orc roars in fury, swinging its blade wildly.")

        assert len(errors) == 0

    def test_damage_number_detected(self):
        """'deals 15 damage' triggers detection."""
        shield = GrammarShield()
        error = shield._check_mechanical_assertions("The sword deals 15 damage to the goblin.")

        assert error is not None
        assert isinstance(error, MechanicalAssertionError)
        assert "damage_quantity" in error.matched_patterns

    def test_ac_reference_detected(self):
        """'AC 18' triggers detection."""
        shield = GrammarShield()
        error = shield._check_mechanical_assertions("The knight's AC 18 deflects the blow.")

        assert error is not None
        assert "armor_class" in error.matched_patterns

    def test_rule_citation_detected(self):
        """'PHB 145' triggers detection."""
        shield = GrammarShield()
        error = shield._check_mechanical_assertions("According to PHB 145, the spell triggers.")

        assert error is not None
        assert "rule_citation" in error.matched_patterns

    def test_dice_notation_detected(self):
        """'2d6' triggers detection."""
        shield = GrammarShield()
        error = shield._check_mechanical_assertions("The fireball explodes for 8d6 fire damage.")

        assert error is not None
        assert "dice_notation" in error.matched_patterns

    def test_dc_reference_detected(self):
        """'DC 15' triggers detection."""
        shield = GrammarShield()
        error = shield._check_mechanical_assertions("Make a DC 15 Reflex save.")

        assert error is not None
        assert "difficulty_class" in error.matched_patterns

    def test_assertion_retry_still_fails_raises(self):
        """All retries contain assertions → raises MechanicalAssertionError."""
        shield = GrammarShield()
        request = _make_request()
        bad_response = _make_response("The sword deals 15 damage.")

        generate_fn = _make_generate_fn([
            _make_response("The attack does 20 damage."),
            _make_response("It deals 10 points of damage."),
        ])

        with pytest.raises(MechanicalAssertionError) as exc_info:
            shield.validate_and_retry(
                request=request,
                response=bad_response,
                generate_fn=generate_fn,
            )

        assert len(exc_info.value.matched_patterns) > 0
        assert len(exc_info.value.matched_text) > 0


# ============================================================================
# Retry Logic Tests (4 tests)
# ============================================================================


class TestRetryLogic:
    """Tests for Grammar Shield retry behavior."""

    def test_retry_budget_tracked(self):
        """ValidationResult.retries_used incremented correctly."""
        shield = GrammarShield()
        request = _make_request(json_mode=True)
        bad_response = _make_response("not json")

        # First retry fails, second retry succeeds
        generate_fn = _make_generate_fn([
            _make_response("still not json"),
            _make_response('{"valid": true}'),
        ])

        result = shield.validate_and_retry(
            request=request,
            response=bad_response,
            generate_fn=generate_fn,
        )

        assert result.retries_used == 2
        assert result.valid is True

    def test_retry_preserves_original_text(self):
        """Original text stored in result when retry needed."""
        shield = GrammarShield()
        request = _make_request(json_mode=True)
        original_response = _make_response("original bad text")
        good_response = _make_response('{"valid": true}')

        generate_fn = _make_generate_fn([good_response])

        result = shield.validate_and_retry(
            request=request,
            response=original_response,
            generate_fn=generate_fn,
        )

        assert result.original_text == "original bad text"
        assert result.final_text == '{"valid": true}'

    def test_retry_prompt_appends_constraint(self):
        """Retry prompt includes constraint text about mechanical assertions."""
        shield = GrammarShield()
        request = _make_request(prompt="Narrate the attack")
        errors = [MechanicalAssertionError(
            matched_patterns=["damage_quantity"],
            matched_text=["15 damage"],
            full_text="deals 15 damage",
        )]

        retry_request = shield._build_retry_prompt(request, errors)

        assert "Do NOT include specific numbers" in retry_request.prompt
        assert retry_request.temperature == 0.9  # 0.8 + 0.1

    def test_no_retry_on_clean_output(self):
        """Clean output → 0 retries, no original text stored."""
        shield = GrammarShield()
        request = _make_request()
        response = _make_response("The orc falls with a thunderous crash.")

        result = shield.validate_and_retry(
            request=request,
            response=response,
            generate_fn=lambda r: response,
        )

        assert result.retries_used == 0
        assert result.original_text is None
        assert result.valid is True


# ============================================================================
# Integration Tests (4 tests)
# ============================================================================


class TestGenerateValidatedIntegration:
    """Tests for LlamaCppAdapter.generate_validated()."""

    @patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
    def test_generate_validated_passthrough_no_shield(self, mock_check):
        """grammar_shield=None → plain generate() passthrough."""
        mock_check.return_value = True
        registry = ModelRegistry.load_from_file("config/models.yaml")
        adapter = LlamaCppAdapter(registry=registry)

        mock_engine = Mock(return_value=_make_mock_llm_response(text=" Hello world."))
        loaded = _make_loaded_model(inference_engine=mock_engine)

        request = SparkRequest(prompt="Say hello", temperature=0.7, max_tokens=50)
        response = adapter.generate_validated(request, loaded, grammar_shield=None)

        assert response.text == "Hello world."
        assert response.finish_reason == FinishReason.COMPLETED
        # No grammar_shield key in metadata when shield is None
        assert "grammar_shield" not in (response.provider_metadata or {})

    @patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
    def test_generate_validated_with_shield_validates(self, mock_check):
        """Shield validates clean output successfully."""
        mock_check.return_value = True
        registry = ModelRegistry.load_from_file("config/models.yaml")
        adapter = LlamaCppAdapter(registry=registry)

        mock_engine = Mock(return_value=_make_mock_llm_response(
            text=" The orc falls with a thunderous crash."
        ))
        loaded = _make_loaded_model(inference_engine=mock_engine)

        shield = GrammarShield()
        request = SparkRequest(prompt="Narrate", temperature=0.8, max_tokens=100)
        response = adapter.generate_validated(request, loaded, grammar_shield=shield)

        assert response.text == "The orc falls with a thunderous crash."
        assert "grammar_shield" in response.provider_metadata
        assert response.provider_metadata["grammar_shield"]["retries_used"] == 0

    @patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
    def test_generate_validated_metadata_includes_shield_info(self, mock_check):
        """provider_metadata includes grammar_shield key with retry info."""
        mock_check.return_value = True
        registry = ModelRegistry.load_from_file("config/models.yaml")
        adapter = LlamaCppAdapter(registry=registry)

        mock_engine = Mock(return_value=_make_mock_llm_response(
            text=" A clean narration without any mechanical claims."
        ))
        loaded = _make_loaded_model(inference_engine=mock_engine)

        shield = GrammarShield()
        request = SparkRequest(prompt="Narrate", temperature=0.8, max_tokens=100)
        response = adapter.generate_validated(request, loaded, grammar_shield=shield)

        gs_meta = response.provider_metadata["grammar_shield"]
        assert "retries_used" in gs_meta
        assert "original_text" in gs_meta
        assert "errors_detected" in gs_meta
        assert gs_meta["retries_used"] == 0
        assert gs_meta["original_text"] is None
        assert gs_meta["errors_detected"] == []

    @patch('aidm.spark.llamacpp_adapter.LlamaCppAdapter._check_llama_cpp_available')
    def test_generate_validated_error_response_skips_validation(self, mock_check):
        """finish_reason=ERROR skips Grammar Shield validation."""
        mock_check.return_value = True
        registry = ModelRegistry.load_from_file("config/models.yaml")
        adapter = LlamaCppAdapter(registry=registry)

        # Template model (no engine) → ERROR response
        loaded = _make_loaded_model(inference_engine=None, model_id="template-narration")

        shield = GrammarShield()
        request = SparkRequest(prompt="Test", temperature=0.5, max_tokens=50)
        response = adapter.generate_validated(request, loaded, grammar_shield=shield)

        # Should return the ERROR response directly, not crash
        assert response.finish_reason == FinishReason.ERROR
        assert "grammar_shield" not in (response.provider_metadata or {})


# ============================================================================
# Additional Edge Case Tests
# ============================================================================


class TestEdgeCases:
    """Additional edge case tests for Grammar Shield."""

    def test_hit_points_detected(self):
        """'25 hp' triggers hit_points detection."""
        shield = GrammarShield()
        error = shield._check_mechanical_assertions("The fighter has 25 hp remaining.")

        assert error is not None
        assert "hit_points" in error.matched_patterns

    def test_attack_bonus_detected(self):
        """'+5 to attack' triggers attack_bonus detection."""
        shield = GrammarShield()
        error = shield._check_mechanical_assertions("With +5 to attack, the blow lands.")

        assert error is not None
        assert "attack_bonus" in error.matched_patterns

    def test_die_roll_result_detected(self):
        """'rolled a 17' triggers die_roll_result detection."""
        shield = GrammarShield()
        error = shield._check_mechanical_assertions("The player rolled a 17 on the check.")

        assert error is not None
        assert "die_roll_result" in error.matched_patterns

    def test_multiple_patterns_in_single_text(self):
        """Multiple patterns in one text all detected."""
        shield = GrammarShield()
        error = shield._check_mechanical_assertions(
            "The wizard rolled a 15 against DC 20, dealing 3d6 damage."
        )

        assert error is not None
        assert len(error.matched_patterns) >= 3

    def test_config_disable_assertion_detection(self):
        """Disabling assertion detection allows mechanical text through."""
        config = GrammarShieldConfig(enable_assertion_detection=False)
        shield = GrammarShield(config=config)

        errors = shield.validate_only(text="deals 15 damage with AC 18")
        assert len(errors) == 0

    def test_retry_temperature_caps_at_2_0(self):
        """Retry temperature increase caps at 2.0."""
        shield = GrammarShield()
        request = _make_request(temperature=1.95)
        errors = [JsonParseError("bad json")]

        retry = shield._build_retry_prompt(request, errors)
        assert retry.temperature == 2.0  # Capped, not 2.05

    def test_json_retry_appends_json_constraint(self):
        """JSON error retry prompt includes JSON constraint."""
        shield = GrammarShield()
        request = _make_request(json_mode=True)
        errors = [JsonParseError("bad json")]

        retry = shield._build_retry_prompt(request, errors)
        assert "MUST be valid JSON" in retry.prompt
