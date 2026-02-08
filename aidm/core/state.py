"""World state representation with deterministic hashing."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import hashlib
import json


@dataclass
class WorldState:
    """Minimal world state for deterministic simulation."""

    ruleset_version: str
    entities: Dict[str, Any] = field(default_factory=dict)
    active_combat: Optional[Dict[str, Any]] = None

    def state_hash(self) -> str:
        """
        Compute deterministic hash of world state.

        Uses stable key ordering to ensure identical states produce identical hashes.
        """
        # Convert to JSON with sorted keys for deterministic serialization
        state_dict = {
            "ruleset_version": self.ruleset_version,
            "entities": self.entities,
            "active_combat": self.active_combat,
        }

        # Serialize with sorted keys
        serialized = json.dumps(state_dict, sort_keys=True, separators=(",", ":"))

        # Hash the serialized representation
        hash_bytes = hashlib.sha256(serialized.encode("utf-8")).digest()

        # Return hex digest
        return hash_bytes.hex()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ruleset_version": self.ruleset_version,
            "entities": self.entities,
            "active_combat": self.active_combat,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldState":
        """Create WorldState from dictionary."""
        return cls(
            ruleset_version=data["ruleset_version"],
            entities=data.get("entities", {}),
            active_combat=data.get("active_combat"),
        )
