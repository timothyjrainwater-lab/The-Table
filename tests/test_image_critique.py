"""Tests for image critique contracts (schemas + adapter protocol).

PRE-M3 CONTRACT TESTS (NON-OPERATIONAL)
---------------------------------------
Tests stub implementations only. No actual critique logic tested.
All tests use StubImageCritic (placeholder scores, no image analysis).

Runtime wiring and actual critique implementations deferred to M3.
"""

import pytest
from aidm.schemas.image_critique import (
    CritiqueDimension,
    CritiqueResult,
    CritiqueRubric,
    RegenerationAttempt,
    DimensionType,
    SeverityLevel,
    DEFAULT_CRITIQUE_RUBRIC,
)
from aidm.core.image_critique_adapter import (
    ImageCritiqueAdapter,
    StubImageCritic,
    create_image_critic,
)


# =============================================================================
# CritiqueDimension Tests
# =============================================================================

def test_critique_dimension_creation_valid():
    """CritiqueDimension creates successfully with valid inputs."""
    dim = CritiqueDimension(
        dimension=DimensionType.READABILITY,
        severity=SeverityLevel.ACCEPTABLE,
        score=0.85,
        reason="Image readable at UI size",
        measurement_method="laplacian_variance"
    )
    assert dim.dimension == DimensionType.READABILITY
    assert dim.severity == SeverityLevel.ACCEPTABLE
    assert dim.score == 0.85
    assert dim.reason == "Image readable at UI size"
    assert dim.measurement_method == "laplacian_variance"


def test_critique_dimension_score_out_of_range():
    """CritiqueDimension rejects scores outside [0.0, 1.0]."""
    with pytest.raises(ValueError, match="score must be in"):
        CritiqueDimension(
            dimension=DimensionType.COMPOSITION,
            severity=SeverityLevel.MINOR,
            score=1.5,  # Invalid
            reason="Test",
            measurement_method="test"
        )

    with pytest.raises(ValueError, match="score must be in"):
        CritiqueDimension(
            dimension=DimensionType.ARTIFACTING,
            severity=SeverityLevel.CRITICAL,
            score=-0.1,  # Invalid
            reason="Test",
            measurement_method="test"
        )


def test_critique_dimension_to_dict():
    """CritiqueDimension serializes to dict with sorted keys."""
    dim = CritiqueDimension(
        dimension=DimensionType.STYLE_ADHERENCE,
        severity=SeverityLevel.MAJOR,
        score=0.45,
        reason="Style mismatch",
        measurement_method="clip_similarity"
    )
    data = dim.to_dict()
    assert list(data.keys()) == sorted(data.keys())  # Keys sorted
    assert data["dimension"] == "style_adherence"
    assert data["severity"] == "major"
    assert data["score"] == 0.45
    assert data["reason"] == "Style mismatch"
    assert data["measurement_method"] == "clip_similarity"


def test_critique_dimension_from_dict_roundtrip():
    """CritiqueDimension roundtrips through dict serialization."""
    original = CritiqueDimension(
        dimension=DimensionType.IDENTITY_MATCH,
        severity=SeverityLevel.CRITICAL,
        score=0.30,
        reason="Species mismatch",
        measurement_method="clip_embedding"
    )
    data = original.to_dict()
    restored = CritiqueDimension.from_dict(data)
    assert restored == original


# =============================================================================
# CritiqueResult Tests
# =============================================================================

def test_critique_result_creation_valid():
    """CritiqueResult creates successfully with valid dimensions."""
    dimensions = [
        CritiqueDimension(
            dimension=DimensionType.ARTIFACTING,
            severity=SeverityLevel.ACCEPTABLE,
            score=0.90,
            reason="No artifacts",
            measurement_method="stub"
        ),
        CritiqueDimension(
            dimension=DimensionType.READABILITY,
            severity=SeverityLevel.ACCEPTABLE,
            score=0.85,
            reason="Readable",
            measurement_method="stub"
        ),
    ]

    result = CritiqueResult(
        passed=True,
        overall_severity=SeverityLevel.ACCEPTABLE,
        dimensions=dimensions,
        overall_score=0.88,
        rejection_reason=None,
        critique_method="stub"
    )
    assert result.passed is True
    assert result.overall_severity == SeverityLevel.ACCEPTABLE
    assert len(result.dimensions) == 2
    assert result.overall_score == 0.88


def test_critique_result_requires_sorted_dimensions():
    """CritiqueResult rejects unsorted dimensions."""
    # Create dimensions in wrong order (readability before artifacting)
    dimensions = [
        CritiqueDimension(
            dimension=DimensionType.READABILITY,  # Should be after artifacting
            severity=SeverityLevel.ACCEPTABLE,
            score=0.85,
            reason="Readable",
            measurement_method="stub"
        ),
        CritiqueDimension(
            dimension=DimensionType.ARTIFACTING,  # Should be first
            severity=SeverityLevel.ACCEPTABLE,
            score=0.90,
            reason="No artifacts",
            measurement_method="stub"
        ),
    ]

    with pytest.raises(ValueError, match="dimensions must be sorted"):
        CritiqueResult(
            passed=True,
            overall_severity=SeverityLevel.ACCEPTABLE,
            dimensions=dimensions,
            overall_score=0.88,
            rejection_reason=None,
            critique_method="stub"
        )


def test_critique_result_overall_score_out_of_range():
    """CritiqueResult rejects overall_score outside [0.0, 1.0]."""
    dimensions = [
        CritiqueDimension(
            dimension=DimensionType.READABILITY,
            severity=SeverityLevel.ACCEPTABLE,
            score=0.85,
            reason="Readable",
            measurement_method="stub"
        ),
    ]

    with pytest.raises(ValueError, match="overall_score must be in"):
        CritiqueResult(
            passed=True,
            overall_severity=SeverityLevel.ACCEPTABLE,
            dimensions=dimensions,
            overall_score=1.2,  # Invalid
            rejection_reason=None,
            critique_method="stub"
        )


def test_critique_result_to_dict():
    """CritiqueResult serializes to dict with sorted keys."""
    dimensions = [
        CritiqueDimension(
            dimension=DimensionType.COMPOSITION,
            severity=SeverityLevel.MINOR,
            score=0.65,
            reason="Slightly off-center",
            measurement_method="bounding_box"
        ),
    ]

    result = CritiqueResult(
        passed=False,
        overall_severity=SeverityLevel.MINOR,
        dimensions=dimensions,
        overall_score=0.65,
        rejection_reason="Composition issue",
        critique_method="heuristics"
    )
    data = result.to_dict()
    assert list(data.keys()) == sorted(data.keys())  # Keys sorted
    assert data["passed"] is False
    assert data["overall_severity"] == "minor"
    assert data["rejection_reason"] == "Composition issue"


def test_critique_result_from_dict_roundtrip():
    """CritiqueResult roundtrips through dict serialization."""
    dimensions = [
        CritiqueDimension(
            dimension=DimensionType.ARTIFACTING,
            severity=SeverityLevel.CRITICAL,
            score=0.20,
            reason="6 fingers detected",
            measurement_method="hand_detection"
        ),
        CritiqueDimension(
            dimension=DimensionType.READABILITY,
            severity=SeverityLevel.ACCEPTABLE,
            score=0.80,
            reason="Readable",
            measurement_method="laplacian"
        ),
    ]

    original = CritiqueResult(
        passed=False,
        overall_severity=SeverityLevel.CRITICAL,
        dimensions=dimensions,
        overall_score=0.50,
        rejection_reason="Critical artifact: extra fingers",
        critique_method="clip_hybrid"
    )
    data = original.to_dict()
    restored = CritiqueResult.from_dict(data)
    assert restored == original


# =============================================================================
# RegenerationAttempt Tests
# =============================================================================

def test_regeneration_attempt_creation_valid():
    """RegenerationAttempt creates successfully with valid inputs."""
    attempt = RegenerationAttempt(
        attempt_number=2,
        cfg_scale=9.0,
        sampling_steps=60,
        creativity=0.7,
        negative_prompt="blurry, low detail",
        generation_time_ms=3200
    )
    assert attempt.attempt_number == 2
    assert attempt.cfg_scale == 9.0
    assert attempt.sampling_steps == 60
    assert attempt.creativity == 0.7
    assert attempt.negative_prompt == "blurry, low detail"
    assert attempt.generation_time_ms == 3200


def test_regeneration_attempt_invalid_attempt_number():
    """RegenerationAttempt rejects attempt_number < 1."""
    with pytest.raises(ValueError, match="attempt_number must be >= 1"):
        RegenerationAttempt(
            attempt_number=0,  # Invalid
            cfg_scale=7.5,
            sampling_steps=50,
            creativity=0.8
        )


def test_regeneration_attempt_invalid_cfg_scale():
    """RegenerationAttempt rejects cfg_scale outside [1.0, 20.0]."""
    with pytest.raises(ValueError, match="cfg_scale must be in"):
        RegenerationAttempt(
            attempt_number=1,
            cfg_scale=0.5,  # Invalid
            sampling_steps=50,
            creativity=0.8
        )

    with pytest.raises(ValueError, match="cfg_scale must be in"):
        RegenerationAttempt(
            attempt_number=1,
            cfg_scale=25.0,  # Invalid
            sampling_steps=50,
            creativity=0.8
        )


def test_regeneration_attempt_invalid_sampling_steps():
    """RegenerationAttempt rejects sampling_steps outside [10, 150]."""
    with pytest.raises(ValueError, match="sampling_steps must be in"):
        RegenerationAttempt(
            attempt_number=1,
            cfg_scale=7.5,
            sampling_steps=5,  # Invalid
            creativity=0.8
        )

    with pytest.raises(ValueError, match="sampling_steps must be in"):
        RegenerationAttempt(
            attempt_number=1,
            cfg_scale=7.5,
            sampling_steps=200,  # Invalid
            creativity=0.8
        )


def test_regeneration_attempt_invalid_creativity():
    """RegenerationAttempt rejects creativity outside [0.0, 1.0]."""
    with pytest.raises(ValueError, match="creativity must be in"):
        RegenerationAttempt(
            attempt_number=1,
            cfg_scale=7.5,
            sampling_steps=50,
            creativity=-0.1  # Invalid
        )

    with pytest.raises(ValueError, match="creativity must be in"):
        RegenerationAttempt(
            attempt_number=1,
            cfg_scale=7.5,
            sampling_steps=50,
            creativity=1.5  # Invalid
        )


def test_regeneration_attempt_to_dict():
    """RegenerationAttempt serializes to dict with sorted keys."""
    attempt = RegenerationAttempt(
        attempt_number=3,
        cfg_scale=11.0,
        sampling_steps=70,
        creativity=0.5,
        negative_prompt="deformed hands, extra fingers"
    )
    data = attempt.to_dict()
    assert list(data.keys()) == sorted(data.keys())  # Keys sorted
    assert data["attempt_number"] == 3
    assert data["cfg_scale"] == 11.0
    assert data["sampling_steps"] == 70
    assert data["creativity"] == 0.5
    assert data["negative_prompt"] == "deformed hands, extra fingers"


def test_regeneration_attempt_from_dict_roundtrip():
    """RegenerationAttempt roundtrips through dict serialization."""
    original = RegenerationAttempt(
        attempt_number=4,
        cfg_scale=13.0,
        sampling_steps=80,
        creativity=0.3,
        negative_prompt="blurry, deformed, cropped",
        generation_time_ms=4500
    )
    data = original.to_dict()
    restored = RegenerationAttempt.from_dict(data)
    assert restored.attempt_number == original.attempt_number
    assert restored.cfg_scale == original.cfg_scale
    assert restored.sampling_steps == original.sampling_steps
    assert restored.creativity == original.creativity
    assert restored.negative_prompt == original.negative_prompt
    assert restored.generation_time_ms == original.generation_time_ms


# =============================================================================
# CritiqueRubric Tests
# =============================================================================

def test_critique_rubric_creation_valid():
    """CritiqueRubric creates successfully with valid thresholds."""
    rubric = CritiqueRubric(
        readability_threshold=0.75,
        composition_threshold=0.70,
        artifacting_threshold=0.80,
        style_threshold=0.65,
        identity_threshold=0.60,
        overall_threshold=0.70
    )
    assert rubric.readability_threshold == 0.75
    assert rubric.composition_threshold == 0.70
    assert rubric.artifacting_threshold == 0.80


def test_critique_rubric_default_values():
    """CritiqueRubric uses default threshold values."""
    rubric = CritiqueRubric()
    assert rubric.readability_threshold == 0.70
    assert rubric.composition_threshold == 0.70
    assert rubric.artifacting_threshold == 0.70
    assert rubric.style_threshold == 0.70
    assert rubric.identity_threshold == 0.60
    assert rubric.overall_threshold == 0.70


def test_critique_rubric_invalid_threshold():
    """CritiqueRubric rejects thresholds outside [0.0, 1.0]."""
    with pytest.raises(ValueError, match="readability_threshold must be in"):
        CritiqueRubric(readability_threshold=1.5)

    with pytest.raises(ValueError, match="composition_threshold must be in"):
        CritiqueRubric(composition_threshold=-0.1)


def test_critique_rubric_to_dict():
    """CritiqueRubric serializes to dict with sorted keys."""
    rubric = CritiqueRubric(
        readability_threshold=0.75,
        composition_threshold=0.68,
        identity_threshold=0.55
    )
    data = rubric.to_dict()
    assert list(data.keys()) == sorted(data.keys())  # Keys sorted
    assert data["readability_threshold"] == 0.75
    assert data["composition_threshold"] == 0.68
    assert data["identity_threshold"] == 0.55


def test_critique_rubric_from_dict_roundtrip():
    """CritiqueRubric roundtrips through dict serialization."""
    original = CritiqueRubric(
        readability_threshold=0.80,
        composition_threshold=0.75,
        artifacting_threshold=0.85,
        style_threshold=0.70,
        identity_threshold=0.65,
        overall_threshold=0.75
    )
    data = original.to_dict()
    restored = CritiqueRubric.from_dict(data)
    assert restored.readability_threshold == original.readability_threshold
    assert restored.composition_threshold == original.composition_threshold
    assert restored.identity_threshold == original.identity_threshold


def test_default_critique_rubric():
    """DEFAULT_CRITIQUE_RUBRIC is accessible and valid."""
    assert DEFAULT_CRITIQUE_RUBRIC.overall_threshold == 0.70
    assert DEFAULT_CRITIQUE_RUBRIC.identity_threshold == 0.60


# =============================================================================
# StubImageCritic Tests
# =============================================================================

def test_stub_image_critic_always_pass():
    """StubImageCritic with always_pass=True returns passed=True."""
    critic = StubImageCritic(always_pass=True, placeholder_score=0.85)
    result = critic.critique(
        image_bytes=b"fake_image_data",
        rubric=DEFAULT_CRITIQUE_RUBRIC
    )
    assert result.passed is True
    assert result.overall_severity == SeverityLevel.ACCEPTABLE
    assert result.overall_score == 0.85
    assert result.rejection_reason is None
    assert result.critique_method == "stub"


def test_stub_image_critic_always_fail():
    """StubImageCritic with always_pass=False returns passed=False."""
    critic = StubImageCritic(always_pass=False, placeholder_score=0.85)
    result = critic.critique(
        image_bytes=b"fake_image_data",
        rubric=DEFAULT_CRITIQUE_RUBRIC
    )
    assert result.passed is False
    assert result.overall_severity == SeverityLevel.MAJOR
    assert abs(result.overall_score - 0.65) < 0.001  # placeholder_score - 0.2 (with floating point tolerance)
    assert result.rejection_reason == "Stub critic configured to always fail"


def test_stub_image_critic_dimensions_sorted():
    """StubImageCritic returns dimensions sorted by dimension type."""
    critic = StubImageCritic(always_pass=True)
    result = critic.critique(
        image_bytes=b"fake_image_data",
        rubric=DEFAULT_CRITIQUE_RUBRIC
    )
    dimension_types = [d.dimension for d in result.dimensions]
    expected_order = [
        DimensionType.ARTIFACTING,
        DimensionType.COMPOSITION,
        DimensionType.IDENTITY_MATCH,
        DimensionType.READABILITY,
        DimensionType.STYLE_ADHERENCE,
    ]
    assert dimension_types == expected_order


def test_stub_image_critic_identity_check_with_anchor():
    """StubImageCritic includes identity check when anchor provided."""
    critic = StubImageCritic(always_pass=True, placeholder_score=0.80)
    result = critic.critique(
        image_bytes=b"fake_image_data",
        rubric=DEFAULT_CRITIQUE_RUBRIC,
        anchor_image_bytes=b"fake_anchor_data"
    )
    identity_dim = [d for d in result.dimensions if d.dimension == DimensionType.IDENTITY_MATCH][0]
    assert identity_dim.score == 0.80
    assert "no actual identity matching" in identity_dim.reason


def test_stub_image_critic_identity_check_without_anchor():
    """StubImageCritic skips identity check when no anchor provided."""
    critic = StubImageCritic(always_pass=True, placeholder_score=0.80)
    result = critic.critique(
        image_bytes=b"fake_image_data",
        rubric=DEFAULT_CRITIQUE_RUBRIC,
        anchor_image_bytes=None
    )
    identity_dim = [d for d in result.dimensions if d.dimension == DimensionType.IDENTITY_MATCH][0]
    assert identity_dim.score == 1.0  # Skip check
    assert identity_dim.severity == SeverityLevel.ACCEPTABLE
    assert "No anchor provided" in identity_dim.reason


def test_stub_image_critic_style_check_with_reference():
    """StubImageCritic includes style check when reference provided."""
    critic = StubImageCritic(always_pass=True, placeholder_score=0.75)
    result = critic.critique(
        image_bytes=b"fake_image_data",
        rubric=DEFAULT_CRITIQUE_RUBRIC,
        style_reference_bytes=b"fake_style_reference"
    )
    style_dim = [d for d in result.dimensions if d.dimension == DimensionType.STYLE_ADHERENCE][0]
    assert style_dim.score == 0.75
    assert "no actual style matching" in style_dim.reason


def test_stub_image_critic_style_check_without_reference():
    """StubImageCritic skips style check when no reference provided."""
    critic = StubImageCritic(always_pass=True, placeholder_score=0.75)
    result = critic.critique(
        image_bytes=b"fake_image_data",
        rubric=DEFAULT_CRITIQUE_RUBRIC,
        style_reference_bytes=None
    )
    style_dim = [d for d in result.dimensions if d.dimension == DimensionType.STYLE_ADHERENCE][0]
    assert style_dim.score == 1.0  # Skip check
    assert style_dim.severity == SeverityLevel.ACCEPTABLE
    assert "No style reference provided" in style_dim.reason


def test_stub_image_critic_empty_image_bytes():
    """StubImageCritic rejects empty image_bytes."""
    critic = StubImageCritic(always_pass=True)
    with pytest.raises(ValueError, match="non-empty image_bytes"):
        critic.critique(
            image_bytes=b"",
            rubric=DEFAULT_CRITIQUE_RUBRIC
        )


def test_stub_image_critic_invalid_placeholder_score():
    """StubImageCritic rejects placeholder_score outside [0.0, 1.0]."""
    with pytest.raises(ValueError, match="placeholder_score must be in"):
        StubImageCritic(always_pass=True, placeholder_score=1.5)


# =============================================================================
# ImageCritiqueAdapter Protocol Tests
# =============================================================================

def test_stub_image_critic_implements_protocol():
    """StubImageCritic implements ImageCritiqueAdapter protocol."""
    critic = StubImageCritic(always_pass=True)
    assert isinstance(critic, ImageCritiqueAdapter)


# =============================================================================
# create_image_critic Factory Tests
# =============================================================================

def test_create_image_critic_stub_default():
    """create_image_critic('stub') returns StubImageCritic with defaults."""
    critic = create_image_critic("stub")
    assert isinstance(critic, StubImageCritic)
    assert critic.always_pass is True
    assert critic.placeholder_score == 0.85


def test_create_image_critic_stub_custom_config():
    """create_image_critic('stub') accepts custom configuration."""
    critic = create_image_critic("stub", always_pass=False, placeholder_score=0.60)
    assert isinstance(critic, StubImageCritic)
    assert critic.always_pass is False
    assert critic.placeholder_score == 0.60


def test_create_image_critic_unknown_backend():
    """create_image_critic raises ValueError for unknown backend."""
    with pytest.raises(ValueError, match="Unknown image critic backend"):
        create_image_critic("nonexistent_backend")


def test_create_image_critic_stub_roundtrip():
    """create_image_critic('stub') produces working critic."""
    critic = create_image_critic("stub", always_pass=True, placeholder_score=0.90)
    result = critic.critique(
        image_bytes=b"test_image",
        rubric=DEFAULT_CRITIQUE_RUBRIC
    )
    assert result.passed is True
    assert result.overall_score == 0.90
