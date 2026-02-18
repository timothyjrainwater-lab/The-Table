# MEMO: Campaign Input Layer for Spark

**From:** Builder (BS Buddy session)
**Date:** 2026-02-14
**Lifecycle:** NEW
**Supersedes:** None
**Resolves:** No mechanism exists for feeding prepared campaign architecture to the Spark

---

## What

Session Zero currently covers rules, alignment, tone, and creative boundaries. It does not cover **campaign-specific world state** — the DM's prepared factions, NPCs, locations, plot hooks, environmental setups, and narrative constraints.

If a user wants to play a specific campaign (e.g., the Wizard Arena) inside the Table, the Spark needs structured access to that campaign's design material. Without this, the Spark improvises blind. With it, the Spark narrates inside a designed world.

---

## The Gap

The current Session Zero config answers:
- What rules are we using?
- What tone are we playing in?
- What boundaries exist?

It does not answer:
- What world are we playing in?
- Who are the NPCs and what do they know?
- What factions exist and what are their relationships?
- What locations exist and what are their properties?
- What plot hooks are active?
- What environmental/terrain setups should the engine expect?

---

## Proposed Addition

A **campaign manifest** layer within or alongside Session Zero that provides:

1. **World State Seed** — faction definitions, NPC profiles (name, role, secrets, disposition), location descriptions, inter-faction relationships
2. **Plot Hook Registry** — active narrative threads the Spark should be aware of and can reference or advance
3. **Environmental Presets** — biome definitions, terrain configurations, hazard tables that the engine's terrain system can consume
4. **Narrative Constraints** — things the Spark must not reveal prematurely (e.g., Mathyrian's true nature, the Soul Engine's function), gated behind player discovery

This is distinct from Session Zero's rules config. Session Zero defines *how the game works*. The campaign manifest defines *what world the game takes place in*.

---

## Why This Matters

The thesis document (`docs/THESIS_BUBBLE_REALM_AND_THE_TABLE.md`) identifies that the Wizard Arena campaign maps 1:1 to the engine's architecture. Playing the Wizard Arena *inside* the Table is a natural validation scenario and a compelling demo. But it requires the Spark to have structured access to the campaign's world state, not just rules and tone.

More broadly: any user who has a campaign idea — whether it's a published module, a homebrew world, or a narrative concept — needs a way to feed that into the system so the Spark can narrate within it rather than around it.

---

## Dependencies

- Session Zero config schema (needs campaign layer extension)
- Spark context window management (campaign material competes for context budget)
- LLM selection (MEMO_SPARK_LLM_SELECTION — context window size affects how much campaign material can be loaded)

---

## Recommendation

This should be scoped as a design spec before implementation. The format of the campaign manifest, how it's authored, how it's loaded into the Spark's context, and how it interacts with Session Zero all need PM-level decisions.

---

*End of memo.*
