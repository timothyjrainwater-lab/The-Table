# WO-ENGINE-SMITE-EVIL-001 — Paladin Smite Evil Runtime

**Type:** Builder WO
**Gate:** ENGINE-SMITE-EVIL
**Tests:** 8 (SE-01 through SE-08)
**Depends on:** Nothing
**Blocks:** Nothing
**Priority:** MEDIUM — class feature with no runtime presence; Paladin is unplayable without it

---

## 1. Target Lock

Paladin Smite Evil (PHB p.44) is the Paladin's signature offensive class feature. At chargen, Paladins receive `"smite_evil_N_per_day"` strings in their class features list. At runtime, there is no `SmiteEvilIntent`, no resolver, no EF tracking of smite uses, and no damage/attack bonus logic. A Paladin PC can be built but cannot smite.

**PHB spec (p.44):**
- Once per day per level (up to Paladin level / 5, minimum 1). E.g., level 5 = 2/day.
- Declare before attack roll on an evil-aligned target.
- Attack bonus: +CHA modifier (added to the attack roll).
- Damage bonus: +Paladin class level (added to damage if the attack hits).
- If used against a non-evil target: attack is wasted, use consumed.
- No action cost beyond the attack action it modifies.

**Deliver:** `SmiteEvilIntent`, `aidm/core/smite_evil_resolver.py`, EF constants, and gate ENGINE-SMITE-EVIL 8/8.

---

## 2. Binary Decisions

| # | Question | Answer |
|---|----------|--------|
| BD-01 | How is Smite Evil declared? | New intent: `SmiteEvilIntent(actor_id: str, target_id: str, weapon: dict)`. The weapon dict is identical to `AttackIntent.weapon` — the smite modifies the underlying attack. |
| BD-02 | How are smite uses tracked? | New EF field `EF.SMITE_USES_REMAINING` (int). Initialized from `"smite_evil_N_per_day"` class feature at entity creation / rest. Decremented on each use. |
| BD-03 | How are the bonuses applied? | `SmiteEvilResolver` computes `cha_mod` from the actor's CHA score, and `paladin_level` from the actor's class levels. These are passed to `attack_resolver.resolve_attack()` as additional modifiers via the TEMPORARY_MODIFIERS dict keys `"smite_attack_bonus"` and `"smite_damage_bonus"`. |
| BD-04 | Target alignment check: who asserts the target is evil? | The DM/AI asserts it. `SmiteEvilIntent` carries a `target_is_evil: bool` field. If False: smite attack bonus and damage bonus are NOT applied, use IS consumed, event emitted with `reason: target_not_evil`. Builder does not implement alignment sensing — that is an Oracle-side concern. |
| BD-05 | Does the Smite resolve a full attack? | No. Smite Evil affects a single attack — not a full attack sequence. It is one attack roll. |
| BD-06 | What events are emitted? | `smite_declared` before the attack, with actor_id, target_id, attack_bonus, damage_bonus. Then the standard `attack_roll` event from the underlying attack resolver. |
| BD-07 | RNG? | Smite itself has no RNG. The underlying attack roll consumes d20 + damage dice normally. |
| BD-08 | Does Smite Evil interact with Cleave? | Yes — if the smite kills the target, Cleave rules apply normally (subject to CLEAVE-WIRE-001 being accepted). No special case needed here. |

---

## 3. Contract Spec

### 3.1 New EF constants (entity_fields.py)

```python
SMITE_USES_REMAINING = "smite_uses_remaining"  # int: smite uses left today
```

### 3.2 New intent: `SmiteEvilIntent` (intents.py)

```python
@dataclass
class SmiteEvilIntent:
    """Intent to use Paladin Smite Evil (PHB p.44)."""
    type: Literal["smite_evil"] = "smite_evil"
    actor_id: str = ""
    target_id: str = ""
    weapon: dict = field(default_factory=dict)
    target_is_evil: bool = True
    """DM/AI assertion. False = use consumed, bonuses not applied."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "actor_id": self.actor_id,
            "target_id": self.target_id,
            "weapon": self.weapon,
            "target_is_evil": self.target_is_evil,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SmiteEvilIntent":
        if data.get("type") != "smite_evil":
            raise IntentParseError(f"Expected type 'smite_evil', got '{data.get('type')}'")
        return cls(
            actor_id=data["actor_id"],
            target_id=data["target_id"],
            weapon=data.get("weapon", {}),
            target_is_evil=data.get("target_is_evil", True),
        )
```

Add to `Intent` type alias and `parse_intent()` dispatch.

### 3.3 New module: `aidm/core/smite_evil_resolver.py`

```python
def validate_smite(actor: dict, world_state) -> Optional[str]:
    """Returns error reason or None.
    Checks: paladin class feature present, EF.SMITE_USES_REMAINING > 0.
    """

def resolve_smite_evil(
    intent: SmiteEvilIntent,
    world_state: WorldState,
    rng: RNGProvider,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """
    1. validate_smite() — fail-close
    2. Decrement EF.SMITE_USES_REMAINING
    3. Compute attack_bonus = CHA modifier
    4. Compute damage_bonus = paladin class level
    5. If target_is_evil: inject smite_attack_bonus and smite_damage_bonus into TEMPORARY_MODIFIERS
    6. Emit smite_declared event
    7. Call attack_resolver.resolve_attack() with existing weapon dict
    8. Clear smite TEMPORARY_MODIFIERS after attack resolves
    9. Return events + updated world_state
    """
```

### 3.4 Events

| Event | Payload |
|-------|---------|
| `smite_declared` | `actor_id`, `target_id`, `target_is_evil: bool`, `attack_bonus: int`, `damage_bonus: int`, `smite_uses_remaining` (after decrement) |

---

## 4. Implementation Plan

1. **Add EF constant** `SMITE_USES_REMAINING` to `aidm/schemas/entity_fields.py`.

2. **Add `SmiteEvilIntent`** to `aidm/schemas/intents.py`. Add to `Intent` union and `parse_intent()`.

3. **Create `aidm/core/smite_evil_resolver.py`** with `validate_smite()` and `resolve_smite_evil()`.

4. **Modify `play_loop.py`**: import `SmiteEvilIntent` and wire to `resolve_smite_evil()`.

5. **Confirm TEMPORARY_MODIFIERS injection/cleanup pattern** — smite modifiers must be set before the attack resolver reads them and cleared immediately after (same call frame). Builder verifies the resolver reads TEMPORARY_MODIFIERS at roll time.

6. **Create `tests/test_engine_gate_smite_evil.py`** — 8 gate tests.

7. **Preflight:** 8/8 pass. Full suite: 0 new failures.

---

## 5. Gate Tests (ENGINE-SMITE-EVIL 8/8)

| ID | Description |
|----|-------------|
| SE-01 | Smite against evil target: attack roll includes +CHA modifier, damage includes +paladin level on hit |
| SE-02 | `smite_declared` event emitted with correct `attack_bonus` and `damage_bonus` values |
| SE-03 | `EF.SMITE_USES_REMAINING` decremented by 1 after use |
| SE-04 | Smite against non-evil target (`target_is_evil=False`): use consumed, bonuses NOT applied, `smite_declared` emitted with `target_is_evil: false` |
| SE-05 | No uses remaining: `intent_validation_failed`, `reason: no_smite_uses` |
| SE-06 | Entity without Paladin class feature: `intent_validation_failed`, `reason: not_a_paladin` |
| SE-07 | Smite damage bonus = paladin class level (not total character level for multiclass) |
| SE-08 | Smite attack bonus = CHA modifier (not total CHA score) |

---

## 6. Delivery Footer

**Files to create:**
```
aidm/core/smite_evil_resolver.py
tests/test_engine_gate_smite_evil.py
```

**Files to modify:**
```
aidm/schemas/entity_fields.py    ← add SMITE_USES_REMAINING
aidm/schemas/intents.py          ← add SmiteEvilIntent, wire into parse_intent()
aidm/core/play_loop.py           ← wire SmiteEvilIntent
```

**Commit requirement:**
```
feat: WO-ENGINE-SMITE-EVIL-001 — Paladin Smite Evil runtime — Gate ENGINE-SMITE-EVIL 8/8
```

**Preflight:**
```
pytest tests/test_engine_gate_smite_evil.py -v
```
8/8 must pass. Full suite: 0 new failures.

---

## 7. Integration Seams

- TEMPORARY_MODIFIERS inject/clear pattern: builder must confirm the exact mechanism by which smite bonuses are applied before the attack roll and cleared after — this must not persist across multiple attacks
- Paladin level extraction: builder must confirm how to extract class-specific level from entity data (e.g., `EF.CLASS_LEVELS` dict with class name keys)
- CHA modifier calculation: confirm which EF field holds the CHA score and that modifier = floor((cha - 10) / 2) is not already a named helper

---

## 8. Assumptions to Validate

- `EF.CLASS_LEVELS` (or equivalent) provides per-class level breakdown for multiclass characters — builder confirms field name and data structure
- `EF.CHA` (or equivalent) provides raw Charisma score — builder confirms
- TEMPORARY_MODIFIERS keys `smite_attack_bonus` and `smite_damage_bonus` will be picked up by the existing modifier aggregation in `attack_resolver.py` — builder verifies the aggregation loop or documents what needs to be added

---

## 9. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
