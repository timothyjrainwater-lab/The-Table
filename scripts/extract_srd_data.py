#!/usr/bin/env python3
"""
WO-DATA-SRD-EXTRACT-001: Extract 3.5e SRD skill data from dnd-generator phb/skills.json.
Source: zellfaze-zz/dnd-generator (CC0/OGL)
Output: aidm/data/srd_skills.json, aidm/data/srd_dc_ranges.json

FIELD MAPPING NOTE (actual source structure, differs from spec template):
  Source is a LIST of objects (not a dict).
  Source fields:
    name        -> name  (lowercase, spaces -> underscores)
    key         -> ability  (lowercase; e.g. "Int" -> "int")
    trained     -> trained_only  (boolean)
    armorcheck  -> armor_check_penalty  (boolean)
    synergy     -> synergy  (list; each entry normalized: lowercase, spaces -> underscores)
"""
import json
import sys
from pathlib import Path

SOURCE_PATH = Path("scripts/phb_source/skills.json")
OUT_SKILLS = Path("aidm/data/srd_skills.json")
OUT_DC = Path("aidm/data/srd_dc_ranges.json")


def _norm_name(s: str) -> str:
    return s.lower().replace(" ", "_")


def extract_skills(raw: list) -> list:
    skills = []
    for entry in raw:
        name = _norm_name(entry.get("name", ""))
        ability = entry.get("key", "").lower()
        trained_only = bool(entry.get("trained", False))
        acp = bool(entry.get("armorcheck", False))
        raw_synergy = entry.get("synergy", [])
        synergy = sorted(_norm_name(s) for s in raw_synergy if s)
        skills.append({
            "ability": ability,
            "armor_check_penalty": acp,
            "name": name,
            "synergy": synergy,
            "trained_only": trained_only,
        })
    return sorted(skills, key=lambda s: s["name"])


def main():
    if not SOURCE_PATH.exists():
        print(f"ERROR: source not found: {SOURCE_PATH}", file=sys.stderr)
        sys.exit(1)
    if not OUT_SKILLS.parent.exists():
        print(f"ERROR: output dir not found: {OUT_SKILLS.parent}", file=sys.stderr)
        sys.exit(1)
    raw = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    skills = extract_skills(raw)
    OUT_SKILLS.write_text(
        json.dumps(skills, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    dc_data = {"dc_max": 40, "dc_min": 5, "source": "PHB p.65"}
    OUT_DC.write_text(
        json.dumps(dc_data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(skills)} skills -> {OUT_SKILLS}")
    print(f"Wrote DC range [{dc_data['dc_min']}, {dc_data['dc_max']}] -> {OUT_DC}")


if __name__ == "__main__":
    main()
