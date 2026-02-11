"""Graduated critique orchestrator for multi-layer image validation.

M3 IMPLEMENTATION: GraduatedCritiqueOrchestrator
-----------------------------------------------
Sequential pipeline wiring that runs Layer 1 → Layer 2 → Layer 3,
short-circuiting on failure, and producing a merged CritiqueResult.

This is the central orchestration component that ties the three
individual critique adapters into a single graduated pipeline.

Based on approved design: SONNET-C_WO-M3-IMAGE-CRITIQUE-02_prep_integration.md

Architecture:
    - Layer 1 (Heuristics): CPU-only, fast rejection (<100ms)
    - Layer 2 (ImageReward): GPU, text-image alignment (~1.5s) [OPTIONAL]
    - Layer 3 (SigLIP): GPU, identity consistency (~0.5s) [OPTIONAL]
    - Short-circuit: If any layer fails, subsequent layers don't run
    - VRAM management: load()/unload() around L2/L3 critique calls
    - Dimension merging: Higher layer wins for same DimensionType
"""

from typing import Optional, List, Dict
from aidm.core.image_critique_adapter import ImageCritiqueAdapter
from aidm.schemas.image_critique import (
    CritiqueResult,
    CritiqueRubric,
    CritiqueDimension,
    DimensionType,
    SeverityLevel,
)


class GraduatedCritiqueOrchestrator:
    """Orchestrates graduated critique pipeline across multiple layers.

    Runs critique layers sequentially with short-circuit on failure.
    Manages VRAM by calling load()/unload() around GPU layers.
    Merges dimensions from all layers that ran (higher layer wins).

    Attributes:
        layer1: Layer 1 adapter (heuristics, CPU-only, required)
        layer2: Layer 2 adapter (imagereward, GPU, optional)
        layer3: Layer 3 adapter (siglip, GPU, optional)
    """

    def __init__(
        self,
        layer1: ImageCritiqueAdapter,
        layer2: Optional[ImageCritiqueAdapter] = None,
        layer3: Optional[ImageCritiqueAdapter] = None
    ):
        """Initialize graduated critique orchestrator.

        Args:
            layer1: Layer 1 adapter (heuristics, CPU, required)
            layer2: Layer 2 adapter (imagereward, GPU, optional)
            layer3: Layer 3 adapter (siglip, GPU, optional)

        Raises:
            ValueError: If layer1 is None
        """
        if layer1 is None:
            raise ValueError("layer1 (heuristics) is required")

        self.layer1 = layer1
        self.layer2 = layer2
        self.layer3 = layer3

    def critique(
        self,
        image_bytes: bytes,
        rubric: CritiqueRubric,
        prompt: Optional[str] = None,
        anchor_image_bytes: Optional[bytes] = None,
        style_reference_bytes: Optional[bytes] = None
    ) -> CritiqueResult:
        """Run graduated critique pipeline.

        Executes layers sequentially with short-circuit on failure:
        1. Layer 1 (heuristics, CPU) - always runs
        2. Layer 2 (imagereward, GPU) - if layer2 is not None and L1 passed
        3. Layer 3 (siglip, GPU) - if layer3 is not None and L1+L2 passed and anchor exists

        Args:
            image_bytes: Generated image (PNG/JPEG bytes)
            rubric: Quality thresholds
            prompt: Generation prompt for Layer 2 text-image alignment (optional)
            anchor_image_bytes: Reference image for Layer 3 identity check (optional)
            style_reference_bytes: Style reference (not used by current layers)

        Returns:
            CritiqueResult with merged dimensions from all layers that ran
        """
        layers_run = []
        layer_results = []

        # LAYER 1: Heuristics (CPU-only, always runs)
        layer1_result = self.layer1.critique(
            image_bytes,
            rubric,
            anchor_image_bytes=anchor_image_bytes,
            style_reference_bytes=style_reference_bytes
        )
        layers_run.append("l1")
        layer_results.append(layer1_result)

        # Short-circuit if Layer 1 failed
        if not layer1_result.passed:
            return self._merge_results(layer_results, layers_run)

        # LAYER 2: ImageReward (GPU, optional)
        if self.layer2 is not None:
            # Load model, run critique, unload model (VRAM management)
            self.layer2.load()
            try:
                layer2_result = self.layer2.critique(
                    image_bytes,
                    rubric,
                    prompt=prompt,
                    anchor_image_bytes=anchor_image_bytes,
                    style_reference_bytes=style_reference_bytes
                )
                layers_run.append("l2")
                layer_results.append(layer2_result)
            finally:
                self.layer2.unload()

            # Short-circuit if Layer 2 failed
            if not layer2_result.passed:
                return self._merge_results(layer_results, layers_run)

        # LAYER 3: SigLIP (GPU, optional, requires anchor)
        if self.layer3 is not None and anchor_image_bytes is not None:
            # Load model, run critique, unload model (VRAM management)
            self.layer3.load()
            try:
                layer3_result = self.layer3.critique(
                    image_bytes,
                    rubric,
                    prompt=prompt,
                    anchor_image_bytes=anchor_image_bytes,
                    style_reference_bytes=style_reference_bytes
                )
                layers_run.append("l3")
                layer_results.append(layer3_result)
            finally:
                self.layer3.unload()

        # All layers that ran have passed (or we short-circuited earlier)
        return self._merge_results(layer_results, layers_run)

    def _merge_results(
        self,
        layer_results: List[CritiqueResult],
        layers_run: List[str]
    ) -> CritiqueResult:
        """Merge critique results from multiple layers.

        Merging strategy:
        - Dimensions: For each DimensionType, use result from highest layer
          (L3 > L2 > L1) since higher layers are more specialized
        - Overall passed: All layers that ran must have passed
        - Overall score: Minimum score across all layers
        - Overall severity: Worst severity across all dimensions
        - Critique method: "graduated_l1", "graduated_l1_l2", or "graduated_l1_l2_l3"

        Args:
            layer_results: List of CritiqueResult from layers that ran
            layers_run: List of layer names that ran (e.g., ["l1", "l2"])

        Returns:
            Merged CritiqueResult
        """
        if not layer_results:
            raise ValueError("No layer results to merge")

        # Determine critique method based on layers that ran
        critique_method = f"graduated_{'_'.join(layers_run)}"

        # Build dimension map: DimensionType -> CritiqueDimension
        # Higher layer wins (iterate in reverse order so last write wins)
        dimension_map: Dict[DimensionType, CritiqueDimension] = {}
        for result in layer_results:
            for dim in result.dimensions:
                dimension_map[dim.dimension] = dim

        # Sort dimensions by dimension type (required by CritiqueResult schema)
        merged_dimensions = sorted(dimension_map.values(), key=lambda d: d.dimension.value)

        # Overall passed: All layers must have passed
        overall_passed = all(result.passed for result in layer_results)

        # Overall score: Minimum score across all layers
        overall_score = min(result.overall_score for result in layer_results)

        # Overall severity: Worst severity across all dimensions
        severity_order = {
            SeverityLevel.ACCEPTABLE: 0,
            SeverityLevel.MINOR: 1,
            SeverityLevel.MAJOR: 2,
            SeverityLevel.CRITICAL: 3
        }
        overall_severity = max(
            (dim.severity for dim in merged_dimensions),
            key=lambda s: severity_order[s]
        )

        # Rejection reason: Use the first layer that failed (if any)
        rejection_reason = None
        if not overall_passed:
            for result in layer_results:
                if not result.passed:
                    rejection_reason = result.rejection_reason
                    break

        return CritiqueResult(
            passed=overall_passed,
            overall_severity=overall_severity,
            dimensions=merged_dimensions,
            overall_score=overall_score,
            rejection_reason=rejection_reason,
            critique_method=critique_method
        )

    def load(self):
        """Load resources for all layers (no-op for orchestrator).

        Required by ImageCritiqueAdapter protocol.
        Individual layers are loaded/unloaded during critique().
        """
        pass

    def unload(self):
        """Unload resources for all layers (no-op for orchestrator).

        Required by ImageCritiqueAdapter protocol.
        Individual layers are loaded/unloaded during critique().
        """
        pass
