# LLM Query Interface Design
## Design Specification for Qwen3 8B Integration with AIDM Indexed Memory

**Document Type:** Design / Architecture Specification
**Source Authority:** WO-RQ-LLM-002, RQ-LLM-001 (Indexed Memory), R1 Technology Stack Validation
**Target Phase:** M3 (LLM Narration Integration)
**Date:** 2026-02-11
**Status:** DESIGN (Non-binding until M3 implementation approval)
**Agent:** Agent A (LLM & Systems Architect)

---

## Purpose

This document defines the **query interface between AIDM and Qwen3 8B LLM** for indexed memory retrieval, narration generation, and structured output requests. It specifies prompt templates, system prompt architecture, structured output enforcement, GuardedNarrationService integration, and error handling.

**What This Document Defines:**
- Prompt template structure (narration, query, structured output)
- System prompt architecture (world state, character context, tone, constraints)
- Structured output enforcement (GB

NF grammar, stop sequences, fallback parsing)
- GuardedNarrationService integration (template vs LLM decision logic)
- Error handling (unparseable output, off-topic, constraint violations)
- Acceptance criteria (query accuracy, JSON parsing, constraint adherence)

**What This Document Does NOT Define:**
- Implementation details (no code changes to GuardedNarrationService or llamacpp_adapter)
- Model fine-tuning (Qwen3 8B used as-is)
- RAG architecture (pure prompt engineering for R0/M3)
- Function calling (Qwen3 8B does not support OpenAI-style function calling)

---

## 1. Prompt Templates

### 1.1 Narration Template

**Purpose:** Generate descriptive flavor text for combat, exploration, social, and environmental scenes.

**Input:**
- Player action (attack, movement, dialogue)
- World state context (active NPCs, environment, scene)
- Recent events (last 1-3 turns)

**Output:** Natural language narration (2-4 sentences, ≤100 tokens)

**Template Structure:**
```
SYSTEM CONTEXT:
{system_prompt}

WORLD STATE:
{world_state_summary}

RECENT EVENTS:
{last_3_events}

NARRATION REQUEST:
Player action: {player_action}
Environment: {environment_description}

Generate 2-4 sentences of narration describing this action. Use fantasy genre tone. Do not invent abilities, stats, or mechanics. Describe only what is visible and dramatic.
```

**Example Prompt:**
```
SYSTEM CONTEXT:
You are the narrator for a D&D 3.5e campaign. Describe player actions with dramatic flair while respecting established world state.

WORLD STATE:
- PC: Theron (Fighter, HP 45/50)
- NPCs: Goblin Archer (HP 12/12, 30ft away)
- Environment: Forest clearing, dusk

RECENT EVENTS:
- Turn 10: Theron drew longsword, advanced 20ft
- Turn 11: Goblin fired arrow, missed

NARRATION REQUEST:
Player action: Theron attacks Goblin with longsword (HIT, 8 damage)
Environment: Forest clearing, fading sunlight

Generate 2-4 sentences of narration describing this action. Use fantasy genre tone. Do not invent abilities, stats, or mechanics. Describe only what is visible and dramatic.
```

**Expected Output:**
```
You surge forward, longsword gleaming in the fading sunlight. The goblin barely has time to nock another arrow before your blade crashes through its guard. The creature stumbles backward with a pained shriek as blood wells from the wound.
```

**Token Budget:** ≤500 tokens total (system + context + request + output)

---

### 1.2 Query Template

**Purpose:** Retrieve entity IDs, event IDs, or relationships from indexed memory.

**Input:**
- Natural language query
- Frozen memory snapshot (SessionLedgerEntry, EvidenceLedger, ThreadRegistry)

**Output:** Structured JSON response with entity_ids, event_ids, summary

**Template Structure:**
```
SYSTEM CONTEXT:
{system_prompt}

INDEXED MEMORY:
{serialized_memory_context}

QUERY: {natural_language_query}

INSTRUCTIONS: Extract all relevant entries matching the query. Return ONLY valid JSON matching this schema:
{
  "entity_ids": ["entity_1", "entity_2"],
  "event_ids": ["event_001", "event_005"],
  "summary": "Brief summary of findings"
}

Output ONLY the JSON, no other text.
```

**Example Prompt:**
```
SYSTEM CONTEXT:
You are a memory retrieval system for D&D campaign records. Extract facts only from indexed memory. Do not invent or infer.

INDEXED MEMORY:
Session Ledger (Session 10):
- Facts: ["Theron befriended Merchant Bob", "Party explored ruined temple"]

Evidence Ledger:
- ev_001: character=theron, type=loyalty, description="Defended ally in combat"
- ev_007: character=theron, type=loyalty, description="Refused to abandon merchant"

Thread Registry:
- clue_merchant_bob_rumors: status=active

QUERY: What evidence exists for Theron showing loyalty?

INSTRUCTIONS: Extract all relevant entries matching the query. Return ONLY valid JSON matching this schema:
{
  "entity_ids": ["entity_1", "entity_2"],
  "event_ids": ["event_001", "event_005"],
  "summary": "Brief summary of findings"
}

Output ONLY the JSON, no other text.
```

**Expected Output:**
```json
{
  "entity_ids": ["theron"],
  "event_ids": ["ev_001", "ev_007"],
  "summary": "Theron showed loyalty by defending allies in combat and refusing to abandon the merchant."
}
```

**Token Budget:** ≤800 tokens total (system + memory + query + output)

---

### 1.3 Structured Output Template

**Purpose:** Generate NPC stats, item properties, or spell effects as JSON conforming to schema.

**Input:**
- Request for structured data (NPC stat block, item properties)
- Schema definition

**Output:** JSON conforming to provided schema

**Template Structure:**
```
SYSTEM CONTEXT:
{system_prompt}

GENERATION REQUEST: {entity_type} - {description}

SCHEMA:
{json_schema}

CONSTRAINTS:
- All fields are required
- Use D&D 3.5e rules only (no invented abilities)
- Stay within provided stat ranges
- Use standard D&D creature types

Output ONLY valid JSON matching the schema, no other text.
```

**Example Prompt:**
```
SYSTEM CONTEXT:
You generate D&D 3.5e creature stat blocks. Follow D&D 3.5e SRD rules exactly. Do not invent abilities.

GENERATION REQUEST: NPC Goblin Warrior

SCHEMA:
{
  "name": "string",
  "hp": "number (1-20 for CR 1/3)",
  "ac": "number (10-16)",
  "attack_bonus": "number (+0 to +3)",
  "species": "string (D&D race)",
  "description": "string (1 sentence)"
}

CONSTRAINTS:
- All fields are required
- Use D&D 3.5e rules only (no invented abilities)
- Stay within provided stat ranges
- Use standard D&D creature types

Output ONLY valid JSON matching the schema, no other text.
```

**Expected Output:**
```json
{
  "name": "Goblin Warrior",
  "hp": 6,
  "ac": 15,
  "attack_bonus": 2,
  "species": "Goblin",
  "description": "A short, wiry humanoid with leathery green skin and yellowed eyes."
}
```

**Token Budget:** ≤600 tokens total (system + request + schema + output)

---

## 2. System Prompt Architecture

### 2.1 System Prompt Components

**Core Structure:**
```
You are {role} for a D&D 3.5e campaign.

WORLD STATE:
{active_npcs}
{player_location}
{active_threads}
{recent_events}

CHARACTER CONTEXT:
{pc_names_classes_levels}
{current_hp_status}
{equipped_items}

TONE GUIDANCE:
- Fantasy genre (no modern slang, sci-fi elements)
- D&D 3.5e rules adherence
- Descriptive but concise (2-4 sentences)

CONSTRAINTS:
- Do not invent abilities, spells, feats not in D&D 3.5e SRD
- Do not assign HP values, ability scores, or stats (use provided values only)
- Do not introduce new NPCs unless explicitly requested
- Respect existing world state (do not contradict established facts)
```

### 2.2 World State Summary Serialization

**Active NPCs:**
```
Active NPCs:
- {npc_name} ({species}, HP {current}/{max}, {status})
- ...
```

**Player Location:**
```
Location: {scene_name} ({scene_type})
```

**Active Threads:**
```
Active Threads:
- {thread_id}: {thread_description} (status: {status})
```

**Recent Events (Last 3-5 Turns):**
```
Recent Events:
- Turn {n}: {event_summary}
- Turn {n-1}: {event_summary}
- Turn {n-2}: {event_summary}
```

### 2.3 Character Context Injection

```
Player Characters:
- {pc_name} (Level {level} {class})
  - HP: {current}/{max}
  - Status: {status_effects}
  - Equipment: {weapon}, {armor}
```

### 2.4 Constraint Injection

**D&D 3.5e Rule Boundaries:**
```
CONSTRAINTS:
1. No ability invention: Use only D&D 3.5e SRD abilities, spells, feats
2. No stat assignment: Never generate HP, AC, attack bonuses, ability scores
3. No NPC invention: Only describe NPCs already in world state
4. No contradiction: Respect all established facts in memory
5. No mechanical claims: Describe outcomes, do not compute mechanics
```

### 2.5 Token Budget for System Prompt

**Target:** ≤1000 tokens total
- Role + tone guidance: ~150 tokens
- World state summary: ~300 tokens
- Character context: ~200 tokens
- Constraints: ~100 tokens
- Buffer: ~250 tokens

**Pruning Strategy:** If system prompt exceeds 1000 tokens:
1. Limit recent events to last 3 turns
2. Limit active NPCs to current scene only
3. Limit active threads to highest priority (status=active)

---

## 3. Structured Output Enforcement

### 3.1 GBNF Grammar Constraints

**Purpose:** Enforce JSON schema compliance using llama.cpp GBNF (Grammar-Based Finite) constraints.

**NPC Stat Block Grammar:**
```gbnf
root ::= npc-stat-block
npc-stat-block ::= "{" ws
  "\"name\":" ws string "," ws
  "\"hp\":" ws number "," ws
  "\"ac\":" ws number "," ws
  "\"attack_bonus\":" ws number "," ws
  "\"species\":" ws string "," ws
  "\"description\":" ws string ws
"}"

string ::= "\"" [^"]* "\""
number ::= [0-9]+
ws ::= [ \t\n]*
```

**Item Properties Grammar:**
```gbnf
root ::= item-properties
item-properties ::= "{" ws
  "\"name\":" ws string "," ws
  "\"type\":" ws string "," ws
  "\"weight\":" ws number "," ws
  "\"value\":" ws number "," ws
  "\"description\":" ws string "," ws
  "\"magical\":" ws boolean ws
"}"

string ::= "\"" [^"]* "\""
number ::= [0-9]+
boolean ::= "true" | "false"
ws ::= [ \t\n]*
```

**Query Result Grammar:**
```gbnf
root ::= query-result
query-result ::= "{" ws
  "\"entity_ids\":" ws string-array "," ws
  "\"event_ids\":" ws string-array "," ws
  "\"summary\":" ws string ws
"}"

string-array ::= "[" ws (string ("," ws string)*)? ws "]"
string ::= "\"" [^"]* "\""
ws ::= [ \t\n]*
```

### 3.2 Stop Sequence Definition

**JSON Response Stop Sequences:**
- Primary: `}\n` (closing brace + newline)
- Fallback: `}\n\n` (closing brace + double newline)

**Rationale:** Ensures LLM stops after completing JSON object, preventing extra commentary.

### 3.3 Fallback Parsing Logic

**When LLM output deviates from schema:**

1. **Partial JSON Parsing**
   - Extract valid fields using lenient JSON parser (json5)
   - Use schema defaults for missing fields
   - Log warning with missing field names

2. **Error Detection**
   - Malformed JSON: Invalid syntax, unclosed braces
   - Missing required fields: Schema validation fails
   - Invalid field types: String where number expected

3. **Retry Logic**
   - Retry 1: Emphasize "Output ONLY valid JSON matching schema"
   - Retry 2: Provide example output in prompt
   - Fallback: Use template or return error to caller

**Expected JSON Parsing Success Rate:** >95%

---

## 4. GuardedNarrationService Integration

### 4.1 Template vs LLM Decision Logic

**Decision Tree:**
```
IF narration_mode == "template_only":
    RETURN template_narration()

IF world_state.complexity < threshold:  # ≤3 active entities
    RETURN template_narration()

IF LLM_available == False:
    RETURN template_narration()

IF player_action in [ATTACK, MOVE, USE_ITEM]:
    # Hybrid: mechanics via template, flavor via LLM
    template_mechanics = generate_mechanics_template()
    llm_flavor = generate_llm_flavor()
    RETURN concatenate(template_mechanics, llm_flavor)

ELSE:
    # Pure LLM for exploration, social, environmental
    RETURN generate_llm_narration()
```

**When to Use Templates:**
- Deterministic mechanics (damage dealt, HP changes, status effects)
- Simple actions (basic attack, standard movement)
- LLM unavailable (timeout, model load failure)

**When to Use LLM:**
- Descriptive flavor (combat descriptions, environment, NPC reactions)
- Complex social interactions (dialogue, persuasion)
- Environmental descriptions (scene setting, atmosphere)

**Hybrid Mode (Recommended):**
- Mechanics: Template (deterministic, always correct)
- Flavor: LLM (generative, atmospheric)
- Output: `"{template_mechanics} {llm_flavor}"`

### 4.2 World State Passing

**Serialization Format:**
```python
def serialize_world_state_for_llm(world_state: WorldState) -> str:
    """Serialize WorldState snapshot to LLM prompt context.

    Returns:
        Markdown-formatted world state summary (≤2000 tokens)
    """
    # Filter to current scene entities only
    active_npcs = [npc for npc in world_state.entities
                   if npc.scene_id == current_scene_id]

    # Limit recent events to last 3 turns
    recent_events = get_last_n_events(event_log, n=3)

    # Format as markdown
    return f"""
WORLD STATE:
Active NPCs: {format_npcs(active_npcs)}
Location: {world_state.current_scene}
Active Threads: {format_threads(active_threads)}

RECENT EVENTS:
{format_events(recent_events)}
"""
```

**Token Budget:** ≤2000 tokens (avoid context window overflow)

### 4.3 LLM Invocation Interface

**Method Signature:**
```python
def generate_narration(
    action: PlayerAction,
    world_state: WorldState,
    narration_type: str = "combat"  # combat, exploration, social, environmental
) -> str:
    """Generate LLM narration for player action.

    Args:
        action: Player action to narrate
        world_state: Current world state snapshot
        narration_type: Type of narration (affects tone/style)

    Returns:
        Natural language narration (2-4 sentences)

    Raises:
        NarrationError: If LLM fails, caller should fallback to template
    """
```

**Error Handling:**
- Timeout (5s GPU, 10s CPU): Fallback to template
- Malformed output: Retry once, then fallback
- Off-topic response: Reject, retry with stricter constraints, then fallback

---

## 5. Error Handling

### 5.1 Unparseable Output

**Symptom:** LLM returns malformed JSON or non-JSON text

**Detection:**
```python
try:
    result = json.loads(llm_output)
except json.JSONDecodeError:
    # Unparseable output detected
```

**Response:**
1. **Retry 1:** Add "Output ONLY valid JSON matching schema, no other text"
2. **Retry 2:** Provide example output: `"Example: {\"name\": \"Goblin\", \"hp\": 6}"`
3. **Fallback:** Use template narration or return error to caller

**Expected Rate:** <5%

### 5.2 Off-Topic Response

**Symptom:** LLM hallucinates abilities, invents NPCs, contradicts world state

**Detection:**
```python
def detect_off_topic(llm_output: str, world_state: WorldState) -> bool:
    """Detect hallucinations and constraint violations."""
    # Check for unknown ability names
    unknown_abilities = find_unknown_abilities(llm_output)
    if unknown_abilities:
        return True

    # Check for unknown NPC names
    unknown_npcs = find_unknown_npcs(llm_output, world_state)
    if unknown_npcs:
        return True

    # Check for contradictions
    contradictions = find_contradictions(llm_output, world_state)
    if contradictions:
        return True

    return False
```

**Response:**
1. **Reject:** Discard LLM output
2. **Retry:** Add constraint reminder: "Do not invent abilities, NPCs, or contradict world state"
3. **Fallback:** Use template narration

**Expected Rate:** <10%

### 5.3 Constraint Violation

**Symptom:** LLM assigns HP values, changes stats, invents mechanics

**Detection:**
```python
def detect_constraint_violation(llm_output: str) -> bool:
    """Detect mechanical claims in narration."""
    # Check for HP value mentions
    if re.search(r'\b\d+\s*(hp|hit points)', llm_output, re.I):
        return True

    # Check for ability score mentions
    if re.search(r'(strength|dexterity|constitution)\s*\d+', llm_output, re.I):
        return True

    # Check for stat assignments
    if re.search(r'(AC|attack bonus|saving throw)\s*\d+', llm_output, re.I):
        return True

    return False
```

**Response:**
1. **Reject:** Discard LLM output
2. **Retry:** Add constraint enforcement: "Do NOT assign HP, stats, or mechanics. Describe only."
3. **Fallback:** Use template narration

**Expected Rate:** <5%

### 5.4 Retry Budget

**Max Retry Attempts:** 2 retries per LLM invocation (3 total attempts)

**Timeout Per Attempt:**
- GPU: 5 seconds
- CPU: 10 seconds

**Total Budget Per Narration:**
- GPU: 15 seconds (3 × 5s)
- CPU: 30 seconds (3 × 10s)

**Fallback Decision:**
- After 2 retries: Always fallback to template narration
- After timeout: Immediate fallback (no retry)

---

## 6. Acceptance Criteria

### 6.1 Query Accuracy

**Metric:** LLM retrieves correct entity IDs, event IDs, relationships

**Success Threshold:** >85% for complex queries

**Test Corpus:**
- 50+ queries total
- 20 entity lookup queries ("Find all NPCs in tavern scene")
- 20 event search queries ("Find all events where Fighter attacked Goblin")
- 10 relationship queries ("What evidence exists for Theron's loyalty?")

**Measurement:**
- Precision: Fraction of retrieved IDs that are correct
- Recall: Fraction of correct IDs that were retrieved
- F1 Score: Harmonic mean of precision and recall
- Target: F1 >0.85

### 6.2 Context Window Management

**Metric:** No context window overflow for 50-turn sessions

**Success Threshold:** System prompt + world state + query ≤ 8000 tokens (Qwen3 8B limit)

**Test Corpus:**
- 5 campaigns with 50+ turns each
- Measure peak token usage per turn

**Pruning Strategy:**
- If context exceeds 7500 tokens: Prune recent events to last 3 turns
- If context exceeds 8000 tokens: Prune active NPCs to current scene only

### 6.3 JSON Parsing Success

**Metric:** LLM outputs valid JSON conforming to schema

**Success Threshold:** >95% for structured output requests

**Test Corpus:**
- 50+ structured output requests
- 20 NPC stat blocks
- 15 item properties
- 15 query results

**Measurement:**
- JSON parse success rate (valid syntax)
- Schema validation success rate (all required fields present)
- Target: >95% for both metrics

### 6.4 Constraint Adherence

**Metric:** LLM respects D&D 3.5e rules and world state

**Success Threshold:** 100% constraint adherence (0 violations in 100 narrations)

**Test Corpus:**
- 100 narrations across all types (combat, exploration, social, environmental)

**Measurement:**
- Invented abilities: 0 occurrences
- HP value assignments: 0 occurrences
- Stat changes: 0 occurrences
- Invented NPCs (unless requested): 0 occurrences
- World state contradictions: 0 occurrences

**Violation Response:** Any violation triggers design revision (stricter constraints, revised prompts)

---

## Integration Notes

### Files Requiring Updates (Implementation Phase)

**aidm/narration/guarded_narration_service.py:**
- Add `generate_llm_narration()` method
- Add template vs LLM decision logic (section 4.1)
- Add world state serialization (section 4.2)
- Add error handling (section 5)

**aidm/spark/llamacpp_adapter.py:**
- Verify grammar constraint support exists (GBNF)
- Add stop sequence configuration
- Add timeout handling per section 5.4

**aidm/schemas/campaign_memory.py:**
- Add `QueryResult` schema (entity_ids, event_ids, summary)
- No changes to existing schemas

---

## Appendix: Example Prompts

### A.1 Combat Narration Example

**Prompt:**
```
You are the narrator for a D&D 3.5e campaign. Describe player actions with dramatic flair.

WORLD STATE:
- PC: Theron (Fighter, HP 45/50)
- NPC: Goblin Archer (HP 12/12)
- Location: Forest clearing, dusk

NARRATION REQUEST:
Player action: Theron attacks Goblin with longsword (HIT, 8 damage)

Generate 2-4 sentences. Do not invent abilities or stats.
```

**Output:**
```
You surge forward, longsword gleaming in the fading sunlight. The goblin barely has time to nock another arrow before your blade crashes through its guard. The creature stumbles backward with a pained shriek as blood wells from the wound.
```

### A.2 Entity Query Example

**Prompt:**
```
You are a memory retrieval system. Extract facts only from indexed memory.

INDEXED MEMORY:
Evidence Ledger:
- ev_001: character=theron, type=loyalty, description="Defended ally in combat"
- ev_007: character=theron, type=loyalty, description="Refused to abandon merchant"

QUERY: What evidence exists for Theron showing loyalty?

Output ONLY valid JSON:
{
  "entity_ids": [...],
  "event_ids": [...],
  "summary": "..."
}
```

**Output:**
```json
{
  "entity_ids": ["theron"],
  "event_ids": ["ev_001", "ev_007"],
  "summary": "Theron showed loyalty by defending allies and refusing to abandon merchant."
}
```

### A.3 Off-Topic Detection Example

**Prompt:**
```
[Same as A.1 combat narration]
```

**Bad Output (Constraint Violation):**
```
Your longsword crackles with lightning energy as you cast Shocking Grasp. The goblin takes 15 damage and is reduced to -3 HP.
```

**Detection:** Invented ability ("lightning energy", "Shocking Grasp"), HP assignment ("15 damage", "-3 HP")

**Response:** REJECT → RETRY with constraint reminder → FALLBACK to template

---

**END OF LLM QUERY INTERFACE DESIGN**

**Date:** 2026-02-11
**Agent:** Agent A (LLM & Systems Architect)
**Phase:** M3 Preparation (Design-Only)
**Deliverable:** LLM_QUERY_INTERFACE.md
**Status:** COMPLETE (awaiting PM review)
**Authority:** DESIGN (non-binding until M3 implementation approval)
