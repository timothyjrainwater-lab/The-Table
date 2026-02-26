# DEBRIEF — WO-SEC-REDACT-002
# Session State HP Redaction: _build_session_state() Entity Dict Stripping

**Verdict:** ACCEPTED 10/10
**Gate:** ENGINE-SEC-REDACT-002
**Date:** 2026-02-26
**WO:** WO-SEC-REDACT-002
**Finding closed:** FINDING-SEC-SESSION-STATE-001

---

## Pass 1 — Per-File Breakdown

### `aidm/server/ws_bridge.py`

**Changes made:**

1. `_ENTITY_STRIP_PLAYER` frozenset — canonical list of raw entity dict keys redacted for PLAYER connections: `hp_current`, `hp_max`, `temporary_modifiers`, `active_poisons`, `active_diseases`, `wild_shape_saved_stats`, `original_stats`

2. `_player_entity_fields(entity: dict) -> dict` — strips `_ENTITY_STRIP_PLAYER` keys from entity dict before inclusion in session state payload.

3. `_dm_entity_fields(entity: dict) -> dict` — pass-through for DM connections (full entity data).

4. `_build_session_state(self, session, in_reply_to, role: ConnectionRole) -> SessionStateMsg` — added `role` parameter; filters each entity via the appropriate helper before constructing `SessionStateMsg.entities`.

5. `_handle_control()` — added `role` parameter threading. Both call sites (join + resume) resolve role via `_assign_role(session_id)` and pass it forward.

**Key design note:** Two distinct filter families now live in the module:
- `_player_token_fields` — operates on TokenAdd schema keys (`hp` / `hp_max`) — established by WO-SEC-REDACT-001
- `_player_entity_fields` — operates on raw engine entity dict keys (`hp_current` / `hp_max` / internal state) — established by this WO

These are semantically different namespaces. Conflating them would produce a false green: stripping `hp` from a TokenAdd object does not strip `hp_current` from a raw entity dict.

**Pass 3 catch (builder):** A test fixture was using a bare string literal for `TEMPORARY_MODIFIERS` instead of the constant. Would have been a false green if the constant value ever changed. Fixed before gate run.

**SR2-07 resolution:** PC entity `hp_current` is stripped for PLAYER connections. No ownership model exists; strip-all is the correct safe default. Documented for future revisit if ownership tracking is added.

**Open findings table:** None. FINDING-SEC-SESSION-STATE-001 closed.

---

## Pass 2 — PM Summary (≤100 words)

WO-SEC-REDACT-002 ACCEPTED 10/10. Second HP disclosure path closed. `_build_session_state()` now role-filters all entity dicts — PLAYER receives entities with `_ENTITY_STRIP_PLAYER` keys removed (hp_current, hp_max, temporary_modifiers, active_poisons, active_diseases, wild_shape_saved_stats, original_stats). DM receives full data. Join and resume both pass role. WO-SEC-REDACT-001 gate 29/29 unchanged. `_ENTITY_STRIP_PLAYER` frozenset is the single update point for any future sensitive entity field. FINDING-SEC-SESSION-STATE-001 CLOSED. HP disclosure path fully closed across all three vectors.

---

## Pass 3 — Retrospective

**Drift caught (builder):** Test fixture used bare string literal for TEMPORARY_MODIFIERS. If the constant value changed, the test would have silently passed with the wrong key. Fixed before gate — correct catch.

**Pattern that matters:** The two-namespace split (`_player_token_fields` for TokenAdd schema keys vs `_player_entity_fields` for raw entity dict keys) is the structural insight of this WO. These key spaces look similar but are distinct. `hp` ≠ `hp_current`. A developer adding a new sensitive field to the engine entity dict could easily add it only to `_player_token_fields` and miss `_ENTITY_STRIP_PLAYER` — leaving session_state open again.

**Recommendation:** Any future WO that introduces a new internal entity field carrying sensitive data should explicitly answer: "Does this field need to be added to `_ENTITY_STRIP_PLAYER`? Yes/No." This should be a line item in Integration Seams, not left to the builder to infer.

**HP disclosure path — fully closed:**
- GAP-WS-003: TokenAdd path (hp/hp_max schema) — CLOSED by WO-SEC-REDACT-001
- GAP-WS-004: hp_changed StateUpdate passthrough — CLOSED by WO-SEC-REDACT-001
- FINDING-SEC-SESSION-STATE-001: session_state raw entity dict path — CLOSED by this WO

**How FINDING-SEC-SESSION-STATE-001 was caught:** WO-SEC-REDACT-001 builder Pass 3. Not a spec review, not a code audit — a retrospective after the work was done. The debrief format is what found it. Without Pass 3, WO-SEC-REDACT-001 closes at 29/29 and the session_state path stays open with a false sense of security. The format works.

---

*Debrief filed by Slate (PM) on builder verdict receipt.*
