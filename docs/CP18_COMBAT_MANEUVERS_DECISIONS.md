# CP-18: Combat Maneuvers — Design Decisions

**Status:** DESIGN COMPLETE (NOT IMPLEMENTED)
**Date:** 2026-02-08
**Depends on:** CP-15 (AoO), CP-16 (Conditions), CP-17 (Saves), CP-18A (Mounted Combat)
**Blocked by gates:** None — G-T1 OPEN (with degradations documented below)
**Governance:** [CAPABILITY_GATE_ESCALATION_PLAYBOOKS.md](CAPABILITY_GATE_ESCALATION_PLAYBOOKS.md), [DETERMINISM_THREAT_MODEL_CP18_CP19.md](DETERMINISM_THREAT_MODEL_CP18_CP19.md)

---

## 1. Executive Summary

CP-18 designs a **minimal but deterministic** combat maneuvers system that implements four primary maneuvers (Bull Rush, Trip, Overrun, Sunder) and two degraded secondary maneuvers (Disarm, Grapple-lite).

**Design Philosophy:** Clarity over completeness. Determinism over fidelity. Governance over ambition.

All maneuvers resolve **within a single action window** and do not require multi-round state machines.

---

## 2. Scope

### 2.1 In Scope (Must Be Designed)

✅ **Primary Maneuvers (Full Implementation)**
- **Bull Rush** — Push opponent back, Strength vs Strength
- **Trip** — Knock opponent prone, touch attack + Str vs Dex/Str
- **Overrun** — Knock down while moving, Str vs Dex/Str
- **Sunder** — Destroy held object (object-only, no persistent item damage)

✅ **Secondary Maneuvers (Degraded)**
- **Disarm** — Attack roll contest, weapon drops (no persistent item state)
- **Grapple** — Binary grappled condition only (no pinning, no escape loops)

✅ **Shared Mechanics**
- Opposed check resolution (deterministic roll ordering)
- Size modifier system (±4 per category, special scale for grapple)
- AoO provocation rules (maneuvers provoke from defender)
- Success/failure effect application via conditions (CP-16)
- Counter-attack mechanics (trip counter-trip)

✅ **Integration Points**
- CP-15 AoO: Maneuvers that provoke AoOs
- CP-16 Conditions: Prone condition from Trip/Overrun
- CP-18A Mounted: Trip vs mounted opponent (uses Ride check option)

### 2.2 Explicitly Out of Scope (Do NOT Design)

❌ **Full Grapple System**
- No pinning mechanics
- No escape attempt loops
- No grapple damage (damage opponent option)
- No move while grappling
- No draw weapon while grappling
- Blocked by: G-T3C (Relational Conditions) — See Section 5.2

❌ **Multi-Round Maneuver State**
- No maintained grapple across turns
- No sustained hold checks
- No grapple breakout sequences

❌ **Feat Interactions**
- Improved Bull Rush (no AoO from defender) — Feat system deferred
- Improved Disarm (no AoO from defender) — Feat system deferred
- Improved Trip (free attack on success) — Feat system deferred
- Improved Grapple (no AoO from defender) — Feat system deferred
- Improved Overrun (no defender avoidance) — Feat system deferred
- Improved Sunder (no AoO from defender) — Feat system deferred

❌ **Persistent Item State**
- No permanent weapon damage from Sunder (HP tracking)
- No weapon hardness system
- No broken weapon conditions
- Blocked by: Would require item HP/state system (future kernel)

❌ **Skill Integration**
- No Escape Artist checks (grapple escape)
- No Tumble through threatened squares
- No Use Rope for grappling
- Blocked by: Skill system not implemented

❌ **Spellcasting While Grappled**
- No Concentration checks in grapple
- No casting restrictions
- Blocked by: Spellcasting system not implemented

❌ **Trip Weapons**
- No special trip weapon mechanics (spiked chain, whip, etc.)
- No "drop weapon to avoid counter-trip" option
- Blocked by: Weapon property system not implemented

### 2.3 Acceptance Criteria

- [ ] All new tests pass
- [ ] All 626+ existing tests still pass
- [ ] Full suite runs in under 2 seconds
- [ ] Bull Rush moves target deterministically
- [ ] Trip applies Prone condition on success
- [ ] Overrun applies Prone and allows continued movement
- [ ] Sunder deals damage to held object (simplified)
- [ ] Disarm causes weapon drop (no persistent state)
- [ ] Grapple applies Grappled condition (binary, no pinning)
- [ ] All maneuvers provoke AoOs correctly (CP-15 integration)
- [ ] Deterministic replay verified (10× identical runs)
- [ ] Gate safety verified (G-T1 only)

---

## 3. D&D 3.5e Rules Reference

### 3.1 Primary Sources

| Maneuver | PHB Page | Key Rule |
|----------|----------|----------|
| Bull Rush | 154-155 | Strength vs Strength, push 5ft + extra per 5 points |
| Disarm | 155 | Opposed attack rolls with size/weapon modifiers |
| Grapple | 155-157 | Touch attack + grapple check, special size modifiers |
| Overrun | 157-158 | Strength vs Dex/Str, defender may avoid |
| Sunder | 158-159 | Opposed attack rolls, damage vs hardness/HP |
| Trip | 158-160 | Touch attack + Str vs Dex/Str, counter-trip possible |

### 3.2 Size Modifier System

**Standard Maneuvers (Bull Rush, Disarm, Overrun, Sunder, Trip):**
| Size | Modifier |
|------|----------|
| Fine | -16 |
| Diminutive | -12 |
| Tiny | -8 |
| Small | -4 |
| Medium | +0 |
| Large | +4 |
| Huge | +8 |
| Gargantuan | +12 |
| Colossal | +16 |

**Grapple (Special Scale):**
Uses same modifiers but applied to grapple check modifier (BAB + Str + size).

### 3.3 Stability Bonus

Certain creatures receive +4 bonus to resist Bull Rush, Overrun, and Trip:
- More than two legs
- Exceptionally stable (dwarf, earth elemental)
- Quadruped form

### 3.4 AoO Provocation Summary

| Maneuver | Provokes AoO? | From Whom? | Feat Prevention |
|----------|---------------|------------|-----------------|
| Bull Rush | Yes | All threatening, including defender | Improved Bull Rush |
| Disarm | Yes | Defender only | Improved Disarm |
| Overrun | Yes | Defender (enter their space) | Improved Overrun |
| Sunder | Yes | Defender | Improved Sunder |
| Trip (unarmed) | Yes | Defender | Improved Trip |
| Grapple | Yes | Defender | Improved Grapple |

**Note:** Feat-based AoO prevention is OUT OF SCOPE for CP-18.

---

## 4. Maneuver Specifications

### 4.1 Bull Rush

**Action Type:** Standard action (or part of charge)

**Resolution Sequence:**
```
1. Attacker declares BullRushIntent {attacker_id, target_id, is_charge}
2. AoO triggered from all threatening enemies (including target)
3. If attacker defeated by AoO → action_aborted, END
4. Opposed Strength check:
   - Attacker: d20 + Str modifier + size modifier + (charge bonus +2)
   - Defender: d20 + Str modifier + size modifier + (stability bonus +4)
5. If attacker wins:
   - Push defender 5 feet back
   - Additional 5 feet per 5 points difference (up to attacker movement)
   - Attacker may advance into vacated space
6. If defender wins:
   - Attacker moves 5 feet back to origin
   - If origin occupied → attacker falls prone
```

**RNG Consumption Order:**
```
1. AoO attack rolls (per CP-15 ordering)
2. AoO damage rolls (if hits)
3. Attacker Strength check (d20) - "combat" stream
4. Defender Strength check (d20) - "combat" stream
```

**Events Emitted:**
| Event Type | Payload |
|------------|---------|
| `bull_rush_declared` | `attacker_id`, `target_id`, `is_charge` |
| `opposed_check` | `check_type: "strength"`, `attacker_total`, `defender_total` |
| `bull_rush_success` | `pushed_distance`, `new_attacker_pos`, `new_defender_pos` |
| `bull_rush_failure` | `attacker_pushed_back`, `attacker_prone: bool` |

**Gate Safety:** ✅ G-T1 only — No entity forking, no relational conditions, no permanent stat changes.

---

### 4.2 Trip

**Action Type:** Standard action (unarmed melee attack)

**Resolution Sequence:**
```
1. Attacker declares TripIntent {attacker_id, target_id}
2. AoO triggered from defender (unarmed touch attack)
3. If attacker defeated by AoO → action_aborted, END
4. Melee touch attack vs target AC (touch AC)
5. If touch attack misses → trip fails, END
6. Opposed check:
   - Attacker: d20 + Str modifier + size modifier
   - Defender: d20 + max(Str, Dex) modifier + size modifier + (stability +4)
7. If attacker wins:
   - Defender gains Prone condition (CP-16)
8. If defender wins:
   - Defender may counter-trip (opposed check, same formula)
   - If counter-trip succeeds → attacker gains Prone condition
```

**RNG Consumption Order:**
```
1. AoO attack rolls (per CP-15 ordering)
2. AoO damage rolls (if hits)
3. Touch attack roll (d20) - "combat" stream
4. Attacker trip check (d20) - "combat" stream
5. Defender trip check (d20) - "combat" stream
6. [If counter-trip] Defender counter-trip check (d20) - "combat" stream
7. [If counter-trip] Attacker counter-trip defense check (d20) - "combat" stream
```

**Events Emitted:**
| Event Type | Payload |
|------------|---------|
| `trip_declared` | `attacker_id`, `target_id` |
| `touch_attack_roll` | `attacker_id`, `target_id`, `roll`, `total`, `hit: bool` |
| `opposed_check` | `check_type: "trip"`, `attacker_total`, `defender_total` |
| `trip_success` | `target_id` (Prone condition applied) |
| `trip_failure` | `attacker_id`, `counter_trip_allowed: bool` |
| `counter_trip_success` | `attacker_id` (Prone condition applied to original attacker) |

**Mounted Combat Integration (CP-18A):**
- If target is mounted, defender may use Ride check instead of Str/Dex
- If trip succeeds vs mounted target → rider dismounted (forced dismount per CP-18A)

**Gate Safety:** ✅ G-T1 only — Uses existing Prone condition from CP-16.

---

### 4.3 Overrun

**Action Type:** Standard action (taken during move, or part of charge)

**Resolution Sequence:**
```
1. Attacker declares OverrunIntent {attacker_id, target_id, path, is_charge}
2. Defender option: Avoid (step aside, no roll needed)
   - If defender avoids → attacker continues movement, END
3. AoO triggered from defender (attacker enters space)
4. If attacker defeated by AoO → action_aborted, END
5. Opposed check:
   - Attacker: d20 + Str modifier + size modifier + (charge bonus +2)
   - Defender: d20 + max(Str, Dex) modifier + size modifier + (stability +4)
6. If attacker wins:
   - Defender gains Prone condition
   - Attacker continues movement along path
7. If defender wins:
   - Attacker moves 5 feet back
   - If defender wins by 5+: attacker falls prone
```

**Design Decision — Defender Avoidance:**

**Problem:** RAW allows defender to simply avoid, which requires interactive input.

**Solution (DEGRADED):** For CP-18, defender avoidance is controlled by AI/doctrine:
- Monster defenders: Doctrine determines avoidance based on tactical situation
- PC defenders: Assumed to NOT avoid (player can specify via intent if needed later)

This is a **degradation** from full RAW but maintains determinism.

**RNG Consumption Order:**
```
1. AoO attack rolls (per CP-15 ordering)
2. AoO damage rolls (if hits)
3. Attacker overrun check (d20) - "combat" stream
4. Defender overrun check (d20) - "combat" stream
```

**Events Emitted:**
| Event Type | Payload |
|------------|---------|
| `overrun_declared` | `attacker_id`, `target_id`, `path`, `is_charge` |
| `overrun_avoided` | `defender_id` (defender chose to step aside) |
| `opposed_check` | `check_type: "overrun"`, `attacker_total`, `defender_total` |
| `overrun_success` | `defender_id` (Prone condition applied) |
| `overrun_failure` | `attacker_id`, `pushed_back: int`, `prone: bool` |

**Gate Safety:** ✅ G-T1 only — Uses existing Prone condition from CP-16.

---

### 4.4 Sunder

**Action Type:** Standard action (melee attack)

**DEGRADATION (CRITICAL):**

Full Sunder requires:
- Weapon hardness system
- Weapon HP tracking
- Broken weapon condition
- Persistent item state modification

This crosses into **item state management** which is not currently implemented.

**CP-18 Degraded Implementation:**
- Sunder deals damage to held object
- Damage is logged as event (for narrative/audit)
- **NO persistent weapon damage** — weapon is NOT actually broken
- This is a **narrative sunder** only

**Resolution Sequence:**
```
1. Attacker declares SunderIntent {attacker_id, target_id, target_item: "weapon"|"shield"}
2. AoO triggered from defender
3. If attacker defeated by AoO → action_aborted, END
4. Opposed attack rolls:
   - Attacker: d20 + BAB + Str modifier + size modifier
   - Defender: d20 + BAB + Str modifier + size modifier + weapon bonuses
5. If attacker wins:
   - Emit sunder_success event with damage roll
   - Damage logged for narrative purposes ONLY
   - NO state change to weapon/shield
6. If defender wins:
   - No effect
```

**Why Degraded:**
- Weapon HP system requires item entity model
- Persistent damage tracking requires G-T2A-adjacent patterns
- Broken weapon conditions require new condition types
- Full system deferred to Item Management kernel (future)

**Events Emitted:**
| Event Type | Payload |
|------------|---------|
| `sunder_declared` | `attacker_id`, `target_id`, `target_item` |
| `opposed_check` | `check_type: "sunder"`, `attacker_total`, `defender_total` |
| `sunder_success` | `damage_dealt` (narrative only, no state change) |
| `sunder_failure` | (no effect) |

**Gate Safety:** ✅ G-T1 only — No persistent item state changes (degraded).

---

### 4.5 Disarm (DEGRADED)

**DEGRADATION:**

Full Disarm requires:
- Dropped weapon positioning
- Weapon pickup mechanics
- Item ownership transfer

**CP-18 Degraded Implementation:**
- Disarm causes weapon to "drop" (event emitted)
- Dropped weapon is **narratively** in defender's square
- **NO persistent item state** — weapon cannot be picked up mechanically
- Defender is assumed to re-arm at start of next turn (narrative abstraction)

**Resolution Sequence:**
```
1. Attacker declares DisarmIntent {attacker_id, target_id}
2. AoO triggered from defender
3. If AoO deals any damage → disarm automatically fails, END
4. If attacker defeated by AoO → action_aborted, END
5. Opposed attack rolls:
   - Attacker: d20 + BAB + Str modifier + size modifier + weapon modifiers
   - Defender: d20 + BAB + Str modifier + size modifier + weapon modifiers
   - Weapon modifiers: +4 two-handed, -4 light weapon, -4 unarmed
6. If attacker wins:
   - Emit disarm_success event
   - Weapon "dropped" (narrative only)
   - If attacker was unarmed: attacker now "holds" weapon (narrative)
7. If defender wins:
   - Defender may counter-disarm (opposed roll, same formula)
   - No follow-up counter-disarm if that fails
```

**Why Degraded:**
- Weapon ownership transfer requires item entity model
- Pickup mechanics require action economy for items
- Persistent disarmed state requires weapon tracking

**Events Emitted:**
| Event Type | Payload |
|------------|---------|
| `disarm_declared` | `attacker_id`, `target_id` |
| `opposed_check` | `check_type: "disarm"`, `attacker_total`, `defender_total` |
| `disarm_success` | `weapon_dropped` (narrative only) |
| `disarm_failure` | `counter_disarm_allowed: bool` |
| `counter_disarm_success` | (attacker's weapon "dropped") |

**Gate Safety:** ✅ G-T1 only — No persistent item state (degraded).

---

### 4.6 Grapple (DEGRADED — Grapple-Lite)

**CRITICAL GATE PRESSURE: G-T3C (Relational Conditions)**

Full Grapple creates:
- Bidirectional relationship (A grapples B, B is grappled by A)
- Condition state that depends on BOTH entities
- Breaking grapple affects both entities simultaneously
- This is the textbook definition of a **relational condition**

**G-T3C Mitigation — Grapple-Lite:**

Instead of full grapple, CP-18 implements a **binary Grappled condition**:
- Grappled condition (from CP-16) applied to defender only
- No "grappling" condition on attacker
- No bidirectional relationship
- No escape checks (condition removed by DM fiat or standard action)
- No pinning, no grapple damage, no move-while-grappling

**Resolution Sequence:**
```
1. Attacker declares GrappleIntent {attacker_id, target_id}
2. AoO triggered from defender
3. If AoO deals any damage → grapple automatically fails, END
4. If attacker defeated by AoO → action_aborted, END
5. Melee touch attack vs target AC (touch AC)
6. If touch attack misses → grapple fails, END
7. Opposed grapple check:
   - Attacker: d20 + BAB + Str modifier + grapple size modifier
   - Defender: d20 + BAB + Str modifier + grapple size modifier
8. If attacker wins:
   - Defender gains Grappled condition (from CP-16)
   - Attacker does NOT gain any condition (asymmetric)
9. If defender wins:
   - No effect
```

**Grapple Size Modifiers (Special Scale):**
| Size | Modifier |
|------|----------|
| Fine | -16 |
| Diminutive | -12 |
| Tiny | -8 |
| Small | -4 |
| Medium | +0 |
| Large | +4 |
| Huge | +8 |
| Gargantuan | +12 |
| Colossal | +16 |

**What Grapple-Lite DOES:**
- Applies Grappled condition to target
- Grappled condition has: `movement_prohibited: True`, `dex_modifier: -4`
- Target loses Dex bonus to AC vs non-grappling opponents
- Target cannot move normally

**What Grapple-Lite Does NOT Do:**
- No attacker restrictions (attacker is NOT "grappling")
- No escape attempt mechanics (Escape Artist or opposed check)
- No pinning
- No damage while grappling
- No casting restrictions (spellcasting not implemented anyway)
- No draw weapon while grappling

**Grapple Condition Removal:**
- Standard action by defender (no check required — degraded)
- DM/narrative fiat
- Entity defeated

**Why This Degradation:**
Full grapple is **explicitly G-T3C territory** (relational conditions). The grapple-lite version:
- Avoids bidirectional state
- Uses existing Grappled condition from CP-16
- Maintains unidirectional causality (attacker → defender only)
- Can be upgraded to full grapple when G-T3C opens

**Events Emitted:**
| Event Type | Payload |
|------------|---------|
| `grapple_declared` | `attacker_id`, `target_id` |
| `touch_attack_roll` | `attacker_id`, `target_id`, `roll`, `total`, `hit: bool` |
| `opposed_check` | `check_type: "grapple"`, `attacker_total`, `defender_total` |
| `grapple_success` | `target_id` (Grappled condition applied) |
| `grapple_failure` | (no effect) |

**Gate Safety:** ✅ G-T1 only — Asymmetric application avoids G-T3C. See Section 5.2.

---

## 5. Gate Safety Analysis

### 5.1 Gate Status Summary

| Gate | Status | CP-18 Usage |
|------|--------|-------------|
| **G-T1** (Tier 1 Mechanics) | ✅ OPEN | **USED** — All maneuvers within this gate |
| **G-T2A** (Permanent Stat Mutation) | 🔒 CLOSED | ✅ NOT CROSSED — No permanent stat changes |
| **G-T2B** (XP Economy) | 🔒 CLOSED | ✅ NOT CROSSED — No XP costs |
| **G-T3A** (Entity Forking) | 🔒 CLOSED | ✅ NOT CROSSED — No entity creation |
| **G-T3C** (Relational Conditions) | 🔒 CLOSED | ⚠️ MITIGATED — Grapple-lite avoids relational pattern |
| **G-T3D** (Transformation History) | 🔒 CLOSED | ✅ NOT CROSSED — No form changes |

### 5.2 G-T3C (Relational Conditions) — Detailed Analysis

**Gate Definition:**
Conditions that create bidirectional state dependencies between entities where:
- Condition on Entity A affects Entity B's state
- Entity B's state changes affect Entity A
- Circular or recursive propagation is possible

**Why Full Grapple Crosses G-T3C:**

```
FULL GRAPPLE (FORBIDDEN):
┌─────────────┐     grappling     ┌─────────────┐
│  Attacker   │ ───────────────▶  │  Defender   │
│             │                   │  (grappled) │
│ (grappling) │ ◀─────────────── │             │
└─────────────┘   grappled_by     └─────────────┘

Breaking either condition affects BOTH entities.
Escape check by defender affects attacker's state.
This is bidirectional relational state → G-T3C VIOLATED.
```

**Why Grapple-Lite Does NOT Cross G-T3C:**

```
GRAPPLE-LITE (PERMITTED):
┌─────────────┐                   ┌─────────────┐
│  Attacker   │ ───────────────▶  │  Defender   │
│             │   applies         │  (grappled) │
│ (no state)  │   condition       │             │
└─────────────┘                   └─────────────┘

Attacker has NO condition.
Defender's condition does NOT reference attacker.
Breaking condition affects defender ONLY.
This is unidirectional causality → G-T1 PERMITTED.
```

**Trade-offs of Grapple-Lite:**
1. ❌ Attacker is not "grappling" (can take other actions freely)
2. ❌ No escape mechanic (defender cannot break out via check)
3. ❌ No pinning progression
4. ✅ Deterministic (no escape loop state machine)
5. ✅ Gate-safe (no relational conditions)
6. ✅ Simple (one condition, one entity)

**Upgrade Path:**
When G-T3C opens (requires SKR-005 Relational Conditions kernel):
- Add `grappling` condition to attacker
- Add `grappled_by` reference to defender's condition
- Implement escape attempt loop
- Implement pinning mechanics

### 5.3 Item State Pressure (Sunder/Disarm)

**Potential Violation:** Persistent item damage/ownership changes

**Mitigation:** Both Sunder and Disarm are **narrative-only**:
- Events emitted for audit/narration
- No persistent state changes to items
- No weapon HP tracking
- No weapon ownership transfer

This is a **functional degradation** but maintains gate safety.

---

## 6. Determinism Requirements

### 6.1 RNG Stream Usage

**All maneuvers use `"combat"` stream only.**

No new RNG streams introduced.

### 6.2 RNG Consumption Order Contract

For each maneuver, the RNG consumption order is **fixed and documented**:

**General Pattern:**
```
1. AoO attack rolls (per CP-15 initiative-based ordering)
2. AoO damage rolls (per CP-15)
3. Touch attack roll (if applicable)
4. Attacker opposed check roll
5. Defender opposed check roll
6. Counter-attack rolls (if applicable)
```

**Invariant:** Same intent + same RNG seed = identical resolution.

### 6.3 Event Ordering Contract

**All maneuvers emit events in deterministic order:**

```
1. {maneuver}_declared
2. aoo_triggered (per CP-15 ordering)
3. attack_roll, damage_applied (AoO resolution)
4. [If AoO defeated attacker] action_aborted, END
5. touch_attack_roll (if applicable)
6. opposed_check
7. {maneuver}_success OR {maneuver}_failure
8. condition_applied (if success applies condition)
9. [Counter-attack events if applicable]
```

### 6.4 Replay Test Pattern

```python
def test_combat_maneuvers_deterministic_replay_10x():
    """Verify 10 identical runs produce identical state hashes."""
    hashes = []
    for _ in range(10):
        rng = RNGManager(seed=12345)
        world_state = create_maneuver_scenario()
        events = resolve_bull_rush(intent, world_state, rng)
        hashes.append(world_state.state_hash())

    assert len(set(hashes)) == 1, "Replay produced different hashes"
```

---

## 7. Schema Design

### 7.1 Intent Schemas

```python
# File: aidm/schemas/maneuvers.py

@dataclass
class BullRushIntent:
    """Bull rush maneuver intent. PHB p.154-155"""
    attacker_id: str
    target_id: str
    is_charge: bool = False

@dataclass
class TripIntent:
    """Trip maneuver intent. PHB p.158-160"""
    attacker_id: str
    target_id: str

@dataclass
class OverrunIntent:
    """Overrun maneuver intent. PHB p.157-158"""
    attacker_id: str
    target_id: str
    is_charge: bool = False
    defender_avoids: bool = False  # Set by AI/doctrine

@dataclass
class SunderIntent:
    """Sunder maneuver intent (degraded). PHB p.158-159"""
    attacker_id: str
    target_id: str
    target_item: Literal["weapon", "shield"]

@dataclass
class DisarmIntent:
    """Disarm maneuver intent (degraded). PHB p.155"""
    attacker_id: str
    target_id: str

@dataclass
class GrappleIntent:
    """Grapple-lite maneuver intent (degraded). PHB p.155-157"""
    attacker_id: str
    target_id: str
```

### 7.2 Result Schemas

```python
@dataclass
class OpposedCheckResult:
    """Result of an opposed check."""
    check_type: str  # "strength", "trip", "grapple", "disarm", "sunder", "overrun"
    attacker_roll: int
    attacker_modifier: int
    attacker_total: int
    defender_roll: int
    defender_modifier: int
    defender_total: int
    attacker_wins: bool
    margin: int  # Positive = attacker wins by X

@dataclass
class ManeuverResult:
    """Result of a combat maneuver."""
    maneuver_type: str
    success: bool
    events: List[Event]
    provoker_defeated: bool  # True if AoO defeated the maneuver initiator
    condition_applied: Optional[str]  # e.g., "prone", "grappled"
    position_change: Optional[Dict]  # For bull rush: new positions
```

### 7.3 Entity Field Extensions

```python
# Added to aidm/schemas/entity_fields.py

class _EntityFields:
    # ... existing fields ...

    # --- Combat Maneuvers (CP-18) ---
    SIZE_CATEGORY = "size_category"     # "small", "medium", "large", etc.
    STABILITY_BONUS = "stability_bonus"  # +4 for dwarves, quadrupeds
    GRAPPLE_SIZE_MODIFIER = "grapple_size_modifier"  # Special scale for grapple
```

---

## 8. Implementation Plan

### 8.1 Files to Create

| File | Purpose |
|------|---------|
| `aidm/schemas/maneuvers.py` | Intent and result schemas |
| `aidm/core/maneuver_resolver.py` | Core maneuver resolution logic |
| `tests/test_maneuvers_core.py` | Tier-1 unit tests |
| `tests/test_maneuvers_integration.py` | Tier-2 integration tests |

### 8.2 Files to Modify

| File | Change |
|------|--------|
| `aidm/schemas/entity_fields.py` | Add SIZE_CATEGORY, STABILITY_BONUS |
| `aidm/core/play_loop.py` | Route maneuver intents to resolver |
| `aidm/core/aoo.py` | Extend AoO triggers for maneuver intents |

### 8.3 RNG Stream

- **Stream used:** `"combat"` (existing)
- **Consumption order:** Documented per maneuver in Section 4

---

## 9. Test Strategy

### 9.1 Tier-1 Tests (Blocking)

| Test Name | Validates |
|-----------|-----------|
| `test_bull_rush_success_pushes_target` | Bull rush moves target on success |
| `test_bull_rush_failure_pushes_attacker` | Bull rush failure pushes attacker back |
| `test_trip_success_applies_prone` | Trip applies Prone condition |
| `test_trip_counter_trip_on_failure` | Failed trip allows counter-trip |
| `test_overrun_success_applies_prone` | Overrun applies Prone on success |
| `test_grapple_lite_applies_condition` | Grapple applies Grappled condition |
| `test_maneuvers_provoke_aoo` | All maneuvers trigger AoOs correctly |
| `test_aoo_damage_fails_disarm_grapple` | AoO damage causes auto-failure |
| `test_size_modifiers_applied_correctly` | Size modifiers affect opposed checks |

### 9.2 Tier-2 Tests (Integration)

| Test Name | Validates |
|-----------|-----------|
| `test_trip_vs_mounted_uses_ride` | Mounted trip uses Ride check option |
| `test_charge_bull_rush_bonus` | Charge provides +2 to bull rush |
| `test_stability_bonus_applied` | Dwarves/quadrupeds get +4 stability |

### 9.3 PBHA Tests (Determinism)

| Test Name | Validates |
|-----------|-----------|
| `test_pbha_maneuvers_10x_replay` | 10 runs produce identical results |

---

## 10. Explicit Deferrals

### 10.1 Deferred to Future CPs

| Item | Blocked By | Notes |
|------|------------|-------|
| Improved Bull Rush feat | Feat system | No AoO from defender |
| Improved Disarm feat | Feat system | No AoO from defender |
| Improved Trip feat | Feat system | Free attack on success |
| Improved Grapple feat | Feat system | No AoO from defender |
| Improved Overrun feat | Feat system | No defender avoidance |
| Improved Sunder feat | Feat system | No AoO from defender |
| Trip weapons | Weapon property system | Spiked chain, whip, etc. |

### 10.2 Deferred to SKR Development

| Item | Blocked By | Notes |
|------|------------|-------|
| Full grapple system | SKR-005 (Relational Conditions) | Pinning, escape, bidirectional state |
| Persistent weapon damage | Item HP kernel | Broken weapon conditions |
| Escape Artist checks | Skill system kernel | Grapple escape alternative |
| Weapon ownership transfer | Item entity kernel | Disarm pickup mechanics |

---

## 11. 5e Contamination Check

- [x] No advantage/disadvantage mechanics used
- [x] No short rest/long rest terminology
- [x] No proficiency bonus (uses BAB + modifiers)
- [x] Damage types use 3.5e names
- [x] Opposed checks use d20 + modifiers (not d20 contests with ties to attacker)
- [x] Size modifiers are ±4 per category (not 5e's simpler system)
- [x] Counter-trip and counter-disarm mechanics preserved (5e lacks these)

---

## 12. Summary

CP-18 designs a **minimal, deterministic, gate-safe** combat maneuvers system:

| Maneuver | Implementation Level | Gate Status |
|----------|---------------------|-------------|
| Bull Rush | Full | ✅ G-T1 |
| Trip | Full | ✅ G-T1 |
| Overrun | Full (degraded avoidance) | ✅ G-T1 |
| Sunder | Degraded (narrative only) | ✅ G-T1 |
| Disarm | Degraded (no persistence) | ✅ G-T1 |
| Grapple | Degraded (unidirectional) | ✅ G-T1 (avoids G-T3C) |

**Key Design Principles:**
1. **Single action window** — No multi-round state machines
2. **Deterministic ordering** — Fixed RNG consumption order per maneuver
3. **Gate-safe** — All G-T2/G-T3 gates remain closed
4. **Degraded over deferred** — Partial implementation preferred to omission
5. **CP-15/16/18A integration** — Uses existing AoO, conditions, mounted combat

**Implementation Complexity:** Medium
**Test Complexity:** Medium (opposed checks, counter-attacks, AoO integration)
**Risk Level:** Low (all gate-crossing features explicitly degraded or deferred)

---

**Document Version:** 1.0
**Last Updated:** 2026-02-08
**Status:** DESIGN COMPLETE (Ready for Implementation Authorization)
