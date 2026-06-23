---
phase: 86-ranker-path-unification
reviewed: 2026-06-23T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/lucy_ng/prediction/resolver.py
  - src/lucy_ng/ranking/ranker.py
  - src/lucy_ng/cli/lsd.py
  - src/lucy_ng/cli/predict.py
  - tests/test_ranking.py
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: issues_found
---

# Phase 86: Code Review Report

**Reviewed:** 2026-06-23
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Phase 86 unifies the two divergent 13C-prediction code paths (`lucy lsd rank` and
`lucy predict c13`) behind a single `resolve_c13_predictor()` backend ladder and adds
`SolutionRanker.from_database`. I reviewed all five listed files at standard depth,
traced the call chain into `C13Predictor`, `DatabaseFinder`, and the downstream
consumer `cli/pylsd.py`, and executed the test suite.

The core refactor is sound and the layering boundary is respected:

- `prediction/resolver.py` does NOT import from `cli/` (verified by `test_resolver_no_cli_layering_inversion`, and by direct inspection). The shipped-table candidate paths are correctly *replicated* rather than imported, avoiding a cli->prediction cycle.
- The backend ladder (explicit db -> explicit table -> auto-detect DB -> auto-detect JSON table, with the `hose_nmrshiftdb.json.gz` filename-trap fallback) matches the documented priority and the old `predict_c13` inline ladder.
- `_perform_ranking`'s new positional/keyword call sites (in `cli/lsd.py` and `cli/pylsd.py`) bind arguments correctly; pylsd now also benefits from DB-first resolution via the defaults.
- The RANK-03 regression test is **genuinely non-circular**: the deterministic test asserts zero r6 HOSE-code overlap between the correct and wrong isomer *before* asserting ordering, and the true ordering-fix validation is carried by the skipif-guarded real-DB test, which I confirmed actually runs (the production DB is present) and passes (ibuprofen reproduces MAE<=0.5 / 13-of-13).
- All 62 tests in `tests/test_ranking.py` pass, including both real-DB ordering-fix parametrizations.

No BLOCKER-level defects (no incorrect behavior, security, or data-loss risk) were
found in the changed code. The findings below are quality/robustness concerns plus
one pre-existing latent bug that the changed file touches (kept as WARNING because
the changed import removal is adjacent to it).

## Warnings

### WR-01: `_is_chemically_plausible()` evaluated twice per solution (correctness-fragile, not just costly)

**File:** `src/lucy_ng/ranking/ranker.py:187-192`
**Issue:** The plausible/implausible partition calls `_is_chemically_plausible(r, ...)`
in *two separate list comprehensions* for every ranked solution:

```python
plausible = [
    r for r in ranked if _is_chemically_plausible(r, experimental_shifts, formula)
]
implausible = [
    r for r in ranked if not _is_chemically_plausible(r, experimental_shifts, formula)
]
```

This is out of v1 performance scope, but the real risk is **correctness coupling**:
the partition is only guaranteed to be a clean disjoint cover because
`_is_chemically_plausible` happens to be deterministic. It calls
`Chem.MolFromSmiles(solution.smiles)` and RDKit aromaticity perception each time. If
that function ever became state-dependent or non-deterministic (e.g. RDKit warning
state, a cached/randomized sanitizer flag, or a future formula-derived heuristic), a
solution could be dropped from BOTH lists (silent data loss) or duplicated into both.
A single evaluation makes the invariant structural rather than incidental.
**Fix:**
```python
flags = [
    (r, _is_chemically_plausible(r, experimental_shifts, formula))
    for r in ranked
]
plausible = [r for r, ok in flags if ok]
implausible = [r for r, ok in flags if not ok]
plausible.sort(key=lambda r: (-r.matched_count, r.mae))
ranked = plausible + [
    r.model_copy(update={"is_plausible": False}) for r in implausible
]
```

### WR-02: `formula` plausibility argument is unreachable from both unified CLI paths

**File:** `src/lucy_ng/ranking/ranker.py:117,184-196` and `src/lucy_ng/cli/lsd.py:208-282`
**Issue:** `SolutionRanker.rank()` accepts a `formula` parameter that drives the DBE
plausibility check (`_is_chemically_plausible` Check 2). But `_perform_ranking` never
accepts or forwards a formula, and `lsd_rank` has no `--formula` option, so through
the unified `lucy lsd rank` path `formula` is always `None` and the DBE consistency
check (`abs(actual_dbe - expected_dbe) > 1`) is dead. The phase explicitly aimed to
make `lsd rank` and `predict c13` consistent and richer; shipping a plausibility
dimension that no CLI can reach is a latent gap that will mislead future maintainers
into thinking DBE filtering is active in CASE runs when it is not.
**Fix:** Either (a) thread a `--formula` option through `lsd_rank` -> `_perform_ranking`
-> `ranker.rank(..., formula=...)`, or (b) if DBE filtering is intentionally deferred,
add a short comment at the `rank()` `formula` param noting no CLI currently supplies it
and reference the backlog item, so the dead branch is documented rather than silent.

### WR-03: `table_info` calls undefined `find_lookup_table` (NameError) in a file this phase edited

**File:** `src/lucy_ng/cli/predict.py:266`
**Issue:** `table_path = Path(table) if table else find_lookup_table()` references a name
that is neither defined nor imported in `predict.py`. Invoking `lucy predict table-info`
without `--table` raises `NameError: name 'find_lookup_table' is not defined` instead of
the intended "No HOSE lookup table found" error. This is **pre-existing** (it predates
the Phase-86 diff), but Phase 86 edited this exact file's import block — it removed
`C13Predictor` from the `lucy_ng.prediction` import while leaving this broken reference
untouched, and the natural fix lives right next to the new `resolve_c13_predictor`
plumbing. Flagging at WARNING (not BLOCKER) because it is not a regression introduced by
this phase and only affects the `--table`-less `table-info` path.
**Fix:** Use the existing finder that this phase already imports elsewhere:
```python
from lucy_ng.database import DatabaseFinder
table_path = Path(table) if table else DatabaseFinder.find_hose_table()
```
(then the existing `if table_path is None or not table_path.exists():` guard handles the
not-found case cleanly).

## Info

### IN-01: Inconsistent type annotation between the two SolutionRanker factory methods

**File:** `src/lucy_ng/ranking/ranker.py:307-309` vs `330-333`
**Issue:** `from_table_file(cls, table_path: str, ...)` annotates `str`, while the new
`from_database(cls, db_path: "str | Path", ...)` annotates `str | Path`. Both implementations
immediately wrap in `Path(...)`, so `from_table_file` already accepts a `Path` at runtime; the
`str`-only annotation is needlessly narrow and inconsistent with its sibling under mypy strict.
**Fix:** Annotate `table_path: "str | Path"` to match `from_database`.

### IN-02: Stale docstring example references a non-shipping table filename

**File:** `src/lucy_ng/ranking/ranker.py:92`
**Issue:** The class docstring example uses
`C13Predictor.from_table_file("hose_lookup.json.gz")`. Per the resolver's own
"filename trap" note, the file that actually ships is `hose_nmrshiftdb.json.gz`;
`hose_lookup.json.gz` is only the `build-table` default output name. A copy-pasted
example pointing at a filename that does not ship will fail for most users.
**Fix:** Update the example to `hose_nmrshiftdb.json.gz`, or prefer
`SolutionRanker.from_database(...)` in the example now that DB is the canonical backend.

### IN-03: `from_table_file` / `from_database` factories are now redundant with the resolver

**File:** `src/lucy_ng/ranking/ranker.py:306-354`
**Issue:** With `resolve_c13_predictor` as the single canonical path, the two
`SolutionRanker.from_*` classmethods duplicate predictor construction (and are what the
tests exercise rather than the CLI path). They remain part of the public API
(`from lucy_ng import SolutionRanker`), so keeping them is defensible, but there is now
a third way to build a ranker that bypasses the unified ladder. Consider documenting
that the resolver is preferred, or having these delegate through it, to prevent future
divergence — the exact class of bug Phase 86 set out to eliminate.
**Fix:** Add a one-line note in each factory docstring pointing callers at
`resolve_c13_predictor` for backend auto-selection, or reimplement `from_database`/
`from_table_file` on top of the resolver to keep a single construction path.

### IN-04: Generic `except Exception` in resolver-error CLI handlers can mask unrelated failures

**File:** `src/lucy_ng/cli/lsd.py:274-278` and `src/lucy_ng/cli/predict.py:76-80`
**Issue:** Both CLIs wrap `resolve_c13_predictor(...)` in `except Exception as e:` and
emit `Error: {e}`. The resolver itself only raises `RuntimeError` for the no-backend
case, but `from_database`/`from_table_file` can surface lower-level errors (corrupt DB,
malformed JSON). Catching bare `Exception` here is acceptable for a CLI boundary, but a
genuinely unexpected programming error (e.g. an `AttributeError` from a future refactor)
would be silently reported as a user-facing "Error:" with exit 1 rather than surfacing a
traceback. Low severity; consistent with surrounding CLI style.
**Fix (optional):** Narrow to `except (RuntimeError, OSError, ValueError) as e:` or let
truly unexpected exceptions propagate, so genuine bugs are not disguised as user errors.

---

_Reviewed: 2026-06-23_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
