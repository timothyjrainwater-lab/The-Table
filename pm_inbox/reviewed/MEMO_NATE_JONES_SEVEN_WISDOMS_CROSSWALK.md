# MEMO: Nate B Jones Principles × Seven Wisdoms Crosswalk

**From:** Anvil (BS Buddy seat)
**To:** Slate (PM)
**Date:** 2026-02-19
**Classification:** OPS-ARCHITECTURE / GOVERNANCE
**Lifecycle:** NEW
**Source:** 7 Nate B Jones video transcripts (Tier 1), cross-referenced against DOCTRINE_09 (Seven Wisdoms)

---

## Context

Thunder observed: "I really feel like this dude was stating the seven wisdoms in his video." This memo tests that claim rigorously. We pulled 7 Tier 1 transcripts from Nate B Jones's channel and mapped every actionable principle against our Seven Wisdoms, our architecture, and our operational patterns.

**Verdict: Thunder is right.** The overlap is not accidental. Nate B Jones independently arrived at the same architectural principles from a different starting point (enterprise software factories) that we derived from D&D engine design. The convergence is strong evidence that the Seven Wisdoms are not project-specific opinions — they are engineering fundamentals.

---

## The Seven Videos Analyzed

| # | Video | Date | Core Thesis |
|---|---|---|---|
| 1 | 100 AI Agents: 6 Principles | 2025-09-23 | 6 principles for reliable multi-agent systems |
| 2 | AI Agents That Actually Work: Anthropic Pattern | 2025-12-08 | Domain memory as the moat, not agent personality |
| 3 | $500K Mistake (Front-End Composability) | 2025-12-31 | Monolith frontend kills engineering velocity |
| 4 | Long-Running AI Agents (Context Engineering) | 2025-12-09 | 9 principles for agentic context management |
| 5 | Beat the 95%: Why AI Projects Fail | 2025-09-12 | MIT study: 95% AI initiatives fail; 4 success factors |
| 6 | AI Agent Lie: Simple Fix | 2025-12-04 | Automate the edges first, not the core |
| 7 | AI Agents Backwards: Simulation Wins | 2025-07-16 | Agents as reality simulators, not just executors |

---

## Crosswalk: Nate's Principles → Our Wisdoms

### Wisdom #1: Truth first.
*"If reality says no, write 'no' and pivot to the nearest workable path."*

| Nate Principle | Video | Alignment |
|---|---|---|
| **Bounded uncertainty** — every agent must know and declare what it doesn't know | #1 (6 Principles) | EXACT MATCH. Our Oracle FactsLedger records what IS known. Named gaps (GAP-A through GAP-C) record what ISN'T. WO verdicts say ACCEPTED or REJECTED — no "maybe." |
| **Architecture validation** — "did the plan survive contact with reality?" | #5 (Beat the 95%) | EXACT MATCH. Every WO debrief answers this question. Hardware falsified CONCURRENT → we pivoted to SEQUENTIAL. That's Wisdom #1 in action. |
| **Fail fast design** — detect failure immediately, don't propagate it | #1 (6 Principles) | STRONG MATCH. Gate tests are fail-fast contracts. Preflight canary catches environment drift before the builder runs. Hooligan protocol deliberately tests failure modes. |

**Score: 3/3 principles map to Wisdom #1.**

---

### Wisdom #2: Authority must be singular per surface.
*"One thing decides, everything else renders."*

| Nate Principle | Video | Alignment |
|---|---|---|
| **Capability-based routing** — route tasks to agents based on capability, not round-robin | #1 (6 Principles) | EXACT MATCH. Zone authority pattern: zones.json is the single source. Oracle owns facts. Director owns beat selection. Lens owns prompts. No overlapping jurisdiction. |
| **Initializer agent + coding agent** — separate the "understand the domain" phase from the "write code" phase | #2 (Anthropic Pattern) | EXACT MATCH. Thunder writes specs and evaluates. Builder agents implement. Slate manages flow. Anvil researches. Aegis audits. No role overlap. |
| **Sub-agent isolation** — child agents should have scoped context, not full parent context | #4 (Context Engineering) | STRONG MATCH. Builder agents get dispatch docs, doctrine subset, and their WO scope. They don't get PM briefings, other WO histories, or Aegis memos. Scoped authority per agent. |

**Score: 3/3 principles map to Wisdom #2.**

---

### Wisdom #3: What you cannot replay, you cannot trust.
*"Determinism is your audit trail, not a preference."*

| Nate Principle | Video | Alignment |
|---|---|---|
| **Stateful intelligence** — agents must maintain and reference state across interactions | #1 (6 Principles) | EXACT MATCH. Oracle cold boot: byte-identical rebuild from content-addressed facts. Replay IS the trust mechanism. seed=42 fuzzer determinism gates. |
| **Domain memory as the moat** — the magic is in the memory scaffold, not the agent personality | #2 (Anthropic Pattern) | EXACT MATCH. Our doctrine files, contracts, schemas, and event log ARE the domain memory. Builder agents are interchangeable. The memory scaffold (Oracle + doctrine) is the moat. |
| **Context as compiled view** — context should be deterministically assembled, not ad-hoc | #4 (Context Engineering) | EXACT MATCH. WorkingSet compiler. PromptPack compiler. Canonical JSON byte-spec profile. Nothing is ad-hoc — context is compiled from stores through deterministic pipeline. |
| **Schema-driven summarization** — use structured schemas, not freeform text, for persistent memory | #4 (Context Engineering) | STRONG MATCH. 8 JSON schemas. FactsLedger entries are structured, not prose. Events have typed payloads. NarrativeBrief is the only freeform surface, and it's renderer-only (Wisdom #6). |

**Score: 4/4 principles map to Wisdom #3. Highest density of any wisdom.**

---

### Wisdom #4: Tests are contracts with teeth.
*"If a rule matters, it deserves a gate."*

| Nate Principle | Video | Alignment |
|---|---|---|
| **Continuous input validation** — validate inputs at every boundary, not just at the front door | #1 (6 Principles) | EXACT MATCH. 256 gate tests across 11 categories. No-backflow gate. Hooligan protocol (adversarial). Fuzzer (generative). Preflight canary (environment). Validator scripts for each contract. |
| **Intelligent friction** — deliberate checkpoints that slow the process to improve quality | #5 (Beat the 95%) | EXACT MATCH. Gate system IS intelligent friction. WO verdict protocol IS intelligent friction. Builder Radar compliance check IS intelligent friction. None of these slow us — they catch breaks. |
| **Holdout scenario suite** — tests the builder can't see during development | #5 (Dark Factory, via separate memo) | GAP. Already identified in MEMO_DARK_FACTORY_PATTERNS.md. Candidate WO: WO-HOLDOUT-SCENARIOS-001. |

**Score: 2/3 exact match, 1 gap already identified.**

---

### Wisdom #5: Decisions decay unless sealed.
*"Record the why, the scope, and the acceptance signal."*

| Nate Principle | Video | Alignment |
|---|---|---|
| **Tiered memory model** — working context / session / memory / artifacts, each with different persistence | #4 (Context Engineering) | EXACT MATCH. Our tiers: (1) WO dispatch = working context, (2) PM briefing = session memory, (3) doctrine files = permanent memory, (4) event log + schemas = artifacts. Four tiers, four lifetimes. |
| **Retrieval beats pinning** — don't force everything into context, retrieve when needed | #4 (Context Engineering) | STRONG MATCH. Rehydration kernel = retrieval index, not full content. Builder agents retrieve from doctrine, not from a pinned megaprompt. PM briefing points to files, doesn't copy them inline. |
| **Learning systems** — organizations that capture and apply lessons from each iteration | #5 (Beat the 95%) | EXACT MATCH. WO verdict table. Doctrine adoption protocol. Field Manuals. Debrief → findings → doctrine update pipeline. Every decision is sealed with a commit hash. |

**Score: 3/3 principles map to Wisdom #5.**

---

### Wisdom #6: Separate narration from mechanics.
*"Vibe can be free, outcomes must be provable."*

| Nate Principle | Video | Alignment |
|---|---|---|
| **Agents as reality simulators** — simulate outcomes before executing them | #7 (Simulation Wins) | STRONG MATCH. Oracle events are mechanical facts (provable). NarrativeBrief is renderer-only prose (free). Lens/Director split enforces this at architecture level. The Director SIMULATES beat selection; the engine RESOLVES mechanical truth. |
| **Digital twin universe** — build behavioral clones to test against | #7 (Simulation Wins) | DEFERRED. Already identified in MEMO_DARK_FACTORY_PATTERNS.md. Local-first architecture eliminates primary need. |
| **Automate the edges, not the core** — the core creative/judgment work stays human | #6 (Agent Lie) | EXACT MATCH. Thunder writes specs and judges outcomes (core). Builder agents handle implementation (edges). STT cleanup layer handles voice input normalization (edge). Gate tests handle validation (edge). The creative decisions — what to build, whether it's right — stay with the operator. |

**Score: 2/3 match, 1 deferred (already tracked).**

---

### Wisdom #7: Protect the operator.
*"Reduce cognitive load by turning unknowns into named gaps."*

| Nate Principle | Video | Alignment |
|---|---|---|
| **Complex health states** — binary "up/down" loses information; use graduated health indicators | #1 (6 Principles) | STRONG MATCH. STOPLIGHT system (GREEN/YELLOW/RED) for voice unknown handling. Gate stoplight (PM briefing). BURST intake queue with tiered priority. Named gaps with severity. The operator never sees raw noise — everything is pre-classified. |
| **Hybrid architectures** — combine AI automation with human judgment at decision points | #5 (Beat the 95%) | EXACT MATCH. Thunder reviews every verdict. PM briefing surfaces "Requires Operator Action" items. Builder agents don't merge without human verdict. The architecture is designed to protect Thunder's attention. |
| **Instrumentation** — measure everything so you can see what's happening | #5 (Beat the 95%) | STRONG MATCH. Gate counts, smoke test pass rates, hooligan findings, fuzzer results, canary logs, WO verdict table with commit hashes. The operator can see system health at a glance without reading code. |

**Score: 3/3 principles map to Wisdom #7.**

---

## Summary Scorecard

| Wisdom | Nate Principles Mapped | Exact Match | Strong Match | Gap |
|---|---|---|---|---|
| #1 Truth first | 3 | 2 | 1 | 0 |
| #2 Singular authority | 3 | 2 | 1 | 0 |
| #3 Replay = trust | 4 | 3 | 1 | 0 |
| #4 Tests = contracts | 3 | 2 | 0 | 1 (holdout, already tracked) |
| #5 Seal decisions | 3 | 2 | 1 | 0 |
| #6 Narration ≠ mechanics | 3 | 1 | 1 | 1 (digital twin, deferred) |
| #7 Protect the operator | 3 | 1 | 2 | 0 |
| **Total** | **22** | **13** | **7** | **2** |

**22 principles across 7 videos. 20 implemented. 2 gaps, both already tracked.**

---

## What This Means for CV Positioning

Thunder noted: "This program falls through like it should. It should line me up with the perfect little project to act as a CV."

The crosswalk validates that claim. Nate B Jones's framework represents current industry best practice for AI-assisted software development (drawn from StrongDM, Anthropic, MIT research, and enterprise-scale production systems). Our operation:

1. **Independently converged** on the same principles from a different domain (D&D engine design).
2. **Exceeds** the framework in several areas (content-addressed deterministic replay, adversarial hooligan testing, multi-architecture AI audit via Aegis).
3. **Codified the principles** as formal doctrine before encountering the framework — not retrofitted after seeing it.
4. **Demonstrates implementation depth** — 256 gate tests, 211K lines of code, 28 accepted WOs, 10 doctrine files — not just theory.

The project IS the CV. The Seven Wisdoms ARE the interview talking points. The gate system IS the evidence.

---

## New Gaps Identified (Beyond Existing Tracking)

**None.** Every actionable gap from the Nate B Jones corpus was already identified in MEMO_DARK_FACTORY_PATTERNS.md or is already implemented. This is unusual and validates our architecture's completeness.

---

## PM Action

1. **READ** this memo.
2. **NOTE** for CV/marketing positioning: the Seven Wisdoms independently converge with industry best practice. This is a defensible claim, not self-promotion.
3. **No new WOs required.** Holdout scenarios and digital twin patterns already tracked in MEMO_DARK_FACTORY_PATTERNS.md.
4. **ARCHIVE** this memo after review.

---

*Seven Wisdoms, no regret.*
