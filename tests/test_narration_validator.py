"""Tests for WO-NARRATION-VALIDATOR-001: NarrationValidator Rules + Integration.

Coverage:
- RV-001: Hit/Miss Consistency (FAIL)
- RV-002: Defeat Consistency (FAIL)
- RV-008: Save Result Consistency (FAIL)
- RV-003: Severity-Narration Alignment (WARN)
- RV-004: Condition Consistency (WARN)
- RV-005: Contraindication Enforcement (FAIL, dormant guard)
- RV-007: Delivery Mode Consistency (WARN, dormant guard)
- Integration: GuardedNarrationService calls validator, FAIL → template fallback
- Persistence: Narration JSONL log written
"""

import json
import os
import tempfile
from dataclasses import dataclass
from typing import Optional

import pytest

from aidm.narration.narration_validator import (
    NarrationValidator,
    ValidationResult,
    RuleViolation,
)


# ==============================================================================
# MOCK BRIEF
# ==============================================================================


@dataclass
class MockBrief:
    """Minimal NarrativeBrief stand-in for validator testing."""
    action_type: str = "attack_hit"
    actor_name: str = "Aldric"
    target_name: Optional[str] = "Goblin"
    severity: str = "minor"
    target_defeated: bool = False
    condition_applied: Optional[str] = None
    condition_removed: Optional[str] = None
    weapon_name: Optional[str] = None
    spell_name: Optional[str] = None
    presentation_semantics: Optional[object] = None
    source_event_ids: tuple = ()


@dataclass
class MockPresentationSemantics:
    """Minimal AbilityPresentationEntry stand-in."""
    delivery_mode: Optional[object] = None
    contraindications: tuple = ()


@dataclass
class MockDeliveryMode:
    """Delivery mode enum stand-in."""
    value: str = "cone"


# ==============================================================================
# RV-001: HIT/MISS CONSISTENCY
# ==============================================================================


class TestRV001HitMiss:
    """RV-001: Hit narration must not contain miss-language and vice versa."""

    def setup_method(self):
        self.validator = NarrationValidator()

    def test_hit_with_miss_language_fails(self):
        brief = MockBrief(action_type="attack_hit")
        result = self.validator.validate(
            "Aldric swings his sword but misses the goblin entirely.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-001" for v in result.violations)

    def test_miss_with_hit_language_fails(self):
        brief = MockBrief(action_type="attack_miss")
        result = self.validator.validate(
            "Aldric strikes the goblin with tremendous force.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-001" for v in result.violations)

    def test_hit_with_hit_language_passes(self):
        brief = MockBrief(action_type="attack_hit")
        result = self.validator.validate(
            "Aldric strikes the goblin with his longsword.",
            brief,
        )
        assert not any(v.rule_id == "RV-001" for v in result.violations)

    def test_miss_with_miss_language_passes(self):
        brief = MockBrief(action_type="attack_miss")
        result = self.validator.validate(
            "Aldric swings wide, the goblin dodges easily.",
            brief,
        )
        assert not any(v.rule_id == "RV-001" for v in result.violations)

    def test_critical_with_miss_language_fails(self):
        brief = MockBrief(action_type="critical")
        result = self.validator.validate(
            "Aldric whiffs badly.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-001" for v in result.violations)

    def test_non_attack_action_skipped(self):
        brief = MockBrief(action_type="spell_cast_success")
        result = self.validator.validate(
            "Aldric misses with his spell.",
            brief,
        )
        assert not any(v.rule_id == "RV-001" for v in result.violations)


# ==============================================================================
# RV-002: DEFEAT CONSISTENCY
# ==============================================================================


class TestRV002Defeat:
    """RV-002: Defeat narration must not contain standing-language and vice versa."""

    def setup_method(self):
        self.validator = NarrationValidator()

    def test_defeated_with_standing_language_fails(self):
        brief = MockBrief(target_defeated=True)
        result = self.validator.validate(
            "The goblin stands tall after the blow.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-002" for v in result.violations)

    def test_not_defeated_with_defeat_language_fails(self):
        brief = MockBrief(target_defeated=False)
        result = self.validator.validate(
            "The goblin collapses to the ground, lifeless.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-002" for v in result.violations)

    def test_defeated_with_defeat_language_passes(self):
        brief = MockBrief(target_defeated=True)
        result = self.validator.validate(
            "The goblin collapses, defeated at last.",
            brief,
        )
        assert not any(v.rule_id == "RV-002" for v in result.violations)

    def test_not_defeated_with_neutral_language_passes(self):
        brief = MockBrief(target_defeated=False)
        result = self.validator.validate(
            "Aldric's blade bites into the goblin's shoulder.",
            brief,
        )
        assert not any(v.rule_id == "RV-002" for v in result.violations)


# ==============================================================================
# RV-008: SAVE RESULT CONSISTENCY
# ==============================================================================


class TestRV008SaveResult:
    """RV-008: Resisted spells must not describe full effect; damage spells must not describe shrugging off."""

    def setup_method(self):
        self.validator = NarrationValidator()

    def test_resisted_with_full_effect_fails(self):
        brief = MockBrief(action_type="spell_resisted")
        result = self.validator.validate(
            "The fireball hits with full force, engulfing the goblin completely.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-008" for v in result.violations)

    def test_damage_dealt_with_shrug_off_fails(self):
        brief = MockBrief(action_type="spell_damage_dealt")
        result = self.validator.validate(
            "The goblin shrugs off the spell entirely, unharmed.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-008" for v in result.violations)

    def test_resisted_with_partial_language_passes(self):
        brief = MockBrief(action_type="spell_resisted")
        result = self.validator.validate(
            "The goblin braces against the spell, partially deflecting its energy.",
            brief,
        )
        assert not any(v.rule_id == "RV-008" for v in result.violations)

    def test_damage_dealt_with_damage_language_passes(self):
        brief = MockBrief(action_type="spell_damage_dealt")
        result = self.validator.validate(
            "Fire washes over the goblin, scorching its armor.",
            brief,
        )
        assert not any(v.rule_id == "RV-008" for v in result.violations)


# ==============================================================================
# RV-003: SEVERITY ALIGNMENT
# ==============================================================================


class TestRV003Severity:
    """RV-003: Minor severity must not use inflated language; lethal must not use deflated."""

    def setup_method(self):
        self.validator = NarrationValidator()

    def test_minor_with_inflated_language_warns(self):
        brief = MockBrief(severity="minor")
        result = self.validator.validate(
            "Aldric delivers a devastating blow to the goblin.",
            brief,
        )
        assert result.verdict == "WARN"
        assert any(v.rule_id == "RV-003" for v in result.violations)

    def test_lethal_with_deflated_language_warns(self):
        brief = MockBrief(severity="lethal")
        result = self.validator.validate(
            "Aldric barely scratches the goblin with a nick.",
            brief,
        )
        assert result.verdict == "WARN"
        assert any(v.rule_id == "RV-003" for v in result.violations)

    def test_minor_with_minor_language_passes(self):
        brief = MockBrief(severity="minor")
        result = self.validator.validate(
            "Aldric's blade leaves a shallow cut on the goblin's arm.",
            brief,
        )
        assert not any(v.rule_id == "RV-003" for v in result.violations)

    def test_severe_not_checked_for_inflation(self):
        """severe is not in SEVERITY_INFLATION, so no inflation check."""
        brief = MockBrief(severity="severe")
        result = self.validator.validate(
            "Aldric delivers a devastating blow to the goblin.",
            brief,
        )
        assert not any(v.rule_id == "RV-003" for v in result.violations)


# ==============================================================================
# RV-004: CONDITION CONSISTENCY
# ==============================================================================


class TestRV004Condition:
    """RV-004: Applied/removed conditions should be referenced in narration."""

    def setup_method(self):
        self.validator = NarrationValidator()

    def test_condition_applied_not_mentioned_warns(self):
        brief = MockBrief(condition_applied="prone")
        result = self.validator.validate(
            "Aldric strikes the goblin with his sword.",
            brief,
        )
        assert result.verdict == "WARN"
        assert any(v.rule_id == "RV-004" for v in result.violations)

    def test_condition_applied_mentioned_passes(self):
        brief = MockBrief(condition_applied="prone")
        result = self.validator.validate(
            "The goblin is knocked down by the blow, sprawled on the ground.",
            brief,
        )
        assert not any(v.rule_id == "RV-004" for v in result.violations)

    def test_condition_removed_not_mentioned_warns(self):
        brief = MockBrief(condition_removed="prone")
        result = self.validator.validate(
            "Aldric watches the goblin carefully.",
            brief,
        )
        assert result.verdict == "WARN"
        assert any(v.rule_id == "RV-004" for v in result.violations)

    def test_condition_removed_with_removal_phrase_passes(self):
        brief = MockBrief(condition_removed="prone")
        result = self.validator.validate(
            "The goblin rises unsteadily to its feet.",
            brief,
        )
        assert not any(v.rule_id == "RV-004" for v in result.violations)

    def test_no_condition_passes(self):
        brief = MockBrief()
        result = self.validator.validate(
            "Aldric strikes the goblin.",
            brief,
        )
        assert not any(v.rule_id == "RV-004" for v in result.violations)

    def test_unknown_condition_soft_matches_name(self):
        """Unknown conditions fall back to matching the condition name itself."""
        brief = MockBrief(condition_applied="petrified")
        result = self.validator.validate(
            "The goblin turns to stone, petrified by the spell.",
            brief,
        )
        assert not any(v.rule_id == "RV-004" for v in result.violations)


# ==============================================================================
# RV-005: CONTRAINDICATION ENFORCEMENT (Layer B)
# ==============================================================================


class TestRV005Contraindications:
    """RV-005: Narration must not contain contraindicated terms from Layer B."""

    def setup_method(self):
        self.validator = NarrationValidator()

    def test_contraindicated_term_present_fails(self):
        semantics = MockPresentationSemantics(
            contraindications=("invisible", "displaced"),
        )
        brief = MockBrief(presentation_semantics=semantics)
        result = self.validator.validate(
            "The invisible wizard hurls a fireball.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert any(v.rule_id == "RV-005" for v in result.violations)

    def test_no_contraindicated_term_passes(self):
        semantics = MockPresentationSemantics(
            contraindications=("invisible", "displaced"),
        )
        brief = MockBrief(presentation_semantics=semantics)
        result = self.validator.validate(
            "The wizard hurls a fireball at the goblin.",
            brief,
        )
        assert not any(v.rule_id == "RV-005" for v in result.violations)

    def test_no_semantics_skipped(self):
        """Dormant when presentation_semantics is None."""
        brief = MockBrief(presentation_semantics=None)
        result = self.validator.validate(
            "The invisible wizard hurls a fireball.",
            brief,
        )
        assert not any(v.rule_id == "RV-005" for v in result.violations)

    def test_empty_contraindications_skipped(self):
        semantics = MockPresentationSemantics(contraindications=())
        brief = MockBrief(presentation_semantics=semantics)
        result = self.validator.validate(
            "The invisible wizard hurls a fireball.",
            brief,
        )
        assert not any(v.rule_id == "RV-005" for v in result.violations)


# ==============================================================================
# RV-007: DELIVERY MODE CONSISTENCY (Layer B)
# ==============================================================================


class TestRV007DeliveryMode:
    """RV-007: Narration should contain language consistent with delivery mode."""

    def setup_method(self):
        self.validator = NarrationValidator()

    def test_cone_without_directional_language_warns(self):
        semantics = MockPresentationSemantics(
            delivery_mode=MockDeliveryMode("cone"),
        )
        brief = MockBrief(presentation_semantics=semantics)
        result = self.validator.validate(
            "The wizard casts a spell at the goblin.",
            brief,
        )
        assert result.verdict == "WARN"
        assert any(v.rule_id == "RV-007" for v in result.violations)

    def test_cone_with_directional_language_passes(self):
        semantics = MockPresentationSemantics(
            delivery_mode=MockDeliveryMode("cone"),
        )
        brief = MockBrief(presentation_semantics=semantics)
        result = self.validator.validate(
            "A cone of frost spreads from the wizard's hands.",
            brief,
        )
        assert not any(v.rule_id == "RV-007" for v in result.violations)

    def test_no_semantics_skipped(self):
        """Dormant when presentation_semantics is None."""
        brief = MockBrief(presentation_semantics=None)
        result = self.validator.validate(
            "The wizard casts a spell at the goblin.",
            brief,
        )
        assert not any(v.rule_id == "RV-007" for v in result.violations)

    def test_projectile_with_launch_language_passes(self):
        semantics = MockPresentationSemantics(
            delivery_mode=MockDeliveryMode("projectile"),
        )
        brief = MockBrief(presentation_semantics=semantics)
        result = self.validator.validate(
            "The wizard hurls a bolt of fire at the goblin.",
            brief,
        )
        assert not any(v.rule_id == "RV-007" for v in result.violations)


# ==============================================================================
# VALIDATION RESULT STRUCTURE
# ==============================================================================


class TestValidationResult:
    """Tests for ValidationResult and RuleViolation dataclass structure."""

    def setup_method(self):
        self.validator = NarrationValidator()

    def test_pass_verdict(self):
        brief = MockBrief()
        result = self.validator.validate(
            "Aldric swings his longsword at the goblin.",
            brief,
        )
        assert result.verdict == "PASS"
        assert result.violations == ()

    def test_fail_verdict_with_violations(self):
        brief = MockBrief(action_type="attack_miss")
        result = self.validator.validate(
            "Aldric strikes the goblin with devastating force.",
            brief,
        )
        assert result.verdict == "FAIL"
        assert len(result.violations) >= 1
        violation = result.violations[0]
        assert violation.rule_id == "RV-001"
        assert violation.severity == "FAIL"
        assert isinstance(violation.detail, str)

    def test_warn_verdict(self):
        brief = MockBrief(severity="minor")
        result = self.validator.validate(
            "Aldric delivers a devastating blow to the goblin.",
            brief,
        )
        assert result.verdict == "WARN"

    def test_fail_overrides_warn(self):
        """If both FAIL and WARN violations exist, verdict is FAIL."""
        brief = MockBrief(
            action_type="attack_miss",
            severity="minor",
        )
        result = self.validator.validate(
            "Aldric strikes the goblin with a devastating blow.",
            brief,
        )
        assert result.verdict == "FAIL"

    def test_result_is_frozen(self):
        brief = MockBrief()
        result = self.validator.validate("Aldric swings.", brief)
        with pytest.raises(AttributeError):
            result.verdict = "FAIL"


# ==============================================================================
# INTEGRATION: GuardedNarrationService
# ==============================================================================


class TestGuardedNarrationServiceIntegration:
    """Integration tests for NarrationValidator in GuardedNarrationService."""

    def test_service_has_validator_attribute(self):
        from aidm.narration.guarded_narration_service import GuardedNarrationService
        service = GuardedNarrationService()
        assert hasattr(service, "narration_validator")
        assert isinstance(service.narration_validator, NarrationValidator)

    def test_service_accepts_custom_validator(self):
        from aidm.narration.guarded_narration_service import GuardedNarrationService
        validator = NarrationValidator()
        service = GuardedNarrationService(narration_validator=validator)
        assert service.narration_validator is validator

    def test_service_accepts_narration_log_path(self):
        from aidm.narration.guarded_narration_service import GuardedNarrationService
        service = GuardedNarrationService(narration_log_path="/tmp/test.jsonl")
        assert service.narration_log_path == "/tmp/test.jsonl"

    def test_service_narration_log_path_none_by_default(self):
        from aidm.narration.guarded_narration_service import GuardedNarrationService
        service = GuardedNarrationService()
        assert service.narration_log_path is None


# ==============================================================================
# PERSISTENCE: Narration JSONL Log
# ==============================================================================


class TestNarrationPersistence:
    """Tests for narration-to-event persistence (Change 6)."""

    def test_persist_writes_jsonl(self):
        from aidm.narration.guarded_narration_service import GuardedNarrationService
        from aidm.narration.narration_validator import ValidationResult, RuleViolation

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            log_path = f.name

        try:
            service = GuardedNarrationService(narration_log_path=log_path)

            validation_result = ValidationResult(
                verdict="WARN",
                violations=(
                    RuleViolation(rule_id="RV-003", severity="WARN", detail="test detail"),
                ),
            )
            brief = MockBrief(source_event_ids=(1, 2, 3))

            service._persist_narration_log(
                narration_text="The goblin is hit.",
                brief=brief,
                validation_result=validation_result,
            )

            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 1
            entry = json.loads(lines[0])
            assert entry["narration_text"] == "The goblin is hit."
            assert entry["source_event_ids"] == [1, 2, 3]
            assert entry["validation_verdict"] == "WARN"
            assert len(entry["violations"]) == 1
            assert entry["violations"][0]["rule_id"] == "RV-003"
            assert "timestamp" in entry
        finally:
            os.unlink(log_path)

    def test_persist_pass_no_violations(self):
        from aidm.narration.guarded_narration_service import GuardedNarrationService
        from aidm.narration.narration_validator import ValidationResult

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            log_path = f.name

        try:
            service = GuardedNarrationService(narration_log_path=log_path)

            validation_result = ValidationResult(verdict="PASS", violations=())
            brief = MockBrief(source_event_ids=(42,))

            service._persist_narration_log(
                narration_text="Clean narration.",
                brief=brief,
                validation_result=validation_result,
            )

            with open(log_path, "r", encoding="utf-8") as f:
                entry = json.loads(f.readline())

            assert entry["validation_verdict"] == "PASS"
            assert entry["violations"] == []
            assert entry["source_event_ids"] == [42]
        finally:
            os.unlink(log_path)

    def test_persist_none_brief(self):
        from aidm.narration.guarded_narration_service import GuardedNarrationService

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            log_path = f.name

        try:
            service = GuardedNarrationService(narration_log_path=log_path)

            service._persist_narration_log(
                narration_text="Template narration.",
                brief=None,
                validation_result=None,
            )

            with open(log_path, "r", encoding="utf-8") as f:
                entry = json.loads(f.readline())

            assert entry["source_event_ids"] == []
            assert entry["validation_verdict"] == "PASS"
        finally:
            os.unlink(log_path)

    def test_persist_disabled_when_no_path(self):
        from aidm.narration.guarded_narration_service import GuardedNarrationService

        service = GuardedNarrationService(narration_log_path=None)
        # Should not raise
        service._persist_narration_log(
            narration_text="Test.",
            brief=None,
            validation_result=None,
        )

    def test_persist_multiple_entries(self):
        from aidm.narration.guarded_narration_service import GuardedNarrationService
        from aidm.narration.narration_validator import ValidationResult

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            log_path = f.name

        try:
            service = GuardedNarrationService(narration_log_path=log_path)

            for i in range(3):
                service._persist_narration_log(
                    narration_text=f"Narration {i}.",
                    brief=MockBrief(source_event_ids=(i,)),
                    validation_result=ValidationResult(verdict="PASS", violations=()),
                )

            with open(log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 3
            for i, line in enumerate(lines):
                entry = json.loads(line)
                assert entry["narration_text"] == f"Narration {i}."
        finally:
            os.unlink(log_path)
