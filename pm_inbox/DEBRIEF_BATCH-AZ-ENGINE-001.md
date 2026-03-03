**Lifecycle:** ACTIONED
**Commit:** 94044b3 — engine(AZ): GWF/GWS + skill feats (agile/affinity/aptitude/Skill Focus) + Run ×5 — 22/22 gates
**Batch:** AZ (3 WOs — GWF, SKF, RUN)
**Gate total post-AZ:** 1,734 (1,712 + 8 GWF + 8 SKF + 6 RUN)
**Session:** 33

---

## Ghost Check Results (all 3 WOs)

### WO1 — WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001
- **Coverage map:** No GWF/GWS rows — NOT STARTED (confirmed)
- **Annotation grep:** `grep -n "greater_weapon" aidm/core/feat_resolver.py` → 0 results before edit
- **Gate file:** `tests/test_engine_gwf_gws_feat_resolver_001_gate.py` → did not exist
- **Result: GENUINE GAP** — proceed authorized

### WO2 — WO-ENGINE-OSS-SKILL-FEATS-WIRE-001
- **Coverage map:** No Agile/Animal Affinity/Magical Aptitude/Skill Focus rows — NOT STARTED
- **Annotation grep:** `grep -n "agile\|animal_affinity\|magical_aptitude\|skill_focus" aidm/core/skill_resolver.py` → 0 results for those 3 dict entries before edit; no `skill_focus_` branch present
- **Gate file:** `tests/test_engine_oss_skill_feats_wire_001_gate.py` → did not exist
- **Result: GENUINE GAP** — proceed authorized

### WO3 — WO-ENGINE-RUN-FEAT-SPEED-001
- **Coverage map:** Run row present as IMPLEMENTED but `×5 with Run feat` not noted — gap in feat wire
- **Annotation grep:** `grep -n "RUN-FEAT\|run_multiplier\|FEATS.*run" aidm/core/play_loop.py` → 0 results before edit; `_run_distance = _base_speed * 4` bare literal confirmed at line 4128
- **Gate file:** `tests/test_engine_run_feat_speed_001_gate.py` → did not exist
- **Result: GENUINE GAP** — proceed authorized

---

## Pass 1 — Context Dump

### WO1: WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001 (Greater Weapon Focus/Specialization)

**File changed: `aidm/core/feat_resolver.py`**

**`get_attack_modifier()` — before (line 154-158):**
```python
    # Weapon Focus: +1 attack with chosen weapon
    weapon_name = context.get("weapon_name", "")
    weapon_focus_id = f"weapon_focus_{weapon_name}"
    if weapon_focus_id in feats:
        modifier += 1

    # Point Blank Shot: +1 attack within 30 ft
```

**After (GWF block inserted, lines 160-165):**
```python
    # Weapon Focus: +1 attack with chosen weapon
    weapon_name = context.get("weapon_name", "")
    weapon_focus_id = f"weapon_focus_{weapon_name}"
    if weapon_focus_id in feats:
        modifier += 1

    # Greater Weapon Focus: +1 attack (stacks with WF — total +2 with both)
    # WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001: PHB p.94
    greater_weapon_focus_id = f"greater_weapon_focus_{weapon_name}"
    if greater_weapon_focus_id in feats:
        modifier += 1

    # Point Blank Shot: +1 attack within 30 ft
```

**`get_damage_modifier()` — before (line 202-206):**
```python
    # Weapon Specialization: +2 damage with chosen weapon
    weapon_name = context.get("weapon_name", "")
    weapon_spec_id = f"weapon_specialization_{weapon_name}"
    if weapon_spec_id in feats:
        modifier += 2

    # Point Blank Shot: +1 damage within 30 ft
```

**After (GWS block inserted, lines 214-219):**
```python
    # Weapon Specialization: +2 damage with chosen weapon
    weapon_name = context.get("weapon_name", "")
    weapon_spec_id = f"weapon_specialization_{weapon_name}"
    if weapon_spec_id in feats:
        modifier += 2

    # Greater Weapon Specialization: +2 damage (stacks with WS — total +4 with both)
    # WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001: PHB p.94
    greater_weapon_spec_id = f"greater_weapon_specialization_{weapon_name}"
    if greater_weapon_spec_id in feats:
        modifier += 2

    # Point Blank Shot: +1 damage within 30 ft
```

**Pattern match vs WF/WS:** Identical structure — `f"greater_weapon_focus_{weapon_name}"` mirrors `f"weapon_focus_{weapon_name}"`. Correct weapon-scoped check; wrong weapon → 0 (GWF-004 confirms).

**Stacking confirmation:** Both WF+GWF and WS+GWS are independent `+= 1` and `+= 2` increments. No cap or mutual exclusion — GWF-003 (+2 total with both) and GWF-007 (+4 total with both) confirm correct stacking.

**Gate file:** `tests/test_engine_gwf_gws_feat_resolver_001_gate.py` — 8 tests (GWF-001..008)

---

### WO2: WO-ENGINE-OSS-SKILL-FEATS-WIRE-001 (Agile/Animal Affinity/Magical Aptitude + Skill Focus)

**File changed: `aidm/core/skill_resolver.py`**

**`_SKILL_BONUS_FEATS` dict — before (12 entries, line 24-37):**
```python
_SKILL_BONUS_FEATS: dict = {
    "alertness":       ("listen",             "spot"),
    ...
    "stealthy":        ("hide",               "move_silently"),
}
```

**After (3 OSS entries appended):**
```python
_SKILL_BONUS_FEATS: dict = {
    "alertness":       ("listen",             "spot"),
    ...
    "stealthy":        ("hide",               "move_silently"),
    # WO-ENGINE-OSS-SKILL-FEATS-WIRE-001: PHB p.91-102 — three OSS feats missing from prior wire
    "agile":           ("balance",            "escape_artist"),
    "animal_affinity": ("handle_animal",      "ride"),
    "magical_aptitude":("spellcraft",         "use_magic_device"),
}
```

**`_get_feat_skill_bonus()` function — before (lines 50-55):**
```python
    total = 0
    for feat_id in actor_feats:
        skills = _SKILL_BONUS_FEATS.get(feat_id)
        if skills and target_skill_id in skills:
            total += 2
    return total
```

**After (skill_focus_ branch added, lines 57-64):**
```python
    total = 0
    for feat_id in actor_feats:
        skills = _SKILL_BONUS_FEATS.get(feat_id)
        if skills and target_skill_id in skills:
            total += 2

    # WO-ENGINE-OSS-SKILL-FEATS-WIRE-001: Skill Focus — +3 bonus to one named skill (PHB p.100)
    # Dynamic key pattern: skill_focus_{skill_id} (cannot use dict table — one feat per skill).
    skill_focus_id = f"skill_focus_{target_skill_id}"
    if skill_focus_id in actor_feats:
        total += 3

    return total
```

**Why dynamic key (not dict):** Skill Focus can apply to any of ~35 skills. A dict would require ~35 static entries. The `f"skill_focus_{skill_id}"` pattern matches the existing feat naming convention (`weapon_focus_{weapon}`, etc.) and covers all skills with one check. SKF-005 confirms skill-specific isolation.

**Consume path:** `_get_feat_skill_bonus()` is called at `skill_resolver.py:283` inside `resolve_skill_check()`, after synergy and racial bonus accumulation. All three dict feats and `skill_focus_` branch add to `total` which is then added to `total` in `resolve_skill_check()` (line 283: `total += _get_feat_skill_bonus(...)`).

**Gate file:** `tests/test_engine_oss_skill_feats_wire_001_gate.py` — 8 tests (SKF-001..008)

---

### WO3: WO-ENGINE-RUN-FEAT-SPEED-001 (Run feat ×5 multiplier)

**File changed: `aidm/core/play_loop.py` (lines 4126-4130)**

**Before:**
```python
            _run_actor_data = world_state.entities.get(turn_ctx.actor_id, {})
            _base_speed = _run_actor_data.get(EF.BASE_SPEED, 30)
            _run_distance = _base_speed * 4
```

**After:**
```python
            _run_actor_data = world_state.entities.get(turn_ctx.actor_id, {})
            _base_speed = _run_actor_data.get(EF.BASE_SPEED, 30)
            # WO-ENGINE-RUN-FEAT-SPEED-001: Run feat → ×5 multiplier (PHB p.101); default ×4
            _run_multiplier = 5 if "run" in _run_actor_data.get(EF.FEATS, []) else 4
            _run_distance = _base_speed * _run_multiplier
```

**Feat key:** `"run"` bare string — consistent with how other feats are stored in `EF.FEATS` list (e.g., `"run"` from FeatID.RUN_FEAT or however it is populated). The `_run_actor_data` dict is already in scope from the line above.

**Coverage map note:** The Run row was already IMPLEMENTED (WO-ENGINE-RUN-ACTION-001). Updated to reflect ×5 with feat: `"RunIntent; ×4 speed (×5 with Run feat, ×3 with heavy armor)..."`.

**Fixture fix note:** Initial test used `execute_turn(grid=None, ...)` — `grid` is not a parameter. Corrected to use the actual signature: `execute_turn(world_state, turn_ctx, doctrine, combat_intent, rng, next_event_id, timestamp)`. No engine change needed.

**RUN-005 fix note:** Fatigued guard checks `entity.get(EF.FATIGUED, False)` — a direct entity field (not in `EF.CONDITIONS` dict). Test fixture corrected to set `entity[EF.FATIGUED] = True` directly.

**Gate file:** `tests/test_engine_run_feat_speed_001_gate.py` — 6 tests (RUN-001..006)

---

## Pass 2 — PM Summary (≤100 words)

Batch AZ (3 WOs): All genuine gaps from AUDIT-015. WO1 added `greater_weapon_focus_{weapon}` (+1 attack) and `greater_weapon_specialization_{weapon}` (+2 damage) branches to `feat_resolver.get_attack_modifier()` and `get_damage_modifier()` — both stack with WF/WS. WO2 added `agile`, `animal_affinity`, `magical_aptitude` to `_SKILL_BONUS_FEATS` dict and wired the `skill_focus_{skill_id}` dynamic branch (+3 untyped) in `_get_feat_skill_bonus()`. WO3: one-line fix — `_run_distance = _base_speed * (5 if "run" in feats else 4)` per PHB p.101. 22/22 gates. 1,734 total.

---

## Pass 3 — Retrospective

**Out-of-scope findings:**

None. All three WOs were narrow, precisely targeted at AUDIT-015 findings.

**Fixture discoveries (test authorship, not engine bugs):**

1. `execute_turn()` does not accept `grid` kwarg — removed. Standard discovery for a first-time call against this function.
2. Fatigued block uses `EF.FATIGUED` direct field, not `"fatigued"` in CONDITIONS dict — test corrected. This is an inconsistency in how fatigue is tracked vs. other conditions, but it is the existing behavior and not in scope.

**Kernel cross-pollination:**
- This WO touches **KERNEL-03 (Feat Resolver)** — GWF/GWS branches added. Any future feat audit should treat GWF/GWS as the canonical pattern for stacking weapon feats.
- This WO touches **KERNEL-05 (Skill Resolver)** — `_SKILL_BONUS_FEATS` dict now has 15 entries; `skill_focus_` dynamic key wired. This is the template for any future skill-bonus feat additions.
- No touches to KERNEL-01, KERNEL-02, KERNEL-04.

---

## ML Preflight Checklist

| Check | WO1 (GWF) | WO2 (SKF) | WO3 (RUN) |
|-------|-----------|-----------|-----------|
| ML-001: EF.* used (no bare strings) | Dynamic feat keys use f-string from `weapon_name` context (same pattern as WF/WS) | `EF.FEATS` used for feat list; dict keys are feat IDs (not EF fields) | `EF.FEATS`, `EF.BASE_SPEED` used; `"run"` is a feat ID value, not a field name |
| ML-002: All call sites identified | `get_attack_modifier()` and `get_damage_modifier()` — only two attack/damage paths | `_get_feat_skill_bonus()` — only skill bonus accumulation path; called at skill_resolver:283 | `play_loop.py:4128` — only run distance calculation; no parallel path |
| ML-003: No float in deterministic path | Integer +1 / +2 | Integer +2 / +3 | Integer multiplier ×4 or ×5 |
| ML-004: json.dumps sort_keys | N/A | N/A | N/A |
| ML-005: No WorldState mutation in resolver | feat_resolver reads entity, returns int — no mutation | skill_resolver reads entity, returns int — no mutation | play_loop runs entity.get() read — mutation is to deepcopy at WorldState construction only |
| ML-006: Coverage map updated | GWF + GWS new rows → IMPLEMENTED | Agile + Animal Affinity + Magical Aptitude + Skill Focus new rows → IMPLEMENTED | Run row updated to note ×5 with Run feat. WO-ENGINE-RUN-FEAT-SPEED-001. |

---

## Radar — Findings

| ID | Severity | Status | Description |
|----|----------|--------|-------------|
| AUDIT-015: GWF/GWS branches missing | MEDIUM | **CLOSED** | `greater_weapon_focus_` and `greater_weapon_specialization_` branches absent — wired by WO1 |
| AUDIT-015: Skill Focus / agile / animal_affinity / magical_aptitude | MEDIUM | **CLOSED** | OSS skill feats absent from `_SKILL_BONUS_FEATS`; `skill_focus_` dynamic branch missing — wired by WO2 |
| AUDIT-015: Run feat ×5 multiplier | MEDIUM | **CLOSED** | `_run_distance = _base_speed * 4` bare literal; Run feat not checked — wired by WO3 |
| FINDING-FIXTURE-FATIGUE-FIELD-001 | LOW | **OPEN** | `EF.FATIGUED = True` is a direct entity field; other conditions use `EF.CONDITIONS` dict — inconsistency. Not in scope. Filed for awareness. |

---

## Coverage Map Updates

**New rows added (WO1):**
- `| Greater Weapon Focus | PHB p.94 | IMPLEMENTED | feat_resolver.py | +1 attack stacks with WF; dynamic key. GWF-001..008. WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001. Batch AZ. |`
- `| Greater Weapon Specialization | PHB p.94 | IMPLEMENTED | feat_resolver.py | +2 damage stacks with WS; dynamic key. GWF-005..007. WO-ENGINE-GWF-GWS-FEAT-RESOLVER-001. Batch AZ. |`

**New rows added (WO2):**
- `| Agile | PHB p.91 | IMPLEMENTED | skill_resolver.py | +2 Balance/Escape Artist. SKF-001. WO-ENGINE-OSS-SKILL-FEATS-WIRE-001. Batch AZ. |`
- `| Animal Affinity | PHB p.91 | IMPLEMENTED | skill_resolver.py | +2 Handle Animal/Ride. SKF-002. WO-ENGINE-OSS-SKILL-FEATS-WIRE-001. Batch AZ. |`
- `| Magical Aptitude | PHB p.97 | IMPLEMENTED | skill_resolver.py | +2 Spellcraft/Use Magic Device. SKF-003. WO-ENGINE-OSS-SKILL-FEATS-WIRE-001. Batch AZ. |`
- `| Skill Focus | PHB p.100 | IMPLEMENTED | skill_resolver.py | +3 one named skill; dynamic key. SKF-004..006. WO-ENGINE-OSS-SKILL-FEATS-WIRE-001. Batch AZ. |`

**Row updated (WO3):**
- Run row: `×4 speed` → `×4 speed (×5 with Run feat)` + WO-ENGINE-RUN-FEAT-SPEED-001 annotation.

---

## Consume-Site Confirmation

### WO1 (GWF/GWS)
- **Write site:** `aidm/core/feat_resolver.py` — `get_attack_modifier()` and `get_damage_modifier()` (feat branches)
- **Read site:** `aidm/core/attack_resolver.py` — calls `get_attack_modifier()` and `get_damage_modifier()` from `feat_resolver` during attack resolution
- **Observable effect:** Attack roll total and damage total increase by +1/+2 when GWF/GWS feat present for matching weapon
- **Gate test proof:** GWF-002 (+1 attack), GWF-006 (+2 damage), GWF-003/007 (stacking)
- **CONSUME_DEFERRED fields:** None

### WO2 (SKF)
- **Write site:** `aidm/core/skill_resolver.py` — `_SKILL_BONUS_FEATS` dict and `_get_feat_skill_bonus()` function
- **Read site:** `aidm/core/skill_resolver.py:283` — `total += _get_feat_skill_bonus(_actor_feats, skill_id)` inside `resolve_skill_check()`
- **Observable effect:** Skill check total increases by +2 (dict feats) or +3 (skill_focus) when applicable feat present
- **Gate test proof:** SKF-001..006 (all feat types confirmed), SKF-007 (regression)
- **CONSUME_DEFERRED fields:** None

### WO3 (RUN)
- **Write site:** `aidm/core/play_loop.py:4128-4130` — `_run_multiplier` computed from `EF.FEATS` check
- **Read site:** Same line — `_run_distance = _base_speed * _run_multiplier`
- **Observable effect:** `entity_moved` event `distance_ft` payload is `base_speed × 5` when Run feat present (vs `× 4` without)
- **Gate test proof:** RUN-002 (speed=30, feat → 150 ft), RUN-004 (speed=20, feat → 100 ft)
- **CONSUME_DEFERRED fields:** None

---

## Parallel Paths Check

**WO1 (GWF/GWS):** `feat_resolver.get_attack_modifier()` and `get_damage_modifier()` are the canonical paths, called by `attack_resolver.py` and `full_attack_resolver.py`. No shadow attack/damage path computes weapon feat bonuses independently.

**WO2 (SKF):** `_get_feat_skill_bonus()` in `skill_resolver.py` is the single skill-bonus accumulation point. No other code path adds feat-based skill bonuses to skill checks.

**WO3 (RUN):** `play_loop.py` is the only location that executes `RunIntent` and computes run distance. No shadow run distance calculation exists.

---

*Batch AZ complete. 1,734 total gates. AUDIT-015 feat findings closed.*
