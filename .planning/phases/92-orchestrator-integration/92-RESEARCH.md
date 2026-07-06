# Phase 92: Orchestrator Integration - Research

**Researched:** 2026-07-06
**Domain:** CASE orchestrator skill (`case.md`) — markdown prompt editing, `lucy webview serve` lifecycle
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WV-07 | When a CASE run starts, `case.md` launches the webview server in the background and reports the dashboard URL and stop hint to the user before work begins. Server outlives the team. | `server.start()` uses `start_new_session=True` (outlives parent); `serve` returns in ~0.5 s (non-blocking); no `[webview] stop` in `terminate_team` |
</phase_requirements>

---

## Summary

Phase 92 is a **single-file markdown prompt edit** to `.claude/commands/lucy-ng/case.md`. No Python code changes are expected. The entire deliverable is a new Bash call and two printed lines inserted into the `spawn_case_team` step — plus explicit documentation in `terminate_team` that the server is NOT stopped. The working dashboard (delivered by Phase 91) makes the URL meaningful for the first time.

The `lucy webview serve <dir>` command already does exactly what this phase needs: it launches a detached uvicorn subprocess (via `subprocess.Popen(..., start_new_session=True)`), waits 0.5 s for a startup probe, and returns immediately with `url`, `pid`, and `port`. The subprocess is a fully independent OS process — it outlives the orchestrator and survives `terminate_team`. Nothing new needs to be built; the integration is wiring only.

The single most important design constraint is the **headless/non-interactive rule** already in `case.md`: "Background-and-wait is forbidden." This rule is NOT violated by `lucy webview serve` because the command is non-blocking — it exits after the 0.5 s startup poll and hands control back. The orchestrator calls it, captures the output, prints the dashboard URL, and proceeds immediately to the peak-picking kick-off.

**Primary recommendation:** Insert a single Bash step in `spawn_case_team` Step 5 — after the `run_start` timing stamp (which creates `analysis/`) and before `phase_start` + `[BEGIN]`. Wrap the call in a shell `if/else` to handle `[webview]` not installed gracefully (print a warning, continue — never abort the CASE run). Add a one-line note in `terminate_team` confirming the server is intentionally left running.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Launch webview at CASE start | Orchestrator (`case.md`) | CLI (`lucy webview serve`) | `case.md` decides when to launch; CLI owns the lifecycle mechanics |
| Server lifecycle (start/stop/status) | CLI (`lucy webview serve/stop/status`) | OS process model | Already built in Phase 90; `case.md` calls it via Bash |
| Server process survival across team shutdown | OS process model (`start_new_session=True`) | — | Kernel-level detachment; no orchestrator cooperation needed |
| Stop hint to user | Orchestrator output | CASE-PROGRESS.md header | User needs it before the run occupies their terminal |
| Failure handling ([webview] not installed) | Orchestrator (`case.md` shell guard) | — | Non-fatal; CASE must continue without the dashboard |

---

## Standard Stack

No new packages. Phase 92 uses only what Phase 90 delivered.

| Component | Already exists | Phase 92 usage |
|-----------|---------------|----------------|
| `lucy webview serve <dir>` | Yes (Phase 90) | Bash call in `case.md` |
| `lucy webview stop <dir>` | Yes (Phase 90) | Mentioned in stop hint; NOT called by orchestrator |
| `.webview.json` | Yes (Phase 90) | Written by `serve`; read by `status`/`stop` |
| `lucy_ng.webview.server.start()` | Yes (Phase 90) | Invoked internally by `lucy webview serve` |

**Installation (no change):** `[webview]` extra is already declared; Phase 92 does not add dependencies.

---

## Package Legitimacy Audit

No new packages are installed in this phase. Section not applicable.

---

## Architecture Patterns

### System Architecture Diagram

```
case.md: spawn_case_team — Step 5 (run start)
         |
         v
  [run_start timing stamp]
    mkdir -p <compound_path>/analysis
    printf ... run_start >> analysis/timing.jsonl
         |
         v  <--- NEW INSERTION POINT (Phase 92)
  [webview launch block]
    lucy webview serve <compound_path>/analysis 2>&1 → captured output
    if success:
      print "Dashboard: <url>"
      print "Stop after run: lucy webview stop <compound_path>/analysis"
    if failure (ImportError / RuntimeError):
      print "Webview unavailable: <error> — install lucy-ng[webview] to enable"
      (continue — CASE run is unaffected)
         |
         v
  [phase_start timing stamp for peak-picking]
  [SendMessage [BEGIN] peak-picking → nmr-chemist]
         |
         ... (full CASE workflow — 1-10 iterations) ...
         |
         v
  [terminate_team]
    Step 0: run_end timing stamp + finalize timing.json
    Step 1: shutdown_request to 4 agents
    Step 2: wait for confirmations
    Step 3: TeamDelete
    (NO lucy webview stop — server deliberately left running)
         |
         v
  [uvicorn subprocess]
    Still running — independent OS process (start_new_session=True)
    Accessible at <url> indefinitely
    User stops via: lucy webview stop <compound_path>/analysis
```

### Recommended Project Structure

```
.claude/commands/lucy-ng/
└── case.md    ← only file modified
```

### Pattern 1: Non-Blocking Webview Launch (Bash in case.md)

**What:** Call `lucy webview serve` via Bash, capture output, print URL + stop hint, proceed immediately.

**When to use:** At CASE run start, after `analysis/` is created by the `run_start` timing stamp.

**Why this is non-blocking:** `server.start()` calls `subprocess.Popen(..., start_new_session=True)`, sleeps 0.5 s for a startup probe, then returns `WebviewState`. The CLI command then prints and exits. The orchestrator's Bash call completes in ~0.5–1 s and returns control.

```bash
# Source: server.py server.start() + cli/webview.py serve command [VERIFIED: read source]
WEBVIEW_OUTPUT=$(lucy webview serve "<compound_path>/analysis" 2>&1)
WEBVIEW_EXIT=$?
if [ $WEBVIEW_EXIT -eq 0 ]; then
  # lucy webview serve (text format) prints:
  #   Webview server running at http://127.0.0.1:NNNNN
  #   Stop with: lucy webview stop <analysis_dir>
  echo "$WEBVIEW_OUTPUT"
else
  echo "Note: Webview dashboard unavailable — $WEBVIEW_OUTPUT"
  echo "Install lucy-ng[webview] to enable the live dashboard."
fi
```

The `2>&1` captures the friendly `click.ClickException` message when `[webview]` is not installed. Exit code is non-zero in that case, so the shell guard catches it cleanly.

### Pattern 2: Injecting Into case.md Step 5 — Exact Context

The new block slots between two existing sentences in `spawn_case_team` Step 5.

**Before (existing lines 218–219, verbatim):**

```
**First, stamp timing** (see the timing step): take the `run_start` stamp (this one also does
`mkdir -p <compound_path>/analysis`), then a `phase_start` stamp for `peak-picking` — both
BEFORE the push below.
```

**After (existing line 224, verbatim):**

```
SendMessage(
  type="message",
  recipient="nmr-chemist",
  content="[BEGIN] peak-picking — start now. ...
```

**New text goes between these two.** The `run_start` stamp creates `analysis/`, making it safe to call `lucy webview serve <compound_path>/analysis` immediately after. The `phase_start` stamp and `[BEGIN]` push come after the webview block.

### Pattern 3: terminate_team — No Stop Call

`terminate_team` (case.md lines 876–908) has four steps:

- Step 0: `run_end` timing stamp + finalize timing.json
- Step 1: send `shutdown_request` to all 4 teammates
- Step 2: wait for shutdown confirmations
- Step 3: `TeamDelete()` — removes Claude Code team/task state ONLY (not OS processes)

**None of these steps stop the webview server.** This is deliberate — Success Criterion #2 requires the server to remain accessible after the run. A one-line comment must be added to `terminate_team` documenting this intent explicitly:

```
Note: the webview server (started at run_start) is intentionally NOT stopped here.
It remains running so the user can review the dashboard after the CASE run ends.
The user stops it with: lucy webview stop <compound_path>/analysis
```

Without this comment, a future editor might incorrectly "fix" the missing stop call.

### Pattern 4: Why the Server Survives terminate_team (Technical Basis)

**Root cause:** `server.start()` in `server.py` (line 122–128) launches the subprocess with:

```python
proc = subprocess.Popen(
    cmd,
    start_new_session=True,   # ← detaches from parent's process group
    stdout=log_file,
    stderr=subprocess.STDOUT,
    close_fds=True,
)
```

`start_new_session=True` calls `setsid()` on POSIX — the subprocess becomes the leader of a new session and process group. It no longer receives `SIGHUP` or `SIGINT` when the terminal/parent session ends. `TeamDelete()` removes Claude Code's in-memory team/task state; it has no knowledge of OS PIDs and does not send signals to subprocesses. The uvicorn process simply continues running until either `lucy webview stop` sends `SIGTERM` or the OS shuts down.

[VERIFIED: read server.py lines 122-128 directly]

### Anti-Patterns to Avoid

- **Calling `lucy webview serve analysis/ &` (background shell operator):** This backgrounds the process AND waits in a non-interactive context — the forbidden "background-and-wait" pattern. The correct call is `lucy webview serve analysis/` (foreground, exits in ~0.5 s).
- **Calling `lucy webview serve` after `SendMessage([BEGIN]):`** The analysis/ directory exists only after the `run_start` timing stamp; calling serve before that step risks a `ValueError: analysis_dir does not exist`.
- **Aborting the CASE run when webview fails:** The dashboard is purely informational. If `[webview]` is not installed, CASE must continue — a missing URL is inconvenient, not a fatal error.
- **Calling `lucy webview stop` in terminate_team:** This is the exact mistake SC #2 guards against. The server must outlive the run.
- **Assuming a fixed port:** No `--port` argument should be passed; `server.start()` picks a free ephemeral port, and the URL in the output is the single source of truth.
- **Passing `--open`:** The `--open` flag calls `webbrowser.open()`, which would try to open a browser in a headless/non-interactive harness. Never pass `--open` from the orchestrator.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Background server launch | Custom subprocess management | `lucy webview serve <dir>` | Already implemented, idempotent, PID-tracked, free-port aware |
| Port tracking | Pass explicit port in case.md | Let `server.start()` pick it | Ephemeral port avoids conflicts; URL is in `.webview.json` and serve output |
| Server survival | Nohup / disown logic | `start_new_session=True` in Popen | Already baked into `server.start()` — no case.md logic needed |
| Stop reminder | Custom reminder wording | Reuse `lucy webview stop <dir>` hint from serve output | Consistent with what Phase 90 CLI already prints |

**Key insight:** The entire mechanism (detached process, PID file, idempotency, stop/status) was built in Phase 90. Phase 92 is three lines of Bash in case.md and two lines of documentation in terminate_team.

---

## Common Pitfalls

### Pitfall 1: Calling `lucy webview serve` Before `analysis/` Exists

**What goes wrong:** `server.start()` raises `ValueError: analysis_dir does not exist or is not a directory`. The orchestrator Bash call fails; if not guarded, the CASE run aborts.

**Why it happens:** The `analysis/` directory is created by the `run_start` timing stamp (`mkdir -p <compound_path>/analysis`). If the webview call is placed before that stamp (e.g., at team spawn, before Step 5), the directory doesn't exist yet.

**How to avoid:** Place the webview launch block AFTER the `run_start` timing stamp in Step 5.

**Warning signs:** Bash returns non-zero and the error message contains "not a directory".

---

### Pitfall 2: Missing `[webview]` Extra at CASE Runtime

**What goes wrong:** The CASE environment was installed with `pip install lucy-ng` (not `pip install lucy-ng[webview]`). `lucy webview serve` prints a `click.ClickException` and exits non-zero. Without a shell guard, the Bash call fails and the orchestrator's error handling takes over.

**Why it happens:** WV-08 intentionally made `[webview]` an optional extra. CASE runs on remote servers (Sheldon) that may not have the extra installed.

**How to avoid:** Guard the Bash call with `if/else` on exit code (see Pattern 1). On failure, print a one-line "Webview unavailable" note and proceed to `phase_start` + `[BEGIN]` without interruption.

**Warning signs:** CASE runs stall or abort with "The webview extra is not installed" text in Bash output.

---

### Pitfall 3: Violating the Headless/Non-Interactive Rule

**What goes wrong:** The orchestrator ends a turn by saying "I've started the webview server, I'll wait for it to be ready" — then the process exits mid-workflow in a headless run.

**Why it happens:** Confusion between "background process is running" and "I must wait for it". The webview server is not a CASE agent; it doesn't send a completion message.

**How to avoid:** The webview launch is entirely synchronous from the orchestrator's perspective — `lucy webview serve` returns in ~0.5 s with a URL. There is nothing to wait for. After printing the URL, proceed immediately to `phase_start` and `[BEGIN]`.

**Warning signs:** case.md says "waiting for webview server to be ready" and then ends the turn.

---

### Pitfall 4: terminate_team Inadvertently Stops the Server

**What goes wrong:** A future edit adds `lucy webview stop` to `terminate_team` (Step 1 or before TeamDelete), breaking SC #2. The dashboard URL becomes unreachable seconds after the run ends.

**Why it happens:** The missing stop call looks like an oversight without documentation.

**How to avoid:** Add an explicit "intentionally NOT stopped" comment in `terminate_team` (see Pattern 3). The comment is the guard against future regression.

---

### Pitfall 5: Fresh Session Required After Editing case.md

**What goes wrong:** The developer edits case.md, runs `/lucy-ng:case` in the SAME Claude Code session, and gets the OLD orchestrator behaviour. The edit appears to have no effect.

**Why it happens:** Claude Code loads skill files (`.md` command files) once at session start. Edits to `.claude/commands/lucy-ng/case.md` are NOT picked up mid-session. case.md contains three `<!-- RELOAD NOTE: ... a FRESH Claude Code session is REQUIRED to reload. -->` comments acknowledging this.

**How to avoid:** After committing the case.md edit, open a FRESH Claude Code session before running any test. This is the standard reload procedure for all skill prompt edits in this project.

**Warning signs:** Edited behaviour is never observed; the old flow still runs.

---

## Code Examples

### Verified `lucy webview serve` Text Output

```
# Source: cli/webview.py serve command, text format output [VERIFIED: read source]
Webview server running at http://127.0.0.1:54312
Stop with: lucy webview stop /path/to/compound/analysis
```

### Verified `lucy webview serve` JSON Output (for reference)

```json
// Source: cli/webview.py serve command, --format json [VERIFIED: read source]
{"url": "http://127.0.0.1:54312", "pid": 12345, "port": 54312}
```

### Verified Server Survival Mechanism

```python
# Source: server.py lines 122-128 [VERIFIED: read source]
proc = subprocess.Popen(
    cmd,
    start_new_session=True,   # setsid() — detaches from parent session
    stdout=log_file,
    stderr=subprocess.STDOUT,
    close_fds=True,
)
```

### Proposed case.md Insertion (Step 5, spawn_case_team)

```markdown
<!-- WV-07: Launch webview dashboard before the first [BEGIN] push.
     analysis/ was just created by the run_start timing stamp above.
     lucy webview serve is non-blocking (~0.5 s startup probe) — it does NOT
     violate the headless/non-interactive rule. The spawned uvicorn process
     uses start_new_session=True and outlives this orchestrator session. -->

Launch the webview dashboard (non-blocking — exits in ~0.5 s):

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

If the server started, the output above already contains the URL and stop hint in the
standard `lucy webview serve` format:
  Webview server running at http://127.0.0.1:NNNNN
  Stop with: lucy webview stop <compound_path>/analysis

Continue to phase_start stamp and [BEGIN] peak-picking push regardless of webview outcome.
```

---

## Open Design Decisions (No CONTEXT.md — Claude's Discretion)

These are unresolved design choices because `/gsd-discuss-phase` was skipped. Each has a recommended default that the planner may treat as a locked decision.

### OD-1: Port — fixed vs auto/ephemeral

**Options:** (a) auto/ephemeral (no `--port`), (b) fixed port (e.g. `--port 8765`), (c) let user configure

**Recommended default: auto/ephemeral (option a)** — no `--port` argument in the case.md Bash call. Rationale: `server.start()` already picks a free ephemeral port using the socket-bind trick; this avoids conflicts on machines running multiple CASE sessions. The URL is always shown to the user; there's no need for a predictable port.

### OD-2: Failure policy — abort vs continue-with-warning

**Options:** (a) abort the CASE run if `lucy webview serve` fails, (b) print a warning and continue

**Recommended default: continue-with-warning (option b).** Rationale: WV-07 is observability, not control. CASE ran successfully for dozens of UAT cases without any dashboard. A missing URL is inconvenient, never fatal. This also makes CASE robust on servers where `[webview]` is not installed (e.g. Sheldon without the extra).

### OD-3: `--open` browser flag

**Options:** (a) pass `--open` to open the browser automatically, (b) never pass `--open`

**Recommended default: never pass `--open` (option b).** Rationale: The orchestrator runs in headless contexts (UAT harness, `claude -p`, Sheldon). `--open` calls `webbrowser.open()`, which either opens a GUI browser (unwanted in headless), fails silently, or errors. The user can open the URL manually from the printed line.

### OD-4: analysis_dir argument form — relative vs absolute

**Options:** (a) `<compound_path>/analysis` (relative-ish, using the compound_path variable), (b) resolved absolute path via `$(realpath <compound_path>/analysis)`

**Recommended default: option (a) — `<compound_path>/analysis` without explicit realpath.** Rationale: `server.start()` calls `Path(analysis_dir).resolve()` internally (server.py line 85), so it handles relative paths correctly. Using the same `<compound_path>/analysis` form that case.md already uses throughout is simpler and consistent.

### OD-5: Where to print the URL — terminal output only vs also in CASE-PROGRESS.md header

**Options:** (a) print to terminal only (before CASE-PROGRESS.md exists), (b) also add a `**Dashboard:**` field to the CASE-PROGRESS.md header

**Recommended default: option (b) — also add to CASE-PROGRESS.md header.** Rationale: The header is the persistent record of the run. Having the dashboard URL there makes it retrievable after the run without needing to re-run `lucy webview status`. The header is written after [SETUP-COMPLETE], so the URL from the earlier Bash call should be stored in a variable and injected into the header. This is a small addition to the progress-format.md write_progress step.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (configured in pyproject.toml) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_case_md_wv07.py -x -v` |
| Full suite command | `pytest` |

### Verification Strategy for case.md (Markdown Skill File)

case.md is a markdown prompt — it has no Python runtime and cannot be exercised by pytest directly. Prior phases (86-89) verified case.md changes via blind CASE runs; those runs take 20–120 min and are not automatable per commit. The recommended strategy for Phase 92 is:

**Automated (fast — pytest greps the skill file):**

Create `tests/test_case_md_wv07.py` with three grep-based assertions:

| Test | What it checks | Automated Command |
|------|---------------|-------------------|
| `test_webview_launch_present` | case.md contains `lucy webview serve` Bash call in spawn_case_team before the first `[BEGIN] peak-picking` SendMessage | `pytest tests/test_case_md_wv07.py::test_webview_launch_present -x` |
| `test_stop_hint_present` | case.md contains `lucy webview stop` reference in the WV-07 block | `pytest tests/test_case_md_wv07.py::test_stop_hint_present -x` |
| `test_terminate_team_no_stop` | terminate_team section does NOT contain `lucy webview stop` (confirming the server is intentionally left running) | `pytest tests/test_case_md_wv07.py::test_terminate_team_no_stop -x` |

These are `Path(".claude/commands/lucy-ng/case.md").read_text()` string-search tests — they run in milliseconds.

**Automated (fast — subprocess integration, already exists):**

The existing `tests/test_cli_webview.py::TestWebviewLifecycle` tests cover `serve` idempotency and `stop` termination (WV-01/WV-02). They implicitly verify that the server survives a parent subprocess exit: `test_stop_terminates` starts a server via fixture, gets the PID, calls stop, then asserts `os.kill(pid, 0)` raises `ProcessLookupError` — confirming the pattern works. No new subprocess-survival test is strictly needed, but one explicit "server outlives caller process" test can be added to `test_cli_webview.py`:

| Test | What it checks | Automated Command |
|------|---------------|-------------------|
| `test_serve_outlives_caller` | Start server from a subprocess, let the subprocess exit, confirm server PID still alive | `pytest tests/test_cli_webview.py::TestWebviewLifecycle::test_serve_outlives_caller -x` |

**Manual (required once — session reload):**

The fresh-session reload is a mandatory one-time manual verification. After the case.md edit is committed:

1. Open a FRESH Claude Code session in the project directory.
2. Run `/lucy-ng:case data/example_compound C9H10O2 --smoke-test`.
3. Confirm the orchestrator prints "Webview server running at http://127.0.0.1:NNNNN" before the first `[BEGIN]` push.
4. Confirm the server is still accessible after the smoke test completes.
5. Run `lucy webview stop data/example_compound/analysis` to clean up.

This is the canonical SC verification for WV-07 SC #1, SC #2, SC #3.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WV-07 | case.md contains webview launch before [BEGIN] | unit (grep) | `pytest tests/test_case_md_wv07.py::test_webview_launch_present -x` | Wave 0 |
| WV-07 | case.md contains stop hint in webview block | unit (grep) | `pytest tests/test_case_md_wv07.py::test_stop_hint_present -x` | Wave 0 |
| WV-07 | terminate_team does not call webview stop | unit (grep) | `pytest tests/test_case_md_wv07.py::test_terminate_team_no_stop -x` | Wave 0 |
| WV-07 SC #2 | server outlives caller process (start_new_session=True) | integration | `pytest tests/test_cli_webview.py::TestWebviewLifecycle::test_serve_outlives_caller -x` | Wave 0 |
| WV-07 SC #1,2,3 | full orchestrator emits URL + stop hint + server survives | manual (fresh session) | smoke-test CASE run | N/A |

### Wave 0 Gaps

- [ ] `tests/test_case_md_wv07.py` — three grep-based tests above (new file)
- [ ] `tests/test_cli_webview.py::TestWebviewLifecycle::test_serve_outlives_caller` — add to existing class

---

## Security Domain

### Applicable ASVS Categories

This phase adds no new attack surface. The webview server was analysed for security in Phase 90 (bound to 127.0.0.1, path-traversal guard on `analysis_dir`, Popen list form, startup probe). Phase 92 only calls the existing CLI from case.md.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Local-only, no user accounts (Phase 90 decision) |
| V3 Session Management | No | No sessions; stateless read-only API |
| V4 Access Control | No | 127.0.0.1 bind is the access control |
| V5 Input Validation | Partial | `<compound_path>/analysis` is a path already used by the orchestrator; no new user input |
| V6 Cryptography | No | No encryption needed for loopback-only service |

### Known Threat Patterns

No new threats introduced by Phase 92. The Bash call is:
```bash
lucy webview serve "<compound_path>/analysis" 2>&1
```
`<compound_path>` is the compound path already validated in `validate_prerequisites` (Step 2 of case.md: `ls <compound_path>` — directory must exist). It is passed as a string argument to the CLI, not via `shell=True`, so shell-injection is not possible.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `lucy` CLI | `lucy webview serve` | Yes | already installed (Phase 90 prerequisite) | — |
| `fastapi` + `uvicorn` | webview server subprocess | Optional | installed in dev env (Phase 90) | Graceful warning; CASE continues |
| `case.md` | this phase's target file | Yes | `.claude/commands/lucy-ng/case.md` (910 lines, read in full) | — |

**Missing dependencies with no fallback:** none — the CASE run proceeds even without `[webview]`.

**Fresh-session requirement:** Edits to case.md are NOT loaded mid-session. A new Claude Code session is required after the edit is committed.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `lucy webview serve` (text format) outputs exactly two lines: "Webview server running at \<url\>" and "Stop with: lucy webview stop \<dir\>" | Code Examples | LOW — verified by reading `cli/webview.py` serve command source directly |

**All other claims were verified by reading source files directly.** The injection point, server survival mechanism, terminate_team content, and headless-compliance were confirmed from `case.md`, `server.py`, `cli/webview.py`, and `state.py`.

---

## Open Questions

1. **Should the dashboard URL appear in CASE-PROGRESS.md header?**
   - What we know: The header is written after [SETUP-COMPLETE] (see progress-format.md). The webview URL is known at run_start (Step 5). The orchestrator can store it in a variable and inject it into the header.
   - What's unclear: Whether the planner considers this OD-5 worth the extra header field.
   - Recommendation: Include it (see OD-5 above). Adds one line to the progress-format.md write trigger. Small value but persistent record.

2. **Smoke-test mode — should webview also launch?**
   - What we know: Smoke-test mode (`--smoke-test` flag in case.md) exits after [VALIDATION-PASSED] and calls `terminate_team`. The analysis/ directory exists.
   - What's unclear: Whether it's useful to launch the dashboard for a 1-iteration smoke test.
   - Recommendation: Launch it anyway (the WV-07 insertion point is before the smoke-test/normal branching). The webview serve call is idempotent and ~0.5 s; there's no cost to including it in smoke-test mode.

---

## Sources

### Primary (HIGH confidence)

- `.claude/commands/lucy-ng/case.md` — read in full (910 lines); injection point pinpointed at lines 218–229 of the `spawn_case_team` step; `terminate_team` confirmed at lines 876–908 with no webview stop call [VERIFIED: read source]
- `src/lucy_ng/webview/server.py` — `start()` function read in full; `subprocess.Popen(..., start_new_session=True)` confirmed at lines 122–128; 0.5 s startup probe confirmed at lines 135–147 [VERIFIED: read source]
- `src/lucy_ng/cli/webview.py` — `serve` command read in full; text output format confirmed at lines 82–83; `--format json` output confirmed at line 80; `--open` flag confirmed optional and defaults to False [VERIFIED: read source]
- `src/lucy_ng/webview/state.py` — `WebviewState.url` field confirmed (`f"http://{host}:{port}"`) [VERIFIED: read source]
- `.claude/commands/lucy-ng/references/progress-format.md` — CASE-PROGRESS.md header format confirmed; write_progress trigger confirmed (after [SETUP-COMPLETE]) [VERIFIED: read source]
- `tests/test_cli_webview.py` — existing lifecycle tests confirmed (TestWebviewLifecycle, lines 288–381); no existing "outlives caller" test [VERIFIED: read source]

### Secondary (MEDIUM confidence)

- `.planning/phases/90-server-cli-and-packaging/90-RESEARCH.md` — `start_new_session=True` survival rationale, Phase 90 design decisions confirmed
- `.planning/phases/91-api-endpoints-depictions-and-static-frontend/91-04-SUMMARY.md` — Phase 91 delivered working dashboard, verified by user on 2026-07-04

### Tertiary (LOW confidence)

None — all critical claims verified from source files.

---

## Metadata

**Confidence breakdown:**
- Injection point: HIGH — located by reading case.md lines 215–229 directly
- Server survival mechanism: HIGH — `start_new_session=True` confirmed in server.py
- Non-blocking behavior: HIGH — 0.5 s startup probe confirmed in server.py; CLI returns after probe
- Headless-rule compliance: HIGH — read case.md lines 92–107; serve exits, does not idle
- terminate_team no-stop: HIGH — read terminate_team step lines 876–908; no webview stop present
- Output formatting: HIGH — read cli/webview.py text output lines directly
- Verification strategy: HIGH — confirmed existing tests; grep-based case.md tests are proven pattern

**Research date:** 2026-07-06
**Valid until:** 2026-08-06 (stable — no fast-moving dependencies; case.md is the only target)
