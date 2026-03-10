# Technology Stack: v7.0 Statistical 4J Detection

**Project:** lucy-ng -- AI-agent powered CASE for NMR
**Milestone:** v7.0 Statistical 4J Detection
**Researched:** 2026-03-10
**Overall confidence:** HIGH (existing stack + proven patterns)

## Executive Summary

Statistical 4J HMBC coupling detection can be built entirely with lucy-ng's existing technology stack. No new external libraries are needed. The approach mines the existing 928K-compound database (895K with SMILES, 788K with both aromatic + aliphatic atom-indexed shifts) to compute bond-distance statistics for carbon-carbon atom pairs. RDKit's `GetDistanceMatrix` provides sub-microsecond bond-path computation per molecule. HOSE codes at radius 4 encode the 4-bond neighborhood but are too coarse for reliable 4J discrimination -- direct bond-path mining from SMILES is the correct approach.

No existing CASE system has solved automatic 4J detection. Sherlock treats all HMBC as generic long-range. WebCocon requires manual user annotation via a "4J-Flag" parameter. LSD supports `HMBC X Y 4` syntax (4-bond path) but requires ELIM command and user knowledge. This milestone would give lucy-ng a genuine competitive advantage.

## Recommended Stack

### Core (already in lucy-ng, no additions)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| RDKit | existing | Bond-distance matrix, aromaticity, shortest path | `GetDistanceMatrix` is <1us per molecule, `GetShortestPath` gives exact atom path |
| SQLite | existing | Store 4J coupling statistics as new table | Follows pattern of hose_stats, bond_pair_stats tables |
| Pydantic v2 | existing | Models for 4J detection results | Follows HybridisationResult, NeighbourResult pattern |
| hosegen | existing | HOSE code generation (radius 1-6) | Existing for shift prediction; NOT used for 4J detection itself |
| NumPy | existing | Statistical computation during mining | Existing dependency |
| tqdm | existing | Progress bars for mining pipeline | Existing dependency |

### No New Dependencies Required

The v7.0 milestone does not require any new Python packages. Every capability needed exists in RDKit + SQLite + the current codebase.

## Key Technical Findings

### 1. RDKit Bond-Distance Computation (HIGH confidence)

**Source:** RDKit 2025.09 documentation, verified with code testing

RDKit provides two key functions for bond-path analysis:

```python
from rdkit import Chem

mol = Chem.MolFromSmiles("CC(C)Cc1ccc(cc1)C(C)C(=O)O")  # Ibuprofen

# Distance matrix: O(1) lookup after O(N^2) computation
dm = Chem.GetDistanceMatrix(mol)
bond_distance = int(dm[atom_i][atom_j])  # Bond count between any pair

# Exact atom path for pathway characterization
path = Chem.GetShortestPath(mol, atom_i, atom_j)  # Tuple of atom indices
```

**Performance verified on local machine:**
- `GetDistanceMatrix`: ~0.3 us (ibuprofen, 15 atoms), ~0.9 us (taxol, 67 atoms)
- Can process 928K compounds in ~1 second of pure distance computation
- Bottleneck will be SMILES parsing + I/O, not distance computation

**Key RDKit properties for 4J pathway classification:**
- `atom.GetIsAromatic()` -- identifies aromatic ring atoms in path
- `atom.GetTotalNumHs()` -- identifies H-bearing carbons (HMBC-observable)
- `mol.GetRingInfo().IsAtomInRingOfSize(idx, N)` -- ring characterization
- `atom.GetHybridization()` -- sp2/sp3 classification

**Ibuprofen validation:** Testing on ibuprofen SMILES identified 12 carbon pairs at exactly 4-bond distance, with the known 4J UAT culprits (ArCH to benzylic CH2/CH) correctly appearing among them.

### 2. LSD HMBC Bond-Distance Syntax (HIGH confidence)

**Source:** LSD Manual v3.5.2 (MANUAL_ENG.html)

LSD supports explicit bond-distance specification for HMBC:

```
HMBC X Y        ; default: 2-3 bonds (standard HMBC)
HMBC X Y 2      ; exactly 2 bonds (forces direct bond via intermediate)
HMBC X Y 4      ; exactly 4 bonds (requires ELIM command to be present)
HMBC X Y 2 4    ; 2 to 4 bonds (range specification)
```

**Critical finding:** `HMBC X Y 4` requires an `ELIM` command in the LSD file. Without ELIM, LSD rejects 4-bond specifications.

**Implication for v7.0:** When the detector flags a correlation as "probable 4J", the agent has three options:
1. Write `HMBC X Y 2 4` -- widen bond range to 2-4 (preserves constraint, needs ELIM)
2. Defer the correlation -- add only as last resort (current v6.0 heuristic approach)
3. Drop the correlation entirely -- lose constraint information

Option 1 is optimal when ELIM is acceptable. Option 2 is the safe default.

### 3. HOSE Codes at Radius 4 -- NOT Suitable for 4J Detection (MEDIUM confidence)

**Source:** Code testing, HOSE code theory

HOSE codes at radius 4 encode the 4-bond neighborhood around a single atom. For ibuprofen:

```
ArCH (C5) R3: C-3;*C*C(*CC,*C/*C,C,*&C/)
ArCH (C5) R4: C-3;*C*C(*CC,*C/*C,C,*&C/*&,CC,CC)
                                              ^^^^^^^^^
                                              Sphere 4 = atoms at 4 bonds

Benzylic CH2 (C3) R3: C-4;CC(CC,*C*C/,,*C,*C/)
Benzylic CH2 (C3) R4: C-4;CC(CC,*C*C/,,*C,*C/*C,*&)
                                                 ^^^^
                                                 Sphere 4
```

**Conclusion:** HOSE R4 encodes THAT 4-bond neighbors exist but NOT which specific atom pairs are 4-bond coupled for HMBC purposes. The HOSE code describes one atom's environment, not a pairwise relationship between two atoms. For 4J detection, we need pairwise bond-distance statistics, which requires direct mining from molecular graphs.

**HOSE codes are NOT the right tool for 4J detection.** Use direct bond-path analysis instead.

### 4. Database Mining Capacity (HIGH confidence)

**Source:** Direct database queries on lucy-ng-derep.db

The existing lucy-ng database provides an excellent mining base:

| Metric | Count |
|--------|-------|
| Compounds with SMILES | 895,099 |
| Total atom-indexed shifts | 23,994,980 |
| Compounds with shifts in 110-160 ppm (aromatic range) | 842,900 |
| Compounds with BOTH aromatic + aliphatic atom-indexed shifts | 788,186 |

Atom indices are 0-based (matching RDKit convention after COCONUT 1-based to 0-based conversion in the importer). For each compound we can:

1. Parse SMILES to RDKit mol
2. Compute `GetDistanceMatrix`
3. For each pair of atom-indexed carbon shifts, look up the bond distance
4. Classify each pair as 2J, 3J, 4J, or >4J
5. Categorize by carbon-type pair and aromatic-path presence
6. Aggregate statistics

**Estimated mining time:** ~895K SMILES to parse, ~24M shifts to pair. At ~50us per compound (SMILES parse + distance matrix + pair enumeration), total ~45 seconds of computation. With database I/O and batching: estimate 10-30 minutes for full mining run. This follows the pattern of the existing HOSE stats generator which processes all compounds in a similar timeframe.

### 5. Existing CASE System Approaches (HIGH confidence)

**Source:** Sherlock thesis (Wenk 2023), WebCocon paper (PMC8398166), LSD Manual

| System | 4J Handling | Approach | Automatic? |
|--------|-------------|----------|------------|
| **Sherlock** | None | Treats all HMBC as generic "M" correlations | No |
| **WebCocon** | Manual "4J-Flag" parameter | User sets 0/N/-1; stepwise trial | No |
| **LSD/pyLSD** | `HMBC X Y 4` with ELIM | User must annotate which are 4J | No |
| **ACD/Labs** | Unknown | Commercial, opaque internals | Unknown |
| **lucy-ng v6.0** | Heuristic flagging | ArCH (110-160) <-> aliphatic (0-55) | Partial |
| **lucy-ng v7.0** | Database-backed statistics | Mine 788K compounds for probability | **Yes** |

**Key finding:** No existing CASE tool has automatic, database-backed 4J detection. All require user knowledge or manual annotation. v7.0 would be a genuine competitive advantage.

### 6. Statistical Approach for 4J Detection (MEDIUM confidence)

The approach builds a new database table storing, for each "carbon environment pair type", the observed frequency of 2-bond, 3-bond, and 4-bond C...C distances across the compound database.

**Proposed table schema:**

```sql
CREATE TABLE coupling_path_stats (
    carbon1_type TEXT NOT NULL,    -- Encoded carbon environment type
    carbon2_type TEXT NOT NULL,    -- Encoded carbon environment type
    bond_distance INTEGER NOT NULL, -- 2, 3, 4, or 5+
    observation_count INTEGER NOT NULL,
    total_pairs INTEGER NOT NULL,  -- Total for this pair type across all distances
    frequency REAL NOT NULL,       -- observation_count / total_pairs
    has_aromatic_path INTEGER NOT NULL DEFAULT 0, -- Count where path traverses aromatic ring
    PRIMARY KEY (carbon1_type, carbon2_type, bond_distance)
);
```

**Carbon type encoding -- recommended: Hybridization + H-count + aromatic flag:**

| Type Code | Description | Shift Range |
|-----------|-------------|-------------|
| `sp2_CH_arom` | Aromatic CH | 110-160 ppm |
| `sp2_C_arom` | Aromatic quaternary C | 110-160 ppm |
| `sp2_CH` | Vinyl/olefinic CH | 100-150 ppm |
| `sp2_C` | Vinyl/olefinic quaternary C | 100-160 ppm |
| `sp2_C_carbonyl` | C=O carbon | 160-220 ppm |
| `sp3_CH3` | Methyl carbon | 5-30 ppm |
| `sp3_CH2` | Methylene carbon | 15-55 ppm |
| `sp3_CH` | Methine carbon | 20-70 ppm |
| `sp3_C` | Quaternary sp3 C | 25-50 ppm |
| `sp3_CH_O` | O-bearing methine | 60-100 ppm |
| `sp3_CH2_O` | O-bearing methylene | 55-75 ppm |

This gives ~12 types, yielding ~12x12x4 = 576 rows in the stats table (manageable).

**Alternatives considered:**

| Encoding | Granularity | Pros | Cons |
|----------|-------------|------|------|
| Shift range bucket (5 types) | Coarse | Simple, fast | Cannot distinguish vinyl from aromatic |
| **Hyb+H+aromatic (12 types)** | **Medium** | **Good discrimination, interpretable** | **May miss fine-grained patterns** |
| HOSE R1 code (~200 types) | Fine | Captures bonded-atom context | Some pairs too sparse for statistics |
| HOSE R2 code (~2000 types) | Very fine | Maximum detail | Most pairs have zero observations |

**Detection algorithm:**

```
For an HMBC correlation between carbon_A (shift_A, mult_A) and carbon_B (shift_B, mult_B):
1. Determine type_A from hybridization + H-count + aromatic flag
2. Determine type_B from hybridization + H-count + aromatic flag
3. Look up coupling_path_stats for (type_A, type_B) at distances 2, 3, 4
4. Compute P(4J) = freq(4) / (freq(2) + freq(3) + freq(4))
5. If P(4J) > 0.15 AND has_aromatic_path frequency > 0.5: flag "potential 4J"
6. If P(4J) > P(3J): flag "probable 4J"
```

The `has_aromatic_path` filter is critical: 4J couplings are mainly observable through aromatic W-pathways, not through flexible aliphatic chains where coupling constants are typically too small for HMBC detection.

## Implementation Architecture

### New Database Table

Add `coupling_path_stats` table in schema v7 migration. Pattern: `bond_pair_stats` (schema v6).

### New Generator Module

`src/lucy_ng/prediction/coupling_stats_generator.py` -- follows `stats_generator.py` and `bond_pair_generator.py` patterns. Resumable with checkpoint table. Processes all compounds with SMILES + atom-indexed shifts.

### New Detection Method

Add `detect_4j_coupling()` to `StatisticalDetector` class in `detection/detector.py`. Pattern: `detect_hybridisation()`, `detect_neighbours()`, `detect_hhb()`.

### New Pydantic Models

Add `CouplingPathResult` and `CouplingPathDistribution` to `detection/models.py`. Pattern: `HybridisationResult`.

### New CLI Command

`lucy detect coupling <shift1> <shift2> --mult1 CH --mult2 CH2 --format json`

Returns probability distribution over 2J, 3J, 4J for the given carbon pair types.

### Agent Skill Updates

1. **nmr-chemist**: Replace v6.0 heuristic 4J flagging with `lucy detect coupling` CLI calls for each HMBC pair
2. **lsd-engineer**: When P(4J) > threshold, use `HMBC X Y 2 4` syntax or defer to last batch
3. **solution-analyst**: Use 4J probabilities in quality assessment

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Bond-path computation | RDKit GetDistanceMatrix | NetworkX graph | RDKit already a dependency, 10-100x faster |
| Statistics storage | New SQLite table | Extend hose_stats | Pairwise relationship does not fit per-atom HOSE schema |
| Carbon type encoding | Hyb+H+aromatic (12 types) | Shift-range buckets (5) | Too coarse; 130 ppm ArCH and 130 ppm vinyl CH behave differently |
| Carbon type encoding | Hyb+H+aromatic (12 types) | Full HOSE codes | Too sparse; most pairs have zero observations |
| Detection approach | Lookup table from mining | ML classifier (random forest, etc.) | Overkill for a structural signal; lookup table is interpretable and debuggable |
| 4J handling in LSD | Defer + optional HMBC X Y 2 4 | Drop correlation entirely | Preserves constraint information; LSD can still use it |
| Aromatic detection | RDKit GetIsAromatic() on path atoms | Shift-range heuristic | RDKit aromaticity is definitive from structure; shift heuristic has false positives |

## Key Constraints

1. **No explicit hydrogens** -- all SMILES parsing must use `MolFromSmiles()` without `AddHs()`, consistent with existing HOSE code convention
2. **Atom index convention** -- COCONUT indices are 1-based in source, converted to 0-based in lucy-ng database. Mining must use 0-based indices
3. **HMBC observability** -- only C-H pairs where BOTH atoms bear hydrogen can appear in HMBC. Mining should track C-C distances but the detection CLI should warn about non-HMBC-observable pairs
4. **LSD ELIM requirement** -- `HMBC X Y 2 4` or `HMBC X Y 4` requires ELIM in the LSD file. The v6.0 deferral approach (skip 4J correlations) is safer as default
5. **Aromatic path is the key signal** -- most 4J HMBC couplings observed in practice traverse an aromatic ring (W-pathway). The mining should track whether the path includes aromatic atoms

## Sources

### Official Documentation (HIGH confidence)
- [RDKit rdmolops module -- GetDistanceMatrix, GetShortestPath](https://www.rdkit.org/docs/source/rdkit.Chem.rdmolops.html)
- [RDKit GitHub issue #2921 -- Bond distance computation](https://github.com/rdkit/rdkit/issues/2921)
- [LSD Manual v3.5.2 -- HMBC X Y P3 P4 syntax, ELIM command](https://nuzillard.github.io/LSD/MANUAL_ENG.html)
- [PyLSD documentation](https://nuzillard.github.io/PyLSD/)

### Research Papers (MEDIUM confidence)
- [WebCocon 4J-HMBC incorporation (PMC8398166)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8398166/) -- 4J-Flag parameter, no automatic detection
- [Sherlock CASE system (PMC9920390)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9920390/) -- No 4J handling documented
- [LSD Tutorial (Nuzillard 2018, MRC)](https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/abs/10.1002/mrc.4612) -- HMBC bond distance examples
- [COCONUT 2.0 database](https://academic.oup.com/nar/article/53/D1/D634/7908792) -- Source compound data

### Project-Internal (HIGH confidence)
- Ibuprofen v4.0 UAT findings (MEMORY.md) -- 3 confirmed 4J W-pathway couplings
- v6.0 Phase 56 skill updates -- heuristic 4J flagging (baseline to replace)
- Database schema v6 (`src/lucy_ng/database/schema.py`) -- pattern for new table
- StatisticalDetector class (`src/lucy_ng/detection/detector.py`) -- pattern for detection
- StatsGenerator (`src/lucy_ng/prediction/stats_generator.py`) -- pattern for mining pipeline
- Sherlock analysis (`background/sherlock-analysis.md`) -- competitive landscape

## Confidence Assessment

| Area | Confidence | Reason |
|------|------------|--------|
| RDKit bond-distance APIs | HIGH | Tested in code, documented, sub-microsecond verified |
| Database mining feasibility | HIGH | 788K usable compounds confirmed via direct queries |
| LSD 4-bond HMBC syntax | HIGH | Confirmed from LSD Manual v3.5.2 with examples |
| No new dependencies needed | HIGH | All tools already in stack |
| Statistical approach design | MEDIUM | Novel for CASE systems; follows proven lucy-ng detection patterns |
| Carbon type encoding granularity | MEDIUM | Need empirical validation; may need HOSE R1 fallback |
| Mining time estimate (10-30 min) | MEDIUM | Extrapolated from per-molecule timing; I/O patterns may vary |
