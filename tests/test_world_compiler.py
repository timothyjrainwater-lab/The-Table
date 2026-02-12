"""Tests for World Compiler pipeline harness.

Covers: input validation, seed derivation, dependency ordering,
Stage 0 (validate), Stage 8 (finalize), full compile flow,
and serialization round-trips.

Reference: docs/contracts/WORLD_COMPILER.md
WO: WO-WORLDCOMPILE-SCAFFOLD-001
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from aidm.core.world_compiler import (
    CompileContext,
    CompileStage,
    ContentPackStub,
    WorldCompiler,
    _run_stage_0,
    _run_stage_8,
    _topological_sort,
    compute_world_id,
    derive_seeds,
)
from aidm.schemas.world_compile import (
    CompileConfig,
    CompileInputs,
    CompileReport,
    StageResult,
    ToolchainPins,
    WorldThemeBrief,
)


# ═══════════════════════════════════════════════════════════════════════
# Test fixtures
# ═══════════════════════════════════════════════════════════════════════


def _make_theme(**overrides):
    """Create a valid WorldThemeBrief with optional overrides."""
    defaults = {
        "genre": "dark_fantasy",
        "tone": "grim",
        "naming_style": "anglo_saxon",
    }
    defaults.update(overrides)
    return WorldThemeBrief(**defaults)


def _make_pins(**overrides):
    """Create valid ToolchainPins with optional overrides."""
    defaults = {
        "llm_model_id": "qwen3-8b-q4",
    }
    defaults.update(overrides)
    return ToolchainPins(**defaults)


def _make_config(tmp_path, **overrides):
    """Create a valid CompileConfig pointing to tmp_path."""
    defaults = {
        "output_dir": str(tmp_path),
    }
    defaults.update(overrides)
    return CompileConfig(**defaults)


def _make_inputs(tmp_path, **overrides):
    """Create valid CompileInputs with optional overrides."""
    defaults = {
        "content_pack_id": "test_pack_001",
        "world_theme_brief": _make_theme(),
        "world_seed": 42,
        "compile_config": _make_config(tmp_path),
        "toolchain_pins": _make_pins(),
    }
    defaults.update(overrides)
    return CompileInputs(**defaults)


def _make_content_pack(pack_id="test_pack_001"):
    """Create a minimal content pack stub."""
    return ContentPackStub(
        pack_id=pack_id,
        entries=(),
        content_hash="abc123def456",
    )


class StubStage(CompileStage):
    """Test helper: configurable stub stage.

    Can be set to succeed or fail, and records whether execute() was called.
    """

    def __init__(
        self,
        stage_id: str,
        stage_number: int,
        depends_on: tuple = (),
        should_fail: bool = False,
        output_files: tuple = (),
    ):
        self._stage_id = stage_id
        self._stage_number = stage_number
        self._depends_on = depends_on
        self._should_fail = should_fail
        self._output_files = output_files
        self.executed = False

    @property
    def stage_id(self) -> str:
        return self._stage_id

    @property
    def stage_number(self) -> int:
        return self._stage_number

    @property
    def depends_on(self) -> tuple:
        return self._depends_on

    def execute(self, context: CompileContext) -> StageResult:
        self.executed = True
        if self._should_fail:
            return StageResult(
                stage_id=self._stage_id,
                status="failed",
                output_files=(),
                error=f"Stage {self._stage_id} failed (test)",
            )
        # Write a stub file for hash tests
        for fname in self._output_files:
            fpath = context.workspace / fname
            fpath.parent.mkdir(parents=True, exist_ok=True)
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump({"stage": self._stage_id, "file": fname}, f)
        context.stage_outputs[self._stage_id] = {"status": "done"}
        return StageResult(
            stage_id=self._stage_id,
            status="success",
            output_files=self._output_files,
        )


# ═══════════════════════════════════════════════════════════════════════
# Test 1: CompileInputs validation rejects missing genre/tone/naming_style
# ═══════════════════════════════════════════════════════════════════════


class TestInputValidation:
    """Tests for CompileInputs validation (§1.3)."""

    def test_rejects_missing_genre(self, tmp_path):
        theme = WorldThemeBrief(genre="", tone="grim", naming_style="anglo_saxon")
        inputs = _make_inputs(tmp_path, world_theme_brief=theme)
        errors = inputs.validate()
        assert any("IV-002" in e for e in errors)

    def test_rejects_missing_tone(self, tmp_path):
        theme = WorldThemeBrief(genre="dark_fantasy", tone="", naming_style="anglo_saxon")
        inputs = _make_inputs(tmp_path, world_theme_brief=theme)
        errors = inputs.validate()
        assert any("IV-002" in e for e in errors)

    def test_rejects_missing_naming_style(self, tmp_path):
        theme = WorldThemeBrief(genre="dark_fantasy", tone="grim", naming_style="")
        inputs = _make_inputs(tmp_path, world_theme_brief=theme)
        errors = inputs.validate()
        assert any("IV-002" in e for e in errors)

    def test_accepts_valid_theme(self, tmp_path):
        inputs = _make_inputs(tmp_path)
        errors = inputs.validate()
        assert errors == []


# ═══════════════════════════════════════════════════════════════════════
# Test 2: CompileInputs validation rejects negative world_seed
# ═══════════════════════════════════════════════════════════════════════


class TestSeedValidation:
    """Tests for world_seed validation (§1.3 IV-003)."""

    def test_rejects_negative_seed(self, tmp_path):
        inputs = _make_inputs(tmp_path, world_seed=-1)
        errors = inputs.validate()
        assert any("IV-003" in e for e in errors)

    def test_rejects_oversized_seed(self, tmp_path):
        inputs = _make_inputs(tmp_path, world_seed=2**63)
        errors = inputs.validate()
        assert any("IV-003" in e for e in errors)

    def test_accepts_zero_seed(self, tmp_path):
        inputs = _make_inputs(tmp_path, world_seed=0)
        errors = inputs.validate()
        assert errors == []

    def test_accepts_max_valid_seed(self, tmp_path):
        inputs = _make_inputs(tmp_path, world_seed=(2**63) - 1)
        errors = inputs.validate()
        assert errors == []


# ═══════════════════════════════════════════════════════════════════════
# Test 3: CompileInputs validation rejects "latest" in toolchain_pins
# ═══════════════════════════════════════════════════════════════════════


class TestToolchainPinsValidation:
    """Tests for toolchain_pins validation (§1.3 IV-004, IV-005)."""

    def test_rejects_latest_in_llm_model(self, tmp_path):
        pins = ToolchainPins(llm_model_id="latest")
        inputs = _make_inputs(tmp_path, toolchain_pins=pins)
        errors = inputs.validate()
        assert any("IV-005" in e for e in errors)

    def test_rejects_latest_in_image_model(self, tmp_path):
        pins = ToolchainPins(llm_model_id="qwen3-8b", image_model_id="sd-latest")
        inputs = _make_inputs(tmp_path, toolchain_pins=pins)
        errors = inputs.validate()
        assert any("IV-005" in e for e in errors)

    def test_rejects_empty_llm_model(self, tmp_path):
        pins = ToolchainPins(llm_model_id="")
        inputs = _make_inputs(tmp_path, toolchain_pins=pins)
        errors = inputs.validate()
        assert any("IV-004" in e for e in errors)

    def test_accepts_valid_pins(self, tmp_path):
        pins = _make_pins()
        errors = pins.validate()
        assert errors == []


# ═══════════════════════════════════════════════════════════════════════
# Test 4: Seed derivation is deterministic
# ═══════════════════════════════════════════════════════════════════════


class TestSeedDerivation:
    """Tests for deterministic seed derivation (§4.1)."""

    def test_same_seed_produces_same_derived_seeds(self):
        seeds_a = derive_seeds(42)
        seeds_b = derive_seeds(42)
        assert seeds_a == seeds_b

    def test_different_seeds_produce_different_derived_seeds(self):
        seeds_a = derive_seeds(42)
        seeds_b = derive_seeds(99)
        # At least the stage seeds should differ
        assert seeds_a["lexicon_seed"] != seeds_b["lexicon_seed"]

    def test_derived_seeds_include_world_seed(self):
        seeds = derive_seeds(42)
        assert seeds["world_seed"] == 42

    def test_derived_seeds_include_all_stages(self):
        seeds = derive_seeds(42)
        expected_keys = {
            "world_seed",
            "lexicon_seed",
            "map_seed",
            "bestiary_seed",
            "asset_seed",
            "doctrine_seed",
            "rulebook_seed",
            "semantics_seed",
            "npc_seed",
        }
        assert set(seeds.keys()) == expected_keys

    def test_derived_seeds_are_non_negative(self):
        seeds = derive_seeds(0)
        for key, value in seeds.items():
            assert value >= 0, f"{key} is negative: {value}"

    def test_derived_seeds_fit_63_bits(self):
        seeds = derive_seeds(999999)
        max_val = (2**63) - 1
        for key, value in seeds.items():
            assert value <= max_val, f"{key} exceeds 63 bits: {value}"


# ═══════════════════════════════════════════════════════════════════════
# Test 5: Stage dependency ordering (topological sort)
# ═══════════════════════════════════════════════════════════════════════


class TestTopologicalSort:
    """Tests for stage dependency ordering."""

    def test_no_dependencies(self):
        stages = {
            "a": StubStage("a", 1),
            "b": StubStage("b", 2),
            "c": StubStage("c", 3),
        }
        order = _topological_sort(stages)
        assert order == ["a", "b", "c"]

    def test_linear_chain(self):
        stages = {
            "c": StubStage("c", 3, depends_on=("b",)),
            "b": StubStage("b", 2, depends_on=("a",)),
            "a": StubStage("a", 1),
        }
        order = _topological_sort(stages)
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_diamond_dependency(self):
        stages = {
            "d": StubStage("d", 4, depends_on=("b", "c")),
            "b": StubStage("b", 2, depends_on=("a",)),
            "c": StubStage("c", 3, depends_on=("a",)),
            "a": StubStage("a", 1),
        }
        order = _topological_sort(stages)
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_cycle_raises_error(self):
        stages = {
            "a": StubStage("a", 1, depends_on=("b",)),
            "b": StubStage("b", 2, depends_on=("a",)),
        }
        with pytest.raises(ValueError, match="cycle"):
            _topological_sort(stages)

    def test_contract_dependency_graph(self):
        """Test the actual dependency graph from the contract (§2.9)."""
        stages = {
            "lexicon": StubStage("lexicon", 1),
            "semantics": StubStage("semantics", 3),
            "rulebook": StubStage("rulebook", 2, depends_on=("lexicon", "semantics")),
            "npc": StubStage("npc", 4),
            "bestiary": StubStage("bestiary", 5, depends_on=("lexicon", "semantics")),
            "maps": StubStage("maps", 6),
            "asset_pools": StubStage("asset_pools", 7),
        }
        order = _topological_sort(stages)
        # Lexicon and semantics must come before rulebook and bestiary
        assert order.index("lexicon") < order.index("rulebook")
        assert order.index("semantics") < order.index("rulebook")
        assert order.index("lexicon") < order.index("bestiary")
        assert order.index("semantics") < order.index("bestiary")


# ═══════════════════════════════════════════════════════════════════════
# Test 6: Stage 0 creates workspace + writes compile_inputs.json
# ═══════════════════════════════════════════════════════════════════════


class TestStage0:
    """Tests for Stage 0 (validate inputs)."""

    def test_creates_workspace(self, tmp_path):
        workspace = tmp_path / "compile_output"
        inputs = _make_inputs(tmp_path, compile_config=CompileConfig(output_dir=str(workspace)))
        context = CompileContext(
            inputs=inputs,
            content_pack=_make_content_pack(),
            workspace=workspace,
            derived_seeds={},
        )
        result = _run_stage_0(context)
        assert result.status == "success"
        assert workspace.exists()

    def test_writes_compile_inputs_json(self, tmp_path):
        workspace = tmp_path / "compile_output"
        inputs = _make_inputs(tmp_path, compile_config=CompileConfig(output_dir=str(workspace)))
        context = CompileContext(
            inputs=inputs,
            content_pack=_make_content_pack(),
            workspace=workspace,
            derived_seeds={},
        )
        result = _run_stage_0(context)
        assert result.status == "success"
        assert "compile_inputs.json" in result.output_files

        inputs_path = workspace / "compile_inputs.json"
        assert inputs_path.exists()
        with open(inputs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["content_pack_id"] == "test_pack_001"
        assert data["world_seed"] == 42

    def test_populates_derived_seeds(self, tmp_path):
        workspace = tmp_path / "compile_output"
        inputs = _make_inputs(tmp_path, compile_config=CompileConfig(output_dir=str(workspace)))
        context = CompileContext(
            inputs=inputs,
            content_pack=_make_content_pack(),
            workspace=workspace,
            derived_seeds={},
        )
        _run_stage_0(context)
        assert "world_seed" in context.derived_seeds
        assert "lexicon_seed" in context.derived_seeds
        assert context.derived_seeds["world_seed"] == 42

    def test_fails_on_invalid_inputs(self, tmp_path):
        workspace = tmp_path / "compile_output"
        theme = WorldThemeBrief(genre="", tone="", naming_style="")
        inputs = _make_inputs(
            tmp_path,
            world_theme_brief=theme,
            compile_config=CompileConfig(output_dir=str(workspace)),
        )
        context = CompileContext(
            inputs=inputs,
            content_pack=_make_content_pack(),
            workspace=workspace,
            derived_seeds={},
        )
        result = _run_stage_0(context)
        assert result.status == "failed"
        assert "IV-002" in result.error

    def test_fails_on_empty_content_pack_id(self, tmp_path):
        workspace = tmp_path / "compile_output"
        inputs = _make_inputs(
            tmp_path,
            content_pack_id="",
            compile_config=CompileConfig(output_dir=str(workspace)),
        )
        context = CompileContext(
            inputs=inputs,
            content_pack=_make_content_pack(pack_id=""),
            workspace=workspace,
            derived_seeds={},
        )
        result = _run_stage_0(context)
        assert result.status == "failed"


# ═══════════════════════════════════════════════════════════════════════
# Test 7: Stage 8 computes correct file hashes
# ═══════════════════════════════════════════════════════════════════════


class TestStage8Hashes:
    """Tests for Stage 8 file hash computation."""

    def test_computes_file_hashes(self, tmp_path):
        workspace = tmp_path / "bundle"
        workspace.mkdir()
        # Write test files
        (workspace / "file_a.json").write_text('{"a":1}', encoding="utf-8")
        (workspace / "file_b.json").write_text('{"b":2}', encoding="utf-8")

        inputs = _make_inputs(tmp_path)
        context = CompileContext(
            inputs=inputs,
            content_pack=_make_content_pack(),
            workspace=workspace,
            derived_seeds=derive_seeds(42),
        )
        result = _run_stage_8(context, [])
        assert result.status == "success"

        hashes_path = workspace / "bundle_hashes.json"
        assert hashes_path.exists()
        with open(hashes_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "root_hash" in data
        assert "file_a.json" in data["files"]
        assert "file_b.json" in data["files"]
        assert len(data["root_hash"]) == 64  # SHA-256 hex

    def test_root_hash_is_deterministic(self, tmp_path):
        """Same files → same root_hash."""
        hashes = []
        for i in range(2):
            workspace = tmp_path / f"bundle_{i}"
            workspace.mkdir()
            (workspace / "data.json").write_text('{"x":1}', encoding="utf-8")

            inputs = _make_inputs(tmp_path)
            context = CompileContext(
                inputs=inputs,
                content_pack=_make_content_pack(),
                workspace=workspace,
                derived_seeds=derive_seeds(42),
            )
            _run_stage_8(context, [])
            with open(workspace / "bundle_hashes.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            hashes.append(data["root_hash"])
        assert hashes[0] == hashes[1]


# ═══════════════════════════════════════════════════════════════════════
# Test 8: Stage 8 writes valid world_manifest.json
# ═══════════════════════════════════════════════════════════════════════


class TestStage8Manifest:
    """Tests for Stage 8 world_manifest.json output."""

    def test_writes_world_manifest(self, tmp_path):
        workspace = tmp_path / "bundle"
        workspace.mkdir()
        (workspace / "compile_inputs.json").write_text("{}", encoding="utf-8")

        inputs = _make_inputs(tmp_path)
        context = CompileContext(
            inputs=inputs,
            content_pack=_make_content_pack(),
            workspace=workspace,
            derived_seeds=derive_seeds(42),
        )
        _run_stage_8(context, [])

        manifest_path = workspace / "world_manifest.json"
        assert manifest_path.exists()
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert "world_id" in manifest
        assert len(manifest["world_id"]) == 32
        assert "root_hash" in manifest
        assert "compile_timestamp" in manifest
        assert "toolchain_pins" in manifest
        assert "seeds" in manifest
        assert manifest["content_pack_id"] == "test_pack_001"
        assert manifest["schema_version"] == "1.0.0"
        assert manifest["world_theme_brief"]["genre"] == "dark_fantasy"

    def test_world_id_is_deterministic(self, tmp_path):
        """Same inputs → same world_id."""
        id_a = compute_world_id(42, "pack_001", _make_pins())
        id_b = compute_world_id(42, "pack_001", _make_pins())
        assert id_a == id_b
        assert len(id_a) == 32

    def test_world_id_changes_with_seed(self, tmp_path):
        id_a = compute_world_id(42, "pack_001", _make_pins())
        id_b = compute_world_id(99, "pack_001", _make_pins())
        assert id_a != id_b

    def test_world_id_changes_with_pack(self, tmp_path):
        id_a = compute_world_id(42, "pack_001", _make_pins())
        id_b = compute_world_id(42, "pack_002", _make_pins())
        assert id_a != id_b


# ═══════════════════════════════════════════════════════════════════════
# Test 9: Full compile with stub stages produces valid bundle
# ═══════════════════════════════════════════════════════════════════════


class TestFullCompile:
    """Tests for full compilation flow."""

    def test_zero_stages_produces_valid_bundle(self, tmp_path):
        """Compiler works with zero registered stages."""
        workspace = tmp_path / "bundle"
        inputs = _make_inputs(tmp_path, compile_config=CompileConfig(output_dir=str(workspace)))
        compiler = WorldCompiler(inputs, _make_content_pack())
        report = compiler.compile(workspace=workspace)

        assert report.status == "success"
        assert len(report.world_id) == 32
        assert len(report.root_hash) == 64
        assert (workspace / "compile_inputs.json").exists()
        assert (workspace / "bundle_hashes.json").exists()
        assert (workspace / "world_manifest.json").exists()
        assert (workspace / "compile_report.json").exists()

    def test_stub_stages_execute_in_order(self, tmp_path):
        workspace = tmp_path / "bundle"
        inputs = _make_inputs(tmp_path, compile_config=CompileConfig(output_dir=str(workspace)))

        stage_a = StubStage("lexicon", 1, output_files=("lexicon.json",))
        stage_b = StubStage("rulebook", 2, depends_on=("lexicon",), output_files=("rulebook.json",))

        compiler = WorldCompiler(inputs, _make_content_pack())
        compiler.register_stage(stage_a)
        compiler.register_stage(stage_b)
        report = compiler.compile(workspace=workspace)

        assert report.status == "success"
        assert stage_a.executed
        assert stage_b.executed
        # Verify stage output files exist
        assert (workspace / "lexicon.json").exists()
        assert (workspace / "rulebook.json").exists()

    def test_compile_report_json_written(self, tmp_path):
        workspace = tmp_path / "bundle"
        inputs = _make_inputs(tmp_path, compile_config=CompileConfig(output_dir=str(workspace)))
        compiler = WorldCompiler(inputs, _make_content_pack())
        compiler.compile(workspace=workspace)

        report_path = workspace / "compile_report.json"
        assert report_path.exists()
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["status"] == "success"
        assert "stage_results" in data
        assert "total_elapsed_ms" in data


# ═══════════════════════════════════════════════════════════════════════
# Test 10: Failed stage halts downstream dependents
# ═══════════════════════════════════════════════════════════════════════


class TestFailureHandling:
    """Tests for fail-closed behavior."""

    def test_failed_stage_halts_dependents(self, tmp_path):
        workspace = tmp_path / "bundle"
        inputs = _make_inputs(tmp_path, compile_config=CompileConfig(output_dir=str(workspace)))

        stage_a = StubStage("lexicon", 1, should_fail=True)
        stage_b = StubStage("rulebook", 2, depends_on=("lexicon",))

        compiler = WorldCompiler(inputs, _make_content_pack())
        compiler.register_stage(stage_a)
        compiler.register_stage(stage_b)
        report = compiler.compile(workspace=workspace)

        assert stage_a.executed
        assert not stage_b.executed  # Skipped due to dependency failure
        # Find the skipped result
        skipped = [r for r in report.stage_results if r.stage_id == "rulebook"]
        assert len(skipped) == 1
        assert skipped[0].status == "skipped"

    def test_failed_validation_halts_all(self, tmp_path):
        workspace = tmp_path / "bundle"
        theme = WorldThemeBrief(genre="", tone="", naming_style="")
        inputs = _make_inputs(
            tmp_path,
            world_theme_brief=theme,
            compile_config=CompileConfig(output_dir=str(workspace)),
        )
        compiler = WorldCompiler(inputs, _make_content_pack())
        report = compiler.compile(workspace=workspace)

        assert report.status == "failed"
        assert "IV-002" in report.error

    def test_independent_stages_unaffected_by_sibling_failure(self, tmp_path):
        workspace = tmp_path / "bundle"
        inputs = _make_inputs(tmp_path, compile_config=CompileConfig(output_dir=str(workspace)))

        stage_a = StubStage("lexicon", 1, should_fail=True)
        stage_b = StubStage("maps", 6)  # No dependency on lexicon

        compiler = WorldCompiler(inputs, _make_content_pack())
        compiler.register_stage(stage_a)
        compiler.register_stage(stage_b)
        report = compiler.compile(workspace=workspace)

        assert stage_a.executed
        assert stage_b.executed  # Independent, should still run

    def test_stage_exception_caught(self, tmp_path):
        """Stage that raises an exception is handled gracefully."""
        workspace = tmp_path / "bundle"
        inputs = _make_inputs(tmp_path, compile_config=CompileConfig(output_dir=str(workspace)))

        class ExplodingStage(CompileStage):
            @property
            def stage_id(self): return "exploding"
            @property
            def stage_number(self): return 1
            @property
            def depends_on(self): return ()
            def execute(self, context):
                raise RuntimeError("Boom!")

        compiler = WorldCompiler(inputs, _make_content_pack())
        compiler.register_stage(ExplodingStage())
        report = compiler.compile(workspace=workspace)

        failed = [r for r in report.stage_results if r.stage_id == "exploding"]
        assert len(failed) == 1
        assert failed[0].status == "failed"
        assert "Boom!" in failed[0].error


# ═══════════════════════════════════════════════════════════════════════
# Test 11: CompileReport round-trip serialization
# ═══════════════════════════════════════════════════════════════════════


class TestSerialization:
    """Tests for to_dict() / from_dict() round-trip."""

    def test_stage_result_round_trip(self):
        original = StageResult(
            stage_id="lexicon",
            status="success",
            output_files=("lexicon.json",),
            warnings=("Low variety",),
            elapsed_ms=1234,
        )
        data = original.to_dict()
        restored = StageResult.from_dict(data)
        assert restored.stage_id == original.stage_id
        assert restored.status == original.status
        assert restored.output_files == original.output_files
        assert restored.warnings == original.warnings
        assert restored.elapsed_ms == original.elapsed_ms

    def test_compile_report_round_trip(self):
        results = (
            StageResult(stage_id="validate", status="success", output_files=("compile_inputs.json",)),
            StageResult(stage_id="finalize", status="success", output_files=("world_manifest.json",)),
        )
        original = CompileReport(
            status="success",
            world_id="abcdef1234567890abcdef1234567890",
            root_hash="a" * 64,
            stage_results=results,
            total_elapsed_ms=5000,
            warnings=("Minor warning",),
        )
        data = original.to_dict()
        json_str = json.dumps(data, sort_keys=True)
        restored_data = json.loads(json_str)
        restored = CompileReport.from_dict(restored_data)

        assert restored.status == original.status
        assert restored.world_id == original.world_id
        assert restored.root_hash == original.root_hash
        assert len(restored.stage_results) == len(original.stage_results)
        assert restored.total_elapsed_ms == original.total_elapsed_ms
        assert restored.warnings == original.warnings

    def test_compile_inputs_round_trip(self, tmp_path):
        original = _make_inputs(
            tmp_path,
            asset_pool_targets=(("portraits", 10), ("tokens", 5)),
            derived_seeds=(("lexicon", 999),),
        )
        data = original.to_dict()
        json_str = json.dumps(data, sort_keys=True)
        restored_data = json.loads(json_str)
        restored = CompileInputs.from_dict(restored_data)

        assert restored.content_pack_id == original.content_pack_id
        assert restored.world_seed == original.world_seed
        assert restored.locale == original.locale
        assert restored.world_theme_brief.genre == original.world_theme_brief.genre
        assert restored.toolchain_pins.llm_model_id == original.toolchain_pins.llm_model_id

    def test_world_theme_brief_round_trip(self):
        original = WorldThemeBrief(
            genre="sci_fi",
            tone="heroic",
            naming_style="latin",
            technology_level="industrial",
            magic_level="low",
            cosmology_notes="Three moons",
            environmental_palette=("ocean", "jungle"),
        )
        data = original.to_dict()
        restored = WorldThemeBrief.from_dict(data)
        assert restored == original

    def test_toolchain_pins_round_trip(self):
        original = ToolchainPins(
            llm_model_id="qwen3-8b-q4",
            hash_algorithm="sha256",
            schema_version="2.0.0",
            image_model_id="sd-xl-v1",
            music_model_id="musicgen-v2",
        )
        data = original.to_dict()
        restored = ToolchainPins.from_dict(data)
        assert restored == original


# ═══════════════════════════════════════════════════════════════════════
# Test 12: Empty content pack is valid input
# ═══════════════════════════════════════════════════════════════════════


class TestEmptyContentPack:
    """Tests for empty content pack handling."""

    def test_empty_content_pack_produces_valid_bundle(self, tmp_path):
        workspace = tmp_path / "bundle"
        inputs = _make_inputs(tmp_path, compile_config=CompileConfig(output_dir=str(workspace)))
        empty_pack = ContentPackStub(pack_id="test_pack_001", entries=(), content_hash="empty")

        compiler = WorldCompiler(inputs, empty_pack)
        report = compiler.compile(workspace=workspace)

        assert report.status == "success"
        assert (workspace / "world_manifest.json").exists()
        assert (workspace / "bundle_hashes.json").exists()

    def test_content_pack_stub_load_from_empty_dir(self, tmp_path):
        pack_dir = tmp_path / "empty_pack"
        pack_dir.mkdir()
        pack = ContentPackStub.load_from_directory("empty", pack_dir)
        assert pack.pack_id == "empty"
        assert pack.entries == ()
        assert len(pack.content_hash) == 64

    def test_content_pack_stub_round_trip(self):
        original = ContentPackStub(
            pack_id="test",
            entries=({"id": "SPELL_001"},),
            content_hash="abc123",
        )
        data = original.to_dict()
        restored = ContentPackStub.from_dict(data)
        assert restored.pack_id == original.pack_id
        assert restored.content_hash == original.content_hash


# ═══════════════════════════════════════════════════════════════════════
# Additional edge case tests
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Additional edge case coverage."""

    def test_duplicate_stage_registration_raises(self, tmp_path):
        inputs = _make_inputs(tmp_path)
        compiler = WorldCompiler(inputs)
        compiler.register_stage(StubStage("lexicon", 1))
        with pytest.raises(ValueError, match="already registered"):
            compiler.register_stage(StubStage("lexicon", 1))

    def test_seed_override_applied(self, tmp_path):
        workspace = tmp_path / "bundle"
        inputs = _make_inputs(
            tmp_path,
            compile_config=CompileConfig(output_dir=str(workspace)),
            derived_seeds=(("lexicon", 999),),
        )
        context = CompileContext(
            inputs=inputs,
            content_pack=_make_content_pack(),
            workspace=workspace,
            derived_seeds={},
        )
        _run_stage_0(context)
        assert context.derived_seeds["lexicon_seed"] == 999

    def test_enable_stages_filters_execution(self, tmp_path):
        workspace = tmp_path / "bundle"
        config = CompileConfig(output_dir=str(workspace), enable_stages=("maps",))
        inputs = _make_inputs(tmp_path, compile_config=config)

        stage_a = StubStage("lexicon", 1)
        stage_b = StubStage("maps", 6)

        compiler = WorldCompiler(inputs, _make_content_pack())
        compiler.register_stage(stage_a)
        compiler.register_stage(stage_b)
        report = compiler.compile(workspace=workspace)

        assert not stage_a.executed  # Filtered out
        assert stage_b.executed  # Enabled
