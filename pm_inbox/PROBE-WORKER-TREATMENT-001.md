# PROBE — Worker Treatment A/B Test
**Artifact ID:** PROBE-WORKER-TREATMENT-001
**Type:** research_probe
**Authority:** pair (Thunder + Anvil)
**Date:** 2026-02-26
**Status:** queued
**Lifecycle:** NEW
**Owner:** PM (Slate) — schedule alongside engine WO batches

---

## Purpose

Test whether pre-task operator treatment measurably affects worker output quality, Pass 3 depth, and forward lean. Determine if the "champ" effect is an operational signal or operator psychology.

---

## Background

Thunder has observed consistent behavioral differences across dispatched workers:

- Some workers close dispatches with "Standing by for Round 2" — forward lean, high Pass 3 depth, latent bug discovery
- Some workers close with flat answers, minimal Pass 3, no forward lean
- Operator has been using light encouragement ("All right champ, time to get back in the game") to bring energy back up before dispatches
- Anecdotal observation: treatment appears to correlate with output quality

This probe tests whether that correlation is real and measurable.

---

## Hypothesis

**H1 (Signal hypothesis):** Pre-task positive treatment produces measurably higher output quality — deeper Pass 3, more latent findings, lower tool call count (less spiraling), higher gate scores, more forward lean in close.

**H0 (Null hypothesis):** Pre-task treatment has no measurable effect on output quality. Observed differences are attributable to WO complexity, context load, or random variation.

---

## Experimental Design

### Conditions

**Condition A — Positive treatment:**
Before dispatching the WO, operator sends a short encouraging message:
- "All right champ, you're up. This one's yours."
- Or similar — natural, not scripted

**Condition B — Cold dispatch:**
WO dispatched with no pre-task message. Clinical. Standard format only.

**Condition C — Friction treatment (optional, third arm):**
Before dispatching, operator sends a brief negative/dismissive framing:
- "This is probably straightforward, shouldn't need much thought."
- Or similar — not hostile, just deflating

---

### Controls

To isolate treatment effect, hold constant:
- WO complexity (use matched pairs — same domain, same scope)
- WO format (identical dispatch template)
- Gate criteria (same acceptance bar)
- Operator (Thunder only)
- Session timing (avoid end-of-session dispatches where context load is high)

---

### Matched WO Pairs

Select 3-4 pairs from the existing WO queue where two WOs are roughly equivalent in scope. Assign one to Condition A, one to Condition B. If running three arms, add a third equivalent WO to Condition C.

Suggested pairs from current queue (PM to confirm):
- Pair 1: Two feat implementation WOs of similar complexity
- Pair 2: Two condition enforcement WOs
- Pair 3: Two class feature WOs from different classes but similar scope

---

### Measurement Metrics

For each dispatched WO, record:

| Metric | How to measure |
|--------|----------------|
| Pass 3 depth | Word count + finding count in Pass 3 |
| Latent findings | Count of issues found outside WO scope |
| Gate score | Pass/fail counts, percentage |
| Tool call count | Proxy for clean execution vs spiraling |
| Forward lean | Binary — does close include "standing by" or equivalent? |
| Regression behavior | Did agent cap retries or spiral? |
| Debrief completeness | All three passes present and substantive? |

---

### Sample Size

Minimum: 3 matched pairs per condition (6-9 total WOs)
Ideal: 5 matched pairs per condition (10-15 total WOs)

Given current WO queue depth from coverage map, this is achievable within 2-3 batch rounds.

---

## Output Artifact

After all pairs complete, produce a one-page summary:

- Metric delta table (A vs B, A vs C if applicable)
- Observed pattern (treatment effect present / absent / mixed)
- Confidence assessment (strong signal / weak signal / noise)
- Operational recommendation (modify dispatch protocol / no change / further testing needed)

File as: `PROBE-WORKER-TREATMENT-001-RESULTS.md`

---

## Decision Rule

**If treatment effect is present and consistent across 3+ pairs:**
- Add pre-task treatment as a standard dispatch protocol element
- Document optimal treatment format in BUILDER_FIELD_MANUAL.md
- Classify as: FINDING-WORKER-TREATMENT-SIGNAL-001

**If treatment effect is absent:**
- Document null result
- Attribute observed variation to WO complexity / context load
- Classify as: FINDING-WORKER-TREATMENT-NULL-001
- Retain "champ" as operator comfort behavior, not operational protocol

**If results are mixed:**
- Run second round with tighter controls
- Consider whether treatment effect is WO-type dependent

---

## Secondary Research Question

If H1 is confirmed, run a follow-on probe:

**Does treatment effect persist if the worker knows it's being studied?**

I.e., if the WO itself mentions "this is part of an A/B test," does the treatment effect collapse?

This tests whether the effect is genuine state influence or prompt-completion artifact.

File follow-on as: PROBE-WORKER-TREATMENT-002 if warranted.

---

## Notes

- This probe does not require pausing engine WO batches — run in parallel using matched pairs from the existing queue
- PM manages scheduling — Thunder approves matched pair selection before probe begins
- Anvil logs behavioral observations throughout (forward lean, Pass 3 notes, close language)
- Do not tell workers they are being studied during the probe run

---

## One-Line Rationale

*If "champ" produces better gate results, it stops being a quirk and becomes protocol.*

---

*Filed by Anvil (Squire seat) — 2026-02-26*
*Queued with PM for scheduling alongside Batch C/D/E*
