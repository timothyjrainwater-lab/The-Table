# Debrief: WO-CONDITION-EXTRACTION-FIX

**From:** Builder
**Date:** 2026-02-14
**Lifecycle:** DELIVERED
**Commit:** `acdf410`
**Source WO:** WO-CONDITION-EXTRACTION-FIX_DISPATCH.md

---

## Results Summary

**All 6 success criteria MET.**

| Criterion | Status | Evidence |
|---|---|---|
| condition_applied non-None for `payload["condition"]` | MET | Smoke test D6 PASS, `condition_applied="paralyzed"` |
| target_name resolves for `payload["entity_id"]` | MET | `target_name="Bandit Lieutenant"` in D6 |
| Backwards compatibility (`condition_type`, `target_id`) | MET | Existing test `test_condition_applied_with_condition_type` still passes (maneuver-style keys) |
| New tests cover both variants | MET | 2 new tests in `test_narrative_brief_046b.py` |
| Existing tests pass | MET | 5,528 passed (2 new), 4 pre-existing failures unrelated |
| Smoke test D6 passes | MET | 44/44 stages PASS (was 43/44) |

### Changes Made

**Production code:** 2 blocks in `aidm/lens/narrative_brief.py`

1. **`condition_applied` handler (lines 537-549):** Added `payload.get("entity_id")` to target fallback chain and `payload.get("condition")` to condition fallback chain. Now accepts both spell-style keys (`entity_id`, `condition`) and maneuver-style keys (`target_id`, `condition_type`).

2. **`condition_removed` handler (lines 551-561):** Expanded from single-line `payload.get()` calls to full fallback chains matching the `condition_applied` pattern. Now accepts both `condition` and `condition_type` for the condition name, and both `entity_id` and `target_id` for target identity.

**Tests:** 2 new tests in `tests/test_narrative_brief_046b.py`

- `test_condition_applied_with_spell_style_keys`: Verifies `payload={"entity_id": ..., "condition": "paralyzed"}` produces `condition_applied="paralyzed"` and `target_name` resolved.
- `test_condition_removed_with_spell_style_keys`: Verifies `payload={"entity_id": ..., "condition": "paralyzed", "reason": "concentration_broken"}` produces `condition_removed="paralyzed"` and `target_name` resolved.

### Dual-Producer Validation

Confirmed two event producers emit `condition_applied` events with different key vocabularies:

| Producer | Target Key | Condition Key |
|---|---|---|
| `play_loop.py` (spell path) | `entity_id` | `condition` |
| `maneuver_resolver.py` (trip, grapple) | `target_id` | `condition_type` |

Both are now handled by the fallback chain. The assembler is the single consumer that must accept both vocabularies.

---

## Friction Log

Zero wasted cycles. The WO was precisely scoped — the smoke test debrief already identified the exact lines, the exact key mismatch, and the exact fix pattern. Assumption validation (read play_loop emission, grep for `condition_type` producers, confirm maneuver_resolver uses different keys) took under 2 minutes and confirmed everything the WO stated. The `condition_removed` handler had the same bug pattern but was not called out in the WO — caught it during the fix.

## Methodology Challenge

The WO says "fix the consumer" (assembler) rather than "fix the producer" (play_loop or maneuver_resolver). This is the right call for this specific case — the producers already have downstream consumers that depend on their current key names. But the root cause is that there's no shared event schema enforcing vocabulary. Two producers emit the same event type (`condition_applied`) with different payload key names. A future WO should define an `EventPayloadSchema` or at minimum a docstring contract in `box_events.py` that says "condition_applied events MUST use these keys." Without that, every new producer will guess differently and every consumer will need a new fallback.

## Field Manual Entry

**15. Dual-producer event vocabulary:** The `condition_applied` event type is emitted by two producers with different key names: `play_loop.py` uses `entity_id` + `condition`, `maneuver_resolver.py` uses `target_id` + `condition_type`. When writing consumers (NarrativeBrief assembler, validators, loggers), always check BOTH producers' emission code. The fallback chain pattern `payload.get("key_a") or payload.get("key_b")` handles vocabulary divergence without requiring producer changes. Grep for the event type across `aidm/core/` to find all producers before writing a consumer.
