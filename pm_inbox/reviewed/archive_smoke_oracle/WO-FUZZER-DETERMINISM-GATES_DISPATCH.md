# WO-FUZZER-DETERMINISM-GATES: Add Determinism Gates to Generative Fuzzer

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-18
**Lifecycle:** DISPATCH-READY
**Horizon:** 2 (Infrastructure hardening — makes fuzzer results provable)
**Priority:** P1 — Unblocked by WO-SMOKE-FUZZER. Required before fuzzer results are trusted for gate decisions.
**Source:** Operator determinism amendment to WO-SMOKE-FUZZER (Change 2a), not implemented by initial builder.

---

## Target Lock

WO-SMOKE-FUZZER landed the generative fuzzer infrastructure (commit `ac67327`). The fuzzer works — 19/20 PASS, 1 FINDING, modular structure operational. But the Operator's determinism amendment (Change 2a) was not implemented. The fuzzer is reproducible at the spell-selection level (same seed = same spells), but there are no provable gates: no ScenarioID hashes, no event log digests, no receipt line, no stop-on-failure default, no `--collect-all` or `--replay` flags.

This WO adds those gates. No new scenarios, no refactoring. Just instrumentation on the existing fuzzer.

## Binary Decisions

1. **Modify fuzzer.py in place or create a wrapper?** Modify `scripts/smoke_scenarios/fuzzer.py` in place. The gates are part of the fuzzer, not a separate layer.

2. **What hash algorithm?** `hashlib.sha256`. Consistent with the project's canonical hashing direction (GT v12, GAP-004).

3. **What constitutes the ScenarioID input?** The scenario spec dict as canonical JSON: `json.dumps(spec, sort_keys=True).encode()`. The spec must include: spell name, entity names, entity HP values, entity positions, and any other randomized fields. It must NOT include runtime results (events, damage rolls).

## Contract Spec

### Change 1: ScenarioID generation

In `fuzzer.py`, after generating each scenario's spec (spell + entities + positioning), compute:
```python
scenario_id = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
```
Store `scenario_id` in the scenario result dict. Print it alongside each scenario's output line.

### Change 2: Event log digest

After each scenario executes, compute:
```python
event_digest = hashlib.sha256(json.dumps(events, sort_keys=True).encode()).hexdigest()
```
Store `event_digest` in the scenario result dict.

### Change 3: FUZZ RECEIPT

At the end of each run, print:
```
FUZZ RECEIPT: seed=N count=N first=<ScenarioID[:8]> last=<ScenarioID[:8]> digest=<run_digest[:12]>
```
Where `run_digest = hashlib.sha256("".join(all_scenario_ids).encode()).hexdigest()`.

### Change 4: Stop-on-first-failure

Change default behavior: when a scenario produces a FINDING, print the seed, ScenarioID, and failure details, then stop. Do not continue to the next scenario.

Add `--collect-all` flag (or `collect_all=False` parameter) that overrides this and continues past failures.

### Change 5: Single scenario replay (optional)

Add `--replay <ScenarioID>` mode. Given a seed, regenerate all scenarios, find the one matching the ScenarioID, and rerun only that one. If no match, error with "ScenarioID not found for seed N".

### Change 6: Update meta-tests

Update `tests/test_smoke_fuzzer.py` to assert:
- Two runs with same seed produce identical ordered ScenarioID lists (determinism gate)
- Two runs with same seed produce identical event log digests (event log gate)
- FUZZ RECEIPT line is printed (check stdout capture)

## Constraints

- Modify only `scripts/smoke_scenarios/fuzzer.py` and `tests/test_smoke_fuzzer.py`
- Do NOT modify production code (`aidm/`)
- Do NOT modify other smoke scenario files (common.py, manual.py)
- Existing 44/44 stages + 20-scenario fuzzer must still work
- If the event log gate reveals non-determinism in the engine, document it as a FINDING — do not mask it

## Success Criteria

- [ ] Each scenario result includes a `scenario_id` (sha256 hex of canonical JSON spec)
- [ ] Each scenario result includes an `event_digest` (sha256 hex of canonical JSON events)
- [ ] Same seed + count produces identical ScenarioID list (meta-test asserts)
- [ ] Same seed + count produces identical event digests (meta-test asserts)
- [ ] FUZZ RECEIPT line printed at end of each run
- [ ] Default behavior stops on first failure
- [ ] `--collect-all` flag continues past failures
- [ ] Existing 44/44 stages still pass
- [ ] Existing meta-tests still pass (or updated to assert new gates)

## Files Expected to Change

- Modified: `scripts/smoke_scenarios/fuzzer.py`
- Modified: `tests/test_smoke_fuzzer.py`

## Files NOT to Change

- Gold masters
- Production code (`aidm/`)
- Other smoke scenario files
- PM inbox files (except PM_BRIEFING_CURRENT.md update per delivery protocol)

---

## Delivery

After all success criteria pass:
1. Write your debrief (`pm_inbox/DEBRIEF_WO-FUZZER-DETERMINISM-GATES.md`, Section 15.5) — 500 words max. Four mandatory sections:
   - **Scope Accuracy** — one sentence: "WO scope was [accurate / partially accurate / missed X]"
   - **Discovery Log** — what you checked, what you learned, what alternatives you considered and rejected
   - **Methodology Challenge** — one thing to push back on
   - **Field Manual Entry** — one ready-to-paste tradecraft entry
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md`
3. `git add` all changed/new files — code, tests, debrief, AND briefing update
4. `git commit -m "feat: WO-FUZZER-DETERMINISM-GATES — provable reproducibility for generative fuzzer"`
5. Record the commit hash and add it to the debrief header (`**Commit:** <hash>`)
6. `git add pm_inbox/DEBRIEF_WO-FUZZER-DETERMINISM-GATES.md && git commit --amend --no-edit`

Everything in the working tree — code AND documents — is at risk of loss if uncommitted.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

---

*End of WO-FUZZER-DETERMINISM-GATES*
