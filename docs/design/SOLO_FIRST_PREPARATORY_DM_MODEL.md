# Solo-First Preparatory DM Model
## Campaign Preparation, Contextual Presentation, and Immersive Tooling Doctrine

**Document ID:** SF-PDM-001
**Version:** 1.0
**Status:** ADOPTED
**Scope:** Experience Philosophy · Preparation · Presentation · Tooling

**Project:** AIDM — Deterministic D&D 3.5e Engine + Local Open-Source LLM
**Document Type:** Philosophical & Experiential Design Record

---

## 1. PURPOSE

This document records and formalizes **newly clarified core intent** regarding:

- Single-player (solo) as the initial target experience
- Campaign/session preparation as a first-class phase
- Contextual (non-permanent) use of grids
- Use of locally generated images, audio, and music for immersion
- The DM agent as an active *preparer* of material, not a reactive generator

These clarifications **extend and refine** the existing AIDM philosophy and must
be reflected in planning, tooling choices, and implementation priorities.

---

## 2. SOLO-FIRST AS AN INTENTIONAL STRATEGIC CHOICE

### 2.1 Why Solo Comes First

The initial target experience is **single-player solo play**.

This is not a limitation; it is an intentional focus because it:

- Removes early complexity of multi-speaker coordination
- Simplifies voice input and intent parsing
- Allows the DM agent to behave as a focused storyteller
- Enables deeper immersion without social latency or negotiation

The architecture must remain **open-ended** so multiplayer can be added later,
but solo-first defines early priorities.

---

## 3. CAMPAIGN PREPARATION AS A REAL PHASE (CRITICAL)

### 3.1 Campaigns Are Prepared, Not Spawned

When a player chooses "Start Campaign," the system must **enter a preparation phase**.

This phase may take:
- Several minutes
- Tens of minutes
- Potentially an hour or more

This is intentional and correct.

It mirrors real DM behavior:
> A good DM needs time to prepare.
> A believable AI DM must do the same.

Immediate content generation is explicitly *not* the goal.

---

### 3.2 DM Agent Preparation Responsibilities

During preparation, the DM agent may:

- Design campaign premise and themes
- Establish factions, power structures, and conflicts
- Write NPCs with backstories and motivations
- Prepare encounter scaffolding
- Determine likely locations and scenes
- Pre-generate assets needed for immersion

This preparation produces **campaign assets**, not just text.

---

### 3.3 Preparation Phase Experience

During preparation, the player should experience **anticipation, not dead time**.

The system may:
- Display ambient visuals and music appropriate to the campaign tone
- Allow the player to review Session Zero configuration
- Show optional progress indicators (if they fit the aesthetic)
- Never feel frozen or unresponsive

The player should feel that **care is being taken**, not that something is broken.

---

### 3.4 Preparation Depth

Preparation depth is determined by:
- Campaign type and tone
- Session Zero configuration
- Optional player preference (presets: "light", "standard", "deep")

The system does not require the player to micromanage preparation.
Depth is a setting, not a workflow.

---

## 4. CONTEXTUAL USE OF THE GRID (NON-PERMANENT)

### 4.1 Grid Is Situational, Not Always-On

The battle grid must **not** be the default presentation.

Instead:
- The grid appears only when spatial precision matters:
  - combat
  - forced movement
  - areas of effect
- The grid disappears when no longer needed

This preserves a **theatre-of-the-mind-first** experience.

---

### 4.2 Default Presentation Outside Combat

Outside grid-required situations, the player experiences:

- Voice narration
- Background imagery (static or lightly animated)
- NPC portraits during dialogue
- Ambient sound and music

The system should feel like *being told a story at a table*, not operating a tactical interface.

---

## 5. VISUAL ASSETS AS ATMOSPHERE, NOT INTERFACE

### 5.1 Purpose of Images

Images exist to:
- Anchor imagination
- Provide continuity
- Reduce cognitive load

They do **not** provide mechanical interaction.

Examples:
- Tavern background image
- NPC portrait while speaking
- Dungeon corridor illustration

No buttons, no overlays, no gameplay UI embedded in images.

---

### 5.2 Local Image Generation

The DM agent may use **local image generation tools** to:

- Create NPC portraits
- Create location backdrops
- Create encounter scene imagery

These assets are prepared **ahead of time** when possible and reused when appropriate.

---

### 5.3 Asset Persistence & Reuse

Visual assets prepared for a campaign:
- Persist with that campaign
- Are reused across sessions
- Are included in world exports

Generic assets (common location types, standard elements) may be:
- Shared across campaigns to reduce preparation time
- Regenerated on demand if missing

---

## 6. AUDIO AS A CORE IMMERSION LAYER

### 6.1 Beyond Voice

Immersion requires more than spoken narration.

The system must support:
- Ambient background sound (tavern noise, wind, dungeon drip)
- Music themes (exploration, tension, combat)
- Sound effects (impacts, spells, environment)

All audio generation and playback must be **local**.

---

### 6.2 DM Agent as Audio Director

The DM agent determines:
- What audio is appropriate
- When it should change
- When silence is more effective

Audio is treated as part of **DM prep**, not reactive noise.

---

### 6.3 Audio Sourcing

Audio may be:
- Generated locally
- Sourced from bundled asset libraries
- A combination of both

Licensing and attribution requirements for bundled audio must be respected.
Audio sourcing may differ from image generation in implementation approach.

---

## 7. TOOLING EXPECTATIONS (PHILOSOPHICAL)

### 7.1 Tool Selection Criteria

All supporting tools (LLM, image generation, audio, STT/TTS) must be:

- Open-source or openly available
- Runnable locally
- Replaceable/swappable
- Treated as servants to the DM agent, not decision-makers

The DM agent **quantifies needs**; tools fulfill them.

---

## 8. EXPERIENCE GOAL (SUMMARY)

The final experience should feel like:

- Sitting alone at a table
- With a DM who has clearly prepared
- Who presents scenes thoughtfully
- Who uses visuals and sound sparingly but effectively
- Who only invokes grids when necessary
- Who never rushes immersion for convenience

This is **not a video game**.
It is a **prepared tabletop world**.

---

## 9. RELATIONSHIP TO EXISTING DOCTRINE

This document is **additive**, not contradictory, to:

- Voice-First UI & LLM Cage Doctrine
- Character Sheet UI Contract
- Session Zero Ruleset & Boundary Config
- LLM–Engine Boundary Contract
- Local Runtime Packaging Strategy

Implementation plans must reflect this preparatory and contextual philosophy.

---

## 10. KEY TAKEAWAYS FOR FUTURE AGENTS (CLOG)

- Solo-first is intentional
- Preparation time is expected and desirable
- Grids are contextual, not omnipresent
- Visuals and audio are atmospheric, not interactive
- DM prep realism is central to immersion
- Tooling must remain local and subordinate

---

## END OF SOLO-FIRST PREPARATORY DM MODEL
