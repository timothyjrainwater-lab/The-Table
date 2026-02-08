"""Condition schemas for CP-16 — Conditions & Status Effects Kernel.

Data-only contracts for combat conditions with mechanical modifiers.
NO ENFORCEMENT LOGIC IN THIS MODULE.

CP-16 MINIMAL SCOPE (OPTION A):
- Conditions are metadata-only descriptors
- Modifiers affect resolution queries only
- No enforcement of movement, standing, actions, or checks
- All enforcement deferred to CP-17+

Conditions describe mechanical truth but do NOT enforce legality.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class ConditionType(str, Enum):
    """Enumeration of condition types (fail-closed)."""

    # MUST-HAVE conditions (CP-16 blocking)
    PRONE = "prone"
    FLAT_FOOTED = "flat_footed"
    GRAPPLED = "grappled"
    HELPLESS = "helpless"

    # SHOULD-HAVE conditions (CP-16 non-blocking)
    STUNNED = "stunned"
    DAZED = "dazed"
    SHAKEN = "shaken"
    SICKENED = "sickened"


@dataclass
class ConditionModifiers:
    """Mechanical modifiers imposed by a condition.

    All modifiers are metadata-only descriptors.
    Resolvers query these modifiers but do NOT enforce legality.

    CP-16 MINIMAL SCOPE:
    - Numeric modifiers affect resolution (AC, attack, damage)
    - Boolean flags are descriptive only (no enforcement)
    - Enforcement of restrictions deferred to CP-17+

    CP-17 EXTENSION:
    - Saving throw modifiers (Fort/Ref/Will)
    - Applied to save resolution pipeline
    """

    ac_modifier: int = 0
    """Modifier to Armor Class (e.g., -4 for prone vs melee)"""

    attack_modifier: int = 0
    """Modifier to attack rolls (e.g., -2 for shaken)"""

    damage_modifier: int = 0
    """Modifier to damage rolls (e.g., -2 for sickened)"""

    dex_modifier: int = 0
    """Modifier to Dexterity-based calculations (e.g., -4 for grappled)"""

    # CP-17 extension: saving throw modifiers
    fort_save_modifier: int = 0
    """Modifier to Fortitude saves (e.g., -2 for shaken)"""

    ref_save_modifier: int = 0
    """Modifier to Reflex saves (e.g., -2 for shaken)"""

    will_save_modifier: int = 0
    """Modifier to Will saves (e.g., -2 for shaken)"""

    # Metadata-only flags (NO ENFORCEMENT in CP-16)
    movement_prohibited: bool = False
    """Metadata: movement restricted (enforcement deferred to CP-17+)"""

    actions_prohibited: bool = False
    """Metadata: actions restricted (enforcement deferred to CP-17+)"""

    standing_triggers_aoo: bool = False
    """Metadata: standing from prone provokes AoO (enforcement deferred to CP-17+)"""

    auto_hit_if_helpless: bool = False
    """Metadata: melee attacks auto-hit helpless targets (enforcement deferred to CP-17+)"""

    loses_dex_to_ac: bool = False
    """Metadata: loses Dex bonus to AC (enforcement deferred to CP-17+)"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ac_modifier": self.ac_modifier,
            "attack_modifier": self.attack_modifier,
            "damage_modifier": self.damage_modifier,
            "dex_modifier": self.dex_modifier,
            "fort_save_modifier": self.fort_save_modifier,  # CP-17
            "ref_save_modifier": self.ref_save_modifier,    # CP-17
            "will_save_modifier": self.will_save_modifier,  # CP-17
            "movement_prohibited": self.movement_prohibited,
            "actions_prohibited": self.actions_prohibited,
            "standing_triggers_aoo": self.standing_triggers_aoo,
            "auto_hit_if_helpless": self.auto_hit_if_helpless,
            "loses_dex_to_ac": self.loses_dex_to_ac
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConditionModifiers":
        """Create from dictionary."""
        return cls(
            ac_modifier=data.get("ac_modifier", 0),
            attack_modifier=data.get("attack_modifier", 0),
            damage_modifier=data.get("damage_modifier", 0),
            dex_modifier=data.get("dex_modifier", 0),
            fort_save_modifier=data.get("fort_save_modifier", 0),  # CP-17
            ref_save_modifier=data.get("ref_save_modifier", 0),    # CP-17
            will_save_modifier=data.get("will_save_modifier", 0),  # CP-17
            movement_prohibited=data.get("movement_prohibited", False),
            actions_prohibited=data.get("actions_prohibited", False),
            standing_triggers_aoo=data.get("standing_triggers_aoo", False),
            auto_hit_if_helpless=data.get("auto_hit_if_helpless", False),
            loses_dex_to_ac=data.get("loses_dex_to_ac", False)
        )


@dataclass
class ConditionInstance:
    """Single condition instance on an entity.

    Conditions are event-sourced: applied via condition_applied event,
    removed via condition_removed event.

    CP-16 SCOPE:
    - No duration tracking (manual removal only)
    - No automatic expiration (deferred to CP-17+)
    - No stacking logic (identical conditions overwrite)
    """

    condition_type: ConditionType
    """Type of condition"""

    source: str
    """Source of condition (e.g., 'trip_attack', 'spell_hold_person', 'grapple_initiated')"""

    modifiers: ConditionModifiers
    """Mechanical modifiers imposed by this condition"""

    applied_at_event_id: int
    """Event ID when condition was applied (for provenance)"""

    notes: Optional[str] = None
    """Optional notes (e.g., 'Prone from successful trip attempt')"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "condition_type": self.condition_type.value,
            "source": self.source,
            "modifiers": self.modifiers.to_dict(),
            "applied_at_event_id": self.applied_at_event_id,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConditionInstance":
        """Create from dictionary."""
        return cls(
            condition_type=ConditionType(data["condition_type"]),
            source=data["source"],
            modifiers=ConditionModifiers.from_dict(data["modifiers"]),
            applied_at_event_id=data["applied_at_event_id"],
            notes=data.get("notes")
        )


# ==============================================================================
# CANONICAL CONDITION DEFINITIONS (PHB 3.5e)
# ==============================================================================

def create_prone_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Prone condition instance.

    PHB p. 311: "A prone attacker has a -4 penalty on melee attack rolls and
    cannot use a ranged weapon (except for a crossbow). A prone defender gains
    a +4 bonus to Armor Class against ranged attacks, but takes a -4 penalty
    to AC against melee attacks."

    CP-16 MINIMAL SCOPE:
    - AC modifier: -4 vs melee (resolvers apply conditionally)
    - Attack modifier: -4 for melee attacks
    - Standing triggers AoO: metadata only (no enforcement)
    """
    return ConditionInstance(
        condition_type=ConditionType.PRONE,
        source=source,
        modifiers=ConditionModifiers(
            ac_modifier=-4,  # vs melee (resolvers apply based on attack type)
            attack_modifier=-4,  # melee attacks only
            standing_triggers_aoo=True  # Metadata: standing provokes (PHB p. 311)
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Prone: -4 AC vs melee, -4 melee attack, standing provokes AoO"
    )


def create_flat_footed_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Flat-Footed condition instance.

    PHB p. 137: "A character who has not yet acted during a combat is
    flat-footed, not yet reacting normally to the situation. A flat-footed
    character loses his Dexterity bonus to AC."

    CP-16 MINIMAL SCOPE:
    - Loses Dex to AC: metadata only (resolver queries entity's Dex bonus)
    - No numeric modifier (Dex bonus is entity-specific)
    """
    return ConditionInstance(
        condition_type=ConditionType.FLAT_FOOTED,
        source=source,
        modifiers=ConditionModifiers(
            loses_dex_to_ac=True  # Metadata: resolver must subtract Dex bonus
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Flat-footed: loses Dex bonus to AC"
    )


def create_grappled_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Grappled condition instance.

    PHB p. 156: "While grappling, you take a -4 penalty to Dexterity. You
    cannot move normally while grappled."

    CP-16 MINIMAL SCOPE:
    - Dex modifier: -4 (affects Dex-based calculations)
    - Movement prohibited: metadata only (no enforcement)
    - No grapple resolution logic (deferred to CP-18+)
    """
    return ConditionInstance(
        condition_type=ConditionType.GRAPPLED,
        source=source,
        modifiers=ConditionModifiers(
            dex_modifier=-4,
            movement_prohibited=True  # Metadata: no normal movement
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Grappled: -4 Dex, no normal movement"
    )


def create_helpless_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Helpless condition instance.

    PHB p. 311: "A helpless character is paralyzed, held, bound, sleeping,
    unconscious, or otherwise completely at an opponent's mercy. A helpless
    defender has a Dexterity of 0 (-5 modifier). Melee attacks against a
    helpless target get a +4 bonus (equivalent to attacking a prone target).
    Ranged attacks get no special bonus. Rogues can sneak attack helpless
    targets."

    CP-16 MINIMAL SCOPE:
    - Loses Dex to AC: metadata (Dex = 0 → -5 modifier)
    - AC modifier: -4 (melee attacks get +4, equivalent to prone)
    - Auto-hit metadata: melee attacks can coup de grace (enforcement deferred)
    """
    return ConditionInstance(
        condition_type=ConditionType.HELPLESS,
        source=source,
        modifiers=ConditionModifiers(
            ac_modifier=-4,  # Melee attacks get +4 bonus
            loses_dex_to_ac=True,  # Dex = 0
            auto_hit_if_helpless=True,  # Metadata: coup de grace eligible
            actions_prohibited=True  # Metadata: cannot take actions
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Helpless: Dex 0, -4 AC vs melee, cannot act"
    )


def create_stunned_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Stunned condition instance.

    PHB p. 311: "A stunned creature drops everything held, can't take actions,
    takes a -2 penalty to AC, and loses its Dexterity bonus to AC (if any)."

    CP-16 MINIMAL SCOPE:
    - AC modifier: -2
    - Loses Dex to AC: metadata
    - Actions prohibited: metadata only (no enforcement)
    """
    return ConditionInstance(
        condition_type=ConditionType.STUNNED,
        source=source,
        modifiers=ConditionModifiers(
            ac_modifier=-2,
            loses_dex_to_ac=True,
            actions_prohibited=True  # Metadata: cannot take actions
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Stunned: -2 AC, loses Dex to AC, cannot act"
    )


def create_dazed_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Dazed condition instance.

    PHB p. 311: "A dazed creature can take no actions, but has no penalty to AC."

    CP-16 MINIMAL SCOPE:
    - No AC penalty
    - Actions prohibited: metadata only (no enforcement)
    """
    return ConditionInstance(
        condition_type=ConditionType.DAZED,
        source=source,
        modifiers=ConditionModifiers(
            actions_prohibited=True  # Metadata: cannot take actions
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Dazed: cannot take actions, no AC penalty"
    )


def create_shaken_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Shaken condition instance.

    PHB p. 311: "A shaken character takes a -2 penalty on attack rolls, saving
    throws, skill checks, and ability checks."

    CP-16 MINIMAL SCOPE:
    - Attack modifier: -2
    - Saving throws/skill checks: out of scope (no system exists)

    CP-17 EXTENSION:
    - Saving throw modifiers: -2 to Fort/Ref/Will
    """
    return ConditionInstance(
        condition_type=ConditionType.SHAKEN,
        source=source,
        modifiers=ConditionModifiers(
            attack_modifier=-2,
            fort_save_modifier=-2,  # CP-17 extension
            ref_save_modifier=-2,   # CP-17 extension
            will_save_modifier=-2   # CP-17 extension
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Shaken: -2 attack rolls and saving throws"
    )


def create_sickened_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Sickened condition instance.

    PHB p. 311: "A sickened character takes a -2 penalty on attack rolls,
    weapon damage rolls, saving throws, skill checks, and ability checks."

    CP-16 MINIMAL SCOPE:
    - Attack modifier: -2
    - Damage modifier: -2
    - Saving throws/skill checks: out of scope (no system exists)

    CP-17 EXTENSION:
    - Saving throw modifiers: -2 to Fort/Ref/Will
    """
    return ConditionInstance(
        condition_type=ConditionType.SICKENED,
        source=source,
        modifiers=ConditionModifiers(
            attack_modifier=-2,
            damage_modifier=-2,
            fort_save_modifier=-2,  # CP-17 extension
            ref_save_modifier=-2,   # CP-17 extension
            will_save_modifier=-2   # CP-17 extension
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Sickened: -2 attack, damage, and saving throws"
    )
