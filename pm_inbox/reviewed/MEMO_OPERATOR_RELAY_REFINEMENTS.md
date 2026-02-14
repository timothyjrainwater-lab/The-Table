# MEMO: Operator Relay Refinements — PM Idle Signal + Bidirectional Relay

**From:** Builder (Opus 4.6), advisory session
**Date:** 2026-02-14
**Lifecycle:** NEW
**Bundles:** MEMO_PM_IDLE_SIGNAL (PM idle audio cue) + bidirectional relay convention (PM→Builder relay blocks)

---

## Action Items (PM decides, builder executes)

1. **PM idle signal — accept/modify/reject.** Add a PM-specific idle line to Rule 22: "Thunder, PM is on standby." Same speak.py infrastructure, distinct wording so the Operator can triage by ear (forge quiet = builder idle, PM on standby = PM idle). Builder executes: add PM variant to Standing Ops Rule 22 + rehydration copy. Blocks: nothing (builder idle signal already live).

2. **Bidirectional relay convention — accept/modify/reject.** When the PM writes a verdict that the Operator will relay to a builder, the PM outputs the verdict in a fenced code block so the Operator can one-click copy-paste it into the builder's context window. Same principle as the builder→PM relay block, applied in reverse. Builder executes: add PM→Builder relay convention to README (PM Verdict Protocol), Standing Ops (PM Behavior section), and kernel. Blocks: nothing.

## Status Updates (Informational only)

- Rule 22 (builder idle notification) is already live — committed as `f26e2c7`. Standing Ops, rehydration copy, and Agent Dev Guidelines all updated.
- Builder→PM relay block convention is already codified and corrected to one-line pointer format — committed as `6a85e85`.
- The relay convention now covers one direction (builder→PM). This memo proposes completing the loop (PM→builder).

## Deferred Items (Not blocking, act when convenient)

- The PM idle signal trigger conditions need PM input: should it fire after every verdict cycle, or only when the PM has no further queued work? The builder version is clear (WO complete + report delivered + nothing queued). The PM equivalent may be more nuanced since the PM often has multiple items to verdict in sequence.

## Retrospective (Pass 3 — Operational judgment)

- **Fragility:** The bidirectional relay convention is a Tier 3 (prose-enforced) rule for the PM side, just like it is for the builder side. The PM must read and follow the instruction in the kernel or Standing Ops. Unlike builder relay blocks (which can potentially be tested by scanning chat output patterns), PM relay blocks depend entirely on the PM reading the instruction during rehydration.

- **Process feedback:** The PM idle signal proposal (MEMO_PM_IDLE_SIGNAL) was created without a retrospective — PMIH-004 violation caught during this session. This is the second memo in this session that arrived without one. The pattern suggests that memos originating from advisory/brainstorming conversations (as opposed to WO execution) are more likely to skip the retrospective because the author doesn't think of it as a "session" with process observations. The template and enforcement exist precisely for this case.

- **Methodology:** The bidirectional relay is the natural completion of the relay block pattern. The original convention only covered builder→PM because that's the direction where context waste was first observed. But the Operator relays in both directions — PM verdicts flow to builders just as builder memos flow to the PM. Applying the same one-click principle in both directions makes the Operator's relay job symmetric and predictable.

- **Concerns:** Adding relay obligations to the PM increases PM cognitive load during verdict writing. The PM's context window is the most expensive resource — if the relay block convention adds friction to verdict output, the PM may skip it. The instruction needs to be minimal: "output your verdict in a fenced code block." One sentence, not a paragraph.

---

**End of Memo**
