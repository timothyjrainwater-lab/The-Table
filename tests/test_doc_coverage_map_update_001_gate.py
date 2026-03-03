"""Gate tests: WO-DOC-COVERAGE-MAP-UPDATE-001 (Batch BA WO1).

CMU-001..006 — Four doc edits to docs/ENGINE_COVERAGE_MAP.md:
  CMU-001: Weapon Finesse row present with IMPLEMENTED + attack_resolver
  CMU-002: Improved Turning row present with IMPLEMENTED + turn_undead_resolver
  CMU-003: §7b IUS entry no longer says "Not Yet Registered" for the feat itself
  CMU-004: §7b stale Run "IMPLEMENTED" row removed from §7b section
  CMU-005: GWF + GWS rows present in §7a (AZ regression)
  CMU-006: At least one of agile/animal_affinity/magical_aptitude/Skill Focus in §7a (AZ regression)

FINDING-AUDIT-015-006 closed.
"""
from __future__ import annotations

import os
import re

_MAP_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "ENGINE_COVERAGE_MAP.md")


def _load_map() -> str:
    with open(_MAP_PATH, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# CMU-001: Weapon Finesse row in §7a with IMPLEMENTED + attack_resolver
# ---------------------------------------------------------------------------

def test_CMU001_weapon_finesse_implemented_row():
    """CMU-001: §7a has Weapon Finesse row marked IMPLEMENTED referencing attack_resolver."""
    content = _load_map()
    assert "Weapon Finesse" in content, (
        "CMU-001: 'Weapon Finesse' not found in ENGINE_COVERAGE_MAP.md"
    )
    # Find the WF row and verify IMPLEMENTED + attack_resolver present
    for line in content.splitlines():
        if "Weapon Finesse" in line and "**IMPLEMENTED**" in line:
            assert "attack_resolver" in line, (
                f"CMU-001: Weapon Finesse IMPLEMENTED row does not reference attack_resolver. Line: {line}"
            )
            return
    raise AssertionError(
        "CMU-001: No line in ENGINE_COVERAGE_MAP.md contains both 'Weapon Finesse' and '**IMPLEMENTED**'"
    )


# ---------------------------------------------------------------------------
# CMU-002: Improved Turning row in §7a with IMPLEMENTED + turn_undead_resolver
# ---------------------------------------------------------------------------

def test_CMU002_improved_turning_implemented_row():
    """CMU-002: §7a has Improved Turning row marked IMPLEMENTED referencing turn_undead_resolver."""
    content = _load_map()
    assert "Improved Turning" in content, (
        "CMU-002: 'Improved Turning' not found in ENGINE_COVERAGE_MAP.md"
    )
    for line in content.splitlines():
        if "Improved Turning" in line and "**IMPLEMENTED**" in line:
            assert "turn_undead_resolver" in line, (
                f"CMU-002: Improved Turning IMPLEMENTED row does not reference turn_undead_resolver. Line: {line}"
            )
            return
    raise AssertionError(
        "CMU-002: No line in ENGINE_COVERAGE_MAP.md contains both 'Improved Turning' and '**IMPLEMENTED**'"
    )


# ---------------------------------------------------------------------------
# CMU-003: §7b IUS annotation no longer says "Not Yet Registered" for feat
# ---------------------------------------------------------------------------

def test_CMU003_ius_annotation_corrected():
    """CMU-003: IUS row no longer relies on '§7b = Not Yet Registered' as annotation;
    row explicitly notes feat IS registered."""
    content = _load_map()
    for line in content.splitlines():
        if "Improved Unarmed Strike" in line:
            # Must NOT rely solely on section header; row should note registration status
            # Accept if row contains 'registered' or has been moved to §7a
            lower = line.lower()
            assert "not yet registered" not in lower or "feat registered" in lower, (
                f"CMU-003: IUS row still implies feat is 'Not Yet Registered'. Line: {line}"
            )
            # Positive check: row should note the feat IS registered
            assert "registered" in lower, (
                f"CMU-003: IUS row should note that feat IS registered in FEAT_REGISTRY. Line: {line}"
            )
            return
    # If IUS not found at all — also a fail
    raise AssertionError("CMU-003: 'Improved Unarmed Strike' not found in ENGINE_COVERAGE_MAP.md")


# ---------------------------------------------------------------------------
# CMU-004: §7b stale Run IMPLEMENTED row removed
# ---------------------------------------------------------------------------

def test_CMU004_run_stale_7b_entry_removed():
    """CMU-004: No §7b stale Run 'IMPLEMENTED' row present in §7b section."""
    content = _load_map()
    # Find §7b section
    in_7b = False
    for line in content.splitlines():
        if "### 7b." in line or "7b. PHB Feats Not Yet Registered" in line:
            in_7b = True
        if in_7b and "---" in line and in_7b:
            break
        if in_7b:
            # In §7b, there should be no Run row with IMPLEMENTED status
            if re.search(r"\|\s*Run\s*\|", line) and "**IMPLEMENTED**" in line:
                raise AssertionError(
                    f"CMU-004: Stale Run IMPLEMENTED row still present in §7b. Line: {line}"
                )


# ---------------------------------------------------------------------------
# CMU-005: GWF + GWS rows present (AZ regression)
# ---------------------------------------------------------------------------

def test_CMU005_gwf_gws_rows_present():
    """CMU-005: Greater Weapon Focus and Greater Weapon Specialization rows present in coverage map (AZ regression)."""
    content = _load_map()
    assert "Greater Weapon Focus" in content, (
        "CMU-005: 'Greater Weapon Focus' not found in ENGINE_COVERAGE_MAP.md"
    )
    assert "Greater Weapon Specialization" in content, (
        "CMU-005: 'Greater Weapon Specialization' not found in ENGINE_COVERAGE_MAP.md"
    )


# ---------------------------------------------------------------------------
# CMU-006: AZ skill feats present (AZ regression)
# ---------------------------------------------------------------------------

def test_CMU006_az_skill_feats_present():
    """CMU-006: At least one of agile/animal_affinity/magical_aptitude/Skill Focus present (AZ regression)."""
    content = _load_map()
    az_feats = ["Agile", "Animal Affinity", "Magical Aptitude", "Skill Focus"]
    found = [f for f in az_feats if f in content]
    assert found, (
        f"CMU-006: None of {az_feats} found in ENGINE_COVERAGE_MAP.md. AZ skill feats missing."
    )
