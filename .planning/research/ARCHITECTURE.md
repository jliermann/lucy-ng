# Architecture Research — v9.3 CASE Web-View Stage 2

**Domain:** FastAPI webview extension — rendered spectra, data tables, formatted log
**Researched:** 2026-07-07
**Confidence:** HIGH — all claims derived from direct inspection of the live codebase

---

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│  Browser (vanilla JS, no build step)                              │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ Tab bar: Candidates | Log | 1D Spectra | 2D Spectra | Tables │
│  │ static/index.html  (HTML + CSS)                          │    │
│  │ static/webview.js  (NEW — extracted + extended JS)       │    │
│  └──────────────────────────────────────────────────────────┘    │
│         3 s polling │ JSON / PNG responses                        │
├──────────────────────────────────────────────────────────────────┤
│  FastAPI app  (create_app(analysis_dir) — app.py)                 │
│  ┌────────┐ ┌──────┐ ┌────────────┐ ┌───────────┐ ┌──────────┐  │
│  │status  │ │log   │ │structures  │ │spectra.py │ │tables.py │  │
│  │.py     │ │.py   │ │.py         │ │(NEW)      │ │(NEW)     │  │
│  └────────┘ └──────┘ └────────────┘ └───────────┘ └──────────┘  │
│  unchanged            unchanged     lazy imports inside           │
│                                     make_router() — WV-08         │
├──────────────────────────────────────────────────────────────────┤
│  Data sources (read-only — server never writes or invokes CLI)    │
│  ┌────────────────────────────┐  ┌──────────────────────────┐    │
│  │ analysis/                  │  │ Bruker experiment dirs   │    │
│  │  timing.json / .jsonl      │  │  <bruker_root>/<N>/      │    │
│  │  CASE-PROGRESS.md          │  │  pdata/1/  (raw NMR)     │    │
│  │  ranking_results.json      │  │                          │    │
│  │  iteration_NN/compound.lsd │  │  Path discovered from:   │    │
│  │  peaks_13c.json            │  │  analysis/.run_manifest  │    │
│  │  peaks_1h.json             │  │  .json (written once by  │    │
│  │  .run_manifest.json (NEW)  │  │  case.md at run_start)   │    │
│  └────────────────────────────┘  └──────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

## New vs Modified Components

| Component | Status | Change |
|-----------|--------|--------|
| `webview/app.py` | MODIFIED | Include two new routers; add `/webview.js` static route |
| `webview/routers/spectra.py` | NEW | `GET /api/spectra`, `GET /api/spectrum/{kind}.png` |
| `webview/routers/tables.py` | NEW | `GET /api/tables`, `GET /api/tables/{name}` |
| `webview/routers/log.py` | UNCHANGED | Raw markdown passthrough stays as-is |
| `webview/routers/status.py` | UNCHANGED | |
| `webview/routers/structures.py` | UNCHANGED | |
| `webview/static/index.html` | MODIFIED | Tab layout, reference `/webview.js`; markdown via client-side renderer |
| `webview/static/webview.js` | NEW | Extracted + extended JS (tab switching, spectrum/table rendering) |
| `pyproject.toml` | MODIFIED | Add `matplotlib>=3.7` to `[webview]` extra |
| `case.md` | MODIFIED | Write `analysis/.run_manifest.json` at `run_start` (one line added) |

---

## Recommended Project Structure

```
src/lucy_ng/webview/
├── app.py                      # MODIFIED: +spectra/tables routers, +/webview.js route
├── server.py                   # unchanged
├── state.py                    # unchanged
├── depiction.py                # unchanged
├── routers/
│   ├── __init__.py             # unchanged
│   ├── status.py               # unchanged
│   ├── log.py                  # unchanged (raw markdown passthrough)
│   ├── structures.py           # unchanged
│   ├── spectra.py              # NEW
│   └── tables.py               # NEW
└── static/
    ├── index.html              # MODIFIED: tab layout, references /webview.js
    └── webview.js              # NEW: extracted + extended JS
```

---

## Architectural Patterns

### Pattern 1: Lazy-import make_router factory (WV-08 — preserved exactly)

Every new router follows the same pattern as the existing ones: FastAPI imported at module level (permitted — only ever reached from inside `create_app()`), all heavy libraries (matplotlib, BrukerReader) imported INSIDE `make_router()` body.

```python
# routers/spectra.py — module-level: fastapi only (WV-08 compliant)
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

def make_router(analysis_dir: Path) -> APIRouter:
    # Lazy heavy imports — only reached via create_app() (WV-08)
    import matplotlib                               # noqa: PLC0415
    matplotlib.use("Agg")                           # non-interactive backend
    import matplotlib.pyplot as plt                 # noqa: PLC0415
    from lucy_ng.readers.bruker import BrukerReader # noqa: PLC0415

    router = APIRouter(prefix="/api")

    @router.get("/spectra")
    def get_spectra() -> dict: ...

    @router.get("/spectrum/{kind}.png")
    def get_spectrum(kind: str) -> Response: ...

    return router
```

The same pattern applies to `tables.py`: all non-fastapi imports inside `make_router()`.

### Pattern 2: Manifest file for cross-boundary path discovery

The webview server "knows" only `analysis_dir`. Rendering spectra requires the Bruker experiment root — a path the server cannot infer reliably (the `analysis_dir.parent` heuristic would break for any run where analysis/ is not a direct child of the compound root).

The solution is a manifest file written once by the orchestrator at run start, read by the server on each spectra request:

```
analysis/.run_manifest.json
{"bruker_data_dir": "/abs/path/to/compound", "formula": "C13H18O2"}
```

The `spectra.py` router reads this file inside each route handler. If absent (pre-v9.3 run, or manual `lucy webview serve` without a case.md launch), `GET /api/spectra` returns `{"available": [], "bruker_dir": null}` and `GET /api/spectrum/{kind}.png` returns HTTP 404. No 500, no crash.

This preserves the "dumb server reads files only" boundary: the server reads a file; neither an environment variable nor a constructor argument changes.

**case.md change (one line in the timing step).** The `run_start` block already does `mkdir -p <compound_path>/analysis`. Add immediately after:

```bash
printf '{"bruker_data_dir":"%s","formula":"%s"}\n' \
  "$(cd "<compound_path>" && pwd)" "<formula>" \
  > <compound_path>/analysis/.run_manifest.json
```

`$(cd ... && pwd)` gives the absolute path robustly (handles symlinks). No CLI signature change. No `WebviewState` model change.

### Pattern 3: Render-on-demand PNG (matplotlib Agg)

Plots are rendered per-request, not pre-rendered to disk. This keeps the server stateless and avoids adding a pre-render step to case.md.

Rationale:
- 1D spectra render in ~20–80 ms — negligible for a local dashboard
- 2D contour plots render in ~150–400 ms — acceptable for human interaction rates (tabs clicked manually, not polled every 3 s)
- Bruker data is immutable once acquired; the rendered image is deterministic per request

Figure lifecycle — `try/finally` is mandatory to prevent matplotlib memory leaks:

```python
import io

fig, ax = plt.subplots(figsize=(10, 3))
try:
    ax.plot(spectrum.ppm_scale[::-1], spectrum.data, lw=0.7, color="#2c5f8a")
    ax.invert_xaxis()
    ax.set_xlabel("Chemical shift (ppm)")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    buf.seek(0)
    return Response(buf.read(), media_type="image/png")
finally:
    plt.close(fig)   # ALWAYS close — even if an exception is raised above
```

A raised exception before `plt.close(fig)` leaks a figure. With many requests this accumulates silently. `try/finally` eliminates the risk.

### Pattern 4: Client-side markdown rendering (log tab)

The v9.2 log endpoint (`D-13`) returns raw markdown and the frontend uses `textContent`. Stage 2 reverses D-13 by rendering markdown in the browser — no server change required, no new Python dependency added.

The `/api/log` endpoint is unchanged. The frontend receives `{"state": "ok", "content": "<raw markdown>"}` and passes `content` through a JS markdown parser before setting `innerHTML` on the log panel.

Recommended: bundle **marked.js** (MIT, ~5 KB minified+gzipped) as a vendored copy inside `webview.js` — avoids CDN dependency for a tool that runs locally. The content of CASE-PROGRESS.md is written entirely by the orchestrator (trusted, run-controlled), so `innerHTML` is acceptable.

### Pattern 5: Tab UI without a build step

The current `index.html` is 428 lines. With tabs, markdown rendering, spectra, and table logic it would grow to ~900–1200 lines. Extract JS to `webview.js` for maintainability — both files ship via the existing `artifacts = ["src/lucy_ng/webview/static/*"]` directive with no pyproject.toml change.

To serve `webview.js`, add one explicit route in `create_app()`:

```python
_webview_js = Path(__file__).parent / "static" / "webview.js"

@app.get("/webview.js")
def webview_js_file() -> FileResponse:
    return FileResponse(str(_webview_js), media_type="application/javascript")
```

Then `index.html` references it as `<script src="/webview.js"></script>`.

Do NOT use `StaticFiles` mount. An explicit route keeps the app structure transparent and avoids an ASGI sub-mount.

Tab switching is pure CSS toggling — no JS framework needed:

```javascript
function showTab(name) {
  document.querySelectorAll('.tab-panel').forEach(function(p) {
    p.style.display = (p.dataset.tab === name) ? '' : 'none';
  });
  document.querySelectorAll('.tab-btn').forEach(function(b) {
    b.classList.toggle('active', b.dataset.tab === name);
  });
}
```

---

## New Endpoint Specification

All new endpoints use the same `prefix="/api"` convention. New routers use separate `APIRouter(prefix="/api")` instances; `app.include_router()` merges them without collision.

### spectra.py router

```
GET /api/spectra
    → {"available": ["13c", "1h", "dept", "hsqc", "hmbc", "cosy"], "bruker_dir": "<abs>"}
    → {"available": [], "bruker_dir": null}    (manifest absent — graceful)

GET /api/spectrum/{kind}.png
    kind ∈ {"13c", "1h", "dept", "hsqc", "hmbc", "cosy"}
    → 200 image/png      (rendered matplotlib plot)
    → 404                (manifest absent, experiment not found, or unknown kind)
```

`GET /api/spectra` logic:
1. Read `analysis/.run_manifest.json` for `bruker_data_dir`
2. Scan numbered subdirs of `bruker_data_dir` for `acqus` files
3. Use NUC1 + PULPROG parameter extraction (same logic as `BrukerReader._detect_experiment_type`) to identify experiment types
4. Return available kinds

Kind mapping — 1D experiments detected by NUC1, 2D by PULPROG keywords:
- `"13c"` — 1D, NUC1=13C, PULPROG not containing "dept"
- `"1h"` — 1D, NUC1=1H
- `"dept"` — 1D, NUC1=13C, PULPROG containing "dept"
- `"hsqc"` — 2D, HSQC (as per existing `_detect_experiment_type`)
- `"hmbc"` — 2D, HMBC
- `"cosy"` — 2D, COSY

`GET /api/spectrum/{kind}.png` logic:
1. Find experiment directory for `kind` (same scan)
2. Call `BrukerReader.read_1d(exp_dir)` for 1D kinds, `BrukerReader.read_2d(exp_dir)` for 2D
3. Render with matplotlib Agg inside `try/finally plt.close(fig)`
4. Return PNG bytes

### tables.py router

```
GET /api/tables
    → {"available": ["peaks_13c", "peaks_1h", "constraints", "hmbc_usage"]}

GET /api/tables/{name}
    name ∈ {"peaks_13c", "peaks_1h", "constraints", "hmbc_usage"}
    → {"state": "ok",      "columns": [...], "rows": [...]}
    → {"state": "waiting", "columns": [],    "rows": []}
```

Data source per name:

| Name | File | Format |
|------|------|--------|
| `peaks_13c` | `analysis/peaks_13c.json` | Lucy JSON from `lucy pick 13c --format json` |
| `peaks_1h` | `analysis/peaks_1h.json` | Lucy JSON from `lucy pick 1h --format json` |
| `constraints` | Newest `analysis/iteration_NN/compound.lsd` | JSON block in LSD header |
| `hmbc_usage` | `analysis/CASE-PROGRESS.md` | Parsed HMBC table from Setup section |

`GET /api/tables` scans for which source files exist and returns only available names.

The `peaks_13c.json` and `peaks_1h.json` files require a small addition to the nmr-chemist workflow: redirect `lucy pick` JSON output to these files during peak-picking setup. This is a one-line `--format json` redirect per experiment in the nmr-chemist agent prompt; no Python code change.

---

## Data Flow

### Spectra request

```
Browser: GET /api/spectrum/hsqc.png
    ↓
spectra.py get_spectrum(kind="hsqc")
    ↓
read analysis/.run_manifest.json → bruker_data_dir
    ↓
scan bruker_data_dir/*/acqus → find HSQC experiment dir
    ↓
BrukerReader.read_2d(exp_dir) → Spectrum2D(f1_ppm_scale, f2_ppm_scale, data)
    ↓
matplotlib Agg: contour(f2_ppm, f1_ppm, data) → BytesIO → plt.close(fig)
    ↓
Response(png_bytes, media_type="image/png")
    ↓
Browser: <img src="/api/spectrum/hsqc.png"> in 2D Spectra tab
```

### Tables request

```
Browser: GET /api/tables/constraints
    ↓
tables.py get_table(name="constraints")
    ↓
find newest analysis/iteration_NN/compound.lsd
    ↓
parse LSD file: extract JSON block between constraint inventory markers
    ↓
{"state": "ok", "columns": ["type","atom1","atom2","note"], "rows": [...]}
    ↓
Browser: renders HTML <table> in Tables tab
```

### Log markdown rendering

```
Browser: GET /api/log  (3 s poll — endpoint unchanged)
    ↓
log.py → {"state": "ok", "content": "<raw markdown>"}
    ↓
webview.js: marked.parse(data.content) → HTML string
    ↓
logPanel.innerHTML = html   (replaces textContent from v9.2)
```

---

## Integration Points

### app.py changes

Add three blocks inside `create_app()`, after the existing `include_router` calls:

```python
# New routers — lazy imports (WV-08)
from lucy_ng.webview.routers import spectra as _spectra  # noqa: PLC0415
from lucy_ng.webview.routers import tables  as _tables   # noqa: PLC0415

app.include_router(_spectra.make_router(analysis_dir))
app.include_router(_tables.make_router(analysis_dir))

# Serve extracted frontend JS
_webview_js_file = Path(__file__).parent / "static" / "webview.js"

@app.get("/webview.js")
def webview_js() -> FileResponse:
    return FileResponse(str(_webview_js_file), media_type="application/javascript")
```

No other changes to `app.py`, `server.py`, or `state.py`.

### case.md change

In the `timing` step, inside the `run_start` block, after `mkdir -p <compound_path>/analysis`:

```bash
printf '{"bruker_data_dir":"%s","formula":"%s"}\n' \
  "$(cd "<compound_path>" && pwd)" "<formula>" \
  > <compound_path>/analysis/.run_manifest.json
```

One line. No other changes to case.md.

### pyproject.toml change

```toml
webview = [
    "fastapi>=0.100",
    "uvicorn>=0.20",
    "matplotlib>=3.7",     # new: spectrum rendering (Agg backend)
]
```

`nmrglue` and `numpy` are already core dependencies — present on all installs.

---

## Build Order for Phases

The four Stage-2 features form a dependency chain. Each phase docks into the frontend established by the previous one.

### Phase A: Formatted Log

**Changes:** `static/index.html` (tab skeleton, reference `/webview.js`), `static/webview.js` (new file — extracted JS + tab switching + bundled marked.js for log panel)

**Dependencies:** none — uses existing `/api/log` endpoint unchanged

**Why first:** self-contained, frontend-only. Introduces the tab framework that all subsequent phases add tabs into. Zero risk of breaking any existing backend behaviour. The JS extraction also pays a maintainability dividend immediately.

### Phase B: Data Tables

**Changes:** new `routers/tables.py`, `app.py` (include router), `webview.js` (Tables tab), nmr-chemist workflow (write `peaks_13c.json` / `peaks_1h.json` to analysis/)

**Dependencies:** `analysis/` only — no Bruker path wiring, no matplotlib, no pyproject.toml change

**Why second:** data source is entirely within `analysis_dir` (already accessible to the server). Establishes the `tables.py` router pattern and the `{"state", "columns", "rows"}` response shape before the more complex `spectra.py`. The one workflow dependency (peak JSON files) is small and testable with fixtures independently of any live CASE run.

### Phase C: 1D Spectra

**Changes:** new `routers/spectra.py`, `app.py` (include router), `webview.js` (1D Spectra tab), `pyproject.toml` (add matplotlib), `case.md` (write `.run_manifest.json`)

**Dependencies:** Bruker path via manifest (requires case.md change), matplotlib (requires pyproject.toml change), `BrukerReader.read_1d()`

**Why third:** introduces the two cross-cutting concerns that 2D spectra also need — Bruker path wiring and matplotlib Agg pipeline. Doing 1D first validates the manifest → BrukerReader → Agg → PNG chain with a simpler plot (line plot) before tackling 2D contours.

### Phase D: 2D Spectra

**Changes:** extend `routers/spectra.py` (add HSQC/HMBC/COSY kinds), `webview.js` (2D Spectra tab, sub-tabs per experiment)

**Dependencies:** all of Phase C (same router, same manifest, same matplotlib backend, `BrukerReader.read_2d()`)

**Why last:** purely additive to Phase C. Router, manifest, and tab framework are already in place. The only new logic is 2D-specific: contour level computation, two-axis ppm labelling (F1 and F2). Risk is low because the full infrastructure is proven.

```
Phase A: Formatted Log
   (frontend-only, tab framework established)
    ↓
Phase B: Data Tables
   (new router, analysis/ data only)
    ↓
Phase C: 1D Spectra
   (manifest wiring + matplotlib + BrukerReader.read_1d)
    ↓
Phase D: 2D Spectra
   (extends Phase C router, BrukerReader.read_2d)
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Pre-rendering plots to disk

**What people do:** write PNG files to `analysis/` during peak-picking (e.g. nmr-chemist runs `lucy pick 13c` then immediately saves a PNG), serve them as static files.

**Why wrong:** couples the CASE workflow to the webview presentation layer. Breaks the separation where the server reads data files (not presentation artefacts). Rendered files become stale if the rendering code is later improved.

**Do this instead:** render on demand inside the route handler. Bruker data is immutable; the ~20–400 ms per request is acceptable for a local human-interaction dashboard.

### Anti-Pattern 2: Adding bruker_data_dir to WebviewState

**What people do:** pass `--bruker-data <path>` to `lucy webview serve`, store it in `.webview.json` alongside PID/port.

**Why wrong:** conflates lifecycle state (PID/port) with data-source config. Changes the CLI signature (case.md update, docs update). Changes the Pydantic model (backward compat concern for existing `.webview.json` files). `server.py` and `state.py` must stay fastapi-free per WV-08; adding path arguments there is additional complexity.

**Do this instead:** `.run_manifest.json` in `analysis_dir`. The `spectra.py` router reads it inside its own route handlers. Lifecycle state stays in `.webview.json` unchanged.

### Anti-Pattern 3: Importing matplotlib at module level in spectra.py

**What people do:** `import matplotlib.pyplot as plt` at the top of `spectra.py`.

**Why wrong:** violates WV-08. Any code path that imports `spectra` — including test imports, type-checker runs, and the router `__init__.py` — would trigger a matplotlib import. On a base `lucy-ng` install without the `[webview]` extra, this raises `ModuleNotFoundError`.

**Do this instead:** import matplotlib INSIDE `make_router()`. Follow the exact pattern of `structures.py` which imports `lucy_ng.webview.depiction` (which loads RDKit) inside `make_router()`.

### Anti-Pattern 4: Calling CLI subprocesses from route handlers

**What people do:** `subprocess.run(["lucy", "pick", "13c", ...])` inside `GET /api/spectrum/13c.png` to regenerate spectra on every request.

**Why wrong:** violates the "dumb server reads files only" boundary, adds seconds of latency, creates a subprocess dependency, and is fragile (PATH, virtual environment, working directory).

**Do this instead:** call `BrukerReader.read_1d()` directly. It reads Bruker binary files from disk (uses nmrglue) without any subprocess. Peak picking is not needed for rendering raw spectra — the raw NMR data in `pdata/1/` is what the plot shows.

---

## Sources

- Direct code inspection: `src/lucy_ng/webview/app.py`, `routers/status.py`, `routers/log.py`, `routers/structures.py`, `webview/server.py`, `webview/state.py`
- Direct code inspection: `src/lucy_ng/readers/bruker.py` — `BrukerReader.read_1d()`, `BrukerReader.read_2d()`, `_detect_experiment_type()`
- Direct code inspection: `.claude/commands/lucy-ng/case.md` — `spawn_case_team` Step 5 (webview launch), `timing` step (`run_start` block)
- Direct code inspection: `pyproject.toml` — `[webview]` extra (fastapi, uvicorn only), hatch `artifacts = ["src/lucy_ng/webview/static/*"]`
- Direct code inspection: `static/index.html` — existing 428-line single-file frontend
- Design spec: `docs/superpowers/specs/2026-07-02-case-webview-design.md` — Stage 2 scope, "dumb server" boundary
- Project context: `.planning/PROJECT.md` — v9.3 milestone goals, v9.2 decisions WV-01..08

---

*Architecture research for: v9.3 CASE Web-View Stage 2 (rendered spectra, data tables, formatted log)*
*Researched: 2026-07-07*
