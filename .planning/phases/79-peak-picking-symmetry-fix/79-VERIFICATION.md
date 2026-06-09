---
phase: 79-peak-picking-symmetry-fix
verified: 2026-06-08T12:00:00Z
status: human_needed
score: 4/4 must-haves verified
overrides_applied: 0
human_verification:
  - test: "CASE9 blind re-run: fresh Claude instance (not the orchestrating one) runs the full CASE workflow on the CASE9 dataset (4-(1-hydroxyethyl)benzoic acid isopropylester, C12H16O3) and reaches an RDKit-verified para-disubstituted aromatic-ester solution via the emergent path."
    expected: "RDKit confirms a C12H16O3 para-disubstituted aromatic ester SMILES; emergent COSY mechanism activated (not forced ring-BONDs); carbonyl at ~166 ppm picked automatically; intensity-symmetry candidates passed to lucy detect aromatic-cosy; QUALITY_CONVERGENCE_FAILURE pattern never fires (or fires at most once and then resolves correctly)."
    why_human: "Per the project blind-UAT protocol (feedback_blind_uat memory), the orchestrating instance is tainted and must not run this UAT. A fresh Claude instance is required. This is UAT-04 (REQUIREMENTS.md), a downstream milestone gate, not a Phase-79 code deliverable."
---

# Phase 79: Peak-Picking Symmetry Fix Verification Report

**Phase Goal:** The CASE9 failure mode is eliminated at both layers — the peak-picker no longer masks weak quaternary carbonyls under a solvent-dominated threshold, 13C intensity-symmetry is used to detect equivalent aromatic carbons (feeding the emergent-COSY mechanism), AND the CASE skill gains a feedback loop so a clean-but-wrong convergence triggers a return to the spectrum instead of silently terminating.
**Verified:** 2026-06-08
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | FIX-04: `lucy pick 1d` uses SNR/MAD absolute threshold with CDCl3-region exclusion; regression tests assert the behavior and existing picking is unchanged | VERIFIED | `_compute_snr_threshold` (peak_picker.py:23) uses `1.4826 * MAD`; `_SOLVENT_EXCLUSION_13C` dict excludes CDCl3 72-82 ppm, CD3CN dual-window, etc.; `use_snr=True` is the new default in `pick_peaks`; CASE1 regression test requires >= 9 peaks; 1037 test suite passes |
| 2 | FIX-05: `detect_intensity_symmetry` is implemented, uses class-normalized 2C-equivalence detection scoped to 100-165 ppm, and for CASE9-like input returns exactly 2 candidates with estimated_count=2 | VERIFIED | Function at peak_picker.py:68; exported from `lucy_ng.processing`; all 5 test_intensity_symmetry.py tests pass including test_case9_flags_two_candidates |
| 3 | FIX-06a: nmr-chemist skill has a MANDATORY DBE self-check after statistical detection (O/N coverage) AND a MANDATORY intensity-symmetry check, both wired into the [SETUP-COMPLETE] template and workflow steps | VERIFIED | Section 5 "Intensity-Symmetry Check (MANDATORY for aromatic compounds)" at line 117; Section "5a. DBE Self-Check (MANDATORY — before [SETUP-COMPLETE])" at line 156; [SETUP-COMPLETE] template includes `DBE balance:` and `Intensity-symmetry:` fields; workflow steps 5a and 6b both labelled MANDATORY |
| 4 | FIX-06b: QUALITY_CONVERGENCE_FAILURE 5th loop-pattern is wired into loop-patterns.md (definition), case.md detect_loops (Pattern 5 criterion) and track_and_decide (count_quality counter, 1-cycle budget, no diagnostic-specialist escalation), and advisory-templates.md (quality_convergence_advisory step with nmr-chemist target) | VERIFIED | loop-patterns.md "Five Loop Patterns" heading; Quality Convergence Failure block with primary + OR-trigger + 1-cycle budget; case.md line 348: "Five patterns to detect"; line 360: Pattern 5 with OR-trigger and guard; line 492: `QUALITY_CONVERGENCE_FAILURE: count_quality`; line 505-510: 1-cycle decision, no diagnostic escalation; advisory-templates.md `<step name="quality_convergence_advisory">` with nmr-chemist SendMessage target and 3-item re-examination checklist |

**Score:** 4/4 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/lucy_ng/processing/peak_picker.py` | SNR/MAD threshold + solvent exclusion + detect_intensity_symmetry | VERIFIED | `1.4826` at line 57; `_SOLVENT_EXCLUSION_13C` dict at line 11; `detect_intensity_symmetry` at line 68; `use_snr=True` default in `pick_peaks` |
| `src/lucy_ng/models/peaks.py` | `Peak1D.snr` and `PeakList1D.noise_sigma` optional fields | VERIFIED | `snr: float | None = None` at line 15; `noise_sigma: float | None = None` at line 50; both preserved in `to_dict()`/`from_dict()` (CR-02 fix) |
| `src/lucy_ng/cli/pick.py` | `noise_sigma` and per-peak `snr` in JSON output; `use_snr = threshold is None` | VERIFIED | Line 55: `use_snr = threshold is None`; line 73: `"noise_sigma": peaks.noise_sigma`; line 79: `"snr": p.snr` in per-peak dict |
| `tests/test_peak_picker_snr.py` | SNR threshold regression tests — all GREEN | VERIFIED | 7 tests (3 in TestSNRThreshold including CR-01 regressions, 2 in TestCASE9Regression skipped without data, 1 in TestCASE1Regression, 2 in TestCLIPick1D) — all pass |
| `tests/test_intensity_symmetry.py` | detect_intensity_symmetry tests — all GREEN | VERIFIED | 5 tests all pass |
| `/Users/steinbeck/.claude/agents/lucy-nmr-chemist.md` | DBE self-check + intensity-symmetry procedural sections | VERIFIED | "MANDATORY" label at lines 117, 156, 307, 310; both fields in [SETUP-COMPLETE] template at lines 259-260; workflow steps 5a and 6b explicit |
| `/Users/steinbeck/.claude/commands/lucy-ng/references/loop-patterns.md` | Quality Convergence Failure 5th pattern | VERIFIED | "Five Loop Patterns" heading; full pattern block with detection criteria, OR-trigger, root causes, 1-cycle budget |
| `/Users/steinbeck/.claude/commands/lucy-ng/case.md` | Pattern 5 in detect_loops; QUALITY_CONVERGENCE_FAILURE counter in track_and_decide | VERIFIED | Line 348: "Five patterns to detect"; line 360: Pattern 5 with OR-trigger and guard; line 492: counter; lines 505-510: 1-cycle termination without diagnostic escalation |
| `/Users/steinbeck/.claude/commands/lucy-ng/references/advisory-templates.md` | quality_convergence_advisory step | VERIFIED | `<step name="quality_convergence_advisory">` at line 243; nmr-chemist SendMessage target; 3-item re-examination checklist |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cli/pick.py` | `processing/peak_picker.py` | `AdaptivePeakPicker.pick_peaks()` with `use_snr`; `PeakList1D.noise_sigma` propagated to JSON | WIRED | `use_snr = threshold is None` computed at line 55; `noise_sigma` surfaced at line 73 |
| `peak_picker.py` | `models/peaks.py` | `Peak1D(snr=snr)` in positive and negative peak loops | WIRED | Lines 248, 264: `snr=snr` passed to Peak1D constructor |
| `tests/test_intensity_symmetry.py` | `processing/peak_picker.py` | `from lucy_ng.processing.peak_picker import detect_intensity_symmetry` | WIRED | Import resolves; all 5 tests pass |
| `case.md` detect_loops | `loop-patterns.md` | "Read file: ~/.claude/commands/lucy-ng/references/loop-patterns.md" before checking patterns | WIRED | Line 346 of case.md: explicit file-read instruction; Pattern 5 criterion in detect_loops references "Quality Convergence Failure" by name |
| `case.md` track_and_decide | `advisory-templates.md` | `quality_convergence_advisory template from advisory-templates.md` | WIRED | Line 506 of case.md explicitly names the template; advisory-templates.md has the matching step |
| `processing/__init__.py` | `peak_picker.py` | `from lucy_ng.processing.peak_picker import AdaptivePeakPicker, detect_intensity_symmetry` | WIRED | WR-02 fix: `detect_intensity_symmetry` in both import and `__all__` |

---

### Data-Flow Trace (Level 4)

Not applicable — this phase delivers algorithmic functions and agent skill files, not UI/rendering components. Data flow is verified via unit and CLI tests.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `detect_intensity_symmetry` importable from package | `python3 -c "from lucy_ng.processing import detect_intensity_symmetry; print('import OK')"` | `import OK` | PASS |
| `_compute_snr_threshold` importable from peak_picker | `from lucy_ng.processing.peak_picker import _compute_snr_threshold` (used in 7 tests, all passing) | Tests pass | PASS |
| CLI JSON includes `noise_sigma` and `snr` fields | `TestCLIPick1D` class (2 tests) | 2 passed | PASS |
| Full test suite unchanged | pytest 1037 passed, 7 skipped, 1 xfailed | All pass | PASS |

---

### Probe Execution

No probe scripts declared in any PLAN. Step 7c: SKIPPED (no probe-*.sh files for this phase).

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| FIX-04 | Plan 79-01 | SNR/MAD threshold; solvent exclusion; per-peak SNR annotation; backwards-compatible | SATISFIED | `_compute_snr_threshold` with `1.4826`; `_SOLVENT_EXCLUSION_13C` dict; `Peak1D.snr`; `use_snr=False` fallback; tests all green |
| FIX-05 | Plan 79-02 | 13C intensity 2C-equivalence detection for aromatic CH | SATISFIED | `detect_intensity_symmetry` function; exported from package; 5 tests all pass |
| FIX-06 | Plan 79-03 | DBE self-check + intensity-symmetry in nmr-chemist; QUALITY_CONVERGENCE_FAILURE 5th pattern in case/loop-patterns/advisory | SATISFIED | MANDATORY sections in nmr-chemist.md; all 4 skill files updated; wired as described |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

No TBD, FIXME, or XXX markers in any phase-modified file. No stub returns, no hardcoded empty data in production paths. The review-fix cycle (79-REVIEW-FIX.md) pre-emptively resolved 2 critical bugs (NaN threshold, to_dict silence) and 4 warnings (DEPTGuidedPicker off-by-one, missing __init__ export, fragile test thresholds, CD3CN dual-window). All 6 findings fixed, 0 skipped.

---

### Human Verification Required

#### 1. CASE9 Blind UAT (UAT-04 Milestone Gate)

**Test:** A fresh, untainted Claude instance runs the full /lucy-ng:case workflow on the CASE9 dataset at `~/Dropbox/develop/data/nmrdata/active-lucy-ng-testprojects/CASE9/` (4-(1-hydroxyethyl)benzoic acid isopropylester, C12H16O3, formula differs from CASE1). The orchestrating instance that worked on Phase 79 must NOT run this.

**Expected:**
- `lucy pick 1d` with default SNR mode picks the ester carbonyl at ~166 ppm (no forced threshold override needed)
- Intensity-symmetry check in nmr-chemist identifies the two 2C aromatic CH equivalence pairs and passes them to `lucy detect aromatic-cosy`
- Emergent-COSY mechanism activates (no forced ring-BOND required)
- RDKit confirms a C12H16O3 para-disubstituted aromatic ester SMILES in the ranked output
- If QUALITY_CONVERGENCE_FAILURE fires: exactly 1 re-examination cycle runs, then the carbonyl/symmetry correction resolves it (pattern fires at most once)
- All four Phase-71-style success criteria pass against on-disk artifacts

**Why human:** Per project protocol (feedback_blind_uat memory), the orchestrating Claude instance that developed Phase 79 is tainted and must not run this UAT. The test requires running the full autonomous CASE workflow end-to-end, including live NMR data outside the repository, and verifying structural correctness via independent RDKit check.

---

### Gaps Summary

No gaps. All 4 must-have truths are verified in the codebase. FIX-04, FIX-05, and FIX-06 are all substantively implemented and wired. The only outstanding item is the downstream blind UAT (UAT-04), which is a milestone gate by design — not a Phase 79 deliverable.

---

_Verified: 2026-06-08_
_Verifier: Claude (gsd-verifier)_
