"""Tests for Emotion Register Router — mood-to-clip deterministic mapping.

Tests:
1. mood_to_register mapping (7 tests)
2. Clip path resolution with fallbacks (6 tests)
3. Clip listing and coverage (4 tests)
4. Integration with Chatterbox adapter (3 tests)

Total: 20 tests (all unit tests, no GPU required)
"""

import io
import os
import wave

import pytest

from aidm.immersion.emotion_router import (
    EMOTION_REGISTERS,
    PHASE1_PERSONAS,
    mood_to_register,
    resolve_emotion_clip,
    list_available_clips,
    get_clip_coverage,
    _clip_filename,
)
from aidm.schemas.immersion import VoicePersona


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def voices_dir(tmp_path):
    """Create a temp voices directory with Phase 1 register clips."""
    for persona in PHASE1_PERSONAS:
        for register in EMOTION_REGISTERS:
            wav_path = tmp_path / f"{persona}__{register}__v1.wav"
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(b"\x00\x00" * 2400)  # 0.1s silence
            wav_path.write_bytes(buf.getvalue())

        # Also create a legacy clip for backward compat testing
        legacy = tmp_path / f"{persona}.wav"
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(b"\x00\x00" * 2400)
        legacy.write_bytes(buf.getvalue())

    return str(tmp_path)


@pytest.fixture
def partial_voices_dir(tmp_path):
    """Create a voices dir with only neutral clips (no tense/angry/grief)."""
    for persona in PHASE1_PERSONAS:
        wav_path = tmp_path / f"{persona}__neutral__v1.wav"
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(b"\x00\x00" * 2400)
        wav_path.write_bytes(buf.getvalue())
    return str(tmp_path)


# ==============================================================================
# TESTS: Mood-to-Register Mapping
# ==============================================================================

class TestMoodToRegister:
    """Test deterministic mood → register mapping."""

    def test_neutral_mood_gives_neutral(self):
        assert mood_to_register("neutral") == "neutral"

    def test_peaceful_mood_gives_neutral(self):
        assert mood_to_register("peaceful") == "neutral"

    def test_tense_mood_gives_tense(self):
        assert mood_to_register("tense") == "tense"

    def test_combat_mood_gives_angry(self):
        assert mood_to_register("combat") == "angry"

    def test_dramatic_mood_gives_grief(self):
        assert mood_to_register("dramatic") == "grief"

    def test_dramatic_with_triumph_tag_gives_neutral(self):
        assert mood_to_register("dramatic", scene_tag="triumph") == "neutral"

    def test_unknown_mood_falls_back_to_neutral(self):
        assert mood_to_register("xyzzy") == "neutral"


# ==============================================================================
# TESTS: Clip Path Resolution
# ==============================================================================

class TestResolveEmotionClip:
    """Test clip path resolution with fallback chain."""

    def test_resolves_register_specific_clip(self, voices_dir):
        path = resolve_emotion_clip("dm_narrator", "combat", voices_dir)
        assert path is not None
        assert "dm_narrator__angry__v1.wav" in path

    def test_resolves_neutral_for_peaceful(self, voices_dir):
        path = resolve_emotion_clip("npc_female", "peaceful", voices_dir)
        assert path is not None
        assert "npc_female__neutral__v1.wav" in path

    def test_falls_back_to_neutral_when_register_missing(self, partial_voices_dir):
        """When angry clip doesn't exist, falls back to neutral."""
        path = resolve_emotion_clip("dm_narrator", "combat", partial_voices_dir)
        assert path is not None
        assert "dm_narrator__neutral__v1.wav" in path

    def test_falls_back_to_legacy_clip(self, voices_dir):
        """Persona not in Phase 1 still gets legacy clip."""
        # heroic is not in PHASE1_PERSONAS, but voices_dir doesn't have it
        # Create a legacy clip for a non-Phase1 persona
        legacy = os.path.join(voices_dir, "heroic.wav")
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(b"\x00\x00" * 2400)
        with open(legacy, "wb") as f:
            f.write(buf.getvalue())

        path = resolve_emotion_clip("heroic", "combat", voices_dir)
        assert path is not None
        assert "heroic.wav" in path

    def test_returns_none_for_missing_persona(self, voices_dir):
        path = resolve_emotion_clip("nonexistent_persona", "neutral", voices_dir)
        assert path is None

    def test_returns_none_for_invalid_dir(self):
        path = resolve_emotion_clip("dm_narrator", "neutral", "/no/such/dir")
        assert path is None


# ==============================================================================
# TESTS: Clip Listing and Coverage
# ==============================================================================

class TestClipInventory:
    """Test clip listing and coverage reporting."""

    def test_list_all_clips(self, voices_dir):
        clips = list_available_clips(voices_dir)
        assert len(clips) == 16  # 4 personas × 4 registers

    def test_list_clips_filtered_by_persona(self, voices_dir):
        clips = list_available_clips(voices_dir, persona_id="dm_narrator")
        assert len(clips) == 4
        assert all("dm_narrator__" in c for c in clips)

    def test_coverage_report(self, voices_dir):
        coverage = get_clip_coverage(voices_dir)
        assert len(coverage) == 4  # 4 Phase 1 personas
        for persona_id, registers in coverage.items():
            assert set(registers) == set(EMOTION_REGISTERS)

    def test_partial_coverage(self, partial_voices_dir):
        coverage = get_clip_coverage(partial_voices_dir)
        for persona_id, registers in coverage.items():
            assert registers == ["neutral"]


# ==============================================================================
# TESTS: Integration with Chatterbox Adapter
# ==============================================================================

class TestChatterboxIntegration:
    """Test that the router integrates with ChatterboxTTSAdapter."""

    def test_adapter_accepts_mood_param(self, voices_dir):
        from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
        adapter = ChatterboxTTSAdapter(voices_dir=voices_dir)
        persona = VoicePersona(
            persona_id="dm_narrator", name="DM", voice_model="chatterbox",
        )
        # Should resolve to the angry register clip
        path = adapter._resolve_reference_audio(persona, mood="combat")
        assert path is not None
        assert "dm_narrator__angry__v1.wav" in path

    def test_adapter_mood_none_uses_legacy_fallback(self, voices_dir):
        from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
        adapter = ChatterboxTTSAdapter(voices_dir=voices_dir)
        persona = VoicePersona(
            persona_id="dm_narrator", name="DM", voice_model="chatterbox",
        )
        # No mood → legacy resolution (persona_id lookup in voices_dir)
        path = adapter._resolve_reference_audio(persona, mood=None)
        assert path is not None
        assert "dm_narrator.wav" in path

    def test_adapter_dramatic_triumph_override(self, voices_dir):
        from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
        adapter = ChatterboxTTSAdapter(voices_dir=voices_dir)
        persona = VoicePersona(
            persona_id="villainous", name="Villain", voice_model="chatterbox",
        )
        # dramatic + triumph → neutral instead of grief
        path = adapter._resolve_reference_audio(
            persona, mood="dramatic", scene_tag="triumph",
        )
        assert path is not None
        assert "villainous__neutral__v1.wav" in path
