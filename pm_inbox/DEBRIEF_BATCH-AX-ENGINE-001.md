# DEBRIEF: BATCH-AX-ENGINE-001

**Lifecycle:** ACTIONED
**Commit:** ba5967a (engine(AX): maneuver condition modifiers + requires_attack_roll CONSUME_DEFERRED — 12/12 gates)
**WOs:** WO-ENGINE-MANEUVER-CONDITION-MODIFIER-001 (MCM-001..008), WO-ENGINE-REQUIRES-ATTACK-ROLL-DEAD-FIELD-001 (RAD-001..004)
**Gates:** 12/12 pass
**Suite:** 0 new regressions (194 pre-existing ws_bridge/UI failures confirmed by git stash regression check)
**Verdict Review Class:** SELF-REVIEW (bounded scope — 6 resolver function insertions + comment-only WO; no architectural change)

---

## Ghost Check Results

### WO1 (MCM): WO-ENGINE-MANEUVER-CONDITION-MODIFIER-001
1. **Coverage map:** Maneuver checks — condition modifiers row: NOT PRESENT → genuine gap.
2. **WO annotation grep:** `grep "WO-ENGINE-MANEUVER-CONDITION-MODIFIER" maneuver_resolver.py` → 0 results. No prior fix.
3. **Gate file:** `tests/test_engine_maneuver_condition_modifier_001_gate.py` did not exist. No prior delivery.

**Result: genuine gap — proceed.**

### WO2 (RAD): WO-ENGINE-REQUIRES-ATTACK-ROLL-DEAD-FIELD-001
1. **Coverage map:** TOUCH/RAY row status already PARTIAL — matches WO expectation (comment-only WO does not change status).
2. **WO annotation grep:** `grep "CONSUME_DEFERRED" spell_resolver.py` → 0 results before edit. No prior comment.
3. **Gate file:** `tests/test_engine_requires_attack_roll_dead_field_001_gate.py` did not exist. No prior delivery.

**Result: genuine gap — proceed.**

---

## Pass 1 — Context Dump

### WO1: WO-ENGINE-MANEUVER-CONDITION-MODIFIER-001

**Import change — `aidm/core/maneuver_resolver.py:52`:**

Before:
```python
from aidm.core.conditions import apply_condition, remove_condition
```

After:
```python
from aidm.core.conditions import apply_condition, remove_condition, get_condition_modifiers
```

**Representative resolver — `resolve_grapple` (before/after at lines 1819–1834):**

Before (lines 1819–1829 pre-edit):
```python
    attacker_grapple_modifier = (
        attacker_bab + attacker_str_mod + attacker_size_modifier + feat_bonus
    )
    defender_grapple_modifier = (
        defender_bab + defender_str_mod + defender_size_modifier
    )

    opposed = _roll_opposed_check(rng, attacker_grapple_modifier, defender_grapple_modifier, "grapple")
```

After (lines 1819–1835):
```python
    attacker_grapple_modifier = (
        attacker_bab + attacker_str_mod + attacker_size_modifier + feat_bonus
    )
    defender_grapple_modifier = (
        defender_bab + defender_str_mod + defender_size_modifier
    )

    # Condition modifiers — PHB: condition penalties apply to maneuver checks (WO-ENGINE-MANEUVER-CONDITION-MODIFIER-001)
    attacker_cond = get_condition_modifiers(world_state, attacker_id, context="attack")
    defender_cond = get_condition_modifiers(world_state, target_id, context="defense")
    attacker_grapple_modifier += attacker_cond.attack_modifier
    defender_grapple_modifier += defender_cond.attack_modifier

    opposed = _roll_opposed_check(rng, attacker_grapple_modifier, defender_grapple_modifier, "grapple")
```

**Pattern match — `resolve_manyshot()` at `attack_resolver.py:2446-2447`:**
```python
attacker_modifiers = get_condition_modifiers(world_state, intent.attacker_id, context="attack")
defender_modifiers = get_condition_modifiers(world_state, intent.target_id, context="defense")
```
Maneuver pattern matches: same import, same function signature, same `context="attack"` / `context="defense"` strings. Confirmed parity.

**All 6 resolver insertion points:**

| Resolver | Function def line | Insertion lines |
|----------|------------------|-----------------|
| `resolve_bull_rush` | 242 | 321–325 |
| `resolve_trip` | 514 | 643–647 |
| `resolve_overrun` | 894 | 999–1003 |
| `resolve_sunder` | 1202 | 1278–1282 |
| `resolve_disarm` | 1423 | 1538–1542 |
| `resolve_grapple` | 1712 | 1823–1827 |

**MCM-002 result: shaken attacker — bull rush roll total:**
Shaken attacker (str_mod=2, size=0, shaken attack_modifier=-2):
- Pre-fix: `attacker_modifier = 2+0 = 2`
- Post-fix: `attacker_modifier = 2+0 + (-2) = 0`
MCM-002 asserts `event.payload["attacker_modifier"] == 0`. PASS.

**`resolve_attack()` unchanged:** MCM-007 confirmed — `resolve_attack` with shaken attacker returns `condition_modifier==-2` in attack_roll payload. No modifications to `attack_resolver.py`.

---

### WO2: WO-ENGINE-REQUIRES-ATTACK-ROLL-DEAD-FIELD-001

**`requires_attack_roll` field declaration — `aidm/core/spell_resolver.py:174–176`:**

Before:
```python
    requires_attack_roll: bool = False
    """Whether spell requires an attack roll (touch/ray)."""
```

After:
```python
    requires_attack_roll: bool = False
    # CONSUME_DEFERRED — not read by SpellResolver. TOUCH/RAY attack roll not yet implemented. See FINDING-AUDIT-SPELL-012-REQUIRES-ATTACK-ROLL-DEAD-001.
    """Whether spell requires an attack roll (touch/ray)."""
```

**Gap-site comment — `aidm/core/spell_resolver.py:709–712`:**

Before:
```python
        elif intent.target_entity_id is not None:
            # Single target spells
            affected_entities = [intent.target_entity_id]
```

After:
```python
        elif intent.target_entity_id is not None:
            # Single target spells
            # CONSUME_DEFERRED — requires_attack_roll not gated here. TOUCH/RAY spells resolve without attack roll per FINDING-AUDIT-SPELL-012-REQUIRES-ATTACK-ROLL-DEAD-001. Implement touch attack roll when Phase 2 spell resolution WO is dispatched.
            affected_entities = [intent.target_entity_id]
```

**RAD-003 — 2 spells with `requires_attack_roll=True`:**
Confirmed from `SPELL_REGISTRY`: `shocking_grasp` (TOUCH, requires_attack_roll=True) and `scorching_ray` (RAY, requires_attack_roll=True). At least 2 present.

**RAD-004 — No conditional logic on `requires_attack_roll`:**
grep `spell_resolver.py` for `if.*requires_attack_roll` → 0 results. Comment-only WO confirmed. TOUCH spells still resolve to hit without attack roll — existing behavior preserved.

---

## PM Acceptance Notes Responses

### WO1 (MCM):
- **Ghost check result:** Genuine gap confirmed — no prior fix, no annotation comment, no gate file.
- **`resolve_grapple` before/after:** Shown above — attacker_cond + defender_cond lines inserted before `_roll_opposed_check()`.
- **Pattern match vs `resolve_manyshot()`:** Identical function call signature, same context strings. Confirmed.
- **All 6 resolvers modified:** Listed by file:line in table above.
- **MCM-002 result:** `attacker_modifier == 0` (str_mod=2, shaken=-2). PASS.
- **`resolve_attack()` unchanged:** MCM-007 regression gate passes.

### WO2 (RAD):
- **`requires_attack_roll` field with CONSUME_DEFERRED comment:** `spell_resolver.py:174–175`. Shown above.
- **Gap-site comment in `resolve_spell()`:** `spell_resolver.py:711`. Comment-only — no conditional logic added.
- **RAD-003 — 2 spells with `requires_attack_roll=True`:** `shocking_grasp`, `scorching_ray`.
- **RAD-004 — No behavior regression:** No `if.*requires_attack_roll` branch in source. TOUCH spells still resolve without attack roll.

---

## Pass 2 — PM Summary (100 words)

WO1 genuine gap. `get_condition_modifiers()` inserted in all 6 maneuver resolvers — import at line 52, 2-call blocks at bull_rush:321, trip:643, overrun:999, sunder:1278, disarm:1538, grapple:1823. Pattern matches `resolve_manyshot()` canonical. Shaken attacker MCM-002: `attacker_modifier=0` (str_mod=2 − 2). All 8/8 MCM gates pass. WO2 comment-only: CONSUME_DEFERRED at `spell_resolver.py:175` (field declaration) and `spell_resolver.py:711` (gap site). RAD-003 confirms ≥2 TOUCH/RAY spells present; RAD-004 confirms no conditional branch added. 4/4 RAD pass. Suite: 9378 pass, 194 pre-existing failures (ws_bridge/UI) confirmed by git stash regression test. Gate total: **1,698**.

---

## Pass 3 — Retrospective

**WO1 field name correction:**
WO spec referenced `attacker_modifiers.attack_bonus` but actual `ConditionModifiers` field is `attack_modifier` (confirmed via `grep -n "attack_modifier\|attack_bonus" aidm/schemas/conditions.py`). Used correct field name; no runtime impact. Low-severity documentation inaccuracy in WO spec.

**Grapple variable name divergence:**
Grapple uses `attacker_grapple_modifier` / `defender_grapple_modifier` rather than `attacker_modifier` / `defender_modifier` (same as other 5 resolvers). Detected by reading local context before editing — no logic error introduced.

**Out-of-scope findings:**
- None identified. No new findings during gate writing or code inspection.

**Kernel touches:**
- This WO touches KERNEL-01 (Combat Core) — maneuver opposed check path now receives condition modifier wiring matching canonical attack path. Full parity with resolve_attack + resolve_manyshot + resolve_nonlethal_attack confirmed.

---

## Radar — Findings

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| FINDING-ENGINE-MANEUVER-CONDITION-MODIFIER-001 | All 6 maneuver resolvers silently ignored condition modifiers (shaken/frightened/prone) on opposed checks | MEDIUM | CLOSED (WO1, Batch AX, commit ba5967a) |
| FINDING-AUDIT-SPELL-012-REQUIRES-ATTACK-ROLL-DEAD-001 | `requires_attack_roll` set on TOUCH/RAY spells but never read by SpellResolver | MEDIUM | CLOSED (WO2 comment-only, Batch AX, commit ba5967a) |

---

## Coverage Map Updates

**Updated rows (`docs/ENGINE_COVERAGE_MAP.md`):**
- New row inserted (after Trip counter-trip): Maneuver checks — condition modifiers (shaken/frightened/prone): NOT PRESENT → **IMPLEMENTED**. `maneuver_resolver.py` — `get_condition_modifiers()` wired for attacker + defender in all 6 resolvers. WO-ENGINE-MANEUVER-CONDITION-MODIFIER-001. MCM-001..008. Batch AX.
- No change to TOUCH/RAY row (remains PARTIAL — WO2 is documentation only, implementation status unchanged).

---

## ML Preflight Checklist

| Check | WO1 (MCM) | WO2 (RAD) |
|-------|-----------|-----------|
| ML-001: No bare string literals (EF.* used) | `attacker_id` / `target_id` passed from entity dicts; conditions extracted via `get_condition_modifiers(world_state, entity_id)` — no bare strings | Comment-only — no EF field changes |
| ML-002: All call sites identified | 6 resolvers identified; `resolve_attack()` confirmed unchanged; no other maneuver dispatch paths | Single field declaration + single `spell_resolver` comment site |
| ML-003: No float in deterministic path | Integer `attack_modifier` only | No computation |
| ML-004: json.dumps sort_keys if any | N/A | N/A |
| ML-005: No WorldState mutation in resolver | Resolvers return events only; no WS mutation | Comment-only |
| ML-006: Coverage map updated | ✅ New maneuver condition modifier row added: IMPLEMENTED | N/A (PARTIAL preserved, gap documented) |

---

## Consume-Site Confirmation

### WO1 (MCM):
- **Write site:** `maneuver_resolver.py:52` — `get_condition_modifiers` added to import
- **Write site (6×):** Lines 323–325, 645–647, 1001–1003, 1280–1282, 1540–1542, 1825–1827 — attacker + defender condition modifiers accumulated into roll totals
- **Read site:** `_roll_opposed_check(rng, attacker_modifier, defender_modifier, check_type)` — receives post-condition totals
- **Observable effect:** Shaken attacker's bull rush roll is −2; frightened defender's grapple defense is −2; prone attacker's trip roll is −4
- **Gate proof:** MCM-002 (shaken −2), MCM-003 (frightened −2), MCM-004 (shaken defender −2), MCM-005 (prone −4), MCM-006 (all 6 maneuver types)

### WO2 (RAD):
- **Write site:** `spell_resolver.py:175` — CONSUME_DEFERRED comment at field declaration
- **Write site:** `spell_resolver.py:711` — CONSUME_DEFERRED comment at gap site
- **Read site:** None (comment-only WO — field intentionally not consumed until Phase 2)
- **Observable effect:** Future builders cannot assume `requires_attack_roll` gates resolver behavior
- **Gate proof:** RAD-001 (comment within 5 lines of field), RAD-002 (both keywords on same comment line at gap site), RAD-003 (≥2 TOUCH/RAY spells still present), RAD-004 (no conditional branch added)

**Post-AX gate count:** 1,686 (post-AW) + 8 (MCM) + 4 (RAD) = **1,698**
**Sweep:** 4/5.
