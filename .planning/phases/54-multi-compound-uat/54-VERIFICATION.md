---
phase: 54-multi-compound-uat
verified: 2026-02-21T14:30:00Z
status: gaps_found
score: 3/5 must-haves verified
re_verification: false
gaps:
  - truth: "5+ compounds have CASE results recorded with solution counts"
    status: failed
    reason: "VALD-01 deferred -- 0 compounds tested with CASE. All 6 local compounds have 4J HMBC coupling risk, making controlled A/B comparison unreliable."
    artifacts:
      - path: ".planning/phases/54-multi-compound-uat/54-UAT.md"
        issue: "UAT report exists but contains no CASE run results -- all compound rows show 'Deferred'"
    missing:
      - "CASE runs on 5+ compounds (baseline + fragment-enhanced) with solution count comparison"
      - "Non-aromatic test compounds that isolate fragment impact from 4J HMBC interference"
  - truth: "At least 3 compounds show solution count reduction with fragments"
    status: failed
    reason: "Zero compounds tested -- cannot measure solution count reduction. Dependent on VALD-01 which is deferred."
    artifacts: []
    missing:
      - "Actual CASE run data showing before/after fragment injection solution counts"
human_verification:
  - test: "Run CASE on a non-aromatic compound with and without fragment DB to measure solution count delta"
    expected: "Fragment-enhanced run produces fewer solutions than baseline"
    why_human: "Requires interactive CASE agent session (~30 min per compound per mode) and suitable non-aromatic test compound"
---

# Phase 54: Multi-Compound UAT Verification Report

**Phase Goal:** Fragment library reduces solution counts across 5+ test compounds -- self-search recall confirmed >99%, real CASE runs show measurable solution count reduction
**Verified:** 2026-02-21T14:30:00Z
**Status:** gaps_found
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

The phase has 5 success criteria from the ROADMAP:

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Self-search validation: 100 compounds' own spectra find their own SSCs with >99% recall | VERIFIED | Plan 01 SUMMARY reports 100.0% (100/100). Fragment DB confirmed at 2,385,146 SSCs from 928,443 compounds. `lucy fragment search` returns results for test queries. |
| 2 | 5+ compounds from Sherlock test set run with full CASE pipeline; solution counts before and after fragment injection recorded and compared | FAILED | 0 compounds tested. VALD-01 deferred. UAT report contains only the scaffold with "Deferred" status on all 6 compounds. |
| 3 | At least 3 of 5 test compounds show a reduction in final solution count when fragment injection is active | FAILED | Cannot be assessed -- no CASE runs performed. |
| 4 | Fragment conflict rate logged per compound | PARTIAL | No CASE runs to generate conflict data. However, the lsd-engineer agent file contains full conflict logging workflow (zero-solution fallback protocol, `deff_fexp` inventory tracking). Infrastructure is wired but untested on real compounds. |
| 5 | UAT report identifies which failures are 4J HMBC vs fragment library gaps | VERIFIED | UAT report (54-UAT.md) provides thorough analysis: all 6 compounds assessed for 4J risk (5 HIGH, 1 MEDIUM), explicit distinction between 4J HMBC failure mode and fragment library gaps, recommendations for SYS-01 as prerequisite. The report correctly identifies the confounding variable problem. |

**Score:** 3/5 truths verified (counting Truth 4 as partial -- infrastructure present but untested)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `data/reference/lucy-ng-fragments.db` | Fragment DB with millions of SSCs | VERIFIED | 605.3 MB, 2,385,146 SSCs, schema v7, bin size 2.0 ppm. Confirmed via `lucy fragment info` and direct file check. |
| `.planning/phases/54-multi-compound-uat/54-UAT.md` | UAT report with compound-by-compound results | PARTIAL | File exists (5,158 bytes). Structure is complete. Self-search and LSD smoke test sections filled in. Per-compound CASE results section is entirely deferred -- no actual CASE data recorded. |
| Agent files (lsd-engineer, devils-advocate, orchestrator) | Fragment search wired into CASE pipeline | VERIFIED | `lucy-lsd-engineer.md` has full fragment search workflow (lines 124-433+), `lucy-devils-advocate.md` has DEFF F file existence check and ordering validation, `case.md` orchestrator logs fragment search/file/DEFF FEXP per iteration. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `lucy fragment build --sample 1000` | `data/reference/lucy-ng-fragments.db` | BFS extraction with self-search validation | VERIFIED | DB populated with 2.4M SSCs. CLI help confirms `--sample` and `--fresh` options. |
| `lucy fragment search` | Fragment DB | Bitset pre-screening + fine matching | VERIFIED | Live test with ibuprofen shifts returned 210 fine matches, 3 top fragments. Command produces JSON output. |
| `lucy fragment to-lsd` | DEFF/FEXP LSD file | SMILES to SSTR/LINK conversion | VERIFIED | Live test with benzene produced valid fragment file with 6 SSTR atoms, 6 LINK bonds, correct DEFF F1/FEXP commands. |
| lsd-engineer | `lucy fragment search` | Agent runs search per iteration | WIRED | Agent file contains explicit workflow: search -> to-lsd -> DEFF/FEXP injection before MULT, zero-solution fallback, inventory tracking. |
| devils-advocate | Fragment .lsd file | Verifies file exists before approving LSD run | WIRED | Agent file contains DEFF F file existence check (line 172-180), ordering validation (DEFF F before MULT, line 184-189). |
| `/lucy-ng:case` | CASE-PROGRESS.md per compound | Logs fragment search results per iteration | WIRED | Orchestrator logs Fragment search, Fragment file, DEFF FEXP fields per iteration. |
| 54-UAT.md | CASE-PROGRESS.md per compound | Aggregated results | NOT WIRED | No CASE runs occurred, so no CASE-PROGRESS.md files exist to aggregate from. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-----------|-------------|--------|----------|
| VALD-01 | 54-02 | Multi-compound UAT on 5+ compounds with solution count before/after fragment injection | DEFERRED | 0 compounds tested. All 6 local compounds have 4J HMBC risk. REQUIREMENTS.md shows "Pending". |
| VALD-02 | 54-01 | Self-search validation: 100 compounds' own spectra must find their own SSCs (>99% recall) | SATISFIED | 100% recall (100/100) on 1K sample. REQUIREMENTS.md shows "Complete" with checkbox. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| 54-UAT.md | 59 | "Compounds tested (CASE runs): 0 / 6 (deferred)" | WARNING | Primary UAT metric is empty -- no actual CASE comparison data exists |
| 54-02-SUMMARY.md | 27 | "requirements-completed: []" | INFO | Correctly reflects that VALD-01 is not complete (honest reporting) |
| 54-02-SUMMARY.md | 50 | "Task 2 checkpoint skipped by user" | INFO | The blocking task (actual CASE runs) was bypassed |

No TODO/FIXME/placeholder markers found in any phase files. No stub implementations detected. The 860 tests all pass (7 skipped, 0 failures). The test count discrepancy (summary claims 860, pytest shows 867 collected / 860 passed / 7 skipped) is consistent -- the 7 skipped tests are counted differently.

### Human Verification Required

### 1. Fragment Library Impact on Non-Aromatic Compound

**Test:** Obtain or identify a non-aromatic test compound (e.g., an aliphatic natural product without benzylic substituents). Run `/lucy-ng:case` twice: once with fragment DB renamed away (baseline), once with fragment DB in place. Compare solution counts.
**Expected:** Fragment-enhanced run produces fewer solutions than baseline. Correct structure appears at higher rank with fragments.
**Why human:** Requires interactive CASE agent session (~30 min per run), suitable test compound selection, and manual result comparison.

### 2. LSD Smoke Test Reproducibility

**Test:** Run the toluene smoke test described in the summary: create a minimal toluene LSD file, run LSD without fragments (expect ~4 solutions), then with benzene ring fragment (expect 1 solution).
**Expected:** Solution count decreases from ~4 to 1 when benzene ring goodlist is applied.
**Why human:** Requires manual LSD file creation and solver interaction. The summary claims this was done but no artifacts (LSD files, solution files) were preserved.

### Gaps Summary

The phase has a **split outcome**: infrastructure is complete and validated, but the primary UAT comparison (VALD-01) was never executed.

**What passed:**
- Fragment database fully populated (2.4M SSCs from 928K compounds)
- Self-search recall 100% (VALD-02 satisfied)
- Full pipeline working end-to-end: build, search, to-lsd, agent integration
- 860 tests passing
- Agent files thoroughly wired with fragment support

**What failed:**
- Zero compounds tested with actual CASE pipeline (VALD-01 deferred)
- No empirical evidence that fragment injection reduces solution counts on real compounds
- The phase goal explicitly requires "real CASE runs show measurable solution count reduction" -- this did not happen

**Root cause:** All 6 locally available test compounds are aromatic with benzylic substituents, placing them at HIGH risk for the known 4J HMBC coupling failure (confirmed in v4.0 UAT). The deferral rationale is scientifically sound -- running A/B tests on these compounds would conflate fragment injection with 4J HMBC exclusion, producing misleading results. However, this is a test compound availability problem, not a code deficiency.

**Path to closure:**
1. Obtain non-aromatic test compounds (aliphatic natural products, compounds without benzylic substituents)
2. Alternatively, implement SYS-01 (statistical 4J HMBC detection) first, then re-run UAT on existing aromatic compounds
3. A single successful A/B comparison on one clean compound would significantly strengthen the validation

---

_Verified: 2026-02-21T14:30:00Z_
_Verifier: Claude (gsd-verifier)_
