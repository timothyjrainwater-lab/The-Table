# DEBRIEF — WO-ENGINE-WILDSHAPE-DURATION-001
**Dispatched:** 2026-02-25
**Gate:** ENGINE-WILDSHAPE-DURATION 10/10 PASS
**Regression:** ENGINE-WILD-SHAPE 10/10 unchanged. No new failures.

---

## Pass 1 — Per-File Breakdown

### `aidm/schemas/entity_fields.py`

Added one constant:
```python
WILD_SHAPE_ROUNDS_REMAINING = "wild_shape_rounds_remaining"
# Int: combat proxy countdown (druid_level × 10); auto-revert at 0 (WO-ENGINE-WILDSHAPE-DURATION-001)
```
`WILD_SHAPE_HOURS_REMAINING` comment updated to note it is the PHB display value, unchanged.

### `aidm/core/wild_shape_resolver.py`

**`resolve_wild_shape()`:** Added one line after `WILD_SHAPE_HOURS_REMAINING` assignment:
```python
actor[EF.WILD_SHAPE_ROUNDS_REMAINING] = druid_level * 10
```

**`resolve_revert_form()`:** Added one line alongside `WILD_SHAPE_HOURS_REMAINING = 0`:
```python
actor[EF.WILD_SHAPE_ROUNDS_REMAINING] = 0
```

**`tick_wild_shape_duration()` (new function, ~55 lines):** Two-pass design:
- Pass 1: decrement all active entities, collect expired IDs
- Pass 2: emit `wild_shape_expired` event + call `resolve_revert_form()` for each expired entity

**Key finding — two-pass requirement:** The spec draft showed a single-pass loop that called `resolve_revert_form()` mid-iteration and reassigned `ws` inside the loop. This caused a bug: `resolve_revert_form()` deepcopies the WorldState at the moment of the call, before subsequent entities in the same tick have been decremented. Their decrements were written to the original deepcopy dict but never committed into the returned `ws`. Two-pass design (decrement all, then revert all) fixes this cleanly.

**Open findings table:**

| ID | Severity | Finding | Status |
|----|----------|---------|--------|
| WSD-F1 | BUG (fixed) | Single-pass mid-loop WorldState reassignment loses decrements for entities processed after the first expiry | Fixed via two-pass design |
| WSD-F2 | INFO | Spec draft showed WorldState rebuild inside expiry branch; not needed in two-pass design | No impact |

### `aidm/core/play_loop.py`

Added round-end wire after `resolve_dying_tick()` block:
```python
# WO-ENGINE-WILDSHAPE-DURATION-001: Wild Shape duration auto-revert
_has_ws = any(
    e.get(EF.WILD_SHAPE_ACTIVE, False)
    for e in world_state.entities.values()
)
if _has_ws:
    from aidm.core.wild_shape_resolver import tick_wild_shape_duration
    _wsd_events, world_state = tick_wild_shape_duration(
        world_state=world_state,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.6,
    )
    events.extend(_wsd_events)
    current_event_id += len(_wsd_events)
```

Timestamp offset `+0.6` places this after dying tick (`+0.5`) per the spec convention.

---

## Pass 2 — PM Summary (≤100 words)

WO-ENGINE-WILDSHAPE-DURATION-001 delivered. New field `WILD_SHAPE_ROUNDS_REMAINING` (druid_level × 10) set at transform, zeroed at revert. New `tick_wild_shape_duration()` function decrements counter at round-end; at 0, emits `wild_shape_expired` then calls `resolve_revert_form()`. Wired into play_loop round-end block at timestamp +0.6. One structural bug caught during build: spec's single-pass mid-loop WorldState reassignment loses decrements for non-expiring entities in multi-druid combat. Fixed with two-pass design. 10/10 gate tests pass including multi-druid independent expiry. 10/10 ENGINE-WILD-SHAPE regression clean.

---

## Pass 3 — Retrospective

**Drift caught:**
- **WSD-F1 (significant):** The spec's `tick_wild_shape_duration()` pseudocode used a single loop that called `resolve_revert_form()` and reassigned `ws` mid-iteration. This is the same class of mutation-commit bug as the bardic tick non-expiry ghost caught in WO-ENGINE-BARDIC-DURATION-001 dispatch. The two-pass pattern (decrement all → revert expired) is the correct idiom for this codebase's immutable WorldState pattern and should be canonical for all future tick functions that may trigger reverts.

**Patterns:**
- This is the third tick function in the codebase (after `tick_inspire_courage` and `resolve_dying_tick`). All three have now encountered the same mutation-commit hazard in some form. Recommendation below.
- The `_has_ws` guard in play_loop (lazy-import + any() check) is clean and matches the dying_resolver pattern. Consistent.
- The `wild_shape_expired` / `wild_shape_end` dual-event pattern (expired = timeout, end = voluntary) is a good consumer API. Future UI/narration consumers can distinguish cause without inspecting payload.

**Recommendations:**
- **Tick function invariant:** Any function that iterates entities and may call a resolver mid-loop that reassigns `ws` MUST use a two-pass design: collect mutation targets in pass 1, apply mutations/resolvers in pass 2. This should be documented as an architectural rule (ARCH-TICK-001 or similar) to prevent this class of bug on the fourth tick function.
- The `timestamp + 0.01` offset used inside `tick_wild_shape_duration()` for the revert call is minor but should be documented — it ensures the `wild_shape_expired` event and `wild_shape_end` event have distinct timestamps for log ordering. If a third event is ever inserted between them, the offset needs to increase.
- WSD-09 (no-tick guard) passed but the `_has_ws` check in play_loop is doing the guard work. The tick function itself handles an empty-loop gracefully. This is double-guarded and correct — both layers are intentional.
