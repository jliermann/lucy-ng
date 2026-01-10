# Phase 3: 2D NMR Reading — Summary

## Outcome

Successfully implemented Bruker 2D file reader supporting HSQC, HMBC, COSY, TOCSY, NOESY, and ROESY experiments.

## What Was Built

### BrukerReader.read_2d() Method
- Reads processed 2D NMR data from Bruker experiment directories
- Extracts F1/F2 nuclei from acqu2s/acqus parameter files
- Generates ppm scales for both dimensions using nmrglue
- Returns populated `Spectrum2D` objects with full metadata

### Experiment Type Detection
- Pattern matching on Bruker pulse program names
- Handles standard pulse programs: hsqc*, hmbc*, cosy*, noesy*, roesy*, tocsy*
- Special handling for `inv4*` programs: distinguishes HSQC from HMBC via long-range indicators (lr, lplr, lrnd)
- Fallback to nucleus-based detection for unknown pulse programs

### Parameter Extraction
- `_get_2d_params()`: Extracts parameters from both acqus (F2) and acqu2s (F1)
- Captures nuclei, frequencies, sweep widths, solvent, pulse program, scans

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 06c0001 | feat | Add read_2d method to BrukerReader |
| 430b42f | test | Add comprehensive 2D reader tests |

## Test Coverage

12 new tests in `TestBrukerReader2D`:
- HSQC: shape, nuclei, experiment type, ppm scales
- HMBC: experiment type, nuclei
- COSY: nuclei, experiment type
- NOESY: detection and nuclei
- Error handling: invalid directory
- Metadata extraction

All 69 tests pass (4 skipped, 26 warnings from nmrglue).

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| Use inv4* long-range detection for HMBC | Bruker uses inv4* prefix for both HSQC and HMBC; "lr/lplr/lrnd" in name indicates long-range (HMBC) |
| F2 frequency as primary | F2 is the direct detection dimension, typically 1H for heteronuclear experiments |
| Store sweep widths in metadata | Useful for future peak picking and ppm range validation |

## Files Changed

- `src/lucy_ng/readers/bruker.py` — Added read_2d(), helper functions
- `tests/test_bruker_reader.py` — Added TestBrukerReader2D class

## Usage Example

```python
from lucy_ng import BrukerReader

# Read HSQC
hsqc = BrukerReader.read_2d("data/Ibuprofen/6")
print(f"Experiment: {hsqc.experiment_type}")  # HSQC
print(f"F1: {hsqc.f1_nucleus}, F2: {hsqc.f2_nucleus}")  # 13C, 1H
print(f"Shape: {hsqc.data.shape}")  # (256, 2048)
```

## Deviations from Plan

- **Added**: Long-range detection for inv4* pulse programs (not in original plan, discovered during testing)
- **Task 5 (Export Spectrum2D)**: Already complete from Phase 1, no changes needed

---
*Completed: 2026-01-10*
