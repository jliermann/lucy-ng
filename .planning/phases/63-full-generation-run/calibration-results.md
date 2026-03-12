# Threshold Calibration Results

**Date:** 2026-03-12
**Database:** data/reference/lucy-ng-derep.db (schema v7)
**Coupling path stats rows:** 3,775,564

---

## 1. Database Statistics

### Overview

| Metric | Value |
|--------|-------|
| Total compounds | 928,443 |
| Compounds processed | 895,099 |
| Compounds skipped (NULL atom indices) | 66,372 (7.2%) |
| Unique (carbon_hose, h_carbon_hose, bond_distance) entries | 3,775,564 |
| Unique (carbon_hose, h_carbon_hose) pairs | 2,869,850 |
| Total observations (sum of all counts) | 303,072,615 |

### Bond Distance Distribution

| Distance | Unique Pairs | Total Observations | % of Total |
|----------|-------------|-------------------|------------|
| 1 (direct bond) | 145,231 | 17,736,470 | 5.9% |
| 2 | 361,117 | 25,511,809 | 8.4% |
| 3 | 579,509 | 28,226,949 | 9.3% |
| 4 | 633,657 | 27,000,516 | 8.9% |
| 5+ (capped) | 2,056,050 | 204,596,871 | 67.5% |

**Key observation:** Distance 5+ accounts for 67.5% of all observations. This is expected — in any molecule larger than ~5 atoms, most pairs of atoms are 5+ bonds apart.

### Sparsity

- Avg observations per unique (carbon_hose, h_carbon_hose) pair: 105.6
- Min: 1, Max: 8,236,870
- Most pairs have sufficient data for analysis

---

## 2. Ibuprofen 4J Validation

### Test Case 1: ArCH(129.38) ↔ CH2(45.03)

```json
{
  "carbon_shift": 129.38,
  "h_carbon_shift": 45.03,
  "distribution": {
    "j2": 0.0693, "j3": 0.0978, "j4": 0.0867, "j5_plus": 0.7461
  },
  "total_observations": 478412,
  "risk_level": "likely_4j",
  "recommendation": "defer"
}
```

### Test Case 2: ArCH(127.26) ↔ CH(44.90)

```json
{
  "carbon_shift": 127.26,
  "h_carbon_shift": 44.90,
  "distribution": {
    "j2": 0.0628, "j3": 0.0899, "j4": 0.0890, "j5_plus": 0.7583
  },
  "total_observations": 467526,
  "risk_level": "likely_4j",
  "recommendation": "defer"
}
```

**Result:** Both ibuprofen 4J correlations correctly classified as `likely_4j`. The `must_haves` specification is technically satisfied.

---

## 3. False Positive Check — Non-Aromatic Pairs

### Test Case 3: Aliphatic CH–CH2 (35.0 ↔ 25.0)

```json
{
  "risk_level": "likely_4j",
  "distribution": {"j2": 0.1055, "j3": 0.0625, "j4": 0.1335, "j5_plus": 0.6984},
  "total_observations": 489685
}
```

### Test Case 4: Carbonyl–Methyl (170.0 ↔ 20.0)

```json
{
  "risk_level": "likely_4j",
  "distribution": {"j2": 0.0409, "j3": 0.0624, "j4": 0.0685, "j5_plus": 0.8281},
  "total_observations": 487714
}
```

### Test Case 5: CH3–CH (15.0 ↔ 40.0)

```json
{
  "risk_level": "likely_4j",
  "distribution": {"j2": 0.0056, "j3": 0.0565, "j4": 0.0694, "j5_plus": 0.8685},
  "total_observations": 45201
}
```

**Result: ALL non-aromatic pairs also return `likely_4j`. False positive rate = 100%.**

---

## 4. Root Cause Analysis

### Why p_long_range Fails as a Discriminator

The current `p_long_range = j4 + j5_plus` metric does not discriminate because:

1. **j5_plus dominates universally.** In any molecule larger than ~6 atoms, most pairs of atoms are 5+ bonds apart. The coupling_path_stats generator records ALL (carbon, proton-bearing-carbon) pairs — not just HMBC-relevant ones. This means j5_plus is typically 70-90% for ALL HOSE code pairs, regardless of chemical environment.

2. **The ±2 ppm HOSE code window is too broad.** Querying with a ±2 ppm window for typical shifts (e.g., 45 ppm) returns 10+ different HOSE codes covering many environments (chains, rings, branched aliphatics, etc.). The aggregated signal mixes all of them.

3. **j4 alone doesn't discriminate.** Even restricting to j4 fraction only: ibuprofen aromatic cases show j4 ≈ 8-9%, while aliphatic CH-CH2 shows j4 ≈ 13%. The direction is backwards — aliphatic pairs show *higher* j4 fraction.

4. **Conditional P(4J | HMBC) = j4/(j2+j3+j4) is also non-discriminating:**
   - ibuprofen ArCH cases: 34-37%
   - aliphatic CH-CH2: 44%
   - carbonyl-methyl: 40%
   - CH3-CH: 53%
   Again, the aliphatic cases appear MORE 4J-like by this metric.

### Why the Ibuprofen Cases "Work" Trivially

The ibuprofen cases correctly return `likely_4j` only because j4+j5+ > 0.5 universally for all tested pairs. The threshold is trivially satisfied — it would be satisfied for ANY pair in the database. This is not genuine detection; it is an artifact.

---

## 5. Threshold Assessment

**Default thresholds (likely >= 0.50, possible >= 0.15) are fundamentally broken against real data.**

The thresholds were designed when `p_long_range` was expected to be a meaningful probability, but the data shows it is ~0.75-0.95 for ALL pairs due to j5+ dominance.

### Options Evaluated

| Approach | Result |
|----------|--------|
| Default (j4+j5+ >= 0.50) | 100% false positive rate |
| Lower thresholds (e.g., >= 0.10) | Still 100% false positive (p_long_range still ~0.80) |
| j4-only (>= 0.05) | No discrimination; aliphatic > aromatic |
| Conditional P(4J\|2-4J) with any threshold | No clean separation |

No threshold combination on the current `p_long_range` metric produces correct behavior.

---

## 6. Required Fix: Architecture Change

The 4J detection requires a fundamentally different approach. The key options are:

### Option A: Restrict to HMBC-Relevant Distances Only (Recommended)

Change `p_long_range` to exclude j5_plus from the denominator AND numerator:
```
p_long_range_hmbc = j4 / (j2 + j3 + j4)
```
This uses only the HMBC-observable bond range (2-4 bonds). However, as shown above, this still doesn't discriminate well when using broad shift windows.

### Option B: Tighten HOSE Code Lookup (Recommended)

Reduce the shift window from ±2.0 ppm to ±0.5 ppm or tighter to get HOSE codes that better represent the specific chemical environment. At ±2 ppm, we average over too many different environments.

### Option C: Use Aromatic Ring Indicator (Most Effective)

The most reliable 4J W-pathway indicator is the **combination** of:
- Carbon shift in aromatic range (120-145 ppm, sp2=aromatic)
- H-carbon shift in aliphatic benzylic range (30-60 ppm)
- HOSE codes confirm: carbon_hose contains aromatic ring markers

This could be implemented as a separate rule-based path in the detection logic, rather than relying on statistical discrimination that doesn't exist in the aggregate data.

### Option D: Normalize Against Background (Partial Fix)

For each HOSE pair, compute:
```
signal = j4 / (j4 of "background" for similar shift patterns)
```
This would require computing the expected j4 fraction for randomly co-occurring pairs and normalizing against it. Complex to implement.

---

## 7. Summary

| Criterion | Status |
|-----------|--------|
| Database populated (3,775,564 entries) | PASS |
| Ibuprofen ArCH↔CH2 classified as likely_4j | PASS (trivially — all pairs get this) |
| Ibuprofen ArCH↔CH classified as likely_4j | PASS (trivially — all pairs get this) |
| Non-aromatic pairs classified as unlikely_4j | FAIL — 100% false positive rate |
| Thresholds calibrated and discriminating | FAIL |
| Database schema and data quality | PASS |

**Conclusion:** The database is correctly populated and the data quality is good. However, the detection algorithm's `p_long_range` metric does not discriminate between genuine 4J risk and non-4J correlations because j5_plus dominates universally. A threshold-only fix is not sufficient. An architectural change to the detection algorithm is required before the 4J detection is useful in practice.

**For Phase 64 UAT:** The detection engine should be fixed before UAT, otherwise ibuprofen CASE will defer all HMBC correlations (100% false positive). Recommended fix: implement Option C (aromatic context check) combined with Option B (tighter shift window).

---

## 8. Tests Status

All 41 existing tests in `tests/test_detection_4j.py` pass. These tests use synthetic data with controlled HOSE code distributions and are not affected by the production data calibration issue.

The tests correctly validate the classification logic (j4 fraction correctly causes likely_4j/possible_4j/unlikely_4j given known distributions). The issue is that the production data doesn't produce the expected j4 distributions.
