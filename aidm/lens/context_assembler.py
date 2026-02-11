"""WO-032: Context Assembler — Token-Budget-Aware Context Window Builder

The Context Assembler builds minimum-necessary context for Spark narration calls.
It enforces token budget limits and prioritizes the most relevant information.

PRIORITY ORDER (highest first):
1. Current NarrativeBrief (always included, ~100 tokens)
2. Scene description (if available, ~50 tokens)
3. Most recent narration texts (for continuity, ~200 tokens)
4. Session history summaries (if budget allows)

TOKEN ESTIMATION:
- Uses rough heuristic: len(text.split()) * 1.3
- No tokenizer dependency required (conservative estimate)

BOUNDARY LAW (BL-003): No imports from aidm.core.
AXIOM 3: Lens adapts stance — we present information, not compute mechanics.

Reference: docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md (WO-032)
"""

from typing import List, Optional

from aidm.lens.narrative_brief import NarrativeBrief


class ContextAssembler:
    """Assembles token-budget-aware context for Spark narration calls.

    Implements WO-032 context assembly with token budget enforcement.
    """

    def __init__(self, token_budget: int = 800):
        """Initialize context assembler.

        Args:
            token_budget: Maximum tokens for input context (not output)
        """
        self.token_budget = token_budget

    def assemble(
        self,
        brief: NarrativeBrief,
        session_history: Optional[List[NarrativeBrief]] = None,
    ) -> str:
        """Build context string within token budget.

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
        if brief.scene_description:
            scene_text = f"Location: {brief.scene_description}"
            scene_tokens = self._estimate_tokens(scene_text)

            if total_tokens + scene_tokens <= self.token_budget:
                context_parts.insert(0, scene_text)  # Add before brief
                total_tokens += scene_tokens

        # Priority 3: Recent narrations (for continuity)
        if brief.previous_narrations:
            recent_text, recent_tokens = self._format_recent_narrations(
                brief.previous_narrations,
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

    def _format_brief(self, brief: NarrativeBrief) -> str:
        """Format NarrativeBrief as context text.

        Args:
            brief: NarrativeBrief to format

        Returns:
            Formatted text
        """
        parts = [f"Current Action: {brief.outcome_summary}"]

        if brief.weapon_name:
            parts.append(f"Weapon: {brief.weapon_name}")

        if brief.damage_type:
            parts.append(f"Damage Type: {brief.damage_type}")

        if brief.condition_applied:
            parts.append(f"Condition Applied: {brief.condition_applied}")

        if brief.target_defeated:
            parts.append("Target Defeated: Yes")

        parts.append(f"Severity: {brief.severity}")

        return " | ".join(parts)

    def _format_recent_narrations(
        self,
        narrations: List[str],
        budget_remaining: int,
    ) -> tuple[str, int]:
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
        history: List[NarrativeBrief],
        budget_remaining: int,
    ) -> tuple[str, int]:
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
            summary = f"{brief.actor_name}: {brief.action_type}"
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

    def _estimate_tokens(self, text: str) -> int:
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
