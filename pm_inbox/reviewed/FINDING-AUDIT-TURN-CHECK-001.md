# FINDING-AUDIT-TURN-CHECK-001 — Turn Undead Check Uses 2d6 Instead of 1d20

**ID:** FINDING-AUDIT-TURN-CHECK-001
**Severity:** HIGH
**Status:** OPEN
**Found by:** AUDIT-WO-004 (2026-02-27)
**Lifecycle:** NEW

---

## Description

The Turn Undead check roll uses 2d6 instead of 1d20 as specified in PHB p.159.

## PHB Specification (p.159–160)

**Step 1 — Turn Check:**
> "Roll 1d20 and add your Charisma modifier. The result is compared to Table 8-1 to determine the maximum Hit Dice of undead you can affect."

**Step 2 — Turning Damage (how many HD total are turned):**
> "Roll 2d6 and add your cleric level and Charisma modifier. The result is how many total Hit Dice of undead you can turn."

Two separate rolls. Turn check = 1d20+CHA. Damage = 2d6+level+CHA.

## Evidence

**Code (`turn_undead_resolver.py` lines 62-67):**
```python
def _roll_turning_check(cleric_level: int, cha_mod: int, rng: RNGProvider) -> int:
    """Roll 2d6 + cleric_level + CHA_mod (PHB p.160)."""
    d1 = combat_rng.randint(1, 6)
    d2 = combat_rng.randint(1, 6)
    return d1 + d2 + cleric_level + cha_mod, d1, d2
```

The classification check uses `d1 + d2 + cleric_level + cha_mod` (2d6+level+CHA). PHB requires 1d20+CHA only for the check; the `cleric_level` term does not belong in the check roll.

**HP budget (lines 72-77):**
```python
def _roll_hp_budget(rng: RNGProvider) -> Tuple[int, int, int]:
    """Roll (2d6) × 10 HP budget (PHB p.160)."""
    return (d1 + d2) * 10, d1, d2
```
HP budget roll is separately correct.

## Impact

- Max die range: 2d6 max=12 vs 1d20 max=20. The turn check is systematically compressed.
- Adding `cleric_level` to the check roll (not just CHA) gives clerics extra turning power beyond RAW.
- All turning classification comparisons via Table 8-1 are based on wrong input.

## Fix

In `turn_undead_resolver.py`, replace `_roll_turning_check` with:
```python
def _roll_turning_check(cha_mod: int, rng: RNGProvider) -> int:
    """Roll 1d20 + CHA_mod (PHB p.159). No cleric_level term."""
    d20 = rng.stream("combat").randint(1, 20)
    return d20 + cha_mod, d20
```
Remove `cleric_level` parameter from this function. It belongs only in the damage roll.

## Corrective WO

Requires corrective WO. All turn undead gate tests will need recalibration (RNG seeds and expected outcomes will shift).
