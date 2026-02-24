# WO-ENGINE-ABILITY-DAMAGE-001 — Ability Score Damage and Drain

**Issued:** 2026-02-24
**Authority:** PM Slate — Thunder approval
**Gate:** ENGINE-ABILITY-DAMAGE (new gate, defined below)
**Parallel-safe:** Yes — adds new EF constants, a new `AbilityDamageIntent` in `intents.py`, and a new `ability_damage_resolver.py`. Touches `attack_resolver.py` (additive bonus adjustment), `rest_resolver.py` (additive heal hook), and `play_loop.py` (new routing branch). Does not overlap with WO-ENGINE-DR-001 (DR path in attack resolution, different section), WO-ENGINE-DEATH-DYING-001 (HP band transitions, different resolver), WO-ENGINE-NONLETHAL-001 (nonlethal pool, different field), or WO-ENGINE-ENERGY-DRAIN-001 (negative levels, different field and resolver).

---

## §1 Target Lock

### What is broken

No ability score damage or drain mechanics exist anywhere in the engine. Poison, disease, and special monster attacks (wight STR drain, shadow STR drain, ghoul paralysis degradation, ability-damaging spells such as Ray of Enfeeblement or Bestow Curse) all require this mechanic. Currently:

- No `STR_DAMAGE`, `DEX_DAMAGE`, `CON_DAMAGE`, `INT_DAMAGE`, `WIS_DAMAGE`, `CHA_DAMAGE` fields exist on entities.
- No `STR_DRAIN`, `DEX_DRAIN`, `CON_DRAIN`, `INT_DRAIN`, `WIS_DRAIN`, `CHA_DRAIN` fields exist.
- No `AbilityDamageIntent` exists in `aidm/schemas/intents.py`.
- No `ability_damage_resolver.py` exists in `aidm/core/`.
- `attack_resolver.py` computes attack bonus from `EF.ATTACK_BONUS` and `EF.STR_MOD` without considering any current STR damage. `EF.DEX_MOD` feeds AC without considering DEX damage. `EF.SAVE_FORT`, `EF.SAVE_REF`, and `EF.SAVE_WILL` are read directly without CON/DEX/WIS damage adjustments.
- `rest_resolver.py` clears some conditions on overnight rest but never heals ability damage.

### What "done" means

- Twelve new EF constants exist (6 damage + 6 drain, all int, default 0).
- `AbilityDamageIntent` dataclass exists in `aidm/schemas/intents.py` and is registered in `parse_intent()`.
- `ability_damage_resolver.py` contains `apply_ability_damage()`, `get_effective_score()`, `get_ability_modifier()`, `heal_ability_damage()`, and `expire_ability_damage_regen()`.
- `attack_resolver.py` reads effective STR score (base − damage − drain) when computing the STR modifier contribution to attack and damage rolls, and reads effective DEX score when computing the DEX bonus cap to AC.
- `rest_resolver.py` calls `expire_ability_damage_regen()` on overnight rest, healing 1 point per damaged ability (damage only — drain does not recover).
- `play_loop.py` routes `AbilityDamageIntent` to `ability_damage_resolver.py`.
- Events `ability_damage_applied`, `ability_score_zero`, and `ability_damage_healed` are emitted with correct payloads.
- Gate ENGINE-ABILITY-DAMAGE 10/10 passes.

---

## §2 PHB Rule Reference

**PHB 3.5e p.215 — Ability Score Loss:**

> **Ability Damage:** Some attacks reduce your ability scores. Some are temporary, reducing an ability score by a specified amount. When an ability score is reduced by 2 points, the modifier decreases by 1. When it comes back up, the modifier goes up accordingly.
>
> **Ability Drain:** Other effects permanently reduce a character's ability score. Points lost to ability drain do not return unless the character gains levels (for experience-based increases) or the effect is reversed by magic such as restoration.

**PHB 3.5e p.215 — Healing Ability Damage:**

> Temporary ability damage returns at the rate of 1 point per day of rest.

**Key rules encoded:**

| Rule | Implementation |
|------|----------------|
| Effective score = base − damage − drain | `get_effective_score(entity, ability)` |
| Each 2 points of loss → −1 to modifier | `get_ability_modifier()` uses `(effective − 10) // 2` |
| Damage heals at 1/day on rest | `expire_ability_damage_regen()` called from `rest_resolver.py` |
| Drain does NOT recover naturally | Drain field never decremented by rest |
| CON to 0 → dead | `apply_ability_damage()` emits `ability_score_zero` with `effect="dead"` |
| STR or DEX to 0 → helpless | `ability_score_zero` with `effect="helpless"` |
| INT, WIS, or CHA to 0 → incapacitated | `ability_score_zero` with `effect="incapacitated"` |
| STR damage → attack/damage roll penalty | `attack_resolver.py` reads effective STR modifier |
| DEX damage → AC/Reflex penalty | `attack_resolver.py` reads effective DEX modifier for AC; save adjustments below |
| CON damage → Fort save penalty | Fort save adjusted dynamically in save resolution |
| Undead immune to ability damage | Caller responsibility — `EF.IS_UNDEAD` flag already exists on entities |

**Modifier computation:**

```
effective_score = base_score − ability_damage − ability_drain
modifier        = (effective_score − 10) // 2
```

The floor division in Python naturally handles odd effective scores (e.g., effective STR 9 → modifier −1, effective STR 7 → modifier −2).

---

## §3 Binary Decisions — Locked

| Decision | Answer |
|----------|--------|
| New resolver file | `aidm/core/ability_damage_resolver.py` |
| Intent location | `aidm/schemas/intents.py` alongside all other intents |
| Damage fields vs. drain fields | Separate: `STR_DAMAGE` (temporary) and `STR_DRAIN` (permanent), for all 6 abilities — 12 constants total |
| Effective score floor | 0 — cannot go negative |
| 0-score death/incap check | Performed inside `apply_ability_damage()` — emits event before returning |
| Save adjustment strategy | Dynamic: save resolver reads effective ability score at resolution time; this WO adds the helper function; save resolver integration is specified as integration point below |
| Rest heal quantity | 1 point per damaged ability per overnight rest (PHB p.215 "one ability per day" interpretation: each damaged ability heals 1 point per day — all damaged abilities each get 1 point) |
| Drain recovery | None — only magic (Restoration spell) removes drain. Out of scope. |
| Undead immunity enforcement | Enforced by the caller (AI/DM layer) via `EF.IS_UNDEAD`. The resolver does not add its own immunity check — consistent with how `EnergyDrainAttackIntent` handles it. |
| Event sourcing pattern | Identical to all other resolvers: pure function returns events, caller applies with `apply_ability_damage_events()` |

---

## §4 Implementation Spec

### §4.1 New EF constants in `aidm/schemas/entity_fields.py`

Add after the `NEGATIVE_LEVELS` entry (line 172), in a new section:

```python
# --- Ability Score Damage and Drain (WO-ENGINE-ABILITY-DAMAGE-001) ---
# Temporary ability damage — heals at 1 point per day of rest (PHB p.215)
STR_DAMAGE = "str_damage"   # Int: temporary STR reduction. Default 0.
DEX_DAMAGE = "dex_damage"   # Int: temporary DEX reduction. Default 0.
CON_DAMAGE = "con_damage"   # Int: temporary CON reduction. Default 0.
INT_DAMAGE = "int_damage"   # Int: temporary INT reduction. Default 0.
WIS_DAMAGE = "wis_damage"   # Int: temporary WIS reduction. Default 0.
CHA_DAMAGE = "cha_damage"   # Int: temporary CHA reduction. Default 0.
# Permanent ability drain — does NOT recover naturally (PHB p.215)
STR_DRAIN = "str_drain"     # Int: permanent STR reduction. Default 0.
DEX_DRAIN = "dex_drain"     # Int: permanent DEX reduction. Default 0.
CON_DRAIN = "con_drain"     # Int: permanent CON reduction. Default 0.
INT_DRAIN = "int_drain"     # Int: permanent INT reduction. Default 0.
WIS_DRAIN = "wis_drain"     # Int: permanent WIS reduction. Default 0.
CHA_DRAIN = "cha_drain"     # Int: permanent CHA reduction. Default 0.
```

**12 new constants total.** All are read via `.get(EF.STR_DAMAGE, 0)` etc. — no entity migration required; missing field equals 0.

### §4.2 New `AbilityDamageIntent` in `aidm/schemas/intents.py`

Add after `FeintIntent` (after line 603, before the `Intent` type alias):

```python
@dataclass
class AbilityDamageIntent:
    """Intent to apply ability score damage or drain to a target entity.

    PHB p.215: Used by poison, disease, and special monster attacks
    (wight slam, shadow touch, ray spells, etc.) that reduce ability scores
    temporarily (damage) or permanently (drain).

    Temporary damage heals at 1 point per day of rest.
    Permanent drain requires magic (Restoration) to remove.

    WO-ENGINE-ABILITY-DAMAGE-001
    """

    actor_id: str
    """Entity applying the effect (attacker, spell source, or 'environment' for poison)."""

    target_id: str
    """Entity whose ability score is being reduced."""

    ability: Literal["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    """Which ability score is affected."""

    amount: int
    """Number of points to reduce the ability score by. Must be >= 1."""

    is_drain: bool = False
    """If True, this is permanent drain (written to STR_DRAIN etc.).
    If False (default), this is temporary damage (written to STR_DAMAGE etc.)."""

    def __post_init__(self):
        valid_abilities = {"STR", "DEX", "CON", "INT", "WIS", "CHA"}
        if self.ability not in valid_abilities:
            raise IntentParseError(
                f"AbilityDamageIntent: ability must be one of {valid_abilities}, "
                f"got '{self.ability}'"
            )
        if self.amount < 1:
            raise IntentParseError(
                f"AbilityDamageIntent: amount must be >= 1, got {self.amount}"
            )
        if not self.actor_id:
            raise IntentParseError("AbilityDamageIntent: actor_id cannot be empty")
        if not self.target_id:
            raise IntentParseError("AbilityDamageIntent: target_id cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "ability_damage",
            "actor_id": self.actor_id,
            "target_id": self.target_id,
            "ability": self.ability,
            "amount": self.amount,
            "is_drain": self.is_drain,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AbilityDamageIntent":
        if data.get("type") != "ability_damage":
            raise IntentParseError(
                f"Expected type 'ability_damage', got '{data.get('type')}'"
            )
        return cls(
            actor_id=data["actor_id"],
            target_id=data["target_id"],
            ability=data["ability"],
            amount=data["amount"],
            is_drain=data.get("is_drain", False),
        )
```

**Update the `Intent` type alias** (line 607) to include `AbilityDamageIntent`:

```python
Intent = (CastSpellIntent | MoveIntent | DeclaredAttackIntent | BuyIntent | RestIntent |
          SummonCompanionIntent | PrepareSpellsIntent | ChargeIntent | CoupDeGraceIntent |
          TurnUndeadIntent | ReadyActionIntent | AidAnotherIntent | FightDefensivelyIntent |
          TotalDefenseIntent | FeintIntent | AbilityDamageIntent)
```

**Update `parse_intent()`** (in the `elif` chain, after the `"feint"` branch):

```python
elif intent_type == "ability_damage":
    return AbilityDamageIntent.from_dict(data)
```

### §4.3 New module: `aidm/core/ability_damage_resolver.py`

Full module content:

```python
"""ability_damage_resolver.py — Ability score damage and drain mechanics.

PHB p.215: Temporary ability damage heals at 1 point per day of rest.
Permanent ability drain does not recover naturally.

Effective score = base_score - ability_damage - ability_drain (floor 0).
Modifier        = (effective_score - 10) // 2

Called from:
  - play_loop.py: on AbilityDamageIntent
  - rest_resolver.py: expire_ability_damage_regen() on overnight rest

WO-ENGINE-ABILITY-DAMAGE-001
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Tuple

from aidm.schemas.entity_fields import EF

# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

# Maps ability name → (base_score_field, damage_field, drain_field)
_ABILITY_FIELDS: Dict[str, Tuple[str, str, str]] = {
    "STR": (EF.BASE_STATS,   EF.STR_DAMAGE, EF.STR_DRAIN),
    "DEX": (EF.BASE_STATS,   EF.DEX_DAMAGE, EF.DEX_DRAIN),
    "CON": (EF.BASE_STATS,   EF.CON_DAMAGE, EF.CON_DRAIN),
    "INT": (EF.BASE_STATS,   EF.INT_DAMAGE, EF.INT_DRAIN),
    "WIS": (EF.BASE_STATS,   EF.WIS_DAMAGE, EF.WIS_DRAIN),
    "CHA": (EF.BASE_STATS,   EF.CHA_DAMAGE, EF.CHA_DRAIN),
}

# Maps ability name → key inside EF.BASE_STATS dict
_BASE_STATS_KEY: Dict[str, str] = {
    "STR": "str", "DEX": "dex", "CON": "con",
    "INT": "int", "WIS": "wis", "CHA": "cha",
}

# Maps ability name → (damage EF constant, drain EF constant)
_DAMAGE_DRAIN_FIELDS: Dict[str, Tuple[str, str]] = {
    "STR": (EF.STR_DAMAGE, EF.STR_DRAIN),
    "DEX": (EF.DEX_DAMAGE, EF.DEX_DRAIN),
    "CON": (EF.CON_DAMAGE, EF.CON_DRAIN),
    "INT": (EF.INT_DAMAGE, EF.INT_DRAIN),
    "WIS": (EF.WIS_DAMAGE, EF.WIS_DRAIN),
    "CHA": (EF.CHA_DAMAGE, EF.CHA_DRAIN),
}

# 0-score consequence per ability (PHB p.215)
_ZERO_SCORE_EFFECT: Dict[str, str] = {
    "STR": "helpless",
    "DEX": "helpless",
    "CON": "dead",
    "INT": "incapacitated",
    "WIS": "incapacitated",
    "CHA": "incapacitated",
}


def _get_base_score(entity: Dict[str, Any], ability: str) -> int:
    """Return raw base ability score from entity dict."""
    base_stats = entity.get(EF.BASE_STATS, {})
    key = _BASE_STATS_KEY[ability]
    return base_stats.get(key, 10)


def get_effective_score(entity: Dict[str, Any], ability: str) -> int:
    """Return effective ability score after damage and drain.

    effective = base - damage - drain, floored at 0.

    PHB p.215: Both temporary damage and permanent drain reduce the score.

    Args:
        entity: Entity dict.
        ability: One of "STR", "DEX", "CON", "INT", "WIS", "CHA".

    Returns:
        Effective ability score (int, >= 0).
    """
    damage_field, drain_field = _DAMAGE_DRAIN_FIELDS[ability]
    base = _get_base_score(entity, ability)
    damage = entity.get(damage_field, 0)
    drain = entity.get(drain_field, 0)
    return max(0, base - damage - drain)


def get_ability_modifier(entity: Dict[str, Any], ability: str) -> int:
    """Return ability modifier after all damage and drain.

    modifier = (effective_score - 10) // 2

    PHB p.8: Standard 3.5e modifier formula.
    Each 2 points of ability damage/drain shifts the modifier by 1.

    Args:
        entity: Entity dict.
        ability: One of "STR", "DEX", "CON", "INT", "WIS", "CHA".

    Returns:
        Ability modifier (int, can be negative).
    """
    effective = get_effective_score(entity, ability)
    return (effective - 10) // 2


def apply_ability_damage(
    entity: Dict[str, Any],
    ability: str,
    amount: int,
    is_drain: bool,
    actor_id: str,
    entity_id: str,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Apply ability damage or drain to an entity.

    Updates the entity dict in-place (caller should work on a deepcopy).
    Emits ability_damage_applied event. If effective score reaches 0,
    also emits ability_score_zero event.

    PHB p.215: Temporary damage written to STR_DAMAGE etc.
               Permanent drain written to STR_DRAIN etc.

    Args:
        entity:       Mutable entity dict (caller's deepcopy).
        ability:      "STR", "DEX", "CON", "INT", "WIS", or "CHA".
        amount:       Points of damage/drain to apply (>= 1).
        is_drain:     True → permanent drain; False → temporary damage.
        actor_id:     Source of the damage (for event payload).
        entity_id:    Target entity ID (for event payload).
        next_event_id: Starting event ID counter.
        timestamp:    Event timestamp.

    Returns:
        (events, entity): Events list and updated entity dict.
    """
    events: List[Dict[str, Any]] = []
    eid = next_event_id

    damage_field, drain_field = _DAMAGE_DRAIN_FIELDS[ability]
    target_field = drain_field if is_drain else damage_field

    # Apply the loss
    current_loss = entity.get(target_field, 0)
    new_loss = current_loss + amount
    entity[target_field] = new_loss

    effective = get_effective_score(entity, ability)

    events.append({
        "event_id": eid,
        "event_type": "ability_damage_applied",
        "timestamp": timestamp,
        "payload": {
            "actor_id": actor_id,
            "target_id": entity_id,
            "ability": ability,
            "amount": amount,
            "is_drain": is_drain,
            "new_score": _get_base_score(entity, ability),
            "effective_score": effective,
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 215}],
    })
    eid += 1

    # 0-score consequence check (PHB p.215)
    if effective == 0:
        effect = _ZERO_SCORE_EFFECT[ability]
        events.append({
            "event_id": eid,
            "event_type": "ability_score_zero",
            "timestamp": timestamp + 0.01,
            "payload": {
                "target_id": entity_id,
                "ability": ability,
                "effect": effect,   # "dead", "helpless", or "incapacitated"
            },
            "citations": [{"source_id": "681f92bc94ff", "page": 215}],
        })
        eid += 1

    return events, entity


def heal_ability_damage(
    entity: Dict[str, Any],
    ability: str,
    amount: int,
    entity_id: str,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Heal temporary ability damage (NOT drain) on an entity.

    PHB p.215: Only temporary damage heals. Drain is permanent.
    Healing cannot exceed the current damage total (cannot go below 0).

    Args:
        entity:        Mutable entity dict (caller's deepcopy).
        ability:       "STR", "DEX", "CON", "INT", "WIS", or "CHA".
        amount:        Points of damage to heal.
        entity_id:     Target entity ID (for event payload).
        next_event_id: Starting event ID counter.
        timestamp:     Event timestamp.

    Returns:
        (events, entity): Events list and updated entity dict.
    """
    events: List[Dict[str, Any]] = []
    damage_field, _ = _DAMAGE_DRAIN_FIELDS[ability]

    current_damage = entity.get(damage_field, 0)
    if current_damage <= 0:
        return events, entity   # Nothing to heal

    healed = min(amount, current_damage)
    new_damage = current_damage - healed
    entity[damage_field] = new_damage

    events.append({
        "event_id": next_event_id,
        "event_type": "ability_damage_healed",
        "timestamp": timestamp,
        "payload": {
            "target_id": entity_id,
            "ability": ability,
            "amount": healed,
            "new_damage_total": new_damage,
        },
        "citations": [{"source_id": "681f92bc94ff", "page": 215}],
    })
    return events, entity


def expire_ability_damage_regen(
    world_state: Any,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Dict[str, Any]], Any]:
    """Heal 1 point of temporary damage per damaged ability, for all entities.

    PHB p.215: "Temporary ability damage returns at the rate of 1 point per
    day of rest." Each damaged ability heals 1 point per overnight rest.
    Drain fields are never touched.

    Called from rest_resolver.py after overnight rest is confirmed.

    Args:
        world_state:   Current WorldState.
        next_event_id: Starting event ID counter.
        timestamp:     Event timestamp.

    Returns:
        (events, updated_world_state)
    """
    from copy import deepcopy

    events: List[Dict[str, Any]] = []
    current_event_id = next_event_id
    entities = {k: deepcopy(v) for k, v in world_state.entities.items()}

    DAMAGE_FIELDS = [
        ("STR", EF.STR_DAMAGE),
        ("DEX", EF.DEX_DAMAGE),
        ("CON", EF.CON_DAMAGE),
        ("INT", EF.INT_DAMAGE),
        ("WIS", EF.WIS_DAMAGE),
        ("CHA", EF.CHA_DAMAGE),
    ]

    for entity_id in sorted(entities.keys()):   # deterministic order
        entity = entities[entity_id]
        for ability, damage_field in DAMAGE_FIELDS:
            current_damage = entity.get(damage_field, 0)
            if current_damage > 0:
                heal_events, entity = heal_ability_damage(
                    entity=entity,
                    ability=ability,
                    amount=1,
                    entity_id=entity_id,
                    next_event_id=current_event_id,
                    timestamp=timestamp,
                )
                events.extend(heal_events)
                current_event_id += len(heal_events)

    from aidm.core.state import WorldState
    updated_state = WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat,
        narrative_context=world_state.narrative_context,
        scene_type=world_state.scene_type,
    )
    return events, updated_state


def apply_ability_damage_events(
    world_state: Any,
    events: List[Dict[str, Any]],
) -> Any:
    """Apply ability damage/drain/heal events to world state.

    Handles:
    - ability_damage_applied: updates damage or drain field on entity
    - ability_damage_healed: decrements damage field on entity
    - ability_score_zero: no field mutation (consequence handled by play_loop)

    Returns updated WorldState (deepcopy pattern).
    """
    from copy import deepcopy
    from aidm.core.state import WorldState

    entities = deepcopy(world_state.entities)

    for event in events:
        etype = event.get("event_type") or event.event_type
        payload = event.get("payload") or event.payload
        target_id = payload.get("target_id")
        if target_id not in entities:
            continue

        entity = entities[target_id]

        if etype == "ability_damage_applied":
            ability = payload["ability"]
            amount = payload["amount"]
            is_drain = payload["is_drain"]
            damage_field, drain_field = _DAMAGE_DRAIN_FIELDS[ability]
            field = drain_field if is_drain else damage_field
            entity[field] = entity.get(field, 0) + amount

        elif etype == "ability_damage_healed":
            ability = payload["ability"]
            new_damage_total = payload["new_damage_total"]
            damage_field, _ = _DAMAGE_DRAIN_FIELDS[ability]
            entity[damage_field] = new_damage_total

        # ability_score_zero: informational only, no field mutation needed

    return WorldState(
        ruleset_version=world_state.ruleset_version,
        entities=entities,
        active_combat=world_state.active_combat,
        narrative_context=world_state.narrative_context,
        scene_type=world_state.scene_type,
    )
```

### §4.4 Integration: `aidm/core/attack_resolver.py` — effective STR for attack/damage

**Location:** In the attack bonus assembly block, after the line that reads `str_mod` from `EF.STR_MOD` (approximately line 270–285, in `resolve_attack()`).

Current code reads the pre-computed modifier:
```python
str_mod = attacker.get(EF.STR_MOD, 0)
```

Replace (or supplement) with the effective modifier computed from current scores:

```python
# WO-ENGINE-ABILITY-DAMAGE-001: use effective STR (reduced by any damage/drain)
from aidm.core.ability_damage_resolver import get_ability_modifier
str_effective_mod = get_ability_modifier(attacker, "STR")
# Use the lesser of the pre-computed mod and the effective mod.
# Pre-computed mod may include equipment/magic bonuses that stack on top of base;
# effective mod is computed from BASE_STATS only. Use effective_mod as the
# base and preserve any delta between EF.STR_MOD and the raw base str_mod.
_raw_str_base_mod = (attacker.get(EF.BASE_STATS, {}).get("str", 10) - 10) // 2
_str_mod_from_base = attacker.get(EF.STR_MOD, 0)
_str_bonus_above_base = _str_mod_from_base - _raw_str_base_mod
str_effective_mod_total = str_effective_mod + _str_bonus_above_base
```

**Builder note:** If the entity's `EF.STR_MOD` is purely the raw base modifier (no equipment stacking), the simpler form suffices:

```python
from aidm.core.ability_damage_resolver import get_ability_modifier
str_mod = get_ability_modifier(attacker, "STR")
```

Builder should audit `attack_resolver.py` lines 270–290 to confirm which pattern applies before choosing. The key invariant: **damaged STR reduces attack bonus, and every 2 points of STR damage reduces the attack modifier by 1.**

**Location for DEX/AC:** In AC computation (if `attack_resolver.py` computes target AC adjustments), read DEX-effective modifier:

```python
# WO-ENGINE-ABILITY-DAMAGE-001: effective DEX modifier for AC
from aidm.core.ability_damage_resolver import get_ability_modifier
dex_effective_mod = get_ability_modifier(target, "DEX")
# DEX bonus to AC is capped at 0 if DEX damaged to 0 (entity is helpless)
```

### §4.5 Integration: `aidm/core/rest_resolver.py` — expire ability damage on overnight rest

**Location:** In `resolve_rest()`, after the spell slot restoration block (approximately line 169), inside the `if is_full_rest:` block.

Add after the existing slot restoration call:

```python
# WO-ENGINE-ABILITY-DAMAGE-001: Heal 1 point per damaged ability on overnight rest (PHB p.215)
from aidm.core.ability_damage_resolver import expire_ability_damage_regen
ability_heal_events, world_state = expire_ability_damage_regen(
    world_state=world_state,
    next_event_id=next_event_id,
    timestamp=timestamp,
)
events.extend(ability_heal_events)
if ability_heal_events:
    next_event_id += len(ability_heal_events)
```

This is a purely additive addition. Entities with no ability damage (all existing entities) have `STR_DAMAGE == 0` etc., so `expire_ability_damage_regen()` emits zero events and the rest of `resolve_rest()` is unaffected.

### §4.6 Integration: `aidm/core/play_loop.py` — route `AbilityDamageIntent`

In the `execute_turn()` intent routing block, add after the `FeintIntent` branch and before the fallthrough/else:

```python
elif isinstance(combat_intent, AbilityDamageIntent):
    # WO-ENGINE-ABILITY-DAMAGE-001: ability score damage/drain
    from aidm.core.ability_damage_resolver import (
        apply_ability_damage, apply_ability_damage_events
    )
    from copy import deepcopy

    target = world_state.entities.get(combat_intent.target_id)
    if target is None:
        events.append({
            "event_id": current_event_id,
            "event_type": "intent_validation_failed",
            "timestamp": timestamp,
            "payload": {
                "reason": "target_not_found",
                "target_id": combat_intent.target_id,
            },
        })
        current_event_id += 1
    else:
        entity_copy = deepcopy(target)
        dmg_events, _ = apply_ability_damage(
            entity=entity_copy,
            ability=combat_intent.ability,
            amount=combat_intent.amount,
            is_drain=combat_intent.is_drain,
            actor_id=combat_intent.actor_id,
            entity_id=combat_intent.target_id,
            next_event_id=current_event_id,
            timestamp=timestamp,
        )
        events.extend(dmg_events)
        current_event_id += len(dmg_events)
        world_state = apply_ability_damage_events(world_state, dmg_events)
```

**Also update `parse_intent()` import at the top of `play_loop.py`** (or in the routing block import): `AbilityDamageIntent` must be importable from `aidm.schemas.intents`.

---

## §5 Event Types

| Event type | Emitted when | New? |
|------------|--------------|------|
| `ability_damage_applied` | `apply_ability_damage()` called — any damage or drain applied | YES |
| `ability_score_zero` | Effective score reaches 0 after applying damage/drain | YES |
| `ability_damage_healed` | `heal_ability_damage()` called and damage > 0 existed | YES |

### `ability_damage_applied` payload

```json
{
  "event_type": "ability_damage_applied",
  "payload": {
    "actor_id": "shadow_01",
    "target_id": "fighter_pc",
    "ability": "STR",
    "amount": 2,
    "is_drain": true,
    "new_score": 16,
    "effective_score": 14
  }
}
```

- `new_score`: base score (unchanged by damage/drain — this is the raw score)
- `effective_score`: base − damage − drain (what the engine uses for mechanics)

### `ability_score_zero` payload

```json
{
  "event_type": "ability_score_zero",
  "payload": {
    "target_id": "fighter_pc",
    "ability": "STR",
    "effect": "helpless"
  }
}
```

`effect` values: `"dead"` (CON), `"helpless"` (STR, DEX), `"incapacitated"` (INT, WIS, CHA).

### `ability_damage_healed` payload

```json
{
  "event_type": "ability_damage_healed",
  "payload": {
    "target_id": "fighter_pc",
    "ability": "STR",
    "amount": 1,
    "new_damage_total": 1
  }
}
```

---

## §6 Regression Risk

**Low.** All changes are either additive (new fields with default 0, new resolver module, new routing branch) or delta-zero for existing entities (which have no ability damage fields, so all `.get(EF.STR_DAMAGE, 0)` calls return 0).

**Specific risks:**

1. **`attack_resolver.py` STR modifier change (§4.4):** If `get_ability_modifier(attacker, "STR")` is used in place of the existing `EF.STR_MOD` read, and existing test entities do not have `EF.BASE_STATS` populated with a `"str"` key, `_get_base_score()` defaults to 10 (modifier 0). Existing fixtures must have `EF.BASE_STATS` or `EF.STR_MOD` consistent. Builder should verify that `EF.BASE_STATS` is populated on all test entities before switching the read path. If not, the simpler guard approach is: read `EF.STR_MOD` and subtract `get_ability_modifier_penalty(attacker, "STR")` where penalty = (damage + drain) // 2. This is strictly additive.

2. **`rest_resolver.py` addition (§4.5):** Purely additive. `expire_ability_damage_regen()` returns 0 events for all existing fixture entities. Zero regression risk.

3. **New `AbilityDamageIntent` routing in `play_loop.py` (§4.6):** Additive new `elif` branch. Does not affect any existing routing path.

4. **Gold master impact:** None expected. No existing gold master scenario uses `AbilityDamageIntent` or entities with ability damage fields. Gold masters will not change.

---

## §7 Gate Spec

**Gate name:** `ENGINE-ABILITY-DAMAGE`
**Test file:** `tests/test_engine_ability_damage_gate.py`

| # | Test ID | Description | Assert |
|---|---------|-------------|--------|
| 1 | AD-01 | All 12 EF constants exist on the `EF` singleton | `hasattr(EF, "STR_DAMAGE")` through `hasattr(EF, "CHA_DRAIN")` — 12 assertions all True |
| 2 | AD-02 | `apply_ability_damage()` with `is_drain=False`, `ability="STR"`, `amount=4` on entity with `base_stats.str=16` → effective STR = 12 | `get_effective_score(entity, "STR") == 12` |
| 3 | AD-03 | `apply_ability_damage()` with `is_drain=True`, `ability="STR"`, `amount=2` → `EF.STR_DRAIN == 2`, `EF.STR_DAMAGE == 0` (drain field used, not damage field) | `entity[EF.STR_DRAIN] == 2` and `entity.get(EF.STR_DAMAGE, 0) == 0` |
| 4 | AD-04 | Entity with `base_stats.str=14`, `STR_DAMAGE=4`, `STR_DRAIN=2` → `get_effective_score(entity, "STR") == 8` (14 − 4 − 2) | `effective == 8` |
| 5 | AD-05 | `apply_ability_damage()` with `ability="CON"`, `amount` sufficient to reduce effective CON to 0 → `ability_score_zero` event emitted with `effect="dead"` | `any(e["event_type"] == "ability_score_zero" and e["payload"]["effect"] == "dead" for e in events)` |
| 6 | AD-06 | `apply_ability_damage()` with `ability="STR"`, effective score reduced to exactly 0 → `ability_score_zero` with `effect="helpless"`. Repeat for `ability="DEX"` → same. | Both abilities: `effect == "helpless"` |
| 7 | AD-07 | `ability_damage_applied` event has all required payload keys: `actor_id`, `target_id`, `ability`, `amount`, `is_drain`, `new_score`, `effective_score` | All 7 keys present and correctly typed |
| 8 | AD-08 | Entity with `base_stats.str=16`, `STR_DAMAGE=3` → `get_ability_modifier(entity, "STR")` returns 1 (effective 13, modifier +1, not +3 from undamaged 16) | `get_ability_modifier(entity, "STR") == 1` |
| 9 | AD-09 | Entity with `base_stats.con=14`, `CON_DAMAGE=4` → effective CON = 10 → CON modifier = 0 → Fort save adjusted accordingly (mock save computation: `EF.SAVE_FORT` base + `get_ability_modifier(entity, "CON")`) | Computed fort save reflects CON modifier of 0, not the +2 from undamaged 14 |
| 10 | AD-10 | `expire_ability_damage_regen()` on entity with `STR_DAMAGE=3` → after call, `STR_DAMAGE=2`; entity with `STR_DRAIN=2` untouched (drain stays at 2) | `entity[EF.STR_DAMAGE] == 2` and `entity[EF.STR_DRAIN] == 2` unchanged |

**Test count target:** 10 checks → Gate `ENGINE-ABILITY-DAMAGE` 10/10.

---

## §8 What This WO Does NOT Do

- Does not implement CON damage → HP max reduction. PHB p.215 states that CON damage reduces Fort saves and CON modifier; HP max reduction from CON changes is a chargen/level concern (PHB p.9). This WO applies the modifier penalty dynamically but does NOT recalculate `EF.HP_MAX` on every CON damage event. HP max adjustment from CON damage is deferred to a follow-up WO.
- Does not implement Restoration or Greater Restoration spells (the magic that removes ability drain). Those are spell resolver additions, deferred.
- Does not implement the "ability damage from poison secondary save failure" timing (poison is a two-stage mechanic with initial and secondary damage separated by 1 minute). This WO provides the damage application primitive; the poison timing loop is a future WO.
- Does not implement ability damage from disease (disease is a save-or-worsen mechanic with a 1-day incubation period). Same pattern — deferred.
- Does not enforce undead immunity within the resolver. The `EF.IS_UNDEAD` field already exists (added by WO-ENGINE-TURN-UNDEAD-001). Immunity enforcement is the caller's responsibility (AI/DM layer checks `EF.IS_UNDEAD` before constructing `AbilityDamageIntent`).
- Does not implement per-hour nonlethal nonlethal recovery — this WO implements only the 1-point-per-ability-per-day-of-rest model from PHB p.215.
- Does not integrate `get_ability_modifier(entity, "DEX")` into `EF.DEX_MOD`-based Reflex save reads or into `EF.SAVE_REF` computation — that integration is specified as an intent (§4.4) but the exact save resolver line numbers are not fixed here, as `save_resolver.py` does not yet exist as a standalone file. Builder must locate the save resolution logic (in `spell_resolver.py` or `attack_resolver.py`) and add the effective modifier lookup there using `get_ability_modifier()`. This is the same additive pattern as `get_negative_level_save_penalty()` from WO-ENGINE-ENERGY-DRAIN-001.
- Does not modify `EF.ATTACK_BONUS` on the entity in place. The effective attack bonus adjustment from STR damage is computed at resolution time, not stored back to the entity field.
- Does not touch `full_attack_resolver.py` directly — the STR modifier read in that file mirrors the pattern in `attack_resolver.py`. Builder must apply the same `get_ability_modifier(attacker, "STR")` substitution in `full_attack_resolver.py` as specified in §4.4 for `attack_resolver.py`.

---

## §9 Preflight

```bash
cd f:/DnD-3.5

# Verify new EF constants are importable:
python -c "from aidm.schemas.entity_fields import EF; print(EF.STR_DAMAGE, EF.CON_DRAIN, EF.CHA_DAMAGE)"
# Expected: str_damage con_drain cha_damage

# Verify AbilityDamageIntent imports cleanly and validates:
python -c "
from aidm.schemas.intents import AbilityDamageIntent
i = AbilityDamageIntent(actor_id='shadow_01', target_id='fighter_pc', ability='STR', amount=2, is_drain=True)
print(i.to_dict())
"
# Expected: dict with all fields printed, no exception.

# Verify invalid ability raises error:
python -c "
from aidm.schemas.intents import AbilityDamageIntent, IntentParseError
try:
    AbilityDamageIntent(actor_id='a', target_id='b', ability='WIT', amount=1)
    print('FAIL: should have raised')
except IntentParseError:
    print('OK: IntentParseError raised correctly')
"

# Verify resolver module imports cleanly:
python -c "
from aidm.core.ability_damage_resolver import (
    get_effective_score, get_ability_modifier,
    apply_ability_damage, heal_ability_damage,
    expire_ability_damage_regen, apply_ability_damage_events,
)
print('OK')
"
# Expected: OK

# Run new gate:
python -m pytest tests/test_engine_ability_damage_gate.py -v
# AD-01 through AD-10 must pass.

# Regression sweep — rest gate (verifies §4.5 addition does not break rest):
python -m pytest tests/test_engine_rest_gate.py -v --tb=short
# All 12 rest checks must still pass.

# Regression sweep — core engine gates:
python -m pytest tests/test_engine_gate_cp17.py tests/test_engine_gate_cp22.py tests/test_engine_gate_cp23.py tests/test_engine_gate_xp01.py -v --tb=short
# Zero new failures expected.

# Full suite:
python -m pytest tests/ -x --tb=short
# Zero new regressions.
```
