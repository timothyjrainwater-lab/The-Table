# Voice Failure Taxonomy & Unknown Handling Policy

**Work Order:** WO-VOICE-RESEARCH-02
**Status:** RESEARCH COMPLETE
**Date:** 2026-02-13
**Author:** Sonnet B (Agent)
**Authority:** PM-approved research deliverable

**Binding references:**
- SPARK_LENS_BOX_DOCTRINE.md (Axiom 2: Authority only from Box)
- VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md (VICP-001, Section 6: No Silent Assumptions)
- RQ_AUDIOFIRST_CLI_CONTRACT_V1.md (Voice routing, salience hierarchy)
- RQ_INTERACT_001_VOICE_FIRST.md (Intent parsing, clarification loop)
- SPARK_SWAPPABLE_INVARIANT.md (STOP-005: Determinism violation on swap)

**Scope constraint:** This document is POLICY ONLY. It does not implement code, modify engine mechanics, or alter doctrine. It defines required system behaviors when voice input is degraded, ambiguous, or unrecognizable.

**Default posture:** FAIL-CLOSED. If a voice input cannot be confidently mapped to a single unambiguous intent, no mechanical action is taken. The system asks, offers a menu, or cancels. It never guesses.

---

## 1. Failure Class Taxonomy

### 1.1 FC-ASR: Automatic Speech Recognition Errors

**Definition:** The ASR engine returns a transcript that does not match what the player said, or returns no transcript at all.

**Sub-classes:**

| ID | Sub-class | Example | Trigger Condition |
|---|---|---|---|
| FC-ASR-01 | Total recognition failure | Player speaks; ASR returns empty string or silence token | ASR confidence < threshold OR empty result |
| FC-ASR-02 | Low-confidence transcript | "Fireball" transcribed as "fire wall" at 0.4 confidence | ASR confidence below YELLOW threshold (see Section 2) |
| FC-ASR-03 | Truncated transcript | "I attack the goblin with my long—" (cut off) | End-of-utterance detected before complete sentence; missing verb/object/target |
| FC-ASR-04 | Noise contamination | Background music or table chatter injected into transcript | ASR returns transcript during non-speech audio event |

**Required behavior:**

| Sub-class | System Response | Spoken Feedback |
|---|---|---|
| FC-ASR-01 | Cancel pending intent. Return to prompt. | "I didn't catch that. What would you like to do?" |
| FC-ASR-02 | Hold transcript. Do NOT parse into intent. Request repeat. | "Could you say that again?" |
| FC-ASR-03 | Hold partial transcript. Request completion. | "You were saying...?" |
| FC-ASR-04 | Discard transcript. Do NOT parse. Return to prompt. | "I didn't catch that. What would you like to do?" |

**Forbidden behavior:**
- Parsing a low-confidence transcript into an intent
- Completing a truncated utterance by guessing the missing words
- Treating noise as a valid command
- Silently committing any action on a degraded transcript

---

### 1.2 FC-HOMO: Homophone and Near-Homophone Ambiguity

**Definition:** ASR returns a valid transcript, but the words map to multiple game-meaningful terms that sound alike.

**Sub-classes:**

| ID | Sub-class | Example Pair | Risk |
|---|---|---|---|
| FC-HOMO-01 | Spell homophone | "Bane" vs "Bain" (NPC name) | Wrong target or wrong action type |
| FC-HOMO-02 | Weapon/item homophone | "Mace" vs "Maze" (spell) | Attack resolved as spell or vice versa |
| FC-HOMO-03 | Entity name collision | "The guard" when 3 guards exist | Wrong target |
| FC-HOMO-04 | Number ambiguity | "For" vs "four"; "to" vs "two" | Wrong spell level, wrong target count |
| FC-HOMO-05 | Action verb ambiguity | "Shoot" vs "Shoo" (intimidate away) | Wrong action type entirely |

**Required behavior:**

| Condition | System Response |
|---|---|
| Game lexicon contains exactly one match | Accept match; proceed to intent parsing |
| Game lexicon contains 2+ matches | Clarify: present options as DM question (not menu) for 2-3 options; present numbered menu for 4+ options |
| Game lexicon contains zero matches | Treat as FC-OOG (Section 1.6) |

**Disambiguation prompt format (DM voice):**
- 2-3 options: "Did you mean the spell Bane, or are you talking to Bain?"
- 4+ options: "There are several guards. Which one?" followed by numbered list with identifiers (e.g., "1. Guard by the door, 2. Guard on the bridge, 3. Guard at the gate")

**Forbidden behavior:**
- Picking the "most likely" match without asking
- Using probabilistic ranking to silently select
- Committing a spell when the player named a person (or vice versa)

---

### 1.3 FC-PARTIAL: Partial and Incomplete Transcripts

**Definition:** ASR returns a valid transcript, but the semantic content is insufficient to populate required intent fields (actor, action_type, primary_target, method).

**Sub-classes:**

| ID | Sub-class | Example | Missing Field(s) |
|---|---|---|---|
| FC-PARTIAL-01 | Missing target | "I attack!" | primary_target |
| FC-PARTIAL-02 | Missing method | "I hit the goblin" | method (which weapon? unarmed?) |
| FC-PARTIAL-03 | Missing action type | "The goblin by the door" | action_type (attack? move toward? examine?) |
| FC-PARTIAL-04 | Pronoun without antecedent | "Hit him again" (no prior target in STM buffer) | primary_target (pronoun resolution failed) |

**Required behavior:**

| Sub-class | System Response | Spoken Feedback |
|---|---|---|
| FC-PARTIAL-01 | Query for target | "Who are you attacking?" |
| FC-PARTIAL-02 | Infer from equipped/default ONLY if exactly one option; else query | "With your longsword, or something else?" |
| FC-PARTIAL-03 | Query for action | "What do you want to do with the goblin by the door?" |
| FC-PARTIAL-04 | Query for target; do NOT search STM beyond 3 turns | "Who do you mean?" |

**Special rule for FC-PARTIAL-02:** If the actor has exactly one melee weapon equipped and no ranged weapon, AND the target is in melee range, the system MAY infer the weapon without asking. This is the ONLY inference permitted for partial transcripts. The inference MUST be logged with `[INFERRED]` provenance tag.

**Forbidden behavior:**
- Inferring target from "nearest enemy" logic
- Inferring action type from context ("they were attacking last turn, so probably attacking again")
- Using STM buffer older than 3 turns for pronoun resolution
- Silently filling any required intent field except the single-weapon exception above

---

### 1.4 FC-TIMING: Turn-Taking and Timing Failures

**Definition:** Voice input arrives at a time when it cannot be processed as a valid command, or overlaps with system output.

**Sub-classes:**

| ID | Sub-class | Example | Trigger |
|---|---|---|---|
| FC-TIMING-01 | Out-of-turn input | Player speaks during NPC's turn resolution | Voice input received while intent lifecycle is in `resolved` state for another entity |
| FC-TIMING-02 | Interruption during TTS | Player speaks while system is reading narration | Voice input overlaps with active TTS playback |
| FC-TIMING-03 | Double-fire | Player repeats command before first resolves | Second intent received while first is in `pending` or `clarifying` state |
| FC-TIMING-04 | Stale input | ASR delivers transcript after significant delay (>5s from utterance) | Timestamp delta between speech-end and transcript-delivery exceeds staleness threshold |

**Required behavior:**

| Sub-class | System Response |
|---|---|
| FC-TIMING-01 | Buffer input. After current resolution completes, check if buffered input is valid for the next eligible turn. If the speaker's turn is next, hold and replay. If not, discard and notify: "Hold on — it's not your turn yet." |
| FC-TIMING-02 | Pause TTS. Process voice input. If valid command, proceed. If not parseable, resume TTS and discard. System MUST NOT require player to wait for TTS to finish before accepting input. |
| FC-TIMING-03 | Ignore second input. Respond: "I heard you — working on it." Do NOT queue a second action. |
| FC-TIMING-04 | Discard stale transcript. Do not parse. No spoken feedback (player has likely already re-spoken). Log discard with timestamp. |

**Forbidden behavior:**
- Executing an action on a turn that doesn't belong to the speaker
- Queuing multiple intents from a single player's turn
- Processing stale transcripts as current commands
- Forcing the player to wait for TTS to finish before accepting input (FC-TIMING-02 is critical: TTS must be interruptible)

---

### 1.5 FC-AMBIG: Semantic Ambiguity (Entity, Spell, Weapon, Action)

**Definition:** ASR transcript is complete and confident, but the semantic meaning maps to multiple valid game-mechanical interpretations.

**Sub-classes:**

| ID | Sub-class | Example | Ambiguity Type |
|---|---|---|---|
| FC-AMBIG-01 | Entity ambiguity | "Attack the goblin" (3 goblins on field) | Multiple valid targets |
| FC-AMBIG-02 | Spell ambiguity | "Cast cure" (Cure Light Wounds? Cure Moderate? Cure Disease?) | Multiple spells match partial name |
| FC-AMBIG-03 | Weapon ambiguity | "Use my sword" (longsword + short sword equipped) | Multiple weapons match |
| FC-AMBIG-04 | Action interpretation | "I want to stop the ritual" (attack caster? dispel? grapple? ready action?) | Multiple valid action types |
| FC-AMBIG-05 | Spatial ambiguity | "Move behind the pillar" (which pillar? which side?) | Multiple valid positions |
| FC-AMBIG-06 | Numeric ambiguity | "Cast it at third level" (3rd level slot? or the spell Fireball which is 3rd level?) | Multiple numeric interpretations |

**Required behavior:**

| Condition | System Response |
|---|---|
| 2-3 valid interpretations | DM-voice clarification question presenting options naturally: "The goblin by the brazier, or the one near the door?" |
| 4+ valid interpretations | Numbered menu with brief identifiers. Spoken as list. |
| Ambiguity resolvable by game state constraints | Apply constraints FIRST (e.g., only one goblin in melee range → select that one). Log constraint resolution with `[CONSTRAINED]` tag. Announce the constraint: "The goblin in front of you — the others are out of reach." |

**Constraint resolution order (deterministic):**
1. Range/reach filter (eliminate targets out of range for declared action)
2. Line-of-sight filter (eliminate targets not visible)
3. Prior-turn context (STM buffer, max 3 turns)
4. If still ambiguous after filters → ask

**Forbidden behavior:**
- Selecting "nearest" or "most damaged" target without asking
- Using LLM probability to rank interpretations
- Resolving ambiguity by rolling randomly
- Committing any action when 2+ valid interpretations remain after constraint filtering

---

### 1.6 FC-OOG: Out-of-Grammar Utterances

**Definition:** The transcript is valid English but does not correspond to any recognized game action, entity, or system command.

**Sub-classes:**

| ID | Sub-class | Example | Detection |
|---|---|---|---|
| FC-OOG-01 | Nonsense / misparse | "Flurble the snark engine" | No game-lexicon tokens matched |
| FC-OOG-02 | Real-world request | "What time is it?" / "Pause the game" | Recognized as meta-request, not game action |
| FC-OOG-03 | Rules question | "Can I use Power Attack with a light weapon?" | Interrogative structure, no action verb |
| FC-OOG-04 | Narrative-only statement | "My character looks around nervously" | Descriptive, no mechanical intent |
| FC-OOG-05 | Profanity / emotional outburst | "Oh crap!" / "Yes!" (celebration) | Exclamatory, no action content |

**Required behavior:**

| Sub-class | System Response |
|---|---|
| FC-OOG-01 | Discard. Request rephrase: "I'm not sure what you mean. What would you like to do?" |
| FC-OOG-02 | Route to system handler (pause, save, quit). Do NOT process as game action. Respond in Arbor voice (system), not DM voice. |
| FC-OOG-03 | Route to rules-query handler. Box answers the mechanical question. No intent created. DM voice: "Let me check... [Box answer]." |
| FC-OOG-04 | Acknowledge narratively. Do NOT create an intent. DM voice: "Kael glances around, uneasy." No mechanical effect. |
| FC-OOG-05 | Ignore. No response. No intent. No log entry (unless debug mode). |

**Forbidden behavior:**
- Treating a rules question as an action declaration
- Creating a mechanical intent from a narrative statement
- Executing a game action from a meta-request
- Responding to emotional outbursts as if they were commands

---

### 1.7 FC-BLEED: Cross-Mode Bleed (Table Talk as Command)

**Definition:** The system interprets conversational speech (table talk, out-of-character remarks, side conversation) as an in-game command.

**Sub-classes:**

| ID | Sub-class | Example | Risk |
|---|---|---|---|
| FC-BLEED-01 | Table talk as action | "I should probably attack the dragon" (thinking aloud) → system initiates attack | Unintended combat action |
| FC-BLEED-02 | Side conversation | "Can you pass me a drink?" → system tries to parse "pass" as in-game action | Nonsense intent creation |
| FC-BLEED-03 | Quoting / storytelling | "Last session I cast fireball and it was amazing" → system detects "cast fireball" | Ghost action from past-tense narrative |
| FC-BLEED-04 | Hypothetical discussion | "What if I moved here instead?" → system starts movement | Speculative input treated as declarative |

**Detection heuristics (all must be evaluated):**

| Signal | Indicates Table Talk | Weight |
|---|---|---|
| Conditional language ("should", "could", "what if", "maybe") | Likely speculative | HIGH |
| Past tense ("I attacked", "we went", "that was") | Likely retrospective | HIGH |
| No entity/action match in current game state | Likely off-topic | MEDIUM |
| Speaker is not the active player for current turn | Likely table talk (solo mode: N/A) | HIGH |
| Hedging language ("probably", "I think", "I guess") | Possibly speculative | MEDIUM |

**Required behavior:**

| Confidence that input is a command | System Response |
|---|---|
| HIGH (imperative verb + valid target + speaker's turn) | Parse as intent normally |
| MEDIUM (some command signals, some table-talk signals) | Clarify: "Are you saying you want to attack the dragon?" |
| LOW (multiple table-talk signals) | Ignore. Do not parse. No spoken feedback. |

**Forbidden behavior:**
- Parsing conditional/hypothetical language as a committed action
- Creating an intent from past-tense narration
- Processing speech from a non-active player as a command (in future multiplayer)
- Treating "I should..." as equivalent to "I will..."

---

## 2. STOPLIGHT Bias Rules

All voice control-plane decisions are classified by a three-tier STOPLIGHT system. The default bias is FAIL-CLOSED (RED until proven GREEN).

### 2.1 Definitions

| Level | Name | Meaning | Default Bias |
|---|---|---|---|
| GREEN | Proceed | Input is unambiguous, confident, and maps to exactly one intent. System may proceed to confirmation step. | Must be EARNED by passing all filters. |
| YELLOW | Clarify | Input has recoverable ambiguity or moderate confidence. System MUST ask before proceeding. | DEFAULT for any input with ambiguity flags. |
| RED | Reject | Input is unrecoverable, dangerous, or uninterpretable. System MUST discard and reset. | DEFAULT for any input below minimum thresholds. |

### 2.2 Classification Rules

| Condition | Color | Action |
|---|---|---|
| ASR confidence >= GREEN_THRESHOLD (configurable, default 0.85) AND exactly 1 intent parse AND all required fields populated AND no table-talk signals | GREEN | Proceed to soft confirmation |
| ASR confidence >= YELLOW_THRESHOLD (configurable, default 0.50) AND < GREEN_THRESHOLD | YELLOW | Request repeat or clarify |
| ASR confidence < YELLOW_THRESHOLD | RED | Discard. "I didn't catch that." |
| ASR confidence >= GREEN_THRESHOLD BUT 2+ intent parses | YELLOW | Clarify: present options |
| ASR confidence >= GREEN_THRESHOLD BUT missing required intent fields | YELLOW | Query for missing fields |
| Any table-talk signal detected (FC-BLEED) with MEDIUM+ weight | YELLOW | Clarify: "Are you saying you want to...?" |
| Multiple HIGH-weight table-talk signals | RED | Ignore. No parse. |
| Transcript matches FC-OOG-01 (no lexicon match) | RED | Discard. Request rephrase. |
| Transcript matches FC-OOG-02 through FC-OOG-05 | ROUTING | Route to appropriate non-intent handler (not RED, not GREEN — routed out of intent pipeline) |

### 2.3 Promotion Rules (RED/YELLOW -> GREEN)

An input may only be promoted from YELLOW to GREEN by:
1. Player verbally confirming a clarification question ("Yes", "The first one", "The goblin by the door")
2. Player selecting from a numbered menu
3. Game-state constraint filtering reducing options to exactly 1

An input may NEVER be promoted from RED to GREEN. RED inputs are terminal. The player must re-speak.

### 2.4 Demotion Rules (GREEN -> YELLOW/RED)

A GREEN input is demoted to YELLOW if:
- Post-parse validation reveals the action is impossible (out of range, wrong turn, etc.)
- The action would trigger an irreversible high-consequence outcome (e.g., attacking an ally) — require explicit confirmation

A GREEN input is demoted to RED if:
- Post-parse validation reveals the action violates game rules in a way that cannot be clarified (e.g., casting a spell the character doesn't know)

### 2.5 Authority Boundary

The STOPLIGHT system operates in the LENS layer. It governs presentation and interaction flow. It MUST NOT:
- Override Box mechanical resolution
- Grant or deny mechanical permissions (that is Box authority)
- Use LLM probability scores to promote YELLOW to GREEN
- Make "probably" judgments about player intent

The STOPLIGHT system MAY:
- Use ASR confidence scores (acoustic model output, not LLM inference)
- Use game-state constraint filters (range, LOS, equipment — deterministic Box queries)
- Use lexicon matching (dictionary lookup, not probabilistic NLP)

---

## 3. Clarification Budget Policy

### 3.1 Purpose

Prevent infinite clarification loops. Every ambiguous input gets a finite number of attempts to reach GREEN before the system cancels the action.

### 3.2 Budget Parameters

| Parameter | Value | Rationale |
|---|---|---|
| MAX_CLARIFICATIONS | 2 | Two questions maximum before escalating. A third question means the system is failing, not the player. |
| ESCALATION_ACTION | Present numbered menu | After 2 failed clarifications, show all valid options as a numbered list. Player selects by number or voice ("the first one"). |
| MENU_TIMEOUT | 30 seconds (configurable) | If player does not respond to the menu within timeout, cancel. |
| CANCEL_PHRASE | "Never mind" / "Cancel" / silence timeout | Player may explicitly cancel at any point, or silence triggers cancel. |
| SILENCE_TIMEOUT | 15 seconds (configurable) | If player says nothing for this duration after a clarification question, cancel the pending intent. |

### 3.3 Clarification Escalation Ladder

```
ATTEMPT 0: Initial voice input
  -> If GREEN: proceed to soft confirmation
  -> If YELLOW: ask clarification question #1

ATTEMPT 1: First clarification response
  -> If GREEN: proceed to soft confirmation
  -> If still YELLOW: ask clarification question #2 (MUST differ from #1)
  -> If RED: cancel. "Let's start over. What would you like to do?"

ATTEMPT 2: Second clarification response
  -> If GREEN: proceed to soft confirmation
  -> If still YELLOW: ESCALATE to numbered menu
  -> If RED: cancel.

MENU: Numbered menu presented
  -> Valid selection: proceed to soft confirmation
  -> Invalid selection: cancel. "Let me know when you're ready."
  -> Timeout: cancel. "Taking that as a pass. Let me know when you're ready."
```

### 3.4 Clarification Question Rules

1. **No repetition.** If clarification #1 asks "Which goblin?", clarification #2 MUST NOT ask "Which goblin?" again. It must rephrase or add context: "The one by the door, or the one near the fire?"
2. **Increasing specificity.** Each subsequent question must provide MORE context, not less.
3. **DM voice only.** All clarification questions use DM persona, not system voice. The player should feel like the DM is asking, not a computer.
4. **No leading questions.** Never phrase a clarification to suggest a preferred answer. "Did you mean the goblin?" is forbidden if there are 3 goblins. Use "Which goblin?" instead.
5. **No mechanical jargon in questions.** "Which goblin?" is correct. "Which target entity?" is forbidden.

### 3.5 Cancel Semantics

| Trigger | Effect | Spoken Feedback |
|---|---|---|
| Player says "cancel" / "never mind" / "stop" | Discard pending intent immediately. Return to prompt. | "Got it. Your action?" |
| Silence timeout (15s) after clarification | Discard pending intent. Return to prompt. | "I didn't catch that. Let me know when you're ready." |
| Menu timeout (30s) | Discard pending intent. Return to prompt. | "Taking that as a pass. Your action?" |
| Player says "wait" / "hold on" | Pause timeout counter. Resume on next speech. | No spoken feedback (silence is acknowledgment). |

**Cancel invariants:**
- Cancel NEVER triggers a partial action
- Cancel NEVER penalizes the player (no lost turn, no wasted action)
- Cancel returns the game state to EXACTLY the state before the failed input
- Cancel is logged with `[CANCELLED]` provenance tag for audit

---

## 4. Cross-Cutting Rules

### 4.1 No Silent Commit

No mechanical action may be committed to the game state based on voice input unless the intent has reached `confirmed` status in the VICP-001 lifecycle. "Confirmed" requires either:
- Explicit verbal confirmation ("Yes", "Do it", "Go ahead")
- Soft confirmation (system states the action; player does not object within 3 seconds)
- Menu selection

### 4.2 No Probabilistic Resolution

The system MUST NOT use LLM inference, embedding similarity, or probabilistic NLP to resolve ambiguity in voice commands. Resolution methods are limited to:
- Exact lexicon matching
- Game-state constraint filtering (deterministic Box queries)
- Direct player clarification

### 4.3 Provenance Tagging

Every voice-derived intent MUST carry provenance metadata:

| Tag | Meaning |
|---|---|
| `[VOICE]` | Intent originated from voice input |
| `[INFERRED]` | One or more fields were inferred (only permitted per FC-PARTIAL-02 single-weapon rule) |
| `[CONSTRAINED]` | Ambiguity resolved by game-state constraint filtering |
| `[CLARIFIED]` | Player answered a clarification question to resolve ambiguity |
| `[MENU-SELECTED]` | Player selected from a numbered menu |
| `[CANCELLED]` | Intent was cancelled before confirmation |

### 4.4 Replay Compatibility

All voice failure handling MUST be deterministic given the same inputs. Specifically:
- The same transcript + game state MUST produce the same STOPLIGHT classification
- The same clarification sequence MUST produce the same escalation path
- Constraint filtering MUST be order-independent and deterministic (sorted by canonical entity ID)

### 4.5 TTS Interruptibility

Per FC-TIMING-02: System TTS MUST be interruptible by player speech at all times. The player is never forced to wait for the system to finish speaking before issuing a command. This is a hard UX requirement, not a suggestion.

---

## 5. Operator-Facing Checklist (Unit-Test-Convertible)

Each row maps a signal condition to an expected system behavior. Format: `[SIGNAL] -> [EXPECTED BEHAVIOR]`.

### 5.1 ASR Failure Signals

| # | Signal | Expected Behavior | STOPLIGHT |
|---|---|---|---|
| T-ASR-01 | ASR returns empty string | No intent created. Spoken: "I didn't catch that." Return to prompt. | RED |
| T-ASR-02 | ASR confidence = 0.40 (below YELLOW_THRESHOLD 0.50) | Transcript discarded. Spoken: "I didn't catch that." | RED |
| T-ASR-03 | ASR confidence = 0.60 (YELLOW zone) | Transcript held. Spoken: "Could you say that again?" No intent created. | YELLOW |
| T-ASR-04 | ASR confidence = 0.90, single valid parse | Intent created at `pending`. Proceed to soft confirmation. | GREEN |
| T-ASR-05 | Transcript truncated mid-word | Partial held. Spoken: "You were saying...?" | YELLOW |
| T-ASR-06 | ASR delivers transcript 8 seconds after speech ended | Transcript discarded. No feedback. Logged with timestamp. | RED |

### 5.2 Homophone and Ambiguity Signals

| # | Signal | Expected Behavior | STOPLIGHT |
|---|---|---|---|
| T-HOMO-01 | "Bane" spoken; spell Bane AND NPC Bain in game state | Clarify: "The spell, or are you talking to Bain?" | YELLOW |
| T-HOMO-02 | "Mace" spoken; only weapon Mace in lexicon (no spell Maze known) | Accept as weapon. Proceed. | GREEN |
| T-HOMO-03 | "Attack the guard"; 3 guards on field | Clarify: "Which guard?" with identifiers. | YELLOW |
| T-HOMO-04 | "Attack the guard"; 1 guard on field | Accept. Proceed to confirmation. | GREEN |

### 5.3 Partial Input Signals

| # | Signal | Expected Behavior | STOPLIGHT |
|---|---|---|---|
| T-PART-01 | "I attack!" (no target specified) | Query: "Who are you attacking?" | YELLOW |
| T-PART-02 | "Hit the goblin" (player has longsword only, goblin in melee range) | Infer longsword. Log `[INFERRED]`. Proceed to confirmation: "Attacking the goblin with your longsword?" | GREEN (with inference) |
| T-PART-03 | "Hit the goblin" (player has longsword + short sword) | Query: "With your longsword or short sword?" | YELLOW |
| T-PART-04 | "Hit him" (no antecedent in last 3 turns) | Query: "Who do you mean?" | YELLOW |
| T-PART-05 | "Hit him" (attacked Goblin Scout last turn, within 3-turn STM window) | Resolve pronoun to Goblin Scout. Log `[CONSTRAINED]`. Proceed. | GREEN |

### 5.4 Timing Signals

| # | Signal | Expected Behavior | STOPLIGHT |
|---|---|---|---|
| T-TIME-01 | Player speaks during NPC turn resolution | Buffer input. Process after NPC resolution if player's turn is next. Otherwise: "Hold on — it's not your turn yet." | YELLOW (buffered) |
| T-TIME-02 | Player speaks while TTS is playing narration | Pause TTS. Process input. If valid, proceed. If not, resume TTS. | GREEN (input accepted) |
| T-TIME-03 | Player repeats "Attack the goblin" while first instance is in `pending` | Ignore second. Spoken: "I heard you — working on it." | RED (duplicate) |
| T-TIME-04 | ASR transcript arrives 6s after speech-end | Discard. No feedback. Logged. | RED |

### 5.5 Semantic Ambiguity Signals

| # | Signal | Expected Behavior | STOPLIGHT |
|---|---|---|---|
| T-AMBIG-01 | "Cast cure" — player knows Cure Light Wounds and Cure Moderate Wounds | Clarify: "Cure Light Wounds or Cure Moderate Wounds?" | YELLOW |
| T-AMBIG-02 | "Cast cure" — player knows only Cure Light Wounds | Accept. No ambiguity. Proceed. | GREEN |
| T-AMBIG-03 | "Move behind the pillar" — 2 pillars in LOS | Clarify: "The pillar on the left or the right?" | YELLOW |
| T-AMBIG-04 | "Attack the goblin" — 3 goblins, but only 1 in melee range and player has no ranged weapon | Constraint filter: only 1 reachable. Accept. Log `[CONSTRAINED]`. Announce: "The goblin in front of you." | GREEN |
| T-AMBIG-05 | "I want to stop the ritual" — multiple valid action types | Clarify: "How? Attack the caster, try to dispel it, or something else?" | YELLOW |

### 5.6 Out-of-Grammar Signals

| # | Signal | Expected Behavior | STOPLIGHT |
|---|---|---|---|
| T-OOG-01 | "Flurble the snark" (no lexicon match) | Discard. Spoken: "I'm not sure what you mean. What would you like to do?" | RED |
| T-OOG-02 | "Pause the game" (system command) | Route to system handler. Pause game. Arbor voice: "Game paused." No intent created. | ROUTING |
| T-OOG-03 | "Can I use Power Attack with a dagger?" (rules question) | Route to rules-query handler. Box answers. No intent created. | ROUTING |
| T-OOG-04 | "My character looks around nervously" (narrative) | Acknowledge narratively. No intent. No mechanical effect. | ROUTING |
| T-OOG-05 | "Oh crap!" (exclamation) | Ignore. No response. No intent. | RED (silent) |

### 5.7 Cross-Mode Bleed Signals

| # | Signal | Expected Behavior | STOPLIGHT |
|---|---|---|---|
| T-BLEED-01 | "I should probably attack the dragon" (conditional + hedging) | Do NOT parse. Ignore or clarify: "Are you saying you want to attack the dragon?" | YELLOW or RED |
| T-BLEED-02 | "Last time I cast fireball" (past tense) | Ignore. No parse. No feedback. | RED (silent) |
| T-BLEED-03 | "What if I moved over here?" (hypothetical) | Do NOT create movement intent. Optionally answer: "You could reach that spot this turn." No mechanical action. | ROUTING |
| T-BLEED-04 | "Can you pass me a drink?" (side conversation) | Ignore. No parse. No feedback. | RED (silent) |

### 5.8 Clarification Budget Signals

| # | Signal | Expected Behavior | STOPLIGHT |
|---|---|---|---|
| T-BUDGET-01 | 2 clarification attempts failed (still YELLOW) | Escalate to numbered menu. | YELLOW -> MENU |
| T-BUDGET-02 | Player silent for 15s after clarification question | Cancel pending intent. Return to prompt. | RED (timeout) |
| T-BUDGET-03 | Player says "cancel" during clarification | Discard intent immediately. Spoken: "Got it. Your action?" | RED (explicit cancel) |
| T-BUDGET-04 | Player says "wait" during clarification | Pause timeout. Resume on next speech. | YELLOW (paused) |
| T-BUDGET-05 | Menu presented; player silent for 30s | Cancel. Spoken: "Taking that as a pass. Your action?" | RED (timeout) |
| T-BUDGET-06 | Menu presented; player says "the second one" | Accept option 2. Proceed to confirmation. | GREEN |

---

## 6. Configuration Parameters (Tunable)

These values are operator-configurable. Defaults are fail-safe (biased toward asking rather than guessing).

| Parameter | Default | Min | Max | Unit |
|---|---|---|---|---|
| GREEN_THRESHOLD | 0.85 | 0.70 | 0.99 | ASR confidence (0-1) |
| YELLOW_THRESHOLD | 0.50 | 0.30 | 0.80 | ASR confidence (0-1) |
| MAX_CLARIFICATIONS | 2 | 1 | 3 | count |
| SILENCE_TIMEOUT | 15 | 5 | 60 | seconds |
| MENU_TIMEOUT | 30 | 10 | 120 | seconds |
| STALE_TRANSCRIPT_THRESHOLD | 5 | 2 | 15 | seconds |
| STM_BUFFER_DEPTH | 3 | 1 | 5 | turns |
| SOFT_CONFIRM_WINDOW | 3 | 1 | 10 | seconds |

**Constraint:** GREEN_THRESHOLD MUST be > YELLOW_THRESHOLD. The system MUST reject configuration where GREEN_THRESHOLD <= YELLOW_THRESHOLD.

---

## 7. Stop Conditions Verified

- **No engine mechanics changes:** This document specifies voice control-plane behavior only. Box resolution, dice rolling, state mutation are untouched.
- **No Box-layer authority leakage:** All mechanical decisions remain with Box. The STOPLIGHT system operates in LENS. Constraint filtering queries Box read-only; it never writes.
- **No doctrine file modifications:** All references to doctrine are read-only citations.
- **No code modifications:** This is policy/spec only.

---

*This research document fulfills WO-VOICE-RESEARCH-02 acceptance criteria 1-6. Criterion 7 (tests pass) verified separately.*
