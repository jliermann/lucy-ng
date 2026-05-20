# Phase 73: Solution Plumbing Fix — Research

**Researched:** 2026-05-20
**Domain:** LSD binary invocation, outlsd SMILES conversion, runner.py / orchestrator.py fix
**Confidence:** HIGH

---

## Summary

Phase 73 is the keystone fix of v9.0: make LSD solutions flow reliably from solver run to ranked SMILES, with zero silent solution loss. The root cause is two independent bugs in `runner.py`'s `_execute_lsd` and `_run_outlsd` methods. The correct patterns already exist in `orchestrator.py` and in `tests/test_lsd_regression.py`; this phase converges runner.py onto those patterns.

**Bug 1 (LSD invocation):** `_execute_lsd` passes the LSD input file contents via stdin (`subprocess.run([lsd_path], input=content, ...)`). In stdin mode, LSD-3.4.9 writes OUTLSD-format solution data to stdout and returns exit code 1 — it does **not** write a `.sol` file. The `.sol` file is only written when LSD receives the input file as a positional argument (`lsd compound.lsd`), which writes `compound.sol` in the CWD. Confirmed empirically: stdin mode → no `.sol` in tmpdir; file-arg mode → `compound.sol` written, 247 701 bytes, 392 solutions.

**Bug 2 (outlsd conversion):** `_run_outlsd` in `runner.py` passes the LSD **input** file as stdin to outlsd, and omits the required `"5"` mode argument. Correct: `outlsd 5 < compound.sol` (the `.sol` file as stdin, with the `"5"` SMILES-mode argument). Without the argument, outlsd exits with a 10-line usage message — exactly the `outlsd.out` artifact documented in the v8.0 UAT postmortem. `orchestrator.py`'s `_run_outlsd` (lines 255-295) does this correctly and is explicitly documented as "bypassing the buggy LSDRunner._run_outlsd".

**Exit-255 root cause:** LSD returns exit code 255 when it encounters an unknown command name (error 102). LSD files containing `SYME` or `DEFF NOT` (which are lucy-ng abstractions, not native LSD-3.4.9 commands) trigger this. In the v8.0 UAT iteration_02 run, `compound.lsd` contained `SYME 4 5`, `SYME 6 7`, `SYME 11 12`, and eight `DEFF NOT ...` lines → LSD returned 255 → `_execute_lsd` reported failure → the agent was forced to fall back to manual workarounds. For Phase 73's scope, the fix is the file-argument invocation; the SYME/DEFF NOT translation is Phase 74's responsibility.

**Primary recommendation:** Replace the stdin invocation in `_execute_lsd` with file-argument invocation and CWD management; replace `_run_outlsd` in runner.py with the pattern from `orchestrator.py`. Add a shared helper so the two implementations are no longer duplicated.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| LSD binary invocation | `lsd/runner.py` `_execute_lsd` | CLI `lucy lsd run` (thin wrapper) | Runner owns subprocess management; CLI is a thin Click wrapper that calls `runner.run_file()` |
| outlsd SMILES conversion | `lsd/runner.py` `_run_outlsd` | `lsd/orchestrator.py` `_run_outlsd` | Runner converts immediately after each LSD run; orchestrator currently has a CORRECT private copy; the fix unifies them |
| Solution parsing | `lsd/parser.py` `LSDOutputParser.parse_smiles_file` | — | Consumes the `.smi` / `outlsd.out` produced by outlsd; unchanged |
| SMILES → ranking | `ranking/` `SolutionRanker` via `cli/lsd.py` `_perform_ranking` | — | Consumes parsed SMILES; unchanged |
| Merge across permutations | `lsd/orchestrator.py` `SolutionMerger` | — | Phase 74 concern; Phase 73 fixes the per-run path that merger depends on |

---

## Bug Analysis: Exact Code with Line Numbers

### Bug 1: `_execute_lsd` stdin invocation (runner.py lines 202-210)

```python
# src/lucy_ng/lsd/runner.py lines 201-210
try:
    # LSD command: lsd < input.lsd   ← COMMENT DOCUMENTS THE BUG
    proc = subprocess.run(
        [str(self.lsd_path)],          # ← NO filename argument
        input=input_file.read_text(),  # ← LSD input content passed as stdin
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=output_dir,
    )
```

**What goes wrong:**
- `lsd < input.lsd` (stdin mode): LSD writes OUTLSD data to stdout, returns rc=1, writes NO `.sol` file.
- `lsd compound.lsd` (file-arg mode): LSD writes `compound.sol` to CWD, returns rc=1, stdout has a short header.
- Both modes return rc=1 on success (not rc=0); rc=255 means an unknown command was encountered.

**Verified empirically (fresh tmpdir):**
```
STDIN mode:  rc=1, sol_files=[], stdout has OUTLSD marker at line 9 (6283 total lines)
FILE ARG mode: rc=1, sol_files=['compound.sol'], compound.sol = 247701 bytes
```

**Success detection side-effect:** `_count_solutions` at line 273-283 parses "392 solutions found" from LSD's stderr → returns 392. Then `success = proc.returncode == 0 or solution_count > 0` evaluates to `True`. So `lucy lsd run` reports "LSD completed successfully, 392 solutions" even though no `.sol` was written and outlsd produces junk. This is a silent failure: the tool says success but downstream ranking gets zero SMILES.

### Bug 2: `_run_outlsd` in runner.py (lines 326-356)

```python
# src/lucy_ng/lsd/runner.py lines 326-356
def _run_outlsd(self, output_dir: Path, input_file: Path) -> None:
    ...
    try:
        # outlsd reads from stdin like lsd   ← WRONG COMMENT
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
            outlsd_file.write_text(proc.stdout) # ← Writes 10-line usage message
    except Exception:
        pass  # Non-fatal - ranking will just skip solutions without SMILES
```

**What goes wrong:**
1. No `"5"` argument → outlsd prints usage and exits rc=1 (not SMILES output).
2. `input_file` is the `.lsd` file (e.g., `compound.lsd`) — not the `.sol` file. Even if "5" were added, outlsd would fail because `.sol` format != `.lsd` format.
3. `proc.stdout.strip()` is truthy for the usage message → `outlsd.out` is written with 10 lines of usage text.
4. `parse_smiles_file` on `outlsd.out` finds 0 valid SMILES → `lucy lsd rank` reports "Error: No SMILES found in file".

**Verified empirically:**
```
outlsd (no arg, .lsd as stdin): rc=1, stdout = 10-line usage text
```
Exact content confirmed: `tests/fixtures/regression/outlsd.out` (produced by current buggy runner) is 10 lines, first line: `"outlsd: usage: outlsd p"`. This matches the v8.0 UAT artifact `.planning/phases/65-hypothesis-gate/outlsd.out` (10 lines, identical).

---

## The Correct Pattern (from orchestrator.py)

### orchestrator.py `_run_outlsd` (lines 255-295) — the TARGET

```python
# src/lucy_ng/lsd/orchestrator.py lines 255-295
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
            stdin=open(sol_file),    # ← CORRECT: .sol file as stdin
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

**Note:** The `orchestrator.py` docstring at line 119 explicitly documents the runner bug: "The outlsd invocation bypasses LSDRunner._run_outlsd() which has a known bug (missing mode argument). See STATE.md Phase 65 findings."

The Phase 73 fix MUST converge `runner._run_outlsd` onto the `orchestrator._run_outlsd` pattern. After the fix, the two should share a single implementation (a module-level helper, or orchestrator delegates to runner).

### experiment/run_experiment.py correct invocation (lines 123-168)

```python
# .planning/phases/72-design-re-validation/experiment/run_experiment.py lines 119-168
# Step 1: Run LSD (file argument mode; .sol written to EXPERIMENT_DIR cwd)
# IMPORTANT: LSD must be given the lsd file as a positional argument (not stdin).
lsd_result = subprocess.run(
    [str(LSD_BIN), str(lsd_file)],   # ← file as POSITIONAL ARGUMENT
    capture_output=True,
    text=True,
    cwd=EXPERIMENT_DIR,   # .sol lands here, named after the input file stem
)

# Step 4: Run outlsd (CORRECT pattern from orchestrator.py lines 281-291)
# Key: "5" argument (SMILES mode) + .sol file as stdin (NOT the .lsd file)
outlsd_proc = subprocess.run(
    [str(OUTLSD_BIN), "5"],       # "5" = SMILES output mode -- REQUIRED
    stdin=sol_file.open(),        # .sol file as stdin -- NOT the .lsd file
    capture_output=True,
    text=True,
    timeout=60,
    cwd=EXPERIMENT_DIR,
)
```

This is the empirically-verified working invocation that produced the Phase 72 experiment results (2 aromatic solutions, ibuprofen confirmed).

---

## `.sol` File Mechanics

### File naming (VERIFIED by experiment)

`lsd compound.lsd` writes a `.sol` file named after the input file stem in the LSD process's CWD:
- Input: `compound.lsd` → Output: `compound.sol` in CWD
- Input: `arm_a.lsd` → Output: `arm_a.sol` in CWD (confirmed by Phase 72 experiment artifacts)

**CWD implication:** `_execute_lsd` must set `cwd=output_dir` AND pass the absolute path of the input file as the positional argument. The current code already sets `cwd=output_dir`; only the invocation mode changes.

### `.sol` file format (VERIFIED by inspection)

```
# From file: /absolute/path/to/compound.lsd.
; LSD input content here (the original .lsd file content)
...
#
OUTLSD
15 1
 1  C 4 0 3 3  0   2 2   3 1  10 1   0 0
 ...
```

The `.sol` file header is: `"# From file: {path}\n"` + original `.lsd` content + `"\n#\nOUTLSD\n"` + solution data. The `OUTLSD` marker appears at line 9 of LSD's stdout in stdin mode (0-indexed), confirming the regression test's reconstruction logic is correct.

### stdin mode stdout structure (VERIFIED empirically)

LSD stdin mode produces to stdout:
```
[0] 'C 13 O 2 H 18 '            # formula summary
[1] '33 atoms'
[2] '37 bonds'
[3] '15 skeletal atoms'
[4] '15 skeletal bonds'
[5] 'Degree of unsaturation: 5'
[6] '1 ring'
[7] 'Total number of charges: 0'
[8] 'M = 206.00000'
[9] 'OUTLSD'                     # ← OUTLSD marker at index 9 (always 9 lines of header)
[10+] solution data...           # 6273 additional lines for 392 solutions
```

The regression test (`test_lsd_regression.py` lines 173-207) already handles this correctly — it searches for the `OUTLSD` marker, reconstructs a synthetic `.sol`, and pipes it to `outlsd 5`.

---

## Header-Strip: Exact Mechanism

### From test_lsd_regression.py (lines 173-207) — the documented workaround

```python
# tests/test_lsd_regression.py lines 173-207
if result.stdout.strip():
    stdout_lines = result.stdout.splitlines(keepends=True)
    try:
        outlsd_idx = next(
            i for i, ln in enumerate(stdout_lines) if ln.strip() == "OUTLSD"
        )
    except StopIteration:
        outlsd_idx = None

    if outlsd_idx is not None:
        outlsd_data = "".join(stdout_lines[outlsd_idx:])
        sol_content = (
            f"# From file: {lsd_fixture}\n"
            + lsd_fixture.read_text()
            + "\n#\n"
            + outlsd_data
        )
        sol_file = tmp_path / "compound.sol"
        sol_file.write_text(sol_content)
        with sol_file.open("r") as stdin_fh:
            proc = subprocess.run(
                [outlsd_bin, "5"],
                stdin=stdin_fh,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        fallback_smi.write_text(proc.stdout)
```

**Important:** This reconstruction pattern is the WORKAROUND for the stdin invocation mode. The Phase 73 fix should NOT continue to use this approach. The fix switches `_execute_lsd` to file-argument mode, which directly produces a `.sol` file that can be piped straight to `outlsd 5`. The reconstruction workaround in the regression test becomes unnecessary after the fix — but the test should still pass because the test will receive a proper `.sol` file (Fallback B branch, lines 222-238).

**Verified empirically:**
```
lsd compound.lsd → compound.sol (247701 bytes)
outlsd 5 < compound.sol → rc=0, 392 SMILES lines
First 5: ['O=C(O)C(C)C(=C1)C(C=C1)=CCC(C)C', ...]
```

---

## How `lucy lsd run` Output Feeds `lucy lsd rank`

### Current (broken) chain

```
lucy lsd run compound.lsd
  → runner.run_file()
  → _execute_lsd(): stdin invocation → no .sol written
  → _run_outlsd(): .lsd as stdin, no "5" → outlsd.out = 10-line usage
  → lucy lsd rank outlsd.out → "Error: No SMILES found"
```

### Fixed chain

```
lucy lsd run compound.lsd
  → runner.run_file()
  → _execute_lsd(): FILE ARG invocation → compound.sol written to output_dir
  → _run_outlsd(): compound.sol as stdin, "5" arg → solutions.smi = N SMILES lines
  → lucy lsd rank solutions.smi --shifts "..." → N ranked solutions
```

**Agent invocation pattern (from CLAUDE.md):**
```bash
lucy lsd run compound.lsd
outlsd 5 < compound.sol > solutions.smi   # alternative: manual override
lucy lsd rank solutions.smi --shifts "155.08,151.58,..."
```

After the fix, `lucy lsd run` should produce a `solutions.smi` (or `outlsd.out`) that `lucy lsd rank` can consume directly — no manual `outlsd 5 < compound.sol` step needed.

**Output file naming decision:** The current runner writes to `outlsd.out`. The orchestrator writes to `solutions.smi`. After the fix, the runner should write to a consistent name. Recommendation: `solutions.smi` (consistent with orchestrator, clearer semantics). The CLI `lsd_rank` command accepts any SMILES file path as its first argument, so the name is not hardcoded.

---

## Scope Boundary

Phase 73 is the **PLUMBING fix only**:

| In scope (Phase 73) | Out of scope |
|---------------------|--------------|
| Fix `_execute_lsd` stdin → file-arg invocation | SYME → BOND/COSY translation (Phase 74) |
| Fix `_run_outlsd` to use `.sol` + `"5"` arg | DEFF NOT → DEFF F/FEXP translation (Phase 74) |
| Unify duplicate `_run_outlsd` implementations | PyLSDOrchestrator constraint preservation (Phase 74) |
| Fix exit-255 (SYME/DEFF NOT cause LSD to error) | SolutionMerger empty-merge bug (Phase 74) |
| Regression tests for the fixed paths | Agent skill documentation (Phase 75) |
| `lucy lsd run` SMILES output usable by `lucy lsd rank` | Permutation file generation (Phase 74) |

**D-01 primary path:** After Phase 73, the single-run path (`lsd compound.lsd` → `compound.sol` → `outlsd 5` → SMILES) works end-to-end. Phase 74 adds `HMBC X Y 2 4` extended-range emission to `LSDInputGenerator` and fixes permutation constraint preservation; those depend on Phase 73's clean single-run path.

---

## CWD Sensitivity Analysis

### Current behavior
`_execute_lsd` already sets `cwd=output_dir`. When switching to file-argument mode, the `.sol` file will be written with the input file's stem as its name, in `output_dir`.

### CWD rule
`lsd arm_a.lsd` (relative path in CWD) → `arm_a.sol` in CWD.
`lsd /absolute/path/arm_a.lsd` (absolute path) → `arm_a.sol` in CWD (not in the file's directory).

**Fix implication:** Pass the absolute path of the input file as the positional argument, and set `cwd=output_dir`. The `.sol` will be written to `output_dir` with the correct stem name. This is exactly what the Phase 72 experiment does:
```python
lsd_result = subprocess.run(
    [str(LSD_BIN), str(lsd_file)],  # absolute path as positional arg
    cwd=EXPERIMENT_DIR,             # .sol lands in EXPERIMENT_DIR
)
```

### DEFF filter path sensitivity
`compound_native.lsd` uses absolute filter paths:
```
DEFF F1 "/Users/steinbeck/Dropbox/develop/LSD/Filters/ring3"
```
These are absolute paths, so CWD does not affect them. Files with relative `DEFF` paths would be CWD-sensitive — but Phase 73 scope does not generate new LSD files; it only fixes invocation of existing files.

---

## Shared Helper Recommendation

Both `runner.py` and `orchestrator.py` have `_run_outlsd` implementations. After the fix they should be identical (or nearly so). Recommended approach:

**Option A (preferred):** Move the correct implementation to a module-level function `_invoke_outlsd(output_dir: Path, sol_file: Path) -> Path | None` in `runner.py`. Both `LSDRunner._run_outlsd` and `PyLSDOrchestrator._run_outlsd` call this shared function.

**Option B:** Make `PyLSDOrchestrator._run_outlsd` delegate to `LSDRunner._run_outlsd` after the fix. Requires `PyLSDOrchestrator` to hold a reference to `self.runner.outlsd_path`.

Option A is cleaner because it avoids circular dependency and makes the single correct implementation visible at the module level.

---

## Regression Test Impact

### Phase 69 baseline test (`test_lsd_regression.py`)

The test uses the `LSDRunner` via `runner.run_file()` then manually handles the outlsd conversion. After the fix, the test will take the **Fallback B** branch (lines 222-238) because the fixed runner will write a `.sol` file to `tmp_path`:
```python
# Fallback B: .sol file from LSD filename-invocation (older LSD versions)
sol_files = list(tmp_path.glob("*.sol"))
assert sol_files, "..."
sol_file = sol_files[0]
with sol_file.open("r") as stdin_fh, fallback_smi.open("w") as stdout_fh:
    subprocess.run([outlsd_bin, "5"], stdin=stdin_fh, stdout=stdout_fh, check=True, timeout=30)
```

This branch is already implemented and correct. The 392-InChI baseline should be identical because the same LSD version produces the same solutions; only the delivery mechanism changes.

**Verdict:** `test_ibuprofen_no_4j_inchi_set_stable` should pass unchanged after the Phase 73 fix. The test may take a slightly different code path (Fallback B instead of the stdout-reconstruction path), but the InChI set will be the same.

### New regression tests for Phase 73

Required tests (with `@pytest.mark.skipif(shutil.which("LSD") is None, reason="LSD binary not installed")`):

1. **`test_runner_writes_sol_file`** — `runner.run_file(fixture.lsd)` → `output_dir / "fixture.sol"` exists and has non-zero size.
2. **`test_runner_produces_smiles`** — `runner.run_file(ibuprofen_no_4j.lsd)` → `output_dir / "solutions.smi"` contains exactly 392 valid SMILES lines (same count as the known baseline).
3. **`test_no_header_only_output`** — after fix, `solutions.smi` first line is a valid SMILES string, not `"outlsd: usage: outlsd p"`.
4. **`test_lsd_rank_end_to_end`** — `runner.run_file()` then `_perform_ranking(solutions.smi, shifts)` returns ranked results with `total_solutions=392` and `ranked_count > 0`.
5. **`test_runner_success_semantics`** — `result.success=True` when and only when solutions were found AND SMILES conversion succeeded (not the current "stdout has 10-line usage message" false-positive success).

---

## Common Pitfalls

### Pitfall 1: CWD vs Absolute Path

**What goes wrong:** `lsd compound.lsd` in `cwd=output_dir` works. But `lsd /abs/path/compound.lsd` in `cwd=output_dir` also works and writes `compound.sol` to `output_dir` (not to `/abs/path/`). If the absolute path is passed without setting CWD to `output_dir`, the `.sol` will land in the caller's working directory.

**How to avoid:** Always set `cwd=output_dir` when passing the file as an absolute-path argument. The Phase 72 experiment demonstrates the correct pattern.

**Warning signs:** `.sol` file appears in an unexpected directory; `glob("*.sol")` in `output_dir` finds nothing.

### Pitfall 2: Duplicate `_run_outlsd` Not Updated

**What goes wrong:** Fixing `runner._run_outlsd` but not updating `orchestrator._run_outlsd` (or vice versa) leaves a latent bug in one path. The orchestrator's version is currently correct; the risk is introducing a regression there while fixing the runner.

**How to avoid:** Create a shared helper function and have both call it. Then there is only one implementation to maintain.

**Warning signs:** `test_lsd_orchestrator.py` passes but `test_lsd_runner.py` fails, or vice versa.

### Pitfall 3: `_count_solutions` False Positive

**What goes wrong:** `_count_solutions` currently parses "N solutions found" from stderr. After the fix, if `lsd compound.lsd` also writes "N solutions found" to stderr, the count will still be correct. But if the CLI `success` flag is now set based on `.sol` file existence rather than stderr parsing, the `_count_solutions` logic may need adjustment.

**Actual LSD behavior (verified):** `lsd compound.lsd` writes "392 solutions found.\n" to stderr (same as stdin mode). So `_count_solutions` will still work correctly for the solution count.

**How to avoid:** Keep `_count_solutions` logic as-is; it reads from stderr and works in both modes. Do NOT change solution counting in Phase 73.

### Pitfall 4: DEFF Filter Paths (Out of Scope But Risk)

**What goes wrong:** Some LSD files use relative paths in `DEFF F1 "ring3"`. With the CWD change, relative paths resolve against `output_dir`, which may not contain the filter files.

**Phase 73 scope:** Phase 73 fixes runner.py only. The test fixtures (`ibuprofen_no_4j.lsd`) do not use DEFF filters. The Phase 74 scope is where native DEFF translation (absolute paths) is addressed.

**Warning signs:** LSD exits 255 with "error 150 - unknown file" on DEFF-filtered inputs.

### Pitfall 5: `solutions.smi` vs `outlsd.out` Naming

**What goes wrong:** The runner currently writes to `outlsd.out`; orchestrator writes to `solutions.smi`. After the fix, if the output file name changes, existing agent invocations that assume `outlsd.out` will break.

**How to avoid:** Document the output file name change in Phase 75 skill updates. For Phase 73, either keep `outlsd.out` (backward compatibility) or use `solutions.smi` (consistent with orchestrator). The `lsd_rank` CLI accepts any path, so either works — but the agent needs to know which to pass.

**Recommendation:** Use `solutions.smi` and document the change. The agent-readable CLAUDE.md already shows `outlsd 5 < compound.sol > solutions.smi` as the manual pattern.

---

## Architecture Patterns

### Recommended Project Structure (Phase 73 changes only)

```
src/lucy_ng/lsd/
├── runner.py              # Fix _execute_lsd (file-arg) + _run_outlsd (add shared helper)
├── orchestrator.py        # _run_outlsd delegates to shared helper in runner.py
└── parser.py              # Unchanged

tests/
├── test_lsd_runner.py     # Extend with 5 new integration tests (skipif LSD missing)
└── test_lsd_regression.py # Unchanged (Fallback B path will now be taken)
```

### Pattern: Correct LSD + outlsd Invocation

```python
# CORRECT — file argument mode
import subprocess
from pathlib import Path

def _invoke_lsd(lsd_path: Path, input_file: Path, output_dir: Path, timeout: int) -> subprocess.CompletedProcess:
    """Invoke LSD with file as positional argument.
    
    LSD writes {input_file.stem}.sol to output_dir (the CWD).
    """
    return subprocess.run(
        [str(lsd_path), str(input_file)],  # file as positional arg, NOT stdin
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=output_dir,                    # .sol lands here
    )

def _invoke_outlsd(outlsd_path: Path, sol_file: Path, output_dir: Path) -> Path | None:
    """Convert .sol to SMILES via outlsd.
    
    Source: orchestrator.py lines 255-295 (the correct implementation).
    Correct call: outlsd 5 < compound.sol > solutions.smi
    """
    smiles_file = output_dir / "solutions.smi"
    try:
        with sol_file.open("r") as fh:
            proc = subprocess.run(
                [str(outlsd_path), "5"],   # "5" = SMILES mode (required!)
                stdin=fh,                  # .sol file as stdin (NOT .lsd file)
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

---

## Validation Architecture

*(nyquist_validation not explicitly disabled in config.json → included)*

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | none detected (pytest discovers from pyproject.toml) |
| Quick run command | `pytest tests/test_lsd_runner.py -x` |
| Full suite command | `pytest tests/test_lsd_runner.py tests/test_lsd_regression.py tests/test_lsd_orchestrator.py -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RELI-01 | `lucy lsd run` writes `.sol` file | integration | `pytest tests/test_lsd_runner.py::TestLSDRunnerFixed::test_runner_writes_sol_file -x` | ❌ Wave 0 |
| RELI-01 | N LSD solutions → N SMILES (not 10-line header) | integration | `pytest tests/test_lsd_runner.py::TestLSDRunnerFixed::test_runner_produces_smiles -x` | ❌ Wave 0 |
| RELI-01 | `solutions.smi` passes to `lucy lsd rank` | integration | `pytest tests/test_lsd_runner.py::TestLSDRunnerFixed::test_lsd_rank_end_to_end -x` | ❌ Wave 0 |
| RELI-01 | Phase 69 baseline (392 InChIs) still matches | regression | `pytest tests/test_lsd_regression.py::TestLSDRegression::test_ibuprofen_no_4j_inchi_set_stable -x` | ✅ exists |

### Sampling Rate

- **Per task commit:** `pytest tests/test_lsd_runner.py -x`
- **Per wave merge:** `pytest tests/test_lsd_runner.py tests/test_lsd_regression.py -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_lsd_runner.py` — add `TestLSDRunnerFixed` class with 5 integration tests (skipif LSD missing)
- [ ] `tests/test_lsd_runner.py` — add mock-based unit test for the shared `_invoke_outlsd` helper

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| LSD binary | `runner._execute_lsd` | ✓ | 3.4.9 | Tests skip (`@pytest.mark.skipif`) |
| outlsd binary | `runner._run_outlsd` | ✓ | same package as LSD | Tests skip |
| pytest | All tests | ✓ | (project dependency) | — |
| rdkit | `test_lsd_regression.py` | ✓ | (project dependency) | — |

LSD binary location: `/Users/steinbeck/Dropbox/develop/LSD/LSD`
outlsd binary location: `/Users/steinbeck/Dropbox/develop/LSD/outlsd`
Both found via `shutil.which("LSD")` (on PATH) and confirmed at direct path.

---

## Security Domain

*(security_enforcement not set → treated as enabled)*

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | Yes (minimal) | LSD input files are researcher-controlled; subprocess invocation uses list form (not shell=True) — no shell injection risk |
| V6 Cryptography | No | Not applicable |

The subprocess calls use `[str(lsd_path), str(input_file)]` (list form), which is safe against shell injection. No change in security posture from the fix.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | LSD always writes `{stem}.sol` in CWD when given file as arg (not relative to the file's location) | .sol File Mechanics | Low — confirmed empirically for the `compound.lsd` → `compound.sol` case and `arm_a.lsd` → `arm_a.sol` in Phase 72 |
| A2 | LSD stdout header is always 9 lines before OUTLSD marker | Header-Strip Mechanism | Low — confirmed for `ibuprofen_no_4j.lsd`; formula-specific header lines may vary for molecules with different atom counts, but OUTLSD marker search handles this |
| A3 | Phase 69 regression test takes Fallback B path (not the stdout-reconstruction path) after the fix | Regression Test Impact | Low — Fallback B is implemented and the logic is: if `.sol` files exist in tmp_path, use them directly |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

Empty assumptions log is not accurate here: see above.

---

## Open Questions (RESOLVED)

1. **Output file name: `solutions.smi` vs `outlsd.out`** — RESOLVED: use `solutions.smi` (orchestrator convention) in the fixed runner. Phase 75 skill docs update to the new name. The naming consistency is tracked as a Phase 75 doc item, not a Phase 73 blocker.

2. **`LSDResult.solutions` field population** — RESOLVED: keep `result.solutions` population unchanged; it reads `.sol` content which is now present after the file-argument fix. `cli/lsd.py lsd_run` uses only `output_files` paths; no caller depends critically on `result.solutions`.

---

## Sources

### Primary (HIGH confidence)

- Empirical LSD binary testing (this session) — stdin vs file-arg behavior, `.sol` file writing, exit codes
- `src/lucy_ng/lsd/runner.py` — exact bug lines quoted with line numbers
- `src/lucy_ng/lsd/orchestrator.py` lines 119, 255-295 — correct pattern and explicit bug documentation
- `tests/test_lsd_regression.py` — workaround pattern and regression baseline
- `.planning/phases/72-design-re-validation/experiment/run_experiment.py` — working invocation
- `.planning/phases/72-design-re-validation/experiment/results.json` — empirical proof (2/2 aromatic, ibuprofen found)

### Secondary (MEDIUM confidence)

- `.planning/v8.0-UAT-POSTMORTEM.md` — forensic analysis of the v8.0 failures
- `CASE-PROGRESS.md` line 244 — agent-observed "exit 255, stdin-Modus → keine .sol" documented in the UAT run
- `.planning/phases/65-hypothesis-gate/outlsd.out` — the exact 10-line usage artifact from the buggy runner

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Bug identification: HIGH — both bugs reproduced and verified empirically
- Fix pattern: HIGH — correct pattern exists in orchestrator.py and was used in Phase 72 experiment
- Regression impact: HIGH — regression test code read and traced; Fallback B branch verified correct
- CWD semantics: HIGH — empirically confirmed (file-arg mode, absolute path, output in CWD)

**Research date:** 2026-05-20
**Valid until:** Stable — LSD-3.4.9 binary behavior does not change; Python subprocess semantics are stable
