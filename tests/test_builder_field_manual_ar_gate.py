"""Gate tests for WO-DOCS-FIELD-MANUAL-AR-001.

FMA-001..008 — BUILDER_FIELD_MANUAL.md hygiene: Rule #34 parity map corrected,
Rules #36-#39 added (PM artifact prohibition, idempotency guard, SeededRNG pattern,
condition dict shorthand). All tests are grep-based presence checks.
"""
import os
import re

import pytest

_MANUAL_PATH = os.path.join(os.path.dirname(__file__), "..", "BUILDER_FIELD_MANUAL.md")

with open(_MANUAL_PATH, encoding="utf-8") as _f:
    _MANUAL = _f.read()


# ---------------------------------------------------------------------------
# FMA-001: Rule #36 header present
# ---------------------------------------------------------------------------
def test_fma_001_rule36_pm_artifact_prohibition_present():
    assert "PM Artifact Prohibition" in _MANUAL, (
        "FMA-001: 'PM Artifact Prohibition' must appear in BUILDER_FIELD_MANUAL.md "
        "(Rule #36, WO-DOCS-FIELD-MANUAL-AR-001)"
    )


# ---------------------------------------------------------------------------
# FMA-002: Rule #36 names all 3 PM-owned files
# ---------------------------------------------------------------------------
def test_fma_002_rule36_names_all_three_pm_files():
    assert "BACKLOG_OPEN.md" in _MANUAL, (
        "FMA-002: Rule #36 must name 'BACKLOG_OPEN.md'"
    )
    assert "PM_BRIEFING_CURRENT.md" in _MANUAL, (
        "FMA-002: Rule #36 must name 'PM_BRIEFING_CURRENT.md'"
    )
    assert "REHYDRATION_KERNEL_LATEST.md" in _MANUAL, (
        "FMA-002: Rule #36 must name 'REHYDRATION_KERNEL_LATEST.md'"
    )


# ---------------------------------------------------------------------------
# FMA-003: Rule #37 idempotency guard present
# ---------------------------------------------------------------------------
def test_fma_003_rule37_idempotency_guard_present():
    assert "Idempotency guard" in _MANUAL, (
        "FMA-003: 'Idempotency guard' must appear in BUILDER_FIELD_MANUAL.md (Rule #37)"
    )


# ---------------------------------------------------------------------------
# FMA-004: Rule #38 SeededRNG discoverability present
# ---------------------------------------------------------------------------
def test_fma_004_rule38_seeded_rng_does_not_exist_present():
    assert "SeededRNG does not exist" in _MANUAL, (
        "FMA-004: 'SeededRNG does not exist' must appear in BUILDER_FIELD_MANUAL.md (Rule #38)"
    )


# ---------------------------------------------------------------------------
# FMA-005: Rule #39 condition dict shorthand present
# ---------------------------------------------------------------------------
def test_fma_005_rule39_condition_dict_shorthand_present():
    assert "Condition dict correct shorthand" in _MANUAL, (
        "FMA-005: 'Condition dict correct shorthand' must appear in BUILDER_FIELD_MANUAL.md (Rule #39)"
    )


# ---------------------------------------------------------------------------
# FMA-006: Rule #34 parity map — FAR row updated to DELETED
# ---------------------------------------------------------------------------
def test_fma_006_rule34_far_row_shows_deleted():
    assert "DELETED (Batch AL FAR" in _MANUAL, (
        "FMA-006: Rule #34 parity map must show resolve_single_attack_with_critical "
        "as 'DELETED (Batch AL FAR...)' not 'DRIFT RISK'"
    )


# ---------------------------------------------------------------------------
# FMA-007: Rule #34 parity map — NSP row updated to Clean
# ---------------------------------------------------------------------------
def test_fma_007_rule34_nsp_row_shows_clean():
    assert "Batch AQ NSP" in _MANUAL, (
        "FMA-007: Rule #34 parity map must reference 'Batch AQ NSP' for "
        "resolve_nonlethal_attack row (no longer DRIFT RISK)"
    )


# ---------------------------------------------------------------------------
# FMA-008: Canary — at least 39 subsections (###) present
# ---------------------------------------------------------------------------
def test_fma_008_canary_at_least_39_subsections():
    count = len(re.findall(r"^###", _MANUAL, re.MULTILINE))
    assert count >= 39, (
        f"FMA-008 CANARY: BUILDER_FIELD_MANUAL.md must have >= 39 subsections (###), "
        f"found {count}. Rules #36-#39 may be missing."
    )
