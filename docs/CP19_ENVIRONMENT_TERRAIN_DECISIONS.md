# CP-19: Environment & Terrain — Design Decisions

**Status:** DESIGN COMPLETE (NOT IMPLEMENTED)
**Date:** 2026-02-08
**Depends on:** CP-15 (AoO), CP-16 (Conditions), CP-18 (Combat Maneuvers), CP-18A (Mounted Combat)
**Blocked by gates:** None — G-T1 OPEN (with degradations documented below)
**Governance:** [CAPABILITY_GATE_ESCALATION_PLAYBOOKS.md](CAPABILITY_GATE_ESCALATION_PLAYBOOKS.md), [DETERMINISM_THREAT_MODEL_CP18_CP19.md](DETERMINISM_THREAT_MODEL_CP18_CP19.md)

---

## 1. Executive Summary

CP-19 designs a **minimal, deterministic** environment and terrain system that modifies movement costs, provides combat modifiers, and handles elevation/falling interactions with forced movement.

**Design Philosophy:** Simple, composable rules. Determinism over realism. Governance over ambition.

All terrain effects resolve **within a single action window** and do not introduce persistent environmental state changes.

---

## 2. Scope

### 2.1 In Scope (Must Be Designed)

✅ **Movement Modifiers**
- Difficult terrain (2× movement cost)
- Stacked movement penalties (4×, 8× cost)
- 5-foot step restrictions in difficult terrain
- Run/charge restrictions

✅ **Cover System**
- Standard cover (+4 AC, +2 Reflex)
- Improved cover (+8 AC, +4 Reflex)
- Total cover (no targeting)
- Soft cover (creatures providing cover)
- Cover blocking AoO execution

✅ **Elevation & Higher Ground**
- Higher ground attack bonus (+1 melee)
- Gradual slopes (no movement penalty, higher ground bonus)
- Steep slopes (2× uphill cost, Balance check downhill)

✅ **Falling Damage**
- 1d6 per 10 feet (max 20d6)
- Falling into water (reduced damage)
- Intentional jump mitigation (DC 15 Jump/Tumble)

✅ **Forced Movement Interactions (CP-18 Integration)**
- Bull Rush into pit/ledge → falling
- Overrun near ledge → falling on failure
- Forced movement into difficult terrain

✅ **Spatial Hazards (Degraded)**
- Pits (binary outcome: fall or not)
- Ledges/drop-offs (falling trigger)
- Shallow water (movement penalty only)

### 2.2 Explicitly Out of Scope (Do NOT Design)

❌ **Weather Systems**
- No rain, snow, wind mechanics
- No visibility from weather
- Deferred to: Future environmental kernel

❌ **Visibility, Lighting, Concealment**
- Already partially covered in visibility.py schemas
- No new visibility mechanics
- Use existing VisionMode, LightLevel, OcclusionTag

❌ **Swimming, Climbing, Flight**
- No Swim check resolution
- No Climb check resolution
- No fly speed mechanics
- Blocked by: Skill system not implemented

❌ **Environmental Damage Over Time**
- No fire spreading
- No cold exposure progression
- No suffocation stages
- Already covered in hazards.py (schema only)
- Blocked by: Requires time advancement integration

❌ **Spell/Magic-Based Terrain**
- No web, grease, entangle
- No wall of fire, wall of ice
- Blocked by: Spellcasting system not implemented

❌ **Persistent Environmental State Changes**
- No terrain destruction
- No ice melting
- No bridges collapsing
- Blocked by: Would require G-T3D (Transformation History)

❌ **Skill Checks Beyond Placeholders**
- No Balance check resolution
- No Tumble check resolution
- No Jump distance calculation
- Placeholder DCs documented, skill system deferred

❌ **Deep/Fast-Moving Water**
- No drowning mechanics
- No current displacement
- No underwater combat
- Deferred to: Aquatic combat kernel

### 2.3 Acceptance Criteria

- [ ] All new tests pass
- [ ] All existing tests still pass
- [ ] Full suite runs in under 2 seconds
- [ ] Difficult terrain doubles movement cost
- [ ] Cover provides correct AC/Reflex bonuses
- [ ] Higher ground provides +1 melee attack
- [ ] Falling damage calculated correctly (1d6/10ft, max 20d6)
- [ ] Forced movement into pit triggers falling
- [ ] Deterministic replay verified (10× identical runs)
- [ ] Gate safety verified (G-T1 only)

---

## 3. D&D 3.5e Rules Reference

### 3.1 Primary Sources

| Topic | PHB Page | DMG Page | Key Rule |
|-------|----------|----------|----------|
| Difficult Terrain | 148-150 | 89-92 | 2× movement cost |
| Cover | 150-152 | — | +4/+8 AC, +2/+4 Reflex |
| Higher Ground | 151 | 90 | +1 melee attack |
| Falling Damage | — | 304 | 1d6/10ft, max 20d6 |
| Steep Slopes | — | 90 | 2× uphill, DC 10 Balance downhill |
| Pits | — | 71-72 | Fall damage + optional spikes |
| Shallow Water | — | 89 | Shallow bog = 2× cost |

### 3.2 Movement Cost Summary

| Terrain Type | Movement Cost | Special Restrictions |
|--------------|---------------|---------------------|
| Normal ground | 1 square | — |
| Difficult terrain | 2 squares | No run/charge |
| Difficult + difficult | 4 squares | No run/charge, no 5-foot step |
| Steep slope (uphill) | 2 squares | — |
| Steep slope (downhill) | 1 square | DC 10 Balance to run/charge |
| Shallow water/bog | 2 squares | No run/charge |

### 3.3 Cover Bonuses

| Cover Type | AC Bonus | Reflex Bonus | AoO Blocked | Hide Bonus |
|------------|----------|--------------|-------------|------------|
| None | +0 | +0 | No | — |
| Standard | +4 | +2 | Yes | — |
| Improved | +8 | +4 | Yes | +10 |
| Total | No targeting | — | Yes | — |
| Soft (creature) | +4 (melee only) | +0 | No | — |

---

## 4. Schema Design

### 4.1 Terrain Cell Schema

```python
# File: aidm/schemas/terrain.py (extension)

@dataclass
class TerrainCell:
    """Terrain properties for a single grid cell.

    Designed for grid-based lookup during movement resolution.
    """

    position: GridPosition
    """Grid coordinates of this cell."""

    elevation: int = 0
    """Elevation in feet above base level (0 = ground floor)."""

    movement_cost: int = 1
    """Movement cost multiplier (1 = normal, 2 = difficult, 4 = very difficult)."""

    terrain_tags: List[str] = field(default_factory=list)
    """List of TerrainTag values affecting this cell."""

    cover_type: Optional[str] = None
    """Cover provided by this cell: 'standard', 'improved', 'total', or None."""

    is_pit: bool = False
    """True if this cell is a pit (triggers falling on entry)."""

    pit_depth: int = 0
    """Depth of pit in feet (0 if not a pit)."""

    is_ledge: bool = False
    """True if this cell is adjacent to a drop-off."""

    ledge_drop: int = 0
    """Height of drop-off in feet (0 if not a ledge)."""
```

### 4.2 Elevation Query Schema

```python
@dataclass
class ElevationDifference:
    """Result of comparing elevation between two positions."""

    attacker_pos: GridPosition
    defender_pos: GridPosition
    attacker_elevation: int
    defender_elevation: int
    difference: int  # Positive = attacker higher

    @property
    def attacker_has_higher_ground(self) -> bool:
        """True if attacker is on higher ground (PHB p.151)."""
        return self.difference > 0
```

### 4.3 Falling Result Schema

```python
@dataclass
class FallingResult:
    """Result of a falling event."""

    entity_id: str
    fall_distance: int  # In feet
    damage_dice: int  # Number of d6 to roll (max 20)
    landing_position: GridPosition
    is_into_water: bool = False
    water_depth: int = 0  # Feet, if falling into water
    is_intentional: bool = False  # True if deliberate jump
```

### 4.4 Cover Check Result

```python
@dataclass
class CoverCheckResult:
    """Result of checking cover between attacker and defender."""

    attacker_id: str
    defender_id: str
    cover_type: Optional[str]  # None, 'standard', 'improved', 'total', 'soft'
    ac_bonus: int
    reflex_bonus: int
    blocks_aoo: bool
    blocks_targeting: bool  # True for total cover
```

### 4.5 Entity Field Extensions

```python
# Added to aidm/schemas/entity_fields.py

class _EntityFields:
    # ... existing fields ...

    # --- Environment & Terrain (CP-19) ---
    ELEVATION = "elevation"           # Current elevation in feet
    IN_DIFFICULT_TERRAIN = "in_difficult_terrain"  # Boolean
    HAS_COVER_FROM = "has_cover_from"  # Dict[entity_id, cover_type]
```

---

## 5. Feature Specifications

### 5.1 Difficult Terrain

**Trigger:** Entity enters cell with `movement_cost > 1`

**Effect:**
- Movement cost multiplied by cell's `movement_cost` value
- Diagonal movement: (base diagonal cost) × movement_cost
- Example: Diagonal into difficult terrain = 3 squares (2 × 1.5 rounded)

**Restrictions:**
- `movement_cost >= 2`: Cannot run or charge through
- `movement_cost >= 4`: Cannot take 5-foot step

**Stacking:**
- Multiple difficult terrain tags: highest movement_cost wins (no multiplication)
- Example: Difficult (2×) + Steep Uphill (2×) = 4× total (PHB p.150)

**RNG:** None (deterministic movement cost lookup)

**Events:**
```
movement_cost_modified {entity_id, from_pos, to_pos, base_cost, modified_cost, reason}
```

---

### 5.2 Cover System

**Trigger:** Attack intent declared, cover check performed

**Resolution:**
1. Determine line from attacker position to defender position
2. Check intervening cells for cover-providing terrain
3. Check intervening entities for soft cover
4. Return highest applicable cover

**Cover Determination (PHB p.151):**
- Ranged: Any line from attacker corner to any defender corner blocked → standard cover
- Melee adjacent: Only wall between squares provides cover
- Melee non-adjacent (reach): Use ranged rules

**Modifiers Applied:**
| Cover Type | AC Bonus | Reflex Bonus | Attack Type |
|------------|----------|--------------|-------------|
| Standard | +4 | +2 | All |
| Improved | +8 | +4 | All |
| Total | No attack | — | Blocked |
| Soft | +4 | +0 | Melee only |

**AoO Blocking:**
- Cannot execute AoO against target with cover relative to you (PHB p.151)
- Exception: Soft cover does NOT block AoO

**RNG:** None (deterministic geometric check)

**Events:**
```
cover_determined {attacker_id, defender_id, cover_type, ac_bonus, reflex_bonus}
```

**Integration with Attack Resolver:**
```python
# In resolve_attack():
cover = check_cover(world_state, attacker_id, target_id)
target_ac = base_ac + cover.ac_bonus + condition_modifiers.ac_modifier
```

---

### 5.3 Higher Ground Bonus

**Trigger:** Melee attack where attacker elevation > defender elevation

**Effect:** +1 attack bonus (melee only, PHB p.151)

**Determination:**
```python
def get_higher_ground_bonus(attacker_id, defender_id, world_state) -> int:
    attacker_elevation = get_entity_elevation(attacker_id, world_state)
    defender_elevation = get_entity_elevation(defender_id, world_state)

    if attacker_elevation > defender_elevation:
        return 1
    return 0
```

**Mounted Combat Interaction (CP-18A):**
- Mounted higher ground bonus already implemented in CP-18A
- CP-19 higher ground is for terrain elevation, stacks with mounted bonus
- Example: Mounted on Large horse (+1) + on hill (+1) = +2 total

**RNG:** None (deterministic comparison)

**Events:**
```
higher_ground_bonus {attacker_id, defender_id, attacker_elevation, defender_elevation, bonus}
```

---

### 5.4 Falling Damage

**Trigger:** Entity falls (forced movement into pit, off ledge, failed save, etc.)

**Damage Calculation (DMG p.304):**
- Base: 1d6 per 10 feet fallen
- Maximum: 20d6 (200 feet)
- All damage is lethal

**Intentional Jump Mitigation:**
- DC 15 Jump or Tumble check (placeholder — skill system deferred)
- Success: First 10 feet = no damage, second 10 feet = nonlethal
- For now: Treat intentional jump as automatic first-10-feet-free

**Falling into Water (Degraded):**
- Water depth >= 10 feet: First 20 feet = no damage
- 20-40 feet into deep water: 1d3 nonlethal per 10 feet
- Beyond 40 feet: 1d6 lethal per 10 feet
- Skill check for diving deferred

**RNG Stream:** `"combat"` for damage rolls

**RNG Consumption Order:**
```
1. Fall distance determined (no RNG)
2. Damage dice rolled (Xd6) - "combat" stream
3. [If into water] Reduced damage calculation
```

**Events:**
```
fall_triggered {entity_id, from_elevation, to_elevation, fall_distance}
falling_damage {entity_id, dice_count, dice_results, total_damage, damage_type}
```

---

### 5.5 Forced Movement into Hazards (CP-18 Integration)

**Trigger:** Bull Rush, Overrun success pushes target into hazardous cell

**Hazard Types:**

| Hazard | Trigger Condition | Effect |
|--------|-------------------|--------|
| Pit | Pushed onto `is_pit=True` cell | Fall damage (pit_depth) |
| Ledge | Pushed off `is_ledge=True` cell | Fall damage (ledge_drop) |
| Difficult terrain | Pushed onto high movement_cost cell | No additional effect (already in cell) |

**Bull Rush into Pit:**
```
1. Bull Rush succeeds, pushes defender N feet
2. Each 5-foot push evaluated sequentially
3. If push would move defender onto pit cell:
   a. Defender enters pit
   b. Fall damage resolved (pit_depth)
   c. Defender's position = pit cell (at pit bottom elevation)
   d. Remaining push distance ignored
```

**Bull Rush off Ledge:**
```
1. Bull Rush succeeds, pushes defender N feet
2. Push moves defender off ledge cell
3. Defender falls (ledge_drop feet)
4. Defender's position = cell below ledge (at lower elevation)
5. Remaining push distance ignored
```

**Overrun near Ledge:**
- If overrun fails by 5+ (attacker prone), attacker position unchanged
- No special ledge interaction for overrun failure

**Determinism Guarantee:**
- Push direction determined by Bull Rush geometry
- Each cell in push path evaluated in order
- First hazard encountered triggers, remaining push canceled

**RNG Consumption Order:**
```
1. Bull Rush opposed check (per CP-18)
2. [If success] Push path calculated (no RNG)
3. [If pit/ledge] Falling damage rolled - "combat" stream
```

**Events:**
```
forced_movement {attacker_id, target_id, maneuver_type, push_distance, push_direction}
hazard_triggered {entity_id, hazard_type, position}
```

---

### 5.6 Shallow Water (Degraded)

**Effect:** Movement cost = 2 squares (difficult terrain)

**Restrictions:**
- Cannot run or charge through shallow water
- Functions identically to difficult terrain

**What is NOT Implemented:**
- No swimming
- No Swim checks
- No drowning
- No underwater combat
- No current/flow effects

**Terrain Tag:** `TerrainTag.SHALLOW_WATER` (already exists in terrain.py)

---

### 5.7 Steep Slopes

**Uphill Movement:**
- Movement cost = 2 squares per cell

**Downhill Movement:**
- Movement cost = 1 square (normal)
- Running/charging downhill: DC 10 Balance check (placeholder)
- Failure: Stumble, movement ends 1d2×5 feet later
- Failure by 5+: Fall prone

**Degradation:**
- Balance check result uses simple pass/fail (skill system deferred)
- Placeholder: Assume DC 10 Balance always passes for creatures with DEX 10+

**Higher Ground:**
- Creature on uphill side gets +1 melee attack vs downhill creature

---

## 6. Determinism Requirements

### 6.1 RNG Stream Usage

| Operation | RNG Stream | Notes |
|-----------|-----------|-------|
| Falling damage | `"combat"` | Xd6 damage roll |
| Cover determination | None | Geometric check |
| Higher ground | None | Elevation comparison |
| Movement cost | None | Cell property lookup |
| Balance check (placeholder) | None | Deterministic pass/fail |

### 6.2 Evaluation Order Contract

**Movement with Terrain:**
```
1. Declare movement intent (from_pos, to_pos, path)
2. For each cell in path:
   a. Check movement cost (difficult terrain)
   b. Accumulate total movement spent
   c. Check for hazards (pit, ledge)
   d. If hazard: resolve immediately, abort remaining path
3. Update entity position
4. Emit movement events
```

**Attack with Cover/Elevation:**
```
1. Declare attack intent
2. Check cover between attacker and defender
3. Check elevation difference
4. Apply modifiers to attack roll
5. Resolve attack (per CP-10/11)
```

**Forced Movement with Hazards:**
```
1. Maneuver success (per CP-18)
2. Calculate push path
3. For each cell in push path:
   a. Check for hazard
   b. If hazard: resolve falling, abort push
4. Update defender position
5. Emit forced_movement and hazard events
```

### 6.3 Replay Guarantee

```python
def test_terrain_deterministic_replay_10x():
    """Verify 10 identical runs produce identical state hashes."""
    hashes = []
    for _ in range(10):
        rng = RNGManager(seed=12345)
        world_state = create_terrain_scenario()
        events = simulate_bull_rush_into_pit(world_state, rng)
        hashes.append(world_state.state_hash())

    assert len(set(hashes)) == 1, "Replay produced different hashes"
```

---

## 7. Gate Safety Analysis

### 7.1 Gate Status Summary

| Gate | Status | CP-19 Usage |
|------|--------|-------------|
| **G-T1** (Tier 1 Mechanics) | ✅ OPEN | **USED** |
| **G-T2A** (Permanent Stat Mutation) | 🔒 CLOSED | ✅ NOT CROSSED |
| **G-T2B** (XP Economy) | 🔒 CLOSED | ✅ NOT CROSSED |
| **G-T3A** (Entity Forking) | 🔒 CLOSED | ✅ NOT CROSSED |
| **G-T3C** (Relational Conditions) | 🔒 CLOSED | ✅ NOT CROSSED |
| **G-T3D** (Transformation History) | 🔒 CLOSED | ✅ NOT CROSSED |

### 7.2 Potential Gate Pressure Points

| Feature | Risk | Mitigation |
|---------|------|------------|
| Terrain modification | G-T3D | No terrain changes — terrain is read-only |
| Hazard entities | G-T3A | No hazard entities — terrain properties only |
| Ongoing penalties | G-T2A | Situational modifiers only — no permanent stats |
| Shared terrain state | G-T3C | No relational terrain — cell properties independent |

### 7.3 What Would Cross Gates

❌ **Terrain that remembers history** (G-T3D)
- Ice that melts over time
- Bridges that collapse after X crossings
- Fires that spread

❌ **Terrain as entities** (G-T3A)
- Spawning pit trap entity
- Creating hazard creature on trigger
- Terrain with HP/conditions

❌ **Relational terrain effects** (G-T3C)
- "Bound" terrain affecting multiple creatures
- Terrain condition applying to all in area
- Zone effects with participant tracking

---

## 8. Implementation Plan

### 8.1 Files to Create

| File | Purpose |
|------|---------|
| `aidm/core/terrain_resolver.py` | Terrain query and effect resolution |
| `tests/test_terrain_effects.py` | Tier-1 terrain tests |
| `tests/test_terrain_integration.py` | Tier-2 integration tests |

### 8.2 Files to Modify

| File | Change |
|------|--------|
| `aidm/schemas/terrain.py` | Add TerrainCell, ElevationDifference, FallingResult |
| `aidm/schemas/entity_fields.py` | Add ELEVATION, IN_DIFFICULT_TERRAIN |
| `aidm/core/attack_resolver.py` | Add cover and higher ground queries |
| `aidm/core/aoo.py` | Add cover-blocks-AoO check |
| `aidm/core/maneuver_resolver.py` | Add forced movement hazard handling |

### 8.3 RNG Stream

- **Stream used:** `"combat"` (falling damage only)
- **New streams:** None

---

## 9. Test Strategy

### 9.1 Tier-1 Tests (Blocking)

| Test Name | Validates |
|-----------|-----------|
| `test_difficult_terrain_doubles_movement_cost` | 2× cost in difficult terrain |
| `test_standard_cover_provides_ac_bonus` | +4 AC from standard cover |
| `test_improved_cover_provides_enhanced_bonus` | +8 AC from improved cover |
| `test_total_cover_blocks_targeting` | Cannot target through total cover |
| `test_higher_ground_melee_bonus` | +1 melee from higher elevation |
| `test_falling_damage_calculation` | 1d6 per 10 feet, max 20d6 |
| `test_bull_rush_into_pit_triggers_fall` | Forced movement into pit |

### 9.2 Tier-2 Tests (Integration)

| Test Name | Validates |
|-----------|-----------|
| `test_cover_blocks_aoo_execution` | AoO blocked by cover |
| `test_mounted_plus_terrain_higher_ground` | Stacked elevation bonuses |
| `test_forced_movement_off_ledge` | Bull rush off ledge |

### 9.3 PBHA Tests (Determinism)

| Test Name | Validates |
|-----------|-----------|
| `test_pbha_terrain_10x_replay` | 10 runs produce identical results |

---

## 10. Explicit Deferrals

### 10.1 Deferred to Future CPs

| Item | Blocked By | Notes |
|------|------------|-------|
| Balance checks | Skill system | Use placeholder pass/fail |
| Tumble checks | Skill system | Use placeholder |
| Jump distance | Skill system | Use placeholder |
| Climb checks | Skill system | Not designed |
| Swim checks | Skill system | Not designed |

### 10.2 Deferred to SKR Development

| Item | Blocked By | Notes |
|------|------------|-------|
| Terrain transformation | SKR-010 (Transformation History) | No terrain changes |
| Hazard entities | SKR-001 (Entity Forking) | No entity creation |
| Persistent terrain damage | SKR-002 (Permanent Stat) | No ongoing penalties |

### 10.3 Deferred to Future Kernels

| Item | Future Kernel | Notes |
|------|---------------|-------|
| Weather effects | Environmental Kernel | Rain, wind, snow |
| Underwater combat | Aquatic Combat Kernel | Swimming, drowning |
| Flight | Movement Kernel | Fly speeds, hovering |
| Magical terrain | Spellcasting Kernel | Web, grease, walls |

---

## 11. 5e Contamination Check

- [x] No advantage/disadvantage mechanics used
- [x] No short rest/long rest terminology
- [x] Cover uses +4/+8 bonuses (not half/three-quarters)
- [x] Difficult terrain uses 2× cost (not +10 feet)
- [x] Falling uses 1d6/10ft (not d6 max 20d6 at 200ft)
- [x] No "heavily obscured" terminology (use OcclusionTag)
- [x] Higher ground is +1 melee (not advantage)

---

## 12. Summary

CP-19 designs a **minimal, deterministic, gate-safe** environment and terrain system:

| Feature | Implementation Level | Gate Status |
|---------|---------------------|-------------|
| Difficult Terrain | Full | ✅ G-T1 |
| Cover System | Full | ✅ G-T1 |
| Higher Ground | Full | ✅ G-T1 |
| Falling Damage | Full | ✅ G-T1 |
| Forced Movement into Hazards | Full | ✅ G-T1 |
| Shallow Water | Degraded (difficult terrain only) | ✅ G-T1 |
| Steep Slopes | Degraded (placeholder skill checks) | ✅ G-T1 |

**Key Design Principles:**
1. **Read-only terrain** — No terrain modification during play
2. **Deterministic queries** — All terrain effects are pure lookups
3. **RNG isolation** — Only falling damage uses RNG ("combat" stream)
4. **Composable modifiers** — Cover, elevation, conditions stack cleanly
5. **CP-18 integration** — Forced movement handles hazards explicitly

**Implementation Complexity:** Low-Medium
**Test Complexity:** Medium (geometric cover checks, hazard interactions)
**Risk Level:** Low (no gate-crossing features)

---

**Document Version:** 1.0
**Last Updated:** 2026-02-08
**Status:** DESIGN COMPLETE (Ready for Implementation Authorization)
