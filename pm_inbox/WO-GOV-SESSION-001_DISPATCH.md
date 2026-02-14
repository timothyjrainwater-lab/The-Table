# WO-GOV-SESSION-001: Governance Enforcement Session

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 0 (gate-lift prerequisite)
**Priority:** P0 — Governance infrastructure for sustainable operations
**Source:** WO_SET_PM_CONTEXT_EFFICIENCY (6 CE items), MEMO_IDLE_NOTIFICATION (Rule 22), MEMO_OPERATOR_RELAY_REFINEMENTS (relay convention), MEMO_FIVE_ROLE_AGENT_ARCHITECTURE (5-role model), MEMO_RESEARCH_SPRINT_SECOND_PASS (BL-021)

---

## Target Lock

Implement governance rules and operational tooling that have been verdicted by the PM but not yet enforced in code or documentation. One builder session, multiple deliverables. All items are documentation edits, light scripting, or test additions — no production engine code changes.

## Items (8 deliverables)

### Item 1: BL-021 — "Events Record Results, Not Formulas"

**Source:** RQ-SPRINT-007, second-pass analysis Action Item 2.

**What:** Add BL-021 to the boundary law list. Add a structural test that asserts no event payload key matches formula-indicative patterns.

**Deliverables:**
- Add BL-021 definition to `docs/design/LLM_ENGINE_BOUNDARY_CONTRACT.md` (or wherever BL-001 through BL-020 are defined).
- Add test to `tests/test_boundary_law.py` that inspects all `MUTATING_EVENTS` and `INFORMATIONAL_EVENTS` payload schemas for keys containing `formula`, `expression`, `calculation`, `equation`, or `compute`. Assert none exist.

**Acceptance:** Test passes. BL-021 appears in boundary law documentation.

### Item 2: Rule 22 — Builder Idle Notification

**Source:** MEMO_IDLE_NOTIFICATION (verdicted with amendments).

**What:** When a builder WO completes and no further WOs are queued, the builder's completion report triggers a voice notification: "Thunder, the forge is quiet."

**Deliverables:**
- Add a function to `scripts/speak.py` (or create `scripts/notify.py`) that accepts a message string and speaks it via the default TTS adapter.
- The WO completion template (in agent development guidelines or equivalent) instructs builders to call this function as their final action when no follow-up WO is queued.
- Voice line text: `"Thunder, the forge is quiet."`

**Constraints:**
- Builder-only trigger. Fires on WO completion, not on arbitrary conditions.
- Uses whatever TTS is available (Chatterbox if GPU, Kokoro if CPU, skip if neither).
- If TTS is unavailable, print the message to stdout instead. Never crash on missing TTS.

**Acceptance:** `python scripts/speak.py "Thunder, the forge is quiet"` (or equivalent) produces audible speech or prints to stdout.

### Item 3: Rule 22 — PM Idle Notification

**Source:** MEMO_PM_IDLE_SIGNAL (reversed rejection, Operator override).

**What:** When PM completes all pending verdicts and no inbox items require PM action, the PM signals: "Thunder, PM is on standby."

**Deliverables:**
- Same mechanism as Item 2 — call the speak function with the PM message.
- Voice line text: `"Thunder, PM is on standby."`
- Trigger: PM outputs this as final line when all verdicts are delivered and briefing shows no PM-required actions.

**Constraints:**
- PM does not execute this directly (PM Execution Boundary). The PM includes the instruction in its output; the Operator's terminal or an assistant agent executes the call.
- Alternative: Add to the PM Context Window Handover Protocol as a final-action instruction.

**Acceptance:** The mechanism exists and is documented. PM knows to signal standby. Voice line plays when called.

### Item 4: Bidirectional Relay Convention

**Source:** MEMO_OPERATOR_RELAY_REFINEMENTS (accepted).

**What:** PM outputs verdicts and WO summaries in fenced code blocks formatted for one-click relay to builders.

**Deliverables:**
- Add a section to `docs/ops/STANDING_OPS_CONTRACT.md` (or equivalent) documenting the relay convention:
  - PM outputs builder-facing instructions in fenced code blocks (```).
  - Operator copies the block verbatim and pastes it to the builder terminal.
  - Builder must NOT edit kernel (PM-owned document).
- Add to kernel: "PM outputs relay blocks in fenced code. Operator pastes to builder terminal."

**Acceptance:** Convention documented in ops contract and kernel.

### Item 5: Five-Role Model Documentation

**Source:** MEMO_FIVE_ROLE_AGENT_ARCHITECTURE (accepted with amendments).

**What:** The 5-role model is in the kernel (table added by PM). This item ensures the roles are also documented in the agent-facing guidelines so builders and assistants see them on startup.

**Deliverables:**
- Add a "Project Roles" section to `docs/ops/AGENT_DEVELOPMENT_GUIDELINES.md` (or equivalent builder-facing doc) with the same 5-role table from the kernel.
- Ensure `docs/ops/BS_BUDDY_ONBOARDING.md` references the 5-role model.
- Do NOT create an Assistant onboarding doc (deferred until first assistant session).

**Acceptance:** Role table appears in agent-facing docs. BS Buddy onboarding references it.

### Item 6: CE-01 — Batch Commit Convention

**Source:** WO_SET_PM_CONTEXT_EFFICIENCY, CE-01.

**What:** Document the convention: one commit per PM action cycle. Don't split a single logical PM action across multiple commits.

**Deliverables:**
- Add to `docs/ops/STANDING_OPS_CONTRACT.md`: "Batch commit convention: one commit per PM action cycle. A single logical action (verdict + briefing update + archive) is one commit, not three."

**Acceptance:** Convention documented.

### Item 7: CE-03 — Kernel Size Gate

**Source:** WO_SET_PM_CONTEXT_EFFICIENCY, CE-03.

**What:** The kernel has a size budget. Establish a line-count gate.

**Deliverables:**
- Add to `docs/ops/STANDING_OPS_CONTRACT.md`: "Kernel size gate: REHYDRATION_KERNEL_LATEST.md must not exceed 300 lines. If an update would exceed this, the PM must compress or archive older sections before adding new content."
- Add a CI-compatible check (script or test) that counts lines in the kernel and warns if >300.

**Acceptance:** Gate documented. Check script exists.

### Item 8: CE-05 — Inbox File Count Cap

**Source:** WO_SET_PM_CONTEXT_EFFICIENCY, CE-05.

**What:** The inbox has a file count cap of 15 active files (already informally enforced). Formalize it.

**Deliverables:**
- Add to `pm_inbox/README.md`: "Active file cap: 15. Persistent files (README, briefing, kernel) don't count. If a new file would exceed the cap, archive the oldest completed file first."
- Add a check script that counts non-persistent files in `pm_inbox/` root and warns if >15.

**Acceptance:** Cap documented in README. Check script exists.

---

## Items NOT Included (deferred CE items)

- **CE-02 (PSD compression):** PSD is already under 500 lines. No action needed now.
- **CE-04 (Auto-archive stale files):** Deferred — requires more design. Filed for future governance sprint.
- **CE-06 (Context drift detection tooling):** Deferred — tripwire already exists in kernel prose. Tooling is future work.

---

## Success Criteria (Overall)

- [ ] BL-021 documented and tested
- [ ] `speak.py` (or equivalent) produces voice output for arbitrary text strings
- [ ] Builder idle notification documented in WO completion protocol
- [ ] PM idle notification mechanism documented
- [ ] Relay convention documented in ops contract
- [ ] 5-role table in agent-facing guidelines
- [ ] Batch commit convention documented
- [ ] Kernel size gate documented + check script
- [ ] Inbox file cap documented + check script
- [ ] All existing tests pass

## Files Expected to Change

- `docs/design/LLM_ENGINE_BOUNDARY_CONTRACT.md` — BL-021
- `tests/test_boundary_law.py` — BL-021 structural test
- `scripts/speak.py` or `scripts/notify.py` — voice notification function
- `docs/ops/STANDING_OPS_CONTRACT.md` — relay convention, batch commit, kernel gate
- `docs/ops/AGENT_DEVELOPMENT_GUIDELINES.md` — 5-role table, WO completion protocol
- `docs/ops/BS_BUDDY_ONBOARDING.md` — role model reference
- `pm_inbox/README.md` — inbox cap formalization
- New: check scripts for kernel size and inbox count

## Files NOT to Change

- Any production engine code (`aidm/core/`, `aidm/schemas/`, `aidm/lens/`, etc.)
- `pm_inbox/REHYDRATION_KERNEL_LATEST.md` — PM-owned, builder must not edit
- `pm_inbox/PM_BRIEFING_CURRENT.md` — PM-owned

---

*End of WO-GOV-SESSION-001*
