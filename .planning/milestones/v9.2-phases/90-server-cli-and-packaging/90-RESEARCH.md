# Phase 90: Server, CLI, and Packaging - Research

**Researched:** 2026-07-02
**Domain:** FastAPI/uvicorn background-server lifecycle, Click optional-extra guard, Python subprocess detachment, Pydantic v2 file model
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WV-01 | `lucy webview serve <dir>` starts a local dashboard server (free-port if omitted), writes `.webview.json` (pid/port/url), prints URL; idempotent on live server | subprocess Popen + socket free-port trick + PID liveness check |
| WV-02 | `lucy webview stop <dir>` terminates server + removes `.webview.json`; `lucy webview status <dir>` reports running/not | PID SIGTERM + os.kill(pid,0) liveness check |
| WV-08 | `pip install lucy-ng` succeeds without FastAPI/uvicorn; `pip install lucy-ng[webview]` adds them; core CLI stays import-safe | lazy-import guard in Click command body + `[project.optional-dependencies]` in pyproject |
</phase_requirements>

---

## Summary

Phase 90 delivers server infrastructure and CLI lifecycle management for the CASE Web-View dashboard. The work splits into three concerns: (1) extending the Click CLI with a new `webview` command group that lazy-imports FastAPI so core installs remain clean, (2) implementing a background server lifecycle using `subprocess.Popen` with `start_new_session=True` and a `.webview.json` state file, and (3) declaring the `lucy-ng[webview]` optional dependency set in `pyproject.toml` under hatchling.

The design spec and requirements are fully locked — FastAPI + uvicorn as an optional extra, server is "dumb" (reads files only), no JS build step, bind 127.0.0.1 only. Phase 90 delivers a minimal FastAPI skeleton with one health route so that the entire lifecycle (serve/stop/status/idempotency) is testable before Phase 91 adds the real endpoints.

**Primary recommendation:** Use `subprocess.Popen` with `start_new_session=True` to launch a hidden `lucy webview _run` subcommand. Pick a free port via the `socket.bind(('127.0.0.1', 0))` trick before launch. Model `.webview.json` with a Pydantic v2 `BaseModel`. Guard all fastapi/uvicorn imports inside Click command bodies with a `try/except ImportError` that prints a friendly "pip install lucy-ng[webview]" message.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Server lifecycle (start/stop/status) | CLI (`lucy webview` commands) | OS process model | CLI owns lifecycle; server is a plain OS process tracked by PID |
| Server process | Backend (uvicorn + FastAPI) | — | FastAPI serves HTTP; uvicorn is the ASGI runner |
| State persistence between CLI invocations | Filesystem (`.webview.json`) | Pydantic v2 model | JSON file in `analysis_dir` bridges independent `serve`/`stop`/`status` invocations |
| Optional dependency isolation | Python packaging (pyproject.toml) | Lazy import guard in CLI | hatchling optional-dependencies + try/except ImportError at call site |
| App code (routes) | Backend (`src/lucy_ng/webview/app.py`) | — | App factory pattern; Phase 91 adds routers without touching Phase 90 code |
| Health/test route | Backend (`GET /health`) | — | Thin skeleton so lifecycle is testable; real endpoints in Phase 91 |

---

## Standard Stack

### Core (webview extra only — NOT added to core dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.139.0 (current); `>=0.100` pin | ASGI web framework; app factory + router pattern | Already used in lucy-ng's broader ecosystem; native Pydantic v2 integration; aligns with design spec decision [VERIFIED: PyPI registry] |
| uvicorn | 0.49.0 (current); `>=0.20` pin | ASGI server running FastAPI; programmatic `uvicorn.run()` in subprocess | Standard uvicorn-as-runner pattern; ships with own `click` CLI integration [VERIFIED: PyPI registry] |

### Testing (dev extra — already present or add to dev)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | 0.28.1 (current, already installed) | Required transport for FastAPI `TestClient`; Starlette's TestClient uses httpx as its ASGI transport | Required for any FastAPI TestClient usage [VERIFIED: PyPI registry + confirmed importable] |

`httpx` is already installed in the dev environment and is pulled in transitively by `starlette`. For the `dev` optional-dependencies in `pyproject.toml`, no change is needed — it arrives as a transitive dependency of `fastapi[webview]`.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `subprocess.Popen` + `_run` subcommand | `multiprocessing.Process` | multiprocessing is harder to track across CLI invocations (no persistent PID outside the process); Popen + PID file is the standard daemon pattern |
| `subprocess.Popen` + `_run` subcommand | direct `uvicorn.run()` in same process | Blocks the CLI; user cannot get back the shell prompt |
| `socket.bind(('127.0.0.1', 0))` free port | `--port 0` to uvicorn | uvicorn does not report the chosen port back to the caller over stdout in a machine-readable way; pre-binding in the parent is simpler [ASSUMED] |
| Pydantic v2 model for `.webview.json` | plain `dict` + `json.dumps` | Pydantic gives mypy-strict type safety for free; project already uses Pydantic v2 everywhere; marginal cost |

**Installation (webview extra):**
```bash
pip install lucy-ng[webview]
```

Which installs: `fastapi>=0.100` and `uvicorn>=0.20` (and their transitive deps: starlette, pydantic, h11, httpx).

---

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| fastapi | PyPI | ~6 yrs | very high (>100M/month) | github.com/fastapi/fastapi | [OK] | Approved |
| uvicorn | PyPI | ~6 yrs | very high | github.com/encode/uvicorn | [OK] | Approved |
| httpx | PyPI | ~5 yrs | very high | github.com/encode/httpx | [OK] | Approved |

**slopcheck result:** All 3 packages returned `[OK]`. Slopcheck ran with `slopcheck install fastapi uvicorn httpx` and found all clean. [VERIFIED: slopcheck 0.6.1 run 2026-07-02]

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
lucy webview serve <analysis_dir>
        |
        v
[serve command]
   1. Lazy-import guard (try fastapi/uvicorn, else print help + exit 1)
   2. Resolve analysis_dir to absolute Path
   3. Check .webview.json -> if exists, check PID liveness
      - alive  ->  print existing URL, exit 0 (IDEMPOTENT)
      - dead   ->  remove stale .webview.json, continue
   4. Pick free port: socket.bind(('127.0.0.1', 0)) -> getsockname()[1] -> close
   5. Write .webview.json (pid=placeholder, port=N, ...)
   6. Popen(["lucy", "webview", "_run", analysis_dir, "--port", N, "--host", "127.0.0.1"],
            start_new_session=True, stdout=log_file, stderr=STDOUT)
   7. Update .webview.json with real PID from Popen.pid
   8. Print URL to user
        |
        v
[_run subcommand — runs in subprocess, foreground from its perspective]
   import fastapi, uvicorn
   app = create_app(analysis_dir)
   uvicorn.run(app, host="127.0.0.1", port=N, log_level="warning")
        |
        v
[FastAPI app — src/lucy_ng/webview/app.py]
   GET /health  ->  {"status": "ok", "analysis_dir": "..."}
   (Phase 91 adds routers for /api/status, /api/structures, /api/log, GET /)

lucy webview stop <analysis_dir>
   Read .webview.json -> pid, send SIGTERM, wait up to 3s, remove file

lucy webview status <analysis_dir>
   Read .webview.json -> pid, os.kill(pid, 0), report running/not
```

### Recommended Project Structure

```
src/lucy_ng/
├── cli/
│   ├── main.py          # add: from lucy_ng.cli.webview import webview; cli.add_command(webview)
│   └── webview.py       # NEW: Click group + serve/stop/status/_run subcommands
└── webview/             # NEW: server package
    ├── __init__.py      # empty or re-exports create_app
    ├── app.py           # create_app(analysis_dir: Path) -> FastAPI; health route
    └── models.py        # WebviewState Pydantic v2 model + load/save helpers

tests/
└── test_cli_webview.py  # NEW: lifecycle + app tests
```

The `webview/` sub-package isolates FastAPI code so it is never imported by the core package tree. Only `cli/webview.py` touches it, and only inside command bodies.

### Pattern 1: Click Group with Lazy Import Guard

The existing codebase pattern (from `database.py`) shows `from lucy_ng.prediction.hose import HOSEGEN_AVAILABLE` inside the command body. The `webview` group follows the same pattern but wraps the entire import:

```python
# src/lucy_ng/cli/webview.py
from __future__ import annotations

from pathlib import Path
import click


@click.group()
def webview() -> None:
    """Webview dashboard server commands."""


def _require_webview() -> None:
    """Raise a friendly error if the webview extra is not installed."""
    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError:
        raise click.ClickException(
            "The webview extra is not installed.\n"
            "Install with: pip install lucy-ng[webview]"
        )


@webview.command("serve")
@click.argument("analysis_dir", type=click.Path(path_type=Path))
@click.option("--port", "-p", type=int, default=None, help="Port (default: auto)")
@click.option("--host", default="127.0.0.1", show_default=True, help="Bind host")
@click.option("--open", "open_browser", is_flag=True, help="Open browser after start")
@click.option("--format", "output_format", type=click.Choice(["text", "json"]),
              default="text", help="Output format")
def webview_serve(
    analysis_dir: Path, port: int | None, host: str, open_browser: bool, output_format: str
) -> None:
    """Start the webview dashboard for ANALYSIS_DIR."""
    _require_webview()
    # ... implementation using subprocess.Popen
```

**Registration in `main.py`** — add two lines following the existing pattern:

```python
from lucy_ng.cli.webview import webview  # top-level import is SAFE — no fastapi import here

cli.add_command(webview)
```

This is safe because `webview.py` itself does not import fastapi at module level.

### Pattern 2: Free-Port Acquisition

```python
# Source: Python stdlib socket docs [ASSUMED pattern — well-known technique]
import socket

def _pick_free_port(host: str = "127.0.0.1") -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
```

Confirmed working on darwin (verified in this session by running the socket bind pattern).

### Pattern 3: Background Process Launch

```python
import subprocess
import sys
import os

proc = subprocess.Popen(
    ["lucy", "webview", "_run",
     str(analysis_dir.resolve()),
     "--port", str(port),
     "--host", host],
    start_new_session=True,        # detach from parent's process group
    stdout=open(log_path, "w"),    # capture uvicorn logs to analysis_dir/.webview.log
    stderr=subprocess.STDOUT,
    close_fds=True,
)
```

`start_new_session=True` is the macOS/Linux equivalent of `daemon=True` for subprocesses. The child survives the parent CLI exiting. `close_fds=True` is good hygiene.

The `_run` hidden subcommand:

```python
@webview.command("_run", hidden=True, deprecated=False)
@click.argument("analysis_dir", type=click.Path(path_type=Path))
@click.option("--port", "-p", type=int, required=True)
@click.option("--host", default="127.0.0.1")
def webview_run_server(analysis_dir: Path, port: int, host: str) -> None:
    """Internal: run uvicorn in the foreground (called by 'serve' subprocess)."""
    import uvicorn
    from lucy_ng.webview.app import create_app
    app = create_app(analysis_dir.resolve())
    uvicorn.run(app, host=host, port=port, log_level="warning")
```

### Pattern 4: PID Liveness Check + Idempotency

```python
import os
import signal
from pathlib import Path
from lucy_ng.webview.models import WebviewState

def _is_server_alive(state: WebviewState) -> bool:
    """Check if the server process is still running."""
    try:
        os.kill(state.pid, 0)  # signal 0 = probe only, no actual signal
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # process exists but we can't signal it

def _check_idempotent_or_clear(analysis_dir: Path) -> WebviewState | None:
    """Return existing state if server is alive, else remove stale file and return None."""
    state_file = analysis_dir / ".webview.json"
    if not state_file.exists():
        return None
    state = WebviewState.model_validate_json(state_file.read_text())
    if _is_server_alive(state):
        return state  # caller should print existing URL and exit
    # Stale file — server died without cleanup
    state_file.unlink()
    return None
```

### Pattern 5: `.webview.json` Pydantic Model

```python
# src/lucy_ng/webview/models.py
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel


class WebviewState(BaseModel):
    """Persistent state written to <analysis_dir>/.webview.json."""
    pid: int
    port: int
    host: str
    url: str
    analysis_dir: str      # absolute path, stored as str for JSON portability
    started_at: str        # ISO 8601 UTC, e.g. "2026-07-02T14:30:00Z"

    @classmethod
    def create(cls, pid: int, port: int, host: str, analysis_dir: Path) -> "WebviewState":
        url = f"http://{host}:{port}"
        return cls(
            pid=pid,
            port=port,
            host=host,
            url=url,
            analysis_dir=str(analysis_dir.resolve()),
            started_at=datetime.now(tz=timezone.utc).isoformat(),
        )

    def save(self, analysis_dir: Path) -> None:
        (analysis_dir / ".webview.json").write_text(self.model_dump_json(indent=2))
```

Pydantic v2 `BaseModel` + `model_validate_json` + `model_dump_json` = mypy --strict compatible with no extra decorators needed.

### Pattern 6: Minimal FastAPI App Skeleton

```python
# src/lucy_ng/webview/app.py
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI


def create_app(analysis_dir: Path) -> FastAPI:
    """Create the webview FastAPI application for a given analysis directory.

    Phase 91 docks additional routers here via app.include_router().
    """
    app = FastAPI(title="lucy-ng webview", docs_url=None, redoc_url=None)
    analysis_dir = analysis_dir.resolve()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "analysis_dir": str(analysis_dir)}

    return app
```

`docs_url=None, redoc_url=None` suppresses the auto-generated Swagger/ReDoc UIs (not needed for a minimal server).

### Anti-Patterns to Avoid

- **Top-level fastapi import in `cli/webview.py`:** `import fastapi` at module level causes `ImportError` on core installs when `main.py` imports the `webview` group. All fastapi/uvicorn imports MUST be inside command function bodies or behind `_require_webview()`.
- **Using `uvicorn --reload` in the background subprocess:** `--reload` spawns additional watcher processes and makes PID tracking unreliable. Never pass `reload=True` to `uvicorn.run()`.
- **Checking only `.webview.json` existence without PID liveness:** Stale files (left by crashed servers) will cause `serve` to incorrectly report "already running". Always call `os.kill(pid, 0)`.
- **Registering `webview` in `main.py` with a lazy import:** `cli.add_command(webview)` requires the `webview` group object at import time — that is fine since `webview.py` itself does not import fastapi. Only the Click group object needs to be importable, not the framework.
- **Popen without `start_new_session=True` on macOS/Linux:** Without it, the child process is in the same process group as the terminal and receives SIGINT/SIGHUP when the terminal closes.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ASGI web server | Custom TCP socket server | `uvicorn` | Handles keep-alive, async, graceful shutdown, signal handling |
| HTTP routing + request parsing | Manual request dispatch | `FastAPI` | Type-safe routing, automatic JSON serialization, Pydantic integration |
| JSON test client for ASGI | Custom test transport | `fastapi.testclient.TestClient` (uses httpx under the hood) | Synchronous ASGI test client; no real HTTP socket needed |
| Optional dependency guard | Custom `importlib` probing | `try: import X / except ImportError: raise click.ClickException(...)` | Standard Python pattern; works with mypy --strict |
| Process liveness check | Port scan or `/proc/` parsing | `os.kill(pid, 0)` | Portable POSIX signal-0 probe; works on macOS and Linux |

**Key insight:** Every piece of server infrastructure in this phase has a well-established Python stdlib or ecosystem solution. The only custom code is the lifecycle coordination (`.webview.json` read/write, PID probe, subprocess launch) — which is 50-80 lines, not a framework.

---

## Common Pitfalls

### Pitfall 1: Stale `.webview.json` Causes False "Already Running"

**What goes wrong:** The server process crashes (or is killed with SIGKILL) without removing `.webview.json`. The next `serve` sees the file, reads the PID, but the process is gone. Without a liveness check, `serve` incorrectly returns the old URL.

**Why it happens:** The `stop` command gracefully removes `.webview.json`, but SIGKILL, reboot, or system crash bypasses the cleanup.

**How to avoid:** Always check `os.kill(pid, 0)` before treating an existing `.webview.json` as live. If the PID is dead, remove the file and proceed with a fresh server start.

**Warning signs:** `lucy webview status` reports "running" but the URL doesn't respond in a browser.

---

### Pitfall 2: ImportError at `lucy --help` on Core Installs

**What goes wrong:** `main.py` does `from lucy_ng.cli.webview import webview` at the top level. If `webview.py` has `import fastapi` at module level, a core install (without the webview extra) raises `ImportError` on every `lucy` invocation, including `lucy --help`.

**Why it happens:** Python eagerly evaluates top-level imports.

**How to avoid:** `lucy_ng/cli/webview.py` must contain ZERO top-level imports of fastapi or uvicorn. The `_require_webview()` guard (inside each command body) is the only import site. Verify with: `python -c "from lucy_ng.cli.webview import webview"` on a core install.

**Warning signs:** Existing `test_cli_main.py::test_all_command_groups_registered` fails if the import is accidental.

---

### Pitfall 3: Port Race Condition Between Free-Port Selection and Subprocess Bind

**What goes wrong:** `_pick_free_port()` closes the socket, then launches the subprocess. Another process grabs the same port before uvicorn can bind it. The subprocess dies immediately; `.webview.json` contains a port no one is listening on.

**Why it happens:** There is an inherent TOCTOU gap between "find free port" and "bind port."

**How to avoid:** For a local-only development tool on a low-port-pressure machine, this is extremely rare and acceptable. Mitigate by keeping the Popen call immediately after `_pick_free_port()` (no I/O between them). Add a brief startup poll: after Popen, sleep 0.5s and check if the process is still alive before printing the URL. If it died (returncode set), report an error and try again.

**Warning signs:** `serve` prints a URL but `status` immediately reports "not running."

---

### Pitfall 4: `stop` Leaves a Zombie if Process Is Slow to Exit

**What goes wrong:** `os.kill(pid, signal.SIGTERM)` is sent, then `.webview.json` is immediately removed. The process is still in its shutdown sequence. A subsequent `status` correctly shows "not running" (file gone), but if `stop` is called again immediately, it tries to signal a pid that may still exist.

**Why it happens:** uvicorn takes up to ~1 second to shut down cleanly (draining connections).

**How to avoid:** After SIGTERM, poll with `os.kill(pid, 0)` in a short loop (e.g., 5 × 0.2s). If still alive after 1s, send SIGKILL. Remove `.webview.json` only after the process exits or after SIGKILL. Use `proc.wait(timeout=3)` if the pid is tracked via a live `Popen` object, but since `stop` reads the PID from file, use `os.waitpid(pid, os.WNOHANG)` in a loop.

---

### Pitfall 5: `lucy webview _run` Visible in `lucy webview --help`

**What goes wrong:** Users see the internal `_run` command in `lucy webview --help` output and try to invoke it directly, causing confusion.

**Why it happens:** Click shows all registered subcommands by default.

**How to avoid:** Decorate `_run` with `@webview.command("_run", hidden=True)`. Click's `hidden=True` suppresses it from `--help` output while keeping it invocable.

---

### Pitfall 6: Hatchling Does Not Include Future Static Assets Without Configuration

**What goes wrong:** Phase 91 will add `src/lucy_ng/webview/static/index.html`. If `pyproject.toml` doesn't declare the static directory as an artifact, `hatch build` will skip it.

**Why it happens:** Hatchling includes Python files (`*.py`) by default but not non-Python assets unless declared in `[tool.hatch.build.targets.wheel]`.

**How to avoid (note for Phase 91):** In Phase 91, add to `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/lucy_ng"]
artifacts = [
    "src/lucy_ng/data/schemas/*",
    "src/lucy_ng/lsd/filters/*",
    "src/lucy_ng/webview/static/*",   # <-- Phase 91 adds this
]
```
Phase 90 does not have static assets, so no pyproject change is needed now — but the planner should note this as a prerequisite for Phase 91.

---

## Code Examples

### Pyproject.toml Changes (Phase 90)

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "ruff>=0.1",
    "mypy>=1.0",
]
prediction = [
    # ... unchanged
]
webview = [
    "fastapi>=0.100",
    "uvicorn>=0.20",
]
```

No changes to `[project.dependencies]` (core deps). No changes to `[tool.hatch.build.targets.wheel]` in Phase 90.

### Full `lucy webview stop` Implementation Sketch

```python
@webview.command("stop")
@click.argument("analysis_dir", type=click.Path(path_type=Path))
@click.option("--format", "output_format", type=click.Choice(["text", "json"]),
              default="text")
def webview_stop(analysis_dir: Path, output_format: str) -> None:
    """Stop the webview server for ANALYSIS_DIR."""
    import os, signal, time
    state_file = analysis_dir / ".webview.json"
    if not state_file.exists():
        if output_format == "json":
            click.echo('{"running": false, "message": "No server found"}')
        else:
            click.echo("No webview server running for this directory.")
        return

    from lucy_ng.webview.models import WebviewState
    state = WebviewState.model_validate_json(state_file.read_text())

    try:
        os.kill(state.pid, signal.SIGTERM)
    except ProcessLookupError:
        state_file.unlink(missing_ok=True)
        click.echo("Server was not running (stale state file removed).")
        return

    # Wait for clean shutdown (up to 3s)
    for _ in range(15):
        time.sleep(0.2)
        try:
            os.kill(state.pid, 0)
        except ProcessLookupError:
            break
    else:
        os.kill(state.pid, signal.SIGKILL)

    state_file.unlink(missing_ok=True)
    if output_format == "json":
        click.echo('{"stopped": true}')
    else:
        click.echo(f"Webview server stopped (was pid {state.pid}).")
```

### FastAPI TestClient Usage (for tests)

```python
# Source: FastAPI official docs — TestClient is from starlette, uses httpx transport
from fastapi.testclient import TestClient
from pathlib import Path
from lucy_ng.webview.app import create_app

def test_health(tmp_path: Path) -> None:
    app = create_app(tmp_path)
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (already configured in pyproject.toml) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_cli_webview.py -x -v` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WV-01 | `serve` starts server, writes `.webview.json`, prints URL | subprocess integration | `pytest tests/test_cli_webview.py::TestWebviewLifecycle::test_serve_writes_state_file -x` | Wave 0 |
| WV-01 | `serve` picks a free port when `--port` is omitted | unit | `pytest tests/test_cli_webview.py::TestFreePort::test_pick_free_port -x` | Wave 0 |
| WV-01 | Second `serve` on a live server returns existing URL (idempotent) | subprocess integration | `pytest tests/test_cli_webview.py::TestWebviewLifecycle::test_serve_idempotent -x` | Wave 0 |
| WV-02 | `stop` terminates server + removes `.webview.json` | subprocess integration | `pytest tests/test_cli_webview.py::TestWebviewLifecycle::test_stop_terminates -x` | Wave 0 |
| WV-02 | `status` reports running when server is live | subprocess integration | `pytest tests/test_cli_webview.py::TestWebviewLifecycle::test_status_running -x` | Wave 0 |
| WV-02 | `status` reports not running when no server | unit | `pytest tests/test_cli_webview.py::TestWebviewStatus::test_status_no_file -x` | Wave 0 |
| WV-02 | `status` detects stale `.webview.json` as not running | unit | `pytest tests/test_cli_webview.py::TestWebviewStatus::test_status_stale_pid -x` | Wave 0 |
| WV-08 | Core `lucy` CLI (`main.py`) imports cleanly without fastapi | unit | `pytest tests/test_cli_webview.py::TestImportSafety::test_main_importable_without_fastapi -x` | Wave 0 |
| WV-08 | `webview serve` on core install prints friendly error | unit (CliRunner mock) | `pytest tests/test_cli_webview.py::TestImportSafety::test_serve_without_webview_extra -x` | Wave 0 |
| WV-01 | `/health` endpoint returns `{"status": "ok"}` | unit (TestClient) | `pytest tests/test_cli_webview.py::TestWebviewApp::test_health_endpoint -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_cli_webview.py -x -v`
- **Per wave merge:** `pytest` (full suite)
- **Phase gate:** full suite green + `mypy src/lucy_ng` passes before `/gsd-verify-work`

### Wave 0 Gaps

All test infrastructure for this phase must be created from scratch:

- [ ] `tests/test_cli_webview.py` — all test classes above (lifecycle, import safety, app unit tests)
- [ ] `tests/conftest.py` already exists; add a `webview_analysis_dir` fixture (tmp_path-based `analysis/` directory) and a `webview_server` fixture that starts/stops a real subprocess with teardown cleanup

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| fastapi | webview app + tests | Yes (already installed) | 0.128.2 installed (0.139.0 current on PyPI) | Install via `[webview]` extra |
| uvicorn | subprocess server runner | Yes (already installed) | 0.40.0 installed (0.49.0 current) | Install via `[webview]` extra |
| httpx | FastAPI TestClient transport | Yes (already installed) | 0.28.1 | None needed — already present |
| socket (stdlib) | free-port acquisition | Yes | stdlib | None needed |
| os/signal (stdlib) | PID lifecycle | Yes | stdlib | None needed |

**Missing dependencies with no fallback:** none
**Missing dependencies with fallback:** none — all required packages already present in the dev environment

---

## Security Domain

> The webview server binds to `127.0.0.1` only (local loopback). This is a local-only observability tool. No authentication, no remote access, no mutation of data.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Not applicable — local-only, no user accounts |
| V3 Session Management | No | No sessions; stateless read-only API |
| V4 Access Control | No | Localhost bind is the access control; no user roles |
| V5 Input Validation | Partial | `analysis_dir` path: resolve to absolute + verify it exists; never pass raw user input to shell |
| V6 Cryptography | No | No encryption needed for 127.0.0.1-only service |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via `analysis_dir` argument | Tampering | Resolve path with `Path.resolve()` + verify it is a directory before starting server |
| Subprocess injection via `analysis_dir` in `Popen` args | Tampering | Pass as list argument to `Popen`, never via shell=True; `str(Path.resolve())` is safe in a list |
| Port squatting (another process binds the chosen port before uvicorn) | Denial of Service | Detect startup failure by polling the subprocess returncode 0.5s after launch |

---

## Open Questions

1. **`lucy` on PATH vs `sys.executable -m lucy_ng.cli`**
   - What we know: `subprocess.Popen(["lucy", "webview", "_run", ...])` requires `lucy` to be on PATH (it is, for any normal `pip install`). Using `sys.executable -m lucy_ng.cli` is more explicit but less ergonomic.
   - What's unclear: editable installs (`pip install -e .`) always put `lucy` on PATH via the entrypoint script; this should be fine.
   - Recommendation: Use `["lucy", "webview", "_run", ...]` for clarity. Add a fallback: if `shutil.which("lucy")` is None, fall back to `[sys.executable, "-m", "lucy_ng.cli", "webview", "_run", ...]`. [ASSUMED — need to verify `lucy_ng.cli` is a valid `__main__` entrypoint or add one]

2. **`--format json` on `serve` and `stop`**
   - What we know: every existing Lucy subcommand supports `--format json`. The design spec doesn't call it out for `webview`, but consistency is a project convention.
   - What's unclear: the `serve` command's output is already structured (URL + pid), making `--format json` straightforward.
   - Recommendation: Add `--format json` to `serve` (outputs `{"url": "...", "pid": N, "port": N}`) and `stop` (outputs `{"stopped": true, "pid": N}`) and `status` (outputs `{"running": true/false, "url": "...", "pid": N}`). This is consistent with the existing codebase and makes the commands orchestrator-friendly for Phase 92.

3. **`.webview.json` written before or after subprocess PID is known**
   - What we know: We need the PID to write the file. `Popen.pid` is available immediately after `Popen()` returns (before the subprocess actually starts).
   - Recommendation: Pick port, launch Popen, write `.webview.json` with `Popen.pid`. This is a one-shot write, not a two-phase update. No ambiguity.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `uvicorn` does not expose the bound port via stdout in machine-readable form, making pre-binding in the parent the simplest approach | Standard Stack | Low — if uvicorn exposes this, we could let the subprocess pick the port and signal back; but pre-binding is simpler |
| A2 | `lucy webview _run` is invocable via `subprocess.Popen(["lucy", ...])` on all install modes | Code Examples | Low — `pip install -e .` always installs entry points on PATH |
| A3 | `lucy_ng.cli` is not a valid `python -m lucy_ng.cli` entrypoint (no `__main__.py` in `src/lucy_ng/cli/`) | Open Questions | Low — fallback to `sys.executable -m lucy_ng.cli` needs a `__main__.py` or the `lucy` script path |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `requests`-based TestClient (Starlette < 0.20) | `httpx`-based TestClient (Starlette >= 0.20) | ~2022 | `httpx` must be importable for tests; already installed |
| `uvicorn` `--reload` for development | `uvicorn.run(reload=False)` for embedded/background use | n/a | Never use `--reload` in a subprocess that is PID-tracked |
| FastAPI auto-generates Swagger at `/docs` | `docs_url=None, redoc_url=None` to suppress | n/a | Suppress in the minimal skeleton; Phase 91 can re-enable if desired |

---

## Sources

### Primary (HIGH confidence)

- PyPI registry — `pip index versions fastapi` (0.139.0 current, 0.128.2 installed), `pip index versions uvicorn` (0.49.0 current, 0.40.0 installed), `pip index versions httpx` (0.28.1)
- Python stdlib `socket`, `os`, `signal`, `subprocess` — well-known POSIX patterns
- FastAPI `TestClient` verified importable and functional: `python -c "from fastapi.testclient import TestClient"` + smoke test against a live app in session
- slopcheck 0.6.1: all 3 packages [OK]
- Confirmed `socket.bind(('127.0.0.1', 0))` free-port trick works on darwin 25.5.0 in this session

### Secondary (MEDIUM confidence)

- Project codebase: `src/lucy_ng/cli/main.py`, `database.py`, `lsd.py` — confirmed CLI patterns, `--format json` convention, lazy-import-inside-command-body precedent (`database.py` `generate-hose-stats` imports `time` and prediction modules inside command body)
- `pyproject.toml` — confirmed `[project.optional-dependencies]` section already exists with `dev` and `prediction` entries; hatchling build backend confirmed

### Tertiary (LOW confidence)

- none

---

## Metadata

**Confidence breakdown:**
- Standard stack (fastapi, uvicorn, httpx): HIGH — all verified on PyPI, slopcheck OK, already installed
- CLI integration pattern: HIGH — read actual source of `main.py`, `database.py`, `lsd.py`
- Background subprocess lifecycle: HIGH — subprocess + signal patterns are stdlib, free-port trick verified on darwin
- Pydantic v2 model for `.webview.json`: HIGH — Pydantic v2 already used throughout project
- Pyproject optional-dependencies declaration: HIGH — existing `dev` extra follows identical pattern
- Import safety analysis: HIGH — read `main.py` top-level imports; confirmed lazy-import-inside-command precedent in codebase

**Research date:** 2026-07-02
**Valid until:** 2026-08-02 (stable stack; FastAPI/uvicorn are not fast-moving for this use case)
