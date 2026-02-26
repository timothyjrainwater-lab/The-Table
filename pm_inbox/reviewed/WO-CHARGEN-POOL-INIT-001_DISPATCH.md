# WO-CHARGEN-POOL-INIT-001
# Class-Feature Pool Initialization at Chargen

**Priority:** MEDIUM
**Filed:** 2026-02-26
**Finding:** FINDING-CHARGEN-POOL-INIT-001
**WO type:** Bug fix — silent wrong behavior

---

## Problem Statement

`build_character()` in `aidm/chargen/builder.py` records class features as string markers only (e.g., `"lay_on_hands"`, `"smite_evil_1_per_day"`). It never translates these markers into working pool fields in the entity dict.

Result: any entity produced by `build_character()` arrives in a live session with the following fields **absent**:

| Field | Resolver | Default read | Behavior |
|-------|----------|-------------|----------|
| `EF.SMITE_USES_REMAINING` | `smite_evil_resolver.py` | `.get(..., 0)` | Paladin silently has 0 smites |
| `EF.BARDIC_MUSIC_USES_REMAINING` | `bardic_music_resolver.py` | `.get(..., 0)` | Bard silently has 0 performances |
| `EF.WILD_SHAPE_USES_REMAINING` | `wild_shape_resolver.py` | `.get(..., 0)` | Druid silently has 0 wild shapes |
| `EF.LAY_ON_HANDS_POOL` | `lay_on_hands_resolver.py` | `.get(..., 0)` | Paladin silently heals 0 HP |
| `EF.LAY_ON_HANDS_USED` | `lay_on_hands_resolver.py` | `.get(..., 0)` | N/A (always 0 anyway) |

No loud failure. No exception. The resolver reads 0 uses remaining and returns a `"no_X_uses"` early-exit code. From the player's perspective, a class feature simply doesn't work — no error, no signal.

Engine gate tests are not affected (they set entity dicts directly in fixtures). Live play via chargen is affected.

---

## Scope

**One file:** `aidm/chargen/builder.py`

**One function:** `build_character()` — the block after equipment init, before return.

No resolver changes. No schema changes. No test fixture changes. Pool field names and formulas are already established by the resolvers and rest_resolver.

---

## Pool Formulas (from resolver source)

### Smite Evil — `EF.SMITE_USES_REMAINING`
PHB p.43: Paladin gains 1 smite use at level 1, +1 use at levels 5, 8, 10, 12, 15, 18, 20.

The `_CLASS_FEATURES["paladin"]` table encodes this as `"smite_evil_N_per_day"` markers. Builder already has access to the full flat feature list for the character's final level.

```python
# Count smite uses from class feature markers
smite_uses = sum(
    1 for f in all_features
    if f.startswith("smite_evil_") and f.endswith("_per_day")
)
```

For levels 1–20: 1/1/1/1/2/2/2/3/3/4/4/5/5/5/6/6/6/7/7/8 smite uses.

### Bardic Music — `EF.BARDIC_MUSIC_USES_REMAINING`
PHB p.29: Bard can use bardic music `bard_level + CHA_mod` times per day (minimum 1 if bard_level > 0).

```python
bard_level = class_levels.get("bard", 0)
if bard_level > 0:
    cha_mod = modifiers["cha"]  # already computed in build_character()
    bardic_uses = max(1, bard_level + cha_mod)
```

### Wild Shape — `EF.WILD_SHAPE_USES_REMAINING`
PHB p.37: Druid gains Wild Shape at level 5. Uses per day: 1 at level 5; +1 per 2 levels above 4 (levels 5,7,9,...).

The formula already lives in `wild_shape_resolver._get_wild_shape_uses(druid_level)`:

```python
def _get_wild_shape_uses(druid_level: int) -> int:
    if druid_level < 4:
        return 0
    return max(1, 1 + (druid_level - 4) // 2)
```

Builder should call this same logic inline or import the helper. Do not import the resolver — duplicate the one-liner inline to avoid circular imports.

### Lay on Hands — `EF.LAY_ON_HANDS_POOL` + `EF.LAY_ON_HANDS_USED`
PHB p.44: `paladin_level × max(1, CHA_mod)`. Pool = 0 if CHA_mod ≤ 0 (no healing from negative CHA).

Formula already in `rest_resolver.py:129`:
```python
pool_max = paladin_level * max(1, cha_mod) if cha_mod > 0 else 0
```

---

## Integration Seams

### Where to insert in `build_character()`

After the existing equipment block (line ~864) and before the final `return entity`. Pattern: follow the racial trait block pattern — a clearly commented section per pool.

```python
# ── Class-feature pool initialization ─────────────────────────────────────
# Pool fields must be set here so chargen entities arrive in live play
# with working pools. Resolvers read .get(field, 0) — absent = silent 0.
# Formulas match rest_resolver.py (full-rest reset uses same math).

# Smite Evil uses (PHB p.43)
paladin_level = class_levels.get("paladin", 0)
if paladin_level > 0:
    all_features_flat = [
        f for lvl_feats in _CLASS_FEATURES.get("paladin", {}).values()
        for f in lvl_feats
        if lvl_feats  # only features up to current paladin_level
    ]
    # NOTE: must filter to features at or below paladin_level
    smite_uses = sum(
        1 for lvl, feats in _CLASS_FEATURES.get("paladin", {}).items()
        if lvl <= paladin_level
        for f in feats
        if f.startswith("smite_evil_") and f.endswith("_per_day")
    )
    entity[EF.SMITE_USES_REMAINING] = smite_uses

# Bardic Music uses (PHB p.29)
bard_level = class_levels.get("bard", 0)
if bard_level > 0:
    cha_mod = modifiers["cha"]
    entity[EF.BARDIC_MUSIC_USES_REMAINING] = max(1, bard_level + cha_mod)

# Wild Shape uses (PHB p.37) — druid 5+ only
druid_level = class_levels.get("druid", 0)
if druid_level >= 5:
    wild_uses = max(1, 1 + (druid_level - 4) // 2)
    entity[EF.WILD_SHAPE_USES_REMAINING] = wild_uses

# Lay on Hands pool (PHB p.44) — paladin 2+
if paladin_level >= 2:
    cha_mod = modifiers["cha"]
    entity[EF.LAY_ON_HANDS_POOL] = paladin_level * max(1, cha_mod) if cha_mod > 0 else 0
    entity[EF.LAY_ON_HANDS_USED] = 0
```

**Notes:**
- `class_levels` is `{class_name: level}` — already in scope inside `build_character()`
- `modifiers["cha"]` is already computed before the entity dict is built
- `_CLASS_FEATURES` is module-level — already in scope
- Do NOT import any resolver — inline the formulas to avoid circular imports
- For multiclass characters: `class_levels` will already contain the correct split (e.g., `{"paladin": 5, "fighter": 3}`)

### `_ENTITY_STRIP_PLAYER` check (WO-SEC-REDACT-002 recommendation)
`EF.SMITE_USES_REMAINING`, `EF.BARDIC_MUSIC_USES_REMAINING`, `EF.WILD_SHAPE_USES_REMAINING` are not HP values. They should NOT be added to `_ENTITY_STRIP_PLAYER`. Players can know their own use counts. No action needed on ws_bridge.

---

## Gate Tests

**Gate name:** `ENGINE-CHARGEN-POOL-INIT`
**File:** `tests/test_engine_chargen_pool_init_001_gate.py`
**Count:** 10 tests

| ID | Description |
|----|-------------|
| CPI-01 | Paladin level 1 entity has `EF.SMITE_USES_REMAINING == 1` |
| CPI-02 | Paladin level 5 entity has `EF.SMITE_USES_REMAINING == 2` |
| CPI-03 | Paladin level 10 entity has `EF.SMITE_USES_REMAINING == 4` |
| CPI-04 | Paladin level 2 entity has `EF.LAY_ON_HANDS_POOL > 0` (positive CHA) |
| CPI-05 | Paladin level 2 entity CHA_mod=0 has `EF.LAY_ON_HANDS_POOL == 0` |
| CPI-06 | Bard level 5 entity has `EF.BARDIC_MUSIC_USES_REMAINING == bard_level + cha_mod` (min 1) |
| CPI-07 | Bard level 1 entity CHA_mod negative has `EF.BARDIC_MUSIC_USES_REMAINING == 1` |
| CPI-08 | Druid level 5 entity has `EF.WILD_SHAPE_USES_REMAINING == 1` |
| CPI-09 | Druid level 7 entity has `EF.WILD_SHAPE_USES_REMAINING == 2` |
| CPI-10 | Fighter level 10 entity has none of the pool fields set (no false init for non-casters) |

---

## Acceptance Criteria

- [ ] All 10 gate tests pass
- [ ] No existing gate regressions
- [ ] `build_character("human", "paladin", level=1)` entity has `EF.SMITE_USES_REMAINING == 1`
- [ ] `build_character("human", "bard", level=3)` entity has `EF.BARDIC_MUSIC_USES_REMAINING >= 1`
- [ ] `build_character("human", "druid", level=5)` entity has `EF.WILD_SHAPE_USES_REMAINING == 1`
- [ ] `build_character("human", "paladin", level=2)` entity has `EF.LAY_ON_HANDS_POOL` set
- [ ] Non-caster classes (fighter, rogue, etc.) do not gain spurious pool fields
- [ ] Multiclass entity with `class_mix={"paladin": 5, "fighter": 3}` correctly initializes paladin pools only

---

## Pass 3 Pre-Brief

**Do not import resolvers.** Circular import risk. Inline the formulas — they are simple enough (one-liners each). The smite formula uses `_CLASS_FEATURES` which is already in module scope.

**The `cha_mod > 0` guard on LOH pool** is not an error — PHB p.44 specifies the pool is `paladin_level × CHA_mod`. A paladin with CHA 8 (CHA_mod = -1) gets a pool of 0 because the formula yields a negative number. This is correct behavior, not a bug.

**Multiclass paladin/bard/druid** — `class_levels` already has the split. The formulas just use `class_levels.get("paladin", 0)` etc. This handles multiclass transparently.

**`EF.LAY_ON_HANDS_USED = 0`** at chargen is always correct — character starts fresh.

---

*Dispatch filed by Slate (PM) — 2026-02-26.*
