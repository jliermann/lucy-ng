# Phase 37: Signal Grouping - Research

**Researched:** 2026-02-11
**Domain:** 1D clustering for NMR shift grouping with multiplicity awareness
**Confidence:** HIGH

## Summary

Signal grouping identifies clusters of carbon chemical shifts within a specified tolerance (0.25 ppm) to handle ambiguous assignments in structure elucidation. This is a **critical capability** — Sherlock's thesis explicitly states that ibuprofen (C4 at 44.90 ppm, C5 at 45.03 ppm, difference 0.13 ppm) **could not be solved without this feature**. Without combinatorial exchange of close shifts, the candidate list was empty.

The implementation is algorithmically straightforward (1D clustering with distance threshold) but requires careful multiplicity awareness to prevent false positives. The key insight from Sherlock analysis: grouping shifts within 0.25 ppm creates combinatorial explosion when carbons are truly different but happen to be close. Prevention requires **multiplicity-aware grouping** — only group CH/CH3 together if both ambiguous, never group CH2 with CH.

**Primary recommendation:** Use simple distance-based clustering (no external dependencies needed) with multiplicity filtering logic. Output LSD-compatible parenthesized atom lists for HMBC constraints.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.10+ | itertools.groupby for clustering | No external dependencies needed |
| NumPy | >=1.24 | Array operations (already in pyproject.toml) | Efficient distance calculations |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| scipy.cluster.hierarchy | >=1.10 | Hierarchical clustering (already in deps) | Alternative if simple threshold insufficient |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Simple threshold | scikit-learn DBSCAN | DBSCAN adds 90MB dependency for 20-line algorithm |
| Simple threshold | dbscan1d package | Specialized but unnecessary — simple approach works |
| Simple threshold | scipy.cluster.hierarchy | More flexible but overkill for 1D tolerance clustering |

**Installation:**
```bash
# No new dependencies needed
# numpy and scipy already in pyproject.toml
```

**Recommendation:** Do NOT add scikit-learn dependency. The clustering problem is simple (1D points, single distance threshold, known tolerance). A clean, readable Python implementation using NumPy is superior to heavyweight ML libraries.

## Architecture Patterns

### Recommended Module Structure
```
src/lucy_ng/detection/
├── __init__.py          # Exports GroupingResult, SignalGrouper (add to existing)
├── models.py            # Add GroupingResult model
├── detector.py          # Add signal grouping to StatisticalDetector
└── grouping.py          # NEW: SignalGrouper class
```

### Pattern 1: Tolerance-Based 1D Clustering

**What:** Group 1D points (chemical shifts) where pairwise distances are all ≤ tolerance.

**When to use:** NMR signal grouping, any scenario with close numerical values needing combinatorial treatment.

**Example:**
```python
# Source: Direct implementation (no library needed)
def cluster_by_tolerance(values: list[float], tolerance: float) -> list[list[int]]:
    """Group indices where all pairwise distances <= tolerance.

    Args:
        values: Sorted list of float values
        tolerance: Maximum distance between any two points in same cluster

    Returns:
        List of index groups
    """
    if not values:
        return []

    sorted_indices = sorted(range(len(values)), key=lambda i: values[i])
    groups = []
    current_group = [sorted_indices[0]]

    for idx in sorted_indices[1:]:
        # Check if this point can join current group
        # All pairwise distances in group must be <= tolerance
        can_join = all(
            abs(values[idx] - values[other_idx]) <= tolerance
            for other_idx in current_group
        )

        if can_join:
            current_group.append(idx)
        else:
            groups.append(current_group)
            current_group = [idx]

    groups.append(current_group)
    return groups
```

**Alternative (if needed):** For more complex clustering needs, scipy.cluster.hierarchy is already available:

```python
# Source: scipy documentation
from scipy.cluster.hierarchy import fclusterdata

def cluster_hierarchical(values: list[float], tolerance: float) -> list[int]:
    """Use scipy hierarchical clustering with distance threshold."""
    data = np.array(values).reshape(-1, 1)
    labels = fclusterdata(data, t=tolerance, criterion='distance', method='single')
    return labels.tolist()
```

**Recommendation:** Start with simple threshold approach. Only use scipy if edge cases require more sophisticated clustering.

### Pattern 2: Multiplicity-Aware Filtering

**What:** Only group shifts if they have compatible multiplicities (prevent grouping CH2 with CH).

**When to use:** After initial distance clustering, filter groups to prevent false positives.

**Example:**
```python
# Source: Research from Sherlock pitfall analysis
def is_multiplicity_compatible(mult1: str | None, mult2: str | None) -> bool:
    """Check if two multiplicities can be grouped.

    Rules:
    - Same multiplicity (both CH2) → compatible
    - Both ambiguous (CH/CH3) → compatible
    - Different definite multiplicities (CH2 vs CH) → incompatible
    - One or both None → conservative, allow grouping

    Args:
        mult1: First multiplicity ("CH", "CH2", "CH3", "CH/CH3", or None)
        mult2: Second multiplicity

    Returns:
        True if grouping is allowed
    """
    # If either is None, conservatively allow grouping
    if mult1 is None or mult2 is None:
        return True

    # Normalize to uppercase
    m1 = mult1.upper()
    m2 = mult2.upper()

    # Same multiplicity → compatible
    if m1 == m2:
        return True

    # Both ambiguous (CH or CH3) → compatible
    ambiguous = {"CH", "CH3", "CH/CH3"}
    if m1 in ambiguous and m2 in ambiguous:
        return True

    # Different definite multiplicities → incompatible
    return False
```

### Pattern 3: LSD Parenthesized Atom List Generation

**What:** Convert grouped atom indices to LSD syntax `(atom1 atom2 ...)` for combinatorial HMBC constraints.

**When to use:** When agent needs to write LSD HMBC commands with grouped carbons.

**Example:**
```python
# Source: Sherlock analysis + LSD manual
def format_lsd_atom_list(atom_indices: list[int]) -> str:
    """Format atom indices for LSD parenthesized syntax.

    Args:
        atom_indices: List of 1-based LSD atom indices

    Returns:
        LSD-compatible string (e.g., "(2 3 4)" or "2" if single)
    """
    if len(atom_indices) == 1:
        return str(atom_indices[0])

    # Sort for canonical representation
    sorted_atoms = sorted(atom_indices)
    atom_str = " ".join(str(a) for a in sorted_atoms)
    return f"({atom_str})"

# Example usage in HMBC constraint:
# Single carbon: "HMBC 2 8"
# Grouped carbons: "HMBC (2 3) 8"  → LSD tries both 2-8 and 3-8 correlations
```

### Anti-Patterns to Avoid

- **Using clustering libraries for simple threshold problem:** DBSCAN/k-means are overkill. Simple sorted iteration is cleaner.
- **Ignoring multiplicity information:** Causes combinatorial explosion with false positives (CH2 grouped with CH).
- **Grouping without warning user:** Agent should document why shifts were grouped (close distance + compatible multiplicities).
- **Tolerance too large:** 0.25 ppm is validated by Sherlock. Don't use 0.5 ppm or you'll group unrelated signals.
- **Overlapping groups:** Groups should be disjoint. If shift X is 0.2 ppm from Y and Y is 0.2 ppm from Z, but X is 0.4 ppm from Z, X and Z should NOT be in same group.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| General ML clustering | Custom DBSCAN, k-means | scipy or scikit-learn | Edge cases, performance optimization, tested code |
| JSON output formatting | String concatenation | Pydantic models | Type safety, validation, serialization |
| Distance calculations | Nested loops | NumPy vectorization | Performance for large datasets |

**Key insight:** The 1D tolerance clustering IS simple enough to hand-roll (20-30 lines). What you DON'T hand-roll is the statistical detection infrastructure (already exists) and the Pydantic result models (follow existing patterns).

## Common Pitfalls

### Pitfall 1: False Positive Grouping (Different Multiplicities)

**What goes wrong:** Grouping C4 (CH2, 44.90 ppm), C5 (CH, 45.03 ppm), C6 (CH3, 45.20 ppm) creates 6x combinatorial search space where 5/6 permutations are wrong.

**Why it happens:** Simple distance threshold without checking DEPT multiplicity data.

**How to avoid:**
1. Accept optional multiplicity argument in `lucy analyze grouping`
2. Filter groups after distance clustering to remove incompatible multiplicities
3. Warn if groups split due to multiplicity filtering

**Warning signs:**
- LSD produces 100+ solutions with similar MAE
- Grouped signals have different DEPT phases (positive vs negative)
- Agent log shows "forced combinatorial exchange" on definitively different carbons

### Pitfall 2: Transitive Grouping Explosion

**What goes wrong:** If tolerance is too large, transitive grouping creates huge clusters. Example: A-B distance 0.24, B-C distance 0.24, C-D distance 0.24 → all four grouped even though A-D distance is 0.72 ppm.

**Why it happens:** Naive clustering algorithms use pairwise distances without checking cluster diameter.

**How to avoid:** Use **complete linkage** criterion — max pairwise distance in cluster must be ≤ tolerance, not just neighbor-to-neighbor.

**Warning signs:**
- Single group contains >5 shifts
- Group span (max - min) exceeds tolerance
- Agent produces "unreasonably large combinatorial search space" warning

### Pitfall 3: Off-by-One Errors in Atom Indexing

**What goes wrong:** LSD uses 1-based atom indices. Python uses 0-based. Converting between the two incorrectly breaks HMBC constraint generation.

**Why it happens:** Mixing LSD atom IDs with Python list indices.

**How to avoid:**
- CLI input: shifts are 0-indexed in order given (shift[0], shift[1], ...)
- CLI output: atom indices are 1-based for LSD compatibility (atom 1, atom 2, ...)
- Document clearly: "Atom IDs in output are 1-based for LSD file generation"

**Warning signs:**
- LSD error "atom 0 does not exist"
- Agent writes `HMBC (1 2) 3` but expects atoms 2 and 3 to be grouped

### Pitfall 4: Missing Edge Case: All Signals Grouped

**What goes wrong:** If all shifts are within tolerance (data calibration error), every carbon is in one massive group → combinatorial explosion.

**Why it happens:** Bad reference calibration, wrong nucleus selected, peak picking threshold too high.

**How to avoid:**
- Check if group size exceeds reasonable limit (e.g., >50% of total signals)
- Warn user: "Unusually large group detected — check spectrum calibration"
- Return warning field in result model

**Warning signs:**
- Single group contains 10+ shifts
- Group span is 2+ ppm (much larger than tolerance)

## Code Examples

Verified patterns from research and existing codebase:

### Example 1: Complete Grouping Algorithm

```python
# Source: Designed based on Sherlock analysis + existing detection patterns
from dataclasses import dataclass
import numpy as np

@dataclass
class SignalGroup:
    """A group of signals within tolerance."""
    indices: list[int]  # 0-based indices into original shift list
    shifts: list[float]  # Chemical shifts in group
    multiplicities: list[str | None]  # Multiplicities (if provided)
    span: float  # max - min in group
    centroid: float  # Mean shift

    @property
    def atom_ids(self) -> list[int]:
        """Return 1-based LSD atom IDs."""
        return [i + 1 for i in self.indices]

    def lsd_atom_list(self) -> str:
        """Format for LSD parenthesized syntax."""
        if len(self.atom_ids) == 1:
            return str(self.atom_ids[0])
        sorted_atoms = sorted(self.atom_ids)
        return f"({' '.join(str(a) for a in sorted_atoms)})"


def group_signals(
    shifts: list[float],
    multiplicities: list[str | None] | None = None,
    tolerance: float = 0.25,
) -> tuple[list[SignalGroup], list[int]]:
    """Group signals by distance tolerance and multiplicity compatibility.

    Args:
        shifts: Chemical shifts to group
        multiplicities: Optional DEPT multiplicities for filtering
        tolerance: Maximum pairwise distance in group (default 0.25 ppm)

    Returns:
        (groups, ungrouped_indices) where groups are SignalGroup objects
        and ungrouped_indices are 0-based indices of singleton signals
    """
    n = len(shifts)
    if n == 0:
        return [], []

    if multiplicities is None:
        multiplicities = [None] * n

    # Sort by shift
    sorted_indices = sorted(range(n), key=lambda i: shifts[i])

    # Distance-based clustering
    groups_raw = []
    current_group = [sorted_indices[0]]

    for idx in sorted_indices[1:]:
        # Check complete linkage: all pairwise distances <= tolerance
        can_join = all(
            abs(shifts[idx] - shifts[other_idx]) <= tolerance
            for other_idx in current_group
        )

        if can_join:
            current_group.append(idx)
        else:
            groups_raw.append(current_group)
            current_group = [idx]

    groups_raw.append(current_group)

    # Filter by multiplicity compatibility
    groups = []
    ungrouped = []

    for group_indices in groups_raw:
        if len(group_indices) == 1:
            ungrouped.append(group_indices[0])
            continue

        # Check multiplicity compatibility within group
        compatible = True
        for i, idx1 in enumerate(group_indices):
            for idx2 in group_indices[i+1:]:
                if not is_multiplicity_compatible(
                    multiplicities[idx1],
                    multiplicities[idx2]
                ):
                    compatible = False
                    break
            if not compatible:
                break

        if compatible:
            group_shifts = [shifts[i] for i in group_indices]
            group_mults = [multiplicities[i] for i in group_indices]
            groups.append(SignalGroup(
                indices=group_indices,
                shifts=group_shifts,
                multiplicities=group_mults,
                span=max(group_shifts) - min(group_shifts),
                centroid=np.mean(group_shifts),
            ))
        else:
            # Multiplicity incompatible — split into singletons
            ungrouped.extend(group_indices)

    return groups, ungrouped
```

### Example 2: CLI Integration Pattern

```python
# Source: Existing CLI patterns (analyze.py, detect.py)
import click
import json

@click.command("grouping")
@click.argument("shifts", type=str)
@click.option(
    "--multiplicities", "-m", type=str, default=None,
    help="Comma-separated DEPT multiplicities (CH, CH2, CH3, CH/CH3).",
)
@click.option(
    "--tolerance", "-t", type=float, default=0.25,
    help="Distance tolerance in ppm (default: 0.25).",
)
@click.option(
    "--format", "output_format",
    type=click.Choice(["text", "json"]), default="text",
    help="Output format.",
)
def grouping_command(
    shifts: str,
    multiplicities: str | None,
    tolerance: float,
    output_format: str,
) -> None:
    """Group carbon shifts within tolerance for LSD combinatorial exchange.

    SHIFTS is a comma-separated list of chemical shifts in ppm.

    Examples:

        lucy analyze grouping "44.90,45.03,129.38,127.26"

        lucy analyze grouping "44.90,45.03,45.20" --multiplicities "CH2,CH,CH3"

        lucy analyze grouping "44.90,45.03" --tolerance 0.15 --format json
    """
    # Parse shifts
    try:
        shift_list = [float(s.strip()) for s in shifts.split(",")]
    except ValueError as e:
        click.echo(f"Error parsing shifts: {e}", err=True)
        raise SystemExit(1)

    # Parse multiplicities
    mult_list = None
    if multiplicities:
        mult_list = [m.strip() or None for m in multiplicities.split(",")]
        if len(mult_list) != len(shift_list):
            click.echo(
                f"Error: {len(shift_list)} shifts but {len(mult_list)} multiplicities",
                err=True,
            )
            raise SystemExit(1)

    # Group signals
    from lucy_ng.detection.grouping import group_signals

    groups, ungrouped = group_signals(shift_list, mult_list, tolerance)

    # Output
    if output_format == "json":
        result = {
            "tolerance": tolerance,
            "groups": [
                {
                    "indices": g.indices,
                    "shifts": g.shifts,
                    "multiplicities": g.multiplicities,
                    "span": g.span,
                    "centroid": g.centroid,
                    "atom_ids": g.atom_ids,
                    "lsd_atom_list": g.lsd_atom_list(),
                }
                for g in groups
            ],
            "ungrouped": [
                {"index": i, "shift": shift_list[i], "atom_id": i+1}
                for i in ungrouped
            ],
        }
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Signal Grouping (tolerance: {tolerance} ppm)")
        click.echo(f"Total signals: {len(shift_list)}")
        click.echo(f"Groups: {len(groups)}")
        click.echo(f"Ungrouped: {len(ungrouped)}")

        if groups:
            click.echo("\nGroups:")
            for i, g in enumerate(groups, 1):
                click.echo(f"  Group {i}: {g.lsd_atom_list()}")
                for idx, shift, mult in zip(g.indices, g.shifts, g.multiplicities):
                    mult_str = f" ({mult})" if mult else ""
                    click.echo(f"    Atom {idx+1}: {shift:.2f} ppm{mult_str}")
                click.echo(f"    Span: {g.span:.3f} ppm, Centroid: {g.centroid:.2f} ppm")

        if ungrouped:
            click.echo("\nUngrouped (single atoms):")
            for idx in ungrouped:
                mult_str = f" ({mult_list[idx]})" if mult_list and mult_list[idx] else ""
                click.echo(f"  Atom {idx+1}: {shift_list[idx]:.2f} ppm{mult_str}")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual assignment of close shifts | Automatic grouping with tolerance threshold | Sherlock (2004-2009) | Solves ibuprofen-class cases that were previously unsolvable |
| Rigid LSD HMBC constraints | Parenthesized atom lists for combinatorial exploration | LSD 1.5+ | Enables structure elucidation with ambiguous assignments |
| Distance-only grouping | Multiplicity-aware grouping | Not yet standard (lucy-ng v3.0 innovation) | Prevents false positive combinatorial explosions |

**Deprecated/outdated:**
- **Multiple LSD files for permutations:** Sherlock's "combinatorial pyLSD" generates separate LSD files for each atom exchange scenario. This is superseded by LSD's native parenthesized syntax which handles combinatorial exploration in a single file.

## Open Questions

1. **Optimal tolerance value**
   - What we know: Sherlock uses 0.25 ppm (validated by ibuprofen case)
   - What's unclear: Should tolerance be nucleus-specific (13C vs 1H)?
   - Recommendation: Hardcode 0.25 ppm for Phase 37, make configurable if needed

2. **Handling DEPT-90 vs DEPT-135 ambiguity**
   - What we know: DEPT-135 distinguishes CH2 (negative) from CH/CH3 (positive)
   - What's unclear: When user has only DEPT-135, CH/CH3 are ambiguous. Should they be grouped?
   - Recommendation: Yes — mark as "CH/CH3" multiplicity and allow grouping within that class

3. **LSD syntax validation**
   - What we know: Parenthesized syntax is documented in LSD manual
   - What's unclear: Does `HMBC (2 3 4) 8` work correctly (3-way grouping)?
   - Recommendation: Phase 37-02 should test with actual LSD runs

## Sources

### Primary (HIGH confidence)
- [Sherlock CASE System Analysis](background/sherlock-analysis.md) - Signal grouping implementation details, ibuprofen case
- [Sherlock Pitfalls Analysis](.planning/research/PITFALLS.md) - Multiplicity-aware grouping rationale
- [Existing detection module](src/lucy_ng/detection/) - Architecture patterns for models and detector
- [scipy.cluster.hierarchy documentation](https://docs.scipy.org/doc/scipy/reference/cluster.hierarchy.html) - Hierarchical clustering (if needed)

### Secondary (MEDIUM confidence)
- [scikit-learn DBSCAN documentation](https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html) - Alternative clustering approach (not recommended)
- [NMR peak grouping with hierarchical clustering](https://pmc.ncbi.nlm.nih.gov/articles/PMC5587626/) - Academic research on tolerance-based grouping with DBSCAN adaptation
- [kmeans1d package](https://pypi.org/project/kmeans1d/) - Specialized 1D clustering (unnecessary for this use case)

### Tertiary (LOW confidence)
- Web search results on 1D clustering - General context, no specific NMR domain knowledge

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Simple problem, no external dependencies needed (numpy/scipy already present)
- Architecture: HIGH - Follows existing detection module patterns (models.py, detector.py, CLI integration)
- Pitfalls: HIGH - Well-documented in Sherlock analysis (false positive grouping is critical)
- LSD syntax: MEDIUM - Parenthesized syntax is documented but needs validation with test cases

**Research date:** 2026-02-11
**Valid until:** 90 days (algorithm is stable, no fast-moving dependencies)

**Research coverage:**
- ✅ Standard stack identified (Python stdlib + numpy)
- ✅ Architecture patterns defined (grouping.py, models, CLI)
- ✅ Pitfalls catalogued (false positives, transitive grouping, indexing)
- ✅ Code examples provided (complete algorithm + CLI integration)
- ✅ LSD syntax researched (needs validation in plan 37-02)

**Key decision for planning:**
- Do NOT add scikit-learn dependency
- Do NOT use complex clustering algorithms (simple threshold sufficient)
- DO implement multiplicity-aware filtering (critical for preventing false positives)
- DO validate LSD parenthesized syntax with test cases before agent integration
