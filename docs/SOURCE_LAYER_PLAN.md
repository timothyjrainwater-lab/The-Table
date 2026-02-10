# Source Layer Directory Plan

**Version:** 1.0
**Date:** 2026-02-07
**Status:** PROPOSAL (no file operations yet)

---

## Goal

Design a clean, maintainable source layer structure for the deterministic AI DM engine that:
1. Consolidates meta indexes, PDF references, and extracted text
2. Supports efficient lookup by sourceId
3. Preserves provenance and traceability
4. Enables future re-extraction without losing existing work

---

## Proposed Directory Structure

```
sources/
├── meta/                       # Source metadata (one JSON per source)
│   ├── 681f92bc94ff.json      # PHB meta
│   ├── fed77f68501d.json      # DMG meta
│   ├── e390dfd9143f.json      # MM meta
│   └── ...                     # 647 total
│
├── text/                       # Extracted page text (one dir per source)
│   ├── 681f92bc94ff/          # PHB extracted text
│   │   ├── 0001.txt
│   │   ├── 0002.txt
│   │   └── ... (322 pages)
│   ├── fed77f68501d/          # DMG extracted text
│   └── ...                     # 18 sources with extracted text
│
├── pdfs/                       # PDF file references (symlinks or catalog)
│   ├── core/
│   │   ├── phb.pdf -> ../../Core Rulebooks/Player's Handbook.pdf
│   │   ├── dmg.pdf -> ../../Core Rulebooks/Dungeon Master's Guide.pdf
│   │   └── mm.pdf -> ../../Core Rulebooks/Monster Manual.pdf
│   └── supplements/
│       └── ... (optional: symlink structure for supplements)
│
├── provenance.json             # Master sourceId → title/path mapping
│
└── README.md                   # Source layer documentation
```

---

## Design Decisions

### 1. Meta: Copy or Reference?

**Decision:** **COPY** `Vault/00-System/Indexes/meta/*.json` → `sources/meta/`

**Rationale:**
- Meta JSONs are small (~200-300 bytes each, 647 files = ~150KB total)
- Copying decouples source layer from Vault
- Allows Vault to be archived without breaking references
- Enables schema migration (can transform copies without touching originals)

**Implementation:**
```python
# Pseudocode
for meta_file in Path("Vault/00-System/Indexes/meta").glob("*.json"):
    shutil.copy(meta_file, f"sources/meta/{meta_file.name}")
```

**Tradeoff:** Duplicates data, but gain is independence and safety.

---

### 2. Extracted Text: Copy or Move?

**Decision:** **COPY** `Vault/00-System/Staging/{sourceId}/pages/` → `sources/text/{sourceId}/`

**Rationale:**
- Extracted text is the result of expensive OCR/processing
- Keep originals in Vault as backup
- Total size: ~18 sources × ~100KB-5MB each = ~50-100MB
- Copying preserves Vault as historical artifact

**Implementation:**
```python
# Pseudocode
for source_id in extracted_sources:
    src = Path(f"Vault/00-System/Staging/{source_id}/pages")
    dst = Path(f"sources/text/{source_id}")
    shutil.copytree(src, dst)
```

**Alternative (if space-constrained):**
- **Symlink** instead: `sources/text/{sourceId} -> ../../Vault/00-System/Staging/{sourceId}/pages/`
- **Pros:** No duplication, instant
- **Cons:** Breaks if Vault is moved/archived

**Recommendation:** Copy for core rulebooks (PHB/DMG/MM), symlink for supplements if needed.

---

### 3. PDFs: Copy, Symlink, or Catalog?

**Decision:** **CATALOG + SYMLINK** (hybrid approach)

**Rationale:**
- PDFs are large (~10-50MB each, 605 found = ~10GB+)
- Copying would double disk usage unnecessarily
- Symlinking preserves access without duplication
- Catalog (provenance.json) provides path lookup without filesystem dependency

**Implementation:**

#### Option A: Symlink Core Rulebooks
```bash
mkdir -p sources/pdfs/core
ln -s "../../Core Rulebooks/Player's Handbook.pdf" sources/pdfs/core/phb.pdf
ln -s "../../Core Rulebooks/Dungeon Master's Guide.pdf" sources/pdfs/core/dmg.pdf
ln -s "../../Core Rulebooks/Monster Manual.pdf" sources/pdfs/core/mm.pdf
```

**Windows equivalent:**
```batch
mklink sources\pdfs\core\phb.pdf "..\..\Core Rulebooks\Player's Handbook.pdf"
```

#### Option B: Catalog-Only (No Symlinks)
Store paths in `provenance.json`:
```json
{
  "681f92bc94ff": {
    "sourceId": "681f92bc94ff",
    "title": "Player's Handbook",
    "pdf_path": "Core Rulebooks/Player's Handbook.pdf",
    "pdf_exists": true,
    "pages": 322,
    "extracted_text": "sources/text/681f92bc94ff"
  }
}
```

**Recommendation:** **Option B (Catalog-Only)** for portability and simplicity. Applications lookup PDF paths from provenance.json at runtime.

---

### 4. Provenance Mapping

**Decision:** Create `sources/provenance.json` as **master registry**

**Schema:**
```json
{
  "version": "1.0",
  "generated": "2026-02-07T12:00:00Z",
  "sources": {
    "681f92bc94ff": {
      "sourceId": "681f92bc94ff",
      "title": "Player's Handbook",
      "short_name": "PHB",
      "pages": 322,
      "pdf_path": "Core Rulebooks/Player's Handbook.pdf",
      "pdf_exists": true,
      "meta_path": "sources/meta/681f92bc94ff.json",
      "text_path": "sources/text/681f92bc94ff",
      "text_extracted": true,
      "reuse_decision": "reuse_strong",
      "tags": ["core", "rulebook", "player"]
    },
    "fed77f68501d": { ... },
    "e390dfd9143f": { ... }
  }
}
```

**Purpose:**
- Single source of truth for sourceId → paths
- Enables fast lookup without scanning filesystem
- Records reuse decisions and extraction status
- Supports tagging (core, supplement, adventure, etc.)

**Generation:**
```python
# Pseudocode
provenance = {
    "version": "1.0",
    "generated": datetime.utcnow().isoformat(),
    "sources": {}
}

for source in audit_data["source_decisions"]:
    provenance["sources"][source["sourceId"]] = {
        "sourceId": source["sourceId"],
        "title": source["title"],
        "pages": source["pages_meta"],
        "pdf_path": source["pdf_path_resolved"],
        "pdf_exists": source["pdf_exists"],
        "meta_path": f"sources/meta/{source['sourceId']}.json",
        "text_path": f"sources/text/{source['sourceId']}",
        "text_extracted": source["extracted_text"]["found"],
        "reuse_decision": source["decision"]
    }
```

---

## Migration Strategy

### Phase 1: Create Structure (Read-Only)
```bash
mkdir -p sources/{meta,text,pdfs/core}
```

### Phase 2: Copy Meta Indexes
```bash
cp Vault/00-System/Indexes/meta/*.json sources/meta/
# Result: 647 files copied (~150KB)
```

### Phase 3: Copy Extracted Text (Core Only)
```bash
for sid in 681f92bc94ff fed77f68501d e390dfd9143f; do
  cp -r "Vault/00-System/Staging/$sid/pages" "sources/text/$sid"
done
# Result: 3 sources copied (~10-15MB)
```

### Phase 4: Generate Provenance
```python
python generate_provenance.py
# Reads: REUSE_DECISION.json
# Writes: sources/provenance.json
```

### Phase 5: Verify Integrity
```bash
# Check file counts
ls sources/meta/*.json | wc -l  # Expected: 647
ls sources/text/ | wc -l         # Expected: 3 (PHB, DMG, MM)

# Check extracted page counts
ls sources/text/681f92bc94ff/*.txt | wc -l  # Expected: 322 (PHB)
ls sources/text/fed77f68501d/*.txt | wc -l  # Expected: 322 (DMG)
ls sources/text/e390dfd9143f/*.txt | wc -l  # Expected: 322 (MM)
```

---

## Filesystem Layout Examples

### Example: PHB Lookup Flow

1. **Query by title:** "Player's Handbook"
   - Search `sources/provenance.json` → find `sourceId: 681f92bc94ff`

2. **Get metadata:**
   - Read `sources/meta/681f92bc94ff.json`
   - Fields: title, pages, extractedAt, path_mnt

3. **Access extracted text:**
   - Read `sources/text/681f92bc94ff/0010.txt` (page 10)

4. **Access PDF (if needed):**
   - Lookup `pdf_path` in provenance: `Core Rulebooks/Player's Handbook.pdf`
   - Resolve to absolute path or open directly

### Example: Directory Tree After Migration

```
sources/
├── meta/
│   └── 681f92bc94ff.json         (260 bytes)
├── text/
│   └── 681f92bc94ff/
│       ├── 0001.txt              (324 bytes, page 1)
│       ├── 0002.txt              (1.2KB, page 2)
│       ├── 0010.txt              (3.4KB, page 10)
│       └── ... (322 files total, ~4.5MB)
├── provenance.json               (150KB, all 647 sources)
└── README.md                     (2KB, documentation)
```

---

## Advantages of This Design

### 1. **Independence from Vault**
- Source layer can function without Vault
- Vault can be archived to `_archive/vault_obsidian/` safely

### 2. **Efficient Lookup**
- `provenance.json` provides O(1) sourceId → path mapping
- Flat `meta/` directory enables fast scanning
- Nested `text/{sourceId}/` mirrors original structure

### 3. **Extensibility**
- Easy to add new extracted sources (just copy to `text/{sourceId}/`)
- Schema versioning in provenance.json supports future changes
- Tagging system in provenance enables filtering (core vs supplements)

### 4. **Traceability**
- Original Vault paths preserved in meta JSONs
- provenance.json records extraction status and decisions
- README.md documents migration provenance

### 5. **Minimal Duplication**
- PDFs not copied (catalog-only)
- Only meta (~150KB) and core text (~15MB) duplicated
- Total overhead: <20MB for 3 core rulebooks

---

## Disk Usage Estimate

| Component | Strategy | Size |
|-----------|----------|------|
| Meta indexes (647) | Copy | ~150KB |
| Core text (PHB/DMG/MM) | Copy | ~15MB |
| Supplement text (15) | Copy (optional) | ~50MB |
| PDFs | Catalog (no copy) | 0 bytes |
| Provenance | Generate | ~150KB |
| **Total** | | **~15-65MB** |

**Tradeoff:** Small disk cost for complete independence from Vault.

---

## Alternative: Minimal Copy Strategy

If disk space is critical:

```
sources/
├── provenance.json             # Master registry (catalog-only)
└── README.md                   # Documentation

# No meta/ or text/ copies
# All paths in provenance.json point to Vault
```

**Pros:** Zero duplication, instant migration
**Cons:** Dependent on Vault, breaks if Vault is moved/archived

**Recommendation:** Only use if truly space-constrained (<100MB available).

---

## Next Steps (After Approval)

1. **Create directory structure:** `mkdir -p sources/{meta,text,pdfs/core}`
2. **Copy meta indexes:** 647 files → `sources/meta/`
3. **Copy core extracted text:** PHB, DMG, MM → `sources/text/`
4. **Generate provenance.json:** Consolidate audit data + meta + decisions
5. **Write sources/README.md:** Document sourceId format, lookup patterns, reuse decisions
6. **Verify integrity:** Compare file counts, page counts, hash spot-checks
7. **Update WORKSPACE_MANIFEST.md:** Add `sources/` section

**No operations performed yet.** Awaiting approval to proceed with migration.

---

**End of Source Layer Directory Plan**
