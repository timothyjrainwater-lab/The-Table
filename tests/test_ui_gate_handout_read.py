"""
Gate UI-HANDOUT-READ: WO-UI-HANDOUT-READ-001 — Fullscreen handout read overlay.

Tests (4):
  HR-01: index.html contains #handout-read-overlay div
  HR-02: handout-object.ts exports getHandoutCanvas method on HandoutManager
  HR-03: main.ts wires handoutReadOverlay to show on handout click
  HR-04: main.ts wires click-to-dismiss on handoutReadOverlay
"""

import re
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
HTML  = ROOT / "client" / "index.html"
HANDOUT_SRC = ROOT / "client" / "src" / "handout-object.ts"
MAIN_SRC    = ROOT / "client" / "src" / "main.ts"

html_text     = HTML.read_text(encoding="utf-8")
handout_text  = HANDOUT_SRC.read_text(encoding="utf-8")
main_text     = MAIN_SRC.read_text(encoding="utf-8")


def test_hr01_overlay_div_in_html():
    """HR-01: index.html contains #handout-read-overlay element."""
    assert 'id="handout-read-overlay"' in html_text, (
        "index.html must contain <div id=\"handout-read-overlay\">"
    )


def test_hr02_get_handout_canvas_on_manager():
    """HR-02: HandoutManager has getHandoutCanvas method returning HTMLCanvasElement | null."""
    assert "getHandoutCanvas" in handout_text, (
        "HandoutManager must expose getHandoutCanvas(handout_id: string): HTMLCanvasElement | null"
    )
    assert "HTMLCanvasElement" in handout_text, (
        "getHandoutCanvas must declare HTMLCanvasElement return type"
    )


def test_hr03_main_shows_overlay_on_handout_click():
    """HR-03: main.ts shows the handout read overlay when a handout is clicked."""
    assert "handoutReadOverlay" in main_text, (
        "main.ts must reference handoutReadOverlay"
    )
    assert "handoutReadOverlay.style.display = 'flex'" in main_text, (
        "main.ts must set handoutReadOverlay display to flex on handout click"
    )
    # Verify the show happens inside the handoutId branch
    handout_click_block = re.search(
        r"const handoutId = handoutMgr\.handleClick.*?return;\s*\}",
        main_text, re.DOTALL
    )
    assert handout_click_block, "handout click block not found in main.ts"
    assert "handoutReadOverlay" in handout_click_block.group(), (
        "handoutReadOverlay show must be inside the handout click handler"
    )


def test_hr04_main_click_dismisses_overlay():
    """HR-04: main.ts wires a click event to dismiss (hide) the handout read overlay."""
    assert "handoutReadOverlay.style.display = 'none'" in main_text, (
        "main.ts must hide handoutReadOverlay on dismiss click"
    )
    # The dismiss listener must be registered on the overlay itself
    assert re.search(
        r"handoutReadOverlay.*addEventListener\('click'",
        main_text, re.DOTALL
    ), (
        "main.ts must add a click listener on handoutReadOverlay for dismiss"
    )
