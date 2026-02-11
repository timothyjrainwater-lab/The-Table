"""Combat Reflexes feat and multiple AoO tracking.

Implements D&D 3.5e Combat Reflexes rules (PHB p.92):
- Grants additional AoO per round equal to Dex modifier
- Maximum AoO = 1 + Dex modifier
- Cannot make more than one AoO against same target for same trigger
- Flat-footed characters cannot make AoO (handled elsewhere)

WO-011: Combat Reflexes + Multiple AoO
Reference: PHB p.92 (Combat Reflexes feat)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, FrozenSet

from aidm.schemas.position import Position
from aidm.schemas.geometry import SizeCategory
from aidm.core.geometry_engine import BattleGrid
from aidm.core.reach_resolver import is_square_threatened


# ==============================================================================
# AOO TRACKER DATACLASS
# ==============================================================================

@dataclass(frozen=True)
class AoOTracker:
    """Tracks AoO usage for a single entity within a round.

    Immutable for determinism and easy state management.
    """

    entity_id: str
    """Entity this tracker belongs to."""

    max_aoo_per_round: int = 1
    """Maximum AoO this entity can make per round."""

    aoo_used_this_round: int = 0
    """Number of AoO used this round."""

    aoo_targets_this_round: FrozenSet[str] = field(default_factory=frozenset)
    """Set of target entity IDs that have been targeted by AoO this round.
    Prevents double-tapping the same target for the same trigger."""

    def to_dict(self) -> dict:
        """Serialize for event logging and state storage."""
        return {
            "entity_id": self.entity_id,
            "max_aoo_per_round": self.max_aoo_per_round,
            "aoo_used_this_round": self.aoo_used_this_round,
            "aoo_targets_this_round": list(self.aoo_targets_this_round),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AoOTracker':
        """Deserialize from dict."""
        return cls(
            entity_id=data["entity_id"],
            max_aoo_per_round=data.get("max_aoo_per_round", 1),
            aoo_used_this_round=data.get("aoo_used_this_round", 0),
            aoo_targets_this_round=frozenset(data.get("aoo_targets_this_round", [])),
        )


# ==============================================================================
# CORE FUNCTIONS
# ==============================================================================

def get_max_aoo(
    entity_id: str,
    has_combat_reflexes: bool,
    dex_modifier: int
) -> int:
    """Calculate maximum AoO per round for an entity.

    Per PHB p.92:
    - Without Combat Reflexes: 1 AoO per round
    - With Combat Reflexes: 1 + Dex modifier AoO per round (minimum 1)

    Args:
        entity_id: Entity identifier (unused, for API consistency)
        has_combat_reflexes: True if entity has Combat Reflexes feat
        dex_modifier: Entity's Dexterity modifier

    Returns:
        Maximum number of AoO per round (always at least 1)
    """
    if not has_combat_reflexes:
        return 1

    # Combat Reflexes: 1 + Dex modifier, minimum 1
    return max(1, 1 + dex_modifier)


def can_make_aoo(tracker: AoOTracker, target_id: str) -> bool:
    """Check if entity can make an AoO against a specific target.

    An AoO can be made if:
    1. Entity has not used all their AoO for the round
    2. Entity has not already targeted this specific target this round

    Args:
        tracker: Current AoO tracker state
        target_id: Potential target entity ID

    Returns:
        True if AoO is allowed, False otherwise
    """
    # Check if max AoO exhausted
    if tracker.aoo_used_this_round >= tracker.max_aoo_per_round:
        return False

    # Check if already targeted this entity this round
    if target_id in tracker.aoo_targets_this_round:
        return False

    return True


def record_aoo(tracker: AoOTracker, target_id: str) -> AoOTracker:
    """Record that an AoO was made against a target.

    Returns a new tracker with updated state (immutable pattern).

    Args:
        tracker: Current tracker state
        target_id: Target that was attacked

    Returns:
        New AoOTracker with incremented count and target added
    """
    new_targets = tracker.aoo_targets_this_round | {target_id}
    return AoOTracker(
        entity_id=tracker.entity_id,
        max_aoo_per_round=tracker.max_aoo_per_round,
        aoo_used_this_round=tracker.aoo_used_this_round + 1,
        aoo_targets_this_round=new_targets,
    )


def reset_aoo_for_round(tracker: AoOTracker) -> AoOTracker:
    """Reset AoO tracking for a new round.

    Returns a new tracker with counts cleared (immutable pattern).

    Args:
        tracker: Current tracker state

    Returns:
        New AoOTracker with aoo_used = 0 and targets cleared
    """
    return AoOTracker(
        entity_id=tracker.entity_id,
        max_aoo_per_round=tracker.max_aoo_per_round,
        aoo_used_this_round=0,
        aoo_targets_this_round=frozenset(),
    )


def check_aoo_trigger(
    mover_id: str,
    from_pos: Position,
    to_pos: Position,
    threatener_id: str,
    threatener_pos: Position,
    reach_ft: int,
    threatener_size: SizeCategory = SizeCategory.MEDIUM
) -> bool:
    """Check if movement triggers an AoO from a specific threatener.

    AoO is triggered when:
    - Mover leaves a square threatened by threatener
    - Moving INTO a threatened square does not trigger
    - Moving WITHIN threatened area does not trigger (unless leaving)

    Per PHB p.137: "Moving out of a threatened square usually provokes
    an attack of opportunity from the threatening opponent."

    Args:
        mover_id: Entity that is moving (unused, for API consistency)
        from_pos: Starting position
        to_pos: Destination position
        threatener_id: Potential AoO maker (unused, for API consistency)
        threatener_pos: Position of threatener (top-left for Large+)
        reach_ft: Threatener's reach in feet
        threatener_size: Threatener's size category

    Returns:
        True if movement triggers AoO from this threatener
    """
    # Check if from_pos was threatened
    was_threatened = is_square_threatened(
        entity_pos=threatener_pos,
        size=threatener_size,
        reach_ft=reach_ft,
        target_pos=from_pos
    )

    if not was_threatened:
        # Was never in threatened area, no trigger
        return False

    # Check if to_pos is threatened
    # Note: Moving to a threatened square from outside doesn't trigger
    # but moving from one threatened square to another doesn't trigger either
    # The key is LEAVING the threat range entirely

    # Actually, the rule is simpler: leaving ANY threatened square triggers,
    # regardless of whether you end up in another threatened square
    # PHB p.137: "Moving out of a threatened square usually provokes..."
    # The trigger is leaving, not entering or staying

    # So if from_pos was threatened, AoO is triggered
    return True


# ==============================================================================
# AOO MANAGER CLASS
# ==============================================================================

class AoOManager:
    """Manages AoO tracking for all entities in combat.

    Provides centralized tracking of AoO usage across multiple entities,
    round management, and movement trigger checking.
    """

    def __init__(self):
        """Initialize empty AoO manager."""
        self._trackers: Dict[str, AoOTracker] = {}

    def register_entity(
        self,
        entity_id: str,
        has_combat_reflexes: bool,
        dex_modifier: int
    ) -> None:
        """Register an entity for AoO tracking.

        Args:
            entity_id: Entity identifier
            has_combat_reflexes: True if entity has Combat Reflexes feat
            dex_modifier: Entity's Dexterity modifier
        """
        max_aoo = get_max_aoo(entity_id, has_combat_reflexes, dex_modifier)
        self._trackers[entity_id] = AoOTracker(
            entity_id=entity_id,
            max_aoo_per_round=max_aoo,
            aoo_used_this_round=0,
            aoo_targets_this_round=frozenset(),
        )

    def get_tracker(self, entity_id: str) -> Optional[AoOTracker]:
        """Get the AoO tracker for an entity.

        Args:
            entity_id: Entity identifier

        Returns:
            AoOTracker or None if entity not registered
        """
        return self._trackers.get(entity_id)

    def start_new_round(self) -> None:
        """Reset all AoO trackers for a new round."""
        for entity_id in list(self._trackers.keys()):
            self._trackers[entity_id] = reset_aoo_for_round(self._trackers[entity_id])

    def check_triggers_for_movement(
        self,
        mover_id: str,
        from_pos: Position,
        to_pos: Position,
        grid: BattleGrid,
        reach_by_entity: Optional[Dict[str, int]] = None,
        size_by_entity: Optional[Dict[str, SizeCategory]] = None
    ) -> List[str]:
        """Check which entities can make AoO against a moving entity.

        Args:
            mover_id: Entity that is moving
            from_pos: Starting position
            to_pos: Destination position
            grid: BattleGrid with entity positions
            reach_by_entity: Optional dict of entity_id -> reach in feet
                            Defaults to 5ft if not specified
            size_by_entity: Optional dict of entity_id -> SizeCategory
                           Defaults to MEDIUM if not specified

        Returns:
            List of entity IDs that can make AoO against the mover
        """
        if reach_by_entity is None:
            reach_by_entity = {}
        if size_by_entity is None:
            size_by_entity = {}

        eligible = []

        for entity_id, tracker in self._trackers.items():
            # Skip the mover
            if entity_id == mover_id:
                continue

            # Skip if can't make AoO against this target
            if not can_make_aoo(tracker, mover_id):
                continue

            # Get entity position
            entity_pos = grid.get_entity_position(entity_id)
            if entity_pos is None:
                continue

            # Get reach and size
            reach_ft = reach_by_entity.get(entity_id, 5)
            size = size_by_entity.get(entity_id, SizeCategory.MEDIUM)

            # Check if movement triggers AoO
            if check_aoo_trigger(
                mover_id=mover_id,
                from_pos=from_pos,
                to_pos=to_pos,
                threatener_id=entity_id,
                threatener_pos=entity_pos,
                reach_ft=reach_ft,
                threatener_size=size
            ):
                eligible.append(entity_id)

        return eligible

    def attempt_aoo(self, attacker_id: str, target_id: str) -> bool:
        """Attempt to make an AoO.

        If successful, records the AoO and updates the tracker.

        Args:
            attacker_id: Entity attempting AoO
            target_id: Target of the AoO

        Returns:
            True if AoO was allowed and recorded, False otherwise
        """
        tracker = self._trackers.get(attacker_id)
        if tracker is None:
            return False

        if not can_make_aoo(tracker, target_id):
            return False

        # Record the AoO
        self._trackers[attacker_id] = record_aoo(tracker, target_id)
        return True

    def to_dict(self) -> dict:
        """Serialize manager state."""
        return {
            "trackers": {
                entity_id: tracker.to_dict()
                for entity_id, tracker in self._trackers.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AoOManager':
        """Deserialize manager state."""
        manager = cls()
        for entity_id, tracker_data in data.get("trackers", {}).items():
            manager._trackers[entity_id] = AoOTracker.from_dict(tracker_data)
        return manager
