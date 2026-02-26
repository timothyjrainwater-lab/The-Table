"""Gate tests: WO-ENGINE-CONCENTRATION-DAMAGE-001 — Caster took damage this turn (PHB p.69/p.175).

DC = 10 + damage taken + spell level. Fires before spell effect resolves.
Failure: spell lost (concentration_failed event). Success: concentration_maintained event.

Gate label: ENGINE-CONCENTRATION-DAMAGE-001
KERNEL-03 (Constraint Algebra) touch.
"""

import pytest
from copy import deepcopy
from unittest.mock import MagicMock

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.core.spell_resolver import SpellCastIntent
from aidm.core.play_loop import _resolve_spell_cast


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_caster(caster_id: str = "caster_01", conc_bonus: int = 0) -> dict:
    return {
        EF.ENTITY_ID: caster_id,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.TEAM: "players",
        EF.DEFEATED: False,
        EF.CONDITIONS: {},
        EF.CLASS_LEVELS: {"wizard": 5},
        EF.SPELL_SLOTS: {3: 3, 1: 4, 2: 3},
        EF.SPELLS_PREPARED: {3: ["fireball"], 1: ["magic_missile"], 2: ["scorching_ray"]},
        EF.CASTER_CLASS: "wizard",
        EF.INT_MOD: 3,
        EF.WIS_MOD: 0,
        EF.FEATS: [],
        EF.CONCENTRATION_BONUS: conc_bonus,
        EF.POSITION: {"x": 0, "y": 0},
    }


def _make_world(caster_id: str = "caster_01", conc_bonus: int = 0) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={caster_id: _make_caster(caster_id, conc_bonus=conc_bonus)},
        active_combat={
            "initiative_order": [caster_id],
            "aoo_used_this_round": [],
            "flat_footed_actors": [],
            "feint_flat_footed": [],
        },
    )


def _make_rng(d20_roll: int = 15):
    rng = MagicMock()
    stream = MagicMock()
    stream.randint.return_value = d20_roll
    rng.stream.return_value = stream
    return rng


def _run_with_damage(spell_id: str, damage_taken: int, conc_bonus: int = 0, d20_roll: int = 15):
    """Run _resolve_spell_cast with damage_taken_this_turn set."""
    caster_id = "caster_01"
    ws = _make_world(caster_id, conc_bonus=conc_bonus)
    intent = SpellCastIntent(caster_id=caster_id, spell_id=spell_id)
    rng = _make_rng(d20_roll)
    events, ws_after, narration = _resolve_spell_cast(
        intent=intent,
        world_state=ws,
        rng=rng,
        grid=None,
        next_event_id=0,
        timestamp=0.0,
        turn_index=0,
        damage_taken_this_turn=damage_taken,
    )
    return events, narration


# ---------------------------------------------------------------------------
# CD-001: Took damage; fails Concentration → spell lost
# ---------------------------------------------------------------------------

def test_cd_001_took_damage_fails_concentration():
    """CD-001: Caster took 15 damage; casts fireball (3rd level); fails → concentration_failed."""
    # DC = 10 + 15 + 3 = 28. conc_bonus=0, d20=5 → total=5 < 28. Fail.
    events, narration = _run_with_damage("fireball", damage_taken=15, conc_bonus=0, d20_roll=5)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" in event_types, \
        f"CD-001: Expected concentration_failed; got {event_types}"
    failed = next(e for e in events if e.event_type == "concentration_failed")
    assert failed.payload["reason"] == "took_damage", \
        f"CD-001: Wrong reason: {failed.payload}"
    assert narration == "concentration_failed", \
        f"CD-001: Expected narration='concentration_failed'; got '{narration}'"


# ---------------------------------------------------------------------------
# CD-002: Took damage; succeeds Concentration → spell resolves
# ---------------------------------------------------------------------------

def test_cd_002_took_damage_succeeds_concentration():
    """CD-002: Caster took 15 damage; casts fireball; succeeds → concentration_maintained."""
    # DC = 28. conc_bonus=20, d20=10 → total=30 ≥ 28. Success.
    events, narration = _run_with_damage("fireball", damage_taken=15, conc_bonus=20, d20_roll=10)
    event_types = [e.event_type for e in events]
    assert "concentration_maintained" in event_types, \
        f"CD-002: Expected concentration_maintained; got {event_types}"
    assert "concentration_failed" not in event_types, \
        f"CD-002: concentration_failed should not fire on success"


# ---------------------------------------------------------------------------
# CD-003: No damage → no Concentration check
# ---------------------------------------------------------------------------

def test_cd_003_no_damage_no_check():
    """CD-003: Caster took 0 damage; no Concentration check triggered."""
    events, narration = _run_with_damage("fireball", damage_taken=0, conc_bonus=0, d20_roll=1)
    event_types = [e.event_type for e in events]
    conc_events = [e for e in events if "concentration" in e.event_type]
    assert len(conc_events) == 0, \
        f"CD-003: Concentration events should not fire at 0 damage; got {event_types}"


# ---------------------------------------------------------------------------
# CD-004: DC formula: 15 damage + 3rd level = DC 28
# ---------------------------------------------------------------------------

def test_cd_004_dc_formula_15_damage_3rd_level():
    """CD-004: DC = 10 + 15 + 3 = 28 confirmed in payload."""
    # Force fail so we get the payload
    events, narration = _run_with_damage("fireball", damage_taken=15, conc_bonus=0, d20_roll=1)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" in event_types, \
        f"CD-004: Expected concentration_failed to read DC; got {event_types}"
    failed = next(e for e in events if e.event_type == "concentration_failed")
    assert failed.payload["dc"] == 28, \
        f"CD-004: Expected DC=28; got {failed.payload['dc']}"
    assert failed.payload["damage_taken"] == 15, \
        f"CD-004: Expected damage_taken=15; got {failed.payload}"


# ---------------------------------------------------------------------------
# CD-005: DC formula: 5 damage + 1st level = DC 16
# ---------------------------------------------------------------------------

def test_cd_005_dc_formula_5_damage_1st_level():
    """CD-005: DC = 10 + 5 + 1 = 16 for magic_missile."""
    events, narration = _run_with_damage("magic_missile", damage_taken=5, conc_bonus=0, d20_roll=1)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" in event_types, \
        f"CD-005: Expected concentration_failed; got {event_types}"
    failed = next(e for e in events if e.event_type == "concentration_failed")
    assert failed.payload["dc"] == 16, \
        f"CD-005: Expected DC=16; got {failed.payload['dc']}"


# ---------------------------------------------------------------------------
# CD-006: High conc bonus; 10 damage + 2nd level → DC 22; can still fail
# ---------------------------------------------------------------------------

def test_cd_006_high_conc_can_still_fail():
    """CD-006: conc_bonus=12; 10 damage + 2nd level (DC 22); d20=1 → total=13 < 22."""
    from aidm.data.spell_definitions import SPELL_REGISTRY
    spell = SPELL_REGISTRY.get("scorching_ray")
    if spell is None:
        pytest.skip("scorching_ray not in registry")
    events, narration = _run_with_damage("scorching_ray", damage_taken=10, conc_bonus=12, d20_roll=1)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" in event_types, \
        f"CD-006: Expected concentration_failed; got {event_types}"
    failed = next(e for e in events if e.event_type == "concentration_failed")
    assert failed.payload["dc"] == 22, \
        f"CD-006: Expected DC=22; got {failed.payload['dc']}"


# ---------------------------------------------------------------------------
# CD-007: No CONCENTRATION_BONUS field → treat as 0, no crash
# ---------------------------------------------------------------------------

def test_cd_007_no_conc_bonus_field_no_crash():
    """CD-007: Caster with no CONCENTRATION_BONUS field; took 10 damage → no crash, treated as 0."""
    caster_id = "caster_01"
    ws = _make_world(caster_id, conc_bonus=0)
    # Remove the concentration bonus field entirely
    del ws.entities[caster_id][EF.CONCENTRATION_BONUS]
    intent = SpellCastIntent(caster_id=caster_id, spell_id="fireball")
    rng = _make_rng(d20_roll=1)
    events, ws_after, narration = _resolve_spell_cast(
        intent=intent, world_state=ws, rng=rng,
        grid=None, next_event_id=0, timestamp=0.0, turn_index=0,
        damage_taken_this_turn=10,
    )
    event_types = [e.event_type for e in events]
    # Should either fail (with correct DC) or succeed — just no crash
    # DC = 10 + 10 + 3 = 23. d20=1 + 0 = 1 < 23 → fail
    assert "concentration_failed" in event_types, \
        f"CD-007: Expected concentration_failed (no bonus = 0); got {event_types}"


# ---------------------------------------------------------------------------
# CD-008: Multiple hits same turn → total damage used for DC
# ---------------------------------------------------------------------------

def test_cd_008_multiple_hits_total_damage():
    """CD-008: 10 + 8 = 18 damage total; 2nd level spell → DC = 10 + 18 + 2 = 30."""
    from aidm.data.spell_definitions import SPELL_REGISTRY
    spell = SPELL_REGISTRY.get("scorching_ray")
    if spell is None:
        pytest.skip("scorching_ray not in registry")
    # damage_taken_this_turn = 18 (caller sums; _resolve_spell_cast receives total)
    events, narration = _run_with_damage("scorching_ray", damage_taken=18, conc_bonus=0, d20_roll=1)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" in event_types, \
        f"CD-008: Expected concentration_failed; got {event_types}"
    failed = next(e for e in events if e.event_type == "concentration_failed")
    assert failed.payload["dc"] == 30, \
        f"CD-008: Expected DC=30 (10+18+2); got {failed.payload['dc']}"
    assert failed.payload["damage_taken"] == 18, \
        f"CD-008: Expected damage_taken=18; got {failed.payload}"
