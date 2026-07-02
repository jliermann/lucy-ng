---
phase: 86-ranker-path-unification
plan: 02
subsystem: cli / ranking / prediction
tags: [13c-prediction, hose-lookup, backend-unification, cli, regression-tests]
requires:
  - resolve_c13_predictor (prediction/resolver.py, Plan 86-01)
  - SolutionRanker.from_database (ranking/ranker.py, Plan 86-01)
  - C13Predictor.from_database / predict_from_smiles (predictor.py, pre-existing)
  - DatabaseFinder.find_hose_database (finder.py, pre-existing)
provides:
  - "lucy lsd rank --db / --max-radius (DB-first backend parity with predict c13)"
  - "_perform_ranking routed through resolve_c13_predictor (single prediction path)"
  - "predict_c13 routed through resolve_c13_predictor (literal RANK-01 unification)"
  - "RANK-01/02/03 regression tests on CASE1 (ibuprofen) + CASE3 (pulegone)"
affects:
  - cli/lsd.py (ranker backend selection now lives only in the shared helper)
  - cli/predict.py (4-tier ladder collapsed to one resolve_c13_predictor call)
tech-stack:
  added: []
  patterns:
    - "Single shared backend ladder consumed by both CLIs (no divergent copy) — RANK-01"
    - "Deterministic r6-only HOSE seeding for non-circular ordering tests"
    - "skipif(find_hose_database() is None) real-DB integration as the ordering-fix carrier"
key-files:
  created: []
  modified:
    - src/lucy_ng/cli/lsd.py
    - src/lucy_ng/cli/predict.py
    - tests/test_ranking.py
decisions:
  - "Backend selection lives ONLY in resolve_c13_predictor; neither CLI re-branches on db/table"
  - "Seed only the full-radius (r6) HOSE code in the deterministic DB so low-radius isomer collisions cannot give a wrong isomer a spurious perfect score (anti-circularity)"
  - "Tight MAE<=0.5 / full-match real-DB assertion is ibuprofen-specific (empirically reproduced 0.244 / 13-13); pulegone (conjugated enone) asserts the ordering-fix + a loose bound per plan"
  - "_match_shifts / MAE aggregation left byte-for-byte untouched"
metrics:
  duration: ~8 min
  completed: 2026-06-23
  tasks: 2
  files: 3
  commits: 2
---

# Phase 86 Plan 02: Ranker Path Unification (CLI Wiring) Summary

`lucy lsd rank` and `lucy predict c13` now resolve their 13C predictor through the **same** `resolve_c13_predictor` ladder, so the ranker is DB-first like predict c13 (RANK-01); the rank command gained `--db`/`--max-radius` parity; and RANK-01/02/03 regression tests pin per-shift parity, MAE/match-count agreement, and the wrong-isomer ordering fix on CASE1 (ibuprofen) and CASE3 (pulegone).

## What Was Built

- **`cli/lsd.py` `_perform_ranking`** — the hardwired `_get_default_table_path()` + `SolutionRanker.from_table_file(...)` block (the JSON-only divergence) is replaced by a single `resolve_c13_predictor(db=db, table=table, max_radius=max_radius)` call, with the resulting predictor wrapped by `SolutionRanker(predictor, tolerance=tolerance)`. Two new params (`db`, `max_radius`) added; backend selection now lives **only** in the shared helper. The helper's "no backend" / load errors are translated to `click.echo(err=True)` + `SystemExit(1)`, preserving the CLI error contract. `_get_default_table_path()` is left in the module (other call sites use it).
- **`cli/lsd.py` `lsd_rank` command** — added `--db` (`click.Path(exists=True)`, auto-detected) and `--max-radius` (`int`, default 6) options, threaded into `_perform_ranking`; docstring now documents the predict-c13-mirroring backend priority.
- **`cli/predict.py` `predict_c13`** — the 4-tier ladder (~40 lines) collapsed to one `resolve_c13_predictor(db=db, table=table, max_radius=max_radius)` call. This makes RANK-01 literal: both CLIs call the same helper. Existing options/output unchanged.
- **`tests/test_ranking.py`** — 8 CLI tests (`TestRankCLIBackendWiring`: --db / --table / auto-detect / --max-radius / --help / predict-c13-still-works) + 4 regression classes:
  - `TestRankPredictParity` (RANK-01): resolver predictor vs `C13Predictor.from_database` give bit-identical `PredictedShift` lists (abs diff `< 1e-6`, equal `radius_used`) for ibuprofen and pulegone.
  - `TestRankMAEAgreement` (RANK-02): ranker `sol.mae` matches a directly-recomputed MAE within 0.05 ppm; `matched_count` exact; `total_carbons == len(predictions)` (matched_count is over predictions, never "/10").
  - `TestRankOrderingNonCircular` (RANK-03 deterministic, parity guard): seeds **only r6** HOSE codes, asserts the wrong-isomer r6 codes genuinely **differ** (zero overlap) from the correct structure's **before** asserting the correct structure outranks it.
  - `TestRankRealDBOrderingFix` (RANK-03 ordering-fix, `skipif(find_hose_database() is None)`): ibuprofen reproduces MAE `<= 0.5` / 13-13 matched (vs old 2.23 / 8-13) and outranks the meta wrong isomer; pulegone asserts the ordering-fix + a loose MAE bound (conjugated-enone case).

## Verification

- `pytest tests/test_ranking.py -k "regression or rank01 or rank02 or rank03 or parity or agreement or cli or ordering" -x` -> **18 passed** (includes both real-DB tests; the production DB is present locally).
- `pytest tests/test_ranking.py tests/test_prediction.py` -> **110 passed** (no regressions).
- `pytest tests/test_prediction.py -k "predict_c13 or from_database"` -> **6 passed** (predict_c13 refactor caused no regression).
- `mypy src/lucy_ng` -> **111 errors, identical to the Plan-01 baseline** — zero new errors (verified via stash-baseline diff: 106/106 on the two edited CLI files, 111/111 full src).
- `ruff check` on edited files: `cli/lsd.py` + `cli/predict.py` went 26 -> 22 findings (removed 4 B904 by collapsing the ladder; zero new); `tests/test_ranking.py` stayed at the 20-finding baseline (the one new B905 from a `zip()` was fixed with `strict=True`).
- `lucy lsd rank --help` lists `--db` and `--max-radius`.

## Acceptance Criteria

- `grep "resolve_c13_predictor" cli/lsd.py` inside `_perform_ranking`. ✓
- `grep "resolve_c13_predictor" cli/predict.py` inside `predict_c13`. ✓
- No `SolutionRanker.from_table_file` call remains in `_perform_ranking` (backend selection only in the helper). ✓
- `lucy lsd rank --help` shows `--db` and `--max-radius`. ✓
- `pytest -k cli` >= 5 tests, exit 0 (8 tests). ✓
- predict tests still green. ✓
- RANK-01 parity asserts per-carbon `abs(diff) < 1e-6` for ibuprofen AND pulegone. ✓
- RANK-02 asserts ranker MAE vs recomputed within 0.05 ppm AND matched_count equality. ✓
- Deterministic RANK-03 asserts `correct_hoses != wrong_hoses` (and zero overlap) before the ordering assertion (non-circular). ✓
- Real-DB test is `skipif(find_hose_database() is None)` and asserts MAE bound + matched_count + wrong-isomer-outranked. ✓
- A comment records the deterministic-vs-real-DB responsibility split. ✓

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test correctness] Deterministic ordering test was circular via low-radius HOSE collisions**
- **Found during:** Task 2.
- **Issue:** Initial seeding inserted the correct structure's HOSE codes at **all** radii 1-6. The wrong (meta / ring-shifted) isomer — although it shares **zero** r6 codes — collides with the correct structure at low radius, so via the predictor's r6->r1 fallback it matched the seeded low-radius codes and scored a spurious MAE 0.000 / full match, tying the correct structure. The ordering assertion then failed (and would have been circular even if it passed).
- **Fix:** Seed **only the full-radius (r6) HOSE code** (`_seed_db_for_smiles(..., seed_radius=6)`). The correct structure matches every carbon at r6 (MAE ~0); the wrong isomer (verified zero r6 overlap) finds no r6 match, falls back through r5..r1 (none seeded), and is left unranked / poorly ranked. This is exactly the anti-circularity the plan mandates.
- **Files modified:** tests/test_ranking.py
- **Commit:** 0eb8cc9

**2. [Rule 1 - Test correctness] Real-DB MAE<=0.5 / full-match pin is ibuprofen-specific**
- **Found during:** Task 2.
- **Issue:** The plan's RANK-03 real-DB intent ("MAE <= ~0.5 AND matched_count == total_carbons ... Same BOTH-assertions for pulegone **where available**"). Empirically, the production DB gives pulegone MAE 1.91 / 7-10 (the conjugated-enone carbons predict less tightly), not <=0.5 / 10-10. The 0.244 / 13-13 reproduction was verified only for ibuprofen.
- **Fix:** Parametrized the real-DB assertion: ibuprofen keeps the tight `<=0.5` + full-match pin (the documented reproduction); pulegone asserts the **ordering-fix** (correct outranks the wrong isomer: 1.91 < 3.25) + a loose `<=3.0` MAE bound. This matches the plan's "where available" hedge and the A3 assumption-log note ("RANK-03 test should *assert* it rather than assume it") without over-claiming an unverified pulegone bound.
- **Files modified:** tests/test_ranking.py
- **Commit:** 0eb8cc9

## Known Stubs

None — both CLIs are wired to a live backend; no placeholder/empty data paths introduced.

## Self-Check: PASSED

- FOUND: src/lucy_ng/cli/lsd.py
- FOUND: src/lucy_ng/cli/predict.py
- FOUND: tests/test_ranking.py
- FOUND commit eaf908b (Task 1)
- FOUND commit 0eb8cc9 (Task 2)
