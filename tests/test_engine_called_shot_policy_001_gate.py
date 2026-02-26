"""Gate tests: WO-ENGINE-CALLED-SHOT-POLICY-001 — Called shot hard denial (STRAT-CAT-05 Option A).

Called shots are not a D&D 3.5e PHB mechanic. The engine emits action_dropped
with nearest named mechanic suggestions. No state mutation. No action consumed.

Gate label: ENGINE-CALLED-SHOT-001
KERNEL-04 (Intent Semantics) + KERNEL-10 (Adjudication Constitution) touch.
"""

import pytest

from aidm.schemas.intents import CalledShotIntent
from aidm.core.play_loop import _called_shot_suggestions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_world_state(actor_id: str = "actor_01"):
    """Minimal world state with one actor."""
    from aidm.core.state import WorldState
    from aidm.schemas.entity_fields import EF
    return WorldState(
        ruleset_version="3.5e",
        entities={
            actor_id: {
                EF.ENTITY_ID: actor_id,
                EF.HP_CURRENT: 20,
                EF.HP_MAX: 20,
                EF.FEATS: [],
                EF.CONDITIONS: {},
                EF.TEAM: "players",
                EF.DEFEATED: False,
            }
        },
        active_combat={
            "initiative_order": [actor_id],
            "aoo_used_this_round": [],
            "flat_footed_actors": [],
            "feint_flat_footed": [],
        },
    )


def _run_execute_turn(combat_intent: CalledShotIntent, world_state=None):
    """Call execute_turn with a CalledShotIntent and return TurnResult."""
    from aidm.core.play_loop import execute_turn, TurnContext

    actor_id = combat_intent.actor_id
    if world_state is None:
        world_state = _make_world_state(actor_id)

    turn_ctx = TurnContext(
        actor_id=actor_id,
        actor_team="players",
        turn_index=0,
    )

    return execute_turn(
        world_state=world_state,
        turn_ctx=turn_ctx,
        combat_intent=combat_intent,
        doctrine=None,
        rng=None,           # CalledShotIntent exempt from RNG requirement
        timestamp=0.0,
        next_event_id=0,
    )


# ---------------------------------------------------------------------------
# CS-001: action_dropped event emitted
# ---------------------------------------------------------------------------

def test_cs_001_action_dropped_emitted():
    """CS-001: CalledShotIntent → action_dropped event emitted."""
    intent = CalledShotIntent(
        actor_id="actor_01",
        target_description="the eye",
        source_text="I shoot him in the eye",
    )
    result = _run_execute_turn(intent)
    event_types = [e.event_type for e in result.events]
    assert "action_dropped" in event_types, f"CS-001: Expected action_dropped; got {event_types}"

    dropped = next(e for e in result.events if e.event_type == "action_dropped")
    assert dropped.payload["dropped_action_type"] == "called_shot", \
        f"CS-001: Expected dropped_action_type='called_shot'; got {dropped.payload}"
    assert dropped.payload["resolved_action_type"] == "none", \
        f"CS-001: Expected resolved_action_type='none'; got {dropped.payload}"


# ---------------------------------------------------------------------------
# CS-002: weapon → disarm suggestion
# ---------------------------------------------------------------------------

def test_cs_002_weapon_suggests_disarm():
    """CS-002: target_description='the sword' → suggestions include disarm."""
    suggestions = _called_shot_suggestions("the sword")
    disarm_found = any("disarm" in s.lower() for s in suggestions)
    assert disarm_found, f"CS-002: Expected disarm suggestion; got {suggestions}"


# ---------------------------------------------------------------------------
# CS-003: leg → trip suggestion
# ---------------------------------------------------------------------------

def test_cs_003_leg_suggests_trip():
    """CS-003: target_description='the leg' → suggestions include trip."""
    suggestions = _called_shot_suggestions("the leg")
    trip_found = any("trip" in s.lower() for s in suggestions)
    assert trip_found, f"CS-003: Expected trip suggestion; got {suggestions}"


# ---------------------------------------------------------------------------
# CS-004: unknown target → default suggestions returned
# ---------------------------------------------------------------------------

def test_cs_004_unknown_target_default_suggestions():
    """CS-004: target_description='unknown target' → default suggestion list (at least one entry)."""
    suggestions = _called_shot_suggestions("unknown target")
    assert len(suggestions) >= 1, f"CS-004: Expected at least one suggestion; got {suggestions}"


# ---------------------------------------------------------------------------
# CS-005: world_state unchanged after CalledShotIntent
# ---------------------------------------------------------------------------

def test_cs_005_world_state_unchanged():
    """CS-005: CalledShotIntent → world_state entities unchanged (no mutation)."""
    from aidm.schemas.entity_fields import EF
    actor_id = "actor_01"
    ws = _make_world_state(actor_id)
    hp_before = ws.entities[actor_id][EF.HP_CURRENT]

    intent = CalledShotIntent(
        actor_id=actor_id,
        target_description="the head",
        source_text="I aim for the head",
    )
    result = _run_execute_turn(intent, world_state=ws)

    hp_after = result.world_state.entities[actor_id][EF.HP_CURRENT]
    assert hp_before == hp_after, \
        f"CS-005: HP changed after CalledShotIntent: {hp_before} → {hp_after}"


# ---------------------------------------------------------------------------
# CS-006: action budget not consumed
# ---------------------------------------------------------------------------

def test_cs_006_action_budget_not_consumed():
    """CS-006: CalledShotIntent → no action_used event in event log."""
    intent = CalledShotIntent(
        actor_id="actor_01",
        target_description="the throat",
        source_text="I go for the throat",
    )
    result = _run_execute_turn(intent)
    action_used_events = [e for e in result.events if e.event_type == "action_used"]
    assert len(action_used_events) == 0, \
        f"CS-006: Expected no action_used events; got {action_used_events}"


# ---------------------------------------------------------------------------
# CS-007: no attack/damage events emitted
# ---------------------------------------------------------------------------

def test_cs_007_no_state_events():
    """CS-007: CalledShotIntent → no hp_changed, attack_roll, or damage_applied events."""
    intent = CalledShotIntent(
        actor_id="actor_01",
        target_description="the knee",
        source_text="I shoot the orc in the knee",
    )
    result = _run_execute_turn(intent)
    forbidden_types = {"hp_changed", "attack_roll", "damage_applied"}
    found = [e.event_type for e in result.events if e.event_type in forbidden_types]
    assert len(found) == 0, f"CS-007: Unexpected state events: {found}"


# ---------------------------------------------------------------------------
# CS-008: reason field contains denial string
# ---------------------------------------------------------------------------

def test_cs_008_reason_field_populated():
    """CS-008: action_dropped payload['reason'] contains 'not a D&D 3.5e mechanic'."""
    intent = CalledShotIntent(
        actor_id="actor_01",
        target_description="the foot",
        source_text="I try to stomp his foot",
    )
    result = _run_execute_turn(intent)
    dropped = next((e for e in result.events if e.event_type == "action_dropped"), None)
    assert dropped is not None, "CS-008: No action_dropped event found"
    reason = dropped.payload.get("reason", "")
    assert "not a D&D 3.5e mechanic" in reason, \
        f"CS-008: Expected denial string in reason; got '{reason}'"
