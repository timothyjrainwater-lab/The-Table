# WO-ENGINE-POISON-DISEASE-001 — Poison & Disease (PHB p.292)

**Issued:** 2026-02-24
**Authority:** PM
**Gate:** ENGINE-POISON-DISEASE (new gate, defined below)

---

## DEPENDENCY BLOCK

> **BLOCKED on WO-ENGINE-ABILITY-DAMAGE-001 ACCEPTED.**
> Do not implement until `ability_damage_resolver.py` exists and EF ability score damage fields are live.
>
> Poison and disease both inflict ability damage as their primary mechanical effect. Without `apply_ability_damage()` and the corresponding EF fields for tracking stat damage (STR_DAMAGE, DEX_DAMAGE, CON_DAMAGE, etc.), this WO has no surface to write its damage onto. Implementation before that WO is accepted will produce dead resolver code that silently no-ops on the most important branch.

---

## 1. Target Lock

PHB p.292: Poisons injure or kill by dealing ability damage on failed Fortitude saves. Diseases expose a target to recurring ability damage after an incubation period, curing naturally only after two consecutive successful saves.

Mechanically:
- **Poison** is a two-save mechanic: an immediate (primary) save at injury, and a secondary save 10 rounds later. Initial and secondary damage can target the same or different ability scores and use different dice.
- **Disease** has an incubation period (rounds or days depending on context) before the first damage check, then repeats at a fixed interval. Two consecutive successful Fort saves remove the disease.
- Both types call `apply_ability_damage()` (from WO-ENGINE-ABILITY-DAMAGE-001) for the actual stat reduction.
- No new player-facing intent is needed for normal play — monsters deliver poison via an optional `poison_payload` on attack events, and GMs/scripted encounters call `apply_disease_exposure()` directly.

**Done means:** `EF.ACTIVE_POISONS` and `EF.ACTIVE_DISEASES` fields defined + `poison_disease_resolver.py` with all five public functions + `play_loop.py` calling tick functions at end of round + events emitted for all save outcomes + Gate ENGINE-POISON-DISEASE 10/10.

---

## 2. PHB Rules (p.292)

### 2.1 Poison

> A poisoned creature must make two Fortitude saving throws. The first is the **initial save**, made immediately when the poison is delivered. The second is the **secondary save**, made 1 minute later (10 rounds). Each save uses the same DC. Failure on either save deals the listed ability damage for that stage. Success on a save means no damage for that stage.

Key rulings:
- **Delivery types:** injury (weapon coated), ingested, inhaled, contact. Each can be avoided differently; most combat poisons are injury type.
- **DC:** varies by poison. Use DC 13 as the default for generic venom when no specific poison_def is provided.
- **Primary and secondary damage may differ:** e.g., "1d6 STR initial / 2d6 STR secondary" or "1d4 CON initial / 1d4 CON secondary".
- **Elves:** immune to sleep and paralysis effects, but not to poison in general. Do not conflate `IMMUNE_SLEEP` with poison immunity.
- **Dwarves:** `EF.SAVE_BONUS_POISON` is already live on the EF class (added in WO-CHARGEN-RACIAL-001) — add this value to the Fort save roll before comparison.
- **Paladins:** immune to all poisons at class level 3+ (detect via `CLASS_LEVELS.get("paladin", 0) >= 3`). Wrap in `is_immune_to_poison()`.
- **Secondary save timing:** schedule at `current_round + 10`. The secondary entry stays in `ACTIVE_POISONS` until resolved; `process_poison_secondaries()` checks `secondary_due_at_round <= current_round` each round.

### 2.2 Disease

> A diseased creature does not take damage immediately. Instead, the disease has an **incubation period** after which the creature must make a Fortitude saving throw at the listed interval (typically once per day, represented here as once per N rounds). On a failed save, the listed ability damage is applied. On a successful save, no damage is dealt. **Two consecutive successful saves** cure the disease naturally.

Key rulings:
- **Incubation period:** measured in rounds for combat-timescale diseases. `apply_disease_exposure()` records `next_check_round = current_round + incubation_rounds`.
- **Damage interval:** typically 1/day in tabletop, mapped to a configurable `check_interval_rounds` in the disease_def (default 10 for most combat diseases; caller passes what the stat block specifies).
- **Consecutive saves tracked per disease instance:** `consecutive_saves` counter in the active disease dict. Increment on success, reset to 0 on failure.
- **Cure:** when `consecutive_saves` reaches 2, emit `disease_cured` and remove from `ACTIVE_DISEASES`.
- **Example:** Filth Fever — Fort DC 12, incubation 1d3 days, 1d3 DEX damage / 1d3 CON damage per day on fail. For combat scale, caller maps days to rounds.
- **Disease delivery types:** contact, inhaled, injury — same taxonomy as poison. Tracked in `delivery_type` field for future immunity checks.

---

## 3. New Entity Fields

Add to `aidm/schemas/entity_fields.py` under a new `# --- Poison & Disease (WO-ENGINE-POISON-DISEASE-001) ---` section:

```python
# --- Poison & Disease (WO-ENGINE-POISON-DISEASE-001) ---
ACTIVE_POISONS = "active_poisons"
# List[dict] — each dict describes one active poison instance on this entity.
# Schema per entry:
# {
#     "poison_id": str,              # unique ID for this poison application (e.g. "spider_venom")
#     "ability_primary": str,        # ability score targeted by primary damage (e.g. "str", "con")
#     "damage_primary": str,         # dice expression for primary damage (e.g. "1d6")
#     "ability_secondary": str,      # ability score targeted by secondary damage
#     "damage_secondary": str,       # dice expression for secondary damage (e.g. "2d6")
#     "fort_dc": int,                # Fortitude DC for both saves
#     "secondary_due_at_round": int, # round number when secondary save fires
#     "delivery_type": str,          # "injury" | "ingested" | "inhaled" | "contact"
#     "resolved": bool,              # True once secondary save has been processed
# }

ACTIVE_DISEASES = "active_diseases"
# List[dict] — each dict describes one active disease instance on this entity.
# Schema per entry:
# {
#     "disease_id": str,             # unique key for disease type (e.g. "filth_fever")
#     "name": str,                   # display name (e.g. "Filth Fever")
#     "ability": str,                # ability score damaged on fail (e.g. "con")
#                                    # May be a list for multi-stat diseases (e.g. ["dex", "con"])
#     "damage_dice": str,            # dice expression (e.g. "1d3")
#     "fort_dc": int,                # Fortitude save DC
#     "next_check_round": int,       # round when next save is required
#     "check_interval_rounds": int,  # rounds between subsequent checks after the first
#     "consecutive_saves": int,      # 0 or 1; reaches 2 → cured
#     "delivery_type": str,          # "contact" | "inhaled" | "injury"
# }
```

**Note on multi-ability diseases:** The `ability` field may be either a `str` (single stat) or a `list[str]` (multi-stat). When it is a list, apply `damage_dice` once per ability listed. The resolver must handle both cases. This covers diseases like Filth Fever (DEX and CON) without requiring a separate entry per stat.

---

## 4. Implementation Spec

### 4.1 New Resolver: `aidm/core/poison_disease_resolver.py`

```python
# aidm/core/poison_disease_resolver.py
"""Poison and disease resolution for D&D 3.5e.

PHB p.292. Requires WO-ENGINE-ABILITY-DAMAGE-001 to be accepted first:
all stat reduction is delegated to apply_ability_damage() from
ability_damage_resolver.py.

WO-ENGINE-POISON-DISEASE-001
"""

from typing import List, Tuple


def is_immune_to_poison(entity: dict) -> bool:
    """Return True if entity is immune to all poison effects.

    Checks:
    - Paladin class level >= 3: entity.get(EF.CLASS_LEVELS, {}).get("paladin", 0) >= 3
    - Construct type (future flag, guarded with .get)
    - Undead type: entity.get(EF.IS_UNDEAD, False)

    Does NOT treat elf IMMUNE_SLEEP as poison immunity.
    """


def apply_poison(
    world_state: "WorldState",
    target_id: str,
    poison_def: dict,
    current_round: int,
    rng: "RNGProvider",
    events: List[dict],
) -> Tuple["WorldState", List[dict]]:
    """Deliver poison to target; resolve primary Fort save immediately.

    Steps:
    1. Check is_immune_to_poison(target) — if immune, emit poison_immune event and return.
    2. Build Fort save total:
           d20 + entity.get(EF.SAVE_FORT, 0)
               + entity.get(EF.SAVE_BONUS_POISON, 0)   # dwarf racial, already on EF
    3. Compare to poison_def["fort_dc"]:
       - FAIL (total < dc): call apply_ability_damage(world_state, target_id,
             poison_def["ability_primary"], roll(poison_def["damage_primary"], rng))
         Emit poison_save_failed (save_type="primary").
       - PASS (total >= dc): Emit poison_save_succeeded (save_type="primary").
    4. Regardless of primary outcome: add entry to target ACTIVE_POISONS
       with resolved=False, secondary_due_at_round=current_round+10.
       (Secondary save always fires unless entity dies first.)
    5. Return updated world_state and events.

    poison_def keys: poison_id, ability_primary, damage_primary,
                     ability_secondary, damage_secondary, fort_dc, delivery_type.
    """


def process_poison_secondaries(
    world_state: "WorldState",
    current_round: int,
    rng: "RNGProvider",
    events: List[dict],
) -> Tuple["WorldState", List[dict]]:
    """Process all pending secondary poison saves that are due this round.

    Called at end of each round by play_loop.py.

    For each entity in world_state.entities:
        For each poison in entity.get(EF.ACTIVE_POISONS, []):
            If not resolved and secondary_due_at_round <= current_round:
                Fort save (same formula as apply_poison).
                FAIL → apply secondary ability damage; emit poison_save_failed (save_type="secondary").
                PASS → emit poison_save_succeeded (save_type="secondary").
                Mark resolved=True.
                Emit poison_resolved.
    """


def apply_disease_exposure(
    world_state: "WorldState",
    target_id: str,
    disease_def: dict,
    current_round: int,
) -> "WorldState":
    """Record a disease exposure on target. Does not make a save immediately.

    Adds disease_def entry to target ACTIVE_DISEASES with:
        next_check_round = current_round + disease_def["incubation_rounds"]
        consecutive_saves = 0

    disease_def keys: disease_id, name, ability, damage_dice, fort_dc,
                      incubation_rounds, check_interval_rounds, delivery_type.

    Deduplication: if disease_id already present in ACTIVE_DISEASES,
    do not add a duplicate (existing infection takes precedence).
    """


def process_disease_ticks(
    world_state: "WorldState",
    current_round: int,
    rng: "RNGProvider",
    events: List[dict],
) -> Tuple["WorldState", List[dict]]:
    """Process all active disease checks due this round.

    Called at end of each round by play_loop.py (after poison secondaries).

    For each entity in world_state.entities:
        For each disease in entity.get(EF.ACTIVE_DISEASES, []):
            If next_check_round <= current_round:
                Fort save (d20 + SAVE_FORT). No racial poison bonus for disease
                unless disease_def specifies otherwise — use base Fort only.
                FAIL:
                    abilities = disease["ability"] if isinstance(list) else [disease["ability"]]
                    For each ability in abilities:
                        apply_ability_damage(world_state, target_id, ability,
                                             roll(disease["damage_dice"], rng))
                    disease["consecutive_saves"] = 0
                    Emit disease_save_failed for each ability damaged.
                PASS:
                    disease["consecutive_saves"] += 1
                    Emit disease_save_succeeded (consecutive_saves=N).
                    If disease["consecutive_saves"] >= 2:
                        Emit disease_cured.
                        Remove disease from ACTIVE_DISEASES list.
                        Continue to next disease.
                If not cured: disease["next_check_round"] += disease["check_interval_rounds"]
    """
```

### 4.2 No New Intent Required

Poison delivery in combat uses an **optional `poison_payload` field on the attack event dict** rather than a separate `PoisonAttackIntent`. This keeps the attack path clean and avoids a combinatorial intent explosion for every venomous monster.

Suggested convention in attack event payloads:
```python
# In the attack hit resolution block of attack_resolver.py (or monster AI layer):
# After confirming a hit, if the attack source carries venom:
if "poison_payload" in attack_source_weapon:
    world_state, events = apply_poison(
        world_state,
        target_id=intent.target_id,
        poison_def=attack_source_weapon["poison_payload"],
        current_round=current_round,
        rng=rng,
        events=events,
    )
```

The `poison_payload` dict lives on the weapon/attack definition, not the intent. Stat blocks for venomous creatures include it in their weapon data. This WO does not wire a specific monster; it only defines the resolver contract. The first venomous monster WO picks up the payload convention.

### 4.3 `play_loop.py` Wiring

At the **end of each round** (after all actors in the initiative order have taken their turns), add:

```python
# WO-ENGINE-POISON-DISEASE-001: poison secondary saves + disease ticks
from aidm.core.poison_disease_resolver import (
    process_poison_secondaries,
    process_disease_ticks,
)

world_state, events = process_poison_secondaries(
    world_state, current_round, rng, events
)
world_state, events = process_disease_ticks(
    world_state, current_round, rng, events
)
```

"End of round" means the moment the last entity in the initiative order finishes its turn before the round counter increments. Poison secondaries fire before disease ticks.

### 4.4 `ability_damage_resolver.py` Integration

`poison_disease_resolver.py` must import and call `apply_ability_damage()` from WO-ENGINE-ABILITY-DAMAGE-001's resolver for all actual stat reductions. This WO does not re-implement stat math.

```python
from aidm.core.ability_damage_resolver import apply_ability_damage
```

If this import fails at module load time, the dependency guard (PD-10) is violated and the WO must be rolled back.

### 4.5 `is_immune_to_poison()` Detail

```python
def is_immune_to_poison(entity: dict) -> bool:
    # Paladin 3+
    class_levels = entity.get(EF.CLASS_LEVELS, {})
    if class_levels.get("paladin", 0) >= 3:
        return True
    # Undead are immune (no living physiology)
    if entity.get(EF.IS_UNDEAD, False):
        return True
    # Construct type: guard with .get for future flag
    if entity.get("is_construct", False):
        return True
    return False
```

Elves are NOT immune to poison — `EF.IMMUNE_SLEEP` does not grant poison immunity. Do not add elf logic here.

### 4.6 Fort Save Formula (Poison)

```
fort_save_total = d20_roll + entity.get(EF.SAVE_FORT, 0) + entity.get(EF.SAVE_BONUS_POISON, 0)
```

`EF.SAVE_BONUS_POISON` is already defined in the EF class (added by WO-CHARGEN-RACIAL-001 for dwarves, value +2). It is 0 for most entities. No special-casing is needed — the field defaults to 0.

### 4.7 Fort Save Formula (Disease)

```
fort_save_total = d20_roll + entity.get(EF.SAVE_FORT, 0)
```

Disease saves do not use `SAVE_BONUS_POISON` unless a specific disease_def sets a flag to allow it. Use base Fort only to avoid incorrect dwarf bonus stacking on non-poison diseases.

---

## 5. New Event Types

| Event | When | Required Payload Keys |
|-------|------|----------------------|
| `poison_save_failed` | Fort save failed vs poison | `target_id`, `poison_id`, `save_type` ("primary"/"secondary"), `ability`, `damage_amount` |
| `poison_save_succeeded` | Fort save passed vs poison | `target_id`, `poison_id`, `save_type` |
| `poison_resolved` | Secondary save processed (pass or fail) | `target_id`, `poison_id` |
| `poison_immune` | Entity immune to poison | `target_id`, `poison_id`, `reason` |
| `disease_save_failed` | Fort save failed vs disease | `target_id`, `disease_id`, `ability`, `damage_amount` |
| `disease_save_succeeded` | Fort save passed vs disease | `target_id`, `disease_id`, `consecutive_saves` |
| `disease_cured` | Two consecutive passes | `target_id`, `disease_id` |

**Note on `damage_amount` in `poison_save_failed`:** This must be the resolved integer after rolling `damage_primary` or `damage_secondary` dice — not the dice expression string. PD-09 checks for the presence of this key with an integer value.

---

## 6. Regression Risk

- **NONE for existing combat path:** No existing intent routes through `poison_disease_resolver.py`. The resolver is dead code until a venomous monster is wired.
- **LOW for play_loop.py tick calls:** Both `process_poison_secondaries()` and `process_disease_ticks()` iterate over entities and skip immediately when `ACTIVE_POISONS` / `ACTIVE_DISEASES` are absent or empty lists. No entities in existing fixtures carry these fields, so both functions are no-ops on every existing test scenario.
- **Gold masters:** Neither poison nor disease events appear in any existing gold master JSONL. The tick calls produce no output against existing fixtures. No drift expected.
- **EF additions:** Adding two new constants to `_EntityFields` is append-only and cannot break existing field lookups.
- **Import guard:** If WO-ENGINE-ABILITY-DAMAGE-001 has not been accepted, the import of `apply_ability_damage` at the top of `poison_disease_resolver.py` will raise `ImportError` at module load, which will surface as a test collection failure — not a silent wrong answer. This is the correct failure mode for a blocked dependency.

---

## 7. What This WO Does NOT Do

- No Poison Use feat (applying poison to weapons without risk of self-poisoning — deferred)
- No exposure DC for splashed venom during combat (deferred)
- No auto-cure via Neutralize Poison or Remove Disease spells (spell resolver handles its own cure logic; it can call `ACTIVE_POISONS.clear()` or `ACTIVE_DISEASES.clear()` directly — no special hook needed here)
- No inhaled poison hold-breath mechanic (deferred — needs breath-holding tracker)
- No contact poison delivery via touch attacks (delivery_type field is recorded for future use; no enforcement this WO)
- No multi-stage poisons beyond the two-save model (deferred)
- No disease incubation measured in real calendar days (all incubation converted to rounds by the caller)
- No Heal skill checks to slow disease progression (deferred)
- No Improved Fortitude feat bonus (feat bonus already flows through SAVE_FORT if chargen includes it; no special case needed)

---

## 8. Gate Spec

**Gate name:** `ENGINE-POISON-DISEASE`
**Test file:** `tests/test_engine_poison_disease_gate.py` (new file)

| # | Test | Check |
|---|------|-------|
| PD-01 | EF fields exist | `EF.ACTIVE_POISONS == "active_poisons"` and `EF.ACTIVE_DISEASES == "active_diseases"` importable from entity_fields |
| PD-02 | apply_poison() — failed primary save | Fort roll rigged to fail; `poison_save_failed` event with `save_type="primary"` emitted; primary ability damage applied to entity stat |
| PD-03 | apply_poison() — schedules secondary | After apply_poison(), entry in entity `ACTIVE_POISONS` with `secondary_due_at_round = current_round + 10` and `resolved=False` |
| PD-04 | process_poison_secondaries() — failed secondary | Advance to secondary round; Fort roll rigged to fail; `poison_save_failed` event with `save_type="secondary"` emitted; secondary ability damage applied |
| PD-05 | process_poison_secondaries() — resolved after secondary | After secondary check fires (pass or fail), entry has `resolved=True` and `poison_resolved` event emitted |
| PD-06 | apply_disease_exposure() — adds to ACTIVE_DISEASES | Call apply_disease_exposure(); entity `ACTIVE_DISEASES` contains entry with correct disease_id, next_check_round = current_round + incubation, consecutive_saves = 0 |
| PD-07 | process_disease_ticks() — failed save applies damage | Advance to next_check_round; Fort roll rigged to fail; `disease_save_failed` event emitted; ability damage applied via apply_ability_damage() |
| PD-08 | Two consecutive disease saves → disease_cured | Fort roll rigged to pass twice; after second pass `disease_cured` event emitted and disease removed from `ACTIVE_DISEASES` |
| PD-09 | poison_save_failed event payload completeness | Event dict contains keys: `target_id`, `poison_id`, `save_type`, `ability`, `damage_amount`; `damage_amount` is int > 0 |
| PD-10 | Dependency guard | Remove or rename ability_damage_resolver.py; attempt to import poison_disease_resolver; assert ImportError raised (confirms hard dependency, not silent no-op) |

**Test count target:** ENGINE-POISON-DISEASE 10/10.

---

## 9. Preflight

```bash
cd f:/DnD-3.5

# Confirm baseline (run before touching any code)
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5

# Confirm dependency WO is accepted before starting
python -c "from aidm.core.ability_damage_resolver import apply_ability_damage; print('dependency OK')"

# After implementation
python -m pytest tests/test_engine_poison_disease_gate.py -v
python -m pytest tests/ -q --ignore=tests/test_heuristics_image_critic.py \
  --ignore=tests/test_ws_bridge.py --ignore=tests/test_spark_integration_stress.py \
  --ignore=tests/test_speak_signal.py | tail -5
```
