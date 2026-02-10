"""Tests for SigLIPCritiqueAdapter (Layer 3 image critique).

M3 IMPLEMENTATION TESTS
-----------------------
Tests reference-based identity consistency validation using SigLIP embeddings.
Validates similarity computation, threshold handling, and skip behavior.

Based on approved design: SONNET-C_WO-M3-IMAGE-CRITIQUE-02_siglip_design.md
"""

import pytest
import io
import numpy as np
from PIL import Image
from unittest.mock import Mock, patch, MagicMock

from aidm.core.siglip_critique_adapter import SigLIPCritiqueAdapter
from aidm.schemas.image_critique import (
    CritiqueRubric,
    DimensionType,
    SeverityLevel,
    DEFAULT_CRITIQUE_RUBRIC,
)
from aidm.core.image_critique_adapter import ImageCritiqueAdapter, create_image_critic


# =============================================================================
# Test Image Generators
# =============================================================================

def generate_test_image_bytes(
    width: int = 512,
    height: int = 512,
    color: tuple = (128, 128, 128)
) -> bytes:
    """Generate simple test image bytes.

    Args:
        width: Image width
        height: Image height
        color: RGB color tuple

    Returns:
        PNG bytes
    """
    img = Image.new('RGB', (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


# =============================================================================
# Protocol Compliance Tests
# =============================================================================

def test_siglip_critic_implements_protocol():
    """SigLIPCritiqueAdapter implements ImageCritiqueAdapter protocol."""
    critic = SigLIPCritiqueAdapter()
    assert isinstance(critic, ImageCritiqueAdapter)


def test_siglip_critic_has_load_unload():
    """SigLIPCritiqueAdapter has load/unload methods."""
    critic = SigLIPCritiqueAdapter()
    # Should not raise
    # Note: We don't actually call load() without mocking as it requires open_clip
    assert hasattr(critic, 'load')
    assert hasattr(critic, 'unload')
    assert callable(critic.load)
    assert callable(critic.unload)


# =============================================================================
# Initialization Tests
# =============================================================================

def test_siglip_critic_default_initialization():
    """SigLIPCritiqueAdapter initializes with default parameters."""
    critic = SigLIPCritiqueAdapter()
    assert critic.model_name == "ViT-B-16-SigLIP"
    assert critic.pretrained == "webli"
    assert critic.similarity_threshold == 0.70
    assert critic.model is None
    assert critic.preprocess is None
    assert critic.device in ["cuda", "mps", "cpu"]


def test_siglip_critic_custom_initialization():
    """SigLIPCritiqueAdapter initializes with custom parameters."""
    critic = SigLIPCritiqueAdapter(
        model_name="ViT-L-16-SigLIP",
        pretrained="webli",
        device="cpu",
        similarity_threshold=0.75
    )
    assert critic.model_name == "ViT-L-16-SigLIP"
    assert critic.pretrained == "webli"
    assert critic.device == "cpu"
    assert critic.similarity_threshold == 0.75


def test_siglip_critic_threshold_validation():
    """SigLIPCritiqueAdapter validates similarity_threshold range."""
    # Valid thresholds
    SigLIPCritiqueAdapter(similarity_threshold=0.0)
    SigLIPCritiqueAdapter(similarity_threshold=0.5)
    SigLIPCritiqueAdapter(similarity_threshold=1.0)

    # Invalid thresholds
    with pytest.raises(ValueError, match="similarity_threshold must be in"):
        SigLIPCritiqueAdapter(similarity_threshold=-0.1)

    with pytest.raises(ValueError, match="similarity_threshold must be in"):
        SigLIPCritiqueAdapter(similarity_threshold=1.1)


# =============================================================================
# Skip Behavior Tests
# =============================================================================

def test_siglip_critic_skip_when_no_anchor():
    """SigLIPCritiqueAdapter returns skip result when no anchor provided."""
    critic = SigLIPCritiqueAdapter()
    image_bytes = generate_test_image_bytes()

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=None)

    assert result.passed is True
    assert result.overall_severity == SeverityLevel.ACCEPTABLE
    assert result.overall_score == 1.0
    assert result.rejection_reason is None
    assert result.critique_method == "siglip_skipped"

    # All dimensions should be skipped
    for dim in result.dimensions:
        assert dim.severity == SeverityLevel.ACCEPTABLE
        assert dim.score == 1.0
        assert dim.measurement_method == "skipped"
        assert "optional" in dim.reason.lower() or "skipped" in dim.reason.lower()


def test_siglip_critic_skip_without_loading_model():
    """SigLIPCritiqueAdapter skips without loading model when no anchor."""
    critic = SigLIPCritiqueAdapter()
    image_bytes = generate_test_image_bytes()

    # Model should not be loaded
    assert critic.model is None

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=None)

    # Model should still not be loaded
    assert critic.model is None
    assert result.passed is True


# =============================================================================
# Load/Unload Tests
# =============================================================================

def test_siglip_critic_load():
    """SigLIPCritiqueAdapter loads model correctly."""
    with patch('builtins.__import__', side_effect=ImportError):
        # Test that load() requires open_clip
        critic = SigLIPCritiqueAdapter(device="cpu")
        with pytest.raises(ImportError, match="open-clip-torch is required"):
            critic.load()


def test_siglip_critic_unload():
    """SigLIPCritiqueAdapter unloads model and frees VRAM."""
    critic = SigLIPCritiqueAdapter()
    critic.model = Mock()
    critic.preprocess = Mock()

    # Unload should work even without torch
    critic.unload()

    # Model should be cleared
    assert critic.model is None
    assert critic.preprocess is None


# =============================================================================
# Similarity Computation Tests (Mocked)
# =============================================================================

def test_siglip_critic_high_similarity_passes():
    """SigLIPCritiqueAdapter passes with high similarity (>= threshold)."""
    critic = SigLIPCritiqueAdapter(similarity_threshold=0.70)

    # Mock _compute_similarity to return high similarity
    with patch.object(critic, '_compute_similarity', return_value=0.85):
        with patch.object(critic, '_load_image_from_bytes', return_value=Image.new('RGB', (512, 512))):
            image_bytes = generate_test_image_bytes()
            anchor_bytes = generate_test_image_bytes()

            result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=anchor_bytes)

            assert result.passed is True
            assert result.overall_severity == SeverityLevel.ACCEPTABLE
            assert result.overall_score == 0.85
            assert result.rejection_reason is None
            assert result.critique_method == "siglip_reference_comparison"

            # Check identity dimension
            identity_dims = [d for d in result.dimensions if d.dimension == DimensionType.IDENTITY_MATCH]
            assert len(identity_dims) == 1
            identity_dim = identity_dims[0]
            assert identity_dim.severity == SeverityLevel.ACCEPTABLE
            assert identity_dim.measurement_method == "siglip_embedding_similarity"


def test_siglip_critic_low_similarity_fails():
    """SigLIPCritiqueAdapter fails with low similarity (< threshold)."""
    critic = SigLIPCritiqueAdapter(similarity_threshold=0.70)

    # Mock _compute_similarity to return low similarity
    with patch.object(critic, '_compute_similarity', return_value=0.45):
        with patch.object(critic, '_load_image_from_bytes', return_value=Image.new('RGB', (512, 512))):
            image_bytes = generate_test_image_bytes()
            anchor_bytes = generate_test_image_bytes()

            result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=anchor_bytes)

            assert result.passed is False
            assert result.rejection_reason is not None
            assert "low identity similarity" in result.rejection_reason.lower()
            assert result.critique_method == "siglip_reference_comparison"

            # Check identity dimension
            identity_dims = [d for d in result.dimensions if d.dimension == DimensionType.IDENTITY_MATCH]
            assert len(identity_dims) == 1
            identity_dim = identity_dims[0]
            assert identity_dim.severity in [SeverityLevel.MINOR, SeverityLevel.MAJOR]


# =============================================================================
# Threshold Boundary Tests
# =============================================================================

def test_siglip_critic_threshold_boundary_below():
    """SigLIPCritiqueAdapter fails just below threshold (0.69 < 0.70)."""
    critic = SigLIPCritiqueAdapter(similarity_threshold=0.70)

    with patch.object(critic, '_compute_similarity', return_value=0.69):
        with patch.object(critic, '_load_image_from_bytes', return_value=Image.new('RGB', (512, 512))):
            image_bytes = generate_test_image_bytes()
            anchor_bytes = generate_test_image_bytes()

            result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=anchor_bytes)

            assert result.passed is False


def test_siglip_critic_threshold_boundary_exact():
    """SigLIPCritiqueAdapter passes at exact threshold (0.70 == 0.70)."""
    critic = SigLIPCritiqueAdapter(similarity_threshold=0.70)

    with patch.object(critic, '_compute_similarity', return_value=0.70):
        with patch.object(critic, '_load_image_from_bytes', return_value=Image.new('RGB', (512, 512))):
            image_bytes = generate_test_image_bytes()
            anchor_bytes = generate_test_image_bytes()

            result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=anchor_bytes)

            assert result.passed is True


def test_siglip_critic_threshold_boundary_above():
    """SigLIPCritiqueAdapter passes just above threshold (0.71 > 0.70)."""
    critic = SigLIPCritiqueAdapter(similarity_threshold=0.70)

    with patch.object(critic, '_compute_similarity', return_value=0.71):
        with patch.object(critic, '_load_image_from_bytes', return_value=Image.new('RGB', (512, 512))):
            image_bytes = generate_test_image_bytes()
            anchor_bytes = generate_test_image_bytes()

            result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=anchor_bytes)

            assert result.passed is True


# =============================================================================
# Dimension Tests
# =============================================================================

def test_siglip_critic_skips_non_identity_dimensions():
    """SigLIPCritiqueAdapter skips non-identity dimensions."""
    critic = SigLIPCritiqueAdapter()
    image_bytes = generate_test_image_bytes()

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=None)

    # Check that non-identity dimensions are skipped
    for dim in result.dimensions:
        if dim.dimension != DimensionType.IDENTITY_MATCH:
            assert dim.score == 1.0
            assert dim.severity == SeverityLevel.ACCEPTABLE
            assert dim.measurement_method == "skipped"
            assert "earlier layers" in dim.reason or "optional" in dim.reason.lower()


def test_siglip_critic_dimensions_sorted():
    """SigLIPCritiqueAdapter returns dimensions sorted by type."""
    critic = SigLIPCritiqueAdapter()
    image_bytes = generate_test_image_bytes()

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=None)

    dimension_types = [d.dimension for d in result.dimensions]
    expected_order = [
        DimensionType.ARTIFACTING,
        DimensionType.COMPOSITION,
        DimensionType.IDENTITY_MATCH,
        DimensionType.READABILITY,
        DimensionType.STYLE_ADHERENCE,
    ]
    assert dimension_types == expected_order


# =============================================================================
# Error Handling Tests
# =============================================================================

def test_siglip_critic_empty_image_bytes_returns_error():
    """SigLIPCritiqueAdapter returns error for empty image bytes."""
    critic = SigLIPCritiqueAdapter()

    # Mock load to avoid actually loading model
    with patch.object(critic, 'load'):
        result = critic.critique(b"", DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=generate_test_image_bytes())

        assert result.passed is False
        assert result.overall_severity == SeverityLevel.CRITICAL
        assert "load failed" in result.rejection_reason.lower()
        assert result.critique_method == "siglip_error"


def test_siglip_critic_invalid_image_returns_error():
    """SigLIPCritiqueAdapter returns error for invalid image data."""
    critic = SigLIPCritiqueAdapter()

    # Mock load to avoid actually loading model
    with patch.object(critic, 'load'):
        result = critic.critique(
            b"not_an_image",
            DEFAULT_CRITIQUE_RUBRIC,
            anchor_image_bytes=generate_test_image_bytes()
        )

        assert result.passed is False
        assert result.overall_severity == SeverityLevel.CRITICAL
        assert "load failed" in result.rejection_reason.lower()


def test_siglip_critic_empty_anchor_bytes_returns_error():
    """SigLIPCritiqueAdapter returns error for empty anchor bytes."""
    critic = SigLIPCritiqueAdapter()
    image_bytes = generate_test_image_bytes()

    # Mock load to avoid actually loading model
    with patch.object(critic, 'load'):
        result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=b"")

        assert result.passed is False
        assert result.overall_severity == SeverityLevel.CRITICAL
        assert "load failed" in result.rejection_reason.lower()


# =============================================================================
# Factory Integration Tests
# =============================================================================

def test_create_image_critic_siglip_backend():
    """create_image_critic('siglip') returns SigLIPCritiqueAdapter."""
    critic = create_image_critic("siglip")
    assert isinstance(critic, SigLIPCritiqueAdapter)
    assert critic.similarity_threshold == 0.70  # Default


def test_create_image_critic_siglip_custom_config():
    """create_image_critic('siglip') accepts custom configuration."""
    critic = create_image_critic(
        "siglip",
        similarity_threshold=0.75,
        device="cpu"
    )
    assert isinstance(critic, SigLIPCritiqueAdapter)
    assert critic.similarity_threshold == 0.75
    assert critic.device == "cpu"


def test_siglip_critic_roundtrip_through_factory():
    """SigLIPCritiqueAdapter created via factory works correctly."""
    critic = create_image_critic("siglip", similarity_threshold=0.80)
    image_bytes = generate_test_image_bytes()

    # Should skip without anchor
    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=None)

    assert result.passed is True
    assert result.critique_method == "siglip_skipped"


# =============================================================================
# CritiqueResult Schema Compliance Tests
# =============================================================================

@patch('aidm.core.siglip_critique_adapter.open_clip')
@patch('aidm.core.siglip_critique_adapter.torch')
def test_siglip_critic_result_schema_compliance(mock_torch, mock_open_clip):
    """SigLIPCritiqueAdapter returns schema-compliant CritiqueResult."""
    mock_model = Mock()
    mock_model.eval = Mock()
    mock_preprocess = Mock(side_effect=lambda img: Mock(unsqueeze=Mock(return_value=Mock(to=Mock(return_value=Mock())))))
    mock_open_clip.create_model_and_transforms.return_value = (mock_model, None, mock_preprocess)

    mock_embedding = Mock()
    mock_embedding.norm = Mock(return_value=Mock(item=Mock(return_value=1.0)))
    mock_embedding.__truediv__ = Mock(return_value=mock_embedding)
    mock_embedding.__matmul__ = Mock(return_value=Mock(item=Mock(return_value=0.75)))
    mock_model.encode_image = Mock(return_value=mock_embedding)

    mock_torch.no_grad = MagicMock()

    critic = SigLIPCritiqueAdapter()
    image_bytes = generate_test_image_bytes()
    anchor_bytes = generate_test_image_bytes()

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, anchor_image_bytes=anchor_bytes)

    # Schema compliance checks
    assert isinstance(result.passed, bool)
    assert isinstance(result.overall_severity, SeverityLevel)
    assert isinstance(result.overall_score, float)
    assert 0.0 <= result.overall_score <= 1.0
    assert isinstance(result.critique_method, str)
    assert len(result.dimensions) == 5  # All 5 dimension types

    # Check all dimensions
    for dim in result.dimensions:
        assert isinstance(dim.dimension, DimensionType)
        assert isinstance(dim.severity, SeverityLevel)
        assert isinstance(dim.score, float)
        assert 0.0 <= dim.score <= 1.0
        assert isinstance(dim.reason, str)
        assert isinstance(dim.measurement_method, str)
