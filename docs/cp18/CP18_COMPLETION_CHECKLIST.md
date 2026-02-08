# CP-18 Completion Checklist (Audit-Grade)
**Date:** 2026-02-08
**Authority:** CP18_IMPLEMENTATION_PACKET.md (binding)

---

## 1) File touch map compliance

### Files to CREATE
- [x] `aidm/schemas/maneuvers.py`
- [x] `aidm/core/maneuver_resolver.py`
- [x] `tests/test_maneuvers_core.py`
- [x] `tests/test_maneuvers_integration.py`

### Files to MODIFY
- [x] `aidm/schemas/entity_fields.py` (add: SIZE_CATEGORY, STABILITY_BONUS, GRAPPLE_SIZE_MODIFIER)
- [x] `aidm/core/play_loop.py` (route maneuver intents)
- [x] `aidm/core/aoo.py` (AoO triggers recognize maneuver intents)

### Files NOT to touch
- [x] `aidm/core/attack_resolver.py` unchanged
- [x] `aidm/core/full_attack_resolver.py` unchanged
- [x] `aidm/core/conditions.py` unchanged
- [x] `aidm/schemas/conditions.py` unchanged
- [x] `aidm/core/mounted_combat.py` unchanged

---

## 2) Functional requirements

- [x] Bull Rush moves target on success
- [x] Bull Rush pushes attacker back on failure
- [x] Trip applies Prone on success
- [x] Trip enables counter-trip on failure
- [x] Overrun applies Prone on success
- [x] Overrun defender can avoid (AI-controlled boolean)
- [x] Sunder emits damage event only (no persistent state)
- [x] Disarm emits weapon drop event only (no persistent state)
- [x] Grapple applies Grappled to defender only
- [x] All maneuvers provoke AoOs correctly
- [x] AoO damage causes Disarm/Grapple auto-failure
- [x] Size modifiers applied correctly (±4 per category)
- [x] Grapple uses special size scale (-16 to +16)
- [x] Stability bonus (+4) applied for dwarves/quadrupeds
- [x] Charge bonus (+2) applied for Bull Rush/Overrun

---

## 3) Test requirements

### Global
- [x] All existing tests pass (626 baseline)
- [x] Full suite runtime < 2 seconds (1.83s)

### New tests (minimums)
- [x] ≥ 9 Tier-1 tests (36 tests)
- [x] ≥ 3 Tier-2 tests (17 tests)
- [x] 1 PBHA determinism test (10× replay) (3 tests)

---

## 4) Determinism requirements

- [x] 10× replay produces identical state hashes
- [x] RNG consumption order matches packet per maneuver
- [x] Event ordering matches design contract
- [x] AoO ordering uses CP-15 ordering (initiative → lexicographic)
- [x] Opposed checks: attacker roll then defender roll (always)

---

## 5) Gate safety requirements

- [x] Grapple is unidirectional (defender-only condition; no attacker state)
- [x] Sunder: no persistent item state change
- [x] Disarm: no persistent item state change
- [x] No new entity fields beyond allowed three

---

## 6) Documentation requirements

- [x] `PROJECT_STATE_DIGEST.md` updated with CP-18 entry
- [x] Test count updated (626 → 679)
- [x] Module inventory updated

---

**STATUS: ✅ COMPLETE** (2026-02-08)
