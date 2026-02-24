# WO-ENGINE-DEFEND-001 — Fight Defensively + Total Defense (PHB p.142)

**Issued:** 2026-02-24
**Authority:** PM
**Gate:** ENGINE-DEFEND (new gate, defined below)

---

## 1. Target Lock

PHB p.142 defines two defensive combat actions:

**Fight Defensively (standard action or as part of full-attack):**
- −4 penalty to all attack rolls this round
- +2 dodge bonus to AC this round
- With Combat Expertise feat: −5 attack / +5 AC (PHB p.92)

**Total Defense (standard action):**
- No attacks allowed this round
- +4 dodge bonus to AC this round
- Can be combined with 5-foot step
- With Expertise feat: not modified — Total Defense is always +4

Both bonuses are **dodge bonuses** — they do stack with other dodge bonuses (unlike most bonuses which don't stack with same type).

Both modifiers persist until **start of the actor's next turn**, using the existing `EF.TEMPORARY_MODIFIERS` dict pattern established by `ChargeIntent` (charge_ac).

**Done means:** `FightDefensivelyIntent` + `TotalDefenseIntent` + modifier write/clear via `TEMPORARY_MODIFIERS` + attack penalty applied in `attack_resolver.py` + dodge bonus applied to AC in `attack_resolver.py` + `fight_defensively_applied` / `total_defense_applied` / `fight_defensively_expired` / `total_defense_expired` events + Gate ENGINE-DEFEND 10/10.

---

## 2. PHB Rule (p.142)

> **Fight Defensively as a Standard Action:** You can choose to fight defensively when attacking. If you do so, you take a –4 penalty on all attacks in a round to gain a +2 dodge bonus to AC until the start of your next action.

> **Fight Defensively as a Part of a Full-Attack Action:** During your full-attack action, you can designate one of your melee attacks to be made as a defensive attack. If you do so, that attack is made at a –4 penalty, but you gain a +2 dodge bonus to your AC until the start of your next action.

> **Total Defense:** You can defend yourself as a standard action. You get a +4 dodge bonus to your AC for 1 round. Your AC improves at the start of this action. You cannot combine total defense with fighting defensively or with the benefit of the Combat Expertise feat (since both are meant to represent focusing on defense.)

Key rulings:
- Fight Defensively with **Combat Expertise feat** (PHB p.92): up to −5 attack for +5 dodge AC (at the attacker's choice of how much penalty to take). For scope: implement at flat −5 attack / +5 AC when actor has the feat and uses FightDefensivelyIntent.
- Total Defense and Fight Defensively are **mutually exclusive** (can't do both in same round)
- Total Defense prevents **all attacks** in the same round
- Both bonuses are type `dodge` — stack with other dodge sources

**Scope for this WO:**
- `FightDefensivelyIntent` as a standard action (not full-attack sub-option — deferred)
- `TotalDefenseIntent` as a standard action
- Combat Expertise escalation: detect feat on actor, apply −5/+5 instead of −4/+2
- Modifier persistence via `TEMPORARY_MODIFIERS` (same pattern as `charge_ac`)
- Attack penalty applied in `attack_resolver.py` at attack roll computation
- Dodge bonus applied to AC in `attack_resolver.py` at AC calculation (as bonus to defender's effective AC)
- Full-attack sub-option (PHB: designate one attack as defensive within full-attack) — **deferred**

---

## 3. New Entity Fields

None. Defensive modifiers stored in `EF.TEMPORARY_MODIFIERS` dict on the actor entity, same as `charge_ac`. Keys:
- `"fight_defensively_ac"` — dodge bonus to AC (2 or 5)
- `"fight_defensively_attack"` — attack penalty (−4 or −5)
- `"total_defense_ac"` — dodge bonus to AC (4)

---

## 4. Implementation Spec

### 4.1 New Intents (intents.py)

```python
@dataclass
class FightDefensivelyIntent:
    """Intent to fight defensively this round.

    PHB p.142: Standard action. −4 attack / +2 dodge AC (or −5/+5 with Combat Expertise).
    Modifier persists until start of actor's next turn.

    WO-ENGINE-DEFEND-001
    """
    actor_id: str

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data) -> "FightDefensivelyIntent": ...


@dataclass
class TotalDefenseIntent:
    """Intent to take total defense this round.

    PHB p.142: Standard action. +4 dodge AC. No attacks allowed.
    Modifier persists until start of actor's next turn.

    WO-ENGINE-DEFEND-001
    """
    actor_id: str

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data) -> "TotalDefenseIntent": ...
```

Add both to Intent union and `parse_intent()` dispatcher.

### 4.2 Modifier Keys in `EF.TEMPORARY_MODIFIERS`

| Key | Value | When set | When cleared |
|-----|-------|----------|--------------|
| `"fight_defensively_attack"` | int (−4 or −5) | On FightDefensivelyIntent | Turn start |
| `"fight_defensively_ac"` | int (+2 or +5) | On FightDefensivelyIntent | Turn start |
| `"total_defense_ac"` | int (+4) | On TotalDefenseIntent | Turn start |

### 4.3 `play_loop.py` — Intent Routing

**A. Turn-start clearance** (beside the existing `charge_ac` block):

```python
# Clear fight_defensively and total_defense modifiers at turn start
_defend_keys = ("fight_defensively_attack", "fight_defensively_ac", "total_defense_ac")
if any(k in _temp_mods for k in _defend_keys):
    _entities_cleared = deepcopy(world_state.entities)
    _cleared_mods = dict(_entities_cleared[turn_ctx.actor_id].get(EF.TEMPORARY_MODIFIERS, {}))
    for k in _defend_keys:
        _cleared_mods.pop(k, None)
    _entities_cleared[turn_ctx.actor_id][EF.TEMPORARY_MODIFIERS] = _cleared_mods
    world_state = WorldState(...)
    events.append(Event(event_type="fight_defensively_expired" or "total_defense_expired", ...))
```

Emit `fight_defensively_expired` if `fight_defensively_ac` was present; emit `total_defense_expired` if `total_defense_ac` was present.

**B. FightDefensivelyIntent routing:**

```python
elif isinstance(combat_intent, FightDefensivelyIntent):
    actor = world_state.entities.get(combat_intent.actor_id, {})
    feats = actor.get(EF.FEATS, [])
    has_combat_expertise = "COMBAT_EXPERTISE" in feats or "Combat Expertise" in feats
    attack_penalty = -5 if has_combat_expertise else -4
    ac_bonus = 5 if has_combat_expertise else 2
    # Write to TEMPORARY_MODIFIERS
    mods = dict(actor.get(EF.TEMPORARY_MODIFIERS, {}))
    mods["fight_defensively_attack"] = attack_penalty
    mods["fight_defensively_ac"] = ac_bonus
    # Update world state entity
    ...
    events.append(Event(event_type="fight_defensively_applied", payload={
        "actor_id": combat_intent.actor_id,
        "attack_penalty": attack_penalty,
        "ac_bonus": ac_bonus,
        "combat_expertise": has_combat_expertise,
    }))
    current_event_id += 1
```

**C. TotalDefenseIntent routing:**

```python
elif isinstance(combat_intent, TotalDefenseIntent):
    mods = dict(actor.get(EF.TEMPORARY_MODIFIERS, {}))
    mods["total_defense_ac"] = 4
    # Also: guard against subsequent attack intents in same turn — handled by action economy
    ...
    events.append(Event(event_type="total_defense_applied", payload={
        "actor_id": combat_intent.actor_id,
        "ac_bonus": 4,
    }))
    current_event_id += 1
```

### 4.4 `attack_resolver.py` — Apply Modifiers

**Attack roll computation** — read attacker's `TEMPORARY_MODIFIERS`:

```python
# WO-ENGINE-DEFEND-001: Fight defensively attack penalty
_attacker_mods = intent_attacker.get(EF.TEMPORARY_MODIFIERS, {})
_fd_attack_penalty = _attacker_mods.get("fight_defensively_attack", 0)
# Add _fd_attack_penalty to total_attack_bonus (it's negative, so subtracted)
```

**AC computation** — read defender's `TEMPORARY_MODIFIERS`:

```python
# WO-ENGINE-DEFEND-001: Fight defensively / total defense AC bonus
_defender_mods = defender.get(EF.TEMPORARY_MODIFIERS, {})
_fd_ac_bonus = _defender_mods.get("fight_defensively_ac", 0)
_td_ac_bonus = _defender_mods.get("total_defense_ac", 0)
_defend_ac_total = _fd_ac_bonus + _td_ac_bonus  # can't both be set, but guard handles it
# Add _defend_ac_total to effective defender AC
```

Add `fight_defensively_ac_bonus` and `total_defense_ac_bonus` fields to attack event payload (both 0 when absent, always present when a defensive action is active in the scenario).

### 4.5 Total Defense — No-Attack Guard

PHB p.142: "You cannot take a standard action to attack" while Total Defense is active. But Total Defense **is** the standard action, so no subsequent attack is possible within the same action budget. The action economy already enforces one standard action per turn — this is implicit. No additional guard needed.

### 4.6 Action Economy

Add to `_build_action_types()` in `action_economy.py`:

```python
_try_add(mapping, "aidm.schemas.intents", "FightDefensivelyIntent", "standard")
_try_add(mapping, "aidm.schemas.intents", "TotalDefenseIntent", "standard")
```

### 4.7 New Event Types

| Event | When | Key Payload Fields |
|-------|------|--------------------|
| `fight_defensively_applied` | `FightDefensivelyIntent` processed | actor_id, attack_penalty, ac_bonus, combat_expertise |
| `total_defense_applied` | `TotalDefenseIntent` processed | actor_id, ac_bonus (4) |
| `fight_defensively_expired` | Turn start with `fight_defensively_ac` in temp mods | entity_id |
| `total_defense_expired` | Turn start with `total_defense_ac` in temp mods | entity_id |

---

## 5. Regression Risk

- **LOW for new intents:** No existing tests use FightDefensivelyIntent or TotalDefenseIntent.
- **LOW for turn-start clearance:** Guards empty dict — only emits events when the keys are actually present.
- **MEDIUM for attack_resolver.py:** The new modifier reads happen on every attack. Guard: `_attacker_mods.get("fight_defensively_attack", 0)` is 0 when absent — no-op for existing flows.
- **Gold masters:** Modifier reads are no-ops (return 0) when absent. No event emitted if temp mods don't contain the defend keys. No gold master drift expected.

---

## 6. What This WO Does NOT Do

- No fight defensively as part of full-attack (full-attack sub-option — deferred)
- No Combat Expertise mid-range: spec is flat −5/+5 when feat is present (full Combat Expertise sliding-scale deferred)
- No Total Defense preventing 5-foot step (PHB explicitly allows it — already allowed)
- No Tumble-based AC bonus (Tumble skill — deferred)
- No defensive casting stance (concentration bonus — deferred)
- No Expertise interaction with total defense (PHB: they're mutually exclusive — action economy handles this implicitly via standard action slot)

---

## 7. Gate Spec

**Gate name:** `ENGINE-DEFEND`
**Test file:** `tests/test_engine_gate_defend.py` (new file)

| # | Test | Check |
|---|------|-------|
| DF-01 | FightDefensivelyIntent applies −4 attack / +2 AC | `fight_defensively_applied` event; modifier in TEMPORARY_MODIFIERS |
| DF-02 | Fight defensively attack penalty reduces attack roll | Attacker's attack roll includes −4; reflected in attack event payload |
| DF-03 | Fight defensively AC bonus improves defender AC | Attacker's hit threshold shifts by +2; attack that would hit without bonus misses with it |
| DF-04 | Combat Expertise escalation: −5 attack / +5 AC | Actor with COMBAT_EXPERTISE feat → `fight_defensively_applied.combat_expertise=true`, penalties −5/+5 |
| DF-05 | Fight defensively expired at actor's next turn start | `fight_defensively_expired` emitted; TEMPORARY_MODIFIERS cleared |
| DF-06 | TotalDefenseIntent applies +4 AC | `total_defense_applied` event; `total_defense_ac=4` in TEMPORARY_MODIFIERS |
| DF-07 | Total defense AC bonus improves defender AC | Attacker hit threshold shifts +4; attack that hits at base AC misses with total defense |
| DF-08 | Total defense expired at actor's next turn start | `total_defense_expired` emitted; TEMPORARY_MODIFIERS cleared |
| DF-09 | FightDefensivelyIntent costs standard action slot | Action budget: standard used; subsequent standard → ACTION_DENIED |
| DF-10 | TotalDefenseIntent costs standard action slot | Action budget: standard used; subsequent standard → ACTION_DENIED |

**Test count target:** ENGINE-DEFEND 10/10.

---

## 8. Preflight

```bash
cd f:/DnD-3.5

# Confirm baseline
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5

# After implementation
python -m pytest tests/test_engine_gate_defend.py -v
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5
```
