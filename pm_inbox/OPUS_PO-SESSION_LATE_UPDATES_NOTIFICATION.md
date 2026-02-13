# PO Session Late Updates — RQ-PRODUCT-001 Refinements

**Agent:** Opus
**Source:** PO design session (2026-02-12) — late-session refinements
**Date:** 2026-02-12
**Status:** Notification — supplements the Research Review Packet
**Related:** `pm_inbox/OPUS_PO-SESSION_RESEARCH_REVIEW_PACKET.md`

---

## Summary

After the initial research review packet was filed, the PO continued the design
session with three significant refinements to RQ-PRODUCT-001 (Content
Independence Architecture). These are already incorporated into the spec and
the review packet, but are flagged here so the PM is aware of the late-session
changes.

**No new artifacts were created.** All changes are revisions to:
- `docs/specs/RQ-PRODUCT-001_CONTENT_INDEPENDENCE_ARCHITECTURE.md`
- `pm_inbox/OPUS_PO-SESSION_RESEARCH_REVIEW_PACKET.md` (Section 3.5 updated)

---

## Change 1: Layered World Authority Model Added (New Section 8)

RQ-PRODUCT-001 now contains a full **Layered World Authority Model** defining
a 5-level creation stack:

| Level | What It Owns |
|-------|-------------|
| 0 — Substrate | Math, resolvers, IDs (immutable) |
| 1 — World | Rulebook, cosmology, species, monster catalog, ability names, **all regions/countries/cities/governments/geography** |
| 2 — Campaign | **Selects a region** of the world; adds local NPCs, plot hooks |
| 3 — Storyline | Characters, plot arcs, adventures |
| 4 — Session | Narration, dice rolls, event logs (ephemeral) |

**Key PO decisions captured:**
- The **rulebook freezes at World level** (Level 1), not Campaign level.
  The world's flavor (space/undersea/fantasy) determines the rulebook's flavor.
  All campaigns in the same world share the same rulebook, monster catalog,
  spell list, and ability names.
- **All geography is world-level.** World generation produces all regions,
  countries, cities, and governments. Campaigns select which region to play in
  — they do not create new geography.
- **World compile is expensive** (the PO's phrase: "come back in hours").
  Campaign creation is cheap (the world already exists, just pick a region).
- **Governmental baseline is world-level.** The world defines what types of
  governance exist and where. Campaigns inherit this; storylines operate within
  it.

This section also includes: cross-campaign familiarity rules, controlled
novelty hierarchy (cost of new session/storyline/campaign/world), replay
provenance tracing, and mapping back to the three-layer content model.

**PM impact:** The creation stack constrains the future campaign compile
pipeline. Codex generation, rulebook generation, and map generation all happen
at world creation, not campaign creation. Review as part of action item #11.

---

## Change 2: Creature Three-Layer Model Added (Section 4 Expansion)

The PO identified that the three-layer content model (mechanical / behavioral /
narrative) applies to **creatures** the same way it applies to abilities. This
was added to RQ-PRODUCT-001 Section 4 as a new subsection.

**Layer 1 — Mechanical Definition (Skeleton):**
Pure stat block. CR, type, size, hit dice, AC, speed, attacks, saves, senses.
YAML-formatted, same across all worlds. Uncopyrightable math.

**Layer 2 — Behavioral Contract (Muscle):**
Combat doctrine, engagement range, opening tactic, retreat threshold, morale,
pack behavior, lair behavior, movement pattern, sensory profile. Static across
all worlds. Constrains Spark's narration of creature behavior.

**Layer 3 — Narrative Skin (World Level):**
What the creature looks like, what it's called, its lore. Different per world.
Generated at world creation, frozen with the world.

| World | CREATURE_014 Name | Appearance | Habitat |
|-------|------------------|------------|---------|
| High Fantasy | Wyvern | Leathery wings, barbed tail | Mountain crags |
| Sci-Fi | Phase Raptor | Shimmering scales, plasma tail | Asteroid nests |
| Undersea | Abyssal Eel | Bioluminescent, venomous spines | Deep trenches |
| Horror | Nightwing | Membranous wings, necrotic sting | Abandoned cathedrals |

Same CR 3. Same 22 HP. Same ambush-then-dive behavior. Different skin.

**IP analysis:** The D&D Monster Manual mixes statistics (uncopyrightable),
combat behavior (functional specification, uncopyrightable), and
appearance/name/lore (creative expression, copyrightable). The content pack
ships layers 1 and 2. Layer 3 is generated fresh per world. Zero copyrightable
text in the shipped product.

**PM impact:** The creature model reinforces that the v1 content pack scope
(Section 4 table) includes ~20 creatures, each requiring mechanical definition
+ behavioral contract. No additional PM action beyond action item #11.

---

## Change 3: RQ-PRODUCT-001 Now Has 11 Sections and 8 Success Criteria

The spec grew from the initial filing. Current section map:

1. Thesis
2. The Three-Layer Content Model
3. The Provenance Firewall
4. Content Pack Schema (v1 Draft) — **now includes Creature Three-Layer Model**
5. Extraction Surface Audit
6. The Behavioral Contract as Narration Guardrail
7. Multi-Skin Support
8. **Layered World Authority Model (Creation Stack)** — NEW
9. Sequencing
10. Success Criteria — **2 new criteria added** (creation stack, world compile)
11. Relationship to Other Work — **2 new relationship entries**

**New success criteria:**
- Layered World Authority Model defined — creation stack with freeze points and
  stability guarantees documented. Rulebook freezes at world level.
- World compile process specified — when the rulebook is generated, what
  freezes, what remains variable, provenance tracing per layer.

---

## PM Action

No new action items beyond those already in the review packet (items #11 and
#12). This notification ensures the PM is aware that RQ-PRODUCT-001 is
substantially more detailed than when initially filed — the creation stack and
creature model were PO-directed additions during the same session.

The review packet (Section 3.5 and the creation stack table) has been updated
to reflect all of these changes.
