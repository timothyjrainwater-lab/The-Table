"""Gate UI-LIGHTING — Environment + lighting baseline (6 checks).

Verifies:
1.  room_back_wall mesh declared in scene-builder.ts (buildRoom)
2.  room_floor mesh declared in scene-builder.ts (buildRoom)
3.  Scene background is NOT the old void black 0x08060a in main.ts
4.  Walnut texture repeat is (1, 0.75) — not (2, 1.5)
5.  Ambient light color is NOT 0x1a1520 (purple cast) in scene-builder.ts
6.  Parchment base color is the darkened value (#b8a06a) — not old #c8b483
"""

import os
import re

ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BUILDER = os.path.join(ROOT, 'client', 'src', 'scene-builder.ts')
_MAIN    = os.path.join(ROOT, 'client', 'src', 'main.ts')


def _src(path: str) -> str:
    with open(path) as f:
        return f.read()


# ---------------------------------------------------------------------------
# CHECK 1: room_back_wall mesh exists in scene-builder.ts
# ---------------------------------------------------------------------------

def test_room_back_wall_declared():
    src = _src(_BUILDER)
    assert "'room_back_wall'" in src or '"room_back_wall"' in src, \
        "scene-builder.ts must declare a mesh named 'room_back_wall' in buildRoom()"
    assert 'buildRoom' in src, \
        "scene-builder.ts must export function buildRoom()"
    assert 'export function buildRoom' in src, \
        "buildRoom must be exported from scene-builder.ts"


# ---------------------------------------------------------------------------
# CHECK 2: room_floor mesh exists in scene-builder.ts
# ---------------------------------------------------------------------------

def test_room_floor_declared():
    src = _src(_BUILDER)
    assert "'room_floor'" in src or '"room_floor"' in src, \
        "scene-builder.ts must declare a mesh named 'room_floor' in buildRoom()"


# ---------------------------------------------------------------------------
# CHECK 3: Scene background is NOT the old void black
# ---------------------------------------------------------------------------

def test_scene_background_not_void_black():
    src = _src(_MAIN)
    # Find the scene.background line and confirm it uses the new color
    bg_match = re.search(r'scene\.background\s*=.*', src)
    assert bg_match, "main.ts must set scene.background"
    bg_line = bg_match.group(0)
    # Strip inline comment before checking for old value
    code_part = bg_line.split('//')[0]
    assert '0x08060a' not in code_part, \
        f"scene.background must not be 0x08060a (void black). Code: {code_part.strip()}"
    assert '0x100c0a' in code_part, \
        f"scene.background must be 0x100c0a (warm dark brown). Code: {code_part.strip()}"


# ---------------------------------------------------------------------------
# CHECK 4: Walnut texture repeat is (1, 0.75) — not (2, 1.5)
# ---------------------------------------------------------------------------

def test_walnut_repeat_corrected():
    src = _src(_BUILDER)
    # Must contain the new repeat value
    assert 'repeat.set(1, 0.75)' in src, \
        "makeWalnutTexture must use tex.repeat.set(1, 0.75) — old (2, 1.5) tiles grain into invisibility"
    # Must NOT contain the old value
    assert 'repeat.set(2, 1.5)' not in src, \
        "Old tex.repeat.set(2, 1.5) must be removed from scene-builder.ts"


# ---------------------------------------------------------------------------
# CHECK 5: Ambient light is NOT the purple-cast color 0x1a1520
# ---------------------------------------------------------------------------

def test_ambient_not_purple_cast():
    src = _src(_BUILDER)
    # Search for AmbientLight constructor — must not use the old purple-cast color
    ambient_matches = re.findall(r'AmbientLight\([^)]+\)', src)
    assert ambient_matches, "scene-builder.ts must create at least one AmbientLight"
    for am in ambient_matches:
        assert '0x1a1520' not in am, \
            f"AmbientLight must not use 0x1a1520 (purple cast). Found: {am}"
    # Confirm warm color is present
    assert '0x1a1208' in src, \
        "Ambient light must use warm color 0x1a1208 in buildAtmosphere()"


# ---------------------------------------------------------------------------
# CHECK 6: Parchment base is the darkened aged value #b8a06a
# ---------------------------------------------------------------------------

def test_parchment_base_darkened():
    src = _src(_BUILDER)
    # Must contain the new darkened parchment color
    assert "'#b8a06a'" in src or '"#b8a06a"' in src, \
        "makeCharacterSheetTexture parchment base must be '#b8a06a' (was '#c8b483' — too bright)"
    # Old bright parchment must be gone from fillStyle context
    # (it may appear in other strings — check only the fillStyle assignment)
    parch_section = src[max(0, src.find('makeCharacterSheetTexture')) :
                        src.find('makeCharacterSheetTexture') + 400]
    assert '#c8b483' not in parch_section, \
        "Old parchment color #c8b483 must be replaced with #b8a06a in makeCharacterSheetTexture"
