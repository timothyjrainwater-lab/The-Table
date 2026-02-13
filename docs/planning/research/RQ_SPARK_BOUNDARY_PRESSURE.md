# RQ-SPARK-BOUNDARYPRESSURE-01: Boundary Pressure as a First-Class Runtime Signal

**Work Order:** WO-RQ-SPARK-BOUNDARYPRESSURE-01
**Status:** RESEARCH COMPLETE
**Date:** 2026-02-13
**Agent:** Sonnet A (Research)
**Authority:** Research-only. No code, no schema changes, no test modifications.

---

## 1. Problem Statement

A veteran DM at a physical table unconsciously signals boundary stress through cadence shifts, pauses, hedging language, and explicit questions. These are perceptible human signals that communicate "I'm not sure about this" or "this is outside my authority" before a ruling is made.

When an LLM replaces or assists the DM (Spark in AIDM), these signals vanish. The LLM either answers confidently (potentially hallucinating mechanics or facts) or refuses entirely. There is no intermediate signal. The current kill switch suite (KILL-001 through KILL-006) catches *post-hoc* violations after generation. Boundary pressure is the *pre-generation* and *mid-generation* analog: detecting conditions likely to produce violations before they reach the player.

**Core insight:** Boundary pressure is the measurable gap between what Spark is asked to do and what it can do safely within its authority.

---

## 2. Definition: Boundary Pressure

### 2.1 Formal Definition

**Boundary pressure** is a runtime-computed signal indicating the risk that a Spark generation call will violate the Box/Spark authority boundary. It is emitted *before* or *instead of* a Spark call, not after.

Boundary pressure does not grant Spark authority. It does the opposite: it measures how close Spark is to exceeding its authority and triggers defensive responses (questions, hedges, hard stops) before a violation can occur.

### 2.2 Signal Properties

| Property | Value |
|----------|-------|
| **Emitted by** | Lens layer (context assembly + intent bridge) |
| **Consumed by** | Session Orchestrator, Narration Service, TTS pipeline |
| **Lifetime** | Per-turn. Recomputed each turn cycle. |
| **Authority** | Zero. Pressure is informational. It cannot modify game state. |
| **Persistence** | Logged to event stream. Not stored in WorldState. |
| **Fail direction** | Closed. Unknown pressure = maximum pressure = hard stop. |

### 2.3 Minimal Schema

```
BoundaryPressure:
  trigger:       PressureTrigger     # enum (see Section 3)
  level:         PressureLevel       # GREEN / YELLOW / RED
  source_module: str                 # e.g. "context_assembler", "intent_bridge"
  turn_number:   int                 # turn when detected
  detail:        str                 # human-readable explanation (1 line)
  confidence:    float               # 0.0-1.0 how certain the detector is
```

```
PressureLevel:
  GREEN  = "green"    # No pressure. Spark can generate freely.
  YELLOW = "yellow"   # Elevated pressure. Spark generates with hedge/question.
  RED    = "red"      # Critical pressure. Spark does NOT generate. Hard stop.
```

**Design note:** `confidence` is included because some detectors are heuristic (e.g., ambiguity detection). A detector that is 60% sure there's ambiguity emits YELLOW; one that is 95% sure emits RED. This allows tuning without changing the trigger taxonomy.

---

## 3. Trigger Taxonomy

Four pressure triggers, grounded in AIDM's existing authority architecture.

### 3.1 MISSING_FACT: Missing Fact Pressure

**Definition:** Spark is asked to narrate or interpret something that depends on a fact not present in the Lens index.

**Detection point:** ContextAssembler (`aidm/lens/context_assembler.py`) during context retrieval, or IntentBridge (`aidm/interaction/intent_bridge.py`) during name resolution.

**Examples:**
- Player says "I attack the shopkeeper" but no entity named "shopkeeper" exists in WorldState
- Narration request references a spell effect but no `spell_cast` event is in the event log
- ContextAssembler retrieves zero session facts for a narration that needs historical context

**Existing partial coverage:**
- IntentBridge already emits `ClarificationRequest` when name resolution fails (zero candidates). This is an implicit MISSING_FACT at RED level.
- ContextAssembler's `retrieve()` returns items with `dropped=True` when budget is exceeded, but does not signal when *zero* relevant items exist.

**Fail-closed behavior:**

| Level | Condition | Response |
|-------|-----------|----------|
| GREEN | All referenced facts present in Lens | Spark generates normally |
| YELLOW | Some facts missing but Spark can hedge | Spark generates with explicit uncertainty marker |
| RED | Critical facts missing (target unknown, action undefined) | Hard stop: question to player, no Spark call |

### 3.2 AUTHORITY: Authority Pressure (Mechanics Boundary)

**Definition:** Spark's prompt or context contains elements that would require mechanical authority to answer correctly, but Spark has zero mechanical authority.

**Detection point:** NarrativeBrief construction in SessionOrchestrator (`aidm/runtime/session_orchestrator.py`), or prompt assembly in GuardedNarrationService (`aidm/narration/guarded_narration_service.py`).

**Examples:**
- Player asks "Can I reach the goblin from here?" (requires geometry engine computation, not Spark narration)
- Player asks "What's my attack bonus?" (requires entity stat lookup, not LLM generation)
- Prompt implicitly asks Spark to adjudicate legality ("Is this action allowed?")

**Existing partial coverage:**
- KILL-002 (mechanical assertion detection) catches *output* violations. AUTHORITY pressure catches *input* conditions that make such violations likely.
- The `detect_mechanical_assertions()` regex patterns in `kill_switch_registry.py` scan output. The same patterns (or a simpler version) applied to the *prompt* or *NarrativeBrief* can detect authority pressure at input time.

**Fail-closed behavior:**

| Level | Condition | Response |
|-------|-----------|----------|
| GREEN | Prompt is purely narrative (no mechanical queries) | Spark generates normally |
| YELLOW | Prompt touches mechanics but Box has already resolved them | Spark generates; Box result is authoritative in NarrativeBrief |
| RED | Prompt requires mechanical adjudication Box hasn't performed | Hard stop: route to Box, not Spark |

**Critical constraint:** AUTHORITY pressure must never be resolved by giving Spark more information about mechanics. The resolution is always to route the query to Box or to refuse the query entirely.

### 3.3 CONTEXT_OVERLOAD: Context Overload Pressure

**Definition:** The token budget for the Spark call is exhausted or severely constrained, degrading generation quality to the point where hallucination risk exceeds tolerance.

**Detection point:** ContextAssembler (`aidm/lens/context_assembler.py`) during budget computation.

**Examples:**
- Token budget is 800 but NarrativeBrief alone consumes 600 (no room for continuity context)
- All session summaries dropped due to budget, leaving Spark with no historical context
- Context window overflow as described in REQ-LLM-SG-005 (M1_LLM_SAFEGUARDS_REQUIREMENTS.md)

**Existing partial coverage:**
- ContextAssembler already tracks `dropped` items with `drop_reason="budget_exceeded"`. This data is available but not surfaced as a pressure signal.
- REQ-LLM-SG-005 specifies abstention policy for context overflow but does not define a graduated pressure signal.

**Fail-closed behavior:**

| Level | Condition | Response |
|-------|-----------|----------|
| GREEN | Budget sufficient for brief + scene + 2 narrations | Spark generates normally |
| YELLOW | Budget exhausted after brief; 0 continuity items included | Spark generates with continuity caveat |
| RED | Brief itself exceeds budget, or total context is empty | Template fallback; no Spark call |

**Measurement:** Pressure level derived from `(items_included / items_available)` ratio from `ContextAssembler.retrieve()`. Thresholds: GREEN > 0.5, YELLOW 0.2-0.5, RED < 0.2.

### 3.4 AMBIGUITY: Ambiguity Pressure (Target/Intent)

**Definition:** The player's declared intent is parseable but ambiguous in a way that could lead Spark to make assumptions about game state.

**Detection point:** IntentBridge (`aidm/interaction/intent_bridge.py`) during intent resolution, or `parse_text_command()` in SessionOrchestrator.

**Examples:**
- "I attack" (no target specified, multiple valid targets exist)
- "Cast healing" (ambiguous spell name, multiple matches)
- "I go north" (no "north" exit defined, but exits exist)
- IntentBridge returns `ClarificationRequest` with `ambiguity_type=MULTIPLE_MATCHES`

**Existing partial coverage:**
- IntentBridge already handles ambiguity via `ClarificationRequest` with `AmbiguityType` enum. This is an implicit AMBIGUITY pressure at YELLOW/RED.
- `parse_text_command()` returns `command_type="unknown"` for unparseable input, which is handled as clarification.

**Fail-closed behavior:**

| Level | Condition | Response |
|-------|-----------|----------|
| GREEN | Intent fully resolved (single target, single spell, clear action) | Spark generates normally |
| YELLOW | Intent partially resolved (2-3 candidates, reasonable default exists) | Spark generates but narration flags uncertainty |
| RED | Intent unresolved (0 candidates, or 4+ candidates, or contradictory) | Hard stop: clarification question to player |

---

## 4. Audio-Friendly Alert Strings

All alerts are single-line, TTS-friendly (no choppy separators, abbreviations, or formatting artifacts). Each follows the pattern: `[Action verb] [what] [why]`.

### 4.1 MISSING_FACT Alerts

| Level | Alert String |
|-------|-------------|
| GREEN | *(no alert)* |
| YELLOW | "I'm not certain about some details here, so I'll keep this general." |
| RED | "I need a moment. Who or what are you referring to?" |

### 4.2 AUTHORITY Alerts

| Level | Alert String |
|-------|-------------|
| GREEN | *(no alert)* |
| YELLOW | "The rules engine has the answer for that. Let me check." |
| RED | "That's a mechanical question. Let me look it up rather than guess." |

### 4.3 CONTEXT_OVERLOAD Alerts

| Level | Alert String |
|-------|-------------|
| GREEN | *(no alert)* |
| YELLOW | "I'm working with limited context right now, so I'll focus on what just happened." |
| RED | "There's too much going on to narrate safely. Here's the mechanical result." |

### 4.4 AMBIGUITY Alerts

| Level | Alert String |
|-------|-------------|
| GREEN | *(no alert)* |
| YELLOW | "I want to make sure I understand. Did you mean one of these?" |
| RED | "I need you to be more specific. What exactly do you want to do?" |

### 4.5 Design Principles for Alert Strings

1. **Conversational, not robotic.** These sound like a DM thinking aloud, not a system error.
2. **No jargon.** Players never hear "boundary pressure" or "context overload."
3. **Action-oriented.** Every alert either asks a question or explains what happens next.
4. **No false confidence.** YELLOW never says "I think" about mechanical facts. It says "let me check."
5. **Compatible with prosodic schema.** YELLOW alerts use `ToneMode.REFLECTIVE` + `PauseProfile.MODERATE`. RED alerts use `ToneMode.DIRECTIVE` + `ClarityMode.HIGH`. (See `PROSODIC_SCHEMA_DRAFT.md`.)

---

## 5. Instrumentation Plan

### 5.1 Where Pressure Is Detected (Lens Boundary)

Pressure detection occurs at three existing checkpoints, all within the Lens/interaction layers. No new modules required for Phase 1.

```
Checkpoint 1: IntentBridge.resolve_*()
  Location:  aidm/interaction/intent_bridge.py
  Detects:   MISSING_FACT (zero candidates), AMBIGUITY (multiple candidates)
  Currently: Returns ClarificationRequest
  Addition:  Also emit BoundaryPressure signal alongside ClarificationRequest

Checkpoint 2: ContextAssembler.retrieve()
  Location:  aidm/lens/context_assembler.py
  Detects:   CONTEXT_OVERLOAD (budget exhaustion), MISSING_FACT (zero relevant items)
  Currently: Returns RetrievedItem list with dropped flags
  Addition:  Compute and return pressure level from item inclusion ratio

Checkpoint 3: SessionOrchestrator._generate_narration()
  Location:  aidm/runtime/session_orchestrator.py
  Detects:   AUTHORITY (mechanical query in prompt)
  Currently: Builds NarrationRequest and delegates to GuardedNarrationService
  Addition:  Pre-scan NarrativeBrief for mechanical query indicators before Spark call
```

### 5.2 How Pressure Is Logged/Telemetried

**Log format:** Structured Python logging (same as KillSwitchEvidence pattern).

```
Log name:      aidm.boundary_pressure
Log level:     GREEN=DEBUG, YELLOW=WARNING, RED=ERROR
Fields:
  trigger:     str     # "MISSING_FACT", "AUTHORITY", "CONTEXT_OVERLOAD", "AMBIGUITY"
  level:       str     # "GREEN", "YELLOW", "RED"
  turn:        int     # turn number
  detail:      str     # human-readable explanation
  confidence:  float   # 0.0-1.0
  source:      str     # module that detected it
  response:    str     # "generate", "hedge", "question", "hard_stop", "template_fallback"
```

**Telemetry aggregation (future):** Per-session counts of GREEN/YELLOW/RED per trigger type. Enables tuning thresholds without code changes.

### 5.3 How Pressure Converts to Responses

The Session Orchestrator is the decision point. It receives pressure from checkpoints and selects a response:

```
                    GREEN           YELLOW              RED
                    -----           ------              ---
MISSING_FACT        generate        generate+hedge      question to player
AUTHORITY           generate        generate (Box data) route to Box
CONTEXT_OVERLOAD    generate        generate+caveat     template fallback
AMBIGUITY           generate        generate+question   question to player

Response types:
  generate          Normal Spark call, no modification
  generate+hedge    Spark call with uncertainty marker prepended to prompt
  generate+caveat   Spark call with reduced context acknowledged in prompt
  generate+question Spark call, but TTS appends clarifying question after narration
  question          No Spark call. Clarification question only.
  route to Box      No Spark call. Box query executed and result narrated via template.
  template fallback No Spark call. Template narration from NarrationTemplates.
  hard stop         No Spark call. No template. System message only.
```

**Key property:** Every RED response avoids a Spark call. This is non-negotiable. RED means "Spark cannot safely generate here."

---

## 6. Minimum Viable Enforcement (Phase 1)

### 6.1 Scope

Phase 1 implements boundary pressure detection using only existing infrastructure. No new modules, no middleware, no external dependencies.

### 6.2 Phase 1 Deliverables

**P1-A: BoundaryPressure dataclass** (new file: `aidm/schemas/boundary_pressure.py`)
- Frozen dataclass matching Section 2.3 schema
- `PressureTrigger` enum (4 values)
- `PressureLevel` enum (3 values)
- Pure data, no imports beyond stdlib

**P1-B: Pressure detection in ContextAssembler** (modify: `aidm/lens/context_assembler.py`)
- Add `compute_pressure()` method to ContextAssembler
- Input: `List[RetrievedItem]` from `retrieve()`
- Output: `BoundaryPressure` with CONTEXT_OVERLOAD trigger
- Logic: count included vs dropped items, apply thresholds
- No new dependencies

**P1-C: Pressure detection in IntentBridge** (modify: `aidm/interaction/intent_bridge.py`)
- When `resolve_*()` returns `ClarificationRequest`, also compute `BoundaryPressure`
- MISSING_FACT if zero candidates, AMBIGUITY if multiple
- Attach pressure to existing ClarificationRequest or return alongside it
- No new dependencies

**P1-D: Pressure-aware orchestration** (modify: `aidm/runtime/session_orchestrator.py`)
- Before Spark call in `_generate_narration()`, check accumulated pressure
- RED pressure: skip Spark, use template fallback + alert string
- YELLOW pressure: modify prompt to include hedge instruction
- GREEN pressure: no change (current behavior)
- Log pressure to `aidm.boundary_pressure` logger

**P1-E: Alert string integration** (modify: `aidm/runtime/session_orchestrator.py`)
- RED/YELLOW pressure prepends or appends alert string to narration output
- TTS receives alert string with appropriate prosodic profile
- Alert strings from Section 4 hardcoded as constants

### 6.3 Phase 1 Non-Goals

- **No AUTHORITY detector.** Mechanical query detection in prompts is complex and deferred. Phase 1 relies on KILL-002 (post-hoc) for this.
- **No ML-based detection.** All thresholds are static. No learned models.
- **No persistence.** Pressure signals are per-turn only. No cross-session trending.
- **No UI.** Pressure is audio-only (alert strings via TTS) and logged.
- **No middleware.** All detection is in-process. No HTTP interceptors or proxy layers.
- **No modification to Box.** Pressure is a Lens-layer concern. Box is unaware of it.

### 6.4 Phase 1 Boundary Laws Compliance

| Law | Impact | Compliance |
|-----|--------|------------|
| BL-001 | BoundaryPressure schema in aidm/schemas/ | schemas/ imports nothing from core/spark/narration |
| BL-003 | ContextAssembler in aidm/lens/ | lens/ does not import core (already compliant) |
| BL-013 | SparkRequest unchanged | No schema changes to SparkRequest |
| BL-020 | FrozenWorldStateView unchanged | Pressure detection reads FrozenWorldStateView, never mutates |
| Axiom 2 | Pressure has zero authority | Pressure can suppress Spark but cannot alter game state |

---

## 7. Future Expansion (Phase 2+)

### 7.1 Phase 2: AUTHORITY Detector

- Pre-scan NarrativeBrief and prompt text for mechanical query patterns
- Reuse `detect_mechanical_assertions()` regex on *input* side
- Add "mechanical query" patterns: "can I", "is it possible", "what's my", "how far"
- Route detected queries to Box (IntentBridge) instead of Spark
- Requires: new regex set, SessionOrchestrator routing logic

### 7.2 Phase 2: Pressure Trending

- Accumulate pressure signals per session
- Detect pressure escalation (3+ consecutive YELLOWs = systemic issue)
- Surface trend in session summary (SegmentTracker integration)
- Requires: pressure history buffer in SessionOrchestrator

### 7.3 Phase 2: Prosodic Integration

- Wire pressure level to prosodic preset selection (PROSODIC_SCHEMA_DRAFT.md)
- GREEN: current prosodic mode (no change)
- YELLOW: `ToneMode.REFLECTIVE`, `PauseProfile.MODERATE`, `EmphasisLevel.LOW`
- RED: `ToneMode.DIRECTIVE`, `ClarityMode.HIGH`, `PauseProfile.MINIMAL`
- Requires: PAS Phase 1 (VoicePersona extension) to be implemented first

### 7.4 Phase 3: Adaptive Thresholds

- Per-player-model threshold adjustment (experienced players tolerate more uncertainty)
- Feedback loop: if YELLOW hedges are always followed by successful generation, raise YELLOW threshold
- Requires: PlayerModel subsystem (SPARK_LENS_BOX_ARCHITECTURE.md Section 5.2)

### 7.5 Explicit Non-Goals (All Phases)

1. **Pressure never grants Spark authority.** A RED pressure signal does not cause Spark to be given "more rules knowledge" to handle the situation. The response is always to route away from Spark or to stop.
2. **Pressure is not a refusal system.** Spark does not refuse. Pressure prevents Spark from being called. The distinction is architectural (Lens gates Spark) not behavioral (Spark self-censors). Per Axiom 1: no refusal originates from Spark.
3. **Pressure does not modify WorldState.** It is purely informational. It lives in the Lens/immersion layers and is logged, never persisted in Box state.
4. **Pressure is not visible as "pressure" to players.** Players hear natural language (alert strings). They never see "YELLOW" or "boundary pressure." The system is transparent in its effect (asking questions, hedging) but opaque in its mechanism.
5. **No infrastructure dependencies.** No Redis, no message queues, no external services. All in-process, all Python, all synchronous within the turn cycle.

---

## 8. Relationship to Existing Systems

### 8.1 Kill Switches vs. Boundary Pressure

Kill switches (KILL-001 through KILL-006) are **post-hoc enforcement**. They fire *after* Spark generates output that violates a boundary. They are the "already broken" signal.

Boundary pressure is **pre-emptive detection**. It fires *before* Spark generates, when conditions suggest a violation is likely. It is the "about to break" signal.

| Dimension | Kill Switches | Boundary Pressure |
|-----------|--------------|-------------------|
| **When** | After Spark generates | Before Spark generates |
| **What** | Detects actual violations | Detects conditions likely to cause violations |
| **Response** | Template fallback + disable Spark | Question, hedge, route, or template |
| **Recovery** | Manual reset required | Automatic per-turn (no state) |
| **Severity** | Binary (triggered/not) | Graduated (GREEN/YELLOW/RED) |
| **Persistence** | Persists until reset | Per-turn only |

**Interaction:** If boundary pressure is RED, the Spark call is skipped entirely, so kill switches never fire. If pressure is YELLOW and Spark generates anyway, kill switches remain the safety net. The two systems are complementary, not redundant.

### 8.2 ClarificationRequest vs. Boundary Pressure

`ClarificationRequest` (from IntentBridge) is the existing mechanism for handling ambiguous player input. Boundary pressure subsumes it:

- ClarificationRequest with zero candidates = MISSING_FACT at RED
- ClarificationRequest with multiple candidates = AMBIGUITY at YELLOW or RED
- ClarificationRequest message = the alert string

Phase 1 does not replace ClarificationRequest. It wraps it: when IntentBridge returns a ClarificationRequest, the orchestrator also logs a BoundaryPressure event. The ClarificationRequest remains the player-facing response.

### 8.3 ContextAssembler Drop Tracking vs. Boundary Pressure

`RetrievedItem.dropped` (from WO-059) tracks which context items were cut due to budget. Boundary pressure converts this into a risk signal:

- Many items dropped = CONTEXT_OVERLOAD at YELLOW
- All items dropped = CONTEXT_OVERLOAD at RED
- No items dropped = GREEN

The `retrieve()` method already computes everything needed. Pressure is a thin computation on top of existing data.

### 8.4 REQ-LLM-SG-005 (Abstention Policy) vs. Boundary Pressure

REQ-LLM-SG-005 mandates abstention when context overflows. Boundary pressure operationalizes this:

- CONTEXT_OVERLOAD at RED = abstention (template fallback, no Spark call)
- This is the concrete implementation path for REQ-LLM-SG-005's "explicit data unavailable response"

---

## 9. Test Ideas (Deterministic, No UI)

Five test scenarios that validate boundary pressure enforcement without requiring a graphical interface or manual interaction.

### Test 1: MISSING_FACT RED Blocks Spark Call

**Setup:** Configure IntentBridge with a WorldState containing no entity matching "shopkeeper." Player input: "attack shopkeeper."

**Assert:**
- IntentBridge returns ClarificationRequest (existing behavior)
- BoundaryPressure emitted with trigger=MISSING_FACT, level=RED
- No SparkRequest is constructed (mock Spark adapter receives zero calls)
- TurnResult contains clarification message, not narration

**Validates:** RED pressure prevents Spark call (fail-closed).

### Test 2: CONTEXT_OVERLOAD Graduated Response

**Setup:** Configure ContextAssembler with token_budget=100. Provide a NarrativeBrief that consumes 90 tokens and 5 previous narrations totaling 500 tokens.

**Assert:**
- `retrieve()` returns brief as included, all narrations as dropped (budget_exceeded)
- `compute_pressure()` returns CONTEXT_OVERLOAD at YELLOW (brief fits, nothing else does)
- Reduce budget to 10 (brief doesn't fit): pressure escalates to RED
- At RED: Spark adapter mock receives zero calls; template narration used

**Validates:** Graduated pressure levels, threshold behavior, RED-to-template fallback.

### Test 3: AMBIGUITY YELLOW Produces Hedge

**Setup:** Configure IntentBridge where "goblin" matches 2 entities (Goblin Warrior, Goblin Archer). Player input: "attack goblin."

**Assert:**
- IntentBridge returns ClarificationRequest with 2 candidates
- BoundaryPressure emitted with trigger=AMBIGUITY, level=YELLOW
- If orchestrator proceeds with Spark (YELLOW allows generation), prompt contains uncertainty hedge instruction
- Alert string matches Section 4.4 YELLOW string

**Validates:** YELLOW pressure modifies Spark prompt without blocking it.

### Test 4: GREEN Pressure No-Op

**Setup:** Standard combat fixture. Player attacks a uniquely named target. Full context budget available. All facts present.

**Assert:**
- BoundaryPressure emitted with level=GREEN for all triggers
- Spark adapter receives exactly one call (no blocking)
- No alert strings in TurnResult narration text
- No WARNING or ERROR log entries for `aidm.boundary_pressure`

**Validates:** GREEN pressure does not interfere with normal operation.

### Test 5: Fail-Closed Default (Unknown Pressure)

**Setup:** Construct a BoundaryPressure with a synthetic trigger not in the enum (simulating a detector malfunction or unhandled case). Or: ContextAssembler returns an empty `retrieve()` list (no items at all, not even the brief).

**Assert:**
- Orchestrator treats unknown/empty pressure as RED (fail-closed)
- Spark adapter receives zero calls
- Template fallback used
- ERROR log entry for `aidm.boundary_pressure` with detail explaining the fail-closed default

**Validates:** Fail-closed behavior when pressure detection itself fails.

---

## 10. Schema Alignment Note (WO-RQ-LLM-CALL-TYPING-01)

This document recommends a `BoundaryPressure` dataclass in `aidm/schemas/boundary_pressure.py`. The `PressureTrigger` and `PressureLevel` enums should be aligned with whatever call-typing schema emerges from WO-RQ-LLM-CALL-TYPING-01.

Specifically, if WO-RQ-LLM-CALL-TYPING-01 defines a `SparkCallType` enum (narration, query, intent_parse, etc.), the pressure trigger taxonomy should map cleanly:

```
SparkCallType.NARRATION   -> MISSING_FACT, CONTEXT_OVERLOAD, AUTHORITY
SparkCallType.QUERY       -> MISSING_FACT, AUTHORITY
SparkCallType.INTENT      -> AMBIGUITY, MISSING_FACT
```

This mapping is not binding. It is a recommendation for schema coherence.

---

## 11. Stop Condition Report

| Stop Condition | Status |
|----------------|--------|
| Need to modify runtime/code/tests | NOT TRIGGERED. This is research only. |
| Recommendation grants Spark mechanical authority | NOT TRIGGERED. All responses either suppress Spark or route to Box. |
| Requires infrastructure not present | NOT TRIGGERED. All detection is in-process using existing modules. |

---

## 12. Compliance Statement

**Research-only work order. No production code written, no schemas created, no tests modified.**

- All file references are to existing code (read-only analysis)
- All proposed schemas are specification only (pseudocode, not importable)
- All modifications described are future work orders, not this document's scope
- This document lives in `docs/planning/research/` (allowed path)

**Forbidden files NOT touched:**
- aidm/core/* (not modified)
- aidm/runtime/* (not modified)
- tests/* (not modified)
- scripts/* (not modified)
- docs/doctrine/* (not modified)
- docs/ops/* (not modified)

---

**END OF RESEARCH DOCUMENT**
