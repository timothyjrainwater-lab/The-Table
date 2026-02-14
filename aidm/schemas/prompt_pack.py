"""PromptPack v1 Schema for WO-045B (AD-002, GAP-002).

Implements the five-channel wire protocol between Lens and Spark.
This is the canonical schema that replaces monolithic string assembly
in ContextAssembler with a structured, versioned, deterministic payload.

CHANNELS (AD-002):
1. Truth    — Hard constraints: what Spark MUST NOT contradict
2. Memory   — Retrieved facts scoped to THIS turn, truncation-safe
3. Task     — What Spark is doing + per-task output schema
4. Style    — Persona + tone knobs, stable across session
5. Contract — Machine-checkable output constraints

NON-NEGOTIABLE PROPERTIES:
- Deterministic: same inputs → same serialized bytes
- Versioned: schema_version field in every PromptPack
- Sectioned: channels are explicit, not interleaved
- Budgeted: each channel has token allocation
- Truncation-safe: Truth/Task/Style/Contract NEVER truncated; Memory truncated FIRST

CITATIONS:
- AD-002: Lens Context Orchestration (five-channel spec)
- RWO-005 SEAM_PROTOCOL_ANALYSIS GAP-002: No canonical PromptPack schema
"""

import json
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from aidm.schemas.presentation_semantics import AbilityPresentationEntry


# =============================================================================
# SCHEMA VERSION
# =============================================================================

PROMPT_PACK_SCHEMA_VERSION = "1.0"


# =============================================================================
# TASK TYPES
# =============================================================================

# Task type constants — defines what Spark is doing
TASK_NARRATION = "narration"           # Describe what happened (2-4 sentences)
TASK_NPC_DIALOGUE = "npc_dialogue"     # Generate in-character NPC speech
TASK_SCENE_BEATS = "scene_beats"       # Propose narrative beats (v2)
TASK_SESSION_SUMMARY = "session_summary"  # Compress events (v2)

# Valid v1 task types
V1_TASK_TYPES = {TASK_NARRATION, TASK_NPC_DIALOGUE}


# =============================================================================
# CHANNEL DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class TruthChannel:
    """Hard constraints that Spark MUST NOT contradict.

    Sourced from NarrativeBrief (Box→Lens one-way valve).
    Never truncated.
    """
    action_type: str                         # narration token (e.g., "attack_hit")
    actor_name: str                          # Display name, NOT entity ID
    target_name: Optional[str] = None        # Display name, NOT entity ID
    outcome_summary: str = ""                # Natural language outcome
    severity: str = "minor"                  # minor/moderate/severe/devastating/lethal
    weapon_name: Optional[str] = None        # Weapon name string
    damage_type: Optional[str] = None        # e.g., "slashing", "fire"
    condition_applied: Optional[str] = None  # e.g., "prone", "stunned"
    condition_removed: Optional[str] = None  # e.g., "prone" (WO-BRIEF-WIDTH-001 bug fix)
    target_defeated: bool = False            # Whether target was defeated
    # Multi-target (WO-BRIEF-WIDTH-001)
    additional_targets: Optional[List[dict]] = None  # [{name, severity, defeated}, ...]
    # Causal chain (WO-BRIEF-WIDTH-001)
    causal_chain_id: Optional[str] = None
    chain_position: int = 0                  # 0=standalone, 1=first, 2+=continuation
    # Condition stack (WO-BRIEF-WIDTH-001)
    active_conditions: Optional[List[str]] = None   # All conditions currently on target
    actor_conditions: Optional[List[str]] = None    # Conditions on actor affecting this action
    scene_description: Optional[str] = None  # Brief location context
    visible_gear: Optional[List[str]] = None  # AD-005 Layer 3: externally visible gear
    # AD-007 Layer B: presentation semantics (WO-GAP-B-001)
    delivery_mode: Optional[str] = None      # e.g., "projectile", "beam", "burst_from_point"
    staging: Optional[str] = None            # e.g., "travel_then_detonate", "instant"
    origin_rule: Optional[str] = None        # e.g., "from_caster", "from_chosen_point"
    scale: Optional[str] = None              # e.g., "subtle", "moderate", "dramatic"
    vfx_tags: Optional[List[str]] = None     # e.g., ["fire", "explosion"]
    sfx_tags: Optional[List[str]] = None     # e.g., ["impact", "sizzle"]
    residue: Optional[List[str]] = None      # Lingering visual effects
    contraindications: Optional[List[str]] = None  # What Spark must NOT narrate


@dataclass(frozen=True)
class MemoryChannel:
    """Retrieved facts scoped to this turn.

    Truncated FIRST when budget is tight. Entries are ordered by
    relevance (most relevant first), so truncation removes from end.
    """
    previous_narrations: tuple = ()  # Last N narration texts for continuity
    session_facts: tuple = ()        # Relevant session facts (quest state, NPC attitudes)
    segment_summaries: tuple = ()    # WO-060: Session segment summary texts (newest first)
    token_budget: int = 200          # Max tokens for this channel


@dataclass(frozen=True)
class TaskChannel:
    """Defines what Spark is doing for this invocation.

    Never truncated. One task type per PromptPack.
    """
    task_type: str = TASK_NARRATION  # One of V1_TASK_TYPES
    output_max_sentences: int = 4    # Max sentences in output
    output_min_sentences: int = 2    # Min sentences in output
    forbidden_content: tuple = (     # Content Spark MUST NOT include
        "damage numbers",
        "AC values",
        "attack bonus values",
        "HP values",
        "die roll results",
        "rule citations",
    )
    # For NPC dialogue
    npc_name: Optional[str] = None      # NPC speaking (for npc_dialogue task)
    npc_personality: Optional[str] = None  # Brief personality descriptor


@dataclass(frozen=True)
class StyleChannel:
    """Persona and tone parameters.

    Never truncated. Must be stable across a session.
    Parameters are bounded knobs, not open-ended instructions.
    """
    verbosity: str = "moderate"   # terse / moderate / verbose
    drama: str = "dramatic"       # understated / dramatic / epic
    humor: str = "none"           # none / dry / wry / comedic
    grittiness: str = "moderate"  # clean / moderate / gritty
    dm_persona: str = "authoritative"  # authoritative / friendly / menacing
    # NPC voice identity (for npc_dialogue tasks)
    npc_voice_id: Optional[str] = None  # Maps to TTS persona if available


@dataclass(frozen=True)
class OutputContract:
    """Machine-checkable output constraints.

    Never truncated. Defines what the output MUST look like
    for automated validation (GrammarShield, kill switches).
    """
    max_length_chars: int = 600     # Max output characters
    required_provenance: str = "[NARRATIVE]"  # Provenance tag
    json_mode: bool = False          # Whether output must be valid JSON
    json_schema: Optional[str] = None  # If json_mode, the expected schema


# =============================================================================
# PROMPTPACK (TOP-LEVEL)
# =============================================================================

@dataclass(frozen=True)
class PromptPack:
    """Five-channel wire protocol payload from Lens to Spark (AD-002).

    This is the canonical schema that crosses the Lens→Spark seam.
    Every field is immutable. Serialization is deterministic.

    Usage:
        pack = PromptPack(
            truth=TruthChannel(action_type="attack_hit", actor_name="Kael", ...),
            memory=MemoryChannel(previous_narrations=("Kael charged forward.",)),
            task=TaskChannel(task_type=TASK_NARRATION),
            style=StyleChannel(verbosity="moderate", drama="dramatic"),
            contract=OutputContract(max_length_chars=600),
        )

        # Deterministic serialization
        prompt_text = pack.serialize()

        # Build SparkRequest
        request = SparkRequest(prompt=prompt_text, temperature=0.7, max_tokens=200)
    """
    schema_version: str = PROMPT_PACK_SCHEMA_VERSION
    truth: TruthChannel = field(default_factory=TruthChannel)
    memory: MemoryChannel = field(default_factory=MemoryChannel)
    task: TaskChannel = field(default_factory=TaskChannel)
    style: StyleChannel = field(default_factory=StyleChannel)
    contract: OutputContract = field(default_factory=OutputContract)

    def __post_init__(self):
        """Validate PromptPack constraints."""
        if self.task.task_type not in V1_TASK_TYPES:
            raise ValueError(
                f"Unknown task type: {self.task.task_type}. "
                f"Valid v1 types: {V1_TASK_TYPES}"
            )

    def serialize(self) -> str:
        """Serialize to deterministic prompt text.

        AD-002 requirement: same inputs → same bytes.
        Channels are explicitly sectioned with markers.

        Returns:
            Deterministic prompt string for SparkRequest.prompt.
        """
        sections = []

        # === SYSTEM PREAMBLE ===
        sections.append(f"[PROMPT_PACK v{self.schema_version}]")
        sections.append("")

        # === TRUTH CHANNEL ===
        sections.append("[TRUTH]")
        sections.append(f"Action: {self.truth.action_type}")
        sections.append(f"Actor: {self.truth.actor_name}")
        if self.truth.target_name:
            sections.append(f"Target: {self.truth.target_name}")
        if self.truth.outcome_summary:
            sections.append(f"Outcome: {self.truth.outcome_summary}")
        sections.append(f"Severity: {self.truth.severity}")
        if self.truth.weapon_name:
            sections.append(f"Weapon: {self.truth.weapon_name}")
        if self.truth.damage_type:
            sections.append(f"Damage Type: {self.truth.damage_type}")
        if self.truth.condition_applied:
            sections.append(f"Condition Applied: {self.truth.condition_applied}")
        if self.truth.condition_removed:
            sections.append(f"Condition Removed: {self.truth.condition_removed}")
        if self.truth.target_defeated:
            sections.append("Target Defeated: yes")
        # WO-BRIEF-WIDTH-001: Multi-target, causal chain, condition stack
        if self.truth.additional_targets:
            target_strs = []
            for t in self.truth.additional_targets:
                defeated_tag = " (defeated)" if t.get("defeated") else ""
                target_strs.append(f"{t['name']} [{t['severity']}]{defeated_tag}")
            sections.append(f"Additional Targets: {'; '.join(target_strs)}")
        if self.truth.causal_chain_id:
            sections.append(f"Causal Chain: {self.truth.causal_chain_id} (position {self.truth.chain_position})")
        if self.truth.active_conditions:
            sections.append(f"Target Conditions: {', '.join(sorted(self.truth.active_conditions))}")
        if self.truth.actor_conditions:
            sections.append(f"Actor Conditions: {', '.join(sorted(self.truth.actor_conditions))}")
        if self.truth.scene_description:
            sections.append(f"Scene: {self.truth.scene_description}")
        if self.truth.visible_gear:
            sections.append(f"Visible Gear: {', '.join(sorted(self.truth.visible_gear))}")
        # AD-007 Layer B presentation semantics
        if self.truth.delivery_mode:
            sections.append(f"Delivery Mode: {self.truth.delivery_mode}")
        if self.truth.staging:
            sections.append(f"Staging: {self.truth.staging}")
        if self.truth.origin_rule:
            sections.append(f"Origin: {self.truth.origin_rule}")
        if self.truth.scale:
            sections.append(f"Scale: {self.truth.scale}")
        if self.truth.vfx_tags:
            sections.append(f"VFX: {', '.join(sorted(self.truth.vfx_tags))}")
        if self.truth.sfx_tags:
            sections.append(f"SFX: {', '.join(sorted(self.truth.sfx_tags))}")
        if self.truth.residue:
            sections.append(f"Residue: {', '.join(sorted(self.truth.residue))}")
        if self.truth.contraindications:
            sections.append(f"Contraindications: {', '.join(sorted(self.truth.contraindications))}")
        sections.append("[/TRUTH]")
        sections.append("")

        # === MEMORY CHANNEL ===
        sections.append("[MEMORY]")
        if self.memory.previous_narrations:
            sections.append("Previous:")
            for narr in self.memory.previous_narrations:
                sections.append(f"- {narr}")
        if self.memory.segment_summaries:
            sections.append("Session Context:")
            for summary in self.memory.segment_summaries:
                sections.append(f"- {summary}")
        if self.memory.session_facts:
            sections.append("Facts:")
            for fact in self.memory.session_facts:
                sections.append(f"- {fact}")
        if not self.memory.previous_narrations and not self.memory.session_facts and not self.memory.segment_summaries:
            sections.append("(none)")
        sections.append("[/MEMORY]")
        sections.append("")

        # === TASK CHANNEL ===
        sections.append("[TASK]")
        sections.append(f"Type: {self.task.task_type}")
        sections.append(f"Sentences: {self.task.output_min_sentences}-{self.task.output_max_sentences}")
        if self.task.task_type == TASK_NPC_DIALOGUE and self.task.npc_name:
            sections.append(f"NPC: {self.task.npc_name}")
            if self.task.npc_personality:
                sections.append(f"Personality: {self.task.npc_personality}")
        sections.append("Forbidden:")
        for item in self.task.forbidden_content:
            sections.append(f"- {item}")
        sections.append("[/TASK]")
        sections.append("")

        # === STYLE CHANNEL ===
        sections.append("[STYLE]")
        sections.append(f"Verbosity: {self.style.verbosity}")
        sections.append(f"Drama: {self.style.drama}")
        sections.append(f"Humor: {self.style.humor}")
        sections.append(f"Grittiness: {self.style.grittiness}")
        sections.append(f"Persona: {self.style.dm_persona}")
        if self.style.npc_voice_id:
            sections.append(f"Voice: {self.style.npc_voice_id}")
        sections.append("[/STYLE]")
        sections.append("")

        # === OUTPUT CONTRACT ===
        sections.append("[CONTRACT]")
        sections.append(f"Max Length: {self.contract.max_length_chars} chars")
        sections.append(f"Provenance: {self.contract.required_provenance}")
        if self.contract.json_mode:
            sections.append("Format: JSON")
            if self.contract.json_schema:
                sections.append(f"Schema: {self.contract.json_schema}")
        else:
            sections.append("Format: prose")
        sections.append("[/CONTRACT]")

        return "\n".join(sections)

    def to_dict(self) -> dict:
        """Serialize to deterministic JSON-compatible dict.

        Useful for logging, debugging, and golden test comparison.
        """
        return {
            "schema_version": self.schema_version,
            "truth": {
                "action_type": self.truth.action_type,
                "actor_name": self.truth.actor_name,
                "target_name": self.truth.target_name,
                "outcome_summary": self.truth.outcome_summary,
                "severity": self.truth.severity,
                "weapon_name": self.truth.weapon_name,
                "damage_type": self.truth.damage_type,
                "condition_applied": self.truth.condition_applied,
                "condition_removed": self.truth.condition_removed,
                "target_defeated": self.truth.target_defeated,
                "additional_targets": self.truth.additional_targets,
                "causal_chain_id": self.truth.causal_chain_id,
                "chain_position": self.truth.chain_position,
                "active_conditions": sorted(self.truth.active_conditions) if self.truth.active_conditions else None,
                "actor_conditions": sorted(self.truth.actor_conditions) if self.truth.actor_conditions else None,
                "scene_description": self.truth.scene_description,
                "visible_gear": sorted(self.truth.visible_gear) if self.truth.visible_gear else None,
                "delivery_mode": self.truth.delivery_mode,
                "staging": self.truth.staging,
                "origin_rule": self.truth.origin_rule,
                "scale": self.truth.scale,
                "vfx_tags": sorted(self.truth.vfx_tags) if self.truth.vfx_tags else None,
                "sfx_tags": sorted(self.truth.sfx_tags) if self.truth.sfx_tags else None,
                "residue": sorted(self.truth.residue) if self.truth.residue else None,
                "contraindications": sorted(self.truth.contraindications) if self.truth.contraindications else None,
            },
            "memory": {
                "previous_narrations": list(self.memory.previous_narrations),
                "session_facts": list(self.memory.session_facts),
                "segment_summaries": list(self.memory.segment_summaries),
                "token_budget": self.memory.token_budget,
            },
            "task": {
                "task_type": self.task.task_type,
                "output_min_sentences": self.task.output_min_sentences,
                "output_max_sentences": self.task.output_max_sentences,
                "forbidden_content": list(self.task.forbidden_content),
                "npc_name": self.task.npc_name,
                "npc_personality": self.task.npc_personality,
            },
            "style": {
                "verbosity": self.style.verbosity,
                "drama": self.style.drama,
                "humor": self.style.humor,
                "grittiness": self.style.grittiness,
                "dm_persona": self.style.dm_persona,
                "npc_voice_id": self.style.npc_voice_id,
            },
            "contract": {
                "max_length_chars": self.contract.max_length_chars,
                "required_provenance": self.contract.required_provenance,
                "json_mode": self.contract.json_mode,
                "json_schema": self.contract.json_schema,
            },
        }

    def to_json(self) -> str:
        """Deterministic JSON serialization.

        Uses sort_keys=True and consistent formatting for byte-level
        reproducibility.
        """
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=True)
