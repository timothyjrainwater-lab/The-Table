"""WO-032/WO-059: Context Assembler — Token-Budget-Aware Retrieval Policy

The Context Assembler builds minimum-necessary context for Spark narration calls.
It enforces token budget limits and prioritizes the most relevant information.

WO-059 ADDITIONS (RQ-LENS-SPARK-001 Deliverable 2):
- RetrievedItem provenance tracking (source, turn_number, relevance_score)
- Salience ranking: recency * 0.5 + actor_match * 0.3 + severity_weight * 0.2
- Hard caps: 3 narrations, 5 session summaries
- Formalized drop order: summaries first (oldest), narrations (oldest), scene

PRIORITY ORDER (highest first):
1. Current NarrativeBrief (always included, ~100 tokens)
2. Scene description (if available, ~50 tokens)
3. Most recent narration texts (for continuity, ~200 tokens, max 3)
4. Session segment summaries (if budget allows, max 5)

TOKEN ESTIMATION:
- Uses rough heuristic: len(text.split()) * 1.3
- No tokenizer dependency required (conservative estimate)

BOUNDARY LAW (BL-003): No imports from aidm.core.
AXIOM 3: Lens adapts stance — we present information, not compute mechanics.

CITATIONS:
- RQ-LENS-SPARK-001: Context Orchestration Sprint (Deliverable 2)
- WO-032: ContextAssembler (original)
- WO-059: Memory Retrieval Policy

Reference: docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md (WO-032)
"""

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple


# ==============================================================================
# RETRIEVED ITEM (WO-059 Provenance Tracking)
# ==============================================================================


@dataclass(frozen=True)
class RetrievedItem:
    """A single item retrieved for Spark context, with provenance.

    Every piece of context fed to Spark carries metadata about where it
    came from, when it was generated, and how relevant it is to the
    current turn. This enables debugging, truncation auditing, and
    future retrieval policy tuning.

    Attributes:
        text: The context text
        source: Origin type — "narration", "session_summary", "scene", "brief"
        turn_number: Turn when this was generated (0 for scene/brief)
        relevance_score: 0.0-1.0 from ranking function
        dropped: True if cut by truncation
        drop_reason: "budget_exceeded", "cap_exceeded", or ""
    """
    text: str
    source: str
    turn_number: int
    relevance_score: float
    dropped: bool = False
    drop_reason: str = ""


# ==============================================================================
# SALIENCE RANKING (WO-059)
# ==============================================================================


# Severity weight mapping for ranking
_SEVERITY_WEIGHTS = {
    "lethal": 1.0,
    "devastating": 0.8,
    "severe": 0.6,
    "moderate": 0.4,
    "minor": 0.2,
}

# Hard caps (RQ-LENS-SPARK-001 Deliverable 2)
MAX_RECENT_NARRATIONS = 3
MAX_SESSION_SUMMARIES = 5


def compute_relevance_score(
    recency_rank: int,
    total_items: int,
    actor_match: bool,
    severity: str,
) -> float:
    """Compute salience score for a retrieved item.

    Formula: recency_weight * 0.5 + actor_match * 0.3 + severity_weight * 0.2

    This is a deterministic heuristic, not ML. Same inputs produce same score.

    Args:
        recency_rank: 0 = most recent, higher = older
        total_items: Total number of candidate items
        actor_match: Whether this item involves same actor/target as current brief
        severity: Severity level of the item's event

    Returns:
        Relevance score in [0.0, 1.0]
    """
    # Recency: 1.0 for most recent, decays linearly
    if total_items <= 1:
        recency_weight = 1.0
    else:
        recency_weight = 1.0 - (recency_rank / (total_items - 1))

    actor_weight = 1.0 if actor_match else 0.0
    severity_weight = _SEVERITY_WEIGHTS.get(severity, 0.2)

    return recency_weight * 0.5 + actor_weight * 0.3 + severity_weight * 0.2


# ==============================================================================
# CONTEXT ASSEMBLER
# ==============================================================================


class ContextAssembler:
    """Assembles token-budget-aware context for Spark narration calls.

    Implements WO-032 context assembly with WO-059 retrieval policy:
    - Salience ranking for narration ordering
    - RetrievedItem provenance on every context piece
    - Hard caps on narration and summary counts
    - Formalized drop order

    Usage:
        assembler = ContextAssembler(token_budget=800)

        # Basic assembly (backward compatible)
        context_text = assembler.assemble(brief, session_history)

        # Full retrieval with provenance (WO-059)
        items = assembler.retrieve(
            brief=brief,
            previous_narrations=narration_list,
            segment_summaries=summary_list,
            current_turn=42,
        )
    """

    def __init__(self, token_budget: int = 800):
        """Initialize context assembler.

        Args:
            token_budget: Maximum tokens for input context (not output)
        """
        self.token_budget = token_budget

    def assemble(
        self,
        brief: Any,  # NarrativeBrief
        session_history: Optional[List[Any]] = None,
    ) -> str:
        """Build context string within token budget.

        Backward-compatible API from WO-032. Uses the new retrieval policy
        internally but returns a plain string.

        Priority order (highest first):
        1. Current NarrativeBrief (always included, ~100 tokens)
        2. Scene description (if available, ~50 tokens)
        3. Most recent narration texts (for continuity, ~200 tokens)
        4. Session history summaries (if budget allows)

        Args:
            brief: Current NarrativeBrief to include
            session_history: Optional list of previous NarrativeBriefs

        Returns:
            Formatted context string for Spark prompt
        """
        context_parts = []
        total_tokens = 0

        # Priority 1: Current NarrativeBrief (always included)
        brief_text = self._format_brief(brief)
        brief_tokens = self._estimate_tokens(brief_text)
        context_parts.append(brief_text)
        total_tokens += brief_tokens

        # Priority 2: Scene description (if available)
        scene_description = getattr(brief, 'scene_description', None)
        if scene_description:
            scene_text = f"Location: {scene_description}"
            scene_tokens = self._estimate_tokens(scene_text)

            if total_tokens + scene_tokens <= self.token_budget:
                context_parts.insert(0, scene_text)  # Add before brief
                total_tokens += scene_tokens

        # Priority 3: Recent narrations (for continuity)
        previous_narrations = getattr(brief, 'previous_narrations', None)
        if previous_narrations:
            recent_text, recent_tokens = self._format_recent_narrations(
                previous_narrations,
                budget_remaining=self.token_budget - total_tokens,
            )

            if recent_text:
                context_parts.insert(0, recent_text)  # Add before scene/brief
                total_tokens += recent_tokens

        # Priority 4: Session history (if budget allows)
        if session_history and total_tokens < self.token_budget:
            history_text, history_tokens = self._format_session_history(
                session_history,
                budget_remaining=self.token_budget - total_tokens,
            )

            if history_text:
                context_parts.insert(0, history_text)  # Add at beginning
                total_tokens += history_tokens

        # Join all parts with double newline
        return "\n\n".join(context_parts)

    def retrieve(
        self,
        brief: Any,  # NarrativeBrief
        previous_narrations: Optional[List[Any]] = None,
        segment_summaries: Optional[List[Any]] = None,
        current_turn: int = 0,
    ) -> List[RetrievedItem]:
        """Retrieve context items with provenance tracking (WO-059).

        Returns a list of RetrievedItem objects, each with source, turn_number,
        relevance_score, and drop status. Items are ordered by priority:
        brief → scene → narrations (ranked) → summaries.

        Items that exceed the token budget or hard caps are included with
        dropped=True and a drop_reason.

        Args:
            brief: Current NarrativeBrief
            previous_narrations: List of dicts or objects with text, actor_name,
                target_name, severity, and turn_number fields
            segment_summaries: List of SessionSegmentSummary objects
            current_turn: Current turn number

        Returns:
            List of RetrievedItem with provenance metadata
        """
        items: List[RetrievedItem] = []
        budget_remaining = self.token_budget

        # --- Priority 1: Current brief (always included) ---
        brief_text = self._format_brief(brief)
        brief_tokens = self._estimate_tokens(brief_text)
        items.append(RetrievedItem(
            text=brief_text,
            source="brief",
            turn_number=current_turn,
            relevance_score=1.0,  # Current brief is always maximally relevant
        ))
        budget_remaining -= brief_tokens

        # --- Priority 2: Scene description ---
        scene_description = getattr(brief, 'scene_description', None)
        if scene_description:
            scene_text = f"Location: {scene_description}"
            scene_tokens = self._estimate_tokens(scene_text)
            if budget_remaining >= scene_tokens:
                items.append(RetrievedItem(
                    text=scene_text,
                    source="scene",
                    turn_number=0,
                    relevance_score=0.9,  # Scene is highly relevant
                ))
                budget_remaining -= scene_tokens
            else:
                items.append(RetrievedItem(
                    text=scene_text,
                    source="scene",
                    turn_number=0,
                    relevance_score=0.9,
                    dropped=True,
                    drop_reason="budget_exceeded",
                ))

        # --- Priority 3: Recent narrations (ranked, capped) ---
        if previous_narrations:
            brief_actor = getattr(brief, 'actor_name', '')
            brief_target = getattr(brief, 'target_name', '')

            # Score and rank narrations
            # Input list is oldest-first, so recency_rank is inverted:
            # last item (newest) gets rank 0, first item (oldest) gets rank N-1
            scored: List[Tuple[float, int, Any]] = []
            total = len(previous_narrations)
            for idx, narr in enumerate(previous_narrations):
                # Recency rank: invert index so last item = most recent = rank 0
                recency_rank = total - 1 - idx

                # Extract fields — support both dict and object
                if isinstance(narr, dict):
                    narr_actor = narr.get('actor_name', '')
                    narr_target = narr.get('target_name', '')
                    narr_severity = narr.get('severity', 'minor')
                    narr_turn = narr.get('turn_number', current_turn - total + idx)
                    narr_text = narr.get('text', str(narr))
                elif isinstance(narr, str):
                    # Plain string narration (backward compat)
                    narr_actor = ''
                    narr_target = ''
                    narr_severity = 'minor'
                    narr_turn = current_turn - total + idx
                    narr_text = narr
                else:
                    # Object with attributes
                    narr_actor = getattr(narr, 'actor_name', '')
                    narr_target = getattr(narr, 'target_name', '')
                    narr_severity = getattr(narr, 'severity', 'minor')
                    narr_turn = getattr(narr, 'turn_number', current_turn - total + idx)
                    narr_text = getattr(narr, 'text', str(narr))

                actor_match = (
                    (narr_actor and narr_actor == brief_actor) or
                    (narr_target and narr_target == brief_target) or
                    (narr_actor and narr_actor == brief_target) or
                    (narr_target and narr_target == brief_actor)
                )

                score = compute_relevance_score(
                    recency_rank=recency_rank,
                    total_items=total,
                    actor_match=actor_match,
                    severity=narr_severity,
                )

                scored.append((score, narr_turn, narr_text))

            # Sort by score descending (highest relevance first)
            scored.sort(key=lambda x: x[0], reverse=True)

            # Apply hard cap and budget
            for i, (score, turn, text) in enumerate(scored):
                tokens = self._estimate_tokens(text)

                if i >= MAX_RECENT_NARRATIONS:
                    items.append(RetrievedItem(
                        text=text,
                        source="narration",
                        turn_number=turn,
                        relevance_score=score,
                        dropped=True,
                        drop_reason="cap_exceeded",
                    ))
                elif budget_remaining < tokens:
                    items.append(RetrievedItem(
                        text=text,
                        source="narration",
                        turn_number=turn,
                        relevance_score=score,
                        dropped=True,
                        drop_reason="budget_exceeded",
                    ))
                else:
                    items.append(RetrievedItem(
                        text=text,
                        source="narration",
                        turn_number=turn,
                        relevance_score=score,
                    ))
                    budget_remaining -= tokens

        # --- Priority 4: Session segment summaries (capped) ---
        if segment_summaries:
            # Summaries ordered newest-first, drop oldest first
            for i, summary in enumerate(segment_summaries):
                if isinstance(summary, str):
                    summary_text = summary
                    summary_turn = 0
                else:
                    summary_text = getattr(summary, 'summary_text', str(summary))
                    turn_range = getattr(summary, 'turn_range', (0, 0))
                    summary_turn = turn_range[1] if isinstance(turn_range, tuple) else 0

                tokens = self._estimate_tokens(summary_text)

                if i >= MAX_SESSION_SUMMARIES:
                    items.append(RetrievedItem(
                        text=summary_text,
                        source="session_summary",
                        turn_number=summary_turn,
                        relevance_score=0.3,  # Summaries have baseline relevance
                        dropped=True,
                        drop_reason="cap_exceeded",
                    ))
                elif budget_remaining < tokens:
                    items.append(RetrievedItem(
                        text=summary_text,
                        source="session_summary",
                        turn_number=summary_turn,
                        relevance_score=0.3,
                        dropped=True,
                        drop_reason="budget_exceeded",
                    ))
                else:
                    items.append(RetrievedItem(
                        text=summary_text,
                        source="session_summary",
                        turn_number=summary_turn,
                        relevance_score=0.3,
                    ))
                    budget_remaining -= tokens

        return items

    def _format_brief(self, brief: Any) -> str:
        """Format NarrativeBrief as context text.

        Args:
            brief: NarrativeBrief to format

        Returns:
            Formatted text
        """
        outcome = getattr(brief, 'outcome_summary', '')
        parts = [f"Current Action: {outcome}"]

        weapon_name = getattr(brief, 'weapon_name', None)
        if weapon_name:
            parts.append(f"Weapon: {weapon_name}")

        damage_type = getattr(brief, 'damage_type', None)
        if damage_type:
            parts.append(f"Damage Type: {damage_type}")

        condition_applied = getattr(brief, 'condition_applied', None)
        if condition_applied:
            parts.append(f"Condition Applied: {condition_applied}")

        target_defeated = getattr(brief, 'target_defeated', False)
        if target_defeated:
            parts.append("Target Defeated: Yes")

        severity = getattr(brief, 'severity', 'minor')
        parts.append(f"Severity: {severity}")

        return " | ".join(parts)

    def _format_recent_narrations(
        self,
        narrations: List[str],
        budget_remaining: int,
    ) -> Tuple[str, int]:
        """Format recent narrations within budget.

        Args:
            narrations: List of narration texts (newest first)
            budget_remaining: Remaining token budget

        Returns:
            Tuple of (formatted_text, tokens_used)
        """
        if not narrations:
            return ("", 0)

        # Take most recent narrations that fit budget
        selected = []
        total_tokens = 0

        header = "Recent Events:"
        header_tokens = self._estimate_tokens(header)
        total_tokens += header_tokens

        for narration in reversed(narrations):  # Oldest to newest
            narration_tokens = self._estimate_tokens(narration)

            if total_tokens + narration_tokens > budget_remaining:
                break

            selected.append(narration)
            total_tokens += narration_tokens

        if not selected:
            return ("", 0)

        # Format with bullet points
        lines = [header]
        lines.extend(f"- {n}" for n in selected)

        return ("\n".join(lines), total_tokens)

    def _format_session_history(
        self,
        history: List[Any],
        budget_remaining: int,
    ) -> Tuple[str, int]:
        """Format session history within budget.

        Args:
            history: List of previous NarrativeBriefs
            budget_remaining: Remaining token budget

        Returns:
            Tuple of (formatted_text, tokens_used)
        """
        if not history:
            return ("", 0)

        header = "Session History:"
        header_tokens = self._estimate_tokens(header)
        total_tokens = header_tokens

        # Summarize each brief
        summaries = []
        for brief in reversed(history):  # Oldest to newest
            actor = getattr(brief, 'actor_name', 'Unknown')
            action = getattr(brief, 'action_type', 'unknown')
            summary = f"{actor}: {action}"
            summary_tokens = self._estimate_tokens(summary)

            if total_tokens + summary_tokens > budget_remaining:
                break

            summaries.append(summary)
            total_tokens += summary_tokens

        if not summaries:
            return ("", 0)

        lines = [header]
        lines.extend(f"- {s}" for s in summaries)

        return ("\n".join(lines), total_tokens)

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count for text.

        Uses rough heuristic: len(text.split()) * 1.3
        This is conservative (overestimates) to stay within budget.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        word_count = len(text.split())
        return int(word_count * 1.3)

    def compute_token_pressure(
        self,
        brief: Any,
        session_history: Optional[List[Any]] = None,
    ) -> Tuple[int, int]:
        """Compute token budget and required tokens for pressure evaluation.

        WO-VOICE-PRESSURE-IMPL-001: Returns (token_budget, token_required)
        so the caller can pass these to boundary pressure detection.
        Does NOT import from aidm.core (BL-003 compliant).

        Args:
            brief: Current NarrativeBrief
            session_history: Optional session history

        Returns:
            Tuple of (token_budget, token_required) where:
            - token_budget is the assembler's configured budget
            - token_required is the estimated tokens needed for all content
        """
        token_required = 0

        # Priority 1: brief (always required)
        brief_text = self._format_brief(brief)
        token_required += self._estimate_tokens(brief_text)

        # Priority 2: scene
        scene_description = getattr(brief, 'scene_description', None)
        if scene_description:
            token_required += self._estimate_tokens(f"Location: {scene_description}")

        # Priority 3: narrations
        previous_narrations = getattr(brief, 'previous_narrations', None)
        if previous_narrations:
            for narr in previous_narrations:
                text = narr if isinstance(narr, str) else getattr(narr, 'text', str(narr))
                token_required += self._estimate_tokens(text)

        # Priority 4: session history
        if session_history:
            for h in session_history:
                actor = getattr(h, 'actor_name', 'Unknown')
                action = getattr(h, 'action_type', 'unknown')
                token_required += self._estimate_tokens(f"{actor}: {action}")

        return (self.token_budget, token_required)
