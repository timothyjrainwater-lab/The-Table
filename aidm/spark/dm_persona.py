"""WO-041: DM Personality Layer — Consistent Voice for Spark Narration

The DM Persona layer provides consistent Dungeon Master voice through
system prompt engineering and tone control. It builds system prompts that
guide Spark narration style without affecting Box mechanical authority.

TONE CONTROL PARAMETERS:
- gravity: 0.0 (humorous) → 1.0 (serious), default 0.7
- verbosity: 0.0 (terse) → 1.0 (verbose), default 0.5
- drama: 0.0 (understated) → 1.0 (theatrical), default 0.6

NPC VOICE MAPPING:
- Maps NPC names to Kokoro TTS voice persona IDs
- Default "Dungeon Master" voice for narration
- Distinct voices for recurring NPCs
- Unknown NPCs fall back to default voice

SESSION MEMORY:
- Summarizes previous N narrations for continuity
- Respects ContextAssembler token budget
- Tracks recurring NPCs and their established characterization

BOUNDARY LAW (BL-003): No imports from aidm.core.
BOUNDARY LAW (BL-004): DM persona affects only Spark prompts, never Box mechanics.
AXIOM 3: Tone control is Lens layer stance adaptation, not mechanical authority.
PROVENANCE: All output tagged [NARRATIVE].

Reference: docs/planning/EXECUTION_PLAN_V2_POST_AUDIT.md (WO-041)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from aidm.lens.narrative_brief import NarrativeBrief


@dataclass(frozen=True)
class ToneConfig:
    """DM voice tone configuration.

    Controls narration style through system prompt engineering.
    Does NOT affect Box mechanical resolution.

    Attributes:
        gravity: 0.0 = humorous, 1.0 = serious (default 0.7)
        verbosity: 0.0 = terse, 1.0 = verbose (default 0.5)
        drama: 0.0 = understated, 1.0 = theatrical (default 0.6)
    """
    gravity: float = 0.7
    verbosity: float = 0.5
    drama: float = 0.6

    def __post_init__(self):
        """Validate tone parameters are in [0.0, 1.0] range."""
        if not (0.0 <= self.gravity <= 1.0):
            raise ValueError(f"gravity must be in [0.0, 1.0], got {self.gravity}")
        if not (0.0 <= self.verbosity <= 1.0):
            raise ValueError(f"verbosity must be in [0.0, 1.0], got {self.verbosity}")
        if not (0.0 <= self.drama <= 1.0):
            raise ValueError(f"drama must be in [0.0, 1.0], got {self.drama}")


@dataclass
class DMPersona:
    """DM personality layer for consistent Spark narration voice.

    Builds system prompts that guide narration style through tone parameters
    and NPC voice hints. All output tagged [NARRATIVE] provenance.

    Attributes:
        tone: ToneConfig controlling narration style
        npc_voices: Map of NPC name → Kokoro TTS voice persona ID
        default_voice: Default voice ID for narrator and unknown NPCs
        npc_characterization: Map of NPC name → established personality traits
    """
    tone: ToneConfig = field(default_factory=ToneConfig)
    npc_voices: Dict[str, str] = field(default_factory=dict)
    default_voice: str = "en_us_male_narrator"
    npc_characterization: Dict[str, List[str]] = field(default_factory=dict)

    def build_system_prompt(
        self,
        brief: NarrativeBrief,
        session_context: str = "",
    ) -> str:
        """Build system prompt for Spark narration generation.

        Constructs prompt with:
        - Base DM persona (authoritative, fair, D&D flavor)
        - Tone modifiers adjusting style (gravity/verbosity/drama)
        - NarrativeBrief context (action_type, severity, outcome_summary)
        - Session context from ContextAssembler (previous narrations)
        - NPC voice hints when NPC is speaking/acting

        BOUNDARY: NO mechanical data (entity IDs, HP, AC, etc.) in prompts.
        NarrativeBrief containment already enforces this.

        Args:
            brief: NarrativeBrief with Spark-safe context
            session_context: Previous narrations from ContextAssembler

        Returns:
            System prompt string for Spark generation
        """
        # Base DM persona
        base_persona = self._build_base_persona()

        # Apply tone modifiers
        tone_modifiers = self._build_tone_modifiers()

        # Extract action context from brief
        action_context = self._build_action_context(brief)

        # Add NPC voice hints if applicable
        npc_hints = self._build_npc_hints(brief)

        # Combine all parts
        prompt_parts = [
            base_persona,
            tone_modifiers,
            action_context,
        ]

        if session_context:
            prompt_parts.append(f"\n\nRECENT EVENTS:\n{session_context}")

        if npc_hints:
            prompt_parts.append(f"\n\nNPC CHARACTERIZATION:\n{npc_hints}")

        prompt_parts.append(
            "\n\nYour task: Narrate this action in 2-3 sentences. "
            "Focus on vivid description and character personality. "
            "Do NOT reveal mechanical details (damage numbers, HP, AC, attack bonuses)."
        )

        return "\n".join(prompt_parts)

    def get_npc_voice(self, npc_name: str) -> str:
        """Get Kokoro TTS voice persona ID for NPC.

        Returns distinct voice for recurring NPCs, falls back to default
        for unknown NPCs.

        Args:
            npc_name: NPC display name

        Returns:
            Kokoro voice persona ID
        """
        return self.npc_voices.get(npc_name, self.default_voice)

    def register_npc(
        self,
        npc_name: str,
        voice_id: str,
        personality_traits: Optional[List[str]] = None,
    ) -> None:
        """Register recurring NPC with voice and personality traits.

        Tracks NPC characterization for consistent narration across session.

        Args:
            npc_name: NPC display name
            voice_id: Kokoro TTS voice persona ID
            personality_traits: List of personality descriptors
        """
        self.npc_voices[npc_name] = voice_id
        if personality_traits:
            self.npc_characterization[npc_name] = personality_traits

    def _build_base_persona(self) -> str:
        """Build base DM persona prompt.

        Returns:
            Base persona string
        """
        return (
            "You are the Dungeon Master for a D&D 3.5e game. "
            "You are authoritative but fair, describing combat outcomes with "
            "vivid imagery and dramatic flair. Your narration brings the world "
            "to life while respecting the mechanical outcomes of the dice."
        )

    def _build_tone_modifiers(self) -> str:
        """Build tone modifier instructions based on ToneConfig.

        Returns:
            Tone modifier string
        """
        modifiers = []

        # Gravity modifier
        if self.tone.gravity < 0.3:
            modifiers.append(
                "Your tone is light and humorous, with occasional wit and wordplay."
            )
        elif self.tone.gravity < 0.6:
            modifiers.append(
                "Your tone balances drama with levity, keeping things engaging but not grim."
            )
        else:
            modifiers.append(
                "Your tone is serious and weighty, emphasizing the stakes and danger."
            )

        # Verbosity modifier
        if self.tone.verbosity < 0.3:
            modifiers.append(
                "Use concise, punchy sentences. Get to the point quickly."
            )
        elif self.tone.verbosity < 0.6:
            modifiers.append(
                "Use moderate detail, balancing clarity with atmosphere."
            )
        else:
            modifiers.append(
                "Use rich, descriptive language with layered sensory details."
            )

        # Drama modifier
        if self.tone.drama < 0.3:
            modifiers.append(
                "Keep descriptions understated and matter-of-fact."
            )
        elif self.tone.drama < 0.6:
            modifiers.append(
                "Add moderate dramatic emphasis to key moments."
            )
        else:
            modifiers.append(
                "Amplify drama with powerful verbs and vivid imagery. "
                "Make every action feel cinematic."
            )

        return "\n\n" + " ".join(modifiers)

    def _build_action_context(self, brief: NarrativeBrief) -> str:
        """Build action context from NarrativeBrief.

        Extracts Spark-safe mechanical context without revealing raw stats.

        Args:
            brief: NarrativeBrief to extract context from

        Returns:
            Action context string
        """
        context_parts = [
            f"\n\nACTION TYPE: {brief.action_type}",
            f"OUTCOME: {brief.outcome_summary}",
            f"SEVERITY: {brief.severity}",
        ]

        if brief.weapon_name:
            context_parts.append(f"WEAPON: {brief.weapon_name}")

        if brief.damage_type:
            context_parts.append(f"DAMAGE TYPE: {brief.damage_type}")

        if brief.condition_applied:
            context_parts.append(f"CONDITION: {brief.condition_applied}")

        if brief.target_defeated:
            context_parts.append("RESULT: Target defeated")

        if brief.scene_description:
            context_parts.append(f"LOCATION: {brief.scene_description}")

        return "\n".join(context_parts)

    def _build_npc_hints(self, brief: NarrativeBrief) -> str:
        """Build NPC characterization hints if applicable.

        Provides established personality traits for recurring NPCs.

        Args:
            brief: NarrativeBrief to check for NPC involvement

        Returns:
            NPC hints string, or empty if no known NPCs
        """
        hints = []

        # Check actor
        if brief.actor_name in self.npc_characterization:
            traits = ", ".join(self.npc_characterization[brief.actor_name])
            hints.append(f"{brief.actor_name}: {traits}")

        # Check target
        if brief.target_name and brief.target_name in self.npc_characterization:
            traits = ", ".join(self.npc_characterization[brief.target_name])
            hints.append(f"{brief.target_name}: {traits}")

        return "\n".join(hints) if hints else ""


# ══════════════════════════════════════════════════════════════════════════
# Preset DM Personas
# ══════════════════════════════════════════════════════════════════════════


def create_default_dm() -> DMPersona:
    """Create default DM persona with balanced tone.

    Returns:
        DMPersona with default ToneConfig
    """
    return DMPersona()


def create_gritty_dm() -> DMPersona:
    """Create gritty, serious DM persona.

    High gravity (serious), low drama (understated), medium verbosity.

    Returns:
        DMPersona with gritty ToneConfig
    """
    tone = ToneConfig(gravity=0.9, verbosity=0.5, drama=0.3)
    return DMPersona(tone=tone)


def create_theatrical_dm() -> DMPersona:
    """Create theatrical, dramatic DM persona.

    High drama, high verbosity, medium gravity.

    Returns:
        DMPersona with theatrical ToneConfig
    """
    tone = ToneConfig(gravity=0.6, verbosity=0.8, drama=0.9)
    return DMPersona(tone=tone)


def create_humorous_dm() -> DMPersona:
    """Create light-hearted, humorous DM persona.

    Low gravity (humorous), medium verbosity, medium drama.

    Returns:
        DMPersona with humorous ToneConfig
    """
    tone = ToneConfig(gravity=0.2, verbosity=0.5, drama=0.5)
    return DMPersona(tone=tone)


def create_terse_dm() -> DMPersona:
    """Create terse, efficient DM persona.

    Low verbosity, low drama, medium gravity.

    Returns:
        DMPersona with terse ToneConfig
    """
    tone = ToneConfig(gravity=0.6, verbosity=0.2, drama=0.3)
    return DMPersona(tone=tone)
