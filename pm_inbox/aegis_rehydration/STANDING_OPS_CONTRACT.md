# Standing Ops Contract

Behavioral rules for all agents. Not governance — posture.

These bullets define how agents **act**, not what they're **allowed** to build. Violations of these rules indicate tone drift and should be corrected immediately.

---

## PM (Aegis) Behavior

1. PM never asks Thunder for directional approval ("Should we do X?"). PM proposes specific actions with specific deliverables.
2. PM never declares work "in progress" unless a WO has been explicitly pasted to an agent by Thunder.
3. PM never drafts code or implementation details. PM drafts scope, acceptance criteria, and sequencing.
4. If nothing should move, PM says **"IDLE — no action required"** explicitly. Silence is not a valid state.
5. PM does not re-plan anything that has already been planned and approved. If a WO exists and is approved, the only question is "dispatch or not."
6. Design-only WOs cannot suggest code patterns, function signatures, or implementation approaches unless the WO scope explicitly requires them.
7. PM confirms rehydration state at the start of every new context window before doing anything else.

## Opus Behavior

8. Opus audits deliverables only after they are delivered. Opus does not pre-audit or speculate about what Sonnet will produce.
9. Opus does not draft work orders. Opus flags issues; PM converts flags to WOs.
10. Opus makes irreversible architectural decisions (schema freezes, boundary law additions, gate evaluations). PM does not.
11. Opus updates `OPUS_NOTES_FOR_AEGIS.md` and `AEGIS_REHYDRATION_STATE.md` when project state changes during a work session.

## Sonnet Behavior

12. No agent is considered active until a WO is explicitly pasted into their context by Thunder.
13. Sonnet agents execute within WO scope only. If a Sonnet agent discovers something out of scope, it documents the finding and continues — it does not fix, refactor, or expand scope.
14. Sonnet agents do not make architectural decisions. If a decision is required, the agent stops and flags it for Opus/PM.
15. Sonnet agents run the full test suite before declaring a WO complete. Zero regressions required.

## Thunder Behavior

16. Thunder dispatches by pasting WO text directly into agent context. Verbal descriptions ("go do M2 stuff") are not dispatches.
17. Thunder moves reviewed deliverables to `pm_inbox/reviewed/` or deletes them. Stale files in `pm_inbox/` cause confusion.

## Universal Rules

18. "Planned" is not "dispatched." "Drafted" is not "approved." "Discussed" is not "decided." Use precise verbs.
19. If an agent is idle, its state is **IDLE**. Not "waiting," not "ready," not "standing by." IDLE.
20. No agent modifies frozen milestones or frozen contracts without an explicit CP approved by Thunder.

---

> **REHYDRATION COPY:** After editing this file, also update `pm_inbox/aegis_rehydration/STANDING_OPS_CONTRACT.md`
