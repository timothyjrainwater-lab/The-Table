# WO-ENGINE-BARDIC-DURATION-001 — Bardic Duration: Bard Incapacitation Auto-Ends Inspire Courage

**Issued:** 2026-02-24
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** LOW (FINDING-BARDIC-DURATION-001 — functional gap; Inspire Courage persists even after bard death/silence)
**WO type:** BUG (missing enforcement)
**Gate:** ENGINE-BARDIC-DURATION (10 tests)

---

## 1. Target Lock

**What works:** `tick_inspire_courage()` in `bardic_music_resolver.py` is already wired in `play_loop.py` at turn-end (line 2876). It decrements `INSPIRE_COURAGE_ROUNDS_REMAINING` each round and clears the bonus when it reaches 0. The 8-round flat duration is live.

**What's missing:** PHB p.29 — Inspire Courage requires the bard to maintain it as a free action each round. If the bard becomes **incapable** of performing (dead, unconscious, silenced/DEAFENED while verbal component required, or has the CONFUSED condition), Inspire Courage ends immediately. Currently, `INSPIRE_COURAGE_ACTIVE=True` persists regardless of bard state — a dead bard keeps buffing allies indefinitely.

**Root cause (confirmed by PM inspection):**
- `tick_inspire_courage()` decrements duration and checks `INSPIRE_COURAGE_ACTIVE` on target entities
- It does **not** check the bard entity's current state (alive, conscious, capable of maintaining)
- `activate_rage` and similar class features correctly gate on entity state — Inspire Courage does not

**PHB reference:** PHB p.29 — "The bard must be able to perform the bardic music ability (see above) to use this ability." PHB p.84 — DEAFENED prevents verbal components. Dying/unconscious bards cannot perform.

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | Where does the incapacitation check live? | In `tick_inspire_courage()` in `bardic_music_resolver.py`. The tick function already iterates all entities — add a bard-state check before decrementing. |
| 2 | Which bard states terminate Inspire Courage? | Three: (1) bard entity is DYING or has HP ≤ 0 (`EF.DYING=True` or `EF.HP_CURRENT ≤ 0`). (2) bard entity is UNCONSCIOUS condition. (3) bard entity is DEAFENED condition. CONFUSED is edge case — defer (8-round flat is safer than phantom silence). |
| 3 | How does tick_inspire_courage know which entity is the bard? | Add `bard_id` field to the active effect. Store `INSPIRE_COURAGE_BARD_ID` on each buffed entity at activation time. Tick function reads that field to look up the bard entity in world_state. |
| 4 | New EF field required? | Yes: `EF.INSPIRE_COURAGE_BARD_ID` (str) — set at activation, read at tick, cleared at expiry. |
| 5 | New event type? | Yes: `inspire_courage_interrupted` — emitted when bard becomes incapacitated, distinct from `inspire_courage_end` (normal duration expiry). |
| 6 | Does this affect activation? | No. Only the tick check changes. Activation (`resolve_bardic_music`) is unchanged except it now also sets `INSPIRE_COURAGE_BARD_ID`. |
| 7 | PHB maintenance as explicit free action (bard declares each round)? | **Deferred.** That requires intent-based confirmation each round — significant action-economy surface. The incapacitation check covers the only game-relevant failure mode. The 8-round flat duration is retained as the nominal case. |

---

## 3. Contract Spec

### New EF constant in `aidm/schemas/entity_fields.py`

```python
INSPIRE_COURAGE_BARD_ID = "inspire_courage_bard_id"
# str: entity_id of the bard who activated this Inspire Courage effect.
# Set on each buffed target at activation. Read by tick_inspire_courage() to
# check bard incapacitation. Cleared when effect expires or is interrupted.
```

### Modification: `resolve_bardic_music()` in `aidm/core/bardic_music_resolver.py`

In the ally-buffing loop, add one line alongside the existing field assignments:
```python
target[EF.INSPIRE_COURAGE_BARD_ID] = intent.actor_id
```

Also set on the bard entity itself (bard is their own ally):
```python
actor[EF.INSPIRE_COURAGE_BARD_ID] = intent.actor_id
```

### Modification: `tick_inspire_courage()` in `aidm/core/bardic_music_resolver.py`

After confirming an entity has `INSPIRE_COURAGE_ACTIVE=True`, check the bard:

```python
def _bard_is_incapacitated(bard_id: str, entities: dict) -> bool:
    """Return True if bard cannot maintain Inspire Courage this round."""
    if not bard_id or bard_id not in entities:
        return True  # Bard left the scene — end the effect
    bard = entities[bard_id]
    # Dead or dying
    if bard.get(EF.HP_CURRENT, 1) <= 0:
        return True
    if bard.get(EF.DYING, False):
        return True
    # Unconscious condition
    conditions = bard.get(EF.CONDITIONS, {})
    if isinstance(conditions, dict):
        if "unconscious" in conditions or "UNCONSCIOUS" in conditions:
            return True
        if "deafened" in conditions or "DEAFENED" in conditions:
            return True
    return False
```

In the main loop of `tick_inspire_courage()`, before the decrement logic:

```python
bard_id = entity.get(EF.INSPIRE_COURAGE_BARD_ID, "")
if _bard_is_incapacitated(bard_id, entities):
    # Bard cannot maintain — interrupt immediately (not normal expiry)
    entity[EF.INSPIRE_COURAGE_ACTIVE] = False
    entity[EF.INSPIRE_COURAGE_BONUS] = 0
    entity[EF.INSPIRE_COURAGE_ROUNDS_REMAINING] = 0
    entity[EF.INSPIRE_COURAGE_BARD_ID] = ""
    interrupted_ids.append(eid)
    continue
```

Emit `inspire_courage_interrupted` event (one event per bard, not per target — group by bard_id):

```python
Event(
    event_id=current_event_id,
    event_type="inspire_courage_interrupted",
    timestamp=timestamp,
    payload={
        "bard_id": bard_id,
        "reason": "bard_incapacitated",
        "affected_entity_ids": [list of interrupted_ids for this bard],
    },
    citations=[],
)
```

Retain the existing `inspire_courage_end` event for normal duration expiry. Do not change it.

### No changes to `play_loop.py`

The tick is already wired at line 2876. No routing changes needed.

---

## 4. Implementation Plan

### Step 1 — `aidm/schemas/entity_fields.py`
Add `INSPIRE_COURAGE_BARD_ID = "inspire_courage_bard_id"` alongside the other bardic EF constants.

### Step 2 — `aidm/core/bardic_music_resolver.py`
1. Add `_bard_is_incapacitated(bard_id, entities)` private helper (~10 lines)
2. In `resolve_bardic_music()`: set `EF.INSPIRE_COURAGE_BARD_ID = intent.actor_id` on each buffed entity (including the bard)
3. In `tick_inspire_courage()`: add incapacitation check before decrement; emit `inspire_courage_interrupted` events grouped by bard_id; clear `INSPIRE_COURAGE_BARD_ID` on expiry/interruption

### Step 3 — Tests (`tests/test_engine_bardic_duration_gate.py`)
Gate: ENGINE-BARDIC-DURATION — 10 tests

| Test | Description |
|------|-------------|
| BD-01 | Normal duration: Inspire Courage decrements each round, ends at round 8 — `inspire_courage_end` emitted |
| BD-02 | Bard dies mid-combat → `inspire_courage_interrupted` emitted on next tick, allies lose bonus immediately |
| BD-03 | Bard goes UNCONSCIOUS → `inspire_courage_interrupted` emitted on next tick |
| BD-04 | Bard goes DEAFENED → `inspire_courage_interrupted` emitted on next tick |
| BD-05 | Bard leaves world_state (removed entity) → `inspire_courage_interrupted` emitted (bard not found) |
| BD-06 | Two bards active — bard A dies, bard B's effect continues; only bard A's targets interrupted |
| BD-07 | `INSPIRE_COURAGE_BARD_ID` set correctly on all ally targets at activation |
| BD-08 | After interruption: `INSPIRE_COURAGE_ACTIVE=False`, `INSPIRE_COURAGE_BONUS=0`, `INSPIRE_COURAGE_BARD_ID=""` on all affected entities |
| BD-09 | Bard at exactly 0 HP (disabled, not dying) → interrupted (PHB: 0 HP = disabled, cannot perform) |
| BD-10 | Regression: existing ENGINE-BARDIC-MUSIC 10/10 still pass after changes |

---

## Integration Seams

**Files touched:**
- `aidm/schemas/entity_fields.py` — 1 new constant
- `aidm/core/bardic_music_resolver.py` — `_bard_is_incapacitated()` helper, `resolve_bardic_music()` bard_id set, `tick_inspire_courage()` incapacitation branch

**Files NOT touched:**
- `aidm/core/play_loop.py` — tick already wired; no changes needed

**Event constructor signature (mandatory):**
```python
Event(
    event_id=<int>,
    event_type=<str>,
    payload=<dict>,
    timestamp=<float>,
    citations=[],
)
```
NOT `id=`, `type=`, `data=`.

**Entity field pattern (mandatory):**
```python
entity.get(EF.CLASS_LEVELS, {}).get("bard", 0)  # bard level check
entity.get(EF.INSPIRE_COURAGE_BARD_ID, "")       # bard_id field
```
`EF.CLASS_FEATURES` does **not** exist.

**Condition name casing:** The conditions dict may use lowercase or uppercase keys depending on how the condition was applied. Check both: `"deafened" in conditions or "DEAFENED" in conditions`. Do not assume either casing exclusively.

**HP_CURRENT ≤ 0 is the incapacitation threshold.** Do not use entity_defeated check — a disabled bard (HP=0, not dying) also cannot perform.

---

## Assumptions to Validate

1. `EF.DYING` exists and is set to `True` on entities in the dying state — confirmed by WO-ENGINE-DEATH-DYING-001 implementation
2. `EF.INSPIRE_COURAGE_ACTIVE`, `EF.INSPIRE_COURAGE_BONUS`, `EF.INSPIRE_COURAGE_ROUNDS_REMAINING` all exist — confirmed by ENGINE-BARDIC-MUSIC gate tests
3. The tick is called at turn-end (not round-end) — confirmed by PM inspection (play_loop.py line 2876). This means the incapacitation check fires once per turn, not once per round — acceptable
4. `tick_inspire_courage` receives a full `WorldState` with all entities — confirmed by function signature

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_barbarian_rage.py tests/test_engine_play_loop_routing_gate.py -x -q
```
Green before touching any file.

After implementation:
```bash
python -m pytest tests/test_engine_bardic_duration_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```
Gate passes at 10/10. ENGINE-BARDIC-MUSIC 10/10 unchanged.

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/schemas/entity_fields.py` — `INSPIRE_COURAGE_BARD_ID` constant
- [ ] `aidm/core/bardic_music_resolver.py` — `_bard_is_incapacitated()`, bard_id set in activation, incapacitation branch in tick
- [ ] `tests/test_engine_bardic_duration_gate.py` — 10/10

**Gate:** ENGINE-BARDIC-DURATION 10/10
**Regression bar:** ENGINE-BARDIC-MUSIC 10/10 unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-BARDIC-DURATION-001.md` on completion.

**Three-pass format:**

**Pass 1 — Full context dump:**
- Per-file breakdown: every file touched, functions added/modified, line counts
- Key findings: anything discovered during implementation not in the WO
- Open findings table: any new gaps found

**Pass 2 — PM summary (≤100 words):**
- Gate result, regression result, any open findings

**Pass 3 — Retrospective:**
- Drift caught, pattern notes, recommendations

Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

After filing the debrief:
```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
