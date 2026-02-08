"""Exposure and environmental condition schemas.

Defines exposure types and environmental conditions.
NO MITIGATION LOGIC - descriptive only.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Literal, Optional
from enum import Enum


class ExposureType(Enum):
    """Type of environmental exposure."""
    HEAT = "heat"
    COLD = "cold"
    SMOKE = "smoke"
    TOXIC_FUMES = "toxic_fumes"
    SUFFOCATION = "suffocation"
    DROWNING = "drowning"


# Type alias for ExposureType literal values
ExposureTypeLiteral = Literal["heat", "cold", "smoke", "toxic_fumes", "suffocation", "drowning"]


@dataclass
class EnvironmentalCondition:
    """
    Environmental condition affecting characters.

    References an EnvironmentalHazard and describes mitigation sources.
    """

    type: ExposureTypeLiteral
    """Type of exposure."""

    hazard_ref: str
    """Reference to EnvironmentalHazard.id."""

    mitigation_sources: List[str] = field(default_factory=list)
    """Descriptive list of mitigation sources (gear, shelter, spells)."""

    notes: str = ""
    """Additional notes about this condition."""

    citation: Optional[Dict[str, Any]] = None
    """Optional citation for condition rules."""

    def __post_init__(self):
        """Validate condition fields."""
        valid_types = ["heat", "cold", "smoke", "toxic_fumes", "suffocation", "drowning"]
        if self.type not in valid_types:
            raise ValueError(f"type must be one of {valid_types}, got {self.type}")

        if not self.hazard_ref:
            raise ValueError("hazard_ref cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "type": self.type,
            "hazard_ref": self.hazard_ref,
            "mitigation_sources": self.mitigation_sources,
            "notes": self.notes
        }

        if self.citation is not None:
            result["citation"] = self.citation

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnvironmentalCondition":
        """Create from dictionary."""
        return cls(
            type=data["type"],
            hazard_ref=data["hazard_ref"],
            mitigation_sources=data.get("mitigation_sources", []),
            notes=data.get("notes", ""),
            citation=data.get("citation")
        )
