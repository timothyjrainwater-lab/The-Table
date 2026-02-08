# Workspace Manifest
**Generated:** 2026-02-07
**Purpose:** Complete inventory of tracked files with metadata

---

## New Foundation Files (Active Codebase)

### Python Package: aidm/

| File Path | Size (bytes) | Last Modified |
|-----------|--------------|---------------|
| `aidm/__init__.py` | 87 | 2026-02-07 18:25:42 |
| `aidm/core/__init__.py` | 44 | 2026-02-07 18:25:45 |
| `aidm/core/event_log.py` | 2,383 | 2026-02-07 18:28:24 |
| `aidm/core/rng_manager.py` | 2,121 | 2026-02-07 18:27:30 |
| `aidm/core/state.py` | 1,719 | 2026-02-07 18:31:25 |
| `aidm/core/replay_runner.py` | 3,403 | 2026-02-07 18:40:17 |
| `aidm/rules/__init__.py` | 40 | 2026-02-07 18:25:49 |
| `aidm/rules/legality_checker.py` | 3,408 | 2026-02-07 18:48:42 |
| `aidm/schemas/__init__.py` | 40 | 2026-02-07 18:25:51 |

**Subtotal:** 13,245 bytes (13KB)

### Test Suite: tests/

| File Path | Size (bytes) | Last Modified |
|-----------|--------------|---------------|
| `tests/__init__.py` | 27 | 2026-02-07 18:25:54 |
| `tests/test_rng_manager.py` | 4,707 | 2026-02-07 18:28:23 |
| `tests/test_event_log.py` | 4,809 | 2026-02-07 18:33:15 |
| `tests/test_state.py` | 3,845 | 2026-02-07 18:38:58 |
| `tests/test_replay_runner.py` | 7,101 | 2026-02-07 18:47:37 |
| `tests/test_legality_checker.py` | 4,916 | 2026-02-07 18:56:05 |

**Subtotal:** 25,405 bytes (25KB)

### Configuration Files

| File Path | Size (bytes) | Last Modified |
|-----------|--------------|---------------|
| `pytest.ini` | 131 | 2026-02-07 18:26:05 |
| `requirements.txt` | 30 | 2026-02-07 18:26:30 |

**Subtotal:** 161 bytes

### Project Documentation

| File Path | Size (bytes) | Last Modified |
|-----------|--------------|---------------|
| `AI_DM_Master_Action_Log.md` | 12,023 | 2026-02-07 18:21:37 |
| `WORKSPACE_MANIFEST.md` | (this file) | 2026-02-07 |

**Subtotal:** 12,023 bytes (12KB)

### Development Configuration

| File Path | Size (bytes) | Last Modified |
|-----------|--------------|---------------|
| `.claude/permissions.json` | 29 | 2026-02-07 18:52:15 |
| `.claude/settings.local.json` | 247 | 2026-02-07 18:55:19 |

**Subtotal:** 276 bytes

**Total New Foundation:** ~51KB code + configuration

---

## Legacy/Archive Candidates

### Research Documents (./Research/)

| File Path | Size (bytes) | Last Modified |
|-----------|--------------|---------------|
| `Research/Ai Dm Master Action Plan.docx` | 14,558 | 2026-02-07 15:22:20 |
| `Research/Ai Dm Master Action Plan V2 — Rule Atom → Modules → Tests.docx` | 16,088 | 2026-02-07 15:21:49 |
| `Research/Ai-driven Local Dm — Master Action Plan.docx` | 16,201 | 2026-02-07 15:22:56 |
| `Research/Action Plan – Deterministic D&d 3.docx` | 19,391 | 2026-02-07 15:33:52 |
| `Research/Action Plan – Deterministic D&d 3 (1).docx` | 14,036 | 2026-02-07 15:23:10 |
| `Research/Action Plan – Deterministic D&d 3 (2).docx` | 17,756 | 2026-02-07 15:46:26 |
| `Research/Action Plan – Deterministic D&d 3 (3).docx` | 25,406 | 2026-02-07 16:15:12 |
| `Research/D&D DM.docx` | 31,222 | 2026-02-07 15:33:54 |
| `Research/D&D Combat.docx` | 26,402 | 2026-02-07 15:36:24 |
| `Research/D&D 3.5e — Deterministic Mechanics.docx` | 18,969 | 2026-02-07 15:44:16 |
| `Research/D&D 3.5 Combat DM Decision Model .docx` | 22,025 | 2026-02-07 15:58:55 |
| `Research/Phase 3.6 — Combat Engine Specification.docx` | 19,154 | 2026-02-07 15:50:04 |

**Subtotal:** 241,208 bytes (235KB, 12 files)

### Vault Knowledge Base (./Vault/)

**Note:** Contains ~1,300+ files. Summary breakdown:

| Component | File Count | Approx Size | Type |
|-----------|------------|-------------|------|
| `Vault/00-System/Indexes/meta/` | ~1,000 | ~250KB | Generated metadata JSON |
| `Vault/*.md` (Rules, Tables, MOCs) | ~300 | ~150KB | Extracted markdown |
| `Vault/00-System/*.db` | 6-10 | Varies | SQLite databases |
| `Vault/00-System/library.json` | 1 | 306KB | Master library index |
| `Vault/.obsidian/` | ~5 | ~8KB | Obsidian IDE config |
| Other system files | ~20 | ~50KB | Logs, policies, compilers |

**Key Files:**
- `Vault/00-System/citation_policy.md` (554 bytes)
- `Vault/00-System/library.json` (306,638 bytes)
- `Vault/00-System/Compiler/passA/PHB.json` (3,691 bytes)
- `Vault/00-System/Compiler/passA/DMG.json` (426 bytes)

**Vault Subtotal:** ~800KB + databases

---

## Reference Materials (Keep)

### Core D&D 3.5e Rulebooks

**Directory:** `Core Rulebooks/`

| File | Type | Purpose |
|------|------|---------|
| `Player's Handbook.pdf` | PDF | Core rules |
| `Dungeon Master's Guide.pdf` | PDF | DM rules |
| `Monster Manual.pdf` | PDF | Creatures |
| `DnD35_Core_Books.pdf` | PDF | Combined/alternate |

**Note:** File sizes not listed (large PDFs, ~10-50MB each)

### Supplemental Materials

| Directory | Contents | Purpose |
|-----------|----------|---------|
| `Dungeon Master Tools/` | Adventures, tokens, accessories | Campaign resources |
| `Supplements/` | Additional D&D sourcebooks | Extended rules |
| `Miscellaneous/` | Miscellaneous resources | Supporting materials |

**Estimated Total:** ~500MB+ of PDFs

---

## Artifacts & Unknown Files

### Delete Candidates

| File Path | Size (bytes) | Reason |
|-----------|--------------|--------|
| `Torrent downloaded from Demonoid.com.txt` | 47 | Metadata artifact (root) |
| `Core Rulebooks/Torrent downloaded from Demonoid.com.txt` | 47 | Metadata artifact (duplicate) |

**Subtotal:** 94 bytes

### Unknown/Review Required

| File Path | Size (bytes) | Last Modified | Question |
|-----------|--------------|---------------|----------|
| `New Text Document.txt` | 189,291 | 2026-02-07 17:58:48 | Original task spec? Review contents. |
| `Usage.txt` | 3,079 | 2026-02-01 18:24:21 | Project usage or D&D licensing? |

**Subtotal:** 192,370 bytes (188KB)

---

## Summary Statistics

| Category | Files | Total Size | Status |
|----------|-------|------------|--------|
| **Active Code** | 9 Python files | ~13KB | ✓ KEEP |
| **Active Tests** | 6 Python files | ~25KB | ✓ KEEP |
| **Active Config** | 3 files | <1KB | ✓ KEEP |
| **Active Docs** | 2 markdown | ~12KB | ✓ KEEP |
| **Research Docs** | 12 DOCX | ~235KB | → ARCHIVE |
| **Vault System** | ~1,300+ | ~800KB | → ARCHIVE |
| **Reference PDFs** | 300+ | ~500MB | ✓ KEEP |
| **Artifacts** | 2 TXT | <1KB | → DELETE |
| **Unknown** | 2 TXT | ~188KB | ? REVIEW |

**Active Codebase:** ~50KB (code + tests + config + docs)
**Archive Candidates:** ~1MB (planning + extraction artifacts)
**Reference Library:** ~500MB (D&D PDFs)

---

## File Type Breakdown

| Extension | Count | Purpose |
|-----------|-------|---------|
| `.py` | 15 | Python source code |
| `.md` | ~302 | Markdown docs (Vault + project) |
| `.json` | ~1,005 | Metadata (Vault indexes + config) |
| `.docx` | 12 | Planning documents |
| `.pdf` | 300+ | D&D reference materials |
| `.txt` | 4 | Mixed (tasks, artifacts, usage) |
| `.ini` | 1 | pytest configuration |
| `.db` | ~10 | SQLite databases (Vault) |

---

## Archive Recommendations

### Suggested Archive Structure

```
_archive/
├── research/                    (Research/*.docx)
├── vault_obsidian/             (Vault/ → moved entirely)
│   ├── 00-System/
│   ├── .obsidian/
│   └── *.md files
└── original_specs/
    └── task_specification.txt  (New Text Document.txt if confirmed)
```

### Commands (After User Confirmation)

```bash
# Create archive structure
mkdir -p _archive/{research,vault_obsidian,original_specs}

# Move research documents
mv Research/*.docx _archive/research/

# Move Vault knowledge base
mv Vault/ _archive/vault_obsidian/

# Clean artifacts
rm "Torrent downloaded from Demonoid.com.txt"
rm "Core Rulebooks/Torrent downloaded from Demonoid.com.txt"
```

---

## Verification Checklist

Before archiving/deleting, confirm:

- [ ] All 42 tests passing (Tasks 0-5 complete)
- [ ] `AI_DM_Master_Action_Log.md` is canonical source of truth
- [ ] Research .docx files no longer actively referenced
- [ ] Vault extraction phase complete (not needed at runtime)
- [ ] `New Text Document.txt` contents reviewed
- [ ] `Usage.txt` contents reviewed
- [ ] No uncommitted work in Vault that needs extraction

---

**End of Manifest**
