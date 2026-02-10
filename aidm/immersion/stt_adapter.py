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


def create_stt_adapter(backend: str = "stub") -> STTAdapter:
    """Create an STT adapter by backend name.

    Args:
        backend: Backend identifier (e.g., 'stub')

    Returns:
        STTAdapter instance

    Raises:
        ValueError: If backend is unknown
    """
    if backend not in _STT_REGISTRY:
        raise ValueError(
            f"Unknown STT backend: '{backend}'. "
            f"Available: {list(_STT_REGISTRY.keys())}"
        )
    return _STT_REGISTRY[backend]()
