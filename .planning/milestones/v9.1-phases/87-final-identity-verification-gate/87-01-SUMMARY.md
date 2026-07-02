---
phase: 87-final-identity-verification-gate
plan: 01
subsystem: verification-tooling
tags: [identity, dereplication, naming-hallucination, regression-gate, rdkit, sqlite]
requires:
  - "DatabaseFinder.find_derep_database() (src/lucy_ng/database/finder.py)"
  - "RDKit (Chem.MolToInchiKey, Chem.MolToSmiles)"
  - "bundled dereplication DB (data/reference/lucy-ng-derep.db, compounds table)"
provides:
  - "scripts/verify_case_solution.py:derive_identity() — deterministic InChIKey + canonical SMILES + two-path DB lookup"
  - "scripts/verify_case_solution.py check-identity subcommand — name<->structure gate (JSON + verdict + warning)"
  - "scripts/verify_case_solution.py:_normalize_name / _name_match — tolerant token-set name matching"
affects:
  - "CASE solution-analyst identity rendering (IDENT-03 consumers, skill-level wiring in a later plan/phase)"
tech-stack:
  added: []
  patterns:
    - "Complementary two-path DB lookup: InChIKey-first (nmrshiftdb) then canonical-SMILES fallback (coconut)"
    - "Tolerant token-set name comparison over ';'-split synonyms (no exact/substring matching)"
    - "Read-only parameterized sqlite3 (mode=ro, ? placeholders)"
    - "Subcommand routing that preserves a legacy positional CLI contract"
key-files:
  created:
    - "tests/test_verify_case_identity.py"
  modified:
    - "scripts/verify_case_solution.py"
decisions:
  - "name_match is tolerant token-set overlap over ';'-split synonyms, NOT exact equality or substring containment (catches CASE5 indigo<->isoindigo; no false-fail on the ';'-delimited DB name; 'in' does not match 'indigo')."
  - "check-identity ALWAYS exits 0 (D-06): a name<->structure mismatch downgrades to verdict 'tentative' + warning, never hard-fails; legacy default mode keeps 0/1 exit."
  - "Canonical SMILES uses bare Chem.MolToSmiles(mol) with default flags to byte-match the importer's stored canonicalization for the SMILES-fallback path."
  - "COCONUT-accession (^CNP\\d+) hits resolve to confidence 'confirmed-structure' (+ trivial_name_confirmed: false) since the structure is known but no human name is stored."
metrics:
  duration: ~3 min
  completed: "2026-06-23"
  tasks: 2
  files: 2
  commits: 3
---

# Phase 87 Plan 01: Final Identity-Verification Gate Summary

Added a deterministic, tool-derived identity core (`derive_identity`) plus an independent name↔structure gate (`check-identity`) to `scripts/verify_case_solution.py`, eliminating the parametric naming-hallucination failure class (CASE4 chamazulene, CASE5 indigo↔isoindigo) by deriving identity from the solved structure and flagging any reported name that does not match.

## What Was Built

- **`derive_identity(smiles, db_path=None)`** — derives a canonical SMILES (`Chem.MolToSmiles`, default flags) and InChIKey (`Chem.MolToInchiKey`), then performs a **complementary two-path** lookup against the `compounds` table: Path 1 InChIKey-first (`WHERE inchi_key = ? AND inchi_key != ''`, reaches the nmrshiftdb partition), Path 2 canonical-SMILES fallback (`WHERE smiles = ? AND smiles != ''`, reaches the COCONUT partition) only if Path 1 misses. Invalid SMILES → `{matched: False, error, confidence: "novel"}`; DB unavailable → structural identity + `db_unavailable: true`. COCONUT-accession (`^CNP\d+`) hits → `confidence: "confirmed-structure"`.
- **`_normalize_name` / `_name_match`** — tolerant token-set comparison over `;`-split synonyms (drops accessions + filler tokens like "dye", strips punctuation, whole-token equality only). Used solely for the name gate.
- **`check-identity` subcommand** — `--smiles` (required), `--reported-name` (optional), `--db` (optional override). Emits `{mode, reported_name, derived, name_match, verdict, warning}`. Verdict: `confirmed`/`confirmed-structure` (matched + name agrees or no name), `tentative` (matched + name disagrees, OR no-hit + asserted name → warning), `novel` (no-hit, no name). Always exits 0.
- **`tests/test_verify_case_identity.py`** — 11 tests: structural derivation, invalid-SMILES novel, indigo-via-InChIKey, coconut-via-SMILES-fallback (live round-trip), CASE4 chamazulene no-hit/tentative, CASE5 indigo↔isoindigo mismatch, tolerant punctuation/word-order match, no-false-substring, novel-clean. DB-dependent tests guarded by `skipif(find_derep_database() is None)`.

## TDD Gate Compliance

- RED gate: `test(87-01): ...` commit `70f2cc3` — 11 tests collectable, all failing against the not-yet-implemented function.
- GREEN gate: `feat(87-01): ...` commit `c5fe865` — implementation; all 19 tests (11 identity + 8 existing) pass.
- No REFACTOR commit needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Test module collectability under RED**
- **Found during:** Task 0
- **Issue:** A module-level `derive_identity = verify_case_solution.derive_identity` binding raised `AttributeError` at import, so `pytest --co` failed (exit ≠ 0) — but the Task 0 acceptance criterion requires the module to be *collectable* while still RED.
- **Fix:** Replaced the eager binding with a thin call-time wrapper `def derive_identity(*args, **kwargs): return verify_case_solution.derive_identity(...)` so collection succeeds and the failure surfaces only when tests run.
- **Files modified:** `tests/test_verify_case_identity.py`
- **Commit:** `70f2cc3`

## Verification Results

- `pytest tests/test_verify_case_identity.py tests/test_verify_case_solution.py -q` → **19 passed** (DB present locally; identity DB-tests would skip cleanly without it).
- All 5 `check-identity` CLI acceptance invocations produce the exact stated verdicts (confirmed / tolerant-confirmed / tentative-mismatch / tentative-no-hit-name / novel), all exit 0.
- SQL parameterization verified: `WHERE inchi_key = ?` present; no f-string/`%`/`.format` interpolation into any SELECT (T-87-01 mitigated).
- `ruff check` clean on both files.
- Existing aromatic-ring + formula default mode unchanged (`test_verify_case_solution.py` green).

## Known Stubs

None.

## Notes

- mypy reports pre-existing project-wide patterns (bare `dict` return types, untyped RDKit `GetAtoms`/`MolToInchiKey` calls) consistent with the original `_check_smiles` in this same file (72 errors across 20 files, project-wide). New code follows the established file convention; out of scope to retype here per the scope boundary.
- Skill-level wiring (analyst rendering tentative identities via this tool, IDENT-03 consumer side) is a separate `repo/.claude/` agent edit, validated by the Phase 89 blind UAT gate — not part of this Python-tooling plan.

## Self-Check: PASSED

- FOUND: scripts/verify_case_solution.py (def derive_identity ×1)
- FOUND: tests/test_verify_case_identity.py (FVZVDQVUOAAMCG fixture present)
- FOUND: .planning/phases/87-final-identity-verification-gate/87-01-SUMMARY.md
- FOUND: commit 70f2cc3 (RED), c5fe865 (GREEN)
