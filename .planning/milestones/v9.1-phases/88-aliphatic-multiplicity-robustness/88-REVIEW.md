---
phase: 88-aliphatic-multiplicity-robustness
reviewed: 2026-06-25T10:25:37Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - src/lucy_ng/cli/pick.py
  - tests/test_cli_pick.py
findings:
  critical: 0
  warning: 2
  info: 1
  total: 3
status: issues_found
---

# Phase 88: Code Review Report

**Reviewed:** 2026-06-25T10:25:37Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed the single executable-code change in Phase 88: the `_detect_multiplicity_edited(data) -> (bool, int)` helper added to `src/lucy_ng/cli/pick.py` and surfaced as `multiplicity_edited` + `negative_crosspeak_count` in `lucy pick hsqc --format json`, plus its tests in `tests/test_cli_pick.py`. The 88-02/88-03 CASE-agent markdown edits are explicitly out of code-review scope.

**Overall assessment: solid, low-risk change.** The port is faithful to the proven `pick_1d` `negative_detected` detector — same `-0.05 * max_abs` threshold, same strict `<`, same `np.min`/`np.max(np.abs(...))` reductions. The empty (`data.size == 0`) and all-zero (`max_abs == 0.0`) guards are correct and degrade to the safe `(False, 0)` default without raising. `pick_2d`/`pick_hmbc` and the existing JSON contracts are untouched (the two new keys are purely additive, backward compatible). The new helper is mypy-clean; the only ruff E501 errors on the file (lines 196, 258) are pre-existing in the base commit and not introduced by this change. All 21 tests in `tests/test_cli_pick.py` pass.

Two robustness gaps remain, both centered on NaN/inf inputs, and one documentation-accuracy issue. None are blockers given the reader does not currently emit NaN/inf, but they are worth recording because the docstring overclaims the guard.

## Warnings

### WR-01: NaN/inf in `data` silently flips a multiplicity-edited HSQC to `(False, 0)` — boolean and count disagree

**File:** `src/lucy_ng/cli/pick.py:43-48`
**Issue:**
The boolean and the count are computed from two *different* reductions that disagree under non-finite values:
- `multiplicity_edited = bool(np.min(data) < cutoff)` (line 47) — relies on `np.min`.
- `negative_crosspeak_count = int(np.count_nonzero(data < cutoff))` (line 48) — relies on an element-wise predicate.

Two concrete failure modes (both reproduced):
1. **A single NaN pixel alongside genuine negative cross-peaks.** `np.min(data)` returns `nan`, and `nan < cutoff` is `False`, so a genuinely multiplicity-edited HSQC is reported `multiplicity_edited=False, negative_crosspeak_count=0` — the real CH2 negatives are masked. (`count_nonzero(data < cutoff)` would also miss them here because the NaN does not affect that predicate, but the point is the *boolean is driven by `np.min` and is wrong*.)
2. **A single `inf` pixel.** `max_abs = float(np.max(np.abs(data)))` becomes `inf`, so `cutoff = -inf`, and no finite negative is ever `< -inf`. Result: `(False, 0)` even with strong real negative cross-peaks.

Because `multiplicity_edited=False` is interpreted downstream as "sign-ambiguous → cannot use HSQC sign to resolve CH2", a NaN/inf-corrupted but genuinely edited HSQC would be silently demoted, which is precisely the multiplicity-model failure class this phase exists to harden against.

This weakness is *inherited verbatim* from the proven `pick_1d` path (`pick.py:90-91`), which has the same unguarded `np.min`/`np.max` — so the port is faithful, and the reader does not currently produce NaN/inf from Bruker binary data, which is why this is a WARNING and not a BLOCKER. But the helper is presented as the deterministic, safe detector, so it should be the one that closes the gap.

**Fix:** Make the boolean derive from the same predicate as the count (so they can never disagree) and screen non-finite values explicitly:
```python
if data.size == 0:
    return False, 0
finite = data[np.isfinite(data)]
if finite.size == 0:
    return False, 0
max_abs = float(np.max(np.abs(finite)))
if max_abs == 0.0:
    return False, 0
cutoff = -0.05 * max_abs
negative_crosspeak_count = int(np.count_nonzero(finite < cutoff))
multiplicity_edited = negative_crosspeak_count > 0
return multiplicity_edited, negative_crosspeak_count
```
This keeps the boolean and count consistent by construction and treats NaN/inf as "ignore that pixel" rather than "poison the whole detection."

### WR-02: Docstring/comment claim a NaN/zero-max guard the code does not implement

**File:** `src/lucy_ng/cli/pick.py:35-40`
**Issue:**
The docstring states the helper "Degrades to the safe default `(False, 0)` on empty/all-zero data without raising," and the inline comment (lines 39-40) says "never call `np.min` on an empty array or divide by a zero max." There is no division anywhere in the function (the `max_abs == 0.0` check guards a *multiply* by `cutoff`, not a divide), and there is no guard for NaN/inf at all — the function relies on IEEE comparison semantics (`nan < x == False`) by accident, not by design (see WR-01). The comment is therefore both inaccurate ("divide by a zero max") and incomplete (implies non-finite inputs are handled when they are not). This is a maintainability hazard: a future reader will trust the stated invariant and may not re-derive the NaN edge case.

**Fix:** After applying WR-01, update the comment to describe what the code actually does, e.g. "Empty / all-non-finite / all-zero data degrades to `(False, 0)`; non-finite pixels are excluded from the threshold computation." Remove the "divide by a zero max" phrasing since there is no division.

## Info

### IN-01: No test covers the `max_abs == 0.0` non-empty branch or non-finite inputs

**File:** `tests/test_cli_pick.py:206-231`
**Issue:**
The unit tests cover `true` (line 209), `false_on_zeros` via a non-empty all-zero array (line 222 — this exercises the `max_abs == 0.0` branch indirectly, good), and `empty` (line 228). There is no test for NaN/inf-containing data. Given the WR-01 fix changes that behavior, a regression test pinning the intended "non-finite pixels are ignored, real negatives still detected" semantics would lock it in. Also, `test_detect_multiplicity_edited_false_on_zeros` and `test_..._empty` both assert the same `(False, 0)` outcome — they verify the two distinct early-return branches (`data.size == 0` vs `max_abs == 0.0`), which is genuine coverage, but the relationship is not obvious from the names.

**Fix:** Add, after the WR-01 fix:
```python
def test_detect_multiplicity_edited_nan_with_real_negative(self) -> None:
    """A NaN pixel must not mask genuine negative cross-peaks."""
    data = np.zeros((64, 256))
    data[10, 50] = 1000.0
    data[30, 120] = -1000.0   # genuine edited CH2
    data[5, 5] = np.nan       # single corrupt pixel
    edited, count = _detect_multiplicity_edited(data)
    assert edited is True
    assert count >= 1
```

---

_Reviewed: 2026-06-25T10:25:37Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
