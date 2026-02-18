# DEBRIEF: WO-UI-01 — Table UI Phase 1

**Commit:** `d172999`
**Gate F:** 10/10 PASS
**Regression:** 111/111 PASS (Gates A-E intact)

---

## 1. Scope Accuracy

The WO specified 7 contract changes across backend and frontend. All 7 were delivered:

1. **Frontend bootstrap** — `client/` with Three.js 0.170 + TypeScript 5.7 + Vite 6. `npm install` succeeds, `npm run dev` starts, `npx vite build` produces production bundle. All licenses MIT/Apache.
2. **Table scene + camera postures** — Three.js scene renders table surface with 3 zone boundaries (map/player/DM). 3 camera postures (STANDARD, DOWN, LEAN_FORWARD) with smoothstep interpolation, interruptible transitions, keyboard controls [1/2/3].
3. **PENDING handshake types** — `PendingRoll`, `PendingPoint` as frozen dataclasses in `aidm/ui/pending.py`. `PendingStateMachine` enforces one-at-a-time rule.
4. **REQUEST intent types** — `DeclareActionIntent`, `DiceTowerDropIntent` as frozen dataclasses. No outcome/legality fields. No banned action-verb names.
5. **PENDING round trip** — Frontend receives PENDING_ROLL via WebSocket, shows overlay, player clicks to send DiceTowerDropIntent, overlay clears. State machine enforces matching handles.
6. **BeatIntent display** — Canvas-textured 3D card on table surface. Receives BeatIntent data via WebSocket state_update messages. Click sends DeclareActionIntent.
7. **Gate F tests** — 10 tests across 4 categories (UI-F1 through UI-F4), all PASS.

Scope matched cleanly. No scope creep, no deferred items.

## 2. Discovery Log

- **Node.js v25.5.0 available** — no hard stop on toolchain.
- **`aidm/ui/` already existed** with `character_sheet.py`. Added `pending.py` and `camera.py` alongside it. Did not modify existing `__init__.py` — new modules are imported directly.
- **ws_protocol.py uses JSON over WebSocket** with `to_dict()`/`from_dict()` pattern and `msg_type` discriminator. PENDING/REQUEST types follow the same frozen dataclass + `to_dict()`/`from_dict()` pattern but live in `aidm/ui/pending.py` rather than extending `ws_protocol.py`, keeping the UI boundary layer separate from the core protocol.
- **License gate passed** — Three.js (MIT), TypeScript (Apache-2.0), Vite (MIT). No GPL/AGPL.
- **Starlette server route** at `/ws` confirmed working. Frontend connects to `ws://localhost:8765/ws` by default.

## 3. Methodology Challenge

The WO was clear and executable. Two minor points:

- **PENDING/REQUEST module location** was left as "confirm path before writing." The WO suggested `aidm/ui/pending.py` or extending `ws_protocol.py`. I chose `aidm/ui/pending.py` to keep the UI boundary gate clean, but the WO could have been prescriptive.
- **BeatIntent delivery mechanism** was underspecified — "polled or pushed" with builder discovering the cleanest path. I used the existing `state_update` message type with `update_type=director_beat_selected` plus a dedicated `beat_intent` message handler as fallback. A production WO should formalize which server→client message type carries BeatIntent data.

## 4. Field Manual Entry

**#28: Frontend→backend contract types live in the backend.** PENDING/REQUEST types are Python frozen dataclasses in `aidm/ui/`. The frontend reads/writes JSON matching `to_dict()`/`from_dict()` shapes. The backend is the source of truth for the contract schema; the frontend consumes it. This prevents schema drift when both sides share the same JSON shapes.
