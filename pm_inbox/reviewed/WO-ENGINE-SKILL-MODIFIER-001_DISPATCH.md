# WO-ENGINE-SKILL-MODIFIER-001 — Wire Real Skill Modifier in _process_skill()
## Status: DISPATCH-READY
## Priority: LOW
## Closes: FINDING-ENGINE-SKILL-MODIFIER-001

---

## Context

WO-ENGINE-RETRY-002 (ACCEPTED 11/11) wired `_process_skill()` in `session_orchestrator.py` to `execute_exploration_skill_check()`. The modifier passed to that function is currently `modifier = 0` — a placeholder documented as FINDING-ENGINE-SKILL-MODIFIER-001.

`execute_exploration_skill_check()` docstring defines modifier as:
> "Total skill modifier (ability mod + ranks + circumstance − ACP)"

All three inputs are already present on the entity dict and are already computed by `skill_resolver.py` helpers (private, not importable). The entity dict is accessible at `self._world_state.entities[actor_id]`. This WO wires the lookup.

**What already exists (do not duplicate):**
- `aidm/schemas/skills.py` — `SKILLS` registry dict. Each entry is a `SkillDefinition(skill_id, name, key_ability, armor_check_penalty, trained_only, phb_page)`.
- `aidm/schemas/entity_fields.py` — `EF.STR_MOD`, `EF.DEX_MOD`, `EF.CON_MOD`, `EF.INT_MOD`, `EF.WIS_MOD`, `EF.CHA_MOD`, `EF.SKILL_RANKS`, `EF.ARMOR_CHECK_PENALTY`.
- `aidm/core/skill_resolver.py` — `_get_ability_modifier(entity, ability)`, `_get_skill_ranks(entity, skill_id)`, `_get_armor_check_penalty(entity)` — private helpers already correct. **Do NOT import these private helpers.** Replicate the lookup inline (three lines).

---

## Section 0 — Assumptions to Validate (read before coding)

1. Read `aidm/runtime/session_orchestrator.py` — find `_process_skill()`, confirm `modifier = 0` placeholder is still present.
2. Read `aidm/schemas/skills.py` — confirm `SKILLS` dict exists and is importable, confirm `SkillDefinition.key_ability` returns lowercase ability name (`"dex"`, `"int"`, etc.).
3. Read `aidm/schemas/entity_fields.py` — confirm `EF.SKILL_RANKS`, `EF.ARMOR_CHECK_PENALTY`, and the six `*_MOD` fields exist.
4. Confirm `SKILLS.get(skill_name)` pattern — some skills may not be in the registry (e.g., if `_normalize_skill()` returns a key not in `SKILLS`). The modifier lookup must fail gracefully (default 0) if `skill_name` not found.

**Preflight gate:** Run `python -m pytest tests/test_engine_retry_002_gate.py -v` — must be 11/11 before any change.

---

## Section 1 — Target Lock

After this WO:
- `_process_skill()` computes `modifier = ability_mod + skill_ranks − acp` from the entity dict before calling `execute_exploration_skill_check()`
- If the entity is not found in `world_state.entities`, modifier defaults to 0 (no crash)
- If the skill is not in the `SKILLS` registry, modifier defaults to 0 (no crash)
- FINDING-ENGINE-SKILL-MODIFIER-001 is closed

---

## Section 2 — Binary Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Lookup location | Inline in `_process_skill()` | Single call site. No abstraction needed. Three lines. |
| Private helpers from skill_resolver.py | Do NOT import | They are private (`_get_*`). Inline the same logic instead. |
| Missing skill in SKILLS registry | Default modifier 0, no exception | `_normalize_skill()` may return a verb not in SKILLS. Fail soft. |
| Missing entity in world_state.entities | Default modifier 0, no exception | Defensive; should not happen in normal flow but guard it. |
| ACP mapping | Use `SKILLS[skill_name].armor_check_penalty` boolean | Already correct in registry. |
| Ability→EF field map | Inline dict `{"dex": EF.DEX_MOD, ...}` | Mirrors existing skill_resolver.py pattern exactly. |

---

## Section 3 — Contract Spec

### Modified: `_process_skill()` in `session_orchestrator.py`

Replace the `modifier = 0` placeholder with:

```python
from aidm.schemas.skills import SKILLS

_entity = self._world_state.entities.get(actor_id, {})
_skill_def = SKILLS.get(skill_name)
if _skill_def is not None:
    _ability_map = {
        "str": EF.STR_MOD, "dex": EF.DEX_MOD, "con": EF.CON_MOD,
        "int": EF.INT_MOD, "wis": EF.WIS_MOD, "cha": EF.CHA_MOD,
    }
    _ability_mod = _entity.get(_ability_map.get(_skill_def.key_ability, ""), 0)
    _ranks = _entity.get(EF.SKILL_RANKS, {}).get(skill_name, 0)
    _acp = _entity.get(EF.ARMOR_CHECK_PENALTY, 0) if _skill_def.armor_check_penalty else 0
    modifier = _ability_mod + _ranks - _acp
else:
    modifier = 0  # skill not in registry — fail soft
```

Remove the `# FINDING-ENGINE-SKILL-MODIFIER-001` comment block after replacement.

**Builder must verify:**
- The import for `SKILLS` goes in the method body (local import is fine) or at module top if already present
- `EF` is already imported at module top — confirm before adding a redundant import
- The placeholder comment and the line `modifier = 0  # placeholder...` are both removed

---

## Section 4 — Implementation Plan

1. **Read** `aidm/runtime/session_orchestrator.py` — locate `_process_skill()`, confirm placeholder
2. **Read** `aidm/schemas/skills.py` — confirm `SKILLS` registry and `SkillDefinition.key_ability` values
3. **Replace** `modifier = 0` block in `_process_skill()` with the inline lookup above
4. **Run** `python -m pytest tests/test_engine_retry_002_gate.py -v` — 11/11 must hold
5. **Write** gate test file `tests/test_engine_skill_modifier_001_gate.py` — minimum 8 tests

### Gate test spec (minimum 8)

| ID | Test | Pass condition |
|----|------|----------------|
| SM-001 | Entity with 3 Search ranks + INT mod +2, no ACP → `_process_skill()` calls `execute_exploration_skill_check` with modifier=5 | modifier == 5 |
| SM-002 | Entity with 0 ranks, DEX mod +3, Hide skill (ACP-affected), ACP=4 → modifier = 0 + 3 − 4 = −1 | modifier == −1 |
| SM-003 | Entity with 5 Move Silently ranks, DEX mod +2, ACP=2 → modifier = 5 + 2 − 2 = 5 | modifier == 5 |
| SM-004 | Entity with 4 Climb ranks, STR mod +1, ACP=3 (Climb is ACP-affected) → modifier = 4 + 1 − 3 = 2 | modifier == 2 |
| SM-005 | Unknown skill not in SKILLS registry → modifier == 0, no exception | no crash |
| SM-006 | Actor ID not in world_state.entities → modifier == 0, no exception | no crash |
| SM-007 | Entity with no EF.SKILL_RANKS field → ranks default 0, no exception | no crash |
| SM-008 | Skill with ACP-affected=False (e.g., Search) → ACP not subtracted even if entity has ARMOR_CHECK_PENALTY=5 | modifier == ability_mod + ranks (no ACP deduction) |

---

## Integration Seams

| Component | File | Notes |
|-----------|------|-------|
| `_process_skill()` | `aidm/runtime/session_orchestrator.py:787` | Sole modification site |
| `SKILLS` registry | `aidm/schemas/skills.py` | `from aidm.schemas.skills import SKILLS` — already used in chargen/builder.py and skill_resolver.py |
| `EF.*_MOD` fields | `aidm/schemas/entity_fields.py` | `EF` already imported in session_orchestrator.py — confirm before re-importing |
| `EF.SKILL_RANKS` | `aidm/schemas/entity_fields.py` | `"skill_ranks"` key on entity dict |
| `EF.ARMOR_CHECK_PENALTY` | `aidm/schemas/entity_fields.py` | `"armor_check_penalty"` key on entity dict |
| `execute_exploration_skill_check()` | `aidm/core/play_loop.py:3148` | Signature unchanged — only `modifier` arg value changes |

---

## Out of Scope

- Circumstance modifiers (magic items, aid another, racial bonuses) — deferred. `modifier` covers base only.
- DM-settable DC override — deferred (DC=15 default remains).
- Voice path skill dispatch — separate pipeline.
- `skill_resolver.py` refactor — do not touch. Private helpers stay private.

---

## Debrief Required

**File to:** `pm_inbox/reviewed/DEBRIEF_WO-ENGINE-SKILL-MODIFIER-001.md`

**Pass 1 — Context dump:**
- List every file modified with line ranges
- Confirm exact modifier formula implemented
- Confirm fallback (0) on missing entity or missing skill
- Confirm SM-001–008 pass counts
- Confirm RT2-001–011 still pass after changes (regression clean)

**Pass 2 — PM summary ≤100 words**

**Pass 3 — Retrospective:**
- Any edge cases encountered not covered by spec?
- Is the inline approach the right long-term pattern or should a helper be extracted?

**Radar (one line each):**
- RT2-001–011: still PASS after changes
- SM-001–008: all PASS
- `modifier = 0` placeholder removed: CONFIRMED
- SKILLS registry import live: CONFIRMED
- Fallback on missing skill: CONFIRMED (SM-005)
- Fallback on missing entity: CONFIRMED (SM-006)
- No ACP applied to non-ACP skills: CONFIRMED (SM-008)

---

## Audio Cue

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

---

*Drafted: 2026-02-25 — Slate*
