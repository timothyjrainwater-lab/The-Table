"""Tests for GraduatedCritiqueOrchestrator (graduated critique pipeline).

M3 IMPLEMENTATION TESTS
-----------------------
Tests the orchestration logic for running Layer 1 → Layer 2 → Layer 3
with short-circuiting on failure and dimension merging.

Based on approved design: SONNET-C_WO-M3-IMAGE-CRITIQUE-02_prep_integration.md
"""

import pytest
from unittest.mock import Mock, MagicMock, call
from aidm.core.graduated_critique_orchestrator import GraduatedCritiqueOrchestrator
from aidm.schemas.image_critique import (
    CritiqueResult,
    CritiqueRubric,
    CritiqueDimension,
    DimensionType,
    SeverityLevel,
    DEFAULT_CRITIQUE_RUBRIC,
)
from aidm.core.image_critique_adapter import ImageCritiqueAdapter, create_image_critic


# =============================================================================
# Helper Functions
# =============================================================================

def create_mock_dimension(
    dimension_type: DimensionType,
    score: float,
    severity: SeverityLevel = SeverityLevel.ACCEPTABLE,
    reason: str = "test",
    measurement_method: str = "mock"
) -> CritiqueDimension:
    """Create a mock CritiqueDimension."""
    return CritiqueDimension(
        dimension=dimension_type,
        severity=severity,
        score=score,
        reason=reason,
        measurement_method=measurement_method
    )


def create_mock_result(
    passed: bool = True,
    dimensions: list = None,
    overall_score: float = 0.85,
    overall_severity: SeverityLevel = SeverityLevel.ACCEPTABLE,
    rejection_reason: str = None,
    critique_method: str = "mock"
) -> CritiqueResult:
    """Create a mock CritiqueResult."""
    if dimensions is None:
        # Create default dimensions (sorted)
        dimensions = [
            create_mock_dimension(DimensionType.ARTIFACTING, 0.90),
            create_mock_dimension(DimensionType.COMPOSITION, 0.85),
            create_mock_dimension(DimensionType.IDENTITY_MATCH, 1.0),
            create_mock_dimension(DimensionType.READABILITY, 0.80),
            create_mock_dimension(DimensionType.STYLE_ADHERENCE, 1.0),
        ]

    return CritiqueResult(
        passed=passed,
        overall_severity=overall_severity,
        dimensions=dimensions,
        overall_score=overall_score,
        rejection_reason=rejection_reason,
        critique_method=critique_method
    )


def create_mock_adapter(result: CritiqueResult) -> Mock:
    """Create a mock ImageCritiqueAdapter."""
    mock = Mock(spec=ImageCritiqueAdapter)
    mock.critique.return_value = result
    mock.load = Mock()
    mock.unload = Mock()
    return mock


# =============================================================================
# Initialization Tests
# =============================================================================

def test_orchestrator_requires_layer1():
    """GraduatedCritiqueOrchestrator requires layer1 (heuristics)."""
    with pytest.raises(ValueError, match="layer1.*required"):
        GraduatedCritiqueOrchestrator(layer1=None)


def test_orchestrator_accepts_layer1_only():
    """GraduatedCritiqueOrchestrator accepts layer1 only (L2/L3 optional)."""
    layer1 = create_mock_adapter(create_mock_result())
    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1)
    assert orchestrator.layer1 is layer1
    assert orchestrator.layer2 is None
    assert orchestrator.layer3 is None


def test_orchestrator_accepts_all_layers():
    """GraduatedCritiqueOrchestrator accepts all three layers."""
    layer1 = create_mock_adapter(create_mock_result())
    layer2 = create_mock_adapter(create_mock_result())
    layer3 = create_mock_adapter(create_mock_result())

    orchestrator = GraduatedCritiqueOrchestrator(
        layer1=layer1,
        layer2=layer2,
        layer3=layer3
    )

    assert orchestrator.layer1 is layer1
    assert orchestrator.layer2 is layer2
    assert orchestrator.layer3 is layer3


# =============================================================================
# Layer 1 Only Pipeline Tests
# =============================================================================

def test_l1_only_pass():
    """L1-only pipeline: L1 pass → overall pass."""
    layer1_result = create_mock_result(passed=True, critique_method="heuristics_cpu")
    layer1 = create_mock_adapter(layer1_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1)
    result = orchestrator.critique(b"image_data", DEFAULT_CRITIQUE_RUBRIC)

    assert result.passed is True
    assert result.critique_method == "graduated_l1"
    assert layer1.critique.called


def test_l1_only_fail():
    """L1-only pipeline: L1 fail → overall fail, short-circuit."""
    layer1_result = create_mock_result(
        passed=False,
        overall_score=0.50,
        rejection_reason="Blurry image",
        critique_method="heuristics_cpu"
    )
    layer1 = create_mock_adapter(layer1_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1)
    result = orchestrator.critique(b"image_data", DEFAULT_CRITIQUE_RUBRIC)

    assert result.passed is False
    assert result.critique_method == "graduated_l1"
    assert result.rejection_reason == "Blurry image"
    assert layer1.critique.called


# =============================================================================
# Layer 1 + Layer 2 Pipeline Tests
# =============================================================================

def test_l1_l2_both_pass():
    """L1+L2 pipeline: L1 pass, L2 pass → overall pass."""
    layer1_result = create_mock_result(passed=True, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(passed=True, critique_method="imagereward")

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2)
    result = orchestrator.critique(b"image_data", DEFAULT_CRITIQUE_RUBRIC, prompt="test prompt")

    assert result.passed is True
    assert result.critique_method == "graduated_l1_l2"
    assert layer1.critique.called
    assert layer2.critique.called
    # Verify VRAM management
    assert layer2.load.called
    assert layer2.unload.called


def test_l1_pass_l2_fail():
    """L1+L2 pipeline: L1 pass, L2 fail → overall fail, L3 not called."""
    layer1_result = create_mock_result(passed=True, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(
        passed=False,
        rejection_reason="Text-image misalignment",
        critique_method="imagereward"
    )

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2)
    result = orchestrator.critique(b"image_data", DEFAULT_CRITIQUE_RUBRIC)

    assert result.passed is False
    assert result.critique_method == "graduated_l1_l2"
    assert result.rejection_reason == "Text-image misalignment"
    assert layer1.critique.called
    assert layer2.critique.called


def test_l1_fail_l2_not_called():
    """L1+L2 pipeline: L1 fail → L2 not called (short-circuit)."""
    layer1_result = create_mock_result(
        passed=False,
        rejection_reason="Blurry",
        critique_method="heuristics_cpu"
    )

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(create_mock_result())

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2)
    result = orchestrator.critique(b"image_data", DEFAULT_CRITIQUE_RUBRIC)

    assert result.passed is False
    assert result.critique_method == "graduated_l1"
    assert layer1.critique.called
    assert not layer2.critique.called  # Short-circuit
    assert not layer2.load.called  # Should not load if not critiquing


# =============================================================================
# Full Pipeline (L1 + L2 + L3) Tests
# =============================================================================

def test_l1_l2_l3_all_pass():
    """Full pipeline: L1 pass, L2 pass, L3 pass → overall pass."""
    layer1_result = create_mock_result(passed=True, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(passed=True, critique_method="imagereward")
    layer3_result = create_mock_result(passed=True, critique_method="siglip")

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)
    layer3 = create_mock_adapter(layer3_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2, layer3=layer3)
    result = orchestrator.critique(
        b"image_data",
        DEFAULT_CRITIQUE_RUBRIC,
        anchor_image_bytes=b"anchor_data"
    )

    assert result.passed is True
    assert result.critique_method == "graduated_l1_l2_l3"
    assert layer1.critique.called
    assert layer2.critique.called
    assert layer3.critique.called
    # Verify VRAM management
    assert layer2.load.called and layer2.unload.called
    assert layer3.load.called and layer3.unload.called


def test_l1_l2_pass_l3_fail():
    """Full pipeline: L1 pass, L2 pass, L3 fail → merged result with overall fail."""
    layer1_result = create_mock_result(passed=True, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(passed=True, critique_method="imagereward")
    layer3_result = create_mock_result(
        passed=False,
        rejection_reason="Identity mismatch",
        critique_method="siglip"
    )

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)
    layer3 = create_mock_adapter(layer3_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2, layer3=layer3)
    result = orchestrator.critique(
        b"image_data",
        DEFAULT_CRITIQUE_RUBRIC,
        anchor_image_bytes=b"anchor_data"
    )

    assert result.passed is False
    assert result.critique_method == "graduated_l1_l2_l3"
    assert result.rejection_reason == "Identity mismatch"
    assert layer1.critique.called
    assert layer2.critique.called
    assert layer3.critique.called


def test_l3_skip_when_no_anchor():
    """Full pipeline: L1 pass, L2 pass, no anchor → L3 skipped."""
    layer1_result = create_mock_result(passed=True, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(passed=True, critique_method="imagereward")

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)
    layer3 = create_mock_adapter(create_mock_result())

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2, layer3=layer3)
    result = orchestrator.critique(
        b"image_data",
        DEFAULT_CRITIQUE_RUBRIC,
        anchor_image_bytes=None  # No anchor
    )

    assert result.passed is True
    assert result.critique_method == "graduated_l1_l2"  # L3 not run
    assert layer1.critique.called
    assert layer2.critique.called
    assert not layer3.critique.called  # Skipped (no anchor)
    assert not layer3.load.called


def test_l1_fail_l2_l3_not_called():
    """Full pipeline: L1 fail → L2 and L3 not called (short-circuit)."""
    layer1_result = create_mock_result(
        passed=False,
        rejection_reason="Blurry",
        critique_method="heuristics_cpu"
    )

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(create_mock_result())
    layer3 = create_mock_adapter(create_mock_result())

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2, layer3=layer3)
    result = orchestrator.critique(
        b"image_data",
        DEFAULT_CRITIQUE_RUBRIC,
        anchor_image_bytes=b"anchor_data"
    )

    assert result.passed is False
    assert result.critique_method == "graduated_l1"
    assert layer1.critique.called
    assert not layer2.critique.called  # Short-circuit
    assert not layer3.critique.called  # Short-circuit
    assert not layer2.load.called
    assert not layer3.load.called


def test_l1_l2_pass_l3_fail_short_circuit():
    """Full pipeline: L1 pass, L2 fail → L3 not called."""
    layer1_result = create_mock_result(passed=True, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(
        passed=False,
        rejection_reason="Text mismatch",
        critique_method="imagereward"
    )

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)
    layer3 = create_mock_adapter(create_mock_result())

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2, layer3=layer3)
    result = orchestrator.critique(
        b"image_data",
        DEFAULT_CRITIQUE_RUBRIC,
        anchor_image_bytes=b"anchor_data"
    )

    assert result.passed is False
    assert result.critique_method == "graduated_l1_l2"
    assert layer1.critique.called
    assert layer2.critique.called
    assert not layer3.critique.called  # Short-circuit


# =============================================================================
# Dimension Merging Tests
# =============================================================================

def test_dimension_merging_higher_layer_wins():
    """Dimension merging: Higher layer wins for same DimensionType."""
    # L1 readability: 0.80
    # L2 readability: 0.90 (should win)
    l1_dims = [
        create_mock_dimension(DimensionType.ARTIFACTING, 0.85, measurement_method="l1_format"),
        create_mock_dimension(DimensionType.COMPOSITION, 0.80, measurement_method="l1_comp"),
        create_mock_dimension(DimensionType.IDENTITY_MATCH, 1.0, measurement_method="l1_skip"),
        create_mock_dimension(DimensionType.READABILITY, 0.80, measurement_method="l1_blur"),
        create_mock_dimension(DimensionType.STYLE_ADHERENCE, 1.0, measurement_method="l1_skip"),
    ]

    l2_dims = [
        create_mock_dimension(DimensionType.ARTIFACTING, 0.90, measurement_method="l2_artifact"),
        create_mock_dimension(DimensionType.COMPOSITION, 0.85, measurement_method="l2_comp"),
        create_mock_dimension(DimensionType.IDENTITY_MATCH, 1.0, measurement_method="l2_skip"),
        create_mock_dimension(DimensionType.READABILITY, 0.90, measurement_method="l2_read"),
        create_mock_dimension(DimensionType.STYLE_ADHERENCE, 0.75, measurement_method="l2_style"),
    ]

    layer1_result = create_mock_result(passed=True, dimensions=l1_dims, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(passed=True, dimensions=l2_dims, critique_method="imagereward")

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2)
    result = orchestrator.critique(b"image_data", DEFAULT_CRITIQUE_RUBRIC)

    # Check that L2 dimensions win
    readability_dim = [d for d in result.dimensions if d.dimension == DimensionType.READABILITY][0]
    assert readability_dim.score == 0.90
    assert readability_dim.measurement_method == "l2_read"

    style_dim = [d for d in result.dimensions if d.dimension == DimensionType.STYLE_ADHERENCE][0]
    assert style_dim.score == 0.75
    assert style_dim.measurement_method == "l2_style"


def test_dimensions_sorted_in_merged_result():
    """Merged result dimensions are sorted by dimension type."""
    layer1_result = create_mock_result(passed=True, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(passed=True, critique_method="imagereward")

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2)
    result = orchestrator.critique(b"image_data", DEFAULT_CRITIQUE_RUBRIC)

    # Verify dimensions are sorted
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
# Overall Score/Severity Tests
# =============================================================================

def test_overall_score_is_minimum():
    """Overall score is minimum across all layers."""
    layer1_result = create_mock_result(passed=True, overall_score=0.90, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(passed=True, overall_score=0.75, critique_method="imagereward")
    layer3_result = create_mock_result(passed=True, overall_score=0.85, critique_method="siglip")

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)
    layer3 = create_mock_adapter(layer3_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2, layer3=layer3)
    result = orchestrator.critique(
        b"image_data",
        DEFAULT_CRITIQUE_RUBRIC,
        anchor_image_bytes=b"anchor_data"
    )

    assert result.overall_score == 0.75  # Minimum


def test_overall_severity_is_worst():
    """Overall severity is worst across all dimensions."""
    l1_dims = [
        create_mock_dimension(DimensionType.ARTIFACTING, 0.85, SeverityLevel.ACCEPTABLE),
        create_mock_dimension(DimensionType.COMPOSITION, 0.80, SeverityLevel.ACCEPTABLE),
        create_mock_dimension(DimensionType.IDENTITY_MATCH, 1.0, SeverityLevel.ACCEPTABLE),
        create_mock_dimension(DimensionType.READABILITY, 0.60, SeverityLevel.MINOR),  # Minor
        create_mock_dimension(DimensionType.STYLE_ADHERENCE, 1.0, SeverityLevel.ACCEPTABLE),
    ]

    l2_dims = [
        create_mock_dimension(DimensionType.ARTIFACTING, 0.90, SeverityLevel.ACCEPTABLE),
        create_mock_dimension(DimensionType.COMPOSITION, 0.85, SeverityLevel.ACCEPTABLE),
        create_mock_dimension(DimensionType.IDENTITY_MATCH, 1.0, SeverityLevel.ACCEPTABLE),
        create_mock_dimension(DimensionType.READABILITY, 0.90, SeverityLevel.ACCEPTABLE),
        create_mock_dimension(DimensionType.STYLE_ADHERENCE, 0.55, SeverityLevel.MAJOR),  # Major (worst)
    ]

    layer1_result = create_mock_result(passed=True, dimensions=l1_dims, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(passed=True, dimensions=l2_dims, critique_method="imagereward")

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2)
    result = orchestrator.critique(b"image_data", DEFAULT_CRITIQUE_RUBRIC)

    assert result.overall_severity == SeverityLevel.MAJOR  # Worst


# =============================================================================
# VRAM Management Tests
# =============================================================================

def test_vram_management_load_unload_l2():
    """VRAM management: load()/unload() called around L2 critique."""
    layer1_result = create_mock_result(passed=True, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(passed=True, critique_method="imagereward")

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2)
    orchestrator.critique(b"image_data", DEFAULT_CRITIQUE_RUBRIC)

    # Verify load/unload called in correct order
    assert layer2.load.call_count == 1
    assert layer2.unload.call_count == 1
    # Load before critique, unload after
    assert layer2.method_calls[0] == call.load()
    assert layer2.method_calls[1] == call.critique(
        b"image_data",
        DEFAULT_CRITIQUE_RUBRIC,
        prompt=None,
        anchor_image_bytes=None,
        style_reference_bytes=None
    )
    assert layer2.method_calls[2] == call.unload()


def test_vram_management_load_unload_l3():
    """VRAM management: load()/unload() called around L3 critique."""
    layer1_result = create_mock_result(passed=True, critique_method="heuristics_cpu")
    layer2_result = create_mock_result(passed=True, critique_method="imagereward")
    layer3_result = create_mock_result(passed=True, critique_method="siglip")

    layer1 = create_mock_adapter(layer1_result)
    layer2 = create_mock_adapter(layer2_result)
    layer3 = create_mock_adapter(layer3_result)

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2, layer3=layer3)
    orchestrator.critique(
        b"image_data",
        DEFAULT_CRITIQUE_RUBRIC,
        anchor_image_bytes=b"anchor_data"
    )

    # Verify load/unload called
    assert layer3.load.call_count == 1
    assert layer3.unload.call_count == 1


def test_vram_management_unload_on_exception():
    """VRAM management: unload() called even if critique() raises exception."""
    layer1_result = create_mock_result(passed=True, critique_method="heuristics_cpu")

    layer1 = create_mock_adapter(layer1_result)
    layer2 = Mock(spec=ImageCritiqueAdapter)
    layer2.load = Mock()
    layer2.critique = Mock(side_effect=Exception("GPU error"))
    layer2.unload = Mock()

    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1, layer2=layer2)

    with pytest.raises(Exception, match="GPU error"):
        orchestrator.critique(b"image_data", DEFAULT_CRITIQUE_RUBRIC)

    # Verify unload was called despite exception
    assert layer2.load.called
    assert layer2.unload.called


# =============================================================================
# Factory Integration Tests
# =============================================================================

def test_factory_creates_graduated_orchestrator():
    """Factory creates GraduatedCritiqueOrchestrator with 'graduated' backend."""
    orchestrator = create_image_critic(
        "graduated",
        layer1_backend="stub",
        layer2_backend=None,
        layer3_backend=None
    )

    assert isinstance(orchestrator, GraduatedCritiqueOrchestrator)
    assert orchestrator.layer1 is not None
    assert orchestrator.layer2 is None
    assert orchestrator.layer3 is None


def test_factory_graduated_with_all_layers():
    """Factory creates graduated orchestrator with all layers."""
    orchestrator = create_image_critic(
        "graduated",
        layer1_backend="stub",
        layer2_backend="stub",
        layer3_backend="stub"
    )

    assert isinstance(orchestrator, GraduatedCritiqueOrchestrator)
    assert orchestrator.layer1 is not None
    assert orchestrator.layer2 is not None
    assert orchestrator.layer3 is not None


def test_factory_graduated_default_layer1_heuristics():
    """Factory uses 'heuristics' as default layer1_backend."""
    orchestrator = create_image_critic("graduated")

    assert isinstance(orchestrator, GraduatedCritiqueOrchestrator)
    # Layer1 should be heuristics (can't check type without importing, but it's not None)
    assert orchestrator.layer1 is not None


# =============================================================================
# Protocol Compliance Tests
# =============================================================================

def test_orchestrator_implements_protocol():
    """GraduatedCritiqueOrchestrator implements ImageCritiqueAdapter protocol."""
    layer1 = create_mock_adapter(create_mock_result())
    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1)
    assert isinstance(orchestrator, ImageCritiqueAdapter)


def test_orchestrator_has_load_unload():
    """GraduatedCritiqueOrchestrator has load/unload methods (no-ops)."""
    layer1 = create_mock_adapter(create_mock_result())
    orchestrator = GraduatedCritiqueOrchestrator(layer1=layer1)
    orchestrator.load()  # Should not raise
    orchestrator.unload()  # Should not raise
