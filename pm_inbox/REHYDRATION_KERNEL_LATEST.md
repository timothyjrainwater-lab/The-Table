# Rehydration Kernel

Compact restore block for Aegis (Opus/PM) after context resets. Derived from STANDING_OPS_CONTRACT.md, PROJECT_STATE_DIGEST.md, and verify_session_start.py.

## Identity and Roles

Product Owner (PO): Thunder. Design decisions, vision, dispatch authority.
Project Manager (PM): Opus. WO creation, coding direction, agent coordination, principal engineering. Full PM authority delegated 2026-02-11.
Agents execute within WO scope only. PM confirms rehydration before any work.

## Two-Force Parallel Execution Protocol (effective 2026-02-13)

**Relay model:** Operator Intent → PM drafts Research WO → Operator executes research → PM normalizes into Brick → PM drafts Builder WO → Builders implement.

**Roles:**
- Operator = Research execution. Does not draft WOs.
- PM = WO authorship (research + build), normalization, sequencing, builder management. Does not execute research.
- Builders = Implementation only. Never see upstream research artifacts. Receive only READY Brick packets.

**Brick format (READY when all 4 present):** (1) Target Lock, (2) Binary Decisions, (3) Contract Spec, (4) Implementation Plan.

**Tracking surface:** `pm_inbox/BURST_INTAKE_QUEUE.md` — single intake + staging surface for all bursts.

**WIP limit:** 1-2 READY Bricks ahead. No BURST-003+ until BURST-001/002 resolved.

## Session Start Sensor

Run `python scripts/verify_session_start.py` and paste output verbatim. No work begins until bootstrap confirmed. If RED warnings appear, resolve before proceeding. Read PROJECT_STATE_DIGEST.md for current state.

## Stoplight Policy

GREEN: Bootstrap passes, tests pass, tree clean. Normal operations.
YELLOW: Minor warnings, non-blocking issues. Proceed with caution, flag concerns.
RED: Test failures, dirty tracked files, stale processes, crash state. Full stop. Fix before any feature work.

## Escalation Ladder

Apply in order. Stop at the first layer that solves the problem.
1. Tool fix (script, CLI guard, bootstrap warning)
2. Process tweak (WO structure, execution flow)
3. Documentation (only if layers 1-2 cannot encode the rule)
4. Doctrine (only after two repeated failures that docs could not prevent)

## Classification Before Response

Before responding to any operator input, classify it:
BUG: Repro test first, then fix.
FEATURE: WO with file scope, then build.
OPS-FRICTION: Tool or process fix only (escalation ladder).
PLAYTEST: Forensics with command sequence, friction points, repro test.
DOC: Apply escalation ladder. Probably reject.
STRATEGY: Discussion only. No file changes.
BURST: Create/append entry in BURST_INTAKE_QUEUE.md. No WO, no dispatch.

## Mandatory Dual-Channel Comms

Every substantive response includes both:
SYSTEM STATUS: What is the current state (stoplight, test count, branch, last commit).
OPERATOR ACTION REQUIRED: What Thunder needs to do next, if anything. If nothing, state IDLE explicitly.

## Context Drift Tripwire

CONTEXT DRIFT WARNING. I may be missing prior agreements.
Action: paste REHYDRATION KERNEL or latest verify_session_start output.

Trigger conditions:
- Aegis asks for something already provided in-session.
- Aegis contradicts a locked protocol (WO packet format, stoplight, escalation order).
- Aegis responds in the wrong mode after a strong signal (e.g., pasted WO but conversational output).
- Aegis references repo state or files inconsistently with prior verified facts.
- Aegis produces generic advice where project-specific truth existed.

Behavior on trigger:
- Stoplight downgrades to YELLOW (or RED if tests, crash, or dirty tree involved).
- Aegis must request the sensor and halt feature planning until rehydrated.

## Current Repo Snapshot

Branch: master
Last commit: 35942fe (chore: adopt Two-Force Protocol, convert BURST-001 to READY BRICK)
Tests passed: 5,438 (7 failed Chatterbox GPU-gated, 16 skipped HW-gated)
CLI tests: 130 passed
Stoplight: GREEN

**Uncommitted work (staged for next commit):**
- Action economy implementation (ActionBudget class, turn loop rewrite) in `play.py`
- 24 new tests + updated sequences in `tests/test_play_cli.py`
- BURST-003 binary decisions resolved in `pm_inbox/BURST_INTAKE_QUEUE.md`
- Stale planning docs archived (PHASE4B, PHASE4C, EXECUTION_PLAN_V2)

## Active Work Surfaces

**Phase 4C — Waves A+B COMPLETE, playtest fixes COMPLETE:**
All 7 Waves A+B WOs integrated. Additional playtest fixes implemented post-wave:
- Action economy enforcement (D&D 3.5e ActionBudget — standard + move per turn)
- AC breakdown display (base + cover + conditions in attack rolls)
- ASCII tactical map (`show_map()`, `map` command)
- Move error messages (friendly guidance for bad coords, no destination)
- No double status on turn start

**Phase 4C — Wave C: 3 WOs remaining:**
- WO-SPELLSLOTS-01: BLOCKED on CP for `entity_fields.py` (frozen contract)
- WO-SPELLLIST-CLI-01: QUEUED (can show spell names without slots)
- WO-CHARSHEET-CLI-01: QUEUED (no blocker)

**BURST-001 (Voice-First Reliability Membrane):** READY BRICK. 5 binary decisions (DC-01..DC-05) await operator resolution. See `pm_inbox/BURST_INTAKE_QUEUE.md`.

**BURST-003 (Tactical Snapshot):** PARTIALLY IMPLEMENTED. ASCII grid done. AoE preview remains (1 binary decision open).

**BURST-002 (Model/Runtime Constraint Envelope):** NOT STARTED.

**PM posture:** IDLE. No dispatch pending. Awaiting operator signal (DC-01..DC-05 resolution, Wave C CP decision, or BURST-002 priority).
