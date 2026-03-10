# Architecture: 4J HMBC Coupling Detection

**Project:** lucy-ng v7.0 Statistical 4J Detection
**Researched:** 2026-03-10
**Confidence:** HIGH (based on thorough existing codebase analysis, established patterns, confirmed problem from UAT)

## Problem Statement

The v4.0 UAT proved that 4J HMBC couplings through aromatic rings silently exclude the correct structure from LSD solutions. The current system uses a heuristic (shift-range-based flagging in the nmr-chemist agent: aromatic 110-160 ppm paired with benzylic 0-55 ppm) that flags suspicious correlations but has no statistical basis. We need database-driven probability scores for each HMBC correlation being 4J, so the agent can make informed deferral decisions rather than relying on crude shift ranges.

## Recommended Architecture

### Core Concept: CH Bond-Path Distance Statistics

For each compound in the database (928K compounds, 24M shifts), enumerate all carbon-hydrogen pairs where:
- The carbon has an assigned 13C shift with a known atom_index
- The hydrogen is attached to a different carbon that also has an assigned 13C shift (HMBC-observable pairs)
- Both atoms are connected via a bond path in the molecular graph

Record the shortest bond-path distance (2, 3, 4, 5+) for each pair. Aggregate by carbon HOSE code and proton-bearing carbon HOSE code pairs.

This gives us: "Given a carbon with HOSE code X correlated to a proton on a carbon with HOSE code Y, what is the probability this is a 2J, 3J, or 4J coupling?"

### Why HOSE-Code Pairs (Not Atom-Type Pairs)

**Decision: Use HOSE codes at radius 2.**

Rationale:
- Simple atom types (sp2-C, sp3-CH2) are too coarse. An aromatic CH at 130 ppm has fundamentally different 4J coupling behavior than an olefinic CH at 130 ppm, but both are "sp2 CH".
- HOSE codes at radius 2 capture the local environment (aromatic vs olefinic, adjacent heteroatoms, ring membership) without being so specific that data becomes sparse.
- The existing `hose_stats` table already uses HOSE codes as the primary statistical key, so this is consistent with the project's established approach.
- Radius 2 balances specificity vs data density. Radius 1 only encodes immediate bond partners -- every aromatic CH would get the same code. Radius 3+ creates so many unique codes that most pairs would have fewer than 10 observations, making statistics unreliable.

### Alternative Considered: Shift-Pair Statistics

Store statistics by (carbon_shift_bin, proton_carbon_shift_bin) pairs instead of HOSE codes.

**Why not:** Shift alone cannot distinguish aromatic CH from olefinic CH from heteroaromatic CH. HOSE codes encode structural context that shift ranges cannot. The whole point of 4J detection is understanding structural pathways, not just shift proximity. If shift-pair binning were sufficient, the current heuristic (aromatic vs benzylic shift ranges) would already work -- it does not.

## Database Schema Design

### New Table: `coupling_path_stats`

```sql
CREATE TABLE IF NOT EXISTS coupling_path_stats (
    carbon_hose TEXT NOT NULL,      -- HOSE code of the observed carbon (radius 2)
    h_carbon_hose TEXT NOT NULL,    -- HOSE code of the proton-bearing carbon (radius 2)
    bond_distance INTEGER NOT NULL, -- Shortest bond path: 2, 3, 4, 5 (5 means 5+)
    count INTEGER NOT NULL,         -- Number of observations across all compounds
    PRIMARY KEY (carbon_hose, h_carbon_hose, bond_distance)
);

CREATE INDEX IF NOT EXISTS idx_coupling_path_carbon
ON coupling_path_stats(carbon_hose);

CREATE INDEX IF NOT EXISTS idx_coupling_path_pair
ON coupling_path_stats(carbon_hose, h_carbon_hose);
```

### Why a Separate Table (Not Extending hose_stats)

1. **Different dimensionality.** `hose_stats` is keyed by a single HOSE code (one atom). Coupling path stats are inherently pairwise (two HOSE codes). The data structure is fundamentally different.
2. **Different cardinality.** `hose_stats` has ~7.9M rows. `coupling_path_stats` will have significantly more rows because each compound contributes O(C x H) pairs where C = number of carbons and H = number of proton-bearing carbons.
3. **Different query patterns.** `hose_stats` is queried by shift window (range scan on mean). `coupling_path_stats` is queried by HOSE code pair (exact match lookup).
4. **Isolation.** Adding a new table leaves the existing detection pipeline completely untouched. No risk of breaking hybridisation, neighbour, or HHB detection.

### Schema Version: v7

Follow the established migration pattern (v3->v4->v5->v6):

```python
# In schema.py
SCHEMA_VERSION = 7

def migrate_v6_to_v7(conn: sqlite3.Connection) -> None:
    """Add coupling_path_stats table for 4J HMBC detection."""
    cursor = conn.cursor()
    cursor.execute(CREATE_COUPLING_PATH_STATS_TABLE)
    cursor.execute(CREATE_COUPLING_PATH_CARBON_INDEX)
    cursor.execute(CREATE_COUPLING_PATH_PAIR_INDEX)
    cursor.execute(
        "UPDATE schema_meta SET value = ? WHERE key = ?",
        ("7", "schema_version"),
    )
    conn.commit()
```

**ALTER TABLE migration, not full regeneration.** The new table is completely independent of existing tables. The migration creates the empty table; population is a separate batch step (same pattern as `bond_pair_stats` generation in v6).

### Index Strategy

Two indices cover the two expected query patterns:

1. **`idx_coupling_path_pair`** on `(carbon_hose, h_carbon_hose)` -- Primary query: "What is the bond-distance distribution for THIS specific HOSE code pair?" Used for precise per-correlation scoring.

2. **`idx_coupling_path_carbon`** on `(carbon_hose)` -- Fallback query: "What bond distances are observed for ANY correlation involving this carbon environment?" Used when the exact pair has insufficient data (marginalizes over all proton partners).

### Estimated Table Size

- 928K compounds, average ~12 carbons each, average ~8 proton-bearing carbons
- Per compound: up to 12 x 8 = ~96 CH pairs, but filtering to bond paths 2-5 reduces this
- RDKit `GetShortestPath` filters: only keep pairs with path length 2-5 (skip disconnected or very distant)
- Estimate: ~40-60 relevant pairs per compound on average
- Raw observations: ~37-56M across all compounds
- After HOSE-pair aggregation: likely 5-15M unique (carbon_hose, h_carbon_hose, bond_distance) rows
- Storage estimate: ~300-600 MB additional in SQLite (text HOSE codes are the bulk)
- Total DB growth: 2.8 GB -> ~3.2-3.4 GB

## Generation Pipeline

### New Module: `coupling_path_generator.py`

Location: `src/lucy_ng/prediction/coupling_path_generator.py`

Following the established patterns of `BondPairStatsGenerator` and `ResumableHOSEStatsGenerator`:

```python
class CouplingPathStatsGenerator:
    """Generate coupling path distance statistics from compound database.

    For each compound: parse SMILES, map atom_index to shift data,
    enumerate all (carbon, proton-bearing-carbon) pairs, compute
    shortest bond path via RDKit, generate HOSE codes at radius 2,
    accumulate (carbon_hose, h_carbon_hose, distance) -> count.
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def generate_all(self, progress: bool = True) -> dict:
        """Iterate all compounds, compute CH pair bond distances.

        Algorithm per compound:
        1. Parse SMILES to RDKit mol (implicit H -- NO AddHs!)
        2. Load atom_index -> shift mapping from shifts table
        3. Skip compound if any shift has NULL atom_index
        4. Identify all carbon atoms with shifts
        5. Partition: proton-bearing carbons (hydrogen_count > 0)
                      and all carbons (including quaternary)
        6. For each (carbon_c, carbon_h) pair where carbon_c != carbon_h:
           a. carbon_c = the observed carbon (can be any carbon)
           b. carbon_h = proton-bearing carbon (hydrogen_count > 0)
           c. Compute shortest bond path: GetShortestPath(mol, c_idx, h_idx)
           d. Record path length (cap at 5 for 5+)
           e. Generate HOSE codes at radius 2 for both atoms
           f. Accumulate: (c_hose_r2, h_hose_r2, path_length) -> count += 1
        7. After all compounds: batch INSERT into coupling_path_stats
        """
```

### Atom Index Mapping

The `shifts` table stores `atom_index` from the original SDF/NMRShiftDB source. Key considerations:

- **COCONUT compounds:** 1-based atom indices. Convert to 0-based: `atom_idx_0based = atom_index - 1` (established convention).
- **NMRShiftDB compounds:** Some have `atom_index = NULL`. Skip these compounds entirely (~68K shifts have NULL atom_index, affecting ~3-5% of compounds). This is acceptable for statistical purposes.
- **Validation:** Always verify `mol.GetAtomWithIdx(atom_idx).GetSymbol() == 'C'` before proceeding. Mismatches indicate index translation errors.

Query: ~24M shifts have non-null atom_index (confirmed from DB query: 23,994,980). Coverage is excellent at ~99.7%.

### HOSE Code Generation

Use the existing `HOSECodeGenerator` class:
- `generate_for_atom(mol, atom_idx, radius=2)` for each carbon in the pair
- **Critical:** molecules must use implicit hydrogens (no `AddHs()`) per the project convention
- HOSE codes at radius 2 are short strings (~20-40 chars), memory-efficient for aggregation

### Resumability

Use the existing `operation_checkpoint` table with new keys:
- `coupling_path_last_compound_id` -- last successfully processed compound ID
- `coupling_path_compounds_processed` -- count for progress reporting
- `coupling_path_compounds_failed` -- compounds that couldn't be processed (bad SMILES, missing indices)

Process compounds in ID order, checkpoint every 10K compounds. On resume, skip compounds with ID <= checkpoint value.

### Performance Estimate

- 928K compounds at ~50-100ms each (SMILES parse + HOSE gen at r=2 for ~12 atoms + path computation for ~50 pairs)
- Total: ~13-26 hours (one-time batch job)
- Memory: accumulate in a `dict[(str, str, int), int]`. At 10-15M entries with ~40-char HOSE strings per key, expect ~2-4 GB RAM.
- If memory is a concern: flush accumulated counts to DB every 100K compounds using INSERT OR UPDATE (add to existing count). This trades I/O for memory.
- Final batch INSERT/UPDATE: single transaction, ~1-2 minutes for 10M rows.

### CLI Command

```bash
lucy database generate-coupling-stats [--db PATH] [--resume/--fresh] [--chunk-size N]
```

Following the pattern of `lucy database generate-bond-stats`. Added to `cli/database.py`.

## Detection Pipeline Integration

### New Method: `StatisticalDetector.detect_4j_coupling()`

Single-correlation scoring:

```python
def detect_4j_coupling(
    self,
    carbon_shift: float,
    h_carbon_shift: float,
    radius: int = 2,
    window_ppm: float = 2.0,
) -> CouplingPathResult:
    """Estimate bond-distance probability for a single HMBC correlation.

    Steps:
    1. Find HOSE codes at radius 2 whose mean shift is within
       window_ppm of carbon_shift -> candidate set A
    2. Find HOSE codes at radius 2 whose mean shift is within
       window_ppm of h_carbon_shift -> candidate set B
    3. Query coupling_path_stats for all (a, b, *) where a in A, b in B
    4. Aggregate counts: total_2j, total_3j, total_4j, total_5j+
    5. Compute frequencies: p_4j = total_4j / total_all

    Fallback: If pair query returns no data, query carbon-only
    (aggregate over all h_carbon partners for set A HOSE codes).
    """
```

### Batch Method: `StatisticalDetector.detect_4j_batch()`

Agent-facing method that scores all HMBC correlations at once:

```python
def detect_4j_batch(
    self,
    correlations: list[tuple[float, float]],  # (carbon_shift, h_carbon_shift) pairs
    radius: int = 2,
    window_ppm: float = 2.0,
) -> list[CouplingPathResult]:
    """Score all HMBC correlations for 4J risk."""
```

The batch method optimizes by:
- Pre-loading all relevant HOSE codes for all unique shifts in one query
- Reusing HOSE code lookups across correlations that share the same carbon shift
- Single database connection for the entire batch

### New Result Models

Added to `detection/models.py`:

```python
class CouplingPathDistribution(BaseModel):
    """Distribution of bond-path distances for a CH correlation."""
    j2: float = 0.0   # P(2-bond coupling)
    j3: float = 0.0   # P(3-bond coupling)
    j4: float = 0.0   # P(4-bond coupling)
    j5_plus: float = 0.0  # P(5+ bond coupling)

    @property
    def p_long_range(self) -> float:
        """P(4J or longer) -- the key metric for deferral decisions."""
        return self.j4 + self.j5_plus

class CouplingPathResult(BaseModel):
    """Result of 4J coupling detection for a single correlation."""
    carbon_shift: float
    h_carbon_shift: float
    distribution: CouplingPathDistribution
    total_observations: int
    unique_pairs: int  # Number of HOSE pair combinations that contributed
    has_data: bool
    risk_level: str  # "low", "medium", "high"
    warning: str | None = None
```

Risk classification thresholds:
- `p_long_range < 0.05` -> `"low"` (safe to include as normal HMBC)
- `0.05 <= p_long_range < 0.15` -> `"medium"` (defer to later batch)
- `p_long_range >= 0.15` -> `"high"` (strongly defer, likely 4J)

These thresholds are initial estimates. They should be calibrated after generation by checking known 4J cases (ibuprofen HMBC 4-8 and 6-9 from UAT).

### CLI Command: `lucy detect 4j`

Two modes -- single correlation and batch:

```bash
# Single correlation
lucy detect 4j 129.38 45.03 --format json

# Batch mode (primary agent-facing command)
lucy detect 4j-batch --correlations "129.38:45.03,127.26:44.90,141.2:30.1" --format json
```

**Batch JSON output:**
```json
{
  "correlations": [
    {
      "carbon_shift": 129.38,
      "h_carbon_shift": 45.03,
      "distribution": {"j2": 0.12, "j3": 0.55, "j4": 0.28, "j5_plus": 0.05},
      "p_long_range": 0.33,
      "risk": "high",
      "total_observations": 4521,
      "recommendation": "defer"
    },
    {
      "carbon_shift": 127.26,
      "h_carbon_shift": 44.90,
      "distribution": {"j2": 0.10, "j3": 0.52, "j4": 0.31, "j5_plus": 0.07},
      "p_long_range": 0.38,
      "risk": "high",
      "total_observations": 3892,
      "recommendation": "defer"
    },
    {
      "carbon_shift": 141.2,
      "h_carbon_shift": 30.1,
      "distribution": {"j2": 0.25, "j3": 0.68, "j4": 0.06, "j5_plus": 0.01},
      "p_long_range": 0.07,
      "risk": "medium",
      "total_observations": 8234,
      "recommendation": "defer_late"
    }
  ],
  "summary": {
    "total": 3,
    "high_risk": 2,
    "medium_risk": 1,
    "low_risk": 0
  }
}
```

## Agent Team Integration

### Current Flow (v6.0 heuristic)

1. **nmr-chemist** flags potential 4J by shift ranges (aromatic 110-160 ppm paired with benzylic 0-55 ppm)
2. **lsd-engineer** defers all flagged correlations to last HMBC batch
3. **devils-advocate** validates deferral decisions

### New Flow (v7.0 statistical)

1. **nmr-chemist** runs `lucy detect 4j-batch` on ALL HMBC correlations after peak picking
   - Replaces the heuristic shift-range check entirely
   - Reports per-correlation risk scores in [SETUP-COMPLETE] message
   - New field in output: `4J risk scores:` with per-correlation entries

2. **lsd-engineer** reads risk scores from nmr-chemist's message
   - `risk: high` -> store in `deferred_4j`, defer to final batch (same as current deferral behavior)
   - `risk: medium` -> store in `deferred_4j`, defer to late batch (batch N-1)
   - `risk: low` -> include normally in regular HMBC batches
   - Constraint inventory retains the existing `"deferred_4j"` field, now populated from statistical scores instead of heuristic flags

3. **devils-advocate** validates based on statistical evidence
   - Can challenge if engineer ignores a high-risk flagging
   - Can challenge if engineer defers a low-risk correlation without justification
   - Statistical p-values provide objective basis for challenges

### Timing: Run Once, Before First LSD Run

4J detection runs **once** during nmr-chemist's setup phase, not iteratively. Rationale:
- The HMBC correlation list does not change between LSD iterations (same peaks, same peak picking)
- The statistical risk scores do not change between iterations (same database, deterministic)
- Running once avoids redundant computation (~500ms per batch is small but pointless to repeat)
- The deferral decisions inform the ENTIRE iteration strategy from the start

### Agent Skill Changes

**nmr-chemist (lucy-nmr-chemist.md):**
- Remove Section 3 ("4J HMBC Coupling Detection") heuristic logic
- Replace with: "Run `lucy detect 4j-batch` on all HMBC correlations"
- Update [SETUP-COMPLETE] format: replace heuristic "Potential 4J correlations:" with statistical "4J risk scores:" including p_long_range and risk level per correlation

**lsd-engineer (lucy-lsd-engineer.md):**
- "4J Deferral Rule" section: change trigger from "nmr-chemist flags as Potential 4J" to "nmr-chemist reports risk: high or medium"
- Add handling for medium-risk correlations (defer to late batch, not final batch)
- No structural changes to the deferral mechanism itself -- only the trigger changes

**devils-advocate (lucy-devils-advocate.md):**
- Add 4J risk score validation to pre-LSD-run checks
- "If high-risk 4J correlation appears in early HMBC batch, flag as error"

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `prediction/coupling_path_generator.py` (NEW) | One-time DB population: iterate 928K compounds, compute CH pair bond paths, aggregate by HOSE pairs | DatabaseManager, HOSECodeGenerator |
| `coupling_path_stats` table (NEW, schema v7) | Store pairwise HOSE bond-distance counts | SQLite |
| `detection/detector.py` (MODIFIED) | New methods: `detect_4j_coupling()`, `detect_4j_batch()` | DatabaseManager, coupling_path_stats |
| `detection/models.py` (MODIFIED) | New models: `CouplingPathDistribution`, `CouplingPathResult` | Pydantic |
| `cli/detect.py` (MODIFIED) | New subcommands: `lucy detect 4j`, `lucy detect 4j-batch` | StatisticalDetector |
| `cli/database.py` (MODIFIED) | New command: `lucy database generate-coupling-stats` | CouplingPathStatsGenerator |
| `database/schema.py` (MODIFIED) | v7 schema, `migrate_v6_to_v7()` | SQLite |
| `database/manager.py` (MODIFIED) | New query: `get_coupling_path_stats(carbon_hose, h_carbon_hose)` | SQLite |
| `database/models.py` (MODIFIED) | New model: `CouplingPathStatsRecord` | Pydantic |
| nmr-chemist agent skill (MODIFIED) | Calls `lucy detect 4j-batch`, reports scores | CLI |
| lsd-engineer agent skill (MODIFIED) | Reads risk scores, applies deferral | nmr-chemist output |
| devils-advocate agent skill (MODIFIED) | Validates deferral decisions against risk scores | lsd-engineer output |

### Data Flow

```
                  [One-time generation pipeline]
compounds + shifts + SMILES (existing DB)
        |
        v
CouplingPathStatsGenerator.generate_all()
  For each compound:
    SMILES -> RDKit mol (implicit H)
    atom_index -> shift mapping
    For each (carbon, h_carbon) pair:
      GetShortestPath() -> bond_distance
      HOSECodeGenerator.generate_for_atom(mol, c_idx, radius=2) -> c_hose
      HOSECodeGenerator.generate_for_atom(mol, h_idx, radius=2) -> h_hose
      Accumulate: (c_hose, h_hose, distance) -> count
        |
        v
coupling_path_stats table (SQLite, schema v7)


                  [Runtime detection pipeline]
HMBC correlations (from peak picking)
  e.g., [(129.38, 45.03), (127.26, 44.90), ...]
        |
        v
lucy detect 4j-batch --correlations "129.38:45.03,..." --format json
        |
        v
StatisticalDetector.detect_4j_batch()
  For each (carbon_shift, h_carbon_shift):
    1. Query hose_stats: shift window -> matching HOSE codes (set A, set B)
    2. Query coupling_path_stats: (A x B) -> distance distributions
    3. Aggregate: total_2j, total_3j, total_4j, total_5j+
    4. Compute: p_long_range = (total_4j + total_5j+) / total_all
    5. Classify: risk level based on thresholds
        |
        v
JSON output -> nmr-chemist [SETUP-COMPLETE] -> lsd-engineer deferral
```

## Patterns to Follow

### Pattern 1: Generator Pattern (from BondPairStatsGenerator)

- Constructor takes `DatabaseManager`
- `generate_all(progress=True)` iterates compounds with tqdm progress bar
- Returns raw counts dict for inspection/testing
- Separate `save_to_database()` or integrated DB writes with checkpointing
- CLI command: `lucy database generate-coupling-stats`

### Pattern 2: Detection Pattern (from detect_hybridisation/detect_neighbours)

- Method on existing `StatisticalDetector` class (not a new class)
- Returns Pydantic result model with `.summary()` method for text output
- CLI subcommand under `lucy detect` (not a new command group)
- Supports `--format json` for agent consumption
- `--db` option with `DatabaseFinder.find_hose_database()` fallback

### Pattern 3: Schema Migration (from migrate_v5_to_v6)

- Function in `schema.py`: `migrate_v6_to_v7(conn)`
- CREATE TABLE for new table (no ALTER on existing tables)
- Update `schema_meta` version
- Single transaction with commit
- `SCHEMA_VERSION = 7` constant update
- Registered in the migration chain

### Pattern 4: Database Model (from HOSEStatsRecord/BondPairStatsRecord)

- Pydantic BaseModel in `database/models.py`
- Maps directly to table columns
- Used by both generator (write) and detector (read)

## Anti-Patterns to Avoid

### Anti-Pattern 1: Embedding Pairwise Statistics in hose_stats

**What:** Adding columns like `avg_4j_probability` to the existing `hose_stats` table.
**Why bad:** Coupling is a pairwise property (two atoms). Reducing it to a single-atom statistic loses the pair-specific information that makes 4J detection accurate. An aromatic CH at 130 ppm has very different 4J behavior depending on whether the partner is a benzylic CH2 at 45 ppm or an aliphatic CH3 at 20 ppm.

### Anti-Pattern 2: Full Database Regeneration

**What:** Requiring users to regenerate the entire 2.8 GB database from scratch to add coupling stats.
**Why bad:** Database download from Figshare takes ~30 minutes. Users should be able to run `lucy database migrate` + `lucy database generate-coupling-stats` on their existing database. The coupling_path_stats table is purely additive.

### Anti-Pattern 3: Runtime Bond-Path Computation

**What:** Computing bond paths at CASE-solving time by parsing each candidate compound's SMILES.
**Why bad:** At CASE time, we do not know the structure (that is what we are solving for). We need pre-computed population-level statistics from the reference database, not per-candidate analysis. The question is: "Given these HOSE environments, how likely is this correlation to be 4J across ALL known compounds?" -- not "Is this correlation 4J in one specific candidate?"

### Anti-Pattern 4: Using HOSE Radius 1 or Radius 3+

**Radius 1 too coarse:** Only encodes immediate bond partners. Every aromatic CH would get the same HOSE code. Cannot distinguish para-substituted benzene CH from isolated benzene CH.
**Radius 3+ too specific:** Creates so many unique codes that most pairs have fewer than 10 observations. Statistics become unreliable. Radius 2 is the sweet spot: ~20-40 character codes that capture ring membership, adjacent heteroatoms, and bond orders while retaining statistical density.

### Anti-Pattern 5: Running 4J Detection Iteratively

**What:** Re-running `lucy detect 4j-batch` at each LSD iteration.
**Why bad:** The HMBC peak list and the database are both unchanged between iterations. The results are deterministic. Re-running wastes time and adds complexity. Run once during setup, use scores throughout all iterations.

## Scalability Considerations

| Concern | Current (v6) | After v7 |
|---------|-------------|----------|
| DB file size | 2.8 GB | ~3.2-3.4 GB (+300-600 MB) |
| Generation time | N/A | ~13-26 hours (one-time batch) |
| Detection query time | <50ms per query (hybridisation) | <100ms per single correlation |
| Batch detection (12 HMBC correlations) | N/A (heuristic, 0ms) | <500ms total |
| Agent workflow impact | Heuristic (in-agent, 0ms compute) | One CLI call during setup (~1s) |
| Memory during generation | N/A | ~2-4 GB for accumulation dict |
| Figshare distribution | 830 MB compressed | ~900-950 MB compressed |

The runtime impact on the CASE workflow is negligible -- one sub-second CLI call during the setup phase. The generation is a one-time batch job comparable in duration to HOSE stats regeneration.

## Open Questions

1. **HOSE radius fallback:** Should we store both radius 1 and radius 2 statistics and fall back to radius 1 when radius 2 data is sparse? **Recommendation:** Start with radius 2 only. After generation, analyze data sparsity. If >20% of HMBC correlations in test cases hit zero observations at radius 2, add radius 1 as a follow-up. This avoids doubling the table size speculatively.

2. **Compounds with NULL atom_index:** ~70K shifts have NULL atom_index. These compounds are skipped during generation. With ~24M non-null atom_index shifts across ~928K compounds, coverage is ~99.7%. This is more than sufficient for reliable statistics.

3. **Quaternary carbon handling:** HMBC correlates a carbon to a proton on a DIFFERENT carbon. Both quaternary carbons (hydrogen_count=0) and proton-bearing carbons (hydrogen_count>0) can be the "observed carbon" side. Only proton-bearing carbons can be the "proton source" side. The generator must track both roles correctly.

4. **Figshare update:** The pre-built database on Figshare will need a new version upload once coupling_path_stats is populated. Plan this as a post-generation step.

5. **Threshold calibration:** The risk thresholds (0.05/0.15) are initial estimates. After generation, validate against the known ibuprofen 4J cases: HMBC C4a(129.38)-H(45.03) and C5a(127.26)-H(44.90) should both score "high" risk. Adjust thresholds if they do not.

## Sources

- Existing codebase (HIGH confidence):
  - `src/lucy_ng/database/schema.py` -- v6 schema, migration patterns
  - `src/lucy_ng/database/manager.py` -- query and insert patterns
  - `src/lucy_ng/database/models.py` -- HOSEStatsRecord, BondPairStatsRecord patterns
  - `src/lucy_ng/prediction/stats_generator.py` -- ResumableHOSEStatsGenerator, WelfordAccumulator
  - `src/lucy_ng/prediction/bond_pair_generator.py` -- BondPairStatsGenerator pattern
  - `src/lucy_ng/prediction/hose.py` -- HOSECodeGenerator
  - `src/lucy_ng/detection/detector.py` -- StatisticalDetector class, detection methods
  - `src/lucy_ng/detection/models.py` -- result model patterns
  - `src/lucy_ng/cli/detect.py` -- CLI command patterns
- Agent skills (HIGH confidence):
  - `~/.claude/agents/lucy-nmr-chemist.md` -- Section 3 (current 4J heuristic)
  - `~/.claude/agents/lucy-lsd-engineer.md` -- 4J Deferral Rule section
- Problem evidence (HIGH confidence):
  - v4.0 UAT findings in MEMORY.md -- confirmed 4J root cause, specific correlations identified
  - `.planning/STATE.md` -- project context, milestone history
- Database analysis (HIGH confidence):
  - Direct queries against production DB (`lucy-ng-derep.db`): 928K compounds, 24M shifts, 99.7% with atom_index, schema v6
  - Fragment library DB (`lucy-ng-fragments.db`): separate file, confirms architectural precedent for new tables

---

*Architecture research for: v7.0 Statistical 4J HMBC Detection*
*Researched: 2026-03-10*
