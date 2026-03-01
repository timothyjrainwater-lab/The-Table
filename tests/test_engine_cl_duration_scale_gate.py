"""Gate tests for WO-ENGINE-CL-DURATION-SCALE-001.

CDU-001..008 — SpellDefinition.effective_duration_rounds() + haste/slow/bless CL scaling.
PHB p.173 (variable duration), p.239 (haste), p.280 (slow), p.205 (bless), p.208 (cause_fear).
"""
import pytest
from aidm.core.spell_resolver import SpellDefinition, SpellTarget, SpellEffect
from aidm.data.spell_definitions import SPELL_REGISTRY


def _make_dur_spell(duration_rounds_per_cl: int, duration_rounds: int = 0) -> SpellDefinition:
    return SpellDefinition(
        spell_id="test_dur",
        name="Test Dur",
        level=3,
        school="transmutation",
        target_type=SpellTarget.SINGLE,
        range_ft=0,
        duration_rounds=duration_rounds,
        duration_rounds_per_cl=duration_rounds_per_cl,
    )


# ---------------------------------------------------------------------------
# CDU-001: effective_duration_rounds(5) with per_cl=1 → 5
# ---------------------------------------------------------------------------
def test_cdu_001_per_cl_1_at_cl5():
    spell = _make_dur_spell(duration_rounds_per_cl=1)
    assert spell.effective_duration_rounds(5) == 5


# ---------------------------------------------------------------------------
# CDU-002: effective_duration_rounds(10) with per_cl=1 → 10
# ---------------------------------------------------------------------------
def test_cdu_002_per_cl_1_at_cl10():
    spell = _make_dur_spell(duration_rounds_per_cl=1)
    assert spell.effective_duration_rounds(10) == 10


# ---------------------------------------------------------------------------
# CDU-003: effective_duration_rounds(5) with per_cl=10 → 50
# ---------------------------------------------------------------------------
def test_cdu_003_per_cl_10_at_cl5():
    spell = _make_dur_spell(duration_rounds_per_cl=10)
    assert spell.effective_duration_rounds(5) == 50


# ---------------------------------------------------------------------------
# CDU-004: static fallback — duration_rounds=3, per_cl=0 → 3 at any CL
# ---------------------------------------------------------------------------
def test_cdu_004_static_fallback():
    spell = _make_dur_spell(duration_rounds_per_cl=0, duration_rounds=3)
    assert spell.effective_duration_rounds(1) == 3
    assert spell.effective_duration_rounds(10) == 3
    assert spell.effective_duration_rounds(20) == 3


# ---------------------------------------------------------------------------
# CDU-005: haste registry entry has duration_rounds_per_cl=1 (not 0)
# ---------------------------------------------------------------------------
def test_cdu_005_haste_has_per_cl_field():
    haste = SPELL_REGISTRY["haste"]
    assert haste.duration_rounds_per_cl == 1, (
        f"haste.duration_rounds_per_cl should be 1, got {haste.duration_rounds_per_cl}"
    )
    assert haste.duration_rounds == 0, "haste.duration_rounds should be 0 (CL-scaled)"


# ---------------------------------------------------------------------------
# CDU-006: haste at CL5 → effective_duration_rounds = 5
# ---------------------------------------------------------------------------
def test_cdu_006_haste_cl5_duration():
    haste = SPELL_REGISTRY["haste"]
    assert haste.effective_duration_rounds(5) == 5


# ---------------------------------------------------------------------------
# CDU-007: bless at CL3 → effective_duration_rounds = 30 (3 × 10 rounds)
# ---------------------------------------------------------------------------
def test_cdu_007_bless_cl3_duration():
    bless = SPELL_REGISTRY["bless"]
    assert bless.duration_rounds_per_cl == 10, (
        f"bless.duration_rounds_per_cl should be 10, got {bless.duration_rounds_per_cl}"
    )
    assert bless.effective_duration_rounds(3) == 30


# ---------------------------------------------------------------------------
# CDU-008: slow at CL8 → effective_duration_rounds = 8
# ---------------------------------------------------------------------------
def test_cdu_008_slow_cl8_duration():
    slow = SPELL_REGISTRY["slow"]
    assert slow.duration_rounds_per_cl == 1, (
        f"slow.duration_rounds_per_cl should be 1, got {slow.duration_rounds_per_cl}"
    )
    assert slow.effective_duration_rounds(8) == 8
