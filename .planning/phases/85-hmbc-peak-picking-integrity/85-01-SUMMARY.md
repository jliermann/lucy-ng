---
phase: 85-hmbc-peak-picking-integrity
plan: 01
subsystem: processing
tags: [peak-picking, hmbc, snr, fix-12]
requires: []
provides:
  - "PeakPicker2D MAD-based SNR-floor pick mode (snr_floor=5.0, use_snr=True)"
  - "Peak2D.snr per-peak annotation"
  - "lucy pick hmbc --snr-floor/-s option (SNR mode by default)"
  - "guided HMBC raw-pick routed through SNR floor by default"
affects:
  - "lucy pick hmbc default output (now SNR mode)"
  - "HMBCGuidedPicker default raw-pick behaviour"
tech-stack:
  added: []
  patterns:
    - "MAD-based robust 2D noise estimate (sigma = 1.4826 * median(|data - median|))"
    - "explicit-threshold-disables-SNR routing mirroring the 1D FIX-08 CLI pattern"
key-files:
  created: []
  modified:
    - src/lucy_ng/models/peaks.py
    - src/lucy_ng/processing/peak_picker_2d.py
    - src/lucy_ng/processing/hmbc_guided_picker.py
    - src/lucy_ng/cli/pick.py
    - tests/test_hmbc_guided_picker.py
decisions:
  - "snr_floor default k=5.0 (matches 1D FIX-08); empirically retains both CASE1 3J-meta peaks (SNR 22.4 and 9.8) and is well above the floor"
  - "global MAD noise estimate (full plane), NOT per-F1-row normalization — the global floor cleanly separates the diagnostic peaks (FIX-12 (c) evaluated, per-row NOT applied)"
  - "explicit -t / threshold argument disables SNR mode (legacy fraction-of-max preserved for all existing direct-call tests)"
metrics:
  tasks-completed: 2
  files-modified: 5
  completed: 2026-06-16
commits:
  - 08153aa: "feat(85-01): add MAD-based SNR-floor pick mode to PeakPicker2D + Peak2D.snr"
  - 641ebe1: "feat(85-01): route guided HMBC through SNR floor + expose pick hmbc --snr-floor"
---

# Phase 85 Plan 01: HMBC SNR-Floor Peak Picking Summary

Gave the 2D HMBC picker a noise-relative MAD-based SNR floor (the HMBC analog of the
1D FIX-08), exposed `lucy pick hmbc --snr-floor`, and routed the guided-HMBC raw pick
through it by default — recovering the weak-but-real ring-diagnostic 3J-meta aromatic
cross-peaks (~0.6 % of the global max) that the fraction-of-max-only threshold
systematically discarded.

## What Was Built

**Task 1 (08153aa)** — `Peak2D.snr` field + MAD-based SNR-floor mode in `PeakPicker2D`:
- Added `Peak2D.snr: float | None = None` (signal-to-noise vs MAD-based 2D sigma).
- Added module-level `_compute_2d_noise_sigma(data)`: robust `sigma = 1.4826 * median(|data - median(data)|)`
  over the full 2D plane, with a finite/non-zero fallback (5 %-of-max / k) mirroring the
  1D zero/NaN guard so the picker never produces NaN.
- `PeakPicker2D.pick_peaks` gained `snr_floor: float = 5.0` and `use_snr: bool = True`.
  In SNR mode the nmrglue `pthres`/`nthres` is set to `snr_floor * sigma` (absolute) and
  every peak is annotated with `snr = abs(intensity) / sigma`. An **explicit** `threshold`
  argument (changed default to `None`) forces the legacy `threshold * max(|data|)` path with
  `snr = None`, preserving every existing direct-call test in `test_peak_picker_2d.py`.

**Task 2 (641ebe1)** — guided routing + CLI:
- `HMBCGuidedPicker.pick_hmbc_peaks` and `pick_hmbc_peaks_from_spectra` gained
  `hmbc_snr_floor=5.0` and `hmbc_use_snr=True`; the raw `PeakPicker2D.pick_peaks` call now
  routes through the SNR floor by default (`hmbc_threshold` gates the legacy path when
  `hmbc_use_snr=False`). Cross-validation filtering, the result shape, and the 13C/HSQC
  reference picking are unchanged.
- `lucy pick hmbc` now mirrors `lucy pick 1d`: `--threshold/-t` default `None` and
  `--snr-floor/-s` default `None`; `use_snr = (threshold is None)`; JSON emits a top-level
  `snr_floor_used` and per-peak `snr`; text output states the active mode. `pick_2d` and
  `pick_hsqc` were left untouched.

## Empirically Chosen Defaults (CASE1 expno-7)

Raw HMBC plane: global max 7.48e7, global MAD sigma **2.15e4**.

| path | validated peaks | H4->C2 (C~141 x H~7.11) | H6->C3 (C~137 x H~7.23) |
|------|----------------|--------------------------|--------------------------|
| legacy fraction-of-max (default 0.05) | 29 | **0 (dropped)** | **0 (dropped)** |
| SNR floor k=5 (new default) | 122 | 5 | 2 |

The target ring-diagnostic peak C140.76 x H7.11 sits at intensity 4.81e5 = SNR **22.4** over
the global MAD sigma — comfortably above a k=5 floor and even above k=15. The companion
C137.07 x H7.23 is SNR ~9.8. Both are dropped entirely by the fraction-of-max path
(0.64 % of max << 5 % default). **`snr_floor=5.0`** was chosen: it matches the 1D FIX-08
default, retains both diagnostic peaks, and the per-peak `snr` annotation lets the downstream
agent curate the larger candidate set.

## Per-Row Normalization Decision (FIX-12 (c))

**Per-F1(13C)-row / region normalization was evaluated and NOT applied.** The global MAD
floor already separates the diagnostic peaks: the two 3J-meta correlations are SNR 22.4 and
9.8 over the single global sigma, far above the k=5 floor, while the noise floods at SNR ~3-4.
There is no region where the global floor fails to surface a genuine diagnostic peak, so a
per-row noise model would add complexity without recovering anything the global MAD floor
misses. Recorded here per the plan's "evaluate + apply if it helps" requirement — it does not
help on the grounding CASE1 evidence, so it was deliberately skipped (not silently omitted).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test encodes superseded behaviour] Pinned `test_picks_reasonable_number_of_peaks` to the legacy path**
- **Found during:** Task 2.
- **Issue:** The integration test asserted `15 <= validated_count <= 50`, an envelope written
  for the fraction-of-max picker. FIX-12 changed the guided default to SNR mode, which
  intentionally surfaces many more weak long-range cross-peaks (122 validated on the bundled
  Ibuprofen data), breaking the upper bound.
- **Fix:** Added `hmbc_use_snr=False` to that single test so it keeps validating the
  well-understood fraction-of-max envelope it was written for, with a comment pointing to the
  dedicated SNR-mode regression test in plan 85-02. The SNR-mode behaviour is therefore
  deliberately left to be pinned by 85-02, per the plan's task split.
- **Files modified:** tests/test_hmbc_guided_picker.py
- **Commit:** 641ebe1

## Deferred Issues

- **Pre-existing ruff/mypy noise (out of scope).** The repo carries ~280 pre-existing ruff
  violations and ~111 pre-existing mypy errors. Untouched pre-existing items in adjacent code
  were left alone per the scope boundary: `pick.py:165` (`pick_2d`) and `pick.py:212`
  (`pick_hsqc`) long-line E501; `hmbc_guided_picker.py:240` long-line E501; and the
  `peak_picker_2d.py:5` `nmrglue` import-untyped note (the import is unchanged from HEAD).
  All lines I authored are ruff-clean and free of new mypy errors.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes at trust
boundaries. The MAD estimate has a zero/NaN-sigma fallback (T-85-02 mitigated); no new
dependencies (T-85-SC).

## Verification

- `pytest tests/test_peak_picker_2d.py tests/test_hmbc_guided_picker.py` — 32 passed.
- `pytest tests/test_peak_picker_snr.py tests/test_peak_picking_integrity.py` (1D FIX-08
  untouched) — 20 passed.
- Full suite — 1064 passed, 14 skipped, 1 xfailed.
- `lucy pick hmbc --help` shows `--snr-floor`.
- `ruff check` — clean for all authored lines (pre-existing violations documented above).
- `mypy src/lucy_ng` — no new errors in touched files (only the pre-existing unchanged
  `nmrglue` import note).

Note: tests were run with `PYTHONPATH=<worktree>/src` because the editable install resolves
`lucy_ng` to the main-repo `src/`; the worktree changes are otherwise correctly on disk.

## Self-Check: PASSED

- src/lucy_ng/models/peaks.py — FOUND (Peak2D.snr present)
- src/lucy_ng/processing/peak_picker_2d.py — FOUND (_compute_2d_noise_sigma, snr_floor)
- src/lucy_ng/processing/hmbc_guided_picker.py — FOUND (hmbc_snr_floor)
- src/lucy_ng/cli/pick.py — FOUND (--snr-floor in pick_hmbc)
- Commit 08153aa — FOUND
- Commit 641ebe1 — FOUND
