# Feature Landscape: Statistical 4J HMBC Detection

**Domain:** NMR-based 4J coupling detection for CASE pipeline
**Researched:** 2026-03-10
**Overall confidence:** MEDIUM-HIGH (NMR chemistry well-established, database approach novel)

## Table Stakes

Features the 4J detection system must have to be useful. Missing any one of these makes the feature ineffective.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Aromatic CH-to-benzylic detection | Ibuprofen UAT failure was exactly this pattern | Medium | ArCH (110-160 ppm) to CH/CH2 (0-55 ppm) through aromatic ring |
| Per-correlation probability score | Binary yes/no is too coarse; agent needs confidence to decide | Medium | Return probability 0.0-1.0 for "this correlation could be 4J" |
| Database-backed statistics | Heuristic shift-range matching (current) is unreliable | High | Requires new database table or query pattern |
| CLI interface (`lucy detect 4j`) | Agent uses CLI for all detection; must follow existing pattern | Low | Consistent with `lucy detect hybridisation`, `lucy detect neighbours` |
| JSON output format | Agent parses JSON programmatically | Low | Pydantic model with `model_dump_json()`, same as other detectors |
| Integration with nmr-chemist flagging | Replaces current heuristic rules in Section 3 of nmr-chemist.md | Low | Agent reads detection output, flags in [SETUP-COMPLETE] |
| Integration with lsd-engineer deferral | Deferred correlations must carry the statistical evidence | Low | Probability score flows through to constraint inventory |

## Differentiators

Features that make this system significantly better than the current heuristic.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Atom-type-pair probability matrix | Not all ArCH-to-aliphatic HMBC are 4J; quantify which pairs | High | Key differentiator: probability varies by hybridization, aromaticity, substituent type |
| W-pathway structural motif detection | W-pathway 4J couplings are 10-100x more intense than non-W | Medium | Para-disubstituted benzenes, vinyl systems, rigid frameworks |
| LSD HMBC bond range output | Tell lsd-engineer to write `HMBC X Y 2 4` instead of deferring | Medium | LSD natively supports `HMBC X Y 2 4` syntax (confirmed in manual) |
| Batch-level 4J assessment | Assess all HMBC correlations at once, not one-by-one | Medium | Cross-correlation patterns (multiple 4J to same aromatic ring) strengthen confidence |
| Aromatic ring sanity integration | Post-ranking check: no aromatic ring + flagged 4J = likely correct diagnosis | Low | Already exists in ranker.py; connect to pre-LSD detection |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Coupling constant prediction (Hz) | Would require DFT or empirical J-coupling database; orthogonal problem | Use structural motif frequency instead |
| Automatic 4J removal | Too risky -- false positives would remove valid 2J/3J correlations | Flag and defer; let agent/LSD explore |
| 5J/6J/7J detection | Extremely rare in standard HMBC; not worth the complexity | Handle via ELIM if encountered (existing mechanism) |
| Intensity-based discrimination | 4J W-pathway couplings can be as intense as 3J; intensity is unreliable | Confirmed by literature: "intensity alone cannot exclude long-range interpretation" |
| LR-HSQMBC integration | Specialized experiment not routinely available | Design API to accept external evidence later |

## Detailed Feature Specifications

### Feature 1: Atom-Type-Pair 4J Probability (CORE)

**What:** For a given HMBC correlation between atom A (carbon, shift_A) and atom B (proton-bearing carbon, shift_B), compute the probability that the correlation is 4J rather than 2J/3J.

**Why:** The current heuristic (Section 3 of nmr-chemist.md) flags ALL aromatic-to-aliphatic HMBC as potential 4J. This over-flags. In ibuprofen, 2 of ~15 HMBC correlations were actually 4J (13%), but the heuristic would flag ~6 (40%). Statistical evidence from the database can narrow this.

**Approach -- Database-Driven Coupling Path Analysis:**

The database contains 928K compounds with known structures and assigned 13C shifts. For each compound:
1. Parse the molecular graph (from SMILES)
2. For each pair of carbon atoms (C_i, C_j) where C_j has attached H:
   - Compute the shortest bond path length between C_i and C_j
   - Record the 13C shifts of both atoms
   - Record the hybridization states of both atoms
   - Record whether either atom is aromatic
3. Aggregate: for atom-type pairs at given shift ranges, what fraction of HMBC-compatible correlations (path length 2-4) are actually 4J?

**Key atom-type pairs for 4J couplings (from NMR literature, HIGH confidence):**

| Carbon A Type | Carbon B Type | Coupling Path | Motif | Relative Intensity |
|---------------|---------------|---------------|-------|-------------------|
| ArCH (sp2, aromatic, 110-160 ppm) | CH2 (sp3, 25-50 ppm) | Ar-Ar-C(sub)-CH2 | Benzylic, W-pathway through para-disubstituted ring | HIGH (W-pathway) |
| ArCH (sp2, aromatic, 110-160 ppm) | CH (sp3, 25-50 ppm) | Ar-Ar-C(sub)-CH | Benzylic methine | HIGH (W-pathway) |
| ArCH (sp2, aromatic, 110-160 ppm) | CH3 (sp3, 10-30 ppm) | Ar-Ar-C(sub)-CH3 | Aromatic methyl | HIGH (W-pathway) |
| ArCq (sp2, aromatic, 120-160 ppm) | CH/CH2/CH3 (sp3, 0-55 ppm) | Ar-Ar-Ar-C(sub) | Through ring to aliphatic | MEDIUM |
| Vinyl CH (sp2, non-aromatic, 100-140 ppm) | CH/CH2 (sp3, 20-50 ppm) | C=C-C-CH | Allylic W-pathway | MEDIUM |
| C=O (sp2, 165-220 ppm) | CH/CH2 (sp3, 20-50 ppm) | O=C-X-C-CH | Through carbonyl + heteroatom | LOW |

**Output model:**

```python
class FourJResult(BaseModel):
    carbon_shift: float
    proton_carbon_shift: float
    carbon_hybridization: str  # "sp2", "sp3"
    proton_carbon_hybridization: str
    carbon_is_aromatic: bool
    proton_carbon_is_aromatic: bool
    probability_4j: float  # 0.0-1.0
    evidence_count: int  # Number of database observations
    classification: str  # "likely_4j", "possible_4j", "unlikely_4j"
    motif: str | None  # "aromatic_benzylic", "aromatic_methyl", "vinyl_allylic", etc.
    recommendation: str  # "defer", "use_extended_range", "include_normally"
```

### Feature 2: W-Pathway Structural Motif Detection

**What:** Identify when an HMBC correlation pair matches a known W-pathway geometry that produces intense 4J couplings.

**Why:** W-pathway 4J couplings are the dangerous ones because they are intense enough to be picked up routinely in HMBC. Non-W-pathway 4J couplings are typically too weak to appear.

**W-pathway motifs (HIGH confidence, textbook NMR):**

1. **Para-disubstituted benzene:** H-C(ring)-C(ring)-C(sub)-C(aliphatic). The W-arrangement through the ring makes ArCH at one position couple to the benzylic carbon at the para position. This is exactly the ibuprofen case.

2. **Meta-coupled aromatics:** H-C(ring)-C(ring)-C(ring)-H. 4J H-H coupling in meta positions (~1-3 Hz). The heteronuclear analog appears in HMBC.

3. **Allylic W-pathway:** H-C=C-C-H. Vinyl proton to allylic proton/carbon through double bond.

4. **Rigid bicyclic systems:** Fixed W-geometry in norbornane-type frameworks.

**Detection logic:**
- Both carbons have known hybridization from `lucy detect hybridisation`
- Carbon A is aromatic (in_aromatic > threshold in hose_stats)
- Carbon B is sp3 (sp3 > threshold)
- Shift ranges match aromatic-to-aliphatic pattern

### Feature 3: CLI Interface (`lucy detect 4j`)

**What:** New CLI subcommand under `lucy detect` that takes HMBC correlations and assesses 4J probability.

**Input options (two modes):**

```bash
# Mode 1: Single correlation assessment
lucy detect 4j --c-shift 129.38 --h-shift 45.03 --format json

# Mode 2: Batch assessment of all HMBC correlations from shift lists
lucy detect 4j --correlations "129.38:45.03,127.26:44.90,141.03:30.12" --format json

# Mode 3: Full assessment with structural context
lucy detect 4j --c-shift 129.38 --h-shift 45.03 --c-hyb sp2 --h-hyb sp3 --c-aromatic --format json
```

**Recommended approach: Mode 1 (single correlation) as primary, Mode 2 (batch) as enhancement.**

Rationale: The nmr-chemist agent already iterates over HMBC correlations during setup. Adding `lucy detect 4j` calls per-correlation fits the existing workflow. Batch mode is an optimization.

**Output (JSON):**

```json
{
  "carbon_shift": 129.38,
  "proton_carbon_shift": 45.03,
  "probability_4j": 0.72,
  "classification": "likely_4j",
  "evidence_count": 4521,
  "motif": "aromatic_to_aliphatic",
  "recommendation": "defer",
  "details": {
    "carbon_hybridization": "sp2 (99.2%)",
    "carbon_aromatic": "yes (97.8%)",
    "proton_carbon_hybridization": "sp3 (99.5%)",
    "path_2_fraction": 0.08,
    "path_3_fraction": 0.20,
    "path_4_fraction": 0.72
  }
}
```

### Feature 4: LSD Bond Range Integration

**What:** When 4J probability is above threshold, suggest `HMBC X Y 2 4` syntax to lsd-engineer instead of deferring the correlation entirely.

**Why:** LSD natively supports extended bond range: `HMBC 6 8 2 4` means "atom 6 correlates with hydrogen atom 8 through 2, 3, or 4 bonds." This is confirmed in the LSD manual (v3.4.9). Currently, the lsd-engineer either includes a correlation as 2-3 bond (default) or defers it entirely. The `HMBC X Y 2 4` syntax provides a middle ground.

**LSD HMBC syntax reference (from manual):**

| Syntax | Meaning |
|--------|---------|
| `HMBC 3 8` | Default: 2 or 3 bonds |
| `HMBC 6 8 2` | Exactly 2 bonds |
| `HMBC 6 8 4` | Exactly 4 bonds (requires ELIM) |
| `HMBC 6 8 2 3` | 2 or 3 bonds (explicit default, never eliminated) |
| `HMBC 6 8 2 4` | 2, 3, or 4 bonds |

**Important constraint:** `HMBC X Y 4` (exactly 4 bonds) requires an ELIM command. But `HMBC X Y 2 4` (range 2-4) does NOT require ELIM because it includes 2 and 3.

**Three-tier recommendation system:**

| 4J Probability | Classification | LSD Recommendation |
|---------------|---------------|-------------------|
| < 0.15 | unlikely_4j | `HMBC X Y` (default 2-3 bonds) |
| 0.15 - 0.50 | possible_4j | `HMBC X Y 2 4` (extended range) |
| > 0.50 | likely_4j | Defer entirely (do not include in early batches) |

**Rationale for thresholds:**
- < 15%: Most correlations fall here. Normal HMBC behavior.
- 15-50%: Genuine ambiguity. Let LSD explore 2-4 bonds without explosion.
- > 50%: More likely 4J than not. Including as 2-3 bond would actively exclude correct structure. Safer to defer.

### Feature 5: Batch Assessment with Cross-Correlation Analysis

**What:** When multiple HMBC correlations are flagged as potential 4J, check if they form a consistent pattern (e.g., multiple 4J correlations to the same aromatic ring system).

**Why:** A single flagged 4J correlation might be a false positive. But if 3 HMBC correlations between aromatic carbons (127-141 ppm) and aliphatic carbons (30-50 ppm) are all flagged, that strongly suggests an aromatic ring with substituents -- reinforcing the 4J diagnosis.

**Logic:**
1. Group flagged correlations by carbon shift clusters
2. If 3+ flagged correlations share carbons in 110-160 ppm range AND connect to carbons in 0-55 ppm range:
   - Upgrade all to "likely_4j" regardless of individual scores
   - Add "aromatic_ring_cluster" motif annotation
3. Report the cluster in the output for the lsd-engineer's constraint inventory

### Feature 6: Database Schema Extension

**What:** New table for computing 4J probabilities from the existing compound/shift/HOSE data.

**Recommended approach: Pre-computed coupling path statistics table.**

```sql
CREATE TABLE coupling_path_stats (
    c1_hyb TEXT NOT NULL,           -- "sp2", "sp3"
    c1_aromatic INTEGER NOT NULL,   -- 0 or 1
    c1_shift_bin INTEGER NOT NULL,  -- shift / 10 (binned to 10 ppm)
    c2_hyb TEXT NOT NULL,
    c2_aromatic INTEGER NOT NULL,
    c2_shift_bin INTEGER NOT NULL,
    path_length INTEGER NOT NULL,   -- 2, 3, or 4
    count INTEGER NOT NULL,
    PRIMARY KEY (c1_hyb, c1_aromatic, c1_shift_bin, c2_hyb, c2_aromatic, c2_shift_bin, path_length)
);
CREATE INDEX idx_coupling_path_shifts ON coupling_path_stats(c1_shift_bin, c2_shift_bin);
```

**Generation algorithm:** During stats generation, for each compound:
1. Parse SMILES to RDKit mol
2. Get all carbon atoms with assigned shifts
3. For each carbon pair (C_i, C_j) where C_j has H > 0:
   - Compute shortest path length via BFS
   - If path is 2, 3, or 4 bonds: record entry
   - Bin shifts to 10 ppm ranges
   - Record hybridization and aromaticity of both carbons
4. Accumulate counts across all compounds

**Why this approach:**
- Pre-computed, fast lookup (< 100ms per query)
- Follows existing pattern (hose_stats is also pre-computed)
- Manageable table size (~50K-200K rows with 10-ppm binning)
- Incremental updates follow existing checkpoint pattern
- Schema version migration from v6 to v7

**Alternative considered and rejected:** Runtime SMILES graph analysis -- too slow (each query would parse hundreds of SMILES).

**Binning strategy:** 10 ppm bins (0-10, 10-20, ..., 210-220). This gives 22 bins per axis. With 2 hybridizations x 2 aromaticity states per carbon and 3 path lengths, theoretical max is ~2 x 2 x 22 x 2 x 2 x 22 x 3 = ~23K rows. Actual will be less (many combinations don't exist).

### Feature 7: Agent Workflow Integration

**What:** How the nmr-chemist, lsd-engineer, and solution-analyst agents use 4J detection results.

**nmr-chemist (detection phase):**
1. After HMBC guided picking, iterate over all HMBC correlations
2. For each correlation where one carbon is aromatic-range (110-160 ppm) and the other is aliphatic-range (0-55 ppm): run `lucy detect 4j --c-shift X --h-shift Y --format json`
3. Parse result; include in [SETUP-COMPLETE] message:
   ```
   Potential 4J correlations (statistical):
   - C4(129.38, ArCH) <-> H-C8(45.03, CH2): prob=0.72, likely_4j, defer
   - C5(127.26, ArCH) <-> H-C9(44.90, CH): prob=0.68, likely_4j, defer
   - C3(141.03, ArCq) <-> H-C7(30.12, CH): prob=0.22, possible_4j, use HMBC X Y 2 4
   ```

**lsd-engineer (constraint building phase):**
1. Read 4J flagging from nmr-chemist's [SETUP-COMPLETE]
2. For "likely_4j" (prob > 0.50): defer as today (add to `deferred_4j` inventory)
3. For "possible_4j" (0.15-0.50): write `HMBC X Y 2 4` in the LSD file
4. For "unlikely_4j" (prob < 0.15): include as normal `HMBC X Y`
5. Update LSDCorrelation model to support `to_lsd_line()` with bond range

**solution-analyst (ranking phase):**
1. After ranking, if top solutions lack aromatic rings but 4J correlations were flagged: confirm diagnosis
2. Use `lucy lsd analyze-j` on top solutions to verify actual path lengths match predictions
3. Report 4J verification status in ranking results

## Feature Dependencies

```
Database schema extension (F6) --> coupling_path_stats table
    |
    v
Statistical detector implementation (F1) --> FourJDetector class
    |
    v
W-pathway motif detection (F2) --> motif classification within detector
    |
    v
CLI interface (F3) --> `lucy detect 4j` command
    |
    v
Batch assessment (F5) --> cross-correlation analysis
    |
    +-- Agent workflow integration (F7) --> skill file updates
    |
    +-- LSD bond range integration (F4) --> lsd-engineer skill update + LSDCorrelation.to_lsd_line() update
```

## MVP Recommendation

**Phase 1 (core -- must ship):**
1. Database schema extension with coupling_path_stats table (F6)
2. Core 4J probability detector (F1) -- single-correlation assessment
3. CLI interface, single-correlation mode (F3, Mode 1)
4. Agent skill updates for nmr-chemist and lsd-engineer (F7)

**Phase 2 (high value -- should ship):**
5. LSD bond range integration -- `HMBC X Y 2 4` output (F4)
6. W-pathway motif annotations (F2)

**Phase 3 (nice to have -- defer if needed):**
7. Batch assessment with cross-correlation analysis (F5)
8. CLI batch mode (F3, Mode 2)

**Defer entirely:**
- 5J+ detection (anti-feature)
- Coupling constant prediction (anti-feature)
- Intensity-based discrimination (anti-feature)

## Thresholds and Classification

**Recommended classification thresholds (initial -- refine with UAT):**

| Metric | Value | Basis |
|--------|-------|-------|
| likely_4j threshold | > 0.50 probability | Conservative: defer only when more-likely-than-not |
| possible_4j threshold | 0.15 - 0.50 probability | Use extended bond range as hedge |
| unlikely_4j threshold | < 0.15 probability | Treat as normal 2-3 bond correlation |
| Minimum evidence count | >= 50 observations | Below this, fall back to heuristic |
| Shift bin width | 10 ppm | Balance granularity vs data sparsity |

**Calibration approach:** After building the coupling_path_stats table, validate thresholds against known 4J cases:
- Ibuprofen: ArCH(129.38) to CH2(45.03) and ArCH(127.26) to CH(44.90) should classify as likely_4j
- Non-4J controls: typical HMBC correlations in the same compound should classify as unlikely_4j

## Comparison with Other CASE Systems

| Feature | ACD/SE | WebCocon | Sherlock | lucy-ng (proposed) |
|---------|--------|----------|----------|-------------------|
| 4J handling | Fuzzy Structure Generation: auto-elongate suspicious correlations | 4J-Flag parameter: user sets max allowed 4J count | Manual marking | Statistical probability per-correlation |
| Detection method | Logical contradiction analysis (90% success) | User identifies beforehand | None (user marks in pyLSD) | Database-backed frequency analysis |
| Automation | Semi-automatic (FSG) | Manual flag count | Manual | Fully automatic statistical flagging |
| Bond range in solver | Adjustable | Not applicable (combinatorial) | pyLSD/LSD `HMBC X Y 2 4` | LSD `HMBC X Y 2 4` |

ACD/SE's approach (detect contradictions, then elongate) is reactive -- it catches 4J after they cause problems. Lucy-ng's proposed approach is proactive -- flag before LSD runs, preventing the problem. This is a genuine advantage.

WebCocon's 4J-Flag approach requires the user to know how many 4J correlations exist. Lucy-ng's per-correlation probability eliminates this guessing.

## Sources

- [Incorporation of 4J-HMBC and NOE Data into CASE with WebCocon](https://pmc.ncbi.nlm.nih.gov/articles/PMC8398166/) -- 4J-Flag parameter design
- [ACD/Structure Elucidator: 20 Years](https://pmc.ncbi.nlm.nih.gov/articles/PMC8588187/) -- Fuzzy Structure Generation for NSC handling
- [Sherlock CASE System](https://pmc.ncbi.nlm.nih.gov/articles/PMC9920390/) -- Open-source CASE with pyLSD
- [Assessment of Long-Range C,H Coupling in Carbazolequinones](https://pmc.ncbi.nlm.nih.gov/articles/PMC10744212/) -- 4J/5J in rigid frameworks
- [LSD Manual v3.4.9](file:///Users/steinbeck/Dropbox/develop/LSD/MANUAL_ENG.html) -- HMBC X Y N M bond range syntax (confirmed locally)
- [Long-range heteronuclear correlation](https://chem.ch.huji.ac.il/nmr/techniques/2d/hmbc/hmbc.html) -- HMBC fundamentals
- [Using HMBC and ADEQUATE to Define Long-Range Coupling Pathways](https://pubs.acs.org/doi/10.1021/np400562u) -- Crews Rule discussion
- lucy-ng v4.0 UAT (ibuprofen CASE1) -- confirmed 4J failure mode with ArCH(129.38)/CH2(45.03) and ArCH(127.26)/CH(44.90)
