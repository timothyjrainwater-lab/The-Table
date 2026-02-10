# Aegis Rehydration Folder

**Purpose:** Drop ALL files in this folder into a new GPT context window to fully rehydrate Aegis (the PM). This eliminates the "planned but never dispatched" failure mode caused by context window shifts.

## How To Use

1. Open a new GPT context window
2. Drag-drop every `.md` file from this folder into the conversation
3. Say: "Warm resume. Assume continuity. Read all files."
4. Aegis should respond with state banner confirmation and next action

## What's In Here

### Posture Files (read first — these anchor behavior)

| File | Purpose |
|------|---------|
| `SESSION_BOOTSTRAP.md` | Resume-from-sleep posture: state banner, authority map, current scope, out-of-scope |
| `STANDING_OPS_CONTRACT.md` | 20 behavioral rules: how PM/Opus/Sonnet/Thunder act (not what they build) |
| `AEGIS_REHYDRATION_STATE.md` | Pipeline status: active WOs, agent states, blockers, post-delivery flow |

### Critical Context (read early — these define current technical direction)

| File | Source | Purpose |
|------|--------|---------|
| `R1_TECHNOLOGY_STACK_SUMMARY.md` | Original (this folder) | **R1 model selections for all 7 technology areas** — executive summary |
| `OPUS_NOTES_FOR_AEGIS.md` | `pm_inbox/OPUS_NOTES_FOR_AEGIS.md` | Opus observations, audit findings, flags for PM |

### Reference Files (read as needed — these provide facts)

| File | Source | Purpose |
|------|--------|---------|
| `PROJECT_STATE_DIGEST.md` | `PROJECT_STATE_DIGEST.md` (repo root) | Full project state — locked systems, module inventory, test counts |
| `KNOWN_TECH_DEBT.md` | `KNOWN_TECH_DEBT.md` (repo root) | Intentionally deferred items — prevents re-scheduling closed work |
| `AIDM_EXECUTION_ROADMAP_V3.md` | `docs/AIDM_EXECUTION_ROADMAP_V3.md` | Canonical milestone roadmap (M0-M4) |
| `AGENT_DEVELOPMENT_GUIDELINES.md` | `AGENT_DEVELOPMENT_GUIDELINES.md` (repo root) | Coding standards, boundary laws, pitfall checklist |

## Reading Order (Recommended for Aegis)

1. `SESSION_BOOTSTRAP.md` — posture + state banner (fastest re-anchor)
2. `AEGIS_REHYDRATION_STATE.md` — pipeline details, WO status, blockers
3. `STANDING_OPS_CONTRACT.md` — behavioral rules (prevents tone drift)
4. `R1_TECHNOLOGY_STACK_SUMMARY.md` — **NEW** — R1 model selections executive summary (critical context)
5. `OPUS_NOTES_FOR_AEGIS.md` — recent observations from principal engineer
6. `PROJECT_STATE_DIGEST.md` — reference as needed (large file, full inventory)
7. `KNOWN_TECH_DEBT.md` — reference as needed (prevents re-scheduling closed items)
8. `AIDM_EXECUTION_ROADMAP_V3.md` — reference as needed (milestone definitions)
9. `AGENT_DEVELOPMENT_GUIDELINES.md` — reference as needed (coding standards for WO drafting)

## Update Protocol

These are **copies** of the source files. They must be refreshed whenever the originals change.

**When to update:**
- After any work order is dispatched, delivered, or status-changed -> update `AEGIS_REHYDRATION_STATE.md` + `SESSION_BOOTSTRAP.md`
- After any CP is completed -> update `PROJECT_STATE_DIGEST.md`
- After any tech debt item is added/closed -> update `KNOWN_TECH_DEBT.md`
- After roadmap changes -> update `AIDM_EXECUTION_ROADMAP_V3.md`
- After R1 model selections change -> update `R1_TECHNOLOGY_STACK_SUMMARY.md`
- After Opus writes new notes -> update `OPUS_NOTES_FOR_AEGIS.md`
- After agent guidelines change -> update `AGENT_DEVELOPMENT_GUIDELINES.md`
- After ops rules change -> update `STANDING_OPS_CONTRACT.md`

**Who updates:**
- Thunder: manual copy when he knows a source changed
- Opus: refreshes copies during work sessions when source files are modified
- Aegis: should NOT modify these files (read-only for PM)

**Quick refresh command (from repo root):**
```
cp PROJECT_STATE_DIGEST.md pm_inbox/aegis_rehydration/
cp KNOWN_TECH_DEBT.md pm_inbox/aegis_rehydration/
cp docs/AIDM_EXECUTION_ROADMAP_V3.md pm_inbox/aegis_rehydration/
cp AGENT_DEVELOPMENT_GUIDELINES.md pm_inbox/aegis_rehydration/
cp pm_inbox/AEGIS_REHYDRATION_STATE.md pm_inbox/aegis_rehydration/
cp pm_inbox/OPUS_NOTES_FOR_AEGIS.md pm_inbox/aegis_rehydration/
```

Note: `SESSION_BOOTSTRAP.md`, `STANDING_OPS_CONTRACT.md`, and `R1_TECHNOLOGY_STACK_SUMMARY.md` live only in this folder (they are originals, not copies). Edit them directly here.
