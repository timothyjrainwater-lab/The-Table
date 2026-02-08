"""Visibility and line-of-sight/effect schemas.

Defines contracts for visibility, targeting, fog-of-war inputs, and lighting over time.
NO ALGORITHMS - schema only for now.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal, Any, Tuple
from enum import Enum

# Re-export canonical VisibilityBlockReason from targeting.py (FIX-02: single source of truth)
from aidm.schemas.targeting import VisibilityBlockReason  # noqa: F401


# Light levels
LightLevel = Literal["bright", "dim", "dark"]


# Vision modes
VisionMode = Literal[
    "normal",
    "low_light",
    "darkvision",
    "blindsense",
    "blindsight"
]


# Occlusion tags for terrain/objects
OcclusionTag = Literal[
    "opaque",
    "heavy_obscurement",
    "light_obscurement"
]


@dataclass
class VisibilityProfile:
    """Creature's vision capabilities."""

    vision_modes: List[VisionMode] = field(default_factory=lambda: ["normal"])
    """Vision modes available to this creature"""

    ranges: Dict[VisionMode, int] = field(default_factory=dict)
    """Vision range in feet for each mode (darkvision: 60, low_light: 120, etc.)"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "vision_modes": list(self.vision_modes),
            "ranges": {mode: distance for mode, distance in self.ranges.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisibilityProfile":
        """Create from dictionary."""
        return cls(
            vision_modes=data.get("vision_modes", ["normal"]),
            ranges=data.get("ranges", {})
        )


@dataclass
class TileVisibility:
    """Visibility properties of a map tile (optional for future use)."""

    light_level: LightLevel = "bright"
    """Current light level of this tile"""

    occlusion_tags: List[OcclusionTag] = field(default_factory=list)
    """Occlusion effects on this tile"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "light_level": self.light_level,
            "occlusion_tags": list(self.occlusion_tags)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TileVisibility":
        """Create from dictionary."""
        return cls(
            light_level=data.get("light_level", "bright"),
            occlusion_tags=data.get("occlusion_tags", [])
        )


@dataclass
class AmbientLightSchedule:
    """
    Scheduled changes to ambient light level over time.

    Used for day/night cycles, dimming torches, etc.
    """

    entries: List[Tuple[int, LightLevel]] = field(default_factory=list)
    """List of (start_t_seconds, light_level) tuples, must be strictly increasing times."""

    def __post_init__(self):
        """Validate schedule entries are strictly increasing."""
        if len(self.entries) < 2:
            return  # Empty or single entry is trivially valid

        for i in range(1, len(self.entries)):
            prev_time = self.entries[i - 1][0]
            curr_time = self.entries[i][0]

            if curr_time <= prev_time:
                raise ValueError(
                    f"Schedule entries must be strictly increasing: "
                    f"entry {i-1} has time {prev_time}, entry {i} has time {curr_time}"
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "entries": [{"t_seconds": t, "light_level": level} for t, level in self.entries]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AmbientLightSchedule":
        """Create from dictionary."""
        entries = []
        for entry in data.get("entries", []):
            entries.append((entry["t_seconds"], entry["light_level"]))

        return cls(entries=entries)


@dataclass
class LightSource:
    """
    Point light source with radius and optional expiration.

    Used for torches, light spells, etc.
    """

    position: Dict[str, int]
    """Position as {"x": int, "y": int} (GridPoint serialized)."""

    radius: int
    """Light radius in feet."""

    light_level: LightLevel
    """Light level provided by this source."""

    expires_at_t_seconds: Optional[int] = None
    """Optional expiration time (for spells, burning torches)."""

    def __post_init__(self):
        """Validate light source fields."""
        if "x" not in self.position or "y" not in self.position:
            raise ValueError("position must have 'x' and 'y' keys")

        if self.radius < 0:
            raise ValueError(f"radius must be >= 0, got {self.radius}")

        if self.expires_at_t_seconds is not None and self.expires_at_t_seconds < 0:
            raise ValueError(f"expires_at_t_seconds must be >= 0, got {self.expires_at_t_seconds}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "position": self.position,
            "radius": self.radius,
            "light_level": self.light_level
        }

        if self.expires_at_t_seconds is not None:
            result["expires_at_t_seconds"] = self.expires_at_t_seconds

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LightSource":
        """Create from dictionary."""
        return cls(
            position=data["position"],
            radius=data["radius"],
            light_level=data["light_level"],
            expires_at_t_seconds=data.get("expires_at_t_seconds")
        )

