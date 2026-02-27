# Debrief: WO-ENGINE-POWER-ATTACK-001
**Artifact ID:** DEBRIEF_WO-ENGINE-POWER-ATTACK-001
**WO:** WO-ENGINE-POWER-ATTACK-001
**Batch:** P
**Commit:** cd429fb
**Date:** 2026-02-27
**Result:** ACCEPTED — 8/8 PA tests PASS

---

## Pass 1: Context Dump

**Target files:** `aidm/core/feat_resolver.py`, `aidm/core/attack_resolver.py`

### `aidm/core/feat_resolver.py` — damage multiplier fix

Pre-existing stub in `get_damage_modifier()` had 2H at `penalty * 2` (wrong — PHB says 2× but dispatch spec says 1.5×). Off-hand path was absent entirely.

Fixed block:
```python
if FeatID.POWER_ATTACK in feats:
    power_attack_penalty = context.get("power_attack_penalty", 0)
    is_two_handed = context.get("is_two_handed", False)
    grip = context.get("grip", "one-handed")
    if is_two_handed:
        modifier += int(power_attack_penalty * 1.5)   # dispatch spec: 1.5:1
    elif grip == "off-hand":
        modifier += power_attack_penalty // 2          # 0.5:1 for TWF off-hand
    else:
        modifier += power_attack_penalty               # 1:1 one-handed / natural
```

Added `grip` context key read. `is_two_handed` was already in context.

### `aidm/core/attack_resolver.py` — validation block + feat_context

Added `"grip": intent.weapon.grip` to `feat_context` dict (alongside existing `is_two_handed`, `power_attack_penalty`).

Inserted PA validation block immediately after `feat_attack_modifier` is computed:
```python
_pa_penalty = intent.power_attack_penalty
if _pa_penalty > 0:
    _pa_feats = attacker.get(EF.FEATS, [])
    if "power_attack" not in _pa_feats:
        events.append(Event(..., "intent_validation_failed",
            payload={"reason": "feat_requirement_not_met", "feat": "power_attack"}))
        return events
    _attacker_bab = attacker.get(EF.BAB, 0)
    if _pa_penalty > _attacker_bab:
        events.append(Event(..., "intent_validation_failed",
            payload={"reason": "penalty_exceeds_bab", ...}))
        return events
```

`power_attack_penalty: int = 0` was already on `AttackIntent` from a prior stub — no schema change required.

---

## Pass 2: PM Summary (≤100 words)

Power Attack wired in two files. feat_resolver.py: fixed 2H multiplier from 2× to 1.5× (dispatch spec); added off-hand 0.5× path keyed on `grip == "off-hand"`; `grip` added to feat_context dict in attack_resolver.py. Validation block in attack_resolver.py: feat guard and BAB cap both emit `intent_validation_failed` and early-return before roll. `power_attack_penalty` attribute was already on AttackIntent from a prior stub. Combat Expertise pattern mirrored exactly. 8/8 PA gates pass, zero regressions.

---

## Pass 3: Retrospective

**Combat Expertise pattern used:** `power_attack_penalty: int = 0` attribute on `AttackIntent` (not a separate intent type). This exactly mirrors `combat_expertise_penalty: int = 0` from Batch C. The attribute was already present as a stub before this WO — only the feat_resolver.py multiplier logic and the attack_resolver.py validation block were new.

**2H multiplier:** Implemented as `int(penalty * 1.5)` per dispatch spec. PHB p.98 says 2×. Dispatch is the arbiter; implementation matches gate tests. FINDING filed below.

**Off-hand multiplier:** `penalty // 2` (integer floor). PHB doesn't explicitly state 0.5× for off-hand Power Attack; dispatch spec dictates this. Consistent with the three-tier PA multiplier contract.

**Feat key string:** `"power_attack"` — lowercase underscore. Confirmed against FEAT_REGISTRY keys from Batch A data import.

**BAB check:** Uses `EF.BAB` directly (pure BAB). NOT `EF.ATTACK_BONUS` (BAB + STR_MOD). Correct: the cap is against base attack bonus only.

**Hidden DM kernel check (KERNEL-03):** PA is a declared penalty added as additive modifier, consistent with CE pattern. No kernel drift.

---

## Radar

| Finding | Severity | Status |
|---------|----------|--------|
| FINDING-ENGINE-PA-2H-PHB-DEVIATION-001 | LOW | OPEN — PHB p.98: 2H Power Attack grants 2× damage bonus. Dispatch spec says 1.5×. Implemented per dispatch. Requires Thunder decision: intentional game-design deviation or spec error? |
| FINDING-ENGINE-PA-FULL-ATTACK-ROUND-LOCK-001 | LOW | OPEN — PA penalty must apply to ALL attacks in the round (declared before rolling). Engine currently trusts the caller to pass the same penalty on each AttackIntent in a full-attack sequence. No round-level enforcement. Not blocking. |
