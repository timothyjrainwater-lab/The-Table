"""Tests for voice intent schemas."""

import pytest
import json
from aidm.schemas.intents import (
    CastSpellIntent,
    MoveIntent,
    DeclaredAttackIntent,
    BuyIntent,
    RestIntent,
    IntentParseError,
    parse_intent
)
from aidm.schemas.position import Position


def test_cast_spell_requires_point_for_aoe():
    """CastSpellIntent should require point for area effects."""
    fireball = CastSpellIntent(
        spell_name="Fireball",
        target_mode="point"
    )

    assert fireball.requires_point is True
    assert fireball.requires_target_entity is False


def test_cast_spell_requires_entity_for_single_target():
    """CastSpellIntent should require entity for single target spells."""
    magic_missile = CastSpellIntent(
        spell_name="Magic Missile",
        target_mode="creature"
    )

    assert magic_missile.requires_point is False
    assert magic_missile.requires_target_entity is True


def test_cast_spell_self_requires_neither():
    """CastSpellIntent with self targeting requires no external input."""
    shield = CastSpellIntent(
        spell_name="Shield",
        target_mode="self"
    )

    assert shield.requires_point is False
    assert shield.requires_target_entity is False


def test_move_intent_destination_optional():
    """MoveIntent should allow None destination (pending UI point)."""
    move_pending = MoveIntent()

    assert move_pending.destination is None
    assert move_pending.type == "move"

    # With destination
    move_complete = MoveIntent(destination=Position(x=5, y=10))

    assert move_complete.destination is not None
    assert move_complete.destination.x == 5
    assert move_complete.destination.y == 10


def test_intent_serialization_roundtrip():
    """All intents should serialize and deserialize correctly."""
    # CastSpellIntent
    spell = CastSpellIntent(spell_name="Fireball", target_mode="point")
    spell_dict = spell.to_dict()
    spell_json = json.dumps(spell_dict, sort_keys=True)
    spell_restored = CastSpellIntent.from_dict(json.loads(spell_json))

    assert spell_restored.spell_name == "Fireball"
    assert spell_restored.target_mode == "point"

    # MoveIntent with destination
    move = MoveIntent(destination=Position(x=3, y=7))
    move_dict = move.to_dict()
    move_json = json.dumps(move_dict, sort_keys=True)
    move_restored = MoveIntent.from_dict(json.loads(move_json))

    assert move_restored.destination.x == 3
    assert move_restored.destination.y == 7

    # DeclaredAttackIntent
    attack = DeclaredAttackIntent(target_ref="goblin_1", weapon="longsword")
    attack_dict = attack.to_dict()
    attack_json = json.dumps(attack_dict, sort_keys=True)
    attack_restored = DeclaredAttackIntent.from_dict(json.loads(attack_json))

    assert attack_restored.target_ref == "goblin_1"
    assert attack_restored.weapon == "longsword"


def test_buy_intent_items_validation():
    """BuyIntent should validate item structure."""
    buy = BuyIntent(items=[
        {"name": "Potion of Healing", "qty": 2},
        {"name": "Rope (50ft)", "qty": 1}
    ])

    assert len(buy.items) == 2
    assert buy.items[0]["name"] == "Potion of Healing"
    assert buy.items[0]["qty"] == 2


def test_buy_intent_invalid_items_raises_error():
    """BuyIntent should raise error for invalid item structure."""
    with pytest.raises(IntentParseError, match="must have 'name' and 'qty'"):
        BuyIntent.from_dict({
            "type": "buy",
            "items": [{"name": "Sword"}]  # Missing qty
        })

    with pytest.raises(IntentParseError, match="must be dictionaries"):
        BuyIntent.from_dict({
            "type": "buy",
            "items": ["invalid"]
        })


def test_rest_intent_types():
    """RestIntent should support D&D 3.5e rest types."""
    overnight_rest = RestIntent(rest_type="overnight")
    assert overnight_rest.rest_type == "overnight"

    full_day_rest = RestIntent(rest_type="full_day")
    assert full_day_rest.rest_type == "full_day"


def test_rest_intent_invalid_type_raises_error():
    """RestIntent should reject invalid rest types."""
    with pytest.raises(IntentParseError, match="Invalid rest_type"):
        RestIntent.from_dict({
            "type": "rest",
            "rest_type": "medium"
        })


def test_parse_intent_dispatches_correctly():
    """parse_intent() should dispatch to correct intent type."""
    spell_data = {"type": "cast_spell", "spell_name": "Fireball", "target_mode": "point"}
    spell = parse_intent(spell_data)
    assert isinstance(spell, CastSpellIntent)
    assert spell.spell_name == "Fireball"

    move_data = {"type": "move"}
    move = parse_intent(move_data)
    assert isinstance(move, MoveIntent)

    attack_data = {"type": "attack", "target_ref": "G1"}
    attack = parse_intent(attack_data)
    assert isinstance(attack, DeclaredAttackIntent)

    buy_data = {"type": "buy", "items": []}
    buy = parse_intent(buy_data)
    assert isinstance(buy, BuyIntent)

    rest_data = {"type": "rest", "rest_type": "overnight"}
    rest = parse_intent(rest_data)
    assert isinstance(rest, RestIntent)


def test_parse_intent_unknown_type_raises_error():
    """parse_intent() should raise error for unknown types."""
    with pytest.raises(IntentParseError, match="Unknown intent type"):
        parse_intent({"type": "unknown_action"})


def test_intent_type_mismatch_raises_error():
    """Intent.from_dict() should reject wrong type field."""
    with pytest.raises(IntentParseError, match="Expected type 'move'"):
        MoveIntent.from_dict({"type": "attack"})

    with pytest.raises(IntentParseError, match="Expected type 'cast_spell'"):
        CastSpellIntent.from_dict({"type": "rest"})


def test_gridpoint_serialization():
    """Position should serialize deterministically."""
    point = Position(x=10, y=20)
    point_dict = point.to_dict()

    assert point_dict == {"x": 10, "y": 20}

    point_restored = Position.from_dict(point_dict)
    assert point_restored.x == 10
    assert point_restored.y == 20


def test_cast_spell_invalid_target_mode_raises_error():
    """CastSpellIntent should reject invalid target modes."""
    with pytest.raises(IntentParseError, match="Invalid target_mode"):
        CastSpellIntent.from_dict({
            "type": "cast_spell",
            "spell_name": "Test",
            "target_mode": "invalid"
        })


def test_intent_to_dict_omits_none_optionals():
    """Intents should omit None optional fields in to_dict()."""
    attack = DeclaredAttackIntent()
    attack_dict = attack.to_dict()

    assert attack_dict == {"type": "attack"}  # No target_ref or weapon

    move = MoveIntent()
    move_dict = move.to_dict()

    assert move_dict == {"type": "move"}  # No destination
