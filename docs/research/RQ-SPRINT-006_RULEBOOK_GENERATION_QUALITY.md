# RQ-SPRINT-006: Rulebook Generation — Player-Facing Documentation Quality

**Document ID:** RQ-SPRINT-006
**Version:** 1.0
**Date:** 2026-02-14
**Status:** RESEARCH COMPLETE
**Author:** Research Agent (Opus 4.6)
**Authority:** Read-only research sprint. No code modified.

---

## Research Question

Can the world compiler produce a player-facing rulebook — the equivalent of a PHB written in a generated world's own vocabulary — that teaches a player how every ability works without ever referencing D&D 3.5e?

## Answer: YES — with the text generation pipeline completed

The schema supports it. RuleTextSlots accepts arbitrary world-flavored text. The world_name field holds a non-D&D name. The generation pipeline does not yet deliver it — current text generation produces D&D parameter dumps like "Damage: 1d4+1; Type: force; Range: medium". The gap is in generation quality, not schema design.

---

## 1. Current Rulebook Schema Analysis

RuleEntry (aidm/schemas/rulebook.py): content_id, procedure_id, rule_type, world_name, tier, tags, parameters (RuleParameters with 11 typed fields + custom dict), text_slots (RuleTextSlots with 4 fields), provenance (RuleProvenance), prerequisites, supersedes.

RuleTextSlots: rulebook_description (unbounded), short_description (120 chars), flavor_text (unbounded), mechanical_summary (unbounded).

D&D is in the parameter field names and enum values, NOT the data model structure. Schema can serve generated content with vocabulary translation at the presentation layer.

---

## 2. Player-Facing Entry Structure

A complete entry needs: Name (world_name), Short description, Flavor text, Mechanical summary, Usage constraints (MISSING), Interaction notes (MISSING).

Current text generation in compile_stages/rulebook.py produces raw D&D field dumps. The text generation pipeline is a stub.

Progressive revelation needs ability knowledge tiers: UNKNOWN → HEARD_OF → OBSERVED → EXPERIENCED → MASTERED.

---

## 3. Schema Extension Recommendations

Add to RuleTextSlots: usage_constraints, interaction_notes, mechanical_summary_vague.
Add to RuleEntry: discovery_text (per-tier text variants for progressive revelation).

No changes needed to: RuleParameters, RuleProvenance, Prerequisite, content_id, procedure_id, tags, tier, supersedes.

---

## 4. Derivability Matrix — Five Abilities

| # | D&D Donor | World Name | Archetype |
|---|-----------|-----------|-----------|
| 1 | Magic Missile | Void Lance | Auto-hit ranged force projectile |
| 2 | Fireball | Searing Detonation | Area burst fire damage + Reflex save |
| 3 | Hold Person | Iron Command | Single-target Will save condition |
| 4 | Cure Light Wounds | Mending Touch | Touch healing |
| 5 | Bull's Strength | Surge of Might | Self-buff duration ability |

~65% deterministic, ~20% templated, ~15% creative generation. No part of output requires D&D reference.

---

## 5. Discovery Log Integration

Ability Knowledge Tiers:
- UNKNOWN: nothing visible
- HEARD_OF: world_name + short_description
- OBSERVED: + mechanical_summary_vague, flavor_text
- EXPERIENCED: + mechanical_summary with observed values, usage_constraints
- MASTERED: + full rulebook_description, interaction_notes, exact parameters

AbilityKnowledgeEvent with sources: NPC_MENTION, LORE_CHECK_SUCCESS, VISUAL_WITNESS, COMBAT_TARGET, SELF_USE, REPEATED_USE, DELIBERATE_STUDY, CRYSTAL_BALL_QUERY.

World Compiler generates per-tier text variants at compile time. Runtime alternative: mask fields from base text_slots using field-visibility table.

---

## 6. Template Families by Mechanical Archetype

5 template families:
1. Projectile Damage: "[Verb] [count] [type] [noun] [target]. [Hit behavior]. [Damage]. [Scaling]. [Resistance]."
2. Area Effect Damage: "[Verb] [effect] in [radius]-foot [shape]. [Damage] to all. [Save] [outcome]."
3. Save-or-Condition: "[Verb] [target] with [effect]. [Save]: on failure, [condition]. [Duration]. [Recurring save]."
4. Touch Healing: "[Verb] [target] to [effect]. [Healing]. [Range]. [Scaling]."
5. Self-Enhancement Buff: "[Verb] your [attribute] for [duration]. [Effect]. [Stacking]. [Manifestation]."

---

## 7. Quality Standard

A generated rulebook entry passes when:
1. Player can read it and understand what the ability does
2. No D&D terminology appears
3. Mechanically precise enough for tactical decisions
4. Flavor text belongs to the world
5. Progressive revelation rewards exploration

---

## Remaining Work

| Item | Current | Required | Effort |
|------|---------|----------|--------|
| Text generation quality | Parameter dumps | World-flavored prose | HIGH |
| Usage constraints field | Missing | Added to RuleTextSlots | LOW |
| Interaction notes field | Missing | Added to RuleTextSlots | LOW |
| Discovery tier text variants | Not implemented | Compile-time generation | MEDIUM |
| Ability knowledge tracking | Not implemented | Extend discovery_log | MEDIUM |
| Template library | Not exists | Template families per archetype | MEDIUM |
| Vague mechanical summary | Not implemented | Added to RuleTextSlots | LOW |

---

## Files Referenced

- aidm/schemas/rulebook.py — RuleEntry, RuleTextSlots, RuleParameters
- aidm/lens/rulebook_registry.py — RulebookRegistry query system
- aidm/core/compile_stages/rulebook.py — RulebookStage compile pipeline
- aidm/lens/discovery_log.py — Progressive revelation state machine
- aidm/schemas/knowledge_mask.py — Knowledge tier definitions
- aidm/schemas/presentation_semantics.py — Layer B (AD-007)
- docs/contracts/DISCOVERY_LOG.md — Progressive revelation contract

---

*End of RQ-SPRINT-006*
