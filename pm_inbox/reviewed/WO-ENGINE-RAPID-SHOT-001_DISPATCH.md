# WO-ENGINE-RAPID-SHOT-001
## Wire Rapid Shot — Extra Ranged Attack + -2 Penalty in Full Attack

**Priority:** MEDIUM
**Classification:** FEATURE
**Gate ID:** ENGINE-RAPID-SHOT
**Minimum gate tests:** 8
**Source:** PHB p.99 — "Rapid Shot: You can get one extra attack per round with a ranged weapon. The attack is at your highest base attack bonus, but each attack you make in that round (the extra one and the normal ones) takes a -2 penalty."
**Dispatch:** ENGINE BATCH C

---

## Target Lock

`feat_resolver.py` already applies the `-2 penalty` to all ranged attacks when `rapid_shot` feat is present (line 167–169). What is **missing**: the extra attack. `full_attack_resolver.py:calculate_iterative_attacks()` builds the iterative attack list without checking for Rapid Shot. The fix: in `resolve_full_attack()`, after the iterative attack list is built, if the attacker has `rapid_shot` and is using a ranged weapon, append one additional attack at `BAB` (highest) before applying per-attack penalties. The `-2 penalty` is already handled by `feat_resolver.get_attack_modifier()` at line 167 — do not double-apply it.

---

## Binary Decisions

1. **Where to inject the extra attack?** In `resolve_full_attack()` in `full_attack_resolver.py`, after `calculate_iterative_attacks()` returns `attack_bonuses` (around line 706 loop setup). Insert a check: if `rapid_shot` in feats and `intent.weapon.is_ranged`, append the extra attack to the `attack_bonuses` list. Do NOT modify `calculate_iterative_attacks()` itself — that function is a pure PHB BAB calculator and should remain clean.

2. **Bonus at what value?** PHB p.99: "at your highest base attack bonus." The iterative list is already ordered highest-first. Append `attack_bonuses[0]` (the highest BAB) as the extra attack. It is appended at the END of the list — PHB doesn't specify position, and appending after all normal attacks is consistent with TWF extra attack pattern already in the engine.

3. **-2 penalty scope?** PHB: "each attack you make in that round… takes a -2 penalty." The existing `feat_resolver.py` line 167–169 already applies `-2` to ALL ranged attacks via `get_attack_modifier()`. Since the extra attack goes through the same attack loop and `get_attack_modifier()` is called per-attack, the penalty will apply automatically. No extra code needed for the penalty.

4. **Prerequisite enforcement?** Feat prerequisites (DEX 13, Point Blank Shot) are enforced at character creation / chargen, not at runtime. The WO does not add runtime prerequisite checks — assume the feat is legitimately held if it appears in `entity.get(EF.FEATS, [])`.

5. **Full attack only?** Yes. PHB p.99: "one extra attack per round" — this is a full attack action benefit. The standard attack path (`attack_resolver.resolve_attack()`) is unaffected. Only `full_attack_resolver.resolve_full_attack()` needs the extra attack injection.

---

## Contract Spec

### `aidm/core/full_attack_resolver.py` — `resolve_full_attack()`

Locate where `attack_bonuses` is finalized (after `calculate_iterative_attacks()` call, before the attack loop at ~line 706). Insert:

```python
# WO-ENGINE-RAPID-SHOT-001: Rapid Shot extra attack (PHB p.99)
# Penalty (-2 to all attacks) already handled by feat_resolver.get_attack_modifier().
# This block only adds the extra attack to the sequence.
_attacker_feats = attacker.get(EF.FEATS, [])
if "rapid_shot" in _attacker_feats and intent.weapon.is_ranged:
    attack_bonuses.append(attack_bonuses[0])  # extra attack at highest BAB
    raw_attack_bonuses.append(raw_attack_bonuses[0])  # mirror raw list if used
```

**Note:** Confirm whether `raw_attack_bonuses` is a separate parallel list that also needs the append. If it is constructed alongside `attack_bonuses`, mirror the append. If it is derived later, only append to `attack_bonuses`.

### `tests/test_engine_rapid_shot_gate.py` — NEW FILE

Minimum 8 gate tests, IDs RS-001 through RS-008:

| Test | Assertion |
|------|-----------|
| RS-001 | No Rapid Shot: full attack with ranged weapon produces N iterative attacks (BAB-based) |
| RS-002 | Rapid Shot + ranged weapon: full attack produces N+1 attacks (one extra at highest BAB) |
| RS-003 | Rapid Shot + ranged weapon: all attacks have -2 applied (existing penalty confirmed) |
| RS-004 | Rapid Shot + melee weapon: no extra attack (feat only applies to ranged) |
| RS-005 | Rapid Shot + ranged weapon + BAB 1 (one normal attack): full attack produces 2 attacks total |
| RS-006 | Rapid Shot + ranged weapon + BAB 11 (three normal): full attack produces 4 attacks total |
| RS-007 | Regression: standard (non-full) ranged attack unaffected by Rapid Shot extra attack |
| RS-008 | Two-weapon fighting attacker with Rapid Shot: extra attack still appended (no conflict) |

---

## Implementation Plan

1. Read `aidm/core/full_attack_resolver.py` lines 90–130 (calculate_iterative_attacks) and lines 680–760 (attack loop setup).
2. Identify exact line where `attack_bonuses` is finalized and the loop begins. Confirm whether `raw_attack_bonuses` is a parallel list.
3. Insert Rapid Shot extra attack block immediately before the loop.
4. Confirm `feat_resolver.py` line 167–169 penalty is in scope for the extra attack (it should be, since all attacks pass through `get_attack_modifier()`).
5. Write `tests/test_engine_rapid_shot_gate.py` with RS-001 through RS-008.
6. Run gate suite: `python -m pytest tests/test_engine_rapid_shot_gate.py -v`.
7. Run regression: `python -m pytest tests/ -q --tb=short --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ui_2d_wiring.py`.
8. Confirm 0 new failures.

---

## Integration Seams

- **`aidm/core/full_attack_resolver.py`** — `resolve_full_attack()` only. `calculate_iterative_attacks()` is not modified.
- **`aidm/core/feat_resolver.py`** — `get_attack_modifier()` already handles -2 penalty at line 167–169. No changes.
- **`aidm/schemas/attack.py`** — `Weapon.is_ranged` property already exists (`weapon_type == "ranged"`). No changes.
- **`aidm/schemas/entity_fields.py`** — `EF.FEATS` already defined. No new constants.
- **Event constructor:** `Event(event_id=..., event_type=..., timestamp=..., payload=...)` — not relevant (events emitted per-attack inside the loop, not at extra attack injection point).
- **Class feature pattern:** Not applicable — feat check via `EF.FEATS` list.

---

## Assumptions to Validate

1. Confirm `feat_resolver.get_attack_modifier()` is called for each attack in the full attack loop (expected: yes — `feat_attack_modifier` is computed per-attack or applied globally; check call site).
2. Confirm `attack_bonuses` is a mutable list at the insertion point (expected: yes — returned by `calculate_iterative_attacks()`).
3. Confirm `raw_attack_bonuses` is a parallel list (expected: uncertain — verify in `resolve_full_attack()` before assuming append is needed).
4. Confirm no existing Rapid Shot extra attack logic anywhere in `full_attack_resolver.py` (expected: grep returns nothing — verify).

---

## Preflight

Before writing any code:
- `grep -n "rapid_shot\|RAPID_SHOT" aidm/core/full_attack_resolver.py` — confirm no existing extra attack implementation
- `grep -n "rapid_shot\|RAPID_SHOT" aidm/core/feat_resolver.py` — confirm penalty location (expected: line 167–169)
- `grep -n "raw_attack_bonuses\|attack_bonuses" aidm/core/full_attack_resolver.py | head -20` — map list construction and usage
- `python -m pytest tests/ -q -k "full_attack or ranged" --tb=short` — regression baseline for full attack path

---

## Delivery Footer

- Files modified: `aidm/core/full_attack_resolver.py`, `tests/test_engine_rapid_shot_gate.py` (new)
- Gate: ENGINE-RAPID-SHOT, minimum 8 tests
- Run full regression before filing debrief
- **Debrief Required:** File to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-RAPID-SHOT-001.md`

### Debrief Template

```
# DEBRIEF — WO-ENGINE-RAPID-SHOT-001

**Verdict:** [PASS/FAIL] [N/N]
**Gate:** ENGINE-RAPID-SHOT
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
