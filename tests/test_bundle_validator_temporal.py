"""Tests for temporal bundle validation."""

import pytest
from aidm.schemas.bundles import SessionBundle, SceneCard
from aidm.schemas.time import GameClock
from aidm.schemas.timers import Deadline
from aidm.schemas.durations import EffectDuration
from aidm.schemas.visibility import AmbientLightSchedule
from aidm.core.bundle_validator import validate_session_bundle


def test_bundle_with_initial_clock_passes():
    """Bundle validation should accept valid initial_clock."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        initial_clock=GameClock(t_seconds=0, scale="narrative")
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_without_initial_clock_passes():
    """Bundle validation should accept bundles without initial_clock."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z"
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_deadline_before_clock_blocks():
    """Bundle validation should block if deadline due time is before clock time."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        initial_clock=GameClock(t_seconds=1000, scale="narrative"),
        deadlines=[
            Deadline(
                id="test",
                name="Test Deadline",
                due_at_t_seconds=500,  # Before clock time
                failure_consequence="Bad",
                visibility="explicit"
            )
        ]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "blocked"
    assert any("before initial_clock time" in note for note in cert.notes)


def test_bundle_deadline_after_clock_passes():
    """Bundle validation should accept deadline after clock time."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        initial_clock=GameClock(t_seconds=1000, scale="narrative"),
        deadlines=[
            Deadline(
                id="test",
                name="Test Deadline",
                due_at_t_seconds=2000,  # After clock time
                failure_consequence="Bad",
                visibility="explicit"
            )
        ]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_deadline_at_exact_clock_time_passes():
    """Bundle validation should accept deadline at exact clock time."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        initial_clock=GameClock(t_seconds=1000, scale="narrative"),
        deadlines=[
            Deadline(
                id="test",
                name="Test Deadline",
                due_at_t_seconds=1000,  # Exact clock time
                failure_consequence="Bad",
                visibility="explicit"
            )
        ]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_effect_start_after_clock_blocks():
    """Bundle validation should block if effect starts after clock time."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        initial_clock=GameClock(t_seconds=1000, scale="combat_round"),
        active_effects=[
            EffectDuration(
                unit="rounds",
                value=10,
                start_t_seconds=1500  # After clock time
            )
        ]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "blocked"
    assert any("after initial_clock time" in note for note in cert.notes)


def test_bundle_effect_start_before_clock_passes():
    """Bundle validation should accept effect that started before clock time."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        initial_clock=GameClock(t_seconds=1000, scale="combat_round"),
        active_effects=[
            EffectDuration(
                unit="rounds",
                value=10,
                start_t_seconds=500  # Before clock time (ongoing effect)
            )
        ]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_effect_end_before_start_blocks():
    """EffectDuration schema should reject end time before start time."""
    # This validation happens at schema construction, not bundle validation
    with pytest.raises(ValueError, match="ends_at_t_seconds.*must be >=.*start_t_seconds"):
        EffectDuration(
            unit="rounds",
            value=10,
            start_t_seconds=1000,
            ends_at_t_seconds=500  # Before start
        )


def test_bundle_multiple_effects_validates_all():
    """Bundle validation should check all active effects."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        initial_clock=GameClock(t_seconds=1000, scale="combat_round"),
        active_effects=[
            EffectDuration(
                unit="rounds",
                value=10,
                start_t_seconds=500  # OK
            ),
            EffectDuration(
                unit="minutes",
                value=5,
                start_t_seconds=2000  # After clock - should block
            )
        ]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "blocked"
    assert any("Effect 1" in note and "after initial_clock time" in note for note in cert.notes)


def test_bundle_scene_with_light_schedule_passes():
    """Bundle validation should accept scene with valid light schedule."""
    scene = SceneCard(
        scene_id="scene_1",
        title="Test Scene",
        description="Test",
        ambient_light_schedule=AmbientLightSchedule(entries=[
            (0, "bright"),
            (1000, "dim"),
            (2000, "dark")
        ])
    )

    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        scene_cards=[scene]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_without_temporal_fields_passes():
    """Bundle validation should pass for bundles without any temporal fields."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z"
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_deadlines_without_clock_passes():
    """Bundle validation should accept deadlines without initial_clock (no time validation)."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        deadlines=[
            Deadline(
                id="test",
                name="Test Deadline",
                due_at_t_seconds=1000,
                failure_consequence="Bad",
                visibility="explicit"
            )
        ]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_effects_without_clock_passes():
    """Bundle validation should accept effects without initial_clock."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        active_effects=[
            EffectDuration(
                unit="rounds",
                value=10,
                start_t_seconds=0
            )
        ]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "ready"


def test_bundle_multiple_deadlines_all_validated():
    """Bundle validation should validate all deadlines."""
    bundle = SessionBundle(
        id="session_001",
        campaign_id="campaign_alpha",
        session_number=1,
        created_at="2025-01-15T10:00:00Z",
        initial_clock=GameClock(t_seconds=1000, scale="narrative"),
        deadlines=[
            Deadline(
                id="deadline_1",
                name="Good Deadline",
                due_at_t_seconds=2000,  # OK
                failure_consequence="Bad",
                visibility="explicit"
            ),
            Deadline(
                id="deadline_2",
                name="Bad Deadline",
                due_at_t_seconds=500,  # Before clock - should block
                failure_consequence="Bad",
                visibility="explicit"
            )
        ]
    )

    cert = validate_session_bundle(bundle)
    assert cert.status == "blocked"
    assert any("deadline_2" in note for note in cert.notes)
