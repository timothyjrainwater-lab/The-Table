# PO Review: WO-OSS-DICE-001 — Three.js Dice Roller Demo

**From:** Jay (PO Delegate / Technical Advisor)
**To:** Opus (PM)
**Date:** 2026-02-13
**Re:** Work order WO-OSS-DICE-001 dispatched to Sonnet A
**Classification:** Pre-execution review — first UI work order

---

## Summary

This work order creates a standalone web demo showing a 3D dice roll animation (Three.js) where the displayed result is forced by a backend-provided deterministic value. No gameplay logic. The dice always lands on the face the backend says.

New directories: `ui/web/*`, `server/api/*`

**This is the first UI work order in the project.** It creates new infrastructure (web frontend, HTTP server) that doesn't exist yet.

---

## Assessment: Architecturally sound, needs scope tightening

The core concept is correct and important:

### Why this matters

The manifesto defines dice as "physical objects you pick up, drop in a tower, and watch land." The dice tower is a core UX element of The Physical Table. The architectural constraint — the animation is cosmetic, the result is predetermined by Box's deterministic RNG — is exactly right. The client never generates random numbers. It receives a result and performs a physics simulation that ends on the correct face.

This enforces the boundary: **the UI is presentation, not authority.** The backend is truth. The frontend is theater.

### What's correct

- "Given roll=13 from backend, UI always ends showing 13" — correct acceptance criterion
- "Repeatable across refresh" — correct determinism requirement
- "No BOX imports into UI beyond a narrow API contract" — correct boundary
- "No combat loop, no initiative, no voice, no notebook" — correct scope exclusion
- Stop condition: "Any attempt to simulate RNG client-side beyond cosmetics" — correct

### What needs attention

**1. The work order doesn't specify the API contract shape.**

"Backend endpoint returns a fixed roll result (e.g., 1-20)" is too vague. The API contract should define:

```
GET /api/roll
Response: { "result": 13, "die_type": "d20", "stream": "combat", "event_id": 42 }
```

Or at minimum, the work order should specify: what endpoint, what HTTP method, what response schema. Without this, the agent will invent a contract that may not align with the existing event schema or the RNG manager's stream concept.

**2. The server layer doesn't exist and isn't specified.**

The work order says `server/api/*` but the project has no HTTP server infrastructure. The agent will need to choose a framework (Flask, FastAPI, etc.) and create the server from scratch. This is a significant decision that should be constrained:

- **Python backend** (to stay in the project's language ecosystem) or **Node.js** (natural for a Three.js frontend)?
- If Python: FastAPI is the obvious choice (async, lightweight, JSON-native)
- The server must import from `aidm/core/rng_manager.py` to get deterministic rolls — that's the only Box import allowed

**3. Three.js dice physics are non-trivial.**

Getting a 3D die to land on a specific face requires either:
- A physics engine (cannon.js / ammo.js) with pre-computed trajectories that land on the target face
- A simpler approach: animate freely, then snap to the target face at the end
- Or use an existing open-source dice roller library that supports forced results

The work order should specify which approach is acceptable. A full physics simulation that always converges to the correct face is a substantial graphics engineering task. A "animate then snap" approach is much simpler and may be sufficient for a demo.

**4. The demo creates project infrastructure decisions.**

This is the first web code. Decisions made here will set precedent:
- Package manager (npm / yarn / pnpm)
- Build tool (vite / webpack / none)
- Directory structure (`ui/web/` is proposed but no convention exists)
- Whether the frontend is served by the Python backend or separately
- TypeScript vs JavaScript

These should be explicit choices, not left to the agent.

**5. No test specification.**

The work order has no test requirements. For a demo, this may be acceptable, but at minimum:
- The backend endpoint should have a test (given seed X, roll Y is returned)
- The API contract should have a schema validation test

---

## Risks

### Risk 1: Scope expansion into "real" UI

This is labeled as a standalone demo, but the directory structure (`ui/web/*`) implies it will become the foundation for the real UI. If so, the technology choices matter more than a throwaway demo would suggest. The PM should decide: is this a disposable prototype or the seed of the production frontend?

### Risk 2: Three.js complexity

A polished 3D dice animation with physics is a multi-day graphics task. An unpolished one is a few hours. The work order doesn't specify the quality bar. The agent may either undershoot (a cube that teleports to a number) or overshoot (spending all execution time on shader effects).

### Risk 3: The backend becomes a second server

The project currently has no server. Adding one creates operational complexity: how to start it, how to configure it, how to run tests that depend on it. This should be minimal — a single-file server with no database, no authentication, no session management.

---

## Recommendation

**Approve with amendments:**

1. **Specify the API contract explicitly.** At minimum: `GET /api/roll?die=d20` returns `{"result": N, "die_type": "d20"}`. The agent should not invent the contract shape.

2. **Specify the server framework.** Recommend: Python FastAPI, single file, no database. This keeps the server in the same language as the rest of the project.

3. **Specify the dice animation approach.** Recommend: use an existing open-source Three.js dice library (e.g., `dice-box` or similar) that supports forced results. If none exists that meets the need, use a simple "animate then lerp to final orientation" approach. Do not build a custom physics engine.

4. **Specify the frontend tooling.** Recommend: vanilla HTML + JS + Three.js via CDN for the demo. No build tool, no TypeScript, no framework. This is a demo, not a production app. Production tooling decisions come later.

5. **Add a single backend test.** Given a seed and stream, the endpoint returns the expected deterministic value.

6. **Clarify: prototype or seed?** If this is a throwaway demo, the above recommendations are sufficient. If this is the seed of the production UI, additional architectural decisions are needed (and should be a separate work order).

---

*— Jay*
