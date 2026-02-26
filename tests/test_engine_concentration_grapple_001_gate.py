"""Gate tests: WO-ENGINE-CONCENTRATION-GRAPPLE-001 — Grappled/entangled caster Concentration (PHB p.175).

GRAPPLED/GRAPPLING: DC 20 + spell level. ENTANGLED: DC 15 + spell level.
Both are checks — spell can succeed. PINNED blocks somatic (separate WO).

Gate label: ENGINE-CONCENTRATION-GRAPPLE-001
KERNEL-02 (Containment Topology) touch.
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.core.spell_resolver import SpellCastIntent
from aidm.core.play_loop import _resolve_spell_cast


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_caster(caster_id: str = "caster_01", conditions: dict = None,
                 conc_bonus: int = 0) -> dict:
    return {
        EF.ENTITY_ID: caster_id,
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.TEAM: "players",
        EF.DEFEATED: False,
        EF.CONDITIONS: conditions or {},
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


def _make_world(caster_id: str = "caster_01", conditions: dict = None,
                conc_bonus: int = 0) -> WorldState:
    return WorldState(
        ruleset_version="3.5e",
        entities={caster_id: _make_caster(caster_id, conditions=conditions,
                                          conc_bonus=conc_bonus)},
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


def _run_grapple_conc(spell_id: str, conditions: dict, conc_bonus: int = 0, d20_roll: int = 15):
    caster_id = "caster_01"
    ws = _make_world(caster_id, conditions=conditions, conc_bonus=conc_bonus)
    intent = SpellCastIntent(caster_id=caster_id, spell_id=spell_id)
    rng = _make_rng(d20_roll)
    events, ws_after, narration = _resolve_spell_cast(
        intent=intent, world_state=ws, rng=rng,
        grid=None, next_event_id=0, timestamp=0.0, turn_index=0,
    )
    return events, narration


# ---------------------------------------------------------------------------
# CG-001: GRAPPLED; 2nd level spell; fails Concentration
# ---------------------------------------------------------------------------

def test_cg_001_grappled_fails_concentration():
    """CG-001: GRAPPLED caster; 2nd level spell; fails → concentration_failed, reason=grappled, DC=22."""
    from aidm.data.spell_definitions import SPELL_REGISTRY
    spell = SPELL_REGISTRY.get("scorching_ray")
    if spell is None:
        pytest.skip("scorching_ray not in registry")
    # DC = 20 + 2 = 22. conc_bonus=0, d20=1 → total=1 < 22.
    events, narration = _run_grapple_conc("scorching_ray",
                                          conditions={"grappled": {}},
                                          conc_bonus=0, d20_roll=1)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" in event_types, \
        f"CG-001: Expected concentration_failed; got {event_types}"
    failed = next(e for e in events if e.event_type == "concentration_failed")
    assert failed.payload["reason"] == "grappled", \
        f"CG-001: Expected reason='grappled'; got {failed.payload['reason']}"
    assert failed.payload["dc"] == 22, \
        f"CG-001: Expected DC=22; got {failed.payload['dc']}"


# ---------------------------------------------------------------------------
# CG-002: GRAPPLED; 2nd level spell; succeeds Concentration → spell resolves
# ---------------------------------------------------------------------------

def test_cg_002_grappled_succeeds_concentration():
    """CG-002: GRAPPLED caster; 2nd level spell; succeeds → no concentration_failed."""
    from aidm.data.spell_definitions import SPELL_REGISTRY
    spell = SPELL_REGISTRY.get("scorching_ray")
    if spell is None:
        pytest.skip("scorching_ray not in registry")
    # DC = 22. conc_bonus=10, d20=15 → total=25 ≥ 22. Success.
    events, narration = _run_grapple_conc("scorching_ray",
                                          conditions={"grappled": {}},
                                          conc_bonus=10, d20_roll=15)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" not in event_types, \
        f"CG-002: concentration_failed should not fire on success"
    assert "concentration_success" in event_types, \
        f"CG-002: Expected concentration_success; got {event_types}"


# ---------------------------------------------------------------------------
# CG-003: ENTANGLED; 1st level spell; fails Concentration
# ---------------------------------------------------------------------------

def test_cg_003_entangled_fails_concentration():
    """CG-003: ENTANGLED caster; 1st level spell; fails → concentration_failed, reason=entangled, DC=16."""
    # DC = 15 + 1 = 16. conc_bonus=0, d20=1 → total=1 < 16.
    events, narration = _run_grapple_conc("magic_missile",
                                          conditions={"entangled": {}},
                                          conc_bonus=0, d20_roll=1)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" in event_types, \
        f"CG-003: Expected concentration_failed; got {event_types}"
    failed = next(e for e in events if e.event_type == "concentration_failed")
    assert failed.payload["reason"] == "entangled", \
        f"CG-003: Expected reason='entangled'; got {failed.payload['reason']}"
    assert failed.payload["dc"] == 16, \
        f"CG-003: Expected DC=16; got {failed.payload['dc']}"


# ---------------------------------------------------------------------------
# CG-004: ENTANGLED; succeeds Concentration → spell resolves
# ---------------------------------------------------------------------------

def test_cg_004_entangled_succeeds_concentration():
    """CG-004: ENTANGLED caster; succeeds Concentration → concentration_success event."""
    # DC = 16. conc_bonus=10, d20=10 → total=20 ≥ 16. Success.
    events, narration = _run_grapple_conc("magic_missile",
                                          conditions={"entangled": {}},
                                          conc_bonus=10, d20_roll=10)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" not in event_types, \
        f"CG-004: concentration_failed should not fire on success"
    assert "concentration_success" in event_types, \
        f"CG-004: Expected concentration_success; got {event_types}"


# ---------------------------------------------------------------------------
# CG-005: No GRAPPLED/ENTANGLED → no grapple Concentration check
# ---------------------------------------------------------------------------

def test_cg_005_no_condition_no_check():
    """CG-005: Caster with no grapple/entangle conditions → no grapple Concentration check."""
    events, narration = _run_grapple_conc("fireball", conditions={}, conc_bonus=0, d20_roll=1)
    conc_events = [e for e in events if e.event_type in ("concentration_failed", "concentration_success")
                   and e.payload.get("reason") in ("grappled", "entangled")]
    assert len(conc_events) == 0, \
        f"CG-005: Grapple/entangle concentration events should not fire without condition; got {conc_events}"


# ---------------------------------------------------------------------------
# CG-006: DC formula: GRAPPLED + 3rd level = DC 23
# ---------------------------------------------------------------------------

def test_cg_006_dc_formula_grappled_3rd_level():
    """CG-006: GRAPPLED + fireball (3rd level) → DC = 20 + 3 = 23."""
    events, narration = _run_grapple_conc("fireball",
                                          conditions={"grappled": {}},
                                          conc_bonus=0, d20_roll=1)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" in event_types, \
        f"CG-006: Expected concentration_failed; got {event_types}"
    failed = next(e for e in events if e.event_type == "concentration_failed")
    assert failed.payload["dc"] == 23, \
        f"CG-006: Expected DC=23; got {failed.payload['dc']}"


# ---------------------------------------------------------------------------
# CG-007: DC formula: ENTANGLED + 3rd level = DC 18
# ---------------------------------------------------------------------------

def test_cg_007_dc_formula_entangled_3rd_level():
    """CG-007: ENTANGLED + fireball (3rd level) → DC = 15 + 3 = 18."""
    events, narration = _run_grapple_conc("fireball",
                                          conditions={"entangled": {}},
                                          conc_bonus=0, d20_roll=1)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" in event_types, \
        f"CG-007: Expected concentration_failed; got {event_types}"
    failed = next(e for e in events if e.event_type == "concentration_failed")
    assert failed.payload["dc"] == 18, \
        f"CG-007: Expected DC=18; got {failed.payload['dc']}"


# ---------------------------------------------------------------------------
# CG-008: GRAPPLING (initiating grapple) → same check as GRAPPLED
# ---------------------------------------------------------------------------

def test_cg_008_grappling_same_as_grappled():
    """CG-008: GRAPPLING condition → same Concentration check as GRAPPLED (DC 20 + spell level)."""
    # PHB p.175: grappled (as initiator or defender) both apply.
    events, narration = _run_grapple_conc("fireball",
                                          conditions={"grappling": {}},
                                          conc_bonus=0, d20_roll=1)
    event_types = [e.event_type for e in events]
    assert "concentration_failed" in event_types, \
        f"CG-008: Expected concentration_failed for grappling; got {event_types}"
    failed = next(e for e in events if e.event_type == "concentration_failed")
    assert failed.payload["reason"] == "grappled", \
        f"CG-008: Expected reason='grappled' for grappling condition; got {failed.payload['reason']}"
    assert failed.payload["dc"] == 23, \
        f"CG-008: Expected DC=23 (20+3); got {failed.payload['dc']}"
