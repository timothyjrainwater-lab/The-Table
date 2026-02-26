# PM Inbox — Drop Zone for Aegis Review

Any deliverable that needs PM (GPT/Aegis) review goes here as a markdown file.

**Core principle:** The PM's context window is the most precious commodity in the system. The PM reads memos, writes verdicts, and sets lifecycle states — nothing else. All resulting actions (file moves, doc updates, briefing maintenance, archival) are executed by builders. If the PM is executing builder actions, context is being wasted on operations instead of judgment.

## Inbox Hygiene Rules

1. **Auto-archive on integration:** When PM marks a WO as INTEGRATED in the PSD, the builder moves the DISPATCH and completion docs to `pm_inbox/reviewed/`.
2. **Inbox cap (ENFORCED — Tier 1):** pm_inbox root must contain no more than **15 active `.md` files** (excluding persistent operational files and subdirectories). Enforced by `tests/test_pm_inbox_hygiene.py`. If count exceeds 15, triage and archive before adding new files.
3. **Review cycle:** When PM sets a file's lifecycle to ARCHIVE, the builder moves it to `pm_inbox/reviewed/`. Stale files cause confusion.
4. **No orphan docs:** Every file in pm_inbox root must be either (a) awaiting review, (b) actively referenced by current work, or (c) a persistent operational file.
5. **Briefing update on intake:** When you add a file to pm_inbox, you MUST also add a one-line entry to `PM_BRIEFING_CURRENT.md` under the appropriate section. This is the PM's entry point — if it's not in the briefing, the PM may not see it.

## File Type Prefixes (ENFORCED — Tier 1)

Every non-persistent file must use one of these prefixes. Enforced by `tests/test_pm_inbox_hygiene.py`.

| Prefix | Purpose | Example |
|--------|---------|---------|
| `WO-` | Work order dispatch | `WO-VERIFY-A_DISPATCH.md` |
| `WO_SET` / `WO_SET-` | Batch of related WOs | `WO_SET_METHODOLOGY_REFINEMENT.md` |
| `MEMO_` / `MEMO-` | Session findings/summary | `MEMO_SESSION2_METHODOLOGY.md` |
| `DEBRIEF_` / `DEBRIEF-` | Full context dump (Section 15.5 Pass 1) | `DEBRIEF_WO-VERIFY-A.md` |
| `HANDOFF_` / `HANDOFF-` | Cross-session context transfer | `HANDOFF_PM_INBOX_HYGIENE.md` |
| `PO_REVIEW` / `PO_REVIEW-` | Product owner review doc | `PO_REVIEW_WO-OSS-DICE-001.md` |
| `BURST_` / `BURST-` | Research intake queue | `BURST_INTAKE_QUEUE.md` |
| `FIX_WO` / `FIX_WO-` | Fix work order dispatch packet | `FIX_WO_DISPATCH_PACKET.md` |
| `WO_INSTITUTIONALIZE` | Institutionalization WO (legacy) | `WO_INSTITUTIONALIZE_DEBRIEF_PROTOCOL.md` |
| `PROBE-` / `PROBE_` | Probe spec / investigation document | `PROBE-JUDGMENT-LAYER-001.md` |
| `STRAT-` / `STRAT_` | Strategy / policy decision document | `STRAT-CAT-05-CALLED-SHOT-POLICY-001.md` |
| `TUNING_` / `TUNING-` | Tuning protocol / observation ledger | `TUNING_001_PROTOCOL.md` |
| `UI_` | UI audit / input document | `UI_POLISH_AUDIT_001.md` |
| `WSM_` | Watch sync / methodology document | `WSM_01_WATCH_SYNC.md` |

## Lifecycle Header (ENFORCED — Tier 1)

Every non-persistent `.md` file must include a `**Lifecycle:**` field in the first 15 lines. Enforced by `tests/test_pm_inbox_hygiene.py`.

Valid lifecycle states:

| State | Meaning | Who sets it |
|-------|---------|-------------|
| `NEW` | Just created, PM hasn't read it | Author (builder) on creation |
| `TRIAGED` | PM has read it, assigned priority | PM (verdict edit) |
| `ACTIONED` | PM has written verdict on contents | PM (verdict edit) |
| `ARCHIVE` | Ready to move to `reviewed/` | PM (verdict edit) — builder executes the move |

Example header block:
```markdown
# MEMO: Session Findings
**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Lifecycle:** NEW
```

## Persistent Operational Files (Exempt from Prefix/Lifecycle Rules)

These files are always present and are not subject to the naming prefix or lifecycle requirements:

- `README.md` — This file
- `PM_BRIEFING_CURRENT.md` — Rolling briefing (PM's entry point)
- `REHYDRATION_KERNEL_LATEST.md` — Compact rehydration block
- `PREFLIGHT_CANARY_LOG.md` — Append-only operational log; builders append one entry per session

## Builder Intake Protocol

When you create a file in pm_inbox:

1. **Choose the correct prefix** from the table above
2. **Include the lifecycle header** with `**Lifecycle:** NEW` in the first 15 lines
3. **Add a one-line entry** to `PM_BRIEFING_CURRENT.md` under "Requires PM Action" or "Requires PM Read"
4. **Check the file count** — if you're near the cap, note it in your debrief
5. **Audit grandfathered items** — when building or updating enforcement rules, review existing items with the same rigor as new entries. Inherited state is the most common source of unquestioned debt.

## PM Verdict Protocol

The PM reads memos and writes verdicts. All physical actions are builder-executed.

**How content reaches the PM:** The PM does not open inbox files directly. The Operator controls what enters the PM's context window. When a builder creates an inbox file, the builder also outputs a fenced code block in chat containing a **one-line pointer** — just the filename and verdict action (e.g., `MEMO_IDLE_NOTIFICATION_FORGE_QUIET — PM verdict needed`). The Operator copy-pastes this pointer into the PM session. The PM already has the briefing for context; if the PM needs detail, the PM opens the file. The relay block is a signal, not a compressed memo. This gives the Operator precise, low-cost control over PM context consumption.

**What the PM does:**
1. Reads `PM_BRIEFING_CURRENT.md` to identify items needing decisions
2. Opens files, reads content, writes verdict edits (lifecycle state changes, decision annotations)
3. Nothing else. The PM never moves files, updates briefings, or modifies infrastructure.

**What the builder does after PM verdict:**
1. Read PM's lifecycle/verdict edits on files
2. Move `Lifecycle: ARCHIVE` files to `reviewed/`
3. Update `PM_BRIEFING_CURRENT.md` (check off completed items, add new entries)
4. Execute any actions the PM's verdict specifies

**WO_SET dispatch rule:** A WO_SET is a *proposal vehicle*, not an *execution vehicle*. When the PM verdicts a WO_SET, the PM must draft individual `WO-*_DISPATCH.md` files for each approved item before setting the WO_SET lifecycle to ARCHIVE. A verdicted WO_SET with no corresponding dispatch documents is an incomplete action. (Primary copy of this rule lives in the rehydration kernel.)

**Briefing guard:** The briefing must not list any WO under "Requires Operator Action" unless a corresponding dispatch document exists in `pm_inbox/` root. Items where PM decisions exist but no dispatch doc has been drafted belong under "Needs PM to Draft WOs."

## Subdirectories

### `reviewed/`
Archived completed work. Builders move files here after PM sets lifecycle to ARCHIVE.

### `aegis_rehydration/`
**Writer:** PM/Thunder ONLY.
PM context files for full context window rehydration. Exception: agents may sync canonical project files (e.g., `AGENT_DEVELOPMENT_GUIDELINES.md`) that have rehydration headers.

### `gpt_rehydration/`
External LLM onboarding packet (tiered structure).

### `research/`
Voice-first research synthesis and completion receipts.
