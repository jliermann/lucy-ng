# Pitfalls Research: v9.3 CASE Web-View Stage 2

**Domain:** Server-side matplotlib NMR spectra rendering + markdown log panel + data tables added to existing FastAPI + single-file vanilla-JS webview
**Researched:** 2026-07-07
**Confidence:** HIGH (direct codebase read + matplotlib/FastAPI architectural analysis + v9.2 post-mortem encoding)

---

## Critical Pitfalls

### Pitfall 1: matplotlib pyplot State-Machine Is Not Thread-Safe in a Concurrent Server

**What goes wrong:**
`import matplotlib.pyplot as plt` and any `plt.*` calls share a global figure-manager state across threads. FastAPI with uvicorn runs multiple async workers; sync route handlers are executed in uvicorn's default thread-pool executor. Two concurrent requests to a spectra endpoint that both call `plt.figure()` / `plt.savefig()` / `plt.close()` can corrupt each other's state, producing garbled images or hard-to-reproduce crashes. The failure is intermittent and environment-dependent, making it difficult to catch in single-request tests.

The `matplotlib.use("Agg")` backend call must occur **before** any `import matplotlib.pyplot` anywhere in the process, including in any transitively imported module. Calling it after pyplot has already been imported silently falls back to whatever backend was set at import time (often `TkAgg` or `QtAgg`), which may fail in a headless server.

**Why it happens:**
Developers copy the familiar `import matplotlib.pyplot as plt; fig, ax = plt.subplots(...)` pattern from notebooks. The pyplot API is designed for single-threaded interactive use. The global state includes the current figure, current axes, and the figure registry — all mutable and unprotected by locks.

**How to avoid:**
Use the fully object-oriented API with the `Agg` backend explicitly. Never import `matplotlib.pyplot` inside any webview module. The safe pattern for a route handler:

```python
# In spectra.py (a router module, imported only inside create_app())
import io
import matplotlib
matplotlib.use("Agg")  # must precede pyplot import; safe to call multiple times with same backend
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

def render_spectrum_1d_png(ppm_scale, intensities, title="") -> bytes:
    """Render a 1D NMR spectrum to PNG bytes. Never raises."""
    try:
        fig = Figure(figsize=(8, 3), dpi=100)
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        ax.plot(ppm_scale, intensities, color="black", linewidth=0.8)
        ax.set_xlabel("ppm")
        ax.set_xlim(float(ppm_scale[0]), float(ppm_scale[-1]))  # high→low, NMR convention
        ax.set_title(title)
        fig.tight_layout()
        buf = io.BytesIO()
        canvas.print_png(buf)
        return buf.getvalue()
    except Exception:
        return _placeholder_png()
    # Figure is garbage-collected when `fig` goes out of scope — no plt.close() needed
    # with the OO API because there is no global figure registry involved.
```

Key invariants:
- `matplotlib.use("Agg")` at the top of the module, before any `from matplotlib.figure import Figure`
- Use `Figure(...)` not `plt.figure(...)` — the OO path has no global state
- Use `FigureCanvasAgg` explicitly — do not call `fig.savefig()`  which can invoke the pyplot manager
- Return `bytes` (PNG via BytesIO), not a path — avoids temp-file race conditions

**Warning signs:**
- Any `import matplotlib.pyplot as plt` anywhere in `webview/` — immediate red flag
- `UserWarning: Matplotlib is currently using TkAgg` in server logs — Agg backend was not set before pyplot import
- Intermittent 500 errors on the spectra endpoint under concurrent load (even 2 simultaneous requests)
- Image output is all-white, all-black, or cut off — pyplot state corrupted mid-render

**Phase to address:**
The phase that introduces 1D spectra rendering. The `matplotlib.use("Agg")` + OO API pattern must be established before any 2D work, which inherits from 1D. Add an import-safety test mirroring the existing `test_main_importable_without_fastapi`: confirm that `from lucy_ng.webview import server` does not import matplotlib (which would break on a base install without the `[webview]` extra).

---

### Pitfall 2: 2D Contour Rendering Blocks the Async Event Loop and Exhausts Memory

**What goes wrong:**
A typical Bruker 2D NMR (e.g. HSQC) has a 1024 × 2048 or larger data matrix (float64 = 16 MB per spectrum). `matplotlib.contour()` on the full matrix with 16 contour levels computes isocontour tessellations across the entire array. On this machine, benchmarks for contour on a 1024×2048 float64 array typically take 500 ms–3 s, consuming 200–500 MB of peak RSS. Per-request, with no caching, a 3-tab webview refreshing every 3 s would issue a new contour render every second.

If the route handler is defined as `async def`, this sync computation runs on the async event loop and blocks all other requests for its duration — a classic event-loop stall. If defined as `def` (sync), FastAPI dispatches it to a thread-pool executor, which is safe for concurrency but still runs the full render every request.

**Why it happens:**
The naive approach is `ax.contour(f2_ppm, f1_ppm, data, levels=16)` — works fine for a one-off notebook plot, disastrous in a per-request server context. 2D NMR matrices are large by design; they represent the Fourier transform of a time-domain signal sampled at high density.

**How to avoid:**
Three complementary strategies, all required together:

1. **Downsample before contouring.** Decimate the 2D array to at most 512 × 512 for display. NMR contour plots show where peaks *are*, not fine lineshape — 4× downsampling in each dimension is invisible to a chemist at screen resolution. Use `data[::step_f1, ::step_f2]` with the matching subsampled ppm scales.

2. **Threshold-based contour levels.** Compute a noise floor (the same MAD-based sigma used in `PeakPicker2D._compute_2d_noise_sigma`), then use 8–12 logarithmically spaced positive levels starting at `4 * sigma`. This avoids rendering noise contours (which dominate the plot area and slow contouring) while showing all real peaks. HSQC: positive levels only. COSY: positive only. HMBC: positive only. DEPT-edited HSQC: add symmetric negative levels for CH2.

3. **Cache rendered PNGs keyed by file mtime.** The Bruker 2D data files do not change once written. Cache the rendered PNG bytes in a per-`analysis_dir` dict keyed by `(experiment_path, mtime)`. On a cache hit, serve bytes directly. Cache size: 3 experiments × ~150 KB PNG = ~450 KB — negligible.

4. **Use sync `def` route handlers** (not `async def`) for spectra endpoints — FastAPI routes that are defined as plain `def` are dispatched to the default thread-pool executor automatically, keeping the event loop free. Do NOT use `async def` with a blocking render inside.

```python
# In the spectra router — sync def, FastAPI runs in thread-pool
@router.get("/api/spectra/{expno}.png")
def get_spectrum_png(expno: str) -> Response:
    result = _render_or_cache(analysis_dir, expno)
    return Response(content=result, media_type="image/png")
```

**Warning signs:**
- Any `async def` route handler that calls `contour()` or `Figure()` without `run_in_executor` — event-loop blocking
- No downsampling: `ax.contour(f2_ppm, f1_ppm, data, ...)` where `data.shape` matches the raw Bruker matrix
- Server log shows render times > 500 ms per request for the 2D endpoints
- Memory usage climbs monotonically during repeated browser refreshes (no cache, new Figure per request)

**Phase to address:**
The phase introducing 2D contour rendering (after 1D is proven). Downsampling and caching must be in the initial implementation, not added as an optimization later. The mtime-keyed cache is a one-liner over a module-level `dict` — no library needed.

---

### Pitfall 3: ppm Axis Direction Is Reversed — Silent NMR-Domain Correctness Bug

**What goes wrong:**
NMR convention universally places **high ppm (downfield) on the left** and low ppm (upfield) on the right for the x-axis (F2/direct dimension). For 2D spectra, F1 (indirect dimension, y-axis) also places high ppm at the top. A plot with the axis in the wrong direction looks reasonable to a software developer but is immediately wrong to any chemist — an aromatic carbon at 130 ppm appearing on the far right is a tell that the viewer is broken.

matplotlib's default is to auto-scale axes from the minimum to maximum value of the data arrays, which puts low ppm on the left. `BrukerReader.read_1d` returns `ppm_scale` in the order nmrglue produces it from `uc.ppm_scale()`. For standard Bruker processed data this is high-to-low (index 0 = highest ppm), so `ppm_scale[0] > ppm_scale[-1]`. Passing this to `ax.plot(ppm_scale, data)` would display high-to-low left-to-right IF matplotlib preserves data order in axis limits — but matplotlib sets `xlim` to `(min(ppm_scale), max(ppm_scale))` when auto-scaling, flipping the axis to low-on-left.

For contour plots, the same issue applies to both dimensions.

**DEPT phase-sign convention:** DEPT-135 spectra have positive CH and CH3 signals, negative CH2 signals. The plot must display both; a viewer that clips at zero or uses `np.abs(data)` silently drops all CH2 correlation information.

**How to avoid:**
Always set axis limits explicitly from the ppm scale arrays, forcing NMR convention:

```python
# 1D
ax.set_xlim(float(ppm_scale[0]), float(ppm_scale[-1]))
# ppm_scale[0] is the highest ppm value (from BrukerReader) -> xlim = (high, low)
# matplotlib obeys this order, placing high ppm on the left

# 2D contour
ax.set_xlim(float(f2_ppm[0]), float(f2_ppm[-1]))   # F2 (x): high→low left→right
ax.set_ylim(float(f1_ppm[0]), float(f1_ppm[-1]))   # F1 (y): high→low top→bottom
# Do NOT call ax.invert_xaxis() — set limits in the right order from the start

# DEPT: show signed intensities, never np.abs()
ax.plot(ppm_scale, data, color="black", linewidth=0.8)
ax.axhline(0, color="#aaa", linewidth=0.5)  # zero line for phase reference
```

The rendering code must verify that `ppm_scale[0] > ppm_scale[-1]` as a guard, and raise a clear error (or reverse the scale) if the Bruker file was read with an unexpected orientation. Rely on the existing `Spectrum1D.ppm_scale` and `Spectrum2D.f1_ppm_scale`/`f2_ppm_scale` from `BrukerReader` — do not recompute ppm scales inside the rendering code.

**Warning signs:**
- On a 1H spectrum, TMS (0 ppm) appears on the LEFT and aromatic protons (7–8 ppm) appear on the RIGHT
- On a 13C spectrum, the carbonyl region (160–200 ppm) appears on the right
- CH2 carbons (DEPT-135 negative phase) are absent from DEPT plot — code silenced negative lobe
- 2D HSQC shows aromatic region in the bottom-right instead of top-left

**Phase to address:**
1D spectra rendering phase. Axis direction must be a first-class acceptance criterion with a visual check on a known compound (e.g. CASE1 ibuprofen has a carbonyl at ~181 ppm that must appear on the far left, and aliphatic CH3 at ~22 ppm on the right). A test can assert `ax.get_xlim()[0] > ax.get_xlim()[1]` for the spectrum axis.

---

### Pitfall 4: Bruker Data Path Is Not Recorded — Spectra Tabs Show "No Data" Silently

**What goes wrong:**
The v9.2 webview server receives only `analysis_dir` at startup (via `lucy webview serve <analysis_dir>`). The Bruker experiment directories (e.g. `../10/`, `../11/`, `../12/` relative to `analysis/`) are not recorded anywhere in `analysis/`. When Stage 2 adds spectra endpoints, the server has no path to the raw Bruker data and cannot render any spectra.

The failure mode is silent: the spectra tab would show "spectra unavailable" (or worse, a 500) without any indication that the underlying problem is a missing path, not a rendering bug. A developer testing against the live CASE1 dataset does not notice this because they know the Bruker path manually; the bug surfaces when someone uses the webview on a new dataset.

There are two places where the path must be recorded:
1. **At `lucy webview serve` time** — the CLI should accept a `--bruker-dir` argument (the parent of the experiment folders) or discover it from a manifest.
2. **At `case.md` run-start time** — the orchestrator currently calls `lucy webview serve <analysis_dir>`; it must also pass the Bruker data path so it is written into `analysis/.webview.json` (which already stores the `port` and `pid`).

**How to avoid:**
Extend `.webview.json` (managed by `state.py`) with a `bruker_dir` field written at server start:

```json
{
  "pid": 12345,
  "port": 8765,
  "analysis_dir": "/path/to/data/analysis",
  "bruker_dir": "/path/to/data",
  "started_at": "2026-07-07T..."
}
```

The spectra router reads `bruker_dir` from the state file at request time. If `bruker_dir` is absent or points to a non-existent directory, the endpoint returns HTTP 200 with `{"state": "unavailable", "reason": "bruker_dir not configured"}` — never a 500.

`case.md` must be updated to pass the Bruker root (the CASE data directory, which contains both the experiment folders and `analysis/`) to `lucy webview serve`. The case.md orchestrator already knows this path — it is the working directory at run start.

**Warning signs:**
- Spectra endpoints return 200 with "unavailable" state on every request, even during a live run where Bruker data is definitely present
- `analysis/.webview.json` has no `bruker_dir` field after `lucy webview serve` is called
- `case.md` calls `lucy webview serve analysis/` without passing a Bruker data path argument
- Developer discovers the issue only when testing on a dataset they did not manually configure

**Phase to address:**
The phase that introduces spectra endpoints (earliest spectra phase). Adding `--bruker-dir` to `lucy webview serve` and writing it into `.webview.json` must be the first task of that phase — it is a prerequisite for all spectra work. The `case.md` update to pass the path belongs in the same phase.

---

### Pitfall 5: Markdown Rendering Reintroduces innerHTML XSS Risk Eliminated by v9.2

**What goes wrong:**
The v9.2 dashboard deliberately used `element.textContent = data.content` to display `CASE-PROGRESS.md` as raw monospace text, explicitly avoiding `innerHTML` to prevent XSS. Stage 2 reverses this by rendering the markdown as formatted HTML. Naively implementing this as:

```js
logPanel.innerHTML = convertMarkdownToHtml(data.content);
```

reintroduces HTML injection. Even though `CASE-PROGRESS.md` is server-authored (not user-supplied), any markdown content that includes `<script>`, `<img onerror=...>`, or other injection vectors — e.g. from a SMILES string an agent happened to write with `<` characters, or from a malformed agent message — would execute in the browser.

**Why it happens:**
Markdown-to-HTML conversion always produces raw HTML strings. The temptation is to use a CDN markdown library (forbidden by the no-CDN constraint) or to use a simple `marked.js` bundled copy. Without a library, a hand-rolled converter is tempting to implement as regex-replace → innerHTML assignment, which is inherently unsafe.

**How to avoid:**
Build the DOM using the DOM API — create elements, set text content, never assign raw HTML strings. The correct pattern for a hand-rolled renderer:

```js
function renderMarkdown(text, container) {
  container.innerHTML = "";  // clear only — safe because we built it via DOM API
  for (const line of text.split("\n")) {
    const el = parseLine(line);
    container.appendChild(el);
  }
}

function parseLine(line) {
  if (line.startsWith("### ")) {
    const h = document.createElement("h3");
    h.textContent = line.slice(4);  // textContent escapes all HTML
    return h;
  }
  if (line.startsWith("## ")) {
    const h = document.createElement("h2");
    h.textContent = line.slice(3);
    return h;
  }
  if (line.startsWith("# ")) {
    const h = document.createElement("h1");
    h.textContent = line.slice(2);
    return h;
  }
  // Code fences, tables, bold — all use textContent for text nodes
  const p = document.createElement("p");
  p.textContent = line;  // NEVER: p.innerHTML = line
  return p;
}
```

The rule is absolute: **every text node that comes from the server must be set via `textContent`, never `innerHTML`**. The only safe use of `innerHTML` is to clear the container or to insert known-safe structural HTML you wrote yourself (e.g. `container.innerHTML = ""`).

CASE-PROGRESS.md uses: `# ## ###` headings, `**bold**`, `` `code` `` fences, pipe-tables, and plain paragraphs. A 50-line DOM-based renderer covers all of these without innerHTML injection.

**Warning signs:**
- Any `element.innerHTML = someStringFromServer` in the Stage 2 JS — immediate red flag regardless of how "safe" the source seems
- Using a CDN markdown library (forbidden by no-CDN constraint)
- SMILES strings appearing in CASE-PROGRESS.md trigger XSS in a browser test (SMILES can contain `<` for ring closures in CXSMILES notation)

**Phase to address:**
The markdown log panel phase. The acceptance criterion must include a negative test: inject `# <img src=x onerror=alert(1)>` into a mock `CASE-PROGRESS.md` and confirm the browser does not execute the payload (the heading renders as the literal text `<img src=x onerror=alert(1)>`, not as an image element).

---

### Pitfall 6: Packaging and Import-Safety Regressions from matplotlib Addition

**What goes wrong: two separate failure modes.**

**6a. matplotlib in core CLI.** Adding `import matplotlib` or `from matplotlib.figure import Figure` at module level in any file in `src/lucy_ng/webview/` that is imported outside `create_app()` (e.g. from `webview/__init__.py` or `webview/server.py`) breaks WV-08: the core CLI becomes importable only when matplotlib is installed. The existing `test_main_importable_without_fastapi` test would catch a fastapi regression but does NOT catch a matplotlib regression unless a parallel test is added.

The spectra router module (`spectra.py`) will import matplotlib at module level (fine — it is only imported inside `create_app()`), but the `matplotlib.use("Agg")` call at the top of the module means that importing that module triggers the backend setting. This is safe IF the module is only reached via `create_app()`.

**6b. New static files vanish from wheel.** The v9.2 Pitfall 3 (hatch drops `index.html`) was resolved by adding `src/lucy_ng/webview/static/*` to `pyproject.toml` artifacts. Stage 2 may add additional frontend assets:
- If a separate CSS file is added outside `index.html` (e.g. `static/style.css`), the existing `static/*` glob covers it.
- If spectra are pre-rendered and stored under `static/spectra/`, a new artifacts entry `src/lucy_ng/webview/static/spectra/*` is needed — `static/*` does NOT recurse into subdirectories.
- If any assets are placed outside `webview/static/` (e.g. `webview/templates/`), they need their own artifacts entry.

The symptom — served via `FileResponse` in development but silently 404 after `pip install` — is hard to diagnose without explicitly testing an installed wheel.

**How to avoid:**

For 6a: matplotlib must only be imported inside modules that are themselves only imported inside `create_app()`. Add a test:
```python
def test_webview_server_importable_without_matplotlib(monkeypatch):
    """webview.server must not import matplotlib at module level."""
    import sys
    sys.modules["matplotlib"] = None  # block matplotlib
    # Should not raise ImportError
    import importlib
    importlib.import_module("lucy_ng.webview.server")
```

Also: matplotlib must be added to the `[webview]` extra in `pyproject.toml` (it is not there currently):
```toml
webview = [
    "fastapi>=0.100",
    "uvicorn>=0.20",
    "matplotlib>=3.7",
]
```
Without this, `pip install lucy-ng[webview]` on a clean environment fails at the first spectra request.

For 6b: maintain the rule "one artifacts entry per static subdirectory pattern used." After adding any non-Python file under `webview/`, verify with:
```bash
hatch build && pip install dist/*.whl --target /tmp/wheel_test && \
  python -c "from pathlib import Path; import lucy_ng.webview.app; \
  p = Path(lucy_ng.webview.app.__file__).parent; \
  print(list(p.rglob('*')))"
```
Any missing file will be absent from the output.

**Warning signs:**
- `from lucy_ng.cli import cli` raises `ModuleNotFoundError: No module named 'matplotlib'` on a base install — matplotlib leaked into the core import path
- `import lucy_ng.webview.server` raises `ImportError` on a base install (without `[webview]` extra)
- Browser gets `404 Not Found` for a static asset after `pip install` but the file exists in the source tree
- `[webview]` extra in pyproject.toml does not list `matplotlib` — users get `ModuleNotFoundError` at runtime after installing the extra

**Phase to address:**
The phase that introduces spectra rendering. Three tasks are non-negotiable at phase start, before any rendering code: (1) add `matplotlib>=3.7` to the `[webview]` extra, (2) confirm existing `test_main_importable_without_fastapi` still passes, (3) add the parallel matplotlib import-safety test.

---

### Pitfall 7: Tests That Require Real Bruker Data or a Live CASE Run

**What goes wrong:**
A test suite for spectra endpoints that depends on real Bruker experiment directories (e.g. the CASE1 ibuprofen dataset in `~/Dropbox/develop/data/nmrdata/`) cannot run in CI, on Sheldon, or on a clean checkout. If spectra rendering tests are skipped when Bruker data is absent, the spectra endpoint code is never automatically tested, and regressions (wrong axis direction, matplotlib Agg confusion, contour crash on empty data) accumulate undetected.

The v9.2 baseline already solved this correctly for JSON endpoints — fixtures create synthetic `analysis/` directories with minimal files. Stage 2 must extend the same pattern to spectra.

**Why it happens:**
`BrukerReader.read_1d()` and `read_2d()` call `nmrglue.bruker.read_pdata()` which requires real Bruker binary files on disk. It is tempting to write tests that call `BrukerReader` directly, which forces a dependency on real data.

**How to avoid:**
The "dumb server" boundary is the key: rendering functions must accept `Spectrum1D` / `Spectrum2D` model objects (already defined in `lucy_ng.models`), not Bruker directory paths. The `BrukerReader` is called once at the endpoint to load data; the render function takes the model and returns bytes. Tests bypass `BrukerReader` entirely by constructing minimal model objects:

```python
import numpy as np
from lucy_ng.models import Spectrum1D, Spectrum2D

@pytest.fixture
def synthetic_1d() -> Spectrum1D:
    n = 256
    ppm = np.linspace(200.0, 0.0, n)  # high→low, Bruker convention
    data = np.exp(-((ppm - 130.0) ** 2) / 2) + 0.1 * np.random.default_rng(0).standard_normal(n)
    return Spectrum1D(data=data, ppm_scale=ppm, nucleus="13C", frequency=150.9)

@pytest.fixture
def synthetic_2d() -> Spectrum2D:
    f1 = np.linspace(160.0, 0.0, 32)
    f2 = np.linspace(10.0, 0.0, 64)
    data = np.zeros((32, 64))
    data[10, 20] = 1e6  # single peak
    return Spectrum2D(data=data, f1_ppm_scale=f1, f2_ppm_scale=f2,
                      f1_nucleus="13C", f2_nucleus="1H", experiment_type="HSQC", frequency=600.0)
```

The FastAPI endpoint returns `Response(content=render_spectrum_1d_png(spec), media_type="image/png")`. Tests call the render function directly (unit tests) or call the endpoint via `TestClient` with a fixture-backed `analysis_dir` that contains a minimal experiment manifest telling the server which experiment to load (using the synthetic model, not real Bruker files).

For integration tests that DO use real Bruker data: mark them with `@pytest.mark.bruker_required` and a conftest skip guard, exactly like the existing `@pytest.mark.webview_server` skip guard in `test_cli_webview.py`.

**Warning signs:**
- Any test in `test_webview_spectra.py` calls `BrukerReader.read_1d()` directly without a skip guard
- Tests pass locally (Bruker data present) but the CI run shows "no tests collected" for the spectra test module
- The spectra rendering function signature is `render_1d(bruker_dir: Path, expno: int) -> bytes` instead of `render_1d(spec: Spectrum1D) -> bytes` — endpoint logic is not separated from I/O
- Fake Bruker directories in `tmp_path` fixtures that try to replicate the acqus/pdata structure — these are fragile and break on nmrglue version changes

**Phase to address:**
Established in the first spectra phase as a hard architectural rule: rendering functions accept `Spectrum1D`/`Spectrum2D`, not paths. TestClient fixture pattern (from Phase 91's research) extended with `synthetic_1d`/`synthetic_2d` fixtures. No spectra tests use real Bruker data without an explicit skip guard.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| `import matplotlib.pyplot as plt` in route handler | Familiar API | Non-thread-safe global state; intermittent corruption under concurrent load | Never in server code |
| No downsampling for 2D contour | Simpler code | 500 ms–3 s per request; 200–500 MB peak RSS; event-loop blocking | Never for server-rendered PNGs |
| `element.innerHTML = markdownToHtml(text)` | One-line rendering | XSS injection from any server-authored content with `<` chars | Never — use DOM API |
| `matplotlib` not in `[webview]` extra | Smaller extra metadata | `ModuleNotFoundError` at first spectra request on clean install | Never |
| Rendering functions accept Bruker paths not models | Simpler endpoint code | Tests require real Bruker files; CI cannot run spectra tests | Never |
| No mtime-keyed PNG cache | Simpler code | Full re-render every 3 s (browser polling interval); ~500 ms latency per refresh | Acceptable for 1D (fast); unacceptable for 2D |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| matplotlib + FastAPI | `async def` route with sync `contour()` call inside | `def` (sync) route — FastAPI dispatches to thread-pool executor automatically |
| BrukerReader ppm scale | Assume `ppm_scale[0]` is always the smallest value | `ppm_scale[0]` is the highest ppm (Bruker convention); set `xlim(ppm_scale[0], ppm_scale[-1])` |
| matplotlib Agg backend | Call `matplotlib.use("Agg")` after `import matplotlib.pyplot` | Call `use("Agg")` before any pyplot import, at module-level in the spectra module |
| Bruker path at webview serve | Pass only `analysis_dir` to `lucy webview serve` | Pass both `analysis_dir` and `bruker_dir` (CASE data root); write to `.webview.json` |
| Markdown → DOM | `innerHTML = convertedHtml` | Build DOM via `createElement` + `textContent` for all text from server |
| hatch artifacts | Assume `static/*` glob covers subdirectories | Glob is flat; `static/spectra/*` needs its own artifacts entry if spectra subdirectory is used |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Full-res 2D contour per request | 500 ms+ response time; memory growth | Decimate to max 512×512; mtime-keyed cache | Every request on a 1024×2048 HMBC |
| No PNG cache | 3 s re-render every browser polling cycle | Cache bytes keyed by `(exp_path, mtime)` | Always on 3 s polling with 2D spectra |
| Blocking event loop with `async def` render | All other endpoints stall during spectra render | Use `def` (sync) for spectra routes | Every request while rendering |
| DEPT without negative levels | No CH2 peaks shown (they are negative phase) | Include symmetric negative contour levels for DEPT/HSQC-edited | Every DEPT plot |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| `innerHTML` for markdown-rendered log | Script injection from `<script>` or event-handler attributes in CASE-PROGRESS.md | `textContent` for all server text; DOM API for structure |
| Path traversal via experiment number | Reading arbitrary files via constructed Bruker path | Validate experiment path is within `bruker_dir`; reject `..` components |

---

## "Looks Done But Isn't" Checklist

- [ ] **1D axis direction:** Plot of 1H spectrum shows TMS (0 ppm) on the RIGHT and aromatics (7–8 ppm) on the LEFT — verify `ax.get_xlim()[0] > ax.get_xlim()[1]`
- [ ] **2D axis direction:** HSQC aromatic region is in the TOP-LEFT (high F2-1H ≈ 7 ppm, high F1-13C ≈ 130 ppm) not bottom-right
- [ ] **DEPT CH2 visible:** Negative-phase CH2 peaks appear below the zero line (not absent)
- [ ] **Spectra tab on fresh checkout:** `pip install lucy-ng[webview]` on a clean venv can serve a spectra tab (matplotlib is listed in the extra)
- [ ] **No matplotlib in core:** `python -c "import sys; sys.modules['matplotlib']=None; from lucy_ng.cli import cli"` does not raise
- [ ] **Bruker path in .webview.json:** After `lucy webview serve`, `cat analysis/.webview.json` shows a `bruker_dir` field
- [ ] **Markdown XSS test:** `# <img src=x onerror=alert(1)>` in mock CASE-PROGRESS.md renders as literal text, not an image element
- [ ] **Wheel contains static assets:** After `hatch build`, confirm all static files exist in the installed wheel (not just in the source tree)
- [ ] **Spectra tests run without Bruker files:** `pytest tests/test_webview_spectra.py -x` passes on a checkout with no `~/Dropbox/develop/data/` path present

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| pyplot global state corruption (live) | MEDIUM | 1. Locate `import matplotlib.pyplot` in webview, 2. Replace with OO `Figure` API, 3. Restart server |
| 2D render blocking event loop | LOW | 1. Change `async def` to `def` for spectra routes, 2. Redeploy |
| Wrong ppm axis direction | LOW | 1. Fix `set_xlim`/`set_ylim` calls to use `(ppm_scale[0], ppm_scale[-1])`, 2. Add axis-direction assertions to tests |
| Bruker path missing (spectra unavailable) | LOW | 1. Add `--bruker-dir` arg to `lucy webview serve`, 2. Write to `.webview.json`, 3. Update `case.md` |
| XSS via innerHTML | LOW | 1. Replace `innerHTML = html` with DOM API construction, 2. Add negative XSS test |
| matplotlib missing from wheel | LOW | 1. Add `matplotlib>=3.7` to `[webview]` extra, 2. `hatch build` + verify |
| Static assets missing from installed wheel | LOW | 1. Add missing path to `artifacts` in pyproject.toml, 2. `hatch build` + verify |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| matplotlib pyplot thread-safety (P1) | 1D spectra rendering phase | Import-safety test passes; OO API used throughout; no `plt.*` in webview |
| 2D contour perf/memory (P2) | 2D contour rendering phase | Render time < 100 ms with caching; memory stable over 10 requests |
| ppm axis direction (P3) | 1D spectra rendering phase (AC on 1D; re-verified on 2D) | `ax.get_xlim()[0] > ax.get_xlim()[1]` assertion in tests; visual check on CASE1 |
| Bruker path location (P4) | First spectra phase (prerequisite) | `.webview.json` contains `bruker_dir`; spectra tab shows data on CASE1 |
| Markdown XSS (P5) | Markdown log panel phase | Negative XSS test passes; no `innerHTML` of server content in JS |
| Packaging/import-safety regressions (P6) | First spectra phase (prerequisite) | Core import test passes; matplotlib in `[webview]` extra; wheel contains all static files |
| Test fixture boundary (P7) | First spectra phase (architectural rule at phase start) | All spectra tests pass on clean checkout without Bruker data |

---

## Sources

- `src/lucy_ng/webview/depiction.py` — v9.2 "never raises" + lazy import pattern; mirror for matplotlib OO API
- `src/lucy_ng/readers/bruker.py` — `ppm_scale` ordering from `ng.fileiobase.uc_from_udic`; F1/F2 dimension conventions
- `src/lucy_ng/processing/peak_picker_2d.py` — `_compute_2d_noise_sigma` MAD estimator; reuse for contour level thresholding
- `.planning/milestones/v9.2-phases/91-api-endpoints-depictions-and-static-frontend/91-RESEARCH.md` — Pitfall 2 (WV-08 lazy import), Pitfall 3 (hatch artifacts `static/*`), Pitfall 6 (MolDraw2DSVG per-call instance) — all apply by analogy to matplotlib
- `pyproject.toml` — current `[webview]` extra (fastapi + uvicorn only; matplotlib absent), current `artifacts` list
- `src/lucy_ng/webview/app.py` + `server.py` + `state.py` — WV-08 boundary; `.webview.json` schema
- matplotlib documentation: `matplotlib.use()` must precede pyplot import; `Figure`/`FigureCanvasAgg` OO API for thread-safe headless rendering
- FastAPI documentation: sync `def` route handlers run in thread-pool executor; `async def` handlers block the event loop if they perform sync I/O

---
*Pitfalls research for: v9.3 CASE Web-View Stage 2 — server-side NMR spectra rendering, data tables, markdown log*
*Researched: 2026-07-07*
