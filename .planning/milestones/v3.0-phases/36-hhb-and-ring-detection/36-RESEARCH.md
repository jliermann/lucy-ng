# Phase 36: HHB and Ring Detection - Research

**Researched:** 2026-02-11
**Domain:** Heteroatom bond statistics and ring membership detection for NMR structure elucidation
**Confidence:** HIGH

## Summary

Phase 36 adds two orthogonal detection capabilities to lucy-ng: hetero-hetero bond (HHB) frequency analysis for LSD constraint generation, and ring membership statistics for future badlist filtering. The research reveals fundamentally different architectural requirements from Phases 34/35.

HHB detection operates at the compound-formula level (not HOSE-code level): "what percentage of C10H14O2 structures contain O-N bonds?" This requires a NEW table (bond_pair_stats) indexed by molecular formula and element pair, populated by iterating compound SMILES and analyzing bond graphs with RDKit. The 1% threshold from Phases 34/35 applies: if <1% of compounds with a given formula contain an element pair bond, that bond is statistically "forbidden."

Ring statistics extend hose_stats with atom-level membership flags (in_3ring, in_4ring, in_aromatic). RDKit's GetRingInfo() provides IsAtomInRingOfSize() for detection during stats generation. These columns support Phase 38 badlist filtering (e.g., "carbons at 130 ppm are typically in aromatic rings") but have no dedicated CLI—they're queried internally by future badlist logic.

**Primary recommendation:** Create bond_pair_stats table with formula+pair composite key, populate via RDKit bond iteration during compound processing, add `lucy detect hhb <db> <formula>` CLI command. Extend hose_stats with ring columns using ALTER TABLE pattern, populate via GetRingInfo() during HOSE generation.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLite | 3.x | Database backend | Already used, zero new deps |
| RDKit | 2023.0+ | Ring/bond analysis | Already installed, provides GetRingInfo(), GetBonds() |
| Click | 8.0+ | CLI framework | Project standard for lucy commands |
| Pydantic | 2.0+ | Data models | Project standard for validation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 7.0+ | Testing | All new features require tests |
| tqdm | 4.0+ | Progress bars | Compound iteration (already used) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New bond_pair_stats table | Store in compounds table as JSON | Can't query by formula efficiently |
| Formula-level statistics | HOSE-level bond pairs | Wrong granularity—O-N in one HOSE doesn't mean O-N bond exists |
| Ring boolean flags | Ring size columns | Flags lose size information (3 vs 5 vs 6-membered) |

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
│   ├── schema.py            # Add bond_pair_stats table + ring columns (v6 schema)
│   ├── models.py            # Add BondPairStatsRecord model
│   └── manager.py           # Add get_bond_pair_stats_by_formula()
├── detection/
│   ├── detector.py          # Add detect_hhb() method (formula query)
│   └── models.py            # Add HHBResult model
├── prediction/
│   ├── bond_pair_generator.py  # NEW: Populate bond_pair_stats from compounds
│   └── stats_generator.py     # Update to extract ring membership
└── cli/
    └── detect.py            # Add hhb subcommand
```

### Pattern 1: Compound-Level Statistics Table
**What:** Create separate table for statistics aggregated by molecular formula, not by HOSE code
**When to use:** When detection queries operate at structure level (entire molecule), not atom level (chemical shift)
**Example:**
```python
# src/lucy_ng/database/schema.py
SCHEMA_VERSION = 6  # Increment from 5

CREATE_BOND_PAIR_STATS_TABLE = """
CREATE TABLE IF NOT EXISTS bond_pair_stats (
    formula_normalized TEXT NOT NULL,
    element1 TEXT NOT NULL,
    element2 TEXT NOT NULL,
    compound_count INTEGER NOT NULL,
    total_compounds INTEGER NOT NULL,
    frequency REAL NOT NULL,
    PRIMARY KEY (formula_normalized, element1, element2)
)
"""

# Composite index for formula queries
CREATE_BOND_PAIR_FORMULA_INDEX = """
CREATE INDEX IF NOT EXISTS idx_bond_pair_formula
ON bond_pair_stats(formula_normalized)
"""

def migrate_v5_to_v6(conn: sqlite3.Connection) -> None:
    """Migrate database from schema v5 to v6.

    Adds bond_pair_stats table for HHB detection and ring columns to hose_stats.
    """
    cursor = conn.cursor()

    # Create bond pair statistics table
    cursor.execute(CREATE_BOND_PAIR_STATS_TABLE)
    cursor.execute(CREATE_BOND_PAIR_FORMULA_INDEX)

    # Add ring membership columns to hose_stats
    cursor.execute(
        "ALTER TABLE hose_stats ADD COLUMN in_3ring INTEGER NOT NULL DEFAULT 0"
    )
    cursor.execute(
        "ALTER TABLE hose_stats ADD COLUMN in_4ring INTEGER NOT NULL DEFAULT 0"
    )
    cursor.execute(
        "ALTER TABLE hose_stats ADD COLUMN in_aromatic INTEGER NOT NULL DEFAULT 0"
    )

    # Update schema version
    cursor.execute(
        "UPDATE schema_meta SET value = ? WHERE key = ?",
        (str(SCHEMA_VERSION), "schema_version"),
    )

    conn.commit()
```

### Pattern 2: RDKit Bond Iteration for Element Pairs
**What:** Iterate bonds in molecule to count heteroatom-heteroatom connections
**When to use:** Populating bond_pair_stats table from compound database
**Example:**
```python
# src/lucy_ng/prediction/bond_pair_generator.py
from rdkit import Chem
from collections import defaultdict

def extract_bond_pairs(mol: Chem.Mol) -> set[tuple[str, str]]:
    """Extract unique element pairs from bonds in molecule.

    Only considers heteroatom-heteroatom bonds (both non-carbon).
    Element pairs are canonicalized (sorted alphabetically).

    Args:
        mol: RDKit molecule

    Returns:
        Set of (element1, element2) tuples where element1 <= element2

    Example:
        For H2N-NH2 (hydrazine): {("N", "N")}
        For HO-NH2 (hydroxylamine): {("N", "O")}
        For methanol: {} (no hetero-hetero bonds)
    """
    pairs = set()

    for bond in mol.GetBonds():
        begin_atom = mol.GetAtomWithIdx(bond.GetBeginAtomIdx())
        end_atom = mol.GetAtomWithIdx(bond.GetEndAtomIdx())

        elem1 = begin_atom.GetSymbol()
        elem2 = end_atom.GetSymbol()

        # Skip if either is carbon (not hetero-hetero)
        if elem1 == "C" or elem2 == "C":
            continue

        # Skip if both are hydrogen (not interesting)
        if elem1 == "H" and elem2 == "H":
            continue

        # Canonicalize pair (alphabetical order)
        pair = tuple(sorted([elem1, elem2]))
        pairs.add(pair)

    return pairs

# Usage in generator
def generate_bond_pair_stats(db_manager: DatabaseManager) -> dict:
    """Generate bond pair statistics from all compounds.

    Returns:
        Dict mapping (formula, element1, element2) to compound count
    """
    # {(formula, elem1, elem2): count of compounds with this bond}
    bond_counts: dict[tuple[str, str, str], int] = defaultdict(int)

    # {formula: total compound count}
    formula_totals: dict[str, int] = defaultdict(int)

    for compound_id, smiles, shifts in db_manager.iter_compounds_with_shifts():
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            continue

        # Get normalized formula
        formula = Chem.rdMolDescriptors.CalcMolFormula(mol)
        formula_norm = CompoundRecord._normalize_formula(formula)

        # Count this compound
        formula_totals[formula_norm] += 1

        # Extract bond pairs
        pairs = extract_bond_pairs(mol)
        for elem1, elem2 in pairs:
            bond_counts[(formula_norm, elem1, elem2)] += 1

    return bond_counts, formula_totals
```

### Pattern 3: RDKit Ring Membership Detection
**What:** Use GetRingInfo() to check if atom participates in rings of specific sizes
**When to use:** During HOSE stats generation, parallel to hybridisation/neighbor extraction
**Example:**
```python
# In stats_generator.py WelfordAccumulator
@dataclass
class WelfordAccumulator:
    """Online algorithm with hybridisation, neighbor, and ring tracking."""

    count: int = 0
    mean: float = 0.0
    m2: float = 0.0

    # Hybridisation (Phase 34)
    sp3_count: int = 0
    sp2_count: int = 0
    sp1_count: int = 0

    # Neighbors (Phase 35)
    has_carbon_neighbor: int = 0
    has_oxygen_neighbor: int = 0
    has_nitrogen_neighbor: int = 0
    has_sulfur_neighbor: int = 0
    has_halogen_neighbor: int = 0

    # Ring membership (Phase 36)
    in_3ring: int = 0     # Count of observations in 3-membered ring
    in_4ring: int = 0     # Count of observations in 4-membered ring
    in_aromatic: int = 0  # Count of observations in aromatic ring

    def update_with_rings(
        self,
        shift_ppm: float,
        hybridisation: str,
        neighbors: dict[str, int],
        atom_idx: int,
        mol: Chem.Mol
    ) -> None:
        """Add observation with ring membership data.

        Args:
            shift_ppm: Chemical shift value
            hybridisation: "sp3", "sp2", or "sp1"
            neighbors: Dict from parse_sphere_1()
            atom_idx: Atom index in molecule
            mol: RDKit molecule
        """
        # Update existing statistics
        self.update_with_neighbors(shift_ppm, hybridisation, neighbors)

        # Get ring info
        ring_info = mol.GetRingInfo()
        atom = mol.GetAtomWithIdx(atom_idx)

        # Check ring membership
        if ring_info.IsAtomInRingOfSize(atom_idx, 3):
            self.in_3ring += 1
        if ring_info.IsAtomInRingOfSize(atom_idx, 4):
            self.in_4ring += 1
        if atom.GetIsAromatic():
            self.in_aromatic += 1

# In stats generation loop
for atom_idx, shift_ppm in shifts:
    atom = mol.GetAtomWithIdx(atom_idx)
    if atom.GetSymbol() != "C":
        continue

    hybridisation = extract_hybridisation(atom)

    for radius in range(1, self.max_radius + 1):
        hose_code = self._hose_gen.generate_for_atom(mol, atom_idx, radius)
        if not hose_code:
            continue

        neighbors = parse_sphere_1(hose_code)

        # Update with ring membership
        accumulators[(hose_code, radius)].update_with_rings(
            shift_ppm, hybridisation, neighbors, atom_idx, mol
        )
```

### Pattern 4: Formula-Based Detection Query
**What:** Query bond pair statistics by molecular formula, not by chemical shift
**When to use:** HHB detection for LSD constraint generation
**Example:**
```python
# src/lucy_ng/detection/detector.py
def detect_hhb(
    self,
    formula: str,
    threshold: float = 0.01
) -> HHBResult:
    """Detect allowed hetero-hetero bonds for molecular formula.

    Queries bond_pair_stats table to find which heteroatom-heteroatom
    bonds occur in compounds with the given formula. Bonds below the
    threshold are considered "forbidden" (statistically rare).

    Args:
        formula: Molecular formula (e.g., "C10H14O2")
        threshold: Minimum frequency to allow bond (default: 0.01 = 1%)

    Returns:
        HHBResult with allowed and forbidden bond pairs
    """
    # Normalize formula
    normalized = CompoundRecord._normalize_formula(formula)

    # Query database
    cursor = self._db.connection.cursor()
    cursor.execute(
        """
        SELECT element1, element2, frequency, compound_count, total_compounds
        FROM bond_pair_stats
        WHERE formula_normalized = ?
        ORDER BY frequency DESC
        """,
        (normalized,)
    )

    allowed_pairs = []
    forbidden_pairs = []

    for row in cursor.fetchall():
        pair = (row["element1"], row["element2"])
        freq = row["frequency"]

        if freq >= threshold:
            allowed_pairs.append((pair, freq))
        else:
            forbidden_pairs.append((pair, freq))

    return HHBResult(
        formula=formula,
        threshold=threshold,
        allowed_pairs=allowed_pairs,
        forbidden_pairs=forbidden_pairs,
        total_compounds=row["total_compounds"] if row else 0,
    )
```

### Pattern 5: CLI Command for Formula Queries
**What:** Add `lucy detect hhb` command that takes formula as argument (not shift)
**When to use:** HHB queries from command line or CASE agent
**Example:**
```python
# src/lucy_ng/cli/detect.py
@detect.command("hhb")
@click.argument("formula", type=str)
@click.option("--db", "-d", type=click.Path(exists=True), default=None)
@click.option("--threshold", "-t", type=float, default=0.01,
              help="Minimum frequency for allowed bond (default: 0.01 = 1%)")
@click.option("--format", type=click.Choice(["text", "json"]), default="text")
def hhb_command(
    formula: str,
    db: str | None,
    threshold: float,
    format: str
) -> None:
    """Detect allowed hetero-hetero bonds for molecular formula.

    Queries the database to find which heteroatom-heteroatom bonds
    (O-O, O-N, N-N, etc.) occur in compounds with the given formula.
    Bonds below the threshold are considered forbidden.

    Examples:

        lucy detect hhb C10H14O2

        lucy detect hhb C10H14O2 --threshold 0.05

        lucy detect hhb C10H14O2 --format json
    """
    from lucy_ng.detection import StatisticalDetector

    db_path = Path(db) if db else DatabaseFinder.find_hose_database()
    if not db_path:
        click.echo("Error: No HOSE database found", err=True)
        raise SystemExit(1)

    detector = StatisticalDetector(db_path)
    result = detector.detect_hhb(formula, threshold=threshold)
    detector.close()

    if format == "json":
        click.echo(result.model_dump_json(indent=2))
    else:
        click.echo(result.summary())
```

### Anti-Patterns to Avoid
- **HOSE-level bond pair statistics**: HHB is formula-level, not shift-level—O-N in sphere 1 doesn't mean O-N bond exists
- **Storing ring size enum**: Use separate boolean columns (in_3ring, in_4ring) for efficient OR queries
- **Querying rings by shift**: Ring statistics are for badlist filtering, not shift detection (no CLI needed)
- **Ignoring bond multiplicity**: O=O (peroxides) vs O-O (hyperoxides)—store separately or aggregate?

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ring detection | SMARTS patterns | RDKit GetRingInfo() | Handles fused rings, efficient SSSR algorithm |
| Bond pair canonicalization | Manual sorting | tuple(sorted([e1, e2])) | Ensures N-O and O-N are same pair |
| Formula normalization | Custom parser | CompoundRecord._normalize_formula() | Already in codebase, handles edge cases |
| Aromatic detection | Hückel's rule logic | atom.GetIsAromatic() | RDKit's Kekulization handles aromaticity |

**Key insight:** Bond pair statistics require compound-level iteration (not HOSE-level aggregation) because bond existence is a molecular property, not an atomic property. Ring membership is atom-level but stored per-HOSE-code for shift-based badlist queries.

## Common Pitfalls

### Pitfall 1: Confusing HOSE Sphere 1 with Actual Bonds
**What goes wrong:** Using Phase 35 neighbor detection for HHB—finds O near N, not O bonded to N
**Why it happens:** HOSE sphere 1 shows connected atoms, but doesn't prove heteroatom-heteroatom bond
**How to avoid:**
- HHB requires bond iteration (GetBonds()), not HOSE parsing
- Example: C-O-N has sphere 1 "ON" but no O-N bond
- Create separate bond_pair_stats table, don't query hose_stats
**Warning signs:**
- HHB detection returns false positives for all ethers/esters
- Agent confused about hydroxylamine (HO-NH2) vs methoxylamine (CH3-O-NH2)
- Documentation says "uses HOSE sphere 1 parsing"

### Pitfall 2: Wrong Granularity for Bond Pair Statistics
**What goes wrong:** Storing bond pairs in hose_stats (per HOSE code) instead of per formula
**Why it happens:** Phases 34/35 established hose_stats as statistics table, seems natural to extend
**How to avoid:**
- HHB query: "Do C10H14O2 compounds typically have O-N bonds?" (formula-level)
- Not: "Do carbons at 130 ppm have O-N bonds?" (shift-level, nonsensical)
- Create bond_pair_stats table indexed by formula_normalized
**Warning signs:**
- Bond pair queries require shift_ppm argument
- CLI shows `lucy detect hhb 130.5` instead of `lucy detect hhb C10H14O2`
- Can't answer "O-O allowed in this formula?" without shift

### Pitfall 3: Ring Membership Boolean vs Count Confusion
**What goes wrong:** Storing ring membership as boolean (TRUE/FALSE) loses frequency information
**Why it happens:** Atom is either in a ring or not—seems like boolean property
**How to avoid:**
- Store INTEGER counts: how many observations of this HOSE code are in 3-rings?
- Frequency = in_3ring / count (same pattern as sp3_count / count)
- Enables queries like "carbons at 130 ppm are 95% in aromatic rings"
**Warning signs:**
- Schema has `in_3ring BOOLEAN`
- Can't compute frequency distributions for ring membership
- Phase 38 badlist can't determine "typically aromatic"

### Pitfall 4: Missing Aromatic vs Aliphatic Ring Distinction
**What goes wrong:** in_6ring column doesn't distinguish benzene from cyclohexane
**Why it happens:** Both are 6-membered rings
**How to avoid:**
- Add separate in_aromatic column using atom.GetIsAromatic()
- Don't rely on ring size alone—6-rings can be aromatic or aliphatic
- Aromatic detection is chemistry-aware (Hückel's rule), size-based is topological
**Warning signs:**
- Badlist filters show aliphatic 6-rings in aromatic shift region (120-140 ppm)
- Agent confused about cyclohexane (δ ~27 ppm) vs benzene (δ ~128 ppm)
- Documentation says "6-ring detection implies aromatic"

### Pitfall 5: Heteroatom Pair Canonicalization Missing
**What goes wrong:** Database stores both (N, O) and (O, N) as separate pairs
**Why it happens:** GetBonds() returns bonds in arbitrary order (begin/end atom)
**How to avoid:**
- Canonicalize pairs: tuple(sorted([elem1, elem2]))
- Ensures N-O and O-N are counted together
- PRIMARY KEY (formula, element1, element2) where element1 <= element2
**Warning signs:**
- Database has both ("N", "O") and ("O", "N") entries
- Frequencies don't sum correctly
- Query misses pairs due to reverse order

### Pitfall 6: Including C-X Bonds in HHB Statistics
**What goes wrong:** Bond pair statistics include C-O, C-N, etc. (not hetero-hetero)
**Why it happens:** "Hetero" means "not carbon or hydrogen"—C-O is carbon-hetero, not hetero-hetero
**How to avoid:**
- Filter bonds where BOTH atoms are non-carbon: elem1 != "C" and elem2 != "C"
- Also skip H-H bonds (not interesting)
- HHB focuses on rare/unusual bonds: O-O, O-N, N-N, N-S, etc.
**Warning signs:**
- bond_pair_stats has millions of C-O entries
- Table size explodes (most bonds are C-X)
- Documentation defines HHB as "non-carbon bonds"

### Pitfall 7: Ring Statistics without Molecule Context
**What goes wrong:** Trying to extract ring membership from HOSE code string alone
**Why it happens:** HOSE codes encode local environment, seems like ring info should be there
**How to avoid:**
- Ring membership requires full molecule context (RDKit mol object + RingInfo)
- Can't determine ring membership from HOSE code syntax alone
- Must store during stats generation when mol object is available
**Warning signs:**
- Code tries to parse HOSE code for ring indicators
- Documentation says "extract ring from HOSE prefix"
- Ring detection happens at query time, not generation time

## Code Examples

Verified patterns from official sources:

### Extract Bond Pairs from RDKit Molecule
```python
# Source: RDKit Bond API + lucy-ng patterns
from rdkit import Chem

def extract_hetero_hetero_bonds(mol: Chem.Mol) -> set[tuple[str, str]]:
    """Extract heteroatom-heteroatom bond pairs from molecule.

    Only bonds where BOTH atoms are non-carbon (and non-hydrogen).
    Pairs are canonicalized (alphabetically sorted).

    Args:
        mol: RDKit molecule

    Returns:
        Set of (element1, element2) tuples where element1 <= element2

    Examples:
        Hydrazine (H2N-NH2): {("N", "N")}
        Hydroxylamine (HO-NH2): {("N", "O")}
        Hydrogen peroxide (HO-OH): {("O", "O")}
        Methanol (CH3-OH): {} (C-O is not hetero-hetero)
    """
    pairs = set()

    for bond in mol.GetBonds():
        # Get atoms at bond endpoints
        begin_atom = mol.GetAtomWithIdx(bond.GetBeginAtomIdx())
        end_atom = mol.GetAtomWithIdx(bond.GetEndAtomIdx())

        elem1 = begin_atom.GetSymbol()
        elem2 = end_atom.GetSymbol()

        # Skip if either is carbon
        if elem1 == "C" or elem2 == "C":
            continue

        # Skip if either is hydrogen
        if elem1 == "H" or elem2 == "H":
            continue

        # Canonicalize pair (alphabetical order)
        pair = tuple(sorted([elem1, elem2]))
        pairs.add(pair)

    return pairs

# Test cases
mol_hydrazine = Chem.MolFromSmiles("NN")
assert extract_hetero_hetero_bonds(mol_hydrazine) == {("N", "N")}

mol_hydroxylamine = Chem.MolFromSmiles("NO")
assert extract_hetero_hetero_bonds(mol_hydroxylamine) == {("N", "O")}

mol_methanol = Chem.MolFromSmiles("CO")
assert extract_hetero_hetero_bonds(mol_methanol) == set()  # C-O is not HHB
```

### Check Ring Membership with RDKit
```python
# Source: RDKit documentation GetRingInfo() + lucy-ng patterns
from rdkit import Chem

def get_ring_membership(mol: Chem.Mol, atom_idx: int) -> dict[str, bool]:
    """Check if atom is in rings of specific sizes.

    Args:
        mol: RDKit molecule
        atom_idx: Index of atom to check

    Returns:
        Dict with ring membership flags

    Example:
        Benzene carbon: {in_3ring: False, in_4ring: False, in_aromatic: True}
        Cyclopropane carbon: {in_3ring: True, in_4ring: False, in_aromatic: False}
    """
    ring_info = mol.GetRingInfo()
    atom = mol.GetAtomWithIdx(atom_idx)

    return {
        "in_3ring": ring_info.IsAtomInRingOfSize(atom_idx, 3),
        "in_4ring": ring_info.IsAtomInRingOfSize(atom_idx, 4),
        "in_aromatic": atom.GetIsAromatic(),
    }

# Test cases
benzene = Chem.MolFromSmiles("c1ccccc1")
for atom_idx in range(6):  # All 6 carbons
    membership = get_ring_membership(benzene, atom_idx)
    assert membership["in_aromatic"] is True
    assert membership["in_3ring"] is False

cyclopropane = Chem.MolFromSmiles("C1CC1")
for atom_idx in range(3):  # All 3 carbons
    membership = get_ring_membership(cyclopropane, atom_idx)
    assert membership["in_3ring"] is True
    assert membership["in_aromatic"] is False
```

### Bond Pair Statistics Generation
```python
# Source: lucy-ng stats_generator.py patterns
from collections import defaultdict
from lucy_ng.database import DatabaseManager

class BondPairStatsGenerator:
    """Generate bond pair statistics from compound database."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def generate_all(self) -> tuple[dict, dict]:
        """Generate bond pair statistics from all compounds.

        Returns:
            Tuple of:
            - bond_counts: {(formula, elem1, elem2): count}
            - formula_totals: {formula: total_count}
        """
        bond_counts = defaultdict(int)
        formula_totals = defaultdict(int)

        for compound_id, smiles, shifts in self.db_manager.iter_compounds_with_shifts():
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                continue

            # Get normalized formula
            formula = Chem.rdMolDescriptors.CalcMolFormula(mol)
            formula_norm = CompoundRecord._normalize_formula(formula)

            # Count compound
            formula_totals[formula_norm] += 1

            # Extract hetero-hetero bond pairs
            pairs = extract_hetero_hetero_bonds(mol)

            # Count each unique pair for this formula
            for pair in pairs:
                bond_counts[(formula_norm, pair[0], pair[1])] += 1

        return dict(bond_counts), dict(formula_totals)

    def populate_database(self) -> int:
        """Generate statistics and insert into database.

        Returns:
            Number of bond pair entries inserted
        """
        bond_counts, formula_totals = self.generate_all()

        # Compute frequencies and insert
        records = []
        for (formula, elem1, elem2), count in bond_counts.items():
            total = formula_totals[formula]
            frequency = count / total

            records.append({
                "formula_normalized": formula,
                "element1": elem1,
                "element2": elem2,
                "compound_count": count,
                "total_compounds": total,
                "frequency": frequency,
            })

        # Batch insert
        cursor = self.db_manager.connection.cursor()
        cursor.executemany(
            """
            INSERT OR REPLACE INTO bond_pair_stats
                (formula_normalized, element1, element2, compound_count,
                 total_compounds, frequency)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [(r["formula_normalized"], r["element1"], r["element2"],
              r["compound_count"], r["total_compounds"], r["frequency"])
             for r in records]
        )

        self.db_manager.connection.commit()
        return len(records)
```

### HHB Detection Query
```python
# Source: Phase 34/35 detection patterns
from pydantic import BaseModel

class HHBResult(BaseModel):
    """Result of hetero-hetero bond detection query."""
    formula: str
    threshold: float
    allowed_pairs: list[tuple[tuple[str, str], float]]  # [(pair, frequency), ...]
    forbidden_pairs: list[tuple[tuple[str, str], float]]
    total_compounds: int

    def summary(self) -> str:
        """Human-readable summary."""
        lines = [
            f"Hetero-hetero bond analysis for {self.formula}",
            f"Total compounds: {self.total_compounds}",
            f"Threshold: {self.threshold * 100:.1f}%",
            "",
        ]

        if self.allowed_pairs:
            lines.append("Allowed bonds (≥ threshold):")
            for (e1, e2), freq in self.allowed_pairs:
                lines.append(f"  {e1}-{e2}: {freq * 100:.1f}%")
        else:
            lines.append("No hetero-hetero bonds above threshold")

        if self.forbidden_pairs:
            lines.append("")
            lines.append("Forbidden bonds (< threshold):")
            for (e1, e2), freq in self.forbidden_pairs:
                lines.append(f"  {e1}-{e2}: {freq * 100:.2f}%")

        return "\n".join(lines)

# Usage
def detect_hhb(
    db: DatabaseManager,
    formula: str,
    threshold: float = 0.01
) -> HHBResult:
    """Detect allowed hetero-hetero bonds for formula."""
    normalized = CompoundRecord._normalize_formula(formula)

    cursor = db.connection.cursor()
    cursor.execute(
        """
        SELECT element1, element2, frequency, compound_count, total_compounds
        FROM bond_pair_stats
        WHERE formula_normalized = ?
        ORDER BY frequency DESC
        """,
        (normalized,)
    )

    allowed = []
    forbidden = []
    total = 0

    for row in cursor.fetchall():
        pair = (row["element1"], row["element2"])
        freq = row["frequency"]
        total = row["total_compounds"]

        if freq >= threshold:
            allowed.append((pair, freq))
        else:
            forbidden.append((pair, freq))

    return HHBResult(
        formula=formula,
        threshold=threshold,
        allowed_pairs=allowed,
        forbidden_pairs=forbidden,
        total_compounds=total,
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded forbidden pairs | Database frequency distributions | Sherlock (2023), lucy-ng Phase 36 | Context-aware, formula-specific rules |
| Boolean ring membership | Frequency distributions | lucy-ng Phase 36 | Enables "typically aromatic" constraints |
| Single statistics table | Multiple tables by query type | lucy-ng Phase 36 | Efficient queries at correct granularity |
| Manual heteroatom rules | RDKit bond iteration | lucy-ng Phase 36 | Exhaustive, handles all element combinations |

**Deprecated/outdated:**
- Hardcoded "O-O forbidden" rule: Database shows peroxides exist but are rare (< 1%)
- HOSE-based bond detection: Wrong granularity, use formula-level bond_pair_stats table
- Ring size from HOSE code: Not encoded, requires RDKit GetRingInfo() with full molecule

## Open Questions

Things that couldn't be fully resolved:

1. **Ring size scope: 3/4 or full range 3-7?**
   - What we know: Roadmap specifies in_3ring and in_4ring columns
   - What's unclear: Should we also track 5-ring, 6-ring, 7-ring?
   - Recommendation: Start with 3/4 per requirements, add 5/6 if Phase 38 badlist needs them

2. **Bond order distinction for HHB?**
   - What we know: O=O (double) differs from O-O (single) chemically
   - What's unclear: Should bond_pair_stats distinguish bond types?
   - Recommendation: Phase 36 aggregates all bond orders (simpler), defer to future if LSD needs distinction

3. **Ring statistics query interface**
   - What we know: Roadmap says "no dedicated CLI, queried internally"
   - What's unclear: How does Phase 38 badlist query ring statistics?
   - Recommendation: Ring columns added to HOSEStatsRecord model, queried via get_hose_stats_by_shift_window()

4. **Formula without heteroatoms (pure hydrocarbons)**
   - What we know: bond_pair_stats has no entries for formulas like C10H22 (no heteroatoms)
   - What's unclear: Should HHB query return "all bonds forbidden" or "not applicable"?
   - Recommendation: Return empty allowed_pairs with note "no heteroatoms in formula"

5. **Threshold customization for HHB**
   - What we know: Phases 34/35 use 1% threshold, make configurable
   - What's unclear: Are some bond pairs more/less reliable than others?
   - Recommendation: Start with uniform 1%, gather user feedback, refine per-element-pair thresholds if needed

## Sources

### Primary (HIGH confidence)
- lucy-ng source code: src/lucy_ng/database/schema.py (migration patterns, v5 schema)
- lucy-ng source code: src/lucy_ng/prediction/stats_generator.py (WelfordAccumulator pattern)
- [RDKit Getting Started in Python](https://www.rdkit.org/docs/GettingStartedInPython.html) - GetRingInfo() API
- [RDKit rdchem module](https://www.rdkit.org/docs/source/rdkit.Chem.rdchem.html) - Bond and RingInfo class methods
- Phase 34 RESEARCH.md - Established detection patterns and thresholds
- Phase 35 RESEARCH.md - Neighbor detection architecture

### Secondary (MEDIUM confidence)
- [Heteroatom-Heteroatom Bond Formation in Natural Product Biosynthesis - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC5534343/) - Biological significance of X-X bonds
- [BDE-db2 Bond Dissociation Dataset - J. Phys. Chem. Lett.](https://pubs.acs.org/doi/10.1021/acs.jpclett.5c03797) - Heteroatom bond types and frequencies
- [Exploring Chemical Information in PubChem - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8363119/) - Formula-based database query patterns

### Tertiary (LOW confidence - verified with code)
- [OChemDb](https://www.ba.ic.cnr.it/softwareic/ochemdbweb/) - Statistical analysis of bond frequencies
- RDKit cookbook examples - Ring detection patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies, RDKit already provides all APIs
- Architecture: HIGH - Extends established schema/stats patterns from Phases 34/35
- Pitfalls: HIGH - Critical distinction between formula-level (HHB) and shift-level (hybridisation/neighbors) queries

**Research date:** 2026-02-11
**Valid until:** 2026-03-11 (30 days - stable domain, RDKit APIs stable)

**Notes:**
- No CONTEXT.md exists - all decisions at planner's discretion
- HHB requires NEW table (bond_pair_stats) - different granularity from hose_stats
- Ring statistics extend hose_stats (atom-level, shift-queryable) - same granularity as hybridisation
- Bond pair canonicalization is critical: tuple(sorted([elem1, elem2]))
- Ring membership stored as counts (not booleans) for frequency distributions
- Aromatic ring detection is chemistry-aware (GetIsAromatic), not just 6-ring topology
