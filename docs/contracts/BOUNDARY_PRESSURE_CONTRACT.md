# Boundary Pressure Contract v1
## Pre-Generation Risk Signal Specification

**Document ID:** RQ-PRESSURE-001
**Version:** 1.0
**Date:** 2026-02-21
**Status:** DRAFT — Awaiting PM Approval
**Authority:** This document is the canonical contract for boundary pressure detection. It governs when a pre-generation risk signal prevents Spark from firing, what structural conditions constitute pressure triggers, how pressure levels are classified, and what response policy applies per level.
**Scope:** Pressure triggers, PressureLevel classification, response policy, detection method, observability, integration points, and invariants. Spec only — no runtime implementation.

**References:**
- `docs/planning/research/RQ_SPARK_BOUNDARY_PRESSURE.md` — Boundary pressure research (Sections 2-8)
- `docs/research/RQ-SPRINT-004_SPARK_CONTAINMENT_AUDIT.md` — Containment mechanisms (Section 1.6)
- `docs/research/VOICE_CONTROL_PLANE_CONTRACT.md` — Voice control plane, boundary invariants
- `docs/contracts/TYPED_CALL_CONTRACT.md` (RQ-TYPEDCALL-001) — Tier 1.3, CallType input schemas, forbidden claims, fallback templates
- `docs/contracts/CLI_GRAMMAR_CONTRACT.md` (RQ-GRAMMAR-001) — Tier 1.1, line types and grammar rules
- `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md` (RQ-UNKNOWN-001) — Tier 1.2, STOPLIGHT pattern, clarification budget

**Existing Implementation (this spec formalizes):**

| Layer | File | Status |
|-------|------|--------|
| Boundary pressure research | `docs/planning/research/RQ_SPARK_BOUNDARY_PRESSURE.md` | Research complete |
| Containment audit | `docs/research/RQ-SPRINT-004_SPARK_CONTAINMENT_AUDIT.md` | Research complete |
| Boundary pressure validator | `scripts/check_boundary_pressure.py` | **New — created by this WO** |
| Gate tests | `tests/test_boundary_pressure_gate_m.py` | **New — created by this WO** |

**Tier Position:** Tier 1.4 in the BURST-001 build order.

| Tier | Contract | Domain |
|------|----------|--------|
| 1.1 | CLI Grammar Contract | Output formatting |
| 1.2 | Unknown Handling Contract | Input failure handling |
| 1.3 | Typed Call Contract | Invocation boundary |
| **1.4** | **Boundary Pressure Contract** | **Pre-generation risk signal** |

---

## Contract Summary (1-Page)

Before Spark sees a prompt, the system evaluates whether the narration task is structurally likely to produce a mechanical authority violation. If risk is high, Spark never fires — template fallback handles it. The rule: **don't generate output you'll have to reject.**

**Detection Model:**

```
PromptPack Assembly
    |
    v
[Pressure Evaluator]  --- Field inspection (content-agnostic)
    |                      4 trigger checks
    |                      PressureLevel computed
    |                      Pressure event logged
    v
[Decision Gate]
    |
    +-- GREEN  --> Spark fires normally
    |
    +-- YELLOW --> Spark fires with advisory fallback pre-loaded
    |              (if post-hoc validation rejects: template immediately, no retry)
    |
    +-- RED    --> Spark does NOT fire. Template fallback directly.
```

**Invariants:**
1. **BP-INV-01:** Every Spark invocation is preceded by a pressure evaluation. No invocation skips the evaluator.
2. **BP-INV-02:** RED pressure level never reaches Spark. Fail-closed guarantee.
3. **BP-INV-03:** Pressure detection uses only structural field inspection. No vocabulary. No game-specific patterns. No regex. No keyword lists.
4. **BP-INV-04:** Every pressure evaluation produces a logged event. Observability guarantee.
5. **BP-INV-05:** Pressure detection is deterministic. Same PromptPack fields = same PressureLevel.

> **INVARIANT-1:** Every Spark invocation is preceded by a pressure evaluation. No unscreened invocations.

> **INVARIANT-2:** RED never reaches Spark. Fail-closed.

> **INVARIANT-3:** Detection is content-agnostic. Zero vocabulary dependencies. Zero game-system dependencies.

> **INVARIANT-4:** Every evaluation is logged. No silent pressure.

> **INVARIANT-5:** Detection is deterministic. Same input, same verdict.

---

## 1. Pressure Triggers

Four pressure triggers. Exhaustive — no additional triggers may be added without a contract amendment.

### 1.1 Trigger: BP-MISSING-FACT

**ID:** BP-MISSING-FACT
**Condition:** Required input fields (per Tier 1.3 CallType input schema) are null, empty, or absent in the PromptPack.
**Default Severity:** RED
**Detection Rule:** For the invocation's CallType, enumerate all fields marked `Required: YES` in the Tier 1.3 input schema. If any required field is null, empty string, empty list, or absent, this trigger fires.

**Affected CallTypes:** ALL (every CallType has required input fields).

**Per-CallType Required Fields (from Tier 1.3):**

| CallType | Required Fields That Fire BP-MISSING-FACT If Absent |
|----------|-----------------------------------------------------|
| COMBAT_NARRATION | truth.action_type, truth.actor_name, truth.outcome_summary, truth.severity, truth.target_defeated, task.task_type, contract.max_length_chars, contract.required_provenance |
| NPC_DIALOGUE | truth.actor_name, truth.scene_description, task.task_type, task.npc_name, task.npc_personality, task.dialogue_context, contract.max_length_chars, contract.required_provenance |
| SUMMARY | truth.scene_description, memory.previous_narrations, memory.session_facts, task.task_type, task.events_to_summarize, contract.json_mode, contract.json_schema, contract.max_length_chars |
| RULE_EXPLAINER | task.task_type, task.rule_topic, contract.max_length_chars, contract.required_provenance |
| OPERATOR_DIRECTIVE | truth.scene_description, truth.actor_name, task.task_type, task.operator_input, task.valid_action_types, contract.json_mode, contract.json_schema |
| CLARIFICATION_QUESTION | task.task_type, task.ambiguity_type, task.operator_input, truth.actor_name, contract.max_length_chars, contract.required_provenance |

**Rationale:** If Box hasn't provided the required data, Spark cannot generate safe output. Missing truth frame data means Spark will invent facts — a mechanical authority violation.

**Fail-closed behavior:**

| Level | Condition | Response |
|-------|-----------|----------|
| GREEN | All required fields populated | Proceed |
| RED | Any required field null/empty/absent | Template fallback, no Spark call |

**Note:** BP-MISSING-FACT has no YELLOW level. Required data is either present or absent — there is no partial state. This is the only trigger that fires RED on its own (per PD-01).

---

### 1.2 Trigger: BP-AMBIGUOUS-INTENT

**ID:** BP-AMBIGUOUS-INTENT
**Condition:** The PromptPack carries multiple valid interpretations of operator intent that cannot be mechanically distinguished.
**Default Severity:** YELLOW
**Detection Rule:** Structural field inspection of the PromptPack's task channel:
- If `task.operator_input` is present AND the invocation is OPERATOR_DIRECTIVE or CLARIFICATION_QUESTION:
  - Check whether the PromptPack's candidate list (if present) contains 2+ candidates
  - Check whether `needs_clarification` is true in a prior OPERATOR_DIRECTIVE result
- If neither condition is present, this trigger does not fire.

**Affected CallTypes:** OPERATOR_DIRECTIVE, CLARIFICATION_QUESTION

**Detection is structural, not semantic.** The evaluator does not parse natural language. It checks whether the PromptPack's candidate count field indicates ambiguity. The ambiguity itself was determined by the IntentBridge (Tier 1.2 domain) before the PromptPack was assembled.

**Fail-closed behavior:**

| Level | Condition | Response |
|-------|-----------|----------|
| GREEN | Single unambiguous intent, or CallType not affected | Proceed |
| YELLOW | 2-3 candidates, or needs_clarification=true | Proceed with advisory fallback pre-loaded |
| RED | 4+ candidates, or 0 candidates (routing failure) | Template fallback, no Spark call |

**Relationship to Tier 1.2:** The 0-candidate case is also an `UNKNOWN_HANDLING_CONTRACT.md` FC-ASR or FC-PARTIAL failure class. Tier 1.2 handles the player-facing response; BP-AMBIGUOUS-INTENT ensures Spark is not called during the confusion.

---

### 1.3 Trigger: BP-AUTHORITY-PROXIMITY

**ID:** BP-AUTHORITY-PROXIMITY
**Condition:** The narration task is structurally close to mechanical territory — the PromptPack's truth frame contains fields that are adjacent to authority boundary violations.
**Default Severity:** YELLOW
**Detection Rule:** Structural field inspection of the PromptPack's truth channel:
- If `truth.outcome_summary` contains the substring "pending" or is empty (Box hasn't fully resolved)
- If the CallType is RULE_EXPLAINER and `task.context_hint` references an active (unresolved) game state query
- If the CallType is COMBAT_NARRATION and `truth.severity` is null (Box didn't classify severity)

**Affected CallTypes:** COMBAT_NARRATION, RULE_EXPLAINER, OPERATOR_DIRECTIVE

**Detection is structural, not semantic.** The evaluator checks field presence and sentinel values, not the content of the fields. "pending" is a sentinel value set by Box when resolution is incomplete, not a vocabulary word.

**Fail-closed behavior:**

| Level | Condition | Response |
|-------|-----------|----------|
| GREEN | Truth frame fully resolved, no proximity signals | Proceed |
| YELLOW | One proximity signal detected | Proceed with advisory fallback pre-loaded |
| RED | Proximity signal combined with other YELLOW triggers (see escalation rules) | Template fallback, no Spark call |

**Rationale:** When the truth frame is incomplete or ambiguous, Spark is pressured to fill gaps with invented mechanical facts. A fully resolved truth frame (severity classified, outcome clear, no pending state) means Spark only needs to add flavor — its proper role.

**Boundary between BP-AMBIGUOUS-INTENT and BP-AUTHORITY-PROXIMITY:** BP-AMBIGUOUS-INTENT fires when the *operator's intent* is unclear (what does the player want?). BP-AUTHORITY-PROXIMITY fires when Box's *resolution* is incomplete (what happened mechanically?). Ambiguity is an input problem. Proximity is an output risk.

---

### 1.4 Trigger: BP-CONTEXT-OVERFLOW

**ID:** BP-CONTEXT-OVERFLOW
**Condition:** The token budget for the Spark call is insufficient to fit the PromptPack's required content plus constraints.
**Default Severity:** YELLOW
**Detection Rule:** Structural inspection of the PromptPack's token budget fields:
- Compute `required_tokens` = estimated token count of all required input fields for this CallType
- Compute `available_tokens` = CallType's token budget ceiling minus system instruction overhead
- Compute `inclusion_ratio` = available_tokens / required_tokens
- Apply thresholds:
  - GREEN: inclusion_ratio >= 1.0 (everything fits)
  - YELLOW: 0.5 <= inclusion_ratio < 1.0 (some context must be dropped)
  - RED: inclusion_ratio < 0.5 (critical context cannot fit)

**Affected CallTypes:** ALL (every CallType has a token budget).

**Detection is content-agnostic.** Token counting is a numerical operation on field sizes. No vocabulary scanning. No pattern matching. The evaluator counts estimated tokens, not specific words.

**Fail-closed behavior:**

| Level | Condition | Response |
|-------|-----------|----------|
| GREEN | All required content fits within budget | Proceed |
| YELLOW | Budget tight; optional context (memory, previous narrations) dropped | Proceed with advisory fallback pre-loaded |
| RED | Required content itself exceeds budget | Template fallback, no Spark call |

**Integration with Tier 1.3:** The per-CallType latency ceilings in the Typed Call Contract (Section 1) imply token budget constraints. A COMBAT_NARRATION call with an 8s latency ceiling and a 600-char output limit constrains the input budget. BP-CONTEXT-OVERFLOW enforces this constraint at the pre-generation boundary.

---

## 2. PressureLevel Classification

### 2.1 Three Levels

| Level | Color | Meaning | Spark Called? | Retry Allowed? |
|-------|-------|---------|---------------|----------------|
| GREEN | Green | No pressure. Normal operation. | YES | YES (per Tier 1.3 pipeline) |
| YELLOW | Yellow | Advisory. Elevated risk. | YES | NO — if post-hoc validation rejects, template fires immediately |
| RED | Red | Fail-closed. Do not generate. | NO | NO — template fallback directly |

**STOPLIGHT pattern alignment:** These three levels mirror the Tier 1.2 STOPLIGHT classification (GREEN/YELLOW/RED) from `UNKNOWN_HANDLING_CONTRACT.md`. The semantics are analogous:
- Tier 1.2 STOPLIGHT classifies *input confidence* (how well did we understand the player?)
- Tier 1.4 PressureLevel classifies *output risk* (how likely is Spark to violate authority?)

### 2.2 Composite Classification Rules

When multiple triggers fire simultaneously, the composite PressureLevel is computed as follows:

| Rule | Condition | Composite Level |
|------|-----------|-----------------|
| R-01 | Any single RED trigger fires | RED |
| R-02 | 1 YELLOW trigger fires | YELLOW |
| R-03 | 2 YELLOW triggers fire | YELLOW |
| R-04 | 3+ YELLOW triggers fire simultaneously | RED (escalation) |
| R-05 | No triggers fire | GREEN |
| R-06 | Unknown/malformed trigger | RED (fail-closed default) |

**Escalation threshold (PD-04):** 3+ YELLOW triggers escalate to RED. The rationale: three simultaneous structural concerns (ambiguous intent + authority proximity + context overflow) indicate a fundamentally unsafe generation environment. Any two might be manageable with advisory fallback; three is a systemic signal.

**Single-RED override:** Any single RED trigger (BP-MISSING-FACT at RED, BP-AMBIGUOUS-INTENT at RED with 0/4+ candidates, BP-CONTEXT-OVERFLOW at RED) forces composite RED regardless of other trigger states. RED is absorbing.

---

## 3. Response Policy

### 3.1 GREEN Response Policy

| Aspect | Policy |
|--------|--------|
| Spark called | YES |
| Retry on validation failure | YES — per Tier 1.3 validation pipeline (Stage 1: 2 retries, Stage 2: 1 retry) |
| Fallback pre-loaded | NO |
| Operator notified | NO |
| Pressure event logged | YES (at DEBUG level) |

GREEN is the normal operating path. No modifications to the Spark call, retry behavior, or fallback behavior.

### 3.2 YELLOW Response Policy

| Aspect | Policy |
|--------|--------|
| Spark called | YES |
| Retry on validation failure | **NO** — if Tier 1.3 post-hoc validation (Stage 1 or Stage 2) rejects the output, use template fallback immediately. No retry attempts. |
| Fallback pre-loaded | YES — template fallback is computed and cached before the Spark call |
| Operator notified | NO (advisory only; alert string may be appended per audio integration) |
| Pressure event logged | YES (at WARNING level) |

**Key constraint:** YELLOW eliminates retry. Under normal (GREEN) conditions, the Tier 1.3 pipeline allows 2 retries at Stage 1 and 1 retry at Stage 2 (3 total). Under YELLOW, the first validation failure fires the template. The rationale: if the system detected elevated risk *before* generation, and the output fails validation, retrying is unlikely to produce a safe result. Fail to template immediately.

**Effect on Tier 1.3 pipeline:** YELLOW does not modify the pipeline's validation logic. It modifies the retry policy only. The same forbidden claims checks run; the same grammar checks run. Only the retry budget changes (from 3 to 0).

### 3.3 RED Response Policy

| Aspect | Policy |
|--------|--------|
| Spark called | **NO** |
| Retry on validation failure | N/A — no generation occurs |
| Fallback used | YES — per-CallType template fallback from Tier 1.3 Section 5 |
| Operator notified | YES — pressure event logged at ERROR level |
| Pressure event logged | YES (at ERROR level) |

**Fail-closed guarantee (PD-02):** RED means Spark never fires. No speculative generation. No "try anyway." The template fallback handles the output. The template is guaranteed to exist and pass GrammarShield (per Tier 1.3 TC-INV-03).

**Which fallback fires:** The per-CallType fallback template from `TYPED_CALL_CONTRACT.md` Section 5:

| CallType | Fallback on RED |
|----------|----------------|
| COMBAT_NARRATION | NarrativeBrief fields -> NarrationTemplates.get_template() |
| NPC_DIALOGUE | "[NPC name] speaks." |
| SUMMARY | Chronological event list |
| RULE_EXPLAINER | "Please consult the Player's Handbook." |
| OPERATOR_DIRECTIVE | Keyword-only IntentBridge parsing |
| CLARIFICATION_QUESTION | Hardcoded templates from session_orchestrator.py |

---

## 4. Detection Method

### 4.1 Pre-Call PromptPack Field Inspection

Detection occurs **before** the PromptPack reaches Spark. The evaluator inspects the assembled PromptPack's fields — it does not inspect the content of those fields.

**Content-agnostic constraint (BP-INV-03):** The detection method uses ONLY:
- Field presence (null check)
- Field emptiness (empty string, empty list)
- Sentinel values ("pending" — set by Box, not vocabulary)
- Numeric comparisons (token counts, candidate counts, inclusion ratios)
- Boolean checks (needs_clarification)

The detection method does NOT use:
- Vocabulary scanning (no keyword lists)
- Regex pattern matching (no mechanical assertion patterns — that's Tier 1.3 Stage 2)
- Game-system-specific rules (no D&D terminology)
- Natural language understanding (no intent parsing — that's Tier 1.2)
- Embedding similarity (no ML models)

### 4.2 Detection Algorithm (Pseudocode)

```
function evaluate_pressure(prompt_pack, call_type):
    triggers_fired = []

    // BP-MISSING-FACT
    for field in call_type.required_input_fields:
        if prompt_pack[field] is null or empty:
            triggers_fired.append(Trigger(BP-MISSING-FACT, RED))
            break  // one missing required field is enough

    // BP-AMBIGUOUS-INTENT
    if call_type in (OPERATOR_DIRECTIVE, CLARIFICATION_QUESTION):
        candidates = prompt_pack.get("candidates", [])
        needs_clar = prompt_pack.get("needs_clarification", false)
        if len(candidates) == 0 or len(candidates) >= 4:
            triggers_fired.append(Trigger(BP-AMBIGUOUS-INTENT, RED))
        elif len(candidates) >= 2 or needs_clar:
            triggers_fired.append(Trigger(BP-AMBIGUOUS-INTENT, YELLOW))

    // BP-AUTHORITY-PROXIMITY
    if call_type in (COMBAT_NARRATION, RULE_EXPLAINER, OPERATOR_DIRECTIVE):
        outcome = prompt_pack.get("truth.outcome_summary", "")
        severity = prompt_pack.get("truth.severity", null)
        if "pending" in outcome or outcome == "":
            triggers_fired.append(Trigger(BP-AUTHORITY-PROXIMITY, YELLOW))
        if call_type == COMBAT_NARRATION and severity is null:
            triggers_fired.append(Trigger(BP-AUTHORITY-PROXIMITY, YELLOW))

    // BP-CONTEXT-OVERFLOW
    required_tokens = estimate_tokens(call_type.required_fields, prompt_pack)
    available_tokens = call_type.token_budget - system_instruction_overhead
    if available_tokens <= 0 or required_tokens <= 0:
        ratio = 0.0
    else:
        ratio = available_tokens / required_tokens
    if ratio < 0.5:
        triggers_fired.append(Trigger(BP-CONTEXT-OVERFLOW, RED))
    elif ratio < 1.0:
        triggers_fired.append(Trigger(BP-CONTEXT-OVERFLOW, YELLOW))

    // Composite classification
    return compute_composite(triggers_fired)
```

### 4.3 Composite Classification Algorithm

```
function compute_composite(triggers_fired):
    if len(triggers_fired) == 0:
        return GREEN

    red_count = count(t for t in triggers_fired if t.level == RED)
    yellow_count = count(t for t in triggers_fired if t.level == YELLOW)

    // R-01: Any single RED -> composite RED
    if red_count > 0:
        return RED

    // R-04: 3+ YELLOW -> escalate to RED
    if yellow_count >= 3:
        return RED

    // R-02, R-03: 1-2 YELLOW -> composite YELLOW
    if yellow_count > 0:
        return YELLOW

    // R-05: No triggers -> GREEN (already handled above)
    // R-06: Unknown/malformed -> RED (defensive)
    return RED  // fail-closed default for unhandled cases
```

---

## 5. Observability

### 5.1 Pressure Event Payload

Every pressure evaluation produces a logged event with the following schema:

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `trigger_ids` | list[string] | IDs of all triggers that fired (e.g., ["BP-MISSING-FACT"]) | YES |
| `trigger_levels` | list[string] | Per-trigger severity (e.g., ["RED"]) | YES |
| `composite_level` | string | Final computed PressureLevel (GREEN, YELLOW, RED) | YES |
| `call_type` | string | The CallType that was attempted | YES |
| `response` | string | Action taken (proceed, advisory_fallback, fail_closed) | YES |
| `correlation_id` | string | UUID linking to post-hoc validation result (if Spark was called) | YES |
| `turn_number` | int | Game turn when evaluation occurred | YES |
| `detail` | string | Human-readable explanation (1 line) | YES |
| `timestamp` | string | ISO 8601 timestamp | YES |

### 5.2 Response Values

| Value | Meaning |
|-------|---------|
| `proceed` | GREEN — normal Spark call, no modifications |
| `advisory_fallback` | YELLOW — Spark called, template pre-loaded, no retry on failure |
| `fail_closed` | RED — Spark not called, template fallback used |

### 5.3 Log Levels

| PressureLevel | Log Level | Rationale |
|---------------|-----------|-----------|
| GREEN | DEBUG | Normal operation; high volume, low interest |
| YELLOW | WARNING | Elevated risk; reviewable but not alarming |
| RED | ERROR | Fail-closed; always reviewable, correlates with template usage |

### 5.4 Correlation with Post-Hoc Validation

When Spark IS called (GREEN or YELLOW), the `correlation_id` in the pressure event matches the `correlation_id` in the Tier 1.3 validation pipeline result. This allows post-hoc analysis:
- **YELLOW + validation pass:** Advisory was conservative; Spark generated safely.
- **YELLOW + validation fail:** Advisory was correct; template fired. Threshold is well-calibrated.
- **GREEN + validation fail:** Pressure detection missed a risk signal. Potential trigger gap.

This correlation is the primary mechanism for threshold tuning. A high rate of "GREEN + validation fail" suggests missing triggers or incorrect GREEN thresholds.

---

## 6. Integration Points

### 6.1 Integration with Tier 1.1 (CLI Grammar Contract)

Pressure does not directly interact with Tier 1.1. However:
- Template fallbacks fired by RED pressure must conform to Tier 1.1 line types (per TC-INV-03)
- The pressure evaluator does not produce CLI output itself — it produces a pressure event and a decision

### 6.2 Integration with Tier 1.2 (Unknown Handling Contract)

| Integration Point | Relationship |
|-------------------|-------------|
| STOPLIGHT pattern | PressureLevel mirrors STOPLIGHT (GREEN/YELLOW/RED) — same color semantics, different domain |
| Clarification budget | When BP-AMBIGUOUS-INTENT fires at YELLOW, the Tier 1.2 clarification escalation ladder applies if the system asks for clarification |
| FC-ASR / FC-PARTIAL | Tier 1.2 failure classes that produce 0-candidate situations trigger BP-AMBIGUOUS-INTENT at RED |

**Shared constraint:** Both Tier 1.2 and Tier 1.4 agree that 0 candidates is a hard stop. Tier 1.2 handles the player-facing response (clarification question). Tier 1.4 ensures Spark is not called during the confusion.

### 6.3 Integration with Tier 1.3 (Typed Call Contract)

| Integration Point | Relationship |
|-------------------|-------------|
| Input schemas | BP-MISSING-FACT checks required fields defined in Tier 1.3 per-CallType input schemas |
| Fallback templates | RED response fires the per-CallType fallback template defined in Tier 1.3 Section 5 |
| Validation pipeline | YELLOW modifies retry policy (no retries); GREEN preserves normal retry policy |
| Latency ceilings | BP-CONTEXT-OVERFLOW's token budget derives from Tier 1.3 per-CallType latency ceilings |

**YELLOW's effect on Tier 1.3 retry budget:**

| PressureLevel | Tier 1.3 Stage 1 Retries | Tier 1.3 Stage 2 Retries | Total |
|---------------|--------------------------|--------------------------|-------|
| GREEN | 2 | 1 | 3 |
| YELLOW | 0 | 0 | 0 |
| RED | N/A (no Spark call) | N/A | N/A |

### 6.4 Ordering in the Full Pipeline

```
PromptPack Assembly (Lens)
    |
    v
[Tier 1.4: Pressure Evaluator]  --- PRE-GENERATION
    |
    +-- RED  --> Template Fallback (Tier 1.3 per-CallType)
    |             No Spark call.
    |
    +-- GREEN/YELLOW --> Spark Generation
                            |
                            v
                       [Tier 1.3 Stage 1: GrammarShield]  --- POST-GENERATION
                            |
                            v
                       [Tier 1.3 Stage 2: ForbiddenClaimChecker]
                            |
                            v
                       [Tier 1.3 Stage 3: RESERVED]
                            |
                            v
                       [Provenance Tagger]
                            |
                            v
                       Validated Output (or template on YELLOW-triggered failure)
```

Tier 1.4 sits BEFORE Tier 1.3 in the pipeline. It gates whether Spark is called at all. Tier 1.3 validates what Spark produces. Together they form a pre/post containment sandwich.

---

## 7. Authority Boundary Statement

This contract governs the pre-generation risk signal. It defines WHEN Spark should not be called and HOW that decision is made. It does not implement the detection logic in code. It does not modify engine mechanics, Box resolution, or Oracle state. It does not change Tier 1.1, 1.2, or 1.3 contracts. It does not add new line types. It does not introduce vocabulary or game-specific detection rules.

Pressure detection is content-agnostic. This is the only mechanism in the entire containment pipeline with zero game-system dependencies (per `RQ-SPRINT-004` Section 1.6).

---

## END OF BOUNDARY PRESSURE CONTRACT v1.0
