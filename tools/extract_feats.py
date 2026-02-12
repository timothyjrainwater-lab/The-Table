"""Feat Extraction Pipeline — WO-CONTENT-EXTRACT-003.

Parses OCR text from PHB Chapter 5 (pages 89-103) and extracts mechanical
feat data into IP-clean MechanicalFeatTemplate records.

Three-layer model:
  - Bone: prerequisites, bonus values, BAB/ability score thresholds
  - Muscle: triggers, action economy changes, conditional modifiers
  - Skin: original names, flavor prose — NEVER in output

Usage:
    python tools/extract_feats.py [--source-dir DIR] [--output-dir DIR]
"""

import json
import logging
import re
import sys
from dataclasses import dataclass, fields as dc_fields
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOURCE_ID = "681f92bc94ff"
# PHB Chapter 5: Feats spans pages 89-103 (0-indexed page files 0089-0103)
FEAT_PAGE_START = 89
FEAT_PAGE_END = 103

# Feat type tags as they appear in OCR headers
FEAT_TYPE_MAP = {
    "GENERAL": "general",
    "METAMAGIC": "metamagic",
    "ITEM CREATION": "item_creation",
    "SPECIAL": "general",  # Spell Mastery is tagged [SPECIAL] but is general
}

# ---------------------------------------------------------------------------
# Dataclass — MechanicalFeatTemplate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MechanicalFeatTemplate:
    template_id: str                        # "FEAT_017"
    feat_type: str                          # "general", "metamagic", "item_creation"

    # Prerequisites (bone)
    prereq_ability_scores: dict             # {"str": 13} or {}
    prereq_bab: Optional[int]              # Minimum BAB required
    prereq_feat_refs: tuple                 # ("FEAT_003",) — resolved in Phase 2
    prereq_class_features: tuple            # ("turn_undead",)
    prereq_caster_level: Optional[int]
    prereq_other: tuple                     # Freeform mechanical prereqs

    # Mechanical effect (bone + muscle)
    effect_type: str                        # "attack_modifier", "skill_modifier", etc.
    bonus_value: Optional[int]
    bonus_type: Optional[str]               # "initiative", "attack_roll", etc.
    bonus_applies_to: Optional[str]         # "all", "melee", "ranged", etc.

    # Trigger (muscle)
    trigger: Optional[str]
    replaces_normal: Optional[str]

    # Action economy changes (muscle)
    grants_action: Optional[str]
    removes_penalty: Optional[str]

    # Conditional (muscle)
    stacks_with: tuple
    limited_to: Optional[str]

    # Fighter bonus feat eligible
    fighter_bonus_eligible: bool

    # Repeatable
    can_take_multiple: bool
    effects_stack: bool

    # Metamagic slot increase
    metamagic_slot_increase: Optional[int]

    # Provenance
    source_page: str
    source_id: str


# ---------------------------------------------------------------------------
# OCR text cleaning
# ---------------------------------------------------------------------------

def ocr_clean(text: str) -> str:
    """Fix common OCR artifacts in the feat pages."""
    # Fix spaced-out italicized text: "I f  y o u" -> "If you"
    # Detect runs of single chars separated by spaces
    def fix_spaced_text(m):
        chars = m.group(0).replace(" ", "")
        return chars

    # Pattern: single char, space, single char, space, ... (min 4 chars)
    text = re.sub(
        r"(?<![A-Za-z])([A-Za-z]) ([A-Za-z]) ([A-Za-z])(?: ([A-Za-z]))+(?![A-Za-z])",
        fix_spaced_text,
        text,
    )
    # Clean up /rhombus4 OCR artifacts
    text = text.replace("/rhombus4", "•")
    return text


# ---------------------------------------------------------------------------
# Feat entry parsing
# ---------------------------------------------------------------------------

# Regex for feat header: "FEAT NAME [TYPE]" or "FEAT NAME\n[TYPE]"
FEAT_HEADER_RE = re.compile(
    r"^([A-Z][A-Z\s()'/,-]+?)\s*\[([A-Z ]+)\]\s*$",
    re.MULTILINE,
)

# Alternative: header name on one line, [TYPE] on next line
FEAT_HEADER_SPLIT_RE = re.compile(
    r"^([A-Z][A-Z\s()'/,-]+?)\s*\n\[([A-Z ]+)\]\s*$",
    re.MULTILINE,
)

# Section labels within a feat entry
SECTION_LABELS = (
    "Prerequisite:",
    "Prerequisites:",
    "Benefit:",
    "Normal:",
    "Special:",
)


def find_feat_entries(text: str) -> List[dict]:
    """Find all feat entries in a page of OCR text.

    Returns list of dicts with keys:
        'name': original feat name (for provenance only)
        'feat_type_raw': type tag from header
        'prerequisite': prerequisite text
        'benefit': benefit text
        'normal': normal text
        'special': special text
        'full_text': all text of the entry
    """
    entries = []

    # Find all feat headers (both single-line and split-line)
    headers = []
    for m in FEAT_HEADER_RE.finditer(text):
        name = m.group(1).strip()
        feat_type = m.group(2).strip()
        headers.append((m.start(), m.end(), name, feat_type))

    for m in FEAT_HEADER_SPLIT_RE.finditer(text):
        name = m.group(1).strip()
        feat_type = m.group(2).strip()
        # Avoid duplicates — check if this start position is already covered
        if not any(abs(h[0] - m.start()) < 5 for h in headers):
            headers.append((m.start(), m.end(), name, feat_type))

    # Sort by position
    headers.sort(key=lambda h: h[0])

    for i, (start, end, name, feat_type) in enumerate(headers):
        # Get text until next header or end of text
        if i + 1 < len(headers):
            entry_text = text[end:headers[i + 1][0]]
        else:
            entry_text = text[end:]

        # Remove chapter footer noise
        entry_text = re.sub(r"CHAPTER\s+\d+:\s*\n?FEATS\s*$", "", entry_text).strip()
        # Remove illustration credits
        entry_text = re.sub(r"Illus\.\s+by\s+[A-Z]\.\s+\w+\s*", "", entry_text).strip()

        entry = _parse_feat_sections(name, feat_type, entry_text)
        entries.append(entry)

    return entries


def _parse_feat_sections(name: str, feat_type_raw: str, text: str) -> dict:
    """Parse a feat entry's sections (Prerequisite, Benefit, Normal, Special)."""
    entry = {
        "name": name,
        "feat_type_raw": feat_type_raw,
        "prerequisite": "",
        "benefit": "",
        "normal": "",
        "special": "",
        "full_text": text,
    }

    # Split the text by section labels
    # First line(s) before any label is the flavor description (skin — discard)
    section_re = re.compile(
        r"(Prerequisites?|Benefit|Normal|Special)\s*:\s*",
        re.IGNORECASE,
    )

    parts = section_re.split(text)
    # parts alternates: [before_first_label, label1, content1, label2, content2, ...]
    if len(parts) >= 3:
        i = 1
        while i < len(parts) - 1:
            label = parts[i].strip().lower().rstrip("s")  # normalize
            content = parts[i + 1].strip()
            if label == "prerequisite":
                entry["prerequisite"] = content
            elif label == "benefit":
                entry["benefit"] = content
            elif label == "normal":
                entry["normal"] = content
            elif label == "special":
                entry["special"] = content
            i += 2

    return entry


# ---------------------------------------------------------------------------
# Prerequisite parsing
# ---------------------------------------------------------------------------

ABILITY_SCORE_RE = re.compile(
    r"(Str|Dex|Con|Int|Wis|Cha)\s+(\d+)",
    re.IGNORECASE,
)

BAB_RE = re.compile(
    r"base attack bonus\s*\+?(\d+)",
    re.IGNORECASE,
)

CASTER_LEVEL_RE = re.compile(
    r"(?:caster|spellcaster)\s+level\s+(\d+)",
    re.IGNORECASE,
)

FIGHTER_LEVEL_RE = re.compile(
    r"fighter\s+level\s+(\d+)",
    re.IGNORECASE,
)

CHARACTER_LEVEL_RE = re.compile(
    r"character\s+level\s+(\d+)",
    re.IGNORECASE,
)

SKILL_RANK_RE = re.compile(
    r"(\w[\w\s]*?)\s+(\d+)\s+rank",
    re.IGNORECASE,
)


def parse_prerequisites(text: str) -> dict:
    """Parse prerequisite text into structured data.

    Returns dict with keys:
        ability_scores: {"str": 13, "dex": 15, ...}
        bab: int or None
        feat_names: ["Power Attack", "Dodge", ...]  (original names, resolved later)
        class_features: ["turn_undead", "wild_shape", ...]
        caster_level: int or None
        other: [str, ...]
    """
    result = {
        "ability_scores": {},
        "bab": None,
        "feat_names": [],
        "class_features": [],
        "caster_level": None,
        "other": [],
    }

    if not text.strip():
        return result

    # Normalize: collapse newlines into spaces (OCR line wraps)
    text = re.sub(r"\s*\n\s*", " ", text).strip()
    # Fix hyphen-broken words: "Two- Weapon" -> "Two-Weapon"
    text = re.sub(r"-\s+", "-", text)

    # Extract ability scores
    for m in ABILITY_SCORE_RE.finditer(text):
        ability = m.group(1).lower()[:3]
        score = int(m.group(2))
        result["ability_scores"][ability] = score

    # Extract BAB
    bab_m = BAB_RE.search(text)
    if bab_m:
        result["bab"] = int(bab_m.group(1))

    # Extract caster level
    cl_m = CASTER_LEVEL_RE.search(text)
    if cl_m:
        result["caster_level"] = int(cl_m.group(1))

    # Extract fighter level
    fl_m = FIGHTER_LEVEL_RE.search(text)
    if fl_m:
        result["other"].append(f"fighter_level_{fl_m.group(1)}")

    # Extract character level
    char_m = CHARACTER_LEVEL_RE.search(text)
    if char_m:
        result["other"].append(f"character_level_{char_m.group(1)}")

    # Extract skill ranks
    for m in SKILL_RANK_RE.finditer(text):
        skill_name = m.group(1).strip().lower().replace(" ", "_")
        ranks = int(m.group(2))
        result["other"].append(f"skill_{skill_name}_{ranks}_rank")

    # Extract class features
    class_feature_patterns = [
        (r"(?:ability\s+to\s+)?turn\s+(?:or\s+rebuke\s+)?(?:undead|creatures)", "turn_undead"),
        (r"wild\s+shape\s+ability", "wild_shape"),
    ]
    for pattern, feature in class_feature_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            result["class_features"].append(feature)

    # Extract wizard level (Spell Mastery)
    wiz_m = re.search(r"[Ww]izard\s+level\s+(\d+)", text)
    if wiz_m:
        result["other"].append(f"wizard_level_{wiz_m.group(1)}")

    # Extract proficiency requirements
    if re.search(r"proficien(?:cy|t)\s+with\s+(?:selected\s+)?weapon", text, re.IGNORECASE):
        result["other"].append("weapon_proficiency")
    if re.search(r"[Ww]eapon\s+[Pp]roficiency\s*\(", text, re.IGNORECASE):
        result["other"].append("weapon_proficiency")

    # Extract feat name references — everything that isn't an ability score,
    # BAB, caster level, fighter level, character level, skill rank, or class feature
    feat_names = _extract_feat_name_refs(text)
    result["feat_names"] = feat_names

    return result


def _extract_feat_name_refs(text: str) -> List[str]:
    """Extract feat name references from prerequisite text.

    This finds references like "Power Attack", "Point Blank Shot",
    "Weapon Focus with selected weapon", etc.
    """
    # Normalize: collapse newlines into spaces
    cleaned = re.sub(r"\s*\n\s*", " ", text).strip()
    # Fix hyphen-broken words: "Two- Weapon" -> "Two-Weapon"
    cleaned = re.sub(r"-\s+", "-", cleaned)
    # Remove already-parsed elements
    # Remove ability score requirements
    cleaned = ABILITY_SCORE_RE.sub("", cleaned)
    # Remove BAB
    cleaned = BAB_RE.sub("", cleaned)
    # Remove caster level
    cleaned = CASTER_LEVEL_RE.sub("", cleaned)
    # Remove fighter level
    cleaned = FIGHTER_LEVEL_RE.sub("", cleaned)
    # Remove character level
    cleaned = CHARACTER_LEVEL_RE.sub("", cleaned)
    # Remove skill ranks
    cleaned = SKILL_RANK_RE.sub("", cleaned)
    # Remove class features
    cleaned = re.sub(
        r"(?:ability\s+to\s+)?turn\s+(?:or\s+rebuke\s+)?(?:undead|creatures)|wild\s+shape\s+ability",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Remove wizard level
    cleaned = re.sub(r"[Ww]izard\s+level\s+\d+\w*", "", cleaned)
    # Remove proficiency mentions
    cleaned = re.sub(
        r"(?:proficien(?:cy|t)\s+with\s+(?:selected\s+)?weapon|[Ww]eapon\s+[Pp]roficiency\s*\([^)]*\))",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Split by comma and clean
    parts = [p.strip().rstrip(".") for p in cleaned.split(",")]

    # Known feat name patterns — capitalized multi-word phrases
    feat_names = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Remove trailing qualifiers like "with selected weapon"
        part = re.sub(r"\s+with\s+(?:selected\s+)?weapon\b.*", "", part).strip()
        # Must start with a capital letter and be at least 3 chars
        if len(part) >= 3 and part[0].isupper():
            # Verify it looks like a feat name (not prose)
            if not re.match(r"^(A |An |The |You |If |When |See )", part):
                feat_names.append(part)

    return feat_names


# ---------------------------------------------------------------------------
# Effect classification
# ---------------------------------------------------------------------------

def classify_feat_effect(entry: dict) -> dict:
    """Classify the mechanical effect of a feat from its benefit text.

    Returns dict with keys matching MechanicalFeatTemplate effect fields.
    """
    benefit = entry.get("benefit", "")
    special = entry.get("special", "")
    normal = entry.get("normal", "")
    full_text = entry.get("full_text", "")
    feat_type_raw = entry.get("feat_type_raw", "GENERAL")
    # Use full_text for flags that may appear outside labeled sections
    combined = benefit + " " + special

    result = {
        "effect_type": "special_action",
        "bonus_value": None,
        "bonus_type": None,
        "bonus_applies_to": None,
        "trigger": None,
        "replaces_normal": None,
        "grants_action": None,
        "removes_penalty": None,
        "stacks_with": (),
        "limited_to": None,
        "fighter_bonus_eligible": False,
        "can_take_multiple": False,
        "effects_stack": False,
        "metamagic_slot_increase": None,
    }

    # Fighter bonus feat eligibility — search full_text since "Special:"
    # labels are sometimes missing in OCR (text after Normal: without label)
    if re.search(r"fighter\s+(?:may\s+select|bonus\s+feat)", full_text, re.IGNORECASE):
        result["fighter_bonus_eligible"] = True

    # Can take multiple times
    if re.search(r"(?:gain|take)\s+(?:this\s+feat|[\w\s]+)\s+multiple\s+times", full_text, re.IGNORECASE):
        result["can_take_multiple"] = True
        if re.search(r"effects?\s+stack", full_text, re.IGNORECASE):
            result["effects_stack"] = True

    # --- Metamagic and item creation feats are never fighter bonus feats ---
    mapped_type = FEAT_TYPE_MAP.get(feat_type_raw, "")
    if mapped_type in ("metamagic", "item_creation"):
        result["fighter_bonus_eligible"] = False

    # --- Metamagic feats ---
    if mapped_type == "metamagic":
        result["effect_type"] = "metamagic_modifier"
        # Extract slot increase
        slot_m = re.search(
            r"spell\s+slot\s+(\w+)\s+level(?:s)?\s+higher",
            benefit,
            re.IGNORECASE,
        )
        if slot_m:
            word_to_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
            word = slot_m.group(1).lower()
            result["metamagic_slot_increase"] = word_to_num.get(word, None)
            if result["metamagic_slot_increase"] is None:
                try:
                    result["metamagic_slot_increase"] = int(word)
                except ValueError:
                    pass
        return result

    # --- Item creation feats ---
    if mapped_type == "item_creation":
        result["effect_type"] = "item_creation"
        return result

    # --- Skill bonus feats (+2 to two skills) ---
    skill_bonus_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+all\s+([\w\s]+?)\s+checks?\s+and\s+([\w\s]+?)\s+checks?",
        benefit,
        re.IGNORECASE,
    )
    if skill_bonus_m:
        result["effect_type"] = "skill_modifier"
        result["bonus_value"] = int(skill_bonus_m.group(1))
        result["bonus_type"] = "skill"
        skill1 = re.sub(r"\s+", "_", skill_bonus_m.group(2).strip().lower())
        skill2 = re.sub(r"\s+", "_", skill_bonus_m.group(3).strip().lower())
        result["bonus_applies_to"] = f"{skill1},{skill2}"
        return result

    # --- Save bonus feats ---
    save_bonus_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+all\s+(Will|Reflex|Fortitude)\s+saving\s+throws?",
        benefit,
        re.IGNORECASE,
    )
    if save_bonus_m:
        result["effect_type"] = "save_modifier"
        result["bonus_value"] = int(save_bonus_m.group(1))
        result["bonus_type"] = "saves"
        result["bonus_applies_to"] = save_bonus_m.group(2).lower()
        return result

    # --- Initiative modifier ---
    init_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+initiative\s+checks?",
        benefit,
        re.IGNORECASE,
    )
    if init_m:
        result["effect_type"] = "initiative_modifier"
        result["bonus_value"] = int(init_m.group(1))
        result["bonus_type"] = "initiative"
        result["bonus_applies_to"] = "all"
        return result

    # --- AC modifier ---
    ac_m = re.search(
        r"\+(\d+)\s+(?:dodge\s+)?bonus\s+to\s+(?:Armor\s+Class|AC)",
        benefit,
        re.IGNORECASE,
    )
    if ac_m:
        result["effect_type"] = "ac_modifier"
        result["bonus_value"] = int(ac_m.group(1))
        result["bonus_type"] = "ac"
        # Check if conditional
        if re.search(r"against\s+attacks\s+of\s+opportunity", benefit, re.IGNORECASE):
            result["trigger"] = "on_aoo_provoked"
            result["bonus_applies_to"] = "vs_aoo"
        elif re.search(r"against\s+attacks\s+from\s+that\s+opponent", benefit, re.IGNORECASE):
            result["trigger"] = "on_designate_opponent"
            result["bonus_applies_to"] = "vs_designated"
        elif re.search(r"shield\s+bonus", benefit, re.IGNORECASE):
            result["bonus_applies_to"] = "shield"
        else:
            result["bonus_applies_to"] = "all"
        return result

    # --- Shield bonus to AC ---
    shield_ac_m = re.search(
        r"\+(\d+)\s+shield\s+bonus\s+to\s+(?:your\s+)?(?:AC|Armor\s+Class)",
        benefit,
        re.IGNORECASE,
    )
    if shield_ac_m:
        result["effect_type"] = "ac_modifier"
        result["bonus_value"] = int(shield_ac_m.group(1))
        result["bonus_type"] = "ac"
        result["bonus_applies_to"] = "shield"
        return result

    # --- Attack roll modifier ---
    attack_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+(?:all\s+)?attack\s+rolls?",
        benefit,
        re.IGNORECASE,
    )
    if attack_m:
        result["effect_type"] = "attack_modifier"
        result["bonus_value"] = int(attack_m.group(1))
        result["bonus_type"] = "attack_roll"
        if re.search(r"selected\s+weapon|chosen\s+weapon", benefit, re.IGNORECASE):
            result["bonus_applies_to"] = "selected_weapon"
        elif re.search(r"ranged\s+weapon", benefit, re.IGNORECASE):
            result["bonus_applies_to"] = "ranged"
        else:
            result["bonus_applies_to"] = "all"
        return result

    # --- Attack and damage modifier (Point Blank Shot pattern) ---
    atk_dmg_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+attack\s+and\s+damage\s+rolls?\s+with\s+ranged\s+weapons?",
        benefit,
        re.IGNORECASE,
    )
    if atk_dmg_m:
        result["effect_type"] = "attack_modifier"
        result["bonus_value"] = int(atk_dmg_m.group(1))
        result["bonus_type"] = "attack_and_damage"
        result["bonus_applies_to"] = "ranged_30ft"
        return result

    # --- Damage roll modifier ---
    damage_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+(?:all\s+)?damage\s+rolls?",
        benefit,
        re.IGNORECASE,
    )
    if damage_m:
        result["effect_type"] = "damage_modifier"
        result["bonus_value"] = int(damage_m.group(1))
        result["bonus_type"] = "damage_roll"
        if re.search(r"selected\s+weapon|chosen\s+weapon", benefit, re.IGNORECASE):
            result["bonus_applies_to"] = "selected_weapon"
        else:
            result["bonus_applies_to"] = "all"
        return result

    # --- Caster level check bonus (Spell Penetration) ---
    cl_check_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+caster\s+level\s+checks?",
        benefit,
        re.IGNORECASE,
    )
    if cl_check_m:
        result["effect_type"] = "caster_level_modifier"
        result["bonus_value"] = int(cl_check_m.group(1))
        result["bonus_type"] = "caster_level_check"
        result["bonus_applies_to"] = "spell_resistance"
        return result

    # --- Save DC modifier (Spell Focus) ---
    dc_m = re.search(
        r"\+(\d+)\s+(?:bonus\s+)?(?:to\s+)?(?:the\s+)?(?:Difficulty\s+Class|DC)\b",
        benefit,
        re.IGNORECASE,
    )
    if dc_m:
        result["effect_type"] = "save_dc_modifier"
        result["bonus_value"] = int(dc_m.group(1))
        result["bonus_type"] = "save_dc"
        result["bonus_applies_to"] = "selected_school"
        return result

    # --- Threat range doubling (Improved Critical) ---
    if re.search(r"threat\s+range\s+is\s+doubled", benefit, re.IGNORECASE):
        result["effect_type"] = "critical_modifier"
        result["bonus_value"] = 2
        result["bonus_type"] = "threat_range_multiplier"
        result["bonus_applies_to"] = "selected_weapon"
        return result

    # --- Hit point bonus (Toughness) ---
    hp_m = re.search(r"\+(\d+)\s+hit\s+points?", benefit, re.IGNORECASE)
    if hp_m:
        result["effect_type"] = "hp_modifier"
        result["bonus_value"] = int(hp_m.group(1))
        result["bonus_type"] = "hp"
        result["bonus_applies_to"] = "all"
        return result

    # --- Enhancement bonus to summoned creatures ---
    summon_m = re.search(
        r"\+(\d+)\s+enhancement\s+bonus\s+to\s+Strength\s+and\s+Constitution",
        benefit,
        re.IGNORECASE,
    )
    if summon_m:
        result["effect_type"] = "summoning_modifier"
        result["bonus_value"] = int(summon_m.group(1))
        result["bonus_type"] = "enhancement"
        result["bonus_applies_to"] = "summoned_creatures"
        return result

    # --- Removes penalty ---
    if re.search(r"do\s+not\s+provoke\s+an?\s+attack\s+of\s+opportunity", benefit, re.IGNORECASE):
        result["removes_penalty"] = "no_aoo"
        # Check what action it applies to
        if re.search(r"grapple", benefit, re.IGNORECASE):
            result["effect_type"] = "special_action"
            result["trigger"] = "on_grapple"
            result["removes_penalty"] = "no_aoo_on_grapple"
        elif re.search(r"disarm", benefit, re.IGNORECASE):
            result["effect_type"] = "special_action"
            result["trigger"] = "on_disarm"
            result["removes_penalty"] = "no_aoo_on_disarm"
        elif re.search(r"sunder", benefit, re.IGNORECASE):
            result["effect_type"] = "special_action"
            result["trigger"] = "on_sunder"
            result["removes_penalty"] = "no_aoo_on_sunder"
        elif re.search(r"bull\s+rush", benefit, re.IGNORECASE):
            result["effect_type"] = "special_action"
            result["trigger"] = "on_bull_rush"
            result["removes_penalty"] = "no_aoo_on_bull_rush"
        elif re.search(r"overrun", benefit, re.IGNORECASE):
            result["effect_type"] = "special_action"
            result["trigger"] = "on_overrun"
            result["removes_penalty"] = "no_aoo_on_overrun"
        elif re.search(r"trip", benefit, re.IGNORECASE):
            result["effect_type"] = "special_action"
            result["trigger"] = "on_trip"
            result["removes_penalty"] = "no_aoo_on_trip"

    # Check for +4 bonus on opposed check (Improved X feats)
    opposed_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+(?:the\s+)?(?:opposed\s+)?(?:Strength|attack)\s+check",
        benefit,
        re.IGNORECASE,
    )
    if opposed_m and result.get("removes_penalty"):
        result["bonus_value"] = int(opposed_m.group(1))
        result["bonus_type"] = "opposed_check"
        return result

    # +4 bonus on grapple checks (Improved Grapple)
    grapple_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+(?:all\s+)?grapple\s+checks?",
        benefit,
        re.IGNORECASE,
    )
    if grapple_m:
        result["effect_type"] = "special_action"
        result["bonus_value"] = int(grapple_m.group(1))
        result["bonus_type"] = "grapple_check"
        result["trigger"] = "on_grapple"
        if not result.get("removes_penalty"):
            result["removes_penalty"] = "no_aoo_on_grapple"
        return result

    if result.get("removes_penalty"):
        return result

    # --- Extra attack (Cleave, Rapid Shot, TWF) ---
    if re.search(r"extra\s+(?:melee\s+)?attack", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        if re.search(r"drop|killing|below\s+0", benefit, re.IGNORECASE):
            result["trigger"] = "on_kill"
            result["grants_action"] = "extra_melee_attack_on_kill"
        elif re.search(r"ranged", benefit, re.IGNORECASE):
            result["grants_action"] = "extra_ranged_attack"
        elif re.search(r"off-hand|off\s+hand", benefit, re.IGNORECASE):
            result["grants_action"] = "extra_off_hand_attack"
        else:
            result["grants_action"] = "extra_attack"
        return result

    # Third off-hand attack
    if re.search(r"third\s+attack\s+with\s+your\s+off-hand", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["grants_action"] = "third_off_hand_attack"
        return result

    # Second off-hand attack
    if re.search(r"second\s+attack\s+with\s+your\s+off-hand", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["grants_action"] = "second_off_hand_attack"
        return result

    # --- Penalty reduction (TWF) ---
    twf_m = re.search(
        r"penalties\s+on\s+attack\s+rolls\s+for\s+fighting\s+with\s+two\s+weapons\s+are\s+reduced",
        benefit,
        re.IGNORECASE,
    )
    if twf_m:
        result["effect_type"] = "attack_modifier"
        result["removes_penalty"] = "twf_penalty_reduction"
        return result

    # --- Retain shield bonus on bash ---
    if re.search(r"retain\s+(?:shield|your)\s+(?:shield\s+)?bonus\s+to\s+AC\s+when\s+(?:shield\s+)?bash",
                  benefit, re.IGNORECASE):
        result["effect_type"] = "passive_defense"
        result["removes_penalty"] = "keep_shield_bonus_on_bash"
        return result

    # --- Action economy: draw as free action ---
    if re.search(r"draw\s+a?\s*weapon\s+as\s+a\s+free\s+action", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["grants_action"] = "draw_weapon_free"
        return result

    # --- Reload speed change ---
    if re.search(r"reload\s+.*?(?:free\s+action|move\s+action)", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["grants_action"] = "faster_reload"
        return result

    # --- Movement-based feats ---
    if re.search(r"move\s+(?:before\s+and\s+after|and\s+attack)", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["grants_action"] = "move_and_attack"
        return result

    # Shot on the Run
    if re.search(r"move\s+.*?ranged\s+attack\s+.*?move", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["grants_action"] = "move_shoot_move"
        return result

    # --- Run speed modifier ---
    if re.search(r"five\s+times\s+your\s+normal\s+speed", benefit, re.IGNORECASE):
        result["effect_type"] = "movement_modifier"
        result["bonus_value"] = 5
        result["bonus_type"] = "run_multiplier"
        return result

    # --- Proficiency feats ---
    if re.search(r"(?:proficient|make\s+attack\s+rolls\s+.*?normally)", benefit, re.IGNORECASE):
        if re.search(r"armor\s+check\s+penalty.*?only", benefit, re.IGNORECASE):
            result["effect_type"] = "proficiency"
            result["removes_penalty"] = "armor_check_penalty_restriction"
            return result
        result["effect_type"] = "proficiency"
        result["removes_penalty"] = "nonproficiency_penalty"
        return result

    # --- Combat Expertise: trade attack for AC ---
    if re.search(r"penalty.*?attack\s+roll.*?(?:dodge\s+)?bonus.*?(?:AC|Armor\s+Class)", benefit, re.IGNORECASE | re.DOTALL):
        result["effect_type"] = "special_action"
        result["trigger"] = "on_attack_action"
        result["grants_action"] = "trade_attack_for_ac"
        return result

    # --- Power Attack: trade attack for damage ---
    if re.search(r"subtract.*?(?:melee\s+)?attack\s+rolls?.*?add.*?(?:melee\s+)?damage", benefit, re.IGNORECASE | re.DOTALL):
        result["effect_type"] = "special_action"
        result["trigger"] = "on_attack_action"
        result["grants_action"] = "trade_attack_for_damage"
        return result

    # --- Deflect Arrows ---
    if re.search(r"deflect\s+it\s+so\s+.*?no\s+damage", benefit, re.IGNORECASE):
        result["effect_type"] = "passive_defense"
        result["trigger"] = "on_ranged_hit"
        result["grants_action"] = "deflect_ranged_attack"
        return result

    # --- Snatch Arrows ---
    if re.search(r"catch\s+.*?arrow|snatch\s+.*?arrow", benefit, re.IGNORECASE):
        result["effect_type"] = "passive_defense"
        result["trigger"] = "on_ranged_hit"
        result["grants_action"] = "catch_ranged_weapon"
        return result

    # --- Blind-Fight ---
    if re.search(r"reroll\s+your?\s+miss\s+chance", benefit, re.IGNORECASE):
        result["effect_type"] = "passive_defense"
        result["trigger"] = "on_miss_from_concealment"
        result["grants_action"] = "reroll_miss_chance"
        return result

    # --- Combat Reflexes: extra AoO ---
    if re.search(r"additional\s+attacks?\s+of\s+opportunity", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["trigger"] = "on_aoo_provoked"
        result["grants_action"] = "extra_aoo"
        return result

    # --- Whirlwind Attack ---
    if re.search(r"one\s+melee\s+attack.*?each\s+opponent\s+within\s+reach", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["trigger"] = "on_full_attack"
        result["grants_action"] = "attack_all_in_reach"
        return result

    # --- Manyshot ---
    if re.search(r"fire\s+(?:two|multiple)\s+arrows?", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["trigger"] = "on_standard_attack"
        result["grants_action"] = "fire_multiple_arrows"
        return result

    # --- Stunning Fist ---
    if re.search(r"stunned\s+for\s+1\s+round", benefit, re.IGNORECASE):
        result["effect_type"] = "special_action"
        result["trigger"] = "on_unarmed_hit"
        result["grants_action"] = "stun_on_hit"
        return result

    # --- Improved Counterspell ---
    if re.search(r"counterspell", benefit, re.IGNORECASE):
        result["effect_type"] = "special_action"
        result["trigger"] = "on_counterspell"
        result["grants_action"] = "counterspell_with_same_school"
        return result

    # --- Track ---
    if re.search(r"Survival\s+check.*?find\s+tracks", benefit, re.IGNORECASE):
        result["effect_type"] = "special_action"
        result["grants_action"] = "track_with_survival"
        return result

    # --- Diehard ---
    if re.search(r"automatically\s+become\s+stable", benefit, re.IGNORECASE):
        result["effect_type"] = "passive_defense"
        result["trigger"] = "on_negative_hp"
        result["grants_action"] = "auto_stabilize"
        return result

    # --- Endurance: +4 to various checks ---
    endurance_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+the\s+following\s+checks\s+and\s+saves",
        benefit,
        re.IGNORECASE,
    )
    if endurance_m:
        result["effect_type"] = "save_modifier"
        result["bonus_value"] = int(endurance_m.group(1))
        result["bonus_type"] = "endurance_checks"
        result["bonus_applies_to"] = "stamina_checks"
        return result

    # --- Mounted Combat feats ---
    if re.search(r"Ride\s+check.*?negate\s+the\s+hit", benefit, re.IGNORECASE):
        result["effect_type"] = "passive_defense"
        result["trigger"] = "on_mount_hit"
        result["grants_action"] = "ride_check_negate_hit"
        return result

    # --- Mounted Archery: penalty halved ---
    if re.search(r"penalty.*?mounted\s+is\s+halved", benefit, re.IGNORECASE):
        result["effect_type"] = "attack_modifier"
        result["removes_penalty"] = "halve_mounted_ranged_penalty"
        return result

    # --- Ride-By Attack ---
    if re.search(r"charge\s+action.*?move\s+again", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["trigger"] = "on_mounted_charge"
        result["grants_action"] = "ride_by_attack"
        return result

    # --- Spirited Charge ---
    if re.search(r"double\s+damage|triple\s+damage", benefit, re.IGNORECASE):
        result["effect_type"] = "damage_modifier"
        result["trigger"] = "on_mounted_charge"
        result["bonus_value"] = 2
        result["bonus_type"] = "damage_multiplier"
        return result

    # --- Trample ---
    if re.search(r"overrun\s+.*?mounted", benefit, re.IGNORECASE):
        result["effect_type"] = "special_action"
        result["trigger"] = "on_mounted_overrun"
        result["grants_action"] = "mount_hoof_attack_on_overrun"
        return result

    # --- Natural Spell ---
    if re.search(r"cast\s+spells?\s+while\s+in\s+a?\s*wild\s+shape", benefit, re.IGNORECASE):
        result["effect_type"] = "special_action"
        result["grants_action"] = "cast_in_wild_shape"
        result["limited_to"] = "druid_wild_shape"
        return result

    # --- Spell Mastery ---
    if re.search(r"prepare\s+.*?spells?\s+without\s+.*?spellbook", benefit, re.IGNORECASE):
        result["effect_type"] = "special_action"
        result["grants_action"] = "prepare_without_spellbook"
        result["limited_to"] = "wizard"
        return result

    # --- Weapon Finesse ---
    if re.search(r"Dexterity\s+modifier\s+instead\s+of.*?Strength", benefit, re.IGNORECASE):
        result["effect_type"] = "attack_modifier"
        result["grants_action"] = "use_dex_for_attack"
        result["limited_to"] = "light_weapons"
        return result

    # --- Leadership ---
    if re.search(r"attract\s+loyal\s+companions", benefit, re.IGNORECASE):
        result["effect_type"] = "special_action"
        result["grants_action"] = "attract_cohort_and_followers"
        return result

    # --- Improved Turning: +turn_level ---
    if re.search(r"turning\s+check.*?as\s+if.*?higher\s+level", benefit, re.IGNORECASE):
        result["effect_type"] = "class_feature_modifier"
        result["bonus_value"] = None
        result["bonus_type"] = "turning_level"
        return result

    # --- Extra Turning ---
    if re.search(r"four\s+more\s+times.*?per\s+day|additional.*?turning", benefit, re.IGNORECASE):
        result["effect_type"] = "class_feature_modifier"
        result["bonus_value"] = 4
        result["bonus_type"] = "turning_attempts"
        return result

    # --- Skill Focus: +3 to one skill ---
    skill_focus_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+(?:all\s+)?(?:checks?\s+with\s+)?(?:a\s+)?(?:selected|chosen)?\s*(?:skill)?",
        benefit,
        re.IGNORECASE,
    )
    if skill_focus_m and re.search(r"(?:selected|chosen)\s+skill", benefit, re.IGNORECASE):
        result["effect_type"] = "skill_modifier"
        result["bonus_value"] = int(skill_focus_m.group(1))
        result["bonus_type"] = "skill"
        result["bonus_applies_to"] = "selected_skill"
        return result

    # --- No melee penalty for shooting ---
    if re.search(r"without\s+(?:taking\s+)?the\s+standard\s+.4\s+penalty", benefit, re.IGNORECASE):
        result["effect_type"] = "attack_modifier"
        result["removes_penalty"] = "no_shooting_into_melee_penalty"
        return result

    # --- Improved Precise Shot: ignore cover/concealment ---
    if re.search(r"ignore\s+.*?(?:cover|concealment)", benefit, re.IGNORECASE):
        result["effect_type"] = "attack_modifier"
        result["removes_penalty"] = "ignore_cover_concealment"
        result["limited_to"] = "ranged"
        return result

    # --- Feint as move action ---
    if re.search(r"feint\s+in\s+combat\s+as\s+a\s+move\s+action", benefit, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["grants_action"] = "feint_as_move"
        return result

    # --- Overrun: target may not avoid ---
    if re.search(r"target\s+may\s+not\s+choose\s+to\s+avoid", benefit, re.IGNORECASE):
        result["effect_type"] = "special_action"
        result["trigger"] = "on_overrun"
        result["removes_penalty"] = "target_cannot_avoid_overrun"
        return result

    # --- Combat Casting ---
    casting_m = re.search(
        r"\+(\d+)\s+bonus\s+on\s+Concentration\s+checks?",
        benefit,
        re.IGNORECASE,
    )
    if casting_m:
        result["effect_type"] = "skill_modifier"
        result["bonus_value"] = int(casting_m.group(1))
        result["bonus_type"] = "concentration"
        result["bonus_applies_to"] = "defensive_casting"
        return result

    # --- Far Shot: range increment ---
    if re.search(r"range\s+increment.*?(?:half|one.?third)", benefit, re.IGNORECASE):
        result["effect_type"] = "attack_modifier"
        result["bonus_type"] = "range_increment"
        return result

    # --- Eschew Materials ---
    if re.search(r"cast.*?without.*?material\s+component", benefit, re.IGNORECASE):
        result["effect_type"] = "special_action"
        result["removes_penalty"] = "no_cheap_material_component"
        return result

    # --- Improved Turning ---
    turning_m = re.search(
        r"turn(?:ing)?\s+(?:or\s+rebuke\s+)?.*?as\s+if\s+.*?(\d+)\s+level", benefit, re.IGNORECASE
    )
    if turning_m:
        result["effect_type"] = "class_feature_modifier"
        result["bonus_value"] = int(turning_m.group(1))
        result["bonus_type"] = "effective_turning_level"
        return result

    # --- No limit to cleave ---
    if re.search(r"no\s+limit\s+to.*?cleave", combined, re.IGNORECASE):
        result["effect_type"] = "action_economy"
        result["trigger"] = "on_kill"
        result["grants_action"] = "unlimited_cleave"
        return result

    # Fallback: if normal text describes what changes
    if normal.strip():
        result["replaces_normal"] = normal[:95].strip()

    return result


# ---------------------------------------------------------------------------
# Phase 1: Extract all feat entries from OCR pages
# ---------------------------------------------------------------------------

def extract_all_feats(source_dir: Path) -> Tuple[List[dict], List[dict]]:
    """Extract all feat entries from OCR pages.

    Concatenates all feat chapter pages into a single text blob to handle
    feats that span page boundaries, then extracts entries from the
    combined text.

    Returns:
        entries: list of parsed feat entry dicts
        page_gaps: list of gap records
    """
    page_gaps = []
    page_texts = []  # (page_num, text) pairs
    combined_text = ""
    page_boundary_offsets = []  # (offset, page_num) to track provenance

    for page_num in range(FEAT_PAGE_START, FEAT_PAGE_END + 1):
        page_file = source_dir / f"{page_num:04d}.txt"
        if not page_file.exists():
            page_gaps.append({
                "page": str(page_num),
                "reason": "page_file_not_found",
            })
            continue

        try:
            raw_text = page_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            page_gaps.append({
                "page": str(page_num),
                "reason": f"read_error: {e}",
            })
            continue

        cleaned = ocr_clean(raw_text)
        # Remove page numbers at top (standalone number on first lines)
        cleaned = re.sub(r"^\s*\d{1,3}\s*\n", "\n", cleaned)
        # Remove chapter footer noise
        cleaned = re.sub(r"CHAPTER\s+\d+:\s*\n?FEATS\s*$", "", cleaned, flags=re.MULTILINE)
        # Remove illustration credits
        cleaned = re.sub(r"Illus\.\s+by\s+[A-Z]\.\s+\w+\s*", "", cleaned)

        # Skip the feat reference table pages (Table 5-1: Feats, spanning 2 pages)
        # These are summary tables, not feat descriptions — they would pollute
        # adjacent feat entries with table row text and footnotes
        is_table_page = re.search(r"Table\s+5.+Feats", cleaned[:200])
        # Also detect continuation of the table (no feat headers, starts with
        # table rows like "Power Attack1 Str 13...")
        if not is_table_page:
            is_table_page = (
                re.match(r"\s*\w[\w\s]+\d\s+", cleaned.lstrip()[:50])
                and "Item Creation Feats" in cleaned
                and "Metamagic Feats" in cleaned
            )
        if is_table_page:
            log.debug("Skipping table page %d", page_num)
            continue

        page_boundary_offsets.append((len(combined_text), page_num))
        combined_text += cleaned + "\n"

    if not combined_text.strip():
        log.warning("No text found in feat pages")
        return [], page_gaps

    # Extract all feat entries from combined text
    entries = find_feat_entries(combined_text)

    # Assign source page based on position in combined text
    for entry in entries:
        entry_start = combined_text.find(entry.get("full_text", "")[:50])
        if entry_start == -1:
            # Fallback: use the page from the header match
            entry["source_page"] = ""
            continue
        # Find which page this offset belongs to
        page = ""
        for offset, pnum in reversed(page_boundary_offsets):
            if entry_start >= offset:
                page = str(pnum)
                break
        entry["source_page"] = page

    log.info("Extracted %d raw feat entries from pages %d-%d",
             len(entries), FEAT_PAGE_START, FEAT_PAGE_END)

    return entries, page_gaps


# ---------------------------------------------------------------------------
# Phase 2: Build templates and resolve prerequisite chains
# ---------------------------------------------------------------------------

def build_templates(
    entries: List[dict],
) -> Tuple[List[MechanicalFeatTemplate], List[dict], List[dict]]:
    """Convert parsed entries into MechanicalFeatTemplates.

    Two-pass approach:
      1. Assign template IDs and build name->ID mapping
      2. Resolve prerequisite feat references

    Returns:
        templates: list of MechanicalFeatTemplate
        provenance: list of provenance records
        gaps: list of gap records
    """
    # --- Pass 1: Assign IDs ---
    name_to_id: Dict[str, str] = {}
    template_data: List[dict] = []
    provenance = []
    gaps = []

    # De-duplicate: some feats span pages and may appear twice
    seen_names = set()

    for i, entry in enumerate(entries):
        name = entry["name"].strip()

        # Skip the format template example from page 89
        if name == "FEAT NAME":
            continue

        # Skip duplicate entries (feat continued from previous page)
        if name in seen_names:
            # Merge: append benefit/normal/special text to existing entry
            for td in template_data:
                if td["_name"] == name:
                    if entry["benefit"]:
                        td["_entry"]["benefit"] += " " + entry["benefit"]
                    if entry["normal"]:
                        td["_entry"]["normal"] += " " + entry["normal"]
                    if entry["special"]:
                        td["_entry"]["special"] += " " + entry["special"]
                    break
            continue

        seen_names.add(name)
        template_id = f"FEAT_{len(template_data) + 1:03d}"
        name_to_id[name] = template_id

        template_data.append({
            "_name": name,
            "_entry": entry,
            "template_id": template_id,
        })

        provenance.append({
            "template_id": template_id,
            "original_name": name,
            "page": entry.get("source_page", ""),
            "feat_type_raw": entry.get("feat_type_raw", ""),
        })

    log.info("Assigned %d template IDs (after dedup)", len(template_data))

    # --- Pass 2: Build templates with resolved prereq references ---
    templates = []

    for td in template_data:
        entry = td["_entry"]
        template_id = td["template_id"]
        name = td["_name"]

        # Parse prerequisites
        prereqs = parse_prerequisites(entry.get("prerequisite", ""))

        # Resolve feat name references to template IDs
        resolved_feat_refs = []
        for feat_name in prereqs["feat_names"]:
            ref_id = name_to_id.get(feat_name)
            if ref_id is None:
                # Try case-insensitive match
                for known_name, known_id in name_to_id.items():
                    if known_name.lower() == feat_name.lower():
                        ref_id = known_id
                        break
            if ref_id is None:
                # Try partial match for "Improved Two-Weapon Fighting" -> "Two-Weapon Fighting"
                for known_name, known_id in name_to_id.items():
                    if feat_name.lower() in known_name.lower() or known_name.lower() in feat_name.lower():
                        ref_id = known_id
                        break
            if ref_id:
                resolved_feat_refs.append(ref_id)
            else:
                gaps.append({
                    "template_id": template_id,
                    "reason": "unresolved_prereq_feat",
                    "feat_name": feat_name,
                    "page": entry.get("source_page", ""),
                })

        # Classify effect
        effects = classify_feat_effect(entry)

        # Determine feat type
        feat_type = FEAT_TYPE_MAP.get(
            entry.get("feat_type_raw", "GENERAL"),
            "general",
        )

        try:
            template = MechanicalFeatTemplate(
                template_id=template_id,
                feat_type=feat_type,
                prereq_ability_scores=prereqs["ability_scores"],
                prereq_bab=prereqs["bab"],
                prereq_feat_refs=tuple(resolved_feat_refs),
                prereq_class_features=tuple(prereqs["class_features"]),
                prereq_caster_level=prereqs["caster_level"],
                prereq_other=tuple(prereqs["other"]),
                effect_type=effects["effect_type"],
                bonus_value=effects["bonus_value"],
                bonus_type=effects["bonus_type"],
                bonus_applies_to=effects["bonus_applies_to"],
                trigger=effects["trigger"],
                replaces_normal=effects["replaces_normal"],
                grants_action=effects["grants_action"],
                removes_penalty=effects["removes_penalty"],
                stacks_with=effects["stacks_with"],
                limited_to=effects["limited_to"],
                fighter_bonus_eligible=effects["fighter_bonus_eligible"],
                can_take_multiple=effects["can_take_multiple"],
                effects_stack=effects["effects_stack"],
                metamagic_slot_increase=effects["metamagic_slot_increase"],
                source_page=entry.get("source_page", ""),
                source_id=SOURCE_ID,
            )
            templates.append(template)
        except Exception as e:
            gaps.append({
                "template_id": template_id,
                "reason": f"template_creation_failed: {e}",
                "page": entry.get("source_page", ""),
            })
            log.warning("Failed to create template %s (%s): %s", template_id, name, e)

    log.info("Built %d templates, %d gaps", len(templates), len(gaps))
    return templates, provenance, gaps


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def template_to_dict(t: MechanicalFeatTemplate) -> dict:
    """Convert template to JSON-serializable dict."""
    d = {}
    for f in dc_fields(t):
        val = getattr(t, f.name)
        if isinstance(val, tuple):
            val = list(val)
        d[f.name] = val
    return d


# ---------------------------------------------------------------------------
# Main extraction pipeline
# ---------------------------------------------------------------------------

def run_extraction(source_dir: str, output_dir: str):
    """Run the full feat extraction pipeline."""
    source_path = Path(source_dir)
    output_path = Path(output_dir)

    if not source_path.exists():
        log.error("Source directory not found: %s", source_path)
        sys.exit(1)

    # Phase 1: Extract raw entries
    entries, page_gaps = extract_all_feats(source_path)

    # Phase 2: Build templates with resolved prerequisites
    templates, provenance, build_gaps = build_templates(entries)

    all_gaps = page_gaps + build_gaps

    # --- Output: feats.json (IP-clean) ---
    feats_out = output_path / "content_pack" / "feats.json"
    feats_out.parent.mkdir(parents=True, exist_ok=True)

    feats_data = {
        "schema_version": "1.0.0",
        "source_id": SOURCE_ID,
        "extraction_version": "WO-CONTENT-EXTRACT-003",
        "feat_count": len(templates),
        "feats": [template_to_dict(t) for t in templates],
    }

    with open(feats_out, "w", encoding="utf-8") as f:
        json.dump(feats_data, f, indent=2, ensure_ascii=False)
    log.info("Wrote %s (%d feats)", feats_out, len(templates))

    # --- Output: feat_provenance.json (INTERNAL ONLY) ---
    tools_data_dir = Path(__file__).parent / "data"
    tools_data_dir.mkdir(parents=True, exist_ok=True)
    prov_out = tools_data_dir / "feat_provenance.json"

    prov_data = {
        "schema_version": "1.0.0",
        "source_id": SOURCE_ID,
        "note": "INTERNAL ONLY — contains original feat names for provenance tracking",
        "name_to_id": {p["original_name"]: p["template_id"] for p in provenance},
        "entries": provenance,
    }

    with open(prov_out, "w", encoding="utf-8") as f:
        json.dump(prov_data, f, indent=2, ensure_ascii=False)
    log.info("Wrote %s (%d entries)", prov_out, len(provenance))

    # --- Output: feat_extraction_gaps.json ---
    gaps_out = tools_data_dir / "feat_extraction_gaps.json"

    gaps_data = {
        "schema_version": "1.0.0",
        "source_id": SOURCE_ID,
        "gap_count": len(all_gaps),
        "gaps": all_gaps,
    }

    with open(gaps_out, "w", encoding="utf-8") as f:
        json.dump(gaps_data, f, indent=2, ensure_ascii=False)
    log.info("Wrote %s (%d gaps)", gaps_out, len(all_gaps))

    return templates, provenance, all_gaps


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract feat mechanics from PHB OCR text"
    )
    parser.add_argument(
        "--source-dir",
        default="sources/text/681f92bc94ff",
        help="Directory containing OCR page text files",
    )
    parser.add_argument(
        "--output-dir",
        default="aidm/data",
        help="Base output directory",
    )
    args = parser.parse_args()

    # Resolve paths relative to project root
    project_root = Path(__file__).parent.parent
    source_dir = project_root / args.source_dir
    output_dir = project_root / args.output_dir

    run_extraction(str(source_dir), str(output_dir))


if __name__ == "__main__":
    main()
