# DEBRIEF — WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001

**Verdict:** PASS [8/8 + 1 bonus boundary]
**Gate:** ENGINE-BARBARIAN-FAST-MOVEMENT
**Date:** 2026-02-26

## Pass 1 — Per-File Breakdown

**`aidm/schemas/entity_fields.py`**
Added `FAST_MOVEMENT_BONUS = "fast_movement_bonus"` and `ARMOR_TYPE = "armor_type"` (lines 301-308). `ARMOR_TYPE` confirmed not pre-existing — added as new constant. `ARMOR_AC_BONUS` also added (shared with Monk WIS-AC WO, same builder pass).

**`aidm/chargen/builder.py`**
`EF.FAST_MOVEMENT_BONUS = 10` set for barbarian class at both single-class path (line 930) and multiclass path (line 1115). Non-barbarian entities default to 0 via `.get()` pattern. `EF.ARMOR_TYPE` set from catalog at chargen alongside `EF.ARMOR_AC_BONUS`.

**`aidm/core/movement_resolver.py`**
Fast Movement logic added after `speed_ft = entity.get(EF.BASE_SPEED, 30)` read (lines 232-237):
```python
# WO-ENGINE-BARBARIAN-FAST-MOVEMENT-001: Fast Movement (PHB p.26)
_fast_movement = entity.get(EF.FAST_MOVEMENT_BONUS, 0)
if _fast_movement > 0:
    _armor_type = entity.get(EF.ARMOR_TYPE, "none")
    if _armor_type != "heavy":
        speed_ft += _fast_movement
        # Note: heavy load check deferred — item_catalog not available in this call path
```
Encumbrance load check deferred — item_catalog not available in movement_resolver call context. Armor check only applied. Documented in code comment.

**`tests/test_engine_barbarian_fast_movement_001_gate.py`** — NEW
FM-001 through FM-008 all pass plus one bonus boundary test (9 total collected). Coverage: no armor +10 (FM-001), light armor +10 (FM-002), medium armor +10 (FM-003), heavy armor blocked (FM-004), non-barbarian no bonus (FM-005), multiclass barbarian +10 (FM-006), chargen flag set (FM-007), non-barbarian chargen 0 (FM-008), boundary test confirming 30+10=40 for human barbarian.

**PHB note confirmed:** Fast Movement applies in no armor, light armor, OR medium armor. Blocked by heavy only. Correctly implemented — not the same restriction as Monk WIS-to-AC (unarmored only).

**Open Finding:** Heavy load encumbrance check deferred — item_catalog not available in movement_resolver. Armor check only. Document as FINDING-ENGINE-FASTMOVEMENT-LOAD-001.

## Pass 2 — PM Summary (≤100 words)

Barbarian Fast Movement fully wired. `EF.FAST_MOVEMENT_BONUS = 10` set at chargen for barbarians (single-class and multiclass). movement_resolver applies +10 after BASE_SPEED read, blocked only by `armor_type == "heavy"` — light and medium armor correctly pass per PHB p.26. New EF constants `FAST_MOVEMENT_BONUS` and `ARMOR_TYPE` added. Encumbrance load check deferred — no catalog in call path. 8/8 + 1 bonus boundary test pass.

## Pass 3 — Retrospective

**Drift caught:** Spec correctly flagged the PHB distinction between Fast Movement (light + medium armor OK) and Monk WIS-to-AC (unarmored only). Builder confirmed the difference was correctly implemented — different armor conditions, different WOs, different behaviors.

**Patterns:** `EF.ARMOR_TYPE` is now a shared infrastructure field used by both Monk WIS-AC and Barbarian Fast Movement. It will also serve the Evasion armor restriction enforcement WO when that ships. Single chargen write, multiple runtime reads — clean.

**Encumbrance deferral pattern:** The spec gave explicit guidance ("if catalog not available, document as deferred finding, use armor check only"). Builder followed precisely. This is the correct pattern for features with partial enforcement paths.

**Open findings:**
| ID | Severity | Description |
|----|----------|-------------|
| FINDING-ENGINE-FASTMOVEMENT-LOAD-001 | LOW | Heavy load should block Fast Movement per PHB p.26; item_catalog not available in movement_resolver call path; armor check only enforced |

## Radar

- ENGINE-BARBARIAN-FAST-MOVEMENT: 8/8 + 1 bonus boundary PASS
- `EF.ARMOR_TYPE` now exists — enables Evasion armor restriction, Monk armor checks, future armor-conditional WOs
- PHB distinction confirmed: Fast Movement = no/light/medium OK; heavy blocked (not same as Monk unarmored-only)
- Dwarf base speed (20 ft) + 10 = 30 ft confirmed correct per PHB p.26 footnote
- FINDING-ENGINE-FASTMOVEMENT-LOAD-001: LOW, OPEN
- Zero new failures in full regression
