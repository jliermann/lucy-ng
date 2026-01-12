# AI Guide to Computer-Assisted Structure Elucidation

This document serves as a comprehensive guide for AI agents performing structure elucidation using lucy-ng. It covers the scientific background, workflow best practices, common pitfalls, and decision-making strategies.

## Table of Contents

- [Overview](#overview)
- [The Structure Elucidation Workflow](#the-structure-elucidation-workflow)
- [Understanding NMR Data](#understanding-nmr-data)
- [Critical Pitfalls and Solutions](#critical-pitfalls-and-solutions)
- [Step-by-Step Guide](#step-by-step-guide)
- [Decision Trees](#decision-trees)
- [Interpreting Results](#interpreting-results)
- [Example Reasoning](#example-reasoning)

---

## Overview

### What is Structure Elucidation?

Structure elucidation is the process of determining the molecular structure of an unknown compound from spectroscopic data. In organic chemistry, this typically involves:

1. **Molecular formula** - From high-resolution mass spectrometry (provided by the user)
2. **1D NMR spectra** - 1H (proton) and 13C (carbon) spectra showing chemical shifts
3. **2D NMR spectra** - Correlation experiments (HSQC, HMBC, COSY) showing atom connectivity

### Your Role as an AI Agent

You assist chemists by:
- Processing and interpreting NMR data systematically
- Checking if the compound matches known structures (dereplication)
- Generating structural constraints for solver programs
- Explaining your reasoning and flagging ambiguities

### Key Principle: Be Conservative

**Always prefer known compounds over de novo structure determination.** Dereplication (database matching) is faster, more reliable, and avoids the combinatorial explosion of possible structures. Only proceed to full structure elucidation if dereplication fails.

---

## The Structure Elucidation Workflow

### Recommended Order of Operations

```
1. DEREPLICATION FIRST
   └── Match against known compounds database
   └── If match found → DONE (report the known structure)
   └── If no match → Continue to step 2

2. GATHER ALL DATA
   └── Read all available spectra (1D and 2D)
   └── Identify experiment types (13C, DEPT, HSQC, HMBC, etc.)
   └── Note what data is available vs. missing

3. ANALYZE SYMMETRY
   └── Compare expected atoms (from formula) with observed signals
   └── Detect molecular symmetry
   └── This affects all subsequent analysis

4. PICK PEAKS SYSTEMATICALLY
   └── 13C spectrum → all carbon positions
   └── DEPT-135 → protonated carbons with multiplicity
   └── HSQC (DEPT-guided) → direct C-H correlations
   └── HMBC (guided) → long-range C-H correlations

5. GENERATE LSD INPUT
   └── Create constraint file from spectroscopic data
   └── Include molecular formula, atom definitions, correlations

6. RUN LSD SOLVER
   └── Execute constraint-based structure generation
   └── Analyze number of solutions

7. RANK SOLUTIONS (if multiple)
   └── Use predict_c13_shifts or rank_lsd_solutions
   └── Compare predicted vs experimental 13C shifts
   └── Sort by MAE (Mean Absolute Error)

8. EVALUATE RESULTS
   └── Single solution → High confidence
   └── Few solutions → Analyze differences, rank by prediction
   └── Many solutions → Need more constraints or data
```

### Why This Order Matters

- **Dereplication first**: ~80% of natural products are rediscoveries. Database matching takes seconds; full elucidation takes minutes to hours.
- **Symmetry before peak picking**: Understanding symmetry prevents confusion about "missing" signals.
- **Guided peak picking**: Using 1D data to filter 2D peaks dramatically reduces noise and false correlations.

---

## Understanding NMR Data

### Experiment Types and What They Tell You

| Experiment | Information Provided | Key Insight |
|------------|---------------------|-------------|
| **1H** | Proton chemical shifts | Hydrogen environment |
| **13C** | Carbon chemical shifts | All carbons including quaternary |
| **DEPT-135** | Protonated carbons only | CH/CH3 positive, CH2 negative |
| **DEPT-90** | CH only | Distinguishes CH from CH3 |
| **HSQC** | Direct C-H connections | Which H is attached to which C |
| **HMBC** | 2-3 bond C-H correlations | Connectivity through bonds |
| **COSY** | H-H correlations | Adjacent protons |

### Chemical Shift Regions (13C)

| Region (ppm) | Typical Assignment |
|--------------|-------------------|
| 0-50 | Aliphatic carbons (CH3, CH2, CH) |
| 50-90 | Carbons attached to oxygen (C-O) |
| 90-120 | Anomeric carbons, alkenes |
| 120-160 | Aromatic carbons, alkenes |
| 160-180 | Carboxylic acids, esters, amides |
| 180-220 | Aldehydes, ketones |

### What Each Lucy-ng Tool Returns

| Tool | Key Output Fields |
|------|------------------|
| `read_spectrum_1d` | nucleus, frequency, ppm_range, data_points |
| `pick_peaks_1d` | peaks (ppm, intensity), count |
| `pick_hsqc_peaks` | peaks (carbon_ppm, proton_ppm), multiplicities |
| `pick_hmbc_peaks` | peaks (carbon_ppm, proton_ppm), validated_count |
| `analyze_symmetry` | expected_carbons, observed_carbons, symmetry_detected |
| `dereplicate_c13` | is_match, top_matches (name, smiles, score) |
| `predict_c13_shifts` | predictions (atom_index, shift, confidence), success |
| `rank_lsd_solutions` | ranked_solutions (smiles, mae, matched_count), total_ranked |

---

## Critical Pitfalls and Solutions

### Pitfall 1: Signal Count ≠ Atom Count

**The Problem**: The molecular formula says C13H18O2 (13 carbons), but you only see 10-11 peaks in the 13C spectrum.

**Why This Happens**: Molecular symmetry causes equivalent atoms to produce identical signals that overlap.

**Example - Ibuprofen**:
```
Molecular formula: C13H18O2
Expected carbons: 13
Observed 13C signals: ~11

The "missing" carbons are due to:
- Para-disubstituted benzene ring
- Two ortho CH carbons are equivalent → 1 signal
- Two meta CH carbons are equivalent → 1 signal
```

**What To Do**:
1. Use `analyze_symmetry` to detect discrepancies
2. Look at HSQC intensities - doubled signals have ~2x intensity
3. Consider common symmetric motifs:
   - Para-substituted benzene (2 pairs of equivalent CH)
   - Isopropyl groups (2 equivalent CH3)
   - Gem-dimethyl groups (2 equivalent CH3)
   - Symmetric ethers/esters

**Key Insight**: If formula hydrogens > sum of (multiplicity × count) from HSQC, you have equivalent positions.

### Pitfall 2: Quaternary Carbons Are Invisible in DEPT/HSQC

**The Problem**: Some carbons appear in the 13C spectrum but have no HSQC correlation.

**Why This Happens**: Quaternary carbons (C with no attached H) don't appear in DEPT or HSQC experiments.

**What To Do**:
1. Compare 13C peak count with DEPT-135 peak count
2. The difference = quaternary carbons
3. Quaternary carbons are only connected to the structure through HMBC correlations
4. Common quaternary carbons:
   - Carbonyl carbons (C=O) at 160-220 ppm
   - Aromatic junction carbons
   - Bridgehead carbons

### Pitfall 3: HMBC Noise Creates False Correlations

**The Problem**: Raw HMBC peak picking finds hundreds of peaks, most of which are noise.

**Why This Happens**: HMBC is an insensitive experiment with many artifacts (t1 noise, 1J bleeding).

**What To Do**:
1. **Always use guided HMBC picking** (`pick_hmbc_peaks`)
2. The guided picker validates that:
   - The carbon position exists in 13C/DEPT
   - The proton position exists in HSQC
3. This typically reduces peak count from hundreds to tens

**Key Insight**: More HMBC correlations = better LSD results, but only if they're real correlations.

### Pitfall 4: Too Many LSD Solutions

**The Problem**: LSD generates hundreds or thousands of candidate structures.

**Why This Happens**: Insufficient or incorrect constraints.

**Common Causes**:
1. Missing HMBC correlations (manually constructed vs. real data)
2. Incorrect atom multiplicities
3. Symmetry not accounted for
4. Quaternary carbons with no HMBC connections

**What To Do**:
1. Verify all HMBC correlations from experimental data
2. Check that all protonated carbons have HSQC correlations
3. Ensure molecular formula is correct
4. Consider if the compound has unusual features (macrocycles, etc.)

**Expected Results**:
- 1-10 solutions: Good constraint quality
- 10-100 solutions: May need more data or review
- 100+ solutions: Likely missing critical constraints

### Pitfall 5: Heteroatom Positions

**The Problem**: Oxygen and nitrogen atoms don't appear directly in standard NMR experiments.

**Why This Happens**: Most heteroatoms have no attached protons (carbonyl O, ether O) or exchange rapidly (OH, NH).

**What To Do**:
1. Infer heteroatom positions from:
   - Molecular formula (tells you how many O, N, etc.)
   - Chemical shifts (C-O carbons appear 50-90 ppm)
   - Carbonyl carbons (160-220 ppm)
2. LSD uses the molecular formula to place heteroatoms
3. Carbons with unusually high chemical shifts likely bear heteroatoms

---

## Step-by-Step Guide

### Step 1: Initial Assessment

**User provides**: Data directory path and molecular formula

**Your first actions**:
```
1. dereplicate_c13(c13_path, molecular_formula)
   → If is_match=true: Report the match and STOP
   → If no match: Continue

2. Read available spectra to understand what data exists:
   - read_spectrum_1d for each 1D experiment
   - read_spectrum_2d for each 2D experiment
```

**Questions to answer**:
- What spectra are available?
- What is the molecular formula? (Calculate degree of unsaturation)
- Is there a database match?

### Step 2: Symmetry Analysis

**Use**: `analyze_symmetry(molecular_formula, hsqc_path, dept135_path)`

**Interpret the results**:
```
If observed_carbons < expected_carbons:
    → Molecular symmetry present
    → Some carbons are equivalent
    → Adjust expectations for subsequent analysis

If observed_carbons ≈ expected_carbons:
    → No significant symmetry
    → Each carbon gives one signal
```

### Step 3: Peak Picking

**Order matters - do this sequentially**:

```python
# 1. Pick 13C peaks (all carbons)
c13_peaks = pick_peaks_1d(c13_path)

# 2. Pick HSQC peaks using DEPT guidance
hsqc_result = pick_hsqc_peaks(hsqc_path, dept135_path, dept90_path)
# This gives you: multiplicities (CH, CH2, CH3)

# 3. Pick HMBC peaks using guided filtering
hmbc_result = pick_hmbc_peaks(hmbc_path, c13_path, hsqc_path, dept135_path)
# This gives you: long-range C-H correlations
```

### Step 4: Data Validation

**Check for consistency**:

1. **Carbon count check**:
   ```
   13C peaks ≈ expected carbons (accounting for symmetry)
   ```

2. **Protonated carbon check**:
   ```
   DEPT-135 peaks ≈ HSQC carbon count
   (Every DEPT carbon should have HSQC correlation)
   ```

3. **Hydrogen budget**:
   ```
   Sum of (multiplicity × count) from HSQC ≤ formula hydrogens
   Difference may indicate: OH groups, NH groups, or equivalent positions
   ```

### Step 5: LSD Generation

**Use**: `generate_lsd_input(data_dir, molecular_formula, output_file)`

**The tool automatically**:
- Reads all available spectra
- Applies guided peak picking
- Generates atom definitions from multiplicities
- Creates HSQC and HMBC correlations
- Handles symmetry information

### Step 6: Structure Solving

**First check**: `check_lsd_availability()`
- If LSD not available, inform the user
- If outlsd not available, solution ranking will be limited (no SMILES conversion)

**Then run**: `run_lsd(input_file, timeout=60)`

**What happens automatically**:
1. LSD generates solution files (.sol) with atom connectivity
2. If outlsd is installed, it automatically converts solutions to SMILES
3. The SMILES are stored in outlsd.out for ranking

**Interpret results**:
```
solution_count = 0:
    → Over-constrained or contradictory data
    → Review input for errors

solution_count = 1-5:
    → Excellent! Well-constrained problem
    → Report the solution(s)

solution_count = 5-50:
    → Acceptable, may need manual inspection
    → Describe the structural variants

solution_count > 100:
    → Under-constrained
    → Need more correlations or data review
```

### Step 7: Solution Ranking (if multiple solutions)

**When to rank**: If LSD produces more than one solution, use ranking to identify the most likely candidate.

**Use**: `rank_lsd_solutions(solutions_dir, experimental_shifts, tolerance=3.0, top_n=10)`

> **Important**: Use the curated peak list you built during the CASE workflow, not a
> fresh re-pick from the spectrum. The peak list may have been validated against DEPT,
> adjusted for overlapping signals, or manually refined. Pass these as `experimental_shifts`.

**How it works**:
1. For each LSD solution with a SMILES structure
2. Predict 13C shifts using HOSE codes
3. Match predicted shifts to experimental peaks (greedy assignment)
4. Calculate MAE (Mean Absolute Error)
5. Sort solutions by MAE (lower = better match)

**Interpret ranking results**:
```
MAE < 2.0 ppm:
    → Excellent match, high confidence

MAE 2.0-3.5 ppm:
    → Good match, reasonable confidence

MAE 3.5-5.0 ppm:
    → Moderate match, review carefully

MAE > 5.0 ppm:
    → Poor match, likely incorrect structure
```

**Important caveats**:
- **Symmetry affects ranking**: If the molecule has equivalent carbons (e.g., para-benzene), the experimental spectrum shows fewer signals than predicted. This causes unmatched predictions and inflated MAE scores.
- **Ranking is a guide, not proof**: The correct structure should rank near the top, but may not always be #1 due to prediction errors.
- **Review top candidates**: Always examine the top 3-5 candidates for chemical reasonableness.

**Alternative - manual prediction**:
```python
# Predict shifts for a specific SMILES
predict_c13_shifts(smiles="CC(C)Cc1ccc(cc1)C(C)C(=O)O")
# Returns: predictions for each carbon with confidence scores
```

---

## Decision Trees

### When to Proceed with Full Elucidation

```
Start
  │
  ├─ Dereplication found match?
  │    ├─ YES → Report match, confidence level, DONE
  │    └─ NO → Continue
  │
  ├─ All necessary spectra available?
  │    ├─ YES → Continue
  │    └─ NO → Request missing data:
  │           - Need at minimum: 13C, HSQC, HMBC
  │           - DEPT highly recommended
  │
  ├─ Molecular formula provided?
  │    ├─ YES → Continue
  │    └─ NO → Request from user (essential!)
  │
  └─ Proceed with peak picking and LSD
```

### Handling Symmetry

```
Symmetry Analysis Result
  │
  ├─ observed_carbons == expected_carbons?
  │    └─ No symmetry → Proceed normally
  │
  ├─ observed_carbons < expected_carbons?
  │    │
  │    ├─ Difference = 2?
  │    │    └─ Likely: one pair of equivalent carbons
  │    │       (e.g., para-benzene CH, isopropyl CH3)
  │    │
  │    ├─ Difference = 4?
  │    │    └─ Likely: two pairs of equivalent carbons
  │    │       (e.g., para-benzene ring)
  │    │
  │    └─ Larger difference?
  │         └─ Highly symmetric molecule
  │            (e.g., C2 or higher symmetry)
  │
  └─ Check HSQC intensities for confirmation
       - Doubled signals have ~2x intensity
```

### LSD Result Interpretation

```
LSD Solution Count
  │
  ├─ 0 solutions
  │    └─ Check:
  │       - Contradictory constraints?
  │       - Wrong molecular formula?
  │       - Missing heteroatoms in formula?
  │
  ├─ 1 solution
  │    └─ High confidence
  │       - Verify solution makes chemical sense
  │       - Check for unusual features
  │       - Optionally verify with predict_c13_shifts
  │
  ├─ 2-10 solutions
  │    └─ Good result → USE RANKING
  │       - rank_lsd_solutions to identify best match
  │       - Examine differences between top candidates
  │       - Often differ in stereochemistry or regiochemistry
  │
  ├─ 10-100 solutions
  │    └─ Needs review → USE RANKING
  │       - rank_lsd_solutions to narrow candidates
  │       - Review top 10 for reasonableness
  │       - Missing HMBC correlations?
  │
  └─ >100 solutions
       └─ Under-constrained
          - Request additional NMR data
          - Review peak picking parameters
          - Ranking may still help identify best candidates
```

---

## Interpreting Results

### Dereplication Results

**High confidence match** (score > 0.85):
```
"The compound matches [NAME] in the database with a score of [X].
This is a known compound: [SMILES/structure description].
The match is based on [N] carbon shifts with an average deviation of [Y] ppm."
```

**Possible match** (score 0.65-0.85):
```
"There is a potential match to [NAME] with a score of [X].
This should be verified by comparing predicted vs. observed shifts.
Key differences are at positions: [list any outliers]."
```

**No match** (score < 0.65 or no candidates):
```
"No database match found. This may be:
1. A novel compound not in the database
2. A known compound with different stereochemistry
3. A compound not yet added to the reference database

Proceeding with de novo structure elucidation..."
```

### LSD Results

**Report solutions like this**:
```
"LSD found [N] candidate structure(s).

Solution 1: [Description]
- Core scaffold: [aromatic/aliphatic/mixed]
- Key features: [functional groups, ring systems]
- Consistent with: [which spectroscopic features]

[If multiple solutions, describe key differences]

The solutions differ in:
- Position of [functional group]
- Ring fusion pattern
- Stereochemistry at [position]
"
```

### Reporting Uncertainty

**Always be transparent about**:
- Missing data that would improve confidence
- Assumptions made during analysis
- Alternative interpretations
- Recommended additional experiments

---

## Example Reasoning

### Example 1: Ibuprofen Analysis

**Input**: Data directory with C13H18O2

**Reasoning process**:

```
Step 1: Dereplication
→ Run dereplicate_c13("data/Ibuprofen/2", "C13H18O2")
→ Result: Match found - Ibuprofen (score 0.92)
→ DONE - Report the known structure

But if no match was found, I would continue:

Step 2: Analyze what we have
- Formula: C13H18O2
- Degree of unsaturation: (2×13 + 2 - 18 + 0)/2 = 5
  → Suggests aromatic ring (4) + one additional unsaturation (C=O)

Step 3: Check symmetry
→ analyze_symmetry shows 11 observed carbons vs 13 expected
→ 2 carbons are equivalent (likely para-substituted benzene)

Step 4: Peak picking
→ DEPT-guided HSQC: Found 10 protonated carbons
   - 2 CH3 (one at high field ~22 ppm, one pair at ~22 ppm)
   - 1 CH2 (~45 ppm)
   - 4 CH (aromatic region 127-130 ppm, some doubled intensity)
   - 1 CH (~45 ppm, attached to aromatic)

→ Quaternary carbons: 3 (observed in 13C but not DEPT)
   - Carbonyl ~180 ppm
   - Two aromatic junction carbons

Step 5: HMBC analysis
→ 28 validated HMBC correlations
→ Key correlations connect:
   - Methyl groups to quaternary aromatic carbon
   - CH adjacent to carboxylic acid
   - Aromatic protons to bridging carbon

Step 6: LSD run
→ 2 solutions generated
→ Both are ibuprofen (differ only in configuration)
```

### Example 2: Handling Missing Data

**User asks**: "Analyze the NMR data in /path/to/unknown for C10H12O2"

**Your response should include**:

```
Let me first check what spectra are available and run dereplication.

[After reading spectra]

I found the following data:
- 13C spectrum (experiment 2)
- HSQC spectrum (experiment 5)

However, I notice we're missing:
- DEPT-135: This would help determine carbon multiplicities
- HMBC: This is essential for determining long-range connectivity

Without HMBC data, LSD cannot determine how the carbons are connected.

I can still:
1. Run dereplication against the database
2. Report the observed chemical shifts
3. Provide preliminary structural insights from chemical shift analysis

Would you like me to proceed with the available data, or can you provide
the HMBC spectrum?
```

---

## Quick Reference Card

### Essential Workflow
1. **Dereplication FIRST** - Always check databases before full analysis
2. **Check symmetry** - Explains "missing" signals
3. **Use guided peak picking** - Reduces noise dramatically
4. **Validate data** - Cross-check between experiments
5. **Run LSD** - Generate candidate structures
6. **Rank solutions** - Use `rank_lsd_solutions` if multiple candidates
7. **Interpret results conservatively** - Report uncertainty

### Red Flags to Watch For
- Fewer signals than expected atoms → Symmetry
- More signals than expected → Impurity or wrong formula
- Zero LSD solutions → Over-constrained or error
- Thousands of LSD solutions → Under-constrained

### Key Tolerances
- 13C chemical shift matching: ±1.5 ppm (carbonyl), ±0.8 ppm (aliphatic)
- HSQC validation: ±1.0 ppm (13C dimension)
- HMBC validation: ±1.5 ppm (13C), ±0.1 ppm (1H)
- Dereplication match: score > 0.85 = high confidence
- Solution ranking: MAE < 2.0 ppm = excellent, 2-3.5 ppm = good, > 5 ppm = poor

### When to Ask for Help
- Conflicting data between experiments
- Unusual chemical shifts outside normal ranges
- Molecular formula doesn't match observed data
- User requests interpretation beyond available data
