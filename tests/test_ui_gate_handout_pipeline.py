"""
Gate UI-HANDOUTS-01: WO-UI-HANDOUTS-01 — Printer slot + tray + recycle well pipeline.

Tests (7):
  HO-01: Intent types exist and are frozen dataclasses, all in ALL_REQUEST_TYPES
  HO-02: Intent type names contain no banned verbs
  HO-03: Handout delivery does not auto-paste to notebook
  HO-04: Discard is retrievable (≤2 actions)
  HO-05: No backflow — handout content cannot affect mechanics
  HO-06: Read overlay is diegetic — no UI chrome
  HO-07: Existing handout read tests still pass (regression marker)
"""

import dataclasses
import pathlib
import re
import sys
import types

ROOT = pathlib.Path(__file__).parent.parent
HANDOUT_SRC = ROOT / "client" / "src" / "handout-object.ts"
HTML         = ROOT / "client" / "index.html"
MAIN_SRC     = ROOT / "client" / "src" / "main.ts"

handout_text = HANDOUT_SRC.read_text(encoding="utf-8")
html_text    = HTML.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# HO-01: Intent types exist and are frozen dataclasses, in ALL_REQUEST_TYPES
# ---------------------------------------------------------------------------

def test_ho01_intent_types_are_frozen_dataclasses():
    """HO-01: All 4 handout intents exist, are frozen dataclasses, in ALL_REQUEST_TYPES."""
    from aidm.ui.pending import (
        HandoutPlacedIntent,
        HandoutDiscardedIntent,
        HandoutRetrievedIntent,
        HandoutPasteToNotebookIntent,
        ALL_REQUEST_TYPES,
    )

    intent_types = [
        HandoutPlacedIntent,
        HandoutDiscardedIntent,
        HandoutRetrievedIntent,
        HandoutPasteToNotebookIntent,
    ]

    for cls in intent_types:
        assert dataclasses.is_dataclass(cls), (
            f"{cls.__name__} must be a dataclass"
        )
        params = dataclasses.fields(cls)
        assert len(params) > 0, f"{cls.__name__} has no fields"
        # Frozen check: attempt mutation must raise FrozenInstanceError
        try:
            instance = cls.__new__(cls)
        except Exception:
            pass  # abstract constructor is fine; field-level frozen is checked via params
        # Confirm frozen flag via dataclass params
        dc_params = cls.__dataclass_params__  # type: ignore[attr-defined]
        assert dc_params.frozen, f"{cls.__name__} must be frozen=True"

    for cls in intent_types:
        assert cls in ALL_REQUEST_TYPES, (
            f"{cls.__name__} must be in ALL_REQUEST_TYPES"
        )


# ---------------------------------------------------------------------------
# HO-02: Intent type names contain no banned verbs
# ---------------------------------------------------------------------------

def test_ho02_no_banned_verbs_in_intent_names():
    """HO-02: Handout intent type names must not contain ROLL, CAST, ATTACK, END_TURN."""
    from aidm.ui.pending import (
        HandoutPlacedIntent,
        HandoutDiscardedIntent,
        HandoutRetrievedIntent,
        HandoutPasteToNotebookIntent,
    )

    BANNED = {"ROLL", "CAST", "ATTACK", "END_TURN"}
    intent_names = [
        HandoutPlacedIntent.__name__,
        HandoutDiscardedIntent.__name__,
        HandoutRetrievedIntent.__name__,
        HandoutPasteToNotebookIntent.__name__,
    ]

    for name in intent_names:
        upper = name.upper()
        for verb in BANNED:
            assert verb not in upper, (
                f"Intent name '{name}' contains banned verb '{verb}'"
            )


# ---------------------------------------------------------------------------
# HO-03: Deliver does not auto-paste to notebook
# ---------------------------------------------------------------------------

def test_ho03_deliver_does_not_auto_paste():
    """HO-03: HandoutTray.deliver() emits no HandoutPasteToNotebookIntent.
    Static scan: handout-object.ts must not call notebook write methods.
    """
    # Static scan — notebook write methods must not appear in handout-object.ts
    FORBIDDEN_NOTEBOOK_CALLS = ["startStroke", "applyBestiaryUpsert", "saveStrokes"]
    for method in FORBIDDEN_NOTEBOOK_CALLS:
        assert method not in handout_text, (
            f"handout-object.ts must not call notebook method '{method}' "
            "(no auto-paste path from handout delivery)"
        )


# ---------------------------------------------------------------------------
# HO-04: Discard is retrievable (≤2 actions)
# ---------------------------------------------------------------------------

def test_ho04_discard_is_retrievable():
    """HO-04: HandoutManager has retrieveFromDiscard; retrieve is ≤2 method calls."""
    # retrieveFromDiscard must exist on HandoutManager
    assert "retrieveFromDiscard" in handout_text, (
        "HandoutManager must expose retrieveFromDiscard(handout_id: string): boolean"
    )

    # Confirm the method is defined directly on HandoutManager (not nested elsewhere)
    # Look for the method definition pattern inside the class body
    assert re.search(
        r"retrieveFromDiscard\s*\(\s*handout_id\s*:\s*string\s*\)",
        handout_text,
    ), (
        "retrieveFromDiscard must have signature (handout_id: string)"
    )

    # ≤2 actions: the method must not delegate through more than one helper method
    # that requires further player action. Static proxy: the method body must return
    # a boolean (restore path) not void, confirming it is a single callable step.
    assert re.search(
        r"retrieveFromDiscard.*?:\s*boolean",
        handout_text,
        re.DOTALL,
    ), (
        "retrieveFromDiscard must return boolean (≤2-action requirement: "
        "caller calls this then emits HandoutRetrievedIntent)"
    )

    # Also verify the discard stack backing structure exists
    assert "_discardStack" in handout_text, (
        "HandoutManager must maintain a _discardStack to support retrieval"
    )


# ---------------------------------------------------------------------------
# HO-05: No backflow — handout content cannot affect mechanics
# ---------------------------------------------------------------------------

def test_ho05_no_backflow_to_mechanics():
    """HO-05: handout-object.ts must not import from or reference aidm core/oracle/lens."""
    BANNED_IMPORTS = [
        "aidm.core",
        "aidm/core",
        "aidm.oracle",
        "aidm/oracle",
        "aidm.lens",
        "aidm/lens",
        "aidm.immersion",
        "aidm/immersion",
    ]
    for banned in BANNED_IMPORTS:
        assert banned not in handout_text, (
            f"handout-object.ts must not import from '{banned}' (backflow violation)"
        )

    # HandoutData must contain no mechanic-bearing field names
    BANNED_FIELDS = ["dc", "damage", "bonus", "modifier", "legality", "outcome"]
    # Locate HandoutData interface block
    data_block_match = re.search(
        r"interface HandoutData\s*\{(.*?)\}",
        handout_text,
        re.DOTALL,
    )
    assert data_block_match, "HandoutData interface not found in handout-object.ts"
    data_block = data_block_match.group(1)
    for field in BANNED_FIELDS:
        assert field not in data_block, (
            f"HandoutData must not contain field '{field}' (mechanic backflow)"
        )


# ---------------------------------------------------------------------------
# HO-06: Read overlay is diegetic — no UI chrome (no close button, no toolbar)
# ---------------------------------------------------------------------------

def test_ho06_overlay_has_no_chrome():
    """HO-06: #handout-read-overlay div has no child buttons, no close-button, no toolbar."""
    # Find the overlay div content in index.html
    overlay_match = re.search(
        r'<div\s+id=["\']handout-read-overlay["\'][^>]*>(.*?)</div>',
        html_text,
        re.DOTALL | re.IGNORECASE,
    )
    assert overlay_match, (
        "#handout-read-overlay div not found in index.html"
    )
    overlay_content = overlay_match.group(1)

    # Must have no child button elements
    assert not re.search(r"<button", overlay_content, re.IGNORECASE), (
        "#handout-read-overlay must not contain any <button> elements (no UI chrome)"
    )

    # Must have no close-button element
    assert "close-button" not in overlay_content.lower(), (
        "#handout-read-overlay must not contain a close-button element"
    )

    # Must have no toolbar element
    assert "toolbar" not in overlay_content.lower(), (
        "#handout-read-overlay must not contain a toolbar element"
    )

    # Dismiss affordance is click-anywhere — overlay itself must be the listener target
    main_text = MAIN_SRC.read_text(encoding="utf-8")
    assert re.search(
        r"handoutReadOverlay.*addEventListener\('click'",
        main_text,
        re.DOTALL,
    ), (
        "Dismiss must be wired as a click listener on handoutReadOverlay itself (no close button)"
    )


# ---------------------------------------------------------------------------
# HO-07: Existing handout read tests still pass (regression marker)
# ---------------------------------------------------------------------------

def test_ho07_handout_read_gate_still_passes():
    """HO-07: Confirms the 4 handout-read gate tests from test_ui_gate_handout_read.py pass.

    This is a regression marker — it re-runs the static assertions from that gate
    so a single pytest invocation catches both new and existing failures.
    """
    main_text    = MAIN_SRC.read_text(encoding="utf-8")

    # HR-01: overlay div exists
    assert 'id="handout-read-overlay"' in html_text, (
        "HR-01 regression: index.html must contain #handout-read-overlay"
    )

    # HR-02: getHandoutCanvas exists
    assert "getHandoutCanvas" in handout_text, (
        "HR-02 regression: HandoutManager must expose getHandoutCanvas"
    )
    assert "HTMLCanvasElement" in handout_text, (
        "HR-02 regression: getHandoutCanvas must declare HTMLCanvasElement return type"
    )

    # HR-03: overlay shown on handout click
    assert "handoutReadOverlay" in main_text, (
        "HR-03 regression: main.ts must reference handoutReadOverlay"
    )
    assert "handoutReadOverlay.style.display = 'flex'" in main_text, (
        "HR-03 regression: main.ts must set handoutReadOverlay display=flex on click"
    )

    # HR-04: click-to-dismiss wired
    assert "handoutReadOverlay.style.display = 'none'" in main_text, (
        "HR-04 regression: main.ts must hide handoutReadOverlay on dismiss"
    )
    assert re.search(
        r"handoutReadOverlay.*addEventListener\('click'",
        main_text,
        re.DOTALL,
    ), (
        "HR-04 regression: main.ts must add click listener on handoutReadOverlay"
    )
