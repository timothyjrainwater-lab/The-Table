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
