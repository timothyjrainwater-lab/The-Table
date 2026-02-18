# PM Rehydration Folder

**Purpose:** Contains files for rehydrating Opus (the PM) in a new context window.

## How To Use

1. Open a new Claude Opus context window
2. Drop the key rehydration files into the conversation
3. Say: "Warm resume. Read all files."
4. Opus should respond with state banner confirmation and resume work

## Reading Order

1. `OPUS_PM_REHYDRATION.md` — **Primary rehydration packet** (state banner, governance, dispatch methodology, WO tracking)
2. `STANDING_OPS_CONTRACT.md` — Behavioral rules for all agents
3. `PROJECT_STATE_DIGEST.md` — Full project state (reference as needed)
4. Other files — Reference as needed

## What's In Here

| File | Purpose |
|------|---------|
| `OPUS_PM_REHYDRATION.md` | Primary PM rehydration: state, governance, dispatch methodology, WO tracking |
| `STANDING_OPS_CONTRACT.md` | Behavioral rules for PM, Sonnet agents, Thunder |
| `PROJECT_STATE_DIGEST.md` | Full project state snapshot (copy from repo root) |
| `AGENT_DEVELOPMENT_GUIDELINES.md` | Coding standards for WO drafting (copy from repo root) |
| `KNOWN_TECH_DEBT.md` | Intentionally deferred issues (copy from repo root) |
| `AIDM_EXECUTION_ROADMAP_V3.md` | Historical M0-M4 roadmap (superseded by 7-step execution plan) |
| `R1_TECHNOLOGY_STACK_SUMMARY.md` | R1 model selections executive summary |

## Update Protocol

- `OPUS_PM_REHYDRATION.md` — Updated by PM (Opus) when state changes
- `STANDING_OPS_CONTRACT.md` — Updated by PM when behavioral rules change
- Other files — Copies refreshed from source when they change

## Historical Note

This folder was originally named `aegis_rehydration/` when Aegis (GPT-4) was PM. As of 2026-02-11, Opus is PM with full authority. The folder name is retained for path stability, but all Aegis-specific files have been removed.
