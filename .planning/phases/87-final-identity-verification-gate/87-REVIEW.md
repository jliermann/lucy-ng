---
phase: 87-final-identity-verification-gate
reviewed: 2026-06-23T00:00:00Z
depth: deep
files_reviewed: 2
files_reviewed_list:
  - scripts/verify_case_solution.py
  - tests/test_verify_case_identity.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 87: Code Review Report

**Reviewed:** 2026-06-23
**Depth:** deep (cross-checked against live dereplication DB schema + content)
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Phase 87 adds a `check-identity` subcommand and a `derive_identity()` core to
`scripts/verify_case_solution.py`, gating an analyst-reported trivial name
against a tool-derived structural identity (InChIKey + canonical SMILES) with a
two-path DB lookup. The review focus areas are mostly clean:

- **SQL parameterization** — correct. Both queries use `?` placeholders with a
  parameter tuple; the SMILES/InChIKey are never string-interpolated. No
  injection surface. (lines 175-186)
- **Two-path lookup** — verified against the live DB. The partitioning the code
  assumes is real: `coconut` rows have `smiles` populated and `inchi_key`
  empty; `nmrshiftdb` rows have `inchi_key` populated and `smiles` empty. Both
  queries guard against the empty-column partition with `!= ''`, so Path 1
  cannot false-hit a coconut row on `inchi_key = ''` and Path 2 cannot
  false-hit an nmrshiftdb row on `smiles = ''`. Logic is sound.
- **Malformed SMILES** — `Chem.MolFromSmiles` returning `None` is handled at
  line 154-156 (returns `matched: False, error, confidence: novel`); no crash.
  Verified by `test_invalid_smiles_returns_novel`.
- **Backward compatibility** — legacy positional `<merged_smi> <formula>` mode
  is byte-unchanged (`_parse_top3`, `_check_smiles`, aromatic/formula checks,
  exit 0/1 semantics all intact). The subcommand is dispatched only on the
  literal first arg `check-identity` (line 328), so the two-positional legacy
  form is unaffected.
- **Exit-code semantics (D-06)** — `_check_identity` calls `sys.exit(0)`
  unconditionally (line 316). No path hard-fails on a name mismatch. Correct.
- **DB resource handling** — `con.close()` is in a `finally` (line 187-188); no
  leak. Missing-DB is guarded (line 162-169, returns `db_unavailable`).
- **Substring false-pass** — `_name_match` requires whole-token subset/equality,
  so `"in"` does not match `"indigo"`. Verified by `test_no_false_substring_match`.

However, the COCONUT-accession handling does not survive contact with the real
data: the majority of COCONUT names carry a version suffix that the accession
regex does not match, producing wrong verdicts. Details below.

## Warnings

### WR-01: COCONUT accession regex misses the `.N` version suffix — majority of COCONUT hits mislabelled as "confirmed"

**File:** `scripts/verify_case_solution.py:33`, used at `:207` and `:229`/`:245`
**Issue:** `_COCONUT_ACCESSION_RE = re.compile(r"^CNP\d+$", ...)` matches
`CNP0220816` but NOT the suffixed forms `CNP0220816.1`, `CNP0220816.2`.
Confirmed against the live DB: of 895,099 COCONUT rows, **489,191 (55%)** have
dot-suffixed names like `CNP0220816.1`, and **0 COCONUT rows have a real
trivial name** (every COCONUT name is an accession). Consequences when a
dot-suffixed COCONUT structure is hit via Path 2 (the common case):

- `derive_identity` falls into the `else` branch at line 210-211 and returns
  `confidence: "confirmed"` with `name: "CNP0220816.1"`, instead of the
  intended `confidence: "confirmed-structure"` / `trivial_name_confirmed:
  False`. The bare accession is presented as a confirmed trivial name.
- In `check-identity`, the verdict for such a hit becomes `confirmed`, and if a
  reported name is supplied it is gated against the accession token-set (see
  WR-02), so a correct trivial name on a known COCONUT structure is reported as
  `tentative` with a warning that the "tool-derived identity" is `CNP0220816.1`.

Empirically reproduced: `derive_identity(<dot-suffixed coconut smiles>)` →
`matched=True, confidence='confirmed', name='CNP0220816.1'`. The existing test
`test_coconut_found_via_smiles_fallback` only exercises a `LIMIT 1` row that
happens to be a non-suffixed `CNP…`, so it passes and masks the defect.

**Fix:** widen the pattern to accept the optional version suffix, and apply it
consistently in `derive_identity`, `_normalize_name`, and `_synonym_token_sets`:
```python
_COCONUT_ACCESSION_RE = re.compile(r"^CNP\d+(?:\.\d+)?$", re.IGNORECASE)
```
Add a regression test that picks a `name LIKE 'CNP%.%'` COCONUT row and asserts
`confidence == "confirmed-structure"` and `trivial_name_confirmed is False`.

### WR-02: `_normalize_name` leaks accession tokens for dot-suffixed names — pollutes name-match comparison

**File:** `scripts/verify_case_solution.py:215-235` and `:238-251`
**Issue:** Both `_normalize_name` and `_synonym_token_sets` drop a synonym only
if `_COCONUT_ACCESSION_RE.match(synonym)` is true (lines 229, 245). Because that
regex (WR-01) does not match `CNP0220816.1`, the accession is NOT dropped;
instead the punctuation-substitution `re.sub(r"[,()'\-–—.]", " ", ...)` splits
it into tokens `{"cnp0220816", "1"}`. Verified:
`_normalize_name("CNP0220816.1") == {'1', 'cnp0220816'}`. These accession-derived
tokens then participate in `_name_match`, so the name gate compares a reported
trivial name against an accession fragment — guaranteeing a spurious `False`
(tentative) for any dot-suffixed COCONUT hit. This is a direct correctness
defect in the name<->structure gate that is the entire purpose of the phase.

**Fix:** fix the regex per WR-01 (the dropping then works). Defensively, also
consider dropping any token matching `^cnp\d+$` after tokenisation, in case
suffix formats vary.

### WR-03: nmrshiftdb hit with empty stored name yields `confidence: "confirmed"` and a misleading "structure not in DB" warning

**File:** `scripts/verify_case_solution.py:198-211`, `:299-303`
**Issue:** 7,861 nmrshiftdb rows have an empty `name` (verified against the live
DB). When such a structure is hit via Path 1, `name` is `""` (not `None`, and
the accession regex does not match `""`), so line 210-211 assigns
`confidence: "confirmed"` even though there is no trivial name to confirm — it
should be treated like the accession case (`confirmed-structure` /
`trivial_name_confirmed: False`). Additionally, if a reported name is supplied
for such a hit, `_check_identity` computes `name_match=False` (empty token set),
falls into the `tentative` branch (line 297), and emits a warning saying the
reported name "does not match tool-derived identity 'none (structure not in
DB)'" (line 299) — but the structure IS in the DB (`matched=True`). The message
is factually wrong and could mislead an operator into discarding a correct name.

**Fix:** treat an empty/whitespace name as a no-trivial-name hit:
```python
stripped = (name or "").strip()
if not stripped or _COCONUT_ACCESSION_RE.match(stripped):
    result["confidence"] = "confirmed-structure"
    result["trivial_name_confirmed"] = False
else:
    result["confidence"] = "confirmed"
```
And in `_check_identity`, derive the warning label from the actual hit state
(matched vs. structure-only) rather than a flat "structure not in DB" string.

## Info

### IN-01: `_check_smiles` re-parses the SMILES already validated by `_parse_top3`

**File:** `scripts/verify_case_solution.py:78`
**Issue:** `_parse_top3` calls `Chem.MolFromSmiles(smiles)` (line 58) to validate,
discards the mol, and `_check_smiles` parses the same string again (line 78).
Harmless and pre-existing (not introduced this phase), but redundant. Not a
correctness issue. Out of scope as a perf concern; noted only for hygiene.
**Fix:** optionally have `_parse_top3` return `(smiles, mol)` pairs.

### IN-02: `import os` inside the exception fallback in `_resolve_db_path`

**File:** `scripts/verify_case_solution.py:109`
**Issue:** `os` is imported lazily inside the `except` block. It works, but the
module already imports `sqlite3`, `json`, etc. at top level; a function-local
import in a rarely-taken branch is mildly surprising and is excluded from
coverage (`# pragma: no cover`). Minor style point.
**Fix:** move `import os` to the module top.

### IN-03: Test helper `derive_identity` wrapper / module-import shim is dead-code scaffolding now that the function exists

**File:** `tests/test_verify_case_identity.py:46-48`
**Issue:** The comment (lines 44-45) and the thin `derive_identity(*args,
**kwargs)` wrapper exist to keep the module collectable during the RED phase
before the function landed. The function now exists, so the wrapper adds an
extra indirection layer for no runtime benefit. Not a defect; cleanup only.
**Fix:** call `verify_case_solution.derive_identity` directly, or keep the alias
without the comment.

---

## Test-coverage gap (cross-cutting)

The three warnings above all survive the current test suite because no test
exercises a **dot-suffixed COCONUT name** (the 55% majority) or an
**empty-name nmrshiftdb hit**. `test_coconut_found_via_smiles_fallback` uses
`LIMIT 1`, which returns a non-suffixed accession and so passes. Recommend
adding the two targeted regression fixtures described in WR-01 and WR-03 before
relying on this gate for COCONUT/nmrshiftdb identity reporting.

---

_Reviewed: 2026-06-23_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
