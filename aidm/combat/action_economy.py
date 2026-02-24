"""Action Economy enforcement kernel — CP-24.

Implements per-round action budget tracking per PHB p.127:
- 1 standard action per round (attack, cast spell, etc.)
- 1 move action per round (move speed, draw weapon, etc.)
- 1 swift action per round (quickened spells, some class features)
- Unlimited free actions
- 1 full-round action (uses both standard + move slots)
- 5-foot step (free but mutually exclusive with move action)

ACTION_TYPES maps intent classes to their action type strings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Optional, Type

if TYPE_CHECKING:
    pass  # Avoid circular imports


# ---------------------------------------------------------------------------
# ActionBudget — per-turn resource tracker
# ---------------------------------------------------------------------------

@dataclass
class ActionBudget:
    """Tracks action resource consumption for one entity's turn.

    Reset at the start of each new turn. All slots begin available (False).
    """

    standard_used: bool = False
    """Standard action slot (attack, cast spell, many abilities)."""

    move_used: bool = False
    """Move action slot (move speed, draw weapon, stand from prone, etc.)."""

    swift_used: bool = False
    """Swift action slot (quickened spells, some class features). PHB p.127."""

    full_round_used: bool = False
    """Full-round action. Consuming this also marks standard + move used."""

    five_foot_step_used: bool = False
    """5-foot step (free action, mutually exclusive with move action)."""

    def can_use(self, action_type: str) -> bool:
        """Return True if the action_type slot is still available.

        Args:
            action_type: One of 'standard', 'move', 'swift', 'free',
                         'full_round', 'five_foot_step'.

        Returns:
            True if the action can be taken, False if already consumed.
        """
        if action_type == "free":
            return True  # Free actions always available
        if action_type == "standard":
            return not self.standard_used and not self.full_round_used
        if action_type == "move":
            return not self.move_used and not self.full_round_used and not self.five_foot_step_used
        if action_type == "swift":
            return not self.swift_used
        if action_type == "full_round":
            return not self.standard_used and not self.move_used and not self.full_round_used
        if action_type == "five_foot_step":
            return not self.move_used and not self.five_foot_step_used
        return True  # Unknown types are allowed (future-proof)

    def consume(self, action_type: str) -> None:
        """Mark an action type as consumed.

        Full-round consumption also marks standard and move used.
        PHB p.127: A full-round action replaces both standard and move actions.

        Args:
            action_type: Action type to consume.
        """
        if action_type == "standard":
            self.standard_used = True
        elif action_type == "move":
            self.move_used = True
        elif action_type == "swift":
            self.swift_used = True
        elif action_type == "full_round":
            self.full_round_used = True
            self.standard_used = True
            self.move_used = True
        elif action_type == "five_foot_step":
            self.five_foot_step_used = True

    def to_dict(self) -> Dict[str, bool]:
        """Serialize to dict for storage in active_combat."""
        return {
            "standard_used": self.standard_used,
            "move_used": self.move_used,
            "swift_used": self.swift_used,
            "full_round_used": self.full_round_used,
            "five_foot_step_used": self.five_foot_step_used,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> "ActionBudget":
        """Deserialize from dict stored in active_combat."""
        return cls(
            standard_used=data.get("standard_used", False),
            move_used=data.get("move_used", False),
            swift_used=data.get("swift_used", False),
            full_round_used=data.get("full_round_used", False),
            five_foot_step_used=data.get("five_foot_step_used", False),
        )

    @classmethod
    def fresh(cls) -> "ActionBudget":
        """Return a blank budget for the start of a turn."""
        return cls()


# ---------------------------------------------------------------------------
# ACTION_TYPES — intent class → action type string
# ---------------------------------------------------------------------------

def _build_action_types() -> Dict[type, str]:
    """Build the intent-class → action-type mapping.

    Late-imported to avoid circular dependencies at module load time.
    """
    from aidm.schemas.attack import AttackIntent, StepMoveIntent
    from aidm.core.spell_resolver import SpellCastIntent

    mapping: Dict[type, str] = {
        AttackIntent: "standard",
        SpellCastIntent: "standard",   # Quickened → swift (checked dynamically)
        StepMoveIntent: "five_foot_step",
    }

    # Optional imports — many may not exist yet
    _try_add(mapping, "aidm.schemas.intents", "MoveIntent", "move")
    _try_add(mapping, "aidm.schemas.intents", "CastSpellIntent", "standard")
    _try_add(mapping, "aidm.core.full_attack_resolver", "FullAttackIntent", "full_round")
    _try_add(mapping, "aidm.schemas.maneuvers", "GrappleIntent", "standard")
    _try_add(mapping, "aidm.schemas.maneuvers", "GrappleEscapeIntent", "standard")
    _try_add(mapping, "aidm.schemas.maneuvers", "BullRushIntent", "standard")
    _try_add(mapping, "aidm.schemas.maneuvers", "TripIntent", "standard")
    _try_add(mapping, "aidm.schemas.maneuvers", "DisarmIntent", "standard")
    _try_add(mapping, "aidm.schemas.maneuvers", "SunderIntent", "standard")
    _try_add(mapping, "aidm.schemas.maneuvers", "OverrunIntent", "standard")
    _try_add(mapping, "aidm.schemas.mounted_combat", "MountedMoveIntent", "move")

    return mapping


def _try_add(mapping: Dict[type, str], module: str, cls_name: str, slot: str) -> None:
    """Safely add a class to the mapping, skipping if import fails."""
    try:
        import importlib
        mod = importlib.import_module(module)
        cls = getattr(mod, cls_name, None)
        if cls is not None:
            mapping[cls] = slot
    except (ImportError, AttributeError):
        pass


# Lazy singleton — built on first access
_ACTION_TYPES: Optional[Dict[type, str]] = None


def get_action_type(intent: object) -> str:
    """Return the action type string for a given intent.

    For SpellCastIntent, checks the `quickened` flag — quickened spells
    consume a swift action rather than a standard action (PHB Metamagic rules).

    Returns:
        Action type string: 'standard', 'move', 'swift', 'free',
        'full_round', 'five_foot_step', or 'free' for unknown types.
    """
    global _ACTION_TYPES
    if _ACTION_TYPES is None:
        _ACTION_TYPES = _build_action_types()

    # Quickened spell check — must come before the type lookup
    from aidm.core.spell_resolver import SpellCastIntent
    if isinstance(intent, SpellCastIntent) and getattr(intent, 'quickened', False):
        return "swift"

    for cls, slot in _ACTION_TYPES.items():
        if isinstance(intent, cls):
            return slot

    return "free"  # Unknown intents cost nothing (conservative/forward-compat)


def check_economy(intent: object, budget: ActionBudget) -> Optional[str]:
    """Check whether an intent can be executed within the current budget.

    Args:
        intent: The combat intent being evaluated.
        budget: The actor's current turn ActionBudget.

    Returns:
        None if action is allowed, or the slot name string if denied
        (e.g. 'standard', 'move', 'swift', 'full_round', 'five_foot_step').
    """
    action_type = get_action_type(intent)
    if not budget.can_use(action_type):
        return action_type
    return None
