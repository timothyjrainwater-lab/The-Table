# DEBRIEF: WO-ENGINE-RAPID-SHOT-001

**Verdict:** PASS [8/8 gate tests]
**Gate:** ENGINE-RAPID-SHOT
**Date:** 2026-02-26
**WO:** WO-ENGINE-RAPID-SHOT-001

---

## Pass 1: Files Modified / Key Findings

### Files Modified
- `aidm/core/full_attack_resolver.py` — 8 lines inserted after `attack_bonuses` initialization (line 666)
- `tests/test_engine_rapid_shot_gate.py` — 8 gate tests RS-001 through RS-008 (new file)

### Implementation
In `resolve_full_attack()`, after `calculate_iterative_attacks()` builds `raw_attack_bonuses`
and `attack_bonuses` is populated with the TWF main-hand penalty applied, a new block checks
for Rapid Shot eligibility:

```python
# WO-ENGINE-RAPID-SHOT-001: Rapid Shot extra attack (PHB p.99)
# Penalty (-2 to all attacks) already handled by feat_resolver.get_attack_modifier().
_attacker_feats = attacker.get(EF.FEATS, [])
if "rapid_shot" in _attacker_feats and intent.weapon.is_ranged:
    raw_attack_bonuses = list(raw_attack_bonuses)  # ensure mutable
    raw_attack_bonuses.append(raw_attack_bonuses[0])  # extra attack at highest BAB
    attack_bonuses = [b + main_penalty for b in raw_attack_bonuses]  # rebuild with extra
```

Both `raw_attack_bonuses` (audit trail) and `attack_bonuses` (penalized, loop-iterated) are
kept parallel. The -2 penalty was already wired in `feat_resolver.get_attack_modifier()`.

### Key Findings
- `FeatID.RAPID_SHOT = "rapid_shot"` — string constant; no new import needed
- `intent.weapon.is_ranged` — property derived from `weapon_type == "ranged"` (Weapon schema)
- The `-2 penalty` is applied via `feat_attack_modifier` from `feat_resolver.get_attack_modifier()`
  and surfaced as `feat_modifier` in `attack_roll` event payloads
- RS-003 initially checked `attack_bonus` in the payload (which is `base_attack_bonus_raw`,
  the raw iterative BAB for audit); corrected to check `feat_modifier == -2`

---

## Pass 2: PM Summary (≤100 words)

Rapid Shot extra attack injection wired in `full_attack_resolver.resolve_full_attack()`. When
attacker has `rapid_shot` feat and weapon is ranged, both `raw_attack_bonuses` and `attack_bonuses`
get a copy of the highest-BAB entry appended. The -2 penalty was pre-existing in feat_resolver.
8/8 gate tests pass. 0 regressions introduced (12 pre-existing failures in cleave-adjacency,
condition-enforcement, and hooligan-tier-A gates remain unchanged).

---

## Pass 3: Retrospective / Drift Caught

- **Drift caught:** RS-003 initially verified the wrong payload field (`attack_bonus` = raw BAB)
  instead of `feat_modifier` (the Rapid Shot -2). Corrected on first run.
- **Scope discipline maintained:** `calculate_iterative_attacks()` was not modified; the penalty
  path in `feat_resolver.py` was not touched. Only injection in `full_attack_resolver.py`.
- **Parallel list invariant:** `raw_attack_bonuses` and `attack_bonuses` are rebuilt together
  to keep them parallel for the `attack_index` → `raw_bab` lookup in the loop body.
- **No import added:** `"rapid_shot"` string literal used directly (consistent with how Cleave
  uses deferred imports; feat string constants are stable).

---

## Radar: Gate Results

| Test | ID | Result |
|------|----|--------|
| No Rapid Shot -> 2 attacks (BAB 6, ranged) | RS-001 | PASS |
| Rapid Shot + ranged -> N+1 attacks | RS-002 | PASS |
| All attacks get -2 feat_modifier | RS-003 | PASS |
| Rapid Shot + melee -> no extra attack | RS-004 | PASS |
| Rapid Shot + BAB 1 -> 2 total attacks | RS-005 | PASS |
| Rapid Shot + BAB 11 -> 4 total attacks | RS-006 | PASS |
| Standard (non-full) attack unaffected | RS-007 | PASS |
| TWF + Rapid Shot + ranged -> 3 attacks | RS-008 | PASS |

**Gate score: 8/8 PASS**

---

*Regression: 1092 passed, 12 pre-existing failures (cleave-adjacency, condition-enforcement,
hooligan-tier-A — all pending WOs). Zero new failures from this change.*
