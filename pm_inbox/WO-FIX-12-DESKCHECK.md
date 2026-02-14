# WO-FIX-12-DESKCHECK: Verify XP Table Levels 11-20

**Authority:** PM (Opus 4.6)
**Date:** 2026-02-14
**Status:** READY for dispatch
**Scope:** Desk check only — verify whether BUG-F2/F3 (XP table levels 11-20) was actually fixed
**Estimated effort:** TRIVIAL (read one file, compare to DMG table)

---

## Context

A builder agent reported WO-FIX-12 F2/F3 as complete, but the Operator couldn't verify the XP table hardcoding was applied. This is a desk check — read the file, compare to DMG Table 2-6, report back.

**Reference:** `pm_inbox/FIX_WO_DISPATCH_PACKET.md` section "WO-FIX-12"

---

## Task

1. Read `aidm/schemas/leveling.py` lines 291-308 (the XP table for levels 11-20).
2. Compare values against DMG Table 2-6 (page 38). Cross-reference with SRD files in `Vault/` if needed.
3. Report one of:
   - **FIXED**: Values match DMG Table 2-6. Quote 3 sample entries as proof.
   - **NOT FIXED**: Values are still formula-generated. Quote the offending code.
   - **PARTIALLY FIXED**: Some entries corrected, others not. List which.

## Do NOT:
- Make any code changes
- Run any tests
- Touch any files

## Completion Report

```
STATUS: [FIXED / NOT FIXED / PARTIALLY FIXED]
EVIDENCE: [3 sample entries compared to DMG]
```
