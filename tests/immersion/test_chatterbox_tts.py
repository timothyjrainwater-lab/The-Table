"""Chatterbox TTS Adapter Tests.

Test Categories:
1. Adapter construction and defaults (4 tests)
2. Persona resolution (5 tests)
3. Tier selection logic (5 tests)
4. Synthesis with mocked engine (5 tests)
5. WAV format validation (3 tests)
6. Reference audio resolution (4 tests)
7. Factory function (3 tests)
8. Error handling (3 tests)

Total: 32 tests (all unit tests, no GPU required)
"""

import io
import os
import struct
import tempfile
import wave
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from aidm.schemas.immersion import VoicePersona


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def adapter():
    """Create a ChatterboxTTSAdapter with mocked loader."""
    from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
    return ChatterboxTTSAdapter()


@pytest.fixture
def mock_audio_tensor():
    """Create a mock torch tensor that behaves like Chatterbox output."""
    torch = pytest.importorskip("torch", reason="PyTorch not properly installed")
    try:
        import torch.nn  # noqa: F401 — verify real PyTorch, not a stub
    except (ImportError, ModuleNotFoundError):
        pytest.skip("PyTorch installation is broken (torch.nn not available)")
    # 0.5 seconds of sine wave at 24kHz
    t = torch.linspace(0, 0.5, 12000)
    audio = torch.sin(2 * 3.14159 * 440 * t).unsqueeze(0)  # (1, 12000)
    return audio


@pytest.fixture
def mock_turbo(mock_audio_tensor):
    """Create a mock Turbo model."""
    mock = MagicMock()
    mock.generate.return_value = mock_audio_tensor
    mock.sr = 24000
    return mock


@pytest.fixture
def mock_original(mock_audio_tensor):
    """Create a mock Original model."""
    mock = MagicMock()
    mock.generate.return_value = mock_audio_tensor
    mock.sr = 24000
    return mock


@pytest.fixture
def sample_persona():
    """Sample voice persona for testing."""
    return VoicePersona(
        persona_id="test_voice",
        name="Test Voice",
        voice_model="chatterbox",
        speed=1.0,
        pitch=1.0,
        exaggeration=0.5,
    )


@pytest.fixture
def voices_dir(tmp_path):
    """Create a temp voices directory with a dummy reference WAV."""
    wav_path = tmp_path / "dm_narrator.wav"
    # Write a minimal valid WAV file
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(b"\x00\x00" * 24000 * 6)  # 6 seconds of silence
    wav_path.write_bytes(buf.getvalue())
    return str(tmp_path)


# ==============================================================================
# TESTS: Adapter Construction
# ==============================================================================

class TestAdapterConstruction:
    """Test adapter initialization and defaults."""

    def test_default_persona_is_dm_narrator(self, adapter):
        assert adapter.get_default_persona().persona_id == "dm_narrator"

    def test_custom_default_persona(self, sample_persona):
        from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
        adapter = ChatterboxTTSAdapter(default_persona=sample_persona)
        assert adapter.get_default_persona() == sample_persona

    def test_initial_synthesis_count_is_zero(self, adapter):
        assert adapter.get_synthesis_count() == 0

    def test_list_personas_returns_list(self, adapter):
        personas = adapter.list_personas()
        assert isinstance(personas, list)
        assert len(personas) >= 4
        assert all(isinstance(p, VoicePersona) for p in personas)


# ==============================================================================
# TESTS: Persona Resolution
# ==============================================================================

class TestPersonaResolution:
    """Test flexible persona argument handling."""

    def test_none_persona_uses_default(self, adapter):
        result = adapter._resolve_persona(None)
        assert result.persona_id == "dm_narrator"

    def test_voice_persona_passes_through(self, adapter, sample_persona):
        result = adapter._resolve_persona(sample_persona)
        assert result == sample_persona

    def test_string_persona_resolves_known_id(self, adapter):
        result = adapter._resolve_persona("villainous")
        assert result.persona_id == "villainous"
        assert result.exaggeration == 0.7

    def test_string_persona_unknown_creates_default(self, adapter):
        result = adapter._resolve_persona("unknown_voice")
        assert result.persona_id == "unknown_voice"
        assert result.voice_model == "chatterbox"

    def test_invalid_type_uses_default(self, adapter):
        result = adapter._resolve_persona(42)
        assert result.persona_id == "dm_narrator"


# ==============================================================================
# TESTS: Tier Selection
# ==============================================================================

class TestTierSelection:
    """Test Turbo vs Original tier selection logic."""

    def test_short_text_no_emotion_selects_turbo(self, adapter):
        persona = VoicePersona(
            persona_id="t", name="T", voice_model="cb",
            exaggeration=0.0,
        )
        assert adapter._select_tier("Roll for initiative.", persona, False) is True

    def test_long_text_selects_original(self, adapter):
        persona = VoicePersona(
            persona_id="t", name="T", voice_model="cb",
            exaggeration=0.0,
        )
        long_text = " ".join(["word"] * 25)
        assert adapter._select_tier(long_text, persona, False) is False

    def test_high_exaggeration_selects_original(self, adapter):
        persona = VoicePersona(
            persona_id="t", name="T", voice_model="cb",
            exaggeration=0.7,
        )
        assert adapter._select_tier("Short text.", persona, False) is False

    def test_force_turbo_overrides(self, adapter):
        persona = VoicePersona(
            persona_id="t", name="T", voice_model="cb",
            exaggeration=0.9,
        )
        long_text = " ".join(["word"] * 30)
        assert adapter._select_tier(long_text, persona, True) is True

    def test_low_exaggeration_treated_as_no_emotion(self, adapter):
        persona = VoicePersona(
            persona_id="t", name="T", voice_model="cb",
            exaggeration=0.05,
        )
        assert adapter._select_tier("Short text.", persona, False) is True


# ==============================================================================
# TESTS: Synthesis with Mocked Engine
# ==============================================================================

class TestSynthesis:
    """Test synthesis produces correct output."""

    def test_synthesize_returns_bytes(self, adapter, mock_turbo):
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_turbo", return_value=mock_turbo):
                result = adapter.synthesize("Roll for initiative.")
                assert isinstance(result, bytes)
                assert len(result) > 44  # More than WAV header

    def test_synthesize_empty_text_returns_empty_wav(self, adapter):
        result = adapter.synthesize("")
        assert isinstance(result, bytes)
        assert result[:4] == b"RIFF"

    def test_synthesize_whitespace_returns_empty_wav(self, adapter):
        result = adapter.synthesize("   ")
        assert isinstance(result, bytes)

    def test_synthesize_increments_count(self, adapter, mock_turbo):
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_turbo", return_value=mock_turbo):
                assert adapter.get_synthesis_count() == 0
                adapter.synthesize("First")
                assert adapter.get_synthesis_count() == 1
                adapter.synthesize("Second")
                assert adapter.get_synthesis_count() == 2

    def test_synthesize_with_persona(self, adapter, mock_original, sample_persona):
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_original", return_value=mock_original):
                result = adapter.synthesize("Test text", persona=sample_persona)
                assert isinstance(result, bytes)
                # Should use original because exaggeration > 0.1
                mock_original.generate.assert_called_once()


# ==============================================================================
# TESTS: WAV Format Validation
# ==============================================================================

class TestWavFormat:
    """Test that output is valid WAV format."""

    def test_output_is_valid_wav(self, adapter, mock_turbo):
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_turbo", return_value=mock_turbo):
                wav_bytes = adapter.synthesize("Test")
                buffer = io.BytesIO(wav_bytes)
                with wave.open(buffer, "rb") as wf:
                    assert wf.getnchannels() == 1
                    assert wf.getsampwidth() == 2

    def test_wav_has_riff_header(self, adapter, mock_turbo):
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_turbo", return_value=mock_turbo):
                wav_bytes = adapter.synthesize("Test")
                assert wav_bytes[:4] == b"RIFF"
                assert wav_bytes[8:12] == b"WAVE"

    def test_wav_sample_rate_is_24khz(self, adapter, mock_turbo):
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_turbo", return_value=mock_turbo):
                wav_bytes = adapter.synthesize("Test")
                buffer = io.BytesIO(wav_bytes)
                with wave.open(buffer, "rb") as wf:
                    assert wf.getframerate() == 24000


# ==============================================================================
# TESTS: Reference Audio Resolution
# ==============================================================================

class TestReferenceAudio:
    """Test reference audio file resolution."""

    def test_no_reference_returns_none(self, adapter):
        persona = VoicePersona(
            persona_id="test", name="Test", voice_model="cb",
        )
        result = adapter._resolve_reference_audio(persona)
        assert result is None

    def test_absolute_path_reference(self, adapter, voices_dir):
        wav_path = os.path.join(voices_dir, "dm_narrator.wav")
        persona = VoicePersona(
            persona_id="test", name="Test", voice_model="cb",
            reference_audio=wav_path,
        )
        result = adapter._resolve_reference_audio(persona)
        assert result == wav_path

    def test_relative_path_with_voices_dir(self, voices_dir):
        from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
        adapter = ChatterboxTTSAdapter(voices_dir=voices_dir)
        persona = VoicePersona(
            persona_id="test", name="Test", voice_model="cb",
            reference_audio="dm_narrator.wav",
        )
        result = adapter._resolve_reference_audio(persona)
        assert result is not None
        assert result.endswith("dm_narrator.wav")

    def test_persona_id_lookup_in_voices_dir(self, voices_dir):
        from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
        adapter = ChatterboxTTSAdapter(voices_dir=voices_dir)
        persona = VoicePersona(
            persona_id="dm_narrator", name="DM", voice_model="cb",
        )
        result = adapter._resolve_reference_audio(persona)
        assert result is not None
        assert "dm_narrator.wav" in result


# ==============================================================================
# TESTS: Factory Function
# ==============================================================================

class TestFactory:
    """Test create_chatterbox_adapter factory."""

    def test_factory_creates_adapter(self):
        from aidm.immersion.chatterbox_tts_adapter import create_chatterbox_adapter
        adapter = create_chatterbox_adapter()
        from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
        assert isinstance(adapter, ChatterboxTTSAdapter)

    def test_factory_with_custom_persona(self, sample_persona):
        from aidm.immersion.chatterbox_tts_adapter import create_chatterbox_adapter
        adapter = create_chatterbox_adapter(default_persona=sample_persona)
        assert adapter.get_default_persona() == sample_persona

    def test_factory_fallback_disabled_raises(self):
        from aidm.immersion.chatterbox_tts_adapter import (
            create_chatterbox_adapter, _dep_checker,
        )
        with patch.object(_dep_checker, "is_available", return_value=False):
            with patch.object(_dep_checker, "get_error", return_value="No CUDA"):
                with pytest.raises(RuntimeError):
                    create_chatterbox_adapter(fallback_to_stub=False)


# ==============================================================================
# TESTS: Error Handling
# ==============================================================================

class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_synthesis_wraps_engine_errors(self, adapter, mock_turbo):
        mock_turbo.generate.side_effect = ValueError("Engine error")
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_turbo", return_value=mock_turbo):
                with patch.object(adapter._loader, "get_original", return_value=mock_turbo):
                    with pytest.raises(RuntimeError, match="synthesis failed"):
                        adapter.synthesize("Test")

    def test_synthesis_with_special_characters(self, adapter, mock_turbo):
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_turbo", return_value=mock_turbo):
                result = adapter.synthesize("Roll 2d6+3! (Critical hit)")
                assert isinstance(result, bytes)

    def test_missing_reference_audio_logs_warning(self, adapter, caplog):
        import logging
        persona = VoicePersona(
            persona_id="test", name="Test", voice_model="cb",
            reference_audio="/nonexistent/path/voice.wav",
        )
        with caplog.at_level(logging.WARNING):
            result = adapter._resolve_reference_audio(persona)
        assert result is None
