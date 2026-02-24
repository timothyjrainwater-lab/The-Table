"""
Gate UI-SESSION-CLEANUP-01 — WO-UI-SESSION-CLEANUP-01: Table reset / tidy baseline.

Tests (8):
  SC-01: main.ts defines _resetToBaseline helper
  SC-02: _resetToBaseline clears entity roster
  SC-03: _resetToBaseline clears map overlay pending state
  SC-04: _resetToBaseline resets notebook consent chain
  SC-05: _resetToBaseline resets camera to STANDARD posture
  SC-06: main.ts handles scene_end → _resetToBaseline
  SC-07: main.ts handles scene_start → _resetToBaseline
  SC-08: session_resume restores notebook cover from storage (never invents)
"""

import re, pathlib

ROOT     = pathlib.Path(__file__).parent.parent
MAIN_SRC = ROOT / "client" / "src" / "main.ts"
HO_SRC   = ROOT / "client" / "src" / "handout-object.ts"

main_text = MAIN_SRC.read_text(encoding="utf-8")
ho_text   = HO_SRC.read_text(encoding="utf-8")


def test_sc01_reset_helper_exists():
    """SC-01: main.ts defines a _resetToBaseline (or resetToBaseline) helper."""
    assert re.search(r'(function\s+|const\s+)_?resetToBaseline', main_text), (
        "main.ts must define a _resetToBaseline helper function "
        "that orchestrates the full scene boundary reset"
    )


def test_sc02_resets_entity_roster():
    """SC-02: _resetToBaseline clears entity roster via syncRoster([]) or clearAll()."""
    # Acceptable patterns: syncRoster([]) or clearAll() on entityRenderer
    assert (
        re.search(r'syncRoster\s*\(\s*\[\s*\]', main_text) or
        re.search(r'entityRenderer\s*\.\s*clearAll\s*\(', main_text)
    ), (
        "_resetToBaseline must call entityRenderer.syncRoster([]) "
        "to clear all tokens at scene boundary"
    )


def test_sc03_clears_overlay_pending():
    """SC-03: _resetToBaseline clears map overlay PENDING state."""
    assert re.search(r'overlayMgr\s*\.\s*clearPending\s*\(', main_text), (
        "_resetToBaseline must call overlayMgr.clearPending() "
        "to clear ephemeral overlays and PENDING gate"
    )


def test_sc04_resets_notebook_consent():
    """SC-04: _resetToBaseline resets the notebook consent chain."""
    assert re.search(r'resetOnSceneEnd\s*\(', main_text), (
        "_resetToBaseline must call notebook.consentChain.resetOnSceneEnd() "
        "— consent does not carry over scene boundaries"
    )


def test_sc05_resets_camera_to_standard():
    """SC-05: _resetToBaseline resets camera posture to STANDARD."""
    assert re.search(r"setPosture\s*\(\s*['\"]STANDARD['\"]", main_text), (
        "_resetToBaseline must call postureCtrl.setPosture('STANDARD') "
        "to return camera to default seated posture"
    )


def test_sc06_scene_end_triggers_reset():
    """SC-06: main.ts handles scene_end WS event and calls _resetToBaseline."""
    assert 'scene_end' in main_text, (
        "main.ts must handle 'scene_end' WS event"
    )
    # The handler must reference the reset helper
    block = re.search(
        r"scene_end.*?resetToBaseline",
        main_text, re.DOTALL | re.IGNORECASE
    )
    assert block, (
        "scene_end handler must call _resetToBaseline (or equivalent) — "
        "scene_end is the primary trigger for the full baseline reset"
    )


def test_sc07_scene_start_triggers_reset():
    """SC-07: main.ts handles scene_start WS event and calls _resetToBaseline."""
    assert 'scene_start' in main_text, (
        "main.ts must handle 'scene_start' WS event"
    )
    block = re.search(
        r"scene_start.*?resetToBaseline",
        main_text, re.DOTALL | re.IGNORECASE
    )
    assert block, (
        "scene_start handler must call _resetToBaseline before loading new scene data"
    )


def test_sc08_session_resume_restores_not_invents():
    """SC-08: session_resume handler restores notebook cover from storage, never invents."""
    assert 'session_resume' in main_text, (
        "main.ts must handle 'session_resume' WS event"
    )
    assert 'loadCoverFromStorage' in main_text, (
        "session_resume must call notebook.loadCoverFromStorage() "
        "— cover state is restored from localStorage, never invented by the client"
    )
    # Confirm it's inside the session_resume block
    block = re.search(
        r"session_resume.*?loadCoverFromStorage",
        main_text, re.DOTALL
    )
    assert block, (
        "loadCoverFromStorage must be called inside the session_resume handler, "
        "not unconditionally at startup"
    )
