"""Base interfaces for World Compiler compile stages.

Defines CompileContext, CompileStage, and StageResult — the canonical
abstractions that every compile stage implements.

WO-UNIFY-COMPILE-001: Unified type hierarchy. The orchestrator
(world_compiler.py) and all stages share these types. StageResult
is re-exported from aidm.schemas.world_compile (the canonical frozen
dataclass with status/output_files/warnings/elapsed_ms).
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from aidm.schemas.world_compile import StageResult  # noqa: F401 — canonical


@dataclass
class CompileContext:
    """Mutable context passed between compile stages.

    Populated by the WorldCompiler before stage execution begins.
    Stages read the flat convenience fields (content_pack_dir,
    workspace_dir, world_seed, etc.) and write outputs to
    stage_outputs.

    Orchestrator-specific fields (stage_outputs, provenance, logger)
    are used by the pipeline harness but are safe to ignore in stages.
    """

    # ── Stage-facing fields (flat, used by all stages) ──────────
    content_pack_dir: Path
    """Path to the content pack directory."""

    workspace_dir: Path
    """Path to the compile workspace (output directory)."""

    world_seed: int
    """Primary world generation seed."""

    world_theme_brief: Dict[str, Any]
    """Structured theme descriptor (genre, tone, naming_style, ...)."""

    toolchain_pins: Dict[str, Any]
    """Pinned tool versions (llm_model_id, hash_algorithm, schema_version, ...)."""

    content_pack_id: str = "base_3.5e_v1"
    """Content pack identifier."""

    locale: str = "en"
    """BCP-47 locale tag."""

    world_id: str = ""
    """World identity hash (set after validation stage)."""

    derived_seeds: Dict[str, int] = field(default_factory=dict)
    """Override derived seeds for specific stages."""

    # ── Orchestrator-facing fields (used by WorldCompiler) ──────
    stage_outputs: Dict[str, Any] = field(default_factory=dict)
    """Accumulated outputs from completed stages: {stage_id: output_data}."""

    logger: logging.Logger = field(
        default_factory=lambda: logging.getLogger("world_compiler")
    )
    """Logger instance for compile messages."""

    # ── Backward-compatible alias ──────────────────────────────
    @property
    def workspace(self) -> Path:
        """Alias for workspace_dir (used by Stage 8 finalization)."""
        return self.workspace_dir


class CompileStage(abc.ABC):
    """Abstract base class for a single World Compiler stage."""

    @property
    @abc.abstractmethod
    def stage_id(self) -> str:
        """Unique stage identifier (e.g., 'lexicon', 'rulebook')."""

    @property
    @abc.abstractmethod
    def stage_number(self) -> int:
        """Numeric order in the compile pipeline."""

    @property
    @abc.abstractmethod
    def depends_on(self) -> Tuple[str, ...]:
        """Stage IDs that must complete before this stage runs."""

    @abc.abstractmethod
    def execute(self, context: CompileContext) -> StageResult:
        """Run the stage and produce artifacts in the workspace.

        Args:
            context: Compile context with all inputs and workspace path.

        Returns:
            StageResult with status, output_files, and optional warnings/error.
        """
