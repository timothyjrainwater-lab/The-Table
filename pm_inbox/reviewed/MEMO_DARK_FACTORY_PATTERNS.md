# MEMO: Dark Factory Patterns — Holdout Scenarios + Digital Twin

**From:** Anvil (BS Buddy seat)
**To:** Slate (PM)
**Date:** 2026-02-19
**Classification:** OPS-ARCHITECTURE
**Lifecycle:** NEW
**Source:** Industry analysis — "5 Levels of AI Coding" (Dan Shapiro framework, StrongDM Software Factory case study, METR 2025 RCT)

---

## Context

Thunder reviewed a 42-minute industry analysis covering the spectrum of AI-assisted software development (Level 0 "spicy autocomplete" through Level 5 "dark factory"). Two actionable patterns surfaced that we don't currently implement. Everything else in the framework maps to practices we already follow or exceed.

**Our current position:** We operate at Level 4-5 by this framework's definition — spec-driven, gate-tested, autonomous builder runs with outcome evaluation. The Golden Ticket, doctrine files, contracts, and gate system constitute the specification layer. WO dispatch → builder run → debrief → verdict is the factory loop. Thunder writes specs and evaluates outcomes. The machines implement.

---

## Pattern 1: Holdout Scenario Suite (RECOMMENDED)

### What It Is

StrongDM separates behavioral tests ("scenarios") from the codebase. The agent cannot see them during development. This prevents the agent from optimizing for test passage rather than correct behavior — the software equivalent of "teaching to the test."

### What We Have Now

Our gate tests (256 across 11 categories) live inside the repo. Builder agents can read them during implementation. The hooligan protocol and fuzzer are adversarial but also visible to the builder.

### What We're Missing

A holdout scenario suite — behavioral tests stored outside the builder's visible context that evaluate the builder's output after the fact. The builder builds against the spec and gates. The holdout suite verifies the output independently.

### Recommendation

1. Create a `scenarios/` directory or external location not included in builder context.
2. Scenarios describe **behavioral expectations** derived from doctrine, not implementation details.
3. Scenarios run post-build as a second verification layer, independent of the gate suite.
4. Builder agents are never given access to scenario definitions.
5. Scenario results feed into the verdict pass alongside gate results.

### Priority

**Low-medium.** Not urgent while Thunder reviews every verdict. Becomes important if/when we move to fully autonomous builder dispatch (WO dispatched → builder runs → PR lands without human review of code).

### Gate Alignment

- Wisdom #3: What you cannot replay, you cannot trust.
- Wisdom #4: Tests are contracts with teeth.
- GT v12 HL-003: Determinism in play-critical paths.

---

## Pattern 2: Digital Twin Universe (DEFERRED)

### What It Is

StrongDM built behavioral clones of every external service their software interacts with — simulated Okta, Jira, Slack, Google Docs. Agents develop against these digital twins so they never touch real production systems.

### What We Have Now

Our system is local-first by design. No external service dependencies during play. The engine assumes the network does not exist (GT v12 invariant). This means we have less need for digital twins than a cloud-dependent product.

### When It Becomes Relevant

When the product integrates with external services at the boundary:
- Discord/voice chat integration
- VTT platform interop
- Cloud save/sync (if ever)
- External content pack repositories
- Any future API surface

### Recommendation

**Defer.** Our local-first architecture eliminates the primary use case. File for future reference when external integration WOs enter the build order.

### Gate Alignment

- GT v12 K5: Local-first.
- PRS-01 P5: Offline guarantee.

---

## What We Already Do (No Action Needed)

For Slate's reference — these are practices from the Level 5 framework that we already implement:

| Framework Concept | Our Implementation |
|---|---|
| Spec-driven development | Golden Ticket v12 (548 lines), 10 doctrine files, 6 contracts, 8 JSON schemas |
| Autonomous agent builds | WO dispatch → builder agent → debrief → verdict |
| Outcome evaluation over code review | Gate count, smoke tests, canaries, fuzzer, hooligan |
| Flat org / no coordination overhead | Thunder (PO), Slate (PM), Anvil (BS Buddy), Aegis (co-PM/auditor) — no sprints, no standups, no Jira |
| External auditor | Aegis (GPT/OpenAI) — no repo access, audits via memos, independent architecture |
| Spec quality as bottleneck | Contracts with gate-tested enforcement, doctrine adoption protocol |
| J-curve avoidance | Workflow designed around AI from day one, not bolted on |

---

## PM Action

1. **READ** this memo.
2. **Evaluate** whether holdout scenario suite warrants a WO slot in the build order. Candidate name: `WO-HOLDOUT-SCENARIOS-001`.
3. **File** digital twin pattern for future reference — no action now.
4. **Archive** this memo after review.

---

*Seven Wisdoms, no regret.*
