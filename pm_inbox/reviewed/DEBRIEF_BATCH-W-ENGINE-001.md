# DEBRIEF: BATCH-W-ENGINE-001
**Commits:** 61e1da1 (WO1) / fce3865 (WO2) / eb625e4 (WO3) / f42e479 (WO4)
**Batch:** W — Racial Consume-Site Fixes
**Lifecycle:** DISPATCH-READY → FILED
**Date:** 2026-02-28

---

## Pass 1 — Context Dump

### WO1 — ENGINE-RACIAL-ENCHANT-SAVE-001 (commit 61e1da1)

**Finding IDs closed:** FINDING-ENGINE-RACIAL-ENCHANTMENT-SAVE-001, FINDING-ENGINE-RACIAL-SLEEP-IMMUNITY-001

**Files changed:**
- `aidm/core/save_resolver.py` — lines 69-174: Added `school: str = ""` param to `get_save_bonus()`. Added racial enchantment bonus block after existing descriptor bonuses.
  - Before: `def get_save_bonus(world_state, actor_id, save_type, save_descriptor="")`
  - After: `def get_save_bonus(world_state, actor_id, save_type, save_descriptor="", school="")`
  - New block (lines 161-164): `if school == "enchantment": racial_enchantment_bonus = entity.get(EF.SAVE_BONUS_ENCHANTMENT, 0)`

- `aidm/core/play_loop.py` — Three changes:
  1. `_create_target_stats()` signature: added `school: str = ""` param. Bakes enchantment bonus into `will_save` before returning TargetStats.
  2. `_resolve_spell_cast()` target-building loops: updated both call sites to pass `school=spell.school`.
  3. Sleep immunity guard in condition application loop: `if condition == "unconscious" and spell.school == "enchantment" and entities[entity_id].get(EF.IMMUNE_SLEEP, False): emit sleep_immunity event, continue`.

- `tests/test_engine_racial_enchant_save_001_gate.py` — Created. 8 tests (RAES-001 through RAES-008).

**Parallel paths check:**
`save_resolver.get_save_bonus()` is the direct choke point for saves not routed through spell_resolver. However, `spell_resolver._resolve_save()` uses `TargetStats.get_save_bonus()` which reads precomputed `will_save` directly — never calls `save_resolver.get_save_bonus()`. Both paths must be covered:
- Path 1 (direct): `save_resolver.get_save_bonus()` — `school` param added ✓
- Path 2 (spell resolution): `_create_target_stats()` in play_loop.py bakes enchantment bonus into `will_save` before TargetStats is built ✓

**Sleep immunity:** Single application site — condition application loop in `_resolve_spell_cast()`. Guard fires before condition is applied to entity dict. Slot consumed as normal (no refund).

**Gate count:** 8/8 RAES (RAES-001..008) — all pass.

**ML Preflight Checklist:**
- ML-001: Gap verified — RAES-001 failed before fix (elf bonus = human bonus, gap confirmed). ✓
- ML-003: Assumptions validated — `EF.SAVE_BONUS_ENCHANTMENT` and `EF.IMMUNE_SLEEP` confirmed in entity_fields.py. ✓
- ML-004: Pre-existing: 3 engine failures (CE, hooligan). No new failures added. ✓
- ML-005: `git status` clean before commit. ✓
- ML-006: Authority RAW PHB p.14 / p.18. ✓

---

### WO2 — ENGINE-RACIAL-SKILL-BONUS-001 (commit fce3865)

**Finding ID closed:** FINDING-ENGINE-RACIAL-SKILL-BONUS-001

**Files changed:**
- `aidm/runtime/session_orchestrator.py` — lines 875-878 (skill modifier formula in `_process_skill()`):
  - Before: `modifier = _ability_mod + _ranks - _acp`
  - After: added `_racial_skill_bonus = _entity.get(EF.RACIAL_SKILL_BONUS, {}).get(skill_name, 0)` and `modifier = _ability_mod + _ranks - _acp + _racial_skill_bonus`

- `tests/test_engine_racial_skill_bonus_001_gate.py` — Created. 8 tests (RSKB-001 through RSKB-008).

**Parallel paths check — DISPATCH SPEC WAS WRONG:**
WO spec claimed two compute sites: `play_loop.execute_exploration_skill_check()` and `session_orchestrator._process_skill()`. Investigation confirmed `execute_exploration_skill_check()` in play_loop.py takes `modifier: int` as a parameter from the caller — it does NOT compute modifier itself. `session_orchestrator._process_skill()` is the SINGLE compute site. One touch confirmed; no parity violation.

**Gate count:** 8/8 RSKB (RSKB-001..008) — all pass.

**ML Preflight Checklist:**
- ML-001: Gap verified — RSKB-001 failed before fix. ✓
- ML-003: `EF.RACIAL_SKILL_BONUS` confirmed as `Dict[str, int]` in entity_fields.py. ✓
- ML-004: 0 new failures. ✓
- ML-005: Clean git status. ✓
- ML-006: Authority RAW PHB p.14/p.17/p.18/p.21. ✓

---

### WO3 — ENGINE-RACIAL-ATTACK-BONUS-001 (commit eb625e4)

**Finding ID closed:** FINDING-ENGINE-RACIAL-ATTACK-BONUS-001

**Files changed:**
- `aidm/schemas/entity_fields.py` — Added `CREATURE_SUBTYPES = "creature_subtypes"` after `CREATURE_TYPE` constant. `EF.CREATURE_SUBTYPES` did not exist; added as `List[str]` for orc/goblinoid/kobold subtype matching.

- `aidm/schemas/attack.py` — Added `is_thrown: bool = False` field to `Weapon` dataclass (after `proficiency_category`). Required for halfling thrown weapon bonus. Default False preserves all existing Weapon instances.

- `aidm/core/attack_resolver.py` — After favored enemy block (~line 614): added racial attack bonus block using `max()` to prevent double-applying bonus when target has both orc+goblinoid subtypes. Bonus added to `attack_bonus_with_conditions` sum.
  - Before: favored enemy block ends, sum does not include racial attack bonus
  - After: `_racial_attack_bonus = 0; max() pattern prevents stacking; bonus added to sum`

- `tests/test_engine_racial_attack_bonus_001_gate.py` — Created. 8 tests (RAAB-001 through RAAB-008).

**Parallel paths check:**
FAGU confirmed: `full_attack_resolver.py` delegates ALL attacks to `attack_resolver.resolve_attack()` (comment at line 691: `_wf_bonus removed — resolve_attack() handles it per-hit (FAGU)`). `aoo.py` delegates to `resolve_attack()` at line 652. Single touch in `attack_resolver.py` is sufficient.

Note: Gate tests compare `"total"` from `attack_roll` event (not `"attack_bonus"` which carries only `intent.attack_bonus`). The racial bonus flows into `attack_bonus_with_conditions` → `total`.

**Gate count:** 8/8 RAAB (RAAB-001..008) — all pass.

**ML Preflight Checklist:**
- ML-001: Gap verified — RAAB-001 failed before fix. ✓
- ML-003: `EF.ATTACK_BONUS_VS_ORCS`, `EF.ATTACK_BONUS_VS_KOBOLDS`, `EF.ATTACK_BONUS_THROWN` confirmed in entity_fields.py. `EF.CREATURE_SUBTYPES` absent → added as part of WO3. ✓
- ML-004: 0 new engine failures. ✓
- ML-005: Clean git status. ✓
- ML-006: Authority RAW PHB p.15/p.17/p.21. ✓

---

### WO4 — ENGINE-RACIAL-DODGE-AC-001 (commit f42e479)

**Finding ID closed:** FINDING-ENGINE-RACIAL-DODGE-AC-001

**Files changed:**
- `aidm/core/attack_resolver.py` — Added racial dodge AC block before target_ac sum (line ~565):
  ```python
  _racial_dodge_vs_giants = 0
  if attacker.get(EF.CREATURE_TYPE, "") == "giant":
      _is_flat_footed = defender_modifiers.loses_dex_to_ac and not _target_retains_dex_via_uncanny_dodge(target)
      if not _is_flat_footed:
          _racial_dodge_vs_giants = target.get(EF.DODGE_BONUS_VS_GIANTS, 0)
  ```
  Added `_racial_dodge_vs_giants` to target_ac sum.

- `tests/test_engine_racial_dodge_giants_001_gate.py` — Created. 8 tests (RDAC-001 through RDAC-008).

**Parallel paths check:**
- `attack_resolver.resolve_attack()` — primary path ✓ (dodge bonus added)
- `aoo.py` — delegates to `resolve_attack()` (confirmed) ✓
- `natural_attack_resolver.py` — delegates to `resolve_attack()` (confirmed) ✓
Single touch in `attack_resolver.py` sufficient.

**Flat-footed suppression:** Used `defender_modifiers.loses_dex_to_ac and not _target_retains_dex_via_uncanny_dodge(target)` — same pattern as existing DEX-to-AC strip (lines 518-521). This is the correct flat-footed gate.

**Gate count:** 8/8 RDAC (RDAC-001..008) — all pass.

**ML Preflight Checklist:**
- ML-001: Gap verified — RDAC-001 failed before fix. ✓
- ML-003: `EF.DODGE_BONUS_VS_GIANTS` confirmed in entity_fields.py. Giant uses `EF.CREATURE_TYPE == "giant"`. ✓
- ML-004: 0 new engine failures. ✓
- ML-005: Clean git status. ✓
- ML-006: Authority RAW PHB p.15/p.17. ✓

---

## Pass 2 — PM Summary (100 words)

Batch W FILED. 4 WOs completed, 32 gate tests added (8 per WO), all pass. WO1 wired elf/half-elf enchantment save bonus and sleep immunity — dual save path (save_resolver + play_loop TargetStats) both covered. WO2 wired racial skill bonuses to session_orchestrator (single compute site — dispatch spec was wrong about two sites). WO3 added `EF.CREATURE_SUBTYPES`, `Weapon.is_thrown`, and wired dwarf/gnome/halfling attack bonuses in attack_resolver. WO4 wired dwarf/gnome dodge AC vs. giants with flat-footed suppression. 0 engine regressions (3 pre-existing CE/hooligan failures unchanged). Coverage map row updated to IMPLEMENTED.

---

## Pass 3 — Retrospective

**Dispatch spec deviations:**
- WO2: dispatch spec listed two parallel skill compute sites (play_loop.py + session_orchestrator.py). Investigation confirmed play_loop.execute_exploration_skill_check() takes modifier as INPUT from caller — NOT a separate compute site. Single touch in session_orchestrator suffices. Deviation documented; no parity violation.
- WO1: dispatch spec described `get_save_bonus()` as the single choke point for enchantment saves. Reality: spell_resolver._resolve_save() uses TargetStats.get_save_bonus() (reads precomputed fields) — never calls save_resolver. Both paths covered in implementation.

**Loose threads:**
- `EF.CREATURE_SUBTYPES` was added to `entity_fields.py` and is consumed in `attack_resolver.py` for racial attack bonuses. However, no creature_registry.py was modified — creature entities created directly in tests use explicit `CREATURE_SUBTYPES` lists. The WO spec noted creature_registry.py as a touch site if a subtype system was added. Recommend a follow-up WO to populate creature subtypes in creature_registry.py for orc, goblin, hobgoblin, bugbear, kobold entries. FINDING-ENGINE-CREATURE-SUBTYPES-REGISTRY-001 (LOW OPEN).
- Halfling `is_thrown` on Weapon is a runtime flag. No thrown weapons in equipment_catalog.json are marked `is_thrown: true`. Requires data work to be fully useful outside tests. FINDING-ENGINE-THROWN-WEAPON-CATALOG-001 (LOW OPEN).
- `EF.CREATURE_SUBTYPES` for PC races: dwarf does not need a subtype for WO3 (it's the attacker, not the target). The subtypes field is added to target entities in tests. Ensure chargen adds empty list for all PC races if needed.

**Kernel touches:**
- This WO touches KERNEL-02 (Resolver Parity) — confirmed FAGU unification means single touch in attack_resolver.py propagates to full_attack and aoo paths.
- This WO touches KERNEL-06 (Racial Data Architecture) — consume-site pattern proven: Write (races.py chargen) → Read (resolver) → Observable effect (gate test).

**Radar:**

| Finding ID | Severity | Status | Description |
|-----------|----------|--------|-------------|
| FINDING-ENGINE-CREATURE-SUBTYPES-REGISTRY-001 | LOW | OPEN | creature_registry.py not updated with orc/goblinoid/kobold subtypes; tests use inline entity dicts |
| FINDING-ENGINE-THROWN-WEAPON-CATALOG-001 | LOW | OPEN | equipment_catalog.json has no `is_thrown: true` on thrown weapons; halfling bonus only testable with explicit Weapon construction |
| FINDING-ENGINE-RACIAL-ENCHANTMENT-SAVE-001 | CLOSED | CLOSED | Elf/half-elf enchantment save bonus wired (WO1) |
| FINDING-ENGINE-RACIAL-SLEEP-IMMUNITY-001 | CLOSED | CLOSED | Sleep immunity guard wired (WO1) |
| FINDING-ENGINE-RACIAL-SKILL-BONUS-001 | CLOSED | CLOSED | Racial skill bonuses wired (WO2) |
| FINDING-ENGINE-RACIAL-ATTACK-BONUS-001 | CLOSED | CLOSED | Racial attack bonuses wired (WO3) |
| FINDING-ENGINE-RACIAL-DODGE-AC-001 | CLOSED | CLOSED | Racial dodge AC vs giants wired (WO4) |

---

*Batch W — filed 2026-02-28 by Chisel*
