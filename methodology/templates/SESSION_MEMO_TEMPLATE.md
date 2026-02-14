# Template: Session Memo

Copy this template when a session produces findings, completes work, or discovers issues that the human coordinator (PM/operator) needs to know about.

See: [PM Context Compression Pattern](../patterns/PM_CONTEXT_COMPRESSION.md)

---

```markdown
# MEMO: [Short Title]

**From:** [Agent identifier]
**Date:** [YYYY-MM-DD]
**Session scope:** [What this session was tasked with — one sentence]

---

## Action Items (PM decides, builder executes)

[Numbered list. Each item has: what decision is needed, who executes after verdict, what it blocks. Keep this SHORT — 3-5 items max. If there are more, prioritize.]

1. **[Decision needed]** — Builder executes: [action after verdict]. Blocks: [what it blocks, or "nothing"].
2. **[Decision needed]** — Builder executes: [action after verdict]. Blocks: [what it blocks].

## Status Updates (Informational only)

[What was completed, what changed, what was committed. The PM does NOT need to act on these — they're for awareness.]

- [Commit hash] — [What was done]
- [Status change] — [What changed and why]

## Deferred Items (Not blocking, act when convenient)

[Low-priority findings, future WO suggestions, observations. The PM can read these when they have spare context budget.]

- [Item] — [Why it can wait]

## Retrospective (Pass 3 — Operational judgment)

[This section is MANDATORY (enforced by test). Reflect on the process, not the output.]

- **Fragility:** [What felt brittle, what nearly broke, what worked well]
- **Process feedback:** [Did WO instructions match reality? Were governance docs accurate?]
- **Methodology:** [New pattern discovered? Existing pattern confirmed or invalidated?]
- **Concerns:** [Anything that worries you about the system's current state]

---

**End of Memo**
```

---

## Three-Pass Writing Process: Dump, Distill, Reflect

**Pass 1 — Full Dump:** Write everything from your context window — cascading impacts, agent failures, schema additions, WO mismatches, test changes, loose ends. Don't filter. Don't worry about length. This is the raw knowledge capture.

**Pass 2 — PM Summary:** Compress the dump into the memo format above. Action items only include decisions the PM must make — not actions the PM must execute. The PM writes verdicts; builders execute. Status updates are one line each. Deferred items get one sentence each.

**Pass 3 — Operational Retrospective:** Reflect on the process itself. This is not what happened — it's what you think about what happened:
- **Fragility observations** — what parts of the system felt brittle, what nearly broke, what worked better than expected
- **Process feedback** — did instructions match reality? Were governance docs accurate? Did the onboarding sequence help or mislead?
- **Methodology insights** — did you discover a new pattern, confirm an existing one, or find a case where the methodology didn't apply?
- **Concerns** — anything that worries you about the system's current state

Pass 3 is a required `## Retrospective` section in the MEMO file, enforced by `tests/test_pm_inbox_hygiene.py` (PMIH-004).

**Why three passes:** Pass 1 prevents context loss. Pass 2 respects the PM's context window budget. Pass 3 captures operational judgment — the kind of insight that only exists while the agent is still inside the problem. If you try to write the compressed version directly, you'll skip things that seemed unimportant but weren't. If you only write the full dump, the PM can't process it. If you skip the retrospective, you lose the meta-observations that improve the system for the next agent.

**Where they go:**
- Pass 1 (full dump): `pm_inbox/DEBRIEF_[SESSION_ID].md` — archived for reference
- Pass 2 (PM summary): `pm_inbox/MEMO_[SHORT_TITLE].md` — this is what the PM reads
- Pass 3 (retrospective): `## Retrospective` section in the MEMO file (mandatory, test-enforced)
- **Operator relay block**: a fenced code block in your chat output containing only the PM-facing content (typically Action Items + enough context to verdict). The Operator copy-pastes this into the PM's context window. The memo file is the archive; the relay block is the actual delivery vehicle. One click, no file opening.

---

## Usage Notes

- **Action Items are the only section the PM might write a verdict on.** Everything else is context. Design your memo so a PM who only reads the Action Items section can write their verdict without reading anything else.
- **Don't combine memos.** One memo per session. If a session produces multiple unrelated findings, that's still one memo — the PM triages internally.
- **Date everything.** Context windows don't have timestamps. The PM needs to know which memo is most recent when two memos conflict.
- **"Session scope" in the header is critical.** It tells the PM what this session was supposed to be doing, which frames everything that follows.
- **Always output an operator relay block.** When you write a memo file, also output a fenced code block in chat containing the PM-facing content the Operator needs to relay. The PM never opens inbox files directly — the Operator controls what enters the PM's context window by copy-pasting relay blocks. Design the relay block so the PM can verdict from it alone without reading the full file.
