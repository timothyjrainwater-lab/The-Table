**Lifecycle:** ACTIONED

# DEBRIEF — ENGINE BATCH Q (WO1–WO4)

**Date:** 2026-02-27
**Commits:** `1a0b128` (WO1) · `5b41a2f` (WO2) · `d0e4ef2` (WO3) · `056e525` (WO4)
**Gates:** 33/33 PASS (9 GC + 8 IUD + 8 WFC + 8 WSP)
**Regressions:** 0 (all 142 pre-existing failures are in `test_ui_*` — no engine regressions)

---

## Pass 1: Context Dump

### WO1 — ENGINE-GREAT-CLEAVE (SAI)

**Files changed:** `tests/test_engine_great_cleave_gate.py` (created)
**Production changes:** NONE — SAI confirmed

**SAI Evidence:**
- `attack_resolver.py:995–1042`: `can_use_cleave()` → `get_cleave_limit()` → `_cl_limit is None or not _cl_already` check
- `full_attack_resolver.py:804–850`: identical pattern
- `get_cleave_limit()` (feat_resolver.py): returns `None` for `FeatID.GREAT_CLEAVE` → `None or not X` = True (always fires)
- `cleave_used_this_turn` flag only set when `_cl_limit == 1` (Cleave, not GC)

**Per-round limit confirmation:** Flag exists (`active_combat["cleave_used_this_turn"]`). GC bypasses it because `_cl_limit is None` short-circuits the `not _already_cleaved` check. Cleave sets the flag. GC does not.

**Adjacency guard confirmed:** `_find_cleave_target()` uses 8-directional adjacency (`|Δx|≤1 AND |Δy|≤1`) on the KILLED target's position — GC inherits this (same call path).

**GC-003 redesign:** Original chain-kill test hit a circular adjacency problem — `resolve_attack()` does not mutate WorldState HP, so "killed" targets remain at original HP and get re-selected. Redesigned GC-003 to verify the flag behavior directly (GC does not set `cleave_used_this_turn`) rather than testing chain kills. Added bonus test GC-003b verifying regular Cleave DOES set the flag. This is architecturally correct — chain kill behavior would require `apply_attack_events()` between attacks, which is outside the resolver's scope.

**Gate file:** `tests/test_engine_great_cleave_gate.py` — 9 tests (GC-001 through GC-008 + GC-003b)

---

### WO2 — ENGINE-IMPROVED-UNCANNY-DODGE (new implementation)

**Files changed:**
- `aidm/core/attack_resolver.py`: IUD guard inserted at `resolve_attack()`, line ~850 (inside `if hit:` block, after `damage_total += _favored_enemy_bonus`, before `calculate_sneak_attack()`)
- `aidm/core/full_attack_resolver.py`: IUD guard inserted at `resolve_full_attack()`, line ~624 (after `get_flanking_info()`, before `is_sneak_attack_eligible()`)

**Before (attack_resolver.py):**
```python
# [SA eligible check with is_flanking=is_flanking]
```

**After (attack_resolver.py):**
```python
# WO-ENGINE-IMPROVED-UNCANNY-DODGE-001: IUD suppresses flanking-based sneak attack (PHB p.26/50)
_sa_is_flanking = is_flanking
if is_flanking and "improved_uncanny_dodge" in target.get(EF.FEATS, []):
    _attacker_rogue = attacker.get(EF.CLASS_LEVELS, {}).get("rogue", 0)
    _target_iud_base = (
        target.get(EF.CLASS_LEVELS, {}).get("rogue", 0)
        + target.get(EF.CLASS_LEVELS, {}).get("barbarian", 0)
    )
    if _attacker_rogue < _target_iud_base + 4:
        events.append(Event(..., event_type="improved_uncanny_dodge_active", ...))
        current_event_id += 1
        _sa_is_flanking = False
# [SA eligible check now uses is_flanking=_sa_is_flanking]
```

**full_attack_resolver.py:** Identical IUD guard but no event emitted (FAR suppresses `_sa_is_flanking` only — event emitted in attack_resolver.py path to avoid double-emission for full attack sequences).

**Key design decisions:**
- `is_flanking` preserved for attack roll audit trail — flanking attack bonus (+2) is NOT removed by IUD
- Only `_sa_is_flanking` is suppressed, passed to `is_sneak_attack_eligible(..., is_flanking=_sa_is_flanking)`
- Rogue-level formula: `attacker_rogue < target_iud_base + 4` where `target_iud_base = target.rogue + target.barbarian`
- Uncanny Dodge flat-footed sites (`attack_resolver.py:388` and `:924`) are UNTOUCHED — IUD only guards the flanking path

**IUD-007 fix:** Original test used `create_flat_footed_condition()` which doesn't exist in the codebase. Rewrote to test the semantic directly: when no ally present → no flanking → IUD guard never fires → no `improved_uncanny_dodge_active` event.

**Closes:** FINDING-ENGINE-IMPROVED-UNCANNY-DODGE-001 (deferred from Batch C WO4)

**Gate file:** `tests/test_engine_improved_uncanny_dodge_gate.py` — 8 tests (IUD-001 through IUD-008)

---

### WO3 — ENGINE-WEAPON-FOCUS (new implementation)

**Files changed:**
- `aidm/core/attack_resolver.py`: `_wf_bonus` computed after `_attacker_feats` line, added to `attack_bonus_with_conditions`; `weapon_focus_active` event emitted when bonus applies
- `aidm/core/full_attack_resolver.py`: `_wf_bonus` computed after rapid-shot block, added to `adjusted_attack_bonus` in per-iterative loop

**attack_resolver.py insertion (line ~639, before `attack_bonus_with_conditions`):**
```python
# WO-ENGINE-WEAPON-FOCUS-001: Weapon Focus +1 attack bonus (PHB p.102)
_wf_bonus = 1 if f"weapon_focus_{intent.weapon.weapon_type}" in _attacker_feats else 0
if _wf_bonus:
    events.append(Event(event_type="weapon_focus_active", ...))
    current_event_id += 1
# + _wf_bonus added to attack_bonus_with_conditions
```

**full_attack_resolver.py insertion (line ~695, after rapid-shot, before full_attack_start):**
```python
_wf_bonus = 1 if f"weapon_focus_{intent.weapon.weapon_type}" in _attacker_feats else 0
# + _wf_bonus added to adjusted_attack_bonus in iterative loop
```

**Weapon type key pattern (simplification from PHB):** PHB assigns WF per specific weapon (e.g., "longsword"). Engine uses categorical `weapon_type` (`light`, `one-handed`, `two-handed`, `ranged`, `natural`). This is an intentional engine simplification — documented in dispatch spec (Intelligence Update). Gate tests use this pattern.

**Natural attack path:** `natural_attack_resolver.py` delegates to `resolve_attack()` in `attack_resolver.py`. WF bonus inherited automatically — no separate touch needed.

**WF abbreviation collision avoidance:** WF = Weapon Finesse (Batch B R1, 8/8 ACCEPTED). This WO uses WFC abbreviation throughout to avoid confusion.

**Note on commit scope:** The WO4 (WSP) production code changes to `attack_resolver.py` and `full_attack_resolver.py` were staged during WO3 development and committed with the WO3 commit (`d0e4ef2`). The WO4 commit (`056e525`) contains only the test file. This is a staging artifact — functionally all WSP tests pass against the correct implementation. Noted here for traceability.

**Gate file:** `tests/test_engine_weapon_focus_gate.py` — 8 tests (WFC-001 through WFC-008)

---

### WO4 — ENGINE-WEAPON-SPECIALIZATION (new implementation)

**Files changed:**
- `aidm/core/attack_resolver.py`: `_wsp_bonus` computed and applied to `base_damage` (pre-crit)
- `aidm/core/full_attack_resolver.py`: `_wsp_bonus` computed and applied inside `resolve_single_attack_with_critical()` — same pre-crit site as enhancement bonus

**attack_resolver.py insertion (line ~832, at `base_damage` computation):**
```python
base_damage = sum(damage_rolls) + intent.weapon.damage_bonus + str_to_damage + intent.weapon.enhancement_bonus
# WO-ENGINE-WEAPON-SPECIALIZATION-001: Weapon Specialization +2 damage bonus (PHB p.102)
_wsp_bonus = 2 if f"weapon_specialization_{intent.weapon.weapon_type}" in _attacker_feats else 0
base_damage += _wsp_bonus
```

**full_attack_resolver.py insertion (inside `resolve_single_attack_with_critical()`, after `base_damage` line):**
```python
_ic_wsp = attacker_feats if attacker_feats is not None else []
_wsp_bonus = 2 if f"weapon_specialization_{getattr(weapon, 'weapon_type', '')}" in _ic_wsp else 0
base_damage += _wsp_bonus
```

**Crit multiplication confirmed:** WSP +2 is pre-crit. On a ×2 crit, the delta is +4 (WSP-004 confirms this). Same multiplication behavior as enhancement bonus and STR mod (PHB p.224: "Roll the damage with all your usual bonuses one extra time").

**Dispatch doc clarification:** Dispatch said "WO4 touches only `attack_resolver.py`." Incorrect — `full_attack_resolver.py` requires a separate touch because `resolve_single_attack_with_critical()` is the damage path for full attacks. The WSP bonus would be absent from all iterative attacks without this. Confirmed by WSP-003 (full attack test).

**WSP+WFC stacking confirmed:** WSP-005 verifies +1 attack AND +2 damage apply simultaneously with no interference. WSP-008 is a regression guard confirming WO3 (WFC) is unaffected.

**Gate file:** `tests/test_engine_weapon_specialization_gate.py` — 8 tests (WSP-001 through WSP-008)

---

## Pass 2: PM Summary

Batch Q completes. WO1 (Great Cleave) SAI — 9 gate tests validate existing behavior. WO2 (IUD) implements flanking SA suppression in both resolvers with rogue-level exception; flat-footed SA unaffected; `improved_uncanny_dodge_active` event emitted. WO3 (Weapon Focus) wires `weapon_focus_{type}` +1 attack in both resolvers with event emission; natural attacks inherit automatically. WO4 (Weapon Specialization) wires `weapon_specialization_{type}` +2 damage pre-crit in both resolvers; crit multiplication verified. 33/33 gates, zero engine regressions. One staging artifact: WSP production code committed in WO3 commit — traceability note in Pass 1.

---

## Pass 3: Retrospective

**Out-of-scope findings:**

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| FINDING-ENGINE-GC-CHAIN-HP-MUTATION-001 | LOW | OPEN | Great Cleave chain kills untestable without `apply_attack_events()` between attacks. Chain kill test must be an integration test (not unit gate). Pre-existing architectural constraint. |
| FINDING-ENGINE-WF-SPECIFIC-WEAPON-001 | LOW | OPEN | Weapon Focus keyed on `weapon_type` category, not specific weapon name (simplification from PHB). Fighter speccing `weapon_focus_one-handed` gains WF vs ALL one-handed weapons. Out-of-scope for Batch Q. |
| FINDING-ENGINE-WSP-DISPATCH-FILE-LIST-001 | INFO | CLOSED | Dispatch doc listed WO4 as touching only `attack_resolver.py`. Actually required `full_attack_resolver.py` touch for full-attack parity. Not a defect — dispatch doc was a planning estimate. |
| FINDING-ENGINE-WFC-NATURAL-ATTACK-INHERIT-001 | INFO | CLOSED | Natural attack path confirmed to inherit WF bonus via delegation to `resolve_attack()` — no `natural_attack_resolver.py` touch needed. |

**Kernel touches:**
- This WO touches KERNEL-01 (attack pipeline) — IUD suppression added to `_sa_is_flanking` pattern; WF/WSP bonuses added to `attack_bonus_with_conditions` and `adjusted_attack_bonus`. Future WOs touching these computations must account for these new fields.
- This WO touches KERNEL-05 (damage computation) — `base_damage` now includes WSP bonus at pre-crit site.

**Radar:**
- `create_flat_footed_condition` does not exist in `aidm/core/conditions.py`. Referenced in dispatch spec. If flat-footed condition factory is needed for future gate tests, it must be added. LOW deferred.
- WSP staging artifact (see Pass 1) — no functional impact but commit log attribution is impure.
