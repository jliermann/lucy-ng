---
phase: 74-constraint-preservation-and-merge
plan: 01
subsystem: lsd
tags: [lsd, models, generator, ring-exclusion, equivalence, native-constraints, tdd]

requires:
  - phase: 72-design-re-validation
    provides: D-03 locked (native-only BOND/COSY; no SYME/DEFF NOT); D-04 locked (no SKEL forcing)
  - phase: 73-solution-plumbing-fix
    provides: LSD runner with cwd=output_dir contract (filter relative-path resolution)

provides:
  - LSDProblem.ring_exclusion_enabled field (bool, default False)
  - LSDProblem.add_equivalence_pair() — gem-dimethyl -> BOND direct injection
  - LSDProblem.add_aromatic_equivalence_pair() — aromatic CH pair -> COSY with dedup
  - LSDInputGenerator.generate() ring-exclusion section (DEFF F1/F2 + FEXP)
  - LSDInputGenerator.write_file() copies bundled ring3/ring4 to output_dir
  - LSDInputGenerator._write_filter_files() static helper via importlib.resources
  - Bundled filter package: src/lucy_ng/lsd/filters/{ring3,ring4,__init__.py}
  - TestNativeConstraintEmission (6 tests) — RELI-02 programmatic path proof

affects:
  - phase: 74-02 (permutation constraint preservation — deepcopy carries new fields)
  - phase: 75-skill-rewrite (agent hand-written path, uses BOND/COSY/DEFF-F idioms from this plan)
  - phase: 76-uat (end-to-end CASE run verifying aromatic emergence)

tech-stack:
  added:
    - importlib.resources (stdlib, Python 3.9+) for bundled filter file access
  patterns:
    - Option A direct injection: add_equivalence_pair() appends to existing constraints/correlations lists; no new model class needed
    - Relative DEFF paths in generated .lsd + copy-to-output-dir at write_file() time
    - TDD RED/GREEN per task commit

key-files:
  created:
    - src/lucy_ng/lsd/filters/__init__.py
    - src/lucy_ng/lsd/filters/ring3
    - src/lucy_ng/lsd/filters/ring4
  modified:
    - src/lucy_ng/lsd/models.py (ring_exclusion_enabled + two new methods)
    - src/lucy_ng/lsd/generator.py (importlib, ring-exclusion section, write_file update, _write_filter_files)
    - tests/test_lsd_generator.py (TestNativeConstraintEmission class, 6 tests)
    - pyproject.toml (artifacts updated to include src/lucy_ng/lsd/filters/*)

key-decisions:
  - "Option A direct injection: add_equivalence_pair()/add_aromatic_equivalence_pair() inject BOND/COSY into existing lists — no EquivalencePair model class needed"
  - "Relative DEFF paths ('ring3'/'ring4') in generated .lsd + copy bundled files to output_dir in write_file() — portable, no absolute LSD install dependency"
  - "ring_exclusion_enabled: bool on LSDProblem (not RingExclusionConfig dataclass) — simplest option satisfying D-03 with no extra model complexity"
  - "COSY deduplication in add_aromatic_equivalence_pair(): check sorted(atom1,atom2) pair against existing correlations before appending"

patterns-established:
  - "Ring exclusion split: generate() emits DEFF/FEXP lines; write_file() copies filter files — keeps generate() pure-string"
  - "importlib.resources.files('lucy_ng.lsd.filters') / name — the canonical bundled resource access pattern for this package"

requirements-completed: [RELI-02, RELI-03]

duration: 25min
completed: 2026-05-24
---

# Phase 74 Plan 01: Native Constraint Emission Summary

**LSDProblem extended with gem-dimethyl BOND injection, aromatic COSY injection, and ring-exclusion DEFF F/FEXP emission via bundled ring3/ring4 filter package — D-03 native-only contract satisfied for programmatic path**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-05-24T00:00:00Z
- **Completed:** 2026-05-24T00:25:00Z
- **Tasks:** 2 (TDD, both RED+GREEN)
- **Files modified:** 7 (4 source, 1 test, 1 config, 3 new package resources)

## Accomplishments

- Extended `LSDProblem` with `ring_exclusion_enabled: bool = False` and two new methods (`add_equivalence_pair`, `add_aromatic_equivalence_pair`) that inject directly into existing constraints/correlations lists (Option A)
- `generate()` now emits `DEFF F1 "ring3"`, `DEFF F2 "ring4"`, `FEXP "NOT F1 AND NOT F2"` when `ring_exclusion_enabled=True` — relative paths, fully portable
- `write_file()` copies bundled `ring3`/`ring4` to `output_dir` via `importlib.resources` so LSD finds them at its CWD
- Bundled `src/lucy_ng/lsd/filters/{ring3,ring4,__init__.py}` as package resources; `pyproject.toml` artifacts updated
- 6-test `TestNativeConstraintEmission` class proves RELI-02 for programmatic path: no SYME, no DEFF NOT, correct BOND/COSY/DEFF-F emission

## Task Commits

1. **Task 1: Bundle ring3/ring4 filter files + extend LSDProblem model** — `70c946e` (test — RED, 4/6 green)
2. **Task 2: Native ring-exclusion emission in generate() and write_file()** — `22669af` (feat — all 6 GREEN)

## Files Created/Modified

- `src/lucy_ng/lsd/filters/__init__.py` — empty package marker enabling `importlib.resources.files("lucy_ng.lsd.filters")`
- `src/lucy_ng/lsd/filters/ring3` — verbatim copy of LSD 3-membered ring SSTR/LINK filter
- `src/lucy_ng/lsd/filters/ring4` — verbatim copy of LSD 4-membered ring SSTR/LINK filter
- `src/lucy_ng/lsd/models.py` — `ring_exclusion_enabled` field, `add_equivalence_pair()`, `add_aromatic_equivalence_pair()`
- `src/lucy_ng/lsd/generator.py` — `importlib.resources` import, ring-exclusion section in `generate()`, updated `write_file()`, new `_write_filter_files()` static method
- `tests/test_lsd_generator.py` — `TestNativeConstraintEmission` class (6 tests)
- `pyproject.toml` — artifacts entry expanded to include `src/lucy_ng/lsd/filters/*`

## Decisions Made

- **Option A direct injection** chosen over Option B (new EquivalencePair dataclass): `add_equivalence_pair()` appends `LSDConstraint("BOND")` directly to `self.constraints`; `add_aromatic_equivalence_pair()` appends `LSDCorrelation("COSY")` directly to `self.correlations`. The existing BOND/COSY rendering sections in `generate()` handle them automatically — zero new generator branches needed for equivalence.
- **Relative DEFF paths** in generated files (`"ring3"`, `"ring4"`) rather than absolute paths — requires copying filter files to output_dir at write time, but fully portable across machines.
- **Single bool field** (`ring_exclusion_enabled: bool`) on `LSDProblem` rather than a `RingExclusionConfig` dataclass — sufficient for the current two-filter case; can be upgraded later if asymmetric exclusion is needed.

## Deviations from Plan

None — plan executed exactly as written. The task boundary note in Task 1 (4 tests green, 2 pending Task 2) behaved exactly as specified.

## Issues Encountered

None.

## Scope Note (RELI-02/03 Partial Satisfaction)

Phase 74 plan 01 satisfies RELI-02 and RELI-03 **for the programmatic path only** (any code calling `LSDInputGenerator.generate()` or `write_file()`). The CASE agent (lucy-lsd-engineer) writes LSD files by hand via Bash/Write tools and does NOT call `LSDInputGenerator`. That path still writes `SYME` and `DEFF NOT`. Phase 75 must update agent skills to write `BOND`/`COSY` and `DEFF F`/`FEXP` instead. RELI-02/03 are fully closed after Phase 75 + Phase 76 UAT.

## Next Phase Readiness

- Phase 74 plan 02 (permutation constraint preservation): `_build_permutation` deepcopy automatically carries `ring_exclusion_enabled` and any `constraints`/`correlations` injected by the new methods — no additional changes needed to orchestrator.py
- Phase 75 (skill rewrite): native BOND/COSY/DEFF-F patterns now proven and documented; filter bundling strategy established

---

## Self-Check

- `src/lucy_ng/lsd/filters/ring3` exists: checked
- `src/lucy_ng/lsd/filters/ring4` exists: checked
- `src/lucy_ng/lsd/filters/__init__.py` exists: checked
- All 48 tests pass (`pytest tests/test_lsd_generator.py -x -q`)
- `ring_exclusion_enabled` count in models.py: 1
- `_write_filter_files` count in generator.py: 2 (declaration + call)
- ring3 SSTR count: 3

## Self-Check: PASSED

---
*Phase: 74-constraint-preservation-and-merge*
*Completed: 2026-05-24*
