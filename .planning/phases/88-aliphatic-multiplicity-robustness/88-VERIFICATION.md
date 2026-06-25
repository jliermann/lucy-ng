---
phase: 88-aliphatic-multiplicity-robustness
verified: 2026-06-25T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: none
  previous_score: n/a
deferred:
  - truth: "Live CASE-team runtime behavior of the [MULTIPLICITY-AMBIGUOUS] / per-family search / coverage gate / G-MULT prompt edits (functional acceptance — chamazulene di-methyl-ethyl constitution reachable, coverage gate reopens the iPr-only run)"
    addressed_in: "Phase 89"
    evidence: "Phase 89 goal: 'Independent blind CASE runs prove the RANK/IDENT/MULT fixes hold end-to-end'; ROADMAP: 'UAT-01 is the acceptance test for MULT (CASE4)'. The .claude/ markdown edits require a FRESH Claude Code session to reload and are validated by the blind CASE4 re-run, not by unit tests this session."
---

# Phase 88: Aliphatic Multiplicity Robustness Verification Report

**Phase Goal:** When aliphatic multiplicity cannot be hard-determined, the search covers every viable multiplicity family so the correct constitution is reachable (hardening v9.0 FIX-10). Targets the CASE4 multiplicity-model-hardcoding failure.
**Verified:** 2026-06-25
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

The phase decomposes into one executable Python seam (88-01, fully verifiable this session) and three layers of CASE-team prompt wiring (88-02/88-03, verifiable at source by grep this session; live runtime behavior is the Phase 89 blind CASE4 UAT, a separate roadmap phase). All four roadmap success criteria / MULT requirements are accounted for and each maps to a plan's `must_haves`.

### Observable Truths

| # | Truth | Status | Evidence |
| - | ----- | ------ | -------- |
| 1 | **MULT-04 (SC2):** nmr-chemist emits a deterministic "multiplicity-ambiguous → enumerate families" signal when HSQC is not multiplicity-edited; the detection basis is programmatic | ✓ VERIFIED | `_detect_multiplicity_edited` in `cli/pick.py:22-55` emits `multiplicity_edited`+`negative_crosspeak_count` in `pick hsqc --format json` (wired at pick.py:235,243-244,257); helper unit-tested (7 tests pass). nmr-chemist.md contains `[MULTIPLICITY-AMBIGUOUS]` (6×), `multiplicity_edited` (8×), `viable_families` (3×), `AND/OR` trigger (l.259), and `NECESSARY BUT NOT SUFFICIENT` caveat (l.265) — the trigger combines the HSQC boolean with APT/DEPT reliability, not the boolean alone |
| 2 | **MULT-01 (SC1):** when ambiguous, the lsd-engineer searches ALL viable multiplicity families as separate fully-constrained LSD runs and ranks across a deduped union | ✓ VERIFIED | lsd-engineer.md: `iteration_NN_<family>/` per-family runs (5×, l.607), deduped `analysis/union_solutions.smi` (l.248-254), "parser does NOT dedup" (l.254), one `lucy lsd rank` across the union (l.257-261), sequential-with-fallback explicitly rejected (l.193), cap-of-3 truncation rule documented in nmr-chemist.md |
| 3 | **MULT-02 (SC3):** an MAE-independent pre-accept coverage gate fires — if ≥2 viable families exist but only one was searched, the run does not accept; it reopens and searches the other(s) | ✓ VERIFIED | case.md `coverage_gate` step (l.659-688): deterministic, **MAE-INDEPENDENT** (l.660,679 "does NOT look at MAE"), set-containment `viable_families ⊆ searched_families` (l.684), guarded by `[MULTIPLICITY-AMBIGUOUS]` record (single-family flow skips), reopens on FAIL; `## Multiplicity Coverage` ledger (l.227-242); `[RANKING-COMPLETE]` routed through coverage_gate→identity_gate (l.335-337); reopen pattern in loop-patterns.md (l.90) + advisory in advisory-templates.md (l.291) |
| 4 | **MULT-03 (SC4):** a devils-advocate "evidence FOR model X" flag forces model X into the search space and cannot be dismissed by the convergence narrative | ✓ VERIFIED | devils-advocate.md `G-MULT` gate (l.441): emits `[MULT-EVIDENCE-FOR] model=X` (l.478), BINDING / pre-accept (l.452), "closeable ONLY by an actual `iteration_NN_X/` search ... NEVER by the convergence narrative" (l.467,528), CASE4 HMBC 11→13 ethyl example embedded (l.500); enforced by case.md coverage gate's DA-mandated-models check (l.688) |

**Score:** 4/4 truths verified

### Deferred Items

| # | Item | Addressed In | Evidence |
| - | ---- | ------------ | -------- |
| 1 | Live CASE-team runtime/functional acceptance of the 88-02/88-03 markdown prompt edits (blind CASE4: chamazulene di-methyl-ethyl reachable; coverage gate reopens the iPr-only run) | Phase 89 | Phase 89 goal: "prove the RANK/IDENT/MULT fixes hold end-to-end"; "UAT-01 is the acceptance test for MULT (CASE4)". Every edited `.claude/` file carries a fresh-session reload note stating runtime behavior is validated by the blind CASE4 re-run, not unit tests this session. Not a Phase-88 gap. |

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/lucy_ng/cli/pick.py` | `multiplicity_edited`+`negative_crosspeak_count` in `pick hsqc` JSON via pure helper | ✓ VERIFIED | Helper present (l.22-55), wired into pick_hsqc JSON (l.243-244) + text branch (l.257); NaN/inf-robust + boolean⟺count consistent (WR-01/WR-02 fixed in 6abb25c) |
| `tests/test_cli_pick.py` | true/false/zeros/empty + NaN/inf regression tests | ✓ VERIFIED | 7 multiplicity tests pass (incl. `_nan_with_real_negative`, `_inf_does_not_poison_scale`, `_boolean_count_consistent`); full file 24 passed |
| `.claude/agents/lucy-nmr-chemist.md` | `[MULTIPLICITY-AMBIGUOUS]` + viable families + AND/OR caveat | ✓ VERIFIED | Section 5b present; all required tokens + fresh-session note |
| `.claude/agents/lucy-lsd-engineer.md` | per-family `iteration_NN_<family>/` + deduped union + SEARCHED-not-RANKED | ✓ VERIFIED | "Per-Family Multiplicity Search (MULT-01)" section (l.235-262, l.607) |
| `.claude/commands/lucy-ng/case.md` | MAE-independent coverage gate + ledger | ✓ VERIFIED | `coverage_gate` step + `## Multiplicity Coverage` ledger |
| `.claude/agents/lucy-devils-advocate.md` | binding `[MULT-EVIDENCE-FOR]` G-MULT gate | ✓ VERIFIED | G-MULT gate l.441-528 |
| `.claude/commands/lucy-ng/references/loop-patterns.md` | coverage-triggered reopen pattern | ✓ VERIFIED | "Multiplicity Coverage Gap" l.90-130 |
| `.claude/commands/lucy-ng/references/advisory-templates.md` | reopen advisory (WHAT-not-HOW) | ✓ VERIFIED | `multiplicity_coverage_reopen_advisory` l.291 |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `pick_hsqc` | `spectrum.data` negative-intensity check | `_detect_multiplicity_edited` (np.min/finite-mask) | ✓ WIRED | pick.py:235 calls helper; emitted in JSON |
| nmr-chemist `[MULTIPLICITY-AMBIGUOUS]` | lsd-engineer per-family runs | structured signal listing viable families | ✓ WIRED | token present in both producers + consumed at lsd-engineer step 2a (l.607) |
| nmr-chemist | `lucy pick hsqc multiplicity_edited` | reads the programmatic boolean | ✓ WIRED | `multiplicity_edited` referenced 8× in nmr-chemist.md |
| case.md coverage gate | CASE-PROGRESS.md viable vs searched | viable ⊆ searched before accept | ✓ WIRED | set-containment check l.684 |
| devils-advocate `[MULT-EVIDENCE-FOR]` | case.md mandatory-search | DA flag recorded + enforced by gate | ✓ WIRED | DA-mandated-models check l.688 |

**Token cross-consistency:** `[MULTIPLICITY-AMBIGUOUS]` in 6 files, `[MULT-EVIDENCE-FOR]` in 4, `Multiplicity Coverage` in 4, `viable_families` in 5 — consistent across producers, orchestrator, and references.

### Data-Flow Trace (Level 4)

Not applicable in the dynamic-render sense — the executable artifact is a CLI detector producing a deterministic boolean from `Spectrum2D.data` (a real reduction over NMR matrix values, no static/empty fallback). Behavioral spot-check below confirms it produces real verdicts on real data.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Helper detects real negative cross-peaks | `_detect_multiplicity_edited(d)` with one -1000 pixel | `(True, 1)` | ✓ PASS |
| NaN does not mask real negatives (WR-01) | same + one `np.nan` pixel | `(True, 1)` | ✓ PASS |
| inf does not poison scale (WR-01) | same + one `np.inf` pixel | `(True, 1)` | ✓ PASS |
| Empty data safe default | `_detect_multiplicity_edited(np.empty((0,0)))` | `(False, 0)` | ✓ PASS |
| All-zero safe default | `np.zeros((10,10))` | `(False, 0)` | ✓ PASS |
| boolean ⟺ count consistency under NaN | `b == (c>0)` | `True` | ✓ PASS |
| Multiplicity test subset | `pytest -k multiplicity_edited` | 7 passed | ✓ PASS |
| Full pick CLI suite | `pytest tests/test_cli_pick.py -q` | 24 passed | ✓ PASS |

### Probe Execution

No probe scripts declared by the phase plans and no `scripts/*/tests/probe-*.sh` convention applies (the phase's only runnable seam is unit-tested). SKIPPED — not a migration/probe phase.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| MULT-01 | 88-02 | lsd-engineer searches ALL viable families, not hard-coded one | ✓ SATISFIED | Truth #2 |
| MULT-02 | 88-03 | MAE-independent clean-but-wrong coverage guardrail | ✓ SATISFIED | Truth #3 |
| MULT-03 | 88-03 | binding DA "evidence FOR model X" flag | ✓ SATISFIED | Truth #4 |
| MULT-04 | 88-01, 88-02 | nmr-chemist deterministic multiplicity-ambiguous signal | ✓ SATISFIED | Truth #1 |

All four MULT requirements appear in REQUIREMENTS.md (l.25-28, mapped to Phase 88 / Complete at l.62-65) and each maps to a plan's `requirements`/`must_haves`. No orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | — | No unreferenced TBD/FIXME/XXX debt markers in modified files; no stub data sources; the two `return False, 0` early-returns in pick.py are intended safe-default guards (T-88-01), not stubs | — | — |

The `return False, 0` lines in pick.py are deliberate degrade-to-safe-default guards pinned by tests, not empty-implementation stubs. The "fresh session required" notes in the `.claude/` files are accurate reload instructions, not "not yet implemented" placeholders.

### Human Verification Required

None for Phase 88. The only functional/runtime check — the blind CASE4 UAT-01 — is a dedicated later phase (Phase 89), not a Phase-88 human-verify item. The 88-02/88-03 prompt edits are source-verified this session; their live behavior is the explicit deliverable of Phase 89.

### Gaps Summary

No gaps. The one Python seam (88-01) is implemented, wired, NaN/inf-robust, and unit-tested (including the WR-01/WR-02 code-review fixes landed in commit 6abb25c with 3 regression tests). All three prompt-wiring layers (88-02 producer agents, 88-03 orchestrator coverage gate + binding DA flag) are present and substantive at source, with cross-consistent signal tokens and both required RESEARCH pitfalls encoded: (1) coverage counts SEARCHED-not-RANKED — a >~50-solution conversion-skipped family still counts (lsd-engineer l.241-245, case.md l.685-686); (2) ambiguity detection is AND/OR with `multiplicity_edited=false` necessary-but-not-sufficient (nmr-chemist l.259,265). All 8 task commits + the fix commit are present. Functional acceptance is correctly deferred to Phase 89's blind CASE4 UAT, recorded as a deferred item rather than a gap.

---

_Verified: 2026-06-25_
_Verifier: Claude (gsd-verifier)_
