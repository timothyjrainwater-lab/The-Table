"""
A/B Test Player — Direct PortAudio playback via sounddevice.
Bypasses Windows media caching entirely.

Plays clips with audible beep separators so you can tell them apart.
1 beep = version A (original)
2 beeps = version B (processed)
3 beeps = version C (processed variant)
"""

import sys
import os
import time
import numpy as np
import sounddevice as sd
import soundfile as sf

def make_beep(freq=880, duration=0.15, sr=24000):
    """Generate a short sine beep."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Apply fade in/out to avoid click
    envelope = np.ones_like(t)
    fade = int(sr * 0.01)
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] = np.linspace(1, 0, fade)
    return (0.3 * np.sin(2 * np.pi * freq * t) * envelope).astype(np.float32)

def make_silence(duration=0.3, sr=24000):
    """Generate silence."""
    return np.zeros(int(sr * duration), dtype=np.float32)

def play_with_marker(filepath, beep_count, sr=24000):
    """Play N beeps then the audio file."""
    beep = make_beep(sr=sr)
    gap = make_silence(0.15, sr)
    pause = make_silence(0.5, sr)

    # Build marker: N beeps with gaps
    marker_parts = []
    for i in range(beep_count):
        marker_parts.append(beep)
        if i < beep_count - 1:
            marker_parts.append(gap)
    marker_parts.append(pause)
    marker = np.concatenate(marker_parts)

    # Load audio
    audio, file_sr = sf.read(filepath, dtype='float32')
    if audio.ndim > 1:
        audio = audio.mean(axis=1)  # mono mixdown

    # Resample marker if needed
    if file_sr != sr:
        marker_resampled = np.interp(
            np.linspace(0, len(marker), int(len(marker) * file_sr / sr)),
            np.arange(len(marker)),
            marker
        ).astype(np.float32)
        marker = marker_resampled
        playback_sr = file_sr
    else:
        playback_sr = sr

    # Concatenate and play
    full = np.concatenate([marker, audio])

    basename = os.path.basename(filepath)
    print(f"  {'*' * beep_count} beep(s) -> {basename}")
    print(f"    samples: {len(audio)}, sr: {playback_sr}, duration: {len(audio)/playback_sr:.1f}s")

    sd.play(full, samplerate=playback_sr)
    sd.wait()

def main():
    if len(sys.argv) < 3:
        print("Usage: python ab_test_player.py file_a.wav file_b.wav [file_c.wav]")
        print("  1 beep = A, 2 beeps = B, 3 beeps = C")
        sys.exit(1)

    files = sys.argv[1:]
    labels = ["A (original)", "B (processed)", "C (variant)"]

    print("=" * 60)
    print("A/B TEST PLAYER — Direct PortAudio (no Windows cache)")
    print("=" * 60)
    for i, f in enumerate(files):
        print(f"  {labels[i]}: {os.path.basename(f)}")
    print()
    print("Listen for beep count: 1=A, 2=B, 3=C")
    print("=" * 60)
    print()

    for i, filepath in enumerate(files):
        if not os.path.exists(filepath):
            print(f"  SKIP: {filepath} not found")
            continue

        play_with_marker(filepath, i + 1)

        if i < len(files) - 1:
            time.sleep(1.0)  # gap between clips

    print()
    print("Done. Which sounded different?")

if __name__ == "__main__":
    main()
