# WO-ENGINE-CONCENTRATION-001 — Per-Spell Concentration Break (3.5e PHB Correct)

**Issued:** 2026-02-24
**Authority:** Thunder approval (parallel backend sprint)
**Gate:** ENGINE-CONCENTRATION (new gate, defined below)
**Parallel-safe:** Yes — isolated to `_check_concentration_break()` in `play_loop.py` and `duration_tracker.py`. No overlap with GRAPPLE-PIN-001 or SPELL-PREP-001.

---

## 1. Target Lock

`_check_concentration_break()` in `play_loop.py` currently:
1. Fetches only the **first** active concentration effect via `get_concentration_effect()` (singular)
2. Rolls a single Concentration check against DC = 10 + damage + that spell's level
3. On failure, calls `break_concentration()` which drops **all** concentration effects

**PHB 3.5e p.170:** "If the spell requires concentration, you must make a Concentration check (DC 10 + the level of the spell you're trying to cast + the damage dealt) or the spell fails."

For multiple active concentration spells: each requires **its own separate check**. Rolling once and dropping all is wrong. A caster maintaining `Hold Person` (level 2) and `Bless` (level 1) who takes 8 damage should roll:
- Check 1: DC = 10 + 8 + 2 = 20 (for Hold Person)
- Check 2: DC = 10 + 8 + 1 = 19 (for Bless)

Each check is independent. Failing one does not affect the other.

**Done means:** `_check_concentration_break()` iterates all active concentration effects, rolls a separate check per effect, and only drops effects that individually fail. Gate ENGINE-CONCENTRATION 10/10.

---

## 2. Current State

| Location | Current behavior | Correct behavior |
|----------|-----------------|------------------|
| `play_loop.py:_check_concentration_break()` | `get_concentration_effect()` → only first effect | `get_concentration_effects()` → all effects |
| `play_loop.py:_check_concentration_break()` | Single roll for all | One roll per concentration effect |
| `play_loop.py:_check_concentration_break()` | `break_concentration()` drops all on fail | Only drop effects whose individual roll fails |
| `duration_tracker.py` | `break_concentration()` removes all | No change needed — add new per-effect method |

The `DurationTracker` already supports multiple concentration spells (see `get_concentration_effects()` which returns a list). The bug is purely in `_check_concentration_break()`.

---

## 3. Implementation Spec

### 3.1 Add `remove_concentration_effect()` to `DurationTracker`

New method in `aidm/core/duration_tracker.py` (alongside existing `break_concentration`):

```python
def remove_concentration_effect(self, effect_id: str) -> Optional[ActiveSpellEffect]:
    """Remove a single concentration effect by ID.

    Called when a specific concentration spell fails its individual check.
    Does not affect other concentration effects the caster may be maintaining.

    Args:
        effect_id: ID of the specific effect to remove

    Returns:
        Removed effect, or None if not found
    """
    return self.remove_effect(effect_id)
```

### 3.2 Rewrite `_check_concentration_break()` in `play_loop.py`

Replace the current implementation with per-spell iteration:

```python
def _check_concentration_break(
    caster_id: str,
    damage_dealt: int,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """Check if damage breaks concentration on each active spell.

    PHB p.170: Each concentration spell the caster is maintaining requires
    its own separate Concentration check (DC = 10 + damage + spell level).
    Only spells whose individual check fails are dropped.

    Args:
        caster_id: Entity that took damage
        damage_dealt: Amount of damage taken
        world_state: Current world state
        rng: RNG manager
        next_event_id: Next event ID
        timestamp: Event timestamp

    Returns:
        Tuple of (events, updated_world_state)
    """
    events = []
    current_event_id = next_event_id

    duration_tracker = _get_or_create_duration_tracker(world_state)

    # Get all concentration effects (3.5e: caster may have multiple)
    concentration_effects = duration_tracker.get_concentration_effects(caster_id)
    if not concentration_effects:
        return events, world_state

    concentration_bonus = world_state.entities.get(caster_id, {}).get("concentration_bonus", 0)

    for effect in list(concentration_effects):  # list() to avoid mutate-during-iterate
        # Each spell gets its own check (PHB p.170)
        spell_level = getattr(effect, 'spell_level', 0)
        dc = 10 + damage_dealt + spell_level
        roll = rng.stream("combat").randint(1, 20)
        total = roll + concentration_bonus

        if total < dc:
            # This specific spell's concentration broken
            duration_tracker.remove_concentration_effect(effect.effect_id)

            events.append(Event(
                event_id=current_event_id,
                event_type="concentration_broken",
                timestamp=timestamp,
                payload={
                    "caster_id": caster_id,
                    "spell_id": effect.spell_id,
                    "spell_name": effect.spell_name,
                    "target_id": effect.target_id,
                    "dc": dc,
                    "roll": roll,
                    "total": total,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 170}],
            ))
            current_event_id += 1

            # Remove condition applied by this effect
            if effect.condition_applied and effect.target_id:
                events.append(Event(
                    event_id=current_event_id,
                    event_type="condition_removed",
                    timestamp=timestamp,
                    payload={
                        "entity_id": effect.target_id,
                        "condition": effect.condition_applied,
                        "reason": "concentration_broken",
                    },
                ))
                current_event_id += 1
        else:
            # Check passed — this spell continues; emit check event for audit trail
            events.append(Event(
                event_id=current_event_id,
                event_type="concentration_check",
                timestamp=timestamp,
                payload={
                    "caster_id": caster_id,
                    "spell_id": effect.spell_id,
                    "spell_name": effect.spell_name,
                    "dc": dc,
                    "roll": roll,
                    "total": total,
                    "maintained": True,
                },
                citations=[{"source_id": "681f92bc94ff", "page": 170}],
            ))
            current_event_id += 1

    # Persist updated duration tracker
    active_combat = deepcopy(world_state.active_combat) if world_state.active_combat else {}
    active_combat["duration_tracker"] = duration_tracker.to_dict()
    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=world_state.entities,
        active_combat=active_combat,
        narrative_context=world_state.narrative_context,
        scene_type=world_state.scene_type,
    )

    return events, updated_state
```

### 3.3 RNG Stream Consumption Note

Each concentration effect now consumes one `rng.stream("combat").randint(1, 20)` call. In a round where a caster takes damage while maintaining 2 concentration spells, 2 RNG draws are consumed (in iteration order: by `effect_id` insertion order, as the dict preserves insertion order in Python 3.7+).

**Test fixtures** that involve concentration break must account for this: if the test entity has 1 concentration spell, behavior is identical to current (1 roll). Tests with 0 concentration spells see no change.

### 3.4 No Changes Required

- `duration_tracker.break_concentration()` — retained for other callers (dispel, etc.)
- The AoO-path concentration check in play_loop.py (around line 1480) — that's the CP-23 pre-cast check, uses a different code path (inline roll, not `_check_concentration_break`). Leave untouched.
- Event type names — `concentration_broken` and `concentration_check` are unchanged

---

## 4. Gate Spec

**Gate name:** `ENGINE-CONCENTRATION`
**Test file:** `tests/test_engine_concentration_gate.py`

| # | Test | Check |
|---|------|-------|
| CC-01 | Caster with 0 concentration spells takes damage → no concentration events emitted | `_check_concentration_break` returns `[]` |
| CC-02 | Caster with 1 concentration spell, roll fails DC → `concentration_broken` event emitted, spell dropped | 1 concentration_broken event |
| CC-03 | Caster with 1 concentration spell, roll passes DC → `concentration_check` event with `maintained=True`, spell not dropped | effect still in tracker |
| CC-04 | Caster with 2 concentration spells, both rolls fail → 2 `concentration_broken` events, both dropped | 2 broken events |
| CC-05 | Caster with 2 concentration spells, roll 1 fails / roll 2 passes → 1 broken + 1 check(maintained), only first dropped | 1 broken, 1 remaining |
| CC-06 | DC correctness: damage=8, spell_level=2 → DC=20 verified in event payload | payload.dc == 20 |
| CC-07 | DC correctness: damage=8, spell_level=1 → DC=19 verified in event payload | payload.dc == 19 |
| CC-08 | Each spell gets its own RNG draw (2 spells → 2 RNG calls in "combat" stream) | seed-based determinism: known seed → known rolls |
| CC-09 | `condition_removed` emitted for broken effect that had `condition_applied` set | event_type == "condition_removed" in events |
| CC-10 | Zero regressions on CP-23 gate (10/10) and existing concentration tests | full suite |

**Test count target:** 10 checks → Gate `ENGINE-CONCENTRATION` 10/10.

---

## 5. What This WO Does NOT Do

- Does not change the CP-23 AoO pre-cast concentration check (different code path, single roll, correct)
- Does not implement action-to-maintain mechanics (no "sustain action" system)
- Does not add saving throw entries for concentration (no Concentration skill — that's 5e)
- Does not add CON-mod-based concentration DCs (PHB 3.5e uses raw die + bonus, not CON-mod save)

---

## 6. Preflight

```bash
cd f:/DnD-3.5
python -m pytest tests/test_engine_concentration_gate.py -v
# CC-01 through CC-10 must pass.
python -m pytest tests/ -x --tb=short
# Zero new regressions.
```
