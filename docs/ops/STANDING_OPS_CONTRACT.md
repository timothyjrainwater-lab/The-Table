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
2. PM never declares work "in progress" unless a WO has been dispatched to a builder by Thunder. Thunder dispatches all builder sessions — this gives Thunder visibility into active work. Exception: PM may spawn read-only research/audit agents (no code writes, no commits) via Task tool without operator relay.
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

12. An agent is considered active when a WO has been dispatched to it — either by Thunder directly or by Slate via Task tool. Both are valid dispatch paths.
13. Sonnet agents execute within WO scope only. If a Sonnet agent discovers something out of scope, it documents the finding and continues — it does not fix, refactor, or expand scope.
14. Sonnet agents do not make architectural decisions. If a decision is required, the agent stops and flags it for Opus/PM.
15. Sonnet agents run the full test suite before declaring a WO complete. Zero regressions required.
15a. **Commit-Before-Report Rule:** Builders MUST `git add` + `git commit` all code changes BEFORE writing a completion report or debrief. A completion report without a commit hash is invalid — the PM cannot verify work that exists only in the working tree. If the session is ending and commit is impossible, the builder MUST document uncommitted files in the debrief so the Operator can recover the work.
15b. **FILED ≠ ACCEPTED — Gate Tests Are the Arbiter:** A builder may file a debrief describing work as complete. That is a claim, not a fact. A WO is ACCEPTED only when gate tests pass and the PM confirms. "FILED" means the builder asserts completion. "ACCEPTED" means the tests prove it. PM never upgrades a WO to ACCEPTED on a debrief alone. *Evidence: WO-ENGINE-RETRY-001 and RETRY-002 debriefs described code as landed; subsequent gate run found all three prerequisite layers absent from the codebase. SKILL-MODIFIER-001 gate run was the arbiter.*
15c. **Gap Exists — Verify Before Writing:** Any WO targeting "missing" functionality MUST include an Assumptions to Validate step that confirms the gap still exists before writing code. If the builder finds the feature is already implemented, gate tests validate existing behavior, zero production changes, and the finding is closed. Never write code targeting a gap that hasn't been verified against the current codebase. *Evidence: WO-ENGINE-SNEAK-ATTACK-IMMUNITY-001 targeted functionality the coverage audit said was missing; it was already implemented. Builder wrote code targeting a ghost.*
15d. **Post-Debrief Loose Thread Query:** After every debrief is accepted, the PM asks the builder: "Anything else you noticed outside the debrief?" Builders orient debriefs toward delivery — drift risks, quiet couplings, and naming inconsistencies surface in a second pass when that question is asked explicitly. Any findings raised in that pass are filed immediately before closing the WO. PM is responsible for asking; builder is responsible for answering honestly. *Evidence: `_normalize_skill()`/`SKILL_TIME_COSTS` coupling and missing `listen` entry in exploration_time.py both surfaced post-debrief and would have walked out with the context window otherwise.*

## Thunder Behavior

16. Thunder dispatches builder sessions by pasting WO text directly into agent context — this gives Thunder live visibility into progress. Verbal descriptions ("go do M2 stuff") are not dispatches. PM may dispatch read-only audit/research agents only.

## Agent Behavior

16a. **Inbox Archival Duty:** At the start of each agent session, scan `pm_inbox/` root for files with lifecycle `PM-REVIEWED`, `INTEGRATED`, or `ARCHIVE`. Move these to `pm_inbox/reviewed/`. Update `PM_BRIEFING_CURRENT.md` to remove archived entries. This is a standing obligation — the agent is the inbox janitor.
16b. **Stale-WO Detection:** At session start, check `PM_BRIEFING_CURRENT.md` for any WO listed as "IN EXECUTION." If a WO has been in execution with no corresponding completion report in `pm_inbox/` for the current session, flag it to the Operator: "WO-XXX shows IN EXECUTION but has no completion report. Check if the builder session died." This catches orphaned builder work early.

## Universal Rules

17. **Definition of Done — Resolver Completeness ≠ Campaign-Ready (THESIS-PHB-JUDGMENT-GAP-001, 2026-02-26):** Implementing all named PHB resolvers does not constitute a campaign-ready AIDM. A complete resolver stack handles known mechanics. A campaign-ready system also handles non-routable player actions through a bounded adjudication protocol (clarification, synthesis, validation, canonical event emission). "Done" means resolvers + adjudication layer. Resolver completeness is a milestone, not the finish line. *Evidence: Shepherd's pole case — creative player action with no PHB entry exposes that the adjudication layer was a hidden dependency, never explicitly designed. Filed as STRATEGY-AIDM-JUDGMENT-LAYER-001.*

17a. **Fail-Closed Campaign Safety Policy (interim, until judgment layer reaches Guarded phase):** Any player action that cannot be routed to a named resolver AND does not have a validated adjudication path MUST emit `needs_clarification` and prompt DM/player input. No canonical ruling event may be emitted from an unvalidated adjudication path. No hallucinated ruling is preferable to a clarification request — a confident wrong ruling with no audit trail is the worst outcome. This policy holds until SPEC-RULING-CONTRACT-001 is implemented and the validator is live. *Evidence: Without fail-closed behavior, non-routable actions produce silent LLM hallucinations that cannot be detected, audited, or replayed.*

18. "Planned" is not "dispatched." "Drafted" is not "approved." "Discussed" is not "decided." Use precise verbs.
19. If an agent is idle, its state is **IDLE**. Not "waiting," not "ready," not "standing by." IDLE.
20. No agent modifies frozen milestones or frozen contracts without an explicit CP approved by Thunder.
21. **Voice Signal — Operator Attention Required:** Any agent (builder or PM) that produces output requiring Operator action calls `python scripts/speak.py --signal` with the signal block piped to stdin. Triggers: completion reports, dispatch packages, CP approvals, verdict deliveries, synthesis memos, or any output tagged `OPERATOR ACTION REQUIRED`. Does NOT trigger for routine messages, mid-work status updates, or clarifying questions. Signal format: `=== SIGNAL: REPORT_READY ===\n<one-line summary>\n<optional body>`.
22. **Idle Notification:** When an agent has completed all assigned work, delivered its output, and has no further work queued, it calls the appropriate idle signal. Triggers once per idle transition — not repeatedly. Not triggered mid-task or when waiting on a clarifying question answer.
    - **Builder idle:** `echo "=== SIGNAL: REPORT_READY ===" && echo "Thunder, the forge is quiet." | python scripts/speak.py --signal`
    - **PM idle:** `echo "=== SIGNAL: PM_STANDBY ===" && echo "Thunder, PM is on standby." | python scripts/speak.py --signal`

---

## Chisel Behavior (Lead Builder)

23. Chisel rehydrates from `docs/ops/CHISEL_KERNEL_001.md` at the start of every session. No work begins before the kernel is read.
24. Chisel receives WOs from Slate and decides: take it (continuity is the asset) or pass it to a clean-slate agent (isolation is the asset). Chisel has authority to make this call without escalating to the operator.
25. Chisel sends live signals to Slate when queue state changes — unblocked dependencies, sequencing implications. These signals do not wait for the debrief cycle.
26. Chisel flags kernel touches in every Pass 3 debrief. Format: "This WO touches KERNEL-0X [name] — [what was noticed]." Anvil receives the flag and updates REGISTER-HIDDEN-DM-KERNELS-001.
27. **Kernel maintenance is a first-class deliverable.** A Chisel session is not closed until `CHISEL_KERNEL_001.md` reflects what changed during the session. Missing kernel update = session not closed.
28. Chisel never makes architectural decisions. If a WO requires one, Chisel stops and flags to PM/operator.
29. Chisel may refuse to execute a WO if the gap assumption has not been verified against the current codebase. Verify before writing — always.

---

## Bidirectional Relay Convention

PM outputs builder-facing instructions in fenced code blocks (` ``` `). When Thunder is relaying manually, he copies the block verbatim. When Slate dispatches via Task tool, the WO document is passed directly — no relay required.

- PM outputs verdicts and WO summaries to Thunder. ACCEPT verdicts include commit hash and gate score. REJECT verdicts include reason and remediation path. Thunder has final authority to override any verdict.
- Builder must NOT edit the kernel (`REHYDRATION_KERNEL_LATEST.md`) — this is a PM-owned document.

## Parallel Execution Policy

Slate may spawn multiple read-only audit/research agents simultaneously. Builder sessions (code writes, commits) are dispatched by Thunder. Slate coordinates sequencing and reports consolidated verdicts.

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
