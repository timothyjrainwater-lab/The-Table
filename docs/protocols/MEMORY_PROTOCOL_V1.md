# Memory Protocol v1 — 3-Tier Agent Memory Standard

**Effective:** 2026-02-22
**Origin:** Aegis proposal (context pressure architecture), Thunder-approved
**Scope:** All agents (Anvil, Slate, future agents)

---

## Problem

Context pressure manifests as backpressure: slower cadence, shorter outputs, more self-correction, drift. The fix is not "give the agent more memory." It's **architect memory so the agent can reach it without loading it.**

Long-term memory lives outside the prompt. The prompt only carries a small working set plus pointers.

---

## The 3-Tier Stack

### Tier 0 — In-Prompt Working Set

What goes into the agent's active context at session start. Hard-capped.

**Contents (maximum):**
- Agent charter header (short)
- One Memory Capsule (200-400 tokens)
- One Focused Recall item (100-250 tokens) — only when directly relevant

**Rule:** One capsule + one recall, max. If an agent needs more context, they must summarize into a new capsule or create a new finding record. This forces compression.

**If the agent starts stuttering, you are over budget. Cut memory, don't add it.**

### Tier 1 — Indexes and Registers

Small files for selection and lookup. Never pasted wholesale — skimmed for pointers.

**Standard files:**
- `STATE_DIGEST.md` — Current environment, known issues, last known green state
- `FINDINGS_REGISTER.md` — One line per finding: ID, severity, status, description, evidence pointer
- `SESSION_INDEX.jsonl` — One JSON line per session: session_id, utc_window, tags, finding_ids, capsule_path, evidence_paths

### Tier 2 — Long-Term Storage

Full receipts. Never pasted wholesale. Accessed by search + pointers.

- Full diary entries / session narratives
- Full raw outputs (validator reports, model outputs)
- AB artifacts, failure logs, diffs
- Evidence packs (JSON frames, JSONL logs)

---

## Memory Capsule v1 Format

Produced after every session. Safe to paste into next session's Tier 0.

```markdown
# Memory Capsule — [Agent] [YYYY-MM-DD HHMMZ]

**Session:** [session_id]
**UTC window:** [start] — [end]
**Environment deltas:** [what changed since last capsule]

## Proven True Now
- [bullet: what is confirmed working]

## Still Broken
- [bullet: what is confirmed broken]

## Top Findings (max 3, by severity)
1. [FINDING-ID] [SEVERITY] — [one line]

## Next Hits (max 3)
1. [what to do next session]

## Evidence Pointers
- [path to evidence file]
```

**Hard cap:** 200-400 tokens. If it doesn't fit, compress harder or split a finding into its own file.

---

## Retrieval Protocol

When an agent needs past context (the two-step recall move):

1. **Select** — Search Tier 1 index by ID or tag. Return up to 3 candidates (finding IDs, session IDs, evidence pointers).
2. **Load** — Summarize ONE candidate into a 100-250 token Focused Recall block. Inject into Tier 0.

No more than one recall block per run.

---

## Agent-Specific Implementations

### Anvil

**Folder:** `anvil_diary/`

```
anvil_diary/
  capsules/          CAPSULE_YYYY-MM-DD_HHMMZ.md
  sessions/          SESSION_YYYY-MM-DD_HHMMZ.md
  findings/          FINDING_<NAME>_YYYY-MM-DD.md
  evidence/          *.json, *.jsonl
  indexes/           SESSION_INDEX.jsonl
  STATE_DIGEST.md
  FINDINGS_REGISTER.md
```

**Standing orders:**
1. After every Spark cage session, produce a capsule in `capsules/`
2. Write full session diary in `sessions/` (narrative + receipts layer)
3. Update `FINDINGS_REGISTER.md` — one line per finding, append-only
4. Append one line to `indexes/SESSION_INDEX.jsonl`
5. Update `STATE_DIGEST.md` with current environment state
6. At session start, load ONLY: latest capsule + one focused recall. Never paste full sessions.

### Slate

Slate's memory is already structured via `pm_inbox/`. No new folder tree.

**Kernel split (Aegis ruling, 2026-02-22):** The rehydration kernel cannot be both a working prompt payload and the canonical PM database. Carrying lists in Tier 0 causes stutter. Carry counts + stoplight + pointers instead. Let Tier 1 be the database.

**Tier 0 (Capsule):** `pm_inbox/REHYDRATION_KERNEL_LATEST.md` — under 400 tokens. Contains:
- Identity and role boundary
- Current priority stack (top 3)
- Stop conditions (what would invalidate the plan)
- Delta since last capsule
- Pointer + hash + timestamp to PM State Register

**Tier 0 (Focused Recall):** Briefing "Requires Operator Action" section — one section, kept tight.

**Tier 1 (PM State Register):** `pm_inbox/PM_BRIEFING_CURRENT.md` + `pm_inbox/BURST_INTAKE_QUEUE.md` — canonical project state. Contains:
- Gate counts (compact stoplight, not full per-gate breakdowns)
- Dispatch list (active and completed)
- Open findings inventory
- Build order position
- Doctrine adoption status

**Tier 2 (Archive):** `pm_inbox/reviewed/` — organized by WO cycle.

**Session index:** Briefing "WO Verdicts" table + handover notes.

**Standing orders:**
1. Kernel is capsule. Under 400 tokens. No lists — counts + stoplight + pointers.
2. Briefing is Tier 1 register. Canonical. This is where lists live.
3. Handover notes at session end serve as session diary.
4. No new folder structure needed.

---

## Compaction Checkpoint (mandatory)

When approaching context pressure, agents perform a **Checkpoint Capsule Refresh** before compaction:

1. Write a fresh capsule to Tier 0 (captures current session state)
2. Update Tier 1 registers (State Register / PM Briefing)
3. Record pointers and hashes
4. Then compaction proceeds

**Rule: No compaction without a new capsule.** Rereading the briefing after compaction works but is manual retrieval, not continuity. The checkpoint makes compaction a controlled boundary instead of a memory cliff.

**Trigger:** If the agent begins stuttering OR is within ~10% of context limit, checkpoint immediately.

---

## Stutter Detection

Context pressure shows up as measurable backpressure:

- Response latency increasing over session
- Output becoming shorter and less specific
- More hedging or self-repair mid-sentence
- "I'll fix it now" impulses without clean evidence linking
- Diary write rate decelerating

**Controls:**
- Keep Tier 0 fixed-size
- One scenario per run (Anvil)
- Log first, patch after
- If blocked, fix only the block, then resume logging
- If stuttering starts, cut memory — don't add it

---

## Future Extensions (out of scope)

1. **Capsule injection into PromptPack** — Add optional capsule field to `PromptPackBuilder.build()`, gets priority slot in MEMORY channel. CODE WO.
2. **Bridge harness Mode A** — Replay-driven prompt compilation tool. Queue behind RV-007. Becomes correctness-enabling once validators are hardened and need real engine truth frames. CODE WO.
3. **Bridge harness Mode B** — Live session bridge. Queue behind Mode A. Needed for "Thunder plays / Spark narrates" continuous operation.
4. **Aegis memory** — If Aegis adopts this protocol, same pattern: `aegis_diary/` with same structure.
5. **PM State Register schema** — Aegis offered to propose exact fields so the kernel split becomes mechanical and enforceable. Accept when ready.
