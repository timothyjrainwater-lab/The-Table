# AIDM: The Case for an Honest Referee

## What This Is

AIDM is a software system that runs tabletop Dungeons & Dragons sessions — specifically the 3.5 Edition ruleset — with an AI acting as the Dungeon Master.

That sentence sounds simple. It is not. Every existing attempt to do this has failed in the same way, and understanding *why* they fail is the reason this project exists.

## The Problem Nobody Solves

When a human Dungeon Master runs a game, they hold two jobs simultaneously: **referee** and **storyteller**. The referee enforces rules, rolls dice, tracks hit points, and determines what is mechanically true. The storyteller describes the world, voices the characters, builds tension, and makes the experience feel alive.

These two jobs have fundamentally different requirements:

- The referee must be **deterministic**. The same attack roll against the same armor class must always produce the same outcome. Players trust the referee because the rules are knowable and consistent.
- The storyteller must be **creative**. No two descriptions of a sword strike should sound identical. Players enjoy the storyteller because the narrative is surprising and evocative.

Every AI Dungeon Master built to date collapses these two jobs into a single language model. The AI generates both the ruling and the narration in one breath. This creates a system where:

- You cannot verify whether a ruling was correct, because the reasoning is entangled with prose.
- You cannot replay a session to check for errors, because the output is non-deterministic.
- You cannot tell whether the AI showed mercy, made a mistake, or followed the rules, because all three look the same from the outside.
- You cannot trust the system, because trust requires transparency, and a language model is opaque.

For casual players, this might be acceptable. For experienced players — the kind who know the rules well enough to notice when something is wrong — it is fatal. One invisible error, one suspicion that the AI fudged a roll or softened an encounter, and the entire system loses credibility permanently. There is no recovery from a DM you suspect of cheating.

## What AIDM Does Differently

AIDM separates the referee from the storyteller at the architectural level. They are not two modes of the same system. They are two independent systems with a strict boundary between them.

### Box: The Referee

Box is a deterministic rules engine. It implements D&D 3.5 Edition combat mechanics in code — not by asking a language model what the rules say, but by encoding the rules directly as algorithms. When a fighter attacks a goblin, Box:

1. Rolls a d20 using a seeded random number generator (the same seed always produces the same sequence of rolls)
2. Adds the attack bonus from the character's stats
3. Compares the total against the target's armor class
4. Determines hit or miss according to the written rules
5. If hit, rolls damage dice and applies the result to the target's hit points
6. Records every step as a structured event with a citation to the specific rulebook page that governs the mechanic

Box handles attacks, spells, saving throws, critical hits, conditions, initiative, attacks of opportunity, combat maneuvers, feats, skills, experience, and leveling. It implements 53 spells, 15 feats, 7 skills, 8 combat conditions, and 6 combat maneuvers — all from the 3.5 Edition core rulebooks (Player's Handbook, Dungeon Master's Guide, Monster Manual).

Box has one inviolable property: **every session is fully reproducible**. Given the same starting state and the same random seed, Box produces the exact same sequence of events, every time, forever. This means:

- Sessions can be replayed for verification
- Bugs can be reproduced deterministically
- Disputes can be resolved by examining the event log
- The system can prove it followed the rules

No language model is involved in any mechanical decision. Ever.

### Spark: The Storyteller

Spark is a language model (a local LLM running on the player's machine) that generates narrative descriptions of what happened. After Box determines that the fighter's sword hit the goblin for 8 damage and the goblin was defeated, Spark turns that into:

> *"Aldric's blade flashes in the torchlight, catching the goblin squarely in the chest. The creature staggers backward, blood soaking its jerkin, and crumples to the ground."*

Spark makes the experience atmospheric and immersive. It gives NPCs distinct voices. It describes environments with sensory detail. It adapts its tone — gritty and terse for a dungeon crawl, theatrical and dramatic for a climactic battle.

Spark has one inviolable property: **it has zero mechanical authority**. It cannot change what happened. It cannot decide that the attack missed when Box said it hit. It cannot invent damage that Box did not calculate. It cannot assert that a character is defeated when Box says otherwise. Spark describes outcomes — it does not determine them.

If Spark fails (the model crashes, times out, or generates something that contradicts the mechanical truth), the system falls back to one of 55 pre-written templates that describe the outcome accurately, if less colorfully. The game never stops. The rules are never compromised.

### Lens: The Boundary

Lens sits between Box and Spark. Its job is to control what Spark can see.

When Box resolves a combat action, it produces detailed mechanical data: entity IDs, hit point values, armor class numbers, dice roll breakdowns, grid coordinates. If Spark could see all of this, it might start asserting mechanical facts in its narration ("the goblin's AC of 15 was no match for the +6 attack bonus"), which would confuse players about where truth comes from.

Lens translates Box's mechanical output into a "narrative brief" — a sanitized summary that tells Spark what happened without exposing the internal machinery. Spark knows that a character hit a target with moderate severity using a longsword. It does not know entity IDs, raw hit point values, armor class numbers, or the random number generator's state.

This is a one-way valve. Information flows from Box through Lens to Spark. It never flows backward. Spark cannot query Box. Spark cannot request mechanical information. Spark cannot influence future mechanical decisions.

## Why This Matters

### For Players

The promise is simple: **the AI will never cheat**. Not because it is instructed not to, but because it is architecturally incapable of doing so. The rules engine cannot be influenced by the narrative engine. The dice rolls are real and verifiable. Every ruling can be traced to a specific page in the rulebook.

If a character dies, it is because the rules dictated that outcome — not because an AI decided it would be dramatic. If a character survives, it is because their armor class was high enough and the enemy's roll was low enough — not because the AI decided to show mercy.

This is important because D&D is, at its core, a game about meaningful consequences in a world governed by consistent rules. Remove the consistency, and the consequences become meaningless. Remove the consequences, and the game becomes a story being told *to* you rather than a story you are *living*.

### For DMs

Experienced Dungeon Masters run games for years. They know the rules deeply. They notice when something is wrong. Existing AI DMs frustrate these players because:

- The AI makes rulings that contradict the written rules, and cannot explain why
- The AI appears to adjust difficulty based on narrative pacing rather than mechanical reality
- The AI cannot be audited — there is no way to examine its reasoning after the fact
- The AI applies safety filters that feel like corporate policy rather than game rules (refusing to describe combat violence, for instance, in a game that is fundamentally about combat)

AIDM addresses each of these:

- Every ruling is backed by a citation to specific rulebook pages
- Difficulty is determined by creature statistics from the Monster Manual and tactical policies derived from creature intelligence — not narrative convenience
- Every session produces a complete event log that can be replayed, audited, and examined
- The narrative layer is configurable (gritty, theatrical, humorous) and never applies content policies that override the game's own rules

### For the Field

AIDM demonstrates that separating mechanical authority from narrative generation is not just possible — it is necessary for trustworthy AI game systems. The architecture proves that:

- A deterministic rules engine can handle real complexity (3,753 tests covering the full combat system pass in under a minute)
- Language models can add genuine value as narrators without needing mechanical authority
- The boundary between deterministic truth and creative generation can be formally enforced
- Sessions played with AI assistance can be fully reproducible and auditable

This has implications beyond tabletop gaming. Any system where an AI must make decisions that users need to trust — legal reasoning, medical protocols, financial compliance — faces the same fundamental problem: how do you separate authoritative computation from natural language presentation without one contaminating the other?

## How It Works in Practice

A player sits down. They speak (or type) a command:

> "I attack the goblin with my longsword."

The system processes this through a pipeline:

1. **Speech recognition** (optional) converts voice to text
2. **Intent parsing** extracts the structured action: attack, target = goblin, weapon = longsword
3. **Intent resolution** maps the natural language references to internal game entities (which goblin? which longsword?)
4. **Box executes** the attack: rolls dice, computes bonuses, determines hit or miss, calculates damage, updates hit points, checks for defeat
5. **Events are logged**: every roll, every computation, every outcome, with rulebook citations
6. **Lens builds a narrative brief**: strips mechanical internals, produces a safe summary for the storyteller
7. **Spark narrates**: generates a 1-2 sentence description of what happened, in the DM's configured voice
8. **Text-to-speech** (optional) reads the narration aloud in a distinct voice

The player hears: *"Your blade catches the goblin across the ribs — it lets out a strangled cry and drops to the ground."*

Behind the scenes, an immutable, auditable record of exactly what happened and why has been appended to the session log.

## What Has Been Built

The system is not a prototype or a concept document. It is a working engine with:

- **3,753 passing tests** covering the full combat resolution stack
- **53 spells** (levels 0-5) with targeting, saving throws, area effects, concentration, and duration tracking
- **15 combat feats** (Power Attack, Cleave, Two-Weapon Fighting, Dodge, Mobility, and more) with prerequisite validation
- **6 combat maneuvers** (Bull Rush, Disarm, Grapple, Overrun, Sunder, Trip) with opposed checks and attacks of opportunity
- **8 combat conditions** (Prone, Flat-Footed, Grappled, Helpless, Stunned, Dazed, Shaken, Sickened) that modify attacks, defense, and saves
- **Area-of-effect geometry** for bursts, cones, and lines
- **Line of sight and cover calculations** for tactical positioning
- **Mounted combat** with rider-mount coupling
- **Monster tactical AI** that selects tactics based on creature intelligence and Monster Manual behavior descriptions — using a deterministic policy engine, not a language model
- **Initiative, action economy, and round tracking** with flat-footed state management
- **Experience and leveling** with CR-based XP calculations
- **Text-to-speech integration** with distinct voice personas for the DM and NPCs
- **Session orchestration** that wires the full pipeline from voice input through combat resolution to narrated output
- **965 pages of extracted rulebook text** organized for page-level citation
- **Deterministic replay verification** (same seed + same actions = identical state hash, proven across thousands of test runs)

## What Is Not Built Yet

The system does not yet support:

- Full campaign persistence across multiple sessions (schemas exist, storage does not)
- NPC dialogue generation (reserved, not implemented)
- Exploration and non-combat gameplay loops
- Character creation workflows
- A graphical user interface (the system is currently command-line and voice)
- All D&D 3.5e content (many spells, feats, prestige classes, and monsters remain unimplemented)

These are engineering tasks, not architectural problems. The hard part — proving that a deterministic referee and a creative storyteller can coexist without contaminating each other — is done.

## The Core Belief

This project is built on one conviction: **players deserve an AI that earns trust through transparency, not one that demands trust through opacity.**

A human DM earns trust over years of consistent rulings. An AI DM cannot earn trust through personality or reputation. It can only earn trust by being auditable — by producing decisions that can be examined, replayed, verified, and challenged.

AIDM does not ask players to trust it. It asks players to verify it. That is the difference.

## The No-Opaque-DM Doctrine

There is no hidden adjudication. When the D&D 3.5e rules are silent — a ladder that doesn't fit in a backpack, a wooden pole that can't support an ogre's weight — the system resolves the gap through pre-declared House Policies: bounded, template-instantiated, logged, and player-inspectable. It never invents rules, exercises discretion, or applies "common sense." If no policy covers a situation, the system fails closed and logs the gap for human review. New policy categories are created between releases by human decision, never during play by the system. Every outcome traces to either the written rules or an explicit, auditable House Policy. There is no third source.

---

*AIDM is an experimental research project. D&D 3.5 Edition is a product of Wizards of the Coast. This project contains no copyrighted game text in its source code; extracted rulebook content is for personal use only.*
