# Phase 34: Hybridisation Detection - Research

**Researched:** 2026-02-10
**Domain:** Statistical detection from HOSE code databases for NMR structure elucidation
**Confidence:** HIGH

## Summary

This phase extends lucy-ng's HOSE statistics database to enable statistical detection of structural constraints from 13C chemical shift queries. The research reveals that hybridisation state (sp3/sp2/sp1) is already encoded in HOSE code prefixes (C-4/C-3/C-2), requiring only database schema extension and frequency distribution computation—no new dependencies needed.

The standard approach in modern CASE systems (Sherlock, nmrshiftdb2) uses shift window queries (typically ± 2 ppm) against HOSE statistics databases, computing frequency distributions for structural features and filtering rare states below 1% occurrence. Lucy-ng already has all infrastructure in place: the SQLite database, HOSE generator, stats computation pipeline, and CLI patterns.

Implementation extends existing patterns: add 8 columns to hose_stats table (sp3/sp2/sp1 counts + neighbor counts), update stats_generator.py's computation loop to extract hybridisation from HOSE prefix, create detection module mirroring prediction module architecture, and add `lucy detect hybridisation` CLI command following existing Click patterns.

**Primary recommendation:** Extend database schema with migration script, compute hybridisation during HOSE stats generation loop, query with shift ± 2 ppm window, return distributions excluding states < 1%.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLite | 3.x | Database backend | Already used for hose_stats, zero new deps |
| RDKit | 2023.0+ | Atom hybridisation extraction | Already installed, provides GetHybridization() |
| Click | 8.0+ | CLI framework | Project standard, lucy CLI uses Click groups |
| Pydantic | 2.0+ | Data models | Project standard for validation/serialization |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 7.0+ | Testing | All new features require tests |
| tqdm | 4.0+ | Progress bars | Stats generation (already used) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLite | PostgreSQL | Overkill for single-user analysis, breaks portability |
| Frequency counts | Machine learning | Unnecessary complexity, less explainable |
| New detection module | Extend predictor | Wrong separation of concerns, detection != prediction |

**Installation:**
```bash
# No new dependencies - all libraries already in pyproject.toml
pip install -e .  # Uses existing dependencies
```

## Architecture Patterns

### Recommended Project Structure
```
src/lucy_ng/
├── database/
│   ├── schema.py            # Add migration to v4 schema
│   ├── models.py            # Extend HOSEStatsRecord with detection fields
│   └── manager.py           # Add get_hose_stats_by_shift_window()
├── detection/               # NEW MODULE (mirrors prediction/)
│   ├── __init__.py          # Export StatisticalDetector
│   ├── detector.py          # StatisticalDetector class
│   └── models.py            # DetectionResult, HybridisationDistribution
├── prediction/
│   └── stats_generator.py  # Extend to compute hybridisation stats
└── cli/
    └── detect.py            # NEW CLI group: lucy detect hybridisation
```

### Pattern 1: Database Schema Migration
**What:** Add columns to existing hose_stats table without breaking backward compatibility
**When to use:** Extending schema for new features on deployed databases
**Example:**
```python
# src/lucy_ng/database/schema.py
SCHEMA_VERSION = 4  # Increment from 3

# Migration function for v3 → v4
def migrate_v3_to_v4(conn: sqlite3.Connection) -> None:
    """Add hybridisation and neighbor columns to hose_stats."""
    cursor = conn.cursor()

    # Add columns with default values
    cursor.execute("ALTER TABLE hose_stats ADD COLUMN sp3_count INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE hose_stats ADD COLUMN sp2_count INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE hose_stats ADD COLUMN sp1_count INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE hose_stats ADD COLUMN c_neighbor_count INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE hose_stats ADD COLUMN o_neighbor_count INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE hose_stats ADD COLUMN n_neighbor_count INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE hose_stats ADD COLUMN s_neighbor_count INTEGER DEFAULT 0")
    cursor.execute("ALTER TABLE hose_stats ADD COLUMN halogen_neighbor_count INTEGER DEFAULT 0")

    # Update schema version
    cursor.execute(
        "UPDATE schema_meta SET value = ? WHERE key = ?",
        (str(SCHEMA_VERSION), "schema_version")
    )
    conn.commit()
```

### Pattern 2: Extract Hybridisation from HOSE Prefix
**What:** Parse HOSE code prefix "C-N" where N encodes hybridisation
**When to use:** During HOSE statistics generation loop
**Example:**
```python
# In stats_generator.py process loop
from rdkit.Chem import HybridizationType

def extract_hybridisation(atom: Atom) -> str:
    """Extract hybridisation state from RDKit atom.

    Returns: "sp3", "sp2", or "sp1"
    """
    hyb = atom.GetHybridization()
    if hyb == HybridizationType.SP3:
        return "sp3"
    elif hyb == HybridizationType.SP2:
        return "sp2"
    elif hyb == HybridizationType.SP:
        return "sp1"
    else:
        # S, UNSPECIFIED, etc. - treat as sp3 (saturated)
        return "sp3"

# In aggregation loop (ResumableHOSEStatsGenerator._process_chunk):
for atom_idx, shift_ppm in shifts:
    atom = mol.GetAtomWithIdx(atom_idx)
    if atom.GetSymbol() != "C":
        continue

    hybridisation = extract_hybridisation(atom)
    # Store in accumulator for this (hose_code, radius) key
    accumulators[(hose_code, radius)].add_observation(
        shift_ppm,
        hybridisation
    )
```

### Pattern 3: Shift Window Query
**What:** Query database for all HOSE codes within ± window of target shift
**When to use:** Detection queries (unlike prediction which uses exact HOSE match)
**Example:**
```python
# src/lucy_ng/database/manager.py
def get_hose_stats_by_shift_window(
    self,
    shift_ppm: float,
    radius: int,
    window_ppm: float = 2.0
) -> list[HOSEStatsRecord]:
    """Query HOSE stats within shift window.

    Args:
        shift_ppm: Target 13C shift
        radius: HOSE radius to query
        window_ppm: Query window (default ± 2 ppm)

    Returns:
        List of HOSEStatsRecord within [shift - window, shift + window]
    """
    cursor = self.connection.cursor()
    cursor.execute(
        """
        SELECT hose_code, radius, mean, std, count,
               sp3_count, sp2_count, sp1_count
        FROM hose_stats
        WHERE radius = ?
          AND mean BETWEEN ? AND ?
          AND count >= 5  -- Minimum observations for reliability
        """,
        (radius, shift_ppm - window_ppm, shift_ppm + window_ppm)
    )
    return [HOSEStatsRecord(**dict(row)) for row in cursor.fetchall()]
```

### Pattern 4: CLI Command Group
**What:** Add new command group following lucy-ng Click patterns
**When to use:** All new CLI functionality
**Example:**
```python
# src/lucy_ng/cli/detect.py
import click
from lucy_ng.detection import StatisticalDetector
from lucy_ng.database import DatabaseFinder

@click.group()
def detect() -> None:
    """Statistical detection of structural constraints from shifts."""
    pass

@detect.command("hybridisation")
@click.argument("shift_ppm", type=float)
@click.option("--db", "-d", type=click.Path(exists=True), default=None)
@click.option("--radius", "-r", type=int, default=3)
@click.option("--window", "-w", type=float, default=2.0)
@click.option("--threshold", "-t", type=float, default=0.01)
@click.option("--format", type=click.Choice(["text", "json"]), default="text")
def hybridisation_command(
    shift_ppm: float,
    db: str | None,
    radius: int,
    window: float,
    threshold: float,
    format: str
) -> None:
    """Detect hybridisation state from 13C chemical shift.

    Example: lucy detect hybridisation 125.5 --radius 3
    """
    db_path = Path(db) if db else DatabaseFinder.find_hose_database()
    if not db_path:
        click.echo("Error: No HOSE database found", err=True)
        raise SystemExit(1)

    detector = StatisticalDetector(db_path)
    result = detector.detect_hybridisation(
        shift_ppm,
        radius=radius,
        window_ppm=window,
        threshold=threshold
    )

    if format == "json":
        click.echo(result.model_dump_json(indent=2))
    else:
        click.echo(result.summary())

# Register in main.py
from lucy_ng.cli.detect import detect
cli.add_command(detect)
```

### Anti-Patterns to Avoid
- **Computing stats on-the-fly**: Precompute during database generation, not at query time
- **Single-radius detection**: Query at radius 3 primarily, but support fallback to radius 2-4
- **Global hybridisation ranges**: Don't use "sp2 = 110-160 ppm" rules—use actual database distributions
- **Storing raw observations**: Store counts/distributions, not individual shift values (memory explosion)

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hybridisation ranges | Hardcoded ppm ranges | Database frequency distributions | Accounts for functional group effects, heteroatoms |
| Neighbor detection | SMARTS pattern matching | HOSE sphere 1 parsing | Already encoded in HOSE, no RDKit traversal needed |
| Query window | Linear scan with filter | SQL BETWEEN on indexed mean | 1000x faster with index on mean column |
| Frequency thresholds | Return all states | Filter < 1% like Sherlock | Reduces noise from rare/erroneous data |

**Key insight:** The HOSE code prefix already encodes hybridisation (C-4=sp3, C-3=sp2, C-2=sp1). RDKit atom.GetHybridization() extracts this during stats generation. Don't parse HOSE strings at query time—precompute counts during generation.

## Common Pitfalls

### Pitfall 1: Breaking Existing Database
**What goes wrong:** Naive ALTER TABLE fails on existing lucy-ng-derep.db (2.8 GB, 7.9M rows)
**Why it happens:** SQLite ALTER TABLE is restrictive, lacks ALTER COLUMN, requires table rebuild for complex changes
**How to avoid:**
- Provide migration script that detects schema version
- Support both v3 (no detection columns) and v4 (with detection)
- Default new columns to 0, mark as "needs regeneration"
- CLI warns if detection columns all zero
**Warning signs:**
- User runs `lucy detect hybridisation` on v3 database
- All sp3_count/sp2_count/sp1_count are 0
- Detection returns "insufficient data"

### Pitfall 2: HOSE Hydrogen Consistency Violation
**What goes wrong:** Adding explicit hydrogens to mol before GetHybridization() breaks HOSE matching
**Why it happens:** CRITICAL architecture decision in lucy-ng: ALL HOSE operations use implicit H
**How to avoid:**
- NEVER call Chem.AddHs() during stats generation
- Use mol from `HOSECodeGenerator.prepare_mol(smiles)` directly
- atom.GetHybridization() works correctly on implicit H molecules
- Verify hybridisation extraction in tests with explicit examples
**Warning signs:**
- Prediction success rate drops from 90% to 0%
- HOSE codes stop matching between generation and query
- atom.GetNumAtoms() shows 9 atoms for ethanol (should be 3)

### Pitfall 3: Quaternary vs. Hybridisation Confusion
**What goes wrong:** Treating quaternary carbons as separate detection category
**Why it happens:** DEPT experiments distinguish C/CH/CH2/CH3, creating false parallel
**How to avoid:**
- Hybridisation (sp3/sp2/sp1) is orthogonal to substitution (C/CH/CH2/CH3)
- sp3 quaternary C exists (tert-butyl center): sp3 + C
- sp2 quaternary C exists (carbonyl): sp2 + C
- Don't create "quaternary_count" column—use hydrogen_count from shifts table
**Warning signs:**
- Documentation says "quaternary or sp2"
- Database has quaternary_count column alongside sp2_count
- Agent confused about carbonyl carbons (sp2 + quaternary)

### Pitfall 4: Insufficient Query Window
**What goes wrong:** Using ± 0.5 ppm window returns no results for many shifts
**Why it happens:** HOSE prediction MAE is ~2-3 ppm, shifts vary with functional groups
**How to avoid:**
- Default to ± 2 ppm window (Sherlock standard)
- Make window configurable via CLI option
- Document that smaller windows increase precision but reduce recall
- Consider radius-dependent windows (smaller radius = larger window)
**Warning signs:**
- Detection returns "no data" for common shifts like 130 ppm (aromatic)
- User complains "database has 7.9M entries but finds nothing"
- Works at ± 5 ppm but fails at ± 1 ppm

### Pitfall 5: Rare State Inclusion
**What goes wrong:** Reporting sp1 at 0.1% frequency creates false constraints
**Why it happens:** Database errors, edge cases, measurement noise
**How to avoid:**
- Filter states below 1% frequency (Sherlock threshold)
- Make threshold configurable but default to 1%
- Round frequencies to 1 decimal place in output
- Document that excluded states are logged at debug level
**Warning signs:**
- Detection reports sp1=0.2%, sp2=0.3%, sp3=99.5% for methyl at 20 ppm
- Structure generator rejects all sp3 solutions due to false sp1 constraint
- Agent spends iterations exploring impossible sp1 carbons

### Pitfall 6: Missing Database Index on mean
**What goes wrong:** Shift window queries scan entire 7.9M row table (30+ seconds per query)
**Why it happens:** SQL BETWEEN on unindexed column requires full table scan
**How to avoid:**
- Create index on (mean, radius) during migration
- Verify index exists in schema.py
- Test query performance: should be < 100ms for ± 2 ppm window
**Warning signs:**
- `lucy detect hybridisation 130.5` takes > 5 seconds
- EXPLAIN QUERY PLAN shows "SCAN TABLE hose_stats"
- CPU pegged at 100% during query

## Code Examples

Verified patterns from official sources:

### Extract Hybridisation from RDKit Atom
```python
# Source: RDKit documentation + lucy-ng HOSE patterns
from rdkit import Chem
from rdkit.Chem import HybridizationType

def get_hybridisation_label(atom: Chem.Atom) -> str:
    """Get hybridisation as sp3/sp2/sp1 string.

    Works on molecules with implicit hydrogens (lucy-ng standard).

    Returns:
        "sp3", "sp2", or "sp1"
    """
    hyb = atom.GetHybridization()

    # Map RDKit enum to string labels
    mapping = {
        HybridizationType.SP3: "sp3",
        HybridizationType.SP2: "sp2",
        HybridizationType.SP: "sp1",
        HybridizationType.S: "sp3",  # Treat as saturated
        HybridizationType.UNSPECIFIED: "sp3",  # Default fallback
    }

    return mapping.get(hyb, "sp3")

# Example usage in stats generation
mol = Chem.MolFromSmiles("CC(=O)O")  # Acetic acid, implicit H
for atom in mol.GetAtoms():
    if atom.GetSymbol() == "C":
        hyb = get_hybridisation_label(atom)
        print(f"Atom {atom.GetIdx()}: {hyb}")
# Output:
# Atom 0: sp3  (methyl)
# Atom 1: sp2  (carbonyl)
```

### Compute Hybridisation Frequencies
```python
# Source: Sherlock detection logic (1% threshold pattern)
from collections import Counter

def compute_hybridisation_distribution(
    sp3_count: int,
    sp2_count: int,
    sp1_count: int,
    threshold: float = 0.01
) -> dict[str, float]:
    """Compute frequency distribution excluding rare states.

    Args:
        sp3_count: Number of sp3 observations
        sp2_count: Number of sp2 observations
        sp1_count: Number of sp1 observations
        threshold: Minimum frequency to include (default 1%)

    Returns:
        Dict mapping "sp3"/"sp2"/"sp1" to frequency (0.0-1.0)
    """
    total = sp3_count + sp2_count + sp1_count
    if total == 0:
        return {}

    distribution = {
        "sp3": sp3_count / total,
        "sp2": sp2_count / total,
        "sp1": sp1_count / total,
    }

    # Filter below threshold
    return {
        state: freq
        for state, freq in distribution.items()
        if freq >= threshold
    }

# Example
dist = compute_hybridisation_distribution(
    sp3_count=850, sp2_count=145, sp1_count=5
)
# Returns: {"sp3": 0.85, "sp2": 0.145}
# sp1 excluded (0.005 < 0.01 threshold)
```

### Accumulator for Online Statistics
```python
# Source: lucy-ng stats_generator.py WelfordAccumulator pattern
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class HybridisationAccumulator:
    """Accumulate hybridisation counts during stats generation.

    Extends WelfordAccumulator pattern with detection counters.
    """
    # Existing shift statistics (Welford)
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0

    # NEW: Hybridisation counts
    sp3_count: int = 0
    sp2_count: int = 0
    sp1_count: int = 0

    def update(self, shift_ppm: float, hybridisation: str) -> None:
        """Add observation with hybridisation label."""
        # Update Welford statistics
        self.count += 1
        delta = shift_ppm - self.mean
        self.mean += delta / self.count
        delta2 = shift_ppm - self.mean
        self.m2 += delta * delta2

        # Update hybridisation counts
        if hybridisation == "sp3":
            self.sp3_count += 1
        elif hybridisation == "sp2":
            self.sp2_count += 1
        elif hybridisation == "sp1":
            self.sp1_count += 1

    def to_tuple(self) -> tuple:
        """Export for database insertion."""
        return (
            self.count, self.mean, self.m2,
            self.sp3_count, self.sp2_count, self.sp1_count
        )

# Usage in stats generator
accumulators: dict[tuple[str, int], HybridisationAccumulator] = defaultdict(
    HybridisationAccumulator
)

for atom_idx, shift_ppm in shifts:
    atom = mol.GetAtomWithIdx(atom_idx)
    hybridisation = get_hybridisation_label(atom)

    for radius in range(1, 7):
        hose_code = hose_gen.generate_for_atom(mol, atom_idx, radius)
        accumulators[(hose_code, radius)].update(shift_ppm, hybridisation)
```

### Migration Detection and Execution
```python
# Source: lucy-ng schema.py patterns + SQLite best practices
import sqlite3

def needs_migration(conn: sqlite3.Connection, target_version: int) -> bool:
    """Check if database needs migration to target version."""
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT value FROM schema_meta WHERE key = ?", ("schema_version",))
        row = cursor.fetchone()
        if row:
            current_version = int(row[0])
            return current_version < target_version
    except sqlite3.OperationalError:
        # No schema_meta table = very old database
        return True

    return True

def migrate_if_needed(db_path: str) -> None:
    """Migrate database to latest schema version."""
    conn = sqlite3.connect(db_path)

    if not needs_migration(conn, SCHEMA_VERSION):
        return

    # Get current version
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM schema_meta WHERE key = ?", ("schema_version",))
    row = cursor.fetchone()
    current_version = int(row[0]) if row else 0

    # Apply migrations in order
    if current_version < 4:
        migrate_v3_to_v4(conn)

    conn.close()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded shift ranges | Database frequency distributions | Sherlock (2023) | Context-aware detection, handles functional groups |
| Global hybridisation rules | HOSE-specific statistics | nmrshiftdb2 (2024) | Accounts for chemical environment |
| Exact HOSE matching | Shift window queries | Sherlock (2023) | Enables detection vs prediction paradigm |
| Return all states | 1% frequency threshold | Sherlock (default) | Filters database noise |
| Text file HOSE tables | SQLite with indexes | lucy-ng v2.0 (2025) | Fast queries on 7.9M entries |

**Deprecated/outdated:**
- JSON HOSE lookup tables: Replaced by SQLite database in lucy-ng v2.0, better query performance
- Separate neighbor detection: HOSE sphere 1 already encodes first neighbors, don't recompute
- Manual DEPT interpretation: Statistical detection complements (not replaces) DEPT multiplicity

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal query radius for detection**
   - What we know: Prediction uses radius 6 with fallback to radius 1
   - What's unclear: Is radius 3 optimal for detection, or should multiple radii be aggregated?
   - Recommendation: Default to radius 3 (balances specificity and database coverage), make configurable

2. **Neighbor detection priority**
   - What we know: Sherlock detects mandatory/forbidden neighbors, uses 1%/95% thresholds
   - What's unclear: Should Phase 34 implement neighbor detection or defer to Phase 35?
   - Recommendation: Implement schema columns now (cheap), defer detection logic to Phase 35

3. **Migration strategy for deployed databases**
   - What we know: Users have downloaded lucy-ng-derep.db (2.8 GB) from Figshare
   - What's unclear: Should migration add columns with 0 counts, or require full regeneration?
   - Recommendation: Add columns with 0s, document regeneration command, warn on query if all zeros

4. **Confidence scoring for detections**
   - What we know: Sherlock uses occurrence frequency, lucy-ng predictor uses match_count
   - What's unclear: How to score confidence when multiple HOSE codes contribute to distribution?
   - Recommendation: Start with simple total_observations count, refine in v3.1 based on user feedback

## Sources

### Primary (HIGH confidence)
- [Sherlock CASE System Paper - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9920390/) - Statistical detection methodology, 1% threshold
- [nmrshiftdb2 Twenty Years - Wiley](https://analyticalsciencejournals.onlinelibrary.wiley.com/doi/10.1002/mrc.5418) - HOSE code usage in modern NMR databases (2024)
- lucy-ng source code: src/lucy_ng/database/schema.py, src/lucy_ng/prediction/stats_generator.py, src/lucy_ng/cli/predict.py
- RDKit documentation: GetHybridization() API

### Secondary (MEDIUM confidence)
- [13C NMR Chemical Shift Ranges - ScienceInsights](https://scienceinsights.org/13c-nmr-chemical-shift-table-and-reference-data/) - sp3/sp2/sp1 typical ranges
- [NMR Metabolomics Tolerance Parameters - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4165451/) - ± 0.6 ppm tolerance for 13C
- [DELTA50 NMR Database - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10051451/) - Database accuracy benchmarks

### Tertiary (LOW confidence - verified with code)
- [13C NMR Shift Prediction sp2 Carbons - ACS](https://pubs.acs.org/doi/10.1021/ci950131x) - Neural network methods (older approach)
- [HOSE Code Stereo Extension - ACS Omega](https://pubs.acs.org/doi/10.1021/acsomega.9b00488) - HOSE code principles

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already in lucy-ng dependencies, zero new installs
- Architecture: HIGH - Patterns directly mirror existing prediction module and CLI structure
- Pitfalls: HIGH - HOSE hydrogen consistency is documented critical decision, migration patterns from schema.py

**Research date:** 2026-02-10
**Valid until:** 2026-03-10 (30 days - stable domain, SQLite/RDKit APIs stable)

**Notes:**
- No user decisions in CONTEXT.md - all implementation choices at planner's discretion
- Sherlock source code not directly accessible, but paper provides sufficient methodology
- ± 2 ppm window is inference from metabolomics literature + prediction MAE, not explicit Sherlock documentation
- 1% threshold explicitly stated in Sherlock paper
- All code examples verified against lucy-ng existing patterns (stats_generator.py, predict.py)
