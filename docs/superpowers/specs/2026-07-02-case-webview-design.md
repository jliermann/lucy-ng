# CASE Web-View — Design Spec (MVP)

**Date:** 2026-07-02
**Status:** Approved (brainstorming) — feeds the GSD milestone
**Author:** Christoph Steinbeck + Claude

## Motivation

A CASE run driven by the agent team takes 20–120 min (per the big blind UAT) and its
progress is currently only visible by tailing files in the `analysis/` folder. A read-only
web dashboard makes a live run observable at a glance: which iteration is running, the best
structures found so far, and the running log. This is purely informative — **no control
functions**.

## Goals / Non-goals

**Goals (MVP):**
- One command `lucy webview serve <analysis_dir>` starts a local HTTP server that renders the
  folder read-only, with auto-refresh, for a **live or finished** run.
- The CASE orchestrator starts it automatically at run start and reports the URL first.
- Three widgets: run **status**, **top structures**, scrollable **log**.

**Non-goals (explicitly out of MVP → Stage 2):**
- Rendered 1D/2D spectra tabs (needs new plotting infrastructure from Bruker data).
- Extra data tables.
- Any control/action over the run (start/stop/edit). The view never mutates the run.

## Architecture

- **Server: FastAPI + uvicorn**, shipped as an optional extra `lucy-ng[webview]` (core CLI
  stays dependency-free). Chosen for future-proofing: FastAPI builds on Pydantic v2 (already
  used throughout lucy-ng, so data models are reused type-safely under `mypy --strict`); the
  endpoint structure scales cleanly to Stage 2; and it leaves room for SSE/WebSocket push
  later if polling proves insufficient.
- **Frontend: a static `index.html` + vanilla JS**, no build step (no node toolchain in a
  Python package). JS polls the JSON endpoints every ~3 s and updates the panels. Structured
  so Stage-2 tabs dock in without a rewrite. (If richer reactivity is later needed: htmx/Alpine
  via CDN — still no build.)
- **The server is "dumb":** it knows nothing about the agent team; it only reads files under
  `analysis_dir`. This is why the same command also serves finished runs (post-hoc review).
- **Structure rendering:** RDKit (already a dependency) → SMILES → SVG depiction.

## Components / Endpoints

Each endpoint reads the live `analysis/` folder on request (no server-side state).

| Widget (MVP) | Data source | Endpoint |
|--------------|-------------|----------|
| Status header — current iteration, active phase, elapsed | `timing.json` / `timing.jsonl` (active phase = last `phase_start` without matching `phase_end`) + `CASE-PROGRESS.md` | `GET /api/status` |
| Top structures (~10) — depiction + MAE/rank | `ranking_results.json` (or `final_results.md`) + `iteration_*/solutions.smi` | `GET /api/structures` + `GET /api/structure/{i}.svg` |
| Scrollable log | `CASE-PROGRESS.md` (raw) | `GET /api/log` |
| Static UI | bundled `index.html` + JS/CSS assets | `GET /` |

## CLI

- `lucy webview serve <analysis_dir> [--port N] [--host 127.0.0.1] [--open]` — start the server
  (background-friendly). Picks a free port if `--port` is omitted; writes a `.webview.json`
  (pid + port + url) into `<analysis_dir>`. Prints the URL.
- `lucy webview stop <analysis_dir>` — reads `.webview.json` and terminates that server.
- `lucy webview status <analysis_dir>` — report whether a server is running for that folder.

## Integration into the CASE run

In `case.md`, at run start (right after the team spawns, before the first `[BEGIN]`), the
orchestrator launches `lucy webview serve analysis/` in the background and **reports to the
user first**: the URL and the stop hint (`lucy webview stop <analysis_dir>`). Reported once,
prominently. The server is NOT torn down at `terminate_team` — it keeps running so the user can
review the finished run, and the user stops it themselves. (The orchestrator notes this.)

## Lifecycle

- Server lifetime is decoupled from the run (per above). One server per `analysis_dir`,
  tracked by `.webview.json`. Starting a second `serve` on a folder that already has a live
  server reports the existing URL instead of double-binding.
- Bind to `127.0.0.1` by default (local-only; no external exposure).

## Error handling (central for a live dashboard)

During a live run the source files are partial or absent (e.g. `ranking_results.json` exists
only after the first ranking; `solutions.smi` only after an iteration). Every endpoint must
degrade gracefully:
- Missing/empty/partly-written file → the endpoint returns a well-formed "no data yet" payload
  (empty list / null fields + a `state` flag), never a 500.
- Malformed SMILES in a solutions file → that entry is skipped with a placeholder, the rest render.
- `GET /api/structure/{i}.svg` for an out-of-range index → 404, not a crash.
The dashboard shows "waiting for first results…" panels rather than errors while data is absent.

## Testing

- FastAPI `TestClient` against a fixture `analysis/` folder (both a mid-run partial folder and a
  finished folder) — assert each endpoint's shape and graceful-degradation behaviour.
- RDKit depiction: known SMILES → non-empty SVG; malformed SMILES → placeholder, no raise.
- Lifecycle: `serve` writes `.webview.json`; `stop` terminates and cleans it; double-`serve`
  returns the existing URL.
- No live agent-team run is needed to test the webview (the "dumb server" boundary makes it
  unit-testable from fixtures).

## Stage 2 (deferred, not in this milestone)

- Tab-based non-interactive rendered spectra (1D 13C/1H/DEPT plots, 2D HSQC/HMBC/COSY contour
  plots) — requires new plotting from Bruker data via the existing readers.
- Additional tables (peak lists, constraint inventory, HMBC usage).
- Optional SSE/WebSocket live push to replace polling.
