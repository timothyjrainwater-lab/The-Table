"""Tests for policy variety config."""

import pytest
import json
from aidm.schemas.policy_config import PolicyVarietyConfig


def test_policy_variety_config_defaults():
    """PolicyVarietyConfig should default to greedy (top_k=1, temp=1.0)."""
    config = PolicyVarietyConfig()

    assert config.top_k == 1
    assert config.temperature == 1.0
    assert config.score_band is None


def test_policy_variety_config_with_top_k():
    """PolicyVarietyConfig should support top-k sampling."""
    config = PolicyVarietyConfig(top_k=5, temperature=0.8)

    assert config.top_k == 5
    assert config.temperature == 0.8


def test_policy_variety_config_with_score_band():
    """PolicyVarietyConfig should support score band filtering."""
    config = PolicyVarietyConfig(
        top_k=10,
        temperature=1.0,
        score_band=5.0
    )

    assert config.score_band == 5.0


def test_policy_variety_config_invalid_top_k_raises():
    """PolicyVarietyConfig should reject top_k < 1."""
    with pytest.raises(ValueError, match="top_k must be >= 1"):
        PolicyVarietyConfig(top_k=0)

    with pytest.raises(ValueError, match="top_k must be >= 1"):
        PolicyVarietyConfig(top_k=-1)


def test_policy_variety_config_invalid_temperature_raises():
    """PolicyVarietyConfig should reject temperature <= 0."""
    with pytest.raises(ValueError, match="temperature must be > 0"):
        PolicyVarietyConfig(temperature=0)

    with pytest.raises(ValueError, match="temperature must be > 0"):
        PolicyVarietyConfig(temperature=-0.5)


def test_policy_variety_config_invalid_score_band_raises():
    """PolicyVarietyConfig should reject negative score_band."""
    with pytest.raises(ValueError, match="score_band must be >= 0"):
        PolicyVarietyConfig(score_band=-1.0)


def test_policy_variety_config_serialization():
    """PolicyVarietyConfig should serialize deterministically."""
    config = PolicyVarietyConfig(
        top_k=3,
        temperature=0.7,
        score_band=2.5
    )

    data = config.to_dict()
    json_str = json.dumps(data, sort_keys=True)
    restored = PolicyVarietyConfig.from_dict(json.loads(json_str))

    assert restored.top_k == config.top_k
    assert restored.temperature == config.temperature
    assert restored.score_band == config.score_band


def test_policy_variety_config_roundtrip():
    """PolicyVarietyConfig should roundtrip correctly."""
    original = PolicyVarietyConfig(
        top_k=5,
        temperature=1.2,
        score_band=3.0
    )

    data = original.to_dict()
    restored = PolicyVarietyConfig.from_dict(data)

    assert restored.top_k == original.top_k
    assert restored.temperature == original.temperature
    assert restored.score_band == original.score_band


def test_policy_variety_config_to_dict_omits_none_score_band():
    """PolicyVarietyConfig.to_dict() should omit None score_band."""
    config = PolicyVarietyConfig(top_k=3, temperature=0.9)

    data = config.to_dict()

    assert "top_k" in data
    assert "temperature" in data
    assert "score_band" not in data


def test_policy_variety_config_deterministic():
    """PolicyVarietyConfig serialization should be deterministic."""
    config = PolicyVarietyConfig(top_k=5, temperature=1.5)

    json1 = json.dumps(config.to_dict(), sort_keys=True)
    json2 = json.dumps(config.to_dict(), sort_keys=True)

    assert json1 == json2


def test_policy_variety_config_greedy():
    """PolicyVarietyConfig with top_k=1 represents greedy selection."""
    greedy = PolicyVarietyConfig(top_k=1, temperature=1.0)

    assert greedy.top_k == 1
    assert greedy.temperature == 1.0


def test_policy_variety_config_low_temperature():
    """PolicyVarietyConfig should allow temperature < 1 for sharpening."""
    config = PolicyVarietyConfig(top_k=5, temperature=0.5)

    assert config.temperature == 0.5


def test_policy_variety_config_high_temperature():
    """PolicyVarietyConfig should allow temperature > 1 for flattening."""
    config = PolicyVarietyConfig(top_k=5, temperature=2.0)

    assert config.temperature == 2.0
