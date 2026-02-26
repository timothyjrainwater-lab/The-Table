#!/usr/bin/env python3
"""PCGen LST file parser — one-time offline data extraction tool.

Parses PCGen RSRD LST files into JSON for use by data ingestion WOs.
Artifact: LST-PARSER-001 (OSS Data Batch A)

Usage:
    python parse_pcgen_lst.py rsrd_spells.lst --type spells --output data/pcgen_extracted/spells_raw.json
    python parse_pcgen_lst.py rsrd_equip.lst --type armor --output data/pcgen_extracted/armor_raw.json
    python parse_pcgen_lst.py rsrd_classes.lst --type classes --output data/pcgen_extracted/class_tables_raw.json
    python parse_pcgen_lst.py rsrd_feats.lst --type feats --output data/pcgen_extracted/feats_raw.json

PCGen LST format (pipe-delimited key-value):
  - Each entry starts at column 0: EntityName\\tTAG1:value1\\tTAG2:value2...
  - Lines beginning with '#' are comments — skipped
  - Lines beginning with whitespace continue the previous entry (tag merging)
  - Blank lines are ignored

Source files (PCGen repo path: data/35e/wizards_of_the_coast/rsrd/basics/):
  - rsrd_spells.lst
  - rsrd_equip.lst
  - rsrd_classes.lst
  - rsrd_feats.lst
  - rsrd_abilities_class.lst  (453KB — hand-extract only, not parsed here)

This script never runs in production. No pytest gate. Human spot-check only.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ==============================================================================
# BASE PARSER
# ==============================================================================

def parse_lst_file(filepath: str) -> List[Dict]:
    """Parse a PCGen LST file into a list of {name, tags} dicts.

    Each non-comment, non-blank line starting at column 0 begins a new entry.
    Lines beginning with whitespace or TAB continue the previous entry.

    Returns:
        List of dicts: [{"name": str, "tags": {str: str}}, ...]
    """
    entries = []
    current: Optional[Dict] = None

    with open(filepath, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")

            # Skip blank lines
            if not line.strip():
                continue

            # Skip comment lines
            if line.startswith("#") or line.startswith("!"):
                continue

            # Continuation line (starts with whitespace/tab)
            if line[0] in (" ", "\t") and current is not None:
                _merge_tags(current["tags"], line.strip())
                continue

            # SOURCE: lines are metadata, not entries
            if line.startswith("SOURCE"):
                continue

            # New entry: EntityName\tTAG:val\tTAG:val...
            if "\t" in line:
                name, _, rest = line.partition("\t")
                current = {"name": name.strip(), "tags": {}}
                _merge_tags(current["tags"], rest)
                entries.append(current)
            else:
                # Line with no tabs — may be a bare name or CLASS: header
                stripped = line.strip()
                if stripped:
                    current = {"name": stripped, "tags": {}}
                    entries.append(current)

    return entries


def _merge_tags(tags: Dict[str, str], tag_string: str) -> None:
    """Parse tab-separated TAG:value pairs and merge into tags dict.

    Handles:
    - Simple: SCHOOL:Evocation
    - Multi-value: CLASSES:Wizard=3,Sorcerer=3
    - Empty value: SUBSCHOOL:
    """
    for part in tag_string.split("\t"):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            key, _, value = part.partition(":")
            tags[key.strip()] = value.strip()
        # Parts without ':' are continuation modifiers — skip for now


# ==============================================================================
# SPELL EXTRACTION
# ==============================================================================

def parse_comps(comps_str: str) -> Tuple[bool, bool, bool]:
    """Parse COMPS string → (has_verbal, has_somatic, has_material).

    Examples:
        'V,S,M'  → (True, True, True)
        'V,S'    → (True, True, False)
        'V'      → (True, False, False)
        'V,M'    → (True, False, True)
        'S,M'    → (False, True, True)
        'DF'     → (False, False, False)  # Divine Focus only
    """
    if not comps_str:
        return (False, False, False)
    parts = [c.strip().upper() for c in comps_str.split(",")]
    has_v = "V" in parts
    has_s = "S" in parts
    has_m = any(p in ("M", "M/DF") or p.startswith("M") for p in parts)
    return has_v, has_s, has_m


def parse_range(range_str: str) -> int:
    """Parse RANGE tag to approximate feet value.

    PHB range categories:
        Touch       → 0
        Close       → 25
        Medium      → 100
        Long        → 400
        Personal    → 0
    """
    if not range_str:
        return 0
    r = range_str.lower()
    if r.startswith("touch"):
        return 0
    if r.startswith("personal"):
        return 0
    if r.startswith("close"):
        return 25
    if r.startswith("medium"):
        return 100
    if r.startswith("long"):
        return 400
    # Try to parse explicit feet: e.g. "30 ft."
    m = re.search(r"(\d+)\s*ft", r)
    if m:
        return int(m.group(1))
    return 0


def parse_duration(duration_str: str) -> int:
    """Parse DURATION tag to approximate rounds.

    Returns 0 for Instantaneous, 10 for per-level, etc.
    """
    if not duration_str:
        return 0
    d = duration_str.lower()
    if "instantaneous" in d:
        return 0
    if "permanent" in d or "until discharged" in d:
        return 9999
    if "concentration" in d:
        return -1  # -1 signals concentration
    # round/level → use 10 rounds (level 10 baseline)
    if "round" in d and "level" in d:
        return 10
    # minute/level
    if "minute" in d and "level" in d:
        return 100  # 10 minutes * 10 rounds
    # hour/level
    if "hour" in d and "level" in d:
        return 600
    # day/level
    if "day" in d and "level" in d:
        return 1440
    # Fixed rounds
    m = re.search(r"(\d+)\s*round", d)
    if m:
        return int(m.group(1))
    return 0


def parse_save(save_str: str) -> Optional[str]:
    """Parse SAVEINFO tag to canonical save type string.

    Returns: 'fort', 'ref', 'will', or None.
    """
    if not save_str or save_str.lower() in ("none", "no"):
        return None
    s = save_str.lower()
    if "fortitude" in s or "fort" in s:
        return "fort"
    if "reflex" in s or "ref" in s:
        return "ref"
    if "will" in s:
        return "will"
    return None


def parse_classes(classes_str: str) -> Dict[str, int]:
    """Parse CLASSES tag to dict of {class_name: level}.

    Example: 'Wizard=3,Sorcerer=3' → {'Wizard': 3, 'Sorcerer': 3}
    """
    result = {}
    if not classes_str:
        return result
    # Remove any leading 'TYPE=' or 'PRECLASS' qualifiers
    for part in classes_str.split(","):
        part = part.strip()
        if "=" in part:
            name, _, level_str = part.partition("=")
            try:
                result[name.strip()] = int(level_str.strip())
            except ValueError:
                pass
    return result


def extract_spells(entries: List[Dict]) -> List[Dict]:
    """Extract spell data from parsed rsrd_spells.lst entries.

    Returns list of dicts with:
        name, level (min class level), class_levels (dict),
        school, has_verbal, has_somatic, has_material,
        casttime, range_ft, duration_rounds, save_type, spell_resistance
    """
    spells = []
    for entry in entries:
        tags = entry.get("tags", {})
        name = entry.get("name", "")

        # Skip non-spell entries (class headers, etc.)
        if not name or "CLASS:" in name:
            continue

        classes = parse_classes(tags.get("CLASSES", "") or tags.get("CLASS", ""))
        if not classes and not tags.get("SCHOOL"):
            continue  # Likely not a spell entry

        min_level = min(classes.values()) if classes else 0
        has_v, has_s, has_m = parse_comps(tags.get("COMPS", "") or tags.get("COMP", ""))

        spells.append({
            "name": name,
            "level": min_level,
            "class_levels": classes,
            "school": (tags.get("SCHOOL", "") or "").lower(),
            "subschool": (tags.get("SUBSCHOOL", "") or "").lower(),
            "descriptor": tags.get("DESCRIPTOR", "") or "",
            "has_verbal": has_v,
            "has_somatic": has_s,
            "has_material": has_m,
            "casttime": tags.get("CASTTIME", "") or "",
            "range_ft": parse_range(tags.get("RANGE", "") or ""),
            "range_raw": tags.get("RANGE", "") or "",
            "duration_rounds": parse_duration(tags.get("DURATION", "") or ""),
            "duration_raw": tags.get("DURATION", "") or "",
            "save_type": parse_save(tags.get("SAVEINFO", "") or ""),
            "save_raw": tags.get("SAVEINFO", "") or "",
            "spell_resistance": (tags.get("SPELLRES", "") or "").lower() == "yes",
            "target_area": tags.get("TARGETAREA", "") or "",
        })

    return spells


# ==============================================================================
# ARMOR/EQUIPMENT EXTRACTION
# ==============================================================================

def extract_armor(entries: List[Dict]) -> List[Dict]:
    """Extract armor data from parsed rsrd_equip.lst entries.

    Filters for entries with TYPE containing 'Armor' or 'Shield'.
    Returns list of dicts with:
        name, armor_type, spell_failure, max_dex, armor_check_penalty,
        ac_bonus, weight_lb
    """
    armors = []
    for entry in entries:
        tags = entry.get("tags", {})
        name = entry.get("name", "")
        entry_type = tags.get("TYPE", "")

        # Only process armor/shield entries
        type_parts = entry_type.split(".")
        is_armor = "Armor" in type_parts
        is_shield = "Shield" in type_parts
        if not (is_armor or is_shield):
            continue

        # Determine armor category
        armor_type = "none"
        if "Heavy" in type_parts:
            armor_type = "heavy"
        elif "Medium" in type_parts:
            armor_type = "medium"
        elif "Light" in type_parts:
            armor_type = "light"
        elif is_shield:
            armor_type = "shield"

        # Parse numeric fields
        def _int(key: str, default: int = 0) -> int:
            try:
                return int(tags.get(key, default))
            except (ValueError, TypeError):
                return default

        def _float(key: str, default: float = 0.0) -> float:
            try:
                return float(tags.get(key, default))
            except (ValueError, TypeError):
                return default

        armors.append({
            "name": name,
            "armor_type": armor_type,
            "arcane_spell_failure": _int("SPELLFAILURE"),
            "max_dex_bonus": _int("MAXDEX", 99),   # 99 = no limit
            "armor_check_penalty": _int("ACCHECK"),  # Negative value
            "ac_bonus": _int("ACCHECK", 0),          # Note: PCGen uses separate tag
            "weight_lb": _float("WT"),
            "cost_gp": _float("COST"),
        })

    return armors


# ==============================================================================
# FEAT EXTRACTION
# ==============================================================================

def extract_feats_prereqs(entries: List[Dict]) -> List[Dict]:
    """Extract feat prerequisite data from parsed rsrd_feats.lst entries.

    Returns list of dicts with:
        name, prereq_feats (list), prereq_stats (dict), prereq_bab
    """
    feats = []
    for entry in entries:
        tags = entry.get("tags", {})
        name = entry.get("name", "")
        if not name or name.startswith("CLASS:"):
            continue

        # PREFEAT:1,feat_name style
        prereq_feats = []
        for key, val in tags.items():
            if key.startswith("PREFEAT"):
                # Format: PREFEAT:1,feat_name_1,feat_name_2
                parts = val.split(",")
                if len(parts) > 1:
                    try:
                        count = int(parts[0])
                        prereq_feats.extend(parts[1:count+1])
                    except ValueError:
                        prereq_feats.extend(parts)

        # PRESTAT:1,STR=13 style
        prereq_stats = {}
        for key, val in tags.items():
            if key.startswith("PRESTAT"):
                parts = val.split(",")
                for part in parts[1:]:  # Skip count
                    if "=" in part:
                        stat, _, score = part.partition("=")
                        try:
                            prereq_stats[stat.strip().lower()] = int(score.strip())
                        except ValueError:
                            pass

        # PREATT:n (base attack bonus)
        prereq_bab = 0
        if "PREATT" in tags:
            try:
                prereq_bab = int(tags["PREATT"])
            except ValueError:
                pass

        feat_type = tags.get("TYPE", "General")

        feats.append({
            "name": name,
            "feat_type": feat_type,
            "prereq_feats": prereq_feats,
            "prereq_stats": prereq_stats,
            "prereq_bab": prereq_bab,
        })

    return feats


# ==============================================================================
# CLASS TABLE EXTRACTION
# ==============================================================================

def _parse_cast_tag(cast_str: str) -> Dict[int, Tuple]:
    """Parse CAST: tag into dict of {level: (slot_0, slot_1, ...)}.

    Format: level1_data|level2_data|...
    Each level_data: slot0,slot1,slot2,...

    Example: '3,1|4,2|4,2,1' → {1: (3,1), 2: (4,2), 3: (4,2,1)}
    """
    result = {}
    if not cast_str:
        return result
    for i, level_data in enumerate(cast_str.split("|"), start=1):
        try:
            slots = tuple(int(x) for x in level_data.split(","))
            result[i] = slots
        except ValueError:
            pass
    return result


def _parse_udam_tag(udam_str: str) -> Dict[int, str]:
    """Parse UDAM: tag into dict of {level: damage_string}.

    Monk UDAM format from PCGen: pipe-separated per class level,
    each value is a damage die string (may vary by creature size).
    We extract the medium-size value (typically index 1 in size array).

    Example: '1d6,1d8|1d6,1d8|1d8,1d10|...' → {1: '1d6', 2: '1d6', 3: '1d8', ...}
    Format uncertainty documented in LST-PARSER-001 WO — verify against actual file.
    """
    result = {}
    if not udam_str:
        return result
    # Try pipe-separated (one per level)
    levels = udam_str.split("|")
    if len(levels) > 1:
        for i, level_data in enumerate(levels, start=1):
            parts = level_data.split(",")
            # Use second value (medium size) if multiple size columns present
            if len(parts) >= 2:
                result[i] = parts[1].strip()  # medium
            elif parts:
                result[i] = parts[0].strip()
        return result
    # Fallback: comma-separated (single row)
    parts = udam_str.split(",")
    for i, p in enumerate(parts, start=1):
        result[i] = p.strip()
    return result


def extract_class_tables(entries: List[Dict]) -> Dict:
    """Extract class progression tables from parsed rsrd_classes.lst entries.

    Returns dict by class name:
        {class_name: {
            "spell_slots_per_day": {level: tuple},
            "spells_known": {level: tuple},
            "udam": {level: str},
        }}
    """
    classes = {}
    for entry in entries:
        tags = entry.get("tags", {})
        name = entry.get("name", "")

        # Class header lines look like 'CLASS:Wizard' or just the class name
        # with CAST: tags
        class_name = None
        if name.startswith("CLASS:"):
            class_name = name[len("CLASS:"):].strip()
        elif "CAST" in tags or "UDAM" in tags or "KNOWN" in tags:
            class_name = name.strip()

        if not class_name:
            continue

        if class_name not in classes:
            classes[class_name] = {
                "spell_slots_per_day": {},
                "spells_known": {},
                "udam": {},
            }

        if "CAST" in tags:
            classes[class_name]["spell_slots_per_day"].update(
                _parse_cast_tag(tags["CAST"])
            )

        if "KNOWN" in tags:
            classes[class_name]["spells_known"].update(
                _parse_cast_tag(tags["KNOWN"])
            )

        if "UDAM" in tags:
            classes[class_name]["udam"].update(
                _parse_udam_tag(tags["UDAM"])
            )

    return classes


# ==============================================================================
# CLI
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Parse PCGen LST files into JSON for AIDM data ingestion."
    )
    parser.add_argument("lst_file", help="Path to the PCGen .lst file")
    parser.add_argument(
        "--type",
        choices=["spells", "armor", "classes", "feats", "raw"],
        default="raw",
        help="Extraction type. 'raw' dumps all parsed entries without domain extraction.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file path. Defaults to stdout.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON output (default: True).",
    )
    args = parser.parse_args()

    lst_path = Path(args.lst_file)
    if not lst_path.exists():
        print(f"ERROR: File not found: {lst_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {lst_path}...", file=sys.stderr)
    entries = parse_lst_file(str(lst_path))
    print(f"  → {len(entries)} raw entries parsed.", file=sys.stderr)

    # Extract domain data
    if args.type == "spells":
        data = extract_spells(entries)
        print(f"  → {len(data)} spell entries extracted.", file=sys.stderr)
    elif args.type == "armor":
        data = extract_armor(entries)
        print(f"  → {len(data)} armor entries extracted.", file=sys.stderr)
    elif args.type == "classes":
        data = extract_class_tables(entries)
        print(f"  → {len(data)} class tables extracted.", file=sys.stderr)
    elif args.type == "feats":
        data = extract_feats_prereqs(entries)
        print(f"  → {len(data)} feat entries extracted.", file=sys.stderr)
    else:
        data = entries  # raw dump

    # Output
    indent = 2 if args.pretty else None
    json_str = json.dumps(data, indent=indent, default=str)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_str, encoding="utf-8")
        print(f"Output written to: {out_path}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
