# The Drift Problem — Part 2: Operational Solutions

**Author:** Claude Opus 4.6
**Date:** 2026-02-13
**Prerequisite:** Part 1 (THESIS_AI_FLEET_ORCHESTRATION_2026_02_13.md)
**Purpose:** For each failure mode identified in Part 1, this document provides a concrete organizational structure, execution protocol, and preventive infrastructure that should be in place from day one.

---

## Preamble: The Design Principle

Every solution in this document follows one rule:

> **If the solution requires an agent to remember to do something, it will fail. If the solution is automated and structural, it will hold.**

Humans forget. Agents don't have persistent memory. Prose rules drift. Therefore, every solution must be encoded in one of three forms:
1. **Automated gate** — code that runs and blocks bad outcomes
2. **Structural constraint** — a file/directory/workflow layout that makes the wrong thing hard to do
3. **Ritual** — a short, repeatable human action that produces verifiable output

---

## Solution 1: Defeating Epistemic Drift

### The Problem (Recap)
Agents read other agents' summaries instead of source code. Each handoff introduces inaccuracies. After 3-4 handoffs, 30-40% of the collective model is wrong.

### The Organizational Structure: Source-of-Truth Registry

Create a single file at the project root that declares, for every important concept, **exactly one file** that is the canonical source of truth.

```
# SOURCES_OF_TRUTH.md
#
# When an agent needs to know something, they read THE FILE LISTED HERE.
# Not a summary. Not a doc. Not another agent's report. The file.
#
# Format: <concept> → <canonical file> → <verification command>

Test count         → pytest output          → python -m pytest tests/ -q --tb=no
Project state      → docs/STATE.md          → python scripts/audit_snapshot.py --write
Boundary law       → tests/test_boundary_completeness_gate.py → pytest tests/test_boundary_completeness_gate.py -v
Immutability rules → tests/test_immutability_gate.py → pytest tests/test_immutability_gate.py -v
World state schema → aidm/core/state.py     → (read file directly)
Attack resolution  → aidm/core/full_attack_resolver.py → pytest tests/test_full_attack.py -v
Spell resolution   → aidm/core/spell_resolver.py → pytest tests/test_spell_resolver.py -v
Entity fields      → aidm/schemas/entity_fields.py → (read file directly)
Layer architecture → tests/test_boundary_completeness_gate.py:LAYERS → (read file directly)
CLI behavior       → play.py                → python play.py (interactive)
```

### The Automated Gate: Handoff Verification Script

Create a script that every agent runs at session start, before doing any work:

```python
# scripts/verify_session_start.py
"""
Run this at the START of every agent session.
It produces machine-verified ground truth that the agent must use
instead of reading previous agent summaries.

Usage: python scripts/verify_session_start.py
"""

# Outputs:
# 1. Current commit hash + dirty/clean status
# 2. Test suite results (exact numbers)
# 3. List of all files modified since last commit
# 4. Any failing gate tests
# 5. CLI smoke test (can the game start?)
```

This script replaces the "read the handoff doc" step. The agent doesn't need to trust the previous agent's claims — it generates its own ground truth.

### The Ritual: The 60-Second Orient

Before any agent does any work, it must:

1. Run `python scripts/verify_session_start.py` (automated)
2. Read the output (10 seconds)
3. State in its first message: "Session starting on commit X. Y tests passing. Z files dirty." (10 seconds)

If an agent starts working without this step, its session output cannot be trusted.

### Execution Plan

| Step | Action | Owner | Gate |
|------|--------|-------|------|
| 1 | Create `SOURCES_OF_TRUTH.md` | First agent session | File exists |
| 2 | Create `scripts/verify_session_start.py` | First agent session | Script runs without error |
| 3 | Add session-start check to agent instructions | Human operator | Instructions include "run verify_session_start.py first" |
| 4 | Every agent session begins with verify output | All agents | First message contains commit hash + test count |

### What This Prevents

- Agent B building on Agent A's fabricated findings (Agent B generates its own truth)
- Conflicting test counts across documents (one script, one source)
- Work starting on a dirty tree without awareness (script flags dirty files)

---

## Solution 2: Defeating Document Accretion

### The Problem (Recap)
Documents accumulate without bound. Multiple docs assert different "facts." No one reads them all. They become a source of false confidence.

### The Organizational Structure: The Document Budget

Enforce a hard cap on documents by category:

```
ROOT LEVEL (max 5 files):
  README.md           — what is this project, how to run it
  SOURCES_OF_TRUTH.md — where to find canonical answers
  CONTRIBUTING.md     — rules for agent sessions
  KNOWN_TECH_DEBT.md  — tracked exceptions to quality gates
  CHANGELOG.md        — what changed and when

docs/ (max 3 files):
  docs/STATE.md       — machine-generated snapshot (never hand-edited)
  docs/ARCHITECTURE.md — layer diagram + boundary rules (one page)
  docs/ONBOARDING.md  — new agent quickstart (one page)

docs/planning/ (unlimited, but auto-pruned):
  — Planning docs live here
  — Any doc older than 30 days is considered stale
  — Agents must not read planning docs as source of truth

pm_inbox/ (unlimited, append-only):
  — Agent session reports go here
  — These are historical records, not living documents
  — Agents must not read other agents' reports as source of truth
```

### The Automated Gate: Document Count Enforcer

```python
# tests/test_document_budget.py
"""Enforce document budget. Fails if too many docs exist."""

import pathlib
import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

def test_root_markdown_count():
    """No more than 5 markdown files at project root."""
    root_md = list(PROJECT_ROOT.glob("*.md"))
    assert len(root_md) <= 5, (
        f"Document budget exceeded: {len(root_md)} root .md files "
        f"(max 5). Files: {[f.name for f in root_md]}"
    )

def test_docs_core_count():
    """No more than 3 core docs in docs/ (excluding planning/)."""
    docs_dir = PROJECT_ROOT / "docs"
    core_docs = [f for f in docs_dir.glob("*.md") if f.is_file()]
    assert len(core_docs) <= 3, (
        f"Document budget exceeded: {len(core_docs)} core docs "
        f"(max 3). Files: {[f.name for f in core_docs]}"
    )

def test_no_stale_planning_docs():
    """Flag planning docs older than 30 days."""
    import time
    planning_dir = PROJECT_ROOT / "docs" / "planning"
    if not planning_dir.exists():
        return
    stale = []
    cutoff = time.time() - (30 * 86400)
    for f in planning_dir.glob("*.md"):
        if f.stat().st_mtime < cutoff:
            stale.append(f.name)
    if stale:
        pytest.fail(
            f"{len(stale)} stale planning docs (>30 days): {stale}. "
            "Archive or delete them."
        )
```

### The Structural Constraint: Directory Layout

```
project/
├── README.md                    # What + how to run
├── SOURCES_OF_TRUTH.md          # Where to find answers
├── CONTRIBUTING.md              # Agent session rules
├── KNOWN_TECH_DEBT.md           # Tracked exceptions
├── CHANGELOG.md                 # History
├── docs/
│   ├── STATE.md                 # Machine-generated (DO NOT EDIT)
│   ├── ARCHITECTURE.md          # One-page layer diagram
│   └── ONBOARDING.md            # New agent quickstart
│   └── planning/                # Ephemeral planning docs
│       └── *.md                 # Auto-pruned after 30 days
├── pm_inbox/                    # Historical agent reports
│   └── *.md                     # Append-only, never read as truth
├── scripts/
│   ├── audit_snapshot.py        # Generates STATE.md
│   └── verify_session_start.py  # Agent session bootstrap
├── aidm/                        # Production code
├── tests/                       # Tests (including gate tests)
└── play.py                      # The playable product
```

### The Ritual: One In, One Out

If any agent needs to create a new root-level or core doc, it must delete an existing one first. The human operator enforces this by rejecting commits that increase the count.

### Execution Plan

| Step | Action | Owner | Gate |
|------|--------|-------|------|
| 1 | Consolidate existing root docs to 5 | Agent session | `test_document_budget.py` passes |
| 2 | Create `docs/ARCHITECTURE.md` (one page) | Agent session | File exists, ≤ 80 lines |
| 3 | Create `docs/ONBOARDING.md` (one page) | Agent session | File exists, ≤ 100 lines |
| 4 | Add `test_document_budget.py` to test suite | Agent session | Test passes |
| 5 | Move all planning docs to `docs/planning/` | Agent session | No planning docs at root |

### What This Prevents

- Unbounded document growth (hard cap enforced by test)
- Contradictory documents (only 5+3 exist, easy to audit)
- Stale planning docs misleading future agents (30-day auto-flag)
- Agents reading each other's reports as truth (pm_inbox is write-only)

---

## Solution 3: Defeating Confidence Cascading

### The Problem (Recap)
Agent A's confident claim becomes Agent B's unquestioned input. False claims propagate through the chain with increasing confidence at each step.

### The Organizational Structure: The Claim/Evidence Split

Every piece of inter-agent communication must separate **claims** from **evidence**. A claim without evidence is not information — it is noise.

Format:

```
CLAIM: The spell resolver does not handle natural 1/20.
EVIDENCE: [NONE — this claim is unverified]

vs.

CLAIM: state.py to_dict() returns a mutable reference.
EVIDENCE: state.py:56-66 — returns dict with live references
          to self.entities. Verified: modified returned dict,
          confirmed original state mutated.
VERIFICATION: python -c "from aidm.core.state import WorldState; ..."
```

The rule: **if the EVIDENCE field is empty or says "NONE," the receiving agent must verify the claim itself before acting on it.**

### The Automated Gate: Claim Verification in Handoffs

This is harder to automate than other gates because it's about agent behavior, not code. The structural enforcement is:

1. The handoff format requires an Evidence block with file:line references
2. The receiving agent's first action is to read those files and verify the claims
3. The `verify_session_start.py` script produces independent ground truth that conflicts with false claims

### The Structural Constraint: The Skepticism Protocol

Add to `CONTRIBUTING.md`:

```markdown
## The Skepticism Protocol

When you receive a handoff from another agent:

1. Run `python scripts/verify_session_start.py` — this is YOUR ground truth
2. Read the handoff's Evidence block
3. For each claim with a file:line reference, READ THAT FILE AND LINE
4. For each claim without evidence, treat it as UNVERIFIED
5. Do not act on unverified claims without checking the source code

If the handoff's Validation block says "5,275 passed" but your
verify script says "5,299 passed," trust YOUR script. The other
agent may have been working on a different commit.

NEVER trust:
- Test counts without pytest output
- Bug descriptions without file:line references
- "I fixed X" without a test that verifies X
- Architectural claims without code evidence
```

### The Ritual: The Trust-But-Verify Checklist

At the start of every session, after running verify_session_start.py, the agent checks:

```
□ I ran verify_session_start.py and recorded commit + test count
□ I read the SOURCES_OF_TRUTH.md for any concept I need
□ I have NOT read previous agent reports as a source of truth
□ Any claims I'm building on, I have verified against source code
□ My session plan references files I've actually read, not summaries
```

### Execution Plan

| Step | Action | Owner | Gate |
|------|--------|-------|------|
| 1 | Define Claim/Evidence format in CONTRIBUTING.md | Agent session | File updated |
| 2 | Add Skepticism Protocol to CONTRIBUTING.md | Agent session | Section exists |
| 3 | Mandate verify_session_start.py as first action | Human operator | In agent instructions |
| 4 | Review first handoff using new format | Human operator | Evidence block has file:line refs |

### What This Prevents

- False claims propagating unquestioned (evidence requirement forces verification)
- Agents building fixes for non-existent bugs (must read the actual code first)
- Confidence accumulating without grounding (each session generates fresh truth)

---

## Solution 4: Defeating Phantom Architecture

### The Problem (Recap)
Architectural rules exist in docs but not in code. Agents may or may not follow them. Violations accumulate silently.

### The Organizational Structure: The Constraint Registry

Every architectural constraint must exist in exactly two places:
1. A test file that enforces it
2. A one-line entry in `docs/ARCHITECTURE.md` that names the test

```markdown
# ARCHITECTURE.md

## Layer Hierarchy
Box (core/) → Lens (lens/) → Spark (spark/) → Immersion (immersion/)
Enforced by: tests/test_boundary_completeness_gate.py

## Immutability Contract
Frozen dataclasses must freeze mutable fields in __post_init__.
Enforced by: tests/test_immutability_gate.py

## State Determinism
WorldState.state_hash() uses sorted-key JSON + SHA-256.
Enforced by: tests/test_state.py::test_deterministic_hash

## Document Budget
Max 5 root .md files, 3 core docs.
Enforced by: tests/test_document_budget.py
```

If a constraint doesn't have a "enforced by" line with a real test file, it is not a constraint. It is a wish.

### The Automated Gate: Constraint Coverage Test

```python
# tests/test_architecture_coverage.py
"""Verify every constraint in ARCHITECTURE.md has an enforcing test."""

import pathlib
import re
import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
ARCH_FILE = PROJECT_ROOT / "docs" / "ARCHITECTURE.md"

def test_all_constraints_have_enforcing_tests():
    """Every 'Enforced by:' reference must point to a real test file."""
    if not ARCH_FILE.exists():
        pytest.skip("ARCHITECTURE.md not yet created")

    content = ARCH_FILE.read_text(encoding="utf-8")
    enforced_refs = re.findall(r"Enforced by:\s*(.+)", content)

    missing = []
    for ref in enforced_refs:
        # Extract test file path (before :: if present)
        test_path = ref.strip().split("::")[0].strip()
        full_path = PROJECT_ROOT / test_path
        if not full_path.exists():
            missing.append(ref.strip())

    if missing:
        pytest.fail(
            f"ARCHITECTURE.md references non-existent test files: {missing}"
        )

def test_no_unenforced_constraints():
    """Every constraint section must have an 'Enforced by:' line."""
    if not ARCH_FILE.exists():
        pytest.skip("ARCHITECTURE.md not yet created")

    content = ARCH_FILE.read_text(encoding="utf-8")
    sections = re.split(r"\n## ", content)

    unenforced = []
    for section in sections[1:]:  # Skip header
        title = section.split("\n")[0].strip()
        if "Enforced by:" not in section:
            unenforced.append(title)

    if unenforced:
        pytest.fail(
            f"Architectural constraints without enforcement: {unenforced}. "
            "Add a test or remove the constraint."
        )
```

### The Structural Constraint: Architecture as Code

The ideal end state is that `ARCHITECTURE.md` doesn't describe the architecture — it **indexes the tests that enforce it.** The tests themselves are the architecture. The document is just a human-readable table of contents.

This means the document can never drift from reality, because if a test is deleted or renamed, `test_architecture_coverage.py` fails.

### Execution Plan

| Step | Action | Owner | Gate |
|------|--------|-------|------|
| 1 | Write `docs/ARCHITECTURE.md` with enforcing-test references | Agent session | File exists |
| 2 | Write `tests/test_architecture_coverage.py` | Agent session | Test passes |
| 3 | Audit existing prose constraints for enforcement | Agent session | All have "Enforced by" |
| 4 | Delete any prose constraint that can't be tested | Agent session | No unenforced sections |

### What This Prevents

- Rules that exist only on paper (every rule has a test or it's deleted)
- Architecture doc drifting from reality (test verifies doc references real files)
- Agents unknowingly violating architectural rules (test suite catches violations)

---

## Solution 5: Defeating Operator Overwhelm

### The Problem (Recap)
The human operator receives volumes of technical output they can't evaluate. They can't distinguish real progress from sophisticated noise. The usual trust signals (confidence, specificity) are unreliable with AI output.

### The Organizational Structure: The Three-Line Dashboard

The human operator should never need to read more than three lines to know the project's status:

```
STATUS: GREEN | YELLOW | RED
TESTS:  5,299 passed / 7 failed (hw-gated) / 16 skipped
PLAY:   Last human playtest: 2026-02-13 — 5 issues found
```

This dashboard is generated by `scripts/audit_snapshot.py` and lives in `docs/STATE.md`. The operator runs it (or an agent runs it for them) and reads three lines. Everything else is detail they can drill into if they choose.

### The Automated Gate: Operator Dashboard Script

Extend `audit_snapshot.py` to produce a one-line summary at the top:

```
PROJECT STATUS: YELLOW (7 hw-gated failures, 0 regressions)
```

The status logic:
- **GREEN**: All tests pass (excluding known hw-gated)
- **YELLOW**: Only known hw-gated failures, no regressions
- **RED**: New failures, gate tests failing, or working tree dirty with no commit plan

### The Structural Constraint: The Operator Interface

The human operator interacts with the project through exactly four touchpoints:

```
1. PLAY THE GAME
   → python play.py
   → Report what happened (paste terminal output)

2. CHECK STATUS
   → python scripts/audit_snapshot.py
   → Read the 3-line summary at top

3. APPROVE/REJECT CHANGES
   → Agent proposes changes in structured handoff
   → Operator says yes or no
   → Operator does NOT need to understand the code

4. SET PRIORITIES
   → "Fix the spell display bug"
   → "Make the goblin fight back harder"
   → "I want to be able to heal myself"
   → Domain language, not code language
```

The operator never needs to:
- Read source code
- Understand git commands
- Evaluate architectural decisions
- Compare agent reports for contradictions

Those are the agent's job. The operator's job is to play the game and say what they want.

### The Ritual: The Playtest Loop

```
WEEKLY CADENCE:

Monday:    Agent session — implement top priority from operator's list
Tuesday:   Agent session — continue or fix issues found
Wednesday: OPERATOR PLAYS THE GAME (15 min)
           → Paste output to agent
           → "Here's what happened, here's what felt wrong"
Thursday:  Agent session — fix playtest issues
Friday:    Run audit_snapshot.py, review 3-line status
           → If GREEN: ship it (merge/push)
           → If YELLOW: acceptable, continue next week
           → If RED: emergency agent session to fix
```

The critical insight: **the operator's playtest on Wednesday is the most important event of the week.** Everything else exists to serve it.

### The Communication Protocol: Operator ↔ Agent

When the operator talks to an agent, they should use domain language:

```
GOOD (operator → agent):
"When I cast fireball, nothing happened. Fix it."
"The goblin should hit harder."
"I want to be able to heal myself."
"The status shows my character twice."

BAD (operator → agent):
"Can you refactor the event formatter to handle spell_resolution events?"
"The IntentBridge.resolve_spell() method needs to search all entities."
"Please update format_events() in play.py to add elif branches."
```

The operator describes the **experience**. The agent translates that into code changes. If the operator starts speaking in code, something has gone wrong — either the agent is leaking implementation details, or the operator is being taught to do the agent's job.

### The Reverse Protocol: Agent → Operator

When an agent reports to the operator, it must lead with experience-level language:

```
GOOD (agent → operator):
"Fixed: casting fireball now shows damage and saving throws."
"Fixed: you can target yourself with spells now."
"Play it again and tell me if it feels right."

BAD (agent → operator):
"Refactored format_events() to add spell_resolution, saving_throw,
and spell_damage event type handlers. Updated IntentBridge to search
all entities instead of filtering by opposing team."
```

The second version is useful for agent-to-agent handoffs. It is noise for the operator.

### Execution Plan

| Step | Action | Owner | Gate |
|------|--------|-------|------|
| 1 | Add 3-line summary to audit_snapshot.py output | Agent session | Script produces summary |
| 2 | Define operator's 4 touchpoints in ONBOARDING.md | Agent session | Section exists |
| 3 | Set up weekly playtest cadence | Human operator | Calendar reminder |
| 4 | Agent instructions include "lead with experience language" | Human operator | In agent prompt |
| 5 | Create VS Code launch config for one-click play | Agent session | F5 launches game |

### What This Prevents

- Operator drowning in technical detail (3-line dashboard)
- Operator not knowing when to play the game (weekly cadence)
- Agents speaking in code to a non-technical operator (communication protocol)
- Operator trying to do the agent's job (clear role separation)

---

## Solution 6: The Agent Instruction Template

All of the above solutions converge on a single artifact: **the instructions given to each agent at session start.** This is the most leveraged intervention point, because it shapes every agent's behavior for their entire session.

### The Template

```markdown
# Agent Session Instructions — AIDM Project

## Before You Do Anything

1. Run: `python scripts/verify_session_start.py`
2. Record the commit hash and test count in your first message
3. Read `SOURCES_OF_TRUTH.md` for any concept you need
4. Do NOT read previous agent reports in pm_inbox/

## While Working

5. Write code and tests, not documents
6. Every claim must have a file:line reference
7. Run tests after every significant change
8. If you create a new constraint, create a test for it

## Before You Finish

9. Run the full test suite: `python -m pytest tests/ -q --tb=short`
10. Run the snapshot: `python scripts/audit_snapshot.py`
11. Write your handoff in the 6-block format (see CONTRIBUTING.md)
12. Your handoff goes in pm_inbox/ with today's date

## Communication Rules

13. When talking to the human operator: use experience language, not code language
14. When writing handoffs for other agents: use file:line references
15. Never assert a test count without pytest output to back it up
16. Never assert a bug exists without showing the specific lines

## What NOT To Do

17. Do not create new root-level markdown files
18. Do not read other agents' reports as source of truth
19. Do not run audits on a dirty working tree
20. Do not write governance documents
21. Do not refactor working code unless directed to
```

### Where This Lives

This template goes in `CONTRIBUTING.md` at the project root. The human operator includes a reference to it when starting any agent session: "Read CONTRIBUTING.md before starting work."

---

## Solution 7: The Bootstrap Sequence

For a new project starting from scratch with this model, here is the exact order of operations:

### Phase 0: Foundation (Before Any Code)

```
1. Create project repository
2. Create CONTRIBUTING.md with agent session instructions
3. Create SOURCES_OF_TRUTH.md (empty initially, populated as code is written)
4. Create scripts/verify_session_start.py
5. Create .vscode/launch.json with "Run Game" configuration
6. Human operator confirms: "I can run verify_session_start.py"
```

### Phase 1: First Feature (Minimal Playable Product)

```
1. Agent writes the smallest possible playable artifact
   — For a game: one command, one response, one loop
   — For a web app: one page, one button, one result
   — For a CLI tool: one input, one output
2. Human operator runs it and reports what happened
3. Agent fixes what the human reported
4. Repeat until human says "this works"
5. Commit. This is your baseline.
```

### Phase 2: First Gate Tests

```
1. Agent writes tests for the feature built in Phase 1
2. Agent writes the first automated gate test
   (whatever constraint matters most for this project)
3. Agent creates audit_snapshot.py or equivalent
4. Run snapshot. Record baseline numbers.
5. Commit. This is your gated baseline.
```

### Phase 3: Growth Loop

```
1. Human plays/uses the product
2. Human reports issues in domain language
3. Agent session: fix issues, add features
4. Agent runs tests + snapshot at end
5. Human plays/uses again
6. Repeat indefinitely
```

### Phase 4: Multi-Agent Operations (When One Agent Isn't Enough)

```
1. Establish the handoff format (6-block)
2. Add verify_session_start.py to agent instructions
3. Add SOURCES_OF_TRUTH.md with all canonical files listed
4. Add test_document_budget.py to prevent doc proliferation
5. Add test_architecture_coverage.py to enforce constraints
6. Human operator's role is now:
   — Play the product weekly
   — Set priorities
   — Approve/reject agent output
   — Run audit_snapshot.py for status
```

---

## Summary: The Complete Organizational Structure

```
HUMAN OPERATOR (The Ground Truth Sensor)
│
├── Plays the product weekly
├── Reports experience in domain language
├── Approves/rejects via 3-line dashboard
├── Sets priorities ("I want X to work")
│
├── DOES NOT: read code, evaluate architecture,
│             compare agent reports, write documents
│
AGENT FLEET (The Builders)
│
├── Session Start:
│   └── verify_session_start.py → ground truth
│
├── During Session:
│   ├── Read SOURCES_OF_TRUTH.md, not agent reports
│   ├── Write code + tests, not documents
│   └── Every claim has file:line evidence
│
├── Session End:
│   ├── pytest + audit_snapshot.py
│   └── 6-block handoff → pm_inbox/
│
AUTOMATED GATES (The Incorruptible Layer)
│
├── test_immutability_gate.py       — frozen dataclass enforcement
├── test_boundary_completeness.py   — layer import enforcement
├── test_document_budget.py         — document count enforcement
├── test_architecture_coverage.py   — constraint enforcement
├── audit_snapshot.py               — truth generation
└── verify_session_start.py         — session bootstrap

THE PRODUCT (The Only Thing That Matters)
│
├── play.py                         — the playable artifact
├── .vscode/launch.json             — one-click to run
└── Human can use it → feedback → agents fix → repeat
```

### The Feedback Loops

```
FAST LOOP (every session):
  Agent writes code → Tests pass → Agent commits

MEDIUM LOOP (weekly):
  Human plays → Reports issues → Agent fixes → Human plays again

SLOW LOOP (monthly):
  Run audit_snapshot → Compare to last month → Identify trends
  Archive stale planning docs → Review tech debt list
```

### The Single Most Important Rule

If you take nothing else from this document:

> **A project with one playable artifact and zero documents
> is healthier than a project with zero playable artifacts
> and fifty documents.**

Build the thing. Let a human touch it. Fix what they find. Everything else is overhead that must justify its existence.

---

*Written on commit `4be2881` (master), clean working tree.*
*Companion to Part 1: THESIS_AI_FLEET_ORCHESTRATION_2026_02_13.md*
