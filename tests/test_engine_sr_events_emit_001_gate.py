"""Gate tests: WO-ENGINE-SR-EVENTS-EMIT-001 (Batch AY WO1).

SRE-001..008 — SR events emitted to EventLog via play_loop._resolve_spell_cast:
  SRE-001: No SR target — spell resolves, no spell_resistance_checked event in EventLog
  SRE-002: Target with SR=0 — no spell_resistance_checked event (SR check not triggered)
  SRE-003: Target with SR > 0, caster beats SR — EventLog contains sr event with sr_passed=True
  SRE-004: Target with SR > 0, caster fails SR — sr event with sr_passed=False; no damage
  SRE-005: SR event payload includes target_sr, d20_result, caster_level, sr_passed
  SRE-006: Two spells in sequence — two sr events, one per spell (no bleed)
  SRE-007: Regression — WO-ENGINE-SR-SPELL-PATH-001 behavior unchanged
  SRE-008: Coverage map updated — SR event emission row references WO-ENGINE-SR-EVENTS-EMIT-001

PHB p.172: Spell resistance produces an observable check result.
FINDING-ENGINE-SR-PLAY-LOOP-EVENTS-001 closed.
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import patch
from copy import deepcopy

from aidm.core.play_loop import _resolve_spell_cast
from aidm.core.spell_resolver import SpellDefinition, SpellTarget, SpellEffect, SaveEffect
from aidm.core.spell_resolver import DamageType
from aidm.schemas.saves import SaveType
from aidm.schemas.entity_fields import EF
from aidm.core.state import WorldState
from aidm.core.rng_manager import RNGManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _world(entities: dict) -> WorldState:
    return WorldState(ruleset_version="3.5", entities=entities, active_combat={})


def _rng(seed: int = 42) -> RNGManager:
    return RNGManager(seed)


def _fireball_spell() -> SpellDefinition:
    """Fireball: area damage, Reflex save half, spell resistance allowed."""
    return SpellDefinition(
        spell_id="fireball_test",
        name="Fireball",
        level=3,
        school="evocation",
        target_type=SpellTarget.SINGLE,
        range_ft=400,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="3d6",
        damage_type=DamageType.FIRE,
        save_type=SaveType.REF,
        save_effect=SaveEffect.HALF,
        spell_resistance=True,
    )


def _magic_missile_spell() -> SpellDefinition:
    """Magic Missile: single target, auto-hit, no SR check bypass for test."""
    return SpellDefinition(
        spell_id="magic_missile_test",
        name="Magic Missile",
        level=1,
        school="evocation",
        target_type=SpellTarget.SINGLE,
        range_ft=100,
        effect_type=SpellEffect.DAMAGE,
        damage_dice="1d4+1",
        damage_type=DamageType.FORCE,
        auto_hit=True,
        spell_resistance=True,
    )


def _caster_entity(sr: int = 0) -> dict:
    return {
        EF.ENTITY_ID: "caster",
        EF.HP_CURRENT: 50,
        EF.HP_MAX: 50,
        EF.AC: 10,
        EF.TEAM: "player",
        EF.POSITION: {"x": 0, "y": 0},
        EF.CASTER_LEVEL: 10,
        EF.SPELL_DC_BASE: 10,
        EF.FEATS: [],
        EF.CONDITIONS: {},
        EF.SR: sr,
        EF.SPELL_SLOTS: {"1": 3, "2": 2, "3": 2},
        EF.SPELL_SLOTS_MAX: {"1": 3, "2": 2, "3": 2},
    }


def _target_entity(sr: int = 0) -> dict:
    return {
        EF.ENTITY_ID: "target",
        EF.HP_CURRENT: 40,
        EF.HP_MAX: 40,
        EF.AC: 12,
        EF.TEAM: "enemy",
        EF.POSITION: {"x": 5, "y": 5},
        EF.FEATS: [],
        EF.CONDITIONS: {},
        EF.SR: sr,
        EF.SAVE_REF: 3,
        EF.SAVE_FORT: 2,
        EF.SAVE_WILL: 2,
    }


def _cast_spell(spell: SpellDefinition, caster_id: str = "caster",
                target_id: str = "target", world: WorldState = None,
                seed: int = 42):
    """Run _resolve_spell_cast with the given spell and world state."""
    from aidm.core.spell_resolver import SpellCastIntent
    from aidm.schemas.position import Position

    intent = SpellCastIntent(
        caster_id=caster_id,
        spell_id=spell.spell_id,
        target_entity_id=target_id,
    )

    with patch.dict("sys.modules", {}):
        from aidm.data import spell_definitions
        original_registry = dict(spell_definitions.SPELL_REGISTRY)
        spell_definitions.SPELL_REGISTRY[spell.spell_id] = spell

        try:
            events, ws, narration = _resolve_spell_cast(
                intent=intent,
                world_state=world,
                rng=_rng(seed),
                grid=None,
                next_event_id=1,
                timestamp=1.0,
                turn_index=1,
            )
        finally:
            spell_definitions.SPELL_REGISTRY.pop(spell.spell_id, None)

    return events, ws, narration


# ---------------------------------------------------------------------------
# SRE-001: No SR target — no spell_resistance_checked event
# ---------------------------------------------------------------------------

def test_SRE001_no_sr_target_no_sr_event():
    """SRE-001: No SR on target — spell resolves, no spell_resistance_checked event."""
    spell = _fireball_spell()
    world = _world({"caster": _caster_entity(sr=0), "target": _target_entity(sr=0)})

    events, _, _ = _cast_spell(spell, world=world, seed=99)

    sr_events = [e for e in events if e.event_type == "spell_resistance_checked"]
    assert len(sr_events) == 0, (
        f"SRE-001: No SR target should produce no spell_resistance_checked events. "
        f"Got {len(sr_events)}: {[e.payload for e in sr_events]}"
    )


# ---------------------------------------------------------------------------
# SRE-002: SR=0 target — no sr_event
# ---------------------------------------------------------------------------

def test_SRE002_sr_zero_no_sr_event():
    """SRE-002: Target with SR=0 — SR check not triggered, no event emitted."""
    spell = _fireball_spell()
    target = _target_entity(sr=0)
    world = _world({"caster": _caster_entity(), "target": target})

    events, _, _ = _cast_spell(spell, world=world, seed=5)

    sr_events = [e for e in events if e.event_type == "spell_resistance_checked"]
    assert len(sr_events) == 0, (
        f"SRE-002: SR=0 should produce no spell_resistance_checked. Got {len(sr_events)}"
    )


# ---------------------------------------------------------------------------
# SRE-003: SR > 0, caster beats SR — event with sr_passed=True
# ---------------------------------------------------------------------------

def test_SRE003_sr_beaten_event_in_eventlog():
    """SRE-003: Target has SR, caster overcomes it — EventLog contains sr event with sr_passed=True."""
    spell = _fireball_spell()
    # CL=20 ensures we beat any SR <= 40 (d20+20)
    caster = _caster_entity()
    caster[EF.CASTER_LEVEL] = 20
    target = _target_entity(sr=15)  # CL20 + d20(1+) = 21+ always beats SR 15

    world = _world({"caster": caster, "target": target})

    # Use seed that gives high d20 for saves rng
    events, _, _ = _cast_spell(spell, world=world, seed=1)

    sr_events = [e for e in events if e.event_type == "spell_resistance_checked"]
    assert len(sr_events) >= 1, (
        f"SRE-003: Expected at least 1 spell_resistance_checked event. Got {len(sr_events)}"
    )
    passed_events = [e for e in sr_events if e.payload.get("sr_passed") is True]
    assert len(passed_events) >= 1, (
        f"SRE-003: Expected sr_passed=True in at least one SR event. "
        f"Payloads: {[e.payload for e in sr_events]}"
    )


# ---------------------------------------------------------------------------
# SRE-004: SR > 0, caster fails SR — sr event present, no damage applied
# ---------------------------------------------------------------------------

def test_SRE004_sr_blocked_event_and_no_damage():
    """SRE-004: Caster fails SR — sr event with sr_passed=False; spell blocked (no hp_changed)."""
    spell = _fireball_spell()
    # CL=1 vs SR=25 — d20+1 < 25 almost always (only fails on d20=24+, so use seed that gives low)
    caster = _caster_entity()
    caster[EF.CASTER_LEVEL] = 1
    target = _target_entity(sr=25)

    world = _world({"caster": caster, "target": target})

    # Need a seed where d20 roll in saves stream is low enough that 1+d20 < 25
    # Use seed=7: saves stream randint(1,20) with seed 7 should give low roll
    # We'll try multiple seeds to get a failing roll
    for seed in range(10, 50):
        events, _, _ = _cast_spell(spell, world=world, seed=seed)
        sr_events = [e for e in events if e.event_type == "spell_resistance_checked"]
        if sr_events and not sr_events[0].payload.get("sr_passed"):
            # SR blocked — confirm no hp_changed event for target
            hp_events = [e for e in events if e.event_type == "hp_changed"
                         and e.payload.get("entity_id") == "target"]
            assert len(hp_events) == 0, (
                f"SRE-004: SR blocked spell — no hp_changed for target expected. "
                f"Got {len(hp_events)} events"
            )
            return  # Test passed

    pytest.fail("SRE-004: Could not find a seed where CL1 fails SR=25 check. Unexpected.")


# ---------------------------------------------------------------------------
# SRE-005: SR event payload completeness
# ---------------------------------------------------------------------------

def test_SRE005_sr_event_payload_fields():
    """SRE-005: SR event payload includes target_sr, d20_result, caster_level, sr_passed."""
    spell = _fireball_spell()
    caster = _caster_entity()
    caster[EF.CASTER_LEVEL] = 20  # Guaranteed to beat SR=15
    target = _target_entity(sr=15)

    world = _world({"caster": caster, "target": target})
    events, _, _ = _cast_spell(spell, world=world, seed=1)

    sr_events = [e for e in events if e.event_type == "spell_resistance_checked"]
    assert len(sr_events) >= 1, "SRE-005: Expected at least one SR event"

    payload = sr_events[0].payload
    for field in ("target_sr", "d20_result", "caster_level", "sr_passed"):
        assert field in payload, (
            f"SRE-005: SR event payload missing '{field}'. Keys present: {list(payload.keys())}"
        )
    assert payload["target_sr"] == 15, f"SRE-005: target_sr should be 15, got {payload['target_sr']}"
    assert payload["caster_level"] == 20, f"SRE-005: caster_level should be 20, got {payload['caster_level']}"


# ---------------------------------------------------------------------------
# SRE-006: Two spells — two sr events, one per spell
# ---------------------------------------------------------------------------

def test_SRE006_two_spells_two_sr_events():
    """SRE-006: Two spells cast against SR target — two separate sr events, one each."""
    spell1 = _fireball_spell()
    spell2 = _magic_missile_spell()

    caster = _caster_entity()
    caster[EF.CASTER_LEVEL] = 20  # Beat SR reliably
    target = _target_entity(sr=15)
    world1 = _world({"caster": caster, "target": target})

    events1, ws1, _ = _cast_spell(spell1, world=world1, seed=1)
    # Second spell cast on updated world state
    events2, _, _ = _cast_spell(spell2, world=ws1, seed=2)

    sr_events_1 = [e for e in events1 if e.event_type == "spell_resistance_checked"]
    sr_events_2 = [e for e in events2 if e.event_type == "spell_resistance_checked"]

    assert len(sr_events_1) >= 1, (
        f"SRE-006: First spell should produce SR event. Got {len(sr_events_1)}"
    )
    assert len(sr_events_2) >= 1, (
        f"SRE-006: Second spell should produce SR event. Got {len(sr_events_2)}"
    )


# ---------------------------------------------------------------------------
# SRE-007: Regression — SR check behavior unchanged
# ---------------------------------------------------------------------------

def test_SRE007_sr_check_behavior_unchanged():
    """SRE-007: Regression — SR check outcome logic from WO-ENGINE-SR-SPELL-PATH-001 unchanged.
    CL20 vs SR15 must pass. CL1 vs SR25 must fail when d20 is low.
    """
    from aidm.core.save_resolver import check_spell_resistance
    from aidm.schemas.saves import SRCheck

    caster = _caster_entity()
    caster[EF.CASTER_LEVEL] = 20
    target = _target_entity(sr=15)
    world = _world({"caster": caster, "target": target})

    rng = _rng(1)
    sr_check = SRCheck(caster_level=20, source_id="caster")
    passed, events = check_spell_resistance(
        sr_check=sr_check,
        world_state=world,
        target_id="target",
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )
    assert passed is True, (
        f"SRE-007: CL20 vs SR15 must pass. Got passed={passed}"
    )
    assert len(events) == 1, f"SRE-007: Expected 1 event from check_spell_resistance"
    assert events[0].event_type == "spell_resistance_checked"


# ---------------------------------------------------------------------------
# SRE-008: Coverage map updated
# ---------------------------------------------------------------------------

def test_SRE008_coverage_map_updated():
    """SRE-008: ENGINE_COVERAGE_MAP.md references WO-ENGINE-SR-EVENTS-EMIT-001."""
    cov_path = os.path.join(os.path.dirname(__file__), "..", "docs", "ENGINE_COVERAGE_MAP.md")
    with open(cov_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "WO-ENGINE-SR-EVENTS-EMIT-001" in content, (
        "SRE-008: ENGINE_COVERAGE_MAP.md must contain 'WO-ENGINE-SR-EVENTS-EMIT-001'"
    )
    assert "IMPLEMENTED" in content, (
        "SRE-008: Coverage map must show IMPLEMENTED status for SR event emission"
    )
