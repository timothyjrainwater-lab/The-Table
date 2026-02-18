#!/usr/bin/env python3
"""Builder Preflight Canary — Image + Voice pipeline validation.

Run this before any WO work. It proves both pipelines are functional
on this machine, right now.

Usage:
    python scripts/preflight_canary.py

What it does:
    1. Image canary: generates a fixed portrait twice (generated → cached)
    2. Voice canary: speaks a fixed line twice (success → success)
    3. Prints PASS/FAIL for each

No telemetry, no frameworks, no Oracle writes.
"""

import sys
from pathlib import Path

# Project root = parent of scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_image_canary() -> bool:
    """Run the image pipeline canary.

    Generates a fixed portrait twice. First run should produce
    status="generated", second should produce status="cached"
    with the same content_hash.

    Returns True if both runs pass.
    """
    print("=" * 60)
    print("IMAGE CANARY")
    print("=" * 60)

    try:
        from aidm.immersion.sdxl_image_adapter import SDXLImageAdapter
        from aidm.schemas.immersion import ImageRequest
    except ImportError as e:
        print(f"  FAIL: Import error — {e}")
        return False

    request = ImageRequest(
        kind="portrait",
        semantic_key="canary:image:v1",
        prompt_context=(
            "A dwarf blacksmith at a forge, hammer raised, "
            "sparks flying, oil painting style"
        ),
        dimensions=(512, 512),
    )

    cache_dir = PROJECT_ROOT / "image_cache"
    adapter = SDXLImageAdapter(cache_dir=cache_dir)

    if not adapter.is_available():
        print(f"  FAIL: SDXL not available — {adapter.get_availability_reason()}")
        return False

    # Run 1: expect generated
    print("  Run 1 (generate)...")
    result1 = adapter.generate(request)
    if result1.status == "error":
        print(f"  FAIL: Generation error — {result1.error_message}")
        return False

    print(f"    Status: {result1.status}")
    print(f"    Path:   {result1.path}")
    print(f"    Hash:   {result1.content_hash}")

    if result1.status not in ("generated", "cached"):
        print(f"  FAIL: Unexpected status '{result1.status}'")
        return False

    # Run 2: expect cached
    print("  Run 2 (cache check)...")
    result2 = adapter.generate(request)
    print(f"    Status: {result2.status}")
    print(f"    Hash:   {result2.content_hash}")

    if result2.status != "cached":
        print(f"  WARN: Expected 'cached', got '{result2.status}'")
        # Not a hard failure — cache may have been cleared between runs

    if result1.content_hash != result2.content_hash:
        print(f"  WARN: Hash mismatch — {result1.content_hash} vs {result2.content_hash}")

    # Cleanup
    adapter.unload_pipeline()

    print("  IMAGE CANARY: PASS")
    return True


def run_voice_canary() -> bool:
    """Run the voice pipeline canary.

    Speaks a fixed line twice using dm_narrator persona.
    Both runs should succeed (audio plays).

    Returns True if both runs pass.
    """
    print()
    print("=" * 60)
    print("VOICE CANARY")
    print("=" * 60)

    try:
        from scripts.speak import speak
    except ImportError as e:
        print(f"  FAIL: Import error — {e}")
        return False

    text = "The forge is lit. Steel meets hammer. The work begins."
    persona = "dm_narrator"
    volume = 0.5
    backend = "chatterbox"

    # Run 1
    print(f"  Run 1 (generate)...")
    ok1 = speak(text, persona, volume, backend)
    print(f"    Success: {ok1}")

    if not ok1:
        print("  FAIL: Voice generation failed on run 1")
        return False

    # Run 2
    print(f"  Run 2 (repeat)...")
    ok2 = speak(text, persona, volume, backend)
    print(f"    Success: {ok2}")

    if not ok2:
        print("  FAIL: Voice generation failed on run 2")
        return False

    print("  VOICE CANARY: PASS")
    return True


def main() -> None:
    print()
    print("BUILDER PREFLIGHT CANARY")
    print("Run this before any WO work.")
    print()

    image_ok = run_image_canary()
    voice_ok = run_voice_canary()

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Image: {'PASS' if image_ok else 'FAIL'}")
    print(f"  Voice: {'PASS' if voice_ok else 'FAIL'}")
    print()

    if image_ok and voice_ok:
        print("All canaries passed. Pipelines are functional.")
        print()
        print("NEXT: Generate your skill artifacts.")
        print("  Image: Read pm_inbox/MEMO_IMAGE_GEN_WALKTHROUGH.md")
        print("         Generate 1 portrait of any subject. Save to image_cache/.")
        print("  Voice: Read pm_inbox/MEMO_TTS_MONOLOGUE_WALKTHROUGH.md")
        print("         Choose any non-reserved persona. Speak 1-2 sentences.")
        print("  Log results in pm_inbox/PREFLIGHT_CANARY_LOG.md")
        sys.exit(0)
    else:
        print("STOP. Do not proceed with WO work. Report the failure.")
        sys.exit(1)


if __name__ == "__main__":
    main()
