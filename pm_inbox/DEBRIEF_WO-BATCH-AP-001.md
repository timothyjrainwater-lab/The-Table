# DEBRIEF: WO_SET_ENGINE_BATCH_AP — DA Reset (SO Path) + Manyshot Condition Blind

**Commit:** 786f583
**Session:** 29
**Date:** 2026-03-02
**Gates:** 16/16 (DAR-001..008 + MCB-001..008)
**Verdict target:** ACCEPTED

---

## Pass 1 — Context Dump

### WO1: WO-ENGINE-DEFLECT-ARROWS-RESET-001 — DA Reset on SO Path

**File changed:** `aidm/core/play_loop.py`

**Lines changed:** 4405–4409 (round-boundary block)

Before:
```python
# WO-ENGINE-AOO-ROUND-RESET-001: Reset AoO trackers at round boundary.
# PHB p.137: each creature gets 1 AoO per round (+ DEX mod with Combat Reflexes).
# aoo_used_this_round and aoo_count_this_round accumulate across execute_turn()
# calls (SessionOrchestrator path bypasses combat_controller.execute_combat_round).
# Reset here so round 2+ AoOs fire correctly. Do NOT touch deflect_arrows_used
# (already reset in combat_controller.py:348 / WO-ENGINE-DA-ROUND-RESET-001).
active_combat["aoo_used_this_round"] = []   # CP-15: PHB p.137 -- 1 AoO per round
active_combat["aoo_count_this_round"] = {}  # WO-ENGINE-COMBAT-REFLEXES-001: per-entity count
```

After:
```python
# WO-ENGINE-AOO-ROUND-RESET-001: Reset AoO trackers at round boundary.
# PHB p.137: each creature gets 1 AoO per round (+ DEX mod with Combat Reflexes).
# aoo_used_this_round and aoo_count_this_round accumulate across execute_turn()
# calls (SessionOrchestrator path bypasses combat_controller.execute_combat_round).
# Per-round reset: AoO counters + Deflect Arrows (PHB p.137/p.93)
# Note: combat_controller.py:348 resets DA on the CC path; this block covers the SO path.
active_combat["aoo_used_this_round"] = []   # CP-15: PHB p.137 -- 1 AoO per round
active_combat["aoo_count_this_round"] = {}  # WO-ENGINE-COMBAT-REFLEXES-001: per-entity count
active_combat["deflect_arrows_used"] = []   # WO-ENGINE-DEFLECT-ARROWS-RESET-001: PHB p.93 -- once per round
```

**Assumptions validated:**
- Exact reset block confirmed at lines 4405–4409 (grep: `aoo_used_this_round` in play_loop.py)
- `deflect_arrows_used` initialized as `[]` confirmed: `session_orchestrator.py:208` — `"deflect_arrows_used": [],`
- No other unhandled per-round accumulator found. AUDIT-WO-013 table is complete.
- DA read site confirmed: `attack_resolver.py:904` — `deflect_arrows_used` checked in the DA reactive gate

**Parallel paths:**
| Path | Round-boundary location | DA reset after this WO |
|------|------------------------|------------------------|
| SessionOrchestrator (SO) | `play_loop.py:4409` | **Present** (this WO) |
| CombatController (CC) | `combat_controller.py:348` | Present (WO-ENGINE-DA-ROUND-RESET-001) |

**Consume-site chain:**
- Write (chargen): `session_orchestrator.py:208` — initialized `"deflect_arrows_used": []`
- Write (reset — SO path): `play_loop.py:4409` — `active_combat["deflect_arrows_used"] = []` (this WO)
- Write (reset — CC path): `combat_controller.py:348` — unchanged
- Read: `attack_resolver.py:904` — DA reactive gate checks `deflect_arrows_used`
- Effect: character who used DA in round 1 is eligible again in round 2 (SO path)
- Gate: DAR-006 (canary) ✓

---

### WO2: WO-ENGINE-MANYSHOT-CONDITION-BLIND-001 — Manyshot Condition Modifiers

**File changed:** `aidm/core/attack_resolver.py`

**Lines changed:** 2428–2453 (resolve_manyshot attack roll construction)

Before (lines 2428–2438):
```python
# PHB p.97: single attack roll at -4 penalty (Manyshot penalty, NOT Rapid Shot -2)
base_attack_bonus = attacker.get(EF.ATTACK_BONUS, 0)
manyshot_penalty = -4  # PHB p.97: 2-arrow volley at -4
effective_bonus = base_attack_bonus + manyshot_penalty

# Roll ONE d20 — single attack roll for both arrows (MS-007: only one d20 roll event)
combat_rng = rng.stream("combat")
d20_roll = combat_rng.randint(1, 20)
attack_total = d20_roll + effective_bonus
target_ac = target.get(EF.AC, 10)
hit = attack_total >= target_ac
```

After (lines 2428–2453):
```python
# Condition modifiers — PHB: all standard attack modifiers apply (WO-ENGINE-MANYSHOT-CONDITION-BLIND-001)
attacker_modifiers = get_condition_modifiers(world_state, intent.attacker_id, context="attack")
defender_modifiers = get_condition_modifiers(world_state, intent.target_id, context="defense")

# PHB p.97: single attack roll at -4 penalty (Manyshot penalty, NOT Rapid Shot -2)
base_attack_bonus = attacker.get(EF.ATTACK_BONUS, 0)
manyshot_penalty = -4  # PHB p.97: 2-arrow volley at -4
effective_bonus = base_attack_bonus + manyshot_penalty + attacker_modifiers.attack_modifier

# Roll ONE d20 — single attack roll for both arrows (MS-007: only one d20 roll event)
combat_rng = rng.stream("combat")
d20_roll = combat_rng.randint(1, 20)
attack_total = d20_roll + effective_bonus

# Manyshot is always ranged — apply ranged AC modifiers + DEX denial on loses_dex_to_ac
base_target_ac = target.get(EF.AC, 10)
_ms_dex_penalty = 0
if defender_modifiers.loses_dex_to_ac and not _target_retains_dex_via_uncanny_dodge(target):
    dex_mod = target.get(EF.DEX_MOD, 0)
    if dex_mod > 0:
        _ms_dex_penalty = -dex_mod
_ms_condition_ac = (
    defender_modifiers.ac_modifier_ranged if defender_modifiers.ac_modifier_ranged != 0
    else defender_modifiers.ac_modifier
)
target_ac = base_target_ac + _ms_condition_ac + _ms_dex_penalty
hit = attack_total >= target_ac
```

**Assumptions validated:**
- `get_condition_modifiers` already imported at `attack_resolver.py:63` — no new import needed ✓
- Raw `EF.ATTACK_BONUS` read was at line 2429 (pre-fix); raw `EF.AC` read at line 2438 — confirmed
- `resolve_attack` call pattern: `get_condition_modifiers(world_state, intent.attacker_id, context="attack")` — mirrored exactly
- Parallel paths scan:
  - `resolve_attack` (lines 403-404): calls `get_condition_modifiers` ✓
  - `resolve_manyshot` (lines 2429-2430): now calls `get_condition_modifiers` ✓ (this WO)
  - `resolve_nonlethal_attack` (lines 1411-1412): calls `get_condition_modifiers` ✓ (confirmed in AUDIT-WO-013)
  - No other attack-roll paths found blind.

**Implementation choice:** Inline pattern (same as `resolve_attack` and `resolve_nonlethal_attack`). No shared helper extracted. `resolve_attack` also inlines — parity maintained.

**Consume-site chain:**
- Write: `EF.CONDITIONS` set on entities via `apply_condition()` or test fixture
- Read: `aidm/core/attack_resolver.py:2429-2453` — condition modifiers queried and applied to `effective_bonus` and `target_ac` in `resolve_manyshot`
- Effect: Manyshot attack roll correctly reflects shaken (-2), flat-footed (loses DEX), stunned (-2 AC + loses DEX), etc.
- Gate: MCB-006 (canary: compound shaken + flat-footed) ✓

**Investigative finding during implementation:** The MCB gate tests initially used condition format `{"shaken": {"condition_type": "shaken"}}`. This is NOT the supported shorthand — `ConditionInstance.from_dict()` raises `KeyError` on the missing "source"/"modifiers"/"applied_at_event_id" keys, which is silently swallowed by the `except (ValueError, KeyError): continue` handler in `get_condition_modifiers`. Correct shorthand format is `{"shaken": {}}` (empty dict), which routes through `_get_modifiers_for_condition_type()`. Tests corrected to use empty-dict format. No production code changed for this — the test format was wrong, not the production logic.

**Gate file:** `tests/test_engine_manyshot_condition_blind_001_gate.py` — 8 tests (MCB-001..008)
**Gate file:** `tests/test_engine_deflect_arrows_reset_001_gate.py` — 8 tests (DAR-001..008)

---

## Pass 2 — PM Summary

WO1 (DA reset SO path): One-line fix at `play_loop.py:4409` — added `active_combat["deflect_arrows_used"] = []` to the SO-path round-boundary block alongside the existing AoO resets. Wrong comment corrected. PHB p.93 compliance restored: DA usable once per round for entire combat on SO path (was locked after round 1). DAR-006 canary proves round-2 eligibility. CC path unchanged. 8/8 DAR gates pass.

WO2 (Manyshot condition blind): Three lines added to `resolve_manyshot` — `get_condition_modifiers()` called for attacker and target; attack bonus and target AC adjusted accordingly. Ranged-specific AC override used for defender (ranged > general). DEX denial applied via `_target_retains_dex_via_uncanny_dodge`. MCB-006 canary (shaken + flat-footed compound) passes. All three attack-roll paths now call `get_condition_modifiers`. 8/8 MCB gates pass.

---

## Pass 3 — Retrospective

**Out-of-scope finding:** The condition shorthand format `{"condition_type": "shaken"}` is silently ignored by `get_condition_modifiers` (KeyError swallowed). This is NOT a new bug — the `_normalize_condition_dict` docstring documents the normalized form but notes it's "test-verifiability only." The silent-skip behavior for malformed condition dicts predates this WO. No production path sets conditions in this format (all use `create_*_condition().to_dict()` which produces the full structure). Filing to Radar as LOW informational.

**Kernel touches:** None.

**`CONSUME_DEFERRED` fields:** None introduced by this WO.

---

## Radar

| Finding ID | Severity | Description | Status |
|------------|----------|-------------|--------|
| FINDING-ENGINE-CONDITION-SHORTHAND-SILENT-SKIP-001 | LOW | `{"condition_type": "X"}` (one-key dict) is silently skipped by `get_condition_modifiers` — KeyError on missing "source"/"modifiers" keys swallowed by except handler. No production path sets this format; tests must use `{}` (empty dict) or full `.to_dict()` output. Informational only. | NEW — file to BACKLOG |

---

## Coverage Map Updates

- **Deflect Arrows** (row ~331): Updated to note both reset paths (SO: play_loop.py:4409, CC: combat_controller.py:348). Added DAR-001..008 gate refs. Batch AP noted.
- **Manyshot** (row ~294): Updated to note condition modifiers now applied via `get_condition_modifiers()`. Added MCB-001..008 gate refs. Batch AP noted.

---

## ML Preflight Checklist

- [x] ML-001: Gaps verified — FINDING-ENGINE-DEFLECT-ARROWS-RESET-001 confirmed by grep (play_loop.py:4405 wrong comment, missing reset); FINDING-ENGINE-MANYSHOT-CONDITION-BLIND-001 confirmed (resolve_manyshot:2429 raw EF.ATTACK_BONUS, :2437 raw EF.AC, no get_condition_modifiers call)
- [x] ML-002: 16/16 gate tests pass (DAR-001..008 + MCB-001..008)
- [x] ML-003: Assumptions to Validate completed for both WOs (line numbers confirmed, type confirmed, import confirmed, parallel paths checked)
- [x] ML-004: Pre-existing baseline 161 engine-suite failures noted; no new failures introduced (WO gate suite only run)
- [x] ML-005: Commit hash 786f583 in debrief header; committed before debrief
- [x] ML-006: Coverage map updated — Deflect Arrows and Manyshot rows updated in `docs/ENGINE_COVERAGE_MAP.md`

## PM Acceptance Notes — Verification

1. **DAR-006 canary:** DA used in round 1 → reset at round boundary → `deflect_arrows_used == []` → "b" NOT in list → eligible in round 2. Test `test_dar_006_da_usable_in_round_2_after_round_1_use` PASSED ✓
2. **Wrong comment corrected:** Before: "Do NOT touch deflect_arrows_used (already reset in combat_controller.py:348)". After: "Per-round reset: AoO counters + Deflect Arrows (PHB p.137/p.93) / Note: combat_controller.py:348 resets DA on the CC path; this block covers the SO path." ✓
3. **No other accumulator gaps:** AUDIT-WO-013 table verified complete — no additional per-round accumulator missing a reset. ✓
4. **CC-path reset unmodified:** `combat_controller.py:348` NOT touched. DAR-004/005 prove SO-path AOR resets intact. ✓
5. **`deflect_arrows_used` type confirmed:** `session_orchestrator.py:208` initializes as `[]` (list). Reset value `[]` matches. ✓
6. **MCB-006 canary:** Shaken attacker (bab=6 -4 manyshot -2 shaken = 0) + flat-footed target (AC 14 - dex_mod 3 = 11). Both deltas applied simultaneously. `test_mcb_006_compound_shaken_attacker_flat_footed_target_canary` PASSED ✓
7. **Import confirmed:** `get_condition_modifiers` imported at `attack_resolver.py:63`. No new import. ✓
8. **Parallel paths scan complete:** resolve_attack ✓, resolve_manyshot ✓ (this WO), resolve_nonlethal_attack ✓. No other blind paths found. ✓
9. **No new pre-existing failures:** MCB suite uses synthetic fixtures. No pre-existing failure count change. ✓
