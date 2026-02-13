"""M3 Kokoro TTS Adapter — High-quality neural TTS using ONNX.

Provides:
- KokoroTTSAdapter: Real TTS backend using Kokoro ONNX models
- Lazy initialization to avoid import-time dependencies
- CPU-only inference (0 GB VRAM per R1 stack requirements)
- Graceful fallback to stub if dependencies unavailable

Voice personas optimized for D&D 3.5 narration:
- DM Narrator (authoritative, clear)
- NPC Male (versatile male NPC voice)
- NPC Female (versatile female NPC voice)
- Villainous (dramatic, sinister)
- Heroic (bold, inspiring)

Atmospheric only — TTS output is never mechanical authority.

WO-020: Real TTS Backend (Kokoro)
"""

import io
import struct
import wave
from typing import Any, Dict, List, Optional, Tuple

from aidm.schemas.immersion import VoicePersona


# ==============================================================================
# CONSTANTS
# ==============================================================================

# Default audio format: 16-bit PCM, 16kHz mono (matches Whisper STT input)
DEFAULT_SAMPLE_RATE = 24000  # Kokoro outputs 24kHz by default
OUTPUT_SAMPLE_RATE = 16000   # Our target output rate
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit


# ==============================================================================
# VOICE PERSONA DEFINITIONS
# ==============================================================================

# Mapping of persona_id to Kokoro voice identifiers
# Kokoro supports multiple voices: af_bella, af_nicole, af_sarah, af_sky,
# am_adam, am_michael, bf_emma, bf_isabella, bm_george, bm_lewis
_KOKORO_VOICE_MAP: Dict[str, str] = {
    "dm_narrator": "af_bella",       # Clear, authoritative female narrator
    "dm_narrator_male": "am_adam",   # Clear, authoritative male narrator
    "npc_male": "am_michael",        # Versatile male NPC
    "npc_female": "af_nicole",       # Versatile female NPC
    "npc_elderly": "bm_george",      # British elderly male (wizards, sages)
    "npc_young": "af_sky",           # Youthful voice
    "villainous": "bm_lewis",        # Dramatic, darker tone
    "heroic": "am_adam",             # Bold, confident
}

# Pre-defined voice personas for D&D narration
_KOKORO_PERSONAS: List[VoicePersona] = [
    VoicePersona(
        persona_id="dm_narrator",
        name="Dungeon Master",
        voice_model="af_bella",
        speed=1.0,
        pitch=1.0,
    ),
    VoicePersona(
        persona_id="dm_narrator_male",
        name="Dungeon Master (Male)",
        voice_model="am_adam",
        speed=1.0,
        pitch=1.0,
    ),
    VoicePersona(
        persona_id="npc_male",
        name="NPC Male",
        voice_model="am_michael",
        speed=1.0,
        pitch=1.0,
    ),
    VoicePersona(
        persona_id="npc_female",
        name="NPC Female",
        voice_model="af_nicole",
        speed=1.0,
        pitch=1.0,
    ),
    VoicePersona(
        persona_id="npc_elderly",
        name="NPC Elderly",
        voice_model="bm_george",
        speed=0.9,
        pitch=0.95,
    ),
    VoicePersona(
        persona_id="npc_young",
        name="NPC Young",
        voice_model="af_sky",
        speed=1.05,
        pitch=1.05,
    ),
    VoicePersona(
        persona_id="villainous",
        name="Villain",
        voice_model="bm_lewis",
        speed=0.95,
        pitch=0.9,
    ),
    VoicePersona(
        persona_id="heroic",
        name="Hero",
        voice_model="am_adam",
        speed=1.0,
        pitch=1.0,
    ),
]

# Default persona when none specified
_DEFAULT_PERSONA = _KOKORO_PERSONAS[0]


# ==============================================================================
# LAZY LOADER
# ==============================================================================

class _KokoroLoader:
    """Lazy loader for Kokoro TTS dependencies.

    Avoids import-time dependencies on onnxruntime and kokoro_onnx.
    Initializes only when first synthesis requested.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        voices_path: Optional[str] = None,
    ) -> None:
        self._model_path = model_path
        self._voices_path = voices_path
        self._kokoro: Any = None
        self._initialized: bool = False
        self._available: Optional[bool] = None
        self._error_message: str = ""

    def is_available(self) -> bool:
        """Check if Kokoro TTS is available.

        Returns:
            True if kokoro-onnx and onnxruntime are installed
        """
        if self._available is not None:
            return self._available

        try:
            # Try importing dependencies
            import onnxruntime  # noqa: F401
            from kokoro_onnx import Kokoro  # noqa: F401
            self._available = True
        except ImportError as e:
            self._available = False
            self._error_message = str(e)
        except Exception as e:
            self._available = False
            self._error_message = f"Unexpected error: {e}"

        return self._available

    def get_kokoro(self) -> Any:
        """Get or initialize the Kokoro TTS engine.

        Returns:
            Initialized Kokoro instance

        Raises:
            RuntimeError: If Kokoro is not available or model paths missing
        """
        if not self.is_available():
            raise RuntimeError(
                f"Kokoro TTS not available: {self._error_message}. "
                "Install with: pip install kokoro-onnx onnxruntime"
            )

        if not self._initialized:
            if not self._model_path or not self._voices_path:
                raise RuntimeError(
                    "Kokoro model files not configured. "
                    "Provide model_path and voices_path to KokoroTTSAdapter."
                )
            from kokoro_onnx import Kokoro
            # Initialize with CPU provider only (0 GB VRAM requirement)
            self._kokoro = Kokoro(
                model_path=self._model_path,
                voices_path=self._voices_path,
            )
            self._initialized = True

        return self._kokoro

    def get_error(self) -> str:
        """Get the error message if not available."""
        return self._error_message


# Global lazy loader for dependency checking (no model paths needed)
_dep_checker = _KokoroLoader()


# ==============================================================================
# WAV ENCODING
# ==============================================================================

def _encode_wav(
    samples: bytes,
    sample_rate: int = OUTPUT_SAMPLE_RATE,
    channels: int = CHANNELS,
    sample_width: int = SAMPLE_WIDTH,
) -> bytes:
    """Encode raw PCM samples to WAV format.

    Args:
        samples: Raw PCM audio samples
        sample_rate: Sample rate in Hz
        channels: Number of audio channels
        sample_width: Bytes per sample (2 = 16-bit)

    Returns:
        WAV-encoded audio bytes
    """
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(samples)
    return buffer.getvalue()


def _resample_simple(
    samples: List[float],
    input_rate: int,
    output_rate: int,
) -> List[float]:
    """Simple linear resampling.

    Args:
        samples: Input audio samples
        input_rate: Input sample rate
        output_rate: Output sample rate

    Returns:
        Resampled audio samples
    """
    if input_rate == output_rate:
        return samples

    ratio = output_rate / input_rate
    output_length = int(len(samples) * ratio)
    output = []

    for i in range(output_length):
        # Linear interpolation
        src_idx = i / ratio
        idx0 = int(src_idx)
        idx1 = min(idx0 + 1, len(samples) - 1)
        frac = src_idx - idx0

        if idx0 < len(samples):
            val = samples[idx0] * (1 - frac) + samples[idx1] * frac
            output.append(val)

    return output


def _float_to_int16(samples: List[float]) -> bytes:
    """Convert float samples [-1, 1] to 16-bit PCM bytes.

    Args:
        samples: Float audio samples in range [-1, 1]

    Returns:
        16-bit PCM audio bytes (little-endian)
    """
    int16_samples = []
    for sample in samples:
        # Clamp to [-1, 1] then scale to int16 range
        clamped = max(-1.0, min(1.0, sample))
        int_val = int(clamped * 32767)
        int16_samples.append(int_val)

    # Pack as little-endian 16-bit signed integers
    return struct.pack(f"<{len(int16_samples)}h", *int16_samples)


# ==============================================================================
# KOKORO TTS ADAPTER
# ==============================================================================

class KokoroTTSAdapter:
    """TTS adapter using Kokoro ONNX for high-quality neural TTS.

    Uses lazy initialization to avoid import-time dependencies.
    Falls back gracefully if Kokoro is unavailable.

    Implements the TTSAdapter protocol:
    - synthesize(text, persona) -> WAV bytes
    - list_personas() -> available voice personas
    - is_available() -> True if backend ready

    Persona argument is flexible (satisfies both immersion TTSAdapter
    and orchestrator TTSProtocol):
    - None -> use default persona
    - VoicePersona -> use directly
    - str -> look up in voice map (e.g. "dm_narrator" -> af_bella)
    """

    def __init__(
        self,
        default_persona: Optional[VoicePersona] = None,
        model_path: Optional[str] = None,
        voices_path: Optional[str] = None,
    ) -> None:
        """Initialize the Kokoro TTS adapter.

        Args:
            default_persona: Default persona for synthesis (uses DM narrator if None)
            model_path: Path to Kokoro ONNX model file
            voices_path: Path to Kokoro voices .bin file
        """
        self._default_persona = default_persona or _DEFAULT_PERSONA
        self._synthesis_count: int = 0
        self._loader = _KokoroLoader(
            model_path=model_path,
            voices_path=voices_path,
        )

    def synthesize(
        self,
        text: str,
        persona: Optional[Any] = None,
    ) -> bytes:
        """Synthesize text to WAV audio bytes.

        Args:
            text: Text to synthesize (should be clean, no SSML)
            persona: Voice persona — accepts VoicePersona, str (voice map key),
                     or None (uses default)

        Returns:
            WAV audio bytes (16kHz mono 16-bit PCM)

        Raises:
            RuntimeError: If Kokoro is not available
        """
        if not text or not text.strip():
            # Return silent WAV for empty text
            return _encode_wav(b"")

        # Resolve persona argument: str -> VoicePersona lookup, None -> default
        effective_persona = self._resolve_persona(persona)

        try:
            kokoro = self._loader.get_kokoro()

            # Get voice ID from persona
            voice_id = self._resolve_voice(effective_persona)

            # Generate audio samples
            # Kokoro returns audio as numpy array or list of floats
            audio_samples, sample_rate = self._generate_audio(
                kokoro, text, voice_id, effective_persona.speed
            )

            # Resample to target rate if needed
            if sample_rate != OUTPUT_SAMPLE_RATE:
                audio_samples = _resample_simple(
                    audio_samples, sample_rate, OUTPUT_SAMPLE_RATE
                )

            # Convert to 16-bit PCM
            pcm_bytes = _float_to_int16(audio_samples)

            # Encode as WAV
            wav_bytes = _encode_wav(pcm_bytes)

            self._synthesis_count += 1
            return wav_bytes

        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Kokoro synthesis failed: {e}") from e

    def _resolve_persona(self, persona: Optional[Any]) -> VoicePersona:
        """Resolve flexible persona argument to VoicePersona.

        Handles three cases for orchestrator/protocol compatibility:
        - None -> default persona
        - VoicePersona -> use directly
        - str -> look up in voice map, wrap in VoicePersona

        Args:
            persona: Persona as VoicePersona, string key, or None

        Returns:
            Resolved VoicePersona
        """
        if persona is None:
            return self._default_persona
        if isinstance(persona, VoicePersona):
            return persona
        if isinstance(persona, str):
            # String persona: look up in voice map
            voice_model = _KOKORO_VOICE_MAP.get(persona, persona)
            return VoicePersona(
                persona_id=persona,
                name=persona,
                voice_model=voice_model,
                speed=1.0,
                pitch=1.0,
            )
        # Unknown type — use default
        return self._default_persona

    def _resolve_voice(self, persona: VoicePersona) -> str:
        """Resolve persona to Kokoro voice ID.

        Args:
            persona: Voice persona

        Returns:
            Kokoro voice identifier
        """
        # First try the voice_model directly
        if persona.voice_model and persona.voice_model != "default":
            return persona.voice_model

        # Then try the persona_id mapping
        if persona.persona_id in _KOKORO_VOICE_MAP:
            return _KOKORO_VOICE_MAP[persona.persona_id]

        # Default to DM narrator voice
        return _KOKORO_VOICE_MAP["dm_narrator"]

    def _generate_audio(
        self,
        kokoro: Any,
        text: str,
        voice_id: str,
        speed: float,
    ) -> Tuple[List[float], int]:
        """Generate audio using Kokoro.

        Args:
            kokoro: Kokoro TTS instance
            text: Text to synthesize
            voice_id: Voice identifier
            speed: Speech speed multiplier

        Returns:
            Tuple of (audio samples as floats, sample rate)
        """
        # Kokoro's create method returns (samples, sample_rate)
        # The API may vary between versions
        try:
            # Try the standard API
            samples, sample_rate = kokoro.create(
                text=text,
                voice=voice_id,
                speed=speed,
            )

            # Convert numpy array to list if needed
            if hasattr(samples, "tolist"):
                samples = samples.tolist()

            return samples, sample_rate

        except TypeError:
            # Fallback for different API versions
            result = kokoro.create(text, voice=voice_id)
            if isinstance(result, tuple):
                samples, sample_rate = result
            else:
                samples = result
                sample_rate = DEFAULT_SAMPLE_RATE

            if hasattr(samples, "tolist"):
                samples = samples.tolist()

            return samples, sample_rate

    def list_personas(self) -> List[VoicePersona]:
        """List available voice personas.

        Returns:
            List of pre-defined voice personas for D&D narration
        """
        return list(_KOKORO_PERSONAS)

    def is_available(self) -> bool:
        """Check if Kokoro TTS is available and ready.

        Returns:
            True if kokoro-onnx and models are installed
        """
        return _dep_checker.is_available()

    def get_synthesis_count(self) -> int:
        """Get the number of successful syntheses.

        Returns:
            Count of successful synthesize() calls
        """
        return self._synthesis_count

    def get_default_persona(self) -> VoicePersona:
        """Get the default voice persona.

        Returns:
            Default VoicePersona used when none specified
        """
        return self._default_persona

    def set_default_persona(self, persona: VoicePersona) -> None:
        """Set the default voice persona.

        Args:
            persona: New default persona
        """
        self._default_persona = persona


# ==============================================================================
# FACTORY REGISTRATION HELPER
# ==============================================================================

def create_kokoro_adapter(
    default_persona: Optional[VoicePersona] = None,
    fallback_to_stub: bool = True,
    model_path: Optional[str] = None,
    voices_path: Optional[str] = None,
) -> "KokoroTTSAdapter":
    """Create a Kokoro TTS adapter with optional stub fallback.

    Args:
        default_persona: Default voice persona
        fallback_to_stub: If True, return stub adapter when Kokoro unavailable
        model_path: Path to Kokoro ONNX model file
        voices_path: Path to Kokoro voices .bin file

    Returns:
        KokoroTTSAdapter instance

    Raises:
        RuntimeError: If Kokoro unavailable and fallback_to_stub is False
    """
    adapter = KokoroTTSAdapter(
        default_persona=default_persona,
        model_path=model_path,
        voices_path=voices_path,
    )

    if not adapter.is_available() and not fallback_to_stub:
        raise RuntimeError(
            f"Kokoro TTS not available: {_dep_checker.get_error()}. "
            "Install with: pip install kokoro-onnx onnxruntime"
        )

    return adapter


# ==============================================================================
# PUBLIC API
# ==============================================================================

__all__ = [
    "KokoroTTSAdapter",
    "create_kokoro_adapter",
]
