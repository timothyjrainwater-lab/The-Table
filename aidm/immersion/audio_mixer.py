"""M3 Audio Mixer — Scene audio state computation and mixer adapter.

Provides:
- compute_scene_audio_state(): Pure function computing mood from world state
- AudioMixerAdapter Protocol: apply_state(), stop_all()
- StubAudioMixerAdapter: Records history for testing

Scene audio state is atmospheric only — never mechanical authority.
Deterministic: same inputs always produce same output.

BL-020: Audio mixer is a non-engine boundary consumer — receives read-only
        FrozenWorldStateView instead of mutable WorldState.
"""

from typing import Dict, List, Optional, Protocol, runtime_checkable

from aidm.core.state import FrozenWorldStateView
from aidm.schemas.immersion import AudioTrack, SceneAudioState


def compute_scene_audio_state(
    world_state: FrozenWorldStateView,
    scene_card: Optional[Dict] = None,
    previous: Optional[SceneAudioState] = None,
) -> SceneAudioState:
    """Compute scene audio state from world state.

    Pure function — deterministic, no side effects.

    Mood rules (checked in order):
    1. active_combat is not None → mood="combat"
    2. Environmental hazards present in scene_card → mood="tense"
    3. ambient_light_level == "dark" in scene_card → mood="tense"
    4. Otherwise → mood="peaceful"

    Tracks transition_reason when mood changes from previous state.

    Args:
        world_state: Current world state (read-only view, BL-020)
        scene_card: Optional scene card dict (with ambient_light_level,
                    environmental_hazards, etc.)
        previous: Previous audio state (for transition detection)

    Returns:
        SceneAudioState with computed mood and tracks
    """
    scene_card = scene_card or {}

    # Determine mood
    mood = "peaceful"
    reason = ""

    if world_state.active_combat is not None:
        mood = "combat"
        reason = "combat started"
    elif scene_card.get("environmental_hazards"):
        mood = "tense"
        reason = "environmental hazards present"
    elif scene_card.get("ambient_light_level") == "dark":
        mood = "tense"
        reason = "darkness"
    # FUTURE_HOOK: condition-driven audio cues (M4+)
    #   When conditions system gains duration tracking, entity conditions
    #   could influence mood (e.g., party-wide fear → "dramatic").
    #   Add elif branch here checking entity conditions from scene_card.
    #   Must remain pure — read conditions, never write them.
    # FUTURE_HOOK: concentration/duration moods (M4+)
    #   Spell concentration or effect durations could add a "dramatic"
    #   mood when high-stakes spells are sustained.
    #   Add elif branch here checking active spell effects from scene_card.
    else:
        mood = "peaceful"
        reason = ""

    # Build transition reason
    transition_reason = ""
    if previous is not None and previous.mood != mood:
        transition_reason = f"{previous.mood} -> {mood}: {reason}" if reason else f"{previous.mood} -> {mood}"
    elif previous is None and mood != "neutral":
        transition_reason = reason

    # Build default track list based on mood
    tracks = _default_tracks_for_mood(mood)

    return SceneAudioState(
        active_tracks=tracks,
        mood=mood,
        transition_reason=transition_reason,
    )


def _default_tracks_for_mood(mood: str) -> List[AudioTrack]:
    """Generate default track list for a mood.

    Returns placeholder tracks appropriate for the mood.
    """
    if mood == "combat":
        return [
            AudioTrack(
                track_id="combat_music",
                kind="combat",
                semantic_key="combat:battle:theme",
                volume=0.8,
                loop=True,
            ),
        ]
    elif mood == "tense":
        return [
            AudioTrack(
                track_id="tense_ambient",
                kind="ambient",
                semantic_key="ambient:tense:drone",
                volume=0.5,
                loop=True,
            ),
        ]
    elif mood == "peaceful":
        return [
            AudioTrack(
                track_id="peaceful_ambient",
                kind="ambient",
                semantic_key="ambient:peaceful:nature",
                volume=0.4,
                loop=True,
            ),
        ]
    return []


# ---------------------------------------------------------------------------
# Mixer Adapter
# ---------------------------------------------------------------------------

@runtime_checkable
class AudioMixerAdapter(Protocol):
    """Protocol for audio mixer adapters."""

    def apply_state(self, audio_state: SceneAudioState) -> None:
        """Apply audio state (start/stop tracks, adjust volumes).

        Args:
            audio_state: Target audio state
        """
        ...

    def stop_all(self) -> None:
        """Stop all currently playing audio."""
        ...

    def is_available(self) -> bool:
        """Check if the audio mixer backend is available."""
        ...


class StubAudioMixerAdapter:
    """Stub audio mixer that records state history for testing."""

    def __init__(self):
        self.history: List[SceneAudioState] = []
        self.stopped: bool = False

    def apply_state(self, audio_state: SceneAudioState) -> None:
        """Record audio state in history."""
        self.history.append(audio_state)
        self.stopped = False

    def stop_all(self) -> None:
        """Record stop event."""
        self.stopped = True

    def is_available(self) -> bool:
        """Stub is always available."""
        return True
