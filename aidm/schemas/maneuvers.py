"""Combat maneuver schemas for CP-18 — Combat Maneuvers.

Data-only contracts for combat maneuvers: Bull Rush, Trip, Overrun,
Sunder (degraded), Disarm (degraded), Grapple-lite (degraded).

DESIGN PRINCIPLES (per CP18_COMBAT_MANEUVERS_DECISIONS.md):
- All maneuvers resolve within a single action window
- No multi-round state machines
- Deterministic RNG consumption order
- Gate-safe: G-T1 only (no G-T3C relational conditions)

DEGRADATIONS:
- Sunder: Narrative only (no persistent item damage)
- Disarm: No persistence (weapon "drops" but no state change)
- Grapple: Unidirectional condition only (defender gets Grappled, attacker unchanged)
- Overrun: Defender avoidance controlled by AI (not interactive)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Literal


# ==============================================================================
# SIZE MODIFIER SCALES (PHB Table 8-1 & p.154)
# ==============================================================================

STANDARD_ATTACK_SIZE_MODIFIER: Dict[str, int] = {
    "fine": 8,
    "diminutive": 4,
    "tiny": 2,
    "small": 1,
    "medium": 0,
    "large": -1,
    "huge": -2,
    "gargantuan": -4,
    "colossal": -8,
}
"""Standard attack size modifiers (PHB Table 8-1).

Used for melee/ranged attack rolls, including the initial touch attack
to initiate a combat maneuver (trip, grapple) and sunder attack rolls.
"""

SIZE_MODIFIER_SCALE: Dict[str, int] = {
    "fine": -16,
    "diminutive": -12,
    "tiny": -8,
    "small": -4,
    "medium": 0,
    "large": 4,
    "huge": 8,
    "gargantuan": 12,
    "colossal": 16,
}
"""Special size modifiers for combat maneuver opposed checks (PHB p.154).

Used for the opposed check portion of grapple, bull rush, trip, overrun, etc.
NOT used for the initial touch attack or attack roll to initiate the maneuver.
"""


def get_size_modifier(size_category: str) -> int:
    """Get SPECIAL size modifier for a given size category (opposed checks).

    Args:
        size_category: Size category string (lowercase)

    Returns:
        Size modifier integer

    Raises:
        ValueError: If size category is unknown
    """
    normalized = size_category.lower().strip()
    if normalized not in SIZE_MODIFIER_SCALE:
        raise ValueError(f"Unknown size category: {size_category}")
    return SIZE_MODIFIER_SCALE[normalized]


def get_standard_attack_size_modifier(size_category: str) -> int:
    """Get STANDARD attack size modifier for a given size category (attack rolls).

    Used for melee touch attacks to initiate maneuvers and sunder attack rolls.
    PHB Table 8-1.

    Args:
        size_category: Size category string (lowercase)

    Returns:
        Size modifier integer

    Raises:
        ValueError: If size category is unknown
    """
    normalized = size_category.lower().strip()
    if normalized not in STANDARD_ATTACK_SIZE_MODIFIER:
        raise ValueError(f"Unknown size category: {size_category}")
    return STANDARD_ATTACK_SIZE_MODIFIER[normalized]


# ==============================================================================
# INTENT SCHEMAS
# ==============================================================================

@dataclass
class BullRushIntent:
    """Bull rush maneuver intent. PHB p.154-155.

    Push opponent back using opposed Strength check.
    Provokes AoOs from all threatening enemies including target.
    """

    attacker_id: str
    """Entity ID of attacker initiating bull rush."""

    target_id: str
    """Entity ID of target being bull rushed."""

    is_charge: bool = False
    """True if bull rush is part of a charge (grants +2 bonus)."""


@dataclass
class TripIntent:
    """Trip maneuver intent. PHB p.158-160.

    Knock opponent prone via melee touch attack + opposed check.
    Provokes AoO from target (unarmed attack).
    """

    attacker_id: str
    """Entity ID of attacker initiating trip."""

    target_id: str
    """Entity ID of target being tripped."""


@dataclass
class OverrunIntent:
    """Overrun maneuver intent. PHB p.157-158.

    Knock down opponent while moving through their space.
    Defender may choose to avoid (controlled by AI in this implementation).
    Provokes AoO from target when entering their space.
    """

    attacker_id: str
    """Entity ID of attacker initiating overrun."""

    target_id: str
    """Entity ID of target being overrun."""

    is_charge: bool = False
    """True if overrun is part of a charge (grants +2 bonus)."""

    defender_avoids: bool = False
    """True if defender chooses to step aside. Controlled by AI/doctrine."""


@dataclass
class SunderIntent:
    """Sunder maneuver intent (DEGRADED). PHB p.158-159.

    Attack a held object (weapon or shield).
    DEGRADED: Damage is logged for narrative only, no persistent state change.
    Provokes AoO from target.
    """

    attacker_id: str
    """Entity ID of attacker initiating sunder."""

    target_id: str
    """Entity ID of target whose item is being sundered."""

    target_item: Literal["weapon", "shield"]
    """Which item is being targeted."""


@dataclass
class DisarmIntent:
    """Disarm maneuver intent (DEGRADED). PHB p.155.

    Knock weapon from opponent's grasp.
    DEGRADED: Weapon "drops" narratively but no persistent state change.
    Provokes AoO from target; if AoO deals damage, disarm auto-fails.
    """

    attacker_id: str
    """Entity ID of attacker initiating disarm."""

    target_id: str
    """Entity ID of target being disarmed."""


@dataclass
class GrappleIntent:
    """Grapple-lite maneuver intent (DEGRADED). PHB p.155-157.

    Initiate grapple via melee touch attack + opposed grapple check.
    DEGRADED: Only applies Grappled condition to target (unidirectional).
    Attacker does NOT gain any condition. No pinning, no escape loops.
    Provokes AoO from target; if AoO deals damage, grapple auto-fails.

    Gate Safety: Avoids G-T3C (Relational Conditions) by being unidirectional.
    """

    attacker_id: str
    """Entity ID of attacker initiating grapple."""

    target_id: str
    """Entity ID of target being grappled."""


# ==============================================================================
# RESULT SCHEMAS
# ==============================================================================

@dataclass
class OpposedCheckResult:
    """Result of an opposed check.

    Used for all maneuver opposed checks: Bull Rush (Str vs Str),
    Trip (Str vs Dex/Str), Overrun (Str vs Dex/Str), Grapple, Disarm, Sunder.
    """

    check_type: str
    """Type of check: 'strength', 'trip', 'grapple', 'disarm', 'sunder', 'overrun'."""

    attacker_roll: int
    """Attacker's d20 roll."""

    attacker_modifier: int
    """Attacker's total modifier (ability + size + bonuses)."""

    attacker_total: int
    """Attacker's total check result (roll + modifier)."""

    defender_roll: int
    """Defender's d20 roll."""

    defender_modifier: int
    """Defender's total modifier (ability + size + bonuses)."""

    defender_total: int
    """Defender's total check result (roll + modifier)."""

    attacker_wins: bool
    """True if attacker won the opposed check (higher total, ties to defender)."""

    margin: int
    """Margin of victory (positive if attacker wins, negative if defender wins)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event payload."""
        return {
            "check_type": self.check_type,
            "attacker_roll": self.attacker_roll,
            "attacker_modifier": self.attacker_modifier,
            "attacker_total": self.attacker_total,
            "defender_roll": self.defender_roll,
            "defender_modifier": self.defender_modifier,
            "defender_total": self.defender_total,
            "attacker_wins": self.attacker_wins,
            "margin": self.margin,
        }


@dataclass
class ManeuverResult:
    """Result of a combat maneuver resolution.

    Captures all events and state changes from maneuver resolution.
    """

    maneuver_type: str
    """Type of maneuver: 'bull_rush', 'trip', 'overrun', 'sunder', 'disarm', 'grapple'."""

    success: bool
    """True if maneuver succeeded."""

    events: List[Dict[str, Any]]
    """All events emitted during resolution (as dicts for serialization)."""

    provoker_defeated: bool = False
    """True if AoO defeated the maneuver initiator (action aborted)."""

    condition_applied: Optional[str] = None
    """Condition applied on success, e.g., 'prone', 'grappled'. None if no condition."""

    position_change: Optional[Dict[str, Any]] = None
    """For bull rush: new positions after push. Structure: {'attacker': {x, y}, 'defender': {x, y}}."""

    counter_attack_result: Optional[Dict[str, Any]] = None
    """For trip/disarm counter: result of counter-attack if it occurred."""

    damage_dealt: int = 0
    """For sunder (narrative only): damage dealt to item."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "maneuver_type": self.maneuver_type,
            "success": self.success,
            "events": self.events,
            "provoker_defeated": self.provoker_defeated,
            "condition_applied": self.condition_applied,
            "position_change": self.position_change,
            "counter_attack_result": self.counter_attack_result,
            "damage_dealt": self.damage_dealt,
        }


@dataclass
class TouchAttackResult:
    """Result of a melee touch attack (used for Trip and Grapple).

    Melee touch attacks use the target's touch AC (base 10 + Dex + deflection + size).
    """

    attacker_id: str
    """Entity ID of attacker."""

    target_id: str
    """Entity ID of target."""

    roll: int
    """d20 roll result."""

    attack_bonus: int
    """Attacker's melee touch attack bonus."""

    total: int
    """Total attack result (roll + bonus)."""

    target_touch_ac: int
    """Target's touch AC."""

    hit: bool
    """True if touch attack hit (total >= touch AC, or natural 20)."""

    is_natural_20: bool = False
    """True if roll was a natural 20 (auto-hit)."""

    is_natural_1: bool = False
    """True if roll was a natural 1 (auto-miss)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event payload."""
        return {
            "attacker_id": self.attacker_id,
            "target_id": self.target_id,
            "roll": self.roll,
            "attack_bonus": self.attack_bonus,
            "total": self.total,
            "target_touch_ac": self.target_touch_ac,
            "hit": self.hit,
            "is_natural_20": self.is_natural_20,
            "is_natural_1": self.is_natural_1,
        }
