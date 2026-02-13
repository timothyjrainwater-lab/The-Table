"""Environmental hazard schemas for deterministic hazard tracking.

Defines hazard types, intervals, effects, and progression.
NO RESOLUTION LOGIC - schema only.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Literal, Optional
from enum import Enum


class HazardIntervalUnit(Enum):
    """Time interval unit for hazard effects."""
    ROUND = "round"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


# Type alias for HazardIntervalUnit literal values
HazardIntervalUnitLiteral = Literal["round", "minute", "hour", "day"]


class HazardEffectType(Enum):
    """Type of effect produced by environmental hazard."""
    DAMAGE = "damage"
    CONDITION = "condition"
    VISIBILITY = "visibility"
    MIXED = "mixed"


# Type alias for HazardEffectType literal values
HazardEffectTypeLiteral = Literal["damage", "condition", "visibility", "mixed"]


@dataclass
class EnvironmentalHazard:
    """
    Environmental hazard definition.

    Represents deterministic, time-indexed hazards (fire, cold, smoke, etc.).
    """

    id: str
    """Unique identifier for this hazard."""

    name: str
    """Human-readable name (e.g., 'Forest Fire', 'Extreme Cold')."""

    interval_unit: HazardIntervalUnitLiteral
    """Time unit for hazard effects (round, minute, hour, day)."""

    interval_value: int
    """Interval frequency (e.g., every 1 round, every 10 minutes)."""

    effect_type: HazardEffectTypeLiteral
    """Type of effect (damage, condition, visibility, mixed)."""

    description: str
    """Short, factual description of hazard effects."""

    escalates: bool = False
    """Whether hazard escalates over time (e.g., suffocation stages)."""

    max_stages: Optional[int] = None
    """Maximum escalation stages if escalates=True."""

    visibility_tags: List[str] = field(default_factory=list)
    """Visibility occlusion tags (e.g., ['heavy_obscurement'])."""

    terrain_tags: List[str] = field(default_factory=list)
    """Terrain property tags (e.g., ['difficult_terrain'])."""

    citation: Optional[Dict[str, Any]] = None
    """Optional citation for hazard rules."""

    def __post_init__(self):
        """Validate hazard fields."""
        if not self.id:
            raise ValueError("Hazard id cannot be empty")

        if not self.name:
            raise ValueError("Hazard name cannot be empty")

        valid_units = ["round", "minute", "hour", "day"]
        if self.interval_unit not in valid_units:
            raise ValueError(f"interval_unit must be one of {valid_units}, got {self.interval_unit}")

        if self.interval_value < 1:
            raise ValueError(f"interval_value must be >= 1, got {self.interval_value}")

        valid_effects = ["damage", "condition", "visibility", "mixed"]
        if self.effect_type not in valid_effects:
            raise ValueError(f"effect_type must be one of {valid_effects}, got {self.effect_type}")

        if self.escalates and self.max_stages is not None:
            if self.max_stages < 1:
                raise ValueError(f"max_stages must be >= 1 if set, got {self.max_stages}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "id": self.id,
            "name": self.name,
            "interval_unit": self.interval_unit,
            "interval_value": self.interval_value,
            "effect_type": self.effect_type,
            "description": self.description,
            "escalates": self.escalates
        }

        if self.max_stages is not None:
            result["max_stages"] = self.max_stages

        if self.visibility_tags:
            result["visibility_tags"] = self.visibility_tags

        if self.terrain_tags:
            result["terrain_tags"] = self.terrain_tags

        if self.citation is not None:
            result["citation"] = self.citation

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvironmentalHazard":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            interval_unit=data["interval_unit"],
            interval_value=data["interval_value"],
            effect_type=data["effect_type"],
            description=data["description"],
            escalates=data.get("escalates", False),
            max_stages=data.get("max_stages"),
            visibility_tags=data.get("visibility_tags", []),
            terrain_tags=data.get("terrain_tags", []),
            citation=data.get("citation")
        )


@dataclass
class HazardStage:
    """
    Single stage in hazard progression.

    Used for escalating hazards like suffocation, starvation, etc.
    """

    stage_index: int
    """Zero-indexed stage number."""

    notes: str
    """Stage description (e.g., 'nonlethal damage', 'lethal damage begins')."""

    citation: Optional[Dict[str, Any]] = None
    """Optional citation for this stage's rules."""

    def __post_init__(self):
        """Validate stage fields."""
        if self.stage_index < 0:
            raise ValueError(f"stage_index must be >= 0, got {self.stage_index}")

        if not self.notes:
            raise ValueError("Stage notes cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "stage_index": self.stage_index,
            "notes": self.notes
        }

        if self.citation is not None:
            result["citation"] = self.citation

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HazardStage":
        """Create from dictionary."""
        return cls(
            stage_index=data["stage_index"],
            notes=data["notes"],
            citation=data.get("citation")
        )


@dataclass
class HazardProgression:
    """
    Progression sequence for escalating hazards.

    Defines ordered stages with increasing severity.
    """

    hazard_id: str
    """ID of associated EnvironmentalHazard."""

    stages: List[HazardStage] = field(default_factory=list)
    """Ordered list of hazard stages."""

    def __post_init__(self):
        """Validate progression fields."""
        if not self.hazard_id:
            raise ValueError("hazard_id cannot be empty")

        if not self.stages:
            raise ValueError("stages cannot be empty")

        # Validate stage_index is strictly increasing
        for i in range(1, len(self.stages)):
            prev_index = self.stages[i - 1].stage_index
            curr_index = self.stages[i].stage_index

            if curr_index <= prev_index:
                raise ValueError(
                    f"Stage indices must be strictly increasing: "
                    f"stage {i-1} has index {prev_index}, stage {i} has index {curr_index}"
                )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "hazard_id": self.hazard_id,
            "stages": [stage.to_dict() for stage in self.stages]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HazardProgression":
        """Create from dictionary."""
        return cls(
            hazard_id=data["hazard_id"],
            stages=[HazardStage.from_dict(s) for s in data.get("stages", [])]
        )
