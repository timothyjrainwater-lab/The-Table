# WO-FULLATTACK-CLI-01 — Full Attack Action in CLI

**Dispatch Authority:** PM (Opus)
**Priority:** Wave B — parallel dispatch (after Wave A completes)
**Risk:** LOW | **Effort:** Medium | **Breaks:** 0 expected
**Depends on:** Wave A complete (WO-CONDFIX-01 INTEGRATED, WO-ROUND-TRACK-01 must be integrated first)

---

## Target Lock

Fighters can only make single attacks. The full attack resolver (`full_attack_resolver.py`) and `FullAttackIntent` routing in `play_loop.py:1104-1137` are complete. Only CLI wiring is missing.

**Goal:** `full attack goblin warrior` invokes the full attack pipeline. Multiple iterative attacks displayed.

---

## Binary Decisions (Locked)

1. **Parser keyword:** `"full attack"` as a two-word verb. Check BEFORE single-word verb split.
2. **Target resolution:** Reuse existing `IntentBridge.resolve_attack()` to get `AttackIntent`, then promote to `FullAttackIntent`.
3. **BAB source:** Read from `entity.get(EF.BAB, 1)` — current fixture Aldric has BAB 3 (1 attack). Consider bumping to BAB 6 in fixture for playtest value (gets +6/+1 iterative).
4. **Display:** `format_events()` already handles multiple `attack_roll` + `damage_roll` events — no display changes needed.

---

## Contract Spec

### File Scope (2 files)

| File | Action | Lines |
|------|--------|-------|
| `play.py` | Modify `parse_input()` (lines 64-119), `resolve_and_execute()` (lines 138-207), `_HELP_TEXT` (lines 122-131) | Add `"full attack"` two-word detection, add `full_attack` action routing, update help |
| `tests/test_play_cli.py` | Add ~8 new tests | Parser, resolution, multi-hit display |

### Implementation Detail

**Parser change (play.py, inside `parse_input()`, BEFORE single-word verb check):**
```python
# Before line 71 (verb = parts[0]):
# Two-word commands — check before single-word verb split
if text.startswith("full attack"):
    target_ref = text[len("full attack"):].strip()
    target_ref = _strip_articles(target_ref) if target_ref else None
    return "full_attack", DeclaredAttackIntent(target_ref=target_ref, weapon=None)
```

**Resolution change (play.py, inside `resolve_and_execute()`, add elif branch):**
```python
elif action_type == "full_attack":
    resolved = bridge.resolve_attack(actor_id, declared, view)
    if isinstance(resolved, ClarificationRequest):
        # ... clarification handling (same as attack) ...
    # Promote AttackIntent to FullAttackIntent
    from aidm.core.full_attack_resolver import FullAttackIntent
    entity = ws_copy.entities[actor_id]
    resolved = FullAttackIntent(
        attacker_id=actor_id,
        target_id=resolved.target_id,
        base_attack_bonus=entity.get(EF.BAB, 1),
        weapon=resolved.weapon,
    )
```

**Help text:** Add `full attack <target>          full attack goblin warrior` line.

### Frozen Contracts

None touched.

---

## Implementation Sequencing

1. Add two-word `"full attack"` detection in `parse_input()` before `verb = parts[0]`
2. Add `"full_attack"` branch in `resolve_and_execute()` — resolve via bridge then promote to `FullAttackIntent`
3. Update `_HELP_TEXT` with `full attack` command
4. Add tests:
   - `test_parse_full_attack` — parser returns `("full_attack", DeclaredAttackIntent)`
   - `test_parse_full_attack_with_target` — target extracted correctly
   - `test_full_attack_resolves` — resolve_and_execute returns events
   - `test_full_attack_multiple_hits_at_high_bab` — BAB 6+ produces 2 attack_roll events
   - `test_full_attack_single_hit_at_low_bab` — BAB <6 produces 1 attack_roll
   - `test_full_attack_help_text` — help includes "full attack"
   - `test_full_attack_no_target` — clarification request
   - `test_full_attack_articles_stripped` — "full attack the goblin" works
5. Run `python -m pytest tests/test_play_cli.py -x` then full suite

---

## Acceptance Criteria

1. `full attack goblin warrior` parses and executes
2. Multiple attack rolls displayed at BAB 6+
3. Single attack at BAB <6 (graceful, not an error)
4. Help text updated
5. All existing tests pass
6. ~8 new tests pass

---

## Agent Instructions

- Read `AGENT_ONBOARDING_CHECKLIST.md` and `AGENT_DEVELOPMENT_GUIDELINES.md` before starting
- This WO modifies `play.py` parser and resolution ONLY. Do NOT modify `play_loop.py`, `full_attack_resolver.py`, or any core engine file
- Do NOT modify `format_events()` — it already handles multiple attack/damage events
- The `FullAttackIntent` constructor requires: `attacker_id`, `target_id`, `base_attack_bonus`, `weapon`
- `FullAttackIntent` is imported from `aidm.core.full_attack_resolver` (line 68)
- Run full suite before declaring completion
