# CP-18A — Mounted Combat & Rider–Mount Coupling (Design Document)

**Status:** DESIGN COMPLETE (NOT IMPLEMENTED)
**Date:** 2026-02-08
**Depends on:** CP-15 (AoO), CP-16 (Conditions), CP-17 (Saves)
**Blocked by gates:** None — G-T1 OPEN (with constraints documented below)

---

## 1. Scope

### 1.1 In Scope (Must Be Designed)

✅ **Rider–Mount Coupling Model**
- Controlled vs independent mount distinction
- Ownership of movement and actions per RAW
- Explicit coupling state representation
- Single shared position model (rider occupies mount's space)

✅ **Movement Delegation**
- Rider movement derived from mount movement
- Interaction with existing diagonal movement rules (1-2-1-2 pattern)
- Position representation as single entity (mount position is rider position)
- Multi-square movement (full move action)

✅ **Attack & AoO Routing**
- Who provokes AoOs (rider, mount, or both) per RAW
- How AoOs target rider vs mount
- Higher ground bonus (+1 melee vs smaller creatures)
- Single melee attack only when mount moves more than 5 feet
- Mounted charge mechanics (double lance damage, Spirited Charge)

✅ **Condition Propagation**
- Explicit enumeration of conditions that transfer rider ↔ mount
- Explicit enumeration of conditions that do NOT transfer
- No ambiguity permitted

✅ **Saving Throws**
- When rider saves vs when mount saves (explicit rules)
- Ride check to stay mounted when mount falls
- Ride check when rider knocked unconscious

✅ **Dismount & Fall Resolution**
- Voluntary dismount (move action, free action with DC 20 Ride)
- Forced dismount (mount defeated, rider falls)
- Mount incapacitation consequences
- Soft fall mechanics (DC 15 Ride check, 1d6 damage on failure)

✅ **Determinism Guarantees**
- Event ordering for mounted combat sequences
- RNG stream usage (explicit documentation)
- Replay invariants maintained

### 1.2 Explicitly Out of Scope (Do NOT Design)

❌ **Spellcasting while mounted** — Blocked by gate, spellcasting system not implemented
❌ **Mounted spell area effects** — Blocked by gate
❌ **Exotic mounts or templates** — Beyond core rules, requires SKR-010
❌ **Ride skill optimization or bonuses** — Skill system not fully implemented
❌ **Feats beyond legality checks** — Feat system deferred (Mounted Combat feat reaction is OUT)
❌ **XP costs, permanence, or transformations** — G-T2A, G-T2B blocked
❌ **Entity forking or relational condition graphs** — G-T3A, G-T3C blocked
❌ **Grapple while mounted** — SKR-005 required
❌ **Mount training or Handle Animal checks** — Out of combat scope

### 1.3 Acceptance Criteria

- [ ] All new tests pass
- [ ] All 594+ existing tests still pass
- [ ] Full suite runs in under 2 seconds
- [ ] Mounted movement triggers AoO correctly (both rider and mount)
- [ ] Rider attacks correctly resolve with higher ground bonus
- [ ] Mount death/fall correctly dismounts rider
- [ ] Deterministic replay verified (10× identical runs)

---

## 2. D&D 3.5e Rules Reference (Authoritative Source)

### 2.1 Primary Sources

| Rule | PHB Page | Summary |
|------|----------|---------|
| Mounted Combat | 157 | Core mounted combat rules |
| Ride Skill | 80-81 | Ride checks and DCs |
| Mounted Combat feat | 98 | Negate mount hit with Ride check (reaction) |
| Mounted Archery feat | 98 | Halved ranged penalty while mounted |
| Ride-By Attack feat | 101 | Move before and after mounted charge |
| Spirited Charge feat | 101 | Double damage (×3 lance) on mounted charge |
| Trample feat | 102-103 | Mounted overrun bonus attack |

### 2.2 Key RAW Excerpts (PHB p.157)

**Mount Acts on Rider's Initiative:**
> "Your mount acts on your initiative count as you direct it. You move at its speed, but the mount uses its action to move."

**Controlled vs Independent (PHB p.157, implied):**
- **Controlled mount:** War-trained mount directed by rider. Mount moves as rider directs but uses its own action to move. Rider and mount share initiative. Mount can attack (Fight with Warhorse, DC 10).
- **Independent mount:** Mount has its own initiative, acts independently. Not in CP-18A scope (requires agency delegation SKR-003).

**Shared Space (PHB p.157):**
> "For simplicity, assume that you share your mount's space during combat."

**Single Attack When Mount Moves (PHB p.157):**
> "If your mount moves more than 5 feet, you can only make a single melee attack."

**Higher Ground Bonus (PHB p.157):**
> "When you attack a creature smaller than your mount that is on foot, you get the +1 bonus on melee attacks for being on higher ground."

**Charge While Mounted (PHB p.157):**
> "If your mount charges, you also take the AC penalty associated with a charge. If you make an attack at the end of the charge, you receive the bonus gained from the charge. When charging on horseback, you deal double damage with a lance."

**Ranged Attacks While Mounted (PHB p.157):**
> "You can use ranged weapons while your mount is taking a double move, but at a –4 penalty on the attack roll. You can use ranged weapons while your mount is running (quadruple speed), at a –8 penalty."

**Mount Falls in Battle (PHB p.157):**
> "If your mount falls, you have to succeed on a DC 15 Ride check to make a soft fall and take no damage. If the check fails, you take 1d6 points of damage."

**Rider Dropped (PHB p.157):**
> "If you are knocked unconscious, you have a 50% chance to stay in the saddle (or 75% if you're in a military saddle). Otherwise you fall and take 1d6 points of damage."

### 2.3 AoO While Mounted (PHB p.137-138)

RAW does not explicitly state whether rider or mount or both provoke. By strict interpretation:
- **Movement provocation:** The mount is the entity moving through threatened squares, so the **mount** provokes.
- **Rider does NOT provoke for movement** (rider is carried, not actively moving).
- **Ranged attack in threatened square:** The **rider** provokes (rider is attacking).
- **Spellcasting in threatened square:** The **rider** provokes (rider is casting).

**Design Decision:** Follow strict RAW interpretation. Movement AoOs target mount only.

---

## 3. Rider–Mount Coupling Model

### 3.1 Core Coupling Schema

```python
# File: aidm/schemas/mounted_combat.py

from dataclasses import dataclass
from typing import Optional
from aidm.schemas.attack import GridPosition

class MountType:
    """Mount classification per PHB p.157."""
    WARHORSE = "warhorse"       # War-trained, controllable in combat
    WARPONY = "warpony"         # War-trained pony
    LIGHT_HORSE = "light_horse" # Not war-trained, DC 20 Ride to control
    HEAVY_HORSE = "heavy_horse" # Not war-trained, DC 20 Ride to control
    PONY = "pony"               # Not war-trained, DC 20 Ride to control

class SaddleType:
    """Saddle types affecting Ride checks."""
    NONE = "none"               # Bareback: -5 Ride penalty
    RIDING = "riding"           # Standard saddle
    MILITARY = "military"       # +2 circumstance bonus, 75% unconscious stay
    PACK = "pack"               # Not for riding


@dataclass
class MountedState:
    """Rider–Mount coupling state stored on RIDER entity.

    DESIGN PRINCIPLE:
    Mount is the "ground truth" for position. Rider position is derived
    from mount position. This prevents position drift and simplifies
    movement resolution.

    Stored in: entities[rider_id]["mounted_state"]
    """

    mount_id: str
    """Entity ID of the mount."""

    is_controlled: bool
    """True if mount is war-trained or rider succeeds DC 20 Ride check.

    Controlled mount: Acts on rider's initiative, moves as directed.
    Uncontrolled mount (CP-18A scope): Rider must spend move action to control.
    Independent mount (OUT OF SCOPE): Mount has own initiative, own actions.
    """

    saddle_type: str = SaddleType.RIDING
    """Saddle type for Ride check bonuses and unconscious fall chance."""

    mounted_at_event_id: int = 0
    """Event ID when mounting occurred (provenance tracking)."""

    def to_dict(self) -> dict:
        """Serialize for WorldState storage."""
        return {
            "mount_id": self.mount_id,
            "is_controlled": self.is_controlled,
            "saddle_type": self.saddle_type,
            "mounted_at_event_id": self.mounted_at_event_id
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MountedState":
        """Deserialize from WorldState storage."""
        return cls(
            mount_id=data["mount_id"],
            is_controlled=data["is_controlled"],
            saddle_type=data.get("saddle_type", SaddleType.RIDING),
            mounted_at_event_id=data.get("mounted_at_event_id", 0)
        )
```

### 3.2 Entity Field Extensions

```python
# Added to aidm/schemas/entity_fields.py

class _EntityFields:
    # ... existing fields ...

    # --- Mounted Combat (CP-18A) ---
    MOUNTED_STATE = "mounted_state"      # MountedState dict on rider
    RIDER_ID = "rider_id"                # Backref on mount to rider entity ID
    MOUNT_SIZE = "mount_size"            # "medium", "large", "huge" for reach/space
    IS_MOUNT_TRAINED = "is_mount_trained"  # True for warhorse/warpony
```

### 3.3 Position Derivation Rule (Critical)

**INVARIANT:** Rider does NOT have independent position when mounted.

```python
def get_entity_position(entity_id: str, world_state: WorldState) -> Optional[GridPosition]:
    """Get entity position, accounting for mounted state.

    If entity is a mounted rider, returns MOUNT's position.
    This ensures rider and mount always share the same grid square.
    """
    entity = world_state.entities.get(entity_id)
    if entity is None:
        return None

    mounted_state = entity.get(EF.MOUNTED_STATE)
    if mounted_state is not None:
        # Rider is mounted - return mount's position
        mount = world_state.entities.get(mounted_state["mount_id"])
        if mount is not None:
            pos_dict = mount.get(EF.POSITION)
            if pos_dict is not None:
                return GridPosition.from_dict(pos_dict)
        # Mount missing - fall through to rider's own position (dismounted)

    # Not mounted or mount missing - return entity's own position
    pos_dict = entity.get(EF.POSITION)
    if pos_dict is not None:
        return GridPosition.from_dict(pos_dict)

    return None
```

---

## 4. Movement Delegation

### 4.1 Movement Intent Schema

```python
@dataclass
class MountedMoveIntent:
    """Intent for mount to move while carrying rider.

    CP-18A SCOPE:
    - Controlled mount only (rider directs movement)
    - Movement uses mount's speed
    - Rider cannot take move action independently while mounted

    This extends StepMoveIntent for multi-step mounted movement.
    """

    rider_id: str
    """Entity directing the movement (must be mounted)."""

    mount_id: str
    """Entity actually moving (derived from rider's mounted_state)."""

    from_pos: GridPosition
    """Starting position of mount."""

    to_pos: GridPosition
    """Destination position of mount."""

    path: Optional[List[GridPosition]] = None
    """Intermediate squares if provided (for AoO checking along path)."""

    is_charge: bool = False
    """True if this is a charge action (PHB p.154)."""

    is_run: bool = False
    """True if mount is running (×4 speed, PHB p.144)."""

    is_double_move: bool = False
    """True if mount is taking double move (×2 speed)."""

    def __post_init__(self):
        if not self.rider_id:
            raise ValueError("rider_id cannot be empty")
        if not self.mount_id:
            raise ValueError("mount_id cannot be empty")
```

### 4.2 Movement Resolution Rules

**Action Economy (PHB p.157):**
- Mount uses its action to move
- Rider may still take a standard action (attack)
- If mount moves more than 5 feet, rider limited to single melee attack

**Diagonal Movement:**
- Uses existing 1-2-1-2 diagonal cost rule
- Applies to mount's movement (rider is carried)

**Movement Event Sequence:**
```
1. mounted_move_declared {rider_id, mount_id, from_pos, to_pos, path}
2. For each step in path:
   2a. Check AoO triggers for MOUNT (not rider)
   2b. Resolve any triggered AoOs against mount
   2c. If mount defeated, emit mount_fallen, dismount rider
   2d. If mount not defeated, emit mount_stepped {step_from, step_to}
3. mount_move_completed {final_pos}
4. (Rider may now take standard action)
```

---

## 5. Attack & AoO Routing

### 5.1 AoO Provocation Rules (RAW-Faithful)

| Provoking Action | Who Provokes | Who Can Be Targeted |
|------------------|--------------|---------------------|
| Mounted movement | Mount | Mount only |
| Rider uses ranged weapon | Rider | Rider only |
| Rider casts spell | Rider | Rider only |
| Rider drinks potion | Rider | Rider only |
| Mount attacks | Mount | Mount only |

**Critical Distinction:** Movement AoOs target the MOUNT because the mount is the entity "moving out of a threatened square" (PHB p.137). The rider is being carried.

### 5.2 AoO Integration with CP-15

```python
def check_mounted_aoo_triggers(
    world_state: WorldState,
    intent: MountedMoveIntent
) -> Tuple[List[AooTrigger], str]:
    """Check AoO triggers for mounted movement.

    Returns:
        Tuple of (triggers, target_entity_id) where target_entity_id
        is the MOUNT's ID (not rider's).
    """
    # AoOs for movement are provoked by the MOUNT
    target_entity_id = intent.mount_id

    # Use existing check_aoo_triggers but with mount as the actor
    triggers = check_aoo_triggers(
        world_state=world_state,
        actor_id=intent.mount_id,  # Mount is the "actor" for movement
        intent=StepMoveIntent(
            actor_id=intent.mount_id,
            from_pos=intent.from_pos,
            to_pos=intent.to_pos
        )
    )

    return triggers, target_entity_id
```

### 5.3 Higher Ground Bonus

```python
def get_mounted_attack_bonus(
    rider_id: str,
    target_id: str,
    world_state: WorldState
) -> int:
    """Calculate mounted attack bonus.

    PHB p.157: +1 melee attack vs creatures smaller than mount
    that are on foot.

    Returns:
        Additional attack bonus (0 or +1)
    """
    rider = world_state.entities.get(rider_id)
    if rider is None:
        return 0

    mounted_state = rider.get(EF.MOUNTED_STATE)
    if mounted_state is None:
        return 0  # Not mounted

    mount = world_state.entities.get(mounted_state["mount_id"])
    if mount is None:
        return 0

    target = world_state.entities.get(target_id)
    if target is None:
        return 0

    # Check if target is mounted (mounted targets don't give higher ground)
    target_mounted = target.get(EF.MOUNTED_STATE) is not None
    if target_mounted:
        return 0

    # Compare sizes (simplified: mount must be larger than target)
    mount_size = mount.get(EF.MOUNT_SIZE, "large")  # Default horse is Large
    target_size = target.get("size", "medium")      # Default humanoid is Medium

    SIZE_ORDER = {"tiny": 0, "small": 1, "medium": 2, "large": 3, "huge": 4}

    mount_size_val = SIZE_ORDER.get(mount_size.lower(), 2)
    target_size_val = SIZE_ORDER.get(target_size.lower(), 2)

    if mount_size_val > target_size_val:
        return 1  # +1 higher ground bonus

    return 0
```

### 5.4 Single Attack Restriction

**Rule:** If mount moves more than 5 feet, rider can only make a single melee attack.

```python
def can_rider_full_attack(
    rider_id: str,
    world_state: WorldState,
    mount_moved_distance: int
) -> bool:
    """Check if rider can make a full attack.

    PHB p.157: If mount moves more than 5 feet, only single attack.

    Args:
        mount_moved_distance: Total distance mount moved this turn (in feet)

    Returns:
        True if full attack allowed, False if only single attack
    """
    return mount_moved_distance <= 5
```

---

## 6. Condition Propagation

### 6.1 Conditions That DO NOT Transfer

These conditions affect only the entity that has them:

| Condition | On Rider | On Mount | Notes |
|-----------|----------|----------|-------|
| Shaken | Rider only | Mount only | Fear is individual |
| Sickened | Rider only | Mount only | Nausea is individual |
| Blinded | Rider only | Mount only | Sight is individual |
| Deafened | Rider only | Mount only | Hearing is individual |
| Dazed | Rider only | Mount only | Mental state individual |
| Confused | Rider only | Mount only | Mental state individual |
| Frightened | Rider only | Mount only | Fear is individual |
| Panicked | Rider only | Mount only | Flees if on mount → dismount |

### 6.2 Conditions With Coupled Effects

These conditions create coupled behaviors:

| Condition | On Mount | Effect on Rider |
|-----------|----------|-----------------|
| **Prone** | Mount prone | Rider falls off (DC 15 Ride to soft fall) |
| **Stunned** | Mount stunned | Mount cannot move, rider stuck |
| **Paralyzed** | Mount paralyzed | Mount falls, rider must dismount |
| **Helpless** | Mount helpless | Rider may dismount freely |
| **Unconscious** | Mount KO'd | Mount falls, rider dismounts |
| **Defeated** | Mount defeated | Mount falls, rider dismounts |

| Condition | On Rider | Effect on Mount |
|-----------|----------|-----------------|
| **Unconscious** | Rider KO'd | 50%/75% stay in saddle, else fall |
| **Paralyzed** | Rider paralyzed | Rider stays mounted (held in saddle) |
| **Grappled** | Rider grappled | OUT OF SCOPE (SKR-005) |

### 6.3 Condition Event Handling

```python
def handle_mounted_condition_change(
    entity_id: str,
    condition_type: str,
    condition_applied: bool,  # True = applied, False = removed
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float
) -> Tuple[WorldState, List[Event]]:
    """Handle condition changes with mounted combat coupling.

    Returns updated WorldState and events for any triggered effects
    (e.g., rider dismount when mount falls).
    """
    events = []

    entity = world_state.entities.get(entity_id)
    if entity is None:
        return world_state, events

    # Check if this entity is a mount with a rider
    rider_id = entity.get(EF.RIDER_ID)
    if rider_id is not None and condition_applied:
        # Mount gained a condition - check rider effects
        if condition_type in {"prone", "stunned", "paralyzed", "helpless",
                              "unconscious", "defeated"}:
            # Mount falls - rider must dismount
            world_state, dismount_events = trigger_forced_dismount(
                rider_id=rider_id,
                mount_id=entity_id,
                reason=f"mount_{condition_type}",
                world_state=world_state,
                rng=rng,
                next_event_id=next_event_id + len(events),
                timestamp=timestamp
            )
            events.extend(dismount_events)

    # Check if this entity is a mounted rider
    mounted_state = entity.get(EF.MOUNTED_STATE)
    if mounted_state is not None and condition_applied:
        if condition_type == "unconscious":
            # Rider KO'd - check if stays in saddle
            world_state, fall_events = check_unconscious_fall(
                rider_id=entity_id,
                mounted_state=mounted_state,
                world_state=world_state,
                rng=rng,
                next_event_id=next_event_id + len(events),
                timestamp=timestamp
            )
            events.extend(fall_events)

    return world_state, events
```

---

## 7. Saving Throws

### 7.1 Save Distribution Rules

| Effect | Who Saves | Notes |
|--------|-----------|-------|
| Area effect spell (Fireball) | Both | Each saves independently |
| Targeted spell on rider | Rider only | Mount not targeted |
| Targeted spell on mount | Mount only | Rider not targeted |
| Fear aura | Both | Each saves independently |
| Breath weapon | Both | Area effect |
| Mounted charge trap | Mount | Mount triggers trap |
| Rider attacked with special | Rider | Effect on rider only |

### 7.2 Integration with CP-17

Mounted combat does not change save resolution mechanics. Saves are resolved per CP-17 for the appropriate entity. The only coupling is:

- If mount fails a save causing a condition that dismounts rider, dismount sequence triggers.
- If rider fails a save causing unconsciousness, unconscious fall check triggers.

---

## 8. Dismount & Fall Resolution

### 8.1 Voluntary Dismount

```python
@dataclass
class DismountIntent:
    """Intent to dismount from a mount.

    PHB p.80 (Ride skill), PHB p.143:
    - Normal dismount: Move action
    - Fast dismount (DC 20 Ride): Free action
    """

    rider_id: str
    """Entity dismounting."""

    fast_dismount: bool = False
    """True to attempt DC 20 fast dismount (free action)."""

    dismount_to: Optional[GridPosition] = None
    """Target square for dismount. If None, DM/system chooses adjacent."""

def resolve_dismount(
    intent: DismountIntent,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float
) -> Tuple[WorldState, List[Event]]:
    """Resolve voluntary dismount.

    Returns:
        Updated world state and events.
    """
    events = []
    rider = world_state.entities.get(intent.rider_id)
    if rider is None:
        return world_state, events

    mounted_state = rider.get(EF.MOUNTED_STATE)
    if mounted_state is None:
        return world_state, events  # Not mounted

    mount = world_state.entities.get(mounted_state["mount_id"])
    if mount is None:
        return world_state, events

    # Fast dismount requires Ride check (deferred - skill system)
    action_type = "free_action" if intent.fast_dismount else "move_action"

    # Determine landing position
    mount_pos = GridPosition.from_dict(mount.get(EF.POSITION))
    dismount_pos = intent.dismount_to or _find_adjacent_empty(mount_pos, world_state)

    # Emit dismount event
    events.append(Event(
        event_id=next_event_id,
        event_type="rider_dismounted",
        timestamp=timestamp,
        payload={
            "rider_id": intent.rider_id,
            "mount_id": mounted_state["mount_id"],
            "action_type": action_type,
            "from_pos": mount_pos.to_dict(),
            "to_pos": dismount_pos.to_dict(),
            "voluntary": True
        },
        citations=[{"source_id": "681f92bc94ff", "page": 80}]
    ))

    # Update world state
    # 1. Remove mounted_state from rider
    # 2. Remove rider_id from mount
    # 3. Set rider position to dismount_pos
    updated_rider = {**rider}
    del updated_rider[EF.MOUNTED_STATE]
    updated_rider[EF.POSITION] = dismount_pos.to_dict()

    updated_mount = {**mount}
    if EF.RIDER_ID in updated_mount:
        del updated_mount[EF.RIDER_ID]

    world_state = world_state.update_entity(intent.rider_id, updated_rider)
    world_state = world_state.update_entity(mounted_state["mount_id"], updated_mount)

    return world_state, events
```

### 8.2 Forced Dismount (Mount Falls/Dies)

```python
def trigger_forced_dismount(
    rider_id: str,
    mount_id: str,
    reason: str,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float
) -> Tuple[WorldState, List[Event]]:
    """Handle forced dismount when mount falls, is defeated, etc.

    PHB p.157: "If your mount falls, you have to succeed on a DC 15 Ride
    check to make a soft fall and take no damage. If the check fails,
    you take 1d6 points of damage."

    Ride check is deferred (skill system not implemented).
    For now: Always roll for damage, take 1d6 on failure.
    """
    events = []

    rider = world_state.entities.get(rider_id)
    if rider is None:
        return world_state, events

    mounted_state = rider.get(EF.MOUNTED_STATE)
    if mounted_state is None:
        return world_state, events

    mount = world_state.entities.get(mount_id)
    mount_pos = GridPosition.from_dict(mount.get(EF.POSITION)) if mount else None

    # Roll Ride check (DC 15 for soft fall)
    # Deferred: For now, simulate with 50% success (no skill system)
    ride_roll = rng.stream("combat").randint(1, 20)
    ride_dc = 15
    # Assume +5 Ride modifier for average rider
    ride_total = ride_roll + 5
    soft_fall = ride_total >= ride_dc

    # Emit ride check event
    events.append(Event(
        event_id=next_event_id,
        event_type="ride_check",
        timestamp=timestamp,
        payload={
            "rider_id": rider_id,
            "check_type": "soft_fall",
            "d20_result": ride_roll,
            "modifier": 5,  # Placeholder
            "total": ride_total,
            "dc": ride_dc,
            "success": soft_fall
        },
        citations=[{"source_id": "681f92bc94ff", "page": 157}]
    ))
    next_event_id += 1
    timestamp += 0.01

    # Calculate falling damage if failed
    fall_damage = 0
    if not soft_fall:
        fall_damage = rng.stream("combat").randint(1, 6)
        events.append(Event(
            event_id=next_event_id,
            event_type="damage_applied",
            timestamp=timestamp,
            payload={
                "entity_id": rider_id,
                "damage": fall_damage,
                "damage_type": "bludgeoning",
                "source": "dismount_fall"
            },
            citations=[{"source_id": "681f92bc94ff", "page": 157}]
        ))
        next_event_id += 1
        timestamp += 0.01

    # Emit dismount event
    dismount_pos = _find_adjacent_empty(mount_pos, world_state) if mount_pos else None

    events.append(Event(
        event_id=next_event_id,
        event_type="rider_dismounted",
        timestamp=timestamp,
        payload={
            "rider_id": rider_id,
            "mount_id": mount_id,
            "action_type": "forced",
            "reason": reason,
            "from_pos": mount_pos.to_dict() if mount_pos else None,
            "to_pos": dismount_pos.to_dict() if dismount_pos else None,
            "voluntary": False,
            "soft_fall": soft_fall,
            "fall_damage": fall_damage
        },
        citations=[{"source_id": "681f92bc94ff", "page": 157}]
    ))

    # Update world state
    updated_rider = {**rider}
    if EF.MOUNTED_STATE in updated_rider:
        del updated_rider[EF.MOUNTED_STATE]
    if dismount_pos:
        updated_rider[EF.POSITION] = dismount_pos.to_dict()

    # Apply fall damage to HP
    current_hp = updated_rider.get(EF.HP_CURRENT, 0)
    updated_rider[EF.HP_CURRENT] = max(0, current_hp - fall_damage)
    if updated_rider[EF.HP_CURRENT] <= 0:
        updated_rider[EF.DEFEATED] = True

    world_state = world_state.update_entity(rider_id, updated_rider)

    # Clear rider_id from mount if mount exists
    if mount is not None:
        updated_mount = {**mount}
        if EF.RIDER_ID in updated_mount:
            del updated_mount[EF.RIDER_ID]
        world_state = world_state.update_entity(mount_id, updated_mount)

    return world_state, events
```

### 8.3 Unconscious Rider Check

```python
def check_unconscious_fall(
    rider_id: str,
    mounted_state: dict,
    world_state: WorldState,
    rng: RNGManager,
    next_event_id: int,
    timestamp: float
) -> Tuple[WorldState, List[Event]]:
    """Check if unconscious rider falls from saddle.

    PHB p.157: "If you are knocked unconscious, you have a 50% chance
    to stay in the saddle (or 75% if you're in a military saddle)."

    Uses "combat" RNG stream for d100 roll.
    """
    events = []

    saddle_type = mounted_state.get("saddle_type", SaddleType.RIDING)
    stay_chance = 75 if saddle_type == SaddleType.MILITARY else 50

    # Roll d100
    roll = rng.stream("combat").randint(1, 100)
    stays_mounted = roll <= stay_chance

    events.append(Event(
        event_id=next_event_id,
        event_type="unconscious_saddle_check",
        timestamp=timestamp,
        payload={
            "rider_id": rider_id,
            "mount_id": mounted_state["mount_id"],
            "saddle_type": saddle_type,
            "stay_chance_percent": stay_chance,
            "roll": roll,
            "stays_mounted": stays_mounted
        },
        citations=[{"source_id": "681f92bc94ff", "page": 157}]
    ))
    next_event_id += 1
    timestamp += 0.01

    if not stays_mounted:
        # Rider falls - take 1d6 damage
        world_state, fall_events = trigger_forced_dismount(
            rider_id=rider_id,
            mount_id=mounted_state["mount_id"],
            reason="rider_unconscious",
            world_state=world_state,
            rng=rng,
            next_event_id=next_event_id,
            timestamp=timestamp
        )
        events.extend(fall_events)

    return world_state, events
```

---

## 9. Event Types

### 9.1 New Event Types for CP-18A

| Event Type | Emitted By | Payload Fields |
|------------|-----------|----------------|
| `rider_mounted` | `resolve_mount()` | `rider_id`, `mount_id`, `saddle_type`, `position` |
| `rider_dismounted` | `resolve_dismount()` | `rider_id`, `mount_id`, `voluntary`, `reason`, `from_pos`, `to_pos`, `fall_damage` |
| `mounted_move_declared` | `resolve_mounted_move()` | `rider_id`, `mount_id`, `from_pos`, `to_pos`, `path`, `is_charge` |
| `mount_stepped` | `resolve_mounted_move()` | `mount_id`, `step_from`, `step_to` |
| `mount_move_completed` | `resolve_mounted_move()` | `mount_id`, `final_pos` |
| `ride_check` | `trigger_forced_dismount()` | `rider_id`, `check_type`, `d20_result`, `modifier`, `total`, `dc`, `success` |
| `unconscious_saddle_check` | `check_unconscious_fall()` | `rider_id`, `mount_id`, `stay_chance_percent`, `roll`, `stays_mounted` |

### 9.2 Event Ordering Guarantee

```
MOUNTED MOVEMENT SEQUENCE:
1. mounted_move_declared {rider_id, mount_id, from_pos, to_pos}
2. For each step in path:
   2a. aoo_triggered (if any) {reactor_id, provoker_id=mount_id}
   2b. attack_roll, damage_applied, etc. (AoO resolution)
   2c. If mount defeated: mount_fallen, rider_dismounted, ABORT
   2d. mount_stepped {step_from, step_to}
3. mount_move_completed {final_pos}
4. (Rider may now take standard action)

MOUNT FALLS SEQUENCE:
1. entity_defeated {entity_id=mount_id} OR condition_applied {condition="prone"}
2. ride_check {check_type="soft_fall", dc=15}
3. damage_applied (if ride check failed)
4. rider_dismounted {voluntary=false, reason="mount_defeated/prone"}
5. (Rider now at dismount position)

RIDER UNCONSCIOUS SEQUENCE:
1. condition_applied {entity_id=rider_id, condition="unconscious"}
2. unconscious_saddle_check {stay_chance, roll, stays_mounted}
3. If !stays_mounted:
   3a. rider_dismounted {reason="rider_unconscious"}
   3b. damage_applied {damage=1d6, source="dismount_fall"}
```

---

## 10. RNG Stream Usage

### 10.1 Stream Assignments

| Operation | RNG Stream | Notes |
|-----------|-----------|-------|
| Mounted attack rolls | `"combat"` | Same as normal attacks |
| AoO attacks against mount | `"combat"` | Same as normal AoOs |
| Ride check (soft fall) | `"combat"` | Combat-related check |
| Unconscious saddle check (d100) | `"combat"` | Combat-related |
| Fall damage (1d6) | `"combat"` | Damage roll |

### 10.2 Consumption Order

For mounted movement with AoO and mount fall:
```
1. AoO attack roll (d20) - "combat"
2. AoO damage roll (dice) - "combat"
3. Ride check (d20) - "combat" (if mount fell)
4. Fall damage (1d6) - "combat" (if ride check failed)
```

**Guarantee:** Same event sequence, same RNG consumption order, identical replay.

---

## 11. Determinism Guarantees

### 11.1 Position Invariant

**INVARIANT:** Rider position is ALWAYS derived from mount position.

```python
# Correct: Get rider position via mount
def get_rider_position(rider_id, world_state):
    rider = world_state.entities.get(rider_id)
    mounted_state = rider.get(EF.MOUNTED_STATE)
    if mounted_state:
        mount = world_state.entities.get(mounted_state["mount_id"])
        return GridPosition.from_dict(mount.get(EF.POSITION))
    return GridPosition.from_dict(rider.get(EF.POSITION))

# WRONG: Never store separate rider position when mounted
# rider[EF.POSITION] = new_position  # DO NOT DO THIS WHEN MOUNTED
```

### 11.2 Coupling State Consistency

**INVARIANT:** If rider has `mounted_state`, mount has `rider_id` pointing back.

```python
def validate_mounted_coupling(world_state: WorldState) -> bool:
    """Validate rider-mount coupling is bidirectionally consistent."""
    for entity_id, entity in world_state.entities.items():
        mounted_state = entity.get(EF.MOUNTED_STATE)
        if mounted_state is not None:
            # Rider claims to be on mount
            mount = world_state.entities.get(mounted_state["mount_id"])
            if mount is None:
                return False  # Mount doesn't exist
            if mount.get(EF.RIDER_ID) != entity_id:
                return False  # Mount doesn't know about rider

        rider_id = entity.get(EF.RIDER_ID)
        if rider_id is not None:
            # Mount claims to have rider
            rider = world_state.entities.get(rider_id)
            if rider is None:
                return False  # Rider doesn't exist
            mounted_state = rider.get(EF.MOUNTED_STATE)
            if mounted_state is None or mounted_state["mount_id"] != entity_id:
                return False  # Rider doesn't know about mount

    return True
```

### 11.3 Replay Test Pattern

```python
def test_mounted_combat_deterministic_replay_10x():
    """Verify 10 identical runs produce identical state hashes."""
    hashes = []
    for _ in range(10):
        # Reset RNG to known seed
        rng = RNGManager(seed=12345)

        # Run mounted combat scenario
        world_state = create_mounted_combat_scenario()
        events = simulate_mounted_combat_turn(world_state, rng)

        # Capture final state hash
        final_hash = world_state.state_hash()
        hashes.append(final_hash)

    # All hashes must be identical
    assert len(set(hashes)) == 1, "Replay produced different hashes"
```

---

## 12. Implementation Plan

### 12.1 Files to Create

| File | Purpose |
|------|---------|
| `aidm/schemas/mounted_combat.py` | MountedState, MountType, SaddleType schemas |
| `aidm/core/mounted_combat.py` | Movement, dismount, condition handling |
| `tests/test_mounted_combat_core.py` | Tier-1 unit tests |
| `tests/test_mounted_combat_integration.py` | Tier-2 integration tests |
| `tests/test_pbha_mounted_combat.py` | Determinism verification |

### 12.2 Files to Modify

| File | Change |
|------|--------|
| `aidm/schemas/entity_fields.py` | Add MOUNTED_STATE, RIDER_ID, MOUNT_SIZE, IS_MOUNT_TRAINED |
| `aidm/core/aoo.py` | Extend check_aoo_triggers for mounted movement (mount as provoker) |
| `aidm/core/attack_resolver.py` | Add higher ground bonus query |
| `aidm/core/conditions.py` | Add mounted condition coupling hooks |
| `aidm/core/play_loop.py` | Handle MountedMoveIntent, DismountIntent |

---

## 13. Pitfalls & Hazards

### 13.1 Position Drift Hazard

**Hazard:** If rider and mount positions are stored independently, they can drift.

**Mitigation:** Rider position is NEVER stored when mounted. All position queries for mounted riders are derived from mount position.

### 13.2 Coupling State Inconsistency

**Hazard:** Rider has `mounted_state` but mount has no `rider_id`, or vice versa.

**Mitigation:** All mount/dismount operations update BOTH entities atomically in same event handler. Validation function checks bidirectional consistency.

### 13.3 AoO Target Confusion

**Hazard:** AoO triggered by mounted movement could incorrectly target rider.

**Mitigation:** Movement AoOs explicitly use `mount_id` as the provoking entity. AoO resolution targets the mount, not rider.

### 13.4 Double Damage Application

**Hazard:** Damage applied to mount could accidentally also apply to rider.

**Mitigation:** Explicit rule: damage to mount affects mount only. Only specific conditions (prone, defeated) trigger rider effects.

---

## 14. Deferred Items (Explicit)

### 14.1 Deferred to Future CPs

| Item | Blocked By | Notes |
|------|------------|-------|
| Mounted Combat feat (reaction) | Feat system (CP-19+) | Negate mount hit with Ride check |
| Mounted Archery | Ranged attack system | Halved ranged penalty |
| Ride-By Attack | Charge system | Move before and after charge |
| Spirited Charge | Charge system | Double/triple damage |
| Trample | Overrun system | Mounted overrun |
| Control mount in battle | Skill system | DC 20 Ride for untrained mount |
| Guide with knees | Skill system | DC 5 Ride to use both hands |

### 14.2 Deferred to SKR Development

| Item | Blocked By | Notes |
|------|------------|-------|
| Independent mounts | SKR-003 (Agency Delegation) | Mount acts on own initiative |
| Grapple while mounted | SKR-005 (Relational Conditions) | Coupled grapple states |
| Exotic mounts | SKR-010 (Transformation History) | Templates, unusual creatures |

---

## 15. 5e Contamination Check

- [x] No advantage/disadvantage mechanics used
- [x] No short rest/long rest terminology
- [x] No proficiency bonus (uses Ride skill ranks)
- [x] Damage types use 3.5e names (bludgeoning)
- [x] No mounted combat concentration rules from 5e

---

## 16. Summary

CP-18A designs a **minimal but complete** mounted combat system that:

1. **Couples rider and mount** via explicit `MountedState` and bidirectional references
2. **Derives rider position** from mount (no drift possible)
3. **Routes AoOs correctly** (mount provokes for movement)
4. **Handles dismount cleanly** (voluntary and forced)
5. **Integrates with CP-15/16/17** without breaking existing systems
6. **Maintains determinism** through explicit RNG stream usage and event ordering
7. **Stays within G-T1** by deferring feats, skills, and relational conditions

**Implementation complexity:** Medium (new schemas, new intents, AoO integration)
**Test complexity:** Medium (coupling validation, event ordering, determinism)
**Risk level:** Low (no closed gates crossed, clean boundaries)

---

**Document Version:** 1.0
**Last Updated:** 2026-02-08
**Status:** DESIGN COMPLETE (Ready for Implementation)
