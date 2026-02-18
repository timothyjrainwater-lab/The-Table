#!/usr/bin/env python3
"""XTTS-v2 voice synthesis via isolated venv.

Called as a subprocess from the main environment.
Usage:
    .venvs/xtts/Scripts/python.exe scripts/xtts_synth.py \
        --ref "models/voices/piper_ref_alan.wav" \
        --text "Your text here" \
        --out "output.wav"
"""

import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="XTTS-v2 synthesis bridge")
    parser.add_argument("--ref", required=True, help="Reference audio WAV path")
    parser.add_argument("--text", required=True, help="Text to synthesize")
    parser.add_argument("--out", required=True, help="Output WAV path")
    parser.add_argument("--language", default="en", help="Language code")
    args = parser.parse_args()

    print(f"Loading XTTS-v2...", file=sys.stderr)
    from TTS.api import TTS

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)

    print(f"Synthesizing...", file=sys.stderr)
    tts.tts_to_file(
        text=args.text,
        speaker_wav=args.ref,
        language=args.language,
        file_path=args.out,
    )
    print(f"Saved: {args.out}", file=sys.stderr)
    print(args.out)


if __name__ == "__main__":
    main()
