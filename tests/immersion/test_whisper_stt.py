"""Tests for WhisperSTTAdapter — Real STT backend using faster-whisper.

Tests:
- Protocol compliance (isinstance(adapter, STTAdapter))
- Factory creation with fallback to stub
- Lazy model loading (no import-time dependencies)
- Audio format handling (16kHz, various durations)
- Confidence scoring (0.0-1.0 range)
- Graceful error handling when model unavailable
- Integration tests (marked @pytest.mark.requires_whisper)

WO-021: Real STT Backend (faster-whisper)
"""

import math
from unittest.mock import MagicMock, patch

import pytest

from aidm.immersion.stt_adapter import (
    STTAdapter,
    StubSTTAdapter,
    create_stt_adapter,
)
from aidm.immersion.whisper_stt_adapter import (
    WhisperSTTAdapter,
    create_whisper_adapter,
)
from aidm.schemas.immersion import Transcript


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def whisper_adapter() -> WhisperSTTAdapter:
    """Create a WhisperSTTAdapter instance."""
    return WhisperSTTAdapter()


@pytest.fixture
def mock_whisper_model():
    """Create a mock Whisper model for testing."""
    mock_model = MagicMock()

    # Create mock segment with word-level info
    mock_word = MagicMock()
    mock_word.probability = 0.95

    mock_segment = MagicMock()
    mock_segment.text = "Hello, adventurer!"
    mock_segment.words = [mock_word, mock_word, mock_word]

    # Create mock transcription info
    mock_info = MagicMock()
    mock_info.language_probability = 0.98

    # Configure model.transcribe to return segments and info
    mock_model.transcribe.return_value = ([mock_segment], mock_info)

    return mock_model


@pytest.fixture
def sample_audio_16khz() -> bytes:
    """Generate sample 16kHz mono PCM audio (1 second of silence)."""
    import struct

    # 16kHz * 1 second = 16000 samples
    # 16-bit signed = 2 bytes per sample
    samples = [0] * 16000
    return struct.pack(f"{len(samples)}h", *samples)


@pytest.fixture
def sample_audio_44100hz() -> bytes:
    """Generate sample 44.1kHz mono PCM audio (1 second of silence)."""
    import struct

    samples = [0] * 44100
    return struct.pack(f"{len(samples)}h", *samples)


# =============================================================================
# Protocol Compliance Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestWhisperProtocolCompliance:
    """Test that WhisperSTTAdapter satisfies STTAdapter protocol."""

    def test_whisper_satisfies_protocol(self, whisper_adapter: WhisperSTTAdapter):
        """WhisperSTTAdapter should satisfy STTAdapter protocol."""
        assert isinstance(whisper_adapter, STTAdapter)

    def test_whisper_has_transcribe_method(self, whisper_adapter: WhisperSTTAdapter):
        """WhisperSTTAdapter should have transcribe method."""
        assert hasattr(whisper_adapter, "transcribe")
        assert callable(whisper_adapter.transcribe)

    def test_whisper_has_is_available_method(self, whisper_adapter: WhisperSTTAdapter):
        """WhisperSTTAdapter should have is_available method."""
        assert hasattr(whisper_adapter, "is_available")
        assert callable(whisper_adapter.is_available)


# =============================================================================
# Factory Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestWhisperFactory:
    """Test STT factory with Whisper backend."""

    def test_factory_creates_whisper(self):
        """Factory should create WhisperSTTAdapter for 'whisper' backend."""
        adapter = create_stt_adapter("whisper")
        assert isinstance(adapter, WhisperSTTAdapter)

    def test_factory_stub_still_works(self):
        """Factory should still create StubSTTAdapter for 'stub' backend."""
        adapter = create_stt_adapter("stub")
        assert isinstance(adapter, StubSTTAdapter)

    def test_factory_default_still_stub(self):
        """Factory default should still be 'stub'."""
        adapter = create_stt_adapter()
        assert isinstance(adapter, StubSTTAdapter)

    def test_factory_unknown_backend_raises(self):
        """Factory should raise ValueError for unknown backend."""
        with pytest.raises(ValueError, match="Unknown STT backend"):
            create_stt_adapter("nonexistent")

    def test_factory_lists_whisper_in_error(self):
        """Error message should list 'whisper' as available backend."""
        with pytest.raises(ValueError) as exc_info:
            create_stt_adapter("nonexistent")
        assert "whisper" in str(exc_info.value)


# =============================================================================
# Lazy Loading Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestWhisperLazyLoading:
    """Test lazy model loading behavior."""

    def test_model_not_loaded_on_init(self):
        """Model should not be loaded during __init__."""
        adapter = WhisperSTTAdapter()
        assert adapter._model is None
        assert adapter._available is None

    def test_create_whisper_adapter_factory(self):
        """create_whisper_adapter should create configured adapter."""
        adapter = create_whisper_adapter(
            model_name="tiny.en",
            device="cpu",
            compute_type="int8",
        )
        assert adapter._model_name == "tiny.en"
        assert adapter._device == "cpu"
        assert adapter._compute_type == "int8"

    def test_get_model_info_before_load(self):
        """get_model_info should work before model is loaded."""
        adapter = WhisperSTTAdapter()
        info = adapter.get_model_info()

        assert info["model_name"] == "small.en"
        assert info["device"] == "cpu"
        assert info["compute_type"] == "int8"
        assert info["loaded"] is False
        assert info["available"] is None


# =============================================================================
# Unavailable Model Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestWhisperUnavailable:
    """Test behavior when faster-whisper is unavailable."""

    def test_is_available_returns_bool(self, whisper_adapter: WhisperSTTAdapter):
        """is_available should return a boolean."""
        result = whisper_adapter.is_available()
        assert isinstance(result, bool)

    def test_transcribe_returns_transcript_when_unavailable(self):
        """transcribe should return Transcript even when model unavailable."""
        adapter = WhisperSTTAdapter()

        # Force unavailable state
        with patch.object(adapter, "_ensure_model", return_value=False):
            adapter._available = False
            result = adapter.transcribe(b"audio data")

            assert isinstance(result, Transcript)
            assert result.confidence == 0.0
            assert "unavailable" in result.adapter_id

    def test_empty_audio_returns_empty_text(self):
        """Empty audio should return empty transcript."""
        adapter = WhisperSTTAdapter()

        # Mock model as available
        with patch.object(adapter, "_ensure_model", return_value=True):
            adapter._model = MagicMock()
            result = adapter.transcribe(b"")

            assert result.text == ""
            assert result.confidence == 1.0
            assert result.adapter_id == "whisper"


# =============================================================================
# Audio Processing Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestWhisperAudioProcessing:
    """Test audio format handling."""

    def test_bytes_to_audio_16khz(
        self, whisper_adapter: WhisperSTTAdapter, sample_audio_16khz: bytes
    ):
        """Should convert 16kHz PCM bytes to float array."""
        import numpy as np

        audio = whisper_adapter._bytes_to_audio(sample_audio_16khz, 16000)

        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert len(audio) == 16000  # No resampling needed

    def test_bytes_to_audio_resamples(
        self, whisper_adapter: WhisperSTTAdapter, sample_audio_44100hz: bytes
    ):
        """Should resample non-16kHz audio to 16kHz."""
        import numpy as np

        audio = whisper_adapter._bytes_to_audio(sample_audio_44100hz, 44100)

        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        # Should be approximately 16000 samples (16kHz target)
        expected_length = int(44100 * (16000 / 44100))
        assert len(audio) == expected_length

    def test_resample_same_rate(self, whisper_adapter: WhisperSTTAdapter):
        """Resampling with same rate should return original array."""
        import numpy as np

        audio = np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32)
        result = whisper_adapter._resample(audio, 16000, 16000)

        assert len(result) == len(audio)
        np.testing.assert_array_equal(result, audio)

    def test_resample_empty_array(self, whisper_adapter: WhisperSTTAdapter):
        """Resampling empty array should return empty array."""
        import numpy as np

        audio = np.array([], dtype=np.float32)
        result = whisper_adapter._resample(audio, 44100, 16000)

        assert len(result) == 0


# =============================================================================
# Confidence Scoring Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestWhisperConfidence:
    """Test confidence scoring logic."""

    def test_confidence_empty_words(self, whisper_adapter: WhisperSTTAdapter):
        """Empty word list should use language probability fallback."""
        mock_info = MagicMock()
        mock_info.language_probability = 0.85

        confidence = whisper_adapter._compute_confidence([], mock_info)

        assert confidence == 0.85

    def test_confidence_single_word(self, whisper_adapter: WhisperSTTAdapter):
        """Single word confidence should be returned directly."""
        mock_info = MagicMock()

        confidence = whisper_adapter._compute_confidence([0.92], mock_info)

        assert confidence == 0.92

    def test_confidence_multiple_words(self, whisper_adapter: WhisperSTTAdapter):
        """Multiple words should use geometric mean."""
        mock_info = MagicMock()
        word_confidences = [0.9, 0.8, 0.7]

        confidence = whisper_adapter._compute_confidence(word_confidences, mock_info)

        # Geometric mean of [0.9, 0.8, 0.7]
        expected = (0.9 * 0.8 * 0.7) ** (1 / 3)
        assert abs(confidence - expected) < 0.001

    def test_confidence_bounded_0_1(self, whisper_adapter: WhisperSTTAdapter):
        """Confidence should be bounded to [0.0, 1.0]."""
        mock_info = MagicMock()

        # Test with perfect confidence
        confidence = whisper_adapter._compute_confidence([1.0, 1.0, 1.0], mock_info)
        assert 0.0 <= confidence <= 1.0

        # Test with low confidence
        confidence = whisper_adapter._compute_confidence([0.1, 0.1, 0.1], mock_info)
        assert 0.0 <= confidence <= 1.0

    def test_confidence_handles_zero(self, whisper_adapter: WhisperSTTAdapter):
        """Confidence computation should handle near-zero values."""
        mock_info = MagicMock()
        word_confidences = [0.0001, 0.0001]

        # Should not raise and should return valid confidence
        confidence = whisper_adapter._compute_confidence(word_confidences, mock_info)
        assert 0.0 <= confidence <= 1.0
        assert not math.isnan(confidence)
        assert not math.isinf(confidence)


# =============================================================================
# Mock Model Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestWhisperWithMockModel:
    """Test transcription with mocked Whisper model."""

    def test_transcribe_with_mock_model(
        self,
        whisper_adapter: WhisperSTTAdapter,
        mock_whisper_model: MagicMock,
        sample_audio_16khz: bytes,
    ):
        """Transcription should work with mocked model."""
        whisper_adapter._model = mock_whisper_model
        whisper_adapter._available = True

        result = whisper_adapter.transcribe(sample_audio_16khz, 16000)

        assert isinstance(result, Transcript)
        assert result.text == "Hello, adventurer!"
        assert result.adapter_id == "whisper"
        assert 0.0 <= result.confidence <= 1.0

    def test_transcribe_validates_result(
        self,
        whisper_adapter: WhisperSTTAdapter,
        mock_whisper_model: MagicMock,
        sample_audio_16khz: bytes,
    ):
        """Transcription result should pass validation."""
        whisper_adapter._model = mock_whisper_model
        whisper_adapter._available = True

        result = whisper_adapter.transcribe(sample_audio_16khz, 16000)

        assert result.validate() == []

    def test_transcribe_handles_model_error(
        self,
        whisper_adapter: WhisperSTTAdapter,
        sample_audio_16khz: bytes,
    ):
        """Transcription should handle model errors gracefully."""
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("Model error")

        whisper_adapter._model = mock_model
        whisper_adapter._available = True

        result = whisper_adapter.transcribe(sample_audio_16khz, 16000)

        assert isinstance(result, Transcript)
        assert "error" in result.adapter_id
        assert result.confidence == 0.0


# =============================================================================
# Diagnostics Tests
# =============================================================================

@pytest.mark.immersion_fast
class TestWhisperDiagnostics:
    """Test diagnostic methods."""

    def test_get_model_info_after_load_attempt(self, whisper_adapter: WhisperSTTAdapter):
        """get_model_info should reflect load attempt."""
        # Trigger load attempt (will likely fail in test env without model)
        _ = whisper_adapter.is_available()

        info = whisper_adapter.get_model_info()

        assert info["available"] is not None  # Should be set after load attempt
        assert isinstance(info["loaded"], bool)

    def test_get_last_error_none_initially(self, whisper_adapter: WhisperSTTAdapter):
        """get_last_error should be None before any load attempt."""
        assert whisper_adapter.get_last_error() is None

    def test_get_last_error_after_failed_load(self):
        """get_last_error should contain message after failed load."""
        adapter = WhisperSTTAdapter()

        # Mock a failed load
        with patch.object(adapter, "_check_dependencies") as mock_check:
            mock_check.return_value = (False, "test error message")
            _ = adapter.is_available()

        error = adapter.get_last_error()
        assert error is not None
        assert "test error message" in error


# =============================================================================
# Integration Tests (requires faster-whisper)
# =============================================================================

# Custom marker for tests that require the Whisper model
requires_whisper = pytest.mark.skipif(
    not WhisperSTTAdapter().is_available(),
    reason="faster-whisper not available or model not loaded",
)


@pytest.mark.requires_whisper
class TestWhisperIntegration:
    """Integration tests that require faster-whisper and model.

    These tests are skipped if faster-whisper is not installed or
    the model cannot be loaded.
    """

    def test_real_transcription(self, sample_audio_16khz: bytes):
        """Real transcription should work with installed model."""
        adapter = WhisperSTTAdapter()

        if not adapter.is_available():
            pytest.skip("Whisper model not available")

        result = adapter.transcribe(sample_audio_16khz, 16000)

        assert isinstance(result, Transcript)
        assert result.adapter_id == "whisper"
        assert 0.0 <= result.confidence <= 1.0

    def test_cpu_only_no_cuda(self):
        """Adapter should use CPU, not CUDA."""
        adapter = WhisperSTTAdapter()

        info = adapter.get_model_info()

        assert info["device"] == "cpu"
        assert info["compute_type"] == "int8"

    def test_model_loads_lazily(self):
        """Model should only load on first transcribe/is_available."""
        adapter = WhisperSTTAdapter()

        # Model should not be loaded yet
        assert adapter._model is None

        # Trigger load
        _ = adapter.is_available()

        # Now model state should be determined
        assert adapter._available is not None
