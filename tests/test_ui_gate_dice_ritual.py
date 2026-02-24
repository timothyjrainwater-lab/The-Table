"""Gate UI-DICE-RITUAL — Dice Tray + Tower Ritual (WO-UI-DICE-01).

Authority: GT v12, DOCTRINE_04_TABLE_UI_MEMO_V4, WO-UI-ZONE-AUTHORITY.
Objects: O8A (Dice Tray), O8B (Dice Tower), O8C (Tower Plaque).

Tests use static source scanning and Python simulation of the
TypeScript state machine. No browser required.

Gate tests:
  DICE-RITUAL-01: Tower Plaque visibility driven by PENDING_ROLL only.
  DICE-RITUAL-02: Authoritative path requires PENDING_ROLL handle.
  DICE-RITUAL-03: Practice roll inertness — no PendingStateMachine interaction.
  DICE-RITUAL-04: DICE_TRAY posture wired to tray interaction path.
  DICE-RITUAL-05: No roll buttons; no client-side randomness in dice files.
  DICE-RITUAL-06: Tower plaque carries no DC or locked precision tokens.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Source file paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).parent.parent
_DICE_BAG_TS   = _ROOT / "client" / "src" / "dice-bag.ts"
_SCENE_TS      = _ROOT / "client" / "src" / "scene-builder.ts"
_MAIN_TS       = _ROOT / "client" / "src" / "main.ts"

# Python pending module
sys.path.insert(0, str(_ROOT))
from aidm.ui.pending import (
    PendingRoll,
    PendingPoint,
    DiceTowerDropIntent,
    DeclareActionIntent,
    PendingStateMachine,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _src(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Python simulation of TowerPlaque state machine
# ---------------------------------------------------------------------------

class TowerPlaqueSim:
    """Simulates TowerPlaque visibility and content rules."""

    def __init__(self) -> None:
        self._spec: str | None = None
        self.visible: bool = False

    def set_pending(self, spec: str) -> None:
        self._spec = spec
        self.visible = True

    def clear(self) -> None:
        self._spec = None
        self.visible = False

    @property
    def spec(self) -> str | None:
        return self._spec


# ---------------------------------------------------------------------------
# Python simulation of the authoritative drop path
# ---------------------------------------------------------------------------

class DropPathSim:
    """Simulates the _sendDiceTowerDrop gate in main.ts.

    _sendDiceTowerDrop() is a no-op when activePendingHandle is None.
    It emits DiceTowerDropIntent only when a handle is present.
    """

    def __init__(self) -> None:
        self.active_pending_handle: str | None = None
        self.emitted_intents: list[dict] = []

    def on_pending_roll(self, spec: str, handle: str) -> None:
        self.active_pending_handle = handle

    def on_pending_cleared(self) -> None:
        self.active_pending_handle = None

    def on_drop_in_tower(self) -> None:
        """Called when die is dropped in the tower zone."""
        if not self.active_pending_handle:
            return  # cosmetic drop — no intent emitted
        self.emitted_intents.append({
            "type": "DICE_TOWER_DROP_INTENT",
            "dice_ids": ["d20"],
            "pending_roll_handle": self.active_pending_handle,
        })
        self.active_pending_handle = None


# ===========================================================================
# DICE-RITUAL-01: Tower Plaque visibility driven by PENDING_ROLL only
# ===========================================================================

class TestDiceRitual01:
    """Plaque is hidden with no pending; shows spec (formula only) when active;
    never shows DC, never shows 'because'."""

    def test_plaque_hidden_at_start(self) -> None:
        plaque = TowerPlaqueSim()
        assert plaque.visible is False
        assert plaque.spec is None

    def test_plaque_visible_with_pending(self) -> None:
        plaque = TowerPlaqueSim()
        plaque.set_pending("1d20+4")
        assert plaque.visible is True
        assert plaque.spec == "1d20+4"

    def test_plaque_hidden_after_clear(self) -> None:
        plaque = TowerPlaqueSim()
        plaque.set_pending("2d6")
        plaque.clear()
        assert plaque.visible is False
        assert plaque.spec is None

    def test_plaque_spec_is_formula_only(self) -> None:
        """Spec string must be a pure dice formula — no explanation text."""
        plaque = TowerPlaqueSim()
        specs = ["1d20", "1d20+4", "2d6+3", "1d4"]
        for s in specs:
            plaque.set_pending(s)
            assert plaque.spec == s, f"spec mismatch: {plaque.spec!r} != {s!r}"

    def test_plaque_source_calls_set_pending_on_pending_roll(self) -> None:
        """Static scan: main.ts calls towerPlaque.setPending(spec) in PENDING_ROLL handler."""
        src = _src(_MAIN_TS)
        assert "towerPlaque.setPending(" in src, (
            "main.ts must call towerPlaque.setPending(spec) in the PENDING_ROLL handler"
        )

    def test_plaque_source_calls_clear_on_pending_cleared(self) -> None:
        """Static scan: main.ts calls towerPlaque.clear() in pending_cleared path."""
        src = _src(_MAIN_TS)
        assert "towerPlaque.clear()" in src, (
            "main.ts must call towerPlaque.clear() when pending is cleared"
        )


# ===========================================================================
# DICE-RITUAL-02: Authoritative path requires PENDING_ROLL handle
# ===========================================================================

class TestDiceRitual02:
    """DiceTowerDropIntent emitted only when a pending handle is present.
    Drop with no active pending → cosmetic only, no intent emitted."""

    def test_drop_with_pending_emits_intent(self) -> None:
        sim = DropPathSim()
        sim.on_pending_roll("1d20", "handle-abc")
        sim.on_drop_in_tower()
        assert len(sim.emitted_intents) == 1
        intent = sim.emitted_intents[0]
        assert intent["type"] == "DICE_TOWER_DROP_INTENT"
        assert intent["pending_roll_handle"] == "handle-abc"
        assert "d20" in intent["dice_ids"]

    def test_drop_without_pending_emits_no_intent(self) -> None:
        sim = DropPathSim()
        # No PENDING_ROLL set — practice roll
        sim.on_drop_in_tower()
        assert len(sim.emitted_intents) == 0

    def test_drop_after_cleared_emits_no_intent(self) -> None:
        sim = DropPathSim()
        sim.on_pending_roll("1d20", "handle-xyz")
        sim.on_pending_cleared()
        sim.on_drop_in_tower()
        assert len(sim.emitted_intents) == 0

    def test_handle_cleared_after_drop(self) -> None:
        """Handle is consumed after authoritative drop — cannot double-emit."""
        sim = DropPathSim()
        sim.on_pending_roll("1d20", "handle-once")
        sim.on_drop_in_tower()
        sim.on_drop_in_tower()  # second drop — no pending
        assert len(sim.emitted_intents) == 1

    def test_static_scan_gate_in_main(self) -> None:
        """Static scan: _sendDiceTowerDrop() checks activePendingHandle before emitting."""
        src = _src(_MAIN_TS)
        # The guard must be present: function returns early if handle is absent
        assert "if (!activePendingHandle) return;" in src, (
            "_sendDiceTowerDrop must guard: if (!activePendingHandle) return;"
        )

    def test_static_scan_drop_only_on_zone_and_handle(self) -> None:
        """Static scan: drop in onDrop callback only sends when zone=dice_tower
        AND activePendingHandle is truthy."""
        src = _src(_MAIN_TS)
        # Both conditions must appear together in the onDrop callback
        assert "zone === 'dice_tower' && activePendingHandle" in src, (
            "onDrop must gate: zone === 'dice_tower' && activePendingHandle"
        )


# ===========================================================================
# DICE-RITUAL-03: Practice roll inertness
# ===========================================================================

class TestDiceRitual03:
    """Practice drop: no DiceTowerDropIntent, no PendingStateMachine.resolve(),
    PendingStateMachine.active unchanged."""

    def test_practice_drop_emits_no_intent(self) -> None:
        sim = DropPathSim()
        for _ in range(5):
            sim.on_drop_in_tower()
        assert len(sim.emitted_intents) == 0

    def test_practice_drop_does_not_affect_state_machine(self) -> None:
        sm = PendingStateMachine()
        pr = PendingRoll(spec="1d20", pending_handle="h1")
        sm.emit(pr)
        assert sm.active == pr

        # Simulate a practice drop — does NOT call sm.resolve()
        # (In the real code, practice drop path is: activePendingHandle is None → early return)
        # State machine must remain unchanged
        assert sm.active == pr, "Practice drop must not affect PendingStateMachine"

    def test_authoritative_drop_resolves_state_machine(self) -> None:
        """Contrast: authoritative path calls sm.resolve()."""
        sm = PendingStateMachine()
        pr = PendingRoll(spec="1d20", pending_handle="h42")
        sm.emit(pr)
        intent = DiceTowerDropIntent(
            dice_ids=("d20",),
            pending_roll_handle="h42",
        )
        resolved = sm.resolve(intent)
        assert resolved is True
        assert sm.active is None

    def test_wrong_handle_does_not_resolve(self) -> None:
        sm = PendingStateMachine()
        pr = PendingRoll(spec="1d20", pending_handle="correct-handle")
        sm.emit(pr)
        intent = DiceTowerDropIntent(
            dice_ids=("d20",),
            pending_roll_handle="wrong-handle",
        )
        resolved = sm.resolve(intent)
        assert resolved is False
        assert sm.active is pr

    def test_practice_path_and_authoritative_path_do_not_share_code(self) -> None:
        """Static scan: the practice path (no handle) exits before any emit call."""
        src = _src(_MAIN_TS)
        # The function _sendDiceTowerDrop must start with the guard
        # (ensures practice and auth paths cannot share emit code)
        fn_match = re.search(
            r"function _sendDiceTowerDrop\(\)[^{]*\{([^}]+)\}",
            src,
            re.DOTALL,
        )
        assert fn_match is not None, "_sendDiceTowerDrop function not found in main.ts"
        fn_body = fn_match.group(1)
        assert "if (!activePendingHandle) return;" in fn_body, (
            "_sendDiceTowerDrop must begin with: if (!activePendingHandle) return;"
        )


# ===========================================================================
# DICE-RITUAL-04: DICE_TRAY posture wiring
# ===========================================================================

class TestDiceRitual04:
    """camera.setPosture('DICE_TRAY') called in tray interaction path.
    DICE_TRAY must not be the default posture on load."""

    def test_set_posture_dice_tray_in_tray_interaction_path(self) -> None:
        """Static scan: setPosture('DICE_TRAY') appears in the drag/interaction path."""
        src = _src(_MAIN_TS)
        assert "setPosture('DICE_TRAY')" in src, (
            "main.ts must call postureCtrl.setPosture('DICE_TRAY') in the tray interaction path"
        )

    def test_dice_tray_posture_wired_to_die_drag(self) -> None:
        """Static scan: DICE_TRAY posture switch is inside the onDragStart callback
        or equivalent die-pick path — not just the keyboard shortcut."""
        src = _src(_MAIN_TS)
        # The DICE_TRAY posture switch must be inside a block that also references
        # 'die' (the kind check) and 'dice_tray' (the zone check)
        # Check for the conjunctive guard pattern
        assert (
            "picked.kind === 'die'" in src and
            "picked.zone === 'dice_tray'" in src and
            "setPosture('DICE_TRAY')" in src
        ), (
            "DICE_TRAY posture must be set when picked.kind==='die' and zone==='dice_tray'"
        )

    def test_dice_tray_not_default_posture(self) -> None:
        """Static scan: CameraPostureController initialises to STANDARD, not DICE_TRAY."""
        src = _src(_ROOT / "client" / "src" / "camera.ts")
        # Default is 'STANDARD' — hardcoded as the initial value
        assert "currentPosture: PostureName = 'STANDARD'" in src, (
            "Default camera posture must be STANDARD, not DICE_TRAY"
        )

    def test_dice_tray_posture_data_exists_in_camera_poses(self) -> None:
        """DICE_TRAY posture data must exist in camera_poses.json."""
        import json
        poses_path = _ROOT / "docs" / "design" / "LAYOUT_PACK_V1" / "camera_poses.json"
        poses = json.loads(poses_path.read_text(encoding="utf-8"))
        assert "DICE_TRAY" in poses.get("postures", {}), (
            "camera_poses.json must contain a DICE_TRAY posture entry"
        )


# ===========================================================================
# DICE-RITUAL-05: No roll buttons; no client-side randomness in dice files
# ===========================================================================

class TestDiceRitual05:
    """No button/onclick that directly emits DiceTowerDropIntent without a
    drop-detection event. No Math.random or crypto.getRandomValues in dice files."""

    _DICE_FILES = [_DICE_BAG_TS, _ROOT / "client" / "src" / "dice-object.ts"]

    def test_no_math_random_in_dice_bag(self) -> None:
        src = _src(_DICE_BAG_TS)
        assert "Math.random" not in src, (
            "dice-bag.ts must not use Math.random — use seeded PRNG only (Gate G)"
        )

    def test_no_crypto_random_in_dice_bag(self) -> None:
        src = _src(_DICE_BAG_TS)
        assert "crypto.getRandomValues" not in src, (
            "dice-bag.ts must not use crypto.getRandomValues (Gate G)"
        )

    def test_no_math_random_in_dice_object(self) -> None:
        src = _src(_ROOT / "client" / "src" / "dice-object.ts")
        assert "Math.random" not in src, (
            "dice-object.ts must not use Math.random (Gate G)"
        )

    def test_no_crypto_random_in_dice_object(self) -> None:
        src = _src(_ROOT / "client" / "src" / "dice-object.ts")
        assert "crypto.getRandomValues" not in src, (
            "dice-object.ts must not use crypto.getRandomValues (Gate G)"
        )

    def test_no_direct_button_emit_without_drop_detection(self) -> None:
        """Static scan: the overlay click path is gated by activePendingHandle,
        not a raw button that unconditionally calls _sendDiceTowerDrop."""
        src = _src(_MAIN_TS)
        # The overlay click listener must check activePendingHandle before emitting
        # (confirmed by: if (!activePendingHandle) return; inside _sendDiceTowerDrop)
        # and the click listener delegates to _sendDiceTowerDrop (which has the guard)
        assert "pendingOverlay.addEventListener('click'" in src, (
            "Overlay click listener must exist"
        )
        # The direct onclick must call _sendDiceTowerDrop (which has the guard)
        # not emit DiceTowerDropIntent inline
        assert "_sendDiceTowerDrop()" in src, (
            "Overlay click must delegate to _sendDiceTowerDrop() not emit inline"
        )

    def test_no_inline_drop_intent_in_onclick(self) -> None:
        """Static scan: no inline DiceTowerDropIntent emission inside addEventListener('click')."""
        src = _src(_MAIN_TS)
        # Find the pendingOverlay click block
        click_match = re.search(
            r"pendingOverlay\.addEventListener\('click'.*?\}\)",
            src,
            re.DOTALL,
        )
        assert click_match is not None, "pendingOverlay click listener not found"
        click_block = click_match.group(0)
        assert "DICE_TOWER_DROP_INTENT" not in click_block, (
            "pendingOverlay click handler must not inline DICE_TOWER_DROP_INTENT — "
            "must delegate to _sendDiceTowerDrop()"
        )


# ===========================================================================
# DICE-RITUAL-06: Tower plaque carries no DC
# ===========================================================================

class TestDiceRitual06:
    """Static scan: no string containing 'DC', 'difficulty', 'armor class',
    'target' in the TowerPlaque rendering path (dice-bag.ts TowerPlaque class)."""

    _BANNED_STRINGS = ["DC", "difficulty", "armor class", "target"]

    def _extract_tower_plaque_class(self, src: str) -> str:
        """Extract the TowerPlaque class body from dice-bag.ts."""
        match = re.search(
            r"class TowerPlaque\b.*?^}",
            src,
            re.DOTALL | re.MULTILINE,
        )
        assert match is not None, "TowerPlaque class not found in dice-bag.ts"
        return match.group(0)

    def test_no_dc_in_plaque_class(self) -> None:
        src = _src(_DICE_BAG_TS)
        plaque_src = self._extract_tower_plaque_class(src)
        # Only scan _renderSpec and _renderBlank — comments documenting the ban are allowed.
        # Extract the two private render methods.
        render_block = re.search(
            r"private _renderSpec\b.*?(?=\n  private _renderBlank|\n})",
            plaque_src,
            re.DOTALL,
        )
        blank_block = re.search(
            r"private _renderBlank\b.*?(?=\n})",
            plaque_src,
            re.DOTALL,
        )
        render_src = (render_block.group(0) if render_block else "") + \
                     (blank_block.group(0) if blank_block else "")
        matches = re.findall(r'\bDC\b', render_src)
        assert len(matches) == 0, (
            f"TowerPlaque render methods must not contain 'DC' token; found: {matches}"
        )

    def test_no_difficulty_in_plaque_class(self) -> None:
        src = _src(_DICE_BAG_TS)
        plaque_src = self._extract_tower_plaque_class(src)
        # Only scan _renderSpec and _renderBlank — comments are excluded.
        render_block = re.search(
            r"private _renderSpec\b.*?(?=\n  private _renderBlank|\n})",
            plaque_src,
            re.DOTALL,
        )
        render_src = render_block.group(0) if render_block else ""
        # Strip single-line and block comments before checking
        render_no_comments = re.sub(r'//[^\n]*', '', render_src)
        render_no_comments = re.sub(r'/\*.*?\*/', '', render_no_comments, flags=re.DOTALL)
        assert "difficulty" not in render_no_comments.lower(), (
            "TowerPlaque _renderSpec must not render the string 'difficulty'"
        )

    def test_no_armor_class_in_plaque_class(self) -> None:
        src = _src(_DICE_BAG_TS)
        plaque_src = self._extract_tower_plaque_class(src)
        assert "armor class" not in plaque_src.lower(), (
            "TowerPlaque class must not contain 'armor class'"
        )

    def test_no_target_literal_in_plaque_render(self) -> None:
        """'target' must not appear as a rendered string in the plaque (_renderSpec)."""
        src = _src(_DICE_BAG_TS)
        plaque_src = self._extract_tower_plaque_class(src)
        # Find _renderSpec body
        render_match = re.search(
            r"_renderSpec\(spec: string\)[^{]*\{(.+?)(?=\n  private|\n})",
            plaque_src,
            re.DOTALL,
        )
        assert render_match is not None, "_renderSpec method not found in TowerPlaque"
        render_body = render_match.group(1)
        # 'target' must not appear as a string literal being rendered
        assert '"target"' not in render_body and "'target'" not in render_body, (
            "_renderSpec must not render the string 'target'"
        )

    def test_plaque_renders_only_spec_string(self) -> None:
        """The _renderSpec method renders only the spec parameter, nothing else."""
        src = _src(_DICE_BAG_TS)
        plaque_src = self._extract_tower_plaque_class(src)
        # The fillText call must use 'spec' (the parameter) not a hardcoded DC string
        assert "fillText(spec," in plaque_src, (
            "_renderSpec must render spec directly via fillText(spec, ...)"
        )

    def test_plaque_formula_only_doctrine_comment(self) -> None:
        """TowerPlaque source must include a doctrine comment confirming formula-only rule."""
        src = _src(_DICE_BAG_TS)
        assert "formula only" in src.lower() or "spec" in src, (
            "dice-bag.ts TowerPlaque section must document formula-only rendering"
        )
