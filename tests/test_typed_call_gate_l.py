"""Gate L tests — Typed Call Contract enforcement.

14 tests across 10 gate categories (L-01 through L-10).

Categories:
    L-01: Every CallType has all required fields (1 test)
    L-02: No two CallTypes share authority+purpose combination (1 test)
    L-03: Line type mapping is subset of Tier 1.1 (1 test)
    L-04: Every CallType has non-empty forbidden claims (1 test)
    L-05: Fallback templates pass GrammarShield (1 test)
    L-06: COMBAT_NARRATION forbidden claims reject mechanical values (1 test)
    L-07: OPERATOR_DIRECTIVE and CLARIFICATION_QUESTION integrate with Tier 1.2 (1 test)
    L-08: Invariants TC-INV-01 through TC-INV-04 are testable assertions (1 test)
    L-09: Authority levels are exhaustive and well-defined (1 test)
    L-10: Validation pipeline is ordered and stages are complete (1 test)

Authority: WO-VOICE-TYPED-CALL-SPEC-001, RQ-TYPEDCALL-001 (TYPED_CALL_CONTRACT.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import pytest


# ---------------------------------------------------------------------------
# CallType contract data — mirroring TYPED_CALL_CONTRACT.md
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CallTypeSpec:
    """Full specification for a single CallType."""
    name: str
    authority_level: str
    purpose: str
    temperature_min: float
    temperature_max: float
    latency_ceiling_s: int
    provenance_tag: str
    required_input_fields: tuple[str, ...]
    output_fields: tuple[str, ...]
    forbidden_claim_ids: tuple[str, ...]
    line_type_mapping: tuple[str, ...]
    fallback_template: str
    tier_1_2_integration: bool = False


# The six CallTypes as defined in the contract
CALL_TYPES: dict[str, CallTypeSpec] = {
    "COMBAT_NARRATION": CallTypeSpec(
        name="COMBAT_NARRATION",
        authority_level="ATMOSPHERIC",
        purpose="Flavor prose for resolved combat actions",
        temperature_min=0.7,
        temperature_max=1.0,
        latency_ceiling_s=8,
        provenance_tag="[NARRATIVE]",
        required_input_fields=(
            "truth.action_type", "truth.actor_name", "truth.outcome_summary",
            "truth.severity", "truth.target_defeated", "task.task_type",
            "contract.max_length_chars", "contract.required_provenance",
        ),
        output_fields=("text", "provenance"),
        forbidden_claim_ids=(
            "FC-CN-01", "FC-CN-02", "FC-CN-03", "FC-CN-04", "FC-CN-05",
            "FC-CN-06", "FC-CN-07", "FC-CN-08", "FC-CN-09", "FC-CN-10",
            "FC-CN-11", "FC-CN-12",
        ),
        line_type_mapping=("RESULT", "NARRATION"),
        fallback_template="NarrativeBrief fields formatted as prose.",
    ),
    "NPC_DIALOGUE": CallTypeSpec(
        name="NPC_DIALOGUE",
        authority_level="ATMOSPHERIC",
        purpose="In-character NPC speech during narration",
        temperature_min=0.7,
        temperature_max=1.1,
        latency_ceiling_s=6,
        provenance_tag="[NARRATIVE]",
        required_input_fields=(
            "truth.actor_name", "truth.scene_description", "task.task_type",
            "task.npc_name", "task.npc_personality", "task.dialogue_context",
            "contract.max_length_chars", "contract.required_provenance",
        ),
        output_fields=("dialogue", "provenance"),
        forbidden_claim_ids=(
            "FC-ND-01", "FC-ND-02", "FC-ND-03", "FC-ND-04", "FC-ND-05",
        ),
        line_type_mapping=("NARRATION", "RESULT"),
        fallback_template="The old merchant speaks.",
    ),
    "SUMMARY": CallTypeSpec(
        name="SUMMARY",
        authority_level="INFORMATIONAL",
        purpose="Compressing event history at segment boundaries",
        temperature_min=0.2,
        temperature_max=0.5,
        latency_ceiling_s=10,
        provenance_tag="[DERIVED]",
        required_input_fields=(
            "truth.scene_description", "memory.previous_narrations",
            "memory.session_facts", "task.task_type",
            "task.events_to_summarize", "contract.json_mode",
            "contract.json_schema", "contract.max_length_chars",
        ),
        output_fields=(
            "summary_text", "key_facts", "entities_involved",
            "unresolved_threads", "provenance",
        ),
        forbidden_claim_ids=(
            "FC-SU-01", "FC-SU-02", "FC-SU-03", "FC-SU-04", "FC-SU-05",
        ),
        line_type_mapping=("SYSTEM",),
        fallback_template="Chronological event list.",
    ),
    "RULE_EXPLAINER": CallTypeSpec(
        name="RULE_EXPLAINER",
        authority_level="NON-AUTHORITATIVE",
        purpose="Answering rules questions without adjudicating",
        temperature_min=0.3,
        temperature_max=0.6,
        latency_ceiling_s=8,
        provenance_tag="[DERIVED]",
        required_input_fields=(
            "task.task_type", "task.rule_topic",
            "contract.max_length_chars", "contract.required_provenance",
        ),
        output_fields=("explanation", "caveat", "provenance"),
        forbidden_claim_ids=(
            "FC-RE-01", "FC-RE-02", "FC-RE-03", "FC-RE-04",
        ),
        line_type_mapping=("RESULT",),
        fallback_template="Please consult the Player's Handbook.",
    ),
    "OPERATOR_DIRECTIVE": CallTypeSpec(
        name="OPERATOR_DIRECTIVE",
        authority_level="UNCERTAIN",
        purpose="Interpreting ambiguous operator input into candidate actions",
        temperature_min=0.3,
        temperature_max=0.6,
        latency_ceiling_s=6,
        provenance_tag="[UNCERTAIN]",
        required_input_fields=(
            "truth.scene_description", "truth.actor_name", "task.task_type",
            "task.operator_input", "task.valid_action_types",
            "contract.json_mode", "contract.json_schema",
        ),
        output_fields=(
            "candidates", "needs_clarification",
            "clarification_prompt", "provenance",
        ),
        forbidden_claim_ids=(
            "FC-OD-01", "FC-OD-02", "FC-OD-03", "FC-OD-04", "FC-OD-05",
        ),
        line_type_mapping=("PROMPT",),
        fallback_template="Keyword-only IntentBridge parsing.",
        tier_1_2_integration=True,
    ),
    "CLARIFICATION_QUESTION": CallTypeSpec(
        name="CLARIFICATION_QUESTION",
        authority_level="UNCERTAIN",
        purpose="Generating clarification prompts for missing or ambiguous info",
        temperature_min=0.2,
        temperature_max=0.4,
        latency_ceiling_s=4,
        provenance_tag="[UNCERTAIN]",
        required_input_fields=(
            "task.task_type", "task.ambiguity_type", "task.operator_input",
            "truth.actor_name", "contract.max_length_chars",
            "contract.required_provenance",
        ),
        output_fields=("question", "options", "provenance"),
        forbidden_claim_ids=(
            "FC-CQ-01", "FC-CQ-02", "FC-CQ-03", "FC-CQ-04",
        ),
        line_type_mapping=("PROMPT",),
        fallback_template="What would you like to do?",
        tier_1_2_integration=True,
    ),
}


# Authority level definitions from contract Section 1.1
AUTHORITY_LEVELS = {
    "ATMOSPHERIC": {
        "meaning": "Flavor text only; zero mechanical weight",
        "provenance_tag": "[NARRATIVE]",
    },
    "UNCERTAIN": {
        "meaning": "System is guessing/paraphrasing; operator must confirm",
        "provenance_tag": "[UNCERTAIN]",
    },
    "INFORMATIONAL": {
        "meaning": "Derived from Box state; not computed, not binding",
        "provenance_tag": "[DERIVED]",
    },
    "NON-AUTHORITATIVE": {
        "meaning": "Explains rules but does not adjudicate",
        "provenance_tag": "[DERIVED]",
    },
}

# Tier 1.1 line types (from CLI_GRAMMAR_CONTRACT.md)
TIER_1_1_LINE_TYPES = frozenset({
    "TURN", "RESULT", "ALERT", "NARRATION", "PROMPT", "SYSTEM", "DETAIL",
})

# Mechanical assertion patterns (from contract Section 3.1)
MECHANICAL_VALUE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("MV-01", re.compile(r"\b\d+\s*(points?\s+of\s+)?damage\b", re.IGNORECASE)),
    ("MV-02", re.compile(r"\bAC\s*\d+\b")),
    ("MV-03", re.compile(r"\b\d+\s*h(it\s*)?p(oints?)?\b", re.IGNORECASE)),
    ("MV-04", re.compile(r"[+-]\d+\s*(to\s+)?(attack|hit)\b", re.IGNORECASE)),
    ("MV-05", re.compile(r"\bDC\s*\d+\b")),
    ("MV-06", re.compile(r"\broll(ed)?\s+(a\s+)?\d+\b", re.IGNORECASE)),
    ("MV-07", re.compile(r"\b\d+d\d+")),
    ("MV-08", re.compile(
        r"\b\d+\s*(?:feet|ft\.?|squares?)\s+(?:of\s+)?(?:movement|range|reach)\b",
        re.IGNORECASE,
    )),
    ("MV-09", re.compile(r"\bnatural\s+\d+\b", re.IGNORECASE)),
]

# Rule citation patterns (from contract Section 3.2)
RULE_CITATION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("RC-01", re.compile(r"\b(PHB|DMG|MM)\s*\d+")),
    ("RC-02", re.compile(r"\b(page|pg\.?|p\.)\s*\d+\b", re.IGNORECASE)),
    ("RC-03", re.compile(r"\bper\s+the\s+\w+\s+rules\b", re.IGNORECASE)),
    ("RC-04", re.compile(r"\brules?\s+(as\s+written|state|say)\b", re.IGNORECASE)),
]

# Validation pipeline stages (from contract Section 4)
VALIDATION_PIPELINE_STAGES = [
    {"stage": 1, "name": "GrammarShield", "status": "active", "max_retries": 2},
    {"stage": 2, "name": "ForbiddenClaimChecker", "status": "active", "max_retries": 1},
    {"stage": 3, "name": "EvidenceValidator", "status": "reserved", "max_retries": 0},
]

# Tier 1.2 clarification budget (from UNKNOWN_HANDLING_CONTRACT.md Section 3.1)
MAX_CLARIFICATIONS = 2


# ---------------------------------------------------------------------------
# L-01: Every CallType has all required fields
# ---------------------------------------------------------------------------

class TestL01CallTypeCompleteness:
    """Every CallType has all required fields: input schema, output schema,
    forbidden claims, fallback template, latency ceiling."""

    def test_six_call_types_defined(self):
        assert len(CALL_TYPES) == 6

    def test_all_required_fields_present(self):
        required_attrs = [
            "name", "authority_level", "purpose", "temperature_min",
            "temperature_max", "latency_ceiling_s", "provenance_tag",
            "required_input_fields", "output_fields", "forbidden_claim_ids",
            "line_type_mapping", "fallback_template",
        ]
        for ct_name, spec in CALL_TYPES.items():
            for attr in required_attrs:
                val = getattr(spec, attr)
                assert val is not None, (
                    f"{ct_name} missing {attr}"
                )
                # Tuples must be non-empty
                if isinstance(val, tuple):
                    assert len(val) > 0, f"{ct_name}.{attr} is empty tuple"
                # Strings must be non-empty
                if isinstance(val, str):
                    assert len(val) > 0, f"{ct_name}.{attr} is empty string"

    def test_temperature_ranges_valid(self):
        for ct_name, spec in CALL_TYPES.items():
            assert spec.temperature_min < spec.temperature_max, (
                f"{ct_name}: temp_min ({spec.temperature_min}) >= temp_max ({spec.temperature_max})"
            )
            assert spec.temperature_min >= 0.0, f"{ct_name}: temp_min < 0"
            assert spec.temperature_max <= 2.0, f"{ct_name}: temp_max > 2.0"

    def test_latency_ceilings_positive(self):
        for ct_name, spec in CALL_TYPES.items():
            assert spec.latency_ceiling_s > 0, (
                f"{ct_name}: latency ceiling must be positive"
            )


# ---------------------------------------------------------------------------
# L-02: No two CallTypes share authority+purpose combination
# ---------------------------------------------------------------------------

class TestL02UniqueTyping:
    """No two CallTypes share the same authority level + purpose combination."""

    def test_unique_authority_purpose_pairs(self):
        seen: set[tuple[str, str]] = set()
        for ct_name, spec in CALL_TYPES.items():
            pair = (spec.authority_level, spec.purpose)
            assert pair not in seen, (
                f"Duplicate authority+purpose: {ct_name} shares "
                f"({spec.authority_level}, {spec.purpose}) with another type"
            )
            seen.add(pair)


# ---------------------------------------------------------------------------
# L-03: Line type mapping is subset of Tier 1.1
# ---------------------------------------------------------------------------

class TestL03LineTypeMapping:
    """Every CallType's line type mapping is a subset of Tier 1.1's seven types."""

    def test_all_mappings_are_valid_tier_1_1_types(self):
        for ct_name, spec in CALL_TYPES.items():
            for lt in spec.line_type_mapping:
                assert lt in TIER_1_1_LINE_TYPES, (
                    f"{ct_name} maps to '{lt}' which is not in Tier 1.1: "
                    f"{sorted(TIER_1_1_LINE_TYPES)}"
                )

    def test_no_call_type_produces_box_tagged_output(self):
        """No CallType may map to a line type that would carry [BOX] provenance.
        TURN and ALERT are Box-originated; CallTypes must not claim them."""
        box_adjacent_types = {"TURN", "ALERT"}
        for ct_name, spec in CALL_TYPES.items():
            for lt in spec.line_type_mapping:
                assert lt not in box_adjacent_types, (
                    f"{ct_name} maps to '{lt}' which is a Box-originated line type"
                )


# ---------------------------------------------------------------------------
# L-04: Every CallType has non-empty forbidden claims
# ---------------------------------------------------------------------------

class TestL04ForbiddenClaimsPresent:
    """Every CallType has a non-empty forbidden claims list."""

    def test_forbidden_claims_non_empty(self):
        for ct_name, spec in CALL_TYPES.items():
            assert len(spec.forbidden_claim_ids) > 0, (
                f"{ct_name} has zero forbidden claims"
            )

    def test_forbidden_claim_ids_are_well_formed(self):
        """Forbidden claim IDs follow FC-XX-NN pattern."""
        fc_pattern = re.compile(r"^FC-[A-Z]{2}-\d{2}$")
        for ct_name, spec in CALL_TYPES.items():
            for fc_id in spec.forbidden_claim_ids:
                assert fc_pattern.match(fc_id), (
                    f"{ct_name}: malformed forbidden claim ID '{fc_id}'"
                )


# ---------------------------------------------------------------------------
# L-05: Fallback templates pass GrammarShield
# ---------------------------------------------------------------------------

class TestL05FallbackTemplatesValid:
    """Every CallType's fallback template itself passes basic validation.

    Since fallback templates are short stubs, we verify they:
    1. Are non-empty strings
    2. Do not contain anti-patterns (AP-01 through AP-06)
    3. Do not contain mechanical assertion patterns
    """

    # Anti-pattern regexes from Tier 1.1
    _ap_patterns = [
        re.compile(r"^-{3,}|^={3,}"),
        re.compile(r"\(.*\)"),
        re.compile(r"\b(atk|dmg|hp|AC|DC|DR|SR|CL|BAB)\b"),
        re.compile(r"^[A-Z][A-Z ]{8,}[.!?]$"),
        re.compile(r"^\d+[.)]\s"),
        re.compile(
            "[\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\u2600-\u27BF]"
        ),
    ]

    def test_fallback_templates_non_empty(self):
        for ct_name, spec in CALL_TYPES.items():
            assert len(spec.fallback_template.strip()) > 0, (
                f"{ct_name} has empty fallback template"
            )

    def test_fallback_templates_no_anti_patterns(self):
        for ct_name, spec in CALL_TYPES.items():
            for ap in self._ap_patterns:
                assert not ap.search(spec.fallback_template), (
                    f"{ct_name} fallback triggers anti-pattern: "
                    f"{ap.pattern!r} on {spec.fallback_template!r}"
                )

    def test_fallback_templates_no_mechanical_values(self):
        for ct_name, spec in CALL_TYPES.items():
            for mv_id, mv_pattern in MECHANICAL_VALUE_PATTERNS:
                assert not mv_pattern.search(spec.fallback_template), (
                    f"{ct_name} fallback contains mechanical value {mv_id}: "
                    f"{spec.fallback_template!r}"
                )


# ---------------------------------------------------------------------------
# L-06: COMBAT_NARRATION forbidden claims reject mechanical values
# ---------------------------------------------------------------------------

class TestL06CombatNarrationMechanicalRejection:
    """Forbidden claims patterns for COMBAT_NARRATION reject strings containing
    mechanical values (AC, damage, HP, die rolls, dice notation, etc.)."""

    MECHANICAL_STRINGS = [
        "AC 18",
        "deals 14 damage",
        "rolled a 17",
        "2d6+3 slashing damage",
        "+7 to hit",
        "DC 15 Fortitude save",
        "24 HP remaining",
        "14 points of damage",
        "natural 20",
        "PHB 145",
        "30 feet of movement",
    ]

    CLEAN_STRINGS = [
        "The blade bites deep into the goblin's shoulder.",
        "A thunderous blow sends the creature reeling backward.",
        "The arrow whistles past, embedding itself in the wall behind.",
        "Steel meets steel with a resounding clash.",
        "The spell fizzles harmlessly against the ward.",
    ]

    def test_mechanical_strings_caught(self):
        """Every mechanical string triggers at least one forbidden pattern."""
        all_patterns = MECHANICAL_VALUE_PATTERNS + RULE_CITATION_PATTERNS
        for mech_str in self.MECHANICAL_STRINGS:
            caught = any(p.search(mech_str) for _, p in all_patterns)
            assert caught, (
                f"No pattern caught mechanical string: {mech_str!r}"
            )

    def test_clean_strings_pass(self):
        """Clean narration strings do not trigger forbidden patterns."""
        all_patterns = MECHANICAL_VALUE_PATTERNS + RULE_CITATION_PATTERNS
        for clean_str in self.CLEAN_STRINGS:
            violations = [
                pid for pid, p in all_patterns if p.search(clean_str)
            ]
            assert not violations, (
                f"False positive on clean string {clean_str!r}: {violations}"
            )


# ---------------------------------------------------------------------------
# L-07: OPERATOR_DIRECTIVE and CLARIFICATION_QUESTION integrate with Tier 1.2
# ---------------------------------------------------------------------------

class TestL07Tier12Integration:
    """OPERATOR_DIRECTIVE and CLARIFICATION_QUESTION map to Tier 1.2 escalation."""

    def test_operator_directive_has_tier_12_flag(self):
        assert CALL_TYPES["OPERATOR_DIRECTIVE"].tier_1_2_integration is True

    def test_clarification_question_has_tier_12_flag(self):
        assert CALL_TYPES["CLARIFICATION_QUESTION"].tier_1_2_integration is True

    def test_other_types_do_not_have_tier_12_flag(self):
        non_tier12 = {
            "COMBAT_NARRATION", "NPC_DIALOGUE", "SUMMARY", "RULE_EXPLAINER",
        }
        for ct_name in non_tier12:
            assert CALL_TYPES[ct_name].tier_1_2_integration is False, (
                f"{ct_name} should not have Tier 1.2 integration"
            )

    def test_clarification_budget_defined(self):
        """The clarification budget from Tier 1.2 is defined and positive."""
        assert MAX_CLARIFICATIONS >= 1
        assert MAX_CLARIFICATIONS <= 3  # contract range: 1-3

    def test_tier_12_types_map_to_prompt_line_type(self):
        """Both Tier 1.2 integrated types produce PROMPT line type output."""
        for ct_name in ("OPERATOR_DIRECTIVE", "CLARIFICATION_QUESTION"):
            assert "PROMPT" in CALL_TYPES[ct_name].line_type_mapping, (
                f"{ct_name} should map to PROMPT for Tier 1.2 integration"
            )


# ---------------------------------------------------------------------------
# L-08: Invariants TC-INV-01 through TC-INV-04
# ---------------------------------------------------------------------------

class TestL08Invariants:
    """Invariants TC-INV-01 through TC-INV-04 are testable assertions."""

    def test_inv_01_every_invocation_carries_one_call_type(self):
        """TC-INV-01: Every Spark invocation carries exactly one CallType.
        Verified structurally: CallType names are unique strings."""
        names = [spec.name for spec in CALL_TYPES.values()]
        assert len(names) == len(set(names)), "Duplicate CallType names"
        # Each name is a non-empty string
        for name in names:
            assert isinstance(name, str) and len(name) > 0

    def test_inv_02_no_call_type_asserts_mechanical_outcomes(self):
        """TC-INV-02: No CallType may assert mechanical outcomes.
        Verified: every CallType's authority level is NOT 'AUTHORITATIVE'
        and no CallType produces [BOX] provenance."""
        for ct_name, spec in CALL_TYPES.items():
            assert spec.authority_level in AUTHORITY_LEVELS, (
                f"{ct_name} has unknown authority level: {spec.authority_level}"
            )
            assert spec.provenance_tag != "[BOX]", (
                f"{ct_name} produces [BOX] provenance — mechanical authority violation"
            )

    def test_inv_03_fallback_exists_for_every_call_type(self):
        """TC-INV-03: Fallback template exists for every CallType."""
        for ct_name, spec in CALL_TYPES.items():
            assert spec.fallback_template is not None, (
                f"{ct_name} has no fallback template"
            )
            assert len(spec.fallback_template.strip()) > 0, (
                f"{ct_name} has empty fallback template"
            )

    def test_inv_04_pipeline_is_ordered_and_deterministic(self):
        """TC-INV-04: Validation pipeline is ordered and deterministic.
        Verified: stages are numbered sequentially with no gaps."""
        stage_numbers = [s["stage"] for s in VALIDATION_PIPELINE_STAGES]
        assert stage_numbers == [1, 2, 3], (
            f"Pipeline stages not sequential: {stage_numbers}"
        )
        # Active stages have defined retry budgets
        for stage in VALIDATION_PIPELINE_STAGES:
            if stage["status"] == "active":
                assert stage["max_retries"] >= 0
            elif stage["status"] == "reserved":
                assert stage["max_retries"] == 0


# ---------------------------------------------------------------------------
# L-09: Authority levels are exhaustive and well-defined
# ---------------------------------------------------------------------------

class TestL09AuthorityLevels:
    """Authority levels are exhaustive: every CallType uses a defined level."""

    def test_four_authority_levels_defined(self):
        assert len(AUTHORITY_LEVELS) == 4

    def test_every_call_type_uses_defined_authority(self):
        for ct_name, spec in CALL_TYPES.items():
            assert spec.authority_level in AUTHORITY_LEVELS, (
                f"{ct_name} uses undefined authority level: {spec.authority_level}"
            )

    def test_provenance_tags_match_authority(self):
        """Each CallType's provenance tag matches its authority level's tag."""
        for ct_name, spec in CALL_TYPES.items():
            expected_tag = AUTHORITY_LEVELS[spec.authority_level]["provenance_tag"]
            assert spec.provenance_tag == expected_tag, (
                f"{ct_name}: provenance tag '{spec.provenance_tag}' does not match "
                f"authority level '{spec.authority_level}' expected tag '{expected_tag}'"
            )

    def test_no_authority_level_is_authoritative(self):
        """No authority level grants mechanical authority (no 'AUTHORITATIVE' level)."""
        for level_name in AUTHORITY_LEVELS:
            assert level_name != "AUTHORITATIVE", (
                "AUTHORITATIVE level exists — violates Spark zero-authority rule"
            )


# ---------------------------------------------------------------------------
# L-10: Validation pipeline stages are complete
# ---------------------------------------------------------------------------

class TestL10ValidationPipeline:
    """Validation pipeline has 3 ordered stages (Stage 3 reserved)."""

    def test_three_stages_defined(self):
        assert len(VALIDATION_PIPELINE_STAGES) == 3

    def test_stage_1_is_grammar_shield(self):
        s1 = VALIDATION_PIPELINE_STAGES[0]
        assert s1["stage"] == 1
        assert s1["name"] == "GrammarShield"
        assert s1["status"] == "active"
        assert s1["max_retries"] == 2

    def test_stage_2_is_forbidden_claim_checker(self):
        s2 = VALIDATION_PIPELINE_STAGES[1]
        assert s2["stage"] == 2
        assert s2["name"] == "ForbiddenClaimChecker"
        assert s2["status"] == "active"
        assert s2["max_retries"] == 1

    def test_stage_3_is_reserved(self):
        s3 = VALIDATION_PIPELINE_STAGES[2]
        assert s3["stage"] == 3
        assert s3["name"] == "EvidenceValidator"
        assert s3["status"] == "reserved"
        assert s3["max_retries"] == 0

    def test_total_retry_budget(self):
        """Total worst-case retries: Stage 1 (2) + Stage 2 (1) = 3."""
        total = sum(
            s["max_retries"]
            for s in VALIDATION_PIPELINE_STAGES
            if s["status"] == "active"
        )
        assert total == 3, f"Total retry budget is {total}, expected 3"
