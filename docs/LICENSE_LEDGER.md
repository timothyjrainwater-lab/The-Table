# License Ledger

**Document ID:** LICENSE_LEDGER
**Version:** 1.0
**Date:** 2026-02-22
**Status:** COMPLETE
**Authority:** PRS-01 §P4 License Compliance Requirement

This ledger documents all dependencies (Python + Node) with their license information.
All fields are required per PRS-01 §P4.

## Schema

| Field | Description |
|-------|-------------|
| `dependency` | Package name |
| `version` | Pinned version |
| `license` | SPDX identifier (e.g., MIT, Apache-2.0) |
| `source_url` | PyPI/npm/GitHub URL |
| `redistribution` | `bundled` / `runtime-dep` / `dev-only` |
| `where_used` | Module or subsystem that imports it |

## Dependencies

| dependency | version | license | source_url | redistribution | where_used |
|------------|---------|---------|------------|----------------|------------|
| pytest | 7.0.0 | MIT | https://pypi.org/project/pytest | dev-only | Test suite (tests/) |
| psutil | 5.9.0 | BSD-3-Clause | https://pypi.org/project/psutil | runtime-dep | Hardware detection (system profiling) |
| pyyaml | 6.0 | MIT | https://pypi.org/project/PyYAML | runtime-dep | Model registry parsing (models.yaml) |
| msgpack | 1.0.0 | Apache-2.0 | https://pypi.org/project/msgpack | runtime-dep | IPC serialization (M1 layer) |
| opencv-python-headless | 4.8.0 | Apache-2.0 | https://pypi.org/project/opencv-python-headless | runtime-dep | Image heuristics (M3 Layer 1) |
| Pillow | 10.0.0 | HPND | https://pypi.org/project/Pillow | runtime-dep | Image loading (M3 Layer 1) |
| numpy | 1.24.0 | BSD-3-Clause | https://pypi.org/project/numpy | runtime-dep | Array operations (M3 Layer 1) |
| starlette | 0.27.0 | BSD-3-Clause | https://pypi.org/project/starlette | runtime-dep | WebSocket bridge server (optional) |
| uvicorn | 0.23.0 | BSD-3-Clause | https://pypi.org/project/uvicorn | runtime-dep | ASGI server for bridge (optional) |
| three | 0.170.0 | MIT | https://www.npmjs.com/package/three | runtime-dep | 3D rendering engine (client UI) |
| @types/three | 0.170.0 | MIT | https://www.npmjs.com/package/@types/three | dev-only | TypeScript definitions for Three.js |
| typescript | 5.7.0 | Apache-2.0 | https://www.npmjs.com/package/typescript | dev-only | TypeScript compiler (client build) |
| vite | 6.0.0 | MIT | https://www.npmjs.com/package/vite | dev-only | Frontend build tool (client) |

---

**License Compatibility Notes:**

All dependencies use permissive licenses (MIT, Apache-2.0, BSD-3-Clause, HPND) that are compatible with common open-source licenses. No GPL dependencies present.

**Redistribution Categories:**
- **runtime-dep**: Required at runtime, users must install these dependencies
- **dev-only**: Only required for development/build, not distributed to end users
