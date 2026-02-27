"""ENGINE-IMPROVED-TURNING Gate -- Improved Turning feat effective level +1 (8 tests).

Gate: ENGINE-IMPROVED-TURNING
Tests: ITN-001 through ITN-008
WO: WO-ENGINE-IMPROVED-TURNING-001

PHB p.96: Improved Turning feat adds +1 to effective turning level.
Applies before turn check table lookup. Affects both cleric and paladin turning.
Also applies to rebuke (evil cleric).

Abbreviation: ITN (NOT IT — IT = Improved Trip+Sunder, Batch N).
"""

from copy import deepcopy
from typing import List

from aidm.core.turn_undead_resolver import resolve_turn_undead, apply_turn_undead_events
from aidm.core.state import WorldState
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.entity_fields import EF
from aidm.schemas.intents import TurnUndeadIntent


# ---------------------------------------------------------------------------
# RNG stub: rolls fixed values for turning check and HP budget
# ---------------------------------------------------------------------------

class _FixedRNG(RNGProvider):
    """Returns fixed dice values for deterministic turn resolution."""

    def __init__(self, d6_val: int = 3):
        self._d6 = d6_val

    def stream(self, name: str):
        return self

    def randint(self, lo: int, hi: int) -> int:
        return min(self._d6, hi)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _cleric(eid="cleric", cleric_level=5, cha_mod=2, feats=None, evil=False,
            turn_uses=5, turn_uses_max=5):
    """Build a cleric entity."""
    entity = {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 14,
        EF.DEFEATED: False,
        EF.CLASS_LEVELS: {"cleric": cleric_level},
        EF.CHA_MOD: cha_mod,
        EF.FEATS: feats if feats is not None else [],
        EF.TURN_UNDEAD_USES: turn_uses,
        EF.TURN_UNDEAD_USES_MAX: turn_uses_max,
        EF.CONDITIONS: {},
        EF.TEMPORARY_MODIFIERS: {},
    }
    if evil:
        entity["class_features"] = {"channels_negative_energy": True}
    return entity


def _paladin(eid="paladin", paladin_level=4, cha_mod=2, feats=None, turn_uses=3):
    """Build a paladin entity. Turns as cleric of level paladin_level // 2."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "party",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.AC: 18,
        EF.DEFEATED: False,
        EF.CLASS_LEVELS: {"paladin": paladin_level},
        EF.CHA_MOD: cha_mod,
        EF.FEATS: feats if feats is not None else [],
        EF.TURN_UNDEAD_USES: turn_uses,
        EF.TURN_UNDEAD_USES_MAX: turn_uses,
        EF.CONDITIONS: {},
        EF.TEMPORARY_MODIFIERS: {},
    }


def _undead(eid, hd, hp=None):
    """Build an undead entity with given HD."""
    return {
        EF.ENTITY_ID: eid,
        EF.TEAM: "enemy",
        EF.HP_CURRENT: hp or hd * 6,
        EF.HP_MAX: hp or hd * 6,
        EF.AC: 12,
        EF.DEFEATED: False,
        EF.IS_UNDEAD: True,
        EF.HD_COUNT: hd,
        EF.CONDITIONS: {},
        EF.TEMPORARY_MODIFIERS: {},
    }


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


# ===========================================================================
# ITN-001: Cleric 5 + Improved Turning → effective level 6 (HD threshold shifts)
# ===========================================================================

def test_itn001_effective_level_plus_one():
    """ITN-001: Cleric 5 + Improved Turning → turns as effective cleric 6.

    With effective level 6 and RNG producing turning check = 3+3+6+2 = 14,
    a HD-5 undead (normally at 5-4=1 → turned, not destroyed at base 5)
    becomes destroyable at effective level 6 (HD 5 ≤ 6-4 = 2 → not yet,
    so let's verify via effective level in the event payload).
    """
    cleric = _cleric(cleric_level=5, cha_mod=2, feats=["improved_turning"])
    # HD-1 undead: at cleric_level 6, 1 ≤ 6-4=2 → destroyed (level 6 check)
    # At cleric_level 5, 1 ≤ 5-4=1 → also destroyed, but ITN-002 covers the interesting case.
    # Here we verify via improved_turning_active event payload.
    skeleton = _undead("skeleton", hd=1, hp=6)
    ws = _world({"cleric": cleric, "skeleton": skeleton})
    rng = _FixedRNG(d6_val=3)

    intent = TurnUndeadIntent(cleric_id="cleric", target_ids=["skeleton"])
    events = resolve_turn_undead(intent, ws, rng, next_event_id=1, timestamp=0.0)

    itn_events = [e for e in events if e.event_type == "improved_turning_active"]
    assert len(itn_events) == 1, f"Expected 1 improved_turning_active event, got {len(itn_events)}"
    assert itn_events[0].payload["effective_level"] == 6, (
        f"Expected effective_level=6, got {itn_events[0].payload['effective_level']}"
    )


# ===========================================================================
# ITN-002: +1 allows turning higher-HD undead than base level alone
# ===========================================================================

def test_itn002_higher_hd_turned_with_improved_turning():
    """ITN-002: Improved Turning allows turning an undead that base level cannot.

    Cleric 5, CHA mod=0. RNG d6=1 → turning check = 1+1+6+0 = 8, budget = (1+1)*10 = 20.
    HD-8 undead with hp=15 (fits budget): turning check 8, HD 8 ≤ 8 → turned.
    Without Improved Turning: check = 1+1+5+0 = 7, HD 8 > 7 → unaffected.
    """
    cleric = _cleric(cleric_level=5, cha_mod=0, feats=["improved_turning"])
    # HD-8 with low HP so it fits within budget (1+1)*10 = 20
    undead_hd8 = _undead("ghoul", hd=8, hp=15)
    ws = _world({"cleric": cleric, "ghoul": undead_hd8})
    rng = _FixedRNG(d6_val=1)  # turning check = 1+1+6+0 = 8, budget = 20

    intent = TurnUndeadIntent(cleric_id="cleric", target_ids=["ghoul"])
    events = resolve_turn_undead(intent, ws, rng, next_event_id=1, timestamp=0.0)

    turned_events = [e for e in events if e.event_type == "undead_turned"]
    assert len(turned_events) == 1, (
        f"Expected HD-8 undead turned with effective level 6; events: {[e.event_type for e in events]}"
    )


# ===========================================================================
# ITN-003: Cleric WITHOUT Improved Turning → turns at base level (regression)
# ===========================================================================

def test_itn003_without_feat_base_level_unchanged():
    """ITN-003: Cleric without Improved Turning uses base cleric level for turning."""
    cleric = _cleric(cleric_level=5, cha_mod=0, feats=[])
    undead_hd8 = _undead("ghoul", hd=8, hp=30)
    ws = _world({"cleric": cleric, "ghoul": undead_hd8})
    rng = _FixedRNG(d6_val=1)  # turning check = 1+1+5+0 = 7 → 8 > 7 → unaffected

    intent = TurnUndeadIntent(cleric_id="cleric", target_ids=["ghoul"])
    events = resolve_turn_undead(intent, ws, rng, next_event_id=1, timestamp=0.0)

    turned_events = [e for e in events if e.event_type == "undead_turned"]
    assert len(turned_events) == 0, (
        f"Expected HD-8 undead unaffected at base level 5 (check=7); got turned events"
    )
    itn_events = [e for e in events if e.event_type == "improved_turning_active"]
    assert len(itn_events) == 0, "No improved_turning_active event should fire without feat"


# ===========================================================================
# ITN-004: improved_turning_active event with correct effective_level payload
# ===========================================================================

def test_itn004_event_emitted_correct_payload():
    """ITN-004: improved_turning_active event emitted with correct cleric_id and effective_level."""
    cleric = _cleric(cleric_level=3, cha_mod=1, feats=["improved_turning"])
    skeleton = _undead("skeleton", hd=1, hp=6)
    ws = _world({"cleric": cleric, "skeleton": skeleton})
    rng = _FixedRNG(d6_val=3)

    intent = TurnUndeadIntent(cleric_id="cleric", target_ids=["skeleton"])
    events = resolve_turn_undead(intent, ws, rng, next_event_id=1, timestamp=0.0)

    itn_events = [e for e in events if e.event_type == "improved_turning_active"]
    assert len(itn_events) == 1
    payload = itn_events[0].payload
    assert payload["cleric_id"] == "cleric", f"Wrong cleric_id: {payload['cleric_id']}"
    assert payload["effective_level"] == 4, (
        f"Expected effective_level=4 (3+1), got {payload['effective_level']}"
    )


# ===========================================================================
# ITN-005: Paladin with Improved Turning → paladin turning level also increases
# ===========================================================================

def test_itn005_paladin_turning_level_increases():
    """ITN-005: Paladin with Improved Turning gets +1 on derived turning level.

    Paladin 4 normally turns as effective cleric 4//2 = 2.
    With Improved Turning: effective level = 3.
    improved_turning_active event should show effective_level=3.
    """
    paladin = _paladin(paladin_level=4, cha_mod=2, feats=["improved_turning"])
    skeleton = _undead("skeleton", hd=1, hp=6)
    ws = _world({"paladin": paladin, "skeleton": skeleton})
    rng = _FixedRNG(d6_val=3)

    intent = TurnUndeadIntent(cleric_id="paladin", target_ids=["skeleton"])
    events = resolve_turn_undead(intent, ws, rng, next_event_id=1, timestamp=0.0)

    itn_events = [e for e in events if e.event_type == "improved_turning_active"]
    assert len(itn_events) == 1, f"Expected improved_turning_active event, got {[e.event_type for e in events]}"
    assert itn_events[0].payload["effective_level"] == 3, (
        f"Expected effective_level=3 (paladin 4//2=2, +1 ITN), got {itn_events[0].payload['effective_level']}"
    )


# ===========================================================================
# ITN-006: Evil cleric (rebuke) with Improved Turning → +1 applies to rebuke
# ===========================================================================

def test_itn006_rebuke_effective_level_plus_one():
    """ITN-006: Evil cleric with Improved Turning → effective level +1 on rebuke attempt."""
    evil_cleric = _cleric(cleric_level=3, cha_mod=1, feats=["improved_turning"], evil=True)
    skeleton = _undead("skeleton", hd=1, hp=6)
    ws = _world({"cleric": evil_cleric, "skeleton": skeleton})
    rng = _FixedRNG(d6_val=3)

    intent = TurnUndeadIntent(cleric_id="cleric", target_ids=["skeleton"])
    events = resolve_turn_undead(intent, ws, rng, next_event_id=1, timestamp=0.0)

    itn_events = [e for e in events if e.event_type == "improved_turning_active"]
    assert len(itn_events) == 1, "improved_turning_active should fire for evil cleric too"
    assert itn_events[0].payload["effective_level"] == 4  # 3 + 1

    # Rebuke should still proceed (evil cleric → rebuked, not turned)
    rebuke_events = [e for e in events if e.event_type == "undead_rebuked"]
    assert len(rebuke_events) == 1, (
        f"Expected rebuke event; got: {[e.event_type for e in events]}"
    )


# ===========================================================================
# ITN-007: Improved Turning + Extra Turning — TURN_UNDEAD_USES_MAX unaffected
# ===========================================================================

def test_itn007_turn_uses_max_not_modified():
    """ITN-007: Improved Turning does not alter TURN_UNDEAD_USES_MAX.

    Forward-compatibility guard for Batch S WO3 (Extra Turning).
    The improved_turning logic must not touch TURN_UNDEAD_USES_MAX.
    """
    initial_uses_max = 5
    cleric = _cleric(cleric_level=5, cha_mod=2, feats=["improved_turning"],
                     turn_uses_max=initial_uses_max)
    skeleton = _undead("skeleton", hd=1, hp=6)
    ws = _world({"cleric": cleric, "skeleton": skeleton})
    rng = _FixedRNG(d6_val=3)

    intent = TurnUndeadIntent(cleric_id="cleric", target_ids=["skeleton"])
    events = resolve_turn_undead(intent, ws, rng, next_event_id=1, timestamp=0.0)
    ws_after = apply_turn_undead_events(events, ws)

    cleric_after = ws_after.entities["cleric"]
    # TURN_UNDEAD_USES_MAX must be unchanged
    assert cleric_after.get(EF.TURN_UNDEAD_USES_MAX) == initial_uses_max, (
        f"TURN_UNDEAD_USES_MAX was modified: expected {initial_uses_max}, "
        f"got {cleric_after.get(EF.TURN_UNDEAD_USES_MAX)}"
    )


# ===========================================================================
# ITN-008: Extra Turning uses count unchanged by ITN commit (ETN regression guard)
# ===========================================================================

def test_itn008_regression_extra_turning_uses_not_modified():
    """ITN-008: Improved Turning logic does not produce any extra_turning events.

    ETN regression guard: ITN commit must not emit extra_turning_* events
    or modify any extra turning-related state.
    """
    cleric = _cleric(cleric_level=5, cha_mod=2, feats=["improved_turning"])
    skeleton = _undead("skeleton", hd=1, hp=6)
    ws = _world({"cleric": cleric, "skeleton": skeleton})
    rng = _FixedRNG(d6_val=3)

    intent = TurnUndeadIntent(cleric_id="cleric", target_ids=["skeleton"])
    events = resolve_turn_undead(intent, ws, rng, next_event_id=1, timestamp=0.0)

    # No extra_turning events of any kind
    extra_events = [e for e in events if "extra_turning" in e.event_type]
    assert extra_events == [], (
        f"Unexpected extra_turning events from ITN commit: {[e.event_type for e in extra_events]}"
    )
    # TURN_UNDEAD_USES_MAX also must not appear in any event payload modification
    use_spent = [e for e in events if e.event_type == "turn_undead_use_spent"]
    assert len(use_spent) == 1, "Should spend exactly 1 regular turn use"
    assert use_spent[0].payload["uses_remaining"] == 4, (
        f"Expected uses_remaining=4 (5-1), got {use_spent[0].payload['uses_remaining']}"
    )
