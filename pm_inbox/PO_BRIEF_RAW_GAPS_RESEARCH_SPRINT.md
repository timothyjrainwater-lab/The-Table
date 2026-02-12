# PO → PM Brief: RAW Gaps Research Sprint

**From:** Thunder (PO)
**To:** Opus (PM)
**Date:** 2026-02-12
**Classification:** Strategic directive — research track authorization
**Priority:** HIGH — blocks future mechanical expansion quality

---

## Context

During architectural review of the NeedFact/WorldPatch authority protocol and the physical affordance discussion (inventory constraints, container capacity, external gear interactions), the PO identified a structural gap that extends beyond any single work order:

**D&D 3.5e RAW is intentionally incomplete.** It optimizes for playability with a human DM who fills gaps with judgment. Once the human DM is removed, every implicit physical assumption becomes an architectural liability — a point where the system must either silently guess (trust violation), let Spark invent an answer (authority violation), or halt without explanation (usability failure).

The No-Opaque-DM Doctrine has been added to the project manifesto:

> *Every outcome traces to either the written rules or an explicit, auditable House Policy. There is no third source.*

This brief authorizes and structures the research sprint needed to systematically identify and catalog these gaps.

---

## What Was Decided

### 1. Two-source authority model (locked)

Every mechanical decision in AIDM traces to exactly one of:

- **RAW** — Rules As Written, cited to specific page in PHB/DMG/MM
- **HOUSE_POLICY** — Explicit, versioned, deterministic, logged, player-inspectable

No third source exists. Spark cannot originate mechanical facts. Lens cannot exercise discretion. Box cannot silently assume.

### 2. Fail-closed on unpatched gaps (locked)

When Box encounters a physical question with no RAW rule and no declared House Policy:

- Action is refused with structured error
- `UNSPECIFIED_POLICY_HIT` is logged with full context
- The gap enters the policy backlog automatically
- The system never guesses, never continues with an assumption

This turns runtime into a discovery mechanism for missing policies.

### 3. Research sprint authorized (new)

A systematic mining operation across official WotC documents and community archives to identify RAW silences that can affect mechanical outcomes. Details below.

---

## Research Sprint: RQ-PHYS-001

**Title:** D&D 3.5e RAW Gap Extraction & House Policy Catalog

### Objective

Produce a structured catalog of every RAW silence that can reach Box — places where the rules are genuinely silent on a question that affects action legality, DCs, outcomes, or state. Each gap gets a disposition and, where appropriate, a proposed House Policy.

### The test for inclusion

A RAW gap is in scope if and only if it can:

- Change whether an action is legal
- Change a mechanical outcome (DC, damage, duration, etc.)
- Change reproducibility or auditability
- Cause Box to need a fact that doesn't exist

Gaps that only affect prose (Spark texture) are out of scope.

### Source mining priority

#### Phase 1: Official WotC sources (highest authority)

| Source | What it provides | Format |
|--------|-----------------|--------|
| D&D 3.5 FAQ PDF (v06/30/2008, final) | Every question WotC received often enough to answer officially. Each entry = confirmed RAW gap. | Structured Q&A |
| PHB/DMG/MM Errata PDFs | Every rule WotC corrected post-publication. Each correction = confirmed error. | Diff format |
| Rules Compendium (2007, Chris Sims) | WotC's own RAW vs. RAI reconciliation. Where it differs from core books, core books were wrong. | Book |
| Skip Williams "Rules of the Game" articles | Most detailed official rules analysis for 3.5e. Each article dissects ambiguities in a specific subsystem. | Article series, PDF compilation exists |

#### Phase 2: Community-curated compilations (pre-filtered, high density)

| Source | What it provides |
|--------|-----------------|
| GitP "Simple Q&A D&D 3.5 (by RAW)" — 31+ threads | Thousands of discrete RAW questions with community-vetted answers. Strictly by-the-text. |
| RPG Stack Exchange `dnd-3.5e+rules-as-written` sorted by votes | Discrete Q&A with vote counts indicating community salience. |
| EN World "What REALLY needed fixing?" thread | Community consensus on broken rules. |
| EN World "3.5 → 3.6" house rules compilation | Community-converged fixes. Where many tables independently house-ruled the same thing = strong evidence for a natural default. |
| GitP "Long-standing debates" thread | Curated list of arguments the community has never settled. These are genuinely ambiguous RAW. |

#### Phase 3: Exploit & stress-test analysis

| Source | What it provides |
|--------|-----------------|
| Brilliant Gameologists / MinMaxForum archive | Optimizer analysis that stress-tests rule interactions |
| Pathfinder 1e deltas from 3.5e | Largest single catalog of "what the community agreed was broken" — Paizo designed PF1e specifically to fix these |

#### Not in scope

- General Reddit threads (too scattered, mostly 5e)
- Unfiltered forum arguments (infinite noise)
- Full 778MB WotC community archive (useful content already preserved by GitP/EN World)

### Output schema

Each finding is captured as:

```
Finding ID:            RQ-PHYS-001-F-XXXX
Source:                [document, page/URL]
Category:              [COMBAT | EQUIPMENT | SPELLCASTING | MOVEMENT | SKILLS | ENVIRONMENT | ACTION_ECONOMY]
Question:              [The RAW question as posed]
RAW Status:            [SILENT | AMBIGUOUS | CONTRADICTORY]
Official Clarification: [FAQ/errata answer if one exists, or "None"]
Community Consensus:   [Brief summary of dominant community resolution, if any]
Mechanical Relevance:  [How this can reach Box — what decision depends on this]
Current AIDM Status:   [IMPLEMENTED | PARTIALLY_IMPLEMENTED | NOT_IMPLEMENTED | OUT_OF_TIER]

Disposition:           [RAW_SUFFICIENT | ERRATA_RESOLVED | NEEDS_HOUSE_POLICY | OUT_OF_SCOPE]

Proposed Policy:       [If NEEDS_HOUSE_POLICY — deterministic rule text]
Authority Tag:         [RAW | OFFICIAL_CLARIFICATION | HOUSE_POLICY]
```

### Disposition definitions

- **RAW_SUFFICIENT** — The rules actually answer this. People argue about the reading, but careful textual analysis resolves it. Tag as RAW with citation.
- **ERRATA_RESOLVED** — WotC published a correction. Apply it. Tag as OFFICIAL_CLARIFICATION.
- **NEEDS_HOUSE_POLICY** — RAW is genuinely silent or contradictory. Requires an explicit, deterministic policy. Tag as HOUSE_POLICY.
- **OUT_OF_SCOPE** — Mechanically irrelevant to current tier, or cannot reach Box under current implementation. Log for future reference, do not policy-patch now.

### Categories expected to produce the most findings

Based on community dispute frequency:

1. **Grappling** — multi-step resolution, size interactions, casting while grappled (already partially implemented in maneuver_resolver.py)
2. **Attacks of Opportunity** — trigger list ambiguities, "threatened squares" edge cases (already implemented in aoo.py)
3. **Equipment storage & carrying** — container capacity, encumbrance interaction, readiness states (not implemented)
4. **Polymorph / Shapechange** — ability transfer rules, subschool revision (not implemented, Tier 2+)
5. **Stacking rules** — typed vs. untyped bonuses, same source, enhancement stacking (partially implemented)
6. **Action economy** — swift/immediate action overlap with older "free action spell" rules (partially implemented)
7. **Cover & concealment** — partial cover calculation, soft cover from creatures (partially implemented)
8. **Mounted combat** — lance rules, charge while mounted, mount vs. rider actions (implemented)
9. **Iterative attacks** — TWF + natural attacks, haste interaction (partially implemented)
10. **Trip/Bull Rush/Disarm** — size modifier edge cases, improved feat chains (implemented)

### Deliverables

1. **Findings catalog** — Structured findings per the schema above, organized by category
2. **Policy draft document** — For all NEEDS_HOUSE_POLICY findings, proposed deterministic rules with explicit HOUSE_POLICY provenance
3. **Schema extension proposal** — Changes needed to `ObjectDefault`, `SourceTier`, and `entity_fields.py` to support the RAW/HOUSE_POLICY distinction
4. **Priority matrix** — Findings ranked by (a) mechanical impact and (b) proximity to currently-implemented systems

### What this sprint does NOT produce

- Implementation code (research only)
- Changes to existing resolvers
- New game mechanics
- Simulationist physics beyond what can reach Box
- Unbounded "exhaustive catalog of all physical reality" — scope is gated by the mechanical relevance test

---

## Relationship to existing work

| Existing component | Impact |
|-------------------|--------|
| Policy Default Library (AD-003) | Extended with RAW vs. HOUSE_POLICY per-field provenance |
| SourceTier enum (lens_index.py) | Needs POLICY_DEFAULT tier distinct from CANONICAL |
| Fact Acquisition (WO-008) | Findings inform which facts need acquisition policies |
| NeedFact/WorldPatch protocol (AD-001) | Policy defaults become a resolver priority in the authority chain |
| Combat resolvers (attack, spell, maneuver, AoO) | Findings may identify gaps in existing implementations |
| Equipment/inventory system | Findings define requirements for future inventory work orders |

---

## Sequencing guidance

This research sprint runs **in parallel** with, not blocking, current development work. Existing work orders (WO-FIX-003, Lens-Spark context orchestration, etc.) continue uninterrupted.

The sprint produces a catalog and policy drafts. Implementation of those policies is a separate set of work orders dispatched after the research is reviewed and approved.

**Start with:** The official FAQ PDF. It's structured, authoritative, and every entry is a confirmed gap. That alone will validate the schema and process before scaling to community sources.

---

## PO expectations

- Findings are research artifacts, not commitments. The PO reviews and approves policies before they become binding.
- The HOUSE_POLICY tag is honest — no finding should be dressed up as RAW when it isn't.
- The fail-closed `UNSPECIFIED_POLICY_HIT` mechanism is implemented as infrastructure regardless of how many policies the sprint produces. The system must catch gaps it doesn't know about yet.
- The No-Opaque-DM Doctrine is now part of the manifesto. All work must comply.

---

*This brief authorizes RQ-PHYS-001. PM has discretion on scheduling, agent assignment, and phase execution order.*

— Thunder
