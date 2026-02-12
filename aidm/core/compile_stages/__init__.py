"""World Compiler compile stages.

Each stage implements the CompileStage interface and produces
one or more artifacts in the compile workspace.
"""

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.core.compile_stages.npc_archetypes import NPCArchetypeStage
from aidm.core.compile_stages.semantics import SemanticsStage

__all__ = [
    "CompileContext",
    "CompileStage",
    "NPCArchetypeStage",
    "SemanticsStage",
    "StageResult",
]
