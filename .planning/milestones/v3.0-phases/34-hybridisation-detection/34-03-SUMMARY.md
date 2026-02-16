---
phase: 34-hybridisation-detection
plan: 03
subsystem: detection
tags: [statistical-detection, hybridisation, cli, database-query]

requires:
  - "34-01"  # v4 schema with hybridisation columns and shift-window query

provides:
  - "User-facing detection module (src/lucy_ng/detection/)"
  - "StatisticalDetector.detect_hybridisation() method"
  - "HybridisationResult and HybridisationDistribution Pydantic models"
  - "lucy detect hybridisation CLI command"
  - "Comprehensive test suite (12 tests)"

affects:
  - "34-04"  # Will use detection module patterns
  - "39"     # CASE agent will call 'lucy detect hybridisation'

tech-stack:
  added: []
  patterns:
    - "Statistical detection via database aggregation"
    - "Threshold-based frequency filtering"
    - "Pydantic models with computed properties (dominant, is_definitive)"
    - "CLI with --format json/text for agent and human use"

key-files:
  created:
    - src/lucy_ng/detection/__init__.py
    - src/lucy_ng/detection/models.py
    - src/lucy_ng/detection/detector.py
    - src/lucy_ng/cli/detect.py
    - tests/test_detection_hybridisation.py
  modified:
    - src/lucy_ng/cli/main.py  # Registered detect command group

decisions:
  - id: DETECT-CLI-THRESHOLD
    what: Default 1% frequency threshold for state filtering
    why: Excludes noise while preserving minor but real states
    alternatives: 5% (too aggressive), 0% (includes spurious states)

  - id: DETECT-RESULT-NORMALIZATION
    what: Normalize remaining frequencies after threshold filter
    why: Ensures distribution sums to ~1.0 for cleaner interpretation
    impact: Minor states slightly amplified when dominant excluded (rare)

  - id: DETECT-WARNING-MECHANISM
    what: Return has_data=False with warning when all hybridisation counts are 0
    why: Distinguishes "no matching HOSE codes" from "database needs regeneration"
    context: Old databases have v4 schema but unpopulated columns until Plan 34-02 runs

metrics:
  duration: ~12 minutes
  completed: 2026-02-11
---

# Phase 34 Plan 03: Detection Module and CLI Command Summary

**One-liner:** Detection module with StatisticalDetector class and 'lucy detect hybridisation' CLI command for querying sp3/sp2/sp1 distributions from HOSE database.

## What Was Done

### Task 1: Detection Module with Models and Detector
Created `src/lucy_ng/detection/` module with three files:

1. **models.py**: Pydantic v2 models
   - `HybridisationDistribution`: sp3/sp2/sp1 frequencies (0.0-1.0)
     - Property `dominant`: Returns state with highest frequency or "unknown"
     - Property `is_definitive`: Returns True if one state >95%
   - `HybridisationResult`: Full detection result with metadata
     - Fields: shift_ppm, window_ppm, radius, threshold, distribution, total_observations, unique_hose_codes, has_data, warning
     - Method `summary()`: Human-readable text output
     - Method `model_dump_json()`: JSON output for agent consumption

2. **detector.py**: StatisticalDetector class
   - Constructor takes database path, opens DatabaseManager connection
   - Implements context manager protocol (`__enter__`/`__exit__`)
   - Method `detect_hybridisation(shift_ppm, radius=3, window_ppm=2.0, threshold=0.01)`:
     - Queries `DatabaseManager.get_hose_stats_by_shift_window()`
     - Aggregates sp3_count, sp2_count, sp1_count across all matching HOSE codes
     - Computes frequencies, applies threshold filter, normalizes remaining states
     - Returns HybridisationResult with all fields populated
     - Returns has_data=False with warning if no data or all zeros

3. **__init__.py**: Exports StatisticalDetector and HybridisationResult

**Verification:** Python import test passed, models construct correctly, summary() contains expected content.

### Task 2: CLI Command and Registration
Created `src/lucy_ng/cli/detect.py` following predict.py pattern:

1. **Command group**: `@click.group() detect()`
   - Docstring: "Statistical detection of structural constraints from shifts."

2. **Subcommand**: `@detect.command("hybridisation")`
   - Arguments: `SHIFT_PPM` (float)
   - Options: `--db`, `--radius`, `--window`, `--threshold`, `--format [text|json]`
   - Uses DatabaseFinder.find_hose_database() for auto-detection
   - Instantiates StatisticalDetector, calls detect_hybridisation()
   - Outputs result.summary() for text or result.model_dump_json() for JSON
   - Prints warning to stderr if result.warning is set

**Modified src/lucy_ng/cli/main.py:**
- Imported detect command group
- Registered with `cli.add_command(detect)`
- Updated docstring to list detect command

**Verification:** `lucy detect hybridisation --help` shows all options, `lucy detect --help` shows hybridisation subcommand.

### Task 3: Comprehensive Tests
Created `tests/test_detection_hybridisation.py` with 12 tests:

1. **Fixture `test_db`**: Creates in-memory SQLite with v4 schema and sample data
   - Aromatic region (~130 ppm): sp2=900, sp3=10, sp1=5 (across 3 HOSE codes)
   - Aliphatic region (~25 ppm): sp3=950, sp2=50, sp1=0 (across 2 HOSE codes)
   - Alkyne region (~85 ppm): sp1=800, sp2=10, sp3=5 (across 2 HOSE codes)
   - Zero data region (~50 ppm): All hybridisation counts = 0 (for warning test)

2. **Detection logic tests**:
   - `test_detect_hybridisation_aromatic`: sp2 dominant (>90%)
   - `test_detect_hybridisation_aliphatic`: sp3 dominant (>90%)
   - `test_detect_hybridisation_alkyne`: sp1 dominant (>90%)
   - `test_detect_threshold_filters`: 5% threshold excludes sp2 (3.3% frequency)
   - `test_detect_no_data`: Query at 300 ppm → has_data=False
   - `test_detect_all_zeros_warning`: Warning message for unpopulated columns

3. **Model tests**:
   - `test_hybridisation_distribution_dominant`: sp3/sp2/sp1/unknown cases
   - `test_hybridisation_distribution_is_definitive`: >95%, =95%, <95% cases
   - `test_hybridisation_result_summary_format`: Contains shift, distribution, dominant, observations
   - `test_hybridisation_result_json_format`: Valid JSON with expected keys

4. **CLI tests**:
   - `test_cli_detect_command_exists`: `--help` works
   - `test_cli_detect_group_exists`: detect group shows hybridisation

**Verification:** All 12 tests pass, no regressions in existing tests, ruff clean.

## Files Modified

| File | Lines | Change |
|------|-------|--------|
| src/lucy_ng/detection/__init__.py | 6 | Created |
| src/lucy_ng/detection/models.py | 120 | Created |
| src/lucy_ng/detection/detector.py | 141 | Created |
| src/lucy_ng/cli/detect.py | 97 | Created |
| src/lucy_ng/cli/main.py | 3 | Modified (import + register + docstring) |
| tests/test_detection_hybridisation.py | 264 | Created |

**Total:** 631 lines added across 6 files

## Test Results

```
tests/test_detection_hybridisation.py::test_detect_hybridisation_aromatic PASSED
tests/test_detection_hybridisation.py::test_detect_hybridisation_aliphatic PASSED
tests/test_detection_hybridisation.py::test_detect_hybridisation_alkyne PASSED
tests/test_detection_hybridisation.py::test_detect_threshold_filters PASSED
tests/test_detection_hybridisation.py::test_detect_no_data PASSED
tests/test_detection_hybridisation.py::test_detect_all_zeros_warning PASSED
tests/test_detection_hybridisation.py::test_hybridisation_distribution_dominant PASSED
tests/test_detection_hybridisation.py::test_hybridisation_distribution_is_definitive PASSED
tests/test_detection_hybridisation.py::test_hybridisation_result_summary_format PASSED
tests/test_detection_hybridisation.py::test_hybridisation_result_json_format PASSED
tests/test_detection_hybridisation.py::test_cli_detect_command_exists PASSED
tests/test_detection_hybridisation.py::test_cli_detect_group_exists PASSED

12 passed in 0.32s
```

**Ruff:** All checks passed.

**No regressions:** Existing tests (test_cli_main.py, etc.) still pass.

## Deviations from Plan

None - plan executed exactly as written.

## Known Limitations

1. **Unpopulated hybridisation data**: Old databases (even after v4 migration) will have all hybridisation counts at 0 until database regeneration with Plan 34-02's updated stats_generator. Detection returns has_data=False with warning in this case.

2. **Threshold edge cases**: When threshold filters out all states (rare), normalization produces all zeros. Distribution.dominant returns "unknown" as expected.

3. **Radius independence**: Detection operates at single radius (default 3). No automatic fallback to other radii if data sparse. This is by design - CASE agent should control radius selection.

## Next Phase Readiness

### Unblocks
- **34-04**: Can follow same module structure for signal grouping detection
- **34-05**, **34-06**: Can use detection patterns for remaining constraint types
- **39**: CASE agent can call `lucy detect hybridisation 130.5 --format json` for hybridisation constraints

### Prerequisites for Full Functionality
- **34-02**: stats_generator must populate sp3_count, sp2_count, sp1_count columns
- **Database regeneration**: Run `lucy database generate-stats` (when 34-02 completes) to populate hybridisation data

### Testing with Real Data
Current tests use synthetic data. End-to-end validation with real HOSE database requires:
1. Plan 34-02 completion (stats_generator update)
2. Database regeneration pass (~2-3 hours)
3. Query at known shifts (e.g., 130 ppm → sp2, 25 ppm → sp3, 85 ppm → sp1)

## Lessons for Future Plans

1. **Pydantic computed properties**: Using `@property` for `dominant` and `is_definitive` keeps API clean and prevents stale computed values. Better than storing as fields.

2. **Warning vs. error handling**: Returning has_data=False with warning (instead of raising exception) allows graceful degradation when database unpopulated. CLI prints warning to stderr while returning valid JSON.

3. **Context manager pattern**: StatisticalDetector implements `__enter__`/`__exit__` for clean resource management, consistent with DatabaseManager pattern.

4. **Threshold normalization**: Normalizing after filtering ensures distribution always sums to ~1.0, simplifying downstream logic in CASE agent.

5. **Test fixture design**: In-memory SQLite with known data distributions enables precise assertions without dependency on 2.8GB production database.

## Commit

**Hash:** dabd914
**Message:** feat(34-03): add hybridisation detection module and CLI command

**Summary:**
- Created detection module with StatisticalDetector class
- Added HybridisationDistribution and HybridisationResult Pydantic models
- Implemented detect_hybridisation() method for querying HOSE database
- Added 'lucy detect hybridisation' CLI command with JSON/text output
- Registered detect command group in main CLI
- Comprehensive test suite (12 tests) covering models, detector, CLI
- Detection queries shift window, aggregates sp3/sp2/sp1 counts
- Threshold filtering excludes states below 1% frequency (configurable)
- Warns when database has no hybridisation data (needs regeneration)

All tests pass, ruff clean, no regressions.
