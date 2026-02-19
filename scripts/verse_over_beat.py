#!/usr/bin/env python3
"""Spoken Verse Over Beat — MVP vocal track generator.

Takes lyrics + instrumental beat, synthesizes spoken-word vocals via
Chatterbox TTS, and mixes them into a single output track.

This is the E-009 MVP path: "spoken verse + instrumental bed."
True singing synthesis is deferred to a future phase.

Usage:
    python scripts/verse_over_beat.py \
        --lyrics "path/to/lyrics.txt" \
        --beat "path/to/beat.mp3" \
        --out "output/track.wav" \
        --voice heroic \
        --exaggeration 0.7

    # Or pass lyrics inline:
    python scripts/verse_over_beat.py \
        --lyrics-text "Seven Wisdoms, no regret" \
        --beat "path/to/beat.mp3" \
        --out "output/track.wav"

Requires:
    - chatterbox-tts (GPU)
    - pydub (for audio mixing)
    - ffmpeg or libav (for MP3 decoding via pydub)
"""

import argparse
import io
import os
import sys
import wave
from pathlib import Path
from typing import List, Optional

# Point pydub at the imageio-ffmpeg binary (avoids needing ffmpeg on PATH)
try:
    import imageio_ffmpeg
    os.environ["PATH"] = str(Path(imageio_ffmpeg.get_ffmpeg_exe()).parent) + os.pathsep + os.environ.get("PATH", "")
except ImportError:
    pass  # Fall back to system ffmpeg

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VOICES_DIR = PROJECT_ROOT / "models" / "voices"
OUTPUT_DIR = PROJECT_ROOT / "output" / "verse_tracks"

# Chatterbox settings
SAMPLE_RATE = 24000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit PCM

# Mix settings
VOCAL_GAIN_DB = 2.0      # Boost vocals slightly over beat
BEAT_GAIN_DB = -4.0       # Duck the beat behind vocals
LEAD_IN_MS = 2000         # Silence before vocals start (let the beat breathe)
VERSE_GAP_MS = 800        # Gap between verse sections
LINE_GAP_MS = 150         # Small gap between lines within a verse


def parse_lyrics(text: str) -> List[dict]:
    """Parse lyrics text into structured sections.

    Recognizes section headers like **Verse 1:**, **Hook:**, **Outro:**
    and groups lines under them. Lines within a section are synthesized
    individually then concatenated with small gaps.

    Returns list of dicts: {"section": str, "lines": [str]}
    """
    sections = []
    current_section = {"section": "intro", "lines": []}

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # Detect section headers: **Verse 1:** or **Hook:** etc.
        if line.startswith("**") and line.endswith("**"):
            header = line.strip("*").strip().rstrip(":")
            if current_section["lines"]:
                sections.append(current_section)
            current_section = {"section": header, "lines": []}
        elif line.startswith("---"):
            # Markdown separator — treat as section break
            if current_section["lines"]:
                sections.append(current_section)
            current_section = {"section": "break", "lines": []}
        else:
            current_section["lines"].append(line)

    if current_section["lines"]:
        sections.append(current_section)

    return sections


def synthesize_line(
    text: str,
    model: object,
    ref_audio: Optional[str],
    exaggeration: float = 0.6,
) -> bytes:
    """Synthesize a single line of lyrics to WAV bytes via Chatterbox Original."""
    import torch

    kwargs = {
        "text": text,
        "exaggeration": exaggeration,
        "cfg_weight": 0.5,
    }
    if ref_audio:
        kwargs["audio_prompt_path"] = ref_audio

    audio_tensor = model.generate(**kwargs)

    # Convert tensor to WAV bytes
    if audio_tensor.dim() == 2:
        audio_tensor = audio_tensor.squeeze(0)
    audio_tensor = audio_tensor.clamp(-1.0, 1.0)
    int16 = (audio_tensor * 32767).to(torch.int16).cpu().numpy()

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(int16.tobytes())
    return buf.getvalue()


def make_silence(duration_ms: int) -> "AudioSegment":
    """Create a silent AudioSegment."""
    from pydub import AudioSegment
    return AudioSegment.silent(duration=duration_ms, frame_rate=SAMPLE_RATE)


def wav_bytes_to_segment(wav_bytes: bytes) -> "AudioSegment":
    """Convert WAV bytes to a pydub AudioSegment."""
    from pydub import AudioSegment
    return AudioSegment.from_wav(io.BytesIO(wav_bytes))


def build_vocal_track(
    sections: List[dict],
    model: object,
    ref_audio: Optional[str],
    exaggeration: float,
    line_gap_ms: int = LINE_GAP_MS,
    verse_gap_ms: int = VERSE_GAP_MS,
) -> "AudioSegment":
    """Synthesize all lyrics sections into a single vocal AudioSegment."""
    from pydub import AudioSegment

    vocal_parts = []
    total_lines = sum(len(s["lines"]) for s in sections)
    done = 0

    for i, section in enumerate(sections):
        section_name = section["section"]
        print(f"\n  [{section_name}]")

        for line in section["lines"]:
            done += 1
            print(f"    ({done}/{total_lines}) \"{line[:50]}{'...' if len(line) > 50 else ''}\"", flush=True)

            wav_bytes = synthesize_line(line, model, ref_audio, exaggeration)
            segment = wav_bytes_to_segment(wav_bytes)
            vocal_parts.append(segment)
            vocal_parts.append(make_silence(line_gap_ms))

        # Gap between sections
        if i < len(sections) - 1:
            vocal_parts.append(make_silence(verse_gap_ms))

    # Concatenate all parts
    if not vocal_parts:
        return AudioSegment.silent(duration=1000, frame_rate=SAMPLE_RATE)

    track = vocal_parts[0]
    for part in vocal_parts[1:]:
        track = track + part

    return track


def mix_vocal_over_beat(
    vocal: "AudioSegment",
    beat_path: str,
    lead_in_ms: int = LEAD_IN_MS,
    vocal_gain_db: float = VOCAL_GAIN_DB,
    beat_gain_db: float = BEAT_GAIN_DB,
) -> "AudioSegment":
    """Mix vocal track over instrumental beat.

    The beat plays from the start. Vocals are overlaid after lead_in_ms.
    If vocals are longer than the beat, the beat loops.
    """
    from pydub import AudioSegment

    # Load the beat — convert non-WAV via ffmpeg first (pydub needs ffprobe for MP3)
    ext = Path(beat_path).suffix.lower()
    if ext == ".wav":
        beat = AudioSegment.from_wav(beat_path)
    else:
        # Convert to temp WAV via ffmpeg (works without ffprobe)
        import subprocess
        try:
            import imageio_ffmpeg
            ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            ffmpeg_bin = "ffmpeg"
        tmp_wav = str(Path(beat_path).parent / "_beat_tmp.wav")
        subprocess.run(
            [ffmpeg_bin, "-y", "-i", beat_path, "-ar", str(SAMPLE_RATE), "-ac", "1", tmp_wav],
            capture_output=True, check=True,
        )
        beat = AudioSegment.from_wav(tmp_wav)
        os.remove(tmp_wav)

    # Resample vocal to match beat if needed (pydub handles this in overlay)
    total_needed_ms = lead_in_ms + len(vocal) + 2000  # 2s tail

    # Loop beat if needed
    if len(beat) < total_needed_ms:
        loops_needed = (total_needed_ms // len(beat)) + 1
        beat = beat * loops_needed

    # Trim beat to needed length
    beat = beat[:total_needed_ms]

    # Apply gain adjustments
    beat = beat + beat_gain_db
    vocal = vocal + vocal_gain_db

    # Overlay vocals onto beat
    mixed = beat.overlay(vocal, position=lead_in_ms)

    return mixed


def resolve_voice_ref(voice_id: str) -> Optional[str]:
    """Resolve a voice persona ID to its reference audio path."""
    # Direct file
    for ext in (".wav", ".flac", ".mp3"):
        candidate = VOICES_DIR / f"{voice_id}{ext}"
        if candidate.is_file():
            return str(candidate)

    # Piper reference
    candidate = VOICES_DIR / f"piper_ref_{voice_id}.wav"
    if candidate.is_file():
        return str(candidate)

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Spoken Verse Over Beat — MVP vocal track generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--lyrics", help="Path to lyrics text file")
    parser.add_argument("--lyrics-text", help="Inline lyrics text")
    parser.add_argument("--beat", required=True, help="Path to instrumental beat (MP3/WAV/OGG)")
    parser.add_argument("--out", help="Output file path (default: output/verse_tracks/track.wav)")
    parser.add_argument(
        "--voice", default="heroic",
        help="Voice persona ID for synthesis (default: heroic)",
    )
    parser.add_argument(
        "--exaggeration", type=float, default=0.65,
        help="Chatterbox exaggeration level 0.0-1.0 (default: 0.65)",
    )
    parser.add_argument(
        "--lead-in", type=int, default=LEAD_IN_MS,
        help=f"Milliseconds of beat before vocals start (default: {LEAD_IN_MS})",
    )
    parser.add_argument(
        "--vocal-gain", type=float, default=VOCAL_GAIN_DB,
        help=f"Vocal gain in dB (default: {VOCAL_GAIN_DB})",
    )
    parser.add_argument(
        "--beat-gain", type=float, default=BEAT_GAIN_DB,
        help=f"Beat gain in dB (default: {BEAT_GAIN_DB})",
    )
    parser.add_argument(
        "--vocals-only", action="store_true",
        help="Output vocals only (no beat mixing)",
    )
    parser.add_argument(
        "--format", choices=["wav", "mp3"], default="wav",
        help="Output format (default: wav)",
    )

    args = parser.parse_args()

    # Get lyrics
    if args.lyrics:
        lyrics_text = Path(args.lyrics).read_text(encoding="utf-8")
    elif args.lyrics_text:
        lyrics_text = args.lyrics_text
    else:
        print("Error: provide --lyrics (file) or --lyrics-text (inline)", file=sys.stderr)
        sys.exit(1)

    # Parse lyrics into sections
    sections = parse_lyrics(lyrics_text)
    total_lines = sum(len(s["lines"]) for s in sections)
    print(f"\n{'='*50}")
    print(f"  VERSE OVER BEAT — MVP v0")
    print(f"  Sections: {len(sections)}")
    print(f"  Lines: {total_lines}")
    print(f"  Voice: {args.voice}")
    print(f"  Exaggeration: {args.exaggeration}")
    print(f"{'='*50}")

    # Resolve voice reference
    ref_audio = resolve_voice_ref(args.voice)
    if ref_audio:
        print(f"  Reference audio: {ref_audio}")
    else:
        print(f"  No reference audio found for '{args.voice}' — using default voice")

    # Load Chatterbox Original
    print(f"\n  Loading Chatterbox Original...", flush=True)
    from chatterbox.tts import ChatterboxTTS
    model = ChatterboxTTS.from_pretrained(device="cuda")
    print(f"  Model loaded.", flush=True)

    # Synthesize vocals
    print(f"\n  Synthesizing vocals...")
    vocal_track = build_vocal_track(
        sections=sections,
        model=model,
        ref_audio=ref_audio,
        exaggeration=args.exaggeration,
        line_gap_ms=LINE_GAP_MS,
        verse_gap_ms=VERSE_GAP_MS,
    )
    print(f"\n  Vocal track: {len(vocal_track) / 1000:.1f}s")

    # Output path
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.out:
        out_path = Path(args.out)
    else:
        out_path = OUTPUT_DIR / f"track.{args.format}"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.vocals_only:
        # Export vocals only
        vocal_track.export(str(out_path), format="wav")
        print(f"\n  Vocals saved: {out_path}")
    else:
        # Mix over beat
        print(f"\n  Mixing over beat: {args.beat}")
        mixed = mix_vocal_over_beat(
            vocal=vocal_track,
            beat_path=args.beat,
            lead_in_ms=args.lead_in,
            vocal_gain_db=args.vocal_gain,
            beat_gain_db=args.beat_gain,
        )
        print(f"  Mixed track: {len(mixed) / 1000:.1f}s")

        # Always export as WAV first
        wav_out = str(out_path.with_suffix(".wav"))
        mixed.export(wav_out, format="wav")

        if args.format == "mp3":
            # Convert WAV to MP3 via ffmpeg
            import subprocess
            try:
                import imageio_ffmpeg
                ffmpeg_bin = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                ffmpeg_bin = "ffmpeg"
            subprocess.run(
                [ffmpeg_bin, "-y", "-i", wav_out, "-b:a", "192k", str(out_path)],
                capture_output=True, check=True,
            )
            os.remove(wav_out)
            print(f"\n  Track saved: {out_path}")
        else:
            print(f"\n  Track saved: {wav_out}")

    print(f"\n  Done. Seven Wisdoms, no regret.")


if __name__ == "__main__":
    main()
