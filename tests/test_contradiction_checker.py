"""Tests for WO-058 ContradictionChecker v1.

Validates post-hoc contradiction detection against NarrativeBrief truth frame.
Organized by contradiction class (A/B/C) following the scripted brief matrix
from RQ-LENS-002.

Test Plan:
- Class A: Entity state contradictions
  - Defeat keywords in non-defeat context (and absence in defeat context)
  - Hit keywords in miss context (and vice versa)
  - Severity inflation and deflation
  - Stance contradictions (prone/standing)
- Class B: Outcome contradictions
  - Wrong weapon name
  - Wrong damage type
- Class C: Continuity contradictions
  - Indoor/outdoor scene mismatch
- Response policy: escalation from retry → template_fallback
- Retry correction prompt generation
- False positive avoidance (correct narration should pass)

Evidence:
- RQ-LENS-SPARK-001: Context Orchestration Sprint (Deliverable 4)
- RQ-LENS-002: Contradiction Surface Mapping (scripted brief matrix)
- WO-058: ContradictionChecker v1

PHB References:
- Severity mapping: derived from HP percentage thresholds
- Weapon/damage types: PHB Chapter 7 (Equipment)
"""

import pytest

from aidm.narration.contradiction_checker import (
    ContradictionChecker,
    ContradictionClass,
    ContradictionMatch,
    ContradictionResult,
    RecommendedAction,
)


# ==============================================================================
# HELPERS — Minimal NarrativeBrief-like objects
# ==============================================================================


class MockBrief:
    """Lightweight NarrativeBrief stand-in for testing.

    Uses the same field names as NarrativeBrief so ContradictionChecker
    can use getattr() on it.
    """
    def __init__(self, **kwargs):
        self.action_type = kwargs.get('action_type', 'attack_hit')
        self.actor_name = kwargs.get('actor_name', 'Kael')
        self.target_name = kwargs.get('target_name', 'Goblin Scout')
        self.outcome_summary = kwargs.get('outcome_summary', '')
        self.severity = kwargs.get('severity', 'minor')
        self.weapon_name = kwargs.get('weapon_name', None)
        self.damage_type = kwargs.get('damage_type', None)
        self.condition_applied = kwargs.get('condition_applied', None)
        self.target_defeated = kwargs.get('target_defeated', False)
        self.scene_description = kwargs.get('scene_description', None)
        self.previous_narrations = kwargs.get('previous_narrations', [])


# ==============================================================================
# CLASS A: DEFEAT KEYWORDS
# ==============================================================================


class TestDefeatKeywords:
    """RQ-LENS-002 Briefs 1-2: Defeat keywords in hit/non-defeat context."""

    def test_defeat_keyword_in_non_defeat_flags(self):
        """Brief #1: Hit, not defeated — 'collapses' should be flagged."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False, severity='moderate')
        result = checker.check("The goblin collapses to the ground.", brief)

        assert result.has_contradiction
        assert result.matches[0].subtype == "defeat_in_non_defeat"
        assert result.matches[0].contradiction_class == ContradictionClass.CLASS_A

    def test_multiple_defeat_keywords_only_one_match(self):
        """Only one defeat keyword match needed to flag."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)
        result = checker.check("The ogre falls unconscious and dies.", brief)

        assert result.has_contradiction
        # Should have exactly 1 match (breaks after first)
        defeat_matches = [m for m in result.matches
                          if m.subtype == "defeat_in_non_defeat"]
        assert len(defeat_matches) == 1

    def test_defeat_keyword_in_defeat_context_passes(self):
        """Brief #2: Hit, defeated — defeat keywords are expected."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=True, severity='lethal')
        result = checker.check("The goblin collapses, slain by the blow.", brief)

        # Should NOT flag defeat keywords when target IS defeated
        defeat_matches = [m for m in result.matches
                          if m.subtype == "defeat_in_non_defeat"]
        assert len(defeat_matches) == 0

    def test_no_defeat_keywords_passes(self):
        """Clean narration without defeat keywords passes."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False, severity='moderate')
        result = checker.check(
            "Kael's longsword bites into the goblin's shoulder.",
            brief,
        )

        defeat_matches = [m for m in result.matches
                          if m.subtype == "defeat_in_non_defeat"]
        assert len(defeat_matches) == 0

    def test_falls_keyword_detected(self):
        """'falls' is in DEFEAT_KEYWORDS and should trigger."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)
        result = checker.check("The creature falls to the ground.", brief)

        assert result.has_contradiction
        assert "falls" in result.matches[0].matched_text.lower()

    def test_lifeless_keyword_detected(self):
        """'lifeless' is in DEFEAT_KEYWORDS."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)
        result = checker.check("The body lies lifeless on the floor.", brief)

        assert result.has_contradiction

    def test_unconscious_keyword_detected(self):
        """'unconscious' is in DEFEAT_KEYWORDS."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)
        result = checker.check("The orc drops unconscious.", brief)

        assert result.has_contradiction


# ==============================================================================
# CLASS A: HIT/MISS KEYWORDS
# ==============================================================================


class TestHitMissKeywords:
    """RQ-LENS-002 Briefs 3-4: Hit/miss keyword context checking."""

    def test_hit_keyword_in_miss_context_flags(self):
        """Brief #3: Miss — 'strikes' should be flagged."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='attack_miss')
        result = checker.check("Kael strikes the goblin with force.", brief)

        assert result.has_contradiction
        assert result.matches[0].subtype == "hit_keyword_in_miss"
        assert result.matches[0].contradiction_class == ContradictionClass.CLASS_A

    def test_miss_keyword_in_hit_context_flags(self):
        """Brief #1: Hit — 'misses' should be flagged."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='attack_hit')
        result = checker.check("Kael misses the goblin entirely.", brief)

        assert result.has_contradiction
        assert result.matches[0].subtype == "miss_keyword_in_hit"

    def test_concealment_miss_flags_hit_keywords(self):
        """Brief #35: Concealment miss — hit keywords should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='concealment_miss')
        result = checker.check("The blade pierces through the fog.", brief)

        assert result.has_contradiction
        assert result.matches[0].subtype == "hit_keyword_in_miss"

    def test_spell_no_effect_flags_hit_keywords(self):
        """Brief #6: Spell no effect — hit keywords should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='spell_no_effect')
        result = checker.check("The spell hits the target with full force.", brief)

        assert result.has_contradiction

    def test_spell_resisted_flags_hit_keywords(self):
        """Brief #36: Spell resisted — hit keywords should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='spell_resisted')
        result = checker.check("The spell connects and wounds the ogre.", brief)

        assert result.has_contradiction

    def test_correct_miss_narration_passes(self):
        """Miss narration describing a miss should pass."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='attack_miss')
        result = checker.check(
            "Kael's blade goes wide, sailing past the goblin.",
            brief,
        )

        hit_miss_matches = [m for m in result.matches
                            if m.subtype in ("hit_keyword_in_miss", "miss_keyword_in_hit")]
        assert len(hit_miss_matches) == 0

    def test_correct_hit_narration_passes(self):
        """Hit narration describing a hit should pass."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='attack_hit', severity='moderate')
        result = checker.check(
            "The longsword finds its mark, biting into the goblin's flank.",
            brief,
        )

        miss_matches = [m for m in result.matches
                        if m.subtype == "miss_keyword_in_hit"]
        assert len(miss_matches) == 0

    def test_dodges_in_miss_context_passes(self):
        """'dodges' in miss context is CORRECT — should NOT flag."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='attack_miss')
        result = checker.check(
            "The goblin dodges the incoming blow with surprising agility.",
            brief,
        )

        # 'dodges' is a MISS keyword — in a miss context, it's correct
        hit_matches = [m for m in result.matches
                       if m.subtype == "hit_keyword_in_miss"]
        assert len(hit_matches) == 0

    def test_critical_hit_is_hit_context(self):
        """Brief #4: Critical — hit keywords should pass, miss should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='critical', severity='devastating')
        result = checker.check(
            "The blade misses its target completely.",
            brief,
        )

        assert result.has_contradiction
        assert result.matches[0].subtype == "miss_keyword_in_hit"


# ==============================================================================
# CLASS A: SEVERITY
# ==============================================================================


class TestSeverity:
    """RQ-LENS-002 Briefs 16-20: Severity inflation/deflation."""

    def test_severity_inflation_minor(self):
        """Brief #16: Minor hit — 'devastating' should flag as inflation."""
        checker = ContradictionChecker()
        brief = MockBrief(severity='minor')
        result = checker.check(
            "A devastating blow cripples the goblin.",
            brief,
        )

        assert result.has_contradiction
        assert result.matches[0].subtype == "severity_inflation"

    def test_severity_inflation_moderate(self):
        """Brief #17: Moderate hit — 'lethal' should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(severity='moderate')
        result = checker.check(
            "A lethal strike sends the goblin reeling.",
            brief,
        )

        assert result.has_contradiction
        assert result.matches[0].subtype == "severity_inflation"

    def test_severity_deflation_lethal(self):
        """Brief #20: Lethal hit — 'scratches' should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(severity='lethal', target_defeated=True)
        result = checker.check(
            "The blade barely scratches the surface.",
            brief,
        )

        assert result.has_contradiction
        severity_matches = [m for m in result.matches
                            if m.subtype == "severity_deflation"]
        assert len(severity_matches) > 0

    def test_severity_deflation_devastating(self):
        """Brief #19: Devastating hit — 'minor' should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(severity='devastating')
        result = checker.check(
            "A minor wound opens on the ogre's arm.",
            brief,
        )

        assert result.has_contradiction
        assert result.matches[0].subtype == "severity_deflation"

    def test_moderate_severity_correct_passes(self):
        """Moderate severity with appropriate language passes."""
        checker = ContradictionChecker()
        brief = MockBrief(severity='moderate')
        result = checker.check(
            "The sword bites into the goblin's shoulder, drawing a pained grunt.",
            brief,
        )

        severity_matches = [m for m in result.matches
                            if m.subtype in ("severity_inflation", "severity_deflation")]
        assert len(severity_matches) == 0

    def test_severe_severity_not_inflated_by_dramatic(self):
        """Severe severity — 'dramatic' is not in inflation list."""
        checker = ContradictionChecker()
        brief = MockBrief(severity='severe')
        result = checker.check(
            "A dramatic swing catches the ogre across the chest.",
            brief,
        )

        severity_matches = [m for m in result.matches
                            if m.subtype in ("severity_inflation", "severity_deflation")]
        assert len(severity_matches) == 0


# ==============================================================================
# CLASS A: STANCE
# ==============================================================================


class TestStance:
    """RQ-LENS-002 Briefs 8-9: Stance contradictions."""

    def test_standing_keyword_when_prone_flags(self):
        """Brief #8: Trip success — 'stands tall' should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(
            action_type='trip_success',
            condition_applied='prone',
        )
        result = checker.check(
            "The ogre stands tall, unfazed by the attack.",
            brief,
        )

        assert result.has_contradiction
        assert result.matches[0].subtype == "stance_contradiction"

    def test_prone_description_when_prone_passes(self):
        """Prone description when condition_applied=prone should pass."""
        checker = ContradictionChecker()
        brief = MockBrief(
            action_type='trip_success',
            condition_applied='prone',
        )
        result = checker.check(
            "The ogre crashes to the ground, sprawled in the dirt.",
            brief,
        )

        stance_matches = [m for m in result.matches
                          if m.subtype == "stance_contradiction"]
        assert len(stance_matches) == 0

    def test_no_stance_check_when_no_condition(self):
        """No stance check when condition_applied is None."""
        checker = ContradictionChecker()
        brief = MockBrief(condition_applied=None)
        result = checker.check(
            "The warrior stands tall before the enemy.",
            brief,
        )

        stance_matches = [m for m in result.matches
                          if m.subtype == "stance_contradiction"]
        assert len(stance_matches) == 0


# ==============================================================================
# CLASS B: WEAPON NAME
# ==============================================================================


class TestWeaponName:
    """RQ-LENS-002 Briefs 21-22: Weapon name substitution."""

    def test_wrong_weapon_flags(self):
        """Brief #21: Longsword — 'greataxe' should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(weapon_name='longsword')
        result = checker.check(
            "Kael swings his greataxe in a wide arc.",
            brief,
        )

        assert result.has_contradiction
        assert result.matches[0].subtype == "wrong_weapon"
        assert result.matches[0].contradiction_class == ContradictionClass.CLASS_B

    def test_correct_weapon_passes(self):
        """Correct weapon name in narration passes."""
        checker = ContradictionChecker()
        brief = MockBrief(weapon_name='longsword')
        result = checker.check(
            "Kael's longsword flashes in the torchlight.",
            brief,
        )

        weapon_matches = [m for m in result.matches
                          if m.subtype == "wrong_weapon"]
        assert len(weapon_matches) == 0

    def test_both_weapons_mentioned_passes(self):
        """If correct weapon IS mentioned alongside another, passes."""
        checker = ContradictionChecker()
        brief = MockBrief(weapon_name='longsword')
        result = checker.check(
            "Kael draws his longsword, ignoring the dagger at his belt.",
            brief,
        )

        weapon_matches = [m for m in result.matches
                          if m.subtype == "wrong_weapon"]
        assert len(weapon_matches) == 0

    def test_no_weapon_name_skips_check(self):
        """No weapon_name in brief → skip weapon check."""
        checker = ContradictionChecker()
        brief = MockBrief(weapon_name=None)
        result = checker.check(
            "The warrior swings his greataxe.",
            brief,
        )

        weapon_matches = [m for m in result.matches
                          if m.subtype == "wrong_weapon"]
        assert len(weapon_matches) == 0


# ==============================================================================
# CLASS B: DAMAGE TYPE
# ==============================================================================


class TestDamageType:
    """RQ-LENS-002 Briefs 27-28: Damage type language."""

    def test_fire_language_for_slashing_flags(self):
        """Brief #28: Slashing damage — 'burn' language should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(damage_type='slashing')
        result = checker.check(
            "The flames burn through the ogre's hide.",
            brief,
        )

        assert result.has_contradiction
        assert result.matches[0].subtype == "wrong_damage_type"
        assert result.matches[0].contradiction_class == ContradictionClass.CLASS_B

    def test_slashing_language_for_fire_flags(self):
        """Brief #27: Fire damage — 'slash' language should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(damage_type='fire')
        result = checker.check(
            "The blade slashes across the ogre's chest.",
            brief,
        )

        assert result.has_contradiction
        assert result.matches[0].subtype == "wrong_damage_type"

    def test_correct_damage_type_passes(self):
        """Correct damage type language passes."""
        checker = ContradictionChecker()
        brief = MockBrief(damage_type='fire')
        result = checker.check(
            "Flames scorch the goblin's armor, searing flesh beneath.",
            brief,
        )

        damage_matches = [m for m in result.matches
                          if m.subtype == "wrong_damage_type"]
        assert len(damage_matches) == 0

    def test_no_damage_type_skips_check(self):
        """No damage_type in brief → skip check."""
        checker = ContradictionChecker()
        brief = MockBrief(damage_type=None)
        result = checker.check(
            "The blast freezes the air around the goblin.",
            brief,
        )

        damage_matches = [m for m in result.matches
                          if m.subtype == "wrong_damage_type"]
        assert len(damage_matches) == 0

    def test_cold_language_for_cold_passes(self):
        """Cold damage with cold language passes."""
        checker = ContradictionChecker()
        brief = MockBrief(damage_type='cold')
        result = checker.check(
            "A wave of frost envelops the goblin, chilling it to the bone.",
            brief,
        )

        damage_matches = [m for m in result.matches
                          if m.subtype == "wrong_damage_type"]
        assert len(damage_matches) == 0


# ==============================================================================
# CLASS C: SCENE CONTINUITY
# ==============================================================================


class TestSceneContinuity:
    """RQ-LENS-002 Briefs 29-30: Scene description continuity."""

    def test_outdoor_in_indoor_scene_flags(self):
        """Brief #29: Dungeon — 'forest' should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(
            scene_description='a narrow dungeon corridor lit by flickering torches',
        )
        result = checker.check(
            "Kael charges through the forest clearing.",
            brief,
        )

        assert result.has_contradiction
        assert result.matches[0].subtype == "scene_location_mismatch"
        assert result.matches[0].contradiction_class == ContradictionClass.CLASS_C

    def test_indoor_in_outdoor_scene_flags(self):
        """Brief #30: Forest — 'dungeon' should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(
            scene_description='a sun-dappled forest clearing',
        )
        result = checker.check(
            "The echoes bounce off the dungeon walls.",
            brief,
        )

        assert result.has_contradiction
        assert result.matches[0].subtype == "scene_location_mismatch"

    def test_matching_scene_passes(self):
        """Narration matching scene description passes."""
        checker = ContradictionChecker()
        brief = MockBrief(
            scene_description='a narrow dungeon corridor lit by flickering torches',
        )
        result = checker.check(
            "Torchlight glints off the blade as Kael lunges forward in the corridor.",
            brief,
        )

        scene_matches = [m for m in result.matches
                         if m.subtype == "scene_location_mismatch"]
        assert len(scene_matches) == 0

    def test_no_scene_skips_check(self):
        """No scene_description in brief → skip check."""
        checker = ContradictionChecker()
        brief = MockBrief(scene_description=None)
        result = checker.check(
            "The battle rages in the forest.",
            brief,
        )

        scene_matches = [m for m in result.matches
                         if m.subtype == "scene_location_mismatch"]
        assert len(scene_matches) == 0


# ==============================================================================
# RESPONSE POLICY
# ==============================================================================


class TestResponsePolicy:
    """RQ-LENS-SPARK-001 response policy table."""

    def test_class_a_first_occurrence_retry(self):
        """Class A, 1st occurrence → retry."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)
        result = checker.check("The goblin collapses.", brief)

        assert result.recommended_action == RecommendedAction.RETRY

    def test_class_a_second_consecutive_template(self):
        """Class A, 2nd consecutive → template_fallback."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)

        # First contradiction
        checker.check("The goblin collapses.", brief)
        # Second consecutive
        result = checker.check("The goblin dies.", brief)

        assert result.recommended_action == RecommendedAction.TEMPLATE_FALLBACK

    def test_class_a_third_consecutive_template(self):
        """Class A, 3rd consecutive → template_fallback."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)

        checker.check("The goblin collapses.", brief)
        checker.check("The goblin dies.", brief)
        result = checker.check("The goblin falls unconscious.", brief)

        assert result.recommended_action == RecommendedAction.TEMPLATE_FALLBACK

    def test_class_c_first_occurrence_annotate(self):
        """Class C, 1st occurrence → annotate."""
        checker = ContradictionChecker()
        brief = MockBrief(
            scene_description='a narrow dungeon corridor',
        )
        result = checker.check("Kael fights in the forest.", brief)

        assert result.recommended_action == RecommendedAction.ANNOTATE

    def test_class_c_second_consecutive_retry(self):
        """Class C, 2nd consecutive → retry."""
        checker = ContradictionChecker()
        brief = MockBrief(
            scene_description='a narrow dungeon corridor',
        )

        checker.check("Kael fights in the forest.", brief)
        result = checker.check("The meadow stretches before them.", brief)

        assert result.recommended_action == RecommendedAction.RETRY

    def test_clean_narration_resets_consecutive(self):
        """Clean narration after contradiction resets counter."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False, severity='moderate')

        # Trigger a contradiction
        checker.check("The goblin collapses.", brief)
        assert checker.consecutive_contradictions == 1

        # Clean narration resets
        checker.check("Kael's blade bites into the goblin's shoulder.", brief)
        assert checker.consecutive_contradictions == 0

    def test_manual_reset_clears_counter(self):
        """reset_consecutive_count() clears the counter."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)

        checker.check("The goblin dies.", brief)
        assert checker.consecutive_contradictions == 1

        checker.reset_consecutive_count()
        assert checker.consecutive_contradictions == 0


# ==============================================================================
# CONTRADICTION RESULT PROPERTIES
# ==============================================================================


class TestContradictionResult:
    """ContradictionResult dataclass behavior."""

    def test_result_is_frozen(self):
        """ContradictionResult is immutable."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)
        result = checker.check("The goblin collapses.", brief)

        with pytest.raises(AttributeError):
            result.has_contradiction = False

    def test_match_is_frozen(self):
        """ContradictionMatch is immutable."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)
        result = checker.check("The goblin collapses.", brief)

        with pytest.raises(AttributeError):
            result.matches[0].subtype = "modified"

    def test_worst_class_a_over_b(self):
        """worst_class returns A when both A and B present."""
        checker = ContradictionChecker()
        brief = MockBrief(
            target_defeated=False,
            weapon_name='longsword',
        )
        result = checker.check(
            "The goblin collapses as the greataxe cleaves through.",
            brief,
        )

        assert result.worst_class == ContradictionClass.CLASS_A

    def test_worst_class_none_when_clean(self):
        """worst_class is None when no contradictions."""
        checker = ContradictionChecker()
        brief = MockBrief(severity='moderate')
        result = checker.check(
            "The blade strikes true, drawing a grunt from the goblin.",
            brief,
        )

        assert result.worst_class is None

    def test_no_contradiction_result(self):
        """Clean narration returns has_contradiction=False."""
        checker = ContradictionChecker()
        brief = MockBrief(severity='moderate')
        result = checker.check(
            "Kael presses forward with another strike.",
            brief,
        )

        assert not result.has_contradiction
        assert len(result.matches) == 0
        assert result.narration_text == "Kael presses forward with another strike."


# ==============================================================================
# RETRY CORRECTION GENERATION
# ==============================================================================


class TestRetryCorrection:
    """build_retry_correction() prompt augmentation."""

    def test_defeat_correction(self):
        """Defeat contradiction generates appropriate correction text."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)
        result = checker.check("The goblin dies.", brief)
        correction = checker.build_retry_correction(result, brief)

        assert "CORRECTION" in correction
        assert "NOT defeated" in correction

    def test_hit_in_miss_correction(self):
        """Hit-in-miss generates miss correction."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='attack_miss')
        result = checker.check("The blade strikes the goblin.", brief)
        correction = checker.build_retry_correction(result, brief)

        assert "MISSED" in correction

    def test_miss_in_hit_correction(self):
        """Miss-in-hit generates hit correction."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='attack_hit')
        result = checker.check("The blow misses completely.", brief)
        correction = checker.build_retry_correction(result, brief)

        assert "HIT" in correction

    def test_severity_inflation_correction(self):
        """Severity inflation generates appropriate correction."""
        checker = ContradictionChecker()
        brief = MockBrief(severity='minor')
        result = checker.check("A devastating blow shatters bone.", brief)
        correction = checker.build_retry_correction(result, brief)

        assert "minor" in correction.lower()

    def test_wrong_weapon_correction(self):
        """Wrong weapon generates weapon correction."""
        checker = ContradictionChecker()
        brief = MockBrief(weapon_name='longsword')
        result = checker.check("Kael swings his greataxe.", brief)
        correction = checker.build_retry_correction(result, brief)

        assert "longsword" in correction

    def test_scene_mismatch_correction(self):
        """Scene mismatch generates scene correction."""
        checker = ContradictionChecker()
        brief = MockBrief(
            scene_description='a narrow dungeon corridor',
        )
        result = checker.check("Kael charges across the forest.", brief)
        correction = checker.build_retry_correction(result, brief)

        assert "dungeon" in correction.lower()


# ==============================================================================
# FALSE POSITIVE AVOIDANCE
# ==============================================================================


class TestFalsePositiveAvoidance:
    """Correct narrations that should NOT trigger false positives."""

    def test_clean_attack_hit_passes(self):
        """Standard attack hit narration passes all checks."""
        checker = ContradictionChecker()
        brief = MockBrief(
            action_type='attack_hit',
            severity='moderate',
            weapon_name='longsword',
            damage_type='slashing',
            target_defeated=False,
            scene_description='a narrow dungeon corridor',
        )
        result = checker.check(
            "Kael's longsword catches the goblin across the arm, "
            "opening a wound that draws a pained snarl.",
            brief,
        )

        assert not result.has_contradiction

    def test_clean_attack_miss_passes(self):
        """Standard attack miss narration passes."""
        checker = ContradictionChecker()
        brief = MockBrief(action_type='attack_miss')
        result = checker.check(
            "The goblin ducks beneath the sweeping blade, "
            "the steel whistling through empty air.",
            brief,
        )

        assert not result.has_contradiction

    def test_clean_defeat_narration_passes(self):
        """Defeat narration with target_defeated=True passes."""
        checker = ContradictionChecker()
        brief = MockBrief(
            action_type='attack_hit',
            severity='lethal',
            target_defeated=True,
            weapon_name='longsword',
            damage_type='slashing',
        )
        result = checker.check(
            "The longsword carves through the goblin's guard. "
            "The creature collapses, slain.",
            brief,
        )

        assert not result.has_contradiction

    def test_clean_spell_narration_passes(self):
        """Clean spell damage narration passes."""
        checker = ContradictionChecker()
        brief = MockBrief(
            action_type='spell_damage_dealt',
            severity='severe',
            damage_type='fire',
            target_defeated=False,
        )
        result = checker.check(
            "A lance of flame scorches the ogre's chest, "
            "leaving a blackened wound.",
            brief,
        )

        assert not result.has_contradiction

    def test_neutral_prose_passes(self):
        """Generic prose without specific keywords passes."""
        checker = ContradictionChecker()
        brief = MockBrief(severity='minor')
        result = checker.check(
            "The exchange continues, blades moving in a dance of steel.",
            brief,
        )

        assert not result.has_contradiction


# ==============================================================================
# EDGE CASES
# ==============================================================================


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_narration(self):
        """Empty string narration should not crash."""
        checker = ContradictionChecker()
        brief = MockBrief()
        result = checker.check("", brief)

        assert not result.has_contradiction

    def test_very_long_narration(self):
        """Very long narration should complete without error."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)
        long_text = "The warriors clash in fierce combat. " * 100
        result = checker.check(long_text, brief)

        # Should complete without error
        assert isinstance(result, ContradictionResult)

    def test_case_insensitive_keyword_matching(self):
        """Keywords should match case-insensitively."""
        checker = ContradictionChecker()
        brief = MockBrief(target_defeated=False)
        result = checker.check("The goblin COLLAPSES to the ground.", brief)

        assert result.has_contradiction

    def test_multiple_contradiction_classes(self):
        """Narration with multiple classes should report all."""
        checker = ContradictionChecker()
        brief = MockBrief(
            action_type='attack_miss',
            target_defeated=False,
            severity='minor',
            scene_description='a narrow dungeon corridor',
        )
        result = checker.check(
            "Kael strikes the goblin with devastating force in the forest.",
            brief,
        )

        assert result.has_contradiction
        # Should have at least hit-in-miss (A) + severity inflation (A) + scene (C)
        assert len(result.matches) >= 2

    def test_healing_spell_no_false_positive(self):
        """Brief #7: Healing — no damage/defeat keywords should flag."""
        checker = ContradictionChecker()
        brief = MockBrief(
            action_type='spell_healed',
            severity='minor',
        )
        result = checker.check(
            "Warm light flows from the cleric's hands, "
            "mending the warrior's wounds.",
            brief,
        )

        assert not result.has_contradiction

    def test_maneuver_action_not_hit_or_miss(self):
        """Maneuver actions should not trigger hit/miss checks."""
        checker = ContradictionChecker()
        brief = MockBrief(
            action_type='trip_success',
            condition_applied='prone',
        )
        result = checker.check(
            "The warrior sweeps the ogre's legs, sending it sprawling.",
            brief,
        )

        hit_miss = [m for m in result.matches
                    if m.subtype in ("hit_keyword_in_miss", "miss_keyword_in_hit")]
        assert len(hit_miss) == 0
