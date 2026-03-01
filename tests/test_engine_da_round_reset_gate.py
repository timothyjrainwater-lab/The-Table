"""Gate tests for Deflect Arrows round-reset fix (WO-ENGINE-DA-ROUND-RESET-001).
Gate IDs: DARR-001 through DARR-004.

Closes:
- FINDING-ENGINE-DA-ROUND-RESET-001: deflect_arrows_used list never cleared between rounds,
  permanently locking out defenders after round 1.
"""

import pytest
from copy import deepcopy
from unittest import mock

from aidm.core.combat_controller import execute_combat_round, start_combat
from aidm.core.attack_resolver import resolve_attack
from aidm.core.state import WorldState
from aidm.schemas.attack import AttackIntent, Weapon
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ws_with_active_combat(deflect_arrows_used=None, initiative_order=None):
    """Minimal WorldState with active_combat already initialized."""
    entities = {
        "attacker": {
            EF.HP_CURRENT: 20, EF.HP_MAX: 20, EF.AC: 12,
            EF.DEFEATED: False, EF.TEAM: "players",
            EF.ATTACK_BONUS: 5,
        },
        "defender": {
            EF.HP_CURRENT: 20, EF.HP_MAX: 20, EF.AC: 12,
            EF.DEFEATED: False, EF.TEAM: "monsters",
            EF.FEATS: ["deflect_arrows"],
            EF.FREE_HANDS: 1,
            EF.CONDITIONS: {},
        },
    }
    active_combat = {
        "turn_counter": 1,
        "round_index": 1,
        "initiative_order": initiative_order if initiative_order is not None else [],
        "flat_footed_actors": [],
        "aoo_used_this_round": ["attacker"],      # pre-populated
        "aoo_count_this_round": {"attacker": 1},  # pre-populated
        "deflect_arrows_used": deflect_arrows_used if deflect_arrows_used is not None else [],
        "grapple_pairs": [],
    }
    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat=active_combat,
    )


def _rng(d20_roll=15, dmg_roll=4):
    stream = mock.MagicMock()
    stream.randint.side_effect = [d20_roll, dmg_roll] * 20
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


def _ranged_weapon():
    return Weapon(
        damage_dice="1d6",
        damage_bonus=0,
        damage_type="piercing",
        critical_multiplier=2,
        critical_range=20,
        weapon_type="ranged",
        range_increment=60,
    )


# ---------------------------------------------------------------------------
# DARR-001: deflect_arrows_used clears at round boundary
# ---------------------------------------------------------------------------

def test_darr_001_list_clears_at_round_boundary():
    """DARR-001: deflect_arrows_used populated before round → empty after execute_combat_round()."""
    ws = _make_ws_with_active_combat(deflect_arrows_used=["defender"])
    assert ws.active_combat["deflect_arrows_used"] == ["defender"], "Pre-condition: list populated"

    result = execute_combat_round(
        world_state=ws,
        doctrines={},
        rng=_rng(),
        next_event_id=10,
        timestamp=1.0,
    )

    da_used = result.world_state.active_combat.get("deflect_arrows_used", "KEY_MISSING")
    assert da_used == [], (
        f"deflect_arrows_used should be [] after round, got: {da_used!r}"
    )


# ---------------------------------------------------------------------------
# DARR-002: DA fires in round 2 after round 1 use
# ---------------------------------------------------------------------------

def test_darr_002_da_fires_in_round_2_after_round_1_use():
    """DARR-002: deflect_arrows_used populated (round 1 used) → round resets → DA fires in round 2."""
    # Start: defender already used DA this round
    ws = _make_ws_with_active_combat(deflect_arrows_used=["defender"])

    # Execute round — this should reset deflect_arrows_used to []
    result = execute_combat_round(
        world_state=ws,
        doctrines={},
        rng=_rng(),
        next_event_id=10,
        timestamp=1.0,
    )
    ws_after_round = result.world_state
    assert ws_after_round.active_combat["deflect_arrows_used"] == [], "Reset confirmed"

    # Now call resolve_attack against defender in the new state — DA should fire
    intent = AttackIntent(
        attacker_id="attacker",
        target_id="defender",
        attack_bonus=15,  # guarantees hit vs AC 12
        weapon=_ranged_weapon(),
    )
    events = resolve_attack(
        intent=intent,
        world_state=ws_after_round,
        rng=_rng(d20_roll=15),
        next_event_id=100,
        timestamp=2.0,
    )
    da_events = [e for e in events if e.event_type == "deflect_arrows"]
    assert len(da_events) == 1, (
        f"DA should fire in round 2 after reset; got {[e.event_type for e in events]}"
    )
    damage_events = [e for e in events if e.event_type == "damage_roll"]
    assert damage_events == [], "No damage_roll after deflect_arrows"


# ---------------------------------------------------------------------------
# DARR-003: all three per-round resets fire together
# ---------------------------------------------------------------------------

def test_darr_003_all_three_resets_together():
    """DARR-003: aoo_used_this_round, aoo_count_this_round, deflect_arrows_used all reset together."""
    ws = _make_ws_with_active_combat(
        deflect_arrows_used=["defender"],
        initiative_order=[],
    )
    # Verify pre-conditions
    assert ws.active_combat["aoo_used_this_round"] == ["attacker"]
    assert ws.active_combat["aoo_count_this_round"] == {"attacker": 1}
    assert ws.active_combat["deflect_arrows_used"] == ["defender"]

    result = execute_combat_round(
        world_state=ws,
        doctrines={},
        rng=_rng(),
        next_event_id=0,
        timestamp=0.0,
    )
    ac = result.world_state.active_combat

    assert ac["aoo_used_this_round"] == [], (
        f"aoo_used_this_round not reset; got {ac['aoo_used_this_round']!r}"
    )
    assert ac["aoo_count_this_round"] == {}, (
        f"aoo_count_this_round not reset; got {ac['aoo_count_this_round']!r}"
    )
    assert ac["deflect_arrows_used"] == [], (
        f"deflect_arrows_used not reset; got {ac['deflect_arrows_used']!r}"
    )


# ---------------------------------------------------------------------------
# DARR-004: DA-001 regression — basic DA still fires (no regression from reset fix)
# ---------------------------------------------------------------------------

def test_darr_004_da_001_regression():
    """DARR-004: regression — DA fires when feat present, ranged hit, free hand, not flat-footed."""
    entities = {
        "attacker": {
            EF.HP_CURRENT: 20, EF.HP_MAX: 20, EF.AC: 10,
            EF.DEFEATED: False, EF.TEAM: "players",
        },
        "defender": {
            EF.HP_CURRENT: 20, EF.HP_MAX: 20, EF.AC: 12,
            EF.DEFEATED: False, EF.TEAM: "monsters",
            EF.FEATS: ["deflect_arrows"],
            EF.FREE_HANDS: 1,
            EF.CONDITIONS: {},
        },
    }
    ws = WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat={
            "deflect_arrows_used": [],
            "turn_counter": 0,
            "round_index": 1,
            "initiative_order": [],
            "flat_footed_actors": [],
            "aoo_used_this_round": [],
            "aoo_count_this_round": {},
            "grapple_pairs": [],
        },
    )
    intent = AttackIntent(
        attacker_id="attacker",
        target_id="defender",
        attack_bonus=15,
        weapon=_ranged_weapon(),
    )
    events = resolve_attack(
        intent=intent,
        world_state=ws,
        rng=_rng(d20_roll=15),
        next_event_id=0,
        timestamp=0.0,
    )
    da_events = [e for e in events if e.event_type == "deflect_arrows"]
    assert len(da_events) == 1, f"DA-001 regression: expected 1 deflect_arrows, got {[e.event_type for e in events]}"
    assert not any(e.event_type == "damage_roll" for e in events), "No damage after deflect"
