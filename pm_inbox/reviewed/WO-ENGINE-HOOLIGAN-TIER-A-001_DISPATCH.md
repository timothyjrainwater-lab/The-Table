# WO-ENGINE-HOOLIGAN-TIER-A-001 — Hooligan Tier A Bug Bundle
## Status: DISPATCH-READY
## Priority: HIGH
## Closes: FINDING-HG-AOE-ORIGIN-001, FINDING-HG-CLW-UNDEAD-001, FINDING-HG-AOE-ALLEGIANCE-001

---

## Context

Anvil's HOOLIGAN-001 run produced 3 Tier A wrong-result failures. These are bundled because they are all engine-layer fixes, all self-contained, and all under the 4-WO dispatch cap.

**Gate baseline:** Run `python -m pytest tests/ -v --tb=short` before any change. Record pass count. No gate may regress.

---

## WO-A — AoE Origin Square Exclusion (HG-F003 / FINDING-HG-AOE-ORIGIN-001)

### Context

`aoe_rasterizer.py` `rasterize_cone()` and `rasterize_line()` start their loops at distance 1, excluding the caster's origin square. `rasterize_burst()` is correct. PHB p.175: all creatures in the spell's area are affected, including the origin square.

**Affected functions:**
- `aidm/core/aoe_rasterizer.py` — `rasterize_cone()` (loop starts `range(1, ...)`) and `rasterize_line()` (loop starts `range(length_squares)` from offset 1)
- `aidm/core/spell_resolver.py` — `_resolve_area_targets()` — calls rasterizers, applies defeated filter. No allegiance filter. Origin is excluded by the rasterizer itself.

### Target Lock

After this WO:
- `rasterize_cone()` includes the origin square in its returned position list
- `rasterize_line()` includes the origin square in its returned position list
- `rasterize_burst()` unchanged (already correct)
- Gate tests HG-A-001 through HG-A-004 pass

### Binary Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Fix location | `aoe_rasterizer.py` — rasterize_cone() and rasterize_line() | Root cause. `_resolve_area_targets()` does not filter origin — no change needed there. |
| Origin square definition | Caster's grid position at time of cast | PHB p.175 — origin is the point from which the AoE extends |
| Self-damage | Caster at origin IS affected | PHB has no caster exemption. Engine already processes caster as a target (targets dict includes caster_id on line 603). |

### Contract Spec

**`rasterize_cone(origin, direction, length_ft)`:**
- Prepend `origin` to the returned list before the directional sweep begins
- Origin must appear exactly once (use set dedup if needed)

**`rasterize_line(origin, direction, length_ft)`:**
- Prepend `origin` to the returned list before the directional sweep begins
- Same dedup requirement

**Builder must verify:**
- `rasterize_burst()` already includes origin — confirm, do not modify
- Existing cone/line gate tests (if any) — update expected counts if they asserted origin exclusion

### Gate Tests (minimum 4)

| ID | Test | Pass condition |
|----|------|----------------|
| HG-A-001 | `rasterize_cone(origin, N, 30)` — origin in returned squares | `origin in result` |
| HG-A-002 | `rasterize_line(origin, N, 30)` — origin in returned squares | `origin in result` |
| HG-A-003 | `rasterize_burst(origin, 10)` — origin in returned squares | `origin in result` (regression confirm) |
| HG-A-004 | Entity at caster origin square → appears in `affected_entities` from `_resolve_area_targets()` for a cone spell | entity_id in resolution.affected_entities |

---

## WO-B — CLW on Undead: Negative Healing (HG-F004 / FINDING-HG-CLW-UNDEAD-001)

### Context

`spell_resolver.py` `_resolve_healing()` has no creature type check. CLW on an undead target caps healing at 0 (max_healing = 0 for full-HP undead) and returns silently — no events, no damage. PHB p.215-216: positive energy (healing spells) deals damage to undead equal to what it would have healed.

`TargetStats` dataclass (lines 339-359 in spell_resolver.py) has no `creature_type` field. Entities carry `EF.CREATURE_TYPE` or similar on the entity dict — builder must verify the exact field name.

### Target Lock

After this WO:
- CLW cast on an undead target emits an `hp_changed` (damage) event, not silence
- Damage amount = what healing would have been (same dice, same caster level bonus)
- No save (PHB p.215 — positive energy damage to undead, no save stated)
- Gate tests HG-B-001 through HG-B-005 pass

### Binary Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Undead detection | Entity dict creature_type field | Builder must find correct EF field. Search entity_fields.py for "undead", "creature_type". |
| Damage amount | Same total as healing would have been | PHB p.215-216 — positive energy deals equivalent damage |
| Save | No save | PHB text does not state a save for this damage |
| Fix location | `_resolve_healing()` in `spell_resolver.py` | Add undead branch: if target is undead, deal damage instead of healing |
| Event type | `hp_changed` with negative delta | Same event as weapon damage — hp_changed with damage amount |
| `TargetStats` | Add `creature_type: str = "humanoid"` field | Required to carry creature type into resolver. Default "humanoid" = no regression on existing tests. |

### Contract Spec

**`TargetStats` dataclass — add field:**
```python
creature_type: str = "humanoid"  # e.g. "undead", "humanoid", "beast"
```

**`_create_target_stats()` in play_loop.py — populate field:**
```python
creature_type = entity.get(EF.CREATURE_TYPE, "humanoid")  # builder verifies field name
```

**`_resolve_healing()` — add undead branch before healing calculation:**
```python
if target.creature_type == "undead":
    # Positive energy damages undead — same amount as healing would deal
    # No save (PHB p.215-216)
    # [compute total same as healing path]
    # Return as damage (negative hp_changed), not healing
    ...
```

**Builder must verify:**
- Exact field name for creature type on entity dict (`EF.CREATURE_TYPE`? `EF.MONSTER_TYPE`? `entity.get("creature_type")`?)
- How `hp_changed` damage events are emitted in play_loop.py — match existing pattern
- FINDING-HG-HEALING-NOOP-001 (H-007: CLW on living emits no `hp_changed`) — check if same root. If `_resolve_healing()` returns a value but play_loop.py doesn't emit `hp_changed` for it, fix the emission site too. Document in debrief.

### Gate Tests (minimum 5)

| ID | Test | Pass condition |
|----|------|----------------|
| HG-B-001 | CLW cast on entity with `creature_type="undead"` → `hp_changed` event present | event in result.events |
| HG-B-002 | CLW on undead: `hp_changed` payload has negative delta (damage, not healing) | delta < 0 |
| HG-B-003 | CLW on undead: damage amount equals what healing roll would have produced | damage == healing_total |
| HG-B-004 | CLW on living target → `hp_changed` event with positive delta (regression) | delta > 0 |
| HG-B-005 | CLW on living target at full HP → healing amount 0 or event not emitted (already capped — verify existing behavior unchanged) | no regression |

---

## WO-C — AoE Allegiance Filter (HG-F005 / FINDING-HG-AOE-ALLEGIANCE-001)

### Context

Anvil's H-011 test observed allies being excluded from AoE blast. Code audit finds no allegiance filter in `_resolve_area_targets()`, `get_entities_in_area()`, or play_loop.py AoE dispatch path. **The filter may not exist in code** — it may have been a test setup artifact (allies not positioned in blast squares).

**Builder preflight (mandatory before writing any code):**
1. Read `aidm/core/aoe_rasterizer.py` — confirm rasterize_burst/cone/line return ALL squares in area including allied positions
2. Read `aidm/core/spell_resolver.py` `_resolve_area_targets()` lines 708-763 — look for any team/faction/allegiance filter
3. Read `aidm/core/geometry_engine.py` `get_entities_in_area()` — confirm pure positional, no team filter
4. Read `aidm/core/play_loop.py` lines 596-700 — look for any post-resolution allegiance filter on `resolution.affected_entities`
5. **If no filter is found anywhere:** The finding was a test setup artifact. Do NOT add a filter. Write gate tests that confirm allies in blast zone ARE hit. Document in debrief that no code change was needed.
6. **If a filter IS found:** Remove it. Write gate tests that confirm removal.

### Target Lock

After this WO:
- Allied entities positioned within an AoE blast zone ARE included in `affected_entities`
- No allegiance/team/faction filter exists in the AoE resolution path
- Gate tests HG-C-001 through HG-C-004 pass

### Binary Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Filter removal | Remove if found; no-op if not found | PHB has no friendly-fire exemption for AoE spells |
| Caster self-damage | Caster included only if in blast area (not caster of a self-targeted cone starting at them) | Handled by WO-A (origin square fix). Separate concern. |

### Gate Tests (minimum 4)

| ID | Test | Pass condition |
|----|------|----------------|
| HG-C-001 | AoE burst: ally entity positioned inside blast radius → in `affected_entities` | ally_id in resolution.affected_entities |
| HG-C-002 | AoE burst: ally entity positioned outside blast radius → NOT in `affected_entities` | ally_id not in resolution.affected_entities |
| HG-C-003 | AoE cone: ally entity in cone area → in `affected_entities` | ally_id in resolution.affected_entities |
| HG-C-004 | Enemy entity in blast → in `affected_entities` (regression) | enemy_id in resolution.affected_entities |

---

## Section 0 — Debrief Focus

**For WO-C:** If no allegiance filter is found in code, the debrief must explicitly state: (1) where the builder looked, (2) what was confirmed absent, (3) what test setup Anvil likely used that produced the false observation. Gate tests must still be written and pass.

**For WO-B:** Debrief must address FINDING-HG-HEALING-NOOP-001 (CLW on living emits no hp_changed). If the root cause is the same as CLW-undead, fix both and document. If separate, file a new finding.

---

## Integration Seams

| Component | File | Notes |
|-----------|------|-------|
| `rasterize_cone()` | `aidm/core/aoe_rasterizer.py` | Add origin prepend |
| `rasterize_line()` | `aidm/core/aoe_rasterizer.py` | Add origin prepend |
| `TargetStats` | `aidm/core/spell_resolver.py:339` | Add `creature_type` field |
| `_create_target_stats()` | `aidm/core/play_loop.py:219` | Populate `creature_type` from entity dict |
| `_resolve_healing()` | `aidm/core/spell_resolver.py:893` | Add undead branch |
| `Event` constructor | `aidm/core/event_log.py` | `Event(event_id=, event_type=, timestamp=, payload=)` — NOT `id=, type=, data=` |
| `EF.*` | `aidm/schemas/entity_fields.py` | Builder must locate exact creature_type field name |

---

## Out of Scope

- Undead immunity to mind-affecting spells — separate concern
- AoE reflex saves for allies — existing save logic handles this, not this WO
- Selective spell feat (excludes chosen creatures from AoE) — future WO
- Improvised weapons (HG-F006) — separate WO
- ReadyIntent (HG-F001) — backlog

---

## Debrief Required

**File to:** `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-HOOLIGAN-TIER-A-001.md`

**Pass 1 — Context dump:**
- List every file modified with line ranges (per WO-A, WO-B, WO-C)
- WO-C: explicitly state whether allegiance filter was found in code or not
- WO-B: state exact creature_type field name found on entity dict; state whether FINDING-HG-HEALING-NOOP-001 shares root cause
- Confirm gate counts per sub-WO

**Pass 2 — PM summary ≤100 words**

**Pass 3 — Retrospective:**
- Any collateral impact from origin square fix (WO-A) on existing spell tests?
- CLW undead: did the fix also resolve FINDING-HG-HEALING-NOOP-001?

**Radar (one line each):**
- Regression gate: PASS (count before vs after)
- HG-A-001–004: all PASS
- HG-B-001–005: all PASS
- HG-C-001–004: all PASS
- Origin square in cone/line rasterizer: CONFIRMED
- `TargetStats.creature_type` field added: CONFIRMED
- CLW on undead emits hp_changed damage event: CONFIRMED
- No allegiance filter in AoE path: CONFIRMED (or: filter removed, state location)
- FINDING-HG-HEALING-NOOP-001: CLOSED or NEW FINDING filed

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Drafted: 2026-02-25 — Slate*
