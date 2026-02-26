# DEBRIEF — LST-PARSER-001: PCGen LST File Parser

**Date:** 2026-02-26
**Status:** ACCEPTED
**Gate score:** N/A (no pytest gate — human spot-check only)

## Deliverables

- **`scripts/parse_pcgen_lst.py`** — Offline PCGen LST → JSON extractor

## Capabilities

| Function | Description |
|----------|-------------|
| `parse_lst_file(filepath)` | Core parser: tab-split, handles continuation lines, skips `#`/`SOURCE:` lines |
| `extract_spells(entries)` | Extracts spell data (school, components, range, duration, save, SR) |
| `extract_armor(entries)` | Filters TYPE=Armor/Shield; extracts ASF, ACP, maxDEX, AC bonus |
| `extract_feats_prereqs(entries)` | Extracts prereq feats, stats, BAB from PREFEAT/PRESTAT/PREATT tags |
| `extract_class_tables(entries)` | Extracts CAST:/KNOWN:/UDAM: per-level tables |
| CLI | `python parse_pcgen_lst.py <file> --type [spells\|armor\|classes\|feats\|raw] --output <path>` |

## Usage

```bash
python parse_pcgen_lst.py rsrd_spells.lst --type spells --output data/pcgen_extracted/spells_raw.json
python parse_pcgen_lst.py rsrd_equip.lst --type armor --output data/pcgen_extracted/armor_raw.json
python parse_pcgen_lst.py rsrd_classes.lst --type classes --output data/pcgen_extracted/class_tables_raw.json
python parse_pcgen_lst.py rsrd_feats.lst --type feats --output data/pcgen_extracted/feats_raw.json
```

## Findings

- PCGen LST files not present locally; script is ready for offline use when Thunder provides them.
- UDAM tag format uncertainty documented inline — verify against actual file when available.
- `rsrd_abilities_class.lst` (453KB) flagged as hand-extract only; not parsed by this script.
