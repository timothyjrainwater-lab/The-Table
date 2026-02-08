# SKR-002 Design Document: Permanent Stat Modification Kernel

**Version:** 1.0
**Date:** 2026-02-08
**Status:** ✅ APPROVED (Design Frozen)
**Kernel ID:** SKR-002
**Blocking Gate:** G-T2A (Permanent Stat Mutation)

---

## 1. Assumptions

1. **Base stats are immutable post-creation**: An entity's base ability scores (STR/DEX/CON/INT/WIS/CHA) are set at entity creation and never directly mutated thereafter. All changes flow through modifier layers.

2. **CP-16 temporary modifiers exist and are stable**: The current condition modifier system (CP-16) handles duration-limited, typed bonuses/penalties. SKR-002 does not replace or modify CP-16.

3. **Event sourcing is mandatory**: All state mutations must emit events. No direct state writes.

4. **Derived stats recalculation is deterministic**: HP max, AC, saves, attack bonuses, skill modifiers all derive from ability scores via deterministic functions. Recalculation order must be stable.

5. **Death is a binary state**: An entity is alive or dead. Death may be triggered by ability score reaching 0, but resurrection mechanics are out of scope (G-T2B/SKR-008).

6. **Restoration reverses drain only**: Restoration-type effects can only remove permanent penalties, not grant bonuses beyond the original base score.

7. **Inherent bonuses are rare and permanent**: Wish-granted +1 stat increases and magic tome/manual bonuses are permanent increases that persist forever (no duration).

8. **No entity forking dependencies**: Permanent stat modifiers apply to single entities. No parent/child lineage interactions (G-T3A/SKR-001).

9. **No XP cost tracking**: Effects that grant permanent stat changes may have XP costs in the rules, but cost enforcement is deferred to SKR-008 (G-T2B).

10. **Replay stability is non-negotiable**: Given identical event log, all stat calculations must produce identical results across replays.

---

## 2. Invariants

### 2.1 Core Invariants

**INV-1: Base Stats Never Mutate**
`entity.base_stats[ability]` is set once at entity creation and never changes. All modifications stored separately.

**INV-2: Permanent Modifiers Persist Indefinitely**
Permanent modifiers have no duration. They remain until explicitly removed by reversal event (e.g., Restoration).

**INV-3: Temporary and Permanent Layers Are Separate**
Permanent modifiers (SKR-002) and temporary modifiers (CP-16) occupy distinct layers. No overlap in storage or lifecycle.

**INV-4: Effective Ability Score = Base + Permanent + Temporary**
Calculation order is deterministic:
```
effective_score = base_score + sum(permanent_modifiers) + sum(temporary_modifiers)
```

**INV-5: Derived Stats Recalculate Atomically**
When ability scores change, all derived stats (HP max, AC, saves, etc.) recalculate in a single atomic operation before the next action resolves.

**INV-6: Ability Score Floor is 0 (Death Trigger)**
If `effective_score <= 0` for any ability, entity dies immediately. No negative ability scores.

**INV-7: HP Max Cannot Exceed Current HP (Implicit Healing)**
If HP max decreases below current HP, current HP is reduced to new max. If HP max increases, current HP does NOT automatically increase (healing requires separate event).

**INV-8: Permanent Penalties and Bonuses Stack Within Type**
Multiple permanent drain effects stack (e.g., two Shadows draining STR). Multiple inherent bonuses stack (e.g., Wish +1 STR, then another Wish +1 STR).

**INV-9: Restoration Cannot Exceed Base**
Restoration removes permanent penalties. It cannot increase an ability score above `base + permanent_bonuses`.

**INV-10: Event Ordering is Deterministic**
Events emitted in this order:
1. `permanent_stat_modified` (source event)
2. `derived_stats_recalculated` (consequence event)
3. `hp_changed` (if HP max decreased below current HP)
4. `entity_died` (if ability score reached 0)

### 2.2 Replay Determinism Invariants

**INV-11: Same Events → Same State**
Replaying the same event log produces identical final ability scores and derived stats.

**INV-12: No Hidden RNG Consumption**
Permanent stat modification does NOT consume RNG. All changes are deterministic from event payloads.

**INV-13: No External State Dependencies**
Derived stat recalculation depends only on entity state, not world state or other entities.

---

## 3. Schemas (Conceptual)

### 3.1 Entity State Extensions

Each entity gains a new state layer:

```python
entity.permanent_stat_modifiers = {
    "str": {
        "drain": -4,         # Cumulative permanent penalties (negative)
        "inherent": +2       # Cumulative permanent bonuses (positive)
    },
    "dex": {"drain": 0, "inherent": 0},
    "con": {"drain": -2, "inherent": 0},
    "int": {"drain": 0, "inherent": 0},
    "wis": {"drain": 0, "inherent": 0},
    "cha": {"drain": 0, "inherent": 0}
}
```

**Separation by Type:**
- `drain`: Permanent penalties (negative). Sources: Shadow STR drain, Vampire CON drain, Feeblemind (INT → 1).
- `inherent`: Permanent bonuses (positive). Sources: Wish, magic tomes/manuals.

**Why Two Fields?**
- Restoration removes `drain` only, never touches `inherent`.
- Drain and inherent stack independently.
- Allows precise reversal (Restoration -2 CON drain → drain field adjusted, inherent untouched).

### 3.2 Derived Stats Storage

Derived stats are calculated, not stored:

```python
# NOT stored in entity state:
hp_max = base_hp + (con_modifier * hd_count) + other_bonuses
ac = 10 + dex_modifier + armor_bonus + shield_bonus + ...
fortitude_save = base_fort + con_modifier + ...
```

**Exception: Current HP is stored** (mutable resource), but HP max is always recalculated on-demand.

### 3.3 Event Payloads

#### Event: `permanent_stat_modified`

```json
{
    "event_type": "permanent_stat_modified",
    "entity_id": "char_12345",
    "ability": "str",
    "modifier_type": "drain",
    "amount": -2,
    "source": "shadow_strength_drain",
    "reversible": true
}
```

#### Event: `permanent_stat_restored`

```json
{
    "event_type": "permanent_stat_restored",
    "entity_id": "char_12345",
    "ability": "con",
    "modifier_type": "drain",
    "amount_removed": 2,
    "source": "restoration_spell"
}
```

#### Event: `derived_stats_recalculated`

```json
{
    "event_type": "derived_stats_recalculated",
    "entity_id": "char_12345",
    "ability_affected": "con",
    "old_effective_score": 14,
    "new_effective_score": 12,
    "hp_max_old": 45,
    "hp_max_new": 35,
    "recalculated_stats": ["hp_max", "fortitude_save"]
}
```

#### Event: `ability_score_death`

```json
{
    "event_type": "ability_score_death",
    "entity_id": "char_12345",
    "ability": "str",
    "final_score": 0,
    "cause": "shadow_strength_drain"
}
```

---

## 4. Event Model

### 4.1 Event Flow: Permanent Penalty Applied

**Scenario:** Shadow drains 2 STR from a fighter (base STR 16, current effective STR 16).

**Event Sequence:**

1. **`permanent_stat_modified`**
   - `ability: "str"`, `modifier_type: "drain"`, `amount: -2`
   - Entity's `permanent_stat_modifiers["str"]["drain"]` becomes -2
   - Effective STR: 16 (base) + (-2 drain) = 14

2. **`derived_stats_recalculated`**
   - `ability_affected: "str"`
   - `old_effective_score: 16`, `new_effective_score: 14`
   - STR modifier changes from +3 to +2
   - Recalculated: attack bonus, damage bonus, CMB, carrying capacity
   - No HP change (STR doesn't affect HP)

3. **(No death event, STR > 0)**

**Replay Guarantee:** Given event 1, event 2 is deterministically emitted. No RNG, no external dependencies.

---

### 4.2 Event Flow: Permanent Penalty Causes Death

**Scenario:** Shadow drains 3 STR from a wizard (base STR 8, current effective STR 8).

**Event Sequence:**

1. **`permanent_stat_modified`**
   - `ability: "str"`, `modifier_type: "drain"`, `amount: -3`
   - Entity's `permanent_stat_modifiers["str"]["drain"]` becomes -3
   - Effective STR: 8 + (-3) = 5

2. **`derived_stats_recalculated`**
   - `old_effective_score: 8`, `new_effective_score: 5`

3. **(Wizard survives, STR = 5 > 0)**

**Scenario 2:** Shadow drains 5 more STR (total 8 drain).

**Event Sequence:**

1. **`permanent_stat_modified`**
   - `amount: -5`
   - Cumulative drain: -3 + (-5) = -8
   - Effective STR: 8 + (-8) = 0

2. **`ability_score_death`**
   - `ability: "str"`, `final_score: 0`
   - Entity dies immediately

3. **`entity_died`** (existing CP event)
   - `cause: "ability_score_death"`

**Replay Guarantee:** Death is deterministic. Same drain sequence → same death outcome.

---

### 4.3 Event Flow: Restoration Removes Drain

**Scenario:** Cleric casts Lesser Restoration on the fighter (STR 14, -2 drain).

**Event Sequence:**

1. **`permanent_stat_restored`**
   - `ability: "str"`, `modifier_type: "drain"`, `amount_removed: 2`
   - Entity's `permanent_stat_modifiers["str"]["drain"]` becomes 0
   - Effective STR: 16 (base) + 0 = 16

2. **`derived_stats_recalculated`**
   - `old_effective_score: 14`, `new_effective_score: 16`
   - Attack/damage bonuses recalculated

**Replay Guarantee:** Restoration events are deterministic. Amount removed is explicit in event payload.

---

### 4.4 Event Flow: Inherent Bonus Applied

**Scenario:** Wizard uses Wish to gain +1 INT (base INT 18).

**Event Sequence:**

1. **`permanent_stat_modified`**
   - `ability: "int"`, `modifier_type: "inherent"`, `amount: +1`
   - Entity's `permanent_stat_modifiers["int"]["inherent"]` becomes +1
   - Effective INT: 18 (base) + 1 (inherent) = 19

2. **`derived_stats_recalculated`**
   - `old_effective_score: 18`, `new_effective_score: 19`
   - INT modifier changes from +4 to +4 (no modifier change, but skill points may change)

**Replay Guarantee:** Inherent bonuses are permanent and deterministic.

---

### 4.5 Event Flow: CON Drain with HP Max Reduction

**Scenario:** Vampire drains 4 CON from a fighter (base CON 14, HD 5, current HP 45/45).

**Step 1: Apply Drain**

1. **`permanent_stat_modified`**
   - `ability: "con"`, `modifier_type: "drain"`, `amount: -4`
   - Effective CON: 14 + (-4) = 10
   - CON modifier: +2 → 0

2. **`derived_stats_recalculated`**
   - `hp_max_old: 45`, `hp_max_new: 35` (lost +2 CON mod × 5 HD = 10 HP)
   - Current HP: 45 > 35 (exceeds new max)

3. **`hp_changed`**
   - `old_hp: 45`, `new_hp: 35`, `cause: "hp_max_reduction"`
   - Current HP clamped to new max

**Step 2: Restoration**

1. **`permanent_stat_restored`**
   - `ability: "con"`, `amount_removed: 4`
   - Effective CON: 14 (restored)

2. **`derived_stats_recalculated`**
   - `hp_max_new: 45` (back to original)
   - Current HP: 35 (does NOT automatically heal)

3. **(No automatic healing event)**

**Key Insight:** HP max increase does NOT grant free healing. Separate healing effect required.

**Replay Guarantee:** HP clamping is deterministic. Current HP never exceeds max.

---

## 5. Derived Stat Recalculation

### 5.1 Recalculation Triggers

Derived stats recalculate **immediately after** any event that changes ability scores:
- `permanent_stat_modified`
- `permanent_stat_restored`
- `condition_applied` (if condition affects ability scores via CP-16)
- `condition_removed`

### 5.2 Recalculation Order

**Phase 1: Calculate Effective Ability Scores**
```python
For each ability (STR/DEX/CON/INT/WIS/CHA):
    effective_score = base + permanent_drain + permanent_inherent + temporary_modifiers
    effective_modifier = (effective_score - 10) // 2
```

**Phase 2: Recalculate Derived Stats (Deterministic Order)**
1. **HP Max**
   `hp_max = base_hp + (con_modifier × hd_count) + other_permanent_bonuses`
2. **AC**
   `ac = 10 + dex_modifier + armor + shield + natural + deflection + ...`
3. **Saves**
   - Fortitude: `base_fort + con_modifier + ...`
   - Reflex: `base_ref + dex_modifier + ...`
   - Will: `base_will + wis_modifier + ...`
4. **Attack Bonuses**
   `melee_attack = bab + str_modifier + ...`
   `ranged_attack = bab + dex_modifier + ...`
5. **Skill Modifiers**
   Each skill recalculates based on governing ability modifier

**Phase 3: Apply Constraints**
- If `current_hp > hp_max`, emit `hp_changed` event (clamp to max)
- If any `effective_score <= 0`, emit `ability_score_death` event

### 5.3 Why This Order?

**Determinism:** Fixed order eliminates race conditions.
**Dependencies:** HP max depends on CON modifier. AC depends on DEX modifier. Order respects dependencies.
**Atomicity:** All derived stats update in one operation. No intermediate states visible to other systems.

---

## 6. Edge Constraints

### 6.1 Ability Score Reaches 0

**Rule:** If `effective_score <= 0` for **any** ability, entity dies immediately.

**Special Cases:**
- **STR 0:** Helpless, cannot move. Death.
- **DEX 0:** Cannot move. Death.
- **CON 0:** Dead (RAW: living creatures with CON 0 die).
- **INT 0:** Comatose (but constructs/undead may have INT -). For living creatures: death.
- **WIS 0:** Comatose, unresponsive. Death.
- **CHA 0:** No sense of self. Death (RAW ambiguous, we choose death for determinism).

**Resurrection:** Out of scope (SKR-008/G-T2B). Dead entities remain dead until resurrection mechanics implemented.

### 6.2 HP Max Drops Below Current HP

**Rule:** Current HP is clamped to new HP max. Emit `hp_changed` event.

**Example:**
- Fighter at 45/45 HP
- CON drain reduces HP max to 35
- Current HP becomes 35/35 (not 45/35)

**No Overflow Death:** If HP clamping brings current HP to exactly 0, entity dies via normal HP death rules (not ability score death).

### 6.3 Restoration Exceeding Drain

**Rule:** Restoration cannot remove more drain than exists. Excess restoration is wasted (no error).

**Example:**
- Entity has -2 STR drain
- Lesser Restoration attempts to remove 4 STR drain
- Result: -2 drain removed, effective STR restored to base, +2 excess wasted

**Rationale:** Prevents accidental bonuses. Restoration only reverses penalties.

### 6.4 Multiple Drain Sources

**Rule:** All drain stacks. No source tracking required (total drain is sum).

**Example:**
- Shadow drains -2 STR
- Another Shadow drains -3 STR
- Total drain: -5 STR

**Restoration removes total drain**, not per-source. No need to track "which Shadow caused which drain."

### 6.5 Inherent Bonuses from Multiple Sources

**Rule:** Inherent bonuses stack (unlike most typed bonuses).

**Example:**
- Wish grants +1 STR
- Later, another Wish grants +1 STR
- Total inherent bonus: +2 STR

**Rationale:** RAW allows multiple Wish stat increases (up to +5 total). Stacking is intentional.

### 6.6 Feeblemind Special Case

**Feeblemind (PHB 229):** Target's INT and CHA drop to 1 (not 0).

**Implementation:**
- Calculate drain amount: `drain = current_effective_score - 1`
- Apply as permanent drain
- Restoration removes drain, restoring original INT/CHA

**Example:**
- Wizard with INT 18
- Feeblemind applied: drain = 18 - 1 = -17
- Effective INT becomes 1
- Restoration removes -17 drain, INT returns to 18

**Why Not Store "Feeblemind Active" Condition?**
- Storing drain amount is more general (supports partial restoration, multiple Feeblemind effects, etc.)
- Condition-based approach would require special-case logic

---

## 7. Failure Modes

### 7.1 Non-Deterministic Recalculation Order

**Failure:** If derived stats recalculate in non-deterministic order (e.g., dict iteration order varies), replay produces different results.

**Mitigation:** Fixed, documented recalculation order (see §5.2).

### 7.2 Permanent and Temporary Modifiers Confused

**Failure:** If temporary modifiers (CP-16) leak into permanent layer, restoration may remove temporary buffs or drain may expire.

**Mitigation:** Strict separation (INV-3). Two distinct storage locations. No shared fields.

### 7.3 HP Max Recalculation Skipped

**Failure:** CON changes, but HP max not recalculated → entity has incorrect HP max → healing/damage resolution wrong.

**Mitigation:** Derived stats recalculate atomically after every ability score change (INV-5).

### 7.4 Ability Score Death Not Detected

**Failure:** Ability score reaches 0, but entity doesn't die → broken game state.

**Mitigation:** Explicit check in Phase 3 of recalculation (§5.2). `ability_score_death` event mandatory.

### 7.5 Restoration Grants Unintended Bonuses

**Failure:** Restoration removes more drain than exists, granting net bonus above base.

**Mitigation:** Edge constraint §6.3. Restoration capped at removing total drain.

### 7.6 Event Ordering Non-Deterministic

**Failure:** Events emitted in variable order → replay divergence.

**Mitigation:** Fixed event ordering (INV-10). Source event → derived stats → HP clamp → death.

### 7.7 Hidden RNG Consumption

**Failure:** If recalculation secretly consumes RNG (e.g., tie-breaking), replay breaks.

**Mitigation:** No RNG allowed in SKR-002 (INV-12). All calculations purely functional.

### 7.8 Cross-Entity Dependencies

**Failure:** If derived stat recalculation depends on other entities' state (e.g., "my AC depends on ally's buff"), non-determinism risk.

**Mitigation:** Entity state is self-contained (INV-13). No cross-entity queries during recalculation.

---

## 8. Open Questions (RESOLVED)

### 8.1 Interaction with CP-16 Temporary Modifiers

**Question:** If entity has temporary STR +4 (Bull's Strength) and permanent STR drain -2, what is effective STR?

**RULING (APPROVED):** `effective_STR = base + permanent_drain + permanent_inherent + temporary_sum`
Example: Base 14 + (-2 drain) + (+4 temp) = 16

---

### 8.2 Ability Score Increase from Leveling

**Question:** When a character levels and gains +1 to an ability score (every 4 levels per RAW), is this a base stat change or a permanent modifier?

**RULING (APPROVED):** This is a **base stat change** (one-time mutation at level-up), not a permanent modifier. SKR-002 does not handle leveling.

---

### 8.3 Polymorph and Ability Score Replacement

**Question:** Polymorph replaces physical stats (STR/DEX/CON) with new form's stats. How does this interact with permanent modifiers?

**RULING (OUT OF SCOPE):** Deferred to G-T3D/SKR-010. Polymorph requires transformation history stack. SKR-002 assumes no form changes. Strict separation is safe.

---

### 8.4 Death and Undead Immunity

**Question:** Undead are immune to ability score damage (not drain). Does this mean undead are immune to temporary ability penalties (CP-16) or permanent drain (SKR-002)?

**RULING (NOT ENFORCED IN SKR-002):** RAW: "Ability damage" = temporary (heals naturally). "Ability drain" = permanent (requires Restoration). Undead immune to damage, NOT drain. Immunity enforcement belongs to attack/effect resolution, not stat kernel. Correct separation maintained.

---

### 8.5 Negative Levels vs Ability Drain

**Question:** Negative levels (from energy drain) also reduce effective stats. How do negative levels interact with SKR-002?

**RULING (OUT OF SCOPE):** Deferred to SKR-011. Negative levels are a separate mechanic (not ability score drain). SKR-002 does not model negative levels. Strict separation is safe.

---

### 8.6 Partial Restoration

**Question:** Can Restoration remove partial drain (e.g., remove 1 point of drain when entity has -4 total)?

**RULING (APPROVED):** **Yes.** Lesser Restoration removes 1 point, Restoration removes all, Greater Restoration removes all (per RAW). Event payload specifies `amount_removed`.

---

### 8.7 Wish-Based Stat Increases Cap

**Question:** RAW: Wish can grant +1 inherent bonus to one ability score, maximum +5 total from all sources. How is the +5 cap enforced?

**RULING (NOT ENFORCED IN SKR-002):** Cap enforcement is spell implementation detail (CP-18A or later). SKR-002 only stores inherent bonuses, doesn't validate source rules. Correct delegation to higher-level validation.

---

### 8.8 Save DC Recalculation

**Question:** If a spellcaster's INT/WIS/CHA changes (permanent or temporary), do spell save DCs recalculate?

**RULING (APPROVED):** **Yes.** Save DCs are derived stats: `DC = 10 + spell_level + ability_modifier`. Recalculated immediately in Phase 2 (§5.2).

---

## 9. Integration Points

### 9.1 Dependencies (What SKR-002 Requires)

1. **CP-16 (Condition Modifiers):** Must remain separate from permanent modifiers. No overlap in storage.
2. **Event Sourcing (Core System):** All mutations via events. Replay infrastructure already exists.
3. **Entity State Schema:** Must support new `permanent_stat_modifiers` field.
4. **HP System:** Must support HP max recalculation and current HP clamping.

### 9.2 Dependents (What Will Use SKR-002)

1. **Monster Abilities:** Shadow STR drain, Vampire CON drain, Wraith CON drain, Spectre STR drain.
2. **Spells (Future):** Feeblemind, Restoration (Lesser/Standard/Greater), Wish (stat increase).
3. **Magic Items (Future):** Tomes/Manuals (+1 to +5 inherent bonuses).
4. **Combat Resolution:** Attack/damage bonuses recalculate when STR/DEX change.
5. **Skill System:** Skill modifiers recalculate when governing ability changes.

---

## 10. Test Strategy

### 10.1 Unit Tests

**Category 1: Permanent Modifier Application**
- Apply drain, verify effective score reduced
- Apply inherent bonus, verify effective score increased
- Apply multiple drains, verify stacking
- Apply drain + inherent, verify both apply

**Category 2: Restoration**
- Restore full drain, verify effective score returns to base
- Restore partial drain, verify partial removal
- Restore when no drain exists, verify no change
- Restore exceeding drain, verify capped at total drain

**Category 3: Derived Stat Recalculation**
- CON drain → HP max reduces
- STR drain → attack/damage bonuses reduce
- DEX drain → AC reduces
- INT drain → skill modifiers reduce
- Verify recalculation order deterministic

**Category 4: Edge Cases**
- Ability score to 0 → death
- HP max drops below current HP → HP clamped
- Multiple sources drain same ability → stacks
- Feeblemind (INT/CHA → 1) → drain calculation correct

**Category 5: Separation from Temporary Modifiers**
- Apply temporary STR buff (CP-16) + permanent STR drain (SKR-002)
- Verify both apply independently
- Remove temporary buff, verify drain persists
- Restore drain, verify temporary buff persists

### 10.2 Integration Tests

**Scenario 1: Shadow Encounter**
- Shadow attacks fighter (STR 16)
- Touch attack hits, drain 2 STR
- Fighter's attack bonus reduces
- Later, cleric casts Lesser Restoration
- Fighter's STR and attack bonus restore

**Scenario 2: Vampire CON Drain with HP Loss**
- Vampire drains 4 CON from fighter (CON 14, HP 45/45)
- HP max drops to 35, current HP clamped to 35
- Later, Restoration cast
- HP max returns to 45, current HP stays 35 (no free healing)

**Scenario 3: Ability Score Death**
- Spectre drains STR from wizard (STR 8)
- First hit: -3 STR (effective 5, survives)
- Second hit: -5 STR (effective 0, death)
- Verify `ability_score_death` event emitted

**Scenario 4: Wish Stat Increase**
- Wizard casts Wish (+1 INT)
- Verify inherent bonus applied
- Spell save DCs increase
- Later, INT drain applied
- Verify drain reduces effective INT, inherent bonus persists

### 10.3 Replay Tests (Determinism)

**Test:** Run 10× replay of each integration scenario
- Verify identical event logs
- Verify identical final ability scores
- Verify identical HP, AC, saves

**Test:** Replay with different RNG seeds
- SKR-002 should NOT consume RNG
- Verify no divergence

### 10.4 Performance Tests

**Test:** Apply 100 drain effects in sequence
- Verify test runtime < 0.1s
- Verify no performance regression

**Test:** Recalculate derived stats 1000 times
- Verify deterministic order maintained
- Verify no memory leaks

---

## 11. Summary

SKR-002 introduces a **permanent stat modification layer** separate from temporary modifiers (CP-16). Key design decisions:

1. **Two modifier types:** `drain` (penalties, reversible) and `inherent` (bonuses, permanent).
2. **Base stats immutable:** All changes via modifier layers.
3. **Deterministic recalculation:** Fixed order, atomic operation, no RNG.
4. **Event sourcing maintained:** All mutations emit events.
5. **Replay stable:** Identical events → identical state.

**Blocking gate G-T2A opens when:**
- This design document approved ✅
- Schema implementation complete (Phase 2)
- Algorithm implementation complete (Phase 3)
- All tests pass
- PBHA passed (10× deterministic replay)
- Kernel marked FROZEN

**Next step:** Phase 2 — Schema Implementation

---

## 12. Approval Record

**Design Review Date:** 2026-02-08
**Approval Status:** ✅ APPROVED
**Approval Confidence:** 0.96

**Key Caveats:**
1. Do not add immunity logic (e.g., undead) into SKR-002 — enforce at effect resolution
2. Freeze `derived_stats_recalculated` payload ordering to preserve replay hashes
3. Any future polymorph or negative-level work must not retroactively alter SKR-002 semantics

**Approved By:** Project Manager (AP-SKR002-01)
**Design Document ID:** SKR-002-DESIGN-v1.0
**Status:** DESIGN FROZEN — Ready for Phase 2 (Schema Implementation)

---

**END OF SKR-002 DESIGN DOCUMENT**
