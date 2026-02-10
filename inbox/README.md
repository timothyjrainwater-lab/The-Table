# Inbox — Drop Zone for Incoming Artifacts

This folder is a staging area for artifacts to be processed by Claude.

## Workflow

1. **Drop** files here (pamphlets, drafts, skeletons, checklists)
2. **Attach a pamphlet** explaining what each file is and how to handle it
3. **Claude processes** according to instructions:
   - Documentation → moves to `docs/cpXX/`
   - Test skeletons → fills in and moves to `tests/`
   - Drafts → stored with DRAFT status until authorized
4. **Processed files get deleted** from this folder

## File Naming Conventions

Use prefixes to clarify intent:

| Prefix | Meaning |
|--------|---------|
| `CPXX_` | Capability packet artifacts |
| `*_DRAFT.md` | Not yet authorized for implementation |
| `*_skeleton.py` | Test template to be filled in |
| `*_PAMPHLET.md` | Instructions for processing other files |

## Current Status

Empty — all artifacts processed.

---
*Last cleaned: 2026-02-08*
