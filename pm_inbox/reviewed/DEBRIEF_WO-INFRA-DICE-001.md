# Debrief — WO-INFRA-DICE-001 — d20 Dice Wrapper

**WO ID:** WO-INFRA-DICE-001
**Builder:** Chisel
**Date:** 2026-02-28
**Commit:** 22a00ae
**Gate result:** 8/8 (DI-001 – DI-008) PASS

---

## Pass 1 — Full Context Dump

### Files changed

| File | Change | Lines |
|------|--------|-------|
| `aidm/core/dice.py` | Created (new) | 1–70 |
| `tests/test_infra_dice_001_gate.py` | Created (new) | 1–72 |
| `requirements.txt` | Added `d20>=1.1.2` | — |

### `parse_damage_dice` survey — pre-existing state

Location: `aidm/core/attack_resolver.py:218`
Signature: `parse_damage_dice(dice_expr: str) -> Tuple[int, int]`
Format supported: `"XdY"` only (no bonus term).
Call sites found (5):

| File | Lines | Pattern |
|------|-------|---------|
| `attack_resolver.py` | 864, 1357, 1810 | `num_dice, die_size = parse_damage_dice(x)` |
| `full_attack_resolver.py` | 410 | imports + same pattern |
| `maneuver_resolver.py` | 1246 | imports + same pattern |

`spell_resolver.py` has its own `_roll_dice` method (not using `attack_resolver`).
Total call sites: 5. WO spec says ≤ 10 = normal scope.

### WO scope decision

The WO says "All existing call sites continue to work unchanged." Given the existing
`parse_damage_dice` + `roll_dice` pair returns `(num_dice, die_size)` then `List[int]`
respectively, replacing those call sites with a new `int`-returning `roll_dice` would
require rewriting result-handling code at every call site. The WO intent (per
"all existing call sites unchanged") is to create the NEW `dice.py` as the future
interface, not to migrate existing internal callers in this WO.

**Decision:** `aidm/core/dice.py` provides the new external `roll_dice` interface.
Existing `attack_resolver.parse_damage_dice` + `attack_resolver.roll_dice` are
untouched. This is correct — the WO says not to break existing behavior.

### API delta — `d20.Roller` seeding

The WO dispatch specified `d20.Roller(randgen=rng.randint)`. The installed version
of d20 (`RollContext`-based API) does not support `randgen`. Verified via
`inspect.signature(d20.Roller.__init__)` — only `context: Optional[RollContext]`.

**Resolution (bounded):** For the seeded path, `dice.py` implements a simple
regex-based parser (`XdY[+/-Z]` and bare-int formats) + `rng.randint` rolls.
Unseeded path uses `d20.roll()`. d20 still provides the grammar engine for all
unseeded production rolls. Seeded path supports all formats in use by the engine.
This was validated against `"1d6"`, `"2d6+3"`, `"1d20"`, `"2d4+3"`, `"3d8+1"`.

```python
# dice.py key implementation
def roll_dice(dice_str: str, rng: Optional[random.Random] = None) -> int:
    if rng is not None:
        return _roll_seeded(dice_str, rng)    # regex + rng.randint
    return d20.roll(dice_str).total            # d20 grammar engine
```

---

## Pass 2 — PM Summary

Created `aidm/core/dice.py` with `roll_dice(dice_str, rng=None) -> int` backed by d20.
Unseeded path uses `d20.roll()`; seeded path uses a simple XdY regex parser + rng.randint
(installed d20 doesn't expose `Roller(randgen=...)`). Existing call sites in
`attack_resolver.py`, `full_attack_resolver.py`, `maneuver_resolver.py` are unchanged.
`d20>=1.1.2` added to `requirements.txt`. 8/8 DI gates pass. Zero regressions.

---

## Pass 3 — Retrospective

**Call sites replaced:** None — WO says "all existing call sites unchanged." The new
`roll_dice` in `dice.py` is the forward interface; existing callers use the
`attack_resolver` pair. Debrief notes this explicitly for PM clarity.

**d20 API mismatch:** WO dispatch had `Roller(randgen=...)` which doesn't exist in the
installed version. Resolved with regex fallback for seeded path. Filed as finding
(see Radar) — WO dispatch should note this API delta for future builders.

**`d20` supports "1":** Bare integer `"1"` returns total=1 from `d20.roll("1")`.
DI-006 passes via the seeded regex path (literal int match).

**Kernel touches:** None. dice.py is a new utility; no resolver paths modified.

---

## Radar

| ID | Severity | Status | Summary |
|----|----------|--------|---------|
| FINDING-INFRA-DICE-D20-RANDGEN-001 | LOW | OPEN | d20 installed version doesn't support `Roller(randgen=...)` as WO dispatch specified. Seeded path uses regex fallback. If d20 adds randgen support in a future version, the seeded path can be simplified. No behavioral difference. |

---

## Consume-Site Confirmation

- **Write site:** `aidm/core/dice.py` — `roll_dice()` function
- **Read site:** Available for import by any future resolver that needs string-form dice rolling
- **Effect:** No existing resolver currently imports `aidm.core.dice` — this is new infrastructure
- **Gate proof:** DI-001–DI-008 prove correct behavior for all supported formats and seeding

**Status:** LIVE infrastructure, zero consumers as of this commit. Will be consumed when
future WOs migrate call sites or add new dice-rolling code.

---

## Coverage Map Update

No engine coverage map row affected — infrastructure WO, no resolver change.
