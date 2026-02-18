# WO-SMOKE-FUZZER: Generative Smoke Test Infrastructure

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-18
**Lifecycle:** DISPATCH-READY
**Horizon:** 2 (Integration infrastructure — validates engine before new subsystem work)
**Priority:** P0 — Gate. Must pass before Oracle buildout begins.
**Source:** WO-SMOKE-TEST-002 methodology challenge (file at 2700 lines), Operator directive (exploratory/randomized testing)
**PM Amendment:** Determinism + logging gates added per Operator directive (2026-02-18)

---

## Target Lock

The current smoke test (`scripts/smoke_test.py`) is 2700+ lines with 8 hand-authored scenarios. Coverage is limited to what the builder thought to test. We need a generative harness that picks random spell/entity combinations from the registry and validates the full narration pipeline for each — discovering integration gaps that hand-authored scenarios miss.

## Binary Decisions

1. **Refactor first or build fuzzer in the existing file?** Refactor first. Create `scripts/smoke_scenarios/` modular structure. The main runner (`scripts/smoke_test.py`) becomes a thin orchestrator that imports scenario modules. Existing scenarios (B through H) move to `scripts/smoke_scenarios/manual.py`. The fuzzer lives in `scripts/smoke_scenarios/fuzzer.py`.

2. **How many random scenarios per run?** Default 20. Configurable via `--fuzz-count N` command line arg. Each run picks N random spell/entity combinations.

3. **What gets randomized?** Spell selection (from SPELL_REGISTRY), entity count (1-4 targets), entity HP range (1-100), entity names (from a small pool), positioning (for AoE). The fuzzer does NOT randomize class/level/ability scores — use reasonable defaults. Keep it simple.

4. **What constitutes a PASS for a fuzzed scenario?** No crash + NarrativeBrief fields populated where expected (non-None for spell_name, actor_name, damage_type when damage > 0, condition_applied when condition spell). Narration text produced (non-empty string). NarrationValidator returns PASS or WARN (not FAIL).

5. **Should the fuzzer test melee/maneuver too?** No. Scope to spells only. SPELL_REGISTRY is the richest combinatorial surface and the one most likely to have integration gaps. Melee fuzzing can be a follow-up WO.

## Contract Spec

### Change 1: Create modular smoke test structure

Create `scripts/smoke_scenarios/` directory with:
- `__init__.py` — empty or minimal
- `manual.py` — existing Scenarios B through H, extracted from smoke_test.py
- `fuzzer.py` — generative scenario runner (see Change 2)
- `common.py` — shared setup utilities (entity creation, world state init, event capture helpers) extracted from the current smoke test

Refactor `scripts/smoke_test.py` to:
- Import and run regression (Phase 1: 14 original stages + 4 fix verifications)
- Import and run manual scenarios from `manual.py`
- Import and run fuzzer from `fuzzer.py` (controlled by `--fuzz-count N`, default 20)
- Print summary combining all results

### Change 2: Build the generative fuzzer

`scripts/smoke_scenarios/fuzzer.py`:
- Read SPELL_REGISTRY to get available spells
- For each fuzz iteration:
  1. Pick a random spell
  2. Generate random entities (caster + 1-4 targets)
  3. Set up world state (positioning appropriate for the spell type — AoE vs single target)
  4. Execute the spell through the full pipeline (spell resolver → play loop events → NarrativeBrief assembly → template narration)
  5. Validate: no crash, expected NarrativeBrief fields non-None, narration text non-empty
  6. If NarrationValidator is importable, run it
  7. Record PASS/FINDING per scenario
- Use Python's `random` module with a configurable seed (`--fuzz-seed N`) for reproducibility
- Print each scenario as it runs (spell name, entity count, result)
- Return structured results for the summary

### Change 2a: Determinism and logging gates (Operator amendment, 2026-02-18)

**Determinism gate (strict):**
- Each generated scenario spec (spell, entities, HP values, names, positions) must produce a stable **ScenarioID** — a hash of the scenario's input parameters. Use `hashlib.sha256` on canonical JSON (`json.dumps(spec, sort_keys=True)`).
- Gate: running the generator twice with the same `--fuzz-seed` and `--fuzz-count` must produce the identical ordered list of ScenarioIDs. The meta-test (Change 3) must assert this.

**Event log gate (strict):**
- For each scenario, capture the event log and compute a final state digest (sha256 of `json.dumps(events, sort_keys=True)`).
- Gate: same inputs must yield byte-equal event logs and identical final state digest across runs. If the engine introduces non-determinism (e.g., dict ordering, floating point), document that as a FINDING — do not mask it.

**Logging receipt (required):**
- Each run must print a single summary receipt line:
  ```
  FUZZ RECEIPT: seed=N count=N first=<ScenarioID[:8]> last=<ScenarioID[:8]> digest=<run_digest[:12]>
  ```
  Where `run_digest` is sha256 of all ScenarioIDs concatenated in order. This is what lets PM and builders reference a run without reading code.

**Failure handling rule (required):**
- One failure is a real failure. The fuzzer must NOT be re-run to obtain a clean result.
- On failure: print the seed, the failing ScenarioID, and the failure details, then STOP. Do not continue to the next scenario.
- Add a `--collect-all` flag that overrides this behavior and continues past failures to collect all findings in a single run. Default behavior is stop-on-first-failure.

**Single scenario replay (optional, high value):**
- Add `--replay <ScenarioID>` mode that regenerates and reruns a single scenario by its ScenarioID. Requires the same seed that produced the original run. This allows failure reproduction without rerunning the full suite.

### Change 3: Test the fuzzer itself

Add a small test (1-2 tests) that runs the fuzzer with `fuzz_count=3` and a fixed seed, verifying:
- It completes without crash and produces results
- Two runs with the same seed produce identical ordered ScenarioID lists (determinism gate)
- Event log digests match across both runs (event log gate)

## Constraints

- Existing regression and manual scenarios MUST still pass after refactoring. 44/44 is the baseline.
- The fuzzer must be provably reproducible: same seed + count = identical ScenarioIDs, identical event logs, identical state digests. "Reproducible" means gate-passing, not vibes.
- Do NOT modify any production code (`aidm/`). This WO only touches `scripts/`.
- Do NOT modify gold masters.
- Keep the fuzzer simple. No ML, no property-based testing frameworks, no external dependencies. Just `random` + `SPELL_REGISTRY` + the existing test infrastructure.

## Success Criteria

- [ ] `scripts/smoke_scenarios/` directory exists with manual.py, fuzzer.py, common.py
- [ ] `scripts/smoke_test.py` refactored to import from smoke_scenarios/
- [ ] Existing 44/44 stages still pass (regression + manual scenarios unchanged in behavior)
- [ ] Fuzzer runs 20 scenarios by default, configurable via `--fuzz-count`
- [ ] Fuzzer is reproducible with `--fuzz-seed`
- [ ] Determinism gate: same seed + count produces identical ordered ScenarioID list (meta-test asserts this)
- [ ] Event log gate: same inputs produce byte-equal event logs and state digests (meta-test asserts this)
- [ ] Each run prints a FUZZ RECEIPT line (seed, count, first/last ScenarioID, run digest)
- [ ] Default behavior stops on first failure (prints seed + ScenarioID + details)
- [ ] `--collect-all` flag continues past failures to collect all findings
- [ ] Each fuzzed scenario validates: no crash, NarrativeBrief fields populated, narration non-empty
- [ ] Summary output shows: total fuzzed, passed, findings, and per-finding details
- [ ] At least one meta-test exists for the fuzzer
- [ ] Existing unit tests pass

## Integration Seams

1. **SPELL_REGISTRY → Fuzzer:** The fuzzer reads SPELL_REGISTRY to select spells. If the registry format changes, the fuzzer breaks. The fuzzer should import the registry the same way production code does.
2. **Fuzzer → NarrativeBrief assembler:** The fuzzer exercises the full pipeline. Any new event vocabulary mismatches will surface as FINDING (non-None expected, None received).

## Assumptions to Validate

1. SPELL_REGISTRY is importable and iterable — confirm the import path before writing.
2. The existing smoke test setup (entity creation, world state init) can be extracted into shared utilities without changing behavior — confirm by running regression after extraction.
3. NarrationValidator is importable from the smoke test context — confirm (it was in WO-SMOKE-TEST-002 Scenarios D and H).
4. The `random` module with a fixed seed produces identical results across Python versions on the same platform — confirm or document the Python version requirement.

---

## Delivery

After all success criteria pass:
1. Write your debrief (`pm_inbox/DEBRIEF_WO-SMOKE-FUZZER.md`, Section 15.5) — 500 words max. Four mandatory sections:
   - **Scope Accuracy** — one sentence: "WO scope was [accurate / partially accurate / missed X]"
   - **Discovery Log** — what you checked, what you learned, what you rejected
   - **Methodology Challenge** — one thing to push back on
   - **Field Manual Entry** — one ready-to-paste tradecraft entry
2. Update `pm_inbox/PM_BRIEFING_CURRENT.md`
3. `git add` all changed/new files — code, tests, debrief, AND briefing update
4. `git commit -m "feat: WO-SMOKE-FUZZER — generative smoke test infrastructure"`
5. Record the commit hash and add it to the debrief header (`**Commit:** <hash>`)
6. `git add pm_inbox/DEBRIEF_WO-SMOKE-FUZZER.md && git commit --amend --no-edit`

Everything in the working tree — code AND documents — is at risk of loss if uncommitted.
Do NOT edit BUILDER_FIELD_MANUAL.md — the PM curates tradecraft from your debrief.

---

*End of WO-SMOKE-FUZZER*
