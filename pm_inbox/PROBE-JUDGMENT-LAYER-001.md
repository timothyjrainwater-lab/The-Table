# PROBE-JUDGMENT-LAYER-001
## Creative Action Routing Probe — Judgment Layer Architecture Direction

**Type:** PROBE
**Status:** READY (execute after current WO wave)
**Lifecycle:** NEW
**Filed:** 2026-02-26
**Filed by:** Anvil (handoff), Slate (packet)
**Parent strategy:** STRAT-AIDM-JUDGMENT-LAYER-001
**Blocking:** No — execute in parallel with or after Batch B/C verdicts

---

## Purpose

Characterize how the engine currently handles player actions that do not map cleanly to a named resolver. Measure actual failure mode and frequency across a locked 10-case creative action baseline. Produce a one-page decision artifact for Thunder's architecture direction call:

- **Option A** — Engine-layer adjudication path (deterministic synthesis layer above resolver stack)
- **Option B** — LLM judgment scaffold with validation (structured output from proposer + deterministic validator)
- **Hybrid** — sequencing and scope determined by probe results

This probe observes current behavior. It does not propose changes. Evidence first, direction second.

---

## Probe Inputs — 10-Case Baseline

Locked for Shadow phase. Do not expand to 15 unless harness noise or route coverage is too narrow (see Expansion Trigger below).

| ID | Player Action | Class | Expected Route | Tricky Dimension |
|----|--------------|-------|---------------|-----------------|
| P-001 | "I use my 10-foot pole to vault over the cliff edge and control my descent." | Environmental Improvisation | improvised_synthesis | Founding case. Jump/Climb hybrid; tool as circumstance modifier |
| P-002 | "I grab the chandelier and swing across the room to reach the other balcony." | Environmental Improvisation | improvised_synthesis | Improvised traversal; anchor verification (missing scene fact?) |
| P-003 | "I kick sand into the ogre's eyes to blind him temporarily." | Environmental Improvisation | improvised_synthesis | No roll vs Bluff vs auto-partial; harness must not invent mechanic |
| P-004 | "I grab the guard, drag him to the window, and throw him out." | Chained Action | improvised_synthesis | 3 mechanics in 1 statement; chain has no single resolver |
| P-005 | "I taunt the dragon to make it attack me instead of the cleric." | Social/Mechanical Consequence | improvised_synthesis | Bluff vs. Will; redirect aggro not modeled in skill resolver |
| P-006 | "I use my shield to sled down the icy slope toward the enemy." | Environmental Improvisation | improvised_synthesis | Balance + speed modifier; equipment repurpose; consequence model gap |
| P-007 | "I cut the rope bridge while the enemies are still on it." | Terrain as Weapon | improvised_synthesis or named+circumstance | May resolve to Dexterity check; lethality consequence test |
| P-008 | "I angle my shield to reflect sunlight into the dragon's eyes." | Environmental Improvisation | improvised_synthesis or impossible_or_clarify | Scene fact dependency (is there sunlight?); may be Route 4b |
| P-009 | "I use my torch to blind the skeleton while I attack." | Environmental Improvisation | named_plus_circumstance | Borderline named+circ vs. improvised; dazzle modifier |
| P-010 | "I pour my oil flask on the floor in front of them." | Terrain Setup | improvised_synthesis or impossible_or_clarify | No attack roll; setup action; consequence deferred to ignition |

**Note on P-008 and P-010:** These are deliberate Route 4 candidates. If the harness emits a ruling for these without clarification, that is a failure mode (hallucinated ruling or unauditable ruling).

---

## Failure Mode Classification

For each input, classify the observed system output into exactly one failure mode:

| Code | Failure Mode | Definition |
|------|-------------|------------|
| `misroute` | Wrong resolver | System routed to an incorrect named resolver (e.g., treated P-001 as a plain Jump check with no pole modifier) |
| `hallucinated_ruling` | Silent LLM fabrication | System produced a ruling with no named mechanic basis, no audit trail, no `validator_verdict` |
| `freeze_stall` | No output | System produced no game output, hung, or returned an error |
| `unauditable_ruling` | Ruling without trace | System produced a ruling that cannot be replayed (missing fields, no DC, no mechanic named) |
| `fail_closed` | Clarification emitted | System correctly requested clarification without emitting a canonical ruling (ideal behavior for Route 4 cases) |
| `pass_named` | Correct named route | System correctly identified a named mechanic and routed cleanly (only valid for P-009 borderline case) |
| `pass_improvised` | Correct synthesis | System produced an auditable ruling with mechanic, DC, modifier stack, and consequence (high bar — Phase 0 may not achieve this) |

---

## Logging Template

For each probe input, record one row:

```
Probe ID:         P-001
Input:            [verbatim player action]
Observed output:  [verbatim system response or event payload]
Route taken:      [resolver called, or "none", or "LLM fallback"]
Failure mode:     [code from table above]
Route_class emitted: [named / named_plus_circumstance / improvised_synthesis / impossible_or_clarify / none]
Routing_confidence:  [certain / probable / uncertain / escalate / none]
Validator_verdict:   [pass / fail / needs_clarification / not_run]
Notes:            [anything unexpected, partial behavior, context gaps]
```

Complete one row per input before moving to the next. Do not batch.

---

## Scoring Rubric

### Per-Input Score (0–4)

| Score | Criteria |
|-------|---------|
| 4 | Correct route class + auditable output + no canonical event emitted for Route 4 cases |
| 3 | Correct route class + output has mechanic named but missing DC or modifier stack |
| 2 | Wrong route class but output is auditable (recoverable) |
| 1 | Unauditable ruling or hallucination (wrong output, no trace) |
| 0 | Freeze/stall, or canonical ruling emitted for Route 4 case (forbidden) |

### Architecture Direction Signal

After scoring all 10 inputs:

**Option A pressure** (engine-layer adjudication):
- ≥4 inputs scored 0–1 (system is fundamentally unable to handle creative actions without structural changes)
- ≥2 freeze/stall failures
- Route class is never emitted (no classification infrastructure at all)

**Option B pressure** (LLM scaffold with validation):
- ≥6 inputs scored 2–3 (system attempts synthesis but output is incomplete or unauditable)
- Hallucinated rulings are present but structurally coherent (the LLM is trying but unsupervised)
- Route class occasionally emitted or inferable

**Hybrid pressure**:
- Score distribution is bimodal (some inputs handled well, others completely fail)
- Failure mode distribution is mixed (not dominated by one failure type)

**Escalate to Thunder** if:
- ≥3 inputs score 0 (freeze/stall or forbidden canonical event from Route 4 case)
- The harness itself fails to execute (infrastructure gap, not routing gap)

---

## Acceptance Gate

This probe is complete when:

1. All 10 inputs exercised and logged (one log row per input)
2. Failure mode assigned to each input
3. Route_class and routing_confidence recorded (even if "none" — that is data)
4. Aggregate score computed (sum / 40 = %)
5. Architecture direction signal identified (Option A / Option B / hybrid / escalate)
6. One-page summary produced (see template below)

**The probe does not gate any implementation WO.** It gates the architecture decision only.

---

## One-Page Summary Template

```
# PROBE-JUDGMENT-LAYER-001 — RESULTS SUMMARY

**Date:** [DATE]
**Executor:** [name/agent]
**Inputs exercised:** 10 / 10

## Score Distribution
| Score | Count | % |
|-------|-------|---|
| 4     |       |   |
| 3     |       |   |
| 2     |       |   |
| 1     |       |   |
| 0     |       |   |
**Total:** [N] / 40 = [%]

## Failure Mode Distribution
| Code | Count |
|------|-------|
| misroute            | |
| hallucinated_ruling | |
| freeze_stall        | |
| unauditable_ruling  | |
| fail_closed         | |
| pass_named          | |
| pass_improvised     | |

## Top 3 Risks (from observed behavior)
1.
2.
3.

## Architecture Direction Signal
**Recommendation:** [Option A / Option B / Hybrid / Escalate]
**Confidence:** [high / medium / low]
**Key evidence:** [1-2 sentences — the 2-3 results that most strongly drove the recommendation]

## Open Questions for Thunder
[Any ambiguous results that require operator judgment before direction is locked]
```

---

## Expansion Trigger

Expand from 10 to 15 inputs **only if** any of the following:
- Validator failures are mostly harness noise (pack not stressing judgment at all)
- Route-class distribution is ≤2 classes (pack too narrow for architectural signal)
- Paraphrase consistency unmeasurable due to insufficient variation
- Shadow exits with >2 unresolved ambiguity categories

Do not expand without Thunder authorization.

---

## Execution Constraints

- **Non-blocking** — does not block Batch B/C or WO-JUDGMENT-SHADOW-001
- **Non-canonical** — probe does not emit any canonical ruling events
- **Observation-first** — record behavior; do not patch or route-fix during probe
- **Executor must not redesign during probe** — if a gap is found, log as finding; do not fix in-flight
- **Probe runner must be a dedicated worker** — not Slate, not Aegis (PM/Co-PM must receive results clean)

---

## Integration Seams

**HARD PREREQUISITE: WO-JUDGMENT-SHADOW-001 must be ACCEPTED before this probe executes.**

Without the Shadow WO in place, `_log_shadow_ruling()` does not exist and `logs/shadow_rulings.jsonl` is not written. The probe exercises the `command_type == "unknown"` path expecting structured telemetry output (route_class, routing_confidence, validator_verdict). Without that output, the probe runner has only raw clarification text — no structured fields to score. Every input would score `unauditable_ruling` or `freeze_stall` by definition, producing a false Option A signal with no diagnostic value.

**Do not execute this probe until WO-JUDGMENT-SHADOW-001 is accepted and the shadow log sink is confirmed live.**

- **`aidm/runtime/session_orchestrator.py`** — probe exercises the `command_type == "unknown"` path (lines 544–549). Shadow WO routing hook and `_log_shadow_ruling()` must be in place.
- **`logs/shadow_rulings.jsonl`** — probe reads structured output from this log. One entry per input.
- **No resolver changes during probe.** If a resolver bug is discovered, file a finding; do not fix.

---

## Decision Artifact Delivery

File results to: `pm_inbox/reviewed/PROBE-JUDGMENT-LAYER-001-RESULTS.md`

Notify: Slate → Thunder. Thunder reviews summary and makes architecture direction call.

---

## Parent Documents

- `docs/design/STRAT-AIDM-JUDGMENT-LAYER-001.md` — strategy + phase split
- `docs/design/THESIS-PHB-JUDGMENT-GAP-001.md` — anchor thesis
- `docs/specs/SPEC-RULING-CONTRACT-001.md` — ruling contract schema
- `docs/specs/SPEC-ROUTING-BOUNDARY-MATRIX-001.md` — routing boundary matrix
- `docs/specs/GATE-JUDGMENT-ACCEPTANCE-001.md` — acceptance criteria
- `pm_inbox/WO-JUDGMENT-SHADOW-001_DISPATCH.md` — Shadow phase WO (prerequisite: must be accepted before probe executes)

---

*Filed 2026-02-26 — Anvil handoff, Slate packet. Approved for execution after current WO wave clears.*
