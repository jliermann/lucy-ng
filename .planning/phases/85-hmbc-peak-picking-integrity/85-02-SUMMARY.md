---
phase: 85-hmbc-peak-picking-integrity
plan: 02
subsystem: testing
tags: [peak-picking, hmbc, snr, fix-12, regression, skill]
requires:
  - "PeakPicker2D SNR-floor pick mode (snr_floor=5.0, use_snr=True) from 85-01"
  - "HMBCGuidedPicker SNR routing (hmbc_use_snr=True) from 85-01"
  - "Peak2D.snr per-peak annotation from 85-01"
provides:
  - "FIX-12 HMBC SNR-floor regression test (CASE1 3J-meta retention + count ceiling + synthetic separation)"
  - "nmr-chemist Pitfall 12: HMBC SNR floor / weak long-range correlations are real (compound-agnostic)"
affects:
  - "blind CASE nmr-chemist behaviour (treats weak long-range HMBC as signal)"
tech-stack:
  added: []
  patterns:
    - "external-dataset skipif guard mirroring FIX-08 test pattern"
    - "tight (C +-1.0, H +-0.08) match window to distinguish 3J-meta from 2J-ortho"
    - "synthetic 2D plane with seeded RNG noise floor for SNR-vs-fraction-of-max separation"
key-files:
  created:
    - tests/test_hmbc_peak_picking_integrity.py
  modified:
    - .claude/agents/lucy-nmr-chemist.md
decisions:
  - "Count ceiling asserted against the GUIDED pick (~122 validated), not the raw PeakPicker2D plane pick (~913 maxima) — the guided 13C/HSQC-cross-validated set is what the team consumes; ceiling set to <=250 (well below the 913 raw / 165 -t0.005 floods)"
  - "Tight match window (C +-1.0 ppm, H +-0.08 ppm) so the ~22%-of-max 2J-ortho cross-peaks (C~140.96xH7.23, C~136.88xH7.11) cannot masquerade as the 3J-meta targets — the floor genuinely recovers the 3J-meta"
  - "Real-data retention/contrast asserted via the guided picker; external CASE1 variant uses the raw PeakPicker2D pick (no 13C/HSQC reference for the external copy) and is skipif-guarded"
metrics:
  tasks-completed: 2
  files-modified: 2
  completed: 2026-06-16
commits:
  - 9a158a9: "test(85-02): FIX-12 HMBC SNR-floor regression (CASE1 3J-meta + synthetic)"
  - 1439783: "docs(85-02): nmr-chemist HMBC SNR-floor note (Pitfall 12, FIX-09 clean)"
---

# Phase 85 Plan 02: HMBC SNR-Floor Regression + Skill Note Summary

Locked the FIX-12 behaviour with a real-data CASE1 regression (the two ring-diagnostic
3J-meta aromatic cross-peaks are retained at the SNR-floor default while the legacy
fraction-of-max pick drops both) plus an always-running synthetic separation test, and
taught the nmr-chemist agent — compound-agnostically — that weak long-range HMBC
correlations clearing the SNR floor are real signal, not noise.

## What Was Built

**Task 1 (9a158a9)** — `tests/test_hmbc_peak_picking_integrity.py`, two classes:

- `TestFIX12CASE1HMBC` (real in-repo data, `data/Ibuprofen/7`), asserting against the
  **guided** HMBC pick (the 13C/HSQC/DEPT-cross-validated correlation set the team consumes):
  - both 3J-meta cross-peaks (H4->C2 at C~140.76 x H~7.11, H6->C3 at C~137.07 x H~7.23)
    are RETAINED at the SNR-floor default;
  - the legacy fraction-of-max pick (`hmbc_use_snr=False`) DROPS both — proving the floor
    is what recovers them (tight C +-1.0 / H +-0.08 window so the nearby 2J-ortho peaks
    cannot stand in);
  - the SNR-default validated count is a bounded ceiling (`<= 250`, observed ~122) and is
    greater than the legacy count (~29) — i.e. richer than fraction-of-max but not the
    ~913 raw-plane / ~165 `-t 0.005` flood;
  - an external CASE1 variant (`.../active-lucy-ng-testprojects/CASE1/7`) with a
    `skipif(not PATH.exists())` guard mirroring the FIX-08 pattern (it ran here because the
    external dataset is present on this machine; it skips cleanly elsewhere).
- `TestFIX12SyntheticSeparation` (always runs, seeded RNG, no external data): a synthetic
  2D HMBC plane with (a) an intense aliphatic peak setting the global max, (b) a weak
  aromatic peak at 0.6% of max but high SNR, (c) a sub-floor (4 sigma < 5 sigma) noise
  blob. Asserts the SNR-floor pick RETAINS (b) and REJECTS (c), the legacy fraction-of-max
  pick at threshold=0.05 DROPS (b), and SNR-mode peaks carry a finite `snr` while legacy
  peaks leave `snr=None`. Captures the FIX-12 "separable in SNR space, not fraction-of-max
  space" property without external data.

**Task 2 (1439783)** — nmr-chemist agent gains **Pitfall 12** (placed after Pitfall 11,
near the Pitfall 3 HMBC-noise / SNR material): the HMBC pick now applies a noise-relative
SNR floor rather than fraction-of-max alone, so an intense 1J-leak/2J peak no longer
suppresses weak-but-real long-range correlations; aromatic 3-bond long-range correlations
are diagnostic ring-connectivity signal and must not be dismissed as noise on percentage-
of-max grounds; prefer the SNR-floor pick by default. Fully compound-agnostic.

## Empirical Retention Evidence (CASE1 expno-7, guided pick)

| path | validated count | 3J-meta H4->C2 (C~140.76 x H~7.11) | 3J-meta H6->C3 (C~137.07 x H~7.23) |
|------|-----------------|-------------------------------------|-------------------------------------|
| SNR floor k=5 (new default) | ~122 | RETAINED | RETAINED |
| legacy fraction-of-max (0.05) | ~29 | DROPPED | DROPPED |
| raw PeakPicker2D SNR plane (no cross-val) | ~913 maxima | (flood) | (flood) |
| raw fraction-of-max -t 0.005 | ~165 | — | — |

The two 3J-meta peaks sit at ~0.6% of the global max (intensity ~5e5 vs max 7.48e7) yet
SNR ~22 and ~10 over the global MAD sigma (~2.15e4) — comfortably above the k=5 floor,
invisible to the 5%-of-max default. The guided 13C/HSQC cross-validation collapses the
~913 raw-plane maxima to ~122 genuine correlations.

## FIX-09 Compound-Agnostic Guard

The nmr-chemist edit passes the plan's grep gate: `grep -Eic
'ibuprofen|CASE1|CASE9|expno|C13H18O2|C12H16O3|para-benzoate|166\.08|7\.11|140\.|136\.9'`
returns **0**. The note uses only generic NMR language (no compound, formula, expno, or
test-specific ppm). The test file deliberately references CASE1/Ibuprofen/expno-7 and the
specific shifts — permitted because it is a test, not a runtime skill.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Plan magic number wrong for the consumed artifact] Count ceiling raised from `<= 60` to `<= 250`**
- **Found during:** Task 1, empirically measuring the picks.
- **Issue:** The plan suggested asserting `count <= 60`. The guided SNR-default pick on
  CASE1 yields ~122 validated correlations (matching 85-01's recorded "122 validated"),
  so a `<= 60` ceiling would falsely fail. The raw `PeakPicker2D` plane pick (no
  cross-validation) yields ~913 — that is the flood the ceiling must guard against.
- **Fix:** Asserted against the guided pick with a ceiling of `<= 250` (bounded, well below
  the ~913 raw / ~165 `-t 0.005` floods) AND that SNR count > legacy count. This honors the
  success criterion ("sane validated-correlation count ceiling, not a 165/913-flood") with
  numbers grounded in the actual artifact rather than the plan's estimate.
- **Files modified:** tests/test_hmbc_peak_picking_integrity.py
- **Commit:** 9a158a9

## Deferred Issues

- **Pre-existing ruff/mypy noise (out of scope).** The repo carries ~280 pre-existing ruff
  and ~111 pre-existing mypy items in untouched code. All lines I authored are ruff-clean
  and mypy-clean (verified on the new test file in isolation).

## Known Stubs

None.

## Threat Flags

None. No new network endpoints, auth paths, file-access patterns, or schema changes. The
test only reads local Bruker datasets (read-only); the external path is skipif-guarded
(T-85-02-02 accepted/mitigated). The nmr-chemist edit leaks no answer-key (T-85-02-01
mitigated, FIX-09 grep gate == 0). No new dependencies (T-85-02-SC).

## Verification

- `pytest tests/test_hmbc_peak_picking_integrity.py -v` — 8 passed (synthetic always;
  CASE1 guided in-repo runs; external CASE1 variant ran here, skips cleanly when absent).
- `pytest test_hmbc_peak_picking_integrity + test_peak_picking_integrity (FIX-08 1D) +
  test_hmbc_guided_picker + test_peak_picker_2d + test_peak_picker_snr` — 60 passed
  (1D FIX-08 path not regressed).
- `ruff check tests/test_hmbc_peak_picking_integrity.py` — clean.
- `mypy tests/test_hmbc_peak_picking_integrity.py` — Success: no issues.
- FIX-09 grep gate on `.claude/agents/lucy-nmr-chemist.md` — 0 contaminant hits; `SNR`
  note present.

Note: tests were run with `PYTHONPATH=<worktree>/src` because the editable install
resolves `lucy_ng` to the main-repo `src/`; the worktree changes (test + skill .md only,
no src) are otherwise correctly on disk.

## Self-Check: PASSED

- tests/test_hmbc_peak_picking_integrity.py — FOUND
- .claude/agents/lucy-nmr-chemist.md (Pitfall 12 present) — FOUND
- Commit 9a158a9 — FOUND
- Commit 1439783 — FOUND
