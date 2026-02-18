"""Gate G tests — Table UI Phase 2 backend contracts.

10 tests across 4 gate categories (UI-G1 through UI-G4).

Categories:
    UI-G1: TableObject types (3 tests)
    UI-G2: Zone validation (3 tests)
    UI-G3: Registry consistency (2 tests)
    UI-G4: Hard bans — static scan (2 tests)

Authority: WO-UI-02, DOCTRINE_04_TABLE_UI_MEMO_V4.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from aidm.ui.table_objects import (
    VALID_ZONES,
    ObjectPositionUpdate,
    TableObjectRegistry,
    TableObjectState,
    validate_zone_position,
    zone_for_position,
)
from aidm.ui.pending import ALL_REQUEST_TYPES, BANNED_REQUEST_VERBS


# ---------------------------------------------------------------------------
# UI-G1: TableObject types (3 tests)
# ---------------------------------------------------------------------------

class TestUIG1TableObjectTypes:
    """TableObjectState and ObjectPositionUpdate — frozen, correct fields."""

    def test_table_object_state_is_frozen_dataclass(self):
        """TableObjectState is a frozen dataclass with object_id, kind, position, zone."""
        obj = TableObjectState(
            object_id="card_1",
            kind="card",
            position=(1.0, 0.05, 3.0),
            zone="player",
        )
        assert dataclasses.is_dataclass(obj)
        assert obj.object_id == "card_1"
        assert obj.kind == "card"
        assert obj.position == (1.0, 0.05, 3.0)
        assert obj.zone == "player"

        # Frozen — cannot mutate.
        with pytest.raises(dataclasses.FrozenInstanceError):
            obj.zone = "map"  # type: ignore[misc]

    def test_object_position_update_is_frozen_dataclass(self):
        """ObjectPositionUpdate is a frozen dataclass with object_id, new_position, new_zone."""
        upd = ObjectPositionUpdate(
            object_id="card_1",
            new_position=(2.0, 0.05, -0.5),
            new_zone="map",
        )
        assert dataclasses.is_dataclass(upd)
        assert upd.object_id == "card_1"
        assert upd.new_position == (2.0, 0.05, -0.5)
        assert upd.new_zone == "map"

        # Frozen — cannot mutate.
        with pytest.raises(dataclasses.FrozenInstanceError):
            upd.new_zone = "dm"  # type: ignore[misc]

    def test_object_position_update_no_outcome_fields(self):
        """ObjectPositionUpdate has no outcome/legality fields (REQUEST-only constraint)."""
        banned_fields = {
            "outcome", "result", "success", "legality",
            "damage", "hp_change", "error",
        }
        field_names = {f.name for f in dataclasses.fields(ObjectPositionUpdate)}
        overlap = field_names & banned_fields
        assert not overlap, f"ObjectPositionUpdate has banned outcome fields: {overlap}"


# ---------------------------------------------------------------------------
# UI-G2: Zone validation (3 tests)
# ---------------------------------------------------------------------------

class TestUIG2ZoneValidation:
    """Zone names, position validation, accept/reject."""

    def test_valid_zone_names_defined_and_enumerable(self):
        """Valid zone names are defined and enumerable."""
        assert isinstance(VALID_ZONES, frozenset)
        assert VALID_ZONES == frozenset({"player", "map", "dm"})
        assert len(VALID_ZONES) == 3

    def test_position_update_to_invalid_zone_rejected(self):
        """Position update to invalid zone is rejected."""
        # Zone that doesn't exist
        error = validate_zone_position((0.0, 0.05, 0.0), "dungeon")
        assert error is not None
        assert "Invalid zone" in error

        # Valid zone name but position outside that zone's bounds
        error = validate_zone_position((0.0, 0.05, 3.0), "dm")
        assert error is not None
        assert "not within zone" in error

    def test_position_update_to_valid_zone_accepted(self):
        """Position update to valid zone is accepted."""
        # Player zone center
        error = validate_zone_position((0.0, 0.05, 3.0), "player")
        assert error is None

        # Map zone center
        error = validate_zone_position((0.0, 0.05, -0.5), "map")
        assert error is None

        # DM zone center
        error = validate_zone_position((0.0, 0.05, -3.5), "dm")
        assert error is None

        # zone_for_position confirms zone detection
        assert zone_for_position(0.0, 3.0) == "player"
        assert zone_for_position(0.0, -0.5) == "map"
        assert zone_for_position(0.0, -3.5) == "dm"
        assert zone_for_position(10.0, 10.0) is None  # outside all zones


# ---------------------------------------------------------------------------
# UI-G3: Registry consistency (2 tests)
# ---------------------------------------------------------------------------

class TestUIG3RegistryConsistency:
    """Object registry — add/get/remove, duplicate handling."""

    def test_registry_tracks_objects_by_id(self):
        """Object registry tracks objects by id (add/get/remove)."""
        reg = TableObjectRegistry()
        obj1 = TableObjectState("card_1", "card", (0.0, 0.05, 3.0), "player")
        obj2 = TableObjectState("card_2", "card", (1.0, 0.05, 3.0), "player")

        reg.add(obj1)
        reg.add(obj2)
        assert len(reg) == 2

        assert reg.get("card_1") == obj1
        assert reg.get("card_2") == obj2
        assert reg.get("card_3") is None

        removed = reg.remove("card_1")
        assert removed == obj1
        assert len(reg) == 1
        assert reg.get("card_1") is None

        # Remove non-existent returns None
        assert reg.remove("card_99") is None

    def test_duplicate_object_id_rejected(self):
        """Duplicate object_id is rejected (raises ValueError)."""
        reg = TableObjectRegistry()
        obj = TableObjectState("card_1", "card", (0.0, 0.05, 3.0), "player")
        reg.add(obj)

        # Adding same id again raises ValueError
        with pytest.raises(ValueError, match="Duplicate object_id"):
            reg.add(obj)


# ---------------------------------------------------------------------------
# UI-G4: Hard bans — static scan (2 tests)
# ---------------------------------------------------------------------------

class TestUIG4HardBans:
    """Static analysis gates — no banned strings in UI code, no action-verb REQUEST names."""

    @staticmethod
    def _ui_source_files() -> list[Path]:
        """Return all Python source files in aidm/ui/."""
        ui_dir = Path(__file__).resolve().parent.parent / "aidm" / "ui"
        return list(ui_dir.glob("*.py"))

    def test_no_tooltip_popover_snippet_strings(self):
        """No tooltip/popover/snippet strings in UI schema code (doctrine section 3)."""
        banned_tokens = {"tooltip", "popover", "snippet"}
        violations = []

        for src_file in self._ui_source_files():
            content = src_file.read_text(encoding="utf-8").lower()
            for token in banned_tokens:
                if token in content:
                    violations.append(f"{src_file.name} contains '{token}'")

        assert not violations, f"Hard ban violations: {violations}"

    def test_no_action_verb_request_type_names(self):
        """No 'do the action' verbs in new REQUEST type names."""
        # This now also covers ObjectPositionUpdate's naming.
        # The name "ObjectPositionUpdate" does not start with any banned verb.
        banned_verbs = {"Roll", "Cast", "Attack", "EndTurn"}

        for req_cls in ALL_REQUEST_TYPES:
            for verb in banned_verbs:
                assert not req_cls.__name__.startswith(verb), (
                    f"REQUEST type {req_cls.__name__} starts with banned verb '{verb}'"
                )

        # Also verify ObjectPositionUpdate name is clean
        name = "ObjectPositionUpdate"
        for verb in banned_verbs:
            assert not name.startswith(verb), (
                f"Type {name} starts with banned verb '{verb}'"
            )
