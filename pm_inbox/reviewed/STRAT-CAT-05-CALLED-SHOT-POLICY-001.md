# STRATEGY — Called Shot Policy
## CAT-05: Anatomy Targeting — DECIDED

**Artifact ID:** STRAT-CAT-05-CALLED-SHOT-POLICY-001
**Type:** strategy / policy_decision
**Status:** DECIDED — 2026-02-26
**Lifecycle:** ACTIONED
**Filed:** 2026-02-26
**Filed by:** Slate (PM), sourced from REDTEAM-CREATIVE-ADVERSARIAL-001 CAT-05
**Authority:** Thunder (PO) — DECIDED

---

## DECISION — Thunder (2026-02-26)

**Option A now. Explicit upgrade path to Option C when scaffold is validated.**

### Canonical Policy Text

> **Core engine does not implement freeform called-shot anatomy penalties or effects. Unsupported called shots are denied as direct mechanics and routed to the nearest named mechanic (Disarm, Trip, Sunder, Grapple) where applicable. Flavor narration may describe targeting intent, but no additional mechanical effect is granted unless supported by a formal subsystem or a validated judgment scaffold.**

### Flavor narration rule

Limited narration flavor is permitted — but only when it is explicitly non-mechanical. Narration must not imply an effect that was not mechanically resolved. Narration-implies-effect is a hallucination vector (see CAT-14).

### Upgrade trigger (pre-committed)

Revisit to Option C path when:
1. `WO-JUDGMENT-SHADOW-001` is ACCEPTED and shadow log sink is confirmed live
2. `PROBE-JUDGMENT-LAYER-001` closes with results that support controlled improvised adjudication
3. Thunder authorizes the upgrade

Until those three conditions are met, Option A holds. No exceptions.

### Gate tests required (filed with WO when drafted)

1. Unsupported anatomy target → no invented mechanic emitted
2. Nearest named mechanic suggested correctly (or clarification emitted if none maps)
3. No extra penalties/conditions applied without subsystem support
4. Narration text does not imply non-existent mechanical effect
5. Event log records denial/remap cleanly (auditable)
6. Fail-closed when target intent is ambiguous ("I go for the eyes" with no inferable anchor)

---

## The Issue

Players will say:

> "I target his sword hand." "I go for the eyes." "I cut out his tongue." "I sever the tendons in his legs."

D&D 3.5e core does **not** support called shots. PHB has no anatomy targeting system. The rules provide:

- **Disarm** — removes a held weapon
- **Grapple** — restrains the target
- **Sunder** — destroys a held item
- **Trip** — knocks prone

None of these are "I target a specific body part." But players will phrase actions as if they are.

**Current engine behavior:** HALLUCINATE. No policy exists. The LLM will invent anatomy rules on the fly. Results are inconsistent across sessions.

---

## Why This Is a Strategy Item, Not a WO

This is not a missing feature. It is a missing policy. The implementation depends entirely on which of the following Thunder authorizes:

### Option A — Hard Denial with Routing

Called shots are not supported in core 3.5e. When detected:
1. Engine emits a clarification / denial: "Called shots are not a core 3.5e mechanic."
2. Engine offers the closest supported mechanic: "Did you mean to Disarm / Trip / Sunder / Grapple?"
3. No anatomy damage applied. Action routed to player choice.

**Pros:** Mechanically clean. No invented rules. Consistent.
**Cons:** Frustrating for players who expect some anatomy interaction. Feels like a hard "no."

### Option B — Narration-Only Acknowledgment

Called shots resolve as normal attacks mechanically. The narrative describes the targeting flavor but no special mechanical effect is applied.

> "You swing for his sword arm — roll to hit normally. On a hit, you narrate the impact."

**Pros:** Preserves player agency in fiction. No invented rules. Easy to implement.
**Cons:** Players will expect mechanical consequence. Second time they try it, they'll push harder.

### Option C — Route to Judgment Scaffold

Called shots that have a plausible mechanical anchor (targeting weapon hand → Disarm, targeting legs → Trip) are routed to the judgment scaffold for synthesis. The scaffold proposes the nearest legal mechanic. No anatomy damage invented.

**Pros:** Handles the "spirit of the action" without hallucinating anatomy rules. Judgment layer does the mapping work.
**Cons:** Requires judgment scaffold to be in place (Phase 0 / Phase 1). Cannot implement until scaffold is live.

### Option D — Optional Subsystem (Future)

Defer called shots to a future optional subsystem (e.g., Arms and Equipment Guide / Unearthed Arcana rules). Mark as NOT SUPPORTED in core mode. Implement as a module that can be enabled per-campaign.

**Pros:** Keeps core engine clean. Allows future expansion.
**Cons:** Deferred indefinitely without a clear trigger.

---

## PM Recommendation

**Option A + Option C combined, sequenced:**

- **Now (pre-scaffold):** Option A. Hard denial with routing to nearest named mechanic. Explicit, consistent, no hallucination. Players know where they stand.
- **After scaffold lands (Phase 1):** Upgrade to Option C. Judgment scaffold handles "I target his sword hand → Disarm intent synthesis." Named mechanic routing remains the fallback.

Option B is not recommended — narration-only with no mechanical distinction is a temporary patch that generates player frustration without resolving the policy.

Option D is not recommended as a primary track — "future optional module" is where features go to die.

---

## Decision Required

~~Thunder: which option? Ruling locks the implementation WO scope.~~

**DECIDED — Option A now, Option C when scaffold is validated. See DECISION section above.**

~~Until Thunder calls it: no WO is drafted for called shot handling. No builder touches this.~~

**WO is now draftable.** Draft when Batch D clears and capacity opens. Do not block on it.

---

## Blocking Status

**Non-blocking** — called shot behavior defaults to LLM hallucination in the interim, which is the current state. This is not getting worse. It just needs a policy before it can get better.

**Do not file a WO until Thunder makes the call.**

---

## Parent Documents

- `docs/design/REDTEAM-CREATIVE-ADVERSARIAL-001.md` — CAT-05
- `docs/design/STRAT-AIDM-JUDGMENT-LAYER-001.md` — judgment scaffold strategy

---

*Filed 2026-02-26 — Slate (PM). DECIDED 2026-02-26 — Thunder (PO). Option A now; Option C upgrade path pre-committed pending scaffold validation.*
