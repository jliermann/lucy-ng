---
phase: 87-final-identity-verification-gate
plan: 03
subsystem: verification-tooling
tags: [identity, cli, gap-closure, reachability, rdkit, dereplication, d-05]
requires:
  - "scripts/verify_case_solution.py 87-01 identity core (derive_identity + verdict logic)"
  - "DatabaseFinder.find_derep_database() (src/lucy_ng/database/finder.py)"
  - "RDKit (Chem.MolToInchiKey, Chem.MolToSmiles)"
  - "Click CLI group (src/lucy_ng/cli/main.py)"
provides:
  - "lucy_ng.identity — installed, importable deterministic identity core (derive_identity, check_identity_result, _name_match, _normalize_name, _resolve_db_path)"
  - "lucy identify CLI subcommand (--smiles / --reported-name / --database / --format json), reachable from any working directory"
  - "scripts/verify_case_solution.py check-identity as a thin adapter over the shared core (back-compat)"
affects:
  - "CASE solution-analyst (IDENT-01) and binding gate (IDENT-02) — can now call `lucy identify` at runtime from an NMR data dir"
  - "tests/test_verify_case_identity.py (repointed to lucy_ng.identity)"
tech-stack:
  added: []
  patterns:
    - "Single-sourced library core consumed by both an installed Click command and a legacy script adapter (D-05)"
    - "Pure verdict function (check_identity_result) with no print / no sys.exit; I/O lives in the CLI/adapter shells"
    - "--format json via click.Choice(['text','json']) mirroring dereplicate/predict"
key-files:
  created:
    - "src/lucy_ng/identity.py"
    - "src/lucy_ng/cli/identify.py"
    - "tests/test_cli_identify.py"
  modified:
    - "src/lucy_ng/cli/main.py"
    - "scripts/verify_case_solution.py"
    - "tests/test_verify_case_identity.py"
decisions:
  - "The 87-01 identity logic moved VERBATIM into lucy_ng.identity (COCONUT dot-suffix regex, empty-name branch, filler tokens, two-path InChIKey-first/canonical-SMILES-fallback lookup, tolerant token-set matching) — delivery was broken, not the logic."
  - "lucy identify never hard-fails: always exits 0 (D-06); a name<->structure disagreement yields verdict 'tentative' + a non-null warning."
  - "Exactly one identity implementation (D-05): both lucy/cli/identify.py and scripts/verify_case_solution.py import lucy_ng.identity; the script is now a thin adapter."
  - "Strict-mypy convention applied to the new src module via dict[str, object] return types + one targeted ignore on RDKit's untyped MolToInchiKey; no runtime-logic change."
metrics:
  duration_min: 3
  tasks_completed: 3
  files_created: 3
  files_modified: 3
  completed: 2026-06-24
---

# Phase 87 Plan 03: lucy identify Delivery (GAP-87-A Closure) Summary

Made the Phase-87 deterministic identity tool reachable at CASE runtime by extracting the
correct 87-01 core into the installed `lucy_ng.identity` package module and exposing it through a
new installed `lucy identify` subcommand — with zero duplicated logic and full back-compat for
`scripts/verify_case_solution.py check-identity`.

## What Was Built

- **`src/lucy_ng/identity.py`** — the single shared identity core. `derive_identity`,
  `_resolve_db_path`, `_normalize_name`, `_synonym_token_sets`, `_name_match`, and the
  `_COCONUT_ACCESSION_RE` / `_NAME_FILLER_TOKENS` constants were moved verbatim from the script.
  Added a new pure `check_identity_result(smiles, reported_name=None, db_path=None) -> dict` that
  holds the four-verdict logic (confirmed / confirmed-structure / tentative / novel) but returns
  the dict instead of printing or calling `sys.exit`. The module imports no argparse/click/sys.
- **`src/lucy_ng/cli/identify.py`** — a `lucy identify` Click command (`--smiles`,
  `--reported-name`, `--database`/`-d`, `--format text|json`) that imports and adapts
  `check_identity_result`. Always exits 0 (D-06). No identity logic of its own.
- **`src/lucy_ng/cli/main.py`** — registered `identify` (`cli.add_command(identify)` + import +
  docstring line).
- **`scripts/verify_case_solution.py`** — thinned: the moved core was deleted and replaced with
  `from lucy_ng.identity import …`; `_check_identity` now wraps `check_identity_result`. The legacy
  positional aromatic-ring/formula mode is untouched.
- **Tests** — `tests/test_verify_case_identity.py` repointed to `lucy_ng.identity` (the
  empty-name monkeypatch test now patches and calls the package directly); new
  `tests/test_cli_identify.py` exercises the command via `CliRunner` (JSON schema, invalid SMILES,
  text smoke, plus DB-guarded CASE5 indigo-vs-isoindigo and CASE4 chamazulene cases).

## Verification

- `cd /tmp && lucy identify --smiles 'CCO' --format json` → exit 0, JSON carries
  `derived.inchi_key` + `verdict` (GAP-87-A: runtime-reachable from outside the repo).
- `lucy --help` lists `identify`.
- `grep -c "def derive_identity" scripts/verify_case_solution.py` → 0; script imports the core.
- `pytest tests/test_verify_case_identity.py tests/test_cli_identify.py tests/test_verify_case_solution.py` → 27 passed (DB present locally; DB-guarded cases skip cleanly when absent).
- `ruff check` clean on all touched src/test files; `mypy src/lucy_ng` clean on `identity.py` and `cli/identify.py`.
- Back-compat: `scripts/verify_case_solution.py check-identity --smiles 'CCO'` exit 0; legacy positional `<merged_smi> <formula>` exit 0.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Strict-mypy typing on the new installed module**
- **Found during:** Task 1
- **Issue:** `mypy src/lucy_ng` runs strict on `packages=["lucy_ng"]`. The verbatim-moved code used bare `dict` return types and an untyped `Chem.MolToInchiKey` call, which the script (under `scripts/`, not type-checked) tolerated but the installed module does not.
- **Fix:** Annotated the three identity functions as `-> dict[str, object]`, added `# type: ignore[no-untyped-call]` on the RDKit `MolToInchiKey` call, and narrowed `derived.get("name")` to `str | None` before passing to `_name_match`. No runtime-logic change.
- **Files modified:** `src/lucy_ng/identity.py`
- **Commit:** 2549eb5

**2. [Rule 3 - Blocking] Import-block ordering in main.py**
- **Found during:** Task 2
- **Issue:** Inserting the `identify` import made ruff (`I001`) flag the whole CLI import block (a pre-existing `predict`/`pylsd` mis-order surfaced).
- **Fix:** `ruff check --fix` reordered the block; the inserted import is alphabetical.
- **Files modified:** `src/lucy_ng/cli/main.py`
- **Commit:** 648f62c

## Self-Check: PASSED

- FOUND: src/lucy_ng/identity.py
- FOUND: src/lucy_ng/cli/identify.py
- FOUND: tests/test_cli_identify.py
- FOUND commit: 2549eb5 (Task 1)
- FOUND commit: 648f62c (Task 2)
- FOUND commit: d04aaa7 (Task 3)
