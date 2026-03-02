# DEBRIEF: BATCH-AW-ENGINE-001

**Lifecycle:** ACTIONED
**Commit:** 34f86d4 (NSP gate + coverage map) / MCB gate previously committed 786f583 (Batch AP)
**WOs:** WO-ENGINE-MANYSHOT-CONDITION-BLIND-001 (MCB-001..008), WO-ENGINE-NONLETHAL-SHADOW-PATH-001 (NSP-001..008)
**Gates:** 16/16 pass
**Suite:** 0 new regressions
**Verdict Review Class:** SELF-REVIEW (both WOs ghost targets — no code changed; gate tests verify existing correct state)

---

## Pass 1 — Context Dump

### WO1: WO-ENGINE-MANYSHOT-CONDITION-BLIND-001 — Ghost Target

**Ghost target status confirmed per Rule 15c.**

Grepping `attack_resolver.py` for `get_condition_modifiers` in `resolve_manyshot`:

```python
# attack_resolver.py:2445-2447
# Condition modifiers — PHB: all standard attack modifiers apply (WO-ENGINE-MANYSHOT-CONDITION-BLIND-001)
attacker_modifiers = get_condition_modifiers(world_state, intent.attacker_id, context="attack")
defender_modifiers = get_condition_modifiers(world_state, intent.target_id, context="defense")
```

Fix was already applied — the WO annotation comment in the code confirms it was done previously.

`resolve_manyshot` post-fix behavior (already present):
- `effective_bonus = base_attack_bonus + manyshot_penalty + attacker_modifiers.attack_modifier` (line 2452)
- `_ms_dex_penalty` applied when `defender_modifiers.loses_dex_to_ac` is True (lines 2462-2465)
- `_ms_condition_ac = defender_modifiers.ac_modifier_ranged` (lines 2466-2469)

**Gate file:** `tests/test_engine_manyshot_condition_blind_001_gate.py`
**Previously committed:** `786f583 engine(AP): DA reset SO-path + manyshot condition blind`

MCB test coverage:
- MCB-001: no conditions → `attack_bonus == bab - 4`
- MCB-002: shaken attacker → `attack_bonus == bab - 4 - 2`
- MCB-003: positive modifier via mock → `attack_bonus == bab - 4 + 2`
- MCB-004: flat-footed target → `target_ac == raw_ac - dex_mod`
- MCB-005: stunned target → `target_ac == raw_ac - 2 - dex_mod`
- MCB-006: compound canary (shaken attacker + flat-footed target)
- MCB-007: `resolve_attack` condition path unaffected (regression)
- MCB-008: no conditions → no spurious delta

All 8/8 pass.

---

### WO2: WO-ENGINE-NONLETHAL-SHADOW-PATH-001 — Ghost Target

**Ghost target status confirmed per Rule 15c.**

All three divergent paths already use canonical helpers with `WO-ENGINE-NONLETHAL-SHADOW-PATH-001` comments:

**Before (described in WO) vs After (already in code):**

`resolve_nonlethal_attack` lines 1435-1437 (condition modifiers — already present):
```python
# Get condition modifiers
attacker_modifiers = get_condition_modifiers(world_state, intent.attacker_id, context="attack")
defender_modifiers = get_condition_modifiers(world_state, intent.target_id, context="defense")
```

`resolve_nonlethal_attack` line 1467 (Weapon Finesse — already uses canonical helper):
```python
_nl_finesse_delta = _compute_finesse_delta(attacker, intent.weapon)  # WO-ENGINE-NONLETHAL-SHADOW-PATH-001
```

`resolve_nonlethal_attack` line 1472 (Improved Critical — already uses canonical helper):
```python
_nl_ic_eff_range = _compute_effective_crit_range(intent.weapon, _nl_attacker_feats)  # WO-ENGINE-NONLETHAL-SHADOW-PATH-001
```

**Approach:** No refactor required (ghost target). Gate tests written to verify existing correct state.

**Gate file:** `tests/test_engine_nonlethal_shadow_path_001_gate.py` (new, this batch)
**Committed:** `34f86d4 engine(AW)`

NSP test coverage:
- NSP-001: no conditions → `attack_roll.nonlethal==True` + `nonlethal_damage` event on hit
- NSP-002: shaken attacker → `condition_modifier==-2` in `attack_roll` payload
- NSP-003: flat-footed target → `target_ac == base_ac - dex_mod`
- NSP-004: Weapon Finesse → attack total reflects DEX bonus via `_compute_finesse_delta`
- NSP-005: Improved Critical → crit range doubled via `_compute_effective_crit_range` (rapier 18→15)
- NSP-006: `-4` nonlethal penalty in `attack_roll.nonlethal_penalty`
- NSP-007: nonlethal >= hp → `threshold_crossed` set + `condition_applied` staggered/unconscious
- NSP-008: regression — `resolve_attack()` shaken `condition_modifier==-2` unchanged

All 8/8 pass.

---

## PM Acceptance Notes Responses

### WO1 (MCB):

**Show `resolve_manyshot` before (raw EF.ATTACK_BONUS/EF.AC) and after (get_condition_modifiers applied):**
Ghost target — no before state exists. The fix was already applied with annotation comment at lines 2445-2447. No "before" in current codebase.

**Confirm pattern matches `resolve_attack()` canonical path:**
`resolve_attack()` lines 434-436:
```python
attacker_modifiers = get_condition_modifiers(world_state, intent.attacker_id, context="attack")
defender_modifiers = get_condition_modifiers(world_state, intent.target_id, context="defense")
```
`resolve_manyshot()` lines 2446-2447: identical pattern, same arguments, same context strings. Match confirmed.

**MCB-002 result: shaken attacker — attack_bonus value in event:**
`attack_bonus = bab(6) + manyshot_penalty(-4) + shaken_modifier(-2) = 0`. MCB-002 passes.

**Confirm `resolve_nonlethal_attack` NOT modified:**
Confirmed. Only `test_engine_nonlethal_shadow_path_001_gate.py` created for WO2. No changes to `resolve_nonlethal_attack` source.

**Confirm `resolve_attack()` unchanged:**
MCB-007 regression gate passes: `resolve_attack` with shaken attacker returns `condition_modifier==-2`.

---

### WO2 (NSP):

**Approach taken: Parity confirmed (ghost target — no code change needed):**
Full delegation was the preferred approach, but the code already uses canonical helpers at both divergent points. The shadow path was already eliminated. No refactor or parity patch needed.

**Before/after of divergent lines:**
Ghost target — no before state in current codebase. All three divergent points already show post-fix state with `WO-ENGINE-NONLETHAL-SHADOW-PATH-001` comments.

**`get_condition_modifiers()` now called for both attacker and target:**
Confirmed at lines 1436-1437. `attacker_modifiers.attack_modifier` used at line 1468. `defender_modifiers.loses_dex_to_ac` used at line 1444.

**NSP-002 result: shaken attacker → confirm –2 applied:**
`condition_modifier==-2` confirmed in `attack_roll` payload. NSP-002 passes.

**NSP-006: –4 penalty still present post-refactor:**
`NONLETHAL_ATTACK_PENALTY = -4` at line 1397. Applied at line 1433: `adjusted_attack_bonus = intent.attack_bonus + NONLETHAL_ATTACK_PENALTY`. In `attack_roll` payload: `nonlethal_penalty=-4`. NSP-006 passes.

---

## Pass 2 — PM Summary (100 words)

Both WOs ghost targets. WO1: `get_condition_modifiers()` already at `attack_resolver.py:2446-2447` with WO annotation comment; MCB gate file previously committed in Batch AP (`786f583`). 8/8 MCB gates pass. WO2: condition modifiers at lines 1436-1437; `_compute_finesse_delta()` at 1467; `_compute_effective_crit_range()` at 1472 — all with WO-ENGINE-NONLETHAL-SHADOW-PATH-001 comments. NSP gate file newly created this batch (`34f86d4`). NSP-002 confirms shaken –2 applied; NSP-006 confirms –4 NL penalty preserved; NSP-007 confirms staggered/unconscious threshold fires. 16/16 gates pass. 0 new regressions. Sweep 3/5.

---

## Pass 3 — Retrospective

**Ghost target process note:**
- Both WOs were complete ghost targets per Rule 15c.
- WO1: MCB gate file was committed in Batch AP (the fix was done during the AP session under a different finding ID/batch). The annotation comment `# WO-ENGINE-MANYSHOT-CONDITION-BLIND-001` was already in the code.
- WO2: NSP fix was applied in Batch AQ (NSP helper extraction commit `08f61e9`). The annotation comments `# WO-ENGINE-NONLETHAL-SHADOW-PATH-001` confirm this.
- Both WOs closed as ghost targets — no code changes made in Batch AW.

**Out-of-scope findings:**
- None identified. No new findings during gate writing.

**Kernel touches:**
- This WO touches KERNEL-01 (Combat Core) — manyshot and nonlethal attack resolution paths verified. Condition modifier wiring confirmed end-to-end via gate tests.

---

## Radar — Findings

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| FINDING-ENGINE-MANYSHOT-CONDITION-BLIND-001 | resolve_manyshot silently skipped condition modifiers | MEDIUM | CLOSED (ghost target — pre-applied in Batch AP) |
| FINDING-ENGINE-NONLETHAL-SHADOW-PATH-001 | resolve_nonlethal_attack shadow-duplicated WF + ImprCrit | MEDIUM | CLOSED (ghost target — pre-applied in Batch AQ) |

---

## Coverage Map Updates

**Updated rows (`docs/ENGINE_COVERAGE_MAP.md`):**
- Manyshot row (line 299): Updated batch reference to AW; ghost target note added.
- Nonlethal attack row (line 68): NSP-001..008 Batch AW gate reference added; ghost target note.

---

## ML Preflight Checklist

| Check | WO1 (MCB) | WO2 (NSP) |
|-------|-----------|-----------|
| ML-001: No bare string literals (EF.* used) | Ghost target — no code written | Ghost target — no code written |
| ML-002: All call sites identified | resolve_manyshot single entry (confirmed); resolve_attack unchanged | resolve_nonlethal_attack single entry; canonical path unchanged |
| ML-003: No float in deterministic path | N/A | N/A |
| ML-004: json.dumps sort_keys if any | N/A | N/A |
| ML-005: No WorldState mutation in resolver | N/A — no code written | N/A — no code written |
| ML-006: Coverage map updated | ✅ Manyshot row updated | ✅ Nonlethal row updated |

---

## Consume-Site Confirmation

**WO1 (MCB) — Ghost Target:**
- Write site: `attack_resolver.py:2446-2447` — `get_condition_modifiers()` called for attacker (context="attack") and target (context="defense")
- Read site: `attack_resolver.py:2452` — `attacker_modifiers.attack_modifier` applied to `effective_bonus`
- Read site 2: `attack_resolver.py:2462-2470` — `defender_modifiers.loses_dex_to_ac` + `ac_modifier_ranged` applied to `target_ac`
- Effect: Shaken manyshot attacker suffers –2 to attack; flat-footed target loses DEX bonus to AC
- Gate proof: MCB-002 (shaken –2), MCB-004 (flat-footed AC drops), MCB-006 (compound canary)

**WO2 (NSP) — Ghost Target:**
- Write site 1: `attack_resolver.py:1436-1437` — `get_condition_modifiers()` for attacker + target
- Write site 2: `attack_resolver.py:1467` — `_compute_finesse_delta()` canonical helper
- Write site 3: `attack_resolver.py:1472` — `_compute_effective_crit_range()` canonical helper
- Read site: `attack_resolver.py:1468` — `attack_bonus_with_conditions` combines adjusted bonus + condition modifier + finesse delta
- Effect: Nonlethal attacks respect all condition modifiers; WF + ImprCrit stay in sync with canonical path
- Gate proof: NSP-002 (shaken –2), NSP-004 (WF finesse), NSP-005 (ImprCrit range), NSP-007 (threshold)

**Post-AW gate count:** 1,678 (post-AV) + 8 (MCB, already in count via AP commit) + 8 (NSP new) = **1,686**
**Note:** MCB-001..008 were committed in Batch AP and already included in the 1,678 count. Net new gates this batch: 8 (NSP).
**Sweep:** 3/5.
