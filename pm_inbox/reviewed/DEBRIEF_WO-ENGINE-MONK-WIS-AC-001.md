# DEBRIEF — WO-ENGINE-MONK-WIS-AC-001

**Verdict:** PASS [8/8]
**Gate:** ENGINE-MONK-WIS-AC
**Date:** 2026-02-26

## Pass 1 — Per-File Breakdown

**Chargen verification (MANDATORY per spec):**
`_assign_starting_equipment()` confirmed: `EF.AC` at chargen = `10 + dex_mod + armor_bonus + wis_mod` (line 236: `ac += wis_mod`). **WIS was baked in.** Branch B taken: WIS removed from `EF.AC` formula; `EF.MONK_WIS_AC_BONUS` set at chargen; attack_resolver adds it at runtime. Net result: `EF.AC` = `10 + DEX + armor` only at chargen.

**`aidm/schemas/entity_fields.py`**
Added four new constants: `MONK_WIS_AC_BONUS`, `ARMOR_AC_BONUS`, `ARMOR_TYPE`, `FAST_MOVEMENT_BONUS` (lines 291-308). Neither `ARMOR_AC_BONUS` nor `ARMOR_TYPE` existed previously — both added as prerequisites for this WO and the Barbarian Fast Movement WO respectively.

**`aidm/chargen/builder.py`**
`_assign_starting_equipment()`: captures `armor_type_str` from catalog, sets `EF.ARMOR_AC_BONUS`, `EF.ARMOR_TYPE`, and `EF.MONK_WIS_AC_BONUS` (WIS mod for monks, 0 for non-monks). Single-class and multiclass pool init paths both updated.

**`aidm/core/attack_resolver.py`**
Monk WIS AC logic added to both standard attack path (line 425-433) and nonlethal attack path (line 942-948). Armor gate: `ARMOR_AC_BONUS == 0` correctly suppresses bonus when armor is worn. Touch AC: no separate touch AC path exists in the engine. WIS is an untyped AC bonus (not armor), so it survives touch attacks by definition — applying it in the main path is architecturally correct per PHB p.41.

**`tests/test_engine_monk_wis_ac_001_gate.py`** — NEW
MW-001 through MW-008 all pass. Coverage: WIS +3 applied when unarmored (MW-001), WIS 0 no change (MW-002), armored monk suppressed (MW-003), non-monk not affected (MW-004), touch attack coverage (MW-005), runtime WIS change (MW-006), chargen flag (MW-007), multiclass (MW-008).

**Open Finding:** Encumbrance-based WIS stripping deferred — heavy load should also suppress Monk WIS AC per PHB p.41. No catalog available in attack_resolver hot path. Documented in code comment.

## Pass 2 — PM Summary (≤100 words)

Monk WIS-to-AC fully wired at runtime. Critical chargen finding: WIS was already baked into `EF.AC` — Branch B taken, WIS removed from base AC at chargen, tracked separately in `EF.MONK_WIS_AC_BONUS`, applied dynamically in attack_resolver. Four new EF constants added: `MONK_WIS_AC_BONUS`, `ARMOR_AC_BONUS`, `ARMOR_TYPE`, `FAST_MOVEMENT_BONUS`. No separate touch AC path found — WIS bonus in main path correctly handles PHB p.41 touch attack coverage. 8/8 gate pass.

## Pass 3 — Retrospective

**Drift caught:** The spec's mandatory pre-flight instruction ("Read `builder.py:_assign_starting_equipment()` before writing a single line") was critical — the branch decision (WIS baked in or not) could not have been made correctly without it. The spec was right to make this mandatory and flag it explicitly.

**Patterns:** The four new EF constants added here (`ARMOR_AC_BONUS`, `ARMOR_TYPE`) will immediately benefit future WOs (armor restriction enforcement for Evasion, Barbarian Fast Movement). Shared infrastructure established in one pass.

**Open findings:**
| ID | Severity | Description |
|----|----------|-------------|
| FINDING-ENGINE-MONK-ENCUMBRANCE-001 | LOW | Heavy load should suppress Monk WIS AC per PHB p.41; encumbrance catalog not available in attack_resolver hot path; deferred |

## Radar

- ENGINE-MONK-WIS-AC: 8/8 PASS
- Chargen branch: WIS WAS baked into EF.AC — Branch B implemented correctly
- EF.ARMOR_AC_BONUS and EF.ARMOR_TYPE now exist (new — enables future armor restriction WOs)
- Touch AC: no separate path; WIS in main path is architecturally correct
- FINDING-ENGINE-MONK-ENCUMBRANCE-001: LOW, OPEN
- Zero new failures in full regression
