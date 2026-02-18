"""Gate G tests — Table UI Phase 2+3+4 backend contracts.

22 tests across 8 gate categories (UI-G1 through UI-G8).

Categories:
    UI-G1: TableObject types (3 tests)
    UI-G2: Zone validation (3 tests)
    UI-G3: Registry consistency (2 tests)
    UI-G4: Hard bans — static scan (2 tests)
    UI-G5: Drift guards (3 tests)
    UI-G6: Zone authority gates (3 tests)
    UI-G7: Dice tray / dice tower / PENDING_ROLL handshake (3 tests)
    UI-G8: Protocol registry + roll_result formalization (3 tests)

Authority: WO-UI-02, WO-UI-03, WO-UI-04, WO-UI-DRIFT-GUARD, WO-UI-ZONE-AUTHORITY,
    DOCTRINE_04_TABLE_UI_MEMO_V4.
"""
from __future__ import annotations

import ast
import dataclasses
import json
import math
import re
import typing
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
        assert VALID_ZONES == frozenset({"player", "map", "dm", "dice_tray", "dice_tower"})
        assert len(VALID_ZONES) == 5

    def test_position_update_to_invalid_zone_rejected(self):
        """Position update to invalid zone is rejected."""
        # Zone that doesn't exist
        result = validate_zone_position((0.0, 0.05, 0.0), "dungeon")
        assert result is False

        # Valid zone name but position outside that zone's bounds
        result = validate_zone_position((0.0, 0.05, 3.0), "dm")
        assert result is False

    def test_position_update_to_valid_zone_accepted(self):
        """Position update to valid zone is accepted."""
        # Player zone center
        result = validate_zone_position((0.0, 0.05, 3.0), "player")
        assert result is True

        # Map zone center
        result = validate_zone_position((0.0, 0.05, -0.5), "map")
        assert result is True

        # DM zone center
        result = validate_zone_position((0.0, 0.05, -3.5), "dm")
        assert result is True

        # Dice tray zone center
        result = validate_zone_position((4.5, 0.3, 1.75), "dice_tray")
        assert result is True

        # Dice tower zone center
        result = validate_zone_position((4.5, 0.3, 0.5), "dice_tower")
        assert result is True

        # zone_for_position confirms zone detection
        assert zone_for_position(0.0, 3.0) == "player"
        assert zone_for_position(0.0, -0.5) == "map"
        assert zone_for_position(0.0, -3.5) == "dm"
        assert zone_for_position(4.5, 1.75) == "dice_tray"
        assert zone_for_position(4.5, 0.5) == "dice_tower"
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


# ---------------------------------------------------------------------------
# UI-G5: Drift guards (3 tests)
# ---------------------------------------------------------------------------

class TestUIG5DriftGuards:
    """Static drift guards — no canonical path, no backflow imports, no teaching strings."""

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parent.parent

    def test_no_canonical_path_for_table_object_types(self):
        """ObjectPositionUpdate/TableObjectState not registered in EventLog or replay_runner.

        Neither type should appear as a registered event type, reducer case,
        or import in aidm/core/event_log.py or aidm/core/replay_runner.py.
        """
        root = self._project_root()
        banned_names = {"ObjectPositionUpdate", "TableObjectState"}
        violations = []

        for rel_path in ("aidm/core/event_log.py", "aidm/core/replay_runner.py"):
            src_file = root / rel_path
            if not src_file.exists():
                continue
            content = src_file.read_text(encoding="utf-8")
            for name in banned_names:
                if name in content:
                    violations.append(f"{rel_path} references {name}")

        assert not violations, (
            f"UI types leaked into canonical path: {violations}"
        )

    def test_no_backflow_imports_in_ui_boundary(self):
        """aidm/ui/ modules do not import from Oracle, EventLog, replay_runner, Lens, or Immersion.

        The UI boundary layer must not depend on canonical state layers.
        """
        root = self._project_root()
        ui_dir = root / "aidm" / "ui"
        banned_import_prefixes = (
            "aidm.oracle",
            "aidm.core.event_log",
            "aidm.core.replay_runner",
            "aidm.core.provenance",
            "aidm.lens",
            "aidm.immersion",
        )
        violations = []

        for src_file in ui_dir.glob("*.py"):
            try:
                tree = ast.parse(src_file.read_text(encoding="utf-8"))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for prefix in banned_import_prefixes:
                            if alias.name.startswith(prefix):
                                violations.append(
                                    f"{src_file.name}: import {alias.name}"
                                )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for prefix in banned_import_prefixes:
                            if node.module.startswith(prefix):
                                violations.append(
                                    f"{src_file.name}: from {node.module} import ..."
                                )

        assert not violations, (
            f"Backflow imports in aidm/ui/: {violations}"
        )

    def test_no_teaching_strings_in_table_objects(self):
        """Zone validation code in table_objects.py has no user-facing explanation strings.

        Static scan for banned patterns: tooltip, popover, error_message,
        explanation, reason, because, cannot, can't, invalid.*zone.*message.
        """
        root = self._project_root()
        src_file = root / "aidm" / "ui" / "table_objects.py"
        content = src_file.read_text(encoding="utf-8").lower()

        banned_tokens = [
            "tooltip",
            "popover",
            "error_message",
            "explanation",
            "reason",
            "because",
            "cannot",
            "can't",
        ]
        banned_patterns = [
            re.compile(r"invalid.*zone.*message", re.IGNORECASE),
        ]

        violations = []
        for token in banned_tokens:
            if token in content:
                violations.append(f"contains '{token}'")

        original_content = src_file.read_text(encoding="utf-8")
        for pattern in banned_patterns:
            if pattern.search(original_content):
                violations.append(f"matches pattern '{pattern.pattern}'")

        assert not violations, (
            f"Teaching string violations in table_objects.py: {violations}"
        )


# ---------------------------------------------------------------------------
# UI-G6: Zone authority gates (3 tests)
# ---------------------------------------------------------------------------

class TestUIG6ZoneAuthority:
    """Zone authority gates — single source of truth, return type, frustum."""

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parent.parent

    def test_validate_zone_position_returns_bool(self):
        """validate_zone_position return annotation is bool (not Optional[str])."""
        hints = typing.get_type_hints(validate_zone_position)
        assert hints["return"] is bool, (
            f"Expected return annotation bool, got {hints['return']}"
        )

    def test_zone_parity_no_hardcoded_zone_coordinates(self):
        """No hardcoded zone boundary coordinates outside zones.json (UI-G6).

        Scans table_objects.py and zones.ts for numeric patterns that look
        like zone coordinate tuples/arrays. The only zone data source should
        be aidm/ui/zones.json.
        """
        root = self._project_root()
        zones_json_path = root / "aidm" / "ui" / "zones.json"
        assert zones_json_path.exists(), "zones.json must exist"

        # Load zones.json as the authoritative source
        zones = json.loads(zones_json_path.read_text(encoding="utf-8"))
        assert len(zones) == 5, f"Expected 5 zones, got {len(zones)}"

        # Scan Python: table_objects.py should NOT contain literal zone tuples
        py_file = root / "aidm" / "ui" / "table_objects.py"
        py_content = py_file.read_text(encoding="utf-8")

        # Pattern: look for tuples like (0.0, -0.5, 3.0, 2.0) — 4-element
        # numeric tuples that match zone bound shapes
        zone_tuple_pattern = re.compile(
            r'\(\s*-?\d+\.?\d*\s*,\s*-?\d+\.?\d*\s*,\s*\d+\.?\d*\s*,\s*\d+\.?\d*\s*\)'
        )
        py_matches = zone_tuple_pattern.findall(py_content)
        assert not py_matches, (
            f"Hardcoded zone coordinate tuples in table_objects.py: {py_matches}"
        )

        # Scan TypeScript: zones.ts should NOT contain literal zone arrays
        ts_file = root / "client" / "src" / "zones.ts"
        ts_content = ts_file.read_text(encoding="utf-8")

        # Pattern: look for lines with centerX/centerZ/halfWidth/halfHeight
        # numeric literals (not from JSON import)
        # A hardcoded zone def looks like:
        #   { name: 'player', centerX: 0, centerZ: 3, halfWidth: 5, ...}
        hardcoded_zone_pattern = re.compile(
            r"centerX:\s*-?\d+\.?\d*\s*,\s*centerZ:\s*-?\d+\.?\d*\s*,"
            r"\s*halfWidth:\s*\d+\.?\d*\s*,\s*halfHeight:\s*\d+\.?\d*"
        )
        ts_matches = hardcoded_zone_pattern.findall(ts_content)
        assert not ts_matches, (
            f"Hardcoded zone coordinates in zones.ts: {ts_matches}"
        )

    def test_camera_frustum_zones_visible_from_standard(self):
        """All zone centers are visible from STANDARD camera posture (UI-G6).

        Pure Python frustum containment check using Three.js-equivalent math.
        Camera params from client/src/camera.ts and client/src/main.ts.
        """
        root = self._project_root()
        zones_json_path = root / "aidm" / "ui" / "zones.json"
        zones = json.loads(zones_json_path.read_text(encoding="utf-8"))

        # Camera parameters (source: client/src/main.ts lines 36-41)
        fov_deg = 60
        aspect = 16 / 9  # common default; test uses a reasonable aspect
        near = 0.1
        far = 100.0

        # Camera postures (source: client/src/camera.ts lines 21-34)
        postures = {
            "STANDARD": {
                "position": (0.0, 5.0, 8.0),
                "lookAt": (0.0, 0.0, 0.0),
            },
            "DOWN": {
                "position": (0.0, 8.0, 3.0),
                "lookAt": (0.0, 0.0, 1.0),
            },
            "LEAN_FORWARD": {
                "position": (0.0, 4.0, 4.0),
                "lookAt": (0.0, 0.0, -2.0),
            },
        }

        def _normalize(v):
            length = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
            if length == 0:
                return (0, 0, 0)
            return (v[0]/length, v[1]/length, v[2]/length)

        def _cross(a, b):
            return (
                a[1]*b[2] - a[2]*b[1],
                a[2]*b[0] - a[0]*b[2],
                a[0]*b[1] - a[1]*b[0],
            )

        def _sub(a, b):
            return (a[0]-b[0], a[1]-b[1], a[2]-b[2])

        def _dot(a, b):
            return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

        def _mat4_mul(m, v4):
            """Multiply 4x4 matrix (row-major list of 16) by vec4."""
            result = [0.0, 0.0, 0.0, 0.0]
            for i in range(4):
                result[i] = sum(m[i*4+j] * v4[j] for j in range(4))
            return result

        def _build_view_matrix(pos, look_at):
            """Build a view (lookAt) matrix — Three.js convention."""
            forward = _normalize(_sub(pos, look_at))
            right = _normalize(_cross((0, 1, 0), forward))
            up = _cross(forward, right)
            return [
                right[0], right[1], right[2], -_dot(right, pos),
                up[0], up[1], up[2], -_dot(up, pos),
                forward[0], forward[1], forward[2], -_dot(forward, pos),
                0, 0, 0, 1,
            ]

        def _build_projection_matrix(fov_deg_, aspect_, near_, far_):
            """Build a perspective projection matrix — Three.js convention."""
            fov_rad = math.radians(fov_deg_)
            top = near_ * math.tan(fov_rad / 2)
            bottom = -top
            right = top * aspect_
            left = -right
            return [
                2*near_/(right-left), 0, (right+left)/(right-left), 0,
                0, 2*near_/(top-bottom), (top+bottom)/(top-bottom), 0,
                0, 0, -(far_+near_)/(far_-near_), -2*far_*near_/(far_-near_),
                0, 0, -1, 0,
            ]

        def _is_point_in_frustum(point, view_mat, proj_mat):
            """Check if a 3D point is within the camera frustum."""
            # Transform to view space
            p4 = [point[0], point[1], point[2], 1.0]
            view_p = _mat4_mul(view_mat, p4)
            # Transform to clip space
            clip_p = _mat4_mul(proj_mat, view_p)
            w = clip_p[3]
            if w == 0:
                return False
            # NDC coordinates
            ndc_x = clip_p[0] / w
            ndc_y = clip_p[1] / w
            ndc_z = clip_p[2] / w
            # Check if within [-1, 1] for all axes
            return (-1 <= ndc_x <= 1) and (-1 <= ndc_y <= 1) and (-1 <= ndc_z <= 1)

        proj_mat = _build_projection_matrix(fov_deg, aspect, near, far)

        # Test: every zone center is visible from at least STANDARD posture
        standard = postures["STANDARD"]
        view_mat = _build_view_matrix(standard["position"], standard["lookAt"])

        for zone in zones:
            # Zone center at y=0 (table surface)
            point = (zone["centerX"], 0.0, zone["centerZ"])
            visible = _is_point_in_frustum(point, view_mat, proj_mat)
            assert visible, (
                f"Zone {zone['name']!r} center {point} is NOT visible "
                f"from STANDARD posture"
            )


# ---------------------------------------------------------------------------
# UI-G7: Dice tray / tower / PENDING_ROLL handshake (3 tests)
# ---------------------------------------------------------------------------

class TestUIG7DiceTrayTower:
    """UI Phase 3 gates — no mechanical authority, handshake determinism, replay stability."""

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parent.parent

    def test_no_mechanical_authority_in_client(self):
        """No RNG calls, roll resolution, or modifier application in client/src/.

        Scans all .ts files in client/src/ for banned patterns:
        Math.random, crypto.getRandomValues, dice roll functions,
        and modifier arithmetic that would bypass Box authority.
        """
        root = self._project_root()
        client_src = root / "client" / "src"
        assert client_src.exists(), "client/src/ must exist"

        banned_patterns = [
            # Direct RNG
            re.compile(r"Math\.random\s*\("),
            re.compile(r"crypto\.getRandomValues\s*\("),
            # Roll resolution — functions that compute roll outcomes
            re.compile(r"function\s+roll[A-Z_]"),
            re.compile(r"const\s+roll\s*="),
            re.compile(r"let\s+roll\s*="),
            # d20 roll computation (not string literals like 'd20')
            re.compile(r"\+\s*Math\.floor\s*\("),
            # Modifier application that would imply roll resolution
            re.compile(r"attackBonus|attack_bonus|damageBonus|damage_bonus", re.IGNORECASE),
        ]

        violations = []
        for ts_file in client_src.glob("*.ts"):
            content = ts_file.read_text(encoding="utf-8")
            for pattern in banned_patterns:
                matches = pattern.findall(content)
                if matches:
                    violations.append(
                        f"{ts_file.name}: matches '{pattern.pattern}' ({len(matches)}x)"
                    )

        assert not violations, (
            f"Mechanical authority violations in client/src/: {violations}"
        )

    def test_pending_handshake_determinism(self):
        """PENDING_ROLL → CONFIRMED transition is deterministic.

        Given identical PendingRoll inputs, the same DiceTowerDropIntent
        produces the same state transition. No implicit timeouts.
        """
        from aidm.ui.pending import (
            PendingRoll,
            PendingStateMachine,
            DiceTowerDropIntent,
        )

        # Run the same scenario multiple times — must produce identical results
        results = []
        for _ in range(5):
            sm = PendingStateMachine()

            # Emit identical PENDING_ROLL
            cancelled = sm.emit(PendingRoll(spec="1d20", pending_handle="roll_001"))
            assert cancelled is None  # No prior PENDING

            # Verify active
            assert sm.active is not None
            assert isinstance(sm.active, PendingRoll)
            assert sm.active.pending_handle == "roll_001"

            # Resolve with matching DiceTowerDropIntent
            resolved = sm.resolve(
                DiceTowerDropIntent(
                    dice_ids=("d20",),
                    pending_roll_handle="roll_001",
                )
            )
            results.append(resolved)

            # Verify cleared
            assert sm.active is None

        # All runs must produce True (resolved)
        assert all(r is True for r in results), (
            f"Non-deterministic handshake results: {results}"
        )

        # Mismatched handle must not resolve
        sm2 = PendingStateMachine()
        sm2.emit(PendingRoll(spec="1d20", pending_handle="roll_002"))
        not_resolved = sm2.resolve(
            DiceTowerDropIntent(
                dice_ids=("d20",),
                pending_roll_handle="wrong_handle",
            )
        )
        assert not_resolved is False, "Mismatched handle should not resolve"
        assert sm2.active is not None, "PENDING should still be active after failed resolve"

    def test_replay_stability(self):
        """Same PENDING_ROLL → confirm → result sequence produces same final state.

        Replay guarantee: if the event log replays, the state machine
        arrives at the same state.
        """
        from aidm.ui.pending import (
            PendingRoll,
            PendingStateMachine,
            DiceTowerDropIntent,
        )

        def _run_sequence() -> list:
            """Run a deterministic sequence and capture state transitions."""
            sm = PendingStateMachine()
            states = []

            # Step 1: Emit PENDING_ROLL for attack
            sm.emit(PendingRoll(spec="1d20+5", pending_handle="atk_001"))
            states.append(("emit_atk", type(sm.active).__name__ if sm.active else None))

            # Step 2: Player drops dice
            r1 = sm.resolve(DiceTowerDropIntent(
                dice_ids=("d20",),
                pending_roll_handle="atk_001",
            ))
            states.append(("resolve_atk", r1, sm.active))

            # Step 3: Emit PENDING_ROLL for saving throw
            sm.emit(PendingRoll(spec="1d20", pending_handle="save_001"))
            states.append(("emit_save", type(sm.active).__name__ if sm.active else None))

            # Step 4: New PENDING cancels previous (if any)
            sm.emit(PendingRoll(spec="1d20+3", pending_handle="save_002"))
            states.append(("emit_save2", type(sm.active).__name__ if sm.active else None))

            # Step 5: Resolve second save
            r2 = sm.resolve(DiceTowerDropIntent(
                dice_ids=("d20",),
                pending_roll_handle="save_002",
            ))
            states.append(("resolve_save2", r2, sm.active))

            return states

        # Run the sequence twice — must produce identical state traces
        trace_a = _run_sequence()
        trace_b = _run_sequence()

        assert trace_a == trace_b, (
            f"Replay divergence detected:\n"
            f"  Run A: {trace_a}\n"
            f"  Run B: {trace_b}"
        )


# ---------------------------------------------------------------------------
# UI-G8: Protocol registry + roll_result formalization (3 tests)
# ---------------------------------------------------------------------------

class TestUIG8ProtocolRegistry:
    """WO-UI-04 gates — message registry, roll_result roundtrip, wildcard removal."""

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parent.parent

    def test_protocol_registry_rejects_unknown_types(self):
        """Unknown message types are rejected by the registry (UI-G8-protocol-registry).

        Also verifies that roll_result IS registered — proving the registry
        is load-bearing, not decorative.
        """
        from aidm.ui.ws_protocol import (
            MESSAGE_REGISTRY,
            RollResult,
            parse_message,
        )

        # Unknown type must raise ValueError
        with pytest.raises(ValueError, match="Unknown message type"):
            parse_message({"type": "garbage_nonexistent_type"})

        # Message with no type field must raise ValueError
        with pytest.raises(ValueError, match="no 'type' or 'msg_type'"):
            parse_message({"d20_result": 15, "total": 20, "success": True})

        # roll_result IS registered
        assert "roll_result" in MESSAGE_REGISTRY
        assert MESSAGE_REGISTRY["roll_result"] is RollResult

        # Prove registry is load-bearing: removing roll_result would break
        # parsing of roll_result messages
        saved = MESSAGE_REGISTRY.pop("roll_result")
        try:
            with pytest.raises(ValueError, match="Unknown message type"):
                parse_message({
                    "type": "roll_result",
                    "d20_result": 15,
                    "total": 20,
                    "success": True,
                })
        finally:
            MESSAGE_REGISTRY["roll_result"] = saved

    def test_roll_result_roundtrip_deterministic(self):
        """Full dice handshake → RollResult round-trip is deterministic (UI-G8-roll-roundtrip).

        1. Create PENDING_ROLL state
        2. Simulate DiceTowerDropIntent
        3. Produce roll_result via RollResult.to_dict()
        4. Deserialize via RollResult.from_dict()
        5. Assert field values match
        6. Assert replay-stable (same inputs → same to_dict() bytes)
        """
        from aidm.ui.pending import (
            PendingRoll,
            PendingStateMachine,
            DiceTowerDropIntent,
        )
        from aidm.ui.ws_protocol import RollResult, parse_message

        # Step 1: Create PENDING_ROLL state
        sm = PendingStateMachine()
        sm.emit(PendingRoll(spec="1d20+5", pending_handle="atk_042"))
        assert sm.active is not None

        # Step 2: Simulate DiceTowerDropIntent
        resolved = sm.resolve(
            DiceTowerDropIntent(dice_ids=("d20",), pending_roll_handle="atk_042")
        )
        assert resolved is True
        assert sm.active is None

        # Step 3: Produce roll_result via RollResult.to_dict()
        result = RollResult(d20_result=17, total=22, success=True)
        raw = result.to_dict()
        assert raw == {
            "type": "roll_result",
            "d20_result": 17,
            "total": 22,
            "success": True,
        }

        # Step 4: Deserialize via from_dict() and parse_message()
        restored = RollResult.from_dict(raw)
        assert restored == result
        assert restored.d20_result == 17
        assert restored.total == 22
        assert restored.success is True

        # Also test via parse_message() dispatch
        parsed = parse_message(raw)
        assert isinstance(parsed, RollResult)
        assert parsed == result

        # Step 5+6: Replay stability — same inputs → identical to_dict()
        results = []
        for _ in range(10):
            r = RollResult(d20_result=17, total=22, success=True)
            results.append(json.dumps(r.to_dict(), sort_keys=True))

        assert len(set(results)) == 1, (
            f"Non-deterministic RollResult serialization: {set(results)}"
        )

    def test_roll_result_not_in_wildcard_handler(self):
        """roll_result is consumed via typed handler, not wildcard sniffing (UI-G8).

        Scans main.ts for the wildcard handler block and verifies that
        roll_result / ROLL_RESULT checks are NOT inside the wildcard
        callback. A dedicated bridge.on('roll_result', ...) must exist.
        """
        root = self._project_root()
        main_ts = root / "client" / "src" / "main.ts"
        content = main_ts.read_text(encoding="utf-8")

        # Find the wildcard handler block: bridge.on('*', (data) => { ... });
        wildcard_start = content.find("bridge.on('*'")
        assert wildcard_start != -1, "Expected wildcard handler in main.ts"

        # Find the closing }); of the wildcard handler callback
        # Search for the first }); after the wildcard start
        wildcard_end = content.find("});", wildcard_start)
        assert wildcard_end != -1, "Could not find wildcard handler closing"
        wildcard_block = content[wildcard_start:wildcard_end + 3]

        # The wildcard block must NOT contain roll_result sniffing
        roll_result_patterns = [
            "isRollResult",
            "'roll_result'",
            '"roll_result"',
            "'ROLL_RESULT'",
            '"ROLL_RESULT"',
        ]
        violations = []
        for pattern in roll_result_patterns:
            if pattern in wildcard_block:
                violations.append(f"wildcard handler contains {pattern}")

        assert not violations, (
            f"roll_result still consumed via wildcard handler: {violations}"
        )

        # Verify a dedicated typed handler exists
        assert "bridge.on('roll_result'" in content, (
            "No dedicated bridge.on('roll_result', ...) handler found in main.ts"
        )
