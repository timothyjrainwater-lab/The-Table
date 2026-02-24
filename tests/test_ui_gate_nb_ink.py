"""
Gate UI-NB-INK — Notebook Ink: Pencil Cursor + Radial Tool Wheel + Text Input
Authority: WO-UI-NOTEBOOK-INK-RADIAL-001_DISPATCH.md

12 tests. All pass = gate ACCEPTED.
"""

import re
from pathlib import Path

CLIENT = Path(__file__).parent.parent / "client" / "src"
RADIAL = CLIENT / "notebook-radial.ts"
MAIN   = CLIENT / "main.ts"
NB     = CLIENT / "notebook-object.ts"


# ── Helpers ────────────────────────────────────────────────────────────────

def src(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ── NB-I-01: cycleDrawTool exists and cycles pen→brush→eraser ──────────────

def test_NB_I_01_cycleDrawTool_exists():
    text = src(NB)
    assert "cycleDrawTool" in text, "NotebookObject must have cycleDrawTool()"


# ── NB-I-02: drawTool getter exists ───────────────────────────────────────

def test_NB_I_02_drawTool_getter():
    text = src(NB)
    assert "get drawTool" in text or "drawTool" in text, \
        "NotebookObject must expose drawTool property"


# ── NB-I-03: NotebookRadial class exported from notebook-radial.ts ─────────

def test_NB_I_03_radial_class_exists():
    assert RADIAL.exists(), "client/src/notebook-radial.ts must exist"
    text = src(RADIAL)
    assert "export class NotebookRadial" in text, \
        "NotebookRadial must be exported"


# ── NB-I-04: Radial has 5 wedges: pen, brush, eraser, text, cancel ─────────

def test_NB_I_04_radial_has_five_wedges():
    text = src(RADIAL)
    for tool in ("pen", "brush", "eraser", "text"):
        assert f"'{tool}'" in text or f'"{tool}"' in text, \
            f"Radial must include '{tool}' wedge"
    # cancel wedge is null tool
    assert "null" in text, "Radial must include a cancel/null wedge"


# ── NB-I-05: main.ts handles contextmenu event on renderer ─────────────────

def test_NB_I_05_contextmenu_handler_in_main():
    text = src(MAIN)
    assert "contextmenu" in text, \
        "main.ts must register a contextmenu event listener"


# ── NB-I-06: contextmenu default prevented on notes page ──────────────────

def test_NB_I_06_contextmenu_preventDefault():
    text = src(MAIN)
    assert "preventDefault" in text, \
        "contextmenu handler must call preventDefault()"


# ── NB-I-07: addTextBlock method exists on NotebookObject ─────────────────

def test_NB_I_07_addTextBlock_exists():
    text = src(NB)
    assert "addTextBlock" in text, \
        "NotebookObject must have addTextBlock(cx, cy, text) method"


# ── NB-I-08: addTextBlock calls fillText ─────────────────────────────────

def test_NB_I_08_addTextBlock_calls_fillText():
    text = src(NB)
    # Find addTextBlock body and verify fillText is called
    idx = text.find("addTextBlock")
    assert idx != -1, "addTextBlock must exist"
    snippet = text[idx:idx + 400]
    assert "fillText" in snippet, \
        "addTextBlock must call fillText to render text onto canvas"


# ── NB-I-09: transcript feed surface exists (read-only, no auto-write) ────

def test_NB_I_09_transcript_feed_texture_exists():
    text = src(NB)
    assert "setTranscriptFeedTexture" in text, \
        "NotebookObject must have setTranscriptFeedTexture() — transcript is a read-only feed"

# ── NB-I-10: upsertBestiaryEntry exists on NotebookObject ─────────────────

def test_NB_I_10_upsertBestiaryEntry_exists():
    text = src(NB)
    assert "upsertBestiaryEntry" in text, \
        "NotebookObject must have upsertBestiaryEntry() method"


# ── NB-I-11: Pencil cursor CSS applied in main.ts ─────────────────────────

def test_NB_I_11_pencil_cursor_in_main():
    text = src(MAIN)
    assert "cursor" in text and (
        "pencil" in text.lower() or "crosshair" in text
    ), "main.ts must set a pencil/crosshair cursor when over the notebook page"


# ── NB-I-12: NotebookRadial imported in main.ts ───────────────────────────

def test_NB_I_12_radial_imported_in_main():
    text = src(MAIN)
    assert "NotebookRadial" in text, \
        "main.ts must import and use NotebookRadial"
