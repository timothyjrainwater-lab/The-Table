# Typed Call Contract v1
## Lens/Spark Invocation Boundary Specification

**Document ID:** RQ-TYPEDCALL-001
**Version:** 1.0
**Date:** 2026-02-21
**Status:** DRAFT — Awaiting PM Approval
**Authority:** This document is the canonical contract for Spark invocation typing. It governs which CallType every Spark invocation must carry, what each CallType is permitted to produce, what it is forbidden from asserting, and what replaces failed output.
**Scope:** CallType enum, per-type input/output schemas, forbidden claims, fallback templates, validation pipeline, and invariants. Invocation boundary spec only — no runtime implementation.

**References:**
- `docs/research/VOICE_CONTROL_PLANE_CONTRACT.md` — Voice control plane (Sections 2-3)
- `docs/research/RQ-SPRINT-004_SPARK_CONTAINMENT_AUDIT.md` — Containment mechanisms (Section 1.5)
- `docs/planning/research/RQ_LLM_TYPED_CALL_CONTRACT.md` — Typed call research (Sections 2-7)
- `docs/contracts/CLI_GRAMMAR_CONTRACT.md` (RQ-GRAMMAR-001) — Tier 1.1, line types and grammar rules
- `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md` (RQ-UNKNOWN-001) — Tier 1.2, failure classes and clarification budget
- `pm_inbox/reviewed/legacy_pm_inbox/research/VOICE_FIRST_RELIABILITY_PLAYBOOK.md` — Playbook (Sections 2, 4.3)

**Existing Implementation (this spec formalizes):**

| Layer | File | Status |
|-------|------|--------|
| Typed call research | `docs/planning/research/RQ_LLM_TYPED_CALL_CONTRACT.md` | Research complete |
| Containment audit | `docs/research/RQ-SPRINT-004_SPARK_CONTAINMENT_AUDIT.md` | Research complete |
| Typed call validator | `scripts/check_typed_call.py` | **New — created by this WO** |
| Gate tests | `tests/test_typed_call_gate_l.py` | **New — created by this WO** |

---

## Contract Summary (1-Page)

Every invocation of Spark (the LLM layer) carries exactly one CallType. The CallType mode-locks the invocation: it constrains what context Lens must provide, what Spark may return, what Spark is forbidden from asserting, and what template replaces failed output. Spark has ZERO mechanical authority. The CallType enforces this at the invocation boundary, before the LLM sees the prompt.

**Three-Layer Model:**

```
Lens Context Assembly  ->  CallType Tag  ->  Spark Generation  ->  Validation Pipeline
  (input schema)         (mode lock)        (constrained out)     (forbidden claims check)
```

The CallType tag is the single point of enforcement between Lens and Spark. Every field the LLM receives is gated by the CallType's input schema. Every field the LLM returns is validated against the CallType's output schema and forbidden claims.

**Invariants:**
1. **TC-INV-01:** Every Spark invocation carries exactly one CallType. No invocation is untyped.
2. **TC-INV-02:** No CallType may assert mechanical outcomes (AC, HP, damage values, save results, hit/miss determinations, die rolls, difficulty classes). Mechanical authority belongs exclusively to Box.
3. **TC-INV-03:** Every CallType has a fallback template that produces correct (if bland) output using only Box-provided data. No invocation can produce empty output.
4. **TC-INV-04:** The validation pipeline is ordered and deterministic. Same output + same validators = same verdict.

> **INVARIANT-1:** Every Spark invocation carries exactly one CallType. No invocation is untyped. No invocation carries two CallTypes simultaneously.

> **INVARIANT-2:** No CallType may assert mechanical outcomes. Spark has ZERO mechanical authority.

> **INVARIANT-3:** Every CallType has a non-empty fallback template. Spark is an enhancement, never a dependency.

> **INVARIANT-4:** Validation is ordered and deterministic. Same input, same verdict.

---

## 1. CallType Enum

Six CallTypes. Exhaustive — no Spark invocation may use a type not listed here.

| CallType | Authority Level | Purpose | Temperature Range | Latency Ceiling |
|----------|----------------|---------|-------------------|-----------------|
| `COMBAT_NARRATION` | ATMOSPHERIC | Flavor prose for resolved combat actions | 0.7 - 1.0 | 8s |
| `NPC_DIALOGUE` | ATMOSPHERIC | In-character NPC speech during narration | 0.7 - 1.1 | 6s |
| `SUMMARY` | INFORMATIONAL | Compressing event history at segment boundaries | 0.2 - 0.5 | 10s |
| `RULE_EXPLAINER` | NON-AUTHORITATIVE | Answering rules questions (does not adjudicate) | 0.3 - 0.6 | 8s |
| `OPERATOR_DIRECTIVE` | UNCERTAIN | Interpreting ambiguous operator input into candidate actions | 0.3 - 0.6 | 6s |
| `CLARIFICATION_QUESTION` | UNCERTAIN | Generating clarification prompts for missing/ambiguous info | 0.2 - 0.4 | 4s |

**Latency ceiling:** Per-call, not per-turn. A turn that makes multiple Spark calls sums ceilings as worst-case budget. If a single call exceeds its ceiling, the system fires the fallback template immediately (KILL-004 consideration).

### 1.1 Authority Level Definitions

| Level | Meaning | Provenance Tag | Mechanical Weight |
|-------|---------|----------------|-------------------|
| ATMOSPHERIC | Flavor text only; zero mechanical weight | `[NARRATIVE]` | None |
| UNCERTAIN | System is guessing/paraphrasing; operator must confirm before Box acts | `[UNCERTAIN]` | None (confirmation required) |
| INFORMATIONAL | Derived from Box state; not computed, not binding | `[DERIVED]` | None (read-only summary) |
| NON-AUTHORITATIVE | Explains rules but does not adjudicate; Box remains sole authority | `[DERIVED]` | None (advisory only) |

**No CallType may produce output tagged `[BOX]`.** Only Box emits `[BOX]`-tagged data. This is the load-bearing constraint of the entire contract.

---

## 2. Per-CallType Specifications

### 2.1 COMBAT_NARRATION

**When used:** After Box resolves a turn and emits events. Lens assembles NarrativeBrief, builds PromptPack, calls Spark to narrate.

**Input Schema (Lens must provide):**

| Field | Source | Required |
|-------|--------|----------|
| `truth.action_type` | NarrativeBrief.action_type | YES |
| `truth.actor_name` | NarrativeBrief.actor_name | YES |
| `truth.target_name` | NarrativeBrief.target_name | if applicable |
| `truth.outcome_summary` | NarrativeBrief.outcome_summary | YES |
| `truth.severity` | NarrativeBrief.severity | YES |
| `truth.weapon_name` | NarrativeBrief.weapon_name | if applicable |
| `truth.damage_type` | NarrativeBrief.damage_type | if applicable |
| `truth.condition_applied` | NarrativeBrief.condition_applied | if applicable |
| `truth.target_defeated` | NarrativeBrief.target_defeated | YES |
| `memory.previous_narrations` | Last 1-3 narrations | if available |
| `task.task_type` | `"narration"` | YES |
| `style.*` | Session persona parameters | YES |
| `contract.max_length_chars` | 600 | YES |
| `contract.required_provenance` | `"[NARRATIVE]"` | YES |

**Output Schema:**

| Field | Type | Constraints |
|-------|------|-------------|
| `text` | string | 2-4 sentences, prose narration, max 600 chars |
| `provenance` | string | Must be `"[NARRATIVE]"` |

**Forbidden Claims:**

| ID | Category | Pattern Description | Example Violations |
|----|----------|--------------------|--------------------|
| FC-CN-01 | mechanical_values | Specific damage numbers | "deals 14 damage", "14 points of damage" |
| FC-CN-02 | mechanical_values | Armor class values | "AC 18", "armor class of 16" |
| FC-CN-03 | mechanical_values | Hit point values | "24 HP remaining", "12 hit points" |
| FC-CN-04 | mechanical_values | Attack bonus values | "+7 to hit", "+5 attack bonus" |
| FC-CN-05 | mechanical_values | Difficulty class values | "DC 15", "difficulty class 20" |
| FC-CN-06 | mechanical_values | Die roll results | "rolled a 17", "natural 20" |
| FC-CN-07 | mechanical_values | Dice notation | "2d6+3", "1d8 damage" |
| FC-CN-08 | rule_citations | Rule book references | "PHB 145", "per the grapple rules on page 155" |
| FC-CN-09 | outcome_assertions | Entity IDs in output | "goblin_02", "entity_id: 7" |
| FC-CN-10 | outcome_assertions | Grid coordinates | "moves to (3,5)", "square B4" |
| FC-CN-11 | outcome_assertions | Facts not in truth frame | Inventing conditions, entities, or outcomes |
| FC-CN-12 | outcome_assertions | Contradicting outcome_summary | Narrating hit when outcome says miss |

**Line Type Mapping (Tier 1.1):** RESULT, NARRATION

**Fallback Template:** NarrativeBrief fields formatted as prose using `NarrationTemplates.get_template()`.

---

### 2.2 NPC_DIALOGUE

**When used:** Narration requires in-character NPC speech. Distinct from COMBAT_NARRATION because it targets a specific NPC persona with voice identity.

**Input Schema (Lens must provide):**

| Field | Source | Required |
|-------|--------|----------|
| `truth.actor_name` | NPC display name | YES |
| `truth.scene_description` | Current scene context | YES |
| `memory.session_facts` | NPC-relevant facts (relationship, attitude, knowledge) | if available |
| `memory.previous_narrations` | Recent interaction context | if available |
| `task.task_type` | `"npc_dialogue"` | YES |
| `task.npc_name` | NPC name | YES |
| `task.npc_personality` | Brief personality descriptor | YES |
| `task.dialogue_context` | What prompted the NPC to speak | YES |
| `style.npc_voice_id` | Voice persona ID for TTS routing | if available |
| `contract.max_length_chars` | 400 | YES |
| `contract.required_provenance` | `"[NARRATIVE]"` | YES |

**Output Schema:**

| Field | Type | Constraints |
|-------|------|-------------|
| `dialogue` | string | 1-4 sentences, in-character speech, max 300 chars |
| `stage_direction` | string (optional) | 1 sentence, physical action/tone, max 100 chars |
| `provenance` | string | Must be `"[NARRATIVE]"` |

**Forbidden Claims:**

| ID | Category | Pattern Description | Example Violations |
|----|----------|--------------------|--------------------|
| FC-ND-01 | mechanical_values | All mechanical assertions | "I'll give you +2 to your rolls" |
| FC-ND-02 | outcome_assertions | Information not in Memory channel | Inventing lore not provided |
| FC-ND-03 | outcome_assertions | Promises implying mechanical outcomes | "This potion will restore 2d8 hit points" |
| FC-ND-04 | outcome_assertions | Contradicting session facts | Friendly when attitude is hostile |
| FC-ND-05 | outcome_assertions | Breaking character | Meta-commentary, out-of-character statements |

**Line Type Mapping (Tier 1.1):** NARRATION, RESULT

**Fallback Template:** `"[NPC name] speaks."`

---

### 2.3 SUMMARY

**When used:** At segment boundaries (end of combat, scene transitions, session end). Lens asks Spark to compress recent narrations and events into stable memory.

**Input Schema (Lens must provide):**

| Field | Source | Required |
|-------|--------|----------|
| `truth.scene_description` | Scene being summarized | YES |
| `memory.previous_narrations` | All narrations in the segment (up to token budget) | YES |
| `memory.session_facts` | Key facts from the segment | YES |
| `task.task_type` | `"session_summary"` | YES |
| `task.events_to_summarize` | Chronologically-ordered event list | YES |
| `contract.json_mode` | `true` | YES |
| `contract.json_schema` | SummaryOutput schema | YES |
| `contract.max_length_chars` | 800 | YES |

**Output Schema:**

| Field | Type | Constraints |
|-------|------|-------------|
| `summary_text` | string | 2-5 sentences, max 800 chars |
| `key_facts` | list[string] | Max 5 items, each traceable to a provided event |
| `entities_involved` | list[string] | Entity names from the summarized events |
| `unresolved_threads` | list[string] | Open narrative threads |
| `provenance` | string | Must be `"[DERIVED]"` |

**Forbidden Claims:**

| ID | Category | Pattern Description | Example Violations |
|----|----------|--------------------|--------------------|
| FC-SU-01 | mechanical_values | All mechanical assertions | "dealt 47 total damage" |
| FC-SU-02 | outcome_assertions | Inventing events not in provided list | "The shaman fled" (not in events) |
| FC-SU-03 | outcome_assertions | Contradicting provided events | "survived" when events show defeat |
| FC-SU-04 | outcome_assertions | Speculating about future events | "They will likely retreat" |
| FC-SU-05 | outcome_assertions | Editorializing player decisions | "The player made a poor choice" |

**Line Type Mapping (Tier 1.1):** SYSTEM (summaries are not spoken; stored in memory)

**Fallback Template:** Chronological event list (no compression, no prose).

---

### 2.4 RULE_EXPLAINER

**When used:** Operator asks a rules question ("how does grappling work?"). Spark explains in natural language. The explanation is non-authoritative — Box remains sole adjudicator.

**Input Schema (Lens must provide):**

| Field | Source | Required |
|-------|--------|----------|
| `task.task_type` | `"rule_explainer"` | YES |
| `task.rule_topic` | The rule being asked about | YES |
| `task.context_hint` | Optional current-situation context | NO |
| `contract.max_length_chars` | 600 | YES |
| `contract.required_provenance` | `"[DERIVED]"` | YES |

**Output Schema:**

| Field | Type | Constraints |
|-------|------|-------------|
| `explanation` | string | 2-6 sentences, prose, max 600 chars |
| `caveat` | string | Non-authoritative disclaimer (always present) |
| `provenance` | string | Must be `"[DERIVED]"` |

**Forbidden Claims:**

| ID | Category | Pattern Description | Example Violations |
|----|----------|--------------------|--------------------|
| FC-RE-01 | mechanical_values | Asserting specific current-state bonuses | "You currently have +7 to hit" |
| FC-RE-02 | outcome_assertions | Declaring actions legal/illegal in current state | "You can't do that" (Box decides) |
| FC-RE-03 | rule_citations | Citing specific page numbers as authoritative | "PHB page 155 says..." |
| FC-RE-04 | outcome_assertions | Contradicting game system rules in spirit | Describing wrong mechanics entirely |

**Line Type Mapping (Tier 1.1):** RESULT (spoken by DM persona as informational response)

**Fallback Template:** `"Please consult the Player's Handbook."` (stub, non-authoritative)

---

### 2.5 OPERATOR_DIRECTIVE

**When used:** Operator inputs ambiguous text ("I want to rush the goblin"). Lens needs Spark to interpret intent into structured candidate actions. Operator must confirm before Box executes.

**Input Schema (Lens must provide):**

| Field | Source | Required |
|-------|--------|----------|
| `truth.scene_description` | Current scene context | YES |
| `truth.actor_name` | Active player/party member name | YES |
| `memory.session_facts` | Relevant entity names, positions, relationships | if available |
| `task.task_type` | `"operator_directive"` | YES |
| `task.operator_input` | Raw operator text string | YES |
| `task.valid_action_types` | List of mechanically valid action types | YES |
| `contract.json_mode` | `true` | YES |
| `contract.json_schema` | CandidateAction schema | YES |

**Output Schema:**

| Field | Type | Constraints |
|-------|------|-------------|
| `candidates` | list[CandidateAction] | Max 3 candidates |
| `needs_clarification` | boolean | If true, route to CLARIFICATION_QUESTION |
| `clarification_prompt` | string (optional) | If needs_clarification is true |
| `provenance` | string | Must be `"[UNCERTAIN]"` |

**CandidateAction schema:**

| Field | Type | Constraints |
|-------|------|-------------|
| `action_type` | string | Must be in `task.valid_action_types` |
| `target` | string | Must match an entity in scene/memory |
| `confidence` | float | 0.0-1.0, Spark self-report (not authority) |
| `reasoning` | string | Brief explanation of interpretation |

**Forbidden Claims:**

| ID | Category | Pattern Description | Example Violations |
|----|----------|--------------------|--------------------|
| FC-OD-01 | mechanical_values | All mechanical assertions | "+5 to hit", "DC 15" |
| FC-OD-02 | outcome_assertions | Declaring actions legal/illegal | "That's not allowed" (Box decides) |
| FC-OD-03 | outcome_assertions | Deciding outcomes | "The goblin dies" |
| FC-OD-04 | outcome_assertions | Asserting facts not in Truth/Memory | Inventing entities or state |
| FC-OD-05 | outcome_assertions | Refusing to interpret | Axiom 1: Spark never refuses; Lens gates |

**Line Type Mapping (Tier 1.1):** PROMPT (clarification routed through Tier 1.2 flow)

**Integration with Tier 1.2:** When `needs_clarification` is true, the system enters the Tier 1.2 clarification escalation ladder. The clarification budget (MAX_CLARIFICATIONS=2, per `UNKNOWN_HANDLING_CONTRACT.md` Section 3.1) applies. After budget exhaustion, the system escalates to numbered menu, then cancels.

**Fallback Template:** Keyword-only IntentBridge parsing (existing deterministic path, no Spark).

---

### 2.6 CLARIFICATION_QUESTION

**When used:** System cannot determine operator intent (ambiguous target, missing information, unclear action). May be triggered by Lens directly or by an OPERATOR_DIRECTIVE call returning `needs_clarification: true`.

**Input Schema (Lens must provide):**

| Field | Source | Required |
|-------|--------|----------|
| `task.task_type` | `"clarification_question"` | YES |
| `task.ambiguity_type` | What is ambiguous (target, action_type, spell_choice, etc.) | YES |
| `task.operator_input` | The original operator text | YES |
| `task.valid_options` | Bounded list of valid choices | if available |
| `truth.actor_name` | Active entity name | YES |
| `contract.max_length_chars` | 200 | YES |
| `contract.required_provenance` | `"[UNCERTAIN]"` | YES |

**Output Schema:**

| Field | Type | Constraints |
|-------|------|-------------|
| `question` | string | 1-2 sentences, max 200 chars |
| `options` | list[string] | Max 5, must be subset of `valid_options` if provided |
| `provenance` | string | Must be `"[UNCERTAIN]"` |

**Forbidden Claims:**

| ID | Category | Pattern Description | Example Violations |
|----|----------|--------------------|--------------------|
| FC-CQ-01 | mechanical_values | All mechanical assertions | Any numbers, DCs, bonuses |
| FC-CQ-02 | outcome_assertions | Suggesting options not in valid_options | Inventing choices |
| FC-CQ-03 | outcome_assertions | Making assumptions about intent | Guessing instead of asking |
| FC-CQ-04 | outcome_assertions | Expressing judgment about input | "That's a strange request" |

**Line Type Mapping (Tier 1.1):** PROMPT (spoken by Arbor persona as calm inquiry)

**Integration with Tier 1.2:** This CallType IS the Tier 1.2 clarification mechanism. The clarification budget applies directly: MAX_CLARIFICATIONS=2 attempts, then escalate to menu, then cancel. Each clarification question MUST differ from the previous (no repetition per `UNKNOWN_HANDLING_CONTRACT.md` Section 3.3 Rule 1).

**Fallback Template:** Hardcoded clarification templates from `session_orchestrator.py`.

---

## 3. Forbidden Claims — Parameterized Pattern System

Forbidden claims are organized into three **pattern categories** that are game-system-independent. Each category defines structural violation types. D&D 3.5e examples are provided for testability, but the pattern definitions work for any game system.

### 3.1 Pattern Category: `mechanical_values`

**Definition:** Any specific numeric value that represents a game-mechanical quantity.

**Structural patterns (game-system-independent):**

| Pattern ID | Regex | Description |
|------------|-------|-------------|
| MV-01 | `\b\d+\s*(points?\s+of\s+)?damage\b` | Damage quantities |
| MV-02 | `\bAC\s*\d+\b` | Armor class values |
| MV-03 | `\b\d+\s*h(it\s*)?p(oints?)?\b` | Hit point values |
| MV-04 | `[+-]\d+\s*(to\s+)?(attack\|hit)\b` | Attack bonus values |
| MV-05 | `\bDC\s*\d+\b` | Difficulty class values |
| MV-06 | `\broll(ed)?\s+(a\s+)?\d+\b` | Die roll results |
| MV-07 | `\b\d+d\d+` | Dice notation |
| MV-08 | `\b\d+\s*(?:feet\|ft\.?\|squares?)\s+(?:of\s+)?(?:movement\|range\|reach)\b` | Distance/range values |
| MV-09 | `\bnatural\s+\d+\b` | Natural die results ("natural 20", "natural 1") |

**D&D 3.5e examples:** "14 points of damage", "AC 18", "24 HP", "+7 to hit", "DC 15", "rolled a 17", "2d6+3", "30 feet of movement", "natural 20"

**Parameterization note:** MV-02 uses "AC" (D&D-specific). In another system, this pattern slot would contain the system's defense stat abbreviation (e.g., "Defense" for a sci-fi system). The pattern category is universal; the regex content is world-specific per `RQ-SPRINT-004` W-1.

### 3.2 Pattern Category: `rule_citations`

**Definition:** Any reference to a specific rulebook, page number, or rule name presented as authoritative source.

**Structural patterns (game-system-independent):**

| Pattern ID | Regex | Description |
|------------|-------|-------------|
| RC-01 | `\b(PHB\|DMG\|MM)\s*\d+` | Rulebook abbreviation + page number |
| RC-02 | `\b(page\|pg\.?\|p\.)\s*\d+\b` | Generic page reference |
| RC-03 | `\bper\s+the\s+\w+\s+rules\b` | "Per the X rules" phrasing |
| RC-04 | `\brules?\s+(as\s+written\|state|say)\b` | RAW assertion phrasing |

**D&D 3.5e examples:** "PHB 145", "per the grapple rules", "rules as written state"

**Parameterization note:** RC-01 uses "PHB|DMG|MM" (D&D 3.5e book abbreviations). In Pathfinder 2e, this would be "CRB|APG|GMG". The pattern category is universal; the abbreviation set is world-specific per `RQ-SPRINT-004` W-10.

### 3.3 Pattern Category: `outcome_assertions`

**Definition:** Any claim about game state, entity status, or action results that is not supported by the truth frame provided in the input schema.

**Structural checks (game-system-independent):**

| Check ID | Method | Description |
|----------|--------|-------------|
| OA-01 | Entity name matching | Every entity named in output must appear in Truth or Memory input |
| OA-02 | Outcome direction | If output implies hit/miss/defeat, must align with `truth.outcome_summary` |
| OA-03 | Condition matching | If output mentions a condition, must match `truth.condition_applied` |
| OA-04 | Severity consistency | Narration intensity must match `truth.severity` |
| OA-05 | Defeat consistency | Defeat language forbidden when `truth.target_defeated` is false |
| OA-06 | Invention check | Claims not traceable to any input field are flagged |

**D&D 3.5e examples:** Narrating "the goblin falls dead" when `target_defeated=false`, describing "stunned" when `condition_applied` is null, referencing "Goblin Shaman" when only "Goblin Scout" appears in truth frame.

---

## 4. Validation Pipeline

Three stages, executed in order. Stage 3 is reserved for a future tier.

```
Spark Output
    |
    v
[Stage 1: GrammarShield]  --- Tier 1.1 conformance
    |                          Line type validation (G-01..G-07)
    |                          Anti-pattern scan (AP-01..AP-07)
    |                          FAIL -> retry (max 2) -> template fallback
    v
[Stage 2: ForbiddenClaimChecker]  --- Per-CallType forbidden claims
    |                                  mechanical_values regex scan
    |                                  rule_citations regex scan
    |                                  outcome_assertions structural check
    |                                  FAIL -> retry (max 1) -> template fallback
    v
[Stage 3: RESERVED — EvidenceValidator]  --- Future tier
    |                                        Evidence tracing against truth frame
    |                                        Not implemented in this spec
    v
[Provenance Tagger]  --- Attach required provenance tag per CallType
    |
    v
Validated Output (or template fallback)
```

### 4.1 Stage 1: GrammarShield (Tier 1.1 Conformance)

**Input:** Raw Spark output text + CallType + line type mapping
**Checks:**
- Output must parse into valid line types per `CLI_GRAMMAR_CONTRACT.md`
- No anti-patterns (AP-01 through AP-07) in spoken output
- Character/sentence count within bounds per line type

**On failure:** Retry (max 2 attempts). If retries exhausted, fire template fallback.

### 4.2 Stage 2: ForbiddenClaimChecker (Per-CallType)

**Input:** Parsed output text + CallType's forbidden claims list
**Checks:**
- Run all `mechanical_values` regex patterns (MV-01 through MV-09)
- Run all `rule_citations` regex patterns (RC-01 through RC-04)
- For COMBAT_NARRATION and NPC_DIALOGUE: run `outcome_assertions` structural checks (OA-01 through OA-06)
- Additional per-CallType forbidden patterns as defined in Section 2

**On failure:** Retry (max 1 attempt) with correction prompt. If retry fails, fire template fallback. Log violation for KILL-002 consideration.

### 4.3 Stage 3: RESERVED — EvidenceValidator

**Slot reserved for future tier.** When implemented, this stage will verify that every mechanical-adjacent claim in Spark output traces back to a specific field in the PromptPack's Truth or Memory channel.

**Not required by this spec.** The slot exists to prevent pipeline redesign when EvidenceValidator is added.

### 4.4 Provenance Tagger

**Input:** Validated output + CallType's required provenance tag
**Action:** Attach the correct provenance tag per Section 1.1 authority level definitions.
**On mismatch:** Fix automatically (re-tag). No retry needed.

### 4.5 Pipeline Invariants

- **Ordered execution:** Stage 1 before Stage 2 before Stage 3. No stage may be skipped.
- **Deterministic verdict:** Given identical output text and identical CallType, the pipeline produces identical pass/fail results.
- **Fail-safe:** If any stage encounters an internal error (not a validation failure but a code error), the pipeline treats the output as failed and fires the template fallback. No unvalidated output reaches the operator.
- **Retry budget:** Stage 1 allows 2 retries. Stage 2 allows 1 retry. Total worst-case: 3 Spark calls per invocation. Consecutive rejections > 3 trigger KILL-005.

---

## 5. Template Fallback Guarantees

Every CallType has a template-based fallback path. Template narration is always safe. Spark is an enhancement, never a dependency.

| CallType | Fallback Path | Output Quality |
|----------|--------------|----------------|
| COMBAT_NARRATION | NarrativeBrief fields -> `NarrationTemplates.get_template()` | Correct, bland prose |
| NPC_DIALOGUE | `"[NPC name] speaks."` | Minimal stub, correct |
| SUMMARY | Chronological event list (no compression) | Verbose but accurate |
| RULE_EXPLAINER | `"Please consult the Player's Handbook."` | Non-authoritative stub |
| OPERATOR_DIRECTIVE | Keyword-only IntentBridge parsing | Deterministic, no LLM |
| CLARIFICATION_QUESTION | Hardcoded templates from `session_orchestrator.py` | Fixed phrasing, functional |

**Fallback invariant:** Every fallback template MUST itself pass GrammarShield validation (Stage 1). A fallback that violates Tier 1.1 grammar rules is a contract violation.

---

## 6. Integration Points

### 6.1 Tier 1.1 (CLI Grammar Contract)

Each CallType's output must conform to one or more Tier 1.1 line types. The mapping is:

| CallType | Permitted Line Types |
|----------|---------------------|
| COMBAT_NARRATION | RESULT, NARRATION |
| NPC_DIALOGUE | NARRATION, RESULT |
| SUMMARY | SYSTEM |
| RULE_EXPLAINER | RESULT |
| OPERATOR_DIRECTIVE | PROMPT |
| CLARIFICATION_QUESTION | PROMPT |

**Constraint:** Every permitted line type in this mapping must exist in the Tier 1.1 taxonomy (7 types: TURN, RESULT, ALERT, NARRATION, PROMPT, SYSTEM, DETAIL). No CallType may produce a line type not defined in Tier 1.1.

### 6.2 Tier 1.2 (Unknown Handling Contract)

Two CallTypes integrate with Tier 1.2:

| CallType | Tier 1.2 Integration |
|----------|---------------------|
| OPERATOR_DIRECTIVE | When `needs_clarification=true`, enters Tier 1.2 clarification escalation. Clarification budget (MAX_CLARIFICATIONS=2) applies. |
| CLARIFICATION_QUESTION | IS the Tier 1.2 clarification mechanism. Budget, escalation ladder, cancel semantics all apply per `UNKNOWN_HANDLING_CONTRACT.md` Section 3. |

**Shared constraints from Tier 1.2:**
- No repetition: clarification #2 must differ from #1 (Section 3.3 Rule 1)
- Increasing specificity: subsequent questions provide more context (Section 3.3 Rule 2)
- DM voice only for clarification questions (Section 3.3 Rule 3)
- No leading questions (Section 3.3 Rule 4)
- No mechanical jargon in questions (Section 3.3 Rule 5)
- Cancel semantics: "cancel"/"never mind"/"stop" discards pending intent (Section 3.4)

---

## 7. Authority Boundary Statement

This contract governs the invocation boundary between Lens and Spark. It defines WHAT each invocation type may produce and HOW violations are detected. It does not implement the validation pipeline in code. It does not modify engine mechanics, Box resolution, or Oracle state. It does not change Tier 1.1 or Tier 1.2 contracts. It does not add new line types.

Spark has ZERO mechanical authority. This contract enforces that constraint at the invocation boundary.

---

## END OF TYPED CALL CONTRACT v1.0
