---
phase: 61-detection-engine
plan: "02"
subsystem: detection
tags: [4j-coupling, cli, batch-detection, hose-codes, click]

# Dependency graph
requires:
  - phase: 61-detection-engine/61-01
    provides: "StatisticalDetector.detect_4j_coupling, CouplingPathResult, RiskLevel models, coupling_path_stats DB queries"
provides:
  - "detect_4j_batch method with HOSE pre-loading optimization"
  - "_classify_from_hose_sets private method shared by single and batch"
  - "lucy detect 4j CLI command (single correlation)"
  - "lucy detect 4j-batch CLI command (multiple correlations with summary)"
affects: [62-agent-skill-updates]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Batch pre-load: collect unique shifts first, then cache HOSE codes, then classify"
    - "Private _classify_from_hose_sets factored out of detect_4j_coupling for reuse"
    - "mix_stderr=False in CliRunner for tests that verify JSON output with warnings"

key-files:
  created:
    - tests/test_cli_detect_4j.py
  modified:
    - src/lucy_ng/detection/detector.py
    - src/lucy_ng/cli/detect.py
    - tests/test_detection_4j.py

key-decisions:
  - "HOSE pre-loading: collect unique shifts from all correlations, pre-query DB once per unique shift, reuse cached results per correlation"
  - "Private _classify_from_hose_sets factored from detect_4j_coupling to share logic with batch — no duplication"
  - "mix_stderr=False in CliRunner for JSON tests where warning on stderr would corrupt output"

patterns-established:
  - "Batch CLI commands follow 4j-batch pattern: correlations as c:h,c:h string, parse then query, summary in both JSON and text"

requirements-completed: [DET-02, CLI-01, CLI-02, CLI-03]

# Metrics
duration: 23min
completed: 2026-03-11
---

# Phase 61 Plan 02: Detection Engine CLI Wiring Summary

**`detect_4j_batch` with HOSE pre-loading and `lucy detect 4j` / `lucy detect 4j-batch` CLI commands completing the 4J detection engine public interface**

## Performance

- **Duration:** 23 min
- **Started:** 2026-03-11T08:46:04Z
- **Completed:** 2026-03-11T09:09:31Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- `detect_4j_batch` scores multiple HMBC correlations, pre-loading HOSE codes for unique shifts to eliminate duplicate DB queries
- `_classify_from_hose_sets` private method extracted so single and batch detection share identical classification logic
- `lucy detect 4j <c_shift> <h_shift>` outputs risk tier and recommendation in JSON or text
- `lucy detect 4j-batch --correlations "c1:h1,c2:h2"` returns per-correlation results plus risk-level summary counts
- 22 new tests (8 batch unit + 14 CLI integration), 0 regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: detect_4j_batch with HOSE code pre-loading** - `52d9eca` (feat)
2. **Task 2: Wire CLI commands 4j and 4j-batch** - `740bd1d` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `src/lucy_ng/detection/detector.py` - Added detect_4j_batch + _classify_from_hose_sets private method; refactored detect_4j_coupling to delegate to _classify_from_hose_sets
- `src/lucy_ng/cli/detect.py` - Added fourj_command (detect 4j) and fourj_batch_command (detect 4j-batch) subcommands
- `tests/test_detection_4j.py` - 8 new batch unit tests appended
- `tests/test_cli_detect_4j.py` - Created: 14 CLI integration tests

## Decisions Made
- HOSE pre-loading collects all unique shifts first, queries DB once per unique shift into a dict, then reuses per correlation — avoids O(N) DB queries when correlations share shifts
- `_classify_from_hose_sets` factors out the exact-pair lookup, fallback, aggregation, and risk classification shared by both the single and batch methods
- `mix_stderr=False` on CliRunner used for tests that parse JSON output — otherwise the warning ("Only 30 observations...") appended to stdout corrupts JSON

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CliRunner default mixes stderr into stdout, breaking JSON parse**
- **Found during:** Task 2 (CLI integration tests)
- **Issue:** `CliRunner()` by default sets `mix_stderr=True`, so the warning output from `click.echo(f"\nWarning: ...", err=True)` was appended to JSON stdout, causing JSONDecodeError
- **Fix:** Changed `runner = CliRunner()` to `runner = CliRunner(mix_stderr=False)` in the test that verifies JSON output for the insufficient_data case
- **Files modified:** tests/test_cli_detect_4j.py
- **Verification:** Test passes after fix, 14/14 tests pass
- **Committed in:** 740bd1d (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in test setup)
**Impact on plan:** Minimal — one-line fix in test infrastructure. CLI code unchanged.

## Issues Encountered
None beyond the CliRunner stderr mixing issue documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Detection engine complete: hybridisation, neighbours, HHB, 4J single and batch all wired to CLI
- Phase 62 (Agent Skill Updates) can now reference `lucy detect 4j` and `lucy detect 4j-batch` commands
- Both JSON and text output formats verified

## Self-Check: PASSED

All files and commits verified:
- FOUND: .planning/phases/61-detection-engine/61-02-SUMMARY.md
- FOUND: src/lucy_ng/detection/detector.py
- FOUND: src/lucy_ng/cli/detect.py
- FOUND: tests/test_cli_detect_4j.py
- FOUND: commit 52d9eca (Task 1)
- FOUND: commit 740bd1d (Task 2)

---
*Phase: 61-detection-engine*
*Completed: 2026-03-11*
