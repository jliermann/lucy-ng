# Phase 4: 2D Peak Picking — Summary

## Outcome

Successfully implemented 2D peak picker for HSQC, HMBC, COSY, and NOESY spectra using nmrglue.

## What Was Built

### PeakPicker2D Class
- `pick_peaks()` — Threshold-based 2D peak picking
- `pick_peaks_snr()` — Signal-to-noise ratio based picking
- `estimate_noise()` — Corner-based noise estimation
- `get_peak_info()` — Detailed peak information helper
- Uses nmrglue's `ng.peakpick.pick()` with connected-region algorithm
- Converts array indices to ppm using spectrum scales

### Spectrum2D Helpers
Added ppm↔index conversion methods:
- `f1_ppm_to_index()`, `f2_ppm_to_index()`
- `f1_index_to_ppm()`, `f2_index_to_ppm()`

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 400fe06 | feat | Add PeakPicker2D for 2D NMR spectra |
| 9b7f7b8 | test | Add comprehensive 2D peak picker tests |
| 3b1cd38 | chore | Export PeakPicker2D from modules |

## Test Coverage

17 new tests in `test_peak_picker_2d.py`:
- 10 tests for `PeakPicker2D` (HSQC, HMBC, COSY picking)
- 3 tests for noise estimation
- 4 tests for ppm/index conversion helpers

All 86 tests passing (4 skipped, 26 warnings from nmrglue).

## Key Technical Decisions

| Decision | Rationale |
|----------|-----------|
| Use nmrglue's connected-region algorithm | Handles overlapping peaks well, returns cluster IDs |
| Corner-based noise estimation | Corners of 2D spectra rarely contain real peaks |
| Store ppm scales, not unit converters | Pydantic serializable, simpler implementation |
| SNR threshold option | More robust than fixed percentage threshold |

## Files Changed

- `src/lucy_ng/processing/peak_picker_2d.py` — New file, PeakPicker2D class
- `src/lucy_ng/models/spectrum.py` — Added ppm/index conversion helpers
- `src/lucy_ng/processing/__init__.py` — Export PeakPicker2D
- `src/lucy_ng/__init__.py` — Export PeakPicker2D and AdaptivePeakPicker
- `tests/test_peak_picker_2d.py` — New file, 17 tests

## Usage Example

```python
from lucy_ng import BrukerReader, PeakPicker2D

# Load HSQC spectrum
hsqc = BrukerReader.read_2d("data/Ibuprofen/6")

# Pick peaks
peaks = PeakPicker2D.pick_peaks(hsqc, threshold=0.05)

print(f"Found {len(peaks.peaks)} peaks")
for peak in peaks.peaks[:5]:
    print(f"  13C: {peak.f1_position:.1f} ppm, 1H: {peak.f2_position:.2f} ppm")
```

## Deviations from Plan

- **Task 2 simplified**: Used ppm_scale interpolation instead of storing unit converters (simpler, serializable)
- **Task 3 combined with Task 1**: Noise estimation added to PeakPicker2D file

## Note

1D peak picking was already implemented in Phase 2.1 (`SimplePeakPicker`, `AdaptivePeakPicker`). This phase focused exclusively on 2D peak picking.

---
*Completed: 2026-01-10*
