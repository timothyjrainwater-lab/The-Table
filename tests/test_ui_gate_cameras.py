"""Gate UI-CAMERAS — Camera posture system wiring (6 checks).

Verifies that:
1. camera.ts imports from camera_poses.json (no hardcoded POSTURES const)
2. TRANSITION_MS exported from camera.ts and reads from JSON field
3. Transition is duration-based (dt / transitionDuration, not dt * speed)
4. All 5 posture hotkeys (1-5) are wired in main.ts
5. camera_poses.json transition_ms is 350
6. All 5 PostureNames are populated from JSON (no missing entries)
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# CHECK 1: camera.ts imports from camera_poses.json
# ---------------------------------------------------------------------------

def test_camera_ts_imports_poses_json():
    path = os.path.join(ROOT, 'client', 'src', 'camera.ts')
    src = open(path).read()
    assert 'camera_poses.json' in src, \
        "camera.ts must import from camera_poses.json"
    # Must not have the old hardcoded POSTURES block
    assert 'speed: number = 3.0' not in src, \
        "camera.ts must not have hardcoded speed:3.0 — use duration-based transitions"


# ---------------------------------------------------------------------------
# CHECK 2: TRANSITION_MS exported and reads from JSON field
# ---------------------------------------------------------------------------

def test_camera_ts_exports_transition_ms():
    path = os.path.join(ROOT, 'client', 'src', 'camera.ts')
    src = open(path).read()
    assert 'export const TRANSITION_MS' in src, \
        "camera.ts must export TRANSITION_MS constant"
    # Must derive from the JSON's transition_ms field
    assert 'transition_ms' in src, \
        "camera.ts must reference transition_ms from the JSON"


# ---------------------------------------------------------------------------
# CHECK 3: Transition is duration-based (dt / transitionDuration)
# ---------------------------------------------------------------------------

def test_camera_ts_duration_based_transition():
    path = os.path.join(ROOT, 'client', 'src', 'camera.ts')
    src = open(path).read()
    # The old speed-based formula was: dt * this.speed
    # The new duration-based formula is: dt / this.transitionDuration
    assert 'dt / this.transitionDuration' in src or 'dt / TRANSITION' in src or 'dt /' in src, \
        "camera.ts update() must use duration-based interpolation (dt / transitionDuration)"
    # Ensure the old speed multiplier is gone
    assert 'dt * this.speed' not in src, \
        "camera.ts must not use dt * speed — transition is duration-based"


# ---------------------------------------------------------------------------
# CHECK 4: All 5 posture hotkeys wired in main.ts
# ---------------------------------------------------------------------------

def test_main_ts_posture_hotkeys():
    path = os.path.join(ROOT, 'client', 'src', 'main.ts')
    src = open(path).read()
    # All five posture switch cases must be present
    required = [
        ("'1'", 'STANDARD'),
        ("'2'", 'DOWN'),
        ("'3'", 'LEAN_FORWARD'),
        ("'4'", 'DICE_TRAY'),
        ("'5'", 'BOOK_READ'),
    ]
    for key_str, posture in required:
        assert key_str in src or f'Digit{key_str[1]}' in src, \
            f"main.ts missing hotkey {key_str}"
        assert posture in src, \
            f"main.ts missing posture reference '{posture}'"


# ---------------------------------------------------------------------------
# CHECK 5: camera_poses.json transition_ms = 350
# ---------------------------------------------------------------------------

def test_camera_poses_json_transition_ms():
    path = os.path.join(ROOT, 'docs', 'design', 'LAYOUT_PACK_V1', 'camera_poses.json')
    with open(path) as f:
        data = json.load(f)
    assert data.get('transition_ms') == 350, \
        f"camera_poses.json transition_ms must be 350, got {data.get('transition_ms')}"


# ---------------------------------------------------------------------------
# CHECK 6: All 5 PostureNames present in camera_poses.json
# ---------------------------------------------------------------------------

def test_camera_poses_json_all_postures():
    path = os.path.join(ROOT, 'docs', 'design', 'LAYOUT_PACK_V1', 'camera_poses.json')
    with open(path) as f:
        data = json.load(f)
    postures = set(data.get('postures', {}).keys())
    required = {'STANDARD', 'DOWN', 'LEAN_FORWARD', 'DICE_TRAY', 'BOOK_READ'}
    assert postures == required, f"camera_poses.json postures mismatch: {postures}"
    # Each posture must have physically grounded values (y > 0)
    for name, cfg in data['postures'].items():
        assert cfg['position']['y'] > 0, \
            f"Posture {name} position.y must be > 0 (camera above table surface)"
