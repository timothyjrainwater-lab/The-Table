"""Generate spell_definitions_ext.py from PCGen rsrd_spells.lst.

Produces stub SpellDefinition entries for the 514 spells not already in SPELL_REGISTRY.
Stubs have correct school/level/save/component/SR fields from PCGen data;
damage_dice/damage_type/target details inferred heuristically from descriptor and
target_area text. Existing fully-detailed entries in spell_definitions.py are unchanged.

Run from repo root: python scripts/gen_spell_defs_ext.py
"""

import sys
import re
import os

sys.path.insert(0, ".")
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from parse_pcgen_lst import parse_lst_file, extract_spells
from aidm.data.spell_definitions import SPELL_REGISTRY

LST_PATH = "scripts/oss_sources/pcgen_sparse/data/35e/wizards_of_the_coast/rsrd/basics/rsrd_spells.lst"
OUT_PATH = "aidm/data/spell_definitions_ext.py"


def spell_id_from_name(name):
    s = name.lower().strip()
    s = re.sub(r"[',/]", "", s)
    s = re.sub(r"[\s\-\(\)]+", "_", s)
    s = s.strip("_")
    return s


def infer_target_type(spell):
    area = (spell.get("target_area") or "").lower()
    if any(kw in area for kw in ["burst", "radius", "spread", "emanation", "-ft.", "area", "cloud", "cylinder"]):
        return "SpellTarget.AREA"
    if "ray" in area:
        return "SpellTarget.RAY"
    if "touch" in area:
        return "SpellTarget.TOUCH"
    if "personal" in area or area.startswith("you ") or area == "you":
        return "SpellTarget.SELF"
    return "SpellTarget.SINGLE"


def infer_effect_type(spell):
    name = (spell.get("name") or "").lower()
    school = (spell.get("school") or "").lower()
    desc = (spell.get("descriptor") or "").lower()
    if any(kw in name for kw in ["cure", "heal", "restoration", "regenerate", "vigor"]):
        return "SpellEffect.HEALING"
    dmg_descs = ["fire", "cold", "acid", "electricity", "sonic", "force", "negative energy"]
    if any(d in desc for d in dmg_descs) or (school == "evocation" and any(d in desc for d in dmg_descs)):
        return "SpellEffect.DAMAGE"
    if school == "necromancy" and any(kw in name for kw in ["drain", "touch", "bolt", "arrow"]):
        return "SpellEffect.DAMAGE"
    if school == "abjuration":
        return "SpellEffect.BUFF"
    buff_kws = ["bless", "bull", "barkskin", "bear", "eagle", "haste", "heroism", "prayer",
                "resistance", "endurance", "cat", "fox", "owl", "shield", "stoneskin", "mage armor",
                "aid", "magic fang", "magic vestment", "divine favor", "divine power"]
    if any(kw in name for kw in buff_kws):
        return "SpellEffect.BUFF"
    debuff_kws = ["hold", "slow", "blind", "fear", "confusion", "stun", "paralyze", "entangle",
                  "sleep", "charm", "dominate", "deep slumber", "bane", "bestow curse"]
    if any(kw in name for kw in debuff_kws):
        return "SpellEffect.DEBUFF"
    return "SpellEffect.UTILITY"


def infer_damage_type(spell, effect_type):
    if effect_type not in ("SpellEffect.DAMAGE", "SpellEffect.HEALING"):
        return "None"
    desc = (spell.get("descriptor") or "").lower()
    name = (spell.get("name") or "").lower()
    school = (spell.get("school") or "").lower()
    for dtype, kw in [("FIRE", "fire"), ("COLD", "cold"), ("ACID", "acid"),
                      ("ELECTRICITY", "electricity"), ("SONIC", "sonic"), ("FORCE", "force")]:
        if kw in desc or kw in name:
            return f"DamageType.{dtype}"
    if effect_type == "SpellEffect.HEALING":
        return "DamageType.POSITIVE"
    if school == "necromancy":
        return "DamageType.NEGATIVE"
    return "None"


def infer_aoe(spell, target_type):
    if target_type != "SpellTarget.AREA":
        return "None", "None", "None"
    area = (spell.get("target_area") or "").lower()
    if "cone" in area:
        shape = "AoEShape.CONE"
        direction = "AoEDirection.N"
    elif "line" in area:
        shape = "AoEShape.LINE"
        direction = "AoEDirection.N"
    else:
        shape = "AoEShape.BURST"
        direction = "None"
    m = re.search(r"(\d+)\s*(?:\-|\s)*ft", area)
    radius = m.group(1) if m else "None"
    return shape, radius, direction


def infer_save_effect(spell, effect_type, save_type_str):
    if save_type_str == "None":
        return "SaveEffect.NONE"
    if effect_type == "SpellEffect.DAMAGE":
        return "SaveEffect.HALF"
    return "SaveEffect.NEGATES"


SAVE_TYPE_MAP = {
    "Will": "SaveType.WILL",
    "Fortitude": "SaveType.FORT",
    "Reflex": "SaveType.REF",
    None: "None",
    "": "None",
    "None": "None",
}


def main():
    lines = parse_lst_file(LST_PATH)
    pcgen_spells = extract_spells(lines)
    print(f"PCGen spells: {len(pcgen_spells)}")

    current_ids = set(SPELL_REGISTRY.keys())
    novel = []
    for s in pcgen_spells:
        sid = spell_id_from_name(s["name"])
        if sid not in current_ids:
            novel.append((sid, s))

    print(f"Novel spells to add: {len(novel)}")
    print(f"Writing to {OUT_PATH}")

    header = '''"""Extension spell definitions — auto-generated by scripts/gen_spell_defs_ext.py.

Source: PCGen rsrd_spells.lst (CC0 / Open Game License)
        scripts/oss_sources/pcgen_sparse/data/35e/wizards_of_the_coast/rsrd/basics/rsrd_spells.lst

These are stub entries with heuristically-inferred target_type / effect_type / damage_type.
PHB-critical spells (fireball, cure wounds, etc.) remain in spell_definitions.py with full fidelity.

DO NOT EDIT MANUALLY — regenerate with: python scripts/gen_spell_defs_ext.py
Generated: {count} novel entries (spells not already in SPELL_REGISTRY).

WO2 / STRAT-OSS-INGESTION-SPRINT-001
"""

from aidm.core.spell_resolver import (
    SpellDefinition, SpellTarget, SpellEffect, SaveEffect, DamageType
)
from aidm.core.aoe_rasterizer import AoEShape, AoEDirection
from aidm.schemas.saves import SaveType

SPELL_REGISTRY_EXT: dict = {{
'''.format(count=len(novel))

    footer = "}\n"

    lines_out = [header]

    for sid, s in novel:
        name = s["name"]
        level = s.get("level", 0)
        school = (s.get("school") or "universal").lower()
        save_raw = s.get("save_type") or s.get("save_raw") or "None"
        save_type_str = SAVE_TYPE_MAP.get(save_raw, "None")
        has_v = s.get("has_verbal", True)
        has_s = s.get("has_somatic", True)
        sr = s.get("spell_resistance", False)
        range_ft = s.get("range_ft", 30) or 30
        dur = s.get("duration_rounds", 0) or 0

        target_type = infer_target_type(s)
        effect_type = infer_effect_type(s)
        dmg_type = infer_damage_type(s, effect_type)
        aoe_shape, aoe_radius, aoe_dir = infer_aoe(s, target_type)
        save_effect = infer_save_effect(s, effect_type, save_type_str)

        entry = f'''    {sid!r}: SpellDefinition(
        spell_id={sid!r},
        name={name!r},
        level={level},
        school={school!r},
        target_type={target_type},
        range_ft={range_ft},
        aoe_shape={aoe_shape},
        aoe_radius_ft={aoe_radius},
        aoe_direction={aoe_dir},
        effect_type={effect_type},
        damage_type={dmg_type},
        save_type={save_type_str},
        save_effect={save_effect},
        duration_rounds={dur},
        has_verbal={has_v},
        has_somatic={has_s},
        spell_resistance={sr},
        rule_citations=("PHB",),
    ),
'''
        lines_out.append(entry)

    lines_out.append(footer)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write("".join(lines_out))

    print(f"Done. Wrote {len(novel)} stubs to {OUT_PATH}")


if __name__ == "__main__":
    main()
