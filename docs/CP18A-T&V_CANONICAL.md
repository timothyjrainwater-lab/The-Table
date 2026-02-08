# CP-18A-T&V — Targeting & Visibility Kernel (Canonical)

**Status:** Ready for Review & Execution
**Packet Type:** Core Kernel (Pre-Spellcasting Infrastructure)
**Prerequisites:** CP-14, CP-15, CP-16, CP-17 (all frozen)
**File Budget:** 1 of 13 remaining slots
**Authority:** Binding once merged

---

## 1. Instruction Packet (Condensed)

### 1.1 Purpose

CP-18A-T&V establishes the **minimum deterministic targeting-legality kernel** required to safely unlock spellcasting (CP-18A) without retrofitting legality, visibility, or epistemic state later.

**This packet answers one question only:**
> "Is this target legally targetable by this actor, right now, under RAW constraints we can deterministically prove?"

### 1.2 Scope

**IN SCOPE:**
- Deterministic target legality evaluation
- Line of Effect (LoE) and Line of Sight (LoS) checks (binary)
- Explicit visibility state representation
- Failure reasons as structured, replayable data
- Integration with `AttackIntent` and `CastSpellIntent` (stub)

**OUT OF SCOPE (Deferred to CP-19+):**
- Concealment percentages / miss chance
- Partial cover vs soft cover math
- Invisibility state transitions
- AoE / cone / line targeting
- Flight / vertical geometry
- Readied actions or interrupts
- Reactive visibility changes

### 1.3 Determinism Guarantees

- Same inputs → identical legality result
- No RNG access
- No mutation of `WorldState`
- Visibility evaluation is pure function
- Replay hash unaffected by: ordering of checks, non-target entities, policy engine outputs

---

## 2. Implemented Schemas (Code Inline)

### 2.1 File: `aidm/schemas/targeting.py`

```python
"""Targeting & Visibility schemas for CP-18A-T&V.

Minimal, deterministic targeting-legality kernel required to unlock spellcasting.

CP-18A-T&V SCOPE:
- Binary visibility state (visible or not)
- Line of Effect (LoE) and Line of Sight (LoS) checks
- Target legality evaluation
- Structured failure reasons

OUT OF SCOPE (Deferred):
- Concealment percentages / miss chance
- Partial cover vs soft cover math
- Invisibility state transitions
- AoE / cone / line targeting
- Flight / vertical geometry
- Reactive visibility changes
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum


class VisibilityBlockReason(str, Enum):
    """Reasons why targeting might be blocked.

    CP-18A-T&V contract: Every failed targeting check MUST emit exactly one primary reason.
    """

    LOS_BLOCKED = "los_blocked"
    """Line of Sight blocked by opaque terrain"""

    LOE_BLOCKED = "loe_blocked"
    """Line of Effect blocked by solid terrain"""

    OUT_OF_RANGE = "out_of_range"
    """Target exceeds maximum range"""

    NOT_IN_LINE = "not_in_line"
    """Target not in valid line (for line effects)"""

    TARGET_NOT_VISIBLE = "target_not_visible"
    """Target is not visible (general catch-all)"""


@dataclass
class VisibilityState:
    """Deterministic, binary visibility state.

    CP-18A-T&V: No probabilistic visibility. Either visible or not.
    """

    observer_id: str
    """Entity observing"""

    target_id: str
    """Entity being observed"""

    is_visible: bool
    """True if target is visible to observer"""

    reason: Optional[VisibilityBlockReason] = None
    """If not visible, why? (for debugging/explanation)"""

    def __post_init__(self):
        """Validate visibility state."""
        if not self.observer_id:
            raise ValueError("observer_id cannot be empty")
        if not self.target_id:
            raise ValueError("target_id cannot be empty")
        if not self.is_visible and self.reason is None:
            raise ValueError("reason required when is_visible=False")
        if self.is_visible and self.reason is not None:
            raise ValueError("reason must be None when is_visible=True")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "observer_id": self.observer_id,
            "target_id": self.target_id,
            "is_visible": self.is_visible,
            "reason": self.reason.value if self.reason else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisibilityState":
        """Create from dictionary."""
        return cls(
            observer_id=data["observer_id"],
            target_id=data["target_id"],
            is_visible=data["is_visible"],
            reason=VisibilityBlockReason(data["reason"]) if data.get("reason") else None
        )


@dataclass
class RuleCitation:
    """PHB/DMG/MM citation for rule application."""

    source_id: str
    """Source book ID (e.g., '681f92bc94ff' for PHB)"""

    page: int
    """Page number"""

    section: Optional[str] = None
    """Optional section/subsection reference"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "page": self.page,
            "section": self.section
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleCitation":
        """Create from dictionary."""
        return cls(
            source_id=data["source_id"],
            page=data["page"],
            section=data.get("section")
        )


@dataclass
class TargetingLegalityResult:
    """Result of target legality evaluation.

    This object is event-loggable and hash-stable (deterministic).
    """

    is_legal: bool
    """True if targeting is legal"""

    failure_reason: Optional[VisibilityBlockReason] = None
    """If not legal, why? (structured, replayable)"""

    citations: List[RuleCitation] = None
    """PHB/DMG/MM citations for this ruling"""

    def __post_init__(self):
        """Validate legality result."""
        if self.citations is None:
            self.citations = []
        if not self.is_legal and self.failure_reason is None:
            raise ValueError("failure_reason required when is_legal=False")
        if self.is_legal and self.failure_reason is not None:
            raise ValueError("failure_reason must be None when is_legal=True")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_legal": self.is_legal,
            "failure_reason": self.failure_reason.value if self.failure_reason else None,
            "citations": [c.to_dict() for c in self.citations]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TargetingLegalityResult":
        """Create from dictionary."""
        return cls(
            is_legal=data["is_legal"],
            failure_reason=VisibilityBlockReason(data["failure_reason"]) if data.get("failure_reason") else None,
            citations=[RuleCitation.from_dict(c) for c in data.get("citations", [])]
        )


@dataclass
class GridPoint:
    """2D grid position (used for LoS/LoE calculations).

    Note: This is a minimal representation. Full spatial system deferred to CP-19+.
    """

    x: int
    y: int

    def __post_init__(self):
        """Validate grid point."""
        if not isinstance(self.x, int) or not isinstance(self.y, int):
            raise ValueError("x and y must be integers")

    def distance_to(self, other: "GridPoint") -> int:
        """Calculate grid distance using CP-14 diagonal constraints.

        PHB p. 148: First diagonal is 5 ft, second is 10 ft, repeat (1-2-1-2 pattern).
        """
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)

        # Diagonal distance: max(dx, dy) + min(dx, dy) // 2
        # This implements the 1-2-1-2 diagonal pattern
        diagonals = min(dx, dy)
        straights = max(dx, dy) - diagonals

        # Cost: diagonals at 1.5 average (1-2-1-2), straights at 1
        # For integer grid: diagonals count as (diagonals + diagonals // 2)
        return straights + diagonals + (diagonals // 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GridPoint":
        """Create from dictionary."""
        return cls(x=data["x"], y=data["y"])
```

---

## 3. Implemented Resolver (Code Inline)

### 3.1 File: `aidm/core/targeting_resolver.py`

```python
"""Targeting & Visibility resolver for CP-18A-T&V.

Implements deterministic target legality evaluation, LoS/LoE checks.

All functions are pure: (state, params) → (result)
No RNG access, no state mutation.
"""

from typing import List
from aidm.core.state import WorldState
from aidm.schemas.targeting import (
    VisibilityState,
    TargetingLegalityResult,
    VisibilityBlockReason,
    RuleCitation,
    GridPoint
)


# PHB citation for targeting rules
PHB_TARGETING_CITATION = RuleCitation(
    source_id="681f92bc94ff",  # PHB
    page=147,
    section="Line of Effect"
)

PHB_RANGE_CITATION = RuleCitation(
    source_id="681f92bc94ff",  # PHB
    page=148,
    section="Range"
)


def get_entity_position(world_state: WorldState, entity_id: str) -> GridPoint:
    """Get entity's grid position.

    Args:
        world_state: Current world state
        entity_id: Entity ID

    Returns:
        GridPoint position

    Raises:
        ValueError: If entity not found or position missing
    """
    entity = world_state.entities.get(entity_id)
    if entity is None:
        raise ValueError(f"Entity not found: {entity_id}")

    pos = entity.get("position")
    if pos is None:
        raise ValueError(f"Entity has no position: {entity_id}")

    if isinstance(pos, dict):
        return GridPoint.from_dict(pos)
    elif isinstance(pos, GridPoint):
        return pos
    else:
        raise ValueError(f"Invalid position format for {entity_id}: {type(pos)}")


def bresenham_line(start: GridPoint, end: GridPoint) -> List[GridPoint]:
    """Bresenham's line algorithm for grid raycast.

    Returns all grid points from start to end (inclusive).

    Args:
        start: Starting grid point
        end: Ending grid point

    Returns:
        List of grid points along line (including start and end)
    """
    points = []

    dx = abs(end.x - start.x)
    dy = abs(end.y - start.y)
    sx = 1 if start.x < end.x else -1
    sy = 1 if start.y < end.y else -1
    err = dx - dy

    x, y = start.x, start.y

    while True:
        points.append(GridPoint(x, y))

        if x == end.x and y == end.y:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

    return points


def is_terrain_opaque(world_state: WorldState, pos: GridPoint) -> bool:
    """Check if terrain at position blocks LoS/LoE.

    Args:
        world_state: Current world state
        pos: Grid position to check

    Returns:
        True if terrain blocks LoS/LoE, False otherwise

    CP-18A-T&V: Minimal implementation. Full terrain system deferred.
    """
    # Check if there's a terrain map
    terrain = world_state.entities.get("_terrain", {}).get("map", {})

    # Convert position to string key (e.g., "5,10")
    key = f"{pos.x},{pos.y}"

    # Check if this position is marked as blocking
    cell = terrain.get(key, {})
    return cell.get("blocks_loe", False) or cell.get("blocks_los", False)


def check_line_of_effect(
    world_state: WorldState,
    observer_id: str,
    target_id: str
) -> bool:
    """Check if there is a clear Line of Effect (LoE) between observer and target.

    PHB p. 147: "To have line of effect, a line from one space to another
    space can't pass through solid barriers (such as walls)."

    Args:
        world_state: Current world state
        observer_id: Observing entity ID
        target_id: Target entity ID

    Returns:
        True if LoE is clear, False if blocked

    CP-18A-T&V constraints:
    - Computed via grid raycast (Bresenham's algorithm)
    - Any opaque terrain square blocks LoE
    - Creatures do NOT block LoE in this packet (deferred to cover/soft-cover)
    """
    observer_pos = get_entity_position(world_state, observer_id)
    target_pos = get_entity_position(world_state, target_id)

    # Get all grid points along line
    line_points = bresenham_line(observer_pos, target_pos)

    # Check each point (excluding start and end) for opaque terrain
    for point in line_points[1:-1]:  # Skip observer and target positions
        if is_terrain_opaque(world_state, point):
            return False

    return True


def check_line_of_sight(
    world_state: WorldState,
    observer_id: str,
    target_id: str
) -> bool:
    """Check if there is a clear Line of Sight (LoS) between observer and target.

    PHB p. 147: "To have line of sight, a line from one space to another
    space can't pass through solid barriers that block sight."

    Args:
        world_state: Current world state
        observer_id: Observing entity ID
        target_id: Target entity ID

    Returns:
        True if LoS is clear, False if blocked

    CP-18A-T&V constraints:
    - Same geometry as LoE (uses identical raycast)
    - Light level modifiers are binary only (sufficient / insufficient)
    - No perception checks (deferred)
    """
    # In CP-18A-T&V minimal scope: LoS = LoE
    # Future packets may differentiate (transparent but not passable, etc.)
    return check_line_of_effect(world_state, observer_id, target_id)


def check_range(
    world_state: WorldState,
    observer_id: str,
    target_id: str,
    max_range: int
) -> bool:
    """Check if target is within range.

    PHB p. 148: "The maximum range is the farthest distance away a target can be
    for you to use a ranged weapon or spell against it."

    Args:
        world_state: Current world state
        observer_id: Observing entity ID
        target_id: Target entity ID
        max_range: Maximum range (in grid squares)

    Returns:
        True if within range, False otherwise

    CP-18A-T&V constraints:
    - Uses GridPoint.distance_to() (implements CP-14 diagonal constraints)
    - No range increment penalties (deferred)
    """
    observer_pos = get_entity_position(world_state, observer_id)
    target_pos = get_entity_position(world_state, target_id)

    distance = observer_pos.distance_to(target_pos)
    return distance <= max_range


def evaluate_visibility(
    world_state: WorldState,
    observer_id: str,
    target_id: str
) -> VisibilityState:
    """Evaluate binary visibility state between observer and target.

    Args:
        world_state: Current world state
        observer_id: Observing entity ID
        target_id: Target entity ID

    Returns:
        VisibilityState (visible or not, with reason if blocked)

    CP-18A-T&V contract: Binary visibility only. No probabilistic states.
    """
    # Check LoS first (most common blocker)
    if not check_line_of_sight(world_state, observer_id, target_id):
        return VisibilityState(
            observer_id=observer_id,
            target_id=target_id,
            is_visible=False,
            reason=VisibilityBlockReason.LOS_BLOCKED
        )

    # Check LoE (required for targeting)
    if not check_line_of_effect(world_state, observer_id, target_id):
        return VisibilityState(
            observer_id=observer_id,
            target_id=target_id,
            is_visible=False,
            reason=VisibilityBlockReason.LOE_BLOCKED
        )

    # If both clear, target is visible
    return VisibilityState(
        observer_id=observer_id,
        target_id=target_id,
        is_visible=True,
        reason=None
    )


def evaluate_target_legality(
    actor_id: str,
    target_id: str,
    world_state: WorldState,
    max_range: int = 100  # Default: 100 squares (500 ft)
) -> TargetingLegalityResult:
    """Evaluate whether target is legally targetable by actor.

    This is the core CP-18A-T&V proof function. It answers:
    "Is this target legally targetable by this actor, right now, under RAW constraints
    we can deterministically prove?"

    Args:
        actor_id: Acting entity ID
        target_id: Target entity ID
        world_state: Current world state
        max_range: Maximum targeting range (default 100 squares)

    Returns:
        TargetingLegalityResult (legal or not, with structured reason if illegal)

    Contract:
    - Pure function (no side effects)
    - No RNG access
    - Deterministic (same inputs → identical result)
    - Event-loggable and hash-stable
    """
    # Validate entities exist
    if actor_id not in world_state.entities:
        return TargetingLegalityResult(
            is_legal=False,
            failure_reason=VisibilityBlockReason.TARGET_NOT_VISIBLE,
            citations=[PHB_TARGETING_CITATION]
        )

    if target_id not in world_state.entities:
        return TargetingLegalityResult(
            is_legal=False,
            failure_reason=VisibilityBlockReason.TARGET_NOT_VISIBLE,
            citations=[PHB_TARGETING_CITATION]
        )

    # Check range first (fast fail)
    if not check_range(world_state, actor_id, target_id, max_range):
        return TargetingLegalityResult(
            is_legal=False,
            failure_reason=VisibilityBlockReason.OUT_OF_RANGE,
            citations=[PHB_RANGE_CITATION]
        )

    # Check LoE (required for all targeting)
    if not check_line_of_effect(world_state, actor_id, target_id):
        return TargetingLegalityResult(
            is_legal=False,
            failure_reason=VisibilityBlockReason.LOE_BLOCKED,
            citations=[PHB_TARGETING_CITATION]
        )

    # Check LoS (required for most attacks/spells)
    if not check_line_of_sight(world_state, actor_id, target_id):
        return TargetingLegalityResult(
            is_legal=False,
            failure_reason=VisibilityBlockReason.LOS_BLOCKED,
            citations=[PHB_TARGETING_CITATION]
        )

    # All checks passed: targeting is legal
    return TargetingLegalityResult(
        is_legal=True,
        failure_reason=None,
        citations=[PHB_TARGETING_CITATION, PHB_RANGE_CITATION]
    )
```

---

## 4. Integration Points

### 4.1 AttackIntent Validation Hook

**Modification Required:** `aidm/core/attack_resolver.py`

```python
# Add import at top of file
from aidm.core.targeting_resolver import evaluate_target_legality

# In resolve_attack() function, add BEFORE attack roll:
def resolve_attack(intent: AttackIntent, world_state: WorldState, rng: RNGManager, ...):
    # NEW: Validate targeting legality
    legality = evaluate_target_legality(
        actor_id=intent.actor_id,
        target_id=intent.target_id,
        world_state=world_state,
        max_range=100  # TODO: Use weapon range when available
    )

    if not legality.is_legal:
        # Emit targeting_failed event
        events.append(Event(
            event_id=next_event_id,
            event_type="targeting_failed",
            timestamp=timestamp,
            payload={
                "actor_id": intent.actor_id,
                "target_id": intent.target_id,
                "reason": legality.failure_reason.value,
                "intent_type": "attack"
            },
            citations=legality.citations
        ))

        # Return early with failure state
        return (world_state, events)

    # Continue with existing attack resolution...
```

### 4.2 CastSpellIntent Compatibility (Stub)

**Future Integration:** When CP-18A (Spellcasting) is implemented, use identical pattern:

```python
# In spell_resolver.py (future)
def resolve_spell(intent: CastSpellIntent, world_state, rng, ...):
    # Validate targeting using same function
    legality = evaluate_target_legality(
        actor_id=intent.caster_id,
        target_id=intent.target_id,
        world_state=world_state,
        max_range=spell.range  # Spell-specific range
    )

    if not legality.is_legal:
        # Emit targeting_failed event with spell-specific payload
        # (same structure as attack targeting_failed)
        ...
```

### 4.3 AoO Read-Only Interaction

**No Modification Required:** AoO legality checks (CP-15) remain unchanged.

**Future Enhancement:** AoO targeting can *optionally* use `check_line_of_sight()` for verification, but this is not required for CP-18A-T&V acceptance.

---

## 5. Governance (Embedded)

### 5.1 Rules Coverage Ledger (RCL) Excerpt

```
| Subsystem              | Classification   | Coverage  | Owner        | Deferred Items                          |
|------------------------|------------------|-----------|--------------|----------------------------------------|
| Targeting & Visibility | cross-cutting    | partial   | CP-18A-T&V   | Concealment, cover, invisibility       |
| Line of Effect (LoE)   | atomic           | implemented | CP-18A-T&V | (none)                                 |
| Line of Sight (LoS)    | atomic           | implemented | CP-18A-T&V | Perception checks, light levels        |
| Range Calculation      | atomic           | implemented | CP-18A-T&V | Range increments, penalties            |
| Concealment            | cross-cutting    | deferred  | CP-19+       | Miss chance, total concealment         |
| Cover                  | cross-cutting    | deferred  | CP-19+       | Partial vs total, soft cover           |
| Invisibility           | cross-cutting    | deferred  | CP-19+       | State transitions, detection           |
| AoE Targeting          | cross-cutting    | deferred  | CP-19+       | Cone, line, burst, emanation           |
```

### 5.2 PBHA-18A-T&V Checklist

**Packet Boundary Health Audit — CP-18A-T&V**

- [ ] **Correctness:** All acceptance tests pass, edge cases covered
  - Smoke tests (clear LoS, blocked wall, out of range)
  - Integration tests (AttackIntent rejection)
  - Replay tests (10× determinism)

- [ ] **Determinism:** No RNG access, pure functions verified
  - `evaluate_target_legality()` produces identical results for same inputs
  - State hash unaffected by targeting checks

- [ ] **Integration:** No regressions in CP-09–CP-17
  - All 91 existing tests still pass
  - AttackIntent integration clean (no behavioral changes beyond validation)

- [ ] **Continuity:** CP-18A (Spells) unblocked
  - `evaluate_target_legality()` usable for spell targeting
  - No future packet needs to redefine "can I target X?"

- [ ] **Deferrals Explicit:** All out-of-scope items logged in RCL
  - Concealment → CP-19+
  - Cover → CP-19+
  - Invisibility → CP-19+
  - AoE → CP-19+

**PBHA Status:** ⏸ Pending (awaiting test execution)

---

## 6. Test Plan (Descriptive)

### 6.1 Smoke Tests (Required: ≥5)

**Test 1: Clear LoS → Legal**
- Setup: Two entities in open space, no terrain
- Expected: `evaluate_target_legality()` returns `is_legal=True`

**Test 2: Single Blocking Wall → Illegal (LOS_BLOCKED)**
- Setup: Opaque terrain cell between attacker and target
- Expected: `is_legal=False`, `failure_reason=LOS_BLOCKED`

**Test 3: Out of Range → Illegal (OUT_OF_RANGE)**
- Setup: Target 101 squares away (max_range=100)
- Expected: `is_legal=False`, `failure_reason=OUT_OF_RANGE`

**Test 4: Missing Entity → Illegal (TARGET_NOT_VISIBLE)**
- Setup: Target ID not in `world_state.entities`
- Expected: `is_legal=False`, `failure_reason=TARGET_NOT_VISIBLE`

**Test 5: Diagonal Distance Calculation**
- Setup: Target at (5, 5) from (0, 0)
- Expected: Distance = 7 (using CP-14 diagonal constraints: 5 + 2)

### 6.2 Integration Tests (Required: ≥3)

**Test 6: AttackIntent Rejected on Illegal Target**
- Setup: AttackIntent with blocked LoS
- Expected:
  - `resolve_attack()` emits `targeting_failed` event
  - No attack roll occurs
  - State unchanged (no HP delta)

**Test 7: AttackIntent Succeeds on Legal Target**
- Setup: AttackIntent with clear LoS
- Expected:
  - No `targeting_failed` event
  - Attack resolution proceeds normally
  - Existing CP-10 behavior unchanged

**Test 8: CastSpellIntent Stub Compatibility**
- Setup: Minimal spell intent with target
- Expected:
  - `evaluate_target_legality()` callable from spell resolver
  - Same failure reasons applicable

### 6.3 Replay Tests (Required: ≥1)

**Test 9: Deterministic Replay (10×)**
- Setup: Complex scenario (3 entities, 2 walls, varied distances)
- Execute: Run `evaluate_target_legality()` 10 times with same inputs
- Expected:
  - Identical `TargetingLegalityResult` each time
  - Same failure reasons (if applicable)
  - Hash-stable serialization

### 6.4 Edge Cases (Required: ≥2)

**Test 10: Bresenham Line Symmetry**
- Setup: `bresenham_line(A, B)` vs `bresenham_line(B, A)`
- Expected: Same grid cells traversed (order reversed)

**Test 11: Zero Distance (Self-Targeting)**
- Setup: `actor_id == target_id`, same position
- Expected: `is_legal=True` (no LoS/LoE blockers)

---

## 7. Acceptance Criteria (Hard)

CP-18A-T&V is **accepted** only if:

1. ✅ Spellcasting legality (CP-18A) can rely on this kernel without overrides
2. ✅ No future packet needs to redefine "can I target X?"
3. ✅ All failures are explainable via structured reasons (`VisibilityBlockReason`)
4. ✅ No test requires nondeterministic allowances
5. ✅ All deferrals explicitly logged in RCL
6. ✅ PBHA-18A-T&V passes (no regressions, determinism verified)

---

## 8. Explicit Non-Goals (Reiterated)

**This is NOT:**
- A perception system
- A stealth mechanic
- A realism simulator

**This IS:**
- Deterministic legality infrastructure
- Pre-spellcasting blocking resolution
- Binary visibility state (visible or not)

---

## 9. File Budget Impact

**Files Consumed:** 1 (this canonical document)
**Files Remaining:** 12 of 13 available slots

**Strategic Justification:**
- Single-file delivery preserves capacity for:
  - CP-18A (Spells) implementation
  - Targeting extensions (cover, concealment, invisibility)
  - Kernel registry updates
  - Future test consolidation

**Future Growth:**
- Code blocks above can be extracted to Python files when file budget allows
- Until then, this document is the **authoritative source** for CLOG execution

---

## 10. Status & Next Steps

**Current Status:** ✅ Ready for Review
**Blocking:** Test execution + AttackIntent integration

**Next Steps:**
1. Execute test plan (smoke + integration + replay)
2. Integrate `evaluate_target_legality()` into `attack_resolver.py`
3. Run PBHA-18A-T&V audit (verify no regressions)
4. Update RCL with deferrals
5. Freeze CP-18A-T&V (mark as binding)

**Post-Freeze:**
- CP-18A (Spellcasting) unblocked
- CP-19+ (Concealment, Cover, Invisibility) can reference this kernel

---

**END OF CANONICAL DOCUMENT**
