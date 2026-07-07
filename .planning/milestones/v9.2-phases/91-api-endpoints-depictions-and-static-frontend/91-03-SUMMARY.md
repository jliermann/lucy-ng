---
phase: 91-api-endpoints-depictions-and-static-frontend
plan: "03"
subsystem: webview
tags: [rdkit, svg, structures, fastapi, router, depiction]
dependency_graph:
  requires: [91-01, 91-02]
  provides: [depiction.py, routers/structures.py]
  affects: [webview API, candidate-structures widget]
tech_stack:
  added: []
  patterns:
    - RDKit MolDraw2DSVG per-call render (no caching)
    - make_router factory with closure over analysis_dir
    - lazy depiction import inside make_router (WV-08)
    - ranked→unranked→waiting degradation tiers
key_files:
  created:
    - src/lucy_ng/webview/depiction.py
    - src/lucy_ng/webview/routers/structures.py
  modified: []
decisions:
  - "RDKit drawOptions attributes (addAtomIndices, addStereoAnnotation) require type: ignore[assignment] due to RDKit mypy stub limitation — same pre-existing pattern as lsd/analyzer.py L214-219"
  - "_load_all_structures returns the full uncapped list; the /structures endpoint slices to [:10] at response time so the /structure/{i}.svg endpoint always resolves against the full index space"
metrics:
  duration_s: 269
  completed_date: "2026-07-04"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 0
---

# Phase 91 Plan 03: Structures Router and RDKit Depiction Summary

**One-liner:** RDKit SVG depiction module (`render_smiles`/`placeholder_svg`) and
FastAPI `/api/structures` + `/api/structure/{i}.svg` router with ranked→unranked→waiting
graceful degradation and per-request on-demand rendering.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create depiction.py | bcbdd77 | src/lucy_ng/webview/depiction.py |
| 2 | Create structures router | fc1c24b | src/lucy_ng/webview/routers/structures.py |

## What Was Built

### Task 1: depiction.py

`render_smiles(smiles, width=300, height=300) -> str | None`

- Uses `from rdkit.Chem.Draw import rdMolDraw2D, PrepareMolForDrawing` (correct import path — Pitfall 1)
- `Chem.MolFromSmiles` returns `None` for malformed SMILES; `render_smiles` propagates `None` to caller
- Fresh `MolDraw2DSVG(width, height)` per call (Pitfall 6 — drawer is stateful)
- `addAtomIndices = False` for clean publication-style depictions (D-09)
- `addStereoAnnotation = True` for publication-quality stereo annotation
- Does NOT call `AddHs()` (repo HOSE-code invariant)

`placeholder_svg(width=300, height=300) -> str`

- Minimal self-contained SVG: grey `#f0f0f0` rect + centred `?` glyph
- No `<script>` element (T-91-07 XSS mitigation)
- No external references

### Task 2: structures router (routers/structures.py)

`make_router(analysis_dir: Path) -> APIRouter(prefix="/api")`

**GET /api/structures:**
- Tier 1: `ranking_results.json` exists → source `"ranked"`, sorted ascending by rank, capped at 10
- Tier 2: newest `iteration_NN/solutions.smi` (integer suffix sort, Pitfall 5) → source `"unranked"`, first 10
- Tier 3: no data → source `"waiting"`, structures=[], total=0
- Never 500s on missing/partial/malformed files (WV-06)

**GET /api/structure/{i}.svg:**
- FastAPI types `i` as `int` (non-integer/path-traversal rejected as 422 before handler — T-91-05)
- Resolves index against FULL (uncapped) list so `i >= 10` correctly 404s instead of mis-mapping
- Out-of-range → HTTP 404 with generic detail (T-91-06 — no length leakage)
- Malformed SMILES → placeholder SVG, HTTP 200 (D-11)
- Valid SMILES → RDKit-rendered SVG, HTTP 200, `image/svg+xml`
- `render_smiles`/`placeholder_svg` imported INSIDE `make_router()` body — RDKit stays lazy (WV-08)

## Verification

```
pytest tests/test_webview_api.py::TestStructuresEndpoint tests/test_webview_api.py::TestDepiction -v
8/8 passed
```

WV-08 confirmed: `import lucy_ng.webview.routers` does not pull in fastapi.
`tests/test_cli_webview.py::TestImportSafety` 2/2 passed.

mypy: no errors in `depiction.py` or `routers/structures.py` (pre-existing RDKit stub
errors in analyzer.py/runner.py out of scope).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing annotation] RDKit drawOptions mypy stub workaround**
- **Found during:** Task 1 mypy check
- **Issue:** `opts.addAtomIndices = False` and `opts.addStereoAnnotation = True` produce
  `error: Incompatible types in assignment (expression has type "bool", variable has type "MolDrawOptions")`
  due to RDKit's mypy stubs not exposing these attributes correctly
- **Fix:** Added `# type: ignore[assignment]` on both lines — identical pattern to pre-existing
  `lsd/analyzer.py` L214-219 in this repo
- **Files modified:** `src/lucy_ng/webview/depiction.py`
- **Commit:** bcbdd77

**2. [Rule 2 - Architecture] Full-list for SVG index resolution**
- **Found during:** Task 2 implementation review
- **Issue:** Plan action says "load the full (uncapped) structure list" for SVG endpoint.
  A naive implementation sharing the same load function with the list endpoint would apply
  the 10-cap to both, causing indices 10+ to always 404 even when valid
- **Fix:** `_load_all_structures` always returns the complete list; `get_structures` applies
  `[:_CAP]` slice at response time only; `get_structure_svg` uses the full list for bounds check
- **Files modified:** `src/lucy_ng/webview/routers/structures.py`
- **Commit:** fc1c24b (part of planned implementation)

## Known Stubs

None. Both files implement complete functionality with no placeholder data or TODO stubs.

## Threat Flags

No new threat surface beyond the plan's threat model (T-91-05 through T-91-SC).

## Self-Check: PASSED

- `src/lucy_ng/webview/depiction.py` exists: FOUND
- `src/lucy_ng/webview/routers/structures.py` exists: FOUND
- Commit bcbdd77 (Task 1): FOUND
- Commit fc1c24b (Task 2): FOUND
- `pytest TestDepiction TestStructuresEndpoint`: 8/8 passed
