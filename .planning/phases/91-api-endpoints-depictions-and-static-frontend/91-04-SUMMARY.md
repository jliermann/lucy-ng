---
phase: 91-api-endpoints-depictions-and-static-frontend
plan: "04"
subsystem: webview
tags: [webview, frontend, packaging, routing, fastapi, vanilla-js]
dependency_graph:
  requires: [91-02, 91-03]
  provides: [WV-06, WV-08]
  affects: [src/lucy_ng/webview/app.py, src/lucy_ng/webview/static/index.html, pyproject.toml]
tech_stack:
  added: []
  patterns:
    - Lazy router registration inside create_app() (WV-08 import-safety)
    - FileResponse for single static file at GET /
    - setInterval polling (vanilla JS, no build step)
    - textContent-only DOM updates (XSS guard T-91-09)
key_files:
  created:
    - src/lucy_ng/webview/static/index.html
  modified:
    - src/lucy_ng/webview/app.py
    - pyproject.toml
decisions:
  - "Stub index.html committed in Task 2 to satisfy TestFrontend acceptance criteria; replaced by full dashboard in Task 3 (same approach as TDD red/green across tasks)"
  - "innerHTML word removed from comments to satisfy grep-based XSS gate (T-91-09); all actual DOM updates use textContent exclusively"
  - "SVG re-fetch gated on SMILES change via lastSmiles cache in JS (D-10: no server-side cache, no flicker)"
  - "Collapse to stacked on narrow windows via single CSS media query at 700 px (Claude's Discretion layout)"
metrics:
  duration: "226s"
  completed: "2026-07-04T14:31:00Z"
  tasks_completed: 3
  tasks_total: 4
  files_changed: 3
---

# Phase 91 Plan 04: Router Wiring, Dashboard Frontend, and Packaging Summary

**One-liner:** Extended create_app() with three lazy router inclusions and FileResponse at GET /, delivered a single-file vanilla-JS dashboard with 3 s polling and scroll-preserving log, and added hatch wheel artifact entry for static/*.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add webview/static/* to hatch wheel artifacts [BLOCKING] | 2d1fc07 | pyproject.toml |
| 2 | Dock routers in create_app() and serve index.html at GET / | 0d7bba4 | app.py, static/index.html (stub) |
| 3 | Build the single-file vanilla-JS dashboard | 14beedf | static/index.html (full) |

## Task 4 (not executed)

Task 4 is `type="checkpoint:human-verify"` — real-browser visual confirmation. See the CHECKPOINT REACHED section in the execution output for exact manual steps.

## What Was Built

### pyproject.toml (Task 1)
`[tool.hatch.build.targets.wheel].artifacts` now has three entries:
- `src/lucy_ng/data/schemas/*` (pre-existing)
- `src/lucy_ng/lsd/filters/*` (pre-existing)
- `src/lucy_ng/webview/static/*` (new — WV-08 packaging gap closed)

Without this entry, hatch silently drops index.html from the wheel and GET / 500s after pip install.

### app.py (Task 2)
`create_app()` extended with:
- Three lazy router imports inside the function body (WV-08 safe)
- `app.include_router()` x3: status, structures, log
- `FileResponse` import inside the function body
- GET / route returning FileResponse(static/index.html, text/html)

WV-08 confirmed: `import lucy_ng.cli.main` does not pull fastapi into sys.modules.

### static/index.html (Task 3)
Single self-contained file (no build step, no CDN):
- Inline CSS: light theme, system fonts, slim status bar + two-column grid/log layout, responsive
- `refreshStatus()`: renders state badge, iteration, active phase, elapsed time
- `refreshStructures()`: builds SVG tiles; re-requests SVG only when SMILES at that index changed (D-10); rank/MAE/quality labels as HTML around tile (D-09); "+N more" hint
- `refreshLog()`: `pre.textContent = data.content` (never a markup-insertion method — T-91-09); scroll preservation (D-13)
- `setInterval(tick, 3000)` polls all three endpoints (D-15)
- Fetch failures handled with `console.warn` (no uncaught rejections)

## Verification Results

```
pytest tests/test_webview_api.py::TestWiring     — PASSED
pytest tests/test_webview_api.py::TestFrontend   — PASSED
pytest tests/test_webview_api.py::TestPackaging  — PASSED
pytest tests/ -k webview                         — 27 passed
WV-08 import safety check                        — PASSED (fastapi not in sys.modules after lucy_ng.cli.main import)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] innerHTML in comments triggered XSS grep gate**
- **Found during:** Task 3 verification
- **Issue:** The acceptance criterion requires `grep -c innerHTML == 0` in index.html. Two explanatory comments used the word "innerHTML" (referencing what NOT to use), which tripped the grep-based gate.
- **Fix:** Rewrote both comments to describe the intent without mentioning the forbidden word.
- **Files modified:** src/lucy_ng/webview/static/index.html
- **Commit:** 14beedf

**2. [Rule 2 - Missing functionality] Stub index.html needed before TestFrontend**
- **Found during:** Task 2 — GET / FileResponse requires the file to exist at serve time.
- **Issue:** Task 2 creates the route; Task 3 creates the full file. Without any file, TestFrontend fails in Task 2.
- **Fix:** Committed a minimal stub index.html in Task 2 alongside app.py; Task 3 replaced it with the full dashboard.
- **Files modified:** src/lucy_ng/webview/static/index.html
- **Commits:** 0d7bba4 (stub), 14beedf (full)

## Known Stubs

None. The "Waiting for candidates..." and "Waiting for log data..." strings are intentional empty-state messages (D-04 graceful degradation), not stubs — they disappear when real data arrives.

## Threat Flags

No new threat surface beyond what was declared in the plan's threat register (T-91-09, T-91-10, T-91-11). T-91-09 mitigation confirmed: the file contains zero occurrences of innerHTML; all log and DOM updates use textContent or createElement + textContent.

## Self-Check: PASSED

| Item | Result |
|------|--------|
| src/lucy_ng/webview/app.py | FOUND |
| src/lucy_ng/webview/static/index.html | FOUND |
| pyproject.toml | FOUND |
| commit 2d1fc07 | FOUND |
| commit 0d7bba4 | FOUND |
| commit 14beedf | FOUND |
