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

def _get_kokoro_adapter_class() -> type:
    """Lazy import of KokoroTTSAdapter to avoid import-time dependencies."""
    from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter
    return KokoroTTSAdapter


def _get_chatterbox_adapter_class() -> type:
    """Lazy import of ChatterboxTTSAdapter to avoid import-time dependencies."""
    from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
    return ChatterboxTTSAdapter


_TTS_REGISTRY: Dict[str, type] = {
    "stub": StubTTSAdapter,
}

# Lazy registration for backends with heavy dependencies
_TTS_LAZY_REGISTRY: Dict[str, callable] = {
    "kokoro": _get_kokoro_adapter_class,
    "chatterbox": _get_chatterbox_adapter_class,
}


def create_tts_adapter(backend: str = "stub") -> TTSAdapter:
    """Create a TTS adapter by backend name.

    Args:
        backend: Backend identifier (e.g., 'stub', 'kokoro')

    Returns:
        TTSAdapter instance

    Raises:
        ValueError: If backend is unknown
    """
    # Check direct registry first
    if backend in _TTS_REGISTRY:
        return _TTS_REGISTRY[backend]()

    # Check lazy registry for backends with heavy dependencies
    if backend in _TTS_LAZY_REGISTRY:
        adapter_class = _TTS_LAZY_REGISTRY[backend]()
        return adapter_class()

    # Build list of all available backends
    all_backends = list(_TTS_REGISTRY.keys()) + list(_TTS_LAZY_REGISTRY.keys())
    raise ValueError(
        f"Unknown TTS backend: '{backend}'. "
        f"Available: {all_backends}"
    )
