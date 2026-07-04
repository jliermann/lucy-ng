# Milestone v9.2 Requirements — CASE Web-View

**Goal:** A read-only web dashboard makes a CASE run observable live (and after the fact) — purely informative, no control functions.

**Source:** User-requested, brainstormed and approved design spec `docs/superpowers/specs/2026-07-02-case-webview-design.md`. Motivated by the big blind UAT (runs of 20–120 min with visibility only via tailing files).

## v9.2 Requirements

### WEBVIEW — read-only run dashboard
- [x] **WV-01**: User can start a local dashboard for any `analysis/` folder with `lucy webview serve <dir>` — for a live OR a finished run (server reads files only, knows nothing of the agent team).
- [x] **WV-02**: User can stop the dashboard with `lucy webview stop <dir>` and check whether one is running with `lucy webview status <dir>` (tracked via a `.webview.json` pid/port file in the folder).
- [x] **WV-03**: User sees the run status live — current iteration, active phase, and elapsed time — derived from `timing.json`/`timing.jsonl` + `CASE-PROGRESS.md`, auto-refreshed.
- [x] **WV-04**: User sees the best ~10 candidate structures rendered (RDKit SVG depiction) with MAE/rank, from `ranking_results.json`/`final_results.md` + `solutions.smi`.
- [x] **WV-05**: User sees the run log (`CASE-PROGRESS.md`) in a scrollable panel that auto-refreshes.
- [x] **WV-06**: The dashboard degrades gracefully during a live run — missing/empty/partly-written source files show a "waiting for data" state, never a 500; malformed SMILES is skipped, not fatal.
- [ ] **WV-07**: When a CASE run starts, the orchestrator (`case.md`) launches the server in the background and reports the dashboard URL and stop hint to the user before work begins.
- [x] **WV-08**: The webview ships as an optional extra `lucy-ng[webview]` (FastAPI + uvicorn); the core `lucy` CLI stays dependency-free. The frontend is static HTML + vanilla JS (no build step).

## Future Requirements (deferred — Stage 2)

- [ ] Tab-based non-interactive rendered spectra (1D 13C/1H/DEPT plots; 2D HSQC/HMBC/COSY contour plots) from Bruker data via the existing readers — the largest Stage-2 item (new plotting infrastructure).
- [ ] Additional data tables (peak lists, constraint inventory, HMBC-usage).
- [ ] SSE/WebSocket live push to replace polling (FastAPI makes this incremental).

## Out of Scope

- Any control/action over the run (start/stop/edit/re-run the CASE workflow). The view is strictly read-only; it never mutates a run. (Rationale: keeps the "dumb server" boundary — observability without a control surface to secure.)
- A JS build toolchain / SPA framework (React/Vue with node build). (Rationale: a build step in a Python package is a maintenance burden; vanilla JS + optional CDN htmx/Alpine covers the need.)
- Remote/authenticated access. Binds to `127.0.0.1` only. (Rationale: local dev observability, not a hosted service.)

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| WV-01 | Phase 90 | Complete |
| WV-02 | Phase 90 | Complete |
| WV-08 | Phase 90 | Complete |
| WV-03 | Phase 91 | Complete |
| WV-04 | Phase 91 | Complete |
| WV-05 | Phase 91 | Complete |
| WV-06 | Phase 91 | Complete |
| WV-07 | Phase 92 | Pending |

**Coverage:** 8/8 requirements mapped. No orphans.
