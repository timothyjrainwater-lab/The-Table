"""ENGINE-PLAY-LOOP-ROUTING Gate — execute_turn routing for class features (10 tests).

Gate: ENGINE-PLAY-LOOP-ROUTING
Tests: PLR-01 through PLR-10
WO: WO-ENGINE-PLAY-LOOP-ROUTING-001

Five routing branches exercised through execute_turn:
  - RageIntent      → activate_rage
  - SmiteEvilIntent → resolve_smite_evil
  - BardicMusicIntent → resolve_bardic_music
  - WildShapeIntent → resolve_wild_shape
  - RevertFormIntent → resolve_revert_form
"""

import pytest
from copy import deepcopy
from unittest import mock

from aidm.core.play_loop import execute_turn, TurnContext
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import (
    RageIntent,
    SmiteEvilIntent,
    BardicMusicIntent,
    WildShapeIntent,
    RevertFormIntent,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _world(entities):
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
            "cleave_used_this_turn": set(),
        },
    )


def _ctx(actor_id, team="party", turn_index=0):
    return TurnContext(turn_index=turn_index, actor_id=actor_id, actor_team=team)


def _mock_rng():
    stream = mock.MagicMock()
    stream.randint.side_effect = [15, 4] + [10] * 200
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _barbarian(eid="barbarian"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 15,
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.STR_MOD: 3,
        EF.DEX_MOD: 1,
        EF.CON_MOD: 2,
        EF.BAB: 3,
        EF.ATTACK_BONUS: 4,
        EF.CLASS_LEVELS: {"barbarian": 4},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.RAGE_ACTIVE: False,
        EF.RAGE_USES_REMAINING: 2,
        EF.RAGE_ROUNDS_REMAINING: 0,
    }


def _paladin(eid="paladin"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 25,
        EF.HP_MAX: 25,
        EF.AC: 18,
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.STR_MOD: 2,
        EF.DEX_MOD: 1,
        EF.CON_MOD: 1,
        EF.CHA_MOD: 2,
        EF.BAB: 4,
        EF.ATTACK_BONUS: 6,
        EF.CLASS_LEVELS: {"paladin": 4},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.SMITE_USES_REMAINING: 1,
        EF.EQUIPMENT_MELDED: False,
    }


def _bard(eid="bard"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 18,
        EF.HP_MAX: 18,
        EF.AC: 13,
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.STR_MOD: 0,
        EF.DEX_MOD: 2,
        EF.CON_MOD: 0,
        EF.CHA_MOD: 3,
        EF.BAB: 2,
        EF.ATTACK_BONUS: 2,
        EF.CLASS_LEVELS: {"bard": 5},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.BARDIC_MUSIC_USES_REMAINING: 5,
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
        EF.INSPIRE_COURAGE_ROUNDS_REMAINING: 0,
    }


def _druid_human(eid="druid"):
    """Druid in human form with wild shape uses remaining."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 22,
        EF.HP_MAX: 22,
        EF.AC: 14,
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.STR_MOD: 1,
        EF.DEX_MOD: 1,
        EF.CON_MOD: 1,
        EF.BAB: 2,
        EF.ATTACK_BONUS: 3,
        EF.CLASS_LEVELS: {"druid": 5},
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.WILD_SHAPE_ACTIVE: False,
        EF.WILD_SHAPE_FORM: "",
        EF.WILD_SHAPE_USES_REMAINING: 2,
        EF.WILD_SHAPE_SAVED_STATS: {},
        EF.WILD_SHAPE_HOURS_REMAINING: 0,
        EF.EQUIPMENT_MELDED: False,
        EF.NATURAL_ATTACKS: [],
        EF.SIZE_CATEGORY: "medium",
    }


def _druid_wolf(eid="druid"):
    """Druid already in wolf form."""
    d = _druid_human(eid)
    d[EF.WILD_SHAPE_ACTIVE] = True
    d[EF.WILD_SHAPE_FORM] = "wolf"
    d[EF.WILD_SHAPE_USES_REMAINING] = 1
    d[EF.WILD_SHAPE_SAVED_STATS] = {
        "str_mod": 1, "dex_mod": 1, "con_mod": 1, "ac": 14,
        "hp_max": 22, "hp_current": 22, "size_category": "medium",
    }
    d[EF.EQUIPMENT_MELDED] = True
    d[EF.NATURAL_ATTACKS] = [{"name": "bite", "damage": "1d6", "damage_type": "piercing"}]
    return d


def _goblin(eid="goblin"):
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: 15,
        EF.HP_MAX: 15,
        EF.AC: 13,
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.TEMPORARY_MODIFIERS: {},
        EF.POSITION: {"x": 1, "y": 0},
    }


# ===========================================================================
# PLR-01: RageIntent routes to activate_rage — emits rage_start
# ===========================================================================

def test_plr01_rage_intent_emits_rage_start():
    """PLR-01: execute_turn with RageIntent emits rage_start event."""
    barb = _barbarian()
    ws = _world({"barbarian": barb})
    intent = RageIntent(actor_id="barbarian")
    ctx = _ctx("barbarian")

    result = execute_turn(ws, ctx, combat_intent=intent, rng=_mock_rng())

    assert result.status == "ok"
    evt_types = [e.event_type for e in result.events]
    assert "rage_start" in evt_types, f"Expected rage_start, got {evt_types}"


# ===========================================================================
# PLR-02: RageIntent updates RAGE_ACTIVE on world_state
# ===========================================================================

def test_plr02_rage_intent_activates_rage_flag():
    """PLR-02: After RageIntent, RAGE_ACTIVE is True in returned world_state."""
    barb = _barbarian()
    ws = _world({"barbarian": barb})
    intent = RageIntent(actor_id="barbarian")
    ctx = _ctx("barbarian")

    result = execute_turn(ws, ctx, combat_intent=intent, rng=_mock_rng())

    actor = result.world_state.entities["barbarian"]
    assert actor.get(EF.RAGE_ACTIVE) is True, "RAGE_ACTIVE should be True after rage activation"


# ===========================================================================
# PLR-03: RageIntent with no uses remaining emits intent_validation_failed
# ===========================================================================

def test_plr03_rage_no_uses_emits_validation_failed():
    """PLR-03: RageIntent with zero uses emits intent_validation_failed."""
    barb = _barbarian()
    barb[EF.RAGE_USES_REMAINING] = 0
    ws = _world({"barbarian": barb})
    intent = RageIntent(actor_id="barbarian")
    ctx = _ctx("barbarian")

    result = execute_turn(ws, ctx, combat_intent=intent, rng=_mock_rng())

    failed = [e for e in result.events if e.event_type == "intent_validation_failed"]
    assert len(failed) > 0, "Should emit intent_validation_failed when no rage uses remain"


# ===========================================================================
# PLR-04: SmiteEvilIntent routes to resolve_smite_evil — emits smite_declared
# ===========================================================================

def test_plr04_smite_intent_emits_smite_declared():
    """PLR-04: execute_turn with SmiteEvilIntent emits smite_declared event."""
    paladin = _paladin()
    goblin = _goblin()
    ws = _world({"paladin": paladin, "goblin": goblin})
    intent = SmiteEvilIntent(
        actor_id="paladin",
        target_id="goblin",
        weapon={"damage_dice": "1d8", "damage_bonus": 0, "damage_type": "slashing",
                "critical_multiplier": 2, "critical_range": 20, "weapon_type": "one-handed",
                "grip": "one-handed", "is_two_handed": False},
        target_is_evil=True,
    )
    ctx = _ctx("paladin")

    result = execute_turn(ws, ctx, combat_intent=intent, rng=_mock_rng())

    assert result.status == "ok"
    evt_types = [e.event_type for e in result.events]
    assert "smite_declared" in evt_types, f"Expected smite_declared, got {evt_types}"


# ===========================================================================
# PLR-05: SmiteEvilIntent decrements SMITE_USES_REMAINING
# ===========================================================================

def test_plr05_smite_decrements_uses():
    """PLR-05: SmiteEvilIntent decrements SMITE_USES_REMAINING by 1."""
    paladin = _paladin()
    goblin = _goblin()
    uses_before = paladin[EF.SMITE_USES_REMAINING]
    ws = _world({"paladin": paladin, "goblin": goblin})
    intent = SmiteEvilIntent(
        actor_id="paladin",
        target_id="goblin",
        weapon={"damage_dice": "1d8", "damage_bonus": 0, "damage_type": "slashing",
                "critical_multiplier": 2, "critical_range": 20, "weapon_type": "one-handed",
                "grip": "one-handed", "is_two_handed": False},
        target_is_evil=True,
    )
    ctx = _ctx("paladin")

    result = execute_turn(ws, ctx, combat_intent=intent, rng=_mock_rng())

    uses_after = result.world_state.entities["paladin"].get(EF.SMITE_USES_REMAINING, 0)
    assert uses_after == uses_before - 1, \
        f"SMITE_USES_REMAINING should decrease by 1: {uses_before} → {uses_after}"


# ===========================================================================
# PLR-06: BardicMusicIntent routes to resolve_bardic_music — emits inspire_courage_start
# ===========================================================================

def test_plr06_bardic_intent_emits_inspire_courage_start():
    """PLR-06: execute_turn with BardicMusicIntent emits inspire_courage_start."""
    bard = _bard()
    ws = _world({"bard": bard})
    intent = BardicMusicIntent(
        actor_id="bard",
        performance="inspire_courage",
        ally_ids=[],
    )
    ctx = _ctx("bard")

    result = execute_turn(ws, ctx, combat_intent=intent, rng=_mock_rng())

    assert result.status == "ok"
    evt_types = [e.event_type for e in result.events]
    assert "inspire_courage_start" in evt_types, f"Expected inspire_courage_start, got {evt_types}"


# ===========================================================================
# PLR-07: BardicMusicIntent sets INSPIRE_COURAGE_ACTIVE on bard
# ===========================================================================

def test_plr07_bardic_sets_inspire_courage_active():
    """PLR-07: After BardicMusicIntent, INSPIRE_COURAGE_ACTIVE is True on bard."""
    bard = _bard()
    ws = _world({"bard": bard})
    intent = BardicMusicIntent(actor_id="bard", performance="inspire_courage", ally_ids=[])
    ctx = _ctx("bard")

    result = execute_turn(ws, ctx, combat_intent=intent, rng=_mock_rng())

    actor = result.world_state.entities["bard"]
    assert actor.get(EF.INSPIRE_COURAGE_ACTIVE) is True, \
        "INSPIRE_COURAGE_ACTIVE should be True after bardic music"


# ===========================================================================
# PLR-08: WildShapeIntent routes to resolve_wild_shape — emits wild_shape_start
# ===========================================================================

def test_plr08_wild_shape_intent_emits_wild_shape_start():
    """PLR-08: execute_turn with WildShapeIntent emits wild_shape_start event."""
    druid = _druid_human()
    ws = _world({"druid": druid})
    intent = WildShapeIntent(actor_id="druid", form="wolf")
    ctx = _ctx("druid")

    result = execute_turn(ws, ctx, combat_intent=intent, rng=_mock_rng())

    assert result.status == "ok"
    evt_types = [e.event_type for e in result.events]
    assert "wild_shape_start" in evt_types, f"Expected wild_shape_start, got {evt_types}"


# ===========================================================================
# PLR-09: WildShapeIntent sets WILD_SHAPE_ACTIVE on the druid
# ===========================================================================

def test_plr09_wild_shape_sets_active_flag():
    """PLR-09: After WildShapeIntent, WILD_SHAPE_ACTIVE is True and form matches."""
    druid = _druid_human()
    ws = _world({"druid": druid})
    intent = WildShapeIntent(actor_id="druid", form="wolf")
    ctx = _ctx("druid")

    result = execute_turn(ws, ctx, combat_intent=intent, rng=_mock_rng())

    actor = result.world_state.entities["druid"]
    assert actor.get(EF.WILD_SHAPE_ACTIVE) is True, "WILD_SHAPE_ACTIVE should be True"
    assert actor.get(EF.WILD_SHAPE_FORM) == "wolf", \
        f"WILD_SHAPE_FORM should be 'wolf', got {actor.get(EF.WILD_SHAPE_FORM)!r}"


# ===========================================================================
# PLR-10: RevertFormIntent routes to resolve_revert_form — emits wild_shape_end
# ===========================================================================

def test_plr10_revert_form_intent_emits_wild_shape_end():
    """PLR-10: execute_turn with RevertFormIntent emits wild_shape_end event."""
    druid = _druid_wolf()
    ws = _world({"druid": druid})
    intent = RevertFormIntent(actor_id="druid")
    ctx = _ctx("druid")

    result = execute_turn(ws, ctx, combat_intent=intent, rng=_mock_rng())

    assert result.status == "ok"
    evt_types = [e.event_type for e in result.events]
    assert "wild_shape_end" in evt_types, f"Expected wild_shape_end, got {evt_types}"
