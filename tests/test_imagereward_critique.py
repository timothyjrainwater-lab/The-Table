"""Tests for ImageRewardCritiqueAdapter (Layer 2 image critique).

M3 IMPLEMENTATION TESTS
-----------------------
Tests GPU-based text-image alignment scoring using ImageReward model.
Validates score normalization, prompt handling, and dimension mapping.

Based on approved design: SONNET-C_WO-M3-IMAGE-CRITIQUE-02_imagereward_design.md

IMPORTANT: These tests use MOCKED ImageReward model to avoid requiring
actual model download (~1 GB). Tests verify adapter logic, not model accuracy.
"""

import pytest
import io
import sys
from PIL import Image
import numpy as np
from unittest.mock import Mock, MagicMock, patch


# =============================================================================
# Mock torch and ImageReward at module level (before imports)
# =============================================================================

_original_torch = sys.modules.get('torch')
_original_imagereward = sys.modules.get('ImageReward')

# Create mock torch module
mock_torch = MagicMock()
mock_torch.cuda.is_available.return_value = False
mock_torch.float16 = float
mock_torch.backends = MagicMock()
sys.modules['torch'] = mock_torch

# Create mock ImageReward module
mock_imagereward = MagicMock()
sys.modules['ImageReward'] = mock_imagereward

# Now we can import the adapter
from aidm.core.imagereward_critique_adapter import ImageRewardCritiqueAdapter
from aidm.schemas.image_critique import (
    CritiqueRubric,
    DimensionType,
    SeverityLevel,
    DEFAULT_CRITIQUE_RUBRIC,
)
from aidm.core.image_critique_adapter import ImageCritiqueAdapter, create_image_critic


@pytest.fixture(autouse=True, scope="module")
def _restore_torch_after_module():
    """Restore original sys.modules entries after this test module completes."""
    yield
    if _original_torch is not None:
        sys.modules['torch'] = _original_torch
    else:
        sys.modules.pop('torch', None)
    if _original_imagereward is not None:
        sys.modules['ImageReward'] = _original_imagereward
    else:
        sys.modules.pop('ImageReward', None)


# =============================================================================
# Test Image Generators
# =============================================================================

def generate_test_image_bytes(width: int = 512, height: int = 512, format: str = "PNG") -> bytes:
    """Generate simple test image bytes.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        format: Image format (PNG or JPEG)

    Returns:
        Image bytes
    """
    # Create simple gradient image
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    gradient = np.linspace(0, 255, width, dtype=np.uint8)
    img_array[:, :, 0] = np.tile(gradient, (height, 1))  # Red channel
    img_array[:, :, 1] = np.tile(gradient[::-1], (height, 1))  # Green channel
    img_array[:, :, 2] = 128  # Blue channel

    # Convert to PIL and encode
    pil_image = Image.fromarray(img_array, mode='RGB')
    buffer = io.BytesIO()
    pil_image.save(buffer, format=format)
    return buffer.getvalue()


# =============================================================================
# Mock ImageReward Model
# =============================================================================

class MockImageRewardModel:
    """Mock ImageReward model for testing without actual model download."""

    def __init__(self, score_value: float = 0.5):
        """Initialize mock model.

        Args:
            score_value: Score to return from score() method (range: [-1.0, +2.0])
        """
        self.score_value = score_value
        self.score_calls = []

    def score(self, prompt: str, image) -> float:
        """Mock ImageReward.score() method.

        Args:
            prompt: Text prompt
            image: PIL Image

        Returns:
            Mock score in ImageReward range [-1.0, +2.0]
        """
        self.score_calls.append({"prompt": prompt, "image": image})
        return self.score_value

    def half(self):
        """Mock model.half() for FP16 conversion."""
        return self


# =============================================================================
# Protocol Compliance Tests
# =============================================================================

def test_imagereward_adapter_implements_protocol():
    """ImageRewardCritiqueAdapter implements ImageCritiqueAdapter protocol."""
    adapter = ImageRewardCritiqueAdapter()
    assert isinstance(adapter, ImageCritiqueAdapter)


def test_imagereward_adapter_has_load_unload():
    """ImageRewardCritiqueAdapter has load/unload methods."""
    adapter = ImageRewardCritiqueAdapter()
    # Should not raise (though we won't actually load the model)
    # Test is just checking methods exist
    assert hasattr(adapter, "load")
    assert hasattr(adapter, "unload")


# =============================================================================
# Initialization Tests
# =============================================================================

def test_imagereward_adapter_default_initialization():
    """ImageRewardCritiqueAdapter initializes with default parameters."""
    adapter = ImageRewardCritiqueAdapter()
    assert adapter.model_name == "ImageReward-v1.0"
    assert adapter.alignment_threshold == 0.0
    assert adapter.model is None
    assert adapter.device in ["cuda", "mps", "cpu"]


def test_imagereward_adapter_custom_initialization():
    """ImageRewardCritiqueAdapter initializes with custom parameters."""
    adapter = ImageRewardCritiqueAdapter(
        model_name="custom-model",
        device="cpu",
        alignment_threshold=0.5,
    )
    assert adapter.model_name == "custom-model"
    assert adapter.device == "cpu"
    assert adapter.alignment_threshold == 0.5


def test_imagereward_adapter_auto_device_detection():
    """ImageRewardCritiqueAdapter auto-detects compute device."""
    adapter = ImageRewardCritiqueAdapter()
    # Should auto-detect to one of: cuda, mps, cpu
    assert adapter.device in ["cuda", "mps", "cpu"]


# =============================================================================
# Score Normalization Tests
# =============================================================================

def test_imagereward_adapter_score_normalization_negative():
    """ImageRewardCritiqueAdapter normalizes negative scores correctly."""
    adapter = ImageRewardCritiqueAdapter()
    # Score -1.0 → normalized 0.0
    normalized = adapter._normalize_score(-1.0)
    assert abs(normalized - 0.0) < 0.01


def test_imagereward_adapter_score_normalization_zero():
    """ImageRewardCritiqueAdapter normalizes zero score correctly."""
    adapter = ImageRewardCritiqueAdapter()
    # Score 0.0 → normalized 0.333
    normalized = adapter._normalize_score(0.0)
    assert abs(normalized - 0.333) < 0.01


def test_imagereward_adapter_score_normalization_positive():
    """ImageRewardCritiqueAdapter normalizes positive scores correctly."""
    adapter = ImageRewardCritiqueAdapter()
    # Score 2.0 → normalized 1.0
    normalized = adapter._normalize_score(2.0)
    assert abs(normalized - 1.0) < 0.01


def test_imagereward_adapter_score_normalization_clipping():
    """ImageRewardCritiqueAdapter clips out-of-range scores."""
    adapter = ImageRewardCritiqueAdapter()
    # Test edge cases beyond expected range
    assert adapter._normalize_score(-2.0) == 0.0  # Clip to 0.0
    assert adapter._normalize_score(3.0) == 1.0   # Clip to 1.0


# =============================================================================
# Critique Tests (with Mocked Model)
# =============================================================================

def test_imagereward_adapter_critique_requires_prompt():
    """ImageRewardCritiqueAdapter requires prompt parameter."""
    adapter = ImageRewardCritiqueAdapter()
    image_bytes = generate_test_image_bytes()

    # Critique without prompt should return error
    result = adapter.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt=None)

    assert result.passed is False
    assert result.overall_severity == SeverityLevel.CRITICAL
    assert "requires prompt" in result.rejection_reason.lower()
    assert result.critique_method == "imagereward_error"


def test_imagereward_adapter_critique_with_valid_prompt():
    """ImageRewardCritiqueAdapter critiques image with valid prompt."""
    # Setup mock ImageReward model
    mock_model = MockImageRewardModel(score_value=0.5)
    mock_imagereward.load.return_value = mock_model

    adapter = ImageRewardCritiqueAdapter(device="cpu")
    image_bytes = generate_test_image_bytes()
    prompt = "A beautiful landscape"

    result = adapter.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt=prompt)

    assert result.critique_method == "imagereward_gpu"
    assert len(result.dimensions) == 5
    # Check that model was called with prompt
    assert len(mock_model.score_calls) == 1
    assert mock_model.score_calls[0]["prompt"] == prompt


def test_imagereward_adapter_high_score_passes():
    """ImageRewardCritiqueAdapter passes image with high alignment score."""
    # High score (1.5 → normalized ~0.83)
    mock_model = MockImageRewardModel(score_value=1.5)
    mock_imagereward.load.return_value = mock_model

    adapter = ImageRewardCritiqueAdapter(device="cpu")
    image_bytes = generate_test_image_bytes()

    result = adapter.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt="test prompt")

    assert result.passed is True
    assert result.overall_severity == SeverityLevel.ACCEPTABLE
    assert result.rejection_reason is None


def test_imagereward_adapter_low_score_fails():
    """ImageRewardCritiqueAdapter fails image with low alignment score."""
    # Low score (-0.8 → normalized ~0.07)
    mock_model = MockImageRewardModel(score_value=-0.8)
    mock_imagereward.load.return_value = mock_model

    adapter = ImageRewardCritiqueAdapter(device="cpu")
    image_bytes = generate_test_image_bytes()

    result = adapter.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt="test prompt")

    assert result.passed is False
    assert result.rejection_reason is not None


# =============================================================================
# Dimension Tests
# =============================================================================

def test_imagereward_adapter_skips_layer1_dimensions():
    """ImageRewardCritiqueAdapter skips Layer 1 dimensions (heuristics)."""
    mock_model = MockImageRewardModel(score_value=0.5)
    mock_imagereward.load.return_value = mock_model

    adapter = ImageRewardCritiqueAdapter(device="cpu")
    image_bytes = generate_test_image_bytes()

    result = adapter.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt="test")

    # Check skipped dimensions
    artifact_dim = [d for d in result.dimensions if d.dimension == DimensionType.ARTIFACTING][0]
    composition_dim = [d for d in result.dimensions if d.dimension == DimensionType.COMPOSITION][0]
    readability_dim = [d for d in result.dimensions if d.dimension == DimensionType.READABILITY][0]

    assert artifact_dim.score == 1.0
    assert artifact_dim.measurement_method == "skipped"
    assert composition_dim.score == 1.0
    assert composition_dim.measurement_method == "skipped"
    assert readability_dim.score == 1.0
    assert readability_dim.measurement_method == "skipped"


def test_imagereward_adapter_scores_identity_dimension():
    """ImageRewardCritiqueAdapter scores IDENTITY_MATCH dimension."""
    mock_model = MockImageRewardModel(score_value=0.5)
    mock_imagereward.load.return_value = mock_model

    adapter = ImageRewardCritiqueAdapter(device="cpu")
    image_bytes = generate_test_image_bytes()

    result = adapter.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt="test")

    identity_dim = [d for d in result.dimensions if d.dimension == DimensionType.IDENTITY_MATCH][0]
    assert identity_dim.score < 1.0
    assert identity_dim.measurement_method == "imagereward_alignment"
    assert "alignment score" in identity_dim.reason.lower()


def test_imagereward_adapter_scores_style_dimension():
    """ImageRewardCritiqueAdapter scores STYLE_ADHERENCE dimension."""
    mock_model = MockImageRewardModel(score_value=0.5)
    mock_imagereward.load.return_value = mock_model

    adapter = ImageRewardCritiqueAdapter(device="cpu")
    image_bytes = generate_test_image_bytes()

    result = adapter.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt="test")

    style_dim = [d for d in result.dimensions if d.dimension == DimensionType.STYLE_ADHERENCE][0]
    assert style_dim.score < 1.0
    assert style_dim.measurement_method == "imagereward_alignment"
    assert "alignment score" in style_dim.reason.lower()


def test_imagereward_adapter_dimensions_sorted():
    """ImageRewardCritiqueAdapter returns dimensions sorted by type."""
    mock_model = MockImageRewardModel(score_value=0.5)
    mock_imagereward.load.return_value = mock_model

    adapter = ImageRewardCritiqueAdapter(device="cpu")
    image_bytes = generate_test_image_bytes()

    result = adapter.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt="test")

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
# Model Loading Tests
# =============================================================================

def test_imagereward_adapter_lazy_load():
    """ImageRewardCritiqueAdapter lazy-loads model on first critique."""
    mock_model = MockImageRewardModel(score_value=0.5)
    mock_imagereward.load.return_value = mock_model

    adapter = ImageRewardCritiqueAdapter(device="cpu")
    assert adapter.model is None

    # First critique should trigger load
    image_bytes = generate_test_image_bytes()
    result = adapter.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt="test")

    assert adapter.model is not None
    assert mock_imagereward.load.called


def test_imagereward_adapter_unload_clears_model():
    """ImageRewardCritiqueAdapter.unload() clears model from memory."""
    mock_model = MockImageRewardModel(score_value=0.5)
    mock_imagereward.load.return_value = mock_model

    adapter = ImageRewardCritiqueAdapter(device="cpu")
    image_bytes = generate_test_image_bytes()
    adapter.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt="test")

    # Model should be loaded
    assert adapter.model is not None

    # Unload
    adapter.unload()
    assert adapter.model is None


# =============================================================================
# Error Handling Tests
# =============================================================================

def test_imagereward_adapter_empty_bytes_returns_error():
    """ImageRewardCritiqueAdapter returns error for empty bytes."""
    mock_model = MockImageRewardModel(score_value=0.5)
    mock_imagereward.load.return_value = mock_model

    adapter = ImageRewardCritiqueAdapter(device="cpu")

    result = adapter.critique(b"", DEFAULT_CRITIQUE_RUBRIC, prompt="test")

    assert result.passed is False
    assert result.overall_severity == SeverityLevel.CRITICAL
    assert "failed" in result.rejection_reason.lower()


def test_imagereward_adapter_invalid_image_returns_error():
    """ImageRewardCritiqueAdapter returns error for invalid image data."""
    mock_model = MockImageRewardModel(score_value=0.5)
    mock_imagereward.load.return_value = mock_model

    adapter = ImageRewardCritiqueAdapter(device="cpu")

    result = adapter.critique(b"not_an_image", DEFAULT_CRITIQUE_RUBRIC, prompt="test")

    assert result.passed is False
    assert result.overall_severity == SeverityLevel.CRITICAL


# =============================================================================
# Factory Integration Tests
# =============================================================================

def test_create_image_critic_imagereward_backend():
    """create_image_critic('imagereward') returns ImageRewardCritiqueAdapter."""
    critic = create_image_critic("imagereward")
    assert isinstance(critic, ImageRewardCritiqueAdapter)
    assert critic.model_name == "ImageReward-v1.0"


def test_create_image_critic_imagereward_custom_config():
    """create_image_critic('imagereward') accepts custom configuration."""
    critic = create_image_critic(
        "imagereward",
        device="cpu",
        alignment_threshold=0.5,
    )
    assert isinstance(critic, ImageRewardCritiqueAdapter)
    assert critic.device == "cpu"
    assert critic.alignment_threshold == 0.5


def test_imagereward_adapter_roundtrip_through_factory():
    """ImageRewardCritiqueAdapter created via factory works correctly."""
    # Use high score (1.5 → normalized ~0.83, above threshold)
    mock_model = MockImageRewardModel(score_value=1.5)
    mock_imagereward.load.return_value = mock_model

    critic = create_image_critic("imagereward", device="cpu")
    image_bytes = generate_test_image_bytes()

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC, prompt="test prompt")

    assert result.passed is True
    assert result.critique_method == "imagereward_gpu"
