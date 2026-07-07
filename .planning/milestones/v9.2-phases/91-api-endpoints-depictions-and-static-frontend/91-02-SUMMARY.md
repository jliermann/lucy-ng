---
phase: 91-api-endpoints-depictions-and-static-frontend
plan: "02"
subsystem: webview
tags: [api, fastapi, graceful-degradation, status-endpoint, log-endpoint]
dependency_graph:
  requires: [91-01]
  provides: [status-router, log-router, routers-package]
  affects: [webview-api-layer]
tech_stack:
  added: []
  patterns:
    - "make_router(analysis_dir) -> APIRouter factory with closure over analysis_dir"
    - "Three-tier file-read degradation: timing.json → timing.jsonl → CASE-PROGRESS.md → waiting"
    - "Per-line json.loads with try/except skip for partial timing.jsonl lines (Pitfall 7)"
key_files:
  created:
    - src/lucy_ng/webview/routers/__init__.py
    - src/lucy_ng/webview/routers/status.py
    - src/lucy_ng/webview/routers/log.py
  modified: []
decisions:
  - "Epoch field in timing.jsonl cast with int() before arithmetic (Pitfall 4 — shell printf writes it as a JSON string)"
  - "Iteration parsed from lsd-iteration-NN phase name using regex; non-matching phases return iteration=0"
  - "dict[str, Any] used for all JSON return types to satisfy strict mypy"
metrics:
  duration_minutes: 4
  completed_date: "2026-07-04"
  tasks_completed: 2
  tasks_total: 2
  files_created: 3
  files_modified: 0
---

# Phase 91 Plan 02: Status and Log API Routers Summary

**One-liner:** GET /api/status with three-tier timing.json/timing.jsonl/CASE-PROGRESS.md degradation and GET /api/log with raw CASE-PROGRESS.md passthrough, both HTTP 200 on missing/partial files.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create routers package + status router | c4acb50 | routers/__init__.py, routers/status.py |
| 2 | Create log router (raw CASE-PROGRESS.md passthrough) | 9e04560 | routers/log.py |

## What Was Built

### Task 1 — routers package + status router

Created `src/lucy_ng/webview/routers/__init__.py` (empty — WV-08 safe: importing it does NOT load fastapi) and `src/lucy_ng/webview/routers/status.py` exporting `make_router(analysis_dir: Path) -> APIRouter`.

The `GET /api/status` handler calls `_derive_status(analysis_dir)` which implements the exact three-tier fallback:

1. **timing.json present** (run finalized): parse `total_duration_s`, return `state="complete"`, `elapsed_s=total_duration_s`, `active_phase=None`.
2. **timing.jsonl present** (live run): read line-by-line, skip any line that fails `json.loads` (Pitfall 7 — partial mid-write lines). Find the last `phase_start` event whose phase has no matching `phase_end` event. Extract iteration from `lsd-iteration-NN` via regex. Compute `elapsed_s = int(now.timestamp()) - int(run_start_event["epoch"])` with explicit `int()` cast (Pitfall 4 — epoch is a JSON string). Return `state="running"`.
3. **CASE-PROGRESS.md present** (timing instrumentation lag): parse `## Iteration N` and `### <Agent>` headers. Return `state="running"`, `elapsed_s=None`, `source="progress_md_fallback"`.
4. **No data**: return `state="waiting"`, all fields None.

Every code path is wrapped in try/except so no exception escapes to a 500.

### Task 2 — log router

Created `src/lucy_ng/webview/routers/log.py` exporting `make_router(analysis_dir: Path) -> APIRouter`.

The `GET /api/log` handler reads `analysis_dir/CASE-PROGRESS.md` via `read_text` and returns `{"state":"ok","content":<raw text>}`. On `FileNotFoundError` or `OSError` returns `{"state":"waiting","content":""}`. No markdown rendering (D-12). Never raises 500.

## Verification

```
pytest tests/test_webview_api.py::TestStatusEndpoint tests/test_webview_api.py::TestLogEndpoint -q
5 passed
```

Import safety confirmed:
- `import lucy_ng.webview.routers` → fastapi NOT in sys.modules (WV-08 intact)
- `import lucy_ng.webview.server` → fastapi NOT in sys.modules

mypy: no errors in status.py or log.py (66 pre-existing errors in other files unchanged).

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. Both routers read live filesystem paths; no hardcoded empty values flow to callers.

## Threat Flags

None. Endpoints are read-only; all file-read errors degrade to HTTP 200 waiting payloads (T-91-03 and T-91-04 mitigated per threat register).

## Self-Check: PASSED

Files exist:
- src/lucy_ng/webview/routers/__init__.py: FOUND
- src/lucy_ng/webview/routers/status.py: FOUND
- src/lucy_ng/webview/routers/log.py: FOUND

Commits exist:
- c4acb50: FOUND (feat(91-02): add routers package + status router with graceful degradation)
- 9e04560: FOUND (feat(91-02): add log router with raw CASE-PROGRESS.md passthrough)
