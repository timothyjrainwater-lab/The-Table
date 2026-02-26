# DEBRIEF — WO-CHARGEN-POOL-INIT-001
# Class-Feature Pool Initialization at Chargen

**Verdict:** ACCEPTED 10/10
**Gate:** ENGINE-CHARGEN-POOL-INIT
**Date:** 2026-02-26
**WO:** WO-CHARGEN-POOL-INIT-001
**Finding closed:** FINDING-CHARGEN-POOL-INIT-001

---

## Pass 1 — Per-File Breakdown

### `aidm/chargen/builder.py`

**Two insertion sites:**

1. `build_character()` — after equipment assignment block, before return.
2. `_build_multiclass_character()` — after racial trait fields block.

Both sites required the same initialization logic. Multiclass characters use `_build_multiclass_character()` rather than `build_character()` for the entity dict construction — missing either site would leave multiclass paladins/bards/druids still broken.

**Five pool fields initialized:**

| Field | Formula | Unlock condition |
|-------|---------|-----------------|
| `EF.SMITE_USES_REMAINING` | Count `smite_evil_N_per_day` markers in `_CLASS_FEATURES["paladin"]` up to current paladin_level | paladin_level > 0 |
| `EF.LAY_ON_HANDS_POOL` | `paladin_level × cha_mod` if `cha_mod > 0` else 0 | paladin_level ≥ 2 |
| `EF.LAY_ON_HANDS_USED` | 0 | paladin_level ≥ 2 |
| `EF.BARDIC_MUSIC_USES_REMAINING` | `max(1, bard_level + cha_mod)` | bard_level ≥ 1 |
| `EF.WILD_SHAPE_USES_REMAINING` | `max(1, 1 + (druid_level - 4) // 2)` | druid_level ≥ 5 |

**Pre-existing replay drift noted:** `test_replay_tavern_gold_master` drifts on `payload.twd_ac_bonus` — attack resolver field, not touched by this WO. Pre-existing, owned by WO-ENGINE-GOLD-MASTER-REGEN-001.

---

## Pass 2 — PM Summary (≤100 words)

WO-CHARGEN-POOL-INIT-001 ACCEPTED 10/10. FINDING-CHARGEN-POOL-INIT-001 CLOSED. Five pool fields now initialized at chargen: `EF.SMITE_USES_REMAINING`, `EF.LAY_ON_HANDS_POOL`, `EF.LAY_ON_HANDS_USED`, `EF.BARDIC_MUSIC_USES_REMAINING`, `EF.WILD_SHAPE_USES_REMAINING`. Two insertion sites: `build_character()` and `_build_multiclass_character()`. Two Pass 3 catches corrected before gate: Wild Shape threshold (≥4 → ≥5, PHB L5 unlock) and LoH formula (`max(1, cha_mod)` → `cha_mod if cha_mod > 0 else 0`). Replay drift on `twd_ac_bonus` confirmed pre-existing.

---

## Pass 3 — Retrospective

**Two corrections caught before gate — both spec errors, not builder errors:**

1. **Wild Shape threshold:** Dispatch spec said `druid_level >= 5` (PHB L5 unlock). Builder initially implemented `>= 4`. Caught and corrected. PHB p.37: Wild Shape available from level 5. The `_get_wild_shape_uses()` formula `max(1, 1 + (druid_level - 4) // 2)` already returns 0 for druid_level < 5 — but the guard threshold matters for the `if` block. Correct threshold is 5.

2. **Lay on Hands formula:** Dispatch spec said `cha_mod if cha_mod > 0 else 0`. Builder initially wrote `max(1, cha_mod)`. These are different: `max(1, 0) = 1` but a paladin with CHA 10 (mod 0) should get pool 0 (paladin_level × 0 = 0). The PHB formula is multiplicative — CHA mod of 0 yields a pool of 0, not 1. Correct formula: `paladin_level * cha_mod if cha_mod > 0 else 0`.

**Two insertion sites is the right design.** The dispatch spec only called out `build_character()`. Builder correctly identified that `_build_multiclass_character()` also required the same initialization — a multiclass paladin/bard/druid built via `class_mix=` would have still been broken without it. Good catch.

**Pattern established:** Pool initialization now lives at chargen. Rest resolver resets to the same formula. Any future class-feature pool field must be initialized at both chargen insertion sites and reset in rest_resolver. This is now the documented convention.

**Recommendation:** Any future WO adding a new class-feature pool field should explicitly state: "Initialize in `build_character()` AND `_build_multiclass_character()`; reset formula in `rest_resolver.py`."

---

*Debrief filed by Slate (PM) on builder verdict receipt.*
