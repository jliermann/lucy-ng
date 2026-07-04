# lucy-ng Roadmap

## Milestones

- [v1.0 Core CASE Pipeline](milestones/v1.0-ROADMAP.md) - Phases 1-10 (shipped 2026-01-12)
- [v1.1 Database-Backed Dereplication](milestones/v1.1-ROADMAP.md) - Phases 11-15 (shipped 2026-01-15)
- [v1.2 HOSE Database Prediction](milestones/v1.2-ROADMAP.md) - Phases 16-19 (shipped 2026-01-18)
- **v2.0 Robust Multi-Agent CASE** - Phases 20-26 (shipped 2026-02-08)
- **v2.1 Working Multi-Agent CASE** - Phases 27-33 (shipped 2026-02-09)
- [v3.0 Statistical Detection](milestones/v3.0-ROADMAP.md) - Phases 34-40 (shipped 2026-02-16)
- [v4.0 Team-Based CASE](milestones/v4.0-ROADMAP.md) - Phases 41-48 (shipped 2026-02-18)
- [v5.0 Fragment Library](milestones/v5.0-ROADMAP.md) - Phases 49-54 (shipped 2026-02-21)
- [v6.0 Skill Quality Overhaul](milestones/v6.0-ROADMAP.md) - Phases 55-58 (shipped 2026-03-10)
- [v7.0 Statistical 4J Detection](milestones/v7.0-ROADMAP.md) - Phases 59-64 (ABANDONED 2026-03-12)
- **v8.0 pyLSD Integration** - Phases 65-71 (superseded by v9.0 before UAT passed)
- ✅ [v9.0 CASE Reliability & Skill Consolidation](milestones/v9.0-ROADMAP.md) - Phases 72-85 (shipped 2026-06-17)
- ✅ [v9.1 CASE Final-Answer Correctness & Verification Gates](milestones/v9.1-ROADMAP.md) - Phases 86-89 (shipped 2026-06-29)
- **v9.2 CASE Web-View** - Phases 90-92 (in progress)

---

**v9.1 outcome:** Closed three "clean-but-wrong" defect classes — RANK (ranker path unified),
IDENT (`lucy identify` + post-solution G-IDENT gate), MULT (per-family multiplicity search +
MAE-independent coverage gate) — and proved them end-to-end with five blind CASE UATs
(CASE5/6/7/8 PASS; CASE4 conditional). Audit: `milestones/v9.1-MILESTONE-AUDIT.md`.
Non-blocking deferred follow-up: CASE4 azulene-regiochemistry-enumeration gap (4th defect class,
exact chamazulene regiochemistry still unreachable) — todo `2026-06-25-case4-azulene-regiochemistry-enumeration-gap`.

---

## v9.2 CASE Web-View

**Goal:** A read-only web dashboard makes a CASE run observable live (and after the fact) —
three widgets (run status, top structures, log), auto-refresh, launched automatically by the
CASE orchestrator and kept alive after the run.

### Phases

- [x] **Phase 90: Server, CLI, and Packaging** — `lucy webview` commands, server lifecycle via `.webview.json`, optional `lucy-ng[webview]` extra (completed 2026-07-03)
- [ ] **Phase 91: API Endpoints, Depictions, and Static Frontend** — three JSON endpoints with graceful degradation, RDKit SVG depictions, vanilla-JS dashboard
- [ ] **Phase 92: Orchestrator Integration** — `case.md` launches the server at run start and reports the URL

### Phase Details

#### Phase 90: Server, CLI, and Packaging

**Goal**: Users can start, stop, and query a read-only webview server for any `analysis/` folder using `lucy webview` commands; the server package is isolated as an optional extra.
**Depends on**: Nothing
**Requirements**: WV-01, WV-02, WV-08
**Success Criteria** (what must be TRUE):
  1. `lucy webview serve <analysis_dir>` starts a FastAPI/uvicorn server, writes `.webview.json` (pid/port/url) into `<analysis_dir>`, and prints the dashboard URL.
  2. `lucy webview stop <analysis_dir>` terminates the server process and removes `.webview.json`; the port is no longer in use.
  3. `lucy webview status <analysis_dir>` reports whether a server is currently running for that folder.
  4. Running `lucy webview serve` on a folder that already has a live server returns the existing URL instead of double-binding (idempotent start).
  5. `pip install lucy-ng` (core) succeeds without FastAPI or uvicorn; `pip install lucy-ng[webview]` adds them.
**Plans**: 3 plans (3 waves)
  - [x] 90-01-PLAN.md — Test infrastructure: `tests/test_cli_webview.py` (6 classes / 11 tests) + conftest fixtures (Wave 0)
  - [x] 90-02-PLAN.md — Webview server package: `state.py` (WebviewState) + `app.py` (create_app) + `server.py` (lifecycle) (Wave 1)
  - [x] 90-03-PLAN.md — CLI group `lucy webview` (serve/stop/status/_run) + `cli/__main__.py` + registration + `[webview]` extra (Wave 2)
**UI hint**: yes

---

#### Phase 91: API Endpoints, Depictions, and Static Frontend

**Goal**: Opening the dashboard URL in a browser shows three auto-refreshing widgets — run status, top candidate structures with RDKit SVG depictions, and the scrollable run log — with graceful degradation during live runs when source files are absent or partial.
**Depends on**: Phase 90
**Requirements**: WV-03, WV-04, WV-05, WV-06
**Success Criteria** (what must be TRUE):
  1. `GET /api/status` on a fixture folder returns iteration number, active phase, and elapsed time derived from `timing.json`/`timing.jsonl` and `CASE-PROGRESS.md`.
  2. `GET /api/log` returns the current raw content of `CASE-PROGRESS.md` as a text/JSON payload.
  3. `GET /api/structures` returns a ranked list with SMILES, MAE, and rank fields; `GET /api/structure/{i}.svg` returns a non-empty RDKit SVG for a valid SMILES index.
  4. All three API endpoints return a well-formed "waiting for data" payload (status 200, not 500) when source files are missing, empty, or mid-write; `GET /api/structure/{i}.svg` for an out-of-range index returns 404.
  5. A malformed SMILES entry in a solutions file causes that entry to render as a placeholder; all other entries in the list render correctly.
  6. Opening `http://localhost:<port>/` in a browser shows the three widgets auto-refreshing every ~3 s without a JavaScript build step.

**Note for planning:** `[tool.hatch.build.targets.wheel]` must add `src/lucy_ng/webview/static/*` to `artifacts` when the static frontend lands (Phase 90 deliberately left it untouched).
**Plans**: 4 plans (3 waves)
Plans:
- [ ] 91-01-PLAN.md — Wave 0 test scaffold: fixtures (empty/live/final analysis dirs) + tests/test_webview_api.py
- [ ] 91-02-PLAN.md — status + log routers (GET /api/status, GET /api/log) with graceful degradation
- [ ] 91-03-PLAN.md — RDKit depiction module + structures router (GET /api/structures, GET /api/structure/{i}.svg)
- [ ] 91-04-PLAN.md — create_app wiring + GET / + static/index.html dashboard + hatch artifacts (BLOCKING)
**UI hint**: yes

---

#### Phase 92: Orchestrator Integration

**Goal**: When a CASE run starts, the orchestrator automatically launches the webview server for the `analysis/` directory and reports the dashboard URL and stop hint to the user before any team work begins; the server outlives the team.
**Depends on**: Phase 91
**Requirements**: WV-07
**Success Criteria** (what must be TRUE):
  1. At CASE run start (before the first `[BEGIN]`), `case.md` runs `lucy webview serve analysis/` in the background and prints the dashboard URL and `lucy webview stop` hint to the user.
  2. After the run ends and `terminate_team` fires, the webview server is still running and the dashboard URL is still reachable.
  3. The orchestrator notes in its output that the user must stop the server manually via `lucy webview stop <analysis_dir>`.
**Plans**: TBD

---

### Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 90. Server, CLI, and Packaging | 3/3 | Complete    | 2026-07-03 |
| 91. API Endpoints, Depictions, and Static Frontend | 0/? | Not started | - |
| 92. Orchestrator Integration | 0/? | Not started | - |

---

**v9.1 outcome (for reference):**
Phases 86-89. All requirements (RANK-01..03, IDENT-01..03, MULT-01..04, UAT-01..03) met.
Tests: 1131 passing at close.
