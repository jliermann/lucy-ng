---
phase: 35-neighbourhood-detection
verified: 2026-02-11T10:45:00Z
status: passed
score: 20/20 must-haves verified
---

# Phase 35: Neighbourhood Detection Verification Report

**Phase Goal:** Agent can query database for forbidden and mandatory bond partners for any 13C shift
**Verified:** 2026-02-11T10:45:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                      | Status     | Evidence                                                                                                    |
| --- | -------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------- |
| 1   | Database schema version is 5 with 5 new neighbour columns in hose_stats   | ✓ VERIFIED | SCHEMA_VERSION=5 in schema.py, CREATE_HOSE_STATS_TABLE includes 5 neighbour columns                        |
| 2   | Migration from v4 to v5 adds columns without data loss                    | ✓ VERIFIED | migrate_v4_to_v5() exists, test_migrate_v4_to_v5 passes                                                     |
| 3   | HOSEStatsRecord accepts has_carbon_neighbor through has_halogen_neighbor  | ✓ VERIFIED | models.py lines 131-135 define all 5 fields with default 0                                                  |
| 4   | parse_sphere_1() extracts element symbols from HOSE code sphere 1         | ✓ VERIFIED | hose_parser.py implements with regex, 12 tests pass                                                         |
| 5   | Database manager handles both v4 and v5 schemas                           | ✓ VERIFIED | manager.py query methods use try/except for v5/v4/v3 fallback, upsert accepts 5/8/13-element tuples        |
| 6   | WelfordAccumulator tracks 5 neighbour element counts                      | ✓ VERIFIED | stats_generator.py lines 85-89 define 5 fields, update_with_neighbors() method exists                      |
| 7   | update_with_neighbors() increments correct neighbour counters             | ✓ VERIFIED | Lines 120-133 check element presence and increment counters, test_update_with_neighbors_counts passes       |
| 8   | to_tuple() returns 11-element tuple (count, mean, m2, sp3-sp1, C-halogen) | ✓ VERIFIED | Line 155 returns 11-element tuple, test_to_tuple_eleven_elements passes                                     |
| 9   | Both generators parse sphere 1 and track neighbours                       | ✓ VERIFIED | ResumableHOSEStatsGenerator line 684, SDFHOSEStatsGenerator line 1071 call update_with_neighbors()         |
| 10  | Upsert tuples prepend hose_code+radius for 13-element total               | ✓ VERIFIED | manager.py upsert_hose_stats_incremental handles 13-element tuples (len==13 branch), test passes            |
| 11  | detect_neighbours() returns frequency distribution of bond partners       | ✓ VERIFIED | detector.py lines 146-210 aggregate neighbour counts and compute frequencies, NeighbourDistribution created |
| 12  | Elements with frequency < forbidden_threshold are classified as forbidden | ✓ VERIFIED | models.py lines 173-174 classify FORBIDDEN, test_detect_neighbours_carbonyl verifies S and halogen forbidden |
| 13  | Elements with frequency > mandatory_threshold are classified as mandatory | ✓ VERIFIED | models.py lines 175-176 classify MANDATORY, test verifies O mandatory in carbonyl region                    |
| 14  | detect_neighbours() warns if neighbour columns are all zero               | ✓ VERIFIED | detector.py lines 193-198 check all counts == 0 and set warning, test_detect_neighbours_zero_columns_warning passes |
| 15  | NeighbourResult has .summary() and .model_dump_json() methods             | ✓ VERIFIED | models.py lines 238-298 define summary(), Pydantic provides model_dump_json(), tests verify both            |
| 16  | lucy detect neighbours 170.5 returns forbidden and mandatory elements     | ✓ VERIFIED | CLI command exists, test_cli_detect_neighbours_text_output passes, output contains "Forbidden:" and "Mandatory:" |
| 17  | lucy detect neighbours 170.5 --format json returns valid JSON             | ✓ VERIFIED | test_cli_detect_neighbours_json_output parses output as JSON, verifies required keys                        |
| 18  | lucy detect neighbours 170.5 --mode relaxed uses 0.1%/99% thresholds      | ✓ VERIFIED | detect.py line 109 sets thresholds when mode=="relaxed", test_cli_detect_neighbours_mode_relaxed passes     |
| 19  | --min-frequency and --max-frequency override default thresholds           | ✓ VERIFIED | CLI options defined lines 79-85, passed to detect_neighbours() call                                         |
| 20  | lucy detect --help lists both hybridisation and neighbours subcommands    | ✓ VERIFIED | test_cli_detect_group_shows_neighbours verifies "neighbours" in help output                                 |

**Score:** 20/20 truths verified

### Required Artifacts

| Artifact                                      | Expected                                                  | Status     | Details                                                                                       |
| --------------------------------------------- | --------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------- |
| `src/lucy_ng/database/schema.py`             | SCHEMA_VERSION=5, migrate_v4_to_v5 function               | ✓ VERIFIED | Line 6: SCHEMA_VERSION=5, Line 155: migrate_v4_to_v5() exists, 5 columns in CREATE statement |
| `src/lucy_ng/database/models.py`             | HOSEStatsRecord with 5 neighbour count fields             | ✓ VERIFIED | Lines 131-135 define all 5 fields (has_carbon_neighbor through has_halogen_neighbor)         |
| `src/lucy_ng/database/manager.py`            | migrate_to_v5(), updated upsert and query methods         | ✓ VERIFIED | Line 127: migrate_to_v5(), query methods include neighbour columns with v3/v4 fallback       |
| `src/lucy_ng/prediction/hose_parser.py`      | parse_sphere_1() function                                 | ✓ VERIFIED | Lines 7-47 implement with regex [A-Z][a-z]?, returns dict[str, int]                          |
| `tests/test_hose_parser.py`                  | Tests for HOSE sphere 1 parsing                           | ✓ VERIFIED | 12 tests covering edge cases, all pass                                                        |
| `tests/test_schema_migration.py`             | Tests for v4->v5 migration                                | ✓ VERIFIED | test_migrate_v4_to_v5 and test_upsert_with_neighbours exist and pass                          |
| `src/lucy_ng/prediction/stats_generator.py`  | WelfordAccumulator with neighbour tracking                | ✓ VERIFIED | Lines 85-89: 5 neighbour fields, Line 109: update_with_neighbors(), Line 155: 11-element tuple|
| `tests/test_stats_generator_neighbours.py`   | Tests for neighbour tracking in WelfordAccumulator        | ✓ VERIFIED | 8 tests covering all aspects, all pass                                                        |
| `src/lucy_ng/detection/models.py`            | ConstraintType enum, ElementConstraint, NeighbourResult   | ✓ VERIFIED | Lines 119-124: ConstraintType, Lines 127-137: ElementConstraint, Lines 219-298: NeighbourResult |
| `src/lucy_ng/detection/detector.py`          | StatisticalDetector.detect_neighbours() method            | ✓ VERIFIED | Lines 146-210 implement detection with frequency aggregation and classification              |
| `src/lucy_ng/detection/__init__.py`          | Exports NeighbourResult                                   | ✓ VERIFIED | NeighbourResult in __all__ exports                                                            |
| `tests/test_detection_neighbours.py`         | Tests for neighbourhood detection                         | ✓ VERIFIED | 16 tests (11 model + 5 CLI) covering all detection scenarios, all pass                        |
| `src/lucy_ng/cli/detect.py`                  | neighbours CLI subcommand with threshold override flags   | ✓ VERIFIED | Lines 146-220 define neighbours_command with all required options                             |

### Key Link Verification

| From                                         | To                                       | Via                                                 | Status     | Details                                                                                 |
| -------------------------------------------- | ---------------------------------------- | --------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------- |
| `src/lucy_ng/database/manager.py`           | `src/lucy_ng/database/schema.py`         | SCHEMA_VERSION import and migrate_v4_to_v5 call     | ✓ WIRED    | Line 18: imports migrate_v4_to_v5, Line 138: calls migrate_v4_to_v5(self.connection)   |
| `src/lucy_ng/database/models.py`            | `src/lucy_ng/database/manager.py`        | HOSEStatsRecord with neighbour fields in queries    | ✓ WIRED    | manager.py lines 525-529 construct HOSEStatsRecord with all 5 neighbour fields         |
| `src/lucy_ng/prediction/stats_generator.py` | `src/lucy_ng/prediction/hose_parser.py`  | parse_sphere_1 import for neighbour extraction      | ✓ WIRED    | Line 11: imports parse_sphere_1, Line 683: calls parse_sphere_1(hose_code)             |
| `src/lucy_ng/prediction/stats_generator.py` | `src/lucy_ng/database/manager.py`        | upsert_hose_stats_incremental with 13-element tuples| ✓ WIRED    | Line 718: calls upsert with (hose_code, radius, *acc.to_tuple()) producing 13 elements |
| `src/lucy_ng/detection/detector.py`         | `src/lucy_ng/database/manager.py`        | get_hose_stats_by_shift_window query                | ✓ WIRED    | Line 174: calls self._db.get_hose_stats_by_shift_window()                              |
| `src/lucy_ng/detection/detector.py`         | `src/lucy_ng/detection/models.py`        | NeighbourDistribution and NeighbourResult construction| ✓ WIRED  | Lines 203-210: constructs both models with aggregated frequencies                      |
| `src/lucy_ng/cli/detect.py`                 | `src/lucy_ng/detection/detector.py`      | StatisticalDetector.detect_neighbours() call        | ✓ WIRED    | Line 114: creates detector, Line 115: calls detect_neighbours()                        |
| `src/lucy_ng/cli/detect.py`                 | `src/lucy_ng/database/DatabaseFinder`    | find_hose_database() for auto-detection             | ✓ WIRED    | Line 112: calls DatabaseFinder.find_hose_database() when --db not provided             |

### Requirements Coverage

Phase 35 maps to requirements DETECT-02, DETECT-03, DETECT-06, DETECT-07 from v3.0 milestone:

| Requirement | Description                                              | Status      | Evidence                                                                   |
| ----------- | -------------------------------------------------------- | ----------- | -------------------------------------------------------------------------- |
| DETECT-02   | Neighbourhood detection from shift queries               | ✓ SATISFIED | detect_neighbours() returns forbidden/mandatory elements, all tests pass   |
| DETECT-03   | Override flags for rare cases                            | ✓ SATISFIED | --min-frequency, --max-frequency, --mode relaxed flags implemented         |
| DETECT-06   | Database-backed statistical detection                    | ✓ SATISFIED | Queries hose_stats neighbour columns, aggregates frequencies               |
| DETECT-07   | CLI exposure for agent integration                       | ✓ SATISFIED | lucy detect neighbours command with text and JSON output                   |

### Anti-Patterns Found

None — all code follows established patterns from Phase 34 (hybridisation detection).

### Human Verification Required

None — all functionality is deterministic and programmatically testable.

---

## Verification Details

### Level 1: Existence (All artifacts)

All 13 required artifacts exist:
- Schema, models, manager, hose_parser, stats_generator, detection (models + detector), cli, tests (6 files)

### Level 2: Substantive (Sample checks)

**hose_parser.py**: 47 lines, substantive implementation with regex extraction
**stats_generator.py**: update_with_neighbors() is 24 lines with proper element checking logic
**detect.py**: neighbours_command is 74 lines with all options, threshold logic, output formatting
**models.py**: NeighbourResult.summary() is 60 lines with comprehensive formatting

All exceed minimum line thresholds. No stub patterns (TODO, placeholder, empty returns) found.

### Level 3: Wired (All key links verified)

All 8 key links are WIRED:
- Database manager imports and calls migration function ✓
- Query methods construct models with neighbour fields ✓
- Stats generator imports and calls HOSE parser ✓
- Stats generator upsert creates 13-element tuples ✓
- Detector queries database for neighbour data ✓
- Detector constructs result models ✓
- CLI calls detector method ✓
- CLI uses database finder for auto-detection ✓

### Test Coverage

**All tests pass:**
- test_hose_parser.py: 12/12 ✓
- test_stats_generator_neighbours.py: 8/8 ✓
- test_detection_neighbours.py: 16/16 ✓
- test_schema_migration.py: includes v4→v5 migration tests ✓

**No regressions:** Existing hybridisation detection tests still pass.

---

_Verified: 2026-02-11T10:45:00Z_
_Verifier: Claude (gsd-verifier)_
