# MEMO: PM Idle Signal — "PM Is On Standby"

**From:** Builder (Opus 4.6), advisory session
**Date:** 2026-02-14
**Lifecycle:** NEW
**Supersedes:** None
**Resolves:** Operator cannot distinguish builder idle from PM idle by ear alone

---

## What

Add a second idle notification line specifically for the PM agent, distinct from the builder line.

- **Builder idle:** "Thunder, the forge is quiet."
- **PM idle:** "Thunder, PM is on standby."

Same `scripts/speak.py --signal` infrastructure, same Arbor voice. Different words so the Operator knows which terminal needs attention without looking.

---

## Why

The Operator runs multiple agents across multiple windows. The builder idle signal (Rule 22, pending) tells the Operator a builder finished. But when the PM finishes a verdict cycle and is waiting on the Operator, it sounds identical — or silent. Two distinct lines let the Operator triage by ear: forge quiet means a builder needs a new WO, PM on standby means decisions have been written and need pickup.

---

## Implementation

### 1. Rule 22 addition (extends the pending builder idle rule)

When Rule 22 is drafted into Standing Ops, include the PM variant:

```
Builder idle signal:
    echo "=== SIGNAL: REPORT_READY ===" && echo "Thunder, the forge is quiet." | python scripts/speak.py --signal

PM idle signal:
    echo "=== SIGNAL: PM_STANDBY ===" && echo "Thunder, PM is on standby." | python scripts/speak.py --signal
```

### 2. Trigger conditions (PM-specific)

- PM finishes a verdict cycle and is waiting on Operator → trigger
- PM completes rehydration and reports SYSTEM STATUS → trigger
- PM finishes drafting WOs/dispatches and has no further queued work → trigger

### 3. NOT triggered when

- PM is mid-verdict (actively reading and writing decisions)
- PM just asked a clarifying question (waiting on answer, not idle)
- Multiple signals in rapid succession (once per idle transition only)

---

## Dependencies

Same as builder idle signal — speak.py, Arbor voice, reference audio. Zero additional infrastructure.

---

## Effort

One additional line in Rule 22. Zero code changes.

---

## Retrospective (Pass 3 — Operational judgment)

- **Fragility:** This memo was superseded by MEMO_OPERATOR_RELAY_REFINEMENTS.md, which bundles this proposal with the bidirectional relay convention. Standalone memo retained in inbox root until PM verdicts the consolidated version.

- **Process feedback:** This is the third memo in this session that arrived without a retrospective section. Advisory/brainstorming memos are the most likely to skip it because the author doesn't frame the conversation as a "session" with process observations. PMIH-004 enforcement catches it regardless.

- **Methodology:** The PM idle signal is the natural companion to the builder idle signal (Rule 22). Distinct audio cues per agent role let the Operator triage by ear — a pattern that scales to any number of concurrent agents.

- **Concerns:** None beyond what the consolidated memo covers.

---

*End of memo.*
