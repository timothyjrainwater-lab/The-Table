# WO-ENGINE-AID-ANOTHER-001 — Aid Another (PHB p.154)

**Issued:** 2026-02-24
**Authority:** PM
**Gate:** ENGINE-AID-ANOTHER (new gate, defined below)

---

## 1. Target Lock

PHB p.154: A character can take a standard action to help an ally in combat. The helper makes an attack roll against AC 10. If successful, the ally gets a +2 circumstance bonus to their next attack roll or AC until the start of the helper's next turn.

Mechanically:
- **Aid Another** is a standard action
- Helper makes an attack roll against **AC 10** (not the target's actual AC)
- Success: ally gains **+2 circumstance bonus** to either:
  - Their **next attack roll** against a specific enemy, OR
  - Their **AC** against a specific enemy's next attack
- Bonus is a **circumstance bonus** — does not stack with other circumstance bonuses
- Bonus lasts until **start of helper's next turn** (or until consumed by one attack/defense)
- Helper must be adjacent to the ally being aided (melee range, ≤5 ft)
- Helper must be adjacent to the enemy (for attack aid) OR the enemy must threaten the ally (for AC aid)

**Done means:** `AidAnotherIntent` + `AidAnotherBonus` applied to `WorldState.active_combat` + evaluation in `execute_turn()` + `aid_another_success` / `aid_another_fail` / `aid_another_bonus_consumed` events + Gate ENGINE-AID-ANOTHER 10/10.

---

## 2. PHB Rule (p.154)

> "In melee combat, you can help a friend attack or defend by distracting or interfering with an opponent. If you're in position to make a melee attack on an opponent that is threatening your ally, you can attempt to aid your ally with the Aid Another action. Make an attack roll against AC 10. If you succeed, your ally gets a +2 bonus on his or her next attack roll against that opponent, or a +2 bonus to AC against that opponent's next attack, your choice. Multiple characters can aid the same friend, and effects stack."

Key rulings:
- The attack roll is against **AC 10** exactly — miss if below 10, succeed if 10 or above (note: PHB says "if you succeed" implying 10 is success threshold, i.e., roll + mods ≥ 10)
- "Next attack roll" and "next attack on AC" — the bonus is consumed on the first application
- "Multiple characters can aid the same friend, and effects stack" — circumstance bonuses from multiple Aid Another actions DO stack (exception to normal circumstance rule)
- PHB p.154 says "if you're in position to make a melee attack on an opponent that is threatening your ally" — melee range to the enemy is required for attack aid; melee range to ally is required for AC aid (standard interpretation; WO defers to simpler adjacent-to-target rule for this scope)

**Scope for this WO:**
- Aid attack: helper adjacent to enemy, ally adjacent to same enemy — grants +2 to ally's next attack vs that enemy
- Aid defense: helper adjacent to ally being aided — grants +2 AC to ally vs next attack from a specified enemy
- Multiple aids stack (circumstance bonuses from Aid Another are explicit PHB exception)
- Adjacent = ≤5 ft distance (standard grid assumption)

---

## 3. New Entity Fields

None. Aid Another bonuses are stored in `WorldState.active_combat["aid_another_bonuses"]`, not on entities. Bonuses are ephemeral (expire or get consumed within same round).

---

## 4. Implementation Spec

### 4.1 New Intent: `AidAnotherIntent` (intents.py)

```python
@dataclass
class AidAnotherIntent:
    """Intent to aid an ally with the Aid Another action.

    PHB p.154: Standard action. Helper makes attack roll vs AC 10.
    Success grants ally +2 circumstance bonus to attack or AC.

    WO-ENGINE-AID-ANOTHER-001
    """

    actor_id: str
    """Entity ID of the helper making the aid action."""

    ally_id: str
    """Entity ID of the ally being aided."""

    enemy_id: str
    """Entity ID of the enemy relevant to the aid (attack target or attacker)."""

    aid_type: Literal["attack", "ac"]
    """
    'attack' — aids ally's next attack roll vs enemy_id (+2 to hit)
    'ac'     — aids ally's AC vs enemy_id's next attack (+2 AC)
    """

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data) -> "AidAnotherIntent": ...
```

Add to Intent union and `parse_intent()` dispatcher.

### 4.2 `AidAnotherBonus` in `active_combat`

Add to `active_combat` dict:

```python
# active_combat["aid_another_bonuses"] = list of dicts:
{
    "beneficiary_id": str,      # ally who receives the bonus
    "enemy_id": str,            # which enemy this applies to
    "aid_type": str,            # "attack" | "ac"
    "bonus": int,               # always +2 per PHB p.154
    "registered_at_event_id": int,
    "expires_at_actor_id": str, # helper's actor_id — expires at their next turn
}
```

Multiple entries may exist (one per successful Aid Another). When applying to an attack roll or AC check, all matching entries for `(beneficiary_id, enemy_id, aid_type)` are summed (PHB stacking exception) and removed.

### 4.3 `aid_another_resolver.py` (new file)

```python
# aidm/core/aid_another_resolver.py

def resolve_aid_another(
    world_state: WorldState,
    intent: AidAnotherIntent,
    rng: RNGProvider,
    current_event_id: int,
) -> Tuple[WorldState, List[dict], int]:
    """Resolve Aid Another action.

    Steps:
    1. Validate actor and ally are not the same entity
    2. Make attack roll vs AC 10 (d20 + actor's base attack bonus)
       - Use actor's melee attack bonus (BAB + Str mod + size mod)
       - Note: this is NOT an actual attack, no miss consequences
    3. If roll >= 10: success — add bonus entry to active_combat
    4. Emit aid_another_success or aid_another_fail event
    """

def consume_aid_another_bonus(
    world_state: WorldState,
    beneficiary_id: str,
    enemy_id: str,
    aid_type: str,  # "attack" | "ac"
) -> Tuple[WorldState, int]:
    """Consume all matching Aid Another bonuses for beneficiary vs enemy.

    Returns (updated_world_state, total_bonus_consumed).
    Removes matched entries from active_combat["aid_another_bonuses"].
    Called from attack_resolver.py when rolling attack (consume attack bonus)
    and from attack_resolver.py when applying AC (consume ac bonus).
    """

def expire_aid_another_bonuses(
    world_state: WorldState,
    actor_id: str,
) -> Tuple[WorldState, List[dict]]:
    """Expire Aid Another bonuses granted by actor_id at their turn start.

    Called at turn start — removes any unconsumed bonuses where
    expires_at_actor_id == actor_id and emits aid_another_bonus_expired events.
    """
```

### 4.4 `execute_turn()` wiring (play_loop.py)

Three insertion points:

**A. At turn start (expire unconsumed bonuses from prior round):**
```python
# Expire unconsumed Aid Another bonuses from this actor's prior turn
world_state, expire_events = expire_aid_another_bonuses(
    world_state, turn_ctx.actor_id
)
events.extend(expire_events)
```

**B. When `AidAnotherIntent` is routed:**
```python
elif isinstance(combat_intent, AidAnotherIntent):
    world_state, aid_events, current_event_id = resolve_aid_another(
        world_state, combat_intent, rng, current_event_id
    )
    events.extend(aid_events)
```

**C. Attack roll consumption** (in `attack_resolver.py`):

When computing total attack roll bonus:
```python
# Consume Aid Another attack bonus (PHB p.154)
world_state, aid_bonus = consume_aid_another_bonus(
    world_state,
    beneficiary_id=intent.attacker_id,
    enemy_id=intent.target_id,
    aid_type="attack",
)
# Add aid_bonus to total attack roll modifier
```

When computing AC:
```python
# Consume Aid Another AC bonus (PHB p.154)
world_state, aid_ac_bonus = consume_aid_another_bonus(
    world_state,
    beneficiary_id=intent.target_id,  # defender
    enemy_id=intent.attacker_id,       # who is attacking
    aid_type="ac",
)
# Add aid_ac_bonus to target AC for this attack
```

**Note on attack_resolver.py integration:** The bonus must affect the attack roll computation AND be reflected in the `attack_roll` event payload. Add `aid_attack_bonus` and `aid_ac_bonus` fields to the attack event payload (both default 0 when absent, always present when Aid Another is active in the scenario).

### 4.5 Action Economy

Add to `_build_action_types()` in `action_economy.py`:
```python
_try_add(mapping, "aidm.schemas.intents", "AidAnotherIntent", "standard")
```

### 4.6 New Event Types

| Event | When | Key Payload Fields |
|-------|------|--------------------|
| `aid_another_success` | Helper's roll ≥ 10 | actor_id, ally_id, enemy_id, aid_type, roll, bonus (+2) |
| `aid_another_fail` | Helper's roll < 10 | actor_id, ally_id, enemy_id, aid_type, roll |
| `aid_another_bonus_consumed` | Bonus applied to attack/AC | beneficiary_id, enemy_id, aid_type, bonus_applied |
| `aid_another_bonus_expired` | Helper's next turn, unused bonus | actor_id (helper), beneficiary_id, aid_type |

---

## 5. Regression Risk

- **LOW for new code path:** `AidAnotherIntent` only activates when that intent is emitted. No existing tests use it.
- **MEDIUM for attack_resolver.py changes:** `consume_aid_another_bonus()` must be a no-op when `active_combat["aid_another_bonuses"]` is empty or absent. Guard: check list is non-empty before summing.
- **LOW for turn-start expiry:** Guard empty list — only emit `aid_another_bonus_expired` when there is actually an entry to expire.
- **Gold masters:** Attack resolver change is guarded by empty-list check; existing scenarios have no Aid Another bonuses registered, so no events added and no drift.

---

## 6. What This WO Does NOT Do

- No aid for skill checks (Aid Another for skills is out-of-combat — deferred)
- No aid for saving throws (not a PHB Aid Another use — deferred)
- No range validation beyond "in position" (melee vs ranged) — positional adjacency is deferred (grid positions may not be tracked for all scenarios; guard is "active_combat present")
- No adjacency enforcement in the resolver — if the intent is submitted, it is assumed valid (DM narrated validity; flag in future WO)
- No aid for spell attack rolls (deferred)
- No Aid Another from flanking position automatic granting (separate feature — flanking is already handled independently)

---

## 7. Gate Spec

**Gate name:** `ENGINE-AID-ANOTHER`
**Test file:** `tests/test_engine_gate_aid_another.py` (new file)

| # | Test | Check |
|---|------|-------|
| AA-01 | AidAnotherIntent registers — success path (roll ≥ 10) | `aid_another_success` event emitted; bonus in active_combat |
| AA-02 | AidAnotherIntent registers — fail path (roll < 10) | `aid_another_fail` event emitted; no bonus in active_combat |
| AA-03 | Aid attack bonus consumed when ally attacks that enemy | `aid_another_bonus_consumed` in events; attack roll shows +2 |
| AA-04 | Aid AC bonus consumed when that enemy attacks ally | `aid_another_bonus_consumed` in events; effective AC shows +2 |
| AA-05 | Multiple Aid Another bonuses stack — two helpers, same ally | Two success events; ally attack roll gets +4 total |
| AA-06 | Bonus is NOT consumed on ally's attack vs a different enemy | Bonus remains in queue after attack on unrelated enemy |
| AA-07 | Unconsumed bonus expires at helper's next turn start | `aid_another_bonus_expired` emitted; queue cleared |
| AA-08 | AidAnotherIntent costs standard action slot | Action budget: `standard` used; second standard → ACTION_DENIED |
| AA-09 | Attack bonus does not apply to AC and vice versa | Type mismatch: aid_type=attack does not boost AC; aid_type=ac does not boost hit |
| AA-10 | Zero regressions suite-wide | Full suite: no new failures |

**Test count target:** ENGINE-AID-ANOTHER 10/10.

---

## 8. Preflight

```bash
cd f:/DnD-3.5

# Confirm baseline
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5

# After implementation
python -m pytest tests/test_engine_gate_aid_another.py -v
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5
```
