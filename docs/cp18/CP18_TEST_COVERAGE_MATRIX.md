# CP-18 Test Coverage Matrix
**Date:** 2026-02-08
**Scope:** CP-18 Combat Maneuvers (Bull Rush, Trip, Overrun, Sunder, Disarm, Grapple-lite)
**Authority:** Derived from CP18_COMBAT_MANEUVERS_DECISIONS.md + CP18_IMPLEMENTATION_PACKET.md + Determinism Threat Model

---

## 1) Coverage Goals (What this matrix is for)

This matrix is intended to:
- Drive *tiered* test creation (Tier-1 unit vs Tier-2 integration vs PBHA determinism).
- Ensure every maneuver is covered for:
  - legality checks
  - AoO provocation + abort behavior
  - RNG consumption order invariants
  - deterministic event ordering + event-count stability
  - gate safety degradations (no persistent item state, no relational grapple state)

---

## 2) Maneuver → Rules/Subsystem Touchpoints

| Maneuver | Implementation Level | Provokes AoO | Special Rolls | Conditions Applied | Position Change | Counter-mechanic | Degradation / Gate Constraint |
|---|---|---:|---|---|---|---|---|
| Bull Rush | Full | Yes (threatening) | Opposed STR vs STR | None (optional narrative) | Yes (push/backstep) | None | Must not require CP-19 terrain (no "choose among multiple paths") |
| Trip | Full | Yes (target only) | Touch attack + opposed trip check | Prone on success | None | Counter-trip on failure | Event-count stability across success/failure/counter |
| Overrun | Full (degraded avoidance) | Yes (target only) | Opposed check | Prone on success | Yes (move-through) | None | Defender avoidance is doctrine input (boolean) |
| Sunder | Degraded (narrative only) | Yes (target only) | Attack roll contest + damage roll on success | None | None | None | No persistent item HP/state; "damage" is event-only |
| Disarm | Degraded | Yes (target only) | Attack roll contest | None | None | Counter-disarm on failure | No weapon ownership transfer/persistence |
| Grapple-lite | Degraded | Yes (target only) | Touch attack + opposed grapple check | Grappled (defender only) | None | None | **Unidirectional** only; no attacker state |

---

## 3) Determinism: Per-maneuver RNG Consumption Contract

All maneuvers use RNG stream: **"combat"** only.

> **Test requirement:** For each maneuver, assert that the number and order of RNG draws is invariant across branches (success/failure, counter-attack present/absent).
> This is validated indirectly via event sequence + PBHA replay hashes.

| Maneuver | RNG Draw Order (must match) |
|---|---|
| Bull Rush | 1) AoO attack rolls; 2) AoO damage rolls; 3) attacker STR d20; 4) defender STR d20 |
| Trip | 1) AoO attack rolls; 2) AoO damage rolls; 3) touch attack d20; 4) attacker trip d20; 5) defender trip d20; 6) defender counter-trip d20 (if triggered); 7) attacker counter-trip defense d20 (if triggered) |
| Overrun | 1) AoO attack rolls; 2) AoO damage rolls; 3) attacker overrun d20; 4) defender overrun d20 |
| Sunder | 1) AoO attack rolls; 2) AoO damage rolls; 3) attacker attack d20; 4) defender attack d20; 5) damage roll (weapon dice) if success |
| Disarm | 1) AoO attack rolls; 2) AoO damage rolls; 3) attacker attack d20; 4) defender attack d20; 5) defender counter-disarm d20 (if triggered); 6) attacker counter-disarm defense d20 (if triggered) |
| Grapple | 1) AoO attack rolls; 2) AoO damage rolls; 3) touch attack d20; 4) attacker grapple d20; 5) defender grapple d20 |

---

## 4) Determinism: Event Ordering Contract (All Maneuvers)

Each maneuver must emit events in deterministic order:

1. `{maneuver}_declared`
2. `aoo_triggered` (CP-15 ordering)
3. `attack_roll`, `damage_applied` (AoO resolution)
4. If AoO defeats attacker: `action_aborted`, END
5. `touch_attack_roll` (if applicable)
6. `opposed_check`
7. `{maneuver}_success` OR `{maneuver}_failure`
8. `condition_applied` (if applicable)
9. Counter-attack events (if applicable)

**Test requirement:** Compare exact `event_type` sequence in unit tests.

---

## 5) Tier-1 Tests (Unit) — Required Set

| Maneuver | Tier-1 Tests (minimum) | What they validate |
|---|---|---|
| Bull Rush | `test_bull_rush_success_moves_target` | Position change emitted + applied |
|  | `test_bull_rush_failure_pushes_attacker_back` | Failure displacement behavior |
|  | `test_bull_rush_provokes_aoo_and_aborts_on_attacker_defeat` | AoO abort path |
| Trip | `test_trip_success_applies_prone` | Condition applied |
|  | `test_trip_failure_triggers_counter_trip_event_sequence` | Counter-trip events + event-count stability |
|  | `test_trip_provokes_aoo_and_aborts_on_attacker_defeat` | AoO abort path |
| Overrun | `test_overrun_success_applies_prone` | Condition applied |
|  | `test_overrun_defender_avoids_skips_resolution_but_preserves_event_count` | Avoidance branch stability |
|  | `test_overrun_provokes_aoo_and_aborts_on_attacker_defeat` | AoO abort path |
| Sunder | `test_sunder_success_emits_damage_event_no_item_state_change` | Event-only item "damage" |
|  | `test_sunder_failure_emits_failure_event` | Failure path |
| Disarm | `test_disarm_success_emits_weapon_drop_event_no_persistence` | Drop event, no state |
|  | `test_disarm_failure_triggers_counter_disarm_event_sequence` | Counter-disarm branch stability |
| Grapple-lite | `test_grapple_success_applies_grappled_to_defender_only` | Gate safety (unidirectional) |
|  | `test_grapple_aoo_damage_causes_auto_failure` | Packet-specific rule: AoO damage auto-failure |

---

## 6) Tier-2 Tests (Integration) — Required Set

These are explicitly called out in design/packet:

- `test_trip_vs_mounted_uses_ride`
- `test_charge_bull_rush_bonus`
- `test_stability_bonus_applied`

Add at least one AoO integration test that validates CP-15 ordering with maneuver triggers.

---

## 7) PBHA Determinism Test

- `test_pbha_maneuvers_10x_replay`

**Assertions:**
- All 10 runs produce identical state hash.
- (Optional) also assert identical emitted event sequences.

---

## 8) Gate Safety Tests

| Gate Pressure | Required Tests |
|---|---|
| G-T3C (Relational Conditions) | `test_grapple_unidirectional_no_attacker_condition` |
| Item state kernel absent | `test_sunder_does_not_mutate_item_state` / `test_disarm_does_not_transfer_ownership` |
| No new fields beyond allowed | Static check in schema test OR unit test that entity dict remains unchanged except allowed fields |

---

## 9) "STOP" Conditions (Test Suite Signals)

If any of these happens, treat as blocking:
- Branch-dependent RNG consumption inferred by divergent replay hashes.
- Event sequences differ between seeds or between runs with same seed.
- Set/dict iteration causes nondeterministic ordering in emitted events.

---

**STATUS: ✅ ALL TESTS IMPLEMENTED AND PASSING** (2026-02-08)
