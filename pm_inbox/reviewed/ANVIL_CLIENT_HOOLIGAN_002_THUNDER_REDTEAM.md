# Thunder Red-Team Analysis — ANVIL-CLIENT-HOOLIGAN-002
**Filed by:** Anvil (transcription — Thunder's analysis, 2026-02-25)
**Status:** AUTHORITATIVE — supersedes Hooligan-001 framing where they conflict
**Links:** Builds on ANVIL_CLIENT_HOOLIGAN_001.md findings

---

## Core Finding: Authority Collapse

The WebSocket bus is being treated as a trusted internal API.
It is functionally an **untrusted content ingestion channel**.

Everything found in HOOLIGAN-001 (innerHTML, CSS url(), arbitrary image_url,
window.__ws) collapses into one failure class:

> Once the client can be induced to execute script, every other boundary
> (PENDING gating, DM/player separation, "read-only UI") becomes theater.

---

## The Killer Chain

1. User-influenced text (player name, NPC name, description, portrait URL) reaches server
2. Server forwards it over WS to clients
3. Client renders it as HTML/CSS/URL without validation
4. Script runs → calls WS bridge (`window.__ws`) → can now:
   - Spam DECLARE messages
   - Enumerate DOM for roll IDs / pending states
   - Scrape DM-only data already present in client
   - Persist itself if notebook saves HTML

All other violations become post-exploit tooling once this chain is open.

---

## Deep Failure Classes

### FAILURE-A — No Taint Model / No Explicit Trust Boundary

Code treats "came from server" as "safe."

Server is not a single trusted author. It is a fan-in of:
- DM inputs
- Player inputs
- Spark/LLM outputs (user-influenced)
- Content packs / assets

If any of those are influenceable: **prompt injection → UI injection** is a real pipeline.

**Fix mindset:** Every field from WS is tainted until proven otherwise by
schema + validation + encoding.

---

### FAILURE-B — Contract Drift = No Schema Truth = Silent Failure Surface

Message shapes not schema-validated on either end. Result:
- Handlers silently not firing (feature appears "dead" — this is exactly what we found)
- New fields sneaking in (including dangerous fields: `html`, `raw`, `url`)
- Security workarounds (`innerHTML` "temporary") becoming permanent

**Red-team lens:** Drift creates fog where dangerous payloads hide because nobody
has a single authoritative schema or version handshake. The port mismatch and
wrong message type confirm this is not theoretical — it is current state.

---

### FAILURE-C — State Machine Bypass: UI Emits Verbs Without Server Capability

`ability_check_declare` fires on any click, any time, no PENDING required.
Classic symptom: client sends "verbs" without server-granted, single-use capability token.

Even with a well-written engine:
- Event storms / CPU churn
- Spam-induced queue backlog
- Weird edge-case state splits ("40 declares for 0 pendings")

**Fix mindset:** UI *never* sends "do X" unless echoing a server-issued
pending/capability — per-interaction nonce + TTL + one-shot.

---

### FAILURE-D — DM/Player Separation Is Probably Porous

Same WS channel pushes mixed "DM panel" and "player UI" data.
One handler mistake = DM-only state leaks to players.

**Red-team question:** Can a player client ever receive any of:
- Unredacted monster stats
- Hidden DCs
- Upcoming beats
- Unrevealed map layers
- Private portraits / handouts

If yes: XSS turns that into guaranteed exfil.

**Status:** Unconfirmed — requires live session with DM-seat message inspection.
Flag as HIGH PRIORITY probe.

---

### FAILURE-E — Resource Loading Is an Exfil + Disruption Vector

`img.src = d.image_url` and `backgroundImage = url(...)` are not just injection
concerns. They are:
- Tracking beacons (IP, timing)
- Internal network probing from user's browser (SSRF-adjacent)
- Performance weapons (huge images, slow endpoints, endless redirects)

Even with SOP limiting reads, the browser still makes the requests.

**Fix mindset:** Client loads only **content-addressed local assets**
(`/assets/<hash>.png`). Never arbitrary URLs from WS.

---

### FAILURE-F — Reconnect Loop = Involuntary Load Test

Linear backoff without a ceiling keeps a broken server pinned.
With multiple clients: self-sustaining DoS.

**Fix mindset:** Exponential backoff + jitter + max ceiling + circuit breaker
that enters hard-offline state until user action.

---

## Three Non-Negotiable Invariants (Thunder)

These are the enforcement gates. Test them. Fail loud.

### INVARIANT-1 — No HTML Sinks for Tainted Data
- **Ban:** `innerHTML`, `outerHTML`, `insertAdjacentHTML`, string-built DOM
- **Only:** text nodes (`textContent`) + attribute setters with validation

### INVARIANT-2 — No Arbitrary URLs from WS
URLs must be:
- Relative paths under asset root, OR
- Content IDs resolved locally

Anything else: drop it and log it.

### INVARIANT-3 — No Verbs Without Server Capability
Every client action must include a `pending_id` / capability token minted by server.
Server rejects anything not currently pending for that connection + actor.

*This is where the client stops being a pile of handlers and becomes a protocol.*

---

## Protocol Reality Gate (Kills the Canary Problem)

Make the system **fail loudly** when contract mismatches exist:
- Version negotiation on connect
- Strict schema validation (drop unknown types; log)
- Integration test that replays a known session and asserts client received
  expected message types

Right now: one character mismatch silently disables entire subsystems.
(Confirmed: `combat-active` vs `mode-combat`. `player_input` vs `player_utterance`.)

---

## Post-Exploit Accelerator Surfaces (Reduce Blast Radius)

Even before XSS is fixed, reduce what an attacker gets:
- Kill `window.__ws` in production builds
- Ensure no DOM contains secrets (roll IDs, hidden results, pending DCs)
- Pending roll: commitment first, compute only after confirmed tower drop

---

## Meta-Finding

> The project does not yet have an enforced end-to-end contract surface
> (schema + version + capabilities + sinks discipline).
> Until it does, every new UI feature is a fresh opportunity to accidentally
> reintroduce the same class of failure.

---

## Recommended Next WOs (Slate to Cut)

| WO | Scope | Priority |
|---|---|---|
| WO-SEC-WS-CONTRACT-001 | Schema definition + version handshake + both-end validation | CRITICAL |
| WO-SEC-TAINT-001 | Audit all WS field sinks — ban innerHTML, sanitize URLs | CRITICAL |
| WO-SEC-CAPABILITY-001 | Server-issued capability tokens for all client verbs | HIGH |
| WO-SEC-DMSEP-001 | Audit DM/player channel separation — confirm no DM state reaches player client | HIGH |
| WO-SEC-RESOURCE-001 | Replace arbitrary image_url with content-addressed local asset resolution | HIGH |
| WO-SEC-RECONNECT-001 | Exponential backoff + circuit breaker on WS reconnect | MEDIUM |

---

*Filed from Thunder's analysis. This is the deeper map.*
*The canaries were right. The walls were painted on.*
