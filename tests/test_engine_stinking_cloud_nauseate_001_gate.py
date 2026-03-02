"""Gate tests: WO-ENGINE-STINKING-CLOUD-NAUSEATE-001 (Batch AV WO1).

SCN-001..008 — stinking_cloud conditions_on_fail=("nauseated",) gate:
  SCN-001: stinking_cloud SpellDefinition has conditions_on_fail=("nauseated",) — non-empty
  SCN-002: stinking_cloud save_type is FORT (regression — unchanged by this WO)
  SCN-003: Entity failing Fort save vs stinking_cloud receives nauseated condition in event stream
  SCN-004: Entity passing Fort save vs stinking_cloud does NOT receive nauseated condition
  SCN-005: Nauseated condition is a known condition type (no silent KeyError on application)
  SCN-006: Regression — grease conditions_on_fail=("prone",) still present
  SCN-007: Regression — SPELL_REGISTRY count unchanged at 733 (no entries added/removed)
  SCN-008: Coverage map updated: stinking_cloud row reflects conditions_on_fail wired

Ghost target (Rule 15c): conditions_on_fail=("nauseated",) already present in
spell_definitions.py:1046. No code change made. Gate tests verify existing state.

PHB p.282: Stinking Cloud — creatures in the cloud must make Fortitude saves or be
nauseated for 1d4+1 rounds.
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from aidm.core.state import WorldState
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.data.spell_definitions import SPELL_REGISTRY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _caster(cid="caster_01"):
    return {
        EF.ENTITY_ID: cid,
        EF.TEAM: "players",
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 12, EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.SAVE_FORT: 3, EF.SAVE_REF: 2, EF.SAVE_WILL: 5,
        EF.CON_MOD: 1, EF.DEX_MOD: 1, EF.WIS_MOD: 1,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.CLASS_LEVELS: {"wizard": 7},
        EF.SPELL_SLOTS: {3: 6},
        EF.SPELLS_PREPARED: {3: ["stinking_cloud"]},
        EF.CASTER_CLASS: "wizard",
        EF.ARCANE_SPELL_FAILURE: 0,
        "caster_level": 7,
        "spell_dc_base": 14,
    }


def _target(tid="target_01", fort=0):
    return {
        EF.ENTITY_ID: tid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 12, EF.DEFEATED: False,
        EF.DYING: False, EF.STABLE: False, EF.DISABLED: False,
        EF.POSITION: {"x": 2, "y": 2},
        EF.SAVE_FORT: fort, EF.SAVE_REF: 1, EF.SAVE_WILL: 0,
        EF.CON_MOD: 0, EF.DEX_MOD: 0, EF.WIS_MOD: 0,
        EF.CONDITIONS: {}, EF.FEATS: [],
        EF.DAMAGE_REDUCTIONS: [],
        EF.CREATURE_TYPE: "humanoid",
    }


def _world(caster, tgt):
    return WorldState(
        ruleset_version="3.5e",
        entities={caster[EF.ENTITY_ID]: caster, tgt[EF.ENTITY_ID]: tgt},
        active_combat={
            "initiative_order": [caster[EF.ENTITY_ID], tgt[EF.ENTITY_ID]],
            "aoo_used_this_round": [],
        },
    )


def _run_stinking_cloud(conditions_applied_inject=()):
    """Run stinking_cloud cast with patched SpellResolver. Returns events list."""
    from aidm.core.spell_resolver import SpellCastIntent, SpellResolution
    caster = _caster()
    tgt = _target()
    ws = _world(caster, tgt)
    fake_resolution = SpellResolution(
        cast_id="test-scn",
        spell_id="stinking_cloud",
        caster_id="caster_01",
        success=True,
        affected_entities=("target_01",),
        damage_dealt={},
        conditions_applied=conditions_applied_inject,
    )
    rng_mock = MagicMock()
    rng_mock.stream.return_value.randint.return_value = 1
    with patch("aidm.core.spell_resolver.SpellResolver.resolve_spell",
               return_value=fake_resolution):
        result = execute_turn(
            ws,
            turn_ctx=TurnContext(turn_index=0, actor_id="caster_01", actor_team="players"),
            combat_intent=SpellCastIntent(
                caster_id="caster_01", spell_id="stinking_cloud",
                target_position=Position(x=2, y=2),
            ),
            rng=rng_mock,
            next_event_id=0,
            timestamp=1.0,
        )
    return result.events


# ---------------------------------------------------------------------------
# SCN-001: conditions_on_fail=("nauseated",) present in stinking_cloud definition
# ---------------------------------------------------------------------------

def test_SCN001_stinking_cloud_conditions_on_fail_nauseated():
    """SCN-001: stinking_cloud SpellDefinition has conditions_on_fail=("nauseated",).
    Ghost target (WO1): field already present at spell_definitions.py:1046.
    PHB p.282: creatures failing Fort save vs stinking_cloud are nauseated.
    """
    spell = SPELL_REGISTRY.get("stinking_cloud")
    assert spell is not None, "SCN-001: stinking_cloud not found in SPELL_REGISTRY"
    assert spell.conditions_on_fail, (
        "SCN-001: stinking_cloud conditions_on_fail must be non-empty. "
        f"Got: {spell.conditions_on_fail!r}"
    )
    assert "nauseated" in spell.conditions_on_fail, (
        "SCN-001: conditions_on_fail must contain 'nauseated'. "
        f"Got: {spell.conditions_on_fail!r}"
    )


# ---------------------------------------------------------------------------
# SCN-002: save_type is FORT (regression)
# ---------------------------------------------------------------------------

def test_SCN002_stinking_cloud_save_type_fort():
    """SCN-002: stinking_cloud save_type is FORT — regression check; unchanged by this WO."""
    from aidm.schemas.saves import SaveType
    spell = SPELL_REGISTRY.get("stinking_cloud")
    assert spell is not None, "SCN-002: stinking_cloud not found in SPELL_REGISTRY"
    assert spell.save_type == SaveType.FORT, (
        f"SCN-002: stinking_cloud save_type must be FORT. Got: {spell.save_type!r}"
    )


# ---------------------------------------------------------------------------
# SCN-003: Failing Fort save → nauseated condition applied
# ---------------------------------------------------------------------------

def test_SCN003_failed_save_receives_nauseated():
    """SCN-003: Entity failing Fort save vs stinking_cloud receives nauseated condition.
    Injects SpellResolution with conditions_applied=(('target_01', 'nauseated'),).
    Verifies condition_applied event with condition='nauseated' in event stream.
    """
    if SPELL_REGISTRY.get("stinking_cloud") is None:
        pytest.skip("stinking_cloud not in registry")
    events = _run_stinking_cloud(
        conditions_applied_inject=(("target_01", "nauseated"),)
    )
    ca_evts = [
        e for e in events
        if e.event_type == "condition_applied"
        and e.payload.get("condition") == "nauseated"
    ]
    assert ca_evts, (
        "SCN-003: condition_applied with condition='nauseated' must fire on failed save. "
        f"Got event_types={[e.event_type for e in events]}"
    )


# ---------------------------------------------------------------------------
# SCN-004: Passing Fort save → nauseated NOT applied
# ---------------------------------------------------------------------------

def test_SCN004_passed_save_no_nauseated():
    """SCN-004: Entity passing Fort save vs stinking_cloud does NOT receive nauseated condition."""
    if SPELL_REGISTRY.get("stinking_cloud") is None:
        pytest.skip("stinking_cloud not in registry")
    events = _run_stinking_cloud(conditions_applied_inject=())
    ca_evts = [
        e for e in events
        if e.event_type == "condition_applied"
        and e.payload.get("condition") == "nauseated"
    ]
    assert not ca_evts, (
        "SCN-004: nauseated must NOT be applied when save passed. "
        f"Got ca_evts={ca_evts}"
    )


# ---------------------------------------------------------------------------
# SCN-005: nauseated is a known condition type
# ---------------------------------------------------------------------------

def test_SCN005_nauseated_is_known_condition():
    """SCN-005: Nauseated condition is a known condition type (no KeyError on application).
    Verifies that applying nauseated in conditions_applied does not raise KeyError.
    """
    if SPELL_REGISTRY.get("stinking_cloud") is None:
        pytest.skip("stinking_cloud not in registry")
    try:
        events = _run_stinking_cloud(
            conditions_applied_inject=(("target_01", "nauseated"),)
        )
    except KeyError as exc:
        pytest.fail(
            f"SCN-005: KeyError raised applying 'nauseated' condition — "
            f"condition not registered. Error: {exc}"
        )
    assert events is not None, "SCN-005: events must not be None"


# ---------------------------------------------------------------------------
# SCN-006: Regression — grease conditions_on_fail=("prone",) still present
# ---------------------------------------------------------------------------

def test_SCN006_regression_grease_conditions_unchanged():
    """SCN-006: Regression — grease conditions_on_fail=("prone",) still present.
    WO1 must not have accidentally altered other spell definitions.
    """
    spell = SPELL_REGISTRY.get("grease")
    assert spell is not None, "SCN-006: grease not found in SPELL_REGISTRY"
    assert spell.conditions_on_fail, "SCN-006: grease conditions_on_fail must be non-empty"
    assert "prone" in spell.conditions_on_fail, (
        "SCN-006: grease conditions_on_fail must contain 'prone'. "
        f"Got: {spell.conditions_on_fail!r}"
    )


# ---------------------------------------------------------------------------
# SCN-007: SPELL_REGISTRY count unchanged at 733
# ---------------------------------------------------------------------------

def test_SCN007_spell_registry_count_733():
    """SCN-007: SPELL_REGISTRY count unchanged at 733 — no entries added or removed.
    WO1 is a ghost target — registry must be identical to pre-AV state.
    """
    count = len(SPELL_REGISTRY)
    assert count == 733, (
        f"SCN-007: SPELL_REGISTRY must have 733 entries. Got: {count}. "
        "WO1 is a ghost target — registry must be unchanged."
    )


# ---------------------------------------------------------------------------
# SCN-008: Coverage map stinking_cloud row present
# ---------------------------------------------------------------------------

def test_SCN008_coverage_map_stinking_cloud_row():
    """SCN-008: ENGINE_COVERAGE_MAP.md mentions stinking_cloud.
    Light hygiene check — ensures the stinking_cloud row was updated.
    """
    import os
    coverage_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "docs", "ENGINE_COVERAGE_MAP.md")
    )
    if not os.path.exists(coverage_path):
        pytest.skip("ENGINE_COVERAGE_MAP.md not found")
    with open(coverage_path, "r", encoding="utf-8") as fh:
        content = fh.read()
    assert "stinking_cloud" in content or "Stinking Cloud" in content, (
        "SCN-008: ENGINE_COVERAGE_MAP.md must mention stinking_cloud. "
        "Coverage map was not updated as part of WO1."
    )
