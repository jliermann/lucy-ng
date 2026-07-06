---
phase: 92
slug: orchestrator-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-06
---

# Phase 92 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (existing `tests/` suite) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_case_md_wv07.py tests/test_cli_webview.py -q` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5–20 seconds (targeted subset) |

---

## Sampling Rate

- **After every task commit:** Run the quick command above
- **After every plan wave:** Run `pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds (targeted subset)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| _(planner fills per task)_ | — | — | WV-07 | — | — | grep/integration | `pytest tests/test_case_md_wv07.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_case_md_wv07.py` — grep-based assertions that `case.md` contains the webview-launch step at run-start, the `lucy webview stop` hint, and that `terminate_team` does NOT stop the server
- [ ] `tests/test_cli_webview.py::TestWebviewLifecycle::test_serve_outlives_caller` — integration test that `lucy webview serve` returns promptly and the spawned server survives the caller (start_new_session detachment)
- [ ] pytest already installed — no framework install needed

*Existing pytest infrastructure covers the phase; only the new case.md grep tests + one lifecycle test are added.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CASE run auto-launches dashboard and prints URL + stop hint before first `[BEGIN]` | WV-07 / SC #1,#3 | Requires a FRESH Claude Code session to reload the edited `case.md` skill; full CASE orchestration is not unit-testable | In a fresh session, start a CASE run on a test dataset; confirm the orchestrator prints the dashboard URL + `lucy webview stop <analysis_dir>` hint before team work, and the server stays reachable after the run ends |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
