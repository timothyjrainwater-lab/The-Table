# Debrief: WO-ENGINE-PRECISE-SHOT-001
**Artifact ID:** DEBRIEF_WO-ENGINE-PRECISE-SHOT-001
**WO:** WO-ENGINE-PRECISE-SHOT-001
**Batch:** P
**Commit:** e39c921
**Date:** 2026-02-27
**Result:** ACCEPTED — 8/8 PS tests PASS

---

## Pass 1: Context Dump

**Target file:** `aidm/core/attack_resolver.py`

**Pre-existing audit:** `feat_resolver.py` contained `ignores_shooting_into_melee_penalty()` — a helper that returned True if attacker has `precise_shot` feat. This function was **never called** anywhere. The -4 ranged-into-melee penalty itself was also **not applied anywhere**. Both the penalty and the bypass were fully absent from the engine.

### New helper: `_is_target_in_melee()`

Added to `attack_resolver.py` before `parse_damage_dice`:
```python
def _is_target_in_melee(target_id: str, attacker_team: str, world_state: "WorldState") -> bool:
    from aidm.schemas.position import Position
    target = world_state.entities.get(target_id)
    if target is None: return False
    target_pos_raw = target.get(EF.POSITION)
    if target_pos_raw is None: return False
    target_pos = Position(**target_pos_raw) if isinstance(target_pos_raw, dict) else target_pos_raw
    for eid, entity in world_state.entities.items():
        if eid == target_id: continue
        if entity.get(EF.DEFEATED, False): continue
        if entity.get(EF.TEAM, "") != attacker_team: continue
        pos_raw = entity.get(EF.POSITION)
        if pos_raw is None: continue
        pos = Position(**pos_raw) if isinstance(pos_raw, dict) else pos_raw
        if target_pos.is_adjacent_to(pos): return True
    return False
```

"In melee" = target has at least one **same-team (friendly)** non-defeated ally adjacent (8-directional, `|Δx| ≤ 1 and |Δy| ≤ 1`, not same square). This is the correct PHB interpretation: attacker's own allies are threatening the target.

### Penalty + bypass in `resolve_attack()`

Inserted after `_attacker_feats` is set, before `attack_bonus_with_conditions`:
```python
_ranged_into_melee_penalty = 0
if not is_melee and _is_target_in_melee(intent.target_id, attacker.get(EF.TEAM, ""), world_state):
    if "precise_shot" in _attacker_feats:
        events.append(Event(..., event_type="precise_shot_active",
            payload={"actor_id": intent.attacker_id}, ...))
        current_event_id += 1
    else:
        _ranged_into_melee_penalty = -4
```

Added `+ _ranged_into_melee_penalty` to `attack_bonus_with_conditions` sum.

### PS-001 test bug and fix

Initial PS-001 had archer with `feats=["precise_shot", "point_blank_shot"]` and target at (1,0) — within PBS 30 ft range. PBS applied +1 feat_modifier, making `total = 15 + BAB + 1 = 21` instead of expected 20. Fixed by removing `point_blank_shot` from PS-001 feats. PS-006 separately tests the PS + PBS combined case.

---

## Pass 2: PM Summary (≤100 words)

-4 ranged-into-melee penalty and Precise Shot bypass both freshly implemented. `_is_target_in_melee()` helper added to attack_resolver.py — checks for same-team non-defeated ally adjacent to target (8-dir). Dead code `ignores_shooting_into_melee_penalty()` in feat_resolver.py was NOT used. Penalty stored as `_ranged_into_melee_penalty` and applied additively in `attack_bonus_with_conditions`. `precise_shot_active` event emitted when feat bypasses penalty. PBS interaction unaffected (separate feat_modifier path). PS-001 test bug (spurious PBS bonus) fixed. 8/8 PS gates pass.

---

## Pass 3: Retrospective

**Adjacency definition:** `Position.is_adjacent_to()` uses 8-directional check (`|Δx| ≤ 1 and |Δy| ≤ 1`, same-position excluded). This is the same adjacency logic used by flanking (Batch C Cleave WO). Consistent across engine.

**"In melee" = friendly adjacency:** PHB p.140 says -4 when firing into a melee — meaning allied creatures adjacent to target. NOT enemy creatures adjacent to target (which would be the case for cover/flanking checks). The helper correctly checks `entity.get(EF.TEAM, "") != attacker_team` (i.e., SAME team as attacker = ally).

**Dead code in feat_resolver.py:** `ignores_shooting_into_melee_penalty()` exists but is never called. Could be wired to `_is_target_in_melee` in the future, or removed. Does not affect behavior.

**Precise Shot feat string:** `"precise_shot"` — lowercase underscore. Confirmed against FEAT_REGISTRY.

**Point Blank Shot interaction:** PBS +1/+1 comes from `get_attack_modifier()` via `feat_context` (range distance ≤ 30 ft). Independent of the ranged-into-melee path. PS-006 confirms both apply when present (PBS +1 feat_modifier + no -4 penalty).

**`_ranged_into_melee_penalty` naming:** Mirrors `_combat_expertise_penalty` pattern (Batch C). Additive modifier applied once in `attack_bonus_with_conditions`.

---

## Radar

| Finding | Severity | Status |
|---------|----------|--------|
| FINDING-ENGINE-PRECISE-SHOT-FEAT-RESOLVER-DEAD-CODE-001 | LOW | OPEN — `ignores_shooting_into_melee_penalty()` in feat_resolver.py is dead code. Never called. The -4 penalty check lives entirely in attack_resolver.py. Future cleanup: remove dead code or wire helper. No functional impact. |
