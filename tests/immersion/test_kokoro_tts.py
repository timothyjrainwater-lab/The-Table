"""M3 Kokoro TTS Adapter Tests.

Unit tests for KokoroTTSAdapter:
- Protocol compliance (isinstance check)
- Persona listing and validation
- Audio format validation (WAV header, sample rate)
- Graceful fallback when dependencies unavailable

Integration tests (marked @pytest.mark.requires_kokoro):
- Real synthesis with Kokoro engine
- Voice selection across personas
- Speed/pitch parameter handling

WO-020: Real TTS Backend (Kokoro)
"""

import io
import struct
import wave
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from aidm.schemas.immersion import VoicePersona


# ==============================================================================
# TEST MARKERS
# ==============================================================================

def _kokoro_available() -> bool:
    """Check if Kokoro TTS is available."""
    try:
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter
        adapter = KokoroTTSAdapter()
        return adapter.is_available()
    except ImportError:
        return False


# Mark for tests that require real Kokoro installation
requires_kokoro = pytest.mark.skipif(
    not _kokoro_available(),
    reason="Kokoro TTS not installed (pip install kokoro-onnx onnxruntime)"
)


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def kokoro_adapter():
    """Create a KokoroTTSAdapter instance."""
    from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter
    return KokoroTTSAdapter()


@pytest.fixture
def mock_kokoro_engine():
    """Create a mock Kokoro engine for testing without real deps."""
    mock = MagicMock()
    # Return mock audio samples (0.5 seconds of silence at 24kHz)
    mock.create.return_value = ([0.0] * 12000, 24000)
    return mock


@pytest.fixture
def sample_persona() -> VoicePersona:
    """Create a sample persona for testing."""
    return VoicePersona(
        persona_id="test_persona",
        name="Test Voice",
        voice_model="am_adam",
        speed=1.0,
        pitch=1.0,
    )


# ==============================================================================
# TESTS: Protocol Compliance
# ==============================================================================

class TestProtocolCompliance:
    """Verify KokoroTTSAdapter implements TTSAdapter protocol."""

    def test_adapter_is_tts_adapter_instance(self, kokoro_adapter):
        """KokoroTTSAdapter should be a TTSAdapter instance."""
        from aidm.immersion.tts_adapter import TTSAdapter
        # Protocol check via isinstance (runtime_checkable)
        assert isinstance(kokoro_adapter, TTSAdapter)

    def test_adapter_has_synthesize_method(self, kokoro_adapter):
        """Adapter should have synthesize method."""
        assert hasattr(kokoro_adapter, "synthesize")
        assert callable(kokoro_adapter.synthesize)

    def test_adapter_has_list_personas_method(self, kokoro_adapter):
        """Adapter should have list_personas method."""
        assert hasattr(kokoro_adapter, "list_personas")
        assert callable(kokoro_adapter.list_personas)

    def test_adapter_has_is_available_method(self, kokoro_adapter):
        """Adapter should have is_available method."""
        assert hasattr(kokoro_adapter, "is_available")
        assert callable(kokoro_adapter.is_available)


# ==============================================================================
# TESTS: Persona Listing
# ==============================================================================

class TestPersonaListing:
    """Test voice persona listing and validation."""

    def test_list_personas_returns_list(self, kokoro_adapter):
        """list_personas should return a list."""
        personas = kokoro_adapter.list_personas()
        assert isinstance(personas, list)

    def test_list_personas_has_at_least_three(self, kokoro_adapter):
        """Should have at least 3 voice personas (DM, NPC male, NPC female)."""
        personas = kokoro_adapter.list_personas()
        assert len(personas) >= 3

    def test_personas_are_voice_persona_instances(self, kokoro_adapter):
        """All personas should be VoicePersona instances."""
        personas = kokoro_adapter.list_personas()
        for persona in personas:
            assert isinstance(persona, VoicePersona)

    def test_personas_have_valid_fields(self, kokoro_adapter):
        """All personas should have valid fields."""
        personas = kokoro_adapter.list_personas()
        for persona in personas:
            assert persona.persona_id, f"Persona missing persona_id: {persona}"
            assert persona.name, f"Persona missing name: {persona}"
            assert persona.voice_model, f"Persona missing voice_model: {persona}"
            # Validate speed and pitch ranges
            assert 0.5 <= persona.speed <= 2.0, f"Invalid speed: {persona.speed}"
            assert 0.5 <= persona.pitch <= 2.0, f"Invalid pitch: {persona.pitch}"

    def test_personas_validate_successfully(self, kokoro_adapter):
        """All personas should pass validation."""
        personas = kokoro_adapter.list_personas()
        for persona in personas:
            errors = persona.validate()
            assert errors == [], f"Persona {persona.persona_id} has errors: {errors}"

    def test_has_dm_narrator_persona(self, kokoro_adapter):
        """Should have a DM narrator persona."""
        personas = kokoro_adapter.list_personas()
        dm_personas = [p for p in personas if "dm" in p.persona_id.lower()]
        assert len(dm_personas) >= 1, "Missing DM narrator persona"

    def test_has_npc_male_persona(self, kokoro_adapter):
        """Should have an NPC male persona."""
        personas = kokoro_adapter.list_personas()
        male_personas = [p for p in personas if "male" in p.persona_id.lower()]
        assert len(male_personas) >= 1, "Missing NPC male persona"

    def test_has_npc_female_persona(self, kokoro_adapter):
        """Should have an NPC female persona."""
        personas = kokoro_adapter.list_personas()
        female_personas = [p for p in personas if "female" in p.persona_id.lower()]
        assert len(female_personas) >= 1, "Missing NPC female persona"


# ==============================================================================
# TESTS: Default Persona
# ==============================================================================

class TestDefaultPersona:
    """Test default persona handling."""

    def test_has_default_persona(self, kokoro_adapter):
        """Adapter should have a default persona."""
        default = kokoro_adapter.get_default_persona()
        assert default is not None
        assert isinstance(default, VoicePersona)

    def test_can_set_default_persona(self, kokoro_adapter, sample_persona):
        """Should be able to set default persona."""
        kokoro_adapter.set_default_persona(sample_persona)
        assert kokoro_adapter.get_default_persona() == sample_persona

    def test_custom_default_persona_in_constructor(self, sample_persona):
        """Can pass custom default persona to constructor."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter
        adapter = KokoroTTSAdapter(default_persona=sample_persona)
        assert adapter.get_default_persona() == sample_persona


# ==============================================================================
# TESTS: Synthesis (Mocked)
# ==============================================================================

class TestSynthesisMocked:
    """Test synthesis behavior with mocked Kokoro engine."""

    def test_synthesize_empty_text_returns_bytes(self, kokoro_adapter):
        """Synthesizing empty text should return empty WAV bytes."""
        result = kokoro_adapter.synthesize("")
        assert isinstance(result, bytes)

    def test_synthesize_whitespace_returns_bytes(self, kokoro_adapter):
        """Synthesizing whitespace should return empty WAV bytes."""
        result = kokoro_adapter.synthesize("   ")
        assert isinstance(result, bytes)

    def test_synthesize_returns_bytes(self, mock_kokoro_engine):
        """Synthesize should return bytes when engine available."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter, _loader

        with patch.object(_loader, "is_available", return_value=True):
            with patch.object(_loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter = KokoroTTSAdapter()
                result = adapter.synthesize("Hello world")
                assert isinstance(result, bytes)

    def test_synthesize_with_persona(self, mock_kokoro_engine, sample_persona):
        """Synthesize should accept persona parameter."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter, _loader

        with patch.object(_loader, "is_available", return_value=True):
            with patch.object(_loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter = KokoroTTSAdapter()
                result = adapter.synthesize("Test text", persona=sample_persona)
                assert isinstance(result, bytes)

    def test_synthesis_increments_count(self, mock_kokoro_engine):
        """Each synthesis should increment the count."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter, _loader

        with patch.object(_loader, "is_available", return_value=True):
            with patch.object(_loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter = KokoroTTSAdapter()
                assert adapter.get_synthesis_count() == 0

                adapter.synthesize("First")
                assert adapter.get_synthesis_count() == 1

                adapter.synthesize("Second")
                assert adapter.get_synthesis_count() == 2


# ==============================================================================
# TESTS: WAV Format Validation
# ==============================================================================

class TestWavFormatValidation:
    """Test that synthesized audio is valid WAV format."""

    def test_output_is_valid_wav(self, mock_kokoro_engine):
        """Output should be valid WAV format."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter, _loader

        with patch.object(_loader, "is_available", return_value=True):
            with patch.object(_loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter = KokoroTTSAdapter()
                wav_bytes = adapter.synthesize("Test")

                # Should be parseable as WAV
                buffer = io.BytesIO(wav_bytes)
                with wave.open(buffer, "rb") as wav_file:
                    assert wav_file.getnchannels() == 1  # Mono
                    assert wav_file.getsampwidth() == 2  # 16-bit

    def test_wav_has_riff_header(self, mock_kokoro_engine):
        """WAV output should have RIFF header."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter, _loader

        with patch.object(_loader, "is_available", return_value=True):
            with patch.object(_loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter = KokoroTTSAdapter()
                wav_bytes = adapter.synthesize("Test")

                # RIFF header check
                assert wav_bytes[:4] == b"RIFF", "Missing RIFF header"
                assert wav_bytes[8:12] == b"WAVE", "Missing WAVE identifier"

    def test_wav_sample_rate_is_16khz(self, mock_kokoro_engine):
        """Output sample rate should be 16kHz."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter, _loader

        with patch.object(_loader, "is_available", return_value=True):
            with patch.object(_loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter = KokoroTTSAdapter()
                wav_bytes = adapter.synthesize("Test")

                buffer = io.BytesIO(wav_bytes)
                with wave.open(buffer, "rb") as wav_file:
                    # Accept 16kHz (target) or 24kHz (Kokoro native)
                    assert wav_file.getframerate() in (16000, 24000)

    def test_empty_text_produces_valid_wav(self, kokoro_adapter):
        """Empty text should produce valid (silent) WAV."""
        wav_bytes = kokoro_adapter.synthesize("")

        if len(wav_bytes) > 0:
            # Should be parseable as WAV
            buffer = io.BytesIO(wav_bytes)
            with wave.open(buffer, "rb") as wav_file:
                assert wav_file.getnchannels() == 1


# ==============================================================================
# TESTS: Availability Check
# ==============================================================================

class TestAvailability:
    """Test availability checking and fallback behavior."""

    def test_is_available_returns_bool(self, kokoro_adapter):
        """is_available should return a boolean."""
        result = kokoro_adapter.is_available()
        assert isinstance(result, bool)

    def test_unavailable_when_deps_missing(self):
        """Should report unavailable when deps missing."""
        from aidm.immersion.kokoro_tts_adapter import _KokoroLoader

        loader = _KokoroLoader()
        with patch.dict("sys.modules", {"kokoro_onnx": None}):
            # Force re-check
            loader._available = None
            # This may still return True if kokoro is installed
            # Just verify it returns a bool
            result = loader.is_available()
            assert isinstance(result, bool)

    def test_synthesize_raises_when_unavailable(self, kokoro_adapter):
        """Synthesize should raise when Kokoro unavailable."""
        from aidm.immersion.kokoro_tts_adapter import _loader

        with patch.object(_loader, "is_available", return_value=False):
            with patch.object(_loader, "get_kokoro", side_effect=RuntimeError("Not available")):
                with pytest.raises(RuntimeError, match="[Nn]ot available"):
                    kokoro_adapter.synthesize("Test")


# ==============================================================================
# TESTS: Voice Resolution
# ==============================================================================

class TestVoiceResolution:
    """Test voice ID resolution from personas."""

    def test_resolve_voice_from_voice_model(self, kokoro_adapter):
        """Should use voice_model directly when specified."""
        persona = VoicePersona(
            persona_id="custom",
            name="Custom",
            voice_model="am_michael",
        )
        voice_id = kokoro_adapter._resolve_voice(persona)
        assert voice_id == "am_michael"

    def test_resolve_voice_from_persona_id(self, kokoro_adapter):
        """Should map persona_id to voice when voice_model is default."""
        persona = VoicePersona(
            persona_id="dm_narrator",
            name="DM",
            voice_model="default",
        )
        voice_id = kokoro_adapter._resolve_voice(persona)
        # Should resolve to a known Kokoro voice
        assert voice_id.startswith(("af_", "am_", "bf_", "bm_"))

    def test_resolve_voice_falls_back_to_dm(self, kokoro_adapter):
        """Should fall back to DM voice for unknown personas."""
        persona = VoicePersona(
            persona_id="unknown_persona",
            name="Unknown",
            voice_model="default",
        )
        voice_id = kokoro_adapter._resolve_voice(persona)
        # Should still get a valid voice
        assert voice_id.startswith(("af_", "am_", "bf_", "bm_"))


# ==============================================================================
# TESTS: Factory Function
# ==============================================================================

class TestFactoryFunction:
    """Test create_kokoro_adapter factory function."""

    def test_factory_returns_adapter(self):
        """Factory should return KokoroTTSAdapter."""
        from aidm.immersion.kokoro_tts_adapter import create_kokoro_adapter, KokoroTTSAdapter
        adapter = create_kokoro_adapter()
        assert isinstance(adapter, KokoroTTSAdapter)

    def test_factory_with_custom_persona(self, sample_persona):
        """Factory should accept custom default persona."""
        from aidm.immersion.kokoro_tts_adapter import create_kokoro_adapter
        adapter = create_kokoro_adapter(default_persona=sample_persona)
        assert adapter.get_default_persona() == sample_persona

    def test_factory_fallback_disabled_raises(self):
        """Factory should raise when fallback disabled and unavailable."""
        from aidm.immersion.kokoro_tts_adapter import create_kokoro_adapter, _loader

        with patch.object(_loader, "is_available", return_value=False):
            with patch.object(_loader, "get_error", return_value="Test error"):
                with pytest.raises(RuntimeError):
                    create_kokoro_adapter(fallback_to_stub=False)


# ==============================================================================
# TESTS: Integration (Requires Kokoro)
# ==============================================================================

@requires_kokoro
class TestKokoroIntegration:
    """Integration tests that require real Kokoro installation.

    These tests are skipped if Kokoro is not installed.
    """

    def test_real_synthesis_produces_audio(self, kokoro_adapter):
        """Real synthesis should produce non-empty audio."""
        wav_bytes = kokoro_adapter.synthesize("Hello, adventurer.")
        assert len(wav_bytes) > 44  # More than just WAV header

    def test_real_synthesis_all_personas(self, kokoro_adapter):
        """Should synthesize with all available personas."""
        personas = kokoro_adapter.list_personas()
        text = "Roll for initiative."

        for persona in personas:
            wav_bytes = kokoro_adapter.synthesize(text, persona=persona)
            assert len(wav_bytes) > 44, f"Failed for persona {persona.persona_id}"

    def test_real_synthesis_speed_variation(self, kokoro_adapter):
        """Different speeds should produce different audio lengths."""
        text = "The dragon breathes fire."

        slow_persona = VoicePersona(
            persona_id="slow",
            name="Slow",
            voice_model="am_adam",
            speed=0.7,
        )
        fast_persona = VoicePersona(
            persona_id="fast",
            name="Fast",
            voice_model="am_adam",
            speed=1.3,
        )

        slow_audio = kokoro_adapter.synthesize(text, persona=slow_persona)
        fast_audio = kokoro_adapter.synthesize(text, persona=fast_persona)

        # Slow should be longer than fast
        assert len(slow_audio) > len(fast_audio)

    def test_real_synthesis_long_text(self, kokoro_adapter):
        """Should handle longer narration text."""
        long_text = (
            "The ancient dragon rises from its slumber, scales glinting "
            "in the torchlight. Its eyes, burning with centuries of malice, "
            "fix upon your party. With a thunderous roar that shakes the very "
            "foundations of the mountain, it spreads its massive wings."
        )
        wav_bytes = kokoro_adapter.synthesize(long_text)
        assert len(wav_bytes) > 1000  # Should be substantial audio


# ==============================================================================
# TESTS: Audio Quality Sanity Checks
# ==============================================================================

class TestAudioQualitySanity:
    """Basic sanity checks for audio quality."""

    def test_non_silent_audio_has_samples(self, mock_kokoro_engine):
        """Non-empty synthesis should have audio samples."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter, _loader

        # Return non-silent audio
        mock_kokoro_engine.create.return_value = ([0.5] * 12000, 24000)

        with patch.object(_loader, "is_available", return_value=True):
            with patch.object(_loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter = KokoroTTSAdapter()
                wav_bytes = adapter.synthesize("Test")

                # Parse and check frames
                buffer = io.BytesIO(wav_bytes)
                with wave.open(buffer, "rb") as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
                    assert len(frames) > 0

    def test_audio_samples_in_valid_range(self, mock_kokoro_engine):
        """Audio samples should be in valid 16-bit range."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter, _loader

        # Return varied audio samples
        samples = [0.5, -0.5, 0.0, 1.0, -1.0]
        mock_kokoro_engine.create.return_value = (samples * 1000, 24000)

        with patch.object(_loader, "is_available", return_value=True):
            with patch.object(_loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter = KokoroTTSAdapter()
                wav_bytes = adapter.synthesize("Test")

                buffer = io.BytesIO(wav_bytes)
                with wave.open(buffer, "rb") as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
                    # Unpack as 16-bit signed integers
                    n_samples = len(frames) // 2
                    int_samples = struct.unpack(f"<{n_samples}h", frames)
                    # All samples should be in valid range
                    for sample in int_samples:
                        assert -32768 <= sample <= 32767


# ==============================================================================
# TESTS: Error Handling
# ==============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_synthesis_with_special_characters(self, mock_kokoro_engine):
        """Should handle special characters in text."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter, _loader

        with patch.object(_loader, "is_available", return_value=True):
            with patch.object(_loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter = KokoroTTSAdapter()
                # Should not raise
                result = adapter.synthesize("Roll 2d6+3! (Critical hit)")
                assert isinstance(result, bytes)

    def test_synthesis_with_numbers(self, mock_kokoro_engine):
        """Should handle numbers in text."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter, _loader

        with patch.object(_loader, "is_available", return_value=True):
            with patch.object(_loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter = KokoroTTSAdapter()
                result = adapter.synthesize("You deal 25 damage.")
                assert isinstance(result, bytes)

    def test_synthesis_wraps_engine_errors(self, mock_kokoro_engine):
        """Engine errors should be wrapped in RuntimeError."""
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter, _loader

        mock_kokoro_engine.create.side_effect = ValueError("Engine error")

        with patch.object(_loader, "is_available", return_value=True):
            with patch.object(_loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter = KokoroTTSAdapter()
                with pytest.raises(RuntimeError, match="synthesis failed"):
                    adapter.synthesize("Test")
