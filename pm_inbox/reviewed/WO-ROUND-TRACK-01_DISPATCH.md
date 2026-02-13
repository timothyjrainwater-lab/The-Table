# WO-ROUND-TRACK-01 — Round Counter and Turn Display

**Dispatch Authority:** PM (Opus)
**Priority:** Wave A — immediate (completes Wave A)
**Risk:** LOW | **Effort:** Small | **Breaks:** ~2 transcript tests
**Depends on:** WO-CONDFIX-01 (INTEGRATED at af77038)

---

## Target Lock

The CLI shows individual turns but no round boundaries. Multi-round combat is disorienting — the player has no sense of temporal flow. The `round_index` field is initialized at 0 in `active_combat` (play_controller.py:245) but is never incremented or displayed.

**Goal:** Print `=== Round N ===` header at each round boundary. Increment the round counter.

---

## Binary Decisions (Locked)

1. **Round numbering starts at 1** (human-facing display). Internal `round_index` can remain 0-based.
2. **Round boundary = top of initiative order.** When the `for actor_id in init_order` loop restarts at index 0, a new round begins.
3. **Header format:** `=== Round N ===` (matches existing `=` separator style in play.py).
4. **First round header prints before the first player turn** (after initiative display, before the `while True` loop body).

---

## Contract Spec

### File Scope (3 files)

| File | Action | Lines |
|------|--------|-------|
| `play.py` | Modify `_main_loop()` (lines 418-533) | Add round counter variable, print round header at boundary, increment `active_combat["round_index"]` |
| `tests/test_play_cli.py` | Update `test_seed_42_transcript_is_stable` (line 566) | Transcript now includes round headers — compare still works if both runs produce same output |
| `tests/test_play_cli.py` | Add ~5 new tests | Round header appears, counter increments, round boundary detection |

### Implementation Detail

**In `_main_loop()` (play.py:418):**

```python
# After line 423 (next_event_id = 0):
round_number = 1

# Before line 451 (while True:), print first round header:
print(f"\n{'=' * 20} Round {round_number} {'=' * 20}")

# Inside the while True loop, after line 459 (for actor_id in init_order:):
# Detect round boundary — when we reach the first living actor in init_order
# This means the for-loop restarted. Track it:
```

**Round boundary logic:**
```python
round_number = 1
print(f"\n{'=' * 20} Round {round_number} {'=' * 20}")

while True:
    over, reason = is_combat_over(ws)
    if over:
        # ... existing code ...
        return

    for actor_id in init_order:
        # ... existing per-actor code ...

    # After the for-loop completes (all actors acted), a new round begins
    round_number += 1
    ws.active_combat["round_index"] = round_number - 1  # 0-based internal
    print(f"\n{'=' * 20} Round {round_number} {'=' * 20}")
```

**Key insight:** The round boundary is the *completion of the for-loop*, not the start. After every actor in `init_order` has acted (or been skipped if defeated), the next iteration of the `while True` loop is a new round. Print the header after the for-loop, before the next combat-over check.

### Frozen Contracts

None touched. `play.py` and `tests/test_play_cli.py` are not frozen.

---

## Implementation Sequencing

1. Add `round_number = 1` variable in `_main_loop()` after line 423
2. Print initial round header `=== Round 1 ===` before the `while True` loop (after status display)
3. After the inner `for actor_id in init_order` loop completes, increment `round_number` and print next round header
4. Update `ws.active_combat["round_index"]` at each round boundary
5. Run existing tests — expect `test_seed_42_transcript_is_stable` and `test_determinism` to still pass (both runs produce identical output including round headers)
6. Add new tests:
   - `test_round_header_appears_in_output` — "Round 1" visible in first output
   - `test_round_counter_increments` — "Round 2" appears after all actors have acted
   - `test_round_index_updates_in_active_combat` — `ws.active_combat["round_index"]` reflects round count
   - `test_round_header_format` — exact format `=== Round N ===` matches
   - `test_round_boundary_skips_defeated_actors` — defeated actors don't delay round boundary
7. Run full test suite — 0 failures expected (additive output doesn't break substring assertions)

---

## Acceptance Criteria

1. `=== Round 1 ===` header visible at start of combat
2. `=== Round N ===` header appears at each round boundary
3. `ws.active_combat["round_index"]` incremented correctly
4. All existing tests pass (transcript tests produce identical output on both runs)
5. ~5 new tests pass

---

## Regression Watch

- `test_seed_42_transcript_is_stable` (line 566): Compares two runs byte-for-byte. Both runs will have round headers, so they should still match. If the test fails, it means round header printing is non-deterministic (it shouldn't be).
- `test_determinism` (line 398): Same seed + same actions = same outcome. Round headers are deterministic (pure function of initiative order iteration), so this should pass.
- `test_combat_completes` (line 383): Feeds 60 attack commands. Should still terminate — round headers are print-only, no logic change.

---

## Agent Instructions

- Read `AGENT_ONBOARDING_CHECKLIST.md` and `AGENT_DEVELOPMENT_GUIDELINES.md` before starting
- Do NOT modify any frozen contracts
- Do NOT add features beyond scope (no turn timer, no initiative re-roll, no fancy formatting)
- Run `python -m pytest tests/test_play_cli.py -x` after changes
- Run full suite `python -m pytest --tb=short -q` before declaring completion
- Report completion with test counts
