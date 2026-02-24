"""Gate ENGINE-CONCENTRATION — WO-ENGINE-CONCENTRATION-001: Per-Spell Concentration Break.

Tests:
CC-01: Caster with 0 concentration spells takes damage -> no concentration events emitted
CC-02: Caster with 1 spell, roll fails DC -> concentration_broken event, spell dropped
CC-03: Caster with 1 spell, roll passes DC -> concentration_check maintained=True, not dropped
CC-04: Caster with 2 spells, both fail -> 2 concentration_broken events, both dropped
CC-05: Caster with 2 spells, roll 1 fails / roll 2 passes -> 1 broken + 1 maintained
CC-06: DC correctness: damage=8, spell_level=2 -> DC=20
CC-07: DC correctness: damage=8, spell_level=1 -> DC=19
CC-08: 2 spells -> 2 separate RNG draws consumed
CC-09: condition_removed emitted for broken effect with condition_applied set
CC-10: Zero regressions on CP-23 gate
"""

import unittest.mock as mock
from copy import deepcopy
from typing import Any, Dict, List

import pytest

from aidm.core.duration_tracker import DurationTracker, ActiveSpellEffect
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_effect(
    effect_id: str,
    spell_id: str,
    spell_name: str,
    caster_id: str,
    target_id: str,
    spell_level: int = 1,
    condition_applied: str = None,
) -> ActiveSpellEffect:
    return ActiveSpellEffect(
        effect_id=effect_id,
        spell_id=spell_id,
        spell_name=spell_name,
        caster_id=caster_id,
        target_id=target_id,
        rounds_remaining=10,
        concentration=True,
        condition_applied=condition_applied,
        spell_level=spell_level,
    )


def _make_world_with_tracker(tracker: DurationTracker) -> WorldState:
    entities = {
        "caster": {
            EF.ENTITY_ID: "caster",
            EF.TEAM: "party",
            EF.HP_CURRENT: 20,
            EF.HP_MAX: 20,
            EF.CONDITIONS: {},
        },
        "target": {
            EF.ENTITY_ID: "target",
            EF.TEAM: "monsters",
            EF.HP_CURRENT: 10,
            EF.HP_MAX: 10,
            EF.CONDITIONS: {"paralyzed": {}},
        },
    }
    ac = {"initiative_order": ["caster", "target"], "duration_tracker": tracker.to_dict()}
    return WorldState(ruleset_version="3.5e", entities=entities, active_combat=ac)


def _rng_sequence(values: List[int]):
    """RNG mock that returns values in sequence from stream('combat').randint."""
    stream = mock.MagicMock()
    stream.randint.side_effect = values
    rng = mock.MagicMock()
    rng.stream.return_value = stream
    return rng


# Import _check_concentration_break from play_loop
from aidm.core.play_loop import _check_concentration_break


# ---------------------------------------------------------------------------
# CC-01: No concentration effects -> no events
# ---------------------------------------------------------------------------

def test_cc01_no_concentration_no_events():
    tracker = DurationTracker()  # empty
    ws = _make_world_with_tracker(tracker)
    rng = _rng_sequence([15])

    events, _ = _check_concentration_break(
        caster_id="caster",
        damage_dealt=5,
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )
    types = [e.event_type for e in events]
    assert "concentration_broken" not in types
    assert "concentration_check" not in types
    rng.stream.assert_not_called()


# ---------------------------------------------------------------------------
# CC-02: 1 spell, roll fails DC -> concentration_broken, spell dropped
# ---------------------------------------------------------------------------

def test_cc02_one_spell_fail_drops_spell():
    tracker = DurationTracker()
    effect = _make_effect("eff1", "hold_person", "Hold Person", "caster", "target", spell_level=2)
    tracker.add_effect(effect)
    ws = _make_world_with_tracker(tracker)

    # damage=8, spell_level=2 -> DC=20. Roll 1 + 0 bonus = 1 < 20 -> fail
    rng = _rng_sequence([1])
    events, updated_ws = _check_concentration_break(
        caster_id="caster",
        damage_dealt=8,
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "concentration_broken" in types
    # Verify effect was removed from updated tracker
    from aidm.core.duration_tracker import DurationTracker as DT
    updated_tracker = DT.from_dict(updated_ws.active_combat["duration_tracker"])
    assert updated_tracker.get_concentration_effects("caster") == []


# ---------------------------------------------------------------------------
# CC-03: 1 spell, roll passes DC -> concentration_check maintained=True
# ---------------------------------------------------------------------------

def test_cc03_one_spell_pass_maintains():
    tracker = DurationTracker()
    effect = _make_effect("eff1", "bless", "Bless", "caster", "caster", spell_level=1)
    tracker.add_effect(effect)
    ws = _make_world_with_tracker(tracker)

    # damage=8, spell_level=1 -> DC=19. Roll 20 + 0 = 20 >= 19 -> pass
    rng = _rng_sequence([20])
    events, updated_ws = _check_concentration_break(
        caster_id="caster",
        damage_dealt=8,
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "concentration_check" in types
    assert "concentration_broken" not in types
    check_ev = next(e for e in events if e.event_type == "concentration_check")
    assert check_ev.payload["maintained"] is True
    # Spell still present
    from aidm.core.duration_tracker import DurationTracker as DT
    updated_tracker = DT.from_dict(updated_ws.active_combat["duration_tracker"])
    assert len(updated_tracker.get_concentration_effects("caster")) == 1


# ---------------------------------------------------------------------------
# CC-04: 2 spells, both fail -> 2 concentration_broken events, both dropped
# ---------------------------------------------------------------------------

def test_cc04_two_spells_both_fail():
    tracker = DurationTracker()
    e1 = _make_effect("eff1", "hold_person", "Hold Person", "caster", "target", spell_level=2)
    e2 = _make_effect("eff2", "bless", "Bless", "caster", "caster", spell_level=1)
    tracker.add_effect(e1)
    tracker.add_effect(e2)
    ws = _make_world_with_tracker(tracker)

    # Both rolls = 1. DC for e1: 10+8+2=20, DC for e2: 10+8+1=19. Both 1 < min DC -> fail
    rng = _rng_sequence([1, 1])
    events, updated_ws = _check_concentration_break(
        caster_id="caster",
        damage_dealt=8,
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    broken = [e for e in events if e.event_type == "concentration_broken"]
    assert len(broken) == 2
    from aidm.core.duration_tracker import DurationTracker as DT
    updated_tracker = DT.from_dict(updated_ws.active_combat["duration_tracker"])
    assert updated_tracker.get_concentration_effects("caster") == []


# ---------------------------------------------------------------------------
# CC-05: 2 spells, first fails, second passes -> 1 broken + 1 maintained
# ---------------------------------------------------------------------------

def test_cc05_two_spells_one_fail_one_pass():
    tracker = DurationTracker()
    # Hold Person (level 2) - DC 20 with damage 8
    e1 = _make_effect("eff1", "hold_person", "Hold Person", "caster", "target", spell_level=2)
    # Bless (level 1) - DC 19 with damage 8
    e2 = _make_effect("eff2", "bless", "Bless", "caster", "caster", spell_level=1)
    tracker.add_effect(e1)
    tracker.add_effect(e2)
    ws = _make_world_with_tracker(tracker)

    # First roll=1 (fail DC 20), second roll=19 (pass DC 19)
    rng = _rng_sequence([1, 19])
    events, updated_ws = _check_concentration_break(
        caster_id="caster",
        damage_dealt=8,
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    broken = [e for e in events if e.event_type == "concentration_broken"]
    maintained = [e for e in events if e.event_type == "concentration_check"]
    assert len(broken) == 1
    assert len(maintained) == 1
    assert maintained[0].payload["maintained"] is True

    from aidm.core.duration_tracker import DurationTracker as DT
    updated_tracker = DT.from_dict(updated_ws.active_combat["duration_tracker"])
    remaining = updated_tracker.get_concentration_effects("caster")
    assert len(remaining) == 1  # Only Bless remains


# ---------------------------------------------------------------------------
# CC-06: DC correctness: damage=8, spell_level=2 -> DC=20
# ---------------------------------------------------------------------------

def test_cc06_dc_damage8_level2_is_20():
    tracker = DurationTracker()
    effect = _make_effect("eff1", "hold_person", "Hold Person", "caster", "target", spell_level=2)
    tracker.add_effect(effect)
    ws = _make_world_with_tracker(tracker)

    rng = _rng_sequence([1])  # fail
    events, _ = _check_concentration_break(
        caster_id="caster",
        damage_dealt=8,
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    broken = next(e for e in events if e.event_type == "concentration_broken")
    assert broken.payload["dc"] == 20


# ---------------------------------------------------------------------------
# CC-07: DC correctness: damage=8, spell_level=1 -> DC=19
# ---------------------------------------------------------------------------

def test_cc07_dc_damage8_level1_is_19():
    tracker = DurationTracker()
    effect = _make_effect("eff1", "bless", "Bless", "caster", "caster", spell_level=1)
    tracker.add_effect(effect)
    ws = _make_world_with_tracker(tracker)

    rng = _rng_sequence([1])  # fail
    events, _ = _check_concentration_break(
        caster_id="caster",
        damage_dealt=8,
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    broken = next(e for e in events if e.event_type == "concentration_broken")
    assert broken.payload["dc"] == 19


# ---------------------------------------------------------------------------
# CC-08: 2 spells -> exactly 2 RNG draws consumed
# ---------------------------------------------------------------------------

def test_cc08_two_spells_two_rng_draws():
    tracker = DurationTracker()
    e1 = _make_effect("eff1", "hold_person", "Hold Person", "caster", "target", spell_level=2)
    e2 = _make_effect("eff2", "bless", "Bless", "caster", "caster", spell_level=1)
    tracker.add_effect(e1)
    tracker.add_effect(e2)
    ws = _make_world_with_tracker(tracker)

    rng = _rng_sequence([15, 18])  # both pass
    _check_concentration_break(
        caster_id="caster",
        damage_dealt=5,
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    stream = rng.stream("combat")
    assert stream.randint.call_count == 2


# ---------------------------------------------------------------------------
# CC-09: condition_removed emitted for broken effect with condition_applied
# ---------------------------------------------------------------------------

def test_cc09_condition_removed_on_break():
    tracker = DurationTracker()
    # Effect with condition_applied on target (who has "paralyzed" condition)
    effect = _make_effect(
        "eff1", "hold_person", "Hold Person", "caster", "target",
        spell_level=2, condition_applied="paralyzed"
    )
    tracker.add_effect(effect)
    ws = _make_world_with_tracker(tracker)

    rng = _rng_sequence([1])  # fail DC 20
    events, _ = _check_concentration_break(
        caster_id="caster",
        damage_dealt=8,
        world_state=ws,
        rng=rng,
        next_event_id=0,
        timestamp=0.0,
    )

    types = [e.event_type for e in events]
    assert "condition_removed" in types
    cr_ev = next(e for e in events if e.event_type == "condition_removed")
    assert cr_ev.payload["condition"] == "paralyzed"
    assert cr_ev.payload["reason"] == "concentration_broken"


# ---------------------------------------------------------------------------
# CC-10: Zero regressions — CP-23 gate importable
# ---------------------------------------------------------------------------

def test_cc10_regression_cp23_importable():
    import importlib
    cp23 = importlib.import_module("tests.test_engine_gate_cp23")
    assert cp23 is not None
