# Quick Reference: Extracted Sources

## Core D&D 3.5e Rulebooks (All Extracted ✓)

### Player's Handbook
- **SourceId:** `681f92bc94ff`
- **Pages:** 322 (complete)
- **PDF:** `Core Rulebooks/Player's Handbook.pdf`
- **Text:** `Vault/00-System/Staging/681f92bc94ff/pages/0001.txt` ... `0322.txt`
- **Quality:** ✓ Clean, readable
- **Status:** **PRODUCTION READY**

### Dungeon Master's Guide
- **SourceId:** `fed77f68501d`
- **Pages:** 322 (complete)
- **PDF:** `Core Rulebooks/Dungeon Master's Guide.pdf`
- **Text:** `Vault/00-System/Staging/fed77f68501d/pages/0001.txt` ... `0322.txt`
- **Quality:** ✓ Clean, readable
- **Status:** **PRODUCTION READY**

### Monster Manual
- **SourceId:** `e390dfd9143f`
- **Pages:** 322 (complete)
- **PDF:** `Core Rulebooks/Monster Manual.pdf`
- **Text:** `Vault/00-System/Staging/e390dfd9143f/pages/0001.txt` ... `0322.txt`
- **Quality:** ✓ Clean, readable
- **Status:** **PRODUCTION READY**

---

## Additional Extracted Sources (15)

| SourceId | Title | Pages | Status |
|----------|-------|-------|--------|
| `8c6ec9825a68` | Player's Handbook II | 224 | ✓ Clean |
| `768a3c15aaf3` | Ravenloft Player's Handbook | 262 | ⚠ Quality issues |
| `1df8bfba088d` | A Dark And Stormy Knight | 8 | ⚠ Empty first page |
| `35f14d2ba4f3` | A Gnomes Affair | 19 | ✓ Clean |
| `3ff82a72b978` | A Giant Ransom | 17 | ✓ Clean |
| `4ae8b6bef981` | Grimtooth's Dungeon of Doom | 80 | ✓ Clean |
| `4d197aed5293` | Munchkin Player's Handbook | 49 | ✓ Clean |
| `5e08ebe3f272` | DnD35_Core_Books | 8 | ✓ Clean |
| `7b081de138ad` | A Lamentation of Thieves | 54 | Partial (87 meta) |
| `810a7ffb57be` | A Harvest of Evil | 7 | ✓ Clean |
| `9bc337f82986` | A Dead Man's Party | 28 | ✓ Clean |
| `a1a7e6e81478` | A Call to Arms | 8 | ✓ Clean |
| `a1e5ef967487` | A Dark And Stormy Knight | 8 | ✓ Clean |
| `f9105ec75047` | Aasimar and Tiefling | 6 | Partial (98 meta) |
| `fbde7a8a50db` | Grimtooth's Traps | 6 | Partial (66 meta) |

**Total:** 18 sources with extracted text
**Usable:** 16 sources (2 have quality/coverage issues)

---

## Usage Examples

### Read PHB Page 10 (Constitution section)
```bash
cat "Vault/00-System/Staging/681f92bc94ff/pages/0010.txt"
```

### Get metadata for PHB
```bash
cat "Vault/00-System/Indexes/meta/681f92bc94ff.json"
```

### List all extracted sources
```bash
find Vault/00-System/Staging -name "pages" -type d | wc -l
# Output: 18
```

### Verify page coverage for a source
```bash
ls Vault/00-System/Staging/681f92bc94ff/pages/*.txt | wc -l
# Output: 322 (matches meta)
```

---

## Reuse Decision Summary

- **18 sources** have extracted text (2.8% of 647)
- **605 sources** have meta only (93.5%)
- **42 sources** have missing PDFs (6.5%)

**Recommendation:** Use existing extracts for core rulebooks immediately. Consider re-extraction for remaining 629 sources if text-based pipeline is needed.

---

**Last Updated:** 2026-02-07
