## WO-029 Completion Report

### Summary
Implemented the 5 remaining kill switches (KILL-002 through KILL-006) that protect
the narration/Spark boundary. Each kill switch detects a specific failure mode, blocks
further Spark calls, falls back to template narration, and logs structured evidence.

### Files created
- `aidm/narration/kill_switch_registry.py` (229 lines) — KillSwitchID enum, KillSwitchEvidence frozen dataclass, KillSwitchRegistry state machine, MECHANICAL_PATTERNS compiled regex, detect_mechanical_assertions(), build_evidence() helper
- `tests/test_kill_switch_suite.py` (650 lines) — 35 tests across 6 test classes
- `pm_inbox/SONNET_WO-029_KILL_SWITCH_SUITE.md` — This report

### Files modified
- `aidm/narration/guarded_narration_service.py` (790 lines, was 584) — Integrated KillSwitchRegistry, replaced `_kill_switch_active` flag, added KILL-002 through KILL-006 detection in generate_narration(), added `_generate_llm_narration_with_meta()`, added `check_world_state_drift()`, added `_check_kill005()`, updated `_trigger_kill_switch`/`reset_kill_switch`/`is_kill_switch_active` for backward compat

### Tests added: 35

| # | Test | What it verifies |
|---|------|-----------------|
| **KillSwitchRegistry (8)** | |
| 1 | test_registry_starts_clean | No switches triggered initially |
| 2 | test_trigger_sets_active | trigger() → is_triggered returns True |
| 3 | test_any_triggered_true_when_one_active | any_triggered() works |
| 4 | test_reset_clears_specific_switch | reset only clears specified switch |
| 5 | test_reset_preserves_other_switches | other switches unaffected |
| 6 | test_get_evidence_returns_stored | evidence retrievable after trigger |
| 7 | test_get_all_active_lists_all | lists multiple active switches |
| 8 | test_metrics_count_lifetime_triggers | counts persist after reset |
| **KILL-002 Mechanical Assertion (6)** | |
| 9 | test_kill002_detects_damage_number | "deals 15 damage" triggers |
| 10 | test_kill002_detects_ac_reference | "AC 18" triggers |
| 11 | test_kill002_detects_rule_citation | "PHB 145" triggers |
| 12 | test_kill002_clean_narration_passes | "The orc roars in fury" does NOT trigger |
| 13 | test_kill002_falls_back_to_template | after trigger, returns template narration |
| 14 | test_kill002_evidence_captures_match | evidence includes matched pattern and text |
| **KILL-003 Token Overflow (4)** | |
| 15 | test_kill003_detects_overflow | tokens_used > max_tokens * 1.1 triggers |
| 16 | test_kill003_at_boundary_no_trigger | tokens_used == max_tokens * 1.1 does NOT trigger |
| 17 | test_kill003_normal_generation_passes | tokens_used < max_tokens passes |
| 18 | test_kill003_evidence_has_token_counts | evidence includes both counts |
| **KILL-004 Latency (4)** | |
| 19 | test_kill004_detects_slow_generation | mock 11s delay triggers |
| 20 | test_kill004_fast_generation_passes | mock 2s delay passes |
| 21 | test_kill004_at_boundary_no_trigger | exactly 10.0s does NOT trigger |
| 22 | test_kill004_evidence_has_elapsed_time | evidence includes elapsed_ms |
| **KILL-005 Consecutive Rejections (4)** | |
| 23 | test_kill005_triggers_on_third_rejection | 3 consecutive triggers KILL-005 |
| 24 | test_kill005_resets_on_success | successful generation resets counter |
| 25 | test_kill005_mixed_switches_count | different switch types still count |
| 26 | test_kill005_evidence_has_rejection_list | evidence includes types |
| **KILL-006 State Hash Drift (4)** | |
| 27 | test_kill006_detects_world_state_drift | changed world state hash triggers |
| 28 | test_kill006_stable_state_passes | same hash before/after passes |
| 29 | test_kill006_independent_of_kill001 | triggers independently from KILL-001 |
| 30 | test_kill006_evidence_has_both_hashes | evidence includes before/after |
| **Integration (5)** | |
| 31 | test_any_kill_switch_blocks_narration | any active switch raises violation |
| 32 | test_reset_specific_switch_allows_narration | reset → narration works again |
| 33 | test_kill002_in_llm_path_falls_back_silently | mechanical assertion in LLM → template |
| 34 | test_backward_compat_trigger_kill_switch | _trigger_kill_switch() backward compat |
| 35 | test_backward_compat_reset_no_arg | reset_kill_switch() with no arg backward compat |

### Tests passing: 3288 total (full suite), 35 in test_kill_switch_suite.py
- 0 failures, 11 skipped (pre-existing skips), 0 regressions
- All 29 existing narration guardrail tests still pass
- All 49 spark adapter tests still pass

### Boundary law verification
- **BL-001** (Spark must not import Core): PASS
- **BL-002** (Spark must not import Narration): PASS
- **BL-003** (Narration must not import Core): PASS — `kill_switch_registry.py` placed in `aidm/narration/` (not `aidm/core/`), uses only stdlib and narration-local types

### Kill switch verification: each switch testable in isolation
- KILL-001: Migrated to use KillSwitchRegistry (backward compatible via `_trigger_kill_switch()`)
- KILL-002: Regex-based mechanical assertion detection, 5 compiled patterns
- KILL-003: Token overflow check (completion > max_tokens * 1.1)
- KILL-004: time.monotonic() latency measurement, 10s threshold
- KILL-005: Consecutive rejection counter with auto-fire at 3
- KILL-006: World state hash drift via `check_world_state_drift()` method

### Key design decisions

1. **Registry placed in `aidm/narration/kill_switch_registry.py`** — BL-003 prohibits narration from importing aidm.core. Placing it in narration allows the service to import it directly.

2. **Backward compatibility preserved** — `_trigger_kill_switch(reason)`, `reset_kill_switch()` (no args), and `is_kill_switch_active()` all still work for existing tests. The `reset_kill_switch()` accepts an optional `switch_id` parameter (defaults to KILL-001).

3. **Mechanical assertion patterns compiled at module level** — The 5 regex patterns in `MECHANICAL_PATTERNS` are compiled once when the module loads, not per-call.

4. **KILL-006 uses explicit `check_world_state_drift()` method** — Since narration can't access world state directly (BL-003), the caller is responsible for computing hashes and calling `check_world_state_drift(before, after)`. The `NarrationRequest.world_state_hash` field is available for recording the "before" hash.

5. **any_triggered() is O(1)** — The registry maintains a `_any_active` boolean cache that's updated on trigger() and reset().

6. **KILL-005 fires at the moment of the 3rd rejection** — `_check_kill005()` is called after every rejection recording. The counter resets on successful LLM narration generation.

7. **No new dependencies** — only stdlib (`time`, `re`, `traceback`, `enum`, `dataclasses`).
