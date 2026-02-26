# WO-ENGINE-WEAPON-FINESSE-001
## Wire Weapon Finesse — DEX-Based Melee Attack Rolls

**Priority:** MEDIUM
**Classification:** FEATURE
**Gate ID:** ENGINE-WEAPON-FINESSE
**Minimum gate tests:** 8
**Source:** PHB p.102 — "Weapon Finesse: Use your Dexterity modifier instead of your Strength modifier on attack rolls with light weapons, rapiers, whips, or spiked chains."
**Dispatch:** ENGINE BATCH B

---

## Target Lock

When an attacker has the `weapon_finesse` feat and is wielding a light weapon (or eligible weapon), substitute DEX modifier for STR modifier in the attack roll bonus computation inside `attack_resolver.py`. The feat only affects the attack roll — damage still uses STR modifier (PHB p.102).

---

## Binary Decisions

1. **Scope:** Light weapons only for this WO. Rapier, whip, spiked chain are edge cases that require weapon-name lookup — defer to a follow-up. PHB p.102 core case is light weapons. `weapon.is_light` (derived property: `weapon_type == "light"`) is the gate.

2. **Where does the swap happen?** At the `attack_bonus_with_conditions` construction in `resolve_attack()` in `attack_resolver.py`. The `intent.attack_bonus` is already set by the caller — the Weapon Finesse swap must happen at the source of `intent.attack_bonus` or as a modifier applied inside `resolve_attack()`. **Correct approach:** inject a `_finesse_bonus` similar to `_inspire_attack_bonus` — compute `max(dex_mod, str_mod)` delta at the attack_bonus_with_conditions block. This preserves the existing `intent.attack_bonus` (which was computed with STR) and adds/subtracts the difference cleanly.

   Actually simpler: the attack bonus injected via `intent.attack_bonus` includes STR already. The correct approach is: if finesse applies, add `(dex_mod - str_mod)` to `attack_bonus_with_conditions`. If DEX > STR this adds a positive delta; if DEX ≤ STR the feat has no effect (attacker may still choose STR — but RAW: the feat says "use DEX instead," implying it's mandatory). PHB p.102: feat is mandatory substitution when wielding a qualifying weapon. Use `dex_mod - str_mod` unconditionally when feat + light weapon both true.

3. **Touch attacks?** PHB p.102 includes melee touch attacks. `attack_resolver.py` handles touch attacks via `spell_resolver`. Scope this WO to standard melee light weapon attacks only. Touch attack finesse is a separate concern.

4. **Both `resolve_attack()` call paths?** Yes — `attack_resolver.py` has two attack resolution paths (standard + nonlethal). Both must receive the finesse modifier.

---

## Contract Spec

### `aidm/core/attack_resolver.py` — `resolve_attack()`

In the `attack_bonus_with_conditions` construction block, after `_favored_enemy_bonus` lookup, add:

```python
# WO-ENGINE-WEAPON-FINESSE-001: Weapon Finesse — DEX replaces STR for light weapon attacks (PHB p.102)
_finesse_delta = 0
_attacker_feats = attacker.get(EF.FEATS, [])
if "weapon_finesse" in _attacker_feats and intent.weapon.is_light:
    _str_mod = attacker.get(EF.STR_MOD, 0)
    _dex_mod = attacker.get(EF.DEX_MOD, 0)
    _finesse_delta = _dex_mod - _str_mod  # positive if DEX > STR, negative if DEX < STR
```

Add `+ _finesse_delta` to `attack_bonus_with_conditions`.

Apply the same block in the nonlethal attack path (`resolve_nonlethal_attack()`) — identical pattern.

### `tests/test_engine_weapon_finesse_gate.py` — NEW FILE

Minimum 8 gate tests, IDs WF-001 through WF-008:

| Test | Assertion |
|------|-----------|
| WF-001 | Weapon Finesse + light weapon + DEX 16 (mod +3) + STR 10 (mod 0): attack roll includes +3 DEX instead of +0 STR |
| WF-002 | Weapon Finesse + light weapon + DEX 10 (mod 0) + STR 16 (mod +3): finesse_delta = -3 (feat mandatory, uses DEX even when lower) |
| WF-003 | Weapon Finesse + one-handed weapon: no finesse bonus (not a light weapon) |
| WF-004 | No Weapon Finesse feat + light weapon + DEX 16: no finesse bonus |
| WF-005 | Weapon Finesse + light weapon: damage still uses STR (finesse only affects attack roll) |
| WF-006 | Weapon Finesse + light weapon + DEX 14, STR 14: finesse_delta = 0 (no change) |
| WF-007 | Weapon Finesse + light weapon + DEX 18 (mod +4): full attack sequence applies finesse to all iterative attacks |
| WF-008 | Regression: non-finesse attacker with one-handed weapon unaffected |

---

## Implementation Plan

1. Read `aidm/core/attack_resolver.py` lines 375–420 (attack_bonus_with_conditions block).
2. Locate `_favored_enemy_bonus` block. Insert `_finesse_delta` block immediately after.
3. Add `+ _finesse_delta` to `attack_bonus_with_conditions`.
4. Find nonlethal attack path (`resolve_nonlethal_attack()`) — apply same pattern.
5. Write `tests/test_engine_weapon_finesse_gate.py` with WF-001 through WF-008.
6. Run gate suite: `python -m pytest tests/test_engine_weapon_finesse_gate.py -v`.
7. Run regression: `python -m pytest tests/ -q --tb=short --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ui_2d_wiring.py`.
8. Confirm 0 new failures.

---

## Integration Seams

- **`aidm/core/attack_resolver.py`** — `resolve_attack()` and `resolve_nonlethal_attack()`. No other files.
- **`aidm/schemas/attack.py`** — `Weapon.is_light` already defined as derived property (`weapon_type == "light"`). No changes.
- **`aidm/schemas/entity_fields.py`** — `EF.FEATS`, `EF.STR_MOD`, `EF.DEX_MOD` all defined. No new constants.
- **Event constructor:** `Event(event_id=..., event_type=..., timestamp=..., payload=...)` — not relevant for this WO.
- **Class feature pattern:** Not applicable — feat check via `EF.FEATS` list.

---

## Assumptions to Validate

1. Confirm `Weapon.is_light` derived property exists in `aidm/schemas/attack.py` (expected: yes — line 107).
2. Confirm `intent.attack_bonus` is computed with STR modifier by the caller (expected: yes — `session_orchestrator.py` sets `attack_bonus = entity.get(EF.ATTACK_BONUS, 0)` which is a flat bonus, not modifier-adjusted). **Critical:** verify whether `intent.attack_bonus` already includes STR mod or whether STR is separate. If STR is already baked in, the delta approach is correct. If `attack_bonus` is BAB only (no STR), the approach needs adjustment.
3. Confirm nonlethal attack path exists as separate function (expected: yes — `resolve_nonlethal_attack()`).

---

## Preflight

Before writing any code:
- `grep -n "attack_bonus\|STR_MOD\|str_mod" aidm/runtime/session_orchestrator.py | head -20` — verify how `intent.attack_bonus` is constructed (BAB only, or BAB + STR)
- `grep -n "weapon_finesse\|WEAPON_FINESSE" aidm/core/attack_resolver.py` — confirm no existing implementation
- `python -m pytest tests/test_engine_favored_enemy_gate.py -v` — regression baseline for attack_resolver

---

## Delivery Footer

- Files modified: `aidm/core/attack_resolver.py`, `tests/test_engine_weapon_finesse_gate.py` (new)
- Gate: ENGINE-WEAPON-FINESSE, minimum 8 tests
- Run full regression before filing debrief
- **Debrief Required:** File to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-WEAPON-FINESSE-001.md`

### Debrief Template

```
# DEBRIEF — WO-ENGINE-WEAPON-FINESSE-001

**Verdict:** [PASS/FAIL] [N/N]
**Gate:** ENGINE-WEAPON-FINESSE
**Date:** [DATE]

## Pass 1 — Per-File Breakdown
[Files modified, changes made, key findings]

## Pass 2 — PM Summary (≤100 words)
[Summary]

## Pass 3 — Retrospective
[Drift caught, patterns, open findings]

## Radar
[Gate results, confirmations]
```

### Audio Cue
```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
