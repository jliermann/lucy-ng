---
phase: 69-cli-command-and-regression-suite
reviewed: 2026-05-19T19:19:43Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - src/lucy_ng/cli/pylsd.py
  - src/lucy_ng/cli/lsd.py
  - src/lucy_ng/cli/main.py
  - src/lucy_ng/lsd/generator.py
  - tests/test_pylsd_cli.py
  - tests/test_lsd_form_tolerance.py
  - tests/test_lsd_regression.py
  - tests/test_cli_lsd.py
  - tests/test_lsd_generator.py
findings:
  critical: 1
  warning: 5
  info: 2
  total: 8
status: issues_found
---

# Phase 69: Code Review Report

**Reviewed:** 2026-05-19T19:19:43Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Phase 69 delivers the `lucy pylsd run` CLI subcommand, helper extraction (`_perform_ranking`,
`_validate_and_parse_inventory`), a FORM-tolerance living regression test, and an ibuprofen
InChI-set regression baseline.  The architecture is sound and the D-13/D-14 design intent
is correctly implemented.  One blocker was found: the `--format json` output path emits two
JSON objects to stdout because `_perform_ranking` already echoes its result via `click.echo`
before returning the dict, and the caller then echoes a second outer wrapper.  Any downstream
consumer calling `json.loads(output)` will fail.  Five warnings round out correctness and
robustness concerns.

---

## Critical Issues

### CR-01: Double JSON echo on `lucy pylsd run --format json`

**File:** `src/lucy_ng/cli/pylsd.py:259-272`
**Issue:** When `output_format == "json"`, `pylsd_run` calls
`_perform_ranking(..., output_format="json")`. Inside `_perform_ranking`
(`lsd.py:304`), `click.echo(json.dumps(data, indent=2))` fires unconditionally,
writing the inner ranking JSON to stdout.  Control then returns to `pylsd_run`,
which calls `click.echo(json.dumps(outer, indent=2))` (line 272), writing the
outer wrapper JSON to stdout.

stdout therefore contains two separate JSON documents.  Any call to
`json.loads(result.output)` by the CASE agent or any other consumer will raise a
`JSONDecodeError`.  The test at `test_pylsd_cli.py:155` passes only because it
patches `_perform_ranking` to return a dict without triggering its internal
`click.echo`, hiding the production bug.

The comment on line 259 explicitly says "_perform_ranking with output_format='json'
echoes JSON + returns dict" — the design acknowledges the dual behaviour but the
caller should not echo a second wrapper after a side-effectful helper has already
written to stdout.

**Fix:** Add a `silent` parameter to `_perform_ranking` (defaulting to `False` for
backward-compat with `lsd rank`), or pass `output_format="json"` only to get the
data dict back and suppress the inner echo when called from `pylsd_run`.  The
simplest approach:

```python
# In lsd.py: _perform_ranking — add silent kwarg
def _perform_ranking(
    smiles_file: str | Path,
    experimental_shifts: list[float],
    top: int = 10,
    tolerance: float = 3.0,
    table: str | Path | None = None,
    output_format: str = "text",
    _silent: bool = False,        # NEW: suppress click.echo when True
) -> dict | None:
    ...
    if output_format == "json":
        ...
        if not _silent:
            click.echo(json.dumps(data, indent=2))
        return data

# In pylsd.py: pylsd_run — pass _silent=True
rank_data = _perform_ranking(
    merge_result.merged_smi,
    experimental_shifts,
    output_format="json",
    _silent=True,         # suppress inner echo; we echo the outer wrapper below
)
```

Alternatively, restructure so `_perform_ranking` never echoes in "json" mode
(breaking change to `lsd rank`'s current behaviour), or factor out the serialisation
logic from the echo.

---

## Warnings

### WR-01: Malformed inventory (START without END) silently degrades instead of exiting 1

**File:** `src/lucy_ng/cli/lsd.py:174-204` and `src/lucy_ng/cli/pylsd.py:51`
**Issue:** `_extract_inventory_block` returns `None` when the START delimiter is
present but the END delimiter is absent (line 200-203 path).
`_validate_and_parse_inventory` receives `None` and returns `None` — the "no block"
path — without raising `SystemExit(1)`.  `_extract_suspects` then falls through to
the D-13b grep fallback with a "No v2 inventory block" warning, silently discarding
a structurally corrupt file.

This is **inconsistent** with `lsd validate-inventory`, which exits 1 for the same
file.  An agent that wrote a partial inventory (e.g., truncated write) would get a
silent fallback rather than an error that would alert the developer.

There are also no tests in `test_pylsd_cli.py` covering this path through
`_extract_suspects`.

**Fix:** In `_validate_and_parse_inventory`, check whether the content has the
START delimiter; if it does but `_extract_inventory_block` returned `None`, treat
it as a corrupted block and raise `SystemExit(1)`:

```python
raw_json = _extract_inventory_block(content)
if raw_json is None:
    if "=== CONSTRAINT INVENTORY v2 ===" in content:
        click.echo(
            "Error: Malformed inventory block — START delimiter found but END "
            "delimiter is missing. Reconcile the LSD file before running pylsd.",
            err=True,
        )
        raise SystemExit(1)
    return None  # no block at all — not an error
```

---

### WR-02: No LSD-binary integration test for comment-form FORM tolerance

**File:** `tests/test_lsd_form_tolerance.py:81` and
`tests/fixtures/form_tolerance/minimal_with_form.lsd`
**Issue:** The xfail integration test (`test_form_line_produces_identical_solutions`)
uses a fixture containing a **bare** `FORM C2H6` line — the very line format that
LSD-3.4.9 rejects (error 102).  The test is correctly marked `xfail` for this
reason.

However, `emit_form()` now generates `; FORM C2H6` (the comment form).  There is
no fixture and no integration test that runs the LSD binary with a file containing
the **comment-form** `; FORM` line.  The claim that LSD silently ignores `; FORM`
(because it starts with `;`) rests on general knowledge of LSD comment syntax, not
on empirical verification in the test suite.  If a future LSD version changed
comment parsing, this would go undetected.

**Fix:** Add a second fixture `minimal_with_comment_form.lsd` containing
`; FORM C2H6` and a corresponding `@pytest.mark.skipif(LSD is None)` test (without
`xfail`) asserting it produces the same solution count as `minimal.lsd`:

```python
# tests/fixtures/form_tolerance/minimal_with_comment_form.lsd
; Minimal LSD test: ethane C2H6 — with FORM as comment
; FORM C2H6
MULT 1 C 3 3
MULT 2 C 3 3
HSQC 1 1
HSQC 2 2
EXIT
```

```python
@pytest.mark.skipif(shutil.which("LSD") is None, reason="LSD binary not installed")
def test_comment_form_line_does_not_affect_solutions(self, tmp_path: Path) -> None:
    """LSD silently ignores '; FORM' comment lines (the emit_form() output)."""
    ...
```

---

### WR-03: `outlsd` subprocess return code unchecked in primary regression-test path

**File:** `tests/test_lsd_regression.py:193-211`
**Issue:** Both `subprocess.run` calls in the primary code paths (lines 193 and 204)
do not use `check=True` and do not inspect `proc.returncode`.  If `outlsd` fails
(wrong input format, version incompatibility), `proc.stdout` will be empty or
contain only an error message.  `fallback_smi.write_text(proc.stdout)` then writes
garbage, `_smiles_to_inchis` returns an empty set, and the final assertion
`actual_inchis == baseline_inchis` fails with a generic "InChI set changed" message
that does not indicate `outlsd` failed.

The Fallback B path correctly uses `check=True` (line 226), making the inconsistency
visible.

**Fix:** Add return-code checks (or use `check=True`) and a guard assertion after
parsing:

```python
proc = subprocess.run(
    [outlsd_bin, "5"],
    stdin=sol_file.open("r"),
    capture_output=True,
    text=True,
    timeout=30,
    check=True,          # raises CalledProcessError on non-zero exit
)
fallback_smi.write_text(proc.stdout)
smiles_path = fallback_smi

...

actual_inchis = _smiles_to_inchis(smiles_path)
assert actual_inchis, (
    f"No InChIs parsed from {smiles_path} — outlsd may have failed silently. "
    f"Check the SMILES file content: {smiles_path.read_text()[:200]}"
)
```

---

### WR-04: Unclosed file handle in regression test subprocess call

**File:** `tests/test_lsd_regression.py:195`
**Issue:** `sol_file.open("r")` creates a file handle that is passed directly to
`subprocess.run` as `stdin=` but is never explicitly closed.  Python's garbage
collector will eventually close it, but this is a resource leak that can cause
`ResourceWarning` noise under pytest and may cause flaky failures on Windows
(where unclosed handles prevent file deletion).

The Fallback B path at line 221 correctly uses a `with` context manager.

**Fix:**
```python
with sol_file.open("r") as stdin_fh:
    proc = subprocess.run(
        [outlsd_bin, "5"],
        stdin=stdin_fh,
        capture_output=True,
        text=True,
        timeout=30,
    )
```

---

### WR-05: Unused variable `lsd_file_str` in `_validate_and_parse_inventory`

**File:** `src/lucy_ng/cli/lsd.py:359`
**Issue:** `lsd_file_str = str(lsd_file)` is assigned but never read in the function
body.  The function immediately converts `lsd_file` to a `Path` on the next line and
uses the `Path` throughout.  This is dead code that suggests a refactoring artifact —
`lsd_file_str` was probably used in an older version for error messages (the
`lsd_validate_inventory` command still uses `lsd_file` directly from the Click
argument).  Mypy strict mode should flag this.

**Fix:** Delete the unused assignment:
```python
# Remove this line:
lsd_file_str = str(lsd_file)
```

---

## Info

### IN-01: `run_report_path` in JSON output is not guaranteed absolute

**File:** `src/lucy_ng/cli/pylsd.py:270`
**Issue:** `"run_report_path": str(merge_result.run_report)` serialises the
`Path` as-is.  When `--working-dir` is a relative path (or the default
`lsd_path.parent / "pylsd_run"` is relative because `lsd_path` was given as a
relative path), the JSON field contains a relative path.  A CASE agent consuming
this JSON from a different working directory cannot resolve it.

**Fix:** Use `.resolve()` to guarantee an absolute path in the output:
```python
"run_report_path": str(merge_result.run_report.resolve()),
```

---

### IN-02: `pylsd` group not listed in `cli` help text

**File:** `src/lucy_ng/cli/main.py:30-41`
**Issue:** The `\b` help block in the `cli` group docstring lists all major commands
but omits `pylsd`.  A user running `lucy --help` would not see the new subcommand
in the formatted help output.

**Fix:** Add `pylsd` to the help block:
```python
"""
...
Commands:

\b
  read        Read NMR spectra (1D, 2D)
  pick        Peak picking from spectra
  analyze     Analysis tools (symmetry detection)
  dereplicate Match against reference databases
  predict     Predict NMR chemical shifts
  detect      Statistical detection (hybridisation)
  lsd         LSD structure elucidation
  pylsd       PyLSD multi-run orchestration (4J HMBC handling)
  visualize   Generate NMR correlation diagrams
  ...
"""
```

---

_Reviewed: 2026-05-19T19:19:43Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
