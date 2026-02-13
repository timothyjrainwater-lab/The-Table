PM Inbox — Drop Zone for Aegis Review

Any deliverable that needs PM (GPT/Aegis) review goes here as a markdown file.

## Inbox Hygiene Rules

1. **Auto-archive on integration:** When PM marks a WO as INTEGRATED in the PSD, PM also moves the DISPATCH and AGENT completion docs to `pm_inbox/reviewed/`.
2. **Inbox cap:** pm_inbox root should contain no more than 10 active items (excluding subdirectories). If count exceeds 10, PM triages before any new work.
3. **Review cycle:** After review is complete, PM archives the file to `pm_inbox/reviewed/`. Stale files cause confusion.
4. **No orphan docs:** Every file in pm_inbox root must be either (a) awaiting review, (b) actively referenced by current work, or (c) a persistent operational file (playtest_log, README, REHYDRATION_KERNEL_LATEST).

Naming convention: {AGENT}_{WO-id}_{short_description}.md
Examples:
  SONNET-C_WO-M1-01_event_reducer_impl.md
  OPUS_WO-M1-01_event_reducer_spec.md

Every file must start with a header block:
  # [Work Order ID]: [Short Title]
  **Agent:** [Sonnet-A, Sonnet-B, Sonnet-C, Sonnet-D, or Opus]
  **Work Order:** [WO-M1-01, etc.]
  **Date:** [YYYY-MM-DD]
  **Status:** [Complete | Partial | Blocked]

## Special Files

- **REHYDRATION_KERNEL_LATEST.md** — Compact rehydration block. Must be kept fresh with current repo state. Canonical version at `docs/ops/REHYDRATION_KERNEL.md`.
- **playtest_log.jsonl** — Structured playtest records (append-only).

## Rehydration Folder

**`aegis_rehydration/`** — Contains copies of ALL documents Aegis needs for a full context window rehydration. Instead of hunting for individual files, drag-drop the entire folder contents into GPT. See `aegis_rehydration/README.md` for contents, update protocol, and recommended reading order.

**Important:** The files in `aegis_rehydration/` are copies. When source files change, the copies must be refreshed.
