"""Tests for M3 Voice Pipeline (STT + TTS Adapters).

Tests:
- STT stub returns canned transcript
- STT protocol compliance
- STT factory creates correct adapter
- STT factory rejects unknown backend
- TTS stub returns empty bytes
- TTS stub lists default persona
- TTS protocol compliance
- TTS factory creates correct adapter
- TTS factory rejects unknown backend
"""

import pytest

from aidm.immersion.stt_adapter import (
    STTAdapter,
    StubSTTAdapter,
    create_stt_adapter,
)
from aidm.immersion.tts_adapter import (
    TTSAdapter,
    StubTTSAdapter,
    create_tts_adapter,
)
from aidm.schemas.immersion import Transcript, VoicePersona


# =============================================================================
# STT Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestSTTAdapter:
    """Tests for STT adapter and factory."""

    def test_stub_returns_transcript(self):
        """StubSTTAdapter should return a Transcript."""
        adapter = StubSTTAdapter()
        result = adapter.transcribe(b"audio data")
        assert isinstance(result, Transcript)
        assert result.text == "[stub transcription]"
        assert result.confidence == 1.0
        assert result.adapter_id == "stub"

    def test_stub_is_available(self):
        """StubSTTAdapter should always be available."""
        adapter = StubSTTAdapter()
        assert adapter.is_available() is True

    def test_stub_ignores_sample_rate(self):
        """StubSTTAdapter should work with any sample rate."""
        adapter = StubSTTAdapter()
        r1 = adapter.transcribe(b"data", sample_rate=8000)
        r2 = adapter.transcribe(b"data", sample_rate=44100)
        assert r1.text == r2.text

    def test_stub_ignores_audio_content(self):
        """StubSTTAdapter should return same result regardless of audio."""
        adapter = StubSTTAdapter()
        r1 = adapter.transcribe(b"")
        r2 = adapter.transcribe(b"\x00" * 1000)
        assert r1.text == r2.text

    def test_stub_satisfies_protocol(self):
        """StubSTTAdapter should satisfy STTAdapter protocol."""
        adapter = StubSTTAdapter()
        assert isinstance(adapter, STTAdapter)

    def test_factory_creates_stub(self):
        """Factory should create StubSTTAdapter for 'stub' backend."""
        adapter = create_stt_adapter("stub")
        assert isinstance(adapter, StubSTTAdapter)

    def test_factory_default_is_stub(self):
        """Factory default should be 'stub'."""
        adapter = create_stt_adapter()
        assert isinstance(adapter, StubSTTAdapter)

    def test_factory_unknown_backend_raises(self):
        """Factory should raise ValueError for unknown backend."""
        with pytest.raises(ValueError, match="Unknown STT backend"):
            create_stt_adapter("nonexistent")

    def test_transcript_validates(self):
        """StubSTTAdapter transcripts should pass validation."""
        adapter = StubSTTAdapter()
        result = adapter.transcribe(b"data")
        assert result.validate() == []


# =============================================================================
# TTS Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestTTSAdapter:
    """Tests for TTS adapter and factory."""

    def test_stub_returns_bytes(self):
        """StubTTSAdapter should return bytes."""
        adapter = StubTTSAdapter()
        result = adapter.synthesize("Hello, adventurers!")
        assert isinstance(result, bytes)
        assert result == b""

    def test_stub_is_available(self):
        """StubTTSAdapter should always be available."""
        adapter = StubTTSAdapter()
        assert adapter.is_available() is True

    def test_stub_lists_one_persona(self):
        """StubTTSAdapter should list one default persona."""
        adapter = StubTTSAdapter()
        personas = adapter.list_personas()
        assert len(personas) == 1
        assert personas[0].name == "Dungeon Master"
        assert personas[0].persona_id == "dm_default"

    def test_stub_persona_validates(self):
        """Default persona should pass validation."""
        adapter = StubTTSAdapter()
        personas = adapter.list_personas()
        assert personas[0].validate() == []

    def test_stub_accepts_persona(self):
        """StubTTSAdapter should accept persona parameter without error."""
        adapter = StubTTSAdapter()
        persona = VoicePersona(persona_id="custom", name="NPC Voice")
        result = adapter.synthesize("text", persona=persona)
        assert isinstance(result, bytes)

    def test_stub_accepts_none_persona(self):
        """StubTTSAdapter should accept None persona."""
        adapter = StubTTSAdapter()
        result = adapter.synthesize("text", persona=None)
        assert isinstance(result, bytes)

    def test_stub_satisfies_protocol(self):
        """StubTTSAdapter should satisfy TTSAdapter protocol."""
        adapter = StubTTSAdapter()
        assert isinstance(adapter, TTSAdapter)

    def test_factory_creates_stub(self):
        """Factory should create StubTTSAdapter for 'stub' backend."""
        adapter = create_tts_adapter("stub")
        assert isinstance(adapter, StubTTSAdapter)

    def test_factory_default_is_stub(self):
        """Factory default should be 'stub'."""
        adapter = create_tts_adapter()
        assert isinstance(adapter, StubTTSAdapter)

    def test_factory_unknown_backend_raises(self):
        """Factory should raise ValueError for unknown backend."""
        with pytest.raises(ValueError, match="Unknown TTS backend"):
            create_tts_adapter("nonexistent")
