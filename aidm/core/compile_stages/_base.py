"""Base interfaces for World Compiler compile stages.

Defines CompileContext, CompileStage, and StageResult — the core
abstractions that every compile stage implements.

NOTE: WorldCompiler/CompileStage may be canonically defined by
WO-WORLDCOMPILE-SCAFFOLD-001 later. This module provides a compatible
local interface until the scaffold WO lands.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


@dataclass
class CompileContext:
    """Immutable bag of inputs available to every compile stage.

    Populated by the WorldCompiler before stage execution begins.
    Stages read from context but never mutate it.
    """

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


@dataclass(frozen=True)
class StageResult:
    """Result returned by a compile stage after execution."""

    stage_id: str
    """Which stage produced this result."""

    success: bool
    """Whether the stage completed without error."""

    artifacts: Tuple[str, ...] = ()
    """Filenames written to the workspace directory."""

    error: Optional[str] = None
    """Error message if success is False."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Stage-specific metadata (entry counts, timings, etc.)."""


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
            StageResult describing what was produced.
        """
