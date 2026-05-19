# FORM-Tolerance Finding: LSD Binary Does NOT Ignore FORM

**Status: CONFIRMED — FORM is NOT tolerated by LSD-3.4.9 (developer confirmed 2026-05-19)**
**Phase 66 compatibility concern: RESOLVED — emit_form() will emit `; FORM` comment (Option 3)**
**Date: 2026-05-19**
**Test: `pytest tests/test_lsd_form_tolerance.py::TestLSDFormTolerance::test_form_line_produces_identical_solutions`**

---

## Hypothesis

LSD binary (LSD-3.4.9) silently ignores an unknown `FORM` command and produces identical solutions compared to a file without the `FORM` line.

This hypothesis was required to confirm that Phase 66's `LSDInputGenerator.emit_form()` (which adds a `FORM` declaration to files generated in `pylsd_mode`) would be safe to use with the existing `lucy lsd run` CLI.

---

## Setup

**LSD version:** LSD-3.4.9

```
LSD 2>&1 | head -1
LSD-3.4.9
```

**Test environment:**
- Platform: macOS (Darwin 25.3.0)
- Python: 3.12.2
- pytest: 9.0.2
- LSD binary: `/Users/steinbeck/Dropbox/develop/LSD/LSD` (confirmed on PATH via `shutil.which("LSD")`)
- outlsd binary: confirmed available (`LSDRunner.is_outlsd_available()`)

**Test date:** 2026-05-19

---

## Method

Two minimal LSD files were created representing the same molecule (ethane, C2H6):

**`tests/fixtures/form_tolerance/minimal.lsd`** (baseline, no FORM):
```
; Minimal LSD test: ethane C2H6
MULT 1 C 3 3
MULT 2 C 3 3
HSQC 1 1
HSQC 2 2
EXIT
```

**`tests/fixtures/form_tolerance/minimal_with_form.lsd`** (FORM variant):
```
; Minimal LSD test: ethane C2H6 — with FORM line
FORM C2H6
MULT 1 C 3 3
MULT 2 C 3 3
HSQC 1 1
HSQC 2 2
EXIT
```

Both files were run via `LSDRunner.run_file()` with a 30-second timeout. Solution counts were compared.

Test: `tests/test_lsd_form_tolerance.py::TestLSDFormTolerance::test_form_line_produces_identical_solutions`

---

## Output

### Baseline (no FORM line)

```
result_without.success = True
result_without.solution_count = 1
result_without.stdout = (1 solution found)
```

### FORM variant

```
result_with.success = False
result_with.solution_count = 0
result_with.stdout = "error 102 - 1 commands read\nUnknown command name: FORM\n"
result_with.return_code = 255
```

### Test result: FAILED

```
pytest tests/test_lsd_form_tolerance.py -v
FAILED tests/test_lsd_form_tolerance.py::TestLSDFormTolerance::test_form_line_produces_identical_solutions
```

**LSD-3.4.9 explicitly rejects the FORM command with:**
```
error 102 - 1 commands read
Unknown command name: FORM
```

Return code 255 (LSD error exit).

---

## Conclusion

**The hypothesis is FALSE.** LSD-3.4.9 does NOT silently ignore the `FORM` command. It reports `error 102 - Unknown command name: FORM` and exits with return code 255, producing zero solutions.

### Phase 66 Compatibility Concern

**This is a Phase 66 compatibility concern requiring re-evaluation before Phase 70 ships.**

Phase 66 added `LSDInputGenerator.emit_form()` to generate a `FORM <formula>` line in LSD files when `pylsd_mode=True`. If the Phase 69 `lucy pylsd run` CLI passes these files directly to the LSD binary, every `pylsd_mode` run would fail with `error 102 - Unknown command name: FORM`.

**Required action before Phase 70:**
One of the following mitigations must be implemented:

1. **Strip FORM from LSD input before running the binary** (recommended): The CLI or LSDRunner strips `FORM` lines from input files generated in `pylsd_mode` before passing them to LSD. The `FORM` field serves as documentation within the inventory block JSON — it does not need to be in the LSD binary input.

2. **Remove `emit_form()` from LSDInputGenerator**: If no other consumer of these files needs the `FORM` line, remove the emission from Phase 66's generator entirely.

3. **Use `FORM` only in comments**: Replace `FORM C2H6` with `; FORM C2H6` (comment) so the formula is documented but not parsed by LSD.

Option 1 is least disruptive to Phase 66. Option 3 preserves readability.

---

## Mitigation Chosen

Mitigation: Phase 66's `emit_form()` will be amended (post-Phase-69) to emit `; FORM C13H18O2` (LSD comment) instead of `FORM C13H18O2` (rejected LSD command). The formula remains documented in the file for human readers and inventory-block consumers while LSD silently ignores the line. See Phase 66 backport commit.

This corresponds to Option 3 from the mitigation list above. It is the least invasive change: the formula information is preserved as a human-readable comment, the inventory block JSON continues to carry the formula as structured data, and no stripping logic is needed in the CLI or LSDRunner.

---

## Reproducibility Notes

This test is a living regression captured in:

```
pytest tests/test_lsd_form_tolerance.py -v
```

- `test_form_tolerance_fixtures_exist` runs on any machine (no LSD binary required)
- `test_form_line_produces_identical_solutions` runs when `LSD` binary is on PATH

If a future LSD version changes this behaviour (e.g., starts accepting FORM silently), `test_form_line_produces_identical_solutions` will PASS, and this document should be updated to reflect the new finding and mark the Phase 66 compatibility concern resolved.

To re-run and update this document:
```bash
pytest tests/test_lsd_form_tolerance.py -v
LSD 2>&1 | head -1  # capture new version string
```
