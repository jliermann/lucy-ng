# Symmetry Handling in LSD Structure Elucidation

## The Symmetry Problem

### What happens with symmetric molecules

Molecules with symmetry (like para-disubstituted benzene in ibuprofen) show fewer NMR signals than their molecular formula suggests:

- **Ibuprofen** (C13H18O2): 13 carbons
- **Observed 13C signals**: 10 unique peaks
- **Missing signals**: 3 (due to equivalent carbons)

Equivalent carbons:
- 2 ortho aromatic CH (129.4 ppm) - appear as 1 signal
- 2 meta aromatic CH (127.3 ppm) - appear as 1 signal
- 2 isopropyl CH3 (22.4 ppm) - appear as 1 signal

### Impact on LSD Input Generation

The automated LSD generator (`LSDInputGenerator`) must handle this discrepancy:

1. Molecular formula says 13 carbons
2. DEPT-guided peak picking finds only 10 unique 13C signals
3. The 3 "missing" carbons need to be accounted for

**Current behavior**: The generator adds missing carbons as quaternary (hybridization=2, H-count=0), which may be incorrect if the missing carbons are actually protonated equivalents.

## LSD Handling of Symmetry

LSD does NOT require explicit symmetry specification. Instead:

1. **Define all atoms**: Specify all 13 carbons + 2 oxygens (15 atoms total)
2. **Let LSD explore**: LSD will find all structures that satisfy the constraints
3. **Symmetry emerges**: Symmetric structures will naturally emerge from the solutions

### Working LSD Input Example (ibuprofen_v4.lsd)

```
; LSD input: Ibuprofen with symmetry
; C13H18O2

; All 13 carbons (even equivalent ones get separate entries)
MULT 1 C 2 0    ; 180.6 ppm - C=O (quaternary)
MULT 2 C 2 0    ; 140.8 ppm - ipso (quaternary)
MULT 3 C 2 0    ; 137.0 ppm - ipso (quaternary)
MULT 4 C 2 1    ; 129.4 ppm - aromatic CH
MULT 5 C 2 1    ; 129.4 ppm - aromatic CH (equivalent to 4)
MULT 6 C 2 1    ; 127.3 ppm - aromatic CH
MULT 7 C 2 1    ; 127.3 ppm - aromatic CH (equivalent to 6)
MULT 8 C 3 2    ; 45.0 ppm - CH2 (benzylic)
MULT 9 C 3 1    ; 44.9 ppm - CH (alpha to COOH)
MULT 10 C 3 1   ; 30.1 ppm - CH (isopropyl)
MULT 11 C 3 3   ; 22.4 ppm - CH3 (isopropyl)
MULT 12 C 3 3   ; 22.4 ppm - CH3 (isopropyl, equivalent to 11)
MULT 13 C 3 3   ; 18.1 ppm - CH3 (alpha)

; Oxygen atoms
MULT 14 O 2 0   ; Carbonyl O
MULT 15 O 3 1   ; Hydroxyl O

; HSQC for all protonated carbons
HSQC 4 4
HSQC 5 5
HSQC 6 6
HSQC 7 7
HSQC 8 8
HSQC 9 9
HSQC 10 10
HSQC 11 11
HSQC 12 12
HSQC 13 13

; Key HMBC correlations (minimal set)
HMBC 1 9        ; C=O to alpha-CH
HMBC 1 13       ; C=O to alpha-CH3

; Carbonyl bond
BOND 1 14

EXIT
```

This input produces **1318 solutions** because:
- The constraints are minimal (only carbonyl HMBC)
- LSD explores all possible structures that satisfy the constraints
- More HMBC correlations would reduce solutions but risk over-constraining

## Solution Ranking Challenges

### The Symmetry Mismatch Problem

When ranking solutions using HOSE-based 13C prediction:

| Aspect | Experimental | Prediction |
|--------|--------------|------------|
| Carbon count | 10 unique signals | 13 individual carbons |
| Equivalent carbons | Combined into 1 signal | Predicted separately |

**Result**: The correct structure may rank lower because:
1. Predictor outputs 13 shifts
2. Only 10 experimental signals to match
3. 3 predicted shifts go unmatched
4. Each unmatched shift incurs a penalty (tolerance value)

### Example: Ibuprofen Ranking

```
Solution 1319 (correct ibuprofen):
  Rank: #965 out of 1319
  MAE: 2.155 ppm
  Matched: 7/13

Top solutions:
  #1: MAE=1.812, matched=8/13 (incorrect structure)
```

The correct structure ranks #965 because:
- Ipso carbons predicted at 132.5 ppm (experimental: 140.8, 137.0) - outside 3 ppm tolerance
- Only 7 of 13 carbons match due to tolerance and symmetry

### Implications

1. **Ranking is a guide, not ground truth**: Lower MAE doesn't guarantee correct structure
2. **Top N review**: Users should review multiple top candidates
3. **Additional validation needed**: Consider:
   - HMBC pattern matching
   - Substructure queries
   - Expert review

## Bugs Fixed During Investigation

### 1. LSD Parser SMILES Indexing Bug

**Location**: `src/lucy_ng/lsd/parser.py`

**Problem**: SMILES from `outlsd.out` were matched to solutions by list position (alphabetical file order) instead of by solution index (numeric order).

**Fix**: Match SMILES to solutions using a dictionary keyed by solution index.

### 2. Ranker Count Bug

**Location**: `src/lucy_ng/ranking/ranker.py`

**Problem**: `ranked_count` in results was calculated after `top_n` truncation, showing only the truncated count.

**Fix**: Store total count before truncation.

## Recommendations for Future Development

1. **Symmetry-aware ranking**: Average predictions for equivalent carbons before matching
2. **Multi-criteria ranking**: Combine MAE with other factors (ring pattern, heteroatom connectivity)
3. **Constraint quality feedback**: Warn when LSD produces >1000 solutions (likely under-constrained)
4. **CDCl3 filtering**: Auto-exclude solvent peaks from HMBC/HSQC correlations
