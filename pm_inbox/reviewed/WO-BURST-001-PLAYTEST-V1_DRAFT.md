# WO-BURST-001-PLAYTEST-V1 — Audio-First CLI Playtest v1

**Type:** PLAYTEST
**Priority:** BURST-001 Tier 5.5 (FINAL)
**Depends on:** WO-IMPL-PRESSURE-ALERTS-001 (4.3 ACCEPTED) + WO-IMPL-SALIENCE-FILTER-001 (4.4 ACCEPTED)
**Blocked by:** 4.3 + 4.4 verdicts — DO NOT DISPATCH until both ACCEPTED
**Lifecycle:** DRAFT

---

## Target Lock

Execute the MVVL (Minimum Viable Voice Loop) playtest scenario and produce a compliance report proving that all BURST-001 reliability gates (B1-B5) hold under integrated conditions. This is not an implementation WO — all code is complete. This is the final validation that closes BURST-001.

**What "done" looks like:** A playtest report documenting 30 checkpoints (all GREEN), 10 MVVL threshold metrics (all GREEN), and B1-B5 gate verification (all PASS). BURST-001 is COMPLETE when this WO is ACCEPTED.

## Binary Decisions (all resolved)

| # | Question | Answer | Source |
|---|----------|--------|--------|
| 1 | Is this a code WO? | No — evaluation/validation only. No new production code. | Playbook §9 |
| 2 | Who executes the playtest? | Builder runs the scenario, collects evidence, writes report. | PM dispatch protocol |
| 3 | What seed? | 42 (determinism baseline). | Playbook §9.3 |
| 4 | What TTS backend? | Chatterbox (GPU) primary. Kokoro (CPU) fallback acceptable. | Playbook §9.3 |
| 5 | What fixture? | Standard combat: 2 PCs vs 2 enemies. | Playbook §9.3 |
| 6 | Can 5.5 PASS with YELLOW thresholds? | No. All 10 metrics must be GREEN. Any RED = FAIL. | Playbook §9.2 |

## Contract Spec

**Source:** Voice-First Reliability Playbook §9 (MVVL definition), BURST_INTAKE_QUEUE.md (B1-B5 gates), CLI Grammar Contract (G-01..G-07), Boundary Pressure Contract §6.3, Unknown Handling Contract, Typed Call Contract.

### Part 1: MVVL Core Requirements

The playtest validates this end-to-end loop:

1. Operator speaks a combat command (STT or typed)
2. IntentBridge resolves to a single action (or asks clarification)
3. Box resolves the action deterministically
4. CLI outputs result in grammar-compliant format (G-01..G-07)
5. TTS speaks TURN + RESULT + NARRATION + PROMPT lines (S1-S4)
6. `[AIDM]` and `[RESOLVE]` lines are NOT spoken (S5-S6 filtered)
7. Operator prompt ("Your action?") is spoken in distinct voice (Arbor persona)
8. Replay with same seed produces identical non-Spark output (determinism)

### Part 2: 30-Checkpoint Playtest Scenario

**Fixture:** 2 PCs vs 2 enemies. Seed 42. TTS: Chatterbox (GPU) or Kokoro (CPU fallback).

#### Step 1: Combat Initialization (3 checkpoints)
- [ ] **CP-01:** Initiative displayed correctly — names sorted by roll
- [ ] **CP-02:** TTS speaks turn order — names only, no numbers
- [ ] **CP-03:** Initiative list is deterministic (replay-identical)

#### Step 2: Turn Banners (4 checkpoints × 2 turns = 8 checkpoints)
- [ ] **CP-04:** Banner format matches G-01 exactly ("Name's Turn")
- [ ] **CP-05:** No dashes, no prefix in banner
- [ ] **CP-06:** Blank line after banner
- [ ] **CP-07:** TTS audible, distinct from system noise
- [ ] **CP-08:** Second turn banner — same format (G-01)
- [ ] **CP-09:** Second turn — no dashes, no prefix
- [ ] **CP-10:** Second turn — blank line after
- [ ] **CP-11:** Second turn — TTS audible

#### Step 3: Action Resolution & Narration (6 checkpoints)
- [ ] **CP-12:** Grammar constraint G-02 — result is 2 sentences max
- [ ] **CP-13:** No mechanical numbers in spoken output
- [ ] **CP-14:** Narration is 1-3 sentences (G-04)
- [ ] **CP-15:** Min 8 words per sentence in narration
- [ ] **CP-16:** Max 120 chars per narration line
- [ ] **CP-17:** TTS prosody natural (not flat, not over-emphasized)

#### Step 4: Salience Routing & Speaker Identity (4 checkpoints)
- [ ] **CP-18:** Prompt ("Your action?") is G-05 exact match
- [ ] **CP-19:** Prompt TTS voice is Arbor (distinct from DM persona)
- [ ] **CP-20:** No `[AIDM]` lines in spoken output (S6 filter working)
- [ ] **CP-21:** No `[RESOLVE]` lines in spoken output (S5 filter working)

#### Step 5: Alerts & Boundary Pressure (3 checkpoints)
- [ ] **CP-22:** Entity defeat alert: "Name is DEFEATED." (G-03: STATUS all-caps)
- [ ] **CP-23:** Alert routed to TTS with emphasis/urgency tone
- [ ] **CP-24:** If RED boundary pressure fires: no Spark call, template fallback used

#### Step 6: Round Structure (4 checkpoints)
- [ ] **CP-25:** Round header present between rounds
- [ ] **CP-26:** Round header spoken by TTS
- [ ] **CP-27:** Turn order maintained across rounds
- [ ] **CP-28:** No duplicate voice output per event (B1)

#### Step 7: Determinism Verification (2 checkpoints)
- [ ] **CP-29:** Replay with seed 42 — non-Spark output lines byte-identical
- [ ] **CP-30:** Spark output structure (line tags, salience) identical even if narration text differs

### Part 3: MVVL GREEN Thresholds (10 metrics)

All must be GREEN to pass.

| # | Metric | GREEN | RED |
|---|--------|-------|-----|
| M-01 | Intent parse success (unambiguous) | >= 80% of test utterances | < 60% |
| M-02 | Box resolution latency (p95) | < 200ms | > 500ms |
| M-03 | TTS generation latency (p95, per line) | < 3s | > 8s |
| M-04 | Grammar compliance (G-01..G-07) | 100% of output lines | < 95% |
| M-05 | Forbidden content in spoken output | 0 violations | 3+ per session |
| M-06 | Golden transcript match (non-Spark) | 100% byte-identical | < 100% |
| M-07 | Salience routing accuracy | 100% (S5/S6 never spoken) | Any S5/S6 spoken |
| M-08 | Boundary pressure detection | All RED events block Spark | Any RED missed |
| M-09 | Template fallback correctness | 100% (valid output) | Any invalid fallback |
| M-10 | Playtest checklist pass rate | 30/30 | < 25/30 |

### Part 4: B1-B5 Reliability Gate Verification

These are acceptance criteria from the BURST-001 scoping (DC-05). Each must PASS.

| Gate | Requirement | Verified By |
|------|-------------|-------------|
| B1 | Single-path playback — no duplicate chimes, no double voice, one emitter per event | CP-28, session log audit |
| B2 | Deterministic routing — same inputs → same persona, register, reference set | CP-29, CP-30, golden transcript comparison |
| B3 | Swap timing instrumentation — measure load, unload, TTFT, first-audio | Session log fields (Gate O instrumentation) |
| B4 | Soak stability — 10 cycles without VRAM creep or routing degradation | Extended run (10 rounds minimum) |
| B5 | Sensor log replay — same audio chunks → same transcript + downstream events | CP-29, CP-30 (seed-based replay) |

## Implementation Plan

1. **Pre-Playtest Audit (automated):**
   - Run `python scripts/check_cli_grammar.py` — all output lines pass G-01..G-07
   - Run `python scripts/check_typed_call.py` — all CallType schemas valid
   - Run `python -m pytest tests/test_forbidden_claims_p.py -v` — zero forbidden patterns
   - Run `python -m pytest tests/test_boundary_pressure_impl_n.py -v` — all pressure scenarios pass
   - Run full suite regression: `python -m pytest tests/ -x --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py`

2. **Scenario Setup:**
   - Create 2 PCs and 2 enemies using standard fixture
   - Set seed to 42
   - Enable TTS (Chatterbox GPU or Kokoro CPU fallback)
   - Enable session logging (structured JSON to `logs/`)

3. **Execute 30-Checkpoint Scenario:**
   - Walk through Steps 1-7 above
   - Document each checkpoint pass/fail with evidence (CLI output snippets, TTS audio confirmation)
   - Capture all boundary pressure events, unknown handling decisions, Spark calls/fallbacks

4. **Determinism Replay:**
   - Replay scenario with seed 42
   - Compare non-Spark output lines for byte-identity
   - Document any Spark narration differences (expected — LLM non-determinism)

5. **Metrics Collection:**
   - Compute M-01 through M-10 from session logs and checkpoint results
   - Report GREEN/YELLOW/RED for each

6. **B1-B5 Gate Verification:**
   - Audit session logs for B1 (single-path), B3 (timing fields), B4 (soak)
   - Use determinism replay for B2 and B5

7. **Report Assembly:**
   - Write playtest report to `pm_inbox/`
   - Include: checkpoint table (30 rows), metrics table (10 rows), B1-B5 gate table (5 rows)
   - Attach session logs as evidence

### Out of Scope

- New production code (all implementation is done in Tiers 1-4)
- Changes to contracts, schemas, or gate tests
- STT integration testing (STT is a separate track — typed input is acceptable for this playtest)
- Performance optimization (this playtest measures, it doesn't fix)
- Extended soak testing beyond 10 rounds (future WO if needed)

## Gate Specification

**No new gate tests.** This WO validates existing gates (A-U) under integrated conditions. The deliverable is the playtest report itself.

**Pass criteria for PM verdict:**
1. All 30 checkpoints documented with evidence
2. All 10 MVVL metrics at GREEN threshold
3. All 5 B-gates verified PASS
4. Full suite regression: zero new failures
5. Session logs attached

**Expected deliverable count:** 1 playtest report + session logs.

## Integration Seams

- `scripts/check_cli_grammar.py` — Pre-playtest grammar audit
- `scripts/check_typed_call.py` — Pre-playtest schema audit
- `tests/test_forbidden_claims_p.py` — Forbidden content check
- `tests/test_boundary_pressure_impl_n.py` — Pressure scenario check
- `aidm/runtime/session_orchestrator.py` — End-to-end runtime under test
- `aidm/voice/line_classifier.py` — Salience filter (4.4 deliverable, must exist)
- `aidm/immersion/prosodic_preset_manager.py` — Pressure modulation (4.3 deliverable, must exist)

## Files to Read

1. `pm_inbox/reviewed/legacy_pm_inbox/research/VOICE_FIRST_RELIABILITY_PLAYBOOK.md` — §9 MVVL definition (source of truth for checkpoints and thresholds)
2. `docs/contracts/CLI_GRAMMAR_CONTRACT.md` — G-01..G-07 grammar rules
3. `docs/contracts/BOUNDARY_PRESSURE_CONTRACT.md` — Pressure evaluation and response mapping
4. `docs/contracts/TYPED_CALL_CONTRACT.md` — CallType schemas and fallback templates
5. `docs/contracts/UNKNOWN_HANDLING_CONTRACT.md` — Failure classification

## Preflight

```bash
python scripts/preflight_canary.py
python scripts/check_cli_grammar.py
python scripts/check_typed_call.py
python -m pytest tests/test_forbidden_claims_p.py -v
python -m pytest tests/test_boundary_pressure_impl_n.py -v
python -m pytest tests/ -x --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ws_bridge.py
```

## Delivery Footer

**Commit requirement:** No code changes expected. If any fixes are needed, commit with descriptive message referencing this WO ID.
**Debrief format:** PLAYTEST — 500 words max. Sections: (1) Pre-Audit Results, (2) Checkpoint Summary (30/30), (3) Metrics Table (10 GREEN thresholds), (4) B1-B5 Gate Summary, (5) Findings (if any). Radar (3 lines).
**Radar bank:** (1) Anything that broke unexpectedly, (2) Any checkpoint that was ambiguous or hard to verify, (3) Any threshold that was close to YELLOW.

## Assumptions to Validate

1. TTS backend (Chatterbox or Kokoro) is available and functional
2. `aidm/voice/line_classifier.py` exists (4.4 deliverable)
3. `ProsodicPresetManager.apply_pressure_modulation()` exists (4.3 deliverable)
4. Session logging produces structured JSON with boundary pressure events
5. Seed 42 produces a combat scenario with at least one entity defeat (for CP-22/23)

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Playtest complete. BURST-001 awaiting verdict."
```
