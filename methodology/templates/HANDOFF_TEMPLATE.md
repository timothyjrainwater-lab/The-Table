# Template: Handoff Document

Copy this template when a session ends with incomplete work, findings that must survive to the next session, or context the next agent needs.

See: [Artifact Primacy Pattern](../patterns/ARTIFACT_PRIMACY.md)

---

```markdown
# Handoff: [Short Description]

**From:** [Agent identifier — e.g., "Builder (Opus 4.6)", "Verifier (Sonnet)"]
**To:** Next agent
**Date:** [YYYY-MM-DD]
**Status:** [READY TO EXECUTE | NEEDS REVIEW | BLOCKED ON [thing]]

---

## Uncommitted Work

[What was changed in the working tree but not committed. Include file paths and a description of each change. If there's nothing uncommitted, write "None — all work committed."]

**File:** `path/to/file.py`
**Change:** [Description of what was modified and why]
**Action:** [What the next agent should do — commit it, review it, revert it]

## Completed This Session

[What was done and committed. Include commit hashes if available.]

- `abc1234` — [commit message / description]
- `def5678` — [commit message / description]

## Next Steps

[Exactly what the next agent should do, in order. Numbered. Each step should be independently verifiable.]

1. [First step]
2. [Second step]
3. [Third step]

## Files to Read Before Executing

[List of files the next agent should read to understand the context. Keep this minimal — only what's needed, not everything that's relevant.]

- This file (you're reading it)
- `path/to/relevant_doc.md` — [why they need it]
- `path/to/modified_file.py` — [to verify the uncommitted edit]

## What NOT to Do

[Guardrails for the next agent. Common mistakes, scope boundaries, files to avoid.]

- Do NOT modify [file/system] — [reason]
- Do NOT start [task] — [it's being handled elsewhere / not ready yet]

---

**End of Handoff**
```

---

## Usage Notes

- **Write this BEFORE you run out of context**, not after. By the time you're summarizing for rollover, you've already lost the ability to write a detailed handoff.
- **The "Next Steps" section is the most important part.** If the next agent only reads one section, it should be this one.
- **Include commit hashes.** The next agent can `git log` to verify what was actually committed vs what the handoff claims.
- **"Files to Read" should be 3-5 files, not 15.** If the next agent needs to read 15 files, the handoff isn't self-contained enough. Add more context to the handoff itself.
- **Be honest about uncommitted work.** A handoff that says "all done" when there's a dirty working tree will confuse the next agent. State exactly what's uncommitted and why.
