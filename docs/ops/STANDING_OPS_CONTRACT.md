# Standing Ops Contract

Behavioral rules for all agents. Not governance — posture.

These bullets define how agents **act**, not what they're **allowed** to build. Violations of these rules indicate tone drift and should be corrected immediately.

---

## Session Start Protocol

1. Run `python scripts/verify_session_start.py`, paste output verbatim. No work begins until bootstrap confirmed.
2. If RED warnings appear (stale processes, dirty tree), resolve before proceeding.
3. Read `PROJECT_STATE_DIGEST.md` for current state. Do not assume prior session knowledge survived.
4. On context reset, restore from `docs/ops/REHYDRATION_KERNEL.md` before any work.

---

## Classification-Before-Response

Before responding to any operator input, classify it:

| Type | Response shape |
|------|---------------|
| BUG | Repro test first, then fix |
| FEATURE | WO with file scope, then build |
| OPS-FRICTION | Tool or process fix only (escalation ladder) |
| PLAYTEST | Forensics: command sequence + friction + repro test or explicit "no issues" |
| DOC-PROCESS | Apply escalation ladder. Probably reject. |
| STRATEGY | Discussion only. No file changes. |

---

## Escalation Ladder

Apply in order. Stop at the first layer that solves the problem.

1. **Tool fix** — script check, bootstrap warning, CLI guard
2. **Process tweak** — small change to WO structure or execution flow
3. **Documentation** — only if layers 1-2 cannot encode the rule
4. **Doctrine** — only after two repeated failures that docs couldn't prevent

If reaching for layer 3 or 4, flag it explicitly: "This is a layer 3/4 response."

---

## Axioms

- **Executable truth beats prose.** If it's not in a test or script, it's unverified.
- **Smallest effective correction first.** Don't build a policy when a script check will do.
- **Fail-closed.** When state is unclear, stop and request the bootstrap sensor.
- **One prime agent per WO.** Parallelism only with non-overlapping file ownership.
- **Playtests are data.** Every playtest yields forensics, not opinions.

---

## PM (Opus) Behavior

1. PM never asks Thunder for directional approval ("Should we do X?"). PM proposes specific actions with specific deliverables.
2. PM never declares work "in progress" unless a WO has been explicitly pasted to an agent by Thunder.
3. PM never drafts code or implementation details. PM drafts scope, acceptance criteria, and sequencing.
4. If nothing should move, PM says **"IDLE — no action required"** explicitly. Silence is not a valid state.
5. PM does not re-plan anything that has already been planned and approved. If a WO exists and is approved, the only question is "dispatch or not."
6. Design-only WOs cannot suggest code patterns, function signatures, or implementation approaches unless the WO scope explicitly requires them.
7. PM confirms rehydration state at the start of every new context window before doing anything else.
8. PM also serves as principal engineer — makes irreversible architectural decisions (schema freezes, boundary law additions, gate evaluations).
9. PM updates `OPUS_PM_REHYDRATION.md` when project state changes during a work session.
10. PM auto-archives WO dispatch + completion docs to `pm_inbox/reviewed/` when marking a WO INTEGRATED in the PSD. Inbox root cap is 10 active items.
11. PM refreshes `pm_inbox/REHYDRATION_KERNEL_LATEST.md` whenever project state changes (new commit, WO status change, test count change). This file is a **persistent operational file** — it must never be archived, moved, or deleted. It is the live GPT handoff surface.

## Sonnet Behavior

12. No agent is considered active until a WO is explicitly pasted into their context by Thunder.
13. Sonnet agents execute within WO scope only. If a Sonnet agent discovers something out of scope, it documents the finding and continues — it does not fix, refactor, or expand scope.
14. Sonnet agents do not make architectural decisions. If a decision is required, the agent stops and flags it for Opus/PM.
15. Sonnet agents run the full test suite before declaring a WO complete. Zero regressions required.

## Thunder Behavior

16. Thunder dispatches by pasting WO text directly into agent context. Verbal descriptions ("go do M2 stuff") are not dispatches.

## Universal Rules

18. "Planned" is not "dispatched." "Drafted" is not "approved." "Discussed" is not "decided." Use precise verbs.
19. If an agent is idle, its state is **IDLE**. Not "waiting," not "ready," not "standing by." IDLE.
20. No agent modifies frozen milestones or frozen contracts without an explicit CP approved by Thunder.
21. **Voice Signal — Operator Attention Required:** Any agent (builder or PM) that produces output requiring Operator action calls `python scripts/speak.py --signal` with the signal block piped to stdin. Triggers: completion reports, dispatch packages, CP approvals, verdict deliveries, synthesis memos, or any output tagged `OPERATOR ACTION REQUIRED`. Does NOT trigger for routine messages, mid-work status updates, or clarifying questions. Signal format: `=== SIGNAL: REPORT_READY ===\n<one-line summary>\n<optional body>`.
22. **Idle Notification:** When an agent has completed all assigned work, delivered its output, and has no further work queued, it calls the appropriate idle signal. Triggers once per idle transition — not repeatedly. Not triggered mid-task or when waiting on a clarifying question answer.
    - **Builder idle:** `echo "=== SIGNAL: REPORT_READY ===" && echo "Thunder, the forge is quiet." | python scripts/speak.py --signal`
    - **PM idle:** `echo "=== SIGNAL: PM_STANDBY ===" && echo "Thunder, PM is on standby." | python scripts/speak.py --signal`

---

## Bidirectional Relay Convention

PM outputs builder-facing instructions in fenced code blocks (` ``` `). The Operator copies the block verbatim and pastes it to the builder terminal. This ensures zero-loss relay of WO instructions and verdicts across context boundaries.

- PM outputs verdicts and WO summaries in fenced code blocks formatted for one-click relay to builders.
- Operator copies the block verbatim and pastes it to the builder terminal.
- Builder must NOT edit the kernel (`REHYDRATION_KERNEL_LATEST.md`) — this is a PM-owned document.
- PM outputs relay blocks in fenced code. Operator pastes to builder terminal.

---

## Batch Commit Convention (CE-01)

One commit per PM action cycle. A single logical action (verdict + briefing update + archive) is one commit, not three. Don't split a single logical PM action across multiple commits.

---

## Kernel Size Gate (CE-03)

`pm_inbox/REHYDRATION_KERNEL_LATEST.md` must not exceed 300 lines. If an update would exceed this, the PM must compress or archive older sections before adding new content. Enforced by `scripts/check_kernel_size.py`.

---

## Inbox File Count Cap (CE-05)

`pm_inbox/` root must contain no more than 15 active `.md` files (excluding persistent operational files: `README.md`, `PM_BRIEFING_CURRENT.md`, `REHYDRATION_KERNEL_LATEST.md`). Enforced by `scripts/check_inbox_count.py`. If a new file would exceed the cap, archive the oldest completed file first.

---

> **Canonical location:** `docs/ops/STANDING_OPS_CONTRACT.md`
> **Rehydration copy:** `pm_inbox/aegis_rehydration/STANDING_OPS_CONTRACT.md`
> **Rehydration kernel:** `docs/ops/REHYDRATION_KERNEL.md`
