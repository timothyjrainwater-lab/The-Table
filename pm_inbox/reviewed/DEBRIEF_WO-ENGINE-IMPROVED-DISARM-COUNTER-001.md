# Debrief: WO-ENGINE-IMPROVED-DISARM-COUNTER-001
**Artifact ID:** DEBRIEF_WO-ENGINE-IMPROVED-DISARM-COUNTER-001
**WO:** WO-ENGINE-IMPROVED-DISARM-COUNTER-001
**Batch:** P
**Commit:** 5d088d6 (gate tests) / 0440ffa (engine changes committed in Batch S PM close-out)
**Date:** 2026-02-27
**Result:** ACCEPTED — 8/8 IDC tests PASS

**Closes:** FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001

---

## Pass 1: Context Dump

**Target file:** `aidm/core/maneuver_resolver.py`

**Audit finding:** Counter-disarm logic was partially implemented but had **two critical bugs**:

1. **Wrong margin calculation:** `margin = check_result.defender_roll - check_result.attacker_roll` — used raw d20 rolls, not totals. Should be `check_result.defender_total - check_result.attacker_total`.

2. **Inverted branch logic:**
   - `if margin >= 10:` → auto-disarmed attacker directly (set `EF.DISARMED = True`, no opposed roll) — **WRONG**: this path should roll a counter
   - `else:` → rolled counter-disarm via `_roll_opposed_check` — **WRONG**: the counter only applies at margin >= 10; margin < 10 should be a simple fail

   The two branches were completely swapped.

3. **`counter_disarm_allowed` always True:** payload field was hardcoded `True` regardless of margin.

### Fix applied

```python
# Fixed margin
margin = check_result.defender_total - check_result.attacker_total
counter_disarm_allowed = margin >= 10

# Restructured branches:
if margin >= 10:
    _att_feats = world_state.entities.get(attacker_id, {}).get(EF.FEATS, [])
    if "improved_disarm" in _att_feats:
        events.append(Event(..., "counter_disarm_suppressed",
            payload={"actor_id": attacker_id, "feat": "improved_disarm"}))
        result = ManeuverResult(success=False, ...)
    else:
        counter_result = _roll_opposed_check(rng, defender_modifier, attacker_modifier, "counter_disarm")
        # ... resolve counter (existing logic moved here)
else:
    # Normal fail — margin < 10, no counter
    result = ManeuverResult(success=False, ...)
```

**B-AMB-04 canary:** The else-block refactor removed a `# B-AMB-04` comment from the weapon-type modifiers line. Test `test_b_amb_04_in_disarm_source` detected this. Fixed by appending ` — B-AMB-04` to the existing comment at line 1456.

**Engine commit note:** The WO4 engine changes landed in commit `0440ffa` (labeled "pm: Batch S ACCEPTED verdict"). The gate test file was committed separately in `5d088d6` after the engine changes were already at HEAD.

---

## Pass 2: PM Summary (≤100 words)

Counter-disarm base was partially implemented with inverted logic and raw-roll margin. Fixed: `margin = defender_total - attacker_total`; `counter_disarm_allowed = margin >= 10`; `if margin >= 10` now rolls counter via `_roll_opposed_check` (feat check first); `margin < 10` is simple fail. Improved Disarm feat suppresses counter at `>= 10` boundary with `counter_disarm_suppressed` event. B-AMB-04 canary comment restored. FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 closed. 8/8 IDC gates pass.

---

## Pass 3: Retrospective

**Counter-disarm base:** Was implemented before this WO (partial implementation from Batch L), but completely broken. Both the base trigger logic AND the suppression path were effectively new work due to the inverted branches.

**Threshold boundary (≥ 10 vs > 10):** Implemented as `>= 10` (inclusive). PHB p.155: "If the attacker loses by 10 or more" — "by 10" means the margin IS 10, so `>= 10` is correct. IDC-002 (margin=5, no counter) and IDC-003 (margin=10, counter triggered) bracket the boundary in the gate tests.

**Attacker DEX-stripped behavior:** PHB p.96: "you lose your Dexterity bonus to AC (if any) against this disarm attempt." This is **NOT implemented** — the counter-disarm uses standard `_roll_opposed_check(rng, defender_modifier, attacker_modifier, ...)` with no flat-footed modification. FINDING-ENGINE-IDC-DEX-STRIPPED-001 filed. Not blocking for Batch P acceptance.

**Counter roll direction:** `_roll_opposed_check(rng, defender_modifier, attacker_modifier, "counter_disarm")` — defender becomes the counter-attacker, original attacker becomes the counter-defender. Consistent with PHB: the target of the original disarm attempt gets the counter.

**IDC-006 test note:** Needed `_SeqRNG` (not `MagicMock` constant RNG) because counter-fail requires counter_attacker to NOT win — which with equal modifiers means counter_attacker_roll ≤ counter_defender_roll. Required seq: `[5, 15, 8, 10]` to produce disarm fail by 10 then counter fail.

---

## Radar

| Finding | Severity | Status |
|---------|----------|--------|
| FINDING-ENGINE-IMPROVED-DISARM-COUNTER-001 | LOW | CLOSED — counter-disarm logic fixed (inverted branches corrected, raw-roll margin fixed, Improved Disarm suppression wired) |
| FINDING-ENGINE-IDC-DEX-STRIPPED-001 | LOW | OPEN — PHB p.96/p.155: attacker loses DEX bonus to AC for the counter attempt. Not implemented — counter uses normal disarm resolution. Future WO: pass flat-footed flag to counter `_roll_opposed_check` or strip DEX from AC in the counter path. |
| FINDING-ENGINE-IDC-INVERTED-LOGIC-BATCH-L-001 | LOW | CLOSED — pre-existing inverted counter-disarm branches (margin >= 10 auto-disarmed, else rolled counter) fixed in this WO. Root cause: Batch L implementation confusion about which margin branch should roll the counter. |
