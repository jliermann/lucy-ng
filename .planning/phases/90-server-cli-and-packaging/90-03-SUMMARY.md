---
phase: 90-server-cli-and-packaging
plan: 03
subsystem: webview
tags: [click, fastapi, uvicorn, optional-extra, import-safety, wave-2]

requires:
  - "90-01 (Wave 0 test scaffold)"
  - "90-02 (Wave 1 library modules: WebviewState, create_app, server lifecycle)"

provides:
  - "lucy webview serve/stop/status CLI commands with --format json support"
  - "Hidden _run subcommand as foreground uvicorn entrypoint for server.start"
  - "_require_webview() guard giving friendly install hint when extra absent"
  - "python -m lucy_ng.cli entrypoint for subprocess-launch fallback"
  - "lucy-ng[webview] optional extra in pyproject.toml (fastapi + uvicorn)"

affects:
  - "90-phase completion — all 11 webview tests green; WV-01/WV-02/WV-08 satisfied"
  - "92 (orchestrator integration) — can now call lucy webview serve from case.md"

tech-stack:
  added:
    - "cli/webview.py: Click group wrapping server.start/stop/status; lazy imports"
    - "cli/__main__.py: python -m lucy_ng.cli entry point"
    - "pyproject.toml: [project.optional-dependencies].webview = [fastapi>=0.100, uvicorn>=0.20]"
  patterns:
    - "Lazy imports inside command bodies (no top-level webview-extra imports in CLI module)"
    - "_require_webview() ImportError catch with click.ClickException and from exc chain"
    - "click.Path(path_type=Path) argument coercion to pathlib.Path"
    - "Hidden Click subcommand (_run) as internal IPC between CLI and server.start subprocess"

key-files:
  created:
    - "src/lucy_ng/cli/webview.py"
    - "src/lucy_ng/cli/__main__.py"
  modified:
    - "src/lucy_ng/cli/main.py"
    - "pyproject.toml"

key-decisions:
  - "raise click.ClickException(...) from exc in _require_webview() — ruff B904 requires chaining in except clause"
  - "Blank line separator between uvicorn import (third-party) and from lucy_ng.webview.app import (local) inside _run body — ruff I001 isort requirement"
  - "stop and status commands do NOT call _require_webview() — server.py/state.py are fastapi-free, so stop/status work even without the webview extra installed"

requirements-completed: [WV-01, WV-02, WV-08]

duration: 15min
completed: 2026-07-03
---

# Phase 90 Plan 03: Server CLI and Packaging — Wave 2 User-Facing Surface

**Click group (serve/stop/status/_run), python -m entrypoint, root CLI registration, and lucy-ng[webview] optional extra — all 11 webview tests green, WV-08 import safety confirmed.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-03T07:20:28Z
- **Completed:** 2026-07-03T07:35:28Z
- **Tasks:** 3
- **Files modified:** 4 (2 new, 2 modified)

## Accomplishments

- Created `src/lucy_ng/cli/webview.py` — Click group with `serve`/`stop`/`status` (all with `--format json`) and hidden `_run` foreground entrypoint; `_require_webview()` guard with exact `pip install lucy-ng[webview]` hint; zero top-level fastapi/uvicorn imports (WV-08)
- Created `src/lucy_ng/cli/__main__.py` — `python -m lucy_ng.cli` entry point; required by `server.start` subprocess fallback when `lucy` binary is not on PATH
- Modified `src/lucy_ng/cli/main.py` — imported and registered `webview` group; added docstring Commands entry
- Modified `pyproject.toml` — added `webview = ["fastapi>=0.100", "uvicorn>=0.20"]` under `[project.optional-dependencies]`; core `[project.dependencies]` unchanged
- All 11 webview tests green (4 Wave-1 tests + 7 new Wave-2 tests including subprocess lifecycle)
- Full suite: 1142 passed, 7 skipped, 1 xfailed — no regressions

## Task Commits

1. **Task 1: webview Click group (cli/webview.py)** — `cf1c90c` (feat)
2. **Task 2: python -m entrypoint + main.py registration** — `63f1142` (feat)
3. **Task 3: pyproject optional extra + ruff fixes** — `97a2831` (feat)

## Files Created/Modified

- `src/lucy_ng/cli/webview.py` — 162 lines; Click group, 4 commands, guard function; fully lazy imports
- `src/lucy_ng/cli/__main__.py` — 12 lines; python -m entrypoint
- `src/lucy_ng/cli/main.py` — added webview import, `cli.add_command(webview)`, docstring entry
- `pyproject.toml` — added `[project.optional-dependencies].webview` block (2 deps)

## Decisions Made

- `raise click.ClickException(...) from exc` — chaining required by ruff B904 in except clause
- `stop` and `status` do not call `_require_webview()` — correct because `server.stop/status` are fastapi-free; the guard is only needed when uvicorn must actually be launched
- `cli/__main__.py` uses `if __name__ == "__main__"` guard — correct for `python -m` execution context

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ruff B904: bare raise in except clause in _require_webview()**
- **Found during:** Task 3 (ruff check during acceptance criteria)
- **Issue:** `raise click.ClickException(...)` inside `except ImportError:` violated ruff B904 (exception chaining)
- **Fix:** Changed to `except ImportError as exc:` / `raise click.ClickException(...) from exc`
- **Files modified:** `src/lucy_ng/cli/webview.py`
- **Commit:** `97a2831`

**2. [Rule 1 - Bug] ruff I001: unsorted import block in _run body**
- **Found during:** Task 3 (ruff check during acceptance criteria)
- **Issue:** `import uvicorn` and `from lucy_ng.webview.app import create_app` were adjacent without the blank-line section separator ruff's isort requires between third-party and local imports
- **Fix:** `ruff check --fix` added blank line; standard isort section separator
- **Files modified:** `src/lucy_ng/cli/webview.py`
- **Commit:** `97a2831`

## Known Stubs

None. All commands have complete dispatch logic; no placeholder returns or TODO bodies.

## Threat Flags

No new security surface beyond the plan's threat register (T-90-08 through T-90-SC). Mitigations:
- T-90-08 path traversal: delegated to `server.start()` which does `Path.resolve() + is_dir()` (plan 90-02)
- T-90-09 arg injection: `server.start` uses LIST-form Popen (plan 90-02); `_run` args are typed Click options
- T-90-10 `_run` direct invocation: accepted; hidden command; loopback-only bind
- T-90-11 import safety: `_require_webview()` guard + WV-08 test confirmed fastapi never leaks into core CLI import

---
*Phase: 90-server-cli-and-packaging*
*Completed: 2026-07-03*
