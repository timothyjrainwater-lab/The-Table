"""Image critique contracts for AIDM immersion pipeline.

PRE-M3 CONTRACT (NON-OPERATIONAL)
---------------------------------
This module defines data contracts for automated image quality validation.
Implementation deferred to M3 (Immersion Layer integration).

CURRENT STATUS: Schema-only, no runtime implementation
R0 SOURCE: R0_IMAGE_CRITIQUE_RUBRIC.md, R0_IMAGE_CRITIQUE_FEASIBILITY.md (advisory)
AUTHORITY: NON-BINDING until formal R0 approval + M3 integration

Design informed by R0 research findings (heuristics + CLIP hybrid approach),
but no actual critique logic, models, or generation integration exists yet.

---

This module provides:
- CritiqueResult: Outcome of image quality validation
- CritiqueRubric: Quality dimensions and thresholds
- RegenerationAttempt: Record of regeneration with parameter adjustments
- CritiqueDimension: Individual quality check (readability, composition, etc.)
- SeverityLevel: Critique failure severity (CRITICAL, MAJOR, MINOR, ACCEPTABLE)

All schemas are deterministic (sorted keys, frozen where applicable).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class SeverityLevel(str, Enum):
    """Critique failure severity levels.

    Based on R0_IMAGE_CRITIQUE_RUBRIC.md § Critique Severity Levels.

    CRITICAL: Automatic reject, no user override
    MAJOR: Reject with high confidence
    MINOR: Reject with low confidence
    ACCEPTABLE: Pass
    """
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    ACCEPTABLE = "acceptable"


class DimensionType(str, Enum):
    """Quality dimensions for image critique.

    Based on R0_IMAGE_CRITIQUE_RUBRIC.md § Quality Dimensions.

    READABILITY: Can details be distinguished at UI size?
    COMPOSITION: Is subject properly framed/centered?
    ARTIFACTING: Obvious AI artifacts (hands, eyes, anatomy)?
    STYLE_ADHERENCE: Matches campaign art style?
    IDENTITY_MATCH: Maintains visual consistency with NPC anchor?
    """
    READABILITY = "readability"
    COMPOSITION = "composition"
    ARTIFACTING = "artifacting"
    STYLE_ADHERENCE = "style_adherence"
    IDENTITY_MATCH = "identity_match"


@dataclass(frozen=True)
class CritiqueDimension:
    """Individual quality check result.

    Represents outcome of checking one quality dimension (e.g., readability).

    Attributes:
        dimension: Which quality dimension was checked
        severity: Severity level of finding (CRITICAL/MAJOR/MINOR/ACCEPTABLE)
        score: Numeric score (0.0-1.0, higher = better quality)
        reason: Human-readable explanation of finding
        measurement_method: How dimension was measured (e.g., "laplacian_variance", "clip_similarity")
    """
    dimension: DimensionType
    severity: SeverityLevel
    score: float
    reason: str
    measurement_method: str

    def __post_init__(self):
        """Validate score range."""
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"CritiqueDimension score must be in [0.0, 1.0], got {self.score}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON storage.

        Returns:
            Dict with sorted keys for deterministic serialization
        """
        return {
            "dimension": self.dimension.value,
            "measurement_method": self.measurement_method,
            "reason": self.reason,
            "score": self.score,
            "severity": self.severity.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CritiqueDimension':
        """Deserialize from dict.

        Args:
            data: Dict with dimension, severity, score, reason, measurement_method

        Returns:
            CritiqueDimension instance
        """
        return cls(
            dimension=DimensionType(data["dimension"]),
            severity=SeverityLevel(data["severity"]),
            score=data["score"],
            reason=data["reason"],
            measurement_method=data["measurement_method"]
        )


@dataclass(frozen=True)
class CritiqueResult:
    """Result of automated image quality validation.

    Represents outcome of running critique on a single generated image.

    Attributes:
        passed: Whether image passed all quality checks
        overall_severity: Worst severity level across all dimensions
        dimensions: List of individual dimension checks (sorted by dimension name)
        overall_score: Aggregate quality score (0.0-1.0, F1 or weighted average)
        rejection_reason: Human-readable rejection reason (if failed)
        critique_method: Which critique approach was used (e.g., "heuristics_only", "heuristics_clip_hybrid")
    """
    passed: bool
    overall_severity: SeverityLevel
    dimensions: List[CritiqueDimension]
    overall_score: float
    rejection_reason: Optional[str]
    critique_method: str

    def __post_init__(self):
        """Validate overall score range and dimension ordering."""
        if not (0.0 <= self.overall_score <= 1.0):
            raise ValueError(f"CritiqueResult overall_score must be in [0.0, 1.0], got {self.overall_score}")

        # Ensure dimensions are sorted by dimension type for deterministic serialization
        expected_order = sorted(self.dimensions, key=lambda d: d.dimension.value)
        if [d.dimension for d in self.dimensions] != [d.dimension for d in expected_order]:
            raise ValueError("CritiqueResult dimensions must be sorted by dimension type")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON storage.

        Returns:
            Dict with sorted keys for deterministic serialization
        """
        return {
            "critique_method": self.critique_method,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "overall_score": self.overall_score,
            "overall_severity": self.overall_severity.value,
            "passed": self.passed,
            "rejection_reason": self.rejection_reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CritiqueResult':
        """Deserialize from dict.

        Args:
            data: Dict with passed, overall_severity, dimensions, etc.

        Returns:
            CritiqueResult instance
        """
        return cls(
            passed=data["passed"],
            overall_severity=SeverityLevel(data["overall_severity"]),
            dimensions=[CritiqueDimension.from_dict(d) for d in data["dimensions"]],
            overall_score=data["overall_score"],
            rejection_reason=data.get("rejection_reason"),
            critique_method=data["critique_method"]
        )


@dataclass
class RegenerationAttempt:
    """Record of a single regeneration attempt with parameter adjustments.

    Tracks how generation parameters were adjusted for each retry attempt.
    Based on R0_BOUNDED_REGEN_POLICY.md § Backoff Strategy.

    Attributes:
        attempt_number: Which attempt (1 = original, 2-4 = retries)
        cfg_scale: Classifier-Free Guidance scale (7.5 default, 9.0-13.0 for retries)
        sampling_steps: Number of denoising steps (50 default, 60-80 for retries)
        creativity: Variation parameter (0.8 default, 0.3-0.7 for retries)
        negative_prompt: Additional negative prompt (added in retries)
        critique_result: Critique result for this attempt (None if not yet generated)
        generation_time_ms: Time taken to generate image (milliseconds)
    """
    attempt_number: int
    cfg_scale: float
    sampling_steps: int
    creativity: float
    negative_prompt: str = ""
    critique_result: Optional[CritiqueResult] = None
    generation_time_ms: Optional[int] = None

    def __post_init__(self):
        """Validate attempt number and parameter ranges."""
        if self.attempt_number < 1:
            raise ValueError(f"RegenerationAttempt attempt_number must be >= 1, got {self.attempt_number}")
        if not (1.0 <= self.cfg_scale <= 20.0):
            raise ValueError(f"RegenerationAttempt cfg_scale must be in [1.0, 20.0], got {self.cfg_scale}")
        if not (10 <= self.sampling_steps <= 150):
            raise ValueError(f"RegenerationAttempt sampling_steps must be in [10, 150], got {self.sampling_steps}")
        if not (0.0 <= self.creativity <= 1.0):
            raise ValueError(f"RegenerationAttempt creativity must be in [0.0, 1.0], got {self.creativity}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for JSON storage.

        Returns:
            Dict with sorted keys for deterministic serialization
        """
        return {
            "attempt_number": self.attempt_number,
            "cfg_scale": self.cfg_scale,
            "creativity": self.creativity,
            "critique_result": self.critique_result.to_dict() if self.critique_result else None,
            "generation_time_ms": self.generation_time_ms,
            "negative_prompt": self.negative_prompt,
            "sampling_steps": self.sampling_steps,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RegenerationAttempt':
        """Deserialize from dict.

        Args:
            data: Dict with attempt_number, cfg_scale, etc.

        Returns:
            RegenerationAttempt instance
        """
        return cls(
            attempt_number=data["attempt_number"],
            cfg_scale=data["cfg_scale"],
            sampling_steps=data["sampling_steps"],
            creativity=data["creativity"],
            negative_prompt=data.get("negative_prompt", ""),
            critique_result=CritiqueResult.from_dict(data["critique_result"]) if data.get("critique_result") else None,
            generation_time_ms=data.get("generation_time_ms")
        )


@dataclass
class CritiqueRubric:
    """Quality thresholds for image critique.

    Defines pass/fail thresholds for each quality dimension.
    Based on R0_IMAGE_CRITIQUE_RUBRIC.md § Quality Dimensions.

    PRE-M3 NOTE: Thresholds are placeholders. Actual calibration deferred to M3.

    Attributes:
        readability_threshold: Min score for readability (0.0-1.0)
        composition_threshold: Min score for composition (0.0-1.0)
        artifacting_threshold: Min score for artifacting (0.0-1.0)
        style_threshold: Min score for style adherence (0.0-1.0)
        identity_threshold: Min score for identity match (0.0-1.0)
        overall_threshold: Min aggregate score for pass (F1 ≥ 0.70 recommended)
    """
    readability_threshold: float = 0.70
    composition_threshold: float = 0.70
    artifacting_threshold: float = 0.70
    style_threshold: float = 0.70
    identity_threshold: float = 0.60  # Lower for NPC continuity (harder task)
    overall_threshold: float = 0.70

    def __post_init__(self):
        """Validate all thresholds in [0.0, 1.0]."""
        for field_name in ["readability_threshold", "composition_threshold", "artifacting_threshold",
                           "style_threshold", "identity_threshold", "overall_threshold"]:
            value = getattr(self, field_name)
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"CritiqueRubric {field_name} must be in [0.0, 1.0], got {value}")

    def to_dict(self) -> Dict[str, float]:
        """Serialize to dict for JSON storage.

        Returns:
            Dict with sorted keys for deterministic serialization
        """
        return {
            "artifacting_threshold": self.artifacting_threshold,
            "composition_threshold": self.composition_threshold,
            "identity_threshold": self.identity_threshold,
            "overall_threshold": self.overall_threshold,
            "readability_threshold": self.readability_threshold,
            "style_threshold": self.style_threshold,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'CritiqueRubric':
        """Deserialize from dict.

        Args:
            data: Dict with threshold fields

        Returns:
            CritiqueRubric instance
        """
        return cls(
            readability_threshold=data["readability_threshold"],
            composition_threshold=data["composition_threshold"],
            artifacting_threshold=data["artifacting_threshold"],
            style_threshold=data["style_threshold"],
            identity_threshold=data["identity_threshold"],
            overall_threshold=data["overall_threshold"]
        )


# Default rubric (based on R0 feasibility analysis)
DEFAULT_CRITIQUE_RUBRIC = CritiqueRubric(
    readability_threshold=0.70,
    composition_threshold=0.70,
    artifacting_threshold=0.70,
    style_threshold=0.70,
    identity_threshold=0.60,
    overall_threshold=0.70
)
