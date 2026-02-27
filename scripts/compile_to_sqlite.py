#!/usr/bin/env python3
"""Compile all D&D 3.5e data sources into a single SQLite database.

WO-INFRA-SQLITE-CONSOLIDATION-001
Usage: python scripts/compile_to_sqlite.py [--output PATH]
Default output: aidm/data/dnd35_engine.db

No external dependencies — stdlib only (sqlite3, json, pathlib, inspect).
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ensure project root is on sys.path so `aidm.*` imports work
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
DEFAULT_DB = PROJECT_ROOT / "aidm" / "data" / "dnd35_engine.db"

SPELLS_JSON = PROJECT_ROOT / "aidm" / "data" / "content_pack" / "spells.json"
FEATS_JSON = PROJECT_ROOT / "aidm" / "data" / "content_pack" / "feats.json"
CREATURES_JSON = PROJECT_ROOT / "aidm" / "data" / "content_pack" / "creatures.json"
EQUIPMENT_JSON = PROJECT_ROOT / "aidm" / "data" / "equipment_catalog.json"


def _load_json(path: Path) -> dict | list | None:
    """Load JSON file. Returns None on missing/malformed."""
    if not path.exists():
        print(f"  WARNING: {path.name} not found — skipping")
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"  WARNING: {path.name} malformed — {exc}")
        return None


# ───────────────────────────────────────────────────────────────────────────
# Table builders
# ───────────────────────────────────────────────────────────────────────────

def _build_spells(conn: sqlite3.Connection) -> int:
    """Table 1: spells + normalized tables."""
    data = _load_json(SPELLS_JSON)
    if data is None:
        return 0

    # spells.json is a top-level array
    entries = data if isinstance(data, list) else data.get("spells", data)
    if not isinstance(entries, list):
        print("  WARNING: spells.json unexpected shape — skipping")
        return 0

    conn.execute("DROP TABLE IF EXISTS spells")
    conn.execute("DROP TABLE IF EXISTS spell_descriptors")
    conn.execute("DROP TABLE IF EXISTS spell_class_levels")
    conn.execute("DROP TABLE IF EXISTS spell_conditions")

    conn.execute("""CREATE TABLE spells (
        template_id TEXT PRIMARY KEY,
        tier INTEGER,
        school_category TEXT,
        subschool TEXT,
        target_type TEXT,
        range_formula TEXT,
        effect_type TEXT,
        damage_formula TEXT,
        damage_type TEXT,
        healing_formula TEXT,
        save_type TEXT,
        save_effect TEXT,
        spell_resistance INTEGER,
        requires_attack_roll INTEGER,
        casting_time TEXT,
        duration_formula TEXT,
        concentration INTEGER,
        verbal INTEGER,
        somatic INTEGER,
        material INTEGER,
        source_page TEXT
    )""")
    conn.execute("""CREATE TABLE spell_descriptors (
        spell_id TEXT, descriptor TEXT
    )""")
    conn.execute("""CREATE TABLE spell_class_levels (
        spell_id TEXT, class_id TEXT, level INTEGER
    )""")
    conn.execute("""CREATE TABLE spell_conditions (
        spell_id TEXT, condition TEXT
    )""")

    count = 0
    for sp in entries:
        if not isinstance(sp, dict):
            continue
        tid = sp.get("template_id")
        if not tid:
            continue
        try:
            conn.execute(
                "INSERT OR REPLACE INTO spells VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    tid,
                    sp.get("tier"),
                    sp.get("school_category"),
                    sp.get("subschool"),
                    sp.get("target_type"),
                    sp.get("range_formula"),
                    sp.get("effect_type"),
                    sp.get("damage_formula"),
                    sp.get("damage_type"),
                    sp.get("healing_formula"),
                    sp.get("save_type"),
                    sp.get("save_effect"),
                    int(sp.get("spell_resistance", False)),
                    int(sp.get("requires_attack_roll", False)),
                    sp.get("casting_time"),
                    sp.get("duration_formula"),
                    int(sp.get("concentration", False)),
                    int(sp.get("verbal", False)),
                    int(sp.get("somatic", False)),
                    int(sp.get("material", False)),
                    sp.get("source_page"),
                ),
            )
            count += 1
        except Exception as exc:
            print(f"  WARNING: spell {tid} — {exc}")
            continue

        # Normalized: descriptors
        for desc in sp.get("descriptors", []):
            conn.execute(
                "INSERT INTO spell_descriptors VALUES (?,?)", (tid, desc)
            )
        # Normalized: class_levels — each entry is [class_name, level]
        for cl_entry in sp.get("class_levels", []):
            if isinstance(cl_entry, (list, tuple)) and len(cl_entry) >= 2:
                conn.execute(
                    "INSERT INTO spell_class_levels VALUES (?,?,?)",
                    (tid, cl_entry[0], cl_entry[1]),
                )
        # Normalized: conditions_applied
        for cond in sp.get("conditions_applied", []):
            conn.execute(
                "INSERT INTO spell_conditions VALUES (?,?)", (tid, cond)
            )

    return count


def _build_feats(conn: sqlite3.Connection) -> int:
    """Table 2: feats + normalized tables."""
    data = _load_json(FEATS_JSON)
    if data is None:
        return 0

    entries = data.get("feats", []) if isinstance(data, dict) else data
    if not isinstance(entries, list):
        print("  WARNING: feats.json unexpected shape — skipping")
        return 0

    conn.execute("DROP TABLE IF EXISTS feats")
    conn.execute("DROP TABLE IF EXISTS feat_prereq_ability")
    conn.execute("DROP TABLE IF EXISTS feat_prereq_feats")

    conn.execute("""CREATE TABLE feats (
        template_id TEXT PRIMARY KEY,
        feat_type TEXT,
        effect_type TEXT,
        bonus_value INTEGER,
        bonus_type TEXT,
        bonus_applies_to TEXT,
        prereq_bab INTEGER,
        prereq_caster_level INTEGER,
        fighter_bonus_eligible INTEGER,
        can_take_multiple INTEGER,
        metamagic_slot_increase INTEGER,
        source_page TEXT
    )""")
    conn.execute("""CREATE TABLE feat_prereq_ability (
        feat_id TEXT, ability TEXT, min_value INTEGER
    )""")
    conn.execute("""CREATE TABLE feat_prereq_feats (
        feat_id TEXT, required_feat_id TEXT
    )""")

    count = 0
    for ft in entries:
        if not isinstance(ft, dict):
            continue
        tid = ft.get("template_id")
        if not tid:
            continue
        try:
            conn.execute(
                "INSERT OR REPLACE INTO feats VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    tid,
                    ft.get("feat_type"),
                    ft.get("effect_type"),
                    ft.get("bonus_value"),
                    ft.get("bonus_type"),
                    ft.get("bonus_applies_to"),
                    ft.get("prereq_bab"),
                    ft.get("prereq_caster_level"),
                    int(ft.get("fighter_bonus_eligible", False)),
                    int(ft.get("can_take_multiple", False)),
                    ft.get("metamagic_slot_increase"),
                    ft.get("source_page"),
                ),
            )
            count += 1
        except Exception as exc:
            print(f"  WARNING: feat {tid} — {exc}")
            continue

        # Normalized: prereq_ability_scores
        for ability, min_val in ft.get("prereq_ability_scores", {}).items():
            conn.execute(
                "INSERT INTO feat_prereq_ability VALUES (?,?,?)",
                (tid, ability, min_val),
            )
        # Normalized: prereq_feat_refs
        for ref_id in ft.get("prereq_feat_refs", []):
            conn.execute(
                "INSERT INTO feat_prereq_feats VALUES (?,?)", (tid, ref_id)
            )

    return count


def _build_feat_registry(conn: sqlite3.Connection) -> int:
    """Table 3: feat_registry from aidm.schemas.feats.FEAT_REGISTRY."""
    try:
        from aidm.schemas.feats import FEAT_REGISTRY
    except ImportError as exc:
        print(f"  WARNING: could not import FEAT_REGISTRY — {exc}")
        return 0

    conn.execute("DROP TABLE IF EXISTS feat_registry")
    conn.execute("""CREATE TABLE feat_registry (
        feat_id TEXT PRIMARY KEY,
        name TEXT,
        modifier_type TEXT,
        phb_page INTEGER,
        description TEXT,
        prerequisites_json TEXT
    )""")

    count = 0
    for feat_id, feat_def in FEAT_REGISTRY.items():
        prereqs = getattr(feat_def, "prerequisites", {})
        conn.execute(
            "INSERT OR REPLACE INTO feat_registry VALUES (?,?,?,?,?,?)",
            (
                feat_id,
                getattr(feat_def, "name", ""),
                getattr(feat_def, "modifier_type", ""),
                getattr(feat_def, "phb_page", None),
                getattr(feat_def, "description", ""),
                json.dumps(prereqs, sort_keys=True) if prereqs else "{}",
            ),
        )
        count += 1
    return count


def _build_creatures(conn: sqlite3.Connection) -> int:
    """Table 4: creatures + normalized tables."""
    data = _load_json(CREATURES_JSON)
    if data is None:
        return 0

    entries = data.get("creatures", []) if isinstance(data, dict) else data
    if not isinstance(entries, list):
        print("  WARNING: creatures.json unexpected shape — skipping")
        return 0

    conn.execute("DROP TABLE IF EXISTS creatures")
    conn.execute("DROP TABLE IF EXISTS creature_subtypes")
    conn.execute("DROP TABLE IF EXISTS creature_attacks")
    conn.execute("DROP TABLE IF EXISTS creature_special_qualities")

    conn.execute("""CREATE TABLE creatures (
        template_id TEXT PRIMARY KEY,
        size_category TEXT,
        creature_type TEXT,
        hit_dice TEXT,
        hp_typical INTEGER,
        ac_total INTEGER,
        ac_touch INTEGER,
        ac_flat_footed INTEGER,
        bab INTEGER,
        fort_save INTEGER,
        ref_save INTEGER,
        will_save INTEGER,
        str_score INTEGER,
        dex_score INTEGER,
        con_score INTEGER,
        int_score INTEGER,
        wis_score INTEGER,
        cha_score INTEGER,
        cr REAL,
        speed_ft INTEGER,
        space_ft INTEGER,
        reach_ft INTEGER,
        source_page TEXT
    )""")
    conn.execute("""CREATE TABLE creature_subtypes (
        creature_id TEXT, subtype TEXT
    )""")
    conn.execute("""CREATE TABLE creature_attacks (
        creature_id TEXT, attack_source TEXT, description TEXT,
        bonus INTEGER, damage TEXT
    )""")
    conn.execute("""CREATE TABLE creature_special_qualities (
        creature_id TEXT, quality TEXT
    )""")

    count = 0
    for cr in entries:
        if not isinstance(cr, dict):
            continue
        tid = cr.get("template_id")
        if not tid:
            continue
        try:
            conn.execute(
                "INSERT OR REPLACE INTO creatures VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    tid,
                    cr.get("size_category"),
                    cr.get("creature_type"),
                    cr.get("hit_dice"),
                    cr.get("hp_typical"),
                    cr.get("ac_total"),
                    cr.get("ac_touch"),
                    cr.get("ac_flat_footed"),
                    cr.get("bab"),
                    cr.get("fort_save"),
                    cr.get("ref_save"),
                    cr.get("will_save"),
                    cr.get("str_score"),
                    cr.get("dex_score"),
                    cr.get("con_score"),
                    cr.get("int_score"),
                    cr.get("wis_score"),
                    cr.get("cha_score"),
                    cr.get("cr"),
                    cr.get("speed_ft"),
                    cr.get("space_ft"),
                    cr.get("reach_ft"),
                    cr.get("source_page"),
                ),
            )
            count += 1
        except Exception as exc:
            print(f"  WARNING: creature {tid} — {exc}")
            continue

        for st in cr.get("subtypes", []):
            conn.execute(
                "INSERT INTO creature_subtypes VALUES (?,?)", (tid, st)
            )
        for atk in cr.get("attacks", []):
            if isinstance(atk, dict):
                conn.execute(
                    "INSERT INTO creature_attacks VALUES (?,?,?,?,?)",
                    (tid, "attack", atk.get("description", ""),
                     atk.get("bonus"), atk.get("damage", "")),
                )
        for atk in cr.get("full_attacks", []):
            if isinstance(atk, dict):
                conn.execute(
                    "INSERT INTO creature_attacks VALUES (?,?,?,?,?)",
                    (tid, "full_attack", atk.get("description", ""),
                     atk.get("bonus"), atk.get("damage", "")),
                )
        for sq in cr.get("special_qualities", []):
            conn.execute(
                "INSERT INTO creature_special_qualities VALUES (?,?)",
                (tid, sq),
            )

    return count


def _build_equipment(conn: sqlite3.Connection) -> int:
    """Table 5: equipment (containers section)."""
    data = _load_json(EQUIPMENT_JSON)
    if data is None:
        return 0
    if not isinstance(data, dict):
        print("  WARNING: equipment_catalog.json unexpected shape — skipping")
        return 0

    conn.execute("DROP TABLE IF EXISTS equipment")
    conn.execute("""CREATE TABLE equipment (
        container_id TEXT PRIMARY KEY,
        name TEXT,
        weight_lb REAL,
        cost_gp REAL,
        size_category TEXT,
        container_capacity_lb REAL,
        draw_action TEXT,
        provenance TEXT
    )""")

    containers = data.get("containers", {})
    count = 0
    for cid, item in containers.items():
        if not isinstance(item, dict):
            continue
        conn.execute(
            "INSERT OR REPLACE INTO equipment VALUES (?,?,?,?,?,?,?,?)",
            (
                cid,
                item.get("name", ""),
                item.get("weight_lb"),
                item.get("cost_gp"),
                item.get("size_category"),
                item.get("container_capacity_lb"),
                item.get("draw_action"),
                item.get("provenance"),
            ),
        )
        count += 1
    return count


def _build_class_progressions(conn: sqlite3.Connection) -> int:
    """Table 6: class_progressions from aidm.schemas.leveling."""
    try:
        from aidm.schemas.leveling import CLASS_PROGRESSIONS
    except ImportError as exc:
        print(f"  WARNING: could not import CLASS_PROGRESSIONS — {exc}")
        return 0

    conn.execute("DROP TABLE IF EXISTS class_progressions")
    conn.execute("""CREATE TABLE class_progressions (
        class_name TEXT PRIMARY KEY,
        hit_die INTEGER,
        bab_type TEXT,
        good_saves TEXT,
        skill_points_per_level INTEGER,
        class_skills TEXT,
        starting_gold_dice TEXT
    )""")

    count = 0
    for cls_name, prog in CLASS_PROGRESSIONS.items():
        good_saves = json.dumps(
            list(getattr(prog, "good_saves", ())), sort_keys=True
        )
        class_skills = json.dumps(
            list(getattr(prog, "class_skills", ())), sort_keys=True
        )
        conn.execute(
            "INSERT OR REPLACE INTO class_progressions VALUES (?,?,?,?,?,?,?)",
            (
                cls_name,
                getattr(prog, "hit_die", None),
                getattr(prog, "bab_type", ""),
                good_saves,
                getattr(prog, "skill_points_per_level", None),
                class_skills,
                getattr(prog, "starting_gold_dice", ""),
            ),
        )
        count += 1
    return count


def _build_ef_fields(conn: sqlite3.Connection) -> int:
    """Table 7: ef_fields — all EF.* constants."""
    try:
        from aidm.schemas.entity_fields import EF
    except ImportError as exc:
        print(f"  WARNING: could not import EF — {exc}")
        return 0

    conn.execute("DROP TABLE IF EXISTS ef_fields")
    conn.execute("""CREATE TABLE ef_fields (
        constant_name TEXT PRIMARY KEY,
        string_value TEXT,
        category TEXT
    )""")

    # Category classification by prefix/keyword
    _CATEGORIES = {
        "HP": "combat", "AC": "combat", "ATTACK": "combat", "DAMAGE": "combat",
        "SAVE": "saves", "FORT": "saves", "REF": "saves", "WILL": "saves",
        "SPELL": "spellcasting", "CASTER": "spellcasting", "DOMAIN": "spellcasting",
        "RACE": "racial", "RACIAL": "racial",
        "SKILL": "skills", "CLASS_SKILL": "skills",
        "FEAT": "feats",
        "POSITION": "spatial", "SIZE": "spatial", "SPACE": "spatial", "REACH": "spatial",
        "CONDITION": "conditions",
        "INVENTORY": "equipment", "ENCUMBRANCE": "equipment", "ARMOR": "equipment",
        "MOUNT": "mounted", "RIDER": "mounted",
        "ENTITY_ID": "identity", "TEAM": "identity", "NAME": "identity",
        "LEVEL": "progression", "XP": "progression",
        "BASE_STAT": "ability_scores", "STR": "ability_scores",
        "DEX": "ability_scores", "CON": "ability_scores",
        "INT": "ability_scores", "WIS": "ability_scores", "CHA": "ability_scores",
    }

    def _classify(name: str) -> str:
        for prefix, cat in _CATEGORIES.items():
            if name.startswith(prefix):
                return cat
        return "other"

    count = 0
    for attr_name in sorted(dir(EF)):
        if attr_name.startswith("_"):
            continue
        val = getattr(EF, attr_name)
        if not isinstance(val, str):
            continue
        conn.execute(
            "INSERT OR REPLACE INTO ef_fields VALUES (?,?,?)",
            (attr_name, val, _classify(attr_name)),
        )
        count += 1
    return count


# ───────────────────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Compile D&D 3.5e data sources into SQLite."
    )
    parser.add_argument(
        "--output", type=Path, default=DEFAULT_DB,
        help=f"Output DB path (default: {DEFAULT_DB})",
    )
    args = parser.parse_args()

    db_path: Path = args.output
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Compiling to: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        builders = [
            ("spells", _build_spells),
            ("feats", _build_feats),
            ("feat_registry", _build_feat_registry),
            ("creatures", _build_creatures),
            ("equipment", _build_equipment),
            ("class_progressions", _build_class_progressions),
            ("ef_fields", _build_ef_fields),
        ]

        for name, builder_fn in builders:
            count = builder_fn(conn)
            print(f"  {name}: {count} rows")

        conn.commit()
        print("Done.")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
