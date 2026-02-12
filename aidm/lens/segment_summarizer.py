"""WO-060: Summarization Stability Protocol — Template-Based Segment Summaries

Implements RQ-LENS-SPARK-001 Deliverable 3 (Phase 1):
- SessionSegmentSummary: frozen dataclass for 10-turn segment summaries
- Template-based summarization from NarrativeBrief history (deterministic)
- Drift detection: entity state consistency and fact monotonicity
- Rebuild-from-sources on drift

SUMMARY TRIGGERS:
- Every 10 turns: segment summary from NarrativeBrief history
- On scene transition: departing scene summary
- On combat end: encounter summary

SUMMARY FORMAT (v1 — template-based, NOT LLM):
  "Turns {start}-{end}: {actor} engaged {target} in combat.
   {hit_count} hits, {miss_count} misses. Severity: {max_severity}.
   {defeated_list}. Scene: {scene_description}."

DRIFT DETECTION:
- Entity state consistency: defeated entities must not act in future segments
- Fact monotonicity: facts that cannot un-happen are checked
- On drift: rebuild from raw NarrativeBrief history (deterministic)

BOUNDARY LAW (BL-003): No imports from aidm.core.
AXIOM 3: Lens adapts stance — we summarize presentations, not mechanics.

CITATIONS:
- RQ-LENS-SPARK-001: Context Orchestration Sprint (Deliverable 3)
- WO-060: Summarization Stability Protocol
"""

import hashlib
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ==============================================================================
# SESSION SEGMENT SUMMARY
# ==============================================================================


@dataclass(frozen=True)
class SessionSegmentSummary:
    """Summary of a 10-turn (or trigger-based) session segment.

    Generated from NarrativeBrief history using deterministic templates.
    Carries provenance metadata for drift detection and rebuild.

    Attributes:
        segment_id: Unique segment identifier (e.g., "seg_001")
        turn_range: (start_turn, end_turn) inclusive
        summary_text: 2-3 sentence factual summary
        key_facts: Bullet points of state changes
        entity_states: entity_name → status at segment end
        defeated_entities: Set of entity names defeated in this segment
        content_hash: SHA-256 of inputs that generated this summary
        schema_version: "1.0.0"
    """
    segment_id: str
    turn_range: Tuple[int, int]
    summary_text: str
    key_facts: Tuple[str, ...]
    entity_states: Tuple[Tuple[str, str], ...]  # Frozen pairs for immutability
    defeated_entities: FrozenSet[str]
    content_hash: str
    schema_version: str = "1.0.0"

    @property
    def entity_state_dict(self) -> Dict[str, str]:
        """Entity states as a mutable dict (convenience accessor)."""
        return dict(self.entity_states)


# ==============================================================================
# DRIFT RESULT
# ==============================================================================


@dataclass(frozen=True)
class DriftResult:
    """Result of drift detection between consecutive segments.

    Attributes:
        has_drift: Whether any drift was detected
        drifted_entities: Entities with state inconsistencies
        details: Human-readable drift descriptions
    """
    has_drift: bool
    drifted_entities: Tuple[str, ...]
    details: Tuple[str, ...]


# ==============================================================================
# SEGMENT SUMMARIZER
# ==============================================================================


# Action types that count as "hit" for summary statistics
_HIT_ACTIONS = {
    'attack_hit', 'critical', 'spell_damage_dealt',
    'full_attack_hit', 'aoo_hit',
}

# Action types that count as "miss"
_MISS_ACTIONS = {
    'attack_miss', 'concealment_miss', 'spell_no_effect',
    'spell_resisted', 'full_attack_miss', 'aoo_miss',
}

# Severity ordering for max_severity
_SEVERITY_ORDER = {
    'minor': 0,
    'moderate': 1,
    'severe': 2,
    'devastating': 3,
    'lethal': 4,
}


class SegmentSummarizer:
    """Generates deterministic segment summaries from NarrativeBrief history.

    Template-based summarization (v1). No LLM involved.
    Same inputs always produce the same summary.

    Usage:
        summarizer = SegmentSummarizer()

        # Generate summary for turns 1-10
        summary = summarizer.summarize(
            briefs=briefs[0:10],
            segment_id="seg_001",
            turn_range=(1, 10),
        )

        # Check for drift between consecutive summaries
        drift = summarizer.detect_drift(summary_a, summary_b)
    """

    def __init__(self):
        """Initialize summarizer."""
        pass

    def summarize(
        self,
        briefs: List[Any],
        segment_id: str,
        turn_range: Tuple[int, int],
    ) -> SessionSegmentSummary:
        """Generate a segment summary from NarrativeBrief history.

        Deterministic template-based summarization.

        Args:
            briefs: List of NarrativeBrief objects for this segment
            segment_id: Unique segment ID
            turn_range: (start_turn, end_turn) inclusive

        Returns:
            Frozen SessionSegmentSummary
        """
        if not briefs:
            return SessionSegmentSummary(
                segment_id=segment_id,
                turn_range=turn_range,
                summary_text=f"Turns {turn_range[0]}-{turn_range[1]}: No significant events.",
                key_facts=(),
                entity_states=(),
                defeated_entities=frozenset(),
                content_hash=self._compute_hash(briefs, segment_id, turn_range),
            )

        # Collect statistics
        hit_count = 0
        miss_count = 0
        max_severity = 'minor'
        defeated: Set[str] = set()
        entity_states: Dict[str, str] = {}
        key_facts: List[str] = []
        actors: Counter = Counter()
        targets: Counter = Counter()
        scene_desc = None

        for brief in briefs:
            action_type = getattr(brief, 'action_type', '')
            actor = getattr(brief, 'actor_name', '')
            target = getattr(brief, 'target_name', '')
            severity = getattr(brief, 'severity', 'minor')
            target_defeated = getattr(brief, 'target_defeated', False)
            condition = getattr(brief, 'condition_applied', None)
            scene = getattr(brief, 'scene_description', None)

            if actor:
                actors[actor] += 1
            if target:
                targets[target] += 1

            # Hit/miss counting
            if action_type in _HIT_ACTIONS:
                hit_count += 1
            elif action_type in _MISS_ACTIONS:
                miss_count += 1

            # Max severity
            if _SEVERITY_ORDER.get(severity, 0) > _SEVERITY_ORDER.get(max_severity, 0):
                max_severity = severity

            # Defeat tracking
            if target_defeated and target:
                defeated.add(target)
                key_facts.append(f"{target} was defeated")
                entity_states[target] = "defeated"

            # Condition tracking
            if condition and target:
                key_facts.append(f"{target} became {condition}")
                if target not in entity_states or entity_states[target] != "defeated":
                    entity_states[target] = condition

            # Scene (use last seen)
            if scene:
                scene_desc = scene

            # Track entity states for non-defeated entities
            if actor and actor not in entity_states:
                entity_states[actor] = "active"
            if target and target not in entity_states:
                entity_states[target] = "active"

        # Build summary text
        summary_parts = [f"Turns {turn_range[0]}-{turn_range[1]}:"]

        # Most active participant
        if actors:
            primary_actor = actors.most_common(1)[0][0]
        else:
            primary_actor = "Unknown"

        if targets:
            primary_target = targets.most_common(1)[0][0]
        else:
            primary_target = None

        if hit_count > 0 or miss_count > 0:
            if primary_target:
                summary_parts.append(
                    f"{primary_actor} engaged {primary_target} in combat."
                )
            else:
                summary_parts.append(f"{primary_actor} was in combat.")
            summary_parts.append(
                f"{hit_count} hit{'s' if hit_count != 1 else ''}, "
                f"{miss_count} miss{'es' if miss_count != 1 else ''}."
            )
            summary_parts.append(f"Severity: {max_severity}.")
        else:
            summary_parts.append(f"{primary_actor} acted.")

        if defeated:
            defeated_list = ", ".join(sorted(defeated))
            summary_parts.append(f"Defeated: {defeated_list}.")

        if scene_desc:
            summary_parts.append(f"Scene: {scene_desc}.")

        summary_text = " ".join(summary_parts)

        # Deduplicate key facts
        seen_facts: Set[str] = set()
        unique_facts: List[str] = []
        for fact in key_facts:
            if fact not in seen_facts:
                seen_facts.add(fact)
                unique_facts.append(fact)

        return SessionSegmentSummary(
            segment_id=segment_id,
            turn_range=turn_range,
            summary_text=summary_text,
            key_facts=tuple(unique_facts),
            entity_states=tuple(sorted(entity_states.items())),
            defeated_entities=frozenset(defeated),
            content_hash=self._compute_hash(briefs, segment_id, turn_range),
        )

    def detect_drift(
        self,
        earlier: SessionSegmentSummary,
        later: SessionSegmentSummary,
    ) -> DriftResult:
        """Detect state drift between consecutive segments.

        Checks two invariants:
        1. Entity state consistency: defeated entities must not act in later segment
        2. Fact monotonicity: defeat is permanent (cannot un-happen)

        Args:
            earlier: The chronologically earlier segment
            later: The chronologically later segment

        Returns:
            DriftResult with drift details
        """
        drifted: List[str] = []
        details: List[str] = []

        # Check 1: Defeated entities should not appear active in later segment
        later_states = later.entity_state_dict
        for entity in earlier.defeated_entities:
            if entity in later_states and later_states[entity] == "active":
                drifted.append(entity)
                details.append(
                    f"Entity '{entity}' was defeated in segment {earlier.segment_id} "
                    f"(turns {earlier.turn_range[0]}-{earlier.turn_range[1]}) "
                    f"but appears active in segment {later.segment_id} "
                    f"(turns {later.turn_range[0]}-{later.turn_range[1]})"
                )

        # Check 2: Fact monotonicity — defeat cannot be reversed
        for entity in earlier.defeated_entities:
            if entity not in later.defeated_entities:
                # Entity was defeated earlier but not in later's defeated set
                # This is only drift if the entity appears at all in later segment
                if entity in later_states:
                    if entity not in drifted:
                        drifted.append(entity)
                    details.append(
                        f"Fact monotonicity violation: '{entity}' defeated in "
                        f"segment {earlier.segment_id} but defeat not carried forward "
                        f"to segment {later.segment_id}"
                    )

        return DriftResult(
            has_drift=len(drifted) > 0,
            drifted_entities=tuple(drifted),
            details=tuple(details),
        )

    def rebuild_from_sources(
        self,
        briefs: List[Any],
        segment_id: str,
        turn_range: Tuple[int, int],
    ) -> SessionSegmentSummary:
        """Rebuild a segment summary from raw NarrativeBrief sources.

        Called when drift is detected. Produces a fresh summary from the
        original briefs, replacing the stale one.

        This is identical to summarize() — the rebuild is deterministic,
        so calling summarize() with the same inputs produces the same output.

        Args:
            briefs: Original NarrativeBrief history for this segment
            segment_id: Segment ID (reused from stale summary)
            turn_range: Turn range (reused from stale summary)

        Returns:
            Fresh SessionSegmentSummary rebuilt from sources
        """
        logger.warning(
            f"Rebuilding segment {segment_id} (turns {turn_range[0]}-{turn_range[1]}) "
            "from raw NarrativeBrief sources due to drift detection"
        )
        return self.summarize(briefs, segment_id, turn_range)

    @staticmethod
    def _compute_hash(
        briefs: List[Any],
        segment_id: str,
        turn_range: Tuple[int, int],
    ) -> str:
        """Compute content hash for summary provenance.

        Hash of the inputs (briefs + segment metadata), not the output.
        Used for drift detection and rebuild verification.

        Args:
            briefs: Source NarrativeBriefs
            segment_id: Segment ID
            turn_range: Turn range

        Returns:
            SHA-256 hex digest
        """
        parts = [segment_id, str(turn_range)]
        for brief in briefs:
            action = getattr(brief, 'action_type', '')
            actor = getattr(brief, 'actor_name', '')
            target = getattr(brief, 'target_name', '')
            severity = getattr(brief, 'severity', '')
            defeated = getattr(brief, 'target_defeated', False)
            parts.append(f"{action}|{actor}|{target}|{severity}|{defeated}")

        combined = "\n".join(parts)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()


# ==============================================================================
# SEGMENT TRACKER (Turn Counter + Auto-Trigger)
# ==============================================================================


SEGMENT_SIZE = 10  # Turns per segment


class SegmentTracker:
    """Tracks turn progress and triggers segment summary generation.

    Integrates with SessionOrchestrator to automatically generate
    segment summaries every SEGMENT_SIZE turns, on scene transitions,
    and on combat end.

    Usage:
        tracker = SegmentTracker()
        tracker.record_turn(brief, turn_number=1)
        ...
        tracker.record_turn(brief, turn_number=10)
        # Automatically generates segment summary at turn 10

        summaries = tracker.get_summaries()
    """

    def __init__(self, summarizer: Optional[SegmentSummarizer] = None):
        """Initialize tracker.

        Args:
            summarizer: Optional SegmentSummarizer instance. Creates default if None.
        """
        self._summarizer = summarizer or SegmentSummarizer()
        self._current_segment_briefs: List[Any] = []
        self._segment_start_turn: int = 1
        self._summaries: List[SessionSegmentSummary] = []
        self._segment_counter: int = 0
        self._all_defeated: Set[str] = set()  # Cumulative defeated entities

    def record_turn(
        self,
        brief: Any,
        turn_number: int,
    ) -> Optional[SessionSegmentSummary]:
        """Record a turn and potentially trigger segment summary.

        Args:
            brief: NarrativeBrief for this turn
            turn_number: Current turn number

        Returns:
            SessionSegmentSummary if a segment boundary was hit, None otherwise
        """
        self._current_segment_briefs.append(brief)

        # Track defeated entities
        if getattr(brief, 'target_defeated', False):
            target = getattr(brief, 'target_name', '')
            if target:
                self._all_defeated.add(target)

        # Check if we hit a segment boundary
        if len(self._current_segment_briefs) >= SEGMENT_SIZE:
            return self._close_segment(turn_number)

        return None

    def force_segment(self, turn_number: int, reason: str = "") -> Optional[SessionSegmentSummary]:
        """Force a segment summary (scene transition, combat end).

        Args:
            turn_number: Current turn number
            reason: Why the segment was forced

        Returns:
            SessionSegmentSummary if there are briefs to summarize
        """
        if not self._current_segment_briefs:
            return None

        if reason:
            logger.info(f"Forced segment summary at turn {turn_number}: {reason}")

        return self._close_segment(turn_number)

    def get_summaries(self) -> List[SessionSegmentSummary]:
        """Get all generated summaries (newest first for retrieval).

        Returns:
            List of SessionSegmentSummary ordered newest-first
        """
        return list(reversed(self._summaries))

    def get_all_defeated(self) -> FrozenSet[str]:
        """Get cumulative set of all defeated entities.

        Returns:
            Frozen set of defeated entity names
        """
        return frozenset(self._all_defeated)

    def check_drift(self) -> Optional[DriftResult]:
        """Check for drift between the two most recent segments.

        Returns:
            DriftResult if drift detected, None if no drift or <2 segments
        """
        if len(self._summaries) < 2:
            return None

        earlier = self._summaries[-2]
        later = self._summaries[-1]
        result = self._summarizer.detect_drift(earlier, later)

        if result.has_drift:
            logger.warning(
                f"Drift detected between segments {earlier.segment_id} "
                f"and {later.segment_id}: {result.details}"
            )

        return result if result.has_drift else None

    def _close_segment(self, end_turn: int) -> SessionSegmentSummary:
        """Close current segment and generate summary.

        Args:
            end_turn: Last turn in this segment

        Returns:
            Generated SessionSegmentSummary
        """
        self._segment_counter += 1
        segment_id = f"seg_{self._segment_counter:03d}"
        turn_range = (self._segment_start_turn, end_turn)

        summary = self._summarizer.summarize(
            briefs=self._current_segment_briefs,
            segment_id=segment_id,
            turn_range=turn_range,
        )

        self._summaries.append(summary)
        self._current_segment_briefs = []
        self._segment_start_turn = end_turn + 1

        logger.info(
            f"Segment {segment_id} closed (turns {turn_range[0]}-{turn_range[1]}): "
            f"{summary.summary_text[:80]}..."
        )

        return summary
