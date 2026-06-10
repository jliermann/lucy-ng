---
phase: 83-constraint-hardness-guard
verified: 2026-06-10T17:00:00Z
status: passed
score: 4/4
overrides_applied: 0
re_verification: false
---

# Phase 83: Constraint-Hardness Guard (FIX-10) — Verification Report

**Phase Goal:** An uncertain structural inference must never become a hard, solution-excluding LSD constraint. A hard heteroatom PROP/BOND is permitted ONLY from (i) direct connectivity evidence (HMBC/HSQC/exchangeable-H) or (ii) convergent multi-source evidence (carbonyl: Cq + 160-220 ppm + C=O chemistry). A single `lucy detect neighbours` probability never hardens alone — a borderline `typical` especially not, and not when carbon is the dominant neighbour.
**Verified:** 2026-06-10T17:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | nmr-chemist states detect-neighbours output as statistical prior/advisory; reads full distribution + dominant-neighbour rule; knows 145-160 ppm aromatic-C ambiguity; forbids renormalization; re-asserts Pitfall 6 | VERIFIED | See SC-1 detail below |
| 2 | lsd-engineer forbids hard heteroatom PROP/BOND from statistics alone; requires direct-evidence OR convergence condition; carbonyl exception preserved | VERIFIED | See SC-2 detail below |
| 3 | devils-advocate has G-PROP-EVIDENCE gate matching G-* pattern; blocks hard heteroatom PROP/BOND lacking direct/convergent evidence; sub-checks for typical/carbon-dominant/renormalized | VERIFIED | See SC-3 detail below |
| 4 | NeighbourResult carries advisory/advisory_note/dominant_element; `lucy detect neighbours --format json` surfaces them; regression test includes CASE9-truth-not-excluded (RDKit: C12H16O3, 0 ring-oxygen, aromatic C with aliphatic-C substituent) | VERIFIED | See SC-4 detail below |

**Score:** 4/4 truths verified

---

## Success Criterion 1: lucy-nmr-chemist.md

**Grep counts (file: `.claude/agents/lucy-nmr-chemist.md`):**

| Pattern | Required | Actual | Status |
|---------|----------|--------|--------|
| `statistical prior` | >=2 | 2 | PASS |
| `dominant` | >=2 | 4 | PASS |
| `FIX-10` | >=1 | 1 | PASS |
| `145-160 ppm` | >=1 | 1 | PASS |
| `renormali` | >=1 | 2 | PASS |

**Key content confirmed (line numbers):**

- Line 57: Pitfall 6 re-asserted as FIX-10 with full text: "detect neighbours output is a statistical prior / advisory signal — never the sole basis for a hard PROP or BOND heteroatom constraint."
- Line 61: Dominant-neighbour rule: "Identify the DOMINANT neighbour (highest frequency). If carbon is dominant, the shift is more consistent with a carbon substituent than a heteroatom substituent."
- Line 63: Renormalization prohibition: "NEVER renormalize or inflate a frequency by excluding other elements."
- Line 65: 145-160 ppm ambiguity block explicitly present.
- Line 170: Section 5 Neighbours line replaced with 8-step advisory protocol: "Output is a statistical prior — advisory only."
- Line 171: Protocol step 1 reads full distribution + identifies dominant element first.
- Line 174: Step 4: "If carbon is the dominant element, report the shift as 'likely C-substituted' in [SETUP-COMPLETE]; do NOT propose a heteroatom constraint."
- Line 178: Step 8 forbids renormalization.

**SC-1: VERIFIED**

---

## Success Criterion 2: lucy-lsd-engineer.md

**Grep counts (file: `.claude/agents/lucy-lsd-engineer.md`):**

| Pattern | Required | Actual | Status |
|---------|----------|--------|--------|
| `G-PROP-EVIDENCE` | >=2 | 3 | PASS |
| `FIX-10` | >=2 | 3 | PASS |
| `convergent` | >=2 | 2 | PASS |
| `dominant` | >=1 | 2 | PASS |
| `renormali` | >=1 | 1 | PASS |

**Key content confirmed (line numbers):**

- Line 73: FIX-10 PROHIBITION block header: "No hard heteroatom PROP/BOND from a single statistical detection value (G-PROP-EVIDENCE)"
- Line 79: Convergent corroboration exception (only): "Cq confirmed by DEPT/HSQC + shift in 160-220 ppm + unambiguous C=O context... This is the ONLY case where a detect-neighbours O value contributes to a hard BOND — because three independent sources converge."
- Line 81: Forbidden patterns list names G-PROP-EVIDENCE gate.
- Line 83: renormalizing forbidden explicitly.
- Line 84: "Emitting a hard heteroatom constraint when carbon is the dominant neighbour at that shift" listed as forbidden.
- Line 87: "(FIX-10)" closes the block.
- Line 245: Manual Checklist item 6 updated with convergent-evidence rule and explicit "Devils-advocate G-PROP-EVIDENCE gate will BLOCK. (FIX-10)".

**SC-2: VERIFIED**

---

## Success Criterion 3: lucy-devils-advocate.md

**Grep counts (file: `.claude/agents/lucy-devils-advocate.md`):**

| Pattern | Required | Actual | Status |
|---------|----------|--------|--------|
| `G-PROP-EVIDENCE` | >=4 | 7 | PASS |
| `\| G-PROP-EVIDENCE \|` (table row) | >=1 | 1 | PASS |
| `FIX-10` | >=2 | 2 | PASS |
| `dominant` | >=2 | 4 | PASS |
| `renormali` | >=1 | 4 | PASS |
| `typical` | >=2 | 4 | PASS |
| `G-ELIM-1` or `G7` (existing gates intact) | >=2 | 5 | PASS |

**Structure confirmed:**

- Line 374: Gate definition header "G-PROP-EVIDENCE: Hard Heteroatom PROP/BOND Without Sufficient Evidence (CRITICAL)"
- Lines 394/396/398: Three independent sub-checks present — (a) constraint_type 'typical', (b) carbon is dominant neighbour, (c) renormalized probability — each triggers CRITICAL independently.
- Line 403: CRITICAL message template with (FIX-10) reference.
- Line 407: Rationale paragraph explaining the defect mode and (FIX-10) tag.
- Line 416: Pipe-delimited summary table row present: `| G-PROP-EVIDENCE | Pre-run, all iterations | CRITICAL | ... |`
- Line 521: Workflow step 8a: "Run G-PROP-EVIDENCE gate (Section 5, Check 5)..."

**Gate appears in:** (a) definition block, (b) pipe-delimited summary table, (c) workflow step 8a — all three required locations confirmed.

**SC-3: VERIFIED**

---

## Success Criterion 4: Tooling — NeighbourResult advisory fields + regression tests

### Model fields (src/lucy_ng/detection/models.py)

| Field | Location | Behavior | Status |
|-------|----------|----------|--------|
| `NeighbourDistribution.dominant_element` property | line 191 | Returns element name with highest frequency or None | VERIFIED |
| `NeighbourResult.advisory: bool = True` | line 253 | Plain field, defaults True, existing construction unaffected | VERIFIED |
| `NeighbourResult.advisory_note: str` | line 254 | Contains "statistical prior" and "FIX-10" | VERIFIED |
| `NeighbourResult.dominant_element` | line 260-264 | `@computed_field` delegating to `distribution.dominant_element` | VERIFIED |
| `summary()` first line | line 273 | `[ADVISORY] {advisory_note}` — starts with `[ADVISORY]` | VERIFIED |
| `summary()` dominant-carbon advisory | lines 322-328 | "Dominant neighbour: carbon — likely carbon-substituted; heteroatom placement uncertain" | VERIFIED |

**Live runtime check (all assertions PASSED):**
```
advisory: True
advisory_note contains statistical prior: True
advisory_note contains FIX-10: True
dominant_element (carbon=0.95, oxygen=0.55): carbon
json advisory: True
json dominant_element: carbon
json advisory_note present: True
summary starts with [ADVISORY]: True
summary contains carbon: True
oxygen dominant (carbon=0.30, oxygen=0.97): oxygen
```

### Regression tests (tests/test_detection_neighbours.py)

| Test | Function | Status |
|------|----------|--------|
| A — advisory default | `test_neighbour_result_advisory_default` (line 406) | PASS |
| B — summary [ADVISORY] prefix | `test_neighbour_result_summary_advisory_prefix` (line 419) | PASS |
| C — carbon dominant_element | `test_dominant_element_carbon` (line 432) | PASS |
| D — oxygen dominant_element | `test_dominant_element_oxygen` (line 438) | PASS |
| E — CLI JSON fields | `test_detect_neighbours_json_advisory_and_dominant_element` (line 444) | PASS |
| F — CASE9 truth not excluded | `test_case9_truth_not_excluded_by_fix10_conformant_constraints` (line 459) | PASS |

**pytest tests/test_detection_neighbours.py:** 22 passed (16 original + 6 new), 0 failures.

**CASE9-truth-not-excluded assertion (Test F, independently re-run):**
- truth SMILES `CC(O)c1ccc(cc1)C(=O)OC(C)C` parses via RDKit: PASS
- formula == C12H16O3: PASS
- ring_O_count == 0: PASS (0 aromatic oxygen atoms)
- aromatic C with aliphatic C substituent >= 1: PASS (count = 2)

**SC-4: VERIFIED**

---

## Compound-Agnostic Guard

All three agent files must contain zero occurrences of CASE9-specific values (150.8, 166.08, C12H16O3, isopropyl 4, ibuprofen, CASE9):

| File | Hits | Status |
|------|------|--------|
| `.claude/agents/lucy-nmr-chemist.md` | 0 | PASS |
| `.claude/agents/lucy-lsd-engineer.md` | 0 | PASS |
| `.claude/agents/lucy-devils-advocate.md` | 0 | PASS |

No compound-specific leak content in any agent file.

---

## Required Artifacts

| Artifact | Status | Evidence |
|----------|--------|---------|
| `.claude/agents/lucy-nmr-chemist.md` | VERIFIED | Contains "statistical prior" x2, "dominant" x4, "145-160 ppm" x1, "renormali" x2, "FIX-10" x1; compound-agnostic |
| `.claude/agents/lucy-lsd-engineer.md` | VERIFIED | Contains "G-PROP-EVIDENCE" x3, "convergent" x2, "FIX-10" x3; compound-agnostic |
| `.claude/agents/lucy-devils-advocate.md` | VERIFIED | Contains "G-PROP-EVIDENCE" x7, table row, workflow step 8a, "FIX-10" x2; existing gates G-ELIM-1, G7 intact |
| `src/lucy_ng/detection/models.py` | VERIFIED | advisory, advisory_note, dominant_element fields present; computed_field import; summary() updated |
| `src/lucy_ng/cli/detect.py` | VERIFIED | Advisory docstring paragraph added to neighbours_command |
| `tests/test_detection_neighbours.py` | VERIFIED | 6 new tests (A-F), all passing; CASE9-truth-not-excluded via RDKit |

---

## Quality Gates

| Gate | Result |
|------|--------|
| `pytest tests/test_detection_neighbours.py` | 22 passed, 0 failed |
| `pytest` (full suite) | 1071 passed, 7 skipped, 1 xfailed, 0 failed |
| `ruff check` (modified files) | All checks passed |
| `mypy src/lucy_ng/detection/` | Success: no issues found in 4 source files |

**Note on pre-existing failures:** The SUMMARY.md notes a pre-existing test `tests/test_validation_ranking.py::TestBadlistPatterns::test_agent_file_exists` was removed (commit `cf98c04` on master, which appears before the phase-83 changes). Full suite is clean at 1071 passed.

---

## Git Commits Verified

All 5 phase-83 commits confirmed on master branch:

| Commit | Description |
|--------|-------------|
| `fedb5cd` | feat(83-01): nmr-chemist — full-distribution advisory rule + Pitfall 6 FIX-10 |
| `2388783` | feat(83-01): lsd-engineer — FIX-10 PROHIBITION block + convergent-evidence rule |
| `d7b844b` | feat(83-01): devils-advocate — G-PROP-EVIDENCE gate (FIX-10 constraint hardness guard) |
| `491ea52` | feat(83-02): add advisory, advisory_note, dominant_element to NeighbourResult |
| `9b2f75c` | test(83-02): add advisory/dominant_element regression tests + CASE9-truth-not-excluded |

---

## Scope Boundary Confirmed

Per ROADMAP.md and plan directives, the following are explicitly OUT of scope for Phase 83 and are NOT evaluated here:

- Benzene-ring emergence (D-04 complex) — separate downstream blocker
- HMBC-pool richness/extraction — separate downstream blocker

FIX-10 removes the hard-exclusion mechanism (the PROP-from-statistics defect). It does not guarantee a full CASE9 solve. **The blind CASE9 re-run by a fresh instance remains the separate milestone AND-gate before v9.0 ships.**

---

## Human Verification Required

None. All success criteria are mechanically verifiable and confirmed.

---

_Verified: 2026-06-10T17:00:00Z_
_Verifier: Claude (gsd-verifier)_
