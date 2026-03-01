**Lifecycle:** ARCHIVE

# DEBRIEF — WO-ENGINE-CL-DAMAGE-SCALE-001

**Commit:** `801875d`
**Gates:** CDS-001..008 — 8/8 PASS
**Batch:** AM (WO1 of 4)

---

## Pass 1 — Context Dump

### Files Changed

| File | Lines | Change |
|------|-------|--------|
| `aidm/core/spell_resolver.py` | ~140–160 (SpellDefinition fields) | Added `damage_dice_per_cl`, `max_damage_cl` fields |
| `aidm/core/spell_resolver.py` | ~185–195 (to_dict) | Added both new fields to serialization |
| `aidm/core/spell_resolver.py` | ~200–215 (new method) | Added `effective_damage_dice(caster_level)` |
| `aidm/core/spell_resolver.py` | ~870–880 (AoE STP call) | `damage_dice=spell.damage_dice or ""` → `spell.effective_damage_dice(caster.caster_level) or ""` |
| `aidm/core/spell_resolver.py` | ~980–1010 (_resolve_damage) | `spell.damage_dice is None` → `_dmg_expr = spell.effective_damage_dice(caster.caster_level)` |
| `aidm/data/spell_definitions.py` | fireball, lightning_bolt entries | `damage_dice="8d6"` → `damage_dice=None, damage_dice_per_cl="d6", max_damage_cl=10` |

### Before / After (key delta — _resolve_damage)

**Before:**
```python
if spell.damage_dice is None:
    return 0, self._stp_builder.damage_roll(...)
if maximize:
    total = apply_maximize_dice(spell.damage_dice)
else:
    rolls, total = self._roll_dice(spell.damage_dice)
```

**After:**
```python
_dmg_expr = spell.effective_damage_dice(caster.caster_level)
if _dmg_expr is None:
    return 0, self._stp_builder.damage_roll(...)
if maximize:
    total = apply_maximize_dice(_dmg_expr)
else:
    rolls, total = self._roll_dice(_dmg_expr)
```

### effective_damage_dice() method
```python
def effective_damage_dice(self, caster_level: int) -> Optional[str]:
    if self.damage_dice_per_cl is not None:
        cl_cap = min(caster_level, self.max_damage_cl) if self.max_damage_cl > 0 else caster_level
        return f"{cl_cap}{self.damage_dice_per_cl}"
    return self.damage_dice
```

### Gate file
`tests/test_engine_cl_damage_scale_gate.py` — 8 tests.

---

## Pass 2 — PM Summary

SpellDefinition extended with `damage_dice_per_cl` (e.g., `"d6"`) and `max_damage_cl` (cap). `effective_damage_dice(cl)` returns CL-scaled string (`"5d6"` at CL5) or static `damage_dice` fallback. Fireball and lightning_bolt updated from hard-coded `"8d6"` to `1d6/CL max 10d6` (PHB p.231/243). `_resolve_damage()` and AoE STP call site both updated to route through `effective_damage_dice()`. Magic missile CL scaling deferred (CONSUME_DEFERRED — per-missile bonus, different mechanic). 8/8 gates pass.

---

## Pass 3 — Retrospective

**FINDING-ENGINE-MAGIC-MISSILE-CL-SCALE-001 (LOW, CONSUME_DEFERRED):** Magic missile is `1d4+1 per missile` not a dice-scaled single attack — the `damage_dice_per_cl` pattern doesn't map cleanly. Requires separate implementation (multiple missiles at higher CL). Filed to BACKLOG.

**Parallel paths checked:** AoE STP call site (`_resolve_area_targets`) and single-target `_resolve_damage()` both updated. No orphaned `spell.damage_dice` reads in spell_resolver.py remain.

**Kernel touches:** None.

---

## Radar

| ID | Severity | Status | Note |
|----|----------|--------|------|
| FINDING-ENGINE-MAGIC-MISSILE-CL-SCALE-001 | LOW | CONSUME_DEFERRED | Multi-missile pattern; different WO |

---

## Coverage Map Update

Row 378 updated: **PARTIAL** → **IMPLEMENTED**
- New text: `SpellDefinition.effective_damage_dice(cl) + effective_duration_rounds(cl); fireball/lightning_bolt CL-scaled; haste/slow/bless/cause_fear duration CL-scaled. CDS-001..008, CDU-001..008. Batch AM.`

## Consume-Site Confirmation

- **Write site:** `spell_definitions.py` — `damage_dice_per_cl="d6", max_damage_cl=10` on fireball/lightning_bolt
- **Read site:** `spell_resolver.py _resolve_damage()` — `spell.effective_damage_dice(caster.caster_level)` → dice expression
- **Effect:** Fireball at CL5 deals 5d6 fire; at CL10 10d6 (capped)
- **Gate proof:** CDS-005 (fireball CL5 → "5d6"), CDS-007 (CL10 → "10d6"), CDS-008 (CL12 → "10d6" cap)
