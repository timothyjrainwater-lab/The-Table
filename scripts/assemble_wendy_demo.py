#!/usr/bin/env python3
"""
Wendy Demo -- Video Assembly Script

Strategy:
  1. For each clip: use PIL to composite a frame image
     (SDXL background + dark text panel + speaker label + caption)
  2. Use ffmpeg to mux that still PNG + WAV audio into a short MP4
  3. Concatenate all clip MP4s into final wendy_demo.mp4

Run:    python scripts/assemble_wendy_demo.py
Output: scripts/wendy_demo_output/wendy_demo.mp4
"""

import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[FAIL] Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR    = PROJECT_ROOT / "scripts" / "wendy_demo_output"
IMAGE_DIR    = AUDIO_DIR / "images"
WORK_DIR     = AUDIO_DIR / "work"
OUTPUT_FILE  = AUDIO_DIR / "wendy_demo.mp4"
WORK_DIR.mkdir(exist_ok=True)

# Output video dimensions (portrait / TikTok)
WIDTH  = 1080
HEIGHT = 1920
FPS    = 30

# Layout
IMG_H      = 880       # background image occupies top N pixels
PANEL_Y    = IMG_H
PANEL_H    = HEIGHT - IMG_H
LABEL_Y    = PANEL_Y + 80
SEP_Y      = LABEL_Y + 95
CAPTION_Y0 = SEP_Y + 55
LINE_GAP   = 90
WM_Y       = HEIGHT - 65

# Fonts (Windows system fonts)
FONT_DIR = Path("C:/Windows/Fonts")

def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    candidates = [FONT_DIR / name]
    for c in candidates:
        if c.exists():
            return ImageFont.truetype(str(c), size)
    return ImageFont.load_default()

# Speaker colors (R, G, B)
COLORS = {
    "ANVIL":   (212, 175,  55),   # gold
    "DM":      (138, 180, 248),   # steel blue
    "NPC_M":   (126, 207, 126),   # sage green
    "NPC_F":   (232, 160, 191),   # rose
    "VILLAIN": (196,  92,  92),   # crimson
}

BG_PANEL  = (13, 10,  6)         # very dark warm black
TEXT_COLOR = (240, 232, 208)      # warm off-white
WM_COLOR   = (90, 90, 90)        # dim grey

# (audio_file, bg_image, speaker, display_name, caption)
CLIPS = [
    ("clip_01_anvil_intro.wav",         "img_01_title_card.png",    "ANVIL",   "ANVIL",
     "Hi Wendy. I'm the AI agent\nworking alongside Tim on this project."),

    ("clip_02_anvil_local.wav",         "img_01_title_card.png",    "ANVIL",   "ANVIL",
     "Everything you hear is generated locally.\nOn Tim's computer. No internet. No cloud."),

    ("clip_03_anvil_voiceintro.wav",    "img_01_title_card.png",    "ANVIL",   "ANVIL",
     "Let me show you what the voice engine can do."),

    ("clip_04_dm_tavern_scene.wav",     "img_02_tavern_scene.png",  "DM",      "DUNGEON MASTER",
     "The door creaks open. The tavern falls silent.\nEvery eye turns toward the entrance."),

    ("clip_05_npc_male_angry.wav",      "img_02_tavern_scene.png",  "NPC_M",   "NPC - MALE",
     "I told you never to come back here.\nYou have five seconds."),

    ("clip_06_npc_female_tense.wav",    "img_02_tavern_scene.png",  "NPC_F",   "NPC - FEMALE",
     "Please. You don't understand what's coming.\nWe have to move. Now."),

    ("clip_07_villain_neutral.wav",     "img_04_villain.png",       "VILLAIN", "VILLAIN",
     "Did you really think you could stop me?\nHow... precious."),

    ("clip_08_dm_grief.wav",            "img_05_fallen_hero.png",   "DM",      "DUNGEON MASTER",
     "And just like that -- it was over.\nThe hero fell. The dungeon swallowed them whole."),

    ("clip_09_anvil_sixvoices.wav",     "img_01_title_card.png",    "ANVIL",   "ANVIL",
     "Five distinct voices. All generated.\nAll local. All part of the same system."),

    ("clip_10_anvil_brains.wav",        "img_06_character_sheet.png","ANVIL",  "ANVIL",
     "Now let me show you the other half.\nThe brains."),

    ("clip_11_anvil_engine.wav",        "img_06_character_sheet.png","ANVIL",  "ANVIL",
     "One command. A complete D&D character --\nevery stat, every skill, calculated correctly."),

    ("clip_12_anvil_meetkira.wav",      "img_03_kira_paladin.png",  "ANVIL",   "ANVIL",
     "Meet Kira. Human Paladin. Level 1.\nSTR 15  HP 11  Attack +3  Ready to play."),

    ("clip_13_anvil_sixthousand.wav",   "img_06_character_sheet.png","ANVIL",  "ANVIL",
     "Over six thousand individual tests.\nEvery rule verified before it ships."),

    ("clip_14_npc_female_question.wav", "img_06_character_sheet.png","NPC_F",  "NPC - FEMALE",
     "You're telling me a computer\nlearned the entire rulebook?"),

    ("clip_15_dm_everypage.wav",        "img_06_character_sheet.png","DM",     "DUNGEON MASTER",
     "Every page."),

    ("clip_16_anvil_wendy.wav",         "img_01_title_card.png",    "ANVIL",   "ANVIL",
     "Wendy -- Tim has been building something real.\nHe is closer to the finish line than the start."),

    ("clip_17_villain_continues.wav",   "img_04_villain.png",       "VILLAIN", "VILLAIN",
     "The project continues."),

    ("clip_18_anvil_wisdoms.wav",       "img_01_title_card.png",    "ANVIL",   "ANVIL",
     "Seven wisdoms. Zero regrets."),
]


def get_duration(wav_path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(wav_path)],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())


def draw_centered(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont,
                  y: int, color: tuple, shadow: bool = True) -> None:
    """Draw horizontally centered text with optional drop shadow."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (WIDTH - tw) // 2
    if shadow:
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 180))
    draw.text((x, y), text, font=font, fill=color)


def make_frame(bg_image_path: Path, speaker: str, display_name: str, caption: str) -> Image.Image:
    """Composite a single frame: background + dark panel + text."""
    color = COLORS.get(speaker, (255, 255, 255))

    # Load and scale background to fill 1080 wide, then fit into IMG_H
    bg = Image.open(str(bg_image_path)).convert("RGB")
    # Scale so width = 1080 (maintain aspect)
    bw, bh = bg.size
    scale = WIDTH / bw
    new_h = int(bh * scale)
    bg = bg.resize((WIDTH, new_h), Image.LANCZOS)
    # Crop or pad vertically to IMG_H
    if new_h >= IMG_H:
        # crop top portion
        top = (new_h - IMG_H) // 4   # slightly above center for better composition
        bg = bg.crop((0, top, WIDTH, top + IMG_H))
    else:
        # pad with black at bottom
        padded = Image.new("RGB", (WIDTH, IMG_H), BG_PANEL)
        padded.paste(bg, (0, 0))
        bg = padded

    # Create full canvas
    canvas = Image.new("RGB", (WIDTH, HEIGHT), BG_PANEL)
    canvas.paste(bg, (0, 0))

    # Dark panel overlay on top of image (gradient feel — darken lower part of image)
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    # Gradient-like darkening: from transparent at IMG_H-200 to solid at IMG_H
    for i in range(200):
        alpha = int((i / 200) * 180)
        ov_draw.line([(0, IMG_H - 200 + i), (WIDTH, IMG_H - 200 + i)],
                     fill=(0, 0, 0, alpha))
    # Solid dark panel below
    ov_draw.rectangle([(0, PANEL_Y), (WIDTH, HEIGHT)], fill=(*BG_PANEL, 255))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(canvas)

    # Load fonts
    font_label    = load_font("segoeuib.ttf", 62)
    font_caption  = load_font("segoeuii.ttf", 50)
    font_watermark = load_font("segoeui.ttf", 36)

    # Speaker label
    draw_centered(draw, display_name, font_label, LABEL_Y, color)

    # Separator line
    sep_x1 = 100
    sep_x2 = WIDTH - 100
    draw.line([(sep_x1, SEP_Y), (sep_x2, SEP_Y)], fill=(*color, 140), width=2)

    # Caption lines
    lines = [l.strip() for l in caption.split("\n") if l.strip()]
    for i, line in enumerate(lines):
        y = CAPTION_Y0 + i * LINE_GAP
        draw_centered(draw, line, font_caption, y, TEXT_COLOR)

    # Watermark
    draw_centered(draw, "AIDM - AI Dungeon Master", font_watermark, WM_Y, WM_COLOR, shadow=False)

    return canvas


def make_clip(idx: int, audio_file: str, bg_image: str, speaker: str,
              display_name: str, caption: str) -> Path:
    out = WORK_DIR / f"clip_{idx:02d}.mp4"
    if out.exists():
        print(f"  [SKIP] {out.name}")
        return out

    audio_path = AUDIO_DIR / audio_file
    image_path = IMAGE_DIR / bg_image
    frame_path = WORK_DIR / f"frame_{idx:02d}.png"
    duration   = get_duration(audio_path)

    print(f"  [FRAME] Compositing frame {idx:02d}  ({speaker})")
    frame = make_frame(image_path, speaker, display_name, caption)
    frame.save(str(frame_path))

    print(f"  [ENCODE] clip_{idx:02d}.mp4  {duration:.1f}s")
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-framerate", str(FPS),
        "-i", str(frame_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "128k",
        "-t", str(duration),
        "-shortest",
        str(out)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [FAIL] ffmpeg error:")
        print(result.stderr[-2000:])
        sys.exit(1)

    return out


def concat_all(clip_paths: list) -> None:
    concat_file = WORK_DIR / "_concat.txt"
    with open(concat_file, "w") as f:
        for p in clip_paths:
            # Use forward slashes
            f.write(f"file '{p.as_posix()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(OUTPUT_FILE)
    ]

    print(f"\n[CONCAT] {len(clip_paths)} clips -> {OUTPUT_FILE.name}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("[FAIL] concat error:")
        print(result.stderr[-2000:])
        sys.exit(1)


def main():
    print("=" * 60)
    print("Wendy Demo -- Video Assembly")
    print("=" * 60)
    print(f"Clips  : {len(CLIPS)}")
    print(f"Output : {OUTPUT_FILE}")
    print(f"Format : {WIDTH}x{HEIGHT} portrait @ {FPS}fps")
    print()

    for audio_file, bg_image, *_ in CLIPS:
        for p, label in [(AUDIO_DIR / audio_file, "audio"), (IMAGE_DIR / bg_image, "image")]:
            if not p.exists():
                print(f"[FAIL] Missing {label}: {p}")
                sys.exit(1)

    clip_paths = []
    for idx, (audio_file, bg_image, speaker, display_name, caption) in enumerate(CLIPS, 1):
        print(f"\nClip {idx:02d}/{len(CLIPS)}: [{speaker}] {audio_file}")
        p = make_clip(idx, audio_file, bg_image, speaker, display_name, caption)
        clip_paths.append(p)

    concat_all(clip_paths)

    size_mb  = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    total_s  = sum(get_duration(AUDIO_DIR / af) for af, *_ in CLIPS)

    print()
    print("=" * 60)
    print(f"DONE:     {OUTPUT_FILE.name}")
    print(f"Size:     {size_mb:.1f} MB")
    print(f"Duration: {total_s:.1f}s  ({total_s/60:.1f} min)")
    print("=" * 60)


if __name__ == "__main__":
    main()
