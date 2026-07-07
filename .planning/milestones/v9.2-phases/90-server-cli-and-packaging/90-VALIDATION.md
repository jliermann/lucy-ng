---
phase: 90
slug: server-cli-and-packaging
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-02
---

# Phase 90 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (already configured in `pyproject.toml` `[tool.pytest.ini_options]`) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/test_cli_webview.py -x -v` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~10–20 seconds for the webview file; full suite is longer |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_cli_webview.py -x -v`
- **After every plan wave:** Run `pytest` (full suite)
- **Before `/gsd-verify-work`:** Full suite green + `mypy src/lucy_ng` passes + `ruff check src tests` clean
- **Max feedback latency:** ~20 seconds (quick run)

---

## Per-Task Verification Map

| Requirement | Behavior | Test Type | Automated Command | File Exists |
|-------------|----------|-----------|-------------------|-------------|
| WV-08 | Core `lucy` CLI (`main.py`) imports cleanly without fastapi/uvicorn | unit | `pytest tests/test_cli_webview.py::TestImportSafety::test_main_importable_without_fastapi -x` | ❌ W0 |
| WV-08 | `webview serve` on a core-only install prints a friendly "install lucy-ng[webview]" error, not an ImportError traceback | unit (CliRunner) | `pytest tests/test_cli_webview.py::TestImportSafety::test_serve_without_webview_extra -x` | ❌ W0 |
| WV-08 | `[project.optional-dependencies] webview` present; core `[project.dependencies]` unchanged | unit (parse pyproject) | `pytest tests/test_cli_webview.py::TestPackaging::test_webview_extra_declared -x` | ❌ W0 |
| WV-01 | `/health` (root) endpoint returns `{"status": "ok"}` | unit (TestClient) | `pytest tests/test_cli_webview.py::TestWebviewApp::test_health_endpoint -x` | ❌ W0 |
| WV-01 | `serve` picks a free port when `--port` is omitted | unit | `pytest tests/test_cli_webview.py::TestFreePort::test_pick_free_port -x` | ❌ W0 |
| WV-01 | `serve` starts server, writes `.webview.json` (pid/port/url), prints URL | subprocess integration | `pytest tests/test_cli_webview.py::TestWebviewLifecycle::test_serve_writes_state_file -x` | ❌ W0 |
| WV-01 | Second `serve` on a live server returns the existing URL (idempotent, no double-bind) | subprocess integration | `pytest tests/test_cli_webview.py::TestWebviewLifecycle::test_serve_idempotent -x` | ❌ W0 |
| WV-02 | `stop` terminates server + removes `.webview.json`; port freed | subprocess integration | `pytest tests/test_cli_webview.py::TestWebviewLifecycle::test_stop_terminates -x` | ❌ W0 |
| WV-02 | `status` reports running when server is live | subprocess integration | `pytest tests/test_cli_webview.py::TestWebviewLifecycle::test_status_running -x` | ❌ W0 |
| WV-02 | `status` reports not running when no `.webview.json` | unit | `pytest tests/test_cli_webview.py::TestWebviewStatus::test_status_no_file -x` | ❌ W0 |
| WV-02 | `status` detects a stale `.webview.json` (dead pid) as not running | unit | `pytest tests/test_cli_webview.py::TestWebviewStatus::test_status_stale_pid -x` | ❌ W0 |

*Status legend: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky · ❌ W0 = file created in Wave 0.*

---

## Wave 0 Requirements

- [ ] `tests/test_cli_webview.py` — all test classes (TestImportSafety, TestPackaging, TestWebviewApp, TestFreePort, TestWebviewLifecycle, TestWebviewStatus)
- [ ] `tests/conftest.py` (already exists) — add a `webview_analysis_dir` fixture (tmp_path-based `analysis/` dir) and a `webview_server` fixture that starts/stops a real subprocess with guaranteed teardown cleanup (no orphan processes)

*Import-safety tests must guard against fastapi being present in the dev env: assert the CLI's top-level import graph does not pull in fastapi (e.g. `main.py` imports succeed and `sys.modules` has no `fastapi` after importing the CLI group), rather than uninstalling the package.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real `pip install lucy-ng` (core) succeeds without fastapi/uvicorn on a clean venv | WV-08 | Requires a clean virtualenv + network install; not run in unit suite | In a fresh venv: `pip install .` then `python -c "import lucy_ng.cli.main"` succeeds and `pip show fastapi` fails; `pip install .[webview]` then `lucy webview --help` works |
| `--open` flag opens the dashboard in a browser | WV-01 | Launches a real browser | `lucy webview serve <dir> --open` opens the URL in the default browser |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (`tests/test_cli_webview.py`, conftest fixtures)
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s (quick run)
- [ ] `nyquist_compliant: true` set in frontmatter once above are satisfied

**Approval:** pending
