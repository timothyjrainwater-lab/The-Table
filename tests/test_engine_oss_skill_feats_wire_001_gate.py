"""Gate tests: WO-ENGINE-OSS-SKILL-FEATS-WIRE-001 (Batch AZ WO2).

SKF-001..008 — Skill feat bonuses wired in skill_resolver:
  SKF-001: agile feat → +2 to balance
  SKF-002: animal_affinity feat → +2 to handle_animal
  SKF-003: magical_aptitude feat → +2 to spellcraft
  SKF-004: skill_focus_{skill} → +3 to that skill
  SKF-005: skill_focus_{skill} does NOT apply to a different skill
  SKF-006: skill_focus stacks with _SKILL_BONUS_FEATS bonus (+2+3=+5 on same skill)
  SKF-007: Regression — alertness still grants +2 to listen
  SKF-008: Coverage map updated — skill feats row references WO-ENGINE-OSS-SKILL-FEATS-WIRE-001

PHB p.91-102: agile, animal_affinity, magical_aptitude each grant +2 untyped to two skills.
PHB p.100: Skill Focus grants +3 bonus to one named skill.
AUDIT-015 finding closed.
"""
from __future__ import annotations

import os
import pytest

from aidm.core.skill_resolver import _get_feat_skill_bonus


# ---------------------------------------------------------------------------
# SKF-001: agile → +2 balance
# ---------------------------------------------------------------------------

def test_SKF001_agile_balance():
    """SKF-001: agile feat grants +2 to balance."""
    bonus = _get_feat_skill_bonus(["agile"], "balance")
    assert bonus == 2, f"SKF-001: agile must grant +2 to balance. Got {bonus}"


# ---------------------------------------------------------------------------
# SKF-002: animal_affinity → +2 handle_animal
# ---------------------------------------------------------------------------

def test_SKF002_animal_affinity_handle_animal():
    """SKF-002: animal_affinity feat grants +2 to handle_animal."""
    bonus = _get_feat_skill_bonus(["animal_affinity"], "handle_animal")
    assert bonus == 2, f"SKF-002: animal_affinity must grant +2 to handle_animal. Got {bonus}"


# ---------------------------------------------------------------------------
# SKF-003: magical_aptitude → +2 spellcraft
# ---------------------------------------------------------------------------

def test_SKF003_magical_aptitude_spellcraft():
    """SKF-003: magical_aptitude feat grants +2 to spellcraft."""
    bonus = _get_feat_skill_bonus(["magical_aptitude"], "spellcraft")
    assert bonus == 2, f"SKF-003: magical_aptitude must grant +2 to spellcraft. Got {bonus}"


# ---------------------------------------------------------------------------
# SKF-004: skill_focus_{skill} → +3 to that skill
# ---------------------------------------------------------------------------

def test_SKF004_skill_focus_grants_3():
    """SKF-004: skill_focus_hide grants +3 to hide."""
    bonus = _get_feat_skill_bonus(["skill_focus_hide"], "hide")
    assert bonus == 3, f"SKF-004: skill_focus_hide must grant +3 to hide. Got {bonus}"


# ---------------------------------------------------------------------------
# SKF-005: skill_focus does NOT apply to a different skill
# ---------------------------------------------------------------------------

def test_SKF005_skill_focus_wrong_skill_zero():
    """SKF-005: skill_focus_hide does not apply to listen."""
    bonus = _get_feat_skill_bonus(["skill_focus_hide"], "listen")
    assert bonus == 0, f"SKF-005: skill_focus_hide must not apply to listen. Got {bonus}"


# ---------------------------------------------------------------------------
# SKF-006: skill_focus stacks with _SKILL_BONUS_FEATS (+2+3=+5)
# ---------------------------------------------------------------------------

def test_SKF006_skill_focus_stacks_with_feat_bonus():
    """SKF-006: agile(+2 balance) + skill_focus_balance(+3) = +5 total (both stack)."""
    bonus = _get_feat_skill_bonus(["agile", "skill_focus_balance"], "balance")
    assert bonus == 5, (
        f"SKF-006: agile(+2) + skill_focus_balance(+3) must stack to +5. Got {bonus}"
    )


# ---------------------------------------------------------------------------
# SKF-007: regression — alertness still grants +2 to listen
# ---------------------------------------------------------------------------

def test_SKF007_alertness_regression():
    """SKF-007: Regression — alertness still grants +2 to listen after this WO."""
    bonus = _get_feat_skill_bonus(["alertness"], "listen")
    assert bonus == 2, f"SKF-007: alertness regression — must still grant +2 to listen. Got {bonus}"


# ---------------------------------------------------------------------------
# SKF-008: Coverage map updated
# ---------------------------------------------------------------------------

def test_SKF008_coverage_map_updated():
    """SKF-008: ENGINE_COVERAGE_MAP.md references WO-ENGINE-OSS-SKILL-FEATS-WIRE-001."""
    cov_path = os.path.join(os.path.dirname(__file__), "..", "docs", "ENGINE_COVERAGE_MAP.md")
    with open(cov_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "WO-ENGINE-OSS-SKILL-FEATS-WIRE-001" in content, (
        "SKF-008: ENGINE_COVERAGE_MAP.md must contain 'WO-ENGINE-OSS-SKILL-FEATS-WIRE-001'"
    )
