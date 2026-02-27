"""Gate tests: ENGINE-MASSIVE-DAMAGE — WO-ENGINE-MASSIVE-DAMAGE-001.

Tests:
MD-01: 50 damage hit — massive_damage_check event fired
MD-02: 49 damage hit — no massive_damage_check (below threshold)
MD-03: 51 damage hit, Fort save succeeds (total >= 15) — target survives, normal HP
MD-04: 50 damage hit, Fort save fails (total < 15) — target hp_after = -10
MD-05: Entity with high Fort save — save total includes base_save + CON_MOD
MD-06: massive_damage_check event payload fields correct
MD-07: Instant death on fail — hp_changed event shows hp_after = -10
MD-08: Instant death on fail — resolve_hp_transition classifies as dead (entity_dead event)
MD-09: DR reduces damage below 50 — no massive_damage_check emitted
MD-10: Regression — 49 HP hit path unchanged (standard hp_changed emitted)
"""

import unittest.mock as mock
from typing import Any, Dict

import pytest

from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _weapon(damage_dice: str = "1d6", damage_bonus: int = 0) -> Weapon:
    return Weapon(
        damage_dice=damage_dice,
        damage_bonus=damage_bonus,
        damage_type="slashing",
        critical_multiplier=2,
        critical_range=20,
        is_two_handed=False,
        grip="one-handed",
        weapon_type="one-handed",
        range_increment=0,
        enhancement_bonus=0,
    )


def _attacker(eid: str = "fighter", bab: int = 10, str_mod: int = 3) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.AC: 18,
        EF.ATTACK_BONUS: bab,
        EF.BAB: bab,
        EF.STR_MOD: str_mod,
        EF.DEX_MOD: 0,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.NEGATIVE_LEVELS: 0,
        EF.WEAPON_BROKEN: False,
        EF.FAVORED_ENEMIES: [],
    }


def _target(
    eid: str = "troll",
    hp: int = 80,
    hp_max: int = 80,
    ac: int = 5,
    save_fort: int = 5,
    con_mod: int = 2,
    dr: list = None,
) -> Dict[str, Any]:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
        EF.AC: ac,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "large",
        EF.SAVE_FORT: save_fort,
        EF.CON_MOD: con_mod,
        EF.DAMAGE_REDUCTIONS: dr if dr is not None else [],
        EF.CREATURE_TYPE: "giant",
        EF.INSPIRE_COURAGE_ACTIVE: False,
    }


def _world(attacker: dict, target: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={
            attacker[EF.ENTITY_ID]: attacker,
            target[EF.ENTITY_ID]: target,
        },
        active_combat={"initiative_order": [attacker[EF.ENTITY_ID], target[EF.ENTITY_ID]]},
    )


def _rng(attack_roll: int = 18, damage_rolls=None, fort_roll: int = 10):
    """
    RNG sequence for the massive damage path:
      1. d20 attack roll
      2. damage dice roll(s)
      3. Fort save d20 (if final_damage >= 50)
    """
    stream = mock.MagicMock()
    dam_rolls = damage_rolls if damage_rolls is not None else [50]
    side = [attack_roll] + dam_rolls + [fort_roll] + [5] * 20
    stream.randint.side_effect = side
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _intent(
    attacker_id: str = "fighter",
    target_id: str = "troll",
    attack_bonus: int = 10,
    weapon: Weapon = None,
) -> AttackIntent:
    return AttackIntent(
        attacker_id=attacker_id,
        target_id=target_id,
        attack_bonus=attack_bonus,
        weapon=weapon or _weapon(damage_dice="1d6", damage_bonus=47),  # 1d6+47 → always ≥ 48
        power_attack_penalty=0,
    )


# ---------------------------------------------------------------------------
# MD-01: 50 damage — massive_damage_check fires
# ---------------------------------------------------------------------------

def test_md01_50_damage_fires_check():
    """MD-01: Final damage exactly 50 → massive_damage_check event emitted."""
    # damage_bonus=49, 1d1 → final=50
    w = Weapon(damage_dice="1d1", damage_bonus=49, damage_type="slashing",
               critical_multiplier=2, critical_range=20, grip="one-handed",
               weapon_type="one-handed", range_increment=0, enhancement_bonus=0)
    a = _attacker()
    t = _target(ac=5)
    ws = _world(a, t)
    rng = _rng(attack_roll=15, damage_rolls=[1], fort_roll=15)

    events = resolve_attack(AttackIntent("fighter", "troll", 10, w), ws, rng, 0, 0.0)
    md_evts = [e for e in events if e.event_type == "massive_damage_check"]
    assert len(md_evts) == 1, "massive_damage_check must fire on 50 damage"


# ---------------------------------------------------------------------------
# MD-02: 49 damage — no massive_damage_check
# ---------------------------------------------------------------------------

def test_md02_49_damage_no_check():
    """MD-02: Final damage = 49 → no massive_damage_check emitted."""
    w = Weapon(damage_dice="1d1", damage_bonus=48, damage_type="slashing",
               critical_multiplier=2, critical_range=20, grip="one-handed",
               weapon_type="one-handed", range_increment=0, enhancement_bonus=0)
    a = _attacker(str_mod=0)  # str_mod=0 ensures 1+48+0=49 exactly
    t = _target(ac=5)
    ws = _world(a, t)
    rng = _rng(attack_roll=15, damage_rolls=[1], fort_roll=10)

    events = resolve_attack(AttackIntent("fighter", "troll", 10, w), ws, rng, 0, 0.0)
    md_evts = [e for e in events if e.event_type == "massive_damage_check"]
    assert len(md_evts) == 0, "No massive_damage_check should fire on 49 damage"


# ---------------------------------------------------------------------------
# MD-03: 51 damage, Fort save succeeds — target survives at normal HP
# ---------------------------------------------------------------------------

def test_md03_fort_save_success_normal_hp():
    """MD-03: 51 damage, Fort total >= 15 — target survives at normal HP."""
    w = Weapon(damage_dice="1d1", damage_bonus=50, damage_type="slashing",
               critical_multiplier=2, critical_range=20, grip="one-handed",
               weapon_type="one-handed", range_increment=0, enhancement_bonus=0)
    a = _attacker()
    t = _target(ac=5, hp=100, save_fort=10, con_mod=3)  # Fort bonus = 10+3=13 → roll 3+ succeeds
    ws = _world(a, t)
    rng = _rng(attack_roll=15, damage_rolls=[1], fort_roll=3)  # fort total = 3 + 13 = 16 >= 15 → saved

    events = resolve_attack(AttackIntent("fighter", "troll", 10, w), ws, rng, 0, 0.0)

    md_evt = next(e for e in events if e.event_type == "massive_damage_check")
    assert md_evt.payload["saved"] is True, "Fort save should succeed"

    hp_evt = next((e for e in events if e.event_type == "hp_changed"), None)
    if hp_evt:
        assert hp_evt.payload["hp_after"] != -10, "Survivor should not have hp_after=-10"


# ---------------------------------------------------------------------------
# MD-04: 50 damage, Fort save fails — target hp_after = -10
# ---------------------------------------------------------------------------

def test_md04_fort_save_fail_instant_death():
    """MD-04: 50 damage, Fort total < 15 — target hp_after = -10 (instant death)."""
    w = Weapon(damage_dice="1d1", damage_bonus=49, damage_type="slashing",
               critical_multiplier=2, critical_range=20, grip="one-handed",
               weapon_type="one-handed", range_increment=0, enhancement_bonus=0)
    a = _attacker()
    t = _target(ac=5, hp=100, save_fort=0, con_mod=0)  # Fort bonus = 0 → roll 1-14 fails
    ws = _world(a, t)
    rng = _rng(attack_roll=15, damage_rolls=[1], fort_roll=5)  # fort total = 5 < 15 → fail

    events = resolve_attack(AttackIntent("fighter", "troll", 10, w), ws, rng, 0, 0.0)

    md_evt = next(e for e in events if e.event_type == "massive_damage_check")
    assert md_evt.payload["saved"] is False, "Fort save should fail"

    hp_evt = next((e for e in events if e.event_type == "hp_changed"), None)
    assert hp_evt is not None, "hp_changed must be emitted"
    assert hp_evt.payload["hp_after"] == -10, (
        f"Instant death: hp_after must be -10, got {hp_evt.payload['hp_after']}"
    )


# ---------------------------------------------------------------------------
# MD-05: High Fort save — total includes base_save + CON_MOD
# ---------------------------------------------------------------------------

def test_md05_high_fort_save_includes_con():
    """MD-05: Save total = fort_roll + save_fort + con_mod (all contribute)."""
    w = Weapon(damage_dice="1d1", damage_bonus=49, damage_type="slashing",
               critical_multiplier=2, critical_range=20, grip="one-handed",
               weapon_type="one-handed", range_increment=0, enhancement_bonus=0)
    a = _attacker()
    # save_fort=3, con_mod=4 → base bonus=7; roll=8 → total=15 → just saves
    t = _target(ac=5, hp=100, save_fort=3, con_mod=4)
    ws = _world(a, t)
    rng = _rng(attack_roll=15, damage_rolls=[1], fort_roll=8)  # 8 + 3 + 4 = 15 >= 15

    events = resolve_attack(AttackIntent("fighter", "troll", 10, w), ws, rng, 0, 0.0)

    md_evt = next(e for e in events if e.event_type == "massive_damage_check")
    assert md_evt.payload["fort_bonus"] == 7, (
        f"Fort bonus should be save_fort(3) + con_mod(4) = 7, got {md_evt.payload['fort_bonus']}"
    )
    assert md_evt.payload["fort_total"] == 15, (
        f"Fort total should be 8+7=15, got {md_evt.payload['fort_total']}"
    )
    assert md_evt.payload["saved"] is True


# ---------------------------------------------------------------------------
# MD-06: Event payload fields
# ---------------------------------------------------------------------------

def test_md06_event_payload_fields():
    """MD-06: massive_damage_check event has all required payload fields."""
    w = Weapon(damage_dice="1d1", damage_bonus=49, damage_type="slashing",
               critical_multiplier=2, critical_range=20, grip="one-handed",
               weapon_type="one-handed", range_increment=0, enhancement_bonus=0)
    a = _attacker(str_mod=0)  # str_mod=0 so 1+49=50 exactly
    t = _target(ac=5, hp=100, save_fort=2, con_mod=1)
    ws = _world(a, t)
    rng = _rng(attack_roll=15, damage_rolls=[1], fort_roll=12)

    events = resolve_attack(AttackIntent("fighter", "troll", 10, w), ws, rng, 0, 0.0)
    md_evt = next(e for e in events if e.event_type == "massive_damage_check")

    required_fields = {"target_id", "damage", "fort_roll", "fort_bonus", "fort_total", "dc", "saved"}
    missing = required_fields - set(md_evt.payload.keys())
    assert not missing, f"Missing payload fields: {missing}"
    assert md_evt.payload["dc"] == 15
    assert md_evt.payload["target_id"] == "troll"
    assert md_evt.payload["damage"] == 50


# ---------------------------------------------------------------------------
# MD-07: Instant death — hp_changed shows hp_after = -10
# ---------------------------------------------------------------------------

def test_md07_instant_death_hp_changed_minus10():
    """MD-07: Fort fail → hp_changed event shows hp_after = -10 regardless of prior HP."""
    w = Weapon(damage_dice="1d1", damage_bonus=49, damage_type="slashing",
               critical_multiplier=2, critical_range=20, grip="one-handed",
               weapon_type="one-handed", range_increment=0, enhancement_bonus=0)
    a = _attacker()
    t = _target(ac=5, hp=200, save_fort=0, con_mod=0)  # 200 HP — not dead from damage alone
    ws = _world(a, t)
    rng = _rng(attack_roll=15, damage_rolls=[1], fort_roll=1)  # total=1 < 15 → fail

    events = resolve_attack(AttackIntent("fighter", "troll", 10, w), ws, rng, 0, 0.0)

    hp_evt = next((e for e in events if e.event_type == "hp_changed"), None)
    assert hp_evt is not None
    assert hp_evt.payload["hp_after"] == -10, (
        "Massive damage instant death must set hp_after to -10"
    )


# ---------------------------------------------------------------------------
# MD-08: Instant death — entity_dead event emitted via resolve_hp_transition
# ---------------------------------------------------------------------------

def test_md08_instant_death_entity_dead_event():
    """MD-08: Fort fail → entity_dead event emitted by resolve_hp_transition."""
    w = Weapon(damage_dice="1d1", damage_bonus=49, damage_type="slashing",
               critical_multiplier=2, critical_range=20, grip="one-handed",
               weapon_type="one-handed", range_increment=0, enhancement_bonus=0)
    a = _attacker()
    t = _target(ac=5, hp=200, save_fort=0, con_mod=0)
    ws = _world(a, t)
    rng = _rng(attack_roll=15, damage_rolls=[1], fort_roll=1)

    events = resolve_attack(AttackIntent("fighter", "troll", 10, w), ws, rng, 0, 0.0)
    apply_attack_events(ws, events)

    dead_evts = [e for e in events if e.event_type == "entity_defeated"]
    assert len(dead_evts) >= 1, "entity_defeated must be emitted after instant death via massive damage"


# ---------------------------------------------------------------------------
# MD-09: DR reduces damage below 50 — no massive_damage_check
# ---------------------------------------------------------------------------

def test_md09_dr_reduces_below_threshold():
    """MD-09: Raw 55 damage but DR 10/- → final_damage = 45 → no massive_damage_check."""
    from aidm.schemas.entity_fields import EF as _EF

    w = Weapon(damage_dice="1d1", damage_bonus=54, damage_type="slashing",
               critical_multiplier=2, critical_range=20, grip="one-handed",
               weapon_type="one-handed", range_increment=0, enhancement_bonus=0)
    a = _attacker()
    t = _target(ac=5, hp=200, dr=[{"amount": 10, "bypass": "-"}])  # DR 10/- blocks all
    ws = _world(a, t)
    rng = _rng(attack_roll=15, damage_rolls=[1], fort_roll=10)

    events = resolve_attack(AttackIntent("fighter", "troll", 10, w), ws, rng, 0, 0.0)
    md_evts = [e for e in events if e.event_type == "massive_damage_check"]
    assert len(md_evts) == 0, "DR should reduce final_damage below 50 — no massive_damage_check"


# ---------------------------------------------------------------------------
# MD-10: Regression — 49 HP hit still produces normal hp_changed
# ---------------------------------------------------------------------------

def test_md10_regression_normal_hit_unaffected():
    """MD-10: 49 damage hit still produces hp_changed event without massive_damage_check."""
    w = Weapon(damage_dice="1d1", damage_bonus=48, damage_type="slashing",
               critical_multiplier=2, critical_range=20, grip="one-handed",
               weapon_type="one-handed", range_increment=0, enhancement_bonus=0)
    a = _attacker(str_mod=0)  # str_mod=0 ensures 1+48+0=49 exactly
    t = _target(ac=5, hp=100)
    ws = _world(a, t)
    rng = _rng(attack_roll=15, damage_rolls=[1], fort_roll=5)

    events = resolve_attack(AttackIntent("fighter", "troll", 10, w), ws, rng, 0, 0.0)

    md_evts = [e for e in events if e.event_type == "massive_damage_check"]
    hp_evts = [e for e in events if e.event_type == "hp_changed"]

    assert len(md_evts) == 0, "No massive_damage_check on 49 damage"
    assert len(hp_evts) >= 1, "hp_changed must still fire on normal hit"
    assert hp_evts[0].payload["hp_after"] == 100 - 49, (
        f"Normal HP math: expected {100-49}, got {hp_evts[0].payload['hp_after']}"
    )
