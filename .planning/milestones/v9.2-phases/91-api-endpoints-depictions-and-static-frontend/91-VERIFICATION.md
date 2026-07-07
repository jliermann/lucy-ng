---
phase: 91-api-endpoints-depictions-and-static-frontend
verified: 2026-07-04T00:00:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
---

# Phase 91: API Endpoints, Depictions, and Static Frontend — Verification Report

**Phase Goal:** Opening the dashboard URL in a browser shows three auto-refreshing widgets — run status, top candidate structures with RDKit SVG depictions, and the scrollable run log — with graceful degradation during live runs when source files are absent or partial.
**Verified:** 2026-07-04
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC-1 | `GET /api/status` returns iteration, active phase, elapsed time from timing.json/timing.jsonl/CASE-PROGRESS.md | VERIFIED | `routers/status.py` 3-tier degradation; `TestStatusEndpoint` 3/3 passing (waiting/live/complete) |
| SC-2 | `GET /api/log` returns raw CASE-PROGRESS.md content as JSON payload | VERIFIED | `routers/log.py` reads raw text; `TestLogEndpoint` 2/2 passing |
| SC-3 | `GET /api/structures` returns ranked list with SMILES/MAE/rank; `/api/structure/{i}.svg` returns non-empty RDKit SVG | VERIFIED | `routers/structures.py` + `depiction.py`; `TestStructuresEndpoint` 5/5 passing, `TestDepiction` 3/3 passing |
| SC-4 | All three API endpoints return HTTP 200 waiting payload on missing/empty/mid-write files; out-of-range SVG index returns 404 | VERIFIED | All file reads wrapped in try/except; `test_waiting_when_empty`, `test_log_waiting_when_empty`, `test_out_of_range_svg_returns_404` passing |
| SC-5 | Malformed SMILES renders as placeholder SVG; all other entries render correctly | VERIFIED | `render_smiles` returns None on malformed; `structures.py` falls back to `placeholder_svg()`; `test_malformed_smiles_returns_placeholder_svg` + `test_valid_smiles_returns_real_svg` passing |
| SC-6 | Opening `http://localhost:<port>/` shows three auto-refreshing widgets every ~3 s, no JS build step | VERIFIED | `index.html` has `setInterval(tick, 3000)`, polls `/api/status`, `/api/structures`, `/api/log`, no CDN refs, no `innerHTML`; `TestFrontend` + `TestWiring` pass; human approved 2026-07-04 (browser visual + ~3 s refresh confirmed) |

**Score:** 6/6 truths verified

---

### Required Artifacts

| Artifact | Status | Evidence |
|----------|--------|----------|
| `src/lucy_ng/webview/routers/__init__.py` | VERIFIED | Exists, empty — imports `lucy_ng.webview.routers` loads zero fastapi |
| `src/lucy_ng/webview/routers/status.py` | VERIFIED | 214 lines; exports `make_router`; 3-tier timing.json/timing.jsonl/CASE-PROGRESS.md degradation; epoch cast via `int()` |
| `src/lucy_ng/webview/routers/log.py` | VERIFIED | 62 lines; exports `make_router`; raw passthrough, FileNotFoundError/OSError → waiting |
| `src/lucy_ng/webview/routers/structures.py` | VERIFIED | 187 lines; exports `make_router`; ranked→unranked→waiting tiers; depiction imported inside `make_router()` |
| `src/lucy_ng/webview/depiction.py` | VERIFIED | 80 lines; `render_smiles` returns None for malformed; `placeholder_svg` has no `<script>`; uses `from rdkit.Chem.Draw import rdMolDraw2D, PrepareMolForDrawing` (correct import path); fresh drawer per call |
| `src/lucy_ng/webview/app.py` | VERIFIED | `create_app` docks 3 routers via lazy imports + `include_router`; serves `GET /` via `FileResponse`; all router/FileResponse imports inside function body |
| `src/lucy_ng/webview/static/index.html` | VERIFIED | 426 lines; inline CSS + JS; `setInterval(tick, 3000)`; all 3 API endpoints polled; `textContent` used (no `innerHTML`); no external CDN |
| `pyproject.toml` | VERIFIED | `artifacts = ["src/lucy_ng/data/schemas/*", "src/lucy_ng/lsd/filters/*", "src/lucy_ng/webview/static/*"]`; `TestPackaging` passing |

---

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `app.py create_app()` | `routers/{status,structures,log}` | lazy `from lucy_ng.webview.routers import … as _x` + `app.include_router(…)` inside function body | WIRED — 3 `include_router` calls confirmed; `TestWiring` passing |
| `routers/structures.py make_router()` | `depiction.render_smiles, placeholder_svg` | `from lucy_ng.webview.depiction import …` inside `make_router()` body | WIRED — grep confirms inside-function import; `TestStructuresEndpoint` SVG tests passing |
| `index.html` | `/api/status`, `/api/structures`, `/api/log`, `/api/structure/{i}.svg` | `fetch(STATUS_URL/…)` in `setInterval(tick, 3000)` | WIRED — all four API paths present in index.html; `TestFrontend` + `TestWiring` passing |
| `pyproject.toml` | wheel build | `[tool.hatch.build.targets.wheel].artifacts` | WIRED — `"src/lucy_ng/webview/static/*"` confirmed via `tomllib`; `TestPackaging` passing |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `routers/status.py` | `timing.json`, `timing.jsonl`, `CASE-PROGRESS.md` | Filesystem read per request (no cache) | Yes — `json.loads` → real fields; fallback tiers confirmed in tests | FLOWING |
| `routers/log.py` | `CASE-PROGRESS.md` | `read_text` per request | Yes — raw file content returned | FLOWING |
| `routers/structures.py` | `ranking_results.json` / `iteration_NN/solutions.smi` | Filesystem read per request | Yes — `json.loads(ranking_results.json).solutions` or `.smi` line parse | FLOWING |
| `depiction.py` | SMILES string | Passed from caller | Yes — `Chem.MolFromSmiles` + `MolDraw2DSVG` → real SVG | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 16 webview API tests pass | `pytest tests/test_webview_api.py -v` | 16 passed, 0 failed | PASS |
| WV-08: CLI import does not load fastapi | `python -c "import lucy_ng.cli.main, sys; assert 'fastapi' not in sys.modules"` | No fastapi in sys.modules | PASS |
| WV-08: routers __init__ does not load fastapi | `python -c "import lucy_ng.webview.routers; …"` | No fastapi in sys.modules | PASS |
| pyproject.toml artifacts correct | `python -c "import tomllib,pathlib; a=…; assert 'src/lucy_ng/webview/static/*' in a"` | OK, 3 artifacts | PASS |
| placeholder_svg has no script tag | `python -c "from lucy_ng.webview.depiction import placeholder_svg; svg=placeholder_svg(); assert '<script' not in svg"` | No script tag, has rect and ? | PASS |
| index.html: no innerHTML, no CDN | `grep innerHTML / grep 'src="http'` | Both absent | PASS |

---

### Requirements Coverage

| Requirement | Phase | Description | Status | Evidence |
|-------------|-------|-------------|--------|----------|
| WV-03 | 91 | Live run status visible (iteration, phase, elapsed) | SATISFIED | `routers/status.py` 3-tier degradation; SC-1 verified |
| WV-04 | 91 | Candidate structures with RDKit SVG depictions | SATISFIED | `routers/structures.py` + `depiction.py`; SC-3 + SC-5 verified |
| WV-05 | 91 | Scrollable run log (CASE-PROGRESS.md) | SATISFIED | `routers/log.py` raw passthrough; SC-2 verified |
| WV-06 | 91 | Graceful degradation on missing/partial files | SATISFIED | All routers guard reads; 200 on empty; 404 on out-of-range SVG; SC-4 verified |

No orphaned requirements: WV-01/WV-02/WV-08 were Phase 90; WV-07 is Phase 92 (pending).

---

### WV-08 Import-Safety Invariant

The plan's cross-cutting WV-08 invariant ("fastapi absent from webview package import path") is verified at three levels:

1. `import lucy_ng.cli.main` → fastapi **not** in `sys.modules` (confirmed)
2. `import lucy_ng.webview.routers` → fastapi **not** in `sys.modules` (confirmed — `routers/__init__.py` is empty)
3. `from lucy_ng.webview.routers import structures` → RDKit not loaded at module import because `depiction` is imported inside `make_router()` body, not at module level

Note: RDKit is already a core dependency (loaded by `lucy_ng.cli.main`); its presence at CLI import time is not a WV-08 violation. The invariant concerns fastapi (the optional extra), not RDKit.

---

### Anti-Patterns Found

None. Scanned all 6 phase-modified source files and `index.html`:
- Zero TBD/FIXME/XXX/TODO markers
- `innerHTML` absent from `index.html` (XSS guard preserved)
- No external `<script src="http…">` or `<link href="http…">` (no CDN dependency)
- No stub patterns (`return null`, `return {}`, empty handlers)
- `placeholder_svg` contains no `<script>` element (T-91-07 mitigation confirmed)

---

### Human Verification

SC-6 (browser visual rendering + ~3 s auto-refresh) was approved by the user on 2026-07-04 at the `checkpoint:human-verify` gate in plan 91-04, task 4. The approval confirmed:
- Status bar, structure grid, and scrollable log panels all visible
- All three widgets refresh on the ~3 s cadence
- No JavaScript build step required

No outstanding human verification items remain.

---

## Gaps Summary

None. All 6 ROADMAP success criteria verified. All 8 required artifacts confirmed substantive and wired. All 16 automated tests pass. WV-08 import-safety invariant holds. Human verification completed 2026-07-04.

---

_Verified: 2026-07-04_
_Verifier: Claude (gsd-verifier)_
