"""Tests for interaction engine."""

import pytest
from aidm.core.interaction import InteractionEngine, PendingAction
from aidm.schemas.intents import (
    CastSpellIntent,
    MoveIntent,
    DeclaredAttackIntent,
    RestIntent,
)
from aidm.schemas.position import Position
from aidm.core.state import WorldState


def test_cast_spell_produces_pending_point_when_required():
    """start_intent() should produce pending point for AOE spells."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    fireball = CastSpellIntent(
        spell_name="Fireball",
        target_mode="point"
    )

    new_state, pending, events = engine.start_intent(
        world_state=world_state,
        intent=fireball,
        next_event_id=0,
        timestamp=1.0
    )

    assert pending is not None
    assert pending.pending_kind == "point"
    assert "Fireball" in pending.prompt
    assert len(events) == 0  # No events until point committed


def test_cast_spell_produces_pending_entity_when_required():
    """start_intent() should produce pending entity for single-target spells."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    magic_missile = CastSpellIntent(
        spell_name="Magic Missile",
        target_mode="creature"
    )

    new_state, pending, events = engine.start_intent(
        world_state=world_state,
        intent=magic_missile,
        next_event_id=0,
        timestamp=1.0
    )

    assert pending is not None
    assert pending.pending_kind == "entity"
    assert "Magic Missile" in pending.prompt
    assert len(events) == 0


def test_cast_spell_commits_immediately_for_self():
    """start_intent() should commit immediately for self-cast spells."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    shield = CastSpellIntent(
        spell_name="Shield",
        target_mode="self"
    )

    new_state, pending, events = engine.start_intent(
        world_state=world_state,
        intent=shield,
        next_event_id=42,
        timestamp=1.0
    )

    assert pending is None
    assert len(events) == 1
    assert events[0].event_type == "spell_cast"
    assert events[0].payload["spell_name"] == "Shield"
    assert events[0].event_id == 42


def test_commit_point_clears_pending_and_emits_event():
    """commit_point() should emit event with supplied point."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    fireball = CastSpellIntent(
        spell_name="Fireball",
        target_mode="point"
    )

    # Start intent
    _, pending, _ = engine.start_intent(
        world_state=world_state,
        intent=fireball,
        next_event_id=0,
        timestamp=1.0
    )

    assert pending is not None

    # Commit with point
    point = Position(x=10, y=15)
    new_state, events = engine.commit_point(
        world_state=world_state,
        pending_action=pending,
        point=point,
        next_event_id=1,
        timestamp=2.0
    )

    assert len(events) == 1
    assert events[0].event_type == "spell_cast"
    assert events[0].payload["spell_name"] == "Fireball"
    assert events[0].payload["target_point"] == {"x": 10, "y": 15}


def test_move_intent_produces_pending_when_no_destination():
    """start_intent() should produce pending point for move without destination."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    move = MoveIntent()  # No destination

    new_state, pending, events = engine.start_intent(
        world_state=world_state,
        intent=move,
        next_event_id=0,
        timestamp=1.0
    )

    assert pending is not None
    assert pending.pending_kind == "point"
    assert "destination" in pending.prompt.lower()
    assert len(events) == 0


def test_move_intent_commits_immediately_with_destination():
    """start_intent() should commit immediately for move with destination."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    move = MoveIntent(destination=Position(x=5, y=5))

    new_state, pending, events = engine.start_intent(
        world_state=world_state,
        intent=move,
        next_event_id=0,
        timestamp=1.0
    )

    assert pending is None
    assert len(events) == 1
    assert events[0].event_type == "move"
    assert events[0].payload["destination"] == {"x": 5, "y": 5}


def test_ambiguous_attack_produces_pending_entity_with_prompt():
    """start_intent() should produce pending entity for attack without target."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    attack = DeclaredAttackIntent(weapon="longsword")  # No target

    new_state, pending, events = engine.start_intent(
        world_state=world_state,
        intent=attack,
        next_event_id=0,
        timestamp=1.0
    )

    assert pending is not None
    assert pending.pending_kind == "entity"
    assert "target" in pending.prompt.lower()
    assert len(events) == 0


def test_attack_commits_immediately_with_target():
    """start_intent() should commit immediately for attack with target."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    attack = DeclaredAttackIntent(target_ref="goblin_1", weapon="longsword")

    new_state, pending, events = engine.start_intent(
        world_state=world_state,
        intent=attack,
        next_event_id=0,
        timestamp=1.0
    )

    assert pending is None
    assert len(events) == 1
    assert events[0].event_type == "attack"
    assert events[0].payload["target_ref"] == "goblin_1"


def test_commit_entity_emits_attack_event():
    """commit_entity() should emit attack event with supplied entity."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    attack = DeclaredAttackIntent(weapon="longsword")

    # Start intent
    _, pending, _ = engine.start_intent(
        world_state=world_state,
        intent=attack,
        next_event_id=0,
        timestamp=1.0
    )

    # Commit with entity
    new_state, events = engine.commit_entity(
        world_state=world_state,
        pending_action=pending,
        entity_id="goblin_2",
        next_event_id=1,
        timestamp=2.0
    )

    assert len(events) == 1
    assert events[0].event_type == "attack"
    assert events[0].payload["target_entity"] == "goblin_2"
    assert events[0].payload["weapon"] == "longsword"


def test_commit_point_wrong_pending_kind_raises_error():
    """commit_point() should raise error if pending_kind != 'point'."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    attack = DeclaredAttackIntent()

    _, pending, _ = engine.start_intent(
        world_state=world_state,
        intent=attack,
        next_event_id=0,
        timestamp=1.0
    )

    # pending_kind is 'entity', trying to commit point
    with pytest.raises(ValueError, match="Expected pending_kind='point'"):
        engine.commit_point(
            world_state=world_state,
            pending_action=pending,
            point=Position(x=1, y=1),
            next_event_id=1,
            timestamp=2.0
        )


def test_commit_entity_wrong_pending_kind_raises_error():
    """commit_entity() should raise error if pending_kind != 'entity'."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    move = MoveIntent()

    _, pending, _ = engine.start_intent(
        world_state=world_state,
        intent=move,
        next_event_id=0,
        timestamp=1.0
    )

    # pending_kind is 'point', trying to commit entity
    with pytest.raises(ValueError, match="Expected pending_kind='entity'"):
        engine.commit_entity(
            world_state=world_state,
            pending_action=pending,
            entity_id="some_entity",
            next_event_id=1,
            timestamp=2.0
        )


def test_rest_intent_commits_immediately():
    """start_intent() should commit rest immediately (no pending input)."""
    engine = InteractionEngine()
    world_state = WorldState(ruleset_version="3.5")

    rest = RestIntent(rest_type="overnight")

    new_state, pending, events = engine.start_intent(
        world_state=world_state,
        intent=rest,
        next_event_id=0,
        timestamp=1.0
    )

    assert pending is None
    assert len(events) == 1
    assert events[0].event_type == "rest"
