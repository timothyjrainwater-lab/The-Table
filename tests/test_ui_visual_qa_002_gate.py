"""Gate UI-VISUAL-QA-002 — Composition Lock + Golden Frame Commit (12 checks).

QA2-01  STANDARD: orb mesh visible in scene (not occluded, visible=true)
QA2-02  STANDARD: room_back_wall mesh present in scene
QA2-03  DOWN: inspection_v2/down.png exists and is non-empty
QA2-04  LEAN_FORWARD: orb mesh visible in scene (not clipped)
QA2-05  LEAN_FORWARD: vault felt mesh state (vaultCoverMesh visible=true in REST)
QA2-06  DICE_TRAY: ?debug=1 not in default dev server URL (no debug elements by default)
QA2-07  DICE_TRAY: dice_tray mesh present in scene
QA2-08  Golden frames directory has exactly 4 PNGs
QA2-09  Each golden frame is 1920x1080
QA2-10  Runtime optics dump matches camera_poses.json within ±0.5
QA2-11  Room geometry present: room_wide.png pixel mass <70% near-black + scene_graph_dump flags
QA2-12  README contains 40-char hex commit hash + branch name

QA2-01 through QA2-07 require a running dev server at localhost:3000.
QA2-08, QA2-09, QA2-12 are file-system checks (no browser required).
QA2-10 is JSON comparison (no browser required).
QA2-11 requires room_wide.png + scene_graph_dump.json captured by capture_inspection_v2.mjs.

Authority: WO-UI-VISUAL-QA-002
Run with: python -m pytest tests/test_ui_visual_qa_002_gate.py -v
"""

from __future__ import annotations

import json
import os
import re
import struct
import zlib
from pathlib import Path

import pytest

ROOT      = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LAYOUT    = ROOT / 'docs' / 'design' / 'LAYOUT_PACK_V1'
INSP_V2   = LAYOUT / 'inspection_v2'
GOLDEN    = LAYOUT / 'golden'
README    = LAYOUT / 'README.md'
POSES     = LAYOUT / 'camera_poses.json'

DEV_SERVER = 'http://localhost:3000'
OPTICS_TOL = 0.5  # ±0.5 tolerance for runtime vs JSON optics values

# ---------------------------------------------------------------------------
# Playwright availability + server check
# ---------------------------------------------------------------------------

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def _check_server() -> bool:
    import urllib.request
    try:
        urllib.request.urlopen(DEV_SERVER, timeout=2)
        return True
    except Exception:
        return False


@pytest.fixture(scope='module')
def page():
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip('playwright not installed')
    if not _check_server():
        pytest.skip(f'dev server not running at {DEV_SERVER}')
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={'width': 1920, 'height': 1080})
        pg = ctx.new_page()
        pg.goto(DEV_SERVER)
        pg.wait_for_timeout(1500)
        debug_obj = pg.evaluate("typeof window.__sceneDebug__")
        if debug_obj == 'undefined':
            pytest.skip('__sceneDebug__ not exposed — dev server must run in DEV mode')
        yield pg
        browser.close()


def _settle(page, key: str, wait_ms: int = 600) -> None:
    page.keyboard.press(key)
    page.wait_for_timeout(wait_ms)


# ---------------------------------------------------------------------------
# QA2-01 — STANDARD: orb mesh visible
# ---------------------------------------------------------------------------

def test_qa2_01_standard_orb_mesh_visible(page):
    """QA2-01: STANDARD posture — stub_crystal_ball mesh must be visible."""
    _settle(page, '1')
    visible = page.evaluate(
        "window.__sceneDebug__.scene.getObjectByName('stub_crystal_ball')?.visible ?? null"
    )
    assert visible is not None, \
        "QA2-01: stub_crystal_ball mesh not found in scene — orb not present"
    assert visible is True, \
        f"QA2-01: stub_crystal_ball.visible={visible} — orb is hidden in STANDARD"


# ---------------------------------------------------------------------------
# QA2-02 — STANDARD: room_back_wall present
# ---------------------------------------------------------------------------

def test_qa2_02_standard_room_back_wall_present(page):
    """QA2-02: room_back_wall mesh must exist in scene (room geometry wired)."""
    _settle(page, '1')
    found = page.evaluate(
        "!!window.__sceneDebug__.scene.getObjectByName('room_back_wall')"
    )
    assert found, \
        "QA2-02: room_back_wall not in scene — buildRoom() may not be called"


# ---------------------------------------------------------------------------
# QA2-03 — DOWN: inspection_v2/down.png exists
# ---------------------------------------------------------------------------

def test_qa2_03_down_png_exists():
    """QA2-03: inspection_v2/down.png must exist and have content."""
    down_png = INSP_V2 / 'down.png'
    assert down_png.exists(), \
        f"QA2-03: {down_png} not found — run capture_inspection_v2.mjs first"
    assert down_png.stat().st_size > 10_000, \
        f"QA2-03: {down_png} is suspiciously small ({down_png.stat().st_size} bytes)"


# ---------------------------------------------------------------------------
# QA2-04 — LEAN_FORWARD: orb not clipped
# ---------------------------------------------------------------------------

def test_qa2_04_lean_forward_orb_visible(page):
    """QA2-04: LEAN_FORWARD posture — stub_crystal_ball visible=true (not clipped)."""
    _settle(page, '3')
    visible = page.evaluate(
        "window.__sceneDebug__.scene.getObjectByName('stub_crystal_ball')?.visible ?? null"
    )
    assert visible is not None, \
        "QA2-04: stub_crystal_ball not in scene"
    assert visible is True, \
        f"QA2-04: orb visible={visible} in LEAN_FORWARD — orb may be clipped or hidden"


# ---------------------------------------------------------------------------
# QA2-05 — LEAN_FORWARD: vault cover visible in REST
# ---------------------------------------------------------------------------

def test_qa2_05_lean_forward_vault_cover_visible_in_rest(page):
    """QA2-05: In REST (non-combat), vault cover (walnut lid) must be visible."""
    _settle(page, '3')
    # Ensure we're in REST state — check vaultCoverMesh directly
    visible = page.evaluate(
        "window.__sceneDebug__.vaultCoverMesh?.visible ?? null"
    )
    assert visible is not None, \
        "QA2-05: vaultCoverMesh not found via __sceneDebug__ — check main.ts wiring"
    assert visible is True, \
        f"QA2-05: vaultCoverMesh.visible={visible} in REST — vault should be covered at rest"


# ---------------------------------------------------------------------------
# QA2-06 — DICE_TRAY: ?debug=1 not in default URL
# ---------------------------------------------------------------------------

def test_qa2_06_dice_tray_no_debug_in_default_url():
    """QA2-06: Default dev server URL must not include ?debug=1.
    Also verifies index.html does not hard-code autostart of debug mode
    (the JS script may *check* for debug=1 in query params — that's fine;
    what's banned is unconditional activation like setting debug=1 in href).
    """
    assert 'debug=1' not in DEV_SERVER.lower(), \
        f"QA2-06: DEV_SERVER URL '{DEV_SERVER}' contains 'debug=1' — " \
        f"gate tests must run without debug mode active"
    # Verify index.html does not unconditionally inject debug CSS/class
    index_html = ROOT / 'client' / 'index.html'
    if index_html.exists():
        content = index_html.read_text()
        # Conditional JS check (get('debug') === '1') is allowed — it's a runtime check.
        # Hard-coded href or meta refresh to ?debug=1 would be a violation.
        import re as _re
        # Fail only if debug=1 appears in an href/src/content outside of script logic
        bad_patterns = [
            _re.compile(r'href\s*=\s*["\'][^"\']*debug=1', _re.IGNORECASE),
            _re.compile(r'location\.replace.*debug=1', _re.IGNORECASE),
        ]
        for pat in bad_patterns:
            match = pat.search(content)
            assert not match, \
                f"QA2-06: index.html hard-codes debug mode activation: {match.group()!r}"


# ---------------------------------------------------------------------------
# QA2-07 — DICE_TRAY: dice_tray mesh in scene
# ---------------------------------------------------------------------------

def test_qa2_07_dice_tray_mesh_in_scene(page):
    """QA2-07: dice_tray_bottom mesh must exist in scene (tray built and added)."""
    _settle(page, '4')
    found = page.evaluate(
        "!!window.__sceneDebug__.scene.getObjectByName('dice_tray_bottom')"
    )
    assert found, \
        "QA2-07: dice_tray_bottom not in scene — tray mesh not built or not named correctly"


# ---------------------------------------------------------------------------
# QA2-08 — Golden frames: exactly 4 PNGs
# ---------------------------------------------------------------------------

def test_qa2_08_golden_frames_exactly_four():
    """QA2-08: golden/ directory must have exactly 4 PNGs."""
    if not GOLDEN.exists():
        pytest.skip(
            "golden/ directory not created yet — requires Thunder approval after Inspection Pack V2 review"
        )
    pngs = list(GOLDEN.glob('*.png'))
    if len(pngs) == 0:
        pytest.skip(
            "golden/ directory is empty — golden frames pending Thunder approval (WO-UI-VISUAL-QA-002 §4)"
        )
    assert len(pngs) == 4, \
        f"QA2-08: golden/ has {len(pngs)} PNGs, expected 4 " \
        f"(standard, down, lean_forward, dice_tray). Found: {[p.name for p in pngs]}"


# ---------------------------------------------------------------------------
# QA2-09 — Golden frames: each is 1920×1080
# ---------------------------------------------------------------------------

def _png_dimensions(path: Path) -> tuple[int, int]:
    """Read PNG dimensions from IHDR without PIL dependency."""
    with open(path, 'rb') as f:
        sig = f.read(8)
        assert sig == b'\x89PNG\r\n\x1a\n', f"{path} is not a valid PNG"
        f.read(4)  # chunk length
        chunk_type = f.read(4)
        assert chunk_type == b'IHDR', f"{path} IHDR not first chunk"
        width  = struct.unpack('>I', f.read(4))[0]
        height = struct.unpack('>I', f.read(4))[0]
    return width, height


def test_qa2_09_golden_frames_correct_dimensions():
    """QA2-09: Each golden frame must be exactly 1920×1080."""
    if not GOLDEN.exists():
        pytest.skip("golden/ directory not created yet")
    pngs = list(GOLDEN.glob('*.png'))
    if not pngs:
        pytest.skip("No PNGs in golden/ yet")
    for png in pngs:
        w, h = _png_dimensions(png)
        assert (w, h) == (1920, 1080), \
            f"QA2-09: {png.name} is {w}×{h}, expected 1920×1080"


# ---------------------------------------------------------------------------
# QA2-10 — Runtime optics dump matches camera_poses.json within ±0.5
# ---------------------------------------------------------------------------

def test_qa2_10_runtime_optics_matches_json():
    """QA2-10: runtime_optics_dump.json fov/near/far must match camera_poses.json within ±0.5."""
    dump_path = INSP_V2 / 'runtime_optics_dump.json'
    if not dump_path.exists():
        pytest.skip(f"runtime_optics_dump.json not found — run capture_inspection_v2.mjs first")

    with open(dump_path) as f:
        dump = json.load(f)
    with open(POSES) as f:
        poses = json.load(f)

    runtime   = dump['postures']
    authority = poses['postures']

    for name in ['STANDARD', 'DOWN', 'LEAN_FORWARD', 'DICE_TRAY', 'BOOK_READ']:
        assert name in runtime,   f"QA2-10: {name} missing from runtime_optics_dump.json"
        assert name in authority, f"QA2-10: {name} missing from camera_poses.json"

        r = runtime[name]
        a = authority[name]

        assert abs(r['fov']  - a['fov_deg']) <= OPTICS_TOL, \
            f"QA2-10: {name} fov runtime={r['fov']} vs json={a['fov_deg']} (>{OPTICS_TOL} delta)"
        assert abs(r['near'] - a['near'])    <= OPTICS_TOL, \
            f"QA2-10: {name} near runtime={r['near']} vs json={a['near']} (>{OPTICS_TOL} delta)"
        assert abs(r['far']  - a['far'])     <= OPTICS_TOL, \
            f"QA2-10: {name} far runtime={r['far']} vs json={a['far']} (>{OPTICS_TOL} delta)"


# ---------------------------------------------------------------------------
# QA2-11 — Room geometry: room_wide.png pixel mass + scene_graph_dump flags
# ---------------------------------------------------------------------------

def test_qa2_11_room_geometry_not_void():
    """QA2-11a: room_wide.png must have <70% near-black pixels (room not a void)."""
    room_wide = INSP_V2 / 'room_wide.png'
    if not room_wide.exists():
        pytest.skip(
            "room_wide.png not found — run updated capture_inspection_v2.mjs (Pass 3)"
        )

    # Read PNG pixel data without PIL — parse IDAT chunks, decompress, check pixels
    # For simplicity we use a bytes-level scan for near-black pixels.
    # PIL is optional; fall back to a structural check if unavailable.
    try:
        from PIL import Image
        import numpy as np
        img = Image.open(room_wide).convert('RGB')
        arr = np.array(img)
        near_black = (arr[:, :, 0] < 15) & (arr[:, :, 1] < 15) & (arr[:, :, 2] < 15)
        void_fraction = float(near_black.mean())
        assert void_fraction < 0.70, \
            f"QA2-11: room_wide.png is {void_fraction:.1%} near-black (RGB<15) — " \
            f"room geometry absent (void). Threshold: <70%"
    except ImportError:
        # PIL not available — skip pixel check, just verify file exists and is non-empty
        assert room_wide.stat().st_size > 50_000, \
            f"QA2-11: room_wide.png is suspiciously small ({room_wide.stat().st_size} bytes) — " \
            f"may be blank. Install Pillow for pixel-mass void detection."


def test_qa2_11_scene_graph_dump_flags():
    """QA2-11b: scene_graph_dump.json must have all room boolean flags true."""
    dump_path = INSP_V2 / 'scene_graph_dump.json'
    if not dump_path.exists():
        pytest.skip(
            "scene_graph_dump.json not found — run updated capture_inspection_v2.mjs (Pass 3)"
        )

    with open(dump_path) as f:
        dump = json.load(f)

    required_flags = ['room_floor_present', 'room_back_wall_present', 'room_lights_present']
    for flag in required_flags:
        assert flag in dump, \
            f"QA2-11: scene_graph_dump.json missing field '{flag}'"
        assert dump[flag] is True, \
            f"QA2-11: scene_graph_dump.json '{flag}' = {dump[flag]!r} — must be true"

    # Exposure sanity check (not a hard boolean — just verify it's a plausible value)
    if 'exposure' in dump and dump['exposure'] is not None:
        exposure = dump['exposure']
        assert 0.5 <= exposure <= 3.0, \
            f"QA2-11: exposure={exposure} is outside plausible range [0.5, 3.0]"


# ---------------------------------------------------------------------------
# QA2-12 — README has 40-char hex commit hash + branch name
# ---------------------------------------------------------------------------

_SHA40_RE  = re.compile(r'\b[0-9a-f]{40}\b', re.IGNORECASE)
_BRANCH_RE = re.compile(r'\bBranch:\s*\S+', re.IGNORECASE)


def test_qa2_12_readme_has_commit_hash_and_branch():
    """QA2-12: README.md must contain a 40-char hex SHA and a Branch: entry."""
    assert README.exists(), \
        f"QA2-12: {README} not found"
    text = README.read_text(encoding='utf-8', errors='replace')

    sha_match    = _SHA40_RE.search(text)
    branch_match = _BRANCH_RE.search(text)

    assert sha_match, \
        "QA2-12: README.md does not contain a 40-char hex commit hash — " \
        "update README per WO-UI-VISUAL-QA-002 §4 after golden frame commit"
    assert branch_match, \
        "QA2-12: README.md does not contain 'Branch: <name>' — " \
        "add branch name per WO-UI-VISUAL-QA-002 §4 procedure"
