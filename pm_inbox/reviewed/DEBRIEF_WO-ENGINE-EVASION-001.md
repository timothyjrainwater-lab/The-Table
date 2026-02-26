# DEBRIEF — WO-ENGINE-EVASION-001

**Verdict:** PASS [10/10]
**Gate:** ENGINE-EVASION
**Date:** 2026-02-26

## Pass 1 — Per-File Breakdown

**`aidm/schemas/entity_fields.py`**
Added `EF.EVASION = "evasion"` and `EF.IMPROVED_EVASION = "improved_evasion"` bool fields as specified. No drift.

**`aidm/chargen/builder.py`**
EF.EVASION=True set at Rogue 2 and Monk 2; EF.IMPROVED_EVASION=True set at Rogue 10 and Monk 9. Both single-class and multiclass builder paths covered. Chargen test EV-09 confirmed: Rogue level 2 has flag, Rogue level 1 does not.

**`aidm/core/spell_resolver.py`**
`_resolve_damage()` required threading `world_state` and `target_entity_id` through from the call site in `resolve_spell()` — spec anticipated this as the likely path. EF import added. Evasion logic inserted in `if saved:` + `SaveEffect.HALF` + `SaveType.REF` path (zero damage). Improved Evasion inserted in `else:` branch (failed save → half damage). Flat-footed AoO path (aoo.py) confirmed not present — no suppression to bypass for this WO.

**`tests/test_engine_evasion_gate.py`** — NEW
EV-01 through EV-10 all pass. Coverage includes: evasion on success, evasion no-op on fail, no-evasion half-damage regression, improved evasion both branches, non-REF save-type gate, NEGATES save_effect gate, chargen flag regression, non-evasion path regression.

**Open Finding:** FINDING-ENGINE-EVASION-ARMOR-001 (LOW, OPEN) — PHB p.56: rogue loses Evasion in medium/heavy armor. EF.EVASION is set at chargen and not cleared on armor equip. Deferred to post-equip-system WO.

## Pass 2 — PM Summary (≤100 words)

Evasion and Improved Evasion fully wired. Rogue 2/Monk 2 now receive EF.EVASION=True at chargen; Rogue 10/Monk 9 receive EF.IMPROVED_EVASION=True. spell_resolver._resolve_damage() now applies zero damage on successful Reflex save (half-damage spells) for evasion holders, and half damage on failed saves for improved evasion holders. Threading world_state+target_entity_id was required — anticipated by spec. 10/10 gate tests pass. One known gap logged: armor restriction deferred.

## Pass 3 — Retrospective

**Drift caught:** None — spec correctly predicted the threading requirement for target_entity in _resolve_damage(). Instruction "validate before writing; if not, thread it through" was precise.

**Patterns:** EF bool field + chargen grant pattern is clean and reusable. The SaveEffect.HALF + SaveType.REF double-gate is the correct PHB constraint.

**Open findings:**
| ID | Severity | Description |
|----|----------|-------------|
| FINDING-ENGINE-EVASION-ARMOR-001 | LOW | Armor restriction (PHB p.56 medium/heavy disables Evasion) not enforced; deferred to equip-system WO |

## Radar

- ENGINE-EVASION: 10/10 PASS
- Pre-existing failures unchanged (test_engine_gate_cleave, test_aoo_kernel ImportError)
- Zero new failures in full regression
- EF.EVASION and EF.IMPROVED_EVASION confirmed in entity_fields.py
- Chargen confirmed: Rogue 2 flag set, Rogue 1 no flag
