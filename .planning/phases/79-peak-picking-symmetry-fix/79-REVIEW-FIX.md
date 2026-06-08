---
phase: 79-peak-picking-symmetry-fix
fixed_at: 2026-06-08T00:00:00Z
review_path: .planning/phases/79-peak-picking-symmetry-fix/79-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 79: Code Review Fix Report

**Fixed at:** 2026-06-08
**Source review:** .planning/phases/79-peak-picking-symmetry-fix/79-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (CR-01, CR-02, WR-01, WR-02, WR-03, WR-04)
- Fixed: 6
- Skipped: 0

## Fixed Issues

### CR-01: NaN threshold when solvent exclusion empties clean_data

**Files modified:** `src/lucy_ng/processing/peak_picker.py`, `tests/test_peak_picker_snr.py`
**Commit:** 12aa6ca
**Applied fix:**
- Changed `_SOLVENT_EXCLUSION_13C` from `dict[str, tuple[float, float]]` to
  `dict[str, list[tuple[float, float]]]` to support multiple exclusion windows per
  solvent (also required for WR-04).
- `_compute_snr_threshold` now builds a combined boolean mask over all windows for the
  solvent. After masking, if `clean_data` is empty (exclusion covered entire spectrum),
  fall back to the full `data` array before computing MAD.
- After MAD computation, guard `sigma_mad == 0.0` or non-finite with a 5%-of-max
  fallback so the function always returns a finite, usable `(threshold, sigma_mad)` pair.
- Added three regression tests to `TestSNRThreshold`:
  `test_empty_clean_data_fallback_is_finite`, `test_zero_mad_fallback_is_finite`,
  and `test_empty_clean_data_fallback_picks_real_peak`.

Note: WR-04 (CD3CN nitrile window) was implemented in this same commit because it
required the same data-structure change.

---

### CR-02: `PeakList1D.to_dict()` silently drops `noise_sigma`

**Files modified:** `src/lucy_ng/models/peaks.py`
**Commit:** 36b6a95
**Applied fix:**
- Added `"noise_sigma": self.noise_sigma` to `PeakList1D.to_dict()`.
- Added `noise_sigma=d.get("noise_sigma")` to `PeakList1D.from_dict()`.
- Round-trip smoke test confirmed: `to_dict()` → `from_dict()` preserves the value.

---

### WR-01: `DEPTGuidedPicker` reports `threshold_used` one step too high on success path

**Files modified:** `src/lucy_ng/processing/dept_guided_picker.py`
**Commit:** 3501fc1
**Applied fix:**
- Changed `threshold_used=threshold / threshold_step if iterations > 0 else initial_hsqc_threshold`
  to `threshold_used=threshold if iterations > 0 else initial_hsqc_threshold`.
- On the success path, `threshold` already holds the working value at `break`; the
  division by `threshold_step` was recovering the value from the previous (failed)
  iteration.

---

### WR-02: `detect_intensity_symmetry` not exported from `processing/__init__.py`

**Files modified:** `src/lucy_ng/processing/__init__.py`
**Commit:** 5ba93ff
**Applied fix:**
- Added `detect_intensity_symmetry` to the import line:
  `from lucy_ng.processing.peak_picker import AdaptivePeakPicker, detect_intensity_symmetry`
- Added `"detect_intensity_symmetry"` to `__all__`.
- Import smoke test confirmed: `from lucy_ng.processing import detect_intensity_symmetry` works.

---

### WR-03: Two fragile threshold tests in `test_dereplication.py`

**Files modified:** `tests/test_dereplication.py`
**Commit:** ba1d044
**Applied fix:**
- Added `use_snr=False` to the `pick_peaks(threshold=0.1)` call in `test_pick_peaks_basic`.
- Added `use_snr=False` to both `pick_peaks(threshold=0.05)` and `pick_peaks(threshold=0.5)`
  calls in `test_pick_peaks_threshold`.
- Both tests now exercise the explicit-threshold path as their names imply, not the MAD/SNR
  path where the `threshold` parameter is ignored.

---

### WR-04: CD3CN solvent exclusion table omits 117.1 ppm nitrile signal

**Files modified:** `src/lucy_ng/processing/peak_picker.py`
**Commit:** 12aa6ca (same commit as CR-01)
**Applied fix:**
- The `_SOLVENT_EXCLUSION_13C` table was restructured to use lists of tuples, enabling
  multiple windows per solvent.
- CD3CN entry changed from `(1.0, 5.0)` to `[(1.0, 5.0), (114.0, 120.0)]`, adding
  a 114–120 ppm window that covers the 117.1 ppm CN nitrile singlet.
- Both windows are now applied together during the combined exclusion mask build.

---

## Skipped Issues

None.

---

**Full pytest result after all fixes:**
`1037 passed, 7 skipped, 1 xfailed, 31 warnings in 388.11s`

_Fixed: 2026-06-08_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
