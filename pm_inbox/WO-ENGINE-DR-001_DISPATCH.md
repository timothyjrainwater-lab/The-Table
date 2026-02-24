# WO-ENGINE-DR-001 — Damage Reduction Enforcement

**Issued:** 2026-02-24
**Authority:** PM Slate — Thunder approval
**Gate:** ENGINE-DR (new gate, defined below)
**Parallel-safe:** Yes — touches only `aidm/core/damage_reduction.py` (new helper and event logic), `aidm/core/attack_resolver.py` (damage-application section), and `aidm/core/full_attack_resolver.py` (damage-application section). Does not overlap with WO-ENGINE-DEATH-DYING-001 (which modifies defeat detection, not damage calculation), WO-ENGINE-CONCENTRATION-FIX (which modifies `play_loop.py` spell path only), or WO-ENGINE-NONLETHAL-001 (which is a new field and intent, no touch on existing lethal path).

---

## §1 Target Lock

### What is broken

`EF.DAMAGE_REDUCTIONS` exists on entities (introduced in WO-048, constant at `aidm/schemas/entity_fields.py` line 121). The `damage_reduction.py` module (`aidm/core/damage_reduction.py`) has `get_applicable_dr()` and `apply_dr_to_damage()` wired in both attack resolvers. However, two things are missing:

1. The `hp_changed` event payload does not carry a `dr_absorbed` field. Downstream consumers (UI, narrator) cannot distinguish "8 damage dealt" from "8 damage attempted but 5 absorbed by DR".
2. No `damage_reduced` event is emitted when DR absorbs damage. The narrator has no signal to say "the troll's thick hide shrugs off part of your blow."
3. If DR reduces damage to 0, `hp_changed` is still emitted with `delta: 0`, which is semantically wrong — no HP change occurred.
4. The `get_applicable_dr()` call in `attack_resolver.py` (line 424) passes only `intent.weapon.damage_type` and no weapon magic/material metadata, so all weapons are treated as non-magic steel regardless of their actual properties. The weapon bypass logic in `damage_reduction.py` is correct but the call sites do not supply the bypass parameters.

### What "done" means

- `hp_changed` events include `"dr_absorbed": int` (0 when no DR applied).
- A `damage_reduced` event is emitted whenever `dr_absorbed > 0`, before `hp_changed`.
- When DR reduces final damage to exactly 0, no `hp_changed` event is emitted (damage was fully negated).
- The `get_applicable_dr()` call sites pass weapon magic/material flags extracted from the `Weapon` object's tags or the entity's `EF.WEAPON` dict.
- Gate ENGINE-DR 10/10 passes.

---

## §2 PHB Rule Reference

**PHB 3.5e p.291 — Damage Reduction:**

> Some magic creatures have the supernatural ability to instantly heal damage from weapons or ignore blows altogether as though they were invulnerable. The numerical part of a creature's damage reduction is the amount of hit points each hit ignores. If a creature has damage reduction 10/magic, a non-magical weapon deals only 5 points of damage per hit (instead of 15). An attack that deals less damage than the damage reduction does not harm the creature.
>
> Whenever damage reduction completely negates the damage from an attack, it also negates most special effects that accompany the attack. A creature's damage reduction is overcome by certain materials.

**Key rules encoded:**

| Rule | Implementation |
|------|---------------|
| DR reduces damage to minimum 0 | `max(0, damage - dr_amount)` |
| Multiple DR: use highest applicable (no stacking) | `get_applicable_dr()` already does this |
| DR/— cannot be bypassed by any weapon | `bypass == "-"` returns False in `_weapon_bypasses_dr()` |
| Magic weapons bypass DR/magic | `is_magic_weapon or enhancement >= 1` |
| Natural attacks are not magic | `weapon=None` or `weapon_type="natural"` → not magic |
| DR does not apply to energy damage | `_ENERGY_DAMAGE_TYPES` set in `damage_reduction.py` |

---

## §3 New Entity Fields

No new EF constants are required. `EF.DAMAGE_REDUCTIONS` already exists (line 121 in `entity_fields.py`):

```python
# --- Damage Reduction (WO-048) ---
DAMAGE_REDUCTIONS = "damage_reductions"  # List of DR dicts, e.g., [{"amount": 10, "bypass": "magic"}]
```

The `Weapon` dataclass in `aidm/schemas/attack.py` does not currently carry magic/material fields. This WO does NOT add those fields to `Weapon` (that is a separate weapon-enrichment WO). Instead, this WO reads bypass metadata from the entity's `EF.WEAPON` dict (which may carry `"tags"` or `"material"` keys) as a fallback, and from the `Weapon.damage_type` field (`"nonlethal"` is not physical, so DR would not apply to it anyway). See §4.1 for the weapon-bypass extraction logic.

---

## §4 Implementation Spec

### 4.1 Update `get_applicable_dr()` call sites to pass weapon bypass metadata

**File:** `aidm/core/attack_resolver.py`, lines 422–427
**File:** `aidm/core/full_attack_resolver.py`, lines 363–365

Both call sites currently call:

```python
dr_amount = get_applicable_dr(
    world_state, intent.target_id, intent.weapon.damage_type,
)
```

Replace with a helper that extracts weapon bypass flags. Add a new private function `_extract_weapon_bypass_flags(weapon, entity)` to `damage_reduction.py` (see §4.2). The updated call in `attack_resolver.py` becomes:

```python
# WO-ENGINE-DR-001: Extract weapon bypass flags for DR calculation
from aidm.core.damage_reduction import (
    get_applicable_dr, apply_dr_to_damage, extract_weapon_bypass_flags
)
is_magic_weapon, weapon_material, weapon_alignment, weapon_enhancement = \
    extract_weapon_bypass_flags(intent.weapon, attacker)
dr_amount = get_applicable_dr(
    world_state, intent.target_id, intent.weapon.damage_type,
    is_magic_weapon=is_magic_weapon,
    weapon_material=weapon_material,
    weapon_alignment=weapon_alignment,
    weapon_enhancement=weapon_enhancement,
)
final_damage, dr_absorbed = apply_dr_to_damage(damage_total, dr_amount)
```

For `full_attack_resolver.py`, the `dr_amount` is computed once in `resolve_full_attack()` (at approximately line 575, in the pre-attack setup block where `get_applicable_dr()` is called) and passed into `resolve_single_attack_with_critical()` via the `dr_amount` parameter. Update that single call site the same way: extract bypass flags from the attacker's weapon, pass them to `get_applicable_dr()`.

### 4.2 New helper `extract_weapon_bypass_flags()` in `damage_reduction.py`

Add to `aidm/core/damage_reduction.py` after the existing `_weapon_bypasses_dr()` function:

```python
def extract_weapon_bypass_flags(
    weapon: Any,
    attacker: dict,
) -> tuple:
    """Extract magic/material/alignment bypass flags from a Weapon or entity dict.

    Priority order:
    1. weapon.damage_type == "nonlethal" → treat as non-physical, DR won't apply
    2. attacker[EF.WEAPON] dict "tags" list: ["magic", "silver", ...]
    3. attacker[EF.WEAPON] dict "material" key: "adamantine", "cold_iron", etc.
    4. Default: non-magic steel, no alignment

    Returns:
        (is_magic: bool, material: str, alignment: str, enhancement: int)
    """
    # Natural attacks: weapon_type == "natural" → never magic
    weapon_type = getattr(weapon, "weapon_type", "one-handed")
    if weapon_type == "natural":
        return (False, "steel", "none", 0)

    entity_weapon = attacker.get(EF.WEAPON, {}) if attacker else {}
    tags = entity_weapon.get("tags", [])
    material = entity_weapon.get("material", "steel")
    alignment = entity_weapon.get("alignment", "none")
    enhancement = entity_weapon.get("enhancement_bonus", 0)

    # "magic" in tags or enhancement >= 1 → magic weapon
    is_magic = ("magic" in tags) or (enhancement >= 1)

    return (is_magic, material, alignment, enhancement)
```

### 4.3 Emit `damage_reduced` event when `dr_absorbed > 0`

**File:** `aidm/core/attack_resolver.py`, insertion point after `apply_dr_to_damage()` call (currently line 427), before the `damage_roll` event block (currently line 429).

Add:

```python
# WO-ENGINE-DR-001: Emit damage_reduced event when DR absorbs damage
if dr_absorbed > 0:
    events.append(Event(
        event_id=current_event_id,
        event_type="damage_reduced",
        timestamp=timestamp + 0.09,
        payload={
            "entity_id": intent.target_id,
            "base_damage": damage_total,
            "dr_absorbed": dr_absorbed,
            "final_damage": final_damage,
            "dr_amount": dr_amount,
            "bypass_type": _get_bypass_type(
                target.get(EF.DAMAGE_REDUCTIONS, []), dr_amount
            ),
        },
        citations=[{"source_id": "681f92bc94ff", "page": 291}]
    ))
    current_event_id += 1
```

Apply the identical block in `full_attack_resolver.py` inside `resolve_single_attack_with_critical()`, after the `apply_dr_to_damage()` call at line 365, before the `damage_roll` event block at line 367.

### 4.4 Add `dr_absorbed` to `hp_changed` payload

**File:** `aidm/core/attack_resolver.py`, `hp_changed` event block (lines 464–477).

Change the payload from:

```python
payload={
    "entity_id": intent.target_id,
    "hp_before": hp_before,
    "hp_after": hp_after,
    "delta": -final_damage,
    "source": "attack_damage"
}
```

To:

```python
payload={
    "entity_id": intent.target_id,
    "hp_before": hp_before,
    "hp_after": hp_after,
    "delta": -final_damage,
    "source": "attack_damage",
    "dr_absorbed": dr_absorbed,   # WO-ENGINE-DR-001
}
```

Apply the identical change in `full_attack_resolver.py` at the `hp_changed` emit block (lines 777–788). In `full_attack_resolver.py`, the `dr_absorbed` is the sum of all per-hit DR absorbed across the full attack sequence. The builder should accumulate a `total_dr_absorbed` variable alongside `total_damage` in the `resolve_full_attack()` loop, then include it in the single `hp_changed` payload at the end.

### 4.5 Suppress `hp_changed` when `final_damage == 0`

**File:** `aidm/core/attack_resolver.py`, HP-subtraction block (lines 460–477).

Wrap the `hp_changed` emit in a guard:

```python
# WO-ENGINE-DR-001: Only emit hp_changed if damage penetrated DR
hp_before = target.get(EF.HP_CURRENT, 0)
hp_after = hp_before - final_damage

if final_damage > 0:
    events.append(Event(
        event_id=current_event_id,
        event_type="hp_changed",
        ...
    ))
    current_event_id += 1
    # WO-ENGINE-DEATH-DYING-001: transition check only when HP changed
    from aidm.core.dying_resolver import resolve_hp_transition
    ...
```

When `final_damage == 0`, skip both `hp_changed` and `resolve_hp_transition`. The `damage_reduced` event (§4.3) already conveys what happened.

Apply the same guard in `full_attack_resolver.py`: the `if total_damage > 0:` guard at line 772 already gates the full-attack `hp_changed`, but it must use the post-DR `total_damage` (i.e., sum of `final_damage` values per hit, not sum of pre-DR `damage_total` values). Verify the accumulation variable is `total_damage += final_damage` not `total_damage += damage_total`.

### 4.6 New private helper `_get_bypass_type()` in `damage_reduction.py`

This small helper returns the bypass string of the DR entry that was used (for the `damage_reduced` event payload):

```python
def _get_bypass_type(dr_list: list, applied_dr_amount: int) -> str:
    """Return the bypass type of the DR entry that was applied.

    Used to populate damage_reduced event payload.
    Returns the bypass of the highest-amount DR entry matching applied_dr_amount,
    or "-" if not found.
    """
    for entry in dr_list:
        if entry.get("amount", 0) == applied_dr_amount:
            return entry.get("bypass", "-")
    return "-"
```

---

## §5 Event Types

| Event type | Emitted when | New? |
|------------|-------------|------|
| `damage_reduced` | `dr_absorbed > 0` after damage calculation | YES |
| `hp_changed` | `final_damage > 0` (DR did not fully negate) | Modified — adds `dr_absorbed` field |

### `damage_reduced` payload

```json
{
  "event_type": "damage_reduced",
  "payload": {
    "entity_id": "orc_01",
    "base_damage": 8,
    "dr_absorbed": 5,
    "final_damage": 3,
    "dr_amount": 5,
    "bypass_type": "magic"
  }
}
```

### `hp_changed` payload (updated)

```json
{
  "event_type": "hp_changed",
  "payload": {
    "entity_id": "orc_01",
    "hp_before": 20,
    "hp_after": 17,
    "delta": -3,
    "source": "attack_damage",
    "dr_absorbed": 5
  }
}
```

When no DR applied: `"dr_absorbed": 0`.

---

## §6 Regression Risk

**Low.** The `damage_reduction.py` module already exists and its logic is correct. The changes are:

1. Adding a field to `hp_changed` payload (`dr_absorbed`) — additive, existing tests that do not assert on `dr_absorbed` are unaffected.
2. Emitting a new `damage_reduced` event before `hp_changed` — any test that asserts on event sequence by index (e.g., `events[2].event_type == "hp_changed"`) may need index adjustment if DR applies. Tests that filter by `event_type` are unaffected.
3. Suppressing `hp_changed` when `final_damage == 0` — this is a behavior change. Any existing test that fires an attack dealing less damage than the target's DR may now see no `hp_changed` event. Check existing DR-related tests (if any) in the engine gate suite.
4. The `extract_weapon_bypass_flags()` call is additive — it reads from the entity's `EF.WEAPON` dict, which may be absent on many test entities. The defaults (non-magic steel, no alignment) preserve existing behavior for entities that have no `EF.WEAPON` dict.

**Gold master impact:** If any gold master scenario involves a target with `EF.DAMAGE_REDUCTIONS`, those `.jsonl` files will now include `damage_reduced` events and modified `hp_changed` payloads. Builder must regenerate affected gold masters after implementation.

---

## §7 Gate Spec

**Gate name:** `ENGINE-DR`
**Test file:** `tests/test_engine_dr_gate.py`

| # | Test ID | Description | Assert |
|---|---------|-------------|--------|
| 1 | DR-01 | Attack deals 8 raw damage, target has DR 5/magic, attacker uses non-magic weapon | `final_damage == 3`, `dr_absorbed == 5`, `hp_changed.delta == -3` |
| 2 | DR-02 | Attack deals 8 raw damage, target has DR 5/magic, attacker uses magic weapon (tag `"magic"` in `EF.WEAPON["tags"]`) | `final_damage == 8`, `dr_absorbed == 0`, no `damage_reduced` event |
| 3 | DR-03 | Attack deals 3 raw damage, target has DR 5/magic, non-magic weapon | `final_damage == 0`, `dr_absorbed == 3`, no `hp_changed` event emitted, `damage_reduced` event present |
| 4 | DR-04 | Target has DR 10/— (nothing bypasses), attacker has magic weapon with enhancement +3 | DR applies regardless; `final_damage == max(0, raw - 10)` |
| 5 | DR-05 | Target has two DR entries: `[{"amount": 10, "bypass": "magic"}, {"amount": 5, "bypass": "silver"}]`, non-magic non-silver weapon | Highest applicable DR (10) used, not sum (15); `dr_absorbed == 10` |
| 6 | DR-06 | Natural attack (`weapon_type="natural"`) against target with DR 5/magic | DR applies (`is_magic=False`); natural attacks are not magic; `dr_absorbed == 5` |
| 7 | DR-07 | Any attack where `dr_absorbed > 0` | `damage_reduced` event present in event list with correct `entity_id`, `base_damage`, `dr_absorbed`, `final_damage` |
| 8 | DR-08 | Magic weapon bypasses DR 5/magic — `dr_absorbed == 0` | No `damage_reduced` event emitted |
| 9 | DR-09 | Full attack sequence with 2 hits: target has DR 5/magic, non-magic weapon, 8 and 6 raw damage | Each hit reduces by 5 independently; `total_damage == 4` (3 + 1); `total_dr_absorbed == 10` in `hp_changed` payload |
| 10 | DR-10 | Entity has no `DAMAGE_REDUCTIONS` field (field absent) | `get_applicable_dr()` returns 0, no DR applied, behavior identical to pre-WO |

**Test count target:** 10 checks → Gate `ENGINE-DR` 10/10.

---

## §8 What This WO Does NOT Do

- Does not add magic/material/enhancement fields to the `Weapon` dataclass in `aidm/schemas/attack.py` — that is a separate weapon-enrichment WO. This WO reads from `EF.WEAPON` dict on the entity as a fallback.
- Does not implement DR for spell damage — spell damage goes through `play_loop.py` / `spell_resolver.py`, not `attack_resolver.py`. DR for spells is deferred.
- Does not implement energy resistance (a related but distinct mechanic — separate field and resolver).
- Does not implement hardness (object damage reduction — different context).
- Does not implement DR stacking for creatures with multiple types (PHB says best applicable wins — already implemented in `get_applicable_dr()`; this WO preserves that).
- Does not change the `Weapon` dataclass validation logic.
- Does not touch `play_loop.py` directly.

---

## §9 Preflight

```bash
cd f:/DnD-3.5

# Verify damage_reduction.py baseline (no regressions before changes):
python -m pytest tests/ -k "dr or damage_reduction" -v --tb=short

# After implementing §4.1–§4.6:
python -m pytest tests/test_engine_dr_gate.py -v
# DR-01 through DR-10 must pass.

# Regression sweep — engine gates:
python -m pytest tests/test_engine_gate_cp17.py tests/test_engine_gate_cp22.py tests/test_engine_gate_cp23.py tests/test_engine_gate_xp01.py -v --tb=short
# Zero new failures expected (dr_absorbed field is additive; hp_changed suppression
# only fires when final_damage==0, which no existing test exercises without DR).

# Full suite:
python -m pytest tests/ -x --tb=short
# Zero new regressions.

# If gold masters affected:
python tests/_gen_v12.py   # or applicable generation script
python -m pytest tests/ -x --tb=short
```
