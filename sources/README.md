# Source Layer Documentation

**Version:** 1.0
**Created:** 2026-02-07
**Purpose:** Consolidated source material registry for the deterministic AI DM engine

---

## Overview

The `sources/` directory provides a clean, consolidated layer for accessing D&D 3.5e source material (meta indexes, extracted text, PDF references) used by the AI DM engine.

**Key Principle:** This layer is **READ-ONLY** during engine runtime. All modifications happen offline through controlled migration scripts.

---

## Directory Structure

```
sources/
├── meta/               # Source metadata (647 JSON files)
├── text/               # Extracted page text (3 core rulebooks)
├── pdfs/               # (Reserved for future PDF references)
├── provenance.json     # Master registry (sourceId → paths)
└── README.md           # This file
```

---

## Component Descriptions

### `meta/` - Source Metadata

**Content:** 647 JSON files, one per source (PHB, DMG, MM, supplements, adventures)

**Format:** `{sourceId}.json` where sourceId is a 12-character hex hash

**Schema:**
```json
{
  "sourceId": "681f92bc94ff",
  "title": "Player's Handbook",
  "path_mnt": "/mnt/f/DnD-3.5/Core Rulebooks/Player's Handbook.pdf",
  "pages": 322,
  "extractedAt": "2024-01-15T10:30:00Z"
}
```

**Usage:** Lookup source metadata by sourceId

**Provenance:** Copied from `Vault/00-System/Indexes/meta/` (2026-02-07)

---

### `text/` - Extracted Page Text

**Content:** Raw OCR text, one `.txt` file per PDF page

**Structure:**
```
text/
├── 681f92bc94ff/          # Player's Handbook
│   ├── 0001.txt          # Page 1
│   ├── 0002.txt          # Page 2
│   └── ...               # 322 pages total
├── fed77f68501d/          # Dungeon Master's Guide (322 pages)
└── e390dfd9143f/          # Monster Manual (322 pages)
```

**Format:**
- Filenames: Zero-padded 4-digit, 1-indexed (`0001.txt` to `NNNN.txt`)
- Encoding: UTF-8
- Content: Raw OCR output (minimal processing)

**Quality:**
- Core rulebooks (PHB, DMG, MM): Clean, readable
- Minor OCR artifacts: `/rhombus4` (bullet •), occasional symbol misreads
- Suitable for NLP, search, rule extraction

**Provenance:** Copied from `Vault/00-System/Staging/{sourceId}/pages/` (2026-02-07)

---

### `pdfs/` - PDF References

**Status:** Reserved for future use

**Planned Usage:** Symlinks or catalog references to PDF files (no copies)

**Current State:** PDFs remain in original locations:
- `Core Rulebooks/*.pdf`
- `Supplements/**/*.pdf`
- `Dungeon Master Tools/**/*.pdf`

**Lookup:** Use `provenance.json` → `pdf_path` field

---

### `provenance.json` - Master Registry

**Purpose:** Single source of truth for sourceId → paths mapping

**Schema:**
```json
{
  "version": "1.0",
  "generated": "2026-02-07T12:00:00Z",
  "total_sources": 647,
  "sources": {
    "681f92bc94ff": {
      "sourceId": "681f92bc94ff",
      "title": "Player's Handbook",
      "short_name": "PHB",
      "pages": 322,
      "pdf_path": "f:\\DnD-3.5\\Core Rulebooks\\Player's Handbook.pdf",
      "pdf_exists": true,
      "meta_path": "sources/meta/681f92bc94ff.json",
      "text_path": "sources/text/681f92bc94ff",
      "text_extracted": true,
      "text_page_count": 322,
      "pages_verified": true,
      "reuse_decision": "reuse_strong",
      "tags": ["core", "rulebook"]
    }
  }
}
```

**Key Fields:**
- `sourceId`: Unique 12-char hex identifier
- `title`: Human-readable source name
- `short_name`: Abbreviation (PHB, DMG, MM) if available
- `pages`: Page count from metadata
- `pdf_path`: Absolute path to PDF (if exists)
- `meta_path`: Relative path to meta JSON
- `text_path`: Relative path to extracted text (if available)
- `text_extracted`: Boolean indicating text availability
- `reuse_decision`: Audit classification (`reuse_strong`, `reuse_meta_only`, `rerun_recommended`)
- `tags`: Categories (e.g., `core`, `rulebook`, `supplement`)

---

## Usage Patterns

### Lookup by SourceId

```python
import json
from pathlib import Path

# Load provenance
with open("sources/provenance.json") as f:
    prov = json.load(f)

# Get source info
source = prov["sources"]["681f92bc94ff"]
print(source["title"])  # "Player's Handbook"

# Read page 10
text_path = Path(source["text_path"]) / "0010.txt"
page_10 = text_path.read_text(encoding="utf-8")
```

### Lookup by Title

```python
def find_source_by_title(title, provenance):
    for sid, source in provenance["sources"].items():
        if title.lower() in source["title"].lower():
            return source
    return None

phb = find_source_by_title("Player's Handbook", prov)
```

### Filter by Tags

```python
# Get all core rulebooks
core_books = [
    s for s in prov["sources"].values()
    if "core" in s["tags"]
]

# Get sources with extracted text
extracted = [
    s for s in prov["sources"].values()
    if s["text_extracted"]
]
```

---

## Read-Only Contract

**CRITICAL:** The `sources/` directory is **READ-ONLY** during engine runtime.

### Allowed Operations:
- ✓ Read meta JSONs
- ✓ Read extracted text files
- ✓ Load provenance.json
- ✓ Resolve PDF paths (read-only)

### Prohibited Operations:
- ✗ Write/modify any files in `sources/`
- ✗ Delete files
- ✗ Move files
- ✗ Create new files (except via offline migration)

**Rationale:**
- Ensures reproducibility (source material doesn't change mid-session)
- Prevents accidental corruption
- Supports deterministic replay (same sources → same results)

**Modification Process:**
1. Offline: Create migration script
2. Offline: Test migration on copy
3. Offline: Execute migration (copy, never move from originals)
4. Offline: Verify integrity (file counts, checksums)
5. Commit: Update provenance.json version

---

## Reuse Decisions

Sources are classified based on audit results:

| Decision | Meaning | Count |
|----------|---------|-------|
| **reuse_strong** | Meta valid + PDF exists + page counts verified + text extracted + quality good | 3 (PHB, DMG, MM) |
| **reuse_meta_only** | Meta valid + PDF exists, but no extracted text or not verified | 602 |
| **rerun_recommended** | PDF missing or severe issues | 42 |

**Usage:**
- `reuse_strong`: Production-ready, use immediately
- `reuse_meta_only`: Use metadata only, re-extract text if needed
- `rerun_recommended`: Exclude from pipeline or fix path issues

---

## Data Provenance

### Original Sources:
- **Meta JSONs:** `Vault/00-System/Indexes/meta/*.json`
- **Extracted Text:** `Vault/00-System/Staging/{sourceId}/pages/*.txt`
- **PDFs:** `Core Rulebooks/*.pdf`, `Supplements/**/*.pdf`, etc.

### Migration:
- **Date:** 2026-02-07
- **Method:** Safe copy (originals preserved in Vault)
- **Validation:** File counts, page counts, no modifications to source

### Audit Trail:
- [AUDIT_REPORT.md](../AUDIT_REPORT.md): Detailed audit of Vault ingestion artifacts
- [REUSE_DECISION.json](../REUSE_DECISION.json): Per-source reuse decisions
- [SOURCE_LAYER_PLAN.md](../SOURCE_LAYER_PLAN.md): Migration design document

---

## Statistics

| Metric | Value |
|--------|-------|
| Total sources | 647 |
| Meta JSONs | 647 (100%) |
| Extracted text | 18 sources (2.8%) |
| Core rulebooks | 3 (PHB, DMG, MM) |
| PDFs found | 605 (93.5%) |
| reuse_strong | 3 |
| reuse_meta_only | 602 |
| rerun_recommended | 42 |

---

## Future Extensions

### Planned:
1. **PDF catalog:** Symlink or catalog remaining 602 PDFs
2. **Bulk extraction:** Re-extract remaining 629 sources
3. **Quality improvement:** Re-extract 2 garbled sources (Ravenloft PHB, A Dark And Stormy Knight)
4. **Schema versioning:** Add version field to meta JSONs for future migrations

### NOT Planned:
- ✗ Moving PDFs (too large, keep in original locations)
- ✗ Processing extracted text (keep raw for flexibility)
- ✗ Runtime modification (strict read-only contract)

---

## Contact & Support

For questions about the source layer:
- See [AUDIT_REPORT.md](../AUDIT_REPORT.md) for audit methodology
- See [SOURCE_LAYER_PLAN.md](../SOURCE_LAYER_PLAN.md) for design rationale
- See [WORKSPACE_MANIFEST.md](../WORKSPACE_MANIFEST.md) for workspace inventory

**Last Updated:** 2026-02-07
