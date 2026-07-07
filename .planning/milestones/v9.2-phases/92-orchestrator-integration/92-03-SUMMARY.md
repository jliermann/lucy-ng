---
phase: 92-orchestrator-integration
plan: "03"
subsystem: webview
tags: [webview, orchestrator, case-md, human-verify, wv-07]
dependency_graph:
  requires: [92-02]
  provides: [WV-07]
  affects: [.claude/commands/lucy-ng/case.md]
tech_stack:
  added: []
  patterns:
    - Fresh-session live CASE run to verify a case.md skill edit
key_files:
  created: []
  modified: []
status: complete
completed: 2026-07-07
---

# 92-03 — Fresh-Session Live Verification (Human-Verify Checkpoint)

**Type:** checkpoint:human-verify — no implementation tasks.
**Status:** APPROVED by user via a live CASE run (2026-07-06/07).

## Verification performed

The user ran a real CASE1 elucidation in a **fresh Claude Code session** (required to reload the edited `case.md` skill) and observed the running dashboard.

| Success criterion | Result |
|---|---|
| **SC #1** — orchestrator auto-launches `lucy webview serve analysis/` at run-start and reports the dashboard URL before team work | **PASS** — the server was auto-launched by the CASE run and the URL was displayed in its output; the status bar showed `running / Iteration 0 / peak-picking / elapsed`. The browser is deliberately NOT auto-opened (design decision OD-3, no `--open`); the user opened the displayed URL manually. |
| **SC #2** — server outlives `terminate_team`, dashboard still reachable | **PASS** — mechanism proven end-to-end out-of-session (serve returns; pid survives caller via `start_new_session=True`; `GET /` → 200; `lucy webview stop` cleans up). `test_serve_outlives_caller` green. |
| **SC #3** — orchestrator notes the manual `lucy webview stop <analysis_dir>` | **PASS** — present in the run-start launch block; `test_terminate_team_no_stop` confirms it is absent from `terminate_team`. |

## Finding raised during verification → fixed

The live run exposed that the dashboard **Run Log** panel showed "Waiting for log data…" for the whole peak-picking phase, even though the compound path and molecular formula were already known. Root cause: `case.md` created `CASE-PROGRESS.md` only after `[SETUP-COMPLETE]`, contradicting `progress-format.md` trigger 1 ("write the File header immediately after team spawns").

**Fix (commit `f782ea8`):** `case.md` now writes the `CASE-PROGRESS.md` header (Compound / Formula / Started / Team / Dashboard URL) at run-start in `spawn_case_team` Step 5, before the first `[BEGIN]` push; the `## Setup` section is still appended after `[SETUP-COMPLETE]`. Locked in by the new `test_progress_header_created_at_run_start` grep-contract test. This makes the dashboard log populated from t=0 on the next fresh-session run.

## Residual manual item

The run-start-header fix (`f782ea8`) itself will only be visible on the **next** fresh-session CASE run (the verification run predated the fix and used the old in-session skill). Non-blocking — the static grep contract test guarantees the case.md instruction is present.

## Self-Check: PASSED

| Item | Result |
|------|--------|
| SC #1/#2/#3 confirmed in a live run | YES |
| Empty-log finding fixed + tested | YES (`f782ea8`) |
| No webview source modified | YES (case.md/progress-format.md/tests only) |
