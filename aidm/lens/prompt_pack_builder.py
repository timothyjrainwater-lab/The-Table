"""WO-057: PromptPackBuilder — Single Prompt Assembly Path (GAP-007 Resolution).

Replaces both PATH 1 (GuardedNarrationService._build_llm_prompt) and
PATH 2 (ContextAssembler.assemble + DMPersona.build_system_prompt) with
a single PromptPack-based assembly.

INPUTS:
- NarrativeBrief (from WO-046B event→brief assembly)
- session_facts: List[str] (from FrozenMemorySnapshot)
- style_config: Optional[StyleChannel] (tone parameters, defaults to moderate)

OUTPUT:
- PromptPack (frozen, deterministic, five-channel)

ASSEMBLY LOGIC:
1. TruthChannel: Populated directly from NarrativeBrief fields
2. MemoryChannel: previous_narrations + session_facts, token budget enforced
3. TaskChannel: TASK_NARRATION, sentence bounds, forbidden mechanical content
4. StyleChannel: From style_config or defaults
5. OutputContract: max_length_chars, required_provenance, prose format

BOUNDARY LAW (BL-003): No imports from aidm.core.
This module lives in Lens. It imports from aidm.lens and aidm.schemas only.

CITATIONS:
- WO-057: PromptPack Consolidation (GAP-007 Resolution)
- AD-002: Lens Context Orchestration (five-channel spec)
- WO-045B: PromptPack v1 Schema
- WO-032: ContextAssembler (token budget logic reused)
"""

from typing import List, Optional

from aidm.lens.narrative_brief import NarrativeBrief
from aidm.schemas.prompt_pack import (
    PromptPack,
    TruthChannel,
    MemoryChannel,
    TaskChannel,
    StyleChannel,
    OutputContract,
    TASK_NARRATION,
)


class PromptPackBuilder:
    """Builds a PromptPack from a NarrativeBrief and session context.

    This is the single prompt assembly path for all LLM narration calls.
    It replaces both the ad-hoc string assembly in GuardedNarrationService
    and the ContextAssembler + DMPersona combination.

    The builder populates all five PromptPack channels from existing
    data sources, enforces token budget on the MemoryChannel, and
    returns a frozen, deterministic PromptPack.
    """

    def __init__(self, memory_token_budget: int = 200):
        """Initialize builder.

        Args:
            memory_token_budget: Max tokens for MemoryChannel.
                Truncation removes from end (least relevant first).
        """
        self.memory_token_budget = memory_token_budget

    def build(
        self,
        brief: NarrativeBrief,
        session_facts: Optional[List[str]] = None,
        segment_summaries: Optional[List[str]] = None,
        style: Optional[StyleChannel] = None,
        contract: Optional[OutputContract] = None,
    ) -> PromptPack:
        """Build PromptPack from NarrativeBrief and context.

        Args:
            brief: Current NarrativeBrief (from WO-046B event→brief)
            session_facts: Facts from FrozenMemorySnapshot (quest state, etc.)
            segment_summaries: WO-060 segment summary texts (newest first)
            style: Optional style override. Defaults to moderate/dramatic.
            contract: Optional contract override. Defaults to 600 chars, prose.

        Returns:
            Frozen, deterministic PromptPack with all five channels.
        """
        truth = self._build_truth(brief)
        memory = self._build_memory(brief, session_facts or [], segment_summaries or [])
        task = self._build_task()
        used_style = style if style is not None else StyleChannel()
        used_contract = contract if contract is not None else OutputContract()

        return PromptPack(
            truth=truth,
            memory=memory,
            task=task,
            style=used_style,
            contract=used_contract,
        )

    def _build_truth(self, brief: NarrativeBrief) -> TruthChannel:
        """Build TruthChannel from NarrativeBrief.

        Maps NarrativeBrief fields directly to TruthChannel fields.
        This is the one-way valve: NarrativeBrief carries only Spark-safe
        data, and TruthChannel is the hard constraint that Spark must
        not contradict.

        Args:
            brief: Current NarrativeBrief

        Returns:
            Frozen TruthChannel
        """
        return TruthChannel(
            action_type=brief.action_type,
            actor_name=brief.actor_name,
            target_name=brief.target_name,
            outcome_summary=brief.outcome_summary,
            severity=brief.severity,
            weapon_name=brief.weapon_name,
            damage_type=brief.damage_type,
            condition_applied=brief.condition_applied,
            target_defeated=brief.target_defeated,
            scene_description=brief.scene_description,
            visible_gear=brief.visible_gear,
        )

    def _build_memory(
        self,
        brief: NarrativeBrief,
        session_facts: List[str],
        segment_summaries: Optional[List[str]] = None,
    ) -> MemoryChannel:
        """Build MemoryChannel with token budget enforcement.

        previous_narrations come from NarrativeBrief.previous_narrations.
        segment_summaries come from SegmentTracker (WO-060, newest first).
        session_facts come from FrozenMemorySnapshot.

        All are truncated to fit within memory_token_budget.
        Truncation removes from end (least relevant entries dropped first).

        Priority order within budget:
        1. previous_narrations (most relevant for continuity)
        2. segment_summaries (session context)
        3. session_facts (quest state, NPC attitudes)

        Args:
            brief: Current NarrativeBrief (carries previous_narrations)
            session_facts: Session facts from memory snapshot
            segment_summaries: WO-060 segment summary texts (newest first)

        Returns:
            Frozen MemoryChannel within token budget
        """
        budget = self.memory_token_budget
        used = 0

        # previous_narrations: most relevant first, truncate from end
        truncated_narrations = []
        for narration in brief.previous_narrations:
            tokens = self._estimate_tokens(narration)
            if used + tokens > budget:
                break
            truncated_narrations.append(narration)
            used += tokens

        # segment_summaries: newest first, truncate from end (oldest dropped)
        truncated_summaries = []
        for summary in (segment_summaries or []):
            tokens = self._estimate_tokens(summary)
            if used + tokens > budget:
                break
            truncated_summaries.append(summary)
            used += tokens

        # session_facts: fill remaining budget
        truncated_facts = []
        for fact in session_facts:
            tokens = self._estimate_tokens(fact)
            if used + tokens > budget:
                break
            truncated_facts.append(fact)
            used += tokens

        return MemoryChannel(
            previous_narrations=tuple(truncated_narrations),
            session_facts=tuple(truncated_facts),
            segment_summaries=tuple(truncated_summaries),
            token_budget=self.memory_token_budget,
        )

    def _build_task(self) -> TaskChannel:
        """Build TaskChannel with narration defaults.

        Returns:
            Frozen TaskChannel for narration task
        """
        return TaskChannel(
            task_type=TASK_NARRATION,
            output_min_sentences=2,
            output_max_sentences=4,
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count for text.

        Reuses the same heuristic as ContextAssembler (WO-032):
        len(text.split()) * 1.3 — conservative overestimate.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return int(len(text.split()) * 1.3)
