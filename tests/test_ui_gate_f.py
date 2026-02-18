"""Gate F tests — Table UI Phase 1 backend contracts.

10 tests across 4 gate categories (UI-F1 through UI-F4).

Categories:
    UI-F1: PENDING state machine (3 tests)
    UI-F2: REQUEST schema (3 tests)
    UI-F3: Camera postures (2 tests)
    UI-F4: Hard bans — static scan (2 tests)

Authority: WO-UI-01, DOCTRINE_04_TABLE_UI_MEMO_V4.
"""
from __future__ import annotations

import ast
import dataclasses
import os
from pathlib import Path

import pytest

from aidm.ui.pending import (
    ALL_REQUEST_TYPES,
    BANNED_REQUEST_VERBS,
    DeclareActionIntent,
    DiceTowerDropIntent,
    PendingPoint,
    PendingRoll,
    PendingStateMachine,
)
from aidm.ui.camera import (
    ALL_POSTURES,
    CameraPosture,
    VALID_TRANSITIONS,
)


# ---------------------------------------------------------------------------
# UI-F1: PENDING state machine (3 tests)
# ---------------------------------------------------------------------------

class TestUIF1PendingStateMachine:
    """PENDING handshake protocol — one-at-a-time, frozen, clearable."""

    def test_pending_roll_is_frozen_dataclass(self):
        """PendingRoll is a frozen dataclass with spec and pending_handle."""
        pr = PendingRoll(spec="1d20", pending_handle="test_001")
        assert dataclasses.is_dataclass(pr)
        assert pr.spec == "1d20"
        assert pr.pending_handle == "test_001"
        # Frozen — cannot mutate.
        with pytest.raises(dataclasses.FrozenInstanceError):
            pr.spec = "2d6"  # type: ignore[misc]

    def test_only_one_pending_active_new_cancels_old(self):
        """Only one PENDING active at a time — new PENDING cancels old."""
        sm = PendingStateMachine()
        assert sm.active is None

        pr1 = PendingRoll(spec="1d20", pending_handle="roll_001")
        pr2 = PendingRoll(spec="2d6", pending_handle="roll_002")

        cancelled = sm.emit(pr1)
        assert cancelled is None
        assert sm.active is pr1

        cancelled = sm.emit(pr2)
        assert cancelled is pr1
        assert sm.active is pr2

    def test_pending_clears_on_request_receipt(self):
        """PENDING clears when corresponding REQUEST is received."""
        sm = PendingStateMachine()
        pr = PendingRoll(spec="1d20", pending_handle="roll_001")
        sm.emit(pr)
        assert sm.active is not None

        req = DiceTowerDropIntent(dice_ids=("d20",), pending_roll_handle="roll_001")
        resolved = sm.resolve(req)
        assert resolved is True
        assert sm.active is None


# ---------------------------------------------------------------------------
# UI-F2: REQUEST schema (3 tests)
# ---------------------------------------------------------------------------

class TestUIF2RequestSchema:
    """REQUEST intent types — frozen, serializable, no outcome fields."""

    def test_request_types_frozen_no_outcome_fields(self):
        """All REQUEST types are frozen dataclasses with no outcome/legality fields."""
        # Outcome/legality field names that must NOT appear.
        banned_fields = {"outcome", "result", "success", "legality", "damage", "hp_change"}

        for req_cls in ALL_REQUEST_TYPES:
            assert dataclasses.is_dataclass(req_cls), f"{req_cls.__name__} is not a dataclass"
            field_names = {f.name for f in dataclasses.fields(req_cls)}
            overlap = field_names & banned_fields
            assert not overlap, f"{req_cls.__name__} has banned outcome fields: {overlap}"

            # Verify frozen.
            instance = req_cls(**{f.name: _default_value(f) for f in dataclasses.fields(req_cls)})
            with pytest.raises(dataclasses.FrozenInstanceError):
                setattr(instance, dataclasses.fields(req_cls)[0].name, "mutated")

    def test_request_types_serialize_deserialize(self):
        """REQUEST types serialize/deserialize cleanly via to_dict/from_dict."""
        dai = DeclareActionIntent(action_kind="melee_strike", source_ref="beat_abc")
        d = dai.to_dict()
        assert d["type"] == "DECLARE_ACTION_INTENT"
        restored = DeclareActionIntent.from_dict(d)
        assert restored == dai

        dtd = DiceTowerDropIntent(dice_ids=("d20", "d6"), pending_roll_handle="roll_001")
        d2 = dtd.to_dict()
        assert d2["type"] == "DICE_TOWER_DROP_INTENT"
        restored2 = DiceTowerDropIntent.from_dict(d2)
        assert restored2 == dtd

    def test_no_action_verb_request_types(self):
        """No REQUEST type names use banned action verbs (ROLL, CAST, ATTACK, END_TURN)."""
        for req_cls in ALL_REQUEST_TYPES:
            name_upper = req_cls.__name__.upper()
            for verb in BANNED_REQUEST_VERBS:
                # The class name must not START with or BE the banned verb.
                # DeclareActionIntent contains "ACTION" but that's allowed —
                # the ban is on verbs that imply execution (ROLL, CAST, ATTACK, END_TURN).
                assert verb not in name_upper.split("_") and not name_upper.startswith(verb), (
                    f"REQUEST type {req_cls.__name__} uses banned verb {verb}"
                )


# ---------------------------------------------------------------------------
# UI-F3: Camera postures (2 tests)
# ---------------------------------------------------------------------------

class TestUIF3CameraPostures:
    """Camera posture definitions from UI doctrine §5."""

    def test_postures_defined(self):
        """STANDARD, DOWN, LEAN_FORWARD defined as posture enum values."""
        assert CameraPosture.STANDARD.value == "STANDARD"
        assert CameraPosture.DOWN.value == "DOWN"
        assert CameraPosture.LEAN_FORWARD.value == "LEAN_FORWARD"
        assert len(ALL_POSTURES) == 3

    def test_any_to_any_transition_valid(self):
        """Any posture → any posture transition is valid (including self)."""
        for src in CameraPosture:
            for dst in CameraPosture:
                assert (src, dst) in VALID_TRANSITIONS, (
                    f"Transition {src.value} → {dst.value} should be valid"
                )
        # 3×3 = 9 transitions total (including self-transitions).
        assert len(VALID_TRANSITIONS) == 9


# ---------------------------------------------------------------------------
# UI-F4: Hard bans — static scan (2 tests)
# ---------------------------------------------------------------------------

class TestUIF4HardBans:
    """Static analysis gates — no tooltip strings, no action-verb REQUEST names."""

    @staticmethod
    def _ui_source_files() -> list[Path]:
        """Return all Python source files in aidm/ui/."""
        ui_dir = Path(__file__).resolve().parent.parent / "aidm" / "ui"
        return list(ui_dir.glob("*.py"))

    def test_no_tooltip_popover_snippet_strings(self):
        """No tooltip/popover/snippet strings in UI schema code (doctrine §3)."""
        banned_tokens = {"tooltip", "popover", "snippet"}
        violations = []

        for src_file in self._ui_source_files():
            content = src_file.read_text(encoding="utf-8").lower()
            for token in banned_tokens:
                if token in content:
                    violations.append(f"{src_file.name} contains '{token}'")

        assert not violations, f"Hard ban violations: {violations}"

    def test_no_action_verb_request_type_names(self):
        """No 'do the action' verbs in REQUEST type names — static scan."""
        banned = {"Roll", "Cast", "Attack", "EndTurn"}

        for req_cls in ALL_REQUEST_TYPES:
            for verb in banned:
                # Class name must not start with the banned verb.
                assert not req_cls.__name__.startswith(verb), (
                    f"REQUEST type {req_cls.__name__} starts with banned verb '{verb}'"
                )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _default_value(f: dataclasses.Field) -> object:
    """Return a plausible default for a dataclass field by type annotation."""
    if f.type in ("str", str):
        return "test"
    if f.type in ("Tuple[str, ...]", "tuple"):
        return ("test",)
    return "test"
