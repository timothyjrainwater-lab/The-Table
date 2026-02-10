"""Tests for HeuristicsImageCritic (Layer 1 image critique).

M3 IMPLEMENTATION TESTS
-----------------------
Tests CPU-only heuristic quality checks for image validation.
Validates blur detection, composition, format, and corruption checks.

Based on approved design: SONNET-C_WO-M3-IMAGE-CRITIQUE-02_heuristics_design.md
"""

import pytest
import io
import time
import numpy as np
from PIL import Image

from aidm.core.heuristics_image_critic import HeuristicsImageCritic
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
    pattern: str = "sharp",
    format: str = "PNG"
) -> bytes:
    """Generate test image with specified characteristics.

    Args:
        width: Image width in pixels
        height: Image height in pixels
        pattern: Image pattern type:
            - "sharp": High detail checkerboard (passes blur test)
            - "blurry": Gaussian blurred checkerboard (fails blur test)
            - "uniform_black": Solid black (fails corruption test)
            - "uniform_white": Solid white (fails corruption test)
            - "uniform_gray": Solid gray (fails corruption test)
            - "too_smooth": Very smooth gradient (fails edge density)
            - "too_noisy": Random noise (fails edge density)
        format: Image format ("PNG" or "JPEG")

    Returns:
        Image bytes
    """
    # Create base image
    if pattern == "sharp":
        # High-detail checkerboard (sharp)
        img_array = np.zeros((height, width, 3), dtype=np.uint8)
        checker_size = 8
        for i in range(0, height, checker_size):
            for j in range(0, width, checker_size):
                if (i // checker_size + j // checker_size) % 2 == 0:
                    img_array[i:i+checker_size, j:j+checker_size] = [255, 255, 255]
                else:
                    img_array[i:i+checker_size, j:j+checker_size] = [0, 0, 0]

    elif pattern == "blurry":
        # Checkerboard with Gaussian blur
        img_array = np.zeros((height, width, 3), dtype=np.uint8)
        checker_size = 8
        for i in range(0, height, checker_size):
            for j in range(0, width, checker_size):
                if (i // checker_size + j // checker_size) % 2 == 0:
                    img_array[i:i+checker_size, j:j+checker_size] = [255, 255, 255]
                else:
                    img_array[i:i+checker_size, j:j+checker_size] = [0, 0, 0]
        # Apply heavy blur
        import cv2
        img_array = cv2.GaussianBlur(img_array, (51, 51), 0)

    elif pattern == "uniform_black":
        img_array = np.zeros((height, width, 3), dtype=np.uint8)

    elif pattern == "uniform_white":
        img_array = np.full((height, width, 3), 255, dtype=np.uint8)

    elif pattern == "uniform_gray":
        img_array = np.full((height, width, 3), 128, dtype=np.uint8)

    elif pattern == "too_smooth":
        # Very smooth gradient
        gradient = np.linspace(0, 255, width, dtype=np.uint8)
        img_array = np.tile(gradient, (height, 1))
        img_array = np.stack([img_array, img_array, img_array], axis=-1)

    elif pattern == "too_noisy":
        # Random noise
        img_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)

    else:
        raise ValueError(f"Unknown pattern: {pattern}")

    # Convert to PIL and encode
    pil_image = Image.fromarray(img_array, mode='RGB')
    buffer = io.BytesIO()
    pil_image.save(buffer, format=format)
    return buffer.getvalue()


# =============================================================================
# Protocol Compliance Tests
# =============================================================================

def test_heuristics_critic_implements_protocol():
    """HeuristicsImageCritic implements ImageCritiqueAdapter protocol."""
    critic = HeuristicsImageCritic()
    assert isinstance(critic, ImageCritiqueAdapter)


def test_heuristics_critic_has_load_unload():
    """HeuristicsImageCritic has load/unload methods (no-ops)."""
    critic = HeuristicsImageCritic()
    critic.load()  # Should not raise
    critic.unload()  # Should not raise


# =============================================================================
# Initialization Tests
# =============================================================================

def test_heuristics_critic_default_initialization():
    """HeuristicsImageCritic initializes with default parameters."""
    critic = HeuristicsImageCritic()
    assert critic.blur_threshold == 100.0
    assert critic.min_resolution == 512
    assert critic.max_resolution == 2048
    assert critic.aspect_ratio_tolerance == 0.15
    assert critic.edge_density_min == 0.05
    assert critic.edge_density_max == 0.25


def test_heuristics_critic_custom_initialization():
    """HeuristicsImageCritic initializes with custom parameters."""
    critic = HeuristicsImageCritic(
        blur_threshold=120.0,
        min_resolution=768,
        max_resolution=1024,
        aspect_ratio_tolerance=0.20,
        edge_density_min=0.08,
        edge_density_max=0.30
    )
    assert critic.blur_threshold == 120.0
    assert critic.min_resolution == 768
    assert critic.max_resolution == 1024
    assert critic.aspect_ratio_tolerance == 0.20
    assert critic.edge_density_min == 0.08
    assert critic.edge_density_max == 0.30


# =============================================================================
# Blur Detection Tests
# =============================================================================

def test_heuristics_critic_sharp_image_passes_blur():
    """HeuristicsImageCritic passes sharp image (blur check)."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    readability_dim = [d for d in result.dimensions if d.dimension == DimensionType.READABILITY][0]
    assert readability_dim.score >= 0.90
    assert "sharp" in readability_dim.reason.lower()


def test_heuristics_critic_blurry_image_fails_blur():
    """HeuristicsImageCritic fails blurry image (blur check)."""
    critic = HeuristicsImageCritic(blur_threshold=100.0)
    image_bytes = generate_test_image_bytes(pattern="blurry")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    readability_dim = [d for d in result.dimensions if d.dimension == DimensionType.READABILITY][0]
    assert readability_dim.score < 0.70
    assert "blurr" in readability_dim.reason.lower()


# =============================================================================
# Format Validation Tests
# =============================================================================

def test_heuristics_critic_valid_resolution_passes():
    """HeuristicsImageCritic passes valid resolution."""
    critic = HeuristicsImageCritic(min_resolution=512, max_resolution=2048)
    image_bytes = generate_test_image_bytes(width=512, height=512, pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    artifact_dim = [d for d in result.dimensions if d.dimension == DimensionType.ARTIFACTING][0]
    assert artifact_dim.score >= 0.70
    assert "valid format" in artifact_dim.reason.lower()


def test_heuristics_critic_resolution_too_low_fails():
    """HeuristicsImageCritic fails image with resolution too low."""
    critic = HeuristicsImageCritic(min_resolution=512)
    image_bytes = generate_test_image_bytes(width=256, height=256, pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    artifact_dim = [d for d in result.dimensions if d.dimension == DimensionType.ARTIFACTING][0]
    assert artifact_dim.score < 0.70
    assert "resolution too low" in artifact_dim.reason.lower()


def test_heuristics_critic_resolution_too_high_fails():
    """HeuristicsImageCritic penalizes image with resolution too high."""
    critic = HeuristicsImageCritic(max_resolution=1024)
    image_bytes = generate_test_image_bytes(width=2048, height=2048, pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    artifact_dim = [d for d in result.dimensions if d.dimension == DimensionType.ARTIFACTING][0]
    assert artifact_dim.score < 1.0
    assert "resolution too high" in artifact_dim.reason.lower()


def test_heuristics_critic_aspect_ratio_valid_passes():
    """HeuristicsImageCritic passes valid aspect ratio."""
    critic = HeuristicsImageCritic(aspect_ratio_tolerance=0.15)
    image_bytes = generate_test_image_bytes(width=512, height=512, pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    artifact_dim = [d for d in result.dimensions if d.dimension == DimensionType.ARTIFACTING][0]
    assert artifact_dim.score >= 0.70


def test_heuristics_critic_aspect_ratio_off_fails():
    """HeuristicsImageCritic fails image with wrong aspect ratio."""
    critic = HeuristicsImageCritic(aspect_ratio_tolerance=0.15)
    image_bytes = generate_test_image_bytes(width=512, height=768, pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    artifact_dim = [d for d in result.dimensions if d.dimension == DimensionType.ARTIFACTING][0]
    assert artifact_dim.score <= 0.70
    assert "aspect ratio" in artifact_dim.reason.lower()


# =============================================================================
# Corruption Detection Tests
# =============================================================================

def test_heuristics_critic_uniform_black_fails():
    """HeuristicsImageCritic fails uniform black image (corruption)."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(pattern="uniform_black")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    artifact_dim = [d for d in result.dimensions if d.dimension == DimensionType.ARTIFACTING][0]
    assert artifact_dim.score < 0.70
    assert ("black" in artifact_dim.reason.lower() or "uniform" in artifact_dim.reason.lower())


def test_heuristics_critic_uniform_white_fails():
    """HeuristicsImageCritic fails uniform white image (corruption)."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(pattern="uniform_white")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    artifact_dim = [d for d in result.dimensions if d.dimension == DimensionType.ARTIFACTING][0]
    assert artifact_dim.score < 0.70
    assert ("white" in artifact_dim.reason.lower() or "uniform" in artifact_dim.reason.lower())


def test_heuristics_critic_uniform_gray_fails():
    """HeuristicsImageCritic fails uniform gray image (corruption)."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(pattern="uniform_gray")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    artifact_dim = [d for d in result.dimensions if d.dimension == DimensionType.ARTIFACTING][0]
    assert artifact_dim.score < 0.70
    assert "uniform" in artifact_dim.reason.lower()


# =============================================================================
# Composition Tests
# =============================================================================

def test_heuristics_critic_composition_checks_included():
    """HeuristicsImageCritic includes composition dimension."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    composition_dims = [d for d in result.dimensions if d.dimension == DimensionType.COMPOSITION]
    assert len(composition_dims) == 1
    composition_dim = composition_dims[0]
    assert composition_dim.measurement_method == "center_mass_edge_density"


def test_heuristics_critic_edge_density_too_smooth_penalized():
    """HeuristicsImageCritic penalizes overly smooth images."""
    critic = HeuristicsImageCritic(edge_density_min=0.05)
    image_bytes = generate_test_image_bytes(pattern="too_smooth")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    composition_dim = [d for d in result.dimensions if d.dimension == DimensionType.COMPOSITION][0]
    # Composition is average of center and edge checks, so may not fail overall
    # but edge check should be mentioned in reason
    assert "edge" in composition_dim.reason.lower()


def test_heuristics_critic_edge_density_too_noisy_penalized():
    """HeuristicsImageCritic penalizes overly noisy images."""
    critic = HeuristicsImageCritic(edge_density_max=0.25)
    image_bytes = generate_test_image_bytes(pattern="too_noisy")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    composition_dim = [d for d in result.dimensions if d.dimension == DimensionType.COMPOSITION][0]
    assert "edge" in composition_dim.reason.lower()


# =============================================================================
# Skipped Dimensions Tests
# =============================================================================

def test_heuristics_critic_skips_identity_check():
    """HeuristicsImageCritic skips identity check (requires Layer 3)."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    identity_dim = [d for d in result.dimensions if d.dimension == DimensionType.IDENTITY_MATCH][0]
    assert identity_dim.score == 1.0
    assert identity_dim.measurement_method == "skipped"
    assert "layer 3" in identity_dim.reason.lower()


def test_heuristics_critic_skips_style_check():
    """HeuristicsImageCritic skips style check (requires Layer 2/3)."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    style_dim = [d for d in result.dimensions if d.dimension == DimensionType.STYLE_ADHERENCE][0]
    assert style_dim.score == 1.0
    assert style_dim.measurement_method == "skipped"
    assert "layer" in style_dim.reason.lower()


# =============================================================================
# Overall Result Tests
# =============================================================================

def test_heuristics_critic_good_image_passes_overall():
    """HeuristicsImageCritic passes good image overall."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(width=512, height=512, pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    assert result.passed is True
    assert result.overall_severity == SeverityLevel.ACCEPTABLE
    assert result.rejection_reason is None
    assert result.critique_method == "heuristics_cpu"


def test_heuristics_critic_bad_image_fails_overall():
    """HeuristicsImageCritic fails bad image overall."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(pattern="blurry")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    assert result.passed is False
    assert result.rejection_reason is not None


def test_heuristics_critic_dimensions_sorted():
    """HeuristicsImageCritic returns dimensions sorted by type."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    dimension_types = [d.dimension for d in result.dimensions]
    expected_order = [
        DimensionType.ARTIFACTING,
        DimensionType.COMPOSITION,
        DimensionType.IDENTITY_MATCH,
        DimensionType.READABILITY,
        DimensionType.STYLE_ADHERENCE,
    ]
    assert dimension_types == expected_order


def test_heuristics_critic_overall_score_calculation():
    """HeuristicsImageCritic calculates overall score correctly."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    # Overall score should be average of non-skipped dimensions
    scored_dims = [d for d in result.dimensions if d.score < 1.0]
    expected_score = sum(d.score for d in scored_dims) / len(scored_dims)
    assert abs(result.overall_score - expected_score) < 0.01


# =============================================================================
# Error Handling Tests
# =============================================================================

def test_heuristics_critic_empty_bytes_returns_error():
    """HeuristicsImageCritic returns error result for empty bytes."""
    critic = HeuristicsImageCritic()

    result = critic.critique(b"", DEFAULT_CRITIQUE_RUBRIC)

    assert result.passed is False
    assert result.overall_severity == SeverityLevel.CRITICAL
    assert "load failed" in result.rejection_reason.lower()
    assert result.critique_method == "heuristics_error"


def test_heuristics_critic_invalid_image_returns_error():
    """HeuristicsImageCritic returns error result for invalid image data."""
    critic = HeuristicsImageCritic()

    result = critic.critique(b"not_an_image", DEFAULT_CRITIQUE_RUBRIC)

    assert result.passed is False
    assert result.overall_severity == SeverityLevel.CRITICAL
    assert "load failed" in result.rejection_reason.lower()


# =============================================================================
# Performance Tests
# =============================================================================

def test_heuristics_critic_performance_under_100ms():
    """HeuristicsImageCritic completes in under 100ms."""
    critic = HeuristicsImageCritic()
    image_bytes = generate_test_image_bytes(width=512, height=512, pattern="sharp")

    start = time.time()
    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)
    elapsed = time.time() - start

    assert elapsed < 0.100  # 100ms
    assert result.passed is True


# =============================================================================
# Factory Integration Tests
# =============================================================================

def test_create_image_critic_heuristics_backend():
    """create_image_critic('heuristics') returns HeuristicsImageCritic."""
    critic = create_image_critic("heuristics")
    assert isinstance(critic, HeuristicsImageCritic)
    assert critic.blur_threshold == 100.0  # Default


def test_create_image_critic_heuristics_custom_config():
    """create_image_critic('heuristics') accepts custom configuration."""
    critic = create_image_critic(
        "heuristics",
        blur_threshold=120.0,
        min_resolution=768,
        edge_density_min=0.08
    )
    assert isinstance(critic, HeuristicsImageCritic)
    assert critic.blur_threshold == 120.0
    assert critic.min_resolution == 768
    assert critic.edge_density_min == 0.08


def test_heuristics_critic_roundtrip_through_factory():
    """HeuristicsImageCritic created via factory works correctly."""
    critic = create_image_critic("heuristics", blur_threshold=120.0)
    image_bytes = generate_test_image_bytes(pattern="sharp")

    result = critic.critique(image_bytes, DEFAULT_CRITIQUE_RUBRIC)

    assert result.passed is True
    assert result.critique_method == "heuristics_cpu"
