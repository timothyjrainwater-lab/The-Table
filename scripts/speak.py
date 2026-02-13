#!/usr/bin/env python3
"""Operator signal voice — speak key status changes via TTS.

Usage (from project root):
    python scripts/speak.py "Work order complete"
    python scripts/speak.py --persona dm_narrator "Playtest ready"
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
    """Generate 440Hz sine wave chime, 200ms, 16-bit PCM, 24kHz.

    Returns WAV bytes ready for playback. No external files needed.
    """
    sample_rate = 24000
    duration = 0.2
    frequency = 440
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        # Apply fade envelope (10ms attack, 10ms release)
        envelope = 1.0
        if t < 0.01:
            envelope = t / 0.01
        elif t > duration - 0.01:
            envelope = (duration - t) / 0.01
        value = int(16000 * envelope * math.sin(2 * math.pi * frequency * t))
        samples.append(struct.pack('<h', max(-32768, min(32767, value))))
    pcm = b''.join(samples)

    # Build WAV file in memory
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Sentence-boundary chunking (TD-023 fix)
# ---------------------------------------------------------------------------

def _chunk_by_sentence(text: str, max_words: int = 55) -> list:
    """Split text at sentence boundaries to stay under Chatterbox generation ceiling.

    Chatterbox has a ~60-80 word generation ceiling. Text exceeding this limit
    is split at sentence boundaries ('. ') so each chunk can be generated and
    played sequentially without mid-sentence truncation.

    Args:
        text: Input text to chunk.
        max_words: Maximum words per chunk (default 55, conservative margin).

    Returns:
        List of text chunks, each ending with a period.
    """
    sentences = text.replace(".\n", ". ").split(". ")
    chunks = []
    current = []
    current_words = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        word_count = len(sentence.split())
        if current_words + word_count > max_words and current:
            chunks.append(". ".join(current) + ".")
            current = [sentence]
            current_words = word_count
        else:
            current.append(sentence)
            current_words += word_count
    if current:
        chunks.append(". ".join(current) + ".")
    return chunks if chunks else [text]


# ---------------------------------------------------------------------------
# Backend: Chatterbox (GPU)
# ---------------------------------------------------------------------------

def _speak_chatterbox(text: str, persona: str) -> bytes:
    """Synthesize via Chatterbox TTS (GPU) with voice-cloned signal voice.

    Voice pipeline: Kokoro am_adam generates a reference clip (models/voices/signal_reference.wav),
    then Chatterbox clones that voice for all signal output. This gives us explicit male voice
    control with GPU-quality synthesis.

    Returns WAV bytes, or raises on failure.
    """
    from aidm.immersion.chatterbox_tts_adapter import ChatterboxTTSAdapter
    from aidm.schemas.immersion import VoicePersona

    # Reference clip: generated by Kokoro am_michael FULL model at native 24kHz
    # No downsample — matches Chatterbox's expected mel spectrogram input exactly.
    # Pipeline: Kokoro fp32 24kHz -> Chatterbox voice clone -> winsound
    ref_clip = str(PROJECT_ROOT / "models" / "voices" / "signal_reference_michael_24k.wav")

    # Voice Profile: Arbor (Chat Readback Mode)
    # Calm, grounded, neutral-operational. Mid-range, low-variance.
    # Optimized for sustained cognitive listening during long sessions.
    # Spec: steady pacing, limited emotional modulation, clean articulation,
    #        no theatrical rise/fall, mid-energy neutrality.
    _ARBOR = VoicePersona(
        persona_id="arbor",
        name="Arbor",
        voice_model="chatterbox",
        speed=0.88,
        pitch=1.0,
        exaggeration=0.15,
        reference_audio=ref_clip,
    )

    adapter = ChatterboxTTSAdapter()

    if not adapter.is_available():
        raise RuntimeError("Chatterbox not available")

    # Original tier: natural-sounding, respects voice cloning + exaggeration
    return adapter.synthesize(text, persona=_ARBOR, force_turbo=False)


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

def speak(text: str, persona: str = "dm_narrator", volume: float = DEFAULT_VOLUME, backend: str = "auto") -> bool:
    """Synthesize and play text.

    Args:
        text: Text to speak
        persona: Voice persona key
        volume: Volume level 0.0-1.0 (default 0.5)
        backend: "auto", "chatterbox", or "kokoro"

    Returns:
        True if audio played successfully
    """
    wav_bytes = None

    # Try backends in priority order
    if backend in ("auto", "chatterbox"):
        try:
            wav_bytes = _speak_chatterbox(text, persona)
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
        print("[speak] No TTS backend available", file=sys.stderr)
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
        speak(result["summary"], args.persona, args.volume, backend="chatterbox")
        # Optionally speak full body, chunked at sentence boundaries
        if args.full and result["body"]:
            chunks = _chunk_by_sentence(result["body"])
            for chunk in chunks:
                speak(chunk, args.persona, args.volume, backend="chatterbox")
        sys.exit(0)

    if not args.text:
        text = sys.stdin.read().strip()
        if not text:
            parser.error("No text provided. Pass as argument or pipe to stdin.")
    else:
        text = args.text

    ok = speak(text, args.persona, args.volume, args.backend)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
