# WO-WAYPOINT-003: Weapon Name Plumbing — feat_context Must Carry Real Weapon Name

**Classification:** CODE (engine fix + gate tests + narrative polish)
**Priority:** Critical path — silently disables all weapon-specific feats (Weapon Focus, Weapon Specialization). Poisons any future feat coverage work.
**Dispatched by:** Slate (PM)
**Date:** 2026-02-21
**Origin:** FINDING-WAYPOINT-02 from WO-WAYPOINT-001 debrief. `attack_resolver` passes `weapon_name="unknown"` to feat context; Weapon Focus matching fails silently.

---

## Objective

Three fixes in one WO, all related to weapon_name flowing through the system:

1. **Weapon name in feat context** — The attack resolver must pass the actual weapon name (from the entity's weapon field or the AttackIntent's Weapon object) into the feat context so weapon-specific feats can match.
2. **NarrativeBrief weapon_name extraction** — `assemble_narrative_brief()` should populate `weapon_name` from attack events when the data is present. (This rides along because weapon_name will now exist end-to-end.)
3. **Event field naming note** — Document `d20_result` as the canonical event payload field name. The WO-WAYPOINT-001 dispatch used `d20_roll`; the actual payload uses `d20_result`. This WO does NOT rename the field — it standardizes the documentation.

**The rule:** When a fighter swings a longsword and has Weapon Focus (longsword), the engine must know it's a longsword. Not "unknown."

---

## Scope

### IN SCOPE

1. **Fix weapon_name in attack_resolver feat context** — Find where `weapon_name="unknown"` is set (reported at ~line 230 of attack_resolver) and replace with the actual weapon name from the entity or intent.
2. **Gate tests** — New test file `tests/test_waypoint_003.py` verifying weapon-specific feat matching works.
3. **NarrativeBrief weapon_name** — If `assemble_narrative_brief()` has a `weapon_name` field that's currently unpopulated (or missing), populate it from the `attack_roll` event payload.
4. **Waypoint scenario update** — Update `tests/test_waypoint_001.py` W-2 to assert `feat_modifier` includes Weapon Focus +1 (currently asserts `feat_modifier == -2` for Power Attack only). This is the ONLY other existing test file the builder may modify.
5. **d20_result documentation** — Add a comment in the test file noting that `d20_result` (not `d20_roll`) is the canonical payload field name.

### OUT OF SCOPE

- No new feat types.
- No changes to feat definitions (the feats themselves are correct — it's the context that's wrong).
- No changes to conditions, spell_resolver, skill_resolver, or play_loop.
- No changes to the Weapon schema or entity schema.
- No changes to doctrine files.
- No field renaming — `d20_result` stays as-is in the codebase. We standardize docs, not code.

---

## Design

### Weapon Name Source

The builder must determine where the weapon name lives. Two likely sources:

1. **AttackIntent.weapon** — If the intent carries a `Weapon` object with a `name` or `weapon_name` field.
2. **Entity's `EF.WEAPON` field** — The entity dict has a `weapon` field (e.g., `"longsword"`).

The attack_resolver likely already has access to one or both. The builder should use whichever is most direct and consistent with existing code patterns. If both exist, the AttackIntent's Weapon object takes precedence (it's the explicit input).

### Feat Context Fix

Where the code currently sets `weapon_name="unknown"` (or equivalent), replace with the actual weapon name. The feat resolver's matching logic (e.g., `weapon_focus_{weapon_name}`) should then correctly match `weapon_focus_longsword` when the weapon is a longsword.

### Expected Impact on WO-WAYPOINT-001 Results

After this fix, Kael's attack in the Waypoint scenario should show:
- `feat_modifier` includes Weapon Focus +1 AND Power Attack -2 → net `feat_modifier` = -1 (or separate fields showing each)
- `power_attack_penalty` = -2 (unchanged)
- Attack total = d20 + BAB(5) + STR(3) + Weapon Focus(+1) + Power Attack(-2) + condition_modifier

The builder must verify the exact feat_modifier computation by reading the feat resolver.

### NarrativeBrief Weapon Name

The `assemble_narrative_brief()` function (in `aidm/lens/narrative_brief.py`) assembles a brief from events. If it has a `weapon_name` field, populate it from the `attack_roll` event payload's weapon information. If the field doesn't exist on the dataclass, add it as an `Optional[str]` field with default `None`.

---

## Gate Tests (`tests/test_waypoint_003.py`)

### WP3-0: Weapon Focus Fires With Correct Weapon Name

Set up: Create an entity with `weapon="longsword"` and `feats=["weapon_focus_longsword"]`. Execute an attack via `execute_turn()`.

| Assert | What it proves |
|--------|---------------|
| `attack_roll` event payload has `feat_modifier` that includes +1 for Weapon Focus | Weapon Focus matching works |
| The feat context used for resolution contains the actual weapon name (not "unknown") | Root cause fixed |

### WP3-1: Weapon Focus Does NOT Fire for Wrong Weapon

Set up: Create an entity with `weapon="greataxe"` and `feats=["weapon_focus_longsword"]`. Execute an attack.

| Assert | What it proves |
|--------|---------------|
| `attack_roll` event payload `feat_modifier` does NOT include Weapon Focus +1 | Matching is weapon-specific, not blanket |

### WP3-2: Power Attack Still Works (Regression Check)

Set up: Create an entity with `weapon="longsword"` and `feats=["power_attack"]`. Execute an attack with `power_attack_penalty=2`.

| Assert | What it proves |
|--------|---------------|
| `attack_roll` event payload has `power_attack_penalty` = -2 | Power Attack unaffected by weapon_name fix |
| `feat_modifier` or `feat_damage_modifier` includes Power Attack | Power Attack still operational |

### WP3-3: Combined Feats — Weapon Focus + Power Attack

Set up: Create an entity with `weapon="longsword"` and `feats=["weapon_focus_longsword", "power_attack"]`. Execute an attack with `power_attack_penalty=2`.

| Assert | What it proves |
|--------|---------------|
| `feat_modifier` includes both Weapon Focus +1 and Power Attack -2 | Both feats fire simultaneously |
| Attack total math is correct: `d20 + BAB + STR + feat_modifier + condition_modifier` | Combined modifier arithmetic is sound |

### WP3-4: NarrativeBrief Weapon Name Populated

Execute an attack. Assemble a `NarrativeBrief` from the resulting events.

| Assert | What it proves |
|--------|---------------|
| `brief.weapon_name` is not None and matches the weapon used | Weapon name flows through to narrative |

### WP3-5: Waypoint Scenario Regression — Weapon Focus Now Active

Re-run the WO-WAYPOINT-001 scenario (same seed, same fixtures). Kael's attack in Turn 1 should now show Weapon Focus +1 in the modifier breakdown.

| Assert | What it proves |
|--------|---------------|
| Kael's `attack_roll` payload includes Weapon Focus bonus | FINDING-WAYPOINT-02 is resolved |
| All other Waypoint gates still pass | No regressions |

---

## Modification to Existing Tests

**`tests/test_waypoint_001.py` — W-2 update (MANDATORY):**

Current W-2 asserts `feat_modifier == -2` (Power Attack only). After this WO, `feat_modifier` should reflect both Weapon Focus +1 and Power Attack -2. The builder must update the assertion to match the actual combined modifier value. The exact value depends on how the feat resolver combines the modifiers — the builder determines this by reading the code.

Also: update any comments referencing `d20_roll` to use `d20_result` for consistency with the actual payload field name.

---

## Integration Seams

| Seam | Module | Function | Contract |
|------|--------|----------|----------|
| Attack resolver | `aidm/core/attack_resolver.py` | `resolve_attack()` | **MODIFIED** — weapon_name in feat context |
| Feat resolver | `aidm/core/feat_resolver.py` | `get_attack_modifier()`, `get_damage_modifier()` | READ ONLY — already matches on weapon_name; currently gets "unknown" |
| Narrative brief | `aidm/lens/narrative_brief.py` | `assemble_narrative_brief()` | **POSSIBLY MODIFIED** — populate weapon_name field |
| Entity fields | `aidm/schemas/entity_fields.py` | `EF.WEAPON` | READ ONLY — weapon field on entity |
| Attack schema | `aidm/schemas/attack.py` | `AttackIntent`, `Weapon` | READ ONLY — weapon object in intent |
| Waypoint tests | `tests/test_waypoint_001.py` | W-2 | MODIFIED — update feat_modifier assertion |

---

## Assumptions to Validate

| # | Assumption | How to validate |
|---|-----------|----------------|
| A1 | `attack_resolver` has a location where it builds a feat context dict with `weapon_name` | Read `aidm/core/attack_resolver.py` |
| A2 | The current value is literally `"unknown"` (not None, not empty string) | Read the line in attack_resolver |
| A3 | The entity's `weapon` field (via `EF.WEAPON`) contains a string like `"longsword"` | Check `aidm/schemas/entity_fields.py` and entity fixtures |
| A4 | `feat_resolver.get_attack_modifier()` matches feat names using the pattern `weapon_focus_{weapon_name}` | Read `aidm/core/feat_resolver.py` |
| A5 | `NarrativeBrief` is a dataclass that can accept an optional `weapon_name` field (or already has one) | Read `aidm/lens/narrative_brief.py` |
| A6 | The `Weapon` object in `AttackIntent` has a name field accessible to attack_resolver | Read `aidm/schemas/attack.py` |

If any assumption fails, STOP. Document which assumption failed and why.

---

## Stop Conditions

1. **Any assumption (A1-A6) fails.** Stop, document, escalate.
2. **Weapon name doesn't exist anywhere accessible to attack_resolver.** If neither the entity nor the intent carries a usable weapon name, this requires schema changes — stop and escalate.
3. **Feat matching logic doesn't use `weapon_name` at all** (i.e., the matching is done differently than assumed). Stop and document the actual matching mechanism.
4. **Existing Waypoint tests break in unexpected ways** beyond the anticipated W-2 modifier change. Stop and document.
5. **Scope creep** — any temptation to add new feat types, modify condition logic, or restructure the attack pipeline. This WO plumbs ONE field through. That's it.

---

## Implementation Order

1. Validate assumptions A1-A6 by reading the integration seam modules
2. Fix weapon_name in attack_resolver feat context
3. Write WP3-0 (Weapon Focus fires)
4. Write WP3-1 (Weapon Focus negative case)
5. Write WP3-2 (Power Attack regression)
6. Write WP3-3 (combined feats)
7. Populate NarrativeBrief weapon_name from attack events
8. Write WP3-4 (NarrativeBrief weapon_name)
9. Update `tests/test_waypoint_001.py` W-2 assertion
10. Write WP3-5 (Waypoint regression)
11. Add `d20_result` canonical field name note in test comments
12. Run full test suite — 0 regressions on existing tests

---

## Sequencing Note

**This WO MUST be dispatched AFTER WO-WAYPOINT-002.** WO-WAYPOINT-002 changes Turn 2 behavior (paralyzed actor now blocked). WO-WAYPOINT-003's regression test (WP3-5) must account for both the action denial (from -002) and the weapon_name fix (from -003). If dispatched in parallel, the Waypoint test modifications will conflict.

**Dispatch order:** WO-WAYPOINT-002 lands first → builder updates W-2 for Branch A → WO-WAYPOINT-003 lands second → builder updates W-2 again for Weapon Focus modifier.

---

## Preflight

Run `python scripts/preflight_canary.py` and log results in `pm_inbox/PREFLIGHT_CANARY_LOG.md` before starting work.

---

## Delivery

### Commit

Single commit. Message format: `fix: WO-WAYPOINT-003 — weapon_name plumbing into feat context, NarrativeBrief weapon extraction`

All new gate tests must pass. All existing tests (including WO-WAYPOINT-001 updated and WO-WAYPOINT-002 tests) must show zero regressions.

### Completion Report

File as `pm_inbox/DEBRIEF_WO-WAYPOINT-003.md`. 500 words max. Five mandatory sections:

0. **Scope Accuracy** — Did you deliver what was asked? Note any deviations.
1. **Discovery Log** — Anything you found that the dispatch didn't anticipate.
2. **Methodology Challenge** — Hardest part and how you solved it.
3. **Field Manual Entry** — One tradecraft tip for the next builder working in this area.
4. **Builder Radar** (mandatory, 3 labeled lines):
   - **Trap.** Hidden dependency or trap for the next WO.
   - **Drift.** Current drift risk.
   - **Near stop.** What got close to triggering a stop condition.

### Audio Cue (MANDATORY)

When all work is complete (commit landed, debrief written), fire this command so the Operator knows you're done:

```
python scripts/speak.py --persona npc_elderly --backend kokoro "Work order complete. Awaiting Thunder."
```

### Debrief Focus Questions

1. **Weapon name source:** Did you use the entity's `EF.WEAPON` field or the `AttackIntent.weapon` object? Why?
2. **Other weapon-specific feats:** Beyond Weapon Focus, are there other feats in the codebase that match on weapon_name? Are they now correctly wired?
