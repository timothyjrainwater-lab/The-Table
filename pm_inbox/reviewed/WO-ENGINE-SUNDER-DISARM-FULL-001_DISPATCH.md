# WO-ENGINE-SUNDER-DISARM-FULL-001 — Sunder & Disarm Full State (PHB p.155, p.158)

**Issued:** 2026-02-24
**Authority:** PM
**Gate:** ENGINE-SUNDER-DISARM-FULL (new gate, defined below)

---

## 1. Target Lock

PHB p.158 / p.155: Sunder and Disarm are combat maneuvers that modify equipment
state. Both are currently DEGRADED in `aidm/core/maneuver_resolver.py` — they
perform full roll mechanics and emit narrative events, but write no persistent
entity state. This WO upgrades both to full implementation.

Mechanically:
- **Sunder** targets a held weapon or shield. Damage dealt minus hardness reduces
  item HP. At 0 HP the item is broken (attack penalty). At or below negative max HP
  the item is destroyed (gone entirely).
- **Disarm** uses an opposed attack roll. On attacker win, the target's weapon is on
  the ground (DISARMED state). On attacker loss by 10 or more, the attacker drops
  their own weapon instead.

**Done means:** `EF.WEAPON_HP`, `EF.WEAPON_BROKEN`, `EF.WEAPON_DESTROYED`, and
`EF.DISARMED` added to `entity_fields.py` + hardness table + `resolve_sunder()`
writes persistent item state + `resolve_disarm()` writes persistent DISARMED state
+ `attack_resolver.py` reads WEAPON_BROKEN (−2 penalty) and DISARMED (guard) +
four new events + Gate ENGINE-SUNDER-DISARM-FULL 10/10.

---

## 2. PHB Rules

### 2.1 Sunder (PHB p.158)

> **Sunder:** You can use a melee attack with a slashing or bludgeoning weapon to
> strike a weapon or shield that your opponent is holding. If you are attempting
> to sunder a weapon or shield, follow the steps outlined here. (A sunder attempt
> provokes an attack of opportunity from the target.)

Key rules:
- Attack roll vs opponent's weapon/shield — treated as attack vs the held object
- The object has **hardness** and **HP**:
  - Light weapon: hardness 5, **2 HP**
  - One-handed weapon: hardness 5, **5 HP**
  - Two-handed weapon: hardness 5, **10 HP**
  - (Armor and shields have their own hardness/HP values — this WO scopes to weapons only)
- Damage dealt **minus hardness** = HP lost by item (minimum 0 if under hardness)
- Item at **0 HP** = broken (−2 attack if weapon; still usable)
- Item at **≤ −(max HP)** = destroyed (removed from play)
- Attacker **provokes AoO** unless they have the **Improved Sunder** feat
  (AoO already handled externally by `aoo_events` parameter — no change needed)

**Hardness table (weapons, PHB p.166):**

| Weapon type | Hardness | HP |
|-------------|----------|----|
| light       | 5        | 2  |
| one-handed  | 5        | 5  |
| two-handed  | 5        | 10 |

Hardness for shields is deferred (this WO scopes to `target_item == "weapon"` only;
shield sunder records narrative as before until a future WO adds shield item state).

### 2.2 Disarm (PHB p.155)

> **Disarm:** As a melee attack, you may attempt to disarm your opponent. If you
> do so with a weapon, you provoke an attack of opportunity from the target of your
> disarm attempt.

Key rules:
- **Opposed attack roll**: attacker vs defender (both roll d20 + attack bonus + size)
- Two-handed weapon wielder: **+4 to their opposed roll**
- Light weapon wielder: **−4 to their opposed roll**
  (both of these modifiers already implemented in current degraded code)
- If **attacker wins**: defender drops their weapon (weapon is on ground at their
  feet; can be picked up as a **move action**)
- If **attacker loses by 10 or more**: attacker drops their own weapon instead
- Attacker **provokes AoO** unless they have the **Improved Disarm** feat
  (AoO already handled externally — no change needed)

**Margin rule for counter-disarm upgrade:**
The existing code already rolls a counter-disarm check when the primary roll fails.
This WO replaces the "attacker loses by 10+" trigger with a **margin check on the
primary opposed roll** (not a second roll): if `check_result.margin <= -10` (i.e.,
attacker lost by 10 or more in the primary check), the attacker is disarmed directly.
The existing counter-disarm roll path is retained for margins between −1 and −9
(defender wins but not by 10+) — no persistent state on that path.

**Scope for this WO:**
- `EF.DISARMED` set to `True` on target when disarm succeeds
- `EF.DISARMED` set to `True` on attacker when attacker loses by ≥ 10
- DISARMED entity cannot make weapon attacks until they pick up their weapon
- Pick-up is handled narratively — no new intent required
  (DM narration clears DISARMED; or implement as automatic on next non-attack turn)
- Attack resolver guard: DISARMED entity attempting weapon attack → `attack_denied`
  event, attack aborted

---

## 3. New Entity Fields

Add all constants to `aidm/schemas/entity_fields.py` under a new section block
`# --- Item State (WO-ENGINE-SUNDER-DISARM-FULL-001) ---`.

```python
# --- Item State (WO-ENGINE-SUNDER-DISARM-FULL-001) ---
WEAPON_HP         = "weapon_hp"         # Int: current HP of equipped weapon (defaults to HP by weapon type)
WEAPON_HP_MAX     = "weapon_hp_max"     # Int: max HP of equipped weapon (set at equip/chargen)
WEAPON_BROKEN     = "weapon_broken"     # Bool: weapon is broken (−2 attack penalty, still usable)
WEAPON_DESTROYED  = "weapon_destroyed"  # Bool: weapon is destroyed (gone; entity has no weapon)
DISARMED          = "disarmed"          # Bool: entity's weapon is on the ground (cannot make weapon attacks)
```

**Default values** (when field absent — use `.get()` with these defaults everywhere):

| Field             | Default | Rationale                                      |
|-------------------|---------|------------------------------------------------|
| `EF.WEAPON_HP`    | 5       | Assumes one-handed weapon; resolver SHOULD set based on weapon type |
| `EF.WEAPON_HP_MAX`| 5       | Same assumption                                |
| `EF.WEAPON_BROKEN`| False   | Normal state                                   |
| `EF.WEAPON_DESTROYED` | False | Normal state                               |
| `EF.DISARMED`     | False   | Normal state                                   |

**Fixture requirement:** Entities used in gate tests MUST have `weapon_hp` and
`weapon_hp_max` set explicitly in their fixture dict to the correct value for
their weapon type (light=2, one-handed=5, two-handed=10). Do not rely on defaults
for gate assertions.

---

## 4. Implementation Spec

### 4.1 Hardness & HP Lookup Helper

Add a private helper near the top of `aidm/core/maneuver_resolver.py`:

```python
# WO-ENGINE-SUNDER-DISARM-FULL-001: Weapon hardness and HP by grip type (PHB p.166)
_WEAPON_HARDNESS: Dict[str, int] = {
    "light":      5,
    "one-handed": 5,
    "two-handed": 5,
}

_WEAPON_HP_MAX: Dict[str, int] = {
    "light":      2,
    "one-handed": 5,
    "two-handed": 10,
}


def _get_weapon_hardness(world_state: WorldState, entity_id: str) -> int:
    """Return hardness of entity's equipped weapon. Default 5."""
    weapon_type = _get_weapon_type(world_state, entity_id)
    return _WEAPON_HARDNESS.get(weapon_type, 5)


def _get_weapon_hp_max(world_state: WorldState, entity_id: str) -> int:
    """Return max HP of entity's equipped weapon. Default 5 (one-handed)."""
    weapon_type = _get_weapon_type(world_state, entity_id)
    return _WEAPON_HP_MAX.get(weapon_type, 5)
```

`_get_weapon_type()` already exists in the module — reuse it.

### 4.2 `resolve_sunder()` Upgrade

Locate the `sunder_success` block in `resolve_sunder()` (currently around line 1167).
Replace the block that appends the `sunder_success` event and builds the result.

**Before (DEGRADED):**
```python
events.append(Event(
    event_id=current_event_id,
    event_type="sunder_success",
    ...
    payload={
        ...
        "note": "DEGRADED: Narrative only, no persistent state change",
    },
    ...
))
```

**After (FULL):**

Step 1 — compute effective damage after hardness:
```python
hardness = _get_weapon_hardness(world_state, target_id)
damage_after_hardness = max(0, total_damage - hardness)
```

Step 2 — read current weapon state from target entity:
```python
target_entity = world_state.entities.get(target_id, {})
current_weapon_hp = target_entity.get(EF.WEAPON_HP, _get_weapon_hp_max(world_state, target_id))
weapon_hp_max = target_entity.get(EF.WEAPON_HP_MAX, _get_weapon_hp_max(world_state, target_id))
weapon_name = (target_entity.get(EF.WEAPON) or {}).get("name", "weapon")
```

Step 3 — decrement weapon HP:
```python
new_weapon_hp = current_weapon_hp - damage_after_hardness
world_state = world_state.update_entity(target_id, {EF.WEAPON_HP: new_weapon_hp})
```

Step 4 — emit `sunder_success` (no DEGRADED note):
```python
events.append(Event(
    event_id=current_event_id,
    event_type="sunder_success",
    timestamp=current_timestamp,
    payload={
        "attacker_id": attacker_id,
        "target_id": target_id,
        "target_item": intent.target_item,
        "damage_dice": damage_dice_expr,
        "damage_rolls": damage_rolls,
        "damage_roll": damage_roll,
        "damage_bonus": damage_bonus,
        "total_damage": total_damage,
        "hardness": hardness,
        "damage_after_hardness": damage_after_hardness,
        "weapon_hp_before": current_weapon_hp,
        "weapon_hp_after": new_weapon_hp,
        **({"causal_chain_id": causal_chain_id, "chain_position": 1} if causal_chain_id is not None else {}),
    },
    citations=[{"source_id": "681f92bc94ff", "page": 158}],
))
current_event_id += 1
current_timestamp += 0.01
```

Step 5 — check for broken / destroyed and emit follow-up events:
```python
if new_weapon_hp <= -weapon_hp_max:
    # Destroyed
    world_state = world_state.update_entity(target_id, {
        EF.WEAPON_BROKEN: True,
        EF.WEAPON_DESTROYED: True,
    })
    events.append(Event(
        event_id=current_event_id,
        event_type="weapon_destroyed",
        timestamp=current_timestamp,
        payload={
            "actor_id": attacker_id,
            "target_id": target_id,
            "weapon_name": weapon_name,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 158}],
    ))
    current_event_id += 1
    current_timestamp += 0.01
elif new_weapon_hp <= 0:
    # Broken (not yet destroyed)
    world_state = world_state.update_entity(target_id, {EF.WEAPON_BROKEN: True})
    events.append(Event(
        event_id=current_event_id,
        event_type="weapon_broken",
        timestamp=current_timestamp,
        payload={
            "actor_id": attacker_id,
            "target_id": target_id,
            "weapon_name": weapon_name,
            "hp_remaining": new_weapon_hp,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 158}],
    ))
    current_event_id += 1
    current_timestamp += 0.01
```

Step 6 — build ManeuverResult (unchanged structure, add new fields):
```python
result = ManeuverResult(
    maneuver_type="sunder",
    success=True,
    events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
    damage_dealt=total_damage,
)
```

**No changes to the sunder failure path** — if attacker loses the opposed check,
no item state is affected.

### 4.3 `resolve_disarm()` Upgrade

#### 4.3.1 Success path (attacker wins primary check)

Locate the `disarm_success` block (currently around line 1351).

**Before (DEGRADED):**
```python
payload={
    ...
    "note": "DEGRADED: Narrative only, no persistent state change",
    ...
}
```

**After (FULL):**

```python
# Set target DISARMED
target_entity = world_state.entities.get(target_id, {})
weapon_name = (target_entity.get(EF.WEAPON) or {}).get("name", "weapon")
world_state = world_state.update_entity(target_id, {EF.DISARMED: True})

events.append(Event(
    event_id=current_event_id,
    event_type="disarm_success",
    timestamp=current_timestamp,
    payload={
        "attacker_id": attacker_id,
        "target_id": target_id,
        "weapon_dropped": True,
        **({"causal_chain_id": causal_chain_id, "chain_position": 1} if causal_chain_id is not None else {}),
    },
    citations=[{"source_id": "681f92bc94ff", "page": 155}],
))
current_event_id += 1
current_timestamp += 0.01

events.append(Event(
    event_id=current_event_id,
    event_type="weapon_disarmed",
    timestamp=current_timestamp,
    payload={
        "actor_id": attacker_id,
        "target_id": target_id,
        "weapon_name": weapon_name,
        "location": "at_feet",
    },
    citations=[{"source_id": "681f92bc94ff", "page": 155}],
))
current_event_id += 1
current_timestamp += 0.01
```

#### 4.3.2 Failure path: margin ≤ −10 (attacker loses by 10+)

In the primary failure branch, **before** the existing counter-disarm roll, add a
margin check. If the primary check margin is −10 or worse the attacker is disarmed
directly and the counter-disarm roll is **skipped**:

```python
# PHB p.155: if attacker loses by 10+, attacker drops their own weapon
if check_result.margin <= -10:
    attacker_entity = world_state.entities.get(attacker_id, {})
    attacker_weapon_name = (attacker_entity.get(EF.WEAPON) or {}).get("name", "weapon")
    world_state = world_state.update_entity(attacker_id, {EF.DISARMED: True})
    events.append(Event(
        event_id=current_event_id,
        event_type="attacker_disarmed",
        timestamp=current_timestamp,
        payload={
            "actor_id": attacker_id,
            "weapon_name": attacker_weapon_name,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 155}],
    ))
    current_event_id += 1
    result = ManeuverResult(
        maneuver_type="disarm",
        success=False,
        events=[{"event_type": e.event_type, "payload": e.payload} for e in events],
    )
    return events, world_state, result
```

Place this block **immediately after** emitting `disarm_failure` with
`"reason": "opposed_check_lost"` and **before** the counter-disarm roll. The
existing counter-disarm roll path (margin between −1 and −9) is retained as-is,
with the `counter_disarm_success` DEGRADED note removed: if counter succeeds, set
`world_state = world_state.update_entity(attacker_id, {EF.DISARMED: True})` and
emit `attacker_disarmed` event in that block as well (same payload shape).

### 4.4 `attack_resolver.py` — WEAPON_BROKEN Penalty and DISARMED Guard

Locate the function that computes the attacker's total attack bonus (the section
that applies `TEMPORARY_MODIFIERS` and condition modifiers). Add the broken weapon
check immediately after existing modifier accumulation:

```python
# WO-ENGINE-SUNDER-DISARM-FULL-001: Broken weapon penalty (PHB p.166)
if attacker_entity.get(EF.WEAPON_BROKEN, False):
    attack_modifier -= 2
```

Add the DISARMED guard near the **top** of the attack resolution function, before
any rolls are made:

```python
# WO-ENGINE-SUNDER-DISARM-FULL-001: DISARMED guard — cannot make weapon attacks
if attacker_entity.get(EF.DISARMED, False):
    events.append(Event(
        event_id=current_event_id,
        event_type="attack_denied",
        timestamp=current_timestamp,
        payload={
            "attacker_id": intent.attacker_id,
            "target_id": intent.target_id,
            "reason": "disarmed",
        },
    ))
    current_event_id += 1
    # Return early — no attack occurs
    return events, world_state, current_event_id
```

Place the DISARMED guard **after** the entity lookup but **before** any RNG
consumption (before the attack roll). This ensures no RNG is consumed when the
attack is denied, preserving RNG stream determinism for gold masters.

**Existing `TEMPORARY_MODIFIERS` and condition modifier patterns in
`attack_resolver.py` serve as the code convention to follow for the broken weapon
penalty insertion point.** The exact line range will vary; search for the block
that sums `attack_modifier` contributions.

### 4.5 `update_entity()` API Note

`WorldState.update_entity()` performs a shallow merge of the provided dict into
the entity's existing dict. Field-level writes such as:
```python
world_state = world_state.update_entity(target_id, {EF.WEAPON_HP: new_weapon_hp})
```
are already the established pattern throughout the codebase (see `dying_resolver.py`,
`grapple` resolution, condition application). Follow that pattern exactly.

### 4.6 `maneuvers.py` — Update Docstrings

Remove the `(DEGRADED)` marker from `SunderIntent` and `DisarmIntent` class
docstrings. Update inline comments in `maneuvers.py` module docstring to reflect
full implementation:

```python
# DEGRADATIONS (remaining after WO-ENGINE-SUNDER-DISARM-FULL-001):
# - Sunder: Shield HP tracking deferred to future WO
# - Disarm: Pick-up intent deferred (cleared narratively by DM)
```

---

## 5. New Event Types

| Event | Emitted When | Required Payload Keys |
|-------|--------------|-----------------------|
| `weapon_broken` | Sunder: `new_weapon_hp <= 0` (and not destroyed) | `actor_id`, `target_id`, `weapon_name`, `hp_remaining` |
| `weapon_destroyed` | Sunder: `new_weapon_hp <= -weapon_hp_max` | `actor_id`, `target_id`, `weapon_name` |
| `weapon_disarmed` | Disarm success (primary check attacker wins) | `actor_id`, `target_id`, `weapon_name`, `location` |
| `attacker_disarmed` | Disarm failure by 10+ (primary or counter) | `actor_id`, `weapon_name` |

**`weapon_broken` payload MUST include all four keys.** Gate SD-10 asserts on this
exact set.

`sunder_success` payload is expanded — the `"note": "DEGRADED: ..."` key is
removed and replaced with `hardness`, `damage_after_hardness`,
`weapon_hp_before`, `weapon_hp_after`.

`disarm_success` payload is similarly cleaned — the `"note": "DEGRADED: ..."` key
is removed.

`counter_disarm_success` and `counter_disarm_failure` DEGRADED notes removed.

---

## 6. Regression Risk

- **LOW for sunder path:** `resolve_sunder()` activates only when a `SunderIntent`
  is emitted. No existing gold masters include sunder sequences. Gold master JSONL
  files do not reference `sunder_success` payloads — no drift expected.
- **MEDIUM for attack_resolver.py:** The DISARMED guard inserts a new early-return
  path. The guard condition is `EF.DISARMED == True`, which defaults to `False` for
  all existing entities. No existing fixture sets this field. Guard is a no-op for
  all current scenarios.
- **LOW for WEAPON_BROKEN penalty:** `EF.WEAPON_BROKEN` defaults to `False` — the
  `attack_modifier -= 2` line is never reached for existing entities. Zero drift.
- **Gold masters:** None of the four scenario gold masters (`boss_100turn`,
  `dungeon_100turn`, `field_100turn`, `tavern_100turn`) include sunder or disarm
  intents. No payload field renames on existing events (only additions to
  `sunder_success` and removal of `"note"` DEGRADED key, which existing masters
  do not assert on).
- **Counter-disarm path:** The margin check (`<= -10`) is inserted before the
  existing counter-disarm roll. For margins −1 to −9 the counter-disarm roll still
  runs as before, with the addition of an `attacker_disarmed` event on counter
  success. Existing tests that assert on `counter_disarm_success` will need to
  tolerate the new follow-up event in the stream.
- **RNG determinism:** DISARMED guard returns before any RNG consumption. Broken
  weapon penalty is a modifier only — no dice consumed. Both changes preserve
  RNG stream ordering for all existing scenarios.

---

## 7. What This WO Does NOT Do

- No shield HP tracking (target_item == "shield" continues to emit narrative only)
- No armor sunder (PHB p.165 armor hardness/HP — deferred)
- No pick-up intent (`PickUpWeaponIntent`) — pick-up is handled narratively by DM
  resetting `EF.DISARMED = False`; no new intent added in this WO
- No Improved Sunder feat bonus (feat already gates AoO via existing AoO path;
  no additional attack roll modifier from Improved Sunder in PHB — no change needed)
- No Improved Disarm feat (disarm already handled via existing AoO; no bonus to
  the disarm roll itself from the feat — no change needed)
- No weapon repair mechanics (broken weapon recovery — deferred)
- No unarmed disarm rules (PHB p.155 unarmed disarm attempt provokes both AoO and
  counter-attack — deferred, current code assumes armed)
- No two-weapon disarm interaction (attacker using two weapons — deferred)

---

## 8. Gate Spec

**Gate name:** `ENGINE-SUNDER-DISARM-FULL`
**Test file:** `tests/test_engine_gate_sunder_disarm_full.py` (new file)

| # | ID | Test | Check |
|---|----|------|-------|
| 1 | SD-01 | `EF.WEAPON_HP` exists and defaults positive | `entity_fields.py`: constant present; `.get(EF.WEAPON_HP, 5)` returns 5 |
| 2 | SD-02 | `EF.WEAPON_BROKEN` exists, defaults False | `entity_fields.py`: constant present; `.get(EF.WEAPON_BROKEN, False)` returns False |
| 3 | SD-03 | `EF.DISARMED` exists, defaults False | `entity_fields.py`: constant present; `.get(EF.DISARMED, False)` returns False |
| 4 | SD-04 | Sunder: WEAPON_HP decremented by damage after hardness | Fixture: weapon_hp=5, hardness=5; total_damage=8 → damage_after_hardness=3 → weapon_hp=2 after resolve |
| 5 | SD-05 | Sunder: WEAPON_HP ≤ 0 → WEAPON_BROKEN = True + `weapon_broken` event | Fixture: weapon_hp=2; total_damage=10 → new_hp=−3; WEAPON_BROKEN=True; `weapon_broken` in events |
| 6 | SD-06 | attack_resolver: −2 penalty when WEAPON_BROKEN True | Entity with WEAPON_BROKEN=True: attack roll total is 2 lower than same entity without it |
| 7 | SD-07 | Disarm success → target DISARMED=True + `weapon_disarmed` event | Rigged rolls (attacker wins); target.DISARMED=True; `weapon_disarmed` event in stream |
| 8 | SD-08 | Disarm failure by 10+ → attacker DISARMED=True + `attacker_disarmed` event | Rigged rolls (margin=−10); attacker.DISARMED=True; `attacker_disarmed` event |
| 9 | SD-09 | DISARMED entity cannot make weapon attack | Entity with DISARMED=True: attack attempt → `attack_denied` event; no attack_roll event |
| 10 | SD-10 | `weapon_broken` event has actor_id, target_id, weapon_name, hp_remaining | Assert all four keys present in event payload |

**Test count target:** ENGINE-SUNDER-DISARM-FULL 10/10.

---

## 9. Preflight

```bash
cd f:/DnD-3.5

# Confirm baseline
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5

# After implementation
python -m pytest tests/test_engine_gate_sunder_disarm_full.py -v
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5
```
