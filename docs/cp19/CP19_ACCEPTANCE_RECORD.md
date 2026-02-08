# CP-19 Acceptance Record (FINAL)
**Status:** FINAL — All criteria met
**Date:** 2026-02-08
**Test Count:** 730 tests passing (728 baseline + 2 CP-19B patch)

---

## 1) Degradations (preserved as designed)
- Shallow water = difficult terrain only; no swim/drowning/underwater combat
- Steep slopes use deterministic placeholder Balance check logic
- No weather, no magical terrain, no persistent terrain changes

---

## 2) Gate Safety Attestation — ✅ VERIFIED
Mitigations against gate crossings:
- Read-only terrain (avoid G‑T3D) ✅
- No hazard entities (avoid G‑T3A) ✅
- Situational modifiers only (avoid G‑T2A) ✅
- No relational terrain effects (avoid G‑T3C) ✅

---

## 3) Determinism Attestation — ✅ VERIFIED
Threat model applied:
- No unordered iteration; deterministic sort keys ✅
- Falling ordering: AoOs → movement → fall resolution ✅
- No terrain RNG leakage (only falling damage rolls) ✅
- 10× replay tests pass ✅

---

## 4) Evidence (collected)
- ✅ Tier‑1 unit tests for terrain lookup + cover + elevation (41 tests)
- ✅ Tier‑2 integration tests for forced movement into pit/ledge and cover affecting attacks (10 tests)
- ✅ PBHA: deterministic 10× replay hash stability scenario
- ✅ CP-19B: Failure path hazard tests (2 tests added)

---

## 5) Deferrals (unchanged)
Design deferrals include skills (Balance/Tumble/Jump placeholders), transformation history, hazard entities, persistent terrain damage, weather, underwater combat, flight, magical terrain.

---
**End (draft).**
