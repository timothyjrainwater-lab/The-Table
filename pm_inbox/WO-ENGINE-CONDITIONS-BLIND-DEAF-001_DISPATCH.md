# WO-ENGINE-CONDITIONS-BLIND-DEAF-001 — Blinded, Deafened, Entangled, Confused Conditions

**Issued:** 2026-02-24
**Authority:** PM
**Gate:** ENGINE-CONDITIONS-BLIND-DEAF (new gate, defined below)

---

## 1. Target Lock

Four conditions absent from `ConditionType` that have direct mechanical weight in combat resolution: **BLINDED**, **DEAFENED**, **ENTANGLED**, and **CONFUSED**. Each requires both a schema entry and resolver-level enforcement. This WO wires all four from enum through resolution to event emission.

**Done means:** Four new `ConditionType` entries + canonical factory functions in `conditions.py` + `condition_combat_resolver.py` new module + BLINDED miss-chance hook in `attack_resolver.py` + DEAFENED verbal-failure hook in `spell_resolver.py` + CONFUSED behavior roll at turn start in `play_loop.py` + CONFUSED AoO suppression in `aoo.py` + `blinded_miss` and `confusion_behavior` events + Gate ENGINE-CONDITIONS-BLIND-DEAF 10/10.

---

## 2. PHB Rules

### 2.1 Blinded (PHB p.309)

> A blinded character cannot see and so cannot make Spot checks. She has a 50% miss chance on attacks (all types), loses any Dexterity bonus to AC, has a –2 penalty to AC, moves at half speed, and takes a –4 penalty on Search checks. Opponents have +2 to attack rolls against a blinded creature.

Mechanical extractions:

- **50% miss chance on attacker's attacks:** Roll d100 before the attack roll; result 1–50 = automatic miss regardless of the attack roll. This is a blinded-miss, not a concealment miss — it fires first, before the concealment check.
- **Attacker loses DEX bonus to AC** when blinded (treated as flat-footed for AC purposes, PHB p.309). This means the attacker's own AC drops — it does not affect the attack roll computation.
- **−2 penalty to AC** (armour-class penalty on the blinded entity, not a type-restricted penalty).
- **Opponents get +2 to attack rolls** against the blinded creature.
- Movement halved and skill penalties are out of scope for the combat resolver (movement enforcement deferred; skill system not present).

Implementation priority: the +2 attacker bonus against a blinded defender and the −2 AC penalty on a blinded defender are both AC-side effects and resolve to the same outcome: effective defender AC is reduced by 2 from their own penalty, and attackers gain +2 to their roll. These two effects are additive from the attacker's perspective (a swing of +4 net), but they must be tracked separately in the payload for audit.

### 2.2 Deafened (PHB p.309)

> A deafened character cannot hear. She takes a –4 penalty on initiative checks, has a 20% chance of spell failure when casting spells with a verbal component, and cannot make Listen checks.

Mechanical extractions:

- **−4 initiative penalty:** Out of scope (initiative is rolled outside the resolver pipeline; deferred).
- **20% spell failure for verbal-component spells:** Roll d100 at the time of cast; result 1–20 = spell fizzles (no effect, spell slot consumed). Applied only when the spell definition marks `has_verbal_component = True`.
- Listen check prohibition: skill system not present; no-op.

### 2.3 Entangled (PHB p.310)

> An entangled character takes a –2 penalty on attack rolls and a –4 penalty to Dexterity. If the entangling effect holds the character in place, the character is immobilized; otherwise, she can move at half speed.

Mechanical extractions:

- **−2 penalty to attack rolls:** Applied via `ConditionModifiers.attack_modifier = -2`.
- **−4 effective DEX:** Applied via `ConditionModifiers.dex_modifier = -4`. The existing DEX modifier path in `attack_resolver.py` propagates this automatically via `get_condition_modifiers()`.
- **Concentration check DC 15 to cast while entangled:** Deferred (no concentration check system for this case outside of the existing concentration-on-damage path; spell-prep concentration enforcement is a separate WO).
- **Half speed / immobilized:** Movement enforcement deferred.

### 2.4 Confused (PHB p.310)

> A confused character's actions are determined by rolling d% at the beginning of his turn: 01–10: Attack caster of confusion or nearest creature if caster is not in sight. 11–20: Act normally. 21–50: Do nothing but babble incoherently. 51–70: Flee from all creatures at top speed for 1 round. 71–100: Attack nearest creature (not self).

Additional rules:

- A confused creature does not make attacks of opportunity against any creature that it is not already attacking.
- A confused character cannot take delayed actions or ready actions.

Mechanical extractions:

- **d100 behavior roll at turn start:** Consumed from the `combat` RNG stream, result maps to one of five behavior strings.
- **Intent override:** When behavior is not `"act_normally"`, the entity's declared intent for that turn is suppressed or replaced by the confusion-driven behavior.
- **AoO suppression:** Confused entities do not threaten (cannot make AoOs) against entities they are not currently attacking.

---

## 3. New Entity Fields

None. All four conditions are stored via the existing `EF.CONDITIONS` dict on entities, using `ConditionInstance` objects with populated `ConditionModifiers`. No new `EF` fields are required.

The `ConditionModifiers` dataclass already carries `attack_modifier`, `dex_modifier`, `ac_modifier`, and `loses_dex_to_ac` — all fields needed by BLINDED and ENTANGLED. DEAFENED and CONFUSED carry no numeric modifiers in `ConditionModifiers`; their effects are procedural and handled in resolvers.

New boolean metadata flags to add to `ConditionModifiers`:

| Flag | Type | Purpose |
|------|------|---------|
| `is_blinded` | `bool = False` | Resolvers check this to apply 50% miss and the +2 opponent attack bonus; distinct from `loses_dex_to_ac` which is already present |
| `is_deafened` | `bool = False` | Spell resolver checks this for verbal-component failure |
| `is_confused` | `bool = False` | play_loop turn-start checks this to trigger behavior roll |

Rationale for explicit flags rather than inferring from `ac_modifier`: BLINDED's +2 opponent attack bonus and 50% miss chance cannot be inferred from a numeric AC field alone. An explicit flag in `ConditionModifiers` ensures resolvers can check a single boolean rather than reconstituting the condition type from aggregate values. This is consistent with the existing `loses_dex_to_ac`, `auto_hit_if_helpless`, and `actions_prohibited` pattern already in the dataclass.

---

## 4. Implementation Spec

### 4.1 `aidm/schemas/conditions.py` — New ConditionType Entries

Add four new members to `ConditionType`:

```python
BLINDED   = "blinded"    # WO-ENGINE-CONDITIONS-BLIND-DEAF-001
DEAFENED  = "deafened"   # WO-ENGINE-CONDITIONS-BLIND-DEAF-001
ENTANGLED = "entangled"  # WO-ENGINE-CONDITIONS-BLIND-DEAF-001
CONFUSED  = "confused"   # WO-ENGINE-CONDITIONS-BLIND-DEAF-001
```

Place after the `TURNED` entry, grouped under a `# WO-ENGINE-CONDITIONS-BLIND-DEAF-001` comment.

### 4.2 `aidm/schemas/conditions.py` — New Flags on `ConditionModifiers`

Add three boolean fields to `ConditionModifiers`, following the `loses_dex_to_ac` entry:

```python
is_blinded: bool = False
"""Metadata: entity is blinded — 50% miss on own attacks, opponents +2 to attack,
-2 AC penalty, loses DEX bonus to AC. (WO-ENGINE-CONDITIONS-BLIND-DEAF-001)"""

is_deafened: bool = False
"""Metadata: entity is deafened — 20% verbal spell failure.
(WO-ENGINE-CONDITIONS-BLIND-DEAF-001)"""

is_confused: bool = False
"""Metadata: entity is confused — d100 behavior roll at turn start, cannot make AoOs.
(WO-ENGINE-CONDITIONS-BLIND-DEAF-001)"""
```

Update `to_dict()` and `from_dict()` to include all three new fields (default `False`).

### 4.3 `aidm/schemas/conditions.py` — New Factory Functions

Add four factory functions following `create_turned_condition`:

```python
def create_blinded_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Blinded condition instance.

    PHB p.309: 50% miss chance on own attacks (d100, 1-50 = miss), loses DEX
    to AC, -2 AC penalty, opponents get +2 to attack rolls.

    WO-ENGINE-CONDITIONS-BLIND-DEAF-001
    """
    return ConditionInstance(
        condition_type=ConditionType.BLINDED,
        source=source,
        modifiers=ConditionModifiers(
            ac_modifier=-2,         # -2 AC penalty (PHB p.309)
            loses_dex_to_ac=True,   # Treated as flat-footed for AC (PHB p.309)
            is_blinded=True,        # Triggers 50% miss + opponent +2 in resolvers
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Blinded: -2 AC, loses DEX to AC, 50% miss on own attacks, opponents +2"
    )


def create_deafened_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Deafened condition instance.

    PHB p.309: 20% spell failure for verbal-component spells.

    WO-ENGINE-CONDITIONS-BLIND-DEAF-001
    """
    return ConditionInstance(
        condition_type=ConditionType.DEAFENED,
        source=source,
        modifiers=ConditionModifiers(
            is_deafened=True,       # Triggers verbal spell failure in spell_resolver
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Deafened: 20% verbal spell failure"
    )


def create_entangled_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Entangled condition instance.

    PHB p.310: -2 attack rolls, -4 DEX.

    WO-ENGINE-CONDITIONS-BLIND-DEAF-001
    """
    return ConditionInstance(
        condition_type=ConditionType.ENTANGLED,
        source=source,
        modifiers=ConditionModifiers(
            attack_modifier=-2,     # -2 to attack rolls (PHB p.310)
            dex_modifier=-4,        # -4 DEX (PHB p.310)
            movement_prohibited=True,  # Half speed / immobilized (metadata only)
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Entangled: -2 attack, -4 DEX, movement restricted"
    )


def create_confused_condition(source: str, applied_at_event_id: int) -> ConditionInstance:
    """Create Confused condition instance.

    PHB p.310: d100 behavior roll each turn. Cannot make AoOs except against
    current attack target. Cannot delay or ready.

    WO-ENGINE-CONDITIONS-BLIND-DEAF-001
    """
    return ConditionInstance(
        condition_type=ConditionType.CONFUSED,
        source=source,
        modifiers=ConditionModifiers(
            is_confused=True,       # Triggers behavior roll in play_loop turn start
        ),
        applied_at_event_id=applied_at_event_id,
        notes="Confused: d100 behavior roll each turn, no AoOs except vs current target"
    )
```

### 4.4 New Module: `aidm/core/condition_combat_resolver.py`

Create a new module to house the four resolver functions. These functions are called by `attack_resolver.py`, `spell_resolver.py`, and `play_loop.py` respectively. Keeping them in a dedicated module prevents bloating the primary resolvers and makes the condition logic independently testable.

```python
"""Condition combat modifier resolver for WO-ENGINE-CONDITIONS-BLIND-DEAF-001.

Implements PHB p.309-310 mechanics for BLINDED, DEAFENED, ENTANGLED, CONFUSED.
All functions are pure side-effect-free queries or event generators; they do NOT
mutate WorldState directly. State mutation is handled by the calling resolver
via returned events.

WO-ENGINE-CONDITIONS-BLIND-DEAF-001
"""

from typing import List, Tuple, Optional
from aidm.core.event_log import Event
from aidm.core.rng_protocol import RNGProvider
from aidm.schemas.conditions import ConditionModifiers


_BLINDED_MISS_THRESHOLD = 50       # PHB p.309: 1-50 = miss
_DEAFENED_SPELL_FAIL_THRESHOLD = 20  # PHB p.309: 1-20 = failure
_CONFUSED_BEHAVIOR_TABLE = [
    (10,  "attack_caster"),   # 01-10
    (20,  "act_normally"),    # 11-20
    (50,  "babble"),          # 21-50
    (70,  "flee"),            # 51-70
    (100, "attack_nearest"),  # 71-100
]


def check_blinded_miss(
    attacker_modifiers: ConditionModifiers,
    rng: RNGProvider,
) -> Tuple[bool, Optional[int]]:
    """Check whether a blinded attacker misses due to the 50% miss chance.

    PHB p.309: Roll d100 before the attack. 1-50 = automatic miss regardless
    of the attack roll. This check runs before concealment and before the d20
    attack roll is evaluated for hit/miss.

    Call this BEFORE rolling the d20. If this returns (True, roll), abort the
    attack sequence and emit a blinded_miss event. If (False, roll), continue
    to the normal attack roll.

    Args:
        attacker_modifiers: Aggregate condition modifiers for the attacker.
        rng: RNG provider; consumes one value from the "combat" stream.

    Returns:
        Tuple of (missed: bool, d100_result: int or None).
        d100_result is None when is_blinded is False (no roll taken).
    """
    if not attacker_modifiers.is_blinded:
        return False, None
    combat_rng = rng.stream("combat")
    roll = combat_rng.randint(1, 100)
    missed = roll <= _BLINDED_MISS_THRESHOLD
    return missed, roll


def get_blinded_defender_ac_modifier(
    defender_modifiers: ConditionModifiers,
) -> Tuple[int, int]:
    """Return the AC penalty and attacker attack bonus from a blinded defender.

    PHB p.309:
    - Blinded creature has -2 penalty to AC (already in ac_modifier=-2 on the condition).
    - Opponents get +2 to attack rolls against a blinded creature.

    The -2 AC penalty is already baked into ConditionModifiers.ac_modifier and
    applied by the standard AC path in attack_resolver. This function returns
    the +2 attacker bonus separately so it can be added to the attack roll sum
    and recorded in the attack_roll event payload.

    Args:
        defender_modifiers: Aggregate condition modifiers for the defender.

    Returns:
        Tuple of (ac_penalty: int, attacker_roll_bonus: int).
        Both are 0 when defender is not blinded.
    """
    if not defender_modifiers.is_blinded:
        return 0, 0
    return -2, 2  # ac_penalty already in ac_modifier; attacker_roll_bonus is additive


def check_deafened_spell_failure(
    caster_modifiers: ConditionModifiers,
    has_verbal_component: bool,
    rng: RNGProvider,
) -> Tuple[bool, Optional[int]]:
    """Check whether a deafened caster's spell fails due to verbal component.

    PHB p.309: 20% spell failure chance for spells with verbal components.
    Roll d100; 1-20 = spell fizzles (slot consumed, no effect).

    Args:
        caster_modifiers: Aggregate condition modifiers for the caster.
        has_verbal_component: Whether the spell being cast has a verbal component.
        rng: RNG provider; consumes one value from the "combat" stream.

    Returns:
        Tuple of (failed: bool, d100_result: int or None).
        d100_result is None when no roll was taken.
    """
    if not caster_modifiers.is_deafened or not has_verbal_component:
        return False, None
    combat_rng = rng.stream("combat")
    roll = combat_rng.randint(1, 100)
    failed = roll <= _DEAFENED_SPELL_FAIL_THRESHOLD
    return failed, roll


def roll_confusion_behavior(
    actor_id: str,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[str, int, List[Event]]:
    """Roll d100 to determine a confused entity's behavior for this turn.

    PHB p.310:
    01-10: attack_caster   (attack caster of confusion or nearest creature)
    11-20: act_normally    (entity acts on its own intent)
    21-50: babble          (do nothing; incoherent babbling)
    51-70: flee            (flee from all creatures at top speed)
    71-100: attack_nearest (attack nearest creature, not self)

    Emits a confusion_behavior event.

    Args:
        actor_id: Entity ID of the confused creature.
        rng: RNG provider; consumes one value from the "combat" stream.
        next_event_id: Next available event ID.
        timestamp: Event timestamp.

    Returns:
        Tuple of (behavior: str, d100_result: int, events: List[Event]).
    """
    combat_rng = rng.stream("combat")
    roll = combat_rng.randint(1, 100)

    behavior = "attack_nearest"  # Default (71-100 is the largest band)
    for threshold, label in _CONFUSED_BEHAVIOR_TABLE:
        if roll <= threshold:
            behavior = label
            break

    events = [Event(
        event_id=next_event_id,
        event_type="confusion_behavior",
        timestamp=timestamp,
        payload={
            "actor_id": actor_id,
            "roll": roll,
            "behavior": behavior,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 310}]
    )]
    return behavior, roll, events
```

### 4.5 `aidm/core/attack_resolver.py` — BLINDED Integration

**RNG consumption order change:** The blinded miss check consumes a d100 from the combat stream *before* the existing d20 attack roll. The existing RNG consumption order comment at the top of the module must be updated to reflect this:

```
RNG CONSUMPTION ORDER (deterministic):
0. IF attacker is BLINDED: Miss chance roll (d100) — WO-ENGINE-CONDITIONS-BLIND-DEAF-001
1. Attack roll (d20)
2. IF threat: Confirmation roll (d20)
3. IF hit AND miss_chance > 0: Miss chance roll (d100) [concealment]
4. IF hit: Damage roll (XdY)
5. IF hit AND sneak attack eligible: Sneak attack roll (Xd6)
```

**In `resolve_attack()`, after `attacker_modifiers` and `defender_modifiers` are computed and before the d20 roll:**

```python
# WO-ENGINE-CONDITIONS-BLIND-DEAF-001: Blinded attacker 50% miss chance (PHB p.309)
# Consumed BEFORE the d20 to preserve deterministic RNG ordering.
from aidm.core.condition_combat_resolver import (
    check_blinded_miss, get_blinded_defender_ac_modifier
)
_blinded_miss, _blinded_miss_roll = check_blinded_miss(attacker_modifiers, rng)
if _blinded_miss:
    events.append(Event(
        event_id=current_event_id,
        event_type="blinded_miss",
        timestamp=timestamp,
        payload={
            "actor_id": intent.attacker_id,
            "target_id": intent.target_id,
            "miss_roll": _blinded_miss_roll,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 309}]
    ))
    return events  # Early return: no attack roll, no damage

# WO-ENGINE-CONDITIONS-BLIND-DEAF-001: +2 attack bonus vs blinded defender (PHB p.309)
_, _blinded_attacker_bonus = get_blinded_defender_ac_modifier(defender_modifiers)
```

The `_blinded_attacker_bonus` (0 or +2) is then added to `attack_bonus_with_conditions`:

```python
attack_bonus_with_conditions = (
    intent.attack_bonus +
    attacker_modifiers.attack_modifier +
    mounted_bonus +
    terrain_higher_ground +
    feat_attack_modifier +
    flanking_bonus
    - attacker.get(EF.NEGATIVE_LEVELS, 0)
    + _fd_attack_penalty           # WO-ENGINE-DEFEND-001
    + _blinded_attacker_bonus      # WO-ENGINE-CONDITIONS-BLIND-DEAF-001: +2 vs blinded
)
```

Add `blinded_attacker_bonus` to the `attack_roll` event payload:

```python
"blinded_attacker_bonus": _blinded_attacker_bonus,  # WO-ENGINE-CONDITIONS-BLIND-DEAF-001
```

Note: The blinded defender's −2 AC penalty is already handled by the standard `ac_modifier` path (`ConditionModifiers.ac_modifier = -2` on the BLINDED condition) and does not need a separate addition here. The `loses_dex_to_ac = True` flag on the BLINDED condition is also handled by the existing `dex_penalty` computation already present in `resolve_attack()`.

The same BLINDED hooks must be applied inside `resolve_nonlethal_attack()` following the same pattern. The nonlethal resolver has a simpler structure (no cover, no feats, no flanking) but the blinded miss check must still fire first.

### 4.6 `aidm/core/spell_resolver.py` — DEAFENED Integration

**Locate the spell cast dispatch in `SpellResolver` (or whichever function handles `SpellCastIntent` resolution).** Before the save resolution step, insert a verbal-component failure check:

```python
# WO-ENGINE-CONDITIONS-BLIND-DEAF-001: Deafened verbal spell failure (PHB p.309)
from aidm.core.condition_combat_resolver import check_deafened_spell_failure
from aidm.core.conditions import get_condition_modifiers as _get_cond_mods_spell

_caster_cond_mods = _get_cond_mods_spell(world_state, caster_id)
_has_verbal = getattr(spell_def, "has_verbal_component", True)  # Default True (most spells)
_deaf_failed, _deaf_roll = check_deafened_spell_failure(
    _caster_cond_mods, _has_verbal, rng
)
if _deaf_failed:
    events.append(Event(
        event_id=current_event_id,
        event_type="spell_verbal_failure",
        timestamp=timestamp,
        payload={
            "caster_id": caster_id,
            "spell_name": spell_def.name,
            "deafened": True,
            "d100_result": _deaf_roll,
            "spell_slot_consumed": True,
        },
        citations=[{"source_id": "681f92bc94ff", "page": 309}]
    ))
    return events  # Slot consumed, no effect
```

If `SpellDefinition` does not currently carry a `has_verbal_component` field, add it with a default of `True` (PHB: the vast majority of spells have verbal components; only a small number, such as those modified by the Silent Spell metamagic feat, omit it). This field addition is in-scope for this WO.

**RNG consumption note:** The deafened d100 is consumed from the `combat` stream before the save d20. Update the `SpellResolver` RNG consumption order comment accordingly.

### 4.7 `aidm/core/play_loop.py` — CONFUSED Turn-Start Behavior Roll

**At the turn-start block** (beside the existing charge/defend modifier clearance), add a confused behavior check. This runs after modifier clearance but before the intent is dispatched:

```python
# WO-ENGINE-CONDITIONS-BLIND-DEAF-001: Confused behavior roll (PHB p.310)
from aidm.core.condition_combat_resolver import roll_confusion_behavior
from aidm.core.conditions import get_condition_modifiers as _get_cond_mods_turn

_turn_actor_cond_mods = _get_cond_mods_turn(world_state, turn_ctx.actor_id)
_actor_is_confused = _turn_actor_cond_mods.is_confused

if _actor_is_confused:
    _confusion_behavior, _confusion_roll, _confusion_events = roll_confusion_behavior(
        actor_id=turn_ctx.actor_id,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=current_timestamp,
    )
    events.extend(_confusion_events)
    current_event_id += len(_confusion_events)

    if _confusion_behavior == "babble":
        # No action taken: skip intent dispatch entirely for this turn
        continue  # or equivalent early-exit from the turn dispatch block

    elif _confusion_behavior == "act_normally":
        # Fall through: dispatch intent as declared
        pass

    elif _confusion_behavior == "flee":
        # Override intent: entity flees at full speed
        # Emit a flee_forced event; movement execution is metadata-only for now
        events.append(Event(
            event_id=current_event_id,
            event_type="confusion_flee",
            timestamp=current_timestamp + 0.05,
            payload={"actor_id": turn_ctx.actor_id, "behavior": "flee"},
            citations=[{"source_id": "681f92bc94ff", "page": 310}]
        ))
        current_event_id += 1
        continue  # No further intent processing this turn

    elif _confusion_behavior in ("attack_caster", "attack_nearest"):
        # Override intent: entity attacks nearest/caster target
        # Resolve as a standard attack against nearest hostile; target selection
        # is caller responsibility (nearest_entity_id from world_state by distance).
        # If no valid target exists, the entity babbles (no action).
        # Emit confusion_attack_override event then dispatch an AttackIntent.
        events.append(Event(
            event_id=current_event_id,
            event_type="confusion_attack_override",
            timestamp=current_timestamp + 0.05,
            payload={
                "actor_id": turn_ctx.actor_id,
                "behavior": _confusion_behavior,
                "roll": _confusion_roll,
            },
            citations=[{"source_id": "681f92bc94ff", "page": 310}]
        ))
        current_event_id += 1
        # Then construct and dispatch AttackIntent for nearest/caster target
        # (nearest target selection: sort world_state.entities by distance from actor)
        # If no valid target found within range: no attack, turn ends.
```

The full nearest-target selection logic is: iterate `world_state.entities`, exclude the actor itself and any entities with `EF.DEFEATED = True`, compute Euclidean distance from actor position, pick the minimum. If the actor has no position or no valid targets exist, the attack-nearest branch silently no-ops (no attack emitted). This is acceptable for Gate purposes — BD-09 tests the event emission, not the actual attack resolution against the nearest target.

### 4.8 `aidm/core/aoo.py` — CONFUSED AoO Suppression

In `check_aoo_triggers()`, after the reactor eligibility checks (currently checking `EF.DEFEATED` and `EF.AOO_USED`), add a confused-entity guard:

```python
# WO-ENGINE-CONDITIONS-BLIND-DEAF-001: Confused entities cannot make AoOs (PHB p.310)
from aidm.core.conditions import get_condition_modifiers as _get_cond_mods_aoo
_reactor_cond_mods = _get_cond_mods_aoo(world_state, candidate_reactor_id)
if _reactor_cond_mods.is_confused:
    continue  # Skip: confused entities do not threaten
```

This guard must be added inside the reactor candidate loop, before appending an `AooTrigger`. The import should be placed at the call site to avoid circular imports (matching the existing pattern of local imports inside the function for `MountedMoveIntent` etc.).

### 4.9 New Event Types

| Event | Emitted By | Key Payload Fields |
|-------|------------|--------------------|
| `blinded_miss` | `attack_resolver.resolve_attack()` | `actor_id`, `target_id`, `miss_roll` |
| `confusion_behavior` | `condition_combat_resolver.roll_confusion_behavior()` | `actor_id`, `roll`, `behavior` |
| `spell_verbal_failure` | `spell_resolver` | `caster_id`, `spell_name`, `deafened`, `d100_result`, `spell_slot_consumed` |
| `confusion_flee` | `play_loop` | `actor_id`, `behavior` |
| `confusion_attack_override` | `play_loop` | `actor_id`, `behavior`, `roll` |

The `blinded_miss` event follows the same shape as the existing `concealment_miss` event for consistency. The `confusion_behavior` event is the primary BD-07 gate target.

---

## 5. Regression Risk

- **LOW for `conditions.py` additions:** New enum members and factory functions are additive-only. No existing code references `BLINDED`, `DEAFENED`, `ENTANGLED`, or `CONFUSED` by value today; the enum is fail-closed, so new values cannot silently match existing data.
- **LOW for new `ConditionModifiers` flags:** The three new boolean fields default to `False`. `get_condition_modifiers()` in `conditions.py` aggregates flags via OR; `False OR False = False`. No existing condition factory sets any of the three new flags, so all currently live conditions produce the same aggregate output as before. `to_dict()` / `from_dict()` addition with `False` defaults is backward-compatible with existing persisted condition dicts.
- **MEDIUM for `attack_resolver.py`:** The blinded miss check is gated on `attacker_modifiers.is_blinded`, which is `False` for all currently used conditions. The `check_blinded_miss()` call returns `(False, None)` when the flag is absent, consuming no RNG. The `_blinded_attacker_bonus` is 0 when defender is not blinded. **Gold master impact:** Because the d100 is consumed *before* the d20 when `is_blinded` is True, any existing test that injects a blinded attacker would see a shifted RNG sequence. No existing tests use BLINDED entities in fixtures, so no gold master drift is expected. Confirm by checking `tests/fixtures/` fixture files for any `"blinded"` condition keys before implementation.
- **LOW for `spell_resolver.py`:** The deafened check is gated on `is_deafened` (False by default) and `has_verbal_component`. No existing spell fixtures set `is_deafened` on the caster. If `SpellDefinition` does not carry `has_verbal_component`, the field addition with `default=True` is a new field on the dataclass; existing code that constructs `SpellDefinition` without the keyword arg will receive `True` (correct default). No test constructs a deafened caster today.
- **LOW for `play_loop.py`:** The confused branch is gated on `is_confused` from `get_condition_modifiers()`. The check reads one aggregated boolean after existing modifier clearance; it is a `if _actor_is_confused:` guard that falls through when False. No existing fixtures set CONFUSED.
- **LOW for `aoo.py`:** The guard is inside the reactor loop; it is a `continue` skip on `is_confused`. When no reactors are confused (all existing test scenarios), the path is never taken.

---

## 6. What This WO Does NOT Do

- No movement enforcement for BLINDED (half speed) — deferred; movement system not in scope.
- No movement enforcement for ENTANGLED — deferred.
- No Concentration check DC 15 for ENTANGLED spellcasting — deferred to spell-prep WO.
- No initiative penalty (−4) for DEAFENED — initiative is not resolved in the play loop.
- No Spot/Search/Listen skill check enforcement — skill system not present.
- No duration tracking for any of the four conditions — existing condition infrastructure handles remove-by-event only; automatic expiration deferred.
- No source tracking for the confusion "attack_caster" behavior (caster-of-confusion entity reference not stored in the condition instance) — the behavior resolves as "attack_nearest" when caster tracking is unavailable.
- No Silent Spell metamagic interaction — deferred.
- No Blind-Fight feat (PHB p.89) reducing blinded miss chance — deferred.
- No Combat Reflexes interaction with confused AoO suppression — deferred.
- No `delay` / `ready` action enforcement for confused entities — action economy deferred.

---

## 7. Gate Spec

**Gate name:** `ENGINE-CONDITIONS-BLIND-DEAF`
**Test file:** `tests/test_engine_conditions_blind_deaf_gate.py` (new file)

| # | ID | Test | Check |
|---|-----|------|-------|
| 1 | BD-01 | All four ConditionType entries present | `ConditionType("blinded")`, `ConditionType("deafened")`, `ConditionType("entangled")`, `ConditionType("confused")` all resolve without `ValueError` |
| 2 | BD-02 | Blinded attacker 50% miss chance fires | Inject blinded condition on attacker; seed RNG so d100 = 25 (≤50); verify `blinded_miss` event emitted and no `attack_roll` event follows |
| 3 | BD-03 | Blinded defender: attacker gets +2, defender loses DEX to AC | Inject blinded on defender; attacker's `attack_roll` event shows `blinded_attacker_bonus=2`; `dex_penalty` reflects stripped DEX; `target_ac` is base − DEX + condition_ac(−2) |
| 4 | BD-04 | Deafened entity: 20% verbal spell failure | Inject deafened on caster; seed RNG so d100 = 15 (≤20); spell with `has_verbal_component=True`; verify `spell_verbal_failure` event with `deafened=True`, `spell_slot_consumed=True` |
| 5 | BD-05 | Entangled: −2 attack roll applied in attack_resolver | Inject entangled on attacker; `attack_roll` event `condition_modifier = -2`; total = d20 + base − 2 |
| 6 | BD-06 | Entangled: −4 effective DEX applied | Inject entangled on entity with DEX_MOD +3; `get_condition_modifiers` returns `dex_modifier = -4`; effective DEX = base − 4 |
| 7 | BD-07 | Confused: d100 behavior roll at turn start, emits confusion_behavior | Inject confused on actor; run turn dispatch; `confusion_behavior` event emitted with `actor_id`, `roll`, `behavior` keys present |
| 8 | BD-08 | Confused: behavior "babble" → no attack or spell intent dispatched | Seed RNG so d100 = 35 (babble band 21–50); verify no `attack_roll` event and no `spell_cast` event in turn output |
| 9 | BD-09 | Confused: behavior "attack_nearest" → nearest enemy targeted | Seed RNG so d100 = 80 (attack_nearest band 71–100); place one enemy in world_state near actor; verify `confusion_attack_override` event emitted with `behavior="attack_nearest"` |
| 10 | BD-10 | blinded_miss event payload has actor_id, target_id, miss_roll | Inspect `blinded_miss` event from BD-02 scenario; assert all three keys present and `miss_roll` equals the seeded d100 value |

**Test count target:** ENGINE-CONDITIONS-BLIND-DEAF 10/10.

---

## 8. Preflight

```bash
cd f:/DnD-3.5

# Confirm baseline passes before touching any file
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5

# After implementation: run the new gate
python -m pytest tests/test_engine_conditions_blind_deaf_gate.py -v

# Confirm no regression in existing gates
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5
```
