# AIDM Master Requirement Register

**Document ID:** MRR-001
**Version:** 1.1.0
**Date:** 2026-02-11
**Status:** ACTIVE (Amended per Whiteboard Session 002)
**Authority:** Consolidation of all GPT-collaborative design documents
**Produced By:** Opus (Acting PM) — line-by-line extraction from 7 source documents
**Amended:** 2026-02-11 — Product Owner corrections applied (see WHITEBOARD_SESSION_002_DECISIONS.md)

---

## Overview

This register consolidates **425 requirements** extracted from the 7 GPT-collaborative design documents (the "golden eggs") produced by Thunder + Aegis during the foundational design phase. Each requirement has been tagged with binding status, category, and roadmap mapping.

### Source Documents

| Doc ID | Document | Requirements | Binding |
|--------|----------|-------------|---------|
| CDR | Chronological Design Record — Core Insight to Research | 61 | 52 |
| GPL | Generative Presentation & Localization Architecture | 67 | 67 |
| MUI | Minimal UI, Text Interaction, Visual Accessibility | 41 | 34 |
| PA | Player Artifacts — Notebook, Handbook, Knowledge Tome | 45 | 33 |
| PM | Player Modeling & Adaptive DM Behavior | 52 | 47 |
| SPA | Secondary Pass Audit — Fine-detail Capture | 86 | 79 |
| TML | Transparent Mechanics Output & Teaching Ledger | 54 | 48 |
| **TOTAL** | | **406** | **360** |

---

## Consolidated Gap Analysis

### Product Owner Corrections (Whiteboard Session 002, 2026-02-11)

The following gaps from the original v1.0.0 analysis were **INVALIDATED** by Thunder during the whiteboarding session. These represent GPT overengineering artifacts, not actual product requirements:

| Gap ID | Status | Reason |
|--------|--------|--------|
| **GAP-02** | **INVALIDATED** | Skin Packs are not real. GPT hallucination. The canonical ID / presentation separation is inherent in the architecture — the DM can call anything whatever it wants. No "Skin Pack" system needed. |
| **GAP-03** | **INVALIDATED** | Import/Extensibility system is not real. Holy Doctrine: "Nothing from the outside needs to go in ever at all for any reason." No imports, no packs, no external content. |
| **GAP-04** | **INVALIDATED** | Localization infrastructure (Language Packs) is not real. GPT overengineering. The DM can rename anything because the engine uses canonical IDs. This is native to the architecture. |
| **GAP-05** | **RESOLVED** | Accessibility is built into the table metaphor. Mouse wheel zooms table objects ("the book gets bigger in your face"). No font settings panel or accessibility control panel needed. |
| **GAP-08** | **RESOLVED** | Knowledge homes already exist. Tome = authoritative reference (spells, monsters, rules). Notebook = player memory (session notes, quest details). D&D solved this 50 years ago. |
| **GAP-11** | **INVALIDATED** | Alias conflict detection was prerequisite for Language Packs, which don't exist. |

### REMAINING Unmapped Requirements by Domain

The following gaps remain valid and require roadmap assignments:

| Gap ID | Domain | Source Reqs | Severity | Description |
|--------|--------|-------------|----------|-------------|
| **GAP-01** | Player Modeling System | REQ-PM-001 through PM-052 (36 unmapped) | **CRITICAL** | Now understood as a **Lens subsystem**. Player model (5 dimensions), inference engine, confidence/decay, LLM prompt parameterization. Lives in the Lens, affects presentation only. See `SPARK_LENS_BOX_ARCHITECTURE.md` Section 5.2. |
| **GAP-06** | Teaching Ledger / Mechanics Window | REQ-TML-001–054 (13 unmapped) | **MEDIUM** | Teaching/passive-education requirements, accessibility of the ledger, player modeling integration. Ledger itself maps to M1.5 but teaching function has no task. |
| **GAP-07** | Clickable Inline Text | REQ-MUI-018–024, PA-028 | **MEDIUM** | Clickable spell/item/condition references in narration text. No M-task covers building this affordance layer. |
| **GAP-09** | Onboarding UX Flows | REQ-SPA-039–054 | **MEDIUM** | DM-first onboarding, persona demo in 30s, dice customization, character creation as conversation, prep-time handoff. Now partially addressed by first interaction spec ("Hi, my name is [DM]. What's yours?") but detailed sub-tasks still needed. |
| **GAP-10** | Daily Launch Interaction | REQ-SPA-059–064 | **MEDIUM** | DM greeting on every launch, recap offer, sheet change discussion, anti-omniscience tone. Now addressed by Session Continuity subsystem in Lens (see `SPARK_LENS_BOX_ARCHITECTURE.md` Section 5.6) but implementation tasks needed. |
| **GAP-12** | Meta-Intent Recognition | REQ-PM-035 | **MEDIUM** | Player override commands ("Explain more", "Skip this") require a meta-intent layer distinct from gameplay intents. |
| **GAP-13** | Terminology Locking | REQ-GPL-022, 044, 053, SPA-082 | **MEDIUM** | Per-session term lock to prevent synonym drift. Valid requirement — the DM should use consistent terms for the same thing within a session. |
| **GAP-14** | Anti-Gamification Constraint | REQ-PA-004, PA-042 | **LOW** | Explicit non-gamification of artifacts. Implied but not stated in amendment. |

### Updated Unmapped Count

**Original analysis:** ~95 unmapped binding requirements
**After corrections:** ~55 unmapped binding requirements (40 requirements invalidated or resolved by Product Owner corrections)

The largest remaining cluster is **Player Modeling** (~36 reqs), which is now understood to be a Lens subsystem and has architectural home in `SPARK_LENS_BOX_ARCHITECTURE.md`.

---

## Category Distribution (All Documents)

| Category | CDR | GPL | MUI | PA | PM | SPA | TML | Total |
|----------|-----|-----|-----|----|----|-----|-----|-------|
| ARCHITECTURE | 17 | 21 | 1 | 2 | 11 | 14 | 3 | **69** |
| CONSTRAINT | 13 | 24 | 8 | 4 | 7 | 12 | 9 | **77** |
| PRINCIPLE | 8 | 4 | 8 | 3 | 6 | 5 | 5 | **39** |
| UX | 0 | 2 | 6 | 3 | 5 | 16 | 5 | **37** |
| MECHANIC | 0 | 0 | 2 | 3 | 10 | 0 | 7 | **22** |
| INTERACTION | 3 | 5 | 4 | 2 | 3 | 5 | 5 | **27** |
| ACCESSIBILITY | 2 | 0 | 6 | 3 | 1 | 4 | 5 | **21** |
| AUDIO | 7 | 2 | 0 | 0 | 0 | 5 | 0 | **14** |
| VISUAL | 5 | 2 | 2 | 0 | 0 | 8 | 0 | **17** |
| NARRATIVE | 0 | 0 | 0 | 0 | 1 | 4 | 0 | **5** |
| PERSISTENCE | 1 | 3 | 0 | 2 | 2 | 4 | 2 | **14** |
| SECURITY | 0 | 1 | 0 | 1 | 0 | 0 | 0 | **2** |
| **TOTAL** | **56** | **64** | **37** | **23** | **46** | **77** | **41** | **344** |

*Note: Some requirements count toward INFORMATIONAL status and are excluded from category totals.*

---

## Binding Status Summary

| Status | CDR | GPL | MUI | PA | PM | SPA | TML | Total |
|--------|-----|-----|-----|----|----|-----|-----|-------|
| BINDING | 52 | 67 | 34 | 33 | 47 | 79 | 48 | **360** |
| ASPIRATIONAL | 1 | 0 | 4 | 0 | 1 | 2 | 3 | **11** |
| INFORMATIONAL | 8 | 0 | 1 | 3 | 4 | 5 | 0 | **21** |
| SUPERSEDED | 0 | 0 | 0 | 9 | 0 | 0 | 0 | **9** |

---

## Roadmap Coverage Heat Map

**NOTE:** The current roadmap (AIDM_EXECUTION_ROADMAP_V3.md) has been declared "trash" by the Product Owner and is scheduled for complete rewrite. The heat map below reflects the V3 roadmap but is retained for historical reference only.

| Roadmap Area | Fully Mapped | Partially Mapped | UNMAPPED |
|-------------|-------------|-----------------|----------|
| M1: Solo Vertical Slice | ~85 reqs | ~20 reqs | ~15 reqs |
| M2: Campaign Prep | ~30 reqs | ~10 reqs | ~5 reqs |
| M3: Immersion Layer | ~60 reqs | ~25 reqs | ~25 reqs |
| M4: Offline Packaging | ~8 reqs | ~5 reqs | ~2 reqs |
| **Cross-cutting** | ~10 reqs | ~5 reqs | **~55 reqs** (was ~95, reduced by PO corrections) |

**After Product Owner corrections:**
1. **Player Modeling** (~36 reqs) — now has architectural home in the Lens (see SPARK_LENS_BOX_ARCHITECTURE.md) but needs implementation tasks
2. ~~Import/Extensibility (~17 reqs) — INVALIDATED~~ (Holy Doctrine: nothing from outside goes in)
3. ~~Accessibility (~21 reqs) — RESOLVED~~ (table metaphor zoom handles this natively)
4. ~~Localization (~5 reqs) — INVALIDATED~~ (canonical ID architecture provides this natively)

---

## Recommended Roadmap Amendments

**NOTE:** These recommendations pre-date the Product Owner's directive for a complete roadmap rewrite. They are retained for reference but the new roadmap will be built from scratch using the Spark/Lens/Box architecture as the organizing principle.

### Surviving Recommendations (not invalidated by PO corrections)

| Task | Description | Source Reqs | Status |
|------|-------------|-------------|--------|
| M1.18 | Implement Teaching Ledger (Mechanics Window) UI | REQ-TML-001–054 | Still valid |
| M1.20 | Implement meta-intent recognition layer | REQ-PM-035, SPA-032 | Still valid |
| M2.14 | Implement Player Profile schema and persistence (Lens subsystem) | REQ-PM-007–010, PM-037, PM-044 | Still valid — now Lens component |
| M2.15 | Implement onboarding UX flows (DM-first, first-prompt, character creation) | REQ-SPA-039–054 | Still valid — expanded by first-prompt spec |
| M2.16 | Implement daily launch interaction (greeting, recap, session continuity) | REQ-SPA-059–064 | Still valid — now Lens Session Continuity |
| M3.18 | Notebook with drawing pad + radial wheel | (existing — preserved) | Expanded: cover personalization, parchment inserts |
| M3.19 | Tome viewer with Vault adapter (Rulebook section) | (existing — preserved) | Expanded: parchment inserts |
| M3.20 | Tome bestiary section with progressive discovery | (existing — preserved) | Unchanged |
| M3.24 | Implement Player Modeling inference engine (Lens subsystem) | REQ-PM-006, 023–027 | Still valid — now Lens component |
| M3.25 | Implement adaptive DM output parameterization | REQ-PM-028–032, 039, 046 | Still valid |

### INVALIDATED Recommendations (removed by PO corrections)

| Task | Description | Reason Invalidated |
|------|-------------|-------------------|
| ~~M1.19~~ | ~~Implement accessibility settings~~ | Accessibility = zoom table objects. No settings panel. |
| ~~M3.16~~ | ~~Formalize Skin Pack schema~~ | Skin Packs don't exist. Holy Doctrine. |
| ~~M3.17~~ | ~~Implement import system~~ | Nothing from outside goes in. Holy Doctrine. |
| ~~M3.21~~ | ~~Implement terminology locking system~~ | Remains valid as concept but implementation is Lens-native, not separate system |
| ~~M3.22~~ | ~~Implement localization template engine~~ | Language Packs don't exist. Canonical ID architecture provides this. |
| ~~M3.23~~ | ~~Implement alias-based intent resolution~~ | Related to Language Packs — invalidated. |
| ~~ACC-01~~ | ~~Accessibility audit + screen-reader compat~~ | Accessibility = zoom. Not a cross-cutting audit task. |
| ~~ACC-02~~ | ~~WCAG color accessibility compliance~~ | Resolved by table metaphor zoom mechanic. |

---

## Amendment Gaps (TABLE_METAPHOR_AND_PLAYER_ARTIFACTS.md)

**STATUS:** TABLE_METAPHOR spec has been updated to v1.1.0 and approved by Product Owner (Whiteboard Session 002).

The following items from the original Player Artifacts spec were assessed:

| Gap | Original Req | Description | Resolution |
|-----|-------------|-------------|------------|
| GAP-PA-01 | REQ-PA-031 | Spell effect tracking in Tome | **RESOLVED** — Tome accepts parchment inserts; spell effects live on character sheet (Box-sourced) |
| GAP-PA-02 | REQ-PA-032 | Known locations registry | **RESOLVED** — Notebook is for player memory ("you wrote it down or you didn't"); Lens Campaign Memory Index tracks locations for the DM |
| GAP-PA-03 | REQ-PA-033 | Factions/NPCs encountered registry | **RESOLVED** — Same as GAP-PA-02; Notebook + Lens Campaign Memory Index |
| GAP-PA-04 | REQ-PA-034 | XP milestone narrative log | **RESOLVED** — Character sheet (Box-sourced XP), Notebook (player's personal record) |
| GAP-PA-05 | REQ-PA-008 | DM can organize Notebook into sections | **DEFERRED** — Notebook is freeform; DM can prompt note-taking but organization is player's choice |
| GAP-PA-06 | REQ-PA-019 | Screen-reader compat for Tome + Sheet | **RESOLVED** — Accessibility = zoom table objects; text-only fallback mode exists for Notebook |
| GAP-PA-07 | REQ-PA-020 | Font/contrast adjust for Tome + Sheet | **RESOLVED** — Mouse wheel zoom on any table object; no separate settings needed |

---

## Individual Extraction Registers

The complete line-by-line extraction for each document is available in the PM session transcript. Each register contains:
- Sequential requirement IDs (REQ-CDR-###, REQ-GPL-###, etc.)
- Source line references
- Category classification
- Binding status assessment
- Roadmap mapping
- Cross-reference notes
- Gap identification

### Document Extraction Summaries

1. **CDR (61 reqs):** Established the mechanics/presentation separation, prep-first generation, voice priority (TTS > STT), indexed memory architecture, hardware baseline (Steam Survey), and research phase gating. ~~4 UNMAPPED (language packs, alias tables)~~ — language pack requirements INVALIDATED by Product Owner (Holy Doctrine: nothing from outside goes in; canonical IDs handle this natively).

2. **GPL (67 reqs):** Formalized canonical ID contract, terminology locking. ALL 67 are BINDING as extracted, but **~24 requirements related to Skin Packs, Language Packs, Import systems, and Alias Conflict Detection have been INVALIDATED by Product Owner** (Whiteboard Session 002). These were GPT overengineering artifacts, not Thunder's actual intent. The canonical ID / presentation separation principle is valid and inherent in the architecture; the import infrastructure built on top of it is not. Remaining valid GPL requirements: canonical ID contract, terminology drift prevention (Lens-native), and presentation layer separation.

3. **MUI (41 reqs):** Locked minimal UI principle, text-as-fallback, clickable inline affordances, font/color accessibility, progressive discovery UX, anti-dashboard constraint. 18 UNMAPPED (accessibility tasks, clickable text, UI theming).

4. **PA (45 reqs):** Original 3-artifact spec now superseded by TABLE_METAPHOR amendment. 9 SUPERSEDED, 14 gaps identified in amendment (5 HIGH: spell tracking, locations, NPCs, accessibility).

5. **PM (52 reqs):** 5-dimension player profiling (experience, pacing, explanation depth, tone, modality), confidence-weighted inference with decay, LLM prompt parameterization. **36 of 48 binding reqs were UNMAPPED** — now understood to be **Lens subsystem components** (see `SPARK_LENS_BOX_ARCHITECTURE.md` Section 5.2: Player Model). The Player Modeling system lives in the Lens, affects presentation only (never mechanics), and is injected into Spark context windows. Has architectural home but needs implementation tasks in the roadmap rewrite.

6. **SPA (86 reqs):** Fine-detail audit covering all domains. Major clusters: onboarding UX (16 reqs), image critique (8 reqs), indexed memory (6 reqs), accessibility (4 reqs), daily launch (6 reqs). Most map to existing M-tasks but add acceptance criteria.

7. **TML (54 reqs):** Teaching Ledger with trust/fairness/accessibility triple mandate. Dice transparency format (type + raw + modifiers + result), passive education through visible mechanics, DM-queryable entries. 13 UNMAPPED (accessibility, teaching function).

---

## Governance

- This register is a **living document** — updated as requirements are implemented, amended, or deprecated
- Requirements marked BINDING must be implemented or formally amended to change status
- Requirements marked UNMAPPED must receive roadmap assignments before their milestone begins
- Requirements marked INVALIDATED have been struck by the Product Owner and will not be implemented
- The TABLE_METAPHOR amendment gaps (GAP-PA-01 through GAP-PA-07) have been resolved (see above)
- The current roadmap is scheduled for complete rewrite — all milestone mappings are provisional

### New Specifications (Written 2026-02-11)

The following specifications were produced from Whiteboard Session 002 and provide architectural homes for many previously unmapped requirements:

| Specification | Addresses |
|--------------|-----------|
| `SPARK_LENS_BOX_ARCHITECTURE.md` | Player Modeling (GAP-01), Session Continuity (GAP-10), Context Assembly, Environmental Data Index |
| `TABLE_SURFACE_UI_SPECIFICATION.md` | Onboarding (GAP-09), all table object interactions, DM presence, accessibility model |
| `BATTLE_MAP_AND_ENVIRONMENTAL_PHYSICS.md` | Battle map mechanics, cover geometry, environmental objects, AoE, movement |
| `WHITEBOARD_SESSION_002_DECISIONS.md` | Raw decision log, all Product Owner corrections, invalidations |

---

## END OF MASTER REQUIREMENT REGISTER
