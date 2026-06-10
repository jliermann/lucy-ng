---
phase: 81-peak-picking-integrity-fix-08
verified: 2026-06-10T00:00:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification: null
gaps: []
human_verification:
  - test: "Blind re-UAT of CASE9 + CASE1 by fresh instances"
    expected: "Both cases produce RDKit-verified aromatic structures via the emergent path with 0 bypass interventions; AND-gate records v9.0 ship decision"
    why_human: "Per feedback_blind_uat, UAT must be run by tainted-context-free fresh Claude instances. This is the downstream milestone gate, not a Phase-81 code deliverable."
---

# Phase 81: Peak-Picking Integrity (FIX-08) Verification Report

**Phase Goal:** Make 13C peak-picking deterministically separate signal from noise so a fresh blind
agent always receives the ~12 real carbons (including weak quaternary carbonyls) and never a
76-peak noise list.

**Verified:** 2026-06-10
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `AdaptivePeakPicker.pick_peaks` and `pick_peaks_instance` default `snr_floor=5.0` | VERIFIED | `inspect.signature` shows `snr_floor: float = 5.0` at lines 162 and 199 of `peak_picker.py`; `test_case9_default_snr_is_5` PASS |
| 2 | `lucy pick 1d --snr-floor` / `-s` flag exposed and wired to picker | VERIFIED | `lucy pick 1d --help` shows `-s, --snr-floor FLOAT`; CLI logic routes to `AdaptivePeakPicker.pick_peaks(snr_floor=snr_floor)`; `test_cli_pick.py` 17/17 PASS |
| 3 | Overcount alarm fires in both `analyze_symmetry` CLI and `SymmetryAnalysisResult.summary()` | VERIFIED | `analyze.py` line 72: `"overcount_alarm": difference < 0`; `symmetry_analysis.py` line 54–59: `if self.missing_carbons < 0: … "OVERCOUNT ALARM: …"`; 8 overcount tests PASS |
| 4 | nmr-chemist skill encodes: SNR≥5=signal, overcount=noise, carbonyl-never-discard | VERIFIED | `lucy-nmr-chemist.md` lines 65–76: Pitfall 10 (SNR floor CRITICAL) + Pitfall 11 (Carbonyl never discard); line 97–98: explicit SNR≥5 cutoff note before quality tiers table |
| 5 | Regression test `tests/test_peak_picking_integrity.py`: CASE9@k=5 ≤30 peaks, carbonyl present, none >230 ppm; overcount guard fires on 76-vs-12; CASE1 not regressed | VERIFIED | All 8 tests PASS (pytest run 2026-06-10): 4 CASE9 integration tests + 3 overcount guard tests + 1 CASE1 regression floor |

**Score:** 5/5 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/lucy_ng/processing/peak_picker.py` | `snr_floor=5.0` in `pick_peaks` and `pick_peaks_instance` | VERIFIED | Lines 162 + 199 confirmed via grep + `inspect.signature` |
| `src/lucy_ng/cli/pick.py` | `--snr-floor / -s` Click option, `snr_floor_used` in JSON output | VERIFIED | Lines 30–35 (option decl), lines 72–78 (routing), lines 90–95 (snr_floor_used); `lucy pick 1d --help` output confirms flag visible |
| `src/lucy_ng/cli/analyze.py` | `overcount_alarm` + `overcount_excess` in JSON; Warning text with "more signals than carbons" | VERIFIED | Lines 72–74 (JSON fields), lines 83–88 (text branch with Warning + re-pick advice) |
| `src/lucy_ng/analysis/symmetry_analysis.py` | `OVERCOUNT ALARM` branch for `missing_carbons < 0` in `summary()` | VERIFIED | Lines 54–59: `if self.missing_carbons < 0` produces "OVERCOUNT ALARM: N more signals than carbons…" |
| `/Users/steinbeck/.claude/agents/lucy-nmr-chemist.md` | Pitfall 10 (SNR≥5), Pitfall 11 (carbonyl), Section 4 SNR cutoff note | VERIFIED | Lines 65–76 (Pitfall 10 + 11); lines 97–98 (Section 4 SNR cutoff); 4 occurrences of "SNR >= 5" |
| `tests/test_peak_picking_integrity.py` | 8 tests: 4 CASE9 integration + 3 overcount + 1 CASE1 regression | VERIFIED | 155 lines, 8 test methods; all 8 PASS (0 skipped — CASE9 data present on this machine) |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `lucy pick 1d --snr-floor N` | `AdaptivePeakPicker.pick_peaks(snr_floor=N)` | `pick.py` lines 72–78 | WIRED | `elif snr_floor is not None: peaks = AdaptivePeakPicker.pick_peaks(..., snr_floor=snr_floor, use_snr=True)` |
| Default `lucy pick 1d` | `AdaptivePeakPicker.pick_peaks()` with new default 5.0 | `pick.py` lines 80–84 | WIRED | No-arg call uses method default; `snr_floor_used=5.0` computed at line 95 |
| `analyze symmetry` CLI | `overcount_alarm` field | `analyze.py` lines 72–74 | WIRED | `"overcount_alarm": difference < 0` in JSON output dict |
| `SymmetryAnalysisResult.summary()` | OVERCOUNT ALARM text | `symmetry_analysis.py` lines 54–59 | WIRED | `if self.missing_carbons < 0` branch fires before existing `elif > 0` branch |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `snr_floor` default is 5.0 | `python -c "import inspect; from lucy_ng.processing.peak_picker import AdaptivePeakPicker; print(inspect.signature(AdaptivePeakPicker.pick_peaks))"` | `snr_floor: float = 5.0` in signature | PASS |
| `--snr-floor` flag visible in CLI | `lucy pick 1d --help` | `-s, --snr-floor FLOAT  SNR floor multiplier k (default: 5.0 ...)` | PASS |
| CASE9 integration tests (all 4) | `pytest tests/test_peak_picking_integrity.py::TestFIX08CASE9Integration -v` | 4/4 PASSED | PASS |
| Overcount guard fires | `pytest tests/test_peak_picking_integrity.py::TestFIX08OvercountGuard -v` | 3/3 PASSED | PASS |
| CASE1 not regressed | `pytest tests/test_peak_picking_integrity.py::TestFIX08CASE1Regression -v` | 1/1 PASSED | PASS |
| All affected test modules | `pytest tests/test_peak_picker_snr.py tests/test_cli_pick.py tests/test_cli_analyze.py tests/test_symmetry_analysis.py -q` | 63 passed | PASS |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|------------|------------|-------------|--------|----------|
| FIX-08(a) | 81-01 | `snr_floor` default 3→5 in `peak_picker.py` | SATISFIED | Lines 162 + 199 both show `snr_floor: float = 5.0` |
| FIX-08(b) | 81-01 | `--snr-floor` CLI flag in `lucy pick 1d` | SATISFIED | Click option declared, wired, `snr_floor_used` in JSON |
| FIX-08(c) | 81-02 | Overcount guard in `analyze.py` + `symmetry_analysis.py` | SATISFIED | Both files have `missing_carbons < 0` branch with alarm text |
| FIX-08(d) | 81-03 | nmr-chemist SNR/overcount/carbonyl rules | SATISFIED | Pitfall 10 + 11 + Section 4 SNR cutoff note all present |
| FIX-08(e) | 81-04 | `tests/test_peak_picking_integrity.py` regression suite | SATISFIED | 8 tests, all PASS, CASE9 external data present and tested |

---

## Anti-Patterns Found

No blockers found. Pre-existing ruff E501 / I001 violations in `cli/pick.py`, `symmetry_analysis.py`, and `cli/lsd.py` are documented in 81-01 and 81-02 SUMMARYs as pre-existing (not introduced by this phase) and are tracked in deferred-items.md. They do not affect functionality.

---

## Human Verification Required

### 1. Blind re-UAT: CASE9 + CASE1 (milestone AND-gate)

**Test:** Run `/lucy-ng:case` on CASE9 (C12H16O3) and CASE1 (C13H18O2) using fresh blind Claude instances (zero context of this codebase). Verify solutions via `scripts/verify_case_solution.py`. Apply the Phase-78 AND-gate: both must pass for v9.0 to ship.

**Expected:** CASE9 picks ~12 peaks including the ester carbonyl at ~166 ppm (no 76-peak noise list); DBE is correctly allocated as benzene(4)+C=O(1); the para-benzoate `CC(C)OC(=O)c1ccc(C(C)O)cc1` appears in LSD solutions. Both CASE1 and CASE9 produce RDKit-verified aromatic structures via the emergent path with 0 bypass interventions.

**Why human:** Per `feedback_blind_uat`, UAT must be run by tainted-context-free fresh Claude instances. This is the downstream milestone gate, not a Phase-81 code deliverable — the phase scope boundary explicitly excludes it.

---

## Gaps Summary

No gaps. All five FIX-08 scope items (a–e) are verified present, substantive, wired, and test-confirmed in the codebase.

**Outstanding milestone gate (separate from this phase):** The blind re-UAT on CASE9 + CASE1 by fresh instances, as required by `feedback_blind_uat` and documented as Phase 81's exit gate in ROADMAP.md, has not been run. This is not a gap in Phase 81's deliverables — it is the downstream v9.0 ship-gate that follows after Phase 81's code fixes are confirmed. Once the blind UAT passes the AND-gate, v9.0 ships.

---

_Verified: 2026-06-10_
_Verifier: Claude (gsd-verifier)_
