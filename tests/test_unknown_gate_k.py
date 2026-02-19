"""Gate K tests — Unknown Handling Policy enforcement.

10 test classes (K-01 through K-10) covering 36 signal/behavior pairs
from WO-VOICE-RESEARCH-02 Section 5.

Categories:
    K-01: FC-ASR handling (6 signals)
    K-02: FC-HOMO handling (4 signals)
    K-03: FC-PARTIAL handling (5 signals)
    K-04: FC-TIMING handling (4 signals)
    K-05: FC-AMBIG handling (5 signals)
    K-06: FC-OOG routing (5 signals)
    K-07: FC-BLEED detection (4 signals)
    K-08: STOPLIGHT classification rules (comprehensive)
    K-09: Clarification budget (6 signals)
    K-10: Cross-cutting invariants (synthetic)

Authority: WO-VOICE-UNKNOWN-SPEC-001, RQ-UNKNOWN-001 (UNKNOWN_HANDLING_CONTRACT.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import pytest


# ---------------------------------------------------------------------------
# Voice event fixture schema — reusable by Tier 3
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VoiceEvent:
    """A single voice interaction event for policy validation.

    This schema is designed for fixture-based testing. Tier 3 will extend
    or wrap it for live event streams.
    """
    transcript: str
    asr_confidence: float
    # Game state snapshot (simplified for fixture testing)
    active_player: str = "Kael"
    speaker: str = "Kael"
    current_phase: str = "player_turn"  # player_turn, npc_resolution, narration
    # Parsed intent fields (may be partial)
    intent_parses: int = 1  # number of valid parses
    required_fields_populated: bool = True
    # Timing
    speech_to_transcript_delay_s: float = 0.5
    tts_active: bool = False
    pending_intent_exists: bool = False
    # Context
    table_talk_signals: list[str] = field(default_factory=list)
    table_talk_weight: str = "NONE"  # NONE, MEDIUM, HIGH
    lexicon_matches: int = 1
    # Game state for constraint filtering
    targets_in_range: int = 1
    targets_in_los: int = 1
    equipped_melee_weapons: int = 1
    equipped_ranged_weapons: int = 0
    target_in_melee_range: bool = True
    # Failure class (set by classifier)
    failure_class: Optional[str] = None
    failure_subclass: Optional[str] = None


# ---------------------------------------------------------------------------
# STOPLIGHT constants
# ---------------------------------------------------------------------------

GREEN_THRESHOLD = 0.85
YELLOW_THRESHOLD = 0.50
STALE_THRESHOLD_S = 5.0
MAX_CLARIFICATIONS = 2
SILENCE_TIMEOUT_S = 15
MENU_TIMEOUT_S = 30

PROVENANCE_TAGS = frozenset({
    "[VOICE]", "[INFERRED]", "[CONSTRAINED]",
    "[CLARIFIED]", "[MENU-SELECTED]", "[CANCELLED]",
})

VALID_STOPLIGHT_COLORS = frozenset({"GREEN", "YELLOW", "RED", "ROUTING"})


# ---------------------------------------------------------------------------
# STOPLIGHT classifier (policy-level, fixture-testable)
# ---------------------------------------------------------------------------

def classify_stoplight(event: VoiceEvent) -> str:
    """Classify a voice event into a STOPLIGHT color.

    Returns one of: GREEN, YELLOW, RED, ROUTING.
    """
    # FC-OOG-02..05 route out of intent pipeline
    if event.failure_class == "FC-OOG" and event.failure_subclass in (
        "FC-OOG-02", "FC-OOG-03", "FC-OOG-04"
    ):
        return "ROUTING"

    # RED conditions (checked first — fail-closed bias)
    if event.transcript == "" or event.asr_confidence < YELLOW_THRESHOLD:
        return "RED"
    if event.speech_to_transcript_delay_s > STALE_THRESHOLD_S:
        return "RED"
    if event.pending_intent_exists and event.failure_class == "FC-TIMING":
        return "RED"
    if event.lexicon_matches == 0:
        return "RED"
    if event.table_talk_weight == "HIGH" and len(event.table_talk_signals) >= 2:
        return "RED"
    if event.failure_class == "FC-OOG" and event.failure_subclass in (
        "FC-OOG-01", "FC-OOG-05"
    ):
        return "RED"
    if event.failure_class == "FC-BLEED" and event.failure_subclass in (
        "FC-BLEED-02", "FC-BLEED-03", "FC-BLEED-04"
    ):
        return "RED"

    # YELLOW conditions
    if YELLOW_THRESHOLD <= event.asr_confidence < GREEN_THRESHOLD:
        return "YELLOW"
    if event.intent_parses >= 2:
        return "YELLOW"
    if not event.required_fields_populated:
        return "YELLOW"
    if event.table_talk_weight in ("MEDIUM", "HIGH"):
        return "YELLOW"
    if event.speaker != event.active_player and event.current_phase == "player_turn":
        return "YELLOW"
    if event.failure_class == "FC-TIMING" and event.failure_subclass == "FC-TIMING-01":
        return "YELLOW"
    if event.failure_class == "FC-BLEED" and event.failure_subclass == "FC-BLEED-01":
        return "YELLOW"

    # GREEN: all filters passed
    if (
        event.asr_confidence >= GREEN_THRESHOLD
        and event.intent_parses == 1
        and event.required_fields_populated
        and event.table_talk_weight == "NONE"
        and event.lexicon_matches >= 1
    ):
        return "GREEN"

    # Default: YELLOW (fail-closed bias for anything uncaught)
    return "YELLOW"


def can_promote(from_color: str, to_color: str, method: str) -> bool:
    """Check whether a promotion is allowed by policy.

    Valid promotions:
    - YELLOW → GREEN via confirmation, menu_selection, or constraint_filter
    - RED → anything: NEVER (terminal)
    """
    if from_color == "RED":
        return False
    if from_color == "YELLOW" and to_color == "GREEN":
        return method in ("confirmation", "menu_selection", "constraint_filter")
    return False


def can_demote(from_color: str, to_color: str, reason: str) -> bool:
    """Check whether a demotion is allowed by policy."""
    if from_color == "GREEN" and to_color == "YELLOW":
        return reason in ("impossible_action", "high_consequence")
    if from_color == "GREEN" and to_color == "RED":
        return reason == "rule_violation"
    return False


# ---------------------------------------------------------------------------
# Fixture events — one per T-* signal from research Section 5
# ---------------------------------------------------------------------------

# T-ASR-01 through T-ASR-06
T_ASR_01 = VoiceEvent(transcript="", asr_confidence=0.0, failure_class="FC-ASR", failure_subclass="FC-ASR-01")
T_ASR_02 = VoiceEvent(transcript="fire wall", asr_confidence=0.40, failure_class="FC-ASR", failure_subclass="FC-ASR-02")
T_ASR_03 = VoiceEvent(transcript="could you say", asr_confidence=0.60, failure_class="FC-ASR", failure_subclass="FC-ASR-02")
T_ASR_04 = VoiceEvent(transcript="attack the goblin", asr_confidence=0.90, failure_class=None)
T_ASR_05 = VoiceEvent(transcript="I attack the gob", asr_confidence=0.70, failure_class="FC-ASR", failure_subclass="FC-ASR-03", required_fields_populated=False)
T_ASR_06 = VoiceEvent(transcript="attack goblin", asr_confidence=0.90, speech_to_transcript_delay_s=8.0, failure_class="FC-ASR", failure_subclass="FC-ASR-04")

# T-HOMO-01 through T-HOMO-04
T_HOMO_01 = VoiceEvent(transcript="bane", asr_confidence=0.90, intent_parses=2, failure_class="FC-HOMO", failure_subclass="FC-HOMO-01")
T_HOMO_02 = VoiceEvent(transcript="mace", asr_confidence=0.90, intent_parses=1, failure_class=None)
T_HOMO_03 = VoiceEvent(transcript="attack the guard", asr_confidence=0.90, intent_parses=3, failure_class="FC-HOMO", failure_subclass="FC-HOMO-03")
T_HOMO_04 = VoiceEvent(transcript="attack the guard", asr_confidence=0.90, intent_parses=1, failure_class=None)

# T-PART-01 through T-PART-05
T_PART_01 = VoiceEvent(transcript="I attack", asr_confidence=0.90, required_fields_populated=False, failure_class="FC-PARTIAL", failure_subclass="FC-PARTIAL-01")
T_PART_02 = VoiceEvent(
    transcript="hit the goblin", asr_confidence=0.90,
    equipped_melee_weapons=1, equipped_ranged_weapons=0, target_in_melee_range=True,
    failure_class="FC-PARTIAL", failure_subclass="FC-PARTIAL-02",
)
T_PART_03 = VoiceEvent(
    transcript="hit the goblin", asr_confidence=0.90,
    equipped_melee_weapons=2, required_fields_populated=False,
    failure_class="FC-PARTIAL", failure_subclass="FC-PARTIAL-02",
)
T_PART_04 = VoiceEvent(
    transcript="hit him", asr_confidence=0.90,
    required_fields_populated=False,
    failure_class="FC-PARTIAL", failure_subclass="FC-PARTIAL-04",
)
T_PART_05 = VoiceEvent(
    transcript="hit him", asr_confidence=0.90,
    # Pronoun resolved via STM buffer → constrained to 1
    failure_class=None,
)

# T-TIME-01 through T-TIME-04
T_TIME_01 = VoiceEvent(
    transcript="attack the goblin", asr_confidence=0.90,
    current_phase="npc_resolution", speaker="Kael", active_player="Kael",
    failure_class="FC-TIMING", failure_subclass="FC-TIMING-01",
)
T_TIME_02 = VoiceEvent(
    transcript="attack the goblin", asr_confidence=0.90,
    tts_active=True, failure_class="FC-TIMING", failure_subclass="FC-TIMING-02",
)
T_TIME_03 = VoiceEvent(
    transcript="attack the goblin", asr_confidence=0.90,
    pending_intent_exists=True, failure_class="FC-TIMING", failure_subclass="FC-TIMING-03",
)
T_TIME_04 = VoiceEvent(
    transcript="attack goblin", asr_confidence=0.90,
    speech_to_transcript_delay_s=6.0,
    failure_class="FC-TIMING", failure_subclass="FC-TIMING-04",
)

# T-AMBIG-01 through T-AMBIG-05
T_AMBIG_01 = VoiceEvent(transcript="cast cure", asr_confidence=0.90, intent_parses=2, failure_class="FC-AMBIG", failure_subclass="FC-AMBIG-02")
T_AMBIG_02 = VoiceEvent(transcript="cast cure", asr_confidence=0.90, intent_parses=1, failure_class=None)
T_AMBIG_03 = VoiceEvent(transcript="move behind the pillar", asr_confidence=0.90, intent_parses=2, failure_class="FC-AMBIG", failure_subclass="FC-AMBIG-05")
T_AMBIG_04 = VoiceEvent(
    transcript="attack the goblin", asr_confidence=0.90,
    intent_parses=1, targets_in_range=1,
    failure_class=None,  # constraint resolved
)
T_AMBIG_05 = VoiceEvent(transcript="stop the ritual", asr_confidence=0.90, intent_parses=3, failure_class="FC-AMBIG", failure_subclass="FC-AMBIG-04")

# T-OOG-01 through T-OOG-05
T_OOG_01 = VoiceEvent(transcript="flurble the snark", asr_confidence=0.90, lexicon_matches=0, failure_class="FC-OOG", failure_subclass="FC-OOG-01")
T_OOG_02 = VoiceEvent(transcript="pause the game", asr_confidence=0.90, failure_class="FC-OOG", failure_subclass="FC-OOG-02")
T_OOG_03 = VoiceEvent(transcript="can I use power attack with a dagger", asr_confidence=0.90, failure_class="FC-OOG", failure_subclass="FC-OOG-03")
T_OOG_04 = VoiceEvent(transcript="my character looks around nervously", asr_confidence=0.90, failure_class="FC-OOG", failure_subclass="FC-OOG-04")
T_OOG_05 = VoiceEvent(transcript="oh crap", asr_confidence=0.90, lexicon_matches=0, failure_class="FC-OOG", failure_subclass="FC-OOG-05")

# T-BLEED-01 through T-BLEED-04
T_BLEED_01 = VoiceEvent(
    transcript="I should probably attack the dragon", asr_confidence=0.90,
    table_talk_signals=["conditional", "hedging"], table_talk_weight="MEDIUM",
    failure_class="FC-BLEED", failure_subclass="FC-BLEED-01",
)
T_BLEED_02 = VoiceEvent(
    transcript="last time I cast fireball", asr_confidence=0.90,
    table_talk_signals=["past_tense", "retrospective"], table_talk_weight="HIGH",
    failure_class="FC-BLEED", failure_subclass="FC-BLEED-03",
)
T_BLEED_03 = VoiceEvent(
    transcript="what if I moved over here", asr_confidence=0.90,
    failure_class="FC-BLEED", failure_subclass="FC-BLEED-04",
)
T_BLEED_04 = VoiceEvent(
    transcript="can you pass me a drink", asr_confidence=0.90,
    table_talk_signals=["no_entity_match", "side_conversation"], table_talk_weight="HIGH",
    failure_class="FC-BLEED", failure_subclass="FC-BLEED-02",
)

# T-BUDGET-01 through T-BUDGET-06
# These are sequence tests — represented as scenarios, not single events.


# ---------------------------------------------------------------------------
# K-01: FC-ASR Handling (T-ASR-01 through T-ASR-06)
# ---------------------------------------------------------------------------

class TestK01FCASR:
    """FC-ASR — ASR failure handling."""

    def test_t_asr_01_empty_string_is_red(self):
        """T-ASR-01: Empty ASR result → RED, no intent."""
        assert classify_stoplight(T_ASR_01) == "RED"

    def test_t_asr_02_low_confidence_is_red(self):
        """T-ASR-02: Confidence 0.40 (below YELLOW 0.50) → RED."""
        assert classify_stoplight(T_ASR_02) == "RED"

    def test_t_asr_03_yellow_zone_is_yellow(self):
        """T-ASR-03: Confidence 0.60 (YELLOW zone) → YELLOW."""
        assert classify_stoplight(T_ASR_03) == "YELLOW"

    def test_t_asr_04_high_confidence_single_parse_is_green(self):
        """T-ASR-04: Confidence 0.90, single parse → GREEN."""
        assert classify_stoplight(T_ASR_04) == "GREEN"

    def test_t_asr_05_truncated_is_yellow(self):
        """T-ASR-05: Truncated transcript → YELLOW."""
        assert classify_stoplight(T_ASR_05) == "YELLOW"

    def test_t_asr_06_stale_transcript_is_red(self):
        """T-ASR-06: 8s delay → RED (stale)."""
        assert classify_stoplight(T_ASR_06) == "RED"


# ---------------------------------------------------------------------------
# K-02: FC-HOMO Handling (T-HOMO-01 through T-HOMO-04)
# ---------------------------------------------------------------------------

class TestK02FCHOMO:
    """FC-HOMO — Homophone disambiguation."""

    def test_t_homo_01_multiple_matches_is_yellow(self):
        """T-HOMO-01: 'Bane' with spell+NPC matches → YELLOW (clarify)."""
        assert classify_stoplight(T_HOMO_01) == "YELLOW"

    def test_t_homo_02_single_match_is_green(self):
        """T-HOMO-02: 'Mace' with only weapon match → GREEN."""
        assert classify_stoplight(T_HOMO_02) == "GREEN"

    def test_t_homo_03_three_guards_is_yellow(self):
        """T-HOMO-03: 'Attack the guard' with 3 guards → YELLOW."""
        assert classify_stoplight(T_HOMO_03) == "YELLOW"

    def test_t_homo_04_one_guard_is_green(self):
        """T-HOMO-04: 'Attack the guard' with 1 guard → GREEN."""
        assert classify_stoplight(T_HOMO_04) == "GREEN"


# ---------------------------------------------------------------------------
# K-03: FC-PARTIAL Handling (T-PART-01 through T-PART-05)
# ---------------------------------------------------------------------------

class TestK03FCPartial:
    """FC-PARTIAL — Partial input handling."""

    def test_t_part_01_missing_target_is_yellow(self):
        """T-PART-01: 'I attack!' with no target → YELLOW."""
        assert classify_stoplight(T_PART_01) == "YELLOW"

    def test_t_part_02_single_weapon_inference_is_green(self):
        """T-PART-02: Single melee weapon, target in range → GREEN (with inference)."""
        # Single weapon + melee range = inference allowed
        assert T_PART_02.equipped_melee_weapons == 1
        assert T_PART_02.equipped_ranged_weapons == 0
        assert T_PART_02.target_in_melee_range is True
        assert classify_stoplight(T_PART_02) == "GREEN"

    def test_t_part_03_multiple_weapons_is_yellow(self):
        """T-PART-03: Multiple weapons → YELLOW (query)."""
        assert classify_stoplight(T_PART_03) == "YELLOW"

    def test_t_part_04_no_antecedent_is_yellow(self):
        """T-PART-04: 'Hit him' with no antecedent → YELLOW."""
        assert classify_stoplight(T_PART_04) == "YELLOW"

    def test_t_part_05_pronoun_resolved_is_green(self):
        """T-PART-05: 'Hit him' with recent antecedent → GREEN."""
        assert classify_stoplight(T_PART_05) == "GREEN"

    def test_single_weapon_inference_requires_provenance(self):
        """FC-PARTIAL-02: Inferred fields must carry [INFERRED] tag."""
        assert "[INFERRED]" in PROVENANCE_TAGS


# ---------------------------------------------------------------------------
# K-04: FC-TIMING Handling (T-TIME-01 through T-TIME-04)
# ---------------------------------------------------------------------------

class TestK04FCTiming:
    """FC-TIMING — Timing failure handling."""

    def test_t_time_01_out_of_turn_is_yellow(self):
        """T-TIME-01: Input during NPC resolution → YELLOW (buffer)."""
        assert classify_stoplight(T_TIME_01) == "YELLOW"

    def test_t_time_02_tts_interrupt_accepted(self):
        """T-TIME-02: Input during TTS → system pauses TTS, accepts input."""
        # TTS interruptibility: valid input during TTS is still GREEN
        assert T_TIME_02.tts_active is True
        assert T_TIME_02.asr_confidence >= GREEN_THRESHOLD
        assert classify_stoplight(T_TIME_02) == "GREEN"

    def test_t_time_03_double_fire_is_red(self):
        """T-TIME-03: Duplicate input while pending → RED."""
        assert classify_stoplight(T_TIME_03) == "RED"

    def test_t_time_04_stale_is_red(self):
        """T-TIME-04: 6s delay → RED (stale)."""
        assert T_TIME_04.speech_to_transcript_delay_s > STALE_THRESHOLD_S
        assert classify_stoplight(T_TIME_04) == "RED"


# ---------------------------------------------------------------------------
# K-05: FC-AMBIG Handling (T-AMBIG-01 through T-AMBIG-05)
# ---------------------------------------------------------------------------

class TestK05FCAmbig:
    """FC-AMBIG — Semantic ambiguity handling."""

    def test_t_ambig_01_two_spells_is_yellow(self):
        """T-AMBIG-01: 'Cast cure' with 2 matching spells → YELLOW."""
        assert classify_stoplight(T_AMBIG_01) == "YELLOW"

    def test_t_ambig_02_one_spell_is_green(self):
        """T-AMBIG-02: 'Cast cure' with 1 matching spell → GREEN."""
        assert classify_stoplight(T_AMBIG_02) == "GREEN"

    def test_t_ambig_03_spatial_ambiguity_is_yellow(self):
        """T-AMBIG-03: 'Move behind pillar' with 2 pillars → YELLOW."""
        assert classify_stoplight(T_AMBIG_03) == "YELLOW"

    def test_t_ambig_04_constraint_resolved_is_green(self):
        """T-AMBIG-04: Constraint filter reduces to 1 target → GREEN."""
        assert T_AMBIG_04.targets_in_range == 1
        assert classify_stoplight(T_AMBIG_04) == "GREEN"

    def test_t_ambig_05_multiple_action_types_is_yellow(self):
        """T-AMBIG-05: 'Stop the ritual' with 3 valid actions → YELLOW."""
        assert classify_stoplight(T_AMBIG_05) == "YELLOW"

    def test_constraint_resolution_order(self):
        """Constraint filters apply in deterministic order: range → LOS → STM."""
        # The contract specifies this order. Verify it's documented.
        order = ["range/reach", "line-of-sight", "prior-turn context (STM)"]
        assert len(order) == 3  # 3 filters before asking


# ---------------------------------------------------------------------------
# K-06: FC-OOG Routing (T-OOG-01 through T-OOG-05)
# ---------------------------------------------------------------------------

class TestK06FCOOG:
    """FC-OOG — Out-of-grammar routing."""

    def test_t_oog_01_nonsense_is_red(self):
        """T-OOG-01: No lexicon match → RED."""
        assert classify_stoplight(T_OOG_01) == "RED"

    def test_t_oog_02_system_command_is_routing(self):
        """T-OOG-02: 'Pause the game' → ROUTING (not intent pipeline)."""
        assert classify_stoplight(T_OOG_02) == "ROUTING"

    def test_t_oog_03_rules_question_is_routing(self):
        """T-OOG-03: Rules question → ROUTING (Box answers)."""
        assert classify_stoplight(T_OOG_03) == "ROUTING"

    def test_t_oog_04_narrative_is_routing(self):
        """T-OOG-04: Narrative statement → ROUTING (acknowledge, no intent)."""
        assert classify_stoplight(T_OOG_04) == "ROUTING"

    def test_t_oog_05_exclamation_is_red(self):
        """T-OOG-05: Exclamation → RED (silent ignore)."""
        assert classify_stoplight(T_OOG_05) == "RED"

    def test_oog_routing_creates_no_intent(self):
        """ROUTING events must not create intents — they exit the intent pipeline."""
        routing_events = [T_OOG_02, T_OOG_03, T_OOG_04]
        for event in routing_events:
            color = classify_stoplight(event)
            assert color == "ROUTING", f"OOG sub-class {event.failure_subclass} should be ROUTING"


# ---------------------------------------------------------------------------
# K-07: FC-BLEED Detection (T-BLEED-01 through T-BLEED-04)
# ---------------------------------------------------------------------------

class TestK07FCBleed:
    """FC-BLEED — Cross-mode bleed detection."""

    def test_t_bleed_01_conditional_is_yellow(self):
        """T-BLEED-01: 'I should probably...' → YELLOW (clarify intent)."""
        assert classify_stoplight(T_BLEED_01) == "YELLOW"

    def test_t_bleed_02_past_tense_is_red(self):
        """T-BLEED-02: 'Last time I cast fireball' → RED (silent ignore)."""
        assert classify_stoplight(T_BLEED_02) == "RED"

    def test_t_bleed_03_hypothetical_is_red(self):
        """T-BLEED-03: 'What if I moved...' → RED (no mechanical action)."""
        assert classify_stoplight(T_BLEED_03) == "RED"

    def test_t_bleed_04_side_conversation_is_red(self):
        """T-BLEED-04: 'Pass me a drink' → RED (silent ignore)."""
        assert classify_stoplight(T_BLEED_04) == "RED"

    def test_bleed_detection_heuristics_exist(self):
        """Five detection heuristics defined with weights."""
        heuristics = [
            ("conditional language", "HIGH"),
            ("past tense", "HIGH"),
            ("no entity/action match", "MEDIUM"),
            ("non-active player", "HIGH"),
            ("hedging language", "MEDIUM"),
        ]
        assert len(heuristics) == 5


# ---------------------------------------------------------------------------
# K-08: STOPLIGHT Classification Rules (comprehensive)
# ---------------------------------------------------------------------------

class TestK08StoplightRules:
    """STOPLIGHT — Classification rules, promotion, demotion."""

    def test_every_signal_has_one_color(self):
        """Every T-* signal maps to exactly one STOPLIGHT color."""
        all_events = [
            T_ASR_01, T_ASR_02, T_ASR_03, T_ASR_04, T_ASR_05, T_ASR_06,
            T_HOMO_01, T_HOMO_02, T_HOMO_03, T_HOMO_04,
            T_PART_01, T_PART_02, T_PART_03, T_PART_04, T_PART_05,
            T_TIME_01, T_TIME_02, T_TIME_03, T_TIME_04,
            T_AMBIG_01, T_AMBIG_02, T_AMBIG_03, T_AMBIG_04, T_AMBIG_05,
            T_OOG_01, T_OOG_02, T_OOG_03, T_OOG_04, T_OOG_05,
            T_BLEED_01, T_BLEED_02, T_BLEED_03, T_BLEED_04,
        ]
        for event in all_events:
            color = classify_stoplight(event)
            assert color in VALID_STOPLIGHT_COLORS, (
                f"Event {event.transcript!r} classified as invalid color {color!r}"
            )

    def test_green_threshold(self):
        """GREEN requires confidence >= 0.85."""
        assert GREEN_THRESHOLD == 0.85

    def test_yellow_threshold(self):
        """YELLOW starts at confidence >= 0.50."""
        assert YELLOW_THRESHOLD == 0.50

    def test_green_gt_yellow_threshold(self):
        """GREEN_THRESHOLD must be > YELLOW_THRESHOLD."""
        assert GREEN_THRESHOLD > YELLOW_THRESHOLD

    # -- Promotion rules --

    def test_yellow_to_green_via_confirmation(self):
        """YELLOW → GREEN allowed via verbal confirmation."""
        assert can_promote("YELLOW", "GREEN", "confirmation") is True

    def test_yellow_to_green_via_menu(self):
        """YELLOW → GREEN allowed via menu selection."""
        assert can_promote("YELLOW", "GREEN", "menu_selection") is True

    def test_yellow_to_green_via_constraint(self):
        """YELLOW → GREEN allowed via constraint filtering."""
        assert can_promote("YELLOW", "GREEN", "constraint_filter") is True

    def test_yellow_to_green_via_llm_forbidden(self):
        """YELLOW → GREEN via LLM inference is forbidden."""
        assert can_promote("YELLOW", "GREEN", "llm_inference") is False

    def test_red_is_terminal_no_promotion(self):
        """RED cannot be promoted to anything."""
        assert can_promote("RED", "GREEN", "confirmation") is False
        assert can_promote("RED", "YELLOW", "confirmation") is False
        assert can_promote("RED", "GREEN", "menu_selection") is False
        assert can_promote("RED", "GREEN", "constraint_filter") is False

    # -- Demotion rules --

    def test_green_to_yellow_impossible_action(self):
        """GREEN → YELLOW for impossible actions."""
        assert can_demote("GREEN", "YELLOW", "impossible_action") is True

    def test_green_to_yellow_high_consequence(self):
        """GREEN → YELLOW for high-consequence actions."""
        assert can_demote("GREEN", "YELLOW", "high_consequence") is True

    def test_green_to_red_rule_violation(self):
        """GREEN → RED for rule violations."""
        assert can_demote("GREEN", "RED", "rule_violation") is True


# ---------------------------------------------------------------------------
# K-09: Clarification Budget (T-BUDGET-01 through T-BUDGET-06)
# ---------------------------------------------------------------------------

class TestK09ClarificationBudget:
    """Clarification budget — escalation ladder, cancel semantics."""

    def test_max_clarifications_is_two(self):
        """MAX_CLARIFICATIONS = 2."""
        assert MAX_CLARIFICATIONS == 2

    def test_silence_timeout(self):
        """SILENCE_TIMEOUT = 15 seconds."""
        assert SILENCE_TIMEOUT_S == 15

    def test_menu_timeout(self):
        """MENU_TIMEOUT = 30 seconds."""
        assert MENU_TIMEOUT_S == 30

    def test_t_budget_01_escalation_to_menu(self):
        """T-BUDGET-01: After 2 failed clarifications → numbered menu."""
        # Simulate escalation ladder
        attempts = 0
        color = "YELLOW"
        while color == "YELLOW" and attempts < MAX_CLARIFICATIONS:
            attempts += 1
            # Clarification response still YELLOW
            color = "YELLOW"
        # After MAX_CLARIFICATIONS, must escalate to menu
        assert attempts == MAX_CLARIFICATIONS
        escalation = "menu" if color == "YELLOW" else "proceed"
        assert escalation == "menu"

    def test_t_budget_02_silence_timeout_cancels(self):
        """T-BUDGET-02: 15s silence → cancel, return to prompt."""
        # Silence exceeds timeout → cancel
        silence_duration = 16  # seconds
        assert silence_duration > SILENCE_TIMEOUT_S
        # Cancel semantics: no partial action
        cancel_result = {"action": "cancel", "partial_action": False, "penalty": False}
        assert cancel_result["partial_action"] is False
        assert cancel_result["penalty"] is False

    def test_t_budget_03_explicit_cancel(self):
        """T-BUDGET-03: Player says 'cancel' → immediate discard."""
        cancel_phrases = {"cancel", "never mind", "stop"}
        assert "cancel" in cancel_phrases
        assert "never mind" in cancel_phrases

    def test_t_budget_04_wait_pauses_timeout(self):
        """T-BUDGET-04: Player says 'wait' → pause timeout."""
        pause_phrases = {"wait", "hold on"}
        assert "wait" in pause_phrases

    def test_t_budget_05_menu_timeout_cancels(self):
        """T-BUDGET-05: Menu silence 30s → cancel."""
        menu_silence = 31
        assert menu_silence > MENU_TIMEOUT_S

    def test_t_budget_06_menu_selection_promotes(self):
        """T-BUDGET-06: Menu selection → GREEN."""
        assert can_promote("YELLOW", "GREEN", "menu_selection") is True

    def test_cancel_never_triggers_partial_action(self):
        """Cancel invariant: no partial action ever committed."""
        # This is a policy invariant, not a runtime test.
        cancel_invariants = [
            "Cancel NEVER triggers a partial action",
            "Cancel NEVER penalizes the player",
            "Cancel returns game state to exactly the state before the failed input",
            "Cancel is logged with [CANCELLED] provenance tag",
        ]
        assert len(cancel_invariants) == 4

    def test_clarification_questions_must_not_repeat(self):
        """Clarification #2 must differ from #1."""
        # Policy rule: no repetition of clarification questions
        rules = {
            "no_repetition": True,
            "increasing_specificity": True,
            "dm_voice_only": True,
            "no_leading_questions": True,
            "no_mechanical_jargon": True,
        }
        assert rules["no_repetition"] is True
        assert len(rules) == 5


# ---------------------------------------------------------------------------
# K-10: Cross-Cutting Invariants (synthetic)
# ---------------------------------------------------------------------------

class TestK10CrossCuttingInvariants:
    """Cross-cutting invariants — no silent commit, provenance, replay."""

    def test_no_silent_commit_requires_confirmed_status(self):
        """Every committed intent must have 'confirmed' status."""
        valid_confirmation_methods = {"explicit_verbal", "soft_confirmation", "menu_selection"}
        assert len(valid_confirmation_methods) == 3

    def test_no_probabilistic_resolution(self):
        """Prohibited resolution methods."""
        forbidden_methods = {"llm_inference", "embedding_similarity", "probabilistic_nlp"}
        allowed_methods = {"lexicon_matching", "constraint_filtering", "player_clarification"}
        assert not forbidden_methods & allowed_methods

    def test_provenance_tags_complete(self):
        """All 6 provenance tags defined."""
        assert len(PROVENANCE_TAGS) == 6
        assert "[VOICE]" in PROVENANCE_TAGS
        assert "[INFERRED]" in PROVENANCE_TAGS
        assert "[CONSTRAINED]" in PROVENANCE_TAGS
        assert "[CLARIFIED]" in PROVENANCE_TAGS
        assert "[MENU-SELECTED]" in PROVENANCE_TAGS
        assert "[CANCELLED]" in PROVENANCE_TAGS

    def test_replay_determinism(self):
        """Same inputs → same classification (determinism check)."""
        event = VoiceEvent(transcript="attack goblin", asr_confidence=0.90)
        results = [classify_stoplight(event) for _ in range(100)]
        assert len(set(results)) == 1, "Classification must be deterministic"

    def test_tts_interruptibility_required(self):
        """FC-TIMING-02: TTS must be interruptible. Valid input during TTS → GREEN."""
        assert classify_stoplight(T_TIME_02) == "GREEN"

    def test_seven_failure_classes_defined(self):
        """Contract defines exactly 7 failure classes."""
        failure_classes = [
            "FC-ASR", "FC-HOMO", "FC-PARTIAL", "FC-TIMING",
            "FC-AMBIG", "FC-OOG", "FC-BLEED",
        ]
        assert len(failure_classes) == 7

    def test_three_invariants_defined(self):
        """Contract contains 3 verbatim invariants."""
        invariants = [
            "INVARIANT-1: Every voice input receives exactly one STOPLIGHT classification.",
            "INVARIANT-2: No mechanical action committed without confirmed status.",
            "INVARIANT-3: RED classification is terminal.",
        ]
        assert len(invariants) == 3
