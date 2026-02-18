# MEMO: Operator Framework Feedback — 3 Structural Changes for Coordination Framework Repo

**From:** PM (Aegis), documenting Operator (Thunder) directive
**Date:** 2026-02-14
**Lifecycle:** ACTIONABLE
**Scope:** Framework repo (swarm-forge or equivalent), not DnD engine repo

---

## 1. Enforcement Hierarchy Must Be Pattern 1

Currently buried as pattern 9 of 9. Move to pattern 1. This is the framework's actual contribution — the insight that test-enforced beats process-enforced beats prose-enforced.

Evidence from this project: `test_pm_inbox_hygiene.py` enforces lifecycle header conventions via pytest. That's tier 1 enforcement applied to the coordination protocol itself. Most frameworks stop at "write good docs." This one says "write a test that catches when the docs are wrong."

**Action:** Reorder patterns. Enforcement Hierarchy becomes pattern 1. Lead with it in README.

## 2. Failure Catalog Is the Differentiator, Not Patterns

The patterns are useful but generic-sounding ("Artifact Primacy" could come from any engineering blog). The failure catalog — real failures, real project, root causes traced to specific coordination breakdowns — is what nobody else has.

**Action:** Restructure README to lead with failure catalog stats. "30 bugs categorized into 8 error patterns" tells readers more in 5 seconds than "9 patterns and 5 templates." The patterns support the failures, not the other way around.

## 3. Add "Integration Canary" Pattern (Pattern 10)

The missing pattern discovered 2026-02-14: each agent builds and tests its piece, all unit tests pass, but nobody tries to use the product.

**Pattern name:** Integration Canary (or End-to-End Smoke Test)
**Problem:** Per-module WOs produce well-tested components. No WO covers "does the product work end-to-end?" Constraints produce consistency within modules but cannot produce integration across modules.
**Solution:** Before dispatching new infrastructure WOs, run one script that exercises the full path. Whatever breaks is your next WO. The failures prioritize the backlog better than any architecture audit.
**Evidence:** Dormant content_id pipeline, unregistered CrossValidateStage, NarrationValidator not wired into play loop — all discovered by trying to run the system, not by auditing documents.
**Already codified:** Integration Constraint Policy in kernel, WO-SMOKE-TEST-001 dispatch.

**Action:** Add as named pattern in framework repo. Document the DnD case study evidence.

## Additional Notes

- Keep DnD project test counts updated in framework README (currently 5,775, will grow after smoke test)
- The "former chef, English educator" framing is the actual differentiator — framework by someone who solved coordination with pure protocol because there was no technical fallback
- "Discovered bottom-up, not designed top-down" framing is correct and should stay prominent

---

*This memo documents Operator directives for framework repo updates. Not a DnD engine WO — no builder dispatch needed. PM or Operator executes directly in framework repo.*
