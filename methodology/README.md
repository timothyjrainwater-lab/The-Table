# Multi-Agent LLM Coordination Framework

**A practical methodology for coordinating multiple AI agents on complex software projects.**

Built and proven on a 5,100+ test, 338-formula deterministic game engine — by a non-technical operator (former chef, English educator) coordinating Claude, GPT, and other LLM agents with zero shared memory.

---

## The Problem

When you use multiple LLM agents to build software, you hit walls that don't exist in solo development:

- **Agents forget everything between sessions.** Every new context window starts from zero.
- **Parallel agents conflict.** Two sessions editing the same file produce merge disasters.
- **Nobody holds the full picture.** No single agent (or human) can keep the entire project in context.
- **Documents drift from reality.** Agent-written docs become stale, contradictory, and self-reinforcing.
- **The human coordinator becomes the bottleneck.** You can't read everything, and you can't tell which agent is right when they disagree.

These aren't theoretical problems. They're what happens on Day 3 of any serious multi-agent project. This framework documents the solutions we discovered by breaking things and codifying the fixes.

---

## Who This Is For

- **Non-technical builders** using AI agents to construct software ("vibe coders")
- **Developers** scaling from one AI assistant to a fleet of specialized agents
- **Researchers** studying multi-agent LLM coordination
- Anyone who has had an AI agent confidently break something another agent just fixed

---

## Core Principles

### 1. Artifact Primacy
> If it's not in a file, it doesn't exist.

Agents have perfect recall within a context window and zero recall across context boundaries. Conversational knowledge vanishes at session end. Every fact, decision, and status that must survive a context rotation must be pinned to a file.

**Implication:** Your project's files aren't just code and docs — they're the only shared memory your agent fleet has.

### 2. Staged Context Loading
> Reading order matters more than reading volume.

Agents waste context window space when they read files in the wrong order or read everything at once. A defined reading sequence — orientation first, then state, then rules — gets agents operational in minimal context.

**Pattern:** Compass (what is this?) → State (what's done?) → Rules (how do we work?) → Task (what do I do?)

### 3. Dispatch Self-Containment
> Every work order must be executable by an agent with zero prior context.

The work order plus the files it references must contain everything an agent needs. No reliance on "the previous agent will have explained this." Test: could a brand-new agent execute this dispatch using only the dispatch file and linked references?

### 4. Machine Truth Over Prose Truth
> When a script and a document disagree, the script is right.

Agent-written prose drifts from reality within 3-4 handoffs. Machine-generated state (test counts, git status, automated snapshots) doesn't. Build scripts that produce canonical facts, and treat everything else as commentary.

### 5. Protocol Over Memory
> Solve coordination with protocols, not shared state.

You can't give agents shared memory. You can give them protocols — handoff checklists, consistency gates, session scope declarations, structured memo formats. The protocols are the coordination mechanism.

---

## Framework Components

### Patterns
Reusable solutions to specific coordination problems. Each pattern documents the problem, the solution, when to use it, and a real example from the proving ground.

| Pattern | Problem It Solves | File |
|---------|------------------|------|
| [Staged Context Loading](patterns/STAGED_CONTEXT_LOADING.md) | Agents waste context reading files in wrong order | How to build a reading sequence that orients agents efficiently |
| [Dispatch Self-Containment](patterns/DISPATCH_SELF_CONTAINMENT.md) | Work orders fail because agents lack context | How to write work orders amnesiac agents can execute |
| [Artifact Primacy](patterns/ARTIFACT_PRIMACY.md) | Knowledge lost between sessions | How to ensure decisions survive context boundaries |
| [Cross-File Consistency Gate](patterns/CROSS_FILE_CONSISTENCY.md) | Partial updates create contradictions | How to enforce all-or-nothing updates |
| [Session Bootstrap](patterns/SESSION_BOOTSTRAP.md) | Agents start with stale assumptions | How to ground agents in machine-verified truth |
| [Concurrent Session Protocol](patterns/CONCURRENT_SESSION_PROTOCOL.md) | Parallel sessions conflict on shared files | How to manage file ownership across sessions |
| [PM Context Compression](patterns/PM_CONTEXT_COMPRESSION.md) | Human coordinator can't read everything | How to structure information flow to a bandwidth-limited human |
| [Coordination Failure Taxonomy](patterns/COORDINATION_FAILURE_TAXONOMY.md) | Same mistakes repeat across projects | Categorized catalog of what goes wrong and why |

### Templates
Ready-to-use file templates for implementing the patterns in your own project.

| Template | Purpose | File |
|----------|---------|------|
| [Onboarding Checklist](templates/ONBOARDING_CHECKLIST_TEMPLATE.md) | Reading order + verification steps for new agents | Implements Staged Context Loading |
| [Work Order Dispatch](templates/WORK_ORDER_TEMPLATE.md) | Self-contained task assignment | Implements Dispatch Self-Containment |
| [Handoff Document](templates/HANDOFF_TEMPLATE.md) | End-of-session knowledge transfer | Implements Artifact Primacy |
| [Session Memo](templates/SESSION_MEMO_TEMPLATE.md) | Structured report to human coordinator | Implements PM Context Compression |
| [Sources of Truth Index](templates/SOURCES_OF_TRUTH_TEMPLATE.md) | Which file is authoritative for which concept | Implements Machine Truth Over Prose |

### Case Study
How these patterns were discovered and proven on a real project.

| Document | Content |
|----------|---------|
| [Project Overview](case-study/PROJECT_OVERVIEW.md) | What was built, by whom, scale and complexity |
| [Failure Catalog](case-study/FAILURE_CATALOG.md) | Real coordination failures, categorized with root causes |
| [Metrics](case-study/METRICS.md) | Quantitative results — formulas verified, bugs found, reclassification rates |
| [Lessons Learned](case-study/LESSONS_LEARNED.md) | What worked, what didn't, what we'd do differently |

---

## Quick Start

If you're starting a multi-agent project today:

1. **Create an onboarding checklist** ([template](templates/ONBOARDING_CHECKLIST_TEMPLATE.md)) — this is the single highest-impact intervention. Define what agents read, in what order.

2. **Create a sources of truth index** ([template](templates/SOURCES_OF_TRUTH_TEMPLATE.md)) — before your second session, decide which file is authoritative for each concept.

3. **Write self-contained work orders** ([template](templates/WORK_ORDER_TEMPLATE.md)) — the moment you start dispatching tasks to agents, the dispatch must stand alone.

4. **Add a session bootstrap script** ([pattern](patterns/SESSION_BOOTSTRAP.md)) — even a simple script that prints git status + test count grounds the agent in reality instead of potentially-stale docs.

5. **Use handoff documents** ([template](templates/HANDOFF_TEMPLATE.md)) — when a session ends, write what the next agent needs to know. This is not optional.

---

## Origin

This framework wasn't designed top-down. It was discovered bottom-up by a non-technical operator coordinating multiple AI agents (Claude Opus, Claude Sonnet, GPT-4) to build a D&D 3.5e deterministic referee engine. Every pattern exists because something broke and the fix got codified into a protocol.

**Project stats at time of extraction:**
- 5,100+ automated tests
- 338 formulas verified against source rules
- 30 bugs found and categorized into 8 error patterns
- 9 verification domains completed
- 7+ governance documents, each born from a specific failure
- Multiple concurrent agent sessions coordinated through file-based protocols

**The operator's background:** Former chef, current English educator, zero programming experience. The methodology emerged because protocols were the only tool available — and it turns out protocols are the right tool for coordinating agents that can't remember yesterday.

---

## Contributing

This is a living framework. If you're using these patterns on your own multi-agent project, your failure cases and solutions make the framework better. Open an issue with:
- What pattern you tried
- What worked or didn't
- What coordination failure you hit that isn't in the taxonomy

---

## License

[Choose your license — MIT recommended for maximum adoption]

---

*"Creative in voice, strict in truth, accountable in every outcome."*
