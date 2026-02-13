"""LLM Query Interface — Prompt templates and structured output enforcement.

Implements the query interface between AIDM and Qwen3 8B LLM for indexed
memory retrieval, narration generation, and structured output requests.

Based on design: docs/design/LLM_QUERY_INTERFACE.md

M3 Implementation:
- Prompt template structure (narration, query, structured output)
- System prompt architecture (world state, character context, constraints)
- Structured output enforcement (GBNF grammar, stop sequences, fallback parsing)
- Error handling (unparseable output, off-topic, constraint violations)

Reference: docs/design/LLM_QUERY_INTERFACE.md
Reference: docs/design/M1_LLM_SAFEGUARD_ARCHITECTURE.md (6 safeguards)
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

from aidm.schemas.campaign_memory import (
    SessionLedgerEntry,
    EvidenceLedger,
    ThreadRegistry,
    QueryResult,
)
from aidm.schemas.engine_result import EngineResult

logger = logging.getLogger(__name__)


# ========================================================================
# Prompt Templates
# ========================================================================


@dataclass
class PromptTemplate:
    """Base class for LLM prompt templates.

    Attributes:
        token_budget: Maximum tokens for this template type
    """

    token_budget: int


@dataclass
class NarrationTemplate(PromptTemplate):
    """Template for generating descriptive flavor text.

    Per LLM_QUERY_INTERFACE.md Section 1.1.
    Token Budget: ≤500 tokens total.
    """

    token_budget: int = 500


@dataclass
class QueryTemplate(PromptTemplate):
    """Template for indexed memory retrieval.

    Per LLM_QUERY_INTERFACE.md Section 1.2.
    Token Budget: ≤800 tokens total.
    """

    token_budget: int = 800


@dataclass
class StructuredOutputTemplate(PromptTemplate):
    """Template for structured data generation.

    Per LLM_QUERY_INTERFACE.md Section 1.3.
    Token Budget: ≤600 tokens total.
    """

    token_budget: int = 600


# ========================================================================
# System Prompt Components
# ========================================================================


@dataclass
class WorldStateSummary:
    """World state summary for LLM context.

    Per LLM_QUERY_INTERFACE.md Section 2.2.
    """

    active_npcs: List[str] = field(default_factory=list)
    """Active NPC summaries (name, species, HP, status)"""

    player_location: str = ""
    """Current scene name and type"""

    active_threads: List[str] = field(default_factory=list)
    """Active thread descriptions"""

    recent_events: List[str] = field(default_factory=list)
    """Recent event summaries (last 3-5 turns)"""

    def to_markdown(self) -> str:
        """Convert to markdown format for prompt."""
        parts = []

        if self.active_npcs:
            parts.append("Active NPCs:")
            for npc in self.active_npcs:
                parts.append(f"- {npc}")
            parts.append("")

        if self.player_location:
            parts.append(f"Location: {self.player_location}")
            parts.append("")

        if self.active_threads:
            parts.append("Active Threads:")
            for thread in self.active_threads:
                parts.append(f"- {thread}")
            parts.append("")

        if self.recent_events:
            parts.append("Recent Events:")
            for event in self.recent_events:
                parts.append(f"- {event}")
            parts.append("")

        return "\n".join(parts)


@dataclass
class CharacterContext:
    """Character context for LLM prompts.

    Per LLM_QUERY_INTERFACE.md Section 2.3.
    """

    pc_name: str = ""
    """Player character name"""

    pc_level: int = 1
    """Character level"""

    pc_class: str = ""
    """Character class"""

    hp_current: int = 0
    """Current HP"""

    hp_max: int = 0
    """Maximum HP"""

    status_effects: List[str] = field(default_factory=list)
    """Active status effects"""

    equipped_items: List[str] = field(default_factory=list)
    """Equipped weapon/armor"""

    def to_markdown(self) -> str:
        """Convert to markdown format for prompt."""
        if not self.pc_name:
            return ""

        parts = [
            f"Player Characters:",
            f"- {self.pc_name} (Level {self.pc_level} {self.pc_class})",
            f"  - HP: {self.hp_current}/{self.hp_max}",
        ]

        if self.status_effects:
            status_str = ", ".join(self.status_effects)
            parts.append(f"  - Status: {status_str}")

        if self.equipped_items:
            items_str = ", ".join(self.equipped_items)
            parts.append(f"  - Equipment: {items_str}")

        return "\n".join(parts)


# ========================================================================
# LLM Query Interface
# ========================================================================


class LLMQueryError(Exception):
    """Base exception for LLM query errors."""

    pass


class UnparseableOutputError(LLMQueryError):
    """Raised when LLM output cannot be parsed."""

    pass


class OffTopicError(LLMQueryError):
    """Raised when LLM output is off-topic or hallucinates."""

    pass


class ConstraintViolationError(LLMQueryError):
    """Raised when LLM output violates constraints."""

    pass


class LLMQueryInterface:
    """LLM Query Interface for narration and memory retrieval.

    Implements prompt templates, system prompt assembly, structured output
    enforcement, and error handling per LLM_QUERY_INTERFACE.md.

    Authority Boundary:
    - The engine DEFINES reality
    - The LLM DESCRIBES reality
    - LLM cannot invent abilities, assign stats, create entities, or contradict world state
    """

    # System prompt token budget per Section 2.5
    SYSTEM_PROMPT_TOKEN_BUDGET = 1000

    # Stop sequences for JSON output per Section 3.2
    JSON_STOP_SEQUENCES = ["}\n", "}\n\n"]

    # Retry budget per Section 5.4
    MAX_RETRIES = 2
    GPU_TIMEOUT_SECONDS = 5
    CPU_TIMEOUT_SECONDS = 10

    def __init__(self, loaded_model: Optional[Any] = None):
        """Initialize LLM query interface.

        Args:
            loaded_model: Optional LoadedModel from Spark Adapter for LLM operations.
                         If None, all operations fallback to templates/errors.
        """
        self.loaded_model = loaded_model
        self.metrics = {
            "unparseable_output": 0,
            "off_topic": 0,
            "constraint_violations": 0,
            "retries": 0,
            "fallbacks": 0,
        }

        if loaded_model is not None:
            logger.info(f"LLMQueryInterface initialized with model: {loaded_model.model_id}")
        else:
            logger.info("LLMQueryInterface initialized without model (template fallback mode)")

    def generate_narration(
        self,
        player_action: str,
        world_state_summary: WorldStateSummary,
        character_context: Optional[CharacterContext] = None,
        temperature: float = 0.8,
        narration_type: str = "combat",
    ) -> str:
        """Generate LLM narration for player action.

        Per LLM_QUERY_INTERFACE.md Section 1.1 (Narration Template).

        Args:
            player_action: Player action to narrate
            world_state_summary: Current world state
            character_context: Optional character context
            temperature: LLM temperature (must be ≥0.7 per LLM-002)
            narration_type: Type of narration (combat, exploration, social, environmental)

        Returns:
            Natural language narration (2-4 sentences)

        Raises:
            LLMQueryError: If LLM fails and no fallback available
        """
        # LLM-002: Narration temperature MUST be ≥0.7
        if temperature < 0.7:
            raise ValueError(
                f"Narration temperature MUST be ≥0.7 (got {temperature}). "
                "Violation: LLM-002 (Temperature Boundaries)"
            )

        if self.loaded_model is None:
            raise LLMQueryError("No LLM model loaded for narration generation")

        # Build prompt
        prompt = self._build_narration_prompt(
            player_action=player_action,
            world_state_summary=world_state_summary,
            character_context=character_context,
        )

        # Generate with retry logic
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                output = self._generate_text(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=150,
                    stop_sequences=[],
                )

                # Validate output (no constraint violations)
                self._validate_narration_output(output)

                return output.strip()

            except ConstraintViolationError as e:
                logger.warning(f"Narration constraint violation (attempt {attempt + 1}): {e}")
                self.metrics["constraint_violations"] += 1

                if attempt < self.MAX_RETRIES:
                    self.metrics["retries"] += 1
                    # Add stricter constraint to prompt
                    prompt += "\n\nIMPORTANT: Do NOT assign HP, stats, or mechanics. Describe only what is visible."
                else:
                    self.metrics["fallbacks"] += 1
                    raise LLMQueryError(f"Narration failed after {self.MAX_RETRIES} retries: {e}")

            except Exception as e:
                logger.error(f"Narration generation failed (attempt {attempt + 1}): {e}")
                if attempt >= self.MAX_RETRIES:
                    self.metrics["fallbacks"] += 1
                    raise LLMQueryError(f"Narration failed after {self.MAX_RETRIES} retries: {e}")
                self.metrics["retries"] += 1

    def query_memory(
        self,
        natural_language_query: str,
        memory_snapshot: Dict[str, Any],
        temperature: float = 0.3,
    ) -> QueryResult:
        """Retrieve entity IDs, event IDs, or relationships from indexed memory.

        Per LLM_QUERY_INTERFACE.md Section 1.2 (Query Template).

        Args:
            natural_language_query: Query in natural language
            memory_snapshot: Frozen memory snapshot (session ledger, evidence, threads)
            temperature: LLM temperature (must be ≤0.5 per LLM-002)

        Returns:
            QueryResult with entity_ids, event_ids, summary

        Raises:
            LLMQueryError: If LLM fails and no fallback available
        """
        # LLM-002: Query temperature MUST be ≤0.5
        if temperature > 0.5:
            raise ValueError(
                f"Query temperature MUST be ≤0.5 (got {temperature}). "
                "Violation: LLM-002 (Temperature Boundaries)"
            )

        if self.loaded_model is None:
            raise LLMQueryError("No LLM model loaded for memory queries")

        # Build prompt
        prompt = self._build_query_prompt(
            query=natural_language_query,
            memory_snapshot=memory_snapshot,
        )

        # Generate with retry logic
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                output = self._generate_text(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=200,
                    stop_sequences=self.JSON_STOP_SEQUENCES,
                )

                # Parse JSON output
                result = self._parse_query_result(output)

                return result

            except UnparseableOutputError as e:
                logger.warning(f"Unparseable query output (attempt {attempt + 1}): {e}")
                self.metrics["unparseable_output"] += 1

                if attempt < self.MAX_RETRIES:
                    self.metrics["retries"] += 1
                    # Add emphasis on JSON output
                    if attempt == 0:
                        prompt += "\n\nOutput ONLY valid JSON matching schema, no other text."
                    else:
                        prompt += '\n\nExample: {"entity_ids": ["entity_1"], "event_ids": ["event_001"], "summary": "Brief summary"}'
                else:
                    self.metrics["fallbacks"] += 1
                    # Return empty result on failure
                    return QueryResult(entity_ids=[], event_ids=[], summary="Query failed: unparseable output")

            except Exception as e:
                logger.error(f"Query generation failed (attempt {attempt + 1}): {e}")
                if attempt >= self.MAX_RETRIES:
                    self.metrics["fallbacks"] += 1
                    return QueryResult(entity_ids=[], event_ids=[], summary=f"Query failed: {str(e)}")
                self.metrics["retries"] += 1

    def generate_structured_output(
        self,
        request_description: str,
        json_schema: Dict[str, Any],
        temperature: float = 0.4,
    ) -> Dict[str, Any]:
        """Generate structured data (NPC stats, item properties) as JSON.

        Per LLM_QUERY_INTERFACE.md Section 1.3 (Structured Output Template).

        Args:
            request_description: Description of what to generate
            json_schema: JSON schema definition
            temperature: LLM temperature (≤0.5 for deterministic generation)

        Returns:
            Dictionary conforming to provided schema

        Raises:
            LLMQueryError: If LLM fails and no fallback available
        """
        if self.loaded_model is None:
            raise LLMQueryError("No LLM model loaded for structured output generation")

        # Build prompt
        prompt = self._build_structured_output_prompt(
            request_description=request_description,
            json_schema=json_schema,
        )

        # Generate with retry logic
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                output = self._generate_text(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=300,
                    stop_sequences=self.JSON_STOP_SEQUENCES,
                )

                # Parse JSON output
                result = json.loads(output.strip())

                return result

            except json.JSONDecodeError as e:
                logger.warning(f"Unparseable structured output (attempt {attempt + 1}): {e}")
                self.metrics["unparseable_output"] += 1

                if attempt < self.MAX_RETRIES:
                    self.metrics["retries"] += 1
                    # Add emphasis on JSON output
                    prompt += "\n\nOutput ONLY valid JSON matching the schema, no other text."
                else:
                    self.metrics["fallbacks"] += 1
                    raise UnparseableOutputError(f"Structured output failed after {self.MAX_RETRIES} retries")

            except Exception as e:
                logger.error(f"Structured output generation failed (attempt {attempt + 1}): {e}")
                if attempt >= self.MAX_RETRIES:
                    self.metrics["fallbacks"] += 1
                    raise LLMQueryError(f"Structured output failed after {self.MAX_RETRIES} retries: {e}")
                self.metrics["retries"] += 1

    # ── Prompt Building ─────────────────────────────────────────────────

    def _build_narration_prompt(
        self,
        player_action: str,
        world_state_summary: WorldStateSummary,
        character_context: Optional[CharacterContext] = None,
    ) -> str:
        """Build narration prompt per Section 1.1."""
        parts = []

        # System context
        parts.append("SYSTEM CONTEXT:")
        parts.append("You are the narrator for a D&D 3.5e campaign. Describe player actions with dramatic flair while respecting established world state.")
        parts.append("")

        # World state
        if world_state_summary:
            parts.append("WORLD STATE:")
            parts.append(world_state_summary.to_markdown())

        # Character context
        if character_context:
            parts.append(character_context.to_markdown())
            parts.append("")

        # Narration request
        parts.append("NARRATION REQUEST:")
        parts.append(f"Player action: {player_action}")
        parts.append("")
        parts.append("Generate 2-4 sentences of narration describing this action. Use fantasy genre tone. Do not invent abilities, stats, or mechanics. Describe only what is visible and dramatic.")

        return "\n".join(parts)

    def _build_query_prompt(
        self,
        query: str,
        memory_snapshot: Dict[str, Any],
    ) -> str:
        """Build query prompt per Section 1.2."""
        parts = []

        # System context
        parts.append("SYSTEM CONTEXT:")
        parts.append("You are a memory retrieval system for D&D campaign records. Extract facts only from indexed memory. Do not invent or infer.")
        parts.append("")

        # Indexed memory
        parts.append("INDEXED MEMORY:")
        parts.append(json.dumps(memory_snapshot, indent=2))
        parts.append("")

        # Query
        parts.append(f"QUERY: {query}")
        parts.append("")

        # Instructions
        parts.append("INSTRUCTIONS: Extract all relevant entries matching the query. Return ONLY valid JSON matching this schema:")
        parts.append('{')
        parts.append('  "entity_ids": ["entity_1", "entity_2"],')
        parts.append('  "event_ids": ["event_001", "event_005"],')
        parts.append('  "summary": "Brief summary of findings"')
        parts.append('}')
        parts.append("")
        parts.append("Output ONLY the JSON, no other text.")

        return "\n".join(parts)

    def _build_structured_output_prompt(
        self,
        request_description: str,
        json_schema: Dict[str, Any],
    ) -> str:
        """Build structured output prompt per Section 1.3."""
        parts = []

        # System context
        parts.append("SYSTEM CONTEXT:")
        parts.append("You generate D&D 3.5e data structures. Follow D&D 3.5e SRD rules exactly. Do not invent abilities.")
        parts.append("")

        # Generation request
        parts.append(f"GENERATION REQUEST: {request_description}")
        parts.append("")

        # Schema
        parts.append("SCHEMA:")
        parts.append(json.dumps(json_schema, indent=2))
        parts.append("")

        # Constraints
        parts.append("CONSTRAINTS:")
        parts.append("- All fields are required")
        parts.append("- Use D&D 3.5e rules only (no invented abilities)")
        parts.append("- Stay within provided stat ranges")
        parts.append("- Use standard D&D creature types")
        parts.append("")
        parts.append("Output ONLY valid JSON matching the schema, no other text.")

        return "\n".join(parts)

    # ── Text Generation ─────────────────────────────────────────────────

    def _generate_text(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stop_sequences: List[str],
    ) -> str:
        """Generate text using loaded LLM model.

        Args:
            prompt: Prompt text
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stop_sequences: Stop sequences

        Returns:
            Generated text

        Raises:
            RuntimeError: If no model loaded or generation fails
        """
        if self.loaded_model is None or self.loaded_model.inference_engine is None:
            raise RuntimeError("No LLM model loaded")

        output = self.loaded_model.inference_engine(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop_sequences,
            echo=False,
        )

        # Extract generated text
        if isinstance(output, dict) and 'choices' in output:
            text = output['choices'][0]['text']
        else:
            text = str(output)

        return text.strip()

    # ── Output Validation ───────────────────────────────────────────────

    def _validate_narration_output(self, output: str) -> None:
        """Validate narration output for constraint violations.

        Per LLM_QUERY_INTERFACE.md Section 5.3.

        Raises:
            ConstraintViolationError: If output violates constraints
        """
        # Check for HP value mentions
        if re.search(r'\b\d+\s*(hp|hit points)', output, re.I):
            raise ConstraintViolationError("Narration assigns HP values")

        # Check for ability score mentions
        if re.search(r'(strength|dexterity|constitution|intelligence|wisdom|charisma)\s*:\s*\d+', output, re.I):
            raise ConstraintViolationError("Narration assigns ability scores")

        # Check for stat assignments
        if re.search(r'(AC|attack bonus|saving throw)\s*:\s*\d+', output, re.I):
            raise ConstraintViolationError("Narration assigns stats")

    def _parse_query_result(self, output: str) -> QueryResult:
        """Parse query result from JSON output.

        Per LLM_QUERY_INTERFACE.md Section 3.3 (Fallback Parsing Logic).

        Args:
            output: LLM output (should be JSON)

        Returns:
            QueryResult

        Raises:
            UnparseableOutputError: If output cannot be parsed
        """
        try:
            # Try standard JSON parsing first
            data = json.loads(output.strip())

            # Validate required fields
            if "entity_ids" not in data:
                data["entity_ids"] = []
            if "event_ids" not in data:
                data["event_ids"] = []
            if "summary" not in data:
                data["summary"] = ""

            return QueryResult.from_dict(data)

        except json.JSONDecodeError:
            # Fallback: Try to extract JSON from output
            match = re.search(r'\{[^}]+\}', output, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                    return QueryResult.from_dict(data)
                except json.JSONDecodeError:
                    pass

            raise UnparseableOutputError(f"Cannot parse query result: {output[:100]}")

    def get_metrics(self) -> Dict[str, int]:
        """Get current LLM query metrics."""
        return self.metrics.copy()
