---
phase: 77-fix-lucy-lsd-run-plumbing-bug-and-re-run-blind-uat-repair-in
plan: 02
subsystem: lsd-generator
tags: [fix, tdd, aromatic-cosy, cross-ring-pairing, cli, detect, generator, grouping]

requires:
  - phase: 77-01
    provides: "filter-file copy in _execute_lsd; arm_a_ring_excl.lsd fixture; fail-loud _invoke_outlsd"

provides:
  - "detect_aromatic_cosy_pairs() module-level function in lucy_ng.lsd.generator"
  - "lucy detect aromatic-cosy CLI subcommand in lucy_ng.cli.detect"
  - "TestDetectAromaticCosyPairs: 4 unit tests for cross-ring pairing algorithm"
  - "TestDetectAromaticCosyIntegration: end-to-end test proving aromatic ring emerges without ring BONDs"

affects:
  - 77-03 (skill hygiene — skill references lucy detect aromatic-cosy)
  - 78 (blind re-UAT — agent uses lucy detect aromatic-cosy instead of hand-deriving pairs)

tech-stack:
  added: []
  patterns:
    - "cross-ring COSY pairing: zip(sorted(groupA.atom_ids), reversed(sorted(groupB.atom_ids)))"
    - "detect_aromatic_cosy_pairs() — pure transform function consuming list[SignalGroup]"
    - "CLI aromatic-cosy: lazy import inside try/except, text/json output, same @detect.command pattern"

key-files:
  created: []
  modified:
    - src/lucy_ng/lsd/generator.py
    - src/lucy_ng/cli/detect.py
    - tests/test_lsd_generator.py

key-decisions:
  - "Algorithm uses zip(sorted(A), reversed(sorted(B))) — cross-ring, never within-group (prevents LSD error 283)"
  - "aromatic_range default (100.0, 165.0) — pure shift-based filter, no multiplicity required"
  - "Integration test uses arm_a_ring_excl.lsd fixture directly (simpler, equally valid per plan option B)"
  - "zip(strict=True) used to satisfy ruff B905 rule (lists are equal-length by construction)"

requirements-completed: [FIX-02]

duration: 8min
completed: "2026-06-01"
---

# Phase 77 Plan 02: detect_aromatic_cosy_pairs() + lucy detect aromatic-cosy Summary

**Deterministic cross-ring COSY pair derivation via `detect_aromatic_cosy_pairs()` in generator.py and `lucy detect aromatic-cosy` CLI — eliminating the agent's manual atom-index reasoning that caused Phase 76 failure (COSY 4 5 / 6 7 within-group instead of COSY 4 7 / 5 6 cross-ring).**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-01T15:57:00Z
- **Completed:** 2026-06-01T16:03:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `detect_aromatic_cosy_pairs()` function in generator.py: filters aromatic groups, pairs cross-ring using reversed-sort algorithm, returns 1-based atom ID tuples ready for `add_aromatic_equivalence_pair()`
- `lucy detect aromatic-cosy` CLI subcommand: accepts shifts + optional multiplicities, emits `COSY a b` lines (text) or `{"cosy_pairs": [...]}` (JSON)
- End-to-end integration test: `arm_a_ring_excl.lsd` with COSY 4 7 + COSY 5 6 (no ring BONDs) produces >= 1 aromatic solution through live LSD runner — proves FIX-01 and FIX-02 work together

## Task Commits

1. **Task 1 RED: TestDetectAromaticCosyPairs (failing)** — `f0f21ce` (test)
2. **Task 1 GREEN: detect_aromatic_cosy_pairs() implementation** — `838bb65` (feat)
3. **Task 2: aromatic-cosy CLI + TestDetectAromaticCosyIntegration** — `56a964b` (feat)

## Files Created/Modified

- `src/lucy_ng/lsd/generator.py` — Added `SignalGroup` import + `detect_aromatic_cosy_pairs()` module-level function (62 lines)
- `src/lucy_ng/cli/detect.py` — Added `aromatic_cosy_command` subcommand registered as `@detect.command("aromatic-cosy")`
- `tests/test_lsd_generator.py` — Added 3 imports, `TestDetectAromaticCosyPairs` (4 unit tests), `TestDetectAromaticCosyIntegration` (1 integration test)

## Decisions Made

- **Algorithm: zip(sorted(A), reversed(sorted(B)))** — Verified against Arm A reference (COSY 4 7 + COSY 5 6 → 2/2 aromatic solutions). The reversed pairing ensures cross-group assignment; `strict=True` added to satisfy ruff B905 (equal-length lists by construction).
- **aromatic_range default (100.0–165.0)** — Pure shift-based filter; no multiplicity filtering required in the function itself (keeps it general; multiplicities handled by group_signals() upstream).
- **Integration test approach: use fixture directly** — The plan offered two options; using `arm_a_ring_excl.lsd` directly is simpler and equally valid since it already contains the correct COSY 4 7 + COSY 5 6 cross-ring pairs.
- **No changes to main.py** — `detect` group already registered; new subcommand auto-discovered.

## Deviations from Plan

None — plan executed exactly as written.

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED: failing tests written | f0f21ce | PASS — ImportError on `detect_aromatic_cosy_pairs` import |
| GREEN: implementation makes tests pass | 838bb65 | PASS — 4/4 unit tests pass |
| REFACTOR | n/a | No refactor needed |

## Verification Gate Results

| Check | Result |
|-------|--------|
| `grep -c "def detect_aromatic_cosy_pairs" generator.py` | 1 |
| `python -c "from lucy_ng.lsd.generator import detect_aromatic_cosy_pairs"` | exits 0 |
| `pytest TestDetectAromaticCosyPairs --collect-only` | 4 collected |
| `pytest TestDetectAromaticCosyPairs -q` | 4 passed |
| `pytest tests/test_lsd_generator.py -q` | 54 passed |
| `grep -c "aromatic-cosy" detect.py` | 4 |
| `lucy detect aromatic-cosy "129.38,129.38,127.26,127.26" --multiplicities "CH,CH,CH,CH" \| grep -c "^COSY"` | 2 |
| JSON cosy_pairs check | PASS |
| No COSY 4 5 / COSY 6 7 in output | PASS |
| `pytest tests/test_lsd_runner.py -q` | 27 passed |
| `ruff check generator.py detect.py` | All checks passed |
| mypy generator.py (new errors only) | 0 new errors |

## Known Stubs

None — all behavior is wired end-to-end.

## Threat Flags

No new threat surfaces introduced. T-77-02-01 (malformed shift string) mitigated by try/except in CLI. T-77-02-04 (self-COSY) prevented by cross-group algorithm + verified by `test_ibuprofen_aromatic_groups_produces_cross_ring_pairs` assertion `all(a != b for a, b in pairs)`.

## Self-Check: PASSED

- `src/lucy_ng/lsd/generator.py`: FOUND (modified)
- `src/lucy_ng/cli/detect.py`: FOUND (modified)
- `tests/test_lsd_generator.py`: FOUND (modified)
- Commit `f0f21ce` (RED): FOUND
- Commit `838bb65` (GREEN): FOUND
- Commit `56a964b` (feat CLI + integration): FOUND
