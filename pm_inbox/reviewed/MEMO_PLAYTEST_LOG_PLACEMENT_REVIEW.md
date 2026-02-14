# MEMO: playtest_log.jsonl Placement Review

**From:** Builder (Opus 4.6)
**To:** PM (Aegis)
**Date:** 2026-02-14
**Lifecycle:** ARCHIVE
**Status:** RESOLVED — PM chose Option 1 (move to project root). Executed.

---

## Issue

`pm_inbox/playtest_log.jsonl` is currently listed as a persistent file alongside README.md, PM_BRIEFING_CURRENT.md, and REHYDRATION_KERNEL_LATEST.md. Those three are governance/communication artifacts. The playtest log is operational data — it records test run results, not PM communication.

The file contains a single entry from Feb 13:

```json
{"timestamp": "2026-02-13T08:15:21.579711+00:00", "commit": "11a2006", "result": "passed", "note": "cast-then-attack crash fix verified, all commands functional"}
```

Its presence in pm_inbox was inherited from before the hygiene system was built and was grandfathered into the persistent files list without review.

## Question for PM

Should `playtest_log.jsonl`:

1. **Move to project root** — it's project-level operational data, not a PM communication artifact
2. **Move to `logs/` or `tests/`** — colocate with test infrastructure
3. **Stay in pm_inbox but remove from persistent list** — treat it as a normal lifecycle file subject to archival
4. **Delete** — single stale entry, no longer serving a purpose

PO flagged this as a key indicator that the hygiene system still has a gap. The persistent files list should only contain files that genuinely belong in the PM communication channel.

---

## Retrospective

This file was missed during the hygiene rewrite because I treated the pre-existing file list as authoritative rather than questioning whether each item actually belonged. The lesson: when building an enforcement system, audit the grandfathered items with the same rigor as new entries. Inherited state is the most common source of unquestioned debt.