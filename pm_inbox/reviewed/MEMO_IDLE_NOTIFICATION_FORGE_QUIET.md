# MEMO: Idle Notification — "The Forge Is Quiet"

**From:** Builder (Opus 4.6), advisory session
**Date:** 2026-02-14
**Lifecycle:** NEW
**Supersedes:** None
**Resolves:** Operator efficiency gap — idle agents not signaling when they need attention

---

## What

When a builder finishes all assigned work and goes idle, it should play an auditory cue so the Operator knows attention is needed — even if the Operator isn't looking at the screen.

**The line:** "Thunder, the forge is quiet."

**Delivery:** Arbor voice (calm, grounded, neutral-operational) via existing `scripts/speak.py --signal` infrastructure.

---

## Why

If an agent finishes a WO, delivers its completion report, and the Operator isn't watching that terminal, the agent sits idle burning nothing but the Operator's time. The Operator has multiple agents running across multiple windows. An auditory cue on idle transition eliminates the "I didn't notice it finished" lag.

The infrastructure already exists (speak.py, Arbor voice profile, chime generation, Rule 21 in Standing Ops). It's just not being triggered on idle.

---

## Implementation (for next builder)

### 1. Add Rule 22 to Standing Ops Contract

**File:** `docs/ops/STANDING_OPS_CONTRACT.md`

Add after Rule 21:

```
22. **Idle Notification:** When a builder has completed all assigned work,
    delivered its completion report, and has no further dispatch queued,
    it calls:
        echo "=== SIGNAL: REPORT_READY ===" && echo "Thunder, the forge is quiet." | python scripts/speak.py --signal
    This signals the Operator that the agent is idle and awaiting direction.
    Triggers once per idle transition — not repeatedly.
```

### 2. Add to Agent Development Guidelines (if referenced in onboarding)

Under the completion protocol section, add:

```
After delivering your completion report, if no further work is queued,
trigger the idle notification:
    echo "=== SIGNAL: REPORT_READY ===" && echo "Thunder, the forge is quiet." | python scripts/speak.py --signal
```

### 3. Trigger conditions

- Builder completes WO, delivers completion report, no follow-up dispatch → trigger
- Builder finishes a conversation/advisory session and Operator hasn't responded → trigger
- PM finishes a verdict cycle and is waiting on Operator → trigger (PM version TBD)

### 4. NOT triggered when

- Builder is mid-WO (even if waiting on a test run)
- Builder just asked a clarifying question (waiting on answer, not idle)
- Multiple signals in rapid succession (once per idle transition only)

---

## Dependencies

- `scripts/speak.py` — exists, working, tested
- Arbor voice profile — exists, calibrated
- `models/voices/signal_reference_michael_24k.wav` — exists
- GPU (Chatterbox) or CPU fallback (Kokoro) — either works
- Rule 21 in Standing Ops — exists, this extends the pattern

---

## Effort

One rule addition to Standing Ops. One line in Agent Development Guidelines. Zero code changes. The speak.py infrastructure handles everything.

---

## Retrospective (Pass 3 — Operational judgment)

- **Fragility:** This memo proposes a Tier 3 (prose-enforced) rule addition. Like the relay block convention, compliance depends on builders reading Standing Ops. If the idle notification proves valuable, consider whether the signal could be triggered by infrastructure (e.g., a hook on session end) rather than relying on agent self-awareness of its idle state.

- **Process feedback:** The proposal leverages existing infrastructure — speak.py, Arbor voice profile, Rule 21 pattern — which keeps the implementation surface minimal. The "zero code changes" framing is accurate: this is a governance doc update, not an engineering task.

- **Methodology:** This extends the signaling pattern from Rule 21 (chime on completion) to idle transitions. The distinction matters: Rule 21 signals "work product ready," Rule 22 would signal "agent available." These are different operator-attention triggers with different urgency profiles.

- **Concerns:** The trigger conditions (Section 3 vs Section 4) need clear boundaries. "Builder finishes a conversation/advisory session and Operator hasn't responded" is ambiguous — how long before the idle signal fires? The PM version (noted as TBD) should be scoped separately to avoid conflating builder and PM idle semantics.

---

*End of memo.*
