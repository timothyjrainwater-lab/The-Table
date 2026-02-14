# WO-WEAPON-PLUMBING-001: Weapon Data Pipeline

**From:** PM (Aegis)
**To:** Builder (via Operator dispatch)
**Date:** 2026-02-14
**Lifecycle:** DISPATCH-READY
**Horizon:** 1
**Priority:** P1 — Highest-impact H1 item. Activates 3 dormant fixes and unblocks ranged combat.
**Source:** Post-fix action plan P4-D, B-AMB-04 (disarm mods), WO-FIX-01 gap (sunder grip), RQ-SPRINT-011

---

## Target Lock

Plumb weapon type data from entity schema through to combat resolvers. Three dormant fixes activate when this lands:

1. **is_ranged detection** — currently hardcoded `False` in attack_resolver.py:227 and full_attack_resolver.py:474. Prone/Helpless AC differentiation (WO-FIX-03) is correct but dormant for ranged attacks.
2. **Disarm weapon type modifiers** — B-AMB-04 decided FIX-SRD. TODO in maneuver_resolver.py:1218-1240. Two-handed +4, light -4.
3. **Sunder grip multiplier** — WO-FIX-01 applied to attack resolvers but missed sunder path in maneuver_resolver.py:1071. Two-handed sunder should deal `int(STR * 1.5)`.

## Binary Decisions

1. **Where does weapon type live?** Add `weapon_type` field to entity weapon data. Values: `"light"`, `"one-handed"`, `"two-handed"`, `"ranged"`, `"natural"`. This is the minimum viable set.
2. **How does ranged detection work?** `is_ranged = weapon_type == "ranged"`. No separate field — derive from weapon_type.
3. **What about max_range?** Add `range_increment` to weapon data. Currently hardcoded `max_range=100`. Replace with `range_increment * 10` (max range = 10 increments per SRD). If no range_increment, weapon is melee.
4. **Does this change WorldState?** Yes — weapon data is entity state. But weapon_type is additive (new field with default), so existing state loads unchanged.
5. **Does this change state_hash?** Only if weapon_type is stored in entity state. Use a default value (`"one-handed"`) so existing entities don't change hash unless explicitly given a weapon_type.

## Contract Spec

### Change 1: Entity Weapon Schema

Add weapon type and range fields to weapon data in entity schema:
- `weapon_type: str = "one-handed"` — default preserves existing behavior
- `range_increment: int = 0` — 0 = melee weapon, >0 = ranged (increment in feet)
- `is_light: bool` — derived property: `weapon_type == "light"`
- `is_two_handed: bool` — derived property: `weapon_type == "two-handed"`
- `is_ranged: bool` — derived property: `weapon_type == "ranged"`

### Change 2: Resolver is_ranged Detection

In `attack_resolver.py` and `full_attack_resolver.py`:
- Replace `"is_ranged": False` with actual detection from weapon data
- Replace `max_range=100` with `range_increment * 10` (or fallback to melee range 5)

### Change 3: Disarm Weapon Type Modifiers

In `maneuver_resolver.py` (disarm path, ~line 1220):
- Activate the existing TODO code
- Two-handed weapon: +4 to opposed check
- Light weapon: -4 to opposed check
- Apply to both attacker and defender

### Change 4: Sunder Grip Multiplier

In `maneuver_resolver.py` (sunder damage path, ~line 1071):
- Apply same grip logic as attack_resolver.py:370-378
- Two-handed: `int(STR * 1.5)`
- Off-hand: `int(STR * 0.5)`
- One-handed: `STR`

### Constraints

- Default weapon_type must be `"one-handed"` — existing entities without explicit weapon data behave as before
- Do NOT implement range increment penalties (-2 per increment) — that's a separate WO
- Do NOT implement shooting into melee (-4 penalty) — separate WO
- Do NOT implement RangedAttackIntent — just detect is_ranged from weapon data
- Existing tests must pass without modification (defaults preserve behavior)

### Boundary Laws Affected

- BL-011 (deterministic hashing): weapon_type default ensures hash stability for existing entities
- BL-012 (reduce_event): NOT AFFECTED — resolvers emit events, not reducer

## Success Criteria

- [ ] `is_ranged` correctly detected from weapon data in both attack resolvers
- [ ] Prone AC differentiation applies correct modifier based on is_ranged
- [ ] Helpless AC differentiation applies correct modifier based on is_ranged
- [ ] Disarm opposed check includes +4 two-handed / -4 light modifiers
- [ ] Sunder damage uses grip-adjusted STR (1.5x for two-handed)
- [ ] Existing tests pass without modification
- [ ] New tests cover: ranged detection, disarm weapon mods, sunder grip
- [ ] `state_hash()` unchanged for entities without explicit weapon_type

## Files Expected to Change

- Entity weapon schema (wherever EF.WEAPON is defined/consumed)
- `aidm/core/attack_resolver.py` — is_ranged, max_range
- `aidm/core/full_attack_resolver.py` — is_ranged, max_range
- `aidm/core/maneuver_resolver.py` — disarm mods, sunder grip
- Test files for new behavior

## Files NOT to Change

- `aidm/core/state.py` — WorldState structure unchanged
- `aidm/core/replay_runner.py` — replay logic untouched
- Any Lens or presentation layer files

---

*End of WO-WEAPON-PLUMBING-001*
