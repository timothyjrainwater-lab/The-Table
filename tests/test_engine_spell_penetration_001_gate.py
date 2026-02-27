"""Gate tests: ENGINE-SPELL-PENETRATION-001

PHB p.100: Spell Penetration — "+2 bonus on caster level checks to overcome SR."
PHB p.94: Greater Spell Penetration — "+2 bonus (stacks with Spell Penetration)."

Total with both feats: +4. No auto-fail rule on SR checks (unlike saves).
Tests SP-001 through SP-008.
WO-ENGINE-SPELL-PENETRATION-001, Batch L (Dispatch #21).
"""

import pytest
from unittest.mock import MagicMock

from aidm.core.save_resolver import check_spell_resistance
from aidm.core.state import WorldState
from aidm.schemas.entity_fields import EF
from aidm.schemas.saves import SRCheck


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_rng(roll=10):
    """Mock RNG: 'saves' stream returns fixed d20 result."""
    rng = MagicMock()
    stream = MagicMock()
    stream.randint = MagicMock(return_value=roll)
    rng.stream = MagicMock(return_value=stream)
    return rng


def _make_caster(cid="caster", feats=None):
    return {
        EF.ENTITY_ID: cid,
        EF.TEAM: "players",
        EF.HP_CURRENT: 30,
        EF.HP_MAX: 30,
        EF.FEATS: feats or [],
        EF.CONDITIONS: {},
        EF.DEFEATED: False,
        EF.POSITION: {"x": 0, "y": 0},
    }


def _make_target(tid="target", sr=15):
    entity = {
        EF.ENTITY_ID: tid,
        EF.TEAM: "monsters",
        EF.HP_CURRENT: 20,
        EF.HP_MAX: 20,
        EF.FEATS: [],
        EF.CONDITIONS: {},
        EF.DEFEATED: False,
        EF.POSITION: {"x": 1, "y": 0},
    }
    if sr:
        entity[EF.SR] = sr
    return entity


def _make_world(caster, target):
    entities = {caster[EF.ENTITY_ID]: caster, target[EF.ENTITY_ID]: target}
    return WorldState(
        ruleset_version="3.5",
        entities=entities,
        active_combat={
            "initiative_order": list(entities.keys()),
            "aoo_used_this_round": [],
        },
    )


def _sr_check(caster_id="caster", caster_level=5):
    return SRCheck(caster_level=caster_level, source_id=caster_id)


def _get_sr_event(events):
    for e in events:
        if e.event_type == "spell_resistance_checked":
            return e
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSpellPenetration001Gate:

    def test_SP001_spell_penetration_feat_adds_2_sr_bypassed(self):
        """SP-001: Caster WITH Spell Penetration — roll + CL + 2 ≥ SR → SR bypassed; bonus=2."""
        # CL=8, d20=5 → base total=13. With SP +2 → 15 = SR=15 → passes.
        caster = _make_caster(feats=["spell_penetration"])
        target = _make_target(sr=15)
        ws = _make_world(caster, target)
        rng = _make_rng(roll=5)  # 5 + 8 + 2 = 15 >= 15 → pass

        sr_check = _sr_check(caster_id="caster", caster_level=8)
        sr_passed, events = check_spell_resistance(sr_check, ws, "target", rng, 0, 0.0)

        assert sr_passed is True, "SP-001: SR should be bypassed (5+8+2=15 >= SR=15)"
        evt = _get_sr_event(events)
        assert evt is not None
        assert evt.payload["penetration_bonus"] == 2, (
            f"SP-001: penetration_bonus should be 2, got {evt.payload.get('penetration_bonus')}"
        )

    def test_SP002_no_spell_penetration_base_cl_only(self):
        """SP-002: Caster WITHOUT Spell Penetration — base CL only; penetration_bonus=0."""
        # CL=8, d20=5 → base total=13 < SR=15 → fails.
        caster = _make_caster(feats=[])
        target = _make_target(sr=15)
        ws = _make_world(caster, target)
        rng = _make_rng(roll=5)  # 5 + 8 + 0 = 13 < 15 → fail

        sr_check = _sr_check(caster_id="caster", caster_level=8)
        sr_passed, events = check_spell_resistance(sr_check, ws, "target", rng, 0, 0.0)

        assert sr_passed is False, "SP-002: SR should NOT be bypassed (5+8=13 < SR=15)"
        evt = _get_sr_event(events)
        assert evt is not None
        assert evt.payload["penetration_bonus"] == 0, (
            f"SP-002: penetration_bonus should be 0, got {evt.payload.get('penetration_bonus')}"
        )

    def test_SP003_both_feats_bonus_is_4(self):
        """SP-003: Caster WITH both Spell Penetration + Greater Spell Penetration — bonus=+4."""
        # CL=6, d20=5 → base=11. With SP+GSP +4 → 15 = SR=15 → passes.
        caster = _make_caster(feats=["spell_penetration", "greater_spell_penetration"])
        target = _make_target(sr=15)
        ws = _make_world(caster, target)
        rng = _make_rng(roll=5)  # 5 + 6 + 4 = 15 >= 15 → pass

        sr_check = _sr_check(caster_id="caster", caster_level=6)
        sr_passed, events = check_spell_resistance(sr_check, ws, "target", rng, 0, 0.0)

        assert sr_passed is True, "SP-003: SR should be bypassed (5+6+4=15 >= SR=15)"
        evt = _get_sr_event(events)
        assert evt is not None
        assert evt.payload["penetration_bonus"] == 4, (
            f"SP-003: penetration_bonus should be 4 (both feats), got {evt.payload.get('penetration_bonus')}"
        )

    def test_SP004_greater_spell_penetration_alone_adds_2(self):
        """SP-004: Caster WITH Greater Spell Penetration only (no basic feat) — bonus=+2."""
        # Greater SP alone: +2 per PHB p.94 (the basic SP gives +2 too, GSP is an additional +2)
        caster = _make_caster(feats=["greater_spell_penetration"])
        target = _make_target(sr=15)
        ws = _make_world(caster, target)
        rng = _make_rng(roll=5)  # 5 + 8 + 2 = 15 >= 15 → pass

        sr_check = _sr_check(caster_id="caster", caster_level=8)
        sr_passed, events = check_spell_resistance(sr_check, ws, "target", rng, 0, 0.0)

        assert sr_passed is True, "SP-004: GSP alone should add +2 (5+8+2=15 >= SR=15)"
        evt = _get_sr_event(events)
        assert evt is not None
        assert evt.payload["penetration_bonus"] == 2, (
            f"SP-004: penetration_bonus should be 2 (GSP alone), got {evt.payload.get('penetration_bonus')}"
        )

    def test_SP005_spell_penetration_exact_equals_sr_passes(self):
        """SP-005: Caster WITH Spell Penetration; total exactly equals SR — SR bypassed (>= check)."""
        # CL=10, d20=3, SP +2 → 15 = SR=15 → passes (>= is correct)
        caster = _make_caster(feats=["spell_penetration"])
        target = _make_target(sr=15)
        ws = _make_world(caster, target)
        rng = _make_rng(roll=3)  # 3 + 10 + 2 = 15 = SR=15 → pass

        sr_check = _sr_check(caster_id="caster", caster_level=10)
        sr_passed, events = check_spell_resistance(sr_check, ws, "target", rng, 0, 0.0)

        assert sr_passed is True, "SP-005: total == SR must pass (>= check)"

    def test_SP006_spell_penetration_d20_equals_1_no_auto_fail(self):
        """SP-006: Caster WITH Spell Penetration; d20=1 — feat bonus still applied (no auto-fail rule)."""
        # CL=14, d20=1, SP +2 → 17 > SR=15 → passes (natural 1 is NOT auto-fail for CL checks)
        caster = _make_caster(feats=["spell_penetration"])
        target = _make_target(sr=15)
        ws = _make_world(caster, target)
        rng = _make_rng(roll=1)  # 1 + 14 + 2 = 17 >= 15 → pass

        sr_check = _sr_check(caster_id="caster", caster_level=14)
        sr_passed, events = check_spell_resistance(sr_check, ws, "target", rng, 0, 0.0)

        assert sr_passed is True, "SP-006: natural 1 is not auto-fail for SR checks; feat bonus applies"
        evt = _get_sr_event(events)
        assert evt.payload["d20_result"] == 1, "SP-006: d20_result should be 1"
        assert evt.payload["penetration_bonus"] == 2

    def test_SP007_target_with_no_sr_bypasses_check(self):
        """SP-007: Target with SR=0 — SR check bypassed entirely; no event emitted."""
        caster = _make_caster(feats=["spell_penetration"])
        target = _make_target(sr=0)
        ws = _make_world(caster, target)
        rng = _make_rng(roll=10)

        sr_check = _sr_check(caster_id="caster", caster_level=5)
        sr_passed, events = check_spell_resistance(sr_check, ws, "target", rng, 0, 0.0)

        assert sr_passed is True, "SP-007: SR=0 → always passes"
        # No SR check event when SR=0
        evt = _get_sr_event(events)
        assert evt is None, "SP-007: No spell_resistance_checked event when SR=0"

    def test_SP008_caster_with_no_ef_feats_field_no_crash(self):
        """SP-008: Caster entity missing EF.FEATS field entirely — no crash; penetration_bonus=0."""
        caster = _make_caster(feats=None)
        # Remove EF.FEATS entirely to test defensive coding
        caster.pop(EF.FEATS, None)

        target = _make_target(sr=15)
        ws = _make_world(caster, target)
        rng = _make_rng(roll=10)  # 10 + 5 + 0 = 15 = SR=15 → passes

        sr_check = _sr_check(caster_id="caster", caster_level=5)
        sr_passed, events = check_spell_resistance(sr_check, ws, "target", rng, 0, 0.0)

        assert sr_passed is True, "SP-008: No crash with missing EF.FEATS; base CL used"
        evt = _get_sr_event(events)
        assert evt is not None
        assert evt.payload["penetration_bonus"] == 0, (
            f"SP-008: penetration_bonus should be 0 when feats missing, got {evt.payload.get('penetration_bonus')}"
        )
