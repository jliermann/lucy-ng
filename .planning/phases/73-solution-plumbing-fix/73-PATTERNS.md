# Phase 73: Solution Plumbing Fix — Pattern Map

**Mapped:** 2026-05-20
**Files analyzed:** 3 (2 modified, 1 extended)
**Analogs found:** 3 / 3

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/lucy_ng/lsd/runner.py` | service (subprocess manager) | request-response | `src/lucy_ng/lsd/orchestrator.py` `_run_outlsd` | exact (same function, correct version) |
| `src/lucy_ng/cli/lsd.py` | CLI (thin wrapper) | request-response | `src/lucy_ng/cli/lsd.py` lsd_run (existing) | self (check only — likely no change needed) |
| `tests/test_lsd_runner.py` | test | integration + unit | `tests/test_lsd_regression.py` | role-match |

---

## Pattern Assignments

### `src/lucy_ng/lsd/runner.py` — Fix `_execute_lsd` and `_run_outlsd`

**Analog 1 (TARGET — correct implementation):** `src/lucy_ng/lsd/orchestrator.py` lines 255–295

**Analog 2 (BUGGY current code):** `src/lucy_ng/lsd/runner.py` lines 201–356 (full file, 401 lines, already in context)

---

#### Bug 1: `_execute_lsd` — stdin invocation (BUGGY, runner.py lines 201–210)

```python
# src/lucy_ng/lsd/runner.py lines 201-210  ← CURRENT BUGGY CODE — DO NOT COPY
try:
    # LSD command: lsd < input.lsd   ← comment documents the bug
    proc = subprocess.run(
        [str(self.lsd_path)],          # ← NO filename argument
        input=input_file.read_text(),  # ← LSD input content passed as stdin
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=output_dir,
    )
```

**What goes wrong:** stdin mode makes LSD write OUTLSD data to stdout and return rc=1; it writes NO `.sol` file to `output_dir`. The `.sol` file is only produced when LSD receives the input file as a positional argument.

**False-positive side-effect (runner.py lines 223–224):** The `success` flag is set based on `solution_count > 0`, which is parsed from stderr. LSD always writes `"392 solutions found.\n"` to stderr regardless of invocation mode — so `result.success=True` even though no `.sol` was written and `_run_outlsd` is about to produce garbage.

```python
# runner.py lines 223-224 — the silent false-positive
success = proc.returncode == 0 or solution_count > 0
```

#### Fix for `_execute_lsd` — file-argument invocation (TARGET pattern)

From `.planning/phases/72-design-re-validation/experiment/run_experiment.py` lines 123–128 (empirically verified):

```python
# CORRECT — file as positional argument; .sol written to cwd=output_dir
lsd_result = subprocess.run(
    [str(LSD_BIN), str(lsd_file)],   # ← absolute path as positional arg
    capture_output=True,
    text=True,
    cwd=EXPERIMENT_DIR,              # ← .sol lands here as {stem}.sol
)
```

**CWD rule (verified):** `lsd /abs/path/compound.lsd` with `cwd=output_dir` writes `compound.sol` to `output_dir` (not to the file's directory). Always pass absolute path AND set `cwd=output_dir`.

**Transformation:** Replace `[str(self.lsd_path)]` + `input=input_file.read_text()` with `[str(self.lsd_path), str(input_file)]` (no `input=` argument). All other kwargs (`capture_output`, `text`, `timeout`, `cwd`) stay identical.

**`success` flag fix:** After the fix, `success` should require that the `.sol` file was actually written (not just that stderr mentions a solution count):

```python
# Fixed success semantics — replace lines 223-224
sol_file = output_dir / f"{input_file.stem}.sol"
smiles_file = output_dir / "solutions.smi"
# Success requires: solutions found AND SMILES conversion succeeded
success = sol_file.exists() and smiles_file is not None
```

---

#### Bug 2: `_run_outlsd` — wrong stdin, missing "5" argument (BUGGY, runner.py lines 326–356)

```python
# src/lucy_ng/lsd/runner.py lines 326-356  ← CURRENT BUGGY CODE — DO NOT COPY
def _run_outlsd(self, output_dir: Path, input_file: Path) -> None:
    ...
    try:
        # outlsd reads from stdin like lsd   ← WRONG comment
        proc = subprocess.run(
            [str(self.outlsd_path)],           # ← MISSING "5" argument
            input=input_file.read_text(),      # ← WRONG: passes .lsd content, not .sol
            capture_output=True,
            text=True,
            timeout=30,
            cwd=output_dir,
        )
        # Write output to outlsd.out
        if proc.stdout.strip():                # ← ALWAYS TRUE: usage message is truthy
            outlsd_file = output_dir / "outlsd.out"
            outlsd_file.write_text(proc.stdout)  # ← writes 10-line usage message
    except Exception:
        pass  # Non-fatal - ranking will just skip solutions without SMILES
```

**What goes wrong (three failures):**
1. No `"5"` argument → outlsd prints usage text (10 lines) and exits rc=1.
2. `input_file` is the `.lsd` file, not the `.sol` file — wrong format even if "5" were present.
3. `proc.stdout.strip()` is truthy for the usage message → `outlsd.out` is written with 10-line usage text → `lucy lsd rank outlsd.out` → "Error: No SMILES found".

---

#### Fix for `_run_outlsd` — exact TARGET (orchestrator.py lines 255–295)

```python
# src/lucy_ng/lsd/orchestrator.py lines 255-295  ← COPY THIS PATTERN
def _run_outlsd(self, perm_dir: Path, lsd_file: Path) -> Path | None:
    """Run outlsd directly, bypassing the buggy LSDRunner._run_outlsd.

    The bug: LSDRunner._run_outlsd passes the LSD input file as stdin
    and omits the required mode argument. The correct call is:
        outlsd 5 < compound.sol > solutions.smi
    """
    outlsd_path = shutil.which("outlsd")
    if outlsd_path is None:
        return None

    sol_files = list(perm_dir.glob("*.sol"))
    if not sol_files:
        return None

    sol_file = sol_files[0]
    smiles_file = perm_dir / "solutions.smi"

    try:
        proc = subprocess.run(
            [outlsd_path, "5"],      # ← CORRECT: "5" = SMILES output mode (required)
            stdin=open(sol_file),    # ← CORRECT: .sol file as stdin (NOT .lsd file)
            capture_output=True,
            text=True,
            timeout=30,
            cwd=perm_dir,
        )
        if proc.stdout.strip():
            smiles_file.write_text(proc.stdout)
            return smiles_file
    except Exception:
        pass

    return None
```

**Adaptation for runner.py:** The orchestrator version calls `shutil.which("outlsd")` because it does not hold a runner reference. In `runner.py`, `self.outlsd_path` is already resolved — use it directly instead of re-calling `shutil.which`. Change signature to return `Path | None` (not `None`) so callers can confirm SMILES conversion succeeded.

---

#### Shared helper recommendation (Option A from RESEARCH.md)

Extract a module-level helper in `runner.py` so both `LSDRunner._run_outlsd` and `PyLSDOrchestrator._run_outlsd` call a single implementation:

```python
# Add at module level in src/lucy_ng/lsd/runner.py (new function)
def _invoke_outlsd(outlsd_path: Path, sol_file: Path, output_dir: Path) -> Path | None:
    """Convert .sol to SMILES via outlsd.

    Correct call: outlsd 5 < compound.sol > solutions.smi
    Source: orchestrator.py lines 255-295.

    Args:
        outlsd_path: Absolute path to outlsd binary.
        sol_file: Path to the .sol file produced by LSD.
        output_dir: Directory where solutions.smi will be written.

    Returns:
        Path to solutions.smi if conversion succeeded, else None.
    """
    smiles_file = output_dir / "solutions.smi"
    try:
        with sol_file.open("r") as fh:
            proc = subprocess.run(
                [str(outlsd_path), "5"],   # "5" = SMILES mode (required)
                stdin=fh,                  # .sol file (NOT the .lsd file)
                capture_output=True,
                text=True,
                timeout=30,
                cwd=output_dir,
            )
        if proc.stdout.strip():
            smiles_file.write_text(proc.stdout)
            return smiles_file
    except Exception:
        pass
    return None
```

Then `LSDRunner._run_outlsd` becomes a one-liner:

```python
def _run_outlsd(self, output_dir: Path, input_file: Path) -> Path | None:
    if self.outlsd_path is None:
        return None
    sol_files = list(output_dir.glob("*.sol"))
    if not sol_files:
        return None
    return _invoke_outlsd(self.outlsd_path, sol_files[0], output_dir)
```

And `PyLSDOrchestrator._run_outlsd` (orchestrator.py lines 255–295) can delegate to the same helper after importing `_invoke_outlsd` from `lucy_ng.lsd.runner`.

---

#### Output file naming

After the fix, `runner._run_outlsd` writes to `solutions.smi` (consistent with orchestrator). The current `outlsd.out` name is not hardcoded in the CLI — `lsd_rank` accepts any path as its first argument — so this is a safe rename. Do NOT write a backward-compatible `outlsd.out` symlink (this creates confusion); update Phase 75 skill docs to reference `solutions.smi` instead.

---

### `src/lucy_ng/cli/lsd.py` — `lsd_run` command (check only, likely no change)

**Analog:** `src/lucy_ng/cli/lsd.py` itself (self-check)

The CLI's `lsd_run` function (lines 64–105) calls `runner.run_file()` and reports `result.output_files`. After the runner fix, `output_files` will include `compound.sol` and `solutions.smi` instead of `outlsd.out`. The CLI iterates and prints them — no logic change needed, only the file names change.

**Verification:** Confirm that `result.output_files` (runner.py lines 213, 230) correctly includes both `.sol` and `.out` globs after the fix. After the fix, the re-scan at line 230 becomes:

```python
# runner.py lines 229-230 (post-fix: include .smi in output_files scan)
output_files = (
    list(output_dir.glob("*.sol"))
    + list(output_dir.glob("*.out"))
    + list(output_dir.glob("*.smi"))   # ← add .smi glob
)
```

No other changes to `cli/lsd.py` are required for Phase 73.

---

### `tests/test_lsd_runner.py` — New `TestLSDRunnerFixed` class

**Analog:** `tests/test_lsd_regression.py` (full file, 262 lines, already in context)

**Imports pattern to copy** (test_lsd_regression.py lines 32–42):

```python
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from rdkit import Chem
from rdkit.Chem.inchi import MolToInchi  # type: ignore[import-untyped]

from lucy_ng.lsd.runner import LSDRunner
```

**skipif guard pattern** (test_lsd_regression.py lines 136–139):

```python
@pytest.mark.skipif(
    shutil.which("LSD") is None,
    reason="LSD binary not installed",
)
```

Note: The existing `TestLSDRunnerExecution` (test_lsd_runner.py lines 121–124) uses `not LSDRunner.is_available()` as the skipif condition. The regression test uses `shutil.which("LSD") is None`. Use `shutil.which("LSD") is None` for consistency with the regression test — it also requires outlsd on PATH, and the new tests need both.

**Fixture dir pattern** (test_lsd_regression.py line 44):

```python
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "regression"
```

**LSDRunner instantiation + run_file call** (test_lsd_regression.py lines 150–154):

```python
runner = LSDRunner()
result = runner.run_file(lsd_fixture, output_dir=tmp_path, timeout=120)
assert result.success, (
    f"LSD run failed:\n  stdout: {result.stdout[:500]}\n  stderr: {result.stderr[:500]}"
)
```

**SMILES → InChI helper** (test_lsd_regression.py lines 52–78 — copy as-is):

```python
def _smiles_to_inchis(smiles_path: Path) -> set[str]:
    inchis: set[str] = set()
    for raw_line in smiles_path.read_text().splitlines():
        parts = raw_line.strip().split()
        if not parts:
            continue
        smiles = parts[0]
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue
        inchi = MolToInchi(mol)
        if inchi is not None:
            inchis.add(inchi)
    return inchis
```

**outlsd subprocess call pattern** (test_lsd_regression.py lines 229–237 — Fallback B, the path the fixed runner will always produce):

```python
# Fallback B pattern — this is the ONLY path after the Phase 73 fix
sol_files = list(tmp_path.glob("*.sol"))
assert sol_files, "No .sol file written by runner"
sol_file = sol_files[0]
with sol_file.open("r") as stdin_fh, fallback_smi.open("w") as stdout_fh:
    subprocess.run(
        [outlsd_bin, "5"],
        stdin=stdin_fh,
        stdout=stdout_fh,
        check=True,
        timeout=30,
    )
```

**Mock pattern for unit tests** (test_lsd_runner.py lines 207–243 — monkeypatch subprocess):

```python
def test_timeout_handling(self, monkeypatch):
    import subprocess

    def mock_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="lsd", timeout=1)

    monkeypatch.setattr(subprocess, "run", mock_run)
    runner = LSDRunner(lsd_path="/bin/true")
    ...
    result = runner.run(problem, output_dir=Path(tmpdir), timeout=1)
    assert result.success is False
```

**Five required tests for `TestLSDRunnerFixed`** (from RESEARCH.md):

| Test name | What to assert | LSD required? |
|---|---|---|
| `test_runner_writes_sol_file` | `(tmp_path / "ibuprofen_no_4j.sol").exists()` and size > 0 | Yes (skipif) |
| `test_runner_produces_smiles` | `(tmp_path / "solutions.smi")` contains exactly 392 non-empty lines | Yes (skipif) |
| `test_no_header_only_output` | `solutions.smi` first line is a valid SMILES (not "outlsd: usage:") | Yes (skipif) |
| `test_lsd_rank_end_to_end` | Call `_perform_ranking(solutions.smi, shifts)` → `total_solutions=392`, `ranked_count > 0` | Yes (skipif) |
| `test_runner_success_semantics` | `result.success=True` iff `.sol` exists AND `solutions.smi` exists (not just stderr count) | Yes (skipif) |
| `test_invoke_outlsd_unit` | Mock: correct `[str(outlsd_path), "5"]` + `stdin=sol_file` call; wrong `.lsd`-stdin call produces None | No (mock) |

The mock-based `test_invoke_outlsd_unit` tests the module-level `_invoke_outlsd` helper directly using `monkeypatch.setattr(subprocess, "run", ...)` to verify correct argument construction without the LSD binary.

---

## Shared Patterns

### Subprocess invocation style
**Source:** `src/lucy_ng/lsd/orchestrator.py` lines 280–288 and `runner.py` throughout
**Apply to:** All `subprocess.run` calls in runner.py and orchestrator.py
- Always use list form (never `shell=True`) — no shell injection risk
- Always set `capture_output=True, text=True`
- Always set explicit `timeout`
- Always set `cwd` explicitly when the output file location matters
- Use context manager (`with sol_file.open("r") as fh`) for stdin file handles

### Error handling pattern
**Source:** `src/lucy_ng/lsd/runner.py` lines 242–256 and orchestrator.py lines 292–294
**Apply to:** `_execute_lsd`, `_run_outlsd`, `_invoke_outlsd`
- `subprocess.TimeoutExpired` → return `LSDResult(success=False, stderr="timed out...")`
- All other exceptions in outlsd → `except Exception: pass; return None` (non-fatal)
- LSD invocation itself → `except Exception as e: return LSDResult(success=False, stderr=str(e))`

### `@pytest.mark.skipif` guard
**Source:** `tests/test_lsd_regression.py` lines 136–139
**Apply to:** All integration tests in `TestLSDRunnerFixed`
```python
@pytest.mark.skipif(
    shutil.which("LSD") is None,
    reason="LSD binary not installed",
)
```
Both `LSD` and `outlsd` must be on PATH for integration tests. Add a second guard or assert inside the test:
```python
outlsd_bin = shutil.which("outlsd")
assert outlsd_bin is not None, "outlsd binary not found on PATH"
```

---

## No Analog Found

None. All three files have close analogs in the codebase.

---

## Key Transformation Summary (for planner actions)

| Location | Current (BUGGY) | Replace With |
|---|---|---|
| `runner.py` line 203–205 | `subprocess.run([str(self.lsd_path)], input=input_file.read_text(), ...)` | `subprocess.run([str(self.lsd_path), str(input_file)], ...)` — remove `input=` kwarg |
| `runner.py` lines 223–224 | `success = proc.returncode == 0 or solution_count > 0` | `success = sol_file.exists() and smiles_path is not None` where `sol_file = output_dir / f"{input_file.stem}.sol"` |
| `runner.py` lines 340–346 | `subprocess.run([str(self.outlsd_path)], input=input_file.read_text(), ...)` | `subprocess.run([str(self.outlsd_path), "5"], stdin=open(sol_file), ...)` — pass `.sol` file |
| `runner.py` lines 351–352 | `outlsd_file = output_dir / "outlsd.out"` | `smiles_file = output_dir / "solutions.smi"` |
| `runner.py` lines 227–230 | `self._run_outlsd(output_dir, input_file)` + rescan `*.out` | `smiles_path = self._run_outlsd(output_dir, input_file)` (capture return value) + add `*.smi` to glob |
| `orchestrator.py` lines 268–291 | Copy of the correct logic (leave intact or delegate to shared helper) | After fix: delegate to `_invoke_outlsd()` from runner.py |

---

## Metadata

**Analog search scope:** `src/lucy_ng/lsd/`, `tests/`, `.planning/phases/72-design-re-validation/experiment/`
**Files scanned:** 5 (`runner.py`, `orchestrator.py` partial, `test_lsd_runner.py`, `test_lsd_regression.py`, `run_experiment.py` partial)
**Pattern extraction date:** 2026-05-20
