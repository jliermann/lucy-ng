# Feature Research

**Domain:** CASE run monitor — v9.3 Web-View Stage 2 (spectra tabs, data tables, formatted log)
**Researched:** 2026-07-07
**Confidence:** HIGH — all findings based on direct inspection of existing codebase, analysis/ artefacts from real CASE runs (CASE1 ibuprofen), and established NMR display conventions

---

## Context: What v9.2 Already Delivers (Do Not Re-Research)

The existing dashboard at `GET /` exposes three auto-refreshing panels:
- Status bar: run state, iteration, active phase, elapsed time (`/api/status`)
- Structure grid: top-10 ranked candidates with RDKit SVG depiction + MAE/rank (`/api/structures`, `/api/structure/{i}.svg`)
- Raw log panel: `CASE-PROGRESS.md` verbatim in a scrollable `<pre>` (`/api/log`)

Architecture constraints carried forward into Stage 2:
- Single-file `index.html` with inline JS/CSS, no build step, no node toolchain
- FastAPI `app.include_router()` pattern; new routers dock into `create_app(analysis_dir)`
- Server is "dumb" — reads `analysis_dir` files only, no agent knowledge, no live-run dependency
- WV-08 import-safety: fastapi and RDKit only reachable via `app.py` (new matplotlib follows same rule)
- Graceful degradation: missing/partial files → HTTP 200 "waiting", never 500
- 3 s polling retained; tabs dock without a rewrite (design spec guarantees this)

---

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Formatted run log** — render CASE-PROGRESS.md as markdown | The CASE agent team writes structured markdown: `## Iteration N`, `### NMR-Chemist`, bold conclusions, code fences, tables. Viewing this as raw `#`/`**` in a `<pre>` is the v9.2 explicitly deferred default. The trigger was met on the live CASE1 run. A chemist watching a live run expects readable structure. | LOW | Pure frontend change. `GET /api/log` already returns the content unchanged. Add `marked.js` via CDN (`<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js">`) and swap the `<pre>` for a `<div id="log">` rendered with `marked.parse(content)`. No new endpoint needed. Auto-scroll-to-bottom behaviour unchanged (already in v9.2 D-13). |
| **Tab navigation** — Overview / Spectra / Tables / Log | With four feature groups the single-panel layout no longer fits. Tab switching is the expected navigation pattern for any dashboard with multiple data views. The design spec explicitly says "tabs dock in without a rewrite." | LOW | Pure frontend CSS show/hide (`display:none`/`block`) with a tab-bar. No new endpoints. The Overview tab contains the existing v9.2 status bar + structure grid unchanged. |
| **¹³C peak list table** — ppm, multiplicity, nH, nC, assignment | The signal table is the primary chemist-facing CASE artefact. After a run the first question is: "did peak picking capture all signals correctly?" A table is the canonical format. Missing this means the inspector has no way to verify NMR input. | LOW | `analysis/peaks/carbon_signals.json` is written by the CASE team with all needed columns (`ppm`, `mult`, `nC`, `assignment`, `confidence`). New endpoint `GET /api/peaks/c13` reads and serves it as JSON. Frontend renders as an HTML table. Graceful degrade when file absent. |
| **HMBC correlation table** — C ppm, H ppm, flag | The HMBC flag column (`ok` / `1J_artifact` / `potential_4J`) is exactly what a chemist checks to understand which correlations drove the structure and which were deferred. This is the key CASE reasoning artefact. | LOW | `analysis/peaks/hmbc.json` is written by the CASE team with `carbon_ppm`, `proton_ppm`, `intensity`, `flag`. New endpoint `GET /api/peaks/hmbc`. Flag column must be colour-coded in the frontend (green=ok, amber=1J_artifact, red=potential_4J). |
| **¹³C bar chart** — stick spectrum with reversed ppm axis | A bar/stick chart of ¹³C signals is the standard CASE run summary display. Without a reversed ppm axis the display is scientifically wrong: NMR convention is high ppm (downfield) on the left, 0 ppm on the right. Bars coloured by multiplicity aid immediate reading. | MEDIUM | Generate server-side via matplotlib from `carbon_signals.json` peak data (NOT from raw Bruker FID — see Anti-Features). `matplotlib` added to `[webview]` optional extra. New endpoint `GET /api/spectra/c13.svg` renders to SVG and returns it as `image/svg+xml`. Axis: 220 ppm left → 0 ppm right (`ax.invert_xaxis()`). Bars coloured by mult: Cq grey, CH blue, CH2 orange, CH3 green. Label each bar with its ppm value. |
| **HSQC scatter** — ¹H (x, reversed) vs ¹³C (y, reversed) | The HSQC scatter is the minimum meaningful 2D display. A chemist expects F2 (¹H, direct) on x-axis and F1 (¹³C) on y-axis, both axes reversed (high ppm at left/top). Swapping these is a domain-correctness error. | MEDIUM | `analysis/peaks/hsqc.json` provides `carbon_ppm`, `proton_ppm`, `intensity`, `one_bond`. Server-side matplotlib scatter. New endpoint `GET /api/spectra/hsqc.svg`. Mark `one_bond=True` peaks with a distinct colour/marker. Axis ranges from peak data + margin. `ax.invert_xaxis()` + `ax.invert_yaxis()`. Reuses matplotlib already added for ¹³C chart. |
| **HMBC scatter** — with flag colouring | The HMBC scatter coloured by flag (`ok` / `1J_artifact` / `potential_4J`) shows at a glance which cross-peaks drove the structure search and which were set aside. This is as important as the table. | MEDIUM | Same approach as HSQC from `hmbc.json`. New endpoint `GET /api/spectra/hmbc.svg`. Legend required. Flag colours match the table: green/amber/red. Reuses matplotlib. |
| **LSD constraint inventory display** | The constraint inventory (MULT count, HMBC batches applied vs deferred, BOND constraints, pending items) is what was actually sent to the solver. Showing it closes the loop from "what peaks exist" to "what the solver received." | MEDIUM | The constraint inventory JSON block is embedded in `analysis/iteration_NN/compound.lsd` headers between `=== CONSTRAINT INVENTORY ===` markers. New endpoint `GET /api/constraints` reads the latest `iteration_NN/` directory (alphabetically last), extracts and parses the JSON block, and serves it. Frontend renders a summary: MULT count, HMBC batches, BOND list, applied vs deferred bullets. Graceful degrade when no LSD file exists yet. |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **DEPT sub-tab** — signed bar chart (positive CH/CH3, negative CH2) | DEPT-135 phase information is lost in a plain ¹³C listing. Showing signed bars makes CH2 immediately identifiable, which is the analytical purpose of DEPT. This turns the ¹³C display from informational to diagnostic. | MEDIUM | Conditional: only render if `multiplicity_edited` field in `hsqc.json` is `true` (DEPT-guided HSQC was used). Otherwise the Spectra > 1D panel shows only the ¹³C tab. Bars: CH/CH3 positive (blue/green), CH2 negative (orange), Cq absent. Source: multiplicity field from `carbon_signals.json`. No new endpoint — same `GET /api/peaks/c13` data, different render flag. |
| **COSY scatter** — ¹H–¹H connectivity | Completes the 2D picture. Chemists verifying connectivity expect to see all three 2D experiments: HSQC, HMBC, COSY. | MEDIUM | `analysis/peaks/cosy.json` exists (confirmed from CASE1). Both axes ¹H reversed. Square plot; diagonal visible. New endpoint `GET /api/spectra/cosy.svg`. Reuses matplotlib. Low incremental effort once HSQC/HMBC are implemented. |
| **Constraint inventory "applied vs deferred" detail** | Side-by-side rendering of `applied_from_detection` and `pending_from_detection` lists directly shows the agent's reasoning about trusted vs held-back evidence. This is unique to the lucy-ng CASE inspector — no other CASE tool exposes this level of solver-input transparency. | LOW | Already in the constraint inventory JSON block — no extra endpoint beyond `GET /api/constraints`. Just needs appropriate frontend layout (two-column list or colour-coded rows). |
| **HSQC correlation table** | Completes the Tables view alongside ¹³C and HMBC. A chemist doing detailed post-run verification wants the direct C–H assignments in tabular form. | LOW | `analysis/peaks/hsqc.json` has `carbon_ppm`, `proton_ppm`, `matched_real_carbon`, `one_bond`. New endpoint `GET /api/peaks/hsqc`. Low incremental effort once ¹³C and HMBC tables are done. Defer to P2 — scatter covers the primary use case. |
| **Per-iteration constraint diff** | Shows how the LSD input changed between iterations (batch 1 → batch 2 HMBC added, new BOND constraints). Enables rapid multi-iteration review without reading individual LSD files. | HIGH | Requires reading all `iteration_NN/compound.lsd` files and diffing constraint inventory JSON blocks. Significant backend logic. Defer to a later milestone. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Full ¹H spectrum trace from raw Bruker FID** | "Looks like a real NMR spectrum" | Requires nmrglue + matplotlib + discovery of the Bruker data directory (which is the parent of `analysis/`, not always predictable). Solvent signals, shimming artefacts, phase correction must be handled. Adds nmrglue to `[webview]` extra (not currently there). The run monitor does not need the ¹H lineshape or multiplet pattern — it needs peak positions. | Show a stick chart of ¹H chemical shifts derived from `hsqc.json` proton_ppm values — sufficient for inspector purposes. |
| **Full 2D contour plots from raw Bruker data** | "Contour plots look like the real experiment" | Same Bruker-path-discovery problem as FID traces. Contour level selection is non-trivial (logarithmic, noise-floor dependent). Large 2D matrices are slow to render on each poll request. The scatter from already-picked peaks contains all information a run reviewer needs. | Scatter from peak JSON already recommended above. |
| **Interactive zoom/pan in spectra** | Chemists zoom in professional NMR tools | Requires a JS charting library (Plotly, Chart.js, D3) or htmx — either adds a build step or a CDN dependency substantially larger than marked.js. The dashboard is an inspector, not a full NMR processing tool. | Serve matplotlib SVGs at higher resolution (600×400 px); add a `download` button on each spectrum tile so chemists can open in their preferred tool. |
| **Editable peak lists or constraint editor** | "Would be useful to fix errors directly" | Violates the core v9.2 design principle: the view never mutates the run. Any write path risks corrupting active CASE run files. | The dashboard is a monitor. Corrections are made by re-running the CASE team with updated parameters. |
| **Raw COSY peak list table** | "Tables exist for ¹³C and HMBC, why not COSY?" | COSY tables are long and chemists do not read raw ¹H–¹H peak lists in tabular form — they trace connectivity in scatter plots. A 200-row table of ¹H–¹H pairs clutters the Tables tab without adding insight. | COSY scatter plot (differentiator above). |
| **SSE/WebSocket live push** | "Eliminate the 3 s polling lag" | Design spec explicitly deferred this: "no functional gain." Adds server-side complexity for a cosmetic improvement on a 20–120 min run where 3 s lag is imperceptible. | Keep 3 s polling. |
| **Server-side markdown rendering** | "Keep the frontend thin" | Requires a Python markdown library in the webview extra (e.g. `mistune`), adds a dependency and server processing for content that is already served verbatim. The frontend already receives the content — render it there. | CDN `marked.js` in the frontend; one `<script>` tag, no new backend dependency. |

---

## Feature Dependencies

```
[Tab navigation]
    └──required by──> [All Stage-2 panels]

[Formatted run log]
    └──reuses──> [GET /api/log (v9.2, unchanged)]
    └──requires──> [marked.js via CDN (frontend only)]

[matplotlib added to [webview] extra]
    └──required by──> [All spectra image endpoints]

[¹³C bar chart endpoint GET /api/spectra/c13.svg]
    └──requires──> [GET /api/peaks/c13 data]
    └──requires──> [matplotlib in [webview] extra]

[GET /api/peaks/c13]
    └──reads──> [analysis/peaks/carbon_signals.json]
    └──shared by──> [¹³C bar chart + ¹³C peak list table]

[DEPT sub-tab]
    └──requires──> [GET /api/peaks/c13 (same endpoint, same data)]
    └──conditional on──> [multiplicity_edited flag in analysis/peaks/hsqc.json]

[HSQC scatter GET /api/spectra/hsqc.svg]
    └──reads──> [analysis/peaks/hsqc.json]
    └──requires──> [matplotlib (shared)]

[HMBC scatter GET /api/spectra/hmbc.svg]
    └──reads──> [analysis/peaks/hmbc.json]
    └──requires──> [matplotlib (shared)]

[COSY scatter GET /api/spectra/cosy.svg]
    └──reads──> [analysis/peaks/cosy.json]
    └──requires──> [matplotlib (shared)]
    └──enhances──> [HMBC scatter — full 2D connectivity picture]

[¹³C peak list table]
    └──reuses──> [GET /api/peaks/c13 JSON]

[HMBC correlation table]
    └──requires──> [GET /api/peaks/hmbc (new JSON endpoint)]
    └──reads──> [analysis/peaks/hmbc.json]

[HSQC correlation table]
    └──requires──> [GET /api/peaks/hsqc (new JSON endpoint)]
    └──reads──> [analysis/peaks/hsqc.json]

[LSD constraint inventory GET /api/constraints]
    └──reads──> [latest analysis/iteration_NN/compound.lsd header block]
    └──requires──> [JSON block extraction from LSD file comments]
```

### Dependency Notes

- **matplotlib is the single new package dependency.** Add once to `[webview]` optional extra; all five spectra image endpoints share it. No other new package required.
- **`GET /api/peaks/c13` is shared.** The ¹³C bar chart image and the ¹³C peak list table use the same endpoint — one returns SVG, the other drives the HTML table from the same JSON.
- **DEPT sub-tab is conditional.** It only appears if `multiplicity_edited: true` in `hsqc.json`. If the condition is not met, the tab is hidden gracefully (no missing-data error).
- **LSD constraint inventory requires at least one `iteration_NN/compound.lsd`.** During the setup phase before iteration 1 the endpoint returns a "waiting" payload. The constraint inventory JSON block is in the file header comments — a simple regex extraction, not a full LSD parser.
- **Spectra images are served on-demand, no server-side cache** (same "dumb server" pattern as D-10 in Phase 91 for structure SVGs). matplotlib render is fast enough for a 3 s poll cycle.

---

## MVP Definition

### Launch With (v9.3 core)

Minimum viable feature set that delivers the "full run inspector" concept.

- [x] **Formatted run log** — renders the markdown structure agents write; immediately improves readability; zero new backend work
- [x] **Tab navigation** — prerequisite for all other panels; pure frontend CSS, no new endpoints
- [x] **¹³C peak list table** — answers "did peak picking work?"; LOW backend complexity
- [x] **HMBC correlation table with flag column** — answers "which correlations drove LSD?"; LOW backend complexity
- [x] **¹³C bar chart** — visual confirmation of signal count and multiplicity; MEDIUM (one new dep: matplotlib)
- [x] **HSQC scatter** — verifies direct C–H assignment; MEDIUM (reuses matplotlib)
- [x] **HMBC scatter** — shows which cross-peaks were flagged; MEDIUM (reuses matplotlib)
- [x] **LSD constraint inventory summary** — closes the loop: what exactly was sent to the solver; MEDIUM (LSD header parsing)

### Add After Validation (v9.3 follow-on)

- [ ] **COSY scatter** — complete 2D picture; low incremental effort once HSQC/HMBC exist
- [ ] **DEPT sub-tab** — valuable when DEPT data is present; conditional rendering is slightly tricky
- [ ] **HSQC correlation table** — useful for detailed review; defer until scatter is confirmed sufficient

### Future Consideration (v9.4+)

- [ ] **Per-iteration constraint diff** — HIGH complexity; useful only for multi-iteration deep-dive
- [ ] **Full spectrum trace from Bruker FID** — large new dependency (nmrglue); revisit if stick charts prove insufficient
- [ ] **Full 2D contour from raw Bruker data** — same issue; scatter is sufficient for the inspector

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Formatted run log | HIGH — immediate readability win on every run | LOW — CDN script + frontend only | P1 |
| Tab navigation | HIGH — prerequisite for all panels | LOW — pure CSS | P1 |
| ¹³C peak list table | HIGH — first verification step | LOW — JSON already available | P1 |
| HMBC correlation table | HIGH — core CASE review artefact | LOW — JSON already available | P1 |
| ¹³C bar chart | HIGH — visual signal summary | MEDIUM — matplotlib new dep | P1 |
| HSQC scatter | HIGH — C–H assignment check | MEDIUM — reuses matplotlib | P1 |
| HMBC scatter | HIGH — correlation overview with flags | MEDIUM — reuses matplotlib | P1 |
| LSD constraint inventory | HIGH — closes solver-input loop | MEDIUM — LSD header parser | P1 |
| COSY scatter | MEDIUM — supporting connectivity view | LOW incremental | P2 |
| DEPT sub-tab | MEDIUM — CH2 sign info | MEDIUM — conditional rendering | P2 |
| HSQC correlation table | LOW — scatter covers use case | LOW incremental | P3 |
| Per-iteration constraint diff | MEDIUM — deep debug aid | HIGH — multi-file diff logic | P3 |

**Priority key:**
- P1: Must have for v9.3 launch
- P2: Should have, add when P1 stable
- P3: Nice to have, future consideration

---

## NMR Domain Correctness Requirements

These are non-negotiable. Wrong convention = scientifically incorrect display.

| Requirement | Correct Convention | Common Mistake to Avoid |
|-------------|-------------------|-------------------------|
| ¹³C x-axis direction | High ppm (≈220) on left, 0 ppm on right | matplotlib default is left→right (low ppm first) |
| ¹H x-axis direction | High ppm (≈12) on left, 0 ppm on right | Same default error |
| HSQC axes | F2=¹H on x (reversed), F1=¹³C on y (reversed) | Swapping axes gives a transposed plot |
| HMBC axes | Same as HSQC: F2=¹H on x, F1=¹³C on y, both reversed | Same swap risk |
| COSY axes | Both ¹H, square, diagonal visible (F1=F2 line), both reversed | Non-square or missing diagonal |
| DEPT sign convention | DEPT-135: CH and CH3 bars above zero, CH2 bars below zero | Showing all bars positive loses CH2 identification |
| 2D y-axis direction | ¹³C: high ppm at top, 0 ppm at bottom | matplotlib default origin is lower-left |

Implementation note: a shared helper `_apply_nmr_axes(ax, xnuc, ynuc)` that calls `ax.invert_xaxis()` and `ax.invert_yaxis()` as appropriate should be shared across all spectrum renderers to prevent inconsistency. Pass `xnuc="1H"` or `xnuc="13C"` to encode the axis direction in one place.

---

## Data Sources and v9.2 Endpoint Dependencies

| Stage-2 Feature | Data Source (in analysis_dir) | Depends on Existing v9.2 | New Endpoint |
|----------------|-------------------------------|--------------------------|--------------|
| Formatted run log | `CASE-PROGRESS.md` | `/api/log` unchanged | None — frontend change only |
| ¹³C peak list table | `peaks/carbon_signals.json` | None | `GET /api/peaks/c13` |
| HMBC correlation table | `peaks/hmbc.json` | None | `GET /api/peaks/hmbc` |
| HSQC correlation table | `peaks/hsqc.json` | None | `GET /api/peaks/hsqc` |
| ¹³C bar chart image | `peaks/carbon_signals.json` + matplotlib | Shares data with ¹³C table | `GET /api/spectra/c13.svg` |
| DEPT sub-tab image | `peaks/carbon_signals.json` (mult field) + matplotlib | Shares data with ¹³C table | No new endpoint; render flag on ¹³C endpoint |
| HSQC scatter image | `peaks/hsqc.json` + matplotlib | None | `GET /api/spectra/hsqc.svg` |
| HMBC scatter image | `peaks/hmbc.json` + matplotlib | None | `GET /api/spectra/hmbc.svg` |
| COSY scatter image | `peaks/cosy.json` + matplotlib | None | `GET /api/spectra/cosy.svg` |
| LSD constraint inventory | `iteration_NN/compound.lsd` header block | None | `GET /api/constraints` |
| Tab navigation | None | `index.html` (extend) | None |

All image endpoints return pre-rendered matplotlib SVG (`image/svg+xml`) — the same format already used for structure depictions in v9.2. On-demand per request; no server-side cache. The `<img src="/api/spectra/c13.svg">` tag in the frontend polls naturally on the 3 s refresh cycle.

---

## Sources

- Direct code inspection: `src/lucy_ng/webview/` (app.py, routers/log.py, routers/status.py, static/index.html) — v9.2 architecture confirmed
- Direct artefact inspection: `data/nmrdata/active-lucy-ng-testprojects/CASE1/analysis/peaks/` — confirmed fields in `carbon_signals.json`, `hmbc.json`, `hsqc.json`, `cosy.json`
- Direct artefact inspection: CASE1 `iteration_01/compound.lsd` — confirmed constraint inventory JSON block structure and the `=== CONSTRAINT INVENTORY ===` delimiter
- Design spec: `docs/superpowers/specs/2026-07-02-case-webview-design.md` § Stage 2 — feature scope confirmed
- Phase 91 context: `.planning/milestones/v9.2-phases/91-api-endpoints-depictions-and-static-frontend/91-CONTEXT.md` — v9.2 decisions locked (D-01 through D-15)
- NMR display conventions: IUPAC standard practice, domain knowledge — ppm axis reversal, DEPT sign convention, 2D F1/F2 axis assignment (HIGH confidence, stable conventions)

---

*Feature research for: v9.3 CASE Web-View Stage 2*
*Researched: 2026-07-07*
