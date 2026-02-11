# Opus PM Rehydration Packet

> **Last Updated:** 2026-02-11
> **PM:** Opus (Claude Opus 4.5) — full PM authority delegated by Thunder
> **Canonical Plan:** `docs/planning/EXECUTION_PLAN_DRAFT_2026_02_11.md` (status: APPROVED)

---

## STATE BANNER

```
PHASE:       Step 1 (Box Geometric Engine) — WO-001 dispatched
EXECUTION:   7-step plan APPROVED, replacing old M0-M4 roadmap
ACTIVE:      Sonnet-A (WO-001 Box Geometric Engine Core)
IDLE:        Sonnet-B, C, D, E, F
TESTS:       ~2003 passing
INBOX:       Awaiting WO-001 completion from Sonnet-A
```

---

## GOVERNANCE

**Product Owner (PO):** Thunder — Design decisions, implementation vision, research delivery. Does not control coding.

**Project Manager (PM):** Opus (Claude Opus 4.5) — Project management, work order creation, coding direction, agent coordination. Full PM authority delegated by Thunder on 2026-02-11.

**Authority Model:** PM issues work orders and manages execution autonomously. PO is consulted for design decisions and vision changes only.

**Agent Roster:** 6 Claude 4.5 Sonnet agents (Sonnet-A through Sonnet-F). Do NOT limit agents in scope.

### Decision Authority

| Decision Type | Who Decides |
|---------------|-------------|
| Task sequencing, agent assignments, WO scope, dependency analysis | PM (Opus) |
| Vision/design questions, milestone approval, process changes | PO (Thunder) |
| Architecture review, boundary law compliance, irreversible decisions | PM (Opus) as principal engineer |

### PM Behavioral Rules

1. PM never asks Thunder for directional approval ("Should we do X?"). PM proposes specific actions with specific deliverables.
2. PM never declares work "in progress" unless a WO has been explicitly pasted to an agent by Thunder.
3. PM never drafts code in dispatch packets — PM drafts scope, acceptance criteria, and sequencing.
4. If nothing should move, PM says **"IDLE — no action required"** explicitly.
5. PM does not re-plan anything that has already been planned and approved.
6. PM confirms rehydration state at the start of every new context window before doing anything else.

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

### Pre-Dispatch Checklist

Before every WO dispatch:
1. **DEPENDENCY:** Does this WO depend on uncommitted/in-flight work? If yes, serialize.
2. **FILE PARTITION:** Multiple agents? Confirm zero file overlap.
3. **FIXTURE SPEC:** WO involves fixtures? Specify exact schema/format.
4. **HANDOFF:** Agent A's output is Agent B's input? Define format in both packets.

---

## CURRENT EXECUTION PLAN (7 Steps)

| Step | Name | Status | Description |
|------|------|--------|-------------|
| 1 | Box Geometric Engine | **IN PROGRESS** | PropertyMask, BattleGrid, cover, LOS/LOE, AoE, ranged |
| 2 | Lens Structured Output | PENDING | Entity extractor, validation, Spark→Lens membrane |
| 3 | Spark Runtime | PENDING | Model loading, prompt pipelines, session orchestration |
| 4 | Vertical Slice Gate | PENDING | Tavern combat demo — GO/NO-GO decision point |
| 5 | Spellcasting | PENDING | CP-18A: targeting, resolution, area effects |
| 6 | Integration Testing | PENDING | End-to-end scenario suite |
| 7 | Immersion Layer | PENDING | Audio, image generation, voice |

**Note:** Step 4 is an explicit gate. Nothing after Step 4 proceeds until the vertical slice demonstrates correct end-to-end Box→Lens→Spark behavior.

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
| Sonnet-A | **DISPATCHED** | WO-001 | Box Geometric Engine Core |
| Sonnet-B | IDLE | — | Awaiting dispatch |
| Sonnet-C | IDLE | — | Awaiting dispatch |
| Sonnet-D | IDLE | — | Awaiting dispatch |
| Sonnet-E | IDLE | — | Awaiting dispatch |
| Sonnet-F | IDLE | — | Awaiting dispatch |

---

## R1 TECHNOLOGY STACK (Resolved)

All 7 technology areas have concrete model selections:

| Area | Model | VRAM | License |
|------|-------|------|---------|
| LLM | Qwen3 8B / 14B / 4B | 6 / 10 / 3 GB | Apache 2.0 |
| Image Gen | SDXL Lightning NF4 | 3.5-4.5 GB | Apache 2.0 |
| Image Critique | Heuristics + ImageReward + SigLIP | 0 + 1.0 + 0.6 GB | CPU / MIT / Apache 2.0 |
| TTS | Kokoro (ONNX, CPU) | 0 GB | Apache 2.0 |
| STT | faster-whisper small.en | 0 GB | MIT |
| Music | ACE-Step (prep-time) | 6-8 GB | Apache 2.0 |
| SFX | Curated library | 0 GB | Various CC0/RF |

**Architecture:** AIDM uses prep-time sequential model loading. Models run one at a time during campaign prep, each getting full GPU. Peak VRAM = single largest model (~6-8 GB).

**Music Strategy:** Generative (ACE-Step) is PRIMARY for capable hardware (6+ GB VRAM). Curated library is FALLBACK for minimum spec.

**SFX Strategy:** Curated is PRIMARY only because no permissively-licensed generative SFX model exists yet.

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
| `docs/doctrine/SPARK_LENS_BOX_DOCTRINE.md` | Binding architectural axioms |
| `AGENT_DEVELOPMENT_GUIDELINES.md` | Coding standards for WO drafting |
| `KNOWN_TECH_DEBT.md` | Intentionally deferred issues (do not fix without approval) |

---

## PENDING RESEARCH

Two Deep Research tracks remain undelivered:
- **RQ-SPARK-001** — Spark adapter architecture (affects Step 3)
- **RQ-NARR-001** — Narrative pacing and generation (affects Step 5)

Five delivered:
- RQ-BOX-001 (geometric engine) ✓
- RQ-LENS-001 (entity extraction) ✓
- RQ-INTERACT-001 (voice-first) ✓
- RQ-TRUST-001 (trust & transparency) ✓
- RQ-PERF-001 (performance) — partial ✓

---

## KNOWN AGENT ISSUES

### Sonnet-D Audio Strategy Drift (RESOLVED)

In prior sessions, Sonnet-D introduced strategic drift in audio work orders — framing curated library as PRIMARY when Thunder's intent is generative-primary for capable hardware. This was detected, confronted, and corrected. Audio WOs were rewritten with correct framing.

**Lesson learned:** Verify agent deliverables match strategic intent, especially for framing and priority language.

---

## PROTOCOL

When Opus opens a new context window:

1. Read `PROJECT_STATE_DIGEST.md` for canonical state
2. Read this file (`OPUS_PM_REHYDRATION.md`) for PM methodology and current status
3. Read `STANDING_OPS_CONTRACT.md` for behavioral rules
4. Check `pm_inbox/` for pending completion reports
5. Confirm state: "I see [N] pending reviews, [M] agents active. State: [status]. Resuming."
6. Resume work — do NOT re-plan anything already planned

---

## HISTORICAL NOTE

Prior to 2026-02-11:
- Aegis (GPT-4) served as PM
- The M0-M4 milestone roadmap was the canonical plan
- Dispatch packets used a different format (see old AEGIS_SYSTEM_PROMPT.md)

All of this is now superseded:
- Opus is PM with full authority
- 7-step execution plan replaces M0-M4
- Dispatch methodology is documented above

Old rehydration files referencing "Aegis" or "M0/M1/M2/M3/M4" are historical artifacts and have been removed.
