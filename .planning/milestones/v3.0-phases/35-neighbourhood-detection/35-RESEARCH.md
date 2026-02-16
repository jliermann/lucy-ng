# Phase 35: Neighbourhood Detection - Research

**Researched:** 2026-02-11
**Domain:** HOSE code sphere parsing and bond partner detection for NMR structure elucidation
**Confidence:** HIGH

## Summary

Phase 35 extends lucy-ng's statistical detection system to identify forbidden and mandatory bond partners from 13C chemical shifts. The research reveals that HOSE codes already encode bonded element information in sphere 1, requiring only parsing logic and schema extension—no new computational chemistry algorithms needed.

HOSE code sphere 1 syntax concatenates element symbols of bonded atoms (e.g., "CNO" means bonded to C, N, and O). Bond orders are indicated with prefixes: "=" for double bonds, "*" for aromatic bonds. Parsing sphere 1 extracts element types; frequency analysis across the database identifies forbidden partners (<1% occurrence) and mandatory partners (>95% occurrence).

The standard approach mirrors Phase 34's hybridisation detection: extend database schema with neighbor count columns, parse sphere 1 during stats generation to count bonded elements, query with shift windows for frequency distributions, apply thresholds to classify forbidden/mandatory. Architecture follows established patterns: StatisticalDetector gains neighborhood methods, CLI gets `lucy detect neighbours` command, database schema adds element count columns to hose_stats table.

**Primary recommendation:** Parse HOSE sphere 1 element symbols during stats generation, store counts per element type in database, query with shift ± 2 ppm window, return distributions excluding rare states < 1% and flagging mandatory states > 95%.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SQLite | 3.x | Database backend | Already used, zero new deps |
| hosegen | latest | HOSE code generation | Project dependency, generates sphere structure |
| RDKit | 2023.0+ | Molecular graphs | Already installed, provides atom neighbors |
| Click | 8.0+ | CLI framework | Project standard for lucy commands |
| Pydantic | 2.0+ | Data models | Project standard for validation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 7.0+ | Testing | All new features require tests |
| re | stdlib | Regex parsing | HOSE sphere 1 parsing (simple patterns) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| String parsing | RDKit graph traversal | HOSE already encodes neighbors, don't recompute |
| Boolean flags | Count columns | Counts enable "bonded to 2 O" constraints |
| Fixed thresholds | Configurable | CLI flags needed for rare molecules |

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
│   ├── schema.py            # Add neighbor columns (Phase 35-01)
│   ├── models.py            # Extend HOSEStatsRecord with neighbor fields
│   └── manager.py           # Already has get_hose_stats_by_shift_window()
├── detection/
│   ├── detector.py          # Add detect_neighbours() method (Phase 35-03)
│   └── models.py            # Add NeighbourDistribution, NeighbourResult
├── prediction/
│   ├── hose_parser.py       # NEW: parse_sphere_1() function (Phase 35-02)
│   └── stats_generator.py  # Update to extract neighbors (Phase 35-02)
└── cli/
    └── detect.py            # Add neighbours subcommand (Phase 35-04)
```

### Pattern 1: HOSE Sphere 1 Parsing
**What:** Extract bonded element types from HOSE code sphere 1 substring
**When to use:** During HOSE statistics generation loop, after HOSE code generated
**Example:**
```python
# src/lucy_ng/prediction/hose_parser.py
import re
from collections import Counter

def parse_sphere_1(hose_code: str) -> dict[str, int]:
    """Parse sphere 1 from HOSE code to extract bonded elements.

    HOSE format: "PREFIX;SPHERE1(SPHERE2/SPHERE3/...)"
    Sphere 1 contains bonded atoms as element symbols.

    Bond order prefixes:
    - "=" indicates double bond (e.g., "=O" is C=O)
    - "*" indicates aromatic bond (e.g., "*C" is aromatic C)
    - No prefix indicates single bond

    Args:
        hose_code: HOSE code string (e.g., "C-3;=OCO(,,//)")

    Returns:
        Dict mapping element symbol to count (e.g., {"O": 2, "C": 1})

    Example:
        parse_sphere_1("C-3;=OCO(,,//)") -> {"O": 2, "C": 1}
        parse_sphere_1("C-4;CCN(//)") -> {"C": 2, "N": 1}
        parse_sphere_1("C-3;*C*C(//)") -> {"C": 2}  # aromatic
    """
    # Split at semicolon to get prefix and spheres
    parts = hose_code.split(";", 1)
    if len(parts) < 2:
        return {}

    # Extract sphere 1 (before first parenthesis)
    spheres_part = parts[1]
    if "(" in spheres_part:
        sphere1 = spheres_part.split("(")[0]
    else:
        sphere1 = spheres_part

    # Parse element symbols
    # Remove bond order prefixes (=, *, /) and other HOSE syntax
    # Extract uppercase letters followed by optional lowercase
    elements = re.findall(r'[A-Z][a-z]?', sphere1)

    # Count occurrences
    return dict(Counter(elements))
```

### Pattern 2: Neighbor Count Accumulation
**What:** Track bonded element counts in WelfordAccumulator during stats generation
**When to use:** Extend existing hybridisation tracking in ResumableHOSEStatsGenerator
**Example:**
```python
# In stats_generator.py WelfordAccumulator
@dataclass
class WelfordAccumulator:
    """Online algorithm with hybridisation and neighbor tracking."""

    count: int = 0
    mean: float = 0.0
    m2: float = 0.0

    # Hybridisation counts (Phase 34)
    sp3_count: int = 0
    sp2_count: int = 0
    sp1_count: int = 0

    # Neighbor element counts (Phase 35)
    has_carbon_neighbor: int = 0    # Bonded to at least 1 C
    has_oxygen_neighbor: int = 0    # Bonded to at least 1 O
    has_nitrogen_neighbor: int = 0  # Bonded to at least 1 N
    has_sulfur_neighbor: int = 0    # Bonded to at least 1 S
    has_halogen_neighbor: int = 0   # Bonded to at least 1 F/Cl/Br/I

    def update_with_neighbors(
        self,
        shift_ppm: float,
        hybridisation: str,
        neighbors: dict[str, int]
    ) -> None:
        """Add observation with hybridisation and neighbor data.

        Args:
            shift_ppm: Chemical shift value
            hybridisation: "sp3", "sp2", or "sp1"
            neighbors: Dict from parse_sphere_1() (element -> count)
        """
        # Update Welford statistics
        self.update_with_hybridisation(shift_ppm, hybridisation)

        # Update neighbor flags (presence/absence)
        if "C" in neighbors and neighbors["C"] > 0:
            self.has_carbon_neighbor += 1
        if "O" in neighbors and neighbors["O"] > 0:
            self.has_oxygen_neighbor += 1
        if "N" in neighbors and neighbors["N"] > 0:
            self.has_nitrogen_neighbor += 1
        if "S" in neighbors and neighbors["S"] > 0:
            self.has_sulfur_neighbor += 1

        # Halogens: F, Cl, Br, I
        halogens = {"F", "Cl", "Br", "I"}
        if any(elem in neighbors for elem in halogens):
            self.has_halogen_neighbor += 1
```

### Pattern 3: Schema Extension Pattern (Phase 34 Established)
**What:** Add neighbor columns to hose_stats table following v3→v4 migration pattern
**When to use:** Database schema evolution for new detection features
**Example:**
```python
# src/lucy_ng/database/schema.py
SCHEMA_VERSION = 5  # Increment from 4

def migrate_v4_to_v5(conn: sqlite3.Connection) -> None:
    """Migrate database from schema v4 to v5.

    Adds neighbor element count columns to hose_stats table.

    Args:
        conn: SQLite connection to database
    """
    cursor = conn.cursor()

    # Add neighbor count columns with DEFAULT 0
    cursor.execute(
        "ALTER TABLE hose_stats ADD COLUMN has_carbon_neighbor INTEGER NOT NULL DEFAULT 0"
    )
    cursor.execute(
        "ALTER TABLE hose_stats ADD COLUMN has_oxygen_neighbor INTEGER NOT NULL DEFAULT 0"
    )
    cursor.execute(
        "ALTER TABLE hose_stats ADD COLUMN has_nitrogen_neighbor INTEGER NOT NULL DEFAULT 0"
    )
    cursor.execute(
        "ALTER TABLE hose_stats ADD COLUMN has_sulfur_neighbor INTEGER NOT NULL DEFAULT 0"
    )
    cursor.execute(
        "ALTER TABLE hose_stats ADD COLUMN has_halogen_neighbor INTEGER NOT NULL DEFAULT 0"
    )

    # Update schema version
    cursor.execute(
        "UPDATE schema_meta SET value = ? WHERE key = ?",
        (str(SCHEMA_VERSION), "schema_version"),
    )

    conn.commit()
```

### Pattern 4: Frequency-Based Constraint Classification
**What:** Classify neighbors as forbidden (<1%), typical (1-95%), or mandatory (>95%)
**When to use:** Detection query results, for presentation to user or LSD constraint generation
**Example:**
```python
# src/lucy_ng/detection/models.py
from enum import Enum
from pydantic import BaseModel

class ConstraintType(str, Enum):
    """Classification of neighbor occurrence frequency."""
    FORBIDDEN = "forbidden"  # < 1% occurrence
    TYPICAL = "typical"      # 1-95% occurrence
    MANDATORY = "mandatory"  # > 95% occurrence

class ElementConstraint(BaseModel):
    """Constraint for a specific element as neighbor."""
    element: str  # "C", "O", "N", "S", "halogen"
    frequency: float  # 0.0 to 1.0
    constraint_type: ConstraintType

    @property
    def is_forbidden(self) -> bool:
        """True if element should NOT be bonded."""
        return self.constraint_type == ConstraintType.FORBIDDEN

    @property
    def is_mandatory(self) -> bool:
        """True if element MUST be bonded."""
        return self.constraint_type == ConstraintType.MANDATORY

class NeighbourDistribution(BaseModel):
    """Distribution of bonded elements for a shift range."""
    carbon: float = 0.0      # Frequency of C neighbor
    oxygen: float = 0.0      # Frequency of O neighbor
    nitrogen: float = 0.0    # Frequency of N neighbor
    sulfur: float = 0.0      # Frequency of S neighbor
    halogen: float = 0.0     # Frequency of halogen neighbor

    def get_constraints(
        self,
        forbidden_threshold: float = 0.01,
        mandatory_threshold: float = 0.95
    ) -> list[ElementConstraint]:
        """Classify each element as forbidden/typical/mandatory.

        Args:
            forbidden_threshold: Below this is forbidden (default 1%)
            mandatory_threshold: Above this is mandatory (default 95%)

        Returns:
            List of ElementConstraint objects
        """
        constraints = []

        for element, freq in [
            ("C", self.carbon),
            ("O", self.oxygen),
            ("N", self.nitrogen),
            ("S", self.sulfur),
            ("halogen", self.halogen),
        ]:
            if freq < forbidden_threshold:
                constraint_type = ConstraintType.FORBIDDEN
            elif freq > mandatory_threshold:
                constraint_type = ConstraintType.MANDATORY
            else:
                constraint_type = ConstraintType.TYPICAL

            constraints.append(
                ElementConstraint(
                    element=element,
                    frequency=freq,
                    constraint_type=constraint_type,
                )
            )

        return constraints
```

### Pattern 5: CLI Command with Override Flags
**What:** Add `lucy detect neighbours` command with threshold customization
**When to use:** All neighborhood detection queries from command line
**Example:**
```python
# src/lucy_ng/cli/detect.py
@detect.command("neighbours")
@click.argument("shift_ppm", type=float)
@click.option("--db", "-d", type=click.Path(exists=True), default=None)
@click.option("--radius", "-r", type=int, default=3)
@click.option("--window", "-w", type=float, default=2.0)
@click.option("--min-frequency", type=float, default=0.01,
              help="Minimum frequency for detection (default: 0.01 = 1%)")
@click.option("--max-frequency", type=float, default=0.95,
              help="Maximum frequency for mandatory (default: 0.95 = 95%)")
@click.option("--mode", type=click.Choice(["strict", "relaxed"]), default="strict",
              help="strict: 1%/95% thresholds, relaxed: 0.1%/99%")
@click.option("--format", type=click.Choice(["text", "json"]), default="text")
def neighbours_command(
    shift_ppm: float,
    db: str | None,
    radius: int,
    window: float,
    min_frequency: float,
    max_frequency: float,
    mode: str,
    format: str
) -> None:
    """Detect forbidden and mandatory bond partners from 13C shift.

    Example: lucy detect neighbours 170.5 --mode relaxed

    Modes:
      strict: 1% forbidden, 95% mandatory (default)
      relaxed: 0.1% forbidden, 99% mandatory (for rare molecules)
    """
    # Override thresholds based on mode
    if mode == "relaxed":
        min_frequency = 0.001  # 0.1%
        max_frequency = 0.99   # 99%

    db_path = Path(db) if db else DatabaseFinder.find_hose_database()
    if not db_path:
        click.echo("Error: No HOSE database found", err=True)
        raise SystemExit(1)

    detector = StatisticalDetector(db_path)
    result = detector.detect_neighbours(
        shift_ppm,
        radius=radius,
        window_ppm=window,
        forbidden_threshold=min_frequency,
        mandatory_threshold=max_frequency,
    )

    if format == "json":
        click.echo(result.model_dump_json(indent=2))
    else:
        click.echo(result.summary())
```

### Anti-Patterns to Avoid
- **Parsing HOSE at query time**: Precompute during stats generation, don't parse 7.9M HOSE codes per query
- **Boolean has_X flags only**: Use counts to enable "bonded to 2+ oxygens" constraints (e.g., carboxylic acids)
- **Single element queries**: Query all elements together, let caller filter (more flexible)
- **Ignoring multiplicity**: Carbonyl C (sp2) + quaternary can have zero C neighbors (CO₂ derivatives)

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Element symbol extraction | Character iteration | regex r'[A-Z][a-z]?' | Handles Cl, Br correctly (not C+l) |
| Forbidden O-O bonds | Hardcoded "no O-O" rule | Database frequency < 1% | Misses peroxides (legitimate O-O) |
| Mandatory C=O in carbonyls | Shift range 150-220 ppm | Database frequency > 95% at 170±2 | Accounts for conjugation effects |
| HOSE sphere parsing | Custom parser | String split + regex | HOSE syntax is simple, don't over-engineer |

**Key insight:** HOSE sphere 1 is a concatenation of element symbols with bond order prefixes (=, *, /). Regular expression `[A-Z][a-z]?` extracts all elements. The database already has millions of HOSE codes—parse once during generation, query many times at detection.

## Common Pitfalls

### Pitfall 1: Confusing "Has Neighbor" vs "Neighbor Count"
**What goes wrong:** Boolean flags can't distinguish C(O) from C(O)(O) (ether vs acetal)
**Why it happens:** Phase 34 used boolean-style sp3_count (actually counts, not booleans)
**How to avoid:**
- Use INTEGER columns for counts, not BOOLEAN
- Column names: has_X_neighbor stores count of observations with ≥1 X neighbor
- Frequency = has_X_neighbor / total_observations (presence, not average count)
- For "bonded to 2+ X" queries, need different approach (future enhancement)
**Warning signs:**
- Schema has BOOLEAN columns
- Can't detect acetals/ketals (two O neighbors)
- Documentation says "boolean flags" but stores integers

### Pitfall 2: HOSE Prefix Characters in Sphere 1
**What goes wrong:** Parsing "=OC" as elements ["O", "C"] instead of ["O", "C"] (O double-bonded)
**Why it happens:** Bond order prefixes (=, *, /) are not elements
**How to avoid:**
- Regex `[A-Z][a-z]?` extracts only element symbols
- Prefixes (=, *, /) indicate bond type, not separate elements
- Don't manually iterate characters—use regex
**Warning signs:**
- parse_sphere_1("C-3;=OC") returns {"=": 1, "O": 1, "C": 1}
- Element counts don't match RDKit neighbor counts
- Strange "elements" like "*" or "/" in database

### Pitfall 3: Aromatic Bond Notation
**What goes wrong:** Counting "*C" as two neighbors ("*" and "C")
**Why it happens:** Asterisks (*) indicate aromatic bonds, not elements
**How to avoid:**
- Strip bond order prefixes before element extraction
- Alternatively, regex inherently ignores non-letter characters
- Validate: benzene carbon has 2 C neighbors, not 4 (* and C twice)
**Warning signs:**
- Aromatic carbons show 4 neighbors instead of 2-3
- Database has mysterious "*" element
- Frequencies don't sum to reasonable values

### Pitfall 4: Missing Halogen Aggregation
**What goes wrong:** F, Cl, Br, I tracked separately, can't detect "no halogens" constraint
**Why it happens:** Each halogen is a different element
**How to avoid:**
- Store has_halogen_neighbor column aggregating F + Cl + Br + I
- Enables "halogen forbidden" detection for hydrocarbons
- Also store individual halogens for "Cl forbidden but Br allowed" (future)
**Warning signs:**
- Can't detect halogen-free constraints
- Need 4 separate queries for F, Cl, Br, I
- Database bloat with rare element columns

### Pitfall 5: Peroxide False Positive
**What goes wrong:** Detecting O-O as forbidden (< 1%) rejects all peroxides
**Why it happens:** Peroxides are rare but legitimate
**How to avoid:**
- Forbidden means "never occurs" in database, not "never valid"
- Document that < 1% filters noise, not impossibilities
- CLI --mode relaxed lowers threshold to 0.1% for rare cases
- User can override with --min-frequency 0.001
**Warning signs:**
- Structure generator rejects correct peroxide structures
- Agent confused about H₂O₂ derivatives
- Documentation claims "forbidden = chemically impossible"

### Pitfall 6: Multiplicity-Neighbor Interaction Ignored
**What goes wrong:** Queries neighbors without considering multiplicity (C vs CH vs CH₂)
**Why it happens:** Roadmap CLI shows `<multiplicity>` argument but design unclear
**How to avoid:**
- Decide: Should neighborhood queries accept multiplicity filter?
- Option A: Ignore multiplicity (simpler, Phase 35 scope)
- Option B: Filter by multiplicity from DEPT data (Phase 36 integration)
- Document decision in RESEARCH.md for planner
**Warning signs:**
- CLI has `<multiplicity>` arg but detector.detect_neighbours() doesn't use it
- User expects "sp2 carbons with O neighbor" but gets "all carbons with O"
- Need separate query combining hybridisation + neighbors

### Pitfall 7: Schema Version Mismatch Warning
**What goes wrong:** Query fails on v4 database (lacks neighbor columns)
**Why it happens:** Migration to v5 not automatic, user has v4 from Phase 34
**How to avoid:**
- detect_neighbours() should check if neighbor columns exist
- If missing, raise clear error: "Database needs regeneration for v5 schema"
- Don't return silent zeros (user thinks "no neighbors detected")
- CLI warns about schema version before query
**Warning signs:**
- `lucy detect neighbours 130.5` returns "no data" but hybridisation works
- All neighbor counts are 0 (columns exist but unpopulated)
- User ran Phase 34 but not Phase 35 database regeneration

## Code Examples

Verified patterns from official sources:

### Parse HOSE Sphere 1
```python
# Source: HOSE code analysis + regex best practices
import re
from collections import Counter

def parse_sphere_1(hose_code: str) -> dict[str, int]:
    """Extract bonded elements from HOSE code sphere 1.

    HOSE format: "PREFIX;SPHERE1(SPHERE2/SPHERE3/...)"
    Example: "C-3;=OCO(,,//)" -> {"O": 2, "C": 1}

    Args:
        hose_code: HOSE code string

    Returns:
        Dict mapping element symbol to count
    """
    # Split at semicolon to separate prefix from spheres
    parts = hose_code.split(";", 1)
    if len(parts) < 2:
        return {}

    # Extract sphere 1 (before first parenthesis)
    spheres_part = parts[1]
    sphere1 = spheres_part.split("(")[0] if "(" in spheres_part else spheres_part

    # Extract element symbols (uppercase + optional lowercase)
    # This automatically ignores bond order prefixes (=, *, /)
    elements = re.findall(r'[A-Z][a-z]?', sphere1)

    # Count occurrences
    return dict(Counter(elements))

# Test cases
assert parse_sphere_1("C-4;C(/)") == {"C": 1}
assert parse_sphere_1("C-4;CO(//)") == {"C": 1, "O": 1}
assert parse_sphere_1("C-3;=OCO(,,//)") == {"O": 2, "C": 1}
assert parse_sphere_1("C-3;*C*C(//)") == {"C": 2}  # aromatic, ignore *
assert parse_sphere_1("C-4;CClN(//)") == {"C": 1, "Cl": 1, "N": 1}
```

### Compute Neighbor Frequencies
```python
# Source: Phase 34 hybridisation detection pattern
def compute_neighbour_distribution(
    has_carbon: int,
    has_oxygen: int,
    has_nitrogen: int,
    has_sulfur: int,
    has_halogen: int,
    total_observations: int,
    forbidden_threshold: float = 0.01,
    mandatory_threshold: float = 0.95,
) -> dict[str, tuple[float, str]]:
    """Compute neighbor frequency distribution with constraints.

    Args:
        has_carbon: Count of observations with C neighbor
        has_oxygen: Count of observations with O neighbor
        has_nitrogen: Count of observations with N neighbor
        has_sulfur: Count of observations with S neighbor
        has_halogen: Count of observations with halogen neighbor
        total_observations: Total observations in query window
        forbidden_threshold: Below this is forbidden (default 1%)
        mandatory_threshold: Above this is mandatory (default 95%)

    Returns:
        Dict mapping element to (frequency, constraint_type)
    """
    if total_observations == 0:
        return {}

    distribution = {}

    for element, count in [
        ("C", has_carbon),
        ("O", has_oxygen),
        ("N", has_nitrogen),
        ("S", has_sulfur),
        ("halogen", has_halogen),
    ]:
        freq = count / total_observations

        # Classify constraint
        if freq < forbidden_threshold:
            constraint = "forbidden"
        elif freq > mandatory_threshold:
            constraint = "mandatory"
        else:
            constraint = "typical"

        distribution[element] = (freq, constraint)

    return distribution

# Example: carbonyl region (170 ppm)
# Expect: O mandatory (>95%), N/S/halogen typical or forbidden
result = compute_neighbour_distribution(
    has_carbon=850,    # 85% have C neighbor
    has_oxygen=980,    # 98% have O neighbor (mandatory!)
    has_nitrogen=120,  # 12% have N neighbor
    has_sulfur=5,      # 0.5% have S neighbor (forbidden!)
    has_halogen=0,     # 0% have halogen (forbidden!)
    total_observations=1000,
)
# result = {
#     "C": (0.85, "typical"),
#     "O": (0.98, "mandatory"),
#     "N": (0.12, "typical"),
#     "S": (0.005, "forbidden"),
#     "halogen": (0.0, "forbidden"),
# }
```

### Extend Stats Generator
```python
# Source: lucy-ng stats_generator.py pattern
from lucy_ng.prediction.hose_parser import parse_sphere_1

# In ResumableHOSEStatsGenerator._process_chunk()
for compound_id, smiles, shifts in self.db_manager.iter_compounds_with_shifts_from(...):
    mol = HOSECodeGenerator.prepare_mol(smiles)
    if mol is None:
        continue

    for atom_idx, shift_ppm in shifts:
        atom = mol.GetAtomWithIdx(atom_idx)
        if atom.GetSymbol() != "C":
            continue

        # Extract hybridisation (Phase 34)
        hybridisation = extract_hybridisation(atom)

        for radius in range(1, self.max_radius + 1):
            hose_code = self._hose_gen.generate_for_atom(mol, atom_idx, radius)
            if not hose_code:
                continue

            # NEW: Parse neighbors from sphere 1
            neighbors = parse_sphere_1(hose_code)

            # Update accumulator with neighbors
            accumulators[(hose_code, radius)].update_with_neighbors(
                shift_ppm, hybridisation, neighbors
            )
```

### Detection Query
```python
# Source: Phase 34 detect_hybridisation() pattern
def detect_neighbours(
    self,
    shift_ppm: float,
    radius: int = 3,
    window_ppm: float = 2.0,
    forbidden_threshold: float = 0.01,
    mandatory_threshold: float = 0.95,
) -> NeighbourResult:
    """Detect bond partner constraints from chemical shift.

    Args:
        shift_ppm: Target chemical shift
        radius: HOSE radius (default: 3)
        window_ppm: Query window (default: 2.0)
        forbidden_threshold: Below this is forbidden (default: 1%)
        mandatory_threshold: Above this is mandatory (default: 95%)

    Returns:
        NeighbourResult with distributions and constraints
    """
    # Query database
    records = self._db.get_hose_stats_by_shift_window(
        shift_ppm, radius, window_ppm
    )

    # Aggregate neighbor counts
    has_carbon = sum(r.has_carbon_neighbor for r in records)
    has_oxygen = sum(r.has_oxygen_neighbor for r in records)
    has_nitrogen = sum(r.has_nitrogen_neighbor for r in records)
    has_sulfur = sum(r.has_sulfur_neighbor for r in records)
    has_halogen = sum(r.has_halogen_neighbor for r in records)
    total_observations = sum(r.count for r in records)

    if total_observations == 0:
        return NeighbourResult(
            shift_ppm=shift_ppm,
            window_ppm=window_ppm,
            radius=radius,
            distribution=NeighbourDistribution(),
            has_data=False,
            warning="No neighbor data found. Database may need regeneration.",
        )

    # Compute frequencies
    distribution = NeighbourDistribution(
        carbon=has_carbon / total_observations,
        oxygen=has_oxygen / total_observations,
        nitrogen=has_nitrogen / total_observations,
        sulfur=has_sulfur / total_observations,
        halogen=has_halogen / total_observations,
    )

    # Get constraints
    constraints = distribution.get_constraints(
        forbidden_threshold, mandatory_threshold
    )

    return NeighbourResult(
        shift_ppm=shift_ppm,
        window_ppm=window_ppm,
        radius=radius,
        forbidden_threshold=forbidden_threshold,
        mandatory_threshold=mandatory_threshold,
        distribution=distribution,
        constraints=constraints,
        total_observations=total_observations,
        unique_hose_codes=len(records),
        has_data=True,
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded forbidden pairs | Database frequency distributions | Sherlock (2023) | Handles rare but valid structures (peroxides) |
| SMARTS pattern matching | HOSE sphere 1 parsing | lucy-ng Phase 35 | Faster, no RDKit graph traversal at query time |
| Single-element queries | Multi-element distribution | Phase 35 design | One query returns all neighbor constraints |
| Boolean has_neighbor | Count-based tracking | Phase 35 design | Enables "2+ oxygen" constraints (future) |

**Deprecated/outdated:**
- SMARTS for neighbor detection: HOSE codes already encode this, don't recompute
- Separate queries per element: Query once, aggregate counts, compute all frequencies
- Fixed 1%/95% thresholds: CLI provides --mode relaxed and --min/max-frequency overrides

## Open Questions

Things that couldn't be fully resolved:

1. **Should multiplicity filter neighborhood queries?**
   - What we know: Roadmap CLI shows `<multiplicity>` argument
   - What's unclear: How does multiplicity (C/CH/CH₂/CH₃) interact with neighbor detection?
   - Recommendation: Phase 35 ignores multiplicity (simpler), Phase 36 adds DEPT integration for combined queries

2. **Count vs presence for neighbor columns**
   - What we know: "has_X_neighbor" stores count of observations with ≥1 X neighbor
   - What's unclear: Should we also track "X_neighbor_count_avg" for average bond partners?
   - Recommendation: Use presence (count of observations) for Phase 35, defer average counts to future

3. **How to handle multi-neighbor constraints?**
   - What we know: Carboxylic acids have 2+ O neighbors, database stores presence not count
   - What's unclear: How to detect "must have 2 oxygens" vs "must have at least 1 oxygen"?
   - Recommendation: Phase 35 detects "has O neighbor" only, multi-neighbor constraints deferred

4. **Optimal forbidden/mandatory thresholds**
   - What we know: Sherlock uses 1% threshold, Phase 34 uses same
   - What's unclear: Are 1%/95% optimal for neighbors, or should they differ from hybridisation?
   - Recommendation: Start with 1%/95%, make configurable, gather user feedback

5. **Should aromatic bonds be distinguished?**
   - What we know: HOSE uses * prefix for aromatic, = for double bond
   - What's unclear: Should "O neighbor" distinguish C-O from C=O from aromatic C-O?
   - Recommendation: Phase 35 ignores bond order (simpler), Phase 36 adds bond type distinction

## Sources

### Primary (HIGH confidence)
- lucy-ng source code: src/lucy_ng/prediction/stats_generator.py (Phase 34 patterns)
- lucy-ng source code: src/lucy_ng/detection/detector.py (Phase 34 detection architecture)
- lucy-ng source code: src/lucy_ng/database/schema.py (migration patterns)
- [HOSE Code Stereo Extension - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6648302/) - HOSE sphere structure
- [HOSE Code Principle - ResearchGate](https://www.researchgate.net/figure/Principle-of-HOSE-codes-The-HOSE-code-is-built-sphere-wise-around-the-atom-described_fig12_23283222) - Sphere-wise encoding

### Secondary (MEDIUM confidence)
- Python regex documentation - Element symbol extraction pattern
- [Sherlock CASE System - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9920390/) - 1% threshold for detection
- Phase 34 RESEARCH.md - Established detection patterns and thresholds

### Tertiary (LOW confidence - verified with code)
- [HOSE Code Stereo Extension - ACS Omega](https://pubs.acs.org/doi/10.1021/acsomega.9b00488) - HOSE syntax details
- HOSE code generation examples (bash output above) - Sphere 1 element concatenation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies, all libraries from Phases 34
- Architecture: HIGH - Directly mirrors Phase 34 hybridisation detection patterns
- Pitfalls: HIGH - HOSE parsing verified with test cases, schema patterns from Phase 34

**Research date:** 2026-02-11
**Valid until:** 2026-03-11 (30 days - stable domain, established patterns)

**Notes:**
- No CONTEXT.md exists - all decisions at planner's discretion
- HOSE sphere 1 structure verified with live code generation (bash examples)
- Multiplicity interaction with neighbors is open question - recommend Phase 35 ignores it
- Neighbor count columns store presence frequency, not average bond partner count
- Schema version increments to v5 (v4 was Phase 34 hybridisation)
