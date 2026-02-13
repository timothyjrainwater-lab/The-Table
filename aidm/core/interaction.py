"""Interaction engine for Declare→Point→Confirm action commit model.

Models tabletop interaction where voice declares intent and UI supplies points/selections.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Literal, Tuple
from aidm.schemas.intents import Intent, CastSpellIntent, MoveIntent, DeclaredAttackIntent
from aidm.schemas.position import Position  # CP-001: Canonical position type
from aidm.core.state import WorldState
from aidm.core.event_log import Event


@dataclass
class PendingAction:
    """
    Action awaiting additional input from UI layer.

    Represents state between voice declaration and final commit.
    """

    intent: Intent
    """Original intent from voice layer"""

    pending_kind: Optional[Literal["point", "entity"]]
    """Type of input needed: grid point or entity selection"""

    candidates: List[Dict[str, Any]]
    """Candidate entities for disambiguation (if pending_kind='entity')"""

    prompt: str
    """DM clarification prompt for UI display"""

    def __post_init__(self):
        """Initialize default candidates list."""
        if self.candidates is None:
            self.candidates = []


class InteractionEngine:
    """
    Orchestrates voice-declared intents and UI-supplied points/selections.

    Fail-closed: unknown patterns produce errors rather than silent fallbacks.
    """

    def start_intent(
        self,
        world_state: WorldState,
        intent: Intent,
        next_event_id: int,
        timestamp: float
    ) -> Tuple[WorldState, Optional[PendingAction], List[Event]]:
        """
        Begin processing an intent.

        Returns:
            (updated_state, pending_action_or_none, events_emitted)

        If pending_action is None, the intent was complete and committed.
        If pending_action is returned, UI must call commit_point() or commit_entity().
        """
        events = []

        # CastSpellIntent: check if requires point or entity
        if isinstance(intent, CastSpellIntent):
            if intent.requires_point:
                # Need UI to provide point for AOE
                return (
                    world_state,
                    PendingAction(
                        intent=intent,
                        pending_kind="point",
                        candidates=[],
                        prompt=f"Select target point for {intent.spell_name}"
                    ),
                    events
                )
            elif intent.requires_target_entity:
                # Need UI to select creature
                # TODO: Check world_state for valid targets, populate candidates
                return (
                    world_state,
                    PendingAction(
                        intent=intent,
                        pending_kind="entity",
                        candidates=[],  # Placeholder: would scan entities in range
                        prompt=f"Select target for {intent.spell_name}"
                    ),
                    events
                )
            else:
                # Self-cast or no-target, commit immediately
                event = Event(
                    event_id=next_event_id,
                    event_type="spell_cast",
                    timestamp=timestamp,
                    payload={
                        "spell_name": intent.spell_name,
                        "target_mode": intent.target_mode
                    }
                )
                events.append(event)
                return (world_state, None, events)

        # MoveIntent: check if destination provided
        elif isinstance(intent, MoveIntent):
            if intent.destination is None:
                # Need UI to provide destination
                return (
                    world_state,
                    PendingAction(
                        intent=intent,
                        pending_kind="point",
                        candidates=[],
                        prompt="Select movement destination"
                    ),
                    events
                )
            else:
                # Destination already set, commit
                event = Event(
                    event_id=next_event_id,
                    event_type="move",
                    timestamp=timestamp,
                    payload={
                        "destination": intent.destination.to_dict()
                    }
                )
                events.append(event)
                return (world_state, None, events)

        # DeclaredAttackIntent: check if target specified
        elif isinstance(intent, DeclaredAttackIntent):
            if intent.target_ref is None:
                # Need UI to select target
                # TODO: Populate candidates from entities in attack range
                return (
                    world_state,
                    PendingAction(
                        intent=intent,
                        pending_kind="entity",
                        candidates=[],
                        prompt="Select attack target"
                    ),
                    events
                )
            else:
                # Target specified, commit
                event = Event(
                    event_id=next_event_id,
                    event_type="attack",
                    timestamp=timestamp,
                    payload={
                        "target_ref": intent.target_ref,
                        "weapon": intent.weapon
                    }
                )
                events.append(event)
                return (world_state, None, events)

        # Other intent types commit immediately (placeholders)
        else:
            event = Event(
                event_id=next_event_id,
                event_type=intent.type,
                timestamp=timestamp,
                payload=intent.to_dict()
            )
            events.append(event)
            return (world_state, None, events)

    def commit_point(
        self,
        world_state: WorldState,
        pending_action: PendingAction,
        point: Position,
        next_event_id: int,
        timestamp: float
    ) -> Tuple[WorldState, List[Event]]:
        """
        Commit a pending action with UI-supplied point.

        Returns:
            (updated_state, events_emitted)
        """
        if pending_action.pending_kind != "point":
            raise ValueError(f"Expected pending_kind='point', got '{pending_action.pending_kind}'")

        events = []
        intent = pending_action.intent

        # CastSpellIntent with point
        if isinstance(intent, CastSpellIntent):
            event = Event(
                event_id=next_event_id,
                event_type="spell_cast",
                timestamp=timestamp,
                payload={
                    "spell_name": intent.spell_name,
                    "target_mode": intent.target_mode,
                    "target_point": point.to_dict()
                }
            )
            events.append(event)

        # MoveIntent with point
        elif isinstance(intent, MoveIntent):
            event = Event(
                event_id=next_event_id,
                event_type="move",
                timestamp=timestamp,
                payload={
                    "destination": point.to_dict()
                }
            )
            events.append(event)

        else:
            raise ValueError(f"Unexpected intent type for point commit: {type(intent)}")

        return (world_state, events)

    def commit_entity(
        self,
        world_state: WorldState,
        pending_action: PendingAction,
        entity_id: str,
        next_event_id: int,
        timestamp: float
    ) -> Tuple[WorldState, List[Event]]:
        """
        Commit a pending action with UI-supplied entity selection.

        Returns:
            (updated_state, events_emitted)
        """
        if pending_action.pending_kind != "entity":
            raise ValueError(f"Expected pending_kind='entity', got '{pending_action.pending_kind}'")

        events = []
        intent = pending_action.intent

        # CastSpellIntent with entity
        if isinstance(intent, CastSpellIntent):
            event = Event(
                event_id=next_event_id,
                event_type="spell_cast",
                timestamp=timestamp,
                payload={
                    "spell_name": intent.spell_name,
                    "target_mode": intent.target_mode,
                    "target_entity": entity_id
                }
            )
            events.append(event)

        # DeclaredAttackIntent with entity
        elif isinstance(intent, DeclaredAttackIntent):
            event = Event(
                event_id=next_event_id,
                event_type="attack",
                timestamp=timestamp,
                payload={
                    "target_entity": entity_id,
                    "weapon": intent.weapon
                }
            )
            events.append(event)

        else:
            raise ValueError(f"Unexpected intent type for entity commit: {type(intent)}")

        return (world_state, events)
