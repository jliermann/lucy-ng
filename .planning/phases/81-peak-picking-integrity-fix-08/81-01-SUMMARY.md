---
phase: 81-peak-picking-integrity-fix-08
plan: "01"
subsystem: peak-picking
tags: [snr-floor, peak-picker, cli, fix-08]
dependency_graph:
  requires: []
  provides: [snr_floor_5_default, snr_floor_cli_option]
  affects: [AdaptivePeakPicker, lucy_pick_1d]
tech_stack:
  added: []
  patterns: [tdd-red-green, click-option]
key_files:
  created: []
  modified:
    - src/lucy_ng/processing/peak_picker.py
    - src/lucy_ng/cli/pick.py
    - tests/test_peak_picker_snr.py
    - tests/test_cli_pick.py
decisions:
  - "snr_floor default raised from 3.0 to 5.0 (IUPAC LoD → signal/noise separation)"
  - "snr_floor_used field added to JSON output (5.0 default, explicit value, or None for -t mode)"
  - "Pre-existing E501 ruff errors in pick_2d/hsqc/hmbc not fixed (out of scope per deviation boundary rule)"
metrics:
  duration: "~20 minutes"
  completed: "2026-06-10"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 4
---

# Phase 81 Plan 01: SNR Floor Default + CLI Option Summary

## One-Liner

Raised `AdaptivePeakPicker` SNR floor default from 3.0 (IUPAC LoD — picks baseline ripple) to 5.0 (signal/noise separation — retains all real carbons, eliminates impossible peaks) and exposed `--snr-floor / -s` in `lucy pick 1d` with `snr_floor_used` in JSON output.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Failing tests for snr_floor=5.0 default | c1372d9 | tests/test_peak_picker_snr.py |
| 1 (GREEN) | Raise snr_floor default 3.0→5.0 | 49eeafa | src/lucy_ng/processing/peak_picker.py |
| 2 (RED) | Failing tests for --snr-floor CLI option | 8d5177f | tests/test_cli_pick.py |
| 2 (GREEN) | Expose --snr-floor in lucy pick 1d | c4ed7a5 | src/lucy_ng/cli/pick.py |

## Pre-Flight Result

Ibuprofen (data/Ibuprofen/2) yields 48 peaks at snr_floor=5.0 — well above the ≥9 floor. Pre-flight PASSED before the default was changed.

## Changes Made

### peak_picker.py

Two method signatures changed:

- `AdaptivePeakPicker.pick_peaks(... snr_floor: float = 5.0 ...)` (was 3.0)
- `AdaptivePeakPicker.pick_peaks_instance(... snr_floor: float = 5.0 ...)` (was 3.0)

Docstrings updated: "IUPAC LoD: k=3" → "k=5 signal/noise separation; use k=3 for exploratory re-pick".

`_compute_snr_threshold` k=3.0 default left unchanged (it is always called with explicit k=snr_floor; its own default is never used).

### cli/pick.py

- Added `--snr-floor / -s` Click option (float, default=None) to `pick_1d()`
- Forward `snr_floor` kwarg to `AdaptivePeakPicker.pick_peaks()` when provided
- Added `snr_floor_used` field to JSON output:
  - `5.0` when no flag (uses new method default)
  - explicit float when `--snr-floor` provided
  - `null` when `-t/--threshold` mode (SNR disabled)
- Only affects the `1d` subcommand; `2d`, `hsqc`, `hmbc` are unchanged

## Test Results

```
tests/test_peak_picker_snr.py: 12/12 passed
tests/test_cli_pick.py: 17/17 passed
Total: 29 passed, 0 failed
```

New tests added:
- `TestSNRFloorDefault::test_pick_peaks_default_snr_floor_is_5`
- `TestSNRFloorDefault::test_pick_peaks_instance_default_snr_floor_is_5`
- `TestSNRFloorDefault::test_explicit_snr_floor_3_still_overrides`
- `TestPick1D::test_pick_1d_snr_floor_flag_routes_to_picker`
- `TestPick1D::test_pick_1d_snr_floor_short_flag`
- `TestPick1D::test_pick_1d_default_snr_floor_used_is_5`
- `TestPick1D::test_pick_1d_threshold_snr_floor_used_is_none`

## Verification

All success criteria from the plan met:

- Pre-flight passed: ibuprofen yields 48 peaks at snr_floor=5.0 (≥9 floor)
- `pick_peaks` and `pick_peaks_instance` both show `snr_floor: float = 5.0` in signatures
- `lucy pick 1d <path> --snr-floor 3` returns `snr_floor_used: 3.0` in JSON
- `lucy pick 1d <path>` (no flags) returns `snr_floor_used: 5.0` in JSON
- `-t/--threshold` still works; JSON output gains `snr_floor_used` field
- 29 tests pass across test_peak_picker_snr.py and test_cli_pick.py
- `ruff check` clean on peak_picker.py (no errors); pick.py has 3 pre-existing E501 (see Deviations)
- mypy errors in peak_picker.py are pre-existing (scipy stubs, ndarray type params)

## Deviations from Plan

### Pre-existing ruff E501 in cli/pick.py

- **Found during:** Task 2 verification
- **Issue:** 3 E501 "line too long" errors in `pick_2d`, `pick_hsqc`, `pick_hmbc` output formatting lines (lines 165, 212, 259 in pick.py after my additions). These existed in the main repo at lines 137, 184, 231 before this plan.
- **Decision:** Not fixed. Per the deviation scope boundary rule, these are pre-existing and not directly caused by my changes. The line numbers shifted because I added ~28 lines to `pick_1d`.
- **Impact:** None on functionality. These affect 2D commands only.

### Worktree Python import path nuance

- **Found during:** Task 1 verification
- **Issue:** `python -c "import lucy_ng ..."` from the worktree loads the main repo's `src/` (editable install via `.pth` file). However, `python -m pytest` from the worktree prepends the worktree's `src/` via `pyproject.toml`'s `pythonpath = ["src"]`, correctly testing the worktree's changes.
- **Impact:** None. All tests correctly verified worktree code. The verify command in the plan (`python -c "..."` without path manipulation) would show the old default; the equivalent test in pytest passes.

## Known Stubs

None.

## Threat Flags

None. This plan makes no network changes, no new attack surface. The `--snr-floor` float option is passed directly as a multiplier; no injection risk.

## Self-Check: PASSED
