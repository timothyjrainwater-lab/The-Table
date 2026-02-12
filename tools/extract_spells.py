#!/usr/bin/env python3
"""Spell extraction pipeline — OCR text to mechanical templates.

Reads OCR text files from the PHB spell chapter, parses spell entries,
strips all skin (names, prose, flavor), and outputs structured mechanical
templates conforming to the content pack schema.

WO-CONTENT-EXTRACT-001: Mechanical Extraction Pipeline — Spells

Usage:
    python tools/extract_spells.py

Output:
    aidm/data/content_pack/spells.json     — Extracted spell database
    tools/data/spell_provenance.json       — Name-to-template mapping (internal)
    tools/data/extraction_gaps.json        — Skipped/flagged spells
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from aidm.schemas.content_pack import MechanicalSpellTemplate


# ==========================================================================
# Constants
# ==========================================================================

SOURCE_DIR = PROJECT_ROOT / "sources" / "text" / "681f92bc94ff"
SOURCE_ID = "681f92bc94ff"
START_PAGE = 197
END_PAGE = 304

SCHOOL_NAMES = {
    "Abjuration", "Conjuration", "Divination", "Enchantment",
    "Evocation", "Illusion", "Necromancy", "Transmutation", "Universal",
}

SCHOOL_RE = re.compile(
    r"^(Abjuration|Conjuration|Divination|Enchantment|Evocation|"
    r"Illusion|Necromancy|Transmutation|Universal)"
    r"(?:\s*\(([^)]+)\))?"       # optional subschool
    r"(?:\s*\[([^\]]+)\])?"      # optional descriptor
    r"\s*$",
)

HEADER_FIELDS = [
    "Level:", "Components:", "Casting Time:", "Range:",
    "Target:", "Targets:", "Area:", "Effect:",
    "Duration:", "Saving Throw:", "Spell Resistance:",
    "Target or Area:", "Target, Effect, or Area:",
    "Target/Area:",
]

HEADER_RE = re.compile(
    r"^(Level|Components|Casting Time|Range|"
    r"Target(?:s| or Area| or Effect|, Effect, or Area|/Area)?|"
    r"Area|Effect|Duration|Saving Throw|Spell Resistance):\s*(.*)",
)

# Range patterns
RANGE_CLOSE_RE = re.compile(
    r"Close\s*\(25\s*ft\.?\s*\+\s*5\s*ft\.?\s*/\s*2\s*levels?\)", re.I
)
RANGE_MEDIUM_RE = re.compile(
    r"Medium\s*\(100\s*ft\.?\s*\+\s*10\s*ft\.?\s*/\s*level\)", re.I
)
RANGE_LONG_RE = re.compile(
    r"Long\s*\(400\s*ft\.?\s*\+\s*40\s*ft\.?\s*/\s*level\)", re.I
)
RANGE_FIXED_RE = re.compile(r"(\d+)\s*ft\.?")

# Duration patterns
DURATION_PER_LEVEL_RE = re.compile(
    r"(\d+)\s*(round|min|hour|day)s?\.?\s*/\s*level", re.I
)

# Damage patterns
DAMAGE_DICE_RE = re.compile(r"(\d+d\d+(?:\s*\+\s*\d+)?)")
DAMAGE_TYPE_RE = re.compile(
    r"(\d+d\d+(?:\s*\+\s*\d+)?)\s*(?:points?\s*of\s*)?"
    r"(fire|cold|acid|electricity|sonic|force|positive energy|negative energy|"
    r"nonlethal|divine|energy)\s*damage",
    re.I,
)
DAMAGE_PER_LEVEL_RE = re.compile(
    r"(\d+d\d+)\s*(?:points?\s*of\s*\w+\s*damage\s*)?per\s*(?:caster\s*)?level"
    r"(?:\s*\(maximum\s*(\d+d\d+)\))?",
    re.I,
)
DAMAGE_PER_LEVEL_ALT_RE = re.compile(
    r"(\d+d\d+)\s*per\s*(?:caster\s*)?level.*?max(?:imum)?\s*(?:of\s*)?(\d+d\d+)",
    re.I,
)

# Healing patterns
HEALING_RE = re.compile(
    r"(?:cures?|heals?|restores?)\s*(\d+d\d+(?:\s*\+\s*\d+)?)", re.I
)

# AoE patterns
AOE_RADIUS_RE = re.compile(
    r"(\d+)-?\s*ft\.?\s*-?\s*(?:radius\s*)?(burst|spread|emanation|cylinder|sphere)",
    re.I,
)
AOE_CONE_RE = re.compile(r"cone", re.I)
AOE_LINE_RE = re.compile(r"(\d+)-?\s*ft\.?\s*(?:-?\s*)?line", re.I)

# Attack roll patterns
RANGED_TOUCH_RE = re.compile(r"ranged\s*touch\s*attack", re.I)
MELEE_TOUCH_RE = re.compile(r"melee\s*touch\s*attack", re.I)

# Condition patterns
KNOWN_CONDITIONS = [
    "blinded", "confused", "cowering", "dazed", "dazzled", "deafened",
    "disabled", "entangled", "exhausted", "fascinated", "fatigued",
    "flat-footed", "frightened", "grappling", "helpless", "incorporeal",
    "invisible", "nauseated", "panicked", "paralyzed", "petrified",
    "pinned", "prone", "shaken", "sickened", "stable", "staggered",
    "stunned", "turned", "unconscious",
]

# "As X except" pattern
INHERITS_RE = re.compile(
    r"(?:This spell )?(?:functions?|works?)\s*(?:like|as)\s+"
    r"([\w\s'/,]+?)(?:\s*,|\s+except|\s+but|\s*\.)",
    re.I,
)

# Class abbreviation patterns
CLASS_LEVEL_RE = re.compile(r"([\w/]+)\s+(\d)")

# Chapter footer to strip
CHAPTER_FOOTER_RE = re.compile(r"\s*CHAPTER\s+11:\s*\n\s*SPELLS\s*$", re.M)

# OCR artifacts
OCR_ARTIFACT_RE = re.compile(r"/\w+\d")

# Level line: "Level: Clr 2, Sor/Wiz 1"
LEVEL_LINE_RE = re.compile(r"Level:\s*(.*)", re.I)

# Component flags
COMP_V_RE = re.compile(r"\bV\b")
COMP_S_RE = re.compile(r"\bS\b")
COMP_M_RE = re.compile(r"\bM\b(?!\s*/)")
COMP_M_DF_RE = re.compile(r"\bM/DF\b")
COMP_F_RE = re.compile(r"\bF\b(?!\s*/)")
COMP_F_DF_RE = re.compile(r"\bF/DF\b")
COMP_DF_RE = re.compile(r"\bDF\b")
COMP_XP_RE = re.compile(r"\bXP?\b|\bX\b")


# ==========================================================================
# Data Classes
# ==========================================================================

@dataclass
class RawSpellEntry:
    """A raw spell entry split from OCR text."""
    name: str
    raw_text: str
    source_page: int
    source_id: str = SOURCE_ID


@dataclass
class ParsedSpell:
    """Fully parsed spell record."""
    name: str
    source_page: int
    source_id: str

    school: str = ""
    subschool: Optional[str] = None
    descriptors: Tuple[str, ...] = ()
    class_levels: List[Tuple[str, int]] = field(default_factory=list)
    min_level: int = 0

    verbal: bool = False
    somatic: bool = False
    material: bool = False
    focus: bool = False
    divine_focus: bool = False
    xp_cost: bool = False

    casting_time_raw: str = ""
    range_raw: str = ""
    range_category: str = ""
    target_raw: Optional[str] = None
    effect_raw: Optional[str] = None
    area_raw: Optional[str] = None
    duration_raw: str = ""
    saving_throw_raw: str = ""
    spell_resistance_raw: str = ""
    body_text: str = ""

    inherits_from: Optional[str] = None

    # Extracted mechanical fields
    target_type: str = "single"
    range_formula: Optional[str] = None
    aoe_shape: Optional[str] = None
    aoe_radius_ft: Optional[int] = None
    effect_type: str = "utility"
    damage_formula: Optional[str] = None
    damage_type: Optional[str] = None
    healing_formula: Optional[str] = None
    save_type: Optional[str] = None
    save_effect: Optional[str] = None
    spell_resistance: bool = False
    requires_attack_roll: bool = False
    auto_hit: bool = False
    casting_time: str = "standard"
    duration_formula: Optional[str] = None
    concentration: bool = False
    dismissible: bool = False
    conditions_applied: Tuple[str, ...] = ()
    conditions_duration: Optional[str] = None
    combat_role_tags: Tuple[str, ...] = ()
    delivery_mode: str = "instantaneous"

    # Flags
    parse_warnings: List[str] = field(default_factory=list)


@dataclass
class ExtractionGap:
    """A spell that was skipped or flagged."""
    name: str
    source_page: int
    reason: str
    details: str = ""


# ==========================================================================
# Stage 1: OCR Loading
# ==========================================================================

def load_pages(source_dir: Path, start: int, end: int) -> List[Tuple[int, str]]:
    """Load OCR pages, returning (page_num, text) pairs."""
    pages = []
    for page_num in range(start, end + 1):
        page_file = source_dir / f"{page_num:04d}.txt"
        if page_file.exists():
            text = page_file.read_text(encoding="utf-8", errors="replace")
            pages.append((page_num, text))
    return pages


def clean_page(text: str) -> str:
    """Strip page header (page number) and chapter footer."""
    # Remove chapter footer
    text = CHAPTER_FOOTER_RE.sub("", text)
    # Remove leading blank lines and page number
    lines = text.split("\n")
    cleaned = []
    skipped_header = False
    for line in lines:
        if not skipped_header:
            stripped = line.strip()
            if stripped == "" or stripped.isdigit():
                continue
            skipped_header = True
        cleaned.append(line)
    return "\n".join(cleaned)


def rejoin_hyphens(text: str) -> str:
    """Rejoin words broken by line-end hyphens."""
    return re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)


def concatenate_pages(pages: List[Tuple[int, str]]) -> str:
    """Concatenate cleaned pages with page markers."""
    parts = []
    for page_num, text in pages:
        cleaned = clean_page(text)
        parts.append(f"<<PAGE:{page_num}>>")
        parts.append(cleaned)
    return "\n".join(parts)


# ==========================================================================
# Stage 2: Spell Splitting
# ==========================================================================

def is_school_line(line: str) -> bool:
    """Check if a line starts with a known spell school."""
    stripped = line.strip()
    for school in SCHOOL_NAMES:
        if stripped.startswith(school):
            return True
    return False


def is_spell_name_candidate(line: str) -> bool:
    """Check if a line looks like a spell name (Title Case, standalone)."""
    stripped = line.strip()
    if not stripped or len(stripped) < 2:
        return False
    # Must not be a header field
    for hf in HEADER_FIELDS:
        if stripped.startswith(hf):
            return False
    # Must not start with common prose indicators
    if stripped[0].islower():
        return False
    # Must not be all caps (like "SPELLS")
    if stripped.isupper() and len(stripped) > 3:
        return False
    # Must not be too long (spell names are typically short)
    if len(stripped) > 60:
        return False
    # Must contain at least one uppercase start word
    words = stripped.split()
    if not words:
        return False
    # First word must start uppercase
    if not words[0][0].isupper():
        return False
    # Check it looks like a title (most words capitalized)
    cap_count = sum(1 for w in words if w[0].isupper())
    # Allow minor words to be lowercase
    if cap_count < len(words) * 0.4:
        return False
    # Should not end with a period (prose sentence)
    if stripped.endswith("."):
        return False
    # Should not contain common prose starters
    if any(stripped.startswith(x) for x in [
        "If ", "The ", "This ", "A ", "An ", "You ", "Each ",
        "Any ", "All ", "When ", "Note ", "For ", "In ",
    ]):
        return False
    return True


def split_spells(text: str) -> List[RawSpellEntry]:
    """Split concatenated OCR text into individual spell entries."""
    lines = text.split("\n")
    entries: List[RawSpellEntry] = []
    current_page = START_PAGE
    current_name: Optional[str] = None
    current_text_lines: List[str] = []
    current_start_page = START_PAGE
    # Track if we've found the first real spell entry (skip preamble)
    found_first_spell = False

    i = 0
    while i < len(lines):
        line = lines[i]

        # Update page tracking
        page_match = re.match(r"<<PAGE:(\d+)>>", line)
        if page_match:
            current_page = int(page_match.group(1))
            i += 1
            continue

        stripped = line.strip()

        # Check for spell boundary: name line followed by school line
        if is_spell_name_candidate(stripped):
            # Look ahead for school line (may be next non-empty line)
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines):
                next_line = lines[j].strip()
                # Handle multi-line school (e.g., wrapped descriptors)
                # Also check if the line after page marker is a school
                if re.match(r"<<PAGE:(\d+)>>", next_line):
                    k = j + 1
                    while k < len(lines) and lines[k].strip() == "":
                        k += 1
                    if k < len(lines):
                        next_line = lines[k].strip()

                if is_school_line(next_line):
                    # Found a spell boundary
                    if current_name is not None:
                        body = "\n".join(current_text_lines).strip()
                        if body:
                            entries.append(RawSpellEntry(
                                name=current_name,
                                raw_text=body,
                                source_page=current_start_page,
                            ))
                    current_name = stripped
                    current_text_lines = []
                    current_start_page = current_page
                    found_first_spell = True
                    i += 1
                    continue

        if found_first_spell and current_name is not None:
            # Skip page markers in body
            if not re.match(r"<<PAGE:(\d+)>>", line):
                current_text_lines.append(line)
        i += 1

    # Don't forget the last spell
    if current_name is not None and current_text_lines:
        body = "\n".join(current_text_lines).strip()
        if body:
            entries.append(RawSpellEntry(
                name=current_name,
                raw_text=body,
                source_page=current_start_page,
            ))

    return entries


# ==========================================================================
# Stage 3: Field Parsing
# ==========================================================================

def parse_school_line(text: str) -> Tuple[str, Optional[str], Tuple[str, ...]]:
    """Parse school/subschool/descriptor from the school line."""
    # May span multiple lines — take the first part
    line = text.strip().split("\n")[0].strip()
    # Try to match the full school pattern
    m = SCHOOL_RE.match(line)
    if m:
        school = m.group(1).lower()
        subschool = m.group(2).lower().strip() if m.group(2) else None
        descriptors = tuple(
            d.strip().lower()
            for d in m.group(3).split(",")
        ) if m.group(3) else ()
        return school, subschool, descriptors
    # Fallback: just get the school name
    for s in SCHOOL_NAMES:
        if line.startswith(s):
            school = s.lower()
            # Try to extract subschool and descriptors
            rest = line[len(s):].strip()
            subschool = None
            descriptors = ()
            paren_m = re.search(r"\(([^)]+)\)", rest)
            if paren_m:
                subschool = paren_m.group(1).strip().lower()
            bracket_m = re.search(r"\[([^\]]+)\]", rest)
            if bracket_m:
                raw = bracket_m.group(1)
                # Handle "see text" and similar
                if raw.lower() != "see text":
                    descriptors = tuple(
                        d.strip().lower() for d in raw.split(",")
                    )
            return school, subschool, descriptors
    return "universal", None, ()


def parse_class_levels(text: str) -> List[Tuple[str, int]]:
    """Parse class/level pairs from the Level: line value."""
    pairs = []
    for m in CLASS_LEVEL_RE.finditer(text):
        cls_abbrev = m.group(1).lower().replace("/", "_")
        level = int(m.group(2))
        pairs.append((cls_abbrev, level))
    return pairs


def parse_components(text: str) -> Dict[str, bool]:
    """Parse component flags from Components: line value."""
    return {
        "verbal": bool(COMP_V_RE.search(text)),
        "somatic": bool(COMP_S_RE.search(text)),
        "material": bool(COMP_M_RE.search(text) or COMP_M_DF_RE.search(text)),
        "focus": bool(COMP_F_RE.search(text) or COMP_F_DF_RE.search(text)),
        "divine_focus": bool(COMP_DF_RE.search(text) or COMP_M_DF_RE.search(text) or COMP_F_DF_RE.search(text)),
        "xp_cost": bool(COMP_XP_RE.search(text)),
    }


def parse_range(text: str) -> Tuple[str, Optional[str]]:
    """Parse range category and formula from Range: line value."""
    t = text.strip()
    if t.lower() == "personal":
        return "personal", "personal"
    if t.lower().startswith("touch"):
        return "touch", "touch"
    if t.lower() == "unlimited":
        return "unlimited", "unlimited"
    if t.lower().startswith("see text"):
        return "see_text", None
    if RANGE_CLOSE_RE.search(t):
        return "close", "close"
    if RANGE_MEDIUM_RE.search(t):
        return "medium", "medium"
    if RANGE_LONG_RE.search(t):
        return "long", "long"
    # Fixed distance
    m = RANGE_FIXED_RE.search(t)
    if m:
        return "fixed", m.group(1)
    # "Personal or touch"
    if "personal" in t.lower() and "touch" in t.lower():
        return "personal_or_touch", "touch"
    return "unknown", None


def parse_duration(text: str) -> Tuple[Optional[str], bool, bool]:
    """Parse duration formula, concentration flag, dismissible flag."""
    t = text.strip()
    conc = "concentration" in t.lower()
    dismiss = "(D)" in t or "(d)" in t or "dismissible" in t.lower()

    if t.lower().startswith("instantaneous"):
        return "instantaneous", False, False
    if t.lower().startswith("permanent"):
        return "permanent", False, dismiss
    if t.lower() == "see text":
        return "see_text", False, False

    m = DURATION_PER_LEVEL_RE.search(t)
    if m:
        num = m.group(1)
        unit = m.group(2).lower()
        if unit.startswith("min"):
            unit = "min"
        elif unit.startswith("hour"):
            unit = "hour"
        elif unit.startswith("day"):
            unit = "day"
        else:
            unit = "round"
        return f"{num}_{unit}_per_CL", conc, dismiss

    # Fixed duration: "7 rounds", "24 hours", etc.
    fixed_m = re.match(r"(\d+)\s*(round|minute|hour|day)s?", t, re.I)
    if fixed_m:
        num = fixed_m.group(1)
        unit = fixed_m.group(2).lower()
        if unit.startswith("minute"):
            unit = "min"
        return f"{num}_{unit}s", conc, dismiss

    # "1d4+1 rounds" style
    dice_m = re.match(r"(\d+d\d+(?:\+\d+)?)\s*(round|minute|hour)s?", t, re.I)
    if dice_m:
        return f"{dice_m.group(1)}_{dice_m.group(2).lower()}s", conc, dismiss

    # "One day/level"
    one_per_m = re.match(r"One\s*(round|day|hour|minute|min)\.?\s*/\s*level", t, re.I)
    if one_per_m:
        unit = one_per_m.group(1).lower()
        if unit.startswith("min"):
            unit = "min"
        return f"1_{unit}_per_CL", conc, dismiss

    if conc:
        return "concentration", True, dismiss

    return "see_text", conc, dismiss


def parse_save(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse save type and effect from Saving Throw: line value."""
    t = text.strip().lower()
    if t.startswith("none"):
        return None, None

    save_type = None
    save_effect = None

    if "fortitude" in t or "fort" in t:
        save_type = "fortitude"
    elif "reflex" in t:
        save_type = "reflex"
    elif "will" in t:
        save_type = "will"

    if "half" in t:
        save_effect = "half"
    elif "negates" in t or "negate" in t:
        save_effect = "negates"
    elif "partial" in t:
        save_effect = "partial"
    elif save_type:
        save_effect = "see_text"

    return save_type, save_effect


def parse_sr(text: str) -> bool:
    """Parse spell resistance from Spell Resistance: line value."""
    t = text.strip().lower()
    return t.startswith("yes")


def parse_casting_time(text: str) -> str:
    """Normalize casting time to enum-like string."""
    t = text.strip().lower()
    if "1 standard action" in t:
        return "standard"
    if "1 full-round action" in t or "1 full round" in t:
        return "full_round"
    if "1 swift action" in t:
        return "swift"
    if "1 immediate action" in t:
        return "immediate"
    if "1 free action" in t:
        return "free"
    m = re.match(r"(\d+)\s*round", t)
    if m:
        n = m.group(1)
        return f"{n}_rounds" if int(n) > 1 else "1_round"
    m = re.match(r"(\d+)\s*minute", t)
    if m:
        return f"{m.group(1)}_min"
    m = re.match(r"(\d+)\s*hour", t)
    if m:
        return f"{m.group(1)}_hour"
    if "see text" in t:
        return "see_text"
    return "standard"


def parse_header_fields(raw_text: str) -> Dict[str, str]:
    """Extract header fields from raw spell text.

    Header fields continue until a blank line or body text begins.
    Multi-line values are joined.
    """
    lines = raw_text.split("\n")
    fields: Dict[str, str] = {}
    current_field: Optional[str] = None
    current_value_parts: List[str] = []
    body_start = 0

    for idx, line in enumerate(lines):
        stripped = line.strip()

        # Check for header field
        m = HEADER_RE.match(stripped)
        if m:
            # Save previous field
            if current_field:
                fields[current_field] = " ".join(current_value_parts).strip()
            current_field = m.group(1)
            current_value_parts = [m.group(2)]
            body_start = idx + 1
            continue

        # If we have a current field and this looks like a continuation
        if current_field and stripped and not stripped == "":
            # Check if it's a new header field
            if any(stripped.startswith(hf) for hf in HEADER_FIELDS):
                m2 = HEADER_RE.match(stripped)
                if m2:
                    fields[current_field] = " ".join(current_value_parts).strip()
                    current_field = m2.group(1)
                    current_value_parts = [m2.group(2)]
                    body_start = idx + 1
                    continue
            # Continuation of current field
            current_value_parts.append(stripped)
            body_start = idx + 1
        elif current_field and stripped == "":
            # Blank line — end of headers
            fields[current_field] = " ".join(current_value_parts).strip()
            current_field = None
            body_start = idx + 1
            break

    # Save last field
    if current_field:
        fields[current_field] = " ".join(current_value_parts).strip()

    # Body text is everything after headers
    body_lines = lines[body_start:]
    fields["__body__"] = "\n".join(body_lines).strip()

    return fields


def extract_damage_info(
    body: str, area_raw: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    """Extract damage formula and type from body text."""
    # Try per-level scaling first
    m = DAMAGE_PER_LEVEL_RE.search(body)
    if m:
        per_level = m.group(1)
        maximum = m.group(2) if m.group(2) else None
        if maximum:
            return f"{per_level}_per_CL_max_{maximum}", None
        return f"{per_level}_per_CL", None

    m = DAMAGE_PER_LEVEL_ALT_RE.search(body)
    if m:
        return f"{m.group(1)}_per_CL_max_{m.group(2)}", None

    # Try typed damage
    m = DAMAGE_TYPE_RE.search(body)
    if m:
        formula = m.group(1).replace(" ", "")
        dtype = m.group(2).lower()
        if dtype == "positive energy":
            dtype = "positive"
        elif dtype == "negative energy":
            dtype = "negative"
        return formula, dtype

    # Try plain damage dice near "damage" keyword
    dam_m = re.search(r"(\d+d\d+(?:\s*\+\s*\d+)?)\s*(?:points?\s*(?:of\s*)?)?damage", body, re.I)
    if dam_m:
        return dam_m.group(1).replace(" ", ""), None

    return None, None


def extract_healing_info(body: str) -> Optional[str]:
    """Extract healing formula from body text."""
    m = HEALING_RE.search(body)
    if m:
        return m.group(1).replace(" ", "")
    return None


def extract_aoe_info(area_raw: Optional[str], body: str) -> Tuple[Optional[str], Optional[int]]:
    """Extract AoE shape and radius."""
    search_text = (area_raw or "") + " " + body

    m = AOE_RADIUS_RE.search(search_text)
    if m:
        radius = int(m.group(1))
        shape = m.group(2).lower()
        return shape, radius

    m = AOE_LINE_RE.search(search_text)
    if m:
        return "line", int(m.group(1))

    if AOE_CONE_RE.search(area_raw or ""):
        return "cone", None

    return None, None


def extract_conditions(body: str) -> Tuple[str, ...]:
    """Extract conditions from body text."""
    found = []
    body_lower = body.lower()
    for cond in KNOWN_CONDITIONS:
        if cond in body_lower:
            # Check it's not negated or conditional
            found.append(cond)
    return tuple(sorted(set(found)))


def infer_target_type(
    range_cat: str,
    area_raw: Optional[str],
    target_raw: Optional[str],
    body: str,
    aoe_shape: Optional[str],
    req_attack: bool,
) -> str:
    """Infer target type from parsed fields."""
    if range_cat == "personal":
        return "self"
    if RANGED_TOUCH_RE.search(body):
        return "ray"
    if range_cat == "touch" and not aoe_shape:
        return "touch"
    if aoe_shape or (area_raw and area_raw.strip()):
        return "area"
    if req_attack and "ray" in body.lower():
        return "ray"
    return "single"


def infer_effect_type(parsed: ParsedSpell) -> str:
    """Infer the primary effect type."""
    if parsed.healing_formula:
        return "healing"
    if parsed.damage_formula:
        return "damage"
    body_lower = parsed.body_text.lower()
    if parsed.conditions_applied:
        # Check if it's a beneficial condition (buff) or harmful (debuff)
        if parsed.save_type and parsed.save_effect in ("negates", "partial"):
            return "debuff"
        if "harmless" in parsed.saving_throw_raw.lower():
            return "buff"
        if parsed.range_category in ("personal", "touch"):
            # Check if it targets allies
            target = (parsed.target_raw or "").lower()
            if "you" in target or "creature touched" in target or "ally" in target:
                return "buff"
            return "debuff"
        return "debuff"
    # Check for buff keywords
    buff_kw = ["bonus", "gain", "increase", "improve", "enhance", "protect"]
    debuff_kw = ["penalty", "reduce", "decrease", "weaken"]
    buff_score = sum(1 for kw in buff_kw if kw in body_lower)
    debuff_score = sum(1 for kw in debuff_kw if kw in body_lower)
    if buff_score > debuff_score and buff_score >= 2:
        return "buff"
    if debuff_score > buff_score and debuff_score >= 2:
        return "debuff"
    return "utility"


def infer_delivery_mode(parsed: ParsedSpell) -> str:
    """Infer how the spell is delivered."""
    if parsed.aoe_shape == "cone":
        return "cone"
    if parsed.aoe_shape == "line":
        return "line"
    if parsed.aoe_shape in ("burst", "spread", "sphere", "cylinder"):
        return "burst_from_point"
    if parsed.aoe_shape == "emanation":
        return "emanation"
    if parsed.target_type == "ray":
        return "ray"
    if parsed.target_type == "touch":
        return "touch"
    if parsed.target_type == "self":
        return "self"
    if parsed.requires_attack_roll:
        return "projectile"
    return "instantaneous"


def infer_combat_role_tags(parsed: ParsedSpell) -> Tuple[str, ...]:
    """Infer combat role tags."""
    tags = []
    if parsed.effect_type == "damage":
        if parsed.target_type == "area":
            tags.append("area_damage")
        else:
            tags.append("single_target_damage")
    if parsed.effect_type == "healing":
        tags.append("healing")
    if parsed.effect_type == "buff":
        tags.append("buff")
    if parsed.effect_type == "debuff":
        tags.append("debuff")
    if parsed.aoe_shape and parsed.effect_type != "damage":
        tags.append("battlefield_control")
    if parsed.effect_type == "utility":
        tags.append("utility")
    if not tags:
        tags.append("utility")
    return tuple(sorted(tags))


def parse_spell_entry(entry: RawSpellEntry) -> ParsedSpell:
    """Parse a raw spell entry into structured fields."""
    parsed = ParsedSpell(
        name=entry.name,
        source_page=entry.source_page,
        source_id=entry.source_id,
    )

    raw = entry.raw_text

    # Parse school line (first line of raw_text)
    lines = raw.split("\n")
    school_line = ""
    body_start_idx = 0
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped and is_school_line(stripped):
            school_line = stripped
            # Check for multi-line school
            next_idx = idx + 1
            while next_idx < len(lines):
                next_stripped = lines[next_idx].strip()
                if next_stripped and not any(
                    next_stripped.startswith(hf) for hf in HEADER_FIELDS
                ):
                    # Could be continuation of school line (e.g., "[Mind-Affecting]")
                    if next_stripped.startswith("[") or next_stripped.startswith("("):
                        school_line += " " + next_stripped
                        next_idx += 1
                        continue
                break
            body_start_idx = next_idx
            break
        body_start_idx = idx + 1

    parsed.school, parsed.subschool, parsed.descriptors = parse_school_line(school_line)

    # Parse header fields from remaining text
    remaining = "\n".join(lines[body_start_idx:])
    fields = parse_header_fields(remaining)

    # Level
    if "Level" in fields:
        parsed.class_levels = parse_class_levels(fields["Level"])
        if parsed.class_levels:
            parsed.min_level = min(lvl for _, lvl in parsed.class_levels)

    # Components
    if "Components" in fields:
        comps = parse_components(fields["Components"])
        parsed.verbal = comps["verbal"]
        parsed.somatic = comps["somatic"]
        parsed.material = comps["material"]
        parsed.focus = comps["focus"]
        parsed.divine_focus = comps["divine_focus"]
        parsed.xp_cost = comps["xp_cost"]

    # Casting Time
    if "Casting Time" in fields:
        parsed.casting_time_raw = fields["Casting Time"]
        parsed.casting_time = parse_casting_time(fields["Casting Time"])

    # Range
    if "Range" in fields:
        parsed.range_raw = fields["Range"]
        parsed.range_category, parsed.range_formula = parse_range(fields["Range"])

    # Target / Area / Effect
    for key in ["Target", "Targets", "Target or Area", "Target/Area",
                 "Target, Effect, or Area"]:
        if key in fields:
            val = fields[key]
            if "area" in key.lower():
                parsed.area_raw = val
            parsed.target_raw = val
            break

    if "Area" in fields:
        parsed.area_raw = fields["Area"]
    if "Effect" in fields:
        parsed.effect_raw = fields["Effect"]

    # Duration
    if "Duration" in fields:
        parsed.duration_raw = fields["Duration"]
        dur_formula, conc, dismiss = parse_duration(fields["Duration"])
        parsed.duration_formula = dur_formula
        parsed.concentration = conc
        parsed.dismissible = dismiss

    # Saving Throw
    if "Saving Throw" in fields:
        parsed.saving_throw_raw = fields["Saving Throw"]
        parsed.save_type, parsed.save_effect = parse_save(fields["Saving Throw"])

    # Spell Resistance
    if "Spell Resistance" in fields:
        parsed.spell_resistance_raw = fields["Spell Resistance"]
        parsed.spell_resistance = parse_sr(fields["Spell Resistance"])

    # Body text
    parsed.body_text = fields.get("__body__", "")

    # Check for inheritance
    m = INHERITS_RE.search(parsed.body_text[:200])
    if m:
        ref_name = m.group(1).strip()
        # Clean up italic markers and trailing text
        ref_name = re.sub(r"\s+$", "", ref_name)
        parsed.inherits_from = ref_name

    # Extract formulas from body
    combined_text = parsed.body_text
    parsed.damage_formula, parsed.damage_type = extract_damage_info(
        combined_text, parsed.area_raw
    )
    parsed.healing_formula = extract_healing_info(combined_text)

    # If damage_type not found from body but present in descriptors
    if parsed.damage_formula and not parsed.damage_type:
        type_map = {
            "fire": "fire", "cold": "cold", "acid": "acid",
            "electricity": "electricity", "sonic": "sonic",
            "force": "force",
        }
        for desc in parsed.descriptors:
            if desc in type_map:
                parsed.damage_type = type_map[desc]
                break

    # AoE
    parsed.aoe_shape, parsed.aoe_radius_ft = extract_aoe_info(
        parsed.area_raw, combined_text
    )

    # Attack roll
    parsed.requires_attack_roll = bool(
        RANGED_TOUCH_RE.search(combined_text) or
        MELEE_TOUCH_RE.search(combined_text)
    )

    # Auto-hit (rare, mainly magic missile)
    if (not parsed.requires_attack_roll and not parsed.save_type and
            parsed.damage_formula and "miss" not in combined_text.lower()):
        # Very few spells auto-hit — be conservative
        if "automatically" in combined_text.lower():
            parsed.auto_hit = True

    # Conditions
    parsed.conditions_applied = extract_conditions(combined_text)

    # Infer higher-level fields
    parsed.target_type = infer_target_type(
        parsed.range_category, parsed.area_raw, parsed.target_raw,
        combined_text, parsed.aoe_shape, parsed.requires_attack_roll,
    )
    parsed.effect_type = infer_effect_type(parsed)
    parsed.delivery_mode = infer_delivery_mode(parsed)
    parsed.combat_role_tags = infer_combat_role_tags(parsed)

    return parsed


# ==========================================================================
# Stage 4: Inheritance Resolution
# ==========================================================================

def resolve_inheritance(
    spells: List[ParsedSpell],
) -> List[ParsedSpell]:
    """Resolve 'as X except' inheritance by copying parent fields."""
    name_map = {s.name.lower(): s for s in spells}

    for spell in spells:
        if not spell.inherits_from:
            continue

        parent_name = spell.inherits_from.lower().strip()
        parent = name_map.get(parent_name)
        if not parent:
            # Try partial matching
            for name, s in name_map.items():
                if parent_name in name or name in parent_name:
                    parent = s
                    break

        if not parent:
            spell.parse_warnings.append(
                f"Cannot resolve inheritance from '{spell.inherits_from}'"
            )
            continue

        # Copy fields that weren't explicitly set
        if not spell.class_levels:
            spell.class_levels = parent.class_levels
            spell.min_level = parent.min_level
        if not spell.verbal and not spell.somatic:
            spell.verbal = parent.verbal
            spell.somatic = parent.somatic
            spell.material = parent.material
            spell.focus = parent.focus
            spell.divine_focus = parent.divine_focus
            spell.xp_cost = parent.xp_cost
        if not spell.casting_time_raw:
            spell.casting_time = parent.casting_time
        if not spell.range_raw:
            spell.range_category = parent.range_category
            spell.range_formula = parent.range_formula
        if not spell.duration_raw:
            spell.duration_formula = parent.duration_formula
            spell.concentration = parent.concentration
            spell.dismissible = parent.dismissible
        if not spell.saving_throw_raw:
            spell.save_type = parent.save_type
            spell.save_effect = parent.save_effect
        if not spell.spell_resistance_raw:
            spell.spell_resistance = parent.spell_resistance
        if not spell.school:
            spell.school = parent.school
            spell.subschool = parent.subschool
            spell.descriptors = parent.descriptors
        if not spell.damage_formula and parent.damage_formula:
            spell.damage_formula = parent.damage_formula
            spell.damage_type = parent.damage_type
        if not spell.healing_formula and parent.healing_formula:
            spell.healing_formula = parent.healing_formula

    return spells


# ==========================================================================
# Stage 5: Template Emission
# ==========================================================================

def emit_templates(
    spells: List[ParsedSpell],
) -> Tuple[List[MechanicalSpellTemplate], Dict[str, Dict[str, str]], List[ExtractionGap]]:
    """Convert parsed spells to skin-stripped templates.

    Returns:
        templates: List of MechanicalSpellTemplate
        provenance: Dict mapping template_id -> {original_ref, source_page, source_id}
        gaps: List of ExtractionGap for skipped/flagged spells
    """
    # Sort alphabetically
    spells.sort(key=lambda s: s.name.lower())

    templates: List[MechanicalSpellTemplate] = []
    provenance: Dict[str, Dict[str, str]] = {}
    gaps: List[ExtractionGap] = []
    name_to_template_id: Dict[str, str] = {}

    for idx, spell in enumerate(spells):
        template_id = f"SPELL_{idx + 1:03d}"
        name_to_template_id[spell.name] = template_id

        # Check for extraction quality
        if not spell.school:
            gaps.append(ExtractionGap(
                name=spell.name,
                source_page=spell.source_page,
                reason="no_school_parsed",
                details="Could not parse school from entry",
            ))
            continue

        if not spell.class_levels and not spell.inherits_from:
            gaps.append(ExtractionGap(
                name=spell.name,
                source_page=spell.source_page,
                reason="no_level_parsed",
                details="No class/level pairs found",
            ))
            continue

        # Determine inherits_from_template
        inherits_template = None
        if spell.inherits_from:
            inherits_template = name_to_template_id.get(spell.inherits_from)

        try:
            template = MechanicalSpellTemplate(
                template_id=template_id,
                tier=spell.min_level,
                school_category=spell.school,
                subschool=spell.subschool,
                descriptors=spell.descriptors,
                class_levels=tuple(tuple(cl) for cl in spell.class_levels),
                target_type=spell.target_type,
                range_formula=spell.range_formula,
                aoe_shape=spell.aoe_shape,
                aoe_radius_ft=spell.aoe_radius_ft,
                effect_type=spell.effect_type,
                damage_formula=spell.damage_formula,
                damage_type=spell.damage_type,
                healing_formula=spell.healing_formula,
                save_type=spell.save_type,
                save_effect=spell.save_effect,
                spell_resistance=spell.spell_resistance,
                requires_attack_roll=spell.requires_attack_roll,
                auto_hit=spell.auto_hit,
                casting_time=spell.casting_time,
                duration_formula=spell.duration_formula,
                concentration=spell.concentration,
                dismissible=spell.dismissible,
                verbal=spell.verbal,
                somatic=spell.somatic,
                material=spell.material,
                focus=spell.focus,
                divine_focus=spell.divine_focus,
                xp_cost=spell.xp_cost,
                conditions_applied=spell.conditions_applied,
                conditions_duration=spell.conditions_duration,
                combat_role_tags=spell.combat_role_tags,
                delivery_mode=spell.delivery_mode,
                source_page=f"PHB p.{spell.source_page}",
                source_id=spell.source_id,
                inherits_from_template=inherits_template,
            )
            templates.append(template)

            provenance[template_id] = {
                "original_ref": f"page_ref:{spell.source_page}",
                "source_page": f"PHB p.{spell.source_page}",
                "source_id": spell.source_id,
            }

        except (ValueError, TypeError) as e:
            gaps.append(ExtractionGap(
                name=spell.name,
                source_page=spell.source_page,
                reason="template_creation_failed",
                details=str(e),
            ))

    return templates, provenance, gaps


# ==========================================================================
# Main Pipeline
# ==========================================================================

def run_pipeline() -> None:
    """Run the full extraction pipeline."""
    print("=" * 60)
    print("WO-CONTENT-EXTRACT-001: Spell Extraction Pipeline")
    print("=" * 60)

    # Stage 1: Load OCR pages
    print(f"\nStage 1: Loading OCR pages {START_PAGE}-{END_PAGE}...")
    pages = load_pages(SOURCE_DIR, START_PAGE, END_PAGE)
    print(f"  Loaded {len(pages)} pages")

    # Concatenate and clean
    text = concatenate_pages(pages)
    text = rejoin_hyphens(text)
    print(f"  Total text length: {len(text):,} chars")

    # Stage 2: Split into spell entries
    print("\nStage 2: Splitting spell entries...")
    entries = split_spells(text)
    print(f"  Found {len(entries)} spell entries")

    # Stage 3: Parse each spell
    print("\nStage 3: Parsing spell entries...")
    parsed_spells = []
    parse_errors = []
    for entry in entries:
        try:
            parsed = parse_spell_entry(entry)
            parsed_spells.append(parsed)
        except Exception as e:
            parse_errors.append(ExtractionGap(
                name=entry.name,
                source_page=entry.source_page,
                reason="parse_error",
                details=str(e),
            ))
    print(f"  Parsed {len(parsed_spells)} spells, {len(parse_errors)} errors")

    # Stage 4: Resolve inheritance
    print("\nStage 4: Resolving 'as X except' inheritance...")
    inherited_count = sum(1 for s in parsed_spells if s.inherits_from)
    parsed_spells = resolve_inheritance(parsed_spells)
    print(f"  {inherited_count} spells inherit from other spells")

    # Stage 5: Emit templates
    print("\nStage 5: Emitting templates...")
    templates, provenance, gaps = emit_templates(parsed_spells)
    gaps.extend(parse_errors)
    print(f"  {len(templates)} templates emitted")
    print(f"  {len(gaps)} gaps/flags")

    # Stage 6: Write output
    print("\nStage 6: Writing output...")

    # spells.json
    output_dir = PROJECT_ROOT / "aidm" / "data" / "content_pack"
    output_dir.mkdir(parents=True, exist_ok=True)
    spells_path = output_dir / "spells.json"
    with open(spells_path, "w", encoding="utf-8") as f:
        json.dump(
            [t.to_dict() for t in templates],
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"  Written {spells_path}")

    # provenance
    data_dir = PROJECT_ROOT / "tools" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    prov_path = data_dir / "spell_provenance.json"
    with open(prov_path, "w", encoding="utf-8") as f:
        json.dump(provenance, f, indent=2, ensure_ascii=False)
    print(f"  Written {prov_path}")

    # gaps
    gaps_path = data_dir / "extraction_gaps.json"
    with open(gaps_path, "w", encoding="utf-8") as f:
        json.dump(
            [{"name": g.name, "source_page": g.source_page,
              "reason": g.reason, "details": g.details} for g in gaps],
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"  Written {gaps_path}")

    # Summary
    print("\n" + "=" * 60)
    print("EXTRACTION REPORT")
    print("=" * 60)
    print(f"  Total spell entries found:   {len(entries)}")
    print(f"  Successfully parsed:         {len(parsed_spells)}")
    print(f"  Templates emitted:           {len(templates)}")
    print(f"  Gaps/flags:                  {len(gaps)}")
    if gaps:
        print("\n  Gap breakdown:")
        reason_counts: Dict[str, int] = {}
        for g in gaps:
            reason_counts[g.reason] = reason_counts.get(g.reason, 0) + 1
        for reason, count in sorted(reason_counts.items()):
            print(f"    {reason}: {count}")

    # Damage type distribution
    type_counts: Dict[str, int] = {}
    for t in templates:
        type_counts[t.effect_type] = type_counts.get(t.effect_type, 0) + 1
    print(f"\n  Effect type distribution:")
    for et, count in sorted(type_counts.items()):
        print(f"    {et}: {count}")

    # School distribution
    school_counts: Dict[str, int] = {}
    for t in templates:
        school_counts[t.school_category] = school_counts.get(t.school_category, 0) + 1
    print(f"\n  School distribution:")
    for sc, count in sorted(school_counts.items()):
        print(f"    {sc}: {count}")

    print("\nDone.")


if __name__ == "__main__":
    run_pipeline()
