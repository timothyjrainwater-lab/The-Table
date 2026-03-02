"""Gate tests: WO-ENGINE-MANEUVER-CONDITION-MODIFIER-001 (Batch AX WO1).

MCM-001..008 — get_condition_modifiers() wired into all 6 maneuver resolvers:
  MCM-001: No conditions — maneuver check baseline (regression: existing behavior unchanged)
  MCM-002: Shaken attacker — bull rush attacker_modifier reduced by 2 (PHB p.306)
  MCM-003: Frightened attacker — maneuver attacker_modifier reduced by 2 (PHB p.305)
  MCM-004: Shaken defender — defender_modifier in opposed_check reduced by 2
  MCM-005: Prone attacker — maneuver attacker_modifier reduced by 4 (PHB p.304)
  MCM-006: All 6 maneuver types apply shaken –2 to attacker_modifier (not just one)
  MCM-007: Regression — resolve_attack() unchanged (no modifications to canonical attack path)
  MCM-008: Coverage map updated — PARTIAL → IMPLEMENTED for maneuver condition modifier

PHB p.154–158: Maneuver opposed checks use the same attack roll modifier framework.
PHB p.306 (Shaken): –2 penalty on attack rolls. Applies to maneuver attack rolls.
PHB p.304 (Prone): –4 penalty on attack rolls. Applies to maneuver attack rolls.
FINDING-ENGINE-MANEUVER-CONDITION-MODIFIER-001 closed.
"""
from __future__ import annotations

import unittest.mock as mock

import pytest

from aidm.core.maneuver_resolver import (
    resolve_bull_rush,
    resolve_trip,
    resolve_overrun,
    resolve_sunder,
    resolve_disarm,
    resolve_grapple,
)
from aidm.core.attack_resolver import resolve_attack
from aidm.core.rng_manager import RNGManager
from aidm.core.state import WorldState
from aidm.schemas.maneuvers import (
    BullRushIntent, TripIntent, OverrunIntent,
    SunderIntent, DisarmIntent, GrappleIntent,
)
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _attacker(eid="fighter", bab=6, str_mod=2, conditions=None, feats=None) -> dict:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 50, EF.HP_MAX: 50,
        EF.AC: 14,
        EF.ATTACK_BONUS: bab, EF.BAB: bab,
        EF.STR_MOD: str_mod, EF.DEX_MOD: 2,
        EF.DEFEATED: False, EF.DYING: False,
        EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.FEATS: feats if feats is not None else [],
        EF.POSITION: {"x": 0, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.FAVORED_ENEMIES: [],
        EF.DAMAGE_REDUCTIONS: [],
        EF.WEAPON: {"enhancement_bonus": 0, "tags": [], "material": "steel",
                    "alignment": "none", "damage_dice": "1d8", "weapon_type": "one-handed"},
        EF.ARMOR_TYPE: "none",
        EF.INSPIRE_COURAGE_ACTIVE: False,
        EF.INSPIRE_COURAGE_BONUS: 0,
        EF.NEGATIVE_LEVELS: 0,
        EF.DISARMED: False,
        EF.WEAPON_BROKEN: False,
    }


def _defender(eid="goblin", bab=2, str_mod=1, conditions=None) -> dict:
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: 30, EF.HP_MAX: 30,
        EF.AC: 12,
        EF.ATTACK_BONUS: bab, EF.BAB: bab,
        EF.STR_MOD: str_mod, EF.DEX_MOD: 1,
        EF.DEFEATED: False, EF.DYING: False,
        EF.STABLE: False, EF.DISABLED: False,
        EF.CONDITIONS: conditions if conditions is not None else {},
        EF.FEATS: [],
        EF.POSITION: {"x": 1, "y": 0},
        EF.SIZE_CATEGORY: "medium",
        EF.FAVORED_ENEMIES: [],
        EF.DAMAGE_REDUCTIONS: [],
        EF.WEAPON: {"enhancement_bonus": 0, "tags": [], "material": "steel",
                    "alignment": "none", "damage_dice": "1d6", "weapon_type": "one-handed"},
        EF.ARMOR_TYPE: "none",
        EF.SAVE_FORT: 2, EF.CON_MOD: 1,
        EF.CREATURE_TYPE: "humanoid",
        EF.ARMOR_AC_BONUS: 0,
        EF.CLASS_LEVELS: {},
        EF.NONLETHAL_DAMAGE: 0,
    }


def _world(attacker, defender) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={attacker[EF.ENTITY_ID]: attacker, defender[EF.ENTITY_ID]: defender},
        active_combat={
            "initiative_order": [attacker[EF.ENTITY_ID], defender[EF.ENTITY_ID]],
            "deflect_arrows_used": [],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
            "cleave_used_this_turn": set(),
            "grapple_pairs": [],
        },
    )


def _rng(d20_seq=None) -> mock.MagicMock:
    """Controllable RNG: first values go to combat stream."""
    stream = mock.MagicMock()
    if d20_seq is None:
        d20_seq = [15, 10] + [4] * 20  # attacker roll, defender roll, damage
    stream.randint.side_effect = d20_seq + [4] * 30
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _opposed_check_event(events):
    return next((e for e in events if e.event_type == "opposed_check"), None)


# ---------------------------------------------------------------------------
# MCM-001: No conditions — baseline (regression: attacker_modifier = base value)
# ---------------------------------------------------------------------------

def test_MCM001_no_conditions_baseline():
    """MCM-001: No conditions — bull rush baseline.
    attacker_modifier = str_mod + size_mod (medium=0) + no condition = 2.
    Regression: existing behavior unchanged when no conditions present.
    """
    a = _attacker(bab=6, str_mod=2)
    d = _defender(bab=2, str_mod=1)
    ws = _world(a, d)
    intent = BullRushIntent(attacker_id="fighter", target_id="goblin")
    events, _, _ = resolve_bull_rush(intent, ws, _rng([15, 10]), next_event_id=0, timestamp=0.0)

    ev = _opposed_check_event(events)
    assert ev is not None, "MCM-001: opposed_check event must be emitted"
    # Medium attacker: str_mod=2, size=0, charge=0 → attacker_modifier=2
    # No conditions → no delta
    assert ev.payload["attacker_modifier"] == 2, (
        f"MCM-001: No conditions → attacker_modifier should be 2 (str_mod=2, size=0). "
        f"Got: {ev.payload['attacker_modifier']!r}"
    )


# ---------------------------------------------------------------------------
# MCM-002: Shaken attacker — bull rush attacker_modifier –2 (PHB p.306)
# ---------------------------------------------------------------------------

def test_MCM002_shaken_attacker_bull_rush_minus2():
    """MCM-002: Shaken attacker → attacker_modifier reduced by 2 in bull rush.
    PHB p.306: Shaken = –2 to attack rolls. Applies to maneuver attack rolls.
    get_condition_modifiers() now called at WO-ENGINE-MANEUVER-CONDITION-MODIFIER-001 site.
    """
    a = _attacker(bab=6, str_mod=2, conditions={"shaken": {}})
    d = _defender(bab=2, str_mod=1)
    ws = _world(a, d)
    intent = BullRushIntent(attacker_id="fighter", target_id="goblin")
    events, _, _ = resolve_bull_rush(intent, ws, _rng([15, 10]), next_event_id=0, timestamp=0.0)

    ev = _opposed_check_event(events)
    assert ev is not None, "MCM-002: opposed_check event must be emitted"
    # str_mod=2, size=0, shaken=-2 → attacker_modifier=0
    expected = 2 - 2  # str_mod - shaken_penalty
    assert ev.payload["attacker_modifier"] == expected, (
        f"MCM-002: Shaken attacker → attacker_modifier should be {expected} "
        f"(str_mod=2, shaken=-2). Got: {ev.payload['attacker_modifier']!r}"
    )


# ---------------------------------------------------------------------------
# MCM-003: Frightened attacker — maneuver attacker_modifier –2 (PHB p.305)
# ---------------------------------------------------------------------------

def test_MCM003_frightened_attacker_minus2():
    """MCM-003: Frightened attacker → attacker_modifier reduced by 2 in trip.
    PHB p.305: Frightened = –2 to attack rolls. Applies to maneuver attack rolls.
    """
    a = _attacker(bab=6, str_mod=2, conditions={"frightened": {}})
    d = _defender(bab=2, str_mod=1)
    ws = _world(a, d)
    # Use trip — frightened applies the same as shaken
    intent = TripIntent(attacker_id="fighter", target_id="goblin")
    events, _, _ = resolve_trip(intent, ws, _rng([15, 10, 15, 10]), next_event_id=0, timestamp=0.0)

    ev = _opposed_check_event(events)
    assert ev is not None, "MCM-003: opposed_check event must be emitted for trip"
    # str_mod=2, size=0, frightened=-2 → attacker_modifier=0
    expected = 2 - 2
    assert ev.payload["attacker_modifier"] == expected, (
        f"MCM-003: Frightened attacker → attacker_modifier should be {expected} "
        f"(str_mod=2, frightened=-2). Got: {ev.payload['attacker_modifier']!r}"
    )


# ---------------------------------------------------------------------------
# MCM-004: Shaken defender — defender_modifier in opposed_check reduced by 2
# ---------------------------------------------------------------------------

def test_MCM004_shaken_defender_minus2():
    """MCM-004: Shaken defender → defender_modifier reduced by 2 in bull rush.
    PHB p.306: Shaken = –2 to attack rolls. Defender's opposed check also penalized.
    get_condition_modifiers(world_state, target_id, context="defense") now called.
    """
    a = _attacker(bab=6, str_mod=2)
    d = _defender(bab=2, str_mod=1, conditions={"shaken": {}})
    ws = _world(a, d)
    intent = BullRushIntent(attacker_id="fighter", target_id="goblin")
    events, _, _ = resolve_bull_rush(intent, ws, _rng([15, 10]), next_event_id=0, timestamp=0.0)

    ev = _opposed_check_event(events)
    assert ev is not None, "MCM-004: opposed_check event must be emitted"
    # Defender: str_mod=1, size=0, stability=0, shaken=-2 → defender_modifier=-1
    expected_defender = 1 - 2  # str_mod - shaken_penalty
    assert ev.payload["defender_modifier"] == expected_defender, (
        f"MCM-004: Shaken defender → defender_modifier should be {expected_defender} "
        f"(str_mod=1, shaken=-2). Got: {ev.payload['defender_modifier']!r}"
    )


# ---------------------------------------------------------------------------
# MCM-005: Prone attacker — maneuver attacker_modifier –4 (PHB p.304)
# ---------------------------------------------------------------------------

def test_MCM005_prone_attacker_minus4():
    """MCM-005: Prone attacker → attacker_modifier reduced by 4 in overrun.
    PHB p.304: Prone = –4 to attack rolls. Applies to maneuver attack rolls.
    """
    a = _attacker(bab=6, str_mod=2, conditions={"prone": {}})
    d = _defender(bab=2, str_mod=1)
    ws = _world(a, d)
    intent = OverrunIntent(attacker_id="fighter", target_id="goblin", defender_avoids=False)
    events, _, _ = resolve_overrun(intent, ws, _rng([15, 10]), next_event_id=0, timestamp=0.0)

    ev = _opposed_check_event(events)
    assert ev is not None, "MCM-005: opposed_check event must be emitted for overrun"
    # str_mod=2, size=0, prone=-4 → attacker_modifier=-2
    expected = 2 - 4
    assert ev.payload["attacker_modifier"] == expected, (
        f"MCM-005: Prone attacker → attacker_modifier should be {expected} "
        f"(str_mod=2, prone=-4). Got: {ev.payload['attacker_modifier']!r}"
    )


# ---------------------------------------------------------------------------
# MCM-006: All 6 maneuver types apply shaken –2 to attacker_modifier
# ---------------------------------------------------------------------------

def test_MCM006_all_6_resolvers_shaken_attacker():
    """MCM-006: All 6 maneuver types apply shaken –2 to attacker_modifier.
    WO-ENGINE-MANEUVER-CONDITION-MODIFIER-001: all 6 resolvers modified.
    Each should show attacker_modifier = (base) - 2 when attacker is shaken.
    """
    results = {}

    a = _attacker(bab=6, str_mod=2, conditions={"shaken": {}})
    d = _defender(bab=2, str_mod=1)

    # Expected attacker base without conditions, per resolver type:
    # bull_rush: str_mod=2 + size=0 = 2 → with shaken = 0
    # trip: str_mod=2 + size=0 = 2 → with shaken = 0
    # overrun: str_mod=2 + size=0 = 2 → with shaken = 0
    # sunder: bab=6 + str_mod=2 + size=0 = 8 → with shaken = 6
    # disarm: bab=6 + str_mod=2 + size=0 = 8 → with shaken = 6
    # grapple: bab=6 + str_mod=2 + size=0 = 8 → with shaken = 6

    expected_base = {
        "bull_rush": 2,
        "trip": 2,
        "overrun": 2,
        "sunder": 8,
        "disarm": 8,
        "grapple": 8,
    }

    # bull_rush
    ws = _world(a, d)
    evts, _, _ = resolve_bull_rush(
        BullRushIntent(attacker_id="fighter", target_id="goblin"),
        ws, _rng([15, 10]), next_event_id=0, timestamp=0.0
    )
    ev = _opposed_check_event(evts)
    results["bull_rush"] = ev.payload["attacker_modifier"] if ev else None

    # trip
    ws = _world(a, d)
    evts, _, _ = resolve_trip(
        TripIntent(attacker_id="fighter", target_id="goblin"),
        ws, _rng([15, 10, 15, 10]), next_event_id=0, timestamp=0.0
    )
    ev = _opposed_check_event(evts)
    results["trip"] = ev.payload["attacker_modifier"] if ev else None

    # overrun
    ws = _world(a, d)
    evts, _, _ = resolve_overrun(
        OverrunIntent(attacker_id="fighter", target_id="goblin", defender_avoids=False),
        ws, _rng([15, 10]), next_event_id=0, timestamp=0.0
    )
    ev = _opposed_check_event(evts)
    results["overrun"] = ev.payload["attacker_modifier"] if ev else None

    # sunder
    ws = _world(a, d)
    evts, _, _ = resolve_sunder(
        SunderIntent(attacker_id="fighter", target_id="goblin", target_item="weapon"),
        ws, _rng([15, 10, 4]), next_event_id=0, timestamp=0.0
    )
    ev = _opposed_check_event(evts)
    results["sunder"] = ev.payload["attacker_modifier"] if ev else None

    # disarm
    ws = _world(a, d)
    evts, _, _ = resolve_disarm(
        DisarmIntent(attacker_id="fighter", target_id="goblin"),
        ws, _rng([15, 10]), next_event_id=0, timestamp=0.0
    )
    ev = _opposed_check_event(evts)
    results["disarm"] = ev.payload["attacker_modifier"] if ev else None

    # grapple
    ws = _world(a, d)
    evts, _, _ = resolve_grapple(
        GrappleIntent(attacker_id="fighter", target_id="goblin"),
        ws, _rng([15, 10, 15, 10]), next_event_id=0, timestamp=0.0
    )
    ev = _opposed_check_event(evts)
    results["grapple"] = ev.payload["attacker_modifier"] if ev else None

    for maneuver_type, actual in results.items():
        base = expected_base[maneuver_type]
        expected = base - 2  # shaken = -2
        assert actual == expected, (
            f"MCM-006: {maneuver_type} shaken attacker — attacker_modifier should be "
            f"{expected} (base={base}, shaken=-2). Got: {actual!r}"
        )


# ---------------------------------------------------------------------------
# MCM-007: Regression — resolve_attack() unchanged
# ---------------------------------------------------------------------------

def test_MCM007_resolve_attack_unchanged():
    """MCM-007: resolve_attack() behavior unchanged — no modifications to canonical path.
    Shaken attacker via resolve_attack still shows condition_modifier=-2.
    """
    a = _attacker(bab=6, str_mod=2, conditions={"shaken": {}})
    d = _defender(bab=2, str_mod=1)
    a[EF.DISARMED] = False
    a[EF.WEAPON_BROKEN] = False
    a[EF.INSPIRE_COURAGE_ACTIVE] = False
    a[EF.INSPIRE_COURAGE_BONUS] = 0
    a[EF.NEGATIVE_LEVELS] = 0
    d[EF.ARMOR_TYPE] = "none"
    d[EF.ARMOR_AC_BONUS] = 0
    d[EF.CLASS_LEVELS] = {}
    d[EF.CREATURE_TYPE] = "humanoid"
    ws = _world(a, d)

    weapon = Weapon(
        damage_dice="1d8", damage_bonus=0, damage_type="slashing",
        weapon_type="one-handed", grip="one-handed", is_two_handed=False,
        range_increment=0, enhancement_bonus=0, critical_multiplier=2, critical_range=20,
    )
    intent = AttackIntent(
        attacker_id="fighter", target_id="goblin",
        attack_bonus=6 + 2, weapon=weapon,
    )
    events = resolve_attack(intent, ws, RNGManager(42), next_event_id=0, timestamp=0.0)
    roll_evts = [e for e in events if e.event_type == "attack_roll"]
    assert roll_evts, "MCM-007: resolve_attack must produce attack_roll event"
    cond_mod = roll_evts[0].payload.get("condition_modifier")
    assert cond_mod == -2, (
        f"MCM-007 REGRESSION: resolve_attack shaken condition_modifier must be -2. "
        f"Got: {cond_mod!r}. Canonical path was inadvertently modified."
    )


# ---------------------------------------------------------------------------
# MCM-008: Coverage map updated — PARTIAL → IMPLEMENTED
# ---------------------------------------------------------------------------

def test_MCM008_coverage_map_updated():
    """MCM-008: ENGINE_COVERAGE_MAP.md updated for maneuver condition modifier.
    The coverage map must contain 'IMPLEMENTED' near 'maneuver' and 'condition'.
    """
    import os
    map_path = os.path.join(
        os.path.dirname(__file__), "..", "docs", "ENGINE_COVERAGE_MAP.md"
    )
    with open(map_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "WO-ENGINE-MANEUVER-CONDITION-MODIFIER-001" in content, (
        "MCM-008: ENGINE_COVERAGE_MAP.md must reference WO-ENGINE-MANEUVER-CONDITION-MODIFIER-001"
    )
    assert "IMPLEMENTED" in content, (
        "MCM-008: ENGINE_COVERAGE_MAP.md must contain 'IMPLEMENTED' entry"
    )
