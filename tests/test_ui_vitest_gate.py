"""Gate TOOLS-VT — Vitest Unit Test Harness (WO-UI-TOOLING-VITEST-001).

Static analysis tests confirm the Vitest infrastructure is correctly
wired and the unit tests cover the required coordinate math and zone logic.

Tests:
    VT-01  vite.config.ts has a test block
    VT-02  vite.config.ts test block includes unit test dir
    VT-03  spatial.test.ts exists in client/tests/unit/
    VT-04  spatial.test.ts covers gridToScene() function
    VT-05  spatial.test.ts covers zone math (zoneAtPosition / getZone)
    VT-06  spatial.test.ts covers camera posture coordinates
    VT-07  spatial.test.ts covers scene-dump.json mesh assertions
    VT-08  scene-dump.json exists in client/tests/
    VT-09  scene-dump.json is valid JSON with 'meshes' array
    VT-10  scene-dump.json contains expected mesh names
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
CLIENT = ROOT / "client"
VITE_CONFIG = CLIENT / "vite.config.ts"
UNIT_DIR    = CLIENT / "tests" / "unit"
SPATIAL_TEST = UNIT_DIR / "spatial.test.ts"
SCENE_DUMP   = CLIENT / "tests" / "scene-dump.json"

REQUIRED_MESH_NAMES = [
    "table_top",
    "felt_vault",
    "stub_crystal_ball",
    "stub_dice_tower",
    "stub_character_sheet",
    "stub_notebook",
    "stub_tome",
    "cup_holder",
    "rail_left",
    "rail_right",
    "rail_far",
]


# ---------------------------------------------------------------------------
# VT-01: vite.config.ts has a test block
# ---------------------------------------------------------------------------

class TestVT01ViteConfigTestBlock:
    def test_vite_config_exists(self):
        assert VITE_CONFIG.exists(), f"vite.config.ts not found at {VITE_CONFIG}"

    def test_vite_config_has_test_block(self):
        text = VITE_CONFIG.read_text(encoding="utf-8")
        assert "test:" in text, "vite.config.ts missing 'test:' configuration block"


# ---------------------------------------------------------------------------
# VT-02: test block includes unit test dir
# ---------------------------------------------------------------------------

class TestVT02TestDirConfigured:
    def test_unit_dir_in_vite_config(self):
        text = VITE_CONFIG.read_text(encoding="utf-8")
        assert "unit" in text, \
            "vite.config.ts test block should include unit test directory"

    def test_include_pattern_in_vite_config(self):
        text = VITE_CONFIG.read_text(encoding="utf-8")
        assert "include" in text, \
            "vite.config.ts test block should have include pattern"


# ---------------------------------------------------------------------------
# VT-03: spatial.test.ts exists
# ---------------------------------------------------------------------------

class TestVT03SpatialTestExists:
    def test_spatial_test_exists(self):
        assert SPATIAL_TEST.exists(), \
            f"spatial.test.ts not found at {SPATIAL_TEST}"


# ---------------------------------------------------------------------------
# VT-04: gridToScene covered
# ---------------------------------------------------------------------------

class TestVT04GridToScene:
    def test_gridToScene_tested(self):
        text = SPATIAL_TEST.read_text(encoding="utf-8")
        assert "gridToScene" in text, \
            "spatial.test.ts must test gridToScene()"

    def test_GRID_SCALE_constant_present(self):
        text = SPATIAL_TEST.read_text(encoding="utf-8")
        assert "GRID_SCALE" in text, \
            "spatial.test.ts must define GRID_SCALE constant"

    def test_TOKEN_Y_constant_present(self):
        text = SPATIAL_TEST.read_text(encoding="utf-8")
        assert "TOKEN_Y" in text, \
            "spatial.test.ts must define TOKEN_Y constant"


# ---------------------------------------------------------------------------
# VT-05: zone math covered
# ---------------------------------------------------------------------------

class TestVT05ZoneMath:
    def test_zoneAtPosition_tested(self):
        text = SPATIAL_TEST.read_text(encoding="utf-8")
        assert "zoneAtPosition" in text or "Zone" in text, \
            "spatial.test.ts must test zone math"

    def test_all_five_zones_referenced(self):
        text = SPATIAL_TEST.read_text(encoding="utf-8")
        for zone in ["player", "map", "dm", "dice_tray", "dice_tower"]:
            assert zone in text, f"Zone '{zone}' not referenced in spatial.test.ts"


# ---------------------------------------------------------------------------
# VT-06: camera posture coordinates covered
# ---------------------------------------------------------------------------

class TestVT06PostureCoords:
    def test_posture_sanity_tested(self):
        text = SPATIAL_TEST.read_text(encoding="utf-8")
        assert "STANDARD" in text, \
            "spatial.test.ts must test STANDARD camera posture"
        assert "LEAN_FORWARD" in text, \
            "spatial.test.ts must test LEAN_FORWARD camera posture"
        assert "DICE_TRAY" in text, \
            "spatial.test.ts must test DICE_TRAY camera posture"


# ---------------------------------------------------------------------------
# VT-07: scene-dump.json mesh assertions present
# ---------------------------------------------------------------------------

class TestVT07SceneDumpAssertions:
    def test_scene_dump_import_in_test(self):
        text = SPATIAL_TEST.read_text(encoding="utf-8")
        assert "scene-dump" in text, \
            "spatial.test.ts must import scene-dump.json"

    def test_mesh_position_assertions_present(self):
        text = SPATIAL_TEST.read_text(encoding="utf-8")
        assert "position" in text and "meshByName" in text, \
            "spatial.test.ts must assert mesh positions from scene dump"


# ---------------------------------------------------------------------------
# VT-08: scene-dump.json exists
# ---------------------------------------------------------------------------

class TestVT08SceneDumpExists:
    def test_scene_dump_exists(self):
        assert SCENE_DUMP.exists(), \
            f"scene-dump.json not found at {SCENE_DUMP}"


# ---------------------------------------------------------------------------
# VT-09: scene-dump.json is valid JSON with meshes array
# ---------------------------------------------------------------------------

class TestVT09SceneDumpValid:
    def _load(self):
        return json.loads(SCENE_DUMP.read_text(encoding="utf-8"))

    def test_valid_json(self):
        data = self._load()
        assert isinstance(data, dict), "scene-dump.json must be a JSON object"

    def test_meshes_array_present(self):
        data = self._load()
        assert "meshes" in data, "scene-dump.json missing 'meshes' key"
        assert isinstance(data["meshes"], list), "'meshes' must be an array"
        assert len(data["meshes"]) > 0, "'meshes' array must not be empty"

    def test_each_mesh_has_name_and_position(self):
        data = self._load()
        for mesh in data["meshes"]:
            assert "name" in mesh, f"Mesh missing 'name' field: {mesh}"
            assert "position" in mesh, f"Mesh '{mesh.get('name')}' missing 'position'"
            pos = mesh["position"]
            for axis in ("x", "y", "z"):
                assert axis in pos, \
                    f"Mesh '{mesh['name']}' position missing '{axis}' field"


# ---------------------------------------------------------------------------
# VT-10: scene-dump.json contains expected mesh names
# ---------------------------------------------------------------------------

class TestVT10SceneDumpMeshNames:
    def _names(self):
        data = json.loads(SCENE_DUMP.read_text(encoding="utf-8"))
        return {m["name"] for m in data["meshes"]}

    def test_required_meshes_present(self):
        names = self._names()
        for expected in REQUIRED_MESH_NAMES:
            assert expected in names, \
                f"Expected mesh '{expected}' not found in scene-dump.json"
