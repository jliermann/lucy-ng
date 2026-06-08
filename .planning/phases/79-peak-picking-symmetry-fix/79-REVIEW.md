---
phase: 79-peak-picking-symmetry-fix
reviewed: 2026-06-08T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - src/lucy_ng/cli/pick.py
  - src/lucy_ng/models/peaks.py
  - src/lucy_ng/processing/dept_guided_picker.py
  - src/lucy_ng/processing/peak_picker.py
  - tests/test_dereplication.py
  - tests/test_intensity_symmetry.py
  - tests/test_peak_picker_snr.py
findings:
  critical: 2
  warning: 4
  info: 2
  total: 8
status: resolved
---

# Phase 79: Code Review Report

**Reviewed:** 2026-06-08
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Phase 79 adds an MAD/SNR-based absolute threshold (FIX-04) for `lucy pick 1d`, per-peak SNR
annotation in the JSON contract, CDCl3 solvent-region exclusion, and a
`detect_intensity_symmetry` function for 13C 2C-equivalence detection (FIX-05).

The MAD scaling constant (1.4826) and the k=3 IUPAC floor are numerically correct. The
solvent-exclusion mask direction is correct regardless of ppm scale orientation. The
backwards-compatibility gate (`use_snr` flag) is correctly wired through the CLI and all
internal callers.

Two blockers are found: (1) `_compute_snr_threshold` produces `NaN` when the solvent-exclusion
window covers the entire ppm range of the spectrum — an edge case that exists in pathological
spectra and in unit-test synthetic data constructed purely inside the exclusion window; `NaN`
propagates silently to `find_peaks` (returns empty) and to the JSON output (emits non-RFC-8259
`NaN` literal). (2) `PeakList1D.to_dict()` omits `noise_sigma` and `from_dict()` does not
restore it, breaking any caller that round-trips through the serialisation interface.

Four warnings are present, the most important being a pre-existing off-by-one in
`DEPTGuidedPicker.pick_hsqc_peaks` that causes `threshold_used` to report the
threshold *before* the successful one on early-break (success path). Two existing tests in
`test_dereplication.py` are also fragile under the new SNR default.

---

## Critical Issues

### CR-01: NaN threshold when solvent exclusion empties clean_data

**File:** `src/lucy_ng/processing/peak_picker.py:40-50`

**Issue:** `_compute_snr_threshold` computes MAD over `data[~mask]`. If the solvent exclusion
window covers the entire ppm range of the input spectrum (e.g. a very short synthetic spectrum
or, more practically, a 1D slice spanning only the excluded region), `clean_data` is an empty
array. `np.median([])` returns `nan` rather than raising, so `mad = nan`, `sigma_mad = nan`,
`threshold = nan`. Downstream effects:

- `find_peaks(height=nan)` returns an empty list — all real peaks are silently discarded.
- `peaks.noise_sigma = nan` is emitted in the JSON output as the literal string `NaN`, which
  is not valid JSON (RFC 8259 §6). Consumers that call `json.loads()` on the output will
  receive a float `nan` without warning in CPython but will raise in strict parsers.
- The returned `PeakList1D` carries `noise_sigma=nan` with no indication that the computation
  failed.

The same silent-zero MAD issue arises with nearly-constant data (e.g. a perfectly zero-
baseline synthetic spectrum): `MAD = 0`, `threshold = 0`, `find_peaks(height=0)` returns
every local maximum — potentially flooding the result. This is less likely in production
but *does* affect the synthetic spectra in `test_dereplication.py` (see WR-03).

**Fix:**
```python
def _compute_snr_threshold(
    data: np.ndarray,
    ppm_scale: np.ndarray,
    solvent: str | None = None,
    k: float = 3.0,
) -> tuple[float, float]:
    exclusion = _SOLVENT_EXCLUSION_13C.get(solvent or "", None)
    if exclusion is not None:
        lo, hi = exclusion
        mask = (ppm_scale >= lo) & (ppm_scale <= hi)
        clean_data = data[~mask]
        # Fall back to full spectrum if exclusion removed all points
        if len(clean_data) == 0:
            clean_data = data
    else:
        clean_data = data

    mad = float(np.median(np.abs(clean_data - np.median(clean_data))))
    sigma_mad = 1.4826 * mad

    # Guard against zero/NaN sigma (constant or empty baseline).
    # Fall back to 5 % of max so the function always returns a usable threshold.
    if not np.isfinite(sigma_mad) or sigma_mad == 0.0:
        fallback = 0.05 * float(np.max(np.abs(data))) if data.size > 0 else 1.0
        return fallback, fallback / k

    return k * sigma_mad, sigma_mad
```

---

### CR-02: `PeakList1D.to_dict()` silently drops `noise_sigma`; `from_dict()` cannot restore it

**File:** `src/lucy_ng/models/peaks.py:61-76`

**Issue:** The new `noise_sigma` field is added to `PeakList1D` at line 50, but `to_dict()`
(lines 61-68) does not include it:

```python
def to_dict(self) -> dict[str, Any]:
    return {
        "peaks": [p.model_dump() for p in self.peaks],
        "nucleus": self.nucleus,
        "spectrum_id": self.spectrum_id,
        # noise_sigma is missing
    }
```

`from_dict()` (lines 70-76) also does not accept or restore `noise_sigma`. Any caller that
serialises a `PeakList1D` via `to_dict()` and later reconstructs it via `from_dict()` loses
the noise floor silently. The dereplicate CLI, the CASE agent, and any future consumer that
caches peak lists to disk are all affected.

Note: the CLI's own JSON output path at `pick.py:70-84` bypasses `to_dict()` and correctly
emits `noise_sigma`, so the immediate CLI contract is correct. But the model-level contract is
broken for downstream library use.

**Fix:**
```python
def to_dict(self) -> dict[str, Any]:
    return {
        "peaks": [p.model_dump() for p in self.peaks],
        "nucleus": self.nucleus,
        "spectrum_id": self.spectrum_id,
        "noise_sigma": self.noise_sigma,   # add this line
    }

@classmethod
def from_dict(cls, d: dict[str, Any]) -> "PeakList1D":
    return cls(
        peaks=[Peak1D(**p) for p in d["peaks"]],
        nucleus=d["nucleus"],
        spectrum_id=d.get("spectrum_id"),
        noise_sigma=d.get("noise_sigma"),   # add this line
    )
```

---

## Warnings

### WR-01: `DEPTGuidedPicker` reports `threshold_used` one step too high on success path

**File:** `src/lucy_ng/processing/dept_guided_picker.py:175`

**Issue:** The loop reduces `threshold` *after* each unsuccessful attempt:
```python
while threshold >= min_hsqc_threshold:
    iterations += 1
    hsqc_peaks = PeakPicker2D.pick_peaks(hsqc, threshold=threshold)
    ...
    if len(unmatched_positions) == 0:
        break          # success: threshold holds the WORKING value
    threshold *= threshold_step  # reduction only on failure
```
After `break`, `threshold` is the value that succeeded. But the return statement is:
```python
threshold_used=threshold / threshold_step if iterations > 0 else initial_hsqc_threshold,
```
`threshold / threshold_step` recovers the value from the iteration *before* the successful
one — one step too high. Example: success on iteration 3 at `threshold = 0.025`;
`threshold_used` reports `0.025 / 0.5 = 0.05` (wrong).

This is a pre-existing bug not introduced by Phase 79, but it is in a file modified this
phase and should be fixed here.

On the loop-exhaustion path the formula happens to give the correct answer (last tried
threshold), so only the success path is wrong.

**Fix:**
```python
threshold_used=threshold if iterations > 0 else initial_hsqc_threshold,
```

---

### WR-02: `detect_intensity_symmetry` not exported from `processing/__init__.py`

**File:** `src/lucy_ng/processing/__init__.py` (not in reviewed set but directly affected)

**Issue:** `detect_intensity_symmetry` is a module-level function in `peak_picker.py` but is
not listed in `processing/__init__.py`'s `__all__` or imported there. The test imports it
directly from `lucy_ng.processing.peak_picker`, and any agent or CLI code must do likewise.
This is inconsistent with `AdaptivePeakPicker` which IS exported. If the skill or agent
calls `from lucy_ng.processing import detect_intensity_symmetry` it will get an
`ImportError`.

**Fix:** Add to `src/lucy_ng/processing/__init__.py`:
```python
from lucy_ng.processing.peak_picker import AdaptivePeakPicker, detect_intensity_symmetry

__all__ = [
    "AdaptivePeakPicker",
    "detect_intensity_symmetry",
    ...
]
```

---

### WR-03: Two existing tests in `test_dereplication.py` silently rely on `threshold` being honoured but it is ignored by the new SNR default

**File:** `tests/test_dereplication.py:146, 162-165`

**Issue:** `test_pick_peaks_basic` (line 146) calls:
```python
peaks = AdaptivePeakPicker.pick_peaks(spectrum, threshold=0.1)
```
and `test_pick_peaks_threshold` (lines 162-165) calls both:
```python
peaks_low  = AdaptivePeakPicker.pick_peaks(spectrum, threshold=0.05)
peaks_high = AdaptivePeakPicker.pick_peaks(spectrum, threshold=0.5)
```
Both call sites omit `use_snr=False`. With `use_snr=True` (new default), the `threshold`
parameter is silently ignored and MAD-based threshold is used instead.

For these synthetic zero-background spectra MAD = 0, so `abs_threshold = 0`, and
`find_peaks(height=0)` returns only the actual isolated signal maxima — the tests still pass.
But the tests no longer validate what their names claim:

- `test_pick_peaks_basic` checks count==4 but would pass with any threshold (threshold is
  not the enforcing mechanism).
- `test_pick_peaks_threshold` asserts `len(low) >= len(high)`, which is vacuously true
  because both calls produce identical results (same MAD-derived threshold).

Any future change that adds noise to the synthetic spectra, or uses a spectrum with a
non-zero baseline, would cause surprising failures in the wrong direction.

**Fix:** Add `use_snr=False` to preserve the original intent of both tests:
```python
peaks = AdaptivePeakPicker.pick_peaks(spectrum, threshold=0.1, use_snr=False)

peaks_low  = AdaptivePeakPicker.pick_peaks(spectrum, threshold=0.05, use_snr=False)
peaks_high = AdaptivePeakPicker.pick_peaks(spectrum, threshold=0.5,  use_snr=False)
```

---

### WR-04: `CD3CN` solvent exclusion table omits the 117 ppm nitrile signal

**File:** `src/lucy_ng/processing/peak_picker.py:16`

**Issue:** The `_SOLVENT_EXCLUSION_13C` table entry for `CD3CN` is:
```python
"CD3CN": (1.0, 5.0),    # 1.32 ppm septet
```
Acetonitrile-d3 has two 13C solvent signals: ~1.32 ppm (CD3) and ~117.1 ppm (CN). The
117.1 ppm nitrile carbon is a moderate-intensity singlet that falls in the aromatic region.
If it is not excluded, it inflates the MAD estimate and raises the threshold, which could
cause weak compound peaks near 117 ppm to be missed.

Similarly, the `acetone` / `acetone-d6` entry covers only the ~30 ppm septet but not the
solvent C=O at ~206 ppm. However, the 206 ppm signal is far from most compound carbons and
above the typical 13C window, so its practical impact is limited.

The CD3CN case is more likely to cause missed peaks because 117 ppm overlaps the aromatic
compound region.

**Fix:**
```python
"CD3CN":    (1.0,   5.0),    # 1.32 ppm CD3 septet
"CD3CN-CN": (114.0, 120.0),  # 117.1 ppm CN singlet
```
Or, if keys must be unique (matching Bruker SOLVENT parameter), use a list of exclusion
windows per solvent:
```python
_SOLVENT_EXCLUSION_13C: dict[str, list[tuple[float, float]]] = {
    "CD3CN": [(1.0, 5.0), (114.0, 120.0)],
    ...
}
```
and update `_compute_snr_threshold` to iterate over the list.

---

## Info

### IN-01: `detect_intensity_symmetry` not exported from public API

**File:** `src/lucy_ng/processing/__init__.py`

**Issue:** See WR-02 for the actionable concern. As an additional note: the function is also
absent from `src/lucy_ng/__init__.py` (the package-level public API). Whether that matters
depends on whether external callers (e.g. agent code) are expected to use the top-level
`lucy_ng` namespace. Low severity since the agent imports are via `lucy detect` CLI, but worth
tracking for consistency.

---

### IN-02: `PeakList1D.to_dict()` uses `model_dump()` for peaks but a manual dict for the container

**File:** `src/lucy_ng/models/peaks.py:61-68`

**Issue:** `Peak1D.model_dump()` correctly includes `snr` (new Phase 79 field). The parent
`PeakList1D.to_dict()` is a hand-rolled dict that must be kept in sync manually whenever new
fields are added to `PeakList1D`. `PeakList2D.to_dict()` has the same pattern. Using
`self.model_dump()` at the container level would make both serialisation and round-trip
restoration automatic and would have prevented the CR-02 omission of `noise_sigma`.

**Fix:** (Non-urgent, consider for a separate refactor)
```python
def to_dict(self) -> dict[str, Any]:
    return self.model_dump()
```
Note: `model_dump()` on a Pydantic model with numpy-array fields requires `mode="json"` or
a custom serialiser, so evaluate impact before switching.

---

_Reviewed: 2026-06-08_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
