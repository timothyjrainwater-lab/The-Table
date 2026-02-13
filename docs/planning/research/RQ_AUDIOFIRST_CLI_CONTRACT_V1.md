# RQ: Audio-First CLI Contract v1 — Output Grammar, Salience Hierarchy, and Playtest Prompts

**Work Order:** WO-RQ-AUDIOFIRST-CLI-CONTRACT-01
**Status:** RESEARCH COMPLETE
**Date:** 2026-02-13
**Author:** Sonnet D (Agent)
**Authority:** PM-approved research deliverable

---

## 1. Purpose

This document defines the Audio-First CLI Contract v1: output grammar rules, salience hierarchy, and playtest prompts optimized for voice playback and golden-transcript stability. The contract ensures CLI output reads well when spoken aloud by TTS (Chatterbox/Kokoro) and remains deterministically stable across runs.

**Binding references:**
- SPARK_LENS_BOX_DOCTRINE.md (Axiom 3: Lens adapts stance, not authority)
- `aidm/runtime/display.py` (current CLI formatting)
- `aidm/immersion/tts_adapter.py` (TTS protocol)
- `aidm/immersion/kokoro_tts_adapter.py`, `chatterbox_tts_adapter.py` (TTS backends)
- `scripts/speak.py` (operator signal voice, Arbor profile)
- `play.py` (CLI combat loop)

**Scope constraint:** This contract is PRESENTATION ONLY. It does not modify engine mechanics, Box resolution, or game state. It specifies how resolved outcomes are formatted for the operator's ears and eyes.

---

## 2. CLI Output Grammar

### 2.1 Output Line Types (Exhaustive)

Every line of CLI output belongs to exactly one of these categories:

| Line Type | Tag | Voice Routing | Example |
|---|---|---|---|
| **Turn Banner** | `TURN` | Spoken (DM persona) | `Kael's Turn` |
| **Action Result** | `RESULT` | Spoken (DM persona) | `Longsword hits Goblin Scout. Moderate wound.` |
| **Critical Alert** | `ALERT` | Spoken (urgent, Arbor) | `Goblin Scout is DEFEATED.` |
| **Narration Block** | `NARRATION` | Spoken (DM persona) | *(2-4 sentence Spark output)* |
| **Operator Prompt** | `PROMPT` | Spoken (Arbor) | `Your action?` |
| **System Message** | `SYSTEM` | Not spoken (display only) | `[AIDM] Session loaded.` |
| **Mechanical Detail** | `DETAIL` | Not spoken (display only) | `[RESOLVE] Rolling attack: [17]+5 = 22 vs AC 16` |

### 2.2 Grammar Rules (Invariants)

**Rule G-01: Turn Boundary**
Every turn begins with exactly one Turn Banner line. No other content may precede it within the turn.

Format:
```
{entity_name}'s Turn
```

Invariants:
- Entity name is the display name (never entity_id)
- No punctuation after "Turn" (period breaks speech cadence)
- No dashes, equals signs, or box-drawing characters
- Blank line after the banner before any results

**Rule G-02: Action Result Lines**
Action results are single lines. One result per mechanical resolution.

Format:
```
{weapon_or_action} {outcome} {target}. {severity_phrase}.
```

Examples:
```
Longsword hits Goblin Scout. Moderate wound.
Longsword misses Goblin Scout. Glancing blow deflected.
Fireball strikes Goblin Shaman. Devastating blast.
```

Invariants:
- Two sentences maximum per result line
- First sentence: what happened (weapon/spell + hit/miss + target)
- Second sentence: severity or effect (maps from NarrativeBrief.severity)
- No mechanical numbers (damage, AC, bonus, roll)
- Always end with period
- Severity phrases (canonical):

| Severity | Canonical Phrase |
|---|---|
| minor | Scratch. / Glancing blow. / Barely felt. |
| moderate | Moderate wound. / Solid hit. / Painful strike. |
| severe | Severe wound. / Crushing blow. / Staggering hit. |
| devastating | Devastating blow. / Nearly lethal. / Bone-breaking force. |
| lethal | Fatal strike. / Killing blow. |
| miss | Misses cleanly. / Deflected. / Whiffs past. |

**Rule G-03: Critical Alerts**
Critical alerts are single-line banners for state changes that the operator must notice immediately.

Format:
```
{entity_name} is {STATUS}.
```

Triggered by:
- Entity defeated: `Goblin Scout is DEFEATED.`
- Entity condition applied: `Kael is PRONE.`
- Entity condition removed: `Kael is no longer STUNNED.`
- Entity at critical HP (below 25%): `Kael is BADLY WOUNDED.`

Invariants:
- Status word is UPPERCASE in display
- Spoken with emphasis (TTS persona adjusts pitch/speed)
- One alert per state change (no batching)
- Blank line before and after each alert

**Rule G-04: Narration Block**
Narration blocks are 1-3 sentence paragraphs from Spark (or template fallback). They follow the Action Result line(s) for the same turn.

Invariants:
- Minimum 1 sentence, maximum 3 sentences for combat narration
- For reflective/exploration blocks: up to 3 sentences
- No single line shorter than 8 words (avoids choppy TTS pacing)
- No line longer than 120 characters (avoids breathless TTS runs)
- Sentences flow as natural prose paragraphs (not bullet points)
- Blank line before and after the narration block

**Rule G-05: Operator Prompt**
After all results, alerts, and narration for a turn are displayed, the operator is prompted for input.

Format:
```
Your action?
```

Invariants:
- Always exactly `Your action?` (stable for golden transcript comparison)
- Spoken by Arbor voice (not DM persona)
- Blank line before the prompt

**Rule G-06: System Messages (Display Only)**
System messages use the `[AIDM]` tag prefix and are NOT spoken aloud by TTS. They are for operator visual reference only.

Format:
```
[AIDM] {message}
```

Invariants:
- Never spoken by TTS (voice pipeline skips `[AIDM]` prefixed lines)
- Used for: session load, bootstrap progress, configuration notices, errors
- Error format: `[AIDM] ERROR: {type}: {message}`

**Rule G-07: Mechanical Detail (Display Only, Verbose Mode)**
Mechanical details use the `[RESOLVE]` tag and are NOT spoken aloud. They show the operator the raw dice math.

Format:
```
[RESOLVE] {roll_description}: [{natural}]+{modifier} = {total} vs {target} -> {outcome}
```

Invariants:
- Never spoken by TTS
- Displayed only when verbose mode is enabled (spec-only concept; default: off for audio-first)
- Roll component ordering is always: `[natural]+modifier = total` (stable, never rearranged)
- Modifier sign is explicit: `+5`, `-2`, `+0`

---

## 3. Formatting Constraints for Voice

### 3.1 Anti-Patterns (MUST NOT)

| Anti-Pattern | Problem for TTS | Fix |
|---|---|---|
| Dashed separators (`---`, `===`) | TTS reads "dash dash dash" or pauses awkwardly | Use blank lines for visual separation |
| Three-word lines (`He attacks it.`) | Choppy, breathless TTS pacing | Minimum 8 words per sentence in narration blocks |
| Long unbroken paragraphs (>4 sentences) | TTS runs out of prosody; listener loses track | Cap at 3 sentences per paragraph |
| Parenthetical asides (`(see PHB p.145)`) | TTS reads parentheses literally or garbles | Remove; rule citations are forbidden in spoken output |
| Abbreviations (`atk`, `dmg`, `hp`, `AC`) | TTS may pronounce letter-by-letter | Spell out in spoken lines; abbreviations only in `[RESOLVE]` detail |
| ALL CAPS for emphasis (entire sentences) | TTS may shout or lose prosody | ALL CAPS only for single status words in ALERT lines |
| Numbered lists in narration | TTS reads "one period, two period" | Use prose sentences for narration; lists only in system output |
| Emoji or Unicode symbols | TTS may describe them ("star emoji") | Never use emoji in CLI output |

### 3.2 Positive Patterns (SHOULD)

| Pattern | Why it Works | Example |
|---|---|---|
| Short declarative sentences (8-15 words) | Clean TTS pacing, clear to operator | "Kael's longsword finds its mark against the goblin's shoulder." |
| Active voice | Sounds authoritative, DM-like | "The goblin stumbles back" not "The goblin is stumbled back by" |
| Concrete sensory language | Engages listening; less abstract | "Steel bites into leather armor" not "Damage is dealt" |
| Natural sentence flow between sentences | TTS prosody follows grammatical structure | "The blade connects. The goblin snarls in pain." |
| Pause-friendly punctuation (periods, commas) | TTS pauses appropriately | Commas for breath breaks in longer descriptions |

### 3.3 Voice Routing Rules

| Output contains | Routed to | Spoken |
|---|---|---|
| Turn Banner | DM persona (Chatterbox/Kokoro) | YES |
| Action Result | DM persona | YES |
| Critical Alert | Arbor (signal voice, urgent register) | YES |
| Narration Block | DM persona | YES |
| Operator Prompt | Arbor (calm register) | YES |
| `[AIDM]` prefix | None | NO |
| `[RESOLVE]` prefix | None | NO |

---

## 4. Salience Hierarchy

### 4.1 Salience Levels

Output is prioritized by salience. Higher-salience lines are always spoken; lower-salience lines may be display-only in audio-first mode.

| Level | Category | Display | Spoken | Interrupts |
|---|---|---|---|---|
| **S1 (Critical)** | ALERT: defeat, death, downed | Always | Always | YES - interrupts any in-progress TTS |
| **S2 (Actionable)** | Operator Prompt, Clarification Question | Always | Always | NO - waits for current TTS to finish |
| **S3 (Primary)** | Turn Banner, Action Result | Always | Always | NO |
| **S4 (Atmospheric)** | Narration Block | Always | Always (can be skipped in fast mode) | NO |
| **S5 (Reference)** | Mechanical Detail (`[RESOLVE]`) | Verbose mode only | Never | NO |
| **S6 (System)** | System Messages (`[AIDM]`) | Always | Never | NO |

### 4.2 Visibility Rule for Operator-Required Actions

When the operator must act (their turn, clarification needed, choice required), the output follows the **PLAYTEST READY** pattern:

```
Kael's Turn

Goblin Scout is BADLY WOUNDED.

Your action?
```

Structure:
1. **Single loud header** (Turn Banner) - who is acting
2. **One-line state alert** (if any critical state change requires attention) - what changed
3. **One-line next step** (Operator Prompt) - what to do now

No narration block is interposed between the alert and the prompt when a critical state change is pending. Narration from the *previous* turn's resolution has already been spoken. The operator's turn starts clean.

### 4.3 Initiative Display

Initiative is displayed once at combat start and is deterministically sorted.

Format:
```
Turn Order:
  1. Kael            18  (d20=14, DEX +4)
  2. Goblin Scout    12  (d20=11, DEX +1)
  3. Goblin Shaman    8  (d20=7, DEX +1)
```

Spoken version (Arbor, calm): "Turn order. Kael goes first, then Goblin Scout, then Goblin Shaman."

Invariants:
- Sorted by: total (descending) > DEX modifier (descending) > entity name (alphabetical)
- Tie-breaking is deterministic and documented
- Column-aligned for visual display
- Spoken version omits numbers and dice, gives only order and names
- Party members marked with `*` prefix in display (not spoken)

---

## 5. Golden-Transcript Stability Policy

### 5.1 Purpose

Golden transcripts are reference outputs that verify CLI formatting stability across code changes. Given identical game state, seed, and inputs, the CLI must produce byte-identical output.

### 5.2 Sorting Rules

All lists in CLI output follow deterministic sort orders:

| List | Primary Sort | Secondary Sort | Tertiary Sort |
|---|---|---|---|
| Initiative order | Total (descending) | DEX modifier (descending) | Entity name (alpha ascending) |
| Entity status list | Entity name (alpha ascending) | -- | -- |
| Target lists | Entity name (alpha ascending) | -- | -- |
| Condition lists | Condition name (alpha ascending) | -- | -- |
| Available actions | Action name (alpha ascending) | -- | -- |
| Visible gear | Gear name (alpha ascending) | -- | -- |

### 5.3 Naming Canonicalization

| Data | Canonical Form | Example |
|---|---|---|
| Entity display names | Title Case, as defined in campaign manifest | "Goblin Scout" (not "goblin scout", "GOBLIN SCOUT") |
| Weapon names | Title Case | "Longsword" (not "longsword", "LONGSWORD") |
| Spell names | Title Case | "Cure Light Wounds" |
| Condition names | UPPER CASE in alerts, lower case in narration | Alert: "PRONE", Narration: "prone" |
| Action types | Lower case with underscores internally, display as Title Case | Internal: "bull_rush", Display: "Bull Rush" |

### 5.4 Stable Ordering of Roll Components

Roll display always follows this exact ordering:

```
[{natural_roll}]+{modifier} = {total}
```

Invariants:
- Natural roll in square brackets: `[17]`
- Modifier with explicit sign: `+5`, `-2`, `+0`
- Equals sign with spaces: ` = `
- Total as plain number: `22`
- If multiple modifiers: show sum only, not breakdown (breakdown in verbose mode)
- vs comparison always follows: `vs AC 16 -> HIT` or `vs DC 15 -> FAIL`
- Arrow is ` -> ` (space-arrow-space), not `→` (Unicode arrow causes TTS issues)

### 5.5 Stable Timestamp Policy

- No timestamps in CLI output (timestamps are non-deterministic)
- Turn numbers are sequential integers starting from 1
- Round numbers are sequential integers starting from 1
- Event IDs are not displayed in standard output (only in `[RESOLVE]` verbose detail)

### 5.6 Template Narration Stability

Template narrations use `str.format_map()` with deterministic inputs. Given identical NarrativeBrief inputs, template output is byte-identical.

Spark narrations (LLM-generated) are NOT golden-stable by design (stochastic). Golden-transcript tests must either:
- Use template narration mode (disable Spark)
- Or compare only non-narration lines (skip `[NARRATIVE]`-tagged blocks)

---

## 6. Playtest Script Template

### 6.1 Purpose

This playtest script validates the audio-first CLI contract in under 2 minutes. An operator executes the steps manually and records pass/fail for each checkpoint.

### 6.2 Prerequisites

- AIDM running with a campaign loaded (any test campaign)
- Combat encounter active with at least 2 entities
- TTS backend available (Kokoro minimum; Chatterbox preferred)
- Volume at 50% (default Arbor profile)

### 6.3 Script

```
AUDIO-FIRST CLI PLAYTEST v1
============================
Date: ___________
Tester: ___________
Campaign: ___________
TTS Backend: [ ] Chatterbox  [ ] Kokoro  [ ] None

STEP 1: INITIATIVE DISPLAY
  Action: Start combat encounter (or observe initiative on new round).
  Observe: Initiative list displayed.
  Check:
    [ ] PASS / [ ] FAIL — Names are sorted by total (highest first)
    [ ] PASS / [ ] FAIL — Ties broken consistently (DEX > name)
    [ ] PASS / [ ] FAIL — Column alignment is clean (no ragged numbers)
    [ ] PASS / [ ] FAIL — TTS speaks "Turn order. [name] goes first, then [name]..."
    [ ] PASS / [ ] FAIL — No dashes or separator lines in output

STEP 2: TURN BANNER
  Action: Observe first entity's turn start.
  Check:
    [ ] PASS / [ ] FAIL — Banner reads "{Name}'s Turn" (no dashes, no prefix tag)
    [ ] PASS / [ ] FAIL — TTS speaks the banner aloud
    [ ] PASS / [ ] FAIL — Blank line follows before any result

STEP 3: ATTACK RESULT
  Action: Command an attack against a target.
  Observe: Result line and optional narration.
  Check:
    [ ] PASS / [ ] FAIL — Result line is 1-2 sentences
    [ ] PASS / [ ] FAIL — No damage numbers in spoken output
    [ ] PASS / [ ] FAIL — No AC values in spoken output
    [ ] PASS / [ ] FAIL — No dice notation in spoken output
    [ ] PASS / [ ] FAIL — Severity phrase matches expected severity level
    [ ] PASS / [ ] FAIL — TTS speaks result naturally (no choppy 3-word sentences)

STEP 4: NARRATION BLOCK
  Action: Listen to narration after the action result.
  Check:
    [ ] PASS / [ ] FAIL — Narration is 1-3 sentences
    [ ] PASS / [ ] FAIL — No sentence shorter than 8 words
    [ ] PASS / [ ] FAIL — TTS reads smoothly (natural pauses at periods/commas)
    [ ] PASS / [ ] FAIL — Narration does not contradict the result

STEP 5: CRITICAL ALERT
  Action: Continue combat until an entity is defeated or a condition is applied.
  (If needed, attack a low-HP target.)
  Check:
    [ ] PASS / [ ] FAIL — Alert reads "{Name} is {STATUS}."
    [ ] PASS / [ ] FAIL — Status word is UPPERCASE in display
    [ ] PASS / [ ] FAIL — TTS speaks the alert with emphasis
    [ ] PASS / [ ] FAIL — Blank line before and after the alert

STEP 6: OPERATOR PROMPT
  Action: Observe the prompt after all output for your turn.
  Check:
    [ ] PASS / [ ] FAIL — Prompt reads exactly "Your action?"
    [ ] PASS / [ ] FAIL — TTS speaks it in Arbor voice (calm, not DM persona)
    [ ] PASS / [ ] FAIL — No narration between alert and prompt (clean handoff)

STEP 7: MECHANICAL DETAIL (VERBOSE)
  Action: Enable verbose mode (if available) and repeat an attack.
  Check:
    [ ] PASS / [ ] FAIL — [RESOLVE] lines appear with roll breakdown
    [ ] PASS / [ ] FAIL — Roll format is [{natural}]+{mod} = {total}
    [ ] PASS / [ ] FAIL — [RESOLVE] lines are NOT spoken by TTS
    [ ] PASS / [ ] FAIL — Modifier has explicit sign (+/-)

STEP 8: DETERMINISM CHECK
  Action: Replay the exact same inputs with the same seed.
  Check:
    [ ] PASS / [ ] FAIL — Turn banners are identical
    [ ] PASS / [ ] FAIL — Action results are identical
    [ ] PASS / [ ] FAIL — Initiative order is identical
    [ ] PASS / [ ] FAIL — Alert lines are identical
    [ ] PASS / [ ] FAIL — [RESOLVE] detail lines are identical

RESULT SUMMARY:
  Total checks: 30
  Passed: ____
  Failed: ____
  Blocking failures (any STEP 1-6 fail): ____

NOTES:
_______________________________________________
_______________________________________________
```

---

## 7. Migration Path from Current CLI

### 7.1 Current State (as-built in display.py and play.py)

The current CLI uses:
- `"=" * 80` separator borders -> **Remove** (voice anti-pattern)
- `"--- {name}'s Turn ---"` banners -> **Simplify** to `{name}'s Turn`
- `[RESOLVE]` prefix for roll details -> **Keep** (display-only, not spoken)
- `[AIDM]` prefix for system messages -> **Keep** (display-only, not spoken)
- `*** {name} is DEFEATED! ***` -> **Simplify** to `{name} is DEFEATED.`
- Entity lines with `| DEFEATED` suffix -> **Keep** for status display

### 7.2 Changes Required

| Current | Audio-First Contract | Breaking? |
|---|---|---|
| `"=" * 80` borders | Blank lines | YES (golden transcripts) |
| `--- Name's Turn ---` | `Name's Turn` | YES (golden transcripts) |
| `*** DEFEATED! ***` | `Name is DEFEATED.` | YES (golden transcripts) |
| Roll format varies | `[nat]+mod = total` fixed | Possibly (need audit) |
| No voice routing tags | Lines tagged for TTS routing | NO (additive) |
| No salience levels | Lines prioritized by salience | NO (additive) |

Golden transcript baselines must be regenerated after migration. This is a one-time cost.

### 7.3 Implementation Boundary

This contract is a **spec**. Implementation requires a future work order to:
1. Update `display.py` formatting functions
2. Update `play.py` combat output
3. Add TTS routing logic (tag-based line filtering)
4. Regenerate golden transcript baselines
5. Update test assertions

No engine mechanics are changed. No Box behavior is modified. This is purely presentation-layer work.

---

## 8. Stop Conditions Verified

- **No engine mechanics changes:** This contract specifies output formatting only. Box resolution, dice rolling, state mutation are untouched.
- **No GUI or UX redesign:** Output remains CLI text. TTS is additive audio overlay on existing text output.
- **No scope expansion:** Spec covers CLI output grammar, voice optimization, and playtest validation only.

---

*This research document fulfills WO-RQ-AUDIOFIRST-CLI-CONTRACT-01 acceptance criteria 1-5.*