"""Gate ENGINE-COUP-DE-GRACE — WO-ENGINE-COUP-DE-GRACE-001: Coup de Grâce.

Tests:
CDG-01: CDG against DYING target — auto-hit, crit damage, no attack_roll event
CDG-02: CDG against HELPLESS target — auto-hit, crit damage, fort save pass -> no entity_defeated
CDG-03: CDG against DISABLED target — validation failure (target_not_helpless)
CDG-04: CDG against conscious target — validation failure (target_not_helpless)
CDG-05: Fort save fails — entity_defeated with cause "coup_de_grace"
CDG-06: Fort save passes — target survives, no entity_defeated
CDG-07: cdg_fort_save event always emitted
CDG-08: CDG uses full_round action — ACTION_DENIED if already acted
CDG-09: ×3 crit weapon deals ×3 damage
CDG-10: CDG against PINNED target — valid target
"""

import unittest.mock as mock
from typing import Any, Dict, List

import pytest

from aidm.core.play_loop import TurnContext, execute_turn
from aidm.core.action_economy import ActionBudget
from aidm.core.state import WorldState
from aidm.schemas.intents import CoupDeGraceIntent
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _weapon(
    damage_dice: str = "1d6",
    damage_bonus: int = 0,
    crit_multiplier: int = 2,
    damage_type: str = "slashing",
    grip: str = "one-handed",
) -> dict:
    return {
        "damage_dice": damage_dice,
        "damage_bonus": damage_bonus,
        "crit_multiplier": crit_multiplier,
        "damage_type": damage_type,
        "grip": grip,
    }


def _entity(
    eid: str,
    team: str,
    hp: int,
    hp_max: int = 30,
    ac: int = 5,
    dying: bool = False,
    defeated: bool = False,
    disabled: bool = False,
    conditions: dict = None,
    save_fort: int = 0,
    str_mod: int = 0,
    crit_immune: bool = False,
) -> Dict[str, Any]:
    e = {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
        EF.AC: ac,
        EF.SAVE_FORT: save_fort,
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: 0,
        EF.ATTACK_BONUS: 5,
        EF.BAB: 5,
        "bab": 5,
        EF.DEFEATED: defeated,
        EF.DYING: dying,
        EF.STABLE: False,
        EF.DISABLED: disabled,
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.FEATS: [],
    }
    if crit_immune:
        e[EF.CRIT_IMMUNE] = True
    return e


def _world(attacker: dict, target: dict, attacker_id: str = "attacker",
           target_id: str = "target") -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={attacker_id: attacker, target_id: target},
        active_combat={"initiative_order": [attacker_id, target_id]},
    )


def _ctx(actor_id: str = "attacker", team: str = "party") -> TurnContext:
    return TurnContext(turn_index=0, actor_id=actor_id, actor_team=team)


def _rng_fixed(damage_roll: int, fort_roll: int):
    """RNG that returns damage_roll first (XdY), then fort_roll (d20)."""
    stream = mock.MagicMock()
    stream.randint.side_effect = [damage_roll, fort_roll] + [fort_roll] * 10
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# CDG-01: CDG against DYING target — auto-hit, crit damage, no attack_roll
# ---------------------------------------------------------------------------

def test_cdg01_dying_target_auto_crit():
    """CDG against DYING target: cdg_damage_roll present, no attack_roll, damage_total correct."""
    # Attacker STR_MOD=2, weapon 1d6 damage_bonus=0, crit_multiplier=2, grip=one-handed
    # RNG: damage roll=4 -> base=(4+0+2)=6, damage_total=6*2=12
    # Fort DC=10+12=22. Fort roll=15, fort_base=0 -> total=15 < 22 -> fails.
    # But we seed fort_roll high enough to pass for CDG-01 to focus on damage.
    attacker = _entity("attacker", "party", hp=20, str_mod=2)
    target = _entity("target", "monsters", hp=5, hp_max=30, dying=True)
    target[EF.HP_CURRENT] = -3  # Dying: HP between -1 and -9
    ws = _world(attacker, target)

    intent = CoupDeGraceIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=_weapon("1d6", damage_bonus=0, crit_multiplier=2, grip="one-handed"),
    )
    # damage=4, str_mod=2 -> base=6, *2=12. Fort DC=22. Fort roll=20 -> 20>=22 fails.
    # Let fort roll pass: fort_roll=22 won't work (d20 max=20).
    # Fort will fail here but that's OK — CDG-01 only checks damage fields.
    rng = _rng_fixed(damage_roll=4, fort_roll=15)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)

    events = result.events

    # No attack_roll event
    atk_events = [e for e in events if e.event_type == "attack_roll"]
    assert len(atk_events) == 0, "CDG emits no attack_roll event (auto-hit)"

    # cdg_damage_roll event present
    cdg_ev = next((e for e in events if e.event_type == "cdg_damage_roll"), None)
    assert cdg_ev is not None
    assert cdg_ev.payload["auto_hit"] is True
    assert cdg_ev.payload["auto_crit"] is True
    # base=(4+0+2)=6, damage_total=6*2=12
    assert cdg_ev.payload["base_damage"] == 6
    assert cdg_ev.payload["damage_total"] == 12
    assert cdg_ev.payload["crit_multiplier"] == 2


# ---------------------------------------------------------------------------
# CDG-02: CDG against HELPLESS target — fort save passes -> no entity_defeated
# ---------------------------------------------------------------------------

def test_cdg02_helpless_target_fort_pass():
    """CDG against HELPLESS target: fort save passes -> no entity_defeated."""
    # damage=3, str=2 -> base=5, *2=10. Fort DC=20. Fort roll=18, fort_base=10 -> 28>=20 passes.
    attacker = _entity("attacker", "party", hp=20, str_mod=2)
    target = _entity("target", "monsters", hp=5, save_fort=10, conditions={"helpless": {}})
    ws = _world(attacker, target)

    intent = CoupDeGraceIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=_weapon("1d6", damage_bonus=0, crit_multiplier=2, grip="one-handed"),
    )
    rng = _rng_fixed(damage_roll=3, fort_roll=18)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)

    events = result.events
    cdg_ev = next((e for e in events if e.event_type == "cdg_damage_roll"), None)
    assert cdg_ev is not None
    # base=(3+0+2)=5, *2=10
    assert cdg_ev.payload["damage_total"] == 10

    fort_ev = next((e for e in events if e.event_type == "cdg_fort_save"), None)
    assert fort_ev is not None
    assert fort_ev.payload["passed"] is True

    defeated_events = [e for e in events if e.event_type == "entity_defeated"]
    assert len(defeated_events) == 0, "Fort save passed: no entity_defeated"


# ---------------------------------------------------------------------------
# CDG-03: CDG against DISABLED target — validation failure
# ---------------------------------------------------------------------------

def test_cdg03_disabled_target_validation_failure():
    """CDG against DISABLED target (not dying/helpless) -> intent_validation_failed."""
    attacker = _entity("attacker", "party", hp=20)
    target = _entity("target", "monsters", hp=0, disabled=True)  # Only DISABLED, not dying
    ws = _world(attacker, target)

    intent = CoupDeGraceIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=_weapon(),
    )
    rng = _rng_fixed(5, 15)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)

    assert result.status == "invalid_intent"
    val_ev = next((e for e in result.events if e.event_type == "intent_validation_failed"), None)
    assert val_ev is not None
    assert val_ev.payload["reason"] == "target_not_helpless"

    cdg_events = [e for e in result.events if e.event_type == "cdg_damage_roll"]
    assert len(cdg_events) == 0


# ---------------------------------------------------------------------------
# CDG-04: CDG against conscious target — validation failure
# ---------------------------------------------------------------------------

def test_cdg04_conscious_target_validation_failure():
    """CDG against fully conscious target -> intent_validation_failed."""
    attacker = _entity("attacker", "party", hp=20)
    target = _entity("target", "monsters", hp=15)  # healthy
    ws = _world(attacker, target)

    intent = CoupDeGraceIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=_weapon(),
    )
    rng = _rng_fixed(5, 15)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)

    assert result.status == "invalid_intent"
    val_ev = next((e for e in result.events if e.event_type == "intent_validation_failed"), None)
    assert val_ev is not None
    assert val_ev.payload["reason"] == "target_not_helpless"


# ---------------------------------------------------------------------------
# CDG-05: Fort save fails — entity_defeated with cause "coup_de_grace"
# ---------------------------------------------------------------------------

def test_cdg05_fort_fail_entity_defeated():
    """Fort save fails -> entity_defeated with cause='coup_de_grace', HP=-10."""
    # Target is HELPLESS with HP=5. CDG damage=5, str=0, crit=2 -> base=5, *2=10.
    # HP 5 - 10 = -5 (dying range). resolve_hp_transition emits entity_dying (not defeated).
    # Fort DC=10+10=20. Fort roll=1 -> 1+0=1 < 20 fails.
    # CDG function then emits entity_defeated with cause='coup_de_grace'.
    attacker = _entity("attacker", "party", hp=20, str_mod=0)
    target = _entity("target", "monsters", hp=5, save_fort=0, conditions={"helpless": {}})
    ws = _world(attacker, target)

    intent = CoupDeGraceIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=_weapon("1d6", damage_bonus=0, crit_multiplier=2, grip="one-handed"),
    )
    rng = _rng_fixed(damage_roll=5, fort_roll=1)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)

    events = result.events
    defeated_events = [e for e in events if e.event_type == "entity_defeated"]
    assert len(defeated_events) > 0

    # The CDG-specific entity_defeated should have cause='coup_de_grace'
    cdg_defeated = next((e for e in defeated_events if e.payload.get("cause") == "coup_de_grace"), None)
    assert cdg_defeated is not None, f"No entity_defeated with cause=coup_de_grace. Events: {[e.event_type for e in events]}"

    # Entity HP in final world_state == -10, DEFEATED=True
    final_target = result.world_state.entities.get("target", {})
    assert final_target.get(EF.DEFEATED, False) is True
    assert final_target.get(EF.HP_CURRENT, 0) == -10


# ---------------------------------------------------------------------------
# CDG-06: Fort save passes — target survives, no entity_defeated
# ---------------------------------------------------------------------------

def test_cdg06_fort_pass_target_survives():
    """Fort save passes -> no entity_defeated, target not defeated."""
    # damage=1, str=0, crit=2 -> base=1, *2=2. Fort DC=12. Fort roll=10, fort_base=10 -> 20>=12 passes.
    attacker = _entity("attacker", "party", hp=20, str_mod=0)
    target = _entity("target", "monsters", hp=5, dying=True, save_fort=10)
    target[EF.HP_CURRENT] = -1
    ws = _world(attacker, target)

    intent = CoupDeGraceIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=_weapon("1d4", damage_bonus=0, crit_multiplier=2, grip="one-handed"),
    )
    rng = _rng_fixed(damage_roll=1, fort_roll=10)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)

    events = result.events
    fort_ev = next((e for e in events if e.event_type == "cdg_fort_save"), None)
    assert fort_ev is not None
    assert fort_ev.payload["passed"] is True

    defeated_events = [e for e in events if e.event_type == "entity_defeated"]
    assert len(defeated_events) == 0, "Fort passed: no entity_defeated"

    final_target = result.world_state.entities.get("target", {})
    assert final_target.get(EF.DEFEATED, False) is False


# ---------------------------------------------------------------------------
# CDG-07: cdg_fort_save event always emitted
# ---------------------------------------------------------------------------

def test_cdg07_fort_save_event_always_emitted():
    """cdg_fort_save event is always emitted for any valid CDG."""
    attacker = _entity("attacker", "party", hp=20)
    target = _entity("target", "monsters", hp=5, dying=True)
    target[EF.HP_CURRENT] = -1
    ws = _world(attacker, target)

    intent = CoupDeGraceIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=_weapon(),
    )
    rng = _rng_fixed(damage_roll=3, fort_roll=15)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)

    fort_events = [e for e in result.events if e.event_type == "cdg_fort_save"]
    assert len(fort_events) == 1

    payload = fort_events[0].payload
    assert "fort_roll" in payload
    assert "dc" in payload
    assert "passed" in payload


# ---------------------------------------------------------------------------
# CDG-08: CDG uses full_round action — ACTION_DENIED if already acted
# ---------------------------------------------------------------------------

def test_cdg08_action_denied_if_already_acted():
    """CDG uses full_round slot — denied if attacker already used standard action."""
    attacker = _entity("attacker", "party", hp=20)
    target = _entity("target", "monsters", hp=5, dying=True)
    target[EF.HP_CURRENT] = -1

    # Set action_budget with standard_used=True for this actor
    budget = ActionBudget.fresh()
    budget.consume("standard")

    ws = WorldState(
        ruleset_version="3.5e",
        entities={"attacker": attacker, "target": target},
        active_combat={
            "initiative_order": ["attacker", "target"],
            "action_budget": budget.to_dict(),
            "action_budget_actor": "attacker",
        },
    )

    intent = CoupDeGraceIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=_weapon(),
    )
    rng = _rng_fixed(3, 15)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)

    assert result.status == "action_denied"
    action_denied = [e for e in result.events if e.event_type in ("action_denied", "ACTION_DENIED")]
    assert len(action_denied) > 0

    cdg_events = [e for e in result.events if e.event_type == "cdg_damage_roll"]
    assert len(cdg_events) == 0


# ---------------------------------------------------------------------------
# CDG-09: ×3 crit weapon deals ×3 damage
# ---------------------------------------------------------------------------

def test_cdg09_triple_crit_multiplier():
    """Weapon with crit_multiplier=3 deals ×3 damage on CDG."""
    # str=0, weapon 1d8 damage_bonus=2, crit=3. Roll=4. base=(4+2+0)=6, damage_total=6*3=18.
    attacker = _entity("attacker", "party", hp=20, str_mod=0)
    target = _entity("target", "monsters", hp=5, dying=True, save_fort=99)
    target[EF.HP_CURRENT] = -1
    ws = _world(attacker, target)

    intent = CoupDeGraceIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=_weapon("1d8", damage_bonus=2, crit_multiplier=3, grip="one-handed"),
    )
    rng = _rng_fixed(damage_roll=4, fort_roll=20)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)

    cdg_ev = next((e for e in result.events if e.event_type == "cdg_damage_roll"), None)
    assert cdg_ev is not None
    assert cdg_ev.payload["crit_multiplier"] == 3
    # base=(4+2+0)=6, *3=18
    assert cdg_ev.payload["base_damage"] == 6
    assert cdg_ev.payload["damage_total"] == 18

    hp_ev = next((e for e in result.events if e.event_type == "hp_changed"), None)
    assert hp_ev is not None
    # final_damage = 18 (no DR), delta = -18
    assert hp_ev.payload["delta"] == -18


# ---------------------------------------------------------------------------
# CDG-10: CDG against PINNED target — valid target (PINNED is helpless)
# ---------------------------------------------------------------------------

def test_cdg10_pinned_target_is_valid():
    """PINNED target is valid for CDG (PHB p.153 helpless-family)."""
    attacker = _entity("attacker", "party", hp=20)
    target = _entity("target", "monsters", hp=8, conditions={"pinned": {}})
    ws = _world(attacker, target)

    intent = CoupDeGraceIntent(
        attacker_id="attacker",
        target_id="target",
        weapon=_weapon(),
    )
    rng = _rng_fixed(damage_roll=3, fort_roll=15)
    result = execute_turn(ws, _ctx(), combat_intent=intent, rng=rng)

    # No validation failure
    val_events = [e for e in result.events if e.event_type == "intent_validation_failed"]
    assert len(val_events) == 0

    cdg_ev = next((e for e in result.events if e.event_type == "cdg_damage_roll"), None)
    assert cdg_ev is not None
    assert cdg_ev.payload["auto_hit"] is True
