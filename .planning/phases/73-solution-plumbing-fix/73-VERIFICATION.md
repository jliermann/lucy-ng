---
phase: 73-solution-plumbing-fix
verified: 2026-05-21T00:00:00Z
status: passed
score: 6/6
overrides_applied: 0
---

# Phase 73: Solution Plumbing Fix — Verification Report

**Phase Goal:** Fix lucy lsd run / outlsd conversion so LSD solutions reliably become SMILES end-to-end (keystone plumbing fix).
**Verified:** 2026-05-21
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | runner.run_file() on a valid LSD file writes a .sol file to output_dir | VERIFIED | `_execute_lsd` copies input to output_dir then invokes `[str(self.lsd_path), lsd_input_name]` (relative filename) with `cwd=output_dir`; `sol_file = output_dir / f"{input_file.stem}.sol"` at line 270 |
| 2 | runner.run_file() produces solutions.smi with N valid SMILES lines (not a 10-line usage header) | VERIFIED | `_invoke_outlsd` uses `[str(outlsd_path), "5"]` with `.sol` file handle as stdin at line 35; `solutions.smi` written at line 43; `test_runner_produces_smiles` asserts 392 non-empty lines |
| 3 | result.success is True only when both .sol and solutions.smi exist; no false-positive from stderr alone | VERIFIED | Line 283: `success = sol_file.exists() and smiles_path is not None`; old `proc.returncode == 0 or solution_count > 0` removed |
| 4 | outlsd invocation uses [outlsd_path, '5'] with the .sol file as stdin — not the .lsd file | VERIFIED | `_invoke_outlsd` lines 33-41: `with sol_file.open("r") as fh: subprocess.run([str(outlsd_path), "5"], stdin=fh, ...)`; `test_invoke_outlsd_unit` verifies argv and stdin via monkeypatch; test passes |
| 5 | Phase 69 regression baseline (392 ibuprofen InChIs) still matches after the fix | VERIFIED | `ibuprofen_no_4j.expected_inchis.txt` contains 392 InChIs; regression test Path A branch reads runner-produced `solutions.smi` directly when it exists; SUMMARY records 3/3 regression tests passed |
| 6 | runner.py and orchestrator.py share a single _invoke_outlsd implementation | VERIFIED | `_invoke_outlsd` defined once at module level in runner.py (lines 13-47); orchestrator line 31 imports it: `from lucy_ng.lsd.runner import LSDResult, LSDRunner, _invoke_outlsd`; orchestrator `_run_outlsd` (lines 255-274) delegates with a one-liner: `return _invoke_outlsd(Path(outlsd_path), sol_files[0], perm_dir)` |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/lucy_ng/lsd/runner.py` | Fixed `_execute_lsd` (file-arg mode), fixed `_run_outlsd`, shared `_invoke_outlsd` helper | VERIFIED | `_invoke_outlsd` at lines 13-47; `_execute_lsd` uses relative-filename invocation at line 251; `_run_outlsd` delegates at line 397 |
| `src/lucy_ng/lsd/orchestrator.py` | `_run_outlsd` delegates to `runner._invoke_outlsd` — no duplicate logic | VERIFIED | Import at line 31; delegation at line 274; old private copy replaced |
| `tests/test_lsd_runner.py` | `TestLSDRunnerFixed` class with 6 tests (5 skipif-gated, 1 mock-based) | VERIFIED | Class at lines 257-492; 6 methods: test_runner_writes_sol_file, test_runner_produces_smiles, test_no_header_only_output, test_lsd_rank_end_to_end, test_runner_success_semantics, test_invoke_outlsd_unit |
| `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt` | 392 baseline InChIs | VERIFIED | 392 lines of real InChI strings; first line `InChI=1S/C13H18O2/...` |
| `src/lucy_ng/cli/lsd.py` | Phase 68/69 work intact: `_validate_and_parse_inventory`, `_perform_ranking` with `_silent`, `validate-inventory` command | VERIFIED | `_perform_ranking` at line 207 with `_silent: bool = False` param; `_validate_and_parse_inventory` at line 346; `validate-inventory` command at line 434 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `runner._execute_lsd` | LSD binary | `subprocess.run([str(self.lsd_path), lsd_input_name], cwd=output_dir)` | VERIFIED | Line 250-255; no `input=` kwarg; relative filename ensures `.sol` lands in `output_dir` |
| `runner._invoke_outlsd` | outlsd binary | `subprocess.run([str(outlsd_path), "5"], stdin=fh, ...)` | VERIFIED | Lines 34-41; "5" present; stdin is file handle of `.sol` file |
| `orchestrator._run_outlsd` | `runner._invoke_outlsd` | `from lucy_ng.lsd.runner import _invoke_outlsd` | VERIFIED | Import at line 31; call at line 274 with `Path(outlsd_path)`, `sol_files[0]`, `perm_dir` |
| `_execute_lsd` success flag | `.sol` file existence + `smiles_path` | `success = sol_file.exists() and smiles_path is not None` | VERIFIED | Line 283; both conditions required; no false-positive from stderr alone |

### Data-Flow Trace (Level 4)

Not applicable. This phase fixes subprocess plumbing (no React/dynamic-data rendering artifacts). The key data flow is: LSD binary writes `.sol` → `_invoke_outlsd` pipes `.sol` to `outlsd 5` → reads stdout → writes `solutions.smi`. All three steps are substantiated by code inspection and the mock test verifying stdin/argv.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `_invoke_outlsd` importable from module level | `python -c "import sys; sys.path.insert(0,'src'); from lucy_ng.lsd.runner import _invoke_outlsd; ..."` | prints "imports ok" | PASS |
| Mock-based unit test verifying argv and stdin | `pytest tests/test_lsd_runner.py::TestLSDRunnerFixed::test_invoke_outlsd_unit -v` | 1 passed | PASS |
| Both modules import without error | `from lucy_ng.lsd.runner import _invoke_outlsd; from lucy_ng.lsd.orchestrator import PyLSDOrchestrator` | imports ok | PASS |

LSD-dependent integration tests (test_runner_writes_sol_file, test_runner_produces_smiles, test_no_header_only_output, test_lsd_rank_end_to_end, test_runner_success_semantics) require the LSD binary and are skipif-gated. They are declared to have passed in the SUMMARY (6 passed, 392-InChI regression confirmed) and verified by code inspection; the mock test confirms the invocation contract without needing the binary.

### Probe Execution

No `probe-*.sh` files declared or found for this phase. Step 7c skipped.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| RELI-01 | 73-01-PLAN.md | LSD solutions reliably convert to ranked SMILES with no silent solution loss | SATISFIED | `_invoke_outlsd` uses correct `outlsd 5` + `.sol` stdin invocation; `_execute_lsd` file-arg mode writes `.sol`; `success` flag requires both files; `test_lsd_rank_end_to_end` exercises full pipeline |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `orchestrator.py` | 119, 122, 194 | Stale class-level docstring: "bypass bug" / "known bug" / "bypass buggy `_run_outlsd`" | INFO | Docstring describes pre-Phase-73 state; `_run_outlsd` method docstring at line 256 is correct ("Delegates to runner._invoke_outlsd"); code behavior is correct; misleading prose only |

No TBD/FIXME/XXX debt markers found in any phase-modified file. No placeholder or stub patterns found. The `outlsd.out` in `tests/fixtures/regression/` is a historical artifact preserved as proof of the old buggy behavior, not new output.

### Human Verification Required

None. All phase truths are verifiable by code inspection and the mock-based unit test. The LSD-dependent integration tests are skipif-gated for environments without the binary, and the SUMMARY records those tests having passed against the real binary (a2b3a17, 6 passed).

### Gaps Summary

No gaps. All 6 must-haves are VERIFIED.

The three bugs described in the PLAN are confirmed fixed:
- Bug 1 (stdin invocation): replaced with file-argument mode using relative filename and `cwd=output_dir`.
- Bug 2 (outlsd wrong args): unified into `_invoke_outlsd` with `["5"]` and `.sol` as stdin.
- Bug 3 (false-positive success): `success = sol_file.exists() and smiles_path is not None`.

The scope boundary is respected: `generator.py` contains no SYME or DEFF NOT changes (those are Phase 74). Phase 68/69 CLI work (`_perform_ranking`, `_validate_and_parse_inventory`, `validate-inventory`) is intact in `cli/lsd.py`.

The one informational note: the `PyLSDOrchestrator` class docstring (lines 112-124) still describes the bypass pattern in present tense ("The outlsd invocation bypasses LSDRunner._run_outlsd() which has a known bug"). The `_run_outlsd` method docstring is correct. This is documentation debt, not a code defect.

---

_Verified: 2026-05-21_
_Verifier: Claude (gsd-verifier)_
