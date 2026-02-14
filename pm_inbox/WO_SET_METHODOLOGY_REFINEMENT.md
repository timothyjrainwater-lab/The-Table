# Work Order Set: Methodology Refinement — Multi-Agent Coordination Gaps

**From:** Builder (Opus 4.6)
**To:** PM (Aegis) / PO (Thunder)
**Date:** 2026-02-14
**Status:** PROPOSAL — requires PM review before dispatch
**Context:** Full-context review of governance stack, thesis/counter-thesis, all 9 verification domains, research corpus, planning files, and existing scripts.

---

## Situation

The project's governance methodology has grown organically from incidents — each document exists because something broke. The thesis (`THESIS_FINAL_AI_FLEET_MANAGEMENT`) and counter-thesis (`COUNTER_THESIS_OPERATIONAL_REALITY`) identified 5 failure modes and proposed 7 concrete solutions. Two of those solutions exist (`verify_session_start.py`, `audit_snapshot.py`). Five do not. Meanwhile, the bone-layer verification exposed coordination gaps that the thesis predicted but the methodology didn't prevent.

This work order set addresses the **unfulfilled counter-thesis recommendations** plus **coordination gaps discovered in practice**. It is organized around three concerns that emerged from analysis:

1. **Agent Cognition Management** — How agents orient in a project they have no memory of
2. **Agent Coordination Across Context Boundaries** — How multiple amnesiac agents coordinate
3. **Quality Assurance at Scale** — How you verify correctness when no single agent holds the full picture

Each WO is self-contained and independently dispatchable. No WO requires another to complete first unless marked with DEPENDS-ON.

---

## WO-GOV-01: Sources of Truth Index

**Concern:** Agent Cognition Management
**Priority:** HIGH
**Effort:** Small (one file, ~50 lines)
**Origin:** Counter-thesis recommendation #1 (unfulfilled)

### Problem

Agents don't know which file is authoritative for a given concept. When the PSD says 303 formulas and the checklist says 338, which is correct? When the compass says 5,121 tests passing and the PSD says 5,510 collected, which is current? There's no index that says "for test counts, the machine-generated `docs/STATE.md` from `audit_snapshot.py --write` is canonical; everything else is commentary."

### Deliverable

Create `SOURCES_OF_TRUTH.md` (root level). Format:

```markdown
# Sources of Truth

| Concept | Canonical Source | Updated By | Frequency |
|---------|-----------------|------------|-----------|
| Test counts & pass rate | `docs/STATE.md` (machine-generated) | `python scripts/audit_snapshot.py --write` | Before any count claim |
| Locked systems & modules | `PROJECT_STATE_DIGEST.md` | Builder agent after each CP | Per CP |
| Formula verification status | `docs/verification/BONE_LAYER_CHECKLIST.md` | Verification agent | Per domain completion |
| Bug inventory | `docs/verification/WRONG_VERDICTS_MASTER.md` | Verification agent | Per verdict change |
| Design decisions (AMBIGUOUS) | `docs/verification/AMBIGUOUS_VERDICTS_DECISION_LOG.md` | Verification agent + PO | Per decision |
| Coding pitfalls | `AGENT_DEVELOPMENT_GUIDELINES.md` | Builder agent | Per discovered pitfall |
| Known deferrals | `KNOWN_TECH_DEBT.md` | Builder agent | Per deferral decision |
| Agent reading order | `AGENT_ONBOARDING_CHECKLIST.md` | PM | Per governance change |
| Architectural doctrine | `PROJECT_COHERENCE_DOCTRINE.md` | PM | Rare (constitutional) |
| Capability gate status | `PROJECT_STATE_DIGEST.md` § Gate Status | PM | Per gate change |
```

**Rules:**
- If two files disagree, the canonical source wins
- Machine-generated sources (`docs/STATE.md`) outrank hand-maintained sources for the same concept
- Adding a new concept requires adding a row to this index

### Acceptance

- File exists at root level
- Added to onboarding checklist reading table (position 2, after PROJECT_COMPASS, before PSD)
- Every row has a non-empty canonical source, updater, and frequency

---

## WO-GOV-02: Concurrent Session Protocol

**Concern:** Agent Coordination Across Context Boundaries
**Priority:** HIGH
**Effort:** Small (add section to AGENT_DEVELOPMENT_GUIDELINES.md)
**Origin:** Verbal discipline from PO ("each context window has a dedicated task"), not yet codified

### Problem

The project regularly runs multiple agent sessions in parallel (e.g., fix WOs in one window, governance in another, research in a third). The only rule preventing cross-wire conflicts is verbal — Thunder tells each session what not to touch. This has already caused problems:
- Domain C consistency miss (one session updated checklist, another session's scope included the domain file)
- ChatGPT work order cross-contamination ("calamity" per PO)
- Agents auto-executing on context rollover before understanding what other sessions are doing

There is no written protocol for how concurrent sessions claim file ownership.

### Deliverable

Add **Section 16: Concurrent Session Protocol** to `AGENT_DEVELOPMENT_GUIDELINES.md`:

```markdown
## 16. Concurrent Session Protocol

When multiple agent sessions run in parallel, file-level conflicts are the primary risk.

### 16.1 Session Scope Declaration

At session start, the operator declares which files this session may modify. The session MUST NOT write to files outside its declared scope. If a task requires touching an out-of-scope file, STOP and flag it to the operator.

### 16.2 File Ownership Rules

- **Source code files (*.py):** Owned by the session whose WO targets them. If two WOs touch the same file, they MUST run sequentially, not in parallel.
- **Governance docs (root *.md):** Owned by governance sessions only. Builder sessions do not modify governance docs unless the WO explicitly requires it.
- **Verification files (docs/verification/):** Owned by verification sessions only.
- **pm_inbox/:** Any session may write NEW files. No session modifies another session's files.

### 16.3 Rollover Discipline

When a context window rolls over and a new session starts from a summary:
1. Do NOT auto-execute. Read the summary and understand scope first.
2. Check git status for uncommitted work from the prior session.
3. Ask the operator what other sessions are running before modifying shared files.
4. If the prior session's scope is unclear, ask — don't assume.

### 16.4 Conflict Resolution

If two sessions accidentally modify the same file:
- The session that committed first wins.
- The second session must re-read the file and reconcile.
- If both sessions have uncommitted changes, the operator decides which takes priority.
```

### Acceptance

- Section 16 added to AGENT_DEVELOPMENT_GUIDELINES.md
- LAST UPDATED header bumped
- Rehydration copy synced

---

## WO-GOV-03: PM Context Compression Protocol

**Concern:** Agent Coordination Across Context Boundaries
**Priority:** HIGH
**Effort:** Medium (new file + template + process definition)
**Origin:** PO identified this as active pain point ("we're still struggling with the issue of the PM itself having a very limited context window")

### Problem

The PM (Aegis/GPT) is the spine anchor for the entire verification and fix process, but it has a limited context window. Currently:
- PM must reconstruct state from 15+ scattered files
- No standard memo format — each session writes memos differently
- No defined PM rehydration sequence
- PM can't distinguish "must read now" from "informational, read later"

The MEMO_GOVERNANCE_SESSION_FINDINGS.md written this session was a one-off solution. This WO systematizes it.

### Deliverable

Create `docs/governance/PM_REHYDRATION_PROTOCOL.md`:

**Section 1: PM Rehydration Reading Order**

When the PM opens a new context window, read in this order:

| Order | File | Purpose | Max Lines |
|-------|------|---------|-----------|
| 1 | `pm_inbox/PM_BRIEFING_CURRENT.md` | Latest session memos, action items | ~200 |
| 2 | `docs/verification/BONE_LAYER_CHECKLIST.md` | Verification completion status | ~70 |
| 3 | `PROJECT_STATE_DIGEST.md` | Operational state | ~500 |
| 4 | On demand: domain files, research docs | Only when a specific question arises | As needed |

**Section 2: Session Memo Format (Mandatory)**

Every agent session that produces strategic findings MUST write a memo to `pm_inbox/` using this format:

```markdown
# MEMO: [Short Title]

**From:** [Agent ID]
**Date:** [YYYY-MM-DD]
**Session scope:** [What this session was tasked with]

## Action Items (PM must act on these)
[Numbered list. Each item has: what needs to happen, who does it, what it blocks]

## Status Updates (Informational only)
[What was completed, what changed, what committed]

## Deferred Items (Not blocking, act when convenient)
[Low-priority findings, future WO suggestions]
```

**Section 3: PM Briefing Rotation**

`pm_inbox/PM_BRIEFING_CURRENT.md` is a rolling file. When the PM processes a memo:
1. Action items resolved → delete from briefing
2. Action items still open → keep in briefing
3. New memos arrive → append their action items to briefing

This ensures the PM's first read is always the smallest, most current document.

### Acceptance

- `docs/governance/PM_REHYDRATION_PROTOCOL.md` created
- `pm_inbox/PM_BRIEFING_CURRENT.md` created (seeded with current action items from MEMO_GOVERNANCE_SESSION_FINDINGS.md)
- Memo format added to AGENT_ONBOARDING_CHECKLIST.md Step 8 (PM Review Inbox section)

---

## WO-GOV-04: Document Budget Enforcement Test

**Concern:** Quality Assurance at Scale
**Priority:** MEDIUM
**Effort:** Small (one test file, ~60 lines)
**Origin:** Counter-thesis recommendation #3 (unfulfilled), thesis failure mode #2 (document accretion)

### Problem

The thesis identified document accretion as a failure mode: unbounded growth of governance docs with contradictory information. The counter-thesis counted 477 total docs (15 root, 245 in docs/, 217 in pm_inbox/) and proposed a hard cap enforced by test. That test was never written.

The project currently has no mechanism to prevent governance bloat. Every session can create new root-level `.md` files without constraint.

### Deliverable

Create `tests/test_document_budget.py`:

```python
"""Enforce document budget — prevent governance bloat.

Counter-thesis recommendation: hard cap on root-level governance docs.
Without enforcement, agent sessions create new docs freely, leading to
contradictory information and context window waste.

Thresholds are set generously — they catch runaway growth, not normal evolution.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def test_root_markdown_count():
    """Root-level .md files should not exceed budget."""
    MAX_ROOT_MD = 12  # Current: ~8-9. Ceiling allows moderate growth.
    root_md = list(PROJECT_ROOT.glob("*.md"))
    assert len(root_md) <= MAX_ROOT_MD, (
        f"Root-level .md file count ({len(root_md)}) exceeds budget ({MAX_ROOT_MD}). "
        f"Files: {sorted(f.name for f in root_md)}. "
        f"Consider consolidating or moving to docs/."
    )

def test_pm_inbox_not_unbounded():
    """pm_inbox should be regularly triaged, not endlessly accumulated."""
    MAX_PM_INBOX = 30  # Alert threshold, not hard block
    inbox = PROJECT_ROOT / "pm_inbox"
    if inbox.exists():
        inbox_files = list(inbox.glob("*.md"))
        assert len(inbox_files) <= MAX_PM_INBOX, (
            f"pm_inbox has {len(inbox_files)} files (threshold: {MAX_PM_INBOX}). "
            f"Triage needed — move reviewed items to pm_inbox/reviewed/."
        )
```

### Acceptance

- Test file exists and passes on current codebase
- Thresholds are set above current counts (budget, not quota)
- Test runs as part of standard `pytest tests/` suite

---

## WO-GOV-05: Coordination Failure Catalog

**Concern:** Quality Assurance at Scale (methodology research artifact)
**Priority:** MEDIUM
**Effort:** Medium (new file, ~150 lines, requires analysis)
**Origin:** Thesis identified 5 failure modes for individual agents. No equivalent catalog exists for multi-agent *coordination* failures.

### Problem

The verification error taxonomy (8 patterns in VERIFICATION_GUIDELINES.md) catalogs *what goes wrong when agents verify SRD formulas*. The thesis catalogs *what goes wrong with individual agent cognition* (epistemic drift, confidence cascading, etc.). But neither catalogs *what goes wrong when multiple agents coordinate on the same codebase*. These coordination failures are distinct from both:

- **Domain C consistency miss** — one session updated 2 of 3 files; another session had the third file in scope but didn't know about the change
- **ChatGPT cross-wire** — an agent from a different LLM provider generated work orders that conflicted with in-flight work
- **Auto-execute on rollover** — agent continued prior session's work without checking if scope had changed
- **Research cross-reference gap** — verification agents didn't have research docs in context because dispatches didn't reference them
- **Fix WO collision risk** — two fix WOs touch the same file, dispatched to parallel sessions

These are all real incidents from this project. Cataloging them serves both the build (prevents recurrence) and the thesis (primary research data on multi-agent failure modes).

### Deliverable

Create `docs/research/COORDINATION_FAILURE_CATALOG.md`:

**Format per entry:**

```markdown
### CF-[NNN]: [Short Name]

**Date:** [When it happened]
**Failure Mode:** [Category — see taxonomy below]
**Sessions Involved:** [Which agents/sessions]
**What Happened:** [Factual description]
**Root Cause:** [Why the coordination protocol didn't prevent it]
**Detection:** [How was it discovered]
**Resolution:** [What was done to fix it]
**Prevention:** [What governance change prevents recurrence, if any]
**Status:** [MITIGATED (governance change made) | OPEN (no prevention yet) | ACCEPTED (risk acknowledged)]
```

**Proposed Taxonomy:**

| Category | Description | Examples |
|----------|-------------|---------|
| **Partial Update** | One session updates some files, another session or the same session misses related files | CF-001: Domain C consistency miss |
| **Cross-Provider Contamination** | Work product from one LLM provider conflicts with in-flight work from another | CF-002: ChatGPT WO cross-wire |
| **Scope Bleed** | A session modifies files outside its declared scope, conflicting with another session | CF-003: Auto-execute on rollover |
| **Context Starvation** | A session lacks documents it needs because the dispatch didn't reference them | CF-004: Research cross-ref gap |
| **Parallel Collision** | Two parallel sessions modify the same file | CF-005: Fix WO file overlap risk |
| **Stale Reference** | A document references another document that has moved, been renamed, or contains outdated numbers | CF-006: Dead planning file link |

### Acceptance

- Catalog exists with at least 6 entries (the known incidents listed above)
- Each entry follows the format template
- Taxonomy covers all known incidents
- File is in `docs/research/` (it's research data, not governance)

---

## WO-GOV-06: Architecture Coverage Test

**Concern:** Quality Assurance at Scale
**Priority:** LOW
**Effort:** Medium (one test file, ~100 lines, requires analysis of boundary laws)
**Origin:** Counter-thesis recommendation #4 (unfulfilled), thesis failure mode #4 (phantom architecture)
**DEPENDS-ON:** None, but less urgent than GOV-01 through GOV-05

### Problem

The thesis identified "phantom architecture" — constraints that exist in documentation but aren't enforced by tests. The counter-thesis proposed `test_architecture_coverage.py` to verify that every documented constraint has a corresponding test. Currently, boundary laws BL-017/018/020 have tests in `tests/test_boundary_law.py`, but not all documented constraints do.

### Deliverable

Create `tests/test_architecture_coverage.py`:

The test should verify that key architectural constraints documented in the governance stack are actually enforced:

```python
"""Verify documented architectural constraints have corresponding enforcement.

Counter-thesis recommendation: every constraint in governance docs should
have a test or script that enforces it. This test checks that the enforcement
mechanisms exist (not that the constraints themselves hold — those are tested
elsewhere).

This is a META-test: it tests that other tests exist.
"""
from pathlib import Path
import ast

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"


def test_boundary_laws_have_tests():
    """Each boundary law (BL-NNN) should have a test in test_boundary_law.py."""
    bl_test = TESTS_DIR / "test_boundary_law.py"
    assert bl_test.exists(), "test_boundary_law.py missing"
    content = bl_test.read_text()
    # BL-017, BL-018, BL-020 are the current boundary laws
    for bl in ["017", "018", "020"]:
        assert f"bl_{bl}" in content.lower() or f"BL-{bl}" in content, (
            f"Boundary law BL-{bl} has no test in test_boundary_law.py"
        )


def test_session_bootstrap_exists():
    """verify_session_start.py must exist and be runnable."""
    script = PROJECT_ROOT / "scripts" / "verify_session_start.py"
    assert script.exists(), "Session bootstrap script missing"
    # Parse to verify it's valid Python
    ast.parse(script.read_text())


def test_audit_snapshot_exists():
    """audit_snapshot.py must exist and be runnable."""
    script = PROJECT_ROOT / "scripts" / "audit_snapshot.py"
    assert script.exists(), "Audit snapshot script missing"
    ast.parse(script.read_text())
```

This is intentionally minimal — it verifies that enforcement *mechanisms* exist, not that every line of every governance doc has a test. The counter-thesis's vision of full coverage is aspirational; this WO delivers the practical subset.

### Acceptance

- Test file exists and passes
- At minimum checks: boundary law tests exist, bootstrap script exists, audit snapshot exists
- Does NOT try to parse governance prose and match it to tests (that's phantom architecture itself)

---

## Dispatch Recommendations

### Wave 1 (HIGH priority, independent, can run in parallel):
- **WO-GOV-01** (Sources of Truth Index) — single file, no dependencies
- **WO-GOV-02** (Concurrent Session Protocol) — single section addition
- **WO-GOV-03** (PM Context Compression) — independent of GOV-01/02

### Wave 2 (MEDIUM priority, can wait for Wave 1):
- **WO-GOV-04** (Document Budget Test) — benefits from GOV-01 being in place
- **WO-GOV-05** (Coordination Failure Catalog) — benefits from GOV-02 being in place

### Wave 3 (LOW priority, defer):
- **WO-GOV-06** (Architecture Coverage Test) — nice-to-have, not blocking anything

### Estimated Scope

| WO | New Files | Modified Files | Lines (approx) |
|----|-----------|----------------|-----------------|
| GOV-01 | 1 | 1 (onboarding) | ~60 |
| GOV-02 | 0 | 1 (dev guidelines) | ~40 |
| GOV-03 | 2 | 1 (onboarding) | ~120 |
| GOV-04 | 1 | 0 | ~40 |
| GOV-05 | 1 | 0 | ~200 |
| GOV-06 | 1 | 0 | ~60 |
| **Total** | **6** | **3** | **~520** |

---

## Relationship to Thesis

These WOs serve dual purpose:

**For the build:** They close concrete gaps that have caused incidents (Domain C consistency miss, PM context overflow, ChatGPT cross-wire, research cross-ref gap). Each WO prevents a specific class of coordination failure.

**For the thesis:** They produce primary research artifacts:
- **GOV-01** demonstrates the "machine-generated truth outranks prose" principle
- **GOV-02** is a novel protocol for concurrent LLM agent session management (no published equivalent)
- **GOV-03** addresses the "PM as bottleneck" problem in hierarchical multi-agent systems
- **GOV-04** enforces the counter-thesis's "document budget" hypothesis with executable evidence
- **GOV-05** is primary data — a categorized failure catalog from a real multi-agent construction project
- **GOV-06** closes the loop on "phantom architecture" by requiring constraints to have enforcement

The coordination failure catalog (GOV-05) is probably the most valuable thesis artifact in this set. Published failure taxonomies for multi-agent LLM coordination don't exist yet — this would be novel.

---

## What This WO Set Does NOT Cover

- **The 7 AMBIGUOUS design decisions** — those are PO decisions, not governance work
- **RED BLOCK lift** — that's a PM action, not a WO
- **PSD refresh** — should happen when RED BLOCK lifts, not as a standalone WO
- **FAQ mining triage** — net-new feature work, not governance
- **Knowledge Synthesis update** — low priority, defer until re-verifications complete
- **Dispatch template amendment** (Gap 3) — PM-side change, not a builder WO
- **Code fixes** — the 13 fix WOs are already running in parallel

---

**End of Work Order Set**
