# WO-ENGINE-SPELL-SLOTS-001 — Spell Slot Governor

**Issued:** 2026-02-23
**Authority:** PM — Thunder approval (parallel backend track)
**Sequence:** Parallel with WO-ENGINE-REST-001. No UI dependency.
**Gate:** ENGINE-SPELL-SLOTS (new gate, defined below)

---

## 1. Target Lock

Spell slots are initialized at character generation but never decremented during play. Casters can spam unlimited spells with zero resource pressure. This WO installs the slot governor: validate availability before casting, decrement on successful cast, emit sensor events, fail-closed on depletion.

**Done means:** A caster with 0 remaining level-1 slots cannot cast a level-1 spell — intent routes to `SPELL_SLOT_EMPTY` failure event. A successful cast decrements the slot. Slot count is readable from entity state. Gate ENGINE-SPELL-SLOTS passes.

---

## 2. Current State (Survey Findings)

| Item | Current state |
|------|--------------|
| `EF.SPELL_SLOTS` | Dict[int, int] — initialized in chargen, never decremented |
| `_resolve_spell_cast()` in `play_loop.py` | No slot check, no decrement |
| `SpellResolver.validate_cast()` | Checks range/LOS/target — no slot check |
| `EF.SPELLS_KNOWN` / `EF.SPELLS_PREPARED` | Initialized, never validated on cast |
| Dual-caster | `EF.SPELL_SLOTS_2` exists, same gap |

---

## 3. Binary Decisions — Locked

| Decision | Answer |
|----------|--------|
| Where slot check lives | `_resolve_spell_cast()` in `play_loop.py`, before SpellResolver call |
| Where decrement lives | `_resolve_spell_cast()`, after successful `SpellResolver.resolve_spell()` — only on success |
| Cantrips (spell level 0) | Exempt — never decrement (unlimited by convention; slot[0]=999) |
| Dual-caster slot routing | Determine which class knows the spell → decrement correct slot dict (primary or secondary) |
| Slot depletion failure event | `spell_slot_empty` sensor event. Intent treated same as `invalid_intent`. |
| Prepared caster validation | Validate spell is in `EF.SPELLS_PREPARED` for wizard/cleric/druid before cast |
| Known spell validation (spontaneous) | Validate spell is in `EF.SPELLS_KNOWN` for sorcerer/bard before cast |
| Non-caster casting | If `EF.SPELL_SLOTS` absent from entity — `spell_slot_empty` (entity can't cast) |
| Slot state in world state | Mutated in-place in `WorldState.entity_states` — same pattern as condition mutation |
| Gate runner | pytest (same as CP-series) |

---

## 4. Implementation Spec

### 4.1 New helper: `_check_spell_slot()`

Add to `play_loop.py`, near `_resolve_spell_cast()`:

```python
def _check_spell_slot(
    entity_state: Dict[str, Any],
    spell_level: int,
    caster_class: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Returns (ok: bool, reason: str).
    reason is empty string on success.
    Cantrips (level 0) always pass.
    """
    if spell_level == 0:
        return True, ""

    slots: Optional[Dict[int, int]] = entity_state.get(EF.SPELL_SLOTS)
    if slots is None:
        return False, "no_spell_slots"

    available = slots.get(spell_level, 0)
    if available <= 0:
        return False, f"spell_slot_empty_level_{spell_level}"

    return True, ""
```

### 4.2 New helper: `_decrement_spell_slot()`

```python
def _decrement_spell_slot(
    entity_state: Dict[str, Any],
    spell_level: int,
) -> None:
    """
    Decrements entity's spell slot count for the given level.
    Cantrips are no-op. Never goes below 0.
    """
    if spell_level == 0:
        return
    slots: Dict[int, int] = entity_state[EF.SPELL_SLOTS]
    slots[spell_level] = max(0, slots.get(spell_level, 0) - 1)
```

### 4.3 New helper: `_validate_spell_known()`

```python
def _validate_spell_known(
    entity_state: Dict[str, Any],
    spell_name: str,
    spell_level: int,
) -> Tuple[bool, str]:
    """
    Validates spell is in prepared list (prepared casters)
    or known list (spontaneous casters).
    Returns (ok, reason).
    """
    caster_class = entity_state.get(EF.CASTER_CLASS, "")

    PREPARED_CASTERS = {"wizard", "cleric", "druid", "ranger", "paladin"}
    SPONTANEOUS_CASTERS = {"sorcerer", "bard"}

    if caster_class in PREPARED_CASTERS:
        prepared: Dict[int, List[str]] = entity_state.get(EF.SPELLS_PREPARED, {})
        level_list = prepared.get(spell_level, [])
        if spell_name not in level_list and spell_level != 0:
            return False, "spell_not_prepared"

    elif caster_class in SPONTANEOUS_CASTERS:
        known: Dict[int, List[str]] = entity_state.get(EF.SPELLS_KNOWN, {})
        level_list = known.get(spell_level, [])
        if spell_name not in level_list and spell_level != 0:
            return False, "spell_not_known"

    # Unknown caster class or cantrip — allow (fail-open for NPCs/monsters)
    return True, ""
```

### 4.4 Wire into `_resolve_spell_cast()`

In `play_loop.py`, inside `_resolve_spell_cast()`, before the `SpellResolver.validate_cast()` call, add:

```python
# ── Spell slot governor ──────────────────────────────────────────────────────
caster_state = world_state.entity_states.get(intent.caster_id, {})
spell_def = SPELL_REGISTRY.get(intent.spell_name)
spell_level = spell_def.level if spell_def else 0

slot_ok, slot_reason = _check_spell_slot(caster_state, spell_level)
if not slot_ok:
    return [SensorEvent(
        event_id=next_event_id,
        event_type="spell_slot_empty",
        payload={
            "actor_id": intent.caster_id,
            "spell_name": intent.spell_name,
            "spell_level": spell_level,
            "reason": slot_reason,
        },
        timestamp=timestamp,
    )], world_state, None

known_ok, known_reason = _validate_spell_known(caster_state, intent.spell_name, spell_level)
if not known_ok:
    return [SensorEvent(
        event_id=next_event_id,
        event_type="spell_slot_empty",
        payload={
            "actor_id": intent.caster_id,
            "spell_name": intent.spell_name,
            "spell_level": spell_level,
            "reason": known_reason,
        },
        timestamp=timestamp,
    )], world_state, None
# ─────────────────────────────────────────────────────────────────────────────
```

After the SpellResolver resolves successfully (resolution returned, no early return):

```python
# ── Decrement slot post-cast ──────────────────────────────────────────────────
_decrement_spell_slot(caster_state, spell_level)
# ─────────────────────────────────────────────────────────────────────────────
```

### 4.5 Dual-caster routing

For dual-caster entities (those with `EF.SPELL_SLOTS_2`), after the primary slot check fails, check secondary:

```python
# If primary slot empty but secondary caster has the spell:
if not slot_ok and EF.SPELL_SLOTS_2 in caster_state:
    # Check if spell belongs to secondary caster class
    secondary_class = caster_state.get(EF.CASTER_CLASS_2, "")
    slot_ok_2, reason_2 = _check_spell_slot_for_dict(
        caster_state.get(EF.SPELL_SLOTS_2, {}), spell_level
    )
    if slot_ok_2:
        # Use secondary slots
        _decrement_secondary = True
        slot_ok = True
        slot_reason = ""
```

Extract `_check_spell_slot_for_dict(slots_dict, level)` as a pure sub-helper to avoid duplication.

**Note:** For simplicity in this WO, dual-caster routing uses a heuristic: if primary slots are empty for the level, try secondary. A future WO can add explicit spell-to-caster-class routing if needed.

---

## 5. Sensor Event Schema

**`spell_slot_empty`** — emitted when slot check fails:

```json
{
  "event_type": "spell_slot_empty",
  "payload": {
    "actor_id": "string",
    "spell_name": "string",
    "spell_level": 0,
    "reason": "spell_slot_empty_level_1 | spell_not_prepared | spell_not_known | no_spell_slots"
  }
}
```

---

## 6. Gate Spec

**Gate name:** `ENGINE-SPELL-SLOTS`
**Test file:** `tests/test_engine_spell_slots_gate.py`

| # | Test | Check |
|---|------|-------|
| SS-01 | Cast level-1 spell with 1 slot remaining → succeeds, slot decrements to 0 | `entity[EF.SPELL_SLOTS][1] == 0` after cast |
| SS-02 | Cast level-1 spell with 0 slots remaining → `spell_slot_empty` event, no damage | event_type == "spell_slot_empty" |
| SS-03 | Cast cantrip (level-0) with depleted slots → succeeds (unlimited) | no slot check on level 0 |
| SS-04 | Cast level-2 spell, level-1 slots depleted but level-2 available → succeeds | correct level targeted |
| SS-05 | Wizard casts unprepared spell → `spell_slot_empty` with reason "spell_not_prepared" | reason == "spell_not_prepared" |
| SS-06 | Sorcerer casts unknown spell → `spell_slot_empty` with reason "spell_not_known" | reason == "spell_not_known" |
| SS-07 | Non-caster (fighter) has no SPELL_SLOTS field → `spell_slot_empty` with reason "no_spell_slots" | reason == "no_spell_slots" |
| SS-08 | Cleric casts from prepared list with slots available → succeeds, slot decrements | combined check |
| SS-09 | Two sequential casts: first succeeds (slot=1→0), second fails (slot=0) | two-step round |
| SS-10 | Dual-caster: primary level exhausted, secondary has slots → succeeds via secondary | slot decremented from SPELL_SLOTS_2 |
| SS-11 | Slot floor: slot cannot go below 0 (decrement on 0-slot is no-op) | `max(0,...)` guard |
| SS-12 | World state is unchanged on `spell_slot_empty` (no partial mutation) | world_state before == after on failure |

**Test count target:** 12 checks → Gate `ENGINE-SPELL-SLOTS` 12/12.

---

## 7. Dependencies

- `EF.SPELL_SLOTS`, `EF.SPELLS_PREPARED`, `EF.SPELLS_KNOWN`, `EF.CASTER_CLASS` — all exist in entity_fields.py (confirmed)
- `SPELL_REGISTRY` — already loaded in play_loop.py scope
- `SensorEvent` — already used in play_loop.py
- No new files required — all changes in `aidm/core/play_loop.py`

---

## 8. What This WO Does NOT Do

- Does not implement spell slot recovery (that is WO-ENGINE-REST-001)
- Does not implement prepared spell management UI (future WO)
- Does not track bonus spell slot sources (domain spells, metamagic rods) — base slots only
- Does not enforce concentration limits (WO-ENGINE-AOO-WIRE-001 handles concentration break, not the limit)
- Does not validate material components

---

## 9. Preflight

```bash
cd f:/DnD-3.5
python -m pytest tests/test_engine_spell_slots_gate.py -v
# All 12 checks must pass.
# Run full suite: python -m pytest tests/ -x --tb=short
# Zero new regressions expected.
```
