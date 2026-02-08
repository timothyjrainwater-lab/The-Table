# CP-20 — Discrete Environmental Damage & Contact Hazards
## Implementation Packet (AUTHORITATIVE)

**Project:** AIDM — Deterministic D&D 3.5e Engine
**CP ID:** CP-20
**Status:** READY FOR IMPLEMENTATION (Upon Authorization)
**Date:** 2026-02-08
**Depends on:** CP-19 (Environment & Terrain), CP-15 (AoO), CP-16 (Conditions)
**Capability Gates:** G-T1 ONLY
**Audience:** Implementing Agent(s)

---

## 1. PURPOSE

This packet authorizes and defines implementation of **discrete environmental
damage hazards** that trigger on **contact or entry**, extending CP-19 terrain
mechanics without introducing persistence, time advancement, or relational state.

---

## 2. SCOPE (STRICT)

### 2.1 In Scope

- Fire squares
- Acid pools (shallow)
- Lava edges (entry-based)
- Spiked pits (on fall entry)
- Integration with forced movement (Bull Rush, Overrun)

### 2.2 Explicitly Out of Scope

- Ongoing damage
- Burning, acid exposure over time
- Environmental conditions (smoke, heat)
- Saving throws (unless explicitly specified later)
- Spell-created hazards
- Terrain modification

---

## 3. FILE TOUCH BOUNDARY

### Files You MAY Create

- `aidm/core/environmental_damage_resolver.py`
- `tests/test_environmental_damage_cp20.py`

### Files You MAY Modify

- `aidm/core/terrain_resolver.py`
- `aidm/core/maneuver_resolver.py` (integration only)

### Files You MUST NOT Touch

- `play_loop.py`
- Any schema files
- Any unrelated resolvers

---

## 4. HAZARD MODEL

### 4.1 Hazard Types

| Hazard | Trigger | Damage |
|------|--------|--------|
| Fire square | Enter | 1d6 fire |
| Acid pool | Enter | 1d6 acid |
| Lava edge | Enter | 2d6 fire |
| Spiked pit | Fall | Fall + 1d6 piercing |

All hazards resolve **once per trigger**.

---

## 5. RESOLUTION ORDER (MANDATORY)

1. AoOs (unchanged)
2. Movement or forced movement
3. Terrain hazard detection
4. Environmental damage resolution
5. Event emission

---

## 6. RNG RULES

- RNG used only for:
  - Environmental damage dice
- RNG stream:
  - `"combat"` ONLY
- No new RNG streams permitted

---

## 7. EVENT REQUIREMENTS

All hazard resolutions must emit explicit events:

```json
{
  "event_type": "environmental_damage",
  "entity_id": "string",
  "hazard_type": "fire|acid|lava|spiked_pit",
  "dice": "1d6|2d6",
  "damage_type": "fire|acid|piercing",
  "damage_total": int
}
```

No state mutation occurs outside event application.

---

## 8. TESTING REQUIREMENTS

### Tier-1 Tests

* Entering fire square applies 1d6 fire
* Forced movement into acid applies 1d6 acid
* Falling into spiked pit applies fall + piercing
* Lava edge entry applies 2d6 fire

### Determinism Tests

* 10× identical replay produces identical hashes

---

## 9. ACCEPTANCE CRITERIA

* All hazards trigger correctly
* No persistence introduced
* No gate violations
* All tests pass
* Runtime < 2s

---

## 10. ESCALATION CONDITIONS

Stop and escalate if:

* Hazard requires persistence
* Hazard requires saving throws
* Any gate boundary becomes unclear
* Any additional file touch appears necessary

---

## 11. COMPLETION DIRECTIVE

Once implemented and verified:

* Mark CP-20 COMPLETE
* Update Rules Coverage Ledger
* Proceed to kernel work (SKR-005)

---

## END OF CP-20 IMPLEMENTATION PACKET
