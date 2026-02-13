# RQ-UNKNOWN-HANDLING-POLICY-01: Unknown Handling Policy for LLM Runtime

**Author:** Agent B (Sonnet) per WO-RQ-UNKNOWN-TAXONOMY-01
**Date:** 2026-02-13
**Status:** DRAFT (requires PM approval before binding)
**Authority:** PM (Thunder) + Agent D (Stop Authority)
**Scope:** All AIDM runtime layers (Spark, Lens, Box) when encountering missing, ambiguous, or unresolvable data

---

## 0. Governing Principle

> **The system must never silently invent.**

When the system encounters something it does not know, it must identify the class of unknown, execute the prescribed response from this policy, and log the encounter. No layer may fabricate mechanical values, assert false facts, or silently paper over missing data. This policy is the runtime counterpart of the Spark/Lens/Box Doctrine and the M1 Implementation Guardrails.

**Binding references:**
- `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` (authority split)
- `docs/design/M1_IMPLEMENTATION_GUARDRAILS.md` (write barriers, kill switches)
- `docs/design/M1_LLM_SAFEGUARD_ARCHITECTURE.md` (safeguard inventory)
- `docs/planning/M1_LLM_SAFEGUARDS_REQUIREMENTS.md` (REQ-LLM-SG-001 through SG-006)
- `aidm/core/fact_acquisition.py` (JIT acquisition protocol, FORBIDDEN_DEFAULTS)

---

## 1. Taxonomy of Unknowns

Every unknown encountered at runtime belongs to exactly one of the following classes. Classification is deterministic: match the first class whose definition fits.

### UK-SCENE: Missing Scene Facts

**Definition:** The system needs a spatial or environmental fact about the current scene that is not present in the frozen WorldState view or Lens index.

**Examples:**
- Distance between two entities not computed (no grid position for one or both)
- Line-of-sight / line-of-effect not determinable (obstacle data missing)
- Cover/concealment status unknown (terrain metadata absent)
- Lighting level at a cell not recorded
- Elevation data missing for a cell or entity

**Upstream cause:** Scene was authored without full geometric data; entity entered play via narration without Box placement; world compile did not produce the needed cell metadata.

---

### UK-TARGET: Missing or Ambiguous Target Identity

**Definition:** A player or NPC action references a target that cannot be resolved to a single canonical entity in the current WorldState.

**Examples:**
- "I attack the goblin" when multiple goblins are on the grid
- "Cast heal on the fighter" when two PCs have the Fighter class
- Pronoun reference ("hit him") with multiple valid antecedents
- Target name does not match any entity in the active encounter
- Target is valid but not currently on the grid (out of scope)

**Upstream cause:** Ambiguous player utterance; insufficient disambiguation in intent bridge; entity naming collision.

---

### UK-RULES: Missing Rules Data

**Definition:** Box needs a rule, value, or interaction that has not been ingested into the deterministic engine. The rule exists in D&D 3.5e RAW but is not yet implemented.

**Examples:**
- Spell effect not in the spell database (spell not yet ingested)
- Feat interaction not coded (feat grants conditional bonus not yet modeled)
- Special attack type not implemented (e.g., trip, disarm, sunder beyond current CP scope)
- Condition interaction not modeled (e.g., grapple as relational condition, per SKR-005)
- Saving throw sub-type modifier not implemented
- Material component or focus requirement not tracked

**Upstream cause:** Rules ingestion is incremental (CP packets); not all PHB/DMG content is in Box yet.

---

### UK-STATE: Missing Entity State

**Definition:** An entity exists in the WorldState but is missing a required mechanical attribute that Box needs to resolve an action.

**Examples:**
- Creature has no `armor_class` value (FORBIDDEN_DEFAULT per `fact_acquisition.py`)
- Creature has no `hit_points` value (FORBIDDEN_DEFAULT)
- Entity has no `size` category (FORBIDDEN_DEFAULT)
- Entity has no `position` on the grid (FORBIDDEN_DEFAULT)
- Condition duration counter missing (condition applied without tracking expiry)
- Ability score not recorded (STR/DEX/CON/INT/WIS/CHA value absent)

**Upstream cause:** Entity was introduced via narration without full mechanical stat block; fact acquisition from Spark failed or timed out; world compile produced incomplete entity.

---

### UK-ASSET: Missing Non-Mechanical Asset

**Definition:** A presentation-layer resource (voice profile, image, music, sound effect) is unavailable.

**Examples:**
- NPC voice persona not generated (Spark voice characterization not cached)
- Character portrait / token image missing
- Ambient music track not available for current scene mood
- Sound effect for spell/action not found
- Reference audio file for TTS not accessible

**Upstream cause:** Asset generation deferred (M2/M3); TTS backend unavailable; cache miss; hardware-gated feature (GPU required but absent).

---

### UK-POLICY: RAW Silence or Ambiguity Requiring House Policy

**Definition:** The D&D 3.5e rules text is genuinely silent, ambiguous, or self-contradictory on the matter in question, and no existing House Policy CP addresses it.

**Examples:**
- RAW does not specify whether a specific action provokes an AoO in an edge case
- Two rules texts appear to contradict each other (e.g., feat description vs. general combat rule)
- RAW is silent on interaction between two subsystems not yet adjudicated
- Errata conflicts with original printing and no project-local decision exists
- Player attempts action not covered by any existing rule or CP

**Upstream cause:** D&D 3.5e RAW has known gaps; the project's CP packets have not yet addressed this specific case.

---

## 2. Response Policy Per Unknown Class

Each unknown class maps to exactly one required response. No runtime component may choose a different response for that class.

### UK-SCENE: Defer to Box + Request Operator If Needed

| Step | Action |
|------|--------|
| 1 | Box checks Lens spatial index for the missing fact. |
| 2 | If Lens has the fact at any source tier: use it, log provenance. |
| 3 | If Lens does not have the fact: trigger JIT Fact Acquisition (Spark callback). |
| 4 | If Spark returns valid data: validate, store in Lens at SPARK tier, proceed. |
| 5 | If Spark times out or returns invalid data: **HALT the pending action**. |
| 6 | Present operator with: `[UNCERTAIN] Cannot determine {fact} for this action. Please specify or place entity on grid.` |
| 7 | Log: `UK-SCENE | entity_id | missing_attr | resolution={acquired|operator|halted}` |

**Stoplight:** YELLOW (action paused, not cancelled; resumes after fact provided).

---

### UK-TARGET: Ask Player (Disambiguation Loop)

| Step | Action |
|------|--------|
| 1 | Intent bridge identifies ambiguous target reference. |
| 2 | Set intent status to `CLARIFYING` (blocking). |
| 3 | Present player with neutral disambiguation prompt listing valid targets. |
| 4 | Player selects target. Intent bridge resolves to canonical entity_id. |
| 5 | If player says "cancel": discard intent, return to action prompt. |
| 6 | **Maximum disambiguation turns: 2.** If unresolved after 2 rounds: discard intent, log, notify operator. |
| 7 | Log: `UK-TARGET | raw_utterance | candidates=[...] | resolution={resolved|cancelled|timeout}` |

**Stoplight:** YELLOW (action paused until player clarifies).

**Disambiguation phrasing rules:** See Section 3 (Forbidden/Allowed Phrasing).

---

### UK-RULES: Halt + Escalate "Rules Not Ingested"

| Step | Action |
|------|--------|
| 1 | Box detects it cannot resolve the action because the rule/spell/feat/interaction is not implemented. |
| 2 | **HALT the action immediately.** Do not approximate, do not use "closest equivalent." |
| 3 | Present operator with: `[BOX] Rule not available: {rule_description}. This action cannot be resolved until the rule is ingested. Skipping action.` |
| 4 | If in combat: skip the entity's turn (entity takes no action this round). Operator may override with manual DM ruling. |
| 5 | Log: `UK-RULES | rule_id | action_attempted | resolution={skipped|operator_override}` |
| 6 | If operator provides a manual override ruling: record it as `[DM_OVERRIDE]` provenance, not `[BOX]`. Create event log entry. |

**Stoplight:** RED (action cannot proceed without rule ingestion or DM override).

---

### UK-STATE: JIT Acquisition, Then Halt If Still Missing

| Step | Action |
|------|--------|
| 1 | Box requests missing attribute from Lens. |
| 2 | If attribute is in ALLOWED_DEFAULTS (`material`, `hardness`, `movement_cost`, `elevation`): apply default, log `[DEFAULT]` provenance. |
| 3 | If attribute is in FORBIDDEN_DEFAULTS (`size`, `position`, `hit_points`, `armor_class`): trigger JIT Fact Acquisition from Spark. |
| 4 | If Spark returns valid data: validate (type checks, range checks per `fact_acquisition.py`), store at SPARK tier, proceed. |
| 5 | If Spark fails/times out/returns invalid: **HALT the action.** |
| 6 | Present operator with: `[UNCERTAIN] Entity "{entity_name}" is missing required attribute: {attr}. Cannot resolve action. Please provide value or remove entity from encounter.` |
| 7 | Log: `UK-STATE | entity_id | missing_attr | resolution={acquired|defaulted|operator|halted}` |

**Stoplight:** RED if FORBIDDEN_DEFAULT missing after acquisition attempt; GREEN if ALLOWED_DEFAULT applied.

---

### UK-ASSET: Silent Fallback (Narration-Only, No New Facts)

| Step | Action |
|------|--------|
| 1 | Presentation layer detects missing asset. |
| 2 | Apply fallback chain per asset type: |
|   | - Voice: use generic archetype voice (pitch=1.0, pace=1.0) |
|   | - Image: use placeholder token / no image |
|   | - Music: use curated library fallback (mood-based generic track) |
|   | - Sound effect: omit silently |
| 3 | **Do NOT halt gameplay.** Assets are atmospheric only (LRP-001). |
| 4 | Do NOT generate new facts or mechanical data as a side effect of asset fallback. |
| 5 | Log: `UK-ASSET | asset_kind | semantic_key | resolution={fallback|omitted}` |

**Stoplight:** GREEN (gameplay unaffected; presentation degraded gracefully).

---

### UK-POLICY: Escalate to "House Policy Needed"

| Step | Action |
|------|--------|
| 1 | Box (or operator via intent bridge) encounters a question that RAW does not answer. |
| 2 | **STOP.** Do not invent a ruling. Do not extrapolate from "similar" rules. |
| 3 | Present operator with: `[UNCERTAIN] RAW is silent on: {description}. A House Policy decision is needed. Action cannot be resolved mechanically.` |
| 4 | Offer operator two choices: |
|   | a) **Provide ad-hoc ruling now** (recorded as `[DM_OVERRIDE]`, single-use, not precedent). |
|   | b) **Skip/defer the action** (entity takes no action or alternative action this round). |
| 5 | If operator provides ad-hoc ruling: create event log entry with `[DM_OVERRIDE]` provenance and the text of the ruling. |
| 6 | Log: `UK-POLICY | description | resolution={dm_override|skipped|deferred}` |
| 7 | Create `pm_inbox` entry: `"House Policy CP needed: {description}"` for future ingestion. |

**Stoplight:** RED (no mechanical resolution possible without operator or House Policy).

**STOP CONDITION:** Any attempt by any layer to resolve a UK-POLICY unknown by invention, extrapolation, or "common sense" reasoning is a **CRITICAL** violation of this policy and the Spark/Lens/Box Doctrine (Axiom 2).

---

## 3. Forbidden and Allowed Phrasing

Phrasing rules are enforced per unknown class. These are short and testable: a compliance check can grep runtime output for forbidden patterns.

### 3.1 Universal Forbidden Phrasing (All Classes)

These phrases are **never permitted** in any system output when an unknown is encountered:

| Forbidden Pattern | Reason |
|---|---|
| `"The rules say..."` (without `[BOX]` provenance and rule citation) | False authority. Doctrine Axiom 2. |
| `"You can't do that"` (without Box computation backing it) | Authority claim without provenance. |
| `"I think..."` / `"Probably..."` / `"Most likely..."` | Speculation presented as information. |
| `"Based on similar rules..."` / `"By analogy..."` | Extrapolation from RAW. UK-POLICY STOP condition. |
| `"The DC is..."` / `"The damage is..."` (fabricated value) | Fabricated mechanical value. CRITICAL violation. |
| `"Let's assume..."` / `"For simplicity..."` | Silent invention of facts. |
| `"In most campaigns..."` / `"Typically..."` / `"Usually..."` | External norms imported. Policy must be local. |
| Any mechanical value without `[BOX]` or `[DM_OVERRIDE]` tag | Unprovenanced authority. |

### 3.2 UK-SCENE: Scene Fact Unknowns

**Allowed:**
- `[UNCERTAIN] Cannot determine distance between {A} and {B}. Grid positions needed.`
- `[UNCERTAIN] Line of sight from {A} to {B} cannot be computed. Obstacle data missing.`
- `[UNCERTAIN] Cover status unknown for {entity} at this position.`

**Forbidden:**
- `"They are about 30 feet apart."` (fabricated distance)
- `"You can probably see the target."` (guessed LoS)
- `"There's partial cover."` (invented cover value)

### 3.3 UK-TARGET: Disambiguation

**Allowed:**
- `[UNCERTAIN] Which target? {list of valid targets with identifiers}`
- `[UNCERTAIN] Multiple matches for "{name}": {list}. Please specify.`
- `"There are {N} goblins. Which one?"`

**Forbidden:**
- `"You probably mean the closest one."` (coaching / assumption)
- `"The one that attacked you last round is a better target."` (tactical coaching)
- `"You should attack the injured one."` (forbidden coaching per intent bridge doctrine)
- `"I'll pick the nearest one for you."` (silent resolution of ambiguity)

### 3.4 UK-RULES: Missing Rules

**Allowed:**
- `[BOX] Rule not available: {description}. Action skipped this round.`
- `[BOX] {Feat/Spell/Ability} is not yet in the rules engine. DM override available.`
- `[DM_OVERRIDE] Operator ruling: {text of ruling}. (Single-use, not precedent.)`

**Forbidden:**
- `"This spell probably does {X} damage."` (fabricated spell effect)
- `"In 3.5e, this usually works like..."` (external reference / community debate)
- `"A reasonable ruling would be..."` (system inventing rulings)
- `"Similar to {other spell}, so..."` (analogy-based invention)

### 3.5 UK-STATE: Missing Entity State

**Allowed:**
- `[UNCERTAIN] Entity "{name}" has no recorded armor class. Cannot resolve attack. Please provide AC.`
- `[UNCERTAIN] Entity "{name}" has no grid position. Place on grid to continue.`
- `[DEFAULT] Material defaulted to "wood" for {entity}. (Overridable.)`

**Forbidden:**
- `"AC is probably around 15."` (fabricated AC)
- `"Assuming medium size."` (FORBIDDEN_DEFAULT — size has no default)
- `"Setting hit points to a reasonable value."` (fabricated HP)
- `"Placing entity at a nearby square."` (fabricated position)

### 3.6 UK-ASSET: Missing Assets

**Allowed:**
- (silent fallback to generic — no user-facing message required)
- `[NARRATIVE] (Using generic voice for {character}.)` (optional transparency note)

**Forbidden:**
- `"This character sounds like..."` (inventing voice characterization as fact)
- Any mechanical claim derived from asset absence (e.g., "the darkness means you can't see" when it's just a missing lighting asset, not a Box-computed lighting state)

### 3.7 UK-POLICY: RAW Silence

**Allowed:**
- `[UNCERTAIN] RAW is silent on: {description}. House Policy decision needed.`
- `[DM_OVERRIDE] Operator rules: {text}. (Logged as ad-hoc, not precedent.)`
- `"This situation requires a DM call. The rules don't cover it."`

**Forbidden:**
- `"The intent of the rules is..."` (designer intent speculation)
- `"RAW clearly implies..."` (extrapolation from silence)
- `"A common house rule is..."` (external community norms)
- `"The FAQ/errata says..."` (unless errata is actually ingested in Box)
- Any fabricated DC, damage, or mechanical outcome

---

## 4. Deterministic Decision Table

This table is the canonical runtime lookup. Given an unknown class, it specifies the permitted action(s) and the stoplight severity. Implementations must enforce this table; any deviation is a compliance violation.

| Unknown Class | Permitted Action | Stoplight | Box Halts? | Gameplay Halts? | Operator Notified? |
|---|---|---|---|---|---|
| **UK-SCENE** | JIT acquire via Spark/Lens; if fail: halt action, ask operator | YELLOW | Yes (pending) | Paused | Yes |
| **UK-TARGET** | Disambiguation loop (max 2 rounds); if fail: discard intent | YELLOW | No (pre-Box) | Paused | On timeout only |
| **UK-RULES** | Halt action; skip turn; offer DM override | RED | Yes (hard) | Yes | Yes (always) |
| **UK-STATE** | JIT acquire; apply ALLOWED_DEFAULT if applicable; halt if FORBIDDEN_DEFAULT missing | RED (forbidden) / GREEN (allowed) | Yes if forbidden | Yes if forbidden | Yes if forbidden |
| **UK-ASSET** | Silent fallback; degrade gracefully | GREEN | No | No | No |
| **UK-POLICY** | STOP; escalate to operator; log pm_inbox entry | RED | Yes (hard) | Yes | Yes (always) |

### Decision Table — Prohibited Actions Per Class

| Unknown Class | NEVER Do This |
|---|---|
| **UK-SCENE** | Fabricate distance, LoS, cover, or elevation values |
| **UK-TARGET** | Auto-select a target; provide tactical advice during disambiguation |
| **UK-RULES** | Approximate rule effects; use "similar rule" reasoning; fabricate DCs or damage |
| **UK-STATE** | Apply FORBIDDEN_DEFAULT values; guess ability scores or HP |
| **UK-ASSET** | Halt gameplay; derive mechanical state from asset absence |
| **UK-POLICY** | Invent rulings; import external community consensus; extrapolate from RAW silence |

---

## 5. Compliance Checklist

This checklist is designed for automated and manual compliance testing. Each item is binary pass/fail. A single FAIL on any CRITICAL item blocks the build.

### 5.1 Automated Checks (CI Gate)

| ID | Check | Severity | Pass Condition |
|---|---|---|---|
| UH-CI-001 | No fabricated mechanical values in LLM output | CRITICAL | Grep narration output for numeric patterns not sourced from `[BOX]` or `[DM_OVERRIDE]` = 0 matches |
| UH-CI-002 | All FORBIDDEN_DEFAULT attributes trigger acquisition, not default | CRITICAL | Unit test: entity missing `size`/`position`/`hit_points`/`armor_class` -> `acquire_facts()` called, NOT default applied |
| UH-CI-003 | Disambiguation never auto-selects | CRITICAL | Unit test: ambiguous target -> `CLARIFYING` status set, NOT silent selection |
| UH-CI-004 | UK-RULES triggers halt, not approximation | CRITICAL | Unit test: unimplemented spell/feat -> action returns `skipped`, NOT a fabricated result |
| UH-CI-005 | UK-POLICY triggers STOP, not invention | CRITICAL | Unit test: RAW-silent scenario -> `[UNCERTAIN]` output, pm_inbox entry created, NOT a ruling |
| UH-CI-006 | Asset fallback does not produce mechanical side-effects | HIGH | Unit test: missing asset -> gameplay state hash unchanged before/after fallback |
| UH-CI-007 | All unknown encounters logged with class + resolution | HIGH | Integration test: each UK class triggered -> log entry with `UK-{CLASS}` prefix found |
| UH-CI-008 | Forbidden phrasing patterns absent from output | HIGH | Grep test output corpus for Section 3.1 forbidden patterns = 0 matches |
| UH-CI-009 | Provenance tags present on all operator-facing unknown messages | HIGH | Regex: all messages containing unknown-class keywords carry `[BOX]`, `[UNCERTAIN]`, `[DEFAULT]`, or `[DM_OVERRIDE]` tag |
| UH-CI-010 | JIT acquisition timeout handled (not swallowed) | HIGH | Unit test: Spark callback returns None -> action halted, NOT silently continued |

### 5.2 Manual Review Checks (PR Gate)

| ID | Check | Severity | Pass Condition |
|---|---|---|---|
| UH-PR-001 | No code path where Box fabricates a value it cannot compute | CRITICAL | Code review: every Box resolver that encounters missing input either returns error/halt or calls acquisition protocol |
| UH-PR-002 | No code path where Spark output is treated as mechanical authority | CRITICAL | Code review: no Spark response written to WorldState without Box validation gate |
| UH-PR-003 | No code path where disambiguation loop provides tactical information | HIGH | Code review: disambiguation prompts contain only entity identifiers and neutral spatial references |
| UH-PR-004 | DM override rulings logged with correct provenance | HIGH | Code review: all DM override writes tagged `[DM_OVERRIDE]`, not `[BOX]` |
| UH-PR-005 | pm_inbox entries created for UK-POLICY encounters | MEDIUM | Code review: UK-POLICY handler creates pm_inbox entry with description |

### 5.3 Violation Signals

If any of these signals are detected at runtime, the system is non-compliant with this policy:

| Signal | Indicates | Severity |
|---|---|---|
| Numeric mechanical value in `[NARRATIVE]`-tagged output (e.g., "takes 15 damage" in narration without matching `[BOX]` event) | Spark/narration fabricating mechanical outcomes | CRITICAL |
| Entity gains `armor_class`, `hit_points`, `size`, or `position` without event log entry or acquisition log | Silent invention of FORBIDDEN_DEFAULT attribute | CRITICAL |
| Disambiguation prompt contains comparative language ("the closer one", "the weaker one", "the one you should target") | Tactical coaching during UK-TARGET | HIGH |
| Action resolved despite Box returning "rule not available" | UK-RULES bypass — approximation or silent fallback | CRITICAL |
| `[BOX]` provenance on a value not computed by deterministic engine | False authority labeling | CRITICAL |
| No `UK-{CLASS}` log entry when an unknown was clearly encountered | Silent unknown (logging bypass) | HIGH |
| Output contains any Section 3.1 forbidden phrase | Phrasing policy violation | HIGH |

---

## 6. Conversion Rule: Playtest Unknowns to Regression Tests

Every unknown discovered during playtest **must** result in one of two outcomes. There is no third option.

### 6.1 The Rule

> For every unknown encountered during a playtest session, the session operator **must** produce either:
>
> **(a)** A regression test that reproduces the unknown scenario and verifies the correct policy response, **or**
>
> **(b)** A logged "no issues" entry in the session debrief confirming the system handled the unknown correctly per this policy, with the specific UK class and log entry ID cited.

### 6.2 Regression Test Requirements

When a playtest unknown becomes a regression test:

1. **Test name format:** `test_uk_{class}_{short_description}` (e.g., `test_uk_scene_missing_distance_between_combatants`)
2. **Test must reproduce:** The exact unknown condition (entity state, scene state, action attempted).
3. **Test must assert:** The correct policy response per Section 2 (halt, disambiguate, fallback, escalate).
4. **Test must verify:** No forbidden phrasing (Section 3) appears in output.
5. **Test must verify:** Correct provenance tag on output.
6. **Test must verify:** Log entry with `UK-{CLASS}` prefix was emitted.

### 6.3 "No Issues" Entry Requirements

When a playtest unknown is resolved correctly and does not need a new regression test:

1. **Entry location:** Session debrief log (append-only).
2. **Entry format:** `UK-{CLASS} | {timestamp} | {description} | HANDLED_CORRECTLY | log_entry_id={id}`
3. **Review:** PM or Agent D must sign off that the handling was genuinely correct, not that the unknown was silently swallowed.

### 6.4 Enforcement

- Every playtest session debrief must include a section: "Unknown Encounters."
- If the section is empty, the debriefer must explicitly attest: "No unknowns encountered this session."
- If unknowns were encountered but neither (a) nor (b) was produced: **playtest session is non-compliant** and must be remediated before the next session.

---

## 7. Stop Conditions (Inherited + New)

These stop conditions are active during policy execution. Any agent or runtime component that detects a stop condition must immediately halt the current operation and log the violation.

| ID | Condition | Action |
|---|---|---|
| STOP-UH-001 | Any layer resolves a RAW silence by invention | STOP. Mark `"requires House Policy CP"`. Log CRITICAL. |
| STOP-UH-002 | Any layer fabricates a mechanical value (DC, damage, hit/miss, AC, HP) | STOP. Log CRITICAL. Trigger KILL-002 equivalent. |
| STOP-UH-003 | Any layer imports external community RAW debates or FAQ not ingested in Box | STOP. Policy must be local and enforceable. Log HIGH. |
| STOP-UH-004 | Disambiguation provides tactical coaching | STOP. Revert to neutral prompt. Log HIGH. |
| STOP-UH-005 | FORBIDDEN_DEFAULT attribute applied without Spark acquisition or operator input | STOP. Remove defaulted value. Log CRITICAL. |
| STOP-UH-006 | Unknown encountered but no `UK-{CLASS}` log entry emitted | STOP (on detection). Retroactively log. Investigate suppression path. |

---

## 8. Layer Responsibility Matrix

This matrix clarifies which layer is responsible for detecting and handling each unknown class, consistent with the Spark/Lens/Box Doctrine.

| Unknown Class | Detecting Layer | Handling Layer | Operator-Facing Layer |
|---|---|---|---|
| UK-SCENE | Box (during resolution) | Lens (JIT acquisition) -> Box (re-resolve) | Lens (presents `[UNCERTAIN]` message) |
| UK-TARGET | Intent Bridge (pre-Box) | Intent Bridge (disambiguation loop) | Lens (presents disambiguation prompt) |
| UK-RULES | Box (during resolution) | Box (halt + skip) | Lens (presents `[BOX]` halt message) |
| UK-STATE | Box (during resolution) | Lens (JIT acquisition) -> Box (re-resolve) | Lens (presents `[UNCERTAIN]` message) |
| UK-ASSET | Lens (during presentation) | Lens (silent fallback) | (No message required; optional transparency note) |
| UK-POLICY | Box or Operator (during any phase) | Operator (ad-hoc ruling) or PM (House Policy CP) | Lens (presents `[UNCERTAIN]` escalation) |

**Invariant:** Spark never detects, handles, or escalates unknowns. Spark is pre-law (Doctrine Axiom 1). Unknown handling is a Box/Lens/Operator responsibility.

---

## 9. Interaction with Existing Safeguards

This policy does not replace existing safeguards; it augments them. Here is how each unknown class interacts with the M1 Safeguard inventory:

| Unknown Class | Relevant Safeguard(s) | Interaction |
|---|---|---|
| UK-SCENE | Safeguard 1 (Read-Only Context), Safeguard 5 (Abstention) | If scene fact is unavailable, abstain per SG-005. Memory snapshot remains immutable per SG-001. |
| UK-TARGET | Safeguard 4 (Paraphrase Validation) | Disambiguation must validate that player's clarification maps to a real entity, not a hallucinated one. |
| UK-RULES | Safeguard 6 (Ground Truth Contract) | Box ground truth cannot include rules not ingested. Halting is the only correct response. |
| UK-STATE | Safeguard 2 (Write-Through Validation), Safeguard 5 (Abstention) | JIT-acquired facts must pass validation before Lens write. If acquisition fails, abstain. |
| UK-ASSET | Safeguard 1 (Read-Only Context) | Asset fallback must not mutate game state. LRP-001 constraint. |
| UK-POLICY | Safeguard 6 (Ground Truth Contract) | Ground truth does not cover RAW silence. Only operator can provide ad-hoc ruling. |

---

## 10. Document Governance

### Amendment Process
This policy may only be amended by PM (Thunder) with Agent D stop authority review. Amendments must:
1. Identify the section being amended.
2. Provide rationale grounded in playtest evidence or architectural change.
3. Update the decision table (Section 4) if any unknown class response changes.
4. Not weaken any CRITICAL-severity compliance check without PM + Agent D joint sign-off.

### Review Cycle
- **Mandatory review:** After every playtest session that produces 3+ unknown encounters.
- **Scheduled review:** At each milestone boundary (M1 -> M2, M2 -> M3).
- **Ad-hoc review:** When a new CP packet closes a previously open UK-RULES or UK-POLICY gap.

### Versioning
| Version | Date | Author | Change |
|---|---|---|---|
| 0.1 (DRAFT) | 2026-02-13 | Agent B (Sonnet) | Initial creation per WO-RQ-UNKNOWN-TAXONOMY-01 |

---

**END OF RQ-UNKNOWN-HANDLING-POLICY-01**

**Date:** 2026-02-13
**Agent:** Agent B (Sonnet)
**Authority:** DRAFT (requires PM approval to become BINDING)
**WO:** WO-RQ-UNKNOWN-TAXONOMY-01
