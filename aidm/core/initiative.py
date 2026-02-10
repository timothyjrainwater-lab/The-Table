"""Initiative system for deterministic combat round management (CP-14).

Provides:
- Initiative rolling (d20 + Dex modifier + misc)
- Deterministic initiative ordering with tie-breaking
- Combat start sequencing

RNG Discipline:
- Uses dedicated "initiative" RNG stream
- RNG consumption order: iterate actors in stable order, roll for each

Deterministic Tie-Breaking:
1. Higher initiative total
2. Higher Dex modifier
3. Lexicographic actor_id
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from aidm.core.rng_manager import RNGManager


@dataclass
class InitiativeRoll:
    """Result of a single actor's initiative roll."""

    actor_id: str
    """Entity ID of the actor"""

    d20_roll: int
    """Raw d20 roll (1-20)"""

    dex_modifier: int
    """Dexterity modifier"""

    misc_modifier: int
    """Miscellaneous modifier (default 0)"""

    total: int
    """Total initiative (d20 + dex + misc)"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event payload."""
        return {
            "actor_id": self.actor_id,
            "d20_roll": self.d20_roll,
            "dex_modifier": self.dex_modifier,
            "misc_modifier": self.misc_modifier,
            "total": self.total
        }


def roll_initiative(
    actor_id: str,
    dex_modifier: int,
    rng: RNGManager,
    misc_modifier: int = 0
) -> InitiativeRoll:
    """
    Roll initiative for a single actor.

    Args:
        actor_id: Entity ID
        dex_modifier: Dexterity modifier
        rng: RNG manager (uses "initiative" stream)
        misc_modifier: Additional modifiers (feats, spells, etc.)

    Returns:
        InitiativeRoll with d20 roll and total
    """
    # Roll d20 using initiative stream
    d20_roll = rng.stream("initiative").randint(1, 20)

    # Calculate total
    total = d20_roll + dex_modifier + misc_modifier

    return InitiativeRoll(
        actor_id=actor_id,
        d20_roll=d20_roll,
        dex_modifier=dex_modifier,
        misc_modifier=misc_modifier,
        total=total
    )


def sort_initiative_order(rolls: List[InitiativeRoll]) -> List[str]:
    """
    Sort initiative rolls into deterministic turn order.

    Tie-breaking rules:
    1. Higher initiative total
    2. Higher Dex modifier
    3. Lexicographic actor_id

    Args:
        rolls: List of initiative rolls

    Returns:
        List of actor_ids in initiative order (highest first)
    """
    # Sort by: -total (descending), -dex_modifier (descending), actor_id (ascending)
    sorted_rolls = sorted(
        rolls,
        key=lambda r: (-r.total, -r.dex_modifier, r.actor_id)
    )

    return [r.actor_id for r in sorted_rolls]


def roll_initiative_for_all_actors(
    actors: List[Tuple[str, int]],  # (actor_id, dex_modifier)
    rng: RNGManager,
    misc_modifiers: Dict[str, int] = None
) -> Tuple[List[InitiativeRoll], List[str]]:
    """
    Roll initiative for all actors and determine turn order.

    RNG consumption order: iterate actors in stable (lexicographic) order,
    roll for each.

    Args:
        actors: List of (actor_id, dex_modifier) tuples
        rng: RNG manager
        misc_modifiers: Optional dict of actor_id -> misc modifier

    Returns:
        Tuple of (initiative_rolls, initiative_order)
    """
    if misc_modifiers is None:
        misc_modifiers = {}

    # Sort actors lexicographically for stable RNG consumption
    sorted_actors = sorted(actors, key=lambda a: a[0])

    # Roll initiative for each actor
    rolls = []
    for actor_id, dex_mod in sorted_actors:
        misc_mod = misc_modifiers.get(actor_id, 0)
        roll = roll_initiative(actor_id, dex_mod, rng, misc_mod)
        rolls.append(roll)

    # Determine initiative order
    initiative_order = sort_initiative_order(rolls)

    return rolls, initiative_order
