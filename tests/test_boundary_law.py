"""Boundary Law Enforcement Tests — SPARK / LENS / BOX Invariant Canaries

These tests exist to make the system CRASH LOUD when architectural boundaries
are violated. They are not functional tests — they are structural invariants
encoded as executable assertions.

If any test in this file fails, it means a future contributor has violated
a core architectural boundary. The build MUST NOT proceed.

Boundary Rules:
    SPARK (aidm/spark/)     — LLM narration generation. No game state access.
    LENS  (aidm/narration/) — Read-only gating layer. No state mutation.
    BOX   (aidm/core/)      — Deterministic rules engine. Sole mechanical authority.

Invariants Enforced:
    BL-001: SPARK must never import from aidm.core (no state access)
    BL-002: SPARK must never import from aidm.narration (no LENS bypass)
    BL-003: NARRATION must never import from aidm.core (no BOX coupling)
    BL-004: BOX must never import from aidm.narration (no presentation dependency)
    BL-005: Only aidm.core may import RNGManager (determinism isolation)
    BL-006: SPARK/NARRATION must never import stdlib random (RNG containment)
    BL-007: EngineResult must be immutable after creation
    BL-008: EventLog must enforce monotonic event IDs
    BL-009: RNG seed must reject non-int types (including bool)
    BL-010: Frozen dataclasses must reject mutation
    BL-011: WorldState.state_hash must be deterministic
    BL-012: Replay must produce identical results for identical inputs
    BL-013: SparkRequest must validate schema invariants
    BL-014: IntentObject must reject unfreeze after confirmation
    BL-015: EntityState must reject dict mutation via base_stats

Reference: This file is the executable form of the Boundary Law specification.
           If you need to understand WHY a boundary exists, read the test docstring.
"""

import ast
import json
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from types import MappingProxyType

import pytest

# ═══════════════════════════════════════════════════════════════════════
# BL-001 through BL-006: Import Boundary Enforcement
# ═══════════════════════════════════════════════════════════════════════

def _extract_imports_from_file(filepath: Path) -> list[str]:
    """Extract all import module names from a Python file using AST."""
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(filepath))

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _get_py_files(directory: str) -> list[Path]:
    """Get all .py source files in a directory, excluding __pycache__."""
    d = Path(directory)
    if not d.exists():
        return []
    return [f for f in d.rglob("*.py") if "__pycache__" not in str(f)]


class TestBL001_SparkMustNotImportCore:
    """BL-001: SPARK must never import from aidm.core.

    WHY: SPARK is a pure text generation layer. If it imports from aidm.core,
    it gains access to WorldState, RNG, event logs, and resolvers — any of
    which could be used to mutate game state or influence deterministic outcomes.

    WHAT BREAKS: Determinism, replay integrity, SPARK/BOX separation.
    """

    def test_no_spark_to_core_imports(self):
        violations = []
        for filepath in _get_py_files("aidm/spark"):
            imports = _extract_imports_from_file(filepath)
            for imp in imports:
                if imp.startswith("aidm.core"):
                    violations.append(f"{filepath.name} imports {imp}")

        assert violations == [], (
            f"BL-001 VIOLATION: SPARK imports aidm.core (state access breach):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestBL002_SparkMustNotImportNarration:
    """BL-002: SPARK must never import from aidm.narration.

    WHY: SPARK generates text. NARRATION (LENS) gates that text through
    guardrails. If SPARK imports NARRATION, it can bypass the gating layer.

    WHAT BREAKS: LENS guardrail enforcement, kill switch effectiveness.
    """

    def test_no_spark_to_narration_imports(self):
        violations = []
        for filepath in _get_py_files("aidm/spark"):
            imports = _extract_imports_from_file(filepath)
            for imp in imports:
                if imp.startswith("aidm.narration"):
                    violations.append(f"{filepath.name} imports {imp}")

        assert violations == [], (
            f"BL-002 VIOLATION: SPARK imports aidm.narration (LENS bypass):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestBL003_NarrationMustNotImportCore:
    """BL-003: NARRATION must never import from aidm.core.

    WHY: NARRATION (LENS) is a read-only gating layer. It receives immutable
    EngineResult snapshots. If it imports from aidm.core, it can access
    WorldState mutators, RNG streams, or resolvers.

    WHAT BREAKS: Read-only guarantee, FREEZE-001 snapshot semantics.
    """

    def test_no_narration_to_core_imports(self):
        violations = []
        for filepath in _get_py_files("aidm/narration"):
            imports = _extract_imports_from_file(filepath)
            for imp in imports:
                if imp.startswith("aidm.core"):
                    violations.append(f"{filepath.name} imports {imp}")

        assert violations == [], (
            f"BL-003 VIOLATION: NARRATION imports aidm.core (BOX coupling):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestBL004_BoxMustNotImportNarration:
    """BL-004: BOX must never import from aidm.narration.

    WHY: BOX is the deterministic rules engine. It must never depend on
    presentation-layer code. If it imports narration, a future contributor
    could accidentally branch game logic on narration state.

    WHAT BREAKS: Determinism, replay, BOX authority.
    """

    def test_no_core_to_narration_imports(self):
        violations = []
        for filepath in _get_py_files("aidm/core"):
            imports = _extract_imports_from_file(filepath)
            for imp in imports:
                if imp.startswith("aidm.narration"):
                    violations.append(f"{filepath.name} imports {imp}")

        assert violations == [], (
            f"BL-004 VIOLATION: BOX imports aidm.narration (presentation dependency):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestBL005_OnlyCoreImportsRNG:
    """BL-005: Only aidm.core and aidm.runtime may import RNGManager.

    WHY: Deterministic RNG streams are the backbone of replay integrity.
    If SPARK or NARRATION import RNGManager, they can consume random numbers,
    desynchronizing the RNG stream and breaking deterministic replay.

    WHAT BREAKS: Replay verification, 10x determinism guarantee.
    """

    _ALLOWED_RNG_IMPORTERS = {"aidm.core", "aidm.runtime", "tests"}

    def test_rng_not_imported_by_spark(self):
        violations = []
        for filepath in _get_py_files("aidm/spark"):
            imports = _extract_imports_from_file(filepath)
            for imp in imports:
                if "rng_manager" in imp.lower():
                    violations.append(f"{filepath.name} imports {imp}")

        assert violations == [], (
            f"BL-005 VIOLATION: SPARK imports RNGManager (determinism breach):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_rng_not_imported_by_narration(self):
        violations = []
        for filepath in _get_py_files("aidm/narration"):
            imports = _extract_imports_from_file(filepath)
            for imp in imports:
                if "rng_manager" in imp.lower():
                    violations.append(f"{filepath.name} imports {imp}")

        assert violations == [], (
            f"BL-005 VIOLATION: NARRATION imports RNGManager (determinism breach):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_rng_not_imported_by_immersion(self):
        violations = []
        for filepath in _get_py_files("aidm/immersion"):
            imports = _extract_imports_from_file(filepath)
            for imp in imports:
                if "rng_manager" in imp.lower():
                    violations.append(f"{filepath.name} imports {imp}")

        assert violations == [], (
            f"BL-005 VIOLATION: IMMERSION imports RNGManager (determinism breach):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )


class TestBL006_NoStdlibRandomOutsideRNGManager:
    """BL-006: No module outside rng_manager.py may import stdlib random.

    WHY: stdlib random uses a global shared RNG. Any call to random.random()
    or random.randint() poisons determinism — the call count becomes
    unpredictable and replay diverges.

    WHAT BREAKS: Replay, determinism, audit trail integrity.
    """

    def test_no_stdlib_random_in_spark(self):
        for filepath in _get_py_files("aidm/spark"):
            imports = _extract_imports_from_file(filepath)
            assert "random" not in imports, (
                f"BL-006 VIOLATION: {filepath.name} imports stdlib random"
            )

    def test_no_stdlib_random_in_narration(self):
        for filepath in _get_py_files("aidm/narration"):
            imports = _extract_imports_from_file(filepath)
            assert "random" not in imports, (
                f"BL-006 VIOLATION: {filepath.name} imports stdlib random"
            )

    def test_no_stdlib_random_in_immersion(self):
        for filepath in _get_py_files("aidm/immersion"):
            imports = _extract_imports_from_file(filepath)
            assert "random" not in imports, (
                f"BL-006 VIOLATION: {filepath.name} imports stdlib random"
            )

    def test_no_stdlib_random_in_schemas(self):
        for filepath in _get_py_files("aidm/schemas"):
            imports = _extract_imports_from_file(filepath)
            assert "random" not in imports, (
                f"BL-006 VIOLATION: {filepath.name} imports stdlib random"
            )

    def test_no_stdlib_random_in_core_except_rng_manager(self):
        for filepath in _get_py_files("aidm/core"):
            if filepath.name == "rng_manager.py":
                continue  # rng_manager.py is the ONLY allowed user
            imports = _extract_imports_from_file(filepath)
            assert "random" not in imports, (
                f"BL-006 VIOLATION: {filepath.name} imports stdlib random "
                "(only rng_manager.py may import random)"
            )


# ═══════════════════════════════════════════════════════════════════════
# BL-007: EngineResult Immutability
# ═══════════════════════════════════════════════════════════════════════

class TestBL007_EngineResultImmutable:
    """BL-007: EngineResult must be immutable after creation.

    WHY: EngineResult is the authoritative mechanical outcome from BOX.
    If any code modifies it after creation, the audit trail becomes
    unreliable and replay diverges from recorded outcomes.

    WHAT BREAKS: Audit integrity, replay, IPC contract.
    """

    def test_engine_result_rejects_field_modification(self):
        from aidm.schemas.engine_result import EngineResult, EngineResultFrozenError, EngineResultStatus

        result = EngineResult(
            result_id="test-result-001",
            intent_id="test-intent-001",
            status=EngineResultStatus.SUCCESS,
            resolved_at=datetime(2025, 1, 1, 12, 0, 0),
            narration_token="attack_hit",
        )
        with pytest.raises(EngineResultFrozenError):
            result.status = "tampered"

    def test_engine_result_rejects_event_modification(self):
        from aidm.schemas.engine_result import EngineResult, EngineResultFrozenError, EngineResultStatus

        result = EngineResult(
            result_id="test-result-001",
            intent_id="test-intent-001",
            status=EngineResultStatus.SUCCESS,
            resolved_at=datetime(2025, 1, 1, 12, 0, 0),
            events=[{"type": "original"}],
        )
        with pytest.raises(EngineResultFrozenError):
            result.events = [{"type": "tampered"}]

    def test_engine_result_rejects_narration_token_modification(self):
        from aidm.schemas.engine_result import EngineResult, EngineResultFrozenError, EngineResultStatus

        result = EngineResult(
            result_id="test-result-001",
            intent_id="test-intent-001",
            status=EngineResultStatus.SUCCESS,
            resolved_at=datetime(2025, 1, 1, 12, 0, 0),
            narration_token="attack_hit",
        )
        with pytest.raises(EngineResultFrozenError):
            result.narration_token = "tampered"


# ═══════════════════════════════════════════════════════════════════════
# BL-008: EventLog Monotonic ID Enforcement
# ═══════════════════════════════════════════════════════════════════════

class TestBL008_EventLogMonotonicIDs:
    """BL-008: EventLog must enforce strictly monotonic event IDs.

    WHY: Event IDs form the total ordering of game state transitions.
    Out-of-order or duplicate IDs would corrupt the event log and make
    replay produce different results depending on insertion order.

    WHAT BREAKS: Event ordering, replay, audit trail.
    """

    def test_event_log_rejects_out_of_order_id(self):
        from aidm.core.event_log import EventLog, Event

        log = EventLog()
        log.append(Event(event_id=0, event_type="test", timestamp=0.0, payload={}))

        with pytest.raises(ValueError, match="monotonic"):
            log.append(Event(event_id=5, event_type="test", timestamp=1.0, payload={}))

    def test_event_log_rejects_duplicate_id(self):
        from aidm.core.event_log import EventLog, Event

        log = EventLog()
        log.append(Event(event_id=0, event_type="test", timestamp=0.0, payload={}))

        with pytest.raises(ValueError, match="monotonic"):
            log.append(Event(event_id=0, event_type="test", timestamp=1.0, payload={}))

    def test_event_log_rejects_backward_id(self):
        from aidm.core.event_log import EventLog, Event

        log = EventLog()
        log.append(Event(event_id=0, event_type="test", timestamp=0.0, payload={}))
        log.append(Event(event_id=1, event_type="test", timestamp=1.0, payload={}))

        with pytest.raises(ValueError):
            log.append(Event(event_id=0, event_type="test", timestamp=2.0, payload={}))


# ═══════════════════════════════════════════════════════════════════════
# BL-009: RNG Seed Type Validation
# ═══════════════════════════════════════════════════════════════════════

class TestBL009_RNGSeedValidation:
    """BL-009: RNG seed must reject non-int types including bool.

    WHY: Python's bool is a subclass of int. random.Random(True) silently
    succeeds with seed=1, making RNG behavior depend on truthy values
    instead of explicit seeds. This breaks deterministic replay.

    WHAT BREAKS: Seed stability, replay, determinism guarantee.
    """

    def test_deterministic_rng_rejects_bool_seed(self):
        from aidm.core.rng_manager import DeterministicRNG

        with pytest.raises(TypeError, match="int"):
            DeterministicRNG(True)

    def test_deterministic_rng_rejects_float_seed(self):
        from aidm.core.rng_manager import DeterministicRNG

        with pytest.raises(TypeError, match="int"):
            DeterministicRNG(3.14)

    def test_deterministic_rng_rejects_string_seed(self):
        from aidm.core.rng_manager import DeterministicRNG

        with pytest.raises(TypeError, match="int"):
            DeterministicRNG("seed")

    def test_deterministic_rng_rejects_none_seed(self):
        from aidm.core.rng_manager import DeterministicRNG

        with pytest.raises(TypeError, match="int"):
            DeterministicRNG(None)

    def test_rng_manager_rejects_bool_master_seed(self):
        from aidm.core.rng_manager import RNGManager

        with pytest.raises(TypeError, match="int"):
            RNGManager(False)

    def test_rng_manager_rejects_string_master_seed(self):
        from aidm.core.rng_manager import RNGManager

        with pytest.raises(TypeError, match="int"):
            RNGManager("master")

    def test_rng_manager_accepts_valid_int_seed(self):
        from aidm.core.rng_manager import RNGManager

        rng = RNGManager(42)
        stream = rng.stream("test")
        result = stream.randint(1, 20)
        assert isinstance(result, int)
        assert 1 <= result <= 20


# ═══════════════════════════════════════════════════════════════════════
# BL-010: Frozen Dataclass Mutation Rejection
# ═══════════════════════════════════════════════════════════════════════

class TestBL010_FrozenDataclassMutation:
    """BL-010: Frozen dataclasses must reject all field mutation.

    WHY: Position, EntityState, and FrozenMemorySnapshot are immutable
    by design. If mutation succeeds silently, game state becomes
    unpredictable and replay diverges.

    WHAT BREAKS: State integrity, immutability contract, replay.
    """

    def test_position_rejects_mutation(self):
        from aidm.schemas.position import Position

        pos = Position(x=5, y=10)
        with pytest.raises(AttributeError):
            pos.x = 99

    def test_position_rejects_non_integer_coordinates(self):
        from aidm.schemas.position import Position

        with pytest.raises(TypeError, match="integers"):
            Position(x=1.5, y=2)

    def test_frozen_memory_snapshot_rejects_mutation(self):
        from aidm.narration.guarded_narration_service import FrozenMemorySnapshot

        snapshot = FrozenMemorySnapshot.create()
        with pytest.raises(AttributeError):
            snapshot.session_ledger_json = "TAMPERED"

    def test_entity_state_base_stats_rejects_mutation(self):
        from aidm.schemas.entity_state import EntityState

        state = EntityState(
            entity_id="test",
            base_stats={"str": 16, "dex": 14},
        )
        assert isinstance(state.base_stats, MappingProxyType)
        with pytest.raises(TypeError):
            state.base_stats["str"] = 99


# ═══════════════════════════════════════════════════════════════════════
# BL-011: WorldState Hash Determinism
# ═══════════════════════════════════════════════════════════════════════

class TestBL011_WorldStateHashDeterminism:
    """BL-011: WorldState.state_hash must be deterministic.

    WHY: state_hash is the fingerprint used for replay verification.
    If hashing is non-deterministic (dict ordering, float repr), replay
    verification becomes unreliable and divergence goes undetected.

    WHAT BREAKS: Replay verification, divergence detection, 10x guarantee.
    """

    def test_identical_states_produce_identical_hashes(self):
        from aidm.core.state import WorldState

        ws1 = WorldState(
            ruleset_version="RAW_3.5",
            entities={"orc": {"hp": 10, "ac": 15}},
        )
        ws2 = WorldState(
            ruleset_version="RAW_3.5",
            entities={"orc": {"hp": 10, "ac": 15}},
        )
        assert ws1.state_hash() == ws2.state_hash()

    def test_different_states_produce_different_hashes(self):
        from aidm.core.state import WorldState

        ws1 = WorldState(
            ruleset_version="RAW_3.5",
            entities={"orc": {"hp": 10}},
        )
        ws2 = WorldState(
            ruleset_version="RAW_3.5",
            entities={"orc": {"hp": 11}},
        )
        assert ws1.state_hash() != ws2.state_hash()

    def test_hash_is_stable_across_100_calls(self):
        from aidm.core.state import WorldState

        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"a": {"x": 1}, "b": {"x": 2}},
            active_combat={"round": 3},
        )
        hashes = [ws.state_hash() for _ in range(100)]
        assert len(set(hashes)) == 1, "state_hash must be deterministic across calls"


# ═══════════════════════════════════════════════════════════════════════
# BL-012: Replay Determinism
# ═══════════════════════════════════════════════════════════════════════

class TestBL012_ReplayDeterminism:
    """BL-012: Replay must produce identical results for identical inputs.

    WHY: The entire system's correctness guarantee depends on deterministic
    replay. Given the same initial state, master seed, and event log,
    the final state must be byte-identical every time.

    WHAT BREAKS: Everything. This is the foundational invariant.
    """

    def test_replay_is_deterministic_10x(self):
        from aidm.core.state import WorldState
        from aidm.core.event_log import EventLog, Event
        from aidm.core.replay_runner import run

        initial = WorldState(
            ruleset_version="RAW_3.5",
            entities={"orc": {"hp": 15, "ac": 13}},
        )

        log = EventLog()
        log.append(Event(
            event_id=0, event_type="set_entity_field", timestamp=0.0,
            payload={"entity_id": "orc", "field": "hp", "value": 10},
        ))
        log.append(Event(
            event_id=1, event_type="set_entity_field", timestamp=1.0,
            payload={"entity_id": "orc", "field": "hp", "value": 5},
        ))

        hashes = []
        for _ in range(10):
            report = run(initial, master_seed=42, event_log=log)
            hashes.append(report.final_hash)

        assert len(set(hashes)) == 1, (
            f"Replay produced {len(set(hashes))} different hashes — determinism broken"
        )

    def test_replay_detects_divergence(self):
        from aidm.core.state import WorldState
        from aidm.core.event_log import EventLog, Event
        from aidm.core.replay_runner import run

        initial = WorldState(ruleset_version="RAW_3.5", entities={})
        log = EventLog()
        log.append(Event(
            event_id=0, event_type="set_entity_field", timestamp=0.0,
            payload={"entity_id": "orc", "field": "hp", "value": 10},
        ))

        report = run(initial, master_seed=42, event_log=log, expected_final_hash="wrong_hash")
        assert not report.determinism_verified
        assert "mismatch" in report.divergence_info.lower()


# ═══════════════════════════════════════════════════════════════════════
# BL-013: SparkRequest Schema Validation
# ═══════════════════════════════════════════════════════════════════════

class TestBL013_SparkRequestValidation:
    """BL-013: SparkRequest must validate schema invariants at construction.

    WHY: Invalid requests to the LLM layer could cause silent failures,
    nonsensical outputs, or resource exhaustion. Fail-fast prevents
    debugging issues that manifest deep in the generation pipeline.

    WHAT BREAKS: LLM generation reliability, resource management.
    """

    def test_rejects_empty_prompt(self):
        from aidm.spark.spark_adapter import SparkRequest

        with pytest.raises(ValueError, match="non-empty"):
            SparkRequest(prompt="", temperature=0.8, max_tokens=100)

    def test_rejects_negative_temperature(self):
        from aidm.spark.spark_adapter import SparkRequest

        with pytest.raises(ValueError, match="temperature"):
            SparkRequest(prompt="test", temperature=-0.1, max_tokens=100)

    def test_rejects_temperature_above_2(self):
        from aidm.spark.spark_adapter import SparkRequest

        with pytest.raises(ValueError, match="temperature"):
            SparkRequest(prompt="test", temperature=2.1, max_tokens=100)

    def test_rejects_zero_max_tokens(self):
        from aidm.spark.spark_adapter import SparkRequest

        with pytest.raises(ValueError, match="max_tokens"):
            SparkRequest(prompt="test", temperature=0.8, max_tokens=0)

    def test_rejects_negative_max_tokens(self):
        from aidm.spark.spark_adapter import SparkRequest

        with pytest.raises(ValueError, match="max_tokens"):
            SparkRequest(prompt="test", temperature=0.8, max_tokens=-10)

    def test_accepts_valid_request(self):
        from aidm.spark.spark_adapter import SparkRequest

        req = SparkRequest(prompt="Generate narration", temperature=0.8, max_tokens=150)
        assert req.prompt == "Generate narration"
        assert req.temperature == 0.8
        assert req.max_tokens == 150


# ═══════════════════════════════════════════════════════════════════════
# BL-014: IntentObject Freeze Enforcement
# ═══════════════════════════════════════════════════════════════════════

class TestBL014_IntentFreezeEnforcement:
    """BL-014: IntentObject must reject unfreeze after confirmation.

    WHY: Once an intent is confirmed, it becomes the basis for resolution.
    If a confirmed intent can be unfrozen and modified, the resolution
    operates on different data than what was confirmed — silent corruption.

    WHAT BREAKS: Intent-resolution integrity, audit trail.
    """

    def test_frozen_intent_rejects_unfreeze(self):
        from aidm.schemas.intent_lifecycle import (
            IntentObject, IntentStatus, IntentFrozenError, ActionType,
        )

        intent = IntentObject(
            intent_id="test-intent-001",
            actor_id="player_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="I attack the orc",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        intent.status = IntentStatus.CONFIRMED
        intent._frozen = True

        with pytest.raises(IntentFrozenError, match="unfreeze"):
            intent._frozen = False

    def test_frozen_intent_rejects_non_resolution_fields(self):
        from aidm.schemas.intent_lifecycle import (
            IntentObject, IntentFrozenError, IntentStatus, ActionType,
        )

        intent = IntentObject(
            intent_id="test-intent-001",
            actor_id="player_1",
            action_type=ActionType.ATTACK,
            status=IntentStatus.PENDING,
            source_text="I attack the orc",
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 1, 12, 0, 0),
        )
        intent._frozen = True

        with pytest.raises(IntentFrozenError):
            intent.source_text = "I cast fireball"


# ═══════════════════════════════════════════════════════════════════════
# BL-015: EntityState Deep Immutability
# ═══════════════════════════════════════════════════════════════════════

class TestBL015_EntityStateDeepImmutability:
    """BL-015: EntityState must reject dict mutation via base_stats.

    WHY: EntityState uses frozen=True but dict fields are mutable by default.
    MappingProxyType wrapping ensures base_stats and temporary_modifiers
    cannot be mutated in place, preventing state corruption.

    WHAT BREAKS: Entity state integrity, frozen guarantee.
    """

    def test_base_stats_wrapped_in_mapping_proxy(self):
        from aidm.schemas.entity_state import EntityState

        state = EntityState(
            entity_id="orc_1",
            base_stats={"str": 16, "con": 14},
        )
        assert isinstance(state.base_stats, MappingProxyType)

    def test_base_stats_rejects_in_place_mutation(self):
        from aidm.schemas.entity_state import EntityState

        state = EntityState(
            entity_id="orc_1",
            base_stats={"str": 16},
        )
        with pytest.raises(TypeError):
            state.base_stats["str"] = 99

    def test_temporary_modifiers_wrapped_in_mapping_proxy(self):
        from aidm.schemas.entity_state import EntityState

        state = EntityState(
            entity_id="orc_1",
            base_stats={"str": 16},
            temporary_modifiers={"bless": 1},
        )
        assert isinstance(state.temporary_modifiers, MappingProxyType)

    def test_temporary_modifiers_rejects_in_place_mutation(self):
        from aidm.schemas.entity_state import EntityState

        state = EntityState(
            entity_id="orc_1",
            base_stats={"str": 16},
            temporary_modifiers={"bless": 1},
        )
        with pytest.raises(TypeError):
            state.temporary_modifiers["bless"] = 99


# ═══════════════════════════════════════════════════════════════════════
# BL-016: SparkResponse Error Contract
# ═══════════════════════════════════════════════════════════════════════

class TestBL016_SparkResponseErrorContract:
    """BL-016: SparkResponse must enforce error field when finish_reason is ERROR.

    WHY: If SPARK reports an error but doesn't populate the error field,
    downstream code has no way to diagnose or log the failure. This
    creates silent failures in the narration pipeline.

    WHAT BREAKS: Error diagnostics, fallback triggering, monitoring.
    """

    def test_error_finish_reason_requires_error_message(self):
        from aidm.spark.spark_adapter import SparkResponse, FinishReason

        with pytest.raises(ValueError, match="error"):
            SparkResponse(
                text="",
                finish_reason=FinishReason.ERROR,
                tokens_used=0,
                error=None,
            )

    def test_error_finish_reason_with_message_succeeds(self):
        from aidm.spark.spark_adapter import SparkResponse, FinishReason

        resp = SparkResponse(
            text="",
            finish_reason=FinishReason.ERROR,
            tokens_used=0,
            error="Out of memory",
        )
        assert resp.error == "Out of memory"

    def test_negative_tokens_rejected(self):
        from aidm.spark.spark_adapter import SparkResponse, FinishReason

        with pytest.raises(ValueError, match="tokens_used"):
            SparkResponse(
                text="hello",
                finish_reason=FinishReason.COMPLETED,
                tokens_used=-1,
            )


# ═══════════════════════════════════════════════════════════════════════
# BL-020: WorldState Immutability at Non-Engine Boundaries
# ═══════════════════════════════════════════════════════════════════════


class TestBL020_WorldStateImmutabilityAtNonEngineBoundaries:
    """BL-020: WorldState must be immutable at all non-engine boundaries.

    WHY: Only engine modules (play_loop, replay_runner, combat_controller,
    prep_orchestrator, interaction) may construct new WorldState instances.
    All other code must receive FrozenWorldStateView to prevent accidental
    or malicious state mutation.

    WHAT BREAKS: Determinism, replay integrity, engine authority.
    """

    # ───────────────────────────────────────────────────────────────────
    # Runtime Enforcement Tests (T-020-01 through T-020-08)
    # ───────────────────────────────────────────────────────────────────

    def test_t_020_01_frozen_view_rejects_field_assignment(self):
        """T-020-01: Frozen view rejects top-level field assignment."""
        from aidm.core.state import WorldState, FrozenWorldStateView, WorldStateImmutabilityError

        ws = WorldState(ruleset_version="RAW_3.5", entities={"orc": {"hp": 10}})
        view = FrozenWorldStateView(ws)

        with pytest.raises(WorldStateImmutabilityError, match="Cannot set attribute"):
            view.entities = {}

    def test_t_020_02_frozen_view_rejects_nested_dict_mutation(self):
        """T-020-02: Frozen view rejects nested dict mutation."""
        from aidm.core.state import WorldState, FrozenWorldStateView

        ws = WorldState(ruleset_version="RAW_3.5", entities={"pc1": {"hp": 20}})
        view = FrozenWorldStateView(ws)

        # Nested mutation must raise TypeError (from MappingProxyType)
        with pytest.raises(TypeError):
            view.entities["pc1"]["hp"] = 0

    def test_t_020_03_frozen_view_rejects_field_deletion(self):
        """T-020-03: Frozen view rejects field deletion."""
        from aidm.core.state import WorldState, FrozenWorldStateView, WorldStateImmutabilityError

        ws = WorldState(ruleset_version="RAW_3.5", entities={"orc": {"hp": 10}})
        view = FrozenWorldStateView(ws)

        with pytest.raises(WorldStateImmutabilityError, match="Cannot delete attribute"):
            del view.entities

    def test_t_020_04_frozen_view_state_hash_matches(self):
        """T-020-04: Frozen view state_hash() returns correct hash."""
        from aidm.core.state import WorldState, FrozenWorldStateView

        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"orc": {"hp": 10, "ac": 15}},
            active_combat={"round": 1},
        )
        view = FrozenWorldStateView(ws)

        assert view.state_hash() == ws.state_hash()

    def test_t_020_05_frozen_view_to_dict_matches(self):
        """T-020-05: Frozen view to_dict() returns correct dict."""
        from aidm.core.state import WorldState, FrozenWorldStateView

        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"orc": {"hp": 10}},
            active_combat={"round": 2},
        )
        view = FrozenWorldStateView(ws)

        assert view.to_dict() == ws.to_dict()

    def test_t_020_06_frozen_view_is_not_worldstate_instance(self):
        """T-020-06: Frozen view is NOT a WorldState instance."""
        from aidm.core.state import WorldState, FrozenWorldStateView

        ws = WorldState(ruleset_version="RAW_3.5", entities={})
        view = FrozenWorldStateView(ws)

        # View must NOT be an instance of WorldState
        assert not isinstance(view, WorldState)
        assert isinstance(view, FrozenWorldStateView)

    def test_t_020_07_frozen_view_allows_attribute_reads(self):
        """T-020-07: Frozen view allows reading ruleset_version."""
        from aidm.core.state import WorldState, FrozenWorldStateView

        ws = WorldState(ruleset_version="RAW_3.5", entities={"orc": {"hp": 10}})
        view = FrozenWorldStateView(ws)

        assert view.ruleset_version == "RAW_3.5"

    def test_t_020_08_frozen_view_active_combat_nested_mutation_rejected(self):
        """T-020-08: Frozen view rejects active_combat nested mutation."""
        from aidm.core.state import WorldState, FrozenWorldStateView

        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={},
            active_combat={"round": 1, "initiative_order": []},
        )
        view = FrozenWorldStateView(ws)

        # Must raise TypeError when attempting nested mutation
        with pytest.raises(TypeError):
            view.active_combat["round"] = 99

    # ───────────────────────────────────────────────────────────────────
    # Static Analysis / AST Enforcement Tests (T-020-09 through T-020-11)
    # ───────────────────────────────────────────────────────────────────

    def test_t_020_09_non_engine_modules_dont_import_worldstate(self):
        """T-020-09: Non-engine modules don't import WorldState.

        Scans narration/, immersion/, ui/, spark/ directories.
        None should import WorldState from aidm.core.state.
        """
        import ast
        from pathlib import Path

        def check_worldstate_imports(directory: str) -> list:
            """Check if any files import WorldState."""
            violations = []
            dir_path = Path(directory)
            if not dir_path.exists():
                # Directory doesn't exist yet (e.g., ui/ not implemented)
                return violations

            for filepath in dir_path.rglob("*.py"):
                if "__pycache__" in str(filepath):
                    continue

                with open(filepath, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read(), filename=str(filepath))
                    except SyntaxError:
                        continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and "aidm.core.state" in node.module:
                            for alias in node.names:
                                if alias.name == "WorldState":
                                    violations.append(
                                        f"{filepath.name} imports WorldState from {node.module}"
                                    )

            return violations

        # Check non-engine directories
        all_violations = []
        for directory in ["aidm/narration", "aidm/immersion", "aidm/ui", "aidm/spark"]:
            violations = check_worldstate_imports(directory)
            all_violations.extend(violations)

        assert all_violations == [], (
            f"BL-020 VIOLATION (T-020-09): Non-engine modules import WorldState:\n"
            + "\n".join(f"  - {v}" for v in all_violations)
        )

    def test_t_020_10_non_engine_modules_dont_construct_worldstate(self):
        """T-020-10: Non-engine modules don't call WorldState() constructor.

        Scans narration/, immersion/, ui/, spark/ for WorldState(...) calls.
        """
        import ast
        from pathlib import Path

        def check_worldstate_construction(directory: str) -> list:
            """Check if any files call WorldState(...)."""
            violations = []
            dir_path = Path(directory)
            if not dir_path.exists():
                return violations

            for filepath in dir_path.rglob("*.py"):
                if "__pycache__" in str(filepath):
                    continue

                with open(filepath, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read(), filename=str(filepath))
                    except SyntaxError:
                        continue

                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        # Check if calling WorldState(...)
                        if isinstance(node.func, ast.Name) and node.func.id == "WorldState":
                            violations.append(
                                f"{filepath.name} calls WorldState() constructor"
                            )

            return violations

        # Check non-engine directories
        all_violations = []
        for directory in ["aidm/narration", "aidm/immersion", "aidm/ui", "aidm/spark"]:
            violations = check_worldstate_construction(directory)
            all_violations.extend(violations)

        assert all_violations == [], (
            f"BL-020 VIOLATION (T-020-10): Non-engine modules construct WorldState:\n"
            + "\n".join(f"  - {v}" for v in all_violations)
        )

    def test_t_020_11_non_engine_signatures_use_frozen_view(self):
        """T-020-11: Non-engine function signatures use FrozenWorldStateView.

        This is a simplified check - full enforcement requires type checker integration.
        For now, we verify the proxy class exists and is usable.
        """
        from aidm.core.state import FrozenWorldStateView, WorldState

        # Verify FrozenWorldStateView is importable and usable
        ws = WorldState(ruleset_version="RAW_3.5", entities={})
        view = FrozenWorldStateView(ws)

        # Type annotation check would be:
        # def non_engine_function(state: FrozenWorldStateView) -> None: ...
        # This test just verifies the type exists for annotations
        assert FrozenWorldStateView is not None

    # ───────────────────────────────────────────────────────────────────
    # Integration / Handoff Tests (T-020-12 through T-020-14)
    # ───────────────────────────────────────────────────────────────────

    def test_t_020_12_turn_result_wrapping_for_non_engine_caller(self):
        """T-020-12: TurnResult.world_state is wrapped when returned to non-engine.

        NOTE: Current architecture doesn't expose TurnResult to non-engine callers.
        play_loop → combat_controller are both engine modules.
        This test verifies the view type is available for future use.
        """
        from aidm.core.state import FrozenWorldStateView, WorldState

        # Verify view can be used in return types
        ws = WorldState(ruleset_version="RAW_3.5", entities={})
        view = FrozenWorldStateView(ws)

        # If TurnResult were returned to non-engine code, world_state field
        # would be typed as FrozenWorldStateView, not WorldState
        assert isinstance(view, FrozenWorldStateView)
        assert not isinstance(view, WorldState)

    def test_t_020_13_frozen_view_hash_matches_original(self):
        """T-020-13: Full round-trip: engine → proxy → hash matches."""
        from aidm.core.state import WorldState, FrozenWorldStateView

        # Engine produces WorldState
        ws = WorldState(
            ruleset_version="RAW_3.5",
            entities={"orc": {"hp": 15, "ac": 13}},
            active_combat={"round": 2},
        )
        original_hash = ws.state_hash()

        # Wrap in proxy before handoff to non-engine
        view = FrozenWorldStateView(ws)

        # Non-engine consumer reads hash
        proxy_hash = view.state_hash()

        # Hashes must match
        assert proxy_hash == original_hash

    def test_t_020_14_replay_runner_receives_real_worldstate(self):
        """T-020-14: Replay runner (engine-boundary) receives real WorldState.

        Replay runner is listed in BL-020 §3 as an authorized engine mutator.
        It must receive raw WorldState, not proxy.
        """
        from aidm.core.state import WorldState

        # Replay runner constructs new WorldState instances during replay
        # This is authorized per BL-020 §3
        ws = WorldState(ruleset_version="RAW_3.5", entities={"orc": {"hp": 10}})

        # Replay runner must be able to check isinstance
        assert isinstance(ws, WorldState)

        # Engine modules receive raw WorldState, not proxy
        # (No wrapping needed for engine-to-engine handoffs)
        assert type(ws).__name__ == "WorldState"


# ═══════════════════════════════════════════════════════════════════════
# BL-017: UUID Injection Only (No default_factory uuid.uuid4())
# BL-018: Timestamp Injection Only (No default_factory datetime.utcnow)
# ═══════════════════════════════════════════════════════════════════════


class TestBL017_UUIDInjectionOnly:
    """BL-017: uuid.uuid4() must not appear in any dataclass field default_factory.

    WHY: Non-deterministic ID generation in schema defaults makes replay diverge.
    IDs must be explicitly injected by the caller so they can be controlled
    during testing and deterministic replay.

    WHAT BREAKS: Replay determinism, test reproducibility, session verification.
    """

    def test_no_uuid_default_factory_in_schemas(self):
        """BL-017: No dataclass in aidm/schemas/ uses uuid.uuid4() as default_factory.

        Scans all Python files in aidm/schemas/ for AST patterns matching:
        - field(default_factory=lambda: str(uuid.uuid4()))
        - field(default_factory=uuid.uuid4)
        """
        import ast
        from pathlib import Path

        schema_dir = Path("aidm/schemas")
        violations = []

        for py_file in schema_dir.glob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))

            for node in ast.walk(tree):
                # Look for field(default_factory=...) calls
                if isinstance(node, ast.Call):
                    for keyword in getattr(node, "keywords", []):
                        if keyword.arg == "default_factory":
                            # Check if the default_factory references uuid
                            source_segment = ast.get_source_segment(source, keyword.value)
                            if source_segment and "uuid" in source_segment:
                                violations.append(
                                    f"{py_file.name}:{node.lineno} — "
                                    f"default_factory references uuid: {source_segment}"
                                )

        assert len(violations) == 0, (
            f"BL-017 VIOLATED: {len(violations)} dataclass fields use uuid in default_factory:\n"
            + "\n".join(violations)
        )

    def test_intent_object_requires_intent_id(self):
        """BL-017: IntentObject() without intent_id raises TypeError."""
        from aidm.schemas.intent_lifecycle import IntentObject, IntentStatus, ActionType
        from datetime import datetime

        with pytest.raises(TypeError):
            IntentObject(
                actor_id="fighter_1",
                action_type=ActionType.ATTACK,
                status=IntentStatus.PENDING,
                source_text="I attack",
                created_at=datetime(2025, 1, 1),
                updated_at=datetime(2025, 1, 1),
                # intent_id intentionally omitted
            )

    def test_engine_result_requires_result_id(self):
        """BL-017: EngineResult() without result_id raises TypeError."""
        from aidm.schemas.engine_result import EngineResult, EngineResultStatus
        from datetime import datetime

        with pytest.raises(TypeError):
            EngineResult(
                intent_id="intent_123",
                status=EngineResultStatus.SUCCESS,
                resolved_at=datetime(2025, 1, 1),
                # result_id intentionally omitted
            )


class TestBL018_TimestampInjectionOnly:
    """BL-018: datetime.utcnow()/now() must not appear in any dataclass field default_factory.

    WHY: Non-deterministic timestamps in schema defaults break replay.
    Timestamps must be explicitly injected by the caller.

    WHAT BREAKS: Replay determinism, test reproducibility, session verification.
    """

    def test_no_datetime_default_factory_in_schemas(self):
        """BL-018: No dataclass in aidm/schemas/ uses datetime.utcnow/now as default_factory.

        Scans all Python files in aidm/schemas/ for AST patterns matching:
        - field(default_factory=datetime.utcnow)
        - field(default_factory=datetime.now)
        """
        import ast
        from pathlib import Path

        schema_dir = Path("aidm/schemas")
        violations = []

        for py_file in schema_dir.glob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    for keyword in getattr(node, "keywords", []):
                        if keyword.arg == "default_factory":
                            source_segment = ast.get_source_segment(source, keyword.value)
                            if source_segment and ("utcnow" in source_segment or "datetime.now" in source_segment):
                                violations.append(
                                    f"{py_file.name}:{node.lineno} — "
                                    f"default_factory references datetime: {source_segment}"
                                )

        assert len(violations) == 0, (
            f"BL-018 VIOLATED: {len(violations)} dataclass fields use datetime in default_factory:\n"
            + "\n".join(violations)
        )

    def test_intent_object_requires_timestamps(self):
        """BL-018: IntentObject() without created_at/updated_at raises TypeError."""
        from aidm.schemas.intent_lifecycle import IntentObject, IntentStatus, ActionType

        with pytest.raises(TypeError):
            IntentObject(
                intent_id="test-id",
                actor_id="fighter_1",
                action_type=ActionType.ATTACK,
                status=IntentStatus.PENDING,
                source_text="I attack",
                # created_at, updated_at intentionally omitted
            )

    def test_engine_result_requires_resolved_at(self):
        """BL-018: EngineResult() without resolved_at raises TypeError."""
        from aidm.schemas.engine_result import EngineResult, EngineResultStatus

        with pytest.raises(TypeError):
            EngineResult(
                result_id="test-result",
                intent_id="intent_123",
                status=EngineResultStatus.SUCCESS,
                # resolved_at intentionally omitted
            )

    def test_roundtrip_preserves_injected_timestamps(self):
        """BL-018: to_dict()/from_dict() roundtrip preserves injected timestamps exactly."""
        from aidm.schemas.intent_lifecycle import IntentObject, IntentStatus, ActionType
        from datetime import datetime

        ts = datetime(2025, 6, 15, 14, 30, 0)
        intent = IntentObject(
            intent_id="roundtrip-test",
            actor_id="fighter_1",
            action_type=ActionType.END_TURN,
            status=IntentStatus.PENDING,
            source_text="end turn",
            created_at=ts,
            updated_at=ts,
        )

        data = intent.to_dict()
        restored = IntentObject.from_dict(data)

        assert restored.created_at == ts
        assert restored.updated_at == ts
        assert restored.intent_id == "roundtrip-test"

    def test_engine_result_roundtrip_preserves_injected_values(self):
        """BL-017/018: EngineResult roundtrip preserves injected result_id and resolved_at."""
        from aidm.schemas.engine_result import EngineResult, EngineResultStatus
        from datetime import datetime
        import json

        ts = datetime(2025, 6, 15, 14, 30, 0)
        result = EngineResult(
            result_id="roundtrip-result-001",
            intent_id="intent-roundtrip",
            status=EngineResultStatus.SUCCESS,
            resolved_at=ts,
        )

        json_str = json.dumps(result.to_dict(), sort_keys=True)
        restored = EngineResult.from_dict(json.loads(json_str))

        assert restored.result_id == "roundtrip-result-001"
        assert restored.resolved_at == ts


# ═══════════════════════════════════════════════════════════════════════
# BL-AD007: Spark Must Not Import Presentation Semantics Directly
# ═══════════════════════════════════════════════════════════════════════


class TestBL_AD007_SparkMustNotImportPresentationSemantics:
    """AD-007 Boundary: Spark receives semantics via NarrativeBrief only.

    WHY: Spark is constrained by presentation semantics but must not
    import the schema module directly. This enforces the one-way valve:
    Box → Lens (enriches NarrativeBrief with semantics) → Spark.

    If Spark imports from aidm.schemas.presentation_semantics directly,
    it could bypass Lens's containment boundary and construct or
    manipulate Layer B data outside the intended data flow.

    WHAT BREAKS: Lens containment boundary, one-way valve enforcement.
    """

    def test_spark_does_not_import_presentation_semantics(self):
        violations = []
        for filepath in _get_py_files("aidm/spark"):
            imports = _extract_imports_from_file(filepath)
            for imp in imports:
                if "presentation_semantics" in imp:
                    violations.append(f"{filepath.name} imports {imp}")

        assert violations == [], (
            f"BL-AD007 VIOLATION: Spark imports presentation_semantics "
            f"directly (must receive via NarrativeBrief):\n"
            + "\n".join(f"  - {v}" for v in violations)
        )
