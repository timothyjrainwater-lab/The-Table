# WO-ENGINE-UNCANNY-DODGE-001
## Wire Uncanny Dodge — Retain DEX to AC While Flat-Footed

**Priority:** MEDIUM
**Classification:** FEATURE
**Gate ID:** ENGINE-UNCANNY-DODGE
**Minimum gate tests:** 8
**Source:** PHB p.51 — "Uncanny Dodge: A rogue retains her Dexterity bonus to AC even if she is caught flat-footed or struck by an invisible attacker. She still loses her Dexterity bonus to AC if immobilized."
**Dispatch:** ENGINE BATCH C

---

## Target Lock

When a rogue (level 2+) is flat-footed, the engine currently removes their DEX bonus to AC as normal. With Uncanny Dodge, the DEX bonus should be **retained** even when flat-footed. The fix lives in the AC computation path inside `attack_resolver.py` where flat-footed DEX denial is applied. Add a bypass: if the defending entity has rogue level ≥ 2, skip the DEX denial.

Also applies to Rangers at level 4 (PHB p.47 — "Uncanny Dodge (Ex): Starting at 4th level, a ranger can react to danger before his senses would normally allow him to do so.") and Barbarians at level 2 (PHB p.26). Wire all three class gates in a single WO.

---

## Binary Decisions

1. **Where is DEX denied when flat-footed?** In `attack_resolver.py`, the flat-footed DEX penalty is applied at the AC calculation block. Locate where `EF.FLAT_FOOTED` or `EF.DEX_MOD` is conditionally excluded. This is the insertion point for the Uncanny Dodge bypass.

2. **Class level thresholds:**
   - Rogue ≥ 2 (PHB p.51)
   - Ranger ≥ 4 (PHB p.47)
   - Barbarian ≥ 2 (PHB p.26)
   Pattern: `entity.get(EF.CLASS_LEVELS, {}).get("rogue", 0) >= 2` etc.

3. **Immobilized exception:** PHB: "She still loses her Dexterity bonus to AC if immobilized." Immobilized = held, paralyzed, stunned. These map to conditions. Check if `EF.CONDITIONS` or similar tracks these. If the engine already denies DEX for paralyzed/held, the Uncanny Dodge bypass must NOT override that denial. Bypass only for flat-footed, not for movement-restricting conditions.

4. **Improved Uncanny Dodge** (PHB p.52 — can't be flanked) is a **separate** mechanic. Defer to a follow-up WO. This WO only wires the base Uncanny Dodge (flat-footed DEX retention).

5. **What if DEX denial is in a different resolver?** Validate pre-implementation. The denial may be in `attack_resolver.py` AC block or in `conditions.py` stat suppression. Find the exact location before writing code.

---

## Contract Spec

### `aidm/core/attack_resolver.py` — AC calculation block

Locate the flat-footed DEX denial (expected pattern: `if entity.get(EF.FLAT_FOOTED, False): dex_bonus = 0` or similar). Wrap with Uncanny Dodge check:

```python
# WO-ENGINE-UNCANNY-DODGE-001: Uncanny Dodge — retain DEX to AC when flat-footed (PHB p.51/47/26)
_has_uncanny_dodge = (
    target.get(EF.CLASS_LEVELS, {}).get("rogue", 0) >= 2
    or target.get(EF.CLASS_LEVELS, {}).get("ranger", 0) >= 4
    or target.get(EF.CLASS_LEVELS, {}).get("barbarian", 0) >= 2
)
_is_flat_footed = target.get(EF.FLAT_FOOTED, False)
if _is_flat_footed and not _has_uncanny_dodge:
    # Standard flat-footed: deny DEX to AC
    target_dex_bonus = 0  # (or however the existing code suppresses it)
elif _is_flat_footed and _has_uncanny_dodge:
    # Uncanny Dodge: retain DEX even flat-footed
    pass  # DEX bonus remains
```

**Note:** The exact variable names and insertion point depend on the pre-implementation read. The builder must read the AC block before writing and adapt this pattern accordingly.

### `tests/test_engine_uncanny_dodge_gate.py` — NEW FILE

Minimum 8 gate tests, IDs UD-001 through UD-008:

| Test | Assertion |
|------|-----------|
| UD-001 | Rogue level 2, flat-footed: DEX bonus retained in AC |
| UD-002 | Rogue level 1, flat-footed: DEX bonus denied (not yet gained) |
| UD-003 | Ranger level 4, flat-footed: DEX bonus retained |
| UD-004 | Ranger level 3, flat-footed: DEX bonus denied |
| UD-005 | Barbarian level 2, flat-footed: DEX bonus retained |
| UD-006 | Non-Uncanny-Dodge class (wizard), flat-footed: DEX denied (regression) |
| UD-007 | Rogue level 2, paralyzed (immobilized): DEX still denied (immobilized exception) |
| UD-008 | Rogue level 2, NOT flat-footed: DEX included normally (no change from base behavior) |

---

## Implementation Plan

1. Read `aidm/core/attack_resolver.py` lines 313–370 (AC calculation block, `target_ac` construction).
2. Locate where flat-footed DEX denial is applied. Confirm variable name and how DEX bonus is suppressed.
3. Read `aidm/schemas/conditions.py` or `aidm/core/conditions.py` — confirm whether paralyzed/held already suppress DEX separately (to avoid double-bypass).
4. Insert Uncanny Dodge bypass at flat-footed DEX denial point.
5. Write `tests/test_engine_uncanny_dodge_gate.py` with UD-001 through UD-008.
6. Run gate suite: `python -m pytest tests/test_engine_uncanny_dodge_gate.py -v`.
7. Run regression: `python -m pytest tests/ -q --tb=short --ignore=tests/test_heuristics_image_critic.py --ignore=tests/test_ui_2d_wiring.py`.
8. Confirm 0 new failures.

---

## Integration Seams

- **`aidm/core/attack_resolver.py`** — AC calculation block (flat-footed DEX denial). No other files.
- **`aidm/schemas/entity_fields.py`** — `EF.FLAT_FOOTED`, `EF.CLASS_LEVELS`, `EF.DEX_MOD` all defined. No new constants.
- **Event constructor:** `Event(event_id=..., event_type=..., timestamp=..., payload=...)` — not relevant (no events emitted from AC calculation).
- **Class feature pattern:** `entity.get(EF.CLASS_LEVELS, {}).get("rogue", 0) >= 2` — confirmed invariant pattern.

---

## Assumptions to Validate

1. Confirm flat-footed DEX denial happens in `attack_resolver.py` AC block (not in `conditions.py` or a separate resolver). If it's in conditions, the insertion point changes.
2. Confirm `EF.FLAT_FOOTED` is the correct field (expected: yes — referenced in FINDING-CE-AUTO-HIT-HELPLESS-001 context).
3. Confirm paralyzed/held DEX denial is handled separately and Uncanny Dodge bypass does NOT need to account for it (expected: yes — immobilized conditions use different suppression path).
4. Confirm no existing Uncanny Dodge implementation (expected: grep returns nothing).

---

## Preflight

Before writing any code:
- `grep -n "uncanny_dodge\|UNCANNY_DODGE" aidm/core/attack_resolver.py` — confirm not already implemented
- `grep -n "flat_footed\|FLAT_FOOTED\|dex_bonus\|DEX_MOD" aidm/core/attack_resolver.py | head -20` — locate DEX denial
- `grep -n "FLAT_FOOTED\|flat_footed" aidm/core/conditions.py` — check if DEX denial lives in conditions
- `python -m pytest tests/ -q -k "flat_footed or dex" --tb=short` — baseline for DEX/flat-footed tests

---

## Delivery Footer

- Files modified: `aidm/core/attack_resolver.py`, `tests/test_engine_uncanny_dodge_gate.py` (new)
- Gate: ENGINE-UNCANNY-DODGE, minimum 8 tests
- Run full regression before filing debrief
- **Debrief Required:** File to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-UNCANNY-DODGE-001.md`

### Debrief Template

```
# DEBRIEF — WO-ENGINE-UNCANNY-DODGE-001

**Verdict:** [PASS/FAIL] [N/N]
**Gate:** ENGINE-UNCANNY-DODGE
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
