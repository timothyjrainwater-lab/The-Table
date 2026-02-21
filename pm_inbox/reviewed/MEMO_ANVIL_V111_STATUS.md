# MEMO: Anvil Kernel v1.1.1 — Status Ping

**From:** Anvil (Squire seat)
**Date:** 2026-02-22
**Lifecycle:** NEW
**Type:** FYI — no action required

---

## Status

Anvil kernel upgraded to v1.1.1. Three micro-patches applied. Protocol v1.1 unchanged — these are Anvil-side boot infrastructure only.

## What Changed (non-blocking, Anvil-side only)

1. **Capsule de-dupe:** "Still Broken" prose replaced with finding IDs only — avoids drift between capsule and Findings Register.
2. **Charter marker:** CHARTER_REV + CHARTER_ID added inside Charter block — version is now machine-readable.
3. **Boot absorb step:** AGENDA_BIND + CONSISTENCY_PING added as boot steps 4-5 — capsule content now explicitly bound to working state on every boot.

## Pointers

- Kernel: `D:\anvil_research\ANVIL_REHYDRATION_KERNEL.md` (v1.1.1)
- Protocol (unchanged): `docs/protocols/MEMORY_PROTOCOL_V1.md` (v1.1, commit f392b1e)

## My Next Step

Proceeding with next bounded milestone per Thunder's direction. No response needed.
