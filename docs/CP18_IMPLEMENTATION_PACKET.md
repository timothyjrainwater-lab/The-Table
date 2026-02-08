# CP-18 IMPLEMENTATION INSTRUCTION PACKET

## Audience: Implementation Agent
## Project: Deterministic D&D 3.5e AI Dungeon Master (AIDM)
## Authority: Binding (Implementation-Constrained)
## Prerequisites: CP-18 Design ACCEPTED
## Date: 2026-02-08

---

## 0. PURPOSE OF THIS PACKET

This packet authorizes and constrains **IMPLEMENTATION** of **CP-18 (Combat Maneuvers)**.

The design is complete and frozen in [CP18_COMBAT_MANEUVERS_DECISIONS.md](CP18_COMBAT_MANEUVERS_DECISIONS.md).

You are authorized to write code that implements the design **exactly as specified**.

---

## 1. AUTHORITATIVE INPUTS (READ FIRST)

Treat the following as canonical:

1. **CP18_COMBAT_MANEUVERS_DECISIONS.md** — Design specification (BINDING)
2. **CP18_ACCEPTANCE_RECORD.md** — Degradations and gate safety (BINDING)
3. **CP15_AOO_DECISIONS.md** — AoO integration patterns
4. **CP16_CONDITIONS_DECISIONS.md** — Condition application patterns
5. **CP18A_MOUNTED_COMBAT_DECISIONS.md** — Mounted trip integration

If your implementation deviates from the design document, your implementation is wrong.

---

## 2. FILE-LEVEL TOUCH MAP

### 2.1 Files to CREATE

| File | Purpose | Estimated Size |
|------|---------|----------------|
| `aidm/schemas/maneuvers.py` | Intent and result schemas | ~200 lines |
| `aidm/core/maneuver_resolver.py` | Core resolution logic | ~600 lines |
| `tests/test_maneuvers_core.py` | Tier-1 unit tests | ~400 lines |
| `tests/test_maneuvers_integration.py` | Tier-2 integration tests | ~300 lines |

### 2.2 Files to MODIFY

| File | Change | Lines Affected |
|------|--------|----------------|
| `aidm/schemas/entity_fields.py` | Add SIZE_CATEGORY, STABILITY_BONUS, GRAPPLE_SIZE_MODIFIER | ~5 lines |
| `aidm/core/play_loop.py` | Route maneuver intents to resolver | ~30 lines |
| `aidm/core/aoo.py` | Extend AoO triggers for maneuver intents | ~20 lines |

### 2.3 Files NOT to touch

❌ `aidm/core/attack_resolver.py` — No changes needed
❌ `aidm/core/full_attack_resolver.py` — No changes needed
❌ `aidm/core/conditions.py` — Use existing, do not modify
❌ `aidm/schemas/conditions.py` — Use existing, do not modify
❌ `aidm/core/mounted_combat.py` — Use existing for trip-vs-mounted

---

## 3. FORBIDDEN CHANGES LIST

The following are **EXPLICITLY FORBIDDEN**:

### 3.1 Gate Violations

❌ **G-T3C**: No bidirectional grapple state (attacker must NOT have "grappling" condition)
❌ **G-T2A**: No persistent stat modifications
❌ **G-T3A**: No entity creation/forking

### 3.2 Scope Creep

❌ No Improved X feats (Improved Trip, Improved Grapple, etc.)
❌ No persistent item damage from Sunder
❌ No weapon ownership transfer from Disarm
❌ No trip weapon mechanics
❌ No Escape Artist checks
❌ No grapple pinning
❌ No grapple damage
❌ No grapple escape loops
❌ No multi-round grapple state

### 3.3 Technical Violations

❌ No floating point in RNG paths
❌ No `set()` objects in WorldState
❌ No bare string literals for entity fields (use `EF.*`)
❌ No unsorted JSON serialization
❌ No new RNG streams (use `"combat"` only)

---

## 4. DETERMINISM CHECKLIST

For each maneuver, verify:

- [ ] RNG consumption order matches design document exactly
- [ ] Same intent + same RNG seed = identical events
- [ ] Same intent + same RNG seed = identical final state hash
- [ ] AoO resolution uses CP-15 ordering (initiative → lexicographic)
- [ ] Opposed checks consume RNG in order: attacker roll, then defender roll
- [ ] Counter-attack rolls (if any) follow main rolls

### 4.1 RNG Consumption Order (Reference)

**Bull Rush:**
```
1. AoO attack rolls (CP-15 order)
2. AoO damage rolls
3. Attacker Strength check (d20)
4. Defender Strength check (d20)
```

**Trip:**
```
1. AoO attack rolls (CP-15 order)
2. AoO damage rolls
3. Touch attack roll (d20)
4. Attacker trip check (d20)
5. Defender trip check (d20)
6. [If counter-trip] Defender counter-trip (d20)
7. [If counter-trip] Attacker counter-trip defense (d20)
```

**Overrun:**
```
1. AoO attack rolls (CP-15 order)
2. AoO damage rolls
3. Attacker overrun check (d20)
4. Defender overrun check (d20)
```

**Sunder:**
```
1. AoO attack rolls (CP-15 order)
2. AoO damage rolls
3. Attacker attack roll (d20)
4. Defender attack roll (d20)
5. [If success] Damage roll (weapon dice)
```

**Disarm:**
```
1. AoO attack rolls (CP-15 order)
2. AoO damage rolls
3. Attacker attack roll (d20)
4. Defender attack roll (d20)
5. [If counter-disarm] Defender attack roll (d20)
6. [If counter-disarm] Attacker attack roll (d20)
```

**Grapple:**
```
1. AoO attack rolls (CP-15 order)
2. AoO damage rolls
3. Touch attack roll (d20)
4. Attacker grapple check (d20)
5. Defender grapple check (d20)
```

---

## 5. INTEGRATION REQUIREMENTS

### 5.1 CP-15 (AoO) Integration

Extend `check_aoo_triggers()` to recognize maneuver intents:

```python
# Maneuvers that provoke AoOs from defender:
# - BullRushIntent: provokes from all threatening (including target)
# - TripIntent: provokes from target only
# - OverrunIntent: provokes from target only (entering space)
# - SunderIntent: provokes from target only
# - DisarmIntent: provokes from target only
# - GrappleIntent: provokes from target only
```

### 5.2 CP-16 (Conditions) Integration

Use existing condition factories:

```python
from aidm.schemas.conditions import create_prone_condition, create_grappled_condition
from aidm.core.conditions import apply_condition

# Trip success:
world_state = apply_condition(world_state, target_id,
    create_prone_condition(source="trip_attack", applied_at_event_id=event_id))

# Grapple success:
world_state = apply_condition(world_state, target_id,
    create_grappled_condition(source="grapple_attack", applied_at_event_id=event_id))
```

### 5.3 CP-18A (Mounted Combat) Integration

For trip vs mounted target:

```python
# If target is mounted, check if using Ride check
target = world_state.entities.get(target_id)
if target.get(EF.MOUNTED_STATE) is not None:
    # Defender may use Ride check instead of Str/Dex
    # If trip succeeds, trigger forced dismount via CP-18A
    from aidm.core.mounted_combat import trigger_forced_dismount
```

---

## 6. ACCEPTANCE CHECKLIST

Before declaring CP-18 COMPLETE:

### 6.1 Test Requirements

- [ ] All new tests pass
- [ ] All 626 existing tests still pass (zero regressions)
- [ ] Full test suite runs in under 2 seconds
- [ ] Minimum 9 Tier-1 tests (per design document)
- [ ] Minimum 3 Tier-2 tests (per design document)
- [ ] 1 PBHA test (10× determinism replay)

### 6.2 Functional Requirements

- [ ] Bull Rush moves target on success
- [ ] Bull Rush pushes attacker back on failure
- [ ] Trip applies Prone condition on success
- [ ] Trip allows counter-trip on failure
- [ ] Overrun applies Prone on success
- [ ] Overrun defender can avoid (AI-controlled)
- [ ] Sunder emits damage event (narrative only, no state change)
- [ ] Disarm emits weapon drop event (no persistent state)
- [ ] Grapple applies Grappled condition to target ONLY
- [ ] All maneuvers provoke AoOs correctly
- [ ] AoO damage causes Disarm/Grapple auto-failure
- [ ] Size modifiers applied correctly (±4 per category)
- [ ] Grapple uses special size scale (-16 to +16)
- [ ] Stability bonus (+4) applied for dwarves/quadrupeds
- [ ] Charge bonus (+2) applied for Bull Rush/Overrun

### 6.3 Determinism Requirements

- [ ] 10× replay produces identical state hashes
- [ ] RNG consumption order matches design exactly
- [ ] Event ordering matches design exactly

### 6.4 Gate Safety Requirements

- [ ] Grapple is unidirectional (defender only has condition)
- [ ] Sunder has no persistent item state change
- [ ] Disarm has no persistent item state change
- [ ] No new entity fields beyond SIZE_CATEGORY, STABILITY_BONUS, GRAPPLE_SIZE_MODIFIER

### 6.5 Documentation Requirements

- [ ] `PROJECT_STATE_DIGEST.md` updated with CP-18 entry
- [ ] Test count updated (626 → new count)
- [ ] Module inventory updated

---

## 7. ESCALATION RULES

STOP and escalate if:

- A maneuver cannot be implemented without crossing a closed gate
- Determinism requires state that persists across turns
- CP-15/16/18A integration produces unexpected behavior
- Test count regression occurs

Do NOT improvise fixes. Report and await guidance.

---

## 8. DEFINITION OF DONE

CP-18 is COMPLETE when:

1. ✅ All files created per touch map
2. ✅ All files modified per touch map
3. ✅ All acceptance criteria met
4. ✅ All tests pass (626 + new tests)
5. ✅ Determinism verified (10× replay)
6. ✅ Gate safety verified
7. ✅ PROJECT_STATE_DIGEST.md updated

---

## FINAL DIRECTIVE

Implement the design **exactly as specified**.

Do not expand scope.
Do not add features.
Do not "improve" degraded maneuvers.

**Minimal. Deterministic. Gate-safe.**

If unsure → stop and ask.

---

**Packet Version:** 1.0
**Created:** 2026-02-08
**Authority:** Implementation-Binding
