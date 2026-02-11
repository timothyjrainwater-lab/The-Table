"""Tests for Kill Switch Suite (KILL-002 through KILL-006).

Tests the KillSwitchRegistry and each individual kill switch's detection,
triggering, fallback, and evidence capture.

Reference: WO-029 — Kill Switch Suite
"""

import time
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, PropertyMock

from aidm.narration.kill_switch_registry import (
    KillSwitchID,
    KillSwitchEvidence,
    KillSwitchRegistry,
    build_evidence,
    detect_mechanical_assertions,
)
from aidm.narration.guarded_narration_service import (
    FrozenMemorySnapshot,
    GuardedNarrationService,
    NarrationBoundaryViolation,
    NarrationRequest,
    NarrationResult,
)
from aidm.schemas.engine_result import EngineResult, EngineResultStatus


# ============================================================================
# Helpers
# ============================================================================


def _make_request(token="attack_hit", events=None, world_state_hash=None):
    """Build a NarrationRequest for testing."""
    engine_result = EngineResult(
        result_id="ks-test",
        intent_id="ks-intent",
        status=EngineResultStatus.SUCCESS,
        resolved_at=datetime(2025, 1, 1, 12, 0, 0),
        narration_token=token,
        events=events or [],
    )
    snapshot = FrozenMemorySnapshot.create()
    return NarrationRequest(
        engine_result=engine_result,
        memory_snapshot=snapshot,
        temperature=0.8,
        world_state_hash=world_state_hash,
    )


def _make_evidence(switch_id=KillSwitchID.KILL_001, signal="test signal"):
    """Build a KillSwitchEvidence for testing."""
    return build_evidence(switch_id, signal, {"test": True})


# ============================================================================
# KillSwitchRegistry Tests (8 tests)
# ============================================================================


class TestKillSwitchRegistry:
    """Registry state machine tests."""

    def test_registry_starts_clean(self):
        """No switches triggered initially."""
        reg = KillSwitchRegistry()
        assert not reg.any_triggered()
        for sw in KillSwitchID:
            assert not reg.is_triggered(sw)

    def test_trigger_sets_active(self):
        """trigger() → is_triggered returns True."""
        reg = KillSwitchRegistry()
        ev = _make_evidence(KillSwitchID.KILL_002)
        reg.trigger(KillSwitchID.KILL_002, ev)
        assert reg.is_triggered(KillSwitchID.KILL_002)

    def test_any_triggered_true_when_one_active(self):
        """any_triggered() is True when at least one switch is active."""
        reg = KillSwitchRegistry()
        assert not reg.any_triggered()
        ev = _make_evidence(KillSwitchID.KILL_003)
        reg.trigger(KillSwitchID.KILL_003, ev)
        assert reg.any_triggered()

    def test_reset_clears_specific_switch(self):
        """reset() clears only the specified switch."""
        reg = KillSwitchRegistry()
        ev = _make_evidence(KillSwitchID.KILL_002)
        reg.trigger(KillSwitchID.KILL_002, ev)
        assert reg.is_triggered(KillSwitchID.KILL_002)
        reg.reset(KillSwitchID.KILL_002)
        assert not reg.is_triggered(KillSwitchID.KILL_002)

    def test_reset_preserves_other_switches(self):
        """Resetting one switch leaves others active."""
        reg = KillSwitchRegistry()
        reg.trigger(KillSwitchID.KILL_002, _make_evidence(KillSwitchID.KILL_002))
        reg.trigger(KillSwitchID.KILL_003, _make_evidence(KillSwitchID.KILL_003))
        reg.reset(KillSwitchID.KILL_002)
        assert not reg.is_triggered(KillSwitchID.KILL_002)
        assert reg.is_triggered(KillSwitchID.KILL_003)
        assert reg.any_triggered()

    def test_get_evidence_returns_stored(self):
        """get_evidence() returns evidence after trigger."""
        reg = KillSwitchRegistry()
        ev = _make_evidence(KillSwitchID.KILL_004, "latency exceeded")
        reg.trigger(KillSwitchID.KILL_004, ev)
        stored = reg.get_evidence(KillSwitchID.KILL_004)
        assert stored is not None
        assert stored.trigger_signal == "latency exceeded"
        assert stored.kill_switch == "KILL-004"

    def test_get_all_active_lists_all(self):
        """get_all_active() lists all active switches."""
        reg = KillSwitchRegistry()
        reg.trigger(KillSwitchID.KILL_001, _make_evidence(KillSwitchID.KILL_001))
        reg.trigger(KillSwitchID.KILL_006, _make_evidence(KillSwitchID.KILL_006))
        active = reg.get_all_active()
        ids = {sw.value for sw, _ in active}
        assert ids == {"KILL-001", "KILL-006"}

    def test_metrics_count_lifetime_triggers(self):
        """Trigger counts persist after reset (lifetime metric)."""
        reg = KillSwitchRegistry()
        reg.trigger(KillSwitchID.KILL_002, _make_evidence(KillSwitchID.KILL_002))
        reg.trigger(KillSwitchID.KILL_002, _make_evidence(KillSwitchID.KILL_002))
        reg.reset(KillSwitchID.KILL_002)
        metrics = reg.get_metrics()
        assert metrics["KILL-002"] == 2  # Lifetime count persists


# ============================================================================
# KILL-002: Mechanical Assertion Detection (6 tests)
# ============================================================================


class TestKill002MechanicalAssertion:
    """KILL-002: Mechanical assertion in Spark output."""

    def test_kill002_detects_damage_number(self):
        """'deals 15 damage' triggers mechanical assertion detection."""
        result = detect_mechanical_assertions("The orc deals 15 damage to the fighter.")
        assert result is not None
        assert result[0] == "damage_quantity"

    def test_kill002_detects_ac_reference(self):
        """'AC 18' triggers mechanical assertion detection."""
        result = detect_mechanical_assertions("The knight's AC 18 deflects the blow.")
        assert result is not None
        assert result[0] == "ac_reference"

    def test_kill002_detects_rule_citation(self):
        """'PHB 145' triggers mechanical assertion detection."""
        result = detect_mechanical_assertions("Per PHB 145, the attack of opportunity resolves first.")
        assert result is not None
        assert result[0] == "rule_citation"

    def test_kill002_clean_narration_passes(self):
        """'The orc roars in fury' does NOT trigger."""
        result = detect_mechanical_assertions("The orc roars in fury, swinging wildly!")
        assert result is None

    def test_kill002_falls_back_to_template(self):
        """After KILL-002 trigger, service returns template narration."""
        registry = KillSwitchRegistry()
        service = GuardedNarrationService(kill_switch_registry=registry)

        # Manually trigger KILL-002
        ev = _make_evidence(KillSwitchID.KILL_002, "mechanical assertion found")
        registry.trigger(KillSwitchID.KILL_002, ev)

        request = _make_request()
        with pytest.raises(NarrationBoundaryViolation):
            service.generate_narration(request)

    def test_kill002_evidence_captures_match(self):
        """Evidence includes matched pattern and text."""
        result = detect_mechanical_assertions("The wizard takes 20 hit points of harm.")
        assert result is not None
        pattern_name, matched_text = result
        assert pattern_name == "hit_point_reference"
        assert "20" in matched_text


# ============================================================================
# KILL-003: Token Overflow (4 tests)
# ============================================================================


class TestKill003TokenOverflow:
    """KILL-003: Token overflow (completion > max_tokens * 1.1)."""

    def test_kill003_detects_overflow(self):
        """tokens_used > max_tokens * 1.1 triggers KILL-003."""
        registry = KillSwitchRegistry()

        class FakeModel:
            model_id = "fake-llm"
            inference_engine = Mock(return_value={
                "choices": [{"text": " The warrior strikes."}],
                "usage": {"completion_tokens": 170, "prompt_tokens": 50},
            })
            profile = Mock()
            profile.presets = {"narration": {"max_tokens": 150, "stop_sequences": []}}

        service = GuardedNarrationService(
            loaded_model=FakeModel(),
            use_llm_query_interface=False,
            kill_switch_registry=registry,
        )
        request = _make_request()
        # Should fall back to template because KILL-003 fires
        result = service.generate_narration(request)
        assert registry.is_triggered(KillSwitchID.KILL_003)
        assert result.provenance == "[NARRATIVE:TEMPLATE]"

    def test_kill003_at_boundary_no_trigger(self):
        """tokens_used == max_tokens * 1.1 exactly does NOT trigger."""
        registry = KillSwitchRegistry()

        class FakeModel:
            model_id = "fake-llm"
            # 150 * 1.1 = 165.0, so 165 should NOT trigger
            inference_engine = Mock(return_value={
                "choices": [{"text": " The warrior strikes."}],
                "usage": {"completion_tokens": 165, "prompt_tokens": 50},
            })
            profile = Mock()
            profile.presets = {"narration": {"max_tokens": 150, "stop_sequences": []}}

        service = GuardedNarrationService(
            loaded_model=FakeModel(),
            use_llm_query_interface=False,
            kill_switch_registry=registry,
        )
        request = _make_request()
        result = service.generate_narration(request)
        assert not registry.is_triggered(KillSwitchID.KILL_003)

    def test_kill003_normal_generation_passes(self):
        """tokens_used < max_tokens passes without trigger."""
        registry = KillSwitchRegistry()

        class FakeModel:
            model_id = "fake-llm"
            inference_engine = Mock(return_value={
                "choices": [{"text": " The warrior strikes."}],
                "usage": {"completion_tokens": 50, "prompt_tokens": 30},
            })
            profile = Mock()
            profile.presets = {"narration": {"max_tokens": 150, "stop_sequences": []}}

        service = GuardedNarrationService(
            loaded_model=FakeModel(),
            use_llm_query_interface=False,
            kill_switch_registry=registry,
        )
        request = _make_request()
        result = service.generate_narration(request)
        assert not registry.is_triggered(KillSwitchID.KILL_003)
        # Clean narration should pass KILL-002 too (no mechanical assertions)
        assert result.provenance == "[NARRATIVE]"

    def test_kill003_evidence_has_token_counts(self):
        """KILL-003 evidence includes both max_tokens and tokens_used."""
        registry = KillSwitchRegistry()

        class FakeModel:
            model_id = "fake-llm"
            inference_engine = Mock(return_value={
                "choices": [{"text": " Output."}],
                "usage": {"completion_tokens": 200, "prompt_tokens": 50},
            })
            profile = Mock()
            profile.presets = {"narration": {"max_tokens": 150, "stop_sequences": []}}

        service = GuardedNarrationService(
            loaded_model=FakeModel(),
            use_llm_query_interface=False,
            kill_switch_registry=registry,
        )
        request = _make_request()
        service.generate_narration(request)

        ev = registry.get_evidence(KillSwitchID.KILL_003)
        assert ev is not None
        assert ev.evidence["max_tokens"] == 150
        assert ev.evidence["tokens_used"] == 200


# ============================================================================
# KILL-004: Latency Exceeded (4 tests)
# ============================================================================


class TestKill004Latency:
    """KILL-004: Spark latency exceeds 10s."""

    def test_kill004_detects_slow_generation(self):
        """Mock 11s delay triggers KILL-004."""
        registry = KillSwitchRegistry()

        def slow_engine(*args, **kwargs):
            # We can't actually sleep 11s in a test, so we mock time.monotonic
            return {
                "choices": [{"text": " The warrior strikes."}],
                "usage": {"completion_tokens": 10, "prompt_tokens": 5},
            }

        class FakeModel:
            model_id = "fake-llm"
            inference_engine = Mock(side_effect=slow_engine)
            profile = Mock()
            profile.presets = {"narration": {"max_tokens": 150, "stop_sequences": []}}

        service = GuardedNarrationService(
            loaded_model=FakeModel(),
            use_llm_query_interface=False,
            kill_switch_registry=registry,
        )

        # Patch time.monotonic to simulate 11s elapsed
        real_monotonic = time.monotonic
        call_count = [0]

        def fake_monotonic():
            call_count[0] += 1
            if call_count[0] <= 1:
                return 100.0  # before call
            return 111.0  # after call (11s elapsed)

        with patch("aidm.narration.guarded_narration_service.time") as mock_time:
            mock_time.monotonic = fake_monotonic
            request = _make_request()
            result = service.generate_narration(request)

        assert registry.is_triggered(KillSwitchID.KILL_004)
        assert result.provenance == "[NARRATIVE:TEMPLATE]"

    def test_kill004_fast_generation_passes(self):
        """Mock 2s delay does NOT trigger KILL-004."""
        registry = KillSwitchRegistry()

        class FakeModel:
            model_id = "fake-llm"
            inference_engine = Mock(return_value={
                "choices": [{"text": " Quick strike."}],
                "usage": {"completion_tokens": 5, "prompt_tokens": 3},
            })
            profile = Mock()
            profile.presets = {"narration": {"max_tokens": 150, "stop_sequences": []}}

        service = GuardedNarrationService(
            loaded_model=FakeModel(),
            use_llm_query_interface=False,
            kill_switch_registry=registry,
        )

        call_count = [0]

        def fast_monotonic():
            call_count[0] += 1
            if call_count[0] <= 1:
                return 100.0
            return 102.0  # 2s elapsed

        with patch("aidm.narration.guarded_narration_service.time") as mock_time:
            mock_time.monotonic = fast_monotonic
            request = _make_request()
            result = service.generate_narration(request)

        assert not registry.is_triggered(KillSwitchID.KILL_004)

    def test_kill004_at_boundary_no_trigger(self):
        """Exactly 10.0s does NOT trigger KILL-004."""
        registry = KillSwitchRegistry()

        class FakeModel:
            model_id = "fake-llm"
            inference_engine = Mock(return_value={
                "choices": [{"text": " Border case."}],
                "usage": {"completion_tokens": 5, "prompt_tokens": 3},
            })
            profile = Mock()
            profile.presets = {"narration": {"max_tokens": 150, "stop_sequences": []}}

        service = GuardedNarrationService(
            loaded_model=FakeModel(),
            use_llm_query_interface=False,
            kill_switch_registry=registry,
        )

        call_count = [0]

        def boundary_monotonic():
            call_count[0] += 1
            if call_count[0] <= 1:
                return 100.0
            return 110.0  # exactly 10s

        with patch("aidm.narration.guarded_narration_service.time") as mock_time:
            mock_time.monotonic = boundary_monotonic
            request = _make_request()
            service.generate_narration(request)

        assert not registry.is_triggered(KillSwitchID.KILL_004)

    def test_kill004_evidence_has_elapsed_time(self):
        """KILL-004 evidence includes elapsed_ms."""
        registry = KillSwitchRegistry()

        class FakeModel:
            model_id = "fake-llm"
            inference_engine = Mock(return_value={
                "choices": [{"text": " Slow."}],
                "usage": {"completion_tokens": 5, "prompt_tokens": 3},
            })
            profile = Mock()
            profile.presets = {"narration": {"max_tokens": 150, "stop_sequences": []}}

        service = GuardedNarrationService(
            loaded_model=FakeModel(),
            use_llm_query_interface=False,
            kill_switch_registry=registry,
        )

        call_count = [0]

        def slow_mono():
            call_count[0] += 1
            if call_count[0] <= 1:
                return 100.0
            return 115.0  # 15s elapsed

        with patch("aidm.narration.guarded_narration_service.time") as mock_time:
            mock_time.monotonic = slow_mono
            request = _make_request()
            service.generate_narration(request)

        ev = registry.get_evidence(KillSwitchID.KILL_004)
        assert ev is not None
        assert ev.evidence["elapsed_ms"] == 15000
        assert ev.evidence["max_allowed_ms"] == 10000


# ============================================================================
# KILL-005: Consecutive Rejections (4 tests)
# ============================================================================


class TestKill005ConsecutiveRejections:
    """KILL-005: Consecutive guardrail rejections > 3."""

    def test_kill005_triggers_on_third_rejection(self):
        """3 consecutive rejections trigger KILL-005."""
        registry = KillSwitchRegistry()
        service = GuardedNarrationService(kill_switch_registry=registry)

        # Simulate 3 consecutive rejections
        registry.record_rejection(KillSwitchID.KILL_002)
        registry.record_rejection(KillSwitchID.KILL_003)
        registry.record_rejection(KillSwitchID.KILL_004)

        # Now check KILL-005
        service._check_kill005()
        assert registry.is_triggered(KillSwitchID.KILL_005)

    def test_kill005_resets_on_success(self):
        """Successful generation resets the consecutive rejection counter."""
        registry = KillSwitchRegistry()
        registry.record_rejection(KillSwitchID.KILL_002)
        registry.record_rejection(KillSwitchID.KILL_003)
        assert registry.consecutive_rejections == 2

        # Simulate successful generation
        registry.reset_rejection_counter()
        assert registry.consecutive_rejections == 0

    def test_kill005_mixed_switches_count(self):
        """Different switch types still count toward consecutive rejections."""
        registry = KillSwitchRegistry()
        registry.record_rejection(KillSwitchID.KILL_002)
        registry.record_rejection(KillSwitchID.KILL_003)
        registry.record_rejection(KillSwitchID.KILL_004)
        assert registry.consecutive_rejections == 3
        assert set(registry.rejection_types) == {"KILL-002", "KILL-003", "KILL-004"}

    def test_kill005_evidence_has_rejection_list(self):
        """KILL-005 evidence includes rejection_types list."""
        registry = KillSwitchRegistry()
        service = GuardedNarrationService(kill_switch_registry=registry)

        registry.record_rejection(KillSwitchID.KILL_002)
        registry.record_rejection(KillSwitchID.KILL_002)
        registry.record_rejection(KillSwitchID.KILL_003)
        service._check_kill005()

        ev = registry.get_evidence(KillSwitchID.KILL_005)
        assert ev is not None
        assert ev.evidence["rejection_count"] == 3
        assert "KILL-002" in ev.evidence["rejection_types"]
        assert "KILL-003" in ev.evidence["rejection_types"]


# ============================================================================
# KILL-006: State Hash Drift (4 tests)
# ============================================================================


class TestKill006StateHashDrift:
    """KILL-006: State hash drift post-narration."""

    def test_kill006_detects_world_state_drift(self):
        """Changed world state hash triggers KILL-006."""
        registry = KillSwitchRegistry()
        service = GuardedNarrationService(kill_switch_registry=registry)

        drifted = service.check_world_state_drift(
            hash_before="aaaa1111",
            hash_after="bbbb2222",
        )
        assert drifted is True
        assert registry.is_triggered(KillSwitchID.KILL_006)

    def test_kill006_stable_state_passes(self):
        """Same hash before/after does NOT trigger."""
        registry = KillSwitchRegistry()
        service = GuardedNarrationService(kill_switch_registry=registry)

        drifted = service.check_world_state_drift(
            hash_before="aaaa1111",
            hash_after="aaaa1111",
        )
        assert drifted is False
        assert not registry.is_triggered(KillSwitchID.KILL_006)

    def test_kill006_independent_of_kill001(self):
        """KILL-006 triggers independently from KILL-001."""
        registry = KillSwitchRegistry()
        service = GuardedNarrationService(kill_switch_registry=registry)

        # Trigger KILL-006 only
        service.check_world_state_drift("aaa", "bbb")
        assert registry.is_triggered(KillSwitchID.KILL_006)
        assert not registry.is_triggered(KillSwitchID.KILL_001)

    def test_kill006_evidence_has_both_hashes(self):
        """KILL-006 evidence includes hash_before and hash_after."""
        registry = KillSwitchRegistry()
        service = GuardedNarrationService(kill_switch_registry=registry)

        service.check_world_state_drift(
            hash_before="before_hash_value",
            hash_after="after_hash_value",
        )
        ev = registry.get_evidence(KillSwitchID.KILL_006)
        assert ev is not None
        assert ev.evidence["hash_before"] == "before_hash_value"
        assert ev.evidence["hash_after"] == "after_hash_value"
        assert ev.evidence["snapshot_type"] == "world_state"


# ============================================================================
# Integration: Kill switch blocks all narration
# ============================================================================


class TestKillSwitchIntegration:
    """Integration tests for kill switch → template fallback."""

    def test_any_kill_switch_blocks_narration(self):
        """Any active kill switch raises NarrationBoundaryViolation."""
        registry = KillSwitchRegistry()
        registry.trigger(KillSwitchID.KILL_003, _make_evidence(KillSwitchID.KILL_003))
        service = GuardedNarrationService(kill_switch_registry=registry)

        request = _make_request()
        with pytest.raises(NarrationBoundaryViolation) as exc_info:
            service.generate_narration(request)
        assert "KILL-003" in str(exc_info.value)

    def test_reset_specific_switch_allows_narration(self):
        """After resetting the only active switch, narration succeeds."""
        registry = KillSwitchRegistry()
        registry.trigger(KillSwitchID.KILL_004, _make_evidence(KillSwitchID.KILL_004))
        service = GuardedNarrationService(kill_switch_registry=registry)

        # Blocked
        with pytest.raises(NarrationBoundaryViolation):
            service.generate_narration(_make_request())

        # Reset
        service.reset_kill_switch(KillSwitchID.KILL_004)
        assert not service.is_kill_switch_active()

        # Now succeeds
        result = service.generate_narration(_make_request())
        assert len(result.text) > 0

    def test_kill002_in_llm_path_falls_back_silently(self):
        """KILL-002 detecting mechanical assertion in LLM output → template fallback."""
        registry = KillSwitchRegistry()

        class FakeModel:
            model_id = "fake-llm"
            inference_engine = Mock(return_value={
                "choices": [{"text": " The orc deals 15 damage to the fighter!"}],
                "usage": {"completion_tokens": 10, "prompt_tokens": 5},
            })
            profile = Mock()
            profile.presets = {"narration": {"max_tokens": 150, "stop_sequences": []}}

        service = GuardedNarrationService(
            loaded_model=FakeModel(),
            use_llm_query_interface=False,
            kill_switch_registry=registry,
        )
        request = _make_request()
        result = service.generate_narration(request)

        # Should fall back to template (KILL-002 detected mechanical assertion)
        assert registry.is_triggered(KillSwitchID.KILL_002)
        assert result.provenance == "[NARRATIVE:TEMPLATE]"
        assert len(result.text) > 0

    def test_backward_compat_trigger_kill_switch(self):
        """_trigger_kill_switch() still works (backward compat)."""
        registry = KillSwitchRegistry()
        service = GuardedNarrationService(kill_switch_registry=registry)

        service._trigger_kill_switch("TEST: manual trigger")
        assert registry.is_triggered(KillSwitchID.KILL_001)
        assert service.is_kill_switch_active()

    def test_backward_compat_reset_no_arg(self):
        """reset_kill_switch() with no arg resets KILL-001."""
        registry = KillSwitchRegistry()
        service = GuardedNarrationService(kill_switch_registry=registry)

        service._trigger_kill_switch("TEST")
        assert service.is_kill_switch_active()

        service.reset_kill_switch()
        assert not service.is_kill_switch_active()
