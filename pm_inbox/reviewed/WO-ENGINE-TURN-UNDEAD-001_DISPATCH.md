# WO-ENGINE-TURN-UNDEAD-001

**Status:** DISPATCH
**Gate:** ENGINE-TURN-UNDEAD 10/10
**PHB ref:** p.159-161
**Blocks:** nothing
**Blocked by:** nothing
**Parallel-safe with:** WO-ENGINE-ENERGY-DRAIN-001

---

## §1 Target Lock

**Gap:** Clerics and paladins have no turning mechanism. `CLASS_FEATURES` includes `cleric` and `paladin`; chargen is complete; `EF.CHA_MOD` and `EF.HD_COUNT` both exist. No `TurnUndeadIntent`, no `turn_undead_resolver.py`, no `TURN_UNDEAD_USES` field.

**Affected files (new):**
- `aidm/schemas/entity_fields.py` — add 3 constants
- `aidm/schemas/conditions.py` — add `ConditionType.TURNED`
- `aidm/schemas/intents.py` — add `TurnUndeadIntent`, update `Intent` alias and `parse_intent()`
- `aidm/core/action_economy.py` — add `_try_add()` mapping
- `aidm/core/turn_undead_resolver.py` — new module
- `aidm/core/play_loop.py` — routing block + import

---

## §2 PHB Rule (p.159-161)

**Turn Undead (PHB p.159-161):**

Good clerics (and all paladins) channel positive energy to turn undead. Evil clerics channel negative energy to rebuke undead. Neutral clerics choose at level 1 which energy type they channel.

**Action:** Standard action.

**Uses per day:** 3 + CHA modifier (minimum 1). Paladin uses same pool but turns as cleric level − 2.

**Turning check:** Roll 2d6 + cleric level + CHA modifier. This result is compared against undead HD to determine which undead are affected.

**Turning table (PHB p.160):**
- Undead HD ≤ (cleric level − 4): **destroyed** (good) or **commanded** (evil — deferred)
- Undead HD ≤ turning check result: **turned** (good) or **rebuked** (evil)
- Undead HD = cleric level + 4: turned/rebuked on a result ≥ 21
- Undead HD > cleric level + 4: **immune** (unaffected)

**HP budget (PHB p.160):** Roll 2d6 × 10. This is the total HP of undead that can be turned/destroyed in one use. Select from lowest HD upward, stopping when budget is exhausted.

**Turned effect (PHB p.161):** Turned undead flee for 10 rounds. If unable to flee, they cower. Cowering = HELPLESS condition.

**Range:** 60 ft, line of sight. (Line of sight not enforced in this WO — spatial system not yet live.)

---

## §3 New Entity Fields

Add to `aidm/schemas/entity_fields.py` after the `NONLETHAL_DAMAGE` entry (line 160):

```python
# --- Turn Undead (WO-ENGINE-TURN-UNDEAD-001) ---
TURN_UNDEAD_USES = "turn_undead_uses"       # Int: remaining uses today (3 + CHA_mod, minimum 1)
TURN_UNDEAD_USES_MAX = "turn_undead_uses_max"  # Int: max uses (set at chargen/rest)
IS_UNDEAD = "is_undead"                     # Bool: True if creature is undead type
```

**`EF.IS_UNDEAD`** is required to validate turning targets without string-matching creature type. Set to `True` at chargen for undead monsters (skeleton, zombie, wight, vampire, spectre, etc.) and `False` for all others. Default `False`.

**`EF.TURN_UNDEAD_USES_MAX`** is set at chargen: `max(1, 3 + entity[EF.CHA_MOD])`. Restored to MAX by `rest_resolver.py` on overnight/full_day rest (add one line to the existing rest block).

---

## §4 Implementation Spec

### §4.1 — New ConditionType: TURNED

In `aidm/schemas/conditions.py`, add to the `ConditionType` enum after `PINNED` (line 45):

```python
TURNED = "turned"  # WO-ENGINE-TURN-UNDEAD-001: fleeing from cleric's turning
```

Add factory function `create_turned_condition(source, applied_at_event_id)`:
- `movement_prohibited = False` (turned undead MUST flee — movement is required, not prohibited)
- `actions_prohibited = True` (cannot take offensive actions while turned)
- Notes: "Turned: must flee from cleric, cannot attack"
- Duration is 10 rounds (tracked externally — no auto-expiry in this WO, manual removal only)

### §4.2 — New Intent: TurnUndeadIntent

In `aidm/schemas/intents.py`, insert after `CoupDeGraceIntent` (after line 390), before the `Intent` type alias (line 393):

```python
@dataclass
class TurnUndeadIntent:
    """Intent to turn or rebuke undead. PHB p.159-161.

    Standard action. Uses EF.TURN_UNDEAD_USES. Cleric channels positive
    energy (turn/destroy) or negative energy (rebuke). Paladin turns as
    cleric level - 2.

    WO-ENGINE-TURN-UNDEAD-001
    """

    cleric_id: str
    """Entity ID of the turning cleric or paladin."""

    target_ids: List[str]
    """Entity IDs of undead targets within range. Resolver validates IS_UNDEAD."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "turn_undead",
            "cleric_id": self.cleric_id,
            "target_ids": self.target_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TurnUndeadIntent":
        if data.get("type") != "turn_undead":
            raise IntentParseError(
                f"Expected type 'turn_undead', got '{data.get('type')}'"
            )
        return cls(
            cleric_id=data["cleric_id"],
            target_ids=data.get("target_ids", []),
        )
```

Update `Intent` type alias (line 393) to include `TurnUndeadIntent`.

Update `parse_intent()` dispatch (line 397) to add:
```python
elif intent_type == "turn_undead":
    return TurnUndeadIntent.from_dict(data)
```

### §4.3 — Action Economy

In `aidm/core/action_economy.py`, add to `_build_action_types()` after line 153 (after `ChargeIntent` entry):

```python
_try_add(mapping, "aidm.schemas.intents", "TurnUndeadIntent", "standard")
```

### §4.4 — New Module: `aidm/core/turn_undead_resolver.py`

**Functions:**

**`_get_cleric_level(entity) -> int`**
- `class_levels = entity.get(EF.CLASS_LEVELS, {})`
- Cleric: `class_levels.get("cleric", 0)`
- Paladin: `class_levels.get("paladin", 0) // 2` (paladin turns as cleric level − 2 per PHB p.33, but the formula is `paladin_level // 2` which gives this result)
- Return `max(cleric_level, paladin_effective_level)`. If both are 0, return 0 (not a turning class).

**`_is_evil_cleric(entity) -> bool`**
- `class_features = entity.get("class_features", {})`
- If `class_features.get("channels_negative_energy", False)` → evil. Otherwise → good.
- Paladin always channels positive (good). Cleric determined by chargen flag.

**`_roll_turning_check(cleric_level, cha_mod, rng) -> int`**
- `d1 = rng.randint(1, 6); d2 = rng.randint(1, 6)`
- Return `d1 + d2 + cleric_level + cha_mod`

**`_classify_target(undead_hd, cleric_level, turning_check, is_evil) -> str`**
- If `undead_hd > cleric_level + 4`: return `"immune"`
- If not evil: if `undead_hd <= cleric_level - 4`: return `"destroyed"`; elif `undead_hd <= turning_check`: return `"turned"`; else: return `"unaffected"`
- If evil: if `undead_hd <= cleric_level - 4`: return `"commanded"` (will emit as rebuked per §8); elif `undead_hd <= turning_check`: return `"rebuked"`; else: return `"unaffected"`

**`_compute_affected_targets(targets, cleric_level, turning_check, is_evil, rng) -> list[tuple[str, str, int]]`**
- `hp_budget = (rng.randint(1,6) + rng.randint(1,6)) * 10`
- Sort targets by `target[EF.HD_COUNT]` ascending (lowest HD first)
- For each target: classify; if turned/destroyed/rebuked, subtract `target[EF.HP_MAX]` from budget; stop when budget < 0 or exhausted
- Return list of `(target_id, outcome, hd_count)`

**`resolve_turn_undead(intent, world_state, rng, next_event_id, timestamp) -> list[Event]`**
1. Get cleric entity from `world_state.entities[intent.cleric_id]`
2. Check `entity.get(EF.TURN_UNDEAD_USES, 0) <= 0` → emit `turn_undead_uses_exhausted`, return
3. `cleric_level = _get_cleric_level(entity)` — if 0, emit `intent_validation_failed` (not a cleric/paladin)
4. `cha_mod = entity.get(EF.CHA_MOD, 0)`
5. `is_evil = _is_evil_cleric(entity)`
6. Validate each target_id: `world_state.entities[tid].get(EF.IS_UNDEAD, False)` — skip non-undead silently
7. `turning_check = _roll_turning_check(cleric_level, cha_mod, rng)` → emit `turning_check_rolled`
8. `affected = _compute_affected_targets(valid_targets, cleric_level, turning_check, is_evil, rng)`
9. For each `(target_id, outcome, hd)`: emit appropriate event
10. Emit `turn_undead_use_spent` (cleric_id, uses_remaining = current − 1)
11. Return all events

**`apply_turn_undead_events(events, world_state) -> WorldState`**
- On `turn_undead_use_spent`: decrement `entity[EF.TURN_UNDEAD_USES]` by 1
- On `undead_turned`: apply `create_turned_condition()` to target's CONDITIONS dict
- On `undead_destroyed`: set `entity[EF.DEFEATED] = True`, `entity[EF.HP_CURRENT] = -10`
- On `undead_rebuked`: apply `create_turned_condition()` (rebuked undead also flee — commanded is deferred)
- Return updated WorldState (deepcopy pattern as per rest of codebase)

### §4.5 — play_loop.py Integration

**Import** (add to existing import block): `from aidm.core.turn_undead_resolver import resolve_turn_undead, apply_turn_undead_events`

**Routing block** — insert as new `elif` after the `CoupDeGraceIntent` block (after line 1799), before `elif isinstance(combat_intent, StepMoveIntent)` (line 1801):

```python
elif isinstance(combat_intent, TurnUndeadIntent):
    # WO-ENGINE-TURN-UNDEAD-001: Turn/rebuke undead (PHB p.159-161)
    combat_events = resolve_turn_undead(
        intent=combat_intent,
        world_state=world_state,
        rng=rng,
        next_event_id=current_event_id,
        timestamp=timestamp + 0.1
    )
    events.extend(combat_events)
    current_event_id += len(combat_events)
    world_state = apply_turn_undead_events(combat_events, world_state)
    narration = "turn_undead_resolved"
```

No AoO: turning undead does not provoke AoO (PHB p.159). No concentration break threading: turning is not a spell.

**Rest integration** — in `aidm/core/rest_resolver.py`, add one line to the existing overnight/full_day rest block:

```python
entity[EF.TURN_UNDEAD_USES] = entity.get(EF.TURN_UNDEAD_USES_MAX, 0)
```

---

## §5 New Event Types

| Event type | Key payload fields |
|---|---|
| `turning_check_rolled` | cleric_id, roll_result, cleric_level, cha_mod, is_evil, hp_budget |
| `undead_turned` | cleric_id, target_id, target_hd, duration_rounds=10 |
| `undead_destroyed` | cleric_id, target_id, target_hd |
| `undead_rebuked` | cleric_id, target_id, target_hd, duration_rounds=10 |
| `undead_immune_to_turning` | cleric_id, target_id, target_hd, cleric_level |
| `turn_undead_uses_exhausted` | cleric_id, uses_remaining=0 |
| `turn_undead_use_spent` | cleric_id, uses_remaining (after decrement) |

---

## §6 Regression Risk

**Low.** New module, new intent type. No existing resolver is modified. `rest_resolver.py` gets one additive line (guarded by `entity.get(EF.TURN_UNDEAD_USES_MAX, 0)` — no-ops for entities without the field).

The new `ConditionType.TURNED` is additive to the enum. The existing conditions enum has no exhaustive match/switch patterns that would break.

`EF.IS_UNDEAD` defaults to `False` — all existing PC entities unaffected.

---

## §7 Gate Spec — ENGINE-TURN-UNDEAD 10/10

| ID | Description |
|----|-------------|
| TU-01 | TurnUndeadIntent consumes a standard action slot; budget is blocked if already spent |
| TU-02 | `TURN_UNDEAD_USES == 0` → `turn_undead_uses_exhausted` emitted, no other events |
| TU-03 | Turning check = 2d6 + cleric_level + CHA_mod; `turning_check_rolled` event correct |
| TU-04 | Undead with HD > cleric_level + 4 → `undead_immune_to_turning` |
| TU-05 | Undead with HD ≤ turning check (good cleric) → `undead_turned` + TURNED condition applied |
| TU-06 | Good cleric + undead HD ≤ cleric_level − 4 → `undead_destroyed` + entity_defeated |
| TU-07 | Evil cleric → `undead_rebuked` instead of `undead_turned` for eligible targets |
| TU-08 | Paladin uses `paladin_level // 2` as effective cleric level for turning |
| TU-09 | HP budget (2d6 × 10) limits affected targets, lowest HD processed first, stops at budget |
| TU-10 | `TURN_UNDEAD_USES` decrements by 1 per use; restored to MAX on overnight rest |

---

## §8 What This WO Does NOT Do

- **Command undead (evil cleric):** Evil clerics can command undead to follow them instead of rebuke. Requires persistent `commanded_undead` tracking. Deferred.
- **Line of sight / range enforcement:** No spatial system for 60ft range check. Deferred.
- **Turned = cowering if can't flee:** Movement enforcement not live. TURNED condition is applied; the flee/cower distinction is not enforced.
- **Paladin's Turn Undead feat prerequisite:** Paladin gains turning at level 1; no feat gate needed per PHB p.33. Already handled by `paladin_level // 2`.
- **Domain granted power bonuses:** Some cleric domains grant +2 effective cleric level for turning (Sun domain). Deferred.
- **24-hour expiry of TURNED condition:** Duration tracking is metadata only. TURNED condition persists until manually removed. Deferred to duration tracker integration.

---

## §9 Preflight

- [ ] `EF.TURN_UNDEAD_USES`, `EF.TURN_UNDEAD_USES_MAX`, `EF.IS_UNDEAD` added to `entity_fields.py` before use anywhere else
- [ ] `ConditionType.TURNED` added to enum; `create_turned_condition()` factory added
- [ ] `TurnUndeadIntent` added to `intents.py`; `Intent` union alias updated; `parse_intent()` updated
- [ ] `_try_add(..., "TurnUndeadIntent", "standard")` added to `action_economy.py`
- [ ] `turn_undead_resolver.py` created with all 5 functions
- [ ] `play_loop.py` routing block added after `CoupDeGraceIntent` block (before `StepMoveIntent`)
- [ ] `rest_resolver.py` restores `TURN_UNDEAD_USES` to `TURN_UNDEAD_USES_MAX`
- [ ] Gate tests TU-01 through TU-10 written in `tests/test_engine_turn_undead_gate.py`
- [ ] Full suite regression run — zero new failures expected
