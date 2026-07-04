# Phase 91: API Endpoints, Depictions, and Static Frontend - Research

**Researched:** 2026-07-04
**Domain:** FastAPI APIRouter pattern, RDKit SVG depiction, CASE data-source schemas, static file serving, hatch packaging, FastAPI TestClient testing
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Derive iteration + active phase + elapsed time from `analysis/timing.jsonl` as the **primary** source. Active phase = last `phase_start` event with no matching `phase_end`. Iteration = parsed from phase name (`lsd-iteration-03` → 3).
- D-02: Fallback to parsing `analysis/CASE-PROGRESS.md` headers (`## Iteration N`, `### <Agent>`) when `timing.jsonl` is missing or empty.
- D-03: Elapsed time computed server-side as `now − run_start` while live; freeze to `total_duration_s` once `run_end` or finalized `timing.json` exists.
- D-04: Missing data → well-formed "waiting for data" HTTP 200 payload; never 500.
- D-05: Pre-ranking, surface candidates from newest `iteration_NN/solutions.smi` with `rank=null`, `mae=null`, `source="unranked"`.
- D-06: Once `ranking_results.json` exists, switch to ranked list.
- D-07: Cap at ~10. Ranked → top 10 by rank. Unranked → first 10 by file order. Expose total count.
- D-08: Missing/empty solutions → "waiting for data" HTTP 200.
- D-09: Clean publication-style 2D depiction, ~300×300 px, **no atom indices**. Rank/MAE shown by frontend HTML, not baked into SVG.
- D-10: Render on-demand per request; no server-side cache. Frontend re-requests SVG only when SMILES at that index changed.
- D-11: Malformed SMILES → placeholder SVG for that entry only. Out-of-range index → HTTP 404.
- D-12: `GET /api/log` returns raw `CASE-PROGRESS.md` content.
- D-13: Frontend renders log as raw monospace in `<pre>`. Auto-scroll to bottom only when user is already at bottom.
- D-14: Single `src/lucy_ng/webview/static/index.html` with inline CSS + JS. No build step. Light theme, system fonts.
- D-15: Auto-refresh every ~3 s by polling three JSON endpoints; no websockets.

### Claude's Discretion
- Exact widget arrangement (default intent: slim status bar on top, two-column below: structure grid left / scrollable log right; collapse to stacked on narrow windows).
- Placeholder-SVG visual style, exact tile grid sizing, precise "waiting for data" payload field names, and error copy.

### Deferred Ideas (OUT OF SCOPE)
- Markdown-rendered log panel.
- Dark-mode toggle / separate CSS + JS assets.
- Atom-numbered depictions for HMBC-assignment debugging.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WV-03 | User sees live run status (iteration, active phase, elapsed time) from `timing.json`/`timing.jsonl` + `CASE-PROGRESS.md`, auto-refreshed | timing.jsonl event schema verified from case.md; elapsed-time derivation pattern documented |
| WV-04 | User sees best ~10 candidate structures rendered (RDKit SVG) with MAE/rank from `ranking_results.json`/`solutions.smi` | ranking_results.json schema verified from lsd.py; RDKit SVG API verified against installed version |
| WV-05 | User sees run log (`CASE-PROGRESS.md`) in scrollable auto-refreshing panel | `CASE-PROGRESS.md` structure verified from progress-format.md |
| WV-06 | Dashboard degrades gracefully during live run; missing/partial files → "waiting" 200; malformed SMILES skipped | solutions.smi parser and graceful degradation patterns documented |
</phase_requirements>

---

## Summary

Phase 91 extends the `create_app()` factory (delivered in Phase 90) with three APIRouter modules, one depiction module, one static HTML file, and the `pyproject.toml` artifact entry to package it. The implementation is constrained to be "dumb" (file reads only) with fastapi and RDKit imports kept lazy — only loaded inside `create_app()`, never at module level in the webview package.

The dominant design challenge is **graceful degradation**: during a live CASE run, `timing.json`, `ranking_results.json`, and `final_results.md` do not yet exist — only the append-only `timing.jsonl` and per-iteration `solutions.smi` files are present. Every endpoint's primary code path must assume final-artifact files are absent and fall back gracefully. Missing/empty/partially-written files must return HTTP 200 with a "waiting for data" payload, never raise a 500.

The RDKit SVG import path is **non-obvious** (see Pitfall 1 below): `from rdkit.Chem.Draw import rdMolDraw2D` — the naive `from rdkit.Chem import rdMolDraw2D` raises `ImportError` on the installed version. This was verified against the project environment.

**Primary recommendation:** Implement each router as a `make_router(analysis_dir: Path) -> APIRouter` factory in its own module under `src/lucy_ng/webview/routers/`; import those modules inside `create_app()` only. Keep the depiction logic in `src/lucy_ng/webview/depiction.py`. Serve `index.html` via `FileResponse` at `GET /`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Live status (iteration, phase, elapsed) | Backend (`GET /api/status`) | Filesystem (`timing.jsonl`, `timing.json`) | Server reads files; elapsed computed server-side per D-03 |
| Candidate structures list | Backend (`GET /api/structures`) | Filesystem (`ranking_results.json`, `iteration_NN/solutions.smi`) | Ranked source or unranked fallback per D-05/D-06 |
| SVG depiction rendering | Backend (`GET /api/structure/{i}.svg`) | RDKit (in-process) | On-demand render per D-10; RDKit is already a core dep |
| Run log | Backend (`GET /api/log`) | Filesystem (`CASE-PROGRESS.md`) | Raw file passthrough per D-12 |
| Auto-refresh polling | Browser / Client (`index.html` vanilla JS) | — | `setInterval` every 3 s; no websockets per D-15 |
| Layout + widgets | Browser / Client (`index.html` inline CSS + JS) | — | No build step; single file per D-14 |
| Graceful degradation | Backend (all API endpoints) | — | Every endpoint must handle missing/partial/malformed files |

---

## Standard Stack

No new package dependencies are introduced in this phase. All required libraries are already present:

### Core (no new additions)
| Library | Already Present | Purpose in Phase 91 |
|---------|----------------|---------------------|
| fastapi | Yes (webview extra) | `APIRouter`, `Response`, `FileResponse` |
| rdkit | Yes (core dep, `rdkit>=2023.0`) | `MolFromSmiles`, `MolDraw2DSVG` SVG rendering |
| pathlib (stdlib) | Yes | File I/O throughout |
| json (stdlib) | Yes | Parsing `timing.jsonl`, `timing.json`, `ranking_results.json` |
| datetime (stdlib) | Yes | Elapsed-time computation (`datetime.now(tz=timezone.utc)`) |

### No New Package Legitimacy Audit Required
No external packages are added in this phase. All dependencies are already audited (Phase 90) or are stdlib/RDKit (core project dependency).

---

## Architecture Patterns

### System Architecture Diagram

```
Browser (index.html — vanilla JS, setInterval 3 s)
    │
    ├── GET /api/status  ──►  status router
    │                            ├── reads analysis_dir/timing.jsonl  (primary — live)
    │                            ├── reads analysis_dir/timing.json   (finalized — if exists)
    │                            └── reads analysis_dir/CASE-PROGRESS.md  (fallback parser)
    │
    ├── GET /api/structures  ──►  structures router
    │                                ├── reads analysis_dir/ranking_results.json  (if exists)
    │                                └── reads analysis_dir/iteration_NN/solutions.smi  (unranked fallback)
    │
    ├── GET /api/structure/{i}.svg  ──►  structures router (SVG endpoint)
    │                                        └── calls depiction.render_smiles(smiles) → SVG
    │                                              └── rdkit MolDraw2DSVG (on-demand, no cache)
    │
    ├── GET /api/log  ──►  log router
    │                          └── reads analysis_dir/CASE-PROGRESS.md  (raw passthrough)
    │
    └── GET /  ──►  app.py create_app()
                        └── FileResponse(static/index.html)
```

### Recommended Project Structure

```
src/lucy_ng/
└── webview/
    ├── __init__.py        # unchanged
    ├── app.py             # EXTEND: import routers inside create_app(); add GET /
    ├── state.py           # unchanged (Phase 90)
    ├── server.py          # unchanged (Phase 90)
    ├── depiction.py       # NEW: render_smiles(smiles) -> str (SVG); placeholder_svg() -> str
    ├── static/
    │   └── index.html     # NEW: single-file dashboard (inline CSS + JS)
    └── routers/
        ├── __init__.py    # NEW: empty
        ├── status.py      # NEW: make_router(analysis_dir) -> APIRouter; GET /api/status
        ├── structures.py  # NEW: make_router(analysis_dir) -> APIRouter; GET /api/structures + GET /api/structure/{i}.svg
        └── log.py         # NEW: make_router(analysis_dir) -> APIRouter; GET /api/log

tests/
└── test_webview_api.py    # NEW: TestClient-based tests for all Phase 91 endpoints
```

### Pattern 1: Lazy Router Registration in `create_app()`

**What:** Router modules that import fastapi or RDKit are imported inside `create_app()`, not at module level. Each router module exports a `make_router(analysis_dir: Path) -> APIRouter` factory that closes over `analysis_dir`.

**Why:** Preserves the WV-08 invariant — the webview package must stay fastapi-free except `app.py`. If router modules were imported at module level anywhere outside `app.py`, `from lucy_ng.webview import server` would pull in fastapi on core installs.

**Example (app.py extension):**
```python
# Source: verified against existing app.py + APIRouter pattern confirmed
def create_app(analysis_dir: Path) -> FastAPI:
    from pathlib import Path as _Path  # already imported at module level

    from fastapi import FastAPI
    from fastapi.responses import FileResponse

    app = FastAPI(title="lucy-ng webview", docs_url=None, redoc_url=None)
    analysis_dir = analysis_dir.resolve()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "analysis_dir": str(analysis_dir)}

    # Phase 91: lazy imports — these modules import fastapi/RDKit
    from lucy_ng.webview.routers import status as _status
    from lucy_ng.webview.routers import structures as _structures
    from lucy_ng.webview.routers import log as _log

    app.include_router(_status.make_router(analysis_dir))
    app.include_router(_structures.make_router(analysis_dir))
    app.include_router(_log.make_router(analysis_dir))

    # Serve the single-page frontend
    _static_file = _Path(__file__).parent / "static" / "index.html"

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(str(_static_file), media_type="text/html")

    return app
```

### Pattern 2: `make_router` Factory with Closure

**What:** Each router module defines a `make_router(analysis_dir: Path) -> APIRouter` that creates routes closing over `analysis_dir`. FastAPI routes defined inside the factory body have access to `analysis_dir` without dependency injection.

**Example (status.py skeleton):**
```python
# Source: FastAPI APIRouter docs + verified working in session
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter


def make_router(analysis_dir: Path) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/status")
    def get_status() -> dict:
        # analysis_dir is captured in closure — no DI needed
        return _derive_status(analysis_dir)

    return router


def _derive_status(analysis_dir: Path) -> dict:
    """Read timing.jsonl / timing.json / CASE-PROGRESS.md and return status dict."""
    ...  # see Data-Source Schemas section below
```

**Note:** The `structures.py` router also hosts `GET /api/structure/{i}.svg`. It imports `depiction.py` inside `make_router()` (not at module level in structures.py) because `depiction.py` imports RDKit.

### Pattern 3: RDKit SVG Rendering

**Correct import path** (VERIFIED — `from rdkit.Chem import rdMolDraw2D` raises ImportError):
```python
# Source: verified against project RDKit installation in this session
from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D, PrepareMolForDrawing
```

**Clean depiction function:**
```python
def render_smiles(smiles: str, width: int = 300, height: int = 300) -> str | None:
    """Render a SMILES string to an SVG string.

    Returns the SVG string on success, or None if smiles is malformed.
    Caller is responsible for returning a placeholder on None.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None  # malformed SMILES

    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    opts = drawer.drawOptions()
    opts.addAtomIndices = False          # suppress atom index labels (D-09)
    opts.addStereoAnnotation = True      # keep stereo — publication style
    PrepareMolForDrawing(mol)
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()
```

**Placeholder SVG** (for malformed SMILES or D-11 cases):
```python
def placeholder_svg(width: int = 300, height: int = 300) -> str:
    """Return a minimal placeholder SVG for a molecule that cannot be rendered."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}">'
        f'<rect width="{width}" height="{height}" fill="#f0f0f0" stroke="#ccc"/>'
        f'<text x="{width//2}" y="{height//2}" text-anchor="middle" '
        f'dominant-baseline="middle" font-size="48" fill="#999">?</text>'
        f'</svg>'
    )
```

**FastAPI SVG response:**
```python
from fastapi import APIRouter
from fastapi.responses import Response

@router.get("/api/structure/{i}.svg")
def get_structure_svg(i: int) -> Response:
    structures = _load_structures(analysis_dir)
    if i < 0 or i >= len(structures):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Structure index out of range")
    smiles = structures[i]["smiles"]
    svg = render_smiles(smiles)
    if svg is None:
        svg = placeholder_svg()
    return Response(content=svg, media_type="image/svg+xml")
```

### Pattern 4: Graceful-Degradation File Reading

**What:** Every file read is wrapped in a try/except (or explicit existence check) that returns the "waiting for data" sentinel on any failure — `FileNotFoundError`, `json.JSONDecodeError` (partial write), `OSError`.

**Example (status endpoint — primary path):**
```python
import json
from datetime import datetime, timezone

def _derive_status(analysis_dir: Path) -> dict:
    """Return status dict; always HTTP 200, never raises."""
    # 1. Try finalized timing.json (post-run)
    timing_json = analysis_dir / "timing.json"
    if timing_json.exists():
        try:
            data = json.loads(timing_json.read_text())
            # Extract completed run info
            return {
                "state": "complete",
                "run_start_utc": data.get("run_start_utc"),
                "run_end_utc": data.get("run_end_utc"),
                "total_duration_s": data.get("total_duration_s"),
                "phases": data.get("phases", []),
                "iteration": _max_iteration(data.get("phases", [])),
                "active_phase": None,
                "elapsed_s": data.get("total_duration_s"),
            }
        except (json.JSONDecodeError, OSError):
            pass  # fall through to timing.jsonl

    # 2. Try append-only timing.jsonl (live run primary source)
    timing_jsonl = analysis_dir / "timing.jsonl"
    if timing_jsonl.exists():
        try:
            lines = [l for l in timing_jsonl.read_text().splitlines() if l.strip()]
            events = []
            for line in lines:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # skip partial last line (mid-write)
            if events:
                return _status_from_events(events)
        except OSError:
            pass

    # 3. Fallback: parse CASE-PROGRESS.md headers
    progress_md = analysis_dir / "CASE-PROGRESS.md"
    if progress_md.exists():
        try:
            return _status_from_progress_md(progress_md.read_text())
        except OSError:
            pass

    # 4. No data yet
    return {"state": "waiting", "message": "Waiting for run data..."}
```

### Anti-Patterns to Avoid

- **`from rdkit.Chem import rdMolDraw2D`** — ImportError on the installed RDKit. Must be `from rdkit.Chem.Draw import rdMolDraw2D`.
- **Importing router or depiction modules at module level in any `webview/` file** — breaks WV-08. Import these inside `create_app()` only.
- **Reusing a `MolDraw2DSVG` instance across requests** — the drawer is stateful; create a new instance per `render_smiles()` call.
- **Sorting iteration folders lexicographically** — `"iteration_10" < "iteration_9"` alphabetically. Parse the numeric suffix and sort by int.
- **Treating `epoch` field in `timing.jsonl` as int** — the shell printf writes it as a string (`"epoch":"1751234567"`). Always `int(event["epoch"])` before arithmetic.
- **Serving static assets with `StaticFiles` mount** — for a single `index.html` with no sub-assets, `FileResponse` at `GET /` is simpler and correct. `StaticFiles` is for directories with many files.

---

## Data-Source Schemas

### `analysis/timing.jsonl` (live run — primary source for WV-03)

One JSON object per line, appended atomically by the case.md coordinator.

```json
{"utc":"2026-07-04T10:00:00Z","epoch":"1751630400","event":"run_start","phase":"run","agent":""}
{"utc":"2026-07-04T10:00:05Z","epoch":"1751630405","event":"phase_start","phase":"peak-picking","agent":"nmr-chemist"}
{"utc":"2026-07-04T10:02:10Z","epoch":"1751630530","event":"phase_end","phase":"peak-picking","agent":"nmr-chemist"}
{"utc":"2026-07-04T10:02:11Z","epoch":"1751630531","event":"phase_start","phase":"lsd-iteration-01","agent":"lsd-engineer"}
```

**Key derivations for D-01:**
- `run_start_utc` = first event with `event="run_start"` → `utc` field
- `run_start_epoch` = `int(first_run_start_event["epoch"])`
- `active_phase` = last event with `event="phase_start"` whose `phase` value has no matching `phase_end` event
- `iteration` = parse `phase` value: `"lsd-iteration-03"` → `3`; `"peak-picking"` → `0` (setup)
- `elapsed_s` = `int(datetime.now(tz=timezone.utc).timestamp()) - run_start_epoch`

**Important:** `epoch` is always a **string** in the JSONL (from shell `printf %s`). Cast with `int()` before arithmetic.

### `analysis/timing.json` (finalized — only after run completes)

```json
{
  "run_start_utc": "2026-07-04T10:00:00Z",
  "run_end_utc": "2026-07-04T11:30:00Z",
  "total_duration_s": 5400,
  "total_duration_hms": "01:30:00",
  "phases": [
    {"phase": "peak-picking", "agent": "nmr-chemist", "start_utc": "...", "end_utc": "...", "duration_s": 125},
    {"phase": "lsd-iteration-01", "agent": "lsd-engineer", "start_utc": "...", "end_utc": "...", "duration_s": 847}
  ]
}
```

**`total_duration_s`** may be `null` if `run_end` was never written (crash exit).

### `analysis/ranking_results.json` (finalized — written by solution-analyst)

Written by the solution-analyst agent via `lucy lsd rank --format json`. Root-level fields (all present):

```json
{
  "total_solutions": 42,
  "ranked_count": 42,
  "skipped_count": 0,
  "experimental_shifts": [180.5, 140.8, 137.0, 129.4],
  "tolerance": 5.0,
  "solutions": [
    {
      "rank": 1,
      "solution_index": 7,
      "smiles": "CC(=O)Oc1ccccc1C(=O)O",
      "mae": 1.234,
      "quality": "excellent",
      "deviations": [0.5, 1.2, 1.8, 2.1],
      "within_3ppm": 3,
      "within_5ppm": 4,
      "total_carbons": 9,
      "max_deviation": 2.1,
      "prediction_rate": 1.0,
      "matched_count": 4,
      "has_aromatic_ring": true
    }
  ],
  "warnings": []
}
```

**Fields for WV-04 API response:** use `rank`, `solution_index`, `smiles`, `mae`, `quality` per-solution. Total count from `total_solutions`.

### `analysis/iteration_NN/solutions.smi` (live run — unranked fallback for D-05)

Plain text, one SMILES per line. No header, no title column. Empty lines and lines starting with `#` or `;` are comments (per `LSDOutputParser.parse_smiles_file`). The parser uses a regex to validate each line; 0-based index i corresponds to line order.

```
CC(=O)Oc1ccccc1C(=O)O
c1ccccc1CC(=O)O
CCc1ccccc1
```

**Iteration folder discovery** (D-05 — "newest iteration"):
```python
import re

def _newest_solutions_smi(analysis_dir: Path) -> Path | None:
    """Return the solutions.smi from the highest-numbered iteration_NN folder."""
    candidates = []
    for p in analysis_dir.glob("iteration_*/solutions.smi"):
        m = re.match(r"iteration_(\d+)", p.parent.name)
        if m:
            candidates.append((int(m.group(1)), p))
    if not candidates:
        return None
    return max(candidates, key=lambda x: x[0])[1]
```

### `analysis/CASE-PROGRESS.md` (fallback for D-02 status, primary source for D-12 log)

Key structural features for the fallback status parser:
- `## Iteration N: <description>` — iteration header
- `### Coordinator` with `**Phase start (UTC):** <ISO>` — timing of iteration start
- `### LSD-Engineer`, `### Solution-Analyst`, `### Devils-Advocate` — agent sections
- `## Timing Summary` — final block (only present after run completes)

Minimal fallback parser for D-02 (iteration + active phase only, no elapsed time):
```python
import re

def _status_from_progress_md(content: str) -> dict:
    """Extract iteration number and active agent from CASE-PROGRESS.md."""
    iteration = 0
    active_phase = None

    for line in content.splitlines():
        m = re.match(r"^## Iteration (\d+)", line)
        if m:
            iteration = int(m.group(1))
        m2 = re.match(r"^### (.+)$", line)
        if m2 and m2.group(1) not in ("Coordinator",):
            active_phase = m2.group(1).lower().replace("-", "_")

    return {
        "state": "running",
        "iteration": iteration,
        "active_phase": active_phase,
        "elapsed_s": None,  # cannot compute elapsed from MD without timestamps
        "source": "progress_md_fallback",
    }
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SMILES → 2D coordinates + SVG | Custom coordinate generator | `rdkit.Chem.Draw.rdMolDraw2D.MolDraw2DSVG` | RDKit's coordinate-generation + SVG renderer handles aromatic perception, stereo, ring systems; hand-rolling is hundreds of lines |
| SMILES validity check | Regex or custom parser | `Chem.MolFromSmiles(smiles) is None` | RDKit's SMILES parser is definitive; a regex can accept invalid SMILES |
| JSON test client for FastAPI | Real HTTP socket | `fastapi.testclient.TestClient` | ASGI in-process transport; no port binding needed; already available |
| Iteration folder sorting | String sort | Parse numeric suffix → sort by `int` | `"iteration_10" < "iteration_9"` lexicographically |

---

## Common Pitfalls

### Pitfall 1: Wrong RDKit `rdMolDraw2D` Import Path (CRITICAL)
**What goes wrong:** `from rdkit.Chem import rdMolDraw2D` raises `ImportError: cannot import name 'rdMolDraw2D' from 'rdkit.Chem'` on the installed project RDKit.

**Why it happens:** `rdMolDraw2D` lives in `rdkit.Chem.Draw`, not directly in `rdkit.Chem`.

**How to avoid:** Always use `from rdkit.Chem.Draw import rdMolDraw2D, PrepareMolForDrawing`.

**Warning signs:** `ImportError` at the SVG endpoint on first request; misleading because the module exists at a different path.

**Verified:** `from rdkit.Chem.Draw import rdMolDraw2D` confirmed working in this session.

---

### Pitfall 2: Import-Safety Violation via Router Module-Level Imports
**What goes wrong:** A `src/lucy_ng/webview/routers/status.py` that has `from fastapi import APIRouter` at module level causes `ImportError` when any code does `from lucy_ng.webview import server` without the webview extra installed.

**Why it happens:** Python eagerly evaluates module-level imports. Any module in the `webview/` package that imports fastapi at module level is pulled in transitively when `webview/__init__.py` or `webview/server.py` imports it.

**How to avoid:** Router modules CAN have `from fastapi import APIRouter` at module level — they are only ever imported from inside `create_app()`. What they must NOT do is be imported from `webview/__init__.py`, `webview/server.py`, or `webview/state.py` at module level.

**The rule:** `routers/*.py` and `depiction.py` are only import-safe because they are only reached via `create_app()`. Keep `webview/__init__.py` empty (or re-exporting only state/server, which have no fastapi imports).

**Warning signs:** `test_main_importable_without_fastapi` (existing test in `test_cli_webview.py`) fails.

---

### Pitfall 3: Hatch Drops `index.html` from Wheel
**What goes wrong:** `hatch build` produces a wheel that does not contain `src/lucy_ng/webview/static/index.html`. `GET /` returns a `FileNotFoundError` or 500 after `pip install`.

**Why it happens:** Hatchling includes `*.py` files by default under `packages = ["src/lucy_ng"]` but silently ignores non-Python files unless declared in `artifacts`.

**How to avoid:** Add to `pyproject.toml` (the existing `artifacts` list already has two entries):

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/lucy_ng"]
artifacts = [
    "src/lucy_ng/data/schemas/*",
    "src/lucy_ng/lsd/filters/*",
    "src/lucy_ng/webview/static/*",   # Phase 91 addition
]
```

**Current `pyproject.toml` state:** `artifacts` line exists with two entries — add the third.

**Warning signs:** `hatch build && pip install dist/*.whl && python -c "from pathlib import Path; import lucy_ng.webview.app; p = Path(lucy_ng.webview.app.__file__).parent / 'static' / 'index.html'; print(p.exists())"` returns `False`.

---

### Pitfall 4: `epoch` Field in `timing.jsonl` Is a String, Not an Integer
**What goes wrong:** Arithmetic on `event["epoch"]` raises `TypeError: unsupported operand type(s) for -: 'str' and 'int'`.

**Why it happens:** The shell printf format in `case.md` uses `%s` for epoch: `"epoch":%s` with `$(date -u +%s)`. This produces `"epoch":"1751630400"` — a JSON string, not a JSON number.

**How to avoid:** Always cast: `int(event["epoch"])` before arithmetic. The finalizer in `case.md` already does `int(e["epoch"])` — follow the same pattern.

---

### Pitfall 5: Lexicographic Iteration Folder Sorting
**What goes wrong:** `sorted(analysis_dir.glob("iteration_*/"))` returns `["iteration_1", "iteration_10", "iteration_2", ...]` — `iteration_10` is picked as "newest" when iteration_9 is actually the newest after a 9-iteration run.

**Why it happens:** String comparison on `"10" < "2"` is False lexicographically but correct numerically.

**How to avoid:** Parse the numeric suffix with a regex and sort by `int`. See the `_newest_solutions_smi` helper in the Data-Source Schemas section.

---

### Pitfall 6: MolDraw2DSVG Instance Reuse Across Requests
**What goes wrong:** Rendering artifacts or corrupted SVG output when the same `MolDraw2DSVG` instance is reused for a second `DrawMolecule()` call.

**Why it happens:** `MolDraw2DSVG` is stateful — `FinishDrawing()` closes the drawing context and the instance is not resettable.

**How to avoid:** Create a fresh `MolDraw2DSVG(width, height)` instance inside `render_smiles()` on every call (D-10: no server-side cache → naturally one-instance-per-call).

---

### Pitfall 7: Mid-Write Partial Line in `timing.jsonl`
**What goes wrong:** The last line of `timing.jsonl` is a partial JSON object (e.g., `{"utc":"2026`...) when the file is read mid-write. `json.loads()` raises `json.JSONDecodeError`, which propagates as a 500.

**Why it happens:** The `printf >> file` shell command is not atomic at the filesystem level; a concurrent read can see a partial write.

**How to avoid:** Parse `timing.jsonl` line-by-line and skip any line that fails `json.loads()`:
```python
events = []
for line in content.splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        events.append(json.loads(line))
    except json.JSONDecodeError:
        continue  # skip partial last line
```

---

## Code Examples

### Full TestClient Test Pattern for Graceful Degradation
```python
# Source: FastAPI TestClient docs + existing test_cli_webview.py patterns
from fastapi.testclient import TestClient
from pathlib import Path
import pytest

@pytest.fixture
def empty_analysis_dir(tmp_path: Path) -> Path:
    """Empty analysis dir — no files at all."""
    d = tmp_path / "analysis"
    d.mkdir()
    return d

@pytest.fixture
def live_analysis_dir(tmp_path: Path) -> Path:
    """Live-run state: only timing.jsonl + iteration_01/solutions.smi."""
    d = tmp_path / "analysis"
    d.mkdir()
    (d / "timing.jsonl").write_text(
        '{"utc":"2026-07-04T10:00:00Z","epoch":"1751630400","event":"run_start","phase":"run","agent":""}\n'
        '{"utc":"2026-07-04T10:00:05Z","epoch":"1751630405","event":"phase_start","phase":"lsd-iteration-01","agent":"lsd-engineer"}\n'
    )
    iter_dir = d / "iteration_01"
    iter_dir.mkdir()
    (iter_dir / "solutions.smi").write_text(
        "CC(=O)Oc1ccccc1C(=O)O\n"
        "c1ccccc1\n"
        "not_a_real_smiles_XXXX\n"  # malformed — triggers placeholder
    )
    return d

@pytest.fixture
def final_analysis_dir(tmp_path: Path) -> Path:
    """Final state: timing.json + ranking_results.json present."""
    import json
    d = tmp_path / "analysis"
    d.mkdir()
    (d / "timing.json").write_text(json.dumps({
        "run_start_utc": "2026-07-04T10:00:00Z",
        "run_end_utc": "2026-07-04T11:30:00Z",
        "total_duration_s": 5400,
        "total_duration_hms": "01:30:00",
        "phases": [
            {"phase": "lsd-iteration-01", "agent": "lsd-engineer",
             "start_utc": "2026-07-04T10:00:05Z", "end_utc": "2026-07-04T11:00:00Z",
             "duration_s": 3595}
        ]
    }))
    (d / "ranking_results.json").write_text(json.dumps({
        "total_solutions": 2, "ranked_count": 2, "skipped_count": 0,
        "experimental_shifts": [128.0], "tolerance": 5.0,
        "solutions": [
            {"rank": 1, "solution_index": 1, "smiles": "c1ccccc1",
             "mae": 0.1, "quality": "excellent", "deviations": [0.1],
             "within_3ppm": 1, "within_5ppm": 1, "total_carbons": 6,
             "max_deviation": 0.1, "prediction_rate": 1.0,
             "matched_count": 1, "has_aromatic_ring": True},
        ],
        "warnings": []
    }))
    return d


class TestStatusEndpoint:
    def test_waiting_when_empty(self, empty_analysis_dir):
        from lucy_ng.webview.app import create_app
        with TestClient(create_app(empty_analysis_dir)) as client:
            r = client.get("/api/status")
        assert r.status_code == 200
        assert r.json()["state"] == "waiting"

    def test_live_from_timing_jsonl(self, live_analysis_dir):
        from lucy_ng.webview.app import create_app
        with TestClient(create_app(live_analysis_dir)) as client:
            r = client.get("/api/status")
        assert r.status_code == 200
        data = r.json()
        assert data["state"] in ("running", "waiting")
        assert data.get("iteration") is not None

    def test_complete_from_timing_json(self, final_analysis_dir):
        from lucy_ng.webview.app import create_app
        with TestClient(create_app(final_analysis_dir)) as client:
            r = client.get("/api/status")
        assert r.status_code == 200
        assert r.json()["state"] == "complete"


class TestStructuresEndpoint:
    def test_unranked_from_solutions_smi(self, live_analysis_dir):
        from lucy_ng.webview.app import create_app
        with TestClient(create_app(live_analysis_dir)) as client:
            r = client.get("/api/structures")
        assert r.status_code == 200
        data = r.json()
        assert data["source"] == "unranked"
        assert len(data["structures"]) <= 10

    def test_out_of_range_svg_returns_404(self, live_analysis_dir):
        from lucy_ng.webview.app import create_app
        with TestClient(create_app(live_analysis_dir)) as client:
            r = client.get("/api/structure/999.svg")
        assert r.status_code == 404

    def test_malformed_smiles_returns_placeholder_svg(self, live_analysis_dir):
        from lucy_ng.webview.app import create_app
        with TestClient(create_app(live_analysis_dir)) as client:
            # index 2 is "not_a_real_smiles_XXXX" in the live fixture
            r = client.get("/api/structure/2.svg")
        assert r.status_code == 200
        assert "image/svg+xml" in r.headers["content-type"]
        # Placeholder contains the grey rect and question mark
        assert "?" in r.text or "rect" in r.text

    def test_valid_smiles_returns_real_svg(self, live_analysis_dir):
        from lucy_ng.webview.app import create_app
        with TestClient(create_app(live_analysis_dir)) as client:
            r = client.get("/api/structure/0.svg")  # aspirin — valid
        assert r.status_code == 200
        assert "image/svg+xml" in r.headers["content-type"]
        # Real RDKit SVG contains path elements
        assert "<path" in r.text or "<line" in r.text
```

### pyproject.toml Artifact Addition
```toml
# Current (Phase 90 state):
[tool.hatch.build.targets.wheel]
packages = ["src/lucy_ng"]
artifacts = ["src/lucy_ng/data/schemas/*", "src/lucy_ng/lsd/filters/*"]

# Phase 91 change — add one line:
[tool.hatch.build.targets.wheel]
packages = ["src/lucy_ng"]
artifacts = [
    "src/lucy_ng/data/schemas/*",
    "src/lucy_ng/lsd/filters/*",
    "src/lucy_ng/webview/static/*",
]
```

### Vanilla JS Auto-Refresh Skeleton
```html
<!-- Source: vanilla JS setInterval + fetch pattern (no build step, inline) -->
<script>
const STATUS_URL = '/api/status';
const STRUCTURES_URL = '/api/structures';
const LOG_URL = '/api/log';
const REFRESH_MS = 3000;

async function refreshStatus() {
  try {
    const r = await fetch(STATUS_URL);
    const data = await r.json();
    // update DOM — e.g., document.getElementById('status-bar').textContent = ...
    renderStatus(data);
  } catch (e) {
    console.warn('status fetch failed:', e);
  }
}

async function refreshLog() {
  const logEl = document.getElementById('log-panel');
  const atBottom = logEl.scrollHeight - logEl.scrollTop <= logEl.clientHeight + 5;
  try {
    const r = await fetch(LOG_URL);
    const data = await r.json();
    logEl.textContent = data.content || '';
    if (atBottom) logEl.scrollTop = logEl.scrollHeight;  // D-13: preserve scroll
  } catch (e) {
    console.warn('log fetch failed:', e);
  }
}

// Start polling
setInterval(refreshStatus, REFRESH_MS);
setInterval(refreshLog, REFRESH_MS);
// Initial load
refreshStatus(); refreshStructures(); refreshLog();
</script>
```

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured in pyproject.toml) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_webview_api.py -x -v` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WV-03 | `GET /api/status` returns 200 with `state=waiting` when no files | unit (TestClient) | `pytest tests/test_webview_api.py::TestStatusEndpoint::test_waiting_when_empty -x` | Wave 0 |
| WV-03 | `GET /api/status` derives iteration + active_phase from `timing.jsonl` | unit (TestClient) | `pytest tests/test_webview_api.py::TestStatusEndpoint::test_live_from_timing_jsonl -x` | Wave 0 |
| WV-03 | `GET /api/status` returns complete state when `timing.json` present | unit (TestClient) | `pytest tests/test_webview_api.py::TestStatusEndpoint::test_complete_from_timing_json -x` | Wave 0 |
| WV-04 | `GET /api/structures` returns unranked list from `solutions.smi` | unit (TestClient) | `pytest tests/test_webview_api.py::TestStructuresEndpoint::test_unranked_from_solutions_smi -x` | Wave 0 |
| WV-04 | `GET /api/structures` returns ranked list from `ranking_results.json` | unit (TestClient) | `pytest tests/test_webview_api.py::TestStructuresEndpoint::test_ranked_from_ranking_results -x` | Wave 0 |
| WV-04 | `GET /api/structure/{i}.svg` returns valid SVG for good SMILES | unit (TestClient) | `pytest tests/test_webview_api.py::TestStructuresEndpoint::test_valid_smiles_returns_real_svg -x` | Wave 0 |
| WV-04 | `GET /api/structure/{i}.svg` returns placeholder for malformed SMILES | unit (TestClient) | `pytest tests/test_webview_api.py::TestStructuresEndpoint::test_malformed_smiles_returns_placeholder_svg -x` | Wave 0 |
| WV-06 | `GET /api/structure/999.svg` returns 404 | unit (TestClient) | `pytest tests/test_webview_api.py::TestStructuresEndpoint::test_out_of_range_svg_returns_404 -x` | Wave 0 |
| WV-05 | `GET /api/log` returns raw CASE-PROGRESS.md content | unit (TestClient) | `pytest tests/test_webview_api.py::TestLogEndpoint::test_log_returns_content -x` | Wave 0 |
| WV-06 | `GET /api/log` returns waiting payload when no CASE-PROGRESS.md | unit (TestClient) | `pytest tests/test_webview_api.py::TestLogEndpoint::test_log_waiting_when_empty -x` | Wave 0 |
| WV-06 | `GET /` serves index.html with Content-Type text/html | unit (TestClient) | `pytest tests/test_webview_api.py::TestFrontend::test_index_html_served -x` | Wave 0 |
| WV-08 | hatch artifacts includes `webview/static/*` | unit (pyproject parse) | `pytest tests/test_webview_api.py::TestPackaging::test_hatch_artifacts_include_static -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_webview_api.py -x -v`
- **Per wave merge:** `pytest` (full suite)
- **Phase gate:** Full suite green + `mypy src/lucy_ng` passes before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_webview_api.py` — all test classes above
- [ ] `tests/conftest.py` — add `live_analysis_dir`, `final_analysis_dir`, `empty_analysis_dir` fixtures (can extend the existing `webview_analysis_dir` fixture already there)

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| fastapi | API router + Response/FileResponse | Yes | 0.128.2 installed | Install via `[webview]` extra |
| rdkit (MolDraw2DSVG) | SVG depiction | Yes | `rdkit>=2023.0` (present as core dep) | None — core dep |
| httpx | TestClient transport | Yes | 0.28.1 | None needed — present |
| pathlib, json, datetime, re | File I/O + parsing | Yes | stdlib | None |

**Missing dependencies with no fallback:** none

---

## Security Domain

No new threat surface introduced. Phase 91 adds read-only file-serving endpoints on the same `127.0.0.1`-bound server established in Phase 90.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Localhost-only; no user accounts |
| V3 Session Management | No | Stateless read-only API |
| V4 Access Control | No | Localhost bind is the access control |
| V5 Input Validation | Partial | `i` in `GET /api/structure/{i}.svg`: FastAPI type annotation `int` provides automatic rejection of non-integer values; range check in handler returns 404 |
| V6 Cryptography | No | No encryption needed for 127.0.0.1-only service |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via `analysis_dir` | Tampering | Already mitigated in Phase 90 (`Path.resolve()` + `is_dir()` check before server starts) |
| SVG injection via SMILES | Spoofing | RDKit renders to an SVG string containing only drawing primitives (paths, circles, text); no inline scripts; SMILES cannot inject JavaScript into RDKit-generated SVG |
| Out-of-bounds index in SVG endpoint | Information Disclosure | Return 404 (not the raw array length or error detail) |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `timing.jsonl` epoch field is always a string (`"epoch":"1751630400"`) produced by shell `printf %s` | Data-Source Schemas | Low — if it were ever a JSON number, `int()` cast still works |
| A2 | `ranking_results.json` is always a dict with a `solutions` array at the top level, as produced by `lucy lsd rank --format json` | Data-Source Schemas | Low — schema verified from `lsd.py` source; format is stable |
| A3 | `solutions.smi` contains only SMILES (no title column) based on `LSDOutputParser.parse_smiles_file` which skips any line not matching the SMILES regex | Data-Source Schemas | Low — verified from `parser.py` source |

---

## Open Questions

1. **`GET /api/status` response schema field names for "waiting for data" payload**
   - What we know: D-04 requires HTTP 200 with a "well-formed" payload; field names are Claude's discretion.
   - Recommendation: Use `{"state": "waiting", "message": "Waiting for run data..."}` consistently across all endpoints; frontends check `state == "waiting"` to show the empty/skeleton widget.

2. **`GET /api/log` response shape: JSON wrapper or raw text?**
   - What we know: SC #2 says "text/JSON payload". D-12 says "raw current content".
   - Recommendation: Return `{"content": "<raw markdown text>", "state": "ok"|"waiting"}` as `application/json`. This avoids `Content-Type` negotiation complexity and keeps all endpoints JSON. Frontend uses `data.content` in `<pre>`.

3. **SVG index convention: 0-based or 1-based?**
   - `solutions.smi` parser uses 1-based `LSDSolution.index`. `ranking_results.json` `rank` is 1-based.
   - Recommendation: Use 0-based indices for the `GET /api/structure/{i}.svg` URL path (matches array indexing on the frontend). Document this clearly in the endpoint.

---

## Sources

### Primary (HIGH confidence)
- `src/lucy_ng/webview/app.py` — actual `create_app()` implementation; Phase 90 comment marks router-docking point
- `src/lucy_ng/webview/state.py`, `server.py` — confirmed fastapi-free; WV-08 invariant enforced
- `src/lucy_ng/lsd/parser.py` `parse_smiles_file` — verified `solutions.smi` format (one SMILES per line, no title column)
- `src/lucy_ng/cli/lsd.py` `_perform_ranking` lines 283–315 — `ranking_results.json` schema verified from source
- `.claude/commands/lucy-ng/case.md` §timing lines 288–351 — `timing.jsonl` event schema + `timing.json` finalization verified
- `.claude/commands/lucy-ng/references/progress-format.md` — `CASE-PROGRESS.md` structure verified
- `pyproject.toml` — confirmed `artifacts` list at `[tool.hatch.build.targets.wheel]`; current entries are `schemas/*` and `filters/*`
- RDKit SVG API — `from rdkit.Chem.Draw import rdMolDraw2D, PrepareMolForDrawing` confirmed working in session; `addAtomIndices` option confirmed; `MolFromSmiles` returns `None` for malformed SMILES confirmed
- FastAPI `APIRouter` prefix + `include_router` — verified in session (`Routes: ['/api/test']`)
- FastAPI `FileResponse` for `GET /` — verified in session (status 200, `text/html` Content-Type)

### Secondary (MEDIUM confidence)
- `tests/test_cli_webview.py` — existing TestClient patterns, fixture structure, skip guards
- `tests/conftest.py` — existing `webview_analysis_dir` and `webview_server` fixtures

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- FastAPI router pattern: HIGH — verified against actual app.py + in-session APIRouter check
- RDKit SVG API: HIGH — import path, `addAtomIndices`, malformed SMILES detection all verified in session
- Data-source schemas: HIGH — verified from actual source files (`parser.py`, `lsd.py`, `case.md`, `progress-format.md`)
- Static file serving: HIGH — FileResponse verified in session
- Packaging (hatch artifacts): HIGH — pyproject.toml read; existing pattern confirmed
- Testing patterns: HIGH — existing test file and conftest read

**Research date:** 2026-07-04
**Valid until:** 2026-08-04 (stable stack; FastAPI/RDKit APIs not fast-moving for this use case)
