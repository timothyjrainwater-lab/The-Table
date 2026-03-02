"""Gate tests: WO-ENGINE-MASSIVE-DAMAGE-THRESHOLD-001 (Batch AV WO2).

MDT-001..008 — Massive damage threshold max(hp//2, 50) gate:
  MDT-001: Entity with HP_MAX=40 — threshold=max(20,50)=50 — damage=49 does NOT trigger save
  MDT-002: Entity with HP_MAX=40 — threshold=50 — damage=50 triggers Fort save DC 15
  MDT-003: Entity with HP_MAX=120 — threshold=max(60,50)=60 — damage=59 does NOT trigger save
  MDT-004: Entity with HP_MAX=120 — threshold=60 — damage=60 triggers Fort save DC 15
  MDT-005: Entity with HP_MAX=120 — damage=50 does NOT trigger save (below half-HP threshold)
  MDT-006: Fort save DC is exactly 15 (PHB p.145)
  MDT-007: Failing the save → new_hp=-10 (instant death)
  MDT-008: Passing the save — no death, combat continues

Key distinguishing cases (static-50 vs formula):
  MDT-003: damage=59 > 50, but formula threshold=60 → correct: no save
           (static-50 would MISS this: 59 >= 50 would incorrectly trigger)
  MDT-005: damage=50 == static threshold, but formula threshold=60 → correct: no save
           (static-50 WOULD incorrectly trigger for high-HP entity)

FINDING-ENGINE-MASSIVE-DAMAGE-THRESHOLD-HALF-HP-001 closed.
Formula: max(entity_max_hp // 2, 50) using EF.HP_MAX.

PHB p.145: "If you ever sustain a single attack that deals an amount of damage equal to half
your total hit points (minimum 50 points of damage), you must make a Fortitude saving throw
(DC 15) or die."
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from aidm.core.state import WorldState
from aidm.core.play_loop import execute_turn, TurnContext
from aidm.schemas.entity_fields import EF
from aidm.schemas.position import Position
from aidm.data.spell_definitions import SPELL_REGISTRY
from aidm.core.spell_resolver import SpellCastIntent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _caster():
    return {
        EF.ENTITY_ID: "wizard_01",
        EF.TEAM: "players",
        EF.HP_CURRENT: 30, EF.HP_MAX: 30, EF.AC: 12, EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
        EF.SAVE_FORT: 2, EF.SAVE_REF: 2, EF.SAVE_WILL: 5,
        EF.CON_MOD: 1, EF.DEX_MOD: 1, EF.WIS_MOD: 1,
        EF.CONDITIONS: {}, EF.FEATS: [], EF.TEMPORARY_MODIFIERS: {},
        EF.CLASS_LEVELS: {"wizard": 9},
        EF.SPELL_SLOTS: {3: 4},
        EF.SPELLS_PREPARED: {3: ["fireball"]},
        EF.CASTER_CLASS: "wizard",
        EF.ARCANE_SPELL_FAILURE: 0,
        "caster_level": 9,
        "spell_dc_base": 14,
    }


def _target(hp, fort=0):
    return {
        EF.ENTITY_ID: "target_01",
        EF.TEAM: "monsters",
        EF.HP_CURRENT: hp, EF.HP_MAX: hp, EF.AC: 12, EF.DEFEATED: False,
        EF.DYING: False, EF.STABLE: False, EF.DISABLED: False,
        EF.POSITION: {"x": 5, "y": 5},
        EF.SAVE_FORT: fort, EF.SAVE_REF: 0, EF.SAVE_WILL: 0,
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


def _inject_spell_damage(hp, damage, fort_roll=1, fort_bonus=0):
    """Run execute_turn with injected spell damage. Returns (events, updated_state).

    Patches SpellResolver.resolve_spell to inject exact damage_dealt without
    needing spell-specific targeting or AoE resolution.
    """
    from aidm.core.spell_resolver import SpellResolution
    caster = _caster()
    tgt = _target(hp=hp, fort=fort_bonus)
    ws = _world(caster, tgt)
    fake_resolution = SpellResolution(
        cast_id="test-mdt",
        spell_id="fireball",
        caster_id="wizard_01",
        success=True,
        affected_entities=("target_01",),
        damage_dealt={"target_01": damage},
    )
    rng_mock = MagicMock()
    rng_mock.stream.return_value.randint.return_value = fort_roll
    with patch("aidm.core.spell_resolver.SpellResolver.resolve_spell",
               return_value=fake_resolution):
        result = execute_turn(
            ws,
            turn_ctx=TurnContext(turn_index=0, actor_id="wizard_01", actor_team="players"),
            combat_intent=SpellCastIntent(
                caster_id="wizard_01", spell_id="fireball",
                target_position=Position(x=5, y=5),
            ),
            rng=rng_mock,
            next_event_id=0,
            timestamp=1.0,
        )
    return result.events, result.world_state


def _massive_damage_saves(events):
    """Return save_rolled events from the massive damage path (dc=15, save_type=fortitude)."""
    return [
        e for e in events
        if e.event_type == "save_rolled"
        and e.payload.get("dc") == 15
        and e.payload.get("save_type") == "fortitude"
    ]


# ---------------------------------------------------------------------------
# MDT-001: 40 HP entity, damage=49 → no save (threshold=50)
# ---------------------------------------------------------------------------

def test_MDT001_40hp_damage49_no_save():
    """MDT-001: Entity HP_MAX=40, threshold=max(20,50)=50; damage=49 does NOT trigger save.
    PHB p.145: 49 < 50 → no Fort save required.
    """
    events, _ = _inject_spell_damage(hp=40, damage=49)
    md_saves = _massive_damage_saves(events)
    assert not md_saves, (
        f"MDT-001: damage=49 must NOT trigger massive damage save (threshold=50). "
        f"Got {len(md_saves)} save event(s). "
        f"Event types: {[e.event_type for e in events]}"
    )


# ---------------------------------------------------------------------------
# MDT-002: 40 HP entity, damage=50 → save triggers (threshold=50)
# ---------------------------------------------------------------------------

def test_MDT002_40hp_damage50_save_triggers():
    """MDT-002: Entity HP_MAX=40, threshold=max(20,50)=50; damage=50 triggers Fort save DC 15."""
    events, _ = _inject_spell_damage(hp=40, damage=50)
    md_saves = _massive_damage_saves(events)
    assert md_saves, (
        f"MDT-002: damage=50 must trigger massive damage save (threshold=50). "
        f"Got no save events. Event types: {[e.event_type for e in events]}"
    )


# ---------------------------------------------------------------------------
# MDT-003: 120 HP entity, damage=59 → no save (threshold=60)
# ---------------------------------------------------------------------------

def test_MDT003_120hp_damage59_no_save():
    """MDT-003: Entity HP_MAX=120, threshold=max(60,50)=60; damage=59 does NOT trigger save.

    KEY TEST: Distinguishes correct formula from static-50.
    Static-50 threshold WOULD incorrectly trigger (59 >= 50).
    Correct formula: threshold=60 → 59 < 60 → no save.
    """
    events, _ = _inject_spell_damage(hp=120, damage=59)
    md_saves = _massive_damage_saves(events)
    assert not md_saves, (
        f"MDT-003: damage=59 must NOT trigger massive damage save (threshold=60 for HP_MAX=120). "
        f"Got {len(md_saves)} save event(s). "
        f"If this fails: threshold is static-50 not max(hp//2,50). "
        f"Event types: {[e.event_type for e in events]}"
    )


# ---------------------------------------------------------------------------
# MDT-004: 120 HP entity, damage=60 → save triggers (threshold=60)
# ---------------------------------------------------------------------------

def test_MDT004_120hp_damage60_save_triggers():
    """MDT-004: Entity HP_MAX=120, threshold=max(60,50)=60; damage=60 triggers Fort save DC 15."""
    events, _ = _inject_spell_damage(hp=120, damage=60)
    md_saves = _massive_damage_saves(events)
    assert md_saves, (
        f"MDT-004: damage=60 must trigger massive damage save (threshold=60 for HP_MAX=120). "
        f"Got no save events. Event types: {[e.event_type for e in events]}"
    )


# ---------------------------------------------------------------------------
# MDT-005: 120 HP entity, damage=50 → NO save (below half-HP threshold of 60)
# ---------------------------------------------------------------------------

def test_MDT005_120hp_damage50_no_save():
    """MDT-005: Entity HP_MAX=120, threshold=60; damage=50 does NOT trigger save.

    KEY TEST: Distinguishes correct formula from static-50.
    Static-50 WOULD trigger (50 >= 50).
    Correct formula: threshold=max(60,50)=60 → 50 < 60 → no save.
    PHB p.145: threshold is max(hp_max//2, 50) = max(60, 50) = 60.
    """
    events, _ = _inject_spell_damage(hp=120, damage=50)
    md_saves = _massive_damage_saves(events)
    assert not md_saves, (
        f"MDT-005: damage=50 must NOT trigger massive damage save (threshold=60 for HP_MAX=120). "
        f"Got {len(md_saves)} save event(s). "
        f"If this fails: threshold is static-50, not max(hp//2,50). "
        f"Event types: {[e.event_type for e in events]}"
    )


# ---------------------------------------------------------------------------
# MDT-006: Fort save DC is exactly 15
# ---------------------------------------------------------------------------

def test_MDT006_fort_save_dc_is_15():
    """MDT-006: Massive damage Fort save DC is exactly 15 (PHB p.145)."""
    events, _ = _inject_spell_damage(hp=40, damage=50)
    md_saves = _massive_damage_saves(events)
    assert md_saves, "MDT-006: must have a massive damage save event to check DC"
    assert md_saves[0].payload["dc"] == 15, (
        f"MDT-006: Massive damage Fort save DC must be 15. "
        f"Got: {md_saves[0].payload['dc']}"
    )


# ---------------------------------------------------------------------------
# MDT-007: Failing the save → new_hp=-10 (instant death)
# ---------------------------------------------------------------------------

def test_MDT007_fail_save_instant_death():
    """MDT-007: Failing Fort save on massive damage → new_hp=-10 (PHB p.145: instant death).
    fort_roll=1, fort_bonus=0 → total=1 < DC 15 → fail.
    """
    events, _ = _inject_spell_damage(hp=40, damage=50, fort_roll=1, fort_bonus=0)
    hp_evts = [
        e for e in events
        if e.event_type == "hp_changed" and e.payload.get("entity_id") == "target_01"
    ]
    assert hp_evts, "MDT-007: hp_changed must be emitted for target_01"
    assert hp_evts[0].payload["new_hp"] == -10, (
        f"MDT-007: Instant death on failed save must set new_hp=-10. "
        f"Got new_hp={hp_evts[0].payload['new_hp']}"
    )


# ---------------------------------------------------------------------------
# MDT-008: Passing the save → no instant death
# ---------------------------------------------------------------------------

def test_MDT008_pass_save_no_death():
    """MDT-008: Passing Fort save on massive damage → target survives (new_hp != -10).
    Uses hp=120, damage=60 (threshold=60 triggered); fort_roll=20 → total=20 >= DC 15 → saved.
    Normal HP after damage: 120-60=60, which is != -10.
    """
    events, _ = _inject_spell_damage(hp=120, damage=60, fort_roll=20, fort_bonus=0)
    hp_evts = [
        e for e in events
        if e.event_type == "hp_changed" and e.payload.get("entity_id") == "target_01"
    ]
    assert hp_evts, "MDT-008: hp_changed must be emitted for target_01"
    assert hp_evts[0].payload["new_hp"] != -10, (
        f"MDT-008: Passing Fort save must NOT result in new_hp=-10. "
        f"Got new_hp={hp_evts[0].payload['new_hp']}"
    )
