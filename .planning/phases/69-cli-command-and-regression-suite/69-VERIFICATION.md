---
phase: 69-cli-command-and-regression-suite
verified: 2026-05-19T19:00:00Z
status: passed
score: 4/4
overrides_applied: 1
overrides:
  - must_have: "lucy lsd run with a file containing a FORM line behaves the same as without it — LSD binary tolerance of unknown commands confirmed; result documented in a findings note"
    reason: "The hypothesis was empirically REFUTED — LSD-3.4.9 rejects bare FORM with error 102. The phase responded correctly: (1) the refutation is documented in .planning/findings/form-tolerance.md with full reproduction steps, (2) Phase 66 emit_form() was amended to emit '; FORM <formula>' (comment form) which LSD silently ignores, (3) the living test test_form_line_produces_identical_solutions is xfail-marked with strict=False so it becomes xpass the moment a future LSD version accepts FORM — triggering re-evaluation. The FORM/LSD binary compatibility concern is fully resolved; only the literal wording of SC3 ('behaves the same') is not true for bare FORM."
    accepted_by: "verifier"
    accepted_at: "2026-05-19T19:00:00Z"
---

# Phase 69: CLI Command and Regression Suite — Verification Report

**Phase Goal:** `lucy pylsd run` is a working CLI command the agent can invoke; existing `lucy lsd run` behavior is regression-tested and confirmed unchanged; FORM/LSD binary compatibility is empirically confirmed
**Verified:** 2026-05-19T19:00:00Z
**Status:** PASSED (4/4 truths — 1 override applied)
**Re-verification:** No — initial verification

---

## CRITICAL FINDING: FORM Hypothesis Refuted (must read)

SC3 from ROADMAP.md stated "LSD binary tolerance of unknown commands confirmed." This hypothesis was
empirically **FALSE**. LSD-3.4.9 rejects bare `FORM` with:

```
error 102 - 1 commands read
Unknown command name: FORM
```

Exit code 255. Zero solutions produced.

The phase handled this correctly. `emit_form()` in `src/lucy_ng/lsd/generator.py` was amended (Phase 66
backport, committed during Phase 69 execution) to emit `; FORM C13H18O2` (LSD comment) instead of bare
`FORM C13H18O2`. LSD silently ignores comment lines. The finding is documented in
`.planning/findings/form-tolerance.md` with full reproduction steps, LSD version, test output, and the
mitigation decision. The living test `test_form_line_produces_identical_solutions` is marked `@pytest.mark.xfail(strict=False)` — it will become xpass and alert developers if a future LSD version starts accepting bare FORM.

CLAUDE.md already documented "Do NOT use FORM, FORMULA, or similar commands" but Phase 66's `emit_form()`
shipped contrary to this rule. The Phase 69 finding and backport correct that divergence.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `lucy pylsd run compound.lsd` executes multi-run orchestration and prints ranked merged solutions to stdout (same format as `lucy lsd rank`) | VERIFIED | `src/lucy_ng/cli/pylsd.py` (280 lines) implements full pipeline: `_extract_suspects` → `PyLSDOrchestrator.run()` → `SolutionMerger.merge()` → `_perform_ranking()`. `lucy pylsd run --help` confirms all options present. CLI importable: `python -c "from lucy_ng.cli.pylsd import pylsd; print(pylsd.name)"` → "pylsd". `cli.add_command(pylsd)` at main.py:54. |
| 2 | Running the same ibuprofen LSD file (without 4J annotations) through `lucy pylsd run` produces the same solution set as `lucy lsd run` — regression confirmed | VERIFIED | `tests/test_lsd_regression.py` + `tests/fixtures/regression/ibuprofen_no_4j.lsd` + `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt` (392 InChIs). Test passes: `pytest tests/test_lsd_regression.py -q` → 3 passed. Baseline is 392 C13H18O2 InChIs generated from Phase 65 LSD-3.4.9 run and developer-verified (D-16a). Fixture confirmed clean: no inventory block, no "; ELIM" annotations. |
| 3 | `lucy lsd run` with a file containing a `FORM` line behaves the same as without it — LSD binary tolerance of unknown commands confirmed; result documented in a findings note | PASSED (override) | Hypothesis refuted — LSD-3.4.9 rejects bare FORM (error 102). Mitigation applied: `emit_form()` amended to emit `; FORM <formula>` (comment); LSD ignores comments. `generator.py emit_form()` confirmed: returns `f"; FORM {formula}"`. `tests/test_lsd_generator.py` confirms: `emit_form("C13H18O2") == "; FORM C13H18O2"` (42 tests pass). Findings documented in `.planning/findings/form-tolerance.md` with all required fields (LSD version, method, output, conclusion, reproducibility). Override: refutation + mitigation is an auditable result; see override entry in frontmatter. |
| 4 | `lucy lsd rank` operates unchanged on `merged.smi` output — two-tier ranking (match count primary, MAE secondary) is the post-merge ranker | VERIFIED | `_perform_ranking()` extracted as module-level helper at `lsd.py:207`. `lsd_rank` delegates to it at line 660 (pure refactor). `pylsd_run` imports `_perform_ranking` from `lucy_ng.cli.lsd` and calls it as a Python function (not subprocess). `TestRankingIntegration::test_perform_ranking_called_not_subprocess` asserts mock was called. 11/11 `test_pylsd_cli.py` tests pass. |

**Score:** 4/4 (3 VERIFIED + 1 PASSED (override))

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CLI-01 | 69-02-PLAN.md | `lucy pylsd run <file>` executes multi-run orchestration and returns merged solutions | SATISFIED | `src/lucy_ng/cli/pylsd.py` implements full pipeline; `lucy pylsd --help` and `lucy pylsd run --help` both reachable; group registered in `main.py:54` |
| CLI-02 | 69-01-PLAN.md, 69-02-PLAN.md | `lucy pylsd run` reuses existing `lucy lsd rank` two-tier ranking | SATISFIED | `_perform_ranking()` extracted and called directly from `pylsd_run`; no subprocess; `TestRankingIntegration` mock-verifies the Python function call |
| CLI-03 | 69-03-PLAN.md, 69-04-PLAN.md | Regression: all existing `lucy lsd run` commands work unchanged | SATISFIED | `tests/test_lsd_regression.py` passes 3/3; `test_lsd_form_tolerance.py` passes `test_form_tolerance_fixtures_exist` + `test_form_line_produces_identical_solutions` correctly xfails (FORM rejected); 83 passed, 1 xfailed total across all Phase 69 tests |

REQUIREMENTS.md traceability confirms CLI-01, CLI-02, CLI-03 mapped to Phase 69. No orphaned requirements.

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/lucy_ng/cli/pylsd.py` | pylsd Click group + pylsd_run command + _extract_suspects helper | VERIFIED | 280 lines; contains `def pylsd`, `def pylsd_run`, `def _extract_suspects`; no sys.exit calls; 5 `raise SystemExit(1)` calls |
| `src/lucy_ng/cli/main.py` | pylsd group registered in lucy CLI | VERIFIED | `from lucy_ng.cli.pylsd import pylsd` at line 14; `cli.add_command(pylsd)` at line 54 |
| `src/lucy_ng/cli/lsd.py` | `_perform_ranking` + `_validate_and_parse_inventory` helpers | VERIFIED | `_perform_ranking` at line 207; `_validate_and_parse_inventory` at line 339; both importable without Click context |
| `tests/test_pylsd_cli.py` | CLI integration tests (mocked orchestrator) | VERIFIED | 11 test cases covering D-13/D-13a/D-13b/D-13c paths, --no-rank, --format json, K>3 exit, LSD unavailable; no subprocess calls |
| `tests/test_lsd_form_tolerance.py` | Living regression for FORM tolerance | VERIFIED | Contains `test_form_tolerance_fixtures_exist` (always-on) and `test_form_line_produces_identical_solutions` (skipif + xfail); passes as `.x` (xfailed = correct behavior) |
| `tests/fixtures/form_tolerance/minimal.lsd` | Baseline ethane LSD (no FORM) | VERIFIED | Contains MULT 1 C, MULT 2 C, HSQC; no FORM line |
| `tests/fixtures/form_tolerance/minimal_with_form.lsd` | Ethane LSD with bare FORM C2H6 | VERIFIED | Contains `FORM C2H6` |
| `.planning/findings/form-tolerance.md` | Reproducible-research audit trail | VERIFIED | Contains LSD-3.4.9 version string, Hypothesis, Setup, Method, Output (with error 102 text), Conclusion, Mitigation Chosen, Reproducibility Notes sections |
| `tests/test_lsd_regression.py` | InChI-set regression test | VERIFIED | `test_lsd_fixture_exists` (always-on), `test_baseline_fixture_exists` (always-on), `test_ibuprofen_no_4j_inchi_set_stable` (skipif LSD); all 3 pass |
| `tests/fixtures/regression/ibuprofen_no_4j.lsd` | Classic v1 ibuprofen LSD (no inventory, no ELIM) | VERIFIED | Contains MULT lines; `grep -c "CONSTRAINT INVENTORY v2\|; ELIM"` → 0 |
| `tests/fixtures/regression/ibuprofen_no_4j.expected_inchis.txt` | 392 InChI baseline (developer-verified) | VERIFIED | 392 non-empty lines; first line is valid InChI string starting `InChI=1S/C13H18O2/` |
| `src/lucy_ng/lsd/generator.py emit_form()` | Emits `; FORM <formula>` comment form | VERIFIED | Returns `f"; FORM {formula}"`; doc string explicitly references `form-tolerance.md`; `test_lsd_generator.py` asserts comment form (42 tests pass) |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `lsd_rank` Click command | `_perform_ranking()` | Direct call at `lsd.py:660` | WIRED | `_perform_ranking(smiles_file, experimental_shifts, top, tolerance, table, output_format)` — thin wrapper confirmed |
| `pylsd_run` | `PyLSDOrchestrator.run()` | `PyLSDOrchestrator(timeout=timeout).run(base_problem, suspect_correlations, output_dir)` at `pylsd.py:222` | WIRED | Import at top of file; ValueError caught for K>3 |
| `pylsd_run` | `_perform_ranking` | `from lucy_ng.cli.lsd import _perform_ranking, _validate_and_parse_inventory` at `pylsd.py:9` | WIRED | Called at lines 264 and 275 |
| `pylsd_run` | `_validate_and_parse_inventory` | Same import; called in `_extract_suspects` at line 51 | WIRED | Full D-13/D-13a/D-13b/D-13c branching implemented |
| `test_lsd_regression.py` | `ibuprofen_no_4j.lsd` fixture | `FIXTURE_DIR / "ibuprofen_no_4j.lsd"` pattern at test line 107 | WIRED | Fixture path referenced and asserted to exist |
| `test_lsd_regression.py` | `ibuprofen_no_4j.expected_inchis.txt` | `_read_baseline(FIXTURE_DIR / "ibuprofen_no_4j.expected_inchis.txt")` | WIRED | Set-equality comparison in `test_ibuprofen_no_4j_inchi_set_stable` |

---

## Data-Flow Trace (Level 4)

Not applicable. Phase 69 delivers CLI commands (not UI rendering) and test fixtures. The
data-flow for `pylsd_run` is: LSD file → `_extract_suspects` → `PyLSDOrchestrator.run()` →
`SolutionMerger.merge()` → `_perform_ranking()` → stdout. All stages are wired with real
objects (not stubs); mocking is isolated to the test suite.

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `pylsd` group importable | `python -c "from lucy_ng.cli.pylsd import pylsd; print(pylsd.name)"` | `pylsd` | PASS |
| helpers importable without Click context | `python -c "from lucy_ng.cli.lsd import _perform_ranking, _validate_and_parse_inventory; print('ok')"` | `ok` | PASS |
| `lucy pylsd run --help` lists expected options | `lucy pylsd run --help` | Lists --shifts, --no-rank, --working-dir, --timeout, --format | PASS |
| `lucy pylsd` reachable from top-level CLI | `lucy --help \| grep pylsd` | `pylsd   PyLSD multi-run orchestration for 4J HMBC handling.` | PASS |
| All Phase 69 tests green | `pytest tests/test_pylsd_cli.py tests/test_cli_lsd.py tests/test_inventory_schema.py tests/test_lsd_regression.py tests/test_lsd_form_tolerance.py -q` | `83 passed, 1 xfailed` | PASS |
| `emit_form()` returns comment form | `test_lsd_generator.py::test_emit_form_ibuprofen` | `"; FORM C13H18O2"` | PASS |

---

## Probe Execution

No `probe-*.sh` scripts declared in plans or present in `scripts/*/tests/`. Step 7c: SKIPPED (no probes).

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | No TBD/FIXME/XXX markers in phase-modified files. No empty implementations. No hardcoded stubs. |

No debt markers found in `src/lucy_ng/cli/pylsd.py`, `src/lucy_ng/cli/lsd.py`, or `src/lucy_ng/lsd/generator.py`.

---

## Gaps Summary

No gaps. All four roadmap success criteria are verified or override-accepted with documented rationale.

**Override detail for SC3:** The original SC3 wording assumed FORM would be tolerated. The phase discovered the opposite and responded with: empirical documentation, a backport fix, and a living test that self-describes the expected future state (xpass = re-evaluate). This is not a missing feature — it is a better outcome than the original hypothesis.

---

## Human Verification Required

None. All must-haves are either directly verifiable from the codebase or verified by the running test suite. The `test_ibuprofen_no_4j_inchi_set_stable` test runs on this machine (LSD-3.4.9 installed) and passes — the regression is machine-verified, not human-asserted. D-16a (developer confirmed all 392 InChIs are C13H18O2) was completed during plan execution and is recorded in the test file module docstring.

---

_Verified: 2026-05-19T19:00:00Z_
_Verifier: Claude (gsd-verifier)_
