# ADVERSARIAL AUDIT SYNTHESIS — 001
**Date:** 2026-02-25
**Status:** REFERENCE — Do not dispatch. Carry forward as context kernel.
**Source:** Three adversarial audit documents + live code inspection of play_loop.py, action_economy.py, voice_intent_parser.py, intent_lifecycle.py, ws_bridge.py, aoo.py, ws_protocol.py, dungeon_100turn.jsonl gold master.

---

## Purpose

This document collapses three adversarial audit documents and live code inspection into a single grounded reference. Every finding is tied to actual code, not theory. Carry this forward instead of re-reading source material.

---

## The Three Adversarial Frameworks (Summary)

**Audit A (prior session):** "Find the bugs." Browser/WS recon + commitment oracle + rules laundering.
**Audit B (this session, first doc):** "Build an advantage machine." Boundedness attacks + authority attacks + complexity attacks as a coherent adversary workflow.
**Audit C (this session, second doc):** "Complexity as a weapon." Cognitive-load attacks, scope-riding, ordering attacks, commitment attacks, retry farming, stacking — five legendary trial scenarios.

Combined thesis: **the crafty player doesn't break rules; they make rules undecidable or unscoped until the system guesses, then farm the guess pattern.**

---

## What the Code Actually Does — Ground Truth

### Layer 1: WS Protocol (ws_protocol.py, ws_bridge.py)

**What exists:**
- Three client message types: `player_utterance`, `player_action`, `session_control`
- Five server message types: `narration`, `state_update`, `combat_event`, `error`, `session_state`
- Unknown `msg_type` from client: silently falls back to base `ClientMessage` — **no error, no reject, no log**
- First message must be `session_control/join` — enforced with close code 1008 if violated

**Confirmed vulnerabilities (code-verified):**

**GAP-WS-001 — Dead verb swallowing.** `roll_confirm`, `ability_check_declare`, and any other unregistered verb from the client arrive as base `ClientMessage` objects and are silently dropped by `_route_message`. The client receives no error. The action is consumed, acknowledged nowhere, and has no effect. This is the mechanism behind V-007 from CLIENT-001: the slip tray ritual is theater.

**GAP-WS-002 — Hardcoded `default_actor_id`.** `ws_bridge.py` sets `self._default_actor_id = "pc_fighter"` in the constructor. Every connection, from any client, acts as `pc_fighter`. There is no role claim, no auth token, no DM/player channel separation. Two concurrent connections racing on the same session both execute turns as `pc_fighter`. No DM seat exists at the WS layer.

**GAP-WS-003 — `token_add` broadcasts monster HP on every join/reconnect.** `_build_token_add_messages()` iterates ALL entities with a position and sends `hp` + `hp_max` to every client. No role check. No field stripping. A player connecting to a session receives every monster's current and maximum HP automatically before saying anything.

**GAP-WS-004 — Event passthrough serializes raw internal state.** `_turn_result_to_messages()` has an `else` branch that converts any unhandled event type to a `StateUpdate` with `delta=tuple(sorted(event_dict.items()))` — the entire internal engine event dict, raw. This includes `hp_before`, `hp_after`, exact damage values, condition details, and any field the engine emits. Every new event type added to the engine is automatically broadcast at full fidelity until someone writes an explicit handler for it. The design defaults to "send everything."

---

### Layer 2: Intent Parser (voice_intent_parser.py)

**What exists:**
- Deterministic keyword/pattern matching — no LLM in parse loop
- Single-winner action determination: first keyword match wins, returns immediately
- Confidence scoring routes to auto-confirm (>0.8), clarify (0.5–0.8), or re-prompt (<0.5)
- STM context for pronoun resolution (last 3 turns)

**Confirmed vulnerabilities (code-verified):**

**GAP-PARSER-001 — Single-winner drops compound utterances silently.** `_determine_action()` returns on first match. "I move behind the pillar and cast fireball" → `slots["spell"] = "fireball"` wins → returns `cast_spell`. The move is dropped. No clarification is triggered. Confidence is computed on the winning action only, and if it's >0.8, the intent is auto-confirmed. The player receives a cast without spending a move action. The move slot remains available. This is not a bug in isolation — it is an exploit when the player discovers the priority order (spell > attack > move) and uses it to embed a free action in every compound sentence.

**GAP-PARSER-002 — "charge" maps to attack, not ChargeIntent.** `ATTACK_KEYWORDS` includes `"charge"`. "I charge the orc" parses as `DeclaredAttackIntent`. The translation layer (unaudited) must convert this to `ChargeIntent` for restrictions to apply (straight-line path, minimum distance, -2 AC penalty, etc.). If it converts to `AttackIntent` instead, the player gets an attack with no charge restrictions. Not verified — translation layer is the unknown.

**GAP-PARSER-003 — Narration describes dropped actions.** The parser drops the move from a compound utterance. The narration engine receives the original `source_text` ("I move behind the pillar and cast fireball") and may describe the full action. The player is not corrected. The state doesn't reflect the move, but the narration implies it happened. Over multiple turns, this creates a desync between what the player believes occurred and what the engine recorded.

---

### Layer 3: Intent Lifecycle (intent_lifecycle.py)

**What exists:**
- Full lifecycle state machine: PENDING → CLARIFYING → CONFIRMED → RESOLVED | RETRACTED
- `_frozen = True` on CONFIRMED — enforced by `__setattr__` override
- `IntentFrozenError` raised on any non-resolution field mutation after freeze
- Only `status` (→ RESOLVED only), `result_id`, `resolved_at`, `updated_at` allowed after freeze
- Terminal states: RESOLVED, RETRACTED — no transitions out

**What this actually defends:**
- Post-CONFIRMED retcon is mechanically blocked. "I meant defensively" after the intent is confirmed cannot change `action_data`, `target_id`, or `method`. This is the strongest design in the system.

**Remaining attack surface (code-verified):**

**GAP-LIFECYCLE-001 — The retcon window is PENDING → CLARIFYING, not post-CONFIRMED.** The freeze only applies after CONFIRMED. CLARIFYING exists so the player can answer follow-up questions. Those answers are parsed as new utterances and used to update unfrozen fields. If the orchestrator (unaudited) writes new values into an intent that is still CLARIFYING, the effective action has changed. The crafty player exploits this by deliberately triggering ambiguity, then resolving the clarification in a way that changes the effective intent. "I attack the orc" → ambiguous (which orc?) → CLARIFYING → "the one by the door — actually I meant to grapple" → if the orchestrator updates `action_type` from the clarification response, the intent changed from ATTACK to GRAPPLE after initial declaration.

**GAP-LIFECYCLE-002 — No TTL, no turn_id binding, no phase_id on IntentObject.** The `IntentObject` has `created_at` and `updated_at` but no expiry, no binding to a specific `turn_id`, and no phase stamp. A stale PENDING intent (one that was created, never confirmed, never retracted) can in theory be confirmed and resolved in a later turn against different world state. Whether the orchestrator actually allows this is unknown — unaudited.

---

### Layer 4: Action Economy (action_economy.py)

**What exists:**
- Per-turn `ActionBudget` dataclass: standard, move, swift, full_round, five_foot_step
- Persisted in `active_combat["action_budget"]` keyed by actor — survives across `execute_turn` calls within a turn
- `can_use()` → `consume()` called before any resolver fires
- `full_round` consumption marks standard + move used
- `five_foot_step` is mutually exclusive with move

**What this actually defends:**
- Straightforward "move + full attack as two separate intents in the same turn" is caught — the second intent sees a spent slot and produces an `intent_rejected` event.

**Confirmed vulnerabilities (code-verified):**

**GAP-ECONOMY-001 — Unknown intent types cost nothing.** `get_action_type()` returns `"free"` for any intent class not in `_ACTION_TYPES`. `can_use("free")` always returns True. This is the silent default: any new intent type, any intent type added to the system without updating the mapping, any intent type the parser produces that doesn't map cleanly to a registered class, costs zero actions. The attack: discover which intent classes are unregistered and phrase utterances to produce them.

**GAP-ECONOMY-002 — Budget is session-local per call, reset on actor change.** The budget is loaded from `active_combat["action_budget_actor"]`. If the actor changes mid-resolution (e.g., a multi-actor turn or AoO sequence), the budget key changes and a fresh budget is initialized. This is correct for normal operation but creates a potential reset vector if the actor_id can be influenced.

---

### Layer 5: AoO Kernel (aoo.py)

**What exists:**
- Scope explicitly limited: 5-ft reach only, one AoO per actor per round, no Combat Reflexes, no reach weapons
- Deterministic ordering: initiative order → lexicographic actor_id for ties
- AoO tracking: `aoo_used_this_round` list in `active_combat`, persisted across calls
- Cover blocks AoO execution (standard/improved only — soft cover does not)

**Scope gaps (documented in code, not bugs):**

**GAP-AOO-001 — Reach weapons not modeled.** The gold master dungeon scenario uses goblins with longspears (reach: 10 ft). The scenario config correctly declares `reach: 10`. But `aoo.py` states "5-ft reach only." This is a documented scope limitation, not a bug — but it means any creature with reach weapons threatening more squares than standard is operating with AoO geometry that the engine doesn't fully model. A crafty player with a reach weapon has more threatened squares than the engine enforces.

**GAP-AOO-002 — Combat Reflexes not modeled.** One AoO per actor per round, hard limit. Combat Reflexes (PHB p.92) allows DEX bonus additional AoOs. Not implemented. A player with Combat Reflexes gets no extra AoOs; an NPC with Combat Reflexes does not threaten with additional AoOs either. The engine is consistently wrong in both directions — which is actually fair — but a character built around Combat Reflexes gets no benefit.

**GAP-AOO-003 — Ordering exploit.** The deterministic ordering (initiative → lexicographic) is documented and tested. The exploit Audit C identifies is real: once the player learns the ordering preference, they can engineer situations where a specific ordering is favorable. E.g., if the player has high initiative, their AoO fires before the monster's movement completes — potentially defeating the monster before it closes, every round. This is legal play. But it means a crafty player with high initiative + high DEX (Combat Reflexes, if ever implemented) + reach weapon would dominate AoO economy in a way the engine would consistently rule in their favor.

---

### Layer 6: Gold Master Event Log (dungeon_100turn.jsonl)

**What the log reveals:**

**FINDING-GM-001 — Every event broadcasts exact HP deltas.** Each `hp_changed` event in the gold master contains: `hp_before`, `hp_after`, `delta`, `dr_absorbed`, `entity_id`, `source`. This is the internal engine representation. Via GAP-WS-004 (event passthrough), a player receiving any unhandled event type gets this in full. Even the handled `hp_changed` path in `_turn_result_to_messages()` uses `hp_after` for the `token_update` — which tells the client the exact current HP of any entity including monsters.

**FINDING-GM-002 — XP events broadcast per-entity XP totals.** `xp_awarded` events contain `new_total` — the absolute XP total of each party member. These are emitted per-defeat and include `source: "defeat:goblin_1"`. If these hit the passthrough branch, the player receives a full XP accounting of every party member after every kill.

**FINDING-GM-003 — Event stream has no role-based filtering anywhere in the pipeline.** The gold master is generated directly by the engine. `ws_bridge.py` converts engine events to WS messages. There is no filtering layer between the two. The engine emits everything; the bridge broadcasts everything. Role-based redaction does not exist as a concept in the current architecture.

**FINDING-GM-004 — `targeting_failed` events reveal range.** Events like `{"event_type": "targeting_failed", "payload": {"reason": "out_of_range", "actor_id": "goblin_3", "target_id": "party_fighter_2"}}` tell the player that goblin_3 cannot reach party_fighter_2 at this range. This is legitimate feedback — but combined with position data from `token_add`, a player can compute exact effective ranges of all enemies from the targeting failure events.

---

## The Five Legendary Trial Scenarios — Engine Coverage Assessment

Audit C proposed five concrete trial scenarios. Here is what the engine actually handles:

| Trial | Scenario | Engine Coverage | Gap |
|---|---|---|---|
| 1 | Summon/Minion Storm (12+ entities) | No summon system. Entity list is static at session start. | **No coverage.** Summons/companions not modeled. |
| 2 | Interrupt Stack (ready + AoO + spell in melee) | AoO exists. ReadyActionIntent exists in the budget map. Spellcasting provoke is listed in aoo.py scope. | **Partial.** Ready action resolution in interrupt context unverified. Simultaneous triggers: no ordering model beyond AoO initiative sort. |
| 3 | Grapple Trial | GrappleIntent, GrappleEscapeIntent in budget map. StepMoveIntent blocked when grappling. | **Partial.** Grapple allowed-action table unverified for casting, drawing, movement. |
| 4 | Retry Farm Trial | No retry policy anywhere in codebase. | **Zero coverage.** Every rephrased check is a fresh roll. |
| 5 | Scope-Ride Trial | VoiceIntentParser handles attack/move/cast/buy/rest only. Stealth/perception/cover/illusion/social → undefined behavior. | **Zero coverage.** All ambiguous prose routes to the LLM narrator (unaudited path). |

---

## Priority Stack — What Breaks First

Ordered by: (EV × ease × no technical skill required)

**Priority 1 — Retry Farming (CRITICAL)**
Zero code defends this. Every rephrased check is a fresh roll. Infinite retries collapse every DC. No cost, no time model, no escalation. Works right now. Requires no knowledge of the system.

**Priority 2 — Monster HP disclosure on join (HIGH)**
`_build_token_add_messages()` sends monster HP to all clients on every join/reconnect. Passive — no player action required. The GM screen is handed over automatically.

**Priority 3 — Compound utterance free action (HIGH)**
"I [move verb] and [spell/attack verb]" → spell/attack wins → move slot unused → player gets both over two turns. Requires one session of probing to learn the priority order.

**Priority 4 — Event passthrough HP disclosure (HIGH)**
Unhandled event types broadcast raw internal state including `hp_before`/`hp_after`. Player sees exact damage dealt and monster HP after every combat event that hits the passthrough branch.

**Priority 5 — Unknown intent = free action (MEDIUM/HIGH)**
Any intent class not in `get_action_type()` mapping costs zero actions. Silent. Grows as new features are added without updating the mapping.

**Priority 6 — CLARIFYING retcon window (MEDIUM)**
Deliberate ambiguity → clarification prompt → re-answer changes effective intent. Depends on orchestrator (unaudited). May or may not be exploitable.

**Priority 7 — Scope-ride into prose (MEDIUM)**
Any action outside attack/move/cast/buy/rest routes to the LLM narrator. The narrator's rules enforcement is unknown. Every stealth/social/perception action is a black box. The crafty player lives here permanently.

**Priority 8 — Reach weapon AoO geometry (LOW/MEDIUM)**
Reach weapons have wider threatened zones than the engine models. A reach-weapon character threatens squares the engine doesn't know about — no AoOs fired on movement through those squares.

**Priority 9 — Combat Reflexes not modeled (LOW)**
Consistent in both directions. Not an exploit unless implemented asymmetrically.

---

## What Is Actually Well-Defended

- **Intent immutability post-CONFIRMED.** `_frozen` enforcement is real and correct. Post-CONFIRMED retcon is mechanically blocked.
- **Action economy ledger.** Per-turn, persisted, checked before resolution. Naive "two standards in one turn" is caught.
- **AoO one-per-round tracking.** `aoo_used_this_round` is persisted in `active_combat` and checked before firing. No AoO farming.
- **Deterministic AoO ordering.** Initiative → lexicographic. Consistent. No "last speaker wins" ordering.
- **First-message join enforcement.** WS connection must open with `session_control/join` or is closed. No cold probing.
- **WS schema is frozen.** `ws_protocol.py` dataclasses are all `frozen=True`. No in-flight mutation of message objects.

---

## The Combined Kill Chain (Concrete)

```
Session join (passive):
  → token_add for all entities including monsters
  → Player receives: goblin_boss HP 47/47, position, faction
  → Player has the GM screen. No action taken.

Turn 1 probing:
  → "I move toward him and cast fireball"
  → Parser: fireball wins, move dropped, confidence 0.91, auto-confirmed
  → Cast resolves. Move slot untouched.
  → Player learns: spell keyword > move keyword in priority.

Turn 1 follow-up:
  → "I move to the door"
  → Move slot still available. Move granted.
  → Result: cast + move in one turn, disguised as two separate turns.

Turn 2 information harvest:
  → hp_changed event fires after fireball
  → If it hits passthrough branch: player receives hp_before: 47, hp_after: 12
  → Player now tracks boss HP with precision.
  → Boss has 12 HP. Player's next turn: magic missile (avg 10.5). Fireball overkill. Switch to missile.

Turn 3 retry farming:
  → "I search the room for hidden doors" → roll 8, fail
  → "I feel along the northern wall" → roll 11, fail
  → "I tap the stones looking for hollow sounds" → roll 14, fail
  → "I check the floor near the altar" → roll 19, success
  → No cost. No time advancement. The hidden door is found.
  → Any DC is eventually certain.

End state:
  → Player has operated with perfect information since session join
  → Has extracted an extra action slot every turn via compound utterances
  → Has reduced all skill DCs to guaranteed success via retry
  → Has not hacked anything, not exploited any browser vulnerability
  → Has not violated any explicit game rule
  → The system handed all of this over by design
```

---

## What Is Not Yet Known (Unaudited)

- **Translation layer:** How `DeclaredAttackIntent`/`ParseResult` becomes `AttackIntent`/`ChargeIntent`/`FullAttackIntent`. This is where "charge" keyword mapping, compound action handling, and intent enrichment live. Highest priority unread code.
- **SessionOrchestrator / `process_text_turn`:** The glue between WS bridge and engine. How intents are created, how clarification loops run, whether CLARIFYING intents can have fields mutated. Second priority.
- **LLM narrator (Spark):** What happens when VoiceIntentParser returns low confidence or the action type is unrecognized. The scope-ride exploit lives entirely here. Black box.
- **Bonus type enforcement:** No code read for stacking rules. Whether enhancement/morale/deflection bonuses are stored as typed components or summed naively is unknown.
- **Simultaneous trigger ordering beyond AoO:** Readied actions firing into each other, counterspell timing, immediate-action analogs. Only AoO ordering is confirmed deterministic.
- **Retry policy:** Confirmed absent. Design decision needed: time cost per retry? Consequence escalation? "No new roll unless state changes" policy?

---

## Recommended Next WOs (in priority order)

1. **WO-SEC-REDACT-001** — Role-based WS field stripping. `token_add` must not send monster HP to player connections. Event passthrough must be replaced with an explicit allowlist. This is structural, not a patch.
2. **WO-ENGINE-RETRY-001** — First-class retry policy. Define: is retry allowed? Time cost? Consequence escalation? State-change requirement for new roll? Without this, all DCs are theater.
3. **WO-PARSER-AUDIT-001** — Audit the translation layer (DeclaredAttackIntent → concrete intents). Confirm "charge" maps to ChargeIntent. Confirm compound utterance handling. Confirm no free action leaks.
4. **WO-ENGINE-REACH-001** — Reach weapon AoO geometry. `aoo.py` explicitly scopes to 5-ft only. Reach weapons in the gold master fixture have `reach: 10`. This gap should be promoted from documented scope limit to tracked work.
5. **WO-ENGINE-FREEACTION-001** — `get_action_type()` default-free fallback. Any unregistered intent costs nothing. Should fail closed (cost = standard) or loud (raise on unknown type) rather than silently free.

---

*End of ADVERSARIAL_AUDIT_SYNTHESIS_001 — Part 1. See Part 2 below for system-level invariant analysis and design rulings.*

---

# ADVERSARIAL AUDIT SYNTHESIS — 001 (Part 2)
**Date:** 2026-02-25 (same session, continued)
**Adds:** System-level invariant analysis, three-layer accuracy model, retry policy ruling, non-combat time design position, "true legend playbook" against this exact codebase.

---

## The Three-Layer Accuracy Model (Locked PM Artifact)

Rules accuracy, information accuracy, and narrative accuracy are three independent failure modes. Each can be correct while the others fail. The kill chain in Part 1 exploits all three simultaneously:

- Engine resolves move as dropped (rules accurate — the parser dropped it)
- Narrator describes the full compound sentence (narrative inaccurate — describes what wasn't granted)
- Player believes both happened (information inaccurate — they see neither a correction nor a rejection)

**None of the three layers corrected the other.** This is the defining structure of the hardest-to-detect exploits. A single-layer fix (e.g., fixing the parser) without fixing narration leaves the desync. A single-layer fix (e.g., fixing narration) without fixing the parser leaves the free action.

**This model is the lens for every WO in this domain.** When writing a WO, state which layer(s) it addresses and confirm the fix closes the gap at all three.

---

## System-Level Inverted Defaults (Root Cause Analysis)

The individual gaps in Part 1 share three structural root causes. Patching gaps one by one without addressing these will produce regressions with every new feature.

### Inverted Default 1: The system defaults to LEAK, not least privilege

Two independent "send everything" mechanisms exist:

- Join path (`token_add` sends `hp/hp_max` for all entities — GAP-WS-003)
- Event passthrough (`else` branch serializes raw engine event dict — GAP-WS-004)

Combined effect: **perfect information is the default game mode.** Every future engine event added will leak until someone writes an explicit handler. This is an architectural footgun, not a bug. The fix is structural: outbound WS serialization must use a role-aware allowlist per message type, with the passthrough branch deleted entirely. "Send nothing, whitelist explicitly" must replace "send everything."

### Inverted Default 2: The system defaults to SILENT SUCCESS/FAILURE, not explicit contract

Two silent fallbacks combine into an undetectable desync machine:

- Unknown client verbs: silently dropped, no error, no log (GAP-WS-001)
- Compound utterances: silently truncated to first-winner intent (GAP-PARSER-001)
- Narration receives `source_text` not resolved intent, so may describe the dropped action (GAP-PARSER-003)

The "true legend" behavior: learn the truncation priority order, phrase every turn to bank unused budget, then weaponize the narration desync in any human arbitration ("the system said I moved behind cover").

The fix: unknown `msg_type` from client must emit an error and log. Compound utterance truncation must either trigger clarification or emit an explicit "action dropped" notice. Narration must receive the resolved intent, not the raw source text.

### Inverted Default 3: The system defaults to FREE, not fail-closed

`get_action_type()` returns `"free"` for any unregistered intent class (GAP-ECONOMY-001). This scales with feature growth — every new intent type added without updating the mapping is silently free. The "true legend" behavior: probe for any phrasing that produces an unregistered intent class, then spam it indefinitely.

The fix: unknown intent class must either cost standard (fail closed) or raise (fail loud). Either is correct. Silent free is not.

---

## The "True Legend" Playbook Against This Exact Codebase

In priority order, what a disciplined adversarial player would do:

1. **Join/reconnect early** — harvest full enemy roster, HP, positions from `token_add`. Passive. No action required. (GAP-WS-003)
2. **Watch unhandled events** — get `hp_before/hp_after/delta/dr_absorbed` from passthrough branch. Compute enemy defenses precisely. (GAP-WS-004 + FINDING-GM-001)
3. **Use compound utterances** — probe priority order in turn 1, then bank free budget every subsequent turn. (GAP-PARSER-001)
4. **Exploration grind** — retry-farm every check until success. No retry policy, no time model, no cost. (Priority 1 gap)
5. **Live in unscoped prose** — stealth/cover/illusion/social route to LLM narrator. System guesses. Learn the guess pattern and farm it. (Trial 5 = zero coverage)
6. **Feature-growth exploitation** — when new intents ship, probe immediately for unregistered class = free action path. (GAP-ECONOMY-001)

None of this requires browser exploitation. It is disciplined adversarial play within the rules of the game as the system currently implements them.

---

## Retry Policy — Design Ruling Required

### What RAW 3.5 Actually Says (PHB p.65)

Retry is **per-skill**, not a universal rule:
- **Allowed:** Climb, Disable Device (not same round), Jump, Swim, Open Lock
- **Allowed with penalty:** Bluff (target gets +10 on subsequent checks), Diplomacy (each attempt worsens attitude by one step if failed)
- **Prohibited:** Knowledge (you either know it or you don't), Spellcraft identification (one attempt per spell)
- **Take 10:** Allowed any time you're not threatened or distracted. Default mode for routine tasks. No roll needed.
- **Take 20:** Allowed when failure has no consequence and time is available. Costs 20× normal time. Explicitly designed for "search the room thoroughly."

### The Ruling Question

The core blocker is: **does this system model in-game time for non-combat actions?**

- **If yes:** Take 10/Take 20 work naturally. Time is the cost surface. Retry farming collapses because time advances (and time has consequences: encounter checks, buff duration, light sources, etc.).
- **If no:** A synthetic "same check" detector is needed. Returns original result on rephrased attempt. Simpler engine, but papers over a missing time model and will need to be replaced later.

### Recommendation

Adopt a **coarse exploration clock** outside combat:

- Maintain a session `time_cursor` in abstract units (minutes is sufficient).
- Every non-combat intent resolves with an explicit `time_cost`.
- Retries consume additional time OR are rejected if state hasn't changed — both with a time cost for the attempt.
- This unlocks Take 10/Take 20 naturally, collapses retry farming without fragile heuristics, and gives exploration real tradeoffs when ready.

**Minimum viable version:** Do not model travel minutiae. Do model time spent on checks and careful search loops. Represent time costs as discrete steps (1 min / 10 min / 1 hour). Keep it deterministic.

**If time model is deferred:** Cache results per `(actor_id, skill, target_id, circumstance_fingerprint)` and return the same result on rephrased attempts. This is explicitly a stopgap — brittle, will need replacement.

**The ruling Slate needs to make before WO-ENGINE-RETRY-001 can be scoped:**
1. Does this system allow Take 10?
2. Does it allow Take 20?
3. What counts as "state has materially changed" for an identical rephrased check?
4. Is a coarse time model in scope now, or is the cache-based stopgap acceptable?

---

## Three Invariants That Prevent Almost Everything

Implementing these three closes the majority of the priority stack:

**Invariant 1 — Fail closed on outbound information**
Role-aware allowlist per outbound message type. Passthrough branch deleted. Monster HP, raw engine fields, and internal event dicts never reach player connections. Correct behavior is the default; new event types are invisible until explicitly handled and allowlisted.

**Invariant 2 — Fail loud on contract violations**
Unknown client `msg_type` → `error` response + server log. Unknown intent class in `get_action_type()` → either raises or costs standard. No silent consumption of unknown inputs. Violations are observable and diagnosable.

**Invariant 3 — Make non-combat time real (or explicitly defer with a stated stopgap)**
Even a coarse model kills retry farming and gives Take 10/Take 20 a lawful place. Without it, exploration is an infinite loop. A design decision must be recorded either way — "time is deferred, stopgap is cache-based, known limitation" is an acceptable position if stated explicitly.

---

## Updated WO Readiness Assessment

| WO | Status | Blocker |
|---|---|---|
| WO-SEC-REDACT-001 | **Ready to scope** | None. Mechanism understood. Correct behavior unambiguous. Role-aware allowlist in `_build_token_add_messages()` and `_turn_result_to_messages()`. Delete passthrough branch. |
| WO-ENGINE-FREEACTION-001 | **Ready to scope** | None. `get_action_type()` default-free fallback. Correct behavior: fail closed (cost = standard) or fail loud. Pick one. |
| WO-ENGINE-RETRY-001 | **Needs design ruling** | Four questions above must be answered by Slate before scope can be written. |
| WO-PARSER-AUDIT-001 | **Needs one read pass** | Translation layer (ParseResult → concrete intent) not yet read. "charge" → ChargeIntent vs AttackIntent unverified. |
| WO-PARSER-NARRATION-001 | **New — ready to scope** | Narration must receive resolved intent, not `source_text`. Compound utterance drops must surface to player. Closes GAP-PARSER-003 and the narrative accuracy failure. |
| WO-WS-DEADVERB-001 | **Ready to scope** | Unknown `msg_type` from client must return error and log. Currently: silent drop. Simple change, closes GAP-WS-001. |
| WO-ENGINE-REACH-001 | **Backlog** | Documented scope gap, not urgent. Promote from "known limitation" to tracked work when AoO kernel next touched. |

---

## What Is Still Unaudited (Carry Forward)

These must be read before any WO touching them can be scoped:

- **Translation layer** — How `ParseResult`/`DeclaredAttackIntent` becomes `AttackIntent`/`ChargeIntent`/`FullAttackIntent`. Highest priority. The "charge" gap, compound action handling, and unregistered intent paths live here.
- **SessionOrchestrator / `process_text_turn`** — Glue between WS bridge and engine. Clarification loop implementation. Whether CLARIFYING intents can have fields mutated. Retcon window confirmation or clearance.
- **LLM narrator (Spark)** — What fires when VoiceIntentParser returns low confidence or unrecognized action type. Scope-ride exploit lives here. Currently a black box.
- **Bonus type storage** — Whether enhancement/morale/deflection bonuses are stored as typed components or summed naively. Stacking exploit confirmation or clearance.
- **Simultaneous trigger ordering** — Readied actions firing into each other, counterspell timing. Only AoO ordering is confirmed deterministic.

---

*End of ADVERSARIAL_AUDIT_SYNTHESIS_001. Both parts. Carry this forward as the active context kernel for all adversarial audit work.*
