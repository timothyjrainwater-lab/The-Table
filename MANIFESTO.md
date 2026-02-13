# The Honest Referee

*A manifesto for trustworthy AI-driven tabletop play*

---

## What We're Building

We're building a tabletop storytelling system that behaves like the best kind of Game Master: **creative in voice, strict in truth, and accountable in every outcome**.

It begins the way real play begins:

A player sits down.
There is no encyclopedia to memorize.
There is a **notebook** and a **conversation**.

From that first moment, the system exists to do one thing well:

**Help humans create meaning together through constrained imagination — without surrendering truth to an opaque machine.**

---

## Why This Exists

Tabletop roleplaying endures for a simple reason:
**humans love telling stories together.**

Not as passive entertainment. As a lived, social act — imagination under rules, creativity under constraints, consequence under choice.

We're extracting the core pattern that works:

**A fair referee + a shared world + free human choice = stories that matter.**

---

## The Central Promise

Most AI systems today are impressive and unreliable. They produce *output*, not *truth*. They mimic coherence, but they don't guarantee it. They feel powerful — until they drift.

This product makes a different promise:

### **The system will never be a hidden decision-maker.**

It will never "decide what seems reasonable" and quietly alter reality.

It will do exactly two things:

1. **Execute rules deterministically** (the reality engine)
2. **Generate meaning creatively** (the narration engine)

And it will never confuse the two.

---

## The Three-Layer System

### 1) The Referee (Deterministic Authority)

The referee is a deterministic engine that:

- resolves actions using explicit procedures
- rolls dice through a reproducible RNG
- updates game state through auditable events
- produces an inspectable trace of *what happened and why*

It has one inviolable property:

> **Same initial state + same inputs = same outcomes. Always.**

That enables replay, verification, debugging, and dispute resolution without "trust me" authority.

No language model is involved in any mechanical decision. Ever.

### 2) The Boundary (Truth Firewall)

Between truth and narration sits a boundary layer that:

- **sanitizes** raw mechanics into narrative-safe facts
- prevents "internal machinery" from becoming story-authority
- enforces **one-way flow**: truth -> brief -> narration, never backward

The storyteller never queries the referee.
The storyteller never decides mechanics.
The storyteller never "fills in" missing mechanical truth.

### 3) The Storyteller (Meaning Generator)

The storyteller is a generative model that:

- turns verified outcomes into evocative prose
- varies voice, tone, and pacing
- makes scenes *feel* real without asserting what is real

It has one inviolable property:

> **Zero mechanical authority.**

If the storyteller fails, the system degrades gracefully: truth remains intact.

---

## The Deeper Shift: Three Kinds of Description

The system separates *three kinds of "description"*:

### Behavior (Immutable Procedures)

What an ability *does* mathematically. Range, area, damage, saves, conditions. Deterministic.

### Presentation Semantics (World-Authored, Frozen)

What an ability *behaves like* in this world. Delivery mode, staging, visual and audio character. Not prose — structured semantic tags authored during world creation and then frozen. A fire projectile always travels and detonates. A healing aura always radiates from the caster. This is what makes the world *learnable*.

### Narration (Ephemeral Prose)

How a moment *feels*. Free-form, varied, atmospheric. Constrained by behavior and presentation semantics, but never identical twice.

Narration can vary.
Presentation semantics **must not drift** within a world.
That stability is authored during world creation, not improvised during play.

---

## The Creation Stack: How Meaning Freezes

The system is built around a boot order that mirrors real tabletop play:

### 0a — Engine Substrate (Immutable)

- Resolution procedures
- Event sourcing / replay
- Determinism infrastructure

### 0b — Character Substrate (Pre-world grammar)

- Attribute schema
- Dice methods
- Character sheet structure
- Progression grammar

This exists before any world exists.

### 1 — World Model (Authored, expensive, frozen)

This is where names and meaning emerge.

Before a world exists, abilities and skills exist as **IDs + math**.
After the world is authored, those IDs bind to:

- names
- taxonomy
- presentation semantics
- rulebook language for that world

The **rulebook belongs here**: authored once, then frozen.

### 2 — Campaign / Region (Scoped play within a world)

- Factions, regional context, starting conditions
- Localized content bindings consistent with the world

### 3 — Storyline (Character-driven arcs)

- PCs, arcs, locations, NPC networks

### 4 — Session (Ephemeral play)

- Narration, rolls, logs, consequences

This is why "come back tomorrow" is not a failure mode — it's the honest equivalent of "the GM needs prep time."

---

## No Opaque DM Doctrine

This is load-bearing.

Every outcome that affects game state must trace to one of exactly two sources:

1. **Rules As Written** (deterministic resolvers)
2. **House Policy** (pre-declared templates, logged, frozen, inspectable)

There is no third source.
There is no "the system decided."
There is no hidden discretion.

If a situation cannot be resolved deterministically from existing rules + declared policies:

**the system fails closed and logs exactly what is missing.**
No guesses. No silent patches.

---

## House Policy, Done Honestly

Real tables evolve rules. That's not a flaw — it's life.

But we refuse the typical failure mode: *unlogged discretion that destroys auditability.*

So we treat house rules as a governed mechanism:

- **finite trigger families** (deterministic checks, not AI judgment)
- **bounded template outputs** (allow / deny / cost / DC, etc.)
- **immutable policy ledger** (player-inspectable, replay-stable)
- **offline evolution loop** (humans decide new families; runtime never invents them)

The system can adapt — **but only inside declared boundaries.**

---

## Content Independence

This is not legal hygiene. It's creative power.

Mechanics are **procedures**.
Names are **skin**.
Meaning is **emergent**.

We model content as:

- **IDs + math + interaction tags** (ship)
- **world vocabulary + presentation semantics** (generated and frozen per world)
- **narration** (generated per moment)

This yields a system where:

- the same procedural truth can be expressed as fantasy, sci-fi, horror, myth, or anything else
- players aren't trapped inside one vocabulary
- the "rulebook" becomes a **world-authored lexicon**: consistent within that world, inspectable, and stable across sessions

---

## The Physical Table

The interface is a recreation of sitting at a real tabletop. Not a simulation — a **truthful instrument**.

Every interaction maps to a physical object at a real table:

- **Notebook**: your memory, your drawings, your saved images, your discovery log
- **Character sheet**: system-managed truth about your character, displayed as paper
- **Rulebook**: the world's own reference — authored at world compile, frozen, opened by asking the DM
- **Dice**: physical objects you pick up, drop in a tower, and watch land
- **Crystal ball**: the DM's presence — it speaks, it shows NPC faces, it answers your questions
- **Battle map**: a magical scroll that unrolls for combat, flat and 2D
- **Handouts**: papers the DM slides across the table — menus, loot lists, letters

You talk to the crystal ball. You roll dice in the tower. You draw in your notebook. You never click a menu.

When in doubt about any interface decision:
**what would it be like at an actual real-world tabletop?**

---

## What We Refuse to Build

- A chatbot that roleplays authority
- A system that trades truth for vibes
- A black box that can't explain itself
- A monetized attention engine wearing a fantasy mask
- A referee that silently invents rules
- A system that warns you before you make mistakes (no mercy, no hand-holding)
- A UI that looks like software instead of a table

If the system cannot remain honest under stress, it does not ship.

---

## Local-First, Owner-First

This product should feel like a *tool you own*, not a service that owns you.

- Runs locally as much as possible
- Avoids dependency on remote monetization loops
- No ads, no engagement traps
- No "infinite updates" that rewrite the ground beneath your feet
- Your worlds and stories are yours

We are not optimizing for addiction.
We are optimizing for **agency**.

---

## The Outcome We Want

A device on the table that gives people what they keep trying to find:

- a fair referee
- a living world
- a space to imagine together
- a structured way to grow
- and a reason to keep telling stories

Not because it replaces humans.

Because it **amplifies what humans do best** —
and makes it easier for more people to do it, consistently, safely, and with integrity.

---

## The Core Belief

> **The most human thing we do is share meaning through stories.**
> If we're going to use powerful generative tools, we must bind them to honesty.

This system doesn't try to replace imagination.
It tries to *protect* it — by making truth stable, inspectable, and fair, so creativity can be free.

---

*The Table is an experimental research project. It uses procedural mechanics extracted from publicly available game systems as scaffolding for a content-independent truthful play engine. No copyrighted game text is included in the shipped product.*
