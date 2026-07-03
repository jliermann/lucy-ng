---
phase: 90-server-cli-and-packaging
verified: 2026-07-03T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
re_verification: false
human_verification:
  - test: "Install the package in a clean virtualenv without the webview extra and confirm `lucy --help` works; then install with `.[webview]` and confirm `lucy webview serve` starts a server."
    expected: "`lucy --help` succeeds with no import errors in the core-only install; `lucy webview serve` starts a server and writes `.webview.json` in the `.[webview]` install."
    why_human: "Requires a clean environment. The test suite verifies pyproject.toml declarations and import-safety via subprocess/monkeypatch, but cannot simulate a bare pip install without the extra. The plan explicitly marked this check as manual-only."
---

# Phase 90: server-cli-and-packaging Verification Report

**Phase Goal:** Users can start, stop, and query a read-only webview server for any `analysis/` folder using `lucy webview` commands; the server package is isolated as an optional extra.
**Verified:** 2026-07-03
**Status:** human_needed
**Re-verification:** No — initial verification.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `lucy webview serve <analysis_dir>` starts a FastAPI/uvicorn server, writes `.webview.json` (pid/port/url), and prints the dashboard URL | VERIFIED | `server.start()` in `server.py:51-150` launches a detached subprocess via list-form `Popen`, writes state via `WebviewState.save()`; CLI `serve` command echoes the URL. `TestWebviewLifecycle::test_serve_writes_state_file` passes. |
| 2 | `lucy webview stop <analysis_dir>` terminates the server and removes `.webview.json`; `lucy webview status <analysis_dir>` reports running/stopped state | VERIFIED | `server.stop()` sends SIGTERM, polls 3 s, escalates to SIGKILL, removes state file. `server.status()` probes PID liveness and removes stale files. `TestWebviewLifecycle::test_stop_terminates` and `test_status_running` both pass. |
| 3 | Core `lucy` CLI does NOT import fastapi/uvicorn at top level (WV-08); a friendly `pip install lucy-ng[webview]` error appears when the extra is absent | VERIFIED | Subprocess check confirms `fastapi` absent from `sys.modules` after importing `lucy_ng.cli.main`. `_require_webview()` in `cli/webview.py` raises a `ClickException` with the exact install hint. `TestImportSafety::test_main_importable_without_fastapi` and `test_serve_without_webview_extra` both pass. |
| 4 | `pyproject.toml` declares the `lucy-ng[webview]` optional extra without adding fastapi/uvicorn to core dependencies | VERIFIED | `pyproject.toml` lines 57-60: `webview = ["fastapi>=0.100", "uvicorn>=0.20"]` under `[project.optional-dependencies]`. Neither appears in `[project.dependencies]`. `TestPackaging::test_webview_extra_declared` passes. |

**Score:** 4/4 truths verified.

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/lucy_ng/webview/__init__.py` | Package marker, no fastapi imports | VERIFIED | Docstring only; no imports |
| `src/lucy_ng/webview/state.py` | WebviewState Pydantic v2 model with create/save/load/is_alive | VERIFIED | 84 lines; all methods substantive; zero fastapi/uvicorn imports |
| `src/lucy_ng/webview/app.py` | `create_app(analysis_dir)` returning FastAPI with `/health` | VERIFIED | Only file in package with top-level `from fastapi import FastAPI`; `docs_url=None, redoc_url=None` |
| `src/lucy_ng/webview/server.py` | `_pick_free_port`, `start`, `stop`, `status` lifecycle functions | VERIFIED | 245 lines; list-form Popen; `start_new_session=True`; no shell=True; no top-level fastapi/uvicorn imports |
| `src/lucy_ng/cli/webview.py` | Click group with serve/stop/status/_run + `_require_webview` guard | VERIFIED | Friendly error message includes `pip install lucy-ng[webview]`; all fastapi/uvicorn imports are lazy (inside command bodies) |
| `src/lucy_ng/cli/__main__.py` | `python -m lucy_ng.cli` entrypoint | VERIFIED | `from lucy_ng.cli import cli; if __name__ == "__main__": cli()` |
| `src/lucy_ng/cli/main.py` | `webview` group registered on root `cli` | VERIFIED | `from lucy_ng.cli.webview import webview` + `cli.add_command(webview)` at line 64 |
| `pyproject.toml` | `[project.optional-dependencies].webview = [fastapi, uvicorn]` | VERIFIED | Lines 57-60; core deps unchanged |
| `tests/test_cli_webview.py` | 11 tests, 6 classes (Wave 0 scaffold) | VERIFIED | All 11 tests collected and pass: 11 passed |
| `tests/conftest.py` | `webview_analysis_dir` + `webview_server` fixtures | VERIFIED | Both fixtures present; no module-level fastapi/uvicorn imports |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/lucy_ng/cli/main.py` | `src/lucy_ng/cli/webview.py` | `from lucy_ng.cli.webview import webview; cli.add_command(webview)` | WIRED | Confirmed at main.py lines 19, 64 |
| `src/lucy_ng/cli/webview.py serve` | `lucy_ng.webview.server` | `import lucy_ng.webview.server as server; server.start(...)` | WIRED | Lazy import inside command body; confirmed at webview.py lines 70-72 |
| `src/lucy_ng/cli/webview.py stop` | `lucy_ng.webview.server` | `import lucy_ng.webview.server as server; server.stop(...)` | WIRED | Lazy import inside command body; confirmed at webview.py lines 98-100 |
| `src/lucy_ng/cli/webview.py status` | `lucy_ng.webview.server` | `import lucy_ng.webview.server as server; server.status(...)` | WIRED | Lazy import inside command body; confirmed at webview.py lines 123-125 |
| `src/lucy_ng/cli/webview.py _run` | `lucy_ng.webview.app.create_app + uvicorn.run` | lazy import inside `_run` body | WIRED | Confirmed at webview.py lines 157-162 |
| `src/lucy_ng/webview/server.py` | `src/lucy_ng/webview/state.py` | `from lucy_ng.webview.state import WebviewState` | WIRED | server.py line 27; state used throughout start/stop/status |
| `src/lucy_ng/webview/server.py start` | detached subprocess | `subprocess.Popen([...], start_new_session=True)` | WIRED | server.py lines 122-128; list-form args, no shell=True |

---

### Data-Flow Trace (Level 4)

Not applicable. Phase 90 implements a process-lifecycle engine and a skeleton FastAPI app. The only data rendered is from the `.webview.json` state file written by `WebviewState.save()` and read back by `WebviewState.load()`. Both paths are directly tested by `TestWebviewStatus` and `TestWebviewLifecycle`. No dynamic database queries or external data sources are involved at this phase.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `lucy_ng.cli.main` imports without loading fastapi | `python -c "import sys, lucy_ng.cli.main; assert 'fastapi' not in sys.modules"` | exit 0; fastapi absent | PASS |
| `python -m lucy_ng.cli webview --help` shows serve/stop/status | `python -m lucy_ng.cli webview --help` | Exits 0; lists serve, status, stop; `_run` hidden | PASS |
| `start_new_session=True` present; `shell=True` absent in server.py | `grep -c "start_new_session=True"` → 1; `grep -c "shell=True"` → 0 | 1 / 0 | PASS |
| Friendly install hint present in cli/webview.py | `grep -c "pip install lucy-ng\[webview\]"` → 1 | 1 | PASS |
| webview extra in pyproject, fastapi/uvicorn absent from core | `tomllib` parse | `webview=['fastapi>=0.100','uvicorn>=0.20']`; core clean | PASS |
| Full webview test suite | `pytest tests/test_cli_webview.py` | 11 passed | PASS |

---

### Probe Execution

No probe scripts (`scripts/*/tests/probe-*.sh`) are declared in this phase. Step 7c: SKIPPED.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| WV-01 | 90-01, 90-02, 90-03 | User can start a local dashboard with `lucy webview serve <dir>` | SATISFIED | `server.start()` + `cli/webview.py serve` + `TestWebviewLifecycle::test_serve_writes_state_file` |
| WV-02 | 90-01, 90-02, 90-03 | User can stop with `lucy webview stop <dir>` and check status with `lucy webview status <dir>` | SATISFIED | `server.stop()` + `server.status()` + corresponding CLI commands + `test_stop_terminates` + `test_status_running` |
| WV-08 | 90-01, 90-02, 90-03 | Webview ships as optional extra `lucy-ng[webview]`; core CLI stays fastapi-free | SATISFIED | `pyproject.toml` optional-dep declaration verified; `test_main_importable_without_fastapi` confirms no leak; `test_serve_without_webview_extra` confirms friendly error |

No orphaned requirements: REQUIREMENTS.md traceability table confirms WV-01, WV-02, WV-08 map exclusively to Phase 90; WV-03–WV-07 map to phases 91–92.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | No TBD/FIXME/XXX markers; no stubs or placeholders detected in any of the 10 phase-modified files |

All code review findings (CR-01, WR-01, WR-02, WR-03, WR-04) from `90-REVIEW.md` are addressed in the implementation:
- **CR-01 / WR-01** (PermissionError in stop poll + SIGTERM): both handled at `server.py:219-235, 240`
- **WR-02** (log_file fd leak): `log_file.close()` called at `server.py:131` immediately after `Popen`
- **WR-03** (corrupt state file crashes status/stop): `try/except Exception` wraps `WebviewState.load()` in both callers (`server.py:170-176, 205-210`)
- **WR-04** (PermissionError-as-alive blocks start): `is_alive()` returns `False` for `PermissionError` at `state.py:81-83` — a deliberate deviation from the original plan spec that treated `PermissionError` as alive; the implementation chose the safer "treat as not-ours = dead" semantics

---

### Human Verification Required

#### 1. Clean-venv install check

**Test:** Create a fresh virtualenv and install `lucy-ng` (core only, without extras). Run `lucy --help`. Then install `lucy-ng[webview]` in a separate virtualenv and run `lucy webview serve <analysis_dir>`.

**Expected:**
- Core install: `lucy --help` exits 0; `lucy webview serve` prints a friendly `pip install lucy-ng[webview]` message and exits non-zero (no raw ImportError traceback).
- `[webview]` install: `lucy webview serve <analysis_dir>` starts a server, prints a URL, writes `.webview.json`; `lucy webview stop <analysis_dir>` terminates it.

**Why human:** Requires a clean environment. Automated tests verify pyproject.toml declarations and import-safety via subprocess/monkeypatch, but cannot simulate an actual bare `pip install` without the optional extra from a fresh virtualenv. The plan explicitly declared this check "manual-only (not in automated gate)" in `90-03-PLAN.md` success criteria.

---

### Gaps Summary

No gaps. All four phase success criteria are met by substantive, wired, data-flowing implementations, verified by 11 passing automated tests and targeted spot-checks. The single human verification item is a supplementary clean-venv packaging confidence check that the plan itself designated manual-only.

---

_Verified: 2026-07-03_
_Verifier: Claude (gsd-verifier)_
