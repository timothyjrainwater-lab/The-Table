"""Tests for M3 Audio Mixer — Scene audio state computation.

Tests:
- Mood computation from world state (combat, hazards, dark, peaceful)
- Transition detection (mood changes tracked)
- Default tracks generated per mood
- StubAudioMixerAdapter records history
- Deterministic output (same inputs → same output)
"""

import pytest

from aidm.core.state import WorldState
from aidm.immersion.audio_mixer import (
    AudioMixerAdapter,
    StubAudioMixerAdapter,
    compute_scene_audio_state,
)
from aidm.schemas.immersion import SceneAudioState


# =============================================================================
# Mood Computation Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestMoodComputation:
    """Tests for compute_scene_audio_state mood rules."""

    def test_combat_active_mood(self):
        """Active combat should produce mood='combat'."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1},
        )
        result = compute_scene_audio_state(ws)
        assert result.mood == "combat"

    def test_environmental_hazards_mood(self):
        """Environmental hazards should produce mood='tense'."""
        ws = WorldState(ruleset_version="RAW_3.5")
        scene = {"environmental_hazards": [{"type": "lava"}]}
        result = compute_scene_audio_state(ws, scene_card=scene)
        assert result.mood == "tense"

    def test_dark_ambient_mood(self):
        """Dark ambient light should produce mood='tense'."""
        ws = WorldState(ruleset_version="RAW_3.5")
        scene = {"ambient_light_level": "dark"}
        result = compute_scene_audio_state(ws, scene_card=scene)
        assert result.mood == "tense"

    def test_peaceful_default_mood(self):
        """No combat, no hazards, not dark → mood='peaceful'."""
        ws = WorldState(ruleset_version="RAW_3.5")
        result = compute_scene_audio_state(ws)
        assert result.mood == "peaceful"

    def test_bright_light_peaceful(self):
        """Bright ambient light without hazards → peaceful."""
        ws = WorldState(ruleset_version="RAW_3.5")
        scene = {"ambient_light_level": "bright"}
        result = compute_scene_audio_state(ws, scene_card=scene)
        assert result.mood == "peaceful"

    def test_dim_light_peaceful(self):
        """Dim ambient light without hazards → peaceful (not tense)."""
        ws = WorldState(ruleset_version="RAW_3.5")
        scene = {"ambient_light_level": "dim"}
        result = compute_scene_audio_state(ws, scene_card=scene)
        assert result.mood == "peaceful"

    def test_combat_overrides_hazards(self):
        """Combat should override hazards (combat > tense)."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1},
        )
        scene = {"environmental_hazards": [{"type": "pit"}]}
        result = compute_scene_audio_state(ws, scene_card=scene)
        assert result.mood == "combat"

    def test_combat_overrides_darkness(self):
        """Combat should override darkness."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 2},
        )
        scene = {"ambient_light_level": "dark"}
        result = compute_scene_audio_state(ws, scene_card=scene)
        assert result.mood == "combat"

    def test_empty_hazards_not_tense(self):
        """Empty hazards list should not trigger tense mood."""
        ws = WorldState(ruleset_version="RAW_3.5")
        scene = {"environmental_hazards": []}
        result = compute_scene_audio_state(ws, scene_card=scene)
        assert result.mood == "peaceful"


# =============================================================================
# Transition Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestTransitions:
    """Tests for mood transition detection."""

    def test_peaceful_to_combat_transition(self):
        """Should record transition when mood changes."""
        ws_peaceful = WorldState(ruleset_version="RAW_3.5")
        prev = compute_scene_audio_state(ws_peaceful)
        assert prev.mood == "peaceful"

        ws_combat = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1},
        )
        result = compute_scene_audio_state(ws_combat, previous=prev)
        assert result.mood == "combat"
        assert "peaceful -> combat" in result.transition_reason

    def test_combat_to_peaceful_transition(self):
        """Should record transition when combat ends."""
        prev = SceneAudioState(mood="combat")
        ws = WorldState(ruleset_version="RAW_3.5")
        result = compute_scene_audio_state(ws, previous=prev)
        assert result.mood == "peaceful"
        assert "combat -> peaceful" in result.transition_reason

    def test_no_transition_same_mood(self):
        """Should have empty transition_reason when mood unchanged."""
        prev = SceneAudioState(mood="peaceful")
        ws = WorldState(ruleset_version="RAW_3.5")
        result = compute_scene_audio_state(ws, previous=prev)
        assert result.mood == "peaceful"
        assert result.transition_reason == ""

    def test_first_state_has_reason(self):
        """First state (no previous) should have initial reason."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1},
        )
        result = compute_scene_audio_state(ws)
        assert result.transition_reason != ""


# =============================================================================
# Track Generation Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestTrackGeneration:
    """Tests for default track generation."""

    def test_combat_has_combat_track(self):
        """Combat mood should have combat track."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 1},
        )
        result = compute_scene_audio_state(ws)
        assert len(result.active_tracks) > 0
        assert result.active_tracks[0].kind == "combat"

    def test_peaceful_has_ambient_track(self):
        """Peaceful mood should have ambient track."""
        ws = WorldState(ruleset_version="RAW_3.5")
        result = compute_scene_audio_state(ws)
        assert len(result.active_tracks) > 0
        assert result.active_tracks[0].kind == "ambient"

    def test_tense_has_ambient_track(self):
        """Tense mood should have ambient track."""
        ws = WorldState(ruleset_version="RAW_3.5")
        scene = {"ambient_light_level": "dark"}
        result = compute_scene_audio_state(ws, scene_card=scene)
        assert len(result.active_tracks) > 0
        assert result.active_tracks[0].kind == "ambient"


# =============================================================================
# Determinism Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestDeterminism:
    """Tests for deterministic output."""

    def test_deterministic_10x(self):
        """Same inputs should produce identical output 10 times."""
        ws = WorldState(
            ruleset_version="RAW_3.5",
            active_combat={"round": 3},
        )
        scene = {"ambient_light_level": "dim"}

        results = [
            compute_scene_audio_state(ws, scene_card=scene)
            for _ in range(10)
        ]

        first = results[0].to_dict()
        for r in results[1:]:
            assert r.to_dict() == first


# =============================================================================
# Stub Mixer Adapter Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestStubMixerAdapter:
    """Tests for StubAudioMixerAdapter."""

    def test_records_history(self):
        """Should record applied states in history."""
        mixer = StubAudioMixerAdapter()
        state = SceneAudioState(mood="combat")
        mixer.apply_state(state)
        assert len(mixer.history) == 1
        assert mixer.history[0].mood == "combat"

    def test_stop_all(self):
        """Should record stop event."""
        mixer = StubAudioMixerAdapter()
        mixer.stop_all()
        assert mixer.stopped is True

    def test_is_available(self):
        """Stub should always be available."""
        mixer = StubAudioMixerAdapter()
        assert mixer.is_available() is True

    def test_satisfies_protocol(self):
        """StubAudioMixerAdapter should satisfy AudioMixerAdapter protocol."""
        mixer = StubAudioMixerAdapter()
        assert isinstance(mixer, AudioMixerAdapter)

    def test_validates(self):
        """Computed audio state should pass validation."""
        ws = WorldState(ruleset_version="RAW_3.5")
        result = compute_scene_audio_state(ws)
        assert result.validate() == []
