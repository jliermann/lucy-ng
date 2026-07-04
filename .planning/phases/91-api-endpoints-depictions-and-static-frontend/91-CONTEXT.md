# Phase 91: API Endpoints, Depictions, and Static Frontend - Context

**Gathered:** 2026-07-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Opening the dashboard URL in a browser shows three auto-refreshing widgets —
**run status**, **top candidate structures** (RDKit SVG depictions with MAE/rank),
and the **scrollable run log** — with **graceful degradation** while a CASE run is
still live and source files are missing, empty, or mid-write.

Delivered in this phase:
- Three JSON API endpoints docked onto the existing `create_app()` factory via
  `app.include_router()`: `GET /api/status`, `GET /api/log`, `GET /api/structures`
  (plus the depiction endpoint `GET /api/structure/{i}.svg`).
- RDKit SVG depiction rendering for candidate SMILES.
- A vanilla-JS static frontend (`GET /`) that auto-refreshes every ~3 s with **no
  JS build step**.
- `pyproject.toml` `[tool.hatch.build.targets.wheel]` `artifacts` entry for
  `src/lucy_ng/webview/static/*` (Phase 90 deliberately left this untouched).

**Out of scope (own phases):** orchestrator integration / auto-launch from
`case.md` (Phase 92, WV-07); any change to the server lifecycle, CLI, or packaging
extra (Phase 90, done).

**Locked from Phase 90 (do NOT re-decide):** FastAPI + uvicorn; server is "dumb"
(reads files only, no compute beyond trivial arithmetic); bind `127.0.0.1` only;
routers docked via `app.include_router()`; static assets under
`src/lucy_ng/webview/static/`; Swagger/ReDoc suppressed. The webview package must
stay fastapi-free outside `app.py` (WV-08 import-safety) — routers/depiction code
that import fastapi/RDKit live in modules only reached through `app.py`.
</domain>

<decisions>
## Implementation Decisions

### Live status derivation (`GET /api/status`, WV-03 / WV-06)
- **D-01:** Derive iteration + active phase + elapsed time from `analysis/timing.jsonl`
  as the **primary** source (append-only, exists during a live run — `timing.json`
  only appears at run end). Active phase = the last `phase_start` event with no
  matching `phase_end`. Iteration number = parsed from the phase name (e.g.
  `lsd-iteration-03` → iteration 3).
- **D-02:** **Fallback** to parsing `analysis/CASE-PROGRESS.md` headers
  (`## Iteration N`, `### <Agent>`) when `timing.jsonl` is missing or empty, so the
  status widget still works if timing instrumentation lags.
- **D-03:** **Elapsed time is computed server-side** as `now − run_start` on each
  request while the run is live; once `run_end` (or the finalized `timing.json`)
  exists, freeze to the final `total_duration_s`. This trivial subtraction is within
  the "dumb server" boundary.
- **D-04:** When no data at all is available, return a well-formed **"waiting for
  data"** payload with HTTP 200 (never 500).

### Structures source & fallback (`GET /api/structures`, WV-04 / WV-06)
- **D-05:** Before any ranking exists (only `analysis/iteration_NN/solutions.smi`
  present), surface candidates from the **newest** `iteration_NN/` `solutions.smi`
  with `rank=null`, `mae=null`, and a `source="unranked"` marker — the user sees
  candidates during the run.
- **D-06:** Once `analysis/ranking_results.json` exists, switch to the **ranked**
  list (rank + MAE + quality per the `lucy lsd rank --format json` schema:
  `rank`, `solution_index`, `smiles`, `mae`, `quality`).
- **D-07:** Cap the list at **~10** ("best ~10"). Ranked → top 10 by rank. Unranked
  → first 10 in file order (no MAE available to sort by). Expose a total count so the
  frontend can indicate there are more.
- **D-08:** Missing/empty solutions → "waiting for data" payload (HTTP 200).

### SVG depiction (`GET /api/structure/{i}.svg`, WV-04 / WV-06)
- **D-09:** **Clean publication-style** 2D depiction, ~300×300 px, **no atom
  numbers/indices**. Rank + MAE are shown as an **HTML label around the tile** by the
  frontend, not baked into the SVG.
- **D-10:** Render **on-demand** per request; **no server-side cache** (keeps the
  server dumb; RDKit render is cheap). The **frontend** re-requests an SVG only when
  the SMILES at that index changed between `/api/structures` polls → no flicker on
  the 3 s refresh.
- **D-11:** A malformed SMILES renders as a **placeholder SVG** (that one entry only);
  all other entries render correctly (WV-06 / SC #5). An **out-of-range index → HTTP
  404** (SC #4).

### Run log (`GET /api/log`, WV-05)
- **D-12:** Endpoint returns the **raw** current content of
  `analysis/CASE-PROGRESS.md` (text/JSON payload per SC #2 — no server-side markdown
  rendering).
- **D-13:** Frontend renders it as **raw monospace** in a scrollable `<pre>` panel.
  **Auto-scroll to bottom only when the user is already at the bottom**; if the user
  has scrolled up, preserve their position across refreshes.

### Frontend design & layout (WV-06)
- **D-14:** **Single `src/lucy_ng/webview/static/index.html`** with **inline CSS +
  JS** — no build step, minimal asset surface (one file to add to hatch artifacts).
  Light theme, clean/functional (system fonts, subtle cards/borders).
- **D-15:** **Auto-refresh every ~3 s** (SC #6) by polling the three JSON endpoints;
  no websockets.

### Claude's Discretion
- **Exact widget arrangement** — user said "Du entscheidest". Default intent: a slim
  status bar on top, and below it two columns (structure grid left, scrollable log
  right); collapse to stacked on narrow windows. Free to adjust for a clean result.
- Placeholder-SVG visual style, exact tile grid sizing, precise "waiting for data"
  payload field names, and error copy — pick sensible, consistent values.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` §"Phase 91" — goal, 6 success criteria, and the hatch
  `artifacts` note for `static/*`.
- `.planning/REQUIREMENTS.md` — WV-03, WV-04, WV-05, WV-06 (this phase); WV-07/WV-08
  for boundary awareness.
- `.planning/phases/90-server-cli-and-packaging/90-RESEARCH.md` — locked stack
  (FastAPI/uvicorn optional extra, no JS build, bind 127.0.0.1), the app-factory /
  `include_router` pattern, recommended structure, and **Pitfall 6** (hatch static
  artifacts — the direct prerequisite for this phase's pyproject change).

### Existing webview code (Phase 90, extend — do not rewrite)
- `src/lucy_ng/webview/app.py` — `create_app(analysis_dir)`; dock routers here.
  Note the module-level rule: only `app.py` may import fastapi.
- `src/lucy_ng/webview/state.py` — `WebviewState` model + `.webview.json` I/O.
- `src/lucy_ng/webview/server.py` — lifecycle (serve/stop/status).

### Data-source formats (read to match schemas exactly)
- `.claude/commands/lucy-ng/case.md` §"timing" (~lines 315–351) — how
  `analysis/timing.jsonl` events and the finalized `analysis/timing.json`
  (`run_start_utc`, `run_end_utc`, `total_duration_s`, `phases[]`) are produced.
- `src/lucy_ng/cli/lsd.py` (`_perform_ranking`, ~lines 283–315) — the exact
  `ranking_results.json` schema (`solutions[].rank/solution_index/smiles/mae/quality/...`).
- `.claude/agents/lucy-solution-analyst.md` — writer of
  `analysis/ranking_results.json` + `analysis/final_results.md`; input
  `analysis/iteration_NN/solutions.smi`.
- `.claude/commands/lucy-ng/references/progress-format.md` — `CASE-PROGRESS.md`
  structure (header, `## Setup`, `## Iteration N`, `### <Agent>` sections) for the
  fallback parser.

### Packaging
- `pyproject.toml` — `[tool.hatch.build.targets.wheel]` `artifacts` (add
  `src/lucy_ng/webview/static/*`) and the `[webview]` optional-dependencies extra.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `create_app(analysis_dir)` already resolves `analysis_dir` and exposes
  `GET /health` — the router modules receive the analysis dir the same way (closure
  or dependency) and just read files under it.
- `lucy lsd rank --format json` already produces the exact structure schema needed
  for `/api/structures` — reuse the field names verbatim from
  `ranking_results.json` rather than inventing new ones.
- RDKit is already a core dependency (used across prediction/dereplication) — SVG
  depiction can import it without adding to the `[webview]` extra, but the importing
  module must only be reached via `app.py` to preserve WV-08 import-safety.

### Established Patterns
- Import-safety invariant: webview package stays fastapi-free except `app.py`.
  New router/depiction modules that import fastapi or RDKit must only be imported
  from inside `create_app()` (lazy), never at package import time.
- All CLI commands support `--format json`; the JSON schemas there are the source of
  truth for API payload shapes.

### Integration Points
- `app.include_router(...)` calls added inside `create_app()` after the `/health`
  route (Phase 90 left a comment marking this spot).
- New static dir `src/lucy_ng/webview/static/` served at `GET /` — requires the
  `pyproject.toml` hatch `artifacts` change or it will be dropped from the wheel
  (Pitfall 6).
</code_context>

<specifics>
## Specific Ideas

- The whole point of the graceful-degradation work is the **live run**: at the moment
  the dashboard is most useful, `timing.json`, `ranking_results.json`, and
  `final_results.md` do NOT yet exist — only `timing.jsonl` and
  `iteration_NN/solutions.smi`. Every endpoint's primary path must assume the
  final-artifact files are absent and degrade to the append-only / per-iteration
  sources. This is the design center, not an edge case.
- "waiting for data" is always HTTP 200 with a well-formed payload; only an
  out-of-range SVG index is a 404. Never surface a 500 from missing/partial files.
</specifics>

<deferred>
## Deferred Ideas

- Markdown-rendered log panel (headings/tables) — rejected for this phase to keep the
  single-file, no-build, no-inlined-library constraint; could be revisited if the raw
  log proves hard to read.
- Dark-mode toggle / separate css+js assets — deferred; light single-file dashboard
  is enough for the CASE run monitor use case.
- Atom-numbered depictions for HMBC-assignment debugging — deferred; the dashboard is
  a monitor, not a structure-verification tool.

None of these are new capabilities within the phase scope — discussion stayed within
Phase 91's boundary.
</deferred>

---

*Phase: 91-api-endpoints-depictions-and-static-frontend*
*Context gathered: 2026-07-04*
