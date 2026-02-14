# Voice Control Plane Contract v0

**Work Order:** WO-VOICE-RESEARCH-01
**Status:** RESEARCH COMPLETE
**Date:** 2026-02-13
**Author:** Sonnet A (Agent)
**Authority:** PM-approved research deliverable

---

## 1. Purpose

This document defines the Voice Control Plane Contract: a deterministic, voice-first command surface that converts lossy speech into crisp intents via explicit grammar, routing prefixes, and two-phase commit.

Speech is a lossy transport layer. This contract ensures that every player utterance is routed, parsed, declared, confirmed, and resolved through a deterministic pipeline with no silent assumptions and no unbounded NLU.

**Binding references:**
- VOICE_INTENT_AND_CLARIFICATION_PROTOCOL.md (VICP-001, adopted)
- RQ_AUDIOFIRST_CLI_CONTRACT_V1.md (output grammar)
- `aidm/schemas/intents.py` (intent schemas)
- `aidm/schemas/intent_lifecycle.py` (lifecycle + freeze boundary)
- `aidm/immersion/voice_intent_parser.py` (keyword parser)
- `aidm/immersion/clarification_loop.py` (clarification engine)
- `aidm/core/interaction.py` (InteractionEngine)

**Scope constraint:** This contract specifies the INPUT surface — how spoken words become structured intents. It does not modify engine mechanics, Box resolution, or output formatting. Output formatting is governed by RQ_AUDIOFIRST_CLI_CONTRACT_V1.md.

---

## 2. Command Grammar v0

### 2.1 Intent Classes (Exhaustive)

Every spoken utterance that reaches the parse layer maps to exactly one of these intent classes. There is no catch-all "freeform" class.

| Intent Class | ActionType | Engine Route | Example Spoken Form |
|---|---|---|---|
| **Attack** | ATTACK | Box: attack_resolver | "I attack the goblin with my longsword" |
| **Cast Spell** | CAST_SPELL | Box: spell_resolver | "Cast fireball on the group by the door" |
| **Move** | MOVE | Box: movement_resolver | "I move behind the pillar" |
| **Use Ability** | USE_ABILITY | Box: ability_resolver | "I use Power Attack on the ogre" |
| **End Turn** | END_TURN | Box: turn_manager | "Done" / "End turn" / "Pass" |
| **Rest** | REST | Box: rest_resolver | "We rest for the night" |
| **Buy** | BUY | Box: shop_resolver | "Buy two healing potions" |
| **Status Query** | — (no Box call) | Lens: FrozenWorldStateView | "How hurt is the goblin?" / "What's my AC?" |

### 2.2 Spoken Forms — Attack

| Spoken Form | Parsed Slots | Notes |
|---|---|---|
| "Attack the goblin" | target=goblin, weapon=default | Default weapon = last used or primary equipped |
| "Hit the orc with my axe" | target=orc, weapon=axe | Explicit weapon |
| "Shoot the skeleton" | target=skeleton, weapon=ranged_default | "shoot"/"fire" implies ranged |
| "Attack him again" | target=STM.last_target, weapon=STM.last_weapon | Pronoun + "again" resolves from STM |
| "Full attack on the troll" | target=troll, weapon=default, full_attack=true | "full attack" triggers iterative sequence |
| "Charge the wizard" | target=wizard, charge=true | "charge" implies move+attack at -2/+2 |

### 2.3 Spoken Forms — Cast Spell

| Spoken Form | Parsed Slots | Notes |
|---|---|---|
| "Cast magic missile at the goblin" | spell=magic_missile, target=goblin | creature-targeted |
| "Fireball the group by the door" | spell=fireball, target_mode=point | Area spell; location needed |
| "Shield" | spell=shield, target_mode=self | Self-buff; no target needed |
| "Cast haste on everyone" | spell=haste, target=party | "everyone" = all party members |
| "Cure light wounds on myself" | spell=cure_light_wounds, target=self | Explicit self-target |
| "Use scorching ray on him" | spell=scorching_ray, target=STM.last_target | "use" is a cast synonym; pronoun from STM |

### 2.4 Spoken Forms — Move

| Spoken Form | Parsed Slots | Notes |
|---|---|---|
| "Move to the door" | destination=landmark("door") | Landmark resolution |
| "Run behind the pillar" | destination=relative("behind", "pillar") | Spatial + landmark |
| "Go there" | destination=STM.last_location | Pronoun from STM |
| "Approach the goblin" | destination=adjacent(target=goblin) | "approach" = move to adjacent square |
| "Retreat" | destination=away(threats) | Move away from nearest enemy |
| "Five foot step north" | destination=5ft_step("north") | No AoO movement |

### 2.5 Spoken Forms — End Turn / Status / Rest / Buy

| Spoken Form | Intent Class | Notes |
|---|---|---|
| "Done" | END_TURN | Minimal form |
| "End turn" | END_TURN | Explicit form |
| "Pass" | END_TURN | Synonym |
| "That's it" | END_TURN | Natural form |
| "How hurt is the goblin?" | STATUS_QUERY | No Box call; reads FrozenWorldStateView |
| "What's my HP?" | STATUS_QUERY | Player self-status |
| "Who's up next?" | STATUS_QUERY | Initiative query |
| "Rest for the night" | REST | Default overnight rest |
| "Full day of bed rest" | REST (full_day) | Extended rest |
| "Buy two healing potions" | BUY | Quantity + item |

---

## 3. Routing Prefixes

### 3.1 Mode Separation

Not all speech is a game command. Players talk to each other, ask rules questions, and make notes. Routing prefixes separate these channels. The system defaults to **Command Mode** (fail-closed: if no prefix is detected and the speaker is the active player during their turn, the utterance is treated as a command attempt).

| Prefix | Mode | Route | Engine Authority | Example |
|---|---|---|---|---|
| *(none, active player's turn)* | **Command** | VoiceIntentParser → IntentBridge → Box | Full mechanical resolution | "I attack the goblin" |
| "Table talk" / "Out of character" | **Table Talk** | Suppressed (not parsed) | None; pass-through to chat log | "Table talk — hey, should we rest first?" |
| "Rules question" / "How does..." | **Rules Question** | RulesRegistry lookup → DM persona response | No Box call; informational only | "Rules question — how does grapple work?" |
| "DM note" / "Note to self" | **DM Note** | Logged to session journal | None; metadata only | "DM note — remember the prisoner" |
| "From Spark" | **Spark Narration** | Narrative injection (Spark layer) | None; atmospheric only | *(system-originated, not player-spoken)* |

### 3.2 Fail-Closed Default

When no routing prefix is detected:
- **Active player, during their turn:** Utterance enters Command mode. If parsing fails, the system asks for clarification (not silent discard).
- **Non-active player, during combat:** Utterance is treated as Table Talk (logged, not parsed as command).
- **Outside combat:** Utterance enters Command mode (exploration commands: move, rest, interact, buy).
- **System silence (no input for timeout period):** No action. See Section 5.3 for timeout behavior.

### 3.3 Prefix Detection Rules

Prefix detection is keyword-based (deterministic, not NLU):
- Prefix must appear at the start of the utterance (first 1-4 words).
- Prefix matching is case-insensitive.
- If a prefix is detected, the remainder of the utterance is routed to the corresponding mode.
- If no prefix is detected, the utterance routes to the default mode per Section 3.2.

| Prefix Keywords | Mode |
|---|---|
| "table talk", "out of character", "OOC" | Table Talk |
| "rules question", "how does", "what happens if", "can I" (outside turn) | Rules Question |
| "DM note", "note to self", "remember that" | DM Note |

### 3.4 Mode Indicators

The system announces the current mode only on transitions:
- Entering combat: "Roll initiative." (implicit Command mode)
- Player says "table talk": DM acknowledges briefly, e.g., "Sure, go ahead."
- Player says "rules question": DM responds in informational register (no mechanical resolution).
- Returning to Command mode after prefix utterance: automatic, no announcement needed.

---

## 4. Two-Phase Commit Semantics

### 4.1 Overview

Every mechanical action follows a two-phase commit: **Declare** then **Confirm**. No action reaches Box resolution without explicit or implicit confirmation. This prevents the engine from acting on misheard or misinterpreted speech.

```
PHASE 1: DECLARE
  Player speaks → STT transcript → VoiceIntentParser → ParseResult
  If high confidence: → soft confirm prompt
  If needs clarification: → ClarificationEngine → DM asks question

PHASE 2: CONFIRM
  DM echoes declared intent → Player confirms or corrects
  On confirm: IntentObject freezes (CONFIRMED) → Box resolves
  On cancel: IntentObject → RETRACTED
  On timeout: IntentObject → RETRACTED (graceful, no penalty)
```

### 4.2 Phase 1 — Declare

The player speaks. The STT layer produces a transcript. The VoiceIntentParser extracts an intent with a confidence score.

**Confidence routing:**

| Confidence | Threshold | Route |
|---|---|---|
| High | > 0.8 | Soft confirm: DM echoes intent, proceeds unless player objects |
| Medium | 0.5 – 0.8 | Clarification: DM asks targeted question about ambiguous slot |
| Low | < 0.5 | Re-prompt: "I didn't quite catch that. What are you trying to do?" |

**Soft confirm** is not a modal dialog. It is natural DM table talk:
> "Alright, you attack the goblin by the door with your longsword."

The player may object verbally at this point. If the player says nothing (within confirm window), the intent proceeds.

### 4.3 Phase 2 — Confirm

Confirmation vocabulary is deterministic. The system recognizes these exact tokens:

| Token | Effect | Notes |
|---|---|---|
| "Yes" / "Yeah" / "Yep" / "Do it" / "Go" / "Confirmed" | CONFIRM | Intent freezes, Box resolves |
| "No" / "Nope" / "Wait" / "Stop" / "Cancel" / "Never mind" | CANCEL | Intent → RETRACTED |
| "Repeat" / "Say that again" / "What?" | REPEAT | DM re-echoes the declared intent |
| *(silence for confirm_timeout)* | TIMEOUT → CANCEL | Graceful retraction, no penalty |
| *(correction utterance)* | RE-DECLARE | New parse replaces current intent; restarts Phase 1 |

### 4.4 Confirm Window Timing

| Parameter | Default | Configurable | Notes |
|---|---|---|---|
| `soft_confirm_window` | 3 seconds | Yes | Time after DM echo before auto-confirm (high confidence only) |
| `explicit_confirm_timeout` | 15 seconds | Yes | Time to wait for explicit yes/no after clarification |
| `clarification_timeout` | 20 seconds | Yes | Time to wait for player response to clarification question |

If `soft_confirm_window` elapses with no player objection and confidence was high, the intent auto-confirms. This avoids requiring "yes" after every action.

If `explicit_confirm_timeout` elapses after a clarification, the intent is RETRACTED:
> "I didn't catch that — let me know when you're ready."

### 4.5 Lifecycle State Mapping

The two-phase commit maps directly to the existing IntentObject lifecycle:

| Phase | IntentStatus | Frozen? | Modifiable? |
|---|---|---|---|
| Player speaks | PENDING | No | Yes — parser fills slots |
| Clarification in progress | CLARIFYING | No | Yes — player provides missing info |
| Player confirms | CONFIRMED | **Yes** | **No** — only resolution fields |
| Box resolves | RESOLVED | Yes | No |
| Player cancels or timeout | RETRACTED | N/A | Terminal state |

Once CONFIRMED, the intent is frozen per BL-014. The voice layer, LLM, and Spark may not alter it. Only the engine writes resolution fields.

### 4.6 Clarification Rounds

Clarification is limited to **3 rounds** (configurable via `ClarificationLoop.max_rounds`). If the player cannot resolve ambiguity within 3 rounds, the intent is RETRACTED:
> "No worries — we'll skip that for now. What would you like to do instead?"

Clarification never loops infinitely. This prevents the system from badgering the player.

---

## 5. Ambiguity Handling Contract

### 5.1 Ambiguity Categories

| Category | Trigger | Resolution Strategy |
|---|---|---|
| **Ambiguous target** | Multiple entities match spoken name | Menu (if 2-3 options) or "Which one?" prompt |
| **Ambiguous location** | Area spell with no point specified | "Where do you want to center it?" + optional map click |
| **Ambiguous weapon** | Multiple weapons equipped, none specified | Use primary equipped weapon (no prompt if default exists) |
| **Ambiguous spell** | Fuzzy match returns 2+ spells | "Did you mean X or Y?" |
| **Ambiguous action** | No recognizable action verb | "I'm not sure what you're trying to do. Could you rephrase?" |
| **Unknown entity** | Spoken name matches nothing in world state | "I don't see anyone by that name. Who did you mean?" |

### 5.2 Entity Resolution Rules

When the player names a target, the IntentBridge resolves it against the current world state:

| Match Count | Behavior |
|---|---|
| **Exactly 1** | Auto-fill target_id. No clarification needed. |
| **2-3 matches** | DM presents options conversationally: "Which goblin — the one by the brazier or the one by the door?" |
| **4+ matches** | DM narrows first: "There are several goblins. The closest ones are the Scout and the Shaman. Which one?" |
| **0 matches (exact)** | Fuzzy match (edit distance). If 1 fuzzy hit, soft-confirm: "Did you mean [name]?" If 0 fuzzy, re-prompt. |

Disambiguation prompts are always phrased as DM table talk, never system error messages:
- Correct: "Which goblin — the one by the brazier or the one by the door?"
- Incorrect: "ERROR: Ambiguous target. Select from: [Goblin Scout, Goblin Shaman]"

### 5.3 Spell Name Resolution

Spell resolution uses the spell registry in `VoiceIntentParser.KNOWN_SPELLS` with multi-word substring matching. Additional rules:

| Scenario | Behavior |
|---|---|
| Exact match | Auto-fill spell_name. |
| Single fuzzy match (edit distance <= 2) | Soft-confirm: "Fireball, right?" |
| 2-3 fuzzy matches | "Did you mean Magic Missile or Mirror Image?" |
| No match | "I don't recognize that spell. What are you casting?" |

### 5.4 Weapon Resolution

| Scenario | Behavior |
|---|---|
| Weapon explicitly named | Use named weapon. |
| No weapon named, one weapon equipped | Use equipped weapon (no prompt). |
| No weapon named, multiple weapons equipped | Use primary weapon (melee default, ranged if "shoot"/"fire"). |
| Named weapon not equipped | "You don't have a [weapon] ready. You have [list]. Which one?" |

### 5.5 No Silent Assumptions

Per VICP-001 Section 6: the system must never guess targeting, infer positioning, or assume rule interpretations. If ambiguity exists, the system asks. Silence is not consent.

The one exception is **default weapon selection** (Section 5.4): if the player has exactly one weapon or a clear primary, no prompt is required. This follows real tabletop behavior where the DM does not ask "with what weapon?" when the fighter holding a longsword says "I attack."

---

## 6. Canonical Examples

### Example 1: Clean Attack (High Confidence)

```
UTTERANCE:    "I attack the goblin with my longsword"
TRANSCRIPT:   "i attack the goblin with my longsword" (confidence: 0.95)
PARSE:        action=ATTACK, target_ref="goblin", weapon="longsword"
CONFIDENCE:   0.95 (high)
DECLARED:     DeclaredAttackIntent(target_ref="goblin", weapon="longsword")
CONFIRM:      DM: "Alright, you swing your longsword at the goblin."
              (3s soft confirm window — player says nothing)
RESULT:       Intent CONFIRMED → Box resolves → "Longsword hits Goblin Scout. Moderate wound."
```

### Example 2: Ambiguous Target (Two Goblins)

```
UTTERANCE:    "I attack the goblin"
TRANSCRIPT:   "i attack the goblin" (confidence: 0.90)
PARSE:        action=ATTACK, target_ref="goblin", weapon=default
MATCH:        IntentBridge finds 2 matches: [Goblin Scout, Goblin Shaman]
CLARIFY:      DM: "Which goblin — the Scout near the brazier or the Shaman by the door?"
RESPONSE:     "The scout"
RE-PARSE:     target_ref="Goblin Scout"
CONFIRM:      DM: "Alright, attacking the Goblin Scout."
RESULT:       Intent CONFIRMED → Box resolves
```

### Example 3: Area Spell Needing Point

```
UTTERANCE:    "Cast fireball on the group by the door"
TRANSCRIPT:   "cast fireball on the group by the door" (confidence: 0.88)
PARSE:        action=CAST_SPELL, spell="fireball", target_mode=point, spatial="by the door"
CLARIFY:      DM: "Where do you want to center the fireball?"
              (Map highlights: phantom 20-ft radius appears at cursor)
RESPONSE:     Player clicks grid point (4, 7)
CONFIRM:      DM: "Fireball centered here — it'll catch the three by the door."
              Player: "Do it."
RESULT:       Intent CONFIRMED → Box resolves → "Fireball strikes Goblin Shaman. Devastating blast."
```

### Example 4: Pronoun Resolution via STM

```
CONTEXT:      Last action was attacking Goblin Scout with longsword.
UTTERANCE:    "Attack him again"
TRANSCRIPT:   "attack him again" (confidence: 0.92)
PARSE:        action=ATTACK, target_ref=STM.last_target("Goblin Scout"),
              weapon=STM.last_weapon("longsword"), repeat=true
CONFIDENCE:   0.92 (high — pronoun resolved from STM)
CONFIRM:      DM: "Alright, another swing at the Goblin Scout."
RESULT:       Intent CONFIRMED → Box resolves
```

### Example 5: Spell with Fuzzy Match

```
UTTERANCE:    "Cast magic missle"
TRANSCRIPT:   "cast magic missle" (confidence: 0.85)
PARSE:        action=CAST_SPELL, spell_raw="magic missle"
FUZZY:        edit_distance("magic missle", "magic missile") = 1 → single match
CONFIRM:      DM: "Magic Missile, right? Who's the target?"
RESPONSE:     "The skeleton"
CONFIRM:      DM: "Magic Missile at the Skeleton. Three bolts streak out."
RESULT:       Intent CONFIRMED → Box resolves
```

### Example 6: Player Cancels During Confirm

```
UTTERANCE:    "I charge the dragon"
TRANSCRIPT:   "i charge the dragon" (confidence: 0.91)
PARSE:        action=ATTACK, target_ref="dragon", charge=true
CONFIRM:      DM: "Alright, you charge the dragon — that's a full-round action."
RESPONSE:     "Wait, no. Never mind."
RESULT:       Intent → RETRACTED. DM: "Alright, what would you like to do instead?"
```

### Example 7: Timeout Retraction

```
UTTERANCE:    "Cast... uh..."
TRANSCRIPT:   "cast uh" (confidence: 0.30)
PARSE:        action=CAST_SPELL, spell=None
CONFIDENCE:   0.30 (low)
PROMPT:       DM: "What spell are you casting?"
              (20 seconds pass, no response)
RESULT:       Intent → RETRACTED. DM: "I didn't catch that — let me know when you're ready."
```

### Example 8: Table Talk Routing

```
UTTERANCE:    "Table talk — hey, should we rest before going in?"
PREFIX:       "table talk" detected → route to Table Talk mode
RESULT:       Utterance logged to chat. No parse. No intent created. No Box call.
              DM does not respond mechanically.
```

### Example 9: Rules Question Routing

```
UTTERANCE:    "Rules question — how does flanking work?"
PREFIX:       "rules question" detected → route to Rules Question mode
RESULT:       RulesRegistry lookup: flanking. DM responds:
              "When you and an ally are on opposite sides of an enemy, you both get
              a +2 flanking bonus on melee attack rolls against that creature."
              No intent created. No Box call.
```

### Example 10: Status Query (No Box Call)

```
UTTERANCE:    "How hurt is the goblin?"
PARSE:        action=STATUS_QUERY, target_ref="goblin"
ROUTE:        Lens → FrozenWorldStateView (no Box call)
RESPONSE:     DM: "The Goblin Scout is looking rough — badly wounded."
              (Maps from HP percentage to severity band; no numbers leak through Lens)
```

### Example 11: Move with Spatial Reference

```
UTTERANCE:    "I move behind the pillar"
TRANSCRIPT:   "i move behind the pillar" (confidence: 0.89)
PARSE:        action=MOVE, destination=relative("behind", "pillar")
ROUTE:        IntentBridge resolves "pillar" to landmark → calculates position
CONFIRM:      DM: "Moving behind the stone pillar — here?"
              (Map shows movement path ghost)
RESPONSE:     "Yes"
RESULT:       Intent CONFIRMED → Box resolves movement → token moves on grid
```

### Example 12: End Turn (Minimal)

```
UTTERANCE:    "Done"
TRANSCRIPT:   "done" (confidence: 0.97)
PARSE:        action=END_TURN
CONFIDENCE:   0.97 (high — unambiguous keyword)
CONFIRM:      (No confirm prompt for END_TURN — auto-confirm)
RESULT:       Turn ends. Next entity's turn begins. Turn Banner spoken.
```

### Example 13: DM Note Routing

```
UTTERANCE:    "DM note — the prisoner mentioned a secret passage"
PREFIX:       "DM note" detected → route to DM Note mode
RESULT:       Note logged to session journal: "the prisoner mentioned a secret passage"
              No intent created. No Box call. No DM spoken response.
```

### Example 14: Multi-Step Correction

```
UTTERANCE:    "I attack the orc"
TRANSCRIPT:   "i attack the orc" (confidence: 0.93)
PARSE:        action=ATTACK, target_ref="orc"
CONFIRM:      DM: "Alright, you swing at the orc."
RESPONSE:     "No, wait — I meant the goblin, with my bow."
RE-PARSE:     action=ATTACK, target_ref="goblin", weapon="bow"
CONFIRM:      DM: "Got it — you shoot at the goblin with your bow."
RESPONSE:     "Yes"
RESULT:       Intent CONFIRMED → Box resolves ranged attack
```

---

## 7. Error Boundaries

### 7.1 Parse Failure

If the VoiceIntentParser cannot extract any intent class from the transcript:
- DM responds conversationally: "I didn't quite catch that. What are you trying to do?"
- No intent is created.
- No Box call is made.
- The player's turn continues (no penalty for misheard speech).

### 7.2 Engine Rejection

If Box rejects a confirmed intent (impossible action):
- The intent is still marked RESOLVED (engine processed it, result = rejection).
- DM explains in-world: "You can't reach that far this round" / "That's out of range for your weapon."
- The player may declare a new intent.
- No silent fallback to a different action.

### 7.3 STT Failure

If the STT adapter returns no transcript or an empty transcript:
- DM: "I didn't hear anything. What would you like to do?"
- No intent is created.
- No timeout penalty.

### 7.4 Cascading Failure

If multiple subsystems fail (STT + parser + clarification):
- The system falls back to text input: "[AIDM] Voice input unavailable. Please type your action."
- Text input follows the same parse → declare → confirm pipeline.
- No action is taken silently.

---

## 8. Vocabulary Reference

### 8.1 Action Verbs (Parser Keywords)

| Category | Keywords |
|---|---|
| Attack | attack, hit, strike, slash, stab, shoot, fire, swing, punch, kick, smite, charge |
| Move | move, go, walk, run, dash, rush, retreat, advance, step, approach, flee |
| Cast | cast, use, invoke, channel, unleash, summon |
| Buy | buy, purchase, acquire, shop |
| Rest | rest, sleep, camp, recover |
| End Turn | done, end turn, pass, that's it, finished, next |

### 8.2 Confirmation Tokens

| Category | Tokens |
|---|---|
| Affirm | yes, yeah, yep, do it, go, confirmed, correct, right, sure, go ahead |
| Cancel | no, nope, wait, stop, cancel, never mind, hold on, actually no |
| Repeat | repeat, say that again, what, come again, say again, one more time |

### 8.3 Routing Prefix Tokens

| Mode | Prefix Tokens |
|---|---|
| Table Talk | table talk, out of character, OOC |
| Rules Question | rules question, how does, what happens if |
| DM Note | DM note, note to self, remember that |

---

## 9. Implementation Boundary

This contract is a **spec**. Implementation requires future work orders to:

1. Add routing prefix detection to `VoiceIntentParser` (keyword scan of first 4 words).
2. Add STATUS_QUERY intent class to `aidm/schemas/intents.py`.
3. Add confirmation token recognition to the session orchestrator.
4. Add soft-confirm window timer to `InteractionEngine`.
5. Add explicit `full_attack` and `charge` flags to `DeclaredAttackIntent`.
6. Extend `KNOWN_SPELLS` registry to cover full D&D 3.5e SRD spell list.
7. Add DM Note logging to session journal.
8. Add Rules Question routing to RulesRegistry.

No engine mechanics are changed by this spec. No Box behavior is modified. This is input surface definition only.

---

## 10. Stop Conditions Verified

- **No engine mechanics changes:** This contract specifies input parsing and routing. Box resolution, dice rolling, and state mutation are untouched.
- **No unbounded NLU:** All parsing is keyword-based and deterministic. Routing prefixes are explicit tokens, not semantic classifiers.
- **No freeform language as mechanics:** Every utterance must resolve to a typed intent class or be routed to a non-mechanical mode. There is no "just say whatever and the AI figures it out" pathway.
- **All tests pass:** Verified via `python -m pytest tests/ -v --tb=short` (see acceptance criterion 7).

---

*This research document fulfills WO-VOICE-RESEARCH-01 acceptance criteria 1-6. Criterion 7 (tests pass) verified at time of delivery.*
