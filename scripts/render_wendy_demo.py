#!/usr/bin/env python3
"""
Wendy Demo — Voice Render Script (Kokoro ONNX backend)

Renders all 18 audio clips for the Wendy presentation video.
Uses Kokoro ONNX — no VRAM required, multiple distinct voices.

Voice assignments:
  Anvil/narrator lines  -> af_bella  (clear, authoritative)
  DM scene lines        -> am_adam   (authoritative male)
  NPC male              -> am_michael
  NPC female            -> af_nicole
  Villainous            -> bm_lewis

Output: scripts/wendy_demo_output/
Run with: .venvs/fish_speech/Scripts/python scripts/render_wendy_demo.py
"""

import sys
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR   = PROJECT_ROOT / "models" / "kokoro"
OUTPUT_DIR   = PROJECT_ROOT / "scripts" / "wendy_demo_output"
OUTPUT_DIR.mkdir(exist_ok=True)

ONNX_PATH   = str(MODELS_DIR / "kokoro-v1.0.onnx")
VOICES_PATH = str(MODELS_DIR / "voices-v1.0.bin")

# Voice IDs
ANVIL   = "af_bella"
DM      = "am_adam"
NPC_M   = "am_michael"
NPC_F   = "af_nicole"
VILLAIN = "bm_lewis"

# (filename, voice_id, speed, text)
CLIPS = [
    ("clip_01_anvil_intro.wav", ANVIL, 0.95,
     "Hi Wendy. My name is Anvil. I'm the AI agent working alongside Tim on this project. "
     "He asked me to talk to you directly — so you can see exactly what we've built, in my own voice."),

    ("clip_02_anvil_local.wav", ANVIL, 0.95,
     "Everything you're about to hear — every voice, every character, every line — "
     "is generated locally. On Tim's computer. No internet. No subscription. "
     "No server somewhere else. It runs right here."),

    ("clip_03_anvil_voiceintro.wav", ANVIL, 0.95,
     "Let me show you what the voice engine can do. "
     "I will start with the narrator — the Dungeon Master's voice. Calm. Authoritative. Setting the scene."),

    ("clip_04_dm_tavern_scene.wav", DM, 0.9,
     "The door creaks open. The tavern falls silent. "
     "Every eye in the room turns toward the entrance — "
     "and what steps through the door is not what anyone expected."),

    ("clip_05_npc_male_angry.wav", NPC_M, 1.0,
     "I told you never to come back here. "
     "You've got five seconds before I throw you out myself."),

    ("clip_06_npc_female_tense.wav", NPC_F, 1.0,
     "Please. You don't understand what's coming. None of you do. "
     "We have to move. Now."),

    ("clip_07_villain_neutral.wav", VILLAIN, 0.88,
     "Did you really think you could stop me? How... precious."),

    ("clip_08_dm_grief.wav", DM, 0.88,
     "And just like that — it was over. The hero fell. "
     "The torch went dark. And the dungeon swallowed them whole."),

    ("clip_09_anvil_sixvoices.wav", ANVIL, 0.95,
     "That is five distinct voices. Narrator, Dungeon Master, male NPC, female NPC, villain. "
     "Each with a different character. All generated. All local. All part of the same system."),

    ("clip_10_anvil_brains.wav", ANVIL, 0.95,
     "Now let me show you the other half. The brains."),

    ("clip_11_anvil_engine.wav", ANVIL, 0.95,
     "This is the character engine. One command. The system builds a complete "
     "Dungeons and Dragons character — every stat, every skill, every ability — "
     "calculated correctly from the official rulebook. Automatically."),

    ("clip_12_anvil_meetkira.wav", ANVIL, 0.95,
     "Meet Kira. Human paladin. Level one. "
     "Strength fifteen. Hit points eleven. Attack bonus plus three. "
     "Fortitude save plus three. Nine class skills. Two feat slots. Ready to play."),

    ("clip_13_anvil_sixthousand.wav", ANVIL, 0.95,
     "The system knows every class. Every race. Every feat and skill from the Player's Handbook. "
     "All of it rules-legal. All of it tested. "
     "Over six thousand individual tests — every rule verified before it ships."),

    ("clip_14_npc_female_question.wav", NPC_F, 1.0,
     "You're telling me a computer learned the entire rulebook?"),

    ("clip_15_dm_everypage.wav", DM, 0.9,
     "Every page."),

    ("clip_16_anvil_wendy.wav", ANVIL, 0.93,
     "Wendy — Tim has been building something real. "
     "The voice engine works. The rules engine works. The characters are ready. "
     "What is left is the table itself — the interface you sit down at and play. "
     "He is closer to the finish line than the start. "
     "And he wanted you to hear it — so you know exactly where the work is going."),

    ("clip_17_villain_continues.wav", VILLAIN, 0.85,
     "The project continues."),

    ("clip_18_anvil_wisdoms.wav", ANVIL, 0.9,
     "Seven wisdoms. Zero regrets."),
]


def save_wav(path: Path, samples, sample_rate: int = 24000):
    import numpy as np
    arr = np.array(samples)
    if arr.dtype != "int16":
        arr = (arr * 32767).clip(-32768, 32767).astype("int16")
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(arr.tobytes())


def main():
    print("=" * 60)
    print("Wendy Demo — Voice Render (Kokoro ONNX)")
    print("=" * 60)
    print(f"Model : {ONNX_PATH}")
    print(f"Voices: {VOICES_PATH}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Clips : {len(CLIPS)}")
    print()

    try:
        from kokoro_onnx import Kokoro
    except ImportError:
        print("[FAIL] kokoro_onnx not importable.")
        print("  Run: .venvs/fish_speech/Scripts/python scripts/render_wendy_demo.py")
        sys.exit(1)

    for p in [ONNX_PATH, VOICES_PATH]:
        if not Path(p).exists():
            print(f"[FAIL] Not found: {p}")
            sys.exit(1)

    print("Loading Kokoro...")
    try:
        kokoro = Kokoro(ONNX_PATH, VOICES_PATH)
        print("  Loaded.\n")
    except Exception as e:
        print(f"[FAIL] {e}")
        sys.exit(1)

    passed = failed = 0

    for filename, voice_id, speed, text in CLIPS:
        out = OUTPUT_DIR / filename

        if out.exists():
            print(f"  [SKIP] {filename}")
            passed += 1
            continue

        print(f"  [RENDER] {filename}  voice={voice_id}  speed={speed}")
        print(f"           {text[:80]}...")

        try:
            import numpy as np
            samples, sample_rate = kokoro.create(
                text, voice=voice_id, speed=speed, lang="en-us"
            )
            save_wav(out, samples, sample_rate)
            dur = len(np.array(samples)) / sample_rate
            print(f"           -> {dur:.1f}s  OK")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Result: {passed} OK, {failed} failed")
    print()
    if failed == 0:
        print("Assembly order:")
        for i, (fn, vid, spd, _) in enumerate(CLIPS, 1):
            print(f"  {i:02d}. {fn}  [{vid}]")
    print("=" * 60)


if __name__ == "__main__":
    main()
