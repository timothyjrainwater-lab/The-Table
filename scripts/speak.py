#!/usr/bin/env python3
"""Operator signal voice — speak key status changes via TTS.

Usage (from project root):
    python scripts/speak.py "Work order complete"
    python scripts/speak.py --persona dm_narrator "Playtest ready"
    python scripts/speak.py --persona villainous --reference models/voices/signal_reference_george_24k.wav "I will destroy you"
    python scripts/speak.py --volume 0.3 "Tests passing"
    python scripts/speak.py --backend kokoro "Fallback test"
    python scripts/speak.py --list-personas
    echo "=== SIGNAL: REPORT_READY ===\\nWO done." | python scripts/speak.py --signal
    echo "=== SIGNAL: REPORT_READY ===\\nSummary.\\nBody text." | python scripts/speak.py --signal --full

Backend priority:
    1. Chatterbox (GPU, CUDA) — higher quality, emotion control
    2. Kokoro (CPU, ONNX) — fast fallback if no GPU

Voice profile (default): Calm, grounded, neutral-operational.
    Mid-low pitch, clean texture, even cadence, controlled warmth.
    Optimized for sustained analytical listening during long sessions.

Called by the AI co-pilot to voice high-value signals:
    - Work order completion
    - Playtest ready
    - Test failures
    - Operator action required
"""

import argparse
import io
import math
import struct
import sys
import tempfile
import wave
from pathlib import Path
from typing import Optional

# Project root = parent of scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = str(PROJECT_ROOT / "models" / "kokoro" / "kokoro-v1.0.int8.onnx")
VOICES_PATH = str(PROJECT_ROOT / "models" / "kokoro" / "voices-v1.0.bin")

# Default volume: 50% — operator requested half volume
DEFAULT_VOLUME = 0.5

# Add project root to path for imports
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Volume attenuation
# ---------------------------------------------------------------------------

def _attenuate_wav(wav_bytes: bytes, volume: float) -> bytes:
    """Scale WAV audio amplitude by volume factor.

    Args:
        wav_bytes: Input WAV data
        volume: 0.0 (silent) to 1.0 (full volume)

    Returns:
        Volume-adjusted WAV bytes
    """
    if volume >= 1.0:
        return wav_bytes

    buf_in = io.BytesIO(wav_bytes)
    buf_out = io.BytesIO()

    with wave.open(buf_in, "rb") as wf_in:
        params = wf_in.getparams()
        raw = wf_in.readframes(params.nframes)

    if params.sampwidth != 2:
        # Only handle 16-bit PCM
        return wav_bytes

    # Unpack, scale, repack
    n_samples = len(raw) // 2
    samples = struct.unpack(f"<{n_samples}h", raw)
    scaled = [int(max(-32768, min(32767, s * volume))) for s in samples]
    raw_out = struct.pack(f"<{n_samples}h", *scaled)

    with wave.open(buf_out, "wb") as wf_out:
        wf_out.setparams(params)
        wf_out.writeframes(raw_out)

    return buf_out.getvalue()


# ---------------------------------------------------------------------------
# Signal parsing
# ---------------------------------------------------------------------------

def parse_signal(text: str) -> Optional[dict]:
    """Detect === SIGNAL: REPORT_READY === header and extract summary + body.

    Args:
        text: Raw text that may contain a signal block.

    Returns:
        Dict with 'signal_type', 'summary', 'body' if signal found, else None.
    """
    lines = text.strip().split("\n")
    if not lines or "=== SIGNAL:" not in lines[0]:
        return None
    signal_type = lines[0].split("SIGNAL:")[1].split("===")[0].strip()
    # First non-empty line after banner = summary
    summary = ""
    body_lines = []
    found_summary = False
    for line in lines[1:]:
        if not found_summary:
            if line.strip():
                summary = line.strip()
                found_summary = True
        else:
            body_lines.append(line)
    return {
        "signal_type": signal_type,
        "summary": summary,
        "body": "\n".join(body_lines).strip(),
    }


# ---------------------------------------------------------------------------
# Chime generation (pure math — no external audio files)
# ---------------------------------------------------------------------------

def _generate_chime() -> bytes:
    """Generate a two-note ascending herald chime, 16-bit PCM, 24kHz.

    Two clean tones: C5 (523Hz) then E5 (659Hz), each 150ms with
    a 50ms gap. Bright and confident — a herald's bell, not a doorbell.

    Returns WAV bytes ready for playback. No external audio files needed.
    """
    sample_rate = 24000
    note_duration = 0.15
    gap_duration = 0.05
    fade_ms = 0.008  # 8ms attack/release

    def _make_tone(frequency: float) -> list:
        num_samples = int(sample_rate * note_duration)
        tone = []
        for i in range(num_samples):
            t = i / sample_rate
            envelope = 1.0
            if t < fade_ms:
                envelope = t / fade_ms
            elif t > note_duration - fade_ms:
                envelope = (note_duration - t) / fade_ms
            # Add a soft second harmonic for warmth
            value = int(12000 * envelope * (
                math.sin(2 * math.pi * frequency * t)
                + 0.3 * math.sin(2 * math.pi * frequency * 2 * t)
            ))
            tone.append(struct.pack('<h', max(-32768, min(32767, value))))
        return tone

    gap_samples = int(sample_rate * gap_duration)
    gap = [struct.pack('<h', 0)] * gap_samples

    pcm = b''.join(_make_tone(523.25) + gap + _make_tone(659.25))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Backend: Chatterbox (GPU)
# ---------------------------------------------------------------------------

def _speak_chatterbox(text: str, persona: str, reference: Optional[str] = None, exaggeration: Optional[float] = None, speed: Optional[float] = None) -> bytes:
    """Synthesize via Chatterbox TTS (GPU) with persona-driven voice.

    Looks up the persona by ID from the adapter's registry, applies its
    speed/pitch/exaggeration settings, and uses the specified reference audio
    for voice cloning.

    Args:
        text: Text to synthesize
        persona: Persona ID string (e.g. "dm_narrator", "villainous")
        reference: Optional path to reference WAV file. If provided, overrides
                   the persona's default reference audio.
        exaggeration: Optional exaggeration override (0.0-1.0).
        speed: Optional speed override (0.5-2.0).

    Returns WAV bytes, or raises on failure.
    """
    from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
    from aidm.schemas.immersion import VoicePersona

    # Default reference clip (used when no other reference is found)
    default_ref = str(PROJECT_ROOT / "models" / "voices" / "signal_reference_michael_24k.wav")

    adapter = ChatterboxTTSAdapter(
        voices_dir=str(PROJECT_ROOT / "models" / "voices"),
    )

    if not adapter.is_available():
        raise RuntimeError("Chatterbox not available")

    # Resolve persona from adapter registry (handles string lookup)
    resolved = adapter._resolve_persona(persona)

    # Apply reference audio: CLI override > persona field > adapter auto-discovery > default
    if reference:
        ref_path = reference
    elif resolved.reference_audio:
        ref_path = resolved.reference_audio
    else:
        # Try adapter's auto-discovery (looks for {persona_id}.wav in voices_dir)
        discovered = adapter._resolve_reference_audio(resolved)
        ref_path = discovered if discovered else default_ref

    # Build effective persona with resolved reference and CLI overrides
    effective = VoicePersona(
        persona_id=resolved.persona_id,
        name=resolved.name,
        voice_model=resolved.voice_model,
        speed=speed if speed is not None else resolved.speed,
        pitch=resolved.pitch,
        exaggeration=exaggeration if exaggeration is not None else resolved.exaggeration,
        reference_audio=ref_path,
    )

    # Original tier: natural-sounding, respects voice cloning + exaggeration
    return adapter.synthesize(text, persona=effective, force_turbo=False)


# ---------------------------------------------------------------------------
# Backend: Kokoro (CPU fallback)
# ---------------------------------------------------------------------------

def _speak_kokoro(text: str, persona: str) -> bytes:
    """Synthesize via Kokoro TTS (CPU).

    Returns WAV bytes, or raises on failure.
    """
    from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter

    adapter = KokoroTTSAdapter(
        model_path=MODEL_PATH,
        voices_path=VOICES_PATH,
    )

    if not adapter.is_available():
        raise RuntimeError("Kokoro not available")

    return adapter.synthesize(text, persona)


# ---------------------------------------------------------------------------
# Main speak function
# ---------------------------------------------------------------------------

def speak(text: str, persona: str = "dm_narrator", volume: float = DEFAULT_VOLUME, backend: str = "auto", reference: Optional[str] = None, exaggeration: Optional[float] = None, speed: Optional[float] = None) -> bool:
    """Synthesize and play text.

    Args:
        text: Text to speak
        persona: Voice persona key
        volume: Volume level 0.0-1.0 (default 0.5)
        backend: "auto", "chatterbox", or "kokoro"
        reference: Optional path to reference WAV for voice cloning
        exaggeration: Optional exaggeration override (0.0-1.0)
        speed: Optional speed override (0.5-2.0)

    Returns:
        True if audio played successfully
    """
    wav_bytes = None

    # Try backends in priority order
    if backend in ("auto", "chatterbox"):
        try:
            wav_bytes = _speak_chatterbox(text, persona, reference=reference, exaggeration=exaggeration, speed=speed)
        except Exception as e:
            if backend == "chatterbox":
                print(f"[speak] Chatterbox failed: {e}", file=sys.stderr)
                return False
            # auto mode: fall through to Kokoro

    if wav_bytes is None and backend in ("auto", "kokoro"):
        try:
            wav_bytes = _speak_kokoro(text, persona)
        except Exception as e:
            print(f"[speak] TTS failed: {e}", file=sys.stderr)
            return False

    if wav_bytes is None:
        print("[speak] No TTS backend available — printing to stdout", file=sys.stderr)
        print(text)
        return False

    # Apply volume
    if volume < 1.0:
        wav_bytes = _attenuate_wav(wav_bytes, volume)

    return _play_wav(wav_bytes)


# ---------------------------------------------------------------------------
# Playback
# ---------------------------------------------------------------------------

def _play_wav(wav_bytes: bytes) -> bool:
    """Play WAV bytes through system audio."""
    # Windows: winsound (built-in)
    try:
        import winsound
        winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)
        return True
    except ImportError:
        pass
    except Exception as e:
        print(f"[speak] winsound failed: {e}", file=sys.stderr)

    # Fallback: temp file + platform command
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(wav_bytes)
            tmp_path = f.name

        import subprocess
        import platform

        system = platform.system()
        if system == "Darwin":
            subprocess.run(["afplay", tmp_path], check=True)
        elif system == "Linux":
            subprocess.run(["aplay", tmp_path], check=True)
        else:
            subprocess.run(["start", "", tmp_path], shell=True, check=True)

        Path(tmp_path).unlink(missing_ok=True)
        return True
    except Exception as e:
        print(f"[speak] Playback failed: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def list_personas() -> None:
    """Print available voice personas from both backends."""
    print("Chatterbox (GPU):")
    try:
        from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
        adapter = ChatterboxTTSAdapter()
        avail = adapter.is_available()
        for p in adapter.list_personas():
            print(f"  {p.persona_id:20s}  {p.name}")
        print(f"  Status: {'AVAILABLE' if avail else 'NOT AVAILABLE (no CUDA)'}")
    except Exception as e:
        print(f"  Error: {e}")

    print()
    print("Kokoro (CPU fallback):")
    try:
        from aidm.immersion.kokoro_tts_adapter import KokoroTTSAdapter
        adapter = KokoroTTSAdapter(model_path=MODEL_PATH, voices_path=VOICES_PATH)
        avail = adapter.is_available()
        for p in adapter.list_personas():
            print(f"  {p.persona_id:20s}  {p.name}  (voice: {p.voice_model})")
        print(f"  Status: {'AVAILABLE' if avail else 'NOT AVAILABLE'}")
    except Exception as e:
        print(f"  Error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Speak operator signals via TTS (Chatterbox GPU / Kokoro CPU)"
    )
    parser.add_argument("text", nargs="?", help="Text to speak")
    parser.add_argument(
        "--persona", default="dm_narrator",
        help="Voice persona (default: dm_narrator)"
    )
    parser.add_argument(
        "--volume", type=float, default=DEFAULT_VOLUME,
        help=f"Volume 0.0-1.0 (default: {DEFAULT_VOLUME})"
    )
    parser.add_argument(
        "--backend", choices=["auto", "chatterbox", "kokoro"], default="auto",
        help="TTS backend (default: auto)"
    )
    parser.add_argument(
        "--list-personas", action="store_true",
        help="List available voice personas"
    )
    parser.add_argument(
        "--signal", action="store_true",
        help="Parse stdin for signal block (chime + spoken summary)"
    )
    parser.add_argument(
        "--full", action="store_true",
        help="With --signal, also speak full body text (chunked at sentence boundaries)"
    )
    parser.add_argument(
        "--reference",
        help="Path to reference WAV file for voice cloning (overrides persona default)"
    )
    parser.add_argument(
        "--exaggeration", type=float,
        help="Emotional exaggeration 0.0-1.0 (overrides persona default). Higher = more expressive."
    )
    parser.add_argument(
        "--speed", type=float,
        help="Speech speed 0.5-2.0 (overrides persona default). Lower = slower."
    )
    args = parser.parse_args()

    if args.list_personas:
        list_personas()
        return

    # Signal mode: parse stdin for signal block
    if args.signal:
        text = sys.stdin.read()
        result = parse_signal(text)
        if result is None:
            sys.exit(0)  # No signal found — silent exit
        # Play chime
        chime = _generate_chime()
        if args.volume < 1.0:
            chime = _attenuate_wav(chime, args.volume)
        _play_wav(chime)
        # Speak summary (Chatterbox only — no Kokoro fallback for signal voice)
        speak(result["summary"], args.persona, args.volume, backend="chatterbox", reference=args.reference, exaggeration=args.exaggeration, speed=args.speed)
        # Optionally speak full body (adapter handles chunking internally)
        if args.full and result["body"]:
            speak(result["body"], args.persona, args.volume, backend="chatterbox", reference=args.reference, exaggeration=args.exaggeration, speed=args.speed)
        sys.exit(0)

    if not args.text:
        text = sys.stdin.read().strip()
        if not text:
            parser.error("No text provided. Pass as argument or pipe to stdin.")
    else:
        text = args.text

    ok = speak(text, args.persona, args.volume, args.backend, reference=args.reference, exaggeration=args.exaggeration, speed=args.speed)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
