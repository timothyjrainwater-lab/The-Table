# Bone-Layer Fix WO Dispatch Packet

**Authority:** PM (Opus 4.6)
**Date:** 2026-02-14
**Status:** READY for dispatch — no dependencies between WOs unless noted
**Lifecycle:** NEW
**Total:** 12 active fix WOs (FIX-WO-05 retired). 30 bugs across 15 files.
**Dispatch model:** All WOs are independent unless marked with DEPENDS-ON. Parallel dispatch is safe for independent WOs.

---

## Universal Builder Instructions

Every fix WO follows this protocol:

1. Read the verification record cited (DOMAIN_X_VERIFICATION.md, formula ID) to understand the exact bug.
2. Read the source file at the cited line numbers.
3. Make the fix described. Do NOT refactor surrounding code. Do NOT add features. Surgical fix only.
4. Run `python -m pytest tests/ -x -q` after each fix. All 5,510+ tests must pass.
5. If any existing test fails, determine whether the test was testing the WRONG behavior (update test) or if your fix introduced a regression (fix the fix).
6. Add new test(s) for the fixed behavior where specified.
7. Commit with message format: `fix: [BUG-ID] — [one-line description]`
8. Do NOT touch any file not listed in the WO.

**Research cross-reference requirement:** Before fixing, check if the bug might be a documented design decision by searching these files for the relevant mechanic keyword:
- `docs/research/findings/PF_DELTA_INDEX.md`
- `docs/research/findings/RQ-BOX-002-F_FAQ_MINING_RESULTS.md`
- `docs/research/findings/SKIP_WILLIAMS_DESIGNER_INTENT.md`
If the research documents show the current behavior is intentional, STOP and report back instead of fixing.

---

## WO-FIX-01: Attack Damage Pipeline

**Priority:** 1 (highest — most frequently executed code path)
**Severity:** HIGH
**Bugs:** BUG-1, BUG-8, BUG-9
**Files to modify:** `aidm/core/attack_resolver.py`, `aidm/core/full_attack_resolver.py`
**Verification refs:** `docs/verification/DOMAIN_A_VERIFICATION.md` — formulas A-attack-resolver-363, A-attack-resolver-369, A-attack-resolver-371

### BUG-1: Two-handed STR multiplier not applied

**Locations:** attack_resolver.py:363, full_attack_resolver.py:297-299
**SRD rule:** PHB p.141 — "Two-handed: Add 1-1/2 times your Strength bonus. Off-hand: Add 1/2 your Strength bonus."
**Current code:** `base_damage = dice_total + weapon_bonus + str_modifier` (flat STR for all grips)
**Fix:**
```python
# Determine STR multiplier based on weapon grip
if weapon_grip == "two-handed":
    str_to_damage = int(str_modifier * 1.5)
elif weapon_grip == "off-hand":
    str_to_damage = int(str_modifier * 0.5)
else:
    str_to_damage = str_modifier

base_damage = dice_total + weapon_bonus + str_to_damage
```
**Implementation notes:**
- `int()` truncates toward zero, matching SRD "round down" for positive values.
- Negative STR modifier: SRD says apply full negative STR to damage even for off-hand. The `int(negative * 0.5)` truncation handles this correctly (e.g., -3 * 0.5 = -1.5 → -1, which is correct — less penalty for off-hand).
- The `weapon_grip` field must already exist on the attack intent or weapon schema. Search for how the weapon's grip type is currently tracked. If not tracked, add a `grip` field to the weapon/intent schema with values `"one-handed"`, `"two-handed"`, `"off-hand"`, defaulting to `"one-handed"`.
- Apply the same fix in BOTH files (attack_resolver.py AND full_attack_resolver.py).

### BUG-8 / BUG-9: Minimum damage on hit should be 1, not 0

**Locations (4 total):**
- attack_resolver.py:369 (critical path)
- attack_resolver.py:371 (non-critical path)
- full_attack_resolver.py:303 (critical path)
- full_attack_resolver.py:305 (non-critical path)

**SRD rule:** PHB p.141 — "If penalties reduce the damage result to less than 1, a hit still deals 1 point of damage."
**Current code:** `max(0, modified_damage * crit_multiplier)` and `max(0, modified_damage)`
**Fix:** Change `max(0, ...)` to `max(1, ...)` at all 4 locations.
**Important:** This minimum-1 applies BEFORE damage reduction (DR). After DR, damage CAN be reduced to 0.

### Tests to add:
1. Two-handed weapon deals `int(STR * 1.5)` damage
2. Off-hand weapon deals `int(STR * 0.5)` damage
3. One-handed weapon deals flat STR damage
4. Negative STR modifier: two-handed = full penalty, off-hand = half penalty
5. Attack with penalties reducing base damage below 1 still deals 1 damage
6. Critical hit with penalties still deals minimum 1 * multiplier
7. After DR, damage CAN be 0

**Commit:** `fix: BUG-1/8/9 — STR multiplier by grip + minimum 1 damage on hit`

---

## WO-FIX-02: Full Attack Loop Early Termination

**Priority:** 2
**Severity:** MEDIUM
**Bugs:** BUG-2
**Files to modify:** `aidm/core/full_attack_resolver.py`
**Verification ref:** `docs/verification/DOMAIN_A_VERIFICATION.md` — formula A-full-attack-595

### BUG-2: Full attack loop doesn't break on target defeat

**Location:** full_attack_resolver.py:546-590
**SRD rule:** PHB p.143 — Attacks in a full attack are resolved sequentially. A dead target cannot be attacked further (unless the attacker can redirect to another adjacent target, which is not implemented).
**Current code:** Loop iterates through all attacks, accumulates damage, checks defeat once at end.
**Fix:**
```python
for attack in iterative_attacks:
    # ... resolve single attack ...
    # Apply damage immediately after each attack
    current_hp -= this_attack_damage
    if current_hp <= 0:
        # Target defeated — stop attacking
        break
```
**Implementation notes:**
- HP must be tracked per-attack, not accumulated and applied at end.
- The defeat check should use the same threshold as the single-attack resolver (hp <= 0).
- Remaining attacks after defeat are simply not executed. No redirect logic needed.
- The total damage reported should be the sum of damage actually dealt, not the theoretical maximum.

### Tests to add:
1. Full attack against 5 HP target: first hit deals 10 damage, second attack should NOT execute
2. Full attack where first hit doesn't kill: all attacks execute normally
3. Total damage reported matches actual damage dealt (not excess)

**Commit:** `fix: BUG-2 — full attack breaks on target defeat`

---

## WO-FIX-03: Condition AC Melee/Ranged Differentiation

**Priority:** 3 (schema change — upstream of attack resolvers)
**Severity:** HIGH
**Bugs:** BUG-3, BUG-4
**Files to modify:** `aidm/schemas/conditions.py`, `aidm/core/attack_resolver.py`, `aidm/core/full_attack_resolver.py`
**Verification ref:** `docs/verification/DOMAIN_D_VERIFICATION.md` — formulas D-conditions-schema-208, D-conditions-schema-281
**DEPENDS-ON:** Should be applied BEFORE WO-FIX-01 (attack resolvers consume condition modifiers)

### BUG-3: Prone AC not melee/ranged differentiated

**Location:** conditions.py:208 (Prone condition definition)
**SRD rule:** PHB p.311 — Prone: "-4 penalty to AC against melee attacks, +4 bonus to AC against ranged attacks"
**Current code:** `ac_modifier=-4` (flat, applied to all attacks)
**Fix:** Replace single `ac_modifier` with two fields:
```python
ac_modifier_melee=-4,
ac_modifier_ranged=4,
```

### BUG-4: Helpless AC not melee/ranged differentiated

**Location:** conditions.py:281 (Helpless condition definition)
**SRD rule:** PHB p.310 — Helpless: effective Dex of 0 (–5 mod). Melee attackers get +4 to hit (equivalent to -4 AC). Ranged attackers get no special bonus.
**Current code:** `ac_modifier=-4` (flat, applied to all attacks)
**Fix:**
```python
ac_modifier_melee=-4,
ac_modifier_ranged=0,
```

### Schema change required:

The `ConditionModifiers` dataclass/schema needs two new fields:
```python
ac_modifier_melee: int = 0
ac_modifier_ranged: int = 0
```
The existing `ac_modifier` field should be kept for conditions that don't differentiate (e.g., Stunned = -2 to all). The attack resolvers must check:
1. If `ac_modifier_melee` or `ac_modifier_ranged` is set (non-zero), use the attack-type-specific value.
2. Otherwise, fall back to `ac_modifier`.

### Consumer updates:

In attack_resolver.py (~line 243) and full_attack_resolver.py (~line 499), where `condition_ac` is consumed:
```python
# Before (flat):
condition_ac = defender_modifiers.ac_modifier

# After (differentiated):
if is_melee_attack:
    condition_ac = defender_modifiers.ac_modifier_melee or defender_modifiers.ac_modifier
else:
    condition_ac = defender_modifiers.ac_modifier_ranged or defender_modifiers.ac_modifier
```

### Cascading conditions:

These conditions inherit Helpless behavior and will be automatically correct once BUG-4 is fixed:
- **Paralyzed** (conditions.py:504) — currently `ac_modifier=-4`, should cascade from Helpless
- **Unconscious** (conditions.py:541) — currently `ac_modifier=-4`, should cascade from Helpless

Update these to use the same `ac_modifier_melee=-4, ac_modifier_ranged=0` pattern.

### Tests to add:
1. Melee attack vs Prone target: AC reduced by 4
2. Ranged attack vs Prone target: AC increased by 4
3. Melee attack vs Helpless target: AC reduced by 4
4. Ranged attack vs Helpless target: no AC change
5. Paralyzed and Unconscious: same behavior as Helpless
6. Stunned (non-differentiated): AC modifier applies to both melee and ranged

**Commit:** `fix: BUG-3/4 — Prone and Helpless AC now melee/ranged differentiated`

---

## WO-FIX-04: Condition Modifier Gaps

**Priority:** 4
**Severity:** MEDIUM
**Bugs:** BUG-5, BUG-6, BUG-7
**Files to modify:** `aidm/schemas/conditions.py`
**Verification ref:** `docs/verification/DOMAIN_D_VERIFICATION.md`

### BUG-5: Panicked incorrectly loses Dex to AC

**Location:** conditions.py:431
**SRD rule:** PHB p.311 — Panicked: flee, -2 to all rolls. Does NOT include losing Dex to AC.
**Fix:** Remove `loses_dex_to_ac=True` from Panicked condition.

### BUG-6: Fatigued missing damage modifier

**Location:** conditions.py:467
**SRD rule:** PHB p.308 — Fatigued: -2 STR penalty → -1 to melee damage.
**Fix:** Add `damage_modifier=-1` to Fatigued condition.

### BUG-7: Exhausted missing damage modifier

**Location:** conditions.py:485
**SRD rule:** PHB p.308 — Exhausted: -6 STR penalty → -3 to melee damage.
**Fix:** Add `damage_modifier=-3` to Exhausted condition.

### Tests to add:
1. Panicked creature retains Dex bonus to AC
2. Fatigued creature deals 1 less melee damage
3. Exhausted creature deals 3 less melee damage
4. Fatigued/Exhausted damage penalty does NOT apply to ranged (unless thrown/composite bow — out of scope, document as limitation)

**Commit:** `fix: BUG-5/6/7 — Panicked Dex-to-AC, Fatigued/Exhausted damage modifiers`

---

## WO-FIX-06: Concentration DC Formula

**Priority:** 5
**Severity:** HIGH
**Bugs:** BUG-C-002
**Files to modify:** `aidm/core/spell_resolver.py`, `aidm/core/play_loop.py`
**Verification ref:** `docs/verification/DOMAIN_C_VERIFICATION.md` — formula C-SPELL-1035

### BUG-C-002: Concentration DC missing spell level

**Locations:** spell_resolver.py:1035, play_loop.py:618
**SRD rule:** PHB p.69 — "DC = 10 + damage taken + spell level"
**Current code:** `dc = 10 + damage_taken` (missing `+ spell_level`)
**Fix:**
```python
# Before:
dc = 10 + damage_taken

# After:
dc = 10 + damage_taken + spell_level
```
**Implementation notes:**
- `spell_level` must be available in the concentration check context. Search the function signature for how it's currently called — if spell_level isn't passed in, add it as a parameter.
- Fix in BOTH locations (spell_resolver.py AND play_loop.py).

### Tests to add:
1. Concentration DC for 3rd-level spell with 5 damage = 18 (not 15)
2. Concentration DC for 0-level cantrip with 5 damage = 15 (same as before, since +0)
3. Concentration DC for 9th-level spell with 1 damage = 20

**Commit:** `fix: BUG-C-002 — concentration DC includes spell level`

---

## WO-FIX-07: Combat Maneuver Size Modifiers

**Priority:** 6
**Severity:** MEDIUM
**Bugs:** B-BUG-1, B-BUG-3, B-BUG-5
**Files to modify:** `aidm/core/maneuver_resolver.py`
**Verification ref:** `docs/verification/DOMAIN_B_VERIFICATION.md`

### Root cause: Touch/attack rolls use special size modifier instead of standard

D&D 3.5e has TWO size modifier tables:
- **Standard attack size modifier:** Fine +8, Diminutive +4, Tiny +2, Small +1, Medium +0, Large -1, Huge -2, Gargantuan -4, Colossal -8
- **Special size modifier (grapple/bull rush/trip/overrun):** Fine -16, Diminutive -12, Tiny -8, Small -4, Medium +0, Large +4, Huge +8, Gargantuan +12, Colossal +16

The initial TOUCH ATTACK to initiate a maneuver uses the standard attack size modifier. Only the OPPOSED CHECK after contact uses the special size modifier.

### B-BUG-1: Trip touch attack

**Location:** maneuver_resolver.py:501
**Fix:** Replace special size modifier with standard attack size modifier for the trip touch attack roll.

### B-BUG-3: Sunder attack rolls

**Locations:** maneuver_resolver.py:1004, 1009
**Fix:** Replace special size modifier with standard attack size modifier for sunder attack rolls.

### B-BUG-5: Grapple touch attack

**Location:** maneuver_resolver.py:1382
**Fix:** Replace special size modifier with standard attack size modifier for the grapple touch attack roll.

### Implementation:
Locate the size modifier lookup for each of these attack rolls. It's currently using the special/grapple size modifier table. Change it to use the standard attack size modifier table. The opposed STR check that follows should KEEP the special size modifier — only the initial touch/attack roll changes.

### Tests to add:
1. Large creature trip touch attack: size modifier = -1 (not +4)
2. Small creature grapple touch attack: size modifier = +1 (not -4)
3. Opposed trip check after touch attack: STILL uses special size modifier (+4 for Large)

**Commit:** `fix: B-BUG-1/3/5 — maneuver touch attacks use standard size modifier`

---

## WO-FIX-08: Overrun Failure Mechanic

**Priority:** 7
**Severity:** HIGH
**Bugs:** B-BUG-2
**Files to modify:** `aidm/core/maneuver_resolver.py`
**Verification ref:** `docs/verification/DOMAIN_B_VERIFICATION.md` — formula B-MR-859

### B-BUG-2: Overrun failure uses flat threshold instead of opposed check

**Location:** maneuver_resolver.py:859
**SRD rule:** PHB p.157 — "If you fail to overrun your opponent, the defender may immediately react and make a Strength check opposed by your Strength check to try to knock you prone."
**Current code:** Uses `margin <= -5` as a flat threshold to determine if the overrunner falls prone.
**Fix:** Replace with a proper opposed Strength check:
```python
# On overrun failure:
defender_str_check = d20 + defender_str_mod + defender_special_size_mod
attacker_str_check = d20 + attacker_str_mod + attacker_special_size_mod
if defender_str_check >= attacker_str_check:
    # Attacker is knocked prone
    attacker_prone = True
```
**Implementation notes:**
- This is a separate roll from the initial overrun check. Both sides roll new d20s.
- The opposed check uses the SPECIAL size modifier (same as grapple/bull rush), not standard attack size.
- Defender wins ties (SRD opposed check default).

### Tests to add:
1. Failed overrun: defender succeeds opposed STR check → attacker prone
2. Failed overrun: defender fails opposed STR check → attacker stops but not prone
3. Size difference affects the opposed check via special size modifier

**Commit:** `fix: B-BUG-2 — overrun failure uses opposed STR check for prone`

---

## WO-FIX-09: Sunder Damage Placeholder

**Priority:** 8 (low urgency)
**Severity:** LOW
**Bugs:** B-BUG-4
**Files to modify:** `aidm/core/maneuver_resolver.py`
**Verification ref:** `docs/verification/DOMAIN_B_VERIFICATION.md` — formula B-MR-1027

### B-BUG-4: Sunder uses hardcoded 1d8 instead of weapon damage

**Location:** maneuver_resolver.py:1027
**SRD rule:** PHB p.158 — Sunder damage is dealt with the attacker's weapon.
**Current code:** Hardcoded `1d8` damage.
**Fix:** Replace with attacker's actual weapon damage dice:
```python
# Before:
damage = rng.stream("combat").randint(1, 8)

# After:
damage = roll_weapon_damage(attacker_weapon)  # Use existing dice rolling utility
```
**Implementation notes:**
- The weapon damage dice should come from the same source as the attack resolver's dice.
- STR modifier applies to sunder damage per normal melee rules.
- If the weapon data isn't available in the sunder context, thread it through from the caller.

### Tests to add:
1. Sunder with longsword (1d8): damage range 1-8 + STR
2. Sunder with greatsword (2d6): damage range 2-12 + STR*1.5
3. Sunder with dagger (1d4): damage range 1-4 + STR

**Commit:** `fix: B-BUG-4 — sunder uses attacker weapon damage`

---

## WO-FIX-10: Movement & Terrain Bugs

**Priority:** 9
**Severity:** MIXED (HIGH + MEDIUM + LOW)
**Bugs:** E-BUG-01, E-BUG-02, E-BUG-03
**Files to modify:** `aidm/core/terrain_resolver.py`, `aidm/core/mounted_combat.py`
**Verification ref:** `docs/verification/DOMAIN_E_VERIFICATION.md`

### E-BUG-01: Soft cover condition inverted (MEDIUM)

**Location:** terrain_resolver.py:256
**SRD rule:** PHB p.152 — Soft cover from creatures applies to RANGED attacks, not melee.
**Current code:** `elif soft_cover and is_melee:`
**Fix:** `elif soft_cover and not is_melee:`
**One-character fix.** Change `is_melee` to `not is_melee`.

### E-BUG-02: Water fall damage incorrect (HIGH)

**Location:** terrain_resolver.py:613-619, 643-644
**SRD rule:** DMG p.304 — "Water at least 10 feet deep: first 20 feet = no damage (DC 15 Swim check). After that, 1d3 nonlethal per 10 feet."
**Current code:** First 20ft free (no check), then 1d6 lethal per 10ft.
**Fix — three changes:**

1. **Add DC 15 Swim check for first-20ft-free zone:**
```python
if is_into_water and water_depth >= 10:
    # DC 15 Swim check for safe entry
    swim_roll = rng.stream("combat").randint(1, 20)
    swim_modifier = entity.get(EF.SWIM_MOD, 0)  # or placeholder
    if swim_roll + swim_modifier >= 15:
        safe_distance = 20
    else:
        safe_distance = 0
    if fall_distance <= safe_distance:
        damage_dice = 0
    else:
        damage_dice = max(0, (fall_distance - safe_distance) // 10)
```

2. **Change die size from d6 to d3 for water falls:**
```python
# Water fall damage uses d3, not d6
if is_water_fall:
    damage_rolls = [combat_rng.randint(1, 3) for _ in range(damage_dice)]
else:
    damage_rolls = [combat_rng.randint(1, 6) for _ in range(damage_dice)]
```

3. **Mark damage as nonlethal for water falls:**
```python
damage_type = "nonlethal" if is_water_fall else "lethal"
```
If the damage system doesn't support lethal/nonlethal distinction, add a comment noting the limitation and use lethal d3 as a partial fix (still closer to SRD than d6 lethal).

### E-BUG-03: SIZE_ORDER missing 3 size categories (LOW)

**Location:** mounted_combat.py:667
**SRD rule:** PHB p.132 — 9 size categories.
**Current code:** 6 entries (missing Fine, Diminutive, Colossal).
**Fix:** Replace with complete table:
```python
SIZE_ORDER = {
    "fine": 0, "diminutive": 1, "tiny": 2, "small": 3,
    "medium": 4, "large": 5, "huge": 6, "gargantuan": 7, "colossal": 8
}
```
**Also update** the fallback default from `2` (Medium in old scale) to `4` (Medium in new scale):
```python
mount_size_val = SIZE_ORDER.get(mount_size.lower(), 4)  # was 2
target_size_val = SIZE_ORDER.get(target_size.lower(), 4)  # was 2
```

### Tests to add:
1. Ranged attack through occupied square: soft cover (+4 AC) applies
2. Melee attack through occupied square: soft cover does NOT apply
3. 50ft fall into deep water with passed Swim check: 3d3 nonlethal (not 3d6 lethal)
4. 50ft fall into deep water with failed Swim check: 5d3 nonlethal
5. Colossal mount vs Medium target: SIZE_ORDER comparison works correctly
6. Fine creature: SIZE_ORDER lookup returns 0 (not default 4)

**Commit:** `fix: E-BUG-01/02/03 — soft cover, water fall damage, size categories`

---

## WO-FIX-11: Action Cost Table

**Priority:** 10
**Severity:** MEDIUM
**Bugs:** G-PLAY-71-86
**Files to modify:** `aidm/core/play_loop.py` (or equivalent action cost table location)
**Verification ref:** `docs/verification/DOMAIN_G_VERIFICATION.md` — formula G-PLAY-71-86

### G-PLAY-71-86: Trip/Disarm/Grapple classified as "standard" instead of "varies"

**Location:** play_loop.py:71-86 (action cost table)
**SRD rule:** PHB Action Types table — Trip, Disarm, and Grapple are listed as "Varies" because they can substitute for any melee attack (including during a full attack).
**Current code:** All three are classified as `"standard"`.
**Fix:**
```python
# Change these entries in the action cost table:
"trip": "varies",      # was "standard"
"disarm": "varies",    # was "standard"
"grapple": "varies",   # was "standard"
```

**Implementation notes:**
- This change affects whether the CLI/action parser allows these maneuvers as part of a full attack sequence.
- If the action parser doesn't currently support `"varies"` type, it needs to be added. The behavior should be: "varies" actions can be used as a standard action OR can replace a single melee attack in a full attack.
- If implementing full "varies" support is too large for this WO, change the classification to `"varies"` and add a `# TODO: enable as attack substitution in full attack` comment. The classification fix is the correctness fix; the full attack integration is a feature.

### Tests to add:
1. Trip action type is "varies" (not "standard")
2. Disarm action type is "varies"
3. Grapple action type is "varies"
4. If "varies" parsing is implemented: trip can be used during full attack sequence

**Commit:** `fix: G-PLAY-71-86 — trip/disarm/grapple action type = varies`

---

## WO-FIX-12: Character Progression Bugs

**Priority:** 11
**Severity:** MEDIUM
**Bugs:** BUG-F1, BUG-F2, BUG-F3
**Files to modify:** `aidm/core/experience_resolver.py`, `aidm/schemas/leveling.py`
**Verification ref:** `docs/verification/DOMAIN_F_VERIFICATION.md`

### BUG-F1: Level 1 feat not granted by apply_level_up

**Location:** experience_resolver.py:230
**SRD rule:** PHB p.22 — Feats at levels 1, 3, 6, 9, 12, 15, 18.
**Current code:** `if level % 3 == 0:` — grants at 3, 6, 9... but misses level 1.
**Fix:**
```python
if new_level == 1 or new_level % 3 == 0:
```
**Investigation needed:** Check if character creation code handles the level-1 feat separately. If it does, this may not be a runtime bug. Search for `feat` in the character creation path. If level-1 feat IS handled in creation, add a comment explaining the split and mark this as not-a-bug. If NOT handled, apply the fix.

### BUG-F2 / BUG-F3: XP table levels 11-20 computed incorrectly

**Location:** leveling.py:291-308
**SRD rule:** DMG Table 2-6 — XP awards by level and CR delta.
**Current code:** Levels 11-20 entries are generated by a formula: flat 150 XP for delta < -2, and `base_xp * (delta + 1)` for delta > 0. Neither matches DMG Table 2-6.
**Fix:** Replace the computed loop with hardcoded values from DMG Table 2-6.

**DMG Table 2-6 reference (per-character XP awards):**

The builder should look up DMG Table 2-6 (page 38) and hardcode the complete table. The table has rows for party levels 1-20 and columns for CR deltas from -7 to +4 (or similar range). Key values for levels 11-20 that the formula gets wrong:

For example, Level 11 party:
- CR 11 (delta 0): 300 XP per character
- CR 10 (delta -1): 263 XP
- CR 9 (delta -2): 225 XP
- CR 8 (delta -3): 200 XP (NOT flat 150)

The exact values must come from the DMG table. The builder should:
1. Read DMG Table 2-6 from d20srd.org or the SRD
2. Create a complete lookup table for levels 1-20 × CR deltas
3. Replace the formula with direct table lookup

### Tests to add:
1. Level 1 character gains feat slot on level-up to level 1 (or verify creation handles it)
2. Level 11 party, CR 8 encounter: XP matches DMG (not flat 150)
3. Level 15 party, CR 16 encounter: XP matches DMG (not `base * 2`)
4. Spot-check 5+ entries across levels 11-20 against DMG table

**Commit:** `fix: BUG-F1/F2/F3 — level 1 feat + hardcoded XP table 11-20`

---

## WO-FIX-13: Colossal Footprint

**Priority:** 12 (lowest — trivial fix)
**Severity:** MEDIUM
**Bugs:** I-GEOM-291
**Files to modify:** `aidm/schemas/geometry.py`
**Verification ref:** `docs/verification/DOMAIN_I_VERIFICATION.md`

### I-GEOM-291: Colossal footprint is 25 instead of 36

**Location:** geometry.py:291-301
**SRD rule:** PHB p.132 — Colossal = 30ft space = 6×6 = 36 squares.
**Current code:** `SizeCategory.COLOSSAL: 25` (implies 5×5 = 25ft space)
**Fix:**
```python
SizeCategory.COLOSSAL: 36  # 6x6 = 30ft space
```
**Also update the docstring** on line 286: change "25 squares (5x5)" to "36 squares (6x6)".

**Check for downstream impact:** Search for any code that assumes Colossal is 5×5 or 25 squares. If any grid rendering, pathfinding, or reach calculations use this value, they'll automatically get the correct 6×6 footprint after this change.

### Tests to add:
1. `SizeCategory.COLOSSAL` footprint returns 36
2. Any grid placement test with Colossal creature uses 6×6 area

**Commit:** `fix: I-GEOM-291 — Colossal footprint 36 squares (6x6), not 25`

---

## WO-FIX-14: TWF Off-Hand Weapon Weight (PM-recommended from AMBIGUOUS)

**Priority:** 13
**Severity:** MEDIUM
**Bugs:** I-AMB-02 (reclassified from AMBIGUOUS to FIX-SRD by PM recommendation)
**Files to modify:** `aidm/core/feat_resolver.py`
**Verification ref:** `docs/verification/DOMAIN_I_VERIFICATION.md` — formula I-FEAT-386

### I-AMB-02: TWF feat ignores heavy off-hand weapon

**Location:** feat_resolver.py:386
**SRD rule:** PHB p.105 — TWF feat: -2/-2 with light off-hand, -4/-4 with heavy off-hand.
**Current code:** Always returns (-2, -2) when TWF feat is present, regardless of `has_light_offhand` parameter.
**Fix:**
```python
if FeatID.TWO_WEAPON_FIGHTING in feats:
    if has_light_offhand:
        return (-2, -2)
    else:
        return (-4, -4)
```
**Note:** The `has_light_offhand` parameter already exists in the function signature — it just needs to be used in the TWF feat branch.

### Tests to add:
1. TWF feat + light off-hand: penalties = (-2, -2)
2. TWF feat + heavy off-hand: penalties = (-4, -4)
3. No TWF feat + light off-hand: penalties = (-4, -4) (existing behavior, verify unchanged)
4. No TWF feat + heavy off-hand: penalties = (-6, -10) (existing behavior, verify unchanged)

**Commit:** `fix: I-AMB-02 — TWF penalties respect off-hand weapon weight`

---

## Dispatch Summary

| WO | Bugs | Severity | Effort | Parallel Safe? | Depends On |
|----|------|----------|--------|----------------|------------|
| WO-FIX-01 | BUG-1/8/9 | HIGH | LOW-MED | Yes (after WO-FIX-03) | WO-FIX-03 |
| WO-FIX-02 | BUG-2 | MEDIUM | LOW | Yes | None |
| WO-FIX-03 | BUG-3/4 | HIGH | MEDIUM | Yes | None |
| WO-FIX-04 | BUG-5/6/7 | MEDIUM | LOW | Yes | None |
| WO-FIX-06 | BUG-C-002 | HIGH | LOW | Yes | None |
| WO-FIX-07 | B-BUG-1/3/5 | MEDIUM | LOW | Yes | None |
| WO-FIX-08 | B-BUG-2 | HIGH | MEDIUM | Yes | None |
| WO-FIX-09 | B-BUG-4 | LOW | LOW | Yes | None |
| WO-FIX-10 | E-BUG-01/02/03 | MIXED | MEDIUM | Yes | None |
| WO-FIX-11 | G-PLAY-71-86 | MEDIUM | MEDIUM | Yes | None |
| WO-FIX-12 | BUG-F1/F2/F3 | MEDIUM | MEDIUM | Yes | None |
| WO-FIX-13 | I-GEOM-291 | MEDIUM | TRIVIAL | Yes | None |
| WO-FIX-14 | I-AMB-02 | MEDIUM | TRIVIAL | Yes | None |

**Recommended dispatch waves:**

**Wave 1 (HIGH priority, parallel):** WO-FIX-03, WO-FIX-06, WO-FIX-08
**Wave 2 (depends on Wave 1):** WO-FIX-01 (depends on WO-FIX-03 schema)
**Wave 3 (MEDIUM priority, parallel):** WO-FIX-02, WO-FIX-04, WO-FIX-07, WO-FIX-10, WO-FIX-11, WO-FIX-12
**Wave 4 (LOW priority, parallel):** WO-FIX-09, WO-FIX-13, WO-FIX-14

---

## End of Fix WO Dispatch Packet
