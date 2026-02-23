"""Gate INGESTION — Content Pack Ingestion Stage tests.

15 tests across 5 classes.

WO-WORLDGEN-INGESTION-001
Reference: docs/contracts/WORLD_COMPILER.md §2.0
Reference: FINDING-WORLDGEN-IP-001
"""

import json
from pathlib import Path

import pytest

from aidm.core.compile_stages._base import CompileContext
from aidm.core.compile_stages.ingestion import IC_001, IC_002, IngestionStage
from aidm.core.world_compiler import (
    ContentPackStub,
    WorldCompiler,
    derive_seeds,
)
from aidm.schemas.world_compile import (
    CompileConfig,
    CompileInputs,
    StageResult,
    ToolchainPins,
    WorldThemeBrief,
)

# Real content pack directory
REAL_PACK_DIR = Path(__file__).parent.parent / "aidm" / "data" / "content_pack"


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


def _make_theme():
    return WorldThemeBrief(genre="dark_fantasy", tone="grim", naming_style="anglo_saxon")


def _make_pins():
    return ToolchainPins(llm_model_id="qwen3-8b-q4")


def _make_inputs(tmp_path):
    return CompileInputs(
        content_pack_id="base_3.5e_v1",
        world_theme_brief=_make_theme(),
        world_seed=42,
        compile_config=CompileConfig(output_dir=str(tmp_path)),
        toolchain_pins=_make_pins(),
    )


def _make_context(workspace: Path, inputs: CompileInputs) -> CompileContext:
    """Build a minimal CompileContext for stage tests."""
    return CompileContext(
        content_pack_dir=workspace,
        workspace_dir=workspace,
        world_seed=inputs.world_seed,
        world_theme_brief=inputs.world_theme_brief.to_dict(),
        toolchain_pins=inputs.toolchain_pins.to_dict(),
        content_pack_id=inputs.content_pack_id,
        derived_seeds=derive_seeds(inputs.world_seed),
    )


def _run_stage(tmp_path: Path, pack_dir: Path) -> tuple[StageResult, dict]:
    """Run IngestionStage and return (result, report_dict)."""
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    inputs = _make_inputs(workspace)
    context = _make_context(workspace, inputs)

    stage = IngestionStage(content_pack_dir=pack_dir)
    result = stage.execute(context)

    report = {}
    report_path = workspace / "ingestion_report.json"
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

    return result, report


def _make_minimal_creature(template_id: str) -> dict:
    """Build a minimal creature dict valid for from_dict()."""
    return {
        "template_id": template_id,
        "size_category": "medium",
        "creature_type": "humanoid",
    }


# ═══════════════════════════════════════════════════════════════════════
# Class 1: Smoke tests
# ═══════════════════════════════════════════════════════════════════════


class TestIngestionStageSmoke:
    """INGESTION-01 through INGESTION-03: basic stage contract."""

    def test_stage_id_and_number(self):
        """INGESTION-01: stage_id, stage_number, depends_on."""
        stage = IngestionStage()
        assert stage.stage_id == "ingestion"
        assert stage.stage_number == 0
        assert stage.depends_on == ()

    @pytest.mark.skipif(
        not REAL_PACK_DIR.exists(),
        reason="Real content pack not present",
    )
    def test_execute_with_real_pack(self, tmp_path):
        """INGESTION-02: execute() succeeds with real content pack."""
        result, _ = _run_stage(tmp_path, REAL_PACK_DIR)
        assert result.status == "success"
        assert "ingestion_report.json" in result.output_files

    @pytest.mark.skipif(
        not REAL_PACK_DIR.exists(),
        reason="Real content pack not present",
    )
    def test_ingestion_report_written(self, tmp_path):
        """INGESTION-03: ingestion_report.json has correct schema."""
        result, report = _run_stage(tmp_path, REAL_PACK_DIR)
        assert result.status == "success"
        assert report["status"] == "success"
        assert len(report["content_hash"]) == 64
        assert report["spell_count"] > 0
        assert report["creature_count"] > 0
        assert report["feat_count"] > 0


# ═══════════════════════════════════════════════════════════════════════
# Class 2: Entity counts
# ═══════════════════════════════════════════════════════════════════════


class TestIngestionCounts:
    """INGESTION-04 through INGESTION-06: entity counts in report."""

    @pytest.mark.skipif(
        not REAL_PACK_DIR.exists(),
        reason="Real content pack not present",
    )
    def test_creature_count_matches_content_pack(self, tmp_path):
        """INGESTION-04: creature_count == 273 (known baseline)."""
        from aidm.lens.content_pack_loader import ContentPackLoader

        loader = ContentPackLoader.from_directory(REAL_PACK_DIR)
        assert loader.creature_count == 273

        _, report = _run_stage(tmp_path, REAL_PACK_DIR)
        assert report["creature_count"] == 273

    @pytest.mark.skipif(
        not REAL_PACK_DIR.exists(),
        reason="Real content pack not present",
    )
    def test_spell_count_positive(self, tmp_path):
        """INGESTION-05: spell_count > 0."""
        _, report = _run_stage(tmp_path, REAL_PACK_DIR)
        assert report["spell_count"] > 0

    @pytest.mark.skipif(
        not REAL_PACK_DIR.exists(),
        reason="Real content pack not present",
    )
    def test_feat_count_positive(self, tmp_path):
        """INGESTION-06: feat_count > 0."""
        _, report = _run_stage(tmp_path, REAL_PACK_DIR)
        assert report["feat_count"] > 0


# ═══════════════════════════════════════════════════════════════════════
# Class 3: Content hash
# ═══════════════════════════════════════════════════════════════════════


class TestIngestionContentHash:
    """INGESTION-07 through INGESTION-09: content_hash correctness."""

    @pytest.mark.skipif(
        not REAL_PACK_DIR.exists(),
        reason="Real content pack not present",
    )
    def test_content_hash_is_64_chars(self, tmp_path):
        """INGESTION-07: content_hash is 64-char hex (SHA-256)."""
        _, report = _run_stage(tmp_path, REAL_PACK_DIR)
        assert len(report["content_hash"]) == 64

    @pytest.mark.skipif(
        not REAL_PACK_DIR.exists(),
        reason="Real content pack not present",
    )
    def test_content_hash_is_deterministic(self, tmp_path):
        """INGESTION-08: same pack dir → same content_hash."""
        _, report_a = _run_stage(tmp_path / "a", REAL_PACK_DIR)
        _, report_b = _run_stage(tmp_path / "b", REAL_PACK_DIR)
        assert report_a["content_hash"] == report_b["content_hash"]

    @pytest.mark.skipif(
        not REAL_PACK_DIR.exists(),
        reason="Real content pack not present",
    )
    def test_content_hash_stored_in_stage_outputs(self, tmp_path):
        """INGESTION-09: content_hash in stage_outputs matches report."""
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        inputs = _make_inputs(workspace)
        context = _make_context(workspace, inputs)

        stage = IngestionStage(content_pack_dir=REAL_PACK_DIR)
        stage.execute(context)

        report_path = workspace / "ingestion_report.json"
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)

        assert context.stage_outputs["ingestion"]["content_hash"] == report["content_hash"]


# ═══════════════════════════════════════════════════════════════════════
# Class 4: Failure modes
# ═══════════════════════════════════════════════════════════════════════


class TestIngestionFailureModes:
    """INGESTION-10 through INGESTION-12: error paths."""

    def test_missing_pack_dir_returns_failed(self, tmp_path):
        """INGESTION-10: IC-001 on missing pack directory."""
        result, _ = _run_stage(tmp_path, Path("/nonexistent/pack/dir"))
        assert result.status == "failed"
        assert IC_001 in result.error

    def test_empty_pack_dir_succeeds_with_zero_counts(self, tmp_path):
        """INGESTION-11: empty dir → success, all counts == 0."""
        empty_dir = tmp_path / "empty_pack"
        empty_dir.mkdir()
        result, report = _run_stage(tmp_path, empty_dir)
        assert result.status == "success"
        assert report["creature_count"] == 0
        assert report["spell_count"] == 0
        assert report["feat_count"] == 0

    def test_validation_failure_returns_failed(self, tmp_path):
        """INGESTION-12: IC-002 on duplicate template_ids."""
        bad_pack = tmp_path / "bad_pack"
        bad_pack.mkdir()
        # Two creatures with same template_id — triggers duplicate check
        creatures_data = {
            "creatures": [
                _make_minimal_creature("CREATURE_0001"),
                _make_minimal_creature("CREATURE_0001"),
            ]
        }
        with open(bad_pack / "creatures.json", "w", encoding="utf-8") as f:
            json.dump(creatures_data, f)

        result, _ = _run_stage(tmp_path, bad_pack)
        assert result.status == "failed"
        assert IC_002 in result.error


# ═══════════════════════════════════════════════════════════════════════
# Class 5: Pipeline integration
# ═══════════════════════════════════════════════════════════════════════


class TestIngestionPipelineIntegration:
    """INGESTION-13 through INGESTION-15: WorldCompiler integration."""

    def _make_compiler_inputs(self, tmp_path):
        workspace = tmp_path / "bundle"
        return CompileInputs(
            content_pack_id="base_3.5e_v1",
            world_theme_brief=_make_theme(),
            world_seed=42,
            compile_config=CompileConfig(output_dir=str(workspace)),
            toolchain_pins=_make_pins(),
        ), workspace

    def test_ingestion_registered_in_world_compiler(self, tmp_path):
        """INGESTION-13: IngestionStage runs inside WorldCompiler.compile()."""
        inputs, workspace = self._make_compiler_inputs(tmp_path)
        content_pack = ContentPackStub(pack_id="base_3.5e_v1", content_hash="test")

        compiler = WorldCompiler(inputs, content_pack)
        # Use empty pack dir so stage succeeds without real pack dependency
        empty_pack = tmp_path / "empty_pack"
        empty_pack.mkdir()
        compiler.register_stage(IngestionStage(content_pack_dir=empty_pack))

        report = compiler.compile(workspace=workspace)

        ingestion_results = [r for r in report.stage_results if r.stage_id == "ingestion"]
        assert len(ingestion_results) == 1

    def test_ingestion_runs_before_dependent_stages(self, tmp_path):
        """INGESTION-14: ingestion result appears before lexicon in report."""
        from aidm.core.world_compiler import CompileStage as _CS

        class _StubLexicon(_CS):
            @property
            def stage_id(self): return "lexicon"
            @property
            def stage_number(self): return 1
            @property
            def depends_on(self): return ("ingestion",)
            def execute(self, ctx):
                return StageResult(stage_id="lexicon", status="success", output_files=())

        inputs, workspace = self._make_compiler_inputs(tmp_path)
        content_pack = ContentPackStub(pack_id="base_3.5e_v1", content_hash="test")

        empty_pack = tmp_path / "empty_pack"
        empty_pack.mkdir()

        compiler = WorldCompiler(inputs, content_pack)
        compiler.register_stage(IngestionStage(content_pack_dir=empty_pack))
        compiler.register_stage(_StubLexicon())

        report = compiler.compile(workspace=workspace)

        ids = [r.stage_id for r in report.stage_results]
        # ingestion must appear before lexicon
        assert ids.index("ingestion") < ids.index("lexicon")

    def test_ingestion_failure_halts_dependents(self, tmp_path):
        """INGESTION-15: failed ingestion → dependent stage skipped."""
        from aidm.core.world_compiler import CompileStage as _CS

        class _StubLexicon(_CS):
            @property
            def stage_id(self): return "lexicon"
            @property
            def stage_number(self): return 1
            @property
            def depends_on(self): return ("ingestion",)
            def execute(self, ctx):
                return StageResult(stage_id="lexicon", status="success", output_files=())

        inputs, workspace = self._make_compiler_inputs(tmp_path)
        content_pack = ContentPackStub(pack_id="base_3.5e_v1", content_hash="test")

        compiler = WorldCompiler(inputs, content_pack)
        # Bad path → IC-001 → ingestion fails
        compiler.register_stage(IngestionStage(content_pack_dir=Path("/bad/path")))
        compiler.register_stage(_StubLexicon())

        report = compiler.compile(workspace=workspace)

        ingestion_result = next(r for r in report.stage_results if r.stage_id == "ingestion")
        lexicon_result = next(r for r in report.stage_results if r.stage_id == "lexicon")

        assert ingestion_result.status == "failed"
        assert lexicon_result.status == "skipped"
