# Phase 86: Ranker Path Unification - Research

**Researched:** 2026-06-23
**Domain:** Python tooling — 13C prediction backend unification (`lucy lsd rank` ↔ `lucy predict c13`)
**Confidence:** HIGH (root cause empirically reproduced against live code + DB this session)

## Summary

The defect is **fully root-caused and empirically reproduced** in this research session. Both
`lucy lsd rank` and `lucy predict c13` already share the *same* prediction engine
(`C13Predictor`), the *same* HOSE generator, the *same* molecule preparation (`prepare_mol`,
no-AddHs), the *same* radius-6→1 fallback, and the *same* shift-matching/MAE algorithm
(`SolutionRanker._match_shifts`). The hypothesis in the original todo ("low HOSE radius",
"different matching") is **wrong** and was already corrected in the todo's 2026-06-21 update.

The single divergence is the **lookup backend (data source)**:

- `lucy predict c13` auto-detects and prefers the **SQLite DB** (`lucy-ng-derep.db`, 3.97 GB,
  7.9M HOSE statistics, COCONUT + NMRShiftDB) via `DatabaseFinder.find_hose_database()`.
- `lucy lsd rank` is **hardwired** to the **JSON table** (`hose_nmrshiftdb.json.gz`, 8.2 MB,
  NMRShiftDB-only) via `SolutionRanker.from_table_file(...)` — and `SolutionRanker` has *no*
  `from_database` classmethod, and the `lucy lsd rank` CLI command has *no* `--db` option.

The NMRShiftDB-only table is ~485× smaller and has sparse coverage of conjugated /
heteroatom-perturbed carbons → inflated MAE and (worse) wrong-isomer ordering. Because
`predict c13` uses the rich DB, the analyst's manual `predict c13` override keeps rescuing
the result.

**Empirical reproduction this session (ibuprofen, the exact bug-report shifts):**

| Backend | What uses it | MAE | matched | Source |
|---------|-------------|-----|---------|--------|
| JSON table | `lucy lsd rank` (current) | **2.230** | **8**/13 | reproduced |
| SQLite DB | `lucy predict c13` | **0.244** | **13**/13 | reproduced |

The 2.230 / "8 matches" reproduces the bug report's "2.23 MAE / 8-of-10" exactly. Swapping
**only** the backend (no algorithm change) drops ranker MAE to 0.244 ≈ `predict c13`'s ~0.27.

**Primary recommendation:** Add `SolutionRanker.from_database(db_path, tolerance, max_radius)`
mirroring `from_table_file` but calling `C13Predictor.from_database(...)`; in `cli/lsd.py`
`_perform_ranking`, replace the hardwired `from_table_file` with the same 4-tier auto-detect
priority `predict c13` uses (DB first via `DatabaseFinder.find_hose_database()`, JSON table
fallback), and add `--db`/`--table` overrides to the `rank` command for parity. Two files,
zero changes to the matching algorithm.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RANK-01 | `lucy lsd rank` and `lucy predict c13` produce the same per-shift 13C prediction for an identical molecule (single prediction path; no divergent code) | Both already call `C13Predictor.predict_from_smiles`; unify only the backend selection so both resolve the same DB. After fix, identical molecule → identical `PredictedShift` list. Verified: DB backend in ranker yields 13/13 matched, MAE 0.244 = predict c13. |
| RANK-02 | For a correct structure, ranker MAE / match-count agrees with `predict c13` within a defined tolerance | Once both use the DB, per-shift predictions are byte-identical → MAE/match-count identical (tolerance can be near-zero, e.g. MAE within 0.01 ppm). The *only* residual source of difference is `--max-radius` parity (both default 6). See "MAE / match-count semantics" below. |
| RANK-03 | Regression test pins ranker↔predict agreement on CASE1 (ibuprofen) and CASE3 (pulegone) | Existing fixture/skip-marker conventions in `tests/test_ranking.py` (`skipif` on table existence) + `temp_db_with_ethanol` DB-fixture pattern in `tests/test_prediction.py` give the exact template. Ibuprofen SMILES + shifts already in the suite (`test_from_table_file_integration`). |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| 13C shift prediction | `prediction/` (`C13Predictor`) | — | Single owner of HOSE→shift logic; both CLIs delegate here |
| HOSE lookup backend selection | `database/` (`DatabaseFinder`) | `cli/predict.py`, `cli/lsd.py` | `DatabaseFinder` is the consolidated finder; CLIs apply the priority |
| Candidate ranking / matching | `ranking/` (`SolutionRanker`) | — | Owns match + MAE; must NOT change in this phase |
| Backend wiring for ranking | `ranking/ranker.py` + `cli/lsd.py` | — | The two files that need editing |

## Standard Stack

This is an existing-codebase refactor — no new external packages. The fix reuses code that
already exists and is tested.

### Core (existing modules — reused, not added)
| Module | Symbol | Purpose | Status |
|--------|--------|---------|--------|
| `lucy_ng.prediction.predictor` | `C13Predictor.from_database` | DB-backed predictor factory | **Already exists** (predictor.py:61-75) — the ranker just doesn't call it |
| `lucy_ng.prediction.db_lookup` | `DatabaseHOSELookup` | SQLite HOSE backend, implements `HOSELookupProtocol` | Already exists, tested |
| `lucy_ng.database.finder` | `DatabaseFinder.find_hose_database()` | Auto-detect `lucy-ng-derep.db` | Already exists, used by `predict c13` |
| `lucy_ng.ranking.ranker` | `SolutionRanker.from_table_file` | **Only** factory; needs a `from_database` sibling | Edit target |
| `lucy_ng.cli.lsd` | `_perform_ranking`, `lsd_rank` | Hardwired to `from_table_file` | Edit target |

### No new dependencies
No `npm`/`pip`/`cargo` installs. The Package Legitimacy Audit is therefore **N/A** for this
phase (no external packages installed). slopcheck not run — nothing to check.

## Architecture Patterns

### System Architecture Diagram (current vs. target)

```
CURRENT (divergent):

  lucy predict c13 <smiles>                 lucy lsd rank <smi-file> --shifts ...
        │                                          │
  cli/predict.py:predict_c13               cli/lsd.py:lsd_rank → _perform_ranking
        │  4-tier priority:                        │  hardwired:
        │  1 --db  2 --table                       │  _get_default_table_path()
        │  3 find_hose_database()  ◄── DB          │  → hose_nmrshiftdb.json.gz ◄── JSON only
        │  4 find_hose_table()                     │
        ▼                                          ▼
  C13Predictor.from_database(DB)           SolutionRanker.from_table_file(JSON)
        │                                          │  (= C13Predictor.from_table_file(JSON))
        └──────────────┬───────────────────────────┘
                       ▼  SAME from here down
            C13Predictor.predict_from_smiles(smiles)
              → prepare_mol (SetAromaticity, no AddHs)   [hose.py:92]
              → predict_from_mol → RemoveHs              [predictor.py:104-128]
              → _predict_for_atom: radius 6→1 fallback   [predictor.py:130-162]
              → lookup.lookup_stats_at_radius(...)  ◄── DIVERGENCE IS UPSTREAM, in `lookup`
              → PredictedShift(shift = stats.mean)
        (rank path additionally:) SolutionRanker._match_shifts → assignments + MAE


TARGET (unified): make `lucy lsd rank` use the SAME 4-tier backend priority,
DB-first, so `lookup` is the same DatabaseHOSELookup in both paths.
```

### Pattern 1: Mirror the existing `from_table_file` factory
`SolutionRanker.from_table_file` (ranker.py:301-323) is the exact template. Add a sibling:

```python
# Source: pattern mirrors ranker.py:301-323 + predictor.py:61-75 (both verified this session)
@classmethod
def from_database(
    cls,
    db_path: str | Path,
    tolerance: float = 3.0,
    max_radius: int = 6,
) -> "SolutionRanker":
    from pathlib import Path
    predictor = C13Predictor.from_database(Path(db_path), max_radius=max_radius)
    return cls(predictor, tolerance=tolerance)
```

### Pattern 2: Reuse the exact backend-priority ladder from `predict c13`
`cli/predict.py:72-115` is the canonical 4-tier ladder (explicit --db → explicit --table →
`find_hose_database()` → `find_hose_table()`). `_perform_ranking` (lsd.py:258-277) should be
refactored to the same ladder so behaviour is identical by construction. Keeping the two
ladders structurally identical (or extracting one shared helper) is the cleanest way to
guarantee RANK-01 long-term.

### Anti-Patterns to Avoid
- **Touching `_match_shifts` or the ranking contract.** The matching/MAE algorithm is correct
  and unchanged. The bug is purely the data source. Editing it risks regressing the 87 passing
  ranking/prediction tests.
- **Leaving `from_table_file` as the only factory** (i.e., "fixing" by changing the default
  table path). The JSON table is fundamentally NMRShiftDB-only and sparse; the fix must reach
  the DB.
- **A second, divergent backend-priority ladder.** If you don't share the ladder with
  `predict c13`, the two paths can drift again. Prefer one shared helper or a structurally
  identical copy with a test that pins parity.
- **Forgetting `--max-radius` parity.** `predict c13` exposes `--max-radius` (default 6);
  the rank path hardcodes `max_radius=6` via `from_table_file`'s default. If a user sets a
  non-default radius on one but not the other, predictions diverge. Keep both at 6 by default;
  optionally expose `--max-radius` on `rank` for true parity.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DB-backed predictor | A new SQLite query path in the ranker | `C13Predictor.from_database` (predictor.py:61) | Already exists + tested |
| Backend auto-detection | New file-search logic in lsd.py | `DatabaseFinder.find_hose_database()` / `find_hose_table()` (finder.py:98-136) | Consolidated, used by predict c13 |
| HOSE lookup over SQLite | Raw `sqlite3` in ranker | `DatabaseHOSELookup` (db_lookup.py) | Implements `HOSELookupProtocol`; backend-agnostic |
| Shift matching / MAE | Rewrite matching | `SolutionRanker._match_shifts` (ranker.py:229) | Correct, symmetry-aware N:1; leave untouched |

**Key insight:** Every building block for the fix already exists and is tested. This is a
**wiring** change (point the ranker at the DB backend), not new logic.

## Code-Path Evidence (file:line)

### Path A — `lucy predict c13` (the GOOD path)
1. `cli/predict.py:48-115` `predict_c13` — 4-tier backend priority:
   - `:75` explicit `--db` → `C13Predictor.from_database`
   - `:83` explicit `--table` → `C13Predictor.from_table_file`
   - `:91` `DatabaseFinder.find_hose_database()` → `from_database`  ← **default hit**
   - `:99` `DatabaseFinder.find_hose_table()` → `from_table_file`
2. `cli/predict.py:118` `predictor.predict_from_smiles(smiles)`
3. `prediction/predictor.py:77-102` `predict_from_smiles` → `HOSECodeGenerator.prepare_mol(smiles)` (`:86`)
4. `prediction/hose.py:92-122` `prepare_mol` — `MolFromSmiles` + `Chem.SetAromaticity`, **no AddHs**
5. `prediction/predictor.py:104-128` `predict_from_mol` — `Chem.RemoveHs(mol)` (`:116`), iterate C atoms
6. `prediction/predictor.py:130-162` `_predict_for_atom` — radius `max_radius`→`min_radius` (6→1) fallback, `:152` `self._lookup.lookup_stats_at_radius(hose_code, radius)`
7. `prediction/db_lookup.py:50-72` `DatabaseHOSELookup.lookup_stats_at_radius` → `self._db.get_hose_stats(...)` → `HOSEStatsResult(mean=record.mean, ...)` (pre-computed)
8. `prediction/predictor.py:192-202` `PredictedShift(shift=stats.mean, ...)`

### Path B — `lucy lsd rank` (the BAD path)
1. `cli/lsd.py:575-675` `lsd_rank` → `:675` `_perform_ranking(smiles_file, shifts, top, tolerance, table, fmt)`
2. `cli/lsd.py:258-267` table resolution: explicit `--table` OR `_get_default_table_path()`
3. `cli/lsd.py:113-139` `_get_default_table_path` — **hardwired** to `hose_nmrshiftdb.json.gz` (project → package → home); **never** consults `DatabaseFinder.find_hose_database()`
4. `cli/lsd.py:271-274` `SolutionRanker.from_table_file(table_path, tolerance)`  ← **DIVERGENCE**
5. `ranking/ranker.py:301-323` `from_table_file` → `C13Predictor.from_table_file(...)` (JSON backend)
6. `cli/lsd.py:279` `ranker.rank(...)` → `ranking/ranker.py:107-227` `rank` → `:140` `self.predictor.predict_from_smiles(...)`  ← **identical engine from here, same steps 3-8 as Path A but with the JSON `HOSELookupTable` backend**
7. `prediction/lookup.py:116-140` `HOSELookupTable.lookup_stats_at_radius` — computes `statistics.mean(shifts)` **on the fly**, **ignores `radius`** (`# noqa: ARG002`)

### The divergence, precisely
- **NOT** HOSE generation (`generate_for_atom`, same).
- **NOT** AddHs / molecule prep (`prepare_mol` + `RemoveHs`, same).
- **NOT** radius fallback (6→1 in `_predict_for_atom`, same).
- **NOT** matching/MAE (`_match_shifts`, same; ranker.py:229-299).
- **IS** the `lookup` object handed to `C13Predictor`:
  - DB path → `DatabaseHOSELookup` over `lucy-ng-derep.db` (7.9M entries, pre-computed mean).
  - JSON path → `HOSELookupTable` over `hose_nmrshiftdb.json.gz` (~8 MB, NMRShiftDB-only,
    mean computed on the fly). **Sparser coverage = misses good high-radius matches for
    conjugated/heteroatom carbons → falls back to coarse low-radius codes or to a poorer mean.**

### Subtle backend semantics (must be aware of, do NOT need to "fix")
- **Radius semantics differ but are harmless for unification:** `HOSELookupTable` ignores the
  `radius` arg (radius is implicit in the HOSE string); `DatabaseHOSELookup` keys on
  `(hose_code, radius)`. Both are driven by the same `_predict_for_atom` 6→1 loop, so the
  effective behaviour is "best available radius." Unifying to the DB is the goal; no change
  to this logic.
- **Aggregation:** both ultimately return `mean`. JSON computes `statistics.mean` live; DB
  returns the pre-computed `hose_stats.mean` (Welford-accumulated at build time). For an
  identical underlying shift population these are equal; the DB simply has a *larger, richer*
  population. So unifying the backend, not the aggregation, is what closes the gap.

## MAE / match-count semantics (for defining RANK-02 tolerance)

`SolutionRanker._match_shifts` (ranker.py:229-299):
- Iterates over **predictions** (one per carbon atom), each finds its **closest experimental
  peak** (N:1 allowed — symmetry: 2 equivalent carbons both match one peak).
- **MAE = mean of |pred − closest_exp| over ALL predictions** (no tolerance cutoff; ranker.py:292-297).
- **matched_count = # predictions within `tolerance` (default 3.0 ppm)** of their closest exp
  (ranker.py:156, 269-272). Note this is counted over *predictions* (13 for ibuprofen), not
  over *experimental peaks* (10) — hence "8/13" and "13/13" in the reproduction, not "/10".
- `predict c13` does **not** compute MAE/match-count at all — it just emits per-shift
  predictions (`cli/predict.py:120-143`). So RANK-02 "agreement" must be defined as:
  **for the same molecule, the per-`PredictedShift` `(atom_index, shift, radius_used)` lists
  produced by the two paths are identical** (this is the real RANK-01 guarantee), from which
  MAE/match-count agreement follows trivially.

**Recommended RANK-02 tolerance definition:** Because after unification both paths run the
*same* `C13Predictor` over the *same* DB, predictions are **bit-identical**, so:
- Per-shift agreement: `abs(rank_shift − predict_shift) < 1e-6` for every carbon (effectively 0).
- MAE agreement: ranker MAE vs a manually-computed MAE-from-`predict c13` within **≤ 0.05 ppm**
  (allows for float-order differences only). The reproduced gap was 2.230 → 0.244; the target
  is full convergence, so a tight tolerance is appropriate and honest.

## Runtime State Inventory

This phase is a code change to backend wiring; it has no stored-data/service/OS state to
migrate. Inventory for completeness:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — the DB (`lucy-ng-derep.db`) and JSON table already exist; we only change *which* is read. No data written/migrated. | None |
| Live service config | None — no external service. | None |
| OS-registered state | None. | None |
| Secrets/env vars | `LUCY_DATABASE` env var is read by `DatabaseFinder.find_derep_database()` (finder.py:42) — unchanged; the rank path will newly *honour* it (a benefit). | None — code reuse only |
| Build artifacts | None new. Editable install means edits to ranker.py/lsd.py take effect immediately (see runtime caveat below). | None |

## Common Pitfalls

### Pitfall 1: Editing while a blind CASE run is in flight
**What goes wrong:** The installed `lucy` is the **editable** repo package. Editing
`ranker.py`/`lsd.py` mid-run alters that run's live `lucy lsd rank` behaviour.
**How to avoid:** Do not execute Phase 86 while a Phase-89 blind UAT is running. (Phase 86
precedes the UAT phase in the roadmap, so this is sequencing-safe — just don't overlap.)
**Source:** todo `2026-06-17-lucy-lsd-rank-scoring-defect.md`, NOTE section.

### Pitfall 2: DB not present in CI / fresh checkout
**What goes wrong:** `lucy-ng-derep.db` is 3.97 GB and **not** in git (`lucy database download`
fetches it). A DB-requiring regression test will fail on a machine without it.
**How to avoid:** Follow the existing `skipif` convention (ranker.py test
`test_from_table_file_integration` uses `@pytest.mark.skipif(not Path(...).exists())`). For the
DB-backed RANK-03 test, either (a) skipif on `DatabaseFinder.find_hose_database() is None`, or
(b) build a tiny `temp_db` with the handful of HOSE codes for ibuprofen/pulegone carbons using
the existing `temp_db_with_ethanol` fixture pattern (test_prediction.py:622-645) so the test
runs without the 3.97 GB DB. **(b) is preferred** for a deterministic, CI-safe pin; **(a)** as
a secondary "real DB" integration test.

### Pitfall 3: The two backend tables have *different filenames*
**What goes wrong:** `DatabaseFinder.DEFAULT_TABLE_PATH = data/reference/hose_lookup.json.gz`
(finder.py:22) but `_get_default_table_path()` in lsd.py looks for
`data/reference/hose_nmrshiftdb.json.gz` (lsd.py:122). Only the latter exists on disk
(verified). If you naïvely swap `_get_default_table_path` for `DatabaseFinder.find_hose_table()`
as the JSON *fallback*, the fallback path changes (it would look for the non-existent
`hose_lookup.json.gz` and miss the present `hose_nmrshiftdb.json.gz`).
**How to avoid:** When unifying, ensure the JSON fallback still locates the file that actually
ships (`hose_nmrshiftdb.json.gz`). Either keep `_get_default_table_path()` as the JSON-table
fallback, or add `hose_nmrshiftdb.json.gz` to `DatabaseFinder.find_hose_table()` candidates.
This is a real, easy-to-miss trap — verified by listing `data/reference/`.

### Pitfall 4: `matched_count` denominator confusion
**What goes wrong:** The bug report says "8-of-10" but the code reports `matched/total_carbons`
= 8/13 (predictions), not /10 (exp peaks). A regression assertion written against "/10" will
be wrong.
**How to avoid:** Assert against `matched_count` (count of matched predictions) and `mae`, not
a hand-derived "/10". Reproduction confirms 8/13 (table) vs 13/13 (DB).

## State of the Art

| Old Approach | Current/Target Approach | When Changed | Impact |
|--------------|------------------------|--------------|--------|
| Ranker scores against NMRShiftDB-only JSON table | Ranker scores against full 7.9M-entry DB (same as predict c13) | Phase 86 | MAE 2.23→0.24 on ibuprofen; correct-isomer ordering on conjugated systems |
| `SolutionRanker` has only `from_table_file` | Add `from_database` + DB-first auto-detect | Phase 86 | Single prediction path (RANK-01) |

## Validation Architecture

`workflow.nyquist_validation` is not set in `.planning/config.json` → treated as **enabled**.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest ≥7.0 (+ pytest-cov) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (testpaths=`tests`, pythonpath=`src`, addopts=`-v --tb=short`) |
| Quick run command | `pytest tests/test_ranking.py tests/test_prediction.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RANK-01 | rank & predict c13 give identical per-shift predictions for same molecule | unit (temp_db) | `pytest tests/test_ranking.py -k path_parity -x` | ❌ Wave 0 |
| RANK-01 | `SolutionRanker.from_database` exists + builds a DB-backed ranker | unit (temp_db) | `pytest tests/test_ranking.py -k from_database -x` | ❌ Wave 0 |
| RANK-01 | `lucy lsd rank` CLI auto-detects DB first, honours `--db`/`--table` | unit (cli_runner + temp_db) | `pytest tests/test_ranking.py -k cli_db -x` | ❌ Wave 0 |
| RANK-02 | ranker MAE/match-count agrees with predict c13 within tolerance | unit (temp_db) | `pytest tests/test_ranking.py -k rank02_agreement -x` | ❌ Wave 0 |
| RANK-03 | regression pins ibuprofen + pulegone ranker↔predict agreement | unit (temp_db) + skipif real-DB integration | `pytest tests/test_ranking.py -k regression_case -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_ranking.py tests/test_prediction.py -x`
- **Per wave merge:** `pytest`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_ranking.py` — add `from_database`, path-parity, CLI-db, RANK-02-agreement,
      and RANK-03 regression tests (extend existing file; do **not** create a new one).
- [ ] Reuse `temp_db_with_ethanol`-style fixture (test_prediction.py:622-645) → build a
      small DB seeded with the HOSE codes needed for ibuprofen + pulegone carbons, OR add a
      `skipif(DatabaseFinder.find_hose_database() is None)` real-DB integration test (or both:
      deterministic temp_db unit test + opportunistic real-DB integration test).
- [ ] Reuse `cli_runner` fixture (test_prediction.py:456) for CLI-level `--db`/`--table`/auto
      tests.

*Framework already installed; no install step needed.*

## Existing Test Conventions (for RANK-03)

| Convention | Location | Reuse for |
|-----------|----------|-----------|
| `skipif(not Path("data/reference/hose_nmrshiftdb.json.gz").exists())` + real ibuprofen rank | `tests/test_ranking.py:451-472` (`test_from_table_file_integration`) | Real-DB integration variant; ibuprofen SMILES `CC(C)Cc1ccc(cc1)C(C)C(=O)O` + shifts already there |
| `temp_db_with_ethanol` — build a tmp SQLite with `HOSEStatsRecord` rows + `insert_hose_stats_batch` | `tests/test_prediction.py:622-645` | Deterministic CI-safe temp_db for RANK-03 |
| `cli_runner` Click `CliRunner` fixture | `tests/test_prediction.py:456` | CLI `--db`/`--table`/auto tests |
| Mock-predictor ranking tests (`MagicMock(spec=C13Predictor)`, `predict_side_effect`) | `tests/test_ranking.py:478-503` | Backend-agnostic ranking-logic tests (unchanged) |
| Regression fixtures dir | `tests/fixtures/regression/` (e.g. `ibuprofen_no_4j.lsd`) | Place any pinned shift/expected files here if needed |

**Verified molecule identities (orchestrator answer-key — keep OUT of the runtime CASE skill):**
- CASE1 = ibuprofen: `CC(C)Cc1ccc(cc1)C(C)C(=O)O` (already in test suite).
- CASE3 = pulegone: canonical `CC(C)=C1CCC(C)CC1=O` (RDKit-canonicalized this session from
  `CC1CCC(=C(C)C)C(=O)C1`). The 2026-06-18 wrong-isomer reproduction was on "a conjugated
  cyclic enone" = pulegone (an α,β-unsaturated cyclohexanone) — exactly the conjugated-carbonyl
  regime the sparse JSON table mis-predicts.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `lucy-ng-derep.db` (HOSE DB) | DB-backed ranking + real-DB integration test | ✓ | 3.97 GB at `data/reference/lucy-ng-derep.db` | temp_db fixture for unit tests |
| `hose_nmrshiftdb.json.gz` | JSON fallback path | ✓ | 8.2 MB at `data/reference/` | — |
| `hosegen` (HOSE_code_generator) | HOSE generation | ✓ | importable (reproduction ran) | hard requirement, no fallback |
| RDKit | mol parsing/aromaticity | ✓ | importable | hard requirement |
| pytest | tests | ✓ | ≥7.0 | — |

**Missing dependencies with no fallback:** None — full reproduction ran successfully this session.

## Project Constraints (from CLAUDE.md)

- **HOSE Codes: NO Explicit Hydrogens.** Both paths already honour this: `prepare_mol` does
  *not* call `AddHs` (hose.py:121 comment), and `predict_from_mol` calls `Chem.RemoveHs`
  (predictor.py:116). The fix must NOT introduce any AddHs. (This was a prime suspect per the
  brief, but is **verified identical** across both paths — not the cause.)
- **COCONUT 1-based atom indices:** irrelevant to this phase (no SDF parsing here).
- Dev commands: `pytest`, `pytest --cov=lucy_ng`, `mypy src/lucy_ng` (strict), `ruff check src tests`.
  The phase must keep mypy-strict + ruff clean. New `from_database` classmethod needs full type
  annotations to satisfy strict mypy (mirror `from_table_file`'s signature, which is annotated).
- **Single native-LSD path / D-02:** unchanged; this phase touches only prediction backend, not
  the solver.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | CASE3 (the "conjugated cyclic enone" in the 2026-06-18 wrong-isomer repro) = pulegone | Test conventions / RANK-03 | Low — RANK-03 names CASE1+CASE3; pulegone is the verified CASE3 identity in CASE-DATASET-IDENTITIES.md. If the 2026-06-18 molecule was a *different* enone, the regression still validly pins CASE1+CASE3 per the requirement; only the historical "2.23 came from this exact molecule" narrative would shift. |
| A2 | After unification, per-shift predictions are bit-identical between paths (tolerance ~0) | RANK-02 tolerance | Low — both call the same `C13Predictor` over the same DB; only `--max-radius` could differ. Mitigation: pin both at default 6 and test parity directly. |
| A3 | The pulegone wrong-isomer ordering is fixed by the DB backend (as ibuprofen MAE was) | Summary | Medium — verified for ibuprofen empirically; pulegone fix is inferred from same mechanism (sparse table misses conjugated-C codes). The RANK-03 test should *assert* it rather than assume it. |

## Open Questions

1. **Should `_perform_ranking` share a single backend-priority helper with `predict_c13`, or
   keep two structurally-identical ladders?**
   - What we know: A shared helper most strongly guarantees RANK-01 won't regress.
   - What's unclear: Whether the planner wants the refactor scope (extracting a
     `resolve_predictor(db, table, max_radius)` helper into e.g. `database/finder.py` or a new
     `prediction` helper) vs. the minimal 2-file change.
   - Recommendation: Extract a tiny shared `resolve_c13_predictor(...)` helper and have both
     CLIs call it — this is the cleanest "single prediction path" and is itself unit-testable.
     If scope must stay minimal, copy the ladder + add a parity test.

2. **Expose `--max-radius` on `lucy lsd rank` for full parity with `predict c13`?**
   - Recommendation: Yes — cheap, and prevents a silent divergence vector. Default 6.

3. **RANK-03: deterministic temp_db vs. real 3.97 GB DB?**
   - Recommendation: Both — a temp_db unit test (CI-safe, the pin) plus a `skipif` real-DB
     integration test (catches DB-content regressions on dev machines).

## Sources

### Primary (HIGH confidence — read this session, file:line cited above)
- `src/lucy_ng/ranking/ranker.py` — `SolutionRanker`, `_match_shifts`, `from_table_file` (no `from_database`)
- `src/lucy_ng/prediction/predictor.py` — `C13Predictor.from_database` / `from_table_file`, predict pipeline
- `src/lucy_ng/prediction/hose.py` — `prepare_mol` (no AddHs, SetAromaticity)
- `src/lucy_ng/prediction/db_lookup.py` / `lookup.py` — DB vs JSON backends, `lookup_stats_at_radius`
- `src/lucy_ng/cli/predict.py:48-115` — 4-tier backend priority (the GOOD path)
- `src/lucy_ng/cli/lsd.py:113-139, 207-336, 575-675` — hardwired JSON path (the BAD path)
- `src/lucy_ng/database/finder.py` — `DatabaseFinder.find_hose_database/find_hose_table`
- `tests/test_ranking.py`, `tests/test_prediction.py`, `tests/conftest.py` — test conventions
- **Empirical reproduction** (this session): ibuprofen table-backend MAE 2.230/matched 8 vs
  DB-backend MAE 0.244/matched 13 — reproduces the bug and proves the backend swap fixes it.

### Secondary (project records)
- `.planning/todos/pending/2026-06-17-lucy-lsd-rank-scoring-defect.md` — root-cause trace (2026-06-21 update is correct; original "low radius" hypothesis is wrong)
- `.planning/REQUIREMENTS.md` (RANK-01/02/03), `.planning/STATE.md`

## Metadata

**Confidence breakdown:**
- Root cause / divergence point: **HIGH** — empirically reproduced + file:line traced.
- Fix shape (2-file backend wiring): **HIGH** — all building blocks exist + tested; swap verified.
- Test conventions for RANK-03: **HIGH** — exact fixtures/markers identified in-repo.
- Pulegone-specific wrong-isomer fix: **MEDIUM** — mechanism verified on ibuprofen; assert in RANK-03.

**Research date:** 2026-06-23
**Valid until:** 2026-07-23 (stable internal code; re-verify if ranker.py/predictor.py/lsd.py change)
