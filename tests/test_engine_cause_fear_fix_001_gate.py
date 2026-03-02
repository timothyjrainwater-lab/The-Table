"""Gate tests for WO-ENGINE-CAUSE-FEAR-FIX-001.

CFF-001..008 — cause_fear duration spec error fix.
PHB p.208: cause_fear duration = "1d4 rounds" (flat, not per-CL).
PHB p.229: *fear* (4th level) = "1 round/level" — the per-CL form.
Engine convention: deterministic midpoint duration_rounds=2 (floor of 1d4 avg 2.5).
"""
import pytest
from aidm.data.spell_definitions import SPELL_REGISTRY


# ---------------------------------------------------------------------------
# CFF-001: cause_fear duration_rounds == 2
# ---------------------------------------------------------------------------
def test_cff_001_cause_fear_duration_rounds():
    assert SPELL_REGISTRY["cause_fear"].duration_rounds == 2, (
        f"cause_fear duration_rounds should be 2 (PHB p.208 1d4 midpoint), "
        f"got {SPELL_REGISTRY['cause_fear'].duration_rounds}"
    )


# ---------------------------------------------------------------------------
# CFF-002: cause_fear duration_rounds_per_cl == 0
# ---------------------------------------------------------------------------
def test_cff_002_cause_fear_no_cl_scaling():
    assert SPELL_REGISTRY["cause_fear"].duration_rounds_per_cl == 0, (
        f"cause_fear duration_rounds_per_cl should be 0 (flat, not per-CL), "
        f"got {SPELL_REGISTRY['cause_fear'].duration_rounds_per_cl}"
    )


# ---------------------------------------------------------------------------
# CFF-003: effective_duration_rounds(1) == 2 — no scaling at CL1
# ---------------------------------------------------------------------------
def test_cff_003_effective_cl1():
    result = SPELL_REGISTRY["cause_fear"].effective_duration_rounds(1)
    assert result == 2, (
        f"cause_fear at CL1 should last 2 rounds, got {result}"
    )


# ---------------------------------------------------------------------------
# CFF-004: effective_duration_rounds(5) == 2 — no scaling at CL5
# ---------------------------------------------------------------------------
def test_cff_004_effective_cl5():
    result = SPELL_REGISTRY["cause_fear"].effective_duration_rounds(5)
    assert result == 2, (
        f"cause_fear at CL5 should last 2 rounds (not 5), got {result}"
    )


# ---------------------------------------------------------------------------
# CFF-005: effective_duration_rounds(20) == 2 — canary: old bug produced 20
# ---------------------------------------------------------------------------
def test_cff_005_effective_cl20_canary():
    result = SPELL_REGISTRY["cause_fear"].effective_duration_rounds(20)
    assert result == 2, (
        f"cause_fear at CL20 should last 2 rounds (old bug: duration_rounds_per_cl=1 "
        f"produced 20), got {result}"
    )


# ---------------------------------------------------------------------------
# CFF-006: regression — haste still scales (1r/CL)
# ---------------------------------------------------------------------------
def test_cff_006_haste_still_scales():
    result = SPELL_REGISTRY["haste"].effective_duration_rounds(5)
    assert result == 5, (
        f"haste at CL5 should still be 5 rounds (1r/CL), got {result}"
    )


# ---------------------------------------------------------------------------
# CFF-007: regression — slow still scales (1r/CL)
# ---------------------------------------------------------------------------
def test_cff_007_slow_still_scales():
    result = SPELL_REGISTRY["slow"].effective_duration_rounds(5)
    assert result == 5, (
        f"slow at CL5 should still be 5 rounds (1r/CL), got {result}"
    )


# ---------------------------------------------------------------------------
# CFF-008: regression — bless still scales (10r/CL)
# ---------------------------------------------------------------------------
def test_cff_008_bless_still_scales():
    result = SPELL_REGISTRY["bless"].effective_duration_rounds(5)
    assert result == 50, (
        f"bless at CL5 should still be 50 rounds (10r/CL), got {result}"
    )
