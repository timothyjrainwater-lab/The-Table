PM Inbox — Drop Zone for Aegis Review

Any deliverable that needs PM (GPT/Aegis) review goes here as a markdown file.
Thunder drag-drops files from this folder into GPT for review.

Naming convention: {AGENT}_{WO-id}_{short_description}.md
Examples:
  SONNET-C_WO-M1-01_event_reducer_impl.md
  SONNET-A_WO-M1-02_deterministic_ids.md
  OPUS_WO-M1-01_event_reducer_spec.md

Every file must start with a header block:
  # [Work Order ID]: [Short Title]
  **Agent:** [Sonnet-A, Sonnet-B, Sonnet-C, Sonnet-D, or Opus]
  **Work Order:** [WO-M1-01, etc.]
  **Date:** [YYYY-MM-DD]
  **Status:** [Complete | Partial | Blocked]

After GPT has reviewed a file, Thunder moves it to pm_inbox/reviewed/ or deletes it.

## Special Files

- **AEGIS_REHYDRATION_STATE.md** — PM state snapshot. Paste this to Aegis at the start of every new GPT context window. Prevents the "planned but never dispatched" failure mode. Updated by Thunder or Opus whenever pipeline state changes.
- **OPUS_NOTES_FOR_AEGIS.md** — Persistent communication channel from Opus to Aegis.
- **SONNET_AGENT_NOTES.md** — Sonnet agent observations and flags.

## Rehydration Folder

**`aegis_rehydration/`** — Contains copies of ALL documents Aegis needs for a full context window rehydration. Instead of hunting for individual files, drag-drop the entire folder contents into GPT. See `aegis_rehydration/README.md` for contents, update protocol, and recommended reading order.

**Important:** The files in `aegis_rehydration/` are copies. When source files change, the copies must be refreshed (see the README in that folder for the refresh command).
