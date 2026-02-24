#!/usr/bin/env python3
"""
Wendy Demo — Image Generation Script (SDXL Turbo)

Generates 6 scene/character images for the Wendy demo video.
Uses SDXL Turbo (4-step, fast) on the RTX 3080 Ti.

Run: .venvs/xtts/Scripts/python scripts/generate_wendy_images.py
Output: scripts/wendy_demo_output/images/
"""

import sys
import io
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR   = PROJECT_ROOT / "scripts" / "wendy_demo_output" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STYLE = (
    ", oil painting, fantasy art, dungeons and dragons 3.5e, "
    "dramatic lighting, highly detailed, cinematic composition, "
    "dark fantasy, rich colors, professional illustration"
)

# (filename, width, height, prompt)
IMAGES = [
    (
        "img_01_title_card.png", 768, 512,
        "Ancient dungeon master's table, thick leather-bound rulebooks stacked, "
        "polished wooden dice tray, ornate metal dice gleaming, "
        "candlelight flickering, parchment maps spread out, "
        "atmospheric tavern background, warm amber tones" + STYLE
    ),
    (
        "img_02_tavern_scene.png", 768, 512,
        "Fantasy medieval tavern interior, door swinging open with dramatic light, "
        "all patrons turning to stare in silence, wooden tables and chairs, "
        "fireplace roaring, mugs of ale, smoke and shadow, "
        "tense atmosphere, moment of dread" + STYLE
    ),
    (
        "img_03_kira_paladin.png", 512, 768,
        "Female human paladin warrior, level one adventurer, "
        "shining silver plate armor, holy symbol on chest, "
        "determined expression, short dark hair, strong build, "
        "divine light emanating, sword held upright, "
        "heroic portrait pose, full armor detail" + STYLE
    ),
    (
        "img_04_villain.png", 512, 768,
        "Sinister villain in dark robes, cold calculating gaze, "
        "smirking with contempt, shadowy dungeon throne room, "
        "ancient stone walls, torchlight, ominous presence, "
        "powerful sorcerer or dark lord, dramatic close portrait" + STYLE
    ),
    (
        "img_05_fallen_hero.png", 768, 512,
        "Fallen adventurer hero on dungeon floor, torch extinguished, "
        "darkness closing in, cracked stone corridor, "
        "scattered equipment, single beam of light fading, "
        "somber atmosphere, tragic end of a quest, grief and loss" + STYLE
    ),
    (
        "img_06_character_sheet.png", 768, 512,
        "Open fantasy character sheet on wooden table, "
        "handwritten stats and abilities, quill pen resting on parchment, "
        "d20 dice beside it, candlelight, rulebook open in background, "
        "organized rows of skills and numbers, ready to play" + STYLE
    ),
]


def generate_images():
    print("=" * 60)
    print("Wendy Demo — Image Generation (SDXL Turbo)")
    print("=" * 60)
    print(f"Output : {OUTPUT_DIR}")
    print(f"Images : {len(IMAGES)}")
    print()

    try:
        import torch
        from diffusers import AutoPipelineForText2Image
    except ImportError as e:
        print(f"[FAIL] {e}")
        print("  Run: .venvs/xtts/Scripts/python scripts/generate_wendy_images.py")
        sys.exit(1)

    if not torch.cuda.is_available():
        print("[FAIL] CUDA not available")
        sys.exit(1)

    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"GPU   : {torch.cuda.get_device_name(0)}")
    print(f"VRAM  : {vram_gb:.1f} GB")
    print()

    print("Loading SDXL Turbo pipeline...")
    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=torch.float16,
        variant="fp16",
    )
    pipe = pipe.to("cuda")
    pipe.enable_attention_slicing()
    print("  Loaded.\n")

    passed = failed = 0

    for filename, width, height, prompt in IMAGES:
        out = OUTPUT_DIR / filename

        if out.exists():
            print(f"  [SKIP] {filename}")
            passed += 1
            continue

        print(f"  [GEN]  {filename}  {width}x{height}")
        print(f"         {prompt[:80]}...")

        try:
            result = pipe(
                prompt=prompt,
                num_inference_steps=4,
                guidance_scale=0.0,
                width=width,
                height=height,
            )
            image = result.images[0]
            image.save(str(out), format="PNG")
            print(f"         -> {out.stat().st_size // 1024} KB  OK")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Result: {passed} OK, {failed} failed")
    if failed == 0:
        print("\nGenerated images:")
        for fn, w, h, _ in IMAGES:
            p = OUTPUT_DIR / fn
            print(f"  {fn}  ({w}x{h}, {p.stat().st_size // 1024} KB)")
    print("=" * 60)


if __name__ == "__main__":
    generate_images()
