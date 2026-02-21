# Phase 54: Multi-Compound UAT Report

**Date:** 2026-02-21
**Fragment DB:** 2,385,146 SSCs from 928,443 compounds
**Self-search recall:** 100% (100/100 compounds on 1K sample)
**Milestone:** v5.0 Fragment Library

## Summary

Fragment library infrastructure is complete and validated. The pipeline (extraction, search, DEFF formatting, agent integration) is fully built, tested (860 tests), and wired into the CASE agent team. Self-search recall is 100%. Comparative CASE runs (with/without fragments) are deferred to incremental testing during normal use — all 6 available test compounds carry 4J HMBC coupling risk, making controlled A/B comparison unreliable for measuring fragment impact in isolation.

## Fragment DB Statistics

| Metric | Value |
|--------|-------|
| SSC count | 2,385,146 |
| Schema version | 7 |
| Bin size | 2.0 ppm |
| DB file size | 605.3 MB |
| Source compounds | 928,443 (COCONUT + NMRShiftDB) |
| Duplicates filtered | ~46.7M |
| Self-search recall | 100% (100/100) |

## Validation Results

### VALD-02: Self-Search Recall (PASSED)

100 compounds' own spectra searched against the fragment library. All 100 found their own SSCs. Recall = 100%, exceeding the >99% requirement. This confirms fingerprint indexing and Boolean AND pre-screening are correct.

### VALD-01: Multi-Compound CASE Comparison (DEFERRED)

**Reason for deferral:** All 6 locally available test compounds are aromatic with benzylic substituents, placing them at HIGH risk for 4J HMBC coupling interference (the known v4.0 failure mode). Running controlled A/B tests on these compounds would conflate two independent variables — fragment injection and 4J HMBC exclusion — making it impossible to isolate fragment library impact.

**What was validated instead:**
1. Fragment extraction pipeline processes 928K compounds to completion (3.5 hours, checkpointed)
2. Self-search recall is 100% on the populated database
3. `lucy fragment search` returns ranked fragments with DEFF/FEXP commands
4. `lucy fragment to-lsd` generates valid LSD fragment files (LSD smoke test passed — toluene: 4 solutions baseline, 1 with benzene ring goodlist)
5. Agent integration complete (lsd-engineer, devils-advocate, orchestrator all updated)
6. LSD goodlist semantics verified via smoke test (not accidentally acting as badlist)

**Recommended path to full VALD-01:** Obtain test compounds WITHOUT 4J HMBC risk (e.g., non-aromatic natural products, or aromatic compounds without benzylic substituents). Alternatively, implement statistical 4J detection (SYS-01) first, then re-run UAT.

## Test Compound Matrix

| # | Compound | Formula | Heavy atoms | Rings | 4J Risk | Status |
|---|----------|---------|-------------|-------|---------|--------|
| 1 | Ibuprofen | C13H18O2 | 15 | 1 | HIGH (KNOWN) | Deferred — confirmed 4J failure in v4.0 |
| 2 | MC047_9 | C10H14O2 | 12 | 1 | HIGH | Deferred — aromatic with benzylic |
| 3 | PSP | C12H12O5 | 17 | 1 | HIGH | Deferred — aromatic |
| 4 | Sali_Eth | C18H20N2 | 20 | 2 | HIGH | Deferred — aromatic |
| 5 | 4-Hydroxy-3-Iodo-biphenyl | C12H9IO | 14 | 2 | MEDIUM | Deferred — biphenyl |
| 6 | HEB | C12H16O3 | 15 | 1 | HIGH | Deferred — aromatic with benzylic |

## Aggregate Results

| Metric | Value |
|--------|-------|
| Compounds tested (CASE runs) | 0 / 6 (deferred) |
| Self-search validated | 100 / 100 |
| LSD smoke test (goodlist semantics) | PASSED |
| Pipeline integration tests | 860 passed, 0 failed |
| Agent files updated | 3 / 3 |

## Conclusions

### Fragment Library Impact

The fragment library is **infrastructure-complete**. All components are built, tested, and integrated:
- 2.4M unique SSCs from 928K compounds
- Two-phase search (bitset pre-screening + fine matching) with DEV/AVGDEV thresholds
- DEFF/FEXP goodlist generation validated against actual LSD solver
- Agent team wired to use fragments on every iteration

Impact measurement requires test compounds that isolate fragment benefit from 4J HMBC interference.

### 4J HMBC as the Dominant Blocker

The 4J HMBC coupling problem (v4.0 finding) remains the primary blocker for successful CASE on aromatic compounds. All 6 available test compounds are aromatic. Until statistical 4J detection (SYS-01) is implemented, fragment injection cannot be meaningfully evaluated on these compounds because the 4J exclusion prevents the correct structure from appearing in the solution set regardless of fragment constraints.

### Recommendations for v5.1

1. **SYS-01: Statistical 4J HMBC detection** — Highest priority. Without this, fragment library benefits are masked by 4J failures on aromatic compounds
2. **Obtain non-aromatic test compounds** — Aliphatic natural products would allow clean fragment impact measurement
3. **Fragment library will be tested incrementally** — As new compounds are elucidated, fragment impact data will accumulate naturally

**UAT Status: PARTIAL** — Self-search validation PASSED (VALD-02). Multi-compound CASE comparison deferred (VALD-01) due to all available compounds having 4J HMBC risk. Fragment library infrastructure is complete and ready for use.

---
*UAT conducted: 2026-02-21*
