# MVP Definition: Session Zero to One Combat

**Author:** PO (Thunder) + PM (Opus) + Third-party review
**Date:** 2026-02-12
**Status:** APPROVED

---

## Purpose

Define the minimum viable product slice that proves the full thesis: trust + meaning + stability + physical table metaphor. This is the smallest thing that demonstrates every architectural layer working together.

---

## What the MVP Proves

1. **Truth is deterministic and replayable** — combat resolves mechanically, event log is inspectable
2. **Meaning is authored but bounded** — presentation semantics are world-frozen, narration respects them
3. **The boundary is visible** — the physical table metaphor makes Box/Lens/Spark separation tangible
4. **Prep is real** — the world compile step produces a frozen artifact set
5. **Content independence** — no copyrighted material in any shipped layer

---

## MVP Scope

### Session Zero

1. Player sits at table (Three.js browser interface)
2. Crystal ball glows, AI asks player's name (TTS)
3. Player speaks name (STT) or types it
4. Name appears on notebook cover
5. AI asks about notebook cover customization
6. Image generator creates cover art, applies to notebook
7. Character creation: AI guides conversationally, player rolls stats with physical dice tower
8. Character sheet populates as choices are made
9. World entry: AI describes the starting location

### The World (Minimum Artifact Set)

- **1 town** with a name, description, and basic map
- **1 shop interior** with pre-authored map layout
- **1 alley/street encounter area** with pre-authored map layout
- **3 NPC types:** shopkeeper, guard, bandit — each with:
  - Portrait (pre-generated)
  - Voice profile (pre-generated)
  - Doctrine profile (behavioral rules for INT/WIS band)
  - Stats (attribute block, HP, AC, attack bonus, etc.)
- **3 abilities** demonstrating different presentation semantics:
  - One projectile burst (fire-type: travel_then_detonate)
  - One melee maneuver (physical: instant impact)
  - One utility (buff/heal: self-targeted, aura)
- **Presentation semantics frozen** for all abilities
- **World-owned rulebook** generated from behavior + semantics
- **Bestiary silhouettes** for all 3 NPC types

### Play Sequence (The Proof)

1. Player enters town, talks to crystal ball about the location
2. Player enters shop, shopkeeper greets them (NPC portrait in crystal ball, distinct voice)
3. Shop menu slides across table as handout
4. Player can buy items (appear on character sheet, gold deducted)
5. **Player attacks shopkeeper** → hostile intent detected → combat state machine activates → initiative rolled with physical dice → scroll unrolls with shop interior map
6. Shopkeeper responds by doctrine (flee and alert guards, or fight back, depending on doctrine profile)
7. Guards arrive (doctrine-driven response to alert)
8. Player uses projectile burst ability → stencil overlay for targeting → voice confirmation → ability resolves → presentation semantics drive map animation (projectile travels, detonates, scorch marks on tiles)
9. Terrain may change (if ability destroys objects — tiles swap)
10. Combat resolves mechanically (attacks, damage, conditions, defeat)
11. After combat: loot handout slides across table
12. Bestiary updates: encountered NPCs go from silhouette to partial entry
13. Rulebook lookup: player asks "show me that fire ability" → crystal ball opens rulebook to the stable entry generated from behavior + semantics
14. Player can save images, notes, handouts to notebook
15. Session log complete, replayable, auditable

### What This Demonstrates

| Thesis Point | How MVP Proves It |
|-------------|-------------------|
| Deterministic truth | Combat resolves via Box, event log proves correctness |
| Replayability | Same seed + same actions = identical session |
| Presentation stability | Fire ability always described as projectile-then-detonate |
| Content independence | No copyrighted names, prose, or references |
| World-owned rulebook | Player can look up abilities, entries are stable |
| Physical table metaphor | Notebook, dice, crystal ball, scroll, handouts |
| Voice-first interaction | Primary input is speech, dice confirm rolls |
| No mercy doctrine | AoO triggers without warning, consequences are real |
| Progressive discovery | Bestiary entries evolve based on encounters |
| Asset rotation | Each NPC has unique portrait and voice |
| Fail-closed | If anything breaks, system logs gap, uses template fallback |

---

## What the MVP Does NOT Include

- Character progression / leveling (one session, no XP advancement needed)
- Multiple sessions / campaign persistence
- Multiplayer
- Complex world generation (hand-authored small world)
- Full spell system (3 abilities, not 53)
- Full feat system (basic combat only)
- NPC dialogue trees (conversational AI handles free-form)
- Exploration gameplay (combat focus)
- Music / ambient audio (voice only)
- Page tearing physics (simplified notebook)
- Dice reskinning (default dice)

---

## Acceptance Criteria

1. A player can complete the full Session Zero → One Combat loop without crashes
2. Combat resolution matches deterministic replay (same seed = same outcome)
3. Presentation semantics are consistent across multiple narrations of the same ability
4. The world-owned rulebook returns stable entries for all 3 abilities
5. Bestiary entries update based on encounter (silhouette → partial)
6. No copyrighted material appears anywhere in the player experience
7. Voice input successfully drives the primary interaction loop
8. Physical dice tower produces results that map to backend RNG
9. All mechanical state changes are recorded in the event log with provenance
10. Template fallback activates correctly when Spark is unavailable

---

*This MVP is not the product. It is the proof that the architecture works end-to-end. Everything after this is scaling the world, deepening the mechanics, and enriching the experience.*
