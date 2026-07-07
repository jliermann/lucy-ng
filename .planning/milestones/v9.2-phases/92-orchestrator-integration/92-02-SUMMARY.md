---
phase: 92-orchestrator-integration
plan: "02"
subsystem: skill-prompt / orchestrator
tags: [wv-07, case-md, webview, orchestrator-integration, observability]
dependency_graph:
  requires: [92-01]
  provides: [WV-07-case-md-launch, OD-5-dashboard-header]
  affects: [.claude/commands/lucy-ng/case.md, .claude/commands/lucy-ng/references/progress-format.md]
tech_stack:
  added: []
  patterns: [foreground-non-blocking-bash, continue-on-failure-guard, skill-prompt-edit]
key_files:
  modified:
    - .claude/commands/lucy-ng/case.md
    - .claude/commands/lucy-ng/references/progress-format.md
decisions:
  - "OD-1: auto/ephemeral port — no --port argument; server.start() picks a free port"
  - "OD-2: continue-with-warning on failure — serve failure prints one line and CASE run proceeds"
  - "OD-3: no --open flag — orchestrator runs headless; user opens URL manually"
  - "OD-4: pass <compound_path>/analysis verbatim — server.start() resolves internally"
  - "OD-5: Dashboard URL recorded in CASE-PROGRESS.md header via **Dashboard:** field"
metrics:
  duration: "~8 minutes"
  completed: "2026-07-06"
  tasks_completed: 2
  tasks_total: 2
---

# Phase 92 Plan 02: Orchestrator Integration — Webview Launch Wiring Summary

**One-liner:** case.md now auto-launches `lucy webview serve` in spawn_case_team Step 5 (before the first `[BEGIN]` push), prints URL + stop hint, continues on failure, and records the URL in the CASE-PROGRESS.md `**Dashboard:**` header field.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Insert webview launch block + terminate_team no-stop comment | `680ff25` | `.claude/commands/lucy-ng/case.md` |
| 2 | Add OD-5 Dashboard header field to progress-format.md + write_progress note | `3a33e29` | `.claude/commands/lucy-ng/references/progress-format.md`, `.claude/commands/lucy-ng/case.md` |

---

## What Was Built

### Task 1 — case.md WV-07 launch block

Inserted immediately after the `run_start` timing stamp comment in `spawn_case_team` Step 5 and before the `SendMessage([BEGIN] peak-picking)` block:

- A `<!-- WV-07 -->` HTML comment explaining the design rationale and constraints.
- A `**Launch the webview dashboard (non-blocking — exits in ~0.5 s):**` subsection with a fenced Bash block:
  ```bash
  WEBVIEW_OUTPUT=$(lucy webview serve "<compound_path>/analysis" 2>&1)
  WEBVIEW_EXIT=$?
  if [ $WEBVIEW_EXIT -eq 0 ]; then
    echo "$WEBVIEW_OUTPUT"
  else
    echo "Note: Webview dashboard unavailable — $WEBVIEW_OUTPUT"
    echo "Install lucy-ng[webview] to enable the live dashboard."
  fi
  ```
- Prose explaining the foreground/non-blocking semantics, the no-`&`/no-`--port`/no-`--open` constraints, the continue-on-failure policy, and the `WEBVIEW_URL` variable storage instruction.

Also added to `terminate_team` (Step 0 area): an explicit "intentionally NOT stopped" note explaining the server is left running for post-run dashboard review, without using the `lucy webview stop` literal (which the `test_terminate_team_no_stop` regression guard prohibits).

### Task 2 — progress-format.md OD-5 Dashboard field

Added one line to the CASE-PROGRESS.md header template in `progress-format.md`, directly after the `**Team:**` line:

```markdown
**Dashboard:** <webview URL printed by `lucy webview serve` at run start, or "unavailable — [webview] extra not installed" if the launch failed>
```

Added one sentence to the `write_progress` step in `case.md` instructing the orchestrator to fill the `**Dashboard:**` field from the `WEBVIEW_URL` variable captured in Step 5.

---

## Verification Results

```
pytest tests/test_case_md_wv07.py tests/test_cli_webview.py::TestWebviewLifecycle::test_serve_outlives_caller -q
5 passed in 4.92s
```

| Test | Status | Notes |
|------|--------|-------|
| `test_webview_launch_present` | GREEN (was RED) | `lucy webview serve` appears before `content="[BEGIN] peak-picking` |
| `test_stop_hint_present` | GREEN (was RED) | `lucy webview stop` in pre-terminate region |
| `test_terminate_team_no_stop` | GREEN (stayed green) | terminate_team section has zero `lucy webview stop` occurrences |
| `test_progress_format_dashboard_field` | GREEN (was RED) | `**Dashboard:**` present in progress-format.md |
| `test_serve_outlives_caller` | GREEN (stayed green) | no regression; webview source untouched |

---

## Deviations from Plan

None — plan executed exactly as written. Both OD-1..5 design decisions adopted as specified.

---

## Known Stubs

None. No placeholder or hardcoded values were introduced.

---

## Threat Flags

No new security surface introduced. All three STRIDE items (T-92-03 through T-92-05) are addressed:
- T-92-03 (DoS via webview failure): mitigated by the continue-on-failure guard in the Bash block.
- T-92-04 (info disclosure): no bind change; server remains 127.0.0.1 only (Phase 90).
- T-92-05 (shell injection): `<compound_path>` passed as a single argv string; pre-validated in Step 2.

---

## Fresh-Session Requirement

**IMPORTANT:** `case.md` is a Claude Code skill prompt loaded at session start. The edits committed in this plan will NOT take effect in the current session. A **fresh Claude Code session** is required before Plan 92-03's live verification. After opening the new session, run `/lucy-ng:case <compound_path> <formula> --smoke-test` and confirm the orchestrator prints `Webview server running at http://127.0.0.1:NNNNN` before the first `[BEGIN]` push.

This is the standard reload procedure; three `<!-- RELOAD NOTE: ... -->` comments already exist in case.md acknowledging this requirement.

---

## Self-Check: PASSED

- FOUND: `.claude/commands/lucy-ng/case.md`
- FOUND: `.claude/commands/lucy-ng/references/progress-format.md`
- FOUND: `.planning/phases/92-orchestrator-integration/92-02-SUMMARY.md`
- FOUND: commit `680ff25` (Task 1)
- FOUND: commit `3a33e29` (Task 2)
