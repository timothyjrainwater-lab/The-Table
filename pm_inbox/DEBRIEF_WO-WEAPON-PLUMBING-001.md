# DEBRIEF: WO-WEAPON-PLUMBING-001 — Weapon Data Pipeline

**From:** Builder (Opus 4.6)
**To:** PM (Aegis), via PO (Thunder)
**Date:** 2026-02-14
**Lifecycle:** NEW
**WO:** WO-WEAPON-PLUMBING-001
**Result:** COMPLETED — all 3 target activations delivered, 34 new tests, zero regressions

---

## Pass 1 — Full Context Dump

### What Was Done

Plumbed `weapon_type` and `range_increment` from entity schema through the intent bridge into all combat resolvers. This activated three dormant fixes: `is_ranged` detection in attack resolvers, B-AMB-04 disarm weapon type modifiers, and sunder grip multiplier.

### Files Modified

1. **`aidm/schemas/attack.py`** — Added `weapon_type: str = "one-handed"` and `range_increment: int = 0` fields to `Weapon` dataclass. Added `__post_init__` validation for both fields. Added `@property is_ranged` (weapon_type == "ranged") and `@property is_light` (weapon_type == "light").

2. **`aidm/interaction/intent_bridge.py`** — Updated `_resolve_weapon()` to handle dict `EF.WEAPON` via `isinstance(entity_weapon, dict)` check before the `.lower()` string path. Added `_build_weapon_from_dict()` method extracting all fields with safe defaults. Set unarmed strike to `weapon_type="natural"`.

3. **`aidm/core/attack_resolver.py`** — Added `get_entity_position` import. Computed `range_ft` from entity positions. Replaced `max_range=100` with `range_increment * 10` for ranged / `100` for melee (preserving legacy behavior). Replaced hardcoded `is_ranged: False` with `intent.weapon.is_ranged` in feat_context. Updated `check_cover` `is_melee` parameter.

4. **`aidm/core/full_attack_resolver.py`** — Same 4 changes as attack_resolver (parallel consumer).

5. **`aidm/core/maneuver_resolver.py`** — Added `_get_weapon_type()` and `_get_weapon_grip()` helpers. Replaced 16-line B-AMB-04 TODO block in disarm with active code (+4 two-handed, -4 light for both attacker and defender). Replaced `damage_bonus = attacker_str` in sunder with grip-aware multiplier (1.5x two-handed, 0.5x off-hand, 1x default).

6. **`aidm/core/aoo.py`** — Updated Weapon constructor from dict data to include `weapon_type` and `range_increment` fields.

### Files Created

1. **`tests/test_weapon_plumbing.py`** — 34 tests across 8 test classes:
   - `TestWeaponDataclass` (9): defaults, is_ranged/is_light derivation, validation
   - `TestRangedDetection` (2): melee/ranged resolve correctly
   - `TestMaxRange` (4): out-of-range, within-range, melee adjacent, legacy no-position
   - `TestDisarmWeaponModifiers` (6): helper tests + statistical win-rate tests
   - `TestSunderGripMultiplier` (5): helper tests + damage_bonus verification
   - `TestIntentBridgeDict` (4): dict weapon flows through intent bridge
   - `TestBackwardCompat` (3): string weapon defaults, unarmed, existing resolution
   - `TestCanaryStillPasses` (1): B-AMB-04 source references active

### Files NOT Changed (per WO constraints)

- `state.py`, `replay_runner.py` — frozen contracts
- All Lens/presentation files — out of scope
- `entity_fields.py` — no new EF constants needed

### Test Results

- **34 new tests passed** (test_weapon_plumbing.py)
- **5,775 total tests passed**, 15 skipped (hardware-gated)
- **Zero regressions** — all existing tests pass without modification
- 14 pre-existing failures unrelated to this WO (TorchAudio environment, import boundary, PM inbox hygiene)

### Key Design Decision: Melee max_range

Initial implementation used `max(5, range_ft)` for melee weapons, which made melee range checks always pass (max_range >= distance is tautological). This broke 43 replay determinism tests. Fixed by keeping legacy `max_range=100` for melee, matching the old hardcoded behavior exactly. Range increment * 10 is only used for `is_ranged` weapons.

---

## Pass 2 — PM Summary

**WO-WEAPON-PLUMBING-001: COMPLETED.** `weapon_type` and `range_increment` plumbed from entity dict through `IntentBridge._build_weapon_from_dict()` to `Weapon` dataclass. Three dormant fixes activated: (1) `is_ranged` detection in attack_resolver.py and full_attack_resolver.py, (2) B-AMB-04 disarm weapon type modifiers in maneuver_resolver.py, (3) sunder grip multiplier in maneuver_resolver.py. 34 new tests, zero regressions. PSD updated and synced.

---

## Retrospective (Pass 3 — Operational Judgment)

### Dual Weapon Pattern

The `EF.WEAPON` field stores EITHER a string name or a dict. The intent bridge now handles both via `isinstance` dispatch. This duality is tech debt — a future WO should normalize all entities to dict-format weapons. Until then, string weapons silently get `weapon_type="one-handed"` defaults, which is correct per the WO spec.

### max_range Regression

The most significant risk was the melee `max_range` formula. `max(5, range_ft)` seemed mathematically correct but violated the WO constraint "existing tests must pass without modification." The fix (keep `max_range=100` for melee) preserves legacy behavior but means melee attacks can target entities up to 100ft away — which is mechanically wrong but matches the pre-existing behavior. Proper melee reach enforcement should be a separate WO.

### Process Feedback

The WO was well-structured. Binary decisions were pre-made, line references were accurate, and the "Do NOT implement range increment penalties / shooting into melee / RangedAttackIntent" constraints prevented scope creep effectively. The `_get_weapon_type()` / `_get_weapon_grip()` helpers follow the existing `_get_entity_field()` pattern in maneuver_resolver.py, keeping the code consistent.

### Concerns

- The `_build_weapon_from_dict()` method in intent_bridge and the Weapon constructor call in aoo.py both extract the same fields with the same defaults. If the Weapon dataclass gains more fields, both sites need updating. Consider a future `Weapon.from_dict(data)` classmethod to centralize construction.
- Disarm and sunder now actively use weapon_type/grip data, but existing entity fixtures don't populate these fields — they silently get defaults. This is correct per the WO but means the new modifiers won't fire in playtests until entities have explicit weapon dicts with `weapon_type` set.
