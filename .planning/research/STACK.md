# Stack Research: v9.3 CASE Web-View Stage 2

**Domain:** Python web dashboard with server-side NMR spectra rendering
**Milestone:** v9.3 CASE Web-View Stage 2
**Researched:** 2026-07-07
**Confidence:** HIGH — all findings grounded in the existing codebase and standard Python/matplotlib/FastAPI API patterns. One gap flagged (data table source path for peak lists).

---

## Context: What Already Exists (Do Not Re-evaluate)

| Component | Version (installed) | pyproject.toml | Status |
|-----------|---------------------|----------------|--------|
| Python | 3.10+ | `>=3.10` | Locked |
| FastAPI | current | `>=0.100` ([webview] extra) | In use |
| uvicorn | current | `>=0.20` ([webview] extra) | In use |
| numpy | 2.x | `>=1.24` (core) | In use |
| RDKit | 2025.x | `>=2023.0` (core) | In use (SVG depiction) |
| BrukerReader | — | lucy_ng internal | In use (reads 1D + 2D Bruker data) |
| nmrglue | git master | git dep (core) | In use (Bruker file I/O) |

Note: The existing `structures.py` router serves RDKit SVG via `Response(content=svg_str, media_type="image/svg+xml")` — the PNG spectra endpoint follows the same pattern with `media_type="image/png"`.

---

## New Dependency Required for Stage 2

**matplotlib is NOT currently in `pyproject.toml`** (confirmed by grep — zero imports in `src/lucy_ng/`; not listed as a dependency). It IS installed on the system (3.10.7), likely as a transitive dep from the scientific Python environment. For Stage 2 spectra rendering, it must be explicitly declared to make the requirement reproducible:

```toml
[project.optional-dependencies]
webview = [
    "fastapi>=0.100",
    "uvicorn>=0.20",
    "matplotlib>=3.7",      # ← ADD: server-side spectra rendering (Stage 2)
]
```

That is the only new library dependency for Stage 2. Everything else is reuse.

---

## Recommended Stack: Five Decision Areas

### 1. Spectra Rendering Backend

**Recommendation: matplotlib Agg (server-side) → PNG**

Use `matplotlib.figure.Figure` with `matplotlib.backends.backend_agg.FigureCanvasAgg` directly, never `matplotlib.pyplot`.

Why:
- `pyplot` maintains global state (current figure/axes) that is NOT thread-safe in a FastAPI/uvicorn worker.
- `Figure()` + explicit `FigureCanvasAgg` is fully stateless and thread-safe — each request gets its own `Figure` object with its own canvas.
- No `matplotlib.use('Agg')` call is needed (that call modifies global backend state). Setting the canvas explicitly via `FigureCanvasAgg(fig)` is sufficient and safe in a server context.
- PNG over SVG because 2D contour plots with hundreds of contour lines produce SVGs with thousands of path elements (easily >1 MB); a 800×500 PNG at dpi=100 is 50–150 KB.
- SVG remains correct for molecular structure depictions (RDKit, already in place) because those are compact line drawings.

Pattern for 1D spectra:
```python
import io
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

def render_1d_spectrum(spectrum: Spectrum1D) -> bytes:
    fig = Figure(figsize=(10, 4))
    FigureCanvasAgg(fig)          # Agg canvas, no global state
    ax = fig.add_subplot(111)
    # NMR convention: ppm scale decreasing left to right
    ax.plot(spectrum.ppm_scale[::-1], spectrum.data.real[::-1], lw=0.8, color='#1a5276')
    ax.set_xlabel('δ (ppm)')
    ax.set_ylabel('Intensity')
    ax.set_title(f'{spectrum.nucleus} NMR')
    ax.invert_xaxis()             # high ppm on left
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    return buf.getvalue()
    # fig goes out of scope here — no plt.close() needed; GC handles it
```

Pattern for 2D spectra (HSQC / HMBC / COSY):
```python
def render_2d_spectrum(spectrum: Spectrum2D) -> bytes:
    fig = Figure(figsize=(8, 8))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    # Determine auto contour levels from top 5% of absolute values
    import numpy as np
    threshold = np.percentile(np.abs(spectrum.data), 95)
    levels = np.linspace(threshold * 0.1, threshold, 8)
    ax.contour(
        spectrum.f2_ppm_scale[::-1],   # F2 = 1H (x-axis)
        spectrum.f1_ppm_scale[::-1],   # F1 = 13C or 1H (y-axis)
        spectrum.data,
        levels=levels,
        colors=['#1a5276'],
        linewidths=0.6,
    )
    ax.set_xlabel(f'F2: {spectrum.f2_nucleus} δ (ppm)')
    ax.set_ylabel(f'F1: {spectrum.f1_nucleus} δ (ppm)')
    ax.set_title(spectrum.experiment_type)
    ax.invert_xaxis()
    ax.invert_yaxis()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    return buf.getvalue()
```

### 2. Serving Images from FastAPI

**Recommendation: `Response(content=bytes, media_type="image/png")` with a per-router in-memory cache**

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

def make_router(analysis_dir: Path) -> APIRouter:
    # WV-08: all heavy imports inside make_router body, never at module level
    from matplotlib.figure import Figure                          # lazy
    from matplotlib.backends.backend_agg import FigureCanvasAgg  # lazy
    from lucy_ng.readers.bruker import BrukerReader               # already imported lazily elsewhere

    router = APIRouter(prefix="/api")
    _cache: dict[str, bytes] = {}  # render-once cache: exp_key → PNG bytes

    @router.get("/spectrum/1d/{exp_type}.png")
    def get_1d_spectrum(exp_type: str) -> Response:
        if exp_type in _cache:
            return Response(content=_cache[exp_type], media_type="image/png")
        exp_dir = _find_experiment(analysis_dir.parent, exp_type)
        if exp_dir is None:
            raise HTTPException(status_code=404, detail="Experiment not found")
        try:
            spectrum = BrukerReader.read_1d(exp_dir)
            png = render_1d_spectrum(spectrum)
            _cache[exp_type] = png
            return Response(content=png, media_type="image/png")
        except Exception:
            raise HTTPException(status_code=404, detail="Cannot render spectrum")

    @router.get("/spectrum/2d/{exp_type}.png")
    def get_2d_spectrum(exp_type: str) -> Response:
        ...  # same pattern

    return router
```

Notes on this pattern:
- `Response(content=bytes, ...)` is correct for pre-loaded in-memory bytes; `StreamingResponse` is for generators/file handles and adds no benefit here.
- The `_cache` dict lives in the closure — one cache per `analysis_dir`, not shared across different analysis dirs. Cache is per-process in-memory; it clears on server restart. This is appropriate because Bruker experiment data is immutable once acquired.
- During a live run before a spectrum file exists, return HTTP 404 gracefully (same as the structures router for out-of-range index).
- Consistent with WV-08: `matplotlib`, `FigureCanvasAgg`, and `BrukerReader` are imported inside `make_router`, never at module level of `routers/spectra.py`.

**Where the Bruker data lives:**
The webview currently takes only `analysis_dir`. CASE always runs `lucy webview serve <compound_path>/analysis`, so `analysis_dir.parent` is the compound path where Bruker experiment directories live (numbered subdirectories: `1/`, `2/`, etc.). The spectra router discovers experiments by scanning `analysis_dir.parent` for directories containing an `acqus` file (1D) or both `acqus` + `acqu2s` files (2D). The `BrukerReader` already handles this correctly.

Discovery helper:
```python
def _find_experiment(compound_path: Path, exp_type: str) -> Path | None:
    """Find Bruker experiment dir by pulse program or nucleus match."""
    for d in sorted(compound_path.iterdir()):
        if not d.is_dir(): continue
        acqus = d / "acqus"
        if not acqus.exists(): continue
        pp = (acqus.read_text(errors='replace')
              .split('PULPROG')[1].split('\n')[0]
              .strip().strip('<>').lower()
              if 'PULPROG' in acqus.read_text(errors='replace') else '')
        if exp_type in ('1h', 'proton') and '1h' in pp or 'zg' in pp:
            return d
        ...
    return None
```

In practice the discovery logic will need to handle the specific PULPROG names used in the test datasets (see `bruker.py`'s `_detect_experiment_type()` for the pattern-matching already in use). The spectra router can delegate to the same `BrukerReader` logic.

### 3. Markdown Rendering in the Frontend

**Recommendation: Hand-rolled safe markdown-to-DOM renderer in `index.html`**

The constraint is self-contained single-file vanilla JS with no CDN and no build step. The existing log panel assigns content via `logEl.textContent = content` — this must be replaced with structured DOM building, but the XSS guard must be preserved.

The exact subset of CASE-PROGRESS.md that needs rendering (written by the orchestrator per `progress-format.md`):

| Markdown syntax | Element | Notes |
|-----------------|---------|-------|
| `## Iteration N` | `<h2>` | Top-level section |
| `### Agent Name` | `<h3>` | Agent sub-section |
| `**bold text**` | `<strong>` | Inline, appears in status lines |
| `` `inline code` `` | `<code>` | Inline, for shift values / formulas |
| `\| col \| col \|` rows | `<table><tr><td>` | Peak assignment tables |
| `---` | `<hr>` | Section separators |
| bare text lines | `<p>` | Narrative paragraphs |
| ` ``` ` fences | `<pre><code>` | LSD snippets (rare) |

Implementation principle — all text content through `textContent`, never `innerHTML`:

```javascript
function renderMarkdown(text) {
    var container = document.createElement('div');
    var lines = text.split('\n');
    var i = 0;

    while (i < lines.length) {
        var line = lines[i];

        // Code fences
        if (line.startsWith('```')) {
            var code = [];
            i++;
            while (i < lines.length && !lines[i].startsWith('```')) {
                code.push(lines[i++]);
            }
            var pre = document.createElement('pre');
            var codeEl = document.createElement('code');
            codeEl.textContent = code.join('\n');  // safe
            pre.appendChild(codeEl);
            container.appendChild(pre);
            i++;
            continue;
        }

        // HR
        if (line.match(/^---+$/)) {
            container.appendChild(document.createElement('hr'));
            i++; continue;
        }

        // Headings
        if (line.startsWith('## ')) {
            var h = document.createElement('h2');
            appendInlineNodes(h, line.slice(3));   // inline parser for bold/code
            container.appendChild(h);
            i++; continue;
        }
        if (line.startsWith('### ')) {
            var h3 = document.createElement('h3');
            appendInlineNodes(h3, line.slice(4));
            container.appendChild(h3);
            i++; continue;
        }

        // Table (collect consecutive pipe-starting lines)
        if (line.startsWith('|')) {
            var table = buildTable(lines, i);
            container.appendChild(table.el);
            i = table.nextI;
            continue;
        }

        // Non-empty paragraph text
        if (line.trim()) {
            var p = document.createElement('p');
            appendInlineNodes(p, line);
            container.appendChild(p);
        }

        i++;
    }
    return container;
}

// appendInlineNodes: safe inline parser for **bold** and `code`
// Uses textContent for all text — never innerHTML
function appendInlineNodes(parent, text) {
    var parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/);
    parts.forEach(function(part) {
        if (part.startsWith('**') && part.endsWith('**')) {
            var strong = document.createElement('strong');
            strong.textContent = part.slice(2, -2);
            parent.appendChild(strong);
        } else if (part.startsWith('`') && part.endsWith('`')) {
            var code = document.createElement('code');
            code.textContent = part.slice(1, -1);
            parent.appendChild(code);
        } else if (part) {
            parent.appendChild(document.createTextNode(part));
        }
    });
}
```

This replaces the current `logEl.textContent = content` in `refreshLog()`. The log panel element changes from `<pre id="log-panel">` to `<div id="log-panel">` (pre is incompatible with block-level elements like table/h2).

**What this does NOT support and why that is acceptable:**
- Nested lists — CASE-PROGRESS.md uses tables, not lists
- Link URLs — not present in CASE-PROGRESS.md content
- Images — not present
- Blockquotes — not present

This renderer is purpose-built for CASE-PROGRESS.md's actual output format, not a general markdown renderer.

### 4. Tabbed UI Without a Build Step

**Recommendation: Pure CSS/JS tab navigation in a single `index.html` file**

The current layout has two panels side by side (`#structure-panel` left, `#log-panel-wrapper` right). Stage 2 adds spectra and data tables. The cleanest restructuring is:

- Keep the top status bar unchanged.
- Replace the two-column `#main` with a layout that has the structure panel on the left (unchanged) and a tabbed panel on the right with four tabs.

HTML structure:
```html
<div id="main">
  <!-- Left: structure panel (unchanged) -->
  <div id="structure-panel">...</div>

  <!-- Right: tabbed panel -->
  <div id="tab-area">
    <div class="tab-bar">
      <button class="tab-btn active" data-tab="log">Run Log</button>
      <button class="tab-btn" data-tab="spectra-1d">1D Spectra</button>
      <button class="tab-btn" data-tab="spectra-2d">2D Spectra</button>
      <button class="tab-btn" data-tab="tables">Data Tables</button>
    </div>
    <div id="tab-log"        class="tab-panel active"><!-- log div --></div>
    <div id="tab-spectra-1d" class="tab-panel hidden"><!-- img tags --></div>
    <div id="tab-spectra-2d" class="tab-panel hidden"><!-- img tags --></div>
    <div id="tab-tables"     class="tab-panel hidden"><!-- table HTML --></div>
  </div>
</div>
```

CSS:
```css
.tab-bar { display: flex; border-bottom: 1px solid #dee2e6; margin-bottom: 8px; }
.tab-btn {
    padding: 6px 14px; border: none; background: none; cursor: pointer;
    font-size: 13px; color: #6c757d; border-bottom: 2px solid transparent;
}
.tab-btn.active { color: #212529; border-bottom-color: #1a5276; font-weight: 600; }
.tab-panel { display: none; }
.tab-panel.active { display: block; }
```

JS (replaces nothing — new event wiring):
```javascript
document.querySelectorAll('.tab-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
        var target = btn.dataset.tab;
        document.querySelectorAll('.tab-btn').forEach(function(b) {
            b.classList.toggle('active', b.dataset.tab === target);
        });
        document.querySelectorAll('.tab-panel').forEach(function(p) {
            p.classList.toggle('active', p.id === 'tab-' + target);
        });
    });
});
```

**`index.html` stays as ONE file.** The hatch artifact entry is `src/lucy_ng/webview/static/*` (glob), so splitting is technically possible, but the v9.2 design decision to keep it as a single file holds — no reason to add complexity.

Spectra panels use `<img>` elements whose `src` points to the new PNG endpoints:
```html
<!-- Inside tab-spectra-1d -->
<img id="spec-13c" src="/api/spectrum/1d/13c.png" alt="13C spectrum" style="max-width:100%">
<img id="spec-1h"  src="/api/spectrum/1d/1h.png"  alt="1H spectrum"  style="max-width:100%">
```

These images are fetched once on page load (or on tab activation via lazy-load logic). No polling needed — spectra are static after acquisition. The 3-second polling loop should NOT re-fetch spectra images on every tick (add a loaded flag per image).

### 5. Data Table Sources

**LSD Constraint Inventory (HIGH confidence)**

Source: `analysis_dir / "iteration_NN" / "compound.lsd"` (the latest iteration dir). The JSON constraint inventory is embedded at the top of every `compound.lsd` file as a POSIX-comment block:

```
; {"constraint_inventory": { ... }}
```

Parse path: read the latest `compound.lsd` → extract lines starting with `; {` → `json.loads()` → serve as `/api/constraints`.

Alternative (also viable): `lucy lsd validate-inventory --format json analysis/iteration_NN/compound.lsd` — uses the existing CLI to extract the JSON. This is safer because the parser already handles edge cases. The router can shell out via `subprocess.run()`.

**HMBC Usage (HIGH confidence)**

Source: HMBC lines in `compound.lsd`:
```
HMBC carbon_idx proton_idx min_j max_j  ; comment
```
Parse path: grep lines starting with `HMBC ` from the latest `compound.lsd` → split fields → serve as part of `/api/constraints`.

**Peak Lists (MEDIUM confidence — design decision required)**

Source: CASE-PROGRESS.md `## Setup` section. The orchestrator writes peak tables into the `## Setup` section from the nmr-chemist's [SETUP-COMPLETE] message. These tables are markdown pipe-tables. The nmr-chemist CLI commands (`lucy pick 1d/hsqc/hmbc --format json`) write to stdout only — no separate peak JSON files are written to disk.

Options for Stage 2:
1. Parse the `## Setup` section of CASE-PROGRESS.md (the markdown table) in a new `/api/peaks` endpoint. Fragile (depends on orchestrator's exact markdown formatting).
2. Modify the CASE workflow to write a `peaks_summary.json` to `analysis_dir` at the end of peak picking. This is cleaner but requires a workflow change.
3. Defer peak tables to a later phase and only show constraint inventory + HMBC usage in Stage 2.

**Recommendation for Stage 2: Start with option 3 (defer peak list tables).** Serve the constraint inventory and HMBC lines from `compound.lsd` (well-structured, machine-parseable). Add a note in the roadmap that peak list tables require either markdown parsing or a workflow addition.

---

## Core Technologies Table

| Technology | Version | Purpose | New for Stage 2? |
|------------|---------|---------|-----------------|
| matplotlib | ≥3.7 | Server-side PNG spectra rendering (1D line, 2D contour) | YES — add to [webview] extra |
| `matplotlib.backends.backend_agg.FigureCanvasAgg` | (part of matplotlib) | Headless, thread-safe canvas — no `use('Agg')` global | YES — use pattern |
| `fastapi.responses.Response` | (part of fastapi) | Serve PNG bytes: `Response(content=bytes, media_type="image/png")` | New endpoint type |
| `io.BytesIO` | (stdlib) | Buffer for `fig.savefig()` output | YES — pattern |
| `lucy_ng.readers.bruker.BrukerReader` | (internal) | Read Bruker 1D/2D data → Spectrum1D/Spectrum2D | Reused |

## Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `matplotlib.figure.Figure` | ≥3.7 | Direct figure construction without pyplot global state | All server-side rendering |
| `numpy` | ≥1.24 (already core dep) | Contour level computation, array slicing | 2D spectra auto-levels |

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `matplotlib.pyplot` (plt.*) | Not thread-safe; uses global state (current figure, current axes); calling `plt.figure()` or `plt.close()` in a FastAPI handler will corrupt renders across concurrent requests | `matplotlib.figure.Figure` + `FigureCanvasAgg` directly |
| `matplotlib.use('Agg')` global call | Modifies module-level backend state; if called after any other matplotlib import it raises `UserWarning` and may be ignored; fragile in a server that might already have imported matplotlib | Explicit `FigureCanvasAgg(fig)` instead |
| Plotly / Bokeh / Altair / d3.js | All require CDN delivery or a build step; violate the self-contained no-CDN constraint | Server-side matplotlib PNG |
| marked.js / micromark / any JS markdown library | Would require CDN or inlining a >10 KB blob; more complex than the needed subset | Hand-rolled 50-line DOM renderer |
| htmx / Alpine.js / any JS framework | CDN dependency; overkill for tab navigation | 10-line vanilla JS tab switcher |
| `StreamingResponse` for PNG | For generators/file handles; adds overhead for in-memory bytes | `Response(content=bytes, ...)` |
| `pandas` | Not needed; constraint inventory from compound.lsd is simple key-value JSON; peak tables are simple lists | Direct `json.loads()` / string split |
| Splitting `index.html` into multiple files | Adds path-join complexity; single file is simpler to package, test, and serve | Keep single `index.html` |

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| Server-side PNG via matplotlib | Client-side plotly.js from CDN | Violates no-CDN constraint; CDN means no air-gap, adds external dependency |
| `FigureCanvasAgg` explicit | `matplotlib.use('Agg')` global | Global state change unsafe in server; fails silently after first import |
| Hand-rolled markdown renderer | Inline minified marked.js (~50 KB) | Maintains XSS discipline; purpose-built for the CASE-PROGRESS.md subset; no blob to maintain |
| PNG format | SVG for spectra | 2D contour SVGs are >1 MB (thousands of path elements); PNG is 50–150 KB |
| `analysis_dir.parent` convention | Passing `compound_path` to `create_app()` | No API change needed; CASE always creates `analysis/` as a direct child of the compound dir |

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| matplotlib ≥3.7 | numpy ≥1.24 | Both already satisfied by existing deps |
| matplotlib 3.10.7 (system) | FastAPI + uvicorn (existing) | No conflicts; matplotlib is only imported inside route handlers |
| FigureCanvasAgg | Python 3.10–3.12 | Stable API; no breaking changes in matplotlib 3.x |

## Installation Delta

```toml
# In pyproject.toml [project.optional-dependencies]:
webview = [
    "fastapi>=0.100",
    "uvicorn>=0.20",
    "matplotlib>=3.7",    # ADD for Stage 2 spectra rendering
]
```

```bash
# Reinstall with updated extra:
pip install -e ".[webview]"
```

## Sources

- Codebase reading: `src/lucy_ng/webview/app.py`, `routers/status.py`, `routers/structures.py`, `routers/log.py`, `static/index.html` — existing patterns confirmed (WV-08 lazy imports, make_router closure, Response for binary content)
- Codebase reading: `src/lucy_ng/readers/bruker.py` — `Spectrum1D`/`Spectrum2D` fields confirmed (data, ppm_scale, f1_ppm_scale, f2_ppm_scale, nucleus, experiment_type)
- Codebase reading: `pyproject.toml` — confirmed matplotlib absent from declared deps
- System: `python3 -c "import matplotlib; print(matplotlib.__version__)"` → 3.10.7 (installed but undeclared)
- Codebase reading: `.claude/agents/lucy-nmr-chemist.md`, `.claude/commands/lucy-ng/case.md` — confirmed peak data only in CASE-PROGRESS.md + compound.lsd (no separate JSON files written to analysis_dir)
- matplotlib official docs pattern: `Figure` + `FigureCanvasAgg` for headless server rendering — standard MEDIUM→HIGH confidence (stable API, widely documented, no version concerns for ≥3.7)
- Design spec: `docs/superpowers/specs/2026-07-02-case-webview-design.md` — Stage 2 requirements confirmed

---

*Stack research for: v9.3 CASE Web-View Stage 2 — spectra rendering, markdown log, tabbed UI, data tables*
*Researched: 2026-07-07*
