"""Voice intent contract schemas for player actions.

Defines structured, JSON-serializable intents accepted from voice layer (ASR/NLU).
"""

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any, Literal


class IntentParseError(Exception):
    """Raised when an intent has invalid structure or values."""
    pass


@dataclass
class GridPoint:
    """2D grid coordinate."""

    x: int
    y: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridPoint":
        """Create from dictionary."""
        return cls(x=data["x"], y=data["y"])


@dataclass
class CastSpellIntent:
    """Intent to cast a spell."""

    type: Literal["cast_spell"] = "cast_spell"
    spell_name: str = ""
    target_mode: Literal["point", "creature", "self", "none"] = "none"

    @property
    def requires_point(self) -> bool:
        """Whether this spell requires a grid point (area effects)."""
        return self.target_mode == "point"

    @property
    def requires_target_entity(self) -> bool:
        """Whether this spell requires a target creature."""
        return self.target_mode == "creature"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "spell_name": self.spell_name,
            "target_mode": self.target_mode
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CastSpellIntent":
        """Create from dictionary."""
        if data.get("type") != "cast_spell":
            raise IntentParseError(f"Expected type 'cast_spell', got '{data.get('type')}'")

        target_mode = data.get("target_mode", "none")
        if target_mode not in ["point", "creature", "self", "none"]:
            raise IntentParseError(f"Invalid target_mode: {target_mode}")

        return cls(
            spell_name=data.get("spell_name", ""),
            target_mode=target_mode
        )


@dataclass
class MoveIntent:
    """Intent to move to a location."""

    type: Literal["move"] = "move"
    destination: Optional[GridPoint] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"type": self.type}
        if self.destination is not None:
            result["destination"] = self.destination.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MoveIntent":
        """Create from dictionary."""
        if data.get("type") != "move":
            raise IntentParseError(f"Expected type 'move', got '{data.get('type')}'")

        destination = None
        if "destination" in data and data["destination"] is not None:
            destination = GridPoint.from_dict(data["destination"])

        return cls(destination=destination)


@dataclass
class DeclaredAttackIntent:
    """Voice-layer intent to attack a target.

    NOTE: This is the voice/interaction layer intent (target_ref + weapon name).
    It is NOT the combat resolution AttackIntent in aidm.schemas.attack which
    contains full weapon stats and numeric attack bonuses. A bridge layer will
    translate DeclaredAttackIntent → attack.AttackIntent for combat resolution.
    """

    type: Literal["attack"] = "attack"
    target_ref: Optional[str] = None
    weapon: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"type": self.type}
        if self.target_ref is not None:
            result["target_ref"] = self.target_ref
        if self.weapon is not None:
            result["weapon"] = self.weapon
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeclaredAttackIntent":
        """Create from dictionary."""
        if data.get("type") != "attack":
            raise IntentParseError(f"Expected type 'attack', got '{data.get('type')}'")

        return cls(
            target_ref=data.get("target_ref"),
            weapon=data.get("weapon")
        )


@dataclass
class BuyIntent:
    """Intent to purchase items."""

    type: Literal["buy"] = "buy"
    items: List[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default items list."""
        if self.items is None:
            self.items = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "items": self.items
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuyIntent":
        """Create from dictionary."""
        if data.get("type") != "buy":
            raise IntentParseError(f"Expected type 'buy', got '{data.get('type')}'")

        items = data.get("items", [])

        # Validate item structure
        for item in items:
            if not isinstance(item, dict):
                raise IntentParseError("Items must be dictionaries")
            if "name" not in item or "qty" not in item:
                raise IntentParseError("Items must have 'name' and 'qty' fields")

        return cls(items=items)


@dataclass
class RestIntent:
    """Intent to rest.

    D&D 3.5e rest types (PHB p.146):
    - overnight: 8-hour rest (natural healing, spell preparation)
    - full_day: Full day of bed rest (3x natural healing rate)
    """

    type: Literal["rest"] = "rest"
    rest_type: Literal["overnight", "full_day"] = "overnight"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "rest_type": self.rest_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RestIntent":
        """Create from dictionary."""
        if data.get("type") != "rest":
            raise IntentParseError(f"Expected type 'rest', got '{data.get('type')}'")

        rest_type = data.get("rest_type", "overnight")
        if rest_type not in ["overnight", "full_day"]:
            raise IntentParseError(f"Invalid rest_type: {rest_type}")

        return cls(rest_type=rest_type)


# Type alias for all intent types
Intent = CastSpellIntent | MoveIntent | DeclaredAttackIntent | BuyIntent | RestIntent


def parse_intent(data: Dict[str, Any]) -> Intent:
    """
    Parse intent from dictionary based on type field.

    Args:
        data: Intent dictionary with 'type' field

    Returns:
        Parsed intent instance

    Raises:
        IntentParseError: If type is unknown or data is invalid
    """
    intent_type = data.get("type")

    if intent_type == "cast_spell":
        return CastSpellIntent.from_dict(data)
    elif intent_type == "move":
        return MoveIntent.from_dict(data)
    elif intent_type == "attack":
        return DeclaredAttackIntent.from_dict(data)
    elif intent_type == "buy":
        return BuyIntent.from_dict(data)
    elif intent_type == "rest":
        return RestIntent.from_dict(data)
    else:
        raise IntentParseError(f"Unknown intent type: {intent_type}")
