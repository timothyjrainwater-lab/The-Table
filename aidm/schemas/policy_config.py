"""Policy variety configuration schemas.

Defines top-k + temperature config for policy engine variety.
NO POLICY ENGINE IMPLEMENTATION - schema only.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class PolicyVarietyConfig:
    """
    Configuration for policy variety (top-k sampling with temperature).

    Used by policy engine to introduce controlled randomness in action selection
    while maintaining determinism via policy RNG stream.
    """

    top_k: int = 1
    """Number of top actions to consider (>= 1). Default 1 = greedy."""

    temperature: float = 1.0
    """Temperature for score scaling (> 0). Default 1.0 = unscaled."""

    score_band: Optional[float] = None
    """Optional: only consider actions within this score range of top action"""

    def __post_init__(self):
        """Validate configuration values."""
        if self.top_k < 1:
            raise ValueError(f"top_k must be >= 1, got {self.top_k}")
        if self.temperature <= 0:
            raise ValueError(f"temperature must be > 0, got {self.temperature}")
        if self.score_band is not None and self.score_band < 0:
            raise ValueError(f"score_band must be >= 0, got {self.score_band}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "top_k": self.top_k,
            "temperature": self.temperature
        }

        if self.score_band is not None:
            result["score_band"] = self.score_band

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyVarietyConfig":
        """Create from dictionary."""
        return cls(
            top_k=data.get("top_k", 1),
            temperature=data.get("temperature", 1.0),
            score_band=data.get("score_band")
        )
