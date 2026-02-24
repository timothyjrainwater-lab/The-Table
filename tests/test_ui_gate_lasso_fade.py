"""
Gate UI-LASSO-FADE: WO-UI-LASSO-FADE-001 — Lasso opacity fade on expiry.

Tests (4):
  LF-01: map-lasso.ts defines FADE_MS constant
  LF-02: map-lasso.ts uses requestAnimationFrame for fade loop (not instant remove)
  LF-03: map-lasso.ts sets mat.opacity to 0 (or approaches it) during fade
  LF-04: map-lasso.ts removes mesh after fade completes (not before)
"""

import re
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
LASSO_SRC = ROOT / "client" / "src" / "map-lasso.ts"

lasso_text = LASSO_SRC.read_text(encoding="utf-8")


def test_lf01_fade_ms_constant():
    """LF-01: map-lasso.ts defines FADE_MS constant."""
    assert "FADE_MS" in lasso_text, (
        "map-lasso.ts must define FADE_MS constant for lasso fade duration"
    )
    m = re.search(r"FADE_MS\s*=\s*(\d+)", lasso_text)
    assert m, "FADE_MS must be assigned a numeric value in milliseconds"
    val = int(m.group(1))
    assert 100 <= val <= 2000, f"FADE_MS={val} — expected between 100 and 2000 ms"


def test_lf02_uses_raf_for_fade():
    """LF-02: map-lasso.ts uses requestAnimationFrame for the fade animation loop."""
    assert "requestAnimationFrame" in lasso_text, (
        "map-lasso.ts must use requestAnimationFrame for smooth opacity fade animation"
    )


def test_lf03_opacity_set_to_zero():
    """LF-03: Fade loop sets mat.opacity toward 0 (lasso disappears)."""
    # Check that opacity is being manipulated in a fade context
    assert "opacity" in lasso_text, "map-lasso.ts must manipulate opacity for fade"
    # The fade should lerp from 1 to 0
    assert re.search(r"opacity\s*=.*[01]", lasso_text), (
        "map-lasso.ts must assign opacity values (1→0) during fade"
    )


def test_lf04_mesh_removed_after_fade():
    """LF-04: Mesh is removed from scene after fade completes, not before."""
    # scene.remove must appear after the rAF fade loop completes
    assert "_scene.remove(" in lasso_text or "scene.remove(" in lasso_text, (
        "map-lasso.ts must remove the lasso mesh from scene after fade completes"
    )
    # The remove call should be inside or after the rAF step function
    raf_block = re.search(
        r"requestAnimationFrame.*?(?=private|$)",
        lasso_text, re.DOTALL
    )
    if raf_block:
        block = raf_block.group()
        assert "remove(" in block, (
            "Mesh removal must occur within the rAF fade completion handler"
        )
