"""Monster Extraction Pipeline — WO-CONTENT-EXTRACT-002.

Parses OCR text from Monster Manual pages and extracts mechanical
stat blocks into IP-clean MechanicalCreatureTemplate records.

Usage:
    python tools/extract_monsters.py [--source-dir DIR] [--output-dir DIR]
"""

import json
import logging
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OCR correction table — common substitution errors
# ---------------------------------------------------------------------------
OCR_CORRECTIONS = [
    (r"\bfe\.", "ft."),
    (r"\bfr\.", "ft."),
    (r"\bsouch\b", "touch"),
    (r"\brouch\b", "touch"),
    (r"\bflar-footed\b", "flat-footed"),
    (r"~(\d)", r"-\1"),      # ~2 -> -2
    (r"—(\d)", r"-\1"),      # em-dash before digit -> minus
    (r"\b1d¢\b", "1d6"),
    (r"\b2dé\b", "2d6"),
    (r"\+(\d)\.(?=\s)", r"+\1"),  # +5. -> +5
    (r";", ":"),              # semicolons used as colons in OCR
    # Fix hit dice OCR errors: 348+3 -> 3d8+3, 412 -> 4d12, etc.
    (r"\b(\d)(4)(\d)\b(?=\s*\()", r"\1d\2+\3"),  # crude but common: digit-4-digit near (hp)
    # Fix saves: "47" at start of saves line -> "+7" (common OCR for Fort +7)
    (r"^(\s*(?:Fort|Ref|Will)\s*):?\s*(\d)(\d),", r"\1 +\3,"),
    # Fix ": Fort" prefix on saves lines
    (r"^:\s*(Fort)", r"\1"),
]


def ocr_clean(text: str) -> str:
    """Apply OCR correction patterns to raw text."""
    for pattern, replacement in OCR_CORRECTIONS:
        text = re.sub(pattern, replacement, text)
    return text


# ---------------------------------------------------------------------------
# Dataclass — MechanicalCreatureTemplate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AttackEntry:
    """A single attack with bonus, damage, and optional notes."""
    description: str  # e.g. "claw +11 melee"
    bonus: Optional[int] = None
    damage: str = ""  # e.g. "2d4+6"
    notes: str = ""   # e.g. "plus slime"


@dataclass(frozen=True)
class MechanicalCreatureTemplate:
    template_id: str
    size_category: str
    creature_type: str
    subtypes: tuple

    # Core stats
    hit_dice: str
    hp_typical: int
    initiative_mod: int
    speed_ft: int
    speed_modes: dict

    # Defense
    ac_total: int
    ac_touch: int
    ac_flat_footed: int
    ac_components: dict

    # Offense
    bab: int
    grapple_mod: int
    attacks: tuple
    full_attacks: tuple
    space_ft: int
    reach_ft: int

    # Saves
    fort_save: int
    ref_save: int
    will_save: int

    # Abilities
    str_score: Optional[int]
    dex_score: Optional[int]
    con_score: Optional[int]
    int_score: Optional[int]
    wis_score: Optional[int]
    cha_score: Optional[int]

    # Special abilities
    special_attacks: tuple
    special_qualities: tuple

    # Classification
    cr: float
    alignment_tendency: str
    environment_tags: tuple

    # Tactical
    intelligence_band: str
    organization_patterns: tuple

    # Provenance
    source_page: str
    source_id: str

    # Advancement (raw)
    advancement: str = ""
    level_adjustment: str = ""
    treasure: str = ""


def _classify_int_band(int_score: Optional[int]) -> str:
    if int_score is None:
        return "mindless"
    if int_score <= 1:
        return "mindless"
    if int_score <= 2:
        return "animal"
    if int_score <= 7:
        return "low"
    if int_score <= 11:
        return "average"
    if int_score <= 15:
        return "high"
    return "genius"


# ---------------------------------------------------------------------------
# Stat block field patterns
# ---------------------------------------------------------------------------

# Field labels as they appear in OCR (after correction)
FIELD_LABELS = [
    "Hit Dice",
    "Initiative",
    "Speed",
    "Armor Class",
    "Base Attack/Grapple",
    "Attack",
    "Full Attack",
    "Space/Reach",
    "Special Attacks",
    "Special Qualities",
    "Saves",
    "Abilities",
    "Skills",
    "Feats",
    "Environment",
    "Organization",
    "Challenge Rating",
    "Treasure",
    "Alignment",
    "Advancement",
    "Level Adjustment",
]

# Regex to match SIZE TYPE (SUBTYPE) lines
SIZE_TYPE_RE = re.compile(
    r"^(Fine|Diminutive|Tiny|Small|Medium|Large|Huge|Gargantuan|Colossal)\s+"
    r"(Aberration|Animal|Construct|Dragon|Elemental|Fey|Giant|Humanoid|Magical Beast|Monstrous Humanoid|Ooze|Outsider|Plant|Undead|Vermin|Deathless)"
    r"(?:\s*\(([^)]+)\))?",
    re.IGNORECASE,
)

# Regex to match creature name header lines
# Creature names appear before the Size/Type line
# They are typically one line, possibly with a comma-separated variant
CREATURE_NAME_RE = re.compile(
    r"^([A-Z][A-Za-z' -]+(?:,\s*[A-Za-z0-9 -]+)?)\s*$"
)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _parse_int(s: str, default: int = 0) -> int:
    """Extract first integer from string."""
    s = s.strip().replace("—", "-").replace("–", "-")
    m = re.search(r"[+-]?\d+", s)
    return int(m.group()) if m else default


def _parse_float(s: str, default: float = 0.0) -> float:
    """Extract first number (int or float) from string."""
    s = s.strip()
    m = re.search(r"\d+(?:/\d+|\.\d+)?", s)
    if m:
        val = m.group()
        if "/" in val:
            num, den = val.split("/")
            return int(num) / int(den)
        return float(val)
    return default


def _parse_hit_dice(text: str) -> tuple:
    """Parse '8d8+40 (76 hp)' -> ('8d8+40', 76).

    Handles OCR corruptions where 'd' is dropped or replaced:
        '348+3' -> '3d8+3'
        '2248+110' -> '22d8+110' (OCR 'd' became '4')
    Uses stated HP to validate candidate interpretations.
    """
    text = text.strip()

    # Extract HP first — used to validate candidate dice expressions
    hp_match = re.search(r"\((\d+)\s*hp\)?", text)
    stated_hp = int(hp_match.group(1)) if hp_match else None

    # Try standard format first
    dice_match = re.search(r"(\d+d\d+(?:[+-]\d+)?)", text)
    if dice_match:
        dice_str = dice_match.group(1)
        hp = stated_hp if stated_hp else _compute_avg_hp(dice_str)
        return dice_str, hp

    # OCR-corrupted: no 'd' found. Extract numeric prefix before (N hp)
    prefix_match = re.match(r"^([0-9+-]+)\s*\(", text)
    if not prefix_match:
        return text.split("(")[0].strip(), stated_hp or 0

    prefix = prefix_match.group(1)

    # Strategy: try inserting 'd' at every position in the prefix
    # and check which interpretation matches the stated HP best
    best_candidate = None
    best_error = float("inf")

    # Split prefix into numeric part and modifier
    mod_match = re.search(r"([+-]\d+)$", prefix)
    if mod_match:
        num_part = prefix[: mod_match.start()]
        mod_str = mod_match.group(1)
        mod_val = int(mod_str)
    else:
        num_part = prefix
        mod_str = ""
        mod_val = 0

    # Try inserting 'd' at each position in num_part
    for i in range(1, len(num_part)):
        count_str = num_part[:i]
        die_str = num_part[i:]

        # The die part might have OCR noise — try with and without chars
        die_candidates = [die_str]
        # Also try dropping each digit in die_str (OCR inserted a digit)
        for j in range(len(die_str)):
            die_candidates.append(die_str[:j] + die_str[j + 1 :])

        for die_cand in die_candidates:
            if not die_cand or not die_cand.isdigit():
                continue
            die_size = int(die_cand)
            if die_size not in (4, 6, 8, 10, 12):
                continue

            try:
                count = int(count_str)
            except ValueError:
                continue
            if count < 1 or count > 100:
                continue

            candidate = f"{count}d{die_size}"
            if mod_val > 0:
                candidate += f"+{mod_val}"
            elif mod_val < 0:
                candidate += str(mod_val)

            avg = _compute_avg_hp(candidate)
            if stated_hp:
                error = abs(avg - stated_hp)
                if error < best_error:
                    best_error = error
                    best_candidate = candidate
            elif best_candidate is None:
                best_candidate = candidate

    if best_candidate:
        hp = stated_hp if stated_hp else _compute_avg_hp(best_candidate)
        return best_candidate, hp

    return prefix, stated_hp or 0


def _compute_avg_hp(dice_str: str) -> int:
    """Compute average HP from dice expression like '8d8+40'."""
    m = re.match(r"(\d+)d(\d+)([+-]\d+)?", dice_str)
    if not m:
        return 0
    n = int(m.group(1))
    d = int(m.group(2))
    mod = int(m.group(3)) if m.group(3) else 0
    return int(n * (d + 1) / 2 + mod)


def _parse_initiative(text: str) -> int:
    """Parse '+1' or '+5' or '-2'."""
    return _parse_int(text)


def _parse_speed(text: str) -> tuple:
    """Parse 'Speed: 30 ft. (6 squares), fly 60 ft. (good), swim 30 ft.'
    Returns (base_speed, {mode: speed}).
    """
    text = text.strip()
    modes = {}
    base_speed = 0

    # Extract base land speed (the first number)
    base_match = re.search(r"(\d+)\s*ft", text)
    if base_match:
        base_speed = int(base_match.group(1))

    # Extract other movement modes
    for mode in ("fly", "swim", "burrow", "climb"):
        mode_match = re.search(
            rf"{mode}\s+(\d+)\s*ft", text, re.IGNORECASE
        )
        if mode_match:
            modes[mode] = int(mode_match.group(1))

    # Check if primary mode is fly (no land speed)
    if text.strip().lower().startswith("fly"):
        fly_match = re.search(r"[Ff]ly\s+(\d+)\s*ft", text)
        if fly_match:
            base_speed = int(fly_match.group(1))
            modes["fly"] = base_speed

    return base_speed, modes


def _parse_ac(text: str) -> dict:
    """Parse AC line into components.

    'Armor Class: 16 (-2 size, +1 Dex, +7 natural), touch 9, flat-footed 15'
    Returns {total, touch, flat_footed, components}.
    """
    result = {"total": 0, "touch": 10, "flat_footed": 10, "components": {}}

    # Total AC
    total_match = re.search(r"(\d+)\s*\(", text)
    if not total_match:
        total_match = re.search(r"^[^:]*:\s*(\d+)", text)
        if not total_match:
            total_match = re.search(r"^(\d+)", text.strip())
    if total_match:
        result["total"] = int(total_match.group(1))

    # Touch AC
    touch_match = re.search(r"touch\s+(\d+)", text, re.IGNORECASE)
    if touch_match:
        result["touch"] = int(touch_match.group(1))

    # Flat-footed AC
    ff_match = re.search(r"flat-footed\s+(\d+)", text, re.IGNORECASE)
    if ff_match:
        result["flat_footed"] = int(ff_match.group(1))

    # AC components within parentheses
    paren_match = re.search(r"\(([^)]+)\)", text)
    if paren_match:
        components_text = paren_match.group(1)
        for comp in re.finditer(r"([+-]\d+)\s+(\w+(?:\s+\w+)?)", components_text):
            val = int(comp.group(1))
            name = comp.group(2).strip().lower()
            result["components"][name] = val

    return result


def _parse_bab_grapple(text: str) -> tuple:
    """Parse '+6/+22' or '+6/+14'."""
    text = text.strip().replace("—", "-").replace("–", "-")
    parts = re.findall(r"[+-]?\d+", text)
    if len(parts) >= 2:
        return int(parts[0]), int(parts[1])
    elif len(parts) == 1:
        return int(parts[0]), int(parts[0])
    return 0, 0


def _parse_attack_line(text: str) -> tuple:
    """Parse attack descriptions into structured entries.

    'Tentacle +12 melee (1d6+8 plus slime)' or
    '2 claws +11 melee (2d4+6) and bite +9 melee (2d8+3)'
    Returns tuple of dicts.
    """
    text = text.strip()
    if not text or text == "-" or text == "—":
        return ()

    attacks = []
    # Split on ' and ' or ' or '
    parts = re.split(r"\s+and\s+|\s+or\s+", text)
    for part in parts:
        part = part.strip()
        if not part:
            continue

        bonus_match = re.search(r"([+-]\d+)\s+(melee|ranged)", part)
        damage_match = re.search(r"\(([^)]+)\)", part)

        entry = {
            "description": part,
            "bonus": int(bonus_match.group(1)) if bonus_match else None,
            "damage": damage_match.group(1) if damage_match else "",
        }
        attacks.append(entry)

    return tuple(attacks)


def _parse_space_reach(text: str) -> tuple:
    """Parse '15 ft./10 ft.' or '5 ft/5 ft.'."""
    text = text.strip()
    nums = re.findall(r"(\d+)\s*ft", text)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    elif len(nums) == 1:
        return int(nums[0]), int(nums[0])
    return 5, 5


def _parse_saves(text: str) -> tuple:
    """Parse 'Fort +7, Ref +3, Will +11'.

    Handles OCR artifacts like:
      '47, Ref +3, Will +11'  (Fort +7 misread as '47')
      ': Fort +7, Ref +6, Will +7' (leading colon)
    """
    # Strip leading colon or label prefix
    text = re.sub(r"^[:\s]*(?:Saves\s*:?\s*)?", "", text.strip())

    fort = ref = will = 0

    # Standard patterns
    fort_m = re.search(r"Fort\s*([+-]\d+)", text, re.IGNORECASE)
    ref_m = re.search(r"Ref\s*([+-]\d+)", text, re.IGNORECASE)
    will_m = re.search(r"Will\s*([+-]\d+)", text, re.IGNORECASE)

    if fort_m:
        fort = int(fort_m.group(1))
    else:
        # OCR artifact: "47, Ref +3" where 47 = Fort +7
        # Try to extract a leading number before "Ref"
        leading_m = re.match(r"^[+-]?(\d{1,2})\s*,\s*Ref", text)
        if leading_m:
            # This is likely a mangled Fort save — the last digit
            val = int(leading_m.group(1))
            if val > 20:
                # Probably OCR artifact: take last digit as the save value
                fort = val % 10
            else:
                fort = val

    if ref_m:
        ref = int(ref_m.group(1))
    if will_m:
        will = int(will_m.group(1))
    return fort, ref, will


def _parse_abilities(text: str) -> dict:
    """Parse 'Str 26, Dex 12, Con 20, Int 15, Wis 17, Cha 17'."""
    result = {}
    for ability in ("Str", "Dex", "Con", "Int", "Wis", "Cha"):
        m = re.search(rf"{ability}\s+(\d+|—|-)", text)
        if m:
            val = m.group(1).strip()
            if val in ("—", "-", ""):
                result[ability.lower()] = None
            else:
                result[ability.lower()] = int(val)
        else:
            result[ability.lower()] = None
    return result


def _parse_special_abilities(text: str) -> tuple:
    """Parse special attacks/qualities into mechanical tags.

    Converts prose descriptions like 'darkvision 60 ft.' into
    tags like 'darkvision_60'.
    """
    text = text.strip()
    if not text or text == "-" or text == "—":
        return ()

    # Split on commas
    parts = [p.strip() for p in text.split(",")]
    tags = []
    for part in parts:
        part = part.strip()
        if not part or part == "-":
            continue
        tag = _mechanize_ability(part)
        if tag:
            tags.append(tag)
    return tuple(tags)


def _mechanize_ability(text: str) -> str:
    """Convert a special ability description into a mechanical tag.

    Examples:
        'darkvision 60 ft.' -> 'darkvision_60'
        'damage reduction 5/magic' -> 'damage_reduction_5_magic'
        'spell resistance 19' -> 'spell_resistance_19'
        'immunity to fire' -> 'immunity_fire'
        'breath weapon' -> 'breath_weapon'
    """
    text = text.strip().lower()
    text = re.sub(r"\s*ft\.?\s*", " ", text)  # remove "ft."
    text = re.sub(r"\s*\([^)]*\)\s*", " ", text)  # remove parentheticals

    # Specific patterns
    # Darkvision/blindsight/tremorsense with range
    m = re.match(r"(darkvision|blindsight|blindsense|tremorsense)\s+(\d+)", text)
    if m:
        return f"{m.group(1)}_{m.group(2)}"

    # Damage reduction
    m = re.match(r"damage reduction\s+(\d+)/([\w—-]+)", text)
    if m:
        bypass = m.group(2).replace("—", "none").replace("-", "none")
        return f"damage_reduction_{m.group(1)}_{bypass}"

    # Spell resistance
    m = re.match(r"spell resistance\s+(\d+)", text)
    if m:
        return f"spell_resistance_{m.group(1)}"

    # Immunity
    m = re.match(r"immunity to\s+(.+)", text)
    if m:
        target = m.group(1).strip().replace(" ", "_")
        return f"immunity_{target}"

    # Resistance to X N
    m = re.match(r"resistance to\s+(\w+)\s+(\d+)", text)
    if m:
        return f"resistance_{m.group(1)}_{m.group(2)}"

    # Fast healing / regeneration
    m = re.match(r"(fast healing|regeneration)\s+(\d+)", text)
    if m:
        return f"{m.group(1).replace(' ', '_')}_{m.group(2)}"

    # Vulnerability
    m = re.match(r"vulnerability to\s+(.+)", text)
    if m:
        target = m.group(1).strip().replace(" ", "_")
        return f"vulnerability_{target}"

    # Generic: just snake_case the text
    tag = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    if len(tag) > 60:
        tag = tag[:60].rstrip("_")
    return tag


def _parse_alignment(text: str) -> str:
    """Normalize alignment to a standard tag."""
    text = text.strip().lower()
    text = re.sub(r"^(always|usually|often)\s+", r"\1_", text)
    text = re.sub(r"\s+", "_", text)
    return text


def _parse_environment(text: str) -> tuple:
    """Parse environment into tags."""
    text = text.strip().lower()
    if not text or text == "-":
        return ()
    parts = [p.strip() for p in re.split(r",|and", text)]
    tags = []
    for p in parts:
        p = p.strip()
        if p:
            tags.append(re.sub(r"\s+", "_", p))
    return tuple(tags)


def _parse_organization(text: str) -> tuple:
    """Parse organization patterns."""
    text = text.strip()
    if not text or text == "-":
        return ()
    parts = [p.strip() for p in re.split(r",\s*or\s+|,\s+or\s+|\bor\b", text)]
    return tuple(p.strip() for p in parts if p.strip())


# ---------------------------------------------------------------------------
# Stat block segmentation
# ---------------------------------------------------------------------------

def _is_field_label_line(line: str) -> Optional[str]:
    """Check if a line starts with a known field label.
    Returns the label name if found, else None.
    """
    line_stripped = line.strip()
    # Some lines start with the label directly, others with 'label:'
    for label in FIELD_LABELS:
        # Match "Label:" or "Label " at start of line
        if re.match(rf"^{re.escape(label)}\s*:", line_stripped, re.IGNORECASE):
            return label
        # Some OCR omits the colon
        if line_stripped.lower().startswith(label.lower() + " "):
            return label
    return None


def _extract_field_value(line: str, label: str) -> str:
    """Extract the value part after the field label."""
    # Try with colon first
    m = re.match(rf"^{re.escape(label)}\s*:\s*(.*)", line.strip(), re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Try without colon
    m = re.match(rf"^{re.escape(label)}\s+(.*)", line.strip(), re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return ""


def segment_stat_blocks(text: str) -> list:
    """Segment OCR page text into individual stat block chunks.

    Returns list of dicts with keys:
        'name': creature name (original, for provenance only)
        'size_type_line': the Size/Type line
        'fields': dict mapping field label -> value text
        'raw_text': the full raw text of the block
    """
    lines = text.split("\n")
    blocks = []
    current_block = None
    current_field = None
    creature_name = None

    # Sequential field order for unlabeled stat blocks
    UNLABELED_FIELD_ORDER = [
        "Hit Dice", "Initiative", "Speed", "Armor Class",
        "Base Attack/Grapple", "Attack", "Full Attack",
        "Space/Reach", "Special Attacks", "Special Qualities",
        "Saves", "Abilities", "Skills", "Feats", "Environment",
        "Organization", "Challenge Rating", "Treasure",
        "Alignment", "Advancement", "Level Adjustment",
    ]
    unlabeled_field_idx = 0
    is_unlabeled_block = False

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Check for Size/Type line
        size_match = SIZE_TYPE_RE.match(stripped)
        if size_match:
            # Save any previous block
            if current_block is not None:
                blocks.append(current_block)

            current_block = {
                "name": creature_name or "",
                "size_type_line": stripped,
                "fields": {},
                "raw_text": stripped + "\n",
            }
            current_field = None
            creature_name = None
            unlabeled_field_idx = 0
            is_unlabeled_block = False
            i += 1
            continue

        # Check for field labels
        label = _is_field_label_line(stripped)
        if label and current_block is not None:
            value = _extract_field_value(stripped, label)
            current_block["fields"][label] = value
            current_block["raw_text"] += stripped + "\n"
            current_field = label
            is_unlabeled_block = False
            i += 1
            continue

        # Check for saves line without label (e.g. "Fort +4, Ref +0, Will -1")
        saves_match = re.match(
            r"^(?::?\s*)?Fort\s+[+-]?\d+", stripped, re.IGNORECASE
        ) or re.match(r"^\d{1,2},\s*Ref\s+[+-]?\d+", stripped)
        if current_block is not None and saves_match:
            current_block["fields"]["Saves"] = stripped
            current_block["raw_text"] += stripped + "\n"
            current_field = "Saves"
            i += 1
            continue

        # Check for abilities line without label
        if current_block is not None and re.match(
            r"^Str\s+\d+", stripped, re.IGNORECASE
        ):
            current_block["fields"]["Abilities"] = stripped
            current_block["raw_text"] += stripped + "\n"
            current_field = "Abilities"
            i += 1
            continue

        # Check for unlabeled stat block values (no field labels at all)
        # This happens with variant stat blocks (e.g. Aboleth Mage)
        if current_block is not None and not current_block["fields"] and not current_field:
            # Check if this looks like a Hit Dice value (NdN+N (N hp))
            if re.match(r"^\d+d\d+|^\d{2,}[+-]\d+\s*\(", stripped):
                is_unlabeled_block = True
                current_block["fields"]["Hit Dice"] = stripped
                current_block["raw_text"] += stripped + "\n"
                current_field = "Hit Dice"
                unlabeled_field_idx = 1
                i += 1
                continue

        # Handle unlabeled block: assign fields by position
        if current_block is not None and is_unlabeled_block and unlabeled_field_idx < len(UNLABELED_FIELD_ORDER):
            field_name = UNLABELED_FIELD_ORDER[unlabeled_field_idx]
            current_block["fields"][field_name] = stripped
            current_block["raw_text"] += stripped + "\n"
            current_field = field_name
            unlabeled_field_idx += 1
            i += 1
            continue

        # If we have a current field, this might be a continuation line
        if current_block is not None and current_field:
            # Continuation: append to current field
            current_block["fields"][current_field] += " " + stripped
            current_block["raw_text"] += stripped + "\n"
            i += 1
            continue

        # Check if this is a creature name line (precedes a size/type line)
        name_match = CREATURE_NAME_RE.match(stripped)
        if name_match and not stripped.startswith(
            ("The ", "This ", "A ", "An ", "In ", "On ", "It ")
        ):
            # Look ahead for Size/Type line
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and SIZE_TYPE_RE.match(lines[j].strip()):
                creature_name = name_match.group(1).strip()
                i += 1
                continue

        # If we're in a block, try appending to raw text
        if current_block is not None:
            current_block["raw_text"] += stripped + "\n"

        i += 1

    # Don't forget the last block
    if current_block is not None:
        blocks.append(current_block)

    return blocks


def _find_stat_blocks_in_table_format(text: str) -> list:
    """Handle side-by-side stat block tables (e.g., Arrowhawk variants).

    These appear as tab/space-separated columns. For now, we skip these
    and log them as gaps — they need manual handling.
    """
    # Detect multi-column format: multiple Size lines on same text line
    lines = text.split("\n")
    multi_col_lines = 0
    for line in lines:
        # Count Size categories in one line
        sizes = re.findall(
            r"(?:Fine|Diminutive|Tiny|Small|Medium|Large|Huge|Gargantuan|Colossal)\s+\w+",
            line,
            re.IGNORECASE,
        )
        if len(sizes) >= 2:
            multi_col_lines += 1

    return multi_col_lines > 0


def _sanitize_text_field(text: str, max_len: int = 100) -> str:
    """Sanitize a text field by truncating and stripping non-mechanical content."""
    text = text.strip()
    # Remove leading apostrophes or parens from OCR
    text = re.sub(r"^['\(]+\s*", "", text)
    # Truncate at max length
    if len(text) > max_len:
        text = text[:max_len].rstrip()
    return text


def _sanitize_treasure(text: str) -> str:
    """Extract just the treasure type from the field.

    Valid values: 'None', 'Standard', 'Double standard',
    'Triple standard', 'No coins', etc.
    """
    text = text.strip()
    # Remove leading apostrophes/parens from OCR
    text = re.sub(r"^['\(]+\s*", "", text)

    # Match known treasure types
    m = re.match(
        r"^(None|No coins[^.]*|Standard|Double standard|Triple standard|"
        r"No goods[^.]*|Half standard|1/10th coins[^.]*)",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    # Take just the first word(s) up to the first non-treasure word
    m = re.match(r"^(\w+(?:\s+\w+)?)", text)
    if m:
        return m.group(1).strip()[:30]
    return ""


def _sanitize_level_adjustment(text: str) -> str:
    """Parse level adjustment: should be a number, '—', or empty."""
    text = text.strip()
    # Extract just the LA value
    m = re.match(r"^[+]?\s*(\d+|—|-|=\s*—)", text)
    if m:
        val = m.group(1).strip()
        if val in ("—", "-", "= —"):
            return "—"
        return val
    # If it starts with a number, take just that
    m = re.match(r"^(\d+)", text)
    if m:
        return m.group(1)
    return ""


# ---------------------------------------------------------------------------
# Block-to-Template conversion
# ---------------------------------------------------------------------------

def block_to_template(
    block: dict,
    template_id: str,
    page_num: str,
    source_id: str,
) -> Optional[MechanicalCreatureTemplate]:
    """Convert a parsed stat block dict into a MechanicalCreatureTemplate."""
    fields = block["fields"]

    # Must have minimum fields to be a valid stat block
    required = ("Hit Dice", "Armor Class")
    if not any(f in fields for f in required):
        return None

    # Parse size/type line
    size_match = SIZE_TYPE_RE.match(block["size_type_line"])
    if not size_match:
        return None

    size_category = size_match.group(1).lower()
    creature_type = size_match.group(2).lower().strip()
    subtypes_raw = size_match.group(3) or ""
    subtypes = tuple(
        s.strip().lower() for s in subtypes_raw.split(",") if s.strip()
    )

    # Hit Dice
    hd_text = fields.get("Hit Dice", "")
    if not hd_text:
        # Try to find HD in raw text
        hd_match = re.search(r"(\d+d\d+[^\n]*hp\))", block["raw_text"])
        if hd_match:
            hd_text = hd_match.group(1)
    hit_dice, hp_typical = _parse_hit_dice(hd_text) if hd_text else ("", 0)

    # Initiative
    init_text = fields.get("Initiative", "")
    initiative_mod = _parse_initiative(init_text)

    # Speed
    speed_text = fields.get("Speed", "")
    speed_ft, speed_modes = _parse_speed(speed_text)

    # AC
    ac_text = fields.get("Armor Class", "")
    ac_data = _parse_ac(ac_text)

    # BAB/Grapple
    bab_text = fields.get("Base Attack/Grapple", "")
    bab, grapple = _parse_bab_grapple(bab_text)

    # Attacks
    attack_text = fields.get("Attack", "")
    attacks = _parse_attack_line(attack_text)

    full_attack_text = fields.get("Full Attack", "")
    full_attacks = _parse_attack_line(full_attack_text)

    # Space/Reach
    sr_text = fields.get("Space/Reach", "")
    space_ft, reach_ft = _parse_space_reach(sr_text)

    # Special abilities
    sa_text = fields.get("Special Attacks", "")
    special_attacks = _parse_special_abilities(sa_text)

    sq_text = fields.get("Special Qualities", "")
    special_qualities = _parse_special_abilities(sq_text)

    # Saves
    saves_text = fields.get("Saves", "")
    fort, ref, will_save = _parse_saves(saves_text)

    # Abilities
    abilities_text = fields.get("Abilities", "")
    abilities = _parse_abilities(abilities_text)

    # CR
    cr_text = fields.get("Challenge Rating", "")
    cr = _parse_float(cr_text)

    # Alignment
    alignment_text = fields.get("Alignment", "")
    alignment = _parse_alignment(alignment_text)

    # Environment
    env_text = fields.get("Environment", "")
    environment_tags = _parse_environment(env_text)

    # Organization
    org_text = fields.get("Organization", "")
    organization = _parse_organization(org_text)

    # Advancement
    adv_text = _sanitize_text_field(fields.get("Advancement", ""))
    level_adj_text = _sanitize_level_adjustment(fields.get("Level Adjustment", ""))
    treasure_text = _sanitize_treasure(fields.get("Treasure", ""))

    int_score = abilities.get("int")
    intelligence_band = _classify_int_band(int_score)

    try:
        return MechanicalCreatureTemplate(
            template_id=template_id,
            size_category=size_category,
            creature_type=creature_type,
            subtypes=subtypes,
            hit_dice=hit_dice,
            hp_typical=hp_typical,
            initiative_mod=initiative_mod,
            speed_ft=speed_ft,
            speed_modes=speed_modes,
            ac_total=ac_data["total"],
            ac_touch=ac_data["touch"],
            ac_flat_footed=ac_data["flat_footed"],
            ac_components=ac_data["components"],
            bab=bab,
            grapple_mod=grapple,
            attacks=attacks,
            full_attacks=full_attacks,
            space_ft=space_ft,
            reach_ft=reach_ft,
            fort_save=fort,
            ref_save=ref,
            will_save=will_save,
            str_score=abilities.get("str"),
            dex_score=abilities.get("dex"),
            con_score=abilities.get("con"),
            int_score=int_score,
            wis_score=abilities.get("wis"),
            cha_score=abilities.get("cha"),
            special_attacks=special_attacks,
            special_qualities=special_qualities,
            cr=cr,
            alignment_tendency=alignment,
            environment_tags=environment_tags,
            intelligence_band=intelligence_band,
            organization_patterns=organization,
            source_page=page_num,
            source_id=source_id,
            advancement=adv_text,
            level_adjustment=level_adj_text,
            treasure=treasure_text,
        )
    except Exception as e:
        log.warning("Failed to create template from block on page %s: %s", page_num, e)
        return None


# ---------------------------------------------------------------------------
# Special ability deep parsing (Phase 2)
# ---------------------------------------------------------------------------

def parse_special_abilities_deep(raw_text: str) -> list:
    """Parse special ability descriptions from the prose sections.

    Looks for patterns like:
        'Breath Weapon (Su): ...'
        'Poison (Ex): ...'

    Returns list of structured ability dicts.
    """
    abilities = []
    # Find ability headers: "Ability Name (Su/Ex/Sp):"
    pattern = re.compile(
        r"([A-Z][A-Za-z ]+)\s*\((Su|Ex|Sp)\)\s*:\s*(.+?)(?=\n[A-Z][A-Za-z ]+\s*\((Su|Ex|Sp)\)|$)",
        re.DOTALL,
    )
    for m in pattern.finditer(raw_text):
        name = m.group(1).strip()
        ability_type = m.group(2)
        description = m.group(3).strip()
        ability = {
            "name": _mechanize_ability(name),
            "type": ability_type.lower(),
            "raw_description": description[:200],  # Truncate for safety
        }

        # Try to extract structured mechanics
        mechanics = _extract_ability_mechanics(name.lower(), description)
        ability.update(mechanics)
        abilities.append(ability)

    return abilities


def _extract_ability_mechanics(name: str, description: str) -> dict:
    """Extract structured mechanics from ability description text."""
    mechanics = {}

    # Breath weapon
    if "breath" in name or "breath weapon" in description.lower():
        shape_m = re.search(r"(\d+)-foot\s+(cone|line)", description)
        if shape_m:
            mechanics["shape"] = shape_m.group(2)
            mechanics["size_ft"] = int(shape_m.group(1))
        damage_m = re.search(r"(\d+d\d+(?:[+-]\d+)?)\s*(fire|cold|acid|electricity|sonic|force)?", description)
        if damage_m:
            mechanics["damage"] = damage_m.group(1)
            if damage_m.group(2):
                mechanics["damage_type"] = damage_m.group(2)
        save_m = re.search(r"DC\s+(\d+)\s+(Reflex|Fortitude|Will)", description)
        if save_m:
            mechanics["save_dc"] = int(save_m.group(1))
            mechanics["save_type"] = save_m.group(2).lower()
        recharge_m = re.search(r"(\d+d\d+)\s+rounds?", description)
        if recharge_m:
            mechanics["recharge"] = recharge_m.group(1)

    # Poison
    if "poison" in name:
        dc_m = re.search(r"DC\s+(\d+)", description)
        if dc_m:
            mechanics["save_dc"] = int(dc_m.group(1))
        damage_m = re.search(r"(\d+d\d+(?:[+-]\d+)?)\s*(Str|Dex|Con|Int|Wis|Cha)", description)
        if damage_m:
            mechanics["damage"] = damage_m.group(1)
            mechanics["ability_affected"] = damage_m.group(2).lower()

    # Gaze attack
    if "gaze" in name:
        dc_m = re.search(r"DC\s+(\d+)", description)
        range_m = re.search(r"(\d+)\s*(?:feet|ft)", description)
        if dc_m:
            mechanics["save_dc"] = int(dc_m.group(1))
        if range_m:
            mechanics["range_ft"] = int(range_m.group(1))

    # Spell resistance
    sr_m = re.search(r"spell resistance\s+(\d+)", description, re.IGNORECASE)
    if sr_m:
        mechanics["spell_resistance"] = int(sr_m.group(1))

    # Damage reduction
    dr_m = re.search(r"damage reduction\s+(\d+)/([\w-]+)", description, re.IGNORECASE)
    if dr_m:
        mechanics["dr_value"] = int(dr_m.group(1))
        mechanics["dr_bypass"] = dr_m.group(2)

    # Regeneration / Fast healing
    regen_m = re.search(r"(regeneration|fast healing)\s+(\d+)", description, re.IGNORECASE)
    if regen_m:
        mechanics[regen_m.group(1).lower().replace(" ", "_")] = int(regen_m.group(2))

    # Spell-like abilities
    if "spell-like" in name or "spell-like" in description.lower():
        sla_entries = re.findall(
            r"(\d+/day|at will)\s*[—:-]\s*([a-z][a-z ']+)",
            description,
            re.IGNORECASE,
        )
        if sla_entries:
            mechanics["spell_like_abilities"] = [
                {"uses": u.lower(), "spell": s.strip()}
                for u, s in sla_entries
            ]
        cl_m = re.search(r"caster level\s+(\d+)", description, re.IGNORECASE)
        if cl_m:
            mechanics["caster_level"] = int(cl_m.group(1))

    return mechanics


# ---------------------------------------------------------------------------
# Name stripping — IP firewall
# ---------------------------------------------------------------------------

# We do NOT include original names in the output creatures.json.
# Names go only to provenance.json (internal, not distributed).


# ---------------------------------------------------------------------------
# Main extraction pipeline
# ---------------------------------------------------------------------------

def process_page(
    page_path: str,
    creature_counter: list,
    source_id: str,
) -> tuple:
    """Process a single OCR page file.

    Returns:
        templates: list of MechanicalCreatureTemplate
        provenance: list of {template_id, original_name, page}
        gaps: list of {page, reason, context}
    """
    page_num = Path(page_path).stem  # e.g. "0010"
    templates = []
    provenance = []
    gaps = []

    try:
        with open(page_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()
    except Exception as e:
        gaps.append({
            "page": page_num,
            "reason": f"failed_to_read: {e}",
            "context": "",
        })
        return templates, provenance, gaps

    # Apply OCR corrections
    cleaned = ocr_clean(raw_text)

    # Check for multi-column format
    if _find_stat_blocks_in_table_format(cleaned):
        # Try to extract anyway, but also log the gap
        gaps.append({
            "page": page_num,
            "reason": "multi_column_format_detected",
            "context": "Side-by-side stat blocks may be partially parsed",
        })

    # Segment into stat blocks
    blocks = segment_stat_blocks(cleaned)

    if not blocks:
        # No stat blocks found — might be a narrative/description page
        return templates, provenance, gaps

    for block in blocks:
        # Validate: must have at least Hit Dice or AC to be a real stat block
        if not block["fields"]:
            continue

        creature_counter[0] += 1
        template_id = f"CREATURE_{creature_counter[0]:04d}"

        template = block_to_template(block, template_id, page_num, source_id)
        if template:
            # Validate quality: must have HD with 'd', non-zero AC, non-zero HP
            valid_hd = bool(template.hit_dice) and "d" in template.hit_dice
            valid_ac = template.ac_total > 0
            valid_hp = template.hp_typical > 0
            has_any_save = template.fort_save != 0 or template.ref_save != 0 or template.will_save != 0
            has_any_ability = any(
                getattr(template, f"{a}_score") is not None
                for a in ("str", "dex", "con", "int", "wis", "cha")
            )

            if valid_hd and valid_ac and valid_hp and (has_any_save or has_any_ability):
                templates.append(template)
                provenance.append({
                    "template_id": template_id,
                    "original_name": block["name"],
                    "page": page_num,
                    "fields_parsed": list(block["fields"].keys()),
                    "field_count": len(block["fields"]),
                })

                # Try deep ability parsing from the page's prose
                deep_abilities = parse_special_abilities_deep(block["raw_text"])
                if deep_abilities:
                    provenance[-1]["deep_abilities"] = deep_abilities
            else:
                reasons = []
                if not valid_hd:
                    reasons.append("invalid_hd")
                if not valid_ac:
                    reasons.append("zero_ac")
                if not valid_hp:
                    reasons.append("zero_hp")
                if not has_any_save and not has_any_ability:
                    reasons.append("no_saves_or_abilities")
                gaps.append({
                    "page": page_num,
                    "reason": f"low_quality: {', '.join(reasons)}",
                    "context": block.get("name", "unknown")[:80],
                    "fields_found": list(block["fields"].keys()),
                })
        else:
            gaps.append({
                "page": page_num,
                "reason": "block_parse_failed",
                "context": block.get("name", "unknown")[:80],
                "fields_found": list(block["fields"].keys()),
            })

    return templates, provenance, gaps


def _template_to_dict(t: MechanicalCreatureTemplate) -> dict:
    """Convert template to JSON-serializable dict."""
    d = {}
    for f_name in t.__dataclass_fields__:
        val = getattr(t, f_name)
        if isinstance(val, tuple):
            val = list(val)
        d[f_name] = val
    return d


def run_extraction(source_dir: str, output_dir: str):
    """Run the full extraction pipeline."""
    source_path = Path(source_dir)
    output_path = Path(output_dir)

    source_id = source_path.name  # e.g. "e390dfd9143f"

    # Collect all page files
    page_files = sorted(source_path.glob("*.txt"))
    log.info("Found %d page files in %s", len(page_files), source_dir)

    # Skip front matter pages (typically pages 1-8 are credits, ToC, etc.)
    # We process all pages and let the parser filter non-stat-block content

    all_templates = []
    all_provenance = []
    all_gaps = []
    creature_counter = [0]  # mutable counter

    for page_file in page_files:
        templates, provenance, gaps = process_page(
            str(page_file), creature_counter, source_id
        )
        all_templates.extend(templates)
        all_provenance.extend(provenance)
        all_gaps.extend(gaps)

    log.info(
        "Extraction complete: %d creatures extracted, %d gaps logged",
        len(all_templates),
        len(all_gaps),
    )

    # -----------------------------------------------------------------------
    # Output: creatures.json (IP-clean — no original names)
    # -----------------------------------------------------------------------
    creatures_out = output_path / "content_pack" / "creatures.json"
    creatures_out.parent.mkdir(parents=True, exist_ok=True)

    creatures_data = {
        "schema_version": "1.0.0",
        "source_id": source_id,
        "extraction_version": "WO-CONTENT-EXTRACT-002",
        "creature_count": len(all_templates),
        "creatures": [_template_to_dict(t) for t in all_templates],
    }

    with open(creatures_out, "w", encoding="utf-8") as f:
        json.dump(creatures_data, f, indent=2, ensure_ascii=False)
    log.info("Wrote %s (%d creatures)", creatures_out, len(all_templates))

    # -----------------------------------------------------------------------
    # Output: creature_provenance.json (INTERNAL ONLY — contains names)
    # -----------------------------------------------------------------------
    tools_data_dir = Path(__file__).parent / "data"
    tools_data_dir.mkdir(parents=True, exist_ok=True)
    prov_out = tools_data_dir / "creature_provenance.json"

    prov_data = {
        "schema_version": "1.0.0",
        "source_id": source_id,
        "note": "INTERNAL ONLY — contains original creature names for provenance tracking",
        "entries": all_provenance,
    }

    with open(prov_out, "w", encoding="utf-8") as f:
        json.dump(prov_data, f, indent=2, ensure_ascii=False)
    log.info("Wrote %s (%d entries)", prov_out, len(all_provenance))

    # -----------------------------------------------------------------------
    # Output: creature_extraction_gaps.json
    # -----------------------------------------------------------------------
    gaps_out = tools_data_dir / "creature_extraction_gaps.json"

    gaps_data = {
        "schema_version": "1.0.0",
        "source_id": source_id,
        "gap_count": len(all_gaps),
        "gaps": all_gaps,
    }

    with open(gaps_out, "w", encoding="utf-8") as f:
        json.dump(gaps_data, f, indent=2, ensure_ascii=False)
    log.info("Wrote %s (%d gaps)", gaps_out, len(all_gaps))

    return all_templates, all_provenance, all_gaps


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract monster stat blocks from MM OCR text"
    )
    parser.add_argument(
        "--source-dir",
        default="sources/text/e390dfd9143f",
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

    if not source_dir.exists():
        log.error("Source directory not found: %s", source_dir)
        sys.exit(1)

    run_extraction(str(source_dir), str(output_dir))


if __name__ == "__main__":
    main()
