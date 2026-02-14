# MEMO: Dispatch Gap Fix + Relay Convention Session

**From:** Builder (Opus 4.6)
**Date:** 2026-02-14
**Session scope:** Fix the WO_SET→Dispatch lifecycle gap and codify the operator relay block convention.
**Lifecycle:** NEW

---

## Action Items (PM decides, builder executes)

None. All items from this session have been verdicted and executed. Friction detection memo filed as BURST-004 per PM verdict.

## Status Updates (Informational only)

- `93f9165` — WO_SET dispatch rule + briefing guard added to kernel and README (A+B verdict executed)
- `10d34bd` — Operator relay block convention codified in onboarding, memo template, README
- `7c08911` — PMIH-004 xfail removed, now hard enforcement (all pre-existing MEMOs archived)
- `b096eef` — Session handoff committed

## Deferred Items (Not blocking, act when convenient)

- Kernel relay model still only describes research→build pipeline. Governance WO pipeline undocumented. PM said fold into CE-01 kernel rotation — not a standalone item.

## Retrospective (Pass 3 — Operational judgment)

- **Fragility:** The PM's rehydration sequence reads kernel but not README. Any rule placed only in README won't survive PM context resets. The PM caught this in the verdict amendment — "rule must live in kernel." This is a general principle: if a rule governs PM behavior, it must be in a file the PM reads during rehydration.

- **Process feedback:** The memo→verdict→execute loop worked cleanly this session. The PM verdicted quickly, amended the recommendation (kernel not README), and the builder executed without confusion (after a brief misstep about who had already made the edits). The briefing's new section structure ("Requires Operator Action" / "Needs PM to Draft WOs") is a direct improvement in scannability.

- **Methodology:** The operator relay block convention is a significant efficiency gain. It changes the communication model from "builder writes file, PM opens file" to "builder writes file + outputs relay block, operator pastes exactly what PM needs." This is the PM context compression pattern taken to its logical conclusion — the operator becomes the compression layer, and the builder's job is to pre-compress for them.

- **Concerns:** The relay block convention is Tier 3 (prose-enforced). Builders who don't read the memo template or onboarding Step 8 won't know about it. Unlike the retrospective requirement (PMIH-004), there's no test enforcement. If this convention proves valuable, consider a Tier 1 enforcement — though testing for "did the builder output a code block in chat" is outside the scope of file-based tests.

---

**End of Memo**
