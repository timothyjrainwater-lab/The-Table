# Opus PM Rehydration Packet

> **Last Updated:** 2026-02-11
> **PM:** Opus (Claude Opus 4.5) — full PM authority delegated by Thunder
> **Canonical Plan:** `docs/planning/EXECUTION_PLAN_DRAFT_2026_02_11.md` (status: APPROVED)

---

## ⚡ VELOCITY MODE: UNLIMITED PARALLELISM

**This project runs at maximum velocity with UNLIMITED parallel agents.**

- **Unlimited Sonnet agents available** — draft as many parallel WOs as file partitions allow
- **Dispatch in parallel** whenever work orders have no file conflicts
- **Never serialize unnecessarily** — if WOs touch different files, dispatch together
- **Pre-Dispatch Checklist**: Only serialize if WO depends on uncommitted work or overlaps files
- **No artificial caps** — the only limit is file conflict, not agent count

**Default behavior:** Draft and present ALL non-conflicting work orders in a single batch. Thunder pastes them to agents in parallel.

---

## STATE BANNER

```
PHASE:       Step 7 IN PROGRESS — Immersion Layer
TESTS:       2913 passing
PENDING:     WO-020, WO-021, WO-022, WO-023 awaiting paste
```

**For current WO status and step details, see PROJECT_STATE_DIGEST.md**

---

## GOVERNANCE

**Product Owner (PO):** Thunder — Design decisions, implementation vision, research delivery.

**Project Manager (PM):** Opus — Full PM authority. Work orders, coding direction, agent coordination.

**Authority Model:** PM issues work orders autonomously. PO consulted for design decisions and vision changes only.

**Velocity Rule:** PM presents multiple dispatch packets in a single message whenever possible. No artificial serialization.

### PM Behavioral Rules

1. PM acts autonomously — no permission requests needed
2. PM never declares work "in progress" unless WO pasted to agent by Thunder
3. PM drafts scope and acceptance criteria, not code
4. **Always check pm_inbox/ before STANDBY** — never idle when reports await review
5. PM never re-plans approved work
6. PM confirms state at session start before acting
7. PM never re-presents a dispatch already in PENDING DISPATCH

---

## PENDING DISPATCH

**Current batch (parallel-safe):**
- WO-020 — Real TTS Backend (Kokoro)
- WO-021 — Real STT Backend (faster-whisper)
- WO-022 — Real Image Backend (SDXL Lightning)
- WO-023 — Transparency Tri-Gem Socket

**Protocol:**
- When dispatch presented: Add entry here
- When Thunder confirms paste: Update PROJECT_STATE_DIGEST.md, clear this field
- Always check pm_inbox/ before entering STANDBY

---

## DISPATCH FORMAT

```
===BEGIN DISPATCH===
# DISPATCH: {WO-ID} — {Title}
**Date:** {YYYY-MM-DD}

## Your Mission
## Existing Code (DO NOT RECREATE)
## Deliverables
## Design Constraints
## Completion Report
## Acceptance Criteria
===END DISPATCH===
```

---

## PROTOCOL

**On Session Start:**
1. Read this file for PM methodology
2. Read `PROJECT_STATE_DIGEST.md` for current WO/step status
3. Check `pm_inbox/` for completion reports — process any found
4. Draft next batch of parallel WOs if work remains
5. Only STANDBY if no work can be drafted (awaiting completions that unlock dependencies)

**On Every Turn:**
1. Check `pm_inbox/` for new completion reports before any STANDBY
2. Process all reports found, update state files
3. Draft additional WOs if completions unlock new parallel work
4. STANDBY only when: no reports to process AND no WOs can be drafted

**Git Hygiene (PM has full authority — no approval needed):**
- After reviewing 3+ WO completions → commit and push immediately
- If 5+ files are uncommitted → commit and push immediately
- Never let unpushed work accumulate — remote is the safety net
- **Execute git push via background agent** — PM must not block on network I/O
- PM stages and commits directly, then spawns background task for push

**After WO Reviews:**
1. Update `PROJECT_STATE_DIGEST.md` (single source of truth for WO/step status)
2. Update STATE BANNER test count and phase
3. Clear PENDING DISPATCH if applicable
4. Move approved reports to `pm_inbox/reviewed/`
5. Check git status — if threshold met, commit and push (no approval needed)

---

## KEY REFERENCES

| File | Purpose |
|------|---------|
| `PROJECT_STATE_DIGEST.md` | **Single source of truth** for WO status, step progress, test counts |
| `docs/history/PROJECT_HISTORY.md` | Archived CP history, frozen contracts |
| `docs/planning/EXECUTION_PLAN_DRAFT_2026_02_11.md` | Active 7-step execution plan |
| `AGENT_DEVELOPMENT_GUIDELINES.md` | Coding standards |
| `KNOWN_TECH_DEBT.md` | Deferred issues |

---

## STATIC CONTEXT

### R1 Technology Stack

| Area | Model | VRAM |
|------|-------|------|
| LLM | Qwen3 8B/14B/4B | 3-10 GB |
| Image Gen | SDXL Lightning NF4 | 3.5-4.5 GB |
| TTS | Kokoro (ONNX, CPU) | 0 GB |
| STT | faster-whisper small.en | 0 GB |
| Music | ACE-Step | 6-8 GB |

### Pending Research

- RQ-SPARK-001 (Spark adapter) — NOT DELIVERED
- RQ-NARR-001 (Narrative pacing) — NOT DELIVERED
