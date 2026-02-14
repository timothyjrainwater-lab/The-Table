# Pattern: Staged Context Loading

## Problem

LLM agents have finite context windows. When dropped into a complex project, they waste context by:
- Reading every file they can find (context exhaustion)
- Reading files in the wrong order (building understanding on unstable foundations)
- Reading stale or superseded documents (poisoning their mental model)
- Not knowing which documents exist (missing critical governance)

Result: agents start working with incomplete or incorrect understanding, producing work that has to be reverted.

## Solution

Define an explicit reading sequence that loads context in layers, from broad orientation to specific operational detail.

### The Layers

```
Layer 1: ORIENTATION
    "What is this project? What are we building?"
    → Single entry-point document (Compass/README)
    → Architecture overview, current phase, what's real vs planned

Layer 2: STATE
    "What's been done? What's the current situation?"
    → Operational state document (test counts, locked systems, active work)
    → Capability gates (what's allowed, what's blocked)

Layer 3: RULES
    "How do I work on this project?"
    → Coding standards, pitfall avoidance
    → Communication protocols, escalation procedures
    → Known tech debt (what NOT to touch)

Layer 4: TASK
    "What specifically am I doing?"
    → Work order / dispatch document
    → Referenced files specific to the task
```

### Why Order Matters

An agent that reads coding standards (Layer 3) before understanding the architecture (Layer 1) will apply rules without context. An agent that reads a work order (Layer 4) before understanding project state (Layer 2) will make assumptions that conflict with reality.

The sequence builds understanding in dependency order: you need to know what the project is before you can understand its state, you need to understand its state before its rules make sense, and you need all three before a specific task is meaningful.

## Implementation

Create a **mandatory reading checklist** as a root-level file. Format:

```markdown
# Agent Onboarding Checklist

**Read this file FIRST. Follow it step by step.**

## Step 1: Read the Governance Documents (IN THIS ORDER)

| Order | File | Purpose |
|-------|------|---------|
| 1 | `PROJECT_COMPASS.md` | Orientation — architecture, status, what's real |
| 2 | `PROJECT_STATE.md` | State — operational detail, what's done, what's active |
| 3 | `DEVELOPMENT_GUIDELINES.md` | Rules — coding standards, pitfalls |
| 4 | `COMMUNICATION_PROTOCOL.md` | Rules — how to flag concerns |
| 5 | `KNOWN_TECH_DEBT.md` | Rules — what not to touch |

## Step 2: Verify the Project Compiles
[Machine verification before any work begins]

## Step 3: Begin Your Task
[Now read the specific work order]
```

### Key Design Decisions

- **Numbered order is mandatory**, not suggested. Agents will skip ahead if given the option.
- **The checklist itself is the entry point.** It's the first file any agent reads, and it tells them exactly what to read next.
- **Keep Layer 1 to a single file.** Multiple orientation documents cause agents to piece together a mental model from fragments. One file, comprehensive, is better than three files that each cover part of the picture.
- **Machine verification (Step 2) comes before task-specific reading.** This grounds the agent in executable truth before they consume prose that might be stale.

## When to Use

- Any project with more than 3 governance/documentation files
- Any project where multiple agents will work across different sessions
- Any project where agent context windows are a binding constraint

## Real Example

The proving-ground project has 7+ root-level governance documents. Without the checklist, agents would read them in arbitrary order, often starting with the most recently modified file (which was frequently a work order, not orientation). After introducing the staged loading pattern:
- Agents oriented correctly on first try
- No more "I assumed X was the architecture" mistakes
- Context window waste dropped significantly — agents read what they need, in order

## Anti-Patterns

- **Dumping everything into a system prompt.** This uses context before the agent even starts working. Staged loading lets agents load context incrementally, spending budget on the layers relevant to their task.
- **Single giant README.** Orientation and operational state change at different rates. A 500-line README that mixes "what we're building" with "what's currently broken" becomes stale in the volatile sections while remaining correct in the stable sections. Separate layers, separate files, separate update frequencies.
- **No reading order, just "read the docs."** Agents will read in whatever order they discover files. Without an explicit sequence, the mental model they build is random.
