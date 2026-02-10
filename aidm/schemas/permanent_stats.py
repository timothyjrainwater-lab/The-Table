"""SKR-002 Phase 2: Permanent Stat Modification Schema (Schema-Only)

BINDING CONSTRAINTS:
- Schema definition only (dataclasses, enums, validation)
- No algorithmic logic (no derived stat computation, no event emission)
- No CP-16 integration (separate layers)
- Deterministic serialization (sorted keys)

This module defines the permanent stat modifier layer separate from temporary
modifiers (CP-16). See SKR-002-DESIGN-v1.0.md for full specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class Ability(str, Enum):
    """The six ability scores in D&D 3.5e."""
    STR = "str"
    DEX = "dex"
    CON = "con"
    INT = "int"
    WIS = "wis"
    CHA = "cha"


class PermanentModifierType(str, Enum):
    """Types of permanent modifiers (SKR-002 §3.1)."""
    DRAIN = "drain"         # Permanent penalties (negative)
    INHERENT = "inherent"   # Permanent bonuses (positive)


@dataclass(frozen=True)
class PermanentModifierTotals:
    """Cumulative permanent modifiers for one ability (schema-only).

    drain: Cumulative permanent penalties (must be <= 0)
    inherent: Cumulative permanent bonuses (must be >= 0)

    Separation enforces restoration mechanics: Restoration removes drain only,
    never touches inherent bonuses (SKR-002 INV-9).
    """
    drain: int = 0
    inherent: int = 0

    def __post_init__(self) -> None:
        """Validate sign constraints (SKR-002 §3.1)."""
        if self.drain > 0:
            raise ValueError("drain must be <= 0 (permanent penalties only)")
        if self.inherent < 0:
            raise ValueError("inherent must be >= 0 (permanent bonuses only)")

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic serialization (sorted keys)."""
        return {"drain": self.drain, "inherent": self.inherent}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PermanentModifierTotals":
        """Deserialize from dictionary."""
        return cls(
            drain=int(data.get("drain", 0)),
            inherent=int(data.get("inherent", 0))
        )


@dataclass(frozen=True)
class PermanentStatModifiers:
    """All permanent modifiers for an entity (schema-only).

    Stores cumulative permanent modifiers for all six abilities.
    Phase 3 will implement calculation logic; this is structure only.
    """
    str: PermanentModifierTotals = PermanentModifierTotals()
    dex: PermanentModifierTotals = PermanentModifierTotals()
    con: PermanentModifierTotals = PermanentModifierTotals()
    int: PermanentModifierTotals = PermanentModifierTotals()
    wis: PermanentModifierTotals = PermanentModifierTotals()
    cha: PermanentModifierTotals = PermanentModifierTotals()

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic serialization (sorted ability order)."""
        return {
            "str": self.str.to_dict(),
            "dex": self.dex.to_dict(),
            "con": self.con.to_dict(),
            "int": self.int.to_dict(),
            "wis": self.wis.to_dict(),
            "cha": self.cha.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PermanentStatModifiers":
        """Deserialize from dictionary."""
        return cls(
            str=PermanentModifierTotals.from_dict(data.get("str", {})),
            dex=PermanentModifierTotals.from_dict(data.get("dex", {})),
            con=PermanentModifierTotals.from_dict(data.get("con", {})),
            int=PermanentModifierTotals.from_dict(data.get("int", {})),
            wis=PermanentModifierTotals.from_dict(data.get("wis", {})),
            cha=PermanentModifierTotals.from_dict(data.get("cha", {})),
        )


# -----------------------------------------------------------------------------
# Event Payload Schemas (Phase 2: Type Definitions + Validation Only)
# -----------------------------------------------------------------------------

@dataclass
class PermanentStatModifiedEvent:
    """Event payload for permanent stat modification (SKR-002 §3.3).

    Phase 2: Schema definition only (no emission logic).
    Phase 3: Will implement event emission in aidm/core/permanent_stats.py.

    Fields accept Ability/PermanentModifierType enums or their string values.
    """
    event_type: str
    entity_id: str
    ability: str
    modifier_type: str
    amount: int
    source: str
    reversible: bool

    def __post_init__(self) -> None:
        """Validate event payload and normalize enums to strings (SKR-002 §3.3)."""
        # Normalize enums to strings if needed
        if hasattr(self.ability, 'value'):
            object.__setattr__(self, 'ability', self.ability.value)
        if hasattr(self.modifier_type, 'value'):
            object.__setattr__(self, 'modifier_type', self.modifier_type.value)

        if self.event_type != "permanent_stat_modified":
            raise ValueError("event_type must be 'permanent_stat_modified'")
        if not self.entity_id:
            raise ValueError("entity_id required")
        if self.ability not in {a.value for a in Ability}:
            raise ValueError(f"invalid ability: {self.ability}")
        if self.modifier_type not in {t.value for t in PermanentModifierType}:
            raise ValueError(f"invalid modifier_type: {self.modifier_type}")
        if not self.source:
            raise ValueError("source required")

        # Sign constraints (SKR-002 §3.1)
        if self.modifier_type == PermanentModifierType.DRAIN.value:
            if self.amount >= 0:
                raise ValueError("drain amount must be negative")
        if self.modifier_type == PermanentModifierType.INHERENT.value:
            if self.amount <= 0:
                raise ValueError("inherent amount must be positive")

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic serialization (sorted keys)."""
        return {
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "ability": self.ability,
            "modifier_type": self.modifier_type,
            "amount": self.amount,
            "source": self.source,
            "reversible": self.reversible,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PermanentStatModifiedEvent":
        """Deserialize from dictionary."""
        return cls(
            event_type=str(data["event_type"]),
            entity_id=str(data["entity_id"]),
            ability=str(data["ability"]),
            modifier_type=str(data["modifier_type"]),
            amount=int(data["amount"]),
            source=str(data["source"]),
            reversible=bool(data["reversible"]),
        )


@dataclass
class PermanentStatRestoredEvent:
    """Event payload for restoration (removes drain only, SKR-002 §3.3).

    Phase 2: Schema definition only.
    Phase 3: Will implement restoration logic.

    Fields accept Ability/PermanentModifierType enums or their string values.
    """
    event_type: str
    entity_id: str
    ability: str
    modifier_type: str
    amount_removed: int
    source: str

    def __post_init__(self) -> None:
        """Validate event payload and normalize enums to strings (SKR-002 §3.3)."""
        # Normalize enums to strings if needed
        if hasattr(self.ability, 'value'):
            object.__setattr__(self, 'ability', self.ability.value)
        if hasattr(self.modifier_type, 'value'):
            object.__setattr__(self, 'modifier_type', self.modifier_type.value)

        if self.event_type != "permanent_stat_restored":
            raise ValueError("event_type must be 'permanent_stat_restored'")
        if not self.entity_id:
            raise ValueError("entity_id required")
        if self.ability not in {a.value for a in Ability}:
            raise ValueError(f"invalid ability: {self.ability}")

        # Restoration only affects drain (SKR-002 INV-9)
        if self.modifier_type != PermanentModifierType.DRAIN.value:
            raise ValueError("restoration only removes drain, not inherent bonuses")

        if self.amount_removed <= 0:
            raise ValueError("amount_removed must be positive")
        if not self.source:
            raise ValueError("source required")

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic serialization (sorted keys)."""
        return {
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "ability": self.ability,
            "modifier_type": self.modifier_type,
            "amount_removed": self.amount_removed,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PermanentStatRestoredEvent":
        """Deserialize from dictionary."""
        return cls(
            event_type=str(data["event_type"]),
            entity_id=str(data["entity_id"]),
            ability=str(data["ability"]),
            modifier_type=str(data["modifier_type"]),
            amount_removed=int(data["amount_removed"]),
            source=str(data["source"]),
        )


@dataclass
class DerivedStatsRecalculatedEvent:
    """Event payload for derived stat recalculation (SKR-002 §3.3).

    Phase 2: Schema definition only.
    Phase 3: Will implement recalculation pipeline (HP max, AC, saves).

    Fields accept Ability enum or its string value.
    """
    event_type: str
    entity_id: str
    ability_affected: str
    old_effective_score: int
    new_effective_score: int
    hp_max_old: Optional[int]
    hp_max_new: Optional[int]
    recalculated_stats: List[str]

    def __post_init__(self) -> None:
        """Validate event payload and normalize enums to strings (SKR-002 §3.3)."""
        # Normalize enums to strings if needed
        if hasattr(self.ability_affected, 'value'):
            object.__setattr__(self, 'ability_affected', self.ability_affected.value)

        if self.event_type != "derived_stats_recalculated":
            raise ValueError("event_type must be 'derived_stats_recalculated'")
        if not self.entity_id:
            raise ValueError("entity_id required")
        if self.ability_affected not in {a.value for a in Ability}:
            raise ValueError(f"invalid ability_affected: {self.ability_affected}")
        if not isinstance(self.recalculated_stats, list):
            raise ValueError("recalculated_stats must be a list")

        # Ability scores must be >= 0 (SKR-002 INV-6: floor is 0)
        if self.old_effective_score < 0:
            raise ValueError("old_effective_score must be >= 0")
        if self.new_effective_score < 0:
            raise ValueError("new_effective_score must be >= 0")

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic serialization (sorted keys)."""
        return {
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "ability_affected": self.ability_affected,
            "old_effective_score": self.old_effective_score,
            "new_effective_score": self.new_effective_score,
            "hp_max_old": self.hp_max_old,
            "hp_max_new": self.hp_max_new,
            "recalculated_stats": list(self.recalculated_stats),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DerivedStatsRecalculatedEvent":
        """Deserialize from dictionary."""
        return cls(
            event_type=str(data["event_type"]),
            entity_id=str(data["entity_id"]),
            ability_affected=str(data["ability_affected"]),
            old_effective_score=int(data["old_effective_score"]),
            new_effective_score=int(data["new_effective_score"]),
            hp_max_old=data.get("hp_max_old"),
            hp_max_new=data.get("hp_max_new"),
            recalculated_stats=list(data.get("recalculated_stats", [])),
        )


@dataclass
class AbilityScoreDeathEvent:
    """Event payload for ability score death (SKR-002 §3.3, INV-6).

    Phase 2: Schema definition only.
    Phase 3: Will implement death trigger when effective_score <= 0.

    Fields accept Ability enum or its string value.
    """
    event_type: str
    entity_id: str
    ability: str
    final_score: int
    cause: str

    def __post_init__(self) -> None:
        """Validate event payload and normalize enums to strings (SKR-002 §3.3, INV-6)."""
        # Normalize enums to strings if needed
        if hasattr(self.ability, 'value'):
            object.__setattr__(self, 'ability', self.ability.value)

        if self.event_type != "ability_score_death":
            raise ValueError("event_type must be 'ability_score_death'")
        if not self.entity_id:
            raise ValueError("entity_id required")
        if self.ability not in {a.value for a in Ability}:
            raise ValueError(f"invalid ability: {self.ability}")

        # SKR-002 INV-6: Ability score floor is 0 (death trigger)
        if self.final_score != 0:
            raise ValueError("final_score must be 0 for ability_score_death (no negative scores)")

        if not self.cause:
            raise ValueError("cause required")

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic serialization (sorted keys)."""
        return {
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "ability": self.ability,
            "final_score": self.final_score,
            "cause": self.cause,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AbilityScoreDeathEvent":
        """Deserialize from dictionary."""
        return cls(
            event_type=str(data["event_type"]),
            entity_id=str(data["entity_id"]),
            ability=str(data["ability"]),
            final_score=int(data["final_score"]),
            cause=str(data["cause"]),
        )
