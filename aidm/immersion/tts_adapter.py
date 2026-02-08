"""M3 TTS Adapter — Text-to-speech with pluggable backends.

Provides:
- TTSAdapter Protocol: synthesize(text, persona) -> bytes
- StubTTSAdapter: Returns empty bytes, lists one default persona
- create_tts_adapter(backend) factory with registry

Atmospheric only — TTS output is never mechanical authority.
"""

from typing import Dict, List, Optional, Protocol, runtime_checkable

from aidm.schemas.immersion import VoicePersona


@runtime_checkable
class TTSAdapter(Protocol):
    """Protocol for text-to-speech adapters."""

    def synthesize(self, text: str, persona: Optional[VoicePersona] = None) -> bytes:
        """Synthesize text to audio bytes.

        Args:
            text: Text to synthesize
            persona: Optional voice persona configuration

        Returns:
            Raw audio bytes (format depends on backend)
        """
        ...

    def list_personas(self) -> List[VoicePersona]:
        """List available voice personas.

        Returns:
            List of available VoicePersona configurations
        """
        ...

    def is_available(self) -> bool:
        """Check if the adapter backend is available."""
        ...


_DEFAULT_PERSONA = VoicePersona(
    persona_id="dm_default",
    name="Dungeon Master",
    voice_model="default",
    speed=1.0,
    pitch=1.0,
)


class StubTTSAdapter:
    """Stub TTS adapter that returns empty audio bytes.

    Used as default when no real TTS backend is installed.
    Lists one default "Dungeon Master" persona.
    """

    def synthesize(self, text: str, persona: Optional[VoicePersona] = None) -> bytes:
        """Return empty bytes (stub).

        Args:
            text: Ignored (stub)
            persona: Ignored (stub)

        Returns:
            Empty bytes
        """
        return b""

    def list_personas(self) -> List[VoicePersona]:
        """Return default persona list.

        Returns:
            List containing one default Dungeon Master persona
        """
        return [_DEFAULT_PERSONA]

    def is_available(self) -> bool:
        """Stub is always available."""
        return True


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_TTS_REGISTRY: Dict[str, type] = {
    "stub": StubTTSAdapter,
}


def create_tts_adapter(backend: str = "stub") -> TTSAdapter:
    """Create a TTS adapter by backend name.

    Args:
        backend: Backend identifier (e.g., 'stub')

    Returns:
        TTSAdapter instance

    Raises:
        ValueError: If backend is unknown
    """
    if backend not in _TTS_REGISTRY:
        raise ValueError(
            f"Unknown TTS backend: '{backend}'. "
            f"Available: {list(_TTS_REGISTRY.keys())}"
        )
    return _TTS_REGISTRY[backend]()
