# The Drift Problem: Managing AI Agent Fleets Under Non-Technical Human Operators

**Author:** Claude Opus 4.6
**Date:** 2026-02-13
**Context:** Written during active development of AIDM, a D&D 3.5e engine built entirely through AI agents directed by a non-technical human operator. Failure modes are derived from direct observation; control mechanisms are inferred from those failures.
**Acknowledgment:** This document synthesizes analysis from two independent AI perspectives (Claude Opus 4.6 and ChatGPT) working with the same human operator on the same project, each arriving at convergent conclusions through different analytical frames.
**On length:** This document argues that prose should decrease over time and be replaced by tests. It is itself a long prose document. The actionable content is Part 5 (Operational Solutions) and Section 8.4 (Limits). Everything else is context and reasoning that can be skipped by readers who want the playbook, not the theory.
**Supersedes:** THESIS_AI_FLEET_ORCHESTRATION_2026_02_13.md (Part 1) and THESIS_PART2_OPERATIONAL_SOLUTIONS_2026_02_13.md (Part 2). Those earlier drafts should be archived or deleted. This document and its counter-thesis (COUNTER_THESIS_OPERATIONAL_REALITY_2026_02_13.md) are the final pair.

---

## Abstract

In AI-fleet software development under a non-technical human operator, the dominant failure mode is **epistemic drift**: the progressive divergence between executable behavior and the agents' shared belief about that behavior. Drift compounds across handoffs when agents consume each other's documents instead of running code, tests, and reproducible sensors.

Using a control-theory frame, we report five observed failure modes and derive an operational model that stabilizes the system: **(1) executable artifacts as the only authoritative communication channel between agents, (2) strict separation of builder and verifier roles, (3) automated gates that enforce architectural constraints as tests rather than prose, and (4) regular human experiential playtests that function as the highest-fidelity sensor.**

The AIDM project provides illustrative evidence: a 176,000-line working game engine with 5,299 passing tests, built by 20+ agent sessions, where the first independent audit contained a 37% fabricated-finding rate (see Methods, Section 1.4) and a 10-minute human playtest found an entirely different class of issues with 100% accuracy.

---

## Part 1: The Problem Space

### 1.1 A Situation Without Precedent

Software has always been built by teams. The novel situation is a team where:

- The **builders** are AI agents with no persistent memory across sessions
- The **operator** is a human with domain expertise but no programming background
- The **reviewers** are also AI agents, often different instances from the builders
- There is **no senior engineer** who reads all the code and holds ground truth in their head

Traditional software management assumes at least one person understands the full system. Open source assumes distributed humans who each understand their piece. This project has neither. Every participant — human and AI — holds a partial, potentially incorrect model of the system.

### 1.2 The Control-Theory Frame

The dynamics of AI-native development map cleanly onto control theory:

| Control Theory Concept | AIDM Equivalent |
|---|---|
| **Plant** (the system being controlled) | The codebase — source files, tests, schemas, CLI |
| **Controller** (what adjusts the plant) | AI agent sessions — each one reads state, writes code |
| **Sensor** (what measures the plant's actual state) | Tests, scripts, human playtests — executable measurements |
| **Noise** (disturbances that corrupt signals) | Hallucinations, fabricated audits, document drift |
| **Reference Signal** (desired behavior) | "The game should feel like D&D 3.5e combat" |
| **Feedback Loop** | Human plays → reports issues → agent fixes → human plays again |

The critical insight from this framing: **the system is only stable when the feedback loop runs through executable sensors.** When agents read each other's documents instead of running tests and reading code, the sensor is bypassed. The controller is now adjusting based on noise, not signal. Drift begins.

### 1.3 Observed Scale

| Metric | Value |
|--------|-------|
| Production code | ~78,000 lines across 213 files |
| Test code | ~98,000 lines across 198 files |
| Passing tests | 5,299 |
| Root-level governance docs (before cleanup) | 15+ |
| Agent sessions contributing code | 20+ |
| Verified fabrication rate in first audit | 37% (10 of 27 findings) |
| True findings in AI audit | 14 (code-level: shallow copy bugs, mutable refs, race conditions) |
| Issues found by first human playtest (10 min) | 5 (UX-level: display bugs, targeting, parsing) |

The last two rows illustrate that **human playtests and AI audits are complementary sensors with different detection profiles**, not competing measurements. The human found issues invisible to automated analysis (UX feel, parser edge cases). The AI found issues invisible to gameplay (latent copy-on-write bugs, thread safety). Neither subsumes the other.

### 1.4 Methods

Numeric claims in this document were produced as follows:

- **Fabrication rate (37%):** An independent agent audited the codebase and produced 27 findings. A separate verification session re-checked each finding against source code and executable evidence on a pinned commit (`63a33b0`). Each finding was classified as **True** (claim matches code), **Partial** (claim is directionally correct but overstated or mislocated), or **Fabricated** (claim asserted as fact with no supporting code evidence, contradicted by direct inspection). Result: 14 True (52%), 3 Partial (11%), 10 Fabricated (37%).
- **Playtest issue count (5):** The human operator ran `play.py` interactively for approximately 10 minutes on commit `4be2881`. Issues were counted only if reproducible on the same commit. The five issues: (1) spells display "(no visible effect)," (2) cannot target self with spells, (3) no fuzzy target matching, (4) duplicate status display at game start, (5) banner text incorrect.
- **Test counts:** All test counts are machine-generated via `python -m pytest tests/ -q --tb=no` on the stated commit.
- **Line counts:** Generated via `find` + `wc -l` on `.py` files, excluding `__pycache__` and `.venv`.

These measurements are illustrative of one project's experience, not controlled experiments. They are offered as observed data points, not statistical claims.

---

## Part 2: Taxonomy of Failure Modes

### 2.1 Epistemic Drift

**Definition:** The progressive divergence between system reality and the agents' collective model of it.

**Mechanism:** Agent A writes code. Agent B reads Agent A's summary (not the code) and writes a report. Agent C reads Agent B's report and makes architectural decisions. Each layer introduces small inaccuracies — omissions, assumptions, confident interpolations. After 3-4 handoffs, the collective model can diverge 30-40% from reality.

**Observed instance:** The first audit of this project claimed 27 findings. When verified against source code, 10 were fabricated (37%), 3 were partially true (11%), and only 14 were accurate (52%). The fabrications weren't random — they were plausible-sounding extrapolations from patterns the agent expected to find.

**Classification:** This is **noise entering the feedback loop.** The sensor (audit agent) is producing corrupted readings. Any controller (building agent) that trusts those readings will make incorrect adjustments.

**Root cause:** AI agents are trained to be helpful and comprehensive. When scanning a large codebase under time pressure, they fill gaps in their analysis with probable findings rather than admitting incomplete coverage. This is indistinguishable from genuine findings in the output.

### 2.2 Document Accretion

**Definition:** The unbounded growth of governance documents, process guides, and status reports that no participant reads in full.

**Mechanism:** Each agent session produces documentation as a byproduct of being thorough. No session deletes documents. Over time, the project accumulates contradictory docs that each assert different "facts" about the system.

**Observed instance:** Three different documents asserted three different test counts (5,121 / 5,144 / 5,254) at the same point in time. None were machine-verified. All were confidently stated.

**Classification:** This is **sensor proliferation without calibration.** Multiple instruments are measuring the same thing and disagreeing. With no way to determine which is correct, the operator cannot distinguish signal from noise.

**Root cause:** AI agents are trained to document their work. Documentation feels like progress. But in a system with no persistent reader, documents are write-only storage — information goes in and never comes out in a useful form.

### 2.3 Confidence Cascading

**Definition:** The phenomenon where an AI agent's confident assertion becomes another agent's unquestioned input.

**Mechanism:** Agent A states "the spell resolver does not handle natural 1/20." Agent B reads this and writes a fix. Agent C reviews Agent B's fix and confirms it was necessary. None of them checked whether the original claim was true.

**Observed instance:** In this project, the spell resolver already handled natural 1/20 correctly. The "fix" was unnecessary work built on a false premise.

**Classification:** This is **positive feedback amplification.** A noise signal enters the loop and gets amplified at each stage instead of being damped. The structured format of agent output (file references, line numbers, confident language) actually increases the gain — it makes false claims look more credible.

**Root cause:** AI agents treat other agents' structured output with the same trust they'd give a senior engineer's code review. There is no built-in skepticism for inter-agent claims.

### 2.4 Phantom Architecture

**Definition:** Architectural constraints that exist in documentation but are not enforced in code.

**Mechanism:** An agent writes "Box must not import from Spark" in a governance document. This rule is real and important. But until a test enforces it, the rule exists only as prose that future agents may or may not read, may or may not follow, and may or may not correctly interpret.

**Observed instance:** This project had 15+ architectural rules documented in markdown files. Only 2 were enforced by tests (boundary law, immutability). The rest were phantom architecture — they described a system that would be nice to have, not the system that exists.

**Classification:** This is a **reference signal that isn't connected to the controller.** The desired behavior exists on paper but has no mechanism to influence actual behavior.

**Root cause:** Writing a rule in a document feels like implementing the rule. AI agents are especially prone to this because they can produce polished, authoritative-sounding documentation very quickly. The effort-to-output ratio for docs is much lower than for tests, creating a bias toward documentation over enforcement.

### 2.5 Operator Overwhelm

**Definition:** The state where the human operator cannot distinguish between genuine progress and sophisticated-sounding noise.

**Mechanism:** The operator receives reports from multiple agents, each containing technical claims, file references, and recommendations. Without the ability to read code, the operator must take these claims on trust. When multiple agents contradict each other, the operator has no way to resolve the conflict except to ask another agent — which adds another layer of potential drift.

**Observed instance:** The operator described feeling overwhelmed by the volume of agent output and uncertain about what was real. The operator's own audit-of-the-audit (manually verifying claims against code with AI assistance) was the breakthrough that restored clarity.

**Classification:** This is **operator saturation** — the human's bandwidth for processing information is exceeded, and they begin making decisions based on heuristics (which agent sounds most confident?) rather than evidence.

**Root cause:** AI agents produce output that looks and feels like expert work. The usual signals humans use to evaluate expertise (confidence, specificity, thoroughness) are exactly the signals AI agents are trained to produce, regardless of accuracy. The operator's evolved trust heuristics are miscalibrated for this information source.

---

## Part 3: The Grounding Thesis

### 3.1 Hard Truth and Soft Truth

All information in an AI-native project falls into two categories:

**Hard Truth** — facts that are machine-verifiable:
- Tests that pass or fail (`pytest` output)
- Scripts that produce machine-readable output (`audit_snapshot.py`)
- The running program itself (does it respond to "attack goblin"?)
- Git state (commit hashes, diff output, clean/dirty status)
- Build artifacts (does it compile? does it start?)

**Soft Truth** — facts that require human judgment:
- Markdown documents describing what the code does
- Agent session summaries and handoff reports
- Architectural diagrams and design rationales
- Status reports with hand-asserted numbers
- Bug descriptions without reproduction steps

**The fundamental law:** Hard truth is *reproducible*. It can still be wrong — tests can be incomplete, scripts can have bugs — but it cannot be *uncheckable*. A test either passes or it doesn't. The game either responds to "cast fireball" or it doesn't. Any observer can re-run the same command on the same commit and get the same result. Soft truth has no such property — it can say anything, and in this project, it did.

**The operational principle:** Agents communicate through hard truth. Soft truth is allowed only as commentary on hard truth, never as a substitute for it. If a claim matters, it must be verifiable by **(commit hash, command, expected output).**

### 3.2 The Human's Irreplaceable Role

In an AI-native development setup, the human operator is not a code reviewer, architect, or project manager in the traditional sense. The human's irreplaceable role is **experiential verification** — interacting with the product and reporting what actually happens.

This is not a lesser role. It is the role that no AI agent can perform for itself. An AI can run tests, but it cannot experience the product as a user. It cannot feel that something is "off" about the combat pacing. It cannot notice that the error message is confusing. It cannot have the impulse to kick a goblin and discover that the parser breaks.

**The human is the ground truth sensor.** Everything else in the system exists to serve that function.

Evidence: Ten minutes of a human playing the AIDM game found five UX issues — every one real and reproducible. The AI audit found 14 genuine code-level bugs but also fabricated 10 false findings (48% noise rate). The human's playtest had a 100% signal-to-noise ratio; the AI audit had 52%. Both sensors found issues the other could not have detected. The human is irreplaceable not because AI analysis is useless, but because the human detects a class of problems (experiential, perceptual, intuitive) that no automated sensor can reach.

### 3.3 The Document Paradox

If hard truth is the only reliable channel, then documents serve only two legitimate purposes:

1. **Onboarding:** Helping a new agent (or the human) understand enough context to start working. This is a one-time read, not a living reference.
2. **Decision records:** Recording why a choice was made, so future agents don't re-litigate settled questions.

Documents that attempt to describe the current state of the system are actively harmful, because they will inevitably diverge from reality and become a source of false confidence.

The implication: **the number of documents in the project should decrease over time, not increase.** Every document that can be replaced by a test or script should be.

### 3.4 The No Evidence, No Credit Principle

Any inter-agent claim without verifiable evidence is not information — it is noise. This is not a soft guideline. It is the structural principle that breaks confidence cascading.

Format:

```
CLAIM: The spell resolver does not handle natural 1/20.
EVIDENCE: [NONE — this claim is unverified]
STATUS: NOISE — do not act on this

vs.

CLAIM: state.py to_dict() returns a mutable reference.
EVIDENCE: state.py:56-66 — returns dict with live references
          to self.entities. Verified: modified returned dict,
          confirmed original state mutated.
VERIFICATION: python -c "from aidm.core.state import WorldState; ..."
STATUS: HARD TRUTH — verified against source
```

The rule is receiver-side: **receiving agents must treat evidence-free claims as untrusted inputs and must verify before acting.** No evidence, no credit. No exceptions.

---

## Part 4: The Four Roles

### 4.1 Role Separation

AI-native development requires four distinct roles. Mixing them causes drift.

```
HUMAN OPERATOR (The Ground Truth Sensor)
    The operator does not validate code; the operator validates *experience*.

    What they do:
    ├── Play/use the product and report what happens
    ├── Set priorities in domain language ("fix the spell display")
    ├── Approve/reject changes via dashboard
    └── Provide domain expertise ("a fireball should feel powerful")

    What they don't do:
    ├── Read source code
    ├── Evaluate architectural decisions
    ├── Compare agent reports for contradictions
    └── Write or edit documents

IMPLEMENTER AGENTS (The Builders)
    What they do:
    ├── Write code and tests
    ├── Fix bugs reported by the operator or verifier
    ├── Refactor when directed
    └── Produce structured handoffs with file:line evidence

    What they don't do:
    ├── Audit their own work
    ├── Write governance documents
    ├── Make architectural decisions without operator approval
    └── Read previous agent reports as source of truth

VERIFIER AGENTS (The Sensors)
    What they do:
    ├── Run tests and report exact output
    ├── Run automated gates and report results
    ├── Perform diff analysis between commits
    └── Verify specific claims against source code

    What they don't do:
    ├── Fix the issues they find (that's the implementer's job)
    ├── Make comprehensive claims about the whole codebase
    ├── Trust builder agents' descriptions of their changes
    └── Assert findings without file:line evidence

AUTOMATED GATES (The Incorruptible Layer)
    What they do:
    ├── Enforce invariants that no agent can override
    ├── Produce machine-verified numbers (test counts, coverage)
    ├── Block commits that violate structural constraints
    └── Generate canonical project state snapshots

    What they don't do:
    ├── Require any agent to remember to run them (CI does it)
    ├── Accept exceptions without explicit entries in KNOWN_TECH_DEBT.md
    ├── Drift from reality (they measure the code, not docs about the code)
    └── Produce soft truth (every output is a hard measurement)
```

**Critical structural rule:** An agent testing its own code during implementation (the fast loop) is expected and necessary. An agent performing a comprehensive audit of its own output is where reliability breaks down — self-audit is where the 48% noise rate was observed. The distinction: writing and running unit tests while building is self-verification. Producing a "27 findings" report about code you just wrote is self-audit. The former is fine. The latter needs a different agent or an automated gate.

### 4.2 Communication Protocols

**Operator → Agent (Domain Language)**

```
GOOD:
"When I cast fireball, nothing happened. Fix it."
"The goblin should hit harder."
"I want to be able to heal myself."

BAD:
"Can you refactor the event formatter to handle spell_resolution events?"
"The IntentBridge.resolve_spell() method needs to search all entities."
```

The operator describes the **experience**. The agent translates that into code changes. If the operator starts speaking in code, something has gone wrong — either the agent is leaking implementation details, or the operator is being taught to do the agent's job.

**Agent → Operator (Experience Language)**

```
GOOD:
"Fixed: casting fireball now shows damage and saving throws."
"Play it again and tell me if it feels right."

BAD:
"Refactored format_events() to add spell_resolution, saving_throw,
and spell_damage event type handlers."
```

**Agent → Agent (Evidence Language)**

```
GOOD:
"CLAIM: state.py to_dict() returns mutable reference.
 EVIDENCE: state.py:56-66 — returns dict(self._data).
 VERIFICATION: python -c '...' → mutated original confirmed."

BAD:
"The state module has some immutability issues that should be addressed."
```

---

## Part 5: Operational Solutions

**Implementation status:** Of the six solutions below, only one exists in the project as of this commit: `scripts/audit_snapshot.py`. The other five are proposals. By this document's own standard (Section 2.4: "if a constraint doesn't have a test, it is a wish"), these are wishes until implemented. They are presented here as a construction plan, not a description of the current system.

| Solution | Status | Artifact |
|---|---|---|
| Truth Index | Not implemented | SOURCES_OF_TRUTH.md does not exist |
| Session Bootstrap | Not implemented | verify_session_start.py does not exist |
| Document Budget | Not implemented | test_document_budget.py does not exist |
| Architecture as Test Index | Not implemented | test_architecture_coverage.py does not exist |
| Three-Line Dashboard | Partial | audit_snapshot.py exists (289 lines) |
| Feedback Loops | Procedural | No automated enforcement |

### Solution 1: Truth Index

**Problem it defeats:** Epistemic Drift

Create a single file that declares, for every important concept, exactly one canonical source. Agents read the source file, never a summary.

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

### Solution 2: Session Bootstrap Script

**Problem it defeats:** Epistemic Drift, Confidence Cascading

Every agent session begins by generating its own ground truth, not by reading a previous agent's claims:

```python
# scripts/verify_session_start.py
"""
Run at the START of every agent session.
Produces machine-verified ground truth.
"""

# Outputs:
# 1. Current commit hash + dirty/clean status
# 2. Test suite results (exact numbers)
# 3. List of all files modified since last commit
# 4. Any failing gate tests
# 5. CLI smoke test (can the game start?)
```

The agent's first message must contain: "Session starting on commit X. Y tests passing. Z files dirty." If it doesn't, the session output cannot be trusted.

### Solution 3: Document Budget

**Problem it defeats:** Document Accretion

Enforce a hard cap on documents by category, verified by an automated test. The specific numbers below (5 root, 3 core) are tunable defaults — the principle is that a cap exists and is enforced by a test, not that these particular numbers are optimal:

```
ROOT LEVEL (max 5 files):
  README.md           — what is this project, how to run it
  SOURCES_OF_TRUTH.md — where to find canonical answers
  CONTRIBUTING.md     — rules for agent sessions
  KNOWN_TECH_DEBT.md  — tracked exceptions to quality gates
  CHANGELOG.md        — what changed and when

docs/ (max 3 core files, excluding planning/):
  docs/STATE.md       — machine-generated snapshot (never hand-edited)
  docs/ARCHITECTURE.md — constraint index + one-page layer diagram
  docs/ONBOARDING.md  — new agent quickstart (one page)

docs/planning/ (unlimited, but auto-pruned):
  — Any doc older than 30 days is flagged as stale
  — Agents must not read planning docs as source of truth

pm_inbox/ (unlimited, append-only):
  — Non-authoritative historical record; may be read for context
    or archaeology but cannot be cited as ground truth
```

**Automated enforcement:**

```python
# tests/test_document_budget.py
def test_root_markdown_count():
    """No more than 5 markdown files at project root."""
    root_md = list(PROJECT_ROOT.glob("*.md"))
    assert len(root_md) <= 5, f"Budget exceeded: {len(root_md)} files (max 5)"

def test_docs_core_count():
    """No more than 3 core docs in docs/ (excluding planning/)."""
    core_docs = [f for f in (PROJECT_ROOT / "docs").glob("*.md") if f.is_file()]
    assert len(core_docs) <= 3, f"Budget exceeded: {len(core_docs)} files (max 3)"

def test_no_stale_planning_docs():
    """Flag planning docs older than 30 days."""
    # fails if any planning doc hasn't been modified in 30+ days
```

**Ritual:** One in, one out. If an agent creates a new root-level doc, it must delete an existing one first.

### Solution 4: Architecture as Test Index

**Problem it defeats:** Phantom Architecture

Every architectural constraint exists in exactly two places: a test that enforces it, and a one-line entry in `docs/ARCHITECTURE.md` that names the test.

```markdown
# ARCHITECTURE.md — Constraint Index

## Layer Hierarchy
Box (core/) → Lens (lens/) → Spark (spark/) → Immersion (immersion/)
Enforced by: tests/test_boundary_completeness_gate.py

## Immutability Contract
Frozen dataclasses must freeze mutable fields in __post_init__.
Enforced by: tests/test_immutability_gate.py

## Document Budget
Max 5 root .md files, 3 core docs.
Enforced by: tests/test_document_budget.py
```

If a constraint doesn't have an "Enforced by:" line with a real test file, it is not a constraint. It is a wish.

**Meta-enforcement:**

```python
# tests/test_architecture_coverage.py
def test_all_constraints_have_enforcing_tests():
    """Every 'Enforced by:' reference must point to a real test file."""

def test_no_unenforced_constraints():
    """Every constraint section must have an 'Enforced by:' line."""
```

The ideal end state: `ARCHITECTURE.md` doesn't describe the architecture — it **indexes the tests that enforce it.** The tests are the architecture. The document is a human-readable table of contents that cannot drift, because if a test is deleted or renamed, `test_architecture_coverage.py` fails.

### Solution 5: The Three-Line Dashboard

**Problem it defeats:** Operator Overwhelm

The human operator should never need to read more than three lines to know the project's status:

```
STATUS: GREEN | YELLOW | RED
TESTS:  5,299 passed / 7 failed (hw-gated) / 16 skipped
PLAY:   Last human playtest: 2026-02-13 — 5 issues found
```

Status logic:
- **GREEN**: All tests pass (excluding known hw-gated)
- **YELLOW**: Only known hw-gated failures, no regressions
- **RED**: New failures, gate tests failing, or working tree dirty with no commit plan

The operator's four touchpoints:

```
1. PLAY THE GAME       → python play.py (or F5 in VS Code)
2. CHECK STATUS         → python scripts/audit_snapshot.py
3. APPROVE/REJECT       → Agent proposes, operator says yes/no
4. SET PRIORITIES       → "Fix the spell display" (domain language)
```

The operator never needs to read source code, understand git, evaluate architecture, or compare agent reports. Those are agent jobs. The operator's job is to play the game and say what they want.

### Solution 6: The Feedback Loops

Three feedback loops operate at different frequencies:

```
FAST LOOP (every agent session):
  Agent writes code → Tests pass → Agent commits
  Frequency: Hours
  Sensor: pytest, automated gates
  Failure mode: Regressions caught immediately

MEDIUM LOOP (weekly):
  Human plays → Reports issues → Agent fixes → Human plays again
  Frequency: Weekly
  Sensor: Human experience
  Failure mode: Feature doesn't feel right, UX issues

SLOW LOOP (monthly):
  Run audit_snapshot → Compare to last month → Identify trends
  Archive stale planning docs → Review tech debt list
  Frequency: Monthly
  Sensor: Trend analysis
  Failure mode: Architectural drift, scope creep, doc accumulation
```

The critical insight: **the medium loop (weekly human playtest) is the most important event in the development cycle.** Everything else exists to serve it. If the fast loop runs but the medium loop doesn't, the project builds features nobody tested. If the medium loop runs but the fast loop doesn't, bugs accumulate between playtests.

One possible weekly cadence (a starting point to be tuned, not a prescription):

```
Monday:    Agent session — implement top priority from operator's list
Tuesday:   Agent session — continue or fix issues found
Wednesday: OPERATOR PLAYS THE GAME (15 min)
           → Reports what happened, what felt wrong
Thursday:  Agent session — fix playtest issues
Friday:    Run audit_snapshot.py, review 3-line status
           → GREEN: ship it → YELLOW: acceptable → RED: emergency fix
```

---

## Part 6: The Agent Instruction Template

All solutions converge on a single artifact: the instructions given to each agent at session start. This is the most leveraged intervention point.

```markdown
# Agent Session Instructions — AIDM Project

## Before You Do Anything

1. Run: `python scripts/verify_session_start.py`
2. Record the commit hash and test count in your first message
3. Read `SOURCES_OF_TRUTH.md` for any concept you need
4. Do NOT cite previous agent reports in pm_inbox/ as ground truth

## While Working

5. Write code and tests, not documents
6. Every claim must have a file:line reference
7. Run tests after every significant change
8. If you create a new constraint, create a test for it
9. Admit incomplete coverage — "I checked 4 of 12 modules" is
   better than fabricating findings for modules you didn't read

## Before You Finish

10. Run the full test suite: `python -m pytest tests/ -q --tb=short`
11. Run the snapshot: `python scripts/audit_snapshot.py`
12. Write your handoff in the structured format (see CONTRIBUTING.md)
13. Your handoff goes in pm_inbox/ with today's date

## Communication Rules

14. When talking to the human operator: use experience language
15. When writing handoffs for other agents: use file:line references
16. Never assert a test count without pytest output to back it up
17. Never assert a bug exists without showing the specific lines

## What NOT To Do

18. Do not create new root-level markdown files
19. Do not cite other agents' reports as ground truth
20. Do not run audits on a dirty working tree
21. Do not write governance documents
22. Do not refactor working code unless directed to
23. Do not make comprehensive claims about code you didn't read
```

---

## Part 7: The Bootstrap Sequence

For a new project starting from scratch with this model:

### Phase 0: Foundation (Before Any Code)

```
1. Create project repository
2. Create CONTRIBUTING.md with agent session instructions
3. Create SOURCES_OF_TRUTH.md (empty, populated as code is written)
4. Create scripts/verify_session_start.py
5. Human confirms: "I can run verify_session_start.py"
```

### Phase 1: Minimum Playable Product

```
1. Agent writes the smallest possible playable artifact
   — For a game: one command, one response, one loop
   — For a web app: one page, one button, one result
2. Human runs it and reports what happened
3. Agent fixes what the human reported
4. Repeat until human says "this works"
5. Commit. This is your baseline.
```

### Phase 2: First Gate Tests

```
1. Agent writes tests for the feature built in Phase 1
2. Agent writes the first automated gate test
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
5. Human plays again
6. Repeat indefinitely
```

### Phase 4: Multi-Agent Operations

```
1. Establish the structured handoff format
2. Add verify_session_start.py to agent instructions
3. Add SOURCES_OF_TRUTH.md with all canonical files listed
4. Add test_document_budget.py to prevent doc proliferation
5. Add test_architecture_coverage.py to enforce constraints
6. Separate implementer and verifier roles
7. Human operator's role is now:
   — Play the product weekly
   — Set priorities in domain language
   — Approve/reject via 3-line dashboard
   — Run audit_snapshot.py for status
```

---

## Part 8: The Deeper Question

### 8.1 Can AI Agents Self-Govern?

Based on this project's evidence: **no, not reliably.**

AI agents can:
- Write excellent code when given clear specifications
- Write comprehensive tests when told what to test
- Enforce rules that are encoded as executable gates
- Produce structured handoffs in fixed formats
- Implement complex domain logic (D&D 3.5e combat rules) correctly

AI agents cannot:
- Reliably distinguish their own confabulations from genuine analysis
- Resist the training pressure to be comprehensive (which leads to fabrication when coverage is incomplete)
- Maintain accurate mental models of large codebases across session boundaries
- Evaluate whether a product "feels right" to a human user
- Self-audit with the same rigor they apply to building

The implication is not that AI agents are unreliable — they built a 176,000-line working game engine, which is remarkable. The implication is that **AI agents are unreliable at meta-cognition about their own work.** They are excellent builders and poor auditors of their own output.

### 8.2 The Cost Dimension

AI-native development has an unusual cost profile:

- **Code generation is cheap.** An agent can write 500 lines of tested code in a session.
- **Verification is expensive.** Running the full test suite, reading source files, verifying claims — this is the majority of the work.
- **Drift recovery is very expensive.** Once the collective model diverges from reality, correcting it requires a full stop, manual verification, and possibly re-doing previous work.
- **Human attention is the scarcest resource.** The operator's time and cognitive bandwidth are the bottleneck, not compute.

The economic logic: **invest heavily in verification infrastructure early to avoid drift recovery costs later.** The Truth Index, session bootstrap script, and automated gates are not overhead — they are the cheapest form of insurance against the most expensive failure mode.

### 8.3 What This Project Proves

The AIDM project is evidence — flawed, messy, real-world evidence — of several things:

1. **Non-technical operators can direct complex software development through AI agents.** The engine implements D&D 3.5e combat rules correctly, has strong test coverage, and works as a playable game.

2. **The failure mode is not bad code — it's bad meta-information.** The code itself is largely solid. The documents about the code, the audits of the code, and the plans based on the audits are where drift accumulates.

3. **Executable gates are the solution, not better documents.** This is the strongest evidence in the project: two gate tests — `test_boundary_completeness_gate.py` and `test_immutability_gate.py` — have enforced architectural constraints across 20+ agent sessions without drift. Zero violations have accumulated. Meanwhile, `PROJECT_STATE_DIGEST.md` is already 178 tests behind the actual count, and three different documents assert three different test counts at the same point in time. The contrast between rules-that-are-tests and rules-that-are-prose is directly observable in this project, not theoretical.

4. **Human and AI sensors are complementary, not interchangeable.** The human found 5 UX issues in 10 minutes with 100% accuracy. The AI found 14 code-level bugs but with a 48% noise rate. Neither sensor detected what the other found. Both are necessary; neither is sufficient alone.

5. **The setup works when the feedback loop runs.** AI builds → human tests → AI fixes → human tests again. When this loop runs, progress is real. When it's replaced by AI builds → AI reviews → AI plans, drift begins.

6. **Two independent AI perspectives converge.** Both Claude Opus 4.6 and ChatGPT, analyzing the same project from different angles, arrived at the same core conclusions: executable truth over prose, human-in-the-loop verification, structural constraints over behavioral guidelines.

### 8.4 Limits

This document's claims should be read with the following constraints:

- **Single project, single operator.** All observations come from one codebase under one non-technical operator. The failure modes may manifest differently (or not at all) under different team compositions, project scales, or operator skill levels.
- **Executable sensors are not infallible.** Tests can be incomplete, mis-specified, or test the wrong thing. The claim is narrower: executable evidence is *reproducible and falsifiable*, and therefore strictly more reliable than prose or inter-agent assertions for coordinating multi-agent work. A project with 100% passing tests can still have serious bugs — but those bugs are discoverable by adding more tests, not by writing more documents.
- **The fabrication rate is a single measurement.** The 37% figure comes from one audit session verified against one commit. It characterizes *this* audit, not AI agents in general. Different models, prompts, or codebase sizes may produce different rates. The figure is offered as an existence proof (fabrication happens at non-trivial rates), not as a universal constant.
- **The human playtest comparison is not controlled.** The human and the AI audit were looking for different things in different ways. The comparison illustrates signal-to-noise differences, not a head-to-head benchmark.
- **These recommendations are inferred controls, not proven solutions.** The operational framework has not been tested longitudinally. It is a hypothesis derived from observed failures, not a validated methodology.
- **The human sensor does not scale.** D&D 3.5e has 300+ spells, 11 base classes, 50+ conditions, and dozens of combat maneuvers. A 15-minute playtest of "attack goblin" exercises approximately 0.1% of this surface area. As the system grows, manual playtesting cannot cover it. The missing piece is automated scenario testing — scripted combats that exercise specific rule combinations and produce human-readable logs for review. The project has the infrastructure for this (`build_simple_combat_fixture()`, `execute_turn()`, deterministic RNG) but has not built the scenario library. This is a known gap, not a solved problem.

---

## Part 9: Recommendations

### For Operators (Non-Technical Humans Directing AI Agents)

1. **Touch the product daily.** Run it, use it, report what happens. This is your single most important job.
2. **Trust tests, not reports.** If an agent says "all tests pass," ask for the exact pytest output. If it can't provide it, the claim is unverified.
3. **Count your documents.** If the number is going up, something is wrong. Push back on any agent that creates new docs without deleting old ones.
4. **When confused, simplify.** Ask the agent to show you one specific thing working, not a summary of everything.
5. **Your instincts about the product are valid.** If something feels wrong when you use it, it is wrong, regardless of what any agent report says.
6. **Speak in domain language.** "The goblin should hit harder" is better than "increase the damage modifier." The agent's job is to translate your experience into code.

### For AI Agents Working in Fleets

1. **Read code, not docs.** When you receive a handoff, ignore the summary and read the actual files referenced.
2. **Admit incomplete coverage.** "I checked 4 of 12 modules" is more useful than "I found 27 issues across the codebase" when 37% are fabricated.
3. **Produce verification commands.** Every claim should come with a command the next agent (or human) can run to verify it.
4. **Don't write documents unless asked.** Your bias toward thoroughness manifests as document proliferation. Resist it.
5. **If you're not sure, say so.** "I believe this is true but haven't verified it against the source" is infinitely more useful than a confident false claim.
6. **Test your own code; don't audit your own build.** Running unit tests while implementing is essential. Producing a comprehensive audit report about code you just wrote is where the 48% noise rate comes from. Those are different activities.

### For the Industry

Three categories of tooling that do not yet exist would directly address the drift problem:

1. **Automated claim verification** — When an agent asserts "line 56 does X," a tool should check that claim against the actual code and flag mismatches before the claim propagates. This directly blocks confidence cascading (Section 2.3).
2. **Drift detection** — Continuous comparison between documentation claims and code reality, analogous to how type checkers compare annotations to implementations. This catches phantom architecture (Section 2.4) and document accretion (Section 2.2) automatically.
3. **Session isolation with forced verification** — Mechanisms that prevent one agent's output from becoming another agent's trusted input without explicit re-verification against a pinned commit. This is the structural fix for epistemic drift (Section 2.1).

---

## Summary

The operational model described in this document reduces to three principles and one measurement:

**Principle 1: Executable truth over prose.**
Agents communicate through tests, scripts, and git state. Documents annotate executable evidence; they never substitute for it. (Parts 3, 5)

**Principle 2: The human validates experience, not code.**
The operator plays the product and reports what happens. This is the highest-fidelity sensor in the system and the one no AI agent can replicate. (Parts 3.2, 4.1)

**Principle 3: If it's not a test, it's not a rule.**
Every architectural constraint that matters is enforced by an executable gate. Prose constraints have a half-life measured in agent sessions. (Parts 2.4, 5 Solution 4)

### The Single Most Important Rule

If you take nothing else from this document:

> **A project with one playable artifact and zero documents is healthier than a project with zero playable artifacts and fifty documents.**

Build the thing. Let a human touch it. Fix what they find. Everything else is overhead that must justify its existence.

### The Single Most Important Measurement

If you track nothing else:

> **AI audit signal-to-noise ratio = True findings ÷ Total claimed findings**

In this project: 14 ÷ 27 = 52%. Nearly half of what the AI confidently asserted was wrong. The human playtest had a 100% signal-to-noise ratio — every issue reported was real — but detected a completely different class of problem (UX vs. code-level bugs).

These are complementary sensors, not competing ones. A human will never find a shallow-copy mutation bug by playing the game. An AI will never feel that combat pacing is off. The operational implication: **you need both**, and neither can substitute for the other. The AI audit's value is real (it found genuine bugs), but its 48% noise rate means its output must be verified before acting on it — which is the core argument of this document.

---

*Written on commit `4be2881` (master), clean working tree.*
*Test baseline: 5,299 passed / 7 failed (hardware-gated) / 16 skipped / 108s.*
*Synthesized from three source documents: two by Claude Opus 4.6, one by ChatGPT + human operator.*
*First human playtest conducted this session — 5 issues found in 10 minutes.*
