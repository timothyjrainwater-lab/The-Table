# WO-ENGINE-DIVINE-HEALTH-001 — Paladin Divine Health: Immunity to Disease

**Issued:** 2026-02-26
**Lifecycle:** DISPATCH-READY
**Track:** ENGINE
**Priority:** MEDIUM (FINDING-COVERAGE-MAP-001 — paladin class feature absent; paladins contract diseases silently)
**WO type:** BUG (class feature absent)
**Gate:** ENGINE-DIVINE-HEALTH (8 tests)

---

## 1. Target Lock

**What works:** `aidm/core/poison_disease_resolver.py` handles disease application and tick. It is not locked. `EF.CLASS_LEVELS` pattern confirmed. Disease application has a clear entry point where an immunity check can be inserted.

**What's missing:** PHB p.44 — "At 3rd level, a paladin is immune to all diseases, including supernatural and magical diseases." A paladin who reaches level 3 contracts diseases silently through the existing disease resolver. Zero enforcement.

**Root cause:** Never implemented. One guard at disease application entry point. Trivial scope.

**PHB reference:** PHB p.44 — Divine Health: "Beginning at 3rd level, a paladin is immune to all diseases, including supernatural and magical diseases (such as mummy rot and lycanthropy)."

---

## 2. Binary Decisions

| # | Decision | Answer |
|---|----------|--------|
| 1 | New EF field or check CLASS_LEVELS at resolution time? | Check `CLASS_LEVELS` at resolution time — no new field needed. `paladin_level >= 3` is the condition. Same pattern as other class feature checks throughout the engine. |
| 2 | Where to insert? | In `poison_disease_resolver.py`, at the disease application function — before the disease is added to `EF.ACTIVE_DISEASES`. If paladin level ≥ 3, return a `disease_immunity` event and skip application. |
| 3 | Does it apply to disease ticks too? | Yes — belt-and-suspenders. If a paladin somehow has an ACTIVE_DISEASE entry (pre-WO entity), the tick should also check and clear it. Add the same guard at tick time. |
| 4 | Does it apply to poison? | No — PHB is explicit: disease only. Poison immunity is a separate paladin feature at level 9 (out of scope). |
| 5 | Event on immunity? | Yes — emit `disease_immunity` event with actor_id and disease name, so the player gets feedback. |

---

## 3. Contract Spec

### Modification: `aidm/core/poison_disease_resolver.py` — disease application

At the function that applies a new disease to an entity, before adding to `EF.ACTIVE_DISEASES`, insert:

```python
# WO-ENGINE-DIVINE-HEALTH-001: Paladin Divine Health — immune to all diseases at level 3+
_paladin_level = target_entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
if _paladin_level >= 3:
    events.append(Event(
        event_id=current_event_id,
        event_type="disease_immunity",
        timestamp=timestamp,
        payload={
            "actor_id": intent.target_id,
            "disease": disease_name,
            "reason": "divine_health",
        },
        citations=["PHB p.44"],
    ))
    return events, world_state  # Disease not applied
```

### Modification: `aidm/core/poison_disease_resolver.py` — disease tick

At the tick function that processes `EF.ACTIVE_DISEASES` each round/day, add a guard:

```python
# WO-ENGINE-DIVINE-HEALTH-001: Clear any pre-existing disease on paladin 3+
_paladin_level = entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
if _paladin_level >= 3 and entity.get(EF.ACTIVE_DISEASES):
    entity[EF.ACTIVE_DISEASES] = []  # Divine Health clears all diseases
    # Optionally emit disease_immunity event for each cleared disease
```

---

## 4. Implementation Plan

### Step 1 — `aidm/core/poison_disease_resolver.py`
Builder reads the file, locates the disease application function and the disease tick function. Inserts the two guard blocks as specified. No other files touched.

### Step 2 — Tests (`tests/test_engine_divine_health_gate.py`)
Gate: ENGINE-DIVINE-HEALTH — 8 tests

| Test | Description |
|------|-------------|
| DH-01 | Paladin level 3+: disease application blocked, `disease_immunity` event emitted |
| DH-02 | Paladin level 2: disease applied normally (below threshold) |
| DH-03 | Non-paladin: disease applied normally |
| DH-04 | Paladin level 5: supernatural disease also blocked (no type distinction) |
| DH-05 | `disease_immunity` event payload: actor_id, disease name, reason="divine_health" |
| DH-06 | Paladin with pre-existing disease (from before level 3): tick clears it at level 3+ |
| DH-07 | Paladin immunity does NOT affect poison (poison tick proceeds normally for paladin) |
| DH-08 | Regression: ENGINE-POISON-DISEASE 10/10 unchanged |

---

## Integration Seams

**Files touched:**
- `aidm/core/poison_disease_resolver.py` — 2 guard blocks (~8 lines each)

**Files NOT touched:**
- `aidm/schemas/entity_fields.py` — no new fields
- `aidm/schemas/intents.py` — no new intent (passive ability, not player-declared)
- `aidm/core/play_loop.py` — no routing change needed

**Event constructor signature (mandatory):**
```python
Event(event_id=<int>, event_type=<str>, payload=<dict>, timestamp=<float>, citations=[])
```

**CLASS_LEVELS pattern (mandatory):**
```python
entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0)
```

**Disease fields:** Builder must confirm exact field names — `EF.ACTIVE_DISEASES` (list) and the disease application function name — from the existing file before writing.

---

## Assumptions to Validate

1. `EF.ACTIVE_DISEASES` is the field name for active disease list — confirm from entity_fields.py and poison_disease_resolver.py
2. Disease application function is a single entry point (not multiple scattered callsites) — confirm
3. Disease tick function is separate from the application function — confirm
4. `EF.CLASS_LEVELS` is on the target entity at disease application time — confirmed pattern throughout

---

## Preflight

```bash
python scripts/verify_session_start.py
python -m pytest tests/test_engine_gate_poison_disease.py -x -q
```

After implementation:
```bash
python -m pytest tests/test_engine_divine_health_gate.py -v
python -m pytest tests/ -x -q --tb=short 2>&1 | tail -20
```

---

## Delivery Footer

**Deliverables:**
- [ ] `aidm/core/poison_disease_resolver.py` — 2 guard blocks
- [ ] `tests/test_engine_divine_health_gate.py` — 8/8

**Gate:** ENGINE-DIVINE-HEALTH 8/8
**Regression bar:** ENGINE-POISON-DISEASE 10/10 unchanged. No new failures.

---

## Debrief Required

Builder files debrief to `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-DIVINE-HEALTH-001.md` on completion.

Three-pass format. Missing debrief or missing Pass 3 = REJECT.

---

## Audio Cue

```bash
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
