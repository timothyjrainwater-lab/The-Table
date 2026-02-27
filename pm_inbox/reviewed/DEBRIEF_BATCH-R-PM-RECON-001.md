# DEBRIEF: Batch R Pre-Dispatch PM Reconnaissance

**From:** Slate (PM)
**To:** Thunder (PO)
**Date:** 2026-02-27
**Lifecycle:** ARCHIVE
**Scope:** Pre-dispatch triage + source audit for WO_SET_ENGINE_BATCH_R.md
**Result:** 3/4 WOs found SAI or implementation-incorrect in draft; dispatch corrected before builder send

---

## Pass 1 — Full Context Dump

### Session Objective

Thunder submitted four WO candidates for Batch R (IE, MB, SP, GTWF). A draft `WO_SET_ENGINE_BATCH_R.md` was found in pm_inbox already. PM performed source file reconnaissance before accepting the draft as-is.

---

### WO1 — WO-ENGINE-IMPROVED-EVASION-001

**File audited:** `aidm/core/spell_resolver.py:895-953`

**Finding: HIGH SAI RISK — both branches already wired.**

Lines 914-916 (save pass → 0 damage):
```python
_evasion_active = _armor in ("none", "light")
if _evasion_active and (_target_raw.get(EF.EVASION, False) or _target_raw.get(EF.IMPROVED_EVASION, False)):
    total = 0
```

Lines 921-927 (save fail → half damage):
```python
if spell.save_type == SaveType.REF and spell.save_effect == SaveEffect.HALF:
    if world_state is not None and target_entity_id is not None:
        _target_raw = world_state.entities.get(target_entity_id, {})
        _armor = _target_raw.get(EF.ARMOR_TYPE, "none")
        if _armor in ("none", "light") and _target_raw.get(EF.IMPROVED_EVASION, False):
            total = total // 2
```

Both the pass-path (→0) and fail-path (→half) are present and gated on `EF.IMPROVED_EVASION` field. Armor check correct (`"none"` or `"light"` only). The field is read directly — chargen must write it. If chargen does not set `EF.IMPROVED_EVASION = True` for eligible classes, that is the only production gap.

**Dispatch correction made:** Assumptions to Validate updated with SAI-first check and specific line numbers. Implementation section rewritten to show SAI path (zero spell_resolver.py changes; chargen write is only candidate action).

---

### WO2 — WO-ENGINE-MOBILITY-001

**Files audited:** `aidm/core/feat_resolver.py:255-294`, `aidm/core/aoo.py:596-624`

**Finding: WRONG IMPLEMENTATION IN DRAFT — dispatch described TEMPORARY_MODIFIERS approach which is not the actual implementation.**

`feat_resolver.py:262-268` computes +4:
```python
if FeatID.MOBILITY in feats:
    is_aoo = context.get("is_aoo", False)
    aoo_trigger = context.get("aoo_trigger", "")
    if is_aoo and aoo_trigger in ("movement_out", "mounted_movement_out"):
        modifier += 4
```

`aoo.py:615-624` applies via deepcopy:
```python
if feat_ac_modifier != 0:
    from copy import deepcopy
    temp_entities = deepcopy(world_state.entities)
    temp_entities[trigger.provoker_id][EF.AC] = temp_entities[trigger.provoker_id].get(EF.AC, 10) + feat_ac_modifier
    world_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=temp_entities,
        active_combat=world_state.active_combat
    )
```

Wiring is complete. The deepcopy approach mutates `EF.AC` on a copy of world_state so the modified AC reaches `resolve_attack()` without touching `attack_resolver.py`. No TEMPORARY_MODIFIERS involvement.

**Also found:** Stale TODO comment at `aoo.py:609-613` ("Current limitation: attack_resolver doesn't accept context-specific AC modifiers") predates the deepcopy workaround below it. Added cleanup of this TODO as a deliverable for WO2.

**BLOCKED condition in draft was wrong.** Draft said WO2 was blocked pending `attack_resolver.py` refactor. This assumption was based on the stale TODO, not the actual implementation. Removed BLOCKED condition.

**Dispatch correction made:** Full WO2 implementation section replaced. TEMPORARY_MODIFIERS set/clear pattern removed. "No production code changes expected; stale TODO cleanup is the only deliverable" is now the WO2 implementation spec. Gate tests updated to verify deepcopy path delivers +4 (not TEMPORARY_MODIFIERS lifecycle behavior).

---

### WO3 — WO-ENGINE-AOO-STANDING-PRONE-001

**Files audited:** `aidm/core/aoo.py:709-817`, gate file search

**Finding: FULL SAI — mechanic implemented and gated in Batch I.**

`check_stand_from_prone_aoo()` is fully implemented at `aoo.py:709-817`:
- Line 737: `if "prone" not in actor_conditions: return []`
- Line 755-796: Full reactor loop (AoO-limit-aware, Combat Reflexes aware)
- Line 779: Flat-footed reactor guard: `if "flat_footed" in _reactor_conditions: continue`
- Returns `AooTrigger` list for `"stand_from_prone"` provoking action

Gate file `tests/test_engine_aoo_stand_from_prone_001_gate.py` exists (Batch I, WO-ENGINE-AOO-STAND-FROM-PRONE-001). AP 8/8 in briefing gate table.

**FINDING-CE-STANDING-AOO-001 resolution confirmed:** The finding tracks "flat-footed AoO suppression for standing entities." The guard is at `aoo.py:779` inside `check_stand_from_prone_aoo()`. Finding can be CLOSED by WO3 builder debrief Pass 3.

**Draft had 8 new gate tests (SP-001–SP-008) and a new gate file.** Draft gate filename `test_engine_aoo_standing_prone_gate.py` would have duplicated the existing Batch I gate under a different name. Corrected before dispatch.

**Dispatch correction made:** Entire WO3 replaced with SAI-only content. Zero production changes, zero new gate tests. Builder confirms existing implementation + runs existing gate. Debrief closes FINDING-CE-STANDING-AOO-001.

---

### WO4 — WO-ENGINE-GREATER-TWF-001

**File audited:** `aidm/core/full_attack_resolver.py:895-952`

**Finding: NEW WORK CONFIRMED — but feat key discrepancy found in draft.**

ITWF block confirmed at line 902: `if "Improved Two-Weapon Fighting" in feats and current_hp > 0:` — Title Case with hyphens.

TWF at line 219: `has_twf = "Two-Weapon Fighting" in feats` — same Title Case pattern.

Draft used `"greater_two_weapon_fighting"` (lowercase underscore). This would silently fail — feat would never match. Corrected to `"Greater Two-Weapon Fighting"` in dispatch, with boot-time verification instruction.

No GTWF block anywhere in `full_attack_resolver.py`. Confirmed genuine new work.

ITWF block BAB formula: `itwf_bab = intent.base_attack_bonus - 5 + off_penalty`. GTWF follows same pattern with `-10`. Full `resolve_single_attack_with_critical()` call block provided verbatim in dispatch.

**Dispatch correction made:** Assumptions to Validate updated with feat key verification step. Implementation block replaced: ITWF pattern mirrored exactly, lowercase key corrected to Title Case, `-10` offset confirmed.

---

### Open Findings Table

| ID | Severity | Status | Notes |
|----|----------|--------|-------|
| FINDING-CE-STANDING-AOO-001 | LOW | CLOSING in Batch R WO3 debrief | Flat-footed guard at aoo.py:779 confirmed |

No new findings generated this session.

---

### Gate Count Summary

| WO | Tests | Type |
|----|-------|------|
| WO1 IE | 8 new | Gate validates existing behavior |
| WO2 MB | 8 new | Gate validates deepcopy wiring |
| WO3 SP | existing gate only | SAI — run and confirm |
| WO4 GTWF | 8 new | New work |
| **Total new** | **24** | — |

---

## Pass 2 — PM Summary

3/4 WOs were SAI or had wrong implementation assumptions in the draft. IE: both evasion branches already wired at `spell_resolver.py:914-927`. SP: fully implemented and gated in Batch I — draft would have created a duplicate gate file. MB: deepcopy approach is the actual wiring, not TEMPORARY_MODIFIERS; BLOCKED condition removed. GTWF: genuine new work, but draft feat key was wrong casing (silent failure). All corrected before dispatch. FINDING-CE-STANDING-AOO-001 primed to close on WO3 debrief.

---

## Pass 3 — Retrospective

### Pre-dispatch recon caught 3/4 wrong assumptions

ML-003 validated again: coverage audits and draft dispatches inherit the confidence of their author at time of writing, not the codebase's actual state. Mobility was blocked on a stale TODO comment that predated the workaround implemented below it. AOO-STANDING-PRONE was treated as new work despite a gate file existing under a slightly different filename. The reconnaissance step cost one session vs. a builder spending context window budget reimplementing working code.

### Stale TODO comments are hazard markers

`aoo.py:609-613` had a TODO that said the workaround was insufficient and `attack_resolver.py` needed touching. The workaround directly below it was complete. A builder reading the TODO without the context of the deepcopy implementation would conclude the task was blocked. Cleanup of stale TODO comments should be a standard deliverable when reconnaisance identifies them.

### Filename near-duplicates are a gate poisoning risk

`test_engine_aoo_stand_from_prone_001_gate.py` vs `test_engine_aoo_standing_prone_gate.py` — one character difference in the middle of the name. If the draft had shipped and a builder created the second file, both would run, both might pass, and the briefing gate table would carry two entries for the same mechanic. Naming discipline on gate files matters.

### Feat key casing convention must be in every TWF WO

TWF chain uses Title Case with hyphens. Anyone generating a GTWF WO from a coverage audit without reading the actual ITWF feat string will write lowercase. This should be noted in the briefing as a standing pattern note, not just caught per-WO.

**Radar:** YELLOW. Batch R in-flight with corrected dispatch. Three wrong assumptions caught pre-builder — no code damage. Environment disruption (VS Code → Cursor migration) caused flat context boot this session; full three-layer rehydration not completed. Process discipline partially degraded. Boot protocol needs re-establishing before next PM session.

---

*Debrief filed by Slate. Batch R dispatched (commit 17b6d93). Awaiting Chisel builder debriefs.*
