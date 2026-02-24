"""Gate UI-LAYOUT-PACK — Layout Pack V1 data-driven wiring (8 checks).

Verifies that:
1. docs/design/LAYOUT_PACK_V1/zones.json exists and has 6 zones + anchors
2. docs/design/LAYOUT_PACK_V1/camera_poses.json exists and has 5 postures + transition_ms
3. docs/design/LAYOUT_PACK_V1/table_objects.json exists and has 7 objects
4. aidm/ui/zones.json uses layout-pack-v1 schema
5. camera.ts imports from camera_poses.json (no hardcoded positions in POSTURES const)
6. scene-builder.ts imports from table_objects.json
7. scene-builder.ts has no stray d6 stubs (d6Positions array removed)
8. debug-overlay.ts exports addZonesOverlay and reads zones.json
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# CHECK 1: zones.json exists and has 6 zones + anchors block
# ---------------------------------------------------------------------------

def test_layout_pack_zones_json_structure():
    path = os.path.join(ROOT, 'docs', 'design', 'LAYOUT_PACK_V1', 'zones.json')
    assert os.path.exists(path), f"Missing: {path}"
    with open(path) as f:
        data = json.load(f)
    assert data.get('schema') == 'layout-pack-v1', "zones.json must have schema=layout-pack-v1"
    zones = data.get('zones', [])
    assert len(zones) == 6, f"Expected 6 zones, got {len(zones)}"
    zone_names = {z['name'] for z in zones}
    expected = {'DM_ZONE', 'VAULT_ZONE', 'WORK_ZONE', 'TRASH_RING_ZONE', 'SHELF_ZONE', 'DICE_STATION_ZONE'}
    assert zone_names == expected, f"Zone names mismatch: {zone_names}"
    assert 'anchors' in data, "zones.json must have an 'anchors' block"
    assert len(data['anchors']) >= 8, f"Expected >=8 anchors, got {len(data['anchors'])}"


# ---------------------------------------------------------------------------
# CHECK 2: camera_poses.json exists and has 5 postures + transition_ms
# ---------------------------------------------------------------------------

def test_layout_pack_camera_poses_json_structure():
    path = os.path.join(ROOT, 'docs', 'design', 'LAYOUT_PACK_V1', 'camera_poses.json')
    assert os.path.exists(path), f"Missing: {path}"
    with open(path) as f:
        data = json.load(f)
    assert 'transition_ms' in data, "camera_poses.json must have transition_ms"
    assert isinstance(data['transition_ms'], (int, float)), "transition_ms must be numeric"
    postures = data.get('postures', {})
    expected_postures = {'STANDARD', 'DOWN', 'LEAN_FORWARD', 'DICE_TRAY', 'BOOK_READ'}
    assert set(postures.keys()) == expected_postures, f"Posture keys mismatch: {set(postures.keys())}"
    for name, cfg in postures.items():
        assert 'position' in cfg, f"Posture {name} missing 'position'"
        assert 'lookAt' in cfg, f"Posture {name} missing 'lookAt'"
        for field in ('position', 'lookAt'):
            for axis in ('x', 'y', 'z'):
                assert axis in cfg[field], f"Posture {name}.{field} missing '{axis}'"


# ---------------------------------------------------------------------------
# CHECK 3: table_objects.json exists and has 7 named objects
# ---------------------------------------------------------------------------

def test_layout_pack_table_objects_json_structure():
    path = os.path.join(ROOT, 'docs', 'design', 'LAYOUT_PACK_V1', 'table_objects.json')
    assert os.path.exists(path), f"Missing: {path}"
    with open(path) as f:
        data = json.load(f)
    objects = data.get('objects', [])
    assert len(objects) == 7, f"Expected 7 objects, got {len(objects)}"
    obj_names = {o['name'] for o in objects}
    expected = {'CHAR_SHEET', 'NOTEBOOK', 'RULEBOOK', 'DICE_BAG', 'CRYSTAL_BALL', 'DICE_TRAY', 'DICE_TOWER'}
    assert obj_names == expected, f"Object names mismatch: {obj_names}"
    for obj in objects:
        assert 'position' in obj, f"Object {obj['name']} missing 'position'"
        assert 'rotation_y' in obj, f"Object {obj['name']} missing 'rotation_y'"


# ---------------------------------------------------------------------------
# CHECK 4: aidm/ui/zones.json uses layout-pack-v1 schema
# ---------------------------------------------------------------------------

def test_aidm_ui_zones_json_schema():
    path = os.path.join(ROOT, 'aidm', 'ui', 'zones.json')
    assert os.path.exists(path), f"Missing: {path}"
    with open(path) as f:
        data = json.load(f)
    assert data.get('schema') == 'layout-pack-v1', \
        f"aidm/ui/zones.json must have schema=layout-pack-v1, got: {data.get('schema')}"
    assert 'zones' in data, "aidm/ui/zones.json must have 'zones' array"
    assert 'anchors' in data, "aidm/ui/zones.json must have 'anchors' block"


# ---------------------------------------------------------------------------
# CHECK 5: camera.ts imports camera_poses.json, no POSTURES hardcoded block
# ---------------------------------------------------------------------------

def test_camera_ts_imports_json_not_hardcoded():
    path = os.path.join(ROOT, 'client', 'src', 'camera.ts')
    assert os.path.exists(path), f"Missing: {path}"
    src = open(path).read()

    # Must import from camera_poses.json
    assert 'camera_poses.json' in src, \
        "camera.ts must import from camera_poses.json"

    # Must NOT define hardcoded POSTURES object with new THREE.Vector3 literals
    # (the old pattern was: STANDARD: { position: new THREE.Vector3(...) }
    # inside a const POSTURES = { ... } block with all 5 entries hardcoded)
    hardcoded_pattern = re.search(
        r'const POSTURES[^=]*=\s*\{[^}]*STANDARD\s*:\s*\{[^}]*new THREE\.Vector3',
        src, re.DOTALL
    )
    assert hardcoded_pattern is None, \
        "camera.ts must not contain a hardcoded POSTURES const with Vector3 literals — use camera_poses.json"


# ---------------------------------------------------------------------------
# CHECK 6: scene-builder.ts imports table_objects.json
# ---------------------------------------------------------------------------

def test_scene_builder_imports_table_objects_json():
    path = os.path.join(ROOT, 'client', 'src', 'scene-builder.ts')
    assert os.path.exists(path), f"Missing: {path}"
    src = open(path).read()
    assert 'table_objects.json' in src, \
        "scene-builder.ts must import from table_objects.json"
    # Must use _objPos helper (or similar) to read positions
    assert '_objPos' in src, \
        "scene-builder.ts must use _objPos() helper to read object positions from JSON"


# ---------------------------------------------------------------------------
# CHECK 7: scene-builder.ts has no stray d6 stub positions array
# ---------------------------------------------------------------------------

def test_scene_builder_no_d6_stubs():
    path = os.path.join(ROOT, 'client', 'src', 'scene-builder.ts')
    src = open(path).read()
    # The old code had: const d6Positions: [number, number, number][] = [
    assert 'd6Positions' not in src, \
        "scene-builder.ts must not contain d6Positions stub array — d6 stubs were removed in WO-UI-LAYOUT-PACK-V1"


# ---------------------------------------------------------------------------
# CHECK 8: debug-overlay.ts exports addZonesOverlay and imports zones.json
# ---------------------------------------------------------------------------

def test_debug_overlay_zones_overlay():
    path = os.path.join(ROOT, 'client', 'src', 'debug-overlay.ts')
    assert os.path.exists(path), f"Missing: {path}"
    src = open(path).read()
    assert 'zones.json' in src, \
        "debug-overlay.ts must import zones.json"
    assert 'addZonesOverlay' in src, \
        "debug-overlay.ts must export addZonesOverlay function"
    assert 'isZonesMode' in src, \
        "debug-overlay.ts must export isZonesMode() function"
