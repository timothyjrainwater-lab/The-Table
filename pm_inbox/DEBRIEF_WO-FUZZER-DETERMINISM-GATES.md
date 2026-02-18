# DEBRIEF: WO-FUZZER-DETERMINISM-GATES

**From:** Builder
**Date:** 2026-02-18
**WO:** WO-FUZZER-DETERMINISM-GATES
**Commit:** `e128342`

---

## Scope Accuracy

WO scope was accurate — all 6 changes implemented as specified with one discovery: the engine's spell resolver uses `uuid4()` for `cast_id`, which is not seeded by `RNGManager`, making raw event logs non-deterministic.

## Discovery Log

1. **Read existing fuzzer.py (355 lines)** — Clean modular structure from WO-SMOKE-FUZZER. The `_fuzz_one_spell` function generates entities inline using helper functions that consume RNG. Key insight: to build a hashable spec, I needed to capture randomized values *before* passing them to entity factories.

2. **RNG consumption order is critical** — The spec must be computed from the same values that the entity factories receive, in the same order. I inlined the random value generation (hp, caster_level, saves, etc.) so both the spec dict and the entity construction use the same values. Verified that RNG sequence is preserved by checking that seed=42 still produces the same spell selections.

3. **Event digest non-determinism discovered** — First meta-test run: ScenarioID determinism PASSED, event digest determinism FAILED. Diagnosed via field-by-field diff: `payload.cast_id` is a `uuid.uuid4()` call in the spell resolver, not seeded by `RNGManager`. All other event fields are byte-identical across runs. Solution: strip `cast_id` from payloads before hashing for the deterministic digest. Store raw digest separately as `event_digest_raw` for auditing.

4. **Stop-on-first-failure default** — Changed `run_fuzz` signature to accept `collect_all=False`. With seed=42 and 20 iterations, default mode now stops at iteration #12 (Cone of Cold FINDING) instead of running all 20. Updated `smoke_test.py` orchestrator to pass through `--collect-all` and `--replay` CLI args.

5. **Replay mode design decision** — The WO says "regenerate all scenarios, find the one matching the ScenarioID." This means replay mode runs all N iterations through the RNG (to keep the sequence stable) but only *keeps* the result for the matching ScenarioID. Prefix matching is supported so `--replay abc12345` matches against full 64-char hashes.

6. **Files changed:** `scripts/smoke_scenarios/fuzzer.py` (355→546 lines), `tests/test_smoke_fuzzer.py` (53→145 lines), `scripts/smoke_test.py` (3 edits: CLI args + passthrough + docstring).

## Methodology Challenge

The WO specifies "identical event log digests" as a gate but the engine uses `uuid4()` for `cast_id` — a design choice that makes true byte-equality impossible without either (a) modifying production code to seed UUIDs, or (b) stripping non-deterministic fields before hashing. Option (a) violates the WO constraint "do NOT modify production code," and option (b) means the digest doesn't cover the full event. I chose (b) and documented the gap. The PM should decide whether a future WO should determinize `cast_id` in the spell resolver.

## Field Manual Entry

**#13: When adding determinism gates, run the gate test FIRST with full data, then strip known-nondeterministic fields as a second pass.** The raw-then-cleaned approach catches real non-determinism (like dict ordering or floating-point variance) while documenting engineered non-determinism (like UUIDs). Never strip fields preemptively — you'll mask real bugs.
