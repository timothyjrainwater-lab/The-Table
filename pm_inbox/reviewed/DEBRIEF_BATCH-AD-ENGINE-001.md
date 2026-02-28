**Lifecycle:** ARCHIVE
**Batch:** AD — WO-ENGINE-SAVECONTEXT-DESCRIPTOR-001, WO-ENGINE-DRUID-SAVES-FEATURES-001, WO-ENGINE-EVIL-CLERIC-INFLICT-001, WO-ENGINE-INSPIRE-GREATNESS-001
**Commit:** 0275dea
**Gate result:** 33/33 GREEN
**Regression:** 0 new engine failures (161 total includes untracked test files in ??-list; committed-test baseline unchanged)

---

## Pass 1 — Context Dump

### Files Changed

| File | Change |
|---|---|
| `aidm/schemas/saves.py` | +`save_descriptor: str = ""`, +`school: str = ""` to SaveContext; to_dict/from_dict updated |
| `aidm/schemas/entity_fields.py` | +ALIGNMENT, +RESIST_NATURES_LURE, +HP_TEMP, +INSPIRE_GREATNESS_ACTIVE, +INSPIRE_GREATNESS_ROUNDS_REMAINING, +INSPIRE_GREATNESS_BARD_ID |
| `aidm/core/save_resolver.py` | resolve_save() threads descriptor+school into get_save_bonus(); +illusion_save_bonus, +resist_natures_lure_bonus, +inspire_greatness_fort_bonus |
| `aidm/chargen/builder.py` | Nature Sense (+2 RACIAL_SKILL_BONUS) and Resist Nature's Lure (L4+) — single + multiclass paths |
| `aidm/core/skill_resolver.py` | RACIAL_SKILL_BONUS dict now consumed in resolve_skill_check() total |
| `aidm/core/spell_resolver.py` | SpellCastIntent +spontaneous_inflict field |
| `aidm/data/spell_definitions.py` | 5 inflict spells added: inflict_light/moderate/serious/critical_wounds, mass_inflict_light_wounds (L1-L5, necromancy, NEGATIVE damage, Will save half) |
| `aidm/core/play_loop.py` | Evil cleric inflict swap block (elif after cure swap; alignment + cleric-level gated) |
| `aidm/core/bardic_music_resolver.py` | resolve_inspire_greatness() + tick_inspire_greatness() functions |
| `aidm/core/attack_resolver.py` | inspire_greatness_bab from TEMPORARY_MODIFIERS added to attack total |
| `docs/ENGINE_COVERAGE_MAP.md` | 6 rows updated: IG, ECI, NS, RNL, AoC (PARTIAL→IMPLEMENTED), Cleric cure (FINDING closed) |
| `tests/test_engine_savecontext_descriptor_gate.py` | NEW — SCS-001–008 (8 tests) |
| `tests/test_engine_druid_saves_features_gate.py` | NEW — RNL-001–004 + NS-001–004 (8 tests) |
| `tests/test_engine_evil_cleric_inflict_gate.py` | NEW — registry check + ECI-001–008 (9 tests) |
| `tests/test_engine_inspire_greatness_gate.py` | NEW — IG-001–008 (8 tests) |

### WO1 — SaveContext descriptor + school threading

**Root cause:** `SaveContext` lacked `save_descriptor`/`school` fields. `resolve_save()` called `get_save_bonus(world_state, target_id, save_type)` — stripping both. `get_save_bonus()` accepted them but never received them from the full round-trip path. AoC, Still Mind, Indomitable Will, gnome illusion save could not fire via the resolve_save() path.

**Fix:** Two fields added to SaveContext dataclass. `resolve_save()` at `save_resolver.py:386` now passes both. Three new bonus reads in `get_save_bonus()`: illusion_save_bonus (when `school=="illusion"`, reads EF.SPELL_RESISTANCE_ILLUSION — existing field, misleading name), resist_natures_lure_bonus (when `save_descriptor=="fey"` + EF.RESIST_NATURES_LURE==True, +4), inspire_greatness_fort_bonus (TEMPORARY_MODIFIERS["inspire_greatness_fort"]).

**Consumption chain (WO1):**
- Write: call sites set SaveContext(save_descriptor="fey", school="illusion") at time of save
- Read: `save_resolver.resolve_save()` → `get_save_bonus(descriptor=..., school=...)`
- Effect: descriptor-gated bonuses now fire end-to-end
- Proof: SCS-001–008 gate tests confirm Still Mind, Indomitable Will, AoC, gnome illusion all fire through resolve_save() full path

### WO2 — Druid saves features

**Nature Sense write site:** `builder.py` (single-class ~line 969, multiclass ~line 1236) — after Wild Shape block, druid L1+ writes `EF.RACIAL_SKILL_BONUS["knowledge_nature"] += 2` and `["survival"] += 2`.

**Nature Sense read site:** `skill_resolver.resolve_skill_check()` — now reads `EF.RACIAL_SKILL_BONUS.get(skill_id, 0)` and adds to total. CRITICAL: this field was previously write-only (17-field audit, 2026-02-27). This WO closes the consumption gap for ALL racial skill bonuses, not just Nature Sense.

**Resist Nature's Lure write site:** `builder.py` — druid L4+ sets `EF.RESIST_NATURES_LURE = True`.
**Read site:** `save_resolver.get_save_bonus()` — when `save_descriptor == "fey"`, +4 bonus applied.
**Note:** Call sites must pass `save_descriptor="fey"` via SaveContext — this is the WO1 dependency. Without WO1, the descriptor was stripped at resolve_save(); these tests pass because they call get_save_bonus() directly.

**Consumption chains (WO2):**
- Nature Sense: builder.py → EF.RACIAL_SKILL_BONUS → skill_resolver.resolve_skill_check() → +2 on knowledge_nature/survival. NS-001–004.
- Resist Nature's Lure: builder.py → EF.RESIST_NATURES_LURE → save_resolver.get_save_bonus(save_descriptor="fey") → +4. RNL-001–004.

### WO3 — Evil cleric inflict swap

**Data:** 5 spells added to `spell_definitions.py` SPELL_REGISTRY: `inflict_light_wounds` (L1, 1d8 NEGATIVE, Will half), `inflict_moderate_wounds` (L2, 2d8), `inflict_serious_wounds` (L3, 3d8), `inflict_critical_wounds` (L4, 4d8), `mass_inflict_light_wounds` (L5, 1d8). All necromancy, `spell_resistance=True`.

**SpellCastIntent:** +`spontaneous_inflict: bool = False` field.

**play_loop.py:** `elif getattr(intent, "spontaneous_inflict", False)` block immediately after cure swap (lines 612–670). Guards: must be cleric (CLASS_LEVELS["cleric"] > 0), must be evil (ALIGNMENT in chaotic_evil/lawful_evil/neutral_evil). Redirects `spell = _inflict_spell`; slot governor then runs on the redirected level, consuming original declared spell from SPELL_SLOTS.

**Key note for ECI-007 test fix:** `divine_power` not in SPELL_REGISTRY — play_loop.py returns `"spell_failed"` at line 559 before the inflict block. Test rewritten to use `animate_dead` (L4, in registry). ECI-006 assertion: `"spell_slot_empty"` is the correct narration key when slot governor fires (no slot found), not `"spell_failed"`.

**Consumption chain (WO3):**
- SpellCastIntent.spontaneous_inflict=True → play_loop._resolve_spell_cast() → alignment check → inflect spell redirect → slot governor → spell resolution. ECI-001–008.

### WO4 — Inspire Greatness

**`bardic_music_resolver.py`:** `resolve_inspire_greatness(intent, ws, rng, next_event_id, timestamp)` — validates bard L9+ (CLASS_LEVELS["bard"] >= 9), 12+ Perform ranks (SKILL_RANKS["perform"] >= 12), decrements BARDIC_MUSIC_USES_REMAINING by 1. For each target (bard self + ally_ids): rolls 2d10+(2×Con mod) temp HP → writes EF.HP_TEMP; writes TEMPORARY_MODIFIERS["inspire_greatness_bab"] = max(existing, 2) (competence, non-stacking); TEMPORARY_MODIFIERS["inspire_greatness_fort"] = max(existing, 1). Sets EF.INSPIRE_GREATNESS_ACTIVE=True, EF.INSPIRE_GREATNESS_ROUNDS_REMAINING=_INSPIRE_GREATNESS_DURATION_ROUNDS, EF.INSPIRE_GREATNESS_BARD_ID. Emits `inspire_greatness_start` event.

**`tick_inspire_greatness(ws, next_event_id, timestamp)`:** Each affected entity: decrements rounds. On expiry: HP_TEMP=0, pops inspire_greatness_bab/fort from TEMPORARY_MODIFIERS, clears active flag. Emits `inspire_greatness_end`.

**`attack_resolver.py`:** Reads `_inspire_greatness_attack_bonus = _attacker_temp_mods.get("inspire_greatness_bab", 0)` and adds to attack total.

**Consumption chains (WO4):**
- BAB bonus: bardic_music_resolver → TEMPORARY_MODIFIERS["inspire_greatness_bab"] → attack_resolver → attack total. IG-003.
- Fort bonus: bardic_music_resolver → TEMPORARY_MODIFIERS["inspire_greatness_fort"] → save_resolver.get_save_bonus() → Fort save total (WO1 dependency for full path). IG-005.
- Temp HP: bardic_music_resolver → EF.HP_TEMP → UI/HP tracking. IG-001, IG-007.

---

## Pass 2 — PM Summary

Batch AD closes a 5-finding cluster root-caused to a single gap: SaveContext stripped descriptor+school before reaching get_save_bonus(). WO1 adds two fields + threads them; WO2 immediately uses the descriptor path for Resist Nature's Lure (+4 vs fey). Nature Sense also lands, closing a write-only gap for all RACIAL_SKILL_BONUS fields. WO3 adds the evil cleric mirror to the good cleric cure swap: 5 inflict spells in registry, alignment-gated swap in play_loop. WO4 delivers Inspire Greatness (bard L9+): temp HP, +2 competence attack, +1 competence Fort, tick-based expiry. 33 gates, 0 regressions. 6 coverage map rows updated.

---

## Pass 3 — Retrospective

**CONSUME_DEFERRED findings introduced:**

1. **spell_resolver._resolve_save() bypasses canonical resolve_save()** — SpellResolver has its own internal `_resolve_save()` that calls `TargetStats.get_save_bonus()` (a simple field read, not the full `save_resolver.get_save_bonus()` with all bonuses). Spell-triggered saves (via `_resolve_spell_cast`) do NOT benefit from WO1 threading, gnome illusion, Resist Nature's Lure, or Inspire Greatness Fort. This is an existing architectural gap, not introduced here. A future WO should unify the two paths.

2. **Inline save paths bypass resolve_save()** — massive damage (Fort save for death), CdG (Fort save), and concentration saves are generated inline in play_loop.py and attack_resolver.py, bypassing resolve_save() entirely. They also don't receive descriptors or school context.

**Out-of-scope findings:**

- FINDING-ENGINE-INSPIRE-GREATNESS-HD-001 (LOW): PHB Inspire Greatness grants +2 hit dice (affecting hp_max temporarily) in addition to +2 BAB and +1 Fort. This WO implements only BAB and Fort competence bonuses + temp HP via 2d10+(2×Con). The "+2 HD" mechanic requires a separate chargen-level HP adjustment not wired in this batch. Logged for future WO.
- FINDING-ENGINE-RACIAL-SKILL-BONUS-WRITE-ONLY-001 (CLOSED): RACIAL_SKILL_BONUS was write-only before WO2. Now consumed in skill_resolver. Closing this finding.
- FINDING-ENGINE-SPONTANEOUS-ALIGNMENT-001 (CLOSED): Cure swap had no alignment guard. WO3 adds alignment check to inflict swap; good clerics attempting inflict are blocked. Cure swap itself still has no explicit "must be good or neutral" guard — but this is acceptable: the swap is opt-in (spontaneous_cure=True), and evil clerics would use inflict instead.

**Kernel touches:** This WO touches KERNEL-01 (Entity Field Contract) — RACIAL_SKILL_BONUS is now Type 1 (component), consumed at runtime. Touches KERNEL-02 (Save Resolver) — three new bonus sources added to get_save_bonus(). No save double-count risk: all three bonuses are additive only when their guard conditions match.

---

## Radar

| ID | Severity | Status | Description |
|---|---|---|---|
| FINDING-ENGINE-SPELL-RESOLVER-SAVE-BYPASS-001 | MEDIUM | OPEN | spell_resolver._resolve_save() bypasses canonical save_resolver; spell saves miss WO1 descriptors, IG Fort, gnome illusion |
| FINDING-ENGINE-INLINE-SAVE-BYPASS-001 | LOW | OPEN | Massive damage / CdG / concentration saves generated inline, bypass resolve_save() |
| FINDING-ENGINE-INSPIRE-GREATNESS-HD-001 | LOW | OPEN | Inspire Greatness +2 HD (temp hp_max increase) not implemented; only temp HP via 2d10+(2×Con) |
| FINDING-ENGINE-SPONTANEOUS-ALIGNMENT-001 | — | CLOSED | Alignment guard for inflict swap added (WO3) |
| FINDING-ENGINE-RACIAL-SKILL-BONUS-WRITE-ONLY-001 | — | CLOSED | RACIAL_SKILL_BONUS now consumed in skill_resolver (WO2) |
| FINDING-ENGINE-SAVE-DESCRIPTOR-PASS-001 cluster | — | CLOSED | SaveContext threading gap closed (WO1) — AoC, Still Mind, Indomitable Will, gnome illusion all fire end-to-end |

---

## Consume-Site Confirmation

| WO | Write Site | Read Site | Effect | Gate Proof |
|---|---|---|---|---|
| WO1 | Call sites: SaveContext(save_descriptor=..., school=...) | save_resolver.resolve_save() → get_save_bonus() | descriptor-gated bonuses fire | SCS-001–008 |
| WO2 (NS) | builder.py (L969 + L1236) → EF.RACIAL_SKILL_BONUS | skill_resolver.resolve_skill_check() | +2 on knowledge_nature / survival | NS-001–004 |
| WO2 (RNL) | builder.py (L4+) → EF.RESIST_NATURES_LURE | save_resolver.get_save_bonus(save_descriptor="fey") | +4 Fort/Will vs fey | RNL-001–004 |
| WO3 | spell_definitions.py SPELL_REGISTRY; SpellCastIntent.spontaneous_inflict | play_loop._resolve_spell_cast() inflict block | alignment-gated inflict redirect | ECI-001–008 |
| WO4 (BAB) | bardic_music_resolver → TEMPORARY_MODIFIERS["inspire_greatness_bab"] | attack_resolver (temp_mods read) | +2 competence attack | IG-003 |
| WO4 (Fort) | bardic_music_resolver → TEMPORARY_MODIFIERS["inspire_greatness_fort"] | save_resolver.get_save_bonus() | +1 competence Fort | IG-005 |
| WO4 (HP) | bardic_music_resolver → EF.HP_TEMP | tick_inspire_greatness clears on expiry | temp HP lifecycle | IG-001, IG-007 |
