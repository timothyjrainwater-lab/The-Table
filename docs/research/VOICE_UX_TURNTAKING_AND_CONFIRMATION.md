# Voice UX: Turn-Taking and Confirmation Patterns

**Work Order:** WO-VOICE-RESEARCH-04
**Status:** RESEARCH COMPLETE
**Date:** 2026-02-13
**Author:** Sonnet D (Agent)
**Authority:** PM-approved research deliverable

---

## 1. Purpose

This document specifies turn-taking states, confirmation patterns, interruption behavior, disambiguation UX, and table-talk separation for voice-first tabletop play. All patterns are optimized for low-friction, high-correctness control and obey deterministic commit rules established by the Box architecture.

**Binding references:**
- `RQ_AUDIOFIRST_CLI_CONTRACT_V1.md` (output grammar, salience hierarchy)
- `RQ_INTERACT_001_VOICE_FIRST.md` (intent parsing, confirmation loop)
- `SONNET-H_WO-024_VOICE_INTENT.md` (voice intent parser, clarification engine)
- `SPARK_LENS_BOX_DOCTRINE.md` (Box authority boundaries)

**Scope constraint:** This spec is INTERACTION DESIGN ONLY. It does not modify engine mechanics, Box resolution, game state, or TTS backend internals. It specifies how the operator and system exchange turns during voice-first play.

---

## 2. Turn-Taking State Machine

### 2.1 States (Exhaustive)

The voice interaction loop has exactly six states. The system is always in exactly one.

| State | System Behavior | Operator Hears | Operator Does |
|---|---|---|---|
| **LISTENING** | VAD active, STT streaming, intent parser primed | Silence (or faint ambient tone if configured) | Speaks intent naturally |
| **PROCESSING** | STT finalizes transcript, intent parser runs, confidence scored | Brief acknowledgment tone (< 200ms) | Waits; may barge-in to cancel or amend |
| **DECLARING** | System announces its interpretation of operator intent | DM persona speaks parsed intent back: "Kael attacks Goblin Scout with longsword." | Listens; may barge-in to correct |
| **AWAITING_CONFIRM** | System waits for operator confirmation or correction | Arbor voice: "Confirm?" (or presents options if ambiguous) | Says "yes" / "no" / correction / option number |
| **EXECUTING** | Box resolves the confirmed action; dice roll, state mutation | Rolling sound cue (optional); silence during resolution | Waits; cannot barge-in (commit in progress) |
| **NARRATING** | TTS speaks result + narration per AudioFirst CLI Contract | DM persona speaks Action Result + Narration Block + Alerts | Listens; may barge-in to skip narration |

### 2.2 State Transition Table

```
LISTENING ──[transcript received]──> PROCESSING
PROCESSING ──[high confidence ≥0.8]──> DECLARING
PROCESSING ──[medium confidence 0.5-0.8]──> AWAITING_CONFIRM (with clarification)
PROCESSING ──[low confidence <0.5]──> AWAITING_CONFIRM (with re-prompt)
PROCESSING ──[barge-in detected]──> LISTENING (cancel current parse)
DECLARING ──[no objection within 1.5s]──> EXECUTING
DECLARING ──[barge-in / "no" / "wait"]──> AWAITING_CONFIRM
AWAITING_CONFIRM ──[confirmed: "yes" / option selected]──> EXECUTING
AWAITING_CONFIRM ──[denied: "no" / correction spoken]──> LISTENING
AWAITING_CONFIRM ──[timeout: 8s silence]──> TIMEOUT_PROMPT (see §3.3)
EXECUTING ──[resolution complete]──> NARRATING
NARRATING ──[narration complete]──> LISTENING (next turn)
NARRATING ──[barge-in: "skip" / new intent]──> LISTENING (truncate narration)
```

### 2.3 State Invariants

- **EXECUTING is non-interruptible.** Once Box begins resolution, no barge-in is accepted. Commit semantics are atomic. Rationale: partial resolution would corrupt game state.
- **LISTENING is the default idle state.** If no input arrives for the idle timeout (§3.3), the system remains in LISTENING. It does not re-prompt unprompted.
- **Only one state is active at any time.** Concurrent voice input during NARRATING triggers a barge-in transition, not parallel processing.
- **State transitions are logged.** Every transition emits a `[AIDM] STATE: {from} -> {to}` system message (display only, never spoken).

---

## 3. Interruption, Timeout, and Retry Rules

### 3.1 Barge-In Behavior

Barge-in allows the operator to interrupt system speech. Behavior varies by current state:

| Current State | Barge-In Allowed | Effect |
|---|---|---|
| **LISTENING** | N/A (system is silent) | N/A |
| **PROCESSING** | YES | Cancel current parse, return to LISTENING. Acknowledgment tone suppressed. |
| **DECLARING** | YES | Halt declaration speech. Transition to AWAITING_CONFIRM with operator's correction as new input. |
| **AWAITING_CONFIRM** | YES | New speech replaces previous input. Re-enter PROCESSING with new transcript. |
| **EXECUTING** | **NO** | Barge-in ignored. If operator speaks, buffer input for next LISTENING state. Audible "locked" cue (two short tones) signals commit-in-progress. |
| **NARRATING** | YES | Halt narration TTS immediately. If operator said "skip" / "next", transition to LISTENING for next turn. If operator spoke a new intent, transition to PROCESSING with that intent. |

**Barge-in detection requirements:**
- VAD must distinguish operator speech from ambient table noise (dice rolling, page turning, cross-talk). Minimum energy threshold: configurable, default -40 dB relative to calibrated voice level.
- Barge-in activates only after 200ms of sustained speech energy above threshold (prevents false triggers from coughs or single-syllable noise).
- During NARRATING, barge-in sensitivity is REDUCED (threshold raised by +6 dB) to avoid accidental interruption during quiet listener reactions ("hmm", "ooh").

### 3.2 Timeout Rules

All timeouts use fail-closed semantics: when a timeout fires, the system does NOT assume intent or execute a default action. It either re-prompts or returns to safe idle.

| Context | Timeout Duration | On Timeout |
|---|---|---|
| **LISTENING (operator's turn)** | No timeout | System waits indefinitely. Operator controls pacing. |
| **AWAITING_CONFIRM** | 8 seconds | Transition to TIMEOUT_PROMPT: Arbor says "Still thinking, or should I repeat that?" |
| **TIMEOUT_PROMPT response** | 8 seconds | If no response: Arbor says "No worries. Your action whenever you're ready." Return to LISTENING. |
| **DECLARING (auto-confirm window)** | 1.5 seconds | If no barge-in: proceed to EXECUTING. Not a timeout failure — this is the happy path. |
| **PROCESSING** | 3 seconds | If parse takes >3s (abnormal): Arbor says "Give me a moment..." Display `[AIDM] PARSE: processing`. |

### 3.3 Retry Limits (Fail-Closed)

Retries prevent infinite clarification loops. The system fails closed after the limit: it does NOT guess or execute a default action.

| Scenario | Max Retries | After Max Retries |
|---|---|---|
| **Low-confidence parse** | 2 | Arbor: "I'm not sure what you'd like to do. Say your action clearly, or say 'help' for options." Return to LISTENING. |
| **Clarification loop (disambiguation)** | 3 | Arbor: "Let me list what I can see. [Reads available actions from game state]. Pick one, or describe what you want." |
| **Confirmation denied ("no") repeatedly** | 3 | Arbor: "Understood, let's start fresh. What would you like to do?" Clear STM context for current action. Return to LISTENING. |
| **STT failure (garbled/empty transcript)** | 2 | Arbor: "I couldn't catch that. Try speaking a bit louder or closer." If still failing after retry: `[AIDM] WARNING: STT quality degraded. Check microphone.` |

**Fail-closed guarantee:** At no point does the system execute a mechanical action (attack, spell, move) without explicit operator confirmation. If all retries are exhausted, the turn remains with the operator in LISTENING state.

---

## 4. Confirmation Discipline

### 4.1 Confidence-Based Routing

The voice intent parser (WO-024) assigns confidence scores. Confirmation UX adapts:

| Confidence | Route | System Says | Operator Says |
|---|---|---|---|
| **High (≥ 0.8)** | DECLARING (auto-confirm window) | "Kael attacks Goblin Scout with longsword." [1.5s pause] | Nothing (silence = confirm) OR "wait" / "no" to interrupt |
| **Medium (0.5–0.8)** | AWAITING_CONFIRM (soft confirm) | "Attack the goblin scout — with your longsword?" | "Yes" / "No, with my greataxe" / correction |
| **Low (< 0.5)** | AWAITING_CONFIRM (re-prompt) | "I didn't quite catch that. What would you like to do?" | Re-states intent clearly |

### 4.2 Auto-Confirm Rules

High-confidence intents use a 1.5-second auto-confirm window to reduce friction:

1. System speaks the declaration in DM persona.
2. 1.5 seconds of silence = confirmed. Transition to EXECUTING.
3. Any operator speech within the window = barge-in. Transition to AWAITING_CONFIRM.
4. "Wait", "hold on", "no", "stop" = explicit denial. Transition to AWAITING_CONFIRM.

**Why 1.5 seconds:** Research on conversational turn-taking shows ~200ms is the natural inter-turn gap. 1.5s gives the operator 7x the natural gap to object — generous enough to feel unhurried, short enough to maintain flow. Adjustable in config (range: 1.0–3.0s).

### 4.3 Destructive Action Override

Certain actions are classified as **destructive** (irreversible or high-consequence). These NEVER auto-confirm regardless of confidence:

| Destructive Action | Forced Confirmation |
|---|---|
| Friendly fire (area spell hitting allies) | "Kael is in the blast radius. Proceed anyway?" |
| Last resort ability (once per day/rest) | "That's your last Fireball for today. Confirm?" |
| Withdraw from combat (provokes opportunity attack) | "That will provoke an attack of opportunity. Go ahead?" |
| Use consumable item (potion, scroll) | "Use your Potion of Healing? You have 1 remaining." |

Destructive actions always require an explicit "yes" or "confirm". Silence does not confirm.

### 4.4 Confirmation Phrasing Rules

- Confirmations are spoken by **Arbor** (operator signal voice), not the DM persona. This audibly separates mechanical questions from narrative flow.
- Confirmations are **one sentence maximum**. No preamble, no justification.
- Confirmations end with a rising intonation (question mark). TTS must render this as a question.
- Affirmative keywords: "yes", "yeah", "yep", "do it", "confirm", "go", "proceed", "fire", "send it".
- Negative keywords: "no", "nope", "cancel", "wait", "hold on", "stop", "nevermind", "scratch that".

---

## 5. Disambiguation UX Patterns

### 5.1 Numbered Menu Pattern

When the system identifies multiple valid interpretations, it presents a short numbered menu. The operator responds with a number instead of re-describing intent.

**Rules:**
- Maximum 3 options per menu (Amazon VUI research: >3 options exceed auditory short-term memory).
- Options are spoken as "Option 1: ... Option 2: ... Option 3: ..."
- Operator responds with just the number: "one", "two", "three" (or "1", "2", "3").
- If none fit, operator says "none of those" or describes intent differently.

**Example — Ambiguous Target:**
```
SYSTEM (Arbor): "Which goblin?
  Option 1: Goblin Scout, near the brazier.
  Option 2: Goblin Shaman, by the door.
  Option 3: Both — cleave attack."
OPERATOR: "Two."
SYSTEM (DM): "Kael attacks Goblin Shaman with longsword."
```

### 5.2 Binary Choice Pattern

When disambiguation has exactly two options, use a simpler "X or Y?" format without numbers.

**Example — Ambiguous Weapon:**
```
SYSTEM (Arbor): "Longsword or greataxe?"
OPERATOR: "Greataxe."
```

### 5.3 Spatial Disambiguation Pattern

When the operator specifies area targeting but placement is ambiguous, the system proposes a placement and asks for adjustment.

**Example — Fireball Placement:**
```
SYSTEM (Arbor): "I can center the fireball to hit two of the three goblins.
  Option 1: Hit the scout and shaman. The archer is out of range.
  Option 2: Hit the scout and archer. The shaman is out of range.
  Move it yourself: say 'nudge left', 'nudge right', or 'five feet north'."
OPERATOR: "Option one."
```

### 5.4 Escalating Help Pattern

If the operator seems stuck (2+ low-confidence parses in a row), the system proactively offers structured help. Three tiers:

**Tier 1 — Rephrase request:**
```
SYSTEM (Arbor): "Could you say that differently?"
```

**Tier 2 — Available actions (after 2 failures):**
```
SYSTEM (Arbor): "Here's what you can do:
  Option 1: Attack — melee or ranged.
  Option 2: Cast a spell.
  Option 3: Move — up to 30 feet."
```

**Tier 3 — Full context dump (after 3 failures):**
```
SYSTEM (Arbor): "Let me lay it out. You have a longsword and a shortbow equipped.
  You can see Goblin Scout at 10 feet and Goblin Shaman at 25 feet.
  You have 2 spell slots remaining: Shield and Magic Missile prepared.
  What would you like to do?"
```

### 5.5 Disambiguation Invariants

- All disambiguation is spoken by **Arbor** (not DM persona). Operator hears the vocal distinction.
- Options use concrete game terms (entity names, weapon names, distances), not vague descriptions.
- Options are ordered by likelihood (most probable interpretation first).
- The system NEVER presents more than 3 options in a single prompt.
- If >3 interpretations exist, system filters to top 3 by confidence and offers "or something else?" as an escape.

---

## 6. Table-Talk Separation (Mode Discipline)

### 6.1 Problem

During tabletop play, the operator talks to other players, makes jokes, discusses rules, and engages in social chatter. The system must NOT interpret table talk as mechanical commands.

### 6.2 Mode Architecture

The system operates in two modes, distinguished by an explicit activation boundary:

| Mode | Trigger Enter | Trigger Exit | System Behavior |
|---|---|---|---|
| **COMMAND** | System prompts "Your action?" / operator says wake phrase | Action confirmed and execution begins / operator says "never mind" | Full voice pipeline active: STT → Parse → Confirm → Execute |
| **AMBIENT** | Execution completes / operator disengages | System prompts "Your action?" / operator says wake phrase | TTS output for narration only. STT is OFF or in wake-word-only mode. No intent parsing. |

### 6.3 Activation Boundary

**Entering COMMAND mode:**
1. **System-initiated:** When it's the operator's turn, the system speaks "Your action?" and enters COMMAND mode automatically. This is the primary path. The operator does not need a wake word during their turn.
2. **Operator-initiated (out of turn):** Operator says the wake phrase (default: "Hey DM" — configurable). System enters COMMAND mode. Use case: asking a question, requesting a ruling, or using a reaction ability.

**Exiting COMMAND mode:**
1. **Action confirmed:** After the confirmed action enters EXECUTING, the system exits COMMAND mode. Narration plays in AMBIENT mode.
2. **Explicit disengage:** Operator says "never mind" / "cancel" / "I'm done." System returns to AMBIENT mode.
3. **Idle timeout:** 30 seconds of silence in COMMAND mode with no parseable input. Arbor says "I'll be here when you're ready." Returns to AMBIENT mode.

### 6.4 Audible Mode Cues

The operator must always know which mode is active. Audible cues (not spoken words) signal transitions:

| Transition | Cue |
|---|---|
| AMBIENT → COMMAND | Soft ascending chime (2 notes, 200ms total) |
| COMMAND → AMBIENT | Soft descending chime (2 notes, 200ms total) |
| Barge-in accepted | Single tap tone (50ms) |
| Barge-in rejected (EXECUTING) | Double tap tone (2x 50ms) |
| Timeout warning (AWAITING_CONFIRM) | Gentle single tone at 6s of 8s timeout |

### 6.5 Table-Talk Filtering Rules

Even in COMMAND mode, the system applies table-talk filters before parsing:

| Filter | Detection Method | Result |
|---|---|---|
| **Side conversation** | Transcript contains second-person address not directed at system ("Hey Mike, pass the chips") | Ignore; remain in LISTENING |
| **Laughter / exclamation** | STT transcript is purely reactive ("haha", "oh no", "nice") with no verb | Ignore; remain in LISTENING |
| **Rules discussion** | Transcript references out-of-game concepts ("what page is that on", "check the PHB") | Ignore; remain in LISTENING |
| **Meta-game commentary** | Transcript uses meta language ("I should probably...", "what if I...") without imperative | Ignore; remain in LISTENING. Exception: if followed by a verb + target within 3s, treat as intent preamble. |

**False positive recovery:** If the system incorrectly parses table talk as intent and enters DECLARING, the operator's barge-in ("no, I was talking to Mike") immediately returns to LISTENING. The clarification engine (WO-024) handles this with: "Sorry about that. Your action whenever you're ready."

---

## 7. End-of-Turn Signaling

### 7.1 Problem

In voice-only interaction, the system must know when the operator is done speaking. Premature cutoff feels rude; waiting too long feels sluggish.

### 7.2 End-of-Utterance Detection

| Method | Parameters | Priority |
|---|---|---|
| **VAD silence detection** | 700ms of silence after speech energy drops below threshold | Primary |
| **Explicit end marker** | Operator says "that's it", "go", "do it", "end turn" | Immediate (overrides VAD wait) |
| **Grammatical completeness** | STT streaming detects complete sentence with period-equivalent prosody | Secondary (supplements VAD) |

**700ms silence threshold rationale:** Natural intra-sentence pauses are typically 200-500ms. 700ms is long enough to avoid cutting off mid-thought, short enough to feel responsive. Configurable (range: 500ms–1500ms).

### 7.3 Multi-Part Utterance Handling

Operators sometimes issue multi-part commands: "Move to the door... [pause] ...and attack the goblin."

**Handling rules:**
1. After 700ms silence, system tentatively finalizes the transcript.
2. If a new utterance begins within 2 seconds and starts with a conjunction ("and", "then", "also"), it is appended to the current transcript as a continuation.
3. If the new utterance begins after 2 seconds or lacks a conjunction, it is treated as a new separate command.
4. The intent parser (WO-024) handles compound intents by extracting the first action. If multiple actions are detected, the system queues them: "I heard two actions. Let's do the move first, then the attack."

---

## 8. Audio Feedback Design

### 8.1 Non-Speech Audio Cues

Audio cues are short, non-verbal sounds that communicate system state without interrupting conversation flow.

| Cue | Sound Description | Duration | Trigger |
|---|---|---|---|
| **Mode enter (COMMAND)** | Rising two-note chime (C5→E5) | 200ms | AMBIENT → COMMAND transition |
| **Mode exit (AMBIENT)** | Falling two-note chime (E5→C5) | 200ms | COMMAND → AMBIENT transition |
| **Acknowledgment** | Soft single click | 80ms | LISTENING → PROCESSING (transcript received) |
| **Commit locked** | Two short taps | 2x 50ms, 50ms gap | Barge-in attempted during EXECUTING |
| **Timeout warning** | Gentle bell | 150ms | 6s into 8s AWAITING_CONFIRM timeout |
| **Error / STT failure** | Low double-tone | 2x 100ms, descending pitch | STT returned empty/garbled transcript |
| **Dice rolling** | Physical dice rattle (optional) | 500ms–1500ms | During EXECUTING for attack/save rolls |

### 8.2 Audio Cue Design Rules

- All cues are ≤ 200ms except dice roll (thematic, skippable).
- Cues are mixed at -12 dB relative to TTS speech (audible but not startling).
- Cues are NEVER spoken words (no "beep" or "ding" spoken aloud — they are synthesized tones).
- Cues can be disabled entirely in config (`audio_cues: false`).
- Cues must not be TTS-routed (they bypass the TTS pipeline entirely and play as PCM samples).

---

## 9. Latency Targets

| Phase | Target Latency | Measured From | Measured To |
|---|---|---|---|
| **Wake phrase detection** | < 300ms | Operator finishes wake phrase | Mode chime plays |
| **STT finalization** | < 600ms | End of utterance (VAD silence) | Transcript available to parser |
| **Intent parsing** | < 50ms | Transcript received | ParseResult available (WO-024 measured: ~50ms) |
| **Declaration TTS start** | < 400ms | ParseResult ready | First audio of declaration plays |
| **Confirmation processing** | < 200ms | Operator says "yes"/"no" | State transition fires |
| **Box resolution** | < 2000ms | EXECUTING entered | Resolution complete, results ready |
| **Narration TTS start** | < 400ms | Resolution complete | First audio of narration plays |
| **Total intent-to-narration** | < 4000ms | End of operator utterance | Narration begins playing |

**Streaming constraint:** TTS MUST use streaming playback. Audio begins as soon as the first chunk is synthesized, not after the entire utterance is rendered. This is critical for narration blocks (1-3 sentences) where batch rendering would add 1-2s of dead air.

---

## 10. Example Micro-Dialogues

### Dialogue 1: Happy Path — High Confidence Attack

```
STATE: LISTENING
[chime: mode enter]
ARBOR: "Your action?"
OPERATOR: "Attack the goblin with my sword."
[click: acknowledgment]
STATE: PROCESSING → DECLARING (confidence: 0.92)
DM: "Kael attacks Goblin Scout with longsword."
[1.5s silence — no objection]
STATE: EXECUTING
[dice rattle sound]
STATE: NARRATING
DM: "Longsword hits Goblin Scout. Moderate wound."
DM: "Steel bites into the goblin's leather armor. The creature snarls,
     stumbling back a half-step before steadying itself."
[chime: mode exit]
STATE: AMBIENT → next entity's turn
```

### Dialogue 2: Medium Confidence — Soft Confirm

```
STATE: LISTENING
ARBOR: "Your action?"
OPERATOR: "Uh, fireball... the group over there."
[click: acknowledgment]
STATE: PROCESSING → AWAITING_CONFIRM (confidence: 0.65)
ARBOR: "Cast Fireball — centered on the goblin group to the east?"
OPERATOR: "Yeah."
STATE: EXECUTING
[dice rattle sound]
STATE: NARRATING
DM: "Fireball strikes Goblin Scout and Goblin Shaman. Devastating blast."
DM: "A sphere of flame erupts among the goblins. The shaman's robes
     catch fire as the scout is hurled backward by the concussion."
ARBOR: "Goblin Scout is DEFEATED."
[chime: mode exit]
```

### Dialogue 3: Low Confidence — Re-Prompt

```
STATE: LISTENING
ARBOR: "Your action?"
OPERATOR: [mumbles unintelligibly]
[error tone: STT quality low]
STATE: PROCESSING → AWAITING_CONFIRM (confidence: 0.22)
ARBOR: "I didn't quite catch that. What would you like to do?"
OPERATOR: "Attack the goblin shaman."
[click: acknowledgment]
STATE: PROCESSING → DECLARING (confidence: 0.88)
DM: "Kael attacks Goblin Shaman with longsword."
[1.5s silence — no objection]
STATE: EXECUTING
```

### Dialogue 4: Barge-In During Declaration

```
STATE: LISTENING
ARBOR: "Your action?"
OPERATOR: "Attack the goblin."
STATE: PROCESSING → DECLARING (confidence: 0.85)
DM: "Kael attacks Goblin Sco—"
OPERATOR: "No, the shaman!"
[tap: barge-in accepted]
STATE: AWAITING_CONFIRM
ARBOR: "Goblin Shaman instead?"
OPERATOR: "Yes."
STATE: EXECUTING
```

### Dialogue 5: Disambiguation — Numbered Menu

```
STATE: LISTENING
ARBOR: "Your action?"
OPERATOR: "Cast a spell on the goblin."
STATE: PROCESSING → AWAITING_CONFIRM (confidence: 0.55, ambiguous: spell + target)
ARBOR: "Which spell?
  Option 1: Magic Missile.
  Option 2: Shield — wait, that's self-only.
  Actually: Option 1: Magic Missile. Option 2: Burning Hands."
OPERATOR: "One."
ARBOR: "Magic Missile at which goblin?
  Option 1: Goblin Scout, 10 feet.
  Option 2: Goblin Shaman, 25 feet."
OPERATOR: "Two."
STATE: DECLARING
DM: "Kael casts Magic Missile at Goblin Shaman."
[1.5s silence]
STATE: EXECUTING
```

### Dialogue 6: Destructive Action Override

```
STATE: LISTENING
ARBOR: "Your action?"
OPERATOR: "Fireball the group."
STATE: PROCESSING → DECLARING (confidence: 0.90)
DM: "Kael casts Fireball centered on the goblin group."
[system detects: ally "Theron" is within blast radius]
STATE: AWAITING_CONFIRM (destructive override)
ARBOR: "Theron is in the blast radius. Proceed anyway?"
OPERATOR: "...yeah, he can take it."
ARBOR: "Confirmed — friendly fire."
STATE: EXECUTING
```

### Dialogue 7: Table Talk Correctly Ignored

```
STATE: COMMAND (operator's turn, LISTENING)
ARBOR: "Your action?"
OPERATOR: [to another player] "Hey Sarah, can you pass the pretzels?"
[table-talk filter: second-person address, no game verb → ignored]
STATE: LISTENING (no change)
OPERATOR: [to another player] "I wonder if I should use my last spell slot..."
[meta-game filter: no imperative verb → ignored]
STATE: LISTENING (no change)
OPERATOR: "Okay — Magic Missile at the shaman."
[click: acknowledgment]
STATE: PROCESSING → DECLARING (confidence: 0.91)
DM: "Kael casts Magic Missile at Goblin Shaman."
```

### Dialogue 8: Timeout and Recovery

```
STATE: LISTENING
ARBOR: "Your action?"
[8 seconds of silence]
[bell: timeout warning at 6s]
STATE: TIMEOUT_PROMPT
ARBOR: "Still thinking, or should I repeat that?"
[8 more seconds of silence]
ARBOR: "No worries. Your action whenever you're ready."
STATE: LISTENING
[operator eventually speaks]
OPERATOR: "Move to the door and take cover."
STATE: PROCESSING → DECLARING (confidence: 0.82)
DM: "Kael moves to the eastern door and takes cover."
```

### Dialogue 9: Retry Limit Exhausted

```
STATE: LISTENING
ARBOR: "Your action?"
OPERATOR: "Do the thing with the... you know..."
STATE: PROCESSING (confidence: 0.15)
ARBOR: "I didn't quite catch that. What would you like to do?"
OPERATOR: "The sword thing, on him."
STATE: PROCESSING (confidence: 0.35)
ARBOR: "Could you say that differently?"
OPERATOR: "Ugh... hit... that one."
STATE: PROCESSING (confidence: 0.28 — retry limit reached)
ARBOR: "Here's what you can do:
  Option 1: Attack — melee or ranged.
  Option 2: Cast a spell.
  Option 3: Move — up to 30 feet."
OPERATOR: "One. Attack the goblin scout."
STATE: PROCESSING → DECLARING (confidence: 0.93)
DM: "Kael attacks Goblin Scout with longsword."
```

### Dialogue 10: Barge-In Rejected During Execution

```
STATE: EXECUTING (Box resolving Fireball)
OPERATOR: "Wait, cancel that!"
[double-tap: commit locked]
[operator's speech is buffered, not parsed]
STATE: NARRATING
DM: "Fireball strikes Goblin Scout and Goblin Shaman. Devastating blast."
DM: "Flames consume the corridor. Both goblins are caught in the inferno."
ARBOR: "Goblin Scout is DEFEATED."
ARBOR: "Goblin Shaman is DEFEATED."
[chime: mode exit]
[after narration completes, buffered speech is discarded — action was atomic]
```

### Dialogue 11: Multi-Part Utterance

```
STATE: LISTENING
ARBOR: "Your action?"
OPERATOR: "Move to the door..."
[700ms silence — tentative finalize]
OPERATOR: "...and attack the goblin."
[conjunction "and" within 2s — appended to transcript]
STATE: PROCESSING
ARBOR: "I heard two actions. Let's do the move first."
DM: "Kael moves to the eastern door."
STATE: EXECUTING (move)
STATE: NARRATING (move result)
ARBOR: "Now the attack. Goblin Scout is at 5 feet. Longsword?"
OPERATOR: "Yes."
STATE: EXECUTING (attack)
```

### Dialogue 12: Wake Phrase Out of Turn

```
STATE: AMBIENT (NPC turn resolving)
OPERATOR: "Hey DM."
[chime: mode enter]
STATE: COMMAND / LISTENING
ARBOR: "Yes?"
OPERATOR: "Can I use my Shield reaction?"
STATE: PROCESSING → DECLARING (confidence: 0.87)
DM: "Kael casts Shield as a reaction."
[1.5s silence]
STATE: EXECUTING
```

---

## 11. Integration Points

### 11.1 Compatibility with Existing Components

| Component | Integration | Notes |
|---|---|---|
| `VoiceIntentParser` (WO-024) | Confidence scores drive §4.1 routing | No changes required |
| `ClarificationEngine` (WO-024) | Generates prompts for §5 disambiguation | No changes required |
| `STMContext` (WO-024) | Cleared on retry limit per §3.3 | Caller manages clear |
| AudioFirst CLI Contract | §6 narration follows output grammar rules | No changes required |
| TTS adapters (Chatterbox/Kokoro) | Must support streaming + barge-in halt | Requires: `stop()` method, streaming chunk API |
| Arbor voice profile | Speaks confirmations, prompts, alerts | Per salience hierarchy S1/S2 |
| DM persona | Speaks declarations, results, narration | Per salience hierarchy S3/S4 |

### 11.2 New Components Required

| Component | Purpose | Scope |
|---|---|---|
| **TurnStateMachine** | Manages §2 state transitions, enforces invariants | New class in `aidm/immersion/` |
| **BargeInDetector** | VAD-based interruption detection per §3.1 | Wraps existing VAD; adds state-aware gating |
| **ModeController** | Manages COMMAND/AMBIENT modes per §6 | New class; owns wake-phrase detection |
| **AudioCuePlayer** | Plays non-speech cues per §8 | Simple PCM sample playback; no TTS routing |

### 11.3 Config Surface

```yaml
voice_ux:
  auto_confirm_window_ms: 1500        # §4.2 — range: 1000-3000
  awaiting_confirm_timeout_ms: 8000    # §3.2
  idle_command_timeout_ms: 30000       # §6.3
  vad_silence_threshold_ms: 700        # §7.2 — range: 500-1500
  multi_utterance_window_ms: 2000      # §7.3
  barge_in_sustain_ms: 200             # §3.1
  barge_in_narrating_boost_db: 6       # §3.1
  max_retries_low_confidence: 2        # §3.3
  max_retries_disambiguation: 3        # §3.3
  max_retries_denial: 3                # §3.3
  audio_cues_enabled: true             # §8.2
  audio_cue_volume_db: -12             # §8.2 — relative to TTS speech
  wake_phrase: "hey dm"                # §6.3
  streaming_tts: true                  # §9
```

---

## 12. Stop Conditions Verified

- **No engine mechanics changes:** This spec defines interaction patterns only. Box resolution, dice rolling, state mutation are untouched.
- **No GUI dependency:** All patterns are voice-first + minimal CLI feedback. No graphical rendering, no map interaction, no mouse input assumed.
- **No authority boundary rewrite:** Box remains sole authority for mechanical resolution. The turn-taking state machine gates input to the Box but never overrides Box decisions.
- **No TTS backend modification:** Spec requires `stop()` and streaming APIs but does not specify TTS internals. Existing adapter interfaces are sufficient.

---

*This research document fulfills WO-VOICE-RESEARCH-04 acceptance criteria 1-6.*