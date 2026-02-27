# DEBRIEF — BATCH V ENGINE (WO1/WO2/WO3)

**Commits:** `3b8f774` (V-WO2) | `f2acd12` (V-WO1) | `147219b` (V-WO3)
**Date:** 2026-02-27
**Batch:** V — Action Economy + Domain Foundation
**Lifecycle:** ARCHIVE

---

## Pass 1 — Context Dump

### Commit Order
WO2 → WO1 → WO3 (per dispatch spec).

---

### V-WO2 — ENGINE-AE-DEAD-MODULE-001

**Gap verified:** `aidm/combat/action_economy.py` existed as a CP-24-era parallel copy of `aidm/core/action_economy.py`. Missing `immediate_used` field and `pending_swift_burn` mechanism. Grep confirmed zero production imports.

**Files deleted:**
- `aidm/combat/action_economy.py`

**Files modified:**
- `aidm/combat/__init__.py` — no change needed (comment-only, no re-exports)

**Files created:**
- `tests/test_engine_ae_dead_module_gate.py` — AE-DEAD-001–002

**Gate:** AE-DEAD-001–AE-DEAD-002: **2/2 PASS**

**Parallel paths:** N/A (deletion WO). Confirmed no consumer.

---

### V-WO1 — ENGINE-AE-INTENT-MAPPING-001

**Gap verified:** `action_economy.py`'s `_build_action_types()` was missing 6 intent class entries. `FullMoveIntent` fell through to `"free"` — voice-path movement never consumed the move slot (FINDING-AUDIT-AE-002 MEDIUM).

**Files modified:**

| File | Lines | Change |
|------|-------|--------|
| `aidm/core/action_economy.py` | `_build_action_types()` | +7 lines: 6 `_try_add` entries |

**Entries added:**
```python
_try_add(mapping, "aidm.schemas.attack", "FullMoveIntent", "move")
_try_add(mapping, "aidm.schemas.intents", "NaturalAttackIntent", "standard")
_try_add(mapping, "aidm.schemas.intents", "BardicMusicIntent", "standard")
_try_add(mapping, "aidm.schemas.intents", "WildShapeIntent", "standard")
_try_add(mapping, "aidm.schemas.intents", "RevertFormIntent", "standard")
_try_add(mapping, "aidm.schemas.intents", "DemoralizeIntent", "standard")
```

**Assumptions validated:**
1. `FullMoveIntent` in `aidm.schemas.attack` — confirmed
2. Others (`NaturalAttackIntent`, `BardicMusicIntent`, `WildShapeIntent`, `RevertFormIntent`, `DemoralizeIntent`) in `aidm.schemas.intents` — confirmed
3. Gate uses `get_action_type(instance)` (not string names) — confirmed, `_ACTION_TYPES` reset before each test
4. `RageIntent` defaults to `"free"` — correct per PHB p.25, not added

**Files created:**
- `tests/test_engine_ae_intent_mapping_gate.py` — AE-MAPPING-001–006

**Gate:** AE-MAPPING-001–AE-MAPPING-006: **6/6 PASS**

**Parallel paths:** `ACTION_TYPES` is the single lookup table. `get_action_type(intent)` is the single caller entry point. No parallel intent→slot resolution path exists.

---

### V-WO3 — ENGINE-DOMAIN-SYSTEM-001

**Gap verified:** `EF.DOMAINS` absent from entity_fields.py. `build_character()` had no `domains` parameter. `TurnUndeadIntent` had no `greater_turning` field. `turn_undead_resolver.py` had "Domain bonuses" listed in DEFERRED.

**Files modified:**

| File | Change |
|------|--------|
| `aidm/schemas/entity_fields.py` | Added `DOMAINS = "domains"` in Turn Undead section |
| `aidm/chargen/builder.py` | Added `domains` param to `build_character()`; wired `entity[EF.DOMAINS] = list(domains) if domains else []` after turn undead block |
| `aidm/schemas/intents.py` | `TurnUndeadIntent`: added `greater_turning: bool = False`; updated `to_dict()` and `from_dict()` |
| `aidm/core/turn_undead_resolver.py` | Added `_greater_turning_active` check; "turned" outcomes emit `"undead_destroyed_by_greater_turning"` when active; state applicator handles new event type |

**Integration seam decision:** Used `"undead_destroyed_by_greater_turning"` as distinct event type (not payload flag) for maximum gate visibility. State applicator handles it identically to `"undead_destroyed"` (DEFEATED=True, HP=-10).

**Assumptions validated:**
1. `TurnUndeadIntent` dataclass — `greater_turning: bool = False` added with `__post_init__` unchanged (only validates cleric_id and target_ids)
2. ChargenParams — `build_character()` directly; `domains=None` → `[]`
3. `turn_undead_resolver.py` receives entity with `EF.DOMAINS` in scope (reads from WorldState entities dict)
4. Greater Turning uses same turn check and HP budget as regular turning — only outcome differs. Confirmed.

**Files created:**
- `tests/test_engine_domain_system_gate.py` — DOMAIN-001–006

**Gate:** DOMAIN-001–DOMAIN-006: **6/6 PASS**

**Parallel paths:** `turn_undead_resolver.py` is the single turn resolution path (confirmed AE audit). No secondary resolver path exists.

**Future domain power WOs:** builder logged in Pass 3 below.

---

## Pass 2 — PM Summary

Batch V: 3 WOs, all PASS. V-WO2 deleted a stale CP-24 parallel copy of action_economy. V-WO1 fixed 6 missing intent mappings — most critically FullMoveIntent was silently eating no action slot (FINDING-AUDIT-AE-002 MEDIUM, CLOSED). V-WO3 laid the domain system foundation: EF.DOMAINS field, chargen wire, TurnUndeadIntent.greater_turning flag, and Sun domain Greater Turning (PHB p.33) destroying turned undead. Gates: 2+6+6 = 14/14 PASS. Zero new failures.

---

## Pass 3 — Retrospective

**Out-of-scope findings:**

| ID | Severity | Source | Notes |
|----|----------|--------|-------|
| FINDING-ENGINE-DOMAIN-FIRE-RESIST-001 | LOW OPEN | V-WO3 recon | `fire_resistance` from Fire domain, `animal_friendship` from Animal domain, etc. — domain power WOs needed after this WO establishes EF.DOMAINS. Not implemented here. |
| FINDING-ENGINE-DOMAIN-MAX-TWO-001 | LOW OPEN | V-WO3 recon | PHB p.32 restricts clerics to ≤2 domains. `build_character()` does not enforce this. Stored as `list(domains)` without length validation. Add validation as a future WO if desired. |

**Kernel touches:**
- This WO touches KERNEL-03 (Intent schema) — `TurnUndeadIntent.greater_turning` field added.
- This WO touches KERNEL-07 (Entity fields) — `EF.DOMAINS` added.
- This WO touches KERNEL-05 (Chargen) — `build_character()` signature extended.

**RAW Fidelity Audit updates (required on ACCEPT):**
- Section 11 (Action Economy): Add "Action economy intent mapping" row → FULL (FullMoveIntent/NaturalAttackIntent/etc.)
- New section or Section 15 Divine: Add "Domain system — EF.DOMAINS" → PARTIAL (Sun domain only), "Sun domain Greater Turning" → FULL

---

*Debrief filed by Chisel.*
