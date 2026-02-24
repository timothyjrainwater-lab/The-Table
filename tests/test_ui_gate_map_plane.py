"""
Gate UI-MAP-PLANE: WO-UI-MAP-01 — MagicMap Plane + Ephemeral Overlays.

Tests (7):
  MAP-01: Map plane exists in scene at VAULT_ZONE / MAP_ZONE
  MAP-02: LEAN_FORWARD posture wiring on map interaction
  MAP-03: PENDING-gate on overlay activation
  MAP-04: No intent emitted without PENDING
  MAP-05: Overlays are TTL-only — nothing persisted
  MAP-06: No permanent drawing path
  MAP-07: Existing lasso + fog gates remain green (regression)

Authority: WO-UI-MAP-01, DOCTRINE_04_TABLE_UI_MEMO_V4 §16.
"""

import re
import pathlib
import subprocess
import sys

ROOT         = pathlib.Path(__file__).parent.parent
SCENE_SRC    = ROOT / "client" / "src" / "scene-builder.ts"
MAIN_SRC     = ROOT / "client" / "src" / "main.ts"
OVERLAY_SRC  = ROOT / "client" / "src" / "map-overlay.ts"
LASSO_SRC    = ROOT / "client" / "src" / "map-lasso.ts"
ZONES_JSON   = ROOT / "aidm" / "ui" / "zones.json"

scene_text   = SCENE_SRC.read_text(encoding="utf-8")
main_text    = MAIN_SRC.read_text(encoding="utf-8")
overlay_text = OVERLAY_SRC.read_text(encoding="utf-8")
lasso_text   = LASSO_SRC.read_text(encoding="utf-8")


# ===========================================================================
# MAP-01: Map plane exists in scene at VAULT_ZONE / MAP_ZONE
# ===========================================================================

def test_map01a_map_plane_mesh_created():
    """MAP-01a: scene-builder.ts creates a mesh named 'map_plane'."""
    assert "map_plane" in scene_text, (
        "scene-builder.ts must create a mesh with name 'map_plane' in the VAULT_ZONE"
    )
    assert re.search(r"\.name\s*=\s*['\"]map_plane['\"]", scene_text), (
        "scene-builder.ts must set mesh.name = 'map_plane'"
    )


def test_map01b_map_plane_in_vault_zone():
    """MAP-01b: scene-builder.ts references VAULT_ZONE for map_plane placement."""
    # Must use _zone('VAULT_ZONE') or zonesJson-derived anchor — not hardcoded coords
    assert "VAULT_ZONE" in scene_text, (
        "scene-builder.ts must reference 'VAULT_ZONE' when placing map_plane"
    )
    assert "zonesJson" in scene_text or "zones.json" in scene_text or "_zone(" in scene_text, (
        "scene-builder.ts must import/use zones.json for map_plane position (not hardcoded)"
    )


def test_map01c_map_plane_uses_vault_center_anchor():
    """MAP-01c: map_plane position uses vault_center anchor from zones.json."""
    assert "vault_center" in scene_text, (
        "scene-builder.ts must use the 'vault_center' anchor from zones.json for map_plane position"
    )
    assert "_zoneAnchor(" in scene_text or re.search(r"anchor.*vault_center|vault_center.*anchor", scene_text), (
        "scene-builder.ts must read vault_center from zones.json anchors"
    )


# ===========================================================================
# MAP-02: LEAN_FORWARD posture wiring on map interaction
# ===========================================================================

def test_map02a_lean_forward_in_map_interaction():
    """MAP-02a: LEAN_FORWARD posture is set when map interaction begins (pointerdown)."""
    # Find the pointerdown handler section and verify LEAN_FORWARD appears near lasso.startDrag
    # We look for LEAN_FORWARD appearing in the same logical block as mapLasso.startDrag
    pointerdown_match = re.search(
        r"pointerdown.*?mapLasso\.startDrag",
        main_text, re.DOTALL
    )
    assert pointerdown_match, (
        "main.ts must wire mapLasso.startDrag inside a pointerdown handler"
    )
    block = pointerdown_match.group()
    assert "LEAN_FORWARD" in block, (
        "main.ts must call postureCtrl.setPosture('LEAN_FORWARD') in the map pointerdown interaction path"
    )


def test_map02b_lean_forward_not_startup_posture():
    """MAP-02b: LEAN_FORWARD is not the default/startup posture in camera.ts."""
    camera_src = ROOT / "client" / "src" / "camera.ts"
    camera_text = camera_src.read_text(encoding="utf-8")
    # The constructor sets STANDARD as the startup posture
    assert re.search(r"currentPosture.*['\"]STANDARD['\"]|POSTURES\.STANDARD", camera_text), (
        "camera.ts must initialize to STANDARD posture, not LEAN_FORWARD"
    )
    # LEAN_FORWARD must not appear as the init/startup value
    init_block = re.search(r"constructor.*?this\._applyOptics", camera_text, re.DOTALL)
    if init_block:
        assert "LEAN_FORWARD" not in init_block.group(), (
            "camera.ts constructor must not start in LEAN_FORWARD posture"
        )


def test_map02c_lean_forward_on_pending_map_events():
    """MAP-02c: LEAN_FORWARD is wired to pending_map_* WS events in main.ts."""
    assert re.search(r"pending_map_aoe.*LEAN_FORWARD|LEAN_FORWARD.*pending_map_aoe", main_text, re.DOTALL), (
        "main.ts must call setPosture('LEAN_FORWARD') when pending_map_aoe fires"
    )
    assert re.search(r"pending_map_point.*LEAN_FORWARD|LEAN_FORWARD.*pending_map_point", main_text, re.DOTALL), (
        "main.ts must call setPosture('LEAN_FORWARD') when pending_map_point fires"
    )
    assert re.search(r"pending_map_search.*LEAN_FORWARD|LEAN_FORWARD.*pending_map_search", main_text, re.DOTALL), (
        "main.ts must call setPosture('LEAN_FORWARD') when pending_map_search fires"
    )


# ===========================================================================
# MAP-03: PENDING-gate on overlay activation (simulation)
# ===========================================================================

class MapOverlayGateSim:
    """Python simulation of MapOverlayManager PENDING gate logic (mirrors map-overlay.ts)."""

    PENDING_AOE    = 'PENDING_AOE'
    PENDING_POINT  = 'PENDING_POINT'
    PENDING_SEARCH = 'PENDING_SEARCH'

    def __init__(self):
        self._active_pending = None
        self._aoe_visible    = False
        self._measure_visible = False
        self._area_visible   = False

    def set_pending(self, kind: str) -> None:
        self._active_pending = kind

    def clear_pending(self) -> None:
        self._active_pending = None
        self._aoe_visible    = False
        self._measure_visible = False
        self._area_visible   = False

    @property
    def active_pending(self) -> str | None:
        return self._active_pending

    def show_aoe(self, data: dict) -> None:
        if self._active_pending != self.PENDING_AOE:
            return  # PENDING gate: no-op
        self._aoe_visible = True

    def hide_aoe(self) -> None:
        self._aoe_visible = False

    def show_measure(self, from_x, from_y, to_x, to_y) -> None:
        if self._active_pending != self.PENDING_POINT:
            return  # PENDING gate: no-op
        self._measure_visible = True

    def hide_measure(self) -> None:
        self._measure_visible = False

    def show_area(self, squares, color_hex=None) -> None:
        if self._active_pending != self.PENDING_SEARCH:
            return  # PENDING gate: no-op
        self._area_visible = True

    def clear_area(self) -> None:
        self._area_visible = False

    @property
    def aoe_visible(self) -> bool:   return self._aoe_visible
    @property
    def measure_visible(self) -> bool: return self._measure_visible
    @property
    def area_visible(self) -> bool:  return self._area_visible


def test_map03a_no_pending_no_overlay():
    """MAP-03a: No overlay activates when there is no active PENDING."""
    mgr = MapOverlayGateSim()
    # No PENDING set — all show calls are no-ops
    mgr.show_aoe({'shape': 'circle', 'origin_x': 0, 'origin_y': 0})
    mgr.show_measure(0, 0, 2, 2)
    mgr.show_area([[0, 0], [1, 1]])
    assert not mgr.aoe_visible,     "showAoE must not activate without PENDING_AOE"
    assert not mgr.measure_visible, "showMeasure must not activate without PENDING_POINT"
    assert not mgr.area_visible,    "showArea must not activate without PENDING_SEARCH"


def test_map03b_pending_aoe_activates_aoe_only():
    """MAP-03b: PENDING_AOE activates showAoE; measure and area remain gated."""
    mgr = MapOverlayGateSim()
    mgr.set_pending('PENDING_AOE')
    mgr.show_aoe({'shape': 'circle', 'origin_x': 0, 'origin_y': 0})
    mgr.show_measure(0, 0, 2, 2)   # wrong PENDING kind — no-op
    mgr.show_area([[0, 0]])         # wrong PENDING kind — no-op
    assert mgr.aoe_visible,          "showAoE must activate when PENDING_AOE is set"
    assert not mgr.measure_visible,  "showMeasure must not activate under PENDING_AOE"
    assert not mgr.area_visible,     "showArea must not activate under PENDING_AOE"


def test_map03c_pending_point_activates_measure_only():
    """MAP-03c: PENDING_POINT activates showMeasure only."""
    mgr = MapOverlayGateSim()
    mgr.set_pending('PENDING_POINT')
    mgr.show_aoe({'shape': 'circle', 'origin_x': 0, 'origin_y': 0})
    mgr.show_measure(0, 0, 2, 2)
    mgr.show_area([[0, 0]])
    assert not mgr.aoe_visible,      "showAoE must not activate under PENDING_POINT"
    assert mgr.measure_visible,      "showMeasure must activate when PENDING_POINT is set"
    assert not mgr.area_visible,     "showArea must not activate under PENDING_POINT"


def test_map03d_pending_search_activates_area_only():
    """MAP-03d: PENDING_SEARCH activates showArea only."""
    mgr = MapOverlayGateSim()
    mgr.set_pending('PENDING_SEARCH')
    mgr.show_aoe({'shape': 'circle', 'origin_x': 0, 'origin_y': 0})
    mgr.show_measure(0, 0, 2, 2)
    mgr.show_area([[0, 0]])
    assert not mgr.aoe_visible,      "showAoE must not activate under PENDING_SEARCH"
    assert not mgr.measure_visible,  "showMeasure must not activate under PENDING_SEARCH"
    assert mgr.area_visible,         "showArea must activate when PENDING_SEARCH is set"


def test_map03e_clear_pending_hides_overlays():
    """MAP-03e: clearPending() clears all active overlays and re-locks gate."""
    mgr = MapOverlayGateSim()
    mgr.set_pending('PENDING_AOE')
    mgr.show_aoe({'shape': 'circle', 'origin_x': 0, 'origin_y': 0})
    assert mgr.aoe_visible, "Precondition: AoE must be visible before clear"
    mgr.clear_pending()
    assert not mgr.aoe_visible,     "AoE must be hidden after clearPending()"
    assert mgr.active_pending is None, "active_pending must be None after clearPending()"
    # Gate re-locked: subsequent show is a no-op
    mgr.show_aoe({'shape': 'circle', 'origin_x': 0, 'origin_y': 0})
    assert not mgr.aoe_visible,     "showAoE must be no-op after clearPending() (gate re-locked)"


def test_map03f_pending_gate_wired_in_overlay_source():
    """MAP-03f: map-overlay.ts source contains PENDING gate checks in show methods."""
    # Each show method must have a PENDING check before activating
    assert re.search(r"showAoE.*?PENDING_AOE.*?return|PENDING_AOE.*?showAoE", overlay_text, re.DOTALL), (
        "map-overlay.ts showAoE must check for PENDING_AOE and return early if not active"
    )
    assert "activePending" in overlay_text or "_activePending" in overlay_text, (
        "map-overlay.ts must maintain an _activePending state field"
    )
    assert "setPending" in overlay_text, (
        "map-overlay.ts must export setPending() method"
    )
    assert "clearPending" in overlay_text, (
        "map-overlay.ts must export clearPending() method"
    )


# ===========================================================================
# MAP-04: No intent emitted without PENDING (simulation)
# ===========================================================================

class MapLassoGateSim:
    """Python simulation of MapLassoManager PENDING gate logic (mirrors map-lasso.ts)."""

    def __init__(self):
        self._is_dragging    = False
        self._points         = []
        self._intents        = []
        self._lasso_visible  = False
        self._active_pending = None

    def set_pending(self, kind: str) -> None:
        self._active_pending = kind

    def clear_pending(self) -> None:
        self._active_pending = None

    @property
    def active_pending(self) -> str | None:
        return self._active_pending

    def start_drag(self, x: float, z: float) -> None:
        self._is_dragging = True
        self._points = [{'x': x, 'z': z}]
        self._lasso_visible = False

    def update_drag(self, x: float, z: float) -> None:
        if not self._is_dragging:
            return
        self._points.append({'x': x, 'z': z})
        if len(self._points) >= 2:
            self._lasso_visible = True

    def end_drag(self, kind: str = 'SEARCH') -> None:
        if not self._is_dragging:
            return
        self._is_dragging = False
        if len(self._points) < 2:
            self._lasso_visible = False
            return
        # Close polygon
        self._points.append(self._points[0])
        # PENDING gate: intent only if pending is active
        if self._active_pending is not None:
            self._intents.append({'kind': kind, 'polygon': list(self._points)})
        # Lasso is still drawn (cosmetic) regardless

    @property
    def is_dragging(self)   -> bool: return self._is_dragging
    @property
    def point_count(self)   -> int:  return len(self._points)
    @property
    def lasso_visible(self) -> bool: return self._lasso_visible
    @property
    def intent_count(self)  -> int:  return len(self._intents)


def test_map04a_no_intent_without_pending():
    """MAP-04a: Drag with no active PENDING emits zero intents."""
    lasso = MapLassoGateSim()
    # No setPending call
    lasso.start_drag(0, 0)
    lasso.update_drag(2, 0)
    lasso.update_drag(2, 2)
    lasso.end_drag('SEARCH')
    assert lasso.intent_count == 0, (
        f"No MapAreaIntent must be emitted without active PENDING; got {lasso.intent_count}"
    )


def test_map04b_lasso_drawn_without_pending():
    """MAP-04b: Lasso is still drawn (cosmetic) even without PENDING."""
    lasso = MapLassoGateSim()
    lasso.start_drag(0, 0)
    lasso.update_drag(2, 0)
    lasso.update_drag(2, 2)
    assert lasso.lasso_visible, (
        "Lasso overlay must be drawn cosmetically even without PENDING (no-intent, visual only)"
    )


def test_map04c_intent_emitted_with_pending_search():
    """MAP-04c: Drag with PENDING_SEARCH active emits MapAreaIntent with kind=SEARCH."""
    lasso = MapLassoGateSim()
    lasso.set_pending('PENDING_SEARCH')
    lasso.start_drag(0, 0)
    lasso.update_drag(2, 0)
    lasso.update_drag(2, 2)
    lasso.end_drag('SEARCH')
    assert lasso.intent_count == 1, (
        f"MapAreaIntent must be emitted with PENDING_SEARCH; got {lasso.intent_count}"
    )
    assert lasso._intents[0]['kind'] == 'SEARCH', (
        f"Intent kind must be SEARCH; got {lasso._intents[0]['kind']}"
    )


def test_map04d_no_point_intent_without_pending():
    """MAP-04d: Single click on map with no PENDING emits zero intents."""
    lasso = MapLassoGateSim()
    # Click = start + end with < 2 points → no intent regardless
    lasso.start_drag(0, 0)
    lasso.end_drag('SEARCH')
    assert lasso.intent_count == 0, (
        "Single click (< 2 points) must not emit any intent"
    )


def test_map04e_pending_gate_wired_in_lasso_source():
    """MAP-04e: map-lasso.ts source contains PENDING gate check in endDrag."""
    assert "_activePending" in lasso_text or "activePending" in lasso_text, (
        "map-lasso.ts must maintain an _activePending state field"
    )
    assert "setPending" in lasso_text, (
        "map-lasso.ts must export setPending() method"
    )
    assert "clearPending" in lasso_text, (
        "map-lasso.ts must export clearPending() method"
    )
    # endDrag must check _activePending before emitting
    end_drag_match = re.search(r"endDrag.*?(?=private|public|dispose|$)", lasso_text, re.DOTALL)
    assert end_drag_match, "map-lasso.ts must define endDrag method"
    end_drag_block = end_drag_match.group()
    assert "_activePending" in end_drag_block or "activePending" in end_drag_block, (
        "map-lasso.ts endDrag must check _activePending before calling _onIntent"
    )


# ===========================================================================
# MAP-05: Overlays are TTL-only — nothing persisted
# ===========================================================================

def test_map05a_no_localstorage_in_overlay():
    """MAP-05a: map-overlay.ts does not use localStorage or sessionStorage."""
    assert "localStorage" not in overlay_text, (
        "map-overlay.ts must NOT use localStorage — overlays are ephemeral TTL-only"
    )
    assert "sessionStorage" not in overlay_text, (
        "map-overlay.ts must NOT use sessionStorage — overlays are ephemeral TTL-only"
    )
    assert "JSON.stringify" not in overlay_text, (
        "map-overlay.ts must NOT serialize overlay state (JSON.stringify)"
    )


def test_map05b_no_localstorage_in_lasso():
    """MAP-05b: map-lasso.ts does not use localStorage or sessionStorage."""
    assert "localStorage" not in lasso_text, (
        "map-lasso.ts must NOT use localStorage — lasso is ephemeral TTL-only"
    )
    assert "sessionStorage" not in lasso_text, (
        "map-lasso.ts must NOT use sessionStorage — lasso is ephemeral TTL-only"
    )
    assert "JSON.stringify" not in lasso_text, (
        "map-lasso.ts must NOT serialize lasso state"
    )


def test_map05c_overlay_state_not_exported_as_getter():
    """MAP-05c: No overlay internal state (mesh/visibility) is returned from exported functions."""
    # Exported members of MapOverlayManager should be setters/actions, not state accessors
    # isVisible getters on sub-classes are OK (used for pulse animation), but
    # _aoe, _measure, _area meshes must not be exported from the class
    assert not re.search(r"export.*_aoe|export.*_measure|export.*_area", overlay_text), (
        "Internal overlay mesh state (_aoe, _measure, _area) must not be directly exported"
    )


# ===========================================================================
# MAP-06: No permanent drawing path
# ===========================================================================

def test_map06a_no_save_strokes():
    """MAP-06a: map-overlay.ts has no saveStrokes or persistent ink mechanism."""
    assert "saveStrokes" not in overlay_text, (
        "map-overlay.ts must not have saveStrokes — no persistent drawing"
    )
    assert "saveStroke" not in overlay_text, (
        "map-overlay.ts must not have saveStroke"
    )


def test_map06b_no_canvas_texture_in_overlay():
    """MAP-06b: map-overlay.ts has no CanvasTexture — overlays are Three.js geometry, not canvas paint."""
    assert "CanvasTexture" not in overlay_text, (
        "map-overlay.ts must not use CanvasTexture — overlays must be Three.js geometry, not canvas"
    )
    assert "canvas-to-image" not in overlay_text.lower(), (
        "map-overlay.ts must not export canvas content"
    )


def test_map06c_no_canvas_texture_in_lasso():
    """MAP-06c: map-lasso.ts has no CanvasTexture or persistent canvas rendering."""
    assert "CanvasTexture" not in lasso_text, (
        "map-lasso.ts must not use CanvasTexture"
    )
    assert "toDataURL" not in lasso_text, (
        "map-lasso.ts must not export lasso as image"
    )


def test_map06d_no_export_image_in_overlay():
    """MAP-06d: No canvas-to-image export path in overlay files."""
    for name, text in [("map-overlay.ts", overlay_text), ("map-lasso.ts", lasso_text)]:
        assert "toDataURL" not in text, (
            f"{name} must not use toDataURL — no canvas-to-image export"
        )
        assert "toBlob" not in text, (
            f"{name} must not use toBlob — no persistent image capture"
        )


# ===========================================================================
# MAP-07: Existing lasso + fog gates remain green (regression)
# ===========================================================================

def test_map07_lasso_regression():
    """MAP-07a: tests/test_ui_gate_lasso.py — all 4 tests pass (regression guard)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         str(ROOT / "tests" / "test_ui_gate_lasso.py"),
         "-v", "--tb=short", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"test_ui_gate_lasso.py regression FAILED:\n{result.stdout}\n{result.stderr}"
    )


def test_map07_lasso_fade_regression():
    """MAP-07b: tests/test_ui_gate_lasso_fade.py — all 4 tests pass (regression guard)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         str(ROOT / "tests" / "test_ui_gate_lasso_fade.py"),
         "-v", "--tb=short", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"test_ui_gate_lasso_fade.py regression FAILED:\n{result.stdout}\n{result.stderr}"
    )


def test_map07_fog_regression():
    """MAP-07c: tests/test_ui_gate_fog.py — all fog tests pass (regression guard)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         str(ROOT / "tests" / "test_ui_gate_fog.py"),
         "-v", "--tb=short", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"test_ui_gate_fog.py regression FAILED:\n{result.stdout}\n{result.stderr}"
    )
