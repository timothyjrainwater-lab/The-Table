# CP-19 IMPLEMENTATION PACKET (FINAL)
**Status:** FINAL — Implementation complete
**Date:** 2026-02-08
**Depends on:** CP-15, CP-16, CP-18, CP-18A
**Governance:** Determinism threat model applies
**Completion:** 730 tests passing (728 baseline + 2 CP-19B patch)

CP‑19 implementation is **complete** and **FROZEN**.

---

## 0) Purpose
Constrain implementation of **CP‑19 (Environment & Terrain)** as a **minimal, deterministic, gate-safe** extension:
- difficult terrain + movement restrictions
- cover (+4/+8/total, soft cover)
- higher ground (+1 melee)
- falling damage (1d6 / 10ft, max 20d6)
- forced movement interactions (pits/ledges)
- degraded shallow water + degraded steep slopes placeholders

---

## 1) Authoritative Inputs (binding once authorized)
1. `docs/CP19_ENVIRONMENT_TERRAIN_DECISIONS.md`
2. `docs/DETERMINISM_THREAT_MODEL_CP18_CP19.md`
3. Gate status from `PROJECT_STATE_DIGEST.md` (Tier‑1 only)

---

## 2) File‑Level Touch Map (proposed)

### 2.1 Create
| File | Purpose |
|------|---------|
| `aidm/core/terrain_resolver.py` | Terrain queries + movement cost + hazard checks + cover/elevation helpers |
| `tests/test_terrain_cp19_core.py` | Tier‑1 unit tests |
| `tests/test_terrain_cp19_integration.py` | Tier‑2 integration tests |

### 2.2 Modify (expected)
| File | Change |
|------|--------|
| `aidm/schemas/terrain.py` | Extend `TerrainCell` as specified |
| `aidm/schemas/entity_fields.py` | Add CP‑19 fields if absent |
| `aidm/core/aoo.py` | Cover can block AoO execution (scope item) |
| `aidm/core/maneuver_resolver.py` | Forced movement hazard checks integration |

---

## 3) Determinism Requirements (hard)
Global rules: fixed RNG stream/order, deterministic event ordering, no unordered iteration

CP‑19 specific:
- Forced movement path ambiguity resolved deterministically
- No terrain-dependent branch explosion
- Falling ordering: AoOs → movement → fall resolution
- No terrain RNG leakage; only falling damage uses `"combat"` stream

---

## 4) Gate Safety (hard)
No persistent terrain, no hazard entities, no permanent stats, no relational terrain effects.

---

## 5) Acceptance Checklist (draft)
### Functional
- [ ] Difficult terrain movement multiplier applied deterministically
- [ ] Run/charge/5-foot-step restrictions enforced
- [ ] Cover modifiers correct; total cover blocks targeting
- [ ] Soft cover supported
- [ ] Higher ground grants +1 melee only
- [ ] Falling damage uses `"combat"` RNG, 1d6/10ft max 20d6
- [ ] Forced movement into pit/ledge triggers falling; hazard events emitted

### Determinism / Replay
- [ ] 10× replay identical state hashes scenario exists

---
**End (draft).**
