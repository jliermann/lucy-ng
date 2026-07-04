---
phase: 91-api-endpoints-depictions-and-static-frontend
reviewed: 2026-07-04T00:00:00Z
depth: deep
files_reviewed: 7
files_reviewed_list:
  - src/lucy_ng/webview/app.py
  - src/lucy_ng/webview/routers/__init__.py
  - src/lucy_ng/webview/routers/status.py
  - src/lucy_ng/webview/routers/log.py
  - src/lucy_ng/webview/routers/structures.py
  - src/lucy_ng/webview/depiction.py
  - src/lucy_ng/webview/static/index.html
  - pyproject.toml
findings:
  critical: 3
  warning: 2
  info: 1
  total: 6
status: resolved
resolved: 2026-07-04
resolution_commit: eb638d2
resolution_note: >-
  CR-01, CR-02, CR-03 (blockers) and WR-02 fixed with regression tests in
  commit eb638d2. WR-01 (extra tier-3 status "source" key) and IN-01 (no static
  file existence check) accepted as non-blocking nits; left as-is.
---

# Phase 91: Code Review Report

**Reviewed:** 2026-07-04
**Depth:** deep
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the full Phase 91 deliverable: three FastAPI routers (status, log, structures),
the RDKit depiction module, the single-file vanilla-JS frontend, the `create_app()`
factory extension, and the pyproject.toml hatch artifact entry.

The architecture is sound — WV-08 import isolation is correctly implemented, all read
paths include try/except guards, the SVG index endpoint validates `i` as an integer
(no path traversal), and the frontend uses `textContent` throughout for untrusted content.
No security vulnerabilities were found.

Three correctness bugs survive into the shipped code:

1. A `None`-rank TypeError in the ranked-solutions sort silently discards all ranked data
   when any solution carries `"rank": null`.
2. `PrepareMolForDrawing` can raise a `KekulizeException` for certain aromatic SMILES,
   propagating to an HTTP 500 and violating the explicit "never 500" invariant.
3. A JavaScript `|| null` falsy-coercion bug causes perpetual per-tick SVG re-fetches
   for any structure entry with an empty SMILES string.

The test suite does not cover any of these paths — all three fixture datasets use
non-null ranks, non-exotic SMILES, and non-empty SMILES strings.

---

## Critical Issues (BLOCKERs)

### CR-01: `None`-rank in solutions silently drops entire ranked tier

**File:** `src/lucy_ng/webview/routers/structures.py:112`

**Issue:** The sort key `lambda s: s.get("rank", 999999)` uses `999999` as the fallback
only when the key is **absent**. When a solution entry has `"rank": null` (valid JSON
from a partially-ranked run), `s.get("rank", 999999)` returns `None` — and Python 3
raises `TypeError: '<' not supported between instances of 'NoneType' and 'int'` when
`None` is compared with an integer during sort. This `TypeError` is caught by the outer
`except (..., TypeError, ...)` on line 125, silently discarding the entire ranked tier
and falling back to unranked solutions from `iteration_NN/solutions.smi`. Valid ranked
data is displayed as if no ranking exists.

The test fixtures always provide integer ranks, so this path is untested.

**Fix:**
```python
solutions_sorted = sorted(
    solutions,
    key=lambda s: s.get("rank") if s.get("rank") is not None else 999999,
)
```
This treats absent-key (`None` default) and explicit-null identically as `999999`,
preserving sort stability without TypeError.

---

### CR-02: `PrepareMolForDrawing` can raise, causing HTTP 500

**File:** `src/lucy_ng/webview/depiction.py:50`

**Issue:** The docstring states "Never raises." but the claim is not enforced. After a
successful `Chem.MolFromSmiles()` call, `PrepareMolForDrawing(mol)` internally calls
`Chem.Kekulize`. RDKit raises `rdkit.Chem.rdchem.KekulizeException` (a C++ exception
that propagates as a Python exception) for certain aromatic systems that parse cleanly
but cannot be kekulized for 2D depiction — for example, some nitrogen-containing fused
heteroaromatics that arrive via LSD output. The exception propagates uncaught through
`get_structure_svg` in `structures.py` to FastAPI, which returns HTTP 500. This violates
the "all file-read paths must degrade to HTTP 200, never 500" invariant stated in the
Phase 91 focus areas.

**Fix:**
```python
def render_smiles(smiles: str, width: int = 300, height: int = 300) -> str | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    try:
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        opts = drawer.drawOptions()
        opts.addAtomIndices = False          # type: ignore[assignment]
        opts.addStereoAnnotation = True      # type: ignore[assignment]
        PrepareMolForDrawing(mol)
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        return drawer.GetDrawingText()
    except Exception:
        return None  # caller substitutes placeholder_svg()
```

---

### CR-03: Falsy-SMILES `|| null` coercion causes perpetual SVG re-fetch

**File:** `src/lucy_ng/webview/static/index.html:331`

**Issue:** The de-duplication guard is:
```javascript
if (smiles !== (lastSmiles[idx] || null)) {
```
`lastSmiles[idx] || null` evaluates the cached value through JavaScript's falsy
coercion. When `smiles` is `""` (empty string, which occurs in Tier 1 when a solution
entry omits the `"smiles"` key), the first tick sets `lastSmiles[idx] = ""`. On
subsequent ticks `"" || null` evaluates to `null` (empty string is falsy), so
`"" !== null` is always `true` — the SVG endpoint is re-fetched on every 3-second tick
for every such tile, forever. The `?t=<timestamp>` cache-buster ensures the browser
honours each re-fetch, producing unnecessary network traffic and SVG flicker.

An empty-SMILES structure also renders as a placeholder (RDKit parses `""` as `null`),
so the re-fetch never produces a different result — it is purely wasted work.

**Fix:** Remove the `|| null` coercion entirely; direct strict-equality comparison is
correct and simpler:
```javascript
if (smiles !== lastSmiles[idx]) {
```
On first render `lastSmiles[idx]` is `undefined`; `smiles !== undefined` is `true`
for any SMILES value including `""`, so the initial fetch fires correctly.

---

## Warnings

### WR-01: Tier 3 response schema includes spurious `source` field

**File:** `src/lucy_ng/webview/routers/status.py:207-213`

**Issue:** `_status_from_progress_md` returns a dict with an extra
`"source": "progress_md_fallback"` key not present in the Tier 1, 2, or 4 responses.
The `/api/status` schema is documented as `{state, iteration, active_phase, elapsed_s}`.
The extra key makes the Tier 3 response structurally inconsistent with the other tiers,
and `warn_return_any = true` mypy strict mode will flag the untyped `Any` return more
severely once callers start checking specific fields.

**Fix:** Remove the `"source"` key from the returned dict, or add it as an
`Optional[str]` field to all four tiers (e.g., `"source": None` for Tiers 1/2/4,
`"source": "progress_md_fallback"` for Tier 3) and add `source: str | None` to the
response TypedDict if one is introduced.

---

### WR-02: `elapsed_s` can be negative; no guard applied

**File:** `src/lucy_ng/webview/routers/status.py:176-177`

**Issue:**
```python
now_epoch = int(datetime.now(tz=timezone.utc).timestamp())
elapsed_s = now_epoch - run_start_epoch
```
If the system clock steps backwards (NTP correction, VM resume after suspend) between
when `run_start_epoch` was recorded and when the endpoint is polled, `elapsed_s` is
negative. The frontend passes this directly to `formatElapsed`:
```javascript
// formatElapsed(-5) → "-5s" (Math.floor(-5/3600)=0, Math.floor(-5/60)=0, sec=-5)
```
The status bar shows a nonsensical negative elapsed time.

**Fix:** Clamp to zero:
```python
elapsed_s = max(0, now_epoch - run_start_epoch)
```

---

## Info

### IN-01: No existence check for `_static_file` at `create_app()` time

**File:** `src/lucy_ng/webview/app.py:59`

**Issue:** `_static_file = Path(__file__).parent / "static" / "index.html"` is
computed but not validated. On an editable install without running `hatch build`, the
`static/` directory is present in the source tree (it is tracked in git), so this is
not a practical problem. However, on a wheel install where the artifact glob
`src/lucy_ng/webview/static/*` was silently not matched (e.g., due to a hatch
regression or a manually assembled wheel), every `GET /` silently returns HTTP 404 from
Starlette without any log line indicating why. A startup assertion or `logger.warning`
would ease debugging.

**Fix (optional):** Log a warning at `create_app()` time if the file is absent:
```python
if not _static_file.exists():
    import logging
    logging.getLogger(__name__).warning(
        "static/index.html not found at %s — GET / will return 404", _static_file
    )
```

---

_Reviewed: 2026-07-04_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
