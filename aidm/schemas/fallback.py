"""Failure fallback schemas for AIDM image generation.

M3 IMPLEMENTATION: Fallback System
-----------------------------------
This module defines schemas for graceful degradation when image generation fails.
Supports four-tier fallback hierarchy: shipped art → generic → solid color → text-only.

Based on approved design: docs/design/IMAGE_GENERATION_FAILURE_FALLBACK.md

Schema Definitions:
- FallbackTier: Enum for fallback quality levels
- FallbackResult: Result of fallback resolution
- FallbackReason: Enum for failure triggers

NO MODIFICATION to existing prep_pipeline or image_critique schemas.
All extensions are additive only.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class FallbackTier(Enum):
    """Four-tier fallback hierarchy for failed image generation.

    Ordered by quality/immersion level (best to worst).
    """
    SHIPPED_ART = "shipped_art_pack"  # Tier 1: Manually vetted archetype-specific art
    GENERIC = "generic_category_placeholder"  # Tier 2: Generic category placeholder
    SOLID_COLOR = "solid_color_text"  # Tier 3: Solid color with text overlay
    TEXT_ONLY = "text_only"  # Tier 4: No image (text description only)


class FallbackReason(Enum):
    """Failure trigger conditions that escalate to fallback.

    Based on design spec Section 2 (Failure Trigger Conditions).
    """
    MAX_ATTEMPTS_EXHAUSTED = "max_attempts_exhausted"  # All retry attempts failed critique
    TIMEOUT = "timeout"  # Time budget exceeded before max attempts reached
    USER_ABORTED = "user_aborted"  # User manually canceled generation
    HARDWARE_FAILURE = "hardware_failure"  # GPU OOM, model loading failure, disk full
    BAD_PROMPT = "bad_prompt"  # Prompt flagged as problematic (all scores <0.30)
    TIER_DEFAULT = "tier_default"  # Tier 5 CPU-only, skipped generation by default


@dataclass
class FallbackResult:
    """Result of fallback resolution.

    Returned by FailureFallbackResolver.resolve_fallback().

    Attributes:
        tier: Which fallback tier was selected
        image_bytes: Image file bytes (None for TEXT_ONLY)
        description: Human-readable description of fallback asset
        file_path: Path to fallback file (empty for TEXT_ONLY or generated solid color)
        metadata: Additional metadata (archetype match, color scheme, etc.)
    """
    tier: FallbackTier
    image_bytes: Optional[bytes]
    description: str
    file_path: str
    metadata: dict

    def __post_init__(self):
        """Validate FallbackResult constraints."""
        # TEXT_ONLY must have no image_bytes
        if self.tier == FallbackTier.TEXT_ONLY and self.image_bytes is not None:
            raise ValueError("TEXT_ONLY tier must have image_bytes=None")

        # Other tiers must have image_bytes
        if self.tier != FallbackTier.TEXT_ONLY and self.image_bytes is None:
            raise ValueError(f"{self.tier.name} tier must have non-None image_bytes")

        # Metadata must be a dict
        if not isinstance(self.metadata, dict):
            raise ValueError("metadata must be a dict")
