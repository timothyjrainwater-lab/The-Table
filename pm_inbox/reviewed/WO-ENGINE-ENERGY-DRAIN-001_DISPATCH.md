# WO-ENGINE-ENERGY-DRAIN-001

**Status:** DISPATCH
**Gate:** ENGINE-ENERGY-DRAIN 10/10
**PHB ref:** p.215-216
**Blocks:** nothing
**Blocked by:** nothing
**Parallel-safe with:** WO-ENGINE-TURN-UNDEAD-001

---

## §1 Target Lock

**Gap:** Energy drain (negative levels) is the signature attack of wights, vampires, and spectres. No resolver, no entity field, no intent exists for it. `EF.HP_MAX`, `EF.HD_COUNT`, `EF.SAVE_FORT`, `EF.SPELL_SLOTS` all exist. `NonlethalAttackIntent` in `aidm/schemas/attack.py` (lines 138-174) is the exact pattern to mirror.

**Affected files (new):**
- `aidm/schemas/entity_fields.py` — add 1 constant
- `aidm/schemas/attack.py` — add `EnergyDrainAttackIntent`
- `aidm/core/energy_drain_resolver.py` — new module
- `aidm/core/attack_resolver.py` — call site after hit confirmed
- `aidm/core/play_loop.py` — no new routing block needed (piggybacks on AttackIntent path)

---

## §2 PHB Rule (p.215-216)

**Energy Drain (PHB p.215-216, Glossary):**

Some undead (wights, vampires, spectres, shadows, wraiths) bestow **negative levels** on successful melee touch or natural attacks.

**Each negative level imposes (PHB p.215):**
- −1 penalty to all attack rolls
- −1 penalty to all saving throws
- −1 penalty to all skill checks and ability checks
- −1 effective caster level (lose 1 highest available spell slot if spellcaster)
- Loss of 5 hit points (HP_MAX reduced by 5)

**Death threshold:** If a living creature gains negative levels equal to or exceeding its total HD (character level), it dies immediately.

**24-hour save (PHB p.215):** After 24 hours, the afflicted creature must make a Fortitude save (DC = 10 + ½ drainer's HD + drainer's CHA modifier) for each negative level. Success: level restored. Failure: level becomes permanent (actual class level lost). This 24-hour mechanic is **deferred** to §8.

**Sources:**
- Wight: 1 negative level on successful slam attack
- Vampire: 2 negative levels on successful slam attack
- Spectre: 1 negative level on successful incorporeal touch
- Shadow: Permanent STR drain (different mechanic — NOT covered in this WO)

---

## §3 New Entity Fields

Add to `aidm/schemas/entity_fields.py` after the `IS_UNDEAD` entry (add after TURN_UNDEAD block, or after NONLETHAL_DAMAGE at line 160 if TURN-UNDEAD-001 not yet landed):

```python
# --- Energy Drain (WO-ENGINE-ENERGY-DRAIN-001) ---
NEGATIVE_LEVELS = "negative_levels"  # Int: accumulated temporary negative levels. 0 = none.
```

**Default value:** `0`. No other fields are needed — penalties are computed dynamically from the count.

---

## §4 Implementation Spec

### §4.1 — New Intent: EnergyDrainAttackIntent

In `aidm/schemas/attack.py`, add after `NonlethalAttackIntent` (after line 174):

```python
@dataclass
class EnergyDrainAttackIntent:
    """Intent to perform an energy drain attack (bestows negative levels on hit).

    PHB p.215-216: Used by undead with energy drain supernatural ability
    (wights, vampires, spectres). Standard attack mechanics first; on hit,
    apply N negative levels to the target.

    Goes in attack.py (not intents.py) — same pattern as NonlethalAttackIntent.

    WO-ENGINE-ENERGY-DRAIN-001
    """

    attacker_id: str
    """Entity performing the energy drain attack."""

    target_id: str
    """Entity being attacked."""

    attack_bonus: int
    """Total attack bonus for the underlying attack roll."""

    weapon: "Weapon"
    """Natural weapon used (claw, slam, incorporeal touch, etc.)."""

    negative_levels_per_hit: int = 1
    """Number of negative levels bestowed on a successful hit. Wight=1, Vampire=2."""

    def __post_init__(self):
        if not self.attacker_id:
            raise ValueError("attacker_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if self.negative_levels_per_hit < 1:
            raise ValueError("negative_levels_per_hit must be >= 1")
```

**No action economy mapping needed** — `EnergyDrainAttackIntent` is not routed through `parse_intent()` / `TurnUndeadIntent`. It is constructed directly by the AI/DM layer as an attack variant. Action economy is consumed by the standard attack path that calls into it.

### §4.2 — New Module: `aidm/core/energy_drain_resolver.py`

**`get_negative_level_attack_penalty(entity) -> int`**
- Return `entity.get(EF.NEGATIVE_LEVELS, 0) * -1`
- Called from attack_resolver.py alongside existing condition modifier lookups

**`get_negative_level_save_penalty(entity) -> int`**
- Return `entity.get(EF.NEGATIVE_LEVELS, 0) * -1`
- Called from spell_resolver.py save resolution alongside existing condition modifier lookups

**`_check_energy_drain_death(target) -> bool`**
- `neg_levels = target.get(EF.NEGATIVE_LEVELS, 0)`
- `effective_hd = target.get(EF.HD_COUNT, 1)`
- Return `neg_levels >= effective_hd`

**`_drain_spell_slot(target) -> int | None`**
- Find highest spell level where `target[EF.SPELL_SLOTS][level] > 0`
- If found: decrement that slot by 1, return that level (for event payload)
- If no slots (non-caster or all empty): return `None`
- Also checks `EF.SPELL_SLOTS_2` for dual-caster (drain from primary first)

**`resolve_energy_drain(intent, world_state, rng, next_event_id, timestamp) -> list[Event]`**

1. **Run underlying attack resolution first:**
   Construct an `AttackIntent(attacker_id, target_id, attack_bonus, weapon)` from the `EnergyDrainAttackIntent` fields and call `resolve_attack()`. Collect events.

2. **Check if hit:** scan returned events for `attack_roll` event with `payload["hit"] == True`.

3. **If miss:** return attack events only. No negative levels applied.

4. **If hit:** for each of `intent.negative_levels_per_hit` negative levels:
   - Emit `negative_levels_applied` event (see §5)
   - Compute `hp_max_reduced_by = 5` (fixed per PHB p.215)
   - Call `_drain_spell_slot(target)` → `spell_slot_lost`

5. **Check death:** if `_check_energy_drain_death(target_after_drain)` → emit `energy_drain_death` event.

6. Return all events (attack events + drain events).

**`apply_energy_drain_events(events, world_state) -> WorldState`**

- On `negative_levels_applied`:
  - `entity[EF.NEGATIVE_LEVELS] = entity.get(EF.NEGATIVE_LEVELS, 0) + payload["negative_levels_added"]`
  - `entity[EF.HP_MAX] = entity[EF.HP_MAX] - payload["hp_max_reduced_by"]`
  - If `payload["spell_slot_lost"]` is not None: decrement `entity[EF.SPELL_SLOTS][payload["spell_slot_lost"]]` by 1
  - Clamp `entity[EF.HP_CURRENT]` to new HP_MAX if it exceeds it
- On `energy_drain_death`: set `entity[EF.DEFEATED] = True`, `entity[EF.HP_CURRENT] = -10`
- Return updated WorldState (deepcopy pattern)

### §4.3 — attack_resolver.py Integration

In `aidm/core/attack_resolver.py`, add the integration in two places:

**Attack bonus assembly** (around line 273, where `attack_bonus_with_conditions` is built):

```python
# WO-ENGINE-ENERGY-DRAIN-001: negative level attack penalty
from aidm.core.energy_drain_resolver import get_negative_level_attack_penalty
negative_level_penalty = get_negative_level_attack_penalty(attacker)
attack_bonus_with_conditions += negative_level_penalty
```

This is additive — no existing logic changes. The import can be a function-level import to avoid circularity.

**Hit branch** — after the existing HP resolution and before `apply_attack_events` is called, check if the intent is an `EnergyDrainAttackIntent`:

```python
from aidm.schemas.attack import EnergyDrainAttackIntent
from aidm.core.energy_drain_resolver import resolve_energy_drain

if isinstance(intent, EnergyDrainAttackIntent) and hit:
    drain_events = resolve_energy_drain(intent, world_state, rng, next_event_id, timestamp)
    # Filter out the duplicate attack_roll event (already in main events list)
    drain_only = [e for e in drain_events if e.event_type != "attack_roll"]
    events.extend(drain_only)
    next_event_id += len(drain_only)
```

**No `play_loop.py` routing change needed.** `EnergyDrainAttackIntent` enters via the existing `AttackIntent` path — the AI layer constructs an `EnergyDrainAttackIntent` and the resolver handles it internally. The routing isinstance check for `AttackIntent` does NOT catch `EnergyDrainAttackIntent` (it's a separate class), so the builder must either:
- Add `isinstance(combat_intent, EnergyDrainAttackIntent)` as an additional branch that also calls into `resolve_attack` internals, OR
- Make `EnergyDrainAttackIntent` resolve itself fully in its own `resolve_energy_drain()` call (preferred — simpler)

**Preferred approach:** Add `elif isinstance(combat_intent, EnergyDrainAttackIntent)` routing block in `play_loop.py` after the `AttackIntent` block (line 1729), calling `resolve_energy_drain()` directly and then `apply_energy_drain_events()`. This is cleaner than patching the middle of `resolve_attack()`.

#### Revised §4.3 — play_loop.py routing (preferred)

Insert after `AttackIntent` block (after line 1729, before `FullAttackIntent` block at line 1730):

```python
elif isinstance(combat_intent, EnergyDrainAttackIntent):
    # WO-ENGINE-ENERGY-DRAIN-001: energy drain natural attack
    from aidm.core.energy_drain_resolver import resolve_energy_drain, apply_energy_drain_events
    from aidm.schemas.attack import EnergyDrainAttackIntent
    combat_events = resolve_energy_drain(
        intent=combat_intent,
        world_state=world_state,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.1
    )
    events.extend(combat_events)
    current_event_id += len(combat_events)
    world_state = apply_energy_drain_events(combat_events, world_state)

    # Concentration break check (same pattern as AttackIntent)
    hp_events = [e for e in combat_events if e.event_type == "hp_changed"]
    for hp_event in hp_events:
        target_id = hp_event.payload.get("entity_id")
        damage = abs(hp_event.payload.get("delta", 0))
        if damage > 0 and target_id:
            conc_events, world_state = _check_concentration_break(
                caster_id=target_id, damage_dealt=damage,
                world_state=world_state, rng=rng,
                next_event_id=current_event_id, timestamp=timestamp + 0.15,
            )
            events.extend(conc_events)
            current_event_id += len(conc_events)

    narration = "energy_drain_attack_resolved"
```

**Also** integrate negative level penalty into `spell_resolver.py` save rolls: in the Fort/Ref/Will save resolution block (around line 782), add:

```python
from aidm.core.energy_drain_resolver import get_negative_level_save_penalty
neg_level_save_penalty = get_negative_level_save_penalty(target_entity)
save_total += neg_level_save_penalty
```

---

## §5 New Event Types

| Event type | Key payload fields |
|---|---|
| `negative_levels_applied` | target_id, negative_levels_added, total_negative_levels, hp_max_reduced_by, spell_slot_lost (int level or null) |
| `energy_drain_death` | target_id, negative_levels, effective_hd |

The underlying attack roll events (`attack_roll`, `hp_changed`, `damage_roll`) are emitted normally by the existing attack resolution path within `resolve_energy_drain()`.

---

## §6 Regression Risk

**Low–Medium.** The negative level attack/save penalty integration touches `attack_resolver.py` and `spell_resolver.py`, but both are additive (penalty is 0 for any entity with `NEGATIVE_LEVELS == 0`). All existing entities default to 0 — no behavior change.

The new `EnergyDrainAttackIntent` class and `play_loop.py` routing block are entirely additive. No existing routing branches are modified.

The `_drain_spell_slot()` function only mutates state through `apply_energy_drain_events()` — event-sourced, safe.

---

## §7 Gate Spec — ENGINE-ENERGY-DRAIN 10/10

| ID | Description |
|----|-------------|
| ED-01 | `EnergyDrainAttackIntent` resolves attack roll first (normal to-hit mechanics) |
| ED-02 | Miss → no `negative_levels_applied` events emitted |
| ED-03 | Hit → `negative_levels_applied` event emitted for each negative level |
| ED-04 | Each `negative_levels_applied` event: `hp_max_reduced_by == 5` |
| ED-05 | Entity's subsequent attack rolls penalized by −1 per negative level |
| ED-06 | Entity's subsequent saving throws penalized by −1 per negative level |
| ED-07 | Spellcaster loses highest available spell slot on each negative level |
| ED-08 | `total_negative_levels >= target[EF.HD_COUNT]` → `energy_drain_death` emitted, entity defeated |
| ED-09 | Two hits from same attacker accumulate negative levels correctly (additive, not overwrite) |
| ED-10 | Negative levels persist across rounds (no rest cure in this WO) |

---

## §8 What This WO Does NOT Do

- **24-hour Fortitude save for permanent loss:** Requires time-tracking infrastructure. Deferred. All negative levels in this WO are treated as temporary (they persist indefinitely until the 24h mechanic is implemented).
- **Permanent level loss (class level drained):** Only implemented via the 24h save. Deferred.
- **Strength drain (shadow):** Shadow permanently drains STR, not HD. Different mechanic, different resolver. Deferred.
- **Incorporeal attack rules:** Spectres are incorporeal — miss chance vs. non-magical attacks. That is a separate WO. `EnergyDrainAttackIntent` handles the drain; the incorporeal miss chance is handled by the `EF.MISS_CHANCE` field already on the entity.
- **Rest recovery of negative levels:** Negative levels do NOT recover on rest in 3.5e (only the 24h save removes them). No rest change needed.
- **Action economy mapping:** `EnergyDrainAttackIntent` does not go through `parse_intent()`. The AI/DM constructs it directly for monster attacks. Standard action consumption is handled the same way as `AttackIntent`.

---

## §9 Preflight

- [ ] `EF.NEGATIVE_LEVELS` added to `entity_fields.py`
- [ ] `EnergyDrainAttackIntent` added to `attack.py` after `NonlethalAttackIntent`
- [ ] `energy_drain_resolver.py` created with all 4 functions
- [ ] `elif isinstance(combat_intent, EnergyDrainAttackIntent)` routing block added to `play_loop.py` after `AttackIntent` block (before `FullAttackIntent` at line 1730)
- [ ] Negative level attack penalty integrated into `attack_resolver.py` bonus assembly
- [ ] Negative level save penalty integrated into `spell_resolver.py` save roll
- [ ] Gate tests ED-01 through ED-10 written in `tests/test_engine_energy_drain_gate.py`
- [ ] Full suite regression run — zero new failures expected
