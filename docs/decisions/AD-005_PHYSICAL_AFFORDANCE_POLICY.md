# AD-005: Physical Affordance Policy

**Status:** RATIFIED
**Date:** 2026-02-12
**Author:** Opus (PM), directed by Thunder (PO)
**Depends on:** AD-001 (Authority Resolution), AD-003 (Self-Sufficiency Resolution)
**Implements:** PO requirement for physical realism in equipment, containers, and storage

---

## Problem Statement

D&D 3.5e defines equipment by weight (PHB Table 7-8, p.128) and carrying capacity by Strength (PHB Table 9-1, p.162). However, the rules are deliberately silent on:

- Container volumes (backpack capacity in cubic feet)
- Item size categories for storage (does a 10-foot pole fit in a backpack?)
- Storage location (in-pack vs. externally strapped vs. in-hand)
- Retrieval times from containers beyond the basic "draw a weapon" rules
- Physical interference from externally carried gear

These missing facts create a gap: actions that depend on physical reasonableness (e.g., "I put the grappling hook in my backpack," "I tumble through the window") cannot be resolved deterministically because the system lacks the physical facts needed to make the determination.

If the system hand-waves these questions, immersion suffers. If Spark invents the physics, determinism is violated. A policy is needed.

---

## Decision

### Principle: Declared Physical Facts

When RAW is silent on a physical property that affects whether an action is legal or how an outcome is described, the system resolves the gap through **declared physical facts** — finite, versioned, deterministic policies that are explicitly labeled as either:

- **RAW** — sourced from the rulebooks with citation
- **HOUSE_POLICY** — declared by the system, not in RAW, but required for simulation integrity

Both types are:
- Stored in the Policy Default Library (AD-003 infrastructure)
- Immutable once declared for a session
- Auditable (provenance tag, version, source citation or "HOUSE_POLICY" marker)
- Deterministic (same input → same output)

### Four-Layer Architecture

Physical affordance concerns decompose into four layers with distinct authority:

| Layer | Concern | Authority | Provenance | Example |
|-------|---------|-----------|------------|---------|
| 1. Weight/Encumbrance | Total carried weight vs STR thresholds | Box | RAW (PHB p.162) | Heavy load → speed -10ft, max Dex +1, -6 check penalty |
| 2. Container Policies | Does item X fit in container Y? | Box | HOUSE_POLICY | Backpack: items ≤ Medium size, ≤ 40 lb capacity |
| 3. Gear Affordances for Narration | What is visible/accessible on the character? | Lens → Spark | DERIVED | visible_gear: ["grappling_hook_external"] |
| 4. Physical Complication Policies | Can external gear cause mechanical consequences? | Box | HOUSE_POLICY | External bulky gear → circumstance penalty on Tumble |

**Layers are independent and incrementally buildable.** Layer 1 is pure RAW. Layer 2 extends the PDL. Layer 3 feeds the NarrativeBrief. Layer 4 is optional and highest risk.

### Authority Rules

1. **If it changes the game state, Box decides it.** Weight penalties, action legality, complication effects — all Box-resolved.

2. **If it changes the prose, Spark decides it.** "Your hook catches the window frame" is narration flavor — Spark chooses the phrasing from Lens-provided affordances.

3. **Lens decides what Spark is allowed to reference.** Spark receives `visible_gear_tags`, `nearby_geometry`, `failure_style_suggestions` — never raw game state.

4. **Spark MUST NOT originate consequences.** If Spark narrates "your hook snags and you stumble," the stumble must already be a Box-decided outcome. Spark is coloring the outcome, not creating it.

5. **HOUSE_POLICY rules are declared before they fire.** A complication policy cannot be invented mid-session by any layer. It must exist in the Policy Default Library at session start.

### Item Property Schema

Every equipment item in the catalog carries:

| Field | Type | Source | Purpose |
|-------|------|--------|---------|
| item_id | str | System | Unique identifier |
| name | str | RAW | Display name |
| weight_lb | float | RAW (PHB Table 7-8) | Encumbrance calculation |
| size_category | str | HOUSE_POLICY | Tiny/Small/Medium/Large/Long — container fit check |
| bulk_category | str | HOUSE_POLICY | compact/standard/bulky — storage behavior |
| container_capacity_lb | float? | HOUSE_POLICY | If container: max weight capacity |
| container_max_size | str? | HOUSE_POLICY | If container: largest item size accepted |
| storage_slots | int? | HOUSE_POLICY | If container: max number of items |
| stow_location | str | HOUSE_POLICY | in_pack / external / belt / hand |
| draw_action | str | RAW / HOUSE_POLICY | free / move / standard — action to access |
| provenance | str | System | RAW or HOUSE_POLICY |

### Storage Location Rules

| Location | Access Cost | Visible to Others | Snag Risk | Source |
|----------|-------------|-------------------|-----------|--------|
| in_hand | free action | yes | no | RAW (PHB p.142) |
| belt | move action | yes | no | RAW (PHB p.142) |
| external | move action | yes | possible (Layer 4) | HOUSE_POLICY |
| in_pack | full-round action | no | no | HOUSE_POLICY |

### Encumbrance Tiers (RAW — PHB Table 9-2, p.162)

| Load | Speed | Max Dex | Check Penalty | Run |
|------|-------|---------|---------------|-----|
| Light | normal | — | 0 | ×4 |
| Medium | -10 ft (if base ≥ 30 ft), -5 ft (if base 20 ft) | +3 | -3 | ×4 |
| Heavy | -10 ft (if base ≥ 30 ft), -5 ft (if base 20 ft) | +1 | -6 | ×3 |

### What This Does NOT Cover

- Magic item properties (handled by spell/item system, not physical affordances)
- Creature inventory (NPCs/monsters — future extension)
- Encumbrance exceptions (Bags of Holding, Handy Haversack — require magic item system)
- Automated packing optimization (system enforces constraints, player decides arrangement)

---

## Implementation Work Orders

| WO | Description | Layer | Priority |
|----|-------------|-------|----------|
| WO-053 | Equipment Item Catalog — extend PDL with 30+ adventuring gear items | 1, 2 | HIGH |
| WO-054 | Inventory + Encumbrance System — entity fields, STR-based capacity, load penalties | 1 | HIGH |
| WO-055 | Container Policies + Storage Location — containment rules, draw action costs | 2 | MEDIUM |
| WO-056 | Gear Affordance Tags — visible_gear in NarrativeBrief for Spark context | 3 | MEDIUM |

Layer 4 (Physical Complication Policies) is explicitly deferred. It requires Layers 1-3 to be stable first and carries the highest risk of over-engineering.

---

## Relationship to Existing Architecture

- **AD-001 (Authority Resolution):** Physical affordance facts follow the same NeedFact pattern. Missing facts trigger a halt-and-resolve, not LLM invention.
- **AD-003 (Self-Sufficiency):** Equipment catalog extends the Policy Default Library. Same JSON-backed, typed, frozen-dataclass pattern.
- **Seam boundaries:** Weight/container policies are Box. Gear affordances are Lens→Spark. The authority boundary is unchanged.

---

## PO Direction

The PO identified the grappling-hook-on-bag scenario as the motivating example:

> "If a character stashes his grappling hook on his bag and does a tumble check and fails, having that element of the grappling hook on the side of the bag catching the window is a vital tiny detail that really enhances the experience."

This policy enables that scenario at Layer 3 (narration texture) immediately, and at Layer 4 (mechanical consequences) when the complication policy is defined. The system never hand-waves and never lets Spark invent physics.
