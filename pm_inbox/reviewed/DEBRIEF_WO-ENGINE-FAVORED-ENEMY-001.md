# DEBRIEF — WO-ENGINE-FAVORED-ENEMY-001
# Ranger Favored Enemy Attack and Damage Bonus

**Verdict:** ACCEPTED 10/10
**Gate:** ENGINE-FAVORED-ENEMY
**Date:** 2026-02-26
**WO:** WO-ENGINE-FAVORED-ENEMY-001

---

## Pass 1 — Per-File Breakdown

### `aidm/schemas/entity_fields.py`

**Changes made:**
- `EF.FAVORED_ENEMIES` — list of creature type strings the ranger has as favored enemies
- `EF.CREATURE_TYPE` — creature type string on entity dict (e.g., `"humanoid"`, `"undead"`, `"giant"`)

### `aidm/core/attack_resolver.py` (lines 397-398)

**Changes made:**
- Favored enemy check before attack roll: `favored_enemy_bonus = _get_favored_enemy_bonus(actor, target)`
- Bonus added to attack roll and to post-crit flat damage

**Damage application note:** Damage bonus is applied post-crit (flat), per PHB p.47: favored enemy bonus is a flat bonus to damage, not multiplied on critical hits. Correct behavior.

### `aidm/core/full_attack_resolver.py` (lines 706-709)

**Changes made:**
- Same favored enemy bonus threading into `resolve_single_attack_with_critical()` via new `favored_enemy_bonus` parameter
- Applied consistently across all iterative attacks in a full attack sequence

**New parameter:** `favored_enemy_bonus` added to `resolve_single_attack_with_critical()` signature — clean extension, existing callers unaffected by default value.

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-FAVORED-ENEMY-001 ACCEPTED 10/10. `EF.FAVORED_ENEMIES` + `EF.CREATURE_TYPE` added to entity_fields. Attack bonus and flat damage bonus both applied when target creature_type in actor's favored_enemies list. Damage post-crit (flat) per PHB p.47. New `favored_enemy_bonus` parameter threaded into `resolve_single_attack_with_critical()` for full attack support. FE-01–FE-10 all pass. No regressions.

---

## Pass 3 — Retrospective

**Post-crit flat damage is the correct ruling.** PHB p.47 is unambiguous: favored enemy damage is a bonus to damage rolls, not a multiplier. Applying it post-crit is correct — the builder got this right without a prompt.

**`favored_enemy_bonus` parameter addition to `resolve_single_attack_with_critical()`** is a clean pattern extension. This is the same socket that weapon enhancement bonus will use. Both WOs land in the same session — no conflict because WE-001 also adds this parameter.

**Field naming note for FINDING-SAI-FRAGMENTATION-001:** `EF.CREATURE_TYPE` is now a first-class EF constant. Any future immunity check (sneak attack, crits) that needs creature type should read from `EF.CREATURE_TYPE`, not a bare string field. When the SAI normalization WO runs, `sneak_attack.py`'s creature_type lookup should migrate to `EF.CREATURE_TYPE`. This is recorded in FINDING-SAI-FRAGMENTATION-001.

---

*Debrief filed by Slate (PM) on builder verdict receipt.*
