# Watch Synchronization Methodology (WSM-01)

**Source:** Aegis, 2026-02-21 ~18:54 CST-CN (10:54 UTC)
**Filed by:** Anvil
**Lifecycle:** ACTIONED
**Trigger:** Anvil's third timezone error in the project. Aegis solved at systems level.

---

Goal: **everyone speaks the same time** (timezone, day boundary, "today"), and every artifact is replayable against an unambiguous timestamp.

### 0) Single Source of Truth

* **Time Truth = UTC** for all logs, filenames, and WO artifacts.
* **Operator display time** may be local (America/Los_Angeles), but it is always **derived** from UTC.

**Rule:** If a timestamp appears without a timezone, it is **invalid**.

---

## 1) Canonical Time Format

Use **ISO 8601 with Zulu** (UTC):

* `2026-02-21T03:14:15Z`

Optional monotonic suffix if you want ordering under identical timestamps:

* `2026-02-21T03:14:15Z#001`

---

## 2) The Sync Ritual (2-minute)

### Trigger

* At **start of every work block**
* At **every -00 / -30 minute** boundary during active sessions (optional but strong)

### Script (copy/paste)

1. **Operator posts**:

   * `TIME_SYNC: <UTC-now> | LOCAL: <local-now> | TZ: America/Los_Angeles`
2. **All seats reply**:

   * `ACK_SYNC: <UTC-now-from-your-device> | DRIFT: <seconds>`

**Drift calculation:** `your_device_utc - operator_utc`

---

## 3) Drift Tiers + Action

|  Drift | Status | Action                                                                                            |
| -----: | ------ | ------------------------------------------------------------------------------------------------- |
|   ≤ 2s | GREEN  | No action                                                                                         |
|  3–10s | YELLOW | Re-sync device clock (NTP), re-ACK                                                                |
| 11–60s | ORANGE | Stop dispatching new WOs; fix clocks; re-run ritual                                               |
|  > 60s | RED    | Treat all timestamps since last GREEN as suspect; re-stamp artifacts with corrected UTC reference |

---

## 4) "Dispatch Time" and "Event Time"

To avoid ambiguity:

* **Dispatch Time** = time WO is issued (UTC)
* **Event Time** = time observed/occurred (UTC)
* **Record both** when they differ.

Example header snippet:

```
DISPATCH_UTC: 2026-02-21T03:14:15Z
EVENT_UTC:    2026-02-21T03:07:02Z
```

---

## 5) File/Artifact Naming Convention

Prefix every artifact with UTC date-time to prevent ordering disputes:

* `2026-02-21T031415Z_WO-002_DEBRIEF.md`
* `2026-02-21T031415Z_AEGIS_REHYDRATION_PACKET.md`
* `2026-02-21T031415Z_ANVIL_OBSERVATION_LOG.md`

If the file lives in Drive and Drive timestamps might drift: **the filename is the truth**, not Drive metadata.

---

## 6) Validation Gate (WSM-GATE-01)

Before any WO is considered "valid for merge/acceptance," it must include:

* `DISPATCH_UTC`
* `AUTHOR_TZ`
* `TIME_SYNC_REF` (the most recent `TIME_SYNC` line)

No `TIME_SYNC_REF` → WO is **incomplete**.

---

## 7) Minimal Tooling (recommended)

* All devices set to **automatic time** (NTP) + auto timezone.
* One shared "time truth" fallback:

  * `time.is/utc` (human check)
  * `date -u +"%Y-%m-%dT%H:%M:%SZ"` (CLI check)

You don't need both; pick one and standardize.

---

## 8) Edge Cases

### Cross-midnight ambiguity

Always reference **UTC date** for "today" in WOs. If you need local day semantics, add:

* `LOCAL_DAY: 2026-02-20 America/Los_Angeles`

### Voice / TTS logs

Any voice-session marker must be stamped with UTC at **start and end**:

* `VOICE_START_UTC`, `VOICE_END_UTC`

---

## 9) One-liner Policy (for the Golden Ticket / Rehydration Pack)

> **Time Truth is UTC. Every authoritative artifact must include ISO8601 UTC stamps and a TIME_SYNC_REF. Unstamped time is invalid.**

---

### Immediate Next Action

Adopt this as **WSM-01** and start using the `TIME_SYNC / ACK_SYNC` ritual on the next dispatch. The first week will surface drift sources (phones on manual time, OS timezone confusion, etc.) quickly.
