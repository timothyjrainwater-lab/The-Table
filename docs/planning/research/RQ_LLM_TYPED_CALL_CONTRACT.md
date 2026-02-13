# RQ: LLM Typed-Call Contract — Lens/Spark Mode-Locked Request/Response Schemas

**Work Order:** WO-RQ-LLM-CALL-TYPING-01
**Status:** RESEARCH COMPLETE
**Date:** 2026-02-13
**Author:** Sonnet C (Agent)
**Authority:** PM-approved research deliverable

---

## 1. Purpose

This document defines the typed-call contract between Lens and Spark: mode-locked request/response schemas, allowed outputs per call type, and enforcement hooks that prevent authority bleed. Every Spark invocation is tagged with exactly one `CallType`, which constrains what Spark may produce and what Lens must validate.

**Binding references:**
- SPARK_LENS_BOX_DOCTRINE.md (Axioms 1-4)
- AD-002: Lens Context Orchestration (Five-Channel PromptPack)
- SPARK_PROVIDER_CONTRACT.md (SparkRequest/SparkResponse schema)
- PromptPack v1 (`aidm/schemas/prompt_pack.py`)
- GrammarShield (`aidm/spark/grammar_shield.py`)

---

## 2. CallType Enum

Each Spark invocation carries exactly one `CallType`. The call type determines the required inputs, forbidden claims, output shape, and validation rules.

| CallType | Purpose | Authority Level | Temperature Range |
|---|---|---|---|
| `COMBAT_NARRATION` | Describe what just happened in combat | ATMOSPHERIC only | 0.7 - 1.0 |
| `OPERATOR_DIRECTIVE` | Interpret operator intent into candidate actions | UNCERTAIN | 0.3 - 0.6 |
| `SUMMARY` | Compress recent events into session memory | INFORMATIONAL | 0.2 - 0.5 |
| `RULE_EXPLAINER` | Explain a rule in natural language (non-authoritative) | NON-AUTHORITATIVE | 0.3 - 0.6 |
| `CLARIFICATION_QUESTION` | Ask operator for missing information | UNCERTAIN | 0.2 - 0.4 |
| `NPC_DIALOGUE` | Generate in-character NPC speech | ATMOSPHERIC only | 0.7 - 1.1 |

### 2.1 Authority Level Definitions

| Level | Meaning | Provenance Tag |
|---|---|---|
| ATMOSPHERIC | Flavor text only; zero mechanical weight | `[NARRATIVE]` |
| UNCERTAIN | System is guessing/paraphrasing; operator must confirm | `[UNCERTAIN]` |
| INFORMATIONAL | Derived from Box state; not computed, not binding | `[DERIVED]` |
| NON-AUTHORITATIVE | Explains rules but does not adjudicate them | `[DERIVED]` |

No CallType may produce output tagged `[BOX]`. Only Box emits `[BOX]`-tagged data.

---

## 3. Per-CallType Schemas

### 3.1 COMBAT_NARRATION

**When used:** After Box resolves a turn and emits events. Lens assembles NarrativeBrief, builds PromptPack, calls Spark to narrate.

**Required Inputs (Lens must provide):**

| Field | Source | Required |
|---|---|---|
| `truth.action_type` | NarrativeBrief.action_type | YES |
| `truth.actor_name` | NarrativeBrief.actor_name (display name) | YES |
| `truth.target_name` | NarrativeBrief.target_name (display name) | if applicable |
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

**Forbidden Claims (Spark MUST NOT include):**

1. Specific damage numbers (e.g., "14 points of damage")
2. AC values (e.g., "AC 16")
3. Hit point values (e.g., "24 HP remaining")
4. Attack bonus values (e.g., "+7 to hit")
5. Difficulty class values (e.g., "DC 15")
6. Die roll results (e.g., "rolled a 17")
7. Dice notation (e.g., "2d6+3")
8. Rule citations (e.g., "PHB 145", "per the grapple rules")
9. Entity IDs (e.g., "goblin_02")
10. Grid coordinates (e.g., "moves to (3,5)")
11. Assertions about game state not provided in Truth channel (inventing facts)
12. Contradictions of outcome_summary (e.g., narrating a hit when outcome says miss)

**Output Shape:**

```
{
  "text": string,           // 2-4 sentences, prose narration
  "provenance": "[NARRATIVE]"
}
```

- Max length: 600 characters
- Min sentences: 2
- Max sentences: 4
- Format: prose (not JSON unless contract.json_mode is true)

---

### 3.2 OPERATOR_DIRECTIVE

**When used:** Operator inputs ambiguous text (e.g., "I want to rush the goblin"). Lens needs Spark to interpret intent into structured candidate actions for Box to evaluate. The operator must confirm before Box executes.

**Required Inputs (Lens must provide):**

| Field | Source | Required |
|---|---|---|
| `truth.scene_description` | Current scene context | YES |
| `truth.actor_name` | Active player/party member name | YES |
| `memory.session_facts` | Relevant entity names, positions, relationships | if available |
| `task.task_type` | `"operator_directive"` | YES |
| `task.operator_input` | Raw operator text string | YES |
| `task.valid_action_types` | List of mechanically valid action types for this context | YES |
| `contract.json_mode` | `true` | YES |
| `contract.json_schema` | CandidateAction schema | YES |

**Forbidden Claims:**

1. All mechanical assertions (damage, AC, HP, rolls, DCs)
2. Declaring any action as "legal" or "illegal" (only Box adjudicates)
3. Deciding outcomes (e.g., "the goblin dies")
4. Asserting facts not provided in Truth/Memory channels
5. Refusing to interpret (Axiom 1: Spark never refuses; Lens gates output)

**Output Shape:**

```json
{
  "candidates": [
    {
      "action_type": "attack",
      "target": "Goblin Scout",
      "confidence": 0.85,
      "reasoning": "Operator said 'rush' which implies melee engagement"
    }
  ],
  "needs_clarification": false,
  "clarification_prompt": null,
  "provenance": "[UNCERTAIN]"
}
```

- Max candidates: 3
- Max length: 400 characters total
- `confidence` is a Spark self-report, not an authority claim. Lens uses it for routing only.
- If `needs_clarification` is true, Lens routes to CLARIFICATION_QUESTION flow instead of Box.

---

### 3.3 SUMMARY

**When used:** At segment boundaries (end of combat, scene transitions, session end). Lens asks Spark to compress recent narrations and events into a stable summary for memory.

**Required Inputs (Lens must provide):**

| Field | Source | Required |
|---|---|---|
| `truth.scene_description` | Scene being summarized | YES |
| `memory.previous_narrations` | All narrations in the segment (up to token budget) | YES |
| `memory.session_facts` | Key facts from the segment | YES |
| `task.task_type` | `"session_summary"` | YES |
| `task.events_to_summarize` | Chronologically-ordered event list | YES |
| `contract.json_mode` | `true` | YES |
| `contract.json_schema` | SummaryOutput schema | YES |
| `contract.max_length_chars` | 800 | YES |

**Forbidden Claims:**

1. All mechanical assertions (damage numbers, AC, HP, rolls, DCs)
2. Inventing events that did not occur (not present in provided narrations/events)
3. Contradicting provided events (e.g., claiming a character survived when events show defeat)
4. Speculating about future events
5. Editorializing about player decisions

**Output Shape:**

```json
{
  "summary_text": "string (2-5 sentences)",
  "key_facts": ["fact_1", "fact_2"],
  "entities_involved": ["name_1", "name_2"],
  "unresolved_threads": ["thread_1"],
  "provenance": "[DERIVED]"
}
```

- Max summary length: 800 characters
- Max key_facts: 5
- Every fact in `key_facts` must be traceable to a provided narration or event. If a validator cannot find the source, the fact is flagged.

---

### 3.4 RULE_EXPLAINER

**When used:** Operator asks "how does grappling work?" or "what does flanking do?". Spark explains the rule in natural language. The explanation is non-authoritative: it helps the operator understand, but Box remains the sole adjudicator.

**Required Inputs (Lens must provide):**

| Field | Source | Required |
|---|---|---|
| `task.task_type` | `"rule_explainer"` | YES |
| `task.rule_topic` | The rule being asked about (e.g., "grapple", "flanking") | YES |
| `task.context_hint` | Optional current-situation context | NO |
| `contract.max_length_chars` | 600 | YES |
| `contract.required_provenance` | `"[DERIVED]"` | YES |

**Forbidden Claims:**

1. Asserting specific numerical bonuses/penalties as currently applying (that is Box's job)
2. Declaring an action legal or illegal in the current game state
3. Citing specific page numbers as authoritative (Box resolves rules, not Spark)
4. Contradicting D&D 3.5e RAW in spirit (Spark may be wrong; output is explicitly NON-AUTHORITATIVE)

**Output Shape:**

```
{
  "explanation": "string (2-6 sentences)",
  "caveat": "This is a general explanation. Actual resolution is handled by the rules engine.",
  "provenance": "[DERIVED]"
}
```

- Max length: 600 characters
- Must always include the caveat or equivalent disclaimer
- Format: prose (not JSON) by default

---

### 3.5 CLARIFICATION_QUESTION

**When used:** When the system cannot determine operator intent (ambiguous target, missing information, unclear action). This may be triggered by Lens directly (keyword parse failure) or by an OPERATOR_DIRECTIVE call that returns `needs_clarification: true`.

**Required Inputs (Lens must provide):**

| Field | Source | Required |
|---|---|---|
| `task.task_type` | `"clarification_question"` | YES |
| `task.ambiguity_type` | What is ambiguous (e.g., "target", "action_type", "spell_choice") | YES |
| `task.operator_input` | The original operator text | YES |
| `task.valid_options` | Bounded list of valid choices | if available |
| `truth.actor_name` | Active entity name | YES |
| `contract.max_length_chars` | 200 | YES |
| `contract.required_provenance` | `"[UNCERTAIN]"` | YES |

**Forbidden Claims:**

1. All mechanical assertions
2. Suggesting options not in `valid_options` (if provided)
3. Making assumptions about operator intent (must ASK, not guess)
4. Expressing frustration or judgment about the operator's input

**Output Shape:**

```
{
  "question": "string (1-2 sentences)",
  "options": ["option_1", "option_2", ...],
  "provenance": "[UNCERTAIN]"
}
```

- Max length: 200 characters
- Max options: 5
- If `valid_options` were provided in input, `options` in output must be a subset of them.

---

### 3.6 NPC_DIALOGUE

**When used:** When narration requires in-character NPC speech. Distinct from COMBAT_NARRATION because it targets a specific NPC persona with voice identity.

**Required Inputs (Lens must provide):**

| Field | Source | Required |
|---|---|---|
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

**Forbidden Claims:**

1. All mechanical assertions
2. NPC revealing information not provided in Memory channel (no inventing lore)
3. NPC making promises that imply mechanical outcomes (e.g., "I'll give you +2 to your rolls")
4. NPC contradicting session facts (e.g., being friendly when attitude is hostile)
5. Breaking character (meta-commentary, out-of-character statements)

**Output Shape:**

```
{
  "dialogue": "string (1-4 sentences, in-character speech)",
  "stage_direction": "string (optional, 1 sentence, physical action/tone)",
  "provenance": "[NARRATIVE]"
}
```

- Max dialogue length: 300 characters
- Max stage_direction length: 100 characters
- Stage direction is atmospheric only (e.g., "He crosses his arms and scowls.")

---

## 4. Evidence Discipline: Structured Reference Enforcement

### 4.1 The Core Rule

**Any mechanical-adjacent statement in Spark output must cite inputs from the frozen view (Truth channel).** If a Spark output references an outcome, condition, or entity state, that reference must be traceable to a specific field in the PromptPack's Truth or Memory channel.

### 4.2 What Counts as "Mechanical-Adjacent"

| Category | Examples | Required Citation |
|---|---|---|
| Outcome description | "the blow lands", "the spell fizzles" | `truth.outcome_summary` must confirm |
| Severity language | "grievous wound", "barely scratched" | `truth.severity` must be consistent |
| Condition reference | "knocked prone", "stunned" | `truth.condition_applied` must match |
| Defeat reference | "falls lifeless", "collapses" | `truth.target_defeated` must be `true` |
| Entity identification | "the goblin", "Kael" | `truth.actor_name` or `truth.target_name` must match |
| Weapon/spell reference | "with his longsword", "the fireball" | `truth.weapon_name` or `task.spell_name` must match |

### 4.3 Enforcement Flow

```
Spark Output
    |
    v
[GrammarShield] --- Regex scan for mechanical assertions
    |                (damage numbers, AC, HP, dice, etc.)
    |                FAIL -> retry (max 2) -> template fallback
    v
[ContradictionChecker] --- Compare output against NarrativeBrief
    |                       FAIL -> retry (1) or template fallback
    |                       (per WO-058 response policy)
    v
[EvidenceValidator] --- Verify mechanical-adjacent claims
    |                    trace back to Truth/Memory inputs
    |                    FAIL -> convert to CLARIFICATION_QUESTION
    |                    or reject and use template fallback
    v
[Provenance Tagger] --- Attach required provenance tag
    |
    v
Validated Output
```

### 4.4 Missing Evidence -> Automatic Conversion

If Spark output contains a mechanical-adjacent claim that cannot be traced to an input field:

1. **Severity: Low** (e.g., slight mismatch in weapon name) -> Annotate in logs, pass through with `[UNCERTAIN]` override
2. **Severity: Medium** (e.g., narrates wrong outcome direction) -> Reject, retry once with correction prompt
3. **Severity: High** (e.g., invents a condition, claims defeat when target is alive) -> Reject, fall back to template narration. Log violation for KILL-002 consideration.

If evidence is missing entirely (Lens failed to populate required Truth fields):
- The call is **not sent to Spark**. Lens returns a CLARIFICATION_QUESTION to the operator or falls back to template narration. This prevents Spark from generating in an under-constrained context.

---

## 5. Response Validator Specification (Logic-Level)

This section defines the validation logic a future `scripts/check_typed_call.py` could implement. No code is provided; this is a spec.

### 5.1 Validator Stages

**Stage 1: Schema Validation**
- Input: Raw Spark output text + CallType + OutputContract
- Check: Does the output parse according to the CallType's output shape?
- For JSON modes: valid JSON + schema match
- For prose modes: sentence count within bounds, character count within max_length_chars

**Stage 2: Forbidden Content Scan**
- Input: Parsed output text + CallType's forbidden_claims list
- Check: Run GrammarShield's MECHANICAL_PATTERNS regex set (8 patterns, see `grammar_shield.py:77-86`)
- Additional per-CallType forbidden patterns (e.g., RULE_EXPLAINER must not assert current-state bonuses)
- Output: list of violations (pattern_name, matched_text)

**Stage 3: Provenance Verification**
- Input: Output provenance tag + CallType's required_provenance
- Check: Does the output carry the correct provenance tag?
- COMBAT_NARRATION -> `[NARRATIVE]`
- OPERATOR_DIRECTIVE -> `[UNCERTAIN]`
- SUMMARY -> `[DERIVED]`
- RULE_EXPLAINER -> `[DERIVED]`
- CLARIFICATION_QUESTION -> `[UNCERTAIN]`
- NPC_DIALOGUE -> `[NARRATIVE]`

**Stage 4: Evidence Tracing (for COMBAT_NARRATION and NPC_DIALOGUE)**
- Input: Output text + PromptPack Truth/Memory channels
- Check: Every entity name mentioned in output must appear in Truth or Memory inputs
- Check: If output implies a specific outcome (hit/miss/defeat), it must align with `truth.outcome_summary`
- Check: If output mentions a condition, it must match `truth.condition_applied`

**Stage 5: Contradiction Detection**
- Input: Output text + NarrativeBrief
- Check: Run ContradictionChecker (WO-058) against the brief
- Detect: outcome reversal (narrate hit when brief says miss), entity swap, severity mismatch

### 5.2 Validator Output

```
{
  "call_type": "COMBAT_NARRATION",
  "valid": true | false,
  "stages": {
    "schema": {"pass": true},
    "forbidden_content": {"pass": true, "violations": []},
    "provenance": {"pass": true},
    "evidence": {"pass": true, "untraced_claims": []},
    "contradiction": {"pass": true, "matches": []}
  },
  "action": "ACCEPT" | "RETRY" | "TEMPLATE_FALLBACK" | "REJECT"
}
```

### 5.3 Action Resolution

| Condition | Action |
|---|---|
| All stages pass | ACCEPT |
| Schema fails (JSON parse, length) | RETRY (max 2) |
| Forbidden content detected | RETRY (max 2), then TEMPLATE_FALLBACK |
| Provenance mismatch | Fix automatically (re-tag) |
| Evidence tracing fails (low severity) | ACCEPT with annotation |
| Evidence tracing fails (medium severity) | RETRY (max 1) |
| Evidence tracing fails (high severity) | TEMPLATE_FALLBACK |
| Contradiction detected (Class A/B) | RETRY (max 1), then TEMPLATE_FALLBACK |
| Contradiction detected (Class C) | ACCEPT with annotation |
| Retries exhausted | TEMPLATE_FALLBACK + trigger KILL-005 counter |

---

## 6. Failure Modes and Correct Fallbacks

### 6.1 Failure Mode Table

| Failure | Detection | Fallback | Severity |
|---|---|---|---|
| **Ambiguous operator input** | IntentBridge parse fails, no keyword match | -> CLARIFICATION_QUESTION call to Spark | LOW |
| **Missing fact in Truth channel** | Lens detects required field is None | -> Do not call Spark. Use template narration or ask operator. | MEDIUM |
| **Spark invents facts** | Evidence tracing finds untraced entity/condition | -> RETRY once with "only reference provided facts" appended. If retry also fails, TEMPLATE_FALLBACK. | HIGH |
| **Spark contradicts outcome** | ContradictionChecker detects reversal | -> RETRY once with correction. If retry fails, TEMPLATE_FALLBACK. | HIGH |
| **Spark includes mechanical numbers** | GrammarShield regex match | -> RETRY (max 2) with stricter prompt. If exhausted, TEMPLATE_FALLBACK + KILL-002 consideration. | CRITICAL |
| **Spark refuses to generate** | Empty output or meta-commentary | -> TEMPLATE_FALLBACK. Axiom 1 violation logged. | HIGH |
| **Token overflow** | tokens_used > max_tokens * 1.1 | -> TEMPLATE_FALLBACK + KILL-003. | HIGH |
| **Latency exceeded** | elapsed > 10s | -> TEMPLATE_FALLBACK + KILL-004. | HIGH |
| **Context overload** | PromptPack exceeds model context window minus response reserve | -> Truncate Memory channel (lowest-relevance items first). If still over, truncate previous_narrations. Never truncate Truth/Task/Style/Contract. | MEDIUM |
| **Consecutive rejections > 3** | KILL-005 counter | -> Halt all Spark calls. Manual reset required. | CRITICAL |

### 6.2 The Golden Rule of Fallbacks

**Template narration is always safe.** Every CallType has a template-based fallback path that produces correct (if bland) output using only Box-provided data. Spark is an enhancement, never a dependency. If Spark is unavailable, slow, or misbehaving, the system degrades to templates without loss of mechanical correctness.

For non-narration CallTypes:
- OPERATOR_DIRECTIVE -> Fall back to keyword-only IntentBridge parsing (existing path)
- SUMMARY -> Fall back to chronological event list (no compression)
- RULE_EXPLAINER -> Fall back to "Please consult the Player's Handbook" stub
- CLARIFICATION_QUESTION -> Fall back to hardcoded clarification templates (existing in session_orchestrator.py)
- NPC_DIALOGUE -> Fall back to "[NPC name] speaks." stub

---

## 7. Example I/O Pairs

### Example 1: COMBAT_NARRATION - CORRECT

**Input (PromptPack Truth):**
```
action_type: "attack_hit"
actor_name: "Kael"
target_name: "Goblin Scout"
outcome_summary: "Kael hits Goblin Scout with longsword"
severity: "moderate"
weapon_name: "longsword"
damage_type: "slashing"
target_defeated: false
```

**Output (ACCEPTED):**
```
Kael's longsword bites into the goblin scout's shoulder, drawing a grunt
of pain. The creature stumbles back a step, clutching the wound, but
keeps its footing.

[NARRATIVE]
```

**Why accepted:** References only provided entities (Kael, Goblin Scout), weapon (longsword), and damage type (slashing implied). Severity "moderate" is consistent with "draws a grunt of pain" and "stumbles but keeps footing." No mechanical numbers. Provenance tag correct.

---

### Example 2: COMBAT_NARRATION - REJECTED (mechanical assertion)

**Input (same as Example 1)**

**Output (REJECTED):**
```
Kael swings his longsword, dealing 14 points of slashing damage to the
Goblin Scout. The goblin's AC of 15 wasn't enough to deflect the blow.

[NARRATIVE]
```

**Why rejected:** Contains "14 points of slashing damage" (damage_quantity pattern), "AC of 15" (armor_class pattern). GrammarShield catches both. Action: RETRY with stricter prompt.

---

### Example 3: COMBAT_NARRATION - REJECTED (contradiction)

**Input (PromptPack Truth):**
```
action_type: "attack_miss"
outcome_summary: "Kael misses Goblin Scout with longsword"
severity: "minor"
target_defeated: false
```

**Output (REJECTED):**
```
Kael's longsword finds its mark, slicing through the goblin's defenses.
The scout howls as the blade draws blood.

[NARRATIVE]
```

**Why rejected:** Outcome says "miss" but narration describes a hit ("finds its mark", "slicing through defenses", "draws blood"). ContradictionChecker detects outcome reversal. Action: RETRY with correction "The attack MISSED. Narrate a miss."

---

### Example 4: OPERATOR_DIRECTIVE - CORRECT

**Input:**
```
operator_input: "I want to rush the big one"
valid_action_types: ["attack", "bull_rush", "move", "charge"]
actor_name: "Kael"
scene_description: "Dusty tavern. Two goblins and an ogre."
```

**Output (ACCEPTED):**
```json
{
  "candidates": [
    {
      "action_type": "bull_rush",
      "target": "Ogre",
      "confidence": 0.7,
      "reasoning": "'Rush' suggests bull rush maneuver against largest enemy"
    },
    {
      "action_type": "charge",
      "target": "Ogre",
      "confidence": 0.6,
      "reasoning": "'Rush' could mean charge attack"
    }
  ],
  "needs_clarification": true,
  "clarification_prompt": "Do you want to bull rush or charge the ogre?",
  "provenance": "[UNCERTAIN]"
}
```

**Why accepted:** Candidates use only valid_action_types. Target "Ogre" matches scene description. No mechanical assertions. Correctly identifies ambiguity and requests clarification.

---

### Example 5: CLARIFICATION_QUESTION - CORRECT

**Input:**
```
ambiguity_type: "target"
operator_input: "attack the goblin"
valid_options: ["Goblin Scout", "Goblin Shaman"]
actor_name: "Kael"
```

**Output (ACCEPTED):**
```
{
  "question": "Which goblin do you want to attack?",
  "options": ["Goblin Scout", "Goblin Shaman"],
  "provenance": "[UNCERTAIN]"
}
```

**Why accepted:** Options are subset of valid_options. No assumptions made. Concise question.

---

### Example 6: SUMMARY - REJECTED (invents facts)

**Input:**
```
events_to_summarize: [
  "Kael attacks Goblin Scout and hits.",
  "Goblin Scout attacks Kael and misses.",
  "Kael attacks Goblin Scout and defeats it."
]
```

**Output (REJECTED):**
```json
{
  "summary_text": "Kael defeated the goblin scout in a fierce duel. The goblin shaman fled the tavern in terror.",
  "key_facts": ["Goblin Scout defeated by Kael", "Goblin Shaman fled"],
  "entities_involved": ["Kael", "Goblin Scout", "Goblin Shaman"],
  "unresolved_threads": [],
  "provenance": "[DERIVED]"
}
```

**Why rejected:** "Goblin Shaman fled the tavern" appears nowhere in the provided events. Evidence tracing finds "Goblin Shaman" in `entities_involved` and "fled" in `key_facts` with no source event. High severity: fact invention. Action: RETRY with "only summarize events that were explicitly provided."

---

## 8. Integration with Existing Architecture

### 8.1 Where CallType Lives in the Stack

```
SessionOrchestrator (runtime)
    |
    |-- determines CallType based on context
    |
    v
PromptPackBuilder (lens)
    |
    |-- populates task.task_type from CallType mapping:
    |     COMBAT_NARRATION   -> "narration"
    |     OPERATOR_DIRECTIVE -> "operator_directive"  (v2 task type)
    |     SUMMARY            -> "session_summary"     (v2 task type)
    |     RULE_EXPLAINER     -> "rule_explainer"       (v2 task type)
    |     CLARIFICATION_QUESTION -> "clarification"    (v2 task type)
    |     NPC_DIALOGUE       -> "npc_dialogue"
    |
    v
PromptPack.serialize() (schemas)
    |
    v
SparkRequest (spark)
    |
    v
SparkAdapter.generate() (spark)
    |
    v
SparkResponse (spark)
    |
    v
Response Validator (lens)
    |-- GrammarShield (stage 2: forbidden content)
    |-- ContradictionChecker (stage 5: contradiction)
    |-- EvidenceValidator (stage 4: future, per this spec)
    |
    v
Validated output or fallback
```

### 8.2 PromptPack v1 Compatibility

The current PromptPack v1 supports two task types: `narration` and `npc_dialogue`. This contract adds four additional CallTypes that map to v2 task types. The PromptPack schema must be extended (in a future work order) to:

1. Add `"operator_directive"`, `"session_summary"`, `"rule_explainer"`, `"clarification"` to the valid task types set
2. Add per-task fields (e.g., `task.operator_input`, `task.rule_topic`, `task.events_to_summarize`)
3. Extend OutputContract to support per-CallType json_schema references

This extension is additive and backward-compatible. Existing v1 PromptPacks continue to work.

### 8.3 Stop Conditions Met

- No middleware outside the runtime process: all validation runs in Lens boundary (GrammarShield, ContradictionChecker, EvidenceValidator).
- Narration never decides mechanics: all CallTypes are constrained to atmospheric/uncertain/informational output. Box remains sole mechanical authority.
- No scope expansion into GUI or full prompt framework: this spec defines typed calls only, within the existing PromptPack wire protocol.

---

## 9. Open Questions for Future Work Orders

1. **EvidenceValidator implementation** — Stage 4 (evidence tracing) is specified here at logic level. A future WO should implement it as a validator class in `aidm/lens/` or `aidm/narration/`.
2. **V2 task types in PromptPack** — Extending `V1_TASK_TYPES` to include the four new CallTypes requires a schema migration WO.
3. **OPERATOR_DIRECTIVE tuning** — The confidence-based routing threshold (when does Lens auto-accept vs ask for clarification?) needs playtest data to calibrate.
4. **RULE_EXPLAINER knowledge boundary** — How much D&D 3.5e knowledge can we assume the LLM has? Should Lens provide rule text in Memory channel, or rely on the model's training data? Providing rule text is safer but costs tokens.

---

*This research document fulfills WO-RQ-LLM-CALL-TYPING-01 acceptance criteria 1-6.*