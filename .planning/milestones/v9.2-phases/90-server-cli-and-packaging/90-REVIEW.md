---
phase: 90-server-cli-and-packaging
reviewed: 2026-07-03T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - pyproject.toml
  - src/lucy_ng/cli/__main__.py
  - src/lucy_ng/cli/main.py
  - src/lucy_ng/cli/webview.py
  - src/lucy_ng/webview/__init__.py
  - src/lucy_ng/webview/app.py
  - src/lucy_ng/webview/server.py
  - src/lucy_ng/webview/state.py
  - tests/conftest.py
  - tests/test_cli_webview.py
findings:
  critical: 1
  warning: 4
  info: 2
  total: 7
status: issues_found
---

# Phase 90: Code Review Report

**Reviewed:** 2026-07-03
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Phase 90 introduces the `lucy webview` CLI group, a FastAPI/uvicorn server factory
(`webview/app.py`), a process-lifecycle engine (`webview/server.py`), a Pydantic state
model (`webview/state.py`), a `python -m lucy_ng.cli` entrypoint (`cli/__main__.py`),
and a `lucy-ng[webview]` optional dependency extra.

The WV-08 import-safety invariant (no top-level fastapi/uvicorn in the core CLI path)
is correctly implemented — the chain `cli/__init__.py` → `cli/main.py` → `cli/webview.py`
carries no module-level fastapi/uvicorn imports, and all lazy imports are deferred to
command body scope or inside `_require_webview()`.

The main correctness concern is in the process-lifecycle engine (`server.py`): PID-based
process tracking without identity verification creates a window where `stop()` can send
SIGKILL to an unrelated process when PID reuse occurs. Supporting robustness issues include
uncaught `PermissionError` in several signal-related paths, a `log_file` fd leak, and
missing error handling for corrupt state files.

---

## Critical Issues

### CR-01: `stop()` can SIGKILL an unrelated process on same-user PID reuse

**File:** `src/lucy_ng/webview/server.py:207-218`
**Issue:** `stop()` sends `SIGTERM` to the recorded PID without first verifying the process
is the webview server. If the server crashes and the OS recycles its PID to a different
process owned by the same user (both conditions reachable in a long-running dev session),
`SIGTERM` lands on the wrong process. The poll loop (`range(15)`) does not catch
`PermissionError`, so if the wrong process does not exit voluntarily on `SIGTERM`, the
for-else escalation fires `SIGKILL` — killing an innocent user process.

Concretely, `os.kill(pid, 0)` in the poll body raises:
- `ProcessLookupError` → `break` (correct)
- `PermissionError` → **not handled** — loop does not break; after 3 s, `SIGKILL` is sent

For a different-user recycled PID, `SIGKILL` raises `PermissionError` which is NOT caught
by `except ProcessLookupError: pass`, propagating as an unhandled exception to the CLI.

**Fix:** Catch `PermissionError` in the poll loop to prevent escalation to SIGKILL when
the target process is not owned by the current user; additionally catch it on the SIGKILL
call itself:

```python
# Poll up to ~3 s for the process to exit.
for _ in range(15):
    time.sleep(0.2)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        break  # Process has exited.
    except PermissionError:
        # PID recycled to another user's process — abort escalation rather
        # than sending SIGKILL to the wrong target.
        break
else:
    # Process still alive after 3 s — escalate to SIGKILL.
    try:
        os.kill(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass  # Died between poll and SIGKILL, or belongs to different user.
```

Note: same-user PID reuse (where SIGTERM silently succeeds on the wrong process) requires
storing process creation time in the state file for reliable defense; the fix above covers
the different-user case which is both more likely and currently causes a hard crash.

---

## Warnings

### WR-01: `PermissionError` unhandled in the `stop()` SIGTERM call — leaves stale state file

**File:** `src/lucy_ng/webview/server.py:199-204`
**Issue:** The initial `os.kill(pid, signal.SIGTERM)` only catches `ProcessLookupError`.
If the PID was recycled to a process owned by a different user, `PermissionError` is
raised, propagates unhandled through `stop()` to the Click layer, and `.webview.json` is
never cleaned up. The user gets a Python traceback from `lucy webview stop`, and the stale
state file remains, making subsequent `lucy webview start` calls believe a server is running
(via `is_alive()` returning `True` for `PermissionError` — see WR-04).

**Fix:**
```python
try:
    os.kill(pid, signal.SIGTERM)
except ProcessLookupError:
    state_file.unlink(missing_ok=True)
    return (False, pid)
except PermissionError:
    # PID belongs to another user; treat as dead from our perspective.
    state_file.unlink(missing_ok=True)
    return (False, pid)
```

---

### WR-02: `log_file` file descriptor leaked in `start()`

**File:** `src/lucy_ng/webview/server.py:120`
**Issue:** `log_file = open(log_path, "w")` is opened and passed to `Popen` as `stdout`,
but the parent-side file descriptor is never closed:

- **Error path** (`proc.poll() is not None`, lines 133-143): `log_file.flush()` is called
  but the fd is not closed before `raise RuntimeError(...)`.
- **Success path** (line 148): `log_file` goes out of scope with the fd still open; CPython
  GC will eventually close it, but on PyPy or in tight loops this is a real leak.

The subprocess inherits its own fd to the log file (fd 1) via `stdout=log_file`. The parent
copy of the fd is redundant after `Popen` returns and should be closed immediately.

**Fix:**
```python
proc = subprocess.Popen(
    cmd,
    start_new_session=True,
    stdout=log_file,
    stderr=subprocess.STDOUT,
    close_fds=True,
)
log_file.close()  # Parent copy no longer needed; subprocess keeps its own fd.
```

In the error path, `log_path.read_text()` already reads via a separate file open, so
closing `log_file` first is safe.

---

### WR-03: `WebviewState.load()` has no error handling — corrupt state file crashes `status()` and `stop()`

**File:** `src/lucy_ng/webview/state.py:63-65`
**Issue:** `WebviewState.load()` calls `model_validate_json()` on the raw file content with
no error handling. A partial write (e.g., disk-full mid-save), external corruption, or a
`.webview.json` left by an older version of the code will raise `pydantic.ValidationError`
or `json.JSONDecodeError`, which propagates unhandled through both callers:

- `server.status()` line 168 — crashes instead of returning `None` and removing the file.
- `server.stop()` line 196 — crashes instead of cleaning up the stale file.

**Fix:** Wrap `load()` in a try/except in both callers (or in `load()` itself):
```python
# In server.status():
try:
    state = WebviewState.load(Path(analysis_dir))
except Exception:
    # Corrupt state file — treat as stale.
    state_file.unlink(missing_ok=True)
    return None

# In server.stop():
try:
    state = WebviewState.load(Path(analysis_dir))
except Exception:
    state_file.unlink(missing_ok=True)
    return (False, None)
```

---

### WR-04: `is_alive()` treats `PermissionError` as alive — stale state with recycled foreign PID permanently blocks `start()`

**File:** `src/lucy_ng/webview/state.py:74-80`
**Issue:** When `os.kill(self.pid, 0)` raises `PermissionError`, `is_alive()` returns
`True`. This is correct for the original server process owned by another user (an unusual
but possible setup), but it creates an unrecoverable state when:

1. The webview server crashes.
2. Its PID is recycled to a process owned by a different user (e.g., a system daemon).
3. `start()` calls `status()` → `is_alive()` → `PermissionError` → `True`.
4. `start()` returns the dead state object as if the server is running.
5. The user has no way to recover without manually deleting `.webview.json`.

The `stop()` command in this scenario also fails with an unhandled `PermissionError` (WR-01).

**Fix:** `is_alive()` treating `PermissionError` as alive is semantically correct for
signal(0) — the process exists. The real fix is in the callers: `start()` should not
silently accept a state whose `url` is unreachable. A lightweight check (attempt TCP
connect to `state.host:state.port`) would distinguish a live server from a recycled PID
before returning early. Alternatively, `stop()` fixing WR-01 gives the user a recovery
path. Document the manual-delete fallback in the CLI `stop` help text as a stopgap.

---

## Info

### IN-01: `serve` silently ignores `--host`/`--port` when idempotent path is taken

**File:** `src/lucy_ng/cli/webview.py:72`
**Issue:** When `server.start()` returns an existing `WebviewState` (idempotent path), the
`--port` and `--host` arguments passed to the second invocation are silently discarded.
A user who runs `lucy webview serve ./analysis --port 9000` after a server is already bound
to port 8080 will see a success message pointing to port 8080 with no indication their
`--port` was ignored. This can cause confusion in scripted environments.

**Fix:** Emit a warning when the returned state's port/host differs from the requested
values:
```python
state = server.start(analysis_dir, port, host)
if port is not None and state.port != port:
    click.echo(
        f"Warning: server already running on port {state.port}; "
        f"--port {port} ignored.",
        err=True,
    )
```

---

### IN-02: `shutil.which("lucy")` may resolve `lucy` from a different virtualenv

**File:** `src/lucy_ng/webview/server.py:103-106`
**Issue:** In virtualenv or `uv`-managed setups, the `lucy` on `PATH` may belong to a
different environment than `sys.executable`. The subprocess would then run a different
package version — silently, with no version mismatch warning. The `sys.executable` fallback
path (`python -m lucy_ng.cli`) is the safer choice in these environments.

**Fix:** Consider preferring `sys.executable` unconditionally, or verifying the `lucy`
binary belongs to the same Python installation before using it:
```python
# Prefer sys.executable to guarantee the subprocess uses the same environment.
launcher = [sys.executable, "-m", "lucy_ng.cli"]
```
If `lucy` must be preferred for UX reasons, add a version-consistency check via
`lucy --version` before trusting it.

---

_Reviewed: 2026-07-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
