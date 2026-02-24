"""Gate UI-VISREG-PLAYWRIGHT — Visual Regression Harness structural checks (10/10).

All checks are static (file existence + content inspection).
No browser required. No committed baselines required.

VR-01  visual-regression.spec.ts exists
VR-02  Spec uses toHaveScreenshot()
VR-03  Spec tests all 4 posture keys (1, 2, 3, 4)
VR-04  Spec tests vault REST state
VR-05  Spec tests vault COMBAT state
VR-06  Spec sets 1920×1080 viewport explicitly
VR-07  test:visreg script exists in package.json
VR-08  test:visreg:update script exists in package.json
VR-09  test:visreg does NOT contain --update-snapshots
VR-10  test:visreg:update DOES contain --update-snapshots

Authority: WO-UI-VISREG-PLAYWRIGHT-001
Run with: python -m pytest tests/test_ui_visreg_playwright_gate.py -v
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

ROOT   = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLIENT = ROOT / 'client'
SPEC   = CLIENT / 'tests' / 'playwright' / 'visual-regression.spec.ts'
PKG    = CLIENT / 'package.json'


def _spec() -> str:
    assert SPEC.exists(), f"VR-01: {SPEC} not found"
    return SPEC.read_text(encoding='utf-8')


def _pkg() -> dict:
    assert PKG.exists(), f"package.json not found at {PKG}"
    return json.loads(PKG.read_text(encoding='utf-8'))


# ---------------------------------------------------------------------------
# VR-01 — spec file exists
# ---------------------------------------------------------------------------

def test_vr01_spec_exists():
    """VR-01: visual-regression.spec.ts must exist."""
    assert SPEC.exists(), \
        f"VR-01: {SPEC} not found — create the spec per WO-UI-VISREG-PLAYWRIGHT-001 §3.1"


# ---------------------------------------------------------------------------
# VR-02 — spec uses toHaveScreenshot()
# ---------------------------------------------------------------------------

def test_vr02_spec_uses_to_have_screenshot():
    """VR-02: Spec must call toHaveScreenshot() — not manual screenshot + file save."""
    src = _spec()
    assert 'toHaveScreenshot' in src, \
        "VR-02: visual-regression.spec.ts does not contain toHaveScreenshot — " \
        "must use Playwright's built-in baseline comparison"


# ---------------------------------------------------------------------------
# VR-03 — spec tests all 4 posture keys
# ---------------------------------------------------------------------------

def test_vr03_spec_covers_all_four_posture_keys():
    """VR-03: Spec must reference hotkeys '1', '2', '3', '4' for all postures."""
    src = _spec()
    for key in ('1', '2', '3', '4'):
        assert f"'{key}'" in src or f'"{key}"' in src, \
            f"VR-03: posture key '{key}' not found in visual-regression.spec.ts — " \
            f"all 4 postures (STANDARD/DOWN/LEAN_FORWARD/DICE_TRAY) must be covered"


# ---------------------------------------------------------------------------
# VR-04 — spec tests vault REST state
# ---------------------------------------------------------------------------

def test_vr04_spec_covers_vault_rest():
    """VR-04: Spec must include a vault REST state snapshot."""
    src = _spec()
    assert 'vault-REST' in src or 'vault: REST' in src, \
        "VR-04: vault REST snapshot missing from visual-regression.spec.ts — " \
        "add test('vault: REST (cover visible)', ...)"


# ---------------------------------------------------------------------------
# VR-05 — spec tests vault COMBAT state
# ---------------------------------------------------------------------------

def test_vr05_spec_covers_vault_combat():
    """VR-05: Spec must include a vault COMBAT state snapshot."""
    src = _spec()
    assert 'vault-COMBAT' in src or 'vault: COMBAT' in src, \
        "VR-05: vault COMBAT snapshot missing from visual-regression.spec.ts — " \
        "add test('vault: COMBAT (cover hidden)', ...)"


# ---------------------------------------------------------------------------
# VR-06 — spec sets 1920×1080 viewport explicitly
# ---------------------------------------------------------------------------

def test_vr06_spec_sets_1920x1080_viewport():
    """VR-06: Spec must set viewport to 1920×1080 — must not rely on device default (1280×720)."""
    src = _spec()
    assert '1920' in src and '1080' in src, \
        "VR-06: visual-regression.spec.ts does not set explicit 1920×1080 viewport — " \
        "devices['Desktop Chrome'] defaults to 1280×720; add setViewportSize({width:1920,height:1080})"


# ---------------------------------------------------------------------------
# VR-07 — test:visreg script exists
# ---------------------------------------------------------------------------

def test_vr07_test_visreg_script_exists():
    """VR-07: package.json must have a test:visreg script."""
    scripts = _pkg().get('scripts', {})
    assert 'test:visreg' in scripts, \
        "VR-07: 'test:visreg' not in client/package.json scripts — " \
        "add: \"test:visreg\": \"playwright test visual-regression.spec.ts\""


# ---------------------------------------------------------------------------
# VR-08 — test:visreg:update script exists
# ---------------------------------------------------------------------------

def test_vr08_test_visreg_update_script_exists():
    """VR-08: package.json must have a test:visreg:update script."""
    scripts = _pkg().get('scripts', {})
    assert 'test:visreg:update' in scripts, \
        "VR-08: 'test:visreg:update' not in client/package.json scripts — " \
        "add: \"test:visreg:update\": \"playwright test visual-regression.spec.ts --update-snapshots\""


# ---------------------------------------------------------------------------
# VR-09 — test:visreg does NOT include --update-snapshots
# ---------------------------------------------------------------------------

def test_vr09_test_visreg_no_update_snapshots():
    """VR-09: test:visreg (CI command) must NOT include --update-snapshots."""
    scripts = _pkg().get('scripts', {})
    visreg_cmd = scripts.get('test:visreg', '')
    assert '--update-snapshots' not in visreg_cmd, \
        f"VR-09: test:visreg contains '--update-snapshots': {visreg_cmd!r} — " \
        f"CI command must be read-only; baseline updates require explicit operator step (test:visreg:update)"


# ---------------------------------------------------------------------------
# VR-10 — test:visreg:update DOES include --update-snapshots
# ---------------------------------------------------------------------------

def test_vr10_test_visreg_update_has_update_snapshots():
    """VR-10: test:visreg:update (operator command) must include --update-snapshots."""
    scripts = _pkg().get('scripts', {})
    update_cmd = scripts.get('test:visreg:update', '')
    assert '--update-snapshots' in update_cmd, \
        f"VR-10: test:visreg:update does not contain '--update-snapshots': {update_cmd!r} — " \
        f"operator baseline update command must include --update-snapshots"
