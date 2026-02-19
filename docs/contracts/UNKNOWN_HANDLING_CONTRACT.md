# Unknown Handling Contract v1
## Voice Input Classification, Failure Handling, and Clarification Policy

**Document ID:** RQ-UNKNOWN-001
**Version:** 1.0
**Date:** 2026-02-19
**Status:** DRAFT — Awaiting PM Approval
**Authority:** This document is the canonical contract for voice input failure classification, STOPLIGHT bias rules, and clarification budget policy. It governs how unrecognized, ambiguous, or malformed voice inputs are handled before any mechanical action is committed.
**Scope:** Failure class taxonomy (FC-ASR through FC-BLEED), STOPLIGHT classification system, clarification escalation, cancel semantics, provenance tagging, and cross-cutting invariants. Voice input policy only — no Box, Oracle, or game-rule authority.

**References:**
- `docs/research/VOICE_FAILURE_TAXONOMY_AND_UNKNOWN_POLICY.md` — Source research (Sections 1-5)
- `docs/contracts/CLI_GRAMMAR_CONTRACT.md` (RQ-GRAMMAR-001) — Companion contract (output formatting)
- `docs/contracts/INTENT_BRIDGE.md` (RQ-INTENT-001) — Intent resolution pipeline
- `pm_inbox/reviewed/legacy_pm_inbox/research/VOICE_FIRST_RELIABILITY_PLAYBOOK.md` — Section 4 (failure policy)

**Existing Implementation (this spec formalizes):**

| Layer | File | Status |
|-------|------|--------|
| Voice intent parser | — | **Not yet implemented (Tier 3)** |
| Unknown handling validator | `scripts/check_unknown_handling.py` | **New — created by this WO** |
| Gate tests | `tests/test_unknown_gate_k.py` | **New — created by this WO** |

---

## Contract Summary (1-Page)

Every voice input received by the system is classified into exactly one STOPLIGHT color (GREEN, YELLOW, RED) or routed to a non-intent handler. The classification determines whether the system proceeds, clarifies, or rejects. No mechanical action is ever committed without confirmed intent. Clarification is budget-limited to prevent infinite loops.

**Three-Layer Model:**

```
Voice Input  →  Failure Classifier  →  STOPLIGHT  →  Action
  (ASR out)      (FC-ASR..FC-BLEED)    (G/Y/R)      (proceed/clarify/reject)
```

The failure classifier identifies which failure class (if any) applies. The STOPLIGHT system assigns a color. The clarification budget governs how many attempts the system gets before escalating to a menu or cancelling.

**Invariants:**
1. **Complete classification:** Every voice input receives exactly one STOPLIGHT classification. No input is unclassified. No input receives two classifications simultaneously.
2. **No silent commit:** No mechanical action is committed to game state from voice input unless the intent has reached `confirmed` status via explicit verbal confirmation, soft confirmation (no objection within timeout), or menu selection.
3. **RED is terminal:** RED classification is terminal. A RED input cannot be promoted to YELLOW or GREEN. The player must re-speak.
4. **Presentation boundary:** This contract operates in the Lens layer. It has zero authority over Box mechanical resolution, Oracle state, or game rules.

> **INVARIANT-1:** Every voice input receives exactly one STOPLIGHT classification. No input is unclassified. No input receives two classifications simultaneously.

> **INVARIANT-2:** No mechanical action is committed to game state from voice input unless the intent has reached `confirmed` status via explicit verbal confirmation, soft confirmation (no objection within timeout), or menu selection.

> **INVARIANT-3:** RED classification is terminal. A RED input cannot be promoted to YELLOW or GREEN. The player must re-speak.

---

## 1. Failure Class Registry

Seven failure classes covering all recognized voice input failure modes.

| Class ID | Name | Sub-classes | Default STOPLIGHT | Response Type |
|----------|------|-------------|-------------------|---------------|
| FC-ASR | ASR Recognition Errors | 4 | RED or YELLOW | Spoken feedback |
| FC-HOMO | Homophone Ambiguity | 5 | YELLOW or GREEN | Clarification or accept |
| FC-PARTIAL | Partial/Incomplete Input | 4 | YELLOW or GREEN | Query or infer |
| FC-TIMING | Timing Failures | 4 | YELLOW or RED | Buffer, pause, ignore, or discard |
| FC-AMBIG | Semantic Ambiguity | 6 | YELLOW or GREEN | Clarify or constrain |
| FC-OOG | Out-of-Grammar | 5 | RED or ROUTING | Discard, route, or ignore |
| FC-BLEED | Cross-Mode Bleed | 4 | YELLOW or RED | Ignore or clarify |

---

### 1.1 FC-ASR: Automatic Speech Recognition Errors

ASR engine returns a transcript that does not match what was said, or returns no transcript.

| Sub-class | Description | Trigger Condition |
|-----------|-------------|-------------------|
| FC-ASR-01 | Total recognition failure | ASR confidence < threshold OR empty result |
| FC-ASR-02 | Low-confidence transcript | ASR confidence below YELLOW_THRESHOLD |
| FC-ASR-03 | Truncated transcript | End-of-utterance detected before complete sentence |
| FC-ASR-04 | Noise contamination | ASR returns transcript during non-speech audio event |

**Required Behavior:**

| Sub-class | System Response | Spoken Feedback |
|-----------|-----------------|-----------------|
| FC-ASR-01 | Cancel pending intent. Return to prompt. | "I didn't catch that. What would you like to do?" |
| FC-ASR-02 | Hold transcript. Do NOT parse into intent. Request repeat. | "Could you say that again?" |
| FC-ASR-03 | Hold partial transcript. Request completion. | "You were saying...?" |
| FC-ASR-04 | Discard transcript. Do NOT parse. Return to prompt. | "I didn't catch that. What would you like to do?" |

**Forbidden Behavior:**
- Parsing a low-confidence transcript into an intent
- Completing a truncated utterance by guessing missing words
- Treating noise as a valid command
- Silently committing any action on a degraded transcript

---

### 1.2 FC-HOMO: Homophone and Near-Homophone Ambiguity

ASR returns a valid transcript, but the words map to multiple game-meaningful terms that sound alike.

| Sub-class | Description | Example Pair |
|-----------|-------------|--------------|
| FC-HOMO-01 | Spell homophone | "Bane" vs "Bain" (NPC name) |
| FC-HOMO-02 | Weapon/item homophone | "Mace" vs "Maze" (spell) |
| FC-HOMO-03 | Entity name collision | "The guard" when 3 guards exist |
| FC-HOMO-04 | Number ambiguity | "For" vs "four"; "to" vs "two" |
| FC-HOMO-05 | Action verb ambiguity | "Shoot" vs "Shoo" (intimidate) |

**Required Behavior:**

| Condition | System Response |
|-----------|-----------------|
| Game lexicon contains exactly 1 match | Accept match; proceed to intent parsing |
| Game lexicon contains 2-3 matches | DM-voice clarification question presenting options naturally |
| Game lexicon contains 4+ matches | Numbered menu with brief identifiers |
| Game lexicon contains 0 matches | Treat as FC-OOG |

**Forbidden Behavior:**
- Picking the "most likely" match without asking
- Using probabilistic ranking to silently select
- Committing a spell when the player named a person (or vice versa)

---

### 1.3 FC-PARTIAL: Partial and Incomplete Transcripts

ASR returns a valid transcript, but semantic content is insufficient to populate required intent fields.

| Sub-class | Description | Missing Field(s) |
|-----------|-------------|-------------------|
| FC-PARTIAL-01 | Missing target | primary_target |
| FC-PARTIAL-02 | Missing method | method (which weapon?) |
| FC-PARTIAL-03 | Missing action type | action_type |
| FC-PARTIAL-04 | Pronoun without antecedent | primary_target (pronoun resolution failed) |

**Required Behavior:**

| Sub-class | System Response | Spoken Feedback |
|-----------|-----------------|-----------------|
| FC-PARTIAL-01 | Query for target | "Who are you attacking?" |
| FC-PARTIAL-02 | Infer if exactly 1 option; else query | "With your longsword, or something else?" |
| FC-PARTIAL-03 | Query for action | "What do you want to do with the goblin by the door?" |
| FC-PARTIAL-04 | Query for target; max 3-turn STM lookback | "Who do you mean?" |

**Single-Weapon Inference Rule (FC-PARTIAL-02 only):** If the actor has exactly one melee weapon equipped and no ranged weapon, AND the target is in melee range, the system MAY infer the weapon without asking. This is the ONLY inference permitted for partial transcripts. The inference MUST be logged with `[INFERRED]` provenance tag.

**Forbidden Behavior:**
- Inferring target from "nearest enemy" logic
- Inferring action type from context
- Using STM buffer older than 3 turns for pronoun resolution
- Silently filling any required intent field except the single-weapon exception above

---

### 1.4 FC-TIMING: Turn-Taking and Timing Failures

Voice input arrives at a time when it cannot be processed as a valid command.

| Sub-class | Description | Trigger |
|-----------|-------------|---------|
| FC-TIMING-01 | Out-of-turn input | Voice input during another entity's resolution |
| FC-TIMING-02 | Interruption during TTS | Voice input overlaps with active TTS playback |
| FC-TIMING-03 | Double-fire | Second intent while first is pending/clarifying |
| FC-TIMING-04 | Stale input | Transcript delivered >5s after speech ended |

**Required Behavior:**

| Sub-class | System Response |
|-----------|-----------------|
| FC-TIMING-01 | Buffer input. If speaker's turn is next, hold and replay. Otherwise discard: "Hold on — it's not your turn yet." |
| FC-TIMING-02 | Pause TTS. Process voice input. If valid, proceed. If not parseable, resume TTS and discard. TTS MUST be interruptible. |
| FC-TIMING-03 | Ignore second input. "I heard you — working on it." |
| FC-TIMING-04 | Discard stale transcript. No spoken feedback. Log with timestamp. |

**Forbidden Behavior:**
- Executing an action on a turn that does not belong to the speaker
- Queuing multiple intents from a single player's turn
- Processing stale transcripts as current commands
- Forcing the player to wait for TTS to finish before accepting input

---

### 1.5 FC-AMBIG: Semantic Ambiguity

ASR transcript is complete and confident, but maps to multiple valid game-mechanical interpretations.

| Sub-class | Description | Ambiguity Type |
|-----------|-------------|----------------|
| FC-AMBIG-01 | Entity ambiguity | Multiple valid targets |
| FC-AMBIG-02 | Spell ambiguity | Multiple spells match partial name |
| FC-AMBIG-03 | Weapon ambiguity | Multiple weapons match |
| FC-AMBIG-04 | Action interpretation | Multiple valid action types |
| FC-AMBIG-05 | Spatial ambiguity | Multiple valid positions |
| FC-AMBIG-06 | Numeric ambiguity | Multiple numeric interpretations |

**Required Behavior:**

| Condition | System Response |
|-----------|-----------------|
| 2-3 valid interpretations | DM-voice clarification question presenting options naturally |
| 4+ valid interpretations | Numbered menu with brief identifiers |
| Ambiguity resolvable by game-state constraints | Apply constraints FIRST, then accept or clarify remainder. Log with `[CONSTRAINED]` tag. |

**Constraint Resolution Order (Deterministic):**
1. Range/reach filter (eliminate targets out of range)
2. Line-of-sight filter (eliminate targets not visible)
3. Prior-turn context (STM buffer, max 3 turns)
4. If still ambiguous after filters → ask

**Forbidden Behavior:**
- Selecting "nearest" or "most damaged" target without asking
- Using LLM probability to rank interpretations
- Resolving ambiguity by rolling randomly
- Committing any action when 2+ valid interpretations remain after constraint filtering

---

### 1.6 FC-OOG: Out-of-Grammar Utterances

Transcript is valid English but does not correspond to any recognized game action, entity, or system command.

| Sub-class | Description | Detection |
|-----------|-------------|-----------|
| FC-OOG-01 | Nonsense / misparse | No game-lexicon tokens matched |
| FC-OOG-02 | Real-world / system request | Recognized as meta-request |
| FC-OOG-03 | Rules question | Interrogative structure, no action verb |
| FC-OOG-04 | Narrative-only statement | Descriptive, no mechanical intent |
| FC-OOG-05 | Profanity / emotional outburst | Exclamatory, no action content |

**Required Behavior:**

| Sub-class | System Response |
|-----------|-----------------|
| FC-OOG-01 | Discard. "I'm not sure what you mean. What would you like to do?" |
| FC-OOG-02 | Route to system handler (pause, save, quit). Arbor voice. No intent. |
| FC-OOG-03 | Route to rules-query handler. Box answers. No intent. DM voice. |
| FC-OOG-04 | Acknowledge narratively. No intent. No mechanical effect. DM voice. |
| FC-OOG-05 | Ignore. No response. No intent. |

**Forbidden Behavior:**
- Treating a rules question as an action declaration
- Creating a mechanical intent from a narrative statement
- Executing a game action from a meta-request
- Responding to emotional outbursts as if they were commands

---

### 1.7 FC-BLEED: Cross-Mode Bleed (Table Talk as Command)

The system interprets conversational speech as an in-game command.

| Sub-class | Description | Example |
|-----------|-------------|---------|
| FC-BLEED-01 | Table talk as action | "I should probably attack the dragon" |
| FC-BLEED-02 | Side conversation | "Can you pass me a drink?" |
| FC-BLEED-03 | Quoting / storytelling | "Last session I cast fireball" |
| FC-BLEED-04 | Hypothetical discussion | "What if I moved here instead?" |

**Detection Heuristics:**

| Signal | Indicates Table Talk | Weight |
|--------|---------------------|--------|
| Conditional language ("should", "could", "what if", "maybe") | Likely speculative | HIGH |
| Past tense ("I attacked", "we went", "that was") | Likely retrospective | HIGH |
| No entity/action match in current game state | Likely off-topic | MEDIUM |
| Speaker is not the active player | Likely table talk | HIGH |
| Hedging language ("probably", "I think", "I guess") | Possibly speculative | MEDIUM |

**Required Behavior:**

| Command Confidence | System Response |
|--------------------|-----------------|
| HIGH (imperative verb + valid target + speaker's turn) | Parse as intent normally |
| MEDIUM (some command signals, some table-talk signals) | Clarify: "Are you saying you want to attack the dragon?" |
| LOW (multiple table-talk signals) | Ignore. No parse. No spoken feedback. |

**Forbidden Behavior:**
- Parsing conditional/hypothetical language as a committed action
- Creating an intent from past-tense narration
- Processing speech from a non-active player as a command
- Treating "I should..." as equivalent to "I will..."

---

## 2. STOPLIGHT Classification Rules

### 2.1 Definitions

| Level | Name | Meaning | Default Bias |
|-------|------|---------|--------------|
| GREEN | Proceed | Input is unambiguous, confident, maps to exactly one intent | Must be EARNED by passing all filters |
| YELLOW | Clarify | Input has recoverable ambiguity or moderate confidence | DEFAULT for any input with ambiguity flags |
| RED | Reject | Input is unrecoverable, dangerous, or uninterpretable | DEFAULT for any input below minimum thresholds |

### 2.2 Classification Truth Table

| Condition | Color | Action |
|-----------|-------|--------|
| ASR confidence >= GREEN_THRESHOLD (0.85) AND exactly 1 parse AND all fields populated AND no table-talk signals | GREEN | Proceed to soft confirmation |
| ASR confidence >= YELLOW_THRESHOLD (0.50) AND < GREEN_THRESHOLD | YELLOW | Request repeat or clarify |
| ASR confidence < YELLOW_THRESHOLD (0.50) | RED | Discard. "I didn't catch that." |
| ASR confidence >= GREEN_THRESHOLD BUT 2+ intent parses | YELLOW | Clarify: present options |
| ASR confidence >= GREEN_THRESHOLD BUT missing required fields | YELLOW | Query for missing fields |
| Any table-talk signal with MEDIUM+ weight | YELLOW | Clarify: "Are you saying you want to...?" |
| Multiple HIGH-weight table-talk signals | RED | Ignore. No parse. |
| Transcript matches FC-OOG-01 (no lexicon match) | RED | Discard. Request rephrase. |
| Transcript matches FC-OOG-02 through FC-OOG-05 | ROUTING | Route to non-intent handler |

### 2.3 Promotion Rules

An input may only be promoted from YELLOW to GREEN by:
1. Player verbally confirming a clarification question
2. Player selecting from a numbered menu
3. Game-state constraint filtering reducing options to exactly 1

**RED is terminal. No RED → GREEN or RED → YELLOW promotion. The player must re-speak.**

### 2.4 Demotion Rules

| Trigger | Demotion |
|---------|----------|
| Post-parse: action is impossible (out of range, wrong turn) | GREEN → YELLOW |
| Post-parse: high-consequence irreversible action (attacking ally) | GREEN → YELLOW (require explicit confirmation) |
| Post-parse: action violates game rules that cannot be clarified | GREEN → RED |

### 2.5 Authority Boundary

The STOPLIGHT system operates in the LENS layer. It MUST NOT:
- Override Box mechanical resolution
- Grant or deny mechanical permissions (Box authority)
- Use LLM probability scores to promote YELLOW to GREEN
- Make "probably" judgments about player intent

The STOPLIGHT system MAY:
- Use ASR confidence scores (acoustic model output, not LLM inference)
- Use game-state constraint filters (range, LOS, equipment — deterministic Box queries)
- Use lexicon matching (dictionary lookup, not probabilistic NLP)

---

## 3. Clarification Budget Policy

### 3.1 Budget Parameters

| Parameter | Default | Configurable | Unit |
|-----------|---------|--------------|------|
| MAX_CLARIFICATIONS | 2 | Yes (1-3) | count |
| SILENCE_TIMEOUT | 15 | Yes (5-60) | seconds |
| MENU_TIMEOUT | 30 | Yes (10-120) | seconds |
| STALE_TRANSCRIPT_THRESHOLD | 5 | Yes (2-15) | seconds |
| STM_BUFFER_DEPTH | 3 | Yes (1-5) | turns |
| SOFT_CONFIRM_WINDOW | 3 | Yes (1-10) | seconds |
| GREEN_THRESHOLD | 0.85 | Yes (0.70-0.99) | ASR confidence |
| YELLOW_THRESHOLD | 0.50 | Yes (0.30-0.80) | ASR confidence |

**Constraint:** GREEN_THRESHOLD MUST be > YELLOW_THRESHOLD. The system MUST reject configuration where GREEN_THRESHOLD <= YELLOW_THRESHOLD.

### 3.2 Clarification Escalation Ladder

```
ATTEMPT 0: Initial voice input
  → GREEN: proceed to soft confirmation
  → YELLOW: ask clarification question #1

ATTEMPT 1: First clarification response
  → GREEN: proceed to soft confirmation
  → Still YELLOW: ask clarification question #2 (MUST differ from #1)
  → RED: cancel. "Let's start over. What would you like to do?"

ATTEMPT 2: Second clarification response
  → GREEN: proceed to soft confirmation
  → Still YELLOW: ESCALATE to numbered menu
  → RED: cancel.

MENU: Numbered menu presented
  → Valid selection: proceed to soft confirmation
  → Invalid selection: cancel. "Let me know when you're ready."
  → Timeout: cancel. "Taking that as a pass. Let me know when you're ready."
```

### 3.3 Clarification Question Rules

1. **No repetition.** Clarification #2 MUST NOT repeat clarification #1. Must rephrase or add context.
2. **Increasing specificity.** Each subsequent question provides MORE context.
3. **DM voice only.** All clarification questions use DM persona.
4. **No leading questions.** Never phrase to suggest a preferred answer.
5. **No mechanical jargon.** "Which goblin?" is correct. "Which target entity?" is forbidden.

### 3.4 Cancel Semantics

| Trigger | Effect | Spoken Feedback |
|---------|--------|-----------------|
| "cancel" / "never mind" / "stop" | Discard pending intent. Return to prompt. | "Got it. Your action?" |
| Silence timeout (15s) after clarification | Discard pending intent. Return to prompt. | "I didn't catch that. Let me know when you're ready." |
| Menu timeout (30s) | Discard pending intent. Return to prompt. | "Taking that as a pass. Your action?" |
| "wait" / "hold on" | Pause timeout counter. Resume on next speech. | No spoken feedback. |

**Cancel Invariants:**
- Cancel NEVER triggers a partial action
- Cancel NEVER penalizes the player (no lost turn, no wasted action)
- Cancel returns game state to EXACTLY the state before the failed input
- Cancel is logged with `[CANCELLED]` provenance tag

---

## 4. Cross-Cutting Rules

### 4.1 No Silent Commit

No mechanical action may be committed to the game state based on voice input unless the intent has reached `confirmed` status. Confirmation requires one of:
- Explicit verbal confirmation ("Yes", "Do it", "Go ahead")
- Soft confirmation (system states the action; player does not object within SOFT_CONFIRM_WINDOW seconds)
- Menu selection

### 4.2 No Probabilistic Resolution

The system MUST NOT use LLM inference, embedding similarity, or probabilistic NLP to resolve ambiguity in voice commands. Resolution methods are limited to:
- Exact lexicon matching
- Game-state constraint filtering (deterministic Box queries)
- Direct player clarification

### 4.3 Provenance Tagging

Every voice-derived intent MUST carry provenance metadata:

| Tag | Meaning |
|-----|---------|
| `[VOICE]` | Intent originated from voice input |
| `[INFERRED]` | One or more fields were inferred (only per FC-PARTIAL-02 single-weapon rule) |
| `[CONSTRAINED]` | Ambiguity resolved by game-state constraint filtering |
| `[CLARIFIED]` | Player answered a clarification question to resolve ambiguity |
| `[MENU-SELECTED]` | Player selected from a numbered menu |
| `[CANCELLED]` | Intent was cancelled before confirmation |

### 4.4 Replay Compatibility

All voice failure handling MUST be deterministic given the same inputs:
- Same transcript + game state → same STOPLIGHT classification
- Same clarification sequence → same escalation path
- Constraint filtering is order-independent and deterministic (sorted by canonical entity ID)

### 4.5 TTS Interruptibility

Per FC-TIMING-02: System TTS MUST be interruptible by player speech at all times. The player is never forced to wait for the system to finish speaking before issuing a command.

---

## 5. Authority Boundary Statement

This contract governs voice input classification, failure handling, and clarification flow. It operates in the Lens layer. It has zero authority over Box mechanical resolution, Oracle state, or game rules. STOPLIGHT classification uses ASR confidence scores and deterministic constraint filters only — never LLM inference or probabilistic NLP.

---

## END OF UNKNOWN HANDLING CONTRACT v1.0
