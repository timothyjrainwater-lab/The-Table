"""Chatterbox TTS Adapter — GPU-accelerated voice-cloning TTS.

Two-tier architecture:
- Turbo: Fast synthesis for combat narration / short callouts (sub-1s short lines)
- Original: Emotion-rich synthesis for scenes, monologues, rest narration

Both tiers share voice cloning via reference audio (audio_prompt_path),
so character voices stay consistent across tiers.

Requires:
- chatterbox-tts >= 0.1.6
- torch with CUDA support
- GPU with >= 6GB VRAM (RTX 3080 Ti tested)

Atmospheric only — TTS output is never mechanical authority.
"""

import io
import logging
import os
import wave
from typing import Any, Dict, List, Optional

from aidm.immersion.tts_chunking import chunk_by_sentence
from aidm.schemas.immersion import VoicePersona

logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTS
# ==============================================================================

SAMPLE_RATE = 24000  # Chatterbox native output rate
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit PCM

# Tier selection: lines shorter than this word count use Turbo
_TURBO_WORD_THRESHOLD = 20

# ==============================================================================
# VOICE PERSONA DEFINITIONS
# ==============================================================================

# D&D voice personas — reference_audio paths are relative to voices_dir
_CHATTERBOX_PERSONAS: List[VoicePersona] = [
    VoicePersona(
        persona_id="dm_narrator",
        name="Dungeon Master",
        voice_model="chatterbox",
        speed=1.0,
        pitch=1.0,
        exaggeration=0.5,
    ),
    VoicePersona(
        persona_id="dm_narrator_male",
        name="Dungeon Master (Male)",
        voice_model="chatterbox",
        speed=1.0,
        pitch=0.85,
        exaggeration=0.5,
    ),
    VoicePersona(
        persona_id="npc_male",
        name="NPC Male",
        voice_model="chatterbox",
        speed=1.0,
        pitch=0.9,
        exaggeration=0.4,
    ),
    VoicePersona(
        persona_id="npc_female",
        name="NPC Female",
        voice_model="chatterbox",
        speed=1.0,
        pitch=1.1,
        exaggeration=0.4,
    ),
    VoicePersona(
        persona_id="npc_elderly",
        name="NPC Elderly",
        voice_model="chatterbox",
        speed=0.85,
        pitch=0.95,
        exaggeration=0.3,
    ),
    VoicePersona(
        persona_id="npc_young",
        name="NPC Young",
        voice_model="chatterbox",
        speed=1.1,
        pitch=1.15,
        exaggeration=0.5,
    ),
    VoicePersona(
        persona_id="villainous",
        name="Villain",
        voice_model="chatterbox",
        speed=0.9,
        pitch=0.8,
        exaggeration=0.7,
    ),
    VoicePersona(
        persona_id="heroic",
        name="Hero",
        voice_model="chatterbox",
        speed=1.0,
        pitch=1.0,
        exaggeration=0.6,
    ),
]

_DEFAULT_PERSONA = _CHATTERBOX_PERSONAS[0]


# ==============================================================================
# LAZY LOADER
# ==============================================================================

class _ChatterboxLoader:
    """Lazy loader for Chatterbox TTS models.

    Loads Original and/or Turbo on first use.
    Avoids import-time GPU allocation.
    """

    def __init__(
        self,
        device: str = "cuda",
        turbo_model_dir: Optional[str] = None,
        original_model_dir: Optional[str] = None,
    ) -> None:
        self._device = device
        self._turbo_model_dir = turbo_model_dir
        self._original_model_dir = original_model_dir
        self._turbo: Any = None
        self._original: Any = None
        self._available: Optional[bool] = None
        self._error_message: str = ""

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            import torch  # noqa: F401
            from chatterbox.tts import ChatterboxTTS  # noqa: F401
            if not torch.cuda.is_available():
                self._available = False
                self._error_message = "CUDA not available"
                return False
            self._available = True
        except ImportError as e:
            self._available = False
            self._error_message = str(e)
        return self._available

    def get_turbo(self) -> Any:
        if not self.is_available():
            raise RuntimeError(
                f"Chatterbox TTS not available: {self._error_message}"
            )
        if self._turbo is None:
            from chatterbox.tts_turbo import ChatterboxTurboTTS
            if self._turbo_model_dir and os.path.isdir(self._turbo_model_dir):
                self._turbo = ChatterboxTurboTTS.from_local(
                    self._turbo_model_dir, device=self._device
                )
            else:
                self._turbo = ChatterboxTurboTTS.from_pretrained(
                    device=self._device
                )
            logger.info("Chatterbox Turbo loaded on %s", self._device)
        return self._turbo

    def get_original(self) -> Any:
        if not self.is_available():
            raise RuntimeError(
                f"Chatterbox TTS not available: {self._error_message}"
            )
        if self._original is None:
            from chatterbox.tts import ChatterboxTTS
            if self._original_model_dir and os.path.isdir(self._original_model_dir):
                self._original = ChatterboxTTS.from_local(
                    self._original_model_dir, device=self._device
                )
            else:
                self._original = ChatterboxTTS.from_pretrained(
                    device=self._device
                )
            logger.info("Chatterbox Original loaded on %s", self._device)
        return self._original

    def get_error(self) -> str:
        return self._error_message


# Global dependency checker (no model loading)
_dep_checker = _ChatterboxLoader()


# ==============================================================================
# WAV ENCODING
# ==============================================================================

def _tensor_to_wav(audio_tensor: Any, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Convert a torch audio tensor to WAV bytes.

    Args:
        audio_tensor: torch.Tensor of shape (1, N) or (N,)
        sample_rate: Output sample rate

    Returns:
        WAV-encoded bytes (mono 16-bit PCM)
    """
    import torch

    if audio_tensor.dim() == 2:
        audio_tensor = audio_tensor.squeeze(0)

    # Clamp and convert to int16
    audio_tensor = audio_tensor.clamp(-1.0, 1.0)
    int16 = (audio_tensor * 32767).to(torch.int16).cpu().numpy()

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(sample_rate)
        wf.writeframes(int16.tobytes())
    return buf.getvalue()


# ==============================================================================
# CHATTERBOX TTS ADAPTER
# ==============================================================================

class ChatterboxTTSAdapter:
    """TTS adapter using Chatterbox with two-tier architecture.

    Tier selection:
    - Short text (< TURBO_WORD_THRESHOLD words): Turbo (speed priority)
    - Long text or persona with exaggeration > 0: Original (emotion priority)
    - force_turbo=True on synthesize(): always use Turbo

    Voice cloning:
    - VoicePersona.reference_audio points to a WAV file
    - Both tiers use audio_prompt_path for voice cloning
    - Reference clips should be 5-15 seconds of clean speech

    Implements the TTSAdapter protocol:
    - synthesize(text, persona) -> WAV bytes
    - list_personas() -> available voice personas
    - is_available() -> True if backend ready
    """

    def __init__(
        self,
        default_persona: Optional[VoicePersona] = None,
        device: str = "cuda",
        voices_dir: Optional[str] = None,
        turbo_model_dir: Optional[str] = None,
        original_model_dir: Optional[str] = None,
        turbo_word_threshold: int = _TURBO_WORD_THRESHOLD,
    ) -> None:
        self._default_persona = default_persona or _DEFAULT_PERSONA
        self._voices_dir = voices_dir
        self._turbo_word_threshold = turbo_word_threshold
        self._synthesis_count: int = 0
        self._loader = _ChatterboxLoader(
            device=device,
            turbo_model_dir=turbo_model_dir,
            original_model_dir=original_model_dir,
        )

    def synthesize(
        self,
        text: str,
        persona: Optional[Any] = None,
        force_turbo: bool = False,
    ) -> bytes:
        """Synthesize text to WAV audio bytes.

        Auto-chunks input at sentence boundaries (max 55 words per chunk)
        to avoid Chatterbox's ~60-80 word generation ceiling, then
        concatenates the WAV output into a single result.

        Auto-selects Turbo or Original based on text length and persona.

        Args:
            text: Text to synthesize
            persona: VoicePersona, str (persona_id lookup), or None (default)
            force_turbo: Force Turbo tier regardless of text length

        Returns:
            WAV audio bytes (24kHz mono 16-bit PCM)

        Raises:
            RuntimeError: If Chatterbox not available
        """
        if not text or not text.strip():
            return _tensor_to_empty_wav()

        effective_persona = self._resolve_persona(persona)
        ref_audio = self._resolve_reference_audio(effective_persona)

        chunks = chunk_by_sentence(text)
        wav_parts: List[bytes] = []

        try:
            for chunk in chunks:
                use_turbo = self._select_tier(chunk, effective_persona, force_turbo)
                if use_turbo:
                    audio_tensor = self._synthesize_turbo(chunk, ref_audio)
                else:
                    audio_tensor = self._synthesize_original(
                        chunk, ref_audio, effective_persona.exaggeration
                    )
                wav_parts.append(_tensor_to_wav(audio_tensor, SAMPLE_RATE))

            wav_bytes = _concatenate_wav(wav_parts) if len(wav_parts) > 1 else wav_parts[0]
            self._synthesis_count += 1
            return wav_bytes

        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Chatterbox synthesis failed: {e}") from e

    def _select_tier(
        self,
        text: str,
        persona: VoicePersona,
        force_turbo: bool,
    ) -> bool:
        """Decide whether to use Turbo or Original.

        Returns True for Turbo, False for Original.
        """
        if force_turbo:
            return True

        word_count = len(text.split())
        wants_emotion = persona.exaggeration > 0.1

        # Short text without heavy emotion → Turbo for speed
        if word_count <= self._turbo_word_threshold and not wants_emotion:
            return True

        # Long text or emotion-heavy → Original
        return False

    def _synthesize_turbo(
        self,
        text: str,
        ref_audio: Optional[str],
    ) -> Any:
        """Synthesize using Chatterbox Turbo (fast, no emotion control)."""
        model = self._loader.get_turbo()
        kwargs: Dict[str, Any] = {"text": text}
        if ref_audio:
            kwargs["audio_prompt_path"] = ref_audio
        return model.generate(**kwargs)

    def _synthesize_original(
        self,
        text: str,
        ref_audio: Optional[str],
        exaggeration: float,
    ) -> Any:
        """Synthesize using Chatterbox Original (emotion + voice cloning)."""
        model = self._loader.get_original()
        kwargs: Dict[str, Any] = {
            "text": text,
            "exaggeration": exaggeration,
            "cfg_weight": 0.5,
        }
        if ref_audio:
            kwargs["audio_prompt_path"] = ref_audio
        return model.generate(**kwargs)

    def _resolve_persona(self, persona: Optional[Any]) -> VoicePersona:
        """Resolve flexible persona argument to VoicePersona."""
        if persona is None:
            return self._default_persona
        if isinstance(persona, VoicePersona):
            return persona
        if isinstance(persona, str):
            for p in _CHATTERBOX_PERSONAS:
                if p.persona_id == persona:
                    return p
            return VoicePersona(
                persona_id=persona,
                name=persona,
                voice_model="chatterbox",
                speed=1.0,
                pitch=1.0,
            )
        return self._default_persona

    def _resolve_reference_audio(self, persona: VoicePersona) -> Optional[str]:
        """Resolve persona to a reference audio file path.

        Checks persona.reference_audio first, then looks in voices_dir.
        Returns None if no reference audio available (uses default voice).
        """
        # Direct path on persona
        if persona.reference_audio:
            path = persona.reference_audio
            if not os.path.isabs(path) and self._voices_dir:
                path = os.path.join(self._voices_dir, path)
            if os.path.isfile(path):
                return path
            logger.warning(
                "Reference audio not found: %s (persona: %s)",
                path, persona.persona_id,
            )

        # Look in voices_dir by persona_id
        if self._voices_dir:
            for ext in (".wav", ".flac", ".mp3"):
                candidate = os.path.join(
                    self._voices_dir, f"{persona.persona_id}{ext}"
                )
                if os.path.isfile(candidate):
                    return candidate

        return None

    def list_personas(self) -> List[VoicePersona]:
        return list(_CHATTERBOX_PERSONAS)

    def is_available(self) -> bool:
        return _dep_checker.is_available()

    def get_synthesis_count(self) -> int:
        return self._synthesis_count

    def get_default_persona(self) -> VoicePersona:
        return self._default_persona

    def set_default_persona(self, persona: VoicePersona) -> None:
        self._default_persona = persona


# ==============================================================================
# HELPERS
# ==============================================================================

def _tensor_to_empty_wav() -> bytes:
    """Return a valid but empty WAV file."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"")
    return buf.getvalue()


def _concatenate_wav(wav_parts: List[bytes]) -> bytes:
    """Concatenate multiple WAV byte segments into a single WAV file.

    All parts must share the same channel count, sample width, and frame rate.
    The output has a single correct WAV header followed by all PCM data.

    Args:
        wav_parts: List of WAV-encoded byte strings.

    Returns:
        Single concatenated WAV byte string.
    """
    if not wav_parts:
        return _tensor_to_empty_wav()
    if len(wav_parts) == 1:
        return wav_parts[0]

    # Read params from first part
    first_buf = io.BytesIO(wav_parts[0])
    with wave.open(first_buf, "rb") as wf:
        params = wf.getparams()

    # Collect all raw PCM frames
    all_frames: list[bytes] = []
    for part in wav_parts:
        buf = io.BytesIO(part)
        with wave.open(buf, "rb") as wf:
            all_frames.append(wf.readframes(wf.getnframes()))

    # Write single WAV with combined frames
    out_buf = io.BytesIO()
    with wave.open(out_buf, "wb") as wf:
        wf.setnchannels(params.nchannels)
        wf.setsampwidth(params.sampwidth)
        wf.setframerate(params.framerate)
        wf.writeframes(b"".join(all_frames))
    return out_buf.getvalue()


# ==============================================================================
# FACTORY
# ==============================================================================

def create_chatterbox_adapter(
    default_persona: Optional[VoicePersona] = None,
    device: str = "cuda",
    voices_dir: Optional[str] = None,
    turbo_model_dir: Optional[str] = None,
    original_model_dir: Optional[str] = None,
    fallback_to_stub: bool = True,
) -> "ChatterboxTTSAdapter":
    """Create a Chatterbox TTS adapter.

    Args:
        default_persona: Default voice persona
        device: Torch device (e.g., "cuda", "cpu")
        voices_dir: Directory containing reference audio WAV files
        turbo_model_dir: Local path to Turbo model weights
        original_model_dir: Local path to Original model weights
        fallback_to_stub: If True, return adapter even when unavailable

    Returns:
        ChatterboxTTSAdapter instance

    Raises:
        RuntimeError: If unavailable and fallback_to_stub is False
    """
    adapter = ChatterboxTTSAdapter(
        default_persona=default_persona,
        device=device,
        voices_dir=voices_dir,
        turbo_model_dir=turbo_model_dir,
        original_model_dir=original_model_dir,
    )

    if not adapter.is_available() and not fallback_to_stub:
        raise RuntimeError(
            f"Chatterbox TTS not available: {_dep_checker.get_error()}. "
            "Install with: pip install chatterbox-tts"
        )

    return adapter


# ==============================================================================
# PUBLIC API
# ==============================================================================

__all__ = [
    "ChatterboxTTSAdapter",
    "create_chatterbox_adapter",
]
