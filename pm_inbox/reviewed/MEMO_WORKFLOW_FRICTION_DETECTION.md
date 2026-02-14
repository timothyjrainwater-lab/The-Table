# MEMO: Workflow Friction Self-Detection — Can Agents Recognize Their Own Stutters?

**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Session scope:** Research question arising from the WO_SET dispatch gap fix — how to make workflow friction self-identifying rather than operator-dependent.
**Lifecycle:** NEW

---

## Action Items (PM decides, builder executes)

1. **Assess whether this research question merits a formal RQ or a governance WO.** The question is domain-independent (methodology, not engine). It could become an RQ in the research sprint, a standalone governance WO, or a BURST entry for later. Builder executes: files the item wherever PM directs. Blocks: nothing — this is forward-looking.

2. **Decide which approach(es) to pursue.** Three approaches identified below (checkpoint assertions, briefing-as-anomaly-surface, agent friction reporting). PM selects scope. Builder executes: drafts the WO or RQ per PM's direction. Blocks: nothing immediately.

## Context

Every governance fix this session was caught the same way: the Operator observed agent workflow in real time and noticed something that didn't flow right — a stutter. The PM asking "shall I proceed?" instead of dispatching. A WO_SET archived with no dispatches produced. A builder refusing to debrief after a read-only WO. A playtest log grandfathered into persistent files.

None of these were caught by tests, naming conventions, or the agents themselves. The agents followed their instructions correctly; the instructions were incomplete or wrong. The Operator's pattern-recognition for "this doesn't flow right" was the sole detection mechanism.

The Operator's research question: **Can we design methodology so that workflow stutters are self-recognizable and flagged for resolution, rather than depending on the Operator watching every interaction?**

## Observed Failure Pattern

| Error | Detection signal | Who caught it |
|-------|-----------------|---------------|
| PM executing builder actions | PM doing non-judgment work (file moves, briefing edits) | Operator |
| Builder hesitation on dispatch | Confirmation loop where none should exist | Operator |
| Debrief refusal on read-only WO | Builder citing scope restriction to skip standing obligation | Operator (via completion report) |
| WO_SET archived without dispatches | Briefing advertising artifacts that don't exist | Operator |
| playtest_log.jsonl grandfathered | Operational data in governance space | Operator |

Common thread: these are **behavioral anomalies**, not mechanical failures. The workflow completed but didn't flow correctly. The output looked done but the process was wrong.

## Three Candidate Approaches

### Approach 1: Checkpoint Assertions at Workflow Transitions

At key transition points, agents verify preconditions before proceeding. Example: before archiving a WO_SET, check "does every approved item have a corresponding dispatch doc?"

This is what the A+B fix just implemented for the WO_SET case. The question is whether to generalize it — define checkpoint assertions for every artifact type's lifecycle transitions.

**Strength:** Catches recurrence of known failure modes with high reliability.
**Weakness:** Can only check for failure modes someone has already anticipated. Every new artifact type or transition needs someone to write the checkpoint. The failures the Operator catches are precisely the ones nobody anticipated.

### Approach 2: Briefing as Anomaly Detection Surface

Make the briefing a state machine with verifiable invariants. The Operator scans a structured surface rather than watching live workflow.

Invariants like:
- "Requires Operator Action" items must have a file in inbox root
- Every WO_SET in reviewed/ must have corresponding dispatches or explicit deferral annotation
- Blocked items must cite their blocker
- No item appears in multiple sections

**Strength:** Reduces operator detection effort from "watch everything" to "scan one page." The briefing guard from this session is already an instance of this approach.
**Weakness:** Only catches friction that manifests in the briefing. Some stutters (builder hesitation, debrief refusal) don't appear in the briefing at all — they appear in agent behavior during execution.

### Approach 3: Agent Self-Reporting of Friction

Teach agents to recognize and report friction at the moment it occurs, not retrospectively. When an agent encounters a situation where the instructions feel incomplete, ambiguous, or require an assumption — flag it immediately.

The debrief retrospective already has "Fragility" and "Process feedback" subsections. But those are written after the work is done. The friction signal exists *during* execution and may be lost or rationalized away by retrospective time.

**Strength:** This is the only approach that could catch novel failure modes without operator observation. It targets the gap between "known checkpoints" and "operator intuition."
**Weakness:** Agents don't experience friction the way humans do. When the PM asked "shall I proceed?" it didn't feel friction — it followed instructions that said to ask. The friction was in the instruction, not in the agent's experience. Current agent capabilities may not support genuine friction detection.

**Possible partial implementation:** Rather than asking agents to detect friction (which they may not be able to), define structural markers that correlate with friction:
- Agent asked a confirmation question that wasn't in the WO spec
- Agent cited a scope restriction to skip an action
- Agent completed a lifecycle transition but didn't produce the expected downstream artifact
- Agent's debrief mentions "I wasn't sure whether..." or "I assumed..."

These are grep-able signals in agent output. Not friction detection per se, but friction *proxies*.

## Assessment

The gap between "known failure modes with checkpoints" (Approach 1) and "novel failure modes only the operator can spot" (Approach 3) is where the Operator's value lives. The question is whether this gap narrows over time.

Evidence it narrows: each fix this session removed a *class* of errors, not just one instance. The dispatch authority fix prevents all future "shall I proceed?" hesitation. The decision-only principle prevents all future PM-executes-builder-action cases. Each checkpoint assertion is reusable.

Evidence it doesn't narrow: the system keeps discovering new categories of stutter. The WO_SET dispatch gap was a category that didn't exist until WO_SETs were introduced. New artifact types create new transition points create new friction opportunities.

The PM has the most direct experience with this — the dispatch gap was the PM's own process error, caught by the Operator, and the PM immediately understood the structural issue. The PM is well-positioned to assess which approaches would have helped the PM itself catch the error earlier.

## Retrospective (Pass 3 — Operational judgment)

- **Fragility:** The Operator is currently a single point of detection for workflow friction. If the Operator isn't watching when a stutter occurs, it propagates until it causes a visible downstream failure. The briefing guard (Approach 2) is the strongest near-term mitigation because it creates a persistent, scannable surface.

- **Process feedback:** The three-pass debrief's Retrospective section is the closest existing mechanism to Approach 3. Agents do sometimes report process friction there. But the signal is mixed with other observations and isn't structured for easy scanning. A dedicated "Friction" subsection in the retrospective — separate from Fragility and Process feedback — might concentrate the signal.

- **Methodology:** This question is domain-independent. It applies to any multi-agent coordination system with a human operator, not just this project. It could become a methodology pattern if a workable approach is found.

- **Concerns:** Approach 3 (agent friction self-reporting) is the most valuable but least proven. It depends on agent capabilities that may not exist yet. The risk is investing governance WO effort into designing a friction reporting system that agents can't actually use effectively. A lightweight pilot (add a "Friction" subsection to the debrief template, see what agents report) would test feasibility before committing to a full design.

---

**End of Memo**
