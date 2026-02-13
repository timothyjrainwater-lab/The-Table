"""M3 Whisper STT Adapter — Real speech-to-text using faster-whisper.

Implements STTAdapter protocol using the faster-whisper library with the
small.en model for CPU-only transcription. Features:
- Lazy model loading (zero import-time dependencies)
- Word-level confidence scoring
- Graceful fallback when model unavailable
- CPU-only operation (no VRAM usage)

WO-021: Real STT Backend (faster-whisper)
"""

from typing import Any, List, Optional, Tuple

from aidm.schemas.immersion import Transcript


# Type alias for lazy-loaded faster-whisper types
_WhisperModel = Any
_TranscribeResult = Any


class WhisperSTTAdapter:
    """Whisper-based STT adapter using faster-whisper library.

    Implements STTAdapter protocol with lazy model loading.
    Uses the small.en model for CPU-only transcription.

    Attributes:
        model_name: Whisper model name (default: "small.en")
        device: Compute device (default: "cpu")
        compute_type: Compute precision (default: "int8" for CPU)
    """

    def __init__(
        self,
        model_name: str = "small.en",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        """Initialize the Whisper adapter.

        Args:
            model_name: Whisper model to use (default: small.en)
            device: Device for inference ("cpu" or "cuda")
            compute_type: Compute type ("int8" for CPU, "float16" for CUDA)
        """
        self._model_name = model_name
        self._device = device
        self._compute_type = compute_type
        self._model: Optional[_WhisperModel] = None
        self._available: Optional[bool] = None
        self._load_error: Optional[str] = None

    # =========================================================================
    # LAZY LOADING
    # =========================================================================

    def _check_dependencies(self) -> Tuple[bool, str]:
        """Check if faster-whisper is installed.

        Returns:
            Tuple of (available, error_message)
        """
        try:
            import faster_whisper  # noqa: F401
            return True, ""
        except ImportError as e:
            return False, f"faster-whisper not installed: {e}"

    def _load_model(self) -> Tuple[bool, str]:
        """Lazy-load the Whisper model.

        Returns:
            Tuple of (success, error_message)
        """
        if self._model is not None:
            return True, ""

        # Check dependencies first
        deps_ok, deps_error = self._check_dependencies()
        if not deps_ok:
            return False, deps_error

        try:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self._model_name,
                device=self._device,
                compute_type=self._compute_type,
            )
            return True, ""
        except Exception as e:
            error_msg = f"Failed to load Whisper model '{self._model_name}': {e}"
            return False, error_msg

    def _ensure_model(self) -> bool:
        """Ensure model is loaded, caching availability result.

        Returns:
            True if model is ready, False otherwise
        """
        if self._available is not None:
            return self._available

        success, error = self._load_model()
        self._available = success
        if not success:
            self._load_error = error

        return self._available

    # =========================================================================
    # STTAdapter PROTOCOL
    # =========================================================================

    def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> Transcript:
        """Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw audio data (PCM 16-bit signed, mono)
            sample_rate: Audio sample rate in Hz (default: 16000)

        Returns:
            Transcript with text, confidence, and adapter_id
        """
        if not self._ensure_model():
            # Fallback: return empty transcript with low confidence
            return Transcript(
                text="",
                confidence=0.0,
                adapter_id="whisper:unavailable",
            )

        if not audio_bytes:
            return Transcript(
                text="",
                confidence=1.0,
                adapter_id="whisper",
            )

        try:
            # Convert bytes to numpy array
            audio_array = self._bytes_to_audio(audio_bytes, sample_rate)

            # Transcribe using faster-whisper
            segments, info = self._model.transcribe(
                audio_array,
                language="en",
                beam_size=5,
                word_timestamps=True,
                vad_filter=True,
            )

            # Collect text and word-level confidences
            text_parts: List[str] = []
            word_confidences: List[float] = []

            for segment in segments:
                text_parts.append(segment.text)

                # Collect word-level confidences if available
                if hasattr(segment, "words") and segment.words:
                    for word_info in segment.words:
                        if hasattr(word_info, "probability"):
                            word_confidences.append(word_info.probability)

            full_text = "".join(text_parts).strip()

            # Compute overall confidence
            confidence = self._compute_confidence(word_confidences, info)

            return Transcript(
                text=full_text,
                confidence=confidence,
                adapter_id="whisper",
            )

        except Exception as e:
            # Return error transcript with low confidence
            return Transcript(
                text=f"[transcription error: {e}]",
                confidence=0.0,
                adapter_id="whisper:error",
            )

    def is_available(self) -> bool:
        """Check if the Whisper backend is available.

        Returns True only if:
        1. faster-whisper is installed
        2. The model can be loaded

        Returns:
            True if ready for transcription, False otherwise
        """
        return self._ensure_model()

    # =========================================================================
    # AUDIO PROCESSING
    # =========================================================================

    def _bytes_to_audio(self, audio_bytes: bytes, sample_rate: int) -> Any:
        """Convert raw PCM bytes to numpy array.

        Assumes 16-bit signed PCM, mono audio.

        Args:
            audio_bytes: Raw PCM audio data
            sample_rate: Sample rate in Hz

        Returns:
            Numpy array of float32 normalized audio
        """
        import numpy as np

        # Convert 16-bit signed PCM to float32 normalized [-1.0, 1.0]
        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0

        # faster-whisper expects 16kHz, resample if needed
        if sample_rate != 16000:
            audio_float32 = self._resample(audio_float32, sample_rate, 16000)

        return audio_float32

    def _resample(
        self, audio: Any, orig_sr: int, target_sr: int
    ) -> Any:
        """Resample audio to target sample rate.

        Uses simple linear interpolation for portability.

        Args:
            audio: Numpy array of audio samples
            orig_sr: Original sample rate
            target_sr: Target sample rate

        Returns:
            Resampled audio array
        """
        import numpy as np

        if orig_sr == target_sr:
            return audio

        # Calculate ratio and new length
        ratio = target_sr / orig_sr
        new_length = int(len(audio) * ratio)

        if new_length == 0:
            return np.array([], dtype=np.float32)

        # Linear interpolation resampling
        old_indices = np.arange(len(audio))
        new_indices = np.linspace(0, len(audio) - 1, new_length)
        resampled = np.interp(new_indices, old_indices, audio)

        return resampled.astype(np.float32)

    # =========================================================================
    # CONFIDENCE SCORING
    # =========================================================================

    def _compute_confidence(
        self, word_confidences: List[float], transcribe_info: Any
    ) -> float:
        """Compute overall transcription confidence.

        Combines word-level probabilities with language detection confidence.

        Args:
            word_confidences: List of per-word confidence scores
            transcribe_info: TranscriptionInfo from faster-whisper

        Returns:
            Overall confidence score in [0.0, 1.0]
        """
        if not word_confidences:
            # Fall back to language probability if no word confidences
            if hasattr(transcribe_info, "language_probability"):
                return float(transcribe_info.language_probability)
            return 0.5  # Unknown confidence

        # Geometric mean of word confidences
        import math

        if len(word_confidences) == 1:
            return float(word_confidences[0])

        # Use log-sum to avoid underflow with many words
        log_sum = sum(math.log(max(p, 1e-10)) for p in word_confidences)
        geometric_mean = math.exp(log_sum / len(word_confidences))

        return float(max(0.0, min(1.0, geometric_mean)))

    # =========================================================================
    # DIAGNOSTICS
    # =========================================================================

    def get_model_info(self) -> dict:
        """Get information about the loaded model.

        Returns:
            Dictionary with model configuration and status
        """
        return {
            "model_name": self._model_name,
            "device": self._device,
            "compute_type": self._compute_type,
            "loaded": self._model is not None,
            "available": self._available,
            "load_error": self._load_error,
        }

    def get_last_error(self) -> Optional[str]:
        """Get the last error message if model loading failed.

        Returns:
            Error message string or None
        """
        return self._load_error


# =============================================================================
# FACTORY HELPER
# =============================================================================

def create_whisper_adapter(
    model_name: str = "small.en",
    device: str = "cpu",
    compute_type: str = "int8",
) -> WhisperSTTAdapter:
    """Create a configured WhisperSTTAdapter.

    Args:
        model_name: Whisper model to use
        device: Device for inference
        compute_type: Compute precision type

    Returns:
        Configured WhisperSTTAdapter instance
    """
    return WhisperSTTAdapter(
        model_name=model_name,
        device=device,
        compute_type=compute_type,
    )
