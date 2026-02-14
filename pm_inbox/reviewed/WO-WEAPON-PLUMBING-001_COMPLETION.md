# WO-WEAPON-PLUMBING-001 Completion Report: Weapon Data Pipeline

**From:** Builder (Opus 4.6)
**To:** PM (Aegis)
**Date:** 2026-02-14
**Lifecycle:** NEW
**Status:** COMPLETE — all 4 contract changes landed, 34 new tests pass, 0 regressions.

---

## Summary

Plumbed weapon type data from entity schema through combat resolvers. Three dormant fixes now active:
1. **is_ranged detection** — live in both attack resolvers
2. **Disarm weapon type modifiers** — +4 two-handed / -4 light applied to opposed checks
3. **Sunder grip multiplier** — two-handed deals `int(STR * 1.5)`, off-hand `int(STR * 0.5)`

## Change 1: Entity Weapon Schema

**Status:** Pre-existing — no new work required.

`Weapon` dataclass in `aidm/schemas/attack.py` already had:
- `weapon_type: str = "one-handed"` (lines 47-51) with validation for `{light, one-handed, two-handed, ranged, natural}`
- `range_increment: int = 0` (lines 53-56) with non-negative validation
- `is_ranged` property (line 96-99): `weapon_type == "ranged"`
- `is_light` property (lines 101-104): `weapon_type == "light"`

Default `"one-handed"` preserves existing entity behavior. Hash stability confirmed via gold master replay.

## Change 2: Resolver is_ranged Detection

**Files:** `aidm/core/attack_resolver.py`, `aidm/core/full_attack_resolver.py`

| Before | After |
|--------|-------|
| `is_ranged: False` (hardcoded) | `intent.weapon.is_ranged` (derived from weapon_type) |
| `range_ft: 5` (hardcoded) | `attacker_pos.distance_to(target_pos)` (actual distance) |
| `max_range=100` (hardcoded) | `range_increment * 10` for ranged; `100` for melee (legacy cap) |
| `is_melee=True` (hardcoded in cover check) | `not intent.weapon.is_ranged` |

Prone/Helpless AC differentiation (`ac_modifier_melee` vs `ac_modifier_ranged`) now activates correctly for ranged attacks via the `is_melee` derivation chain.

## Change 3: Disarm Weapon Type Modifiers

**File:** `aidm/core/maneuver_resolver.py` (lines 1250-1263)

- Added `_get_weapon_type(world_state, entity_id)` helper (lines 98-107)
- Replaced 16-line TODO block with live code
- Two-handed weapon: `attacker_modifier += 4` / `defender_modifier += 4`
- Light weapon: `attacker_modifier -= 4` / `defender_modifier -= 4`
- Applied to both attacker and defender independently

## Change 4: Sunder Grip Multiplier

**File:** `aidm/core/maneuver_resolver.py` (lines 1094-1101)

- Added `_get_weapon_grip(world_state, entity_id)` helper (lines 110-118)
- Sunder damage bonus now grip-adjusted:
  - Two-handed: `int(attacker_str * 1.5)`
  - Off-hand: `int(attacker_str * 0.5)`
  - One-handed (default): `attacker_str`

Same logic as `attack_resolver.py:370-378`.

## Test Results

**New tests:** 34 passed in `tests/test_weapon_plumbing.py`

| Suite | Tests | Description |
|-------|-------|-------------|
| TestWeaponDataclass | 9 | weapon_type, range_increment, is_ranged, is_light, validation |
| TestRangedDetection | 2 | Melee and ranged weapons resolve through attack resolver |
| TestMaxRange | 4 | Out-of-range fails, within-range succeeds, melee adjacent, legacy no-position |
| TestDisarmWeaponModifiers | 6 | Helper tests, +4/-4 modifiers, statistical win-rate validation |
| TestSunderGripMultiplier | 5 | Helper tests, 1.5x/0.5x/1x STR damage verification |
| TestIntentBridgeDict | 4 | Dict EF.WEAPON flows weapon_type, grip, range_increment through IntentBridge |
| TestBackwardCompat | 3 | String weapon defaults, unarmed natural, existing resolution unchanged |
| TestCanaryStillPasses | 1 | B-AMB-04 references + _get_weapon_type present in source |

**Existing tests:** 229 combat-related tests passed (attack, full attack, maneuvers, replay, determinism). Zero regressions.

**Gold master replay:** PASS — dungeon_100turn.jsonl replays identically. `state_hash` unchanged.

## Constraint Compliance

- [x] Default weapon_type = `"one-handed"` — existing entities behave as before
- [x] No range increment penalties implemented (separate WO)
- [x] No shooting into melee penalty implemented (separate WO)
- [x] No RangedAttackIntent implemented — is_ranged derived from weapon data
- [x] Existing tests pass without modification
- [x] BL-011 (deterministic hashing): hash stability confirmed via gold master
- [x] BL-012 (reduce_event): NOT AFFECTED — resolvers emit events, not reducer

## Success Criteria Checklist

- [x] `is_ranged` correctly detected from weapon data in both attack resolvers
- [x] Prone AC differentiation applies correct modifier based on is_ranged
- [x] Helpless AC differentiation applies correct modifier based on is_ranged
- [x] Disarm opposed check includes +4 two-handed / -4 light modifiers
- [x] Sunder damage uses grip-adjusted STR (1.5x for two-handed)
- [x] Existing tests pass without modification
- [x] New tests cover: ranged detection, disarm weapon mods, sunder grip
- [x] `state_hash()` unchanged for entities without explicit weapon_type

## Files Changed

| File | Change |
|------|--------|
| `aidm/core/attack_resolver.py` | is_ranged, range_ft, max_range, is_melee cover check |
| `aidm/core/full_attack_resolver.py` | Same pipeline as attack_resolver |
| `aidm/core/maneuver_resolver.py` | _get_weapon_type, _get_weapon_grip helpers; disarm mods; sunder grip |
| `tests/test_weapon_plumbing.py` | 34 new tests |

## Files NOT Changed (per WO constraint)

- `aidm/core/state.py` — WorldState structure unchanged
- `aidm/core/replay_runner.py` — replay logic untouched
- `aidm/schemas/attack.py` — schema already had weapon_type/range_increment (pre-existing)
- Any Lens or presentation layer files

---

*End of WO-WEAPON-PLUMBING-001 Completion Report*
