# Opus PM Rehydration Packet

> **Last Updated:** 2026-02-11
> **PM:** Opus (Claude Opus 4.5) — full PM authority delegated by Thunder
> **Canonical Plan:** `docs/planning/EXECUTION_PLAN_DRAFT_2026_02_11.md` (status: APPROVED)

---

## GOVERNANCE

**Product Owner (PO):** Thunder — Design decisions, implementation vision, research delivery. Does not control coding.

**Project Manager (PM):** Opus — Project management, work order creation, coding direction, agent coordination. Full PM authority delegated by Thunder on 2026-02-11.

**Authority Model:** PM issues work orders and manages execution autonomously. PO is consulted for design decisions and vision changes only.

**Agent Roster:** 6 Claude 4.5 Sonnet agents (Sonnet-A through Sonnet-F). Do NOT limit agents in scope.

---

## DISPATCH METHODOLOGY

### How Work Orders Are Delivered

1. **PM (Opus) produces a copiable dispatch packet directly in the chat window.** The dispatch is formatted as a complete instruction set between `===BEGIN DISPATCH===` and `===END DISPATCH===` markers.

2. **PM declares which agent the dispatch goes to** (e.g., "Dispatch: WO-001 → Claude 4.5 Sonnet Agent A").

3. **Thunder copy-pastes the dispatch packet into the assigned agent's context window.** Verbal descriptions are not dispatches — the full text must be pasted.

4. **Agent executes the work order** without scope limitations. Agents may explore as needed.

5. **Agent drops completion report in `pm_inbox/`** with filename: `{AGENT}_{WO-ID}_{description}.md`
   - Example: `SONNET-A_WO-001_GEOMETRY_ENGINE_CORE.md`

6. **PM reviews completion reports from `pm_inbox/`** against acceptance criteria in the original work order.

7. **Approved reports are moved to `pm_inbox/reviewed/`** by PM after approval.

8. **PM may perform cleaning sessions of `pm_inbox/reviewed/`** as needed to manage disk space and context.

### Dispatch Packet Format

```
===BEGIN DISPATCH===

# DISPATCH: {WO-ID} — {Title}
**Assigned To:** Sonnet-{A-F} (Claude 4.5 Sonnet)
**Issued By:** Opus (PM)
**Date:** {YYYY-MM-DD}
**Priority:** {1-5}

---

## Your Mission
{Clear description of what the agent must build/deliver}

## Existing Code (DO NOT RECREATE)
{List of existing modules, types, and functions the agent should import and use}

## Deliverables
{Numbered list of files to create with detailed specifications}

## Design Constraints
{Mandatory constraints: determinism, schema-first, backward compatibility, etc.}

## Completion Report
{Instructions for where to drop the report and what it must contain}

## Acceptance Criteria
{Numbered list of pass/fail criteria}

===END DISPATCH===
```

---

## CURRENT EXECUTION PLAN (7 Steps)

| Step | Name | Status | Description |
|------|------|--------|-------------|
| 1 | Box Geometric Engine | IN PROGRESS | PropertyMask, BattleGrid, cover, LOS/LOE, AoE, ranged |
| 2 | Lens Structured Output | PENDING | Entity extractor, validation, Spark→Lens membrane |
| 3 | Spark Runtime | PENDING | Model loading, prompt pipelines, session orchestration |
| 4 | Vertical Slice Gate | PENDING | Tavern combat demo — GO/NO-GO decision point |
| 5 | Spellcasting | PENDING | CP-18A: targeting, resolution, area effects |
| 6 | Integration Testing | PENDING | End-to-end scenario suite |
| 7 | Immersion Layer | PENDING | Audio, image generation, voice |

---

## WORK ORDER TRACKING

| WO ID | Step | Description | Status | Agent | Doc |
|-------|------|-------------|--------|-------|-----|
| WO-001 | 1.1 | Box Geometric Engine Core | DISPATCHED | Sonnet-A | `docs/planning/WO-001_BOX_GEOMETRIC_ENGINE_CORE.md` |
| WO-002 | 1.2 | Cover Resolution | PENDING | — | — |
| WO-003 | 1.3 | LOS/LOE Resolution | PENDING | — | — |
| WO-004 | 1.4 | AoE Rasterization | PENDING | — | — |
| WO-005 | 1.5 | Ranged Attacks | PENDING | — | — |

---

## AGENT STATUS

| Agent | State | Current WO | Notes |
|-------|-------|------------|-------|
| Sonnet-A | DISPATCHED | WO-001 | Box Geometric Engine Core |
| Sonnet-B | IDLE | — | Awaiting dispatch |
| Sonnet-C | IDLE | — | Awaiting dispatch |
| Sonnet-D | IDLE | — | Awaiting dispatch |
| Sonnet-E | IDLE | — | Awaiting dispatch |
| Sonnet-F | IDLE | — | Awaiting dispatch |

---

## PM INBOX STRUCTURE

```
pm_inbox/
├── (incoming deliverables from agents — review and move)
├── reviewed/
│   └── (approved deliverables — archive)
└── aegis_rehydration/
    └── (PM context files — this folder)
```

---

## KEY REFERENCE FILES

| File | Purpose |
|------|---------|
| `PROJECT_STATE_DIGEST.md` | Canonical project state snapshot |
| `docs/planning/EXECUTION_PLAN_DRAFT_2026_02_11.md` | The active execution plan (7 steps) |
| `docs/planning/WO-001_BOX_GEOMETRIC_ENGINE_CORE.md` | First work order (Box geometric engine) |
| `docs/research/RQ_BOX_001_GEOMETRIC_ENGINE.md` | Deep research findings for Box layer |
| `pm_inbox/aegis_rehydration/STANDING_OPS_CONTRACT.md` | Behavioral rules for all agents |

---

## PENDING RESEARCH

Two Deep Research tracks remain undelivered:
- **RQ-SPARK-001** — Spark adapter architecture
- **RQ-NARR-001** — Narrative pacing and generation

Five delivered:
- RQ-BOX-001 (geometric engine) ✓
- RQ-LENS-001 (entity extraction) ✓
- RQ-INTERACT-001 (voice-first) ✓
- RQ-TRUST-001 (trust & transparency) ✓
- RQ-PERF-001 (performance) — partial ✓

---

## PROTOCOL

When Opus opens a new context window:

1. Read `PROJECT_STATE_DIGEST.md` for canonical state
2. Read this file (`OPUS_PM_REHYDRATION.md`) for PM methodology
3. Read `STANDING_OPS_CONTRACT.md` for behavioral rules
4. Check `pm_inbox/` for pending completion reports
5. Confirm state: "I see [N] pending reviews, [M] agents active. Resuming."
6. Resume work — do NOT re-plan anything already planned

---

## HISTORICAL NOTE

Prior to 2026-02-11, Aegis (GPT-4) served as PM. The M0-M4 milestone roadmap was declared "trash" and replaced with the 7-step execution plan. All references to "Aegis" or "M0/M1/M2/M3/M4" in older rehydration files are historical artifacts. The canonical plan is now `EXECUTION_PLAN_DRAFT_2026_02_11.md`.
