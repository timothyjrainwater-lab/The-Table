# ENGINE COVERAGE MAP
## AIDM D&D 3.5e PHB + DMG Mechanics vs. Engine Implementation
### Status: Authoritative Gap Analysis | Generated: 2026-02-26 | Bulk sync: 2026-02-27 (46 row updates; ~39% IMPLEMENTED)
### Sources: PHB_35_MECHANICS_INVENTORY (Parts 1-3), DMG-MECHANICS-INVENTORY (Parts 1-5), aidm/core/, aidm/schemas/

---

## COVERAGE STATUS DEFINITIONS

| Status | Meaning |
|--------|---------|
| **IMPLEMENTED** | Engine has a working resolver/mechanic. Tests exist. |
| **PARTIAL** | Engine handles the mechanic but incompletely (degraded, narrative-only, or missing edge cases). |
| **NOT STARTED** | No implementation exists. Gap for future WO. |
| **DEFERRED** | Explicitly noted as deferred in WO comments or engine code. |

---

## SECTION 1 — COMBAT CORE

| Mechanic | Source | Status | Engine File(s) | Notes / Gap Description |
|----------|--------|--------|----------------|--------------------------|
| Initiative roll (d20 + DEX) | PHB p.136 | **IMPLEMENTED** | `initiative.py`, `combat_controller.py` | Full d20 + DEX roll; ties broken by modifier |
| Flat-footed before first action | PHB p.136 | **IMPLEMENTED** | `conditions.py`, `schemas/conditions.py` | FLAT_FOOTED condition; loses DEX to AC |
| Readying an action | PHB p.136 | **IMPLEMENTED** | `readied_action_resolver.py`, `play_loop.py` | ReadyActionIntent wired; trigger/action declared |
| Delaying an action | PHB p.136 | **IMPLEMENTED** | `withdraw_delay_resolver.py`, `play_loop.py` | DelayIntent wired into play loop |
| Initiative ties (re-roll / higher mod) | PHB p.136 | **PARTIAL** | `initiative.py` | Higher modifier wins; simultaneous tie re-roll not enforced |
| Standard action | PHB p.127 | **IMPLEMENTED** | `action_economy.py`, `play_loop.py` | ActionBudget tracks standard slot; enforced CP-24 |
| Move action | PHB p.127 | **IMPLEMENTED** | `action_economy.py`, `play_loop.py` | Move slot tracked; step/full-move intents wired |
| Full-round action | PHB p.127 | **IMPLEMENTED** | `action_economy.py`, `play_loop.py` | Full-round consumes both standard + move |
| Free action | PHB p.127 | **IMPLEMENTED** | `action_economy.py` | Always available; unlimited per turn |
| Swift action | PHB p.127 | **IMPLEMENTED** | `action_economy.py` | swift_used slot tracked; quickened spells use it |
| Immediate action | PHB p.127 | **IMPLEMENTED** | `action_economy.py`, `play_loop.py` | `immediate_used` slot in ActionBudget. Cross-turn `pending_swift_burn` set on use; burns swift slot at next turn start. DEBRIEF_WO-ENGINE-IMMEDIATE-ACTION-001. |
| 5-foot step | PHB p.127 | **IMPLEMENTED** | `action_economy.py`, `aoo.py` | five_foot_step_used flag; mutually exclusive with move |
| Single melee attack roll (d20 + bonus vs AC) | PHB p.140 | **IMPLEMENTED** | `attack_resolver.py` | Full roll + bonus vs AC; natural 1 always miss, natural 20 always hit |
| Single ranged attack roll | PHB p.140 | **IMPLEMENTED** | `ranged_resolver.py`, `attack_resolver.py` | Ranged attacks handled; range penalty not yet automatic |
| Touch attack (melee) | PHB p.140 | **PARTIAL** | `spell_resolver.py` | Touch attacks supported for spells (TOUCH SpellTarget); standalone melee touch intent not separated |
| Ranged touch attack | PHB p.140 | **PARTIAL** | `spell_resolver.py` | RAY SpellTarget uses ranged touch; standalone ranged touch attack not separated |
| AC calculation (base 10 + all bonuses) | PHB p.136 | **IMPLEMENTED** | `attack_resolver.py`, `conditions.py` | All layers: armor, shield, DEX, size, deflection, dodge, natural, misc |
| Armor bonus to AC | PHB p.136 | **PARTIAL** | `attack_resolver.py` | AC field on entity used; armor-type tracking not granular (no separate armor/shield/natural fields enforced) |
| Shield bonus to AC | PHB p.136 | **PARTIAL** | `attack_resolver.py` | Included in entity AC; not tracked as independent shield field |
| DEX bonus to AC (lost when flat-footed) | PHB p.136 | **IMPLEMENTED** | `conditions.py`, `attack_resolver.py` | DEX_MOD field; loses_dex_to_ac flag in ConditionModifiers applied |
| Natural armor bonus | PHB p.136 | **PARTIAL** | `wild_shape_resolver.py` | natural_ac tracked for Wild Shape forms; not a generalized entity field |
| Dodge bonus to AC | PHB p.136 | **PARTIAL** | `feat_resolver.py` | Dodge feat (+1 vs designated target); stackable rule acknowledged but general dodge tracking limited |
| Deflection bonus to AC | PHB p.136 | **NOT STARTED** | — | No deflection bonus field on entity; needed for rings of protection |
| Size modifier to AC/attack | PHB p.136 | **IMPLEMENTED** | `schemas/maneuvers.py`, `maneuver_resolver.py` | SIZE_CATEGORY and size modifiers for maneuvers; size-to-AC also referenced in attack |
| Cover bonus to AC | PHB p.151 | **IMPLEMENTED** | `cover_resolver.py`, `attack_resolver.py` | Standard +4, improved +8; total cover blocks targeting |
| Concealment miss chance | PHB p.152 | **IMPLEMENTED** | `concealment.py`, `attack_resolver.py` | MISS_CHANCE entity field; 20%/50% miss; d100 rolled post-hit |
| Flanking bonus (+2 to attack) | PHB p.153 | **IMPLEMENTED** | `flanking.py`, `attack_resolver.py` | Geometry-based flanking check; angle ≥135 degrees |
| Higher ground bonus (+1 melee) | PHB p.153 | **IMPLEMENTED** | `attack_resolver.py` | ELEVATION field; +1 melee vs lower-elevation target |
| Damage roll (weapon dice + STR/modifier) | PHB p.141 | **IMPLEMENTED** | `attack_resolver.py` | parse_damage_dice(); STR mod added from entity |
| Minimum 1 damage | PHB p.141 | **IMPLEMENTED** | `attack_resolver.py` | Clamped to minimum 1 on hit |
| Critical hit — threat range detection | PHB p.140 | **IMPLEMENTED** | `attack_resolver.py`, `full_attack_resolver.py` | threat_range from weapon; default 20; 19-20 and 18-20 supported |
| Critical hit — confirmation roll | PHB p.140 | **IMPLEMENTED** | `attack_resolver.py` | Second d20 rolled vs AC on threat; no auto-hit on natural 20 for confirm |
| Critical hit — damage multiplier (x2/x3/x4) | PHB p.140 | **IMPLEMENTED** | `attack_resolver.py` | crit_multiplier from weapon applied |
| Damage Reduction (DR X/type) | PHB p.291 | **IMPLEMENTED** | `damage_reduction.py` | DR applied post-crit; bypass types: magic, adamantine, cold_iron, silver, good, evil, lawful, chaotic, epic, "-" |
| Full attack action | PHB p.140 | **IMPLEMENTED** | `full_attack_resolver.py` | Iterative attacks at BAB, BAB-5, BAB-10, BAB-15; all attacks resolved |
| Iterative attack penalty (-5 per attack) | PHB p.140 | **IMPLEMENTED** | `full_attack_resolver.py` | Automatic -5 progression applied to each iterative |
| Two-weapon fighting | PHB p.160 | **IMPLEMENTED** | `play_loop.py` (TWF wire) | TWFIntent wired; normal penalties -6/-10; TWF feat reduces to -4/-4; light offhand -4/-4 |
| Improved TWF (second off-hand attack) | PHB p.160 | **IMPLEMENTED** | `schemas/feats.py`, `feat_resolver.py` | Feat registered; extra off-hand attack at BAB-5 |
| Greater TWF (third off-hand attack) | PHB p.160 | **IMPLEMENTED** | `schemas/feats.py` | Feat registered; third off-hand at BAB-10 |
| Death at -10 HP | PHB p.145 | **IMPLEMENTED** | `dying_resolver.py` | classify_hp(); -10 or below = dead → entity_defeated event |
| Dying (-1 to -9 HP) | PHB p.145 | **IMPLEMENTED** | `dying_resolver.py` | DYING field; entity_dying event emitted |
| Disabled (0 HP) | PHB p.145 | **IMPLEMENTED** | `dying_resolver.py` | DISABLED field; entity_disabled event |
| Stable (dying but not losing HP) | PHB p.145 | **IMPLEMENTED** | `dying_resolver.py`, `schemas/entity_fields.py` | STABLE field; DC 10 Fort save each round or -1 HP |
| Dying → bleed 1 HP/round (DC 10 Fort) | PHB p.145 | **IMPLEMENTED** | `dying_resolver.py` | Fort save each round; pass = stable; fail = -1 HP |
| Nonlethal damage tracking | PHB p.146 | **IMPLEMENTED** | `play_loop.py` | NONLETHAL_DAMAGE field; staggered when NL ≥ HP; unconscious when NL > HP |
| Massive damage rule (50+ HP = Fort DC 15 or die) | PHB p.145 | **IMPLEMENTED** | `attack_resolver.py` | Post-DR check: `if final_damage >= 50`. nat1/nat20 auto-fail/pass enforced (PHB p.136). WO-ENGINE-MD-SAVE-RULES-001. |
| Natural healing (level HP/night) | PHB p.130 | **IMPLEMENTED** | `rest_resolver.py` | RestIntent → level × max(1, CON mod) HP per night; full day = double |
| Stabilization by ally (DC 15 Heal) | PHB p.145 | **PARTIAL** | `heal_resolver.py`, `play_loop.py` | HealIntent + DC 15 Heal skill check wired; entity must be DYING. 8/8 gate pass. DEBRIEF_WO-ENGINE-STABILIZE-ALLY-001. |

---

## SECTION 2 — SPECIAL ATTACKS & MANEUVERS

| Mechanic | Source | Status | Engine File(s) | Notes / Gap Description |
|----------|--------|--------|----------------|--------------------------|
| Bull Rush — provokes AoO | PHB p.154 | **IMPLEMENTED** | `maneuver_resolver.py`, `aoo.py` | AoO triggered from all threateners before resolution |
| Bull Rush — opposed STR check | PHB p.154 | **IMPLEMENTED** | `maneuver_resolver.py` | Attacker STR vs defender STR; size modifiers applied |
| Bull Rush — push distance | PHB p.154 | **IMPLEMENTED** | `maneuver_resolver.py` | 5 ft per 5 points margin; forced movement with hazard check |
| Bull Rush — into hazards | PHB p.154 | **IMPLEMENTED** | `maneuver_resolver.py`, `terrain_resolver.py` | Falling/pit damage on forced movement |
| Charge attack (+2 attack, -2 AC) | PHB p.154 | **IMPLEMENTED** | `play_loop.py` | ChargeIntent → +2 attack, -2 AC; must move at least 10 ft |
| Charge — must move in straight line | PHB p.154 | **PARTIAL** | `play_loop.py` | Charge movement direction validated; LOS not fully enforced |
| Charge — lance/mounted charge (×2 damage) | PHB p.154 | **PARTIAL** | `mounted_combat.py` | Mounted combat resolver exists; lance ×2 damage not auto-applied |
| Cleave — free attack after dropping foe | PHB p.154 | **IMPLEMENTED** | `attack_resolver.py` | _find_cleave_target(); free attack on adjacent enemy when foe drops |
| Great Cleave — unlimited cleaves per round | PHB p.155 | **IMPLEMENTED** | `attack_resolver.py` | Great Cleave feat check; no limit on cleaves per round |
| Coup de Grace — helpless target, instant kill | PHB p.153 | **IMPLEMENTED** | `attack_resolver.py`, `save_resolver.py` | CoupDeGraceIntent; auto-crit; Fort DC (10 + damage) via get_save_bonus(); nat1/nat20; feats/Divine Grace/racial bonuses apply. WO-ENGINE-CDG-SAVE-PATH-001. |
| Disarm — opposed attack rolls | PHB p.155 | **IMPLEMENTED** | `maneuver_resolver.py` | DisarmIntent; attacker vs defender opposed attack rolls; DISARMED field |
| Disarm — counter-disarm | PHB p.155 | **IMPLEMENTED** | `maneuver_resolver.py` | Any attacker failure allows counter-disarm (PHB p.155). Improved Disarm suppresses counter. Size modifier verified (+4 per category). WO-ENGINE-DISARM-FIDELITY-001. |
| Disarm — two-handed weapon advantage | PHB p.155 | **NOT STARTED** | — | +4 if using two-handed weapon for disarm not implemented |
| Disarm — weapon drops to ground | PHB p.155 | **PARTIAL** | `maneuver_resolver.py` | DISARMED flag set; no world-space "dropped weapon" object tracking |
| Feint — Bluff vs Sense Motive | PHB p.156 | **IMPLEMENTED** | `feint_resolver.py`, `play_loop.py` | FeintIntent; Bluff vs Sense Motive opposed check; deny DEX to AC on success |
| Improved Feint (feint as move action) | PHB p.156 | **IMPLEMENTED** | `schemas/feats.py` | IMPROVED_FEINT feat registered and wired |
| Grapple — provokes AoO | PHB p.156 | **IMPLEMENTED** | `maneuver_resolver.py`, `aoo.py` | AoO from target before grapple resolution |
| Grapple — touch attack to grab | PHB p.156 | **IMPLEMENTED** | `maneuver_resolver.py` | Touch attack resolved before grapple check |
| Grapple — opposed grapple checks | PHB p.156 | **IMPLEMENTED** | `maneuver_resolver.py` | BAB + STR + size modifier; GRAPPLED/GRAPPLING conditions applied. _get_bab() now uses EF.BAB (Type 1) — WO-ENGINE-MANEUVER-BAB-FIX-001 (all 5 maneuver types). |
| Grapple — in-grapple actions (damage, pin, escape) | PHB p.156-158 | **IMPLEMENTED** | `maneuver_resolver.py` | GrappleEscapeIntent, PinEscapeIntent wired; PINNED condition added |
| Grapple — pin (helpless) | PHB p.157 | **IMPLEMENTED** | `maneuver_resolver.py`, `schemas/conditions.py` | PINNED condition; auto-hit_if_helpless; WO-ENGINE-GRAPPLE-PIN-001 |
| Grapple — tie up/bound | PHB p.157 | **NOT STARTED** | — | No rope-binding mechanic; tied condition not implemented |
| Grapple — multiple combatants | PHB p.158 | **NOT STARTED** | — | Multi-person grapples not modeled |
| Overrun — provokes AoO | PHB p.158 | **IMPLEMENTED** | `maneuver_resolver.py` | AoO on entry |
| Overrun — opposed checks / avoid | PHB p.158 | **IMPLEMENTED** | `maneuver_resolver.py` | OverrunIntent; defender may avoid or oppose; STR/size checks. Prone sub-check uses max(STR,DEX) for defender per PHB p.157. WO-ENGINE-MANEUVER-FIDELITY-002. Batch AA. |
| Sunder — attack weapon/shield | PHB p.158 | **PARTIAL** | `maneuver_resolver.py` | SunderIntent wired; AoO triggered; attack roll resolved; WEAPON_HP/WEAPON_BROKEN fields tracked (WO-ENGINE-SUNDER-DISARM-FULL-001) |
| Sunder — object hardness | PHB p.158 | **PARTIAL** | `damage_reduction.py` | Hardness as DR; WEAPON_HP/WEAPON_HP_MAX/WEAPON_DESTROYED fields present; full item destruction flow partial |
| Trip — provokes AoO from target | PHB p.158 | **IMPLEMENTED** | `maneuver_resolver.py` | TripIntent; AoO from target |
| Trip — touch attack (if weapon) | PHB p.158 | **IMPLEMENTED** | `maneuver_resolver.py` | Touch attack resolved before trip check |
| Trip — opposed STR/DEX checks | PHB p.158 | **IMPLEMENTED** | `maneuver_resolver.py` | Attacker vs defender; PRONE condition on success |
| Trip — counter-trip | PHB p.158 | **IMPLEMENTED** | `maneuver_resolver.py` | Defender may counter-trip on failure |
| Aid Another (combat) — +2 attack or AC | PHB p.154 | **IMPLEMENTED** | `aid_another_resolver.py`, `play_loop.py` | AidAnotherIntent; DC 10 attack roll; +2 bonus to ally attack or AC |

---

## SECTION 3 — ATTACKS OF OPPORTUNITY

| Mechanic | Source | Status | Engine File(s) | Notes / Gap Description |
|----------|--------|--------|----------------|--------------------------|
| AoO trigger: movement out of threatened square | PHB p.137 | **IMPLEMENTED** | `aoo.py` | check_aoo_triggers() on StepMoveIntent/MountedMoveIntent |
| AoO trigger: ranged attack in threatened square | PHB p.137 | **IMPLEMENTED** | `aoo.py` | "ranged_attack" provoking_action type |
| AoO trigger: spellcasting in threatened square | PHB p.137 | **IMPLEMENTED** | `aoo.py` | "spellcasting" provoking_action type |
| AoO trigger: combat maneuvers (bull rush, disarm, etc.) | PHB p.137 | **IMPLEMENTED** | `aoo.py`, `maneuver_resolver.py` | Maneuver-specific AoO triggers per PHB |
| AoO trigger: picking up object | PHB p.137 | **NOT STARTED** | — | No item pickup mechanic; AoO not triggered |
| AoO trigger: reading scroll | PHB p.137 | **NOT STARTED** | — | Scroll use not implemented |
| AoO trigger: using skill in combat | PHB p.137 | **NOT STARTED** | — | Skill use in combat AoO not implemented |
| AoO trigger: standing from prone | PHB p.137 | **IMPLEMENTED** | `aoo.py`, `play_loop.py` | `check_stand_from_prone_aoo()` at `aoo.py:709–817`. Called from `play_loop.py:3530`. Full AoO tracking + prone condition clearing. DEBRIEF_WO-ENGINE-AOO-STAND-FROM-PRONE-001. |
| One AoO per round per entity (base) | PHB p.137 | **IMPLEMENTED** | `aoo.py` | aoo_opportunity_used flag; one AoO per reactor per round |
| AoO resolution (full attack roll) | PHB p.137 | **IMPLEMENTED** | `aoo.py` | resolve_aoo_sequence(); full attack resolution |
| Combat Reflexes — DEX mod extra AoOs | PHB p.92 | **IMPLEMENTED** | `combat_reflexes.py`, `aoo.py` | COMBAT_REFLEXES feat; DEX mod additional AoOs per round |
| Reach weapons — 10-ft threatened square | PHB p.145 | **IMPLEMENTED** | `reach_resolver.py` | Weapon reach tracked; 10-ft vs 5-ft threatened area |
| Reach weapons — cannot threaten adjacent | PHB p.145 | **PARTIAL** | `reach_resolver.py` | Reach weapon reach tracked; no-adjacent-threat enforcement partial |
| 5-foot step — no AoO | PHB p.143 | **IMPLEMENTED** | `action_economy.py`, `aoo.py` | five_foot_step_used prevents movement AoO |
| Withdraw — first square of movement no AoO | PHB p.143 | **IMPLEMENTED** | `withdraw_delay_resolver.py`, `play_loop.py` | WithdrawIntent; first square safe from AoO |
| Cover blocks AoO | PHB p.151 | **IMPLEMENTED** | `aoo.py`, `cover_resolver.py` | Standard/improved cover blocks AoO execution; soft cover does not |

---

## SECTION 4 — CONDITIONS (All PHB Conditions)

| Condition | Source | Status | Engine File(s) | Notes / Gap Description |
|-----------|--------|--------|----------------|--------------------------|
| Blinded | PHB p.309 | **IMPLEMENTED** | `schemas/conditions.py`, `conditions.py` | 50% miss on attacks; opponents +2; -2 AC; loses DEX to AC; WO-ENGINE-CONDITIONS-BLIND-DEAF-001 |
| Confused | PHB p.309 | **IMPLEMENTED** | `schemas/conditions.py` | d100 behavior roll per turn; -2 attack, -4 DEX |
| Cowering | PHB p.309 | **IMPLEMENTED** | `schemas/conditions.py`, `conditions.py` | COWERING condition type; loses DEX to AC, no actions. DEBRIEF_WO-ENGINE-COWERING-FASCINATED-001. |
| Dazed | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py` | No actions, no AC penalty; 1-round duration default |
| Dazzled | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py`, `conditions.py` | DAZZLED condition; -1 attack, -1 Spot. DEBRIEF_WO-ENGINE-DAZZLED-CONDITION-001. |
| Deafened | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py` | DEAFENED condition type; 20% verbal spell failure; bardic music check |
| Entangled | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py` | -2 attack, -4 DEX; from web spell and similar |
| Exhausted | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py` | -6 STR/DEX (proxied as -3 attack/-3 damage/-6 DEX mod); half speed |
| Fascinated | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py`, `conditions.py`, `session_orchestrator.py` | FASCINATED condition; cannot attack or move; flat-footed AC; -4 skill penalty (PHB p.308). WO-ENGINE-MD-SAVE-RULES-001 (FSKL). |
| Fatigued | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py`, `schemas/entity_fields.py`, `play_loop.py`, `save_resolver.py` | -2 STR/DEX; FATIGUED bool field and condition; post-rage fatigue; blocks charge and run (PHB p.308). WO-ENGINE-FATIGUE-MOBILITY-001. WO-AE-WO2: EF.FATIGUED=True now wired to -2 Ref penalty in save_resolver.get_save_bonus(). |
| Flat-footed | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py` | FLAT_FOOTED condition; loses DEX to AC |
| Frightened | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py` | -2 attack/saves; flees from source; FRIGHTENED condition |
| Grappled | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py` | -4 DEX, no normal movement; GRAPPLED condition |
| Helpless | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py` | DEX 0; -4 AC vs melee; auto-hit_if_helpless; HELPLESS condition |
| Incorporeal | PHB p.310 | **NOT STARTED** | — | No incorporeal condition or miss chance mechanic; EF.MISS_CHANCE exists but not incorporeal-specific |
| Invisible | PHB p.310 | **PARTIAL** | `concealment.py` | MISS_CHANCE field set to 50% for invisibility; no "invisible" condition type; no granular see-invisible enforcement |
| Nauseated | PHB p.310 | **IMPLEMENTED** | `schemas/conditions.py` | Only move action per turn; actions_prohibited=True |
| Panicked | PHB p.311 | **IMPLEMENTED** | `schemas/conditions.py` | Drops items, flees; -2 saves; PANICKED condition |
| Paralyzed | PHB p.311 | **IMPLEMENTED** | `schemas/conditions.py` | STR/DEX 0; helpless; cannot act; PARALYZED condition |
| Petrified | PHB p.311 | **NOT STARTED** | — | Not in ConditionType enum; no stone statue mechanic |
| Pinned | PHB p.311 | **IMPLEMENTED** | `schemas/conditions.py` | Helpless; DEX 0; melee +4; PINNED condition from grapple escalation |
| Prone | PHB p.311 | **IMPLEMENTED** | `schemas/conditions.py` | -4 AC vs melee, +4 AC vs ranged, -4 melee attack; PRONE condition |
| Shaken | PHB p.311 | **IMPLEMENTED** | `schemas/conditions.py` | -2 attack, -2 Fort/Ref/Will; SHAKEN condition |
| Sickened | PHB p.311 | **IMPLEMENTED** | `schemas/conditions.py` | -2 attack, -2 damage, -2 saves; SICKENED condition |
| Stable | PHB p.311 | **IMPLEMENTED** | `schemas/entity_fields.py`, `dying_resolver.py` | STABLE bool field; formerly dying, not losing HP |
| Staggered | PHB p.311 | **IMPLEMENTED** | `schemas/conditions.py` | Only standard or move action per round; STAGGERED condition |
| Stunned | PHB p.311 | **IMPLEMENTED** | `schemas/conditions.py` | -2 AC, loses DEX; drops items; cannot act; STUNNED condition |
| Turned | PHB p.311 | **IMPLEMENTED** | `schemas/conditions.py` | Flees from cleric; cannot attack; TURNED condition; 10-round expiry DEFERRED |
| Unconscious | PHB p.311 | **IMPLEMENTED** | `schemas/conditions.py` | Helpless; cannot move or act; UNCONSCIOUS condition |
| Condition duration tracking (tick-down) | PHB p.309 | **IMPLEMENTED** | `conditions.py`, `duration_tracker.py` | duration_rounds field; tick_conditions() in play loop |
| Condition auto-removal on expiry | PHB p.309 | **IMPLEMENTED** | `conditions.py` | Conditions with duration_rounds expire automatically |
| Condition empty-dict format robustness | Engine infra | **IMPLEMENTED** | `conditions.py` | {cond_id: {}} no longer silently drops condition; _get_modifiers_for_condition_type() calls factory to get canonical ConditionModifiers; legacy list format (or any non-dict) raises ValueError. CLF-001..008. Batch AI/AM. |

---

## SECTION 5 — SAVING THROWS

| Mechanic | Source | Status | Engine File(s) | Notes / Gap Description |
|----------|--------|--------|----------------|--------------------------|
| Fortitude save base calculation | PHB p.174 | **IMPLEMENTED** | `save_resolver.py` | SAVE_FORT is Type 2 (base + CON baked at chargen). WO-ENGINE-SAVE-DOUBLE-COUNT-FIX-001: ability_mod no longer double-counted. |
| Reflex save base calculation | PHB p.174 | **IMPLEMENTED** | `save_resolver.py` | SAVE_REF is Type 2 (base + DEX baked at chargen). WO-ENGINE-SAVE-DOUBLE-COUNT-FIX-001. |
| Will save base calculation | PHB p.174 | **IMPLEMENTED** | `save_resolver.py` | SAVE_WILL is Type 2 (base + WIS baked at chargen). WO-ENGINE-SAVE-DOUBLE-COUNT-FIX-001. |
| Condition modifiers to saves | PHB p.310-311 | **IMPLEMENTED** | `save_resolver.py`, `schemas/conditions.py` | fort_save_modifier, ref_save_modifier, will_save_modifier in ConditionModifiers |
| Racial bonuses to saves (halfling +1 all) | PHB p.20 | **IMPLEMENTED** | `schemas/entity_fields.py` | RACIAL_SAVE_BONUS field; SAVE_BONUS_SPELLS for dwarves/gnomes |
| Negative level penalty to saves | PHB p.215 | **IMPLEMENTED** | `energy_drain_resolver.py`, `save_resolver.py` | NEGATIVE_LEVELS × -1 applied to saves |
| Natural 1 on save (auto-fail) | PHB p.174 | **IMPLEMENTED** | `save_resolver.py` | d20 = 1 → automatic failure |
| Natural 20 on save (auto-succeed) | PHB p.174 | **IMPLEMENTED** | `save_resolver.py` | d20 = 20 → automatic success |
| Spell Resistance check (d20 + caster level vs SR) | PHB p.177 | **IMPLEMENTED** | `save_resolver.py`, `spell_resolver.py` | SR function in save_resolver; now wired into spell resolution per-target loop (PHB p.177 order: SR before save). Spell Penetration bonus flows through. WO-ENGINE-SR-SPELL-PATH-001. Conjuration (creation) spells (web, grease, stinking_cloud, fog_cloud) set spell_resistance=False. WO-ENGINE-SPELLCASTING-DATA-CLEANUP-001. Batch AA. |
| Energy resistance (absorb first N damage) | PHB p.291 | **IMPLEMENTED** | `energy_resistance_resolver.py`, `schemas/entity_fields.py` | EF.ENERGY_RESISTANCES dict; absorbs first N damage per energy type. WO-ENGINE-ENERGY-RESISTANCE-001. |
| Evasion (no damage on successful Reflex save) | PHB p.50 | **IMPLEMENTED** | `spell_resolver.py`, `schemas/entity_fields.py` | EF.HAS_EVASION; Ref save success → 0 damage. Armor guard: none/light only. WO-ENGINE-EVASION-ARMOR-001. |
| Improved Evasion (half damage on failed Reflex) | PHB p.51 | **IMPLEMENTED** | `spell_resolver.py`, `schemas/entity_fields.py` | EF.IMPROVED_EVASION; failed Ref save → half damage. Monk class feature. WO-ENGINE-EVASION-ARMOR-001. |
| Spell save DC calculation (10 + spell level + ability mod) | PHB p.175 | **IMPLEMENTED** | `spell_resolver.py` | DC computed from CasterStats; ability mod from caster class |
| Spell target saves (TargetStats) | PHB p.175 | **IMPLEMENTED** | `play_loop.py`, `save_resolver.py` | _create_target_stats() now routes through canonical save_resolver.get_save_bonus(). Includes Divine Grace, save feats, racial bonuses, conditions, inspire courage. WO-ENGINE-SPELL-SAVE-UNIFY-001. |
| Concentration checks (damage during casting) | PHB p.175 | **IMPLEMENTED** | `play_loop.py` | Concentration break on damage; DC = 10 + damage + spell level. EF.CONCENTRATION_BONUS wired at chargen (ranks + CON_MOD). WO-ENGINE-CONCENTRATION-WRITE-001. |
| Concentration — vigorous motion | PHB p.175 | **PARTIAL** | `play_loop.py` | Vigorous motion DC check added; not all motion contexts covered. WO-ENGINE-CONCENTRATION-VIGOROUS-001. |
| Concentration — violent weather | PHB p.175 | **NOT STARTED** | — | No weather-based concentration DC |
| Concentration — entangled | PHB p.175 | **NOT STARTED** | — | Entangled condition does not trigger concentration penalty |
| Concentration — grappled | PHB p.175 | **IMPLEMENTED** | `play_loop.py` | Grappled condition triggers concentration DC 10 + spell level. DEBRIEF_WO-ENGINE-CONCENTRATION-GRAPPLE-001. |
| Arcane Spell Failure (armor) | PHB p.175 | **IMPLEMENTED** | `play_loop.py` | ASF d100 check in `_resolve_spell_cast()`; slot consumed on failure; V-only spells bypass; divine casters bypass. WO-ENGINE-ARCANE-SPELL-FAILURE-001. |
| Casting defensively (DC 15 Concentration or provoke AoO) | PHB p.140 | **IMPLEMENTED** | `aoo.py`, `play_loop.py` | DefensiveCastingIntent; Concentration check vs DC 15; success bypasses AoO. WO-ENGINE-DEFENSIVE-CASTING-001. |

---

## SECTION 6 — SKILLS (All 34 PHB Skills)

Note: All 34 skills are defined in `aidm/schemas/skills.py` with skill_id, ability, ACP, trained_only. The `skill_resolver.py` provides standard check + opposed check resolution. "Tracked" means ranks + ability modifier contribute to check resolution; "Enforced" means the skill is actively called in engine action flow.

| Skill | Source | Status | Engine File(s) | Notes / Gap Description |
|-------|--------|--------|----------------|--------------------------|
| Appraise | PHB p.67 | **PARTIAL** | `schemas/skills.py` | Defined and tracked; no active resolution path in engine action flow |
| Balance | PHB p.67 | **PARTIAL** | `schemas/skills.py`, `skill_resolver.py` | Defined; not triggered by terrain/prone actions in engine |
| Bluff | PHB p.68 | **PARTIAL** | `skill_resolver.py`, `feint_resolver.py` | Used for Feint opposed check; general Bluff not auto-triggered |
| Climb | PHB p.69 | **PARTIAL** | `schemas/skills.py` | Defined and tracked; not auto-triggered on movement over climbable terrain |
| Concentration | PHB p.69 | **IMPLEMENTED** | `skill_resolver.py`, `play_loop.py` | Concentration checks triggered during casting; DC 10 + damage + spell level |
| Craft | PHB p.70 | **PARTIAL** | `schemas/skills.py` | Defined; no item crafting system |
| Decipher Script | PHB p.71 | **PARTIAL** | `schemas/skills.py` | Defined; no scroll/cipher interaction system |
| Diplomacy | PHB p.71 | **PARTIAL** | `schemas/skills.py` | Defined; NPC relationship system exists but not linked to Diplomacy rolls |
| Disable Device | PHB p.72 | **PARTIAL** | `schemas/skills.py` | Defined; no trap interaction system |
| Disguise | PHB p.73 | **PARTIAL** | `schemas/skills.py` | Defined; no disguise/recognition system |
| Escape Artist | PHB p.73 | **PARTIAL** | `schemas/skills.py` | Defined; grapple escape not using Escape Artist (uses opposed grapple check) |
| Forgery | PHB p.74 | **PARTIAL** | `schemas/skills.py` | Defined; no document system |
| Gather Information | PHB p.74 | **PARTIAL** | `schemas/skills.py` | Defined; no information-gathering action system |
| Handle Animal | PHB p.74 | **PARTIAL** | `schemas/skills.py` | Defined; companion resolver exists but Handle Animal DC not enforced |
| Heal | PHB p.75 | **PARTIAL** | `schemas/skills.py` | Defined; stabilization (DC 15 Heal) and poison treatment (DC 15/25) not wired |
| Hide | PHB p.76 | **PARTIAL** | `schemas/skills.py`, `skill_resolver.py` | Defined; no stealth-based combat concealment system |
| Intimidate | PHB p.76 | **PARTIAL** | `schemas/skills.py` | Defined; no Intimidate → Shaken chain implemented |
| Jump | PHB p.77 | **PARTIAL** | `schemas/skills.py` | Defined; no jump action or movement modifier |
| Knowledge (Arcana) | PHB p.78 | **PARTIAL** | `schemas/skills.py` | Defined; no knowledge check trigger system |
| Knowledge (Dungeoneering) | PHB p.78 | **PARTIAL** | `schemas/skills.py` | Defined; no knowledge check trigger system |
| Knowledge (Nature) | PHB p.78 | **PARTIAL** | `schemas/skills.py` | Defined; no knowledge check trigger system |
| Knowledge (Religion) | PHB p.78 | **PARTIAL** | `schemas/skills.py` | Defined; no knowledge check trigger system |
| Knowledge (The Planes) | PHB p.78 | **PARTIAL** | `schemas/skills.py` | Defined; no knowledge check trigger system |
| Listen | PHB p.78 | **PARTIAL** | `schemas/skills.py` | Defined; no active Listen check triggering in exploration |
| Move Silently | PHB p.79 | **PARTIAL** | `schemas/skills.py`, `skill_resolver.py` | Defined; no stealth action system |
| Open Lock | PHB p.79 | **PARTIAL** | `schemas/skills.py` | Defined; no door/lock interaction system |
| Perform | PHB p.79 | **PARTIAL** | `schemas/skills.py` | Defined; no bardic performance skill-check enforcement |
| Profession | PHB p.80 | **PARTIAL** | `schemas/skills.py` | Defined; no economy system |
| Ride | PHB p.80 | **PARTIAL** | `schemas/skills.py` | Defined; mounted combat resolver exists but Ride DCs not auto-enforced |
| Search | PHB p.81 | **PARTIAL** | `schemas/skills.py` | Defined; stonecunning passive +2 tracked; no active search action loop |
| Sense Motive | PHB p.81 | **PARTIAL** | `skill_resolver.py`, `feint_resolver.py` | Used for Feint defense; general Sense Motive not triggered |
| Sleight of Hand | PHB p.81 | **PARTIAL** | `schemas/skills.py` | Defined; no pickpocket/conceal system |
| Spellcraft | PHB p.82 | **PARTIAL** | `schemas/skills.py` | Defined; no Spellcraft identification system in engine |
| Spot | PHB p.83 | **PARTIAL** | `schemas/skills.py` | Defined; no active perception loop |
| Survival | PHB p.83 | **PARTIAL** | `schemas/skills.py` | Defined; no wilderness navigation system |
| Swim | PHB p.84 | **PARTIAL** | `schemas/skills.py` | Defined; no water movement/drowning check integration |
| Tumble | PHB p.84 | **IMPLEMENTED** | `schemas/skills.py`, `skill_resolver.py`, `aoo.py` | DC 15 check wired in aoo.py lines 493–548; trained-only guard; `tumble_check` + `aoo_avoided_by_tumble` events emitted. Confirmed 2026-02-26. |
| Use Magic Device | PHB p.85 | **PARTIAL** | `schemas/skills.py` | Defined; no UMD resolution for scrolls/wands |
| Use Rope | PHB p.86 | **PARTIAL** | `schemas/skills.py` | Defined; no rope/binding system |
| Skill synergies | PHB p.65 | **IMPLEMENTED** | `skill_resolver.py`, `schemas/skills.py` | Synergy bonus system (+2 when 5+ ranks in source skill). DEBRIEF_WO-ENGINE-SKILL-SYNERGY-001. |
| Take 10 / Take 20 mechanics | PHB p.65 | **NOT STARTED** | — | No Take 10 or Take 20 enforcement; all checks use d20 rolls |
| Armor Check Penalty application | PHB p.65 | **IMPLEMENTED** | `skill_resolver.py`, `schemas/entity_fields.py` | ARMOR_CHECK_PENALTY field; ACP subtracted from relevant skills in skill_resolver |

---

## SECTION 7 — FEATS (~100 PHB Feats)

Feats are defined in `aidm/schemas/feats.py`. The feat_resolver provides prerequisite validation and modifier computation. "Registered" means the feat is in FEAT_REGISTRY. "Active" means the modifier is called in combat resolution. Feats not yet registered are NOT STARTED.

### 7a. Implemented/Active Feats (modifiers wired into combat)

| Feat | Source | Status | Engine File(s) | Notes / Gap Description |
|------|--------|--------|----------------|--------------------------|
| Power Attack | PHB p.98 | **IMPLEMENTED** | `feat_resolver.py`, `full_attack_resolver.py` | Attack-to-damage trade; 1:1 one-hand; 1:2 two-hand |
| Cleave | PHB p.92 | **IMPLEMENTED** | `attack_resolver.py`, `schemas/feats.py` | Free attack on adjacent foe after drop |
| Great Cleave | PHB p.94 | **IMPLEMENTED** | `attack_resolver.py`, `schemas/feats.py` | Unlimited cleaves per round |
| Dodge | PHB p.93 | **PARTIAL** | `feat_resolver.py`, `schemas/feats.py` | +1 dodge AC vs designated target; designating not enforced per-round |
| Mobility | PHB p.98 | **IMPLEMENTED** | `feat_resolver.py`, `aoo.py` | +4 dodge AC vs AoO from movement |
| Spring Attack | PHB p.100 | **IMPLEMENTED** | `attack_resolver.py`, `aoo.py`, `play_loop.py`, `action_economy.py` | Full-round; single melee; no AoO from target via filter_aoo_from_target; heavy armor blocked. Batch AH. SPRK-001–008. |
| Point Blank Shot | PHB p.98 | **IMPLEMENTED** | `feat_resolver.py` | +1 attack/damage within 30 ft |
| Precise Shot | PHB p.98 | **IMPLEMENTED** | `feat_resolver.py` | No -4 penalty for shooting into melee |
| Rapid Shot | PHB p.99 | **IMPLEMENTED** | `feat_resolver.py`, `full_attack_resolver.py` | Extra ranged attack at -2 all; wired. WO-ENGINE-RAPID-SHOT-001. |
| Weapon Focus | PHB p.102 | **IMPLEMENTED** | `feat_resolver.py` (canonical), `attack_resolver.py` (event) | +1 attack with chosen weapon. WO-ENGINE-WF-SCHEMA-FIX-001: unified to canonical `weapon_focus_{weapon_name}` key. 8/8 WFS + 8/8 WFC gates. |
| Weapon Specialization | PHB p.102 | **IMPLEMENTED** | `feat_resolver.py` | +2 damage with chosen weapon |
| Two-Weapon Fighting | PHB p.102 | **IMPLEMENTED** | `play_loop.py`, `schemas/feats.py` | -4/-4 with light offhand; wired in TWF play |
| Improved Two-Weapon Fighting | PHB p.96 | **IMPLEMENTED** | `schemas/feats.py`, `full_attack_resolver.py` | Second off-hand attack at BAB-5 |
| Greater Two-Weapon Fighting | PHB p.94 | **IMPLEMENTED** | `schemas/feats.py` | Third off-hand attack |
| Improved Initiative | PHB p.96 | **IMPLEMENTED** | `feat_resolver.py`, `combat_controller.py` | +4 initiative |
| Great Fortitude | PHB p.94 | **IMPLEMENTED** | `schemas/feats.py`, `save_resolver.py` | +2 Fort; wired into get_save_bonus(). |
| Iron Will | PHB p.97 | **IMPLEMENTED** | `schemas/feats.py`, `save_resolver.py` | +2 Will; wired into get_save_bonus(). |
| Lightning Reflexes | PHB p.97 | **IMPLEMENTED** | `schemas/feats.py`, `save_resolver.py` | +2 Ref; wired into get_save_bonus(). |
| Toughness | PHB p.101 | **IMPLEMENTED** | `schemas/feats.py`, `chargen/builder.py` | +3 HP per stack; stackable via .count(). Batch O. |
| Combat Reflexes | PHB p.92 | **IMPLEMENTED** | `combat_reflexes.py`, `aoo.py` | DEX mod additional AoOs per round |
| Improved Bull Rush | PHB p.96 | **IMPLEMENTED** | `schemas/feats.py`, `maneuver_resolver.py`, `play_loop.py` | AoO suppression + +4 STR bonus on bull rush. DEBRIEF_WO-ENGINE-IMPROVED-BULL-RUSH-001. |
| Improved Disarm | PHB p.96 | **IMPLEMENTED** | `schemas/feats.py`, `maneuver_resolver.py`, `play_loop.py` | AoO suppression + +4 bonus; counter-disarm suppressed. DEBRIEF_WO-ENGINE-IMPROVED-DISARM-001. |
| Improved Feint | PHB p.96 | **IMPLEMENTED** | `schemas/feats.py`, `feint_resolver.py` | Feint as move action |
| Improved Grapple | PHB p.96 | **IMPLEMENTED** | `schemas/feats.py`, `maneuver_resolver.py`, `play_loop.py` | AoO suppression + +4 grapple bonus. DEBRIEF_WO-ENGINE-IMPROVED-GRAPPLE-001. |
| Improved Overrun | PHB p.96 | **IMPLEMENTED** | `schemas/feats.py`, `maneuver_resolver.py` | AoO suppression + defender cannot avoid. Batch O. |
| Improved Sunder | PHB p.96 | **IMPLEMENTED** | `schemas/feats.py`, `maneuver_resolver.py`, `play_loop.py` | AoO suppression + +4 sunder bonus. Batch N. |
| Improved Trip | PHB p.96 | **IMPLEMENTED** | `schemas/feats.py`, `maneuver_resolver.py`, `play_loop.py` | AoO suppression + free attack after trip (if weapon provided). Batch N. |
| Mounted Combat | PHB p.98 | **PARTIAL** | `schemas/feats.py`, `mounted_combat.py` | Registered; mounted_combat resolver exists; Ride check to negate hit not wired |
| Ride-By Attack | PHB p.99 | **PARTIAL** | `schemas/feats.py` | Registered; move-attack-move-mounted not fully wired |
| Spirited Charge | PHB p.100 | **PARTIAL** | `schemas/feats.py` | Registered; ×2/×3 damage on mounted charge not auto-applied |
| Trample | PHB p.101 | **PARTIAL** | `schemas/feats.py` | Registered; no automatic hoof attack on overrun |
| Shot on the Run | PHB p.99 | **IMPLEMENTED** | `attack_resolver.py`, `aoo.py`, `play_loop.py`, `action_economy.py` | Full-round; single ranged; target AoO suppressed via filter_aoo_from_target (shared with Spring Attack); heavy armor blocked; range penalty still applies. Batch AH. SOTR-001–008. |
| Manyshot | PHB p.97 | **IMPLEMENTED** | `attack_resolver.py`, `play_loop.py`, `action_economy.py` | Standard action; single roll at −4 penalty; 2 damage_roll events on hit; 30-ft cap; BAB+11/+16 scaling CONSUME_DEFERRED. Batch AH. MS-001–008. |
| Improved Critical | PHB p.96 | **IMPLEMENTED** | `schemas/feats.py`, `attack_resolver.py` | Threat range doubled for chosen weapon. DEBRIEF_WO-ENGINE-IMPROVED-CRITICAL-001. |
| Blind-Fight | PHB p.91 | **IMPLEMENTED** | `schemas/feats.py`, `attack_resolver.py` | Reroll miss chance; `blind_fight_reroll` event emitted on every reroll. Batch O. |
| Combat Expertise | PHB p.92 | **IMPLEMENTED** | `schemas/feats.py`, `feat_resolver.py` | Trade attack bonus for AC dodge bonus. Batch O SAI — already wired. |
| Whirlwind Attack | PHB p.102 | **IMPLEMENTED** | `schemas/intents.py`, `attack_resolver.py`, `play_loop.py`, `action_economy.py` | WhirlwindAttackIntent; resolve_whirlwind_attack() loops resolve_attack() once per target at full attack bonus (PHB p.102: no iterative penalty). Feat gate + empty-target guard. Full-round action. WA-001–008. Batch AI. |
| Alertness | PHB p.91 | **IMPLEMENTED** | `skill_resolver.py` | +2 Listen/Spot via _SKILL_BONUS_FEATS dict in skill_resolver; untyped bonus stacks. Batch AH. SBF-001–002. |
| Athletic | PHB p.91 | **IMPLEMENTED** | `skill_resolver.py` | +2 Climb/Swim via _SKILL_BONUS_FEATS; untyped. Batch AH. SBF-004. |
| Acrobatic | PHB p.91 | **IMPLEMENTED** | `skill_resolver.py` | +2 Jump/Tumble via _SKILL_BONUS_FEATS; untyped. Batch AH. |
| Deceitful | PHB p.93 | **IMPLEMENTED** | `skill_resolver.py` | +2 Bluff/Forgery via _SKILL_BONUS_FEATS; untyped. Batch AH. |
| Deft Hands | PHB p.93 | **IMPLEMENTED** | `skill_resolver.py` | +2 Sleight of Hand/Use Rope via _SKILL_BONUS_FEATS; untyped. Batch AH. |
| Diligent | PHB p.93 | **IMPLEMENTED** | `skill_resolver.py` | +2 Appraise/Decipher Script via _SKILL_BONUS_FEATS; untyped. Batch AH. |
| Investigator | PHB p.97 | **IMPLEMENTED** | `skill_resolver.py` | +2 Gather Info/Search via _SKILL_BONUS_FEATS; untyped. Batch AH. SBF-008. |
| Negotiator | PHB p.97 | **IMPLEMENTED** | `skill_resolver.py` | +2 Diplomacy/Sense Motive via _SKILL_BONUS_FEATS; untyped. Batch AH. |
| Nimble Fingers | PHB p.97 | **IMPLEMENTED** | `skill_resolver.py` | +2 Disable Device/Open Lock via _SKILL_BONUS_FEATS; untyped. Batch AH. |
| Persuasive | PHB p.97 | **IMPLEMENTED** | `skill_resolver.py` | +2 Bluff/Intimidate via _SKILL_BONUS_FEATS; untyped; both skills fire independently. Batch AH. SBF-007. |
| Self-Sufficient | PHB p.99 | **IMPLEMENTED** | `skill_resolver.py` | +2 Heal/Survival via _SKILL_BONUS_FEATS; untyped. Batch AH. |
| Stealthy | PHB p.100 | **IMPLEMENTED** | `skill_resolver.py` | +2 Hide/Move Silently via _SKILL_BONUS_FEATS; untyped. Batch AH. SBF-005–006. |
| Spell Focus | PHB p.100 | **IMPLEMENTED** | `schemas/feats.py`, `spell_resolver.py` | +1 save DC per school; wired into spell_resolver DC computation. WO-ENGINE-SPELL-FOCUS-001. |
| Greater Spell Focus | PHB p.94 | **IMPLEMENTED** | `schemas/feats.py`, `spell_resolver.py` | +1 additional DC per school; stacks with Spell Focus for +2 total. WO-ENGINE-SPELL-FOCUS-DC-001. |
| Spell Penetration | PHB p.100 | **IMPLEMENTED** | `schemas/feats.py`, `save_resolver.py` | +2 CL for SR checks; wired into check_spell_resistance(). DEBRIEF_WO-ENGINE-SPELL-PENETRATION-001. |
| Greater Spell Penetration | PHB p.94 | **IMPLEMENTED** | `schemas/feats.py`, `save_resolver.py` | +4 total with Spell Penetration; wired. DEBRIEF_WO-ENGINE-SPELL-PENETRATION-001. |
| Armor Proficiency (Light/Medium/Heavy) | PHB p.91 | **PARTIAL** | `schemas/feats.py` | Registered; proficiency not enforced (no ASF/ACP enforcement) |
| Shield Proficiency / Tower Shield | PHB p.99 | **PARTIAL** | `schemas/feats.py` | Registered; not enforced |
| Extra Turning | PHB p.94 | **IMPLEMENTED** | `schemas/feats.py`, `chargen/builder.py` | +4 turning uses; stackable via .count(); applied to TURN_UNDEAD_USES_MAX at chargen. DEBRIEF_WO-ENGINE-EXTRA-TURNING-001. |
| Natural Spell | PHB p.97 | **PARTIAL** | `schemas/feats.py` | Registered; Wild Shape + spellcasting not wired |
| Track | PHB p.101 | **PARTIAL** | `schemas/feats.py` | Registered; no tracking system |
| Endurance | PHB p.93 | **PARTIAL** | `schemas/feats.py` | Registered (+4 vs environmental checks); not wired |
| Diehard | PHB p.93 | **IMPLEMENTED** | `schemas/feats.py`, `dying_resolver.py` | Stable at -1 to -9; wired to dying_resolver. DEBRIEF_WO-ENGINE-DIEHARD-001. |
| Scribe Scroll | PHB p.99 | **PARTIAL** | `schemas/feats.py` | Registered; no scroll creation system |
| Brew Potion | PHB p.91 | **PARTIAL** | `schemas/feats.py` | Registered; no potion brewing system |
| Craft Wondrous Item | PHB p.92 | **PARTIAL** | `schemas/feats.py` | Registered; no item creation system |

### 7b. PHB Feats Not Yet Registered

| Feat | Source | Status | Notes |
|------|--------|--------|-------|
| Augment Summoning | PHB p.91 | **NOT STARTED** | No summoning system |
| Deflect Arrows | PHB p.93 | **IMPLEMENTED** | `attack_resolver.py`, `combat_controller.py`, `play_loop.py`, `schemas/entity_fields.py`, `chargen/builder.py` | Reactive gate in resolve_attack() after hit, before damage_roll; conditions: feat present + ranged weapon + free hand (EF.FREE_HANDS≥1) + not flat-footed + not used this round; deflect_arrows_used list in active_combat; EF.FREE_HANDS set at chargen (both paths) via inventory scan fallback. DA-001..008. FHS-001..008. Batch AI/AM. |
| Far Shot | PHB p.94 | **IMPLEMENTED** | `attack_resolver.py` | compute_range_penalty(feats, distance_ft, weapon_dict); ranged: increment×3//2 (integer, no float); thrown: increment×2; penalty = −2 per full effective increment. Trusted-caller model. FSHOT-001–008. Batch AI. |
| Leadership | PHB p.97 / DMG | **NOT STARTED** | DMG system; no cohort/follower framework |
| Empower Spell (metamagic) | PHB p.93 | **IMPLEMENTED** | `metamagic_resolver.py` | ×1.5 variable numeric effects |
| Enlarge Spell (metamagic) | PHB p.93 | **PARTIAL** | `metamagic_resolver.py` | Registered; range doubling not wired |
| Extend Spell (metamagic) | PHB p.94 | **IMPLEMENTED** | `metamagic_resolver.py` | Duration ×2 |
| Heighten Spell (metamagic) | PHB p.95 | **IMPLEMENTED** | `metamagic_resolver.py` | Raises save DC to target level |
| Maximize Spell (metamagic) | PHB p.97 | **IMPLEMENTED** | `metamagic_resolver.py` | Maximum dice value; no RNG |
| Quicken Spell (metamagic) | PHB p.98 | **IMPLEMENTED** | `metamagic_resolver.py` | Swift action cast; no AoO |
| Silent Spell (metamagic) | PHB p.100 | **IMPLEMENTED** | `has_verbal` flag on SpellDefinition; silent metamagic bypasses verbal requirement. WO-ENGINE-SILENT-SPELL-001. |
| Still Spell (metamagic) | PHB p.100 | **IMPLEMENTED** | `is_still` guard bypasses ASF check; somatic-free cast. WO-ENGINE-STILL-SPELL-001. |
| Widen Spell (metamagic) | PHB p.102 | **NOT STARTED** | Not in metamagic_resolver |
| Spell Mastery (wizard) | PHB p.100 | **NOT STARTED** | Prepare without spellbook; no wizard spellbook system |
| Craft Magic Arms and Armor | PHB p.92 | **NOT STARTED** | No item creation |
| Craft Rod | PHB p.92 | **NOT STARTED** | No item creation |
| Craft Staff | PHB p.92 | **NOT STARTED** | No item creation |
| Craft Wand | PHB p.92 | **NOT STARTED** | No item creation |
| Forge Ring | PHB p.94 | **NOT STARTED** | No item creation |
| Improved Counterspell | PHB p.96 | **NOT STARTED** | No counterspell system |
| Improved Familiar | PHB p.96 | **NOT STARTED** | No familiar system |
| Run | PHB p.99 | **IMPLEMENTED** | `play_loop.py`, `action_economy.py` | RunIntent; ×4 speed (×3 with heavy armor); full-round action. DEBRIEF_WO-ENGINE-RUN-ACTION-001. |
| Mounted Archery | PHB p.98 | **NOT STARTED** | No mounted archery system |
| Exotic Weapon Proficiency | PHB p.94 | **NOT STARTED** | No weapon proficiency enforcement system |
| Simple/Martial Weapon Proficiency | PHB p.100 | **NOT STARTED** | No proficiency enforcement |
| Multiattack | MM feat | **IMPLEMENTED** | `feat_resolver.py`, `natural_attack_resolver.py` | Secondary natural attacks at -2 instead of -5. DEBRIEF_WO-ENGINE-MULTIATTACK-001. |
| Secondary natural attack ½ STR | PHB p.314 | **IMPLEMENTED** | `natural_attack_resolver.py`, `attack_resolver.py` | Secondary natural attacks use grip="off-hand" → `int(str_mod * 0.5)`. WO-ENGINE-ATTACK-MODIFIER-FIDELITY-001. |
| Stunning Fist | PHB p.101 | **IMPLEMENTED** | `attack_resolver.py`, `chargen/builder.py`, `rest_resolver.py`, `schemas/entity_fields.py` | EF.HAS_STUNNING_FIST, STUNNING_FIST_USES, STUNNING_FIST_USED. Must declare before roll; use consumed on miss. Fort DC = 10 + (level//2) + WIS_mod. STUNNED 1 round on failure. Monk gets monk_level uses; non-monk with feat gets char_level//4. Resets on overnight rest. 8 gate tests SF-001–008. WO-ENGINE-AG-WO1. |
| Improved Unarmed Strike | PHB p.96 | **NOT STARTED** | No unarmed strike system beyond natural attacks |

---

## SECTION 8 — SPELLCASTING SYSTEM

| Mechanic | Source | Status | Engine File(s) | Notes / Gap Description |
|----------|--------|--------|----------------|--------------------------|
| Spell slots (prepared casters) | PHB p.177 | **IMPLEMENTED** | `schemas/entity_fields.py`, `spell_prep_resolver.py` | SPELL_SLOTS / SPELL_SLOTS_MAX; slot decremented on cast; refilled on rest |
| Spell slots (spontaneous casters) | PHB p.177 | **IMPLEMENTED** | `schemas/entity_fields.py` | Same slot structure; SPELLS_KNOWN used instead of prepared |
| Spell preparation (wizard/cleric/druid) | PHB p.177 | **IMPLEMENTED** | `spell_prep_resolver.py`, `play_loop.py` | PrepareSpellsIntent → SPELLS_PREPARED; slot count validated |
| Spell preparation — wizard spellbook | PHB p.178 | **NOT STARTED** | — | No spellbook object; wizard may prepare any known spell (no spellbook restriction) |
| Bonus spells from high ability score | PHB p.8 | **PARTIAL** | `chargen/spellcasting.py` | Bonus slots included in SPELL_SLOTS at chargen; dynamic recalculation on ability change not wired |
| Arcane spell failure (armor) | PHB p.123 | **IMPLEMENTED** | `play_loop.py` | ASF% d100 check in `_resolve_spell_cast()`; slot consumed on failure. WO-ENGINE-ARCANE-SPELL-FAILURE-001. |
| Spell components — V (verbal) | PHB p.174 | **IMPLEMENTED** | `play_loop.py` | Verbal block enforced; silenced/deafened condition prevents verbal spells. DEBRIEF_WO-ENGINE-VERBAL-SPELL-BLOCK-001. |
| Spell components — S (somatic) | PHB p.174 | **IMPLEMENTED** | `play_loop.py`, `schemas/entity_fields.py` | FREE_HAND_BLOCKED guard; hand-free requirement enforced; grapple/pin block somatic. DEBRIEF_WO-ENGINE-SOMATIC-HAND-FREE-001. |
| Spell components — M (material) | PHB p.174 | **NOT STARTED** | — | No material component inventory or consumption |
| Spell components — F (focus) | PHB p.174 | **NOT STARTED** | — | No focus item tracking |
| Spell components — DF (divine focus) | PHB p.174 | **NOT STARTED** | — | No holy symbol requirement enforcement |
| Spell components — XP (experience) | PHB p.174 | **NOT STARTED** | — | No XP cost deduction for spells |
| Caster level effects (variable dice/range/etc.) | PHB p.174 | **IMPLEMENTED** | `spell_resolver.py`, `data/spell_definitions.py`, `play_loop.py` | SpellDefinition.effective_damage_dice(cl) + effective_duration_rounds(cl); fireball/lightning_bolt 1d6/CL max 10d6; haste/slow 1r/CL, bless 10r/CL, cause_fear 1r/CL. Both resolver and play_loop paths updated for parity. Note: `requires_attack_roll` write-only (CONSUME_DEFERRED); magic missile multi-missile CL scale CONSUME_DEFERRED. CDS-001..008, CDU-001..008. Batch AM. |
| Multiclass spellcasting — independent CL per class | PHB p.57 | **IMPLEMENTED** | `play_loop.py` | `_get_caster_level(entity, use_secondary)` helper; `_create_caster_stats(use_secondary=True)` routes CL_2; SpellCastIntent.use_secondary flag. WO-ENGINE-CASTER-LEVEL-2-001. |
| Spell DC (10 + spell level + ability mod) | PHB p.175 | **IMPLEMENTED** | `spell_resolver.py` | Full DC computation in SpellResolver |
| SR penetration check (d20 + CL vs SR) | PHB p.175 | **IMPLEMENTED** | `save_resolver.py` | SRCheck schema; full roll vs entity SR |
| Dispel magic check | PHB p.223 | **NOT STARTED** | — | No dispel mechanic; duration_tracker has no dispel interface |
| Counterspelling | PHB p.178 | **NOT STARTED** | — | No counterspell action or opposed check |
| Concentration checks (damage) | PHB p.175 | **IMPLEMENTED** | `play_loop.py` | Concentration break triggers on damage during casting |
| Concentration checks (other causes) | PHB p.175 | **PARTIAL** | `play_loop.py` | Vigorous motion and grappled now covered. Entangled and violent weather still NOT STARTED. FINDING-ENGINE-CONCENTRATION-ENTANGLED-001 OPEN. |
| Duration tracking | PHB p.175 | **IMPLEMENTED** | `duration_tracker.py` | ActiveSpellEffect; rounds_remaining; tick on end of each turn |
| Duration — concentration (ends on break) | PHB p.175 | **IMPLEMENTED** | `duration_tracker.py`, `play_loop.py` | concentration=True flag; caster damage → break |
| Duration — discharge (touch spells held) | PHB p.175 | **NOT STARTED** | — | Touch spell "charge held" mechanic not implemented |
| AoE rasterization — burst | PHB p.176 | **IMPLEMENTED** | `aoe_rasterizer.py` | Octagonal burst; discrete distance formula |
| AoE rasterization — cone | PHB p.176 | **IMPLEMENTED** | `aoe_rasterizer.py` | Triangular cone from caster; 8-directional |
| AoE rasterization — line | PHB p.176 | **IMPLEMENTED** | `aoe_rasterizer.py` | 5-foot wide line; 120-ft range |
| AoE rasterization — spread | PHB p.176 | **PARTIAL** | `aoe_rasterizer.py` | SPREAD listed in enum but "not yet implemented" per module comment |
| AoE rasterization — cylinder | PHB p.176 | **PARTIAL** | `aoe_rasterizer.py` | CYLINDER enum exists; same as burst for 2D grid |
| AoE rasterization — emanation | PHB p.176 | **NOT STARTED** | — | Emanation shape (from creature) not implemented |
| Touch spells (melee touch attack on cast) | PHB p.176 | **IMPLEMENTED** | `spell_resolver.py` | SpellTarget.TOUCH; touch attack resolved against target |
| Ray spells (ranged touch attack) | PHB p.176 | **IMPLEMENTED** | `spell_resolver.py` | SpellTarget.RAY; ranged touch attack rolled |
| Polymorph mechanics | PHB p.263 | **PARTIAL** | `wild_shape_resolver.py` | Wild Shape is the primary implementation; general polymorph spell (for targets) not in SPELL_REGISTRY as full mechanic |
| Metamagic — Empower | PHB p.93 | **IMPLEMENTED** | `metamagic_resolver.py` | +2 slot; ×1.5 variable numeric effects |
| Metamagic — Maximize | PHB p.97 | **IMPLEMENTED** | `metamagic_resolver.py` | +3 slot; maximum die value |
| Metamagic — Extend | PHB p.94 | **IMPLEMENTED** | `metamagic_resolver.py` | +1 slot; duration ×2 |
| Metamagic — Heighten | PHB p.95 | **IMPLEMENTED** | `metamagic_resolver.py` | Variable slot; raises save DC |
| Metamagic — Quicken | PHB p.98 | **IMPLEMENTED** | `metamagic_resolver.py` | +4 slot; swift action; no AoO |
| Metamagic — Enlarge | PHB p.93 | **IMPLEMENTED** | `metamagic_resolver.py` | +1 slot; registered in METAMAGIC_SLOT_COST + _FEAT_NAMES. Range doubling effect deferred (registration-only). WO-ENGINE-METAMAGIC-COMPLETION-001. Batch AA. |
| Metamagic — Silent | PHB p.100 | **IMPLEMENTED** | `metamagic_resolver.py`, `play_loop.py` | `has_verbal` flag; verbal-free cast. WO-ENGINE-SILENT-SPELL-001. |
| Metamagic — Still | PHB p.100 | **IMPLEMENTED** | `metamagic_resolver.py`, `play_loop.py` | `is_still` guard; ASF bypass. WO-ENGINE-STILL-SPELL-001. |
| Metamagic — Widen | PHB p.102 | **IMPLEMENTED** | `metamagic_resolver.py` | +3 slot; registered in METAMAGIC_SLOT_COST + _FEAT_NAMES. AoE doubling effect deferred (registration-only). WO-ENGINE-METAMAGIC-COMPLETION-001. Batch AA. Completes 9/9 PHB metamagic feats. |
| Spontaneous casting (cleric cure/inflict) | PHB p.32 | **IMPLEMENTED** | `play_loop.py` | Cleric cure redirect before V/S/ASF guards; SpellDefinition rewritten; declared slot consumed. DEBRIEF_WO-ENGINE-CLERIC-SPONTANEOUS-001. FINDING-ENGINE-SPONTANEOUS-ALIGNMENT-001 (LOW, no alignment check). |

---

## SECTION 9 — SPELLS BY CATEGORY

The SPELL_REGISTRY in `aidm/data/spell_definitions.py` contains approximately 733 spells (215 prior + 518 PCGen RSRD stubs added by STRAT-OSS-INGESTION-SPRINT-001 WO2). Prior entries have full PHB fidelity. PCGen stubs have correct school/level/components/SR; target_type/effect_type/damage_type inferred heuristically. Coverage is now broad (≥90% PHB spells by name).

### 9a. Damage Spells

| Spell | Level | Source | Status | Notes |
|-------|-------|--------|--------|-------|
| Fireball | 3 | PHB p.231 | **IMPLEMENTED** | Burst; 1d6/CL (max 10d6); Ref half; in SPELL_REGISTRY |
| Burning Hands | 1 | PHB p.207 | **IMPLEMENTED** | Cone; 1d4/CL (max 5d4); Ref half; in SPELL_REGISTRY |
| Lightning Bolt | 3 | PHB p.248 | **IMPLEMENTED** | Line; 1d6/CL (max 10d6); Ref half; in SPELL_REGISTRY |
| Cone of Cold | 5 | PHB p.212 | **IMPLEMENTED** | Cone; 1d6/CL (max 15d6); Ref half; in SPELL_REGISTRY |
| Magic Missile | 1 | PHB p.251 | **IMPLEMENTED** | Single; 1d4+1/missile (no save, auto-hit); in SPELL_REGISTRY |
| Scorching Ray | 2 | PHB p.274 | **IMPLEMENTED** | Ray; 4d6/ray; ranged touch; in SPELL_REGISTRY |
| Melf's Acid Arrow | 2 | PHB p.253 | **IMPLEMENTED** | Ray; 2d4/round; in SPELL_REGISTRY |
| Acid Splash (0) | 0 | PHB p.196 | **PARTIAL** | Not in SPELL_REGISTRY; cantrip coverage incomplete |
| Flame Strike | 5 | PHB p.231 | **NOT STARTED** | No entry in SPELL_REGISTRY |
| Disintegrate | 6 | PHB p.222 | **NOT STARTED** | No entry in SPELL_REGISTRY |
| Finger of Death | 7 | PHB p.230 | **NOT STARTED** | No entry |
| Slay Living | 5 | PHB p.279 | **NOT STARTED** | No entry |
| Power Word Kill | 9 | PHB p.265 | **NOT STARTED** | No entry |
| Wail of the Banshee | 9 | PHB p.298 | **NOT STARTED** | No entry |

### 9b. Healing Spells

| Spell | Level | Source | Status | Notes |
|-------|-------|--------|--------|-------|
| Cure Light Wounds | 1 | PHB p.215 | **IMPLEMENTED** | 1d8+1/CL (max +5); touch; in SPELL_REGISTRY |
| Cure Moderate Wounds | 2 | PHB p.216 | **IMPLEMENTED** | 2d8+1/CL (max +10); touch; in SPELL_REGISTRY |
| Cure Serious Wounds | 3 | PHB p.216 | **IMPLEMENTED** | 3d8+1/CL (max +15); touch; in SPELL_REGISTRY |
| Cure Critical Wounds | 4 | PHB p.215 | **NOT STARTED** | No entry in SPELL_REGISTRY |
| Heal | 6 | PHB p.238 | **NOT STARTED** | No entry |
| Mass Cure Light Wounds | 5 | PHB p.254 | **NOT STARTED** | No entry |
| Restoration | 4 | PHB p.272 | **NOT STARTED** | No entry; negative level removal also DEFERRED |
| Raise Dead | 5 | PHB p.268 | **NOT STARTED** | No entry; no resurrection mechanics |

### 9c. Buff Spells

| Spell | Level | Source | Status | Notes |
|-------|-------|--------|--------|-------|
| Mage Armor | 1 | PHB p.249 | **IMPLEMENTED** | +4 AC (armor type); buff; in SPELL_REGISTRY |
| Shield | 1 | PHB p.278 | **IMPLEMENTED** | +4 shield AC; self; in SPELL_REGISTRY |
| Bull's Strength | 2 | PHB p.207 | **IMPLEMENTED** | +4 enhancement STR; touch; in SPELL_REGISTRY |
| Haste | 3 | PHB p.239 | **IMPLEMENTED** | Multi-target buff; hasted condition; in SPELL_REGISTRY |
| Bear's Endurance | 2 | PHB p.203 | **IMPLEMENTED** | +4 CON; in SPELL_REGISTRY (WO-036) |
| Cat's Grace | 2 | PHB p.208 | **IMPLEMENTED** | +4 DEX; in SPELL_REGISTRY (WO-036) |
| Eagle's Splendor | 2 | PHB p.225 | **IMPLEMENTED** | +4 CHA; in SPELL_REGISTRY (WO-036) |
| Fox's Cunning | 2 | PHB p.233 | **IMPLEMENTED** | +4 INT; in SPELL_REGISTRY (WO-036) |
| Owl's Wisdom | 2 | PHB p.259 | **IMPLEMENTED** | +4 WIS; in SPELL_REGISTRY (WO-036) |
| Blur | 2 | PHB p.207 | **IMPLEMENTED** | 20% miss; blur condition; in SPELL_REGISTRY (WO-036) |
| Invisibility | 2 | PHB p.245 | **IMPLEMENTED** | 50% miss; invisible condition; in SPELL_REGISTRY (WO-036) |
| Mirror Image | 2 | PHB p.254 | **NOT STARTED** | No image duplication mechanic |
| Bless | 1 | PHB p.206 | **IMPLEMENTED** | +1 morale attack/fear; in SPELL_REGISTRY (WO-036) |
| Barkskin | 2 | PHB p.202 | **NOT STARTED** | No entry (natural armor enhancement) |
| Aid | 2 | PHB p.196 | **NOT STARTED** | No entry |
| Greater Invisibility | 4 | PHB p.245 | **NOT STARTED** | No entry |
| Stoneskin | 4 | PHB p.284 | **NOT STARTED** | No entry; would need DR mechanic |
| Fly | 3 | PHB p.232 | **NOT STARTED** | No flight movement system |
| Enlarge Person | 1 | PHB p.226 | **NOT STARTED** | No size change mechanic |
| Reduce Person | 1 | PHB p.269 | **NOT STARTED** | No size change mechanic |

### 9d. Debuff / Condition Spells

| Spell | Level | Source | Status | Notes |
|-------|-------|--------|--------|-------|
| Hold Person | 3 | PHB p.241 | **IMPLEMENTED** | Will negates; paralyzed; in SPELL_REGISTRY |
| Slow | 3 | PHB p.280 | **IMPLEMENTED** | Will negates; slowed condition; in SPELL_REGISTRY |
| Blindness/Deafness | 2 | PHB p.206 | **IMPLEMENTED** | Fort negates; blinded condition; in SPELL_REGISTRY |
| Web | 2 | PHB p.301 | **IMPLEMENTED** | Ref partial; entangled; in SPELL_REGISTRY |
| Fear | 4 | PHB p.229 | **IMPLEMENTED** | Will partial; frightened; in SPELL_REGISTRY (WO-036) |
| Ray of Enfeeblement | 1 | PHB p.269 | **IMPLEMENTED** | Ray; STR damage; in SPELL_REGISTRY (WO-036) |
| Ray of Exhaustion | 3 | PHB p.269 | **IMPLEMENTED** | Ray; exhausted; in SPELL_REGISTRY (WO-036) |
| Bestow Curse | 3 | PHB p.203 | **NOT STARTED** | No curse mechanic |
| Feeblemind | 5 | PHB p.229 | **NOT STARTED** | No entry |
| Hold Monster | 5 | PHB p.241 | **NOT STARTED** | No entry |
| Power Word Stun | 8 | PHB p.265 | **NOT STARTED** | No entry |
| Flesh to Stone | 6 | PHB p.232 | **NOT STARTED** | No petrify mechanic |
| Dominate Person | 5 | PHB p.224 | **NOT STARTED** | No mind control system |

### 9e. Summoning / Teleportation

| Spell | Level | Source | Status | Notes |
|-------|-------|--------|--------|-------|
| Summon Monster I–IX | 1–9 | PHB p.285 | **NOT STARTED** | No summoning framework |
| Summon Nature's Ally I–IX | 1–9 | PHB p.286 | **PARTIAL** | Animal companion system exists; instant summoning not wired |
| Dimension Door | 4 | PHB p.222 | **NOT STARTED** | No planar/teleport movement |
| Teleport | 5 | PHB p.292 | **NOT STARTED** | No teleportation system |
| Plane Shift | 5/7 | PHB p.262 | **NOT STARTED** | No planar travel |
| Gate | 9 | PHB p.234 | **NOT STARTED** | No planar gate |

### 9f. Divination / Illusion / Enchantment / Necromancy / Transmutation

| Spell | Level | Source | Status | Notes |
|-------|-------|--------|--------|-------|
| Detect Magic | 0 | PHB p.219 | **IMPLEMENTED** | Utility; concentration; in SPELL_REGISTRY |
| True Strike | 1 | PHB p.296 | **IMPLEMENTED** | +20 attack, ignore concealment; in SPELL_REGISTRY (WO-036) |
| Charm Person | 1 | PHB p.209 | **NOT STARTED** | No charm/compulsion system |
| Sleep | 1 | PHB p.280 | **IMPLEMENTED** | Will negates; unconscious; in SPELL_REGISTRY (WO-036) |
| Color Spray | 1 | PHB p.210 | **NOT STARTED** | No entry |
| Glitterdust | 2 | PHB p.236 | **NOT STARTED** | No entry |
| Inflict Light Wounds | 1 | PHB p.244 | **IMPLEMENTED** | Touch; 1d8+CL force-damage undead; in SPELL_REGISTRY (WO-036) |
| Cause Fear | 1 | PHB p.208 | **IMPLEMENTED** | Will; shaken/frightened; in SPELL_REGISTRY (WO-036) |
| Enervation | 4 | PHB p.226 | **NOT STARTED** | No entry; energy drain is separate system |
| Animate Dead | 3 | PHB p.199 | **NOT STARTED** | No undead creation system |
| Energy Drain | 9 | PHB p.226 | **DEFERRED** | energy_drain_resolver.py handles bestowed negative levels; spell form deferred |
| Wish / Miracle | 9 | PHB p.302/254 | **NOT STARTED** | No entry |
| Time Stop | 9 | PHB p.294 | **NOT STARTED** | No entry |
| Dispel Magic | 3 | PHB p.223 | **NOT STARTED** | No dispel mechanic in duration_tracker |

---

## SECTION 10 — CLASS FEATURES

### 10a. Barbarian

| Feature | Source | Status | Engine File(s) | Notes / Gap Description |
|---------|--------|--------|----------------|--------------------------|
| Rage (+4 STR/CON, +2 Will, -2 AC) | PHB p.25 | **IMPLEMENTED** | `rage_resolver.py` | RageIntent; activation, per-turn tick, end-of-rage fatigue |
| Rage duration (3 + CON mod rounds) | PHB p.25 | **IMPLEMENTED** | `rage_resolver.py` | RAGE_ROUNDS_REMAINING field |
| Rage uses per day (scaling by level) | PHB p.25 | **IMPLEMENTED** | `rage_resolver.py` | RAGE_USES_REMAINING; 1 to 6 per day by level |
| Post-rage fatigue | PHB p.25 | **IMPLEMENTED** | `rage_resolver.py` | FATIGUED field set to True after rage ends |
| Rage HP transition (+2 HP/HD enter, -2 HP/HD exit) | PHB p.25 | **IMPLEMENTED** | `rage_resolver.py` | HP_MAX and HP_CURRENT adjust by 2×total_HD on enter/exit; unconscious event if HP≤0 after exit. WO-ENGINE-RAGE-HP-TRANSITION-001. |
| Fast Movement (+10 speed) | PHB p.25 | **IMPLEMENTED** | `movement_resolver.py`, `chargen/builder.py` | EF.FAST_MOVEMENT_BONUS +10 at chargen; heavy armor or heavy load suppresses. Medium load OK (PHB p.25). WO-ENGINE-FAST-MOVEMENT-LOAD-FIX-001. |
| Uncanny Dodge (Dex to AC when flat-footed) | PHB p.25 | **IMPLEMENTED** | `attack_resolver.py` | _UD_THRESHOLDS: barbarian L2, rogue L4. Ranger removed. WO-ENGINE-UNCANNY-DODGE-CLASS-FIX-001. |
| Trap Sense (+1 Ref vs traps per 3 levels) | PHB p.26 | **IMPLEMENTED** | `schemas/entity_fields.py`, `chargen/builder.py`, `core/save_resolver.py` | EF.TRAP_SENSE_BONUS = (barb_level // 3) + (rogue_level // 3). Chargen write; resolver consume on REF + 'trap' descriptor. TSB-AE-001–008. CONSUME_DEFERRED: AC vs traps (FINDING-ENGINE-TRAP-SENSE-AC-001). WO-AE-WO4. |
| Damage Reduction (DR X/-) | PHB p.26 | **IMPLEMENTED** | `damage_reduction.py`, `chargen/builder.py` | EF.DAMAGE_REDUCTIONS list of dicts; barbarian DR/- set by level at chargen. DEBRIEF_WO-ENGINE-BARBARIAN-DR-001. |
| Improved Uncanny Dodge (flank immunity) | PHB p.26 | **IMPLEMENTED** | `schemas/entity_fields.py`, `sneak_attack.py` | EF.HAS_IMPROVED_UNCANNY_DODGE; flanking rogue must be 4+ levels higher. gate(Q-WO2). |
| Greater Rage (+6 STR/CON, +3 Will) | PHB p.26 | **IMPLEMENTED** | `rage_resolver.py` | L11+ barbarian gets +6/+6/+3/-2. WO-ENGINE-RAGE-PROGRESSION-001. Batch AA. |
| Indomitable Will (extra Will in rage) | PHB p.26 | **IMPLEMENTED** | `save_resolver.py`, `rage_resolver.py` | Barbarian L14+ gets +4 Will vs enchantment while raging. Set via TEMPORARY_MODIFIERS indomitable_will_active. WO-ENGINE-STILL-MIND-INDOMITABLE-WILL-001. Batch AB. |
| Tireless Rage (no post-rage fatigue) | PHB p.27 | **IMPLEMENTED** | `rage_resolver.py` | L17+ barbarian skips FATIGUED + fatigue penalties on rage end. HP loss still fires. WO-ENGINE-RAGE-PROGRESSION-001. Batch AA. |
| Mighty Rage (+8 STR/CON, +4 Will) | PHB p.27 | **IMPLEMENTED** | `rage_resolver.py` | L20+ barbarian gets +8/+8/+4/-2. HP gain/loss scales with tier. WO-ENGINE-RAGE-PROGRESSION-001. Batch AA. |

### 10b. Bard

| Feature | Source | Status | Engine File(s) | Notes / Gap Description |
|---------|--------|--------|----------------|--------------------------|
| Inspire Courage (morale bonus to attack/damage/fear saves) | PHB p.29 | **IMPLEMENTED** | `bardic_music_resolver.py`, `save_resolver.py` | BardicMusicIntent; +1 to +4 by level; 8-round duration; WO-ENGINE-BARDIC-MUSIC-001. WO-AE-WO3: IC save bonus now scoped to fear/charm descriptors only in get_save_bonus() (PHB p.29 — was firing on ALL saves). BSS-AE-001–004. |
| Inspire Courage — level scaling (+1/+2/+3/+4) | PHB p.29 | **IMPLEMENTED** | `bardic_music_resolver.py` | get_inspire_courage_bonus() at levels 1-7/8-13/14-19/20 |
| Inspire Courage — ends on bard incapacitation | PHB p.29 | **IMPLEMENTED** | `bardic_music_resolver.py` | WO-ENGINE-BARDIC-DURATION-001; DEFEATED/DYING/DEAFENED ends effect |
| Bardic Music uses per day (bard level) | PHB p.29 | **IMPLEMENTED** | `schemas/entity_fields.py` | BARDIC_MUSIC_USES_REMAINING field |
| Bardic Knowledge | PHB p.29 | **NOT STARTED** | — | No Knowledge check with Bardic Knowledge bonus |
| Countersong | PHB p.29 | **NOT STARTED** | — | No Perform check vs sonic/language effects |
| Fascinate | PHB p.29 | **IMPLEMENTED** | `fascinate_resolver.py`, `play_loop.py`, `schemas/intents.py`, `schemas/entity_fields.py` | FascinateIntent; up to bard_level//3 targets; Will DC = 10 + (bard_level//2) + CHA_mod; FASCINATED condition on failure; requires PERFORM_RANKS ≥ 3; blocked if target has in_combat condition; uses BARDIC_MUSIC_USES_REMAINING resource. 8 gate tests FA-001–008. WO-ENGINE-AG-WO4. |
| Inspire Competence | PHB p.30 | **NOT STARTED** | — | +2 competence to skill not implemented |
| Suggestion (bardic) | PHB p.30 | **NOT STARTED** | — | No Suggestion bardic performance |
| Inspire Greatness | PHB p.30 | **IMPLEMENTED** | `bardic_music_resolver.py`, `attack_resolver.py`, `save_resolver.py` | resolve_inspire_greatness(): bard L9+, 12+ Perform; 2d10+(2×Con) temp HP; inspire_greatness_bab=2 competence (TEMPORARY_MODIFIERS, non-stacking max); inspire_greatness_fort=1 Fort competence. tick_inspire_greatness() clears on expiry. attack_resolver reads bab bonus. save_resolver reads Fort bonus. Batch AD. IG-001–008. |
| Song of Freedom | PHB p.30 | **NOT STARTED** | — | No breaking-enchantment performance |
| Inspire Heroics | PHB p.30 | **NOT STARTED** | — | No bardic heroics performance |
| Mass Suggestion | PHB p.30 | **NOT STARTED** | — | No mass bardic Suggestion |
| Bard Spellcasting | PHB p.29 | **IMPLEMENTED** | `spell_prep_resolver.py`, `play_loop.py` | Spontaneous caster; SPELLS_KNOWN; SPELL_SLOTS managed |

### 10c. Cleric

| Feature | Source | Status | Engine File(s) | Notes / Gap Description |
|---------|--------|--------|----------------|--------------------------|
| Cleric Spellcasting (prepared, divine) | PHB p.32 | **IMPLEMENTED** | `spell_prep_resolver.py`, `play_loop.py` | PrepareSpellsIntent; SPELLS_PREPARED; SPELL_SLOTS |
| Turn Undead | PHB p.32 | **IMPLEMENTED** | `turn_undead_resolver.py` | TurnUndeadIntent; 1d20+CHA mod check (PHB p.159; corrected Batch U WO2); HP budget; WO-ENGINE-TURN-UNDEAD-001 |
| Rebuke Undead (evil clerics) | PHB p.32 | **PARTIAL** | `turn_undead_resolver.py` | channels_negative_energy flag; command undead DEFERRED |
| Domain powers | PHB p.32 | **NOT STARTED** | — | No domain system; no domain power resolver |
| Spontaneous casting (cure spells) | PHB p.32 | **IMPLEMENTED** | `play_loop.py` | Cure redirect wired; declared slot consumed. DEBRIEF_WO-ENGINE-CLERIC-SPONTANEOUS-001. FINDING-ENGINE-SPONTANEOUS-ALIGNMENT-001 CLOSED (Batch AD: evil cleric inflict swap added; alignment check now enforced). |
| Spontaneous casting (inflict spells, evil) | PHB p.32 | **IMPLEMENTED** | `play_loop.py`, `spell_definitions.py`, `spell_resolver.py` | Evil cleric (chaotic/lawful/neutral evil) inflict swap: 5 inflict spells added to SPELL_REGISTRY (L1-L5, necromancy, NEGATIVE damage, Will save half). elif block after cure swap; alignment-gated. SpellCastIntent +spontaneous_inflict flag. Batch AD. ECI-001–008. |
| Aura (good/evil/lawful/chaotic) | PHB p.32 | **NOT STARTED** | — | No alignment aura tracking |
| Command undead (persistent, evil) | PHB p.159 | **DEFERRED** | `turn_undead_resolver.py` | Explicitly noted as DEFERRED in module |
| Domain spells (bonus slot per level) | PHB p.32 | **NOT STARTED** | — | No domain spell slot |

### 10d. Druid

| Feature | Source | Status | Engine File(s) | Notes / Gap Description |
|---------|--------|--------|----------------|--------------------------|
| Druid Spellcasting (prepared, divine) | PHB p.35 | **IMPLEMENTED** | `spell_prep_resolver.py` | Full prepared caster |
| Wild Shape (Small/Medium/Large animal) | PHB p.37 | **IMPLEMENTED** | `wild_shape_resolver.py` | WildShapeIntent; stat swap; natural attacks; EF.WILD_SHAPE_* fields; WO-ENGINE-WILD-SHAPE-001 |
| Wild Shape uses per day (level-based) | PHB p.37 | **IMPLEMENTED** | `wild_shape_resolver.py`, `chargen/builder.py` | WILD_SHAPE_USES_REMAINING field; PHB Table 3-14 lookup (irregular progression: 5→1, 6→2, 7→3, 10→4, 14→5, 18→6). Chargen delegates to resolver lookup. WO-ENGINE-WS-FORMULA-FIX-001. |
| Wild Shape duration (hours = druid level) | PHB p.37 | **IMPLEMENTED** | `schemas/entity_fields.py`, `wild_shape_resolver.py` | WILD_SHAPE_HOURS_REMAINING; WO-ENGINE-WILDSHAPE-DURATION-001 |
| Wild Shape — equipment melds | PHB p.37 | **IMPLEMENTED** | `schemas/entity_fields.py` | EQUIPMENT_MELDED flag; weapon attacks blocked |
| Wild Shape — HP management | PHB p.37 | **IMPLEMENTED** | `wild_shape_resolver.py` | WO-ENGINE-WILDSHAPE-HP-001; HP scaled correctly on transform/revert |
| Wild Shape — revert on 0 HP | PHB p.37 | **IMPLEMENTED** | `wild_shape_resolver.py` | Resolves HP gate for reversion |
| Wild Shape — Tiny/Huge forms (higher levels) | PHB p.37 | **NOT STARTED** | — | Only Small/Medium forms in WILD_SHAPE_FORMS dict |
| Wild Shape — Plant forms (12th level) | PHB p.38 | **NOT STARTED** | — | No plant form support |
| Wild Shape — Elemental (16th level) | PHB p.38 | **NOT STARTED** | — | No elemental form support |
| Animal Companion | PHB p.36 | **IMPLEMENTED** | `companion_resolver.py` | SummonCompanionIntent; build_animal_companion(); WO-ENGINE-COMPANION-WIRE |
| Nature Sense | PHB p.36 | **IMPLEMENTED** | `builder.py`, `skill_resolver.py` | Druid L1+: writes +2 to EF.RACIAL_SKILL_BONUS["knowledge_nature"] and ["survival"] at chargen. skill_resolver.py now consumes RACIAL_SKILL_BONUS dict (was write-only gap). Batch AD. NS-001–004. |
| Wild Empathy | PHB p.36 | **NOT STARTED** | — | No animal attitude system |
| Woodland Stride | PHB p.36 | **NOT STARTED** | — | No difficult terrain interaction |
| Trackless Step | PHB p.36 | **NOT STARTED** | — | No tracking system to be immune to |
| Resist Nature's Lure | PHB p.36 | **IMPLEMENTED** | `builder.py`, `save_resolver.py` | Druid L4+: builder sets EF.RESIST_NATURES_LURE=True. save_resolver reads when save_descriptor="fey": +4 bonus. Requires WO1 SaveContext threading to fire via resolve_save() path. Batch AD. RNL-001–004. |
| Venom Immunity | PHB p.38 | **IMPLEMENTED** | `poison_disease_resolver.py` | Druid L9+ immune to all poisons. `is_immune_to_poison()` checks CLASS_LEVELS. WO-ENGINE-CLASS-IMMUNITY-001. Batch AB. |
| Spontaneous summon (summon nature's ally) | PHB p.35 | **IMPLEMENTED** | `play_loop.py`, `spell_resolver.py` | Druid loses any prepared spell slot to cast SNA of same level. elif block after spontaneous_inflict; druid class gate; _SNA_SPELLS_BY_LEVEL dict levels 1–9. SpellCastIntent.spontaneous_summon flag. Lower-level selection CONSUME_DEFERRED (FINDING-ENGINE-DRUID-SUMMON-LOWER-LEVEL-001). WO-ENGINE-DRUID-SPONTANEOUS-SUMMON-001. Batch AK. DSS-001–008. |
| Thousand Faces | PHB p.38 | **NOT STARTED** | — | No alter self at will |
| Timeless Body | PHB p.38 | **NOT STARTED** | — | No aging mechanic |

### 10e. Fighter

| Feature | Source | Status | Engine File(s) | Notes / Gap Description |
|---------|--------|--------|----------------|--------------------------|
| Bonus Feats (every even level) | PHB p.38 | **PARTIAL** | `schemas/entity_fields.py` | FEAT_SLOTS field tracked; fighter-specific feat slot bonus not auto-granted on level |

### 10f. Monk

| Feature | Source | Status | Engine File(s) | Notes / Gap Description |
|---------|--------|--------|----------------|--------------------------|
| Unarmed Strike (scaling damage by level) | PHB p.41 | **IMPLEMENTED** | `chargen/builder.py`, `schemas/entity_fields.py`, `aidm/core/attack_resolver.py` | EF.MONK_UNARMED_DICE set at chargen per PHB Table 3-10; attack_resolver.py now reads MONK_UNARMED_DICE for unarmed strikes (WO2 Batch AF). level_up() returns monk_unarmed_dice delta. Flurry path already reading MONK_UNARMED_DICE (confirmed parity). 8 gates MUW-001–008. Closes FINDING-ENGINE-MONK-UNARMED-ATTACK-WIRE-001. |
| Flurry of Blows | PHB p.41 | **IMPLEMENTED** | `aidm/core/flurry_of_blows_resolver.py`, `aidm/core/play_loop.py` | FlurryOfBlowsIntent; penalty table (L1-4:-2, L5-8:-1, L9+:0); unarmed/monk-weapon gate; armor/enc block; iterative attack sequence. FOB-001–008. Batch AC. |
| AC Bonus (WIS mod to AC in no armor) | PHB p.41 | **IMPLEMENTED** | `schemas/entity_fields.py`, `chargen/builder.py` | WIS mod to AC when unarmored; enforced at chargen. WO-ENGINE-MONK-WIS-AC-001. |
| Fast Movement (monk speed bonus) | PHB p.41 | **IMPLEMENTED** | `movement_resolver.py` | Monk L3+ speed bonus per PHB Table 3-13 (+10 to +60). Blocked by ANY armor or medium+ load. WO-ENGINE-MONK-FAST-MOVEMENT-001. Batch AB. |
| Still Mind (+2 vs enchantments) | PHB p.41 | **IMPLEMENTED** | `save_resolver.py` | Monk L3+ gets +2 all saves vs enchantment. Stacks with racial enchantment bonus. WO-ENGINE-STILL-MIND-INDOMITABLE-WILL-001. Batch AB. |
| Ki Strike (magic, lawful, adamantine) | PHB p.42 | **IMPLEMENTED** | `damage_reduction.py` | Monk L4 magic, L10 lawful, L16 adamantine. `extract_weapon_bypass_flags()` checks CLASS_LEVELS + MONK_UNARMED_DICE. WO-ENGINE-KI-STRIKE-001. Batch AB. |
| Slow Fall | PHB p.42 | **NOT STARTED** | — | No fall distance reduction |
| Purity of Body (disease immunity) | PHB p.42 | **IMPLEMENTED** | `poison_disease_resolver.py` | Monk L5+ immune to all diseases. `apply_disease_exposure()` emits disease_immunity event. WO-ENGINE-CLASS-IMMUNITY-001. Batch AB. |
| Wholeness of Body (self-heal 2/level) | PHB p.42 | **IMPLEMENTED** | `aidm/core/wholeness_of_body_resolver.py`, `aidm/chargen/builder.py`, `aidm/core/play_loop.py` | WholenessOfBodyIntent; pool=2×monk_level (L7+), clamped heal, five event types. EF.WHOLENESS_OF_BODY_POOL + WHOLENESS_OF_BODY_USED. WOB-001–008. Batch AC. |
| Improved Evasion | PHB p.42 | **IMPLEMENTED** | `spell_resolver.py`, `schemas/entity_fields.py` | EF.IMPROVED_EVASION; failed Ref → half damage. WO-ENGINE-EVASION-ARMOR-001. |
| Diamond Body (poison immunity) | PHB p.42 | **IMPLEMENTED** | `poison_disease_resolver.py` | Monk L11+ immune to all poisons. `is_immune_to_poison()` checks CLASS_LEVELS. WO-ENGINE-CLASS-IMMUNITY-001. Batch AB. |
| Abundant Step (dimension door) | PHB p.42 | **NOT STARTED** | — | No ability |
| Diamond Soul (SR = level + 10) | PHB p.43 | **IMPLEMENTED** | `aidm/chargen/builder.py`, `aidm/core/save_resolver.py` | EF.SR = monk_level+10 at L13+; max() preserves racial SR; level_up() delta["spell_resistance"]; check_spell_resistance path. DS-001–008. Batch AC. |
| Quivering Palm | PHB p.43 | **NOT STARTED** | — | No death touch ability |
| Empty Body (etherealness) | PHB p.43 | **NOT STARTED** | — | No ethereal plane interaction |
| Perfect Self (outsider type) | PHB p.43 | **NOT STARTED** | — | No type change mechanic |
| Timeless Body | PHB p.43 | **NOT STARTED** | — | No aging mechanic |

### 10g. Paladin

| Feature | Source | Status | Engine File(s) | Notes / Gap Description |
|---------|--------|--------|----------------|--------------------------|
| Smite Evil (+CHA attack, +level damage) | PHB p.44 | **IMPLEMENTED** | `smite_evil_resolver.py` | SmiteEvilIntent; CHA to attack, level to damage; SMITE_USES_REMAINING |
| Divine Grace (CHA mod to all saves) | PHB p.44 | **IMPLEMENTED** | `save_resolver.py`, `schemas/entity_fields.py` | CHA mod added to all saves for paladin. WO-ENGINE-DIVINE-GRACE-001. |
| Lay on Hands (CHA × level HP) | PHB p.44 | **IMPLEMENTED** | `aidm/core/lay_on_hands_resolver.py`, `chargen/builder.py`, `core/rest_resolver.py`, `core/play_loop.py` | Pool = paladin_level × CHA_mod (0 if CHA_mod ≤ 0); divisible across recipients; standard action. Write: builder.py:959 (EF.LAY_ON_HANDS_POOL). Read: lay_on_hands_resolver.py (clamps to remaining). Reset: rest_resolver.py:130–131. Dispatch: play_loop.py:2965. 8 play_loop gate tests LOH-WO1-001–008 (WO1 Batch AF). SAI close — file committed from untracked. Closes PARTIAL. |
| Detect Evil (at will) | PHB p.44 | **NOT STARTED** | — | No alignment detection |
| Aura of Courage (+4 morale vs fear) | PHB p.44 | **IMPLEMENTED** | `aidm/core/save_resolver.py`, `aidm/chargen/builder.py`, `aidm/schemas/entity_fields.py`, `aidm/schemas/saves.py` | EF.FEAR_IMMUNE=True (paladin L3+, sentinel=999); ally +4 morale Chebyshev≤2; morale non-stacking max(IC,AoC). WO1 (Batch AD) closed SaveContext gap. WO-AE-WO3: threshold fixed L2→L3 (PHB p.49). ALT-AE-001–004. SCS-001–008. |
| Divine Health (disease immunity) | PHB p.44 | **IMPLEMENTED** | `schemas/entity_fields.py`, `chargen/builder.py` | EF.IMMUNE_DISEASE set at paladin L3+ chargen. WO-ENGINE-DIVINE-HEALTH-001. |
| Turn Undead (as cleric level -2) | PHB p.44 | **IMPLEMENTED** | `turn_undead_resolver.py` | Effective cleric level = paladin_level // 2; 1d20+CHA check; full turn resolution wired. |
| Aura of Good | PHB p.44 | **NOT STARTED** | — | No alignment aura |
| Remove Disease (1/week per 3 levels) | PHB p.44 | **IMPLEMENTED** | `aidm/core/remove_disease_resolver.py`, `chargen/builder.py`, `core/rest_resolver.py`, `core/play_loop.py`, `schemas/entity_fields.py` | Uses = paladin_level // 3 (1 at L3, 2 at L6, 3 at L9). HOUSE_POLICY: "per week" = "per full rest" (consistent with LOH, smite, spell slots). Write: builder.py. Read: remove_disease_resolver.py. Reset: rest_resolver.py. Clears EF.ACTIVE_DISEASES list. 8 gate tests RD-001–008 (WO3 Batch AF). NOT STARTED → IMPLEMENTED. |
| Special Mount | PHB p.44 | **NOT STARTED** | — | No special mount summoning |
| Paladin Spellcasting | PHB p.44 | **IMPLEMENTED** | `spell_prep_resolver.py` | Prepared divine caster from level 4; SPELL_SLOTS managed |

### 10h. Ranger

| Feature | Source | Status | Engine File(s) | Notes / Gap Description |
|---------|--------|--------|----------------|--------------------------|
| Track feat | PHB p.47 | **NOT STARTED** | — | Track feat registered but no tracking system |
| Wild Empathy | PHB p.47 | **NOT STARTED** | — | No animal attitude system |
| Combat Style — Archery (PBS / Rapid Shot) | PHB p.47 | **PARTIAL** | `schemas/feats.py` | Feats registered; no automatic free feat at level 2 |
| Combat Style — TWF (TWF feat) | PHB p.47 | **PARTIAL** | `schemas/feats.py` | TWF registered; no automatic free feat at level 2 |
| Endurance | PHB p.47 | **PARTIAL** | `schemas/feats.py` | Registered; +4 environmental not wired |
| Animal Companion | PHB p.47 | **PARTIAL** | `companion_resolver.py` | Companion resolver exists; ranger gets companion at level 4 not auto-enforced |
| Favored Enemy (+2 attack/damage) | PHB p.47 | **IMPLEMENTED** | `attack_resolver.py`, `schemas/entity_fields.py` | EF.FAVORED_ENEMIES list; +2 attack/damage vs favored type. FE bonus now in pre-crit base (multiplied on crit per PHB p.140). WO-ENGINE-ATTACK-MODIFIER-FIDELITY-001. |
| Ranger Spellcasting (level 4+) | PHB p.47 | **IMPLEMENTED** | `spell_prep_resolver.py` | Prepared caster from level 4 |
| Swift Tracker | PHB p.48 | **NOT STARTED** | — | No tracking system |
| Woodland Stride | PHB p.48 | **NOT STARTED** | — | No difficult terrain interaction |
| Evasion | PHB p.48 | **PARTIAL** | `spell_resolver.py` | Evasion wired generically; ranger gets Evasion at L9 per PHB p.48. Verify chargen wires EF.HAS_EVASION at correct level — FINDING-ENGINE-UD-RANGER-FALSE-001 (Batch X) may overlap. |
| Camouflage | PHB p.48 | **NOT STARTED** | — | No Hide check in natural terrain bonus |
| Hide in Plain Sight | PHB p.48 | **NOT STARTED** | — | No HIPS mechanic |

### 10i. Rogue

| Feature | Source | Status | Engine File(s) | Notes / Gap Description |
|---------|--------|--------|----------------|--------------------------|
| Sneak Attack (Xd6 extra damage) | PHB p.50 | **IMPLEMENTED** | `sneak_attack.py`, `attack_resolver.py` | WO-050B; flanked or denied DEX; NOT crit-multiplied; ranged limit 30 ft |
| Sneak Attack — level scaling (1d6 per 2 levels) | PHB p.50 | **IMPLEMENTED** | `sneak_attack.py` | (level+1)//2 dice |
| Trapfinding | PHB p.50 | **NOT STARTED** | — | No trap detection/disabling system |
| Evasion | PHB p.50 | **IMPLEMENTED** | `spell_resolver.py`, `schemas/entity_fields.py` | EF.HAS_EVASION; Ref success → 0 damage; armor guard. WO-ENGINE-EVASION-ARMOR-001. |
| Trap Sense (+1 Ref vs traps per 3 levels) | PHB p.51 | **IMPLEMENTED** | `schemas/entity_fields.py`, `chargen/builder.py`, `core/save_resolver.py` | EF.TRAP_SENSE_BONUS = (barb_level // 3) + (rogue_level // 3). Multiclass sums contributions. Resolver consume on REF + 'trap' descriptor. TSB-AE-001–008. CONSUME_DEFERRED: AC vs traps (FINDING-ENGINE-TRAP-SENSE-AC-001). WO-AE-WO4. |
| Uncanny Dodge | PHB p.51 | **IMPLEMENTED** | `attack_resolver.py` | Rogue L4 threshold (was L2). Ranger removed (PHB p.48). _UD_THRESHOLDS dict. WO-ENGINE-UNCANNY-DODGE-CLASS-FIX-001. |
| Improved Uncanny Dodge | PHB p.51 | **IMPLEMENTED** | `schemas/entity_fields.py`, `sneak_attack.py` | EF.HAS_IMPROVED_UNCANNY_DODGE; flanker rogue must be 4+ levels higher. gate(Q-WO2). |
| Rogue Special Abilities (each) | PHB p.51 | **PARTIAL** | `aidm/core/attack_resolver.py`, `core/save_resolver.py`, `chargen/builder.py`, `core/rest_resolver.py`, `schemas/entity_fields.py` | **Defensive Roll IMPLEMENTED** (WO4 Batch AF): triggers in attack_resolver.py on physical blow that would reduce HP ≤ 0; Reflex save DC = damage dealt; success = half damage; 1/day; blocked when flat-footed or DEFENSIVE_ROLL_USED=True; resets on rest. **Crippling Strike IMPLEMENTED** (WO-ENGINE-AG-WO2): sneak attack → target takes 1 STR ability damage; STR_DAMAGE accumulates; heals 1/overnight rest; EF.STR_MOD recalculated. 8 gate tests CS-001–008. **Slippery Mind IMPLEMENTED** (WO-ENGINE-AG-WO3): failed enchantment Will save → SLIPPERY_MIND_RETRY_PENDING queued; one retry at same DC; resolve_slippery_mind_retry(); SaveContext.school="enchantment" trigger. 8 gate tests SM-001–008. Remaining NOT STARTED: Feat, Improved Evasion, Opportunist, Skill Mastery. |

### 10j. Sorcerer

| Feature | Source | Status | Engine File(s) | Notes / Gap Description |
|---------|--------|--------|----------------|--------------------------|
| Sorcerer Spellcasting (spontaneous, arcane) | PHB p.54 | **IMPLEMENTED** | `play_loop.py`, `schemas/entity_fields.py` | SPELLS_KNOWN; SPELL_SLOTS; no preparation required |
| Familiar | PHB p.52 | **NOT STARTED** | — | No familiar system |

### 10k. Wizard

| Feature | Source | Status | Engine File(s) | Notes / Gap Description |
|---------|--------|--------|----------------|--------------------------|
| Wizard Spellcasting (prepared, arcane) | PHB p.57 | **IMPLEMENTED** | `spell_prep_resolver.py` | SPELLS_PREPARED; SPELL_SLOTS; PrepareSpellsIntent |
| Wizard Spellbook | PHB p.178 | **NOT STARTED** | — | No spellbook object; prepare-any-known fallback |
| Scribe Scroll | PHB p.59 | **PARTIAL** | `schemas/feats.py` | Feat registered; no scroll creation system |
| Bonus Feats (every 5 levels) | PHB p.59 | **NOT STARTED** | — | Wizard bonus feat slots not auto-granted |
| Arcane School Specialization | PHB p.57 | **NOT STARTED** | — | No specialization system; no opposed school tracking |
| Familiar | PHB p.57 | **NOT STARTED** | — | No familiar system |

---

## SECTION 11 — RACES

All 7 PHB races are defined in `aidm/data/races.py` with stat mods, speed, favored class, bonus feats/skills. Racial traits are encoded in `aidm/schemas/entity_fields.py` with specific boolean/int fields.

| Race | Source | Stat Mods | Special Abilities | Vision | Status |
|------|--------|-----------|-------------------|--------|--------|
| Human | PHB p.12 | None | +1 feat, +4 skill pts | Normal | **IMPLEMENTED** — Bonus feat and skill pts at chargen |
| Dwarf | PHB p.14 | STR/CON, -CHA | Stonecunning, darkvision, +2 vs poison/spells/SLAs, +4 vs giants, +1 vs orcs/goblinoids, speed penalty w/ armor immunity | Darkvision 60 ft | **IMPLEMENTED** — All fields in EF; STONECUNNING, DARKVISION_RANGE, SAVE_BONUS_POISON, etc. |
| Elf | PHB p.15 | DEX, -CON | Immunity to sleep, +2 vs enchantment, low-light vision, automatic search secret doors, +2 Spot/Listen/Search | Low-light | **IMPLEMENTED** — IMMUNE_SLEEP, SAVE_BONUS_ENCHANTMENT, LOW_LIGHT_VISION, AUTOMATIC_SEARCH_DOORS fields |
| Gnome | PHB p.16 | CON, -STR | Darkvision, +2 vs illusion SR, +1 DC illusions, +1 vs kobolds/goblinoids, +4 vs giants, +2 Craft(alchemy)/Listen | Low-light + darkvision | **IMPLEMENTED** — SPELL_RESISTANCE_ILLUSION, ILLUSION_DC_BONUS, ATTACK_BONUS_VS_KOBOLDS fields. ILLUSION_DC_BONUS now consumed at runtime in `_resolve_spell_cast()`: gnome +1 caster-side illusion DC wired (WO-ENGINE-ILLUSION-DC-WIRE-001, Batch AK, ILD-001–008). |
| Half-Elf | PHB p.18 | None | Low-light vision, immunity to sleep, +2 vs enchantment, +2 Diplomacy/Gather Info | Low-light | **IMPLEMENTED** — Fields tracked |
| Half-Orc | PHB p.18 | STR, -INT/-CHA | Darkvision, orc blood | Darkvision 60 ft | **IMPLEMENTED** — Fields tracked |
| Halfling | PHB p.20 | DEX, -STR | +2 saves all, +1 attack w/ thrown, +2 Climb/Jump/Listen/Move Silently, +2 vs fear | Normal | **IMPLEMENTED** — RACIAL_SAVE_BONUS, ATTACK_BONUS_THROWN fields |
| Racial trait active enforcement in combat | — | — | — | — | **IMPLEMENTED** — Batch W: enchantment save bonus (save_resolver + play_loop), sleep immunity (play_loop), racial skill bonuses (session_orchestrator), racial attack bonuses dwarf/gnome/halfling (attack_resolver), racial dodge AC vs giants (attack_resolver). EF.CREATURE_SUBTYPES added. |
| Favored class / multiclass XP penalty | PHB p.56 | — | — | — | **PARTIAL** — DEFERRED; multiclass XP penalty not enforced (experience_resolver exists but XP penalty logic missing) |

---

## SECTION 12 — EQUIPMENT & ITEMS

| Mechanic | Source | Status | Engine File(s) | Notes / Gap Description |
|----------|--------|--------|----------------|--------------------------|
| Weapon damage dice | PHB p.116 | **IMPLEMENTED** | `schemas/attack.py` | Weapon dataclass with damage_dice; parsed in attack_resolver |
| Weapon critical range | PHB p.116 | **IMPLEMENTED** | `schemas/attack.py` | threat_range field on Weapon; confirmation roll |
| Weapon critical multiplier | PHB p.116 | **IMPLEMENTED** | `schemas/attack.py` | crit_multiplier field on Weapon |
| Weapon type (slashing/piercing/bludgeoning) | PHB p.116 | **PARTIAL** | `schemas/attack.py` | damage_type field exists; DR bypass by material checked |
| Weapon material (adamantine, cold iron, silver) | PHB p.284 | **PARTIAL** | `damage_reduction.py` | Bypass types checked in DR resolver; no equipment catalog material field on entity weapon |
| Magic weapon enhancement bonus | PHB p.284 | **IMPLEMENTED** | `damage_reduction.py`, `attack_resolver.py` | `is_magic` and `enhancement_bonus` fields; DR bypass + +X to attack/damage from enhancement. WO-ENGINE-WEAPON-ENHANCEMENT-001. |
| Ammunition (arrow, bolt, bullet) | PHB p.116 | **NOT STARTED** | — | No ammunition tracking or expenditure |
| Armor bonus to AC | PHB p.123 | **PARTIAL** | `schemas/entity_fields.py` | Included in base AC field; no separate armor type breakdown |
| Armor max DEX bonus | PHB p.123 | **NOT STARTED** | — | No max DEX cap enforced from armor type |
| Armor check penalty (ACP) | PHB p.123 | **IMPLEMENTED** | `schemas/entity_fields.py`, `skill_resolver.py` | ARMOR_CHECK_PENALTY field; applied in skill checks |
| Arcane spell failure | PHB p.123 | **IMPLEMENTED** | `play_loop.py` | ASF% enforced; slot consumed on failure; V-only spells and divine casters bypass. WO-ENGINE-ARCANE-SPELL-FAILURE-001. |
| Shield types | PHB p.120 | **NOT STARTED** | — | No shield type differentiation; shield AC included in entity AC |
| Special materials — adamantine | PHB p.284 | **PARTIAL** | `damage_reduction.py` | Bypass type "adamantine" for DR; no hardness 20 auto-applied to worn armor |
| Special materials — mithral | PHB p.284 | **NOT STARTED** | — | No mithral material effects (lighter, ASF reduction) |
| Special materials — cold iron | PHB p.284 | **PARTIAL** | `damage_reduction.py` | Bypass type "cold_iron" for DR |
| Special materials — silver | PHB p.284 | **PARTIAL** | `damage_reduction.py` | Bypass type "silver" for DR |
| Encumbrance (light/medium/heavy/overloaded) | PHB p.162 | **IMPLEMENTED** | `encumbrance.py` | ENCUMBRANCE_LOAD; carrying capacity table; load tier from STR score |
| Carrying capacity (STR-based table) | PHB p.162 | **IMPLEMENTED** | `encumbrance.py` | Full capacity table; light/medium/heavy thresholds |
| Encumbrance penalties (speed, max DEX, ACP) | PHB p.162 | **PARTIAL** | `encumbrance.py` | Tier computed; penalties not yet auto-applied to movement/skill resolvers |
| Inventory tracking | PHB p.162 | **IMPLEMENTED** | `schemas/entity_fields.py` | INVENTORY list of item dicts with item_id, quantity, stow_location |
| Equipment catalog | PHB p.112 | **PARTIAL** | `data/equipment_catalog.json` | Equipment catalog loaded; not fully integrated into entity equipment model |

---

## SECTION 13 — MAGIC ITEMS (DMG)

| Category | Source | Status | Engine File(s) | Notes / Gap Description |
|----------|--------|--------|----------------|--------------------------|
| Armor enhancement bonus (+1 to +5) | DMG p.218 | **NOT STARTED** | — | No magic item equipping system; enhancement not applied to entity AC |
| Armor special abilities | DMG p.219 | **NOT STARTED** | — | No magic armor special properties |
| Weapon enhancement bonus (+1 to +5) | DMG p.224 | **PARTIAL** | `damage_reduction.py` | is_magic / enhancement_bonus used for DR bypass; not applied as attack/damage bonus |
| Weapon special abilities (flaming, keen, etc.) | DMG p.225 | **NOT STARTED** | — | No weapon special property system |
| Potions | DMG p.229 | **NOT STARTED** | — | No potion item or consumption system |
| Rings | DMG p.230 | **NOT STARTED** | — | No ring equip/effect system |
| Rods | DMG p.235 | **NOT STARTED** | — | No rod equip/effect system |
| Staves | DMG p.238 | **NOT STARTED** | — | No staff charge/cast system |
| Wands | DMG p.241 | **NOT STARTED** | — | No wand charge/use system |
| Wondrous Items | DMG p.243 | **NOT STARTED** | — | No wondrous item system |
| Artifacts | DMG p.273 | **NOT STARTED** | — | Not applicable to most campaigns |
| Cursed Items | DMG p.272 | **NOT STARTED** | — | No curse system |
| Intelligent Items | DMG p.268 | **NOT STARTED** | — | Not applicable to most campaigns |
| Item creation feats (Craft Wand, Forge Ring, etc.) | PHB p.92 | **PARTIAL** | `schemas/feats.py` | Feats registered; no creation mechanics |
| Identifying magic items (Spellcraft DC 15+spell level) | PHB p.180 | **NOT STARTED** | — | No identification mechanic |
| Magic item slot system (body slots) | DMG p.176 | **NOT STARTED** | — | No body slot tracking (head, eyes, throat, etc.) |
| Charged item usage (wand/rod/staff) | DMG p.175 | **NOT STARTED** | — | No charge tracking on item entities |

---

## SECTION 14 — ENVIRONMENTAL & HAZARDS (DMG)

| Mechanic | Source | Status | Engine File(s) | Notes / Gap Description |
|----------|--------|--------|----------------|--------------------------|
| Falling damage (1d6/10 ft, max 20d6) | DMG p.303 | **PARTIAL** | `environmental_damage_resolver.py`, `maneuver_resolver.py` | Spiked pit falling damage in maneuver context; general falling from movement not fully wired |
| Fire damage (contact, 1d6/round) | DMG p.303 | **IMPLEMENTED** | `environmental_damage_resolver.py` | Fire hazard squares; 1d6 fire on entry |
| Catching fire (sustained fire, DC 15 Ref) | DMG p.303 | **NOT STARTED** | — | No "on fire" condition; no 1d6/round sustained fire mechanic |
| Lava (2d6/round contact) | DMG p.303 | **IMPLEMENTED** | `environmental_damage_resolver.py` | Lava hazard; 2d6 fire on entry |
| Acid (1d6/round) | DMG p.303 | **IMPLEMENTED** | `environmental_damage_resolver.py` | Acid pool hazard; 1d6 acid on entry |
| Drowning sequence | DMG p.304 | **NOT STARTED** | — | No drowning mechanic; Swim skill not linked to HP |
| Cold/heat environmental damage | DMG p.302 | **NOT STARTED** | — | No temperature check system |
| Altitude sickness | DMG p.305 | **NOT STARTED** | — | Not implemented |
| Starvation / thirst | DMG p.304 | **NOT STARTED** | — | No survival resource tracking |
| Disease (incubation, saves, 2-save cure) | DMG p.292 | **IMPLEMENTED** | `poison_disease_resolver.py` | ACTIVE_DISEASES field; incubation period; consecutive saves; WO-ENGINE-POISON-DISEASE-001 |
| Poison (initial/secondary saves) | DMG p.292 | **IMPLEMENTED** | `poison_disease_resolver.py` | ACTIVE_POISONS field; initial + secondary save (1 minute later); WO-ENGINE-POISON-DISEASE-001 |
| Cave-ins / avalanches | DMG p.305 | **NOT STARTED** | — | No structural collapse mechanic |
| Object hardness (attacks on objects) | DMG p.309 | **PARTIAL** | `damage_reduction.py` | Hardness as DR applied; WEAPON_HP for weapon sundering; general object HP not tracked |
| Object HP by size | DMG p.309 | **NOT STARTED** | — | No generalized object entity HP |
| Door types (HP, hardness, break DC) | DMG p.307 | **NOT STARTED** | — | No door interaction system |
| Wall types (HP, hardness) | DMG p.307 | **NOT STARTED** | — | No structural wall system |
| Darkness / light levels | DMG p.301 | **PARTIAL** | `concealment.py` | MISS_CHANCE used for darkness concealment; no lighting level system |
| Smoke (concealment, Fort save) | DMG p.303 | **NOT STARTED** | — | No smoke mechanic |
| Wind effects (ranged attack penalties) | DMG p.302 | **NOT STARTED** | — | No wind system |
| Quicksand | DMG p.305 | **NOT STARTED** | — | Not implemented |
| Wilderness encounter frequency | DMG p.186 | **NOT STARTED** | — | No random encounter table system |

---

## SECTION 15 — DMG SYSTEMS

| Mechanic | Source | Status | Engine File(s) | Notes / Gap Description |
|----------|--------|--------|----------------|--------------------------|
| Challenge Rating (CR) assignment | DMG p.36 | **IMPLEMENTED** | `experience_resolver.py` | CR used in XP calculation; DMG table rules referenced |
| Encounter Level (EL) calculation | DMG p.37 | **IMPLEMENTED** | `experience_resolver.py` | EL derived from multiple creature CRs |
| XP award calculation (Table 2-6) | DMG p.38 | **IMPLEMENTED** | `experience_resolver.py` | Full XP table; CR fractions; party size division |
| Story XP awards | DMG p.40 | **NOT STARTED** | — | No narrative award mechanic |
| Encounter difficulty categories | DMG p.48 | **NOT STARTED** | — | No automated difficulty rating system |
| Traps — Search check to find | DMG p.70 | **NOT STARTED** | — | No trap entity system |
| Traps — Disable Device check | DMG p.70 | **NOT STARTED** | — | No Disable Device trigger |
| Traps — attack roll / save | DMG p.70 | **NOT STARTED** | — | Trap stat block not modeled |
| Treasure generation (Table 3-5) | DMG p.52 | **NOT STARTED** | — | No treasure roll system |
| Gem / art object tables | DMG p.55 | **NOT STARTED** | — | No random treasure generation |
| NPC class — Adept | DMG p.107 | **NOT STARTED** | — | NPC classes not modeled as class options |
| NPC class — Aristocrat | DMG p.107 | **NOT STARTED** | — | Not implemented |
| NPC class — Commoner | DMG p.107 | **NOT STARTED** | — | Not implemented |
| NPC class — Expert | DMG p.107 | **NOT STARTED** | — | Not implemented |
| NPC class — Warrior | DMG p.107 | **NOT STARTED** | — | Not implemented |
| Prestige classes (15 DMG core) | DMG p.155 | **NOT STARTED** | — | No prestige class system |
| Leadership feat / cohort / followers | DMG p.157 | **NOT STARTED** | — | No leadership system |
| Planar traits (gravity, time, magic, alignment) | DMG p.166 | **NOT STARTED** | — | No planar rules engine |
| Plane travel mechanics | DMG p.166 | **NOT STARTED** | — | No planar movement |
| Random encounter tables | DMG p.50 | **NOT STARTED** | — | No random encounter framework |
| NPC gear value table | DMG p.127 | **NOT STARTED** | — | No NPC wealth generation |
| Variant rule — ability score generation | DMG p.169 | **NOT STARTED** | — | Engine uses fixed arrays; roll methods not implemented |
| Variant rule — spell roll saves | DMG p.171 | **NOT STARTED** | — | Fixed DC formula; roll variant not supported |
| Variant rule — faster/slower XP | DMG p.171 | **NOT STARTED** | — | XP rate is fixed |
| Economy — cost of living | DMG p.130 | **NOT STARTED** | — | No economy simulation |
| Economy — hirelings | DMG p.130 | **NOT STARTED** | — | No hireling system |
| Epic level basics (BAB/save continuation) | DMG p.206 | **NOT STARTED** | — | Level caps at 20; no epic progression |

---

## SECTION 16 — EXPERIENCE & LEVELING

| Mechanic | Source | Status | Engine File(s) | Notes / Gap Description |
|----------|--------|--------|----------------|--------------------------|
| XP total tracking | PHB p.22 | **IMPLEMENTED** | `schemas/entity_fields.py`, `experience_resolver.py` | EF.XP field; award_xp() function; WO-ENGINE-LEVELUP-WIRE |
| Level threshold checks (when to level up) | PHB p.22 | **IMPLEMENTED** | `experience_resolver.py` | LEVEL_THRESHOLDS schema; check_level_up() |
| Level-up procedure (HP, saves, BAB, feats) | PHB p.22 | **IMPLEMENTED** | `builder.py`, `experience_resolver.py` | apply_level_up(); HP rolled + CON; multiclass saves/BAB use sum() across classes (PHB p.22). WO-ENGINE-MULTICLASS-FORMULA-FIX-001. |
| Multiclass XP penalty (-20% per favored class violation) | PHB p.60 | **NOT STARTED** | — | No multiclass XP penalty applied; DEFERRED |
| Ability score increase (every 4 levels) | PHB p.8 | **PARTIAL** | `experience_resolver.py` | Feat slot granted at odd levels; ability score increase at 4/8/12/16/20 not auto-applied |
| Feat slots (every odd level: 1, 3, 5...) | PHB p.8 | **IMPLEMENTED** | `experience_resolver.py` | FEAT_SLOTS granted at levels 1, 3, 5, 7, 9... |
| Class skill points on level (class base + INT mod) | PHB p.62 | **PARTIAL** | `experience_resolver.py` | Skill points allocated at chargen; per-level skill point gain tracked but not fully auto-allocated |
| Max ranks increase on level-up | PHB p.62 | **PARTIAL** | `experience_resolver.py` | Max rank = level + 3 (class) enforced at chargen; not dynamically re-enforced on each level-up |
| Death and XP (dead still get XP) | DMG p.40 | **NOT STARTED** | — | No post-death XP award to dead characters |

---

## SECTION 17 — INFRASTRUCTURE SYSTEMS

| Mechanic | Source | Status | Engine File(s) | Notes / Gap Description |
|----------|--------|--------|----------------|--------------------------|
| WS Event Routing (player_utterance → engine → client) | INFRA | **IMPLEMENTED** | `aidm/server/ws_bridge.py`, `client/src/main.ts` | WO-INFRA-WS-PLUMB-001. Fixed msg_type mismatch (player_input→player_utterance). Expanded _turn_result_to_messages() from 5 to 10 handlers: added attack_roll, save_rolled, condition_applied, xp_awarded, level_up_applied. Fixed dual event format key lookup ("type" vs "event_type"). 8/8 gates (WP-001–WP-008). |

---

## SUMMARY TABLE

| Domain | Total Mechanics | Implemented | Partial | Not Started | Deferred | Coverage % |
|--------|----------------|-------------|---------|-------------|----------|------------|
| Section 1 — Combat Core | 45 | 28 | 8 | 8 | 1 | 62% |
| Section 2 — Special Attacks | 27 | 16 | 7 | 4 | 0 | 59% |
| Section 3 — Attacks of Opportunity | 17 | 12 | 3 | 2 | 0 | 71% |
| Section 4 — Conditions | 31 | 21 | 3 | 7 | 0 | 68% |
| Section 5 — Saving Throws | 17 | 9 | 3 | 5 | 0 | 53% |
| Section 6 — Skills | 40 | 3 | 35 | 2 | 0 | 8% active / 95% defined |
| Section 7 — Feats | 90 | 14 | 45 | 31 | 0 | 16% fully active |
| Section 8 — Spellcasting System | 37 | 17 | 9 | 11 | 0 | 46% |
| Section 9 — Spells by Category | 60 | 25 | 5 | 30 | 1 | 42% |
| Section 10 — Class Features | 95 | 22 | 14 | 59 | 1 | 23% |
| Section 11 — Races | 15 | 8 | 6 | 0 | 1 | 53% |
| Section 12 — Equipment & Items | 18 | 5 | 7 | 6 | 0 | 28% |
| Section 13 — Magic Items (DMG) | 15 | 0 | 3 | 12 | 0 | 0% |
| Section 14 — Environmental & Hazards | 22 | 5 | 5 | 12 | 0 | 23% |
| Section 15 — DMG Systems | 25 | 3 | 0 | 22 | 0 | 12% |
| Section 16 — Experience & Leveling | 9 | 4 | 4 | 1 | 0 | 44% |
| **TOTALS** | **563** | **192** | **157** | **212** | **4** | **34% implemented / 62% touched** |

---

## SECTION 18 — DATA LAYER (OSS-INGESTION-SPRINT-001)

| Registry | Before | After | Source | Status | Notes |
|----------|--------|-------|--------|--------|-------|
| FEAT_REGISTRY (`aidm/schemas/feats.py`) | 66 | 109 | zellfaze CC0 feats.json (109 entries) | **EXPANDED** | 43 novel feats added: skill bonus, metamagic, item creation, combat. FI-001–FI-008 (29/29). Adjusted threshold: ≥109 (STRAT estimated ≥200 from incorrect source count). |
| SPELL_REGISTRY (`aidm/data/spell_definitions.py`) | 215 | 733 | PCGen rsrd_spells.lst (CC0/OGL, 721 entries) | **EXPANDED** | 518 PCGen stub entries added via spell_definitions_ext.py. SI-001–SI-008 (22/22). Stubs: school/level/components/SR faithful; target_type/effect_type heuristic. Original 215 unchanged. |
| equipment_catalog.json | 22 weapons, 18 armor | unchanged | PCGen rsrd_equip_arms_and_armor.lst (cross-validation) | **VERIFIED** | All 18 PHB armor types confirmed against PCGen. All 5 weapon spot-checks (dagger/longsword/greatsword/battleaxe/greataxe) match PCGen exactly. EI-001–EI-008 (27/27). No updates needed — catalog was already correct. |
| CREATURE_REGISTRY (`aidm/data/creature_registry.py`) | 29 | 225 | Obsidian SRD Markdown (CC0/OGL) — Monsters.md + Animals + Vermin | **EXPANDED** | 196 novel creatures added via creature_registry_ext.py. Custom parser (`scripts/parse_obsidian_monsters.py`). MI-001–MI-008 (24/24). CR/HP/AC/saves/abilities from source text; attack parsing heuristic. |

---

## PRIORITY GAP LIST — TOP 20 CRITICAL MISSING MECHANICS

Ordered by: (1) frequency in normal play, (2) dependency depth (other mechanics break without this), (3) silent failure risk (engine produces wrong output without awareness).

| Rank | Mechanic | Domain | Why Critical | Estimated WO Scope |
|------|----------|--------|-------------|-------------------|
| 1 | **Arcane Spell Failure (armor)** | Spellcasting | Every armored arcane caster silently ignores ASF. No error — just wrong. Any fighter/wizard hybrid or armored caster is broken. | Small — add ASF% field; roll d100 on arcane cast |
| 2 | **Spell save DC feat modifiers (Spell Focus)** | Feats | Spell Focus is registered but unwired. Every caster who has it is missing +1 or +2 DC on all spells in their school. Silent error every spell cast. | Small — add feat check in SpellResolver.compute_dc() |
| 3 | **Great Fortitude / Iron Will / Lightning Reflexes wired to saves** | Feats | Three of the most common fighter/paladin/bard feats. Registered in FEAT_REGISTRY but not queried in save_resolver. Silent -2 effective on saves for all such characters. | Trivial — add feat lookup in get_save_bonus() |
| 4 | **Evasion / Improved Evasion** | Saves/Class | Rogue and monk core defensive ability. Every rogue in an AoE spell takes full damage instead of zero. Affects every encounter with area spells. | Small — add evasion check in save resolver for Reflex/half scenarios |
| 5 | **Favored Enemy (+2 attack/damage)** | Class Features | Every ranger is effectively broken in combat. No bonus applied ever. Frequent ability used every encounter against the favored type. | Medium — add FAVORED_ENEMIES list to entity; check in attack_resolver |
| 6 | **Divine Grace (paladin CHA to saves)** | Class Features | Every paladin's defining defensive feature. Missing means paladin saves are wildly under-stated. Affects every save a paladin makes. | Small — add CHA_MOD to save_resolver for paladins |
| 7 | **Energy Resistance (field on entity)** | Saves/Defense | No resistance field. Creatures with fire resistance 10 (half-dragons, fire giants with ring, etc.) take full fire damage from all spells. Silent wrong output. | Small — add ENERGY_RESISTANCE dict field; apply in spell_resolver damage |
| 8 | **Unarmed Strike / Flurry of Blows (Monk)** | Class Features | Monks have no class features at all. A monk entity is functionally a commoner. The class is the most mechanically unique and is completely absent. | Large — requires unarmed damage table, Flurry intent, AC bonus, WIS-to-AC |
| 9 | **Dispel Magic** | Spells | No dispel mechanic means buffs never end from opponent action. Every spellcaster can layer buffs indefinitely without counterplay. Core tactical spell. | Medium — add dispel check in duration_tracker; caster level opposed roll |
| 10 | **Cleric Domain Powers** | Class Features | Every cleric's 2 domains are missing. Domain powers include some of the most used abilities (Travel domain speed bonus, Luck reroll, War domain weapon mastery). | Large — domain framework + 30+ domain power implementations |
| 11 | **Spell components enforcement (V/S/M)** | Spellcasting | Verbal (deafened blocks) and somatic (grappled/armored) are partially relevant but M components go entirely untracked. Rare but critical for Concentration, Silence zone, and costly material spells. | Medium — add component flags to SpellDefinition; enforce in play_loop |
| 12 | **Touch spell charge held** | Spellcasting | After a touch spell is cast, the charge should persist until discharged. Currently single touch; caster cannot "hold the charge" and touch next round. Common paladin/cleric pattern. | Medium — add held_touch_charge field to entity; drain on next touch attack |
| 13 | **Lay on Hands (paladin)** | Class Features | Paladin's other core feature besides smite. No healing ability at all beyond spells. Frequently used every session for paladin builds. | Small — add LAY_ON_HANDS_POOL field; resolve like HP heal |
| 14 | ~~**Tumble to avoid AoO (DC 15)**~~ | Skills | **ALREADY IMPLEMENTED** — confirmed 2026-02-26. aoo.py lines 493–548. Remove from gap list. | — |
| 15 | **Massive damage rule (50+ HP = DC 15 Fort or die)** | Combat Core | Absent entirely. Any single hit dealing 50+ damage against a character of any HP should trigger instant-death check. Silent wrong outcome. | Trivial — add check in attack_resolver after damage applied |
| 16 | **Weapon enhancement bonus to attack/damage** | Equipment | Magic weapons (+1 longsword etc.) are the most common magic items in play. The enhancement bonus is only used for DR bypass; it does not add to attack or damage rolls. Every magic weapon is mechanically equivalent to mundane. | Small — add enhancement_bonus modifier in attack_resolver |
| 17 | **Concentration checks (grappled / entangled / other causes)** | Spellcasting | Only damage-during-casting is checked. Grappled casters, entangled casters, and casters on unstable surfaces should also make Concentration checks. Common scenario in grapple-focused monsters. | Small — add condition checks in play_loop before spell resolution |
| 18 | **Stabilization by ally (DC 15 Heal check)** | Combat Core | A dying PC can be saved by an ally using Heal skill (DC 15). No mechanic exists. Dying characters must self-stabilize (Fort save) or die. Missing means standard rescue action doesn't work. | Small — add HealIntent or Stabilize action; Heal skill check |
| 19 | **Sneak Attack immunity (constructs, undead, plants, oozes)** | Class Features | Sneak attack is implemented but CRIT_IMMUNE flag handles this. However, the flag is opt-in and not auto-applied based on creature type. Any undead/construct without the explicit flag takes sneak attack damage incorrectly. | Small — add creature_type field; auto-set CRIT_IMMUNE for relevant types |
| 20 | **Cleric spontaneous cure casting** | Class Features | Every good cleric can swap any prepared spell for a cure spell of the same level. Extremely common — clerics often run out of cure slots and rely on this. Currently there is no swap mechanism. | Medium — add spontaneous_swap flag check in play_loop on CastSpellIntent |

---

## APPENDIX — ENGINE FILE REFERENCE

| Engine Module | Primary Mechanic | Status |
|---------------|-----------------|--------|
| `core/attack_resolver.py` | Single attack roll; crits; damage; DR; sneak attack; concealment | Active |
| `core/full_attack_resolver.py` | Iterative attacks; TWF; feat modifiers | Active |
| `core/maneuver_resolver.py` | Bull Rush, Trip, Overrun, Sunder, Disarm, Grapple | Active |
| `core/aoo.py` | Attacks of Opportunity; trigger detection; AoO sequence | Active |
| `core/combat_reflexes.py` | Combat Reflexes feat; extra AoOs | Active |
| `core/spell_resolver.py` | Spell targeting; save resolution; AoE; SR; damage | Active |
| `core/save_resolver.py` | Fort/Ref/Will saves; SR; condition modifiers; nat 1/20 | Active |
| `core/skill_resolver.py` | Skill checks; opposed checks; ACP | Active |
| `core/feat_resolver.py` | Feat prerequisite validation; combat modifier computation | Active |
| `core/metamagic_resolver.py` | Empower; Maximize; Extend; Heighten; Quicken | Active |
| `core/dying_resolver.py` | Death/dying/disabled/stable HP bands; bleed | Active |
| `core/poison_disease_resolver.py` | Poison initial/secondary saves; disease incubation | Active |
| `core/energy_drain_resolver.py` | Negative levels from energy drain attacks | Active |
| `core/damage_reduction.py` | DR X/type; bypass types; hardness | Active |
| `core/sneak_attack.py` | Sneak attack dice; flanking eligibility; crit immunity | Active |
| `core/concealment.py` | Miss chance; blur; invisibility | Active |
| `core/flanking.py` | Geometric flanking check | Active |
| `core/aoe_rasterizer.py` | Burst; cone; line; cylinder AoE shapes | Active |
| `core/cover_resolver.py` | Standard/improved/total cover | Active |
| `core/reach_resolver.py` | Weapon reach; threatened squares | Active |
| `core/action_economy.py` | Action budget; standard/move/swift/free/full/5ft | Active |
| `core/initiative.py` | Initiative rolls; tie-breaking | Active |
| `core/rage_resolver.py` | Barbarian Rage: activate/tick/end/fatigue | Active |
| `core/bardic_music_resolver.py` | Inspire Courage; bardic uses; duration; bard incapacitation | Active |
| `core/wild_shape_resolver.py` | Wild Shape transform/revert; HP gate; duration gate | Active |
| `core/companion_resolver.py` | Animal companion summoning | Active |
| `core/turn_undead_resolver.py` | Turn/rebuke undead; HD budget; paladin turning | Active |
| `core/smite_evil_resolver.py` | Paladin Smite Evil; CHA bonus; level damage | Active |
| `core/ability_damage_resolver.py` | STR/DEX/CON/INT/WIS/CHA temporary damage and permanent drain | Active |
| `core/natural_attack_resolver.py` | Natural attacks (bite/claw/talon); Wild Shape integration | Active |
| `core/feint_resolver.py` | Feint; Bluff vs Sense Motive; deny DEX | Active |
| `core/aid_another_resolver.py` | Aid Another combat; DC 10 attack; +2 ally bonus | Active |
| `core/rest_resolver.py` | Overnight rest; HP recovery; spell slot refill | Active |
| `core/spell_prep_resolver.py` | Spell preparation; slot validation; spontaneous caster rejection | Active |
| `core/duration_tracker.py` | Spell effect duration; concentration; tick-down; expiry | Active |
| `core/mounted_combat.py` | Mounted move/dismount; higher-ground bonus | Active |
| `core/encumbrance.py` | Carrying capacity table; load tier computation | Active |
| `core/experience_resolver.py` | XP award; level threshold; apply_level_up | Active |
| `core/environmental_damage_resolver.py` | Fire/acid/lava/spiked pit hazard damage on entry | Active |
| `core/withdraw_delay_resolver.py` | Withdraw (safe first square); Delay (initiative change) | Active |
| `core/readied_action_resolver.py` | Readied action trigger/response | Active |
| `schemas/conditions.py` | All 24 condition type definitions; ConditionModifiers | Active |
| `schemas/entity_fields.py` | All entity field constants (single source of truth) | Active |
| `schemas/feats.py` | ~60 feat definitions in FEAT_REGISTRY | Active |
| `schemas/skills.py` | 34 skill definitions in SKILLS dict | Active |
| `data/spell_definitions.py` | ~45 spell entries in SPELL_REGISTRY | Active |
| `data/races.py` | 7 PHB race definitions with all fields | Active |

---

---

## Phase 2 — Data Layer

| File / Artifact | What it covers | Status |
|----------------|----------------|--------|
| `data/srd_skills.json` | 49 PHB SRD skill entries: name, ability, trained_only, armor_check_penalty, synergy. Source: dnd-generator CC0. Consumer: WO-JUDGMENT-VALIDATOR-001 (CONSUME_DEFERRED). | IMPLEMENTED — SE-001–SE-008 |
| `data/srd_dc_ranges.json` | DC bounds constants: dc_min=5, dc_max=40 (PHB p.65). Must match ruling_validator.py constants when built. | IMPLEMENTED — SE-005–SE-006 |

---

*Document generated 2026-02-26. Engine baseline: master branch, post-WO-ENGINE-WILDSHAPE-DURATION-001.*
*Updated 2026-03-01: WSP schema fix (WSS), AoO round reset (AOR), SRD data extract (SE).*
*Next recommended review: after any WO that adds new mechanics to cross-check against this map.*
