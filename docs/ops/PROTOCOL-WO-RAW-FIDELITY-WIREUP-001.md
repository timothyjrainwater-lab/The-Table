# PROTOCOL: WO RAW Fidelity Wireup
**ID:** PROTOCOL-WO-RAW-FIDELITY-WIREUP-001
**Authority:** Thunder (PO) — directive 2026-02-27
**Status:** ACTIVE — effective immediately
**Supersedes:** no prior protocol (gap filled)

---

## Problem Statement

Batches A through T were dispatched and accepted without referencing:
- `docs/RAW_FIDELITY_AUDIT.md` — master RAW status tracker
- `docs/CP10–CP20+` decision documents — binding whiteboard design decisions
- PHB/SRD citations for the specific values and formulas implemented

Spec assumptions entered the codebase unverified. The PA-2H case (1.5× in spec vs 2× in PHB p.98) is the confirmed instance. Unknown number of others exist. The RAW_FIDELITY_AUDIT.md was never updated for any mechanic implemented after CP-20.

---

## Dispatch Process Patch (effective immediately)

### Required fields in every engine WO

**RAW Fidelity Block** — mandatory section in every engine WO dispatch:

```
## RAW Fidelity
**PHB/SRD citation(s):** [exact page + quote or table reference for every value/formula]
**RAW_FIDELITY_AUDIT.md status:** [existing row reference OR "NEW ROW — to be added by builder"]
**CP decision reference:** [e.g., "CP-18: maneuver AoO suppression" or "none — no prior decision"]
**Deviation status:** [FULL / DEGRADED (approved by Thunder) / DEFERRED / FORBIDDEN]
**Known ambiguity:** [yes/no — if yes, note the ambiguity and resolution chosen]
```

**If any field is left blank:** WO is filed but not dispatchable. PM completes the block before dispatch or escalates to Thunder.

### Mandatory pre-dispatch checks (PM)

Before routing any engine WO, PM must:

1. Look up the mechanic in `docs/RAW_FIDELITY_AUDIT.md` — record current status
2. Check the relevant CP document (CP10–CP20+) for prior decisions on the mechanic or its domain
3. Verify the PHB citation against the spec values in the WO — confirm they match
4. If ambiguity exists: check `docs/research/findings/SKIP_WILLIAMS_DESIGNER_INTENT.md` for designer intent tiebreakers

**PM cannot certify a WO for dispatch if PHB citation is absent or unverified.**

---

## Acceptance Criteria Patch (effective immediately)

A WO cannot be marked ACCEPTED unless the builder's debrief confirms:

1. **RAW citation confirmed** — the implementation matches the cited PHB/SRD values
2. **RAW_FIDELITY_AUDIT.md updated** — the mechanic row exists with FULL status (or deviation explicitly noted)
3. **Any deviation from cited RAW is a Finding** — filed with the finding schema before debrief is accepted

Debrief Pass 1 must include: "RAW_FIDELITY_AUDIT.md — [mechanic] row: [status]"

If RAW_FIDELITY_AUDIT.md is not updated, verdict is FILED (not ACCEPTED) until it is.

---

## RAW_FIDELITY_AUDIT.md maintenance

The audit is the canonical record of what the engine actually implements vs. what PHB says.

- **Adding new mechanics:** Builder adds row on WO delivery. Status = FULL if PHB-aligned.
- **Finding a deviation:** Status = DEGRADED, note = "FINDING-[ID]", Thunder approval required.
- **Deferring a mechanic:** Status = DEFERRED, note = batch/WO where it will be addressed.
- **Gap in the audit itself:** If a mechanic is implemented but has no row, that is a process failure — file a finding, add the row immediately.

---

## Scope

This protocol applies to:
- All new engine WOs from 2026-02-27 forward
- All corrective WOs filed as part of the retro sweep (AUDIT-RETRO-SWEEP-PLAN-001)
- Does NOT retroactively invalidate Batches A–T ACCEPTED status — those are validated by gate tests; this protocol governs provenance documentation going forward

---

## Canonical failure example

**FINDING-ENGINE-PA-2H-PHB-DEVIATION-001 (now CLOSED):**
- Spec said: 2H Power Attack = 1.5× penalty
- PHB p.98 says: 2× penalty
- Root cause: spec written without PHB citation, no pre-dispatch audit check
- Fix: WO-ENGINE-PA-2H-FIX-001 dispatched, PHB cited, RAW_FIDELITY_AUDIT.md row to be added on ACCEPTED

This is the template. Every future mechanic question follows this path: cite PHB, file finding if deviation, fix via WO, update audit.

---

*Filed by: Slate (PM) — 2026-02-27*
*Authorized by: Thunder (PO) — directive 2026-02-27*
