"""Gate V13 — Engine Companion Wire.

WO-ENGINE-COMPANION-WIRE

Tests that spawn_companion() correctly wires build_animal_companion() into the
engine event stream, and that SummonCompanionIntent routes through execute_turn()
into WorldState via add_entity events.

20 tests covering:
  V13-01 to V13-06 : spawn_companion() happy-path — entity lands in WorldState
  V13-07 to V13-10 : spawn_companion() failure modes (idempotent, bad type, no class, missing actor)
  V13-11 to V13-14 : add_entity event shape and replay determinism
  V13-15 to V13-17 : SummonCompanionIntent through execute_turn()
  V13-18 to V13-20 : EF metadata fields, parse_intent round-trip, no chargen regressions
"""

import pytest
from copy import deepcopy

from aidm.chargen.builder import build_character
from aidm.chargen.companions import BASE_COMPANION_STATS
from aidm.core.companion_resolver import spawn_companion, SummonCompanionResult
from aidm.core.replay_runner import reduce_event, run as replay_run
from aidm.core.state import WorldState
from aidm.core.event_log import Event, EventLog
from aidm.core.rng_manager import RNGManager
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import SummonCompanionIntent, parse_intent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _druid(level: int) -> dict:
    return build_character(
        "human", "druid", level=level,
        ability_overrides={"str": 10, "dex": 10, "con": 12, "int": 10, "wis": 14, "cha": 10},
    )


def _ranger(level: int) -> dict:
    return build_character(
        "human", "ranger", level=level,
        ability_overrides={"str": 14, "dex": 14, "con": 12, "int": 10, "wis": 12, "cha": 10},
    )


def _fighter(level: int = 5) -> dict:
    return build_character(
        "human", "fighter", level=level,
        ability_overrides={"str": 16, "dex": 12, "con": 14, "int": 10, "wis": 10, "cha": 10},
    )


def _world_with(entities: dict) -> WorldState:
    return WorldState(ruleset_version="3.5e", entities=entities)


def _apply_events(ws: WorldState, events: list) -> WorldState:
    """Apply a list of events to a WorldState via reduce_event."""
    rng = RNGManager(0)
    for evt in events:
        ws = reduce_event(ws, evt, rng)
    return ws


# ---------------------------------------------------------------------------
# V13-01: Druid 1 + wolf — companion lands in WorldState
# ---------------------------------------------------------------------------

def test_v13_01_druid1_wolf_lands_in_world_state():
    druid = _druid(1)
    druid[EF.ENTITY_ID] = "druid_pc"
    ws = _world_with({"druid_pc": druid})

    result = spawn_companion("druid_pc", "wolf", ws)

    assert result.status == "ok"
    assert result.companion_entity_id == "companion_wolf_druid_pc"
    assert len(result.events) == 1
    assert result.events[0].event_type == "add_entity"

    # Apply event and verify entity is in state
    updated = _apply_events(ws, result.events)
    assert "companion_wolf_druid_pc" in updated.entities


# ---------------------------------------------------------------------------
# V13-02: Druid 7 + eagle — correct scaling applied
# ---------------------------------------------------------------------------

def test_v13_02_druid7_eagle_scaling():
    druid = _druid(7)
    druid[EF.ENTITY_ID] = "druid_7"
    ws = _world_with({"druid_7": druid})

    result = spawn_companion("druid_7", "eagle", ws)
    assert result.status == "ok"

    updated = _apply_events(ws, result.events)
    eagle = updated.entities["companion_eagle_druid_7"]

    # Effective level 7: str_dex_adj=2, bonus_hd=4
    # Eagle base: STR 10, DEX 15 → +2 each
    assert eagle[EF.BASE_STATS]["str"] == 12
    assert eagle[EF.BASE_STATS]["dex"] == 17
    # Total HD = 1 + 4 = 5 → LEVEL field = 5
    assert eagle[EF.LEVEL] == 5


# ---------------------------------------------------------------------------
# V13-03: Ranger 4 — effective companion level 1, wolf spawns
# ---------------------------------------------------------------------------

def test_v13_03_ranger4_wolf_effective_level_1():
    ranger = _ranger(4)
    ranger[EF.ENTITY_ID] = "ranger_4"
    ws = _world_with({"ranger_4": ranger})

    # Ranger 4 → effective level = max(0, 4-3) = 1
    result = spawn_companion("ranger_4", "wolf", ws)
    assert result.status == "ok"

    updated = _apply_events(ws, result.events)
    wolf = updated.entities["companion_wolf_ranger_4"]
    # At effective level 1: str_dex_adj=0 → base str=13
    assert wolf[EF.BASE_STATS]["str"] == 13


# ---------------------------------------------------------------------------
# V13-04: All 5 companion types spawn without error
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ctype", list(BASE_COMPANION_STATS.keys()))
def test_v13_04_all_companion_types_spawn(ctype):
    druid = _druid(1)
    druid[EF.ENTITY_ID] = "druid_x"
    ws = _world_with({"druid_x": druid})

    result = spawn_companion("druid_x", ctype, ws)
    assert result.status == "ok", f"Expected ok for {ctype}, got {result.status}: {result.failure_reason}"
    updated = _apply_events(ws, result.events)
    assert f"companion_{ctype}_druid_x" in updated.entities


# ---------------------------------------------------------------------------
# V13-05: EF.COMPANION_OWNER_ID and EF.COMPANION_TYPE tagged on entity
# ---------------------------------------------------------------------------

def test_v13_05_companion_metadata_fields():
    druid = _druid(1)
    druid[EF.ENTITY_ID] = "druid_meta"
    ws = _world_with({"druid_meta": druid})

    result = spawn_companion("druid_meta", "riding_dog", ws)
    assert result.status == "ok"

    updated = _apply_events(ws, result.events)
    dog = updated.entities["companion_riding_dog_druid_meta"]

    assert dog[EF.COMPANION_OWNER_ID] == "druid_meta"
    assert dog[EF.COMPANION_TYPE] == "riding_dog"


# ---------------------------------------------------------------------------
# V13-06: Companion team matches parent team
# ---------------------------------------------------------------------------

def test_v13_06_companion_team_matches_parent():
    druid = _druid(1)
    druid[EF.ENTITY_ID] = "druid_team"
    druid[EF.TEAM] = "party"
    ws = _world_with({"druid_team": druid})

    result = spawn_companion("druid_team", "viper_snake", ws)
    assert result.status == "ok"

    updated = _apply_events(ws, result.events)
    snake = updated.entities["companion_viper_snake_druid_team"]
    assert snake[EF.TEAM] == "party"


# ---------------------------------------------------------------------------
# V13-07: Idempotent guard — spawning same companion twice returns already_active
# ---------------------------------------------------------------------------

def test_v13_07_idempotent_already_active():
    druid = _druid(1)
    druid[EF.ENTITY_ID] = "druid_idem"
    ws = _world_with({"druid_idem": druid})

    result1 = spawn_companion("druid_idem", "wolf", ws)
    assert result1.status == "ok"
    ws_after = _apply_events(ws, result1.events)

    result2 = spawn_companion("druid_idem", "wolf", ws_after)
    assert result2.status == "already_active"
    assert result2.companion_entity_id == "companion_wolf_druid_idem"
    assert len(result2.events) == 0


# ---------------------------------------------------------------------------
# V13-08: Unknown companion type returns invalid_type
# ---------------------------------------------------------------------------

def test_v13_08_invalid_companion_type():
    druid = _druid(1)
    druid[EF.ENTITY_ID] = "druid_badtype"
    ws = _world_with({"druid_badtype": druid})

    result = spawn_companion("druid_badtype", "dragon", ws)
    assert result.status == "invalid_type"
    assert result.events == []
    assert "dragon" in result.failure_reason


# ---------------------------------------------------------------------------
# V13-09: None companion type returns invalid_type
# ---------------------------------------------------------------------------

def test_v13_09_none_companion_type():
    druid = _druid(1)
    druid[EF.ENTITY_ID] = "druid_nonetype"
    ws = _world_with({"druid_nonetype": druid})

    result = spawn_companion("druid_nonetype", None, ws)
    assert result.status == "invalid_type"
    assert result.events == []


# ---------------------------------------------------------------------------
# V13-10: Fighter (no qualifying class) returns invalid_actor
# ---------------------------------------------------------------------------

def test_v13_10_fighter_no_companion_class():
    fighter = _fighter()
    fighter[EF.ENTITY_ID] = "fighter_pc"
    ws = _world_with({"fighter_pc": fighter})

    result = spawn_companion("fighter_pc", "wolf", ws)
    assert result.status == "invalid_actor"
    assert result.events == []
    assert "fighter_pc" in result.failure_reason


# ---------------------------------------------------------------------------
# V13-11: add_entity event payload has correct entity_id and data
# ---------------------------------------------------------------------------

def test_v13_11_event_payload_shape():
    druid = _druid(4)
    druid[EF.ENTITY_ID] = "druid_payload"
    ws = _world_with({"druid_payload": druid})

    result = spawn_companion("druid_payload", "wolf", ws)
    assert result.status == "ok"
    assert len(result.events) == 1

    evt = result.events[0]
    assert evt.event_type == "add_entity"
    assert evt.payload["entity_id"] == "companion_wolf_druid_payload"
    assert evt.payload["owner_id"] == "druid_payload"
    assert evt.payload["companion_type"] == "wolf"
    data = evt.payload["data"]
    assert data[EF.ENTITY_ID] == "companion_wolf_druid_payload"
    assert data[EF.DEFEATED] is False
    assert EF.HP_MAX in data
    assert EF.AC in data


# ---------------------------------------------------------------------------
# V13-12: Replay determinism — same event log → same state_hash
# ---------------------------------------------------------------------------

def test_v13_12_replay_determinism():
    druid = _druid(1)
    druid[EF.ENTITY_ID] = "druid_replay"
    initial_ws = _world_with({"druid_replay": druid})

    result = spawn_companion("druid_replay", "wolf", initial_ws)
    assert result.status == "ok"

    event_log = EventLog()
    for evt in result.events:
        event_log.append(evt)

    report1 = replay_run(
        initial_state=initial_ws,
        master_seed=42,
        event_log=event_log,
    )
    report2 = replay_run(
        initial_state=initial_ws,
        master_seed=42,
        event_log=event_log,
    )

    assert report1.final_hash == report2.final_hash
    assert report1.determinism_verified
    assert "companion_wolf_druid_replay" in report1.final_state.entities


# ---------------------------------------------------------------------------
# V13-13: Replay includes companion in final state entities
# ---------------------------------------------------------------------------

def test_v13_13_replay_companion_in_final_state():
    druid = _druid(7)
    druid[EF.ENTITY_ID] = "druid_r7"
    initial_ws = _world_with({"druid_r7": druid})

    result = spawn_companion("druid_r7", "light_horse", initial_ws)
    assert result.status == "ok"

    event_log = EventLog()
    for evt in result.events:
        event_log.append(evt)

    report = replay_run(initial_state=initial_ws, master_seed=0, event_log=event_log)
    final = report.final_state

    assert "companion_light_horse_druid_r7" in final.entities
    horse = final.entities["companion_light_horse_druid_r7"]
    assert horse[EF.RACE] == "animal"


# ---------------------------------------------------------------------------
# V13-14: spawn_companion does not mutate the original WorldState
# ---------------------------------------------------------------------------

def test_v13_14_no_mutation_of_original_world_state():
    druid = _druid(1)
    druid[EF.ENTITY_ID] = "druid_pure"
    ws = _world_with({"druid_pure": druid})
    original_hash = ws.state_hash()

    result = spawn_companion("druid_pure", "wolf", ws)
    assert result.status == "ok"

    # WorldState must be unchanged after resolver call
    assert ws.state_hash() == original_hash
    assert "companion_wolf_druid_pure" not in ws.entities


# ---------------------------------------------------------------------------
# V13-15: SummonCompanionIntent through execute_turn — companion in WorldState
# ---------------------------------------------------------------------------

def test_v13_15_execute_turn_summon_companion():
    druid = _druid(1)
    druid[EF.ENTITY_ID] = "druid_turn"
    druid[EF.TEAM] = "party"
    ws = _world_with({"druid_turn": druid})

    intent = SummonCompanionIntent(companion_type="wolf")
    turn_ctx = TurnContext(turn_index=0, actor_id="druid_turn", actor_team="party")

    result = execute_turn(
        world_state=ws,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        next_event_id=0,
        timestamp=0.0,
    )

    assert result.status == "ok"
    assert result.narration == "companion_summoned"
    assert "companion_wolf_druid_turn" in result.world_state.entities


# ---------------------------------------------------------------------------
# V13-16: SummonCompanionIntent with invalid type → invalid_intent status
# ---------------------------------------------------------------------------

def test_v13_16_execute_turn_invalid_companion_type():
    druid = _druid(1)
    druid[EF.ENTITY_ID] = "druid_bad"
    druid[EF.TEAM] = "party"
    ws = _world_with({"druid_bad": druid})

    intent = SummonCompanionIntent(companion_type="unicorn")
    turn_ctx = TurnContext(turn_index=0, actor_id="druid_bad", actor_team="party")

    result = execute_turn(
        world_state=ws,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        next_event_id=0,
        timestamp=0.0,
    )

    # Status is ok (turn completes), but companion NOT in world state
    assert "companion_unicorn_druid_bad" not in result.world_state.entities
    # An intent_validation_failed event was emitted
    failed_events = [e for e in result.events if e.event_type == "intent_validation_failed"]
    assert len(failed_events) >= 1


# ---------------------------------------------------------------------------
# V13-17: Fighter attempts summon → invalid_actor, no companion in state
# ---------------------------------------------------------------------------

def test_v13_17_execute_turn_fighter_cannot_summon():
    fighter = _fighter()
    fighter[EF.ENTITY_ID] = "fighter_nosummon"
    fighter[EF.TEAM] = "party"
    ws = _world_with({"fighter_nosummon": fighter})

    intent = SummonCompanionIntent(companion_type="wolf")
    turn_ctx = TurnContext(turn_index=0, actor_id="fighter_nosummon", actor_team="party")

    result = execute_turn(
        world_state=ws,
        turn_ctx=turn_ctx,
        combat_intent=intent,
        next_event_id=0,
        timestamp=0.0,
    )

    assert result.status == "ok"
    # No wolf companion in final state
    companion_entities = [k for k in result.world_state.entities if k.startswith("companion_wolf")]
    assert len(companion_entities) == 0

    # Validation-failure event present
    failed = [e for e in result.events if e.event_type == "intent_validation_failed"]
    assert len(failed) >= 1


# ---------------------------------------------------------------------------
# V13-18: SummonCompanionIntent parse_intent round-trip
# ---------------------------------------------------------------------------

def test_v13_18_parse_intent_round_trip():
    original = SummonCompanionIntent(companion_type="eagle")
    as_dict = original.to_dict()
    parsed = parse_intent(as_dict)

    assert isinstance(parsed, SummonCompanionIntent)
    assert parsed.companion_type == "eagle"
    assert parsed.type == "summon_companion"


# ---------------------------------------------------------------------------
# V13-19: EF constants exist and have correct string values
# ---------------------------------------------------------------------------

def test_v13_19_ef_constants_correct():
    assert EF.COMPANION_OWNER_ID == "companion_owner_id"
    assert EF.COMPANION_TYPE == "companion_type"


# ---------------------------------------------------------------------------
# V13-20: build_character regression — no regressions from wire changes
# ---------------------------------------------------------------------------

def test_v13_20_chargen_regression():
    """build_character() still works for all 11 classes after wire changes."""
    classes = [
        "barbarian", "bard", "cleric", "druid", "fighter",
        "monk", "paladin", "ranger", "rogue", "sorcerer", "wizard",
    ]
    for cls in classes:
        entity = build_character("human", cls, level=1)
        assert entity.get(EF.ENTITY_ID) is not None, f"Missing ENTITY_ID for {cls}"
        assert entity.get(EF.HP_MAX, 0) > 0, f"Zero HP_MAX for {cls}"
