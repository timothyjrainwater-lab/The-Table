"""WO-SPARK-RV007-001: Forbidden Meta-Game Claims Detection — Gate P Tests.

Proves that NarrationValidator detects forbidden meta-game content (damage
numbers, HP values, dice rolls, AC, DC, attack bonuses, dice notation,
distance/range, natural die results) and rulebook citations. Also verifies
RV-004 underscore normalization fix (FINDING-HOOLIGAN-01).

GATE TESTS:
  P-01: FUZZ-01 Reproduction — Damage Number
  P-02: FUZZ-02 Reproduction — HP Reference
  P-03: FUZZ-03 Reproduction — Die Roll Result
  P-04: MV-02 — AC Reference
  P-05: MV-05 — DC Reference
  P-06: MV-07 — Dice Notation
  P-07: MV-09 — Natural 20
  P-08: MV-04 — Attack Bonus
  P-09: MV-08 — Distance/Range
  P-10: RC-01 — Rulebook Citation
  P-11: RC-03 — Rule Reference Phrasing
  P-12: RC-04 — RAW Assertion
  P-13: Clean Narration — No False Positives
  P-14: Clean Narration With Numbers — No False Positives on Prose Numbers
  P-15: Multiple Violations — All Reported
  P-16: RV-004 Underscore Fix — Condition Keyword Normalization
  P-17: MV-03 Variant — "hit points" with space
  P-18: Existing Rules Still Work — No Regression

Authority: WO-SPARK-RV007-001, FINDING-HOOLIGAN-02, Typed Call Contract Section 3.1-3.2.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest

from aidm.narration.narration_validator import (
    NarrationValidator,
    ValidationResult,
    RuleViolation,
)


# ---------------------------------------------------------------------------
# MOCK BRIEF (replicates test_narration_validator.py pattern)
# ---------------------------------------------------------------------------

@dataclass
class MockBrief:
    """Minimal NarrativeBrief stand-in for validator testing."""
    action_type: str = "attack_hit"
    actor_name: str = "Kael"
    target_name: Optional[str] = "Goblin"
    severity: str = "moderate"
    target_defeated: bool = False
    condition_applied: Optional[str] = None
    condition_removed: Optional[str] = None
    weapon_name: Optional[str] = "longsword"
    spell_name: Optional[str] = None
    presentation_semantics: Optional[object] = None
    source_event_ids: tuple = ()


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def validator():
    return NarrationValidator()


# ===========================================================================
# P-01: FUZZ-01 Reproduction — Damage Number
# ===========================================================================

class TestP01_FuzzDamage:
    """P-01: "dealing 14 damage" must be caught by RV-009 (MV-01)."""

    def test_damage_number_detected(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "Kael's longsword slashes through, dealing 14 damage to the goblin.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-009" for v in result.violations)


# ===========================================================================
# P-02: FUZZ-02 Reproduction — HP Reference
# ===========================================================================

class TestP02_FuzzHP:
    """P-02: "42 HP remaining" must be caught by RV-009 (MV-03)."""

    def test_hp_reference_detected(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "The goblin staggers back (42 HP remaining), clutching its wound.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-009" for v in result.violations)


# ===========================================================================
# P-03: FUZZ-03 Reproduction — Die Roll Result
# ===========================================================================

class TestP03_FuzzRoll:
    """P-03: "rolled a 19" must be caught by RV-009 (MV-06)."""

    def test_roll_result_detected(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "Kael rolled a 19, his blade finding its mark in the goblin's side.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-009" for v in result.violations)


# ===========================================================================
# P-04: MV-02 — AC Reference
# ===========================================================================

class TestP04_ACReference:
    """P-04: "AC 16" must be caught by RV-009 (MV-02)."""

    def test_ac_reference_detected(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "The strike pierces the goblin's AC 16 armor.",
            brief,
        )
        assert result.verdict == "FAIL"
        rv009 = [v for v in result.violations if v.rule_id == "RV-009"]
        assert len(rv009) >= 1
        assert any("MV-02" in v.detail for v in rv009)


# ===========================================================================
# P-05: MV-05 — DC Reference
# ===========================================================================

class TestP05_DCReference:
    """P-05: "DC 15" must be caught by RV-009 (MV-05)."""

    def test_dc_reference_detected(self, validator):
        brief = MockBrief(action_type="spell_damage_dealt", spell_name="Hold Monster")
        result = validator.validate(
            "Seraphine's spell (DC 15) overwhelms the bandit's will.",
            brief,
        )
        assert result.verdict == "FAIL"
        rv009 = [v for v in result.violations if v.rule_id == "RV-009"]
        assert any("MV-05" in v.detail for v in rv009)


# ===========================================================================
# P-06: MV-07 — Dice Notation
# ===========================================================================

class TestP06_DiceNotation:
    """P-06: "8d6" must be caught by RV-009 (MV-07)."""

    def test_dice_notation_detected(self, validator):
        brief = MockBrief(action_type="spell_damage_dealt", spell_name="Fireball")
        result = validator.validate(
            "The fireball erupts, dealing 8d6 fire across the chamber.",
            brief,
        )
        assert result.verdict == "FAIL"
        rv009 = [v for v in result.violations if v.rule_id == "RV-009"]
        assert any("MV-07" in v.detail for v in rv009)


# ===========================================================================
# P-07: MV-09 — Natural 20
# ===========================================================================

class TestP07_Natural20:
    """P-07: "natural 20" must be caught by RV-009 (MV-09)."""

    def test_natural_20_detected(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "With a natural 20, Kael's blade finds the perfect gap in the armor.",
            brief,
        )
        assert result.verdict == "FAIL"
        rv009 = [v for v in result.violations if v.rule_id == "RV-009"]
        assert any("MV-09" in v.detail for v in rv009)


# ===========================================================================
# P-08: MV-04 — Attack Bonus
# ===========================================================================

class TestP08_AttackBonus:
    """P-08: "+7 to hit" must be caught by RV-009 (MV-04)."""

    def test_attack_bonus_detected(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "Kael swings with +7 to hit, his longsword a blur of steel.",
            brief,
        )
        assert result.verdict == "FAIL"
        rv009 = [v for v in result.violations if v.rule_id == "RV-009"]
        assert any("MV-04" in v.detail for v in rv009)


# ===========================================================================
# P-09: MV-08 — Distance/Range
# ===========================================================================

class TestP09_DistanceRange:
    """P-09: "30 feet of movement" must be caught by RV-009 (MV-08)."""

    def test_distance_range_detected(self, validator):
        brief = MockBrief(action_type="move")
        result = validator.validate(
            "The goblin retreats 30 feet of movement back toward the cave.",
            brief,
        )
        assert result.verdict == "FAIL"
        rv009 = [v for v in result.violations if v.rule_id == "RV-009"]
        assert any("MV-08" in v.detail for v in rv009)


# ===========================================================================
# P-10: RC-01 — Rulebook Citation
# ===========================================================================

class TestP10_RulebookCitation:
    """P-10: "PHB 154" must be caught by RV-010 (RC-01)."""

    def test_rulebook_citation_detected(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "As described in PHB 154, the charge carries Kael forward.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-010" for v in result.violations)


# ===========================================================================
# P-11: RC-03 — Rule Reference Phrasing
# ===========================================================================

class TestP11_RuleReference:
    """P-11: "Per the grapple rules" must be caught by RV-010 (RC-03)."""

    def test_rule_reference_detected(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "Per the grapple rules, the goblin is pinned.",
            brief,
        )
        assert result.verdict == "FAIL"
        rv010 = [v for v in result.violations if v.rule_id == "RV-010"]
        assert any("RC-03" in v.detail for v in rv010)


# ===========================================================================
# P-12: RC-04 — RAW Assertion
# ===========================================================================

class TestP12_RAWAssertion:
    """P-12: "rules as written" must be caught by RV-010 (RC-04)."""

    def test_raw_assertion_detected(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "The rules as written state the attack provokes.",
            brief,
        )
        assert result.verdict == "FAIL"
        rv010 = [v for v in result.violations if v.rule_id == "RV-010"]
        assert any("RC-04" in v.detail for v in rv010)


# ===========================================================================
# P-13: Clean Narration — No False Positives
# ===========================================================================

class TestP13_CleanNarration:
    """P-13: Clean prose must NOT trigger RV-009 or RV-010."""

    def test_clean_narration_no_false_positives(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "Kael's longsword slices through the goblin's armor, sending sparks "
            "flying. The creature staggers back, its green skin marred by a deep gash.",
            brief,
        )
        rv009_010 = [v for v in result.violations if v.rule_id in ("RV-009", "RV-010")]
        assert len(rv009_010) == 0


# ===========================================================================
# P-14: Clean Narration With Numbers — No False Positives on Prose Numbers
# ===========================================================================

class TestP14_ProseNumbers:
    """P-14: Prose numbers and standalone digits must NOT trigger RV-009/RV-010."""

    def test_prose_numbers_no_false_positives(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "Three goblins surround Kael. The first lunges, but Kael's blade is faster.",
            brief,
        )
        rv009_010 = [v for v in result.violations if v.rule_id in ("RV-009", "RV-010")]
        assert len(rv009_010) == 0

    def test_minor_damage_word_alone_no_false_positive(self, validator):
        """The word 'damage' without a preceding digit must NOT trigger MV-01."""
        brief = MockBrief()
        result = validator.validate(
            "The goblin's blade leaves minor damage on Kael's shield.",
            brief,
        )
        rv009 = [v for v in result.violations if v.rule_id == "RV-009"]
        assert len(rv009) == 0


# ===========================================================================
# P-15: Multiple Violations — All Reported
# ===========================================================================

class TestP15_MultipleViolations:
    """P-15: Multiple MV patterns all reported, no early break (DD-05)."""

    def test_three_violations_all_reported(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "Kael rolled a 19, dealing 14 damage to the goblin (42 HP remaining).",
            brief,
        )
        assert result.verdict == "FAIL"
        rv009 = [v for v in result.violations if v.rule_id == "RV-009"]
        # MV-01 (damage), MV-03 (HP), MV-06 (rolled)
        assert len(rv009) >= 3


# ===========================================================================
# P-16: RV-004 Underscore Fix — Condition Keyword Normalization
# ===========================================================================

class TestP16_RV004UnderscoreFix:
    """P-16: Underscore in condition name matches space-separated narration text."""

    def test_mummy_rot_underscore_matches(self, validator):
        brief = MockBrief(
            action_type="condition_removed",
            condition_removed="mummy_rot",
        )
        result = validator.validate(
            "Seraphine's holy light banishes the mummy rot from Grunk's skin.",
            brief,
        )
        rv004 = [v for v in result.violations if v.rule_id == "RV-004"]
        assert len(rv004) == 0, f"RV-004 should not fire — 'mummy_rot' should match 'mummy rot'. Got: {rv004}"

    def test_underscore_condition_applied(self, validator):
        brief = MockBrief(
            action_type="condition_applied",
            condition_applied="mummy_rot",
        )
        result = validator.validate(
            "The mummy rot creeps through Grunk's veins, darkening his skin.",
            brief,
        )
        rv004 = [v for v in result.violations if v.rule_id == "RV-004"]
        assert len(rv004) == 0


# ===========================================================================
# P-17: MV-03 Variant — "hit points" with space
# ===========================================================================

class TestP17_HitPointsVariant:
    """P-17: "12 hit points" must be caught by RV-009 (MV-03)."""

    def test_hit_points_with_space_detected(self, validator):
        brief = MockBrief()
        result = validator.validate(
            "The goblin has only 12 hit points left.",
            brief,
        )
        assert result.verdict == "FAIL"
        rv009 = [v for v in result.violations if v.rule_id == "RV-009"]
        assert any("MV-03" in v.detail for v in rv009)


# ===========================================================================
# P-18: Existing Rules Still Work — No Regression
# ===========================================================================

class TestP18_NoRegression:
    """P-18: Baseline Hooligan scenarios H-01, H-02, H-03 still PASS."""

    def test_h01_melee_hit_clean(self, validator):
        """H-01: Standard melee hit with clean narration."""
        brief = MockBrief(action_type="attack_hit", severity="moderate")
        result = validator.validate(
            "Kael's longsword bites into the goblin's shoulder, sending the "
            "creature reeling. Green blood wells from the deep wound.",
            brief,
        )
        assert result.verdict != "FAIL", f"H-01 baseline should not FAIL: {result.violations}"

    def test_h02_miss_clean(self, validator):
        """H-02: Standard miss with clean narration."""
        brief = MockBrief(action_type="attack_miss", severity="minor")
        result = validator.validate(
            "Grunk's battleaxe whistles through empty air where the skeleton "
            "stood moments ago. The undead warrior sidesteps with unnatural grace.",
            brief,
        )
        assert result.verdict != "FAIL", f"H-02 baseline should not FAIL: {result.violations}"

    def test_h03_kill_shot_clean(self, validator):
        """H-03: Kill shot with clean narration."""
        brief = MockBrief(
            action_type="attack_hit",
            severity="devastating",
            target_defeated=True,
            target_name="Dire Wolf Alpha",
        )
        result = validator.validate(
            "Vex's arrow strikes true, punching through the dire wolf's thick "
            "hide. The great beast crashes to the forest floor, ending its "
            "reign over the pack.",
            brief,
        )
        assert result.verdict != "FAIL", f"H-03 baseline should not FAIL: {result.violations}"
