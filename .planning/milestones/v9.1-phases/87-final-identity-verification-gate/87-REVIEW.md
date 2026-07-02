---
phase: 87-final-identity-verification-gate
reviewed: 2026-06-24T00:00:00Z
depth: deep
files_reviewed: 6
files_reviewed_list:
  - scripts/verify_case_solution.py
  - tests/test_verify_case_identity.py
  - src/lucy_ng/identity.py
  - src/lucy_ng/cli/identify.py
  - src/lucy_ng/cli/main.py
  - tests/test_cli_identify.py
findings:
  critical: 1
  warning: 3
  info: 3
  total: 7
status: issues_found
---

# Phase 87: Code Review Report

**Reviewed:** 2026-06-23 (original 87-01) / 2026-06-24 (gap-closure 87-03/87-04)
**Depth:** deep (cross-checked against live dereplication DB schema + content)
**Files Reviewed:** 6
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
trivial name** (every COCONUT name is an accession).

**Status (2026-06-24): FIXED in gap-closure 87-03.** The moved core
`src/lucy_ng/identity.py:33` now uses `re.compile(r"^CNP\d+(?:\.\d+)?$",
re.IGNORECASE)`; regression `test_dotsuffixed_coconut_accession_is_recognised`
and DB-guarded `test_dotsuffixed_coconut_row_is_structure_only` lock it.

### WR-02: `_normalize_name` leaks accession tokens for dot-suffixed names — pollutes name-match comparison

**File:** `scripts/verify_case_solution.py:215-235` and `:238-251`
**Issue:** Both `_normalize_name` and `_synonym_token_sets` drop a synonym only
if `_COCONUT_ACCESSION_RE.match(synonym)` is true; the un-suffixed regex did not
match `CNP0220816.1`, so the accession leaked into the token set.

**Status (2026-06-24): FIXED in gap-closure 87-03.** Same regex fix resolves it;
`_normalize_name("CNP0220816.1") == set()` is asserted by
`test_dotsuffixed_coconut_accession_is_recognised`
(`src/lucy_ng/identity.py:179`, `:195`).

### WR-03: nmrshiftdb hit with empty stored name yields `confidence: "confirmed"` and a misleading "structure not in DB" warning

**File:** `scripts/verify_case_solution.py:198-211`, `:299-303`
**Issue:** ~7,861 nmrshiftdb rows have an empty `name`; an empty-name hit was
labelled `confirmed` and the mismatch warning falsely claimed the structure was
"not in DB".

**Status (2026-06-24): FIXED in gap-closure 87-03.** `src/lucy_ng/identity.py:156-161`
now does `stripped = name.strip() if name else ""; if not stripped or
_COCONUT_ACCESSION_RE.match(stripped): confirmed-structure`, and
`check_identity_result` (`:268-272`) emits `"none (structure in DB but no
trivial name stored)"` for a matched-but-nameless hit. Locked by
`test_empty_name_match_warns_in_db_not_absent`.

## Info

### IN-01: `_check_smiles` re-parses the SMILES already validated by `_parse_top3`

**File:** `scripts/verify_case_solution.py:78`
**Issue:** `_parse_top3` calls `Chem.MolFromSmiles(smiles)` to validate, discards
the mol, and `_check_smiles` parses the same string again. Harmless,
pre-existing. **(Unchanged by gap-closure; legacy mode untouched.)**

### IN-02: `import os` inside the exception fallback in `_resolve_db_path`

**File:** `src/lucy_ng/identity.py:55` (moved from script)
**Issue:** `os` is imported lazily inside the `except` block (`# pragma: no
cover`). Works; minor style point. Carried over verbatim in the move.

### IN-03: Test helper module-import shim removed in gap-closure

**File:** `tests/test_verify_case_identity.py`
**Status (2026-06-24): RESOLVED.** The RED-phase wrapper is gone; the test now
imports `derive_identity` / `check_identity_result` directly from
`lucy_ng.identity` (lines 38-40). Cleanup complete.

---

## Gap-Closure Review (87-03 / 87-04)

**Scope:** commits `2549eb5`, `648f62c`, `d04aaa7` (src), `602f54c`, `8cb6ef5`
(agent `.md` prompt edits — not reviewed as code). Diff base `283b06a..HEAD`.

### Move integrity — VERIFIED FAITHFUL (D-05: one implementation)

A line-level diff of the old script's identity core (`283b06a:scripts/verify_case_solution.py`
lines 36-328) against `src/lucy_ng/identity.py` shows the logic is **byte-identical**
except for three deliberate, behaviour-neutral edits:

1. Type-annotation tightening: `dict` → `dict[str, object]` (`identity.py:75`, `:145`, `:224`).
2. A `# type: ignore[no-untyped-call]` on `Chem.MolToInchiKey` (`identity.py:105`).
3. Refactor of `_check_identity(args)` (print + `sys.exit(0)`) into the **pure**
   `check_identity_result(smiles, reported_name, db_path)` (`identity.py:224-287`)
   that returns the dict and neither prints nor exits — plus a defensive
   `isinstance(derived_name, str)` guard before `_name_match` (`identity.py:254-256`).

The four focus invariants survived the move UNCHANGED and now carry the
WR-01/02/03 fixes:

- COCONUT regex `^CNP\d+(?:\.\d+)?$` — `identity.py:33`
- empty-name → confirmed-structure branch — `identity.py:156-161`
- `_NAME_FILLER_TOKENS = frozenset({"dye","the","a","an","of"})` — `identity.py:36` (identical)
- tolerant token-set `_name_match` (whole-token subset/equality) — `identity.py:204-221`

**Exactly one implementation now.** `scripts/verify_case_solution.py:31-38`
imports the six symbols from `lucy_ng.identity` (with `# noqa: F401` re-export for
back-compat) and contains **zero** duplicate identity logic — `_resolve_db_path`,
`derive_identity`, `_normalize_name`, `_synonym_token_sets`, `_name_match`, and the
verdict logic are all gone from the script. The adapter retains only legacy
positional helpers (`_parse_top3`, `_check_smiles`) and a thin `_check_identity`
that calls `check_identity_result` then `sys.exit(0)`.

**SQL still parameterized** — `identity.py:121-132`, `?` placeholders, RO `file:`
URI connection. No injection surface introduced by the move.

**No import-cycle risk** — `lucy_ng.identity` imports only `re`, `sqlite3`,
`pathlib`, and `rdkit.Chem` at module top. `DatabaseFinder` is imported lazily
**inside** `_resolve_db_path` (`identity.py:51`), so importing the module does
not pull in heavy package internals. `python -c "import lucy_ng.identity;
import lucy_ng.cli.identify"` succeeds with no cycle.

**JSON schema parity** — verified empirically. `lucy identify --format json`
emits exactly `{mode, reported_name, derived, name_match, verdict, warning}`
with `derived = {canonical_smiles, confidence, inchi_key, matched, name,
source}` — identical to the old `check-identity` output. `verdict` ∈
{confirmed, confirmed-structure, tentative, novel}.

**Back-compat** — legacy `verify_case_solution.py <merged_smi> <formula>` runs
green (exit 0, keys `{pass, formula, top_n_checked, checks}`); `check-identity`
subprocess path still parsed by `tests/test_verify_case_identity.py`.

**`lucy identify` registered** — `cli/main.py:12,53` imports and `add_command`s
`identify`; help text line 36 present.

**Tests** — `tests/test_cli_identify.py` (8) + `tests/test_verify_case_identity.py`
(repointed): **19 passed** locally. mypy on the two new files: **0 errors in
identity.py / cli/identify.py** (the 108 project-wide errors are pre-existing in
unrelated modules: database.py, ranker.py, predict.py, lsd.py, pylsd.py).

### Critical Issues

#### CR-01: Corrupt / non-DB `--database` file (or partially-downloaded bundled DB) raises an uncaught `sqlite3.DatabaseError`, crashing `lucy identify` with a traceback and nonzero exit — violates the D-06 "always exits 0" contract

**File:** `src/lucy_ng/identity.py:117-134` (raises at `:121`); reached via
`src/lucy_ng/cli/identify.py:66`

**Issue:** `--database` is declared `click.Path(exists=True)`
(`cli/identify.py:37`), which validates only that the path **exists**, not that
it is a valid SQLite database. `_resolve_db_path` returns any existing path
unchecked (`identity.py:46-48`). `sqlite3.connect(...uri=True)` is lazy and
succeeds, but the first `con.execute(...)` at `identity.py:121` raises
`sqlite3.DatabaseError: file is not a database`. Nothing in `derive_identity`,
`check_identity_result`, or the CLI catches it, so the exception propagates to
the top and the command **crashes with a Python traceback and a nonzero exit
code**. Reproduced:

```
$ lucy identify --smiles CCO --database /tmp/not_a_db.smi --format json
Traceback (most recent call last):
  ...
  File ".../identity.py", line 121, in derive_identity
    row = con.execute(
sqlite3.DatabaseError: file is not a database
```

This is a real, reachable failure, not theoretical:
- An operator pointing `--database` at the wrong file (e.g. a `.smi`, a `.txt`,
  or a half-downloaded `.db`) gets a stack trace instead of a graceful verdict.
- The **auto-resolve** path is equally exposed: if the bundled
  `lucy-ng-derep.db` is present but **truncated/corrupt** (a known failure mode
  for a ~830 MB download — see CLAUDE.md "Database Reference"), `DatabaseFinder`
  returns the path and the same uncaught error fires inside a CASE run.

The module docstring and `cli/identify.py:11,60` explicitly promise D-06
("identity never hard-fails — always exits 0"). The only handled DB failure is
**missing** DB (`identity.py:108-115` → `db_unavailable`); a **corrupt/invalid**
DB is not handled. `test_identify_invalid_smiles_exits_zero` only covers bad
SMILES, never a bad DB, so the gap is unguarded by tests.

**Fix:** wrap the lookup in a try/except for `sqlite3.Error` and degrade to the
same graceful "DB unavailable" result instead of propagating:

```python
# identity.py — in derive_identity, replacing lines 117-142
try:
    con = sqlite3.connect(f"file:{resolved_db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            "SELECT name, source FROM compounds "
            "WHERE inchi_key = ? AND inchi_key != '' LIMIT 1",
            (inchi_key,),
        ).fetchone()
        if row is None:
            row = con.execute(
                "SELECT name, source FROM compounds "
                "WHERE smiles = ? AND smiles != '' LIMIT 1",
                (canonical_smiles,),
            ).fetchone()
    finally:
        con.close()
except sqlite3.Error as exc:
    return {
        "matched": False,
        "inchi_key": inchi_key,
        "canonical_smiles": canonical_smiles,
        "confidence": "novel",
        "db_unavailable": True,
        "error": f"db error: {exc}",
    }
```

Add a regression test: write a few bytes of non-SQLite content to a tmp file,
invoke `lucy identify --smiles CCO --database <that file> --format json`, and
assert `exit_code == 0` with `verdict == "novel"` and `db_unavailable is True`.

---

_Reviewed: 2026-06-23 (original) / 2026-06-24 (gap-closure)_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
