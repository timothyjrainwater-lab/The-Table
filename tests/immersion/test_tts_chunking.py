"""Tests for TTS sentence-boundary chunking and adapter-level integration.

WO-TTS-CHUNKING-001: Validates:
1. chunk_by_sentence() utility (ported from speak.py)
2. ChatterboxTTSAdapter auto-chunks long input
3. KokoroTTSAdapter auto-chunks long input
4. WAV concatenation produces valid output
"""

import io
import struct
import wave
from unittest.mock import MagicMock, patch

import pytest

from aidm.immersion.tts_chunking import chunk_by_sentence
from aidm.schemas.immersion import VoicePersona


# ==============================================================================
# TESTS: chunk_by_sentence utility
# ==============================================================================

class TestChunkBySentence:
    """Test the shared chunking function."""

    def test_short_text_single_chunk(self):
        text = "This is short."
        chunks = chunk_by_sentence(text)
        assert len(chunks) == 1
        assert "This is short" in chunks[0]

    def test_multi_sentence_splits(self):
        text = "First sentence. Second sentence. Third sentence."
        chunks = chunk_by_sentence(text, max_words=5)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.endswith(".")

    def test_respects_max_words(self):
        sentences = [f"Sentence number {i} with extra words" for i in range(20)]
        text = ". ".join(sentences) + "."
        chunks = chunk_by_sentence(text, max_words=20)
        for chunk in chunks:
            word_count = len(chunk.split())
            assert word_count <= 30  # max_words + single-sentence tolerance

    def test_empty_text_returns_original(self):
        chunks = chunk_by_sentence("")
        assert len(chunks) == 1

    def test_preserves_all_content(self):
        text = "Alpha done. Beta done. Gamma done. Delta done."
        chunks = chunk_by_sentence(text, max_words=5)
        combined = " ".join(chunks)
        for word in ("Alpha", "Beta", "Gamma", "Delta"):
            assert word in combined

    def test_single_long_sentence_returned_as_is(self):
        text = "This is a single very long sentence that exceeds the maximum word count limit."
        chunks = chunk_by_sentence(text, max_words=5)
        assert len(chunks) == 1

    def test_default_max_words_is_55(self):
        # 55 words should fit in one chunk
        words = ["word"] * 55
        text = " ".join(words) + "."
        chunks = chunk_by_sentence(text)
        assert len(chunks) == 1

    def test_over_55_words_triggers_split(self):
        # Build text with multiple sentences totalling >55 words
        s1 = " ".join(["word"] * 30) + "."
        s2 = " ".join(["word"] * 30) + "."
        text = f"{s1} {s2}"
        chunks = chunk_by_sentence(text)
        assert len(chunks) == 2

    def test_newline_periods_treated_as_sentence_boundaries(self):
        text = "First.\nSecond.\nThird."
        chunks = chunk_by_sentence(text, max_words=2)
        assert len(chunks) >= 2


# ==============================================================================
# TESTS: ChatterboxTTSAdapter chunking integration
# ==============================================================================

class TestChatterboxChunking:
    """Test that ChatterboxTTSAdapter.synthesize() auto-chunks."""

    @pytest.fixture
    def mock_audio_tensor(self):
        torch = pytest.importorskip("torch", reason="PyTorch not installed")
        try:
            import torch.nn  # noqa: F401
        except (ImportError, ModuleNotFoundError):
            pytest.skip("PyTorch installation is broken")
        t = torch.linspace(0, 0.5, 12000)
        return torch.sin(2 * 3.14159 * 440 * t).unsqueeze(0)

    @pytest.fixture
    def adapter(self):
        from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
        return ChatterboxTTSAdapter()

    @pytest.fixture
    def mock_turbo(self, mock_audio_tensor):
        mock = MagicMock()
        mock.generate.return_value = mock_audio_tensor
        return mock

    @pytest.fixture
    def mock_original(self, mock_audio_tensor):
        mock = MagicMock()
        mock.generate.return_value = mock_audio_tensor
        return mock

    def test_long_input_calls_generate_multiple_times(self, adapter, mock_original):
        """100+ word input should be chunked and generate called per chunk."""
        long_text = ". ".join([f"Sentence {i} with some words" for i in range(20)]) + "."
        persona = VoicePersona(
            persona_id="test", name="Test", voice_model="cb",
            exaggeration=0.5,
        )
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_original", return_value=mock_original):
                result = adapter.synthesize(long_text, persona=persona)
                assert isinstance(result, bytes)
                assert result[:4] == b"RIFF"
                # Should have been called multiple times (one per chunk)
                assert mock_original.generate.call_count > 1

    def test_short_input_single_generate(self, adapter, mock_turbo, mock_original):
        """Short input should produce one generate call (turbo or original)."""
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_turbo", return_value=mock_turbo):
                with patch.object(adapter._loader, "get_original", return_value=mock_original):
                    adapter.synthesize("Short text.")
                    total = mock_turbo.generate.call_count + mock_original.generate.call_count
                    assert total == 1

    def test_concatenated_output_is_valid_wav(self, adapter, mock_original):
        """Multi-chunk output should be a single valid WAV."""
        long_text = ". ".join([f"Sentence {i} with some words" for i in range(20)]) + "."
        persona = VoicePersona(
            persona_id="test", name="Test", voice_model="cb",
            exaggeration=0.5,
        )
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_original", return_value=mock_original):
                wav_bytes = adapter.synthesize(long_text, persona=persona)
                buf = io.BytesIO(wav_bytes)
                with wave.open(buf, "rb") as wf:
                    assert wf.getnchannels() == 1
                    assert wf.getsampwidth() == 2
                    assert wf.getframerate() == 24000
                    # Concatenated audio should have more frames than single chunk
                    assert wf.getnframes() > 12000


# ==============================================================================
# TESTS: KokoroTTSAdapter chunking integration
# ==============================================================================

class TestKokoroChunking:
    """Test that KokoroTTSAdapter.synthesize() auto-chunks."""

    @pytest.fixture
    def mock_kokoro_engine(self):
        mock = MagicMock()
        mock.create.return_value = ([0.5] * 12000, 24000)
        return mock

    @pytest.fixture
    def adapter(self):
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter
        return KokoroTTSAdapter()

    def test_long_input_calls_create_multiple_times(self, adapter, mock_kokoro_engine):
        """100+ word input should be chunked and create called per chunk."""
        long_text = ". ".join([f"Sentence {i} with some words" for i in range(20)]) + "."
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_kokoro", return_value=mock_kokoro_engine):
                result = adapter.synthesize(long_text)
                assert isinstance(result, bytes)
                assert result[:4] == b"RIFF"
                assert mock_kokoro_engine.create.call_count > 1

    def test_short_input_single_create(self, adapter, mock_kokoro_engine):
        """Short input should produce one create call."""
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_kokoro", return_value=mock_kokoro_engine):
                adapter.synthesize("Short text.")
                assert mock_kokoro_engine.create.call_count == 1

    def test_concatenated_output_is_valid_wav(self, adapter, mock_kokoro_engine):
        """Multi-chunk output should be a single valid WAV."""
        long_text = ". ".join([f"Sentence {i} with some words" for i in range(20)]) + "."
        with patch.object(adapter._loader, "is_available", return_value=True):
            with patch.object(adapter._loader, "get_kokoro", return_value=mock_kokoro_engine):
                wav_bytes = adapter.synthesize(long_text)
                buf = io.BytesIO(wav_bytes)
                with wave.open(buf, "rb") as wf:
                    assert wf.getnchannels() == 1
                    assert wf.getsampwidth() == 2
                    # Kokoro outputs at 16kHz (resampled)
                    assert wf.getframerate() in (16000, 24000)
                    assert wf.getnframes() > 0


# ==============================================================================
# TESTS: WAV concatenation helper
# ==============================================================================

class TestWavConcatenation:
    """Test _concatenate_wav produces valid WAV output."""

    def _make_wav(self, n_frames: int = 4800, sample_rate: int = 24000) -> bytes:
        """Create a valid WAV with n_frames of sine wave data."""
        import math
        samples = []
        for i in range(n_frames):
            val = int(16000 * math.sin(2 * math.pi * 440 * i / sample_rate))
            samples.append(struct.pack('<h', val))
        pcm = b''.join(samples)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm)
        return buf.getvalue()

    def test_chatterbox_concatenate_two_parts(self):
        from aidm.immersion.chatterbox_tts_adapter import _concatenate_wav
        wav1 = self._make_wav(4800)
        wav2 = self._make_wav(4800)
        result = _concatenate_wav([wav1, wav2])
        buf = io.BytesIO(result)
        with wave.open(buf, "rb") as wf:
            assert wf.getnframes() == 9600
            assert wf.getframerate() == 24000
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2

    def test_kokoro_concatenate_two_parts(self):
        from aidm.immersion.kokoro_tts_adapter import _concatenate_wav
        wav1 = self._make_wav(4800, sample_rate=16000)
        wav2 = self._make_wav(4800, sample_rate=16000)
        result = _concatenate_wav([wav1, wav2])
        buf = io.BytesIO(result)
        with wave.open(buf, "rb") as wf:
            assert wf.getnframes() == 9600
            assert wf.getframerate() == 16000

    def test_concatenate_single_part_passthrough(self):
        from aidm.immersion.chatterbox_tts_adapter import _concatenate_wav
        wav = self._make_wav(4800)
        result = _concatenate_wav([wav])
        assert result == wav

    def test_concatenated_wav_is_playable(self):
        """Concatenated WAV should have correct RIFF header."""
        from aidm.immersion.chatterbox_tts_adapter import _concatenate_wav
        parts = [self._make_wav(2400) for _ in range(3)]
        result = _concatenate_wav(parts)
        assert result[:4] == b"RIFF"
        assert result[8:12] == b"WAVE"
        buf = io.BytesIO(result)
        with wave.open(buf, "rb") as wf:
            assert wf.getnframes() == 7200
            frames = wf.readframes(wf.getnframes())
            assert len(frames) == 7200 * 2  # 16-bit = 2 bytes per frame
