"""Saving throw schemas for CP-17 — Saving Throws & Defensive Resolution Kernel.

Data-only contracts for saving throws, spell resistance, and save outcomes.
NO RESOLUTION LOGIC IN THIS MODULE.

CP-17 SCOPE:
- Fortitude, Reflex, Will saving throws
- Save DC computation
- Save resolution outcomes (success / failure / partial)
- Condition + damage gating via save result
- Spell Resistance (SR) checks (minimal, generic)
- Deterministic RNG consumption for saves

OUT OF SCOPE (deferred to CP-18+):
- Full spellcasting system (spell lists, preparation, targeting)
- Concentration checks
- Counterspelling
- Complex multi-save effects (phased spells)
- Environmental saves (hazards) beyond generic hooks
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class SaveType(str, Enum):
    """Enumeration of saving throw types (PHB p. 177)."""

    FORT = "fortitude"
    """Fortitude save (CON-based): resist poison, disease, death effects"""

    REF = "reflex"
    """Reflex save (DEX-based): avoid area effects, traps"""

    WILL = "will"
    """Will save (WIS-based): resist mental effects, spells"""


class SaveOutcome(str, Enum):
    """Save resolution outcome."""

    SUCCESS = "success"
    """Save succeeded: on_success effect applies"""

    FAILURE = "failure"
    """Save failed: on_failure effect applies"""

    PARTIAL = "partial"
    """Save succeeded with reduced effect (e.g., half damage)"""


@dataclass
class SRCheck:
    """Spell Resistance check specification.

    CP-17 MINIMAL SCOPE:
    - SR is data-only (no spell typing, no penetration feats)
    - Caster level is explicit (no spell system assumptions)
    - SR check occurs before save (PHB p. 177)
    """

    caster_level: int
    """Caster level for SR check (d20 + CL vs SR)"""

    source_id: str
    """Entity ID of caster/effect source (for attribution)"""

    def __post_init__(self):
        """Validate SR check data."""
        if self.caster_level < 1:
            raise ValueError(f"caster_level must be positive, got {self.caster_level}")
        if not self.source_id:
            raise ValueError("source_id cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "caster_level": self.caster_level,
            "source_id": self.source_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SRCheck":
        """Create from dictionary."""
        return cls(
            caster_level=data["caster_level"],
            source_id=data["source_id"]
        )


@dataclass
class EffectSpec:
    """Effect specification for save outcomes (CP-17 minimal scope).

    Defines what happens when a save succeeds, fails, or partially succeeds.

    CP-17 SCOPE:
    - Damage scaling via multiplier (no dice, scales pre-computed damage)
    - Condition application (0..N conditions via CP-16 factory functions)
    - No complex multi-effect sequencing (deferred to CP-18+)

    DESIGN RATIONALE:
    - damage_multiplier avoids re-implementing dice in CP-17
    - Canonical use case: half damage on successful save (multiplier = 0.5)
    - Conditions use CP-16 pipeline (apply_condition)
    """

    damage_multiplier: float = 1.0
    """Multiplier applied to base_damage (allowed: 0.0, 0.5, 1.0)"""

    conditions_to_apply: List[str] = field(default_factory=list)
    """Condition types to apply (e.g., ['prone', 'stunned'])"""

    def __post_init__(self):
        """Validate effect spec."""
        if self.damage_multiplier not in {0.0, 0.5, 1.0}:
            raise ValueError(
                f"damage_multiplier must be 0.0, 0.5, or 1.0, got {self.damage_multiplier}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "damage_multiplier": self.damage_multiplier,
            "conditions_to_apply": self.conditions_to_apply
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EffectSpec":
        """Create from dictionary."""
        return cls(
            damage_multiplier=data.get("damage_multiplier", 1.0),
            conditions_to_apply=data.get("conditions_to_apply", [])
        )


@dataclass
class SaveContext:
    """Saving throw context (resolver-agnostic).

    CP-17 TRIGGER MECHANISM (C-lite):
    - SaveContext is emitted by resolvers (attack, spell, hazard)
    - Not a player-facing intent (internal event)
    - Turn executor resolves save immediately in same turn phase

    EVENT ORDERING:
    1. Effect declared (attack/spell/hazard)
    2. Primary resolution (damage, etc.)
    3. save_triggered event emitted (contains SaveContext)
    4. SR check (if sr_check present)
    5. Save roll
    6. Outcome effects applied

    PARTIAL SAVE RULE:
    - If save succeeds and on_partial is defined → PARTIAL
    - If save succeeds and on_partial is None → SUCCESS
    - Typically used for "half damage on save" (on_partial with 0.5 multiplier)
    """

    save_type: SaveType
    """Type of save required (Fort/Ref/Will)"""

    dc: int
    """Save DC (difficulty class)"""

    source_id: str
    """Entity/effect that triggered the save"""

    target_id: str
    """Entity making the save"""

    base_damage: int = 0
    """Base damage to scale by EffectSpec.damage_multiplier"""

    on_success: Optional[EffectSpec] = None
    """Effect applied on successful save"""

    on_failure: Optional[EffectSpec] = None
    """Effect applied on failed save"""

    on_partial: Optional[EffectSpec] = None
    """Effect applied on partial success (e.g., half damage)"""

    sr_check: Optional[SRCheck] = None
    """Spell Resistance check (if applicable)"""

    save_descriptor: str = ""
    """Optional context tag — "fear", "poison", "spell", "sla", "fey" (default: "").
    WO-ENGINE-SAVECONTEXT-DESCRIPTOR-001: threaded into get_save_bonus() via resolve_save().
    Type 3 (Runtime-Only): not persisted, passed at call site."""

    school: str = ""
    """Spell school (lowercase) for school-specific bonuses — e.g. "enchantment", "illusion".
    WO-ENGINE-SAVECONTEXT-DESCRIPTOR-001: threaded into get_save_bonus() via resolve_save().
    Type 3 (Runtime-Only): not persisted, passed at call site."""

    def __post_init__(self):
        """Validate save context."""
        if self.dc < 0:
            raise ValueError(f"dc must be non-negative, got {self.dc}")
        if not self.source_id:
            raise ValueError("source_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.base_damage < 0:
            raise ValueError(f"base_damage must be non-negative, got {self.base_damage}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "save_type": self.save_type.value,
            "dc": self.dc,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "base_damage": self.base_damage,
            "on_success": self.on_success.to_dict() if self.on_success else None,
            "on_failure": self.on_failure.to_dict() if self.on_failure else None,
            "on_partial": self.on_partial.to_dict() if self.on_partial else None,
            "sr_check": self.sr_check.to_dict() if self.sr_check else None,
            "save_descriptor": self.save_descriptor,
            "school": self.school,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SaveContext":
        """Create from dictionary."""
        return cls(
            save_type=SaveType(data["save_type"]),
            dc=data["dc"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            base_damage=data.get("base_damage", 0),
            on_success=EffectSpec.from_dict(data["on_success"]) if data.get("on_success") else None,
            on_failure=EffectSpec.from_dict(data["on_failure"]) if data.get("on_failure") else None,
            on_partial=EffectSpec.from_dict(data["on_partial"]) if data.get("on_partial") else None,
            sr_check=SRCheck.from_dict(data["sr_check"]) if data.get("sr_check") else None,
            save_descriptor=data.get("save_descriptor", ""),
            school=data.get("school", ""),
        )
