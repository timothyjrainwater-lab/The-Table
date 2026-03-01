"""Parse Obsidian SRD Markdown monster files into CreatureStatBlock data.

Produces Python code for creature_registry_ext.py containing novel creatures
not already in CREATURE_REGISTRY.

Run from repo root: python scripts/parse_obsidian_monsters.py
"""

import sys
import re
import os

sys.path.insert(0, ".")

from aidm.data.creature_registry import CREATURE_REGISTRY

MONSTER_FILES = [
    "scripts/oss_sources/obsidian_srd_markdown/Monsters/Monsters.md",
    "scripts/oss_sources/obsidian_srd_markdown/Monsters/Monsters - Animals.md",
    "scripts/oss_sources/obsidian_srd_markdown/Monsters/Monsters - Vermin.md",
]

OUT_PATH = "aidm/data/creature_registry_ext.py"


def creature_id_from_name(name):
    s = name.lower().strip()
    s = re.sub(r"[',/\(\)\[\]]", "", s)
    s = re.sub(r"[\s\-\+]+", "_", s)
    s = s.strip("_")
    s = re.sub(r"_+", "_", s)
    return s


def extract_first_col(line):
    """Extract first column value from a two-column stat table line.

    Splits at 10+ consecutive spaces after the label colon.
    """
    # Remove leading whitespace
    s = line.strip()
    # Get value after colon
    if ":" in s:
        s = s.split(":", 1)[1].lstrip()
    # Split at long whitespace gap to get only first column
    s = re.split(r"\s{8,}", s)[0].strip()
    return s


def parse_stat_block(lines):
    """Parse a monster stat block table from its lines. Returns dict of fields."""
    data = {}
    type_line_found = False

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("---"):
            continue

        # Type line: no leading label, starts with size
        if (not type_line_found
                and not re.match(r"[A-Z][a-z].*:", stripped)
                and re.match(r"(Fine|Diminutive|Tiny|Small|Medium|Large|Huge|Gargantuan|Colossal)\s", stripped)):
            # Take first column (split on large whitespace)
            type_val = re.split(r"\s{8,}", stripped)[0].strip()
            data["type_line"] = type_val
            type_line_found = True
            continue

        # Labeled fields
        m = re.match(r"([\w\s/]+):\s*(.*)", stripped)
        if not m:
            continue

        label = m.group(1).strip()
        raw_val = m.group(2)
        # Take first column only (split on long whitespace)
        val = re.split(r"\s{8,}", raw_val)[0].strip()

        label_lower = label.lower()
        if "hit dice" in label_lower:
            data["hit_dice"] = val
        elif "initiative" in label_lower:
            data["initiative"] = val
        elif "speed" in label_lower:
            data["speed"] = val
        elif "armor class" in label_lower:
            data["armor_class"] = val
        elif "base attack" in label_lower:
            data["base_attack"] = val
        elif "attack" == label_lower:
            data["attack"] = val
        elif "full attack" in label_lower:
            data["full_attack"] = val
        elif "saves" in label_lower:
            data["saves"] = val
        elif "abilities" in label_lower:
            data["abilities"] = val
        elif "challenge rating" in label_lower:
            data["cr"] = val
        elif "special qualities" in label_lower:
            data["special_qualities"] = val
        elif "special attacks" in label_lower:
            data["special_attacks"] = val

    return data


def parse_cr(cr_str):
    """Parse CR string to float."""
    cr_str = cr_str.strip()
    if "/" in cr_str:
        parts = cr_str.split("/")
        try:
            return float(parts[0]) / float(parts[1])
        except Exception:
            return 1.0
    try:
        return float(cr_str)
    except Exception:
        return 1.0


def parse_hp(hit_dice_str):
    """Extract HP from hit dice string like '6d8+12 (39 hp)'."""
    m = re.search(r"\((\d+)\s*hp\)", hit_dice_str, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # Estimate from dice if no parenthetical
    m2 = re.match(r"(\d+)d(\d+)([+-]\d+)?", hit_dice_str.strip())
    if m2:
        hd = int(m2.group(1))
        die = int(m2.group(2))
        bonus = int(m2.group(3)) if m2.group(3) else 0
        return int(hd * (die / 2 + 0.5) + bonus)
    return 10


def parse_ac(ac_str):
    """Extract total AC from 'XX (-Y size, +Z Dex, ...), touch ZZ, flat-footed ZZ'."""
    m = re.match(r"\s*(\d+)", ac_str)
    if m:
        return int(m.group(1))
    return 10


def parse_bab(bab_grapple_str):
    """Extract BAB from '+6/+22' style string."""
    m = re.match(r"[+-]?(\d+)", bab_grapple_str.strip())
    if m:
        return int(m.group(1))
    return 0


def parse_saves(saves_str):
    """Parse 'Fort +7, Ref +3, Will +11' → (fort, ref, will)."""
    fort = ref = will = 0
    m = re.search(r"Fort\s*([+-]\d+)", saves_str)
    if m:
        fort = int(m.group(1))
    m = re.search(r"Ref\s*([+-]\d+)", saves_str)
    if m:
        ref = int(m.group(1))
    m = re.search(r"Will\s*([+-]\d+)", saves_str)
    if m:
        will = int(m.group(1))
    return fort, ref, will


def parse_abilities(ab_str):
    """Parse 'Str 26, Dex 12, Con 20, Int 15, Wis 17, Cha 17' → dict."""
    result = {"str": 10, "dex": 10, "con": 10, "int": 10, "wis": 10, "cha": 10}
    for key, pattern in [("str", r"Str\s+(\d+)"), ("dex", r"Dex\s+(\d+)"),
                          ("con", r"Con\s+(\d+)"), ("int", r"Int\s+(\d+)"),
                          ("wis", r"Wis\s+(\d+)"), ("cha", r"Cha\s+(\d+)")]:
        m = re.search(pattern, ab_str)
        if m:
            result[key] = int(m.group(1))
        elif "---" in ab_str:
            result[key] = 0  # mindless/undead marker
    return result


def parse_type_line(type_line):
    """Parse 'Large Outsider (Evil, Extraplanar, Lawful)' → (size, creature_type)."""
    SIZE_WORDS = ["fine", "diminutive", "tiny", "small", "medium", "large",
                  "huge", "gargantuan", "colossal"]
    TYPES = ["aberration", "animal", "construct", "dragon", "elemental", "fey",
             "giant", "humanoid", "magical beast", "monstrous humanoid",
             "ooze", "outsider", "plant", "undead", "vermin"]

    size = "medium"
    creature_type = "magical beast"

    tl = type_line.lower()
    for s in SIZE_WORDS:
        if s in tl:
            size = s
            break

    for t in TYPES:
        if t in tl:
            creature_type = t
            break

    return size, creature_type


def parse_attack(atk_str):
    """Parse attack line into structured dict."""
    if not atk_str or atk_str == "---":
        return []

    # Try to extract: 'Claw +9 melee (2d6+4)'
    attacks = []
    # Handle multiple attacks (from Full Attack)
    parts = re.split(r"\band\b", atk_str)
    for part in parts:
        part = part.strip()
        m = re.match(r"([\w\s]+?)\s+([+-]\d+)\s+(?:melee|ranged)?\s*(?:touch\s*)?\(?(\d+d\d+[+-]?\d*)\)?", part, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            bonus = int(m.group(2))
            damage = m.group(3)
            dtype = "slashing"
            if "claw" in name.lower() or "talon" in name.lower():
                dtype = "slashing"
            elif "bite" in name.lower() or "sting" in name.lower():
                dtype = "piercing"
            elif "slam" in name.lower() or "fist" in name.lower():
                dtype = "bludgeoning"
            elif "tentacle" in name.lower():
                dtype = "bludgeoning"
            attacks.append({
                "name": name,
                "attack_bonus": bonus,
                "damage_dice": damage,
                "damage_type": dtype,
            })
    return attacks


def parse_monster_section(name, section_text):
    """Parse one ## section and return CreatureStatBlock kwargs or None."""
    # Find the table (between separator lines)
    lines = section_text.split("\n")
    in_table = False
    table_lines = []
    type_line_raw = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("---") and len(stripped) > 10:
            if not in_table:
                in_table = True
            else:
                break
            continue
        if in_table:
            table_lines.append(line)
            # Detect type line (no label, starts with size word)
            if (not type_line_raw
                    and re.match(r"\s+(Fine|Diminutive|Tiny|Small|Medium|Large|Huge|Gargantuan|Colossal)\s", line)):
                type_line_raw = re.split(r"\s{8,}", line.strip())[0].strip()

    if not table_lines:
        return None

    data = parse_stat_block(table_lines)
    if type_line_raw:
        data["type_line"] = type_line_raw

    # Require CR at minimum
    cr_str = data.get("cr")
    if not cr_str or cr_str in ("---", "—"):
        return None

    cr = parse_cr(cr_str)
    hp = parse_hp(data.get("hit_dice", ""))
    if hp <= 0:
        return None

    ac = parse_ac(data.get("armor_class", "10"))
    bab = parse_bab(data.get("base_attack", "0"))
    fort, ref, will = parse_saves(data.get("saves", ""))
    abilities = parse_abilities(data.get("abilities", ""))
    size, creature_type = parse_type_line(data.get("type_line", "medium magical beast"))

    # Use full_attack if available, else attack
    atk_str = data.get("full_attack") or data.get("attack") or ""
    attacks = parse_attack(atk_str)

    # Special qualities
    sq = data.get("special_qualities", "")
    sq_list = [s.strip() for s in sq.split(",") if s.strip() and s.strip() != "---"] if sq else []

    cid = creature_id_from_name(name)

    return {
        "creature_id": cid,
        "name": name,
        "creature_type": creature_type,
        "size": size,
        "hp": hp,
        "ac": ac,
        "bab": bab,
        "fort": fort,
        "ref": ref,
        "will": will,
        "str_score": abilities["str"],
        "dex_score": abilities["dex"],
        "con_score": abilities["con"],
        "int_score": abilities["int"],
        "wis_score": abilities["wis"],
        "cha_score": abilities["cha"],
        "attacks": attacks,
        "cr": cr,
        "special_qualities": sq_list,
    }


def format_creature(d):
    """Format a creature dict as Python code for CreatureStatBlock."""
    atks = d["attacks"]
    atk_str = repr(atks)
    sq_str = repr(d["special_qualities"])
    cr_val = d["cr"]
    cr_repr = f"{cr_val}" if cr_val == int(cr_val) else repr(cr_val)

    return f'''    {d["creature_id"]!r}: CreatureStatBlock(
        creature_id={d["creature_id"]!r}, name={d["name"]!r},
        creature_type={d["creature_type"]!r}, size={d["size"]!r},
        hp={d["hp"]}, ac={d["ac"]}, bab={d["bab"]},
        fort={d["fort"]}, ref={d["ref"]}, will={d["will"]},
        str_score={d["str_score"]}, dex_score={d["dex_score"]},
        con_score={d["con_score"]}, int_score={d["int_score"]},
        wis_score={d["wis_score"]}, cha_score={d["cha_score"]},
        attacks={atk_str},
        cr={cr_repr},
        special_qualities={sq_str},
    ),'''


def main():
    current_ids = set(CREATURE_REGISTRY.keys())
    novel = []
    failed = []

    for fpath in MONSTER_FILES:
        with open(fpath, encoding="utf-8", errors="replace") as f:
            content = f.read()

        sections = re.split(r"\n## ", content)
        print(f"\n{os.path.basename(fpath)}: {len(sections)-1} sections")

        for sec in sections[1:]:
            lines = sec.split("\n")
            name = lines[0].strip()
            if not name:
                continue
            cid = creature_id_from_name(name)
            if cid in current_ids or cid in {d["creature_id"] for d in novel}:
                continue

            result = parse_monster_section(name, sec)
            if result:
                novel.append(result)
            else:
                failed.append(name)

    print(f"\nParsed: {len(novel)} novel creatures")
    print(f"Failed/skipped: {len(failed)} ({failed[:10]}...)")

    header = '''"""Extension creature stat blocks — auto-generated by scripts/parse_obsidian_monsters.py.

Source: Obsidian-TTRPG-Community/DnD-3.5-SRD-Markdown (Monsters.md, Animals, Vermin)
        CC0 / Open Game License — facts not copyrightable

Heuristically parsed stat blocks. Key stats (CR, HP, AC, saves, abilities) are from
source text. Attack parsing may be incomplete for complex multi-attack entries.

DO NOT EDIT MANUALLY — regenerate with: python scripts/parse_obsidian_monsters.py
Generated: {count} novel entries.

WO4 / STRAT-OSS-INGESTION-SPRINT-001
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from aidm.data.creature_registry import CreatureStatBlock

CREATURE_REGISTRY_EXT: dict = {{
'''.format(count=len(novel))

    footer = "}\n"

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(header)
        for d in novel:
            try:
                f.write(format_creature(d) + "\n")
            except Exception as e:
                print(f"  Error formatting {d.get('name')}: {e}")
        f.write(footer)

    print(f"\nWrote {len(novel)} creatures to {OUT_PATH}")


if __name__ == "__main__":
    main()
