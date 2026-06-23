---
created: 2026-06-17
title: Fix lucy lsd rank scoring defect (divergent from predict c13)
area: tooling
resolves_phase: 86
files:
  - src/lucy_ng/ranking/ranker.py
  - src/lucy_ng/prediction/hose.py
  - src/lucy_ng/cli/lsd.py
---

## Problem

`lucy lsd rank` under-scores the correct structure relative to `lucy predict c13`.
Found in the CASE1 (ibuprofen) blind UAT 2026-06-17:

- `lucy lsd rank <top-solution>.smi --shifts <exp>` → **MAE 2.23 ppm, matched 8/10**
  for the correct ibuprofen structure.
- `lucy predict c13 <same SMILES>` → shifts matching experiment to **MAE ~0.27, 10/10**.
- The discrepancy is **identical for the Kekulé form AND the RDKit-canonical aromatic
  form** (both give 2.23 via rank), so it is NOT a Kekulé/aromatization (FIX-11) problem.
  FIX-11 (Phase 84) works correctly in `predict c13`.

`lucy lsd rank` and `lucy predict c13` evidently use divergent prediction/matching code
paths; the ranker is the worse one.

**Risk:** the CASE solution-analyst relies on the ranker to discriminate candidates.
Under-scoring the truth could rank a wrong structure first. The 2026-06-17 run only
succeeded because the agent worked around it by hand-scoring via `predict c13`.

**Misdiagnosis to avoid:** ranking_results.json `note_on_kekule` credits RDKit
canonicalization for the 0.27 — but that 0.27 came from `predict c13`, not from
`lucy lsd rank` on canonical input (which still returns 2.23).

Evidence: `CASE1/analysis/ranking_results.json`; reproduced directly via
`lucy lsd rank <smi> --shifts "180.56,140.84,137.00,129.38,127.26,45.03,44.90,30.14,22.37,18.09"`.

## Update 2026-06-18 — reproduced, more severe

Hit again on a later blind CASE run (a conjugated cyclic enone). This time the ranker did
not merely inflate the MAE — **it placed the WRONG regioisomer at rank 1**. The correct
structure was only recovered by a manual analyst override using a higher-radius (r6) HOSE
prediction plus a diagnostic carbon shift. Root cause is the same: the ranker's
prediction/matching path predicts conjugated carbonyl/olefin carbons poorly (low HOSE radius),
so structures whose distinctive carbons sit in that regime get mis-scored. A less careful
agent that trusted the algorithmic rank-1 would have reported the wrong structure.

→ Raises priority. Likely fix: have `lucy lsd rank` use the same prediction path/HOSE radius
as `lucy predict c13` (which scores these correctly), or escalate radius when a candidate has
conjugated sp2 systems.

## ROOT CAUSE LOCATED 2026-06-21 (read-only code trace)

The earlier "low HOSE radius" hypothesis is **WRONG**. Both paths share the same
`C13Predictor`, the same radius-6→1 fallback, and `SolutionRanker._match_shifts` is
correct (N:1, symmetry-aware, MAE over all predictions to nearest experimental). The
divergence is the **lookup backend / data source**:

- `lucy predict c13` (cli/predict.py) auto-detects and prefers the SQLite DB via
  `DatabaseFinder.find_hose_database()` → `C13Predictor.from_database(...)` =
  `data/reference/lucy-ng-derep.db` (**3.7 GB, 7.9M HOSE statistics**, COCONUT+NMRShiftDB).
- `lucy lsd rank` (cli/lsd.py) is hardwired to `SolutionRanker.from_table_file(...)` =
  `data/reference/hose_nmrshiftdb.json.gz` (**7.8 MB, NMRShiftDB-only**). `SolutionRanker`
  has ONLY a `from_table_file` classmethod — there is NO `from_database`.

So the ranker scores candidates against a ~500× smaller, NMRShiftDB-only table → sparse
coverage of conjugated/unusual carbons (azulenes, conjugated enones, H-bonded carbonyls)
→ inflated MAE and, worse, isomer mis-ordering (the wrong isomer can win). `predict c13`,
on the full DB, scores the same molecules correctly — which is exactly why the analyst's
manual `predict c13` override keeps rescuing the result.

## Solution

Make `lucy lsd rank` use the SAME rich DB backend as `lucy predict c13`. Concrete, contained
(2 files, no change to the matching algorithm):

1. **`ranking/ranker.py`**: add `SolutionRanker.from_database(db_path, tolerance=3.0,
   max_radius=6)` mirroring `from_table_file` but calling `C13Predictor.from_database(...)`.
2. **`cli/lsd.py`** (rank command): replace the hardwired `from_table_file` with the same
   auto-detect priority predict c13 uses — `DatabaseFinder.find_hose_database()` first
   (prefer the 7.9M DB), fall back to the JSON table only if no DB is present. Keep
   `--table`/`--db` overrides for parity.

Regression: re-rank a known conjugated-enone / azulene candidate set and confirm the correct
isomer now ranks #1 under the DB backend (it does via `predict c13`), and that ibuprofen's
ranker MAE drops from ~2.23 to ~0.27 to match `predict c13`.

NOTE: do NOT edit while a blind CASE run is in flight — the installed `lucy` is the editable
repo package, so changing ranker.py/lsd.py would alter that run's live `lucy lsd rank` calls.

Align `lucy lsd rank` scoring with `lucy predict c13`. Root-cause hypotheses to check:
- ranker matching/aggregation leaving exp shifts unmatched (matched=8 → 2 unmatched at tol 3.0)
- symmetry-equivalent-carbon collapsing (2C signals) handled differently than predict
- a different HOSE radius / fallback than the predict path

Non-gating for v9.0. Candidate for v9.1 or a `/gsd-debug` session. Start by diffing the
prediction entry points used by `ranking/ranker.py` vs `prediction/hose.py` (prepare_mol +
HOSE radius), then reconcile the per-shift matching/MAE computation.
