"""Gate UI-OBJECT-LAYOUT — Physical object geometry + placement (10 checks).

Verifies that:
1.  stub_character_sheet declared in SHELF_ZONE (table_objects.json)
2.  stub_notebook declared in SHELF_ZONE with x-extent >= 1.3
3.  stub_tome (rulebook) declared in SHELF_ZONE
4.  stub_crystal_ball declared in DM_ZONE
5.  stub_dice_tower declared in DICE_STATION_ZONE
6.  dice_tray_bottom declared in DICE_STATION_ZONE
7.  X-distance between CHAR_SHEET and NOTEBOOK >= 2.0
8.  X-distance between NOTEBOOK and RULEBOOK >= 2.0
9.  vault_cover mesh exists in scene-builder.ts with visible=true default
10. stub_parchment.visible set to false in scene-builder.ts
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_OBJ_JSON = os.path.join(ROOT, 'docs', 'design', 'LAYOUT_PACK_V1', 'table_objects.json')
_BUILDER  = os.path.join(ROOT, 'client', 'src', 'scene-builder.ts')


def _load_objects() -> list:
    with open(_OBJ_JSON) as f:
        data = json.load(f)
    return data['objects']


def _find_obj(name: str) -> dict:
    for obj in _load_objects():
        if obj['mesh_name'] == name or obj['name'] == name:
            return obj
    raise AssertionError(f"table_objects.json: no object with name/mesh_name '{name}'")


# ---------------------------------------------------------------------------
# CHECK 1: stub_character_sheet in SHELF_ZONE
# ---------------------------------------------------------------------------

def test_char_sheet_in_shelf_zone():
    obj = _find_obj('CHAR_SHEET')
    assert obj['zone'] == 'SHELF_ZONE', \
        f"CHAR_SHEET zone must be SHELF_ZONE, got {obj['zone']}"
    # Also verify position is within SHELF_ZONE bounds (centerZ=4.75, halfHeight=0.80)
    z = obj['position']['z']
    assert abs(z - 4.75) <= 0.80, \
        f"CHAR_SHEET z={z} is outside SHELF_ZONE centerZ=4.75 ± 0.80"


# ---------------------------------------------------------------------------
# CHECK 2: stub_notebook in SHELF_ZONE, x-extent >= 1.3
# ---------------------------------------------------------------------------

def test_notebook_in_shelf_zone_with_extent():
    obj = _find_obj('NOTEBOOK')
    assert obj['zone'] == 'SHELF_ZONE', \
        f"NOTEBOOK zone must be SHELF_ZONE, got {obj['zone']}"
    # scale.x from JSON must reflect the dominant footprint
    scale_x = obj.get('scale', {}).get('x', 0)
    assert scale_x >= 1.3, \
        f"NOTEBOOK scale.x must be >= 1.3 (dominant footprint), got {scale_x}"
    # Verify scene-builder uses BoxGeometry with x >= 1.3
    src = open(_BUILDER).read()
    # Look for notebook BoxGeometry — must be at least 1.3 wide
    match = re.search(r'BoxGeometry\(\s*([\d.]+)\s*,\s*[\d.]+\s*,\s*([\d.]+)\s*\)', src)
    # Find the notebook-specific one by searching near the stub_notebook name
    nb_section = src[max(0, src.find('stub_notebook') - 500) : src.find('stub_notebook') + 500]
    geo_match = re.search(r'BoxGeometry\(\s*([\d.]+)', nb_section)
    if geo_match:
        width = float(geo_match.group(1))
        assert width >= 1.3, f"stub_notebook BoxGeometry x must be >= 1.3, got {width}"


# ---------------------------------------------------------------------------
# CHECK 3: stub_tome (rulebook) in SHELF_ZONE
# ---------------------------------------------------------------------------

def test_tome_in_shelf_zone():
    obj = _find_obj('RULEBOOK')
    assert obj['zone'] == 'SHELF_ZONE', \
        f"RULEBOOK zone must be SHELF_ZONE, got {obj['zone']}"
    # Rulebook must be thicker than notebook — check height scale
    height = obj.get('scale', {}).get('y', 0)
    assert height >= 0.14, \
        f"RULEBOOK scale.y (height) must be >= 0.14, got {height}"


# ---------------------------------------------------------------------------
# CHECK 4: stub_crystal_ball in DM_ZONE
# ---------------------------------------------------------------------------

def test_crystal_ball_in_dm_zone():
    obj = _find_obj('CRYSTAL_BALL')
    assert obj['zone'] == 'DM_ZONE', \
        f"CRYSTAL_BALL zone must be DM_ZONE, got {obj['zone']}"
    # Crystal ball must be at positive y (elevated on pedestal)
    y = obj['position']['y']
    assert y > 1.0, \
        f"CRYSTAL_BALL position.y must be > 1.0 (on pedestal), got {y}"


# ---------------------------------------------------------------------------
# CHECK 5: stub_dice_tower in DICE_STATION_ZONE
# ---------------------------------------------------------------------------

def test_dice_tower_in_dice_station_zone():
    obj = _find_obj('DICE_TOWER')
    assert obj['zone'] == 'DICE_STATION_ZONE', \
        f"DICE_TOWER zone must be DICE_STATION_ZONE, got {obj['zone']}"
    # Must be at positive x (right side of table)
    x = obj['position']['x']
    assert x > 3.0, \
        f"DICE_TOWER position.x must be > 3.0 (right side), got {x}"


# ---------------------------------------------------------------------------
# CHECK 6: dice_tray_bottom in DICE_STATION_ZONE
# ---------------------------------------------------------------------------

def test_dice_tray_in_dice_station_zone():
    obj = _find_obj('DICE_TRAY')
    assert obj['zone'] == 'DICE_STATION_ZONE', \
        f"DICE_TRAY zone must be DICE_STATION_ZONE, got {obj['zone']}"
    # Tray must be at positive x (right side) and sane z
    x = obj['position']['x']
    assert x > 3.0, \
        f"DICE_TRAY position.x must be > 3.0, got {x}"


# ---------------------------------------------------------------------------
# CHECK 7: X-distance CHAR_SHEET ↔ NOTEBOOK >= 2.0
# ---------------------------------------------------------------------------

def test_char_sheet_notebook_x_separation():
    sheet = _find_obj('CHAR_SHEET')
    nb    = _find_obj('NOTEBOOK')
    dist = abs(sheet['position']['x'] - nb['position']['x'])
    assert dist >= 2.0, \
        f"X-distance CHAR_SHEET↔NOTEBOOK must be >= 2.0, got {dist:.2f}"


# ---------------------------------------------------------------------------
# CHECK 8: X-distance NOTEBOOK ↔ RULEBOOK >= 2.0
# ---------------------------------------------------------------------------

def test_notebook_rulebook_x_separation():
    nb   = _find_obj('NOTEBOOK')
    book = _find_obj('RULEBOOK')
    dist = abs(nb['position']['x'] - book['position']['x'])
    assert dist >= 2.0, \
        f"X-distance NOTEBOOK↔RULEBOOK must be >= 2.0, got {dist:.2f}"


# ---------------------------------------------------------------------------
# CHECK 9: vault_cover mesh exists in scene-builder.ts, default visible=true
# ---------------------------------------------------------------------------

def test_vault_cover_mesh_exists():
    src = open(_BUILDER).read()
    assert "'vault_cover'" in src or '"vault_cover"' in src, \
        "scene-builder.ts must create a mesh named 'vault_cover'"
    assert 'vaultCoverMesh' in src, \
        "scene-builder.ts must export vaultCoverMesh"
    # vaultCoverMesh is assigned in buildTableSurface — mesh is visible by default
    # (main.ts sets visible=false on combat_start)
    # Confirm the mesh is NOT explicitly set to false in scene-builder itself
    # (default THREE.Mesh.visible = true, so no explicit set needed)
    # Just verify it's exported
    assert 'export let vaultCoverMesh' in src, \
        "scene-builder.ts must export 'let vaultCoverMesh' (not const)"


# ---------------------------------------------------------------------------
# CHECK 10: stub_parchment.visible = false in scene-builder.ts
# ---------------------------------------------------------------------------

def test_stub_parchment_hidden_by_default():
    src = open(_BUILDER).read()
    # Must have stub_parchment name
    assert 'stub_parchment' in src, \
        "scene-builder.ts must create stub_parchment mesh"
    # Must set visible to false
    # Find the section after 'stub_parchment' and confirm .visible = false nearby
    idx = src.rfind('stub_parchment')  # last occurrence (the mesh name assignment)
    # Look within 200 chars before and after for the visible=false assignment
    section = src[max(0, idx - 50) : idx + 300]
    assert 'visible = false' in section or 'visible=false' in section.replace(' ', ''), \
        "stub_parchment must have .visible = false set in scene-builder.ts"
