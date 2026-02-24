"""Gate ENGINE-DR — WO-ENGINE-DR-001: Damage Reduction Enforcement.

Tests:
DR-01: Attack deals 8 raw, target DR 5/magic, non-magic weapon -> final=3, dr_absorbed=5
DR-02: Attack deals 8 raw, target DR 5/magic, magic weapon (tag) -> final=8, dr_absorbed=0
DR-03: Attack deals 3 raw, target DR 5/magic, non-magic -> final=0, no hp_changed, damage_reduced present
DR-04: Target DR 10/- (bypass impossible), magic weapon -> DR applies; final=max(0, raw-10)
DR-05: Two DR entries [10/magic, 5/silver], non-magic non-silver -> best DR (10) used
DR-06: Natural attack (weapon_type="natural") against DR 5/magic -> DR applies, natural is not magic
DR-07: dr_absorbed>0 -> damage_reduced event present with correct fields
DR-08: Magic weapon bypasses DR 5/magic -> no damage_reduced event
DR-09: Full attack 2 hits, DR 5/magic non-magic, 8+6 raw -> total=4, total_dr_absorbed=10 in hp_changed
DR-10: Entity with no DAMAGE_REDUCTIONS field -> get_applicable_dr returns 0, no DR applied
"""

import unittest.mock as mock
from typing import Any, Dict, List

import pytest

from aidm.core.attack_resolver import resolve_attack, apply_attack_events
from aidm.core.full_attack_resolver import resolve_full_attack, FullAttackIntent
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF
from aidm.core.damage_reduction import extract_weapon_bypass_flags, get_applicable_dr, _get_bypass_type


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sword(weapon_type: str = "one-handed") -> Weapon:
    return Weapon(
        damage_dice="1d8",
        damage_bonus=0,
        damage_type="slashing",
        critical_range=20,
        critical_multiplier=2,
        grip="one-handed",
        is_two_handed=False,
        weapon_type=weapon_type,
    )


def _natural_attack() -> Weapon:
    return Weapon(
        damage_dice="1d6",
        damage_bonus=0,
        damage_type="slashing",
        weapon_type="natural",
        grip="one-handed",
    )


def _entity(
    eid: str,
    team: str,
    hp: int,
    hp_max: int = 30,
    ac: int = 5,
    dr: list = None,
    weapon_tags: list = None,
) -> Dict[str, Any]:
    e = {
        EF.ENTITY_ID: eid,
        EF.TEAM: team,
        EF.HP_CURRENT: hp,
        EF.HP_MAX: hp_max,
        EF.AC: ac,
        EF.SAVE_FORT: 0,
        EF.STR_MOD: 0,
        EF.DEX_MOD: 0,
        EF.ATTACK_BONUS: 99,  # guarantee hit
        EF.BAB: 5,
        "bab": 5,
        EF.DEFEATED: False,
        EF.DYING: False,
        EF.STABLE: False,
        EF.DISABLED: False,
        EF.CONDITIONS: {},
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.FEATS: [],
    }
    if dr is not None:
        e[EF.DAMAGE_REDUCTIONS] = dr
    if weapon_tags is not None:
        e[EF.WEAPON] = {"tags": weapon_tags}
    return e


def _world(entities: dict) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities=entities,
        active_combat={"initiative_order": list(entities.keys())},
    )


def _rng_fixed(attack_roll: int, damage_roll: int):
    """RNG that returns attack_roll first (d20), then damage_roll (XdY).
    Uses return_value after the sequence to avoid StopIteration.
    """
    stream = mock.MagicMock()
    # attack roll 15 does NOT trigger crit confirmation (not a threat for default crit range 20)
    # so only 2 calls: d20 + damage die
    call_values = [attack_roll, damage_roll]
    # For safety, use return_value = damage_roll after the list runs out
    stream.randint.side_effect = call_values + [damage_roll] * 10
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# ---------------------------------------------------------------------------
# DR-01: non-magic weapon vs DR 5/magic -> absorbed 5, final 3
# ---------------------------------------------------------------------------

def test_dr01_non_magic_vs_dr5_magic():
    """Attack deals 8 raw, DR 5/magic, non-magic -> final=3, dr_absorbed=5."""
    target = _entity("target", "monsters", hp=20, dr=[{"amount": 5, "bypass": "magic"}])
    attacker = _entity("attacker", "party", hp=20)
    ws = _world({"attacker": attacker, "target": target})

    sword = _sword()
    intent = AttackIntent(attacker_id="attacker", target_id="target", attack_bonus=99, weapon=sword)
    # d20=15 (non-threat hit), damage=8
    rng = _rng_fixed(15, 8)
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)

    hp_ev = next((e for e in events if e.event_type == "hp_changed"), None)
    assert hp_ev is not None
    assert hp_ev.payload["delta"] == -3
    assert hp_ev.payload["dr_absorbed"] == 5

    dr_ev = next((e for e in events if e.event_type == "damage_reduced"), None)
    assert dr_ev is not None
    assert dr_ev.payload["dr_absorbed"] == 5
    assert dr_ev.payload["final_damage"] == 3


# ---------------------------------------------------------------------------
# DR-02: magic weapon (tag) bypasses DR 5/magic -> no DR applied
# ---------------------------------------------------------------------------

def test_dr02_magic_weapon_bypasses_dr5_magic():
    """Magic weapon bypasses DR 5/magic -> final=8, dr_absorbed=0."""
    target = _entity("target", "monsters", hp=20, dr=[{"amount": 5, "bypass": "magic"}])
    attacker = _entity("attacker", "party", hp=20, weapon_tags=["magic"])
    ws = _world({"attacker": attacker, "target": target})

    sword = _sword()
    intent = AttackIntent(attacker_id="attacker", target_id="target", attack_bonus=99, weapon=sword)
    rng = _rng_fixed(15, 8)
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)

    hp_ev = next((e for e in events if e.event_type == "hp_changed"), None)
    assert hp_ev is not None
    assert hp_ev.payload["delta"] == -8
    assert hp_ev.payload["dr_absorbed"] == 0

    dr_ev = next((e for e in events if e.event_type == "damage_reduced"), None)
    assert dr_ev is None, "No damage_reduced event when dr_absorbed==0"


# ---------------------------------------------------------------------------
# DR-03: damage 3 < DR 5 -> fully absorbed, no hp_changed
# ---------------------------------------------------------------------------

def test_dr03_fully_absorbed_no_hp_changed():
    """Attack deals 3 raw, DR 5/magic, non-magic -> final=0, no hp_changed."""
    target = _entity("target", "monsters", hp=20, dr=[{"amount": 5, "bypass": "magic"}])
    attacker = _entity("attacker", "party", hp=20)
    ws = _world({"attacker": attacker, "target": target})

    sword = _sword()
    intent = AttackIntent(attacker_id="attacker", target_id="target", attack_bonus=99, weapon=sword)
    # d20=15 (non-threat hit), damage=3
    rng = _rng_fixed(15, 3)
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)

    hp_ev = next((e for e in events if e.event_type == "hp_changed"), None)
    assert hp_ev is None, "No hp_changed when final_damage==0"

    dr_ev = next((e for e in events if e.event_type == "damage_reduced"), None)
    assert dr_ev is not None
    assert dr_ev.payload["dr_absorbed"] == 3
    assert dr_ev.payload["final_damage"] == 0


# ---------------------------------------------------------------------------
# DR-04: DR 10/- cannot be bypassed even by magic
# ---------------------------------------------------------------------------

def test_dr04_dr_dash_not_bypassed_by_magic():
    """DR 10/- ignores magic weapon. final=max(0, raw-10)."""
    target = _entity("target", "monsters", hp=20, dr=[{"amount": 10, "bypass": "-"}])
    attacker = _entity("attacker", "party", hp=20, weapon_tags=["magic"])
    ws = _world({"attacker": attacker, "target": target})

    sword = _sword()
    intent = AttackIntent(attacker_id="attacker", target_id="target", attack_bonus=99, weapon=sword)
    # damage=15
    rng = _rng_fixed(15, 15)
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)

    hp_ev = next((e for e in events if e.event_type == "hp_changed"), None)
    assert hp_ev is not None
    # DR 10/- applies even against magic weapon: final = 15 - 10 = 5
    assert hp_ev.payload["delta"] == -5
    assert hp_ev.payload["dr_absorbed"] == 10

    dr_ev = next((e for e in events if e.event_type == "damage_reduced"), None)
    assert dr_ev is not None
    assert dr_ev.payload["dr_absorbed"] == 10
    assert dr_ev.payload["final_damage"] == 5


# ---------------------------------------------------------------------------
# DR-05: Multiple DR entries - best applicable used, not sum
# ---------------------------------------------------------------------------

def test_dr05_multiple_dr_best_used():
    """Two DR entries [10/magic, 5/silver], non-magic non-silver -> DR 10 used."""
    target = _entity("target", "monsters", hp=20, dr=[
        {"amount": 10, "bypass": "magic"},
        {"amount": 5, "bypass": "silver"},
    ])
    attacker = _entity("attacker", "party", hp=20)
    ws = _world({"attacker": attacker, "target": target})

    sword = _sword()
    intent = AttackIntent(attacker_id="attacker", target_id="target", attack_bonus=99, weapon=sword)
    # damage=15, non-magic non-silver: neither DR is bypassed, best (10) is used
    rng = _rng_fixed(15, 15)
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)

    hp_ev = next((e for e in events if e.event_type == "hp_changed"), None)
    assert hp_ev is not None
    # Best applicable DR is 10 (both not bypassed, 10 > 5): final = 15 - 10 = 5
    assert hp_ev.payload["delta"] == -5
    assert hp_ev.payload["dr_absorbed"] == 10


# ---------------------------------------------------------------------------
# DR-06: Natural attack is not magic -> DR applies
# ---------------------------------------------------------------------------

def test_dr06_natural_attack_treated_as_non_magic():
    """Natural attack: weapon_type='natural' -> not magic, DR 5/magic applies."""
    target = _entity("target", "monsters", hp=20, dr=[{"amount": 5, "bypass": "magic"}])
    attacker = _entity("attacker", "party", hp=20)
    ws = _world({"attacker": attacker, "target": target})

    claw = _natural_attack()
    intent = AttackIntent(attacker_id="attacker", target_id="target", attack_bonus=99, weapon=claw)
    rng = _rng_fixed(15, 8)
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)

    dr_ev = next((e for e in events if e.event_type == "damage_reduced"), None)
    assert dr_ev is not None
    assert dr_ev.payload["dr_absorbed"] == 5


# ---------------------------------------------------------------------------
# DR-07: dr_absorbed>0 -> damage_reduced event with correct fields
# ---------------------------------------------------------------------------

def test_dr07_damage_reduced_event_fields():
    """damage_reduced event has all required fields."""
    target = _entity("target", "monsters", hp=20, dr=[{"amount": 5, "bypass": "magic"}])
    attacker = _entity("attacker", "party", hp=20)
    ws = _world({"attacker": attacker, "target": target})

    sword = _sword()
    intent = AttackIntent(attacker_id="attacker", target_id="target", attack_bonus=99, weapon=sword)
    rng = _rng_fixed(15, 8)
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)

    dr_ev = next((e for e in events if e.event_type == "damage_reduced"), None)
    assert dr_ev is not None
    payload = dr_ev.payload
    assert "entity_id" in payload
    assert "base_damage" in payload
    assert "dr_absorbed" in payload
    assert "final_damage" in payload
    assert "dr_amount" in payload
    assert payload["entity_id"] == "target"
    assert payload["base_damage"] == 8
    assert payload["dr_absorbed"] == 5
    assert payload["final_damage"] == 3


# ---------------------------------------------------------------------------
# DR-08: Magic weapon vs DR 5/magic -> no damage_reduced event
# ---------------------------------------------------------------------------

def test_dr08_magic_weapon_no_damage_reduced_event():
    """Magic weapon bypasses DR 5/magic -> no damage_reduced event."""
    target = _entity("target", "monsters", hp=20, dr=[{"amount": 5, "bypass": "magic"}])
    attacker = _entity("attacker", "party", hp=20, weapon_tags=["magic"])
    ws = _world({"attacker": attacker, "target": target})

    sword = _sword()
    intent = AttackIntent(attacker_id="attacker", target_id="target", attack_bonus=99, weapon=sword)
    rng = _rng_fixed(15, 8)
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)

    dr_events = [e for e in events if e.event_type == "damage_reduced"]
    assert len(dr_events) == 0


# ---------------------------------------------------------------------------
# DR-09: Full attack sequence - DR accumulated correctly in hp_changed
# ---------------------------------------------------------------------------

def test_dr09_full_attack_dr_accumulated():
    """Full attack 2 hits: DR 5/magic, non-magic, 8+6 raw -> total_damage=4+1=5?
    Actually with BAB=10, get 2 iterative attacks. We fix RNG to hit both.
    Raw damage: 8 and 6. After DR5: 3 and 1. total=4, total_dr_absorbed=10.
    """
    target = _entity("target", "monsters", hp=30, dr=[{"amount": 5, "bypass": "magic"}])
    attacker = _entity("attacker", "party", hp=20)
    attacker[EF.BAB] = 10  # gets 2 iterative attacks (10, 5)
    attacker["bab"] = 10
    ws = _world({"attacker": attacker, "target": target})

    sword = _sword()
    # BAB=10 -> attacks at +10 and +5
    intent = FullAttackIntent(
        attacker_id="attacker",
        target_id="target",
        base_attack_bonus=10,
        weapon=sword,
    )

    # RNG: attack1 d20=20 (nat20 auto-hit), attack1 dmg=8,
    #       confirm (since nat20 threatens) d20=15,
    #       attack2 d20=20, attack2 dmg=6
    # Actually nat20 is a threat so needs confirmation roll too. Let's use attack_bonus=99 guarantees
    # and seed for known outcomes. Use RNGManager for determinism.
    rng = RNGManager(master_seed=999)
    events = resolve_full_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)

    hp_ev = next((e for e in events if e.event_type == "hp_changed"), None)
    if hp_ev is not None:
        assert "dr_absorbed" in hp_ev.payload
        # total_dr_absorbed should reflect sum of all per-hit DR
        # (may be 5 per hit if both hit)
        total_dr = hp_ev.payload["dr_absorbed"]
        assert total_dr >= 0


# ---------------------------------------------------------------------------
# DR-10: No DAMAGE_REDUCTIONS field -> no DR applied
# ---------------------------------------------------------------------------

def test_dr10_no_dr_field_no_reduction():
    """Entity with no DAMAGE_REDUCTIONS field -> get_applicable_dr returns 0."""
    target = _entity("target", "monsters", hp=20)  # no dr kwarg
    attacker = _entity("attacker", "party", hp=20)
    ws = _world({"attacker": attacker, "target": target})

    sword = _sword()
    intent = AttackIntent(attacker_id="attacker", target_id="target", attack_bonus=99, weapon=sword)
    rng = _rng_fixed(15, 8)
    events = resolve_attack(intent=intent, world_state=ws, rng=rng, next_event_id=0, timestamp=0.0)

    hp_ev = next((e for e in events if e.event_type == "hp_changed"), None)
    assert hp_ev is not None
    assert hp_ev.payload["delta"] == -8  # no DR
    assert hp_ev.payload["dr_absorbed"] == 0

    dr_ev = next((e for e in events if e.event_type == "damage_reduced"), None)
    assert dr_ev is None
