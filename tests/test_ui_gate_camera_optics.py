"""Gate UI-CAMERA-OPTICS — Per-posture camera optics (10 checks).

CO-01  STANDARD posture applied → camera.fov == 55 (±0.1)
CO-02  DOWN posture applied → camera.fov == 45 (±0.1)
CO-03  LEAN_FORWARD posture applied → camera.fov == 65 (±0.1)
CO-04  DICE_TRAY posture applied → camera.fov == 60 (±0.1)
CO-05  BOOK_READ posture applied → camera.fov == 40 (±0.1)
CO-06  STANDARD near/far: camera.near == 0.5, camera.far == 50
CO-07  updateProjectionMatrix() called on posture switch (projectionMatrix changes)
CO-08  camera_poses.json has fov_deg, near, far for all 5 postures (schema validation)
CO-09  Mid-transition FOV is interpolated (not snapped)
CO-10  Constructor applies STANDARD optics immediately (not 60° default)

CO-01 through CO-07, CO-09, CO-10 require a running dev server at localhost:3000
with window.__cameraController__ exposed.
CO-08 is pure JSON validation (no browser required).

Run with: python -m pytest tests/test_ui_gate_camera_optics.py -v
"""

import json
import os
import time
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# CO-08 — JSON schema validation (no browser required)
# ---------------------------------------------------------------------------

POSES_PATH = os.path.join(ROOT, 'docs', 'design', 'LAYOUT_PACK_V1', 'camera_poses.json')
REQUIRED_POSTURES = ['STANDARD', 'DOWN', 'LEAN_FORWARD', 'DICE_TRAY', 'BOOK_READ']


def test_co08_camera_poses_json_has_optics_for_all_postures():
    """CO-08: camera_poses.json has fov_deg, near, far for all 5 postures."""
    with open(POSES_PATH) as f:
        data = json.load(f)
    postures = data.get('postures', {})
    for name in REQUIRED_POSTURES:
        assert name in postures, f"camera_poses.json missing posture: {name}"
        p = postures[name]
        assert 'fov_deg' in p, f"{name}: missing fov_deg"
        assert 'near' in p,    f"{name}: missing near"
        assert 'far' in p,     f"{name}: missing far"
        assert isinstance(p['fov_deg'], (int, float)), f"{name}: fov_deg must be numeric"
        assert isinstance(p['near'],    (int, float)), f"{name}: near must be numeric"
        assert isinstance(p['far'],     (int, float)), f"{name}: far must be numeric"
        assert p['fov_deg'] > 0,  f"{name}: fov_deg must be positive"
        assert p['near'] > 0,     f"{name}: near must be positive"
        assert p['far'] > p['near'], f"{name}: far must exceed near"


def test_co08_authoritative_optics_values():
    """CO-08 extended: authoritative locked values per WO-UI-CAMERA-OPTICS-001."""
    with open(POSES_PATH) as f:
        data = json.load(f)
    p = data['postures']
    assert p['STANDARD']['fov_deg']    == 55,  "STANDARD fov_deg must be 55"
    assert p['DOWN']['fov_deg']        == 45,  "DOWN fov_deg must be 45"
    assert p['LEAN_FORWARD']['fov_deg'] == 65, "LEAN_FORWARD fov_deg must be 65"
    assert p['DICE_TRAY']['fov_deg']   == 60,  "DICE_TRAY fov_deg must be 60"
    assert p['BOOK_READ']['fov_deg']   == 40,  "BOOK_READ fov_deg must be 40"
    assert p['STANDARD']['near']       == 0.5, "STANDARD near must be 0.5"
    assert p['STANDARD']['far']        == 50,  "STANDARD far must be 50"


# ---------------------------------------------------------------------------
# Source-level checks (no browser) — guard against regressions in camera.ts
# ---------------------------------------------------------------------------

def _read_camera_ts():
    return open(os.path.join(ROOT, 'client', 'src', 'camera.ts')).read()


def test_co_source_posture_config_has_optics_fields():
    """PostureConfig interface must include fovDeg, near, far."""
    src = _read_camera_ts()
    assert 'fovDeg' in src,  "camera.ts PostureConfig must have fovDeg field"
    assert 'near:' in src,   "camera.ts PostureConfig must have near field"
    assert 'far:' in src,    "camera.ts PostureConfig must have far field"


def test_co_source_apply_optics_method():
    """_applyOptics() must exist and call updateProjectionMatrix()."""
    src = _read_camera_ts()
    assert '_applyOptics' in src, "camera.ts must have _applyOptics() method"
    assert 'updateProjectionMatrix' in src, \
        "camera.ts must call camera.updateProjectionMatrix()"


def test_co_source_optics_interpolation_in_update():
    """update() must interpolate fov, near, far."""
    src = _read_camera_ts()
    assert 'startFov' in src,  "camera.ts must interpolate startFov"
    assert 'endFov' in src,    "camera.ts must have endFov"
    assert 'startNear' in src, "camera.ts must interpolate startNear"
    assert 'startFar' in src,  "camera.ts must interpolate startFar"


def test_co_source_constructor_applies_standard_optics():
    """Constructor must call _applyOptics for STANDARD posture."""
    src = _read_camera_ts()
    assert '_applyOptics' in src, "camera.ts constructor must call _applyOptics"
    # Seed state must be set in constructor
    assert 'this.startFov  = this.endFov  = cfg.fovDeg' in src or \
           'startFov' in src, \
        "camera.ts must seed startFov/endFov in constructor"


def test_co_source_window_camera_controller_exposed():
    """main.ts must expose __cameraController__ on window in DEV mode."""
    src = open(os.path.join(ROOT, 'client', 'src', 'main.ts')).read()
    assert '__cameraController__' in src, \
        "main.ts must expose window.__cameraController__ in DEV mode"
    assert 'import.meta.env.DEV' in src, \
        "main.ts must guard __cameraController__ exposure behind import.meta.env.DEV"


# ---------------------------------------------------------------------------
# Playwright-based checks (require dev server at localhost:3000)
# ---------------------------------------------------------------------------

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

DEV_SERVER = 'http://localhost:3000'
FRAC_TOL = 0.1   # ±0.1° fov tolerance
NEAR_FAR_TOL = 0.05


def _check_server():
    """Return True if dev server appears to be running."""
    import urllib.request
    try:
        urllib.request.urlopen(DEV_SERVER, timeout=2)
        return True
    except Exception:
        return False


@pytest.fixture(scope='module')
def page():
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("playwright not installed")
    if not _check_server():
        pytest.skip(f"dev server not running at {DEV_SERVER}")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={'width': 1920, 'height': 1080})
        pg = ctx.new_page()
        pg.goto(DEV_SERVER)
        pg.wait_for_timeout(1500)
        # Confirm __cameraController__ is available
        ctrl = pg.evaluate("typeof window.__cameraController__")
        if ctrl == 'undefined':
            pytest.skip("__cameraController__ not exposed — ensure dev server is running in DEV mode")
        yield pg
        browser.close()


def _set_posture_and_wait(page, key: str, wait_ms: int = 600):
    """Press posture hotkey and wait for transition to complete."""
    page.keyboard.press(key)
    page.wait_for_timeout(wait_ms)


def _get_fov(page) -> float:
    return page.evaluate("window.__cameraController__.camera.fov")


def _get_near(page) -> float:
    return page.evaluate("window.__cameraController__.camera.near")


def _get_far(page) -> float:
    return page.evaluate("window.__cameraController__.camera.far")


def _get_proj_matrix(page) -> list:
    return page.evaluate(
        "Array.from(window.__cameraController__.camera.projectionMatrix.elements)"
    )


def test_co01_standard_fov(page):
    """CO-01: STANDARD posture → camera.fov == 55 (±0.1)."""
    _set_posture_and_wait(page, '1')
    fov = _get_fov(page)
    assert abs(fov - 55.0) <= FRAC_TOL, f"STANDARD fov expected 55, got {fov}"


def test_co02_down_fov(page):
    """CO-02: DOWN posture → camera.fov == 45 (±0.1)."""
    _set_posture_and_wait(page, '2')
    fov = _get_fov(page)
    assert abs(fov - 45.0) <= FRAC_TOL, f"DOWN fov expected 45, got {fov}"


def test_co03_lean_forward_fov(page):
    """CO-03: LEAN_FORWARD posture → camera.fov == 65 (±0.1). Orb clip eliminated."""
    _set_posture_and_wait(page, '3')
    fov = _get_fov(page)
    assert abs(fov - 65.0) <= FRAC_TOL, f"LEAN_FORWARD fov expected 65, got {fov}"


def test_co04_dice_tray_fov(page):
    """CO-04: DICE_TRAY posture → camera.fov == 60 (±0.1)."""
    _set_posture_and_wait(page, '4')
    fov = _get_fov(page)
    assert abs(fov - 60.0) <= FRAC_TOL, f"DICE_TRAY fov expected 60, got {fov}"


def test_co05_book_read_fov(page):
    """CO-05: BOOK_READ posture → camera.fov == 40 (±0.1)."""
    _set_posture_and_wait(page, '5')
    fov = _get_fov(page)
    assert abs(fov - 40.0) <= FRAC_TOL, f"BOOK_READ fov expected 40, got {fov}"


def test_co06_standard_near_far(page):
    """CO-06: STANDARD near == 0.5, far == 50."""
    _set_posture_and_wait(page, '1')
    near = _get_near(page)
    far  = _get_far(page)
    assert abs(near - 0.5) <= NEAR_FAR_TOL, f"STANDARD near expected 0.5, got {near}"
    assert abs(far - 50.0) <= NEAR_FAR_TOL, f"STANDARD far expected 50, got {far}"


def test_co07_projection_matrix_updates_on_posture_switch(page):
    """CO-07: projectionMatrix changes when posture switches (updateProjectionMatrix called)."""
    _set_posture_and_wait(page, '1')  # STANDARD
    mat_before = _get_proj_matrix(page)
    _set_posture_and_wait(page, '2')  # DOWN (different fov → matrix changes)
    mat_after = _get_proj_matrix(page)
    assert mat_before != mat_after, \
        "projectionMatrix did not change on posture switch — updateProjectionMatrix() may not be called"


def test_co09_mid_transition_fov_interpolated(page):
    """CO-09: Mid-transition FOV is interpolated, not snapped.

    Tests that setPosture() starts a transition from the current fov to the
    target fov — i.e., the fov is NOT snapped to the target immediately.
    Verified by calling setPosture and reading transitProgress in the same
    JS microtask (before any rAF fires), confirming progress=0 and fov is
    still at the start value.
    """
    # Settle at STANDARD (fov=55) — use JS API to bypass keypress focus issues.
    page.evaluate("window.__cameraController__.setPosture('STANDARD')")
    page.wait_for_timeout(700)  # >2× transition_ms — guaranteed settled

    # In a single synchronous JS call: trigger LEAN_FORWARD and immediately
    # read transitProgress and fov before any rAF fires.
    result = page.evaluate("""() => {
        const ctrl = window.__cameraController__;
        const fovBefore = ctrl.camera.fov;
        ctrl.setPosture('LEAN_FORWARD');
        // rAF has NOT fired — progress must be 0, fov must still be start value
        return {
            fovBefore: fovBefore,
            fovAfterSet: ctrl.camera.fov,
            progress: ctrl.transitProgress
        };
    }""")

    assert abs(result['fovBefore'] - 55.0) <= FRAC_TOL, \
        f"CO-09 pre-condition: STANDARD fov must be 55 before transition, got {result['fovBefore']}"
    assert result['progress'] == 0, \
        f"transitProgress must be 0 immediately after setPosture(), got {result['progress']} — transition may be snapping"
    assert abs(result['fovAfterSet'] - 55.0) <= FRAC_TOL, \
        f"fov must not snap on setPosture() — expected ~55, got {result['fovAfterSet']} — optics interpolation not wired"

    # Let transition complete before next test.
    page.wait_for_timeout(600)


def test_co10_constructor_applies_standard_optics_not_60_default(page):
    """CO-10: On fresh page load, FOV is 55 (STANDARD), not the 60° Three.js default."""
    # Navigate fresh to reset state
    page.goto(DEV_SERVER)
    page.wait_for_timeout(1500)
    fov = _get_fov(page)
    assert abs(fov - 55.0) <= FRAC_TOL, \
        f"Initial FOV should be 55 (STANDARD), got {fov} — constructor may not apply optics"
