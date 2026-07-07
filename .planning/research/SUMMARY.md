# Project Research Summary

**Project:** lucy-ng v9.3 — CASE Web-View Stage 2
**Domain:** FastAPI webview extension — rendered NMR spectra, data tables, formatted log
**Researched:** 2026-07-07
**Confidence:** HIGH

---

## Executive Summary

v9.3 adds four self-contained panels to the existing v9.2 CASE run monitor: a markdown-formatted log, peak/correlation data tables, 1D ¹³C stick spectra, and 2D HSQC/HMBC/COSY scatter plots. The key architectural insight — verified against a real CASE1 (ibuprofen) run — is that **all spectra are rendered from the curated peak/correlation JSON files already written to `analysis/peaks/`**, not from raw Bruker FID traces. This means no new path-wiring, no nmrglue in the webview, and no `.run_manifest.json` or `--bruker-dir` machinery. The "dumb server reads `analysis/` files only" boundary from v9.2 is fully preserved.

The single new package dependency is `matplotlib>=3.7` (added to the `[webview]` extra). It must be used exclusively via the OO API (`Figure` + `FigureCanvasAgg`, never `pyplot`) with figures closed in `try/finally`, lazy-imported inside `make_router()` per the WV-08 pattern. Every spectra plot requires reversed ppm axes (NMR convention: high ppm left/top) via a shared `_apply_nmr_axes()` helper — this is a silent correctness bug if missed. The markdown log uses a ~50-line hand-rolled DOM renderer (createElement + textContent throughout, never innerHTML), satisfying both the no-CDN constraint and the v9.2 XSS discipline.

The four phases build in a strictly dependency-justified order: (A) tab framework + formatted log — pure frontend, no new backend; (B) data tables — establishes the peak-JSON router pattern against `analysis/` only; (C) 1D ¹³C stick spectra — introduces matplotlib and the Agg→PNG pipeline; (D) 2D scatter — extends the spectra router for HSQC/HMBC/COSY. Because everything is peak-JSON-based there is no Bruker-path prerequisite phase at all.

---

## Key Findings

### Recommended Stack

The stack delta for v9.3 is minimal. One package is added (`matplotlib>=3.7` to `[webview]` extra); all other dependencies (FastAPI, uvicorn, numpy, RDKit) are already declared. matplotlib is system-installed but undeclared in pyproject.toml today — it must be explicitly listed to make spectra rendering reproducible on a clean install.

**Core technologies:**

- **matplotlib `Figure` + `FigureCanvasAgg`** — server-side PNG spectra rendering. OO API is mandatory (never `pyplot`); `FigureCanvasAgg(fig)` explicitly sets the Agg canvas without touching global backend state; all figures closed in `try/finally`.
- **`fastapi.responses.Response(content=bytes, media_type="image/png")`** — PNG endpoint pattern, identical to the existing SVG structure endpoint; `StreamingResponse` is unnecessary for in-memory bytes.
- **`io.BytesIO`** — buffer for `canvas.print_png(buf)`; no temp files, no race conditions.
- **Vanilla JS tab switcher** — plain CSS show/hide + `data-tab` attributes; no framework, no CDN, ~10 lines.
- **Hand-rolled markdown→DOM renderer** — ~50 lines; covers the exact subset CASE-PROGRESS.md uses (## headings, **bold**, `code`, pipe-tables, code fences, --- hr); all text via `textContent`, zero innerHTML of server content.

**What NOT to add:** `matplotlib.pyplot` (not thread-safe in a server), `matplotlib.use('Agg')` as a global call (fragile after-import; use explicit `FigureCanvasAgg` instead), `marked.js` via CDN (violates no-CDN constraint), `marked.js` bundled (unnecessary for the markdown subset), Plotly/Bokeh/D3 (require CDN or build step), SVG format for spectra (2D scatter SVGs can exceed 1 MB; PNG at 800×500 dpi=100 is 50–150 KB), `pandas` (not needed; JSON is flat).

### Expected Features

**Must have — v9.3 core (P1):**
- Formatted run log — renders CASE-PROGRESS.md markdown structure; pure frontend change, zero new endpoints
- Tab navigation — prerequisite for all panels; pure CSS/JS
- ¹³C peak list table — answers "did peak picking work?"; reads `analysis/peaks/carbon_signals.json`
- HMBC correlation table with flag column — core CASE review artefact; reads `analysis/peaks/hmbc.json`; flag must be colour-coded (green/amber/red)
- ¹³C stick spectrum — visual signal summary with multiplicity colouring; matplotlib from `carbon_signals.json`
- HSQC scatter — C–H assignment check; reads `analysis/peaks/hsqc.json`
- HMBC scatter with flag colouring — shows which cross-peaks drove LSD; reads `analysis/peaks/hmbc.json`
- LSD constraint inventory summary — closes the solver-input loop; reads `analysis/iteration_NN/compound.lsd` header JSON block

**Should have — v9.3 follow-on (P2):**
- COSY scatter — completes the 2D connectivity picture; reads `analysis/peaks/cosy.json`; low incremental effort once HSQC/HMBC done
- DEPT sub-tab — signed bar chart (CH/CH3 positive, CH2 negative); conditional on `multiplicity_edited` flag in `hsqc.json`
- HSQC correlation table — tabular C–H assignments; defer until scatter confirmed sufficient

**Defer to v9.4+ (P3):**
- Per-iteration constraint diff — HIGH complexity multi-file diff; useful only for deep debug
- Full ¹H spectrum trace from raw Bruker FID — requires nmrglue + path wiring; scatter from HSQC proton_ppm values is sufficient
- Full 2D contour from raw Bruker data — same issue; peak scatter is sufficient
- Interactive zoom/pan — requires JS charting library; out of scope for the inspector
- SSE/WebSocket live push — design spec deferred; 3 s polling is adequate for 20–120 min runs

**Anti-features (do not add):**
- Raw COSY peak list table — scatter covers the use case; 200-row ¹H–¹H table adds clutter
- Any write path (editable peak lists, constraint editor) — monitor never mutates the run
- `marked.js` via CDN — violates no-CDN constraint
- `innerHTML = convertedMarkdown(serverContent)` — reintroduces XSS; SMILES strings in CASE-PROGRESS.md may contain `<` characters

**One open product decision to confirm in requirements:**
Peak-based stick/scatter plots (recommended: simpler, uses curated elucidation data, stays within `analysis/` boundary) vs. real processed spectrum traces from Bruker FIDs (out of scope for v9.3). Flag for explicit confirmation at requirements step.

### Architecture Approach

The v9.2 architecture is extended, never restructured. `create_app(analysis_dir)` gains two new router inclusions (`spectra.py`, `tables.py`) and one new static file route (`/webview.js`). The existing four routers are unchanged. `index.html` is split into `static/index.html` + `static/webview.js` (+ optional css) for maintainability — both files are covered by the existing `src/lucy_ng/webview/static/*` hatch artifact glob, but this must be verified with a packaging test.

**Major components:**

1. **`routers/tables.py` (NEW)** — reads `analysis/peaks/carbon_signals.json`, `analysis/peaks/hmbc.json`, `analysis/peaks/hsqc.json`, `analysis/peaks/cosy.json`, and `analysis/iteration_NN/compound.lsd` header JSON block; returns `{"state", "columns", "rows"}` response shape; all imports lazy inside `make_router()` per WV-08.
2. **`routers/spectra.py` (NEW)** — reads same peak JSON files; renders matplotlib PNG via `Figure` + `FigureCanvasAgg`; returns `Response(content=bytes, media_type="image/png")`; figures closed in `try/finally`; all matplotlib imports lazy inside `make_router()`.
3. **`static/webview.js` (NEW)** — extracted + extended JS: tab switching, markdown→DOM renderer, table rendering, spectrum `<img>` tag management; no build step, served via explicit `FileResponse` route in `app.py`.
4. **`static/index.html` (MODIFIED)** — tab layout shell; references `/webview.js`; log panel changed from `<pre>` to `<div>` for block-level markdown elements.
5. **`pyproject.toml` (MODIFIED)** — `matplotlib>=3.7` added to `[webview]` extra.

**Key pattern — shared `_apply_nmr_axes(ax, xnuc, ynuc)` helper:**
Called by every spectrum renderer to enforce NMR convention (high ppm left/top). Encodes `ax.invert_xaxis()` / `ax.invert_yaxis()` logic in one place. Skipping this is the primary silent correctness risk.

**Data sources confirmed from real CASE1 run (`analysis/peaks/`):**
`carbon_signals.json` (ppm, mult, nC, assignment, formula, dbe, solvent), `hsqc.json`, `hmbc.json`, `hmbc_correlations.json`, `cosy.json`, plus `iteration_NN/compound.lsd` containing a JSON constraint inventory block in the file header comments.

### Critical Pitfalls

1. **matplotlib pyplot thread-safety** — `import matplotlib.pyplot as plt` and any `plt.*` calls share global state across FastAPI worker threads. Use the OO API exclusively: `from matplotlib.figure import Figure; from matplotlib.backends.backend_agg import FigureCanvasAgg`. Never import `matplotlib.pyplot` in any webview module. Figures closed in `try/finally`. Add an import-safety test alongside the existing `test_main_importable_without_fastapi`.

2. **Reversed ppm axes are a silent NMR correctness bug** — matplotlib default auto-scales left→right (low ppm on left), which is scientifically wrong. All spectra renderers must call `ax.invert_xaxis()` and/or `ax.invert_yaxis()` via the shared `_apply_nmr_axes()` helper. Acceptance criterion on CASE1 ibuprofen: carbonyl at ~181 ppm must appear on the far LEFT of the ¹³C stick chart. Test: assert `ax.get_xlim()[0] > ax.get_xlim()[1]`.

3. **Markdown innerHTML reintroduces v9.2 XSS** — CASE-PROGRESS.md contains run-derived text including SMILES strings (CXSMILES can contain `<`). Any `innerHTML = convertedHtml` reintroduces injection risk. Mandatory: every text node from the server set via `textContent`, never `innerHTML`. Acceptance criterion: inject `# <img src=x onerror=alert(1)>` into mock CASE-PROGRESS.md and confirm it renders as literal text.

4. **hatch artifacts must cover all new static files** — The existing `artifacts = ["src/lucy_ng/webview/static/*"]` glob is flat (does not recurse). Adding `webview.js` is covered; adding any subdirectory requires a separate entry. After each phase that adds static files, verify with a packaging test. Symptom of failure: 404 in production that does not reproduce in development.

5. **matplotlib not in `[webview]` extra yet** — system-installed but undeclared. A clean `pip install lucy-ng[webview]` will fail at the first spectra request with `ModuleNotFoundError`. Must be added at the start of Phase C.

---

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase A: Formatted Log + Tab Framework

**Rationale:** Pure frontend, no new backend. Ships first to establish the tab dock-in that all subsequent phases populate. Zero risk of breaking existing backend behaviour. Extracts `index.html` JS into `webview.js`, paying a maintainability dividend immediately.

**Delivers:** Working tabbed layout (Candidates | Log | 1D Spectra | 2D Spectra | Tables); markdown-formatted CASE-PROGRESS.md log; `webview.js` established as the frontend JS home.

**Implements:** Tab switching (vanilla JS, ~10 lines), markdown→DOM renderer (~50 lines, textContent-only), `<pre>` → `<div>` for log panel, `webview.js` served via `FileResponse` route in `app.py`.

**Avoids:** XSS via innerHTML (Pitfall 3 — textContent throughout); CDN dependency (no CDN).

### Phase B: Data Tables

**Rationale:** Data sources are entirely within `analysis/` (already accessible to the server). No new package dependencies; no matplotlib yet. Establishes the `tables.py` router and `{"state", "columns", "rows"}` response shape before the more complex spectra router.

**Delivers:** Tables tab with ¹³C peak list, HMBC correlation table (flag colour-coded), LSD constraint inventory summary.

**Implements:** `routers/tables.py` reading `analysis/peaks/carbon_signals.json`, `analysis/peaks/hmbc.json`, `analysis/iteration_NN/compound.lsd` header JSON block. New endpoints `GET /api/peaks/c13`, `GET /api/peaks/hmbc`, `GET /api/constraints`. All imports lazy inside `make_router()` (WV-08).

### Phase C: 1D ¹³C Stick Spectra

**Rationale:** Introduces matplotlib and the Agg→PNG pipeline. 1D stick chart is simpler than 2D scatter — validates the full render chain before Phase D adds 2D complexity. This is where the two most critical correctness requirements land: matplotlib OO API and reversed ppm axes.

**Delivers:** 1D Spectra tab with ¹³C stick spectrum (bars coloured by multiplicity), reversed ppm axis (high ppm left), rendered as PNG from `analysis/peaks/carbon_signals.json`.

**Implements:** `routers/spectra.py` with lazy matplotlib imports (`Figure` + `FigureCanvasAgg`, never `pyplot`); shared `_apply_nmr_axes()` helper; `try/finally` figure close; `GET /api/spectra/c13.png`; matplotlib added to `[webview]` extra; import-safety test added.

**Avoids:** matplotlib pyplot thread-safety (Pitfall 1 — OO API only); reversed ppm axes (Pitfall 2 — shared helper); matplotlib not in extra (Pitfall 5); hatch artifacts regression (Pitfall 4 — packaging test).

### Phase D: 2D HSQC/HMBC/COSY Scatter

**Rationale:** Purely additive to Phase C. Router, tab framework, and matplotlib Agg pipeline are already in place. Only new logic is 2D-specific: two-axis ppm labelling, flag colouring for HMBC, diagonal for COSY.

**Delivers:** 2D Spectra tab with HSQC scatter (F2=¹H x reversed, F1=¹³C y reversed), HMBC scatter (flag-coloured), COSY scatter (square, diagonal, both ¹H axes reversed). All PNG from `analysis/peaks/*.json`.

**Implements:** Extends `spectra.py` with `GET /api/spectra/hsqc.png`, `GET /api/spectra/hmbc.png`, `GET /api/spectra/cosy.png`; reuses `_apply_nmr_axes()` for both axes; mtime-keyed per-router PNG cache to avoid re-rendering on every 3-second poll.

**Avoids:** Axis direction on both dimensions (Pitfall 2); memory growth from un-cached 2D re-renders.

### Phase Ordering Rationale

- **A before B/C/D:** Tab framework is prerequisite for all panels; frontend-only phase ships with zero backend risk.
- **B before C:** Establishes the `analysis/` peak-JSON router pattern with simpler (no-matplotlib) logic; any router bug surfaces cheaply before the more complex spectra router is added.
- **C before D:** 1D stick validates the Agg→PNG pipeline and axis inversion before 2D (which adds two-axis complexity and caching concerns).
- **No Bruker-path prerequisite phase:** All spectra derive from `analysis/peaks/*.json` — the entire four-phase sequence touches `analysis/` only. No path-wiring step needed.

### Research Flags

**All phases use standard patterns — skip research phase for all four:**
- Phase A — tab switching and DOM-based markdown rendering are fully specified; no unknowns.
- Phase B — JSON file reading + table rendering; established FastAPI router pattern.
- Phase C — matplotlib OO API is stable and well-documented; all correctness requirements specified.
- Phase D — purely additive to Phase C; all patterns established.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified against live codebase and real CASE1 run artefacts; matplotlib version pinned from system install; reconciliation directives resolve all divergences |
| Features | HIGH | Data sources confirmed from real `analysis/peaks/` artefacts; feature scope from v9.2 design spec; anti-features clearly motivated |
| Architecture | HIGH | All patterns derived from direct inspection of existing webview code; reconciliation resolves Bruker-path divergence authoritatively |
| Pitfalls | HIGH | All four critical pitfalls grounded in codebase inspection and v9.2 post-mortem; matplotlib thread-safety and axis convention well-documented |

**Overall confidence: HIGH**

### Gaps to Address

- **Peak-based vs Bruker-FID spectra (product decision — confirm in requirements):** This summary recommends peak-based stick/scatter plots (simpler, stays within `analysis/` boundary). Confirm explicitly before Phase C begins.

- **`compound.lsd` header JSON block delimiter:** FEATURES.md and ARCHITECTURE.md describe the format differently (`=== CONSTRAINT INVENTORY ===` vs `; {` comment prefix). The `tables.py` implementation must verify the exact format against a real CASE1 `iteration_NN/compound.lsd` before writing the parser. One-minute check, not a research task.

- **DEPT sub-tab `multiplicity_edited` field:** Field described but not confirmed against real CASE1 artefact. Treat DEPT as a P2 deliverable; verify field presence before implementing.

---

## Sources

### Primary (HIGH confidence)

- Direct artefact inspection: `data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/peaks/` — confirmed `carbon_signals.json`, `hsqc.json`, `hmbc.json`, `hmbc_correlations.json`, `cosy.json` and their field schemas
- Direct code inspection: `src/lucy_ng/webview/` (app.py, routers/, static/index.html, server.py, state.py) — v9.2 architecture and WV-08 pattern confirmed
- Direct code inspection: `src/lucy_ng/readers/bruker.py` — `Spectrum1D`/`Spectrum2D` fields, ppm_scale ordering
- Direct code inspection: `pyproject.toml` — `[webview]` extra (fastapi + uvicorn only; matplotlib absent); hatch `artifacts = ["src/lucy_ng/webview/static/*"]`
- Design spec: `docs/superpowers/specs/2026-07-02-case-webview-design.md` — Stage 2 scope, "dumb server" boundary, no-CDN constraint
- Phase 91 context: `.planning/milestones/v9.2-phases/91-api-endpoints-depictions-and-static-frontend/91-CONTEXT.md` — WV-01 through WV-08 decisions locked
- Orchestrator reconciliation directives — verified real CASE1 run artefact locations and authoritative resolutions of researcher divergences

### Secondary (MEDIUM confidence)

- matplotlib official docs — `Figure` + `FigureCanvasAgg` OO API for headless server rendering; thread-safety of sync route handlers
- FastAPI docs — sync `def` route handlers dispatched to thread-pool executor; `async def` blocks event loop if sync compute inside
- IUPAC NMR display conventions — ppm axis reversal (high downfield left), DEPT sign convention, 2D F1/F2 axis assignment

---

*Research completed: 2026-07-07*
*Ready for roadmap: yes*
