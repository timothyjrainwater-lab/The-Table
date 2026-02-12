#!/usr/bin/env python3
"""Bridge verification: extracted templates vs gold-standard SPELL_REGISTRY.

Compares the content pack extraction output against the 53 hand-authored
spells in SPELL_REGISTRY to validate extraction accuracy.

WO-CONTENT-EXTRACT-001: Mechanical Extraction Pipeline — Spells

Usage:
    python tools/verify_spell_bridge.py
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from aidm.schemas.spell_definitions import SPELL_REGISTRY
from aidm.core.spell_resolver import (
    SpellDefinition, SpellTarget, SpellEffect, SaveEffect, DamageType,
)
from aidm.schemas.saves import SaveType


# ==========================================================================
# Field Mapping
# ==========================================================================

TARGET_TYPE_MAP = {
    SpellTarget.SINGLE: "single",
    SpellTarget.AREA: "area",
    SpellTarget.SELF: "self",
    SpellTarget.TOUCH: "touch",
    SpellTarget.RAY: "ray",
}

EFFECT_TYPE_MAP = {
    SpellEffect.DAMAGE: "damage",
    SpellEffect.HEALING: "healing",
    SpellEffect.BUFF: "buff",
    SpellEffect.DEBUFF: "debuff",
    SpellEffect.UTILITY: "utility",
}

SAVE_TYPE_MAP = {
    SaveType.REF: "reflex",
    SaveType.FORT: "fortitude",
    SaveType.WILL: "will",
}

SAVE_EFFECT_MAP = {
    SaveEffect.NONE: None,
    SaveEffect.HALF: "half",
    SaveEffect.NEGATES: "negates",
    SaveEffect.PARTIAL: "partial",
}

DAMAGE_TYPE_MAP = {
    DamageType.FIRE: "fire",
    DamageType.COLD: "cold",
    DamageType.ACID: "acid",
    DamageType.ELECTRICITY: "electricity",
    DamageType.SONIC: "sonic",
    DamageType.FORCE: "force",
    DamageType.POSITIVE: "positive",
    DamageType.NEGATIVE: "negative",
    DamageType.UNTYPED: "untyped",
}


@dataclass
class FieldComparison:
    """Comparison result for a single field."""
    field: str
    gold_value: Any
    extracted_value: Any
    match: bool
    note: str = ""


@dataclass
class SpellComparison:
    """Full comparison for one spell."""
    gold_name: str
    gold_id: str
    template_id: Optional[str]
    found: bool
    comparisons: List[FieldComparison]

    @property
    def match_count(self) -> int:
        return sum(1 for c in self.comparisons if c.match)

    @property
    def total_count(self) -> int:
        return len(self.comparisons)

    @property
    def match_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.match_count / self.total_count


def find_template_for_gold(
    gold: SpellDefinition,
    templates: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Find the extracted template that corresponds to a gold spell.

    Matches by source page (from rule_citations) and mechanical fingerprint.
    The OCR pages are offset by +1 from PHB page numbers (OCR file 0231.txt
    contains PHB page 230), so we search with that offset applied.
    """
    # Extract page number from gold's rule_citations
    gold_pages = set()
    for citation in gold.rule_citations:
        m = re.search(r"p\.(\d+)", citation)
        if m:
            gold_pages.add(int(m.group(1)))

    if not gold_pages:
        return None

    # Build candidate set from matching pages (with OCR offset tolerance)
    search_pages = set()
    for p in gold_pages:
        for offset in range(-2, 3):  # -2 to +2 page tolerance
            search_pages.add(p + offset)

    candidates = []
    for t in templates:
        m = re.search(r"p\.(\d+)", t.get("source_page", ""))
        if m and int(m.group(1)) in search_pages:
            candidates.append(t)

    if not candidates:
        return None

    if len(candidates) == 1:
        return candidates[0]

    # Multiple candidates — score by field similarity with strong weighting
    gold_school = gold.school.lower()
    gold_level = gold.level
    gold_effect = EFFECT_TYPE_MAP.get(gold.effect_type, "utility")
    gold_target = TARGET_TYPE_MAP.get(gold.target_type, "single")
    gold_save = SAVE_TYPE_MAP.get(gold.save_type) if gold.save_type else None
    gold_dt = DAMAGE_TYPE_MAP.get(gold.damage_type) if gold.damage_type else None
    gold_aoe = gold.aoe_shape.value if gold.aoe_shape else None

    best_score = -1
    best = None
    for c in candidates:
        score = 0
        # Level match is critical (10 points)
        if c.get("tier") == gold_level:
            score += 10
        # School match is very important (8 points)
        if c.get("school_category", "").lower() == gold_school:
            score += 8
        # Effect type (5 points)
        if c.get("effect_type") == gold_effect:
            score += 5
        # Target type (4 points)
        if c.get("target_type") == gold_target:
            score += 4
        # Damage type (4 points)
        if gold_dt and c.get("damage_type") == gold_dt:
            score += 4
        # Save type (3 points)
        if gold_save and c.get("save_type") == gold_save:
            score += 3
        elif gold_save is None and c.get("save_type") is None:
            score += 2
        # AoE shape (3 points)
        if gold_aoe and c.get("aoe_shape") in (gold_aoe, "spread"):
            score += 3  # burst/spread are interchangeable for matching
        elif gold_aoe is None and c.get("aoe_shape") is None:
            score += 1
        # Attack roll (2 points)
        if c.get("requires_attack_roll") == gold.requires_attack_roll:
            score += 2
        # Auto hit (2 points)
        if c.get("auto_hit") == gold.auto_hit:
            score += 2
        # Concentration (1 point)
        if c.get("concentration") == gold.concentration:
            score += 1

        # Prefer exact page match over nearby pages
        for page in gold_pages:
            if f"p.{page}" in c.get("source_page", ""):
                score += 5
                break

        if score > best_score:
            best_score = score
            best = c

    return best


def compare_spell(
    gold: SpellDefinition,
    template: Dict[str, Any],
) -> List[FieldComparison]:
    """Compare a gold spell to an extracted template."""
    comps = []

    # School
    comps.append(FieldComparison(
        "school",
        gold.school.lower(),
        template.get("school_category", ""),
        gold.school.lower() == template.get("school_category", ""),
    ))

    # Level
    comps.append(FieldComparison(
        "level",
        gold.level,
        template.get("tier"),
        gold.level == template.get("tier"),
    ))

    # Target type
    gold_tt = TARGET_TYPE_MAP.get(gold.target_type, "single")
    ext_tt = template.get("target_type", "single")
    comps.append(FieldComparison(
        "target_type",
        gold_tt,
        ext_tt,
        gold_tt == ext_tt,
    ))

    # Effect type
    gold_et = EFFECT_TYPE_MAP.get(gold.effect_type, "utility")
    ext_et = template.get("effect_type", "utility")
    comps.append(FieldComparison(
        "effect_type",
        gold_et,
        ext_et,
        gold_et == ext_et,
    ))

    # Damage type
    gold_dt = DAMAGE_TYPE_MAP.get(gold.damage_type) if gold.damage_type else None
    ext_dt = template.get("damage_type")
    comps.append(FieldComparison(
        "damage_type",
        gold_dt,
        ext_dt,
        gold_dt == ext_dt,
    ))

    # Save type
    gold_st = SAVE_TYPE_MAP.get(gold.save_type) if gold.save_type else None
    ext_st = template.get("save_type")
    comps.append(FieldComparison(
        "save_type",
        gold_st,
        ext_st,
        gold_st == ext_st,
    ))

    # Save effect
    gold_se = SAVE_EFFECT_MAP.get(gold.save_effect)
    ext_se = template.get("save_effect")
    comps.append(FieldComparison(
        "save_effect",
        gold_se,
        ext_se,
        gold_se == ext_se,
    ))

    # Concentration
    comps.append(FieldComparison(
        "concentration",
        gold.concentration,
        template.get("concentration", False),
        gold.concentration == template.get("concentration", False),
    ))

    # Requires attack roll
    comps.append(FieldComparison(
        "requires_attack_roll",
        gold.requires_attack_roll,
        template.get("requires_attack_roll", False),
        gold.requires_attack_roll == template.get("requires_attack_roll", False),
    ))

    # Auto hit
    comps.append(FieldComparison(
        "auto_hit",
        gold.auto_hit,
        template.get("auto_hit", False),
        gold.auto_hit == template.get("auto_hit", False),
    ))

    # Spell resistance
    comps.append(FieldComparison(
        "spell_resistance",
        # Gold doesn't have explicit SR field — infer from save presence
        True,  # Placeholder
        template.get("spell_resistance", False),
        True,  # Skip this comparison
        note="gold has no explicit SR field",
    ))

    return comps


def run_verification() -> None:
    """Run bridge verification."""
    print("=" * 60)
    print("Spell Bridge Verification")
    print("=" * 60)

    # Load extracted templates
    spells_path = PROJECT_ROOT / "aidm" / "data" / "content_pack" / "spells.json"
    if not spells_path.exists():
        print("ERROR: spells.json not found — run tools/extract_spells.py first")
        sys.exit(1)

    with open(spells_path) as f:
        templates = json.load(f)

    print(f"\nExtracted templates: {len(templates)}")
    print(f"Gold standard spells: {len(SPELL_REGISTRY)}")

    # Compare each gold spell
    results: List[SpellComparison] = []
    not_found: List[str] = []

    for spell_id, gold in sorted(SPELL_REGISTRY.items()):
        template = find_template_for_gold(gold, templates)

        if template is None:
            not_found.append(f"{gold.name} ({spell_id})")
            results.append(SpellComparison(
                gold_name=gold.name,
                gold_id=spell_id,
                template_id=None,
                found=False,
                comparisons=[],
            ))
            continue

        comps = compare_spell(gold, template)
        results.append(SpellComparison(
            gold_name=gold.name,
            gold_id=spell_id,
            template_id=template.get("template_id"),
            found=True,
            comparisons=comps,
        ))

    # Report
    found_count = sum(1 for r in results if r.found)
    print(f"\nMatched: {found_count}/{len(SPELL_REGISTRY)}")

    if not_found:
        print(f"\nNot found ({len(not_found)}):")
        for name in not_found:
            print(f"  - {name}")

    # Per-field accuracy
    field_totals: Dict[str, int] = {}
    field_matches: Dict[str, int] = {}
    for r in results:
        if not r.found:
            continue
        for c in r.comparisons:
            if c.note:  # Skip fields with notes (not comparable)
                continue
            field_totals[c.field] = field_totals.get(c.field, 0) + 1
            if c.match:
                field_matches[c.field] = field_matches.get(c.field, 0) + 1

    print("\nPer-field accuracy:")
    for field in sorted(field_totals.keys()):
        total = field_totals[field]
        matches = field_matches.get(field, 0)
        pct = matches / total * 100 if total > 0 else 0
        status = "OK" if pct >= 70 else "LOW"
        print(f"  {field:25s}: {matches:3d}/{total:3d} ({pct:5.1f}%) {status}")

    # Overall accuracy
    total_comps = sum(
        len([c for c in r.comparisons if not c.note])
        for r in results if r.found
    )
    total_matches = sum(
        sum(1 for c in r.comparisons if c.match and not c.note)
        for r in results if r.found
    )
    overall = total_matches / total_comps * 100 if total_comps > 0 else 0
    print(f"\nOverall field match rate: {total_matches}/{total_comps} ({overall:.1f}%)")

    # Show mismatches
    print("\nMismatches (first 30):")
    mismatch_count = 0
    for r in results:
        if not r.found:
            continue
        for c in r.comparisons:
            if not c.match and not c.note:
                print(f"  {r.gold_name:30s} {c.field:20s}: "
                      f"gold={c.gold_value!r:20s} extracted={c.extracted_value!r}")
                mismatch_count += 1
                if mismatch_count >= 30:
                    break
        if mismatch_count >= 30:
            break

    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {found_count}/{len(SPELL_REGISTRY)} gold spells matched, "
          f"{overall:.1f}% field accuracy")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_verification()
