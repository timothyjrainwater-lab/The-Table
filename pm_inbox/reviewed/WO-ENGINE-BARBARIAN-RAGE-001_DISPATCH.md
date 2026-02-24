# WO-ENGINE-BARBARIAN-RAGE-001 — Barbarian Rage Runtime

**Type:** Builder WO
**Gate:** ENGINE-BARBARIAN-RAGE
**Tests:** 10 (BR-01 through BR-10)
**Depends on:** Nothing
**Blocks:** Nothing
**Priority:** MEDIUM — class feature with no runtime presence; Barbarian is unplayable without it

---

## 1. Target Lock

Barbarian Rage (PHB p.25) is the Barbarian's core class feature. At chargen, Barbarians receive `"rage_1_per_day"` through `"rage_6_per_day"` strings in their class features list. At runtime, there is no `RageIntent`, no resolver, no EF fields for `RAGE_ACTIVE` or `RAGE_USES_REMAINING`, and no stat modification logic. A Barbarian PC can be built but cannot rage during play.

**PHB spec (p.25):**
- Standard action to activate. Lasts `3 + Constitution modifier` rounds.
- While raging: +4 Str, +4 Con, +2 Will saves, −2 AC.
- Cannot use skills requiring patience (e.g., no spellcasting, no Use Magic Device, no Disable Device).
- At end of rage: fatigue for the remainder of the encounter (−2 Str, −2 Dex, cannot rage again until rest).
- Uses per day: 1/day (Barbarian 1), scaling to 6/day (Barbarian 20).

**Deliver:** `RageIntent`, `aidm/core/rage_resolver.py`, EF constants, and gate ENGINE-BARBARIAN-RAGE 10/10.

---

## 2. Binary Decisions

| # | Question | Answer |
|---|----------|--------|
| BD-01 | How is Rage activated? | New intent: `RageIntent(actor_id: str)`. Standard action. Wired into `play_loop.py`. |
| BD-02 | How are rage uses tracked? | New EF field `EF.RAGE_USES_REMAINING` (int). Set at combat start from the Barbarian's class feature count (parse `"rage_N_per_day"` string). Decremented on each activation. |
| BD-03 | How is "currently raging" tracked? | New EF field `EF.RAGE_ACTIVE` (bool). New EF field `EF.RAGE_ROUNDS_REMAINING` (int). Decremented at end of each of the barbarian's turns. |
| BD-04 | How are the stat bonuses applied? | Added to `EF.TEMPORARY_MODIFIERS` dict (same pattern as fight_defensively, charge). Keys: `"rage_str_bonus": 4`, `"rage_con_bonus": 4`, `"rage_will_bonus": 2`, `"rage_ac_penalty": -2`. The attack resolver and save resolver must check these keys. |
| BD-05 | When does Rage end? | After `3 + CON modifier` rounds (calculated at activation using the base CON modifier, not the rage-enhanced one). Also ends if Barbarian becomes unconscious. |
| BD-06 | Fatigue after Rage? | Yes. Set `EF.FATIGUED = True` at rage end. Fatigued: −2 Str, −2 Dex, cannot run or charge, cannot rage again until rest. Add `EF.FATIGUED` to entity_fields. The attack_resolver already checks temporary modifiers — add `"fatigued_str_penalty": -2` and `"fatigued_dex_penalty": -2` to TEMPORARY_MODIFIERS at rage-end. |
| BD-07 | Can a Fatigued Barbarian rage again? | No. `validate_rage()` checks `EF.FATIGUED` — if True, emit `intent_validation_failed` with `reason: "already_fatigued"`. |
| BD-08 | Skill restrictions during Rage? | Out of scope for v1. No skill system integration yet. Log as FINDING-RAGE-SKILL-001 LOW. |
| BD-09 | Is rage available outside combat? | RageIntent can fire at any time (not restricted to active_combat). RAGE_USES_REMAINING must be initialized from class features at combat start AND persisted across encounters in entity state. |
| BD-10 | RNG? | Rage activation has no RNG. Duration is deterministic (3 + CON mod). |

---

## 3. Contract Spec

### 3.1 New EF constants (entity_fields.py)

```python
RAGE_ACTIVE = "rage_active"               # bool: True while raging
RAGE_USES_REMAINING = "rage_uses_remaining"  # int: uses left this day
RAGE_ROUNDS_REMAINING = "rage_rounds_remaining"  # int: rounds left in current rage
FATIGUED = "fatigued"                     # bool: True after rage ends (until rest)
```

### 3.2 New intent: `RageIntent` (intents.py)

```python
@dataclass
class RageIntent:
    """Intent to activate Barbarian Rage (PHB p.25)."""
    type: Literal["rage"] = "rage"
    actor_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"type": self.type, "actor_id": self.actor_id}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RageIntent":
        if data.get("type") != "rage":
            raise IntentParseError(f"Expected type 'rage', got '{data.get('type')}'")
        return cls(actor_id=data["actor_id"])
```

Add to `Intent` type alias and `parse_intent()` dispatch.

### 3.3 New module: `aidm/core/rage_resolver.py`

```python
def validate_rage(actor: dict, world_state) -> Optional[str]:
    """Returns error reason string or None."""
    # Fail if: no rage class feature, EF.RAGE_ACTIVE already True,
    # EF.RAGE_USES_REMAINING <= 0, EF.FATIGUED == True

def activate_rage(actor_id: str, world_state) -> Tuple[List[Event], WorldState]:
    """
    Apply rage bonuses to TEMPORARY_MODIFIERS.
    Set EF.RAGE_ACTIVE = True.
    Set EF.RAGE_ROUNDS_REMAINING = 3 + base_con_modifier.
    Decrement EF.RAGE_USES_REMAINING.
    Emit rage_start event.
    """

def tick_rage(actor_id: str, world_state) -> Tuple[List[Event], WorldState]:
    """
    Called at end of each of the barbarian's turns while raging.
    Decrement EF.RAGE_ROUNDS_REMAINING.
    If 0: call end_rage().
    """

def end_rage(actor_id: str, world_state) -> Tuple[List[Event], WorldState]:
    """
    Remove rage modifiers from TEMPORARY_MODIFIERS.
    Set EF.RAGE_ACTIVE = False.
    Set EF.FATIGUED = True.
    Add fatigued_str_penalty and fatigued_dex_penalty to TEMPORARY_MODIFIERS.
    Emit rage_end event.
    """
```

### 3.4 Events

| Event | Payload |
|-------|---------|
| `rage_start` | `actor_id`, `rage_rounds_total`, `rage_uses_remaining` (after decrement), `str_bonus: 4`, `con_bonus: 4`, `will_bonus: 2`, `ac_penalty: -2` |
| `rage_end` | `actor_id`, `reason: "expired" | "unconscious"`, `fatigued: true` |

### 3.5 Wiring in `play_loop.py`

- `RageIntent` → calls `validate_rage()` → calls `activate_rage()`
- At turn end: if `EF.RAGE_ACTIVE`: call `tick_rage()`

---

## 4. Implementation Plan

1. **Add EF constants** to `aidm/schemas/entity_fields.py`: `RAGE_ACTIVE`, `RAGE_USES_REMAINING`, `RAGE_ROUNDS_REMAINING`, `FATIGUED`.

2. **Add `RageIntent`** to `aidm/schemas/intents.py`. Add to `Intent` union type and `parse_intent()`.

3. **Create `aidm/core/rage_resolver.py`** with four functions: `validate_rage`, `activate_rage`, `tick_rage`, `end_rage`.

4. **Modify `play_loop.py`**:
   - Import `RageIntent` and rage resolver functions
   - Wire `RageIntent` → `validate_rage` → `activate_rage`
   - At turn-end: check `EF.RAGE_ACTIVE` → call `tick_rage()`

5. **Confirm `TEMPORARY_MODIFIERS` pattern** in `attack_resolver.py`/`save_resolver.py` — verify that `rage_str_bonus`, `rage_will_bonus`, `rage_ac_penalty`, `fatigued_str_penalty`, `fatigued_dex_penalty` keys are picked up by the existing modifier aggregation logic (or add them).

6. **Create `tests/test_engine_gate_barbarian_rage.py`** — 10 gate tests.

7. **Preflight:** 10/10 gate pass. Full suite 0 new failures.

---

## 5. Gate Tests (ENGINE-BARBARIAN-RAGE 10/10)

| ID | Description |
|----|-------------|
| BR-01 | Rage activates: `rage_start` event emitted, `EF.RAGE_ACTIVE = True`, `EF.RAGE_USES_REMAINING` decremented by 1 |
| BR-02 | Rage bonuses applied: attacker with rage has +4 Str (attack bonus increased), −2 AC in TEMPORARY_MODIFIERS |
| BR-03 | Rage duration: `EF.RAGE_ROUNDS_REMAINING` decremented each turn; rage ends when it reaches 0 |
| BR-04 | Rage end: `rage_end` event emitted, RAGE_ACTIVE cleared, FATIGUED set True, Str/Dex penalties applied |
| BR-05 | Cannot rage while already raging: `intent_validation_failed`, `reason: already_raging` |
| BR-06 | Cannot rage while fatigued: `intent_validation_failed`, `reason: already_fatigued` |
| BR-07 | No uses remaining: `intent_validation_failed`, `reason: no_rage_uses` |
| BR-08 | Entity without Barbarian class feature: `intent_validation_failed`, `reason: not_a_barbarian` |
| BR-09 | Rage duration = 3 + CON modifier (base CON, not rage-enhanced CON) |
| BR-10 | Rage round tick is deterministic — same result across 10 replays |

---

## 6. Delivery Footer

**Files to create:**
```
aidm/core/rage_resolver.py
tests/test_engine_gate_barbarian_rage.py
```

**Files to modify:**
```
aidm/schemas/entity_fields.py    ← add RAGE_ACTIVE, RAGE_USES_REMAINING, RAGE_ROUNDS_REMAINING, FATIGUED
aidm/schemas/intents.py          ← add RageIntent, wire into parse_intent()
aidm/core/play_loop.py           ← wire RageIntent + turn-end rage tick
```

**Commit requirement:**
```
feat: WO-ENGINE-BARBARIAN-RAGE-001 — Barbarian Rage runtime (activate/tick/end/fatigue) — Gate ENGINE-BARBARIAN-RAGE 10/10
```

**Preflight:**
```
pytest tests/test_engine_gate_barbarian_rage.py -v
```
10/10 must pass. Full suite: 0 new failures.

---

## 7. Integration Seams

- `FATIGUED` is a new EF constant — builder must confirm no existing code uses a string `"fatigued"` without the constant (grep for `"fatigued"` before adding)
- `TEMPORARY_MODIFIERS` key format: builder must verify the existing modifier aggregation in `attack_resolver.py` and `save_resolver.py` uses a pattern that will pick up new keys, or document exactly which keys need to be added to the aggregation logic
- `tick_rage()` is called at turn end — builder must find the exact turn-end hook in `play_loop.py` and confirm it fires after all actions for the turn are resolved

---

## 8. Assumptions to Validate

- `TEMPORARY_MODIFIERS` aggregation in `attack_resolver.py` and `save_resolver.py` is key-based and will pick up new keys without code changes — builder confirms
- `EF.CON` (or equivalent) is accessible from entity dict to compute rage duration — builder confirms the field name
- No existing EF field `"fatigued"` already exists under a different constant name — builder greps before adding

---

## 9. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
