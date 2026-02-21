# DEBRIEF: WO-WAYPOINT-003 — Weapon Name Plumbing

**Builder:** Claude Opus 4.6
**Date:** 2026-02-21
**Status:** COMPLETE — all 18 gate tests pass, zero regressions

---

## 0. Scope Accuracy

Delivered exactly what was asked. ONE line changed in `attack_resolver.py` line 230: `"weapon_name": "unknown"` replaced with `attacker.get(EF.WEAPON, "unknown")`. Added `weapon_name` to the `attack_roll` event payload (line 304) so NarrativeBrief can extract it. Created `tests/test_waypoint_003.py` with 19 tests (18 passed, 1 conditional skip). Updated `tests/test_waypoint_001.py` W-2 `feat_modifier` assertion from `== -2` to `== -1` and hardened the Turn 1 brief weapon_name assertion. Added `d20_result` canonical field name notes in both test file docstrings. Gold master JSONL files regenerated (field scenario changed from 9→11 turns due to modified damage output). No deviations from the dispatch.

## 1. Discovery Log

The `Weapon` dataclass has no `name` field — the weapon name lives only on the entity dict via `EF.WEAPON`. The dispatch anticipated either `AttackIntent.weapon` or `entity[EF.WEAPON]` as sources; only the entity source exists. The attacker variable was already in scope at the feat_context construction point (line 225), so the fix was a single-expression change.

The NarrativeBrief assembler already had weapon_name extraction logic at lines 674-678 (`"weapon_name" in payload`), but the attack_roll event payload never included the field. Adding `weapon_name` to the payload was sufficient — no changes to `narrative_brief.py` were needed.

Beyond Weapon Focus, `feat_resolver.get_damage_modifier()` also matches on weapon_name for `weapon_specialization_{weapon_name}`. This is now correctly wired. No entities in the current fixtures use Weapon Specialization, but the plumbing is in place.

## 2. Methodology Challenge

The gold master JSONL files recorded events with the old payload shape (no `weapon_name` field). Adding the field to `attack_roll` caused 4 gold master replay regressions — the replay harness detected drift at `payload.weapon_name` (Expected: None, Actual: weapon name). Regenerating via `python -m tests.fixtures.gold_masters.generate` resolved all 4 failures. The field scenario changed from 338→368 events because Weapon Focus +1 on attack rolls altered hit/miss outcomes, changing the battle flow.

## 3. Field Manual Entry

**When adding a new field to an event payload in `attack_resolver.py`, always regenerate gold master JSONL files.** The replay regression harness does field-by-field comparison and will flag any new or changed payload fields as drift. Run `python -m tests.fixtures.gold_masters.generate` and commit the updated files alongside the code change.

## 4. Builder Radar

- **Trap.** The `feat_context["weapon_name"]` is read from `attacker.get(EF.WEAPON, "unknown")`, but `EF.WEAPON` stores a bare string (e.g., `"longsword"`). If the entity schema ever changes `weapon` to a dict or object, this lookup silently returns the wrong type and feat matching breaks. The feat resolver does `f"weapon_focus_{weapon_name}"` string interpolation — a dict would produce `weapon_focus_{'name': 'longsword'}`.
- **Drift.** The `assemble_narrative_brief()` weapon_name extraction at line 674-678 checks `"weapon" in event` then `"weapon_name" in payload`. These two paths could diverge if a future event type puts weapon data in a different shape. A single canonical extraction path would be safer.
- **Near stop.** A6 validation was close — the `Weapon` dataclass has no `name` field at all. The dispatch anticipated the weapon name might come from `AttackIntent.weapon`, but the `Weapon` class only has mechanical fields (damage_dice, damage_type, etc.). Had the entity also lacked `EF.WEAPON`, the WO would have required schema changes and triggered stop condition #2.

---

## Debrief Focus Questions

1. **Weapon name source:** Used the entity's `EF.WEAPON` field. The `Weapon` dataclass has no name/weapon_name field — it's purely mechanical (damage dice, type, critical range). The entity dict is the authoritative source for the weapon's identity.

2. **Other weapon-specific feats:** `weapon_specialization_{weapon_name}` in `get_damage_modifier()` also matches on weapon_name and is now correctly wired. No other weapon-name-dependent feats exist in the current `FEAT_REGISTRY`.
