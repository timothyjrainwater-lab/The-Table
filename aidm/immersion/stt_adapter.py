"""M3 STT Adapter — Speech-to-text with pluggable backends.

Provides:
- STTAdapter Protocol: transcribe(audio_bytes, sample_rate) -> Transcript
- StubSTTAdapter: Returns canned transcript (confidence=1.0)
- create_stt_adapter(backend) factory with registry

Atmospheric only — STT output is never mechanical authority.
"""

from typing import Dict, List, Optional, Protocol, runtime_checkable

from aidm.schemas.immersion import Transcript


@runtime_checkable
class STTAdapter(Protocol):
    """Protocol for speech-to-text adapters."""

    def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> Transcript:
        """Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw audio data
            sample_rate: Audio sample rate in Hz

        Returns:
            Transcript with text, confidence, and adapter_id
        """
        ...

    def is_available(self) -> bool:
        """Check if the adapter backend is available."""
        ...


class StubSTTAdapter:
    """Stub STT adapter that returns canned transcripts.

    Used as default when no real STT backend is installed.
    Always returns a fixed transcript with confidence=1.0.
    """

    def transcribe(self, audio_bytes: bytes, sample_rate: int = 16000) -> Transcript:
        """Return a canned transcript.

        Args:
            audio_bytes: Ignored (stub)
            sample_rate: Ignored (stub)

        Returns:
            Transcript with placeholder text
        """
        return Transcript(
            text="[stub transcription]",
            confidence=1.0,
            adapter_id="stub",
        )

    def is_available(self) -> bool:
        """Stub is always available."""
        return True


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_STT_REGISTRY: Dict[str, type] = {
    "stub": StubSTTAdapter,
}


def _get_whisper_adapter_class() -> type:
    """Lazy import of WhisperSTTAdapter to avoid import-time dependencies."""
    from aidm.immersion.whisper_stt_adapter import WhisperSTTAdapter
    return WhisperSTTAdapter


# Lazy-loaded adapters (import on first use)
_STT_LAZY_REGISTRY: Dict[str, callable] = {
    "whisper": _get_whisper_adapter_class,
}


def create_stt_adapter(backend: str = "stub") -> STTAdapter:
    """Create an STT adapter by backend name.

    Args:
        backend: Backend identifier (e.g., 'stub', 'whisper')

    Returns:
        STTAdapter instance

    Raises:
        ValueError: If backend is unknown
    """
    # Check direct registry first
    if backend in _STT_REGISTRY:
        return _STT_REGISTRY[backend]()

    # Check lazy registry
    if backend in _STT_LAZY_REGISTRY:
        adapter_class = _STT_LAZY_REGISTRY[backend]()
        return adapter_class()

    # Unknown backend
    all_backends = list(_STT_REGISTRY.keys()) + list(_STT_LAZY_REGISTRY.keys())
    raise ValueError(
        f"Unknown STT backend: '{backend}'. "
        f"Available: {all_backends}"
    )
