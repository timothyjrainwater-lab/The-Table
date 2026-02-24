"""Gate ENGINE-DEFEND — WO-ENGINE-DEFEND-001

Tests:
DF-01: FightDefensivelyIntent applies -4 attack / +2 AC (no Combat Expertise)
DF-02: FightDefensivelyIntent with Combat Expertise applies -5 attack / +5 AC
DF-03: TotalDefenseIntent applies +4 dodge AC bonus
DF-04: TotalDefenseIntent and FightDefensively both cost standard action
DF-05: fight_defensively_applied event emitted with penalty/bonus
DF-06: total_defense_applied event emitted with bonus=4
DF-07: Fight defensively AC bonus reduces effective AC of target (attack roll calculation)
DF-08: fight_defensively_expired emitted at start of next turn
DF-09: total_defense_expired emitted at start of next turn
DF-10: parse_intent roundtrips FightDefensivelyIntent and TotalDefenseIntent
"""

import unittest.mock as mock
from typing import Any, Dict

import pytest

from aidm.core.state import WorldState
from aidm.core.play_loop import TurnContext, execute_turn
from aidm.core.action_economy import ActionBudget, get_action_type, check_economy
from aidm.schemas.intents import FightDefensivelyIntent, TotalDefenseIntent, parse_intent
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity(eid: str, team: str, hp: int = 30, ac: int = 12, attack_bonus: int = 5,
             bab: int = 5, feats: list = None, temporary_modifiers: dict = None,
             pos: dict = None) -> Dict[str, Any]:
    e = {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp,
        EF.AC: ac,
        EF.ATTACK_BONUS: attack_bonus,
        EF.BAB: bab,
        EF.STR_MOD: 2,
        EF.DEX_MOD: 0,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: feats or [],
        EF.POSITION: pos or {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.TEMPORARY_MODIFIERS: temporary_modifiers or {},
    }
    return e


def _world(entities: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={"initiative_order": list(entities.keys())},
    )


def _ctx(actor_id: str, team: str = "party") -> TurnContext:
    return TurnContext(turn_index=0, actor_id=actor_id, actor_team=team)


def _rng(rolls=(15, 5)) -> mock.MagicMock:
    stream = mock.MagicMock()
    stream.randint.side_effect = list(rolls) + [5] * 50
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# DF-01: FightDefensivelyIntent applies -4 attack / +2 AC (no expertise)
# ---------------------------------------------------------------------------

def test_df01_fight_defensively_no_expertise():
    """Without Combat Expertise: attack penalty -4, AC bonus +2."""
    fighter = _entity("fighter", "party")
    dummy = _entity("dummy", "enemy")
    ws = _world({"fighter": fighter, "dummy": dummy})

    intent = FightDefensivelyIntent(actor_id="fighter")
    result = execute_turn(
        turn_ctx=_ctx("fighter"),
        world_state=ws,
        combat_intent=intent,
        rng=_rng(),
    )

    assert result.status == "ok"
    mods = result.world_state.entities["fighter"].get(EF.TEMPORARY_MODIFIERS, {})
    assert mods.get("fight_defensively_attack") == -4
    assert mods.get("fight_defensively_ac") == 2


# ---------------------------------------------------------------------------
# DF-02: FightDefensivelyIntent with Combat Expertise: -5 attack / +5 AC
# ---------------------------------------------------------------------------

def test_df02_fight_defensively_with_combat_expertise():
    """With Combat Expertise feat: attack penalty -5, AC bonus +5."""
    fighter = _entity("fighter", "party", feats=["Combat Expertise"])
    dummy = _entity("dummy", "enemy")
    ws = _world({"fighter": fighter, "dummy": dummy})

    intent = FightDefensivelyIntent(actor_id="fighter")
    result = execute_turn(
        turn_ctx=_ctx("fighter"),
        world_state=ws,
        combat_intent=intent,
        rng=_rng(),
    )

    mods = result.world_state.entities["fighter"].get(EF.TEMPORARY_MODIFIERS, {})
    assert mods.get("fight_defensively_attack") == -5
    assert mods.get("fight_defensively_ac") == 5


# ---------------------------------------------------------------------------
# DF-03: TotalDefenseIntent applies +4 dodge AC
# ---------------------------------------------------------------------------

def test_df03_total_defense_applies_plus4():
    """TotalDefenseIntent stores total_defense_ac = 4 in TEMPORARY_MODIFIERS."""
    fighter = _entity("fighter", "party")
    dummy = _entity("dummy", "enemy")
    ws = _world({"fighter": fighter, "dummy": dummy})

    intent = TotalDefenseIntent(actor_id="fighter")
    result = execute_turn(
        turn_ctx=_ctx("fighter"),
        world_state=ws,
        combat_intent=intent,
        rng=_rng(),
    )

    mods = result.world_state.entities["fighter"].get(EF.TEMPORARY_MODIFIERS, {})
    assert mods.get("total_defense_ac") == 4
    assert "fight_defensively_ac" not in mods


# ---------------------------------------------------------------------------
# DF-04: Both intents cost standard action
# ---------------------------------------------------------------------------

def test_df04_standard_action_cost():
    """FightDefensivelyIntent and TotalDefenseIntent both cost standard action."""
    fd = FightDefensivelyIntent(actor_id="x")
    td = TotalDefenseIntent(actor_id="x")
    assert get_action_type(fd) == "standard"
    assert get_action_type(td) == "standard"

    budget = ActionBudget(standard_used=True)
    assert check_economy(fd, budget) == "standard"
    assert check_economy(td, budget) == "standard"


# ---------------------------------------------------------------------------
# DF-05: fight_defensively_applied event emitted
# ---------------------------------------------------------------------------

def test_df05_fight_defensively_applied_event():
    """fight_defensively_applied event is emitted with penalty and bonus."""
    fighter = _entity("fighter", "party")
    dummy = _entity("dummy", "enemy")
    ws = _world({"fighter": fighter, "dummy": dummy})

    intent = FightDefensivelyIntent(actor_id="fighter")
    result = execute_turn(
        turn_ctx=_ctx("fighter"),
        world_state=ws,
        combat_intent=intent,
        rng=_rng(),
    )

    applied = [e for e in result.events if e.event_type == "fight_defensively_applied"]
    assert len(applied) == 1
    assert applied[0].payload["attack_penalty"] == -4
    assert applied[0].payload["ac_bonus"] == 2
    assert applied[0].payload["combat_expertise"] is False


# ---------------------------------------------------------------------------
# DF-06: total_defense_applied event emitted with bonus=4
# ---------------------------------------------------------------------------

def test_df06_total_defense_applied_event():
    """total_defense_applied event is emitted with ac_bonus=4."""
    fighter = _entity("fighter", "party")
    dummy = _entity("dummy", "enemy")
    ws = _world({"fighter": fighter, "dummy": dummy})

    intent = TotalDefenseIntent(actor_id="fighter")
    result = execute_turn(
        turn_ctx=_ctx("fighter"),
        world_state=ws,
        combat_intent=intent,
        rng=_rng(),
    )

    applied = [e for e in result.events if e.event_type == "total_defense_applied"]
    assert len(applied) == 1
    assert applied[0].payload["ac_bonus"] == 4


# ---------------------------------------------------------------------------
# DF-07: fight_defensively AC bonus reduces hit chance in attack
# ---------------------------------------------------------------------------

def test_df07_fight_defensively_ac_bonus_reduces_hit():
    """Attacker misses because target has fight_defensively AC bonus applied."""
    from aidm.schemas.attack import AttackIntent, Weapon
    from aidm.core.attack_resolver import resolve_attack

    # Defender has +2 fight defensively bonus — effective AC 22
    defender = _entity("orc", "enemy", ac=20, temporary_modifiers={"fight_defensively_ac": 2})
    attacker = _entity("fighter", "party", attack_bonus=8, bab=6)
    ws = _world({"fighter": attacker, "orc": defender})

    weapon = Weapon(
        damage_dice="1d8", damage_bonus=0, critical_range=20,
        critical_multiplier=2, grip="one-handed", damage_type="slashing",
        weapon_type="one-handed", range_increment=0, is_two_handed=False,
    )
    intent = AttackIntent(
        attacker_id="fighter", target_id="orc",
        attack_bonus=8, weapon=weapon, power_attack_penalty=0,
    )

    # d20=12 + 8 = 20, but effective AC is 22 → miss
    stream = mock.MagicMock()
    stream.randint.side_effect = [12] + [5] * 20  # attack roll 12 → total 20 < 22
    rng = mock.MagicMock()
    rng.stream.return_value = stream

    events = resolve_attack(intent, ws, rng, 0, 0.0)
    attack_event = next(e for e in events if e.event_type == "attack_roll")
    assert not attack_event.payload["hit"]
    assert attack_event.payload["fight_defensively_ac_bonus"] == 2


# ---------------------------------------------------------------------------
# DF-08: fight_defensively_expired emitted at start of next turn
# ---------------------------------------------------------------------------

def test_df08_fight_defensively_expired_at_turn_start():
    """fight_defensively_expired is emitted when actor with the modifier starts their turn."""
    fighter = _entity("fighter", "party",
                      temporary_modifiers={"fight_defensively_attack": -4, "fight_defensively_ac": 2})
    dummy = _entity("dummy", "enemy")
    ws = _world({"fighter": fighter, "dummy": dummy})

    # Start fighter's turn with an unrelated intent — expire block fires first
    intent = FightDefensivelyIntent(actor_id="fighter")  # any intent; expiry fires at turn-start
    result = execute_turn(
        turn_ctx=_ctx("fighter"),
        world_state=ws,
        combat_intent=intent,
        rng=_rng(),
    )

    expired = [e for e in result.events if e.event_type == "fight_defensively_expired"]
    assert len(expired) == 1
    assert expired[0].payload["entity_id"] == "fighter"

    # After expiry, the intent also re-applies fresh modifiers
    mods = result.world_state.entities["fighter"].get(EF.TEMPORARY_MODIFIERS, {})
    assert mods.get("fight_defensively_ac") == 2  # re-applied by intent


# ---------------------------------------------------------------------------
# DF-09: total_defense_expired emitted at start of next turn
# ---------------------------------------------------------------------------

def test_df09_total_defense_expired_at_turn_start():
    """total_defense_expired is emitted when actor with total_defense modifier starts their turn."""
    fighter = _entity("fighter", "party",
                      temporary_modifiers={"total_defense_ac": 4})
    dummy = _entity("dummy", "enemy")
    ws = _world({"fighter": fighter, "dummy": dummy})

    intent = TotalDefenseIntent(actor_id="fighter")
    result = execute_turn(
        turn_ctx=_ctx("fighter"),
        world_state=ws,
        combat_intent=intent,
        rng=_rng(),
    )

    expired = [e for e in result.events if e.event_type == "total_defense_expired"]
    assert len(expired) == 1
    assert expired[0].payload["entity_id"] == "fighter"


# ---------------------------------------------------------------------------
# DF-10: parse_intent roundtrips
# ---------------------------------------------------------------------------

def test_df10_parse_intent_roundtrip():
    """FightDefensivelyIntent and TotalDefenseIntent roundtrip through parse_intent."""
    fd = FightDefensivelyIntent(actor_id="fighter")
    td = TotalDefenseIntent(actor_id="fighter")

    fd2 = parse_intent(fd.to_dict())
    td2 = parse_intent(td.to_dict())

    assert isinstance(fd2, FightDefensivelyIntent)
    assert fd2.actor_id == "fighter"

    assert isinstance(td2, TotalDefenseIntent)
    assert td2.actor_id == "fighter"
