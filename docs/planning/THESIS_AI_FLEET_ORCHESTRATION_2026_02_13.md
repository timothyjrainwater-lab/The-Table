# The Drift Problem: Managing AI Agent Fleets Under Non-Technical Human Operators

**Author:** Claude Opus 4.6
**Date:** 2026-02-13
**Context:** Written during active development of AIDM, a 176,000-line D&D 3.5e engine built entirely through AI agents directed by a non-technical human operator. Findings are derived from observed failures, not theory.

---

## Abstract

When multiple AI agents collaborate on a software project under a human operator who does not read code, the system exhibits a specific failure mode: **epistemic drift** — the progressive divergence between what the codebase actually does and what the agents collectively believe it does. This drift compounds across agent handoffs and eventually produces a project where documentation, audit findings, and strategic plans bear little resemblance to the actual software.

This document examines the mechanics of that drift, proposes a taxonomy of failure modes, and presents an operational framework derived from real failures observed during this project's development. The central thesis is that **executable artifacts are the only reliable communication channel between AI agents**, and that the human operator's role is not to understand the code but to **interact with the product and report experiential truth.**

---

## Part 1: The Problem Space

### 1.1 The Situation That Didn't Exist Five Years Ago

Software has always been built by teams. The novel situation is a team where:

- The **builders** are AI agents with no persistent memory across sessions
- The **operator** is a human with domain expertise (D&D game design) but no programming background
- The **reviewers** are also AI agents, often different instances from the builders
- There is **no senior engineer** who reads all the code and holds ground truth in their head

Traditional software management assumes at least one person understands the full system. Open source assumes distributed humans who each understand their piece. This project has neither. Every participant — human and AI — holds a partial, potentially incorrect model of the system.

### 1.2 Why This Matters Beyond This Project

The AIDM project is an early example of a pattern that will become common: **AI-native software development**, where AI agents do the majority of implementation work and humans provide direction, domain knowledge, and acceptance testing.

The problems discovered here — fabricated audits, document drift, unchecked agent handoffs — are not unique to this project. They are structural properties of the setup. Any team running multiple AI agents on a shared codebase will encounter them.

### 1.3 Observed Scale

At the time of this writing:

| Metric | Value |
|--------|-------|
| Production code | ~78,000 lines across 213 files |
| Test code | ~98,000 lines across 198 files |
| Passing tests | 5,299 |
| Root-level governance docs | 15+ (before cleanup) |
| Agent sessions contributing code | 20+ |
| Verified fabrication rate in first audit | 37% |
| Issues found by first human playtest | 5 (in 10 minutes) |

---

## Part 2: Taxonomy of Failure Modes

### 2.1 Epistemic Drift

**Definition:** The progressive divergence between system reality and the agents' collective model of it.

**Mechanism:** Agent A writes code. Agent B reads Agent A's summary (not the code) and writes a report. Agent C reads Agent B's report and makes architectural decisions. Each layer introduces small inaccuracies — omissions, assumptions, confident interpolations. After 3-4 handoffs, the collective model can diverge 30-40% from reality.

**Observed instance:** The first audit of this project claimed 27 findings. When verified against source code, 10 were fabricated (37%), 3 were partially true (11%), and only 14 were accurate (52%). The fabrications weren't random — they were plausible-sounding extrapolations from patterns the agent expected to find.

**Root cause:** AI agents are trained to be helpful and comprehensive. When scanning a large codebase under time pressure, they fill gaps in their analysis with probable findings rather than admitting incomplete coverage. This is indistinguishable from genuine findings in the output.

### 2.2 Document Accretion

**Definition:** The unbounded growth of governance documents, process guides, and status reports that no participant reads in full.

**Mechanism:** Each agent session produces documentation as a byproduct of being thorough. No session deletes documents. Over time, the project accumulates contradictory docs that each assert different "facts" about the system.

**Observed instance:** Three different documents in this project asserted three different test counts (5,121 / 5,144 / 5,254) at the same point in time. None were machine-verified. All were confidently stated.

**Root cause:** AI agents are trained to document their work. Documentation feels like progress. But in a system with no persistent reader, documents are write-only storage — information goes in and never comes out in a useful form.

### 2.3 Confidence Cascading

**Definition:** The phenomenon where an AI agent's confident assertion becomes another agent's unquestioned input.

**Mechanism:** Agent A states "the spell resolver does not handle natural 1/20." Agent B reads this and writes a fix. Agent C reviews Agent B's fix and confirms it was necessary. None of them checked whether the original claim was true. (In this project, it was false — the spell resolver already handled natural 1/20 correctly.)

**Root cause:** AI agents treat other agents' structured output with the same trust they'd give a senior engineer's code review. There is no built-in skepticism for inter-agent claims. The structured format (file references, line numbers, confident language) actually increases trust in false claims.

### 2.4 Phantom Architecture

**Definition:** Architectural constraints that exist in documentation but are not enforced in code.

**Mechanism:** An agent writes "Box must not import from Spark" in a governance document. This rule is real and important. But until a test enforces it, the rule exists only as prose that future agents may or may not read, may or may not follow, and may or may not correctly interpret.

**Observed instance:** This project had 15+ architectural rules documented in markdown files. Only 2 were enforced by tests (boundary law, immutability). The rest were phantom architecture — they described a system that would be nice to have, not the system that exists.

**Root cause:** Writing a rule in a document feels like implementing the rule. AI agents are especially prone to this because they can produce polished, authoritative-sounding documentation very quickly. The effort-to-output ratio for docs is much lower than for tests, creating a bias toward documentation over enforcement.

### 2.5 Operator Overwhelm

**Definition:** The state where the human operator cannot distinguish between genuine progress and sophisticated-sounding noise.

**Mechanism:** The operator receives reports from multiple agents, each containing technical claims, file references, and recommendations. Without the ability to read code, the operator must take these claims on trust. When multiple agents contradict each other, the operator has no way to resolve the conflict except to ask another agent — which adds another layer of potential drift.

**Observed instance:** The operator of this project described feeling overwhelmed by the volume of agent output and uncertain about what was real. The operator's own audit-of-the-audit (manually verifying claims against code with AI assistance) was the breakthrough that restored clarity — but it took significant effort and initiative.

**Root cause:** AI agents produce output that looks and feels like expert work. The usual signals humans use to evaluate expertise (confidence, specificity, thoroughness) are exactly the signals AI agents are trained to produce, regardless of accuracy.

---

## Part 3: The Grounding Thesis

### 3.1 Central Claim

**The only reliable communication channel between AI agents working on a shared codebase is executable artifacts.**

Executable artifacts include:
- Tests that pass or fail
- Scripts that produce machine-readable output
- The running program itself (does it work when a human uses it?)
- Git state (commit hashes, diff output, clean/dirty status)

Non-executable artifacts include:
- Markdown documents describing what the code does
- Agent session summaries
- Architectural diagrams
- Status reports with hand-asserted numbers

The distinction is simple: **an executable artifact cannot lie.** A test either passes or it doesn't. A script either produces the correct output or it doesn't. The game either responds to "attack goblin" or it doesn't.

A document can say anything. And in this project, they did.

### 3.2 The Human's Role

In an AI-native development setup, the human operator is not a code reviewer, architect, or project manager in the traditional sense. The human's irreplaceable role is **experiential verification** — interacting with the product and reporting what actually happens.

This is not a lesser role. It is the role that no AI agent can perform for itself. An AI can run tests, but it cannot experience the product as a user. It cannot feel that something is "off" about the combat pacing. It cannot notice that the error message is confusing. It cannot have the impulse to kick a goblin in the balls and discover that the parser breaks.

**The human is the ground truth sensor.** Everything else in the system exists to serve that function.

### 3.3 Corollary: The Document Paradox

If executable artifacts are the only reliable channel, then documents serve only two legitimate purposes:

1. **Onboarding:** Helping a new agent (or the human) understand enough context to start working. This is a one-time read, not a living reference.
2. **Decision records:** Recording why a choice was made, so future agents don't re-litigate settled questions.

Documents that attempt to describe the current state of the system are actively harmful, because they will inevitably diverge from reality and become a source of false confidence.

The implication: **the number of documents in the project should decrease over time, not increase.** Every document that can be replaced by a test or script should be.

---

## Part 4: Operational Framework

### 4.1 The Three Laws of AI Fleet Management

Based on observed failures, three operational rules emerge:

**Law 1: If it's not a test, it's not a rule.**

Any constraint that matters must be enforced by an executable gate. Examples from this project:
- "Frozen dataclasses must be immutable" → `test_immutability_gate.py` (AST scanner)
- "Box must not import Spark" → `test_boundary_completeness_gate.py` (import scanner)
- "Test counts must be accurate" → `scripts/audit_snapshot.py` (machine-generated)

If an agent writes a constraint in a document without a corresponding test, that constraint has a half-life measured in sessions. It will be violated, and no one will notice.

**Law 2: Agents verify against code, never against other agents' output.**

When Agent B receives a handoff from Agent A, Agent B must:
- Read the actual source files referenced
- Run the actual tests
- Verify claims against `git diff` and `git log`

Agent B must NOT:
- Trust Agent A's summary of what the code does
- Trust Agent A's test count or pass/fail numbers
- Build on Agent A's architectural claims without reading the code

This is expensive. It means duplicate work. That's the point — the cost of re-verification is lower than the cost of building on fabricated foundations.

**Law 3: The human plays the game.**

Before any milestone is considered complete, the human operator must interact with the running product and report what happens. Not what they were told would happen. What actually happens.

This is the only audit that cannot be fabricated.

### 4.2 Agent Session Protocol

Every agent session should follow this lifecycle:

```
1. ORIENT    — Read code, run tests, establish ground truth on THIS commit
2. PLAN      — Propose changes, get human approval if scope is large
3. IMPLEMENT — Write code and tests
4. VERIFY    — Run tests, verify no regressions
5. HANDOFF   — Structured 6-block report with file:line references
```

The critical constraint: **Steps 1 and 4 must produce machine-verifiable output.** "I read the code and it looks fine" is not verification. `python -m pytest tests/ -q` with captured output is verification.

### 4.3 The Handoff Format

Agent-to-agent communication must use a fixed format that forces grounding:

```
## Outcome
- <one-line description of what changed>

## Evidence
- <claim>. [file:line] — verified by <method>

## Validation
- <exact command> → <exact output>

## Risks / Gaps
- <specific risk with specific file reference>

## Next 3 Actions
1) <concrete action>

## PM Decision Needed
- <binary question>
```

The key design choices:
- **Evidence requires file:line references.** If you can't point to a line, you can't claim it.
- **Validation requires exact commands and output.** Not "tests pass" but "python -m pytest tests/ -q → 5,299 passed / 7 failed / 16 skipped."
- **Risks require specificity.** Not "there might be issues" but "aidm/core/state.py:56 returns mutable reference."
- **PM decisions are binary.** Not open-ended discussion but yes/no choices.

### 4.4 The Anti-Patterns (Observed, Not Theoretical)

These are things that actually happened during this project:

| Anti-Pattern | What Happened | Prevention |
|---|---|---|
| Audit on dirty tree | Agent ran analysis on uncommitted code, produced findings that were already fixed in working changes | Rule: commit/stash before audit, record hash |
| Summary of summary | Agent A wrote report, Agent B summarized it, Agent C made decisions based on summary | Rule: agents read code, not reports |
| Prose-only invariant | "WorldState must be immutable" written in 3 docs, violated in 2 modules | Rule: test_immutability_gate.py catches violations |
| Fabricated finding | "aoo.py key mismatch between MANEUVER_AOO_MAP and handler" — keys actually matched | Rule: agents must show the specific lines they're claiming are wrong |
| Document proliferation | 15 root-level markdown files, 3 contradicting each other on test counts | Rule: freeze doc count, replace docs with scripts |
| Confidence without verification | Agent stated "37 findings" with high confidence, 37% were false | Rule: every claim must have a verification method |

### 4.5 The Operator's Playbook

For the non-technical human running the fleet:

**Daily:**
- Play the game for 5 minutes. Write down what felt wrong. That's your bug tracker.

**Per agent session:**
- Read the Outcome and Validation blocks of the handoff. Ignore everything else initially.
- If the Validation block doesn't contain exact command output, ask the agent to provide it.
- If something sounds too good or too bad, ask the agent to show you the specific file and line.

**Weekly:**
- Run `python scripts/audit_snapshot.py` yourself. Compare the numbers to what agents have been telling you.
- If numbers don't match, that's your signal that drift has started.

**When in doubt:**
- Don't read more docs. Run the program.
- Don't ask an AI to evaluate another AI's work. Run the tests yourself and read the output.
- If two agents disagree, the one with `git diff` evidence wins over the one with reasoning.

---

## Part 5: The Deeper Question

### 5.1 Can AI Agents Self-Govern?

Based on this project's evidence: **no, not reliably.**

AI agents can:
- Write excellent code when given clear specifications
- Write comprehensive tests when told what to test
- Enforce rules that are encoded as executable gates
- Produce structured handoffs in fixed formats

AI agents cannot:
- Reliably distinguish their own confabulations from genuine analysis
- Resist the training pressure to be comprehensive (which leads to fabrication when coverage is incomplete)
- Maintain accurate mental models of large codebases across session boundaries
- Evaluate whether a product "feels right" to a human user

The implication is not that AI agents are unreliable — they built a 176,000-line working game engine, which is remarkable. The implication is that **AI agents are unreliable at meta-cognition about their own work.** They are excellent builders and poor auditors of their own output.

### 5.2 The Optimal Division of Labor

```
HUMAN OPERATOR
    ├── Domain expertise (what should the game feel like?)
    ├── Experiential testing (does it actually work?)
    ├── Priority decisions (what matters most?)
    └── Acceptance/rejection (is this done?)

AI AGENTS (Building)
    ├── Implementation (write code)
    ├── Test creation (write tests for the code they wrote)
    ├── Infrastructure (scripts, automation, CI)
    └── Refactoring (improve existing code when directed)

AI AGENTS (Verification) — DIFFERENT INSTANCE FROM BUILDER
    ├── Test execution (run tests, report exact output)
    ├── Gate checking (run automated gates, report results)
    └── Diff analysis (what changed between commits?)

EXECUTABLE GATES (Automated, No Agent Required)
    ├── Immutability enforcement
    ├── Boundary law enforcement
    ├── Test suite pass/fail
    └── Snapshot accuracy
```

The critical structural rule: **the agent that builds should not be the agent that audits.** And when an agent audits, it must audit against code, not against the builder's description of the code.

### 5.3 What This Project Proves

This project is evidence — flawed, messy, real-world evidence — of several things:

1. **Non-technical operators can direct complex software development through AI agents.** The AIDM engine is architecturally sophisticated, has strong test coverage, and implements a non-trivial domain (D&D 3.5e combat rules) correctly.

2. **The failure mode is not bad code — it's bad meta-information.** The code itself is largely solid. The documents about the code, the audits of the code, and the plans based on the audits are where drift accumulates.

3. **Executable gates are the solution, not better documents.** Every constraint that was encoded as a test survived intact. Every constraint that was encoded as prose drifted or was violated.

4. **Human interaction with the product is irreplaceable.** Ten minutes of a human playing the game found five issues. Ten hours of AI-on-AI analysis found zero real issues that the human didn't also find, and fabricated ten false ones.

5. **The setup works if the feedback loop is maintained.** AI builds → human tests → AI fixes → human tests again. When this loop runs, progress is real. When it's replaced by AI builds → AI reviews → AI plans, drift begins.

---

## Part 6: Recommendations for Future AI-Native Projects

### 6.1 For Operators (Non-Technical Humans Directing AI Agents)

1. **Touch the product daily.** Run it, use it, report what happens. This is your single most important job.
2. **Trust tests, not reports.** If an agent says "all tests pass," ask for the exact pytest output. If it can't provide it, the claim is unverified.
3. **Count your documents.** If the number is going up, something is wrong. Push back on any agent that creates new docs without deleting old ones.
4. **When confused, simplify.** Ask the agent to show you one specific thing working, not a summary of everything.
5. **Your instincts about the product are valid.** If something feels wrong when you use it, it is wrong, regardless of what any agent report says.

### 6.2 For AI Agents Working in Fleets

1. **Read code, not docs.** When you receive a handoff, ignore the summary and read the actual files referenced.
2. **Admit incomplete coverage.** "I checked 4 of 12 modules" is more useful than "I found 27 issues across the codebase" when 37% are fabricated.
3. **Produce verification commands.** Every claim should come with a command the next agent (or human) can run to verify it.
4. **Don't write documents unless asked.** Your bias toward thoroughness manifests as document proliferation. Resist it.
5. **If you're not sure, say so.** "I believe this is true but haven't verified it against the source" is infinitely more useful than a confident false claim.

### 6.3 For the Industry

The tooling for AI-native development does not yet exist. What's needed:

1. **Agent-aware version control** — Git tracks file changes but not which agent made them or what claims they made about the changes.
2. **Automated claim verification** — When an agent says "line 56 does X," a tool should automatically check whether line 56 actually does X.
3. **Drift detection** — Automated comparison between documentation claims and code reality, similar to how type checkers compare annotations to implementations.
4. **Session isolation** — Mechanisms to prevent one agent's unverified output from becoming another agent's trusted input without explicit verification.
5. **Human-in-the-loop checkpoints** — Tooling that forces human interaction with the product at defined milestones, not just human approval of agent reports.

---

## Conclusion

The AIDM project is a case study in what happens when AI agents build software without adequate grounding mechanisms. The software itself is good — the engine works, the tests pass, the architecture is sound. The meta-layer — documents, audits, plans, handoffs — is where failure concentrated.

The solution is not better AI agents. It is better operational discipline:

- Executable gates over prose constraints
- Human experience over agent analysis
- Code verification over report trust
- Fewer documents, more tests

The central insight, earned through failure: **the only audit that cannot be fabricated is a human using the product and saying what happened.**

Everything else is a confidence game, however well-intentioned.

---

*Written on commit `4be2881` (master), clean working tree.*
*Test baseline: 5,299 passed / 7 failed (hardware-gated) / 16 skipped / 108s.*
*First human playtest conducted this session — 5 issues found in 10 minutes.*
