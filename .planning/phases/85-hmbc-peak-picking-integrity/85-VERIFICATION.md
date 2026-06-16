---
phase: 85-hmbc-peak-picking-integrity
verified: 2026-06-16T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
---

# Phase 85: HMBC Peak-Picking Integrity (FIX-12) Verification Report

**Phase Goal:** Give the 2D HMBC picker a noise-relative SNR floor (HMBC analog of the FIX-08 1D fix) so weak-but-real long-range cross-peaks — especially the ring-diagnostic 3J-meta correlations — are retained instead of dropped by the fraction-of-max threshold. Load-bearing proof: on CASE1 (data/Ibuprofen/7) the 3J-meta cross-peaks H4→C2 (C≈141/H≈7.11) and H6→C3 (C≈137/H≈7.23) must be RETAINED at the SNR default but are DROPPED by the legacy fraction-of-max path.

**Verified:** 2026-06-16
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Success Criteria 1–5)

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | PeakPicker2D has noise-relative MAD-based SNR-floor mode; explicit `-t` keeps legacy fraction-of-max; Peak2D carries `snr` | ✓ VERIFIED | `peak_picker_2d.py`: module-level `_compute_2d_noise_sigma` (sigma = 1.4826·MAD over full plane, zero/NaN fallback to 5%·max/k); `pick_peaks(threshold=None, snr_floor=5.0, use_snr=True)`; `snr_mode = use_snr and threshold is None` → explicit `threshold` forces legacy `threshold*max(|data|)` with `snr=None`. `Peak2D.snr: float\|None` present (`peaks.py:37`). Live: legacy peaks carry `snr=None`. |
| 2 | `lucy pick hmbc --snr-floor` exposed, mirroring `pick 1d` (SNR default when no `-t`); HMBCGuidedPicker routes through SNR by default | ✓ VERIFIED | `pick.py` `pick_hmbc`: `--threshold/-t` default None + `--snr-floor/-s` default None; `use_snr = threshold is None`; JSON emits `snr_floor_used` + per-peak `snr`. `--help` confirmed to show `--snr-floor` (live CliRunner). `hmbc_guided_picker.py`: both `pick_hmbc_peaks` and `pick_hmbc_peaks_from_spectra` gained `hmbc_snr_floor=5.0`/`hmbc_use_snr=True`; raw pick at lines 145–151 routes through `PeakPicker2D.pick_peaks(..., use_snr=True)` by default; `_from_spectra` delegates to `pick_hmbc_peaks` (lines 242–253). |
| 3 | CASE1 regression: both 3J-meta retained at SNR default, legacy drops both, bounded count ceiling, plus synthetic SNR-vs-fraction separation test | ✓ VERIFIED | `tests/test_hmbc_peak_picking_integrity.py` `TestFIX12CASE1HMBC` (in-repo data/Ibuprofen/7, ran live) + `TestFIX12SyntheticSeparation` (always runs). Live regression: 8 passed, 0 skipped. Independent check below confirms retention + legacy drop. Ceiling asserted on guided pick (≤250, observed ~122), not raw 913 / 165 flood. |
| 4 | nmr-chemist skill note on weak long-range/3J HMBC clearing SNR floor = real signal, COMPOUND-AGNOSTIC (FIX-09 grep = 0) | ✓ VERIFIED | `lucy-nmr-chemist.md` Pitfall 12 present (lines 90–95: "HMBC SNR floor; weak long-range correlations are real"). FIX-09 grep gate (`ibuprofen\|CASE1\|CASE9\|expno\|C13H18O2\|C12H16O3\|para-benzoate\|166.08\|7.11\|140.\|136.9`) returns **0**. |
| 5 | No regression: 1D FIX-08 path untouched; full suite green | ✓ VERIFIED | `git diff 08153aa~1 HEAD -- peak_picker.py` = **empty** (1D untouched). 1D FIX-08 suite (`test_peak_picker_snr.py` + `test_peak_picking_integrity.py`): 20 passed. Full suite: **1079 passed, 7 skipped, 1 xfailed** (367.8s). |

**Score:** 5/5 truths verified

### Live Regression Result (load-bearing)

`python -m pytest tests/test_hmbc_peak_picking_integrity.py -q` → **8 passed, 0 skipped** (in-repo data/Ibuprofen/7 ran live; not skipped).

Independent behavior confirmation (`PeakPicker2D.pick_peaks` direct call, raw plane):

| Cross-peak | SNR set (snr_floor=5.0) | Legacy (threshold=0.05) |
| ---------- | ----------------------- | ----------------------- |
| H4→C2 (C≈140.76 / H≈7.105) | PRESENT, SNR **22.4** | ABSENT (dropped) |
| H6→C3 (C≈137.07 / H≈7.234) | PRESENT, SNR **9.8** | ABSENT (dropped) |
| raw plane peak count | 913 maxima | 30 |
| legacy `snr` field | — | `None` (backward-compat) |

Both ring-diagnostic 3J-meta correlations are retained in the SNR set at high SNR and absent in the legacy fraction-of-max set — the load-bearing FIX-12 proof holds. (The 913 raw maxima are collapsed by the guided 13C/HSQC cross-validation to ~122; the test's ≤250 ceiling guards the consumed guided set.)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/lucy_ng/processing/peak_picker_2d.py` | MAD noise + SNR-floor mode | ✓ VERIFIED | `_compute_2d_noise_sigma` + `snr_floor`/`use_snr` params; substantive, wired into guided picker + CLI |
| `src/lucy_ng/models/peaks.py` | `Peak2D.snr` | ✓ VERIFIED | `snr: float\|None = None` (FIX-12) |
| `src/lucy_ng/cli/pick.py` | `pick hmbc --snr-floor` | ✓ VERIFIED | `--snr-floor`/`-s` + `use_snr=(threshold is None)`; `pick_2d`/`pick_hsqc` untouched |
| `src/lucy_ng/processing/hmbc_guided_picker.py` | SNR routing by default | ✓ VERIFIED | `hmbc_snr_floor`/`hmbc_use_snr` in both methods; raw pick routed |
| `tests/test_hmbc_peak_picking_integrity.py` | CASE1 + synthetic regression | ✓ VERIFIED | 2 classes, 8 tests pass live |
| `.claude/agents/lucy-nmr-chemist.md` | compound-agnostic SNR note | ✓ VERIFIED | Pitfall 12; FIX-09 grep = 0 |

### Key Link Verification

| From | To | Via | Status |
| ---- | -- | --- | ------ |
| `pick.py` pick_hmbc | PeakPicker2D SNR path | default SNR when no `-t` (`use_snr=threshold is None`) | ✓ WIRED |
| `hmbc_guided_picker.py` | PeakPicker2D SNR path | default raw-pick routing (`hmbc_use_snr=True` → `use_snr=True`) | ✓ WIRED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| `pick hmbc --snr-floor` exposed | CliRunner `pick hmbc --help` | `--snr-floor` present | ✓ PASS |
| 3J-meta retained / legacy-dropped | direct PeakPicker2D call on data/Ibuprofen/7 | SNR 22.4 & 9.8 present; legacy absent | ✓ PASS |
| 1D FIX-08 untouched | `git diff` on peak_picker.py | empty diff | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Status | Evidence |
| ----------- | ----------- | ------ | -------- |
| FIX-12 | 85-01, 85-02 | ✓ SATISFIED | SNR-floor 2D picker (a), `--snr-floor` CLI (b), per-row normalization evaluated & not needed — global MAD separates (c), regression test (e), skill note (d). FIX-09 guard clean. |

### Anti-Patterns Found

None. No TBD/FIXME/XXX/HACK/PLACEHOLDER in any touched source file. No stubs. Repo clean (committed). Pre-existing ruff/mypy noise documented as out-of-scope in both summaries; all authored lines clean.

### Gaps Summary

None. All five success criteria are verified against the actual code and live execution. The load-bearing CASE1 retention proof was independently reproduced.

### Downstream Follow-Up (out of scope here)

Per the scope boundary: FIX-12 only RESTORES the 3J-meta correlations into the picked set. Whether the benzene ring then actually emerges WITHOUT forced ring-BONDs in a live blind CASE run (the D-04 emergent-ring goal) is the **downstream test** and is NOT verified or failed by this phase. Both UAT runs (UAT-03 CASE1, UAT-04 CASE9) currently PASS only with documented ring-BOND escalation; confirming emergent ring with the recovered correlations is the next milestone-gate step.

---

_Verified: 2026-06-16_
_Verifier: Claude (gsd-verifier)_
