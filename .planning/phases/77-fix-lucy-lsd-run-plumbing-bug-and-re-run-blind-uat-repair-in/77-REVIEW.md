---
phase: 77-fix-lucy-lsd-run-plumbing-bug-and-re-run-blind-uat-repair-in
reviewed: 2026-06-01T18:00:00Z
depth: standard
files_reviewed: 3
files_reviewed_list:
  - src/lucy_ng/lsd/runner.py
  - src/lucy_ng/lsd/generator.py
  - src/lucy_ng/cli/detect.py
findings:
  critical: 1
  warning: 3
  info: 2
  total: 6
status: partial_fixed
fixed: [CR-01, WR-01, WR-02, IN-01]
accepted_advisory: [WR-03, IN-02]
---

# Phase 77: Code Review Report

**Reviewed:** 2026-06-01T18:00:00Z
**Depth:** standard
**Files Reviewed:** 3
**Status:** issues_found

## Summary

Phase 77 delivers two code fixes (FIX-01: `_execute_lsd` filter-file copy + `_invoke_outlsd` fail-loud hardening; FIX-02: `detect_aromatic_cosy_pairs()` + `lucy detect aromatic-cosy` CLI) against the Phase 76 UAT failures. The root-cause diagnosis is correct and the core implementation is sound. However, one critical residual silent-failure path survives the new fail-loud logic, three warning-level quality issues are present, and two info items round out the findings.

The most dangerous finding (CR-01) is a new silent-failure vector introduced by the partial fail-loud predicate: outlsd error output that does not match any of the three guarded patterns is written verbatim to `solutions.smi` as if it were valid SMILES, and the runner reports `success=True`. The Phase 77 fixes eliminate the specific `"This is not a file for OUTLSD."` failure mode but leave the door open for any other unexpected outlsd output.

---

## Critical Issues

### CR-01: Incomplete fail-loud predicate — unknown outlsd error output written as valid SMILES

**File:** `src/lucy_ng/lsd/runner.py:44-65`

**Issue:** `_invoke_outlsd` guards against exactly three known bad-output patterns (empty, `"This is not a file for OUTLSD"`, starts with `"outlsd:"`). Any outlsd error output that does not match one of those three patterns passes all checks, is written to `solutions.smi` via `smiles_file.write_text(proc.stdout)` (line 59), and causes `_execute_lsd` to report `success=True` (line 304: `success = sol_file.exists() and smiles_path is not None`).

Concrete examples of output that would slip through:
- `"Error: unable to open input file\n"` — does not start with `"outlsd:"`, does not contain the known error string, is not empty.
- A future outlsd version that changes its error prefix from `outlsd:` to `error:`.
- `"0 solutions"` — hypothetically if outlsd outputs a plain-text summary when a `.sol` file has no actual solutions.

The Phase 77 fix is a significant improvement over the previous state (the specific reproducing error string is now caught), but the fix is not structurally sound because it relies on an enumerated list of known bad strings rather than validating that the output IS valid SMILES. The RESEARCH.md explicitly identified RDKit validation as an optional stronger guarantee and deferred it; the resulting incomplete predicate is still a silent-failure risk for any future outlsd failure mode not yet observed.

**Fix:** Add a SMILES content validation step after the string checks, before writing to disk. The RESEARCH.md already documents the pattern:

```python
# After the three string guards and before smiles_file.write_text():
lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
if not lines:
    raise RuntimeError("outlsd produced no parseable lines")
try:
    from rdkit import Chem
    first_smiles = lines[0].split()[0]
    if Chem.MolFromSmiles(first_smiles) is None:
        raise RuntimeError(
            f"outlsd output is not valid SMILES: {lines[0][:100]!r}. "
            "Full output may be an unrecognised error message."
        )
except ImportError:
    # RDKit not available — string checks above are the last line of defence
    pass
```

RDKit is an existing project dependency (pyproject.toml); this does not add a new requirement. The `ImportError` fallback preserves current behaviour in environments without RDKit.

---

## Warnings

### WR-01: `_invoke_outlsd` timeout is silently swallowed and loses diagnostic information

**File:** `src/lucy_ng/lsd/runner.py:63-65`

**Issue:** The `except Exception: pass` catch-all at lines 63–65 is reached by `subprocess.TimeoutExpired` (which inherits from `Exception`) raised when the outlsd 30-second timeout fires. The exception is swallowed; `_invoke_outlsd` returns `None`; `_execute_lsd` sees `smiles_path is None` and sets `success=False` with no stderr message explaining the timeout. The caller (e.g., `lucy lsd run`) gets a failure with an empty `stderr`, giving no indication that outlsd timed out rather than that LSD itself failed.

Note: this is a pre-existing weakness that is not worsened by Phase 77. However, the Phase 77 redesign of the except structure was an opportunity to fix it and did not.

**Fix:**

```python
    except RuntimeError:
        raise  # fail-loud errors propagate to _execute_lsd
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            "outlsd timed out after 30 seconds — .sol file may be very large"
        )
    except Exception as e:
        # All other errors (FileNotFoundError, etc.): return None with no diagnostics
        # These indicate an infrastructure problem, not a bad .sol file.
        _ = e
    return None
```

### WR-02: Integration test `test_ring_exclusion_lsd_produces_smiles` does not assert `result.success`

**File:** `tests/test_lsd_runner.py:549-581`

**Issue:** The regression test for FIX-01A calls `runner.run_file()` but discards the returned `LSDResult` (line 561: result is not captured). It then asserts that `solutions.smi` exists (line 564) and contains valid SMILES. This means the test does not verify that `LSDResult.success` is `True` after the fix. If a future regression introduces a code path where `solutions.smi` is written but `success` is set to `False` (or vice versa), the test would not catch it.

This matters because `success=True` is the contract that downstream consumers (the `lucy lsd run` CLI) check to determine whether to proceed with ranking.

**Fix:**

```python
result = runner.run_file(lsd_fixture, output_dir=tmp_path, timeout=120)
assert result.success is True, (
    f"LSDResult.success must be True after successful run. stderr: {result.stderr!r}"
)
```

### WR-03: `detect_aromatic_cosy_pairs` aromatic range includes non-aromatic alkenes — no user-visible warning

**File:** `src/lucy_ng/lsd/generator.py:637`

**Issue:** The `aromatic_range` default is `(100.0, 165.0)` which covers all classical aromatic carbons but also captures non-aromatic sp2 carbons (olefinic CH groups such as those in conjugated dienes and cyclic alkenes). Two equal-sized groups of olefinic CH signals at, say, 120 and 135 ppm would be cross-paired and emitted as aromatic COSY equivalences, potentially generating incorrect LSD constraints. The function name (`detect_aromatic_cosy_pairs`) implies aromatic-ring semantics, but the implementation uses only a chemical-shift filter with no aromaticity verification.

There is no user-visible warning when the function is called with groups that fall in the ambiguous 100–165 ppm range but lack unambiguous aromatic multiplicity evidence.

**Fix (short-term):** Tighten the default range to `(118.0, 145.0)` which better excludes typical olefinic carbons while retaining para-disubstituted benzene signals. Alternatively, add an optional `require_multiplicity: bool = False` parameter that, when True, only accepts groups where all shifts have `"CH"` (not `"CH/CH3"`) multiplicity, and document the ambiguity in the function's docstring.

**Fix (longer-term):** Accept multiplicity evidence from the upstream `group_signals` call (already available in `SignalGroup.multiplicities`) and filter for `"CH"` / `None` multiplicities within the aromatic range before pairing. This is the pattern described in the RESEARCH.md recommended algorithm but was simplified away in the implementation.

---

## Info

### IN-01: `test_ring_exclusion_lsd_produces_smiles` skipif uses `"LSD"` (uppercase) while `LSDRunner._find_lsd` uses `"lsd"` (lowercase)

**File:** `tests/test_lsd_runner.py:545-546`

**Issue:** The skipif guard checks `shutil.which("LSD")` (uppercase). `LSDRunner._find_lsd()` calls `shutil.which("lsd")` (lowercase). On case-sensitive Linux filesystems, these are different lookups: the test can be skipped when the runner would find the binary, or vice versa. All existing tests in `TestLSDRunnerFixed` have the same inconsistency (lines 266, 288, 318, 348, 390), but the Phase 77 integration test introduces the same pattern again.

**Fix:** Use consistent casing. The runner uses lowercase:

```python
@pytest.mark.skipif(
    shutil.which("lsd") is None,  # matches LSDRunner._find_lsd()
    reason="LSD binary not installed",
)
```

### IN-02: `aromatic_cosy_command` emits no JSON-mode warning when no pairs are detected

**File:** `src/lucy_ng/cli/detect.py:250-258`

**Issue:** In `--format text` mode, the command prints `"No aromatic equivalence pairs detected."` when the result is empty. In `--format json` mode it outputs `{"cosy_pairs": []}` with no explanation. Callers consuming JSON output have no way to distinguish "no groups detected at all" from "groups detected but no pair-able groups found" from "groups outside aromatic range filtered out". This is a DX issue for agent callers that parse JSON output.

**Fix:** Add an optional `"warning"` key to the JSON output when pairs is empty:

```python
if output_format == "json":
    import json
    result: dict = {"cosy_pairs": [list(p) for p in pairs]}
    if not pairs:
        result["warning"] = "No aromatic equivalence groups detected. Check shifts are in aromatic range (100–165 ppm) and that equivalent signals were grouped."
    click.echo(json.dumps(result))
```

---

_Reviewed: 2026-06-01T18:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
