# WO-BUGFIX-TIER0-001 — Tier 0 Correctness Bugs from Action Economy Audit

**Dispatch Authority:** PM (Opus)
**Priority:** Tier 0 — correctness bugs that produce wrong math. Fix before any further playtesting.
**Risk:** MEDIUM | **Effort:** Medium | **Breaks:** 0 expected (existing tests pass; new tests added)
**Depends on:** None. All fixes are in non-frozen files.
**Source:** `docs/research/ACTION_ECONOMY_AUDIT.md` Section X
**Lifecycle:** NEW

---

## Target Lock

The Action Economy Audit (2026-02-13) identified 10 correctness bugs in combat resolvers. 4 are rated HIGH — they produce wrong damage math or wrong AC calculations that deviate from PHB 3.5e RAW. These 4 bugs must be fixed before playtest signals can be trusted.

**Goal:** All 4 HIGH bugs fixed with regression tests. Existing tests remain green.

---

## Binary Decisions (Locked)

1. **BUG-1 fix scope:** Two-handed STR 1.5x applies only to melee weapons with `is_two_handed=True`. Formula: `int(str_modifier * 1.5)` (round down per PHB p.114). Off-hand weapons (future TWF) get 0.5x — NOT in scope for this WO.
2. **BUG-2 fix scope:** Full attack loop breaks when target HP reaches 0 or below after any single attack. Remaining iterative attacks are NOT redirected to other targets (no Cleave/Great Cleave yet). The existing accumulate-then-apply pattern is replaced with per-attack HP application.
3. **BUG-3/BUG-4 fix scope:** The `ac_modifier` on Prone and Helpless conditions stays at -4. The fix is in the **consumer** (attack_resolver.py), not the condition definition. When `is_ranged` is True, the resolver ignores the Prone/Helpless `ac_modifier` (Prone gets +4 instead, Helpless gets 0). This avoids changing the frozen condition schema.
4. **is_ranged detection:** For this WO, `is_ranged` remains hardcoded False (no ranged attack system exists). The fix adds the **plumbing** so that when ranged attacks are implemented (future WO), the condition modifier logic is already correct. A new helper `_get_condition_ac_modifier(modifiers, is_ranged)` encapsulates the melee/ranged branching.

---

## Contract Spec

### File Scope (4 files)

| File | Action | Bug |
|------|--------|-----|
| `aidm/core/attack_resolver.py` | Fix STR 1.5x for two-handed (line ~367), add `_get_condition_ac_modifier()` helper | BUG-1, BUG-3/4 |
| `aidm/core/full_attack_resolver.py` | Fix STR 1.5x (line ~298), per-attack defeat check in loop (lines ~546-590) | BUG-1, BUG-2 |
| `tests/test_bugfix_tier0.py` | New — ~20 tests | All 4 bugs |
| `tests/test_play_cli.py` | Update any gold masters affected by damage changes | If needed |

### Implementation Detail

**BUG-1: Two-handed STR 1.5x (attack_resolver.py, line ~367):**
```python
# Before:
base_damage = sum(damage_rolls) + intent.weapon.damage_bonus + str_modifier

# After:
if intent.weapon.is_two_handed:
    effective_str = int(str_modifier * 1.5)  # PHB p.114: 1.5x STR for two-handed
else:
    effective_str = str_modifier
base_damage = sum(damage_rolls) + intent.weapon.damage_bonus + effective_str
```

Same fix in `full_attack_resolver.py` line ~298.

**BUG-2: Per-attack defeat check (full_attack_resolver.py):**
```python
# Replace accumulate-then-apply pattern with per-attack application
hp_remaining = hp_current

for attack_index, raw_attack_bonus in enumerate(attack_bonuses):
    # ... existing attack resolution ...

    attack_events, current_event_id, damage = resolve_single_attack_with_critical(...)
    events.extend(attack_events)

    if damage > 0:
        hp_remaining -= damage
        # Emit hp_changed event per attack
        events.append(Event(
            event_id=current_event_id,
            event_type="hp_changed",
            ...
            payload={"hp_before": hp_remaining + damage, "hp_after": hp_remaining, "delta": -damage, ...}
        ))
        current_event_id += 1

        if hp_remaining <= 0:
            # Emit defeat event and break
            events.append(Event(...event_type="entity_defeated"...))
            current_event_id += 1
            break

# Remove the old post-loop damage application block
```

**BUG-3/BUG-4: Condition AC modifier branching (attack_resolver.py):**
```python
def _get_condition_ac_modifier(attacker_modifiers, is_ranged: bool) -> int:
    """Apply melee/ranged-aware condition AC modifiers.

    PHB p.311:
    - Prone: -4 AC vs melee, +4 AC vs ranged
    - Helpless: -4 AC vs melee, 0 vs ranged

    Current implementation: conditions store -4 (melee case).
    This function adjusts for ranged when is_ranged=True.
    """
    base_ac_mod = attacker_modifiers.ac_modifier

    if not is_ranged:
        return base_ac_mod  # Melee: use stored value as-is

    # Ranged: if target is prone, flip -4 to +4
    # if target is helpless, neutralize -4 to 0
    # Detection: check if prone/helpless flags are set on target conditions
    # For now, return base_ac_mod (is_ranged is always False)
    # When ranged attacks exist, this function will query target conditions
    return base_ac_mod
```

**Note:** The full ranged AC branching requires querying target conditions for Prone/Helpless state, which requires passing target condition data into this helper. The helper signature and call site are established in this WO; the ranged branch logic activates when `is_ranged` becomes dynamic (future ranged attack WO).

### Test Plan (tests/test_bugfix_tier0.py)

**BUG-1 tests (~6):**
- Two-handed weapon adds `int(STR * 1.5)` to damage (STR 16 = +4 → +6)
- One-handed weapon adds STR 1x to damage
- Negative STR modifier with two-handed (STR 8 = -1 → -1, floor of -1.5)
- Full attack with two-handed weapon gets 1.5x on each iterative attack
- Power Attack + two-handed STR stack correctly

**BUG-2 tests (~6):**
- Full attack stops after target is defeated by first attack
- Full attack stops after target is defeated by second attack
- hp_changed events emitted per-attack (not accumulated)
- entity_defeated event emitted at correct point
- RNG consumed only for attacks actually made (determinism check)
- Single-attack full attack (BAB < 6) behaves identically

**BUG-3/BUG-4 tests (~6):**
- `_get_condition_ac_modifier()` returns base modifier when is_ranged=False
- Helper exists and is callable (plumbing test)
- Prone condition stored modifier is -4 (schema unchanged)
- Helpless condition stored modifier is -4 (schema unchanged)
- Integration: attack against prone target with is_ranged=False gets -4 AC (correct)
- Integration: melee attack damage against prone target unchanged from current behavior

**Regression (~2):**
- Existing attack_resolver test suite passes
- Existing full_attack_resolver test suite passes
