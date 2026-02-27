# REGISTER — Hidden DM Kernels
**Artifact ID:** REGISTER-HIDDEN-DM-KERNELS-001
**Type:** architecture_register / kernel_map
**Authority:** pair (Thunder + Anvil)
**Date:** 2026-02-26
**Status:** live
**Source:** Cheevo canary analysis + deeper pass on "what the engine models vs. what it is"
**Related:** LEDGER-CHEEVO-CANARY-EXPANSION-001, CANARY-GAP-TAXONOMY-001, STRATEGY-REDTEAM-AXIS-001

---

## Purpose

The PHB documents what mechanics do.

It does not document the ten DM functions a human already knows how to perform before opening the book. These functions are invisible because they are never wrong for a human DM — they operate below the level of conscious decision.

When you encode the PHB, you get all the mechanics. You do not get these functions.

This register names them.

**The coverage map asks:** which mechanics are implemented?
**This register asks:** which assumptions are implemented?

These are different maps. The coverage map can reach 100% and still fail a creative player because none of the mechanics it tracks address what a Genie *is*.

---

## The Core Insight

> **The engine models what entities can do. It does not model what entities are.**

What something *is* determines:
- What it's bound by (contracts, nature, weaknesses)
- What it wants (motivation, not just stat blocks)
- How it interacts with the environment
- What persists when it leaves the immediate encounter
- How all mechanics apply to it

The Lich isn't just an entity with high HP and a phylactery field. The Lich is a *type of thing* with a nature that governs how all mechanics apply to it. The engine has a stats layer. It does not have a nature layer.

Every canary in the Cheevo list is a player finding where the nature layer is missing.

---

## The Canary Question

When a new canary surfaces, ask this before anything else:

> **"Which hidden DM kernel is this scene forcing me to use?"**

That surfaces the missing primitive faster than scenario-level discussion.

---

## The Register

---

### KERNEL-01 — Entity Lifecycle Ontology

**What the human DM does silently:**
Tracks what an entity is across all states — alive, dying, dead, destroyed, transformed, incorporeal, undead, summoned, dismissed, imprisoned, rejuvenating. Knows which mechanics apply at each state. Knows what persists through state transitions.

**Canary examples:**
- Lich at 0 HP — not dead; rejuvenating at phylactery
- Troll at 0 HP — not dead; regenerating unless fire/acid applied
- Vampire at 0 HP — not dead; gaseous form retreating to coffin
- Defeated entity → corpse → lootable remains → raised undead → defeated again
- Entity polymorphed into object — is it still targetable as a creature?

**Current engine support:** NONE
The engine has: alive / dead / removed from combat. That is a two-state model for a ten-state problem.

**Failure mode if missing:**
- Lich is "dead" after HP 0 — phylactery mechanic never fires
- Troll is "dead" — regeneration never triggers
- Corpse doesn't exist — looting, Speak with Dead, Raise Dead all fail
- Transformed entities have wrong mechanics applied

**Artifact route:** PROBE-WORLDMODEL-001 → STRATEGY-ENTITY-LIFECYCLE-001 → WOs

**Priority:** CRITICAL — blocks looting, necromancy, boss encounters, crafting

**Canary cross-pollination log:**
- [WO-ENGINE-BARBARIAN-DR-001, Batch S] Pass 3: FINDING-ENGINE-LEVELUP-POOL-SYNC-001 — chargen builder.py applies barbarian DR pool effects; level-up path does not. Entity lifecycle transitions (chargen → level-up → rest → death) must each apply all relevant field updates. The engine's two-state model (chargen/play) does not account for in-play state transitions that accumulate fields (DR, HP, feat unlocks). Level-up is a lifecycle event, not just a stat increment.

---

### KERNEL-02 — Containment Topology

**What the human DM does silently:**
Reasons about physical location as a relationship, not just a map position. Knows that "inside the Barbarian's stomach" is a location. Knows that "inside a Bag of Holding" is a different kind of location. Knows the difference between carried, swallowed, imprisoned, and contained.

**Canary examples:**
- Phylactery swallowed — item inside a creature's body
- Player swallowed whole by Purple Worm — creature inside a creature
- Bag of Holding — item inside extradimensional space inside an object
- Rope Trick — party inside a pocket dimension
- Mimic — is it a creature or an object right now?

**Current engine support:** NONE
The engine has: grid coordinates. Items have positions. Creatures have positions. Neither can be inside the other.

**Failure mode if missing:**
- Containment scenarios crash or route to HALLUCINATE
- "Inside" is not a valid location concept
- Nested effects (AoE inside a contained space) have no resolution

**Artifact route:** PROBE-WORLDMODEL-001 → STRATEGY-TOPOLOGY-001 → WOs

**Priority:** HIGH — required for swallow attacks, extradimensional items, imprisonment

---

### KERNEL-03 — Constraint Algebra

**What the human DM does silently:**
Tracks behavioral constraints on all actors — oaths, vows, curses, Geas, compulsions, pact obligations, divine mandates, contracts. Knows which constraints conflict. Knows precedence. Evaluates each action against active constraints before resolving it. Knows the difference between letter and spirit.

**Canary examples:**
- Kevin's 6 simultaneous Pegasus oaths
- Paladin Code of Conduct — multiple prohibitions
- Geas — Constitution damage for non-compliance
- Warlock pact obligations
- "I never kill" self-imposed restriction — does healing the Orc and burning him violate it?

**Current engine support:** NONE
Constraints exist as narrative flavor only. No tracking, no evaluation, no violation detection.

**Failure mode if missing:**
- Paladin violations not detected — no fall, no consequence
- Geas has no mechanical enforcement
- Stacked oath exploitation not caught
- Constraint conflicts silently ignored

**Artifact route:** PROBE (can judgment scaffold track/evaluate constraints?) → STRATEGY-CONSTRAINT-ALGEBRA-001 → WOs

**Priority:** HIGH — Paladins alone make this constant

**Cross-pollination note:** Concentration spells, attunement limits, spell preparation tracking, and Geas all require the same underlying constraint primitive. One subsystem serves all of these.

---

### KERNEL-04 — Intent Semantics / Adjudication Language Policy

**What the human DM does silently:**
Interprets player declarations with appropriate charity. Knows when to read literally, when to read intent, when to ask for clarification. Has a consistent policy for ambiguous phrasing. Doesn't let the player exploit ambiguity against their own interest, and doesn't punish them for imprecise language.

**Canary examples:**
- Genie wish wording — "I wish to be free of the lamp" → strictly literal → floppy on the floor
- "I attack the orc" — which orc? With what? Main hand? Off hand?
- "I want to do something creative" — meaningless declaration, requires clarification
- "I try to disarm him" vs "I grab his sword" vs "I cut off his hand" — three very different intents

**Current engine support:** PARTIAL
Intent parsing exists in the parser/routing layer. Policy for ambiguous declarations is not formalized.

**Failure mode if missing:**
- Literal reading advantages the house over the player (or vice versa inconsistently)
- Ambiguous declarations route to wrong resolver
- Player exploits imprecision intentionally without detection
- LLM grants wishes on clever wording without flagging the interpretation

**Artifact route:** POLICY decision → SPEC-INTENT-SEMANTICS-001 → Gate

**Priority:** MEDIUM — parser exists; policy formalization is the gap

---

### KERNEL-05 — Epistemic State

**What the human DM does silently:**
Tracks what each actor knows, believes, suspects, and falsely believes. Gates action resolution on in-fiction knowledge. Knows that the player knowing a monster's weakness doesn't mean the character knows it. Asks for Knowledge checks before allowing weakness exploitation.

**Canary examples:**
- Player knows Lich has a phylactery — does character know this? Knowledge: Religion DC 15?
- Player knows Medusa gaze is mutual — has the character observed this?
- Player knows troll regeneration stops with fire — Knowledge: Nature check?
- Player knows exactly where the vampire's coffin is — how?

**Current engine support:** NONE
Engine has no per-actor knowledge model. Player omniscience is the default.

**Failure mode if missing:**
- Players exploit monster mechanics without earning the knowledge
- LLM acts omniscient when generating rulings
- Metagaming is structurally rewarded
- Knowledge skills have no function

**Artifact route:** PROBE-JUDGMENT-LAYER-001 (can the scaffold gate on knowledge?) → STRATEGY-EPISTEMIC-MODEL-001

**Priority:** HIGH — metagaming is the default behavior without this

---

### KERNEL-06 — Termination Doctrine

**What the human DM does silently:**
Feels when a scene has run its course. Compresses repeated cycles. Says "OK, after three more rounds of this, let's say the Orc is done." Knows when to abstract rather than resolve every iteration. Has criteria — often unstated — for when tactical resolution gives way to narrative summary.

**Canary examples:**
- Heal/burn loop — mechanically legal, but a DM ends it after a few cycles
- Repeated Intimidate attempts — DM sets a practical limit
- Pursuing a fleeing creature across multiple sessions — at some point it becomes montage
- 20-round combat where one side is clearly losing — DM compresses

**Current engine support:** NONE
Engine resolves every round identically. No loop detection. No compression. No escalation path to operator.

**Failure mode if missing:**
- Loops run indefinitely
- Event logs explode
- Pacing collapses
- Table trust erodes
- Operator has no mechanism to intervene

**Artifact route:** POLICY (define compression triggers) → SPEC-TERMINATION-DOCTRINE-001 → Gate

**Priority:** HIGH — abuse-loop prevention is required for production

---

### KERNEL-07 — Social / Moral Consequence Propagation

**What the human DM does silently:**
Tracks the world's response to player actions beyond HP. Notes when an action has reputation consequences. Notes when a town would hear about what happened. Notes alignment drift candidates. Tells the player "the innkeeper looks at you differently now." Makes the world feel like it remembers.

**Canary examples:**
- Kevin tortures the Orc without technically killing him — the Pegasus notices
- Barbarian eats the Succubus's heart — a reputation event
- Paladin uses Detect Evil on crowd — witnesses react
- Player kills a surrendered enemy — no mechanical penalty, but consequences

**Current engine support:** NONE
Engine emits no consequence signals. All legal actions are treated identically.

**Failure mode if missing:**
- Pathological legal play is structurally rewarded
- NPCs have no memory
- Alignment is flavor only
- The world feels like a combat simulator, not a living world

**Artifact route:** STRATEGY-CONSEQUENCE-SYSTEM-001 → DM layer design (not engine mechanics) → Gate

**Priority:** MEDIUM now / HIGH for full AIDM experience

---

### KERNEL-08 — Precedent / Jurisprudence

**What the human DM does silently:**
Remembers past rulings. Applies them consistently. Promotes recurring rulings into standing policy. Says "we ruled last time that sand kicks count as a blinding attempt with a Reflex save — same ruling here." Converts ad hoc decisions into common law over time.

**Canary examples:**
- Sand kick in session 1 → same action in session 4 → should get same ruling
- "Torch to face" ruled as Dazzled save in one encounter — should be consistent
- Improvised lockpick ruling should propagate to next improvised tool
- Hag coven ruling should set precedent for all group-dependent abilities

**Current engine support:** NONE
Every session starts cold. No ruling memory. No promotion path. No precedent register.

**Failure mode if missing:**
- Inconsistent rulings across sessions
- Players game the inconsistency
- Builders re-solve the same problem in every WO
- LLM hallucinates new answers to questions already answered

**Artifact route:** POLICY → SPEC-PRECEDENT-REGISTER-001 → Gate

**Priority:** MEDIUM — becomes HIGH as session count increases

**Cross-pollination note:** Every WO debrief Pass 3 that catches a latent issue is potentially a precedent entry. The debrief and the precedent register should be connected.

---

### KERNEL-09 — Resolution Granularity / Abstraction Ladder

**What the human DM does silently:**
Chooses how detailed to be. Resolves a long chase as "you run for an hour, roll Endurance twice" rather than 600 individual movement actions. Knows when to zoom in (critical combat moment) and when to zoom out (routine activity). Moves up and down this ladder constantly.

**Canary examples:**
- 10-round search of a large room — not 10 individual Search checks
- Travel to the next town — not resolved as individual 6-second movement rounds
- Repeated crafting attempts — "you spend a week working on it, roll twice"
- Long interrogation — summary result, not every exchange resolved

**Current engine support:** NONE
Engine resolves at tactical granularity. No abstraction layer. No montage mode.

**Failure mode if missing:**
- All activities resolved at same granularity regardless of importance
- Time compression impossible
- Downtime activities have no resolution mechanism
- Players can slow the game by insisting on round-by-round for irrelevant activities

**Artifact route:** STRATEGY-RESOLUTION-GRANULARITY-001 → Spec → Gate

**Priority:** MEDIUM — required before the engine can support non-combat play

---

### KERNEL-10 — Adjudication Constitution

**What the human DM does silently:**
Has an implicit policy for what they will and won't rule on. Will adjudicate "I try to disarm him" but abstract "I want to torture him for information." Will resolve "I set fire to the tapestry" but not narrate the results in graphic detail. Has lines, and applies them consistently without articulating them.

**Canary examples:**
- "I torture the prisoner graphically" — DM abstracts the narration, resolves mechanics only
- "I try to seduce the guard" — DM decides whether to resolve mechanically or narratively
- "I do something completely impossible" — DM declines cleanly without crashing
- "I want to do X which requires rules we never established" — DM escalates to operator

**Current engine support:** PARTIAL (content boundaries exist; policy is not formalized)

**Failure mode if missing:**
- Engine narrates disallowed content while resolving mechanics
- Engine refuses legal actions because narration is uncomfortable
- Mechanical resolution collapses when content boundary is hit
- No escalation path when engine can't rule

**Artifact route:** POLICY → SPEC-ADJUDICATION-CONSTITUTION-001 → Gate

**Priority:** HIGH — required before LLM narration layer can be trusted

---

## Summary Table

| # | Kernel Name | Engine Support | Priority | Route |
|---|-------------|----------------|----------|-------|
| 01 | Entity Lifecycle Ontology | NONE | CRITICAL | PROBE-WORLDMODEL → STRATEGY |
| 02 | Containment Topology | NONE | HIGH | PROBE-WORLDMODEL → STRATEGY |
| 03 | Constraint Algebra | NONE | HIGH | PROBE → STRATEGY |
| 04 | Intent Semantics / Adjudication Language | PARTIAL | MEDIUM | POLICY → SPEC |
| 05 | Epistemic State | NONE | HIGH | PROBE-JUDGMENT → STRATEGY |
| 06 | Termination Doctrine | NONE | HIGH | POLICY → SPEC |
| 07 | Social / Moral Consequence | NONE | MEDIUM→HIGH | STRATEGY → DM layer |
| 08 | Precedent / Jurisprudence | NONE | MEDIUM→HIGH | POLICY → SPEC |
| 09 | Resolution Granularity | NONE | MEDIUM | STRATEGY → SPEC |
| 10 | Adjudication Constitution | PARTIAL | HIGH | POLICY → SPEC |
| 11 | Time / Calendar / Refresh Semantics | NONE | HIGH | STRATEGY-WORLD-CLOCK-001 |
| 12 | Event Idempotency / One-Time State Transitions | NONE | HIGH | PROBE-WORLDMODEL → STRATEGY |
| 13 | Ownership / Provenance / Legitimacy | NONE | MEDIUM | PROBE-WORLDMODEL → STRATEGY |
| 14 | Effect Composition Semantics | NONE | MEDIUM | PROBE-JUDGMENT → STRATEGY |
| 15 | Social State Propagation / Institutional Memory | NONE | HIGH | PROBE-WORLDMODEL → STRATEGY |

---

## The Cross-Pollination Routing Instruction

**For Slate / builders:**

When a WO debrief Pass 3 surfaces a finding that touches a kernel listed above, flag it in this register.

Format: add to the relevant kernel's canary examples list:
```
- [WO-ID] Pass 3 finding: [what was noticed]
```

This makes the compounding automatic. Builders in adjacent areas see the same primitive showing up across multiple WOs. One subsystem gets built instead of three bespoke solutions.

**Examples of what to watch for:**
- Concentration spell tracking → KERNEL-03 (Constraint Algebra)
- Attunement limits → KERNEL-03
- Geas mechanical enforcement → KERNEL-03
- Ranger favored enemy knowledge → KERNEL-05 (Epistemic State)
- Lich boss encounter HP → KERNEL-01 (Lifecycle Ontology)
- Item looting after combat → KERNEL-01
- NPC attitude shift after player action → KERNEL-07 (Social Consequence)
- Judgment scaffold ruling that recurs → KERNEL-08 (Precedent)

---

## The Real Thesis

> **The PHB documents mechanics. The human DM is ten invisible functions running underneath them.**

The coverage map tracks mechanics. This register tracks the functions.

Both maps are needed.

A coverage map at 100% with no kernel register means the engine can resolve every named mechanic correctly and still fail a creative player who finds a seam between them.

The Barbarian found every seam. Twelve minutes. Comedy video.

The kernels are where the gas is coming in. The canaries showed us the vents.

---

### KERNEL-11 — Time / Calendar / Refresh Semantics

**What the human DM does silently:**
Tracks what "a day" means in-world. Knows what resets on a short rest vs. long rest vs. per-day vs. per-session. Knows how much time passes between scenes. Knows when a buff expires, when a disease progresses, when a negative level save comes due, when a wanted poster goes stale.

**Canary examples:**
- Coffeelock — exploit depends on skipping the long rest reset trigger entirely
- Guard goldfish memory — crime state resets after an implicit timer
- Negative level 24-hour save — delayed mechanical consequence with real-world clock
- Disease progression — Con drain happens over days; engine must track calendar
- Downtime — party rests a week; what does the world do during that time?

**Current engine support:** NONE
Engine resolves moment-to-moment and round-to-round. No world clock. No calendar. No refresh-cycle awareness beyond per-encounter.

**Failure mode if missing:**
- Time-delayed conditions (negative levels, disease) never fire
- Rest economy exploits are undetectable
- The world doesn't age — NPCs, quests, and events never change with time
- Buff durations that outlast encounters have no expiry mechanism

**Artifact route:** STRATEGY-WORLD-CLOCK-001 (new) → Spec → WOs

**Priority:** HIGH — negative levels, disease, and rest economy all require this

---

### KERNEL-12 — Event Idempotency / One-Time State Transitions

**What the human DM does silently:**
Knows that some events happen once. A quest reward is given once. A secret is revealed once. A trap triggers once (then it's sprung). A bargain is struck once. Marks events as consumed and doesn't re-trigger them. Knows the difference between a repeatable action and a unique event.

**Canary examples:**
- NPC dialogue loop — reward re-given because event is not marked consumed
- Quest turn-in repeated — no flag on "already completed"
- Trap reset — does a triggered trap automatically reset, or is it spent?
- Diplomacy check repeated — does a failed persuasion attempt lock out future attempts?
- Unique item granted — can the same unique item be awarded twice?

**Current engine support:** NONE
Engine has no event-history state. NPC interactions are stateless. Events are not flagged as consumed.

**Failure mode if missing:**
- Infinite reward loops are structurally possible
- Players can retry social checks until they succeed with no cost
- Traps reset invisibly
- Unique events repeat
- AI-DM has no memory of what already happened to gate repetition

**Artifact route:** PROBE-WORLDMODEL-001 — event history is world state → STRATEGY-EVENT-IDEMPOTENCY-001

**Priority:** HIGH — directly determines whether the AI-DM can be gamed via repetition

---

### KERNEL-13 — Ownership / Provenance / Legitimacy

**What the human DM does silently:**
Tracks who owns what. Knows when an item is stolen, lost, gifted, or inherited. Knows that "selling a stolen item" has different social consequences than selling one's own goods. Knows that a forged document has different legitimacy than a real one. Tracks item provenance as a world property, not just a player-inventory property.

**Canary examples:**
- Stolen loot resale — merchant should recognize their own goods
- Fencing stolen items — different NPCs have different reactions based on item origin
- Forged noble seal (Prestidigitation) — legitimacy is world state, not just item appearance
- Inherited magic item — provenance affects whether it's recognized by a faction
- Looted holy symbol — does the temple know this belongs to a fallen cleric?

**Current engine support:** NONE
Items have no provenance field. Ownership is not tracked. All items in a player's inventory are equally "theirs."

**Failure mode if missing:**
- Stolen goods are functionally identical to legitimately owned goods
- Fraud via Prestidigitation or forgery has no detectable world-state difference
- Social consequence of theft is unenforceable
- Economy exploits (stolen loot resale) structurally succeed

**Artifact route:** PROBE-WORLDMODEL-001 — provenance as item metadata → STRATEGY-ECONOMY-PROVENANCE-001

**Priority:** MEDIUM — required for living-world economy; HIGH if social consequence system is prioritized

---

### KERNEL-14 — Effect Composition Semantics

**What the human DM does silently:**
Adjudicates what happens when two legal effects combine into a higher-order outcome that neither rule anticipated. Knows that Mold Earth + Silent Image might produce a convincing fake pit. Knows that Prestidigitation + poison might produce an undetectable poisoned meal. Knows when composition produces something new vs. when two effects simply coexist independently.

**Canary examples:**
- Prestidigitation masking poison — two effects composing into a social/deception outcome
- Illusion + terrain — Silent Image of a pit fools enemies into walking off a real ledge
- Silence + Darkness — two AoE denial spells stacked; who can do what?
- Grease + Fire — fire spell on a greased floor; is the interaction modeled?
- Bull Rush into a Wall of Fire — does the pushed creature take fire damage on entry?

**Current engine support:** NONE
Engine resolves each effect independently. No composition model. Emergent outcomes from effect stacking are unaddressed.

**Failure mode if missing:**
- Creative combinations either silently fail or silently succeed with no consistent model
- LLM adjudicates compositions inconsistently across sessions
- Players with composition knowledge gain structural advantage over players without it
- Novel interactions produce HALLUCINATE or refusal rather than consistent rulings

**Artifact route:** PROBE-JUDGMENT-LAYER-001 — composition adjudication is a judgment gap → STRATEGY-EFFECT-COMPOSITION-001

**Priority:** MEDIUM — becomes HIGH as spell variety increases

---

### KERNEL-15 — Social State Propagation / Institutional Memory

**What the human DM does silently:**
Models how information spreads through the world. Knows that killing a guard in town A doesn't immediately alert town B, but that news travels and factions communicate. Knows that a bounty posted in the capital reaches the frontier in days, not rounds. Knows that the Thieves' Guild remembers what happened to their member even if the city watch doesn't. Tracks reputation not just as a per-NPC attitude but as a world-level state.

**Canary examples:**
- Guard goldfish memory — crime witnessed but not propagated to other guards
- Faction excommunication — does the whole faction know simultaneously?
- Wanted poster — how fast does a bounty spread? Does it cross zone boundaries?
- Player kills an NPC's family — does anyone else in the family hear about it?
- Party burns a village — do neighboring villages bar their doors when the party arrives?

**Current engine support:** NONE
Engine tracks per-NPC attitude at best. No faction-level state. No propagation model. No world-level reputation. Information is local and static.

**Failure mode if missing:**
- Actions have no persistent social footprint
- World feels like isolated encounter pods with no memory between them
- Faction mechanics are unenforceable
- Reputation systems are narrative-only, never mechanical
- Players can commit crimes and outrun the news every time

**Artifact route:** PROBE-WORLDMODEL-001 — faction state and information propagation are world model → STRATEGY-SOCIAL-PROPAGATION-001

**Priority:** HIGH — required for a living world; without it, the VLDL guard memory gap is permanent

---

## Summary Table (Updated)

| # | Kernel Name | Engine Support | Priority | Route |
|---|-------------|----------------|----------|-------|
| 01 | Entity Lifecycle Ontology | NONE | CRITICAL | PROBE-WORLDMODEL → STRATEGY |
| 02 | Containment Topology | NONE | HIGH | PROBE-WORLDMODEL → STRATEGY |
| 03 | Constraint Algebra | NONE | HIGH | PROBE → STRATEGY |
| 04 | Intent Semantics / Adjudication Language | PARTIAL | MEDIUM | POLICY → SPEC |
| 05 | Epistemic State | NONE | HIGH | PROBE-JUDGMENT → STRATEGY |
| 06 | Termination Doctrine | NONE | HIGH | POLICY → SPEC |
| 07 | Social / Moral Consequence | NONE | MEDIUM→HIGH | STRATEGY → DM layer |
| 08 | Precedent / Jurisprudence | NONE | MEDIUM→HIGH | POLICY → SPEC |
| 09 | Resolution Granularity | NONE | MEDIUM | STRATEGY → SPEC |
| 10 | Adjudication Constitution | PARTIAL | HIGH | POLICY → SPEC |
| 11 | Time / Calendar / Refresh Semantics | NONE | HIGH | STRATEGY-WORLD-CLOCK-001 |
| 12 | Event Idempotency / One-Time State Transitions | NONE | HIGH | PROBE-WORLDMODEL → STRATEGY |
| 13 | Ownership / Provenance / Legitimacy | NONE | MEDIUM | PROBE-WORLDMODEL → STRATEGY |
| 14 | Effect Composition Semantics | NONE | MEDIUM | PROBE-JUDGMENT → STRATEGY |
| 15 | Social State Propagation / Institutional Memory | NONE | HIGH | PROBE-WORLDMODEL → STRATEGY |

---

*Filed 2026-02-26. Authority: pair (Thunder + Anvil).*
*KERNEL-01 through KERNEL-10: sourced from Dungeon Soup canary analysis.*
*KERNEL-11 through KERNEL-15: sourced from second-wave canary analysis (Pack Tactics, VLDL, Dungeon Dad, Zee Bashew) — surfaced by Aegis review.*
*This register grows as Pass 3 debriefs surface kernel touches. Make the compounding automatic.*
*The coverage map tells you what's implemented. This register tells you what's assumed.*
