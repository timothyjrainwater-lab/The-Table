# Sonnet Agent Notes

Shared communication channel for Sonnet implementer agents (A, B, C, D) to flag
observations, concerns, and questions for Opus (principal engineer) and Aegis (PM).

**How this works:**
- When you notice something during implementation that doesn't belong in a commit
  or test file, append an entry here.
- Opus reads this file at the start of each session and triages entries.
- Thunder may relay entries to Aegis (GPT) when relevant.
- After an entry has been addressed, Opus moves it to the `## Resolved` section.

**When to write here:**
- You made a judgment call that could have gone either way (document it)
- You found something that looks like a bug but isn't in your scope to fix
- You hit an ambiguity in a work order and chose an interpretation
- You noticed a pattern violation in existing code while working nearby
- You have a suggestion for a future work order

**Entry format:**
```
### [DATE] — [AGENT LETTER] — [SHORT TITLE]
**Context:** What you were working on
**Observation:** What you noticed or decided
**Action taken:** What you did (or "none — flagging only")
```

---

## Active Notes

_(No entries yet)_

---

## Resolved

_(Opus moves addressed entries here)_
