# DEBRIEF: WO-UI-ZONE-AUTHORITY

**Lifecycle:** DELIVERED
**WO:** WO-UI-ZONE-AUTHORITY — Single Source of Truth for Zones + Return Type Fix + Camera Frustum Gate
**Commit:** `cbcdc35`
**Gate result:** 127/127 gate tests PASS (124 existing + 3 new UI-G6). 0 regressions (5871/5871 suite pass; 4 pre-existing failures unchanged).

---

## 0 — Scope Accuracy

WO scope matched implementation exactly. Six contract changes delivered:
1. `aidm/ui/zones.json` created as single source of truth (3 zones, flat schema).
2. Python `_ZONE_BOUNDS` replaced with JSON loader; `VALID_ZONES` derived from loaded data.
3. TypeScript `ZONES` constant replaced with `zones.json` import via Vite; color strings parsed to hex ints at load time.
4. `validate_zone_position` return type changed from `Optional[str]` to `bool`; caller updated; diagnostic info moved to `logging.debug`.
5. Zone parity gate: regex scan confirms no hardcoded zone coordinates in `table_objects.py` or `zones.ts`.
6. Camera frustum gate: pure Python projection math confirms all zone centers visible from STANDARD posture.

No scope creep. No out-of-scope files modified.

## 1 — Discovery Log

Validated before writing code:
- `_ZONE_BOUNDS` only in `table_objects.py` — confirmed.
- `ZONES` only in `zones.ts` — confirmed; `main.ts` and `drag-interaction.ts` consume via imports, not redefine.
- Vite 6.0.0 supports JSON import natively — confirmed. Added `resolveJsonModule: true` to tsconfig and `server.fs.allow: ['..']` to vite.config.ts for cross-root access.
- `validate_zone_position` has 1 production caller (`update_position`) and 5 test callers. None depend on error string content.
- Camera posture numeric params (position, lookAt) exist only in TypeScript (`camera.ts`). Python has enum only. Frustum test hardcodes values with source comments.
- `from __future__ import annotations` in `table_objects.py` makes return annotations strings at runtime; used `typing.get_type_hints()` instead of `inspect.signature` for the return type gate.

## 2 — Methodology Challenge

**Color field in zones.json.** The WO schema spec says `{name, centerX, centerZ, halfWidth, halfHeight}` but the existing TS `ZoneDef` interface includes `color: number`. Omitting color from zones.json would force the TS code to hardcode colors separately, defeating the single-source-of-truth goal. I included `color` as a hex string in zones.json and parse it in TS. The Python side ignores it (not needed for zone math). This is a defensible divergence: the WO says "and any additional fields the current `_ZONE_BOUNDS` dict contains" but color was in the TS definition, not `_ZONE_BOUNDS`.

**tsconfig `rootDir` removal.** Importing `../../aidm/ui/zones.json` from `client/src/` goes outside the original `rootDir: ./src`. Removed `rootDir` from tsconfig to allow the cross-root JSON import. This is necessary for the single-source architecture. `outDir` still controls output location.

## 3 — Process / Field Notes

All hard stop conditions checked negative: zones.json expresses current definitions, Vite handles JSON natively, return type change has no external callers.

## 4 — Builder Radar

**Future risk:** The `server.fs.allow: ['..']` in vite.config.ts opens the parent directory to Vite's dev server. This is necessary for the cross-root zones.json import but widens the file access surface. If the project adds sensitive files at the repo root, this could be a concern. For production builds this is irrelevant (Vite bundles at build time).

## 5 — Focus Questions

**Hidden dependency:** The `from __future__ import annotations` PEP 563 behavior was the biggest hidden dependency. The signature gate test needed `typing.get_type_hints()` instead of `inspect.signature().return_annotation` because annotations are stored as strings, not resolved types. Easy fix once identified, but would have caused a test failure if not caught.

**Spec divergence:** The WO specified the zone schema as flat JSON without mentioning `color`, but the existing TypeScript `ZoneDef` interface requires it for rendering. The WO's "additional fields" clause covered this implicitly, but a more explicit schema spec would have prevented the decision moment.
