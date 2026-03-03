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
    GRAPPLING = "grappling"
    HELPLESS = "helpless"

    # SHOULD-HAVE conditions (CP-16 non-blocking)
    STUNNED = "stunned"
    DAZED = "dazed"
    SHAKEN = "shaken"
    SICKENED = "sickened"

    # Phase 2 conditions (PHB p.310-311, needed for saves/spells)
    FRIGHTENED = "frightened"
    PANICKED = "panicked"
    NAUSEATED = "nauseated"
    FATIGUED = "fatigued"
    EXHAUSTED = "exhausted"
    PARALYZED = "paralyzed"
    STAGGERED = "staggered"
    UNCONSCIOUS = "unconscious"
    PINNED = "pinned"           # WO-ENGINE-GRAPPLE-PIN-001: helpless from grapple escalation
    TURNED = "turned"           # WO-ENGINE-TURN-UNDEAD-001: undead routed by cleric turning

    # WO-ENGINE-CONDITIONS-BLIND-DEAF-001
    BLINDED = "blinded"         # 50% miss on own attacks; opponents +2; -2 AC; loses Dex to AC
    DEAFENED = "deafened"       # 20% verbal spell failure
    ENTANGLED = "entangled"     # -2 attack, -4 Dex
    CONFUSED = "confused"       # d100 behavior roll each turn

    # WO-ENGINE-DAZZLED-CONDITION-001
    DAZZLED = "dazzled"         # -1 attack rolls; -1 Spot checks (PHB p.309)

    # WO-ENGINE-COWERING-FASCINATED-001
    COWERING = "cowering"       # Frozen in fear: no actions, -2 AC, loses Dex to AC (PHB p.309)
    FASCINATED = "fascinated"   # Entranced: no actions, -4 reactive skill checks (PHB p.310)

    # WO-ENGINE-RUN-ACTION-001
    RUNNING = "running"         # Running: loses DEX to AC until start of next turn (PHB p.144)

    # WO-ENGINE-PETRIFIED-CONDITION-001
    PETRIFIED = "petrified"     # Turned to stone: DEX 0 (-5 mod), cannot act, immune to poison/disease (PHB p.310)

    # WO-ENGINE-INCORPOREAL-MISS-CHANCE-001
    INCORPOREAL = "incorporeal"  # Immune to nonmagical physical attacks (PHB p.310)


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
    """Modifier to Armor Class (applied to all attacks unless melee/ranged specific)"""

    ac_modifier_melee: int = 0
    """Modifier to AC against melee attacks only (overrides ac_modifier if non-zero)"""

    ac_modifier_ranged: int = 0
    """Modifier to AC against ranged attacks only (overrides ac_modifier if non-zero)"""

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

    aoo_blocked: bool = False
    """Metadata: cannot make attacks of opportunity (PHB p.156 — grappled/grappling)"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ac_modifier": self.ac_modifier,
            "ac_modifier_melee": self.ac_modifier_melee,
            "ac_modifier_ranged": self.ac_modifier_ranged,
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
            "loses_dex_to_ac": self.loses_dex_to_ac,
            "aoo_blocked": self.aoo_blocked
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConditionModifiers":
        """Create from dictionary."""
        return cls(
            ac_modifier=data.get("ac_modifier", 0),
            ac_modifier_melee=data.get("ac_modifier_melee", 0),
            ac_modifier_ranged=data.get("ac_modifier_ranged", 0),
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
            loses_dex_to_ac=data.get("loses_dex_to_ac", False),
            aoo_blocked=data.get("aoo_blocked", False)
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

    duration_rounds: Optional[int] = None
    """Number of rounds remaining (None = permanent, removed only by explicit action)."""

    immune_to: List[str] = field(default_factory=list)
    """List of damage/effect types this condition grants immunity to (e.g., ['poison', 'disease'])."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "condition_type": self.condition_type.value,
            "source": self.source,
            "modifiers": self.modifiers.to_dict(),
            "applied_at_event_id": self.applied_at_event_id,
            "notes": self.notes
        }
        if self.duration_rounds is not None:
            result["duration_rounds"] = self.duration_rounds
        if self.immune_to:
            result["immune_to"] = list(self.immune_to)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConditionInstance":
        """Create from dictionary."""
        return cls(
            condition_type=ConditionType(data["condition_type"]),
            source=data["source"],
            modifiers=ConditionModifiers.from_dict(data["modifiers"]),
            applied_at_event_id=data["applied_at_event_id"],
            notes=data.get("notes"),
            duration_rounds=data.get("duration_rounds", None),
            immune_to=list(data.get("immune_to", []))
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
            ac_modifier_melee=-4,  # -4 AC vs melee (PHB p.311)
            ac_modifier_ranged=4,  # +4 AC vs ranged (PHB p.311)
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
            movement_prohibited=True,  # Metadata: no normal movement
            aoo_blocked=True  # WO-ENGINE-GRAPPLE-CONDITION-ENFORCE-001: PHB p.156
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Grappled: -4 Dex, no normal movement"
    )


def create_grappling_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Grappling condition for the initiator of a grapple.

    PHB p.156: While grappling, attacker also takes -4 Dex, cannot 5-foot step.
    CP-22: Applied to the grapple initiator when grapple is established.
    """
    return ConditionInstance(
        condition_type=ConditionType.GRAPPLING,
        source=source,
        modifiers=ConditionModifiers(
            dex_modifier=-4,
            movement_prohibited=True,
            aoo_blocked=True  # WO-ENGINE-GRAPPLE-CONDITION-ENFORCE-001: PHB p.156
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Grappling: -4 Dex, no 5-foot step, limited actions"
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
            ac_modifier_melee=-4,  # Melee attacks get +4 bonus (PHB p.310)
            ac_modifier_ranged=0,  # Ranged attacks get no special bonus
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
        notes="Stunned: -2 AC, loses Dex to AC, cannot act",
        duration_rounds=1
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
        notes="Dazed: cannot take actions, no AC penalty",
        duration_rounds=1
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


# ==============================================================================
# PHASE 2 CONDITION DEFINITIONS (PHB 3.5e p.310-311)
# ==============================================================================

def create_frightened_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Frightened condition instance.

    PHB p.310: "A frightened creature flees from the source of its fear as best
    it can. If unable to flee, it may fight. A frightened creature takes a -2
    penalty on all attack rolls, saving throws, skill checks, and ability checks."
    """
    return ConditionInstance(
        condition_type=ConditionType.FRIGHTENED,
        source=source,
        modifiers=ConditionModifiers(
            attack_modifier=-2,
            fort_save_modifier=-2,
            ref_save_modifier=-2,
            will_save_modifier=-2,
            movement_prohibited=False  # Must flee, but CAN move
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Frightened: -2 attacks, saves; must flee from source"
    )


def create_panicked_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Panicked condition instance.

    PHB p.311: "A panicked creature must drop anything it holds and flee at top
    speed from the source of its fear. It can't take any other actions. A panicked
    creature takes a -2 penalty on all saving throws, skill checks, and ability checks."
    """
    return ConditionInstance(
        condition_type=ConditionType.PANICKED,
        source=source,
        modifiers=ConditionModifiers(
            fort_save_modifier=-2,
            ref_save_modifier=-2,
            will_save_modifier=-2
            # Note: Panicked does NOT lose Dex to AC per PHB p.311
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Panicked: drops items, flees, -2 saves"
    )


def create_nauseated_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Nauseated condition instance.

    PHB p.311: "Creatures with the nauseated condition experience stomach
    distress. Nauseated creatures are unable to attack, cast spells, concentrate
    on spells, or do anything else requiring attention. The only action such a
    character can take is a single move action per turn."
    """
    return ConditionInstance(
        condition_type=ConditionType.NAUSEATED,
        source=source,
        modifiers=ConditionModifiers(
            actions_prohibited=True  # Can only take move action
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Nauseated: cannot attack/cast, only move action per turn",
        duration_rounds=1
    )


def create_fatigued_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Fatigued condition instance.

    PHB p.311: "A fatigued character can neither run nor charge and takes a -2
    penalty to Strength and Dexterity."
    """
    return ConditionInstance(
        condition_type=ConditionType.FATIGUED,
        source=source,
        modifiers=ConditionModifiers(
            attack_modifier=-1,  # -2 STR → -1 melee attack (from STR penalty)
            damage_modifier=-1,  # -2 STR → -1 melee damage (PHB p.308)
            dex_modifier=-2  # -2 DEX affects AC, Reflex, ranged
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Fatigued: -2 STR/DEX, can't run or charge"
    )


def create_exhausted_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Exhausted condition instance.

    PHB p.311: "An exhausted character moves at half speed and takes a -6 penalty
    to Strength and Dexterity."
    """
    return ConditionInstance(
        condition_type=ConditionType.EXHAUSTED,
        source=source,
        modifiers=ConditionModifiers(
            attack_modifier=-3,  # -6 STR → -3 melee attack (from STR penalty)
            damage_modifier=-3,  # -6 STR → -3 melee damage (PHB p.308)
            dex_modifier=-6  # -6 DEX affects AC, Reflex, ranged
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Exhausted: -6 STR/DEX, half speed"
    )


def create_paralyzed_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Paralyzed condition instance.

    PHB p.311: "A paralyzed character is frozen in place and unable to move or
    act. A paralyzed character has effective Dexterity and Strength scores of 0
    and is helpless."
    """
    return ConditionInstance(
        condition_type=ConditionType.PARALYZED,
        source=source,
        modifiers=ConditionModifiers(
            ac_modifier_melee=-4,  # Helpless: melee +4 bonus (PHB p.311)
            ac_modifier_ranged=0,  # Helpless: no ranged bonus
            loses_dex_to_ac=True,
            auto_hit_if_helpless=True,
            actions_prohibited=True,
            movement_prohibited=True
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Paralyzed: STR/DEX 0, helpless, cannot move or act"
    )


def create_staggered_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Staggered condition instance.

    PHB p.311: "A staggered character may only take a single move action or
    standard action each round (but not both, nor can she take full-round actions)."
    """
    return ConditionInstance(
        condition_type=ConditionType.STAGGERED,
        source=source,
        modifiers=ConditionModifiers(),  # No numeric penalties, action restriction only
        applied_at_event_id=applied_at_event_id,
        notes="Staggered: only one move or standard action per round"
    )


def create_unconscious_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Unconscious condition instance.

    PHB p.311: "An unconscious character is helpless. Unconsciousness can result
    from having current hit points between -1 and -9, or from nonlethal damage
    in excess of current hit points."
    """
    return ConditionInstance(
        condition_type=ConditionType.UNCONSCIOUS,
        source=source,
        modifiers=ConditionModifiers(
            ac_modifier_melee=-4,  # Helpless: melee +4 bonus (PHB p.311)
            ac_modifier_ranged=0,  # Helpless: no ranged bonus
            loses_dex_to_ac=True,
            auto_hit_if_helpless=True,
            actions_prohibited=True,
            movement_prohibited=True
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Unconscious: helpless, cannot move or act"
    )


def create_pinned_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Pinned condition instance.

    PHB p.156: A pinned character is helpless — cannot take actions,
    loses Dexterity to AC (treated as Dex 0), and melee attackers
    gain +4 bonus (equivalent to attacking helpless target).

    Pinned is more severe than Grappled. Applied when grappler
    succeeds at a second grapple check against an already-grappled target.
    """
    return ConditionInstance(
        condition_type=ConditionType.PINNED,
        source=source,
        modifiers=ConditionModifiers(
            ac_modifier_melee=-4,        # Melee attackers get +4 (PHB p.310 helpless)
            ac_modifier_ranged=0,        # Ranged unaffected
            loses_dex_to_ac=True,        # Dex treated as 0
            auto_hit_if_helpless=True,   # Coup de grace eligible
            actions_prohibited=True,     # Cannot take actions
            movement_prohibited=True,    # Cannot move
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Pinned: helpless, Dex 0, melee +4 bonus, cannot act"
    )


def create_turned_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Turned condition instance.

    PHB p.159 (Turn/Rebuke Undead): A turned undead flees from the cleric as
    fast as possible for 10 rounds. It cannot attack unless cornered or the
    only way to reach safety is through the cleric. Turned undead that are
    commanded by another cleric do not flee but are under that cleric's command.

    WO-ENGINE-TURN-UNDEAD-001:
    - movement_prohibited=False (must flee; CAN and MUST move away)
    - actions_prohibited=True (cannot attack while fleeing unless cornered)
    - No numeric AC/attack modifier (turning is behavioral, not stat-based)
    """
    return ConditionInstance(
        condition_type=ConditionType.TURNED,
        source=source,
        modifiers=ConditionModifiers(
            actions_prohibited=True,    # Cannot attack while fleeing (PHB p.159)
            movement_prohibited=False,  # Must flee at full speed away from cleric
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Turned: flees from cleric for 10 rounds, cannot attack unless cornered"
    )


def create_dazzled_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Dazzled condition instance.

    PHB p.309: "The creature is unable to see well because of overstimulation
    of the eyes. A dazzled creature takes a -1 penalty on attack rolls, Search
    checks, and Spot checks."

    WO-ENGINE-DAZZLED-CONDITION-001:
    - attack_modifier: -1 (flows automatically through get_condition_modifiers)
    - Spot check penalty: -1 (enforced explicitly in skill_resolver for SkillID.SPOT)
    - Does NOT affect saves, AC, or other attributes.
    """
    return ConditionInstance(
        condition_type=ConditionType.DAZZLED,
        source=source,
        modifiers=ConditionModifiers(
            attack_modifier=-1,  # -1 to attack rolls (PHB p.309)
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Dazzled: -1 attack rolls, -1 Spot checks"
    )


def create_cowering_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Cowering condition instance.

    PHB p.309: "A cowering character is frozen in fear and can take no actions.
    A cowering character takes a -2 penalty to Armor Class and loses her
    Dexterity bonus (if any)."

    WO-ENGINE-COWERING-FASCINATED-001:
    - ac_modifier: -2 (PHB p.309)
    - loses_dex_to_ac: True (PHB p.309 — attacker uses flat-footed AC)
    - actions_prohibited: True (no actions possible)

    FINDING-ENGINE-COWERING-FEAR-STACK-001: PHB fear progression is
    Shaken → Frightened → Panicked → Cowering. Engine does not enforce
    escalation. Future WO.
    """
    return ConditionInstance(
        condition_type=ConditionType.COWERING,
        source=source,
        modifiers=ConditionModifiers(
            ac_modifier=-2,          # -2 AC penalty (PHB p.309)
            loses_dex_to_ac=True,    # Loses Dex bonus to AC
            actions_prohibited=True, # Cannot take any actions
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Cowering: frozen in fear. -2 AC, loses Dex to AC, no actions (PHB p.309)"
    )


def create_fascinated_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Fascinated condition instance.

    PHB p.310: "A fascinated creature is entranced by a supernatural or spell
    effect. The creature stands or sits quietly, taking no actions other than
    to pay attention to the fascinating effect... It takes a -4 penalty on
    skill checks made as reactions, such as Listen and Spot checks."

    WO-ENGINE-COWERING-FASCINATED-001:
    - actions_prohibited: True (cannot take any actions while fascinated)
    - No AC modifier (PHB p.310 does not grant AC penalty)

    FINDING-ENGINE-FASCINATED-SKILL-PENALTY-001: PHB grants -4 to reactive
    skill checks (Spot/Listen). ConditionModifiers has no reactive_skill_modifier
    field. The penalty is documented but not wired. Future WO to add
    skill_modifier_reactive: int = 0 to ConditionModifiers.

    KERNEL-06 NOTE: FASCINATED ends on any hostile action directed at the target
    or its allies (PHB p.310). Engine has no 'hostile action directed at' detector.
    Architectural gap — future WO.
    """
    return ConditionInstance(
        condition_type=ConditionType.FASCINATED,
        source=source,
        modifiers=ConditionModifiers(
            actions_prohibited=True, # Cannot take any actions while fascinated
            # NOTE: -4 reactive skill penalty (Spot/Listen) not wired —
            # see FINDING-ENGINE-FASCINATED-SKILL-PENALTY-001
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Fascinated: entranced. No actions, -4 reactive skill checks (PHB p.310)"
    )


def create_running_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Running condition instance.

    PHB p.144: A running character loses their Dexterity bonus to Armor Class
    until the start of their next action. Run is a full-round action granting ×4
    movement speed (×5 with the Run feat — deferred).

    WO-ENGINE-RUN-ACTION-001:
    - loses_dex_to_ac: True (PHB p.144 — attacker uses flat-footed AC)
    - No numeric AC modifier (Dex bonus is entity-specific)
    - No duration_rounds — cleared explicitly at start of actor's next turn
      (same pattern as charge_ac: expires at start of next actor turn, NOT via tick)

    FINDING-ENGINE-RUN-FEAT-001: Run feat removes the DEX-to-AC penalty and
    increases multiplier to ×5. This WO implements baseline only (×4, DEX penalty).
    """
    return ConditionInstance(
        condition_type=ConditionType.RUNNING,
        source=source,
        modifiers=ConditionModifiers(
            loses_dex_to_ac=True,  # Loses Dex bonus to AC while running (PHB p.144)
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Running: loses Dex bonus to AC until start of next turn (PHB p.144)"
        # No duration_rounds — cleared at start of actor's next turn (like charge_ac pattern)
    )


def create_petrified_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Petrified condition instance.

    PHB p.310: A petrified creature is turned to stone.
    - DEX is treated as 0 (–5 DEX modifier) — effectively immobilized
    - No actions can be taken (no attacks, no spells, no movement)
    - Immune to poison and disease (stone doesn't metabolize)
    - Permanent until Remove Petrification / Stone to Flesh

    WO-ENGINE-PETRIFIED-CONDITION-001:
    - actions_prohibited: True (cannot act)
    - immune_to: ["poison", "disease"]
    - DEX override (–5 - entity.dex_mod) applied entity-specifically in get_condition_modifiers()
      because EF.AC is Type 2 (DEX already baked in at chargen).
    - duration_rounds: None (permanent)
    """
    # WO-ENGINE-PETRIFIED-CONDITION-001: PHB p.310
    return ConditionInstance(
        condition_type=ConditionType.PETRIFIED,
        source=source,
        modifiers=ConditionModifiers(
            actions_prohibited=True,  # Cannot take any actions (PHB p.310)
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Petrified: turned to stone. DEX 0, cannot act, immune to poison/disease (PHB p.310)",
        duration_rounds=None,         # Permanent until Stone to Flesh / Remove Petrification
        immune_to=["poison", "disease"],  # Stone doesn't metabolize
    )


def create_incorporeal_condition(
    source: str = "incorporeal_form",
    applied_at_event_id: int = 0,
) -> ConditionInstance:
    """Create Incorporeal condition instance.

    PHB p.310: Incorporeal creatures have no physical body.
    - Immune to all nonmagical attack forms (weapons, natural attacks without magic)
    - +1 or better magic weapons can harm incorporeal creatures
    - 50% chance to ignore damage from corporeal magical sources: CONSUME_DEFERRED
    - Spells harm incorporeal creatures normally (PHB p.310)
    - No AC penalty, no action prohibition, no movement restriction

    WO-ENGINE-INCORPOREAL-MISS-CHANCE-001:
    - Auto-miss enforced in attack_resolver.py for nonmagical physical attacks
    - enhancement_bonus >= 1 = magical weapon (bypasses auto-miss)
    - 50% damage avoidance vs magical weapons: CONSUME_DEFERRED
    - duration_rounds: None (permanent for creature type; spell-granted has duration)
    """
    # WO-ENGINE-INCORPOREAL-MISS-CHANCE-001: PHB p.310
    return ConditionInstance(
        condition_type=ConditionType.INCORPOREAL,
        source=source,
        modifiers=ConditionModifiers(),  # No standard modifiers; immunity enforced in attack_resolver
        applied_at_event_id=applied_at_event_id,
        notes="Incorporeal: immune to nonmagical physical attacks (PHB p.310). 50% magic damage avoidance CONSUME_DEFERRED.",
        duration_rounds=None,  # Permanent for creature type; spell-granted forms may have duration
    )
