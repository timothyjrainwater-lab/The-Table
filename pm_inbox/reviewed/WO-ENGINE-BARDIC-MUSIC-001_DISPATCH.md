# WO-ENGINE-BARDIC-MUSIC-001 — Bardic Music / Inspire Courage Runtime

**Type:** Builder WO
**Gate:** ENGINE-BARDIC-MUSIC
**Tests:** 10 (BM-01 through BM-10)
**Depends on:** Nothing
**Blocks:** Nothing
**Priority:** MEDIUM — class feature with no runtime presence; Bard is unplayable without it

---

## 1. Target Lock

Bardic Music / Inspire Courage (PHB p.29) is the Bard's primary combat support class feature. At chargen, Bards receive `"bardic_music"` and `"inspire_courage_1"` (scaling) as class feature strings. At runtime, there is no `BardicMusicIntent`, no resolver, no EF fields tracking uses or active buff, and no attack/damage bonus logic. A Bard PC can be built but cannot perform.

**PHB spec (pp.29–30) — Inspire Courage only (other performances deferred):**
- Standard action to begin. Effect persists as long as the bard performs (concentration, move action each turn to maintain) plus 5 rounds after.
- Allies (including the bard) within 60 feet who can hear: +1 morale bonus to attack rolls, weapon damage rolls, and saves vs. fear/charm. Scales: +2 at Bard 8, +3 at Bard 14, +4 at Bard 20.
- Uses per day = Bard level (minimum 1).
- Deferred performances: Countersong, Fascinate, Inspire Competence, Inspire Greatness, Song of Freedom, Inspire Heroics, Mass Suggestion.

**Deliver:** `BardicMusicIntent`, `aidm/core/bardic_music_resolver.py`, EF constants, and gate ENGINE-BARDIC-MUSIC 10/10.

**Scope:** Inspire Courage only. All other performances are deferred — no stubs, no TODOs in code, just out of scope.

---

## 2. Binary Decisions

| # | Question | Answer |
|---|----------|--------|
| BD-01 | How is Inspire Courage activated? | New intent: `BardicMusicIntent(actor_id: str, performance: Literal["inspire_courage"])`. Performance field exists for future extensibility — only "inspire_courage" is accepted in v1. |
| BD-02 | How are bardic music uses tracked? | New EF field `EF.BARDIC_MUSIC_USES_REMAINING` (int). Set from Bard class level (1/day per level). Decremented on each activation. |
| BD-03 | How is the active buff tracked? | New EF field `EF.INSPIRE_COURAGE_ACTIVE` (bool) on each affected ally. New EF field `EF.INSPIRE_COURAGE_BONUS` (int) on each ally — the bonus value (+1/+2/+3/+4). New EF field `EF.INSPIRE_COURAGE_ROUNDS_REMAINING` (int) on the bard — rounds of performance remaining. |
| BD-04 | Who is affected? | All allies within 60 feet who are not the bard, plus the bard themselves. "Allies" = same faction/team as the bard. "Within 60 feet" = AI/DM assertion via `ally_ids` list on the intent. Builder does not implement distance calculation — the caller provides the ally list. |
| BD-05 | Bonus value: how is it determined? | Parse Bard class level. Level 1-7: +1. Level 8-13: +2. Level 14-19: +3. Level 20: +4. |
| BD-06 | How is "maintaining concentration" handled? | Out of scope for v1. The bard uses a move action each turn to maintain — no action economy enforcement. The buff is active for a fixed `5 + bard_level / 7 * 2` rounds (generous approximation; exact duration enforcement deferred to DURATION-TRACKER integration). For v1: buff lasts 8 rounds flat after activation. Log as FINDING-BARDIC-DURATION-001 LOW. |
| BD-07 | How does the bonus apply to attacks? | Stored in `EF.INSPIRE_COURAGE_BONUS` on each ally entity. `attack_resolver.py` must check this field and add it to the attack roll and damage roll as a morale bonus (morale bonuses don't stack — use `max()` if multiple bards). |
| BD-08 | How does the bonus apply to saves vs. fear/charm? | `save_resolver.py` must check `EF.INSPIRE_COURAGE_BONUS` when resolve type is "fear" or "charm". Same approach as BD-07. |
| BD-09 | Does Inspire Courage stack with other Inspire Courage buffs? | No. Morale bonuses do not stack (PHB p.180). If ally already has a morale bonus, take the higher value. |
| BD-10 | RNG? | None. Inspire Courage has no dice. |

---

## 3. Contract Spec

### 3.1 New EF constants (entity_fields.py)

```python
BARDIC_MUSIC_USES_REMAINING = "bardic_music_uses_remaining"  # int: uses remaining today
INSPIRE_COURAGE_ACTIVE = "inspire_courage_active"            # bool: buff active
INSPIRE_COURAGE_BONUS = "inspire_courage_bonus"              # int: morale bonus value
INSPIRE_COURAGE_ROUNDS_REMAINING = "inspire_courage_rounds_remaining"  # int: rounds left
```

### 3.2 New intent: `BardicMusicIntent` (intents.py)

```python
@dataclass
class BardicMusicIntent:
    """Intent to use Bardic Music — Inspire Courage (PHB p.29)."""
    type: Literal["bardic_music"] = "bardic_music"
    actor_id: str = ""
    performance: Literal["inspire_courage"] = "inspire_courage"
    ally_ids: List[str] = field(default_factory=list)
    """IDs of allies within hearing range (60ft). DM/AI asserts this list."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "actor_id": self.actor_id,
            "performance": self.performance,
            "ally_ids": self.ally_ids,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BardicMusicIntent":
        if data.get("type") != "bardic_music":
            raise IntentParseError(f"Expected type 'bardic_music', got '{data.get('type')}'")
        performance = data.get("performance", "inspire_courage")
        if performance != "inspire_courage":
            raise IntentParseError(f"Unsupported performance type: {performance}")
        return cls(
            actor_id=data["actor_id"],
            performance=performance,
            ally_ids=data.get("ally_ids", []),
        )
```

Add to `Intent` union and `parse_intent()`.

### 3.3 New module: `aidm/core/bardic_music_resolver.py`

```python
def validate_bardic_music(actor: dict, world_state) -> Optional[str]:
    """Returns error reason or None.
    Checks: Bard class feature present, EF.BARDIC_MUSIC_USES_REMAINING > 0.
    """

def get_inspire_courage_bonus(bard_class_level: int) -> int:
    """Return the morale bonus for the given Bard class level.
    Level 1-7: +1. Level 8-13: +2. Level 14-19: +3. Level 20: +4.
    """

def resolve_bardic_music(
    intent: BardicMusicIntent,
    world_state: WorldState,
    next_event_id: int,
    timestamp: float,
) -> Tuple[List[Event], WorldState]:
    """
    1. validate_bardic_music() — fail-close
    2. Decrement EF.BARDIC_MUSIC_USES_REMAINING
    3. Compute bonus = get_inspire_courage_bonus(bard_level)
    4. For bard + each ally_id:
       - Set EF.INSPIRE_COURAGE_ACTIVE = True
       - Set EF.INSPIRE_COURAGE_BONUS = max(existing, new bonus)
       - Set EF.INSPIRE_COURAGE_ROUNDS_REMAINING = 8 (v1 fixed duration)
    5. Emit inspire_courage_start event
    6. Return events + updated world_state
    """
```

### 3.4 Events

| Event | Payload |
|-------|---------|
| `inspire_courage_start` | `actor_id`, `affected_ids: list`, `bonus: int`, `rounds: int`, `uses_remaining: int` |
| `inspire_courage_end` | `actor_id` (bard), `affected_ids: list` |

---

## 4. Implementation Plan

1. **Add EF constants** to `aidm/schemas/entity_fields.py`.

2. **Add `BardicMusicIntent`** to `aidm/schemas/intents.py`. Add to `Intent` union and `parse_intent()`.

3. **Create `aidm/core/bardic_music_resolver.py`** with `validate_bardic_music()`, `get_inspire_courage_bonus()`, `resolve_bardic_music()`.

4. **Modify `play_loop.py`**: wire `BardicMusicIntent` → `resolve_bardic_music()`. At turn end: decrement `INSPIRE_COURAGE_ROUNDS_REMAINING` for all affected entities; if 0, clear buff.

5. **Modify `attack_resolver.py`**: in the modifier aggregation, add: if entity has `EF.INSPIRE_COURAGE_ACTIVE = True`, add `EF.INSPIRE_COURAGE_BONUS` to attack and damage rolls as a morale bonus.

6. **Modify `save_resolver.py`**: if save type is fear or charm and entity has `EF.INSPIRE_COURAGE_ACTIVE`, add `EF.INSPIRE_COURAGE_BONUS` to the save roll.

7. **Create `tests/test_engine_gate_bardic_music.py`** — 10 gate tests.

8. **Preflight:** 10/10 pass. Full suite: 0 new failures.

---

## 5. Gate Tests (ENGINE-BARDIC-MUSIC 10/10)

| ID | Description |
|----|-------------|
| BM-01 | Inspire Courage activates: `inspire_courage_start` event emitted, `EF.INSPIRE_COURAGE_ACTIVE = True` on bard and all `ally_ids` |
| BM-02 | Bonus value: level 1 Bard → +1; level 8 Bard → +2; level 14 Bard → +3; level 20 Bard → +4 |
| BM-03 | `EF.BARDIC_MUSIC_USES_REMAINING` decremented by 1 after activation |
| BM-04 | Affected ally's attack roll includes +1 (or higher) morale bonus |
| BM-05 | Affected ally's fear save includes morale bonus |
| BM-06 | No stacking: ally already at +2 morale bonus — second Bard's +1 Inspire Courage does not reduce bonus (take max) |
| BM-07 | No uses remaining: `intent_validation_failed`, `reason: no_bardic_music_uses` |
| BM-08 | Entity without Bard class feature: `intent_validation_failed`, `reason: not_a_bard` |
| BM-09 | Buff expires: after 8 rounds, `EF.INSPIRE_COURAGE_ACTIVE = False`, bonus cleared, `inspire_courage_end` event emitted |
| BM-10 | Unsupported performance type: `intent_validation_failed`, `reason: unsupported_performance` |

---

## 6. Delivery Footer

**Files to create:**
```
aidm/core/bardic_music_resolver.py
tests/test_engine_gate_bardic_music.py
```

**Files to modify:**
```
aidm/schemas/entity_fields.py    ← add 4 new EF constants
aidm/schemas/intents.py          ← add BardicMusicIntent, wire into parse_intent()
aidm/core/play_loop.py           ← wire BardicMusicIntent + turn-end buff tick
aidm/core/attack_resolver.py     ← add INSPIRE_COURAGE_BONUS to modifier aggregation
aidm/core/save_resolver.py       ← add INSPIRE_COURAGE_BONUS for fear/charm saves
```

**Commit requirement:**
```
feat: WO-ENGINE-BARDIC-MUSIC-001 — Bardic Music Inspire Courage runtime — Gate ENGINE-BARDIC-MUSIC 10/10
```

**Preflight:**
```
pytest tests/test_engine_gate_bardic_music.py -v
```
10/10 must pass. Full suite: 0 new failures.

---

## 7. Integration Seams

- `attack_resolver.py` morale bonus aggregation: builder must confirm how the modifier dict is accumulated and where to add the EF field check
- `save_resolver.py` save type: builder must confirm how save type (fear, charm) is passed into the resolver and where to inject the bonus
- Turn-end buff tick: confirm it fires after all actions for the turn and uses the same decrement pattern as RAGE_ROUNDS_REMAINING (if Rage WO is accepted first)

---

## 8. Assumptions to Validate

- Bard class level is accessible from entity data (not just total character level) for multiclass support — builder confirms
- `save_resolver.py` passes save type (fear vs charm vs other) in a way the resolver can check — builder confirms before injecting the bonus

---

## 9. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
