**Lifecycle:** ARCHIVE

# DEBRIEF — WO-ENGINE-FREE-HAND-SETTER-001

**Commit:** `801875d`
**Gates:** FHS-001..008 — 8/8 PASS
**Batch:** AM (WO3 of 4)

---

## Pass 1 — Context Dump

### Files Changed

| File | Lines | Change |
|------|-------|--------|
| `aidm/chargen/builder.py` | ~937–946 (after _assign_starting_equipment) | Path 1: FREE_HANDS setter + inventory scan fallback |
| `aidm/chargen/builder.py` | ~1334–1343 (_build_multiclass_character) | Path 2: identical FREE_HANDS setter |

### Before / After (Path 1)

**Before:** (field absent — not set)

**After:**
```python
# WO-ENGINE-FREE-HAND-SETTER-001: Free hand count for Deflect Arrows gate (PHB p.93)
_fhs_wdict = entity.get(EF.WEAPON) or {}
if not _fhs_wdict:
    for _fhs_item in entity.get(EF.INVENTORY, []):
        _fhs_w = _catalog_weapon(_fhs_item.get("item_id", ""))
        if _fhs_w:
            _fhs_wdict = _fhs_w
            break
entity[EF.FREE_HANDS] = 0 if _fhs_wdict.get("weapon_type") == "two-handed" else 1
```

### Key Design Decision — Inventory Scan Fallback

`_assign_starting_equipment()` has two paths:
- **Default kit path:** sets `entity[EF.WEAPON]` — weapon dict available directly
- **Override path** (`starting_equipment` kwarg provided): returns early without setting `EF.WEAPON` — only `EF.INVENTORY` is populated

The inventory scan fallback (`for _fhs_item in entity.get(EF.INVENTORY, [])`) handles the override path by looking up the first inventory item via `_catalog_weapon()`. Without this, greatsword overrides would return FREE_HANDS=1 (wrong).

### PM Acceptance Notes — all confirmed

- FHS-001: greatsword → 0 ✓ (via inventory scan)
- FHS-002: longsword → 1 ✓ (via inventory scan)
- FHS-003: empty equipment → 1 ✓ (no weapon in inventory)
- FHS-004: both paths produce same result ✓ (multiclass: unarmed → 1)
- FHS-005: EF.FREE_HANDS key explicitly present ✓
- FHS-006: longbow → 1 ✓
- FHS-007: greatsword + deflect_arrows feat → FREE_HANDS=0 blocks ✓
- FHS-008: longsword + deflect_arrows → FREE_HANDS≥1 eligible ✓

### Gate file
`tests/test_engine_free_hand_setter_gate.py` — 8 tests.

---

## Pass 2 — PM Summary

`EF.FREE_HANDS` now set at chargen in both `build_character` and `_build_multiclass_character` paths. Two-handed weapon (`weapon_type=="two-handed"`) → 0; all other cases → 1. Inventory scan fallback handles the override-path edge case where `EF.WEAPON` is absent but `EF.INVENTORY` is populated. Consume site confirmed: `attack_resolver.py:906` — Deflect Arrows gate reads `FREE_HANDS` to check `>= 1`. FHS-007 proves block (greatsword), FHS-008 proves eligibility (longsword). PHB p.93 honored. 8/8 gates pass.

---

## Pass 3 — Retrospective

**FINDING-ENGINE-TWF-FREE-HANDS-001 (LOW, CONSUME_DEFERRED):** Two-weapon fighting (both hands occupied) would be FREE_HANDS=0, but TWF chargen doesn't specify this at inventory build time. Deferred — TWF mechanic not yet in engine.

**Parallel paths confirmed:** Both `build_character` (line ~937) and `_build_multiclass_character` (line ~1334) receive identical FREE_HANDS setter logic. Multiclass path starts unarmed → defaults to 1. Verified multiclass path does NOT call `_assign_starting_equipment` (confirmed via comment at line 1326 and grep).

**Kernel touches:** None.

---

## Radar

| ID | Severity | Status | Note |
|----|----------|--------|------|
| FINDING-ENGINE-TWF-FREE-HANDS-001 | LOW | CONSUME_DEFERRED | TWF not in engine yet; no blocker |

---

## Coverage Map Update

Row 331 (Deflect Arrows) updated to add FHS reference:
- Added: `EF.FREE_HANDS now set at chargen (both paths) via inventory scan fallback. FHS-001..008. Batch AM.`

## Consume-Site Confirmation

- **Write site:** `builder.py` ~line 937 (Path 1) + ~line 1334 (Path 2) — `entity[EF.FREE_HANDS] = 0 if ... else 1`
- **Read site:** `attack_resolver.py:906` — `free_hands = entity.get(EF.FREE_HANDS, 1); if free_hands < 1: ... skip deflect`
- **Effect:** Greatsword wielder cannot Deflect Arrows; longsword wielder can
- **Gate proof:** FHS-007 (greatsword FREE_HANDS=0 → deflect blocked), FHS-008 (longsword FREE_HANDS≥1 → eligible)
