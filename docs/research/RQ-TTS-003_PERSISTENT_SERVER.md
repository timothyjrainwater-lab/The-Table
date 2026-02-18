# RQ-TTS-003: Persistent Server Architecture

**Sprint:** WO-TTS-COLD-START-RESEARCH
**Date:** 2026-02-14
**Dependencies:** RQ-TTS-001 (timing data), RQ-TTS-002 (VRAM data)

---

## Recommendation

**Build a `speak_server.py` daemon that wraps `ChatterboxTTSAdapter`, loads the model once, and accepts synthesis requests over HTTP on localhost.** This eliminates 15 seconds of cold start per call (81% of total latency) with minimal architectural complexity.

---

## Architecture Design

### Core Design

```
                          +--------------------------+
  speak.py (client)  ---->| speak_server.py          |
  BS buddy           ---->|   HTTP on localhost:9452  |
  combat narration   ---->|   ChatterboxTTSAdapter   |
  idle signals       ---->|   (model loaded once)    |
                          +--------------------------+
                                      |
                               GPU / VRAM
                         (Original: 3,059 MB resident)
```

### Server: `scripts/speak_server.py`

```python
# Pseudocode — design spec, not implementation
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

adapter = ChatterboxTTSAdapter(voices_dir="models/voices")
# Model loads on first synthesize() — stays resident after

class TTSHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        text = body["text"]
        persona = body.get("persona", "dm_narrator")
        reference = body.get("reference")
        exaggeration = body.get("exaggeration")

        wav_bytes = adapter.synthesize(text, persona=..., force_turbo=body.get("turbo", False))

        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.end_headers()
        self.wfile.write(wav_bytes)

    def do_GET(self):
        # /health endpoint for client detection
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "vram_mb": torch.cuda.memory_allocated() / 1024**2,
            "loaded_tiers": [...],
        }).encode())

server = HTTPServer(("127.0.0.1", 9452), TTSHandler)
server.serve_forever()
```

### Client Changes to `speak.py`

```python
def _speak_via_server(text, persona, reference=None, exaggeration=None):
    """Try the persistent server first; fall back to cold load."""
    try:
        resp = urllib.request.urlopen(
            urllib.request.Request(
                "http://127.0.0.1:9452/synthesize",
                data=json.dumps({"text": text, "persona": persona, ...}).encode(),
                headers={"Content-Type": "application/json"},
            ),
            timeout=120,  # Long timeout for synthesis
        )
        return resp.read()
    except (ConnectionRefusedError, urllib.error.URLError):
        # Server not running — fall back to current behavior
        return None
```

The client flow becomes:
1. Try `_speak_via_server()` — if server is up, get WAV bytes in ~3.5s (inference only)
2. If server is down (connection refused), fall back to `_speak_chatterbox()` — full cold start (~18.6s)
3. No behavior change for the caller — same CLI interface, same WAV output

---

## Transport Comparison

| Transport | Latency Overhead | Complexity | Cross-Platform | Port Conflicts | Debugging |
|-----------|-----------------|------------|---------------|----------------|-----------|
| **HTTP/REST (recommended)** | ~1-5ms | Low | Yes | Manageable | Easy (curl) |
| TCP socket | ~0.5-2ms | Medium | Yes | Same | Medium |
| Named pipe (Windows) | ~0.1-1ms | High | No (Windows-specific) | None | Hard |
| Shared memory | ~0.01ms | Very High | No | None | Very Hard |

**HTTP/REST is recommended** because:
- The latency overhead (1-5ms) is negligible vs. inference time (1,475-3,511ms)
- No external dependencies needed — Python's `http.server` and `urllib` are built-in
- Testable via `curl` for debugging
- The project already uses FastAPI/Starlette patterns (`aidm/server/app.py`)
- Port 9452 is arbitrary; server can detect conflicts and retry

---

## Lifecycle Management

### Who starts the server?

| Strategy | Pros | Cons |
|----------|------|------|
| **Operator manual start (recommended)** | Simple, explicit, operator controls VRAM | Requires remembering to start it |
| Agent auto-start on first speak | Seamless, no operator action | First call still has cold start; agent spawns daemon |
| System service (Windows) | Always available | Wastes VRAM when not needed |

**Recommended: Operator manual start** with agent auto-start as fallback.

```bash
# Operator starts at session beginning:
python scripts/speak_server.py &

# Or agent detects missing server and starts it:
# speak.py --ensure-server (starts server if not running, then sends request)
```

### Auto-shutdown after idle timeout

The server should shut down after N minutes of inactivity to free VRAM:
- Default idle timeout: 30 minutes
- On timeout: `del adapter` + `torch.cuda.empty_cache()` + exit
- Configurable via `--idle-timeout` flag
- Health endpoint reports idle time

### Crash recovery

- If server crashes during synthesis: client gets connection error, falls back to cold load
- Server should catch exceptions in synthesis, return HTTP 500, and stay alive
- Only crash if Python itself segfaults (rare with torch) — at which point cold restart is the only option

---

## Design Considerations

### Thread safety

`ChatterboxTTSAdapter` is not designed for concurrent synthesis. The server should:
- Use a single-threaded HTTP server (no `ThreadingHTTPServer`)
- Queue requests sequentially — synthesis is GPU-bound anyway, concurrent requests would OOM
- Return 503 if a synthesis is already in progress (or queue and wait)

### VRAM management

- Default: Load Original tier only (3,059 MB)
- Combat mode: Load Turbo on demand via `/load-turbo` endpoint
- Unload tiers: `/unload-turbo`, `/unload-original` endpoints
- Health: `/health` reports VRAM usage, loaded tiers, idle time

### Security

- Bind to `127.0.0.1` only (no external access)
- No authentication needed (localhost only)
- Validate text input length (prevent OOM from very long text)

---

## Performance Impact (Measured)

| Scenario | Without Server | With Server | Improvement |
|----------|---------------|-------------|-------------|
| Single call (Original) | 18,621 ms | 3,511 ms | **5.3x faster** |
| Single call (Turbo) | 17,287 ms* | 1,475 ms | **11.7x faster** |
| 5 sequential calls (Original) | 93,105 ms | 17,555 ms | **5.3x faster** |
| 5 sequential calls (Turbo) | 86,435 ms* | 7,375 ms | **11.7x faster** |

*Turbo cold start includes ~1,700ms for torch import on first call only; subsequent calls pay full cold start.

---

## Interaction with WO-TTS-CHUNKING

The persistent server **does not change** the chunking strategy. Text-level chunking (split at sentence boundaries) is still valuable because:
- Chatterbox quality degrades on very long inputs (>55 words)
- Chunking allows overlap between synthesis and playback within a server process
- The adapter already handles chunking internally — the server just wraps the adapter

**No scope change needed for WO-TTS-CHUNKING-001.**

---

## Prototype Status

The design above is straightforward and can be prototyped in a single session. The `ChatterboxTTSAdapter` already has the right API surface — the server is essentially:

```python
adapter = ChatterboxTTSAdapter()
while True:
    request = receive_http()
    wav = adapter.synthesize(request.text, persona=request.persona)
    send_http(wav)
```

**Prototype deferred** per WO dispatch rule: "No production code changes. Prototypes go in `scripts/` or `docs/research/`."

---

*Key question answered: The simplest architecture that eliminates cold start is an HTTP server on localhost wrapping the existing adapter. No new abstractions needed — just a process boundary change.*
