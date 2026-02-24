# WO-ENGINE-METAMAGIC-001 — Metamagic Feats at Runtime

**Type:** Builder WO
**Gate:** ENGINE-METAMAGIC
**Tests:** 12 (MM-01 through MM-12)
**Depends on:** WO-ENGINE-SPELL-SLOTS-001 (ACCEPTED — slot governor live), WO-ENGINE-SPELL-PREP-001 (ACCEPTED — SPELLS_PREPARED live)
**Blocks:** nothing
**Priority:** Medium — completes core spellcasting surface

---

## 1. Target Lock

Metamagic feats (PHB Chapter 5) modify spells at cast time — increasing slot cost, altering damage, duration, or component requirements. Feat recognition exists in chargen (`EF.FEATS`) but no runtime effect is wired. This WO implements four metamagic feats: **Empower**, **Maximize**, **Extend**, and **Heighten**. Quicken is partially wired (AoO exemption in `aoo.py`) — this WO formalizes its slot cost. Silent and Still (component removal) are deferred — no component system exists yet.

**PHB specs:**
- **Empower Spell** (PHB p.93): All variable numeric effects × 1.5. Slot cost +2.
- **Maximize Spell** (PHB p.97): All variable numeric effects use maximum value (no dice roll). Slot cost +3.
- **Extend Spell** (PHB p.94): Duration × 2. Slot cost +1.
- **Heighten Spell** (PHB p.95): Spell treated as higher level (raises save DC). Slot cost = target level (operator-specified).
- **Quicken Spell** (PHB p.98): Cast as swift action, no AoO provocation. Slot cost +4. (Formalize existing partial wiring.)

---

## 2. Binary Decisions

| # | Question | Answer |
|---|---|---|
| BD-01 | How does the caster declare metamagic? | Optional fields on `CastSpellIntent`. Extend `CastSpellIntent` with `metamagic: List[str] = field(default_factory=list)` and `heighten_to_level: Optional[int] = None`. |
| BD-02 | Slot cost enforcement | Existing slot governor in `play_loop.py` already checks slot level. Builder must add metamagic slot cost calculation before the governor check — compute effective slot = base spell level + metamagic surcharge, then check against available slots. |
| BD-03 | Feat prerequisite check | Yes — before applying metamagic, verify the caster has the feat in `EF.FEATS`. Fail with `intent_validation_failed` + `reason: missing_metamagic_feat` if not present. |
| BD-04 | Empower vs Maximize interaction | Both cannot apply to the same spell simultaneously (they affect the same dice). If both listed, emit `intent_validation_failed` + `reason: incompatible_metamagic`. |
| BD-05 | Maximize implementation | Set a `maximize=True` flag passed into `_roll_dice()` context — return max value without consuming RNG (preserves determinism for subsequent rolls). |
| BD-06 | Empower implementation | After damage total computed (post-crit, pre-DR), multiply by 1.5 and floor. Applied to all variable numeric effects: damage dice, healing dice. NOT to flat bonuses. |
| BD-07 | Extend implementation | Multiply `duration_rounds` on the resulting `ActiveSpellEffect` by 2 before storing. |
| BD-08 | Heighten implementation | Raise effective spell level to `heighten_to_level` for DC calculation only. `get_spell_dc()` uses `spell_level` param — pass heightened level. Slot cost = heightened level. |
| BD-09 | Quicken formalization | Add `"quickened"` to `metamagic` list on `CastSpellIntent`. In `play_loop.py` AoO check: replace `getattr(intent, 'quickened', False)` with canonical `"quickened" in getattr(intent, 'metamagic', [])`. Slot cost +4. Action type: swift (already in action_economy.py? builder verifies). |
| BD-10 | RNG determinism | Maximize must NOT consume RNG (return max without rolling). Empower computes multiplier on final total — no RNG consumed. Order of RNG consumption must not change for non-metamagic paths. |

---

## 3. Contract Spec

### Extended `CastSpellIntent` (intents.py)

```python
@dataclass
class CastSpellIntent:
    type: Literal["cast_spell"] = "cast_spell"
    spell_name: str = ""
    target_mode: Literal["point", "creature", "self", "none"] = "none"
    metamagic: List[str] = field(default_factory=list)
    # Valid values: "empower", "maximize", "extend", "heighten", "quicken"
    heighten_to_level: Optional[int] = None
    # Required when "heighten" in metamagic — target slot level
```

### New module: `aidm/core/metamagic_resolver.py`

```python
METAMAGIC_SLOT_COST = {
    "empower": 2,
    "maximize": 3,
    "extend": 1,
    "heighten": 0,   # variable — cost = heighten_to_level - base_level
    "quicken": 4,
}

def validate_metamagic(intent: CastSpellIntent, caster: dict) -> Optional[str]:
    """Validate metamagic prerequisites. Returns error reason string or None."""

def compute_effective_slot_level(spell_base_level: int, intent: CastSpellIntent) -> int:
    """Compute slot level after metamagic surcharges."""

def apply_empower(damage_total: int) -> int:
    """Return floor(damage_total * 1.5)."""

def apply_maximize_dice(damage_dice: str) -> int:
    """Return maximum possible value for dice string without consuming RNG."""

def apply_extend(effect: ActiveSpellEffect) -> ActiveSpellEffect:
    """Return effect with duration_rounds doubled."""

def apply_heighten_dc(base_dc: int, base_spell_level: int, heighten_to_level: int) -> int:
    """Return DC adjusted for heightened spell level."""
```

### Wiring in `play_loop.py` / `_resolve_spell_cast()`

Order of operations:
1. Parse `intent.metamagic` list
2. Call `validate_metamagic()` → fail-close on error
3. Call `compute_effective_slot_level()` → pass to existing slot governor
4. Pass `maximize=("maximize" in intent.metamagic)` into spell resolver
5. After damage computed: if `"empower" in intent.metamagic` → apply empower multiplier
6. After effect created: if `"extend" in intent.metamagic` → apply extend
7. DC calculation: if `"heighten" in intent.metamagic` → pass `heighten_to_level` to `get_spell_dc()`

### Event payload additions

Add to `spell_cast` event:
```python
"metamagic_applied": list,   # e.g. ["empower"] or []
"effective_slot_level": int, # slot level consumed (base + surcharge)
```

---

## 4. Implementation Plan

1. **`aidm/schemas/intents.py`** — extend `CastSpellIntent` with `metamagic` + `heighten_to_level` fields (backward compatible — defaults to empty list / None)
2. **`aidm/core/metamagic_resolver.py`** — new module, all five helpers
3. **`play_loop.py`** — wire `validate_metamagic()` + `compute_effective_slot_level()` before slot governor; wire empower/maximize/extend/heighten into spell resolution path; canonicalize quicken AoO check
4. **`spell_resolver.py`** — accept `maximize=False` kwarg in damage resolution; when True, skip dice roll and return max value
5. **`aoo.py`** — update quicken check from `getattr(intent, 'quickened', False)` to `"quicken" in getattr(intent, 'metamagic', [])`
6. **`tests/test_engine_metamagic_gate.py`** — 12 gate tests
7. Full suite — 0 new regressions

---

## 5. Gate Tests (ENGINE-METAMAGIC 12/12)

| ID | Description |
|----|-------------|
| MM-01 | Empower: damage total is floor(base × 1.5); slot cost +2 consumed |
| MM-02 | Maximize: damage equals dice maximum (no RNG consumed for damage roll); slot cost +3 consumed |
| MM-03 | Extend: `duration_rounds` on resulting `ActiveSpellEffect` is 2× base; slot cost +1 consumed |
| MM-04 | Heighten: spell DC equals base DC + (heighten_to_level − base_level); slot cost = heighten_to_level consumed |
| MM-05 | Quicken: no AoO provoked; swift action slot used; slot cost +4 consumed |
| MM-06 | Missing feat: caster without "Empower Spell" in `EF.FEATS` → `intent_validation_failed`, `reason: missing_metamagic_feat` |
| MM-07 | Empower + Maximize on same intent → `intent_validation_failed`, `reason: incompatible_metamagic` |
| MM-08 | Insufficient slot: effective slot level exceeds available slots → `spell_slot_empty` event (existing behavior) |
| MM-09 | `spell_cast` event payload contains `metamagic_applied` list and `effective_slot_level` |
| MM-10 | Maximize does not consume RNG — subsequent attack roll in same turn uses same seed position as without maximize |
| MM-11 | Empower applied to healing spell: healing total is floor(base × 1.5) |
| MM-12 | Non-metamagic cast path: `metamagic_applied: []`, `effective_slot_level` equals base spell level; zero behavior change |

---

## 6. Delivery Footer

**Files to create:**
- `aidm/core/metamagic_resolver.py`
- `tests/test_engine_metamagic_gate.py`

**Files to modify:**
- `aidm/schemas/intents.py` — extend `CastSpellIntent`
- `aidm/core/play_loop.py` — wire metamagic validation + slot cost + empower/extend/heighten + canonicalize quicken
- `aidm/core/spell_resolver.py` — accept `maximize` kwarg in damage resolution
- `aidm/core/aoo.py` — canonicalize quicken check

**Commit requirement:** Builder commits all changes. Message: `feat: WO-ENGINE-METAMAGIC-001 — Metamagic runtime (Empower/Maximize/Extend/Heighten/Quicken) — Gate ENGINE-METAMAGIC 12/12`

**Preflight:** Run `pytest tests/test_engine_metamagic_gate.py -v` — 12/12 must pass. Run full suite — 0 new failures.

---

## 7. Integration Seams

- `CastSpellIntent.metamagic` is backward compatible (default empty list) — existing callers unaffected
- Slot governor in `play_loop.py` already takes `spell_level` as input — builder replaces that with `effective_slot_level` from `compute_effective_slot_level()`
- `spell_resolver.py` `_roll_dice()` context: builder must confirm the exact call site for damage dice rolling to insert `maximize` bypass cleanly
- `aoo.py` quicken check: confirm `getattr(intent, 'quickened', False)` is the only check — replace with canonical form

---

## 8. Assumptions to Validate

- `ActiveSpellEffect` has a `duration_rounds` field that is mutable after construction — builder confirms before implementing Extend
- `get_spell_dc()` in `spell_resolver.py` takes `spell_level: int` — builder confirms signature matches Heighten wiring plan
- Swift action slot exists in `action_economy.py` for Quicken — builder confirms; if absent, add it
- Empower applies only to variable numeric effects (dice), not flat bonuses — builder verifies which components of spell damage are dice-based vs flat in `spell_resolver.py`

---

## 9. Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```
