# WO-ANVIL-HOOLIGAN-001 — Engine Smoke + Hooligan Protocol Run

**Issued:** 2026-02-25
**Lifecycle:** IN FLIGHT — dispatched by Thunder 2026-02-25
**Track:** QA / Engine
**Priority:** HIGH — confirms engine baseline and validates three specific WS gaps
**WO type:** EXECUTION + TRIAGE (run, read, report — no code changes)
**Seat:** Anvil (BS Buddy)

**Blocks:** WO-SEC-REDACT-001 scoping and prioritization

---

## 1. Target Lock

Run the full engine smoke test suite including the Hooligan Protocol adversarial scenarios.
Confirm engine baseline under adversarial-but-non-hacking play. Produce debrief with WS frame evidence.
File a structured report to `pm_inbox/`.

**Scope:** Engine only. No model/LLM required. `spark_hooligan.py` is OUT OF SCOPE — that
requires a live LlamaCppAdapter and is blocked on GAP-B (VS Build Tools not provisioned).

**Required gap confirmations (confirm or refute with evidence):**
- **GAP-WS-003** — `token_add` on join includes `hp` + `hp_max` for monster entities
- **GAP-WS-004** — unhandled event types emit raw internal delta fields (`hp_before`, `hp_after`, `delta`, etc.) via passthrough branch
- **GAP-WS-002** — `default_actor_id = "pc_fighter"` effect observable in multi-connection or log evidence

If a claim is inconclusive, debrief must state what blocked it (missing endpoint, no repro, UI path absent).

---

## 2. What To Run

### Step 1 — Session bootstrap
```bash
python scripts/verify_session_start.py
```
Confirm green before proceeding. If not green, report to Slate and stop.

### Step 2 — Full smoke suite (includes Hooligan as Phase 3)
```bash
cd f:/DnD-3.5
python scripts/smoke_test.py --no-fuzz 2>&1 | tee pm_inbox/HOOLIGAN_RUN_LATEST.txt
```

`--no-fuzz` skips the generative fuzzer (Phase 4) to keep the run focused and fast.
Remove `--no-fuzz` if Thunder wants the full fuzzer run — it adds randomized spell/entity
combinations on top.

### Step 3 — Gate regression check
```bash
python -m pytest tests/ -q --tb=no 2>&1 | tail -10
```
Confirm no new gate failures. Baseline: 44 pre-existing failures, 7,221+ passing.

---

## 3. What To Report

For each Hooligan scenario (H-001 through H-012):

| ID | Verdict | Notes |
|----|---------|-------|
| H-001 | PASS / FINDING / CRASH | Ready Action Targeting Terrain |
| H-002 | ... | ... |
| ... | | |

**Triage each FINDING:**
- Is it pre-existing (already on the board)?
- Is it a new functional gap?
- Severity: CRASH (stop everything) / HIGH / MEDIUM / LOW / INFO

**Triage each CRASH:**
- Crashes are stop-everything. Report immediately to Slate.
- Include full traceback.

---

## 4. What Anvil Does NOT Do

- No code changes. Read, run, report only.
- No fixes. If something is broken, file a finding — do not patch it.
- No spark_hooligan.py. Model seat is not available.
- No new WOs. Slate drafts WOs from findings.

---

## 5. Delivery

File report to: `pm_inbox/ANVIL_HOOLIGAN_001.md`

**Required sections:**

### Section 1 — Run Summary
- Date/time
- `verify_session_start.py` output (pass/fail)
- Gate baseline before run (passing count, pre-existing failures)
- Gate baseline after run (same — confirm no regression)

### Section 2 — Hooligan Results Table
Full H-001 through H-012 verdict table. Tier A vs Tier B call-out.

### Section 3 — Findings
For each FINDING or CRASH: scenario ID, description, module, severity, PM recommendation
(new board entry vs already tracked vs hold).

### Section 4 — Verdict
One of:
- **CLEAN** — all Tier A pass, no Tier B crashes, no new findings
- **FINDINGS ONLY** — Tier A pass, no crashes, new findings logged (list them)
- **TIER A FAILURE** — one or more Tier A scenarios wrong result (escalate immediately)
- **CRASH** — any scenario threw an exception (escalate immediately)

---

## 6. Hooligan Scenario Reference

For Anvil's orientation — what's being tested:

**Tier A (must resolve correctly — wrong answer = failure):**
- H-003, H-004, H-008, H-010, H-011

**Tier B (must not crash — findings OK):**
- H-001, H-002, H-005, H-006, H-007, H-009, H-012

Full scenario list is in `scripts/smoke_scenarios/hooligan.py`. Anvil can read it for
context but does not modify it.

---

## 7. Escalation

- Any CRASH → stop, report to Slate immediately, include full traceback
- Any Tier A FAILURE → stop, report to Slate immediately
- FINDINGS ONLY → complete the run, file the full report, Slate triages
- CLEAN → file the report, note clean sweep

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Hooligan run complete. Results filed."
```
