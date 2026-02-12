"""World Compiler — offline pipeline that produces a Frozen World Bundle.

Orchestrates world compilation through registered stages. Implements the
pipeline harness (Stage 0 validation + Stage 8 finalization) plus the
plugin interface that stage-specific work orders implement.

Reference: docs/contracts/WORLD_COMPILER.md (full contract)
Reference: docs/schemas/world_bundle.schema.json

BOUNDARY LAW: No imports from aidm/lens/ or aidm/immersion/.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from aidm.core.provenance import ProvenanceStore
from aidm.schemas.world_compile import (
    CompileConfig,
    CompileInputs,
    CompileReport,
    StageResult,
    ToolchainPins,
    WorldThemeBrief,
    IV_001,
    IV_005,
)


# ═══════════════════════════════════════════════════════════════════════
# Seed derivation (§4.1)
# ═══════════════════════════════════════════════════════════════════════

# Canonical stage names for seed derivation (contract §4.1)
_SEED_STAGE_NAMES = (
    "lexicon",
    "map",
    "bestiary",
    "asset",
    "doctrine",
    "rulebook",
    "semantics",
    "npc",
)

_MAX_SEED = (2**63) - 1


def derive_seeds(world_seed: int, stage_names: tuple = _SEED_STAGE_NAMES) -> Dict[str, int]:
    """Derive child seeds for each stage from world_seed.

    Uses sha256(f"{stage_name}:{world_seed}") -> int, clamped to 63-bit.
    Deterministic: same world_seed always produces same child seeds.

    Reference: docs/contracts/WORLD_COMPILER.md §4.1
    """
    seeds: Dict[str, int] = {"world_seed": world_seed}
    for name in stage_names:
        raw = f"{name}:{world_seed}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        seeds[f"{name}_seed"] = int(digest, 16) % (_MAX_SEED + 1)
    return seeds


def compute_world_id(world_seed: int, content_pack_id: str, pins: ToolchainPins) -> str:
    """Compute deterministic world identity hash.

    world_id = sha256(world_seed + content_pack_id + pins_hash)[:32]

    Reference: docs/contracts/WORLD_COMPILER.md §2.8
    """
    pins_serialized = json.dumps(pins.to_dict(), sort_keys=True, separators=(",", ":"))
    pins_hash = hashlib.sha256(pins_serialized.encode("utf-8")).hexdigest()
    raw = f"{world_seed}:{content_pack_id}:{pins_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


# ═══════════════════════════════════════════════════════════════════════
# Content pack stub (minimal, no aidm/lens imports)
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ContentPackStub:
    """Minimal content pack representation for the compiler.

    The real content pack loader will come from WO-CONTENT-PACK-SCHEMA-001.
    This stub provides enough interface for Stage 0 validation and tests.
    """

    pack_id: str
    """Content pack identifier."""

    entries: tuple = ()
    """Content entries as tuple of dicts. Empty is valid (produces empty bundle)."""

    content_hash: str = ""
    """SHA-256 hash of the content pack data."""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to JSON-compatible dictionary."""
        return {
            "pack_id": self.pack_id,
            "entries": list(self.entries),
            "content_hash": self.content_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentPackStub":
        """Deserialize from dictionary."""
        return cls(
            pack_id=data["pack_id"],
            entries=tuple(data.get("entries", [])),
            content_hash=data.get("content_hash", ""),
        )

    @classmethod
    def load_from_directory(cls, pack_id: str, directory: Path) -> "ContentPackStub":
        """Load content pack from a directory of JSON files.

        Reads all .json files, sorts by filename for determinism,
        and computes a content hash over the sorted data.
        """
        entries: List[Dict[str, Any]] = []
        if directory.exists():
            for json_file in sorted(directory.glob("*.json")):
                with open(json_file, "r", encoding="utf-8") as f:
                    entries.append(json.load(f))

        serialized = json.dumps(entries, sort_keys=True, separators=(",", ":"))
        content_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return cls(
            pack_id=pack_id,
            entries=tuple(entries) if entries else (),
            content_hash=content_hash,
        )


# ═══════════════════════════════════════════════════════════════════════
# Compile Stage interface (ABC)
# ═══════════════════════════════════════════════════════════════════════


class CompileStage(ABC):
    """Abstract base for a single compile stage.

    Stage-specific work orders implement this interface. The WorldCompiler
    executes stages in dependency order (topological sort).
    """

    @property
    @abstractmethod
    def stage_id(self) -> str:
        """Stage identifier: 'lexicon', 'rulebook', 'bestiary', etc."""
        ...

    @property
    @abstractmethod
    def stage_number(self) -> int:
        """Stage number (1-7). Stages 0 and 8 are built-in."""
        ...

    @property
    @abstractmethod
    def depends_on(self) -> tuple:
        """Stage IDs this stage depends on. Tuple of strings."""
        ...

    @abstractmethod
    def execute(self, context: CompileContext) -> StageResult:
        """Execute this compile stage.

        Args:
            context: Mutable compile context with inputs, workspace,
                     and accumulated stage outputs.

        Returns:
            StageResult indicating success/failure.
        """
        ...


# ═══════════════════════════════════════════════════════════════════════
# Compile Context (mutable, passed between stages)
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class CompileContext:
    """Mutable context passed between compile stages.

    Accumulates outputs from each stage. Stages read from stage_outputs
    and write their own results.
    """

    inputs: CompileInputs
    """Frozen compile inputs."""

    content_pack: ContentPackStub
    """Content pack data (frozen)."""

    workspace: Path
    """Compile workspace directory."""

    derived_seeds: Dict[str, int]
    """Stage-specific derived seeds."""

    stage_outputs: Dict[str, Any] = field(default_factory=dict)
    """Accumulated outputs from completed stages: {stage_id: output_data}."""

    provenance: ProvenanceStore = field(default_factory=ProvenanceStore)
    """PROV-DM tracking for compile provenance."""

    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("world_compiler"))
    """Logger instance for compile messages."""


# ═══════════════════════════════════════════════════════════════════════
# Built-in stages: Stage 0 (Validate) and Stage 8 (Finalize)
# ═══════════════════════════════════════════════════════════════════════


def _hash_file(file_path: Path) -> str:
    """Compute SHA-256 hash of a file's contents."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_stage_0(context: CompileContext) -> StageResult:
    """Stage 0: Validate inputs + create workspace.

    1. Validate all required inputs against schemas (§1.3)
    2. Verify content pack exists and is loadable
    3. Verify toolchain pins don't contain 'latest'
    4. Derive child seeds from world_seed
    5. Create compile workspace directory
    6. Write compile_inputs.json (frozen snapshot)

    Reference: docs/contracts/WORLD_COMPILER.md §2.0
    """
    start_ms = time.monotonic_ns() // 1_000_000
    warnings: List[str] = []
    output_files: List[str] = []

    # 1. Validate inputs
    errors = context.inputs.validate()
    if errors:
        elapsed = (time.monotonic_ns() // 1_000_000) - start_ms
        return StageResult(
            stage_id="validate",
            status="failed",
            output_files=(),
            error="; ".join(errors),
            elapsed_ms=elapsed,
        )

    # 2. Verify content pack
    if not context.content_pack.pack_id:
        elapsed = (time.monotonic_ns() // 1_000_000) - start_ms
        return StageResult(
            stage_id="validate",
            status="failed",
            output_files=(),
            error=IV_001,
            elapsed_ms=elapsed,
        )

    # 3. Verify no 'latest' in pins (already checked in validate, but explicit)
    pins_dict = context.inputs.toolchain_pins.to_dict()
    for key, value in pins_dict.items():
        if isinstance(value, str) and "latest" in value.lower():
            elapsed = (time.monotonic_ns() // 1_000_000) - start_ms
            return StageResult(
                stage_id="validate",
                status="failed",
                output_files=(),
                error=f"{IV_005} (field: {key})",
                elapsed_ms=elapsed,
            )

    # 4. Derive child seeds (apply overrides from derived_seeds)
    seeds = derive_seeds(context.inputs.world_seed)
    override_dict = dict(context.inputs.derived_seeds)
    for stage_id, seed_val in override_dict.items():
        seed_key = f"{stage_id}_seed"
        if seed_key in seeds:
            seeds[seed_key] = seed_val
            warnings.append(f"Seed override applied: {seed_key}={seed_val}")
    context.derived_seeds.update(seeds)

    # 5. Create workspace
    context.workspace.mkdir(parents=True, exist_ok=True)

    # 6. Write compile_inputs.json
    inputs_path = context.workspace / "compile_inputs.json"
    inputs_data = context.inputs.to_dict()
    inputs_data["derived_seeds"] = seeds
    with open(inputs_path, "w", encoding="utf-8") as f:
        json.dump(inputs_data, f, indent=2, sort_keys=True)
    output_files.append("compile_inputs.json")

    elapsed = (time.monotonic_ns() // 1_000_000) - start_ms
    return StageResult(
        stage_id="validate",
        status="success",
        output_files=tuple(output_files),
        warnings=tuple(warnings),
        elapsed_ms=elapsed,
    )


def _run_stage_8(context: CompileContext, stage_results: List[StageResult]) -> StageResult:
    """Stage 8: Finalize hashes + write manifest + compile report.

    1. Compute SHA-256 hash of every file in the bundle workspace
    2. Write bundle_hashes.json
    3. Compute root bundle hash: sha256(sorted(all_file_hashes))
    4. Write world_manifest.json (§2.8)
    5. Write compile_report.json with stage timings, warnings, status

    Reference: docs/contracts/WORLD_COMPILER.md §2.8
    """
    start_ms = time.monotonic_ns() // 1_000_000
    output_files: List[str] = []
    warnings: List[str] = []

    workspace = context.workspace

    # 1. Compute SHA-256 hash of every file in the bundle
    file_hashes: Dict[str, str] = {}
    for file_path in sorted(workspace.rglob("*")):
        if file_path.is_file():
            rel_path = file_path.relative_to(workspace).as_posix()
            # Skip files we're about to write
            if rel_path in ("bundle_hashes.json", "world_manifest.json", "compile_report.json"):
                continue
            file_hashes[rel_path] = _hash_file(file_path)

    # 2. Write bundle_hashes.json
    # Root hash: sha256 of sorted concatenation of all file hashes
    sorted_hashes = [file_hashes[k] for k in sorted(file_hashes.keys())]
    hash_concat = "".join(sorted_hashes)
    root_hash = hashlib.sha256(hash_concat.encode("utf-8")).hexdigest()

    bundle_hashes_data = {
        "root_hash": root_hash,
        "algorithm": context.inputs.toolchain_pins.hash_algorithm,
        "files": {k: file_hashes[k] for k in sorted(file_hashes.keys())},
    }
    hashes_path = workspace / "bundle_hashes.json"
    with open(hashes_path, "w", encoding="utf-8") as f:
        json.dump(bundle_hashes_data, f, indent=2, sort_keys=True)
    output_files.append("bundle_hashes.json")

    # 3. Compute world_id
    world_id = compute_world_id(
        context.inputs.world_seed,
        context.inputs.content_pack_id,
        context.inputs.toolchain_pins,
    )

    # 4. Write world_manifest.json
    manifest_data = {
        "world_id": world_id,
        "world_name": context.stage_outputs.get("world_name", ""),
        "schema_version": context.inputs.toolchain_pins.schema_version,
        "compile_timestamp": datetime.now(timezone.utc).isoformat(),
        "toolchain_pins": context.inputs.toolchain_pins.to_dict(),
        "seeds": context.derived_seeds,
        "content_pack_id": context.inputs.content_pack_id,
        "content_pack_hash": context.content_pack.content_hash,
        "root_hash": root_hash,
        "file_count": len(file_hashes) + 2,  # +2 for manifest + hashes themselves
        "world_theme_brief": {
            "genre": context.inputs.world_theme_brief.genre,
            "tone": context.inputs.world_theme_brief.tone,
            "naming_style": context.inputs.world_theme_brief.naming_style,
        },
    }
    manifest_path = workspace / "world_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, sort_keys=True)
    output_files.append("world_manifest.json")

    # 5. Determine overall status
    all_warnings: List[str] = []
    for r in stage_results:
        all_warnings.extend(r.warnings)
    all_warnings.extend(warnings)

    any_failed = any(r.status == "failed" for r in stage_results)
    any_skipped = any(r.status == "skipped" for r in stage_results)
    if any_failed:
        overall_status = "failed"
    elif any_skipped:
        overall_status = "partial"
    else:
        overall_status = "success"

    elapsed = (time.monotonic_ns() // 1_000_000) - start_ms

    # Write compile_report.json
    finalize_result = StageResult(
        stage_id="finalize",
        status="success",
        output_files=tuple(output_files),
        warnings=tuple(warnings),
        elapsed_ms=elapsed,
    )
    all_results = list(stage_results) + [finalize_result]
    total_elapsed = sum(r.elapsed_ms for r in all_results)

    report_data = {
        "status": overall_status,
        "world_id": world_id,
        "root_hash": root_hash,
        "schema_version": context.inputs.toolchain_pins.schema_version,
        "compile_timestamp": manifest_data["compile_timestamp"],
        "stage_results": [r.to_dict() for r in all_results],
        "total_elapsed_ms": total_elapsed,
        "warnings": all_warnings,
        "input_snapshot_hash": hashlib.sha256(
            json.dumps(context.inputs.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }
    report_path = workspace / "compile_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, sort_keys=True)

    return StageResult(
        stage_id="finalize",
        status="success",
        output_files=tuple(output_files + ["compile_report.json"]),
        warnings=tuple(warnings),
        elapsed_ms=elapsed,
    )


# ═══════════════════════════════════════════════════════════════════════
# Topological sort for stage dependency ordering
# ═══════════════════════════════════════════════════════════════════════


def _topological_sort(stages: Dict[str, CompileStage]) -> List[str]:
    """Sort stages by dependency order (Kahn's algorithm).

    Returns list of stage_ids in execution order.
    Raises ValueError if there's a dependency cycle.
    """
    # Build adjacency and in-degree maps
    in_degree: Dict[str, int] = {sid: 0 for sid in stages}
    dependents: Dict[str, List[str]] = {sid: [] for sid in stages}

    for sid, stage in stages.items():
        for dep in stage.depends_on:
            if dep in stages:
                in_degree[sid] += 1
                dependents[dep].append(sid)

    # Start with zero in-degree nodes, sorted by stage_number for determinism
    queue: List[str] = sorted(
        [sid for sid, deg in in_degree.items() if deg == 0],
        key=lambda sid: stages[sid].stage_number,
    )
    result: List[str] = []

    while queue:
        current = queue.pop(0)
        result.append(current)
        for dep_sid in sorted(dependents[current], key=lambda s: stages[s].stage_number):
            in_degree[dep_sid] -= 1
            if in_degree[dep_sid] == 0:
                queue.append(dep_sid)
        # Re-sort queue for determinism
        queue.sort(key=lambda s: stages[s].stage_number)

    if len(result) != len(stages):
        missing = set(stages.keys()) - set(result)
        raise ValueError(f"Dependency cycle detected involving stages: {missing}")

    return result


# ═══════════════════════════════════════════════════════════════════════
# World Compiler (orchestrator)
# ═══════════════════════════════════════════════════════════════════════


class WorldCompiler:
    """Orchestrates world compilation through registered stages.

    Usage:
        compiler = WorldCompiler(inputs, content_pack)
        compiler.register_stage(LexiconStage())
        compiler.register_stage(RulebookStage())
        report = compiler.compile()

    The compiler handles:
    - Stage 0 (validation) and Stage 8 (finalization) automatically
    - Dependency ordering via topological sort
    - Fail-closed: any stage failure halts downstream dependents
    - Deterministic seed derivation from world_seed
    """

    def __init__(
        self,
        inputs: CompileInputs,
        content_pack: Optional[ContentPackStub] = None,
    ) -> None:
        self._inputs = inputs
        self._content_pack = content_pack or ContentPackStub(pack_id=inputs.content_pack_id)
        self._stages: Dict[str, CompileStage] = {}
        self._results: List[StageResult] = []

    def register_stage(self, stage: CompileStage) -> None:
        """Register a compile stage. Order determined by dependencies."""
        if stage.stage_id in self._stages:
            raise ValueError(f"Stage already registered: {stage.stage_id}")
        self._stages[stage.stage_id] = stage

    def compile(self, workspace: Optional[Path] = None) -> CompileReport:
        """Execute all registered stages in dependency order.

        1. Stage 0: Validate inputs + create workspace
        2. Execute stages respecting depends_on (topological sort)
        3. Stage 8: Finalize hashes + write manifest

        Args:
            workspace: Override workspace directory. If None, uses
                       compile_config.output_dir.

        Returns:
            CompileReport with overall status.
        """
        compile_start = time.monotonic_ns() // 1_000_000
        self._results = []

        # Resolve workspace
        if workspace is None:
            workspace = Path(self._inputs.compile_config.output_dir)

        # Build context
        context = CompileContext(
            inputs=self._inputs,
            content_pack=self._content_pack,
            workspace=workspace,
            derived_seeds={},
        )

        # Configure logger
        log_level = getattr(logging, self._inputs.compile_config.log_level, logging.INFO)
        context.logger.setLevel(log_level)

        # ── Stage 0: Validate ──────────────────────────────────────
        stage_0_result = _run_stage_0(context)
        self._results.append(stage_0_result)

        if stage_0_result.status == "failed":
            # Fail-closed: write report and return
            total_elapsed = (time.monotonic_ns() // 1_000_000) - compile_start
            world_id = compute_world_id(
                self._inputs.world_seed,
                self._inputs.content_pack_id,
                self._inputs.toolchain_pins,
            )
            return CompileReport(
                status="failed",
                world_id=world_id,
                root_hash="",
                stage_results=tuple(self._results),
                total_elapsed_ms=total_elapsed,
                error=stage_0_result.error,
            )

        # ── Execute registered stages in dependency order ──────────
        failed_stages: set = set()

        if self._stages:
            # Filter stages by enable_stages if configured
            enabled = set(self._inputs.compile_config.enable_stages)
            active_stages = {
                sid: stage for sid, stage in self._stages.items()
                if not enabled or sid in enabled
            }

            if active_stages:
                try:
                    execution_order = _topological_sort(active_stages)
                except ValueError as e:
                    total_elapsed = (time.monotonic_ns() // 1_000_000) - compile_start
                    return CompileReport(
                        status="failed",
                        world_id=compute_world_id(
                            self._inputs.world_seed,
                            self._inputs.content_pack_id,
                            self._inputs.toolchain_pins,
                        ),
                        root_hash="",
                        stage_results=tuple(self._results),
                        total_elapsed_ms=total_elapsed,
                        error=str(e),
                    )

                for stage_id in execution_order:
                    stage = active_stages[stage_id]

                    # Check if any dependency failed
                    deps_failed = any(dep in failed_stages for dep in stage.depends_on)
                    if deps_failed:
                        skip_result = StageResult(
                            stage_id=stage_id,
                            status="skipped",
                            output_files=(),
                            warnings=(
                                f"Skipped due to failed dependency: "
                                f"{[d for d in stage.depends_on if d in failed_stages]}",
                            ),
                        )
                        self._results.append(skip_result)
                        failed_stages.add(stage_id)
                        continue

                    # Execute stage
                    try:
                        result = stage.execute(context)
                    except Exception as exc:
                        result = StageResult(
                            stage_id=stage_id,
                            status="failed",
                            output_files=(),
                            error=str(exc),
                        )

                    self._results.append(result)
                    if result.status == "failed":
                        failed_stages.add(stage_id)

        # ── Stage 8: Finalize ──────────────────────────────────────
        stage_8_result = _run_stage_8(context, self._results)
        self._results.append(stage_8_result)

        # Build final report
        total_elapsed = (time.monotonic_ns() // 1_000_000) - compile_start

        all_warnings: List[str] = []
        for r in self._results:
            all_warnings.extend(r.warnings)

        any_failed = any(r.status == "failed" for r in self._results)
        any_skipped = any(r.status == "skipped" for r in self._results)
        if any_failed:
            overall_status = "failed"
        elif any_skipped:
            overall_status = "partial"
        else:
            overall_status = "success"

        world_id = compute_world_id(
            self._inputs.world_seed,
            self._inputs.content_pack_id,
            self._inputs.toolchain_pins,
        )

        # Read root_hash from bundle_hashes.json
        hashes_path = context.workspace / "bundle_hashes.json"
        root_hash = ""
        if hashes_path.exists():
            with open(hashes_path, "r", encoding="utf-8") as f:
                hashes_data = json.load(f)
                root_hash = hashes_data.get("root_hash", "")

        return CompileReport(
            status=overall_status,
            world_id=world_id,
            root_hash=root_hash,
            stage_results=tuple(self._results),
            total_elapsed_ms=total_elapsed,
            warnings=tuple(all_warnings),
            error=self._results[-1].error if any_failed else None,
        )
