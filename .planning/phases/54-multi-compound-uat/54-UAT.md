# Phase 54: Multi-Compound UAT Report

**Date:** 2026-02-20
**Fragment DB:** 2,385,146 SSCs from 928,443 compounds
**Self-search recall:** 100% (100/100 compounds on 1K sample)
**Milestone:** v5.0 Fragment Library

## Summary

{To be filled after all CASE runs}

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

## Test Compound Matrix

| # | Compound | Formula | Heavy atoms | Rings | 4J Risk | Baseline solutions | Fragment solutions | Delta | Fragment conflicts | Diagnosis |
|---|----------|---------|-------------|-------|---------|-------------------|-------------------|-------|-------------------|-----------|
| 1 | Ibuprofen | C13H18O2 | 15 | 1 | HIGH (KNOWN) | - | - | - | - | - |
| 2 | MC047_9 | C10H14O2 | 12 | 1 | HIGH | - | - | - | - | - |
| 3 | PSP | C12H12O5 | 17 | 1 | HIGH | - | - | - | - | - |
| 4 | Sali_Eth | C18H20N2 | 20 | 2 | HIGH | - | - | - | - | - |
| 5 | 4-Hydroxy-3-Iodo-biphenyl | C12H9IO | 14 | 2 | MEDIUM | - | - | - | - | - |
| 6 | HEB | C12H16O3 | 15 | 1 | HIGH | - | - | - | - | - |

## Per-Compound Results

### 1. Ibuprofen (C13H18O2) -- EXPECTED 4J FAILURE

**Known:** v4.0 UAT confirmed 3 W-pathway 4J HMBC couplings cause LSD to miss correct structure.

#### Baseline (no fragments)
- Solution count: -
- Aromatic ring warning: -
- Notes: -

#### With fragments
- Solution count: -
- Fragment applied: -
- Fragment conflicts: -
- Aromatic ring warning: -
- Notes: -

#### Diagnosis
{4J failure / fragment gap / success}

### 2. MC047_9 (C10H14O2)

**Note:** Pyranone ring (not benzene). May have lower 4J risk.

#### Baseline (no fragments)
- Solution count: -
- Aromatic ring warning: -
- Notes: -

#### With fragments
- Solution count: -
- Fragment applied: -
- Fragment conflicts: -
- Aromatic ring warning: -
- Notes: -

#### Diagnosis
{4J failure / fragment gap / success}

### 3. PSP (C12H12O5)

**Note:** No DEPT-135 -- relies on edited HSQC for multiplicities.

#### Baseline (no fragments)
- Solution count: -
- Aromatic ring warning: -
- Notes: -

#### With fragments
- Solution count: -
- Fragment applied: -
- Fragment conflicts: -
- Aromatic ring warning: -
- Notes: -

#### Diagnosis
{4J failure / fragment gap / success}

### 4. Sali_Eth (C18H20N2)

**Note:** Largest compound (20 heavy atoms, 2 rings). No DEPT-135.

#### Baseline (no fragments)
- Solution count: -
- Aromatic ring warning: -
- Notes: -

#### With fragments
- Solution count: -
- Fragment applied: -
- Fragment conflicts: -
- Aromatic ring warning: -
- Notes: -

#### Diagnosis
{4J failure / fragment gap / success}

### 5. 4-Hydroxy-3-Iodo-biphenyl (C12H9IO)

**Note:** Contains iodine. Biphenyl = two aromatic rings. No DEPT-135.

#### Baseline (no fragments)
- Solution count: -
- Aromatic ring warning: -
- Notes: -

#### With fragments
- Solution count: -
- Fragment applied: -
- Fragment conflicts: -
- Aromatic ring warning: -
- Notes: -

#### Diagnosis
{4J failure / fragment gap / success}

### 6. HEB (C12H16O3)

**Note:** Full name: 4-(1-Hydroxyethyl)benzoic acid isopropylester. Non-standard experiment numbering (HSQC=/5, HMBC=/4, COSY=/8, DEPT=/13).

#### Baseline (no fragments)
- Solution count: -
- Aromatic ring warning: -
- Notes: -

#### With fragments
- Solution count: -
- Fragment applied: -
- Fragment conflicts: -
- Aromatic ring warning: -
- Notes: -

#### Diagnosis
{4J failure / fragment gap / success}

## Aggregate Results

| Metric | Value |
|--------|-------|
| Compounds tested | - / 6 |
| Solution count reduced | - / 6 |
| Correct structure found (any rank) | - / 6 |
| 4J HMBC failures | - |
| Fragment library gaps | - |
| Fragment conflict rate (avg) | - |

## Conclusions

### Fragment Library Impact
{Summary of solution count reduction across compounds}

### 4J HMBC vs Fragment Library Gaps
{Analysis distinguishing the two failure modes}

### Recommendations for v5.1
{Based on findings}

---
*UAT conducted: 2026-02-20*
