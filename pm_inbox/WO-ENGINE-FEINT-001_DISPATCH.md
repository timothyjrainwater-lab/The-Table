# WO-ENGINE-FEINT-001 — Feint (PHB p.68, 76)

**Issued:** 2026-02-24
**Authority:** PM
**Gate:** ENGINE-FEINT (new gate, defined below)

---

## 1. Target Lock

PHB p.68 / p.76: A character with ranks in Bluff can use the Feint action in combat to deny the target their Dexterity bonus to AC for the next attack.

Mechanically:
- **Feint** is a **standard action**
- Actor makes a **Bluff check** (DC = target's Sense Motive check result, minimum DC 10)
- Success: target is **denied Dex to AC** against the **next attack** from the feinting character
- The denied-Dex state is consumed by the first attack and does not persist beyond it
- Target is immune to feint if they cannot be caught flat-footed (Uncanny Dodge class feature — deferred)
- Improved Feint feat (PHB p.96): can feint as a move action instead of standard action (deferred for this WO scope)

**Done means:** `FeintIntent` + Bluff vs Sense Motive resolution + `feint_success` / `feint_fail` events + `feint_flat_footed` marker in `active_combat` + consumed on next attack from feinting actor + `feint_bonus_consumed` event + Gate ENGINE-FEINT 10/10.

---

## 2. PHB Rule (p.68, 76)

> **Feint (Standard Action):** You can use Bluff to make your opponent think you are attacking in one way when you are really attacking in another. As a standard action, make a Bluff check opposed by your opponent's Sense Motive check. If you succeed, you can denote the opponent as flat-footed for the next melee attack against them. This feint does not work against creatures that cannot be caught flat-footed.

From PHB p.76 (Bluff skill):
> **Feinting in Combat:** You can also use Bluff to mislead an opponent in melee combat (so that he can't dodge your next attack effectively). To feint, make a Bluff check opposed by your target's Sense Motive check, but in this case, the target may add his base attack bonus to the roll. If your Bluff check result exceeds this defender's check result, the next melee attack you make against the target does not allow him to use his Dexterity bonus to AC (if any). This attack must be made on or before your next turn.

Key rulings:
- Feint check: **Bluff vs (Sense Motive + BAB)** — the target's BAB is added to Sense Motive
- Success: denied Dex on **next melee attack** from the feinting actor, made on **or before** the feinting actor's next turn
- Feint only works in **melee** — ranged feints don't apply (PHB Bluff skill notes)
- Improved Feint feat: feint as **move action** — scope is deferred for this WO
- Uncanny Dodge immunity: if target has Uncanny Dodge, they cannot be caught flat-footed — deferred (add immunity check field in future WO)

**Scope for this WO:**
- `FeintIntent` as standard action (Bluff check vs Sense Motive + BAB)
- Success stores `(feinting_actor_id, target_id)` pair in `active_combat["feint_flat_footed"]`
- `attack_resolver.py` reads the feint marker when the feinting actor attacks the feinted target — applies flat-footed (denied Dex) and removes marker
- Marker expires at feinting actor's next turn start (PHB: "on or before your next turn")
- Bluff rank requirement: actor must have at least 1 rank in `skill_ranks["bluff"]` — otherwise `feint_invalid` (no Bluff skill)
- Sense Motive for target: `skill_ranks.get("sense_motive", 0) + BAB + WIS_mod` — use target's base values

---

## 3. New Entity Fields

None. Feint state stored in `WorldState.active_combat["feint_flat_footed"]` as a list of dicts:

```python
# active_combat["feint_flat_footed"] = list of dicts:
{
    "feinting_actor_id": str,   # who performed the feint
    "target_id": str,           # who is denied Dex
    "registered_at_event_id": int,
    "expires_at_actor_id": str, # feinting_actor_id — expires at their next turn start
}
```

---

## 4. Implementation Spec

### 4.1 New Intent: `FeintIntent` (intents.py)

```python
@dataclass
class FeintIntent:
    """Intent to feint in melee combat.

    PHB p.68/76: Standard action. Bluff check vs (Sense Motive + BAB).
    Success: target denied Dex to AC against feinting actor's next melee attack.

    WO-ENGINE-FEINT-001
    """
    actor_id: str
    """Entity ID of the feinting character."""

    target_id: str
    """Entity ID of the feint target."""

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data) -> "FeintIntent": ...
```

Add to Intent union and `parse_intent()` dispatcher.

### 4.2 `feint_resolver.py` (new file)

```python
# aidm/core/feint_resolver.py

def resolve_feint(
    world_state: WorldState,
    intent: FeintIntent,
    rng: RNGProvider,
    current_event_id: int,
) -> Tuple[WorldState, List[dict], int]:
    """Resolve a Feint action.

    PHB p.76: Roll Bluff vs (target Sense Motive + target BAB).
    Both rolls use d20.

    Steps:
    1. Validate actor has Bluff ranks (>= 1) — emit feint_invalid if absent
    2. Compute actor Bluff total: d20 + skill_ranks["bluff"] + INT_mod
       (Bluff uses CHA, not INT — use CHA_mod for the modifier)
       Actor Bluff = d20 + skill_ranks.get("bluff", 0) + CHA_mod
    3. Compute target Sense Motive total: d20 + skill_ranks.get("sense_motive", 0) + WIS_mod + BAB
    4. If actor Bluff > target Sense Motive total: success
       - Add entry to active_combat["feint_flat_footed"]
       - Emit feint_success event
    5. If actor Bluff <= target Sense Motive total: fail
       - Emit feint_fail event
    """

def consume_feint_marker(
    world_state: WorldState,
    attacker_id: str,
    target_id: str,
) -> Tuple[WorldState, bool]:
    """Check if attacker has a feint marker on target; consume if present.

    Returns (updated_world_state, feint_active).
    Called from attack_resolver.py before AC calculation.
    Removes the matching entry on consumption.
    """

def expire_feint_markers(
    world_state: WorldState,
    actor_id: str,
    current_event_id: int,
) -> Tuple[WorldState, List[dict], int]:
    """Expire feint markers set by actor_id at their turn start.

    Called at turn start — removes entries where expires_at_actor_id == actor_id.
    Emits feint_expired for each removed entry.
    """
```

### 4.3 Stat Computation Detail

**Actor Bluff check:** `d20 + skill_ranks.get("bluff", 0) + CHA_modifier`
- CHA modifier: `(entity.get(EF.CHA, 10) - 10) // 2`

**Target Sense Motive + BAB check:** `d20 + skill_ranks.get("sense_motive", 0) + WIS_modifier + entity.get(EF.BAB, 0)`
- WIS modifier: `(entity.get(EF.WIS, 10) - 10) // 2`
- BAB: `entity.get(EF.BAB, 0)` — use raw BAB field

**Success condition:** Actor Bluff **strictly greater than** target result (ties go to defender — PHB "exceeds this defender's check result")

### 4.4 `play_loop.py` Wiring

**A. Turn start — expire feint markers:**
```python
world_state, feint_expire_events, current_event_id = expire_feint_markers(
    world_state, turn_ctx.actor_id, current_event_id
)
events.extend(feint_expire_events)
```

**B. FeintIntent routing:**
```python
elif isinstance(combat_intent, FeintIntent):
    world_state, feint_events, current_event_id = resolve_feint(
        world_state, combat_intent, rng, current_event_id
    )
    events.extend(feint_events)
```

### 4.5 `attack_resolver.py` Integration

When computing target's effective AC and denied-Dex status, check feint markers:

```python
# WO-ENGINE-FEINT-001: Check feint flat-footed
world_state, feint_active = consume_feint_marker(
    world_state,
    attacker_id=intent.attacker_id,
    target_id=intent.target_id,
)
if feint_active:
    # Target is denied Dex to AC (same path as other denied-Dex cases)
    target_denied_dex = True
    # Emit feint_bonus_consumed event
    events.append(...)
```

Add `feint_flat_footed: bool` to attack event payload (False when not applicable).

### 4.6 Action Economy

Add to `_build_action_types()` in `action_economy.py`:
```python
_try_add(mapping, "aidm.schemas.intents", "FeintIntent", "standard")
```

### 4.7 New Event Types

| Event | When | Key Payload Fields |
|-------|------|--------------------|
| `feint_success` | Bluff > Sense Motive+BAB | actor_id, target_id, bluff_roll, sense_motive_roll |
| `feint_fail` | Bluff ≤ Sense Motive+BAB | actor_id, target_id, bluff_roll, sense_motive_roll |
| `feint_invalid` | Actor has 0 Bluff ranks | actor_id, target_id, reason |
| `feint_bonus_consumed` | Feint marker applied to attack | attacker_id, target_id |
| `feint_expired` | Feinting actor's next turn start, unused | actor_id, target_id |

---

## 5. Regression Risk

- **LOW for new code path:** `FeintIntent` only activates when that intent is emitted. No existing tests use it.
- **LOW for attack_resolver.py:** `consume_feint_marker()` is a no-op when `active_combat["feint_flat_footed"]` is absent or empty. Guard empty list before iterating.
- **LOW for turn-start expiry:** Only emit `feint_expired` when there's actually an entry to expire.
- **Gold masters:** The `feint_active` flag in attack payload defaults to `False` — no existing gold master scenarios use feints, so no drift.
- **Sneak attack interaction:** Feint that denies Dex also enables sneak attack (denied-Dex path already in `is_sneak_attack_eligible()`). This interaction is automatic — no extra code needed since `target_denied_dex = True` feeds the same path.

---

## 6. What This WO Does NOT Do

- No Improved Feint (move action feint — deferred)
- No Uncanny Dodge immunity check (deferred — needs class feature flag)
- No range restriction enforcement beyond "melee" (positional check deferred — intent assumed melee)
- No Feint via ranged attacks (PHB explicitly disallows)
- No Greater Feint feat (deferred)
- No auto-feint from class features (deferred)

---

## 7. Gate Spec

**Gate name:** `ENGINE-FEINT`
**Test file:** `tests/test_engine_gate_feint.py` (new file)

| # | Test | Check |
|---|------|-------|
| FT-01 | FeintIntent success — high Bluff beats low Sense Motive | `feint_success` event; marker in active_combat |
| FT-02 | FeintIntent fail — low Bluff vs high Sense Motive+BAB | `feint_fail` event; no marker in active_combat |
| FT-03 | Feint success → next attack ignores target Dex | Attack event: `feint_flat_footed=true`; `feint_bonus_consumed` emitted |
| FT-04 | Feint marker consumed — second attack NOT flat-footed | Second attack on same target: `feint_flat_footed=false` (marker gone) |
| FT-05 | Feint enables sneak attack for rogue | Rogue feints → denied-Dex path → sneak attack dice added to damage |
| FT-06 | Feint invalid — actor has 0 Bluff ranks | `feint_invalid` event; no marker set |
| FT-07 | Feint marker expires at feinting actor's next turn | `feint_expired` emitted; queue cleared |
| FT-08 | Feint marker does NOT apply to different target | Attack on non-feinted target: `feint_flat_footed=false` |
| FT-09 | FeintIntent costs standard action slot | Action budget: standard used; subsequent standard → ACTION_DENIED |
| FT-10 | Zero regressions suite-wide | Full suite: no new failures |

**Test count target:** ENGINE-FEINT 10/10.

---

## 8. Preflight

```bash
cd f:/DnD-3.5

# Confirm baseline
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5

# After implementation
python -m pytest tests/test_engine_gate_feint.py -v
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5
```
