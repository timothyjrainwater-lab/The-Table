"""World Compiler compile stages.

Each stage implements the CompileStage interface and produces
one or more artifacts in the compile workspace.
"""

from aidm.core.compile_stages._base import CompileContext, CompileStage, StageResult
from aidm.core.compile_stages.bestiary import BestiaryStage
from aidm.core.compile_stages.lexicon import LexiconStage
from aidm.core.compile_stages.npc_archetypes import NPCArchetypeStage
from aidm.core.compile_stages.rulebook import RulebookStage
from aidm.core.compile_stages.semantics import SemanticsStage

__all__ = [
    "BestiaryStage",
    "CompileContext",
    "CompileStage",
    "LexiconStage",
    "NPCArchetypeStage",
    "RulebookStage",
    "SemanticsStage",
    "StageResult",
]
