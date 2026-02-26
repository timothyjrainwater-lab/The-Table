# WO-ENGINE-COMBAT-REFLEXES-001
## Wire Combat Reflexes — DEX-Based AoO Count Per Round

**Priority:** MEDIUM
**Classification:** FEATURE
**Gate ID:** ENGINE-COMBAT-REFLEXES
**Minimum gate tests:** 8
**Source:** PHB p.92 — "Combat Reflexes: You may make a number of additional attacks of opportunity equal to your Dexterity bonus. With this feat, you may also make attacks of opportunity while flat-footed."
**Dispatch:** ENGINE BATCH B

---

## Target Lock

Currently `aoo.py` allows one AoO per entity per round (`aoo_used_this_round` set — if entity_id is present, skip). With Combat Reflexes, the limit becomes `1 + DEX modifier` AoOs per round. The fix: change the eligibility check from a boolean (used/not used) to a count (times_used < aoo_limit).

Also: Combat Reflexes allows AoOs while flat-footed (PHB p.92). The flat-footed AoO suppression (if any) must be bypassed for entities with the feat.

---

## Binary Decisions

1. **Data structure change:** `aoo_used_this_round` is currently a set of entity IDs (used once = blocked). Change to a dict `{entity_id: count}` to track count per entity. This is a schema change on `active_combat` — must confirm `active_combat` is a dict (mutable) and that the change doesn't break existing AoO tests.

   **Alternative:** Keep the set, add a parallel `aoo_count_this_round: Dict[str, int]` key to `active_combat`. Safer — existing set-based code can be migrated incrementally. **Use this approach.**

2. **AoO limit formula:** `1 + max(0, dex_mod)` if entity has `combat_reflexes` feat; `1` otherwise. PHB p.92: DEX bonus, not DEX modifier — if DEX mod ≤ 0, Combat Reflexes grants 0 additional AoOs (still just 1). So: `aoo_limit = 1 + max(0, dex_mod) if "combat_reflexes" in feats else 1`.

3. **Flat-footed AoO:** PHB p.92: "you may also make attacks of opportunity while flat-footed." Current code: check if `aoo.py` suppresses flat-footed reactors. Validate whether this suppression exists. If it does, bypass it for Combat Reflexes holders. If it doesn't exist yet, note it as out of scope.

4. **Where does the limit check live?** In `check_aoo_triggers()` in `aoo.py`, at the eligibility loop (lines 373–374 and 342–343 for target-only path). Replace the simple `if entity_id in aoo_used_this_round: continue` with a count-based check.

---

## Contract Spec

### `aidm/core/aoo.py` — `check_aoo_triggers()`

**Step 1:** Read `aoo_count_this_round` from `active_combat` (new dict key, defaults to `{}`):
```python
aoo_count_this_round = active_combat.get("aoo_count_this_round", {})
```

**Step 2:** Replace the boolean eligibility check with a count check. For the standard (all-threateners) path, replace:
```python
if entity_id in aoo_used_this_round:
    continue
```
with:
```python
_reactor_feats = reactor.get(EF.FEATS, [])
_reactor_dex = reactor.get(EF.DEX_MOD, 0)
_aoo_limit = 1 + max(0, _reactor_dex) if "combat_reflexes" in _reactor_feats else 1
_aoo_used = aoo_count_this_round.get(entity_id, 0)
if _aoo_used >= _aoo_limit:
    continue
```

For the target-only path (lines ~342–343), same replacement using `target_id`.

**Step 3:** In `resolve_aoo_sequence()` (where AoOs are executed and `aoo_used_this_round` is updated), also increment `aoo_count_this_round[entity_id]`. Read `resolve_aoo_sequence()` to find where `aoo_used_this_round` is updated and mirror the update to `aoo_count_this_round`.

**Step 4:** Flat-footed check — validate whether `check_aoo_triggers()` suppresses flat-footed reactors. If suppression exists, add bypass: `if reactor.get(EF.FLAT_FOOTED, False) and "combat_reflexes" not in reactor_feats: continue`.

### `tests/test_engine_combat_reflexes_gate.py` — NEW FILE

Minimum 8 gate tests, IDs CR-001 through CR-008:

| Test | Assertion |
|------|-----------|
| CR-001 | No Combat Reflexes: entity gets exactly 1 AoO per round (second trigger skipped) |
| CR-002 | Combat Reflexes + DEX 16 (mod +3): entity can make 4 AoOs in one round |
| CR-003 | Combat Reflexes + DEX 10 (mod 0): entity gets 1 AoO (0 bonus — same as no feat) |
| CR-004 | Combat Reflexes + DEX 8 (mod -1): entity gets 1 AoO (negative DEX mod — no additional AoOs) |
| CR-005 | Combat Reflexes + DEX 14 (mod +2): exactly 3 AoOs allowed; 4th trigger skipped |
| CR-006 | Regression: existing AoO test — single AoO entity still blocked after first use |
| CR-007 | aoo_count_this_round increments correctly on each AoO execution |
| CR-008 | Two different entities with Combat Reflexes: each tracked independently |

---

## Implementation Plan

1. Read `aidm/core/aoo.py` — full file. Map all locations where `aoo_used_this_round` is read or written.
2. Add `aoo_count_this_round` parallel tracking — read from `active_combat`, default `{}`.
3. Replace boolean eligibility checks with count-based checks in both code paths.
4. Find `resolve_aoo_sequence()` — add `aoo_count_this_round` increment wherever `aoo_used_this_round` is updated.
5. Validate flat-footed suppression exists; add bypass if so.
6. Write `tests/test_engine_combat_reflexes_gate.py` with CR-001 through CR-008.
7. Run gate suite: `python -m pytest tests/test_engine_combat_reflexes_gate.py -v`.
8. Run CP-15/CP-18 regression: `python -m pytest tests/test_aoo_kernel.py tests/test_engine_combat_reflexes_gate.py -v`.
9. Run full regression. Confirm 0 new failures.

---

## Integration Seams

- **`aidm/core/aoo.py`** — `check_aoo_triggers()` and `resolve_aoo_sequence()`. No other files.
- **`aidm/schemas/entity_fields.py`** — `EF.FEATS`, `EF.DEX_MOD` already defined. No new constants.
- **`active_combat` dict** — adding `aoo_count_this_round` key. This key is not persisted between rounds — it lives in `active_combat` which is reset each round via the existing round-reset logic. Confirm round-reset clears `active_combat` keys (or that `aoo_count_this_round` is initialized fresh each round like `aoo_used_this_round`).
- **Event constructor:** `Event(event_id=..., event_type=..., timestamp=..., payload=...)` — not relevant for this WO.
- **Class feature pattern:** `entity.get(EF.CLASS_LEVELS, {}).get(...)` — not applicable here; feat check via `EF.FEATS` list.

---

## Assumptions to Validate

1. Confirm `aoo_used_this_round` is a set (not already a dict/counter) in `active_combat` (expected: yes — `set(active_combat.get("aoo_used_this_round", []))`).
2. Confirm `active_combat["aoo_used_this_round"]` is reset each round (expected: yes — verify in `play_loop.py` round-start logic).
3. Confirm no existing flat-footed AoO suppression in `check_aoo_triggers()` (expected: unclear — validate before implementing bypass).
4. Confirm `resolve_aoo_sequence()` is the function that appends to `aoo_used_this_round` (expected: yes — find the add/update call).

---

## Preflight

Before writing any code:
- `grep -n "aoo_used_this_round\|aoo_count" aidm/core/aoo.py` — map all read/write sites
- `grep -n "aoo_used_this_round" aidm/core/play_loop.py` — confirm round-reset location
- `grep -n "flat_footed\|FLAT_FOOTED" aidm/core/aoo.py` — check flat-footed suppression
- `python -m pytest tests/test_aoo_kernel.py -v` — regression baseline (pre-existing failure `test_aoo_usage_resets_each_round` is known)

---

## Delivery Footer

- Files modified: `aidm/core/aoo.py`, `tests/test_engine_combat_reflexes_gate.py` (new)
- Gate: ENGINE-COMBAT-REFLEXES, minimum 8 tests
- Run full regression before filing debrief
- **Debrief Required:** File to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-COMBAT-REFLEXES-001.md`

### Debrief Template

```
# DEBRIEF — WO-ENGINE-COMBAT-REFLEXES-001

**Verdict:** [PASS/FAIL] [N/N]
**Gate:** ENGINE-COMBAT-REFLEXES
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
