"""Lens Layer — Spark-Box Data Membrane

The Lens layer implements Axiom 3: LENS adapts stance, not authority.
It mediates between Box (mechanical resolution) and Spark (narration),
controlling what mechanical data Spark can see.

BOUNDARY LAW (BL-003): Lens must NOT import from core (BOX) directly.
Lens receives FrozenWorldStateView for read-only state access.

BOUNDARY LAW (BL-004): BOX must not import from Lens.
Data flows one way: Box → Lens → Spark.

Module Structure:
- narrative_brief: NarrativeBrief dataclass + assembler (WO-032)
- context_assembler: Token-budget-aware context window builder (WO-032)

Reference: docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md
"""

from aidm.lens.narrative_brief import (
    NarrativeBrief,
    assemble_narrative_brief,
)
from aidm.lens.context_assembler import (
    ContextAssembler,
    RetrievedItem,
    compute_relevance_score,
    MAX_RECENT_NARRATIONS,
    MAX_SESSION_SUMMARIES,
)
from aidm.lens.segment_summarizer import (
    SessionSegmentSummary,
    SegmentSummarizer,
    SegmentTracker,
    DriftResult,
    SEGMENT_SIZE,
)
from aidm.lens.discovery_log import (
    DiscoveryLog as LensDiscoveryLog,
    KnowledgeEvent,
    KnowledgeSource,
)

__all__ = [
    "NarrativeBrief",
    "assemble_narrative_brief",
    "ContextAssembler",
    "RetrievedItem",
    "compute_relevance_score",
    "MAX_RECENT_NARRATIONS",
    "MAX_SESSION_SUMMARIES",
    "SessionSegmentSummary",
    "SegmentSummarizer",
    "SegmentTracker",
    "DriftResult",
    "SEGMENT_SIZE",
    "LensDiscoveryLog",
    "KnowledgeEvent",
    "KnowledgeSource",
]
